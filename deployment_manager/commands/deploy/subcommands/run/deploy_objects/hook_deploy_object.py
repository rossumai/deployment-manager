from copy import deepcopy

import questionary
from rich import print as pprint

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.hook_reference_replacer import (
    HookReferenceReplacer,
)
from deployment_manager.commands.deploy.subcommands.run.merge.merge import get_nested_value, prompt_conflict_resolution
from deployment_manager.commands.deploy.subcommands.run.models import Target
from deployment_manager.common.read_write import write_str
from deployment_manager.utils.consts import display_error, settings
from deployment_manager.utils.functions import extract_id_from_url, templatize_name_id
from rossum_api.api_client import Resource


class HookDeployObject(DeployObject):
    type: Resource = Resource.Hook
    ref_replacer: HookReferenceReplacer = None
    hook_template_url: str = None
    secrets: dict = {}

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)
        # Overwrites default ref_replacer
        self.ref_replacer = HookReferenceReplacer(self)

        self.hook_template_url = (deploy_file.hook_templates.get(self.id, None),)
        self.secrets = deploy_file.secrets.get(templatize_name_id(self.name, self.id), {})
        await self.update_hook_code()

        if self.is_creating_targets:
            self.hook_template_url = await self.find_template_for_hook()

    async def initialize_target_object_data(self, data: dict, target: Target):
        if self.secrets:
            data["secrets"] = self.secrets

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        data = getattr(target, data_attribute)
        # Change token owner to TARGET user (important for cross-org migrations or per-hook override)
        token_owner_override = target.attribute_override.get("token_owner")
        if token_owner_override:
            data["token_owner"] = token_owner_override
        elif not self.deploy_file.is_same_org:
            data["token_owner"] = (
                self.deploy_file.client._http_client.base_url + f"/users/{self.deploy_file.token_owner_id}"
            )

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
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="queues"
        )

        data["run_after"] = await self.ref_replacer.replace_hook_run_after_list(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            use_dummy_references=use_dummy_references,
        )
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="run_after"
        )

    async def create_remote(self, data_attribute: str, target: Target):
        try:
            data = getattr(target, data_attribute)

            result = await self.create_hook_with_known_template(hook=data)
            if not result:
                result = await self.create_hook_without_known_template(
                    hook=data,
                )

            # Remember last_applied only if the API call succeeds
            target.last_applied_data = self.scrub_attributes(data)
            target.data_from_remote = result
            target.update_after_first_create()

            pprint(f"{settings.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.")
            return result
        except Exception as e:
            display_error(
                f"Error while creating {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True
            return {}

    def scrub_attributes(self, data):
        data_copy = deepcopy(data)
        data_copy.pop("secrets", None)
        return data_copy

    async def create_hook_without_known_template(self, hook: dict):
        return await self.deploy_file.client._http_client.create(self.type, hook)

    async def get_hook_template_from_user(self, hook_templates: list):
        # Use only for private webhooks

        if self.data.get("type", None) != "function" and self.data.get("config", {}).get("private", None):
            template_choices = [
                questionary.Choice(title=template["name"], value=template["url"]) for template in hook_templates
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
        created_hook = await self.deploy_file.client._http_client.request_json(
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

        return await self.deploy_file.client._http_client.update(resource=self.type, id_=created_hook["id"], data=hook)

    async def find_template_for_hook(self):
        if self.data.get("hook_template", None) and self.deploy_file.is_same_org:
            return self.data["hook_template"]

        target_hook_template_match_url = None
        target_hook_templates = [
            item async for item in self.deploy_file.client._http_client.fetch_all_by_url("hook_templates")
        ]

        if self.data.get("hook_template", None):
            # Hook template ids might differ inbetween orgs
            # We try to find the corresponding template by comparing names
            # If no match is found, this hook will be processed as if the hook_template was not there at all
            template_id = extract_id_from_url(self.data["hook_template"])
            source_hook_template = await self.deploy_file.source_client.request_json(
                "GET", f"hook_templates/{template_id}"
            )

            for target_template in target_hook_templates:
                if target_template["name"] == source_hook_template["name"]:
                    target_hook_template_match_url = target_template["url"]
                    break

        # TODO: artifical test of hook template names not matching (letting user choose)
        if not target_hook_template_match_url:
            target_hook_template_match_url = await self.get_hook_template_from_user(
                hook_templates=target_hook_templates
            )

        return target_hook_template_match_url

    async def update_hook_code(self):
        """Checks if there is not newer code in the associated file and uses that for release.
        The original hook file is not modified.
        """
        if self.data.get("extension_source", "") != "rossum_store" and (self.data.get("config", {}).get("code", None)):
            suffix = ".py" if "python" in self.data["config"].get("runtime") else ".js"
            code_path = self.path.with_suffix(suffix)
            new_code = await code_path.read_text()
            self.data["config"]["code"] = new_code

    async def resolve_code_conflict(self, attribute_path: str, last_applied: dict, target_val: str):
        if attribute_path != "config.code":
            return False

        suffix = ".py" if "python" in self.data["config"].get("runtime") else ".js"
        code_path = self.path.with_suffix(suffix)

        last_applied_code = get_nested_value(last_applied, attribute_path)

        await prompt_conflict_resolution(
            target_str=target_val,
            last_applied_str=last_applied_code,
            object_path=code_path,
        )

        return True

    async def apply_code_rebase(self, attribute_path, target_val):
        if attribute_path != "config.code":
            return False

        suffix = ".py" if "python" in self.data["config"].get("runtime") else ".js"
        code_path = self.path.with_suffix(suffix)

        await write_str(code_path, target_val)

        return True
