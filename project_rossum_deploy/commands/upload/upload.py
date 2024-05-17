from anyio import Path
from rich import print
from rich.panel import Panel
from rich.progress import Progress

import click
from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.upload.operations import (
    create_object,
    update_object,
)
from project_rossum_deploy.common.git import get_changed_file_paths
from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
    display_error,
    find_all_object_paths,
    gather_with_concurrency,
    make_request_with_progress,
    merge_formula_changes,
    merge_hook_changes,
    evaluate_create_dependencies,
)


@click.command(
    name=settings.UPLOAD_COMMAND_NAME,
    help="""
Updates local files that were changed into Rossum.
Only source files are taken into account by default.
               """,
)
@click.argument(
    "destination",
    default=settings.SOURCE_DIRNAME,
    type=click.Choice([settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]),
)
@click.option(
    "--all",
    "-a",
    default=False,
    is_flag=True,
    help="Uploads all local files in the selected destination (source/target) and not just files that were locally modified.",
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
)
@coro
async def upload_project_wrapper(destination, all, force):
    # To be able to run the command progammatically without the CLI decorators
    await upload_project(destination=destination, upload_all=all, force=force)


async def upload_project(
    destination: str, client: ElisAPIClient = None, upload_all=False, force=False
):
    try:
        org_path = Path("./")

        if not client:
            match destination:
                case settings.SOURCE_DIRNAME:
                    client = ElisAPIClient(
                        base_url=settings.SOURCE_API_URL,
                        token=settings.SOURCE_TOKEN,
                        username=settings.SOURCE_USERNAME,
                        password=settings.SOURCE_PASSWORD,
                    )
                case settings.TARGET_DIRNAME:
                    client = ElisAPIClient(
                        base_url=settings.TARGET_API_URL,
                        token=settings.TARGET_TOKEN,
                        username=settings.TARGET_USERNAME,
                        password=settings.TARGET_PASSWORD,
                    )
                case _:
                    raise click.ClickException(
                        f'Unrecognized destination "{destination}" to use {settings.UPLOAD_COMMAND_NAME}.'
                    )

        changes = get_changed_file_paths(destination)

        if changes:
            changes = await merge_hook_changes(changes, org_path)
            # changes = await evaluate_delete_dependencies(changes, org_path)
            changes = await merge_formula_changes(changes)
            changes = await evaluate_create_dependencies(changes, org_path, client)

        if upload_all:
            await include_unmodified_files(Path(org_path) / destination, changes)

        requests = []
        errors = []

        for change in changes:
            op, path = change
            match op:
                case GIT_CHARACTERS.CREATED:
                    requests.append(
                        create_object(
                            path=org_path / path,
                            client=client,
                            errors=errors,
                            force=force,
                        )
                    )
                case GIT_CHARACTERS.CREATED_STAGED:
                    requests.append(
                        create_object(
                            path=org_path / path,
                            client=client,
                            errors=errors,
                            force=force,
                        )
                    )
                # case GIT_CHARACTERS.DELETED:
                #    requests.append(delete_object(org_path / path, client, errors))
                case GIT_CHARACTERS.UPDATED:
                    if upload_all:
                        requests.append(
                            update_create_object(
                                client=client,
                                path=org_path / path,
                                errors=errors,
                                force=force,
                            )
                        )
                    else:
                        requests.append(
                            update_object(
                                client=client,
                                path=org_path / path,
                                errors=errors,
                                force=force,
                            )
                        )
                case _:
                    display_error(f'Unrecognized operation "{op}" for "{path}".')
                    errors.append({"op": op, "path": path})

        with Progress() as progress:
            task = progress.add_task(
                "Pushing changes to Rossum...", total=len(requests)
            )
            await gather_with_concurrency(
                5,
                *map(lambda r: make_request_with_progress(r, progress, task), requests),
            )

        if len(errors):
            errors_listed = "\n".join(list(map(lambda x: str(x["path"]), errors)))
            display_error(
                f"Errors happened during {settings.UPLOAD_COMMAND_NAME} for the following paths. Do not run {settings.DOWNLOAD_COMMAND_NAME} or you might lose changes in these files:\n{errors_listed}",
            )
            return
        else:
            print(
                Panel(
                    f"Finished {settings.UPLOAD_COMMAND_NAME}. Please commit the changes before running this command again."
                )
            )

    except Exception as e:
        display_error(f"Error during project {settings.UPLOAD_COMMAND_NAME}: {e}", e)


async def update_create_object(client, path, errors, force):
    result = await update_object(client=client, path=path, errors=errors, force=force)

    if not result:
        print(f'Recreating object with path "{path}".')
        await create_object(path=path, client=client, errors=errors, force=force)


async def include_unmodified_files(
    destination_path: Path, changes: list[tuple[str, Path]]
):
    all_files = await find_all_object_paths(destination_path)

    changes_paths = set(map(lambda x: x[1], changes))
    for file_path in all_files:
        if file_path not in changes_paths:
            changes.append((GIT_CHARACTERS.UPDATED.value, file_path))
