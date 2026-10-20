#!/usr/bin/env python3
"""Rebuild Phase 14's shared files from fresh ``origin/main`` copies for the API landing, and verify the replay.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- Phase 14 landing from turing
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- one-off landing helper; RETAINED as provenance (owner policy 2026-08-25)
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      util/ad-hoc/2026-10-20_phase14_item30_apply.py, util/ad-hoc/2026-10-20_phase14_ledger_round*_corrections.py;
              util/open_signed_pr.py; util/ad-hoc/2026-10-17_push_signed_with_retry.py
License:      MIT License

WHY. Shared files (the ledger, the matrix, the parent handoff, the INDEX, the Phase 13 handoff) land from turing as
whole-file uploads, and a copy built from a stale base reverts whatever concurrent sessions merged in between (the
#2262 incident). So each is rebuilt here from ``git show origin/main:<path>`` after a fetch, by replaying the same
passes that produced the worktree's copy, in order, and then compared byte for byte with the worktree. A difference
means a hand edit the passes do not carry, which must be moved into a pass before landing.

Usage:
    git fetch origin
    python3 -I util/ad-hoc/2026-10-20_phase14_rebuild_shared_files_for_landing.py --out-root <dir> [--pass SCRIPT ...]
Prints the ``--add LOCAL:REPO`` arguments for the five shared files on success.
"""

from __future__ import annotations

import argparse
import filecmp
import subprocess  # noqa: S404 -- git show / the pass scripts, literal arguments
import sys
from pathlib import Path

SHARED = [
    "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md",
    "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md",
]
NEW_FROM_PASSES = [
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md",
]
DEFAULT_PASSES = [
    "util/ad-hoc/2026-10-20_phase14_item30_apply.py",
    "util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--pass", dest="passes", action="append", default=None, help="pass scripts in order (default: apply, round 1)")
    ap.add_argument("--ref", default="origin/main")
    args = ap.parse_args()
    passes = args.passes or DEFAULT_PASSES
    repo = Path(__file__).resolve().parents[2]
    out = Path(args.out_root).resolve()
    head = subprocess.run(["git", "rev-parse", args.ref], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()  # noqa: S603, S607
    print(f"base {args.ref} = {head}")
    for rel in SHARED:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(["git", "show", f"{args.ref}:{rel}"], cwd=repo, capture_output=True, check=True).stdout  # noqa: S603, S607
        dst.write_bytes(blob)
        print(f"  fetched {rel} ({len(blob)} bytes)")
    for p in passes:
        r = subprocess.run([sys.executable, "-I", str(repo / p), "--root", str(out)], capture_output=True, text=True, check=False)  # noqa: S603
        print(f"  pass {p}: rc={r.returncode} {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''} {r.stderr.strip()[-300:]}")
        if r.returncode != 0:
            return 1
    ok = True
    for rel in SHARED + NEW_FROM_PASSES:
        same = filecmp.cmp(out / rel, repo / rel, shallow=False)
        ok &= same
        print(f"  {'SAME    ' if same else 'DIFFERS '} {rel}")
    if not ok:
        print("NOT byte-identical to the worktree: move the hand edit into a pass before landing")
        return 1
    print("ALL SAME; --add arguments for the shared files:")
    for rel in SHARED + NEW_FROM_PASSES:
        print(f"  --add {out / rel}:{rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
