"""
Apply one source mutant in a validator worktree of juniper-data, run pytest, restore it, and log the verdict.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (claims and docs lens): the #520 / #522 / #524 docstring and PR-body
         claims about what main's existing suites miss.

Never point it at a carrier worktree: it edits the named source file in place (restored by sha256 afterwards).
Usage: python3 util/ad-hoc/2026-11-08_flood4r2_val_data-claims_mutants.py <worktree> <log_dir> <scope> <mutant_id> [...]
       scope: "full" (juniper_data/tests/), or a comma-separated list of test paths relative to the worktree.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

PY = "/opt/miniforge3/envs/JuniperData/bin/python"
SPLIT = "juniper_data/core/split.py"
EQ = "juniper_data/generators/equities/generator.py"
MW = "juniper_data/api/middleware.py"

MUTANTS: dict[str, tuple[str, str, str]] = {
    # #524: temporal_split_indices clamp and sum check
    "V9-train-floor": (SPLIT, "train_end = min(max(train_end, 1), n_samples - 2)", "train_end = min(max(train_end, 0), n_samples - 2)"),
    "V10-val-floor": (SPLIT, "val_end = min(max(val_end, train_end + 1), n_samples - 1)", "val_end = min(max(val_end, train_end), n_samples - 1)"),
    "V12-test-floor": (SPLIT, "val_end = min(max(val_end, train_end + 1), n_samples - 1)", "val_end = min(max(val_end, train_end + 1), n_samples)"),
    "V11-sum-ge-to-gt": (SPLIT, "if train_ratio + val_ratio >= 1.0:", "if train_ratio + val_ratio > 1.0:"),
    # #522: the lost-symbol branch and the shared gate
    "V4-gate-or": (EQ, "allowed = settings.equities_allow_truncation if params.allow_truncation is None else params.allow_truncation", "allowed = settings.equities_allow_truncation or params.allow_truncation"),
    "V5-explicit-false-skips-lost": (EQ, '            reasons = "; ".join(f"{ticker}: {reason}" for ticker, reason in sorted(requested_lost.items())[:8])\n            raise IncompleteDataError(', '            reasons = "; ".join(f"{ticker}: {reason}" for ticker, reason in sorted(requested_lost.items())[:8])\n            if params.allow_truncation is not False:\n              raise IncompleteDataError('),
    "V13-drop-while-shut": (EQ, "        if not allowed:\n            return INCOMPLETE_FAIL", "        if not allowed:\n            return INCOMPLETE_DROP if params.incomplete_rows == INCOMPLETE_DROP else INCOMPLETE_FAIL"),
    # #520: RequestBodyLimitMiddleware's two comparisons
    "V1-stream-gt-to-ge": (MW, "if size > self._max_bytes:", "if size >= self._max_bytes:"),
    "V2-declared-gt-to-ge": (MW, "if declared_length > self._max_bytes:", "if declared_length >= self._max_bytes:"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(wt: Path, log_dir: Path, scope: str, mid: str) -> str:
    rel, old, new = MUTANTS[mid]
    target = wt / rel
    original = target.read_text(encoding="utf-8")
    before = sha(target)
    if original.count(old) != 1:
        return f"{mid}: SKIPPED -- old text occurs {original.count(old)} times in {rel}"
    tests = ["juniper_data/tests/"] if scope == "full" else scope.split(",")
    cmd = [PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", *tests]
    try:
        target.write_text(original.replace(old, new), encoding="utf-8")
        start = time.monotonic()
        proc = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, check=False)
        took = time.monotonic() - start
    finally:
        target.write_text(original, encoding="utf-8")
    restored = sha(target) == before
    log = log_dir / f"{mid}__{'full' if scope == 'full' else 'named'}.log"
    log.write_text(f"$ (cwd={wt}) {' '.join(cmd)}\nexit={proc.returncode}\n\n{proc.stdout[-6000:]}\n{proc.stderr[-3000:]}", encoding="utf-8")
    tail = [line for line in proc.stdout.splitlines() if line.strip()][-1:] or ["<no output>"]
    verdict = "GREEN" if proc.returncode == 0 else "RED"
    return f"{mid} [{scope if scope != 'full' else 'full suite'}]: {verdict} exit={proc.returncode} | {tail[0]} | {took:.0f}s | restored={restored} | log={log}"


def main() -> int:
    wt, log_dir, scope = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    log_dir.mkdir(parents=True, exist_ok=True)
    if "flood4r2-consolidated" in wt.name or "flood4r2-retry-after" in wt.name:
        print("refusing: that is a carrier worktree")
        return 2
    for mid in sys.argv[4:]:
        print(run_one(wt, log_dir, scope, mid), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
