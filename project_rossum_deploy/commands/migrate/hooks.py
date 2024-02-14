from rich.progress import Progress
from anyio import Path
import click
from rossum_api import ElisAPIClient
from rich import print
from rich.prompt import Prompt

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    get_token_owner,
    is_first_time_migration,
)
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.common.attribute_override import override_attributes
from project_rossum_deploy.common.upload import upload_hook
from project_rossum_deploy.utils.functions import (
    PauseProgress,
    detemplatize_name_id,
    extract_id_from_url,
    read_json,
)


async def migrate_hooks(
    source_path: Path, client: ElisAPIClient, mapping: dict, progress: Progress
):
    source_id_target_pairs = {}
    hook_paths = [hook_path async for hook_path in (source_path / "hooks").iterdir()]
    task = progress.add_task("Releasing hooks...", total=len(hook_paths))

    target_token_owner_id = ""
    if not settings.IS_PROJECT_IN_SAME_ORG:
        target_org_token_owner = await get_token_owner(client)
        if not target_org_token_owner:
            with PauseProgress(progress):
                target_token_owner_id = Prompt.ask(
                    "Please input user ID of the hook token owner (e.g., 938382)"
                )
        else:
            target_token_owner_id = target_org_token_owner.id

    for hook_path in hook_paths:
        if hook_path.suffix != ".json":
            continue

        try:
            _, id = detemplatize_name_id(hook_path.stem)
            hook = await read_json(hook_path)

            hook["run_after"] = []
            hook["queues"] = []
            # Change token owner to TARGET user (important for cross-org migrations)
            if not settings.IS_PROJECT_IN_SAME_ORG:
                hook["token_owner"] = (
                    settings.TARGET_API_URL + f"/users/{target_token_owner_id}"
                )

            hook_mapping = find_mapping_of_object(mapping["organization"]["hooks"], id)
            if hook_mapping.get("ignore", None):
                progress.update(task, advance=1)
                continue

            hook = override_attributes(
                complete_mapping=mapping,
                mapping=hook_mapping,
                object=hook,
            )

            migrated_hook = None
            if is_first_time_migration(hook_mapping):
                migrated_hook = await create_hook_based_on_template(hook, client)

                if not migrated_hook:
                    migrated_hook = await create_hook_without_template(
                        hook=hook, hook_mapping=hook_mapping, client=client
                    )
            else:
                migrated_hook = await upload_hook(
                    client, hook, hook_mapping["target_object"]
                )

            hook_mapping["target_object"] = migrated_hook["id"]
            source_id_target_pairs[id] = migrated_hook

            progress.update(task, advance=1)
        except Exception as e:
            print(f"Error while migrating hook: {e}")

    await migrate_hook_dependency_graph(client, source_path, source_id_target_pairs)

    click.echo(
        "Hooks were successfully migrated to target. Please add any necessary secrets manually."
    )

    private_dummy_url_hooks = list(
        filter(
            lambda x: x["config"].get("url", None) == settings.PRIVATE_HOOK_DUMMY_URL,
            source_id_target_pairs.values(),
        )
    )
    if len(private_dummy_url_hooks):
        click.echo(
            "Private hooks detected. Please replace dummy URL in the following hooks using Django Admin:",
        )
        click.echo(
            "\n".join(
                list(
                    map(
                        lambda x: f'{x["name"]} ({x["id"]}): {x["url"]}',
                        private_dummy_url_hooks,
                    )
                )
            )
        )

    return source_id_target_pairs


async def create_hook_based_on_template(hook: dict, client: ElisAPIClient):
    if not hook.get("hook_template", None):
        return None

    if settings.IS_PROJECT_IN_SAME_ORG:
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
        source_hook_template = await source_client._http_client.fetch_one(
            "hook_templates", template_id
        )

        target_hook_templates = [
            item async for item in await client._http_client.fetch_all("hook_templates")
        ]
        target_hook_template_match = None
        for target_template in target_hook_templates:
            if target_template["name"] == source_hook_template["name"]:
                target_hook_template_match = target_template
                break

        if not target_hook_template_match:
            return None

        hook["hook_template"] = target_hook_template_match["url"]
        return await client._http_client.request_json(
            "POST", url="hooks/create", json=hook
        )


async def create_hook_without_template(
    hook: dict, hook_mapping: dict, client: ElisAPIClient
):
    # Use the dummy URL only for newly-created private hooks
    # And only if attribute override does not specify the url
    if (
        hook["type"] != "function"
        and hook.get("config", {}).get("private", None)
        and hook_mapping.get("attribute_override", {}).get("config", {}).get("path", "")
        != "url"
    ):
        hook["config"]["url"] = settings.PRIVATE_HOOK_DUMMY_URL

    return await upload_hook(client, hook, hook_mapping["target_object"])


async def migrate_hook_dependency_graph(
    client: ElisAPIClient, source_path: Path, source_id_target_pairs: dict
):
    async for hook_path in (source_path / "hooks").iterdir():
        if hook_path.suffix != ".json":
            continue

        try:
            _, old_hook_id = detemplatize_name_id(hook_path.stem)
            old_hook = await read_json(hook_path)
            new_hook = source_id_target_pairs.get(old_hook_id, None)

            # The hook was ignored, it has no target equivalent anyway
            if not new_hook:
                continue

            run_after = []
            for predecessor_url in old_hook["run_after"]:
                predecessor_id = extract_id_from_url(predecessor_url)
                # The hook was ignored, it has no target equivalent anyway
                target_object = source_id_target_pairs.get(predecessor_id, None)
                if not target_object:
                    continue

                new_url = predecessor_url.replace(
                    str(predecessor_id), str(target_object["id"])
                )
                run_after.append(new_url)

                await upload_hook(client, {"run_after": run_after}, new_hook["id"])
        except Exception as e:
            print(
                f"Error while migrating dependency graph for hook '{source_path}': {e}"
            )
