import re
import sys

from anyio import Path
from pydantic import BaseModel, ConfigDict
from rich import print as pprint
from rich.panel import Panel
from rich.prompt import Confirm
from rossum_api.domain_logic.resources import Resource
from rossum_api.dtos import Token

from deployment_manager.commands.deploy.common.helpers import validate_credentials
from deployment_manager.commands.deploy.subcommands.run.helpers import get_token
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import Credentials
from deployment_manager.commands.download.directory import OrganizationDirectory
from deployment_manager.commands.upload.apply import apply_plan, format_api_error
from deployment_manager.commands.upload.dependencies import (
    mark_unstaged_objects_as_updated,
    merge_formula_changes,
    merge_hook_changes,
)
from deployment_manager.commands.upload.models import PushException
from deployment_manager.commands.upload.plan import (
    classify,
    determine_type_from_local_path,
    render_plan,
    strip_org_prefix,
    validate,
)
from deployment_manager.common.determine_path import determine_object_type_from_url
from deployment_manager.common.git import get_changed_file_paths, load_deleted_object_from_git
from deployment_manager.common.modified_at import check_modified_timestamp
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json
from deployment_manager.common.rossum_client import CustomAsyncAPIClient
from deployment_manager.utils.consts import GIT_CHARACTERS, CustomResource, display_error, display_warning, settings
from deployment_manager.utils.functions import find_all_object_paths


class ChangedObject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    operation: GIT_CHARACTERS
    path: Path
    data: dict = {}
    is_new: bool = False
    is_rename: bool = False
    placeholder_path: Path | None = None
    resolved_type: Resource | None = None

    @property
    def type(self) -> Resource:
        url = self.data.get("url", "")
        if url:
            return determine_object_type_from_url(url)
        if self.resolved_type:
            return self.resolved_type
        # Fall back to path-derived type for new objects (no url yet).
        derived = determine_type_from_local_path(self.placeholder_path or self.path)
        if derived is None:
            raise Exception(f"Cannot determine resource type for {self.path}")
        return derived

    @property
    def id(self) -> str:
        return self.data.get("id", "")

    @property
    def display_type(self) -> str:
        # Remove the plural 's'
        return f"[yellow]{self.type.value[: -2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self) -> str:
        name = self.data.get("name", "no-name")
        if self.id and name:
            return f'"[orange]{name}[/orange] ([purple]{self.id}[/purple])"'
        else:
            return f"[red]{self.path}[/red]"

    @property
    def display_operation(self):
        display_operation = ""
        match self.operation:
            case GIT_CHARACTERS.CREATED | GIT_CHARACTERS.CREATED_STAGED | GIT_CHARACTERS.CREATED_STAGED_MODIFIED:
                display_operation = settings.CREATE_PRINT_STR
            case GIT_CHARACTERS.DELETED:
                display_operation = settings.DELETE_PRINT_STR
            case GIT_CHARACTERS.UPDATED | GIT_CHARACTERS.PARTIALLY_UPADTED:
                display_operation = settings.UPDATE_PRINT_STR
        return display_operation

    def create_timestamp_mismatch_message(self):
        return f"{self.display_type} {self.display_label}: Remote object has a different timestamp. Please stash your changes and run {settings.DOWNLOAD_COMMAND_NAME} first."

    def create_success_message(self):
        return f"{self.display_operation} {self.display_type} {self.display_label}"

    def create_failure_message(self, error: str):
        return f"{self.display_operation} {self.display_type} {self.display_label}: {error}"


class UploadOrganizationDirectory(OrganizationDirectory):
    upload_all: bool = False
    force: bool = False
    indexed_only: bool = False
    assume_yes: bool = False
    changed_objects: list[ChangedObject] = []
    request_errors: list[str] = []
    # Set when an early-return path has already shown its own error block —
    # caller should skip auto-pull and not re-print request_errors.
    has_blocking_errors: bool = False

    async def initialize(self):
        if not self.project_path:
            self.project_path = Path(".")

        if not self.client:
            token = await get_token(
                project_path=self.project_path,
                org_name=self.name,
                api_url=self.api_base,
            )
            credentials = Credentials(token=token, url=self.api_base)
            await validate_credentials(credentials)
            self.client = CustomAsyncAPIClient(base_url=self.api_base, credentials=Token(token=token))

    async def prepare_changed_objects(self):
        changes = get_changed_file_paths(self.project_path / self.name, indexed_only=self.indexed_only)
        if not changes:
            display_warning(f"No changes to {settings.UPLOAD_COMMAND_NAME} found in {self.org_path}.")
            return

        changes = await merge_hook_changes(changes, self.project_path)
        # changes = await evaluate_delete_dependencies(changes, org_path)
        changes = await merge_formula_changes(changes)
        changes = await mark_unstaged_objects_as_updated(changes, self.project_path, self.client)

        # Include files from all subdirs, the non-included subdir objects will be filtered out later
        if self.upload_all:
            await self.include_unmodified_files(changes)

        for op, path in changes:
            if op == GIT_CHARACTERS.DELETED:
                # Deleted file is not on disk; reconstruct enough to delete remotely.
                changed_object = self._build_deleted_changed_object(op, path)
                if changed_object is not None:
                    self.changed_objects.append(changed_object)
                continue

            try:
                data = await read_object_from_json(path)
            except FileNotFoundError:
                continue

            object_url = data.get("url", "")
            if object_url:
                object_type = determine_object_type_from_url(object_url)
                subdir = self.find_subdir_of_object(data)
                if not subdir:
                    display_warning(f"No subdir found for path: {path}, skipping.")
                    continue
                if not subdir.include:
                    continue
                if object_type in [CustomResource.Workflow, CustomResource.WorkflowStep]:
                    continue

                changed_object = ChangedObject(operation=op, path=path, data=data)
                self.changed_objects.append(changed_object)
                continue

            # No url => possibly a brand-new object marked with `_[]`.
            rel_path = strip_org_prefix(path, self.project_path / self.name)
            resolved_type = determine_type_from_local_path(rel_path)
            if resolved_type is None:
                display_warning(f"Cannot determine resource type for {path}, skipping.")
                continue
            # Subdir filtering for new objects: include them if any subdir under
            # which they live is included. We don't have an id to look up, so
            # use the path: the first segment is the subdir name.
            subdir = self._find_subdir_by_path(rel_path)
            if subdir is not None and not subdir.include:
                continue

            changed_object = ChangedObject(
                operation=op,
                path=path,
                data=data,
                resolved_type=resolved_type,
            )
            self.changed_objects.append(changed_object)

    def _find_subdir_by_path(self, rel_path: Path):
        if not rel_path.parts:
            return None
        subdir_name = rel_path.parts[0]
        return self.subdirectories.get(subdir_name)

    def _build_deleted_changed_object(self, op, path: Path):
        """Construct a ChangedObject for a DELETE op without reading the file.

        The id is recovered from the segment that owns the object's identity:
          - Workspace/Queue/Engine: the immediate parent folder's `_[<id>]`.
          - Hook/Rule/EngineField: the file's own `_[<id>]` stem.
          - Schema/Inbox: filenames carry no id, so we read it from git history.
        """
        rel_path = strip_org_prefix(path, self.project_path / self.name)
        # Skip non-resource paths: hook code companions, email_templates,
        # labels, formulas, non_versioned_object_attributes.json, etc.
        resolved_type = determine_type_from_local_path(rel_path)
        if resolved_type is None:
            return None

        # Schema/Inbox filenames carry no id — recover it from git history
        # (staged or HEAD) so the DELETE op can be issued. If never in git,
        # skip silently.
        if resolved_type in (Resource.Schema, Resource.Inbox):
            recovered = load_deleted_object_from_git(self.project_path, path)
            if not recovered or "id" not in recovered:
                return None
            subdir = self._find_subdir_by_path(rel_path)
            if subdir is not None and not subdir.include:
                return None
            return ChangedObject(
                operation=op,
                path=path,
                data={"id": recovered["id"], "url": recovered.get("url", "")},
                resolved_type=resolved_type,
            )

        pat = re.compile(r"_\[(\d+)\]")
        owner_segment: str
        if resolved_type in (Resource.Workspace, Resource.Queue, Resource.Engine):
            if len(path.parts) < 2:
                display_warning(f"Cannot determine id for deleted path: {path}")
                return None
            owner_segment = path.parts[-2]
        else:  # Hook, Rule, EngineField — id is in the filename stem
            owner_segment = path.parts[-1]
        m = pat.search(owner_segment)
        if not m:
            display_warning(f"Cannot determine id for deleted path: {path}")
            return None
        obj_id = int(m.group(1))

        subdir = self._find_subdir_by_path(rel_path)
        if subdir is not None and not subdir.include:
            return None

        return ChangedObject(
            operation=op,
            path=path,
            data={"id": obj_id},
            resolved_type=resolved_type,
        )

    def find_subdir_of_object(self, object: dict):
        for subdir in self.subdirectories.values():
            if object.get("id", None) in subdir.object_ids:
                return subdir
        return None

    async def upload_organization(self):
        try:
            await self.initialize()
        except Exception as e:
            display_error(f"Error while initializing {self.display_label}: {str(e)}")
            self.has_blocking_errors = True
            return

        try:
            await self.find_object_ids_for_subdirs()
            await self.prepare_changed_objects()
        except PushException as e:
            display_error(
                f"Error while preparing objects to {settings.UPLOAD_COMMAND_NAME} for {self.display_label}: {str(e)}",
            )
            self.has_blocking_errors = True
            return
        except Exception as e:
            display_error(
                f"Error while preparing objects to {settings.UPLOAD_COMMAND_NAME} for {self.display_label}: {str(e)}",
                e,
            )
            self.has_blocking_errors = True
            return

        if not self.changed_objects:
            return

        org_path = self.project_path / self.name
        plan = classify(self.changed_objects, org_path)
        validate(plan)

        if plan.errors:
            display_error(
                f"Validation errors while planning {settings.UPLOAD_COMMAND_NAME} for {self.display_label}:\n"
                + "\n".join(f"  - {e}" for e in plan.errors)
            )
            self.has_blocking_errors = True
            return

        if plan.is_empty:
            return

        if plan.has_structural_changes:
            render_plan(plan, label=str(self.display_label))
            if not self.assume_yes:
                # Confirm.ask raises EOFError on closed stdin — bail cleanly.
                if not sys.stdin.isatty():
                    display_error(
                        f"{self.display_label}: plan contains CREATE/DELETE ops but "
                        "stdin is non-interactive. Re-run with --yes to apply, or "
                        "from a TTY to confirm."
                    )
                    self.has_blocking_errors = True
                    return
                if not Confirm.ask(
                    f"Apply this plan to {self.display_label}?",
                    default=False,
                ):
                    pprint(Panel("Aborted.", style="yellow"))
                    self.has_blocking_errors = True
                    return

        total = len(plan.creates) + len(plan.updates) + len(plan.deletes)
        pprint(Panel(f"Pushing objects to {self.display_label} (Total objects: {total})"))
        await apply_plan(plan, self)

    async def include_unmodified_files(self, changes: list[tuple[str, Path]]):
        all_files = await find_all_object_paths(self.org_path)

        changes_paths = set(map(lambda x: x[1], changes))
        for file_path in all_files:
            if file_path not in changes_paths:
                changes.append((GIT_CHARACTERS.UPDATED.value, file_path))

    async def make_update_request(self, object: ChangedObject):
        try:
            url = object.data.get("url", None)
            if not object.id:
                raise Exception("Missing object ID")
            if not url:
                raise Exception("Missing object URL")
            # Skip the timestamp check for rename UPDATEs — the keys in
            # non_versioned_object_attributes.json are path-based, so the new
            # post-rename path has no entry and local.modified_at == "" would
            # always mismatch the remote.
            if not self.force and not object.is_rename:
                local_remote_timestamp_synced = await check_modified_timestamp(
                    client=self.client,
                    resource=object.type,
                    id=object.id,
                    local_object=object.data,
                )
                if not local_remote_timestamp_synced:
                    self.request_errors.append(object.create_timestamp_mismatch_message())
                    return None

            # queue.inbox attributes are ready-only in Elis API, but we don't ignore them when pulling to distinguish queues with and without inboxes
            if object.type == Resource.Queue:
                object.data.pop("inbox", None)

            result = await self.client._http_client.update(object.type, object.id, object.data)

            # Just to update the timestamp
            await write_object_to_json(
                object.path,
                result,
                object.type,
            )

            pprint(object.create_success_message())
            return result
        except Exception as e:
            self.request_errors.append(object.create_failure_message(format_api_error(e)))

            if self.upload_all:
                pprint(Panel(f"Recreating {object.display_type} {object.display_label}"))
                return await self.make_create_request(object=object)

    async def make_create_request(self, object: ChangedObject):
        try:
            object.data["id"] = None
            result = await self.client._http_client.create(object.type, object.data)

            # Just to update the timestamp
            await write_object_to_json(
                object.path,
                result,
                object.type,
            )

            pprint(object.create_success_message())
            return result
        except Exception as e:
            self.request_errors.append(object.create_failure_message(format_api_error(e)))
