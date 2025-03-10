from typing import Annotated
from pydantic import BaseModel, BeforeValidator


# TODO: reorganize for both upload/download
class Subdirectory(BaseModel):
    name: str
    regex: str = None
    include: bool = False
    object_ids: set[int] = []


def create_subdir_configuration(subdirs):
    return {
        name: Subdirectory(name=name, **value if value else {})
        for name, value in subdirs.items()
    }


SubdirectoriesDict = Annotated[
    dict[str, Subdirectory],
    BeforeValidator(lambda subdirs: create_subdir_configuration(subdirs)),
]
