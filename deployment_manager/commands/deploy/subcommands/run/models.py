from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Annotated, Union
import uuid
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field, field_validator

from rossum_api.domain_logic.resources import Resource

# { source_id: { Resource.Hooks: [Target1, Target2] } }
type LookupTable = dict[int, dict[Resource, list[Target]]]
# { Resource.Hooks: { target_id: source_id } }
type ReverseLookupTable = dict[Resource, dict[str, int]]


if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
        DeployObject,
    )


class Target(BaseModel):
    id: Union[str, None] = Field(
        default_factory=lambda: str(uuid.uuid4()),
    )
    attribute_override: dict = {}

    # Computed
    index: int = 0
    parent_object: "DeployObject" = None
    exists_on_remote: bool = False

    # Replaced static fields (attribute override, etc.) but reference IDs are still for source
    pre_reference_replace_data: dict | None = None
    # Includes reference IDs translated from source to target including dummy IDs
    visualized_plan_data: dict | None = None
    # Includes reference IDs translated from source to target but not dummy IDs
    first_deploy_data: dict | None = None
    # Second deploy that might have reference IDs that did not yet exist during the first deploy
    second_deploy_data: dict | None = None

    # Data returned by Elis API after first/second deploy
    data_from_remote: dict | None = None
    # Data that will be stored in deploy_state
    last_applied_data: dict | None = None

    @property
    def display_label(self):
        return f'"[green]{self.pre_reference_replace_data.get('name', 'no-name')}[/green] ([purple]{self.pre_reference_replace_data.get('id', 'no-id')}[/purple])"'

    @field_validator("id", mode="before")
    @classmethod
    def fill_id_if_none(cls, v):
        return str(uuid.uuid4()) if v is None else v

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v):
        if isinstance(v, int):
            return str(v)
        return v

    def model_post_init(self, __context):
        self.exists_on_remote = self._is_real_id(self.id)

    def create_dummy_id_from_parent(self):
        # self.id = f"<NEW COPY>[{self.index}]([yellow]{self.parent_object.name}[/yellow] - [purple]{self.parent_object.id}[/purple])"
        self.id = f"<NEW COPY>[{self.index}]({self.parent_object.name} - {self.parent_object.id})"

    def update_after_first_create(self):
        self.id = self.data_from_remote["id"]
        self.exists_on_remote = True

    @staticmethod
    def _is_real_id(id_val: str) -> bool:
        try:
            # Real IDs are numeric strings; dummy UUIDs have hyphens
            int(id_val)
            return True
        except (ValueError, TypeError):
            return False


def convert_int_id_to_class(model, val):
    if not isinstance(val, dict):
        return model(id=None)
    return val


TargetWithDefault = Annotated[
    Target, BeforeValidator(lambda x: convert_int_id_to_class(Target, x))
]


class SubObjectException(Exception): ...


class PathNotFoundException(Exception): ...


class TimestampMismatchException(Exception): ...


class NonExistentObjectException(Exception): ...


class DeployException(Exception): ...
