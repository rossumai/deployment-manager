import asyncio
from copy import deepcopy
from typing import Optional

from anyio import Path
from pydantic import Field
import questionary

from deployment_manager.commands.download.downloader import Downloader
from rossum_api import APIClientError
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    remove_queue_attributes_for_cross_org,
)
from deployment_manager.commands.deploy.subcommands.run.inbox_release import (
    InboxRelease,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    SubObjectException,
    Target,
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
    settings,
    QUEUE_ENGINE_ATTRIBUTES,
    display_error,
    display_warning,
)
from deployment_manager.utils.functions import (
    extract_id_from_url,
    templatize_name_id,
)


class QueueRelease(ObjectRelease):
    type: Resource = Resource.Queue
    keep_hook_dependencies_without_equivalent: bool = False

    ignore_all_deploy_warnings: bool = False
    ignore_deploy_warnings: bool = False

    overwrite_ignored_fields: bool = False

    schema_release: SchemaRelease = Field(alias="schema")
    inbox_release: Optional[InboxRelease] = Field(
        default_factory=lambda: EmptyObjectRelease(type=Resource.Inbox), alias="inbox"
    )

    schema_targets: dict[int, list] = []
    workspace_targets: dict[int, list] = []
    hook_targets: dict[int, list] = []

    unselected_hooks: list[int] = []

    async def initialize(
        self,
        workspace_targets: dict[int, list],
        hook_targets: dict[int, list],
        unselected_hooks: list[int],
        **kwargs,
    ):
        try:
            self.schema_release.base_path = self.base_path
            self.inbox_release.base_path = self.base_path

            await super().initialize(**kwargs)

            self.unselected_hooks = unselected_hooks
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
                ignore_unassigned_hooks = await self.verify_no_unassigned_hooks()
                ignore_workflow_warnings = await self.evaluate_workflow_warning()
                ignore_engine_warnings = await self.evaluate_engine_warning()
                self.ignore_deploy_warnings = any(
                    [
                        ignore_unassigned_hooks,
                        ignore_workflow_warnings,
                        ignore_engine_warnings,
                    ]
                )

            await self.schema_release.initialize(
                yaml=self.yaml,
                client=self.client,
                source_dir_path=self.base_path,
                plan_only=self.plan_only,
                is_same_org_deploy=self.is_same_org_deploy,
                parent_queue=self,
                last_deploy_timestamp=self.last_deploy_timestamp,
                force_deploy=self.force_deploy,
                ignore_timestamp_mismatches=self.ignore_timestamp_mismatches,
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
                    remove_queue_attributes_for_cross_org(queue_copy=queue_copy)

                previous_workspace_url = queue_copy["workspace"]
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="workspace",
                    source_id_target_pairs=self.workspace_targets,
                )
                new_workspace_id = queue_copy["workspace"].split("/")[-1]

                if previous_workspace_url == queue_copy["workspace"] and not target.id:
                    raise Exception(
                        f'Cannot create target for {self.display_type} "{queue_copy['name']} ({queue_copy['id']})" - there is no target workspace to put it into.'
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
                        f'Cannot create target for {self.display_type} "{queue_copy['name']} ({queue_copy['id']})" - there is no target schema to use it with.'
                    )

                # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
                # We need full target object to be able to handle 'dangling' hooks
                target_queue = await self.find_target_object(target, Resource.Queue)
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="hooks",
                    source_id_target_pairs=self.hook_targets,
                    target_object=target_queue,
                    keep_hook_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
                )
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="webhooks",
                    source_id_target_pairs=self.hook_targets,
                    target_object=target_queue,
                    keep_hook_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
                )

                if not self.overwrite_ignored_fields:
                    # Ignore should preceed attribute override, so that override can win if it is defined
                    await self.ignore_ai_fields(queue=queue_copy, target=target)

                self.overrider.override_attributes_v2(
                    object=queue_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(target_object=queue_copy, target=target)
                release_requests.append(request)

            if self.plan_only:
                results = []
                # Run sequentially when planning because user may have to input things in the CLI
                for request in release_requests:
                    results.append(await request)
            else:
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
                force_deploy=self.force_deploy,
                ignore_timestamp_mismatches=self.ignore_timestamp_mismatches,
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

    async def find_target_object(self, target: Target, type):
        downloader = Downloader(client=self.client)
        objects = await downloader.download_remote_objects(type=type)
        for object_ in objects:
            if object_["id"] == target.id:
                return object_
        return None

    async def verify_subobjects_have_same_target_count(self):
        mismatch_found = False

        queue_targets_len = len(self.targets)
        schema_targets_len = len(self.schema_release.targets)

        if queue_targets_len != schema_targets_len:
            display_error(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its {self.schema_release.display_type} has {schema_targets_len}. Please make the target counts equal."
            )
            mismatch_found = True

        for rule in self.schema_release.rule_releases:
            rule_targets_len = len(rule.targets)
            if queue_targets_len != rule_targets_len:
                display_error(
                    f"{self.display_type} {self.display_label} has {queue_targets_len} targets while one of its [yellow]schema rules[/yellow] ({rule.display_label}) has {rule_targets_len}. Please make the target counts equal."
                )
                mismatch_found = True

        inbox_targets_len = len(self.inbox_release.targets)
        queue_has_inbox = bool(self.data.get("inbox", "")) and self.inbox_release.id
        if queue_has_inbox and queue_targets_len != inbox_targets_len:
            display_error(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its {self.inbox_release.display_type} has {inbox_targets_len}. Please make the target counts equal."
            )
            mismatch_found = True

        if mismatch_found:
            raise SubObjectException(
                "Incorrect inbox/schema target count vs queue target count"
            )

    async def verify_no_unassigned_hooks(self):
        if self.ignore_all_deploy_warnings or self.ignore_deploy_warnings:
            return True

        queue_hook_urls = self.data.get("hooks", [])
        queue_hook_ids = [extract_id_from_url(url) for url in queue_hook_urls]

        deployed_hook_ids = set(self.hook_targets.keys()) | set(self.unselected_hooks)

        for queue_hook_id in queue_hook_ids:
            if queue_hook_id not in deployed_hook_ids:
                display_warning(
                    f"{self.display_type} {self.display_label} depends on hook [purple]{queue_hook_id}[/purple] that is not in the deploy file - is this a new hook created after the deploy file?"
                )
                return await self.prompt_user_about_warnings()

    async def evaluate_workflow_warning(self):
        if (
            self.ignore_all_deploy_warnings
            or self.ignore_deploy_warnings
            or self.is_same_org_deploy
        ):
            return True

        if self.data.get("workflows", []):
            display_warning(
                f"{self.display_type} {self.display_label} has 'workflows' defined. Please make sure to create and assign them manually for the target."
            )
            return await self.prompt_user_about_warnings()

    async def evaluate_engine_warning(self):
        for attr in QUEUE_ENGINE_ATTRIBUTES:
            if (
                self.ignore_all_deploy_warnings
                or self.ignore_deploy_warnings
                or self.is_same_org_deploy
            ):
                return True

            if self.data.get(attr, None):
                display_warning(
                    f"{self.display_type} {self.display_label} has '{attr}' defined. Please make sure to create and assign it manually for the target."
                )
                return await self.prompt_user_about_warnings()

    async def prompt_user_about_warnings(
        self, message="Do you want to disable warnings like this for this queue?"
    ):
        user_answer = await questionary.text(
            message=message,
            instruction="(y/n/yy)",
        ).ask_async()
        # Disable warnings for all other queues
        if user_answer.casefold() == "yy":
            self.ignore_all_deploy_warnings = True
            return True

        return user_answer == "y"

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

    async def ignore_ai_fields(self, queue: dict, target: Target):
        # Object was not deployed to this target yet -> no AI fields to preserve in target
        if not target.id:
            return

        try:
            target_queue = await self.client.retrieve_queue(target.id)
            queue["automation_enabled"] = target_queue.automation_enabled
            queue["automation_level"] = target_queue.automation_level
            queue["default_score_threshold"] = target_queue.default_score_threshold

            queue.get("settings", {})["columns"] = target_queue.settings.get(
                "columns", []
            )
            queue.get("settings", {})["annotation_list_table"] = (
                target_queue.settings.get("annotation_list_table", {})
            )

        except Exception as e:
            raise Exception(f"Error while ignoring queue AI fields") from e
