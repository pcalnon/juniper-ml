#!/usr/bin/env python3
"""
Re-probe the latest PyPI release of every package the parent ``Juniper/AGENTS.md`` RELEASED paragraph names.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (one edit of the parent AGENTS.md, after juniper-ml 0.11.4's publish)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.14);
         util/ad-hoc/2026-10-05_ecosystem_live_census.py (reads each package's latest version, but not the recurrence pair)

Why this exists
---------------
The parent ``Juniper/AGENTS.md`` (unversioned) says under "What has moved since (re-probed against PyPI on <date>)"
which release of each package is the newest. Its date may only move when every package it names has been re-read,
so this reads them all: for each, the newest release (by PyPI's ordering of the ``releases`` keys, which is
PEP 440 order, ignoring pre-releases and yanked files) and when its first file was uploaded. The aggregate endpoint
can lag a new publish, so a version the caller names with ``--expect PKG=VERSION`` is also read from its version
endpoint, and a mismatch is reported rather than trusted either way.

Read-only: the PyPI JSON API. Exit status: 0 when every read succeeds and every ``--expect`` holds, 1 when an
``--expect`` does not hold, 2 when a read fails (a failed read is never reported as "no release").

    python3 -I util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py --expect juniper-ml=0.11.4 --expect juniper-recurrence=0.8.1
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request

# The packages the RELEASED paragraph names, plus juniper-model-core, whose floor juniper-recurrence 0.8.1 moved.
PACKAGES = ["juniper-data", "juniper-data-client", "juniper-recurrence-model", "juniper-recurrence", "juniper-recurrence-client", "juniper-canopy", "juniper-cascor", "juniper-ml", "juniper-model-core", "juniper-observability", "juniper-service-core"]
_PRE = re.compile(r"(a|b|rc|dev)\d*", re.IGNORECASE)


def read_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 - fixed https PyPI URLs
        return json.load(resp)


def key(version: str) -> tuple:
    return tuple(int(part) for part in re.findall(r"\d+", version.split("+")[0])[:3])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect", action="append", default=[], metavar="PKG=VERSION", help="assert PKG's newest final release is VERSION")
    args = ap.parse_args()
    expects = dict(item.split("=", 1) for item in args.expect)
    unreadable = mismatched = 0
    for package in PACKAGES:
        try:
            meta = read_json(f"https://pypi.org/pypi/{package}/json")
        except Exception as exc:  # noqa: BLE001 - a failed read must be reported, never read as "none"
            print(f"UNREADABLE {package}: {exc}")
            unreadable += 1
            continue
        finals = {v: files for v, files in meta["releases"].items() if files and not _PRE.search(v) and not all(f.get("yanked") for f in files)}
        newest = max(finals, key=key) if finals else None
        uploaded = min(f["upload_time_iso_8601"] for f in finals[newest]) if newest else "-"
        line = f"{package:28} newest {newest} (first file {uploaded}); aggregate info.version {meta['info']['version']}"
        if package in expects:
            want = expects[package]
            try:
                served = read_json(f"https://pypi.org/pypi/{package}/{want}/json")["info"]["version"]
            except Exception as exc:  # noqa: BLE001 - see above
                print(f"UNREADABLE {package} {want}: {exc}")
                unreadable += 1
                continue
            ok = newest == want and served == want
            mismatched += 0 if ok else 1
            line += f"; expect {want}: {'OK' if ok else 'DIFFERS'} (version endpoint serves {served})"
        print(line)
    if unreadable:
        return 2
    return 1 if mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
