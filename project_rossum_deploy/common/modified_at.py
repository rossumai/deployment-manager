from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


async def check_modified_timestamp(
    client: ElisAPIClient, resource: Resource, id: int, local_object: dict
):
    object = await client._http_client.fetch_one(resource, id)
    return object.get("modified_at", "") == local_object.get("modified_at", "")