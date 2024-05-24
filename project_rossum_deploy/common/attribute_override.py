import json
import re
import jmespath
from rich import print
from rich.panel import Panel

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
    target_submapping: dict,
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
            f'Cannot perform attribute_override on None object (target name: {target_submapping.get("name", "")} | target id: {target_submapping.get("id", "")}).'
        )

    attribute_overrides = target_submapping.get("attribute_override", {})
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


async def replace_ids_in_settings(
    object_id: int,
    object_settings: dict,
    lookup_table: dict,
    object_index: int,
    num_targets: int,
):
    stringified_dict = json.dumps(object_settings)
    for source_id, target_ids in lookup_table.items():
        source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
        if not re.search(source_id_regex, stringified_dict):
            continue

        if len(target_ids) != 1 and num_targets != len(target_ids):
            print(
                Panel(
                    f"Could not override source '{source_id}' in settings of '{object_id}'. There are multiple target IDs. Please do the attribute_override explicitly.",
                    style="yellow",
                ),
            )
            continue

        # Using lambdas for sub() because of quotes inside strings
        # N:N objects -> objects are referenced in pairs
        elif num_targets == len(target_ids):
            stringified_dict = re.sub(
                source_id_regex,
                lambda m: str(target_ids[object_index])
                if m[0] == str(source_id)
                else m[0],
                stringified_dict,
            )
        # N:1 objects -> everything should be mapped to the first target ID
        else:
            stringified_dict = re.sub(
                source_id_regex,
                lambda m: str(target_ids[0]) if m[0] == str(source_id) else m[0],
                stringified_dict,
            )

    return json.loads(stringified_dict)
