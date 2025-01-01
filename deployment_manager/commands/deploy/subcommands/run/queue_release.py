import asyncio
from copy import deepcopy
from typing import Optional

from anyio import Path
from pydantic import Field
import questionary
from rossum_api import APIClientError
from deployment_manager.commands.deploy.subcommands.run.inbox_release import (
    InboxRelease,
)
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    EmptyObjectRelease,
    ObjectRelease,
    PathNotFoundException,
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


class SubObjectException(Exception): ...


class QueueRelease(ObjectRelease):
    type: Resource = Resource.Queue
    keep_hook_dependencies_without_equivalent: bool = False
    ignore_deploy_warnings: bool = False

    schema_ignore_timestamp_mismatch: bool = False
    inbox_ignore_timestamp_mismatch: bool = False

    schema_release: SchemaRelease = Field(alias="schema")
    inbox_release: Optional[InboxRelease] = Field(
        default_factory=lambda: EmptyObjectRelease(), alias="inbox"
    )

    schema_targets: dict[int, list] = []
    workspace_targets: dict[int, list] = []
    hook_targets: dict[int, list] = []

    async def initialize(
        self,
        schema_ignore_timestamp_mismatch,
        inbox_ignore_timestamp_mismatch,
        workspace_targets: dict[int, list],
        hook_targets: dict[int, list],
        **kwargs,
    ):
        try:
            self.schema_release.base_path = self.base_path
            self.inbox_release.base_path = self.base_path

            self.schema_ignore_timestamp_mismatch = schema_ignore_timestamp_mismatch
            self.inbox_ignore_timestamp_mismatch = inbox_ignore_timestamp_mismatch

            await super().initialize(**kwargs)

            self.workspace_targets = workspace_targets
            self.hook_targets = hook_targets
        except Exception as e:
            display_error(
                f"Error while initializing {self.display_type} {self.display_label}: {e}",
                None if isinstance(e, PathNotFoundException) else e,
            )
            self.initialize_failed = True

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
                await self.verify_subobjects_have_same_target_count()

                # Ignore warnings independently (ignore in first function would hide warning in second)
                self.ignore_deploy_warnings = await self.evaluate_workflow_warning()
                self.ignore_deploy_warnings = await self.evaluate_engine_warning()

            await self.schema_release.initialize(
                yaml=self.yaml,
                client=self.client,
                source_dir_path=self.base_path,
                plan_only=self.plan_only,
                is_same_org_deploy=self.is_same_org_deploy,
                parent_queue=self,
                last_deploy_timestamp=self.last_deploy_timestamp,
                ignore_timestamp_mismatch=self.schema_ignore_timestamp_mismatch,
                source_client=self.source_client,
            )
            if self.schema_release.initialize_failed:
                raise SubObjectException()

            await self.schema_release.deploy()
            self.schema_targets = {
                self.schema_release.id: [
                    target.data for target in self.schema_release.targets if target.data
                ]
            }
            if self.schema_release.deploy_failed:
                raise SubObjectException()

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
                    raise Exception(
                        f'Cannot create target for queue "{queue_copy['name']} ({queue_copy['id']})" - there is no target workspace to put it into.'
                    )

                previous_schema_url = queue_copy["schema"]
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="schema",
                    source_id_target_pairs=self.schema_targets,
                )

                if previous_schema_url == queue_copy["schema"] and not target.id:
                    raise Exception(
                        f'Cannot create target for queue "{queue_copy['name']} ({queue_copy['id']})" - there is no target schema to use it with.'
                    )

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

            if self.deploy_failed:
                raise SubObjectException()

            await self.inbox_release.initialize(
                yaml=self.yaml,
                client=self.client,
                source_dir_path=self.base_path,
                plan_only=self.plan_only,
                is_same_org_deploy=self.is_same_org_deploy,
                queue_targets={self.id: [target.data for target in self.targets]},
                parent_queue=self,
                last_deploy_timestamp=self.last_deploy_timestamp,
                ignore_timestamp_mismatch=self.inbox_ignore_timestamp_mismatch,
                source_client=self.source_client,
            )
            if self.inbox_release.initialize_failed:
                raise SubObjectException()

            await self.inbox_release.deploy()

            if self.inbox_release.deploy_failed:
                raise SubObjectException()

        except SubObjectException:
            self.deploy_failed = True
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True

    def remove_attributes_for_cross_org(self, queue_copy: dict):
        queue_copy.pop("workflows", None)
        for attr in QUEUE_ENGINE_ATTRIBUTES:
            queue_copy.pop(attr)

    async def verify_subobjects_have_same_target_count(self):
        mismatch_found = False

        queue_targets_len = len(self.targets)
        schema_targets_len = len(self.schema_release.targets)
        inbox_targets_len = len(self.inbox_release.targets)
        queue_has_inbox = bool(self.data.get("inbox", ""))

        if queue_targets_len != schema_targets_len:
            display_warning(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its schema has {schema_targets_len}. Please make the target counts are equal."
            )
            mismatch_found = True
        if queue_has_inbox and queue_targets_len != inbox_targets_len:
            display_warning(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its inbox has {inbox_targets_len}. Please make the target counts are equal."
            )
            mismatch_found = True

        if mismatch_found:
            raise Exception("Incorrect inbox/schema target count vs queue target count")

    async def evaluate_workflow_warning(self):
        if self.ignore_deploy_warnings or self.is_same_org_deploy:
            return True

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
                return True

            if self.data.get(attr, None):
                display_warning(
                    f"{self.display_type} {self.display_label} has '{attr}' defined. Please make sure to create and assign it manually for the target."
                )
                return await questionary.confirm(
                    "Do you want to disable warnings like this for this queue?",
                ).ask_async()

    async def check_source_object(self):
        try:
            remote_queue = await self.source_client._http_client.fetch_one(
                self.type, self.id
            )
            return remote_queue["status"] != "deletion_requested"
        except APIClientError as e:
            if e.status_code == 404:
                return False
            raise e
        return True
