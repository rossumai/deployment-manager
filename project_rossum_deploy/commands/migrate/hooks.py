from rich.progress import Progress
from anyio import Path
import click
from rossum_api import ElisAPIClient
from rich import print

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    get_token_owner,
)
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.common.attribute_override import override_attributes
from project_rossum_deploy.common.upload import upload_hook
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    extract_id_from_url,
    read_json,
)


async def migrate_hooks(
    source_path: Path, client: ElisAPIClient, mapping: dict, progress: Progress
):
    source_id_target_pairs = {}
    token_owner = await get_token_owner(client)
    hook_paths = [hook_path async for hook_path in (source_path / "hooks").iterdir()]
    task = progress.add_task("Releasing hooks...", total=len(hook_paths))

    for hook_path in hook_paths:
        if hook_path.suffix != ".json":
            continue

        try:
            _, id = detemplatize_name_id(hook_path.stem)
            hook = await read_json(hook_path)

            hook["run_after"] = []
            hook["queues"] = []
            # Change token owner to TO user (important for cross-org migrations)
            hook["token_owner"] = token_owner.url

            hook_mapping = find_mapping_of_object(mapping["organization"]["hooks"], id)
            if hook_mapping.get("ignore", None):
                progress.update(task, advance=1)
                continue

            if (
                hook["type"] != "function"
                and hook.get("config", {}).get("private", None)
                and not hook_mapping["target"]
            ):
                # For updating already migrated private hooks, URL cannot be included in the payload
                hook["config"]["url"] = settings.PRIVATE_HOOK_DUMMY_URL

            hook = override_attributes(
                complete_mapping=mapping,
                mapping=hook_mapping,
                object=hook,
            )
            result = await upload_hook(client, hook, hook_mapping["target"])
            hook_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result

            progress.update(task, advance=1)
        except Exception as e:
            print(f"Error while migrating hook '{id}': {e}")

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
