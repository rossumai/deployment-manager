"""Pure planning module for `prd2 push`.

Turns a list of git-detected changes into a `PushPlan` with ordered create /
update / delete operations and a list of validation errors. No I/O against
the Rossum API except the existing pulled-not-committed lookup, which is
done in `dependencies.mark_unstaged_objects_as_updated` before this module
is invoked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from anyio import Path
from rich import print as pprint
from rich.panel import Panel
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.upload.placeholder import path_has_own_placeholder
from deployment_manager.utils.consts import GIT_CHARACTERS, settings

# Type-level topo order used for CREATE apply ordering; reverse is used for DELETE.
CREATE_TYPE_ORDER: list[Resource] = [
    Resource.Workspace,
    Resource.Engine,
    Resource.EngineField,
    Resource.Schema,
    Resource.Queue,
    Resource.Inbox,
    Resource.Hook,
    Resource.Rule,
]

DELETE_TYPE_ORDER: list[Resource] = list(reversed(CREATE_TYPE_ORDER))


CREATE_OPS = (
    GIT_CHARACTERS.CREATED,
    GIT_CHARACTERS.CREATED_STAGED,
    GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
)
UPDATE_OPS = (GIT_CHARACTERS.UPDATED, GIT_CHARACTERS.PARTIALLY_UPADTED)


@dataclass
class PushPlan:
    creates: list = field(default_factory=list)
    updates: list = field(default_factory=list)
    deletes: list = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_structural_changes(self) -> bool:
        return bool(self.creates or self.deletes)

    @property
    def is_empty(self) -> bool:
        return not (self.creates or self.updates or self.deletes)


def determine_type_from_local_path(path: Path) -> Optional[Resource]:
    """Determine a creatable Rossum resource type from a local path.

    Works for paths that may contain `_[]` placeholders. Returns None if the
    path doesn't match any creatable shape.
    """
    parts = path.parts
    if not parts:
        return None

    name = parts[-1]
    # Workspace: */workspaces/<X>/workspace.json
    if name == "workspace.json" and len(parts) >= 3 and parts[-3] == "workspaces":
        return Resource.Workspace
    # Queue: */queues/<X>/queue.json
    if name == "queue.json" and len(parts) >= 3 and parts[-3] == "queues":
        return Resource.Queue
    # Schema: */queues/<X>/schema.json
    if name == "schema.json" and len(parts) >= 3 and parts[-3] == "queues":
        return Resource.Schema
    # Inbox: */queues/<X>/inbox.json
    if name == "inbox.json" and len(parts) >= 3 and parts[-3] == "queues":
        return Resource.Inbox
    # Engine: */engines/<X>/engine.json
    if name == "engine.json" and len(parts) >= 3 and parts[-3] == "engines":
        return Resource.Engine
    # Engine field: */engines/<X>/engine_fields/<Y>.json
    if (
        len(parts) >= 4
        and parts[-2] == "engine_fields"
        and parts[-4] == "engines"
        and name.endswith(".json")
    ):
        return Resource.EngineField
    # Hook: */hooks/<X>.json
    if len(parts) >= 2 and parts[-2] == "hooks" and name.endswith(".json"):
        return Resource.Hook
    # Rule: */rules/<X>.json
    if len(parts) >= 2 and parts[-2] == "rules" and name.endswith(".json"):
        return Resource.Rule
    return None


def is_new_path(path: Path) -> bool:
    """True if this path itself, or any of its ancestor folders, has `_[]`.

    A schema.json under a `MyQueue_[]/` parent counts as new even though the
    file's own name has no placeholder.
    """
    return path_has_own_placeholder(path)


def classify(
    changed_objects: list,
    org_path: Path,
) -> PushPlan:
    """Sort `ChangedObject`s into a PushPlan, populating is_new / placeholder_path.

    Two-pass:
      1. Index DELETE ops by id so we can match renames (D + ?? with same id).
      2. Walk the rest, classifying each op. Renames collapse to a single
         UPDATE that PATCHes `name`; the matching delete is dropped.
    """
    plan = PushPlan()

    deletes: list = [
        o for o in changed_objects if o.operation == GIT_CHARACTERS.DELETED
    ]
    deletes_by_id: dict[int, object] = {}
    for d in deletes:
        d_id = d.data.get("id") or _parse_id_from_path(d.path)
        if d_id is not None:
            deletes_by_id[int(d_id)] = d

    consumed_delete_ids: set[int] = set()

    for obj in changed_objects:
        if obj.operation == GIT_CHARACTERS.DELETED:
            continue  # processed below

        rel_path = strip_org_prefix(obj.path, org_path)

        if obj.operation in UPDATE_OPS:
            # Pair UPDATE-at-new-path with DELETE-at-old-path (from a rename)
            # so we don't both update and delete the same live object.
            obj_id = obj.data.get("id")
            if obj_id is not None and int(obj_id) in deletes_by_id:
                consumed_delete_ids.add(int(obj_id))
                obj.is_rename = True
            plan.updates.append(obj)
            continue

        if obj.operation in CREATE_OPS:
            has_id = bool(obj.data.get("id"))
            has_url = bool(obj.data.get("url"))
            is_new = is_new_path(rel_path)

            if is_new:
                obj.is_new = True
                obj.placeholder_path = rel_path
                if has_id or has_url:
                    plan.errors.append(
                        f"{obj.path}: new object (path uses '_[]') but JSON still has an "
                        "id/url. Clear them so push can POST a fresh object."
                    )
                    continue
                plan.creates.append(obj)
                continue

            # Path has no `_[]`. If the JSON has a real id+url, this is either
            # a rename (matches a D of the same id) or pulled-not-committed
            # for an object whose remote disappeared.
            if has_id and has_url:
                obj_id = int(obj.data["id"])
                if obj_id in deletes_by_id:
                    # Rename: collapse to UPDATE.
                    consumed_delete_ids.add(obj_id)
                    obj.operation = GIT_CHARACTERS.UPDATED
                    obj.is_rename = True
                    plan.updates.append(obj)
                    continue
                plan.errors.append(
                    f"{obj.path}: file has an id ({obj_id}) but the path lacks the '_[]' "
                    "placeholder and the remote object was not found. Either delete the "
                    "local id/url to push as new, or pull to refresh."
                )
                continue

            # Inbox filenames never carry `_[]` — a no-id inbox.json under
            # an existing queue is a valid CREATE.
            if rel_path.parts and rel_path.parts[-1] == "inbox.json":
                obj.is_new = True
                obj.placeholder_path = rel_path
                plan.creates.append(obj)
                continue

            plan.errors.append(
                f"{obj.path}: uncommitted file with no id/url and no '_[]' placeholder — "
                "cannot tell whether to create or update. Rename to use '_[]' to create, "
                "or pull to refresh."
            )
            continue

        plan.errors.append(f"{obj.path}: unrecognized git op '{obj.operation}'.")

    for d in deletes:
        d_id = d.data.get("id") or _parse_id_from_path(d.path)
        if d_id is not None and int(d_id) in consumed_delete_ids:
            continue  # paired into a rename
        plan.deletes.append(d)

    return plan


def _parse_id_from_path(path: Path) -> Optional[int]:
    """Try to extract the `_[<id>]` id from any segment of the path."""
    import re

    pat = re.compile(r"_\[(\d+)\]")
    for part in path.parts:
        m = pat.search(part)
        if m:
            return int(m.group(1))
    return None


def strip_org_prefix(path: Path, org_path: Path) -> Path:
    """Strip the org subdir prefix from a git-relative path, if present.

    Git status emits paths relative to the repo root, so `path` may look like
    `myorg/workspaces/Foo_[]/workspace.json`. The placeholder check should
    look only at the org-internal portion.
    """
    try:
        return path.relative_to(org_path)
    except ValueError:
        # The org_path may itself include a leading slash or differ; fall back
        # to a string-based strip.
        org_str = str(org_path).rstrip("/") + "/"
        path_str = str(path)
        if path_str.startswith(org_str):
            return Path(path_str[len(org_str) :])
        return path


# Required-on-create fields per type. Fields auto-resolved from the local
# filesystem at apply time (workspace.organization, queue.workspace,
# queue.schema, schema.queues, inbox.queues, engine_field.engine) are
# intentionally NOT listed here — the user doesn't write them by hand.
# `type` for Hook is also omitted: the API defaults it to "webhook"; the
# runtime/code consistency check below catches function hooks missing runtime.
REQUIRED_FIELDS: dict[Resource, list[str]] = {
    Resource.Workspace: ["name"],
    Resource.Queue: ["name"],
    Resource.Schema: ["name", "content"],
    Resource.Inbox: ["name"],
    Resource.Hook: ["name", "events", "queues", "config"],
    Resource.Rule: ["name"],
    Resource.Engine: ["name", "description"],
    Resource.EngineField: ["name"],
}


def validate(plan: PushPlan) -> None:
    """Add validation errors to `plan.errors` in place. Idempotent."""
    creates_by_placeholder: dict[str, object] = {}

    for op in plan.creates:
        rtype = determine_type_from_local_path(op.placeholder_path or op.path)
        if rtype is None:
            plan.errors.append(
                f"{op.path}: cannot determine resource type from path layout."
            )
            continue
        op.resolved_type = rtype  # cached for apply

        # Required fields — presence-based check (empty list/dict is OK)
        missing = [
            f
            for f in REQUIRED_FIELDS.get(rtype, [])
            if f not in op.data or op.data.get(f) in (None, "")
        ]
        if missing:
            plan.errors.append(
                f"{op.path}: new {rtype.value} missing required field(s): {', '.join(missing)}"
            )

        # New queue must have sibling schema.json (creating-from-scratch case)
        if rtype == Resource.Queue:
            sibling_schema = op.path.parent / "schema.json"
            schema_present = any(
                _samefile(o.path, sibling_schema) for o in plan.creates
            ) or _file_exists_sync(sibling_schema)
            if not schema_present:
                plan.errors.append(
                    f"{op.path}: new queue requires a sibling schema.json (Rossum's queue "
                    "creation endpoint requires a schema)."
                )

        # New schema/inbox must have a parent queue (placeholder or existing)
        if rtype in (Resource.Schema, Resource.Inbox):
            parent_queue_dir = op.path.parent
            queue_json = parent_queue_dir / "queue.json"
            if not _file_exists_sync(queue_json) and not any(
                _samefile(o.path, queue_json) for o in plan.creates
            ):
                plan.errors.append(
                    f"{op.path}: new {rtype.value[:-1]} has no parent queue.json next to it."
                )

        # Inbox needs one of email_prefix or email (API cross-field rule).
        if rtype == Resource.Inbox:
            if not op.data.get("email_prefix") and not op.data.get("email"):
                plan.errors.append(
                    f"{op.path}: new inbox needs one of `email_prefix` or `email`."
                )

        # Engine field must have parent engine
        if rtype == Resource.EngineField:
            parent_engine_dir = op.path.parent.parent
            engine_json = parent_engine_dir / "engine.json"
            if not _file_exists_sync(engine_json) and not any(
                _samefile(o.path, engine_json) for o in plan.creates
            ):
                plan.errors.append(
                    f"{op.path}: new engine_field has no parent engine.json."
                )

        # Hook runtime/code consistency
        if rtype == Resource.Hook:
            cfg = op.data.get("config", {}) or {}
            runtime = cfg.get("runtime", "") or ""
            code = cfg.get("code", "")
            sibling_py = op.path.with_suffix(".py")
            sibling_js = op.path.with_suffix(".js")
            has_py = _file_exists_sync(sibling_py)
            has_js = _file_exists_sync(sibling_js)
            if (code or has_py or has_js) and not runtime:
                plan.errors.append(
                    f"{op.path}: hook has code but no `config.runtime` set."
                )
            if has_py and "python" not in runtime.lower() and runtime:
                plan.errors.append(
                    f"{op.path}: hook has a .py companion file but runtime is '{runtime}'."
                )
            if (
                has_js
                and "node" not in runtime.lower()
                and "js" not in runtime.lower()
                and runtime
            ):
                plan.errors.append(
                    f"{op.path}: hook has a .js companion file but runtime is '{runtime}'."
                )

        # Track for duplicate-name detection
        key = str(op.placeholder_path or op.path)
        creates_by_placeholder[key] = op

    # Duplicate name within the same parent for new objects of the same type
    seen: dict[tuple, list] = {}
    for op in plan.creates:
        rtype = getattr(op, "resolved_type", None)
        if not rtype:
            continue
        parent_key = str(
            op.path.parent.parent
            if rtype in (Resource.Queue, Resource.Schema, Resource.Inbox)
            else op.path.parent
        )
        seen.setdefault((rtype, parent_key, op.data.get("name", "")), []).append(op)
    for (rtype, parent_key, name), ops in seen.items():
        if len(ops) > 1 and name:
            plan.errors.append(
                f"Multiple new {rtype.value} named '{name}' under {parent_key}: "
                + ", ".join(str(o.path) for o in ops)
            )

    # Per-DELETE: warn if a delete is the parent of a create (we'd be deleting
    # under a brand-new sibling, but Rossum cascade-delete may erase it).
    delete_paths = {str(d.path) for d in plan.deletes}
    for c in plan.creates:
        for ancestor in c.path.parents:
            if str(ancestor) in delete_paths:
                plan.errors.append(
                    f"{c.path}: would be created under a folder that is being deleted ({ancestor})."
                )


def _samefile(a: Path, b: Path) -> bool:
    return str(a) == str(b)


def _file_exists_sync(path: Path) -> bool:
    """Sync existence check — anyio.Path.exists is async, but the plan module
    is intentionally synchronous; use the underlying pathlib stat."""
    import pathlib

    return pathlib.Path(str(path)).exists()


def order_creates(plan: PushPlan) -> list:
    """Return `plan.creates` sorted by CREATE_TYPE_ORDER, stable within type."""
    type_index = {t: i for i, t in enumerate(CREATE_TYPE_ORDER)}
    return sorted(
        plan.creates,
        key=lambda o: type_index.get(o.type, len(CREATE_TYPE_ORDER)),
    )


def order_deletes(plan: PushPlan) -> list:
    """Return `plan.deletes` sorted by DELETE_TYPE_ORDER (children-before-parents)."""
    type_index = {t: i for i, t in enumerate(DELETE_TYPE_ORDER)}
    return sorted(
        plan.deletes,
        key=lambda o: type_index.get(o.type, len(DELETE_TYPE_ORDER)),
    )


def render_plan(plan: PushPlan, label: str = "") -> None:
    """Print a human-readable plan via rich. Side-effect only."""
    if plan.is_empty:
        return

    lines: list[str] = []
    if label:
        lines.append(f"[bold]PLAN:[/bold] {label}")

    if plan.creates:
        lines.append("")
        lines.append("[bold green]WILL CREATE[/bold green]")
        for op in order_creates(plan):
            t = _short_type(op.type)
            label_str = _create_label(op)
            lines.append(
                f"  [yellow]{t:<13}[/yellow] [green][+][/green] {label_str:<35} {op.path}"
            )

    if plan.updates:
        lines.append("")
        lines.append("[bold blue]WILL UPDATE[/bold blue]")
        for op in plan.updates:
            t = _short_type(op.type)
            name = op.data.get("name", "")
            id_ = op.data.get("id", "")
            label_str = f"{name}_[{id_}]" if id_ else str(op.path)
            lines.append(f"  [yellow]{t:<13}[/yellow]     {label_str:<35} {op.path}")

    if plan.deletes:
        lines.append("")
        lines.append("[bold red]WILL DELETE[/bold red]")
        for op in order_deletes(plan):
            t = _short_type(op.type)
            name = op.data.get("name", "")
            id_ = op.data.get("id", "")
            label_str = f"{name}_[{id_}]" if id_ else str(op.path)
            lines.append(
                f"  [yellow]{t:<13}[/yellow] [red][-][/red] {label_str:<35} {op.path}"
            )

    pprint(Panel("\n".join(lines), title=f"{settings.UPLOAD_COMMAND_NAME} plan"))


_SHORT_TYPE: dict[Resource, str] = {
    Resource.Workspace: "workspace",
    Resource.Queue: "queue",
    Resource.Schema: "schema",
    Resource.Inbox: "inbox",
    Resource.Engine: "engine",
    Resource.EngineField: "engine_field",
    Resource.Hook: "hook",
    Resource.Rule: "rule",
}


def _short_type(resource: Resource) -> str:
    return _SHORT_TYPE.get(resource, getattr(resource, "value", str(resource)))


def _create_label(op) -> str:
    name = op.data.get("name", "")
    if name:
        return f"{name}_[]"
    return str(op.path)
