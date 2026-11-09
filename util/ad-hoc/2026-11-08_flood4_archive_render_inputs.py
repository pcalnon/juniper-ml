#!/usr/bin/env python3
"""
Archive the flood-4 record's sec 5 render inputs (the six carriers' manifests) under reports/, so sec 5 stays
reproducible after this arc's agent worktrees are removed.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (sec 5);
         util/ad-hoc/2026-11-07_flood4_disposition_render.py (the renderer);
         util/ad-hoc/2026-10-08_fleet_flood3_disposition.json (flood 3 versioned its verdicts the same way)

WHY THIS EXISTS
The renderer reads each builder's manifest from that builder's worktree tmp/, and `git worktree remove`
deletes a worktree's tmp/. The rendered table also truncates each evaluation at 420 characters, so the
manifests hold more than the record does. This copies each manifest byte for byte into reports/ and writes a
render config whose manifest paths are repo-relative, so the renderer run from the repository root re-renders
sec 5 from versioned files.

Usage (from the repository root):
  2026-11-08_flood4_archive_render_inputs.py --config <tmp render config> --dest reports/2026-11-08_flood4-disposition
"""

import argparse
import hashlib
import json
import os
import shutil
import sys


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as fh:
        src = json.load(fh)
    os.makedirs(a.dest, exist_ok=True)
    out = {"carriers": [], "extra": src.get("extra", [])}
    for c in src["carriers"]:
        name = "manifest_%s_%s.json" % (c["repo"], c["kind"])
        target = os.path.join(a.dest, name)
        shutil.copyfile(c["manifest"], target)
        if sha256(target) != sha256(c["manifest"]):
            raise SystemExit("REFUSING: copy of %s differs from its source" % c["manifest"])
        out["carriers"].append({"repo": c["repo"], "kind": c["kind"], "pr": c["pr"], "manifest": "%s/%s" % (a.dest.rstrip("/"), name)})
        print("%s  %s" % (sha256(target)[:12], target))
    cfg = os.path.join(a.dest, "render_config.json")
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("wrote %s (%d carriers, %d extra rows)" % (cfg, len(out["carriers"]), len(out["extra"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
