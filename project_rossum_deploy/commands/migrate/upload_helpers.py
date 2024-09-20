from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.utils.functions import (
    find_object_by_id,
)
from project_rossum_deploy.common.modified_at import check_modified_timestamp
from project_rossum_deploy.utils.consts import (
    display_warning,
    settings,
)
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
)


class TargetObjectNotFoundException(Exception):
    def __init__(self, target_id, *args, **kwargs):
        msg = f'Not could not find target object with ID "{target_id}" locally. If it exists only on remote or is in {settings.SOURCE_DIRNAME}, please {settings.DOWNLOAD_COMMAND_NAME} it first.'
        super().__init__(msg, *args, **kwargs)


async def upload_organization(
    client: ElisAPIClient,
    organization: dict,
    local_target_organization: dict = None,
    errors={},
    force=False,
):
    if not local_target_organization:
        return

    target_organization_id = local_target_organization["id"]
    local_remote_timestamp_synced = await check_modified_timestamp(
        client,
        Resource.Organization,
        target_organization_id,
        local_target_organization,
    )
    if not force and not local_remote_timestamp_synced:
        errors[target_organization_id] = (
            Resource.Organization,
            local_target_organization.get("name", ""),
        )
        return local_target_organization

    if organization["id"] == target_organization_id:
        print(
            Panel(
                f"Skipping organization {settings.MIGRATE_COMMAND_NAME} - they are the same."
            )
        )
        return local_target_organization

    # Use only a subset of org fields where it makes sense to migrate
    organization_fields = {k: organization[k] for k in settings.ORGANIZATION_FIELDS}

    return await client._http_client.update(
        Resource.Organization, id_=target_organization_id, data=organization_fields
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
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Workspace, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Workspace, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Workspace, id_=target_id, data=workspace
        )
        print(f'Released (updated) workspace "{workspace['id']}" -> "{target_id}".')
        return result
    else:
        result = await client._http_client.create(Resource.Workspace, workspace)
        print(f'Released (created) workspace "{workspace['id']}" -> "{result['id']}".')
        return result


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
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Queue, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Queue, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Queue, id_=target_id, data=queue
        )
        print(f'Released (updated) queue "{queue['id']}" -> "{target_id}".')
        return result
    else:
        result = await client._http_client.create(Resource.Queue, queue)
        print(f'Released (created) queue "{queue['id']}" -> "{result['id']}".')
        return result


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
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Inbox, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Inbox, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Inbox, id_=target_id, data=inbox
        )
        print(f'Released (updated) inbox "{inbox['id']}" -> "{target_id}".')
        return result
    else:
        result = await client._http_client.create(Resource.Inbox, inbox)
        print(f'Released (created) inbox "{inbox['id']}" -> "{result['id']}".')
        return result


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
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Schema, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Schema, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Schema, id_=target_id, data=schema
        )
        print(f'Released (updated) schema "{schema['id']}" -> "{target_id}".')
        return result
    else:
        result = await client._http_client.create(Resource.Schema, schema)
        print(f'Released (created) schema "{schema['id']}" -> "{result['id']}".')
        return result


async def upload_hook(
    client: ElisAPIClient,
    hook: dict,
    hook_mapping: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Hook, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Hook, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Hook, id_=target_id, data=hook
        )
        print(f'Released (updated) hook "{hook['id']}" -> "{target_id}".')
        return result

    else:
        created_hook = await create_hook_based_on_template(hook=hook, client=client)
        if not created_hook:
            created_hook = await create_hook_without_template(
                hook=hook, client=client, hook_mapping=hook_mapping
            )
        print(f'Released (created) hook "{hook['id']}" -> "{created_hook['id']}".')
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
        try:
            source_client = await create_and_validate_client(
                destination=settings.SOURCE_DIRNAME
            )
        except Exception:
            display_warning(
                f"Invalid credentials for {settings.SOURCE_DIRNAME}, hooks will be created not based on their template."
            )
            return None

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

        # In case the hook became private, remove conflicting fields
        if (hook_config := created_hook.get("config", {})).get("private", False):
            fields_to_remove = ["code", "third_part_library_pack", "runtime"]
            for field in fields_to_remove:
                hook_config.pop("code", field)

        return await client._http_client.update(
            resource=Resource.Hook, id_=created_hook["id"], data=hook
        )


async def create_hook_without_template(
    hook: dict, hook_mapping: dict, client: ElisAPIClient
):
    # Use the dummy URL only for newly-created private hooks
    # And only if attribute override does not specify the url
    if (
        hook.get("type", None) != "function"
        and hook.get("config", {}).get("private", None)
        and hook_mapping.get("attribute_override", {}).get("config", {}).get("path", "")
        != "url"
    ):
        private_hook_url = Prompt.ask(
            f"Please provide hook url (target base_url is '{client._http_client.base_url}') for '{hook['name']}'"
        )
        hook["config"]["url"] = (
            private_hook_url if private_hook_url else settings.PRIVATE_HOOK_DUMMY_URL
        )

    return await client._http_client.create(Resource.Hook, hook)
