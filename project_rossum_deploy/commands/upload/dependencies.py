import os
from rich.prompt import Confirm
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.migrate.schemas import find_schema_id
from project_rossum_deploy.common.read_write import (
    read_formula_file,
    read_json,
    write_json,
)
from project_rossum_deploy.utils.consts import GIT_CHARACTERS, display_error, settings


from anyio import Path


def is_change_existing(change, changes):
    c_op, c_path = change
    for op, path in changes:
        if c_op == op and str(c_path) == str(path):
            return True
    return False


async def merge_formula_changes(changes):
    merged_changes = []
    for change in changes:
        op: str
        path: Path
        op, path = change
        str_path = str(path)

        if (
            (
                op == GIT_CHARACTERS.UPDATED
                or op == GIT_CHARACTERS.CREATED
                or op == GIT_CHARACTERS.CREATED_STAGED
            )
            and (path.suffix == ".py")
            and "schemas" in str_path
        ):
            formula_code = await read_formula_file(path)
            formula_name = path.stem

            schema_file_name = str(path.parent.stem).removeprefix(
                settings.FORMULA_DIR_PREFIX
            )
            schema_path = path.parent.parent / f"{schema_file_name}.json"
            schema = await read_json(schema_path)

            schema_id = find_schema_id(schema["content"], formula_name)
            schema_id["formula"] = formula_code

            await write_json(schema_path, schema)
            new_change = ("M", schema_path)
            if not is_change_existing(new_change, merged_changes):
                merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)
    return merged_changes


async def merge_hook_changes(changes, org_path):
    merged_changes = []
    for change in changes:
        op, path = change
        path = str(path)
        if (
            op == GIT_CHARACTERS.UPDATED
            or op == GIT_CHARACTERS.CREATED
            or op == GIT_CHARACTERS.CREATED_STAGED
        ) and (path.endswith("py") and "hooks" in path):
            with open(path, "r") as file:
                code_str = file.read()
                object_path = org_path / (
                    Path(str(path).removesuffix(".py").removesuffix(".js") + ".json")
                )
                hook_object = await read_json(object_path)
                hook_object["config"]["code"] = code_str
                await write_json(object_path, hook_object)
                new_change = ("M", object_path)
                exists = is_change_existing(new_change, merged_changes)
                if not exists:
                    merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)
    return merged_changes


async def evaluate_create_dependencies(changes, org_path, client: ElisAPIClient):
    changes_updated = []
    for change in changes:
        path: Path
        op, path = change
        if (
            op == GIT_CHARACTERS.CREATED or op == GIT_CHARACTERS.CREATED_STAGED
        ) and path.suffix == ".json":
            object_path = org_path / path
            object = await read_json(object_path)
            id = object.get("id", None)
            obj = None
            if str(path).endswith("workspace.json"):
                if id:
                    obj = await client.retrieve_workspace(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path).endswith("queue.json"):
                if id:
                    obj = await client.retrieve_queue(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("hooks"):
                if id:
                    obj = await client.retrieve_hook(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("schemas"):
                if id:
                    obj = await client.retrieve_schema(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path).endswith("inbox.json") or str(path).endswith(
                "organization.json"
            ):
                display_error(
                    f"Creating organization or inbox is not supported. ({path})"
                )
            else:
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
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
