from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)

from rossum_api.api_client import Resource


class EngineDeployObject(DeployObject):
    type: Resource = Resource.Engine

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="organization",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Organization,
            use_dummy_references=use_dummy_references,
        )

        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="training_queues",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Queue,
            use_dummy_references=use_dummy_references,
        )

        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="training_queues"
        )
