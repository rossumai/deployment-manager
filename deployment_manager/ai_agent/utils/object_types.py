TYPE_ALIASES: dict[str, str] = {
    "workspace": "workspaces",
    "workspaces": "workspaces",
    "queue": "queues",
    "queues": "queues",
    "schema": "schemas",
    "schemas": "schemas",
    "inbox": "inboxes",
    "inboxes": "inboxes",
    "hook": "hooks",
    "hooks": "hooks",
    "rule": "rules",
    "rules": "rules",
    "engine": "engines",
    "engines": "engines",
    "label": "labels",
    "labels": "labels",
    "email_template": "email_templates",
    "email_templates": "email_templates",
}


def normalize_object_type(obj_type: str) -> str | None:
    return TYPE_ALIASES.get(obj_type.lower())
