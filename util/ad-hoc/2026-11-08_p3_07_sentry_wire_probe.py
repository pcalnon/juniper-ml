#!/usr/bin/env python3
"""P3-07 probe: which outbound Sentry items carry a sensitive request value, and in which field.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use probe)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Drives one FastAPI app through the REAL sentry-sdk, initialised by the INSTALLED
``juniper_observability.configure_sentry``, into a capturing transport (nothing leaves the
host). Each request carries one marker secret in ``X-API-Key``, ``Authorization``, ``Cookie``
and, since the owner's ruling of 2026-11-08 widened the hook's header set,
``Proxy-Authorization``, ``Sec-WebSocket-Protocol``, ``X-CSRF-Token`` and ``X-XSRF-Token``.
For each ``send_pii`` value it prints, per envelope item (``transaction`` / ``event``),
whether the marker is in the serialised item, and the JSON paths that hold it.

Run it once against the code before P3-07 and once after: before, a ``send_pii=True``
transaction carries the raw ``X-API-Key`` (round-42 finding F2), and the three headers that
neither SDK list names reach every item under either ``send_pii`` value; after, no item
carries the marker. To run it against another copy of the package, drop ``-I`` and put the
copy on ``PYTHONPATH``; the first line it prints names the module it imported.

Exit status: 0 when no item carries the marker under either ``send_pii`` value; 1 when at least
one does; 2 when the harness saw no transaction or no error event, or an item that did not record
every probed header (a vacuous run: an absent header cannot leak, and proves nothing).

Usage: python -I util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py
"""

from __future__ import annotations

import json
import sys

import sentry_sdk
from sentry_sdk.transport import Transport

from juniper_observability import configure_sentry

# Built from parts so the whole value never appears in this file's source (the SDK ships
# source context around frames, which would put a literal on the wire by another channel).
MARKER = "-".join(("p307", "probe", "secret", "LEAKMARK", "5be1"))


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


def _run(send_pii: bool) -> tuple[int, int, int, int]:
    transport = _Capturing()
    real_init = sentry_sdk.init

    def init_with_local_transport(**kwargs):
        kwargs["transport"] = transport
        kwargs["traces_sample_rate"] = 1.0  # sample every transaction: a deterministic probe
        return real_init(**kwargs)

    sentry_sdk.init = init_with_local_transport
    try:
        configure_sentry("http://public@127.0.0.1:9/1", "p307-probe", "0", send_pii=send_pii)
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

    # Two cookies: ``session`` is on the SDK's EventScrubber denylist, ``juniper_auth`` is not.
    headers = {
        "X-API-Key": MARKER,
        "Authorization": "Bearer " + MARKER,
        "Cookie": "session=" + MARKER + "; juniper_auth=" + MARKER,
        "Proxy-Authorization": "Basic " + MARKER,
        "Sec-WebSocket-Protocol": "bearer, " + MARKER,
        "X-CSRF-Token": MARKER,
        "X-XSRF-Token": MARKER,
    }
    client = TestClient(app, raise_server_exceptions=False)
    client.get("/ok", headers=headers)
    client.get("/boom", headers=headers)
    sentry_sdk.flush(timeout=5)

    leaks = transactions = events = headerless = 0
    for envelope in transport.envelopes:
        for item in envelope.items:
            if item.type not in ("transaction", "event"):
                continue
            if item.type == "transaction":
                transactions += 1
            else:
                events += 1
            raw = item.get_bytes()
            payload = json.loads(raw)
            paths = _paths_holding(payload, MARKER)
            on_wire = MARKER.encode() in raw
            leaks += int(on_wire)
            # Absence of the marker means nothing for a header the item never recorded at all.
            recorded = (payload.get("request") or {}).get("headers") or {}
            missing = [name.lower() for name in headers if name.lower() not in recorded]
            headerless += int(bool(missing))
            print(f"  send_pii={send_pii!s:5} {item.type:11} marker-on-wire={on_wire!s:5} paths={paths}" + (f" MISSING-HEADERS={missing}" if missing else ""))
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)
    return leaks, transactions, events, headerless


def main() -> int:
    import juniper_observability

    print("sentry-sdk", sentry_sdk.VERSION, "| juniper_observability from", juniper_observability.__file__)
    total_leaks = 0
    for send_pii in (False, True):
        leaks, transactions, events, headerless = _run(send_pii)
        if transactions == 0 or events == 0 or headerless:
            print(f"VACUOUS: send_pii={send_pii} saw {transactions} transaction(s) and {events} event(s); {headerless} item(s) lacked a probed header")
            return 2
        total_leaks += leaks
    print("RESULT:", "LEAK" if total_leaks else "CLEAN", f"({total_leaks} item(s) carry the marker)")
    return 1 if total_leaks else 0


if __name__ == "__main__":
    sys.exit(main())
