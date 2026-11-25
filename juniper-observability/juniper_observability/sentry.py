"""Sentry initialization with reconciled signature and SEC-10 hook.

This module exposes the **superset** signature originally introduced
in juniper-data for SEC-10 (security review of Sentry forwarding) and
makes it the cross-service standard:

- ``send_pii`` is keyword-only, defaulting to ``False``.
- Frame-local variables are never captured (``include_local_variables=False``).
  The SDK default is ``True``, which snapshots every frame's locals into
  each error event. An exception raised inside an API-key comparison
  therefore shipped the comparison loop's local holding the REAL
  configured key -- found by the validation of juniper-canopy#683
  (2026-09-24), where an anonymous ``X-API-Key: \\xa0`` made
  ``hmac.compare_digest`` raise ``TypeError``. The SDK's own
  ``EventScrubber`` did not help: it redacts locals by NAME. ``api_key``,
  the PRESENTED key, is on its default denylist; ``candidate``, the loop
  variable holding the CONFIGURED key, is not. No name list can be
  complete, so the fix is to capture no locals at all.
- A ``before_send`` hook always scrubs the request headers named in
  ``_SENTRY_SENSITIVE_HEADERS`` (``X-API-Key``, ``Authorization`` and
  ``Cookie``; from 0.4.2 also ``Proxy-Authorization``,
  ``Sec-WebSocket-Protocol``, ``X-CSRF-Token`` and ``X-XSRF-Token``) from
  outbound events regardless of ``send_default_pii``, and deletes any
  frame ``vars`` that still reach
  it — defense in depth so that future Sentry SDK changes (replay,
  custom integrations) cannot leak credentials. That second half is not
  hypothetical: the opt-in ``PureEvalIntegration`` writes frame ``vars``
  from its own event processor without consulting
  ``include_local_variables`` (``sentry_sdk/integrations/pure_eval.py``,
  sentry-sdk 2.58.0), and event processors run before ``before_send``.
- The same hook is installed as ``before_send_transaction``, because the
  SDK never hands a transaction to ``before_send``. Under
  ``send_default_pii=True`` the SDK's own header filter is off, and its
  ``EventScrubber`` denylist names ``x_api_key`` but not ``x-api-key``, so
  until 0.4.2 every sampled transaction carried the raw ``X-API-Key``
  (round-42 finding F2, 2026-09-24).
- The hook also redacts the request's parsed ``cookies``, which the
  Starlette and FastAPI integrations add under ``send_default_pii=True``
  beside the ``Cookie`` header itself. The SDK's denylist redacts a cookie
  by NAME (``session``, ``csrftoken`` ...), so any other name reached the
  wire, in error events and transactions alike, until 0.4.2. A dict keeps
  its names and loses every value; a non-empty ``cookies`` of any other
  shape is dropped.
- Still OUTSIDE the hook (left for R-OBS-SC-3, to be designed and validated
  on its own): query strings,
  Sentry Logs (``enable_logs=True`` has no ``before_send_log``), request
  bodies, breadcrumbs, exception values and list-shaped ``headers``. On 3.x
  the hooks do only what 2.x's deleted ``EventScrubber`` did to bodies and
  breadcrumb data: replace values under the names it denylisted.

Both sentry-sdk majors are supported, and the installed one's major decides
which options are passed (:func:`_sentry_sdk_major`):

- On 2.x the options are the ones 0.4.2 passed: ``send_default_pii``,
  ``include_local_variables=False``, ``enable_logs=True``, and the hook as
  ``before_send`` and ``before_send_transaction``.
- sentry-sdk 3.0.0 removed every one of those but ``before_send``, and
  ``sentry_sdk.init`` raises ``TypeError`` for an unknown option. On 3.x the
  same choices go through ``data_collection`` (:func:`_data_collection`).
- 3.x streams spans in place of transactions. The server span carries each
  request header as an ``http.request.header.<name>`` attribute, so
  :func:`_strip_sensitive_span_attributes` is installed as
  ``before_send_span``. The SDK's own denylist matches no term in
  ``sec-websocket-protocol``: with the SDK's defaults juniper-canopy's
  WebSocket key reached every span raw (measured on 3.0.0).
- 3.x no longer installs the logging integration by default. It is passed
  with ``event_level=logging.ERROR``, so an ERROR record is still an error
  event and INFO and above still become Sentry Logs and breadcrumbs, as on 2.x
  with ``enable_logs=True``.

``configure_sentry`` is a no-op when ``dsn`` is ``None`` or the empty
string, so consumers can call it unconditionally during startup.
"""

import logging as _logging

DEFAULT_SENTRY_TRACES_SAMPLE_RATE = 0.1

# SEC-10: header names that may carry API keys, credentials or session identifiers, compared
# lower-case. 0.4.2 added the last four. ``sec-websocket-protocol`` is where juniper-canopy's
# server reads a WebSocket key (``bearer, <key>``) when its opt-in ``ws_auth_enabled`` is on;
# it and the two CSRF tokens are on neither of the SDK's own lists, so they reached Sentry even
# under the default ``send_pii=False``. sentry-sdk 2.35.0 filters ``proxy-authorization`` in
# neither mode (2.73.0 does, in both).
_SENTRY_SENSITIVE_HEADERS = frozenset(
    {
        "x-api-key",
        "authorization",
        "cookie",
        "proxy-authorization",
        "sec-websocket-protocol",
        "x-csrf-token",
        "x-xsrf-token",
    }
)

# Headers that carry the client's address, compared lower-case. sentry-sdk 2.x removes both from every
# event unless ``send_default_pii`` is on (``SENSITIVE_ENV_KEYS`` in ``integrations/_wsgi_common.py``,
# 2.35.0 and 2.76.0). 3.x's denylist matches neither, so ``_data_collection`` adds them to it when
# ``send_pii`` is off.
_SENTRY_ADDRESS_HEADERS = frozenset({"x-forwarded-for", "x-real-ip"})

# sentry-sdk 3.x records each request header on the server span under this prefix, as a one-item list.
_SPAN_REQUEST_HEADER_PREFIX = "http.request.header."

# sentry-sdk 2.x's ``EventScrubber`` security denylist (``DEFAULT_DENYLIST`` in ``scrubber.py``, 2.76.0),
# normalised as 2.76.0 normalises it: lower-case, ``-`` to ``_``. By default 2.x replaces the value of
# every such top-level KEY in request headers and cookies, ``request.data``, ``extra``, ``user``, each
# breadcrumb's ``data``, frame ``vars`` and each span's ``data``. sentry-sdk 3.0.0 deleted the scrubber and
# put nothing in its place for most of those containers, so on 3.x the hooks apply the list themselves
# (:func:`_redact_by_name`). On 2.x they leave it to the SDK: 2.35.0 matches names without reading ``-``
# as ``_``, so a second pass would change what 2.x sends.
_SENTRY_DENYLIST = frozenset(
    name.lower().replace("-", "_")
    for name in (
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
        "proxy-authorization",
        "x_api_key",
        "aiohttp_session",
        "connect.sid",
        "csrf_token",
        "csrf",
        "_csrf",
        "_csrf_token",
        "PHPSESSID",
        "_session",
        "symfony",
        "user_session",
        "_xsrf",
        "XSRF-TOKEN",
    )
)

# sentry-sdk 2.x's ``EventScrubber`` PII denylist (``DEFAULT_PII_DENYLIST`` in ``scrubber.py``, 2.35.0 and
# 2.76.0), normalised the same way. Without ``send_default_pii`` 2.x adds it to the list above, so a value
# under ``ip_address``, ``remote_addr``, ``x_forwarded_for`` or ``x_real_ip`` (in any case, ``-`` or ``_``)
# is replaced in every container the scrubber reads, request headers included. On 3.x the hooks add it
# unless PII is on.
_SENTRY_PII_DENYLIST = frozenset({"x_forwarded_for", "x_real_ip", "ip_address", "remote_addr"})

# The ``send_pii`` of the latest ``configure_sentry`` call that initialised a client, and that client.
# Without ``send_default_pii`` 2.x's ``EventScrubber`` drops ``user.ip_address`` from every event; 3.0.0
# applies the scope's user to every event whatever ``user_info`` says (``Scope._apply_user_to_event``), so
# the event hook drops it. False until configured, so a consumer that installs the hook on its own gets
# 2.x's default. The hooks treat PII as on only for the client ``configure_sentry`` made, while this AND
# its ``user_info`` say so (:func:`_pii_on`): a later ``sentry_sdk.init`` must not inherit an earlier
# ``send_pii=True``, whether it turns PII off or leaves ``user_info`` at 3.x's default, True.
_send_pii = False
_configured_client = None

# Event interfaces whose ``values`` entries each carry their own ``stacktrace``
# (an event may also carry one top-level ``stacktrace``, e.g. a message
# captured with ``attach_stacktrace``).
_SENTRY_STACKTRACE_INTERFACES = ("exception", "threads")


def _strip_frame_local_variables(event):
    """Delete ``vars`` from every stack frame of a Sentry event, in place.

    Covers every place the Sentry protocol puts frames: each
    ``exception.values[*].stacktrace`` (one per exception in a chain), each
    ``threads.values[*].stacktrace``, and the top-level ``stacktrace``.
    Anything that is not the expected dict/list shape is skipped rather than
    raised on -- a ``before_send`` hook that raises drops the event, and an
    unreadable event is no reason to lose the report.
    """
    stacktraces = [event.get("stacktrace")]
    for interface in _SENTRY_STACKTRACE_INTERFACES:
        container = event.get(interface)
        values = container.get("values") if isinstance(container, dict) else None
        if isinstance(values, list):
            stacktraces.extend(value.get("stacktrace") for value in values if isinstance(value, dict))
    for stacktrace in stacktraces:
        frames = stacktrace.get("frames") if isinstance(stacktrace, dict) else None
        if isinstance(frames, list):
            for frame in frames:
                if isinstance(frame, dict):
                    frame.pop("vars", None)


def _redact_denylisted_keys(mapping, names=_SENTRY_DENYLIST):
    """Replace, in place, the value of every top-level key of ``mapping`` that ``names`` holds.

    The match is 2.76.0's: the whole key, lower-cased, ``-`` read as ``_``. Anything that is not a dict
    is left alone, as 2.x's ``EventScrubber.scrub_dict`` leaves it.
    """
    if isinstance(mapping, dict):
        for key in list(mapping):
            if isinstance(key, str) and key.lower().replace("-", "_") in names:
                mapping[key] = "[Filtered]"


def _sdk_scrubs_by_name() -> bool:
    """True on sentry-sdk 2.x, whose own ``EventScrubber`` has applied both denylists before the hooks run.

    The hooks then leave every container that scrubber reads as 2.x left it. Redacting again is not a
    no-op on every 2.x: 2.35.0 matches names without reading ``-`` as ``_``, does not read list-shaped
    bodies, and replaces ``user.ip_address`` rather than dropping it. Any error reads as "not 2.x": a
    hook must not raise, and redacting is the safe side.
    """
    try:
        return _sentry_sdk_major() == 2
    except Exception:  # noqa: BLE001 — a Sentry hook must never raise
        return False


def _pii_on() -> bool:
    """Whether the hooks may let PII through: the active client is the one ``configure_sentry(send_pii=True)`` made, and its ``user_info`` is on.

    The module flag alone goes stale: after ``configure_sentry(send_pii=True)``, a consumer's own
    ``sentry_sdk.init`` kept it, and 3.0.0 sent the scope user's address, whether that init turned
    ``user_info`` off or left it at 3.x's default (True), where 2.x's ``send_default_pii`` defaults to
    False. Any other client, no active client, or any error, reads as "no".
    """
    if not _send_pii or _configured_client is None:
        return False
    try:
        import sentry_sdk

        client = sentry_sdk.get_client()
        if client is not _configured_client:
            return False
        data_collection = client.options.get("data_collection") if client.is_active() else None
        return isinstance(data_collection, dict) and bool(data_collection.get("user_info"))
    except Exception:  # noqa: BLE001 — a Sentry hook must never raise
        return False


def _denylist():
    """The names the hooks redact on 3.x: 2.x's security denylist, and without PII its PII denylist too."""
    return _SENTRY_DENYLIST if _pii_on() else _SENTRY_DENYLIST | _SENTRY_PII_DENYLIST


def _redact_by_name(event):
    """What 2.x's ``EventScrubber`` did to an event by default and 3.0.0 no longer does, in the same containers.

    Request headers and ``request.data`` (a dict, or a list of them), ``extra``, ``user`` and each
    breadcrumb's ``data``: every value under a name in :func:`_denylist`. Without PII,
    ``user.ip_address`` is dropped, as 2.76.0 drops it.
    """
    names = _denylist()
    request_data = event.get("request")
    if isinstance(request_data, dict):
        _redact_denylisted_keys(request_data.get("headers"), names)
        data = request_data.get("data")
        for mapping in data if isinstance(data, list) else [data]:
            _redact_denylisted_keys(mapping, names)
    _redact_denylisted_keys(event.get("extra"), names)
    user = event.get("user")
    if isinstance(user, dict) and not _pii_on():
        user.pop("ip_address", None)
    _redact_denylisted_keys(user, names)
    breadcrumbs = event.get("breadcrumbs")
    crumbs = breadcrumbs.get("values") if isinstance(breadcrumbs, dict) else None
    if isinstance(crumbs, list):
        for crumb in crumbs:
            if isinstance(crumb, dict):
                _redact_denylisted_keys(crumb.get("data"), names)


def _strip_sensitive_headers(event, hint):  # noqa: ARG001 — Sentry hook signature
    """Redact sensitive request headers and cookies, and drop frame-local variables.

    Sentry calls this via ``before_send`` for every error event and via
    ``before_send_transaction`` for every transaction; a transaction never
    reaches ``before_send``. The header filter only rewrites keys in
    :data:`_SENTRY_SENSITIVE_HEADERS` so non-sensitive diagnostic headers
    (user-agent, trace IDs, etc.) still reach Sentry unchanged. Every value
    of a non-empty ``request.cookies`` dict is replaced and its names are
    kept: it is the ``Cookie`` header parsed into names and values, and no
    list of cookie names can say which of them carries a session. A
    non-empty ``cookies`` of any other shape (the protocol also allows a raw
    header string or a list of pairs) is dropped rather than rewritten: the
    SDK's integrations produce the dict, a string would have to be parsed,
    and the protocol reads a string as a raw ``Cookie`` header, which a bare
    ``[Filtered]`` is not.

    On sentry-sdk 3.x (any SDK but 2.x) it also does what 2.x's ``EventScrubber`` did by default and
    3.0.0 deleted (:func:`_redact_by_name`): the value of every key 2.x denylists, in request headers,
    ``request.data``, ``extra``, ``user`` and each breadcrumb's ``data``. On 2.x the SDK has done that
    already, and the hook leaves those containers exactly as the SDK left them.

    It also deletes every frame's ``vars`` (:func:`_strip_frame_local_variables`).
    ``configure_sentry`` already passes ``include_local_variables=False``, so
    the SDK's own capture paths attach none; this is the backstop for
    anything that adds them regardless. The name is kept although the hook
    now does more than headers, because juniper-data and juniper-cascor import
    it by this name (cascor's ``main.py`` passes it to its own
    ``sentry_sdk.init``), and a rename would break those imports.
    """
    if not isinstance(event, dict):
        return event
    request_data = event.get("request", {})
    headers = request_data.get("headers", {}) if isinstance(request_data, dict) else {}
    if isinstance(headers, dict):
        for key in list(headers.keys()):
            if key.lower() in _SENTRY_SENSITIVE_HEADERS:
                headers[key] = "[Filtered]"
    if isinstance(request_data, dict):
        cookies = request_data.get("cookies")
        if isinstance(cookies, dict):
            if cookies:
                request_data["cookies"] = dict.fromkeys(cookies, "[Filtered]")
        elif cookies:
            del request_data["cookies"]
    # 2.x's EventScrubber did this by default; 3.0.0 deleted it. On 2.x, the SDK's own pass stands.
    if not _sdk_scrubs_by_name():
        _redact_by_name(event)
    _strip_frame_local_variables(event)
    return event


def _strip_sensitive_span_attributes(span, hint):  # noqa: ARG001 — Sentry hook signature
    """Redact the sensitive request headers a sentry-sdk 3.x span carries as attributes.

    3.x streams spans, and hands each one, serialised, to ``before_send_span``: there is no
    transaction any more, so ``before_send_transaction`` no longer exists. The server span records
    each request header as ``http.request.header.<name>``, after the SDK's own header filter, which
    :func:`_data_collection` extends with every name in :data:`_SENTRY_SENSITIVE_HEADERS`. This is
    the backstop, as :func:`_strip_sensitive_headers` is for events: each such attribute whose
    header is in that set, or whose normalised name 2.x denylisted (:func:`_denylist`), becomes
    ``["[Filtered]"]``. Every other attribute under a name 2.x denylisted becomes ``"[Filtered]"``,
    as 2.x's ``EventScrubber`` redacted it in a span's ``data``; the rest are left alone.

    It never raises, and it returns the span it was given. On 3.0.0 a ``before_send_span`` that
    raises, or that returns anything without a ``name``, makes the SDK send the ORIGINAL span
    (``Client._capture_telemetry``), so a scrubber that failed would fail open.
    """
    attributes = span.get("attributes") if isinstance(span, dict) else None
    if isinstance(attributes, dict):
        names = _denylist()
        for key in list(attributes):
            if not isinstance(key, str):
                continue
            if key.lower().startswith(_SPAN_REQUEST_HEADER_PREFIX):
                header = key[len(_SPAN_REQUEST_HEADER_PREFIX) :].lower()
                if header in _SENTRY_SENSITIVE_HEADERS or header.replace("-", "_") in names:
                    attributes[key] = ["[Filtered]"]
            elif key.lower().replace("-", "_") in names:
                # 2.x's EventScrubber redacted these names in every span's ``data``.
                attributes[key] = "[Filtered]"
    return span


def _sentry_sdk_major() -> int:
    """The installed sentry-sdk's major version, read from ``sentry_sdk.VERSION`` (``"3.0.0"`` is 3).

    The major decides, not the presence of an option: sentry-sdk 2.76.0 accepts ``data_collection``
    beside ``send_default_pii``, and passing it there would change what 2.x sends.

    A module without a string ``VERSION`` is a stand-in, not an SDK: juniper-data's and juniper-cascor's
    tests put an object with only ``init`` in ``sys.modules["sentry_sdk"]`` and assert 0.4.2's options,
    and a ``MagicMock`` answers ``VERSION`` with another mock. Every real sentry-sdk defines ``VERSION`` as
    a string, so a stand-in reads as 2, the options 0.4.2 passed to every SDK. A ``VERSION`` that does not
    start with ASCII digits reads as 0, which no code path supports (``"\u00b2".isdigit()`` is True and
    ``int`` refuses it): ``configure_sentry`` logs and initialises nothing, rather than raising at startup.
    """
    import sentry_sdk

    version = getattr(sentry_sdk, "VERSION", None)
    if not isinstance(version, str):
        return 2
    head = version.split(".", 1)[0]
    return int(head) if head.isascii() and head.isdigit() else 0


def _data_collection(send_pii: bool) -> dict:
    """sentry-sdk 3.x's ``data_collection``: what 2.x collected under ``send_default_pii=send_pii``, and no more.

    3.x collects by category, and its defaults collect almost everything (``data_collection.py``,
    3.0.0): user identity and the client's address, cookies, every request header, and every
    frame's locals, with a substring denylist (``auth``, ``key``, ``token``, ``session`` ...)
    replacing the values of the keys it matches.

    - ``user_info`` is ``send_pii``: the client's address and the user, as ``send_default_pii``
      governed them on 2.x.
    - Cookies: without ``send_pii``, none, as 2.x attached none; with it, an allowlist with no terms,
      which keeps every cookie's name and replaces every value -- what 0.4.2's hook made of the
      cookies 2.x attached under ``send_default_pii=True``.
    - Request headers: the SDK's denylist, also naming every header in
      :data:`_SENTRY_SENSITIVE_HEADERS` and, without ``send_pii``, :data:`_SENTRY_ADDRESS_HEADERS`.
      The terms are substrings, so each name matches itself.
    - ``stack_frame_variables`` is off, as ``include_local_variables=False`` is on 2.x.

    - Bodies, SQL parameters and redis arguments: none. Queue job arguments, GenAI and MCP inputs and
      outputs, GraphQL documents and variables: only with ``send_pii``, as 2.x attached them. 3.x's
      defaults collect every one of these whatever ``send_pii`` says.

    The remaining categories keep the SDK's default. Query parameters are R-OBS-SC-3's to decide:
    3.x filters them with the same denylist where 2.x sent the query string raw.
    """
    header_terms = _SENTRY_SENSITIVE_HEADERS if send_pii else _SENTRY_SENSITIVE_HEADERS | _SENTRY_ADDRESS_HEADERS
    return {
        "user_info": send_pii,
        "cookies": {"mode": "allowlist", "terms": []} if send_pii else {"mode": "off"},
        "http_headers": {"request": {"mode": "denylist", "terms": sorted(header_terms)}},
        "stack_frame_variables": False,
        # No bodies: 2.x redacted a body's denylisted keys with the EventScrubber that 3.0.0 deleted,
        # and 3.x also puts the raw body on every sampled server span (``http.request.body.data``).
        # R-OBS-SC-3 decides bodies on both majors; until then 3.x sends none.
        "http_bodies": [],
        # 2.x never recorded SQL parameters by default (only under ``_experiments.record_sql_params``)
        # and recorded a redis command's arguments only under ``send_default_pii``; 3.x records both.
        "database_query_data": False,
        # 2.x attached these only under ``send_default_pii``; 3.x's defaults attach them always.
        "queues": send_pii,
        "gen_ai": {"inputs": send_pii, "outputs": send_pii},
        "mcp": {"inputs": send_pii, "outputs": send_pii},
        "graphql": {"document": send_pii, "variables": send_pii},
    }


def configure_sentry(
    dsn: str | None,
    service_name: str,
    version: str,
    *,
    send_pii: bool = False,
    traces_sample_rate: float = DEFAULT_SENTRY_TRACES_SAMPLE_RATE,
) -> None:
    """Initialize Sentry. No-op when ``dsn`` is None or empty.

    Frame-local variables are never captured, and there is deliberately no
    parameter to turn them back on: the value they add to a report is not
    worth a secret in any frame's locals reaching a third-party service.

    Works with sentry-sdk 2.x and 3.x; the installed major decides which
    options are passed (see the module docstring).

    Args:
        dsn: Sentry DSN URL. Pass ``None`` or empty string to skip
            initialization.
        service_name: Service name for Sentry environment tag (used in
            the ``release`` field as ``"<service_name>@<version>"``).
        version: Application version string.
        send_pii: Whether to send default PII (IP addresses, etc.) to
            Sentry. **Defaults to False** (SEC-10); operators opt in
            explicitly via per-service env vars when they accept the
            risk. The hooks (``before_send`` for error events; on 2.x
            ``before_send_transaction`` for transactions, on 3.x
            ``before_send_span`` for spans) still scrub sensitive headers
            and cookies regardless of this flag.
        traces_sample_rate: Fraction of transactions (on 3.x, traces) to send (0.0–1.0).
    """
    if not dsn:
        return

    import sentry_sdk

    major = _sentry_sdk_major()
    if major not in (2, 3):
        # Neither option set has been measured against this major, and consumers' own pins
        # (``sentry-sdk>=2.0.0``) admit it: send nothing rather than guess.
        _logging.getLogger(__name__).warning("sentry-sdk %s is not supported (2.x and 3.x are); Sentry is not initialised", sentry_sdk.VERSION)
        return

    options = {
        "dsn": dsn,
        "traces_sample_rate": traces_sample_rate,
        "release": f"{service_name}@{version}",
        "before_send": _strip_sensitive_headers,
    }
    if major == 3:
        from sentry_sdk.integrations.logging import LoggingIntegration

        options.update(
            # PII, cookies, the extra header terms and no frame locals, by category.
            data_collection=_data_collection(send_pii),
            # Installed whatever ``traces_sample_rate`` says: at 0.0 the SDK still sends
            # a span whose caller's ``sentry-trace`` header marks the trace sampled.
            before_send_span=_strip_sensitive_span_attributes,
            # 3.x installs no logging integration by default; 2.x's default made an ERROR
            # record an error event, which 3.x's default ``event_level`` (None) does not.
            integrations=[LoggingIntegration(event_level=_logging.ERROR)],
            # 3.x defaults it to True (2.x: False): every message event, an ERROR record without an
            # exception among them, would carry the whole thread stack with its source context.
            attach_stacktrace=False,
        )
    else:
        options.update(
            send_default_pii=send_pii,
            # Never snapshot frame locals into events: a local can hold a secret
            # under any name (the canopy#683 finding's was ``candidate``).
            include_local_variables=False,
            enable_logs=True,
            # The SDK never passes a transaction to ``before_send``. Without this, a
            # ``send_pii=True`` transaction carries the raw ``X-API-Key`` (round-42 F2).
            # Installed whatever ``traces_sample_rate`` says: even at 0.0 the SDK sends
            # a transaction whose caller's ``sentry-trace`` header marks it sampled.
            before_send_transaction=_strip_sensitive_headers,
        )
    sentry_sdk.init(**options)
    # Recorded once ``init`` has returned: a call that raised, or that initialised nothing, leaves the
    # previous client and its ``send_pii`` in place, and the two still agree.
    global _send_pii, _configured_client
    try:
        client = sentry_sdk.get_global_scope().client
    except Exception:  # noqa: BLE001 — a stand-in ``sentry_sdk`` (the consumers' tests) has only ``init``
        client = None
    _send_pii, _configured_client = send_pii, client
