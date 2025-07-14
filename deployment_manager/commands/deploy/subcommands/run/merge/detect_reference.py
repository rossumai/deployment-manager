import re
from typing import Any, Optional, Tuple

from rossum_api.api_client import Resource

# TODO: old US URLs fail with this regex
ROSSUM_URL_RE = re.compile(r"https?://[\w\.-]+/api/v1/(\w+)/\d+")


# Field name hints → known Resource types
FIELD_TO_RESOURCE = {
    "queues": Resource.Queue,
    "run_after": Resource.Hook,
    "schema": Resource.Schema,
    "inbox": Resource.Inbox,
    "webhooks": Resource.Hook,
    "workspace": Resource.Workspace,
    "users": Resource.User,
    "token_owner": Resource.User,
    "hook_template": "hook_templates",
    "organization": Resource.Organization,
}


def detect_reference_with_type(
    value: Any, field_name: str = ""
) -> Tuple[bool, Optional[Resource]]:
    """
    Try to detect if a value is a likely reference to another object and return the referenced type.

    Returns:
        (is_reference: bool, reference_type: Optional[Resource])
    """
    # 1. Field name gives strong clue
    if field_name in FIELD_TO_RESOURCE:
        return True, FIELD_TO_RESOURCE[field_name]

    # 2. Detect Rossum-style URL
    if isinstance(value, str):
        match = ROSSUM_URL_RE.match(value)
        if match:
            resource_str = match.group(1)
            try:
                resource = Resource(resource_str)
                return True, resource
            except ValueError:
                pass  # Unrecognized type

    # 3. Heuristic: ID-looking value — fallback only if field name implies nothing
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        id_val = int(value)
        if 1 <= id_val <= 999_999_999:
            return True, None  # Can't infer type from ID alone

    return False, None
