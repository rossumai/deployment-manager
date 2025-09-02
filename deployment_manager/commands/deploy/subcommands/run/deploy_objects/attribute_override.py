import re
import jmespath


from deployment_manager.utils.consts import settings
from deployment_manager.utils.functions import (
    flatten,
)
from rossum_api.api_client import Resource


class AttributeOverrideException(Exception): ...


class AttributeOverrider:

    def __init__(self, type: Resource):
        self.type = type

    def override_attribute_v2(
        self,
        object: dict,
        key_query: str,
        new_value: str,
    ):
        parent, key = parse_parent_and_key(key_query)

        search = perform_search(parent, object)

        for override_parent in search:
            # The attribute (key) might not be on all parent objects (e.g., configurations[*].queue_ids)
            if key not in override_parent:
                continue

            if isinstance(new_value, str):
                source_regex, new_value = parse_regex_attribute_override(new_value)

                if not source_regex:
                    override_parent[key] = new_value
                else:
                    pattern = re.compile(source_regex)
                    override_parent[key] = re.sub(
                        pattern, new_value, override_parent[key]
                    )
            # Overwriting dicts -> merge keys, overwrite only the provided ones
            elif isinstance(new_value, dict):
                override_parent[key] = {**override_parent[key], **new_value}
            # Overwriting lists and any other values -> replace the whole list
            else:
                override_parent[key] = new_value

    def override_attributes_v2(
        self,
        object: dict,
        attribute_overrides: dict,
    ) -> dict:
        if not object:
            raise Exception(
                f'Cannot perform attribute_override on None object (target name: {object.get("name", "")} | target id: {object.get("id", "")}).'
            )

        for key, value in attribute_overrides.items():
            self.override_attribute_v2(
                object=object,
                key_query=key,
                new_value=value,
            )

    def reverse_attributes_v2(
        self,
        source_object: dict,
        target_object: dict,
        attribute_overrides: dict,
    ) -> dict[str, any]:
        if not target_object:
            raise Exception(
                f'Cannot reverse attribute_override on None object (target name: {target_object.get("name", "")} | target id: {target_object.get("id", "")}).'
            )

        reversed_overrides = {}

        for key in attribute_overrides:
            single_reversal = self.reverse_attribute_override_v2(
                source_object=source_object,
                target_object=target_object,
                key_query=key,
            )
            reversed_overrides.update(single_reversal)

        return reversed_overrides

    def reverse_attribute_override_v2(
        self,
        source_object: dict,
        target_object: dict,
        key_query: str,
    ) -> dict[str, any]:
        parent, key = parse_parent_and_key(key_query)

        source_matches = perform_search(parent, source_object)
        target_matches = perform_search(parent, target_object)

        if len(source_matches) != len(target_matches):
            raise AttributeOverrideException(
                f'Mismatch in number of matches when reversing override at "{key_query}" '
                f"(source={len(source_matches)}, target={len(target_matches)})."
            )

        reversed_values = []

        for source_parent, target_parent in zip(source_matches, target_matches):
            if key not in source_parent or key not in target_parent:
                continue  # Can't reverse if missing

            source_val = source_parent[key]
            target_val = target_parent[key]

            if source_val != target_val:
                reversed_values.append(source_val)

        if not reversed_values:
            return {}

        if len(reversed_values) == 1:
            return {key_query: reversed_values[0]}
        else:
            return {
                key_query: reversed_values
            }  # list of values if multiple elements matched


def traverse_mapping(submapping: dict):
    if isinstance(submapping, list):
        for el in submapping:
            yield from traverse_mapping(el)
    elif isinstance(submapping, dict):
        yield submapping
        for k, v in submapping.items():
            if k not in settings.MAPPING_TRAVERSE_IGNORE_FIELDS:
                yield from traverse_mapping(v)


def create_regex_override_syntax(source: str, target: str):
    return f"{source}{settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR}{target}"


def parse_regex_attribute_override(value: str):
    split_values = value.split(settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR)
    if len(split_values) == 1:
        return ["", value]
    else:
        return split_values


def parse_parent_and_key(key_query: str):
    try:
        dot = [pos for pos, char in enumerate(key_query) if char == "."]
        pipe = [pos for pos, char in enumerate(key_query) if char == "|"]
        dot_idx = dot[-1] if dot else -1
        pipe_idx = pipe[-1] if pipe else -1
        idx = dot_idx if dot_idx > -1 else pipe_idx if pipe_idx > -1 else -1
        parent = key_query[:idx].strip() if idx > -1 else None
        key = key_query[idx + 1 :].strip() if idx > -1 else key_query
    except Exception:
        raise AttributeOverrideException(
            f'Invalid attribute override query "{key_query}" - the last part must be a single object key.'
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
        raise AttributeOverrideException(
            f'JMESPath query "{parent}" returned no result.'
        )

    return search
