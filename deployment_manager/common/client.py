import click

from deployment_manager.utils.consts import settings, validate_token
from rossum_api import ElisAPIClient


async def create_and_validate_client(
    destination: str,
):
    if destination == settings.SOURCE_DIRNAME or (
        destination == settings.TARGET_DIRNAME and settings.IS_PROJECT_IN_SAME_ORG
    ):
        if not settings.SOURCE_API_BASE:
            raise click.ClickException(f"No base URL provided for {destination}.")

        if settings.SOURCE_TOKEN and not settings.SOURCE_PASSWORD:
            validate_token(settings.SOURCE_API_BASE, settings.SOURCE_TOKEN, "source")

        try:
            client = ElisAPIClient(
                base_url=settings.SOURCE_API_URL,
                token=settings.SOURCE_TOKEN,
                username=settings.SOURCE_USERNAME,
                password=settings.SOURCE_PASSWORD,
            )
            await client.request("get", "auth/user")
            return client
        except Exception:
            raise click.ClickException(f'Invalid credentials for "{destination}".')

    elif destination == settings.TARGET_DIRNAME and not settings.IS_PROJECT_IN_SAME_ORG:
        if not settings.TARGET_API_URL:
            raise click.ClickException(f"No base URL provided for {destination}.")

        if settings.TARGET_TOKEN and not settings.TARGET_PASSWORD:
            validate_token(settings.TARGET_API_BASE, settings.TARGET_TOKEN, "target")

        try:
            client = ElisAPIClient(
                base_url=settings.TARGET_API_URL,
                token=settings.TARGET_TOKEN,
                username=settings.TARGET_USERNAME,
                password=settings.TARGET_PASSWORD,
            )
            await client.request("get", "auth/user")
            return client
        except Exception:
            raise click.ClickException(f'Invalid credentials for "{destination}".')

    else:
        raise click.ClickException(f'Unrecognized destination "{destination}".')


if __name__ == "__main__":
    create_and_validate_client("source")
