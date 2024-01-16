import asyncio
import dataclasses
import filecmp
from anyio import Path

from rossum_api.models import Schema, Hook, Workspace, Queue, Inbox, Organization

from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    extract_id_from_url,
    extract_source_target_pairs,
    extract_sources_targets,
    read_json,
    templatize_name_id,
)
from project_rossum_deploy.utils.consts import settings


async def compare_mappings(project_one_path: Path, project_two_path: Path):
    mapping_one, mapping_two = await read_mapping(
        project_one_path / settings.MAPPING_FILENAME
    ), await read_mapping(project_two_path / settings.MAPPING_FILENAME)

    assert mapping_one == mapping_two


async def compare_projects(project_one_path: Path, project_two_path: Path):
    # Compare mapping and organization files manually because the root folders could
    # include more files where we don't want comparision (e.g. .env)
    await compare_mappings(project_one_path, project_two_path)

    org_one, org_two = await asyncio.gather(
        *[
            read_json(project_one_path / settings.SOURCE_DIRNAME / "organization.json"),
            read_json(project_two_path / settings.SOURCE_DIRNAME / "organization.json"),
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
    reference: Organization | Workspace | Queue | Hook | Schema | Inbox = None,
):
    """Checks that the project files include the specified object"""
    assert await expected_path.exists()
    saved_json_object = await read_json(expected_path)
    if reference:
        assert dataclasses.asdict(reference) == saved_json_object
        object_id = reference.id
    else:
        object_id = saved_json_object["id"]

    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, targets = extract_sources_targets(mapping)
    if settings.TARGET_DIRNAME in str(expected_path):
        assert object_id in targets[object_type]
    else:
        assert object_id in sources[object_type]


async def ensure_source_objects_have_target_counter_part(mapping: dict, tmp_path: Path):
    """Check each object in mapping has a target and a json file in target dir."""
    source_target_pairs = extract_source_target_pairs(mapping)
    for object_type, pairs in source_target_pairs.items():
        for target in pairs.values():
            assert target
        if object_type == "queues" or object_type == "inboxes":
            continue

        targets_with_json = []
        # Skip checking queues and inboxes because of their nested nature
        target_dir: Path = tmp_path / settings.TARGET_DIRNAME / object_type
        async for path in target_dir.iterdir():
            targets_with_json.append(detemplatize_name_id(path.stem)[1])

        for target in pairs.values():
            assert target in targets_with_json


async def ensure_hooks_have_same_dependency_graph(mapping: dict, tmp_path: Path):
    source_target_pairs = extract_source_target_pairs(mapping)
    async for source_hook_path in (
        tmp_path / settings.SOURCE_DIRNAME / "hooks"
    ).iterdir():
        source_hook = await read_json(source_hook_path)

        target_hook_id = source_target_pairs["hooks"][source_hook["id"]]
        target_hook_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "hooks"
            / f'{templatize_name_id(source_hook["name"], target_hook_id)}.json'
        )
        target_hook = await read_json(target_hook_path)

        remapped_source_hook_ids = []
        for hook_url in source_hook["run_after"]:
            hook_id = extract_id_from_url(hook_url)
            remapped_source_hook_ids.append(
                hook_url.replace(
                    str(hook_id), str(source_target_pairs["hooks"][hook_id])
                )
            )
        source_hook["run_after"] = remapped_source_hook_ids
        assert source_hook["run_after"] == target_hook["run_after"]
