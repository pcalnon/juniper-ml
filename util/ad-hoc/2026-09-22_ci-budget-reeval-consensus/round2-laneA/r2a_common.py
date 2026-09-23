#!/usr/bin/env python3
"""
Shared read-only helpers for the round-2 Lane A re-derivation (CI-budget re-evaluation, ml#2017).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- consensus round 2, Lane A (independent re-derivation; never imports the reprobe)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Every call is a READ. REST calls are counted so the shared budget can be reported.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed-argv gh calls only
import time
from datetime import datetime

OWNER = "pcalnon"
REST_CALLS = {"n": 0}
GQL_CALLS = {"n": 0}


def rest(path: str, attempts: int = 3, raw: bool = False):
    """One REST read (retried on transient failure). raw=True returns (rc, text)."""
    last = None
    for attempt in range(1, attempts + 1):
        REST_CALLS["n"] += 1
        proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
        if raw:
            if proc.returncode == 0 or attempt == attempts:
                return proc.returncode, proc.stdout, proc.stderr
        else:
            if proc.returncode == 0:
                try:
                    return json.loads(proc.stdout or "null")
                except json.JSONDecodeError as exc:
                    last = exc
            else:
                last = proc.stderr.strip()[-400:]
        time.sleep(2 * attempt)
    raise RuntimeError(f"REST {path} failed: {last}")


def rest_pages(path: str, key: str | None = None, max_pages: int = 20) -> list:
    out: list = []
    sep = "&" if "?" in path else "?"
    for page in range(1, max_pages + 1):
        data = rest(f"{path}{sep}per_page=100&page={page}")
        items = data.get(key, []) if key else data
        if not items:
            break
        out.extend(items)
        if len(items) < 100:
            break
    return out


def gql(query: str, attempts: int = 3) -> dict:
    last = None
    for attempt in range(1, attempts + 1):
        GQL_CALLS["n"] += 1
        proc = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True, check=False)  # nosec B603 B607
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if data.get("errors"):
                last = data["errors"]
            else:
                return data["data"]
        else:
            last = proc.stderr.strip()[-600:]
        time.sleep(2 * attempt)
    raise RuntimeError(f"GraphQL failed: {last}")


def ts(s: str | None):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def budget_line() -> str:
    return f"[calls] REST {REST_CALLS['n']}  GraphQL {GQL_CALLS['n']}"
