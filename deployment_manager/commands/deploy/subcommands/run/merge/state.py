import json
import pathlib
import anyio
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.utils.consts import CustomResource, display_error, display_info, settings
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal

from rossum_api.api_client import Resource


class LastAppliedEntry(BaseModel):
    forward: Optional[dict] = Field(default=None)
    reverse: Optional[dict] = Field(default=None)
    derived_fields: Optional[list] = Field(default_factory=list)


class DeploymentEntry(BaseModel):
    last_applied: LastAppliedEntry = Field(default_factory=LastAppliedEntry)


class ResourceDeployments(BaseModel):
    # Maps target_id to deployments
    deployments: Dict[int, DeploymentEntry] = Field(default_factory=dict)


class DeployState(BaseModel):
    organizations: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    hooks: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    schemas: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    rules: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    rule_templates: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    queues: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    inboxes: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    workspaces: Dict[int, ResourceDeployments] = Field(default_factory=dict)
    engines: Dict[int, ResourceDeployments] = Field(default_factory=dict)

    @classmethod
    async def ensure_deploy_state_file(
        cls, path: anyio.Path, base_path: anyio.Path, deploy_file_path: anyio.Path
    ) -> "DeployState":
        if not str(path) or path == anyio.Path(""):
            path = await get_filepath_from_user(
                project_path=base_path,
                default=settings.DEFAULT_DEPLOY_STATE_PARENT
                + "/"
                + f"{deploy_file_path.stem}.json",
                default_text="Name for the deploy state file:",
            )

        if not await path.exists():
            await cls().write_deploy_state(deploy_state_path=path)

        return path

    @classmethod
    def load_deploy_state(cls, path: pathlib.Path) -> "DeployState":
        if path.exists():
            try:
                contents = path.read_text()
                return cls(**json.loads(contents))
            except Exception as e:
                display_error(f"Failed to load deploy state from {path}: {e}")

        return cls()

    def get_last_applied(
        self,
        resource_type: Resource | CustomResource,
        source_id: int | str,
        target_id: int | str,
        direction: Literal["forward", "reverse"],
    ) -> Optional[dict]:
        try:
            entry = (
                getattr(self, resource_type.value)[int(source_id)]
                .deployments[int(target_id)]
                .last_applied
            )
            result = entry.dict().get(direction)
            if result is not None:
                result["derived_fields"] = entry.derived_fields or []
            return result
        except KeyError:
            return None

    async def update_deploy_state(
        self, objects: list[tuple[Resource, list[DeployObject]]], direction="forward"
    ):
        for resource_type, releases in objects:
            state_map = getattr(self, resource_type.value)

            for release in releases:
                for target in release.targets:
                    if target.last_applied_data and not release.deploy_failed:
                        source_id, target_id = int(release.id), int(target.id)
                        config = target.last_applied_data

                        # Ensure entry exists
                        if source_id not in state_map:
                            state_map[source_id] = ResourceDeployments()

                        if target_id not in state_map[source_id].deployments:
                            state_map[source_id].deployments[
                                target_id
                            ] = DeploymentEntry()

                        last_applied = (
                            state_map[source_id].deployments[target_id].last_applied
                        )

                        if direction == "forward":
                            last_applied.forward = config
                        else:
                            last_applied.reverse = config

    async def write_deploy_state(
        self, deploy_state_path: anyio.Path, direction="forward"
    ):
        try:
            await deploy_state_path.parent.mkdir(parents=True, exist_ok=True)
            await deploy_state_path.write_text(self.model_dump_json(indent=2))
            display_info(f"Saved deploy state to [green]{deploy_state_path}[/green]")
        except Exception as e:
            display_error(f"Could not save deploy state: {e}", e)
