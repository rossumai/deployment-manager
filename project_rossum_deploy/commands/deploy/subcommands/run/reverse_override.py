from copy import deepcopy
import questionary
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
)
from project_rossum_deploy.commands.deploy.subcommands.run.release_file import (
    ReleaseFile,
)
from project_rossum_deploy.commands.migrate.helpers import get_token_owner
from project_rossum_deploy.utils.consts import display_error, display_warning, settings


import jmespath
from rossum_api import ElisAPIClient
from rossum_api.models.organization import Organization
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.functions import flatten, templatize_name_id


class ObjectConfigReverser:
    prev_source_client: ElisAPIClient
    prev_target_client: ElisAPIClient

    def __init__(
        self, prev_source_client: ElisAPIClient, prev_target_client: ElisAPIClient
    ):
        self.prev_source_client = prev_source_client
        self.prev_target_client = prev_target_client

    async def reverse_config(self, object: dict, type: Resource):
        if target_len := len(object.get("targets", [])) != 1:
            display_warning(
                f"Cannot reverse object {object}: it has {target_len} and not 1."
            )
            return

        prev_source_id = object["id"]
        prev_target_id = object["targets"][0]["id"]
        prev_target_object = await self.prev_target_client._http_client.fetch_one(
            resource=type, id_=prev_target_id
        )
        prev_source_object = await self.prev_source_client._http_client.fetch_one(
            resource=type, id_=prev_source_id
        )

        object["id"] = prev_target_id
        object["name"] = prev_target_object.get("name", "")

        object["targets"][0]["id"] = prev_source_id
        self.reverse_attribute_override(
            prev_source_object=prev_source_object,
            attribute_override=object["targets"][0].get("attribute_override", {}),
        )

    def reverse_attribute_override(
        self, prev_source_object: dict, attribute_override: dict
    ):
        for attribute, prev_value in attribute_override.items():
            result = jmespath.search(attribute, prev_source_object)
            if not result:
                new_value = prev_value
            elif isinstance(result, list):
                result = flatten(result)
            else:
                result = [result]
            new_value = result[0]
            attribute_override[attribute] = new_value


class QueueConfigReverse(ObjectConfigReverser):
    prev_source_dir: str
    prev_target_dir: str

    def __init__(
        self, prev_source_client, prev_target_client, prev_source_dir, prev_target_dir
    ):
        super().__init__(prev_source_client, prev_target_client)
        self.prev_source_dir = prev_source_dir
        self.prev_target_dir = prev_target_dir

    async def reverse_config(self, object: dict, type: Resource):
        if target_len := len(object.get("targets", [])) != 1:
            display_warning(
                f"Cannot reverse object {object}: it has {target_len} and not 1."
            )
            return

        prev_source_id = object["id"]
        prev_target_id = object["targets"][0]["id"]
        prev_target_object = await self.prev_target_client._http_client.fetch_one(
            resource=type, id_=prev_target_id
        )
        prev_source_object = await self.prev_source_client._http_client.fetch_one(
            resource=type, id_=prev_source_id
        )

        object["id"] = prev_target_id
        object["name"] = prev_target_object.get("name", "")

        object["targets"][0]["id"] = prev_source_id
        self.reverse_attribute_override(
            prev_source_object=prev_source_object,
            attribute_override=object["targets"][0].get("attribute_override", {}),
        )
        prev_base_path = object[settings.DEPLOY_KEY_BASE_PATH]
        new_base_path = prev_base_path.replace(
            self.prev_source_dir, self.prev_target_dir
        )

        prev_source_ws = await self.prev_source_client.request_json(
            method="GET", url=prev_source_object["workspace"]
        )
        prev_ws_name_id = templatize_name_id(
            prev_source_ws["name"], prev_source_ws["id"]
        )
        prev_target_ws = await self.prev_target_client.request_json(
            method="GET", url=prev_target_object["workspace"]
        )
        new_ws_name_id = templatize_name_id(
            prev_target_ws["name"], prev_target_ws["id"]
        )
        new_base_path = new_base_path.replace(prev_ws_name_id, new_ws_name_id)

        object[settings.DEPLOY_KEY_BASE_PATH] = new_base_path

        await self.reverse_sub_object_config(
            object=object[settings.DEPLOY_KEY_SCHEMA], type=Resource.Schema
        )
        await self.reverse_sub_object_config(
            object=object[settings.DEPLOY_KEY_INBOX], type=Resource.Inbox
        )

    async def reverse_sub_object_config(self, object: dict, type: Resource):
        prev_source_id = object["id"]
        prev_target_id = object["targets"][0]["id"]
        prev_source_object = await self.prev_source_client._http_client.fetch_one(
            resource=type, id_=prev_source_id
        )

        object["id"] = prev_target_id
        object["targets"][0]["id"] = prev_source_id
        self.reverse_attribute_override(
            prev_source_object=prev_source_object,
            attribute_override=object["targets"][0].get("attribute_override", {}),
        )


async def reverse_source_target_in_yaml(
    yaml: DeployYaml,
    source_org: Organization,
    target_org: Organization,
    prev_source_client: ElisAPIClient,
    prev_target_client: ElisAPIClient,
):
    try:
        yaml = deepcopy(yaml)
        # Reverse dirs and urls
        prev_source_dir, prev_target_dir = (
            yaml.data[settings.DEPLOY_KEY_SOURCE_DIR],
            yaml.data[settings.DEPLOY_KEY_TARGET_DIR],
        )
        yaml.data[settings.DEPLOY_KEY_SOURCE_DIR] = prev_target_dir
        yaml.data[settings.DEPLOY_KEY_TARGET_DIR] = prev_source_dir

        prev_source_url, prev_target_url = (
            yaml.data[settings.DEPLOY_KEY_SOURCE_URL],
            yaml.data[settings.DEPLOY_KEY_TARGET_URL],
        )
        yaml.data[settings.DEPLOY_KEY_SOURCE_URL] = prev_target_url
        yaml.data[settings.DEPLOY_KEY_TARGET_URL] = prev_source_url

        yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = source_org.id

        if source_org.id == target_org.id:
            token_owner_id = yaml.data[settings.DEPLOY_KEY_TOKEN_OWNER]
        else:
            target_token_owner_from_remote = await get_token_owner(prev_target_client)
            if target_token_owner_from_remote:
                token_owner_id = target_token_owner_from_remote.id
            else:
                users = [user async for user in prev_target_client.list_all_users()]
                user_roles = [
                    role async for role in prev_target_client.list_all_user_roles()
                ]
                user_choices = [
                    questionary.Choice(title=user.username, value=user.id)
                    for user in users
                    if ReleaseFile.is_user_admin(user=user, user_roles=user_roles)
                ]
                token_owner_id = await questionary.select(
                    "Please choose target hook token owner:", choices=user_choices
                ).ask_async()
        yaml.data[settings.DEPLOY_KEY_TOKEN_OWNER] = token_owner_id

        # Reverse objects
        reverser = ObjectConfigReverser(
            prev_source_client=prev_source_client, prev_target_client=prev_target_client
        )
        queue_reverser = QueueConfigReverse(
            prev_source_client=prev_source_client,
            prev_target_client=prev_target_client,
            prev_source_dir=prev_source_dir,
            prev_target_dir=prev_target_dir,
        )

        for workspace in yaml.data.get(settings.DEPLOY_KEY_WORKSPACES, []):
            await reverser.reverse_config(object=workspace, type=Resource.Workspace)
        for queue in yaml.data.get(settings.DEPLOY_KEY_QUEUES, []):
            await queue_reverser.reverse_config(object=queue, type=Resource.Queue)
        for hook in yaml.data.get(settings.DEPLOY_KEY_HOOKS, []):
            await reverser.reverse_config(object=hook, type=Resource.Hook)

        # Empty unselected hooks: there is no equivalent to reverse since they were not selected for deploy...
        yaml.data[settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS] = []

        yaml.data[settings.DEPLOY_KEY_REVERSE_MAPPING] = False

        return yaml
    except Exception as e:
        display_error("Error while reversing mapipng in the deploy file. ^", e)
