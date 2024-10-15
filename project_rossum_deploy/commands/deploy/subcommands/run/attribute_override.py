import jmespath

from project_rossum_deploy.utils.functions import (
    flatten,
)


def override_attributes_v2(
    object: dict,
    attribute_overrides: dict,
) -> dict:
    def override_attribute_v2(
        key_query: str,
        new_value: str,
    ):
        parent, key = parse_parent_and_key(key_query)

        search = perform_search(parent, object)

        for override_parent in search:
            # The attribute (key) might not be on all parent objects (e.g., configurations[*].queue_ids)
            if key not in override_parent:
                continue

            # value_to_override = override_parent[key]
            override_parent[key] = new_value

    if not object:
        raise Exception(
            f'Cannot perform attribute_override on None object (target name: {object.get("name", "")} | target id: {object.get("id", "")}).'
        )

    for key, value in attribute_overrides.items():
        override_attribute_v2(
            key_query=key,
            new_value=value,
        )


def parse_parent_and_key(key_query: str):
    try:
        parent, key = ".".join(key_query.split(".")[:-1]), key_query.split(".")[-1]
    except Exception:
        raise Exception(
            f'Invalid query "{key_query}" - the last part must be a single object key.'
        )
    return parent, key


def perform_search(parent: str, object: dict):
    # The query targets a key of the top-most object, no need to search
    if not parent:
        return [object]

    search = jmespath.search(parent, object)
    if isinstance(search, list):
        search = flatten(search)
    else:
        search = [search]

    if not len(search) or not search[0]:
        raise Exception(f'Query "{parent}" returned no result.')

    return search
