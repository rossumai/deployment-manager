from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    PathNotFoundException,
    Target,
)
from deployment_manager.commands.migrate.helpers import replace_dependency_url
from deployment_manager.common.read_write import read_formula_file
from deployment_manager.common.schema import find_schema_id
from deployment_manager.utils.consts import CustomResource, display_error, settings


import asyncio
from copy import deepcopy

from deployment_manager.utils.functions import templatize_name_id


class RuleRelease(ObjectRelease):
    type: CustomResource = CustomResource.Rule

    parent_schema: ObjectRelease = None
    schema_targets: list[Target] = []

    async def initialize(self, parent_schema, schema_targets, **kwargs):
        try:
            self.parent_schema = parent_schema
            self.schema_targets = schema_targets

            await super().initialize(**kwargs)
        except Exception as e:
            display_error(
                f"Error while initializing {self.display_type} {self.display_label}: {e}",
                None if isinstance(e, PathNotFoundException) else e,
            )
            self.initialize_failed = True

    @property
    def path(self) -> Path:
        return (
            self.parent_schema.path.parent
            / "rules"
            / f"{templatize_name_id(self.name, self.id)}.json"
        )

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_schema.yaml_reference
        rules = parent_yaml_reference.get("rules", [])
        for rule in rules:
            if rule.get("id", None) == self.id:
                return rule
        return None

    async def deploy(self):
        try:
            release_requests = []
            target_objects_count = len(self.targets)
            for target_index, target in enumerate(self.targets):
                if len(self.parent_schema.targets) < target_index:
                    raise Exception(
                        f"Parent {self.parent_schema.display_type} {self.parent_schema.display_label} of {self.display_type} does not have target with index {target_index}"
                    )

                target.index = target_index

                rule_copy = deepcopy(self.data)
                override_copy = deepcopy(target.attribute_override)

                previous_schema_url = rule_copy["schema"]
                replace_dependency_url(
                    object=rule_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="schema",
                    source_id_target_pairs=self.schema_targets,
                )

                if previous_schema_url == rule_copy["schema"] and not target.id:
                    raise Exception(
                        f'Cannot create target for {self.display_type} "{rule_copy['name']} ({rule_copy['id']})" - there is no target schema to use it with.'
                    )

                self.overrider.override_attributes_v2(
                    object=rule_copy, attribute_overrides=override_copy
                )

                request = self.upload(target_object=rule_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            self.update_targets(results)
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True
