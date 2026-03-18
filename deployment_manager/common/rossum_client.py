from __future__ import annotations

import random

import httpx
import tenacity
from rich.console import Console
from rich.panel import Panel
from rossum_api import APIClientError, AsyncRossumAPIClient
from rossum_api.clients.internal_async_client import InternalAsyncClient
from rossum_api.domain_logic.retry import should_retry
from rossum_api.types import HttpMethod


class _CustomAPIClientError(APIClientError):
    def __init__(self, method: HttpMethod, url: str, status_code: int, error: str, retry_after: int | None = None):
        super().__init__(method, url, status_code, error)
        self.retry_after = retry_after


def _wait_with_retry_after(retry_backoff_factor: float, retry_max_jitter: float):
    standard_backoff = tenacity.wait_exponential_jitter(initial=retry_backoff_factor, jitter=retry_max_jitter)
    rate_limit_backoff = tenacity.wait_exponential_jitter(initial=retry_backoff_factor, jitter=retry_max_jitter, max=60)

    def wait_func(retry_state: tenacity.RetryCallState) -> float:
        exception = retry_state.outcome.exception()
        if isinstance(exception, _CustomAPIClientError) and exception.status_code == 429:
            if exception.retry_after is not None:
                jitter_factor = 0.5 + (random.random() * 4.5)
                return max(0.1, exception.retry_after * jitter_factor)
            return rate_limit_backoff(retry_state)
        return standard_backoff(retry_state)

    return wait_func


def _rate_limit_stop_strategy(n_retries: int):
    def should_stop(retry_state: tenacity.RetryCallState) -> bool:
        exception = retry_state.outcome.exception() if retry_state.outcome else None
        if isinstance(exception, _CustomAPIClientError) and exception.status_code == 429:
            if retry_state.attempt_number > 8:
                Console().print(
                    Panel(
                        f"High retry count detected: {retry_state.attempt_number} retries. "
                        f"Consider lowering concurrency with --concurrency flag or PRD2_CONCURRENCY env var."
                    ),
                    style="bold yellow",
                )
            return False
        return retry_state.attempt_number >= n_retries

    return should_stop


class _CustomInternalClient(InternalAsyncClient):
    def _retrying(self) -> tenacity.AsyncRetrying:
        return tenacity.AsyncRetrying(
            wait=_wait_with_retry_after(self.retry_backoff_factor, self.retry_max_jitter),
            retry=tenacity.retry_if_exception(should_retry),
            stop=_rate_limit_stop_strategy(self.n_retries),
            reraise=True,
        )

    async def _raise_for_status(self, response: httpx.Response, method: HttpMethod) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            content = response.content if response.stream is None else await response.aread()
            retry_after = None
            if response.status_code == 429 and "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass
            raise _CustomAPIClientError(
                method, str(response.url), response.status_code, content.decode("utf-8"), retry_after
            ) from e


class CustomAsyncAPIClient(AsyncRossumAPIClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The parent already created _http_client as InternalAsyncClient.
        # We can't pass our subclass in, so we reassign __class__ to swap the methods.
        self._http_client.__class__ = _CustomInternalClient
