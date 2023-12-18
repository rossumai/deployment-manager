import json
import requests

class RossumClient:
    def __init__(self, authorization_token: str, base_url: str, api_version: str) -> None:
        self.token = authorization_token
        self.api_url = f"{base_url}/{api_version}"

    def get(self, object_name: str, object_id: str | int | None) -> dict | list[dict]:
        object_id = str(object_id) if object_id else None
        endpoint_suffix = f"/{object_name}/{object_id}" if object_id else f"/{object_name}"
        response = requests.get(self.api_url + endpoint_suffix, headers={"Authorization" : f"Bearer {self.token}"})
        return self._process_response(response)
        

    def post(self, object_name: str, object_id: str | int, body: dict) -> dict | list[dict]:
        object_id = str(object_id) if object_id else None
        endpoint_suffix = f"/{object_name}/{object_id}" if object_id else f"/{object_name}"
        response = requests.post(self.api_url + endpoint_suffix, headers={"Authorization" : f"Bearer {self.token}"}, json=body)
        return self._process_response(response)

    def post(self, object_name: str, object_id: str | int, body: dict) -> dict | list[dict]:
        object_id = str(object_id) if object_id else None
        endpoint_suffix = f"/{object_name}/{object_id}" if object_id else f"/{object_name}"
        response = requests.patch(self.api_url + endpoint_suffix, headers={"Authorization" : f"Bearer {self.token}"}, json=body)
        return self._process_response(response)

    def _process_response(self, response: requests.Response) -> dict | list[dict]:
        if response.status_code == 200:
            return response.json()
        else:
            raise MessageException("error", response.text)


class MessageException(Exception):
    """
    Exception raised when a message should be displayed to the user (e.g. missing field in schema).
    """

    def __init__(self, message_type: str, message_content: str):
        """
        :param message_type: type of the message - info, warning or error
        :param message_content: content of the message
        :param datapoint_id: id of the datapoint to which the message relates (None for "global" messages)
        """
        self.message_type = message_type
        self.message_content = message_content

        
def auth(base_url: str, api_version: str, username: str, password: str) -> dict:
    body = {"username": username, "password": password}
    response = requests.post(f"{base_url}/{api_version}/auth/login", json=body)
    if response.status_code == 200:
        return response.json()
    else:
        raise MessageException("error", response.text)