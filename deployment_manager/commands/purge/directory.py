import asyncio
import questionary
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rich import print as pprint
from rich.panel import Panel

from deployment_manager.commands.download.downloader import Downloader

from deployment_manager.utils.consts import (
    display_error,
    display_info,
    display_warning,
    settings,
)

from deployment_manager.commands.download.directory import OrganizationDirectory
from deployment_manager.utils.functions import extract_id_from_url

ALL_OBJECT_TYPES = [
    Resource.Schema.value,
    Resource.Hook.value,
    Resource.Workspace.value,
    Resource.Queue.value,
]


# Click can only work with strings, not enum objects, but RossumAPIClient expects the enums
OBJECT_TYPE_MAPPING = {
    Resource.Schema.value: Resource.Schema,
    Resource.Hook.value: Resource.Hook,
    Resource.Workspace.value: Resource.Workspace,
    Resource.Queue.value: Resource.Queue,
}

# Queues should be deleted before (used) schemas and workspaces
OBJECT_PRIORITIES = {
    Resource.Queue.value: 0,
    Resource.Schema.value: 1,
    Resource.Workspace.value: 2,
    Resource.Hook.value: 3,
}


class PurgeOrganizationDirectory(OrganizationDirectory):
    api_base: str = None  # Make non-required
    org_id: int = None  # Make non-required

    client: ElisAPIClient
    selected_subdirs: list[str]
    # dict with object types as keys and optional explicit list of ids to purge
    purged_object_types_ids: dict[str, list[int]]

    objects: list[dict] = []

    def display_label(self, name: str, id: str):
        return f'"[green]{name}[/green] ([purple]{id}[/purple])"'

    def display_type(self, type: Resource):
        if not type:
            return ""
        # Remove the plural 's'
        return f"[yellow]{type.value[:-2 if type in [Resource.Inbox] else -1]}[/yellow]"

    def all_subdirs_included(self):
        return all(
            subdir.include for subdir in self.subdirectories.values()
        ) or not len(self.subdirectories.keys())

    async def get_remote_objects_by_type(self):
        object_types = self.purged_object_types_ids.keys()
        object_types = sorted(
            object_types, key=lambda x: OBJECT_PRIORITIES.get(x, float("inf"))
        )

        for object_type in object_types:
            if object_type == settings.UNUSED_SCHEMAS:
                self.objects.extend(await self.download_unused_schemas())
            else:
                object_type_as_enum = OBJECT_TYPE_MAPPING.get(object_type)
                self.objects.extend(
                    await self.download_objects_by_type(type=object_type_as_enum)
                )


    def keep_only_objects_with_explicit_ids(self):
        # this method is used when purging from deploy template. It will filter only those objects present in template
        keep_objects = []
        for object in self.objects:
            if object["id"] in self.purged_object_types_ids[object["type"].value]:
                keep_objects.append(object)
        self.objects = keep_objects


    def keep_only_objects_of_included_subdirs(self):
        kept_objects = []
        # No point filtering by subdirs if all should be purged
        if self.all_subdirs_included():
            return

        for object in self.objects:
            subdir = self.find_subdir_of_object(object=object)
            if not subdir:
                display_warning(
                    f"Could not find subdir for {self.display_type(object.get('type', ''))} {self.display_label(object.get('name', 'no-name'), object.get('id', 'no-id'))} - skipping."
                )
                continue
            if subdir.include:
                kept_objects.append(object)
        self.objects = kept_objects

    def find_subdir_of_object(self, object: dict):
        for subdir in self.subdirectories.values():
            if object.get("id", None) in subdir.object_ids:
                return subdir
        return None

    async def download_objects_by_type(self, type: Resource):
        objects = []
        for object in await Downloader(client=self.client).download_remote_objects(
            type=type
        ):
            objects.append({**object, "type": type})
        return objects

    async def download_unused_schemas(self):
        schemas = []
        for schema in await Downloader(client=self.client).download_remote_objects(
            type=Resource.Schema
        ):
            if not len(schema.get("queues")):
                schemas.append({**schema, "type": Resource.Schema})
        return schemas

    def display_objects_to_be_deleted(object_types_ids: list[tuple[Resource, str]]):
        for type, id in object_types_ids:
            pprint(f"[yellow]{type.value}[/yellow] {id}")

    async def purge_organization(self):
        try:
            for subdir_name, subdir in self.subdirectories.items():
                subdir.include = subdir_name in self.selected_subdirs
            await self.find_object_ids_for_subdirs()
            await self.get_remote_objects_by_type()
            if any(i for i in self.purged_object_types_ids.values()):
                # using explicit ids to delete
                self.keep_only_objects_with_explicit_ids()
            self.keep_only_objects_of_included_subdirs()
        except Exception as e:
            display_error(
                f"Error while initializing {settings.PURGE_COMMAND_NAME} of {self.name}: {str(e)}",
                e,
            )
            return

        try:
            pprint(
                Panel(
                    f"Running {settings.PURGE_COMMAND_NAME} in [green]{self.name}[/green] ([purple]{self.org_id}[/purple]).\n"
                    f"Removing [red]{'[/red], [red]'.join(self.purged_object_types_ids.keys())}[/red] "
                    f"from subdir(s) [red]{'[/red], [red]'.join(self.selected_subdirs)}[/red]."
                )
            )
            for object in self.objects:
                pprint(
                    f"{settings.PLAN_PRINT_STR} {settings.DELETE_PRINT_STR} {self.display_type(object.get('type', ""))} {self.display_label(object.get('name', "no-name"), object.get('id', "no-id"))}"
                )

            if not await questionary.confirm(
                "Are you sure you want to delete the objects above? This operation cannot be undone.",
                default=False,
            ).ask_async():
                return
        except Exception as e:
            display_error(
                f"Error while planning {settings.PURGE_COMMAND_NAME} of {self.name}: {str(e)}",
                e,
            )
            return

        try:

            await self.delete_objects()
        except Exception as e:
            display_error(f"Error while deleting objects in {self.name}: {str(e)}")
            return

    async def delete_objects(self):
        for object in self.objects:
            type, object_id = object.get("type", ""), object.get("id", "no-id")
            if not type:
                display_warning(
                    f"Unknown type for {object.get('name', 'no-name')} - skipping"
                )
                continue
            elif not object_id:
                display_warning(
                    f"Unknown ID for {object.get('name', 'no-name')} - skipping"
                )
                continue

            try:

                # Queues have a "cooldown" period for deletion which needs to be overriden
                if type == Resource.Queue:
                    (
                        await self.client._http_client._request(
                            "DELETE",
                            f"queues/{object_id}",
                            params={"delete_after": "0"},
                        ),
                    )
                else:
                    if type == Resource.Schema:
                        schema = await self.client.retrieve_schema(object_id)
                        queues = [extract_id_from_url(queue_url) for queue_url in schema.queues]
                        if not queues:
                            queues = []

                        queue_deleted_count = 0
                        while queue_deleted_count != len(queues):
                            for queue in queues:
                                queue_id = extract_id_from_url(queue)
                                try:
                                    await self.client.retrieve_queue(queue_id)
                                except APIClientError as e:
                                    if e.status_code == 404:
                                        queue_deleted_count += 1

                            if queue_deleted_count == len(queues):
                                break
                            # Deleting queues (even when providing 'delete_after': 0) is asynchronous, wait for a short while
                            display_info(
                                "Waiting for queues to be deleted in the API..."
                            )
                            await asyncio.sleep(5)

                    await self.client._http_client.delete(resource=type, id_=object_id)

                pprint(
                    f"{settings.DELETE_PRINT_STR} {self.display_type(object.get('type', ""))} {self.display_label(object.get('name', "no-name"), object.get('id', "no-id"))}"
                )
            except Exception as e:
                if isinstance(e, APIClientError) and e.status_code == 404:
                    display_warning(
                        f"{self.display_type(type)} [purple]{object_id}[/purple] already does not exist on remote."
                    )
                display_error(
                    f"Error while deleting {self.display_type(type)} [purple]{object_id}[/purple]: {e}"
                )
