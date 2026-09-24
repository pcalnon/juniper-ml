#!/usr/bin/env python
"""Copy the canopy E2E Phase 9 evidence that existed only on tmpfs into the repository.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, Lane A2's durability finding)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         memory reference_tmp_is_tmpfs_reboot_kills_the_isolated_stack.md

WHY. The Phase 9 authoring session (259b4d16) kept its suite logs, the review lanes' raw outputs and
Lane B's F-CANOPY-058 repro scripts in its scratchpad under /tmp, which is tmpfs: a reboot deletes it.
Lane A2 of the ledger's validation found the P1's only evidence there. This copies the files the
ledger's claims rest on -- never the extracted canopy source trees or tarballs -- into:

  reports/e2e-canopy-2026-09-02/phase9-scratch/<origin>/   raw outputs, byte-for-byte
  util/ad-hoc/2026-09-23_<lane>_<name>.{py,js}             lane scripts, a provenance header
                                                           prepended, the lane's code unmodified

Refuses to overwrite an existing destination, and refuses a source containing a secret-shaped
string. Re-running after a successful run is therefore a no-op that reports what exists.

Usage:
    python3 util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence.py [--dry-run]
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

S0 = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad")
REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "reports/e2e-canopy-2026-09-02/phase9-scratch"
SECRET_RE = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}|AGE-SECRET-KEY-|hf_[A-Za-z0-9]{20,}|pypi-AgEIcHlwaS|xox[abpr]-")

RAW = {
    "orchestrator": [
        "cuts_full_suite.log", "f055_full_suite.log", "cuts_r2_tests.log", "f055_tests_parent.log", "f055_tests_fix.log",
        "f055_tests_fix2.log", "f055_watchdog.log", "census_f055.log", "census_f055_150s.log", "f025_drive.log",
        "idle_cuts_live_check_rebuilt.log", "cuts_fix_tests.log",
    ],
    "f055_r1_laneA": [
        "laneA.UzPRF5/" + n for n in ("parent_junit.xml", "fix_junit.xml", "mut_i_junit.xml", "mut_ii_junit.xml", "mut_iii_junit.xml", "mut_iv_junit.xml", "mut_iv_b_junit.xml", "mut_v_junit.xml", "mut_vi_junit.xml")
    ],
    "cuts_r1_laneA": ["laneA_cuts.iVwNcF/m3_parent.log", "laneA_cuts.iVwNcF/m6_collect_ce78.txt"],
    "cuts_r3_laneB3": ["laneB3cuts.9xxSoB/parent_run.txt", "laneB3cuts.9xxSoB/head_run.txt", "laneB3cuts.9xxSoB/precommit_head.txt"],
    "f055_r1_laneB": ["laneB_f055.Iywb95/run_apply.json", "laneB_f055.Iywb95/run_watchdog.json", "laneB_f055.Iywb95/run_watchdog_r3.json"],
}

SCRIPTS = [
    ("laneB_f055.Iywb95/repro_f055.py", "2026-09-23_f055_r1_laneB_repro.py", "F-CANOPY-055 round 1, Lane B: the synthetic Dash app with the first fix's exact wiring, driven on the real renderer (the F-CANOPY-058 repro)"),
    ("laneB_f055.Iywb95/cascade_sim.py", "2026-09-23_f055_r1_laneB_cascade_sim.py", "F-CANOPY-055 round 1, Lane B: the eviction-cascade model (median time to the next applied response after a trigger)"),
    ("laneB_f055.Iywb95/compare_watchdog_js.py", "2026-09-23_f055_r1_laneB_compare_watchdog_js.py", "F-CANOPY-055 round 1, Lane B: compares the refactored strand watchdogs' JavaScript"),
    ("laneB_f055.Iywb95/dump_callbacks.py", "2026-09-23_f055_r1_laneB_dump_callbacks.py", "F-CANOPY-055 round 1, Lane B: dumps the built app's callback map"),
    ("laneB_f055.Iywb95/rerender_check.py", "2026-09-23_f055_r1_laneB_rerender_check.py", "F-CANOPY-055 round 1, Lane B: does a re-render re-request the feeder?"),
    ("laneB_f055.Iywb95/srcmap_extract.py", "2026-09-23_f055_r1_laneB_srcmap_extract.py", "F-CANOPY-055 round 1, Lane B: extracts dash-renderer source from its source map"),
    ("laneB_f055.Iywb95/no_interaction_sim.js", "2026-09-23_f055_r1_laneB_no_interaction_sim.js", "F-CANOPY-055 round 1, Lane B: the watchdog false-fire model with no user interaction"),
    ("laneB_f055.Iywb95/watchdog_alias_sim.js", "2026-09-23_f055_r1_laneB_watchdog_alias_sim.js", "F-CANOPY-055 round 1, Lane B: the strand watchdog's sampling-alias model"),
    ("laneB_probe_deps.py", "2026-09-23_cuts_r1_laneB_probe_deps.py", "the idle cuts' round 1, Lane B: the built-app dependency probe (the single-writer check over 178 callbacks)"),
]

HEADER = [
    "-" * 75,
    "ARCHIVED VERBATIM, 2026-09-24: {role}.",
    "Source: session 259b4d16's tmpfs scratchpad, {src}",
    "Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon",
    "Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane",
    "  (a subagent), not by the orchestrator; paths and ports inside are the lane's own.",
    "Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)",
    "Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;",
    "  reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md",
    "Everything below this block is the lane's file, unmodified.",
    "-" * 75,
]


def _header(role: str, src: str, comment: str) -> str:
    return "".join(f"{comment} {line.format(role=role, src=src)}\n" for line in HEADER)


def _refuse_secret(path: Path) -> bool:
    if SECRET_RE.search(path.read_text(encoding="utf-8", errors="replace")):
        print(f"REFUSED: secret-shaped string in {path}", file=sys.stderr)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    copied = existed = 0
    for origin, names in RAW.items():
        for name in names:
            src = S0 / name
            dst = EVIDENCE / origin / Path(name).name
            if dst.exists():
                existed += 1
                continue
            if not src.is_file():
                print(f"MISSING: {src}", file=sys.stderr)
                return 1
            if _refuse_secret(src):
                return 1
            if not args.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            copied += 1
    for name, dst_name, role in SCRIPTS:
        src = S0 / name
        dst = REPO / "util/ad-hoc" / dst_name
        if dst.exists():
            existed += 1
            continue
        if not src.is_file():
            print(f"MISSING: {src}", file=sys.stderr)
            return 1
        if _refuse_secret(src):
            return 1
        text = src.read_text(encoding="utf-8")
        if dst_name.endswith(".js"):
            out = _header(role, name, "//") + text
        elif text.startswith("#!"):
            first, _, rest = text.partition("\n")
            out = first + "\n" + _header(role, name, "#") + rest
        else:
            out = _header(role, name, "#") + text
        if not args.dry_run:
            dst.write_text(out, encoding="utf-8")
        copied += 1
    print(f"{'would copy' if args.dry_run else 'copied'} {copied}, already present {existed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
