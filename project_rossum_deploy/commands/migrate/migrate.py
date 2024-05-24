from copy import deepcopy
from anyio import Path
from rich import print
from rich.panel import Panel
from rich.progress import Progress
import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import (
    download_project,
)
from project_rossum_deploy.common.attribute_override import (
    override_migrated_objects_attributes,
    validate_override_migrated_objects_attributes,
)
from project_rossum_deploy.common.mapping import extract_flat_lookup_table, extract_sources_targets, read_mapping, write_mapping

from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.commands.migrate.schemas import migrate_schemas
from project_rossum_deploy.commands.migrate.workspaces import migrate_workspaces

from project_rossum_deploy.commands.migrate.upload_helpers import (
    upload_organization,
)

from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    PrdVersionException,
    display_error,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
    find_all_object_paths,
    flatten,
)


@click.command(
    name=settings.MIGRATE_COMMAND_NAME,
    help="""
Applies selected changes onto other objects.
If these objects don't exist, they get created.
The specifics of what objects to migrate and where to migrate them are specified in a mapping.yaml file.
               """,
)
@click.option(
    "--plan-only",
    "-p",
    help=f"Prints/simulates operations that would be done in the actual {settings.MIGRATE_COMMAND_NAME}.",
    default=False,
    is_flag=True,
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
)
@coro
async def migrate_project_wrapper(plan_only: bool, force: bool):
    await migrate_project(plan_only=plan_only, force=force)


async def migrate_project(
    client: ElisAPIClient = None,
    org_path: Path = None,
    plan_only: bool = False,
    force: bool = False,
):
    try:
        if not org_path:
            org_path = Path("./")
        mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
        previous_mapping = deepcopy(mapping)

        target_organizations = mapping["organization"].get("targets", [])

        if "target_object" in mapping["organization"]:
            raise PrdVersionException(
                f'Detected "target_object" for organization. Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
            )

        target_organization_id = (
            target_organizations[0].get("target_id", None)
            if len(target_organizations)
            else None
        )
        if not target_organization_id:
            raise click.ClickException(
                "No target for organization. If you want to migrate inside the same organization, just add a target with the same ID."
            )
        elif len(target_organizations) > 1:
            raise click.ClickException(
                "Multiple targets for the same organization are not supported. If you want to migrate the organization multiple times, create separate GIT branches and specify a different target_id."
            )

        if not client:
            if settings.IS_PROJECT_IN_SAME_ORG:
                client = ElisAPIClient(
                    base_url=settings.SOURCE_API_URL,
                    token=settings.SOURCE_TOKEN,
                    username=settings.SOURCE_USERNAME,
                    password=settings.SOURCE_PASSWORD,
                )
            else:
                client = ElisAPIClient(
                    base_url=settings.TARGET_API_URL,
                    token=settings.TARGET_TOKEN,
                    username=settings.TARGET_USERNAME,
                    password=settings.TARGET_PASSWORD,
                )

        source_id_target_pairs = {}
        sources_by_source_id_map = {}
        errors_by_target_id = {}

        if not (
            await validate_override_migrated_objects_attributes(
                org_path / settings.SOURCE_DIRNAME, mapping
            )
        ):
            return

        with Progress() as progress:
            task = progress.add_task("Releasing organization...", total=1)

            organization = await read_json(
                org_path / settings.SOURCE_DIRNAME / "organization.json"
            )
            sources_by_source_id_map[organization["id"]] = organization
            # Use only a subset of org fields where it makes sense to migrate
            organization_fields = {
                k: organization[k] for k in settings.ORGANIZATION_FIELDS
            }

            target_paths = await find_all_object_paths(
                org_path / settings.TARGET_DIRNAME
            )
            target_objects = [await read_json(path) for path in target_paths]

            source_id_target_pairs[mapping["organization"]["id"]] = [
                await upload_organization(
                    client,
                    organization_fields,
                    target_organization_id,
                    target_objects=[organization]
                    if settings.IS_PROJECT_IN_SAME_ORG
                    else target_objects,
                    errors=errors_by_target_id,
                    force=force,
                )
            ]
            progress.update(task, advance=1)

            source_path = org_path / settings.SOURCE_DIRNAME

            await migrate_schemas(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
                plan_only=plan_only,
                target_objects=target_objects,
                errors=errors_by_target_id,
                force=force,
            )
            await migrate_hooks(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
                plan_only=plan_only,
                target_objects=target_objects,
                errors=errors_by_target_id,
                force=force,
            )
            await migrate_workspaces(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
                plan_only=plan_only,
                target_objects=target_objects,
                errors=errors_by_target_id,
                force=force,
            )

        if plan_only:
            return

        # Update the mapping with right hand sides (targets) created during migration
        await write_mapping(org_path / settings.MAPPING_FILENAME, mapping)

        _, previous_targets = extract_sources_targets(previous_mapping)
        lookup_table = extract_flat_lookup_table(mapping)
        current_target_ids = set(
            flatten(filter(lambda x: len(x) > 0, lookup_table.values()))
        )

        previous_target_ids = []
        for objects in previous_targets.values():
            if len(objects):
                previous_target_ids.extend(objects)
        previous_target_ids = set(previous_target_ids)

        new_target_ids = current_target_ids.difference(previous_target_ids)

        if len(new_target_ids):
            print(Panel(f"These target objects were created: {new_target_ids}"))

        await override_migrated_objects_attributes(
            mapping=mapping,
            client=client,
            sources_by_source_id_map=sources_by_source_id_map,
            source_id_target_pairs=source_id_target_pairs,
            lookup_table=lookup_table,
            errors=errors_by_target_id,
        )

        if len(errors_by_target_id.keys()):
            errors_listed = "\n".join(
                [
                    f"{err[1][0]} - {err[1][1]} ({err[0]})"
                    for err in errors_by_target_id.items()
                ]
            )
            display_error(
                f"The following target IDs were not released because of a newer version existed in Rossum. Please check these remote versions and retry:\n{errors_listed}\n\nChanges made to target objects were not pulled to local because some target objects were not released, please do so manually.",
            )
            return
        else:
            await download_project(client=client, org_path=org_path)
            print(Panel(f"Finished {settings.MIGRATE_COMMAND_NAME}."))
    except PrdVersionException as e:
        print(Panel(f"Unexpected error while migrating objects: {e}"))
        return
    except Exception as e:
        display_error(f"Unexpected error while migrating objects: {e}", e)
