from rich.prompt import Confirm

from project_rossum_deploy.common.mapping import extract_sources_targets
from project_rossum_deploy.utils.consts import display_warning, settings


def check_ids_exclusively_source_or_target(mapping: dict):
    # Organization is the only object that can be both source and target at the same time
    sources, targets = extract_sources_targets(mapping, include_organization=False)

    ids_on_both_sides = set()
    for source_group, target_group in zip(sources.values(), targets.values()):
        source_set, target_set = set(source_group), set(target_group)
        intersection = source_set.intersection(target_set)
        if len(intersection):
            for el in intersection:
                ids_on_both_sides.add(el)

    if ids_on_both_sides:
        display_warning(
            f"Found objects which are both {settings.SOURCE_DIRNAME} and {settings.TARGET_DIRNAME} in mapping:\n{ids_on_both_sides}"
        )
        user_decision = Confirm.ask(
            f"You should probably remove the objects from mapping and run {settings.DOWNLOAD_COMMAND_NAME}. Otherwise, the object will have a copy created even though it should be {settings.TARGET_DIRNAME}. Should {settings.MIGRATE_COMMAND_NAME} continue?"
        )
        return user_decision

    return True
