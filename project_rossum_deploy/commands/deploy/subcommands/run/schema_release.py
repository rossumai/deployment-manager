from anyio import Path
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from project_rossum_deploy.commands.migrate.schemas import update_formula_fields_code
from project_rossum_deploy.utils.consts import display_error


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy


class SchemaRelease(ObjectRelease):
    type: Resource = Resource.Schema
    name: str = ""

    parent_queue: ObjectRelease = None

    async def initialize(
        self, yaml, client, source_dir_path, plan_only, is_same_org_deploy, parent_queue
    ):
        self.parent_queue = parent_queue
        # dynamic property caused issues in some function calls
        self.name = f"schema:{self.parent_queue.name}"

        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
            is_same_org_deploy=is_same_org_deploy,
        )

        await update_formula_fields_code(self.path, self.data)

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "schema.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("schema", {})

    def prepare_object_copy_for_deploy(self, target: Target):
        schema_copy = deepcopy(self.data)
        schema_copy["queues"] = []
        self.overrider.override_attributes_v2(
            object=schema_copy, attribute_overrides=target.attribute_override
        )

        return schema_copy

    async def deploy(self):
        try:
            release_requests = []
            for target in self.targets:
                schema_copy = self.prepare_object_copy_for_deploy(target=target)

                request = self.upload(target_object=schema_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            self.update_targets(results)
        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}) ^",
                e,
            )
            self.deploy_failed = True
