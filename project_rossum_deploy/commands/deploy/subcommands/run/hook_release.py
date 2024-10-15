from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    override_attributes_v2,
)
from rich import print
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from project_rossum_deploy.commands.deploy.subcommands.run.upload_helpers import (
    create_hook_based_on_template,
    create_hook_without_template,
)
from project_rossum_deploy.commands.migrate.hooks import update_hook_code
from project_rossum_deploy.utils.consts import (
    PrdVersionException,
    display_error,
    settings,
)


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy


class HookRelease(ObjectRelease):
    type: Resource = Resource.Hook
    token_owner_id: int = None

    async def initialize(self, yaml, client, token_owner_id, source_dir_path):
        await super().initialize(yaml, client, source_dir_path)
        self.token_owner_id = token_owner_id

    async def deploy(self):
        try:
            self.data["run_after"] = []
            self.data["queues"] = []

            # TODO: how to remember across releases? Put into deploy file?

            # Change token owner to TARGET user (important for cross-org migrations)
            if not settings.IS_PROJECT_IN_SAME_ORG:
                self.data["token_owner"] = (
                    settings.TARGET_API_URL + f"/users/{self.token_owner_id}"
                )

            await update_hook_code(self.path, self.data)

            release_requests = []
            for target in self.targets:
                hook_copy = deepcopy(self.data)
                override_attributes_v2(
                    object=hook_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(object=hook_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id

        except PrdVersionException as e:
            raise e
        except Exception as e:
            display_error(
                f"Error while migrating hook {self.name} ({self.path}): {e}", e
            )

    async def create_remote(self, object: dict, target: Target):
        try:
            result = await create_hook_based_on_template(
                hook=object, client=self.client
            )
            if not result:
                # TODO: include a missing private hook url in the plan as a warning
                result = await create_hook_without_template(
                    hook=object,
                    client=self.client,
                    hook_mapping={"attribute_override": target.attribute_override},
                )
            print(
                f'Released (created) hook "{object['name']} ({object['id']})" -> "{result['id']}".'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while creating hook "{object['name']} ({object['id']})":', e
            )
            return {}
