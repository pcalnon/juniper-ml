"""
Run the pinned pre-commit (and optionally one hook) on an explicit path list, and report any file it rewrote.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier, round-2 validation (corrections and their blast radius)

Usage (from the validator's own worktree root):
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_precommit.py PRE_COMMIT PATHS_FILE OUT.log [HOOK_ID]

PATHS_FILE holds one repo-relative path per line. sha256 of every path is taken before and after;
a changed hash means a hook rewrote the file (the carrier would not be hook-clean).
"""

from __future__ import annotations

import hashlib
import subprocess  # nosec B404 -- fixed argv
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "-"


def main(argv: list[str]) -> int:
    pre_commit, paths_file, out = argv[0], argv[1], argv[2]
    hook = argv[3] if len(argv) > 3 else None
    paths = [p.strip() for p in Path(paths_file).read_text(encoding="utf-8").splitlines() if p.strip()]
    before = {p: _sha(Path(p)) for p in paths}
    cmd = [pre_commit, "run"] + ([hook] if hook else []) + ["--files", *paths]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)  # nosec B603
    after = {p: _sha(Path(p)) for p in paths}
    changed = [p for p in paths if before[p] != after[p]]
    text = proc.stdout + proc.stderr + f"\nexit={proc.returncode} paths={len(paths)} rewritten={changed if changed else 'NONE'}\n"
    Path(out).write_text(text, encoding="utf-8")
    sys.stdout.write(text[-3000:])
    return proc.returncode or (1 if changed else 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
