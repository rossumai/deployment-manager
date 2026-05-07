"""Apply phase for `prd2 push`: takes a validated PushPlan and executes it
against the Rossum API.

CREATEs are sequential (each may produce a URL referenced by the next).
UPDATEs and DELETEs run with the existing concurrency primitive.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Optional

from anyio import Path
from rich import print as pprint
from rossum_api import APIClientError
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.upload.placeholder import (
    replace_first_placeholder,
)
from deployment_manager.commands.upload.plan import (
    PushPlan,
    determine_type_from_local_path,
    order_creates,
    order_deletes,
)
from deployment_manager.commands.upload.references import resolve_references
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    write_object_to_json,
)
from deployment_manager.utils.functions import gather_with_concurrency

# Queue DELETE uses `?delete_after=0` to skip Rossum's soft-delete grace
# window. The server still takes a moment to actually drop the row; we poll
# until GET returns 404 so the schema/inbox DELETEs that follow don't see a
# referencing-queue 409. If the queue isn't gone within the timeout, we abort
# the rest of the push so the user can re-run when Rossum has caught up.
QUEUE_HARD_DELETE_POLL_INTERVAL_S = 2
QUEUE_HARD_DELETE_TIMEOUT_S = 30


class _AbortDeletes(Exception):
    """Raised to bail out of the DELETE phase mid-stream (timeout, fatal error)."""


async def apply_plan(
    plan: PushPlan,
    directory,
) -> None:
    """Run a validated plan. `directory` is an UploadOrganizationDirectory.

    Mutates `directory.request_errors` on per-op failure so the caller can
    surface them after the run.
    """
    project_path: Path = directory.project_path
    lookup: dict[str, str] = {}  # rel_path_str -> created url
    placeholder_id_lookup: dict[str, int] = {}  # placeholder folder/file segment -> created id

    for op in order_creates(plan):
        try:
            await _create_one(op, directory, lookup, placeholder_id_lookup, project_path)
        except Exception as e:
            directory.request_errors.append(op.create_failure_message(format_api_error(e)))
            return

    if plan.updates:
        await gather_with_concurrency(
            *(directory.make_update_request(object=op) for op in plan.updates)
        )

    # Sequential by type — Rossum FK constraints (workspace can't be deleted
    # while it has queues) make a single concurrent gather unsafe. Within a
    # type, concurrent is fine.
    if plan.deletes:
        ordered = order_deletes(plan)
        bucket: list = []
        bucket_type = None
        try:
            for op in ordered:
                if bucket_type is None or op.type == bucket_type:
                    bucket.append(op)
                    bucket_type = op.type
                else:
                    await gather_with_concurrency(*(_delete_one(o, directory) for o in bucket))
                    bucket = [op]
                    bucket_type = op.type
            if bucket:
                await gather_with_concurrency(*(_delete_one(o, directory) for o in bucket))
        except _AbortDeletes:
            return


async def _create_one(
    op,
    directory,
    lookup: dict[str, str],
    placeholder_id_lookup: dict[str, int],
    project_path: Path,
) -> None:
    rtype = op.resolved_type or determine_type_from_local_path(op.placeholder_path or op.path)
    if rtype is None:
        raise Exception(f"Cannot determine resource type for {op.path}")
    op.resolved_type = rtype

    # Parents already created have had their `_[]` replaced on disk; mirror
    # that here so we read the file from where it actually lives now.
    rel_current_path = _substitute_parent_placeholders(op.path, placeholder_id_lookup)
    abs_current_path = project_path / rel_current_path

    org_path = project_path / directory.name
    await resolve_references(op, lookup, org_path)

    # Defensive — the inbox-under-existing-queue create path doesn't get the
    # validator's id/url check, and programmatic callers may bypass it too.
    op.data.pop("id", None)
    op.data.pop("url", None)

    result = await directory.client._http_client.create(rtype, op.data)

    new_id = result.get("id")
    new_url = result.get("url")

    # Only the segment THIS object owns goes into placeholder_id_lookup;
    # ancestor `_[]` segments belong to other ops.
    if op.placeholder_path is not None:
        lookup[str(op.placeholder_path)] = new_url
        own_segment = _own_placeholder_segment(op.placeholder_path, rtype)
        if own_segment is not None:
            placeholder_id_lookup[own_segment] = new_id

    # Schema and inbox keep their filename and stay in place — the parent
    # queue's create will move the folder around them.
    if rtype in (Resource.Schema, Resource.Inbox):
        abs_new_path = abs_current_path
    else:
        abs_new_path = (
            replace_first_placeholder(abs_current_path, new_id)
            if "_[]" in str(abs_current_path)
            else abs_current_path
        )

    await _rename_for_create(rtype, abs_current_path, abs_new_path, new_id)

    # Writeback so future runs see the real id/url.
    await write_object_to_json(abs_new_path, result, rtype)

    if rtype == Resource.Hook:
        code_path = create_custom_hook_code_path(abs_current_path, op.data)
        if code_path and await code_path.exists():
            new_code_path = replace_first_placeholder(code_path, new_id)
            os.rename(str(code_path), str(new_code_path))

    pprint(op.create_success_message())


def _own_placeholder_segment(placeholder_path: Path, rtype: Resource) -> Optional[str]:
    """Return the placeholder segment this object OWNS, or None.

    Folder-based types (workspace/queue/engine) own the folder right above the
    object file. File-based types (hook/rule/engine_field) own the file's
    stem. Schema and inbox have no own placeholder — they live inside their
    parent queue's folder.
    """
    parts = placeholder_path.parts
    if rtype in (Resource.Workspace, Resource.Queue, Resource.Engine):
        if len(parts) >= 2 and parts[-2].endswith("_[]"):
            return parts[-2]
        return None
    if rtype in (Resource.Hook, Resource.Rule, Resource.EngineField):
        name = parts[-1]
        if name.endswith("_[].json") or name.endswith("_[].py") or name.endswith("_[].js"):
            return name.rsplit(".", 1)[0]
        return None
    return None  # Schema, Inbox


def _substitute_parent_placeholders(path: Path, placeholder_id_lookup: dict[str, int]) -> Path:
    """Substitute already-created parent placeholders into `path` so we read
    the file from where it actually lives on disk right now.
    """
    if not placeholder_id_lookup:
        return path
    parts = list(path.parts)
    for i, part in enumerate(parts):
        if part in placeholder_id_lookup:
            parts[i] = part.replace("_[]", f"_[{placeholder_id_lookup[part]}]", 1)
    return Path(*parts)


async def _rename_for_create(
    rtype: Resource,
    current_path: Path,
    new_path: Path,
    new_id: int | str,
) -> None:
    """Rename the just-created object's filesystem location.

    For folder-based resources (workspace/queue/engine), the *folder* is
    renamed (so all children come along). For file-based resources
    (hook/rule/engine_field), the file itself is renamed. Schema and inbox
    keep their filenames — they live inside a queue folder that's already at
    its final name (or just got renamed by the queue create).
    """
    if str(current_path) == str(new_path):
        return

    if rtype in (Resource.Schema, Resource.Inbox):
        return

    if rtype in (Resource.Workspace, Resource.Queue, Resource.Engine):
        old_dir = current_path.parent
        new_dir = new_path.parent
        if str(old_dir) != str(new_dir):
            os.rename(str(old_dir), str(new_dir))
        return

    os.rename(str(current_path), str(new_path))


async def _delete_one(op, directory) -> None:
    if op.type == Resource.Queue:
        await _delete_queue_hard(op, directory)
        return
    try:
        if not op.id:
            return
        # No timestamp check: the local file is gone, `data` was rebuilt from
        # path/git and has no `modified_at`. The plan-confirm prompt is the
        # opt-in.
        await directory.client._http_client.delete(op.type, op.id)
        pprint(op.create_success_message())
    except APIClientError as e:
        if e.status_code == 404:
            pprint(f"{op.create_success_message()} (already gone — likely cascade)")
            return
        directory.request_errors.append(op.create_failure_message(format_api_error(e)))
    except Exception as e:
        directory.request_errors.append(op.create_failure_message(format_api_error(e)))


async def _delete_queue_hard(op, directory) -> None:
    """Hard-delete a queue via `?delete_after=0` and poll until it's gone."""
    if not op.id:
        return
    try:
        await directory.client._http_client._request(
            "DELETE", f"queues/{op.id}", params={"delete_after": "0"}
        )
    except APIClientError as e:
        if e.status_code == 404:
            pprint(f"{op.create_success_message()} (already gone — likely cascade)")
            return
        directory.request_errors.append(op.create_failure_message(format_api_error(e)))
        raise _AbortDeletes()
    except Exception as e:
        directory.request_errors.append(op.create_failure_message(format_api_error(e)))
        raise _AbortDeletes()

    deadline = time.monotonic() + QUEUE_HARD_DELETE_TIMEOUT_S
    while True:
        try:
            await directory.client._http_client.fetch_one(Resource.Queue, op.id)
        except APIClientError as e:
            if e.status_code == 404:
                pprint(op.create_success_message())
                return
            directory.request_errors.append(op.create_failure_message(format_api_error(e)))
            raise _AbortDeletes()

        if time.monotonic() >= deadline:
            directory.request_errors.append(
                op.create_failure_message(
                    f"Queue still present after {QUEUE_HARD_DELETE_TIMEOUT_S}s of "
                    "polling its hard-delete. Re-run push in a minute — Rossum "
                    "should have caught up by then."
                )
            )
            raise _AbortDeletes()
        await asyncio.sleep(QUEUE_HARD_DELETE_POLL_INTERVAL_S)


def format_api_error(e: Exception) -> str:
    """Pretty-print an APIClientError so field-validation 4xx responses come
    out as a readable list. Falls back to str(e) if the body isn't a JSON
    field-error map.
    """
    if not isinstance(e, APIClientError):
        return str(e)
    body = e.error if isinstance(e.error, str) else None
    if not body:
        return str(e)
    try:
        parsed = json.loads(body)
    except (ValueError, TypeError):
        return str(e)
    if not isinstance(parsed, dict):
        return str(e)

    field_lines = []
    other_lines = []
    for key, val in parsed.items():
        if isinstance(val, list) and val and all(isinstance(v, str) for v in val):
            for msg in val:
                field_lines.append(f"  - {key}: {msg}")
        elif isinstance(val, str):
            other_lines.append(f"  - {key}: {val}")
        else:
            other_lines.append(f"  - {key}: {val!r}")
    if not field_lines and not other_lines:
        return str(e)

    summary = f"Rossum rejected the request (HTTP {e.status_code})."
    return "\n".join([summary, *field_lines, *other_lines])
