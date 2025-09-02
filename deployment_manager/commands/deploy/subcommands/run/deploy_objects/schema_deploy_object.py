from anyio import Path
from pydantic import Field
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.rule_deploy_object import (
    RuleDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.models import SubObjectException, Target

from deployment_manager.common.read_write import (
    find_fields_in_schema,
    read_formula_file,
)
from deployment_manager.common.schema import find_schema_id
from deployment_manager.utils.consts import display_error, settings, CustomResource


from rossum_api.api_client import Resource


import asyncio

from deployment_manager.utils.functions import templatize_name_id


class SchemaDeployObject(DeployObject):
    type: Resource = Resource.Schema
    name: str = ""

    overwrite_ignored_fields: bool = False

    rule_deploy_objects: list[RuleDeployObject] = Field(
        default_factory=lambda: [], alias="rules"
    )

    parent_queue: DeployObject = None

    @property
    def path(self) -> Path:
        return self.parent_queue.path.parent / "schema.json"

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("schema", {})

    async def initialize_deploy_object(self, deploy_file, parent_queue):
        # Must come first!
        self.parent_queue = parent_queue
        # dynamic property caused issues in some function calls
        self.name = self.parent_queue.name
        await super().initialize_deploy_object(deploy_file)

        await self.update_formula_fields_code()

        await asyncio.gather(
            *[
                object.initialize_deploy_object(
                    deploy_file=deploy_file, parent_schema=self
                )
                for object in self.rule_deploy_objects
            ]
        )

        for rule in self.rule_deploy_objects:
            if rule.initialize_failed:
                self.initialize_failed = True
                raise SubObjectException()

    # Overrides the parent method
    async def initialize_target_objects(self):
        await super().initialize_target_objects()

        await asyncio.gather(
            *[object.initialize_target_objects() for object in self.rule_deploy_objects]
        )

    async def initialize_target_object_data(self, data: dict, target: Target):
        if "name" not in target.attribute_override:
            # Use the target queue's name for the schema unless user specified explicit schema.name override
            parent_target = self.parent_queue.targets[target.index]
            parent_name_override = parent_target.attribute_override.get("name", None)
            if parent_name_override:
                target.attribute_override["name"] = parent_name_override
            else:
                data["name"] = self.name

        if not self.overwrite_ignored_fields:
            # Ignore should preceed attribute override, so that override can win if it is defined
            await self.use_schema_ai_fields_from_remote(schema=data, target=target)

    async def override_references(self, data_attribute, use_dummy_references):
        await super().override_references(data_attribute, use_dummy_references)

        await asyncio.gather(
            *[
                object.override_references(
                    data_attribute=data_attribute,
                    use_dummy_references=use_dummy_references,
                )
                for object in self.rule_deploy_objects
            ]
        )

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)

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
        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="rules",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=CustomResource.Rule,
            use_dummy_references=use_dummy_references,
        )

        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="queues"
        )
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="rules"
        )

        # Do not send an empty array if it's not an explicit emptying (compared to target)
        if not data.get('rules', []):
            remote_target = await self.get_remote_object(target.id)
            if not remote_target.get('rules', []):
                data.pop('rules', None)

    async def visualize_changes(self):
        await super().visualize_changes()

        for rule in self.rule_deploy_objects:
            await rule.visualize_changes()

    async def deploy_target_objects(self, data_attribute):
        try:
            await super().deploy_target_objects(data_attribute)

            await asyncio.gather(
                *[
                    object.deploy_target_objects(data_attribute=data_attribute)
                    for object in self.rule_deploy_objects
                ]
            )

            for rule in self.rule_deploy_objects:
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

    async def use_schema_ai_fields_from_remote(self, schema: dict, target: Target):
        DEPLOY_IGNORED_SCHEMA_ATTRIBUTES = [("score_threshold", 1)]

        # Object was not deployed to this target yet -> no AI fields to preserve in target
        if not target.exists_on_remote:
            return

        try:
            target_schema = await self.deploy_file.client.retrieve_schema(target.id)
            schema_ids = find_fields_in_schema(schema["content"])

            for schema_id in schema_ids:
                target_schema_id = find_schema_id(
                    target_schema.content, schema_id["id"]
                )
                if not target_schema_id:
                    continue
                if target_schema_id['type'] in ['button']:
                    continue
                for ignored_field, default_value in DEPLOY_IGNORED_SCHEMA_ATTRIBUTES:
                    schema_id[ignored_field] = target_schema_id.get(
                        ignored_field, default_value
                    )

        except Exception as e:
            raise Exception(f"Error while ignoring schema AI fields") from e
