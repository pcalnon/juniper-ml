#!/usr/bin/env python3
"""Print the text around each mention of the given worktree names (flood-4 session 12, ruling 7's inventory).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s12_r7_scan.py (writes mentions.tsv),
    util/ad-hoc/2026-11-24_flood4_s12_r7_mentions_index.py (the classes used by --classes)

For each NAME (a worktree name, or an agent's bare id), every mention in <dir>/mentions.tsv whose file is in one of
--classes is printed as ``name  file:line | <text around it>``, at most --max per name. Reading the context is how a
mention is judged: a log line can name a peer's worktree to disown it.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_context.py --dir tmp/flood4/session12/r7 [--classes state,brief,...] \
        [--max N] [--width N] NAME [NAME ...]
It only reads.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_classify():
    here = Path(__file__).with_name("2026-11-24_flood4_s12_r7_mentions_index.py")
    spec = importlib.util.spec_from_file_location("r7_mentions_index", here)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.classify


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--classes", default="handoff-flood4,handoff-1106,record,state,brief")
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--width", type=int, default=170)
    ap.add_argument("names", nargs="+")
    a = ap.parse_args()
    classify = _load_classify()
    classes = set(a.classes.split(","))
    want = {}
    for n in a.names:
        bare = n[len("agent-"):] if n.startswith("agent-") else n
        want[n] = want[bare] = n
        want["agent-" + bare] = n
    shown: dict[str, int] = {}
    cache: dict[str, list[str]] = {}
    with (a.dir / "mentions.tsv").open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            name, path, ln = line.rstrip("\n").split("\t")
            key = want.get(name)
            if key is None or shown.get(key, 0) >= a.max:
                continue
            cls = classify(path)
            if cls not in classes and "all" not in classes:
                continue
            if path not in cache:
                try:
                    cache[path] = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    cache[path] = []
            lines = cache[path]
            text = lines[int(ln) - 1] if 0 < int(ln) <= len(lines) else ""
            i = max(text.find(name), 0)
            lo = max(0, i - a.width)
            parts = Path(path).parts
            short = "/".join(parts[parts.index("tmp") + 1:]) if "tmp" in parts else path.rsplit("/", 1)[-1]
            print(f"{key}  [{cls}] {short}:{ln} | {text[lo:i + 60].strip()}")
            shown[key] = shown.get(key, 0) + 1
    for n in a.names:
        if n not in shown:
            print(f"{n}  (no mention in classes {sorted(classes)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
