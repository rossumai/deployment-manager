from anyio import Path
from rossum_api.api_client import Resource

from deployment_manager.utils.consts import CustomResource


def determine_object_type_from_path(path: Path) -> Resource:
    split_path = str(path).split("/") # TODO
    type = split_path[-2] if len(split_path) > 1 else path.stem + "s"
    allowed_types = set(resource.value for resource in Resource)
    if type in allowed_types:
        return Resource(type)
    else:
        type = split_path[-3] if len(split_path) > 1 else path.stem + "s"
        allowed_types = set(resource.value for resource in Resource)
        if type in allowed_types:
            return Resource(type)
        else:
            raise Exception(f'Unknown resource "{type}".')


def determine_object_type_from_url(url: str) -> Resource:
    split_path = url.split("/")
    type = split_path[-2]
    if type in set(resource.value for resource in Resource):
        return Resource(type)
    elif type in set(resource.value for resource in CustomResource):
        return CustomResource(type)
    else:
        raise Exception(f'Unknown resource "{type}".')
