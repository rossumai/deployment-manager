import asyncio
import functools
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from project_rossum_deploy.commands.migrate.helpers import (
    check_if_selected,
    get_token_owner,
    migrate_object_to_multiple_targets,
    simulate_migrate_object,
)
from project_rossum_deploy.common.mapping import find_mapping_of_object
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    PrdVersionException,
    display_error,
    settings,
)
from project_rossum_deploy.commands.migrate.upload_helpers import upload_hook
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    extract_id_from_url,
)


async def migrate_hooks(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict[int, list],
    sources_by_source_id_map: dict,
    plan_only: bool = False,
    selected_only: bool = False,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
):
    hook_paths = [hook_path async for hook_path in (source_path / "hooks").iterdir()]

    target_token_owner_id = ""
    if not settings.IS_PROJECT_IN_SAME_ORG:
        target_org_token_owner = await get_token_owner(client)
        if not target_org_token_owner:
            target_token_owner_id = Prompt.ask(
                "Please input user ID of the hook token owner (e.g., 938382)"
            )
        else:
            target_token_owner_id = target_org_token_owner.id

    async def migrate_hook(hook_path: Path):
        if hook_path.suffix != ".json":
            return

        try:
            _, id = detemplatize_name_id(hook_path.stem)
            hook = await read_json(hook_path)
            sources_by_source_id_map[id] = hook

            hook["run_after"] = []
            hook["queues"] = []
            # Change token owner to TARGET user (important for cross-org migrations)
            if not settings.IS_PROJECT_IN_SAME_ORG:
                hook["token_owner"] = (
                    settings.TARGET_API_URL + f"/users/{target_token_owner_id}"
                )

            hook_mapping = find_mapping_of_object(mapping["organization"]["hooks"], id)

            skip_migration = hook_mapping.get("ignore", None) or (
                selected_only and not check_if_selected(hook_mapping)
            )

            await update_hook_code(hook_path, hook)

            if plan_only or skip_migration:
                partial_upload_hook = functools.partial(
                    simulate_migrate_object,
                    client=client,
                    source_object=hook,
                    target_object_type=Resource.Hook,
                    silent=skip_migration,
                )
            else:
                partial_upload_hook = functools.partial(
                    upload_hook,
                    client=client,
                    hook=hook,
                    hook_mapping=hook_mapping,
                    target_objects=target_objects,
                    errors=errors,
                    force=force,
                )
            source_id_target_pairs[id] = []
            if "target_object" in hook_mapping:
                raise PrdVersionException(
                    f'Detected "target_object" for hook with ID "{id}". Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
                )

            results = await migrate_object_to_multiple_targets(
                submapping=hook_mapping,
                upload_function=partial_upload_hook,
                plan_only=plan_only,
            )
            source_id_target_pairs[id].extend(results)
        except PrdVersionException as e:
            raise e
        except Exception as e:
            display_error(f"Error while migrating hook with path '{hook_path}': {e}", e)

    if plan_only:
        print(Panel("Simulating hooks."))

    await asyncio.gather(
        *[migrate_hook(hook_path=hook_path) for hook_path in hook_paths]
    )

    if plan_only:
        return

    await migrate_hook_dependency_graph(client, source_path, source_id_target_pairs)

    print(
        Panel(
            "Hooks were successfully migrated to target. Please add any necessary secrets manually."
        )
    )


async def update_hook_code(hook_path: Path, hook: dict):
    """Checks if there is not newer code in the associated file and uses that for release.
    The original hook file is not modified.
    """
    if hook.get("extension_source", "") != "rossum_store" and (
        hook.get("config", {}).get("code", None)
    ):
        suffix = ".py" if "python" in hook["config"].get("runtime") else ".js"
        code_path = hook_path.with_suffix(suffix)
        new_code = await code_path.read_text()
        hook["config"]["code"] = new_code


async def migrate_hook_dependency_graph(
    client: ElisAPIClient, source_path: Path, source_id_target_pairs: dict[int, list]
):
    async for hook_path in (source_path / "hooks").iterdir():
        if hook_path.suffix != ".json":
            continue

        try:
            _, old_hook_id = detemplatize_name_id(hook_path.stem)
            old_hook = await read_json(hook_path)
            new_hooks = source_id_target_pairs.get(old_hook_id, None)

            # The hook was ignored, it has no targets equivalent
            if not new_hooks or not len(new_hooks):
                continue

            for new_hook_index, new_hook in enumerate(new_hooks):
                new_run_after = []
                for predecessor_url in old_hook["run_after"]:
                    predecessor_id = extract_id_from_url(predecessor_url)
                    target_objects = source_id_target_pairs.get(predecessor_id, [])
                    # The hook was ignored, it has no targets equivalent
                    if not len(target_objects):
                        continue
                    # Assume each hook should have its own run_after
                    elif len(new_hooks) == len(target_objects):
                        new_url = predecessor_url.replace(
                            str(predecessor_id),
                            str(target_objects[new_hook_index]["id"]),
                        )
                        new_run_after.append(new_url)
                    # All hooks will have the same single run_after
                    elif len(target_objects) == 1:
                        new_url = predecessor_url.replace(
                            str(predecessor_id), str(target_objects[0]["id"])
                        )
                        new_run_after.append(new_url)
                    else:
                        new_url = predecessor_url.replace(
                            str(predecessor_id), str(target_objects[0]["id"])
                        )
                        new_run_after.append(new_url)
                        new_hook_ids = "".join(list(map(lambda x: x["id"], new_hooks)))
                        print(
                            Panel(
                                f'Could not determine new predecessors for migrated hooks "{new_hook_ids}". The source predecessor ID is "{predecessor_id}". Assigning everything to target predecessor "{target_objects[0]["id"]}"'
                            )
                        )
                        continue

                await client._http_client.update(
                    Resource.Hook, id_=new_hook["id"], data={"run_after": new_run_after}
                )
        except Exception as e:
            display_error(
                f"Error while migrating dependency graph for hook '{source_path}': {e}",
                e,
            )
            raise e
