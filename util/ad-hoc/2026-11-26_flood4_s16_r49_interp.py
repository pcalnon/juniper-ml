"""
Print the running interpreter's identity and the versions of the packages a juniper-canopy unit-lane run depends on.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49 (COMMON_S16 section 1: record every interpreter used)

Usage:
    <interpreter> -I <this file>
Prints one JSON object: sys.version, sys.executable, sys.base_prefix and the installed versions (importlib.metadata)
of pytest, pytest-asyncio, pytest-timeout, pytest-cov, pytest-repeat, coverage, fastapi, starlette, httpx, anyio and
juniper-canopy. Imports nothing from canopy.
"""

from __future__ import annotations

import importlib.metadata
import json
import sys

PACKAGES = ("pytest", "pytest-asyncio", "pytest-timeout", "pytest-cov", "pytest-repeat", "coverage", "fastapi", "starlette", "httpx", "anyio", "juniper-canopy")


def main() -> int:
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    print(json.dumps({"version": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "packages": versions}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
