from anyio import Path
import pytest
import io


from project_rossum_deploy.commands.download.saver import WorkspaceSaver
from project_rossum_deploy.commands.download.subdirectory import Subdirectory
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.functions import templatize_name_id


@pytest.mark.asyncio
async def test_workspace_path(
    workspace_json: dict, tmp_path: Path, test_subdir: Subdirectory
):
    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )
    object_path = workspace_saver.construct_object_path(
        subdir=test_subdir, object=workspace_json
    )
    assert object_path == (
        tmp_path
        / test_subdir.name
        / "workspaces"
        / templatize_name_id(workspace_json["name"], workspace_json["id"])
        / "workspace.json"
    )


@pytest.mark.asyncio
async def single_single_subdir_assignment(
    workspace_json: dict, tmp_path: Path, test_subdir: Subdirectory
):
    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )

    subdir = workspace_saver.find_subdir_of_object(workspace_json)

    assert subdir == test_subdir


@pytest.mark.asyncio
async def test_regex_subdir_assignment(
    workspace_json: dict,
    tmp_path: Path,
    test_subdir: Subdirectory,
    prod_subdir: Subdirectory,
):
    workspace_json["name"] = "WS [PROD]"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir, prod_subdir],
    )

    subdir = workspace_saver.find_subdir_of_object(workspace_json)

    assert subdir == prod_subdir


@pytest.mark.asyncio
async def test_unknown_subdir(
    workspace_json: dict,
    tmp_path: Path,
    test_subdir: Subdirectory,
    prod_subdir: Subdirectory,
):
    workspace_json["name"] = "WS [DEV]"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir, prod_subdir],
    )

    subdir = workspace_saver.find_subdir_of_object(workspace_json)

    assert subdir is None


@pytest.mark.asyncio
async def test_save_workspace_fresh(
    workspace_json: dict, tmp_path: Path, test_subdir: Subdirectory
):
    test_subdir.regex = "TEST"
    workspace_json["name"] = "WS [TEST]"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )
    await workspace_saver.save_downloaded_objects()

    object_path = workspace_saver.construct_object_path(
        subdir=test_subdir, object=workspace_json
    )
    saved_object = await read_json(object_path)
    assert saved_object == workspace_json


@pytest.mark.asyncio
async def test_save_workspace_ignores_unincluded_subdir(
    workspace_json, tmp_path, test_subdir: Subdirectory
):
    workspace_json["name"] = "WS [TEST]"
    test_subdir.include = False

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )
    await workspace_saver.save_downloaded_objects()

    # Make sure the subdir was recognized
    assert workspace_json not in workspace_saver.objects_without_subdir

    object_path = workspace_saver.construct_object_path(
        subdir=test_subdir, object=workspace_json
    )
    assert not await object_path.exists()


# Not working with CLI input...
@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_subdir_from_user(
    workspace_json: dict,
    tmp_path: Path,
    test_subdir: Subdirectory,
    prod_subdir: Subdirectory,
    monkeypatch,
):
    workspace_json["name"] = "WS [DEV]"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir, prod_subdir],
    )

    workspace_saver.find_subdir_of_object(workspace_json)

    # CLI input
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    await workspace_saver.handle_objects_without_subdir()

    object_path = workspace_saver.construct_object_path(
        subdir=test_subdir, object=workspace_json
    )
    saved_object = await read_json(object_path)
    assert saved_object == workspace_json
