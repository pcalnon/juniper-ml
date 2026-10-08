#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — one-off; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Copy the Phase 11 review lanes' own probe scripts out of tmpfs into ``util/ad-hoc/``, one round at a time.

The ledger's Phase 11 (``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md``) rests in part on
executions those lanes ran: Lane 11-A2's independent reader of the raw transcripts, Lane 11-A3's instrument
mutations and stamp-skew measurement, and the B lanes' trigger and gap probes. Their scratch directories are
tmpfs, which a reboot deletes, so the scripts are copied here with a provenance header, the file's content
otherwise unchanged. A file holding a secret shape or an e-mail address (other than a ``noreply`` one) is
refused, and the run stops before writing anything.

Copied: each lane's OWN scripts. Not copied: the copies the lanes made of repo or canopy files (the census
scripts, the triage tool, canopy's ``test_poll_gating.py`` and ``canopy_constants.py``), and Lane 11-B1's and
Lane 11-B2's shell helpers (``canopy_grep*.sh``, ``canopy_diff.sh``, ``canopy_extract.sh``, ``extract.sh``),
which only extract and grep git objects and would fall under this repo's shellcheck hook. Lane 11-A2's directory
was outside this session's scratchpad (``/tmp/tmp.AFzDbAMY9I``); its scripts were first byte-copied to
``scratchpad/lane_probes/a2/``, which this reads.

Round 2's lanes (11-R2A and 11-R2B) are archived the same way. Not copied from them: Lane 11-R2A's copies of
canopy's ``test_poll_gating.py`` and ``canopy_constants.py``, and Lane 11-R2B's copies of the census scripts, the
two readers (old and new), the round-1 pass and the triage tool.

Round 3's lanes (11-R3A and 11-R3B) ran from 2026-10-05 to 2026-10-08, stopped in between by the API's usage
limit, so their probes carry the later date. Not copied from them: Lane 11-R3A's copy of the alias replay as of
``1b7cf44b`` and its outputs, and Lane 11-R3B's copies of the ledger, canopy's CHANGELOG and
``dashboard_manager.py``, its replay trees and its shell runners. Lane 11-R3B's directory was outside this
session's scratchpad (``/tmp/tmp.cIFAKjB6BD``); its scripts were first byte-copied to
``scratchpad/lane_probes/r3b/``, which this reads.

Round 4's lanes (11-R4A and 11-R4B) are archived the same way. Not copied from them: their outputs, mutated
transcripts and replay trees, and their copies of the ledger and of repo files. Round 5's (11-R5A and 11-R5B)
likewise, without Lane 11-R5A's copy of canopy's ``network_editor_panel.py`` or its shell runners. Round 6's
(11-R6A and 11-R6B) likewise, without their outputs, replay trees and copies of the ledger, the manual, the
CHANGELOG and the plan; Lane 11-R6A's directory was outside this session's scratchpad (``/tmp/tmp.y8saaB4Mk1``),
so its scripts were first byte-copied to ``scratchpad/lane_probes/r6a/``, which this reads.

Targets are ``util/ad-hoc/<date>_phase11_r<round>_<lane>_<name>``, the date 2026-10-05 for rounds 1 and 2 and
2026-10-08 for rounds 3 to 6. Paths and ports inside are the lane's own.

Usage:
    python3 util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py [--round 1|2|3|4|5|6] [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad")
OUT = Path(__file__).resolve().parent
LANES_R2 = {
    "a": (
        "lane11R2A.sffLXI",
        "Lane 11-R2A (measurement re-creation, on round 1's corrections)",
        ["horizon.py", "jitter_dist.py", "jitter_dist_old.py", "myreader.py", "myreplay.py", "selftest_on_old.py", "stall.py", "trig.py", "types.py"],
    ),
    "b": (
        "lane11R2B.ChB7s3/tools",
        "Lane 11-R2B (adversarial, on round 1's correction pass)",
        ["a_to_w.py", "pairing_blindspot.py", "peek.py", "peek2.py", "reenables.py", "replay_pass.py", "x_to_w.py"],
    ),
}
LANES_R3 = {
    "a": (
        "lane11R3A.THYyw0",
        "Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections)",
        [
            "break_test.py",
            "can015g_plans.py",
            "canopy_changelog.py",
            "canopy_changelog_057.py",
            "extra_checks.py",
            "myhorizon.py",
            "old_replay.py",
            "pending_check.py",
            "probe_archive_check.py",
            "rating_basis.py",
            "replay.py",
        ],
    ),
    "b": (
        "lane_probes/r3b",
        "Lane 11-R3B (adversarial, on round 2's correction pass)",
        ["altbreak_mut.py", "horizon.py", "late_to_x.py", "p1_headers.py", "peek.py", "r2b_case.py", "reenable_to_x.py", "verify_archive_r2.py"],
    ),
}
LANES_R4 = {
    "a": (
        "lane11R4A.mG5yhk",
        "Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections)",
        [
            "ast_compare.py",
            "codeql_replay.py",
            "guard_test.py",
            "ka_lines.py",
            "lane_interrupt.py",
            "myreader.py",
            "prescreen_sweep.py",
            "r3_probe_compare.py",
            "readers_compare.py",
            "replay_check.py",
        ],
    ),
    "b": (
        "r4b.5mnsCd",
        "Lane 11-R4B (adversarial, on round 3's correction pass)",
        ["breakmut.py", "codeql_check.py", "myreader.py", "open_basis.py", "prescreen_ph11.py", "readers_cmp.py", "replay.py", "triglag.py"],
    ),
}
LANES_R5 = {
    "a": (
        "lane11R5A.LBVRcz",
        "Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections)",
        ["cq_ast.py", "guard.py", "lane_transcripts.py", "prescreen_branch.py", "triglag.py"],
    ),
    "b": ("r5b.KImIJx", "Lane 11-R5B (adversarial, on round 4's correction pass)", ["codeql_r4.py", "trig.py"]),
}
LANES_R6 = {
    "a": (
        "lane_probes/r6a",
        "Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections)",
        ["canopy_manual.py", "cq_check.py", "prescreen_branch.py", "stage_cq.py", "transcripts.py", "transcripts2.py"],
    ),
    "b": (
        "r6b.lTWETu",
        "Lane 11-R6B (adversarial, on round 5's correction pass)",
        [
            "ast_eq.py",
            "cmd_head.py",
            "main_window.py",
            "noB_scan.py",
            "prescreen_branch.py",
            "pyc_header.py",
            "r4b_noB.py",
            "report_lengths.py",
            "result_flags.py",
            "run_paths.py",
            "verbatim_check.py",
        ],
    ),
}
#: each round's archive date: the date in the targets' names, the header and the round's report file
ROUND_DATE = {1: "2026-10-05", 2: "2026-10-05", 3: "2026-10-08", 4: "2026-10-08", 5: "2026-10-08", 6: "2026-10-08"}
LANES = {
    "a1": ("lane11A1.4njt8I", "Lane 11-A1 (measurement re-creation, source-first)", ["extract_interval.py", "fire_ranges.py", "lane_types.py", "late_ranges.py", "write_pairs.py"]),
    "a2": (
        "lane_probes/a2",
        "Lane 11-A2 (measurement re-creation, raw-transcript-first)",
        ["backdate.py", "enabled_check.py", "mech.py", "myreader.py", "owngaps.py", "replay_innermost.py", "short_enabled.py", "triggers.py", "variants.py", "windows.py"],
    ),
    "a3": (
        "lane11A3.psxzxh/tools",
        "Lane 11-A3 (measurement re-creation, instrument-adequacy-first)",
        [
            "dump.py",
            "enabled_check.py",
            "own_accounting.py",
            "pairing.py",
            "pyc_check.py",
            "readme_replay.py",
            "rt_mut.py",
            "spot.py",
            "stamp_skew.py",
            "stamp_skew2.py",
            "synth_pred.py",
            "wd_chance.py",
            "wd_more.py",
            "wd_mut.py",
        ],
    ),
    "b1": ("lane11B1.oCpUdY", "Lane 11-B1 (adversarial, dispositions and ratings, fold side)", ["gaps.py", "logconn.py", "misc.py", "triggers.py", "window.py"]),
    "b2": ("lane11B2.KZI9rh", "Lane 11-B2 (adversarial, claims beyond evidence, escalate side)", ["model6.py", "probe1.py", "probe2.py", "probe3.py", "probe4.py", "probe5.py", "probe7.py"]),
}
SECRET = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}|AGE-SECRET-KEY-|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def header(lane_label: str, src: Path, rnd: int = 1) -> str:
    date = ROUND_DATE[rnd]
    lines = [
        f"ARCHIVED VERBATIM, {date}: a probe from round {rnd} of the canopy E2E ledger's Phase 11 validation.",
        f"Source: a tmpfs scratch directory, {src.parent.name}/{src.name}",
        f"Written by {lane_label}, a review lane (a subagent), not by the orchestrator.",
        "Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon",
        "Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)",
        "Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;",
        f"  reports/e2e-canopy-2026-09-02/consensus/{date}_validator_reports_phase11_round{rnd}.md",
        "Everything below this block is the lane's file, unmodified.",
    ]
    bar = "# " + "-" * 75
    return "\n".join([bar] + [f"# {x}" for x in lines] + [bar]) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--round", type=int, choices=(1, 2, 3, 4, 5, 6), default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    plan, refused = [], []
    for lane, (dirname, label, files) in {1: LANES, 2: LANES_R2, 3: LANES_R3, 4: LANES_R4, 5: LANES_R5, 6: LANES_R6}[args.round].items():
        for name in files:
            src = SCRATCH / dirname / name
            text = src.read_text(encoding="utf-8")
            emails = [e for e in EMAIL.findall(text) if "noreply" not in e]
            if SECRET.search(text) or emails:
                refused.append(f"{dirname}/{name}")
                continue
            body, shebang = text, ""
            if body.startswith("#!"):
                shebang, body = body.split("\n", 1)
                shebang += "\n"
            plan.append((OUT / f"{ROUND_DATE[args.round]}_phase11_r{args.round}_{lane}_{name}", shebang + header(label, src, args.round) + body))
    if refused:
        print("REFUSED (secret shape or e-mail address):", ", ".join(refused), file=sys.stderr)
        return 1
    for dst, _content in plan:
        if dst.exists():
            print(f"REFUSED: {dst.name} exists", file=sys.stderr)
            return 1
    for dst, content in plan:
        print(("would write " if args.dry_run else "wrote ") + str(dst.relative_to(OUT.parents[1])))
        if not args.dry_run:
            dst.write_text(content, encoding="utf-8")
    print(f"{len(plan)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
