from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich.progress import Progress
from rich.prompt import Prompt

from project_rossum_deploy.commands.migrate.helpers import (
    find_object_by_id,
)
from project_rossum_deploy.common.modified_at import check_modified_timestamp
from project_rossum_deploy.utils.consts import (
    settings,
)
from project_rossum_deploy.utils.functions import (
    PauseProgress,
    extract_id_from_url,
)


async def upload_organization(
    client: ElisAPIClient,
    organization: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if not target_id:
        return

    local_object = find_object_by_id(target_id, target_objects)
    local_remote_timestamp_synced = await check_modified_timestamp(
        client, Resource.Organization, target_id, local_object
    )
    if not force and not local_remote_timestamp_synced:
        errors[target_id] = (Resource.Organization, local_object.get("name", ""))
        return local_object

    return await client._http_client.update(
        Resource.Organization, id_=target_id, data=organization
    )


async def upload_workspace(
    client: ElisAPIClient,
    workspace: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Workspace, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Workspace, local_object.get("name", ""))
            return local_object

        return await client._http_client.update(
            Resource.Workspace, id_=target_id, data=workspace
        )
    else:
        return await client._http_client.create(Resource.Workspace, workspace)


async def upload_queue(
    client: ElisAPIClient,
    queue: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Queue, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Queue, local_object.get("name", ""))
            return local_object

        return await client._http_client.update(
            Resource.Queue, id_=target_id, data=queue
        )
    else:
        return await client._http_client.create(Resource.Queue, queue)


async def upload_inbox(
    client: ElisAPIClient,
    inbox: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Inbox, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Inbox, local_object.get("name", ""))
            return local_object

        return await client._http_client.update(
            Resource.Inbox, id_=target_id, data=inbox
        )
    else:
        return await client._http_client.create(Resource.Inbox, inbox)


async def upload_schema(
    client: ElisAPIClient,
    schema: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Schema, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Schema, local_object.get("name", ""))
            return local_object

        return await client._http_client.update(
            Resource.Schema, id_=target_id, data=schema
        )
    else:
        return await client._http_client.create(Resource.Schema, schema)


async def upload_hook(
    client: ElisAPIClient,
    hook: dict,
    hook_mapping: dict,
    target_id: int,
    progress: Progress,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Hook, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Hook, local_object.get("name", ""))
            return local_object

        return await client._http_client.update(Resource.Hook, id_=target_id, data=hook)
    else:
        created_hook = await create_hook_based_on_template(hook=hook, client=client)
        if not created_hook:
            created_hook = await create_hook_without_template(
                hook=hook, client=client, hook_mapping=hook_mapping, progress=progress
            )
        return created_hook


async def create_hook_based_on_template(hook: dict, client: ElisAPIClient):
    if not hook.get("hook_template", None):
        return None

    if settings.IS_PROJECT_IN_SAME_ORG:
        # Some of the properties (e.g., url) are not in the json, but are required by the API
        hook.pop("config", None)
        return await client._http_client.request_json(
            "POST", url="hooks/create", json=hook
        )
    else:
        # Client is different in case of cross-org migrations
        source_client = ElisAPIClient(
            base_url=settings.SOURCE_API_URL,
            token=settings.SOURCE_TOKEN,
            username=settings.SOURCE_USERNAME,
            password=settings.SOURCE_PASSWORD,
        )

        # Hook template ids might differ in between orgs
        # We try to find the corresponding template by comparing names
        # If no match is found, this hook will be processed as if the hook_template was not there at all
        template_id = extract_id_from_url(hook["hook_template"])
        source_hook_template = await source_client.request_json(
            "GET", f"hook_templates/{template_id}"
        )

        target_hook_templates = [
            item
            async for item in client._http_client.fetch_all_by_url("hook_templates")
        ]
        target_hook_template_match = None
        for target_template in target_hook_templates:
            if target_template["name"] == source_hook_template["name"]:
                target_hook_template_match = target_template
                break

        if not target_hook_template_match:
            return None

        hook["hook_template"] = target_hook_template_match["url"]

        initial_fields = ["name", "hook_template", "token_owner", "events"]
        create_payload = {
            **{k: hook[k] for k in initial_fields},
            "queues": [],
        }
        created_hook = await client._http_client.request_json(
            "POST", url="hooks/create", json=create_payload
        )
        return await client._http_client.update(
            resource=Resource.Hook, id_=created_hook["id"], data=hook
        )


async def create_hook_without_template(
    hook: dict, hook_mapping: dict, client: ElisAPIClient, progress: Progress
):
    # Use the dummy URL only for newly-created private hooks
    # And only if attribute override does not specify the url
    if (
        hook.get("type", None) != "function"
        and hook.get("config", {}).get("private", None)
        and hook_mapping.get("attribute_override", {}).get("config", {}).get("path", "")
        != "url"
    ):
        with PauseProgress(progress):
            private_hook_url = Prompt.ask(
                f"Please provide hook url (target base_url is '{client._http_client.base_url}') for '{hook['name']}'"
            )
            hook["config"]["url"] = (
                private_hook_url
                if private_hook_url
                else settings.PRIVATE_HOOK_DUMMY_URL
            )

    return await client._http_client.create(Resource.Hook, hook)
