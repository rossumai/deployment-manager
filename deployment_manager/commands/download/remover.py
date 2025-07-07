import json
import os
import shutil
from typing import Any
from anyio import Path
from pydantic import BaseModel

from deployment_manager.commands.download.helpers import delete_objects_non_versioned_attributes
from rossum_api.api_client import Resource

from deployment_manager.common.determine_path import determine_object_type_from_url
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    find_formula_fields_in_schema,
    read_object_from_json,
    NON_VERSIONED_ATTRIBUTES_FILE_LOCK
)
from deployment_manager.utils.consts import (
    CustomResource,
    display_warning,
    settings,
)
from deployment_manager.commands.download.subdirectory import (
    Subdirectory,
)


# TODO: error handling? Level of objects vs level of object ?
class ObjectRemover(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    type: Resource | CustomResource
    subdir: Subdirectory
    directory: Any = None

    local_path: Path
    local_object: dict

    remote_object: dict = {}

    @staticmethod
    async def construct_remover(object_path: Path, id_objects_map, **kwargs):

        local_object = await read_object_from_json(object_path)
        url, id = local_object.get("url", ""), local_object.get("id", "")
        # Clearly not a Rossum object, just ignore
        if not url or not id:
            return None

        object_type = determine_object_type_from_url(url)
        remote_object = id_objects_map.get(object_type, {}).get(id, {})

        if object_type == Resource.Hook:
            constructor = HookRemover
        elif object_type == Resource.Schema:
            constructor = SchemaRemover
        else:
            constructor = ObjectRemover
        return constructor(
            type=object_type,
            local_object=local_object,
            local_path=object_path,
            remote_object=remote_object,
            **kwargs,
        )

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    async def remove_if_stale(self):
        # There is not remote object with this ID (for this type)
        if not self.remote_object:
            await self.delete_object()
            return True

        # The object exists, but it got renamed, assigned elsewhere, etc.
        remote_path = self.directory.construct_path_for_remote_object(
            object_type=self.type, remote_object=self.remote_object, subdir=self.subdir
        )
        # The names are lowercased because some OS's (mainly MacOS) are case-insensitive in their paths
        if str(remote_path).casefold() != str(self.local_path).casefold():
            await self.delete_object()
            return True

    # Async because of subobjects potentially needing async operations
    async def delete_object(self):
        display_warning(
            f"Deleting {self.display_type} that no longer exists in Rossum, was renamed, or its parent object moved elsewhere: [green]{self.local_path}[/green]"
        )
        os.remove(self.local_path)
        await delete_objects_non_versioned_attributes(self.local_path)


class SchemaRemover(ObjectRemover):
    async def remove_if_stale(self):
        removed_schema = await super().remove_if_stale()

        # Check if individual formula fields are still in the schema
        if not removed_schema:
            remote_formula_fields = find_formula_fields_in_schema(
                self.remote_object["content"]
            )
            remote_field_ids = [ff[0] for ff in remote_formula_fields]
            local_formula_dir = create_formula_directory_path(self.local_path)
            if not local_formula_dir or not await local_formula_dir.exists():
                return
            async for formula_path in local_formula_dir.iterdir():
                local_field_id = formula_path.stem
                if local_field_id not in remote_field_ids:
                    os.remove(formula_path)

    async def delete_object(self):
        await super().delete_object()

        formula_dir_path = create_formula_directory_path(self.local_path)
        if await formula_dir_path.exists():
            shutil.rmtree(formula_dir_path)


class HookRemover(ObjectRemover):
    async def delete_object(self):
        await super().delete_object()

        hook_code_path = create_custom_hook_code_path(
            hook_path=self.local_path, hook=self.local_object
        )
        if hook_code_path and await hook_code_path.exists():
            os.remove(hook_code_path)
