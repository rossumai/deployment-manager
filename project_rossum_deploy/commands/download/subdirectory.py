from typing import Annotated
from pydantic import BaseModel, BeforeValidator


class Subdirectory(BaseModel):
    name: str
    regex: str = None
    download: bool = False
    object_ids: set[int] = None


def create_subdir_configuration(subdirs):
    return {
        name: Subdirectory(name=name, **value if value else {})
        for name, value in subdirs.items()
    }


SubdirectoriesDict = Annotated[
    dict[str, Subdirectory],
    BeforeValidator(lambda subdirs: create_subdir_configuration(subdirs)),
]
