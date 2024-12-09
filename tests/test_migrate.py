import io
import pytest

import pytest_asyncio
from rossum_api import ElisAPIClient

from deployment_manager.commands.download.download import (
    download_organization_combined_source_target,
    download_organizations_separate,
)
from deployment_manager.commands.migrate.helpers import traverse_mapping
from deployment_manager.common.mapping import (
    extract_sources_targets,
    find_mapping_of_object,
    read_mapping,
    write_mapping,
)
from deployment_manager.commands.migrate.migrate import migrate_project
from deployment_manager.common.read_write import read_json, write_json
from deployment_manager.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    MAPPING_SELECTED_ATTRIBUTE,
    settings,
)
from deployment_manager.utils.functions import templatize_name_id
from tests.utils.compare import (
    ensure_hooks_have_same_dependency_graph,
    ensure_source_objects_have_target_counter_part,
)

from tests.utils.functions import create_self_targetting_org, delete_migrated_objects


@pytest_asyncio.fixture(scope="function")
async def same_org_migration_path(client: ElisAPIClient, tmp_path):
    await download_organization_combined_source_target(client, tmp_path)
    await create_self_targetting_org(tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    sources, _ = extract_sources_targets(mapping)

    yield tmp_path

    await delete_migrated_objects(sources, client)
    await create_self_targetting_org(tmp_path, undo=True)


@pytest_asyncio.fixture(scope="function")
async def cross_org_migration_path(
    client: ElisAPIClient, target_client: ElisAPIClient, tmp_path
):
    await download_organization_combined_source_target(client, tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)

    organizations = [org async for org in target_client.list_all_organizations()]
    if not len(organizations):
        raise Exception("No target organization found.")

    mapping["organization"]["targets"][0] = {"target_id": organizations[0].id}
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)
    sources, _ = extract_sources_targets(mapping)

    await download_organizations_separate(tmp_path)

    yield tmp_path

    await delete_migrated_objects(sources, target_client)


@pytest.mark.asyncio
async def test_migrate_creates_new_objects_in_target(
    client: ElisAPIClient, same_org_migration_path
):
    await migrate_project(client=client, org_path=same_org_migration_path)

    # check each object in mapping has a target and a json file in target dir
    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)
    await ensure_source_objects_have_target_counter_part(
        mapping, same_org_migration_path
    )
    await ensure_hooks_have_same_dependency_graph(mapping, same_org_migration_path)


@pytest.mark.asyncio
async def test_migrate_works_with_attribute_override(
    client: ElisAPIClient, same_org_migration_path
):
    ATTRIBUTE_TO_OVERRIDE = "description"
    OVERRIDE_VALUE = "this is a target hook"

    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)

    hook_mappings = mapping["organization"]["hooks"]

    if not len(hook_mappings):
        raise Exception("No hook mappings to test attribute override")

    overriden_hook = hook_mappings[0]
    overriden_hook["targets"][0] = {
        "attribute_override": {ATTRIBUTE_TO_OVERRIDE: OVERRIDE_VALUE}
    }

    overriden_schema = mapping["organization"]["schemas"][0]
    overriden_schema["targets"][0] = {
        "attribute_override": {
            "name": f"{ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD} - PROD"
        }
    }

    await write_mapping(same_org_migration_path / settings.MAPPING_FILENAME, mapping)

    await migrate_project(client=client, org_path=same_org_migration_path)

    # check each object in mapping has a target and a json file in target dir
    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)
    await ensure_source_objects_have_target_counter_part(
        mapping, same_org_migration_path
    )
    await ensure_hooks_have_same_dependency_graph(mapping, same_org_migration_path)

    # Check dynamic name of schema with attribute override
    overriden_schema_mapping_after_migration = find_mapping_of_object(
        mapping["organization"]["schemas"], overriden_schema["id"]
    )

    overriden_schema_name = f'{overriden_schema["name"]} - PROD'
    target_schema_path = (
        same_org_migration_path
        / settings.TARGET_DIRNAME
        / "schemas"
        / f"{templatize_name_id(overriden_schema_name, overriden_schema_mapping_after_migration['targets'][0]['target_id'])}.json"
    )
    assert await target_schema_path.exists()

    # Check ATTRIBUTE_TO_OVERRIDE in target hook
    overriden_hook_mapping_after_migration = find_mapping_of_object(
        mapping["organization"]["hooks"], overriden_hook["id"]
    )
    target_hook_path = (
        same_org_migration_path
        / settings.TARGET_DIRNAME
        / "hooks"
        / f"{templatize_name_id(overriden_hook_mapping_after_migration['name'], overriden_hook_mapping_after_migration['targets'][0]['target_id'])}.json"
    )
    assert await target_hook_path.exists()

    source_hook_path = (
        same_org_migration_path
        / settings.SOURCE_DIRNAME
        / "hooks"
        / f"{templatize_name_id(overriden_hook_mapping_after_migration['name'], overriden_hook_mapping_after_migration['id'])}.json"
    )
    source_hook = await read_json(source_hook_path)
    target_hook = await read_json(target_hook_path)

    assert source_hook[ATTRIBUTE_TO_OVERRIDE] == ""
    assert target_hook[ATTRIBUTE_TO_OVERRIDE] == OVERRIDE_VALUE


@pytest.mark.asyncio
async def test_migrate_twice_is_idempotent(
    client: ElisAPIClient, same_org_migration_path
):
    await migrate_project(client=client, org_path=same_org_migration_path)
    mapping_after_first_migrate = await read_mapping(
        same_org_migration_path / settings.MAPPING_FILENAME
    )
    await migrate_project(client=client, org_path=same_org_migration_path)
    mapping_after_second_migrate = await read_mapping(
        same_org_migration_path / settings.MAPPING_FILENAME
    )

    assert mapping_after_first_migrate == mapping_after_second_migrate


@pytest.mark.asyncio
async def test_migrate_ignores_designated_object(
    client: ElisAPIClient, same_org_migration_path
):
    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)

    ignored_hook_mapping = mapping["organization"]["hooks"][0]
    ignored_hook_mapping["ignore"] = True
    await write_mapping(same_org_migration_path / settings.MAPPING_FILENAME, mapping)

    await migrate_project(client=client, org_path=same_org_migration_path)

    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)
    post_migration_ignored_hook_mapping = find_mapping_of_object(
        mapping["organization"]["hooks"], ignored_hook_mapping["id"]
    )

    assert post_migration_ignored_hook_mapping == ignored_hook_mapping

    source_hook_paths = [
        path
        async for path in (
            same_org_migration_path / settings.SOURCE_DIRNAME / "hooks"
        ).iterdir()
        if path.suffix != ".py"
    ]
    target_hook_paths = [
        path
        async for path in (
            same_org_migration_path / settings.TARGET_DIRNAME / "hooks"
        ).iterdir()
        if path.suffix != ".py"
    ]
    assert len(source_hook_paths) == len(target_hook_paths) + 1


@pytest.mark.asyncio
async def test_migrate_ignores_non_selected_objects(
    client: ElisAPIClient, same_org_migration_path
):
    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)

    selected_hook_mapping = mapping["organization"]["hooks"][0]
    selected_hook_mapping[MAPPING_SELECTED_ATTRIBUTE] = True
    await write_mapping(same_org_migration_path / settings.MAPPING_FILENAME, mapping)

    await migrate_project(
        client=client, org_path=same_org_migration_path, selected_only=True
    )

    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)

    for mapping_object in traverse_mapping(mapping["organization"]):
        if mapping_object["id"] == mapping["organization"]["id"]:
            continue

        if mapping_object["id"] == selected_hook_mapping["id"]:
            assert len(mapping_object.get("targets", [])) == 1
            assert mapping_object.get("targets", [{"target_id": None}])[0]["target_id"]
        else:
            assert not mapping_object.get("targets", [{"target_id": None}])[0][
                "target_id"
            ]


@pytest.mark.asyncio
async def test_migrate_adds_new_object_on_second_run(
    client: ElisAPIClient, same_org_migration_path
):
    await migrate_project(client=client, org_path=same_org_migration_path)

    schema = await client.create_new_schema(
        {"name": "new source schema", "content": []}
    )
    await download_organization_combined_source_target(
        client=client, org_path=same_org_migration_path
    )

    await migrate_project(client=client, org_path=same_org_migration_path)

    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)
    source_schema_in_mapping = find_mapping_of_object(
        mapping["organization"]["schemas"], schema.id
    )
    target_schema_id = source_schema_in_mapping["targets"][0]["target_id"]
    assert target_schema_id

    target_schema_path = (
        same_org_migration_path
        / settings.TARGET_DIRNAME
        / "schemas"
        / f"{templatize_name_id(schema.name, target_schema_id)}.json"
    )
    assert await target_schema_path.exists()


@pytest.mark.asyncio
async def test_migrate_updates_object_on_second_run(
    client: ElisAPIClient, same_org_migration_path
):
    await migrate_project(client=client, org_path=same_org_migration_path)

    some_hook_path = await anext(
        (same_org_migration_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
    )
    some_hook = await read_json(some_hook_path)
    some_hook["active"] = False
    await write_json(some_hook_path, some_hook)

    await migrate_project(client=client, org_path=same_org_migration_path)

    mapping = await read_mapping(same_org_migration_path / settings.MAPPING_FILENAME)
    some_hook_in_mapping = find_mapping_of_object(
        mapping["organization"]["hooks"], some_hook["id"]
    )
    target_hook_after_migration_path = (
        same_org_migration_path
        / settings.TARGET_DIRNAME
        / "hooks"
        / f"{templatize_name_id(some_hook['name'], some_hook_in_mapping['targets'][0]['target_id'])}.json"
    )
    assert await target_hook_after_migration_path.exists()
    target_hook_after_migration = await read_json(target_hook_after_migration_path)
    assert not target_hook_after_migration["active"]


@pytest.mark.asyncio
async def test_migrate_creates_new_objects_in_different_org(
    target_client: ElisAPIClient, cross_org_migration_path, monkeypatch
):
    users = [user async for user in target_client.list_all_users()]
    # Input user ID from the target org (for hook authorization)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{users[0].id}\ny"))
    await migrate_project(client=target_client, org_path=cross_org_migration_path)

    # check each object in mapping has a target and a json file in target dir
    mapping = await read_mapping(cross_org_migration_path / settings.MAPPING_FILENAME)
    await ensure_source_objects_have_target_counter_part(
        mapping, cross_org_migration_path
    )
