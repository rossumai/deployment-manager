import hashlib

import questionary
from anyio import Path
from rich import print as pprint
from rossum_api import AsyncRossumAPIClient

from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_api_url_from_user,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.template.helpers import (
    add_override_to_deploy_file_objects,
    add_targets_from_mapping,
    collect_rule_dependency_ids,
    create_deploy_file_template,
    get_attribute_overrides_from_user,
    get_dir_and_subdir_from_user,
    get_email_templates_from_user,
    get_engines_from_user,
    get_hooks_from_user,
    get_labels_from_user,
    get_multi_targets_from_user,
    get_queues_from_user,
    get_rule_dependency_objects,
    get_rules_from_user,
    get_secrets_from_user,
    get_workspaces_from_user,
)
from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.common.mapping import read_mapping
from deployment_manager.common.read_write import (
    read_object_from_json,
    write_object_to_json,
)
from deployment_manager.utils.consts import display_error, display_info, settings


async def create_deploy_template(
    input_file_path: Path = None,
    mapping_file_path: Path = None,
    org_path: Path = None,
    interactive: bool = False,
    source_client: AsyncRossumAPIClient = None,
    target_client: AsyncRossumAPIClient = None,
):
    if not input_file_path:
        input_file_content = create_deploy_file_template()
        # Without an initial input file, the user must always do the selections himself
        interactive = True
    else:
        input_file_content = await input_file_path.read_text()

    yaml = DeployYaml(file=input_file_content)
    deploy_file_object = yaml.data

    if not org_path:
        org_path = Path("./")

    # Source dir
    source_dir_and_subdir = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_DIR, None)
    if interactive or not source_dir_and_subdir:
        source_dir_and_subdir = await get_dir_and_subdir_from_user(
            project_path=org_path,
            type=settings.SOURCE_DIRNAME.upper(),
            default=source_dir_and_subdir,
        )
    deploy_file_object[settings.DEPLOY_KEY_SOURCE_DIR] = source_dir_and_subdir

    source_path = org_path / source_dir_and_subdir
    if not (await (source_path / "workspaces").exists()):
        display_error(f'Did not find "workspaces" directory in the "{source_dir_and_subdir}" directory.')
        return

    # Target dir/subdir
    target_dir_and_subdir = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_DIR, None)
    if interactive or not target_dir_and_subdir:
        target_dir_and_subdir = await get_dir_and_subdir_from_user(
            project_path=org_path,
            type=settings.TARGET_DIRNAME.upper(),
            default=target_dir_and_subdir,
        )
    deploy_file_object[settings.DEPLOY_KEY_TARGET_DIR] = target_dir_and_subdir

    # Source URL
    # Target URL can be in the deploy file already, in a config file, or inputted by the user
    source_url = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_URL, "")
    if not source_url:
        source_url = await get_api_url_from_config(base_path=org_path, org_name=source_dir_and_subdir.split("/")[0])
    if interactive or not source_url:
        source_url = await get_api_url_from_user(type=settings.SOURCE_DIRNAME, default=source_url)
    deploy_file_object[settings.DEPLOY_KEY_SOURCE_URL] = source_url

    # TODO: specify hook_template URL for hook in the deploy file

    # Target URL
    # Target URL can be in the deploy file already, in a config file, or inputted by the user
    target_url = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_URL, "")
    if not target_url and target_dir_and_subdir:
        target_url = await get_api_url_from_config(base_path=org_path, org_name=target_dir_and_subdir.split("/")[0])
    if interactive or not target_url:
        target_url = await get_api_url_from_user(type=settings.TARGET_DIRNAME, default=target_url)
    deploy_file_object[settings.DEPLOY_KEY_TARGET_URL] = target_url

    # Workspaces
    workspaces = deploy_file_object.get(settings.DEPLOY_KEY_WORKSPACES, [])
    deploy_file_workspaces, selected_ws_paths = await get_workspaces_from_user(
        previous_deploy_file_workspaces=workspaces,
        source_path=source_path,
        interactive=interactive,
    )
    deploy_file_object[settings.DEPLOY_KEY_WORKSPACES] = deploy_file_workspaces

    # Queues
    queues = deploy_file_object.get(settings.DEPLOY_KEY_QUEUES, [])
    deploy_file_queues, selected_queues = await get_queues_from_user(
        previous_deploy_file_queues=queues,
        deploy_ws_paths=[ws.parent for ws in selected_ws_paths],
        interactive=interactive,
    )
    deploy_file_object[settings.DEPLOY_KEY_QUEUES] = deploy_file_queues

    # Hooks
    hooks = deploy_file_object.get(settings.DEPLOY_KEY_HOOKS, [])
    unselected_hook_ids = deploy_file_object.get(settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS, [])
    selected_hooks, unselected_hooks = await get_hooks_from_user(
        previous_deploy_file_hooks=hooks,
        unselected_hook_ids=unselected_hook_ids,
        source_path=source_path,
        queues=selected_queues,
        interactive=interactive,
    )
    deploy_file_object[settings.DEPLOY_KEY_HOOKS] = selected_hooks
    deploy_file_object[settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS] = unselected_hooks

    # Rules
    rules = deploy_file_object.get(settings.DEPLOY_KEY_RULES, [])
    deploy_file_rules, selected_rule_objects = await get_rules_from_user(
        previous_deploy_file_rules=rules,
        source_path=source_path,
        queues=selected_queues,
        interactive=interactive,
    )
    deploy_file_object[settings.DEPLOY_KEY_RULES] = deploy_file_rules

    # Engines
    engines = deploy_file_object.get(settings.DEPLOY_KEY_ENGINES, [])
    selected_engines, engine_paths = await get_engines_from_user(
        previous_deploy_file_engines=engines,
        source_path=source_path,
        interactive=interactive,
    )
    deploy_file_object[settings.DEPLOY_KEY_ENGINES] = selected_engines

    # Labels/email templates referenced by the selected rules, surfaced as mandatory in the
    # menus below. Re-derived each run, so dropping a rule drops its dependencies.
    label_rule_ids, email_template_rule_ids = collect_rule_dependency_ids(selected_rule_objects)

    # `or []`: a bare `labels:` in the template parses as None, not []
    previous_labels = deploy_file_object.get(settings.DEPLOY_KEY_LABELS) or []
    user_labels = await get_labels_from_user(
        previous_deploy_file_labels=previous_labels,
        source_path=source_path,
        interactive=interactive,
        rule_required_ids=label_rule_ids,
    )

    previous_email_templates = deploy_file_object.get(settings.DEPLOY_KEY_EMAIL_TEMPLATES) or []
    user_email_templates = await get_email_templates_from_user(
        previous_deploy_file_email_templates=previous_email_templates,
        selected_queues=selected_queues,
        interactive=interactive,
        rule_required_ids=email_template_rule_ids,
    )

    # Rule dependencies the menus can't reach: labels with no local file, and email templates
    # of queues not in this deploy file. Exclude what the menus already covered.
    rule_labels, rule_email_templates = await get_rule_dependency_objects(
        selected_rules=selected_rule_objects,
        source_path=source_path,
        exclude_label_ids={obj["id"] for obj in user_labels},
        exclude_email_template_ids={obj["id"] for obj in user_email_templates},
        previous_deploy_file_labels=previous_labels,
        previous_deploy_file_email_templates=previous_email_templates,
    )
    deploy_file_object[settings.DEPLOY_KEY_LABELS] = user_labels + rule_labels
    deploy_file_object[settings.DEPLOY_KEY_EMAIL_TEMPLATES] = user_email_templates + rule_email_templates

    # Multi-target specification
    if interactive:
        await get_multi_targets_from_user(deploy_file_object)

    # Global attribute overrides
    if interactive:
        overrides = await get_attribute_overrides_from_user()
        for override in overrides:
            add_override_to_deploy_file_objects(override, deploy_file_object)

    # Mapping reuse
    if mapping_file_path and await mapping_file_path.exists():
        try:
            mapping = await read_mapping(mapping_path=mapping_file_path)
            add_targets_from_mapping(mapping=mapping, deploy_file=yaml.data)
        except Exception as e:
            display_error("Error while applying mapping ^", e)

    # Filename
    if interactive:
        source_subdir_name = source_dir_and_subdir.split("/")[1]
        target_subdir_name = target_dir_and_subdir.split("/")
        default_deploy_name = (
            f"{source_subdir_name}_{target_subdir_name[1] if len(target_subdir_name) > 1 else "NA"}.yaml"
        )
        deploy_filepath = await get_filepath_from_user(
            org_path,
            default=(
                str(input_file_path) if input_file_path else settings.DEFAULT_DEPLOY_PARENT + "/" + default_deploy_name
            ),
        )
    else:
        deploy_filepath = input_file_path

    # Deploy secrets
    secrets_file_path = deploy_file_object.get(settings.DEPLOY_KEY_SECRETS_PATH, "")
    if secrets_file_path and await (secrets_file_path := Path(secrets_file_path)).exists():
        previous_secrets_file = await read_object_from_json(secrets_file_path)
    else:
        secrets_file_path = None
        previous_secrets_file = {}
    if (
        interactive
        and await questionary.confirm(
            f"Do you wish to {'update' if secrets_file_path else 'create'} secrets file?"
        ).ask_async()
    ):
        secrets = await get_secrets_from_user(
            deploy_file_object,
            previous_secrets_file=(previous_secrets_file),
        )
        if not secrets_file_path:
            secrets_file_path = await get_filepath_from_user(
                org_path,
                default=(settings.DEFAULT_DEPLOY_SECRETS_PARENT + "/" + f"{deploy_filepath.stem}_secrets.json"),
            )
        await write_object_to_json(secrets_file_path, secrets)

    deploy_file_object[settings.DEPLOY_KEY_SECRETS_PATH] = str(secrets_file_path)

    # Deploy state
    state_file_path = deploy_file_object.get(settings.DEPLOY_KEY_STATE_PATH, "")

    if not state_file_path:
        hash_suffix = hashlib.sha1(
            f"{source_dir_and_subdir}_{target_dir_and_subdir}_{source_url}_{target_url}".encode("utf-8")
        ).hexdigest()[:6]
        state_file_path = settings.DEFAULT_DEPLOY_STATE_PARENT + "/" + f"{deploy_filepath.stem}_{hash_suffix}.json"

    deploy_file_object[settings.DEPLOY_KEY_STATE_PATH] = state_file_path

    await yaml.save_to_file(deploy_filepath)

    display_info(f"Deploy file saved to [green]{deploy_filepath}[/green]. Use it by running:")

    pprint(
        f"\n  {settings.NEW_COMMAND_NAME} {settings.DEPLOY_COMMAND_NAME} {settings.DEPLOY_RUN_COMMAND_NAME} {deploy_filepath}\n"
    )
