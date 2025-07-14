import difflib
import json
import re
import subprocess
import tempfile

import questionary
from rich.panel import Panel


def deep_three_way_merge(
    last_applied: dict,
    source: dict,
    target: dict,
    prefer: str = "neither",
    ignored_fields: list[str] = None,
    override_fields: list[str] = None,
    derived_fields: list[str] = None,
    path: str = "",
) -> tuple[dict, dict, dict]:
    """
    Returns:
        merged: dict with resolved values
        conflicts: dict[path -> (source_val, target_val)]
        rebase_candidates: dict[path -> target_val]
    """
    if ignored_fields is None:
        ignored_fields = []
    if override_fields is None:
        override_fields = []
    if derived_fields is None:
        derived_fields = []

    merged = {}
    conflicts = {}
    rebase_candidates = {}

    all_keys = set(last_applied) | set(source) | set(target)

    for key in all_keys:
        k_path = f"{path}.{key}" if path else key

        if k_path in ignored_fields:
            # Just take source, or fallback to target, or last_applied
            merged[key] = source.get(key, target.get(key, last_applied.get(key)))
            continue

        s_val = source.get(key)
        t_val = target.get(key)
        l_val = last_applied.get(key)

        # Skip derived fields not in source
        if k_path in derived_fields and key not in source:
            merged[key] = t_val
            continue

        # If all values are dicts → recurse
        if (
            isinstance(s_val, dict)
            and isinstance(t_val, dict)
            and isinstance(l_val, dict)
        ):
            sub_merged, sub_conflicts, sub_rebases = deep_three_way_merge(
                last_applied=l_val,
                source=s_val,
                target=t_val,
                prefer=prefer,
                ignored_fields=ignored_fields,
                override_fields=override_fields,
                derived_fields=derived_fields,
                path=k_path,
            )
            merged[key] = sub_merged
            conflicts.update(sub_conflicts)
            rebase_candidates.update(sub_rebases)
            continue

        # Direct match
        if s_val == t_val:
            merged[key] = s_val
            continue

        # Source-only change
        if s_val != l_val and t_val == l_val:
            merged[key] = s_val
            continue

        # Target-only change → rebase candidate
        if s_val == l_val and t_val != l_val:
            merged[key] = s_val
            rebase_candidates[k_path] = t_val
            continue

        # Explicit override
        if k_path in override_fields:
            merged[key] = s_val
            continue

        # Prefer one side
        if prefer == "source":
            merged[key] = s_val
            continue
        elif prefer == "target":
            merged[key] = t_val
            continue

        # Real conflict
        conflicts[k_path] = (s_val, t_val)
        merged[key] = s_val  # could defer resolution here

    return merged, conflicts, rebase_candidates

# TODO: do a colorized diff with substring changes detection
def create_rebase_diff(source_val, target_val) -> str:
    return Panel(f"SOURCE: {source_val}\n\nTARGET: {target_val}")


def get_nested_value(obj: dict, dotted_path: str, default=None):
    """
    Safely retrieve a nested value from a dictionary using a dotted path like "config.code"
    """
    keys = dotted_path.split(".")
    for key in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key, default)
    return obj


def set_nested_value(obj: dict, dotted_path: str, value):
    """
    Set a nested value in a dictionary using a dotted path.
    Creates nested dictionaries as needed.
    """
    keys = dotted_path.split(".")
    for key in keys[:-1]:
        obj = obj.setdefault(key, {})
    obj[keys[-1]] = value


async def prompt_rebase_field(label, path):
    return await questionary.confirm(
        "Rebase it into source?",
        default=False,
    ).ask_async()


# TODO: --ours and --theirs params to resolve conflicts automatically
async def prompt_conflict_resolution(target_val, last_applied_val, object_path):

    # ! This assumes that these two objects were created from the same JSON as source
    # Thanks to that, sorting of keys is preserved (Python dict implementation guarantee) without the need to resort
    last_applied_str = json.dumps(last_applied_val, indent=2)
    target_str = json.dumps(target_val, indent=2)

    with tempfile.NamedTemporaryFile() as f1, tempfile.NamedTemporaryFile() as f2:
        f1.write(last_applied_str.encode("utf-8"))
        f2.write(target_str.encode("utf-8"))
        f1.flush()
        f2.flush()

        subprocess.run(
            [
                "git",
                "merge-file",
                "-L",
                "SOURCE",
                "-L",
                "LAST_APPLIED",
                "-L",
                "REMOTE TARGET",
                str(object_path),
                f1.name,
                f2.name,
            ]
        )


def mark_derived_fields(deploy_state, resource_type, source_id, target_objs, fields):
    state_map = getattr(deploy_state, resource_type)
    source_id_str = str(source_id)

    for target in target_objs:
        target_id = str(target.data.get("id"))
        try:
            entry = state_map[source_id_str].deployments[target_id].last_applied
            for f in fields:
                if f not in entry.derived_fields:
                    entry.derived_fields.append(f)
        except KeyError:
            continue
