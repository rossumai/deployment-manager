# import json
# import yaml
from anyio import Path
import jmespath
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue, Inbox

from project_rossum_deploy.utils.consts import (
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
)
from project_rossum_deploy.utils.functions import flatten


def override_attributes_v2(
    lookup_table: dict,
    submapping: dict,
    object: Organization | Workspace | Hook | Schema | Queue | Inbox,
) -> Organization | Workspace | Hook | Schema | Queue | Inbox:
    attribute_overrides = submapping.get("attribute_override", {})
    for key, value in attribute_overrides.items():
        override_attribute_v2(
            key_query=key, new_value=value, object=object, lookup_table=lookup_table
        )


def override_attribute_v2(
    key_query: str, new_value: str, object: dict, lookup_table: dict
):
    parent, key = parse_parent_and_key(key_query)

    search = perform_search(parent, object)
    search = flatten(search)

    for override_parent in search:
        value_to_override = override_parent[key]

        # Referencing the value in source -> replace the '$' placeholder
        if ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD in new_value:
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
                for source_reference in value_to_override:
                    looked_up_value = lookup_table.get(source_reference, None)
                    if looked_up_value:
                        new_values.append(looked_up_value)
                override_parent[key] = new_values
            else:
                looked_up_value = lookup_table.get(value_to_override, None)
                if not looked_up_value:
                    raise Exception(
                        f'Found no target value for source key "{key}" and value "{value_to_override}".'
                    )
                override_parent[key] = looked_up_value
        # Value is not using any reference -> just replace
        else:
            override_parent[key] = new_value


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
        search = object
    else:
        search = jmespath.search(parent, object)
        if not search:
            raise Exception(f'Query "{parent}" returned no result.')

    if not isinstance(search, list):
        search = [search]

    return search


def preview_attribute_override(path: Path | str, object: dict, query_key: str):
    ...


def override_attributes(
    complete_mapping,
    mapping: dict,
    object: Organization | Workspace | Hook | Schema | Queue | Inbox,
) -> Organization | Workspace | Hook | Schema | Queue | Inbox:
    """
    Top level function for attribute_override. Either performs complex lookup in nested path or just replaces attribute with value as is.
    complete_mapping - mapping.yaml converted to JSON
    mapping - portion of mapping.yaml representing one Rossum object (queue, hook, ...).
    object - json representation of the API object that is being processed as downloaded from Rossum API.
    """
    if mapping.get("attribute_override"):
        keys = list(mapping["attribute_override"].keys())
        for key in keys:
            if isinstance(mapping["attribute_override"][key], dict):
                overrides = [mapping["attribute_override"][key]]
            elif isinstance(mapping["attribute_override"][key], list):
                overrides = mapping["attribute_override"][key]
            else:
                overrides = mapping["attribute_override"][key]

            if isinstance(overrides, list):
                for override in overrides:
                    path = override["path"]
                    reference_type = override["reference_type"].lower()
                    replace_reference_on_path(
                        complete_mapping=complete_mapping,
                        path=[key] + path.split("."),
                        reference_type=reference_type,
                        object=object,
                    )
            else:
                object[key] = overrides
    return object


def replace_reference_on_path(
    complete_mapping: dict,
    path: list,
    reference_type: str,
    object: Organization | Workspace | Hook | Schema | Queue | Inbox,
) -> Organization | Workspace | Hook | Schema | Queue | Inbox:
    """Function iterating over any dict and searching for the path defined - found values are then replaced with their counterpart values (determined from mapping)."""
    path_element = path.pop(0)
    object = object.get(path_element)
    if object and isinstance(object, list):
        for node in object:
            if isinstance(node, dict) and path[0] not in node:
                replace_reference_on_path(complete_mapping, path, reference_type, node)
            else:
                new_val = replace_value_of_type(
                    complete_mapping, reference_type, node[path[0]]
                )
                if new_val:
                    node[path[0]] = new_val
    elif object and isinstance(object, dict):
        replace_reference_on_path(complete_mapping, path, reference_type, object)
    elif object:
        new_val = replace_value_of_type(complete_mapping, reference_type, object)
        if new_val:
            object = new_val


def replace_value_of_type(complete_mapping, reference_type, value):
    """Replaces value (or values in case of list) that was found on the path."""
    ref_objects = find_mapping_section(complete_mapping, reference_type)
    if isinstance(value, list):
        for idx, val in enumerate(value):
            target_id = find_target_id(ref_objects, val)
            if target_id:
                value[idx] = target_id
    else:
        target_id = find_target_id(ref_objects, val)
        if target_id:
            value = target_id
    return value


def find_target_id(ref_objects, value):
    """Finds a counterpart value in the mapping.yaml file for each individual value found on path."""
    type, converted_value = convert_value(value)
    for objects in ref_objects:
        for object in objects:
            if object["id"] == converted_value:
                if type == "str":
                    return str(object["target_object"])
                elif type == "int":
                    return object["target_object"]
                elif type == "url":
                    parts = value.split("/")[:-1]
                    parts.append(str(object["target_object"]))
                    return "".join(parts)


def convert_value(value):
    """Converts value into int if necessary - supports int, str and url (ie. https://elis.rossum.ai/api/v1/queues/156)"""
    if isinstance(value, int):
        return "int", value
    elif isinstance(value, str) and "https" in value:
        return "url", int(value.split("/")[-1])
    elif isinstance(value, str):
        return "str", int(value)


def find_mapping_section(mapping, key):
    """Iterates over mapping json structure to find the section that holds array of objects of specific type - hooks, queues, ..."""
    if isinstance(mapping, list):
        for i in mapping:
            for x in find_mapping_section(i, key):
                yield x
    elif isinstance(mapping, dict):
        if key in mapping:
            yield mapping[key]
        for j in mapping.values():
            for x in find_mapping_section(j, key):
                yield x


"""
mapping = open("/Users/jan.sporek@rossum.ai/Projects/projectdeployment/project_rossum_deploy/common/mapping.yaml")

yaml_object = yaml.safe_load(mapping)
mapping = json.loads(json.dumps(yaml_object))

mapping_dm = {"id": 279307, "name": "my DMv2", "target_object": 123, "attribute_override": {"settings": {"path": "configurations.queue_ids", "type": "QUEUES"}}}
mapping_queue = {"id": 725687, "name": "queue 1", "target_object": 1234, "attribute_override": {"name": "new name of a queue"}}

with open("/Users/jan.sporek@rossum.ai/Projects/projectdeployment/project_rossum_deploy/common/dm.json") as f:
    payload = json.loads(f.read())
    print(override_attribute(mapping, mapping_dm, payload))

with open("/Users/jan.sporek@rossum.ai/Projects/projectdeployment/project_rossum_deploy/common/queue.json") as f:
    payload = json.loads(f.read())
    print(override_attribute(mapping, mapping_queue, payload))

"""
