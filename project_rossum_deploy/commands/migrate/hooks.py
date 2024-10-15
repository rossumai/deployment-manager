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
    skip_migrate_object,
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
    find_all_hook_paths_in_destination,
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
    hook_paths = await find_all_hook_paths_in_destination(source_path)

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

            if plan_only and not skip_migration:
                partial_upload_hook = functools.partial(
                    simulate_migrate_object,
                    client=client,
                    source_object=hook,
                )
            elif skip_migration:
                partial_upload_hook = functools.partial(
                    skip_migrate_object,
                    source_object=hook,
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

    await migrate_hook_dependency_graph(client, hook_paths, source_id_target_pairs)

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
    client: ElisAPIClient,
    hook_paths: list[Path],
    source_id_target_pairs: dict[int, list],
):
    for hook_path in hook_paths:
        try:
            _, source_hook_id = detemplatize_name_id(hook_path.stem)
            source_hook = await read_json(hook_path)
            target_hooks = source_id_target_pairs.get(source_hook_id, [])

            # The hook was ignored, it has no targets equivalent
            if not len(target_hooks):
                continue

            for target_hook_index, target_hook in enumerate(target_hooks):
                target_run_after = await migrate_target_hook_run_after(
                    client=client,
                    target_hook_index=target_hook_index,
                    target_hook_count=len(target_hooks),
                    source_run_after=source_hook.get("run_after", []),
                    source_id_target_pairs=source_id_target_pairs,
                )
                await client._http_client.update(
                    Resource.Hook,
                    id_=target_hook["id"],
                    data={"run_after": target_run_after},
                )
        except Exception as e:
            display_error(
                f"Error while migrating dependency graph for hook '{hook_path}':",
                e,
            )


async def migrate_target_hook_run_after(
    client: ElisAPIClient,
    source_run_after: dict,
    target_hook_index: int,
    target_hook_count: int,
    source_id_target_pairs: dict[int, list],
):
    async def find_missing_hook_run_after(predecessor_id: int):
        # The predecessor hook was ignored, it has no targets equivalent
        # Take the predecessor's source and find its predecessor (if none, stop)
        # Find the predecessors' target and put that into run_after for this hook
        # If there is no target, repeat from line one
        try:
            predecessor = await client.retrieve_hook(predecessor_id)
        except Exception as e:
            display_error(
                f'Error while finding predecessor hook with ID "{predecessor_id}" in Rossum.',
                e,
            )
            return []

        return await migrate_target_hook_run_after(
            client=client,
            source_run_after=predecessor.run_after,
            target_hook_index=target_hook_index,
            target_hook_count=target_hook_count,
            source_id_target_pairs=source_id_target_pairs,
        )

    target_run_after = []

    for predecessor_url in source_run_after:
        predecessor_id = extract_id_from_url(predecessor_url)
        predecessor_target_objects = source_id_target_pairs.get(predecessor_id, [])

        if not len(predecessor_target_objects):
            target_run_after += await find_missing_hook_run_after(predecessor_id)
        # Assume each newly created hook should have its own run_after
        elif target_hook_count == len(predecessor_target_objects):
            new_url = predecessor_url.replace(
                str(predecessor_id),
                str(predecessor_target_objects[target_hook_index]["id"]),
            )
            target_run_after.append(new_url)
        # All hooks will have the same single run_after
        else:
            new_url = predecessor_url.replace(
                str(predecessor_id),
                str(predecessor_target_objects[0]["id"]),
            )
            target_run_after.append(new_url)

    return target_run_after
