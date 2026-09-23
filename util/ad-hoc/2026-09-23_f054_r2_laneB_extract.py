#!/usr/bin/env python
"""Extract canopy#670's v1 / v1-merged / v2 files from git OBJECTS into a scratch tree, and diff them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 round-2 review (Lane B); util/ad-hoc/2026-09-23_f054_r2_laneB_gitobj.py

Builds: c0530279 (v1 as opened), 723ee812 (v1 merged with main 0fca86e9, local), 85415f3c (v2, local
freeze). Also materialises the WHOLE v2 ``src/`` tree (for building the app and running its tests on a
copy), never touching the fix worktree's working tree.

Usage:
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_extract.py --objects <canopy .git/objects> --dest <scratch dir>
"""

import argparse
import difflib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gitobj", HERE / "2026-09-23_f054_r2_laneB_gitobj.py")
gitobj = importlib.util.module_from_spec(spec)
sys.modules["gitobj"] = gitobj
spec.loader.exec_module(gitobj)

BUILDS = {"v1": "c0530279", "v1m": "723ee812", "v2": "85415f3c"}
FILES = [
    "CHANGELOG.md",
    "src/frontend/components/metrics_panel.py",
    "src/tests/regression/snapshots/metrics_panel.txt",
    "src/tests/unit/frontend/test_f048_replay_cycle.py",
    "src/tests/unit/frontend/test_f054_replay_block_clientside.py",
    "docs/testing/TESTING_MANUAL.md",
    "docs/testing/TESTING_REFERENCE.md",
    "docs/cascor/CASCOR_BACKEND_MANUAL.md",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", required=True)
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    st = gitobj.Store(a.objects)
    dest = Path(a.dest)
    for name, ref in BUILDS.items():
        for f in FILES:
            try:
                sha, body = st.blob_at(st.resolve(ref), f)
            except KeyError as e:
                print(f"{name}:{f} MISSING ({e})")
                continue
            out = dest / name / f
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
    # whole v2 src/ tree, plus the root files pytest may need
    flat = st.flat(st.commit(st.resolve(BUILDS["v2"]))["tree"])
    n = 0
    for path, sha in flat.items():
        if path.startswith("src/") or path in ("pyproject.toml", "pytest.ini", "setup.cfg") or path.startswith("conf/"):
            kind, body = st.read(sha)
            if kind != "blob":
                continue
            out = dest / "v2tree" / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            n += 1
    print(f"v2 tree: {n} files -> {dest / 'v2tree'}")
    for f in FILES:
        a_, b_ = dest / "v1m" / f, dest / "v2" / f
        if a_.exists() and b_.exists():
            d = list(difflib.unified_diff(a_.read_text(encoding="utf-8").splitlines(), b_.read_text(encoding="utf-8").splitlines(), f"723ee812/{f}", f"85415f3c/{f}", lineterm="", n=3))
            (dest / "diffs").mkdir(exist_ok=True)
            (dest / "diffs" / (f.replace("/", "__") + ".diff")).write_text("\n".join(d) + "\n", encoding="utf-8")
            print(f"{f}: {sum(1 for x in d if x.startswith('+') and not x.startswith('+++'))} added, {sum(1 for x in d if x.startswith('-') and not x.startswith('---'))} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
