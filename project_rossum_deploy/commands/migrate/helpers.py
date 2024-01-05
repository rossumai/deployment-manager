from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.helpers import extract_sources_targets

from project_rossum_deploy.utils.functions import extract_id_from_url


def is_org_targetting_itself(mapping: dict):
    return mapping["organization"]["target"] == mapping["organization"]["id"]


def replace_dependency_url(object: dict, dependency: str, source_id_target_pairs: dict):
    if isinstance(object[dependency], list):
        new_urls = []
        for old_url in object[dependency]:
            old_id = extract_id_from_url(old_url)
            if new_object := source_id_target_pairs.get(old_id, None):
                new_url = old_url.replace(str(old_id), str(new_object["id"]))
                new_urls.append(new_url)
        object[dependency] = new_urls
    else:
        if new_object := source_id_target_pairs.get(
            extract_id_from_url(object[dependency]), None
        ):
            old_url = object[dependency]
            old_id = extract_id_from_url(old_url)
            new_url = old_url.replace(str(old_id), str(new_object["id"]))
            object[dependency] = new_url


def find_mapping_of_object(sub_mapping: list[dict], id: int):
    for object in sub_mapping:
        if object["id"] == id:
            return object
    return None


async def get_token_owner(client: ElisAPIClient):
    users = [
        user
        async for user in client.list_all_users(username=client._http_client.username)
    ]
    return users[0]


def traverse_mapping(mapping: dict):
    if isinstance(mapping, list):
        for el in mapping:
            yield from traverse_mapping(el)
    elif isinstance(mapping, dict):
        yield mapping
        for v in mapping.values():
            yield from traverse_mapping(v)


def find_created_target_ids(previous_mapping: dict, source_id_target_pairs: dict):
    _, previous_targets = extract_sources_targets(previous_mapping)
    previous_target_ids = []
    for objects in previous_targets.values():
        if isinstance(objects, list):
            previous_target_ids.extend(objects)
    previous_target_ids = set(previous_target_ids)

    all_target_ids = set()
    for object in source_id_target_pairs.values():
        all_target_ids.add(object["id"])

    return all_target_ids.difference(previous_target_ids)
