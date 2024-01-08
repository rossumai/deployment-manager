import asyncio
import dataclasses
import filecmp
from anyio import Path

from rossum_api.models import Schema, Hook, Workspace, Queue, Inbox, Organization

from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.utils.functions import read_json
from project_rossum_deploy.utils.consts import settings


async def compare_projects(project_one_path: Path, project_two_path: Path):
    # Compare mapping and organization files manually because the root folders could
    # include more files where we don't want comparision (e.g. .env)
    mapping_one, mapping_two = await read_mapping(
        project_one_path / settings.MAPPING_FILENAME
    ), await read_mapping(project_two_path / settings.MAPPING_FILENAME)
    assert mapping_one == mapping_two

    org_one, org_two = await asyncio.gather(
        *[
            read_json(project_one_path / "organization.json"),
            read_json(project_two_path / "organization.json"),
        ]
    )
    assert org_one == org_two

    source_one_path, source_two_path = (
        project_one_path / settings.SOURCE_DIRNAME,
        project_two_path / settings.SOURCE_DIRNAME,
    )

    assert are_dir_trees_equal(source_one_path, source_two_path)

    target_one_path, target_two_path = (
        project_one_path / settings.TARGET_DIRNAME,
        project_two_path / settings.TARGET_DIRNAME,
    )

    # Both should either exist or neither
    assert (await target_one_path.exists() and await target_two_path.exists()) or (
        not await target_one_path.exists() and not await target_two_path.exists()
    )

    if await target_one_path.exists():
        assert are_dir_trees_equal(target_one_path, target_two_path)


# https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi
def are_dir_trees_equal(dir1: Path, dir2: Path):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """

    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = dir1 / common_dir
        new_dir2 = dir2 / common_dir
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


async def ensure_downloaded_object(
    tmp_path: Path,
    expected_path: Path,
    object_type: str,
    reference: Organization | Workspace | Queue | Hook | Schema | Inbox,
):
    """Checks that the project files include the specified object"""
    assert await expected_path.exists()
    assert dataclasses.asdict(reference) == await read_json(expected_path)

    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)

    if settings.TARGET_DIRNAME not in str(expected_path):
        found = False
        for ws_mapping in mapping["organization"][object_type]:
            if ws_mapping["id"] == reference.id:
                found = True
                break
        assert found
