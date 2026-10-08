#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Prints which test dependencies the running interpreter can import
# (run with `python -s` so ~/.local does not masquerade as the env), and where any
# juniper_* client package would be imported from. Read-only.
"""Probe the current interpreter for the client-library test dependencies."""
import importlib
import sys

MODULES = [
    "numpy", "pytest", "yaml", "requests", "responses", "pytest_cov", "pytest_timeout",
    "juniper_observability", "juniper_data_client", "juniper_cascor_client",
    "juniper_cascor_worker", "websockets", "torch", "aiohttp", "httpx",
]

print(sys.executable, sys.version.split()[0])
for name in MODULES:
    try:
        mod = importlib.import_module(name)
        print(f"  ok      {name:24s} {getattr(mod, '__version__', '')} {getattr(mod, '__file__', '')}")
    except Exception as exc:  # noqa: BLE001 - a probe reports every failure shape
        print(f"  MISSING {name:24s} {type(exc).__name__}: {exc}")
