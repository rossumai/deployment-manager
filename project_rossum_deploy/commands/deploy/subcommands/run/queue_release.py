import asyncio
from copy import deepcopy

from anyio import Path
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    Target,
)
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    override_attributes_v2,
)
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)


from rossum_api.api_client import Resource

from project_rossum_deploy.commands.migrate.helpers import replace_dependency_url
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import display_error
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
    templatize_name_id,
)


class InboxRelease(ObjectRelease):
    type: Resource = Resource.Inbox
    queue_id: int
    queue_targets: list[Target]

    # Override parent object method
    async def initialize(self): ...

    def prepare_object_copy_for_deploy(self, target: Target):
        inbox_copy = deepcopy(self.data)
        # Should either create a new one or it is already present
        inbox_copy.pop("email", None)
        # Name target inbox as its target queue (includes attribute override of the queue's name)
        inbox_copy["name"] = target.data["name"]
        return inbox_copy

    async def prepare_inbox_target(self, queue_target: Target):
        """Target needs to be created on the fly because it is not in the deploy file"""
        target_inbox_url = queue_target.data.get("inbox", None)
        # No URL when planning also happens when the queue is updated
        # Check if there is an inbox and report it would be updated
        plan_object_updated = not self.check_plan_object_id(queue_target.id)
        if not target_inbox_url and self.plan_only and plan_object_updated:
            target_queue_from_remote = await self.client.retrieve_queue(queue_target.id)
            target_inbox_url = target_queue_from_remote.inbox

        target_inbox_id = (
            extract_id_from_url(target_inbox_url) if target_inbox_url else None
        )
        return Target(id=target_inbox_id)

    async def deploy(self):
        try:
            for target_index, queue_target in enumerate(self.queue_targets):
                inbox_copy = self.prepare_object_copy_for_deploy(target=queue_target)
                previous_queue_urls = inbox_copy.get("queues", [])
                replace_dependency_url(
                    object=inbox_copy,
                    dependency="queues",
                    target_index=target_index,
                    target_objects_count=len(self.targets),
                    source_id_target_pairs={
                        self.queue_id: [target.data for target in self.queue_targets]
                    },
                )

                target_inbox = await self.prepare_inbox_target(queue_target)
                if previous_queue_urls == inbox_copy["queues"] and not target_inbox.id:
                    display_error(
                        f'Cannot create target for {self.display_type} "{inbox_copy['name']} ({inbox_copy['id']})" - there is no target queue to associate it with.'
                    )
                    return

                await self.upload(
                    target_object=inbox_copy,
                    target=target_inbox,
                )

        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}): ^",
                e,
            )


class QueueRelease(ObjectRelease):
    type: Resource = Resource.Queue

    inbox: InboxRelease = None

    workspace_targets: dict[int, list] = []
    schema_targets: dict[int, list] = []
    hook_targets: dict[int, list] = []

    async def initialize(
        self,
        yaml,
        client,
        source_dir_path,
        plan_only,
        workspace_targets: dict[int, list],
        schema_targets: dict[int, list],
        hook_targets: dict[int, list],
    ):
        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
        )
        self.workspace_targets = workspace_targets
        self.schema_targets = schema_targets
        self.hook_targets = hook_targets

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "queue.json"
        )

    @property
    def inbox_path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "inbox.json"
        )

    async def deploy(self):
        try:
            release_requests = []
            target_objects_count = len(self.targets)
            for target_index, target in enumerate(self.targets):
                queue_copy = deepcopy(self.data)
                queue_copy.pop("inbox", None)

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
                )
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="webhooks",
                    source_id_target_pairs=self.hook_targets,
                )

                override_attributes_v2(
                    object=queue_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(target_object=queue_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id

            if not await self.inbox_path.exists():
                return

            inbox_data = await read_json(self.inbox_path)
            self.inbox = InboxRelease(
                plan_only=self.plan_only,
                id=inbox_data["id"],
                name=inbox_data["name"],
                data=inbox_data,
                queue_id=self.id,
                client=self.client,
                queue_targets=self.targets,
            )
            await self.inbox.deploy()

        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}): {e}",
                e,
            )
