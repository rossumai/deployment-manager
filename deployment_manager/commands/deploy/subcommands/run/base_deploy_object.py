from collections import defaultdict
from copy import deepcopy
from datetime import datetime

from pydantic import BaseModel
import questionary
from deployment_manager.commands.deploy.subcommands.run.attribute_override import (
    AttributeOverrider,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    generate_deploy_timestamp,
    remove_queue_attributes_for_cross_org,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    LookupTable,
    Target,
    TargetWithDefault,
)
from deployment_manager.commands.deploy.subcommands.run.merge.state import DeployState
from deployment_manager.common.read_write import read_json
from rich import print as pprint
from rich.panel import Panel


from anyio import Path
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.utils.consts import CustomResource, display_error, settings
from deployment_manager.utils.functions import templatize_name_id


class PathNotFoundException(Exception): ...


class TimestampMismatchException(Exception): ...


class NonExistentObjectException(Exception): ...


class DeployException(Exception): ...


# TODO: document methods
class DeployObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource

    release_file_reference: "ReleaseOrchestrator" = None
    yaml_reference: dict = None
    data: dict = None

    initialize_failed: bool = False
    deploy_failed: bool = False

    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    # TODO: better parsing -> better dummy ID
    PLAN_CREATE_TBD_ID_STR: str = "0000000"

    overrider: AttributeOverrider = None

    async def initialize_from_release_file(self, release_file: "ReleaseOrchestrator"):
        self.release_file_reference = release_file
        self.yaml_reference = self.get_object_in_yaml()

        self.ignore_timestamp_mismatch = (
            self.release_file_reference.force_deploy
            or self.release_file_reference.ignore_timestamp_mismatches.get(
                self.type, {}
            ).get(self.id, False)
        )

        self.overrider = AttributeOverrider(type=self.type, plan_only=self.plan_only)

        if not self.data:
            try:
                self.data = await read_json(self.path)
            except Exception:
                raise PathNotFoundException(
                    f"Could not load object data from: [green]{self.path}[/green]. Is the object name in deploy file in-sync with its local path?"
                ) from None

    async def deploy(self):
        """Creates/updates the object in the Elis API"""
        ...

    @property
    def path(self) -> Path:
        return (
            Path(self.release_file_reference.base_path)
            / self.type.value
            / f"{templatize_name_id(self.name, self.id)}.json"
        )

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self):
        return f'"[green]{self.name}[/green] ([purple]{self.id}[/purple])"'

    @property
    def is_creating_targets(self):
        for target in self.targets:
            if not target.id:
                return True
        return False

    def get_object_in_yaml(self):
        objects = self.release_file_reference.yaml.data.get(self.type.value, [])
        for object in objects:
            if object.get("id", None) == self.id:
                return object
        return None

    def prepare_object_copy_for_deploy(self, target: Target): ...

    def create_source_to_target_string(self, target: dict):
        return f'"{self.name} ([purple]{self.id}[/purple])" -> "{target['name']} ([purple]{target['id']}[/purple])"'

    def create_plan_target_object_id(self, source_id: int):
        return f"{str(source_id)}{self.PLAN_CREATE_TBD_ID_STR}"

    def check_plan_object_id(self, object_id: any):
        return self.PLAN_CREATE_TBD_ID_STR in str(object_id)

    async def check_modified_timestamps_equal(
        self, last_deploy_timestamp, remote_object_id: int
    ):
        remote_object = await self.get_remote_object(remote_object_id)
        try:
            remote_modified_at = remote_object.get("modified_at", "")
            # Both timestamps are needed for a meaningful comparison
            if not remote_modified_at or not last_deploy_timestamp:
                return True
            remote_timestamp = datetime.fromisoformat(remote_modified_at)
            deploy_timestamp = datetime.fromisoformat(last_deploy_timestamp)
            if remote_timestamp > deploy_timestamp:
                display_error(
                    f"Timestamp of remote target {self.display_type} {remote_object.get('name', 'no-name')} [purple]({remote_object.get('id', 'no-id')})[/purple] is newer than last deploy [white](remote: {remote_modified_at} | deploy_file: {self.last_deployed_at})[/white]"
                )
                return False
            return True
        except Exception:
            raise ValueError("One of the provided timestamps is not in ISO format")

    async def get_remote_object(self, remote_object_id):
        try:
            return await self.client._http_client.fetch_one(self.type, remote_object_id)
        except APIClientError as e:
            if e.status_code == 404:
                raise NonExistentObjectException(
                    f"{self.display_type} [purple]{remote_object_id}[/purple] does not exist on remote."
                ) from None
            raise e

    def update_targets(self, results):
        # asyncio.gather returns results in the same order as they were put in
        for index, (result, target) in enumerate(zip(results, self.targets)):
            # In case of errors, do not overwrite the existing target ID, the object still exists
            if new_id := result.get("id", None):
                target.id = new_id
            target.data = result
            self.yaml_reference["targets"][index]["id"] = target.id

    # TODO: rename target_object (misleading)
    async def upload(self, target_object: dict, target: Target):
        if target.id:
            return await self.update_remote(target_object=target_object, target=target)
        else:
            return await self.create_remote(target_object=target_object, target=target)

    async def check_source_object(self):
        try:
            await self.source_client._http_client.fetch_one(self.type, self.id)
        except APIClientError as e:
            if e.status_code == 404:
                return False
            raise e
        return True

    def remove_object_from_yaml(self):
        objects = self.yaml.data.get(self.type.value, [])
        self.yaml.data[self.type.value] = [
            obj for obj in objects if obj.get("id") != self.id
        ]

    # Target is provided so that subclasses can use it (even if this basic method does not)
    async def create_remote(self, target_object: dict, target: Target = None):
        try:
            if self.plan_only:
                result = deepcopy(target_object)
                result_id = self.create_plan_target_object_id(target_object["id"])
                result["url"] = result["url"].replace(str(result["id"]), str(result_id))
                result["id"] = result_id
            else:
                result = await self.client._http_client.create(self.type, target_object)
                self.last_deployed_at = generate_deploy_timestamp()
            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )

            return result
        except Exception as e:
            display_error(
                f"Error while creating {self.display_type} {self.display_label} ^",
                e,
            )
            self.deploy_failed = True
            return {}

    async def update_remote(self, target_object: dict, target: Target):
        try:
            if self.plan_only:
                result = deepcopy(target_object)
                result["url"] = result["url"].replace(str(result["id"]), str(target.id))
                result["id"] = target.id

                if (
                    not self.ignore_timestamp_mismatch
                    and not await self.check_modified_timestamps_equal(
                        self.last_deployed_at, target.id
                    )
                ):
                    if await questionary.confirm(
                        "Overwrite the remote target?", default=True
                    ).ask_async():
                        self.ignore_timestamp_mismatch = True
                    else:
                        raise TimestampMismatchException(
                            "Unexpected timestamp mismatch"
                        )
            else:
                result = await self.client._http_client.update(
                    resource=self.type, id_=target.id, data=target_object
                )
                # Important for the ID override phase (deploy file still the old one and the remote just got updated)
                self.last_deployed_at = result.get(
                    "modified_at", generate_deploy_timestamp()
                )
            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.UPDATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )
            return result
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type} {self.display_label} -> "{target.id}: {e}',
                (
                    None
                    if isinstance(e, NonExistentObjectException)
                    or isinstance(e, TimestampMismatchException)
                    else e
                ),
            )
            self.deploy_failed = True
            return {}

    async def delete_remote(self, target: Target):
        try:
            if not self.plan_only:
                await self.client._http_client.delete(self.type, id_=target.id)

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.DELETE_PRINT_STR} {self.display_type}: [purple]({target.id})[/purple]."
            )
        except Exception as e:
            display_error(
                f'Error while deleting {self.display_type} {self.display_label} -> "{target.id}: {e}',
                e,
            )
            self.deploy_failed = True

    async def implicit_override_targets(self, lookup_table: LookupTable):
        try:
            for target_index, target in enumerate(self.targets):
                overriding_object = deepcopy(target)
                self.remove_override_irrelevant_props(overriding_object.data)

                self.overrider.replace_ids_in_target_object(
                    target=overriding_object,
                    lookup_table=lookup_table,
                    target_object_index=target_index,
                    num_targets=len(self.targets),
                )

                if self.plan_only:
                    # When updating, take the real remote object
                    # The diff comparison will then show only overrides that are not on the remote already (not all overrides from source)
                    if target.id and not self.check_plan_object_id(target.id):
                        overriden_object_data = await self.get_remote_object(target.id)
                    else:
                        overriden_object_data = deepcopy(self.data)

                    self.remove_override_irrelevant_props(overriden_object_data)

                    diff = self.overrider.create_override_diff(
                        overriden_object_data, overriding_object.data
                    )
                    if not diff:
                        return

                    colorized_diff = self.overrider.parse_diff(diff)
                    message = f"Attribute override: {self.display_type} {self.create_source_to_target_string(overriding_object.data)}:\n{colorized_diff}"
                    pprint(Panel(message))
                else:
                    # Update only objects where there was a difference after override
                    await self.update_remote(
                        target_object=overriding_object.data, target=target
                    )
        except Exception as e:
            display_error(
                f'Error while overriding IDs of {self.display_type} {self.display_label} -> "{target.id}: {e}',
                e,
            )
            raise DeployException(
                "ID override failed, see error details above."
            ) from None

    def remove_override_irrelevant_props(self, data):
        # These attribute either should not be compared or were already replaced via replace_dependency_url()
        data.pop("created_by", None)
        data.pop("created_at", None)
        data.pop("modified_by", None)
        data.pop("modified_at", None)

        # These keys are not pulled locally so comparing a remote object with a local one would yield false diffs
        ignored_keys_for_type = settings.NON_VERSIONED_KEYS_PER_OBJECT.get(self.type, [])
        for key in ignored_keys_for_type:
            data.pop(key, None)

        match self.type:
            case Resource.Schema:
                data.pop("queues", None)
            case Resource.Hook:
                data.pop("token_owner", None)
                data.pop("guide", None)
                data.pop("run_after", None)
                data.pop("queues", None)
            case Resource.Workspace:
                data.pop("queues", None)
                data.pop("organization", None)
            case Resource.Queue:
                data.pop("users", None)
                data.pop("counts", None)
                data.pop("workspace", None)
                data.pop("inbox", None)
                data.pop("schema", None)
                data.pop("hooks", None)
                data.pop("webhooks", None)
                if not self.is_same_org_deploy:
                    remove_queue_attributes_for_cross_org(data)


class EmptyObjectRelease(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int = None
    name: str = ""
    type: Resource = "no-type"
    base_path: Path = None

    initialize_failed: bool = False
    deploy_failed: bool = False
    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    async def initialize(*args, **kwargs): ...

    async def deploy(self): ...

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"
