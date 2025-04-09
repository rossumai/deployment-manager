import json
import re
import requests
import time
from requests.exceptions import RequestException
from pydantic import BaseModel, ValidationError, confloat
from txscript import TxScript, is_empty


def rossum_hook_request_handler(payload: dict) -> dict:
    """
    Handles incoming payloads for Rossum hook requests and processes them
    based on the given configurations, updated datapoints, and other settings.

    :param payload: Dictionary containing request payload data.
    :return: Dictionary response to be returned to the hook.
    """
    t = TxScript.from_payload(payload)

    token = payload.get("rossum_authorization_token", "")
    if not token:
        t.show_error("Please set a token owner for the extension.")
        return t.hook_response()

    base_url = payload.get("base_url")
    headers = {"Authorization": f"Bearer {token}"}

    settings = payload.get("settings", {})
    action = payload.get("action", "")
    updated_datapoints = payload.get("updated_datapoints", [])

    try:
        config = Configuration(**settings)

        if not check_condition(t, config.condition):
            return t.hook_response()

        if action == "updated":
            if not check_for_updates(t, config.input, updated_datapoints):
                return t.hook_response()

        content = ContentHandler(t, config.input)

        generator = ResponseGenerator(t, content.extracted_data, config.temperature)
        response = generator.send_request(base_url, headers)

        content.update_datapoints(response, config.output)

    except ValidationError as e:
        t.show_error(format_validation_errors(e.errors()))
    except Exception as e:
        t.show_error(str(e))

    return t.hook_response()


class Configuration(BaseModel):
    """
    Represents the configuration for processing a hook request.

    Attributes:
        input (dict[str, str]): Mapping of input fields to process.
        output  str: output schema_id
        temperature (float): Temperature for response generation (0.0 to 1.0).
        condition (str): Condition to evaluate before processing the configuration.
    """

    input: dict[str, str]
    output: str
    temperature: confloat(ge=0.0, le=1.0) = 0.0
    condition: str = ""


class ContentHandler:
    """
    Handles the extraction and updating of content based on the input mapping.

    Attributes:
        t (TxScript): TxScript object.
        extracted_data (dict): Extracted data from input mapping.
    """

    def __init__(self, t: TxScript, input_map: dict[str, str]):
        """
        Initializes the content handler with the transaction script and input mapping.

        :param t: Transaction script object.
        :param input_map: Mapping of input fields to extract.
        """
        self.t = t
        self.extracted_data = self._gather_field_values(input_map)

    def _gather_field_values(self, input_map: dict[str, str]) -> dict:
        """
        Gathers values for the specified input fields.

        :param input_map: Mapping of input field descriptors to field IDs.
        :return: Dictionary of gathered field values.
        """
        results = {}
        for descriptor, field_id in input_map.items():
            if not hasattr(self.t.field, field_id):
                raise ValueError(f"Field '{field_id}' not found.")
            value = getattr(self.t.field, field_id).value
            results[descriptor] = value
        return results

    def update_datapoints(self, response_data: dict, target_field: str):
        """
        Updates datapoints with the response data.

        :param response_data: Dictionary containing response data to update fields.
        :raises ValueError: If response format is invalid or target fields are not found.
        """
        try:
            content = response_data["messages"][1]["content"]
            json_match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
            if not json_match:
                raise KeyError("No JSON in LLM's response")
            json_data = json_match.group(0)

            if hasattr(self.t.field, target_field):
                setattr(self.t.field, target_field, json_data)
            # parsed_response = json.loads(json_data)

            # for item in parsed_response:
            #     target_field = item["field"]
            #     new_value = item["response"]

            #     if hasattr(self.t.field, target_field):
            #         setattr(self.t.field, target_field, new_value)
            #     else:
            #         raise ValueError(f"Target field '{target_field}' not found.")

        except (KeyError, IndexError) as parse_error:
            raise ValueError(f"Invalid response format: {parse_error}")


class ResponseGenerator:
    """
    Generates and sends requests to the LLM for processing input data.

    Attributes:
        t (TxScript): TxScript object.
        input_data (dict): Data to be processed.
        output_schema (list): Schema for the desired output.
        temperature (float): Temperature for response generation.
        prompt (str): Generated prompt for the LLM.
    """

    def __init__(self, t: TxScript, input_data: dict, temperature: float):
        """
        Initializes the response generator with input data, output schema, and temperature.

        :param t: Transaction script object.
        :param input_data: Input data for processing.
        :param output_schema: Desired output schema.
        :param temperature: Temperature for the LLM request.
        """
        self.t = t
        self.input_data = input_data
        # self.output_schema = output_schema
        self.temperature = temperature
        self.prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        """
        Builds the prompt for the LLM request.

        :return: Prompt string for the LLM.
        """
        return (
            f"Given the input payment terms text:\n{json.dumps(self.input_data, indent=2)}\n\n"
            """Given the input payment terms text: <input>{input_text}</input>

Parse out the following values from the payment terms text. Return the result as a JSON object with these keys:
- Days_to_Pay_Net: Number of days to pay the net amount (integer or 0)
- Days_to_Discount: Number of days to get discount (integer or 0)
- Day_of_Month_to_Net: Day of month when net payment is due (integer or 0)
- Day_of_Month_to_Discount: Day of month when discount payment is due (integer or 0)
- Net_Beginning_Month_C_N: Whether net payment is from Current or Next month (C, N) - write C if not mentioned
- Discount_Beginning_Month_C_N: Whether discount is from Current or Next month (C, N) - write C if not mentioned
- Discount_%: Discount percentage as decimal (float or 0)

Return ONLY the JSON object, nothing else.

Examples:
* "30 days Due net" -> {{'Days_to_Pay_Net': 30, 'Days_to_Discount': 0, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 0, 'Net_Beginning_Month_C_N': 'C', 'Discount_Beginning_Month_C_N': 'C', 'Discount_%': 0}}
* "within 60 days 3 % cash discount within 61 days Due net" -> {{'Days_to_Pay_Net': 60, 'Days_to_Discount': 61, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 0, 'Net_Beginning_Month_C_N': 'C', 'Discount_Beginning_Month_C_N': 'C', 'Discount_%': 0.03}}
* "1% 10, NET 31" -> {{'Days_to_Pay_Net': 31, 'Days_to_Discount': 10, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 0, 'Net_Beginning_Month_C_N': 'C', 'Discount_Beginning_Month_C_N': 'C', 'Discount_%': 0.01}}
* "4% 10th day net 30" -> {{'Days_to_Pay_Net': 30, 'Days_to_Discount': 0, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 10, 'Net_Beginning_Month_C_N': ‘C’, 'Discount_Beginning_Month_C_N': ‘C’, 'Discount_%': 0.04}}
* “1-30 Net 60” -> {{'Days_to_Pay_Net': 60, 'Days_to_Discount': 30, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 0, 'Net_Beginning_Month_C_N': ‘C’, 'Discount_Beginning_Month_C_N': ‘C’, 'Discount_%': 0.01}}
* “within 30 days 2 % cash discount within 31 days Due net” -> {{'Days_to_Pay_Net': 31, 'Days_to_Discount': 30, 'Day_of_Month_to_Net': 0, 'Day_of_Month_to_Discount': 0, 'Net_Beginning_Month_C_N': ‘C’, 'Discount_Beginning_Month_C_N': ‘C’, 'Discount_%': 0.02}}
"""
        )

    def send_request(self, base_url: str, headers: dict, retries: int = 5) -> dict:
        """
        Sends a request to the LLM endpoint with retry logic.

        :param base_url: Base URL of the API.
        :param headers: Headers for the API request.
        :param retries: Number of retry attempts.
        :return: JSON response from the LLM.
        :raises RuntimeError: If all retry attempts fail.
        """
        endpoint = f"{base_url}/api/v1/internal/llmchat"
        body = {
            "messages": [{"role": "user", "content": self.prompt}],
            "temperature": self.temperature,
        }
        for attempt in range(retries):
            try:
                response = requests.post(endpoint, headers=headers, json=body)
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self.t.show_error(f"Request exception encountered: {e}")
                if attempt < retries - 1:
                    time.sleep(2**attempt)
        raise RuntimeError("Exceeded maximum retry attempts for the LLM request.")


def format_validation_errors(errors: list[dict]) -> str:
    """
    Formats validation errors into a readable string.

    :param errors: List of validation error dictionaries.
    :return: Formatted error string.
    """
    messages = []
    for err in errors:
        field_name = ".".join(str(loc) for loc in err.get("loc", []))
        error_msg = err.get("msg", "Invalid value")
        messages.append(f"{field_name}: {error_msg}")
    return "Validation Error(s):\n" + "\n".join(messages)


def check_for_updates(
    t: TxScript, input_map: dict[str, str], updated_datapoints: list[str]
) -> bool:
    """
    Checks if any of the input fields have been updated.

    :param t: TxScript object.
    :param input_map: Mapping of input fields to check.
    :param updated_datapoints: List of updated datapoints.
    :return: True if any input fields are updated, False otherwise.
    """
    for field in input_map.values():
        field_id = getattr(t.field, field).attr.id
        if field_id in updated_datapoints:
            return True
    return False


def check_condition(t: TxScript, condition: str) -> bool:
    """
    Evaluates a condition string.

    :param t: TxScript object.
    :param condition: Condition string to evaluate.
    :return: True if the condition is met, False otherwise.
    :raises ValueError: If the condition contains an invalid field.
    """
    if not condition:
        return True

    try:
        if "==" in condition:
            field, value_expected = map(str.strip, condition.split("=="))
            value_expected = value_expected.strip("'\"")
            actual_value = getattr(t.field, field.strip("{}")).value
            return str(actual_value) == str(value_expected)
        elif "!=" in condition:
            field, value_expected = map(str.strip, condition.split("!="))
            value_expected = value_expected.strip("'\"")
            actual_value = getattr(t.field, field.strip("{}")).value
            return str(actual_value) != str(value_expected)
        else:
            field = condition.strip("{}")
            val = getattr(t.field, field).value
            return not is_empty(val)
    except AttributeError:
        raise ValueError(f"Invalid field in condition: {condition}")