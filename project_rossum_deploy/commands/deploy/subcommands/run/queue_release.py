import asyncio
from copy import deepcopy

from anyio import Path
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    override_attributes_v2,
)
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)


from rossum_api.api_client import Resource

from project_rossum_deploy.commands.migrate.helpers import replace_dependency_url
from project_rossum_deploy.utils.consts import display_error
from project_rossum_deploy.utils.functions import (
    templatize_name_id,
)


class QueueRelease(ObjectRelease):
    type: Resource = Resource.Queue

    ws_path: Path = None

    workspace_targets: dict[int, list] = []
    schema_targets: dict[int, list] = []
    hook_targets: dict[int, list] = []

    async def initialize(
        self,
        yaml,
        client,
        source_dir_path,
        workspace_targets: dict[int, list],
        schema_targets: dict[int, list],
        hook_targets: dict[int, list],
    ):
        await super().initialize(yaml, client, source_dir_path)
        self.workspace_targets = workspace_targets
        self.schema_targets = schema_targets
        self.hook_targets = hook_targets

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "queue.json"
        )

    async def deploy(self):
        try:
            self.data.pop("inbox", None)
            previous_workspace_url = self.data["workspace"]

            # TODO: dangling hook dependency (add back target_object)

            # TODO: inbox release

            release_requests = []
            target_objects_count = len(self.targets)
            for target_index, target in enumerate(self.targets):
                queue_copy = deepcopy(self.data)

                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="workspace",
                    source_id_target_pairs=self.workspace_targets,
                )

                if previous_workspace_url == queue_copy["workspace"] and not target.id:
                    display_error(
                        f'Cannot create target for queue "{queue_copy['id']}" - there is no target workspace to put it into.'
                    )
                    return queue_copy

                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="schema",
                    source_id_target_pairs=self.schema_targets,
                )
                # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="hooks",
                    source_id_target_pairs=self.hook_targets,
                )
                replace_dependency_url(
                    object=queue_copy,
                    target_index=target_index,
                    target_objects_count=target_objects_count,
                    dependency="webhooks",
                    source_id_target_pairs=self.hook_targets,
                )

                override_attributes_v2(
                    object=queue_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(object=queue_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id

        except Exception as e:
            display_error(
                f"Error while migrating hook {self.name} ({self.path}): {e}", e
            )
