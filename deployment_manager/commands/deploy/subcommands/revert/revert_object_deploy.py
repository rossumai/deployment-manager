import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    Target,
    TargetWithDefault,
)
from rich import print as pprint


from anyio import Path
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.commands.deploy.subcommands.run.models import (
    SubObjectException,
)
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    display_warning,
    settings,
)


class NonExistentObjectException(Exception): ...


class RevertObjectDeploy(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource

    yaml: DeployYaml = None
    yaml_reference: dict = None

    client: ElisAPIClient = None

    plan_only: bool = False

    revert_failed: bool = False

    targets: list[TargetWithDefault] = []

    async def initialize(
        self,
        yaml,
        client,
        plan_only=False,
    ):
        self.yaml = yaml
        self.yaml_reference = self.get_object_in_yaml()
        self.plan_only = plan_only
        self.client = client

    async def revert(self):
        try:
            delete_requests = []
            for target_index, target in enumerate(self.targets):
                if not target.id:
                    continue

                target.index = target_index

                request = self.delete_remote(target=target)
                delete_requests.append(request)

            await asyncio.gather(*delete_requests)

            self.delete_target_ids_in_deploy_file()

        except Exception as e:
            display_error(
                f"Error while reverting deploy of {self.display_type} {self.name} ({self.id}) ^",
                e,
            )
            self.revert_failed = True

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self):
        return f'"[green]{self.name}[/green] ([purple]{self.id}[/purple])"'

    def delete_target_ids_in_deploy_file(self):
        for target_index, _ in enumerate(self.targets):
            self.yaml_reference["targets"][target_index]["id"] = None

    def target_display_label(self, name, id):
        return f'"[green]{name}[/green] ([purple]{id}[/purple])"'

    def get_object_in_yaml(self):
        objects = self.yaml.data.get(self.type.value, [])
        for object in objects:
            if object.get("id", None) == self.id:
                return object
        return None

    async def get_remote_object(self, remote_object_id):
        try:
            return await self.client._http_client.fetch_one(self.type, remote_object_id)
        except APIClientError as e:
            if e.status_code == 404:
                raise NonExistentObjectException(
                    f"{self.display_type} [purple]{remote_object_id}[/purple] does not exist on remote."
                ) from None
            raise e

    async def delete_remote(self, target: Target):
        try:
            remote_object = await self.get_remote_object(target.id)

            if not self.plan_only:
                await self.client._http_client.delete(self.type, id_=target.id)

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.DELETE_PRINT_STR} {self.display_type}: {self.target_display_label(remote_object.get('name', 'no-name'), remote_object.get('id', 'no-id'))}"
            )
        except NonExistentObjectException:
            display_warning(
                f"{self.display_type} [purple]{target.id}[/purple] already does not exist on remote."
            )
            self.yaml_reference["targets"][target.index]["id"] = None
        except Exception as e:
            display_error(
                f"Error while deleting {self.display_type} [purple]{target.id}[/purple]: {e}",
                e,
            )
            self.revert_failed = True

    def delete_target_ids(self):
        for target in self.yaml_reference["targets"]:
            target["id"] = None


class EmptyRevertObjectDeploy(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int = None
    name: str = ""
    type: Resource = "no-type"
    base_path: Path = None

    revert_failed: bool = False

    targets: list[TargetWithDefault] = []

    async def initialize(*args, **kwargs): ...

    async def revert(self): ...


class RevertHookDeploy(RevertObjectDeploy):
    type: Resource = Resource.Hook


class RevertWorkspaceDeploy(RevertObjectDeploy):
    type: Resource = Resource.Workspace


class RevertSchemaDeploy(RevertObjectDeploy):
    type: Resource = Resource.Schema
    name: str = ""
    parent_queue: RevertObjectDeploy = None

    async def initialize(self, parent_queue, **kwargs):
        self.parent_queue = parent_queue
        await super().initialize(**kwargs)

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("schema", {})

    async def delete_remote(self, target: Target):
        try:
            await super().delete_remote(target)
        except APIClientError as e:
            if e.status_code == 409:
                display_warning(
                    f"{self.display_type} [purple]{target.id}[/purple] referenced by another queue."
                )


class RevertInboxDeploy(RevertObjectDeploy):
    type: Resource = Resource.Inbox
    name: str = ""
    parent_queue: RevertObjectDeploy = None

    async def initialize(self, parent_queue, **kwargs):
        self.parent_queue = parent_queue
        await super().initialize(**kwargs)

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_queue.yaml_reference
        return parent_yaml_reference.get("inbox", {})


class RevertQueueDeploy(RevertObjectDeploy):
    type: Resource = Resource.Queue

    schema_release: RevertSchemaDeploy = Field(alias="schema")
    inbox_release: Optional[RevertInboxDeploy] = Field(
        default_factory=lambda: EmptyRevertObjectDeploy(), alias="inbox"
    )

    async def ensure_queues_deleted(self):
        if not self.plan_only:
            queue_deleted_count = 0
            while queue_deleted_count != len(self.targets):
                # Deleting queues (even when providing 'delete_after': 0) is asynchronous, wait for a short while
                display_info("Waiting for queues to be deleted in the API...")
                await asyncio.sleep(5)
                for target in self.targets:
                    try:
                        await self.client.retrieve_queue(target.id)
                    except APIClientError as e:
                        if e.status_code == 404:
                            queue_deleted_count += 1
                        else:
                            raise e

    async def delete_remote(self, target: Target):
        try:
            remote_object = await self.get_remote_object(target.id)

            if not self.plan_only:
                await self.client._http_client._request(
                    "DELETE",
                    f"queues/{target.id}",
                    params={"delete_after": "0"},
                )
                self.yaml_reference["targets"][target.index]["id"] = None

            pprint(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ''} {settings.DELETE_PRINT_STR} {self.display_type}: {self.target_display_label(remote_object.get('name', 'no-name'), remote_object.get('id', 'no-id'))}"
            )
        except NonExistentObjectException:
            display_warning(
                f"{self.display_type} [purple]{target.id}[/purple] already does not exist on remote."
            )
            self.yaml_reference["targets"][target.index]["id"] = None
        except Exception as e:
            display_error(
                f"Error while deleting {self.display_type} [purple]{target.id}[/purple]: {e}",
                e,
            )
            self.revert_failed = True

    async def revert(self):
        try:
            await self.inbox_release.initialize(
                yaml=self.yaml,
                client=self.client,
                plan_only=self.plan_only,
                parent_queue=self,
            )

            await self.inbox_release.revert()

            if self.inbox_release.revert_failed:
                raise SubObjectException()

            await super().revert()

            if self.revert_failed:
                return

            await self.ensure_queues_deleted()

            await self.schema_release.initialize(
                yaml=self.yaml,
                client=self.client,
                plan_only=self.plan_only,
                parent_queue=self,
            )

            await self.schema_release.revert()

            if self.schema_release.revert_failed:
                raise SubObjectException()

        except SubObjectException:
            self.revert_failed = True
