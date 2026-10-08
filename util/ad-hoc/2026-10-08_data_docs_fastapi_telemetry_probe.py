#!/usr/bin/env python3
"""Probe FastAPI 0.142 native telemetry behaviour for the juniper-data #454/#456/#447 adjudication.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. Run under a venv that pins the lock's fastapi/sentry-sdk versions, one MODE per
fresh process (OpenTelemetry global providers are process-wide and set-once):

    <venv>/bin/python -I util/ad-hoc/2026-10-08_data_docs_fastapi_telemetry_probe.py default
    <venv>/bin/python -I ... sentry          # sentry_sdk.init the way juniper-observability does
    OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:9 <venv>/bin/python -I ... lifespan
    OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:9 <venv>/bin/python -I ... lifespan-optout

The DSN / endpoint point at a closed localhost port, so nothing leaves the machine.
"""

import logging
import sys

from fastapi import FastAPI
from opentelemetry import _logs, metrics, trace

OPT_OUT = {"tracing": False, "metrics": False, "logs": False, "operation_spans": False, "auto_configure": False}


def providers() -> str:
    return f"tracer={type(trace.get_tracer_provider()).__name__} meter={type(metrics.get_meter_provider()).__name__} logger={type(_logs.get_logger_provider()).__name__}"


def main(mode: str) -> int:
    if mode == "default":
        app = FastAPI()
        print(f"[default] {providers()} native_enabled={app._native_telemetry.enabled()}")
        return 0
    if mode == "sentry":
        import sentry_sdk

        sentry_sdk.init(
            dsn="http://public@127.0.0.1:9/1",
            send_default_pii=False,
            include_local_variables=False,
            enable_logs=True,
            traces_sample_rate=0.1,
            release="juniper-data@probe",
        )
        app = FastAPI()
        print(f"[sentry {sentry_sdk.VERSION}] {providers()} native_enabled={app._native_telemetry.enabled()}")
        return 0
    if mode in ("lifespan", "lifespan-optout"):
        from fastapi.testclient import TestClient

        records: list[str] = []

        class Grab(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        logging.getLogger("fastapi").addHandler(Grab())
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
        app = FastAPI(telemetry=OPT_OUT) if mode == "lifespan-optout" else FastAPI()

        @app.get("/ping")
        def ping() -> dict:
            return {"ok": True}

        with TestClient(app) as client:
            status = client.get("/ping").status_code
        warned = [r for r in records if "FastAPI automatic telemetry configuration failed" in r]
        print(f"[{mode}] status={status} {providers()} warnings={len(warned)}")
        for w in warned:
            print(f"    {w[:300]}")
        return 0
    print(f"unknown mode {mode!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "default"))
