"""Sentry initialization with reconciled signature and SEC-10 hook.

This module exposes the **superset** signature originally introduced
in juniper-data for SEC-10 (security review of Sentry forwarding) and
makes it the cross-service standard:

- ``send_pii`` is keyword-only, defaulting to ``False``.
- A ``before_send`` hook always scrubs ``X-API-Key``, ``Authorization``,
  and ``Cookie`` headers from outbound events regardless of
  ``send_default_pii`` — defense in depth so that future Sentry SDK
  changes (replay, custom integrations) cannot leak credentials.

``configure_sentry`` is a no-op when ``dsn`` is ``None`` or the empty
string, so consumers can call it unconditionally during startup.
"""

DEFAULT_SENTRY_TRACES_SAMPLE_RATE = 0.1

# SEC-10: header names that may carry API keys or session identifiers.
_SENTRY_SENSITIVE_HEADERS = frozenset({"x-api-key", "authorization", "cookie"})


def _strip_sensitive_headers(event, hint):  # noqa: ARG001 — Sentry hook signature
    """Redact sensitive request headers in a Sentry event with ``[Filtered]``.

    Sentry calls this via ``before_send`` for every outbound event.
    The filter only rewrites keys in :data:`_SENTRY_SENSITIVE_HEADERS`
    so non-sensitive diagnostic headers (user-agent, trace IDs, etc.)
    still reach Sentry unchanged.
    """
    request_data = event.get("request", {}) if isinstance(event, dict) else {}
    headers = request_data.get("headers", {}) if isinstance(request_data, dict) else {}
    if isinstance(headers, dict):
        for key in list(headers.keys()):
            if key.lower() in _SENTRY_SENSITIVE_HEADERS:
                headers[key] = "[Filtered]"
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

    Args:
        dsn: Sentry DSN URL. Pass ``None`` or empty string to skip
            initialization.
        service_name: Service name for Sentry environment tag (used in
            the ``release`` field as ``"<service_name>@<version>"``).
        version: Application version string.
        send_pii: Whether to send default PII (IP addresses, etc.) to
            Sentry. **Defaults to False** (SEC-10); operators opt in
            explicitly via per-service env vars when they accept the
            risk. The ``before_send`` filter still scrubs sensitive
            headers regardless of this flag.
        traces_sample_rate: Fraction of transactions to send (0.0–1.0).
    """
    if not dsn:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=send_pii,
        enable_logs=True,
        traces_sample_rate=traces_sample_rate,
        release=f"{service_name}@{version}",
        before_send=_strip_sensitive_headers,
    )
