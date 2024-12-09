from typing import Annotated
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field


type LookupTable = dict[int, list[int]]


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
