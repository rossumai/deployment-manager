import re
from anyio import Path
from pydantic import BaseModel
import questionary
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.download.helpers import should_write_object
from project_rossum_deploy.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    create_formula_file,
    find_formula_fields_in_schema,
    write_json,
    write_str,
)
from project_rossum_deploy.utils.functions import (
    templatize_name_id,
)
from project_rossum_deploy.commands.download.subdirectory import (
    Subdirectory,
)


# TODO: error handling? Level of objects vs level of object ?
class Saver(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    type: Resource
    base_path: Path
    subdirs: list[Subdirectory] = []
    objects: list[dict]
    changed_files: list
    download_all: bool = False

    objects_without_subdir: list[dict] = []

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    async def save_downloaded_objects(self):
        for object in self.objects:
            subdir = self.find_subdir_of_object(object)
            if not subdir:
                self.objects_without_subdir.append(object)
                continue
            # The subdir should not be pulled, disregard the current object
            elif not subdir.download:
                continue
            await self.save_downloaded_object(object, subdir)

        if self.objects_without_subdir:
            object_name_ids = [
                templatize_name_id(object["name"], object["id"])
                for object in self.objects_without_subdir
            ]
            manual_assign = await questionary.confirm(
                f"Found remote {self.type} that could not be assigned to any subdirectory. Do you want to assign them manually now?\n{'\n'.join(object_name_ids)}\n"
            ).ask_async()

            if not manual_assign:
                return

            for object in self.objects_without_subdir:
                subdir = await self.get_subdir_from_user(object)
                await self.save_downloaded_object(object, subdir)

    async def get_subdir_from_user(self, object):
        subdir_choices = [
            questionary.Choice(title=subdir.name, value=subdir)
            for subdir in self.subdirs
        ]
        return await questionary.select(
            f"Choose subdir for {templatize_name_id(object['name'], object['id'])}:",
            choices=subdir_choices,
        ).ask_async()

    async def save_downloaded_object(self): ...

    def find_subdir_of_object(self, object: dict):
        if len(self.subdirs) == 1:
            return self.subdirs[0]

        for subdir in self.subdirs:
            if object["id"] in subdir.object_ids:
                return subdir

        for subdir in self.subdirs:
            if not subdir.regex:
                continue
            subdir_regex = re.compile(subdir.regex)
            if subdir_regex.findall(object["name"]):
                return subdir

        return None


class WorkspaceSaver(Saver):
    type: Resource = Resource.Workspace

    async def save_downloaded_object(self, workspace: dict, subdir: Subdirectory):
        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace["name"], workspace["id"])
            / "workspace.json"
        )

        if self.download_all or await should_write_object(
            object_path, workspace, self.changed_files
        ):
            await write_json(
                object_path,
                workspace,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class QueueSaver(Saver):
    type: Resource = Resource.Queue
    workspaces: list[dict]

    def find_subdir_of_object(self, object: dict):
        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        workspace = self.find_workspace_for_queue(object)
        if workspace:
            # If you know the parent's subdir, you can use its subdir
            return super().find_subdir_of_object(workspace)

        return None

    async def save_downloaded_object(self, queue: dict, subdir: Subdirectory):
        workspace_for_queue = self.find_workspace_for_queue(queue)
        if not workspace_for_queue:
            raise Exception(f'Could not find workspace for queue {queue['name']}.')

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue["name"], queue["id"])
            / "queue.json"
        )

        if self.download_all or await should_write_object(
            object_path, queue, self.changed_files
        ):
            await write_json(
                object_path,
                queue,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

    def find_workspace_for_queue(self, queue: dict):
        for ws in self.workspaces:
            if ws["url"] == queue.get("workspace", None):
                return ws
        return None


class InboxSaver(QueueSaver):
    type: Resource = Resource.Inbox
    queues: list[dict]

    def find_subdir_of_object(self, object: dict):
        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        queue = self.find_queue_for_inbox(object)
        if queue:
            # If you know the parent's subdir, you can use its subdir
            return super().find_subdir_of_object(queue)

        return None

    async def save_downloaded_object(self, inbox: dict, subdir: Subdirectory):
        if not inbox.get("queues", []):
            return

        queue_for_inbox = self.find_queue_for_inbox(inbox)
        if not queue_for_inbox:
            raise Exception(f'Could not find queue for inbox {inbox['name']}.')
        workspace_for_queue = self.find_workspace_for_queue(queue_for_inbox)
        if not workspace_for_queue:
            raise Exception(
                f'Could not find workspace for queue {queue_for_inbox['name']}.'
            )

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_inbox["name"], queue_for_inbox["id"])
            / "inbox.json"
        )

        if self.download_all or await should_write_object(
            object_path, inbox, self.changed_files
        ):
            await write_json(
                object_path,
                inbox,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

    def find_queue_for_inbox(self, inbox: dict):
        for queue in self.queues:
            if queue["url"] == inbox.get("queues", [None])[0]:
                return queue
        return None


class SchemaSaver(Saver):
    type: Resource = Resource.Schema

    async def save_downloaded_object(self, schema: dict, subdir: Subdirectory):
        object_path = (
            self.base_path
            / subdir.name
            / "schemas"
            / f'{templatize_name_id(schema["name"], schema["id"])}.json'
        )

        if self.download_all or await should_write_object(
            object_path, schema, self.changed_files
        ):
            await write_json(
                object_path,
                schema,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

            formula_fields = find_formula_fields_in_schema(schema["content"])
            if formula_fields:
                formula_directory_path = create_formula_directory_path(
                    object_path, schema.get("name", ""), schema.get("id", "")
                )
                for field_id, code in formula_fields:
                    await create_formula_file(
                        formula_directory_path / f"{field_id}.py", code
                    )


class HookSaver(Saver):
    type: Resource = Resource.Hook

    async def save_downloaded_object(self, hook: dict, subdir: Subdirectory):
        object_path = (
            self.base_path
            / subdir.name
            / "hooks"
            / f'{templatize_name_id(hook["name"], hook["id"])}.json'
        )

        if self.download_all or await should_write_object(
            object_path, hook, self.changed_files
        ):
            await write_json(
                object_path,
                hook,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

            custom_hook_code_path = create_custom_hook_code_path(object_path, hook)
            if custom_hook_code_path:
                await write_str(
                    custom_hook_code_path, hook.get("config", {}).get("code", None)
                )
