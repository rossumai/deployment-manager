from anyio import Path
import questionary
from rossum_api import ElisAPIClient
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    get_url_and_credentials,
)
from deployment_manager.commands.hook.helpers import (
    get_annotation_id_from_frontend_url,
    get_org_name_from_hook_path,
    get_project_path_from_hook_path,
    load_hook_object,
)
from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import display_error, display_warning

STATUS_REQUIRING_EVENTS = ["annotation_status", "annotation_content"]


async def generate_and_save_hook_payload(
    hook_path: Path, annotation_url: str = "", client: ElisAPIClient = None
):
    try:
        payload = await generate_hook_payload(
            hook_path=hook_path, annotation_url=annotation_url, client=client
        )
        if not payload:
            return

        project_path = get_project_path_from_hook_path(hook_path=hook_path)
        payload_filename = await get_filepath_from_user(
            project_path=project_path,
            default=str(Path(f"payloads/payload_{hook_path.stem}.json")),
            default_text="Name for the payload JSON file",
        )

        await write_object_to_json(path=payload_filename, object=payload)
    except Exception as e:
        display_error("Error while generating hook payload {} ^", e)


async def generate_hook_payload(
    hook_path: Path, annotation_url: str = "", client: ElisAPIClient = None
):
    hook = await load_hook_object(hook_path=hook_path)
    if not hook:
        return

    if not client:
        project_path = get_project_path_from_hook_path(hook_path=hook_path)
        org_name = get_org_name_from_hook_path(hook_path=hook_path)
        credentials = await get_url_and_credentials(
            project_path=project_path,
            org_name=org_name,
        )
        if not credentials:
            return
        client = ElisAPIClient(base_url=credentials.url, token=credentials.token)

    if not annotation_url:
        annotation_url = await questionary.text(
            "Annotation URL for hook payload:"
        ).ask_async()
    if not annotation_url:
        display_warning("No annotation URL provided.")
        return
    # The annotation was pasted from the FE
    if "/document" in annotation_url:
        annotation_id = get_annotation_id_from_frontend_url(url=annotation_url)
        annotation_url = client._http_client.base_url + f"/annotations/{annotation_id}"

    event_action_choices = [
        questionary.Choice(title=event, value=event.split("."))
        for event in hook.get("events", [])
    ]
    if not event_action_choices:
        display_warning(f"No events attribute found in hook with path {hook_path}")
        return

    event, action = await questionary.select(
        "Choose event for hook payload:", choices=event_action_choices
    ).ask_async()

    request_body = {"event": event, "action": action, "annotation": annotation_url}

    if event in STATUS_REQUIRING_EVENTS:
        request_body["status"] = await questionary.text(
            "Annotation status:", "to_review"
        ).ask_async()

    return await client._http_client.request_json(
        method="POST",
        url=f"hooks/{hook['id']}/generate_payload",
        json=request_body,
    )
