"""
Build full src/ copies of n3's mutants (from the scratch cascor worktree) for the probe and sweep runs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_val_n3-code_mutants.py
"""

import importlib.util
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("n3_mutants", HERE / "2026-11-09_flood4r2_val_n3-code_mutants.py")
mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mut)

DEST = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/tmp/flood4r2-val/n3-code-lens/mutant-trees")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    for m in mut.MUTANTS:
        tree = DEST / m["name"].split("-")[0]
        if tree.exists():
            shutil.rmtree(tree)
        shutil.copytree(mut.WT / "src", tree / "src", ignore=shutil.ignore_patterns("__pycache__", "tests"))
        for rel, old, new in m["edits"]:
            p = tree / rel
            text = p.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{m['name']}: edit matched {text.count(old)} times")
            p.write_text(text.replace(old, new), encoding="utf-8")
        print(tree / "src")
    return 0


if __name__ == "__main__":
    sys.exit(main())
