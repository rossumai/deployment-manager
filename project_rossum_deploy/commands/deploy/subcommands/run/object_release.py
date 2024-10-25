from copy import deepcopy
import subprocess
import tempfile
from typing import Annotated, Any
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.common.read_write import read_json
from rich import print as pprint
import json
from rich.panel import Panel


from anyio import Path
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import display_error, display_warning
from project_rossum_deploy.utils.functions import templatize_name_id


class PathNotFoundException(Exception): ...


type LookupTable = dict[int, list[int]]
IMPLICIT_OVERRIDE_KEYS = ["settings", "metadata"]


class Target(BaseModel):
    id: int | None = Field(
        validation_alias=AliasChoices("id", "target_id"), default=None
    )
    data: dict = {}
    attribute_override: dict = {}


def convert_int_id_to_class(model, val):
    if not isinstance(val, dict):
        return model(id=None)
    return val


TargetWithDefault = Annotated[
    Target, BeforeValidator(lambda x: convert_int_id_to_class(Target, x))
]


# TODO: split some of the functionality into smaller classes (e.g., attr override)
class ObjectRelease(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    name: str
    type: Resource
    base_path: str = None
    yaml_reference: dict = None
    data: dict = None
    client: ElisAPIClient = None
    plan_only: bool = False
    is_same_org_deploy: bool = False
    deploy_failed: bool = False

    targets: list[TargetWithDefault] = []

    UPDATE_PRINT_STR: str = "[blue]UPDATE[/blue]"
    CREATE_PRINT_STR: str = "[red]CREATE[/red]"
    PLAN_PRINT_STR: str = "[bold]PLAN:[/bold]"
    # TODO: better parsing -> better dummy ID
    PLAN_CREATE_TBD_ID_STR: str = "0000000"

    async def initialize(
        self,
        yaml: DeployYaml,
        client: ElisAPIClient,
        source_dir_path: Path,
        plan_only: bool = False,
        is_same_org_deploy=False,
    ):
        if not self.base_path:
            self.base_path = source_dir_path
        self.yaml_reference = yaml.get_object_in_yaml(self.type.value, self.id)

        self.plan_only = plan_only
        self.is_same_org_deploy = is_same_org_deploy

        try:
            self.data = await read_json(self.path)
        except Exception:
            raise PathNotFoundException(
                f"Error while initializing object with path: {self.path}"
            )
        self.client = client

    async def plan(self, target_object: dict, target: Target):
        print()

    async def deploy(self): ...

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / f"{templatize_name_id(self.name, self.id)}.json"
        )

    @property
    def display_type(self):
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self):
        return f'"[green]{self.name}[/green] ([purple]{self.id}[/purple])"'

    @property
    def is_creating_targets(self):
        for target in self.targets:
            if not target.id:
                return True
        return False

    def prepare_object_copy_for_deploy(self, target: Target): ...

    def create_source_to_target_string(self, target: dict):
        return f'"{self.name} ([purple]{self.id}[/purple])" -> "{target['name']} ([purple]{target['id']}[/purple])"'

    def create_plan_target_object_id(self, source_id: int):
        return f"{str(source_id)}{self.PLAN_CREATE_TBD_ID_STR}"

    def check_plan_object_id(self, object_id: any):
        return self.PLAN_CREATE_TBD_ID_STR in str(object_id)

    async def check_modified_timestamps_equal(
        self, last_deploy_timestamp, remote_object_id: int
    ):
        remote_object = await self.client._http_client.fetch_one(
            self.type, remote_object_id
        )
        return remote_object.get("modified_at", "") == last_deploy_timestamp

    def update_targets(self, results):
        # asyncio.gather returns results in the same order as they were put in
        for index, (result, target) in enumerate(zip(results, self.targets)):
            target.id = result.get("id", None)
            target.data = result
            self.yaml_reference["targets"][index]["id"] = target.id

    # TODO: rename target_object (misleading)
    async def upload(self, target_object: dict, target: Target):
        if target.id:
            return await self.update_remote(target_object=target_object, target=target)
        else:
            return await self.create_remote(target_object=target_object, target=target)

    # Target is provided so that subclasses can use it (even if this basic method does not)
    async def create_remote(self, target_object: dict, target: Target = None):
        try:
            if self.plan_only:
                result = deepcopy(target_object)
                result_id = self.create_plan_target_object_id(target_object["id"])
                result["url"] = result["url"].replace(str(result["id"]), str(result_id))
                result["id"] = result_id
            else:
                result = await self.client._http_client.create(self.type, target_object)

            pprint(
                f'{self.PLAN_PRINT_STR if self.plan_only else ''} {self.CREATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while creating {self.display_type}  "{self.name} ({self.id})" ^',
                e,
            )
            self.deploy_failed = True
            return {}

    async def update_remote(self, target_object: dict, target: Target):
        try:
            if self.plan_only:
                result = deepcopy(target_object)
                result["url"] = result["url"].replace(str(result["id"]), str(target.id))
                result["id"] = target.id

                # TODO: timestamp checking
                # if not await self.check_modified_timestamps_equal(
                #     last_deploy_timestamp, target.id
                # ):
                #     display_warning(f"Remote timestamp of ")
                # If timestamps differ, show warning and let the user end the plan (to go review/sync changes)
            else:
                # TODO: check again to eliminate race conditions
                # Should remember if the user said "overwrite" in the step above

                result = await self.client._http_client.update(
                    self.type, id_=target.id, data=target_object
                )

            pprint(
                f'{self.PLAN_PRINT_STR if self.plan_only else ''} {self.UPDATE_PRINT_STR} {self.display_type}: {self.create_source_to_target_string(result)}.'
            )
            return result
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type}: "{self.name} ({self.id})" -> "{target.id} ^',
                e,
            )
            self.deploy_failed = True
            return {}

    async def implicit_override_targets(self, lookup_table: LookupTable):
        for target_index, target in enumerate(self.targets):
            override_source_data_copy = deepcopy(self.data)
            override_target_copy = deepcopy(target)

            self.remove_override_irrelevant_props(override_source_data_copy)
            self.remove_override_irrelevant_props(override_target_copy.data)

            self.replace_ids_in_target_object(
                target=override_target_copy,
                lookup_table=lookup_table,
                target_object_index=target_index,
                num_targets=len(self.targets),
            )

            diff = self.create_override_diff(
                override_source_data_copy, override_target_copy.data
            )
            if not diff:
                return

            if self.plan_only:
                colorized_diff = self.parse_diff(diff)
                message = f"Attribute override: {self.display_type} {self.create_source_to_target_string(override_target_copy.data)}:\n{colorized_diff}"
                pprint(Panel(message))
            else:
                # Update only objects where there was a difference after override
                await self.update_remote(
                    target_object=override_target_copy.data, target=target
                )

    # TODO: compile lists for each object?
    # TODO: add more attributes (e.g., modified_by, modified_at)
    def remove_override_irrelevant_props(self, data):
        data.pop("modified_by", None)
        data.pop("modified_at", None)
        match self.type:
            case Resource.Schema:
                data.pop("queues", None)
            case Resource.Hook:
                data.pop("token_owner", None)
                data.pop("guide", None)
                data.pop("run_after", None)
                data.pop("queues", None)
            case Resource.Workspace:
                data.pop("queues", None)
                data.pop("organization", None)
            case Resource.Queue:
                data.pop("users", None)
                data.pop("workflows", None)
                data.pop("counts", None)
                data.pop("workspace", None)
                data.pop("inbox", None)
                data.pop("schema", None)
                data.pop("hooks", None)
                data.pop("webhooks", None)

    def create_override_diff(self, before_object: dict, after_object: dict):
        """Displays both implicit and explicit overrides (the explicit applied already when uploading the file itself)"""
        # Do not display diffs in ID, but the ID must be retained for later reference
        after_object_id = after_object.pop("id", None)
        after_object_url = after_object.pop("url", None)
        before_object.pop("id", None)
        before_object.pop("url", None)

        with tempfile.NamedTemporaryFile() as tf1, tempfile.NamedTemporaryFile() as tf2:
            tf1.write(bytes(json.dumps(before_object, indent=2), "UTF-8"))
            tf2.write(bytes(json.dumps(after_object, indent=2), "UTF-8"))
            # Has to be manually seeked back to start
            tf1.seek(0)
            tf2.seek(0)

            diff = subprocess.run(
                ["diff", tf1.name, tf2.name, "-U" "3"],
                capture_output=True,
                text=True,
            )
            after_object["id"] = after_object_id
            after_object["url"] = after_object_url

            return diff.stdout

    def parse_diff(self, diff: str):
        colorized_lines = []
        split_lines = diff.splitlines()
        del split_lines[0:3]

        for index, line in enumerate(split_lines):
            if line.startswith("-"):
                colorized_line = f"[red]{line}[/red]"
            elif line.startswith("+"):
                colorized_line = f"[green]{line}[/green]"
            # The second is a CRLF issue related to diff
            elif line.startswith("@@") or "newline at end of file" in line:
                del split_lines[index]
            else:
                colorized_line = line
            colorized_lines.append(colorized_line)
        return "\n".join(colorized_lines)

    def replace_ids_in_target_object(
        self,
        target: Target,
        lookup_table: dict,
        target_object_index: int,
        num_targets: int,
    ):
        for key in IMPLICIT_OVERRIDE_KEYS:
            if key not in target.data:
                continue

            for parent, key_in_parent, value in ObjectRelease.traverse_object(
                target.data, key, target.data[key]
            ):
                for source_id, targets in lookup_table.items():
                    # source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
                    # if not re.search(source_id_regex, str(value)):
                    # continue
                    if str(source_id) not in str(value):
                        continue

                    if not targets:
                        display_warning(
                            f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target.id}". No target IDs found.',
                        )
                        self.remove_id_from_boject(
                            object=parent, key=key_in_parent, value=value
                        )
                        continue
                    # N:N objects -> objects are referenced in pairs
                    elif num_targets == len(targets):
                        target_id = targets[target_object_index]["id"]
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )
                    # N:1 objects -> everything should be mapped to the first target ID
                    else:
                        target_id = targets[0]["id"]
                        self.replace_id_in_object(
                            object=parent,
                            key=key_in_parent,
                            value=value,
                            source_id=source_id,
                            target_id=target_id,
                        )

                        if len(targets) != 1:
                            display_warning(
                                f"For overriding source_id '{source_id}' in {self.type.value} '{target.id}', There are multiple target IDs that could be assigned. The first one was used.",
                            )

            # stringified_dict = json.dumps(target.data[key])
            # for source_id, targets in lookup_table.items():
            #     source_id_regex = re.compile(f"(?<!\\w)({source_id})(?!\\w)")
            #     # This ID from source was not found in the subobject
            #     if not re.search(source_id_regex, stringified_dict):
            #         continue

            #     if not targets:
            #         display_warning(
            #             f'Could not override source_id "{source_id}" to its target equivalent in {self.type.value} "{target.id}". No target IDs found.',
            #         )
            #         continue
            #     # N:N objects -> objects are referenced in pairs
            #     elif num_targets == len(targets):
            #         target_id = targets[target_object_index]["id"]
            #         stringified_dict = self.replace_id_in_stringified_object(
            #             object_str=stringified_dict,
            #             regex=source_id_regex,
            #             source_id=source_id,
            #             target_id=target_id,
            #         )
            #     # N:1 objects -> everything should be mapped to the first target ID
            #     else:
            #         target_id = targets[0]["id"]
            #         stringified_dict = self.replace_id_in_stringified_object(
            #             object_str=stringified_dict,
            #             regex=source_id_regex,
            #             source_id=source_id,
            #             target_id=target_id,
            #         )

            #         if len(targets) != 1:
            #             display_warning(
            #                 f"For overriding source_id '{source_id}' in {self.type.value} '{target.id}', There are multiple target IDs that could be assigned. The first one was used.",
            #             )

            #     target.data[key] = json.loads(stringified_dict)

    def replace_id_in_object(
        self, object: dict, key: str, value: str | int, source_id: int, target_id: int
    ):
        if isinstance(object[key], list):
            value_index = object[key].index(value)
            if value_index > -1:
                new_value = str(value).replace(str(source_id), str(target_id))
                # Convert value back to int if applicable
                if isinstance(value, int):
                    new_value = int(new_value)
                object[key][value_index] = new_value
        else:
            new_value = str(value).replace(str(source_id), str(target_id))
            # Convert value back to int if applicable
            if isinstance(value, int):
                new_value = int(new_value)
            object[key] = new_value
        # Using lambdas for sub() because of quotes inside strings
        # return re.sub(
        #     regex,
        #     lambda m: str(target_id) if m[0] == str(source_id) else m[0],
        #     object_str,
        # )

    def remove_id_from_boject(self, object: dict, key: str, value: str | int):
        if isinstance(object[key], list):
            value_index = object[key].index(value)
            if value_index > -1:
                del object[key][value_index]
        else:
            del object[key]

    @staticmethod
    def traverse_object(parent_object: dict | None, parent_key: str, value: Any):
        if isinstance(value, list):
            for i in value:
                yield from ObjectRelease.traverse_object(parent_object, parent_key, i)
        elif isinstance(value, dict):
            for k, v in value.items():
                yield from ObjectRelease.traverse_object(value, k, v)
        elif isinstance(value, str) or isinstance(value, int):
            yield parent_object, parent_key, value
