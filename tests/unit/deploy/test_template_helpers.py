"""Tests for deploy/subcommands/template/helpers.py — pure helpers only."""

import pytest
from anyio import Path

from deployment_manager.commands.deploy.subcommands.template.helpers import (
    DEFAULT_TARGETS,
    check_input_integer,
    create_deploy_file_template,
    find_engine_field_paths_for_engine,
    find_engine_paths_for_dir,
    find_hooks_for_queues,
    find_queue_paths_for_workspaces,
    find_rule_paths_for_dir,
    find_ws_paths_for_dir,
    prepare_deploy_file_objects,
    prepare_subqueue_deploy_file_object,
)
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings


class TestCreateDeployFileTemplate:
    def test_contains_required_keys(self):
        template = create_deploy_file_template()
        for key in (
            settings.DEPLOY_KEY_TARGET_URL,
            settings.DEPLOY_KEY_SOURCE_DIR,
            settings.DEPLOY_KEY_TARGET_DIR,
            settings.DEPLOY_KEY_TOKEN_OWNER,
            settings.DEPLOY_KEY_PATCH_TARGET_ORG,
        ):
            assert f"{key}:" in template

    def test_has_section_headers(self):
        template = create_deploy_file_template()
        for section in ("workspaces:", "queues:", "hooks:", "engines:", "rules:"):
            assert section in template


class TestCheckInputInteger:
    def test_valid_integer(self):
        assert check_input_integer("42") is True

    def test_zero(self):
        # falsy int → returns None (not True)
        assert check_input_integer("0") is None

    def test_invalid_string(self):
        assert check_input_integer("abc") == "Invalid integer"

    def test_empty(self):
        assert check_input_integer("") == "Invalid integer"


class TestPrepareDeployFileObjects:
    def test_basic_shape(self):
        objects = [
            {"id": 1, "name": "Q1", "path": Path("src/primary/workspaces/W_[5]/queues/Q_[1]/queue.json")},
        ]
        result = prepare_deploy_file_objects(objects=objects, include_path=True)
        assert len(result) == 1
        entry = result[0]
        assert entry["id"] == 1
        assert entry["name"] == "Q1"
        # base_path is parent.parent.parent of the queue.json (= workspace dir)
        assert entry[settings.DEPLOY_KEY_BASE_PATH] == "src/primary/workspaces/W_[5]"
        assert entry[settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS

    def test_without_path(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        result = prepare_deploy_file_objects(objects=objects, include_path=False)
        assert settings.DEPLOY_KEY_BASE_PATH not in result[0]

    def test_preserves_previous_targets(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        previous = [
            {"id": 1, "targets": [{"id": 99, "attribute_override": {"name": "kept"}}]}
        ]
        result = prepare_deploy_file_objects(
            objects=objects,
            include_path=False,
            objects_in_previous_file=previous,
        )
        # Previous targets preserved
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 99, "attribute_override": {"name": "kept"}}]

    def test_extra_attributes(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        result = prepare_deploy_file_objects(
            objects=objects,
            include_path=False,
            extra_attributes={"ignore_deploy_warnings": False},
        )
        assert result[0]["ignore_deploy_warnings"] is False


class TestPrepareSubqueueDeployFileObject:
    def test_basic(self):
        obj = {"id": 42, "name": "subobject"}
        result = prepare_subqueue_deploy_file_object(obj)
        assert result == {"id": 42, "targets": DEFAULT_TARGETS}

    def test_with_name_flag(self):
        obj = {"id": 42, "name": "subobject"}
        result = prepare_subqueue_deploy_file_object(obj, include_name=True)
        assert result["name"] == "subobject"

    def test_preserves_previous_targets(self):
        obj = {"id": 42, "name": "x"}
        previous = {"targets": [{"id": 99}]}
        result = prepare_subqueue_deploy_file_object(obj, previous_object=previous)
        assert result["targets"] == [{"id": 99}]


@pytest.mark.asyncio
class TestFindPaths:
    async def test_find_ws_paths_for_dir(self, tmp_path):
        base = tmp_path / "src"
        await (base / "workspaces" / "WS_[1]").mkdir(parents=True)
        await (base / "workspaces" / "WS_[2]").mkdir(parents=True)
        result = await find_ws_paths_for_dir(base)
        assert len(result) == 2

    async def test_find_queue_paths_for_workspaces(self, tmp_path):
        ws_path = tmp_path / "workspaces" / "WS_[1]"
        await (ws_path / "queues" / "Q_[10]").mkdir(parents=True)
        await (ws_path / "queues" / "Q_[10]" / "queue.json").write_text("{}")
        result = await find_queue_paths_for_workspaces([ws_path])
        assert len(result) == 1
        assert result[0].name == "queue.json"

    async def test_find_rule_paths_for_dir(self, tmp_path):
        rules_dir = tmp_path / settings.RULES_DIR_NAME
        await rules_dir.mkdir(parents=True)
        await (rules_dir / "rule_[1].json").write_text("{}")
        await (rules_dir / "notrule.txt").write_text("x")
        result = await find_rule_paths_for_dir(tmp_path)
        assert len(result) == 1

    async def test_find_rule_paths_for_dir_missing(self, tmp_path):
        assert await find_rule_paths_for_dir(tmp_path) == []

    async def test_find_engine_paths_for_dir(self, tmp_path):
        engine_dir = tmp_path / "engines"
        await (engine_dir / "engine_[1]").mkdir(parents=True)
        await (engine_dir / "engine_[1]" / "engine.json").write_text("{}")
        # Also a top-level engine json (older layout)
        await (engine_dir / "flat_engine_[2].json").write_text("{}")
        result = await find_engine_paths_for_dir(tmp_path)
        assert len(result) == 2

    async def test_find_engine_field_paths_for_engine(self, tmp_path):
        engine_file = tmp_path / "engines" / "eng_[1]" / "engine.json"
        await engine_file.parent.mkdir(parents=True)
        await engine_file.write_text("{}")
        fields_dir = engine_file.parent / "engine_fields"
        await fields_dir.mkdir()
        await (fields_dir / "f_[99].json").write_text("{}")
        result = await find_engine_field_paths_for_engine(engine_file)
        assert len(result) == 1

    async def test_find_hooks_for_queues_matches_by_id(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        await hooks_dir.mkdir(parents=True)

        h1 = {
            "id": 100,
            "name": "H1",
            "url": "https://api/hooks/100",
            "type": "function",
            "events": [],
            "active": True,
            "queues": [],
            "run_after": [],
            "config": {},
            "extension_source": "custom",
            "secrets": {},
            "sideload": [],
        }
        h2 = {**h1, "id": 200, "name": "H2"}
        await write_object_to_json(hooks_dir / "H1_[100].json", h1)
        await write_object_to_json(hooks_dir / "H2_[200].json", h2)

        # Queue only references H1
        queues = [{"hooks": ["https://api/v1/hooks/100"]}]
        result = await find_hooks_for_queues(tmp_path, queues)
        assert len(result) == 1
        assert result[0]["id"] == 100
