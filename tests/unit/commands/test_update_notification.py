"""Tests for the new-version notification in commands/update.py.

Covers `notify_if_new_version_available()` — the best-effort check that runs
before any command and prints a panel when a newer GitHub release exists.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import deployment_manager.commands.update as update
from deployment_manager.utils.consts import settings


@pytest.fixture
def cache_path(tmp_path):
    """Point the shared version-check cache at a temp file for each test.

    The root conftest swaps ``tmp_path`` for an async ``anyio.Path``; the
    production code uses synchronous ``pathlib.Path``, so convert it back.
    """
    path = Path(str(tmp_path)) / "version_check.json"
    with patch.object(settings, "VERSION_CHECK_CACHE_PATH", path):
        yield path


def _run(current: str, *, fetched: str | None = None):
    """Run the notifier with a mocked installed version and GitHub response.

    Returns (display_info_mock, fetch_mock) so callers can assert on both the
    notification and whether the network was hit.
    """
    with (
        patch.object(update.importlib.metadata, "version", return_value=current),
        patch.object(update, "_fetch_latest_version_str", return_value=fetched) as fetch_mock,
        patch.object(update, "display_info") as info_mock,
    ):
        update.notify_if_new_version_available()
    return info_mock, fetch_mock


class TestNotifyIfNewVersionAvailable:
    def test_notifies_when_newer_version_available(self, cache_path):
        info_mock, fetch_mock = _run("1.0.0", fetched="2.0.0")

        assert fetch_mock.called
        info_mock.assert_called_once()
        message = info_mock.call_args.args[0]
        assert "2.0.0" in message
        assert "1.0.0" in message
        assert f"{settings.NEW_COMMAND_NAME} {settings.UPDATE_COMMAND_NAME}" in message

    def test_silent_when_up_to_date(self, cache_path):
        info_mock, _ = _run("2.0.0", fetched="2.0.0")
        info_mock.assert_not_called()

    def test_silent_when_current_is_newer(self, cache_path):
        info_mock, _ = _run("3.0.0", fetched="2.0.0")
        info_mock.assert_not_called()

    def test_local_install_is_never_notified(self, cache_path):
        # Poetry installs report 0.0.0 — must skip without even hitting GitHub.
        info_mock, fetch_mock = _run("0.0.0", fetched="2.0.0")
        info_mock.assert_not_called()
        assert not fetch_mock.called

    def test_devrelease_install_is_never_notified(self, cache_path):
        # pip editable installs report a dev release — also skipped.
        info_mock, fetch_mock = _run("1.0.0.dev1", fetched="2.0.0")
        info_mock.assert_not_called()
        assert not fetch_mock.called

    def test_failed_fetch_is_silent(self, cache_path):
        info_mock, fetch_mock = _run("1.0.0", fetched=None)
        assert fetch_mock.called
        info_mock.assert_not_called()

    def test_fetch_throttled_by_fresh_cache(self, cache_path):
        # First run fetches and notifies.
        _, fetch_mock_1 = _run("1.0.0", fetched="2.0.0")
        assert fetch_mock_1.called

        # Second run within the interval reuses the cached latest version
        # (no network) and stays silent (already notified for this version).
        info_mock, fetch_mock_2 = _run("1.0.0", fetched="2.0.0")
        assert not fetch_mock_2.called
        info_mock.assert_not_called()

    def test_refetches_after_interval_elapses(self, cache_path):
        cache_path.write_text(
            json.dumps(
                {
                    "latest_version": "2.0.0",
                    "last_checked": 0,  # epoch 0 => far older than the interval
                }
            )
        )
        _, fetch_mock = _run("1.0.0", fetched="2.5.0")
        assert fetch_mock.called

    def test_notification_throttled_for_same_version(self, cache_path):
        # A previous notification for 2.0.0 was just shown -> stay quiet.
        cache_path.write_text(
            json.dumps(
                {
                    "latest_version": "2.0.0",
                    "last_checked": time.time(),
                    "last_notified_version": "2.0.0",
                    "last_notified_at": time.time(),
                }
            )
        )
        info_mock, fetch_mock = _run("1.0.0", fetched="2.0.0")
        assert not fetch_mock.called  # cache fresh
        info_mock.assert_not_called()  # throttled

    def test_shared_cache_holds_both_fetch_and_notify_state(self, cache_path):
        _run("1.0.0", fetched="2.0.0")

        cache = json.loads(cache_path.read_text())
        assert cache["latest_version"] == "2.0.0"
        assert "last_checked" in cache
        assert cache["last_notified_version"] == "2.0.0"
        assert "last_notified_at" in cache

    def test_unreadable_install_version_is_silent(self, cache_path):
        # importlib.metadata raising must not crash the command.
        with (
            patch.object(
                update.importlib.metadata,
                "version",
                side_effect=Exception("no metadata"),
            ),
            patch.object(update, "_fetch_latest_version_str") as fetch_mock,
            patch.object(update, "display_info") as info_mock,
        ):
            update.notify_if_new_version_available()
        assert not fetch_mock.called
        info_mock.assert_not_called()
