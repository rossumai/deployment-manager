import re
from anyio import Path
from pydantic import BaseModel
import questionary
from rossum_api.api_client import Resource

from deployment_manager.commands.download.helpers import should_write_object
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    create_formula_file,
    find_formula_fields_in_schema,
    write_json,
    write_str,
)
from deployment_manager.utils.consts import display_error, display_warning
from deployment_manager.utils.functions import (
    templatize_name_id,
)
from deployment_manager.commands.download.subdirectory import (
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

    def display_label(self, name, id):
        return f'"[green]{name}[/green] ([purple]{id}[/purple])"'

    async def save_downloaded_objects(self):
        for object in self.objects:
            subdir = self.find_subdir_of_object(object)
            if not subdir:
                self.objects_without_subdir.append(object)
                continue
            # The subdir should not be pulled, disregard the current object
            elif not subdir.include:
                continue
            await self.save_downloaded_object(object, subdir)

        await self.handle_objects_without_subdir()

    async def handle_objects_without_subdir(self):
        if self.objects_without_subdir:
            object_name_ids = [
                templatize_name_id(object["name"], object["id"])
                for object in self.objects_without_subdir
            ]
            # Keeping in plural on purpose -> hence self.type
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

    def construct_object_path(self, subdir: Subdirectory, object: dict) -> Path: ...

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

    def construct_object_path(self, subdir: Subdirectory, object: dict) -> Path:
        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(object["name"], object["id"])
            / "workspace.json"
        )
        return object_path

    async def save_downloaded_object(self, workspace: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, object=workspace)
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

    def construct_object_path(self, subdir: Subdirectory, queue: dict) -> Path:
        workspace_for_queue = self.find_workspace_for_queue(queue)
        if not workspace_for_queue:

            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue["name"], queue["id"])
            / "queue.json"
        )
        return object_path

    async def save_downloaded_object(self, queue: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, queue=queue)
        if not object_path:
            return
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
        display_error(
            f"Could not find workspace for {self.display_type} {self.display_label(queue.get('name', "no-name"), queue.get('id', 'no-id'))}. Skipping."
        )
        return None


class InboxSaver(QueueSaver):
    type: Resource = Resource.Inbox
    queues: list[dict]

    def find_subdir_of_object(self, object: dict):
        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        queue = self.find_queue(object)
        if queue:
            # If you know the parent's subdir, you can use its subdir
            return super().find_subdir_of_object(queue)

        return None

    def find_queue(self, inbox: dict):
        for queue in self.queues:
            if queue["url"] == inbox.get("queues", [None])[0]:
                return queue
        display_warning(
            f"Could not find queue for {self.display_type} {self.display_label(inbox.get('name', 'no-name'), inbox.get('id', 'no-id'))}. The object will not be saved locally."
        )
        return None

    def construct_object_path(self, subdir: Subdirectory, inbox: dict) -> Path:
        queue_for_inbox = self.find_queue(inbox)
        if not queue_for_inbox:
            return
        workspace_for_queue = self.find_workspace_for_queue(queue_for_inbox)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_inbox["name"], queue_for_inbox["id"])
            / "inbox.json"
        )
        return object_path

    async def save_downloaded_object(self, inbox: dict, subdir: Subdirectory):
        if not inbox.get("queues", []):
            return

        object_path = self.construct_object_path(subdir=subdir, inbox=inbox)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, inbox, self.changed_files
        ):
            await write_json(
                object_path,
                inbox,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class SchemaSaver(QueueSaver):
    type: Resource = Resource.Schema
    queues: list[dict]

    async def save_downloaded_objects(self):
        for object in self.objects:
            subdir = self.find_subdir_of_object(object)
            if not subdir:
                self.objects_without_subdir.append(object)
                continue
            # The subdir should not be pulled, disregard the current object
            elif not subdir.include:
                continue
            await self.save_downloaded_object(object, subdir)

    def find_subdir_of_object(self, object: dict):
        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        queue = self.find_queue(object)
        if queue:
            # If you know the parent's subdir, you can use its subdir
            return super().find_subdir_of_object(queue)

        return None

    def find_queue(self, schema: dict):
        schema_queues = schema.get("queues", [None])
        warning_message = f"Could not find queue for {self.display_type} {self.display_label(schema.get('name', 'no-name'), schema.get('id', 'no-id'))}. The object will not be saved locally."
        # The schema might not have any queues assigned ([])
        if not schema_queues:
            display_warning(warning_message)
            return None

        for queue in self.queues:
            if queue["url"] == schema_queues[0]:
                return queue

        display_warning(warning_message)
        return None

    def construct_object_path(
        self,
        subdir: Subdirectory,
        schema: dict,
    ) -> Path:
        queue_for_schema = self.find_queue(schema)
        if not queue_for_schema:
            return
        workspace_for_queue = self.find_workspace_for_queue(queue_for_schema)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_schema["name"], queue_for_schema["id"])
            / "schema.json"
        )
        return object_path

    async def save_downloaded_object(self, schema: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, schema=schema)
        if not object_path:
            return
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
                formula_directory_path = create_formula_directory_path(object_path)
                for field_id, code in formula_fields:
                    await create_formula_file(
                        formula_directory_path / f"{field_id}.py", code
                    )


class HookSaver(Saver):
    type: Resource = Resource.Hook

    def construct_object_path(self, subdir: Subdirectory, hook: dict) -> Path:
        object_path = (
            self.base_path
            / subdir.name
            / "hooks"
            / f'{templatize_name_id(hook["name"], hook["id"])}.json'
        )
        return object_path

    async def save_downloaded_object(self, hook: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, hook=hook)
        if not object_path:
            return
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
