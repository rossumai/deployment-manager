import questionary
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    override_attributes_v2,
)
from rich import print
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)

from project_rossum_deploy.commands.migrate.hooks import update_hook_code
from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.utils.consts import (
    PrdVersionException,
    display_error,
    display_warning,
    settings,
)


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy

from project_rossum_deploy.utils.functions import extract_id_from_url


class HookRelease(ObjectRelease):
    type: Resource = Resource.Hook
    token_owner_id: int = None

    async def initialize(self, yaml, client, token_owner_id, source_dir_path):
        await super().initialize(yaml, client, source_dir_path)
        await update_hook_code(self.path, self.data)
        self.token_owner_id = token_owner_id

    async def deploy(self):
        try:
            release_requests = []
            for target in self.targets:
                hook_copy = deepcopy(self.data)
                hook_copy["run_after"] = []
                hook_copy["queues"] = []

                # Change token owner to TARGET user (important for cross-org migrations)
                if not settings.IS_PROJECT_IN_SAME_ORG:
                    hook_copy["token_owner"] = (
                        settings.TARGET_API_URL + f"/users/{self.token_owner_id}"
                    )

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
            result = await self.create_hook_based_on_template(hook=object)
            if not result:
                # TODO: include a missing private hook url in the plan as a warning
                result = await self.create_hook_without_template(
                    hook=object,
                    target=target,
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

    async def create_hook_without_template(self, hook: dict, target: Target):
        # Use the dummy URL only for newly-created private hooks
        # And only if attribute override does not specify the url
        if (
            hook.get("type", None) != "function"
            and hook.get("config", {}).get("private", None)
            and target.attribute_override.get("config", {}).get("path", "") != "url"
        ):
            private_hook_url = await questionary.text(
                f"Please provide hook url (target base_url is '{self.client._http_client.base_url}') for '{hook['name']}':"
            ).ask_async()
            hook["config"]["url"] = (
                private_hook_url
                if private_hook_url
                else settings.PRIVATE_HOOK_DUMMY_URL
            )

        return await self.client._http_client.create(Resource.Hook, hook)

    async def create_hook_based_on_template(self, hook: dict):
        if not hook.get("hook_template", None):
            return None

        if settings.IS_PROJECT_IN_SAME_ORG:
            # Some of the properties (e.g., url) are not in the json, but are required by the API
            hook.pop("config", None)
            return await self.client._http_client.request_json(
                "POST", url="hooks/create", json=hook
            )
        else:
            # TODO: support other source dir names
            # Client is different in case of cross-org migrations
            try:
                source_client = await create_and_validate_client(
                    destination=settings.SOURCE_DIRNAME
                )
            except Exception:
                display_warning(
                    f"Invalid credentials for {settings.SOURCE_DIRNAME}, hooks will be created not based on their template."
                )
                return None

            # Hook template ids might differ in between orgs
            # We try to find the corresponding template by comparing names
            # If no match is found, this hook will be processed as if the hook_template was not there at all
            template_id = extract_id_from_url(hook["hook_template"])
            source_hook_template = await source_client.request_json(
                "GET", f"hook_templates/{template_id}"
            )

            target_hook_templates = [
                item
                async for item in self.client._http_client.fetch_all_by_url(
                    "hook_templates"
                )
            ]
            target_hook_template_match = None
            for target_template in target_hook_templates:
                if target_template["name"] == source_hook_template["name"]:
                    target_hook_template_match = target_template
                    break

            if not target_hook_template_match:
                return None

            hook["hook_template"] = target_hook_template_match["url"]

            initial_fields = ["name", "hook_template", "token_owner", "events"]
            create_payload = {
                **{k: hook[k] for k in initial_fields},
                "queues": [],
            }
            created_hook = await self.client._http_client.request_json(
                "POST", url="hooks/create", json=create_payload
            )

            # In case the hook became private, remove conflicting fields
            if created_hook.get("config", {}).get("private", False):
                fields_to_remove = [
                    "code",
                    "third_party_library_pack",
                    "runtime",
                    "private",
                ]
                hook_config = hook.get("config", {})
                for field in fields_to_remove:
                    hook_config.pop(field, None)

            # Do not try patching the type of extension in case it changed (e.g., SF to lambda)
            hook.pop("type", None)

            return await self.client._http_client.update(
                resource=Resource.Hook, id_=created_hook["id"], data=hook
            )
