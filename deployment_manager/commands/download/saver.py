from anyio import Path
from pydantic import BaseModel

from deployment_manager.commands.download.helpers import should_write_object
from deployment_manager.commands.download.subdirectory import Subdirectory
from deployment_manager.commands.download.types import ObjectSaver
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    create_formula_file,
    find_formula_fields_in_schema,
    write_object_to_json,
    write_str,
)
from deployment_manager.utils.consts import CustomResource, Settings, display_warning
from deployment_manager.utils.functions import templatize_name_id
from rossum_api.api_client import Resource


class WorkspaceSaver(ObjectSaver):
    type: Resource = Resource.Workspace

    def construct_object_path(self, subdir: Subdirectory, object: dict) -> Path:
        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(object["name"], object["id"])
            / "workspace.json"
        )
        return object_path

    async def save_downloaded_object(self, workspace: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, object=workspace)
        if self.download_all or await should_write_object(
            object_path, workspace, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                workspace,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class QueueSaver(ObjectSaver):
    type: Resource = Resource.Queue
    workspaces: list[dict]

    def find_subdir_of_object(self, object: dict):
        parent = self.find_parent_object(object)
        if parent:
            # If you know the parent's subdir, you can use its subdir
            subdir = self.subdirs_by_object_id.get(parent["id"])
            return subdir if subdir else super().find_subdir_of_object(parent)

        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        return None

    def find_parent_object(self, child):
        return self.find_workspace_for_queue(child)

    def construct_object_path(self, subdir: Subdirectory, queue: dict) -> Path:
        workspace_for_queue = self.find_workspace_for_queue(queue)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue["name"], queue["id"])
            / "queue.json"
        )
        return object_path

    async def save_downloaded_object(self, queue: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, queue=queue)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, queue, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                queue,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

    def find_workspace_for_queue(self, queue: dict):
        for ws in self.workspaces:
            if ws["url"] == queue.get("workspace", None):
                return ws
        # display_error(
        #     f"Could not find workspace for {self.display_type} {self.display_label(queue.get('name', "no-name"), queue.get('id', 'no-id'))}. Skipping."
        # )
        return None


class EmailTemplateSaver(QueueSaver):
    type: Resource = Resource.EmailTemplate
    queues: list[dict]

    def find_parent_object(self, child):
        return self.find_queue(child)

    def find_queue(self, email_template: dict):
        for queue in self.queues:
            if queue["url"] == email_template.get("queue", None):
                return queue
        # display_warning(
        #     f"Could not find queue for {self.display_type} {self.display_label(email_template.get('name', 'no-name'), email_template.get('id', 'no-id'))}. The object will not be saved locally."
        # )
        return None

    def construct_object_path(self, subdir: Subdirectory, email_template: dict) -> Path:
        queue_for_schema = self.find_queue(email_template)
        if not queue_for_schema:
            return
        workspace_for_queue = self.find_workspace_for_queue(queue_for_schema)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_schema["name"], queue_for_schema["id"])
            / Settings.EMAIL_TEMPLATES_DIR_NAME
            / f'{templatize_name_id(email_template["name"], email_template["id"])}.json'
        )
        return object_path

    def _get_message_for_subdir_selection(self, object):
        message = super()._get_message_for_subdir_selection(object)

        queue = self.find_queue(object)
        if queue:
            return message + f", for [yellow]queue[/yellow]: {self.display_label(queue['name'], queue['id'])}"
        return message

    async def save_downloaded_object(self, email_template: dict, subdir: Subdirectory):
        if not email_template.get("queue", None):
            return

        object_path = self.construct_object_path(subdir=subdir, email_template=email_template)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, email_template, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                email_template,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class InboxSaver(QueueSaver):
    type: Resource = Resource.Inbox
    queues: list[dict]

    def find_parent_object(self, child):
        return self.find_queue(child)

    def find_queue(self, inbox: dict):
        for queue in self.queues:
            if queue["url"] == inbox.get("queues", [None])[0]:
                return queue
        # display_warning(
        #     f"Could not find queue for {self.display_type} {self.display_label(inbox.get('name', 'no-name'), inbox.get('id', 'no-id'))}. The object will not be saved locally."
        # )
        return None

    def construct_object_path(self, subdir: Subdirectory, inbox: dict) -> Path:
        queue_for_inbox = self.find_queue(inbox)
        if not queue_for_inbox:
            return
        workspace_for_queue = self.find_workspace_for_queue(queue_for_inbox)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_inbox["name"], queue_for_inbox["id"])
            / "inbox.json"
        )
        return object_path

    async def save_downloaded_object(self, inbox: dict, subdir: Subdirectory):
        if not inbox.get("queues", []):
            return

        object_path = self.construct_object_path(subdir=subdir, inbox=inbox)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, inbox, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                inbox,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class SchemaSaver(QueueSaver):
    type: Resource = Resource.Schema
    queues: list[dict]

    async def save_downloaded_objects(self):
        for object in self.objects:
            subdir = self.find_subdir_of_object(object)
            if not subdir:
                self.objects_without_subdir.append(object)
                continue
            # The subdir should not be pulled, disregard the current object
            elif not subdir.include:
                continue
            await self.save_downloaded_object(object, subdir)

    def find_parent_object(self, child):
        return self.find_queue(child)

    def find_queue(self, schema: dict):
        schema_queues = schema.get("queues", [None])
        # The schema might not have any queues assigned ([])
        if not schema_queues:
            # display_warning(warning_message)
            return None

        for queue in self.queues:
            if queue["url"] == schema_queues[0]:
                if len(schema_queues) > 1:
                    display_warning(
                        f"{self.display_type} {self.display_label(schema.get('name', 'no-name'), schema.get('id', 'no-id'))} has multiple queues assigned - saving it under the first one ({self.display_label(queue.get('name', 'no-name'), queue.get('id', 'no-id'))})"
                    )

                return queue

        # display_warning(warning_message)
        return None

    def construct_object_path(
        self,
        subdir: Subdirectory,
        schema: dict,
    ) -> Path:
        queue_for_schema = self.find_queue(schema)
        if not queue_for_schema:
            return
        workspace_for_queue = self.find_workspace_for_queue(queue_for_schema)
        if not workspace_for_queue:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workspaces"
            / templatize_name_id(workspace_for_queue["name"], workspace_for_queue["id"])
            / "queues"
            / templatize_name_id(queue_for_schema["name"], queue_for_schema["id"])
            / "schema.json"
        )
        return object_path

    async def save_downloaded_object(self, schema: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, schema=schema)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, schema, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                schema,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

            formula_saver = FormulaSaver(parent_schema_path=object_path, parent_schema=schema)
            await formula_saver.save_downloaded_objects()


class FormulaSaver(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    parent_schema_path: Path
    parent_schema: dict

    formula_fields: dict[str, str] = {}

    @property
    def formula_directory_path(self):
        return create_formula_directory_path(self.parent_schema_path)

    async def save_downloaded_objects(self):
        formula_fields = find_formula_fields_in_schema(self.parent_schema["content"])
        for field_id, code in formula_fields:
            await create_formula_file(self.construct_object_path(field_id=field_id), code)

    def construct_object_path(self, field_id):
        return self.formula_directory_path / f"{field_id}.py"


class RuleSaver(ObjectSaver):
    type: Resource = CustomResource.Rule
    queues: list[dict]

    def find_subdir_of_object(self, object: dict):
        parent = self.find_parent_object(object)
        if parent:
            # If you know the parent's subdir, you can use its subdir
            subdir = self.subdirs_by_object_id.get(parent["id"])
            return subdir if subdir else super().find_subdir_of_object(parent)

        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        return None

    def find_parent_object(self, child):
        return self.find_queue_for_rule(child)

    def find_queue_for_rule(self, rule: dict):
        rule_queues = rule.get("queues", [])
        # The rule might not have any queues assigned
        if not rule_queues:
            return None

        # Use the first queue to determine the subdir
        # If a rule spans multiple subdirs, this will use the first one
        for queue in self.queues:
            if queue["url"] in rule_queues:
                return queue

        return None

    def construct_object_path(self, subdir: Subdirectory, rule: dict) -> Path:
        object_path = (
            self.base_path
            / subdir.name
            / Settings.RULES_DIR_NAME
            / f'{templatize_name_id(rule["name"], rule["id"])}.json'
        )
        return object_path

    async def save_downloaded_object(self, rule: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, rule=rule)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, rule, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                rule,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class HookSaver(ObjectSaver):
    type: Resource = Resource.Hook

    def construct_object_path(self, subdir: Subdirectory, hook: dict) -> Path:
        object_path = self.base_path / subdir.name / "hooks" / f'{templatize_name_id(hook["name"], hook["id"])}.json'
        return object_path

    async def save_downloaded_object(self, hook: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, hook=hook)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, hook, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                hook,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

            custom_hook_code_path = create_custom_hook_code_path(object_path, hook)
            if custom_hook_code_path:
                await write_str(custom_hook_code_path, hook.get("config", {}).get("code", None))


class WorkflowSaver(ObjectSaver):
    type: Resource = CustomResource.Workflow

    def construct_object_path(self, subdir: Subdirectory, object: dict) -> Path:
        object_path = (
            self.base_path
            / subdir.name
            / "workflows"
            / templatize_name_id(object["name"], object["id"])
            / "workflow.json"
        )
        return object_path

    async def save_downloaded_object(self, workflow: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, object=workflow)
        if self.download_all or await should_write_object(
            object_path, workflow, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                workflow,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )


class WorkflowStepSaver(ObjectSaver):
    type: Resource = CustomResource.WorkflowStep
    workflows: list[dict]

    def find_subdir_of_object(self, object: dict):
        parent = self.find_parent_object(object)
        if parent:
            # If you know the parent's subdir, you can use its subdir
            subdir = self.subdirs_by_object_id.get(parent["id"])
            return subdir if subdir else super().find_subdir_of_object(parent)

        subdir = super().find_subdir_of_object(object)
        if subdir:
            return subdir

        return None

    def find_parent_object(self, child):
        return self.find_workflow_for_workflow_step(child)

    def construct_object_path(self, subdir: Subdirectory, workflow_step: dict) -> Path:
        workflow_for_workflow_step = self.find_workflow_for_workflow_step(workflow_step)
        if not workflow_for_workflow_step:
            return

        object_path = (
            self.base_path
            / subdir.name
            / "workflows"
            / templatize_name_id(workflow_for_workflow_step["name"], workflow_for_workflow_step["id"])
            / "workflow_steps"
            / f'{templatize_name_id(workflow_step["name"], workflow_step["id"])}.json'
        )
        return object_path

    async def save_downloaded_object(self, workflow_step: dict, subdir: Subdirectory):
        object_path = self.construct_object_path(subdir=subdir, workflow_step=workflow_step)
        if not object_path:
            return
        if self.download_all or await should_write_object(
            object_path, workflow_step, self.changed_files, self.parent_dir_reference
        ):
            await write_object_to_json(
                object_path,
                workflow_step,
                self.type,
                log_message=f"Pulled {self.display_type} {object_path}",
            )

    def find_workflow_for_workflow_step(self, workflow_step: dict):
        for ws in self.workflows:
            if ws["url"] == workflow_step.get("workflow", None):
                return ws
        # display_error(
        #     f"Could not find workflow for {self.display_type} {self.display_label(queue.get('name', "no-name"), queue.get('id', 'no-id'))}. Skipping."
        # )
        return None
