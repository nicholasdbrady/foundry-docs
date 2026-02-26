"""Retry helpers for transient network/API failures."""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TypeVar

from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError
from openai import APIConnectionError, APIStatusError, APITimeoutError, InternalServerError, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AdaptiveThrottle:
    """Shared throttle gate for concurrent workers after rate-limit signals."""

    def __init__(self):
        self.enabled = os.environ.get("FOUNDRY_ADAPTIVE_THROTTLE_ENABLED", "1") != "0"
        self.max_pause_s = _env_float("FOUNDRY_ADAPTIVE_THROTTLE_MAX_PAUSE_S", 60.0)
        self._next_allowed_at = 0.0
        self._lock = threading.Lock()

    def wait(self):
        if not self.enabled:
            return
        while True:
            with self._lock:
                delay = self._next_allowed_at - time.monotonic()
            if delay <= 0:
                return
            time.sleep(min(delay, 0.5))

    def pause(self, seconds: float):
        if not self.enabled:
            return
        capped = max(0.0, min(seconds, self.max_pause_s))
        if capped <= 0:
            return
        with self._lock:
            now = time.monotonic()
            target = now + capped
            if target > self._next_allowed_at:
                self._next_allowed_at = target


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _retryable_status(status_code: int | None) -> bool:
    if status_code is None:
        return True
    return status_code in {408, 409, 423, 425, 429} or status_code >= 500


def _parse_retry_after_value(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        return float(raw)
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (dt - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delta)
    except Exception:
        return None


def retry_after_seconds(exc: Exception) -> float | None:
    """Extract server-requested retry delay in seconds when available."""
    response = getattr(exc, "response", None)
    if response is None:
        return None

    headers = getattr(response, "headers", None)
    if not headers:
        return None

    retry_after = _parse_retry_after_value(headers.get("retry-after", ""))
    if retry_after is not None:
        return retry_after

    retry_after_ms = headers.get("x-ms-retry-after-ms")
    if retry_after_ms:
        try:
            return max(0.0, float(retry_after_ms) / 1000.0)
        except ValueError:
            return None
    return None


def is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)):
        return True

    if isinstance(exc, APIStatusError):
        status_code = getattr(exc, "status_code", None)
        return _retryable_status(status_code)

    if isinstance(exc, (ServiceRequestError, ServiceResponseError)):
        return True

    if isinstance(exc, HttpResponseError):
        status_code = getattr(exc, "status_code", None)
        if status_code is None and getattr(exc, "response", None) is not None:
            status_code = getattr(exc.response, "status_code", None)
        return _retryable_status(status_code)

    return False


def with_retry(
    fn: Callable[[], T],
    *,
    operation: str,
    max_attempts: int | None = None,
    base_delay_s: float | None = None,
    max_delay_s: float | None = None,
    jitter_ratio: float | None = None,
    throttle: AdaptiveThrottle | None = None,
) -> T:
    """Execute an operation with exponential backoff + jitter on transient errors."""
    max_attempts = max_attempts or _env_int("FOUNDRY_RETRY_MAX_ATTEMPTS", 5)
    base_delay_s = base_delay_s or _env_float("FOUNDRY_RETRY_BASE_DELAY_S", 0.5)
    max_delay_s = max_delay_s or _env_float("FOUNDRY_RETRY_MAX_DELAY_S", 8.0)
    jitter_ratio = jitter_ratio if jitter_ratio is not None else _env_float("FOUNDRY_RETRY_JITTER_RATIO", 0.2)

    if max_attempts < 1:
        max_attempts = 1

    attempt = 1
    while True:
        try:
            if throttle is not None:
                throttle.wait()
            return fn()
        except Exception as exc:
            retryable = is_retryable_exception(exc)
            if not retryable or attempt >= max_attempts:
                raise

            delay = min(base_delay_s * (2 ** (attempt - 1)), max_delay_s)
            retry_after = retry_after_seconds(exc)
            if retry_after is not None:
                delay = max(delay, retry_after)
            jitter = delay * jitter_ratio * random.random()
            sleep_s = min(delay + jitter, max_delay_s)
            if throttle is not None:
                throttle.pause(sleep_s)
            logger.warning(
                "Retrying %s after attempt %s/%s due to %s; sleeping %.2fs",
                operation,
                attempt,
                max_attempts,
                type(exc).__name__,
                sleep_s,
            )
            time.sleep(sleep_s)
            attempt += 1
