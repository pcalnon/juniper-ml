#!/usr/bin/env python3
"""Print the validator's simulation logs (2026-11-08_flood4r2_val_ml-propose_simulate.py) as a readable report.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; the ml-propose carrier

Reads ``<out>/sim/<scenario>/<variant>/log.json`` and prints, per step: the gate's failing tests, each proposal's
edit paths, its docs/REFERENCE.md checklist lines and changed REFERENCE lines (trimmed), then the module suites.
Read-only; prints to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenario", action="append", default=[])
    ap.add_argument("--variant", action="append", default=[])
    ap.add_argument("--width", type=int, default=260)
    args = ap.parse_args(argv)
    root = Path(args.out) / "sim"
    for scen in sorted(p.name for p in root.iterdir()):
        if args.scenario and scen not in args.scenario:
            continue
        for variant in ("main", "carrier"):
            if args.variant and variant not in args.variant:
                continue
            log_path = root / scen / variant / "log.json"
            if not log_path.exists():
                continue
            with open(log_path, encoding="utf-8") as fh:
                log = json.load(fh)
            print(f"##### {scen} / {variant}")
            for rec in log:
                if "modules" in rec:
                    for suite, m in rec["modules"].items():
                        print(f"  module {suite}: rc={m['rc']} {m['summary']} failing={[f.split(' ')[0] for f in m['failing']]}")
                    continue
                failing = {k: v for k, v in (rec.get("gate") or {}).items() if v != "ok"}
                print(f"  STEP {rec['step']}")
                if "edit_paths" in rec:
                    print(f"    skipped={rec['skipped_reason']} edits={rec['edit_paths']} dup={rec['duplicate_paths']} body_lists_ref={rec['pr_body_lists_reference']}")
                    for item in rec["reference_checklist"]:
                        print(f"    CL: {item[: args.width * 2]}")
                    for ln in rec["reference_changed_lines"]:
                        print(f"    REF {ln[: args.width]}")
                for k, v in failing.items():
                    print(f"    GATE {k}: {v[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
