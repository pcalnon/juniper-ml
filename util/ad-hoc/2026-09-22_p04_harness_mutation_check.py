#!/usr/bin/env python3
"""Mutation-check the P0.4 envelope harness: every deliberately-broken record must FAIL it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc, roadmap step P0.4 acceptance)
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (the acceptance evidence for the cascor P0.4 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md §3.1 ("Acceptance ... a
         harness that fails a deliberately-broken record in cascor CI. Mutation-check it.")

WHY THIS EXISTS

A harness that has never been seen to fail proves nothing (the vacuous-pass class). This applies
each mutation to the REAL cascor source in a worktree, runs the contract test, and restores the
file with ``git checkout`` in a ``finally`` -- so a crash cannot leave a mutated tree behind.

The mutation set is the union of the roadmap's acceptance and the breaks Lane B1 of the 2026-09-22
handoff validation showed a formatter-string golden CANNOT see (M1, M3, M5, M11, M12, V2, V3):

  * record shape: the ``+`` sentinel on each sink, timestamp precision, stdout -> stderr, the
    console/file closure swap, the lazy ``%``-args interpolation;
  * P2.1's two plausible mistakes -- the frame captured inside ``_log_at_level`` WITHOUT
    ``.f_back`` (every record names logger.py) and with one hop too many;
  * the marker surface: a message text edit, and a marker demoted INFO -> DEBUG while its DEBUG
    twin keeps the literal alive in source;
  * the file surface: the ``juniper`` logger level, the rotation count, the file name, a datefmt.

Two POSITIVE controls must PASS: the unmutated tree, and P2.1 implemented as prescribed
(``frame = cls._frm().f_back`` inside ``_log_at_level``) -- a harness that rejects a correct P2.1
would block the step it exists to protect.

USAGE

    python3 util/ad-hoc/2026-09-22_p04_harness_mutation_check.py --worktree <cascor worktree>

Exit 0 when every mutant fails and both controls pass; 1 otherwise; 2 on usage error.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
TEST = "src/tests/unit/test_log_record_envelope_contract.py"
LOGGER = "src/log_config/logger/logger.py"
CONSTANTS = "src/cascor_constants/constants.py"
CLOG = "src/cascor_constants/constants_logging/constants_logging.py"
CC = "src/cascade_correlation/cascade_correlation.py"
YAML = "conf/logging_config.yaml"
OBS = "src/api/observability.py"

EMIT_OLD = "cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level="
EMIT_NEW = "cls._log_at_level(level="
FILTER = "        if cls._filter_by_level(level=level, log_level=cls._log_level):\n"


def p21(frame_expr: str) -> list[tuple[str, str, str, int]]:
    """P2.1 as a mutation: drop the eager arguments from all eight methods, capture inside."""
    return [(LOGGER, EMIT_OLD, EMIT_NEW, 8), (LOGGER, FILTER, FILTER + f"            frame = {frame_expr}\n            tsp = cls._tsp()\n", 1)]


# name -> (expect "PASS" | "FAIL", [(file, old, new, expected occurrence count)])
MUTANTS: dict[str, tuple[str, list[tuple[str, str, str, int]]]] = {
    "C0 unmutated tree (control)": ("PASS", []),
    "C1 P2.1 done as prescribed: frame = cls._frm().f_back (control)": ("PASS", p21("cls._frm().f_back")),
    "M1a drop '+' on the stdout sink": ("FAIL", [(LOGGER, 'print(f"+{_console_message', 'print(f"{_console_message', 1)]),
    "M1b drop '+' on the file sink": ("FAIL", [(LOGGER, '_line = f"+{_file_message', '_line = f"{_file_message', 1)]),
    "M3 Path A timestamp gains microseconds": ("FAIL", [(CONSTANTS, '_PROJECT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"', '_PROJECT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"', 1)]),
    "M5 Path A console record goes to stderr": ("FAIL", [(LOGGER, 'print(f"+{_console_message(frame, tsp, level, message)}")', 'print(f"+{_console_message(frame, tsp, level, message)}", file=sys.stderr)', 1)]),
    "M11 console/file closures swapped": ("FAIL", [(LOGGER, "_console_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)", "_console_message = cls._logging_message(cls._formatter_string_file, cls._file_dict)", 1), (LOGGER, "_file_message = cls._logging_message(cls._formatter_string_file, cls._file_dict)", "_file_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)", 1)]),
    "M12 lazy %-args interpolation dropped": ("FAIL", [(LOGGER, "                message = message % args\n", "                pass\n", 1)]),
    "V2 P2.1 with .f_back forgotten (records name logger.py)": ("FAIL", p21("cls._frm()")),
    "V3 P2.1 one hop too many": ("FAIL", p21("cls._frm().f_back.f_back")),
    "MK1 marker text edited (train_candidates)": ("FAIL", [(CC, "train_candidates: Executing candidate training with", "train_candidates: Running candidate training with", 1)]),
    "MK2 INFO twin of a marker demoted to DEBUG (Output Layer Training)": ("FAIL", [(CC, 'self.logger.info(f"CascadeCorrelationNetwork: train_output_layer: Output Layer Training - Epoch', 'self.logger.debug(f"CascadeCorrelationNetwork: train_output_layer: Output Layer Training - Epoch', 1)]),
    "F1 juniper logger INFO -> WARNING in the YAML": ("FAIL", [(YAML, "  juniper:\n    # level: TRACE\n    # level: VERBOSE\n    # level: DEBUG\n    level: INFO\n", "  juniper:\n    # level: TRACE\n    # level: VERBOSE\n    # level: DEBUG\n    level: WARNING\n", 1)]),
    "F2 rotation backupCount 5 -> 3": ("FAIL", [(CLOG, "_LOGGER_LOG_FILE_BACKUP_COUNT: int = 5", "_LOGGER_LOG_FILE_BACKUP_COUNT: int = 3", 1)]),
    "F3 Path C log file renamed": ("FAIL", [(OBS, 'log_file = log_dir / "juniper_cascor.log"', 'log_file = log_dir / "juniper-cascor-api.log"', 1)]),
    "F4 Path B file datefmt gains milliseconds": ("FAIL", [(YAML, '    format: "[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"\n    datefmt: "%Y-%m-%d %H:%M:%S"\n', '    format: "[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"\n    datefmt: "%Y-%m-%d %H:%M:%S,%f"\n', 1)]),
}


def run(worktree: Path) -> int:
    env = {k: v for k, v in os.environ.items() if k not in {"JUNIPER_CASCOR_LOG_DIR", "CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL", "LOG_ENVELOPE_CAPTURE"}}
    # Refuse only when a file this tool MUTATES is already modified: restoring it with
    # ``git checkout`` would destroy that edit. Other modified files (the PR's own CHANGELOG
    # entry, say) are left alone and are not touched.
    mutated = sorted({rel for _expect, edits in MUTANTS.values() for rel, *_ in edits})
    dirty = subprocess.run(["git", "-C", str(worktree), "status", "--porcelain", "--untracked-files=no", "--", *mutated], capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        print(f"mutation: refusing -- files this tool mutates are already modified in {worktree}:\n{dirty}", file=sys.stderr)
        return 2
    rows = []
    for name, (expect, edits) in MUTANTS.items():
        touched = sorted({f for f, *_ in edits})
        try:
            for rel, old, new, count in edits:
                path = worktree / rel
                src = path.read_text(encoding="utf-8")
                assert src.count(old) == count, f"{name}: expected {count} x {old!r} in {rel}, found {src.count(old)} -- the mutation is stale"
                path.write_text(src.replace(old, new), encoding="utf-8")
            proc = subprocess.run([PY, "-m", "pytest", TEST, "-m", "unit and not slow", "-p", "no:cacheprovider", "--timeout=120", "-q", "-o", "addopts="], cwd=worktree, env=env, capture_output=True, text=True)
            tail = [ln for ln in proc.stdout.splitlines() if ln.strip()][-1:] or ["<no output>"]
            got = "PASS" if proc.returncode == 0 else "FAIL"
            failed = sorted({ln.split("::")[1].split(" ")[0] for ln in proc.stdout.splitlines() if ln.startswith("FAILED ")})
            rows.append((name, expect, got, tail[0], failed))
        finally:
            if touched:
                subprocess.run(["git", "-C", str(worktree), "checkout", "--", *touched], check=True)
    ok = True
    for name, expect, got, tail, failed in rows:
        verdict = "ok " if expect == got else "BAD"
        ok &= expect == got
        print(f"{verdict} expect {expect:<4} got {got:<4}  {name}\n      {tail}" + (f"\n      failing classes: {', '.join(failed)}" if failed else ""))
    clean = subprocess.run(["git", "-C", str(worktree), "status", "--porcelain", "--untracked-files=no", "--", *mutated], capture_output=True, text=True, check=True).stdout.strip()
    print(f"\nmutation: tree restored: {'yes' if not clean else 'NO -- ' + clean}")
    print(f"mutation: {'ALL MUTANTS KILLED, BOTH CONTROLS PASS' if ok else 'HARNESS DEFECT: see BAD rows'}")
    return 0 if ok and not clean else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worktree", required=True, help="a juniper-cascor worktree carrying the P0.4 harness (the files this tool mutates must be unmodified)")
    args = ap.parse_args(argv)
    return run(Path(args.worktree).resolve())


if __name__ == "__main__":
    sys.exit(main())
