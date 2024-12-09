import asyncio
from copy import deepcopy
from typing import Union

from anyio import Path
from pydantic import Field
import questionary
from deployment_manager.commands.deploy.subcommands.run.inbox_release import (
    InboxRelease,
)
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    EmptyObjectRelease,
    ObjectRelease,
)


from rossum_api.api_client import Resource

from deployment_manager.commands.deploy.subcommands.run.schema_release import (
    SchemaRelease,
)
from deployment_manager.commands.migrate.helpers import replace_dependency_url
from deployment_manager.utils.consts import (
    QUEUE_ENGINE_ATTRIBUTES,
    display_error,
    display_warning,
)
from deployment_manager.utils.functions import (
    templatize_name_id,
)


class QueueRelease(ObjectRelease):
    type: Resource = Resource.Queue
    keep_hook_dependencies_without_equivalent: bool = False
    ignore_deploy_warnings: bool = False

    schema_release: SchemaRelease = Field(alias="schema")
    inbox_release: Union[InboxRelease, EmptyObjectRelease] = Field(
        alias="inbox", union_mode="left_to_right"
    )

    schema_targets: dict[int, list] = []
    workspace_targets: dict[int, list] = []
    hook_targets: dict[int, list] = []

    async def initialize(
        self,
        yaml,
        client,
        source_dir_path,
        plan_only,
        is_same_org_deploy,
        workspace_targets: dict[int, list],
        hook_targets: dict[int, list],
    ):
        self.schema_release.base_path = self.base_path
        self.inbox_release.base_path = self.base_path
        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
            is_same_org_deploy=is_same_org_deploy,
        )

        self.workspace_targets = workspace_targets
        self.hook_targets = hook_targets

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "queue.json"
        )

    async def deploy(self):
        try:
            if self.plan_only:
                # Ignore warnings independently (ignore in first function would hide warning in second)
                self.yaml_reference[
                    "ignore_deploy_warnings"
                ] = await self.evaluate_workflow_warning()
                self.yaml_reference[
                    "ignore_deploy_warnings"
                ] = await self.evaluate_engine_warning()

            await self.schema_release.initialize(
                yaml=self.yaml,
                client=self.client,
                source_dir_path=self.base_path,
                plan_only=self.plan_only,
                is_same_org_deploy=self.is_same_org_deploy,
                parent_queue=self,
            )
            await self.schema_release.deploy()
            self.schema_targets = {
                self.schema_release.id: [
                    target.data for target in self.schema_release.targets if target.data
                ]
            }
            if self.schema_release.deploy_failed:
                raise Exception()

            release_requests = []
            target_objects_count = len(self.targets)
            for target_index, target in enumerate(self.targets):
                queue_copy = deepcopy(self.data)
                queue_copy.pop("inbox", None)
                if not self.is_same_org_deploy:
                    self.remove_attributes_for_cross_org(queue_copy=queue_copy)

                previous_workspace_url = queue_copy["workspace"]
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="workspace",
                    source_id_target_pairs=self.workspace_targets,
                )

                if previous_workspace_url == queue_copy["workspace"] and not target.id:
                    display_error(
                        f'Cannot create target for queue "{queue_copy['name']} ({queue_copy['id']})" - there is no target workspace to put it into.'
                    )
                    return

                previous_schema_url = queue_copy["schema"]
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="schema",
                    source_id_target_pairs=self.schema_targets,
                )

                if previous_schema_url == queue_copy["schema"] and not target.id:
                    display_error(
                        f'Cannot create target for queue "{queue_copy['name']} ({queue_copy['id']})" - there is no target schema to use it with.'
                    )
                    return

                # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="hooks",
                    source_id_target_pairs=self.hook_targets,
                    keep_hook_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
                )
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="webhooks",
                    source_id_target_pairs=self.hook_targets,
                    keep_hook_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
                )

                self.overrider.override_attributes_v2(
                    object=queue_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(target_object=queue_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)

            self.update_targets(results)

            await self.inbox_release.initialize(
                yaml=self.yaml,
                client=self.client,
                source_dir_path=self.base_path,
                plan_only=self.plan_only,
                is_same_org_deploy=self.is_same_org_deploy,
                queue_targets={self.id: [target.data for target in self.targets]},
                parent_queue=self,
            )
            await self.inbox_release.deploy()

        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}): {e}",
                e,
            )

    def remove_attributes_for_cross_org(self, queue_copy: dict):
        queue_copy.pop("workflows", None)
        for attr in QUEUE_ENGINE_ATTRIBUTES:
            queue_copy.pop(attr)

    async def evaluate_workflow_warning(self):
        if self.ignore_deploy_warnings or self.is_same_org_deploy:
            return

        if self.data.get("workflows", []):
            display_warning(
                f"{self.display_type} {self.display_label} has 'workflows' defined. Please make sure to create and assign them manually for the target."
            )
            return await questionary.confirm(
                "Do you want to disable warnings like this for this queue?",
            ).ask_async()

    async def evaluate_engine_warning(self):
        for attr in QUEUE_ENGINE_ATTRIBUTES:
            if self.ignore_deploy_warnings or self.is_same_org_deploy:
                return

            if self.data.get(attr, None):
                display_warning(
                    f"{self.display_type} {self.display_label} has '{attr}' defined. Please make sure to create and assign it manually for the target."
                )
                return await questionary.confirm(
                    "Do you want to disable warnings like this for this queue?",
                ).ask_async()