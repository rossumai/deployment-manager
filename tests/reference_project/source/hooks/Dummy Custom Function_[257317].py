"""
This example function does 2 things:
1. Displays a warning message to the user for all the "item_amount_total" fields which exceed the predefined threshold
2. Removes all dashes from the "document_id" field

More about custom functions - https://developers.rossum.ai/docs/how-to-use-serverless-functions
"""


def rossum_hook_request_handler(payload: dict) -> dict:
    """
    Obligatory main function
    :param payload: differs for each event, see https://rdttest.rossum.app/api/docs/#webhook-events
    :return: dictionary with messages to the user and operations that update the annotation content
    """
    messages = []
    operations = []

    # Annotation content tree (see https://rdttest.rossum.app/api/docs/#annotation-data)
    content: list = payload["annotation"]["content"]

    # Values over the threshold trigger a warning message
    TOO_BIG_THRESHOLD = 1000000

    # List of all datapoints with item_amount_total schema id
    amount_total_column_datapoints: list = find_by_schema_id(
        content, "item_amount_total"
    )

    # Display warning message for all the "item_amount_total" fields exceeding the threshold
    for amount_total_column_datapoint in amount_total_column_datapoints:
        # Use normalized_value for comparing values of Date and Number fields
        value = float(amount_total_column_datapoint["content"]["normalized_value"] or 0)
        if value >= TOO_BIG_THRESHOLD:
            messages.append(
                create_message(
                    "warning", "Value is too big", amount_total_column_datapoint["id"]
                )
            )

    # There should be only one "document_id" datapoint
    document_id_datapoint: dict = find_by_schema_id(content, "document_id")[0]

    # Remove dashes from the "document_id" field
    document_id: str = document_id_datapoint["content"]["value"]
    operations.append(
        create_replace_operation(
            document_id_datapoint["id"], document_id.replace("-", "")
        )
    )

    return {"messages": messages, "operations": operations}


# --- HELPER FUNCTIONS ---


def find_by_schema_id(content: list, schema_id: str) -> list:
    """
    Return all datapoints matching a schema id.
    :param content: annotation content tree (see https://rdttest.rossum.app/api/docs/#content-object)
    :param schema_id: field's ID as defined in the extraction schema (see https://rdttest.rossum.app/api/docs/#document-schema)
    :return: list of datapoints matching the schema ID
    """
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator


def create_message(
    message_type: str, message_content: str, datapoint_id: int = None
) -> dict:
    """
    Create a message which will be shown to the user
    :param message_type: type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.
    :param message_content: message shown to the user
    :param datapoint_id: id of the datapoint where the message will appear (None for "global" messages).
    :return: dict with the message definition (see https://rdttest.rossum.app/api/docs/#annotation-content-event-response-format)
    """
    return {
        "content": message_content,
        "type": message_type,
        "id": datapoint_id,
    }


def create_replace_operation(datapoint_id: int, new_value: str) -> dict:
    """
    Replace the value of the datapoint with a new value.
    :param datapoint_id: id of the datapoint to be changed
    :param new_value: new value of the datapoint
    :return: dict with replace operation definition (see https://rdttest.rossum.app/api/docs/#annotation-content-event-response-format)
    """
    return {
        "op": "replace",
        "id": datapoint_id,
        "value": {
            "content": {
                "value": new_value,
            },
        },
    }
