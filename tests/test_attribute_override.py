import jmespath
import pytest
import pytest_asyncio
from deployment_manager.common.attribute_override import override_attributes_v2

from deployment_manager.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
    settings,
)
from deployment_manager.common.mapping import read_mapping
from deployment_manager.common.read_write import read_json
from tests.utils.consts import REFERENCE_PROJECT_PATH

pytestmark = pytest.mark.skip(reason="This test file needs refactor.")


@pytest_asyncio.fixture(scope="function")
async def loaded_mapping():
    return await read_mapping(REFERENCE_PROJECT_PATH / settings.MAPPING_FILENAME)


@pytest.mark.asyncio
async def test_simple_override(loaded_mapping: dict):
    NAME = "oooh weeee"
    loaded_mapping["organization"]["attribute_override"] = {"name": NAME}

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    override_attributes_v2(
        lookup_table={},
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert NAME == organization["name"]


@pytest.mark.asyncio
async def test_override_not_adding_keys(loaded_mapping: dict):
    KEY = "some_key"
    loaded_mapping["organization"]["attribute_override"] = {KEY: "some_value"}

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    override_attributes_v2(
        lookup_table={},
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert organization.get(KEY, "nothing") == "nothing"


@pytest.mark.asyncio
async def test_override_cannot_find_invalid_target_reference(loaded_mapping: dict):
    KEY = "name"
    loaded_mapping["organization"]["attribute_override"] = {
        KEY: ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
    }

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    with pytest.raises(Exception):
        override_attributes_v2(
            lookup_table={},
            target_submapping=loaded_mapping["organization"],
            object=organization,
        )


@pytest.mark.asyncio
async def test_override_dict_value(loaded_mapping: dict):
    METADATA = {"foo": "bar"}
    loaded_mapping["organization"]["attribute_override"] = {"metadata": METADATA}

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    override_attributes_v2(
        lookup_table={},
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert organization["metadata"] == METADATA


@pytest.mark.asyncio
async def test_override_simple_target_reference(loaded_mapping: dict):
    SOURCE_REF, TARGET_REF = 123, 456
    PATH = "metadata.reference"
    lookup_table = {SOURCE_REF: [TARGET_REF]}

    loaded_mapping["organization"]["attribute_override"] = {
        PATH: ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
    }

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )
    organization["metadata"]["reference"] = SOURCE_REF

    override_attributes_v2(
        lookup_table=lookup_table,
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert jmespath.search(PATH, organization) == [TARGET_REF]


@pytest.mark.asyncio
async def test_override_list_of_target_references(loaded_mapping: dict):
    SOURCE_REF, SOURCE_REF_2, TARGET_REF, TARGET_REF_2 = 123, 456, "haha", "hehe"
    PATH = "metadata.references"
    lookup_table = {SOURCE_REF: [TARGET_REF], SOURCE_REF_2: [TARGET_REF_2]}

    loaded_mapping["organization"]["attribute_override"] = {
        PATH: ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
    }
    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )
    organization["metadata"]["references"] = [SOURCE_REF, SOURCE_REF_2]

    override_attributes_v2(
        lookup_table=lookup_table,
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert jmespath.search(PATH, organization) == [
        v[0] for v in list(lookup_table.values())
    ]


@pytest.mark.asyncio
async def test_override_target_references_in_different_objects(loaded_mapping: dict):
    SOURCE_REF, SOURCE_REF_2, TARGET_REF, TARGET_REF_2 = 123, 456, "haha", "hehe"
    PATH = "metadata.references[*].key"
    lookup_table = {SOURCE_REF: [TARGET_REF], SOURCE_REF_2: [TARGET_REF_2]}

    loaded_mapping["organization"]["attribute_override"] = {
        PATH: ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
    }
    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )
    organization["metadata"]["references"] = [
        {"key": [SOURCE_REF, SOURCE_REF_2]},
        {"key": [SOURCE_REF]},
    ]

    override_attributes_v2(
        lookup_table=lookup_table,
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert jmespath.search(PATH, organization) == [
        [TARGET_REF, TARGET_REF_2],
        [TARGET_REF],
    ]


@pytest.mark.asyncio
async def test_override_multiple_values_in_same_object(loaded_mapping: dict):
    PATH_1, PATH_2 = "metadata.foo", "metadata.bar"
    NEW_VALUE_1, NEW_VALUE_2 = "new_1", "new_2"

    loaded_mapping["organization"]["attribute_override"] = {
        PATH_1: NEW_VALUE_1,
        PATH_2: NEW_VALUE_2,
    }

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )
    organization["metadata"]["foo"] = "whatever"
    organization["metadata"]["bar"] = "whatever"

    override_attributes_v2(
        lookup_table={},
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert jmespath.search(PATH_1, organization) == NEW_VALUE_1
    assert jmespath.search(PATH_2, organization) == NEW_VALUE_2


@pytest.mark.asyncio
async def test_override_uses_source_value_reference(loaded_mapping: dict):
    OLD_NAME, NEW_NAME = "OLD_NAME", "oooh weeh"
    loaded_mapping["organization"]["attribute_override"] = {
        "name": f"{NEW_NAME} - {ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD}"
    }

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )
    organization["name"] = OLD_NAME

    override_attributes_v2(
        lookup_table={},
        target_submapping=loaded_mapping["organization"],
        object=organization,
    )

    assert f"{NEW_NAME} - {OLD_NAME}" == organization["name"]
