#!/usr/bin/env python3
"""
Apply a claims validator's exact (file, old, new) replacements to the juniper-data gitleaks fix, refusing any non-unique old string.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (round 2 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
A validator handed back replacements as exact strings. Applying them by hand risks a silent partial edit; this
applies them in the order given, and refuses the whole batch unless every old string occurs EXACTLY ONCE in its
target at the moment it is applied (so an earlier replacement cannot shadow a later one). A target under
tmp/flood4-fix/m1/ (the author's PR and commit bodies) is redirected to the round-2 copy under --r2, which is
seeded from the author's file on first use. Writes nothing without --apply; always writes a JSON log.

Usage:
    python3 <this> --findings <val-b/findings.json> --worktree <juniper-data worktree> --r2 <r2 dir> [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REDIRECT_PREFIX = "tmp/flood4-fix/m1/"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--findings", type=Path, required=True)
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--r2", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    with open(args.findings, encoding="utf-8") as fh:
        findings = json.load(fh)["findings"]

    def target(rel: str) -> Path:
        if rel.startswith(REDIRECT_PREFIX):
            dest = args.r2 / rel[len(REDIRECT_PREFIX) :]
            if not dest.exists():
                shutil.copyfile(args.worktree / rel, dest)
            return dest
        return args.worktree / rel

    texts: dict[Path, str] = {}
    before: dict[Path, str] = {}
    log: list[dict] = []
    failures = 0
    for finding in findings:
        for i, rep in enumerate(finding.get("replacements", []), start=1):
            path = target(rep["file"])
            if path not in texts:
                with open(path, encoding="utf-8") as fh:
                    texts[path] = fh.read()
                before[path] = sha256(texts[path])
            count = texts[path].count(rep["old"])
            entry = {"finding": finding["id"], "n": i, "file": rep["file"], "applied_to": str(path), "old_occurrences": count}
            if count == 1:
                texts[path] = texts[path].replace(rep["old"], rep["new"], 1)
                entry["new_occurrences_after"] = texts[path].count(rep["new"])
                entry["status"] = "ok"
            else:
                entry["status"] = "REFUSED"
                failures += 1
            log.append(entry)
            print(f"{entry['status']:<8} {finding['id']:<4} #{i} {rep['file']} (old occurs {count})")

    changed = [{"file": str(p), "sha256_before": before[p], "sha256_after": sha256(t)} for p, t in texts.items()]
    out = {"applied": bool(args.apply and not failures), "failures": failures, "replacements": log, "files": changed}
    if args.apply and not failures:
        for path, text in texts.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
    args.r2.joinpath("logs").mkdir(parents=True, exist_ok=True)
    name = "valb_replacements_apply.json" if args.apply else "valb_replacements_check.json"
    with open(args.r2 / "logs" / name, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(f"{len(log)} replacement(s), {failures} refused; {'written' if out['applied'] else 'nothing written'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
