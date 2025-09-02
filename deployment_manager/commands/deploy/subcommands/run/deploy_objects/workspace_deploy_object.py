from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from rossum_api.api_client import Resource

from deployment_manager.utils.functions import templatize_name_id


class WorkspaceDeployObject(DeployObject):
    type: Resource = Resource.Workspace

    @property
    def path(self) -> Path:
        return (
            Path(self.deploy_file.source_dir_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "workspace.json"
        )

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)
        data["organization"] = self.deploy_file.target_org.url

        # TODO: 1 workspace target with 2 queue targets -> one dep URL needs multiplying
        # ! This will require per-object-type logic of replacing deps, no general rules exist
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
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="queues"
        )
