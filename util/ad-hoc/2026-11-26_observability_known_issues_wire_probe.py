#!/usr/bin/env python3
"""The pre-existing Sentry exposures that juniper-observability 0.4.3 leaves as 0.4.2 had them, measured on the wire.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling of 2026-11-26 that the juniper-observability 0.4.3 Release lists these as its Known
    Issues; notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md ("New pre-existing
    findings for the Overtoad"); util/ad-hoc/2026-11-24_sentry_sdk_major_wire_probe.py, whose capturing transport and
    init wrapper this reuses, and which does not send any of the values below.

Drives one FastAPI app through the REAL sentry-sdk, initialised by ``juniper_observability.configure_sentry`` (the copy
on ``sys.path``; the first line printed names it), into a capturing transport: nothing leaves the host, and the DSN is
a placeholder. Every trace is sampled. For each ``send_pii`` value it sends three requests:

1. PROXY: ``GET /boom`` raises. It carries a client address in each of five proxy headers that the hooks do not name:
   ``Forwarded``, ``X-Client-IP``, ``CF-Connecting-IP``, ``True-Client-IP`` and ``X-Cluster-Client-IP``, one
   documentation address (TEST-NET-3) each.
2. BODY: ``POST /api/remote/connect`` carries juniper-canopy's request body (``host``, ``port``, and ``authkey`` as a
   pydantic ``SecretStr``; ``src/main.py`` on canopy's ``main``) and logs an ERROR record, as canopy's handler does
   when the connection fails.
3. LOGS: ``GET /log`` logs a WARNING record whose ``extra`` carries one marker under ``api_key``, a name both
   majors' denylists name, and another under ``detail``, a name neither does.

For each value it prints every envelope item that carries it, with the JSON paths. That item is the finding: the
script reports, it does not judge. Run it once per sentry-sdk major.

Exit status: 0 when every request produced the item that could carry its value; 2 (VACUOUS) when the error event for
``/boom`` recorded none of the five headers, or ``/api/remote/connect`` produced no error event, since a value that
never reached the SDK cannot be measured. A run with no ``log`` item prints so: it is a finding, not vacuity.

Usage: PYTHONPATH=juniper-observability python util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py
"""

from __future__ import annotations

import json
import logging
import sys

import sentry_sdk
from pydantic import BaseModel, Field, SecretStr
from sentry_sdk.transport import Transport

import juniper_observability

# Each built from parts, so the whole value never appears in this file's source: the SDK ships source context
# around frames, which would put a literal on the wire by another channel.
BODY_MARKER = "-".join(("kiw", "probe", "authkey", "AKMARK", "5be3"))
LOG_MARKER_DENYLISTED = "-".join(("kiw", "probe", "logextra", "LXMARK", "a1f0"))
LOG_MARKER_PLAIN = "-".join(("kiw", "probe", "logdetail", "LDMARK", "77c2"))

#: Header -> the address it carries. Five distinct two-digit last octets, so no address is a prefix of another.
PROXY_ADDRESSES = {
    "Forwarded": ".".join(("203", "0", "113", "81")),
    "X-Client-IP": ".".join(("203", "0", "113", "82")),
    "CF-Connecting-IP": ".".join(("203", "0", "113", "83")),
    "True-Client-IP": ".".join(("203", "0", "113", "84")),
    "X-Cluster-Client-IP": ".".join(("203", "0", "113", "85")),
}

CONNECT_LOG_MESSAGE = "Remote connect failed"


class RemoteConnectRequest(BaseModel):
    """juniper-canopy's ``POST /api/remote/connect`` body. Module-level: with postponed annotations FastAPI resolves
    an endpoint's annotation in the module's globals, and a model local to ``_app`` read as a missing query
    parameter (HTTP 422, the handler never ran)."""

    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    authkey: SecretStr


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


def _header_value(name: str, address: str) -> str:
    return f"for={address}" if name == "Forwarded" else address


def _app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI()
    log = logging.getLogger("kiw.probe")

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    @app.post("/api/remote/connect")
    async def connect(request: RemoteConnectRequest):  # noqa: ARG001 -- FastAPI parses the body; the SDK reads it
        # A constant message: the record needs to exist, not to carry the client's values. Logging request.host and
        # request.port, as canopy's handler does, was CodeQL py/log-injection (alerts 1135 and 1136 on ml#2669).
        log.error(CONNECT_LOG_MESSAGE)
        return JSONResponse({"error": "Connection failed"}, status_code=500)

    @app.get("/log")
    def log_route():
        log.warning("probe log record", extra={"api_key": LOG_MARKER_DENYLISTED, "detail": LOG_MARKER_PLAIN})
        return {"ok": True}

    return app


def _items(send_pii: bool):
    """Drive the three requests once each; return every envelope item as (type, payload, raw bytes)."""
    transport = _Capturing()
    real_init = sentry_sdk.init

    def init_with_local_transport(**kwargs):
        kwargs["transport"] = transport
        kwargs["traces_sample_rate"] = 1.0  # sample every trace: a deterministic probe
        return real_init(**kwargs)

    sentry_sdk.init = init_with_local_transport
    try:
        juniper_observability.configure_sentry("http://public@127.0.0.1:9/1", "kiw-probe", "0", send_pii=send_pii)
    finally:
        sentry_sdk.init = real_init

    from fastapi.testclient import TestClient

    client = TestClient(_app(), raise_server_exceptions=False)
    statuses = (
        client.get("/boom", headers={name: _header_value(name, address) for name, address in PROXY_ADDRESSES.items()}).status_code,
        client.post("/api/remote/connect", json={"host": "10.0.0.1", "port": 1, "authkey": BODY_MARKER}).status_code,
        client.get("/log").status_code,
    )
    # /boom raises (500), /api/remote/connect answers 500 after logging, /log answers 200. Anything else means a
    # handler did not run as designed, so its item cannot be measured.
    print(f"  HTTP statuses (/boom, /api/remote/connect, /log): {statuses}")
    sentry_sdk.flush(timeout=5)

    items = []
    for envelope in transport.envelopes:
        for item in envelope.items:
            raw = item.get_bytes()
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = None
            items.append((item.type, payload, raw))
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)
    return items


def _carriers(items, value: str):
    """(item type, JSON paths) for every item whose payload, or raw bytes, holds ``value``."""
    found = []
    for item_type, payload, raw in items:
        paths = _paths_holding(payload, value)
        if paths or value.encode() in raw:
            found.append((item_type, paths or ["<raw bytes only>"]))
    return found


def _is_boom_event(item_type, payload) -> bool:
    if item_type != "event" or not isinstance(payload, dict):
        return False
    url = (payload.get("request") or {}).get("url") or ""
    return url.endswith("/boom")


def _is_connect_event(item_type, payload) -> bool:
    if item_type != "event" or not isinstance(payload, dict):
        return False
    message = json.dumps(payload.get("logentry") or payload.get("message") or "")
    return CONNECT_LOG_MESSAGE in message


def main() -> int:
    print("sentry-sdk", sentry_sdk.VERSION, "| juniper_observability", juniper_observability.__version__, "from", juniper_observability.__file__)
    vacuous = False
    for send_pii in (False, True):
        items = _items(send_pii)
        print(f"== send_pii={send_pii}: {len(items)} item(s): {sorted({t for t, _, _ in items})}")

        boom = [p for t, p, _ in items if _is_boom_event(t, p)]
        recorded = set()
        for payload in boom:
            recorded |= {name.lower() for name in ((payload.get("request") or {}).get("headers") or {})}
        proxy_recorded = sorted(name for name in PROXY_ADDRESSES if name.lower() in recorded)
        print(f"  PROXY  /boom error events: {len(boom)}; proxy headers recorded on them: {proxy_recorded}")
        if not proxy_recorded:
            vacuous = True
        for name, address in PROXY_ADDRESSES.items():
            print(f"    {name:20} address carried by: {_carriers(items, address)}")

        connect = [p for t, p, _ in items if _is_connect_event(t, p)]
        print(f"  BODY   /api/remote/connect error events: {len(connect)}")
        if not connect:
            vacuous = True
        for payload in connect:
            data = (payload.get("request") or {}).get("data")
            shown = {k: ("<marker>" if BODY_MARKER in json.dumps(v) else v) for k, v in data.items()} if isinstance(data, dict) else data
            print(f"    request.data: {shown!r}")
        print(f"    authkey carried by: {_carriers(items, BODY_MARKER)}")

        logs = [p for t, p, _ in items if t == "log"]
        print(f"  LOGS   log items: {len(logs)}")
        print(f"    extra api_key (denylisted name) carried by: {_carriers(items, LOG_MARKER_DENYLISTED)}")
        print(f"    extra detail (plain name) carried by:      {_carriers(items, LOG_MARKER_PLAIN)}")
    if vacuous:
        print("VACUOUS: a request produced no item that could carry its value")
        return 2
    print("DONE: every request produced its item; the carriers above are the findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
