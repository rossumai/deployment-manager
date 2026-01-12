import click
from deployment_manager.common.custom_client import CustomAsyncRossumAPIClient as AsyncRossumAPIClient
from rossum_api.dtos import Token, UserCredentials

from deployment_manager.utils.consts import settings, validate_token


async def create_and_validate_client(
    destination: str,
):
    if destination == settings.SOURCE_DIRNAME or (
        destination == settings.TARGET_DIRNAME and settings.IS_PROJECT_IN_SAME_ORG
    ):
        if not settings.SOURCE_API_BASE:
            raise click.ClickException(f"No base URL provided for {destination}.")

        if not (
            settings.SOURCE_TOKEN
            or (settings.SOURCE_USERNAME and settings.SOURCE_PASSWORD)
        ):
            raise ValueError("username + password or token must be specified.")

        if settings.SOURCE_TOKEN and not settings.SOURCE_PASSWORD:
            validate_token(settings.SOURCE_API_BASE, settings.SOURCE_TOKEN, "source")

        try:
            if settings.SOURCE_TOKEN:
                client = AsyncRossumAPIClient(
                    base_url=settings.SOURCE_API_URL,
                    credentials=Token(settings.SOURCE_TOKEN),
                )
            else:
                client = AsyncRossumAPIClient(
                    base_url=settings.SOURCE_API_URL,
                    credentials=UserCredentials(
                        username=settings.SOURCE_USERNAME,
                        password=settings.SOURCE_PASSWORD,
                    ),
                )

            await client.request("GET", "auth/user")
            return client
        except Exception:
            raise click.ClickException(f'Invalid credentials for "{destination}".')

    elif destination == settings.TARGET_DIRNAME and not settings.IS_PROJECT_IN_SAME_ORG:
        if not settings.TARGET_API_URL:
            raise click.ClickException(f"No base URL provided for {destination}.")

        if not (
            settings.TARGET_TOKEN
            or (settings.TARGET_USERNAME and settings.TARGET_PASSWORD)
        ):
            raise ValueError("username + password or token must be specified.")

        if settings.TARGET_TOKEN and not settings.TARGET_PASSWORD:
            validate_token(settings.TARGET_API_BASE, settings.TARGET_TOKEN, "target")

        try:
            if settings.TARGET_TOKEN:
                client = AsyncRossumAPIClient(
                    base_url=settings.TARGET_API_URL,
                    credentials=Token(settings.TARGET_TOKEN),
                )
            else:
                client = AsyncRossumAPIClient(
                    base_url=settings.TARGET_API_URL,
                    credentials=UserCredentials(
                        username=settings.TARGET_USERNAME,
                        password=settings.TARGET_PASSWORD,
                    ),
                )

            await client.request("GET", "auth/user")
            return client
        except Exception:
            raise click.ClickException(f'Invalid credentials for "{destination}".')

    else:
        raise click.ClickException(f'Unrecognized destination "{destination}".')


if __name__ == "__main__":
    create_and_validate_client("source")
