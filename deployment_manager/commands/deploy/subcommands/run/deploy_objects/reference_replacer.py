from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING, Any

from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.helpers import create_object_label, traverse_object
from deployment_manager.commands.deploy.subcommands.run.models import LookupTable, ReverseLookupTable
from deployment_manager.utils.consts import CustomResource, display_warning
from deployment_manager.utils.functions import extract_id_from_url

if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject


def _singular(resource_url_part: str) -> str:
    if resource_url_part.endswith("es") and resource_url_part[:-2].endswith(("x", "s", "h", "z")):
        return resource_url_part[:-2]
    return resource_url_part.removesuffix("s")


REFERENCE_TYPES: list[Resource | CustomResource] = [
    Resource.Organization,
    Resource.Workspace,
    Resource.Queue,
    Resource.Schema,
    Resource.Inbox,
    Resource.Hook,
    Resource.Rule,
    Resource.Engine,
    Resource.EngineField,
    Resource.EmailTemplate,
    CustomResource.Label,
    CustomResource.Workflow,
    CustomResource.WorkflowStep,
]
REFERENCE_TYPE_BY_KEY: dict[str, Resource | CustomResource] = {
    **{resource.value: resource for resource in REFERENCE_TYPES},
    **{_singular(resource.value): resource for resource in REFERENCE_TYPES},
}
REFERENCE_KEY_NOISE_TOKENS = ("id", "ids", "url", "urls", "ref", "refs", "reference", "references")


class ReferenceReplacer:
    type: Resource
    parent_object_reference: "DeployObject"

    IMPLICIT_OVERRIDE_KEYS = ["settings", "metadata", "actions"]
    # Paths (as "key.subkey") where reference IDs must match exactly in unstructured attributes replacer rather than as
    # substrings, to avoid corrupting values (e.g., UUIDs) that happen to contain the source ID.
    EXACT_MATCH_PATHS = ["actions.id"]

    NOT_A_REFERENCE = object()

    def __init__(self, parent_object_reference: DeployObject, type: Resource):
        self.parent_object_reference = parent_object_reference
        self.type = type

    def replace_base_url(self, url: str, source_base_url: str, target_base_url: str):
        return url.replace(source_base_url, target_base_url)

    @staticmethod
    def _is_valid_id(id_val) -> bool:
        """Check if an ID is a valid numeric ID (not a dummy UUID)."""
        return isinstance(id_val, int) or (isinstance(id_val, str) and id_val.isdigit())

    @staticmethod
    def _id_regex(source_id: int | str) -> re.Pattern:
        """Match the ID only when it is not glued to another alphanumeric character."""
        return re.compile(rf"(?<![0-9A-Za-z]){re.escape(str(source_id))}(?![0-9A-Za-z])")

    @staticmethod
    def _replace_id_in_url(url: str, target_id: str) -> str:
        """Swap the object ID (the last URL path segment) for the target one."""
        base, _, _ = url.rpartition("/")
        return f"{base}/{target_id}" if base else target_id

    @classmethod
    def _reference_type_from_value(cls, value: str, source_id: int | str) -> Resource | CustomResource | None:
        """Infer what the ID refers to from a URL-like value (e.g., ".../hooks/1" -> Resource.Hook)."""
        for resource in REFERENCE_TYPES:
            if re.search(rf"(?:^|/){resource.value}/{re.escape(str(source_id))}(?![0-9])", value):
                return resource
        return None

    @classmethod
    def _reference_type_from_key(cls, key: str) -> Resource | CustomResource | None:
        """Infer what the ID refers to from its key (e.g., "next_phase_hook_id" -> Resource.Hook)."""
        tokens = str(key).lower().split("_")
        while tokens and tokens[-1] in REFERENCE_KEY_NOISE_TOKENS:
            tokens.pop()

        for index in range(len(tokens)):
            candidate = "_".join(tokens[index:])
            if candidate in REFERENCE_TYPE_BY_KEY:
                return REFERENCE_TYPE_BY_KEY[candidate]
        return None

    @classmethod
    def _resolve_reference_type(
        cls,
        key: str,
        value: str,
        source_id: int | str,
        types_dict: dict,
    ):
        """Resolve which type sharing this source ID is referenced (else NOT_A_REFERENCE, or None if ambiguous)."""
        if len(types_dict) == 1:
            return next(iter(types_dict))

        inferred_type = cls._reference_type_from_value(value, source_id) or cls._reference_type_from_key(key)
        if inferred_type is None:
            return None if value.strip() == str(source_id) else cls.NOT_A_REFERENCE
        if inferred_type in types_dict:
            return inferred_type
        return cls.NOT_A_REFERENCE

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
        id_regexes = {source_id: self._id_regex(source_id) for source_id in lookup_table}

        for key in self.IMPLICIT_OVERRIDE_KEYS:
            if key not in target_object:
                continue

            for parent, key_in_parent, value in traverse_object(target_object, key, target_object[key]):
                # Resolve every reference against the ORIGINAL value, then apply them in a single pass,
                # so an ID written by one lookup entry cannot be re-matched by a later one.
                replacements: dict[str, str] | None = {}
                for source_id, types_dict in lookup_table.items():
                    if not id_regexes[source_id].search(str(value)):
                        continue
                    elif f"{key}.{key_in_parent}" in self.EXACT_MATCH_PATHS and str(source_id) != str(value):
                        # Skip substring-only matches for paths like "actions.id" where partial ID replacement would corrupt values (e.g., UUIDs)
                        continue

                    if not len(types_dict.keys()):
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target_object_label}". No target IDs found.',
                        )
                        self.remove_id_from_list(object=parent, key=key_in_parent, value=value)
                        replacements = None
                        break

                    reference_type = self._resolve_reference_type(
                        key=key_in_parent, value=str(value), source_id=source_id, types_dict=types_dict
                    )
                    if reference_type is self.NOT_A_REFERENCE:
                        continue
                    if reference_type is None:
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target_object_label}". There are different types of objects with the same ID ({list(types_dict.keys())}).',
                        )
                        self.remove_id_from_list(object=parent, key=key_in_parent, value=value)
                        replacements = None
                        break

                    targets = types_dict[reference_type]
                    # N:N objects -> objects are referenced in pairs
                    if num_targets == len(targets):
                        target_id = targets[target_object_index].id
                    # N:1 objects -> everything should be mapped to the first target ID
                    else:
                        target_id = targets[0].id

                        if len(targets) != 1:
                            display_warning(
                                f"For overriding source_id '{source_id}' in {self.type.value} '{target_object_label}', There are multiple target IDs that could be assigned. The first one was used.",
                            )

                    replacements[str(source_id)] = str(target_id)

                if replacements:
                    self.replace_ids_in_object(
                        object=parent, key=key_in_parent, value=value, replacements=replacements
                    )

    def replace_ids_in_object(self, object: dict, key: str, value: str | int, replacements: dict[str, str]):
        """Replace all source IDs in the value in one pass; matching the original value means a written
        target is never re-matched as another ID's source. Handles a scalar, a multi-reference string, or a list element."""
        if key not in object:
            return value

        alternation = "|".join(re.escape(s) for s in sorted(replacements, key=len, reverse=True))
        pattern = re.compile(rf"(?<![0-9A-Za-z])({alternation})(?![0-9A-Za-z])")
        new_value = pattern.sub(lambda m: replacements[m.group(0)], str(value))
        # Convert value back to int if applicable
        # Only do it if the new ID can be converted - dummy references cannot for instance
        if isinstance(value, int) and new_value.isdigit():
            new_value = int(new_value)

        if isinstance(object[key], list):
            if value not in object[key]:
                return value
            object[key][object[key].index(value)] = new_value
        else:
            object[key] = new_value

        return new_value

    def replace_id_in_object(self, object: dict, key: str, value: str | int, source_id: int, target_id: int):
        return self.replace_ids_in_object(object, key, value, {str(source_id): str(target_id)})

    def remove_id_from_list(self, object: dict, key: str, value: str | int):
        if key not in object:
            return

        if isinstance(object[key], list):
            if value in object[key]:
                object[key].remove(value)
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

        # New object is referenced - skip if it doesn't exist yet and we're not using dummy refs
        # Also check if the ID is a real numeric ID (indicating successful creation)
        # as exists_on_remote might not be set correctly in some edge cases
        target_id_is_valid = self._is_valid_id(selected_target.id)
        if not selected_target.exists_on_remote and not target_id_is_valid and not use_dummy_references:
            return

        target_id_str = str(selected_target.id)

        source_base_url = self.parent_object_reference.deploy_file.source_client._http_client.base_url
        target_base_url = self.parent_object_reference.deploy_file.client._http_client.base_url

        if selected_target.data_from_remote and selected_target.data_from_remote.get("url"):
            remote_url = selected_target.data_from_remote["url"]
            target_id_str = str(extract_id_from_url(remote_url))

        new_url = self._replace_id_in_url(source_dependency_url, target_id_str)
        if source_base_url != target_base_url:
            new_url = new_url.replace(source_base_url, target_base_url)
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
        new_urls = copy.deepcopy(object.get(dependency_name, [])) if keep_dependencies_without_equivalent else []
        for source_index, source_dependency_url in enumerate(object.get(dependency_name, [])):
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
            for target_id, source_id in reverse_lookup_table.get(reference_type, {}).items():
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
