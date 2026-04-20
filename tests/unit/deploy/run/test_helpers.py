import re
from datetime import datetime

import pytest

from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    create_object_label,
    generate_deploy_timestamp,
    remove_queue_attributes_for_cross_org,
    traverse_object,
)
from deployment_manager.utils.consts import QUEUE_ENGINE_ATTRIBUTES, settings


class TestDeployYaml:
    def test_parses_yaml_content(self):
        raw = "source_dir: myproj\ntarget_url: https://api.rossum.ai/api/v1\n"
        y = DeployYaml(raw)
        assert y.data[settings.DEPLOY_KEY_SOURCE_DIR] == "myproj"
        assert y.data[settings.DEPLOY_KEY_TARGET_URL] == "https://api.rossum.ai/api/v1"

    def test_preserves_quotes(self):
        raw = "'quoted_key': 'value'\n"
        y = DeployYaml(raw)
        assert y.data["quoted_key"] == "value"

    def test_release_keyword_regex(self):
        rx = DeployYaml.RELEASE_KEYWORD_REGEX
        assert rx.match("release")
        assert rx.match("release_staging")
        # No non-word chars after underscore
        assert not rx.match("release-staging")

    @pytest.mark.asyncio
    async def test_save_to_file_roundtrip(self, tmp_path):
        raw = "source_dir: myproj\n"
        y = DeployYaml(raw)
        out_path = tmp_path / "out.yaml"
        await y.save_to_file(out_path)
        content = await out_path.read_text()
        assert "source_dir" in content

    @pytest.mark.asyncio
    async def test_save_to_file_creates_parents(self, tmp_path):
        y = DeployYaml("a: b\n")
        nested = tmp_path / "a" / "b" / "c.yaml"
        await y.save_to_file(nested)
        assert await nested.exists()


class TestCheckRequiredKeys:
    def test_all_present(self):
        release = {
            settings.DEPLOY_KEY_SOURCE_DIR: "s",
            settings.DEPLOY_KEY_TARGET_URL: "u",
        }
        assert check_required_keys(release) is True

    def test_missing_source_dir(self, capsys):
        release = {settings.DEPLOY_KEY_TARGET_URL: "u"}
        assert check_required_keys(release) is False

    def test_missing_target_url(self, capsys):
        release = {settings.DEPLOY_KEY_SOURCE_DIR: "s"}
        assert check_required_keys(release) is False

    def test_empty(self):
        assert check_required_keys({}) is False


class TestTraverseObject:
    def test_simple_dict(self):
        obj = {"name": "foo", "id": 42}
        results = list(traverse_object(None, "root", obj))
        # name, id
        assert (obj, "name", "foo") in results
        assert (obj, "id", 42) in results

    def test_nested_dict(self):
        inner = {"deep": 1}
        obj = {"a": inner}
        results = list(traverse_object(None, "root", obj))
        assert (inner, "deep", 1) in results

    def test_list_of_primitives(self):
        # traverse_object recurses into list items but passes through same parent/key
        obj = {"items": [1, 2, 3]}
        results = list(traverse_object(None, "root", obj))
        # list yields each element with parent=obj, key="items"
        keys_values = [(parent_key, value) for _, parent_key, value in results]
        assert ("items", 1) in keys_values
        assert ("items", 2) in keys_values
        assert ("items", 3) in keys_values

    def test_list_of_dicts(self):
        obj = {"items": [{"x": 1}, {"x": 2}]}
        results = list(traverse_object(None, "root", obj))
        # Each dict's inner keys are yielded
        inner_values = [value for _, key, value in results if key == "x"]
        assert 1 in inner_values
        assert 2 in inner_values

    def test_primitive_only(self):
        # A bare primitive should be yielded once, with the given parent+key
        results = list(traverse_object({"top": "v"}, "top", "v"))
        assert results == [({"top": "v"}, "top", "v")]


class TestGenerateDeployTimestamp:
    def test_ends_with_Z(self):
        ts = generate_deploy_timestamp()
        assert ts.endswith("Z")

    def test_is_parseable_iso(self):
        ts = generate_deploy_timestamp()
        # Strip the Z for datetime.fromisoformat
        parsed = datetime.fromisoformat(ts.rstrip("Z"))
        assert parsed is not None

    def test_contains_microseconds(self):
        ts = generate_deploy_timestamp()
        # ISO format with microseconds pattern: YYYY-MM-DDTHH:MM:SS.ffffff
        assert re.search(r"\.\d{6}Z$", ts)


class TestRemoveQueueAttributesForCrossOrg:
    def test_removes_workflows(self):
        queue = {"workflows": [1, 2], "name": "q"}
        remove_queue_attributes_for_cross_org(queue)
        assert "workflows" not in queue
        assert queue["name"] == "q"

    def test_removes_engines(self):
        queue = {attr: "v" for attr in QUEUE_ENGINE_ATTRIBUTES}
        queue["keep"] = "this"
        remove_queue_attributes_for_cross_org(queue)
        for attr in QUEUE_ENGINE_ATTRIBUTES:
            assert attr not in queue
        assert queue["keep"] == "this"

    def test_safe_if_missing(self):
        queue = {"name": "q"}
        remove_queue_attributes_for_cross_org(queue)
        assert queue == {"name": "q"}


class TestCreateObjectLabel:
    def test_format(self):
        label = create_object_label("myname", 42)
        assert "myname" in label
        assert "42" in label
        # Color markup present
        assert "[green]" in label
        assert "[purple]" in label
