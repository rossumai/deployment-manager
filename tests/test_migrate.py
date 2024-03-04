import io
from anyio import Path
import click
import jmespath
import pytest

from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.download.download import (
    download_organization_combined_source_target,
)
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import find_mapping_of_object
from project_rossum_deploy.commands.migrate.migrate import migrate_project
from project_rossum_deploy.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
    settings,
)
from project_rossum_deploy.utils.functions import (
    extract_sources_targets,
    extract_flat_lookup_table,
    read_json,
    templatize_name_id,
    write_json,
)
from tests.utils.compare import (
    ensure_hooks_have_same_dependency_graph,
    ensure_source_objects_have_target_counter_part,
)
from tests.utils.functions import create_self_targetting_org, delete_migrated_objects
from tests.conftest import (
    base_url,
    username,
    password,
    target_username,
    target_password,
    target_base_url,
)


@pytest.mark.asyncio
async def test_migrate_fails_without_specific_org_target(
    client: ElisAPIClient, tmp_path
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        with pytest.raises(click.ClickException):
            await migrate_project(client=client, org_path=tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_creates_new_objects_in_target(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        settings.IS_PROJECT_IN_SAME_ORG = True
        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y\ny"))
        await migrate_project(client=client, org_path=tmp_path)

        # check each object in mapping has a target and a json file in target dir
        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
        await ensure_hooks_have_same_dependency_graph(mapping, tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_works_with_attribute_override(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined_source_target(client, tmp_path)
    await create_self_targetting_org(tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        QUEUE_IDS_OVERRIDE_PATH = "settings.configurations[*].queue_ids"

        hook_mappings = mapping["organization"]["hooks"]
        for hook_mapping in hook_mappings:
            if hook_mapping["name"] == "Master Data Hub":
                overriden_hook = hook_mapping
                overriden_hook["attribute_override"] = {
                    QUEUE_IDS_OVERRIDE_PATH: ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
                }
                break

        overriden_schema = mapping["organization"]["schemas"][0]
        overriden_schema["attribute_override"] = {
            "name": f"{ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD} - PROD"
        }

        await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

        settings.IS_PROJECT_IN_SAME_ORG = True
        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y\ny"))
        await migrate_project(client=client, org_path=tmp_path)

        # check each object in mapping has a target and a json file in target dir
        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
        await ensure_hooks_have_same_dependency_graph(mapping, tmp_path)

        # Check dynamic name of schema with attribute override
        overriden_schema_mapping_after_migration = find_mapping_of_object(
            mapping["organization"]["schemas"], overriden_schema["id"]
        )

        overriden_schema_name = f'{overriden_schema["name"]} - PROD'
        target_schema_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "schemas"
            / f"{templatize_name_id(overriden_schema_name, overriden_schema_mapping_after_migration['target_object'])}.json"
        )
        assert await target_schema_path.exists()

        # Check dynamic queue_ids in hook with attribute override
        overriden_hook_mapping_after_migration = find_mapping_of_object(
            mapping["organization"]["hooks"], overriden_hook["id"]
        )
        target_hook_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "hooks"
            / f"{templatize_name_id(overriden_hook_mapping_after_migration['name'], overriden_hook_mapping_after_migration['target_object'])}.json"
        )
        assert await target_schema_path.exists()

        source_hook_path = (
            tmp_path
            / settings.SOURCE_DIRNAME
            / "hooks"
            / f"{templatize_name_id(overriden_hook_mapping_after_migration['name'], overriden_hook_mapping_after_migration['id'])}.json"
        )
        source_hook = await read_json(source_hook_path)
        migrated_hook = await read_json(target_hook_path)
        lookup_table = extract_flat_lookup_table(mapping)
        source_queue_ids = jmespath.search(QUEUE_IDS_OVERRIDE_PATH, source_hook)

        assert jmespath.search(QUEUE_IDS_OVERRIDE_PATH, migrated_hook)[0] == list(
            map(lambda source_queue_id: lookup_table[source_queue_id][0], source_queue_ids[0])
        )
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_twice_is_idempotent(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_ignores_designated_object(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined_source_target(client, tmp_path)
    await create_self_targetting_org(tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        ignored_hook_mapping = mapping["organization"]["hooks"][0]
        ignored_hook_mapping["ignore"] = True
        await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        post_migration_ignored_hook_mapping = find_mapping_of_object(
            mapping["organization"]["hooks"], ignored_hook_mapping["id"]
        )

        assert post_migration_ignored_hook_mapping == ignored_hook_mapping

        source_hook_paths = [
            path
            async for path in (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
            if path.suffix != ".py"
        ]
        target_hook_paths = [
            path
            async for path in (tmp_path / settings.TARGET_DIRNAME / "hooks").iterdir()
            if path.suffix != ".py"
        ]
        assert len(source_hook_paths) == len(target_hook_paths) + 1
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_adds_new_object_on_second_run(
    client: ElisAPIClient, tmp_path, monkeypatch
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

        schema = await client.create_new_schema(
            {"name": "new source schema", "content": []}
        )
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await download_organization_combined_source_target(client=client, org_path=tmp_path)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

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
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)
    try:
        await create_self_targetting_org(tmp_path)

        # Confirm configuration overwriting
        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

        some_hook_path = await anext(
            (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
        )
        some_hook = await read_json(some_hook_path)
        some_hook["active"] = False
        await write_json(some_hook_path, some_hook)

        monkeypatch.setattr("sys.stdin", io.StringIO("y"))
        await migrate_project(client=client, org_path=tmp_path)

        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        some_hook_in_mapping = find_mapping_of_object(
            mapping["organization"]["hooks"], some_hook["id"]
        )
        target_hook_after_migration_path = (
            tmp_path
            / settings.TARGET_DIRNAME
            / "hooks"
            / f"{templatize_name_id(some_hook['name'], some_hook_in_mapping['target_object'])}.json"
        )
        assert await target_hook_after_migration_path.exists()
        target_hook_after_migration = await read_json(target_hook_after_migration_path)
        assert not target_hook_after_migration["active"]
    finally:
        # Cleanup
        await delete_migrated_objects(sources, client)


@pytest.mark.asyncio
async def test_migrate_creates_new_objects_in_different_org(
    client: ElisAPIClient,
    target_client: ElisAPIClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)

    organizations = [org async for org in target_client.list_all_organizations()]
    if not len(organizations):
        raise Exception("No target organization found.")
    mapping["organization"]["target_object"] = organizations[0].id
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)
    sources, _ = extract_sources_targets(mapping)

    try:
        settings.SOURCE_API_BASE = base_url
        settings.SOURCE_USERNAME = username
        settings.SOURCE_PASSWORD = password
        settings.TARGET_API_BASE = target_base_url
        settings.TARGET_USERNAME = target_username
        settings.TARGET_PASSWORD = target_password
        users = [user async for user in target_client.list_all_users()]
        monkeypatch.setattr("sys.stdin", io.StringIO(f"{users[0].id}\ny"))
        await migrate_project(client=target_client, org_path=tmp_path)

        # check each object in mapping has a target and a json file in target dir
        mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
        await ensure_source_objects_have_target_counter_part(mapping, tmp_path)
    finally:
        # Cleanup
        await delete_migrated_objects(sources, target_client)
