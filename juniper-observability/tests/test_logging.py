"""Tests for ``JuniperJsonFormatter`` and ``configure_logging``."""

import json
import logging
import sys

import pytest

from juniper_observability import (
    DEFAULT_LOG_FORMAT_PLAIN,
    LOG_FORMAT_JSON,
    JuniperJsonFormatter,
    configure_logging,
    request_id_var,
)


class TestJuniperJsonFormatter:
    def test_format_emits_documented_keys(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert parsed["service"] == "juniper-test"
        assert "timestamp" in parsed
        assert "request_id" in parsed

    def test_format_includes_request_id_from_contextvar(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        token = request_id_var.set("abc-123")
        try:
            record = logging.LogRecord(name="t", level=logging.INFO, pathname="", lineno=0, msg="hi", args=None, exc_info=None)
            parsed = json.loads(formatter.format(record))
            assert parsed["request_id"] == "abc-123"
        finally:
            request_id_var.reset(token)

    def test_format_empty_request_id_when_unset(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        record = logging.LogRecord(name="t", level=logging.INFO, pathname="", lineno=0, msg="hi", args=None, exc_info=None)
        parsed = json.loads(formatter.format(record))
        assert parsed["request_id"] == ""

    def test_format_includes_exception_info(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(name="t", level=logging.ERROR, pathname="", lineno=0, msg="error", args=None, exc_info=exc_info)
            parsed = json.loads(formatter.format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_omits_exception_when_exc_info_none(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        record = logging.LogRecord(name="t", level=logging.INFO, pathname="", lineno=0, msg="ok", args=None, exc_info=None)
        parsed = json.loads(formatter.format(record))
        assert "exception" not in parsed

    def test_format_omits_exception_when_exc_info_tuple_is_none_values(self):
        formatter = JuniperJsonFormatter(service="juniper-test")
        record = logging.LogRecord(name="t", level=logging.INFO, pathname="", lineno=0, msg="ok", args=None, exc_info=(None, None, None))
        parsed = json.loads(formatter.format(record))
        assert "exception" not in parsed


@pytest.fixture
def _isolated_root_logger():
    """Capture and restore the root logger between tests."""
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    yield root
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)


class TestConfigureLogging:
    def test_json_mode_installs_json_formatter(self, _isolated_root_logger):
        configure_logging("INFO", LOG_FORMAT_JSON, "juniper-test")
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JuniperJsonFormatter)

    def test_text_mode_uses_plain_formatter(self, _isolated_root_logger):
        configure_logging("INFO", "text", "juniper-test")
        root = logging.getLogger()
        assert len(root.handlers) == 1
        formatter = root.handlers[0].formatter
        assert formatter is not None
        assert not isinstance(formatter, JuniperJsonFormatter)
        # Plain formatter uses the documented format.
        assert DEFAULT_LOG_FORMAT_PLAIN in (getattr(formatter, "_fmt", "") or "")

    def test_invalid_level_falls_back_to_info(self, _isolated_root_logger):
        configure_logging("BOGUS", "text")
        assert logging.getLogger().level == logging.INFO

    def test_case_insensitive_level(self, _isolated_root_logger):
        configure_logging("debug", "text")
        assert logging.getLogger().level == logging.DEBUG

    def test_replaces_existing_handlers(self, _isolated_root_logger):
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler())
        root.addHandler(logging.StreamHandler())
        configure_logging("INFO", "text")
        assert len(root.handlers) == 1

    def test_handler_level_matches_root_level(self, _isolated_root_logger):
        configure_logging("WARNING", "text")
        root = logging.getLogger()
        assert root.handlers[0].level == logging.WARNING
