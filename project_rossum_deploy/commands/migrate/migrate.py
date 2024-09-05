from copy import deepcopy
from anyio import Path
from rich import print
from rich.panel import Panel
import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import (
    download_project,
)
from project_rossum_deploy.commands.migrate.organization import migrate_organization
from project_rossum_deploy.common.migrate_config import migrate_config
from project_rossum_deploy.common.attribute_override import (
    override_migrated_objects_attributes,
    validate_override_migrated_objects_attributes,
)
from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.common.mapping import (
    extract_flat_lookup_table,
    extract_sources_targets,
    read_mapping,
    write_mapping,
)

from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.commands.migrate.schemas import migrate_schemas
from project_rossum_deploy.commands.migrate.workspaces import migrate_workspaces

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
    "--selected-only",
    "-so",
    default=False,
    is_flag=True,
    help="Releases only objects with a `selected: true` attribute in mapping.yaml and ignores the rest even without an ignore flag. Unlike ignore, this flag is not recursive = you have to put it on sub-objects (e.g., both queue AND inbox).",
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
)
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the pushed changes automatically.",
)
@click.option(
    "--message",
    "-m",
    default="Released changes to target organization",
    help="Commit message for pulling.",
)
@coro
async def migrate_project_wrapper(
    plan_only: bool, selected_only: bool, force: bool, commit: bool, message: str
):
    await migrate_config()
    await migrate_project(
        plan_only=plan_only,
        selected_only=selected_only,
        force=force,
        commit=commit,
        commit_message=message,
    )


async def migrate_project(
    client: ElisAPIClient = None,
    org_path: Path = None,
    plan_only: bool = False,
    selected_only: bool = False,
    force: bool = False,
    commit: bool = False,
    commit_message: str = "",
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

        if "ignore" in mapping["organization"]:
            raise click.ClickException(
                "Cannot ignore the whole organization, please remove the attribute from mapping."
            )

        source_organization_id = mapping["organization"].get("id", "")
        target_organization_id = (
            target_organizations[0].get("target_id", None)
            if len(target_organizations)
            else None
        )
        if not target_organization_id:
            raise click.ClickException(
                "No target for organization. If you want to migrate inside the same organization, just add a target with the same ID."
            )
        elif (
            settings.IS_PROJECT_IN_SAME_ORG
            and target_organization_id != source_organization_id
        ):
            raise click.ClickException(
                'Source and target organizations are different even though credentials.json has "use_same_org_as_target": true.'
            )
        elif (
            not settings.IS_PROJECT_IN_SAME_ORG
            and target_organization_id == source_organization_id
        ):
            raise click.ClickException(
                'Source and target organizations are the same even though credentials.json has "use_same_org_as_target": false.'
            )
        elif len(target_organizations) > 1:
            raise click.ClickException(
                "Multiple targets for the same organization are not supported. If you want to migrate the organization multiple times, create separate GIT branches and specify a different target_id."
            )

        if not client:
            client = await create_and_validate_client(settings.TARGET_DIRNAME)

        source_id_target_pairs = {}
        sources_by_source_id_map = {}
        errors_by_target_id = {}

        if not (
            await validate_override_migrated_objects_attributes(
                org_path / settings.SOURCE_DIRNAME, mapping
            )
        ):
            return

        source_path = org_path / settings.SOURCE_DIRNAME
        target_paths = await find_all_object_paths(org_path / settings.TARGET_DIRNAME)
        target_objects = [await read_json(path) for path in target_paths]

        await migrate_organization(
            source_path=source_path,
            client=client,
            mapping=mapping,
            source_id_target_pairs=source_id_target_pairs,
            sources_by_source_id_map=sources_by_source_id_map,
            target_organization_id=target_organization_id,
            plan_only=plan_only,
            selected_only=selected_only,
            target_objects=target_objects,
            errors=errors_by_target_id,
            force=force,
        )

        await migrate_schemas(
            source_path=source_path,
            client=client,
            mapping=mapping,
            source_id_target_pairs=source_id_target_pairs,
            sources_by_source_id_map=sources_by_source_id_map,
            plan_only=plan_only,
            selected_only=selected_only,
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
            plan_only=plan_only,
            selected_only=selected_only,
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
            plan_only=plan_only,
            selected_only=selected_only,
            target_objects=target_objects,
            errors=errors_by_target_id,
            force=force,
        )

        if not plan_only:
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

        if not plan_only and len(new_target_ids):
            print(Panel(f"These target objects were created: {new_target_ids}"))

        await override_migrated_objects_attributes(
            mapping=mapping,
            client=client,
            sources_by_source_id_map=sources_by_source_id_map,
            source_id_target_pairs=source_id_target_pairs,
            lookup_table=lookup_table,
            errors=errors_by_target_id,
            plan_only=plan_only,
            selected_only=selected_only,
        )

        if plan_only:
            return

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
            await download_project(
                destination=settings.TARGET_DIRNAME,
                client=client,
                org_path=org_path,
                commit=commit,
                commit_message=commit_message,
            )

            hints = """
            ! attention !
            The following was not migrated - queue.dedicated_engine, queue.generic_engine, queue.users, hook.secrets, queue.workflows.
            Make sure to check the following:
                1. assign dedicated/generic engine(s) to queues
                2. set hook.secrets for migrated hooks
                3. assign users to queues
                4. assign workflows to queues
            This applies only for newly created objects. Once these attributes are set on the target object, subsequent release commands keep the values.
            """
            print(Panel(f"{hints}"))
            print(
                Panel(
                    f"Finished {settings.MIGRATE_COMMAND_NAME}. Please check all messages printed during the process."
                )
            )
    except PrdVersionException as e:
        print(Panel(f"Unexpected error while migrating objects: {e}"))
        return
    except Exception as e:
        display_error(f"Unexpected error while migrating objects: {e}", e)
