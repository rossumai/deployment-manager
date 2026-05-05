from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import Path
from rossum_api import APIClientError

from deployment_manager.commands.upload.dependencies import (
    cascade_delete_ops,
    evaluate_delete_dependencies,
    is_change_existing,
    mark_unstaged_objects_as_updated,
    merge_formula_changes,
    merge_hook_changes,
)
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json, write_str
from deployment_manager.utils.consts import GIT_CHARACTERS, settings


class TestIsChangeExisting:
    def test_same_op_and_path_returns_true(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("a.json")), changes) is True

    def test_different_op_same_path(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.DELETED, Path("a.json")), changes) is False

    def test_different_path(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("b.json")), changes) is False

    def test_empty_list(self):
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("a.json")), []) is False


@pytest.mark.asyncio
class TestMergeHookChanges:
    async def test_updated_py_file_merges_into_json(self, tmp_path):
        org_path = tmp_path
        hook_dir = tmp_path / "org" / "hooks"
        await hook_dir.mkdir(parents=True)
        hook_json_path = hook_dir / "h1.json"
        hook_py_path = hook_dir / "h1.py"

        # Write the initial JSON object and a new Python file
        await write_object_to_json(
            hook_json_path,
            {"config": {"code": "old_code", "runtime": "python3.8"}, "extension_source": "custom"},
        )
        await write_str(hook_py_path, "new_code_here")

        changes = [(GIT_CHARACTERS.UPDATED, hook_py_path)]
        result = await merge_hook_changes(changes, org_path)

        # The result should have a single UPDATED for the JSON file
        assert len(result) == 1
        assert result[0][0] == GIT_CHARACTERS.UPDATED
        assert "h1.json" in str(result[0][1])

        # The JSON file itself should now contain the new code
        updated = await read_object_from_json(hook_json_path)
        assert updated["config"]["code"] == "new_code_here"

    async def test_unrelated_change_is_passed_through(self, tmp_path):
        other_path = tmp_path / "workspace.json"
        change = (GIT_CHARACTERS.UPDATED, other_path)
        result = await merge_hook_changes([change], tmp_path)
        assert change in result


@pytest.mark.asyncio
class TestMergeFormulaChanges:
    async def test_formula_update_merges_into_schema(self, tmp_path):
        formula_dir = settings.FORMULA_DIR_NAME
        queue_dir = tmp_path / "ws_[1]" / "queues" / "q_[5]"
        formula_path = queue_dir / formula_dir / "target_field.py"
        schema_path = queue_dir / "schema.json"

        await (queue_dir / formula_dir).mkdir(parents=True)

        # Write schema with that formula field
        await write_object_to_json(
            schema_path,
            {
                "content": [
                    {
                        "category": "section",
                        "children": [
                            {"id": "target_field", "category": "datapoint", "formula": "old"},
                        ],
                    }
                ]
            },
        )
        # Write new formula code
        await write_str(formula_path, "new_formula_code")

        changes = [(GIT_CHARACTERS.UPDATED, formula_path)]
        result = await merge_formula_changes(changes)

        # Should produce a single UPDATED schema.json change
        assert len(result) == 1
        assert result[0][0] == GIT_CHARACTERS.UPDATED
        assert "schema.json" in str(result[0][1])

        # Schema file now has updated formula code
        updated = await read_object_from_json(schema_path)
        datapoint = updated["content"][0]["children"][0]
        assert datapoint["formula"] == "new_formula_code"

    async def test_unrelated_change_passthrough(self, tmp_path):
        p = tmp_path / "something.json"
        change = (GIT_CHARACTERS.UPDATED, p)
        result = await merge_formula_changes([change])
        assert change in result


def _client_with_obj(remote_obj=None, status_code=None):
    client = MagicMock()
    client._http_client = MagicMock()
    if remote_obj is not None:
        client._http_client.request_json = AsyncMock(return_value=remote_obj)
    elif status_code is not None:
        client._http_client.request_json = AsyncMock(
            side_effect=APIClientError("GET", "/api", status_code, "Not Found")
        )
    else:
        client._http_client.request_json = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
class TestMarkUnstagedObjectsAsUpdated:
    async def test_skips_uncommitted_object_without_id(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/hooks/h.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(org_path / path, {"id": None, "url": None})

        client = _client_with_obj(remote_obj={"id": 1})
        result = await mark_unstaged_objects_as_updated(
            [(GIT_CHARACTERS.CREATED, path)], org_path, client
        )
        # Object with no id/url is silently skipped
        assert result == []

    async def test_remote_exists_changes_create_to_update(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/hooks/h.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(
            org_path / path,
            {"id": 1, "url": "https://api/v1/hooks/1"},
        )

        client = _client_with_obj(remote_obj={"id": 1, "url": "https://api/v1/hooks/1"})
        result = await mark_unstaged_objects_as_updated(
            [(GIT_CHARACTERS.CREATED, path)], org_path, client
        )
        # CREATED → UPDATED because the remote already has the object
        assert result == [(GIT_CHARACTERS.UPDATED, path)]

    async def test_remote_404_keeps_create(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/hooks/h.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(
            org_path / path,
            {"id": 1, "url": "https://api/v1/hooks/1"},
        )

        client = _client_with_obj(status_code=404)
        result = await mark_unstaged_objects_as_updated(
            [(GIT_CHARACTERS.CREATED, path)], org_path, client
        )
        assert result == [(GIT_CHARACTERS.CREATED, path)]

    async def test_organization_create_is_warned_and_skipped(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/organization.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(
            org_path / path,
            {"id": 1, "url": "https://api/v1/organizations/1"},
        )
        client = _client_with_obj(status_code=404)
        result = await mark_unstaged_objects_as_updated(
            [(GIT_CHARACTERS.CREATED, path)], org_path, client
        )
        # Organizations cannot be created → returned as empty
        assert result == []

    async def test_inbox_create_is_warned_and_skipped(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/inboxes/i.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(
            org_path / path,
            {"id": 1, "url": "https://api/v1/inboxes/1"},
        )
        client = _client_with_obj(status_code=404)
        result = await mark_unstaged_objects_as_updated(
            [(GIT_CHARACTERS.CREATED, path)], org_path, client
        )
        assert result == []

    async def test_passes_through_non_create_changes(self, tmp_path):
        # DELETED, UPDATED ops are not touched
        change = (GIT_CHARACTERS.DELETED, Path("a.json"))
        result = await mark_unstaged_objects_as_updated(
            [change], tmp_path, _client_with_obj()
        )
        assert result == [change]

    async def test_propagates_non_404_api_errors(self, tmp_path):
        org_path = tmp_path
        path = Path("source/org/hooks/h.json")
        await (org_path / path).parent.mkdir(parents=True)
        await write_object_to_json(
            org_path / path,
            {"id": 1, "url": "https://api/v1/hooks/1"},
        )
        client = _client_with_obj(status_code=500)
        with pytest.raises(APIClientError):
            await mark_unstaged_objects_as_updated(
                [(GIT_CHARACTERS.CREATED, path)], org_path, client
            )


@pytest.mark.asyncio
class TestCascadeDeleteOps:
    async def test_cascades_files_under_parent_dir(self, tmp_path):
        # Build a queue dir with sub-files; deleting queue.json cascades
        org_dir = "test-org"
        queue_dir = tmp_path / "source" / org_dir / "workspaces/W_[1]/queues/Q_[10]"
        await queue_dir.mkdir(parents=True)
        await (queue_dir / "queue.json").write_text("{}")
        await (queue_dir / "schema.json").write_text("{}")
        await (queue_dir / "inbox.json").write_text("{}")  # inbox is skipped from cascade

        change = (GIT_CHARACTERS.DELETED, queue_dir / "queue.json")
        changes_updated = []
        result = await cascade_delete_ops(
            queue_dir / "queue.json", change, changes_updated, Path(org_dir)
        )

        # Expected: queue.json + schema.json deletes (inbox.json explicitly skipped)
        deleted_paths = [str(p) for op, p in result if op == "D"]
        # Find the additions - they will be under "source/<org_dir>/..."
        assert any("schema.json" in p for p in deleted_paths)
        # inbox.json must not appear
        assert not any("inbox.json" in p for p in deleted_paths)
        # Original queue.json change is preserved
        assert change in result


@pytest.mark.asyncio
class TestEvaluateDeleteDependencies:
    async def test_workspace_delete_cascades_when_confirmed(self, tmp_path, monkeypatch):
        ws_dir = tmp_path / "source/org/workspaces/W_[1]"
        await ws_dir.mkdir(parents=True)
        await (ws_dir / "workspace.json").write_text("{}")
        # A child queue
        q_dir = ws_dir / "queues/Q_[10]"
        await q_dir.mkdir(parents=True)
        await (q_dir / "queue.json").write_text("{}")

        change = (GIT_CHARACTERS.DELETED, ws_dir / "workspace.json")

        with patch(
            "deployment_manager.commands.upload.dependencies.Confirm.ask",
            return_value=True,
        ):
            result = await evaluate_delete_dependencies([change], Path("org"))

        # Result includes the workspace.json delete plus cascaded children
        deleted_paths = [str(p) for op, p in result if op == "D"]
        assert any("queue.json" in p for p in deleted_paths)

    async def test_workspace_delete_aborted_when_user_declines(self, tmp_path):
        ws_dir = tmp_path / "source/org/workspaces/W_[1]"
        await ws_dir.mkdir(parents=True)
        await (ws_dir / "workspace.json").write_text("{}")

        change = (GIT_CHARACTERS.DELETED, ws_dir / "workspace.json")
        with patch(
            "deployment_manager.commands.upload.dependencies.Confirm.ask",
            return_value=False,
        ):
            result = await evaluate_delete_dependencies([change], Path("org"))

        # Nothing happens when user declines
        assert result == []

    async def test_queue_delete_cascades(self, tmp_path):
        q_dir = tmp_path / "source/org/workspaces/W_[1]/queues/Q_[10]"
        await q_dir.mkdir(parents=True)
        await (q_dir / "queue.json").write_text("{}")
        await (q_dir / "schema.json").write_text("{}")

        change = (GIT_CHARACTERS.DELETED, q_dir / "queue.json")
        result = await evaluate_delete_dependencies([change], Path("org"))
        deleted_paths = [str(p) for op, p in result if op == "D"]
        assert any("schema.json" in p for p in deleted_paths)

    async def test_other_delete_passes_through(self, tmp_path):
        change = (GIT_CHARACTERS.DELETED, Path("source/org/hooks/h.json"))
        result = await evaluate_delete_dependencies([change], Path("org"))
        assert result == [change]

    async def test_non_delete_change_passes_through(self):
        change = (GIT_CHARACTERS.UPDATED, Path("a.json"))
        result = await evaluate_delete_dependencies([change], Path("org"))
        assert result == [change]
