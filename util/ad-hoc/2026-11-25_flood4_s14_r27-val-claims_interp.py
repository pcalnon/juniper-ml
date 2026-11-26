"""
Print the running interpreter's identity and the versions of the packages a canopy unit-lane claim depends on.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r27 (juniper-canopy unit-lane :8100 connects)

Usage (run with the interpreter under test):
    python -I <this file>

Prints one JSON object: sys.version, sys.executable, sys.base_prefix, and for each named distribution its installed
version or null when it is not installed.
"""

from __future__ import annotations

import importlib.metadata
import json
import sys

DISTRIBUTIONS = (
    "pytest",
    "pytest-asyncio",
    "pytest-timeout",
    "pytest-cov",
    "httpx",
    "httpcore",
    "anyio",
    "starlette",
    "fastapi",
    "juniper-observability",
    "juniper-service-core",
    "juniper-cascor-client",
    "juniper-data-client",
    "torch",
    "h5py",
)


def main() -> int:
    versions = {}
    for name in DISTRIBUTIONS:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    print(json.dumps({"version": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "distributions": versions}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
