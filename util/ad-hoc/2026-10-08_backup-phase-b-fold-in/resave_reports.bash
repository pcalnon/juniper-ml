#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File:          2026-10-08_backup-phase-b-fold-in/resave_reports.bash
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
# -----------------------------------------------------------------------------
# Purpose: re-save session 097ae87b's lane reports (2026-10-08) from their
# subagent transcripts, verbatim. Needed once already: a pre-commit run over a
# file list that still included the untracked report copies let the whitespace
# fixers rewrite them on disk, so they no longer matched the record (which was
# assembled before the run and is the verbatim copy). Run it, then
# `2026-10-05_reassemble_phase_b_record.bash --check` must say IDENTICAL.
#
# Each line: <agent-id> <heading prefix> <output file>.
# Usage: bash util/ad-hoc/2026-10-08_backup-phase-b-fold-in/resave_reports.bash [<tasks-dir>]
# -----------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/../../.."
TASKS="${1:-${HOME}/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-golden-floating-willow/097ae87b-7a4c-4970-9f46-d052521e17c7/subagents}"
SAVE=util/ad-hoc/2026-10-08_save_subagent_report_by_heading.py
g=util/ad-hoc/2026-10-08_backup-phase-b-fold-in
q=util/ad-hoc/2026-10-08_backup-phase-b-round4
C1=af8deb5d02e79f8c8
C2=ae11ddab82ec7af39
P=a3228333a9e753ae6

save() { PYTHONDONTWRITEBYTECODE=1 python3 "$SAVE" --tasks-dir "$TASKS" --agent "$1" --heading "$2" --out "$3"; }

save "$C1" "## Lane C1 report: backup Phase B round-3" "$g/C1.md"
save "$C2" "# Lane C2 report: Phase B round-3" "$g/C2.md"
save "$P" "I've finished all nine work items" "$g/P.md"
save "$P" "Second pass is done" "$g/P_pass2.md"
save a1067ee0f54a5ab90 "# Phase B round 4" "$q/R4B.md"
save aa97a51df0dc3f8cf "# Phase B round 4" "$q/R4A.md"
save a37bdddbe6b47b206 "# Phase B round 4" "$q/R4C.md"
save "$C1" "## Lane C1 report: backup Phase B round-4" "$g/C1_round4.md"
save "$C2" "# Lane C2 report: Phase B round-4" "$g/C2_round4.md"
save "$P" "My round-4 items" "$g/P_round4.md"
save "$P" "C1's and C2's round-4 prose" "$g/P_round4b.md"
save a440741121f775352 "# Phase B round 5" "$q/R5A.md"
save ae0ab5376baf90c5e "# Phase B round 5" "$q/R5B.md"
save "$C1" "## Lane C1 report: backup Phase B round-5" "$g/C1_round5.md"
save "$C2" "# Lane C2 report: Phase B round-5" "$g/C2_round5.md"
save "$P" "Round 5 is folded" "$g/P_round5.md"
save "$P" "C1's and C2's round-5 prose" "$g/P_round5b.md"
save aa6be6fea6bbc7507 "# Phase B round 6" "$q/R6.md"
save "$C1" "## Lane C1 report: backup Phase B round-6" "$g/C1_round6.md"
save "$C2" "# Lane C2 report: Phase B round-6" "$g/C2_round6.md"
save "$P" "Round 6 is folded" "$g/P_round6.md"
save ac8deb6e8659240cb "# Phase B round 7" "$q/R7.md"
save "$C2" "# Lane C2: round-7" "$g/C2_round7.md"
save "$P" "Round 7 is folded" "$g/P_round7.md"
