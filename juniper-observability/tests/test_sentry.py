"""Tests for ``configure_sentry`` and its SEC-10 hooks, on sentry-sdk 2.x and 3.x.

The installed sentry-sdk's major decides which options ``configure_sentry`` passes. The option
tests patch that decision, so both majors' options are checked whichever SDK is installed. The wire
tests run the REAL installed SDK, so each major's run covers its own channels: transactions on 2.x,
streamed spans on 3.x, and error events on both.
"""

import asyncio
import hmac
import inspect
import json
import logging
from unittest.mock import patch

import pytest

from juniper_observability import configure_sentry
from juniper_observability import sentry as sentry_module
from juniper_observability.sentry import _strip_frame_local_variables, _strip_sensitive_headers, _strip_sensitive_span_attributes

pytest.importorskip("sentry_sdk")

# The configured key the leak exposed. Built at import time so that the whole value
# never appears in this file's SOURCE: the SDK ships ~5 lines of source context around
# every frame, and a literal here would reach the wire through that channel and make
# every "is the secret absent?" assertion below fail for the wrong reason.
_SECRET = "-".join(("real", "configured", "key", "LEAKMARK", "7f3a"))

#: The installed SDK's major, as ``configure_sentry`` reads it.
_SDK_MAJOR = sentry_module._sentry_sdk_major()
_ON_SDK_2 = pytest.mark.skipif(_SDK_MAJOR >= 3, reason="sentry-sdk 2.x only (transactions, EventScrubber, send_default_pii)")
_ON_SDK_3 = pytest.mark.skipif(_SDK_MAJOR < 3, reason="sentry-sdk 3.x only (streamed spans, data_collection)")

_DSN = "https://key@sentry.io/0"

#: Every option each major's ``sentry_sdk.init`` is given, spelled out. 3.0.0 raises ``TypeError``
#: for any 2.x-only name, and 2.76.0 accepts ``data_collection`` and would change what it sends.
_SDK2_OPTIONS = {"dsn", "traces_sample_rate", "release", "before_send", "send_default_pii", "include_local_variables", "enable_logs", "before_send_transaction"}
_SDK3_OPTIONS = {"dsn", "traces_sample_rate", "release", "before_send", "data_collection", "before_send_span", "integrations", "attach_stacktrace"}

#: As the ASGI integration records them: lower-case. Spelled out rather than read from the
#: module, so that dropping a name from the hook's set fails here instead of shrinking the test.
_SENSITIVE_HEADER_NAMES = ("x-api-key", "authorization", "cookie", "proxy-authorization", "sec-websocket-protocol", "x-csrf-token", "x-xsrf-token")

#: ``_data_collection`` for each ``send_pii``, spelled out for the same reason.
_EXPECTED_DATA_COLLECTION = {
    send_pii: {
        "user_info": send_pii,
        "cookies": {"mode": "allowlist", "terms": []} if send_pii else {"mode": "off"},
        "http_headers": {"request": {"mode": "denylist", "terms": sorted(_SENSITIVE_HEADER_NAMES) if send_pii else sorted([*_SENSITIVE_HEADER_NAMES, "x-forwarded-for", "x-real-ip"])}},
        "stack_frame_variables": False,
        "http_bodies": [],
        "database_query_data": False,
        "queues": send_pii,
        "gen_ai": {"inputs": send_pii, "outputs": send_pii},
        "mcp": {"inputs": send_pii, "outputs": send_pii},
        "graphql": {"document": send_pii, "variables": send_pii},
    }
    for send_pii in (False, True)
}


def _init_kwargs(major, *args, **kwargs):
    """The keywords ``configure_sentry(*args, **kwargs)`` passes to ``sentry_sdk.init`` when the installed SDK's major is ``major``."""
    with patch.object(sentry_module, "_sentry_sdk_major", return_value=major), patch("sentry_sdk.init") as mock_init:
        configure_sentry(*args, **kwargs)
    mock_init.assert_called_once()
    return mock_init.call_args.kwargs


class TestConfigureSentry:
    def test_noop_when_dsn_is_none(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(None, "juniper-test", "1.0.0")
            mock_init.assert_not_called()

    def test_noop_when_dsn_is_empty(self):
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry("", "juniper-test", "1.0.0")
            mock_init.assert_not_called()

    @pytest.mark.parametrize("major", [2, 3])
    def test_initializes_when_dsn_provided(self, major):
        kwargs = _init_kwargs(major, _DSN, "juniper-test", "1.2.3")
        assert kwargs["dsn"] == _DSN
        assert kwargs["release"] == "juniper-test@1.2.3"

    @pytest.mark.parametrize(("major", "expected"), [(2, _SDK2_OPTIONS), (3, _SDK3_OPTIONS)])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_each_major_gets_its_own_options_and_no_other(self, major, expected, send_pii):
        """3.0.0 raises on a 2.x-only option; 2.76.0 would switch to its 3.x behaviour on ``data_collection``."""
        assert set(_init_kwargs(major, _DSN, "juniper-test", "1.0.0", send_pii=send_pii)) == expected

    def test_every_option_is_one_the_installed_sdk_accepts(self):
        """The options for the installed major are all parameters of the installed ``sentry_sdk.init``."""
        from sentry_sdk.consts import ClientConstructor

        accepted = set(inspect.signature(ClientConstructor.__init__).parameters)
        options = set(_init_kwargs(_SDK_MAJOR, _DSN, "juniper-test", "1.0.0"))
        assert options <= accepted, sorted(options - accepted)

    def test_the_installed_major_is_the_one_used(self):
        """Unpatched, ``configure_sentry`` takes the installed SDK's options."""
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(_DSN, "juniper-test", "1.0.0")
        assert set(mock_init.call_args.kwargs) == (_SDK3_OPTIONS if _SDK_MAJOR >= 3 else _SDK2_OPTIONS)

    def test_default_send_pii_is_false(self):
        """SEC-10: default-deny PII forwarding."""
        assert _init_kwargs(2, _DSN, "juniper-test", "1.0.0")["send_default_pii"] is False
        assert _init_kwargs(3, _DSN, "juniper-test", "1.0.0")["data_collection"] == _EXPECTED_DATA_COLLECTION[False]

    def test_send_pii_true_honored(self):
        assert _init_kwargs(2, _DSN, "juniper-test", "1.0.0", send_pii=True)["send_default_pii"] is True
        assert _init_kwargs(3, _DSN, "juniper-test", "1.0.0", send_pii=True)["data_collection"] == _EXPECTED_DATA_COLLECTION[True]

    @pytest.mark.parametrize("major", [2, 3])
    def test_default_traces_sample_rate(self, major):
        assert _init_kwargs(major, _DSN, "juniper-test", "1.0.0")["traces_sample_rate"] == 0.1

    @pytest.mark.parametrize("major", [2, 3])
    def test_custom_traces_sample_rate(self, major):
        assert _init_kwargs(major, _DSN, "juniper-test", "1.0.0", traces_sample_rate=0.5)["traces_sample_rate"] == 0.5

    @pytest.mark.parametrize("major", [2, 3])
    @pytest.mark.parametrize("traces_sample_rate", [0.0, 0.1, 1.0])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_before_send_hook_always_installed(self, major, send_pii, traces_sample_rate):
        """SEC-10: ``before_send`` hook scrubs sensitive headers regardless of ``send_pii``.

        And of the sample rate, which governs transactions only: an error event is sent at 0.0
        too (round 2 of P3-07's validation: a hook installed only above 0.0 passed every test).
        """
        kwargs = _init_kwargs(major, _DSN, "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=traces_sample_rate)
        assert kwargs["before_send"] is _strip_sensitive_headers

    @pytest.mark.parametrize("traces_sample_rate", [0.0, 0.1, 1.0])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_before_send_transaction_hook_always_installed(self, send_pii, traces_sample_rate):
        """The SDK never hands a transaction to ``before_send``, so the same hook must be installed for transactions too.

        Round-42 finding F2: without it, a ``send_pii=True`` transaction carried the raw ``X-API-Key``.
        Whatever the sample rate: at 0.0 the SDK still sends a transaction that the caller's
        ``sentry-trace`` header marks sampled (the wire test for it is in
        ``TestNoSensitiveRequestValueReachesTheWire``).
        """
        kwargs = _init_kwargs(2, _DSN, "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=traces_sample_rate)
        assert kwargs["before_send_transaction"] is _strip_sensitive_headers

    @pytest.mark.parametrize("traces_sample_rate", [0.0, 0.1, 1.0])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_before_send_span_hook_always_installed(self, send_pii, traces_sample_rate):
        """3.x streams spans in place of transactions; each one reaches ``before_send_span``, whatever the sample rate.

        At 0.0 the SDK still samples a span whose caller's ``sentry-trace`` header marks the trace
        sampled (``_make_sampling_decision`` in ``tracing_utils.py``, 3.0.0).
        """
        kwargs = _init_kwargs(3, _DSN, "juniper-test", "1.0.0", send_pii=send_pii, traces_sample_rate=traces_sample_rate)
        assert kwargs["before_send_span"] is _strip_sensitive_span_attributes

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_local_variables_are_never_captured(self, send_pii):
        """The SDK default captures every frame's locals; it must be off, whatever ``send_pii`` says.

        ``is False`` rather than falsy: omitting the key would leave the SDK default, which is on.
        """
        assert _init_kwargs(2, _DSN, "juniper-test", "1.0.0", send_pii=send_pii)["include_local_variables"] is False
        assert _init_kwargs(3, _DSN, "juniper-test", "1.0.0", send_pii=send_pii)["data_collection"]["stack_frame_variables"] is False

    def test_sentry_logs_stay_on(self):
        """0.4.2 passed ``enable_logs=True``. 3.x has no such option and sends Sentry Logs through the logging integration."""
        assert _init_kwargs(2, _DSN, "juniper-test", "1.0.0")["enable_logs"] is True

    def test_the_logging_integration_is_installed_on_3x(self):
        """3.x installs no logging integration by default; without it an ERROR record is neither an event nor a log.

        Its ``event_level`` is pinned on the wire, by the ``logging`` case of
        ``TestNoSecretLocalReachesTheWire`` on 3.x: that event exists only through it.
        """
        from sentry_sdk.integrations.logging import LoggingIntegration

        integrations = _init_kwargs(3, _DSN, "juniper-test", "1.0.0")["integrations"]
        assert [type(integration) for integration in integrations] == [LoggingIntegration]

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_attach_stacktrace_is_off_on_3x(self, send_pii):
        """3.x defaults it to True; 2.x to False. ``is False``: a key whose value flipped would pass a key-set test."""
        assert _init_kwargs(3, _DSN, "juniper-test", "1.0.0", send_pii=send_pii)["attach_stacktrace"] is False


class TestSentrySdkMajor:
    @pytest.mark.parametrize(("version", "major"), [("2.35.0", 2), ("2.76.0", 2), ("3.0.0", 3), ("3.0.1b2", 3), ("3.0.0rc1", 3), ("", 0), ("dev", 0), ("v3.0.0", 0), ("\u00b2.0.0", 0)])
    def test_reads_the_major_from_the_sdk_version(self, version, major):
        with patch("sentry_sdk.VERSION", version):
            assert sentry_module._sentry_sdk_major() == major

    def test_a_stand_in_without_version_reads_as_2(self, monkeypatch):
        """juniper-data's and juniper-cascor's tests replace ``sys.modules["sentry_sdk"]`` with an object that has only ``init``."""
        import sys

        monkeypatch.setitem(sys.modules, "sentry_sdk", type("_StandIn", (), {"init": staticmethod(lambda **kwargs: None)}))
        assert sentry_module._sentry_sdk_major() == 2

    def test_a_stand_in_gets_0_4_2s_options(self, monkeypatch):
        """The consumers' assertion, verbatim in spirit: ``send_default_pii`` is False and the hook is ``before_send``."""
        import sys

        captured = {}
        monkeypatch.setitem(sys.modules, "sentry_sdk", type("_StandIn", (), {"init": staticmethod(lambda **kwargs: captured.update(kwargs))}))
        configure_sentry(_DSN, "juniper-test", "1.0.0")
        assert set(captured) == _SDK2_OPTIONS
        assert captured["send_default_pii"] is False
        assert captured["before_send"] is _strip_sensitive_headers

    def test_a_mock_stand_in_gets_0_4_2s_options(self, monkeypatch):
        """``MagicMock()`` answers ``VERSION`` with another mock: a stand-in, as 0.4.2 treated it, not an unsupported SDK."""
        import sys
        from unittest.mock import MagicMock

        stand_in = MagicMock()
        monkeypatch.setitem(sys.modules, "sentry_sdk", stand_in)
        configure_sentry(_DSN, "juniper-test", "1.0.0")
        assert set(stand_in.init.call_args.kwargs) == _SDK2_OPTIONS
        assert stand_in.init.call_args.kwargs["send_default_pii"] is False

    def test_matches_the_installed_sdk(self):
        import sentry_sdk

        assert _SDK_MAJOR == int(sentry_sdk.VERSION.split(".")[0])


class TestDataCollection:
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_is_exactly_the_expected_mapping(self, send_pii):
        assert sentry_module._data_collection(send_pii) == _EXPECTED_DATA_COLLECTION[send_pii]

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_the_header_denylist_names_every_scrubbed_header(self, send_pii):
        """The SDK filters these at the source, in events and span attributes alike; the hooks are the backstop."""
        terms = sentry_module._data_collection(send_pii)["http_headers"]["request"]["terms"]
        assert set(_SENSITIVE_HEADER_NAMES) <= set(terms)

    def test_the_address_headers_are_filtered_only_without_send_pii(self):
        """2.x removed ``X-Forwarded-For`` and ``X-Real-IP`` unless ``send_default_pii`` was on; 3.x's denylist matches neither."""
        without = set(sentry_module._data_collection(False)["http_headers"]["request"]["terms"])
        with_pii = set(sentry_module._data_collection(True)["http_headers"]["request"]["terms"])
        assert without - with_pii == {"x-forwarded-for", "x-real-ip"}

    def test_each_call_returns_a_fresh_mapping(self):
        """The SDK keeps and resolves the dict it is given; one caller's copy must not be another's."""
        first = sentry_module._data_collection(False)
        first["http_headers"]["request"]["terms"].clear()
        assert sentry_module._data_collection(False) == _EXPECTED_DATA_COLLECTION[False]


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
        """Each carries a credential or a session-bound token (Overtoad ruling, 2026-11-08).

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


def _span(**attributes):
    """A serialised span as 3.x hands it to ``before_send_span``: request headers are one-item lists."""
    return {"trace_id": "771a43a4192642f0b136d5159a501700", "span_id": "b7ad6b7169203331", "name": "GET /ok", "attributes": attributes}


class TestStripSensitiveSpanAttributes:
    """The ``before_send_span`` backstop: no value of a header the hook names survives on a 3.x span."""

    @pytest.mark.parametrize("name", _SENSITIVE_HEADER_NAMES)
    def test_filters_each_sensitive_request_header(self, name):
        span = _span(**{f"http.request.header.{name}": [_SECRET], "http.request.header.user-agent": ["curl/8.0"], "url.path": "/ok"})
        result = _strip_sensitive_span_attributes(span, {})
        assert result["attributes"] == {f"http.request.header.{name}": ["[Filtered]"], "http.request.header.user-agent": ["curl/8.0"], "url.path": "/ok"}

    def test_case_insensitive(self):
        """The ASGI integration records lower-case names; another integration need not."""
        span = _span(**{"http.request.header.X-API-Key": [_SECRET], "HTTP.Request.Header.Authorization": ["Bearer " + _SECRET]})
        result = _strip_sensitive_span_attributes(span, {})
        assert result["attributes"] == {"http.request.header.X-API-Key": ["[Filtered]"], "HTTP.Request.Header.Authorization": ["[Filtered]"]}

    def test_returns_the_span_it_was_given_with_its_name(self):
        """3.0.0 keeps the ORIGINAL span when the hook returns anything without a ``name``, so the same dict comes back."""
        span = _span(**{"http.request.header.x-api-key": [_SECRET]})
        assert _strip_sensitive_span_attributes(span, {}) is span
        assert span["name"] == "GET /ok"

    def test_leaves_every_other_attribute_alone(self):
        """Only ``http.request.header.<name>`` attributes are request headers; nothing else is touched, even a lookalike."""
        attributes = {
            "http.request.method": "GET",
            "http.request.header.accept": ["*/*"],
            "x-api-version": "not a header attribute",
            "http.response.header.authorization": ["a response header, not the request's"],
            "user_agent.original": "curl/8.0",
            "http.response.status_code": 200,
        }
        result = _strip_sensitive_span_attributes(_span(**attributes), {})
        assert result["attributes"] == attributes

    @pytest.mark.parametrize("span", ["not a span", None, ["a", "list"], {"name": "no attributes"}, {"name": "n", "attributes": None}, {"name": "n", "attributes": ["x"]}, {"name": "n", "attributes": "x"}])
    def test_tolerates_unexpected_shapes(self, span):
        """A hook that raised would make the SDK send the original span; an odd shape is returned as it came."""
        before = repr(span)
        assert _strip_sensitive_span_attributes(span, {}) is span
        assert repr(span) == before

    def test_skips_a_key_that_is_not_a_string(self):
        span = {"name": "n", "attributes": {1: "one", "http.request.header.x-api-key": [_SECRET]}}
        result = _strip_sensitive_span_attributes(span, {})
        assert result["attributes"] == {1: "one", "http.request.header.x-api-key": ["[Filtered]"]}


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
    serialisation, the SDK's own scrubbing, the hooks -- and what the transport
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


def _locals_captured():
    """The ``sentry_sdk.init`` override that turns frame-local capture back on, for the installed major."""
    if _SDK_MAJOR >= 3:
        return {"data_collection": {**sentry_module._data_collection(False), "stack_frame_variables": True}}
    return {"include_local_variables": True}


def _locals_redacted_by_name():
    """Frame locals captured, with the SDK's own redaction by NAME: 2.x's ``EventScrubber``, 3.x's denylist mode."""
    if _SDK_MAJOR >= 3:
        return {"data_collection": {**sentry_module._data_collection(False), "stack_frame_variables": {"mode": "denylist"}}}
    return {"include_local_variables": True}


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
    leak at all. On 3.x the ``logging`` path exists only through the logging integration that
    ``configure_sentry`` installs: 3.x's default makes an ERROR record no event at all.
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
        """``include_local_variables=False`` (3.x: ``stack_frame_variables=False``) with the ``before_send`` backstop disabled."""
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
        overrides.update(_locals_captured())
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
        overrides.update(_locals_captured())
        overrides["in_app_exclude"] = [__name__]
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture(how)

        frame = _finding_frame(transport)
        # The case under test, or the absence below proves nothing about library frames.
        assert frame["in_app"] is False
        assert "vars" not in frame
        assert _SECRET.encode() not in _wire_bytes(transport)

    def test_control_the_harness_sees_the_leak_when_both_layers_are_off(self, wire, monkeypatch):
        """The SDK's own name-based redaction leaks the configured key, and this harness can see it.

        If this ever passes vacuously -- an SDK that stops snapshotting locals, a transport
        that stops receiving events -- every absence assertion above stops meaning anything,
        which is why it is a test and not a one-off check.
        """
        transport, overrides = wire
        overrides.update(_locals_redacted_by_name())
        monkeypatch.setattr(sentry_module, "_strip_frame_local_variables", lambda event: None)
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _raise_and_capture("capture_exception")

        frame = _finding_frame(transport)
        assert _SECRET in frame["vars"]["candidate"]
        # The PRESENTED key is redacted by the SDK's own name-based redaction, and that is
        # exactly why it did not help: the name that mattered was ``candidate``.
        assert "[Filtered]" in frame["vars"]["api_key"]
        assert _SECRET.encode() in _wire_bytes(transport)


#: The secret in every header the hook names. The ``Cookie`` header holds two cookies: ``session``
#: is on 2.x's ``EventScrubber`` denylist and ``juniper_auth`` is not, which is the whole difference
#: between redaction by name and this hook on 2.x. 3.x's denylist matches substrings, and ``auth``
#: is one of them, so it filters ``juniper_auth`` itself; its tests use ``_COOKIE_NO_TERM`` instead.
_SENSITIVE_REQUEST_HEADERS = {
    "X-API-Key": _SECRET,
    "Authorization": "Bearer " + _SECRET,
    "Cookie": "session=" + _SECRET + "; juniper_auth=" + _SECRET,
    "Proxy-Authorization": "Basic " + _SECRET,
    "Sec-WebSocket-Protocol": "bearer, " + _SECRET,
    "X-CSRF-Token": _SECRET,
    "X-XSRF-Token": _SECRET,
}

#: The parsed cookies, as the hook leaves them: every name kept, every value gone.
_FILTERED_COOKIES = {"session": "[Filtered]", "juniper_auth": "[Filtered]"}

#: For 3.x: ``canopy_ui`` holds none of the terms 3.x's denylist matches (``data_collection.py``,
#: ``_SENSITIVE_DENYLIST``), so under its denylist mode the SDK collects that cookie raw.
_COOKIE_NO_TERM = {"Cookie": "session=" + _SECRET + "; canopy_ui=" + _SECRET}
_FILTERED_COOKIES_NO_TERM = {"session": "[Filtered]", "canopy_ui": "[Filtered]"}

#: A caller's trace header that marks the trace sampled upstream (the trailing ``-1``).
_PARENT_SAMPLED = {"sentry-trace": "771a43a4192642f0b136d5159a501700-b7ad6b7169203331-1"}

#: The item each route sends on 2.x: a plain request sends a transaction, a failing one an error event too.
_ITEM_ROUTES = [("transaction", "/ok"), ("event", "/boom")]

#: The span attributes 3.x records the hook's headers under.
_SPAN_HEADER_KEYS = tuple(f"http.request.header.{name}" for name in _SENSITIVE_HEADER_NAMES)


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


def _asgi_app():
    """The app ``_drive_one_request`` builds, for a request that no HTTP client carries."""
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/ok")
    def ok():
        return {"ok": True}

    return app


def _drive_one_asgi_request(route, extra_headers=None):
    """The same request, straight into the ASGI app with no HTTP client in between.

    On 3.x the SDK's httpx integration, once set up in a process, replaces a request's own
    ``sentry-trace`` header with the client side's trace (measured on 3.0.0), so a caller's
    sampling decision cannot be sent through ``TestClient``.
    """
    import sentry_sdk

    headers = {**_SENSITIVE_REQUEST_HEADERS, **(extra_headers or {})}
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": route,
        "raw_path": route.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")] + [(name.lower().encode(), value.encode()) for name, value in headers.items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(_asgi_app()(scope, receive, send))
    assert sent and sent[0]["type"] == "http.response.start", sent
    sentry_sdk.flush()


def _the_request(transport, item_type):
    """The ``request`` interface of the one ``item_type`` item the transport received, or fail.

    An absence assertion is vacuous unless the item that WOULD carry the secret was sent.
    """
    payloads = [json.loads(item.get_bytes()) for envelope in transport.envelopes for item in envelope.items if item.type == item_type]
    assert len(payloads) == 1, f"expected one {item_type} item, got {len(payloads)} ({len(transport.envelopes)} envelopes)"
    return payloads[0]["request"]


def _server_span(transport):
    """The attributes of the one ``http.server`` span the transport received, each unwrapped from ``{value, type}``, or fail."""
    spans = [span for envelope in transport.envelopes for item in envelope.items if item.type == "span" for span in json.loads(item.get_bytes())["items"]]
    servers = [span for span in spans if span.get("attributes", {}).get("sentry.op", {}).get("value") == "http.server"]
    assert len(servers) == 1, f"expected one http.server span, got {len(servers)} of {len(spans)} span(s) ({len(transport.envelopes)} envelopes)"
    return {key: value["value"] for key, value in servers[0]["attributes"].items()}


def _scrubbing_nothing():
    """An ``EventScrubber`` with empty denylists: the SDK's own name-based redaction, turned off (2.x only)."""
    from sentry_sdk.scrubber import EventScrubber

    return EventScrubber(denylist=[], pii_denylist=[])


def _sdk_plain_denylist():
    """3.x's ``data_collection`` with ``send_pii`` on and the SDK's own denylists only: no extra header terms, cookies by name.

    The SDK then leaves ``sec-websocket-protocol`` raw (its denylist matches no term in it) and the
    ``canopy_ui`` cookie raw, so only the hooks stand between those and the wire.
    """
    return {"data_collection": {**sentry_module._data_collection(True), "http_headers": {"request": {"mode": "denylist"}}, "cookies": {"mode": "denylist"}}}


class TestNoSensitiveRequestValueReachesTheWire:
    """End to end: no value of a header the hook names, and no parsed cookie, reaches Sentry.

    The scope is exactly that: the seven headers in ``_SENSITIVE_HEADER_NAMES`` and
    ``request.cookies``. Query strings, request bodies, breadcrumbs, exception values and Sentry
    Logs are other channels, which the hooks do not touch and this class does not test.

    Error events are checked on both majors. On 2.x a request also sends a transaction: round-42
    finding F2 was that the SDK hands it to ``before_send_transaction``, never to ``before_send``,
    and that under ``send_pii=True`` its own header filter is off and its ``EventScrubber`` redacts
    by name (``x_api_key`` but not ``x-api-key``, ``session`` but not ``juniper_auth``). On 3.x
    there are no transactions: the server span carries each header as an attribute, and reaches
    ``before_send_span``.

    Each layer is pinned on its own, as in the class above: the production configuration; on 3.x
    the SDK's configuration with the hooks off; the hooks with the SDK's own filtering reduced to
    its defaults; and a control with both off, which proves the harness sees the leak.
    """

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_no_sensitive_value_reaches_the_wire(self, wire, send_pii):
        """In an error event, on either major; the trace items have their own tests below (2.x transactions, 3.x spans)."""
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_request("/boom")

        request = _the_request(transport, "event")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        # The parsed ``Cookie`` header reaches an event only under ``send_pii=True``, on either major.
        assert request.get("cookies") == (_FILTERED_COOKIES if send_pii else None)
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_2
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_no_sensitive_value_reaches_a_transaction(self, wire, send_pii):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_request("/ok")

        request = _the_request(transport, "transaction")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        # The integrations parse the ``Cookie`` header into ``request.cookies`` only under ``send_pii=True``.
        assert request.get("cookies") == (_FILTERED_COOKIES if send_pii else None)
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    @pytest.mark.parametrize("route", ["/ok", "/boom"])
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_no_sensitive_value_reaches_a_span(self, wire, route, send_pii):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_request(route)

        attributes = _server_span(transport)
        assert {key: attributes[key] for key in _SPAN_HEADER_KEYS} == dict.fromkeys(_SPAN_HEADER_KEYS, ["[Filtered]"])
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_2
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

    @_ON_SDK_3
    def test_a_parent_sampled_span_is_scrubbed_at_a_zero_sample_rate(self, wire):
        """3.x honours a caller's sampling decision too, so at 0.0 this server span is sent, and must be scrubbed.

        Driven straight into the ASGI app (``_drive_one_asgi_request`` says why), with the rate given
        to ``configure_sentry`` itself, as in the 2.x test above.
        """
        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True, traces_sample_rate=0.0)

        _drive_one_asgi_request("/ok", extra_headers=_PARENT_SAMPLED)

        attributes = _server_span(transport)
        assert {key: attributes[key] for key in _SPAN_HEADER_KEYS} == dict.fromkeys(_SPAN_HEADER_KEYS, ["[Filtered]"])
        assert _SECRET.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_an_error_event_is_scrubbed_at_a_zero_sample_rate(self, wire, send_pii):
        """The sample rate governs traces only: at 0.0 an error event is still sent, and scrubbed.

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

    @_ON_SDK_2
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

    @_ON_SDK_2
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

    @_ON_SDK_3
    @pytest.mark.parametrize("send_pii", [False, True])
    def test_the_sdk_configuration_alone_keeps_every_sensitive_value_out(self, wire, send_pii):
        """``data_collection`` with both hooks off: the extra header terms, and the cookie modes, filter at the source.

        Without ``send_pii`` no cookie is collected; with it, the allowlist with no terms keeps the
        names and replaces every value, ``canopy_ui`` too, which the SDK's denylist would not.
        """
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides["before_send"] = None
        overrides["before_send_span"] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_request("/boom", extra_headers=_COOKIE_NO_TERM)

        request = _the_request(transport, "event")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert request.get("cookies") == (_FILTERED_COOKIES_NO_TERM if send_pii else None)
        attributes = _server_span(transport)
        assert {key: attributes[key] for key in _SPAN_HEADER_KEYS} == dict.fromkeys(_SPAN_HEADER_KEYS, ["[Filtered]"])
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    def test_the_hooks_alone_keep_what_the_sdk_misses_out(self, wire):
        """The SDK reduced to its own denylists: it leaves ``sec-websocket-protocol`` and ``canopy_ui`` raw, and the hooks do not."""
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides.update(_sdk_plain_denylist())
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_request("/boom", extra_headers=_COOKIE_NO_TERM)

        request = _the_request(transport, "event")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert request["cookies"] == _FILTERED_COOKIES_NO_TERM
        attributes = _server_span(transport)
        assert {key: attributes[key] for key in _SPAN_HEADER_KEYS} == dict.fromkeys(_SPAN_HEADER_KEYS, ["[Filtered]"])
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    def test_control_the_harness_sees_what_the_sdk_misses_when_the_hooks_are_off(self, wire):
        """With the hooks off as well, the WebSocket key reaches the event and the span, and ``canopy_ui`` the event.

        If a future SDK starts filtering ``sec-websocket-protocol`` or ``canopy_ui`` itself, this
        fails: the instrument has changed, and the two tests above need a value the SDK leaves alone.
        """
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides.update(_sdk_plain_denylist())
        overrides["before_send"] = None
        overrides["before_send_span"] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_request("/boom", extra_headers=_COOKIE_NO_TERM)

        request = _the_request(transport, "event")
        assert _SECRET in request["headers"]["sec-websocket-protocol"]
        assert request["cookies"] == {"session": "[Filtered]", "canopy_ui": _SECRET}
        assert _SECRET in _server_span(transport)["http.request.header.sec-websocket-protocol"][0]
        assert _SECRET.encode() in _wire_bytes(transport)


#: The client's address, in the two headers a proxy puts it in: a documentation address (TEST-NET-3).
_ADDRESS = ".".join(("203", "0", "113", "77"))
_ADDRESS_HEADERS = {"X-Forwarded-For": _ADDRESS, "X-Real-IP": _ADDRESS}


class TestNoClientAddressWithoutSendPii:
    """The client's address is PII: without ``send_pii`` it reaches no item, on either major; with it, it does.

    2.x removes ``X-Forwarded-For`` and ``X-Real-IP`` unless ``send_default_pii`` is on, and attaches
    the address it reads from them only then. 3.x's denylist matches neither header, so
    ``_data_collection`` names both when ``send_pii`` is off, and ``user_info`` keeps the address
    attributes off.
    """

    @pytest.mark.parametrize("route", ["/ok", "/boom"])
    def test_no_address_without_send_pii(self, wire, route):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _drive_one_request(route, extra_headers=_ADDRESS_HEADERS)

        # A sessions envelope is always sent, so "any envelope" proves nothing: require the item that would carry the address.
        assert any(item.type in ("event", "transaction", "span") for envelope in transport.envelopes for item in envelope.items), "no event, transaction or span reached the transport"
        assert _ADDRESS.encode() not in _wire_bytes(transport)

    @pytest.mark.parametrize("route", ["/ok", "/boom"])
    def test_control_the_address_is_sent_with_send_pii(self, wire, route):
        """The operator's opt-in: the address reaches Sentry, as 2.x sent it, and the harness can see it."""
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_request(route, extra_headers=_ADDRESS_HEADERS)

        assert _ADDRESS.encode() in _wire_bytes(transport)
        assert _SECRET.encode() not in _wire_bytes(transport)


class TestExplicitUserAddress:
    """2.x drops ``user.ip_address`` without ``send_default_pii``; 3.0.0 attaches the scope's user to every event, so the hook does."""

    @pytest.mark.parametrize(("pii", "expected"), [(False, {"id": "u-1"}), (True, {"id": "u-1", "ip_address": _SECRET})])
    def test_the_hook_follows_send_pii(self, pii, expected):
        """On 3.x. On 2.x the SDK's own scrubber has decided already (the next test)."""
        event = {"user": {"id": "u-1", "ip_address": _SECRET}}
        with patch.object(sentry_module, "_sentry_sdk_major", return_value=3), patch.object(sentry_module, "_pii_on", return_value=pii):
            assert _strip_sensitive_headers(event, {})["user"] == expected

    @pytest.mark.parametrize("pii", [False, True])
    def test_on_2x_the_hook_leaves_the_user_to_the_sdk(self, pii):
        """2.35.0 replaces ``ip_address`` and keeps ``x-api-key``; 2.76.0 drops and replaces them. Either way the hook changes nothing."""
        event = {"user": {"id": "u-1", "ip_address": "[Filtered]", "x-api-key": _SECRET}, "extra": {"X-Api-Key": _SECRET}}
        before = repr(event)
        with patch.object(sentry_module, "_sentry_sdk_major", return_value=2), patch.object(sentry_module, "_pii_on", return_value=pii):
            assert repr(_strip_sensitive_headers(event, {})) == before

    def test_a_later_init_with_pii_off_is_obeyed(self, wire):
        """``configure_sentry(send_pii=True)``, then a consumer's own init with PII off and the hook: the active client decides.

        On 3.0.0 the module flag alone kept PII on, and the scope user's address reached the wire.
        """
        import sentry_sdk

        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)
        pii_off = {"data_collection": {"user_info": False, "stack_frame_variables": False}} if _SDK_MAJOR >= 3 else {"send_default_pii": False, "include_local_variables": False}
        sentry_sdk.init(dsn="http://public@127.0.0.1:9/1", before_send=_strip_sensitive_headers, **pii_off)
        with sentry_sdk.new_scope() as scope:
            scope.set_user({"id": "u-1", "ip_address": _ADDRESS})
            sentry_sdk.capture_message("after a re-init")
        sentry_sdk.flush()

        assert _the_event(transport)["user"]["id"] == "u-1"
        assert _ADDRESS.encode() not in _wire_bytes(transport)

    def test_a_later_init_that_says_nothing_about_pii_is_obeyed(self, wire):
        """The same with an init that leaves PII to the SDK's default, which is off on 2.x and ``user_info=True`` on 3.x.

        On 3.0.0 the flag AND that client's ``user_info`` both said yes, so the hooks let every value under
        2.x's PII names through, the scope user's address among them; 2.76.0 filters them for the same init.
        """
        import sentry_sdk

        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)
        no_locals = {"data_collection": {"stack_frame_variables": False}} if _SDK_MAJOR >= 3 else {"include_local_variables": False}
        sentry_sdk.init(dsn="http://public@127.0.0.1:9/1", before_send=_strip_sensitive_headers, **no_locals)
        with sentry_sdk.new_scope() as scope:
            scope.set_user({"id": "u-1", "ip_address": _ADDRESS})
            scope.set_extra("remote_addr", _ADDRESS)
            sentry_sdk.capture_message("after a re-init")
        sentry_sdk.flush()

        assert _the_event(transport)["extra"]["remote_addr"] == "[Filtered]"
        assert _ADDRESS.encode() not in _wire_bytes(transport)


class TestPiiOn:
    """``_pii_on``: the client the latest ``configure_sentry(send_pii=True)`` made, still active, with ``user_info`` on; anything else is "no"."""

    @staticmethod
    def _client(active, user_info):
        return type("_Client", (), {"is_active": lambda self: active, "options": {"data_collection": {"user_info": user_info}}})()

    @pytest.mark.parametrize(("flag", "active", "user_info", "expected"), [(False, True, True, False), (True, False, True, False), (True, True, False, False), (True, True, True, True)])
    def test_both_must_say_yes(self, monkeypatch, flag, active, user_info, expected):
        client = self._client(active, user_info)
        monkeypatch.setattr(sentry_module, "_send_pii", flag)
        monkeypatch.setattr(sentry_module, "_configured_client", client)
        with patch("sentry_sdk.get_client", return_value=client):
            assert sentry_module._pii_on() is expected

    def test_only_for_the_client_configure_sentry_made(self, monkeypatch):
        """Another active client with ``user_info`` on, 3.x's default, is not the configured one: no PII."""
        monkeypatch.setattr(sentry_module, "_send_pii", True)
        monkeypatch.setattr(sentry_module, "_configured_client", self._client(True, True))
        with patch("sentry_sdk.get_client", return_value=self._client(True, True)):
            assert sentry_module._pii_on() is False

    def test_configure_sentry_records_its_client(self, wire):
        """The control for the identity check: right after ``configure_sentry(send_pii=True)`` PII is on, on 3.x."""
        import sentry_sdk

        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)
        assert sentry_module._configured_client is sentry_sdk.get_client()
        if _SDK_MAJOR >= 3:
            assert sentry_module._pii_on() is True

    def test_an_error_reads_as_no(self, monkeypatch):
        monkeypatch.setattr(sentry_module, "_send_pii", True)
        monkeypatch.setattr(sentry_module, "_configured_client", self._client(True, True))
        with patch("sentry_sdk.get_client", side_effect=RuntimeError("no client")):
            assert sentry_module._pii_on() is False

    def test_the_module_default_is_no(self):
        """A consumer that installs the hook without ``configure_sentry`` gets 2.x's default, no PII."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_fresh_juniper_observability_sentry", sentry_module.__file__)
        fresh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fresh)
        assert fresh._send_pii is False

    @pytest.mark.parametrize(("major", "expected"), [(2, True), (3, False), (4, False), (0, False)])
    def test_only_2x_scrubs_by_name_itself(self, major, expected):
        with patch.object(sentry_module, "_sentry_sdk_major", return_value=major):
            assert sentry_module._sdk_scrubs_by_name() is expected

    def test_an_unreadable_major_is_not_2x(self):
        with patch.object(sentry_module, "_sentry_sdk_major", side_effect=AttributeError("VERSION")):
            assert sentry_module._sdk_scrubs_by_name() is False

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_on_the_wire(self, wire, send_pii):
        """Without ``send_pii`` the address reaches no event; with it, it does (the control)."""
        import sentry_sdk

        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)
        with sentry_sdk.new_scope() as scope:
            scope.set_user({"id": "u-1", "ip_address": _ADDRESS})
            sentry_sdk.capture_message("with an explicit user")
        sentry_sdk.flush()

        assert _the_event(transport)["user"]["id"] == "u-1"
        assert (_ADDRESS.encode() in _wire_bytes(transport)) is send_pii


class TestUnsupportedSdkMajor:
    @pytest.mark.parametrize("major", [0, 1, 4])
    def test_an_unmeasured_major_initialises_nothing(self, major, caplog):
        """Consumers' own pins (``sentry-sdk>=2.0.0``) admit 4.x: an unmeasured major gets no options at all."""
        with patch.object(sentry_module, "_sentry_sdk_major", return_value=major), patch("sentry_sdk.init") as mock_init, caplog.at_level(logging.WARNING):
            configure_sentry(_DSN, "juniper-test", "1.0.0")
        mock_init.assert_not_called()
        assert "not supported" in caplog.text


#: Names 2.x's ``EventScrubber`` denylists, in the spellings a service uses.
_DENYLISTED = {"api_key": _SECRET, "Password": _SECRET, "X-Api-Key": _SECRET, "token": _SECRET}
_DENYLISTED_FILTERED = dict.fromkeys(_DENYLISTED, "[Filtered]")


class TestRedactsWhat2xEventScrubberRedacted:
    """sentry-sdk 3.0.0 deleted 2.x's ``EventScrubber``; on 3.x the hooks redact the same names in the same containers.

    Run as 3.x without PII; on 2.x the SDK's own scrubber does it, and ``TestExplicitUserAddress`` pins
    that the hook then leaves those containers alone.
    """

    @pytest.fixture(autouse=True)
    def _on_3x_without_pii(self):
        with patch.object(sentry_module, "_sentry_sdk_major", return_value=3), patch.object(sentry_module, "_pii_on", return_value=False):
            yield

    def test_the_denylists_are_2xs(self):
        """2.76.0's ``DEFAULT_DENYLIST`` and ``DEFAULT_PII_DENYLIST``, normalised and spelled out: a name dropped from the module fails here."""
        assert sentry_module._SENTRY_DENYLIST == frozenset(
            {
                "password",
                "passwd",
                "secret",
                "api_key",
                "apikey",
                "auth",
                "credentials",
                "mysql_pwd",
                "privatekey",
                "private_key",
                "token",
                "session",
                "csrftoken",
                "sessionid",
                "x_csrftoken",
                "set_cookie",
                "cookie",
                "authorization",
                "proxy_authorization",
                "x_api_key",
                "aiohttp_session",
                "connect.sid",
                "csrf_token",
                "csrf",
                "_csrf",
                "_csrf_token",
                "phpsessid",
                "_session",
                "symfony",
                "user_session",
                "_xsrf",
                "xsrf_token",
            }
        )
        assert sentry_module._SENTRY_PII_DENYLIST == frozenset({"x_forwarded_for", "x_real_ip", "ip_address", "remote_addr"})

    def test_every_breadcrumb_and_an_event_without_a_request(self):
        """The denylisted crumb is neither the first nor the last, and a message event has no ``request``."""
        event = {
            "extra": {"secret": _SECRET, "request_id": "r-1"},
            "user": {"id": "u-1", "credentials": _SECRET},
            "breadcrumbs": {"values": [{"data": {"status": 200}}, {"data": {"session": _SECRET}}, {"data": {"ok": 1}}]},
        }
        result = _strip_sensitive_headers(event, {})
        assert result["extra"] == {"secret": "[Filtered]", "request_id": "r-1"}
        assert result["user"] == {"id": "u-1", "credentials": "[Filtered]"}
        assert [crumb["data"] for crumb in result["breadcrumbs"]["values"]] == [{"status": 200}, {"session": "[Filtered]"}, {"ok": 1}]

    @pytest.mark.parametrize("pii", [False, True])
    def test_2xs_pii_names_follow_send_pii(self, pii):
        """2.x replaces values under its PII names (any case, ``-`` or ``_``) unless ``send_default_pii`` is on; its security names always."""
        names = {"ip_address": _SECRET, "Remote-Addr": _SECRET, "X_Forwarded_For": _SECRET, "x-real-ip": _SECRET}
        event = {
            "extra": dict(names),
            "user": {"id": "u-1", "remote_addr": _SECRET},
            "breadcrumbs": {"values": [{"data": dict(names)}]},
            "request": {"headers": {"Remote-Addr": _SECRET, "Symfony": _SECRET, "Accept": "*/*"}, "data": dict(names)},
        }
        with patch.object(sentry_module, "_pii_on", return_value=pii):
            result = _strip_sensitive_headers(event, {})
        expected = names if pii else dict.fromkeys(names, "[Filtered]")
        assert result["extra"] == expected
        assert result["request"]["data"] == expected
        assert result["breadcrumbs"]["values"][0]["data"] == expected
        assert result["user"] == {"id": "u-1", "remote_addr": _SECRET if pii else "[Filtered]"}
        assert result["request"]["headers"] == {"Remote-Addr": _SECRET if pii else "[Filtered]", "Symfony": "[Filtered]", "Accept": "*/*"}

    def test_extra_user_breadcrumbs_and_request_data(self):
        event = {
            "extra": {**_DENYLISTED, "request_id": "r-1"},
            "user": {"id": "u-1", "api_key": _SECRET},
            "breadcrumbs": {"values": [{"category": "auth", "data": {**_DENYLISTED, "status": 200}}]},
            "request": {"data": {**_DENYLISTED, "username": "u"}},
        }
        result = _strip_sensitive_headers(event, {})
        assert result["extra"] == {**_DENYLISTED_FILTERED, "request_id": "r-1"}
        assert result["user"] == {"id": "u-1", "api_key": "[Filtered]"}
        assert result["breadcrumbs"]["values"][0]["data"] == {**_DENYLISTED_FILTERED, "status": 200}
        assert result["request"]["data"] == {**_DENYLISTED_FILTERED, "username": "u"}

    def test_a_list_shaped_request_body(self):
        event = {"request": {"data": [{"password": _SECRET}, "raw", {"username": "u"}]}}
        assert _strip_sensitive_headers(event, {})["request"]["data"] == [{"password": "[Filtered]"}, "raw", {"username": "u"}]

    @pytest.mark.parametrize("event", [{"extra": "x"}, {"user": None}, {"breadcrumbs": {"values": "x"}}, {"breadcrumbs": {"values": [None, {"data": None}]}}, {"request": {"data": "raw body"}}])
    def test_tolerates_unexpected_shapes(self, event):
        before = repr(event)
        assert _strip_sensitive_headers(event, {}) is event
        assert repr(event) == before

    def test_span_attribute_names(self):
        span = _span(api_key=_SECRET, auth=_SECRET, **{"url.path": "/ok", "http.request.method": "GET"})
        result = _strip_sensitive_span_attributes(span, {})
        assert result["attributes"] == {"api_key": "[Filtered]", "auth": "[Filtered]", "url.path": "/ok", "http.request.method": "GET"}

    def test_span_attribute_names_in_other_spellings_and_header_names(self):
        """Case and ``-`` as 2.x read them; a header attribute under a denylisted or PII name stays a one-item list."""
        attributes = {"API_KEY": _SECRET, "X-Api-Key": _SECRET, "remote_addr": _SECRET, "http.request.header.symfony": [_SECRET], "http.request.header.remote-addr": [_SECRET], "http.request.header.accept": ["*/*"]}
        result = _strip_sensitive_span_attributes(_span(**attributes), {})
        assert result["attributes"] == {"API_KEY": "[Filtered]", "X-Api-Key": "[Filtered]", "remote_addr": "[Filtered]", "http.request.header.symfony": ["[Filtered]"], "http.request.header.remote-addr": ["[Filtered]"], "http.request.header.accept": ["*/*"]}


def _the_event(transport):
    """The one error event the transport received, or fail."""
    events = [json.loads(item.get_bytes()) for envelope in transport.envelopes for item in envelope.items if item.type == "event"]
    assert len(events) == 1, f"expected one event, got {len(events)} ({len(transport.envelopes)} envelopes)"
    return events[0]


def _drive_denylisted_values():
    """A request that puts the secret under denylisted names: an extra, a breadcrumb's data, a span's data, the JSON body."""
    import sentry_sdk
    from fastapi import Body, FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.post("/boom")
    def boom(payload: dict = Body(...)):  # noqa: B008
        sentry_sdk.set_extra("api_key", _SECRET)
        sentry_sdk.add_breadcrumb(category="auth", message="token refreshed", data={"token": _SECRET})
        if _SDK_MAJOR >= 3:
            with sentry_sdk.start_span(name="call upstream") as span:
                span.set_attribute("api_key", _SECRET)
        else:
            with sentry_sdk.start_span(op="http.client", name="call upstream") as span:
                span.set_data("api_key", _SECRET)
        raise RuntimeError("boom")

    TestClient(app, raise_server_exceptions=False).post("/boom", json={"username": "u", "password": _SECRET})
    sentry_sdk.flush()


class TestNoDenylistedValueReachesTheWire:
    """End to end, on either major: no value under a name 2.x's ``EventScrubber`` denylists reaches Sentry.

    2.x redacts it with that scrubber, and the hooks again; on 3.x, which deleted the scrubber, the
    hooks alone do (and ``http_bodies`` is empty, so no body is collected). The control turns the
    hooks off on 3.x and shows the values, or the absence above would prove nothing.
    """

    def test_no_denylisted_value_reaches_the_wire(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _drive_denylisted_values()

        assert _the_event(transport)["extra"]["api_key"] == "[Filtered]"
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    def test_control_the_harness_sees_the_values_when_the_hooks_are_off(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides["before_send"] = None
        overrides["before_send_span"] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _drive_denylisted_values()

        event = _the_event(transport)
        assert event["extra"]["api_key"] == _SECRET
        assert [crumb["data"] for crumb in event["breadcrumbs"]["values"] if crumb.get("category") == "auth"] == [{"token": _SECRET}]
        assert _SECRET.encode() in _wire_bytes(transport)


def _drive_address_under_pii_names():
    """A request that puts the address under 2.x's PII names: an extra, a breadcrumb's data, a span's data and, on 3.x, a request header.

    2.35.0 reads ``Remote-Addr`` as ``remote-addr``, not ``remote_addr``, so it sends that header raw; the header
    is checked on 3.x only, where the hooks match it as 2.76.0 does.
    """
    import sentry_sdk
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/boom")
    def boom():
        sentry_sdk.set_extra("remote_addr", _ADDRESS)
        sentry_sdk.add_breadcrumb(category="net", message="peer", data={"ip_address": _ADDRESS})
        if _SDK_MAJOR >= 3:
            with sentry_sdk.start_span(name="call upstream") as span:
                span.set_attribute("x_real_ip", _ADDRESS)
        else:
            with sentry_sdk.start_span(op="http.client", name="call upstream") as span:
                span.set_data("x_real_ip", _ADDRESS)
        raise RuntimeError("boom")

    TestClient(app, raise_server_exceptions=False).get("/boom", headers={"Remote-Addr": _ADDRESS} if _SDK_MAJOR >= 3 else {})
    sentry_sdk.flush()


class TestNoAddressUnderA2xPiiName:
    """2.x's PII denylist: without ``send_pii`` no value under ``ip_address``, ``remote_addr``, ``x_forwarded_for`` or ``x_real_ip`` reaches Sentry, on either major."""

    def test_without_send_pii(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _drive_address_under_pii_names()

        assert _the_event(transport)["extra"]["remote_addr"] == "[Filtered]"
        assert _ADDRESS.encode() not in _wire_bytes(transport)

    def test_control_with_send_pii(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_address_under_pii_names()

        assert _the_event(transport)["extra"]["remote_addr"] == _ADDRESS

    @_ON_SDK_3
    def test_control_the_harness_sees_the_address_when_the_hooks_are_off(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides["before_send"] = None
        overrides["before_send_span"] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")

        _drive_address_under_pii_names()

        event = _the_event(transport)
        assert event["extra"]["remote_addr"] == _ADDRESS
        assert event["request"]["headers"]["remote-addr"] == _ADDRESS
        assert _ADDRESS in _server_span(transport)["http.request.header.remote-addr"][0]


def _drive_one_websocket():
    """One WebSocket session straight into the ASGI app: connect, one text frame, then a failing handler.

    juniper-canopy's server reads its WebSocket key from ``Sec-WebSocket-Protocol`` (``bearer, <key>``).
    """
    import sentry_sdk
    from fastapi import FastAPI, WebSocket

    app = FastAPI()

    @app.websocket("/ws")
    async def ws(websocket: WebSocket):
        await websocket.accept(subprotocol="bearer")
        await websocket.receive_text()
        raise RuntimeError("ws boom")

    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": "/ws",
        "raw_path": b"/ws",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")] + [(name.lower().encode(), value.encode()) for name, value in _SENSITIVE_REQUEST_HEADERS.items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "subprotocols": ["bearer", _SECRET],
    }
    inbox = [{"type": "websocket.connect"}, {"type": "websocket.receive", "text": "hello"}, {"type": "websocket.disconnect", "code": 1000}]

    async def receive():
        return inbox.pop(0)

    async def send(message):
        return None

    with pytest.raises(RuntimeError, match="ws boom"):
        asyncio.run(app(scope, receive, send))
    sentry_sdk.flush()


def _websocket_span(transport):
    """The attributes of the one ``websocket.server`` span the transport received, unwrapped, or fail."""
    spans = [span for envelope in transport.envelopes for item in envelope.items if item.type == "span" for span in json.loads(item.get_bytes())["items"]]
    servers = [span for span in spans if span.get("attributes", {}).get("sentry.op", {}).get("value") == "websocket.server"]
    assert len(servers) == 1, f"expected one websocket.server span, got {len(servers)} of {len(spans)} span(s)"
    return {key: value["value"] for key, value in servers[0]["attributes"].items()}


class TestNoSensitiveValueReachesTheWireOverAWebSocket:
    """The WebSocket scope, which no HTTP request exercises: the key in ``Sec-WebSocket-Protocol`` never reaches Sentry."""

    @pytest.mark.parametrize("send_pii", [False, True])
    def test_no_sensitive_value_reaches_the_wire(self, wire, send_pii):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=send_pii)

        _drive_one_websocket()

        request = _the_request(transport, "event")
        assert {name: request["headers"][name] for name in _SENSITIVE_HEADER_NAMES} == dict.fromkeys(_SENSITIVE_HEADER_NAMES, "[Filtered]")
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    def test_the_hooks_alone_keep_the_websocket_key_out(self, wire):
        """The SDK reduced to its own denylists, which match no term in ``sec-websocket-protocol``."""
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides.update(_sdk_plain_denylist())
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_websocket()

        assert _websocket_span(transport)["http.request.header.sec-websocket-protocol"] == ["[Filtered]"]
        assert _the_request(transport, "event")["headers"]["sec-websocket-protocol"] == "[Filtered]"
        assert _SECRET.encode() not in _wire_bytes(transport)

    @_ON_SDK_3
    def test_control_the_harness_sees_the_websocket_key_when_the_hooks_are_off(self, wire):
        transport, overrides = wire
        overrides["traces_sample_rate"] = 1.0
        overrides.update(_sdk_plain_denylist())
        overrides["before_send"] = None
        overrides["before_send_span"] = None
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0", send_pii=True)

        _drive_one_websocket()

        assert _SECRET in _websocket_span(transport)["http.request.header.sec-websocket-protocol"][0]
        assert _SECRET in _the_request(transport, "event")["headers"]["sec-websocket-protocol"]


class TestLoggingBehavesAs2xDid:
    """2.x's default ``LoggingIntegration`` with ``enable_logs=True``: INFO and above become breadcrumbs and Sentry Logs, ERROR and above error events.

    3.x installs no logging integration by default, so ``configure_sentry`` passes one. Each of its
    three levels is pinned here, on whichever major is installed.
    """

    def test_info_and_warning_are_breadcrumbs_and_logs_and_only_error_is_an_event(self, wire):
        import sentry_sdk

        transport, _overrides = wire
        configure_sentry("http://public@127.0.0.1:9/1", "juniper-test", "1.0.0")
        log = logging.getLogger("juniper_observability.tests.levels")
        previous = log.level
        log.setLevel(logging.INFO)
        try:
            log.info("an info record")
            log.warning("a warning record")
            log.error("an error record")
        finally:
            log.setLevel(previous)
        sentry_sdk.flush()

        event = _the_event(transport)
        assert (event.get("logentry") or {}).get("message", event.get("message")) == "an error record"
        crumbs = [crumb.get("message") for crumb in event["breadcrumbs"]["values"]]
        assert crumbs[-2:] == ["an info record", "a warning record"]
        logs = [entry["body"] for envelope in transport.envelopes for item in envelope.items if item.type == "log" for entry in json.loads(item.get_bytes())["items"]]
        assert logs == ["an info record", "a warning record", "an error record"]
