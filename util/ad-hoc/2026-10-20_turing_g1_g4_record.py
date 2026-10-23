"""
Record G1's landing and G4's promotion in the turing bring-up plan, idempotently (plan v1.4.2).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (the G1 / G4-promotion record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.2, §18.3);
         juniper-ml#2287 (G1), juniper-ml#2289 (G4's promotion); util/ad-hoc/2026-10-20_turing_e2_record.py (the pattern)

Why: the plan is a shared file, so the edits are anchored on text and re-run on a fresh origin/main copy before the
upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing, nothing is written.

    python3 -I util/ad-hoc/2026-10-20_turing_g1_g4_record.py [--root DIR] [--dry-run]

The edits, all in the plan:
  1. the Version line, 1.4.1 -> 1.4.2. Only from 1.4.1: another version is reported and left alone;
  2. §18's opening paragraph names the following session and its handoff;
  3. §18.2's G4 row (promoted) and G1 row (landed);
  4. §18.3 gains errata E-G1 (G1's shape against §9.3 and task G1) and E-DUP (two sessions, one handoff).

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PICKED_UP = HANDOFF_DIR + "HANDOFF_2026-10-20_turing-session-3-final-e2-validated-g1-next.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md"
G1_PR, G1_SHA = "juniper-ml#2287", "e3ba1936"
G4P_PR, G4P_SHA = "juniper-ml#2289", "5a383ae1"

VERSION_OLD = "- **Version**: 1.4.1 — v1.4.0 plus E2's completion"
VERSION_NEW = (
    "- **Version**: 1.4.2 — v1.4.1 plus G1's landing and G4's promotion (§18.2's G1 and G4 rows; errata E-G1 and E-DUP in "
    "§18.3; 2026-10-20). v1.4.1 was v1.4.0 plus E2's completion"
)

INTRO_OLD = "written after E2's validation (v1.4.1)."
INTRO_NEW = (
    "written after E2's validation (v1.4.1). G1 and G4's promotion landed in the following session (v1.4.2), whose "
    f"handoff is `{THIS_HANDOFF}`."
)

G4_PREFIX = "| G4 | landed, advisory |"
G4_ROW = (
    "| G4 | landed; **required** since its promotion | juniper-ml#2276 (`3968ca04`), built after juniper-ml#2273 merged "
    "(E-LAND-3): the `host-tooling-macos` job runs the host-tooling suites on `macos-latest` under `/bin/bash` 3.2, behind "
    "in-job change detection. First run, on the PR: green on arm64 macOS 26 (`/bin/bash` 3.2.57, `/opt/homebrew`), 371 tests, "
    "7 skipped, 2 m 13 s. On turing: 376 tests, 1 skipped. **Promoted** by "
    f"{G4P_PR} (`{G4P_SHA}`) after 12 consecutive green push runs on `main`, from `3968ca04` to `e3ba1936`. Each ran the "
    "suites, and the last ran all eleven, G1's two included. It joined the Quality Gate's `needs:` with its own "
    '`!= "success"` arm, never as a separate ruleset context |'
)

G1_PREFIX = "| G1 | not started |"
G1_ROW = (
    f"| G1 | landed | {G1_PR} (`{G1_SHA}`), in the following session. `util/host_state_probe.bash` collects ten sections "
    "of raw command captures; `util/host_state_check.py` judges seven of the ten §9.3 gates against "
    "`conf/hosts/turing/expected.yaml`, condition by condition (E-G1). The 54 tests are in `tests/test_host_state_probe.py` "
    "and `tests/test_host_state_check.py`. `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` kills 57 of 57 mutants, "
    "and `host-tooling-macos` ran all eleven suites green. **I-G1's first reading (2026-10-20): 0 of 7 gates pass.** Each "
    "failure is an open task: A1; C1, C2 and C3; D4; E4; A6 and F2; node mode (F3) and D7; and the I-SIGN record "
    "(signing plan K10) |"
)

ERRATA_ANCHOR = "\n\n## 19. Commit signing for the terminal and the IDEs"
ERRATA = (
    "\n- **E-G1 (G1's shape, against §9.3 and task G1).**\n"
    "  - **Two modes.** The report exits 0 whatever the gates say. `--check`, which is I-G1, exits 1 on a failed gate "
    "and 2 on a condition it could not evaluate; 2 wins. `--section` names gates for the check (`G-MEM`, `g-mem` or "
    "`mem`) and fact sections for the probe.\n"
    "  - **Owner-run results are records.** Two gates have an owner-run half that the check cannot measure: G-SIGN's "
    "I-B5, widened to the signing plan's I-SIGN matrix (K10, recorded by K11), and G-NET's iperf3 result (F2). Each is a "
    "record in `expected.yaml` whose file under `reports/` must exist. Until it does, its condition fails and names the "
    "task. So do the parent AGENTS.md hash (E4) and the reserved address (A6).\n"
    "  - **Identity first.** The probe's `uname -m`, `hw.memsize`, `hw.physicalcpu` and `hw.ncpu` must equal "
    "`identity`, or the run exits 2: the file would describe another machine.\n"
    "  - **R-G1 is validation.** An `expected.yaml` whose VM does not fit exits 2 before anything runs. That covers "
    "`vm.mem_gib` plus G-MEM's reserve over `hw.memsize`, and vCPUs over physical cores (X2's 8 vCPU on 6 cores).\n"
    "  - **G-SIGN and D11.** G-SIGN reads only the preflight's `pinentry`, `agent-socket` and `external-cache` lines, "
    "which do not depend on an agent session's D11 override, plus `util/configure_commit_signing.py --check`, which sets "
    "D11 aside itself. So the probe never strips D11 from its environment.\n"
    "  - **The probe's JSON escaping** is bash parameter expansion under `LC_ALL=C`. In bash 3.2 its cost still grows "
    "with size times escapes: 3 s for the 16 KB alias capture, and 7.6 s for a 19 KB capture dense with quotes. A UTF-8 "
    "locale is 20 to 25 times slower (68 s and 159 s), which is why the probe exports `LC_ALL=C`. A full probe takes "
    "about 9 s on turing.\n"
    "- **E-DUP (two sessions, one handoff).** The \"mac dev env\" and \"code signing\" sessions both started G1 from "
    f"`{PICKED_UP}`. {G1_PR} merged first, and juniper-ml#2288 was closed as superseded without touching main's G1 "
    "files. Its draft of the G4 promotion became the base of "
    f"{G4P_PR}. Before starting a handoff's task, check `gh pr list` for it and `ListAgents` for another session on the "
    "same handoff."
)


def edit(text: str, old: str, new: str, done_mark: str, label: str, report: list) -> str:
    if done_mark in text:
        report.append(f"present  {label}")
        return text
    if text.count(old) != 1:
        report.append(f"MISSING  {label}: anchor found {text.count(old)} times")
        return text
    report.append(f"applied  {label}")
    return text.replace(old, new)


def replace_row(text: str, prefix: str, new_row: str, label: str, report: list) -> str:
    if new_row in text:
        report.append(f"present  {label}")
        return text
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        report.append(f"MISSING  {label}: {len(hits)} rows start with {prefix!r}")
        return text
    lines[hits[0]] = new_row
    report.append(f"applied  {label}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if G4P_SHA == "PENDING":
        print("G4P_SHA is not set: fill in juniper-ml#2289's merge sha first")
        return 1
    path = args.root / PLAN
    text = original = path.read_text(encoding="utf-8")
    report: list[str] = []
    if "- **Version**: 1.4.2 —" in text:
        report.append("present  Version line 1.4.2")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW)
        report.append("applied  Version line 1.4.2")
    else:
        report.append("MISSING  Version line: the plan is at neither 1.4.1 nor 1.4.2")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "§18 opening paragraph: the following session", report)
    text = replace_row(text, G4_PREFIX, G4_ROW, "§18.2 G4 row", report)
    text = replace_row(text, G1_PREFIX, G1_ROW, "§18.2 G1 row", report)
    text = edit(text, ERRATA_ANCHOR, ERRATA + ERRATA_ANCHOR, "- **E-G1 (G1's shape", "§18.3 errata E-G1 and E-DUP", report)
    print("\n".join(report))
    if any(line.startswith("MISSING") for line in report):
        print("nothing written")
        return 1
    changed = text != original
    if changed and not args.dry_run:
        path.write_text(text, encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {int(changed)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
