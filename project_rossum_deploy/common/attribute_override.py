import jmespath
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue, Inbox

from project_rossum_deploy.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
)
from project_rossum_deploy.utils.functions import (
    flatten,
    convert_source_to_target_value,
)


def override_attributes_v2(
    lookup_table: dict,
    submapping: dict,
    object: Organization | Workspace | Hook | Schema | Queue | Inbox,
    is_dryrun: bool = False,
) -> Organization | Workspace | Hook | Schema | Queue | Inbox:
    if is_dryrun:
        lookup_table = {k: "dummy" for k in lookup_table}

    def override_attribute_v2(
        key_query: str,
        new_value: str,
    ):
        parent, key = parse_parent_and_key(key_query)

        search = perform_search(parent, object)

        for override_parent in search:

            # The attribute (key) might not be on all parent objects (e.g., configurations[*].queue_ids)
            if key not in override_parent:
                continue

            value_to_override = override_parent[key]

            # Referencing the value in source -> replace the '$' placeholder
            if (
                isinstance(new_value, str)
                and ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD in new_value
            ):
                if isinstance(value_to_override, list) or isinstance(
                    value_to_override, dict
                ):
                    raise Exception(
                        f'Cannot override non-primitive value "{value_to_override}" with "{new_value}".'
                    )
                override_parent[key] = new_value.replace(
                    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD, value_to_override
                )
            # Referencing a value from target -> perform lookup based on source value
            elif new_value == ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD:
                if isinstance(value_to_override, dict):
                    raise Exception(
                        f'Cannot override non-primitive value "{value_to_override}" with "{new_value}".'
                    )
                elif isinstance(value_to_override, list):
                    new_values = []
                    for source_value in value_to_override:
                        target_value = convert_source_to_target_value(
                            source_value, lookup_table
                        )
                        if target_value is not None:
                            new_values.append(target_value)

                    if not len(new_values):
                        raise Exception(
                            f'Found no target values for source key "{key_query}" and values "{value_to_override}".'
                        )
                    override_parent[key] = new_values
                else:
                    target_value = convert_source_to_target_value(
                        value_to_override, lookup_table
                    )
                    if target_value is None:
                        raise Exception(
                            f'Found no target value for source key "{key_query}" and value "{value_to_override}".'
                        )
                    override_parent[key] = target_value
            # Value is not using any reference -> just replace
            else:
                override_parent[key] = new_value

    attribute_overrides = submapping.get("attribute_override", {})
    for key, value in attribute_overrides.items():
        override_attribute_v2(
            key_query=key,
            new_value=value,
        )


def parse_parent_and_key(key_query: str):
    try:
        parent, key = ".".join(key_query.split(".")[:-1]), key_query.split(".")[-1]
    except Exception:
        raise Exception(
            f'Invalid query "{key_query}" - the last part must be a single object key.'
        )
    return parent, key


def perform_search(parent: str, object: dict):
    # The query targets a key of the top-most object, no need to search
    if not parent:
        return [object]

    search = jmespath.search(parent, object)
    if isinstance(search, list):
        search = flatten(search)
    else:
        search = [search]

    if not len(search):
        raise Exception(f'Query "{parent}" returned no result.')

    return search
