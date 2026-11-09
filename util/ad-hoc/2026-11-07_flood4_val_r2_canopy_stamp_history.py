#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Round-2 check of a docs carrier's version stamps against canopy's practice.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#802 docs carrier, validation round 2, correction D-F6 (findings: tmp/flood4/canopy/val-round2/)

Per doc: every `**Version**:` / `**Version:**` line on main and in the carrier (header and
footer must agree; one bump from main: patch+1, or minor+1 with patch 0); headings outside
code fences added/removed (main vs carrier); and main's history of the stamp (each commit
that changed the doc's first Version value: old -> new, bump kind, headings that commit added
to the doc). Read-only (git show / git log in the canopy primary).

Usage: python3 <this> <canopy primary> <base sha> <carrier> <out json> <doc> [<doc> ...]
"""
import json
import pathlib
import re
import subprocess
import sys

VER = re.compile(r"^\*\*Version:?\*\*:?\s*([0-9]+\.[0-9]+\.[0-9]+)")
HEAD = re.compile(r"^#{1,6}\s+\S")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def git(primary, *args):
    return subprocess.run(["git", "-C", primary, *args], capture_output=True, text=True).stdout


def versions(text):
    return [m.group(1) for m in (VER.match(ln) for ln in text.splitlines()) if m]


def headings(text):
    out, fenced = [], False
    for ln in text.splitlines():
        if FENCE.match(ln):
            fenced = not fenced
            continue
        if not fenced and HEAD.match(ln):
            out.append(ln.strip())
    return out


def kind(old, new):
    a, b = [int(x) for x in old.split(".")], [int(x) for x in new.split(".")]
    if b[0] > a[0]:
        return "major"
    if b[0] == a[0] and b[1] > a[1]:
        return "minor" + ("" if b[1] == a[1] + 1 and b[2] == 0 else "(non-single-step)")
    if b[:2] == a[:2] and b[2] > a[2]:
        return "patch" + ("" if b[2] == a[2] + 1 else f"(+{b[2] - a[2]})")
    return "other"


def main() -> int:
    primary, base, carrier, out = sys.argv[1:5]
    docs = sys.argv[5:]
    report = {}
    for doc in docs:
        old = git(primary, "show", f"{base}:{doc}")
        new = (pathlib.Path(carrier) / doc).read_text()
        vo, vn = versions(old), versions(new)
        ho, hn = headings(old), headings(new)
        added = [h for h in hn if h not in ho]
        removed = [h for h in ho if h not in hn]
        hist = []
        commits = git(primary, "log", "--format=%h", "-n", "40", base, "--", doc).split()
        for c in commits:
            after = git(primary, "show", f"{c}:{doc}")
            before = git(primary, "show", f"{c}^:{doc}")
            va, vb = versions(before), versions(after)
            if va and vb and va[0] != vb[0]:
                subj = git(primary, "log", "-1", "--format=%cs %s", c).strip()[:90]
                gained = [h for h in headings(after) if h not in headings(before)]
                hist.append({"commit": c, "subject": subj, "from": va[0], "to": vb[0], "kind": kind(va[0], vb[0]), "headings_added": len(gained)})
        report[doc] = {
            "main_versions": vo,
            "carrier_versions": vn,
            "header_footer_agree": len(set(vn)) == 1,
            "bump": kind(vo[0], vn[0]) if vo and vn else "n/a",
            "headings_added": added,
            "headings_removed": removed,
            "history": hist[:12],
        }
    pathlib.Path(out).write_text(json.dumps(report, indent=2))
    for doc, r in report.items():
        hist_kinds = [f"{h['kind']}:{h['headings_added']}h" for h in r["history"]]
        print(f"{doc}: main {r['main_versions']} -> carrier {r['carrier_versions']} agree={r['header_footer_agree']} bump={r['bump']} +headings={len(r['headings_added'])} -headings={len(r['headings_removed'])}")
        print(f"    history (newest first, kind:headings-added): {hist_kinds}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
