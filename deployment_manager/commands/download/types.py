# types.py - Shared Interfaces to Break Circular Imports
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel
import re
from anyio import Path
import questionary
from rossum_api.api_client import Resource

from rich import print as pprint
from deployment_manager.commands.download.subdirectory import (
    Subdirectory,
)


if TYPE_CHECKING:
    from deployment_manager.commands.download.directory import (
        DownloadOrganizationDirectory,
    )


# TODO: error handling? Level of objects vs level of object ?
class ObjectSaver(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    parent_dir_reference: Optional["DownloadOrganizationDirectory"] = None
    type: Resource
    base_path: Path
    subdirs: list[Subdirectory] = []
    objects: list[dict]
    changed_files: list
    download_all: bool = False
    skip_objects_without_subdir: bool = False

    objects_without_subdir: list[dict] = []
    subdirs_by_object_id: dict[int, str] = {}

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    def display_label(self, name, id):
        return f'"[green]{name}[/green] ([purple]{id}[/purple])"'

    async def save_downloaded_objects(self):
        for object in self.objects:
            subdir = self.find_subdir_of_object(object)
            if not subdir:
                self.objects_without_subdir.append(object)
                continue
            # The subdir should not be pulled, disregard the current object
            elif not subdir.include:
                continue

            self.subdirs_by_object_id[object["id"]] = subdir
            await self.save_downloaded_object(object, subdir)

        await self.handle_objects_without_subdir()

    async def handle_objects_without_subdir(self):
        if not self.objects_without_subdir or self.skip_objects_without_subdir:
            return

        for object in self.objects_without_subdir:
            subdir = await self.get_subdir_from_user(object)
            self.subdirs_by_object_id[object["id"]] = subdir
            await self.save_downloaded_object(object, subdir)

    async def get_subdir_from_user(self, object):
        subdir_choices = [
            questionary.Choice(title=subdir.name, value=subdir)
            for subdir in self.subdirs
        ]
        pprint(
            f"{self.display_type} {self.display_label(object['name'], object['id'])}",
            end=" ",
        )
        return await questionary.select(
            "- select subdir:",
            choices=subdir_choices,
        ).ask_async()

    def construct_object_path(self, subdir: Subdirectory, object: dict) -> Path: ...

    async def save_downloaded_object(self): ...

    def find_subdir_of_object(self, object: dict):
        if len(self.subdirs) == 1:
            return self.subdirs[0]

        for subdir in self.subdirs:
            if object["id"] in subdir.object_ids:
                return subdir

        for subdir in self.subdirs:
            if not subdir.regex:
                continue
            subdir_regex = re.compile(subdir.regex)
            if subdir_regex.findall(object["name"]):
                return subdir

        return None
