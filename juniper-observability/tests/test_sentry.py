"""Tests for ``configure_sentry`` and the SEC-10 ``before_send`` hook."""

import hmac
import logging
from unittest.mock import patch

import pytest

from juniper_observability import configure_sentry
from juniper_observability import sentry as sentry_module
from juniper_observability.sentry import _strip_frame_local_variables, _strip_sensitive_headers

pytest.importorskip("sentry_sdk")

# The configured key the leak exposed. Built at import time so that the whole value
# never appears in this file's SOURCE: the SDK ships ~5 lines of source context around
# every frame, and a literal here would reach the wire through that channel and make
# every "is the secret absent?" assertion below fail for the wrong reason.
_SECRET = "-".join(("real", "configured", "key", "LEAKMARK", "7f3a"))


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

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_local_variables_are_never_captured(self, send_pii):
        """The SDK default is ``include_local_variables=True``; it must be off, whatever ``send_pii`` says.

        ``is False`` rather than falsy: omitting the key would leave the SDK default, which is on.
        """
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", send_pii=send_pii)
        assert mock_init.call_args.kwargs["include_local_variables"] is False


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


def _frames(*names):
    """Protocol-shaped frames, each carrying a ``vars`` snapshot that holds the secret."""
    return [{"function": name, "lineno": 1, "vars": {"candidate": repr(_SECRET)}} for name in names]


class TestStripFrameLocalVariables:
    """The ``before_send`` backstop: no frame ``vars`` survive, wherever the protocol puts frames."""

    def test_drops_vars_from_every_exception_in_a_chain(self):
        event = {"exception": {"values": [{"type": "KeyError", "stacktrace": {"frames": _frames("a", "b")}}, {"type": "TypeError", "stacktrace": {"frames": _frames("c")}}]}}
        _strip_sensitive_headers(event, None)
        frames = [frame for value in event["exception"]["values"] for frame in value["stacktrace"]["frames"]]
        assert len(frames) == 3
        assert all("vars" not in frame for frame in frames)
        # Only the snapshot goes; the rest of each frame is kept for the report.
        assert [frame["function"] for frame in frames] == ["a", "b", "c"]

    def test_drops_vars_from_thread_stacktraces(self):
        """``attach_stacktrace`` and the logging integration's ``stack_info`` put frames under ``threads``."""
        event = {"threads": {"values": [{"stacktrace": {"frames": _frames("worker")}, "current": True}]}}
        _strip_sensitive_headers(event, None)
        assert "vars" not in event["threads"]["values"][0]["stacktrace"]["frames"][0]

    def test_drops_vars_from_a_top_level_stacktrace(self):
        event = {"stacktrace": {"frames": _frames("handler")}}
        _strip_sensitive_headers(event, None)
        assert "vars" not in event["stacktrace"]["frames"][0]

    def test_scrubs_headers_and_frames_in_the_same_event(self):
        """The two halves of the hook are independent: doing one must not skip the other."""
        event = {"request": {"headers": {"X-API-Key": _SECRET}}, "exception": {"values": [{"stacktrace": {"frames": _frames("validate")}}]}}
        _strip_sensitive_headers(event, None)
        assert event["request"]["headers"]["X-API-Key"] == "[Filtered]"
        assert _SECRET not in repr(event)

    @pytest.mark.parametrize(
        "event",
        [
            {"exception": "not-a-dict"},
            {"exception": {"values": "not-a-list"}},
            {"exception": {"values": ["not-a-dict", {"no": "stacktrace"}, {"stacktrace": "not-a-dict"}]}},
            {"threads": {"values": [{"stacktrace": {"frames": "not-a-list"}}]}},
            {"stacktrace": {"frames": ["not-a-dict", {"function": "no-vars"}]}},
        ],
    )
    def test_tolerates_unexpected_shapes(self, event):
        """A hook that raises drops the event; an odd shape is no reason to lose the report."""
        before = repr(event)
        assert _strip_frame_local_variables(event) is None
        assert repr(event) == before


def _validate_like_the_finding(api_key, configured_keys):
    """The shape juniper-canopy#683's validation found: the comparison loop of ``APIKeyAuth.validate``.

    ``hmac.compare_digest`` raises ``TypeError`` on a non-ASCII ``str`` -- here the ``\\xa0``
    an anonymous caller sent -- so this frame dies holding ``candidate``: the REAL configured
    key, under a name no scrubber denylist carries. The parameter keeps ``validate``'s own
    name, ``api_key``, because that one IS on the SDK's denylist, and the control below shows
    the difference.
    """
    matched = False
    for candidate in configured_keys:
        if hmac.compare_digest(api_key, candidate):
            matched = True
    return matched


class _CapturingTransport:
    """Built lazily so that importing this module never needs ``sentry_sdk``."""

    @staticmethod
    def build():
        from sentry_sdk.transport import Transport

        class Capturing(Transport):
            def __init__(self):
                super().__init__()
                self.envelopes = []

            def capture_envelope(self, envelope):
                self.envelopes.append(envelope)

        return Capturing()


@pytest.fixture
def wire(monkeypatch):
    """The REAL SDK, initialised through ``configure_sentry``, with a local transport in place of HTTP.

    Everything upstream of the network runs for real -- event construction, frame
    serialisation, the SDK's own ``EventScrubber``, ``before_send`` -- and what the transport
    receives is exactly what would have been POSTed to Sentry. ``overrides`` lets a test
    change one ``sentry_sdk.init`` keyword, which is how each layer is disabled in turn.
    """
    import sentry_sdk

    transport = _CapturingTransport.build()
    overrides = {}
    real_init = sentry_sdk.init

    def init_with_local_transport(**kwargs):
        kwargs.update(overrides)
        return real_init(transport=transport, **kwargs)

    monkeypatch.setattr(sentry_sdk, "init", init_with_local_transport)
    try:
        yield transport, overrides
    finally:
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(None)


def _raise_and_capture(how):
    import sentry_sdk

    try:
        # compare_digest raises on the FIRST comparison, so the secret is ``candidate`` when the
        # frame dies (it is also inside ``configured_keys``).
        _validate_like_the_finding("\xa0", [_SECRET, "another-configured-key"])
    except TypeError:
        if how == "capture_exception":
            sentry_sdk.capture_exception()
        else:
            # The uvicorn shape: an unhandled request exception is LOGGED with exc_info.
            logging.getLogger("juniper_observability.tests.wire").exception("Exception in ASGI application")
    sentry_sdk.flush()


def _wire_bytes(transport):
    return b"\n".join(envelope.serialize() for envelope in transport.envelopes)


def _finding_frame(transport):
    """The serialised frame that held the secret, from the error event the transport received.

    Asserting absence is vacuous unless the event that WOULD carry the secret was sent, and
    its frame serialised. This finds that frame or fails.
    """
    for envelope in transport.envelopes:
        event = envelope.get_event()
        if not event or "exception" not in event:
            continue
        for value in event["exception"]["values"]:
            for frame in value.get("stacktrace", {}).get("frames", []):
                if frame.get("function") == _validate_like_the_finding.__name__:
                    assert value["type"] == "TypeError"
                    return frame
    raise AssertionError(f"no error event carrying the {_validate_like_the_finding.__name__} frame reached the transport ({len(transport.envelopes)} envelopes)")


_CAPTURE_PATHS = ["capture_exception", "logging"]


class TestNoSecretLocalReachesTheWire:
    """End to end: a secret in a frame's locals never reaches Sentry.

    The two layers are pinned separately as well as together. With both, a regression in
    either one would stay green; each single-layer test disables the other layer, so each
    guard has a test that fails without it. The control proves the instrument can see the
    leak at all.
    """

    @pytest.mark.parametrize("how", _CAPTURE_PATHS)
    def test_a_captured_exception_never_carries_a_secret_local(self, wire, how):
        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture(how)

        frame = _finding_frame(transport)
        assert "vars" not in frame
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize("how", _CAPTURE_PATHS)
    def test_the_option_alone_keeps_the_secret_out(self, wire, how, monkeypatch):
        """``include_local_variables=False`` with the ``before_send`` backstop disabled."""
        transport, _overrides = wire
        monkeypatch.setattr(sentry_module, "_strip_frame_local_variables", lambda event: None)
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture(how)

        assert "vars" not in _finding_frame(transport)
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize("how", _CAPTURE_PATHS)
    def test_the_before_send_hook_alone_keeps_the_secret_out(self, wire, how):
        """The backstop, with the SDK told to capture locals (the default this package overrides)."""
        transport, overrides = wire
        overrides["include_local_variables"] = True
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture(how)

        assert "vars" not in _finding_frame(transport)
        assert _SECRET.encode() not in _wire_bytes(transport)

    def test_control_the_harness_sees_the_leak_when_both_layers_are_off(self, wire, monkeypatch):
        """The SDK default leaks the configured key, and this harness can see it.

        If this ever passes vacuously -- an SDK that stops snapshotting locals, a transport
        that stops receiving events -- every absence assertion above stops meaning anything,
        which is why it is a test and not a one-off check.
        """
        transport, overrides = wire
        overrides["include_local_variables"] = True
        monkeypatch.setattr(sentry_module, "_strip_frame_local_variables", lambda event: None)
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture("capture_exception")

        frame = _finding_frame(transport)
        assert _SECRET in frame["vars"]["candidate"]
        # The PRESENTED key is redacted by the SDK's own name-based EventScrubber, and that is
        # exactly why the scrubber did not help: the name that mattered was ``candidate``.
        assert frame["vars"]["api_key"] == "[Filtered]"
        assert _SECRET.encode() in _wire_bytes(transport)
