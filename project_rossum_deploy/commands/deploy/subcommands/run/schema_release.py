from anyio import Path
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from project_rossum_deploy.common.read_write import read_formula_file
from project_rossum_deploy.common.schema import find_schema_id
from project_rossum_deploy.utils.consts import display_error, settings


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy

from project_rossum_deploy.utils.functions import templatize_name_id


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

        await self.update_formula_fields_code()

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

    async def update_formula_fields_code(self):
        """Checks if there is not newer code in the associated formula fields and uses that for release.
        The original schema file is not modified.
        """
        formula_directory = (
            self.path.parent
            / f"{settings.FORMULA_DIR_NAME}{templatize_name_id(self.data['name'], self.data['id'])}"
        )
        if not await formula_directory.exists():
            return

        async for field_file_path in formula_directory.iterdir():
            if not await field_file_path.is_file():
                continue

            formula_code = await read_formula_file(field_file_path)
            formula_name = field_file_path.stem

            schema_id = find_schema_id(self.data["content"], formula_name)
            schema_id["formula"] = formula_code
