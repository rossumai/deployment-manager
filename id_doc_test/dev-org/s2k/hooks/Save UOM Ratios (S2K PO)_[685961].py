import copy
import json
import re
from datetime import datetime

import requests


def rossum_hook_request_handler(payload):
    """
    The rossum_hook_request_handler is an obligatory main function that accepts
    input and produces output of the rossum custom function hook.
    :param payload: see https://api.elis.rossum.ai/docs/#annotation-content-event-data-format
    :return: messages and operations that update the annotation content or show messages
    """
    messages = []
    operations = []

    if (
        payload["event"] == "annotation_status"
        and payload["action"] in ("changed")
        and payload["annotation"]["status"] in ("confirmed", "exported", "failed_export")
    ):
        try:
            messages, operations = main(payload)
        except Exception as msg:
            messages = [create_message("error", str(msg), None)]

    return {"messages": messages, "operations": operations}


def main(payload):
    messages = []
    operations = []

    # init variables
    token = payload["rossum_authorization_token"]
    settings = payload["settings"]
    fields_to_db = payload["settings"]["fields_to_db"]
    fields_to_db, aliases = get_aliases(fields_to_db)
    base_url = payload["base_url"]
    collection_name = settings["collection_name"]
    ds_url = f"{base_url}/svc/data-storage/api/v1"

    # get content and schema
    header = {"Authorization": f"Bearer {token}"}
    res = requests.get(payload["annotation"]["content"], headers=header, timeout=20)
    content = json.loads(res.text)["content"]
    schema = payload["schemas"][0]["content"]

    # reformat annotation content for easier use
    document = [normalize_annotation(content, {}, [], False, schema, fields_to_db)]
    # normalize line items if needed
    if settings.get("normalize_array"):
        document = normalize_arrays(document, settings["normalize_array"])

    # cleanup documents if there are docs to be excluded
    included_documents = list()
    if settings.get("skip_record_insert"):
        for excl_key_values in settings.get("skip_record_insert"):
            for doc in document:
                print(doc)
                exclude_doc = True
                for key in excl_key_values:
                    if excl_key_values[key] != doc.get(key):
                        exclude_doc = False
                        break
                if not exclude_doc:
                    included_documents.append(doc)
    else:
        included_documents = document

    # run DS operations
    if included_documents:
        skip_insert = False
        if settings.get("unique_natural_key") and settings.get("primary_key"):
            skip_insert = remove_existing_objects(
                included_documents,
                collection_name,
                settings["unique_natural_key"],
                settings["primary_key"],
                settings.get("keep_first", False),
                token,
                ds_url,
            )
        # find record with the same annotation_id, if it exists
        if not skip_insert:
            response = find_in_data_storage_collection(
                collection_name, {"annotation_id": payload["annotation"]["id"]}, token, ds_url, {}
            )
            messages = process_data(
                payload, response, included_documents, token, messages, aliases, collection_name, ds_url
            )

    return messages, operations


def process_data(payload, response, document, token, messages, aliases, collection_name, ds_url):
    if not response["result"]:
        messages = create_record_in_ds(messages, payload, document, token, aliases, collection_name, ds_url)

    elif response["result"]:  # there is record with the same annotation id already
        delete_many_data_storage_collection(
            collection_name, {"annotation_id": payload["annotation"]["id"]}, token, ds_url
        )
        messages = create_record_in_ds(messages, payload, document, token, aliases, collection_name, ds_url)

    return messages


def replace_aliases(document, aliases):
    for alias in aliases.keys():
        if alias in document:
            document[aliases[alias]] = document[alias]
            del document[alias]
    return document


def get_aliases(fields_to_db: dict):
    aliases = {}
    fields_to_db_n = []
    for ftdb in fields_to_db:
        parts = ftdb.split(" as ")
        if len(parts) > 1:
            fields_to_db_n.append(parts[0])
            aliases[parts[0]] = parts[1]
        else:
            fields_to_db_n.append(parts[0])
    return fields_to_db_n, aliases


def normalize_arrays(document, array_name):
    document = document[0]
    objects = []
    doc_without_array = copy.deepcopy(document)
    del doc_without_array[array_name]
    array = document.get(array_name)
    if array:
        for array_item in array:
            tmp = copy.deepcopy(doc_without_array)
            tmp.update(array_item)
            objects.append(tmp)

    return objects


def normalize_annotation(
    content: dict,
    accumulator: dict,
    path: dict,
    was_multivalue: bool,
    schema: dict,
    fields_to_db: list,
) -> dict:

    for index, node in enumerate(content):
        if was_multivalue:
            path.append(node["schema_id"] + "[" + str(index) + "]")
        else:
            path.append(node["schema_id"])
        if "schema_id" in node and "children" in node:
            normalize_annotation(
                node["children"],
                accumulator,
                path,
                True if node["category"] == "multivalue" else False,
                schema,
                fields_to_db,
            )
            path.pop()
        else:
            if node["content"]:
                if node["schema_id"] not in fields_to_db:
                    path.pop()
                    continue
                schema_id_def = get_schema_field_by_id(schema, node["schema_id"])
                schema_id_type = (
                    schema_id_def["type"] if schema_id_def["type"] != "enum" else schema_id_def.get("enum_value_type")
                )
                if not schema_id_type:
                    schema_id_type = "string"
                if schema_id_type == "number":
                    try:
                        value = float(node["content"]["normalized_value"])
                    except Exception:
                        try:
                            value = float(node["content"]["value"])
                        except Exception:
                            value = node["content"]["value"]
                else:
                    value = node["content"]["value"]

                groups = re.match(r"(.+)\[(\d+)\]", path[len(path) - 2])
                array_idx = None
                if groups:
                    array_idx = int(groups.group(2))
                if array_idx is not None:
                    array_path = path[len(path) - 3]
                    if accumulator.get(array_path) and len(accumulator[array_path]) - 1 >= array_idx:
                        obj = accumulator[array_path][array_idx]
                        obj[path[-1]] = value
                    else:
                        if accumulator.get(array_path):
                            accumulator[array_path].append({path[-1]: value})
                        else:
                            accumulator[array_path] = []
                            accumulator[array_path].append({path[-1]: value})
                else:
                    accumulator[path[-1]] = value
            path.pop()
    return accumulator


def get_schema_field_by_id(content: dict, schema_id: str) -> str:
    """
    Go over Extraction schema (https://api.elis.rossum.ai/docs/#document-schema) and find the field's definition based on its ID.
    :param dict: content: schema content
    :param str: schema_id: the ID of the field to be found
    :return str: found field or None
    """
    if not isinstance(content, list):
        return get_schema_field_by_id([content], schema_id)

    for datapoint in content:
        if "id" in datapoint and datapoint["id"] == schema_id:
            return datapoint
        else:
            if "children" in datapoint:
                datapoint = get_schema_field_by_id(datapoint["children"], schema_id)
                if datapoint is not None:
                    return datapoint
    return None


def remove_existing_objects(documents, collection_name, natural_key, primary_key, keep_first, token, ds_url):
    for doc in documents:
        filter_cond = {}
        for key in natural_key:
            filter_cond[key] = doc[key]
        if keep_first:
            results = find_in_data_storage_collection(collection_name, filter_cond, token, ds_url, {"created_at": -1})
            if len(results["result"]) > 1:
                oids = []
                # only want to keep the oldest record if the primary key did not change, otherwise replace them all
                oldest_record = results["result"][0]
                for pk in primary_key:
                    if oldest_record.get(pk, "") != doc[pk]:
                        oids.append({"_id": oldest_record["_id"]})
                        break
                # get ids of all records sharing the same natural key except the oldest one
                for res in results["result"][1:]:
                    oids.append({"_id": res["_id"]})
                filter_cond = {"$or": oids}
                delete_many_data_storage_collection(collection_name, filter_cond, token, ds_url)
                return True
            elif len(results["result"]) == 1:
                return True
            return False
        else:
            delete_many_data_storage_collection(collection_name, filter_cond, token, ds_url)
            return False


def create_record_in_ds(messages, payload, document, token, aliases, collection_name, ds_url):
    ts = int(datetime.now().timestamp() * 1000)
    for doc in document:
        doc = replace_aliases(doc, aliases)
        doc["annotation_id"] = payload["annotation"]["id"]
        doc["created_at"] = {"$date": {"$numberLong": ts}}

    response = insert_many_data_storage_collection(collection_name, document, token, ds_url)
    if response.status_code != 200:
        messages.append(
            create_message("warning", "Data storage find endpoint returned an error message: " + response.text, None)
        )
    else:
        messages.append(create_message("info", "Record(s) inserted", None))
    return messages


def insert_many_data_storage_collection(collectionName, document, token, ds_url):
    payload = {"collectionName": collectionName, "documents": document}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    try:
        req = requests.post(f"{ds_url}/data/insert_many", json=payload, headers=headers, timeout=20)
    except Exception as ex:
        return str(ex)

    return req


def delete_many_data_storage_collection(collectionName, document, token, ds_url):
    payload = {"collectionName": collectionName, "filter": document}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    try:
        req = requests.post(f"{ds_url}/data/delete_many", json=payload, headers=headers, timeout=20)
    except Exception as ex:
        return str(ex)

    return req


def find_in_data_storage_collection(collectionName, query, token, ds_url, sort):
    payload = {"collectionName": collectionName, "query": query, "sort": sort}
    header = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    try:
        req = requests.post(f"{ds_url}/data/find", json=payload, headers=header, timeout=20)
    except Exception as ex:
        return str(ex)

    return json.loads(req.text)


def find_by_schema_id(content: dict, schema_id: str) -> tuple:
    """
    Return datapoints matching a schema id.
    :param content: annotation content tree (see https://api.elis.rossum.ai/docs/#annotation-data)
    :param schema_id: field's ID as defined in the extraction schema(see https://api.elis.rossum.ai/docs/#document-schema)
    :param accumulator: list for accumulating values with the same schema_id (f.e. values from same table column)
    :return: the list of datapoints matching the schema ID
    """
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator


def create_replace_operation(datapoint, new_value):
    """
    Create and operation to replace the value of the datapoint with a new value.
    :param datapoint: content of the datapoint
    :param new_value: new value of the datapoint
    :return: dict with replace operation definition (see https://api.elis.rossum.ai/docs/#annotation-content-event-response-format)
    """
    return {
        "op": "replace",
        "id": datapoint["id"],
        "value": {
            "content": {
                "value": new_value,
            }
        },
    }


def find_by_datapoint_id(content, datapoint_id):
    """
    Find specific datapoint by a datapoint ID.
    :param content: annotation content tree (see https://api.elis.rossum.ai/docs/#annotation-data)
    :param datapoint_id: ID of a specific datapoint
    :return: dict representing the found field
    """
    for node in content:
        if node["id"] == datapoint_id:
            return node

        elif "children" in node:
            result = find_by_datapoint_id(node["children"], datapoint_id)

            if result:
                return result
            else:
                continue

    return None


def create_message(message_type, message_content, datapoint_id=None):
    """
    Create a message which will be shown to the user
    :param message_type: type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.
    :param message_content: message shown to the user
    :param datapoint_id: id of the datapoint where the message will appear (None for "global" messages).
    :return: dict with the message definition (see https://api.elis.rossum.ai/docs/#annotation-content-event-response-format)
    """
    return {
        "content": message_content,
        "type": message_type,
        "id": datapoint_id,
    }