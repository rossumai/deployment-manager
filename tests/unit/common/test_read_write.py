import json

import pytest
from anyio import Path

from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    find_fields_in_schema,
    find_formula_fields_in_schema,
    read_object_from_json,
    read_prd_cred_file,
    read_prd_project_config,
    read_yaml,
    write_object_to_json,
    write_prd_cred_file,
    write_str,
    write_txt,
    write_yaml,
)
from deployment_manager.utils.consts import settings
from rossum_api.domain_logic.resources import Resource


@pytest.mark.asyncio
class TestWriteReadJson:
    async def test_write_and_read_simple_object(self, tmp_path):
        path = tmp_path / "thing.json"
        await write_object_to_json(path, {"id": 1, "name": "foo"})
        loaded = await read_object_from_json(path, False)
        assert loaded == {"id": 1, "name": "foo"}

    async def test_creates_missing_parents(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "file.json"
        await write_object_to_json(path, {"a": 1})
        assert await path.exists()

    async def test_non_pulled_keys_stripped(self, tmp_path):
        # Queue has "counts" and "users" in NON_PULLED_KEYS_PER_OBJECT
        path = tmp_path / "queue.json"
        await write_object_to_json(
            path,
            {"id": 1, "name": "q", "counts": {"foo": 1}, "users": [1, 2]},
            type=Resource.Queue,
        )
        loaded = await read_object_from_json(path, False)
        assert "counts" not in loaded
        assert "users" not in loaded

    async def test_hook_status_stripped(self, tmp_path):
        path = tmp_path / "hook.json"
        await write_object_to_json(
            path,
            {"id": 1, "name": "h", "status": "running"},
            type=Resource.Hook,
        )
        loaded = await read_object_from_json(path, False)
        assert "status" not in loaded


@pytest.mark.asyncio
class TestNonVersionedAttributes:
    async def test_modified_at_goes_to_separate_file(self, tmp_path, monkeypatch):
        # The non-versioned attribute logic uses path.parents[-3], which assumes
        # relative paths (third-from-end parent must be the org/subdir root).
        # chdir into tmp_path and operate via a relative path.
        import os

        monkeypatch.chdir(tmp_path)

        obj = {
            "id": 1,
            "name": "ws",
            "modified_at": "2024-01-01T00:00:00Z",
            "autopilot": True,
        }
        rel_ws_path = Path("org") / "subdir" / "workspaces" / "ws_[1]" / "workspace.json"

        await write_object_to_json(rel_ws_path, obj, type=Resource.Workspace)

        raw = json.loads(os.path.exists(rel_ws_path) and open(rel_ws_path).read())
        assert "modified_at" not in raw
        assert raw["autopilot"] is True

        # Non-versioned sidecar file exists on org/subdir level
        nv_file = Path("org") / "subdir" / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME
        assert await nv_file.exists()

        # Reading with include_non_version_attribtues=True merges them back in
        merged = await read_object_from_json(rel_ws_path, include_non_version_attribtues=True)
        assert merged["modified_at"] == "2024-01-01T00:00:00Z"

    async def test_write_outside_subdir_does_not_split(self, tmp_path, monkeypatch):
        # Path too shallow -> no sidecar; modified_at stays in main file
        monkeypatch.chdir(tmp_path)
        path = Path("shallow.json")
        await write_object_to_json(
            path,
            {"id": 1, "modified_at": "2024-01-01T00:00:00Z"},
            type=Resource.Workspace,
        )
        raw = json.loads(open(tmp_path / "shallow.json").read())
        # modified_at still in the file because depth is less than 3
        assert "modified_at" in raw


class TestFindFormulaFieldsInSchema:
    def test_empty_schema(self):
        assert find_formula_fields_in_schema([]) == []

    def test_simple_formula_datapoint(self):
        schema = [
            {
                "category": "datapoint",
                "id": "field_a",
                "formula": "1 + 1",
            }
        ]
        assert find_formula_fields_in_schema(schema) == [("field_a", "1 + 1")]

    def test_datapoint_without_formula_skipped(self):
        schema = [{"category": "datapoint", "id": "x"}]
        assert find_formula_fields_in_schema(schema) == []

    def test_nested_section(self):
        schema = [
            {
                "category": "section",
                "children": [
                    {"category": "datapoint", "id": "a", "formula": "f1"},
                    {"category": "datapoint", "id": "b"},
                ],
            }
        ]
        assert find_formula_fields_in_schema(schema) == [("a", "f1")]

    def test_dict_at_root(self):
        schema = {
            "category": "section",
            "children": [{"category": "datapoint", "id": "x", "formula": "42"}],
        }
        result = find_formula_fields_in_schema(schema)
        assert result == [("x", "42")]


class TestFindFieldsInSchema:
    def test_all_datapoints(self):
        schema = [
            {
                "category": "section",
                "children": [
                    {"category": "datapoint", "id": "a"},
                    {
                        "category": "multivalue",
                        "children": {
                            "category": "tuple",
                            "children": [{"category": "datapoint", "id": "b"}],
                        },
                    },
                ],
            }
        ]
        found = find_fields_in_schema(schema)
        ids = [f["id"] for f in found]
        assert "a" in ids
        assert "b" in ids


class TestCustomHookCodePath:
    def test_python_code(self, tmp_path):
        hook = {
            "config": {"code": "pass", "runtime": "python3.8"},
            "extension_source": "custom",
        }
        path = Path("/tmp/hooks/myhook.json")
        result = create_custom_hook_code_path(path, hook)
        assert str(result).endswith(".py")

    def test_js_code(self, tmp_path):
        hook = {
            "config": {"code": "console.log(1);", "runtime": "nodejs18"},
            "extension_source": "custom",
        }
        path = Path("/tmp/hooks/myhook.json")
        result = create_custom_hook_code_path(path, hook)
        assert str(result).endswith(".js")

    def test_rossum_store_returns_none(self):
        hook = {
            "config": {"code": "pass", "runtime": "python3.8"},
            "extension_source": "rossum_store",
        }
        path = Path("/tmp/hooks/myhook.json")
        assert create_custom_hook_code_path(path, hook) is None

    def test_no_code_returns_none(self):
        hook = {
            "config": {"runtime": "python3.8"},
            "extension_source": "custom",
        }
        path = Path("/tmp/hooks/myhook.json")
        assert create_custom_hook_code_path(path, hook) is None


class TestFormulaDirectoryPath:
    def test_directory_path(self):
        schema_path = Path("/base/queues/q_[1]/schema.json")
        result = create_formula_directory_path(schema_path)
        assert result.name == settings.FORMULA_DIR_NAME
        assert result.parent == Path("/base/queues/q_[1]")


@pytest.mark.asyncio
class TestReadWriteYaml:
    async def test_roundtrip(self, tmp_path):
        path = tmp_path / "config.yaml"
        data = {"source_api_base": "https://a", "use_same_org_as_target": True}
        await write_yaml(path, data)
        assert read_yaml(path) == data

    async def test_write_yaml_creates_parent(self, tmp_path):
        path = tmp_path / "nested" / "config.yaml"
        await write_yaml(path, {"k": "v"})
        assert await path.exists()


@pytest.mark.asyncio
class TestReadWriteStrAndTxt:
    async def test_write_and_read_str(self, tmp_path):
        path = tmp_path / "file.txt"
        await write_str(path, "hello")
        contents = await path.read_text()
        assert contents == "hello"

    async def test_write_txt_creates_parent(self, tmp_path):
        path = tmp_path / "nested" / "file.txt"
        await write_txt(path, "hi")
        assert await path.read_text() == "hi"


@pytest.mark.asyncio
class TestPrdFiles:
    async def test_read_config_missing(self, tmp_path):
        assert await read_prd_project_config(tmp_path) is None

    async def test_read_config_present(self, tmp_path):
        config_path = tmp_path / settings.CONFIG_FILENAME
        await config_path.write_text("key: value\n")
        assert (await read_prd_project_config(tmp_path))["key"] == "value"

    async def test_read_cred_missing(self, tmp_path):
        assert await read_prd_cred_file(tmp_path) is None

    async def test_write_and_read_cred(self, tmp_path):
        org_path = tmp_path / "org"
        await org_path.mkdir()
        await write_prd_cred_file(org_path, {"token": "t", "api_base": "x"})
        loaded = await read_prd_cred_file(org_path)
        assert loaded["token"] == "t"
