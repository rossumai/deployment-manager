
from deployment_tool_config import rossum_password, rossum_username, base_url, api_version
import rossum_client, api
token = rossum_client.auth(base_url, api_version, rossum_username, rossum_password)
client = rossum_client.RossumClient(token, base_url, api_version)
orgs = api.get_organizations(client)
workspaces = api.get_organizations(client)
