from anyio import Path
from rossum_api import ElisAPIClient
from rich import print

from project_rossum_deploy.commands.migrate.helpers import (
    check_if_selected,
    simulate_migrate_object,
)
from project_rossum_deploy.utils.functions import (
    find_object_by_id,
)
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    PrdVersionException,
    display_error,
    settings,
)
from project_rossum_deploy.commands.migrate.upload_helpers import (
    upload_organization,
)


class MissingTargetOrganizationException(Exception): ...


async def migrate_organization(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict[int, list],
    sources_by_source_id_map: dict,
    target_organization_id: int,
    plan_only: bool = False,
    selected_only: bool = False,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
):
    try:
        organization = await read_json(source_path / "organization.json")
        sources_by_source_id_map[organization["id"]] = organization

        if settings.IS_PROJECT_IN_SAME_ORG:
            local_target_organization = organization
        else:
            local_target_organization = find_object_by_id(
                target_organization_id, target_objects
            )
            if not local_target_organization:
                raise MissingTargetOrganizationException(
                    f"Missing local target object, please {settings.DOWNLOAD_COMMAND_NAME} it first."
                )

        source_id_target_pairs[mapping["organization"]["id"]] = [
            local_target_organization
        ]

        if selected_only and not check_if_selected(mapping["organization"]):
            return

        if plan_only:
            await simulate_migrate_object(
                client=client,
                source_object=organization,
                target_id=target_organization_id,
            )
        else:
            source_id_target_pairs[mapping["organization"]["id"]] = [
                await upload_organization(
                    client=client,
                    organization=organization,
                    local_target_organization=local_target_organization,
                    errors=errors,
                    force=force,
                )
            ]

            print(
                f'Released organization "{organization['id']}" -> "{target_organization_id}".'
            )
    except PrdVersionException as e:
        raise e
    except MissingTargetOrganizationException as e:
        raise e
    except Exception as e:
        display_error(f"Error while migrating organization object: {e}", e)
