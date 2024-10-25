import questionary
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    AttributeOverrideException,
    override_attributes_v2,
)
from rich import print as pprint
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)

from project_rossum_deploy.commands.migrate.hooks import update_hook_code
from project_rossum_deploy.utils.consts import (
    display_error,
)


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy

from project_rossum_deploy.utils.functions import extract_id_from_url


class HookRelease(ObjectRelease):
    type: Resource = Resource.Hook
    token_owner_id: int = None
    source_client: ElisAPIClient = None
    hook_template_url: str = None

    async def initialize(
        self,
        yaml,
        client,
        source_client,
        token_owner_id,
        source_dir_path,
        plan_only,
        is_same_org_deploy,
        hook_template_url,
    ):
        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
            is_same_org_deploy=is_same_org_deploy,
        )
        self.source_client = source_client
        self.token_owner_id = token_owner_id
        if not self.hook_template_url:
            self.hook_template_url = hook_template_url
        await update_hook_code(self.path, self.data)

    async def deploy(self):
        try:
            if self.plan_only and self.is_creating_targets:
                self.hook_template_url = await self.find_template_for_hook()

            release_requests = []
            for target in self.targets:
                hook_copy = deepcopy(self.data)
                hook_copy["run_after"] = []
                hook_copy["queues"] = []

                # Change token owner to TARGET user (important for cross-org migrations)
                if not self.is_same_org_deploy:
                    hook_copy["token_owner"] = (
                        self.client._http_client.base_url
                        + f"/users/{self.token_owner_id}"
                    )

                override_attributes_v2(
                    object=hook_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(target_object=hook_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id
        except AttributeOverrideException as e:
            display_error(
                f"Error while migrating {self.display_type} {self.display_label}: {e}",
            )
            self.deploy_failed = True
        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}) ^",
                e,
            )
            self.deploy_failed = True

    async def create_remote(self, target_object: dict, target: Target):
        try:
            if self.plan_only:
                result = deepcopy(target_object)
                result_id = self.create_plan_target_object_id(target_object["id"])
                result["url"] = result["url"].replace(str(result["id"]), str(result_id))
                result["id"] = result_id
            else:
                result = await self.create_hook_with_known_template(hook=target_object)
                if not result:
                    result = await self.create_hook_without_known_template(
                        hook=target_object,
                    )

            pprint(
                f'{self.PLAN_PRINT_STR if self.plan_only else ''} {self.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while creating {self.display_type} "{self.name} ({self.id})" ^',
                e,
            )
            self.deploy_failed = True
            return {}

    async def create_hook_without_known_template(self, hook: dict):
        return await self.client._http_client.create(self.type, hook)

    async def get_hook_template_from_user(self, hook_templates: list):
        # Use only for private webhooks

        if self.data.get("type", None) != "function" and self.data.get(
            "config", {}
        ).get("private", None):
            template_choices = [
                questionary.Choice(title=template["name"], value=template["url"])
                for template in hook_templates
            ]
            template_choices = sorted(template_choices, key=lambda choice: choice.title)
            template_choices.append(questionary.Choice(title="N/A", value=None))
            template_url = await questionary.select(
                f"Please select template for hook {self.name} ({self.id}):",
                choices=template_choices,
            ).ask_async(patch_stdout=True)

            return template_url

    async def create_hook_with_known_template(self, hook: dict):
        if not self.hook_template_url:
            return None

        hook["hook_template"] = self.hook_template_url

        # if self.is_same_org_deploy:
        #     # Some of the properties (e.g., url) are not in the json, but are required by the API
        #     hook.pop("config", None)
        #     return await self.client._http_client.request_json(
        #         "POST", url="hooks/create", json=hook
        #     )

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
            resource=self.type, id_=created_hook["id"], data=hook
        )

    async def find_template_for_hook(self):
        if self.data.get("hook_template", None) and self.is_same_org_deploy:
            return self.data["hook_template"]

        target_hook_template_match = None
        target_hook_templates = [
            item
            async for item in self.client._http_client.fetch_all_by_url(
                "hook_templates"
            )
        ]

        if self.data.get("hook_template", None):
            # Hook template ids might differ inbetween orgs
            # We try to find the corresponding template by comparing names
            # If no match is found, this hook will be processed as if the hook_template was not there at all
            template_id = extract_id_from_url(self.data["hook_template"])
            source_hook_template = await self.source_client.request_json(
                "GET", f"hook_templates/{template_id}"
            )

            for target_template in target_hook_templates:
                if target_template["name"] == source_hook_template["name"]:
                    target_hook_template_match = target_template
                    break

        # TODO: artifical test of hook template names not matching (letting user choose)
        if not target_hook_template_match:
            target_hook_template_match = await self.get_hook_template_from_user(
                hook_templates=target_hook_templates
            )

        return target_hook_template_match
