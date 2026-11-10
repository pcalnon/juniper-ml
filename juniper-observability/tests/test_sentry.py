"""Tests for ``configure_sentry`` and the SEC-10 ``before_send`` / ``before_send_transaction`` hook."""

import hmac
import json
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

    @pytest.mark.parametrize("traces_sample_rate", [0.0, 0.1, 1.0])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_before_send_hook_always_installed(self, send_pii, traces_sample_rate):
        """SEC-10: ``before_send`` hook scrubs sensitive headers regardless of ``send_pii``.

        And of the sample rate, which governs transactions only: an error event is sent at 0.0
        too (round 2 of P3-07's validation: a hook installed only above 0.0 passed every test).
        """
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=traces_sample_rate)
        before_send = mock_init.call_args.kwargs["before_send"]
        assert before_send is _strip_sensitive_headers

    @pytest.mark.parametrize("traces_sample_rate", [0.0, 0.1, 1.0])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_before_send_transaction_hook_always_installed(self, send_pii, traces_sample_rate):
        """The SDK never hands a transaction to ``before_send``, so the same hook must be installed for transactions too.

        Round-42 finding F2: without it, a ``send_pii=True`` transaction carried the raw ``X-API-Key``.
        Whatever the sample rate: at 0.0 the SDK still sends a transaction that the caller's
        ``sentry-trace`` header marks sampled (the wire test for it is in
        ``TestNoSensitiveRequestValueReachesTheWire``).
        """
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("https://key@sentry.io/0", "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=traces_sample_rate)
        assert mock_init.call_args.kwargs["before_send_transaction"] is _strip_sensitive_headers

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

    @pytest.mark.parametrize("name", ["Proxy-Authorization", "Sec-WebSocket-Protocol", "X-CSRF-Token", "X-XSRF-Token"])
    def test_filters_the_headers_added_in_0_4_2(self, name):
        """Each carries a credential or a session-bound token (owner ruling, 2026-11-08).

        ``Sec-WebSocket-Protocol`` is where juniper-canopy's server reads a WebSocket key
        (``bearer, <key>``) when its opt-in ``ws_auth_enabled`` is on; it and the two CSRF tokens
        are on neither of the SDK's own lists.
        """
        event = {"request": {"headers": {name: _SECRET, "User-Agent": "curl/8.0"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["headers"] == {name: "[Filtered]", "User-Agent": "curl/8.0"}

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

    def test_redacts_every_parsed_cookie_value_and_keeps_the_names(self):
        """``request.cookies`` is the ``Cookie`` header parsed; a name list cannot say which cookie is a session.

        The names stay so the result is still a cookie dict: the protocol reads a STRING ``cookies``
        as a raw ``Cookie`` header, which a bare ``[Filtered]`` is not.
        """
        event = {"request": {"headers": {"User-Agent": "curl/8.0"}, "cookies": {"juniper_auth": _SECRET, "theme": "dark"}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"]["cookies"] == {"juniper_auth": "[Filtered]", "theme": "[Filtered]"}
        assert result["request"]["headers"] == {"User-Agent": "curl/8.0"}

    def test_redacts_a_single_parsed_cookie(self):
        """One cookie is the common case: juniper-canopy's own session is the single ``canopy_session``."""
        event = {"request": {"cookies": {"canopy_session": _SECRET}}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"] == {"cookies": {"canopy_session": "[Filtered]"}}

    @pytest.mark.parametrize("headers", [None, [["X-Trace-Id", "t"]], "X-Trace-Id: t"], ids=["none", "list-of-pairs", "string"])
    def test_redacts_cookies_whatever_shape_the_headers_have(self, headers):
        """The cookie step does not depend on the header step: an odd or absent ``headers`` skips only the header filter."""
        before = repr(headers)  # a snapshot: the event holds the same object, so an in-place change would hide
        event = {"request": {"headers": headers, "cookies": {"juniper_auth": _SECRET}}}
        result = _strip_sensitive_headers(event, None)
        assert repr(result["request"]["headers"]) == before
        assert result["request"]["cookies"] == {"juniper_auth": "[Filtered]"}

    @pytest.mark.parametrize("cookies", ["juniper_auth=" + _SECRET, [["juniper_auth", _SECRET]], ("juniper_auth", _SECRET)], ids=["raw-string", "list-of-pairs", "tuple"])
    def test_drops_parsed_cookies_of_any_other_shape(self, cookies):
        """Only the dict the SDK's integrations produce is redacted, into a dict of the same names; any other shape goes."""
        event = {"request": {"headers": {"User-Agent": "curl/8.0"}, "cookies": cookies}}
        result = _strip_sensitive_headers(event, None)
        assert result["request"] == {"headers": {"User-Agent": "curl/8.0"}}

    @pytest.mark.parametrize(
        "request_data",
        [{"headers": {}}, {"headers": {}, "cookies": {}}, {"headers": {}, "cookies": None}, {"headers": {}, "cookies": ""}, {"headers": {}, "cookies": []}],
        ids=["absent", "empty-dict", "none", "empty-string", "empty-list"],
    )
    def test_leaves_absent_or_empty_cookies_alone(self, request_data):
        """Nothing to hide: an absent or empty ``cookies`` is not turned into a ``[Filtered]`` that claims otherwise."""
        before = repr(request_data)
        result = _strip_sensitive_headers({"request": request_data}, None)
        assert repr(result["request"]) == before


def _frames(*names):
    """Protocol-shaped frames, each carrying a ``vars`` snapshot that holds the secret.

    Each is marked ``in_app: False``, library code, which is what a frame in an installed package
    is: juniper-data's image installs juniper-data itself (``pip install --no-deps .``), so its
    own ``validate`` frame is library code there, and an installed service-core's ``validate``
    serialises as ``in_app: False``. Until these frames carried the mark, no test frame was
    marked library code, and a backstop that skipped library frames passed every test here
    (round-42 finding F6).
    """
    return [{"function": name, "lineno": 1, "in_app": False, "vars": {"candidate": repr(_SECRET)}} for name in names]


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

    def test_drops_vars_from_library_and_application_frames_alike(self):
        """``in_app`` changes how Sentry displays and groups a frame, never whether its locals may leave."""
        frames = [
            {"function": "library", "in_app": False, "vars": {"candidate": repr(_SECRET)}},
            {"function": "application", "in_app": True, "vars": {"candidate": repr(_SECRET)}},
            {"function": "unmarked", "vars": {"candidate": repr(_SECRET)}},
        ]
        event = {"exception": {"values": [{"stacktrace": {"frames": frames}}]}}
        _strip_sensitive_headers(event, None)
        assert [frame["function"] for frame in frames] == ["library", "application", "unmarked"]
        assert all("vars" not in frame for frame in frames)

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

    @pytest.mark.parametrize("how", _CAPTURE_PATHS)
    def test_the_before_send_hook_strips_a_library_frame_too(self, wire, how):
        """A frame in an installed package is library code; ``in_app_exclude`` makes this one library code too.

        Round-42 finding F6: no frame these tests produced was marked library code, so a backstop that
        skipped library frames stayed green. Local-variable capture is back ON here, as in the test above,
        so only the hook stands between the frame's locals and the wire.
        """
        transport, overrides = wire
        overrides["include_local_variables"] = True
        overrides["in_app_exclude"] = [__name__]
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture(how)

        frame = _finding_frame(transport)
        # The case under test, or the absence below proves nothing about library frames.
        assert frame["in_app"] is False
        assert "vars" not in frame
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


#: The secret in every header the hook names. The ``Cookie`` header holds two cookies: ``session``
#: is on the SDK's own ``EventScrubber`` denylist and ``juniper_auth`` is not, which is the whole
#: difference between a scrubber that redacts by name and this hook.
_SENSITIVE_REQUEST_HEADERS = {
    "X-API-Key": _SECRET,
    "Authorization": "Bearer " + _SECRET,
    "Cookie": "session=" + _SECRET + "; juniper_auth=" + _SECRET,
    "Proxy-Authorization": "Basic " + _SECRET,
    "Sec-WebSocket-Protocol": "bearer, " + _SECRET,
    "X-CSRF-Token": _SECRET,
    "X-XSRF-Token": _SECRET,
}

#: As the ASGI integration records them: lower-case. Spelled out rather than read from the
#: module, so that dropping a name from the hook's set fails here instead of shrinking the test.
_SENSITIVE_HEADER_NAMES = ("x-api-key", "authorization", "cookie", "proxy-authorization", "sec-websocket-protocol", "x-csrf-token", "x-xsrf-token")

#: The parsed cookies, as the hook leaves them: every name kept, every value gone.
_FILTERED_COOKIES = {"session": "[Filtered]", "juniper_auth": "[Filtered]"}

#: A caller's trace header that marks the trace sampled upstream (the trailing ``-1``).
_PARENT_SAMPLED = {"sentry-trace": "771a43a4192642f0b136d5159a501700-b7ad6b7169203331-1"}

#: The item each route sends: a plain request sends a transaction, a failing one an error event too.
_ITEM_ROUTES = [("transaction", "/ok"), ("event", "/boom")]


def _drive_one_request(route, extra_headers=None):
    """One request through FastAPI and the SDK's own ASGI integration, the way a service takes it."""
    import sentry_sdk
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    TestClient(app, raise_server_exceptions=False).get(route, headers={**_SENSITIVE_REQUEST_HEADERS, **(extra_headers or {})})
    sentry_sdk.flush()


def _the_request(transport, item_type):
    """The ``request`` interface of the one ``item_type`` item the transport received, or fail.

    An absence assertion is vacuous unless the item that WOULD carry the secret was sent.
    """
    payloads = [json.loads(item.get_bytes()) for envelope in transport.envelopes for item in envelope.items if item.type == item_type]
    assert len(payloads) == 1, f"expected one {item_type} item, got {len(payloads)} ({len(transport.envelopes)} envelopes)"
    return payloads[0]["request"]


def _scrubbing_nothing():
    """An ``EventScrubber`` with empty denylists: the SDK's own name-based redaction, turned off."""
    from sentry_sdk.scrubber import EventScrubber

    return EventScrubber(denylist=[], pii_denylist=[])


class TestNoSensitiveRequestValueReachesTheWire:
    """End to end: no value of a header the hook names, and no parsed cookie, reaches Sentry, in an error event or a transaction.

    The scope is exactly that: the seven headers in ``_SENSITIVE_HEADER_NAMES`` and
    ``request.cookies``. Query strings, request bodies, breadcrumbs, exception values and Sentry
    Logs are other channels, which the hook does not touch and this class does not test.

    Round-42 finding F2: the SDK hands a transaction to ``before_send_transaction``, never to
    ``before_send``. Under ``send_pii=True`` its own header filter is off, and its ``EventScrubber``
    redacts by name: the denylist holds ``x_api_key`` but not ``x-api-key``, and ``session`` but not
    ``juniper_auth``. So until 0.4.2 every sampled transaction carried the raw ``X-API-Key``, and
    both kinds of item carried any cookie the denylist does not name, in the ``request.cookies`` the
    Starlette integration parses out of the header.

    Each layer is pinned on its own, as in the class above: the production configuration; the hook
    with the SDK's scrubbing turned off; and a control with the hook off too, which proves the
    harness sees the leak.
    """

    @pytest.mark.parametrize("send_pii", [False, True])
    @pytest.mark.parametrize(("item_type", "route"), _ITEM_ROUTES)
    def test_no_sensitive_value_reaches_the_wire(self, wire, item_type, route, send_pii):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_request(route)

        request = _the_request(transport, item_type)
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        # The integrations parse the ``Cookie`` header into ``request.cookies`` only under ``send_pii=True``.
        assert request.get("cookies") == (_FILTERED_COOKIES if send_pii else None)
        assert _SECRET.encode() not in _wire_bytes(transport)

    def test_a_parent_sampled_transaction_is_scrubbed_at_a_zero_sample_rate(self, wire):
        """``traces_sample_rate=0.0`` samples nothing itself, but the SDK honours a caller's sampling decision.

        A ``sentry-trace`` header ending ``-1`` marks the trace sampled upstream, so this transaction
        is sent. ``configure_sentry`` is called with the rate itself, not through ``overrides``, so a
        hook installed only when the rate is above zero lets this one through raw (the round-1
        validation's mutant CM07 did, 2026-11-08). juniper-data passes an operator-set rate.
        """
        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True, traces_sample_rate=0.0)

        _drive_one_request("/ok", extra_headers=_PARENT_SAMPLED)

        request = _the_request(transport, "transaction")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert request["cookies"] == _FILTERED_COOKIES
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_an_error_event_is_scrubbed_at_a_zero_sample_rate(self, wire, send_pii):
        """The sample rate governs transactions only: at 0.0 an error event is still sent, and scrubbed.

        Called with the rate itself, as above. A ``before_send`` installed only when the rate is
        above zero sends this event with ``x-csrf-token`` raw under either ``send_pii`` value
        (round 2 of P3-07's validation, 2026-11-08).
        """
        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=0.0)

        _drive_one_request("/boom")

        request = _the_request(transport, "event")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert request.get("cookies") == (_FILTERED_COOKIES if send_pii else None)
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize(("item_type", "route"), _ITEM_ROUTES)
    def test_the_hook_alone_keeps_every_sensitive_value_out(self, wire, item_type, route):
        """``send_pii=True`` turns the SDK's header filter off, and an empty scrubber its denylist."""
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides["event_scrubber"] = _scrubbing_nothing()
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_request(route)

        request = _the_request(transport, item_type)
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert request["cookies"] == _FILTERED_COOKIES
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize(("item_type", "route", "hook"), [("transaction", "/ok", "before_send_transaction"), ("event", "/boom", "before_send")])
    def test_control_the_harness_sees_the_leak_when_the_hook_is_off(self, wire, item_type, route, hook):
        """With the item's hook off as well, every value reaches the wire raw, and this harness sees it.

        If a future SDK starts redacting one of these values itself, this fails: the instrument has
        changed, and the absence assertions above need a value the SDK leaves alone.
        """
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides["event_scrubber"] = _scrubbing_nothing()
        overrides[hook] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_request(route)

        request = _the_request(transport, item_type)
        # Every header, not one: an absence assertion above means nothing for a header that never arrived raw.
        assert {name: _SECRET in request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, True)
        assert request["cookies"] == {"session": _SECRET, "juniper_auth": _SECRET}
        assert _SECRET.encode() in _wire_bytes(transport)
