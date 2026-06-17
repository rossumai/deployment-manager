from rossum_api import AsyncRossumAPIClient
from rossum_api.domain_logic.resources import Resource


async def check_modified_timestamp(client: AsyncRossumAPIClient, resource: Resource, id: int, local_object: dict):
    object = await client._http_client.fetch_one(resource, id)
    return object.get("modified_at", "") == local_object.get("modified_at", "")
