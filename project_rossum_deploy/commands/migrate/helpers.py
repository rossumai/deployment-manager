import asyncio
import copy
from typing import Callable
from rossum_api import ElisAPIClient
from rich import print

from project_rossum_deploy.common.determine_path import determine_object_type_from_url
from project_rossum_deploy.utils.consts import (
    MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER,
    display_warning,
    settings,
    MAPPING_SELECTED_ATTRIBUTE,
)
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
)
from project_rossum_deploy.utils.functions import find_object_by_id


def is_first_time_migration(submapping: dict):
    return not submapping.get("target_object", None)


def check_if_selected(submapping: dict):
    return bool(submapping.get(MAPPING_SELECTED_ATTRIBUTE, None))


# TODO: not used for release
async def should_upload_object(
    client: ElisAPIClient, target_id: int, target_objects: list[dict]
):
    if target_id:
        target_object = find_object_by_id(target_id, target_objects)
        if not target_object:
            return True

        remote_object = await client._http_client.request_json(
            method="get", url=target_object.get("url", "")
        )

        return remote_object.get("modified_at", "") == target_object.get(
            "modified_at", ""
        )
    else:
        return True


def replace_dependency_url(
    object: dict,
    target_index: int,
    target_objects_count: int,
    dependency: str,
    source_id_target_pairs: dict[int, list],
    target_object: dict = None,
):
    if isinstance(object[dependency], list):
        replace_list_of_dependency_urls(
            object=object,
            target_index=target_index,
            target_objects_count=target_objects_count,
            dependency=dependency,
            source_id_target_pairs=source_id_target_pairs,
            target_object=target_object,
        )
    else:
        source_dependency_url = object[dependency]
        source_id = extract_id_from_url(source_dependency_url)
        target_dependency_objects = source_id_target_pairs.get(source_id, [])

        # Dependency object has no target equivalents (e.g., when ignored)
        if not len(target_dependency_objects):
            return
        # There are multiple objects released (e.g., queues) and their number is the same as the number of their dependencies (e.g., hooks) -> assume that each object should have its own dependency
        if len(target_dependency_objects) == target_objects_count:
            target_id_str = str(target_dependency_objects[target_index]["id"])
        # All objects will have the same dependency
        else:
            target_id_str = str(target_dependency_objects[0]["id"])

        source_id_str = str(source_id)
        new_url = source_dependency_url.replace(
            source_id_str,
            target_id_str,
        )
        object[dependency] = new_url

        if source_id_str == target_id_str:
            if settings.IS_PROJECT_IN_SAME_ORG and dependency == "organization":
                return

            display_warning(
                f'Dependency "{dependency}" for object "{object.get('id', 'no-ID')}" was not modified. Source and target objects share the dependency. This can happen if you did not {settings.MIGRATE_COMMAND_NAME} the dependency and no target equivalent exists.'
            )


# TODO: refactor to use the same replace URL function
def replace_list_of_dependency_urls(
    object: dict,
    target_index: int,
    target_objects_count: int,
    dependency: str,
    source_id_target_pairs: dict[int, list],
    target_object: dict = None,
):
    new_urls = []
    for source_index, source_dependency_url in enumerate(object[dependency]):
        source_id = extract_id_from_url(source_dependency_url)
        target_dependency_objects = source_id_target_pairs.get(source_id, [])

        # Dependency object has no target equivalents (e.g., when ignored)
        if not len(target_dependency_objects):
            continue
        # There are multiple objects released (e.g., queues) and their number is the same as the number of their dependencies (e.g., hooks) -> assume that each object should have its own dependency
        if len(target_dependency_objects) == target_objects_count:
            target_id_str = str(target_dependency_objects[target_index]["id"])
        # All objects will have the same dependency
        else:
            target_id_str = str(target_dependency_objects[0]["id"])

        source_id_str = str(source_id)
        new_url = source_dependency_url.replace(source_id_str, target_id_str)

        if source_id_str == target_id_str:
            display_warning(
                f'Dependency "{dependency}"[{source_index}] for object "{object.get('id', 'no-ID')}" was not changed to a target counterpart because none was found.'
            )
        else:
            new_urls.append(new_url)

    # Target queues can have 'dangling' hooks that exist only on target, these should not be overwritten.
    if target_object:
        for target_dependency_url in target_object[dependency]:
            # Target ID was found in the new list as well
            if target_dependency_url in new_urls:
                continue

            target_has_source = False
            # Check if this target has a source. If not, it is a dangling target and we need to add it back.
            target_id = extract_id_from_url(target_dependency_url)
            for _, targets in source_id_target_pairs.items():
                for target in targets:
                    if target.get("id", "") == target_id:
                        target_has_source = True
                        break

            if not target_has_source:
                new_urls.append(target_dependency_url)

    object[dependency] = new_urls


async def get_token_owner(client: ElisAPIClient):
    async for user in client.list_all_users(username=client._http_client.username):
        if user.username == settings.TARGET_USERNAME:
            return user

    return None


def traverse_mapping(submapping: dict):
    if isinstance(submapping, list):
        for el in submapping:
            yield from traverse_mapping(el)
    elif isinstance(submapping, dict):
        yield submapping
        for k, v in submapping.items():
            if k not in settings.MAPPING_TRAVERSE_IGNORE_FIELDS:
                yield from traverse_mapping(v)


async def migrate_object_to_default_target(
    submapping: dict, upload_function: Callable, pass_index_args: bool = False
):
    extra_args = {}
    if pass_index_args:
        extra_args["target_index"] = 0
        # extra_args["target_objects_count"] = len(targets)
    result = await upload_function(target_id=submapping["target_object"], **extra_args)
    submapping["target_object"] = result["id"]
    return result


async def migrate_object_to_multiple_targets(
    submapping: dict,
    upload_function: Callable,
    pass_index_args: bool = False,
    plan_only: bool = False,
):
    requests = []
    targets = submapping.get("targets", [])
    for target_index, target in enumerate(targets):
        target_id = target.get("target_id", None)
        extra_args = {}
        if pass_index_args or plan_only:
            extra_args["target_index"] = target_index
            extra_args["target_objects_count"] = len(targets)

        requests.append(upload_function(target_id=target_id, **extra_args))

    results = await asyncio.gather(*requests)
    # asyncio.gather returns results in the same order as they were put in
    for index, result in enumerate(results):
        # In case of planning and selected_only mode, the same objects are returned
        # They should target themselves
        if result and (target_id := result.get("id", None)) != submapping.get("id", ""):
            submapping.get("targets", [])[index]["target_id"] = result.get("id", None)

    return list(filter(lambda x: x, results))


# Extra args are there to accomodate all upload function signatures
async def simulate_migrate_object(
    client: ElisAPIClient,
    source_object: dict,
    target_id: int,
    target_index: int = 0,
    target_objects_count: int = None,
):
    object_counter = f"({target_index +1}/{target_objects_count if target_objects_count is not None else 1})"
    object_type = determine_object_type_from_url(source_object["url"])
    if target_id:
        target_object = await client.request_json(
            method="GET",
            url=source_object["url"].replace(str(source_object["id"]), str(target_id)),
        )
        print(
            f'[blue]UPDATE[/blue] [yellow]{object_type.value}[/yellow]: source "{source_object.get('id', None)} {source_object.get('name', '')}" -> target "{target_id} {target_object.get('name', 'no-name')}" {object_counter}.'
        )
        return target_object
    else:
        print(
            f'[red]CREATE[/red] [yellow]{object_type.value}[/yellow]: source "{source_object.get('id', None)} {source_object.get('name', '')}" -> target "{MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER}" {object_counter}.'
        )
        return copy.deepcopy(source_object)


# TODO: use typing.protocol?
# Extra args are there to accomodate all upload function signatures
async def skip_migrate_object(
    source_object,
    target_id: int,
    target_index: int = 0,
    target_objects_count: int = None,
):
    object_type = determine_object_type_from_url(source_object["url"])
    print(
        f'Skipping {settings.MIGRATE_COMMAND_NAME} of {object_type} "{source_object['id']} {source_object['name']}".'
    )
    return None
