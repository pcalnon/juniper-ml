#!/usr/bin/env python3
"""Edit the parent Juniper/AGENTS.md RELEASED paragraph for juniper-cascor 0.14.0 and juniper-canopy 0.10.0 (R-OBS-SC-2).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one edit of the parent AGENTS.md, after both releases published (Overtoad ruling of 2026-11-15:
        "Edit it once both publish (Recommended)")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_parent_agents_released_paragraph_0_11_5.py (the previous edit, the pattern);
         util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py (the re-probe that runs first);
         util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py (the publish check, 0 failed);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.16 records the edit)

Why
---
The parent ``Juniper/AGENTS.md`` is unversioned: no PR, CI or history guards it, so an edit is a script with a backup, a
before-hash it refuses to edit without, and a recorded after-hash. On 2026-11-15 juniper-cascor 0.14.0 and
juniper-canopy 0.10.0 published, which makes four of its passages stale: the re-probe date, the cascor 0.13.0 bullet's
"juniper-deploy pins the 0.13.0 image", the observability bullet's "juniper-cascor's and juniper-canopy's next releases
raise theirs", and the absence of a bullet for the two releases. juniper-deploy#278 pins both images, so the script
refuses until that PR has merged.

Usage
-----
    python3 util/ad-hoc/2026-11-15_parent_agents_released_paragraph_cascor_0_14_0_canopy_0_10_0.py [--check]

Without ``--check`` it writes the backup under the juniper-ml primary's ``tmp/2026-11-15-parent-agents-md-backup/``,
then the edit, and prints both sha256. ``--check`` writes nothing and exits 1 while an edit is pending. Every anchor must
occur exactly once; otherwise, or when the file's sha256 is neither the expected before- nor after-state, it refuses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PARENT_NAME = "AGENTS.md"
BEFORE_SHA = "f3f69b34e33cfc8daaea05fb67297f2ed6793cb93607ce4b5ac6da4a3c473bfd"
BACKUP_DIR = "tmp/2026-11-15-parent-agents-md-backup"

_DATE_OLD = "**Last Updated**: 2026-11-14\n"
_DATE_NEW = "**Last Updated**: 2026-11-15\n"
_PROBE_OLD = "    **What has moved since (re-probed against PyPI on 2026-11-14 UTC):**\n"
_PROBE_NEW = "    **What has moved since (re-probed against PyPI on 2026-11-15 UTC):**\n"
_PIN_OLD = (
    "      2026-10-29). juniper-deploy pins the `0.13.0` image since juniper-deploy#266\n"
    "      (2026-10-30). The experiment stack launches the cascor primary's `src/` (for the\n"
)
_PIN_NEW = (
    "      2026-10-29). juniper-deploy pinned the `0.13.0` image from juniper-deploy#266\n"
    "      (2026-10-30) until juniper-deploy#278 (2026-11-15) moved it to 0.14.0 (below). The\n"
    "      experiment stack launches the cascor primary's `src/` (for the\n"
)
_FLOORS_OLD = (
    "      `Retry-After` up instead of truncating it. Of the published consumers, only juniper-ml\n"
    "      0.11.5's `[tools]` floors them (next bullet). juniper-data 0.17.1 (under `[api]`),\n"
    "      juniper-cascor 0.13.0, juniper-canopy 0.9.0 and juniper-recurrence 0.8.1 (its\n"
    "      observability floor under `[observability]`) floor 0.4.1 and 0.7.1. juniper-cascor's\n"
    "      and juniper-canopy's next releases raise theirs (Overtoad rulings of 2026-11-09 and\n"
    "      2026-11-13).\n"
)
_FLOORS_NEW = (
    "      `Retry-After` up instead of truncating it. Of the published consumers, juniper-cascor\n"
    "      0.14.0, juniper-canopy 0.10.0 and juniper-ml 0.11.5's `[tools]` floor them (the next\n"
    "      two bullets). juniper-data 0.17.1 (under `[api]`) and juniper-recurrence 0.8.1 (its\n"
    "      observability floor under `[observability]`) floor 0.4.1 and 0.7.1; their next\n"
    "      releases raise theirs (Overtoad ruling of 2026-11-09). juniper-cascor 0.13.0 and\n"
    "      juniper-canopy 0.9.0 floor 0.4.1 and 0.7.1 too.\n"
)
_META_ANCHOR = "    - **The meta-package: juniper-ml 0.11.5** (2026-11-14 00:16Z, publish run\n"
_RELEASES = (
    "    - **juniper-canopy 0.10.0** (PyPI 2026-11-15 05:17Z, publish run 43664277663; Release\n"
    "      `v0.10.0` 01:41Z) and **juniper-cascor 0.14.0** (05:24Z, publish run 43663237489;\n"
    "      Release `v0.14.0` 01:28Z), R-OBS-SC-2's consumer cuts, each held at its `pypi` gate\n"
    "      until then. Each floors `juniper-observability>=0.4.2` (canopy's `<0.5.0`) and\n"
    "      `juniper-service-core>=0.7.2,<0.8.0`, its image locks 0.4.2 and 0.7.2, and each\n"
    "      carries its own `Retry-After` round-up and FastAPI telemetry opt-out. canopy's PyPI\n"
    "      files are the ones TestPyPI took. cascor's are a second build of `bf6f0108`: every\n"
    "      file in them equals TestPyPI's, but the archives differ, because cascor's publish\n"
    "      run builds once per publish job (to be fixed: Overtoad ruling of 2026-11-15).\n"
    "      juniper-deploy pins both images since juniper-deploy#278 (2026-11-15).\n"
)
EDITS = (
    ("Last Updated", _DATE_OLD, _DATE_NEW),
    ("re-probe date", _PROBE_OLD, _PROBE_NEW),
    ("cascor 0.13.0's pin", _PIN_OLD, _PIN_NEW),
    ("the floors sentence", _FLOORS_OLD, _FLOORS_NEW),
    ("the two releases' bullet", _META_ANCHOR, _RELEASES + _META_ANCHOR),
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def primary_checkout() -> Path:
    out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=_REPO, capture_output=True, text=True, check=True)
    return Path(out.stdout.strip()).parent


def deploy_pin_merged() -> bool:
    out = subprocess.run(["gh", "pr", "view", "278", "--repo", "pcalnon/juniper-deploy", "--json", "state,mergedAt"], capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    print(f"juniper-deploy#278: {data['state']} (merged {data['mergedAt']})")
    return data["state"] == "MERGED"


def apply(text: str) -> tuple[str, list[str]]:
    """Apply each pending edit; an edit already in place is skipped, and an anchor not found exactly once refuses."""
    pending = []
    for label, old, new in EDITS:
        # The insertion keeps its anchor (``old`` is a suffix of ``new``), so it is done when the inserted text is there.
        done = (_RELEASES in text) if new.endswith(old) else (old not in text and text.count(new) == 1)
        if done:
            continue
        if text.count(old) != 1:
            raise SystemExit(f"refusing: anchor for {label!r} found {text.count(old)} times")
        text = text.replace(old, new)
        pending.append(label)
    return text, pending


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 while an edit is pending")
    args = ap.parse_args()
    parent = primary_checkout().parent / PARENT_NAME
    text = parent.read_text(encoding="utf-8")
    before = sha(text)
    edited, pending = apply(text)
    after = sha(edited)
    print(f"{parent}: sha256 {before}")
    if not pending:
        print("nothing pending: every edit is already in place")
        return 0
    if before != BEFORE_SHA:
        raise SystemExit(f"refusing: sha256 {before} is not the expected before-state {BEFORE_SHA} (edited since?)")
    print(f"pending: {pending}; sha256 after would be {after}")
    if args.check:
        return 1
    if not deploy_pin_merged():
        raise SystemExit("refusing: juniper-deploy#278 has not merged, and the edit cites its pin")
    backup = primary_checkout() / BACKUP_DIR
    backup.mkdir(parents=True, exist_ok=True)
    (backup / "AGENTS.md.before-cascor-0-14-0-canopy-0-10-0-edit").write_text(text, encoding="utf-8")
    parent.write_text(edited, encoding="utf-8")
    (backup / "AGENTS.md.after-cascor-0-14-0-canopy-0-10-0-edit").write_text(edited, encoding="utf-8")
    print(f"wrote {parent}: sha256 {before} -> {after}; backup in {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
