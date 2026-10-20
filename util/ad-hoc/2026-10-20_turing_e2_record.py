"""
Record turing bring-up task E2's completion in the bring-up plan, idempotently (plan v1.4.1).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (the E2 record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2, §18.3);
         reports/2026-10-20_turing-e2-envs/; conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml

Why: the plan is a shared file. The "code signing" session's juniper-ml#2280 (§19, v1.4.0) merged while E2 was
being validated, and erratum E-LAND-2 says to keep each shared-file edit in an idempotent script, run on a fresh
origin/main copy. Every edit below is anchored on text, reports `present`, `applied` or `MISSING`, and is never
applied twice. If any anchor is missing, nothing is written.

    python3 -I util/ad-hoc/2026-10-20_turing_e2_record.py [--root DIR] [--dry-run]

The edits, all in the plan:
  1. the Version line, 1.4.0 -> 1.4.1. Only from 1.4.0: another version is reported and left alone;
  2. §18's opening paragraph names the session's final handoff beside the record PR's;
  3. §18.2's E2 row and G1 row;
  4. §18.3 gains errata E-BLAS and E-REQ, after E-LAND-3's last sub-bullet (§19 follows it).

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
RECORD_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-20_turing-session-3-g5-g6-g4-landed-e2-two-envs-created-pypi-blocked.md"
FINAL_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-20_turing-session-3-final-e2-validated-g1-next.md"

VERSION_OLD = "- **Version**: 1.4.0 — v1.3.0 plus"
VERSION_NEW = (
    "- **Version**: 1.4.1 — v1.4.0 plus E2's completion (§18.2's E2 row; errata E-BLAS and E-REQ in §18.3; 2026-10-20). "
    "v1.4.0 was v1.3.0 plus"
)

INTRO_OLD = f", and its own handoff is `{RECORD_HANDOFF}`."
INTRO_NEW = (
    f". Its handoffs are `{RECORD_HANDOFF}`, written with the record PR (juniper-ml#2277), and `{FINAL_HANDOFF}`, "
    "written after E2's validation (v1.4.1)."
)

E2_ROW_PREFIX = "| E2 | **partial (OWNER: Little Snitch for PyPI)** |"
E2_ROW_NEW = (
    "| E2 | **done** | All three envs were created on 2026-10-20 with `MAMBA_SSL_VERIFY=true` (E-SSL), then validated "
    "against their repos' CI lanes by `util/ad-hoc/2026-10-19_turing_e2_validate_envs.py`, through a "
    "`venv --system-site-packages` overlay so that each env stays what its spec builds. "
    "JuniperCascor1: unit 5777 of 5777 passed (coverage 96.55%), integration 172 of 172. "
    "JuniperData: unit 2201 passed and 3 skipped of 2204 (97.82%; the skips need GNU `base64` and `date`), "
    "integration 62 of 62. "
    "JuniperCanopy1, re-specified on MKL after its OpenBLAS build hung (E-BLAS): unit 7947 passed, 10 skipped and "
    "2 failed of 7959 (96.68%), integration 523 passed and 79 skipped of 602; the 2 failures are E-REQ. "
    "Exports, summaries and pip freezes are in `reports/2026-10-20_turing-e2-envs/`. G-ENV's env half holds; its "
    "parent-AGENTS.md half still fails, because that file is not on turing |"
)

G1_ROW_OLD = "| G1 | not started | next agent task, with E2's validation once PyPI is allowed |"
G1_ROW_NEW = "| G1 | not started | the next agent task |"

ERRATA_ANCHOR = "  - The count line cannot be avoided, so a suite-adding PR (G4) is built from main after the other suite-adding PR merges.\n"
ERRATA_MARK = "- **E-BLAS (E2, JuniperCanopy1's BLAS).**"
ERRATA = (
    "- **E-BLAS (E2, JuniperCanopy1's BLAS).** The first JuniperCanopy1 kept the Linux env's `libblas 3.11.0`. On "
    "osx-64 that is OpenBLAS 0.3.30 (the openmp build) under conda-forge's `cpu_generic` torch. juniper-canopy's unit "
    "lane hung in it twice, at results 4351 and 4353 of 7959 (`src/tests/unit/frontend/test_stage2_global_lane.py`), "
    "at about 300% CPU. pytest-timeout's 60 s limit never fired, because the main thread never returned to the "
    "interpreter.\n"
    "  - `sample` showed three threads spinning in OpenBLAS's `blas_memory_alloc`: the main thread (torch `linear` → "
    "`addmm` → `sgemm`) and two demo-mode `_training_loop` daemon threads that earlier tests had left running "
    "(`sgemv` under `goto_set_num_threads`, and `sgemm`). The same two threads, Thread-210 and Thread-257, were there "
    "in both runs.\n"
    "  - With `OMP_NUM_THREADS=6`, torch's intra-op default on turing, every thread's OpenMP count agrees, and the "
    "same lane ran to the end. That points at OpenBLAS resetting its thread count on each call from a thread whose "
    "OpenMP count differs. A synthetic three-thread script, `util/ad-hoc/2026-10-20_turing_e2_blas_concurrency_repro.py`, "
    "did not hang, so the trigger takes more than concurrent BLAS calls.\n"
    "  - Fix: the spec takes the MKL variant (`libblas`, `libcblas` and `liblapack` 3.9.0 `20_osx64_mkl`, and `mkl` "
    "2023.2.0, so the solver picks the `cpu_mkl` torch). On Linux canopy's torch is the PyPI wheel, which carries its "
    "own MKL, so canopy's CI never runs torch on OpenBLAS; JuniperCascor1 already ran this stack. Evidence: "
    "`reports/2026-10-20_turing-e2-envs/JuniperCanopy1.openblas-hang.txt`.\n"
    "  - Follow-up (juniper-canopy, not filed): the tests that leave demo mode's training thread running. Off "
    "OpenBLAS they cost only CPU.\n"
    "- **E-REQ (E2, juniper-canopy's `requests` floor).** Two canopy tests assume `requests` refuses a header value "
    "with a trailing LF: `src/tests/unit/frontend/test_internal_api_key_rules.py::test_a_key_requests_refuses_to_send_is_left_off_the_self_call[trailing-lf]` "
    "and `src/tests/regression/test_blank_api_key_warning_boot.py::test_a_padded_key_never_reaches_a_log_record`. "
    "requests refuses it from 2.33.1 on, while 2.33.0 and 2.32.5 accept it (checked with each wheel's "
    "`check_header_validity`). canopy floors `requests>=2.28.0`, and its CI resolves the newest, 2.34.2. "
    "JuniperCanopy1 keeps the Linux env's 2.32.5, so both tests fail here, as they would in the Linux env the spec "
    "was exported from.\n"
    "  - Not a turing defect. Follow-up (juniper-canopy, not filed): raise the floor to `requests>=2.33.1`, or derive "
    "the refused set from the installed requests.\n"
)


def edit(text: str, old: str, new: str, done_mark: str, label: str, report: list) -> str:
    if done_mark in text:
        report.append(f"present  {label}")
        return text
    if text.count(old) != 1:
        report.append(f"MISSING  {label}: anchor found {text.count(old)} times")
        return text
    report.append(f"applied  {label}")
    return text.replace(old, new, 1)


def replace_row(text: str, prefix: str, new_row: str, label: str, report: list) -> str:
    if new_row in text:
        report.append(f"present  {label}")
        return text
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        report.append(f"MISSING  {label}: row prefix found {len(hits)} times")
        return text
    lines[hits[0]] = new_row
    report.append(f"applied  {label}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    report: list[str] = []

    if VERSION_NEW in text:
        report.append("present  Version line 1.4.1")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  Version line 1.4.0 -> 1.4.1")
    else:
        line = next((x for x in text.split("\n") if x.startswith("- **Version**:")), "<none>")
        report.append(f"skipped  Version line is not 1.4.0, left alone: {line[:60]}")

    new = edit(text, INTRO_OLD, INTRO_NEW, FINAL_HANDOFF, "§18 opening paragraph: the final handoff", report)
    new = replace_row(new, E2_ROW_PREFIX, E2_ROW_NEW, "§18.2 E2 row", report)
    new = edit(new, G1_ROW_OLD, G1_ROW_NEW, G1_ROW_NEW, "§18.2 G1 row", report)
    new = edit(new, ERRATA_ANCHOR, ERRATA_ANCHOR + ERRATA, ERRATA_MARK, "§18.3 errata E-BLAS and E-REQ", report)

    for line in report:
        print(line)
    if any(line.startswith("MISSING") for line in report):
        print("not written: an anchor is missing")
        return 1
    if new == path.read_text(encoding="utf-8"):
        print("would change 0 file(s)" if args.dry_run else "changed 0 file(s)")
        return 0
    if args.dry_run:
        print(f"would change 1 file(s): {PLAN}")
        return 0
    path.write_text(new, encoding="utf-8")
    print(f"changed 1 file(s): {PLAN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
