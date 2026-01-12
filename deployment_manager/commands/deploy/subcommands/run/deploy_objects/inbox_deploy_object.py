from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)

from rossum_api.domain_logic.resources import Resource


class InboxDeployObject(DeployObject):
    type: Resource = Resource.Inbox
    name: str = ""

    parent_queue: DeployObject = None

    async def initialize_deploy_object(self, deploy_file, parent_queue):
        # Must come first!
        self.parent_queue = parent_queue
        # dynamic property caused issues in some function calls
        self.name = self.parent_queue.name
        await super().initialize_deploy_object(deploy_file)

    async def initialize_target_object_data(self, data, target):
        if "name" not in target.attribute_override:
            # Use the target queue's name for the schema unless user specified explicit schema.name override
            parent_target = self.parent_queue.targets[target.index]
            parent_name_override = parent_target.attribute_override.get("name", None)
            if parent_name_override:
                target.attribute_override["name"] = parent_name_override
            else:
                data["name"] = self.name

        # Should either create a new one or it is already present
        data.pop("email", None)

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)
        # previous_queue_urls = data.get("queues", [])

        # There must be a single queue in this list, we do not persist target-only ('dangling') references
        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="queues",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Queue,
            use_dummy_references=use_dummy_references,
        )

        # if previous_queue_urls == data["queues"] and not target.id:
        #     raise Exception(
        #         f"Cannot create target for {self.display_type} {self.display_label} - there is no target queue to associate it with."
        #     )

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "inbox.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("inbox", {})
