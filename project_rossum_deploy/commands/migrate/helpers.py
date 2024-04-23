from rossum_api import ElisAPIClient
from project_rossum_deploy.utils.consts import settings

from project_rossum_deploy.utils.functions import extract_id_from_url


def is_first_time_migration(submapping: dict):
    return not submapping.get("target_object", None)


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
    async for user in client.list_all_users(username=client._http_client.username):
        if user.username == settings.TARGET_USERNAME:
            return user

    return None


def traverse_mapping(mapping: dict):
    if isinstance(mapping, list):
        for el in mapping:
            yield from traverse_mapping(el)
    elif isinstance(mapping, dict):
        yield mapping
        for v in mapping.values():
            yield from traverse_mapping(v)
