import os

from anyio import Path
from rich.prompt import Confirm
from rossum_api import APIClientError, AsyncRossumAPIClient
from rossum_api.domain_logic.resources import Resource

from deployment_manager.common.determine_path import determine_object_type_from_url
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    create_formula_file,
    find_formula_fields_in_schema,
    read_formula_file,
    read_object_from_json,
    write_object_to_json,
    write_str,
)
from deployment_manager.common.schema import find_schema_id
from deployment_manager.utils.consts import GIT_CHARACTERS, display_warning, settings


def is_change_existing(change, changes):
    c_op, c_path = change
    for op, path in changes:
        if c_op == op and str(c_path) == str(path):
            return True
    return False


async def merge_formula_changes(changes: list[tuple[str, Path]]):
    merged_changes = []
    for change in changes:
        op, path = change

        if (
            op
            in [
                GIT_CHARACTERS.UPDATED,
                GIT_CHARACTERS.CREATED,
                GIT_CHARACTERS.CREATED_STAGED,
                GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
            ]
            and settings.FORMULA_DIR_NAME in path.parent.name
            and (path.suffix == ".py")
        ):
            formula_code = await read_formula_file(path)
            formula_name = path.stem

            schema_path = path.parent.parent / "schema.json"
            if not await schema_path.exists():
                continue

            schema = await read_object_from_json(schema_path)
            if "content" not in schema:
                # Malformed/new schema without `content`; let plan.validate
                # surface the missing-required-field error.
                continue
            schema_id = find_schema_id(schema["content"], formula_name)
            schema_id["formula"] = formula_code

            await write_object_to_json(schema_path, schema)
            new_change = (GIT_CHARACTERS.UPDATED, schema_path)
            if not is_change_existing(new_change, merged_changes):
                merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)

    # If code file was not among the changes, the JSON schemas file already has the new code thanks to the for loop above and no change is technically actually made.
    # In case code of a schema was changed directly in the JSON file, update the formula code file as well.
    for change in merged_changes:
        op, path = change
        if (
            op
            in [
                GIT_CHARACTERS.UPDATED,
                GIT_CHARACTERS.CREATED,
                GIT_CHARACTERS.CREATED_STAGED,
                GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
            ]
            and "schema.json" in path.name
        ):
            schema = await read_object_from_json(path)

            if "content" not in schema:
                continue
            formula_fields = find_formula_fields_in_schema(schema["content"])
            if formula_fields:
                formula_directory_path = create_formula_directory_path(path)
                for field_id, code in formula_fields:
                    await create_formula_file(formula_directory_path / f"{field_id}.py", code)

    return merged_changes


async def merge_hook_changes(changes: list[tuple[str, Path]], org_path: Path):
    merged_changes = []
    for change in changes:
        op, path = change
        if (
            op
            in [
                GIT_CHARACTERS.UPDATED,
                GIT_CHARACTERS.CREATED,
                GIT_CHARACTERS.CREATED_STAGED,
                GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
            ]
            and path.parent.name == "hooks"
            and path.suffix in [".py", ".js"]
        ):
            # Overwrite the code property in the JSON hook file with the code from the file.
            # If the JSON hook file also had changed code, it will get overwritten!
            with open(path, "r") as file:
                code_str = file.read()
                object_path = org_path / (Path(str(path).removesuffix(".py").removesuffix(".js") + ".json"))
                if not await object_path.exists():
                    continue
                hook = await read_object_from_json(object_path)
                hook.setdefault("config", {})["code"] = code_str
                await write_object_to_json(object_path, hook)
                new_change = (GIT_CHARACTERS.UPDATED, object_path)
                exists = is_change_existing(new_change, merged_changes)
                if not exists:
                    merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)

    # Dedup by path: a brand-new hook may emit both (CREATE, json) directly
    # and (UPDATE, json) synthesized from its .py companion. Prefer CREATE.
    create_ops = {
        GIT_CHARACTERS.CREATED,
        GIT_CHARACTERS.CREATED_STAGED,
        GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
    }
    deduped: list[tuple[str, Path]] = []
    seen: dict[str, int] = {}
    for op, path in merged_changes:
        key = str(path)
        if key not in seen:
            seen[key] = len(deduped)
            deduped.append((op, path))
        else:
            existing_op = deduped[seen[key]][0]
            if op in create_ops and existing_op not in create_ops:
                deduped[seen[key]] = (op, path)
    merged_changes = deduped

    # If code file was not among the changes, the JSON hook file already has the new code thanks to the for loop above and no change is technically actually made.
    # In case code of a hook was changed directly in the JSON file, update the code file as well.
    for change in merged_changes:
        op, path = change
        if (
            op
            in [
                GIT_CHARACTERS.UPDATED,
                GIT_CHARACTERS.CREATED,
                GIT_CHARACTERS.CREATED_STAGED,
                GIT_CHARACTERS.CREATED_STAGED_MODIFIED,
            ]
            and path.parent.name == "hooks"
        ) and path.suffix == ".json":
            # The change list can contain a CREATE for a file that no longer
            # exists on disk — e.g. a `RD` rename whose new path was deleted
            # by the user. Skip silently; the planner will resolve it via the
            # paired DELETE for the old path.
            if not await path.exists():
                continue
            hook = await read_object_from_json(path)

            code_path = create_custom_hook_code_path(Path(path), hook)
            if not code_path:
                continue

            await write_str(code_path, hook.get("config", {}).get("code", None))

    return merged_changes


async def mark_unstaged_objects_as_updated(changes, org_path, client: AsyncRossumAPIClient):
    """
    Unstaged changes may be truly new objects or existing objects that were
    pulled and not yet committed. Change op-codes based on their existence on
    the remote.

    `_[]` placeholder semantics: if the path has any `_[]` segment, it is an
    explicit CREATE — no remote check needed. The plan module rejects any
    no-`_[]` create that lacks id+url with a clearer error than this stage.
    """
    from deployment_manager.commands.upload.placeholder import path_has_own_placeholder

    changes_updated = []
    for change in changes:
        path: Path
        op, path = change
        if op in (GIT_CHARACTERS.CREATED, GIT_CHARACTERS.CREATED_STAGED, GIT_CHARACTERS.CREATED_STAGED_MODIFIED) and path.suffix == ".json":
            # Explicit `_[]` placeholder => CREATE, do not consult the remote.
            if path_has_own_placeholder(path):
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
                continue

            object_path = org_path / path
            try:
                object = await read_object_from_json(object_path)
            except FileNotFoundError:
                # File deleted between git status and our read — skip.
                continue

            id, url = object.get("id", None), object.get("url", None)
            if not id or not url:
                # No `_[]` and no id/url — let plan.classify surface a clear error.
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
                continue

            obj = None
            is_non_creatable_object = False
            object_type = determine_object_type_from_url(url)
            if object_type in [Resource.Organization]:
                is_non_creatable_object = True

            try:
                obj = await client._http_client.request_json(method="GET", url=url)
            # 404 may happen when looking for the object
            except APIClientError as e:
                if e.status_code != 404:
                    raise e

            # Object exists on remote -> this should really be an update, not create
            if obj:
                op = GIT_CHARACTERS.UPDATED
                changes_updated.append((op, path))
            elif is_non_creatable_object:
                display_warning(f"Creating organization is not supported: ({path})")
                continue
            # Object does not exist on remote -> keep it as create
            elif not is_change_existing(change, changes_updated):
                changes_updated.append(change)
        # Add back anything that does not have created git status op codes
        else:
            changes_updated.append(change)

    return changes_updated


async def cascade_delete_ops(path, change, changes_updated, org_path):
    abs_path = await path.parent.absolute()
    file_set = set()
    for dir_, _, files in os.walk(str(abs_path)):
        for file_name in files:
            rel_dir = os.path.relpath(dir_, str(abs_path))
            rel_file = os.path.join(rel_dir, file_name)
            file_set.add(rel_file)
    for object in file_set:
        new_path = Path("source") / org_path / Path(object)
        if new_path.stem == "inbox":  # ignore deleting inboxes, it will be deleted when queue is deleted
            continue
        op_obj = ("D", new_path)
        if not is_change_existing(op_obj, changes_updated):
            changes_updated.append(op_obj)
    if not is_change_existing(change, changes_updated):
        changes_updated.append(change)
    return changes_updated


async def evaluate_delete_dependencies(changes, org_path):
    changes_updated = []
    for change in changes:
        op, path = change
        if op == GIT_CHARACTERS.DELETED:
            if str(path).endswith("workspace.json"):
                if not Confirm.ask(
                    "You are about to delete a workspace - the tool will cascade delete all associated queues/inboxes with the workspace. Are you sure you want to proceed?",
                ):
                    continue
                changes_updated = await cascade_delete_ops(path, change, changes_updated, org_path)
            elif str(path).endswith("queue.json"):
                changes_updated = await cascade_delete_ops(path, change, changes_updated, org_path)
            else:
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
        else:
            if not is_change_existing(change, changes_updated):
                changes_updated.append(change)

    return changes_updated
