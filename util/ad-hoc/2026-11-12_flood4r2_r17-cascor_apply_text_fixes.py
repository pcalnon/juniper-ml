#!/usr/bin/env python3
"""
Apply a validator's exact old -> new text fixes to a carrier and its deliverables, each by its exact old string, and log every one.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/r17-cascor-claims-lens-s5/text_fixes.json (19 fixes; "COPY/<path>" is a
         repository file, "DELIVERABLES/<name>" a file of the carrier's deliverables directory);
         tmp/flood4/session6/briefs/B_r17_cascor_round2_finish.txt step 3 (apply each by its exact
         old string and report any that no longer occurs; never guess a replacement)

For every fix in the JSON file, in order (numbered from 1), this reports how often its ``old`` and
its ``new`` string occur in the file it names. With ``--apply N [N ...]`` it replaces ``old`` by
``new`` for those numbers only, and only where ``old`` occurs exactly once; any other count is
reported and left alone. A fix that is not named in ``--apply`` is never applied: the caller
states in ``--skip N=<reason>`` why each one it leaves out is left out, and the reason is logged
beside the counts. Nothing is ever guessed: the only strings written are the JSON file's own.

Usage:
  2026-11-12_flood4r2_r17-cascor_apply_text_fixes.py --fixes <text_fixes.json> --copy <carrier root> --deliverables <dir>
      [--apply N ...] [--skip N=<reason> ...] [--out <json log>]
Exit: 0 when every fix named in --apply was applied; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--fixes", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path, help="the carrier checkout (COPY/...)")
    parser.add_argument("--deliverables", required=True, type=Path, help="the deliverables directory (DELIVERABLES/...)")
    parser.add_argument("--apply", type=int, nargs="*", default=[], help="1-based numbers of the fixes to apply")
    parser.add_argument("--skip", action="append", default=[], help="N=<reason>: why fix N is not applied as written")
    parser.add_argument("--out", type=Path, help="write the per-fix log here as JSON")
    args = parser.parse_args()

    roots = {"COPY": args.copy.resolve(), "DELIVERABLES": args.deliverables.resolve()}
    reasons = {}
    for item in args.skip:
        number, _, reason = item.partition("=")
        reasons[int(number)] = reason
    fixes = json.loads(args.fixes.read_text(encoding="utf-8"))
    wanted = set(args.apply)
    log = []
    failed = []
    for number, fix in enumerate(fixes, start=1):
        kind, _, relative = fix["file"].partition("/")
        path = roots[kind] / relative
        text = path.read_text(encoding="utf-8")
        entry = {"number": number, "finding": fix["finding"], "file": fix["file"], "old_count_before": text.count(fix["old"]), "new_count_before": text.count(fix["new"])}
        if number in wanted:
            if entry["old_count_before"] == 1:
                path.write_text(text.replace(fix["old"], fix["new"]), encoding="utf-8")
                entry["action"] = "applied: old replaced by new, exactly as written"
            else:
                entry["action"] = f"NOT applied: old occurs {entry['old_count_before']} times, expected 1"
                failed.append(number)
        elif number in reasons:
            entry["action"] = "not applied as written: " + reasons[number]
        elif entry["old_count_before"] == 0 and entry["new_count_before"] == 1:
            entry["action"] = "already in place: new occurs once and old does not occur"
        else:
            entry["action"] = "left alone (not named in --apply, no reason given)"
        after = path.read_text(encoding="utf-8")
        entry["old_count_after"] = after.count(fix["old"])
        entry["new_count_after"] = after.count(fix["new"])
        log.append(entry)
        print(f"{number:2} {fix['finding']:4} {fix['file']:68} old x{entry['old_count_before']}->x{entry['old_count_after']}  new x{entry['new_count_before']}->x{entry['new_count_after']}  {entry['action']}")
    if args.out:
        args.out.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    if failed:
        print(f"FAIL: fixes {failed} were named in --apply and could not be applied")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
