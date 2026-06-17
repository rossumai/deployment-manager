"""Helpers for the `_[]` placeholder convention used by `prd2 push` to mark
a brand-new local object that does not yet exist on the remote.

A path "contains a placeholder" if any of its segments ends with `_[]`. A
placeholder segment looks like `MyHook_[]` (file stem) or `MyWS_[]` (folder).
A child of a placeholder parent inherits its newness; the file's own name
need not have `_[]` (e.g. `schema.json` under `MyQueue_[]/`).
"""

from anyio import Path

PLACEHOLDER = "_[]"


def segment_has_placeholder(segment: str) -> bool:
    return segment.endswith("_[]") or segment.endswith("_[].json") or segment.endswith("_[].py") or segment.endswith("_[].js")


def path_has_own_placeholder(path: Path) -> bool:
    """True iff this exact path has a `_[]` segment (own filename or own folder)."""
    return any(segment_has_placeholder(part) for part in path.parts)


def replace_first_placeholder(path: Path, real_id: int | str) -> Path:
    """Return a copy of `path` with the first `_[]` segment replaced by `_[<id>]`.

    Used to compute the post-create rename target for a created object.
    """
    new_parts = []
    replaced = False
    for part in path.parts:
        if not replaced and "_[]" in part:
            new_parts.append(part.replace("_[]", f"_[{real_id}]", 1))
            replaced = True
        else:
            new_parts.append(part)
    return Path(*new_parts)


def replace_all_placeholders_with_lookup(path: Path, lookup: dict[str, int | str]) -> Path:
    """Return a copy of `path` with every `_[]` segment replaced according to
    `lookup`, where `lookup` maps the placeholder folder name (e.g. `"MyWS_[]"`)
    to the real id created for it.

    Segments not present in the lookup are left untouched.
    """
    new_parts = []
    for part in path.parts:
        if part in lookup:
            new_parts.append(part.replace("_[]", f"_[{lookup[part]}]", 1))
        elif part.endswith("_[].json") or part.endswith("_[].py") or part.endswith("_[].js"):
            stem = part.rsplit(".", 1)[0]
            if stem in lookup:
                ext = part[len(stem):]
                new_parts.append(stem.replace("_[]", f"_[{lookup[stem]}]", 1) + ext)
            else:
                new_parts.append(part)
        else:
            new_parts.append(part)
    return Path(*new_parts)
