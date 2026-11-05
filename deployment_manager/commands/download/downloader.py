import asyncio

from pydantic import BaseModel, ConfigDict, PrivateAttr
from rossum_api import APIClientError, AsyncRossumAPIClient
from rossum_api.domain_logic.resources import Resource

from deployment_manager.utils.consts import CustomResource, settings

# List payload verified identical to the detail GET, so the per-object refetch is skipped for these types.
TYPES_WITH_COMPLETE_LIST_PAYLOAD = {
    Resource.Workspace,
    Resource.EmailTemplate,
    Resource.Inbox,
    Resource.Engine,
    Resource.EngineField,
    Resource.Rule,
    Resource.Hook,
}


class Downloader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: AsyncRossumAPIClient

    # One limit shared by all per-object fetches across all types (--concurrency / PRD2_CONCURRENCY)
    _fetch_semaphore: asyncio.Semaphore = PrivateAttr(
        default_factory=lambda: asyncio.Semaphore(settings.CONCURRENCY if settings else 5)
    )

    async def download_remote_objects(self, type: Resource | CustomResource, check_access: bool = False):
        # Some API objects (e.g., rules) might not be allowed and Elis API would return 403...
        paginated_objects = []
        try:
            async for object in self.client._http_client.fetch_all(type):
                paginated_objects.append(object)
        except APIClientError:
            # Only an error before the first item means no access; a later error must not look like "all deleted"
            if check_access and not paginated_objects:
                # display_warning(f"Could not download {type.value}, skipping: {e}")
                return []
            raise

        if type in TYPES_WITH_COMPLETE_LIST_PAYLOAD:
            return paginated_objects

        # Refetch in case the paginated fields don't include everything
        # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
        return await asyncio.gather(*[self._fetch_one(type, object["id"]) for object in paginated_objects])

    async def _fetch_one(self, type: Resource | CustomResource, object_id: int):
        async with self._fetch_semaphore:
            return await self.client._http_client.fetch_one(type, object_id)
