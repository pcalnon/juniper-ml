"""
Apply each flood-4 juniper-ml test draft's OWN hunks (merge-base..head) onto the worktree with a 3-way apply.

Never copies a draft's whole file: each `<scratch>/patches/pr<N>.patch` (written by
2026-11-07_flood4_ml_tests_survey.py, `git diff --binary --full-index <merge-base> <head>`) is applied
in order with `git apply --3way`, so a shared file (ci.yml, docs/REFERENCE.md, a test module several
drafts extend) keeps everything main gained since the draft's base. Per-draft `--exclude` paths keep
hunks the carrier re-derives itself (see EXCLUDES). Stops at the first draft that does not apply, so
the tree is never left half-merged without a record. Writes `<scratch>/apply.json`.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_apply.py <scratch-dir> [N ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md (flood-4 consolidation)
"""

import json
import subprocess
import sys
from pathlib import Path

# Merge-plan order from the 2026-11-06 triage: wave 1, the ci.yml group, then the fix-first drafts.
ORDER = [2466, 2419, 2427, 2430, 2436, 2439, 2441, 2443, 2445, 2447, 2451, 2458, 2461, 2463, 2425, 2413, 2414, 2416, 2429, 2431, 2434, 2421, 2448, 2459, 2410, 2455, 2403, 2407]

# #2466's second REFERENCE.md hunk rewrites the util/claude_agent_guard.py bullet's prose (behaviour
# documentation, the docs carrier's lane); the carrier re-derives that suite's registrations instead.
EXCLUDES = {2466: ["docs/REFERENCE.md"]}


def main() -> int:
    scratch = Path(sys.argv[1]).resolve()
    order = [int(a) for a in sys.argv[2:]] or ORDER
    results = []
    rc_all = 0
    for n in order:
        patch = scratch / "patches" / f"pr{n}.patch"
        argv = ["git", "apply", "--3way", "--whitespace=nowarn"]
        argv += [f"--exclude={p}" for p in EXCLUDES.get(n, [])]
        argv.append(str(patch))
        proc = subprocess.run(argv, capture_output=True, text=True, check=False)
        out = (proc.stdout + proc.stderr).strip()
        results.append({"pr": n, "argv": argv, "rc": proc.returncode, "output": out})
        print(f"#{n} rc={proc.returncode} excludes={EXCLUDES.get(n, [])}")
        if out:
            print("    " + out.replace("\n", "\n    "))
        if proc.returncode != 0:
            rc_all = 1
            break
    with open(scratch / "apply.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
