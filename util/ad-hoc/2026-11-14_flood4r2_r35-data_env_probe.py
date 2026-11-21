#!/usr/bin/env python3
"""Print what an interpreter is, which test packages it imports, and which secret-scanner build pre-commit cached.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260
Version:     0.1.0
License:     MIT License

Run it under the interpreter to be trusted (this host's python3 on PATH was re-pointed at the system CPython on
2026-11-14, so an interpreter is evidence only once its sys.executable and sys.base_prefix are on record).

Usage:
    <interpreter> util/ad-hoc/2026-11-14_flood4r2_r35-data_env_probe.py [--out <json>]

It reads pre-commit's cache database READ-ONLY (sqlite URI mode=ro) and hashes the cached scanner binary; it writes
nothing but the optional --out file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import pathlib
import sqlite3
import sys

PRE_COMMIT_DB = pathlib.Path.home() / ".cache" / "pre-commit" / "db.db"
PACKAGES = ("pytest", "yaml", "pytest_timeout", "pytest_cov", "juniper_data")


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _packages() -> dict[str, str]:
    found: dict[str, str] = {}
    for name in PACKAGES:
        try:
            module = importlib.import_module(name)
        except ImportError as error:
            found[name] = f"MISSING ({error})"
            continue
        found[name] = f"{getattr(module, '__version__', '?')} at {getattr(module, '__file__', '?')}"
    return found


def _scanner_builds() -> list[dict[str, str]]:
    if not PRE_COMMIT_DB.is_file():
        return []
    connection = sqlite3.connect(f"file:{PRE_COMMIT_DB}?mode=ro", uri=True)
    try:
        rows = [row for row in connection.execute("select repo, ref, path from repos") if "leaks" in row[0]]
    finally:
        connection.close()
    builds = []
    for repo, ref, path in rows:
        binary = pathlib.Path(path) / "golangenv-system" / "bin" / "gitleaks"
        builds.append({"repo": repo, "ref": ref, "path": path, "binary": str(binary), "exists": str(binary.is_file()), "sha256": _sha256(binary) if binary.is_file() else ""})
    return builds


def main(argv: list[str]) -> int:
    """Print the probe as JSON, and write it to --out when given."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", help="also write the JSON here")
    args = parser.parse_args(argv)
    probe = {
        "sys.version": sys.version,
        "sys.executable": sys.executable,
        "sys.base_prefix": sys.base_prefix,
        "sys.prefix": sys.prefix,
        "packages": _packages(),
        "pre_commit_scanner_builds": _scanner_builds(),
    }
    text = json.dumps(probe, indent=1)
    print(text)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
