#!/usr/bin/env python3
"""Which outbound Sentry items carry a sensitive request value or the client's address, on sentry-sdk 2.x or 3.x.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: R14 of notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md; successor of
    util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py, which reads only ``transaction`` and ``event`` items and cannot
    run on sentry-sdk 3.x, where transactions became streamed spans.

Drives one FastAPI app through the REAL sentry-sdk, initialised by ``juniper_observability.configure_sentry`` (the copy
on ``sys.path``; the first line printed names it), into a capturing transport: nothing leaves the host, and the DSN is
a placeholder. Each request carries one secret marker in every header the hooks name (``X-API-Key``,
``Authorization``, ``Proxy-Authorization``, ``Sec-WebSocket-Protocol``, ``X-CSRF-Token``, ``X-XSRF-Token`` and
``Cookie``), in two cookies (``session``, which both majors' denylists name, and ``canopy_ui``, which neither does),
the client's address in ``X-Forwarded-For`` and ``X-Real-IP``, and a query-string marker in ``?api_key=``.

For each ``send_pii`` value it prints, per envelope item (``event``; ``transaction`` on 2.x, ``span`` on 3.x; ``log``),
the JSON paths that hold the secret, the address and the query marker.

Verdict, and exit status:
- 1, LEAK: the secret is in any item, or the address is in any item under ``send_pii=False``.
- 2, VACUOUS: no error event, or no trace item (a transaction on 2.x, an ``http.server`` span on 3.x), or an event or
  trace item that did not record every one of the hooks' headers. A header that never arrived cannot leak.
- 0, CLEAN otherwise.
The query-string marker is reported and not judged: query strings are R-OBS-SC-3's channel.

Usage: python -I util/ad-hoc/2026-11-24_sentry_sdk_major_wire_probe.py   (an installed juniper-observability)
       PYTHONPATH=juniper-observability python util/ad-hoc/2026-11-24_sentry_sdk_major_wire_probe.py   (a checkout)
"""

from __future__ import annotations

import json
import sys

import sentry_sdk
from sentry_sdk.transport import Transport

import juniper_observability

# Each built from parts, so the whole value never appears in this file's source: the SDK ships source context
# around frames, which would put a literal on the wire by another channel.
MARKER = "-".join(("s3w", "probe", "secret", "LEAKMARK", "9d21"))
ADDRESS = ".".join(("203", "0", "113", "77"))  # TEST-NET-3, a documentation address
QUERY_MARKER = "-".join(("s3w", "query", "QMARK", "41c7"))

#: The hooks' headers, lower-case as the ASGI integration records them.
HOOK_HEADERS = ("x-api-key", "authorization", "cookie", "proxy-authorization", "sec-websocket-protocol", "x-csrf-token", "x-xsrf-token")

REQUEST_HEADERS = {
    "X-API-Key": MARKER,
    "Authorization": "Bearer " + MARKER,
    "Cookie": "session=" + MARKER + "; canopy_ui=" + MARKER,
    "Proxy-Authorization": "Basic " + MARKER,
    "Sec-WebSocket-Protocol": "bearer, " + MARKER,
    "X-CSRF-Token": MARKER,
    "X-XSRF-Token": MARKER,
    "X-Forwarded-For": ADDRESS,
    "X-Real-IP": ADDRESS,
}


class _Capturing(Transport):
    def __init__(self) -> None:
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope) -> None:
        self.envelopes.append(envelope)


def _paths_holding(node, marker, prefix=""):
    """Every JSON path in ``node`` whose string value contains ``marker``."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            found.extend(_paths_holding(value, marker, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_paths_holding(value, marker, f"{prefix}[{index}]"))
    elif isinstance(node, str) and marker in node:
        found.append(prefix)
    return found


def _recorded_headers(item_type, payload):
    """The hook headers an event or trace item recorded: ``request.headers`` (event, transaction) or the server span's attributes."""
    if item_type in ("event", "transaction"):
        headers = (payload.get("request") or {}).get("headers") or {}
        return {name.lower() for name in headers}
    names = set()
    for span in payload.get("items", []):
        attributes = span.get("attributes") or {}
        if (attributes.get("sentry.op") or {}).get("value") == "http.server":
            names |= {key[len("http.request.header.") :] for key in attributes if key.startswith("http.request.header.")}
    return names


def _run(send_pii: bool) -> tuple[int, int, int, int]:
    """Drive /ok and /boom once each; return (leaks, events, trace items, items missing a hook header)."""
    transport = _Capturing()
    real_init = sentry_sdk.init

    def init_with_local_transport(**kwargs):
        kwargs["transport"] = transport
        kwargs["traces_sample_rate"] = 1.0  # sample every trace: a deterministic probe
        return real_init(**kwargs)

    sentry_sdk.init = init_with_local_transport
    try:
        juniper_observability.configure_sentry("http://public@127.0.0.1:9/1", "s3w-probe", "0", send_pii=send_pii)
    finally:
        sentry_sdk.init = real_init

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/ok?api_key=" + QUERY_MARKER, headers=REQUEST_HEADERS)
    client.get("/boom?api_key=" + QUERY_MARKER, headers=REQUEST_HEADERS)
    sentry_sdk.flush(timeout=5)

    trace_type = "span" if int(sentry_sdk.VERSION.split(".")[0]) >= 3 else "transaction"
    leaks = events = traces = headerless = 0
    for envelope in transport.envelopes:
        for item in envelope.items:
            raw = item.get_bytes()
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = None
            marker_paths = _paths_holding(payload, MARKER)
            address_paths = _paths_holding(payload, ADDRESS)
            query = _paths_holding(payload, QUERY_MARKER)
            leaked = bool(marker_paths) or MARKER.encode() in raw or (not send_pii and (bool(address_paths) or ADDRESS.encode() in raw))
            leaks += int(leaked)
            missing = []
            if item.type in ("event", trace_type) and isinstance(payload, dict):
                recorded = _recorded_headers(item.type, payload)
                if item.type == "event":
                    events += 1
                else:
                    traces += int(bool(recorded))
                missing = [name for name in HOOK_HEADERS if name not in recorded]
                headerless += int(bool(missing) and (item.type == "event" or bool(recorded)))
            print(
                f"  send_pii={send_pii!s:5} {item.type:12} leak={leaked!s:5} marker_paths={marker_paths} address_paths={address_paths} query(not judged)={query}"
                + (f" MISSING-HEADERS={missing}" if missing else "")
            )
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)
    return leaks, events, traces, headerless


def main() -> int:
    print("sentry-sdk", sentry_sdk.VERSION, "| juniper_observability from", juniper_observability.__file__)
    total_leaks = 0
    for send_pii in (False, True):
        leaks, events, traces, headerless = _run(send_pii)
        if events == 0 or traces == 0 or headerless:
            print(f"VACUOUS: send_pii={send_pii} saw {events} event(s) and {traces} trace item(s); {headerless} item(s) lacked a hook header")
            return 2
        total_leaks += leaks
    print("RESULT:", "LEAK" if total_leaks else "CLEAN", f"({total_leaks} item(s) carry the secret, or the address without send_pii)")
    return 1 if total_leaks else 0


if __name__ == "__main__":
    sys.exit(main())
