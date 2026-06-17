import pytest
from anyio import Path
from rossum_api.domain_logic.resources import Resource

from deployment_manager.common.determine_path import (
    determine_object_type_from_path,
    determine_object_type_from_url,
)
from deployment_manager.utils.consts import CustomResource


class TestDetermineObjectTypeFromPath:
    def test_queue_nested_in_queues_dir(self):
        path = Path("org/sub/workspaces/ws_[1]/queues/q_[5]/queue.json")
        assert determine_object_type_from_path(path) == Resource.Queue

    def test_schema_inside_queue_dir_falls_back_to_queue(self):
        # -2 is "q_[5]" (not a resource name), fallback -3 is "queues" -> Resource.Queue
        path = Path("org/sub/workspaces/ws_[1]/queues/q_[5]/schema.json")
        assert determine_object_type_from_path(path) == Resource.Queue

    def test_hook_in_hooks_dir(self):
        path = Path("org/sub/hooks/myhook_[17].json")
        assert determine_object_type_from_path(path) == Resource.Hook

    def test_workspace_direct_stem(self):
        # Path is just "workspace.json" — stem + "s" = workspaces
        path = Path("workspace.json")
        assert determine_object_type_from_path(path) == Resource.Workspace

    def test_unknown_type_raises(self):
        path = Path("weird/path/unknown.json")
        with pytest.raises(Exception):
            determine_object_type_from_path(path)


class TestDetermineObjectTypeFromUrl:
    def test_hook(self):
        assert determine_object_type_from_url("https://api.rossum.ai/api/v1/hooks/1234") == Resource.Hook

    def test_workspace(self):
        assert determine_object_type_from_url("https://api.rossum.ai/api/v1/workspaces/5") == Resource.Workspace

    def test_queue(self):
        assert determine_object_type_from_url("https://api.rossum.ai/api/v1/queues/7") == Resource.Queue

    def test_custom_resource_labels(self):
        assert determine_object_type_from_url("https://api.rossum.ai/api/v1/labels/1") == CustomResource.Label

    def test_custom_resource_workflows(self):
        assert determine_object_type_from_url("https://api.rossum.ai/api/v1/workflows/1") == CustomResource.Workflow

    def test_unknown_raises(self):
        with pytest.raises(Exception):
            determine_object_type_from_url("https://api.rossum.ai/api/v1/nonsense/1")
