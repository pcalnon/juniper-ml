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
- Still OUTSIDE the hook (left for 0.4.3, to be designed and validated on
  its own): query strings,
  Sentry Logs (``enable_logs=True`` has no ``before_send_log``), request
  bodies, breadcrumbs, exception values and list-shaped ``headers``.

``configure_sentry`` is a no-op when ``dsn`` is ``None`` or the empty
string, so consumers can call it unconditionally during startup.
"""

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
    _strip_frame_local_variables(event)
    return event


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

    Args:
        dsn: Sentry DSN URL. Pass ``None`` or empty string to skip
            initialization.
        service_name: Service name for Sentry environment tag (used in
            the ``release`` field as ``"<service_name>@<version>"``).
        version: Application version string.
        send_pii: Whether to send default PII (IP addresses, etc.) to
            Sentry. **Defaults to False** (SEC-10); operators opt in
            explicitly via per-service env vars when they accept the
            risk. The hook (``before_send`` for error events,
            ``before_send_transaction`` for transactions) still scrubs
            sensitive headers and cookies regardless of this flag.
        traces_sample_rate: Fraction of transactions to send (0.0–1.0).
    """
    if not dsn:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=send_pii,
        # Never snapshot frame locals into events: a local can hold a secret
        # under any name (the canopy#683 finding's was ``candidate``).
        include_local_variables=False,
        enable_logs=True,
        traces_sample_rate=traces_sample_rate,
        release=f"{service_name}@{version}",
        before_send=_strip_sensitive_headers,
        # The SDK never passes a transaction to ``before_send``. Without this, a
        # ``send_pii=True`` transaction carries the raw ``X-API-Key`` (round-42 F2).
        # Installed whatever ``traces_sample_rate`` says: even at 0.0 the SDK sends
        # a transaction whose caller's ``sentry-trace`` header marks it sampled.
        before_send_transaction=_strip_sensitive_headers,
    )
