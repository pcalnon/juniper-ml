#!/usr/bin/env python3
"""Record what a lock-built environment holds for the Sentry and telemetry paths, as JSON.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Run with the interpreter of a venv built from one consumer lock (``python -I``). It prints:

* the installed versions of the packages the probe cares about;
* every ``opentelemetry*`` distribution, and which of them are an SDK, an exporter, a distro or
  an instrumentation (the plan's condition for "the spans become another path");
* FastAPI's native-telemetry setting for an app built with no ``telemetry=`` argument, which is
  what juniper-cascor's and juniper-canopy's app factories build (juniper-data passes
  ``telemetry=`` with every signal off, data#454); FastAPI before 0.142 has no such setting;
* the type of the global OpenTelemetry tracer provider (a proxy or no-op provider exports nothing);
* the six Sentry DSN variables of plan H-14 as this process sees them, and any ``OTEL_*`` names.

Usage: <venv>/bin/python -I util/ad-hoc/2026-11-09_lock_round_2_env_record.py
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
import json
import os
import sys

SIX_DSNS = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
WATCH = ("fastapi", "starlette", "sentry-sdk", "juniper-observability", "juniper-service-core", "uvicorn", "httpx", "pydantic")
SPAN_PATHS = ("opentelemetry-sdk", "opentelemetry-exporter", "opentelemetry-distro", "opentelemetry-instrumentation")


def _version(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def main() -> int:
    record: dict[str, object] = {"python": sys.version.split()[0], "executable": sys.executable}
    record["versions"] = {name: _version(name) for name in WATCH}
    otel = sorted({f"{(dist.metadata['Name'] or '').lower()}=={dist.version}" for dist in md.distributions() if (dist.metadata["Name"] or "").lower().startswith("opentelemetry")})
    record["opentelemetry_distributions"] = otel
    record["span_paths_present"] = [entry for entry in otel if entry.startswith(SPAN_PATHS)]
    try:
        # FastAPI >= 0.142. A call, not an import statement, so CodeQL's unused-import query has nothing to flag;
        # it imports the module exactly as ``import fastapi.telemetry`` did when the lock round's records were made.
        importlib.import_module("fastapi.telemetry")

        record["fastapi_has_native_telemetry"] = True
    except ImportError:
        record["fastapi_has_native_telemetry"] = False
    from fastapi import FastAPI

    app = FastAPI()
    record["fastapi_default_telemetry"] = getattr(app, "_telemetry", None)
    try:
        from opentelemetry import trace

        record["otel_tracer_provider"] = type(trace.get_tracer_provider()).__name__
    except ImportError:
        record["otel_tracer_provider"] = None
    record["sentry_dsn_env"] = {name: os.environ.get(name) for name in SIX_DSNS}
    record["otel_env_names"] = sorted(name for name in os.environ if name.startswith("OTEL_"))
    print(json.dumps(record, indent=1, sort_keys=True, default=repr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
