import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import Path
from rossum_api import APIClientError
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.upload import apply as apply_mod
from deployment_manager.commands.upload.apply import apply_plan, format_api_error
from deployment_manager.commands.upload.directory import (
    ChangedObject,
    UploadOrganizationDirectory,
)
from deployment_manager.commands.upload.plan import classify, validate
from deployment_manager.utils.consts import GIT_CHARACTERS


def _write_json(path: Path, obj: dict) -> None:
    os.makedirs(str(path.parent), exist_ok=True)
    with open(str(path), "w") as f:
        json.dump(obj, f)


def _build_directory(tmp_path: Path, org_name: str, client) -> SimpleNamespace:
    """Construct just enough of an UploadOrganizationDirectory for apply_plan."""
    directory = SimpleNamespace()
    directory.project_path = tmp_path
    directory.name = org_name
    directory.client = SimpleNamespace(_http_client=client)
    directory.request_errors = []

    async def _make_update(object: ChangedObject):
        await client.update(object.type, object.id, object.data)

    directory.make_update_request = _make_update
    return directory


@pytest.mark.asyncio
class TestApplyCreate:
    async def test_create_workspace_renames_folder_and_writes_back(self, tmp_path):
        org_name = "source"
        org_path = Path(tmp_path) / org_name
        ws_dir = org_path / "workspaces" / "AP_[]"
        ws_path = ws_dir / "workspace.json"
        org_url = "https://example.com/api/v1/organizations/1"
        _write_json(ws_path, {"name": "AP", "organization": org_url})

        client = MagicMock()
        client.create = AsyncMock(
            return_value={
                "id": 100,
                "url": "https://example.com/api/v1/workspaces/100",
                "name": "AP",
                "organization": org_url,
            }
        )
        directory = _build_directory(Path(tmp_path), org_name, client)

        obj = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "AP_[]" / "workspace.json",
            data={"name": "AP", "organization": org_url},
        )
        plan = classify([obj], Path(org_name))
        validate(plan)
        assert plan.errors == []

        await apply_plan(plan, directory)

        client.create.assert_awaited_once()
        args, _ = client.create.await_args
        assert args[0] == Resource.Workspace
        assert args[1].get("name") == "AP"
        assert "id" not in args[1] or args[1]["id"] is None

        # Folder renamed to AP_[100], file written back with id/url.
        new_path = org_path / "workspaces" / "AP_[100]" / "workspace.json"
        assert os.path.exists(str(new_path))
        with open(str(new_path)) as f:
            body = json.load(f)
        assert body["id"] == 100
        assert body["url"].endswith("/workspaces/100")

    async def test_create_queue_resolves_workspace_url_from_lookup(self, tmp_path):
        org_name = "source"
        org_path = Path(tmp_path) / org_name
        ws_dir = org_path / "workspaces" / "AP_[]"
        queue_dir = ws_dir / "queues" / "Inv_[]"
        org_url = "https://x/api/v1/organizations/1"
        _write_json(ws_dir / "workspace.json", {"name": "AP", "organization": org_url})
        _write_json(queue_dir / "queue.json", {"name": "Inv"})
        _write_json(queue_dir / "schema.json", {"name": "Inv schema", "content": []})

        client = MagicMock()

        async def fake_create(rtype, data):
            # Return distinct ids per type so we can inspect ref resolution.
            if rtype == Resource.Workspace:
                return {"id": 100, "url": "https://x/api/v1/workspaces/100", "name": "AP"}
            if rtype == Resource.Schema:
                return {"id": 200, "url": "https://x/api/v1/schemas/200", "name": "Inv schema"}
            if rtype == Resource.Queue:
                return {"id": 300, "url": "https://x/api/v1/queues/300", "name": "Inv"}
            raise AssertionError(f"unexpected type {rtype}")

        client.create = AsyncMock(side_effect=fake_create)
        directory = _build_directory(Path(tmp_path), org_name, client)

        ws = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "AP_[]" / "workspace.json",
            data={"name": "AP", "organization": org_url},
        )
        queue = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "AP_[]" / "queues" / "Inv_[]" / "queue.json",
            data={"name": "Inv"},
        )
        schema = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "AP_[]" / "queues" / "Inv_[]" / "schema.json",
            data={"name": "Inv schema", "content": []},
        )
        plan = classify([ws, queue, schema], Path(org_name))
        validate(plan)
        assert plan.errors == []

        await apply_plan(plan, directory)

        # The queue create call should receive `workspace` and `schema` URLs.
        queue_call = next(c for c in client.create.await_args_list if c.args[0] == Resource.Queue)
        qdata = queue_call.args[1]
        assert qdata.get("workspace") == "https://x/api/v1/workspaces/100"
        assert qdata.get("schema") == "https://x/api/v1/schemas/200"

    async def test_new_queue_with_sibling_schema_renames_folder_once(self, tmp_path):
        """Regression: schema + queue under the same `_[]` folder must end up in a
        single `_[<queue_id>]/` folder — not split between schema-id and queue-id."""
        org_name = "source"
        org_path = Path(tmp_path) / org_name
        # Pre-existing workspace on disk (already _[123], not new).
        ws_dir = org_path / "workspaces" / "WS_[123]"
        queue_dir = ws_dir / "queues" / "Inv_[]"
        _write_json(ws_dir / "workspace.json", {"id": 123, "url": "https://x/api/v1/workspaces/123", "name": "WS"})
        _write_json(queue_dir / "queue.json", {"name": "Inv"})
        _write_json(queue_dir / "schema.json", {"name": "Inv schema", "content": []})

        client = MagicMock()

        async def fake_create(rtype, data):
            if rtype == Resource.Schema:
                return {"id": 200, "url": "https://x/api/v1/schemas/200", "name": "Inv schema", "content": []}
            if rtype == Resource.Queue:
                return {"id": 300, "url": "https://x/api/v1/queues/300", "name": "Inv"}
            raise AssertionError(f"unexpected type {rtype}")

        client.create = AsyncMock(side_effect=fake_create)
        directory = _build_directory(Path(tmp_path), org_name, client)

        queue = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "WS_[123]" / "queues" / "Inv_[]" / "queue.json",
            data={"name": "Inv"},
        )
        schema = ChangedObject(
            operation=GIT_CHARACTERS.CREATED,
            path=Path(org_name) / "workspaces" / "WS_[123]" / "queues" / "Inv_[]" / "schema.json",
            data={"name": "Inv schema", "content": []},
        )
        plan = classify([queue, schema], Path(org_name))
        validate(plan)
        assert plan.errors == []

        await apply_plan(plan, directory)

        # Only one new folder (named with the queue id) should exist; the schema
        # came along with the rename.
        queues_root = ws_dir / "queues"
        children = sorted(os.listdir(str(queues_root)))
        assert children == ["Inv_[300]"], f"got: {children}"
        assert os.path.exists(str(queues_root / "Inv_[300]" / "queue.json"))
        assert os.path.exists(str(queues_root / "Inv_[300]" / "schema.json"))

        # The queue create should have received the schema URL via the lookup table.
        queue_call = next(c for c in client.create.await_args_list if c.args[0] == Resource.Queue)
        assert queue_call.args[1].get("schema") == "https://x/api/v1/schemas/200"
        assert queue_call.args[1].get("workspace") == "https://x/api/v1/workspaces/123"


class TestFormatApiError:
    def test_field_validation_400(self):
        body = '{"events":["This field is required."],"queues":["This field is required."],"config":["This field is required."]}'
        err = APIClientError("POST", "https://x/api/v1/hooks", 400, body)
        out = format_api_error(err)
        assert "HTTP 400" in out
        assert "events: This field is required." in out
        assert "queues: This field is required." in out
        assert "config: This field is required." in out

    def test_falls_back_for_non_json_body(self):
        err = APIClientError("POST", "https://x/api/v1/hooks", 500, "Internal Server Error")
        out = format_api_error(err)
        # Falls back to APIClientError's default __str__.
        assert "HTTP 500" in out
        assert "Internal Server Error" in out

    def test_passes_through_non_api_exceptions(self):
        e = ValueError("nope")
        assert format_api_error(e) == "nope"


def test_changed_object_display_operation_for_delete():
    """display_operation returns DELETE label for D ops (was incorrectly CREATE)."""
    obj = ChangedObject(
        operation=GIT_CHARACTERS.DELETED,
        path=Path("source/hooks/Foo_[42].json"),
        data={"id": 42},
    )
    assert "DELETE" in obj.display_operation
    assert "CREATE" not in obj.display_operation


@pytest.mark.asyncio
async def test_make_update_request_skips_timestamp_check_for_rename(tmp_path):
    """is_rename=True bypasses check_modified_timestamp (which would otherwise
    fail because non_versioned_object_attributes.json is keyed by old path)."""
    client = MagicMock()
    client._http_client.update = AsyncMock(
        return_value={
            "id": 42,
            "url": "https://x/api/v1/hooks/42",
            "modified_at": "2026-02-02",
            "name": "Renamed",
        }
    )

    upload_dir = UploadOrganizationDirectory.model_construct(
        name="test-org",
        client=client,
        project_path=Path(tmp_path),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
        force=False,
        upload_all=False,
        request_errors=[],
    )

    obj = ChangedObject(
        operation=GIT_CHARACTERS.UPDATED,
        path=Path("test-org/hooks/Renamed_[42].json"),
        data={
            "id": 42,
            "url": "https://x/api/v1/hooks/42",
            "name": "Renamed",
            "modified_at": "2026-01-01",  # local
        },
        is_rename=True,
    )

    # check_modified_timestamp would return False (mismatch). If we forgot to
    # skip it, make_update_request would early-return with a timestamp error.
    with patch(
        "deployment_manager.commands.upload.directory.check_modified_timestamp",
        AsyncMock(return_value=False),
    ) as mock_check, patch(
        "deployment_manager.commands.upload.directory.write_object_to_json",
        AsyncMock(),
    ):
        result = await upload_dir.make_update_request(obj)

    mock_check.assert_not_called()
    assert result is not None
    assert upload_dir.request_errors == []
    client._http_client.update.assert_awaited_once()


@pytest.mark.asyncio
class TestApplyDelete:
    async def test_404_is_idempotent_success(self, tmp_path):
        org_name = "source"
        client = MagicMock()
        err = APIClientError("DELETE", "https://x/api/v1/hooks/42", 404, "not found")
        client.delete = AsyncMock(side_effect=err)
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "hooks" / "Old_[42].json",
            data={"id": 42, "url": "https://x/api/v1/hooks/42"},
        )
        plan = classify([deleted], Path(org_name))
        assert plan.deletes == [deleted]

        await apply_plan(plan, directory)

        client.delete.assert_awaited_once()
        assert directory.request_errors == []

    async def test_schema_409_surfaces_as_error(self, tmp_path):
        """With queue hard-delete + poll, schema 409 should no longer happen in
        practice — but if it does (cross-queue ref, etc.) it's a real error, not
        something we silently swallow."""
        org_name = "source"
        client = MagicMock()
        err = APIClientError(
            "DELETE",
            "https://x/api/v1/schemas/200",
            409,
            '{"detail":"Cannot delete because referenced by deleted queue."}',
        )
        client.delete = AsyncMock(side_effect=err)
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "schema.json",
            data={"id": 200, "url": "https://x/api/v1/schemas/200"},
            resolved_type=Resource.Schema,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        assert len(directory.request_errors) == 1
        assert "409" in directory.request_errors[0]

    async def test_inbox_409_surfaces_as_error(self, tmp_path):
        """Same as schema: inbox 409 is a real error now."""
        org_name = "source"
        client = MagicMock()
        err = APIClientError(
            "DELETE",
            "https://x/api/v1/inboxes/300",
            409,
            '{"detail":"Cannot delete because referenced."}',
        )
        client.delete = AsyncMock(side_effect=err)
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "inbox.json",
            data={"id": 300, "url": "https://x/api/v1/inboxes/300"},
            resolved_type=Resource.Inbox,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        assert len(directory.request_errors) == 1

    async def test_inbox_404_treated_as_already_gone(self, tmp_path):
        """Inboxes are cascade-deleted by their parent queue's hard-delete.
        When the inbox's own DELETE op fires after that, it 404s — this is
        the normal happy path during a queue+inbox DELETE plan and must NOT
        surface as an error."""
        org_name = "source"
        client = MagicMock()
        client.delete = AsyncMock(
            side_effect=APIClientError(
                "DELETE", "https://x/api/v1/inboxes/300", 404, "not found"
            )
        )
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "inbox.json",
            data={"id": 300, "url": "https://x/api/v1/inboxes/300"},
            resolved_type=Resource.Inbox,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        assert directory.request_errors == []

    async def test_workspace_409_surfaces_as_error(self, tmp_path):
        """409 on non-Schema/Inbox types (e.g. workspace) IS surfaced as error."""
        org_name = "source"
        client = MagicMock()
        err = APIClientError(
            "DELETE",
            "https://x/api/v1/workspaces/100",
            409,
            '{"detail":"Cannot delete workspace because it contains queues."}',
        )
        client.delete = AsyncMock(side_effect=err)
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[100]" / "workspace.json",
            data={"id": 100, "url": "https://x/api/v1/workspaces/100"},
            resolved_type=Resource.Workspace,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        assert len(directory.request_errors) == 1

    async def test_queue_uses_delete_after_zero_and_polls_until_404(self, tmp_path, monkeypatch):
        """Queue DELETE should hit `_request("DELETE", queues/{id}, params={delete_after:0})`
        and then poll fetch_one until 404 confirms the row is actually gone."""
        monkeypatch.setattr(apply_mod, "QUEUE_HARD_DELETE_POLL_INTERVAL_S", 0)
        monkeypatch.setattr(apply_mod, "QUEUE_HARD_DELETE_TIMEOUT_S", 5)

        org_name = "source"
        client = MagicMock()
        client._request = AsyncMock(return_value=None)
        # First two polls find it, third returns 404.
        poll_seq = [
            {"id": 999, "status": "deletion_requested"},
            {"id": 999, "status": "deletion_requested"},
            APIClientError("GET", "https://x/api/v1/queues/999", 404, "not found"),
        ]

        async def fake_fetch_one(resource, id_):
            nxt = poll_seq.pop(0)
            if isinstance(nxt, APIClientError):
                raise nxt
            return nxt

        client.fetch_one = fake_fetch_one
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[999]" / "queue.json",
            data={"id": 999, "url": "https://x/api/v1/queues/999"},
            resolved_type=Resource.Queue,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        client._request.assert_awaited_once_with(
            "DELETE", "queues/999", params={"delete_after": "0"}
        )
        assert directory.request_errors == []
        assert poll_seq == []  # all polls consumed

    async def test_queue_timeout_aborts_remaining_deletes(self, tmp_path, monkeypatch):
        """If the queue is still around after the poll deadline, abort — the rest
        of the DELETE phase (schema, workspace, etc.) must not run, since they'd
        409 anyway."""
        monkeypatch.setattr(apply_mod, "QUEUE_HARD_DELETE_POLL_INTERVAL_S", 0)
        monkeypatch.setattr(apply_mod, "QUEUE_HARD_DELETE_TIMEOUT_S", 0)  # never wait

        org_name = "source"
        client = MagicMock()
        client._request = AsyncMock(return_value=None)

        async def stuck_fetch_one(resource, id_):
            return {"id": 999, "status": "deletion_requested"}

        client.fetch_one = stuck_fetch_one
        client.delete = AsyncMock()  # would be called for schema/workspace if not aborted
        directory = _build_directory(Path(tmp_path), org_name, client)

        queue = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[999]" / "queue.json",
            data={"id": 999, "url": "https://x/api/v1/queues/999"},
            resolved_type=Resource.Queue,
        )
        schema = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[999]" / "schema.json",
            data={"id": 200, "url": "https://x/api/v1/schemas/200"},
            resolved_type=Resource.Schema,
        )
        plan = classify([queue, schema], Path(org_name))
        await apply_plan(plan, directory)

        assert len(directory.request_errors) == 1
        assert "Re-run push" in directory.request_errors[0]
        client.delete.assert_not_awaited()

    async def test_queue_404_immediately_skips_polling(self, tmp_path):
        """If the queue is already gone (cascade-deleted by an earlier op), the
        DELETE returns 404 — treat as success, don't poll."""
        org_name = "source"
        client = MagicMock()
        client._request = AsyncMock(
            side_effect=APIClientError("DELETE", "https://x/api/v1/queues/999", 404, "not found")
        )
        client.fetch_one = AsyncMock()
        directory = _build_directory(Path(tmp_path), org_name, client)

        deleted = ChangedObject(
            operation=GIT_CHARACTERS.DELETED,
            path=Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[999]" / "queue.json",
            data={"id": 999, "url": "https://x/api/v1/queues/999"},
            resolved_type=Resource.Queue,
        )
        plan = classify([deleted], Path(org_name))
        await apply_plan(plan, directory)

        assert directory.request_errors == []
        client.fetch_one.assert_not_awaited()
