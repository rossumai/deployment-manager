import asyncio
from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    PathNotFoundException,
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

    async def initialize(self, queue_targets, parent_queue, **kwargs):
        try:
            self.queue_targets = queue_targets
            self.parent_queue = parent_queue
            # dynamic property caused issues in some function calls
            self.name = self.parent_queue.name

            await super().initialize(**kwargs)
        except Exception as e:
            display_error(
                f"Error while initializing {self.display_type} {self.display_label}: {e}",
                None if isinstance(e, PathNotFoundException) else e,
            )
            self.initialize_failed = True

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "inbox.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("inbox", {})

    def prepare_object_copy_for_deploy(self, target: Target, target_index: int):
        target_queue = self.parent_queue.targets[target_index]

        inbox_copy = deepcopy(self.data)
        override_copy = deepcopy(target.attribute_override)

        if "name" not in override_copy:
            # Use the target queue's name for the schema unless user specified explicit schema.name override
            parent_name_override = target_queue.attribute_override.get("name", None)
            if parent_name_override:
                override_copy["name"] = parent_name_override
            else:
                inbox_copy["name"] = self.name

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
        if previous_queue_urls == inbox_copy["queues"] and not target.id:
            raise Exception(
                f"Cannot create target for {self.display_type} {self.display_label} - there is no target queue to associate it with."
            )
        # TODO
        self.overrider.override_attributes_v2(
            object=inbox_copy, attribute_overrides=override_copy
        )

        return inbox_copy

    async def deploy(self):
        try:
            release_requests = []
            for target_index, target in enumerate(self.targets):
                target.index = target_index

                inbox_copy = self.prepare_object_copy_for_deploy(
                    target=target, target_index=target_index
                )

                request = self.upload(
                    target_object=inbox_copy,
                    target=target,
                )
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            self.update_targets(results)

        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.name} ({self.id}): ^",
                e,
            )
            self.deploy_failed = True
