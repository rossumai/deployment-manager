import io
import click
import pytest

from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.download.download import download_organization_combined
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import find_mapping_of_object
from project_rossum_deploy.commands.migrate.migrate import migrate_project
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    extract_sources_targets,
    read_json,
    templatize_name_id,
    write_json,
)
from tests.utils.compare import (
    ensure_hooks_have_same_dependency_graph,
    ensure_source_objects_have_target_counter_part,
)
from tests.utils.functions import create_self_targetting_org, delete_migrated_objects


# TEST: migrate to a different org


@pytest.mark.asyncio
async def test_migrate_fails_without_specific_org_target(
    client: ElisAPIClient, tmp_path
):
    await download_organization_combined(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        with pytest.raises(click.ClickException):
            await migrate_project(
                mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
            )
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_creates_new_objects_in_target(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        # check each object in mapping has a target and a json file in target dir
        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
        await ensure_hooks_have_same_dependency_graph(mapping, tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_twice_is_idempotent(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_ignores_designated_object(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined(client, tmp_path)
    await create_self_targetting_org(tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        ignored_hook_mapping = mapping["organization"]["hooks"][0]
        ignored_hook_mapping["ignore"] = True
        await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        post_migration_ignored_hook_mapping = find_mapping_of_object(
            mapping["organization"]["hooks"], ignored_hook_mapping["id"]
        )

        assert post_migration_ignored_hook_mapping == ignored_hook_mapping

        source_hook_paths = [
            path
            async for path in (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
        ]
        target_hook_paths = [
            path
            async for path in (tmp_path / settings.TARGET_DIRNAME / "hooks").iterdir()
        ]
        assert len(source_hook_paths) == len(target_hook_paths) + 1
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_adds_new_object_on_second_run(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        schema = await client.create_new_schema(
            {"name": "new source schema", "content": []}
        )
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await download_organization_combined(client=client, org_path=tmp_path)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        source_schema_in_mapping = find_mapping_of_object(
            mapping["organization"]["schemas"], schema.id
        )
        target_schema_id = source_schema_in_mapping["target_object"]
        assert target_schema_id

        target_schema_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "schemas"
            / f"{templatize_name_id(schema.name, target_schema_id)}.json"
        )
        assert await target_schema_path.exists()
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_updates_object_on_second_run(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        some_hook_path = await anext(
            (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
        )
        some_hook = await read_json(some_hook_path)
        some_hook["active"] = False
        await write_json(some_hook_path, some_hook)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(
            mapping=settings.MAPPING_FILENAME, client=client, org_path=tmp_path
        )

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        some_hook_in_mapping = find_mapping_of_object(
            mapping["organization"]["hooks"], some_hook["id"]
        )
        target_hook_after_migration_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "hooks"
            / f"{templatize_name_id(some_hook['name'], some_hook_in_mapping['target'])}.json"
        )
        assert await target_hook_after_migration_path.exists()
        target_hook_after_migration = await read_json(target_hook_after_migration_path)
        assert not target_hook_after_migration["active"]
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)
