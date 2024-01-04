import asyncio
import logging
import httpx
from rossum_api import ElisAPIClient

from project_rossum_deploy.utils.functions import extract_id_from_url

def is_org_targetting_itself(mapping:dict):
    return mapping["organization"]["target"] == mapping["organization"]["id"]

def replace_dependency_url(object: dict, dependency: str, source_id_target_pairs: dict):
    if isinstance(object[dependency], list):
        new_urls = []
        for old_url in object[dependency]:
            old_id = extract_id_from_url(old_url)
            if new_object := source_id_target_pairs.get(old_id, None):
                new_url = old_url.replace(str(old_id), str(new_object['id']))
                new_urls.append(new_url)
        object[dependency] = new_urls
    else:
        if new_object := source_id_target_pairs.get(
            extract_id_from_url(object[dependency]), None
        ):
            old_url = object[dependency]
            old_id = extract_id_from_url(old_url)
            new_url = old_url.replace(str(old_id), str(new_object['id']))
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


async def _delete_migrated_object(client: httpx.AsyncClient, object_url: str):
    try:
        res = await client.delete(object_url)
        res.raise_for_status()
    except Exception as e:
        logging.exception(e)


# Debug function to clean up
async def _delete_migrated_objects(object_urls: list[str]):
    token = "0bc0524610e5c84253603811bd94d02c5296334d"

    async with httpx.AsyncClient(headers={"Authorization": f"Token {token}"}) as client:
        await asyncio.gather(
            *[_delete_migrated_object(client, url) for url in object_urls]
        )
