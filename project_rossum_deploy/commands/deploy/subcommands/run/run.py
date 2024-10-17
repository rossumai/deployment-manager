import asyncio
from anyio import Path
import questionary
from rossum_api import APIClientError, ElisAPIClient


from project_rossum_deploy.commands.deploy.subcommands.run.organization_release import (
    OrganizationRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.release_file import (
    ReleaseFile,
)
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    get_target_credentials,
)

from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    display_error,
    settings,
)


async def deploy_release_file(
    release_file_path: Path,
    org_path: Path = None,
    target_client: ElisAPIClient = None,
    # force: bool = False,
    # commit: bool = False,
    # commit_message: str = "",
):
    release_file = await release_file_path.read_text()
    yaml = DeployYaml(release_file)
    if not check_required_keys(yaml.data):
        return

    if not org_path:
        org_path = Path("./")
    source_dir_path = org_path / yaml.data[settings.DEPLOY_KEY_SOURCE_DIR]

    # TODO: enable other non-target destinations
    # TODO: cross-org release test
    source_org = await read_json(source_dir_path / "organization.json")

    # TODO: parallelize release API requests

    # TODO: create a deployed version with target ids and keep the original file as is

    if not target_client:
        target_url = yaml.data[settings.DEPLOY_KEY_TARGET_URL]
        target_credentials = await get_target_credentials(
            org_path=org_path, yaml_data=yaml.data
        )
        if not target_credentials:
            display_error("Missing credentials for target API.")
            return
        target_client = ElisAPIClient(
            base_url=target_url, token=target_credentials.token
        )

    release = ReleaseFile(**yaml.data, client=target_client)

    if release.deployed_org_id:
        try:
            await target_client.retrieve_organization(release.deployed_org_id)
        except APIClientError as e:
            if e.status_code == 404:
                display_error(
                    f'Organization with ID "{release.deployed_org_id}" not found with the specified token in {target_client._http_client.base_url}. Please make sure you have to correct token and target URL.'
                )
                return

    organization_choices = []
    async for org in target_client.list_all_organizations():
        organization_choices.append(questionary.Choice(title=org.name, value=org))
    if len(organization_choices) > 1:
        target_org = await questionary.select(
            "Select target organization:", choices=organization_choices
        ).ask_async()
    else:
        target_org = organization_choices[0].value

    ### Organization
    if release.patch_target_org and target_org.id != source_org["id"]:
        organization_release = OrganizationRelease(
            client=target_client, data=source_org, target_org=target_org
        )
        await organization_release.deploy()

    ### Schemas
    await asyncio.gather(
        *[
            schema_release.initialize(
                yaml=yaml,
                client=target_client,
                source_dir_path=source_dir_path,
            )
            for schema_release in release.schemas
        ]
    )
    schema_targets = {}
    for schema_release in release.schemas:
        await schema_release.deploy()
        schema_targets[schema_release.id] = [
            target.data for target in schema_release.targets if target.data
        ]

    ### Hooks
    await asyncio.gather(
        *[
            hook_release.initialize(
                source_dir_path=source_dir_path,
                yaml=yaml,
                client=target_client,
                token_owner_id=release.token_owner_id,
            )
            for hook_release in release.hooks
        ]
    )
    hook_targets = {}
    for hook_release in release.hooks:
        await hook_release.deploy()
        hook_targets[hook_release.id] = [
            target.data for target in hook_release.targets if target.data
        ]
    await release.migrate_hook_dependency_graph(hook_targets=hook_targets)

    ### Workspaces
    await asyncio.gather(
        *[
            workspace_release.initialize(
                yaml=yaml,
                client=target_client,
                target_org_url=target_org.url,
                source_dir_path=source_dir_path,
            )
            for workspace_release in release.workspaces
        ]
    )
    workspace_targets = {}
    for workspace_release in release.workspaces:
        await workspace_release.deploy()
        workspace_targets[workspace_release.id] = [
            target.data for target in workspace_release.targets if target.data
        ]

    ### Queues
    await asyncio.gather(
        *[
            queue_release.initialize(
                yaml=yaml,
                client=target_client,
                source_dir_path=source_dir_path,
                workspace_targets=workspace_targets,
                hook_targets=hook_targets,
                schema_targets=schema_targets,
            )
            for queue_release in release.queues
        ]
    )
    queue_targets = {}
    for queue_release in release.queues:
        await queue_release.deploy()
        queue_targets[queue_release.id] = [
            target.data for target in queue_release.targets if target.data
        ]

    yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org.id
    yaml.save_to_file(str(release_file_path))

    lookup_table = {
        **schema_targets,
        **hook_targets,
        **workspace_targets,
        **queue_targets,
    }

    for release_object in [
        *release.schemas,
        *release.hooks,
        *release.workspaces,
        *release.queues,
    ]:
        release_object.implicit_override(lookup_table)

    return

    # TODO: check if remote was not modified when updating?

    # TODO: Show plan first, then ask for confirmation
    # Plan should include org names
    # Plan should check the files exist locally...
    # check if queue has its WS being deployed or it is a queue with an existing target_id

    # TODO: better representation of the deploy process

    # TODO: ??? How to solve name changes? (path and name will be different and won't locate the object)
    # During planning, show error that it cannot be found
    # Eventually, create utility to update a release file (template --update or whatever)

    # TODO: log all messages to stdout and into a separate file as well

    # TODO: make purge work with deploy files as well

    # TODO: download changes into proper dir (based on the deploy file)
