from txscript import TxScript, default_to, substitute, is_empty
from rossum.lib.api_client import RossumClient, RossumException

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)
    rossum_client = get_rossum_client(payload)

    confirmed_by_url = payload['annotation'].get('exported_by', "")
    if not confirmed_by_url:
        return t.hook_response()
    
    confirmed_by_id = confirmed_by_url.split("/")[-1]
    
    try:
        user = rossum_client.get_user(confirmed_by_id)
        t.field.confirmed_by = user.get('email', "unknown")
    except Exception as e:
        print(e)
        t.field.confirmed_by = "unknown"

    return t.hook_response()
    
def get_rossum_client(payload: dict) -> RossumClient:
    rossum_client = RossumClient(None, payload["base_url"] + "/api/v1")
    rossum_client.token = get_auth_token_from_payload(payload)
    return rossum_client


def get_auth_token_from_payload(payload: dict) -> str:
    auth_token = payload.get("rossum_authorization_token")
    if not auth_token:
        raise HookConfigurationError(
            f"Authorization token not found in the payload. Configure Rossum API access at {payload['hook']}."
        )
    return auth_token