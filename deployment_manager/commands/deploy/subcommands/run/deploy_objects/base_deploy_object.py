from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
    AttributeOverrider,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.deploy_differ import (
    DeployObjectDiffer,
)
from deployment_manager.commands.deploy.subcommands.run.merge.detect_reference import (
    detect_reference_with_type,
)
from deployment_manager.commands.deploy.subcommands.run.merge.merge import (
    create_rebase_diff,
    get_nested_value,
    prompt_conflict_resolution,
    prompt_rebase_field,
    set_nested_value,
)
from deployment_manager.commands.deploy.subcommands.run.merge.merge import (
    deep_three_way_merge,
)

if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (
        DeployOrchestrator,
    )

from copy import deepcopy
from datetime import datetime

from pydantic import BaseModel
import questionary
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.reference_replace import (
    ReferenceReplacer,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    create_object_label,
    generate_deploy_timestamp,
    remove_queue_attributes_for_cross_org,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    DeployException,
    LookupTable,
    NonExistentObjectException,
    PathNotFoundException,
    Target,
    TargetWithDefault,
    TimestampMismatchException,
)
from deployment_manager.common.read_write import read_json, write_json
from rich import print as pprint
from rich.panel import Panel
from rich.console import Console


from anyio import Path
from rossum_api import APIClientError
from rossum_api.api_client import Resource

from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.utils.functions import extract_id_from_url, templatize_name_id

console = Console()


# TODO: document methods
# TODO: prebuilt exceptions that automatically reference the type/name/id of object
class DeployObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource
    data: dict = None

    deploy_file: DeployOrchestrator = None
    yaml_reference: dict = None

    conflict_detected: bool = False
    rebase_detected: bool = False

    initialize_failed: bool = False
    deploy_failed: bool = False
    ignore_timestamp_mismatch: bool = False

    targets: list[TargetWithDefault] = []

    ignored_attributes: list[str] = []

    overrider: AttributeOverrider = None
    ref_replacer: ReferenceReplacer = None

    async def initialize_deploy_object(self, release_file: "DeployOrchestrator"):
        self.deploy_file = release_file
        self.yaml_reference = self.get_object_in_yaml()

        self.overrider = AttributeOverrider(type=self.type)
        self.ref_replacer = ReferenceReplacer(type=self.type)

        try:
            self.data = await read_json(self.path)
        except Exception:
            raise PathNotFoundException(
                f"Could not load object data from: [green]{self.path}[/green]. Is the object name in deploy file in-sync with its local path?"
            ) from None

        self.ignored_attributes = [
            *settings.DEPLOY_NON_DIFFED_KEYS.get(self.type, []),
            *settings.NON_VERSIONED_KEYS_PER_OBJECT.get(self.type, []),
            *(
                settings.DEPLOY_CROSS_ORG_NON_DIFFED_KEYS.get(self.type, [])
                if not self.deploy_file.is_same_org
                else []
            ),
        ]

    # TODO: if attribute override explicitly specified a reference to target object, this would not work
    async def initialize_target_objects(self):
        """Prepares target.pre_reference_replace_data = everything except for reference replacing"""
        for target_index, target in enumerate(self.targets):
            target.index = target_index
            target.parent_object = self

            data_copy = deepcopy(self.data)

            # Should run before attribute override
            self.remove_ignored_attributes(data_copy)

            # TODO: for cross-cluster/cross-org, URL might be different -> create from client base API URL?
            data_copy["url"] = data_copy["url"].replace(
                str(data_copy["id"]), str(target.id)
            )
            data_copy["id"] = target.id

            # Should be run before attribute override - e.g., schema's name override is sometimes added dynamically in this method
            # Some methods also ignore attributes - explicit attr override is a way to overrule that ignore as long as it runs after this method
            await self.initialize_target_object_data(data=data_copy, target=target)

            self.overrider.override_attributes_v2(
                object=data_copy, attribute_overrides=target.attribute_override
            )

            target.pre_reference_replace_data = data_copy
            target.visualized_plan_data = deepcopy(data_copy)
            target.first_deploy_data = deepcopy(data_copy)
            target.second_deploy_data = deepcopy(data_copy)

    async def initialize_target_object_data(self, data: dict, target: Target):
        """Method for specific deploy_objects (e.g., hooks) to add their custom logic"""
        ...

    @property
    def path(self) -> Path:
        return (
            Path(self.deploy_file.source_dir_path)
            / self.type.value
            / f"{templatize_name_id(self.name, self.id)}.json"
        )

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

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
        return f'"{self.name} ([purple]{self.id}[/purple])" -> "{target['name']} ([purple]{target['id']}[/purple])"'

    async def get_remote_object(self, remote_object_id):
        try:
            return await self.deploy_file.client._http_client.fetch_one(
                self.type, remote_object_id
            )
        except APIClientError as e:
            if e.status_code == 404:
                raise NonExistentObjectException(
                    f"{self.display_type} [purple]{remote_object_id}[/purple] does not exist on remote."
                ) from None
            raise e

    def update_targets(self):
        for target in self.targets:
            # In case of errors, do not overwrite the existing target ID, the object still exists
            if target.data_from_remote and (
                new_id := target.data_from_remote.get("id", None)
            ):
                target.id = new_id
            self.yaml_reference["targets"][target.index]["id"] = target.id

    async def deploy_target_objects(self, data_attribute: str):
        requests = []
        for target in self.targets:
            # Before first deploy of some objects (e.g., queues), it is important to create schemas, workspaces, etc. that must exist first
            # At this point, those objects were deployed, their local target objects have refreshed IDs
            await self.override_references(
                data_attribute=data_attribute, use_dummy_references=False
            )

            if target.exists_on_remote:
                requests.append(
                    self.update_remote(data_attribute=data_attribute, target=target)
                )
            else:
                requests.append(
                    self.create_remote(data_attribute=data_attribute, target=target)
                )

        await asyncio.gather(*requests)
        # asyncio.gather returns results in the same order as they were put in
        self.update_targets()

    async def create_remote(self, data_attribute: dict, target: Target = None):
        try:
            data = getattr(target, data_attribute)

            result = await self.deploy_file.client._http_client.create(self.type, data)
            # Only if the API call succeeds
            target.last_applied_data = data
            target.data_from_remote = result

            pprint(
                f"{settings.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )
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

            result = await self.deploy_file.client._http_client.update(
                resource=self.type, id_=target.id, data=data
            )
            # Only if the API call succeeds
            target.last_applied_data = data
            target.data_from_remote = result

            pprint(
                f"{settings.UPDATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}."
            )
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
                await self.deploy_file.client._http_client.delete(
                    self.type, id_=target.id
                )

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

            # TODO: dummy references flag here
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

    async def persist_target_only_references(
        self, target: Target, data_attribute: str, dependency_name: str
    ):
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

    def remove_ignored_attributes(self, data):
        data.pop("created_by", None)
        data.pop("created_at", None)
        data.pop("modified_by", None)
        data.pop("modified_at", None)

        for attribute in self.ignored_attributes:
            data.pop(attribute, None)

        # These keys are not pulled locally so comparing a remote object with a local one would yield false diffs
        ignored_keys_for_type = settings.NON_VERSIONED_KEYS_PER_OBJECT.get(self.type, [])
        for key in ignored_keys_for_type:
            data.pop(key, None)

        # match self.type:
        #     case Resource.Queue:
        #         if not self.is_same_org_deploy:
        #             remove_queue_attributes_for_cross_org(data)

    # TODO: handle half-ignored fields like queue.generic_engine
    # ! TODO: if source has multiple targets, rebasing should be done in attr_override, not in source itself
    # ! Conflicts write twice to the same file, making it unresolvable with nice IDE diffing
    # (The user probably does not want to propagate the change into all targets in such a case)
    async def compare_target_objects(self):
        try:
            for target in self.targets:
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
                    prefer="neither",
                    override_fields=[],
                    ignored_fields=[
                        "id",
                        "url",
                        *self.ignored_attributes,
                    ],
                    derived_fields=last_applied.get("derived_fields", []),
                )

                for path, target_val in rebase_candidates.items():
                    # Target-only drift - should the value be saved in source? -> ask user

                    # ! TODO: check how paths look like for something like "first ID in hook.queues"
                    # ! TODO: what if target hook is assigned to 2 target queues mapping to the same source? Is it OK to reference the same queue multiple times in the list?
                    is_ref, reference_type = detect_reference_with_type(
                        value=target_val, field_name=path
                    )
                    if is_ref:
                        if reference_type:
                            target_val = ReferenceReplacer.reverse_target_reference_into_source(
                                value=target_val,
                                reference_type=reference_type,
                                reverse_lookup_table=self.deploy_file.reverse_lookup_table,
                            )
                        else:
                            target_val = (
                                ReferenceReplacer.reverse_unknown_reference_type(
                                    target_val
                                )
                            )

                    # TODO: display big(ger) warning if reference is unknown
                    diff = create_rebase_diff(
                        source_val=get_nested_value(last_applied, path),
                        target_val=target_val,
                    )
                    display_warning(
                        f'{self.display_label}: Field "[green]{path}[/green]" has changed in {settings.TARGET_DIRNAME} only.'
                    )
                    console.print(diff)
                    # User accepts rebase/conflict and source now has target value (e.g., name)
                    # But if there is attribute override, this will still be applied and so the rebase/conflict will not be resolved
                    # ! TODO: Must also update attribute override

                    # TODO: yy option to do it for all targets
                    if await prompt_rebase_field(self.display_label, path):
                        self.rebase_detected = True
                        # Mutate local source data directly here
                        # ! TODO: if name changes, the file needs to be resaved (would be good to wrap that logic in write_json).
                        set_nested_value(self.data, path, target_val)
                        await write_json(self.path, self.data)

                # TODO: if source queue ABC maps to target queue 123 and 456 and target hook is assigned only to 456, there will be a conflict we can detect but not visualize back both references are translated to the same source
                if conflicts:
                    self.conflict_detected = True
                    # Use source with potentially applied rebases
                    # But if user declined some rebase, we should not put it into this object, hence using self.data and not merged_data
                    # We should also not write any version of data with replaced references or attribute overrides
                    source_with_target_values = deepcopy(self.data)
                    for path, (_, target_val) in conflicts.items():
                        # Target-only drift - should the value be saved in source? -> ask user
                        is_ref, reference_type = detect_reference_with_type(
                            value=target_val, field_name=path
                        )
                        if is_ref:
                            if reference_type:
                                target_val = ReferenceReplacer.reverse_target_reference_into_source(
                                    value=target_val,
                                    reference_type=reference_type,
                                    reverse_lookup_table=self.deploy_file.reverse_lookup_table,
                                )
                            else:
                                target_val = (
                                    ReferenceReplacer.reverse_unknown_reference_type(
                                        target_val
                                    )
                                )

                        set_nested_value(source_with_target_values, path, target_val)
                    # Real conflict - write to file and let user resolve
                    await prompt_conflict_resolution(
                        source_with_target_values, last_applied, self.path
                    )
                    display_error(
                        f"Conflict between {settings.SOURCE_DIRNAME} and remote {settings.TARGET_DIRNAME} detected for: [green]{self.path}[/green]"
                    )

                # ? Initial data does not have references replaced, but it has attr overrides etc. <- would have to distinguish if the change was a reference field
                # ? Rebased fields can be visualized and first_deployed, but reference fields were reversed!
                # ? Conflict fields are resolved in source -> they require a reload of command or reload of data and reparsing of everything again
                # ? Idea: once rebase and conflict done (do not stop command execution), reload the object from source and create visualied + first_deploy again - do not compare this time!
                # ! Watch out for attr override overriding what the user just resolved as a conflict/rebase
                # ? second_deploy_data can just be a reload of initial data
                # ? Once reloaded, just show plan, do not compare again

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

            diff = DeployObjectDiffer.create_override_diff(
                overriden_object_data, target.visualized_plan_data
            )
            if not diff:
                return

            colorized_diff = DeployObjectDiffer.parse_diff(diff)
            message = f"{self.display_type} {self.create_source_to_target_string(target.visualized_plan_data)}:\n{colorized_diff}"
            pprint(Panel(message))


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

    async def initialize(*args, **kwargs): ...

    async def deploy(self): ...

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"
