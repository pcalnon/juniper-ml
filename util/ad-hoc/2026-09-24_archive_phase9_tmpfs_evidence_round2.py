#!/usr/bin/env python
"""Copy the rest of the canopy E2E Phase 9 evidence that exists only on tmpfs, including round 2's, into the repository.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round 2: Lane R2-F's finding 17, Lane R2-B's finding 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence.py (the first pass, session 259b4d16 only);
         notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md

WHY. The first pass copied what round 1 of the ledger's validation found on tmpfs. Round 2 found more, in two
sessions' scratchpads: files the ledger's claims rest on that the first pass missed (Lane B's
``fix_callbacks.json``, which its archived repro reads; four probe scripts; B3's 111- and 321-test outputs;
Lane A's m1 diffs), and the round-1 and round-2 lanes' own repros, which exist nowhere else. /tmp is tmpfs,
and a reboot deletes all of it.

Destinations, as in the first pass:

  reports/e2e-canopy-2026-09-02/phase9-scratch/<origin>/   raw outputs, byte-for-byte
  util/ad-hoc/<date>_<lane>_<name>.py                      lane scripts, a provenance header prepended,
                                                           the lane's code unmodified

Never the lanes' copies of canopy, cascor or renderer source, or of this ledger. Refuses to overwrite a
destination, refuses a source with a secret-shaped string, and refuses one containing an e-mail address
other than a ``noreply`` one or the Codecov uploader's public GPG key address (``@codecov.io``), which CI
logs print. Re-running after a successful run is a no-op that reports what exists.

Usage:
    python3 util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence_round2.py [--dry-run]
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

TMP = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml")
S0 = TMP / "259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad"  # Phase 9's authoring session
S1 = TMP / "ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad"  # the ledger-validation session
REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "reports/e2e-canopy-2026-09-02/phase9-scratch"
# Every GitHub token prefix (ghp_ gho_ ghu_ ghs_ ghr_) and JWTs were added 2026-09-24 after round 3 (Lane R3-B).
SECRET_RE = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"
    r"|AGE-SECRET-KEY-|hf_[A-Za-z0-9]{20,}|pypi-AgEIcHlwaS|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}|xox[abposr]-|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
)
# The local part must hold an alphanumeric somewhere: a diff line "+@pytest.mark.unit" is not an address, and
# "_lead@example.org" is (round 4, Lane R4-B, found the first, alphanumeric-first form missed the latter).
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[._%+-]*[A-Za-z0-9][A-Za-z0-9._%+-]*(?:@|%40)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")

# (origin directory under EVIDENCE, source root, path under the root)
RAW = [
    ("cuts_r3_laneB3", S0, "laneB3cuts.9xxSoB/head_js.txt"),
    ("cuts_r3_laneB3", S0, "laneB3cuts.9xxSoB/head_related.txt"),
    ("cuts_r1_laneA", S0, "laneA_cuts.iVwNcF/m1_orig.diff"),
    ("cuts_r1_laneA", S0, "laneA_cuts.iVwNcF/m1_rebuilt.diff"),
    ("cuts_r1_laneA", S0, "laneA_cuts.iVwNcF/m1_orig.norm"),
    ("cuts_r1_laneA", S0, "laneA_cuts.iVwNcF/m1_rebuilt.norm"),
    ("f055_r1_laneB/fix", S0, "laneB_f055.Iywb95/fix/fix_callbacks.json"),
    ("ledger_r1_laneB1", S1, "f058repro.6JTgea/app.log"),
    ("ledger_r2_laneB", S1, "r2b.SQyNnR/app204.log"),
    ("ledger_r2_laneB", S1, "r2b.SQyNnR/appdata.log"),
    ("ledger_r2_laneB", S1, "r2b.SQyNnR/app2.log"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkD/ci_py313_unit.log"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/int_0254.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/int_05f2.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/int_3a6d.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/int_c053.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/msg_4b4c.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/msg_e905.txt"),
    ("ledger_r2_laneF", S1, "r2f.xB7Gf1/forkC/pr676_edits.json"),
]

R1_CUTS = "reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md"
L_R1 = "reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round1.md"
L_R2 = "reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md"

# (source root, path under the root, destination name in util/ad-hoc, role, the report that cites it)
SCRIPTS = [
    (S0, "laneB_probe_walk.py", "2026-09-23_cuts_r1_laneB_probe_walk.py", "the idle cuts' round 1, Lane B: the layout walk over every Interval", R1_CUTS),
    (S0, "laneB_probe_mutation.py", "2026-09-23_cuts_r1_laneB_probe_mutation.py", "the idle cuts' round 1, Lane B: the injected dead Interval the CLASS check must flag", R1_CUTS),
    (S0, "laneB_probe_stop.py", "2026-09-23_cuts_r1_laneB_probe_stop.py", "the idle cuts' round 1, Lane B: the Stop probe behind F-CANOPY-056", R1_CUTS),
    (S0, "laneB_probe_exact.py", "2026-09-23_cuts_r1_laneB_probe_exact.py", "the idle cuts' round 1, Lane B: the exact-envelope probe of _merge_session", R1_CUTS),
    (S1, "f058repro.6JTgea/app.py", "2026-09-24_ledger_r1_laneB1_second_input_app.py", "the ledger's round 1, Lane B1: the synthetic app for F-CANOPY-058's second-Input trigger", L_R1),
    (S1, "f058repro.6JTgea/drive.py", "2026-09-24_ledger_r1_laneB1_second_input_drive.py", "the ledger's round 1, Lane B1: the driver for F-CANOPY-058's second-Input trigger", L_R1),
    (S1, "r2b.SQyNnR/synth_app.py", "2026-09-24_ledger_r2_laneB_census_synth_app.py", "the ledger's round 2, Lane R2-B: the synthetic app that refuted the F-058 census's eviction count", L_R2),
    (S1, "r2b.SQyNnR/synth_drive.py", "2026-09-24_ledger_r2_laneB_census_synth_drive.py", "the ledger's round 2, Lane R2-B: runs the F-058 census's own JavaScript on that app", L_R2),
    (S1, "r2b.SQyNnR/synth_app2.py", "2026-09-24_ledger_r2_laneB_watchdog_synth_app.py", "the ledger's round 2, Lane R2-B: canopy's watchdog JavaScript over a 40 s lane", L_R2),
    (S1, "r2b.SQyNnR/synth_drive2.py", "2026-09-24_ledger_r2_laneB_watchdog_synth_drive.py", "the ledger's round 2, Lane R2-B: the fire-detector check (2 real fires, 0 counted)", L_R2),
    (S1, "r2b.SQyNnR/entries_in_window.py", "2026-09-24_ledger_r2_laneB_entries_in_window.py", "the ledger's round 2, Lane R2-B: every transcript entry in the 21:41-01:40Z window", L_R2),
    (S1, "r2b.SQyNnR/bg_tasks.py", "2026-09-24_ledger_r2_laneB_bg_tasks.py", "the ledger's round 2, Lane R2-B: background task launches and completion notices", L_R2),
    (S1, "r2f.xB7Gf1/forkE/probe_merge.py", "2026-09-24_ledger_r2_laneF_probe_merge.py", "the ledger's round 2, Lane R2-F: _merge_session and render_session on cascor's real session (the KeyError)", L_R2),
    (S1, "r2f.xB7Gf1/forkC/scan_676.py", "2026-09-24_ledger_r2_laneF_scan_676.py", "the ledger's round 2, Lane R2-F: transcript scan for a ready or arm of canopy#676", L_R2),
    (S1, "r2f.xB7Gf1/forkC/scan_drafts.py", "2026-09-24_ledger_r2_laneF_scan_drafts.py", "the ledger's round 2, Lane R2-F: which sessions drafted the nine PRs", L_R2),
    (S1, "r2f.xB7Gf1/forkC/window_entries.py", "2026-09-24_ledger_r2_laneF_window_entries.py", "the ledger's round 2, Lane R2-F: transcript entries in the rate-limit window", L_R2),
    (S1, "r2f.xB7Gf1/forkC/bg_all.py", "2026-09-24_ledger_r2_laneF_bg_all.py", "the ledger's round 2, Lane R2-F: every background launch and its completion", L_R2),
]

HEADER = [
    "-" * 75,
    "ARCHIVED VERBATIM, 2026-09-24: {role}.",
    "Source: session {session}'s tmpfs scratchpad, {src}",
    "Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon",
    "Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane",
    "  (a subagent), not by the orchestrator; paths and ports inside are the lane's own.",
    "Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)",
    "Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;",
    "  {report}",
    "Everything below this block is the lane's file, unmodified.",
    "-" * 75,
]


def _header(role: str, session: str, src: str, report: str, comment: str) -> str:
    return "".join(f"{comment} {line.format(role=role, session=session, src=src, report=report)}\n" for line in HEADER)


def _refuse(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    if SECRET_RE.search(text):
        print(f"REFUSED: secret-shaped string in {path}", file=sys.stderr)
        return True
    # Allowed: noreply trailers, and the Codecov uploader's public GPG key UID that CI logs print.
    emails = sorted({m for m in EMAIL_RE.findall(text) if "noreply" not in m.lower() and not m.lower().endswith("@codecov.io")})
    if emails:
        print(f"REFUSED: {len(emails)} non-noreply e-mail address(es) in {path}; review by hand", file=sys.stderr)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    copied = existed = flagged = 0
    for origin, root, name in RAW:
        src, dst = root / name, EVIDENCE / origin / Path(name).name
        if dst.exists():
            existed += 1
            flagged += _refuse(dst)  # re-check what is already archived (round 4, Lane R4-B)
            continue
        if not src.is_file():
            print(f"MISSING: {src}", file=sys.stderr)
            return 1
        if _refuse(src):
            return 1
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied += 1
    for root, name, dst_name, role, report in SCRIPTS:
        src, dst = root / name, REPO / "util/ad-hoc" / dst_name
        if dst.exists():
            existed += 1
            flagged += _refuse(dst)  # re-check what is already archived (round 4, Lane R4-B)
            continue
        if not src.is_file():
            print(f"MISSING: {src}", file=sys.stderr)
            return 1
        if _refuse(src):
            return 1
        text = src.read_text(encoding="utf-8")
        head = _header(role, root.parent.name[:8], name, report, "#")
        if text.startswith("#!"):
            first, _, rest = text.partition("\n")
            out = first + "\n" + head + rest
        else:
            out = head + text
        if not args.dry_run:
            dst.write_text(out, encoding="utf-8")
        copied += 1
    print(f"{'would copy' if args.dry_run else 'copied'} {copied}, already present {existed} (re-checked; {flagged} failed a check)")
    if flagged:
        print(f"{flagged} archived file(s) failed the secret or e-mail check; review them by hand", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
