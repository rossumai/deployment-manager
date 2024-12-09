import asyncio
from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from deployment_manager.commands.migrate.helpers import replace_dependency_url
from deployment_manager.utils.consts import display_error


from rossum_api.api_client import Resource


from copy import deepcopy


class InboxRelease(ObjectRelease):
    type: Resource = Resource.Inbox
    name: str = ""

    parent_queue: ObjectRelease = None
    queue_targets: list[Target] = []

    async def initialize(
        self,
        yaml,
        client,
        source_dir_path,
        plan_only,
        is_same_org_deploy,
        queue_targets,
        parent_queue,
    ):
        self.queue_targets = queue_targets
        self.parent_queue = parent_queue
        # dynamic property caused issues in some function calls
        self.name = f"inbox:{self.parent_queue.name}"

        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
            is_same_org_deploy=is_same_org_deploy,
        )

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "inbox.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("inbox", {})

    # async def prepare_inbox_target(self, queue_target: Target):
    #     target_inbox_url = queue_target.data.get("inbox", None)
    #     # No URL when planning also happens when the queue is updated
    #     # Check if there is an inbox and report it would be updated
    #     plan_object_updated = not self.check_plan_object_id(queue_target.id)
    #     if not target_inbox_url and self.plan_only and plan_object_updated:
    #         target_queue_from_remote = await self.client.retrieve_queue(queue_target.id)
    #         target_inbox_url = target_queue_from_remote.inbox

    #     target_inbox_id = (
    #         extract_id_from_url(target_inbox_url) if target_inbox_url else None
    #     )
    #     return Target(id=target_inbox_id)

    async def deploy(self):
        try:
            release_requests = []
            for target_index, target in enumerate(self.targets):
                inbox_copy = deepcopy(self.data)
                # Should either create a new one or it is already present
                inbox_copy.pop("email", None)

                previous_queue_urls = inbox_copy.get("queues", [])
                replace_dependency_url(
                    object=inbox_copy,
                    dependency="queues",
                    target_index=target_index,
                    target_objects_count=len(self.targets),
                    source_id_target_pairs=self.queue_targets,
                )

                self.overrider.override_attributes_v2(
                    object=inbox_copy, attribute_overrides=target.attribute_override
                )

                if previous_queue_urls == inbox_copy["queues"] and not target.id:
                    display_error(
                        f"Cannot create target for {self.display_type} {self.display_label} - there is no target queue to associate it with."
                    )
                    return

                request = self.upload(
                    target_object=inbox_copy,
                    target=target,
                )
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            self.update_targets(results)

        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}): ^",
                e,
            )
