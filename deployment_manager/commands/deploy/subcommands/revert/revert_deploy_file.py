from pydantic import BaseModel, ConfigDict
from rich import print as pprint
from rich.panel import Panel
from rossum_api import APIClientError, AsyncRossumAPIClient

from deployment_manager.commands.deploy.subcommands.revert.revert_object_deploy import (
    RevertEmailTemplateDeploy,
    RevertEngineDeploy,
    RevertHookDeploy,
    RevertLabelDeploy,
    RevertObjectDeploy,
    RevertQueueDeploy,
    RevertRuleDeploy,
    RevertWorkspaceDeploy,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.run.models import DeployException
from deployment_manager.utils.consts import display_error, settings
from deployment_manager.utils.functions import gather_with_concurrency


class RevertDeployFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    plan_only: bool = False

    deployed_org_id: int | None = ""

    client: AsyncRossumAPIClient
    yaml: DeployYaml

    workspaces: list[RevertWorkspaceDeploy] = []
    queues: list[RevertQueueDeploy] = []
    hooks: list[RevertHookDeploy] = []
    engines: list[RevertEngineDeploy] = []
    rules: list[RevertRuleDeploy] = []
    labels: list[RevertLabelDeploy] = []
    email_templates: list[RevertEmailTemplateDeploy] = []

    async def display_reverted_organization(self):
        if not self.deployed_org_id:
            raise DeployException(f"No {settings.DEPLOY_KEY_DEPLOYED_ORG_ID} found in the deploy file.")

        try:
            target_org = await self.client.retrieve_organization(self.deployed_org_id)
            pprint(Panel(f"Deleting targets from {target_org.name} ({target_org.id})"))
        except APIClientError as e:
            if e.status_code == 404:
                display_error(
                    f'Organization with ID "{self.deployed_org_id}" not found with the specified token in {self.client._http_client.base_url}. Please make sure you have to correct token and target URL.'
                )
                return

    async def revert_hooks(self):
        await gather_with_concurrency(
            *[
                hook_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for hook_release in self.hooks
            ]
        )

        await gather_with_concurrency(*[hook_release.revert() for hook_release in self.hooks])
        self.detect_revert_phase_exceptions(self.hooks)

    async def revert_email_templates(self):
        await gather_with_concurrency(
            *[
                email_template_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for email_template_release in self.email_templates
            ]
        )

        await gather_with_concurrency(
            *[email_template_release.revert() for email_template_release in self.email_templates]
        )
        self.detect_revert_phase_exceptions(self.email_templates)

    async def revert_engines(self):
        await gather_with_concurrency(
            *[
                engine_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for engine_release in self.engines
            ]
        )

        await gather_with_concurrency(*[engine_release.revert() for engine_release in self.engines])
        self.detect_revert_phase_exceptions(self.engines)

    async def revert_rules(self):
        await gather_with_concurrency(
            *[
                rule_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for rule_release in self.rules
            ]
        )

        await gather_with_concurrency(*[rule_release.revert() for rule_release in self.rules])
        self.detect_revert_phase_exceptions(self.rules)

    async def revert_labels(self):
        await gather_with_concurrency(
            *[
                label_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for label_release in self.labels
            ]
        )

        await gather_with_concurrency(*[label_release.revert() for label_release in self.labels])
        self.detect_revert_phase_exceptions(self.labels)

    async def revert_workspaces(self):
        await gather_with_concurrency(
            *[
                workspace_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for workspace_release in self.workspaces
            ]
        )

        await gather_with_concurrency(*[workspace_release.revert() for workspace_release in self.workspaces])
        self.detect_revert_phase_exceptions(self.workspaces)

    async def revert_queues(self):
        await gather_with_concurrency(
            *[
                queue_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    plan_only=self.plan_only,
                )
                for queue_release in self.queues
            ]
        )

        await gather_with_concurrency(*[queue_release.revert() for queue_release in self.queues])
        self.detect_revert_phase_exceptions(self.queues)

    def detect_revert_phase_exceptions(self, releases: list[RevertObjectDeploy]):
        for release in releases:
            if release.revert_failed:
                raise DeployException(
                    f"Revert of {release.display_type} {release.display_label} failed, see error details above."
                )
