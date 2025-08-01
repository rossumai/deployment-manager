import re
from typing import Any, Optional, Tuple

from rossum_api.api_client import Resource

from enum import Enum, auto
from typing import Any, Optional, Tuple


class ReferenceDetectionStatus(Enum):
    DEFINITELY_REFERENCE = auto()
    DEFINITELY_NOT = auto()
    UNKNOWN = auto()


ROSSUM_URL_RE = re.compile(
    r"^https?://(?:[\w-]+\.)*api\.rossum\.ai/(?:api/)?v1/(\w+)/(\d+)$"
)


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
) -> Tuple[ReferenceDetectionStatus, Optional[Resource]]:
    """
    Try to detect if a value is a likely reference to another object and return the referenced type.

    Returns:
        (status: ReferenceDetectionStatus, reference_type: Optional[Resource])
    """
    # 1. Field name gives strong clue
    if field_name in FIELD_TO_RESOURCE:
        return (
            ReferenceDetectionStatus.DEFINITELY_REFERENCE,
            FIELD_TO_RESOURCE[field_name],
        )

    # 2. Detect Rossum-style URL
    if isinstance(value, str) and (match := ROSSUM_URL_RE.match(value)):
        resource_str = match.group(1)
        try:
            resource = Resource(resource_str)
            return ReferenceDetectionStatus.DEFINITELY_REFERENCE, resource
        except ValueError:
            return ReferenceDetectionStatus.DEFINITELY_NOT, None

    # 3. Heuristic: numeric ID-looking value, fallback only
    if type(value) is int or (isinstance(value, str) and value.isdigit()):
        id_val = int(value)
        if 1 <= id_val <= 999_999_999:
            return (
                ReferenceDetectionStatus.UNKNOWN,
                None,
            )  # Might be a reference, might not

    # 4. Primitives or clearly non-reference
    if isinstance(value, (list, dict, bool, float, type(None))):
        return ReferenceDetectionStatus.DEFINITELY_NOT, None

    return ReferenceDetectionStatus.DEFINITELY_NOT, None
