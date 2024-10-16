from typing import Annotated
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.common.read_write import read_json
from rich import print
import json
import re
from rich.panel import Panel


from anyio import Path
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import display_error
from project_rossum_deploy.utils.functions import templatize_name_id

type LookupTable = dict[int, list[int]]
IMPLICIT_OVERRIDE_KEYS = ["settings", "metadata"]


class Target(BaseModel):
    id: int | None = Field(
        validation_alias=AliasChoices("id", "target_id"), default=None
    )
    data: dict = {}
    attribute_override: dict = {}


def convert_int_id_to_class(model, val):
    if not isinstance(val, dict):
        return model(id=None)
    return val


TargetWithDefault = Annotated[
    Target, BeforeValidator(lambda x: convert_int_id_to_class(Target, x))
]


class ObjectRelease(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource
    base_path: str = None
    yaml_reference: dict = None
    data: dict = None
    client: ElisAPIClient = None

    targets: list[TargetWithDefault] = []

    async def initialize(
        self, yaml: DeployYaml, client: ElisAPIClient, source_dir_path: Path
    ):
        if not self.base_path:
            self.base_path = source_dir_path
        self.yaml_reference = yaml.get_object_in_yaml(self.type.value, self.id)
        # TODO: error handling of missing objects
        self.data = await read_json(self.path)
        self.client = client

    async def plan(self): ...

    async def deploy(self): ...

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
        if self.type in [Resource.Inbox]:
            return self.type.value[:-2]
        return self.type.value[:-1]

    async def upload(self, object: dict, target: Target):
        if target.id:
            return await self.update_remote(object=object, target=target)
        else:
            return await self.create_remote(object=object, target=target)

    # Target is provided so that subclasses can use it (even if this basic method does not)
    async def create_remote(self, object: dict, target: Target = None):
        try:
            result = await self.client._http_client.create(self.type, object)
            print(
                f'Released (created) {self.display_type} "{object['name']} ({object['id']})" -> "{result['name']} ({result['id']})".'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while creating {self.display_type}  "{object['name']} ({object['id']})" ^',
                e,
            )
            return {}

    async def update_remote(self, object: dict, target: Target):
        try:
            result = await self.client._http_client.update(
                self.type, id_=target.id, data=object
            )
            print(
                f'Released (updated) {self.display_type} "{object['name']} ({object['id']})" -> "{result['name']} ({result['id']})".'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type} "{object['name']} ({object['id']})" -> "{target.id} ^',
                e,
            )
            return {}

    def implicit_override(self, lookup_table: LookupTable):
        for target_index, target in enumerate(self.targets):
            for key in IMPLICIT_OVERRIDE_KEYS:
                if key not in target:
                    continue

                self.replace_ids_in_target_subobject(
                    target_id=target.id,
                    subobject=target.data[key],
                    lookup_table=lookup_table,
                    target_index=target_index,
                    num_targets=len(self.targets),
                )

    def replace_ids_in_target_subobject(
        self,
        target_id: int,
        subobject: dict,
        lookup_table: dict,
        object_index: int,
        num_targets: int,
    ):
        stringified_dict = json.dumps(subobject)
        for source_id, target_ids in lookup_table.items():
            source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
            # This ID from source was not found in the subobject
            if not re.search(source_id_regex, stringified_dict):
                continue

            basic_error_message = f"Could not override source_id '{source_id}' to its target equivalent in {self.type.value} '{target_id}'."
            if not target_ids:
                print(
                    Panel(
                        f"{basic_error_message} No target IDs found.",
                        style="yellow",
                    ),
                )
                continue
            # Using lambdas for sub() because of quotes inside strings
            # N:N objects -> objects are referenced in pairs
            elif num_targets == len(target_ids):
                stringified_dict = re.sub(
                    source_id_regex,
                    lambda m: str(target_ids[object_index])
                    if m[0] == str(source_id)
                    else m[0],
                    stringified_dict,
                )
            # N:1 objects -> everything should be mapped to the first target ID
            else:
                stringified_dict = re.sub(
                    source_id_regex,
                    lambda m: str(target_ids[0]) if m[0] == str(source_id) else m[0],
                    stringified_dict,
                )
                if len(target_ids) != 1:
                    print(
                        Panel(
                            f"For overriding source_id '{source_id}' in {self.type.value} '{target_id}', There are multiple target IDs that could be assigned. The first one was used.",
                            style="yellow",
                        ),
                    )

        return json.loads(stringified_dict)
