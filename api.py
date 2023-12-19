from rossum_client import RossumClient

def get_organizations(client: RossumClient):
    objects = client.get("organizations", None)
    return objects

def get_workspaces(client: RossumClient):
    objects = client.get("workspaces", None)
    return objects

def get_queues(client: RossumClient):
    objects = client.get("queues", None)
    return objects

def get_schemas(client: RossumClient):
    objects = client.get("schemas", None)
    return objects

def get_users(client: RossumClient):
    objects = client.get("users", None)
    return objects

def get_hooks(client: RossumClient):
    objects = client.get("hooks", None)
    return objects

def get_organization(client: RossumClient, id: str | int):
    object = client.get(f"organizations", id)
    return object

def get_workspace(client: RossumClient, id: str | int):
    object = client.get(f"workspaces", id)
    return object

def get_queue(client: RossumClient, id: str | int):
    object = client.get(f"queues", id)
    return object

def get_schema(client: RossumClient, id: str | int):
    object = client.get(f"schemas", id)
    return object

def get_user(client: RossumClient, id: str | int):
    object = client.get(f"users", id)
    return object

def get_hook(client: RossumClient, id: str | int):
    object = client.get(f"hooks", id)
    return object

def create_organization(client: RossumClient, body: dict):
    object = client.post(f"organizations")
    return object

def create_workspace(client: RossumClient, body: dict):
    object = client.post(f"workspaces")
    return object

def create_queue(client: RossumClient, body: dict):
    object = client.post(f"queues")
    return object

def create_schema(client: RossumClient, body: dict):
    object = client.post(f"schemas")
    return object

def create_user(client: RossumClient, body: dict):
    object = client.post(f"users")
    return object

def create_hook(client: RossumClient, body: dict):
    object = client.post(f"hooks")
    return object

def update_organization(client: RossumClient, body: dict):
    object = client.patch(f"organizations")
    return object

def update_workspace(client: RossumClient, body: dict):
    object = client.patch(f"workspaces")
    return object

def update_queue(client: RossumClient, body: dict):
    object = client.patch(f"queues")
    return object

def update_schema(client: RossumClient, body: dict):
    object = client.patch(f"schemas")
    return object

def update_user(client: RossumClient, body: dict):
    object = client.patch(f"users")
    return object

def update_hook(client: RossumClient, body: dict):
    object = client.patch(f"hooks")
    return object