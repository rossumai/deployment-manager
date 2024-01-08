import asyncio
import filecmp
from anyio import Path

from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.utils.functions import read_json


async def compare_projects(project_one_path: Path, project_two_path: Path):
    mapping_one, mapping_two = await read_mapping(
        project_one_path / "mapping.yaml"
    ), await read_mapping(project_two_path / "mapping.yaml")
    assert mapping_one == mapping_two

    org_one, org_two = await asyncio.gather(
        *[
            read_json(project_one_path / "organization.json"),
            read_json(project_two_path / "organization.json"),
        ]
    )
    assert org_one == org_two

    source_one_path, source_two_path = (
        project_one_path / "source",
        project_two_path / "source",
    )

    assert are_dir_trees_equal(source_one_path, source_two_path)

    target_one_path, target_two_path = (
        project_one_path / "target",
        project_two_path / "target",
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
