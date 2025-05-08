from anyio import Path
from pydantic import Field
from deployment_manager.commands.deploy.subcommands.run.models import SubObjectException
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    PathNotFoundException,
    Target,
)
from deployment_manager.commands.deploy.subcommands.run.rule_release import RuleRelease
from deployment_manager.common.read_write import (
    find_fields_in_schema,
    create_formula_directory_path,
    read_formula_file,
)
from deployment_manager.common.schema import find_schema_id
from deployment_manager.utils.consts import display_error, settings


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy

from deployment_manager.utils.functions import templatize_name_id


class SchemaRelease(ObjectRelease):
    type: Resource = Resource.Schema
    name: str = ""

    overwrite_ignored_fields: bool = False

    rule_releases: list[RuleRelease] = Field(default_factory=lambda: [], alias="rules")

    parent_queue: ObjectRelease = None

    async def initialize(self, parent_queue, **kwargs):
        try:
            self.parent_queue = parent_queue
            # dynamic property caused issues in some function calls
            self.name = self.parent_queue.name

            await super().initialize(**kwargs)

            await self.update_formula_fields_code()
        except Exception as e:
            display_error(
                f"Error while initializing {self.display_type} {self.display_label}: {e}",
                None if isinstance(e, PathNotFoundException) else e,
            )
            self.initialize_failed = True

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "schema.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("schema", {})

    async def prepare_object_copy_for_deploy(
        self, target: Target, target_queue: Target
    ):
        schema_copy = deepcopy(self.data)
        override_copy = deepcopy(target.attribute_override)

        if "name" not in override_copy:
            # Use the target queue's name for the schema unless user specified explicit schema.name override
            parent_name_override = target_queue.attribute_override.get("name", None)
            if parent_name_override:
                override_copy["name"] = parent_name_override
            else:
                schema_copy["name"] = self.name

        schema_copy["rules"] = []
        schema_copy["queues"] = []

        if not self.overwrite_ignored_fields:
            # Ignore should preceed attribute override, so that override can win if it is defined
            await self.ignore_schema_ai_fields(schema=schema_copy, target=target)

        self.overrider.override_attributes_v2(
            object=schema_copy, attribute_overrides=override_copy
        )

        return schema_copy

    async def deploy(self):
        try:
            release_requests = []
            for target_index, target in enumerate(self.targets):
                target.index = target_index

                target_queue = self.parent_queue.targets[target.index]
                schema_copy = await self.prepare_object_copy_for_deploy(
                    target=target, target_queue=target_queue
                )

                request = self.upload(target_object=schema_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            self.update_targets(results)

            await asyncio.gather(
                *[
                    rule_release.initialize(
                        yaml=self.yaml,
                        client=self.client,
                        source_dir_path=self.base_path,
                        plan_only=self.plan_only,
                        is_same_org_deploy=self.is_same_org_deploy,
                        parent_schema=self,
                        schema_targets={
                            self.id: [target.data for target in self.targets]
                        },
                        last_deploy_timestamp=self.last_deploy_timestamp,
                        force_deploy=self.force_deploy,
                        ignore_timestamp_mismatches=self.ignore_timestamp_mismatches,
                        source_client=self.source_client,
                    )
                    for rule_release in self.rule_releases
                ]
            )

            for rule_release in self.rule_releases:
                if rule_release.initialize_failed:
                    raise SubObjectException()

            for rule in self.rule_releases:
                await rule.deploy()
                if rule.deploy_failed:
                    raise SubObjectException()

        except SubObjectException:
            self.deploy_failed = True
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True

    async def update_formula_fields_code(self):
        """Checks if there is not newer code in the associated formula fields and uses that for release.
        The original schema file is not modified.
        """
        formula_directory = create_formula_directory_path(self.path)

        if not await formula_directory.exists():
            return

        async for field_file_path in formula_directory.iterdir():
            if not await field_file_path.is_file():
                continue

            formula_code = await read_formula_file(field_file_path)
            formula_name = field_file_path.stem

            schema_id = find_schema_id(self.data["content"], formula_name)
            schema_id["formula"] = formula_code

    async def ignore_schema_ai_fields(self, schema: dict, target: Target):
        DEPLOY_IGNORED_SCHEMA_ATTRIBUTES = [("score_threshold", 1)]

        # Object was not deployed to this target yet -> no AI fields to preserve in target
        if not target.id:
            return

        try:
            target_schema = await self.client.retrieve_schema(target.id)
            schema_ids = find_fields_in_schema(schema['content'])

            for schema_id in schema_ids:
                target_schema_id = find_schema_id(target_schema.content, schema_id["id"])
                if not target_schema_id:
                    continue
                for ignored_field, default_value in DEPLOY_IGNORED_SCHEMA_ATTRIBUTES:
                    schema_id[ignored_field] = target_schema_id.get(ignored_field, default_value)

        except Exception as e:
            raise Exception(f"Error while ignoring schema AI fields") from e
