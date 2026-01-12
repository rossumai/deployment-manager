"""
Custom Rossum API client with enhanced retry logic for rate limiting.

Key features:
- Never gives up on 429 rate limit errors
- Respects Retry-After header from API responses
- Uses aggressive jitter (0.5x to 5.0x) for 429s to desynchronize concurrent retries
- Standard exponential backoff for other retryable errors (408, 500, 502, 503, 504)
"""

from __future__ import annotations

import logging
import random
import typing

import httpx
import tenacity
from rossum_api import APIClientError, AsyncRossumAPIClient
from rossum_api.clients.internal_async_client import InternalAsyncClient
from rossum_api.dtos import Token, UserCredentials

if typing.TYPE_CHECKING:
    from rossum_api.types import HttpMethod

logger = logging.getLogger(__name__)

RETRIED_HTTP_CODES = (408, 429, 500, 502, 503, 504)


class CustomInternalAsyncClient(InternalAsyncClient):
    """
    Extended InternalAsyncClient with custom retry logic for rate limiting.

    - Never gives up on 429 rate limit errors
    - Respects Retry-After header with aggressive jitter
    - Retries other errors (408, 500, 502, 503, 504) with exponential backoff
    """

    def _retrying(self) -> tenacity.AsyncRetrying:
        """Build Tenacity retrying with custom 429 handling."""

        # Create backoff strategies once, not on every retry
        standard_backoff = tenacity.wait_exponential_jitter(
            initial=self.retry_backoff_factor, jitter=self.retry_max_jitter
        )
        rate_limit_backoff = tenacity.wait_exponential_jitter(
            initial=self.retry_backoff_factor, jitter=self.retry_max_jitter, max=60
        )

        def wait_with_retry_after(retry_state: tenacity.RetryCallState) -> float:
            """Wait strategy that respects Retry-After header for 429 errors."""
            exception = retry_state.outcome.exception()

            if isinstance(exception, APIClientError) and exception.status_code == 429:
                retry_after = getattr(exception, "retry_after", None)
                if retry_after is not None:
                    # Add aggressive jitter to desynchronize concurrent retries (0.5x to 5.0x)
                    jitter_factor = 0.5 + (random.random() * 4.5)
                    wait_time = max(0.1, retry_after * jitter_factor)
                    logger.debug(
                        f"Rate limited (429). Retry-After: {retry_after}s, "
                        f"waiting {wait_time:.2f}s (jitter factor: {jitter_factor:.2f}x)"
                    )
                    return wait_time
                logger.debug(
                    "Rate limited (429) without Retry-After header, using exponential backoff"
                )
                return rate_limit_backoff(retry_state)

            return standard_backoff(retry_state)

        def should_retry_request(exc: BaseException) -> bool:
            """Determine if a request should be retried based on the exception."""
            if isinstance(exc, httpx.RequestError):
                return True
            if isinstance(exc, httpx.HTTPStatusError):
                return exc.response.status_code in RETRIED_HTTP_CODES
            if isinstance(exc, APIClientError):
                return exc.status_code in RETRIED_HTTP_CODES
            # Also check for ForceRetry from the client's auth logic
            if exc.__class__.__name__ == "ForceRetry":
                return True
            return False

        def should_stop(retry_state: tenacity.RetryCallState) -> bool:
            """Stop after n_retries attempts for most errors, but never stop for 429 rate limits."""
            exception = retry_state.outcome.exception() if retry_state.outcome else None

            # For 429 errors, never stop retrying
            if isinstance(exception, APIClientError) and exception.status_code == 429:
                logger.debug(
                    f"Rate limited (429) - continuing retries (attempt {retry_state.attempt_number})"
                )
                return False

            # For other errors, use the standard retry count
            return retry_state.attempt_number >= self.n_retries

        return tenacity.AsyncRetrying(
            wait=wait_with_retry_after,
            retry=tenacity.retry_if_exception(should_retry_request),
            stop=should_stop,
            reraise=True,
        )

    async def _raise_for_status(
        self, response: httpx.Response, method: HttpMethod
    ) -> None:
        """Raise an exception in case of HTTP error, extracting retry_after for 429s."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            content = (
                response.content if response.stream is None else await response.aread()
            )

            # Extract Retry-After header for 429 errors
            retry_after = None
            if response.status_code == 429 and "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    logger.warning(
                        f"Invalid Retry-After header value: {response.headers['Retry-After']}"
                    )

            error = APIClientError(
                method, response.url, response.status_code, content.decode("utf-8")
            )
            # Add retry_after as a custom attribute
            error.retry_after = retry_after
            raise error from e


class CustomAsyncRossumAPIClient(AsyncRossumAPIClient):
    """
    AsyncRossumAPIClient that uses CustomInternalAsyncClient for enhanced retry logic.

    This is a drop-in replacement for AsyncRossumAPIClient with the same API.
    """

    def __init__(
        self,
        base_url: str,
        credentials: UserCredentials | Token,
        *,
        deserializer: typing.Any | None = None,
        timeout: float | None = None,
        n_retries: int = 3,
        retry_backoff_factor: float = 1.0,
        retry_max_jitter: float = 1.0,
        max_in_flight_requests: int = 4,
        response_post_processor: typing.Any | None = None,
    ) -> None:
        """
        Initialize the custom Rossum API client.

        Args:
            base_url: Base URL for the Rossum API
            credentials: Token or UserCredentials for authentication
            deserializer: Custom deserialization callable
            timeout: Request timeout in seconds
            n_retries: Number of retries for non-429 errors (default: 3)
            retry_backoff_factor: Base backoff time in seconds (default: 1.0)
            retry_max_jitter: Maximum random jitter to add to backoff (default: 1.0)
            max_in_flight_requests: Maximum concurrent requests
            response_post_processor: Response post-processing callable
        """
        # Call parent to set up deserializer and other properties
        super().__init__(
            base_url=base_url,
            credentials=credentials,
            deserializer=deserializer,
            timeout=timeout,
            n_retries=n_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_max_jitter=retry_max_jitter,
            max_in_flight_requests=max_in_flight_requests,
            response_post_processor=response_post_processor,
        )

        # Replace the standard InternalAsyncClient with our custom one
        # Extract credentials components
        username = (
            credentials.username if isinstance(credentials, UserCredentials) else None
        )
        password = (
            credentials.password if isinstance(credentials, UserCredentials) else None
        )
        token = credentials.token if isinstance(credentials, Token) else None

        self._http_client = CustomInternalAsyncClient(
            base_url=base_url,
            username=username,
            password=password,
            token=token,
            timeout=timeout,
            n_retries=n_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_max_jitter=retry_max_jitter,
            max_in_flight_requests=max_in_flight_requests,
            response_post_processor=response_post_processor,
        )
