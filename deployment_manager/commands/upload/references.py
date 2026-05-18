"""Filesystem-derived reference resolution for newly-created objects.

When the apply phase is about to POST a new object to Rossum, some of its
fields must point to URLs of related objects (parent or sibling). For new
objects in the same push, those URLs are not known until the related object
is created. This module fills them in by walking the local filesystem and
consulting the lookup table populated as creates succeed.

For UPDATE/DELETE we don't touch references — the JSON is sent as-is.
"""

from __future__ import annotations

from typing import Optional

from anyio import Path
from rossum_api.domain_logic.resources import Resource

from deployment_manager.common.read_write import read_object_from_json


async def resolve_references(
    op,
    lookup: dict[str, str],
    org_path: Path,
) -> None:
    """Mutate `op.data` so that filesystem-derived URL fields are populated.

    `lookup` maps a placeholder-path-string to a real URL. We use it to find
    URLs of newly-created parents/siblings; for parents/siblings that exist
    on the remote already, we read their JSON from disk and pull the `url`
    out.
    """
    rtype = op.resolved_type or op.type

    # Use the placeholder_path (path inside the org dir) for parent walking.
    rel = op.placeholder_path or op.path

    if rtype == Resource.Workspace:
        await _fill_url(op, "organization", Path("organization.json"), lookup, org_path)
    elif rtype == Resource.Queue:
        await _fill_url(op, "workspace", _parent_workspace_path(rel), lookup, org_path)
        await _fill_url(op, "schema", _sibling_schema_path(rel), lookup, org_path)
    elif rtype == Resource.Schema:
        # Schema's queues list — Rossum auto-assigns once the queue is POSTed,
        # but if the parent queue already exists on remote we must include it.
        url = await _resolve_url(_parent_queue_path(rel), lookup, org_path)
        if url:
            op.data["queues"] = [url]
        else:
            op.data.setdefault("queues", [])
    elif rtype == Resource.Inbox:
        url = await _resolve_url(_parent_queue_path(rel), lookup, org_path)
        if url:
            op.data["queues"] = [url]
    elif rtype == Resource.EngineField:
        await _fill_url(op, "engine", _parent_engine_path(rel), lookup, org_path)
    # Hook / Rule / Engine: no filesystem-derived refs.


def _parent_workspace_path(rel: Path) -> Optional[Path]:
    """For .../workspaces/<X>/queues/<Y>/queue.json — return the workspace.json path."""
    parts = rel.parts
    for i, p in enumerate(parts):
        if p == "workspaces" and i + 2 < len(parts):
            return Path(*parts[: i + 2]) / "workspace.json"
    return None


def _parent_queue_path(rel: Path) -> Optional[Path]:
    """For .../queues/<X>/{schema,inbox}.json — return the queue.json path."""
    parts = rel.parts
    for i, p in enumerate(parts):
        if p == "queues" and i + 2 < len(parts):
            return Path(*parts[: i + 2]) / "queue.json"
    return None


def _sibling_schema_path(rel: Path) -> Optional[Path]:
    """For .../queues/<X>/queue.json — return the sibling schema.json."""
    return rel.parent / "schema.json"


def _parent_engine_path(rel: Path) -> Optional[Path]:
    """For .../engines/<X>/engine_fields/<Y>.json — return the engine.json path."""
    parts = rel.parts
    for i, p in enumerate(parts):
        if p == "engines" and i + 2 < len(parts):
            return Path(*parts[: i + 2]) / "engine.json"
    return None


async def _fill_url(op, field: str, target_path: Optional[Path], lookup: dict[str, str], org_path: Path) -> None:
    if target_path is None:
        return
    url = await _resolve_url(target_path, lookup, org_path)
    if url:
        op.data[field] = url


async def _resolve_url(rel_target: Path, lookup: dict[str, str], org_path: Path) -> Optional[str]:
    """Return the URL for the object whose local path is `rel_target` (relative
    to the org root). Checks the lookup table first, then falls back to the
    file's own `url` field.
    """
    key = str(rel_target)
    if key in lookup:
        return lookup[key]

    abs_target = org_path / rel_target
    if not await abs_target.exists():
        return None
    try:
        data = await read_object_from_json(abs_target)
    except Exception:
        return None
    return data.get("url")
