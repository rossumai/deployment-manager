import pytest
from anyio import Path

from deployment_manager.commands.hook.helpers import (
    get_annotation_id_from_frontend_url,
    get_org_name_from_hook_path,
    get_project_path_from_hook_path,
    load_hook_object,
)
from deployment_manager.common.read_write import write_object_to_json


class TestGetProjectPathFromHookPath:
    def test_basic(self):
        hook_path = Path("project/my-org/test/hooks/hook.json")
        assert get_project_path_from_hook_path(hook_path) == Path("project")


class TestGetOrgNameFromHookPath:
    def test_basic(self):
        hook_path = Path("project/my-org/test/hooks/hook.json")
        assert get_org_name_from_hook_path(hook_path) == "my-org"


class TestGetAnnotationIdFromFrontendUrl:
    def test_valid_url(self):
        url = "https://my-org.rossum.app/document/12345"
        assert get_annotation_id_from_frontend_url(url) == "12345"

    def test_url_with_query(self):
        url = "https://my-org.rossum.app/document/12345?foo=bar"
        assert get_annotation_id_from_frontend_url(url) == "12345"

    def test_no_document(self):
        assert get_annotation_id_from_frontend_url("https://my-org.rossum.app/dashboard") == ""


@pytest.mark.asyncio
class TestLoadHookObject:
    async def test_loads_json(self, tmp_path):
        path = tmp_path / "hook.json"
        await write_object_to_json(path, {"id": 1, "name": "hook"})
        result = await load_hook_object(path)
        assert result == {"id": 1, "name": "hook"}

    async def test_non_json_suffix_returns_none(self, tmp_path):
        path = tmp_path / "hook.py"
        await path.write_text("pass")
        result = await load_hook_object(path)
        assert result is None

    async def test_missing_file_returns_none(self, tmp_path):
        path = tmp_path / "no_such_hook.json"
        result = await load_hook_object(path)
        assert result is None
