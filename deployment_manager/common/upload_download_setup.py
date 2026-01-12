from anyio import Path
from deployment_manager.commands.download.directory import OrganizationDirectory
from deployment_manager.utils.consts import display_warning, settings

ConfiguredDirectories = dict[str, OrganizationDirectory]


def check_unique_org_ids(configured_directories: ConfiguredDirectories):
    unique_org_ids = set(
        dir_config.org_id for dir_config in configured_directories.values()
    )
    if len(unique_org_ids) != len(configured_directories.values()):
        display_warning(
            "Configured directories do not have unique org IDs. If you want to have multiple directories for the same organization, use subdirectories."
        )
        return False
    return True


def expand_destinations(
    destinations: tuple[Path],
    project_path: Path,
    configured_directories: ConfiguredDirectories,
):
    """Expands the given destinations to include all subdirectories"""
    expanded_destinations = []
    for destination in destinations:
        dir_name = (
            str(destination.name)
            if destination.parent == project_path
            else str(destination.parent)
        )
        if dir_name not in configured_directories:
            display_warning(
                f'Destination "{destination}" not configured in {settings.CONFIG_FILENAME}. Skipping.'
            )
            continue

        # Only the "org-level" destination was specified
        # Go through configured subdirectories and add them as destinations
        if destination.parent == project_path:
            dir_config = configured_directories.get(destination.name, {})
            expanded_destinations.extend(
                [
                    str(project_path / destination / subdir)
                    for subdir in dir_config.subdirectories.keys()
                ]
            )

        else:
            expanded_destinations.append(str(destination))

    return expanded_destinations


def mark_subdirectories_to_include(
    configured_directories: ConfiguredDirectories,
    expanded_destinations: list[str],
):
    # Normalize path separators for cross-platform compatibility (Windows uses backslashes)
    normalized_destinations = [d.replace("\\", "/") for d in expanded_destinations]
    for dir_name, dir_config in configured_directories.items():
        for subdir_name, subdir_config in dir_config.subdirectories.items():
            if f"{dir_name}/{subdir_name}" in normalized_destinations:
                subdir_config.include = True
