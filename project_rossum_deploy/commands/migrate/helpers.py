import asyncio
import copy
from typing import Callable
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
)


def is_first_time_migration(submapping: dict):
    return not submapping.get("target_object", None)


def find_object_by_id(id: int, objects: list):
    object = None
    for candidate in objects:
        if candidate["id"] == id:
            object = candidate
            break
    return object


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
        new_urls = []
        for source_dependency_url in object[dependency]:
            source_id = extract_id_from_url(source_dependency_url)
            target_dependency_objects = source_id_target_pairs.get(source_id, [])
            # The object was ignored during release, no target equivalents exist
            if not len(target_dependency_objects):
                continue
            # Assume each object should have its own dependency
            elif len(target_dependency_objects) == target_objects_count:
                new_url = source_dependency_url.replace(
                    str(source_id),
                    str(target_dependency_objects[target_index]["id"]),
                )
                new_urls.append(new_url)
            # All objects will have the same dependency
            else:
                new_url = source_dependency_url.replace(
                    str(source_id), str(target_dependency_objects[0]["id"])
                )
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
    else:
        source_dependency_url = object[dependency]
        source_id = extract_id_from_url(source_dependency_url)
        target_dependency_objects = source_id_target_pairs.get(source_id)

        # The object was ignored during release, no target equivalents exist
        if not len(target_dependency_objects):
            return

        # Assume each object should have its own dependency
        if len(target_dependency_objects) == target_objects_count:
            new_url = source_dependency_url.replace(
                str(source_id),
                str(target_dependency_objects[target_index]["id"]),
            )
        # All objects will have the same dependency
        else:
            new_url = source_dependency_url.replace(
                str(source_id), str(target_dependency_objects[0]["id"])
            )

        object[dependency] = new_url


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
        if result and result.get("id", None):
            submapping.get("targets", [])[index]["target_id"] = result.get("id", None)

    return list(filter(lambda x: x, results))


# Extra args are there to accomodate all upload function signatures
async def simulate_migrate_object(
    client: ElisAPIClient,
    source_object: dict,
    target_object_type: Resource,
    target_id: int,
    target_index: int = 0,
    target_objects_count: int = None,
    source_id_target_pairs: dict[int, list] = None,
):
    object_counter = f"({target_index +1}/{target_objects_count if target_objects_count is not None else 1})"
    if target_id:
        print(
            f'UPDATE source {target_object_type} "{source_object.get('id', None)} {source_object.get('name', '')}" -> target "{target_id}" {object_counter}.'
        )
        return await client._http_client.fetch_one(target_object_type, target_id)
    else:
        print(
            f'CREATE source {target_object_type} "{source_object.get('id', None)} {source_object.get('name', '')}" -> target {object_counter}.'
        )
        return copy.deepcopy(source_object)
