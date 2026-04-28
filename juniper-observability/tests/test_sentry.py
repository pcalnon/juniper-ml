"""Tests for ``configure_sentry`` and the SEC-10 ``before_send`` hook."""

from unittest.mock import patch

import pytest

from juniper_observability import configure_sentry
from juniper_observability.sentry import _strip_sensitive_headers

pytest.importorskip("sentry_sdk")


class TestConfigureSentry:
    def test_noop_when_dsn_is_none(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(None, "juniper-test", "1.0.0")
            mock_init.assert_not_called()

    def test_noop_when_dsn_is_empty(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("", "juniper-test", "1.0.0")
            mock_init.assert_not_called()

    def test_initializes_when_dsn_provided(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.2.3")
        mock_init.assert_called_once()
        kwargs = mock_init.call_args.kwargs
        assert kwargs["dsn"] == "https://key@sentry.io/0"
        assert kwargs["release"] == "juniper-test@1.2.3"

    def test_default_send_pii_is_false(self):
        """SEC-10: default-deny PII forwarding."""
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0")
        assert mock_init.call_args.kwargs["send_default_pii"] is False

    def test_send_pii_true_honored(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", send_pii=True)
        assert mock_init.call_args.kwargs["send_default_pii"] is True

    def test_default_traces_sample_rate(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0")
        assert mock_init.call_args.kwargs["traces_sample_rate"] == 0.1

    def test_custom_traces_sample_rate(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", traces_sample_rate=0.5)
        assert mock_init.call_args.kwargs["traces_sample_rate"] == 0.5

    def test_before_send_hook_always_installed(self):
        """SEC-10: ``before_send`` hook scrubs sensitive headers regardless of ``send_pii``."""
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", send_pii=True)
        before_send = mock_init.call_args.kwargs["before_send"]
        assert before_send is _strip_sensitive_headers


class TestStripSensitiveHeaders:
    def test_filters_x_api_key(self):
        event = {"request": {"headers": {"X-API-Key": "secret"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["headers"]["X-API-Key"] == "[Filtered]"

    def test_filters_authorization(self):
        event = {"request": {"headers": {"Authorization": "Bearer xyz"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["headers"]["Authorization"] == "[Filtered]"

    def test_filters_cookie(self):
        event = {"request": {"headers": {"Cookie": "session=abc"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["headers"]["Cookie"] == "[Filtered]"

    def test_case_insensitive(self):
        """Lower-case, upper-case, mixed all filtered."""
        event = {"request": {"headers": {"x-api-key": "a", "AUTHORIZATION": "b", "CoOkIe": "c"}}}
        result = _strip_sensitive_headers(event, None)
        for v in result["request"]["headers"].values():
            assert v == "[Filtered]"

    def test_preserves_non_sensitive_headers(self):
        event = {"request": {"headers": {"User-Agent": "curl/8.0", "X-Trace-Id": "trace-1"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["headers"]["User-Agent"] == "curl/8.0"
        assert result["request"]["headers"]["X-Trace-Id"] == "trace-1"

    def test_handles_missing_request_key(self):
        """No request key in event → returned unchanged."""
        event = {"level": "error"}
        result = _strip_sensitive_headers(event, None)
        assert result == event

    def test_handles_non_dict_event(self):
        """Non-dict event types (rare) returned unchanged."""
        event = "not a dict"
        result = _strip_sensitive_headers(event, None)
        assert result == event
