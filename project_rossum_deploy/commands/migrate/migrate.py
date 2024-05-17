from copy import deepcopy
import re
from anyio import Path
from rich import print
from rich.panel import Panel
from rich.progress import Progress
import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import (
    download_project,
)
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import (
    traverse_mapping,
)
from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.commands.migrate.schemas import migrate_schemas
from project_rossum_deploy.commands.migrate.workspaces import migrate_workspaces
from project_rossum_deploy.common.attribute_override import (
    override_attributes_v2,
    replace_ids_in_settings,
)
from project_rossum_deploy.common.determine_path import determine_object_type_from_url
from project_rossum_deploy.common.upload import (
    upload_organization,
)

from project_rossum_deploy.utils.consts import PrdVersionException, settings
from project_rossum_deploy.utils.functions import (
    coro,
    display_error,
    extract_flat_lookup_table,
    extract_sources_targets,
    find_all_object_paths,
    flatten,
    read_json,
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
@coro
async def migrate_project_wrapper(plan_only: bool):
    await migrate_project(plan_only=plan_only)


async def migrate_project(
    client: ElisAPIClient = None, org_path: Path = None, plan_only: bool = False
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

            source_id_target_pairs[mapping["organization"]["id"]] = [
                await upload_organization(
                    client, organization_fields, target_organization_id
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
            )
            await migrate_hooks(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
                plan_only=plan_only,
            )
            await migrate_workspaces(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
                plan_only=plan_only,
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
        )

        print(Panel(f"Finished {settings.MIGRATE_COMMAND_NAME}."))

        await download_project(client=client, org_path=org_path)
    except PrdVersionException as e:
        print(Panel(f"Unexpected error while migrating objects: {e}"))
        return
    except Exception as e:
        display_error(f"Unexpected error while migrating objects: {e}", e)


def filter_created_target_ids(
    previous_mapping: dict, source_id_target_pairs: dict[int, list]
):
    _, previous_targets = extract_sources_targets(previous_mapping)
    previous_target_ids = []
    for objects in previous_targets.values():
        if isinstance(objects, list):
            previous_target_ids.extend(objects)
    previous_target_ids = set(previous_target_ids)

    all_target_ids = set()
    for objects in source_id_target_pairs.values():
        for object_id in map(lambda o: o["id"], objects):
            all_target_ids.add(object_id)

    return all_target_ids.difference(previous_target_ids)


async def validate_override_migrated_objects_attributes(
    base_path: Path, mapping: dict
) -> bool:
    try:
        print(Panel("Validating attribute_override..."))
        source_paths = await find_all_object_paths(base_path)
        source_objects = [await read_json(path) for path in source_paths]
        for mapping_object in traverse_mapping(mapping):
            if mapping_object.get("ignore", None) or not (
                targets := mapping_object.get("targets", [])
            ):
                continue

            source_object = None
            for source_candidate in source_objects:
                if source_candidate["id"] == mapping_object["id"]:
                    source_object = source_candidate
                    break

            for target in targets:
                source_copy = deepcopy(source_object)
                override_attributes_v2(
                    lookup_table=extract_flat_lookup_table(mapping),
                    target_submapping=target,
                    object=source_copy,
                    is_dryrun=True,
                )

        print(Panel("Attribute override dry-run found no errors."))
        return True
    except Exception as e:
        display_error(f"Attribute override dry-run failed: {e}", e)
        return False


async def override_migrated_objects_attributes(
    mapping: dict,
    client: ElisAPIClient,
    sources_by_source_id_map: dict,
    source_id_target_pairs: dict[int, list],
    lookup_table: dict,
):
    print(Panel("Running attribute_override..."))
    for mapping_object in traverse_mapping(mapping["organization"]):
        if mapping_object.get("ignore", None):
            continue

        source_object = sources_by_source_id_map.get(mapping_object["id"], None)
        target_objects = source_id_target_pairs.get(mapping_object["id"], [])
        targets_in_mapping = mapping_object.get("targets", [])

        if not source_object or not len(target_objects):
            continue

        for target_index, target_object in enumerate(target_objects):
            resource = determine_object_type_from_url(target_object["url"])

            # Implicit override for settings
            if "settings" in target_object:
                target_settings = await replace_ids_in_settings(
                    target_object["id"],
                    target_object["settings"],
                    lookup_table,
                    target_index,
                    num_targets=len(target_objects),
                )
                await client._http_client.update(
                    resource, target_object["id"], {"settings": target_settings}
                )

            # Explicit override for settings and anything else
            attribute_overrides = find_attribute_override_for_target(
                targets_in_mapping, target_object["id"]
            )
            source_object_subset = get_attributes_from_object(
                source_object, attribute_overrides
            )

            source_object_subset["id"] = target_object["id"]
            source_object_subset["url"] = target_object["url"]

            override_attributes_v2(
                lookup_table=lookup_table,
                target_submapping={
                    "target_id": target_object["id"],
                    "attribute_override": attribute_overrides,
                },
                object=source_object_subset,
            )

            await client._http_client.update(
                resource, target_object["id"], source_object_subset
            )


def find_attribute_override_for_target(targets_in_mapping: dict, target_id: int):
    for target in targets_in_mapping:
        if target.get("target_id", None) == target_id:
            return target.get("attribute_override", {})
    return {}


def get_attributes_from_object(object: dict, attribute_overrides: dict):
    ROOT_KEY_REGEX = re.compile(r"^(\w+)")
    object_subset = {}
    for query_key in attribute_overrides:
        regex_search = ROOT_KEY_REGEX.findall(query_key)
        if len(regex_search) and (root_key := regex_search[0]) not in object_subset:
            object_subset[root_key] = deepcopy(object[root_key])
    return object_subset
