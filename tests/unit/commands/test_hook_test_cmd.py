"""Tests for commands/hook/test.py — the `prd2 hook test` action."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deployment_manager.commands.hook.test import test_hook as _run_hook_test
from deployment_manager.common.read_write import write_object_to_json


def _make_client_mock(base_url: str = "https://api.example.com/v1", request_json_response: dict = None):
    client = MagicMock()
    client._http_client = MagicMock()
    client._http_client.base_url = base_url
    client._http_client.request_json = AsyncMock(
        return_value=request_json_response or {"response": {"messages": []}, "log": ""}
    )
    return client


@pytest.mark.asyncio
class TestTestHook:
    async def test_uses_payload_file_when_provided(self, tmp_path):
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[42].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 42, "name": "H", "config": {}, "events": []})

        payload_path = project / "payload.json"
        await write_object_to_json(payload_path, {"event": "x", "annotation": {}})

        client = _make_client_mock(request_json_response={"response": {"ok": True}, "log": "hi"})

        await _run_hook_test(hook_path=hook_path, payload_path=payload_path, client=client)

        # Confirm the request body contains the payload from the file
        kwargs = client._http_client.request_json.call_args.kwargs
        assert kwargs["url"] == "hooks/42/test"
        assert kwargs["json"]["payload"] == {"event": "x", "annotation": {}}

    async def test_generates_payload_when_no_payload_path(self, tmp_path):
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[42].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 42, "name": "H", "config": {}, "events": ["x.y"]})

        client = _make_client_mock()
        with patch(
            "deployment_manager.commands.hook.test.generate_hook_payload",
            new=AsyncMock(return_value={"event": "x", "action": "y"}),
        ) as gen_mock:
            await _run_hook_test(hook_path=hook_path, annotation_url="1", client=client)

        gen_mock.assert_awaited_once()
        body = client._http_client.request_json.call_args.kwargs["json"]
        assert body["payload"] == {"event": "x", "action": "y"}

    async def test_returns_when_generated_payload_is_empty(self, tmp_path):
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[42].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 42, "name": "H", "config": {}, "events": []})

        client = _make_client_mock()
        with patch(
            "deployment_manager.commands.hook.test.generate_hook_payload",
            new=AsyncMock(return_value=None),
        ):
            await _run_hook_test(hook_path=hook_path, client=client)

        # No /test request was sent
        client._http_client.request_json.assert_not_called()

    async def test_overrides_code_with_local_py_file(self, tmp_path):
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[42].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(
            hook_path,
            {
                "id": 42,
                "name": "H",
                "config": {"runtime": "python3.12", "code": "old_code"},
                "events": [],
            },
        )
        # Local .py file contains updated code
        py_path = hook_path.with_suffix(".py")
        await py_path.write_text("def rossum_hook_request_handler(payload):\n    pass\n")

        payload_path = project / "p.json"
        await write_object_to_json(payload_path, {"event": "x"})

        client = _make_client_mock()
        await _run_hook_test(hook_path=hook_path, payload_path=payload_path, client=client)

        body = client._http_client.request_json.call_args.kwargs["json"]
        assert body["config"]["runtime"] == "python3.12"
        assert "rossum_hook_request_handler" in body["config"]["code"]

    async def test_swallows_exceptions(self, tmp_path):
        project = tmp_path / "project"
        hook_path = project / "my-org" / "sub" / "hooks" / "Hook_[42].json"
        await hook_path.parent.mkdir(parents=True)
        await write_object_to_json(hook_path, {"id": 42, "name": "H", "config": {}, "events": []})

        payload_path = project / "p.json"
        await write_object_to_json(payload_path, {"event": "x"})

        client = _make_client_mock()
        client._http_client.request_json = AsyncMock(side_effect=RuntimeError("boom"))

        # Must not raise
        await _run_hook_test(hook_path=hook_path, payload_path=payload_path, client=client)
