from typing import Annotated
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field
from rossum_api.api_client import Resource

type LookupTable = dict[int, dict[Resource, list[int]]]


class Target(BaseModel):
    id: int | None = Field(
        validation_alias=AliasChoices("id", "target_id"), default=None
    )
    data: dict = {}
    attribute_override: dict = {}
    index: int = 0


def convert_int_id_to_class(model, val):
    if not isinstance(val, dict):
        return model(id=None)
    return val


TargetWithDefault = Annotated[
    Target, BeforeValidator(lambda x: convert_int_id_to_class(Target, x))
]


class SubObjectException(Exception): ...
