from typing import TYPE_CHECKING

from anyio import Path

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.utils.functions import templatize_name_id
from rossum_api.api_client import Resource

if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_objects.engine_deploy_object import (
        EngineDeployObject,
    )


class EngineFieldDeployObject(DeployObject):
    type: Resource = Resource.EngineField
    parent_engine: "EngineDeployObject" = None

    async def initialize_deploy_object(self, deploy_file, parent_engine=None):
        if parent_engine:
            self.parent_engine = parent_engine
        await super().initialize_deploy_object(deploy_file)

    def get_object_in_yaml(self):
        if not self.parent_engine or not self.parent_engine.yaml_reference:
            return None
        engine_fields = self.parent_engine.yaml_reference.get("engine_fields", [])
        for engine_field in engine_fields:
            if engine_field.get("id") == self.id:
                return engine_field
        return None

    def update_targets(self):
        for target in self.targets:
            if target.data_from_remote and (new_id := target.data_from_remote.get("id", None)):
                target.id = new_id
                if self.yaml_reference:
                    self.yaml_reference["targets"][target.index]["id"] = target.id
                    self.yaml_reference["targets"][target.index]["attribute_override"] = target.attribute_override

    @property
    def path(self) -> Path:
        if self.parent_engine:
            return self.parent_engine.path.parent / "engine_fields" / f"{templatize_name_id(self.name, self.id)}.json"
        return (
            Path(self.deploy_file.source_dir_path) / "engine_fields" / f"{templatize_name_id(self.name, self.id)}.json"
        )

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        data = getattr(target, data_attribute)

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="engine",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Engine,
            use_dummy_references=use_dummy_references,
        )
