#!/usr/bin/env python3
"""Index the scan's worktree mentions by the kind of file they occur in (flood-4 session 12, ruling 7's inventory).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s12_r7_scan.py (writes mentions.tsv); tmp/flood4/session12/briefs/R7_inventory.txt

A mention is evidence of different strength depending on where it sits:
  handoff-flood4  an archived flood-4 handoff on main (HANDOFF_2026-11-*_flood4*)
  handoff-1106    the 11-06 handoff that names "the five" (HANDOFF_2026-11-06_open-pr-sweep-*)
  handoff-other   any other archived handoff (another arc's, so it argues AGAINST the worktree being flood-4's)
  record          the disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)
  state           a running log: STATE*.txt or OPEN_ITEMS.txt
  brief           an agent brief: BRIEF*.txt or a file under briefs/
  copy            a file inside a copied repository tree (a path holding /prompts/, /notes/, /clones/, /src/, /docs/ ...)
  work            any other file in the arc's tmp trees (agents' reports, findings, logs, manifests)
Bare agent ids (a + 16 hex) are folded into their worktree name (agent-<id>).

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_mentions_index.py --dir tmp/flood4/session12/r7
Reads <dir>/mentions.tsv and <dir>/scan_worktrees.json; writes <dir>/mentions_index.json and <dir>/mentions_index.tsv.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AGENT_BARE = re.compile(r"a[0-9a-f]{16}")
COPY_MARKERS = ("/prompts/", "/notes/", "/clones/", "/src/", "/docs/", "/juniper_data/", "/juniper-service-core/", "/tests/", "/.github/", "/util/", "/reports/")


def tmp_tail(path: str) -> str | None:
    """The part of PATH after its first ``tmp`` component, or None when no component is ``tmp`` (relative or absolute)."""
    parts = Path(path).parts
    if "tmp" not in parts:
        return None
    return "/".join(parts[parts.index("tmp") + 1:])


def classify(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    tail = tmp_tail(path)
    if tail is None:
        # a file on main in the orchestrator worktree (the corpus passes these as relative paths)
        if "prompts/thread-handoff_automated-prompts/" in path:
            if base.startswith("HANDOFF_2026-11-") and "_flood4" in base:
                return "handoff-flood4"
            if base.startswith("HANDOFF_2026-11-06_open-pr-sweep"):
                return "handoff-1106"
            return "handoff-other"
        if path.endswith("notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md"):
            return "record"
        return "work"
    # inside a tmp tree from here on
    if base.startswith("STATE") or base == "OPEN_ITEMS.txt":
        return "state"
    if base.startswith("BRIEF") or "/briefs/" in "/" + tail:
        return "brief"
    if any(m in "/" + tail for m in COPY_MARKERS):
        return "copy"
    return "work"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dir", required=True, type=Path)
    a = ap.parse_args()
    names = {w["name"] for w in json.loads((a.dir / "scan_worktrees.json").read_text(encoding="utf-8"))}
    index: dict[str, dict] = {}
    with (a.dir / "mentions.tsv").open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            name, path, ln = line.rstrip("\n").split("\t")
            if AGENT_BARE.fullmatch(name):
                name = "agent-" + name
            if name not in names:
                continue
            cls = classify(path)
            ent = index.setdefault(name, {"counts": {}, "first": {}, "files": set()})
            ent["counts"][cls] = ent["counts"].get(cls, 0) + 1
            ent["files"].add(path)
            key = f"{path}:{ln}"
            if cls not in ent["first"] or key < ent["first"][cls]:
                ent["first"][cls] = key
    out = {n: {"counts": e["counts"], "first": e["first"], "n_files": len(e["files"])} for n, e in sorted(index.items())}
    (a.dir / "mentions_index.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    classes = ["handoff-flood4", "handoff-1106", "record", "state", "brief", "work", "copy", "handoff-other"]
    with (a.dir / "mentions_index.tsv").open("w", encoding="utf-8") as fh:
        fh.write("name\t" + "\t".join(classes) + "\tfirst_strongest\n")
        for n, e in out.items():
            strongest = next((e["first"][c] for c in classes if c in e["first"]), "")
            fh.write(n + "\t" + "\t".join(str(e["counts"].get(c, 0)) for c in classes) + f"\t{strongest}\n")
    print(f"{len(out)} of {len(names)} entries are mentioned somewhere in the corpus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
