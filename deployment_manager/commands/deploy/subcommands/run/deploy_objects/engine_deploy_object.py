from anyio import Path
from pydantic import Field

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.engine_field_deploy_object import (
    EngineFieldDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.models import SubObjectException
from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import templatize_name_id
from rossum_api.api_client import Resource


class EngineDeployObject(DeployObject):
    type: Resource = Resource.Engine
    base_path: str = ""

    engine_field_deploy_objects: list[EngineFieldDeployObject] = Field(default_factory=list, alias="engine_fields")

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)

        for engine_field_object in self.engine_field_deploy_objects:
            await engine_field_object.initialize_deploy_object(
                deploy_file=self.deploy_file,
                parent_engine=self,
            )
            if engine_field_object.initialize_failed:
                self.initialize_failed = True

    @property
    def path(self) -> Path:
        if self.base_path:
            return Path(self.base_path) / "engine.json"
        return (
            Path(self.deploy_file.source_dir_path) / "engines" / templatize_name_id(self.name, self.id) / "engine.json"
        )

    async def initialize_target_objects(self):
        await super().initialize_target_objects()

        for engine_field_object in self.engine_field_deploy_objects:
            await engine_field_object.initialize_target_objects()

    async def override_references(self, data_attribute, use_dummy_references):
        await super().override_references(data_attribute, use_dummy_references)

        for engine_field_object in self.engine_field_deploy_objects:
            await engine_field_object.override_references(
                data_attribute=data_attribute, use_dummy_references=use_dummy_references
            )

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
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

    async def visualize_changes(self):
        await super().visualize_changes()

        for engine_field_object in self.engine_field_deploy_objects:
            await engine_field_object.visualize_changes()

    async def deploy_target_objects(self, data_attribute):
        try:
            await super().deploy_target_objects(data_attribute)

            for engine_field_object in self.engine_field_deploy_objects:
                await engine_field_object.deploy_target_objects(data_attribute=data_attribute)

                if engine_field_object.deploy_failed:
                    raise SubObjectException()
        except SubObjectException:
            self.deploy_failed = True
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True
