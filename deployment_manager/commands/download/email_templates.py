import asyncio
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.commands.download.helpers import (
    should_write_object,
)

from deployment_manager.common.read_write import write_json
from deployment_manager.utils.functions import (
    templatize_name_id,
)


async def download_email_templates_for_queue(
    client: ElisAPIClient,
    queue_id: int,
    parent_dir: Path,
    changed_files: list = [],
    download_all: bool = False,
):
    # email_templates = []

    paginated_email_templates = [
        email_template
        async for email_template in client.list_all_email_templates(queue=queue_id)
    ]

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_email_templates = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.EmailTemplate, email_template.id)
            for email_template in paginated_email_templates
        ]
    )

    for email_template in full_email_templates:
        email_template_path = (
            parent_dir
            / "email_templates"
            / f'{templatize_name_id(email_template["name"], email_template["id"])}.json'
        )
        if download_all or await should_write_object(
            email_template_path, email_template, changed_files
        ):
            await write_json(
                email_template_path,
                email_template,
                Resource.EmailTemplate,
                log_message=f"Pulled {email_template_path}",
            )

        # email_templates.append((destination_local, email_template))

    # return email_templates
