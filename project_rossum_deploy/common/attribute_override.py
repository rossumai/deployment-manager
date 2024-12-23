import json
import re
import subprocess
import tempfile
import jmespath
from rich import print
from rich.panel import Panel
from copy import deepcopy
from anyio import Path
from rossum_api import ElisAPIClient

from project_rossum_deploy.common.mapping import extract_flat_lookup_table
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
    MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER,
)
from project_rossum_deploy.utils.functions import (
    flatten,
    find_all_object_paths,
)
from project_rossum_deploy.commands.migrate.helpers import (
    check_if_selected,
    traverse_mapping,
)
from project_rossum_deploy.common.determine_path import determine_object_type_from_url
from project_rossum_deploy.utils.consts import (
    display_error,
)


def convert_reference_to_int_id(value):
    """Converts value into int if necessary and returns the original type - supports int, str and url (ie. https://elis.rossum.ai/api/v1/queues/156)"""
    if isinstance(value, int):
        return "int", value
    elif isinstance(value, str) and "https" in value:
        return "url", int(value.split("/")[-1])
    elif isinstance(value, str):
        return "str", int(value)


def convert_source_to_target_values(source_value, lookup_table: dict) -> list:
    """Finds a counterpart id in the lookup table file and replace it based on the type of the original value.
    There can be multiple target values for a single source value.
    """
    result = []
    type, source_id = convert_reference_to_int_id(source_value)
    target_ids = lookup_table.get(source_id, None)
    if len(target_ids):
        for target_id in target_ids:
            match type:
                case "str":
                    result.append(str(target_id))
                case "url":
                    parts = source_value.split("/")[:-1]
                    parts.append(str(target_id))
                    result.append("".join(parts))
                case "int":
                    result.append(target_id)
    return result


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
        dot = [pos for pos, char in enumerate(key_query) if char == "."]
        pipe = [pos for pos, char in enumerate(key_query) if char == "|"]
        dot_idx = dot[-1] if dot else -1
        pipe_idx = pipe[-1] if pipe else -1
        idx = dot_idx if dot_idx>-1 else pipe_idx if pipe_idx>-1 else -1
        parent = key_query[:idx].strip() if idx > -1 else None 
        key = key_query[idx+1:].strip() if idx > -1 else key_query
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

        basic_error_message = (
            f"Could not override source '{source_id}' in settings of '{object_id}'."
        )
        if not target_ids:
            print(
                Panel(
                    f"{basic_error_message} No target IDs found.",
                    style="yellow",
                ),
            )
            continue
        elif num_targets != len(target_ids):
            print(
                Panel(
                    f"{basic_error_message} There are multiple target IDs that could be assigned. Please do the attribute_override explicitly.",
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


async def validate_override_migrated_objects_attributes(
    base_path: Path, mapping: dict
) -> bool:
    try:
        print(Panel("Validating attribute_override."))
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
    errors: dict,
    plan_only: bool = False,
    selected_only: bool = False,
):
    print(Panel(f"Running attribute_override{' (simulated)' if plan_only else ''}."))
    for mapping_object in traverse_mapping(mapping["organization"]):
        if mapping_object.get("ignore", None) or (
            selected_only and not check_if_selected(mapping_object)
        ):
            continue

        source_object = sources_by_source_id_map.get(mapping_object["id"], None)
        target_objects = source_id_target_pairs.get(mapping_object["id"], [])
        targets_in_mapping = mapping_object.get("targets", [])

        if not source_object or not len(target_objects):
            continue

        for target_index, target_object in enumerate(target_objects):
            if target_object["id"] in errors:
                continue

            object_type = determine_object_type_from_url(target_object["url"])

            # Implicit override for settings
            if "settings" in target_object:
                target_settings = await replace_ids_in_settings(
                    target_object["id"],
                    target_object["settings"],
                    lookup_table,
                    target_index,
                    num_targets=len(target_objects),
                )
                if plan_only:
                    with tempfile.NamedTemporaryFile() as tf1, tempfile.NamedTemporaryFile() as tf2:
                        tf1.write(
                            bytes(
                                json.dumps(target_object["settings"], indent=2), "UTF-8"
                            )
                        )
                        tf2.write(bytes(json.dumps(target_settings, indent=2), "UTF-8"))
                        # Has to be manually seeked back to start
                        tf1.seek(0)
                        tf2.seek(0)
                        diff = subprocess.run(
                            ["diff", tf1.name, tf2.name],
                            capture_output=True,
                            text=True,
                        )
                        if diff.stdout:
                            print(
                                print_simulation_message(
                                    attribute_override_type="implicit",
                                    object_type=object_type.value,
                                    source_object=source_object,
                                    target_object=target_object,
                                    source_object_subset=diff.stdout,
                                )
                            )
                else:
                    await client._http_client.update(
                        object_type, target_object["id"], {"settings": target_settings}
                    )
            # Explicit override for settings and anything else
            attribute_overrides = find_attribute_override_for_target(
                targets_in_mapping, target_object["id"], target_index
            )
            if not attribute_overrides:
                continue

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
            if plan_only:
                # Clean up for display
                del source_object_subset["id"]
                del source_object_subset["url"]
                print(
                    print_simulation_message(
                        attribute_override_type="explicit",
                        object_type=object_type.value,
                        source_object=source_object,
                        target_object=target_object,
                        source_object_subset=source_object_subset,
                    )
                )
            else:
                await client._http_client.update(
                    object_type, target_object["id"], source_object_subset
                )


def print_simulation_message(
    attribute_override_type: str,
    object_type: str,
    source_object: dict,
    target_object: dict,
    source_object_subset: dict,
):
    target_name = (
        f'{target_object['id']} {target_object.get('name', 'no-name')}'
        if target_object["id"] != source_object["id"]
        else MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER
    )
    return f'Simulated [green]{attribute_override_type}[/green] attribute override of [yellow]{object_type}[/yellow]: source "{source_object['id']} {source_object.get('name', 'no-name')}" to target "{target_name}": {json.dumps(source_object_subset, indent=2)}'


def find_attribute_override_for_target(
    targets_in_mapping: dict, target_id: int, target_index: int
):
    for iterated_target_index, target in enumerate(targets_in_mapping):
        iterated_target_id = target.get("target_id", None)
        if iterated_target_id is None and target_index == iterated_target_index:
            return target.get("attribute_override", {})
        elif iterated_target_id == target_id:
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
