#!/usr/bin/env python3
"""
Summarise a saved juniper-data CodeQL alert listing: has a module-level ``pytestmark`` ever drawn an alert?

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation (is the prescreen's ``unused-global: pytestmark`` prediction a real CodeQL alert?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_codeql_python_prescreen.py; juniper-data#529 (the precedent)

Usage:
    python3 <this> <alerts.json> [<repo-relative path> ...]

<alerts.json> is the saved output of the code-scanning alerts listing for the repository (every state, CodeQL only;
``--paginate`` output, so one JSON array per page, concatenated). Prints, per rule the prescreen predicts
(py/unused-global-variable, py/unused-local-variable), every alert with its state, path and line, then every alert of
any rule on the paths named on the command line. Reads one file and writes nothing.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

RULES = ("py/unused-global-variable", "py/unused-local-variable")


def _load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    decoder = json.JSONDecoder()
    alerts: list[dict] = []
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        page, pos = decoder.raw_decode(text, pos)
        alerts.extend(page)
    return alerts


def _row(alert: dict) -> str:
    loc = (alert.get("most_recent_instance") or {}).get("location") or {}
    return f"  #{alert.get('number')} {alert.get('state'):9} {alert['rule']['id']:28} {loc.get('path')}:{loc.get('start_line')} created {str(alert.get('created_at'))[:10]} {str(alert.get('dismissed_reason') or '')}"


def main() -> int:
    alerts = _load(sys.argv[1])
    paths = set(sys.argv[2:])
    print(f"{len(alerts)} CodeQL alerts in all states; by state: {dict(Counter(a.get('state') for a in alerts))}")
    for rule in RULES:
        mine = [a for a in alerts if a["rule"]["id"] == rule]
        print(f"{rule}: {len(mine)} alert(s) ever; in a tests path: {sum(1 for a in mine if '/tests/' in str(((a.get('most_recent_instance') or {}).get('location') or {}).get('path')))}")
        for alert in mine:
            print(_row(alert))
    if paths:
        print("alerts of any rule on the named paths:")
        hits = [a for a in alerts if ((a.get("most_recent_instance") or {}).get("location") or {}).get("path") in paths]
        for alert in hits:
            print(_row(alert))
        print(f"  ({len(hits)} alert(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
