from copy import deepcopy

from pydantic import BaseModel
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    AttributeOverrider,
)
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.subcommands.run.models import (
    LookupTable,
    Target,
    TargetWithDefault,
)
from project_rossum_deploy.common.read_write import read_json
from rich import print as pprint
from rich.panel import Panel


from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import display_error, settings
from project_rossum_deploy.utils.functions import templatize_name_id


class PathNotFoundException(Exception): ...


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
    plan_only: bool = False
    is_same_org_deploy: bool = False
    deploy_failed: bool = False

    targets: list[TargetWithDefault] = []

    # TODO: better parsing -> better dummy ID
    PLAN_CREATE_TBD_ID_STR: str = "0000000"

    overrider: AttributeOverrider = None

    async def initialize(
        self,
        yaml: DeployYaml,
        client: ElisAPIClient,
        source_dir_path: Path,
        plan_only: bool = False,
        is_same_org_deploy=False,
    ):
        # Base path is defined in the config itself for some objects (queues), for others, it needs to be added
        if not self.base_path:
            self.base_path = source_dir_path
        self.yaml = yaml
        self.yaml_reference = self.get_object_in_yaml()

        self.plan_only = plan_only
        self.is_same_org_deploy = is_same_org_deploy

        self.overrider = AttributeOverrider(self.type)

        try:
            self.data = await read_json(self.path)
        except Exception:
            raise PathNotFoundException(
                f"Error while initializing object with path: {self.path}"
            )
        self.client = client

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
        remote_object = await self.client._http_client.fetch_one(
            self.type, remote_object_id
        )
        return remote_object.get("modified_at", "") == last_deploy_timestamp

    def update_targets(self, results):
        # asyncio.gather returns results in the same order as they were put in
        for index, (result, target) in enumerate(zip(results, self.targets)):
            target.id = result.get("id", None)
            target.data = result
            self.yaml_reference["targets"][index]["id"] = target.id

    # TODO: rename target_object (misleading)
    async def upload(self, target_object: dict, target: Target):
        if target.id:
            return await self.update_remote(target_object=target_object, target=target)
        else:
            return await self.create_remote(target_object=target_object, target=target)

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

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )
            return result
        except Exception as e:
            display_error(
                f'Error while creating {self.display_type}  "{self.name} ({self.id})" ^',
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

                # TODO: timestamp checking
                # if not await self.check_modified_timestamps_equal(
                #     last_deploy_timestamp, target.id
                # ):
                #     display_warning(f"Remote timestamp of ")
                # If timestamps differ, show warning and let the user end the plan (to go review/sync changes)
            else:
                # TODO: check again to eliminate race conditions
                # Should remember if the user said "overwrite" in the step above

                result = await self.client._http_client.update(
                    self.type, id_=target.id, data=target_object
                )

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.UPDATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )
            return result
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type}: "{self.name} ({self.id})" -> "{target.id} ^',
                e,
            )
            self.deploy_failed = True
            return {}

    async def implicit_override_targets(self, lookup_table: LookupTable):
        for target_index, target in enumerate(self.targets):
            override_source_data_copy = deepcopy(self.data)
            override_target_copy = deepcopy(target)

            self.remove_override_irrelevant_props(override_source_data_copy)
            self.remove_override_irrelevant_props(override_target_copy.data)

            self.overrider.replace_ids_in_target_object(
                target=override_target_copy,
                lookup_table=lookup_table,
                target_object_index=target_index,
                num_targets=len(self.targets),
            )

            diff = self.overrider.create_override_diff(
                override_source_data_copy, override_target_copy.data
            )
            if not diff:
                return

            if self.plan_only:
                colorized_diff = self.overrider.parse_diff(diff)
                message = f"Attribute override: {self.display_type} {self.create_source_to_target_string(override_target_copy.data)}:\n{colorized_diff}"
                pprint(Panel(message))
            else:
                # Update only objects where there was a difference after override
                await self.update_remote(
                    target_object=override_target_copy.data, target=target
                )

    # TODO: compile lists for each object?
    # TODO: add more attributes (e.g., modified_by, modified_at)
    def remove_override_irrelevant_props(self, data):
        # These attribute either should not be compared or were already replaced via replace_dependency_url()
        data.pop("modified_by", None)
        data.pop("modified_at", None)
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
                data.pop("workflows", None)
                data.pop("counts", None)
                data.pop("workspace", None)
                data.pop("inbox", None)
                data.pop("schema", None)
                data.pop("hooks", None)
                data.pop("webhooks", None)


class EmptyObjectRelease(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int = None
    name: str = ""
    type: Resource = "no-type"
    base_path: Path = None

    async def initialize(**kwargs): ...

    async def deploy(): ...
