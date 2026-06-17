"""In-memory Rossum-like API for integration tests.

Rather than mock `AsyncRossumAPIClient` piecewise everywhere, we implement a
small data store + adapter with just the methods PRD2 actually calls:

- client._http_client.base_url / token
- client._http_client.fetch_all(Resource)  -> async generator of dicts
- client._http_client.fetch_all_by_url(url) -> async generator of dicts
- client._http_client.fetch_one(Resource, id) -> dict
- client._http_client.create(Resource, data) -> dict
- client._http_client.update(Resource, id, data) -> dict
- client._http_client.delete(Resource, id)
- client._http_client.request_json(method, url, json=...)
- client.retrieve_organization(id) -> Organization dataclass
- client.retrieve_queue(id) -> Queue dataclass
- client.retrieve_user(id) -> User dataclass
- client.retrieve_hook(id) -> Hook dataclass
- client.list_organizations() -> async iterator of Organization
"""

from __future__ import annotations

import copy
from dataclasses import fields
from datetime import datetime, timezone

from rossum_api import APIClientError, AsyncRossumAPIClient
from rossum_api.domain_logic.resources import Resource
from rossum_api.models.hook import Hook
from rossum_api.models.inbox import Inbox
from rossum_api.models.organization import Organization
from rossum_api.models.queue import Queue
from rossum_api.models.schema import Schema
from rossum_api.models.user import User
from rossum_api.models.workspace import Workspace


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "") + "Z"


def _resource_value(resource) -> str:
    """Get the string key we store under (works for Resource and CustomResource)."""
    return resource.value if hasattr(resource, "value") else str(resource)


class VirtualRossumOrg:
    """An in-memory simulated Rossum organization.

    Holds per-type dicts keyed by object id. Methods construct canonical Rossum-style
    URLs and auto-assign IDs for objects that don't specify one.
    """

    def __init__(self, org_id: int, name: str, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._next_id = 10_000_000
        self._stores: dict[str, dict[int, dict]] = {
            _resource_value(Resource.Organization): {},
            _resource_value(Resource.Workspace): {},
            _resource_value(Resource.Queue): {},
            _resource_value(Resource.Schema): {},
            _resource_value(Resource.Hook): {},
            _resource_value(Resource.Inbox): {},
            _resource_value(Resource.EmailTemplate): {},
            _resource_value(Resource.Engine): {},
            _resource_value(Resource.EngineField): {},
            _resource_value(Resource.Rule): {},
            _resource_value(Resource.User): {},
            "labels": {},
            "workflows": {},
            "workflow_steps": {},
            "hook_templates": {},
        }
        # Seed the organization itself
        self._stores[_resource_value(Resource.Organization)][org_id] = {
            "id": org_id,
            "name": name,
            "url": self._build_url(Resource.Organization, org_id),
            "workspaces": [],
            "users": [],
            "organization_group": f"{self.base_url}/organization_groups/1",
            "is_trial": False,
            "created_at": _iso_now(),
            "trial_expires_at": None,
            "ui_settings": {},
            "metadata": {},
        }
        self.org_id = org_id

    def _alloc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _build_url(self, resource, id_: int) -> str:
        return f"{self.base_url}/{_resource_value(resource)}/{id_}"

    def _store(self, resource) -> dict[int, dict]:
        key = _resource_value(resource)
        if key not in self._stores:
            self._stores[key] = {}
        return self._stores[key]

    def add_user(self, username: str = "tester", id_: int | None = None) -> dict:
        if id_ is None:
            id_ = self._alloc_id()
        user = {
            "id": id_,
            "username": username,
            "email": f"{username}@example.com",
            "url": self._build_url(Resource.User, id_),
            "organization": self._build_url(Resource.Organization, self.org_id),
            "queues": [],
            "groups": [],
            "first_name": "",
            "last_name": "",
            "last_login": _iso_now(),
            "ui_settings": {},
            "date_joined": _iso_now(),
            "metadata": {},
            "is_active": True,
            "oidc_id": None,
            "auth_type": "password",
        }
        self._store(Resource.User)[id_] = user
        self._stores[_resource_value(Resource.Organization)][self.org_id]["users"].append(user["url"])
        return user

    def add_workspace(self, name: str, id_: int | None = None, **extra) -> dict:
        if id_ is None:
            id_ = self._alloc_id()
        ws = {
            "id": id_,
            "name": name,
            "url": self._build_url(Resource.Workspace, id_),
            "organization": self._build_url(Resource.Organization, self.org_id),
            "queues": [],
            "metadata": {},
            "autopilot": True,
            "modified_at": _iso_now(),
        }
        ws.update(extra)
        self._store(Resource.Workspace)[id_] = ws
        self._stores[_resource_value(Resource.Organization)][self.org_id]["workspaces"].append(ws["url"])
        return ws

    def add_schema(self, name: str, content: list | None = None, id_: int | None = None, **extra) -> dict:
        if id_ is None:
            id_ = self._alloc_id()
        schema = {
            "id": id_,
            "name": name,
            "url": self._build_url(Resource.Schema, id_),
            "queues": [],
            "content": content if content is not None else [],
            "metadata": {},
            "rules": [],
            "modified_at": _iso_now(),
        }
        schema.update(extra)
        self._store(Resource.Schema)[id_] = schema
        return schema

    def add_inbox(
        self,
        name: str,
        queue_id: int,
        email: str | None = None,
        id_: int | None = None,
        **extra,
    ) -> dict:
        if id_ is None:
            id_ = self._alloc_id()
        inbox = {
            "id": id_,
            "name": name,
            "url": self._build_url(Resource.Inbox, id_),
            "queues": [self._build_url(Resource.Queue, queue_id)],
            "email": email or f"inbox-{id_}@example.com",
            "email_prefix": f"inbox-{id_}",
            "bounce_email_to": None,
            "bounce_unprocessable_attachments": False,
            "bounce_deleted_annotations": False,
            "bounce_postponed_annotations": False,
            "bounce_email_with_no_attachments": False,
            "dmarc_check_action": "accept",
            "filters": {},
            "metadata": {},
            "modified_at": _iso_now(),
        }
        inbox.update(extra)
        self._store(Resource.Inbox)[id_] = inbox
        return inbox

    def add_queue(
        self,
        name: str,
        workspace_id: int,
        schema_id: int,
        hooks: list[int] | None = None,
        id_: int | None = None,
        add_inbox: bool = True,
        **extra,
    ) -> dict:
        if id_ is None:
            id_ = self._alloc_id()

        hook_urls = [self._build_url(Resource.Hook, h) for h in (hooks or [])]

        queue = {
            "id": id_,
            "name": name,
            "url": self._build_url(Resource.Queue, id_),
            "workspace": self._build_url(Resource.Workspace, workspace_id),
            "schema": self._build_url(Resource.Schema, schema_id),
            "inbox": None,
            "connector": None,
            "hooks": hook_urls,
            "webhooks": [],
            "session_timeout": "01:00:00",
            "rir_url": None,
            "rir_params": None,
            "default_score_threshold": 0.975,
            "automation_enabled": False,
            "automation_level": "never",
            "locale": "en_US",
            "metadata": {},
            "settings": {"columns": [], "hide_export_button": False},
            "use_confirmed_state": True,
            "document_lifetime": None,
            "dedicated_engine": None,
            "generic_engine": None,
            "delete_after": None,
            "status": "active",
            "workflows": [],
            "modified_by": None,
            "modified_at": _iso_now(),
            "engine": None,
            "training_enabled": True,
            "archive_enabled": False,
            "counts": {},
            "users": [],
            "rules": [],
        }
        queue.update(extra)
        self._store(Resource.Queue)[id_] = queue

        # Link workspace -> queue
        ws = self._store(Resource.Workspace).get(workspace_id)
        if ws:
            ws["queues"].append(queue["url"])

        # Link schema -> queue
        schema = self._store(Resource.Schema).get(schema_id)
        if schema:
            schema["queues"].append(queue["url"])

        # Link hooks -> queue
        for hook_id in hooks or []:
            hook = self._store(Resource.Hook).get(hook_id)
            if hook:
                hook["queues"].append(queue["url"])

        if add_inbox:
            inbox = self.add_inbox(name=f"{name} inbox", queue_id=id_)
            queue["inbox"] = inbox["url"]

        return queue

    def add_hook(
        self,
        name: str,
        queues: list[int] | None = None,
        run_after: list[int] | None = None,
        code: str | None = None,
        runtime: str = "python3.8",
        id_: int | None = None,
        extension_source: str = "custom",
        hook_type: str = "function",
        **extra,
    ) -> dict:
        if id_ is None:
            id_ = self._alloc_id()
        hook = {
            "id": id_,
            "name": name,
            "url": self._build_url(Resource.Hook, id_),
            "type": hook_type,
            "events": ["annotation_content.user_update"],
            "active": True,
            "queues": [self._build_url(Resource.Queue, q) for q in (queues or [])],
            "run_after": [self._build_url(Resource.Hook, h) for h in (run_after or [])],
            "config": {
                "code": code if code is not None else "def rossum_hook_request_handler(payload):\n    return {}\n",
                "runtime": runtime,
            },
            "extension_source": extension_source,
            "secrets": {},
            "sideload": [],
            "token_owner": None,
            "guide": "",
            "metadata": {},
            "modified_at": _iso_now(),
            "status": "active",
            # Required by Hook dataclass
            "test": {},
            "read_more_url": "",
            "extension_image_url": "",
        }
        hook.update(extra)
        self._store(Resource.Hook)[id_] = hook
        return hook


class _VirtualHttpClient:
    def __init__(self, org: VirtualRossumOrg, token: str = "fake-token"):
        self.org = org
        self.token = token

    @property
    def base_url(self) -> str:
        return self.org.base_url

    async def fetch_all(self, resource, **kwargs):
        store = self.org._store(resource)
        for obj in list(store.values()):
            yield copy.deepcopy(obj)

    async def fetch_all_by_url(self, url: str, **kwargs):
        # Last path component is the resource name
        key = url.rstrip("/").split("/")[-1]
        store = self.org._stores.get(key, {})
        for obj in list(store.values()):
            yield copy.deepcopy(obj)

    async def fetch_one(self, resource, id_):
        store = self.org._store(resource)
        if int(id_) not in store:
            raise APIClientError("GET", f"/{_resource_value(resource)}/{id_}", 404, "Not found")
        return copy.deepcopy(store[int(id_)])

    async def create(self, resource, data: dict):
        new_id = self.org._alloc_id()
        new_obj = copy.deepcopy(data)
        new_obj["id"] = new_id
        new_obj["url"] = self.org._build_url(resource, new_id)
        new_obj["modified_at"] = _iso_now()
        self.org._store(resource)[new_id] = new_obj
        return copy.deepcopy(new_obj)

    async def update(self, resource, id_, data: dict):
        store = self.org._store(resource)
        if int(id_) not in store:
            raise APIClientError("PUT", f"/{_resource_value(resource)}/{id_}", 404, "Not found")
        existing = store[int(id_)]
        updated = {**existing, **data}
        updated["id"] = int(id_)
        updated["url"] = existing.get("url", self.org._build_url(resource, int(id_)))
        updated["modified_at"] = _iso_now()
        store[int(id_)] = updated
        return copy.deepcopy(updated)

    async def delete(self, resource, id_=None, **kwargs):
        store = self.org._store(resource)
        if int(id_) in store:
            del store[int(id_)]

    async def _request(self, method: str, url: str, **kwargs):
        # Minimal path-based routing used by deploy queue deletion etc.
        parts = url.strip("/").split("/")
        if len(parts) >= 2:
            resource_key, id_ = parts[0], parts[1]
            store = self.org._stores.get(resource_key, {})
            if method.upper() == "DELETE" and int(id_) in store:
                del store[int(id_)]
        return None

    async def request_json(self, method: str, url: str, json: dict | None = None, **kwargs):
        # Support hook creation via `hooks/create` and arbitrary GETs by URL
        parts = url.strip("/").split("/")

        if method.upper() == "POST" and url.strip("/") == "hooks/create":
            return await self.create(Resource.Hook, json or {})

        if method.upper() == "GET" and parts[0] in self.org._stores:
            resource_key = parts[0]
            id_ = int(parts[1])
            store = self.org._stores[resource_key]
            if id_ in store:
                return copy.deepcopy(store[id_])
            raise APIClientError("GET", url, 404, "Not found")

        # Absolute URLs
        if url.startswith("http"):
            for key, store in self.org._stores.items():
                prefix = f"{self.org.base_url}/{key}/"
                if url.startswith(prefix):
                    id_ = int(url[len(prefix) :].rstrip("/"))
                    if id_ in store:
                        return copy.deepcopy(store[id_])

        raise APIClientError(method, url, 404, "Not found")


def _dataclass_from_dict(cls, data: dict):
    """Build a dataclass instance from a dict, keeping only known fields."""
    valid = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in valid})


class VirtualRossumClient(AsyncRossumAPIClient):
    """Minimal AsyncRossumAPIClient-compatible object.

    Inherits from the real client so pydantic `isinstance` checks accept it;
    overrides the methods PRD2 actually calls to hit our in-memory store.
    """

    _RESOURCE_TO_DATACLASS: dict = {
        Resource.Organization: Organization,
        Resource.Workspace: Workspace,
        Resource.Queue: Queue,
        Resource.Schema: Schema,
        Resource.Hook: Hook,
        Resource.Inbox: Inbox,
        Resource.User: User,
    }

    def __init__(self, org: VirtualRossumOrg):
        # Skip super().__init__() entirely — we don't want the real HTTP client.
        self.org = org
        self._http_client = _VirtualHttpClient(org)
        self._deserializer = self._deserialize

    def _deserialize(self, resource, obj):
        cls = self._RESOURCE_TO_DATACLASS.get(resource)
        if cls is None:
            return obj
        return _dataclass_from_dict(cls, obj)

    # High-level convenience methods — PRD2 uses these sparingly
    async def list_organizations(self):
        for org in self.org._store(Resource.Organization).values():
            yield _dataclass_from_dict(Organization, copy.deepcopy(org))

    async def retrieve_organization(self, id_):
        store = self.org._store(Resource.Organization)
        if int(id_) not in store:
            raise APIClientError("GET", f"/organizations/{id_}", 404, "Not found")
        return _dataclass_from_dict(Organization, copy.deepcopy(store[int(id_)]))

    async def retrieve_user(self, id_):
        store = self.org._store(Resource.User)
        if int(id_) not in store:
            raise APIClientError("GET", f"/users/{id_}", 404, "Not found")
        return _dataclass_from_dict(User, copy.deepcopy(store[int(id_)]))

    async def retrieve_queue(self, id_):
        store = self.org._store(Resource.Queue)
        if int(id_) not in store:
            raise APIClientError("GET", f"/queues/{id_}", 404, "Not found")
        return _dataclass_from_dict(Queue, copy.deepcopy(store[int(id_)]))

    async def retrieve_hook(self, id_):
        store = self.org._store(Resource.Hook)
        if int(id_) not in store:
            raise APIClientError("GET", f"/hooks/{id_}", 404, "Not found")
        return _dataclass_from_dict(Hook, copy.deepcopy(store[int(id_)]))

    async def retrieve_schema(self, id_):
        store = self.org._store(Resource.Schema)
        if int(id_) not in store:
            raise APIClientError("GET", f"/schemas/{id_}", 404, "Not found")
        return _dataclass_from_dict(Schema, copy.deepcopy(store[int(id_)]))

    async def retrieve_workspace(self, id_):
        store = self.org._store(Resource.Workspace)
        if int(id_) not in store:
            raise APIClientError("GET", f"/workspaces/{id_}", 404, "Not found")
        return _dataclass_from_dict(Workspace, copy.deepcopy(store[int(id_)]))

    async def delete_workspace(self, id_):
        self.org._store(Resource.Workspace).pop(int(id_), None)

    async def delete_schema(self, id_):
        self.org._store(Resource.Schema).pop(int(id_), None)

    async def list_workspaces(self):
        for ws in self.org._store(Resource.Workspace).values():
            yield _dataclass_from_dict(Workspace, copy.deepcopy(ws))

    async def list_queues(self):
        for q in self.org._store(Resource.Queue).values():
            yield _dataclass_from_dict(Queue, copy.deepcopy(q))

    async def list_hooks(self):
        for h in self.org._store(Resource.Hook).values():
            yield _dataclass_from_dict(Hook, copy.deepcopy(h))

    async def list_schemas(self):
        for s in self.org._store(Resource.Schema).values():
            yield _dataclass_from_dict(Schema, copy.deepcopy(s))


def build_simple_org(org_id: int = 100, name: str = "virtual-org", base_url: str = "https://virt.rossum.app/api/v1") -> VirtualRossumOrg:
    """Common starting point: one WS, one Queue (with schema+inbox), one Hook."""
    org = VirtualRossumOrg(org_id=org_id, name=name, base_url=base_url)
    org.add_user(username="tester")

    ws = org.add_workspace(name="WS1", id_=500001)
    schema = org.add_schema(
        name="Schema1",
        id_=500002,
        content=[
            {
                "category": "section",
                "id": "basic_info",
                "children": [
                    {
                        "category": "datapoint",
                        "id": "invoice_id",
                        "label": "Invoice ID",
                        "type": "string",
                    }
                ],
            }
        ],
    )
    hook = org.add_hook(name="MyHook", id_=500003, code="def rossum_hook_request_handler(payload):\n    return {}\n")
    org.add_queue(
        name="Q1",
        id_=500004,
        workspace_id=ws["id"],
        schema_id=schema["id"],
        hooks=[hook["id"]],
    )
    return org


def build_empty_target_org(
    org_id: int = 200,
    name: str = "target-org",
    base_url: str = "https://tgt.rossum.app/api/v1",
) -> VirtualRossumOrg:
    """Target org that has only its organization+user record, nothing else."""
    org = VirtualRossumOrg(org_id=org_id, name=name, base_url=base_url)
    org.add_user(username="target-tester")
    return org


__all__ = [
    "VirtualRossumClient",
    "VirtualRossumOrg",
    "build_empty_target_org",
    "build_simple_org",
]
