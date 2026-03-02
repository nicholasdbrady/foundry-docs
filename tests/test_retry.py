"""Tests for foundry_docs_mcp.retry — retry helpers and adaptive throttling."""

import time
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from foundry_docs_mcp.retry import (
    AdaptiveThrottle,
    _parse_retry_after_value,
    _retryable_status,
    is_retryable_exception,
    retry_after_seconds,
    with_retry,
)


# ---------------------------------------------------------------------------
# _retryable_status
# ---------------------------------------------------------------------------

class TestRetryableStatus:
    @pytest.mark.parametrize("code", [408, 409, 423, 425, 429, 500, 502, 503, 504])
    def test_retryable_codes(self, code):
        assert _retryable_status(code) is True

    @pytest.mark.parametrize("code", [200, 201, 400, 401, 403, 404, 422])
    def test_non_retryable_codes(self, code):
        assert _retryable_status(code) is False

    def test_none_is_retryable(self):
        assert _retryable_status(None) is True


# ---------------------------------------------------------------------------
# _parse_retry_after_value
# ---------------------------------------------------------------------------

class TestParseRetryAfterValue:
    def test_integer_string(self):
        assert _parse_retry_after_value("5") == 5.0

    def test_empty(self):
        assert _parse_retry_after_value("") is None

    def test_whitespace(self):
        assert _parse_retry_after_value("  ") is None

    def test_invalid(self):
        assert _parse_retry_after_value("not-a-date-or-number") is None


# ---------------------------------------------------------------------------
# retry_after_seconds
# ---------------------------------------------------------------------------

class TestRetryAfterSeconds:
    def test_no_response(self):
        exc = Exception("no response attr")
        assert retry_after_seconds(exc) is None

    def test_retry_after_header(self):
        response = MagicMock()
        response.headers = {"retry-after": "3"}
        exc = MagicMock(spec=Exception)
        exc.response = response
        assert retry_after_seconds(exc) == 3.0

    def test_retry_after_ms_header(self):
        response = MagicMock()
        response.headers = {"x-ms-retry-after-ms": "2000"}
        exc = MagicMock(spec=Exception)
        exc.response = response
        assert retry_after_seconds(exc) == 2.0

    def test_no_headers(self):
        response = MagicMock()
        response.headers = {}
        exc = MagicMock(spec=Exception)
        exc.response = response
        assert retry_after_seconds(exc) is None


# ---------------------------------------------------------------------------
# is_retryable_exception
# ---------------------------------------------------------------------------

class TestIsRetryableException:
    def test_rate_limit(self):
        exc = MagicMock(spec=RateLimitError)
        exc.__class__ = RateLimitError
        assert is_retryable_exception(exc) is True

    def test_timeout(self):
        exc = MagicMock(spec=APITimeoutError)
        exc.__class__ = APITimeoutError
        assert is_retryable_exception(exc) is True

    def test_connection_error(self):
        exc = MagicMock(spec=APIConnectionError)
        exc.__class__ = APIConnectionError
        assert is_retryable_exception(exc) is True

    def test_internal_server_error(self):
        exc = MagicMock(spec=InternalServerError)
        exc.__class__ = InternalServerError
        assert is_retryable_exception(exc) is True

    def test_service_request_error(self):
        exc = ServiceRequestError("test")
        assert is_retryable_exception(exc) is True

    def test_service_response_error(self):
        exc = ServiceResponseError("test")
        assert is_retryable_exception(exc) is True

    def test_http_response_429(self):
        exc = HttpResponseError(message="throttled")
        exc.status_code = 429
        assert is_retryable_exception(exc) is True

    def test_http_response_400(self):
        exc = HttpResponseError(message="bad request")
        exc.status_code = 400
        assert is_retryable_exception(exc) is False

    def test_generic_exception(self):
        assert is_retryable_exception(ValueError("nope")) is False


# ---------------------------------------------------------------------------
# with_retry
# ---------------------------------------------------------------------------

class TestWithRetry:
    def test_success_on_first_try(self):
        fn = MagicMock(return_value="ok")
        result = with_retry(fn, operation="test", max_attempts=3, base_delay_s=0.01)
        assert result == "ok"
        assert fn.call_count == 1

    def test_retries_on_transient_error(self):
        fn = MagicMock(side_effect=[ServiceRequestError("fail"), "ok"])
        result = with_retry(fn, operation="test", max_attempts=3, base_delay_s=0.01, max_delay_s=0.02)
        assert result == "ok"
        assert fn.call_count == 2

    def test_raises_after_max_attempts(self):
        fn = MagicMock(side_effect=ServiceRequestError("always fails"))
        with pytest.raises(ServiceRequestError):
            with_retry(fn, operation="test", max_attempts=2, base_delay_s=0.01, max_delay_s=0.02)
        assert fn.call_count == 2

    def test_non_retryable_raises_immediately(self):
        fn = MagicMock(side_effect=ValueError("not retryable"))
        with pytest.raises(ValueError):
            with_retry(fn, operation="test", max_attempts=5, base_delay_s=0.01)
        assert fn.call_count == 1

    def test_single_attempt(self):
        fn = MagicMock(side_effect=ServiceRequestError("fail"))
        with pytest.raises(ServiceRequestError):
            with_retry(fn, operation="test", max_attempts=1, base_delay_s=0.01)
        assert fn.call_count == 1


# ---------------------------------------------------------------------------
# AdaptiveThrottle
# ---------------------------------------------------------------------------

class TestAdaptiveThrottle:
    def test_no_pause_no_wait(self):
        throttle = AdaptiveThrottle()
        throttle.wait()  # should return immediately

    def test_pause_then_wait(self):
        throttle = AdaptiveThrottle()
        throttle.pause(0.1)
        start = time.monotonic()
        throttle.wait()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05  # should have waited ~0.1s

    def test_disabled(self):
        with patch.dict("os.environ", {"FOUNDRY_ADAPTIVE_THROTTLE_ENABLED": "0"}):
            throttle = AdaptiveThrottle()
        throttle.pause(10.0)
        start = time.monotonic()
        throttle.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # should not wait when disabled

    def test_max_pause_capped(self):
        with patch.dict("os.environ", {"FOUNDRY_ADAPTIVE_THROTTLE_MAX_PAUSE_S": "0.2"}):
            throttle = AdaptiveThrottle()
        throttle.pause(100.0)  # request 100s, should be capped to 0.2s
        start = time.monotonic()
        throttle.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

    def test_with_retry_uses_throttle(self):
        throttle = AdaptiveThrottle()
        fn = MagicMock(side_effect=[ServiceRequestError("fail"), "ok"])
        result = with_retry(
            fn, operation="test", max_attempts=3,
            base_delay_s=0.01, max_delay_s=0.02, throttle=throttle,
        )
        assert result == "ok"
