import json
import re
import subprocess
import tempfile
import jmespath

from rossum_api.api_client import Resource

from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    traverse_object,
)
from project_rossum_deploy.commands.deploy.subcommands.run.models import Target
from project_rossum_deploy.utils.consts import display_warning, settings
from project_rossum_deploy.utils.functions import (
    flatten,
)


class AttributeOverrideException(Exception): ...


class AttributeOverrider:
    type: Resource

    IMPLICIT_OVERRIDE_KEYS = ["settings", "metadata"]

    def __init__(self, type: Resource):
        self.type = type

    def replace_ids_in_target_object(
        self,
        target: Target,
        lookup_table: dict,
        target_object_index: int,
        num_targets: int,
    ):
        for key in self.IMPLICIT_OVERRIDE_KEYS:
            if key not in target.data:
                continue

            for parent, key_in_parent, value in traverse_object(
                target.data, key, target.data[key]
            ):
                for source_id, targets in lookup_table.items():
                    # source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
                    # if not re.search(source_id_regex, str(value)):
                    # continue
                    if str(source_id) not in str(value):
                        continue

                    if not targets:
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target.id}". No target IDs found.',
                        )
                        self.remove_id_from_boject(
                            object=parent, key=key_in_parent, value=value
                        )
                        continue
                    # N:N objects -> objects are referenced in pairs
                    elif num_targets == len(targets):
                        target_id = targets[target_object_index]["id"]
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )
                    # N:1 objects -> everything should be mapped to the first target ID
                    else:
                        target_id = targets[0]["id"]
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )

                        if len(targets) != 1:
                            display_warning(
                                f"For overriding source_id '{source_id}' in {self.type.value} '{target.id}', There are multiple target IDs that could be assigned. The first one was used.",
                            )

            # stringified_dict = json.dumps(target.data[key])
            # for source_id, targets in lookup_table.items():
            #     source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
            #     # This ID from source was not found in the subobject
            #     if not re.search(source_id_regex, stringified_dict):
            #         continue

            #     if not targets:
            #         display_warning(
            #             f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target.id}". No target IDs found.',
            #         )
            #         continue
            #     # N:N objects -> objects are referenced in pairs
            #     elif num_targets == len(targets):
            #         target_id = targets[target_object_index]["id"]
            #         stringified_dict = self.replace_id_in_stringified_object(
            #             object_str=stringified_dict,
            #             regex=source_id_regex,
            #             source_id=source_id,
            #             target_id=target_id,
            #         )
            #     # N:1 objects -> everything should be mapped to the first target ID
            #     else:
            #         target_id = targets[0]["id"]
            #         stringified_dict = self.replace_id_in_stringified_object(
            #             object_str=stringified_dict,
            #             regex=source_id_regex,
            #             source_id=source_id,
            #             target_id=target_id,
            #         )

            #         if len(targets) != 1:
            #             display_warning(
            #                 f"For overriding source_id '{source_id}' in {self.type.value} '{target.id}', There are multiple target IDs that could be assigned. The first one was used.",
            #             )

            #     target.data[key] = json.loads(stringified_dict)

    def replace_id_in_object(
        self, object: dict, key: str, value: str | int, source_id: int, target_id: int
    ):
        if isinstance(object[key], list):
            value_index = object[key].index(value)
            if value_index > -1:
                new_value = str(value).replace(str(source_id), str(target_id))
                # Convert value back to int if applicable
                if isinstance(value, int):
                    new_value = int(new_value)
                object[key][value_index] = new_value
        else:
            new_value = str(value).replace(str(source_id), str(target_id))
            # Convert value back to int if applicable
            if isinstance(value, int):
                new_value = int(new_value)
            object[key] = new_value
        # Using lambdas for sub() because of quotes inside strings
        # return re.sub(
        #     regex,
        #     lambda m: str(target_id) if m[0] == str(source_id) else m[0],
        #     object_str,
        # )

    def remove_id_from_boject(self, object: dict, key: str, value: str | int):
        if isinstance(object[key], list):
            value_index = object[key].index(value)
            if value_index > -1:
                del object[key][value_index]
        else:
            del object[key]

    def create_override_diff(self, before_object: dict, after_object: dict):
        """Displays both implicit and explicit overrides (the explicit applied already when uploading the file itself)"""
        # Do not display diffs in ID, but the ID must be retained for later reference
        after_object_id = after_object.pop("id", None)
        after_object_url = after_object.pop("url", None)
        before_object.pop("id", None)
        before_object.pop("url", None)

        with tempfile.NamedTemporaryFile() as tf1, tempfile.NamedTemporaryFile() as tf2:
            tf1.write(bytes(json.dumps(before_object, indent=2), "UTF-8"))
            tf2.write(bytes(json.dumps(after_object, indent=2), "UTF-8"))
            # Has to be manually seeked back to start
            tf1.seek(0)
            tf2.seek(0)

            diff = subprocess.run(
                ["diff", tf1.name, tf2.name, "-U" "3"],
                capture_output=True,
                text=True,
            )
            after_object["id"] = after_object_id
            after_object["url"] = after_object_url

            return diff.stdout

    def parse_diff(self, diff: str):
        colorized_lines = []
        split_lines = diff.splitlines()
        del split_lines[0:3]

        for index, line in enumerate(split_lines):
            if line.startswith("-"):
                colorized_line = f"[red]{line}[/red]"
            elif line.startswith("+"):
                colorized_line = f"[green]{line}[/green]"
            # The second is a CRLF issue related to diff
            elif line.startswith("@@") or "newline at end of file" in line:
                del split_lines[index]
            else:
                colorized_line = line
            colorized_lines.append(colorized_line)
        return "\n".join(colorized_lines)


def create_regex_override_syntax(source: str, target: str):
    return f"{source}{settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR}{target}"


def parse_regex_attribute_override(value: str):
    split_values = value.split(settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR)
    if len(split_values) == 1:
        return ["", value]
    else:
        return split_values


def override_attribute_v2(
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

        source_regex, new_value = parse_regex_attribute_override(new_value)
        if not source_regex:
            override_parent[key] = new_value
        else:
            pattern = re.compile(source_regex)
            override_parent[key] = re.sub(pattern, new_value, override_parent[key])


def override_attributes_v2(
    object: dict,
    attribute_overrides: dict,
) -> dict:
    if not object:
        raise Exception(
            f'Cannot perform attribute_override on None object (target name: {object.get("name", "")} | target id: {object.get("id", "")}).'
        )

    for key, value in attribute_overrides.items():
        override_attribute_v2(
            object=object,
            key_query=key,
            new_value=value,
        )


def parse_parent_and_key(key_query: str):
    try:
        parent, key = ".".join(key_query.split(".")[:-1]), key_query.split(".")[-1]
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
