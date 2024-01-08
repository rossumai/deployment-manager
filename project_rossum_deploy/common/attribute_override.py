# import json
# import yaml
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue, Inbox


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
                path = mapping["attribute_override"][key]["path"]
                reference_type = mapping["attribute_override"][key]["reference_type"].lower()
                replace_reference_on_path(
                    complete_mapping=complete_mapping,
                    path=[key] + path.split("."),
                    reference_type=reference_type,
                    object=object,
                )
            else:
                object[key] = mapping["attribute_override"][key]
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
                    return str(object["target"])
                elif type == "int":
                    return object["target"]
                elif type == "url":
                    parts = value.split("/")[:-1]
                    parts.append(str(object["target"]))
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

mapping_dm = {"id": 279307, "name": "my DMv2", "target": 123, "attribute_override": {"settings": {"path": "configurations.queue_ids", "type": "QUEUES"}}}
mapping_queue = {"id": 725687, "name": "queue 1", "target": 1234, "attribute_override": {"name": "new name of a queue"}}

with open("/Users/jan.sporek@rossum.ai/Projects/projectdeployment/project_rossum_deploy/common/dm.json") as f:
    payload = json.loads(f.read())
    print(override_attribute(mapping, mapping_dm, payload))

with open("/Users/jan.sporek@rossum.ai/Projects/projectdeployment/project_rossum_deploy/common/queue.json") as f:
    payload = json.loads(f.read())
    print(override_attribute(mapping, mapping_queue, payload))

"""
