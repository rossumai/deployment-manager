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
class ObjectRelease(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource
    base_path: str = None

    yaml: DeployYaml = None
    yaml_reference: dict = None
    data: dict = None

    client: ElisAPIClient = None
    source_client: ElisAPIClient = None

    plan_only: bool = False
    force_deploy: bool = False
    auto_delete: bool = False
    is_same_org_deploy: bool = False

    initialize_failed: bool = False
    deploy_failed: bool = False

    last_deploy_timestamp: str = ""
    ignore_timestamp_mismatches: dict[Resource | CustomResource, dict[int, bool]] = (
        defaultdict(dict)
    )
    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    # TODO: better parsing -> better dummy ID
    PLAN_CREATE_TBD_ID_STR: str = "0000000"

    overrider: AttributeOverrider = None

    async def initialize(
        self,
        yaml,
        client,
        source_client,
        source_dir_path,
        auto_delete=False,
        plan_only=False,
        force_deploy=False,
        is_same_org_deploy=False,
        ignore_timestamp_mismatches: dict = {},
        last_deploy_timestamp="",
    ):
        # Base path is defined in the config itself for some objects (queues), for others, it needs to be added
        if not self.base_path:
            self.base_path = source_dir_path
        self.yaml = yaml
        self.yaml_reference = self.get_object_in_yaml()

        self.auto_delete = auto_delete
        self.plan_only = plan_only
        self.force_deploy = force_deploy
        self.is_same_org_deploy = is_same_org_deploy

        self.ignore_timestamp_mismatches = ignore_timestamp_mismatches
        self.ignore_timestamp_mismatch = (
            force_deploy
            or ignore_timestamp_mismatches.get(self.type, {}).get(self.id, False)
        )
        self.last_deploy_timestamp = last_deploy_timestamp

        self.overrider = AttributeOverrider(type=self.type, plan_only=self.plan_only)

        try:
            self.data = await read_json(self.path)
        except Exception:
            raise PathNotFoundException(
                f"Could not load object data from: [green]{self.path}[/green]. Is the object name in deploy file in-sync with its local path?"
            ) from None
        self.client = client
        self.source_client = source_client

    async def deploy(self):
        """Creates/updates the object in the Elis API"""
        ...

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
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
        objects = self.yaml.data.get(self.type.value, [])
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
            if not remote_modified_at:
                return True
            remote_timestamp = datetime.fromisoformat(remote_modified_at)
            deploy_timestamp = datetime.fromisoformat(last_deploy_timestamp)
            if remote_timestamp > deploy_timestamp:
                display_error(
                    f"Timestamp of remote target {self.display_type} {remote_object.get('name', 'no-name')} [purple]({remote_object.get('id', 'no-id')})[/purple] is newer than last deploy [white](remote: {remote_modified_at} | deploy_file: {self.last_deploy_timestamp})[/white]"
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
                self.last_deploy_timestamp = generate_deploy_timestamp()
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
                        self.last_deploy_timestamp, target.id
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
                self.last_deploy_timestamp = result.get(
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

                # ! Previous code was implicitly relying on some attributes being removed, not just in diff comparison
                # e.g., hook.queues=[] was set before updating/creating it, queue.hooks then assigns hooks
                # But if we send out hook.queues during ID override, the hooks will get unassigned
                # TODO: keep current override_irrelevant function for what should not get sent (do not touch what was replaced by replace dep url)
                # TODO: create a modified version of the function to apply to diffing

                # Object that is being sent into Rossum
                overriding_object = deepcopy(target)
                self.remove_override_irrelevant_props(overriding_object.data)

                self.overrider.replace_ids_in_target_object(
                    target=overriding_object,
                    lookup_table=lookup_table,
                    target_object_index=target_index,
                    num_targets=len(self.targets),
                )

                if self.plan_only:
                    await self.display_planned_diffs(target=target)
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

    async def display_planned_diffs(self, overriding_object: Target):
        # Object that is displayed as diff
        diff_overriding_object_data = deepcopy(overriding_object.data)
        self.remove_diff_irrelevant_props(diff_overriding_object_data)

        # When updating, take the real remote object
        # The diff comparison will then show only overrides that are not on the remote already (not all overrides from source)
        if overriding_object.id and not self.check_plan_object_id(overriding_object.id):
            overriden_object_data = await self.get_remote_object(overriding_object.id)
        else:
            overriden_object_data = deepcopy(self.data)

        # Code diffs need some of the attributes retained - use the original for that
        diff_overriden_object_data = deepcopy(overriden_object_data)
        self.remove_diff_irrelevant_props(diff_overriden_object_data)

        diff = self.overrider.create_override_diff(
            diff_overriden_object_data, diff_overriding_object_data
        )

        hook_code_diff = self.overrider.create_hook_code_override_diff(
            overriden_object_data, overriding_object.data
        )

        formula_code_diffs = self.overrider.create_formula_code_override_diffs(
            overriden_object_data, overriding_object.data
        )

        if diff:
            colorized_diff = self.overrider.parse_diff(diff)
            message = f"Attribute override: {self.display_type} {self.create_source_to_target_string(overriding_object.data)}:\n{colorized_diff}"
            pprint(Panel(message))

        if hook_code_diff:
            colorized_code_diff = self.overrider.parse_diff(hook_code_diff)
            message = f"Hook code diff: {self.display_type} {self.create_source_to_target_string(overriding_object.data)}:\n\n{colorized_code_diff}"
            pprint(Panel(message))

        for field_id, code_diff in formula_code_diffs.items():
            colorized_code_diff = self.overrider.parse_diff(code_diff)
            message = f"[yellow]{field_id}[/yellow]:\n\n{colorized_code_diff}"
            pprint(Panel(message))

    def remove_override_irrelevant_props(self, data):
        """
        Deletes attributes that should not be part of the update override payload (e.g., hook.queues is empty from the deploy process, by removing it, we keep whatever deploy assigned)
        """
        data.pop("created_by", None)
        data.pop("created_at", None)
        data.pop("modified_by", None)
        data.pop("modified_at", None)

        # These keys are not pulled locally and are read-only - no point sending them back to Rossum
        ignored_keys_for_type = settings.IGNORED_KEYS.get(self.type, [])
        for key in ignored_keys_for_type:
            data.pop(key, None)

        match self.type:
            case Resource.Schema:
                data.pop("queues", None)
            case Resource.Hook:
                data.pop("token_owner", None)
                data.pop("run_after", None)
                data.pop("queues", None)
            case Resource.Workspace:
                data.pop("queues", None)
                data.pop("organization", None)
            case Resource.Queue:
                data.pop("workspace", None)
                data.pop("inbox", None)
                data.pop("schema", None)
                data.pop("hooks", None)
                data.pop("webhooks", None)
                if not self.is_same_org_deploy:
                    remove_queue_attributes_for_cross_org(data)

    def remove_diff_irrelevant_props(self, data):
        """
        Deletes attributes that should not be shown in the diff (even if they are theoretically part of the payload).
        """
        # These attribute either should not be compared or were already replaced via replace_dependency_url()
        data.pop("created_by", None)
        data.pop("created_at", None)
        data.pop("modified_by", None)
        data.pop("modified_at", None)

        # These keys are not pulled locally so comparing a remote object with a local one would yield false diffs
        ignored_keys_for_type = settings.IGNORED_KEYS.get(self.type, [])
        for key in ignored_keys_for_type:
            data.pop(key, None)

        match self.type:
            case Resource.Organization:
                data.pop("users", None)
                data.pop("trial_expires_at", None)
                data.pop("creator", None)
            case Resource.Schema:
                self.remove_formula_fields_code(data.get("content", []))
                self.remove_schema_ignored_attributes(data.get("content", []))
            case Resource.Inbox:
                # Email will always be different and cannot be edited
                data.pop("email", None)
            case Resource.Hook:
                # Code is displayed separately, this would just show one huge string
                data.get("config", {}).pop("code", None)
                data.pop("token_owner", None)
            case Resource.Workspace:
                ...
            case Resource.Queue:
                # Should be ignored because we do not send it (Elis API does not accept inbox assignment)
                # If not ignored, it would look like we are unassigning the inbox
                data.pop("inbox", None)
                if not self.is_same_org_deploy:
                    remove_queue_attributes_for_cross_org(data)

    def remove_formula_fields_code(self, node: dict):
        if isinstance(node, list):
            for subnode in node:
                self.remove_formula_fields_code(subnode)
        elif isinstance(node, dict):
            if node["category"] == "datapoint" and node.get("formula", None):
                node.pop("formula", None)
            elif "children" in node:
                return self.remove_formula_fields_code(node["children"])

    def remove_schema_ignored_attributes(self, node: dict):
        if isinstance(node, list):
            for subnode in node:
                self.remove_schema_ignored_attributes(subnode)
        elif isinstance(node, dict):
            if node["category"] == "datapoint":
                for field, _ in settings.DEPLOY_IGNORED_SCHEMA_ATTRIBUTES:
                    node.pop(field, None)
            elif "children" in node:
                return self.remove_schema_ignored_attributes(node["children"])


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
