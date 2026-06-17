"""Tests for commands/hook/payload.py — generate_hook_payload and generate_and_save_hook_payload."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deployment_manager.commands.hook.payload import (
    STATUS_REQUIRING_EVENTS,
    generate_and_save_hook_payload,
    generate_hook_payload,
)
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json


def _make_questionary_mock(answer):
    async def _fake_ask_async():
        return answer

    m = MagicMock()
    m.ask_async = _fake_ask_async
    return m


def _make_client_mock(base_url: str = "https://api.example.com/v1", request_json_response: dict = None):
    """Build a fake API client that mimics the parts payload.py touches."""
    client = MagicMock()
    client._http_client = MagicMock()
    client._http_client.base_url = base_url
    client._http_client.request_json = AsyncMock(return_value=request_json_response or {"event": "ok"})
    return client


@pytest.mark.asyncio
class TestGenerateHookPayload:
    async def test_returns_none_when_hook_file_missing(self, tmp_path):
        # load_hook_object returns None when the file can't be loaded
        result = await generate_hook_payload(hook_path=tmp_path / "missing.json")
        assert result is None

    async def test_returns_none_when_no_annotation_url_provided(self, tmp_path):
        # Build a project structure so the helpers don't blow up.
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        await write_object_to_json(hook_path, {"id": 1, "name": "Hook", "events": ["annotation_content.user_update"]})

        client = _make_client_mock()
        # questionary asks for the annotation; user gives nothing
        with patch(
            "deployment_manager.commands.hook.payload.questionary.text",
            return_value=_make_questionary_mock(""),
        ):
            result = await generate_hook_payload(hook_path=hook_path, client=client)
        assert result is None

    async def test_returns_none_when_no_events(self, tmp_path):
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        await write_object_to_json(hook_path, {"id": 1, "name": "Hook", "events": []})

        client = _make_client_mock()
        result = await generate_hook_payload(hook_path=hook_path, annotation_url="42", client=client)
        assert result is None

    async def test_numeric_annotation_id_is_expanded_into_url(self, tmp_path):
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": ["invoice_postprocess.created"]})

        client = _make_client_mock(base_url="https://api.example.com/v1")
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock(["invoice_postprocess", "created"]),
        ):
            await generate_hook_payload(hook_path=hook_path, annotation_url="42", client=client)

        # request_json was called with the annotation URL constructed from base_url + /annotations/42
        kwargs = client._http_client.request_json.call_args.kwargs
        body = kwargs["json"]
        assert body["annotation"] == "https://api.example.com/v1/annotations/42"
        assert kwargs["url"] == "hooks/1/generate_payload"
        assert kwargs["method"] == "POST"

    async def test_frontend_url_is_converted_to_api_url(self, tmp_path):
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": ["invoice_postprocess.created"]})

        client = _make_client_mock(base_url="https://api.example.com/v1")
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock(["invoice_postprocess", "created"]),
        ):
            await generate_hook_payload(
                hook_path=hook_path,
                annotation_url="https://elis.rossum.ai/document/9999?queue=1",
                client=client,
            )

        body = client._http_client.request_json.call_args.kwargs["json"]
        assert body["annotation"] == "https://api.example.com/v1/annotations/9999"

    async def test_status_requiring_events_add_status_field(self, tmp_path):
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        # Use one of STATUS_REQUIRING_EVENTS as the event prefix
        event = STATUS_REQUIRING_EVENTS[0]
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": [f"{event}.created"]})

        client = _make_client_mock()
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock([event, "created"]),
        ), patch(
            "deployment_manager.commands.hook.payload.questionary.text",
            return_value=_make_questionary_mock("to_review"),
        ):
            await generate_hook_payload(hook_path=hook_path, annotation_url="1", client=client)

        body = client._http_client.request_json.call_args.kwargs["json"]
        assert body["status"] == "to_review"
        assert body["event"] == event
        assert body["action"] == "created"

    async def test_returns_request_json_response(self, tmp_path):
        org_dir = tmp_path / "my-org" / "sub" / "hooks"
        await org_dir.mkdir(parents=True)
        hook_path = org_dir / "Hook_[1].json"
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": ["invoice_postprocess.created"]})

        expected = {"event": "invoice_postprocess", "action": "created", "annotation": {}}
        client = _make_client_mock(request_json_response=expected)
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock(["invoice_postprocess", "created"]),
        ):
            result = await generate_hook_payload(hook_path=hook_path, annotation_url="1", client=client)

        assert result == expected


@pytest.mark.asyncio
class TestGenerateAndSaveHookPayload:
    async def test_writes_payload_to_file(self, tmp_path):
        # Set up project / org / sub / hooks layout so get_project_path_from_hook_path resolves correctly
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[1].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": ["invoice_postprocess.created"]})

        client = _make_client_mock(request_json_response={"event": "invoice_postprocess"})
        # User picks the only event and a relative output path
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock(["invoice_postprocess", "created"]),
        ), patch(
            "deployment_manager.commands.hook.payload.get_filepath_from_user",
            new=AsyncMock(return_value=project / "payloads" / "out.json"),
        ):
            await generate_and_save_hook_payload(
                hook_path=hook_path, annotation_url="1", client=client
            )

        assert await (project / "payloads" / "out.json").exists()
        data = await read_object_from_json(project / "payloads" / "out.json")
        assert data == {"event": "invoice_postprocess"}

    async def test_no_payload_means_no_file_written(self, tmp_path):
        # Hook with no events -> generate_hook_payload returns None -> nothing written
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[1].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": []})

        client = _make_client_mock()
        save_mock = AsyncMock()
        with patch(
            "deployment_manager.commands.hook.payload.get_filepath_from_user",
            new=save_mock,
        ):
            await generate_and_save_hook_payload(
                hook_path=hook_path, annotation_url="1", client=client
            )
        save_mock.assert_not_called()

    async def test_swallows_exceptions(self, tmp_path):
        # If generate_hook_payload raises, error is reported but does not propagate
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[1].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 1, "name": "H", "events": ["x.y"]})

        client = _make_client_mock()
        client._http_client.request_json = AsyncMock(side_effect=RuntimeError("boom"))
        with patch(
            "deployment_manager.commands.hook.payload.questionary.select",
            return_value=_make_questionary_mock(["x", "y"]),
        ):
            # Must not raise
            await generate_and_save_hook_payload(
                hook_path=hook_path, annotation_url="1", client=client
            )
