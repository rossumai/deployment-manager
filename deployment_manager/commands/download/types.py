# types.py - Shared Interfaces to Break Circular Imports
import subprocess
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel
import re
from anyio import Path
import questionary

from deployment_manager.commands.download.helpers import get_pull_decision
from deployment_manager.common.git import PullStrategy
from deployment_manager.common.read_write import write_json
from deployment_manager.utils.consts import display_warning
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

    async def save_downloaded_object(self, object: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir, object)
        if not object_path:
            return
        if self.download_all:
            await self.save(object, object_path)
            return

        pull_strategy = await get_pull_decision(
            object_path, object, self.changed_files, self.parent_dir_reference
        )

        if pull_strategy == PullStrategy.overwrite:
            await self.save(object, object_path)
            return

        if pull_strategy == PullStrategy.skip:
            return

        if pull_strategy == PullStrategy.merge:
            await self.merge(object, object_path)

    async def save(self, hook, object_path) -> list[Path] | None:
        await write_json(
            object_path,
            hook,
            self.type,
            log_message=f"Pulled {self.display_type} {object_path}",
        )

    async def merge(self, object, object_path):
        # stash, pull, commit, stash pop
        subprocess.run(["git", "stash", "push", str(object_path)], capture_output=True, text=True, check=True)
        additional_paths = await self.save(object, object_path)
        if not additional_paths:
            additional_paths = []
        elif not isinstance(additional_paths, list):
            additional_paths = [additional_paths]

        for file in [object_path] + additional_paths:
            subprocess.run(["git", "add", file], capture_output=True, text=True, check=True)
        subprocess.run(["git", "commit", "-m", f"commit {object_path}"], capture_output=True, text=True, check=True)
        merge_result = subprocess.run(["git", "stash", "pop"], capture_output=True, text=True, check=False)
        if merge_result.returncode != 0:
            display_warning(
                "There is a merge conflict while pulling remote to your local changes. Solve it using git before continuing. Watch out that the 'local' and 'remote' changes are swapped in this situation.")
            while True:
                await questionary.confirm(
                    "Press enter after solving the conflict", default=True
                ).ask_async()
                status = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
                if "Unmerged paths" in status.stdout:
                    display_warning("There are still unsolved changes.")
                else:
                    break

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
