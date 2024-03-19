import jmespath

from project_rossum_deploy.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
)
from project_rossum_deploy.utils.functions import (
    flatten,
    convert_source_to_target_values,
)


def override_attributes_v2(
    lookup_table: dict,
    object: dict,
    submapping: dict,
    is_dryrun: bool = False,
) -> dict:
    if is_dryrun:
        lookup_table = {k: ["dummy"] for k in lookup_table}

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
                        target_values = convert_source_to_target_values(
                            source_value, lookup_table
                        )
                        if len(target_values):
                            new_values.extend(target_values)

                    if not len(new_values):
                        raise Exception(
                            f'Found no target values for source key "{key_query}" and values "{value_to_override}".'
                        )
                    override_parent[key] = new_values
                else:
                    target_values = convert_source_to_target_values(
                        value_to_override, lookup_table
                    )
                    if not len(target_values):
                        raise Exception(
                            f'Found no target values for source key "{key_query}" and value "{value_to_override}".'
                        )
                    override_parent[key] = target_values
            # Value is not using any reference -> just replace
            else:
                override_parent[key] = new_value

    if not object:
        raise Exception(
            f'Cannot perform attribute_override on None object (name: {submapping.get("name", "")} | id: {submapping.get("id", "")}).'
        )

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

    if not len(search) or not search[0]:
        raise Exception(f'Query "{parent}" returned no result.')

    return search
