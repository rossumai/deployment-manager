import asyncio
from pydantic import BaseModel
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


class Downloader(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    client: ElisAPIClient

    async def download_remote_objects(self, type: Resource):
        paginated_objects = [
            object async for object in self.client._http_client.fetch_all(type)
        ]

        # Refetch in case the paginated fields don't include everything
        # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
        full_objects = await asyncio.gather(
            *[
                self.client._http_client.fetch_one(type, object["id"])
                for object in paginated_objects
            ]
        )

        return full_objects

    # async def save_downloaded_objects(self, objects: list[dict]): ...
