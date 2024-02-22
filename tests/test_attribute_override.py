import pytest
import pytest_asyncio
from project_rossum_deploy.common.attribute_override import override_attributes

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.utils.functions import read_json
from tests.utils.consts import REFERENCE_PROJECT_PATH


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

    overriden_organization = override_attributes(
        loaded_mapping, loaded_mapping["organization"], organization
    )

    assert NAME == overriden_organization["name"]


@pytest.mark.asyncio
async def test_override_adding_keys(loaded_mapping: dict):
    KEY = "some_key"
    loaded_mapping["organization"]["attribute_override"] = {KEY: "some_value"}

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    overriden_organization = override_attributes(
        loaded_mapping, loaded_mapping["organization"], organization
    )

    assert overriden_organization.get(KEY, None)


@pytest.mark.asyncio
async def test_override_dict_value(loaded_mapping: dict):
    METADATA = {"foo": "bar"}
    loaded_mapping["organization"]["attribute_override"] = {"metadata": METADATA}

    organization = await read_json(
        REFERENCE_PROJECT_PATH / settings.SOURCE_DIRNAME / "organization.json"
    )

    overriden_organization = override_attributes(
        loaded_mapping, loaded_mapping["organization"], organization
    )

    for key in METADATA:
        assert key in overriden_organization["metadata"]


@pytest.mark.asyncio
async def test_override_nested_reference(loaded_mapping: dict):
    ...


@pytest.mark.asyncio
async def test_override_multiple_values_of_same_object(loaded_mapping: dict):
    ...


@pytest.mark.asyncio
async def test_override_multiple_paths(loaded_mapping: dict):
    ...
