import questionary
from anyio import Path
from pydantic import BaseModel
from rich import print as pprint
from deployment_manager.common.custom_client import CustomAsyncRossumAPIClient as AsyncRossumAPIClient
from rossum_api.domain_logic.resources import Resource
from rossum_api.dtos import Token

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
    AttributeOverrider,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    get_url_and_credentials,
)
from deployment_manager.commands.download.downloader import Downloader
from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    display_warning,
    settings,
)
from deployment_manager.utils.functions import extract_id_from_url, templatize_name_id


class DeployFileReverser(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    input_file_path: Path
    project_path: Path

    source_path: Path = None
    target_path: Path = None

    source_client: AsyncRossumAPIClient = None
    target_client: AsyncRossumAPIClient = None

    yaml: DeployYaml = None

    async def initialize(self):
        input_file_content = await self.input_file_path.read_text()
        self.yaml = DeployYaml(file=input_file_content)

        source_dir_subdir = self.yaml.data[settings.DEPLOY_KEY_SOURCE_DIR]
        source_org_name = source_dir_subdir.split("/")[0]

        source_credentials = await get_url_and_credentials(
            project_path=self.project_path,
            org_name=source_org_name,
            type=settings.SOURCE_DIRNAME,
            yaml_data=self.yaml.data,
        )
        if not source_credentials:
            return
        self.source_client = AsyncRossumAPIClient(
            base_url=source_credentials.url, credentials=Token(source_credentials.token)
        )

        target_dir_subdir = self.yaml.data.get(settings.DEPLOY_KEY_TARGET_DIR, "")
        target_org_name = target_dir_subdir.split("/")[0]

        target_credentials = await get_url_and_credentials(
            project_path=self.project_path,
            org_name=target_org_name if target_dir_subdir else "",
            type=settings.TARGET_DIRNAME,
            yaml_data=self.yaml.data,
        )
        if not target_credentials:
            return
        self.target_client = AsyncRossumAPIClient(
            base_url=target_credentials.url, credentials=Token(target_credentials.token)
        )

        self.source_path = self.project_path / source_dir_subdir
        self.target_path = self.project_path / target_dir_subdir

    async def reverse_deploy_file(self):
        # ! A new hook in target not in deploy file will not get reversed -> needs to check proactively and ask user
        deploy_file_object = self.yaml.data

        deploy_file_object[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = None
        deploy_file_object[settings.DEPLOY_KEY_TOKEN_OWNER] = None
        deploy_file_object[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = None
        deploy_file_object[settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS] = []

        source_dir_and_subdir = deploy_file_object.get(
            settings.DEPLOY_KEY_SOURCE_DIR, None
        )
        target_dir_and_subdir = deploy_file_object.get(
            settings.DEPLOY_KEY_TARGET_DIR, None
        )

        (
            deploy_file_object[settings.DEPLOY_KEY_SOURCE_DIR],
            deploy_file_object[settings.DEPLOY_KEY_TARGET_DIR],
        ) = (
            target_dir_and_subdir,
            source_dir_and_subdir,
        )

        source_url = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_URL, "")
        target_url = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_URL, "")

        (
            deploy_file_object[settings.DEPLOY_KEY_SOURCE_URL],
            deploy_file_object[settings.DEPLOY_KEY_TARGET_URL],
        ) = (target_url, source_url)

        deploy_file_object[settings.DEPLOY_KEY_WORKSPACES] = (
            await self.reverse_object_type(
                type=Resource.Workspace,
                deploy_file_object=deploy_file_object,
            )
        )

        deploy_file_object[settings.DEPLOY_KEY_QUEUES] = await self.reverse_object_type(
            type=Resource.Queue,
            deploy_file_object=deploy_file_object,
        )

        deploy_file_object[settings.DEPLOY_KEY_HOOKS] = await self.reverse_object_type(
            type=Resource.Hook,
            deploy_file_object=deploy_file_object,
        )

        default_deploy_name = f"reverse_{self.input_file_path.stem}.yaml"
        deploy_file_path = (
            self.project_path / settings.DEFAULT_DEPLOY_PARENT / default_deploy_name
        )
        if await deploy_file_path.exists():
            deploy_file_path = await get_filepath_from_user(
                self.project_path,
                default=str(deploy_file_path),
            )

        state_file_name = f"reverse_{deploy_file_path.stem}.json"
        state_file_path = (
            self.project_path / settings.DEFAULT_DEPLOY_STATE_PARENT / state_file_name
        )
        if await state_file_path.exists():
            state_file_path = await get_filepath_from_user(
                self.project_path,
                default=str(state_file_path),
            )
        deploy_file_object[settings.DEPLOY_KEY_STATE_PATH] = str(state_file_path)

        await self.yaml.save_to_file(deploy_file_path)

        display_info(
            f"Deploy file saved to [green]{deploy_file_path}[/green]. Use it by running:"
        )

        pprint(
            f"\n  {settings.NEW_COMMAND_NAME} {settings.DEPLOY_COMMAND_NAME} {settings.DEPLOY_RUN_COMMAND_NAME} {deploy_file_path}\n"
        )

    async def reverse_object_type(self, type: Resource, deploy_file_object: dict):
        target_downloader = Downloader(client=self.target_client)
        source_downloader = Downloader(client=self.source_client)
        overrider = AttributeOverrider(type=type)

        source_objects = deploy_file_object.get(type.value, [])
        reversed_source_objects = []

        remote_target_objects = await target_downloader.download_remote_objects(
            type=type
        )
        remote_source_objects = await source_downloader.download_remote_objects(
            type=type
        )

        for source_object in source_objects:
            source_object_id, source_object_name = source_object.get(
                "id", ""
            ), source_object.get("name", "")
            if not source_object_id:
                display_warning(
                    f"No source ID for {type.value} {source_object_name} - skipping."
                )
                continue

            source_targets = source_object.get(settings.DEPLOY_KEY_TARGETS, [])
            if len(source_targets) == 0:
                display_warning(
                    f"No targets for {type.value} {source_object_name} ({source_object_id}) - skipping."
                )
                continue

            target_choices = self.prepare_target_choices(
                targets=source_targets, remote_targets=remote_target_objects
            )
            if not target_choices:
                display_warning(
                    f"No target ID specified for {type.value} {source_object_name} - skipping."
                )
                continue
            elif len(source_targets) > 1:
                display_warning(
                    f"{source_object_name} ({source_object_id}) has multiple targets."
                )
                selected_target_index = await questionary.select(
                    "Select which target should be used as source",
                    choices=target_choices,
                ).ask_async()
            else:
                selected_target_index = 0

            selected_target = source_targets[selected_target_index]
            remote_target = next(
                (x for x in remote_target_objects if selected_target["id"] == x["id"]),
            )

            reversed_object = {
                "id": remote_target["id"],
                "name": remote_target["name"],
                settings.DEPLOY_KEY_TARGETS: [{"id": source_object_id}],
            }

            if attribute_overrides := selected_target.get(
                settings.DEPLOY_KEY_OVERRIDES, {}
            ):
                remote_source = next(
                    (x for x in remote_source_objects if source_object_id == x["id"]),
                    None,
                )
                # If source does not exist, we preserve the attribute override even though there will be the same value since we might be using target even as source
                reversed_object[settings.DEPLOY_KEY_TARGETS][0][
                    settings.DEPLOY_KEY_OVERRIDES
                ] = overrider.reverse_attributes_v2(
                    source_object=remote_source if remote_source else remote_target,
                    target_object=remote_target,
                    attribute_overrides=attribute_overrides,
                )

            if type == Resource.Queue:
                try:
                    workspace_url = remote_target["workspace"]
                    workspace_id = extract_id_from_url(workspace_url)
                    workspace = await self.target_client.retrieve_workspace(
                        workspace_id
                    )
                    reversed_object[settings.DEPLOY_KEY_BASE_PATH] = str(
                        self.target_path
                        / "workspaces"
                        / templatize_name_id(workspace.name, workspace.id)
                    )
                except Exception:
                    display_warning(
                        f"Could not fetch workspace {workspace_id} for queue {reversed_object}"
                    )

            source_schema, source_inbox = source_object.get(
                settings.DEPLOY_KEY_SCHEMA, {}
            ), source_object.get(settings.DEPLOY_KEY_INBOX, {})

            if source_schema:
                source_schema_targets = source_schema.get(
                    settings.DEPLOY_KEY_TARGETS, []
                )
                if (
                    not source_schema_targets
                    or len(source_schema_targets) < selected_target_index
                ):
                    display_error(
                        f"Target schema found for {reversed_object['id']} - skipping"
                    )
                    continue
                selected_target_schema = source_schema_targets[selected_target_index]
                reversed_object[settings.DEPLOY_KEY_SCHEMA] = {
                    "id": selected_target_schema["id"],
                    settings.DEPLOY_KEY_TARGETS: [{"id": source_schema["id"]}],
                }

            if source_inbox:
                source_inbox_targets = source_inbox.get(settings.DEPLOY_KEY_TARGETS, [])
                if (
                    source_inbox_targets
                    and len(source_inbox_targets) >= selected_target_index
                ):
                    selected_target_inbox = source_inbox_targets[selected_target_index]
                    reversed_object[settings.DEPLOY_KEY_INBOX] = {
                        "id": selected_target_inbox["id"],
                        settings.DEPLOY_KEY_TARGETS: [{"id": source_inbox["id"]}],
                    }

            reversed_source_objects.append(reversed_object)

        return reversed_source_objects

    def prepare_target_choices(self, targets: list[dict], remote_targets: list[dict]):
        choices = []
        for target_index, target in enumerate(targets):
            if not (local_target_id := target.get("id", "")):
                continue
            remote_target = next(
                (x for x in remote_targets if local_target_id == x["id"]),
                None,
            )
            if not remote_target:
                display_warning(
                    f"No remote target found for target ID {local_target_id}."
                )
                continue

            remote_target_label = f'{remote_target["name"]} ({remote_target['id']})'
            choices.append(
                questionary.Choice(title=remote_target_label, value=target_index)
            )

        return choices
