"""
Three-way merge each pair of round-2 juniper-data carriers (both orders) and the landing order, per shared file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (claims and docs lens), juniper-data data-docs / data-tests / data-code

Read-only on the carriers: reads their working-tree files and `git show <base>:<path>`; merges run on copies in
<out_dir> with `git merge-file` (no repository is touched).
Usage: python3 util/ad-hoc/2026-11-08_flood4r2_val_data-claims_merge_matrix.py <out_dir>
"""

from __future__ import annotations

import itertools
import subprocess
import sys
from pathlib import Path

BASE = "4f04fc8d0ba713fd1d3fced899488d3fad6d5f74"
WT = Path.home() / "Development" / "python" / "Juniper" / "worktrees"
CARRIERS = {
    "data-tests": WT / "juniper-data--test--flood4r2-consolidated-tests--20261108-1831--4f04fc8d",
    "data-docs": WT / "juniper-data--docs--flood4r2-consolidated-docs--20261108-1831--4f04fc8d",
    "data-code": WT / "juniper-data--fix--flood4r2-retry-after-round-up--20261108-1831--4f04fc8d",
}
FILES = ["CHANGELOG.md", "docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET.md"]
LANDING = ["data-tests", "data-docs", "data-code"]


def base_text(path: str) -> str:
    proc = subprocess.run(["git", "-C", str(CARRIERS["data-docs"]), "show", f"{BASE}:{path}"], capture_output=True, text=True, check=True)
    return proc.stdout


def merge(ours: str, base: str, theirs: str, work: Path, tag: str) -> tuple[int, str]:
    a, o, b = work / f"{tag}.ours", work / f"{tag}.base", work / f"{tag}.theirs"
    a.write_text(ours, encoding="utf-8")
    o.write_text(base, encoding="utf-8")
    b.write_text(theirs, encoding="utf-8")
    proc = subprocess.run(["git", "merge-file", "-p", str(a), str(o), str(b)], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for path in FILES:
        base = base_text(path)
        texts = {name: (wt / path).read_text(encoding="utf-8") for name, wt in CARRIERS.items()}
        changed = [n for n in texts if texts[n] != base]
        print(f"== {path}: changed by {changed}")
        for x, y in itertools.permutations(changed, 2):
            rc, merged = merge(texts[x], base, texts[y], out, f"{Path(path).name}.{x}+{y}")
            print(f"   {x} then {y}: conflicts={rc}")
            if rc:
                hunks = merged.count("<<<<<<< ")
                (out / f"{Path(path).name}.{x}+{y}.merged").write_text(merged, encoding="utf-8")
                print(f"      conflict blocks: {hunks}")
        # landing order: each later carrier merged onto the result so far (same base for its own diff)
        acc, acc_rc = base, 0
        for name in LANDING:
            if name not in changed:
                continue
            rc, acc = merge(acc, base, texts[name], out, f"{Path(path).name}.landing.{name}")
            acc_rc += rc
            print(f"   landing +{name}: conflicts={rc}")
        (out / f"{Path(path).name}.landing.result").write_text(acc, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
