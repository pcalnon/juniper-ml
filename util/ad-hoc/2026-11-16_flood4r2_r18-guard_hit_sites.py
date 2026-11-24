#!/usr/bin/env python3
"""
Count, by the guard functions that made it, every hit a newer agent guard adds over an older one on real commands.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_r18-guard_census_explain.py (its transcript reader is reused).

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_hit_sites.py <transcripts dir> <max files> <out.json>
        <older guard.py> <newer guard.py>

For each Bash command the older guard passes and the newer one denies, the newer guard is run again with its
``BashAnalyzer.hit`` wrapped to record the guard functions on the stack when each hit is made (function names only),
the analyzer's reading (``_mode``) and whether the command names dotglob or GLOBIGNORE. AGGREGATES ONLY: counts of
(rule, reading, call chain); no command text and no evidence is written.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list) -> int:
    explain = load(HERE / "2026-11-16_flood4r2_r18-guard_census_explain.py", "census_explain")
    root = Path(argv[1]).expanduser()
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[: int(argv[2])]
    every = [command for path in files for command in explain.commands(path)]
    older = load(argv[4], "guard_older_sites")
    newer = load(argv[5], "guard_newer_sites")
    chains = collections.Counter()
    commands_changed = 0
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (home / name).mkdir(parents=True)
        ctx_old = older.Context([str(home)], tmp)
        ctx_new = newer.Context([str(home)], tmp)
        for command in every:
            if explain.outcome(older, ctx_old, command) != "ok" or explain.outcome(newer, ctx_new, command) == "ok":
                continue
            commands_changed += 1
            analyzer = newer.BashAnalyzer(ctx_new)
            original = analyzer.hit
            dotglob = bool(newer._DOTGLOB_RE.search(command)) if hasattr(newer, "_DOTGLOB_RE") else False

            def hit(rule_id, evidence, _original=original, _analyzer=analyzer, _dotglob=dotglob):
                names = [frame.name for frame in traceback.extract_stack()[:-1] if frame.filename.endswith(Path(argv[5]).name)]
                chains[(rule_id, _analyzer._mode, _dotglob, " > ".join(names[-4:]))] += 1
                _original(rule_id, evidence)

            analyzer.hit = hit
            try:
                analyzer.analyze(command)
            except newer.MalformedInput:
                chains[("refused", analyzer._mode, dotglob, "")] += 1
    rows = [{"rule": r, "reading": m, "names_dotglob": d, "chain": c, "hits": n} for (r, m, d, c), n in chains.most_common()]
    Path(argv[3]).write_text(json.dumps({"commands_changed": commands_changed, "chains": rows}, indent=1) + "\n", encoding="utf-8")
    print("commands changed: %d" % commands_changed)
    for row in rows[:25]:
        print("%6d  %-20s %s dotglob=%s  %s" % (row["hits"], row["rule"], row["reading"], row["names_dotglob"], row["chain"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
