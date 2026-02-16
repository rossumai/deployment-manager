from __future__ import annotations

import json
from typing import TYPE_CHECKING

import questionary

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import AttributeOverrider
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.deploy_differ import DeployObjectDiffer
from deployment_manager.commands.deploy.subcommands.run.merge.detect_reference import (
    ReferenceDetectionStatus,
    detect_reference_with_type,
)
from deployment_manager.commands.deploy.subcommands.run.merge.merge import (
    create_rebase_diff,
    deep_three_way_merge,
    get_nested_value,
    prompt_conflict_resolution,
    prompt_rebase_field,
    set_nested_value,
)

if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (
        DeployOrchestrator,
    )

from copy import deepcopy

from anyio import Path
from pydantic import BaseModel
from rich import print as pprint
from rich.console import Console
from rich.panel import Panel

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.reference_replacer import ReferenceReplacer
from deployment_manager.commands.deploy.subcommands.run.helpers import create_object_label
from deployment_manager.commands.deploy.subcommands.run.models import (
    NonExistentObjectException,
    PathNotFoundException,
    Target,
    TargetWithDefault,
)
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json
from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.utils.functions import gather_with_concurrency, templatize_name_id, extract_id_from_url
from deployment_manager.utils.logging import append_raw_event
from rossum_api import APIClientError
from rossum_api.api_client import Resource

console = Console(stderr=True)


# TODO: prebuilt exceptions that automatically reference the type/name/id of object
class DeployObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource
    data: dict = {}

    deploy_file: DeployOrchestrator = None
    yaml_reference: dict = None

    conflict_detected: bool = False
    rebase_all: bool = False
    rebase_none: bool = False
    rebase_detected: bool = False

    initialize_failed: bool = False
    deploy_failed: bool = False
    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    ignored_attributes: list[str] = []
    sort_list_attributes: list[str] = []

    overrider: AttributeOverrider = None
    ref_replacer: ReferenceReplacer = None

    async def initialize_deploy_object(self, deploy_file: "DeployOrchestrator"):
        self.deploy_file = deploy_file
        self.yaml_reference = self.get_object_in_yaml()
        self.rebase_none = self.deploy_file.no_rebase

        self.overrider = AttributeOverrider(type=self.type)
        self.ref_replacer = ReferenceReplacer(type=self.type, parent_object_reference=self)

        # Only read from filesystem if data wasn't already provided (e.g., from auto-loading)
        if not self.data:
            try:
                self.data = await read_object_from_json(self.path, False)
            except PathNotFoundException:
                self.initialize_failed = True
                display_error(
                    f"Could not load object data from: [green]{self.path}[/green]. Is the object name in deploy file in-sync with its local path?"
                )
            except Exception as e:
                self.initialize_failed = True
                display_error(f"Could not read data from: [green]{self.path}[/green]: {e}")

        self.ignored_attributes = [
            *settings.DEPLOY_NON_DIFFED_KEYS.get(self.type, []),
            *settings.NON_PULLED_KEYS_PER_OBJECT.get(self.type, []),
            *(settings.DEPLOY_CROSS_ORG_NON_DIFFED_KEYS.get(self.type, []) if not self.deploy_file.is_same_org else []),
        ]

        self.sort_list_attributes = settings.DEPLOY_SORT_LIST_KEYS.get(self.type, [])

    # TODO: if attribute override explicitly specified a reference to target object, this would not work
    async def initialize_target_objects(self):
        """Prepares target.pre_reference_replace_data = everything except for reference replacing"""
        for target_index, target in enumerate(self.targets):
            target.index = target_index
            target.parent_object = self
            # New targets have a UUID as fallback
            # For display purposes, create an ID that mentions the name of source object
            if not target.exists_on_remote:
                target.create_dummy_id_from_parent()
            else:
                try:
                    await self.get_remote_object(target.id)
                except NonExistentObjectException:
                    display_error(f"{self.display_type} {target.display_label} does not exist on remote.")
                    raise

            data_copy = deepcopy(self.data)

            # Should run before attribute override
            self.remove_ignored_attributes(data_copy)

            data_copy["url"] = self.ref_replacer.replace_base_url(
                url=data_copy["url"],
                source_base_url=self.deploy_file.source_client._http_client.base_url,
                target_base_url=self.deploy_file.client._http_client.base_url,
            )
            data_copy["url"] = data_copy["url"].replace(str(data_copy["id"]), str(target.id))
            data_copy["id"] = target.id

            # Should be run before attribute override - e.g., schema's name override is sometimes added dynamically in this method
            # Some methods also ignore attributes - explicit attr override is a way to overrule that ignore as long as it runs after this method
            await self.initialize_target_object_data(data=data_copy, target=target)

            self.overrider.override_attributes_v2(object=data_copy, attribute_overrides=target.attribute_override)

            target.pre_reference_replace_data = data_copy
            target.visualized_plan_data = deepcopy(data_copy)
            target.first_deploy_data = deepcopy(data_copy)
            target.second_deploy_data = deepcopy(data_copy)

    async def initialize_target_object_data(self, data: dict, target: Target):
        """Method for specific deploy_objects (e.g., hooks) to add their custom logic"""
        ...

    def scrub_attributes(self, data: dict):
        """Removes fields that should not be saved into last_applied deploy state (e.g., hook.secrets)"""
        return data

    @property
    def path(self) -> Path:
        return (
            Path(self.deploy_file.source_dir_path) / self.type.value / f"{templatize_name_id(self.name, self.id)}.json"
        )

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[: -2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self):
        return create_object_label(self.name, self.id)

    @property
    def is_creating_targets(self):
        for target in self.targets:
            if not target.exists_on_remote:
                return True
        return False

    def get_object_in_yaml(self):
        objects = self.deploy_file.yaml.data.get(self.type.value, [])
        for object in objects:
            if object.get("id", None) == self.id:
                return object
        return None

    def create_source_to_target_string(self, target: dict):
        return f'"{self.name} ([purple]{self.id}[/purple])" -> "{target["name"]} ([purple]{target["id"]}[/purple])"'

    async def get_remote_object(self, remote_object_id):
        try:
            return await self.deploy_file.client._http_client.fetch_one(self.type, remote_object_id)
        except APIClientError as e:
            if e.status_code == 404:
                raise NonExistentObjectException(
                    f"{self.display_type} {remote_object_id} does not exist on remote."
                ) from None
            raise e

    def update_targets(self):
        for target in self.targets:
            # In case of errors, do not overwrite the existing target ID, the object still exists
            if target.data_from_remote and (new_id := target.data_from_remote.get("id", None)):
                target.id = new_id
                # Only update yaml_reference if it exists (auto-loaded objects don't have yaml_reference)
                if self.yaml_reference:
                    self.yaml_reference["targets"][target.index]["id"] = target.id
            # Only update yaml_reference if it exists (auto-loaded objects don't have yaml_reference)
            if self.yaml_reference:
                self.yaml_reference["targets"][target.index]["attribute_override"] = target.attribute_override

    async def deploy_target_objects(self, data_attribute: str):
        requests = []
        for target in self.targets:
            # Before first deploy of some objects (e.g., queues), it is important to create schemas, workspaces, etc. that must exist first
            # At this point, those objects were deployed, their local target objects have refreshed IDs
            await self.override_references_in_target_object_data(
                data_attribute=data_attribute, target=target, use_dummy_references=False
            )

            self.ref_replacer.replace_references_in_unstructured_attributes(
                target_object=getattr(target, data_attribute),
                target_object_label=self.display_label,
                lookup_table=self.deploy_file.lookup_table,
                target_object_index=target.index,
                num_targets=len(self.targets),
            )

            if target.exists_on_remote:
                requests.append(self.update_remote(data_attribute=data_attribute, target=target))
            else:
                requests.append(self.create_remote(data_attribute=data_attribute, target=target))

        await gather_with_concurrency(*requests)
        # asyncio.gather returns results in the same order as they were put in
        self.update_targets()

    async def create_remote(self, data_attribute: dict, target: Target = None):
        try:
            data = getattr(target, data_attribute)

            create_copy = deepcopy(data)
            # Temporary fix because some objects like rules fail if ID is sent
            create_copy.pop("id", None)

            result = await self.deploy_file.client._http_client.create(self.type, create_copy)
            # Remember last_applied only if the API call succeeds
            target.last_applied_data = self.scrub_attributes(data)
            target.data_from_remote = result
            target.update_after_first_create()

            pprint(f"{settings.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.")
        except Exception as e:
            display_error(
                f"Error while creating {self.display_type} {self.display_label} ^",
                e,
            )
            self.deploy_failed = True
            return {}

    async def update_remote(self, data_attribute: str, target: Target):
        try:
            data = getattr(target, data_attribute)

            update_copy = deepcopy(data)
            # Temporary fix because some objects like rules fail if ID is sent
            update_copy.pop("id", None)

            result = await self.deploy_file.client._http_client.update(
                resource=self.type, id_=target.id, data=update_copy
            )
            # Only if the API call succeeds
            target.last_applied_data = self.scrub_attributes(data)
            target.data_from_remote = result

            pprint(f"{settings.UPDATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.")
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type} {self.display_label} -> "{target.id}: {e}',
                (None if isinstance(e, NonExistentObjectException) else e),
            )
            self.deploy_failed = True
            return {}

    async def delete_remote(self, target: Target):
        try:
            if not self.plan_only:
                await self.deploy_file.client._http_client.delete(self.type, id_=target.id)

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.DELETE_PRINT_STR} {self.display_type}: [purple]({target.id})[/purple]."
            )
        except Exception as e:
            display_error(
                f'Error while deleting {self.display_type} {self.display_label} -> "{target.id}: {e}',
                e,
            )
            self.deploy_failed = True

    async def override_references(self, data_attribute: str, use_dummy_references: bool):
        for target in self.targets:
            data = getattr(target, data_attribute)

            self.ref_replacer.replace_references_in_unstructured_attributes(
                target_object=data,
                target_object_label=self.display_label,
                lookup_table=self.deploy_file.lookup_table,
                target_object_index=target.index,
                num_targets=len(self.targets),
            )

            await self.override_references_in_target_object_data(
                data_attribute=data_attribute,
                target=target,
                use_dummy_references=use_dummy_references,
            )

    async def override_references_in_target_object_data(
        self, data_attribute: str, target: Target, use_dummy_references: bool
    ):
        """Method for specific deploy_objects (e.g., hooks) to add their custom logic"""
        ...

    async def persist_target_only_references(self, target: Target, data_attribute: str, dependency_name: str):
        """For lists of references, adds back any references that were not overriden and that are target-only"""
        if not target.exists_on_remote:
            return

        remote_target = await self.get_remote_object(target.id)
        data_with_overriden_references = getattr(target, data_attribute)
        overriden_references = data_with_overriden_references.get(dependency_name, [])

        for remote_target_reference_url in remote_target.get(dependency_name, []):
            # Target ID was found in the new list as well
            if remote_target_reference_url in overriden_references:
                continue
            overriden_references.append(remote_target_reference_url)

    async def persist_target_only_reference(
        self,
        target: Target,
        data_attribute: str,
        dependency_name: str,
        object_type: Resource | None = None,
    ):
        """For single references, restores the target-only value when mapping is missing."""
        if not target.exists_on_remote:
            return

        remote_target = await self.get_remote_object(target.id)
        remote_reference = remote_target.get(dependency_name)
        if not remote_reference:
            return

        data_with_overriden_reference = getattr(target, data_attribute)
        current_reference = data_with_overriden_reference.get(dependency_name)
        if not current_reference:
            data_with_overriden_reference[dependency_name] = remote_reference
            return

        source_reference = None
        if target.pre_reference_replace_data:
            source_reference = target.pre_reference_replace_data.get(dependency_name)

        if object_type and source_reference:
            source_reference_id = extract_id_from_url(source_reference)
            if source_reference_id is not None:
                targets = self.deploy_file.lookup_table.get(source_reference_id, {}).get(object_type, [])
                if targets:
                    return

        source_base_url = self.deploy_file.source_client._http_client.base_url
        target_base_url = self.deploy_file.client._http_client.base_url
        if source_reference and current_reference == source_reference:
            data_with_overriden_reference[dependency_name] = remote_reference
        elif source_base_url != target_base_url and str(current_reference).startswith(source_base_url):
            data_with_overriden_reference[dependency_name] = remote_reference

    def remove_ignored_attributes(self, data):
        data.pop("created_by", None)
        data.pop("created_at", None)
        data.pop("modified_by", None)
        data.pop("modified_at", None)

        for attribute in self.ignored_attributes:
            data.pop(attribute, None)

        # These keys are not pulled locally so comparing a remote object with a local one would yield false diffs
        ignored_keys_for_type = settings.NON_PULLED_KEYS_PER_OBJECT.get(self.type, [])
        for key in ignored_keys_for_type:
            data.pop(key, None)

    # TODO: if source has multiple targets, rebasing should be done in attr_override, not in source itself
    async def compare_target_objects(self):
        try:
            for target in self.targets:
                # No point comparing what does not yet exist
                if not target.exists_on_remote:
                    continue

                # Get last applied from deploy state
                last_applied = (
                    self.deploy_file.deploy_state.get_last_applied(
                        resource_type=self.type,
                        source_id=self.id,
                        target_id=target.id,
                        direction="forward",
                    )
                    or {}
                )

                remote_object = await self.get_remote_object(target.id)
                self.remove_ignored_attributes(remote_object)

                # Use visualized version (with dummy refs) for comparison
                # This allows comparing against last_applied and knowing if new references were added (target references will equal, dummy refs will not because they are not in last_applied)
                _, conflicts, rebase_candidates = deep_three_way_merge(
                    last_applied=last_applied,
                    source=target.visualized_plan_data,
                    target=remote_object,
                    prefer=self.deploy_file.prefer,
                    override_fields=[],
                    ignored_fields=[
                        "id",
                        "url",
                        *self.ignored_attributes,
                    ],
                    derived_fields=last_applied.get("derived_fields", []),
                )

                for path, target_val in rebase_candidates.items():
                    if self.rebase_none:
                        break

                    # Target-only drift - should the value be saved in source? -> ask user

                    ref_status, reference_type = detect_reference_with_type(value=target_val, field_name=path)
                    if ref_status in [
                        ReferenceDetectionStatus.DEFINITELY_REFERENCE,
                        ReferenceDetectionStatus.UNKNOWN,
                    ]:
                        if reference_type:
                            target_val = ReferenceReplacer.reverse_target_reference_into_source(
                                value=target_val,
                                reference_type=reference_type,
                                reverse_lookup_table=self.deploy_file.reverse_lookup_table,
                                source_base_url=self.deploy_file.source_client._http_client.base_url,
                                target_base_url=self.deploy_file.client._http_client.base_url,
                            )
                        else:
                            target_val = ReferenceReplacer.reverse_unknown_reference_type(target_val)

                    source_val = get_nested_value(self.data, path)

                    # Ensure consistent order for lists of IDs
                    if path in self.sort_list_attributes:
                        source_val = sorted(source_val if source_val else [])
                        target_val = sorted(target_val if target_val else [])

                    diff = create_rebase_diff(
                        source_val=source_val,
                        target_val=target_val,
                    )
                    if not diff:
                        continue
                    display_warning(
                        f'{self.display_label}: Field "[green]{path}[/green]" has changed in {settings.TARGET_DIRNAME} only.'
                    )
                    colorized_diff = DeployObjectDiffer.parse_diff(diff)
                    pprint(Panel(colorized_diff))
                    # User accepts rebase/conflict and source now has target value (e.g., name)
                    # But if there is attribute override, this will still be applied and so the rebase/conflict will not be resolved
                    # ! TODO: Must also update attribute override

                    if not self.rebase_all and not self.rebase_none:
                        (
                            should_rebase,
                            self.rebase_all,
                            self.rebase_none,
                        ) = await prompt_rebase_field(self.display_label, path)
                    if self.rebase_all or should_rebase:
                        self.rebase_detected = True

                        # Conflict in code was written into that file instead
                        if await self.apply_code_rebase(
                            attribute_path=path,
                            target_val=target_val,
                        ):
                            continue
                        # Mutate local source data directly here
                        # ! TODO: if name changes, the file needs to be resaved (would be good to wrap that logic in write_object_to_json).
                        set_nested_value(self.data, path, target_val)
                        await write_object_to_json(self.path, self.data)

                        data_copy = deepcopy(self.data)
                        self.overrider.override_attributes_v2(data_copy, target.attribute_override)
                        initial_value = get_nested_value(self.data, path)
                        post_override_value = get_nested_value(data_copy, path)
                        if initial_value != post_override_value:
                            display_warning(
                                f"Attribute override mutates the rebased value in {path}:\n\nRebased: {initial_value}\nOveride: {post_override_value}"
                            )
                            override_choices = [
                                questionary.Choice(title=f"{key}: {value}", value=key)
                                for key, value in target.attribute_override.items()
                            ]
                            keys_to_delete = await questionary.checkbox(
                                "Select overrides to delete:", choices=override_choices
                            ).ask_async()
                            for key in keys_to_delete:
                                target.attribute_override.pop(key, None)
                            self.update_targets()
                            await self.deploy_file.yaml.save_to_file(self.deploy_file.deploy_file_path)

                # Only do it for the first target if there are conflicts with multiple of them
                if conflicts:
                    if self.conflict_detected:
                        display_warning(
                            f"Conflict detected between multiple {settings.TARGET_DIRNAME}s and a single {settings.SOURCE_DIRNAME} - only the first was written into the {settings.SOURCE_DIRNAME} file."
                        )
                        continue

                    self.conflict_detected = True
                    # Use source with potentially applied rebases
                    # But if user declined some rebase, we should not put it into this object, hence using self.data and not merged_data
                    # We should also not write any version of data with replaced references or attribute overrides
                    source_with_target_values = deepcopy(self.data)
                    for path, (_, target_val) in conflicts.items():
                        # Conflict in code was written into that file instead
                        if await self.resolve_code_conflict(
                            attribute_path=path,
                            last_applied=last_applied,
                            target_val=target_val,
                        ):
                            continue

                        # Target-only drift - should the value be saved in source? -> ask user
                        ref_status, reference_type = detect_reference_with_type(value=target_val, field_name=path)
                        if ref_status in [
                            ReferenceDetectionStatus.DEFINITELY_REFERENCE,
                            ReferenceDetectionStatus.UNKNOWN,
                        ]:
                            if reference_type:
                                target_val = ReferenceReplacer.reverse_target_reference_into_source(
                                    value=target_val,
                                    reference_type=reference_type,
                                    reverse_lookup_table=self.deploy_file.reverse_lookup_table,
                                    source_base_url=self.deploy_file.source_client._http_client.base_url,
                                    target_base_url=self.deploy_file.client._http_client.base_url,
                                )
                            else:
                                target_val = ReferenceReplacer.reverse_unknown_reference_type(target_val)

                        set_nested_value(source_with_target_values, path, target_val)

                    # Real conflict - write to file and let user resolve
                    # ! This assumes that these two objects were created from the same JSON as source
                    # Thanks to that, sorting of keys is preserved (Python dict implementation guarantee) without the need to resort
                    last_applied_str = json.dumps(last_applied, indent=2)
                    target_str = json.dumps(source_with_target_values, indent=2)
                    await prompt_conflict_resolution(
                        target_str=target_str,
                        last_applied_str=last_applied_str,
                        object_path=self.path,
                    )
                    display_error(
                        f"Conflict between {settings.SOURCE_DIRNAME} and remote {settings.TARGET_DIRNAME} detected for: [green]{self.path}[/green]"
                    )
        except Exception as e:
            display_error(
                f"Error while comparing {self.display_type} {self.name} ({self.id}) ^",
                e,
            )
            self.deploy_failed = True

    async def visualize_changes(self):
        for target in self.targets:
            # When updating, take the real remote object
            # The diff comparison will then show only overrides that are not on the remote already (not all overrides from source)
            if target.exists_on_remote:
                overriden_object_data = await self.get_remote_object(target.id)
            else:
                overriden_object_data = {}

            self.remove_ignored_attributes(overriden_object_data)
            self.sort_lists(overriden_object_data)

            self.sort_lists(target.visualized_plan_data)

            action = "update" if target.exists_on_remote else "create"
            plan_label = f"{settings.PLAN_PRINT_STR} {settings.UPDATE_PRINT_STR if target.exists_on_remote else settings.CREATE_PRINT_STR}"
            diff = DeployObjectDiffer.create_override_diff(overriden_object_data, target.visualized_plan_data)
            colorized_diff = DeployObjectDiffer.parse_diff(diff)
            message = f"{plan_label} {self.display_type} {self.create_source_to_target_string(target.visualized_plan_data)}:\n{colorized_diff if colorized_diff else ''}"
            pprint(Panel(message))
            append_raw_event(
                "plan_object",
                {
                    "action": action,
                    "type": self.type.value,
                    "source_id": self.id,
                    "source_name": self.name,
                    "target_id": target.visualized_plan_data.get("id"),
                    "target_name": target.visualized_plan_data.get("name"),
                    "diff": diff,
                },
            )

    async def resolve_code_conflict(self, attribute_path: str, last_applied: dict, target_val: str): ...

    async def apply_code_rebase(self, attribute_path: str, target_val: str): ...

    def sort_lists(self, object: dict):
        """Done only before diffing to not show lists of URLS/IDs as different just because the ordering is different"""
        for key in self.sort_list_attributes:
            set_nested_value(object, key, sorted(get_nested_value(object, key, [])))


class EmptyDeployObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int = None
    name: str = ""
    type: Resource = "no-type"
    base_path: Path = None

    initialize_failed: bool = False
    deploy_failed: bool = False
    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    async def initialize_deploy_object(self, *args, **kwargs): ...
    async def initialize_target_objects(self, *args, **kwargs): ...
    async def initialize_target_object_data(self, *args, **kwargs): ...
    async def deploy_target_objects(self, *args, **kwargs): ...
    async def override_references(self, *args, **kwargs): ...
    async def override_references_in_target_object_data(self, *args, **kwargs): ...
    async def visualize_changes(self, *args, **kwargs): ...

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[: -2 if self.type in [Resource.Inbox] else -1]}[/yellow]"
