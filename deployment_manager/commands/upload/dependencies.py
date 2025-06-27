import os
from rich.prompt import Confirm
from rossum_api import ElisAPIClient
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
from deployment_manager.utils.consts import (
    GIT_CHARACTERS,
    display_error,
    display_warning,
    settings,
)


from anyio import Path

from rossum_api.api_client import APIClientError


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
            ]
            and "schema.json" in path.name
        ):
            schema = await read_object_from_json(path)

            formula_fields = find_formula_fields_in_schema(schema["content"])
            if formula_fields:
                formula_directory_path = create_formula_directory_path(path)
                for field_id, code in formula_fields:
                    await create_formula_file(
                        formula_directory_path / f"{field_id}.py", code
                    )

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
            ]
            and path.parent.name == "hooks"
            and path.suffix in [".py", ".js"]
        ):
            # Overwrite the code property in the JSON hook file with the code from the file.
            # If the JSON hook file also had changed code, it will get overwritten!
            with open(path, "r") as file:
                code_str = file.read()
                object_path = org_path / (
                    Path(str(path).removesuffix(".py").removesuffix(".js") + ".json")
                )
                hook = await read_object_from_json(object_path)
                hook["config"]["code"] = code_str
                await write_object_to_json(object_path, hook)
                new_change = (GIT_CHARACTERS.UPDATED, object_path)
                exists = is_change_existing(new_change, merged_changes)
                if not exists:
                    merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)

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
            ]
            and path.parent.name == "hooks"
        ) and path.suffix == ".json":
            hook = await read_object_from_json(path)

            code_path = create_custom_hook_code_path(Path(path), hook)
            if not code_path:
                continue

            await write_str(code_path, hook.get("config", {}).get("code", None))

    return merged_changes


async def mark_unstaged_objects_as_updated(changes, org_path, client: ElisAPIClient):
    """
    Unstaged changes may be truly new objects or existing objects that were pulled and not yet committed. Change op-codes based on their existence on the remote.
    """
    changes_updated = []
    for change in changes:
        path: Path
        op, path = change
        if (
            op == GIT_CHARACTERS.CREATED or op == GIT_CHARACTERS.CREATED_STAGED
        ) and path.suffix == ".json":
            object_path = org_path / path
            object = await read_object_from_json(object_path)

            id = object.get("id", None)
            if not id:
                display_warning(
                    f"Skipping uncommitted object without ID: ({object_path})"
                )
                continue

            obj = None
            is_non_creatable_object = False
            object_type = ""

            if str(path).endswith("workspace.json"):
                object_type = "workspaces"
            elif str(path).endswith("queue.json"):
                object_type = "queues"
            elif str(path.parent).endswith("hooks"):
                object_type = "hooks"
            elif str(path).endswith("schema.json"):
                object_type = "schemas"
            elif str(path).endswith("inbox.json"):
                object_type = "inboxes"
                is_non_creatable_object = True
            elif str(path).endswith("organization.json"):
                object_type = "organizations"
                is_non_creatable_object = True

            try:
                obj = await client.request_json(method="GET", url=f"{object_type}/{id}")
            # 404 may happen when looking for the object
            except APIClientError as e:
                if e.status_code != 404:
                    raise e

            # Object exists on remote -> this should really be an update, not create
            if obj:
                op = GIT_CHARACTERS.UPDATED
                changes_updated.append((op, path))
            elif is_non_creatable_object:
                display_warning(
                    f"Creating organization or inbox is not supported: ({path})"
                )
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
        if (
            new_path.stem == "inbox"
        ):  # ignore deleting inboxes, it will be deleted when queue is deleted
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
                changes_updated = await cascade_delete_ops(
                    path, change, changes_updated, org_path
                )
            elif str(path).endswith("queue.json"):
                changes_updated = await cascade_delete_ops(
                    path, change, changes_updated, org_path
                )
            else:
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
        else:
            if not is_change_existing(change, changes_updated):
                changes_updated.append(change)

    return changes_updated
