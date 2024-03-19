import asyncio
from typing import Callable
from rossum_api import ElisAPIClient
from project_rossum_deploy.utils.consts import settings

from project_rossum_deploy.utils.functions import extract_id_from_url


def is_first_time_migration(submapping: dict):
    return not submapping.get("target_object", None)


def replace_dependency_url(
    object: dict,
    object_index: int,
    target_objects_count: int,
    dependency: str,
    source_id_target_pairs: dict[int, list],
):
    if isinstance(object[dependency], list):
        new_urls = []
        for source_dependency_url in object[dependency]:
            source_id = extract_id_from_url(source_dependency_url)
            target_dependency_objects = source_id_target_pairs.get(source_id, None)
            # The object was ignored during release, no target equivalents exist
            if not len(target_dependency_objects):
                continue
            # Assume each object should have its own dependency
            elif len(target_dependency_objects) == target_objects_count:
                new_url = source_dependency_url.replace(
                    str(source_id),
                    str(target_dependency_objects[object_index]["id"]),
                )
                new_urls.append(new_url)
            # All objects will have the same dependency
            else:
                new_url = source_dependency_url.replace(
                    str(source_id), str(target_dependency_objects[0]["id"])
                )
                new_urls.append(new_url)
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
                str(target_dependency_objects[object_index]["id"]),
            )
        # All objects will have the same dependency
        else:
            new_url = source_dependency_url.replace(
                str(source_id), str(target_dependency_objects[0]["id"])
            )

        object[dependency] = new_url


def find_mapping_of_object(sub_mapping: list[dict], id: int):
    for object in sub_mapping:
        if object["id"] == id:
            return object
    return None


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
    submapping: dict, upload_function: Callable, pass_index_args: bool = False
):
    requests = []
    targets = submapping.get("targets", [])
    for target_index, target in enumerate(targets):
        target_id = target.get("target_id", None)
        extra_args = {}
        if pass_index_args:
            extra_args["target_index"] = target_index
            extra_args["target_objects_count"] = len(targets)
        requests.append(upload_function(target_id=target_id, **extra_args))

    results = await asyncio.gather(*requests)
    # asyncio.gather returns results in the same order as they were put in
    for index, result in enumerate(results):
        if result and result.get("id", None):
            submapping.get("targets", [])[index]["target_id"] = result.get("id", None)

    return list(filter(lambda x: x, results))
