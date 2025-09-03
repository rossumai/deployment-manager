import asyncio
from pydantic import BaseModel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.utils.consts import CustomResource, display_warning


class Downloader(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    client: ElisAPIClient

    async def download_remote_objects(
        self, type: Resource | CustomResource, check_access: bool = False
    ):
        # Some API objects (e.g., rules) might not be allowed and Elis API would return 403...
        if check_access:
            try:
                async for item in  self.client._http_client.fetch_all(type):
                    # First item is enough to check
                    break
            except APIClientError as e:
                # display_warning(f"Could not download {type.value}, skipping: {e}")
                return []

        paginated_object_ids = await self.download_remote_object_ids(type=type)

        # Refetch in case the paginated fields don't include everything
        # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
        full_objects = await asyncio.gather(
            *[
                self.client._http_client.fetch_one(type, object_id)
                for object_id in paginated_object_ids
            ]
        )

        return full_objects

    async def download_remote_object_ids(self, type: Resource):
        return [
            object["id"] async for object in self.client._http_client.fetch_all(type)
        ]
