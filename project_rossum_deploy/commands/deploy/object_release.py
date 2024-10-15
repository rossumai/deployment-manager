from typing import Annotated
from project_rossum_deploy.commands.deploy.helpers import DeployYaml
from project_rossum_deploy.common.read_write import read_json
from rich import print

from anyio import Path
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import display_error
from project_rossum_deploy.utils.functions import templatize_name_id


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
        return self.type.value[:-1]

    async def upload(self, object: dict, target: Target):
        if target.id:
            return await self.update_remote(object=object, target=target)
        else:
            return await self.create_remote(object=object, target=target)

    # Target is provided so that subclasses can use it (even if this basic method does not)
    async def create_remote(self, object: dict, target: Target):
        try:
            result = await self.client._http_client.create(self.type, object)
            print(
                f'Released (created) {self.display_type} "{object['name']} ({object['id']})" -> "{result['id']}".'
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
                f'Released (updated) {self.display_type} "{object['id']}" -> "{result['id']}".'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type} "{object['name']} ({object['id']})" -> "{target.id} ^',
                e,
            )
            return {}
