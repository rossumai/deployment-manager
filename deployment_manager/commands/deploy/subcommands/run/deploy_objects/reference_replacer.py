from __future__ import annotations
from curses.ascii import isdigit
import re
from typing import TYPE_CHECKING

from typing import Any
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    create_object_label,
    traverse_object,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    LookupTable,
    ReverseLookupTable,
)
from deployment_manager.utils.consts import display_warning, settings
from deployment_manager.utils.functions import extract_id_from_url
from rossum_api.api_client import Resource


import copy

if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
        DeployObject,
    )


class ReferenceReplacer:
    type: Resource
    parent_object_reference: "DeployObject"

    IMPLICIT_OVERRIDE_KEYS = ["settings", "metadata"]

    def __init__(self, parent_object_reference: DeployObject, type: Resource):
        self.parent_object_reference = parent_object_reference
        self.type = type

    def replace_base_url(self, url: str, source_base_url: str, target_base_url: str):
        return url.replace(source_base_url, target_base_url)

    def replace_references_in_unstructured_attributes(
        self,
        target_object_label: str,
        target_object: dict,
        lookup_table: LookupTable,
        target_object_index: int,
        num_targets: int,
    ):
        """
        Traverses selected "free-form" attributes like settings and replaces IDs of known objects using the lookup table
        """
        for key in self.IMPLICIT_OVERRIDE_KEYS:
            if key not in target_object:
                continue

            for parent, key_in_parent, value in traverse_object(
                target_object, key, target_object[key]
            ):
                for source_id, types_dict in lookup_table.items():
                    # source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
                    # if not re.search(source_id_regex, str(value)):
                    # continue
                    if str(source_id) not in str(value):
                        continue

                    if len(types_dict.keys()) > 1:
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target_object_label}". There are different types of objects with the same ID ({list(types_dict.keys())}).',
                        )
                        self.remove_id_from_list(
                            object=parent, key=key_in_parent, value=value
                        )
                        continue

                    elif not len(types_dict.keys()):
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target_object_label}". No target IDs found.',
                        )
                        self.remove_id_from_list(
                            object=parent, key=key_in_parent, value=value
                        )
                        continue

                    targets = list(types_dict.values())[0]
                    # N:N objects -> objects are referenced in pairs
                    if num_targets == len(targets):
                        target_id = targets[target_object_index].id
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )
                    # N:1 objects -> everything should be mapped to the first target ID
                    else:
                        target_id = targets[0].id
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )

                        if len(targets) != 1:
                            display_warning(
                                f"For overriding source_id '{source_id}' in {self.type.value} '{target_object_label}', There are multiple target IDs that could be assigned. The first one was used.",
                            )

    def replace_id_in_object(
        self, object: dict, key: str, value: str | int, source_id: int, target_id: int
    ):
        if isinstance(object[key], list):
            if value in object[key]:
                value_index = object[key].index(value)
                new_value = str(value).replace(str(source_id), str(target_id))
                # Convert value back to int if applicable
                if isinstance(value, int) and all(isdigit(c) for c in new_value):
                    new_value = int(new_value)
                object[key][value_index] = new_value
        else:
            new_value = str(value).replace(str(source_id), str(target_id))
            # Convert value back to int if applicable
            # Only do it if the new ID can be converted - dummy references cannot for instance
            if isinstance(value, int) and all(isdigit(c) for c in new_value):
                new_value = int(new_value)
            object[key] = new_value
        # Using lambdas for sub() because of quotes inside strings
        # return re.sub(
        #     regex,
        #     lambda m: str(target_id) if m[0] == str(source_id) else m[0],
        #     object_str,
        # )

    def remove_id_from_list(self, object: dict, key: str, value: str | int):
        if isinstance(object[key], list):
            value_index = object[key].index(value)
            if value_index > -1:
                del object[key][value_index]
        else:
            del object[key]

    def _replace_reference_in_url(
        self,
        source_dependency_url,
        lookup_table: LookupTable,
        reverse_lookup_table: ReverseLookupTable,
        object_type: Resource,
        target_objects_count,
        target_index,
        use_dummy_references: bool = True,
    ):
        source_id = extract_id_from_url(source_dependency_url)
        target_dependency_objects = lookup_table.get(source_id, {}).get(object_type, [])

        # Dependency object has no target equivalents (e.g., when ignored)
        if not len(target_dependency_objects):
            # Check if the source_id is not actually a target ID that was replaced previously
            if str(source_id) in reverse_lookup_table.get(object_type, {}):
                return source_dependency_url

            return
        # There are multiple objects released (e.g., queues) and their number is the same as the number of their dependencies (e.g., hooks) -> assume that each object should have its own dependency
        if len(target_dependency_objects) == target_objects_count:
            selected_target = target_dependency_objects[target_index]
        # All objects will have the same dependency
        else:
            selected_target = target_dependency_objects[0]

        # New object is referenced
        if not selected_target.exists_on_remote and not use_dummy_references:
            return

        target_id_str = str(selected_target.id)
        source_id_str = str(source_id)
        new_url = source_dependency_url.replace(source_id_str, target_id_str)
        return new_url

    def replace_reference_url(
        self,
        object: dict,
        target_index: int,
        target_objects_count: int,
        dependency_name: str,
        lookup_table: LookupTable,
        reverse_lookup_table: ReverseLookupTable,
        object_type: Resource,
        use_dummy_references: bool,
        keep_dependency_without_equivalent: bool = False,
        allow_empty_reference: bool = False,
    ):
        source_dependency_url = object.get(dependency_name, "")
        if not source_dependency_url:
            if allow_empty_reference:
                object.pop(dependency_name, "")
            return

        new_url = self._replace_reference_in_url(
            source_dependency_url=source_dependency_url,
            lookup_table=lookup_table,
            reverse_lookup_table=reverse_lookup_table,
            object_type=object_type,
            target_objects_count=target_objects_count,
            target_index=target_index,
            use_dummy_references=use_dummy_references,
        )
        if new_url:
            object[dependency_name] = new_url
            return

        if keep_dependency_without_equivalent:
            return

        # Remove object instead of making it None - Elis API does not allow that for some attribtues (e.g., queue.inbox)
        if allow_empty_reference:
            object.pop(dependency_name, "")
            return

        raise Exception(
            f'Dependency "{dependency_name}": "{source_dependency_url}" for {create_object_label(object.get('name', 'no-name'), object.get('id', 'no-id'))} was not modified. Source ID could not be found in the list of deployed objects.'
        )

    def replace_list_of_reference_urls(
        self,
        object: dict,
        target_index: int,
        target_objects_count: int,
        dependency_name: str,
        object_type: Resource,
        lookup_table: LookupTable,
        reverse_lookup_table: ReverseLookupTable,
        use_dummy_references: bool,
        keep_dependencies_without_equivalent: bool = False,
    ):
        # The list is either copied and URLs are replaced, or they are simply added
        new_urls = (
            copy.deepcopy(object.get(dependency_name, []))
            if keep_dependencies_without_equivalent
            else []
        )
        for source_index, source_dependency_url in enumerate(
            object.get(dependency_name, [])
        ):
            new_url = self._replace_reference_in_url(
                source_dependency_url=source_dependency_url,
                reverse_lookup_table=reverse_lookup_table,
                lookup_table=lookup_table,
                object_type=object_type,
                target_objects_count=target_objects_count,
                target_index=target_index,
                use_dummy_references=use_dummy_references,
            )

            # Unlike for a single reference, a list item can be missing
            # In situations where this could be a problem, there are special warnings (e.g., forgotten hooks for queues)
            if not new_url:
                continue

            # Replace this specific reference, other references may remain unchanged in the final list
            if keep_dependencies_without_equivalent:
                new_urls[source_index] = new_url
            else:
                new_urls.append(new_url)

        object[dependency_name] = new_urls

    @classmethod
    def reverse_target_reference_into_source(
        cls,
        value: Any,
        reference_type: Resource,
        reverse_lookup_table: ReverseLookupTable,
        source_base_url: str,
        target_base_url: str,
    ):
        if isinstance(value, str) or isinstance(value, int):
            value = str(value)
            for target_id, source_id in reverse_lookup_table.get(
                reference_type, {}
            ).items():
                if target_id in value:
                    value = value.replace(target_id, str(source_id))

            if re.compile(target_base_url).match(value):
                value = value.replace(target_base_url, source_base_url)
            return value
        elif isinstance(value, list):
            return [
                cls.reverse_target_reference_into_source(
                    v,
                    reference_type,
                    reverse_lookup_table,
                    source_base_url,
                    target_base_url,
                )
                for v in value
            ]
        elif isinstance(value, dict):
            return {
                k: cls.reverse_target_reference_into_source(
                    v,
                    reference_type,
                    reverse_lookup_table,
                    source_base_url,
                    target_base_url,
                )
                for k, v in value.items()
            }
        return value

    @classmethod
    def reverse_unknown_reference_type(cls, value: Any):
        return f"UNKNOWN_REFERENCE({value})"
