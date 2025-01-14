import asyncio
from pydantic import BaseModel
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.utils.consts import CustomResource


class Downloader(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    client: ElisAPIClient

    async def download_remote_objects(self, type: Resource | CustomResource):
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
