#!/usr/bin/env bash
# Re-assemble the backup arc's Phase B consensus record from its header and its reports, in order.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-10-05
# Status:      ad-hoc -- validation record
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py (the archiver this drives)
#              util/ad-hoc/2026-10-05_match_reports_to_final_messages.py (checks origin lines by content)
#              util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in (the header)
#              notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md (the record)
#
# One ordered list, ENTRIES, names every report: its heading, the file it was saved to, and its origin.
# Both modes read that list, so they cannot disagree about which reports exist.
#
#   (default)     Every report the record already holds is lifted from the record (--prefer-record); only
#                 the others are read from their files. With the record and header on main, nothing else is
#                 needed until a new report is added.
#   --from-files  Every report is read from its file. Round 2's files and the 2026-10-03 handoff's validation
#                 are untracked in the worktree cached-swinging-summit (byte-identical to the files the lanes
#                 wrote; override with ROUND2_DIR); round 3's are untracked in worktree sorted-stargazing-garden,
#                 and the 2026-10-08 fold-in and round 4-7 reports are untracked in worktree golden-floating-willow
#                 (session 097ae87b). The record is their durable copy; the files were kept out of the commit
#                 because verbatim reports do not pass markdownlint outside the record's disable block.
#                 A missing file is refused, never skipped.
#   --check       Passed to the archiver: nothing is written; exit 0 if the result equals the record byte for
#                 byte, 1 if it differs, 2 if a guard refuses.
#
# The archiver's guards, and the option that overrides each (passed straight through):
#   - a report file that exists but differs from the archived report, body or origin  --replace "<heading>"
#   - a run that would drop an archived report, or record text outside every section  --allow-drop
#   - a header file that differs from the record's header                             --accept-header
# Run with --check first, and read what it refuses, before overriding anything.
#
# Adding a report (round 4's, say): save it the moment it lands with
# util/ad-hoc/2026-10-04_save_subagent_report.py, append "<heading>|<file>|<origin>" to ENTRIES, and run.
# Completing the header's "Disposition of round 3" is a header change: run with --accept-header.

set -euo pipefail

cd "$(dirname "$0")/../.."
RECORD=notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md
HEADER=util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in
ARCHIVER=util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py

v="${ROUND2_DIR:-/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit/util/ad-hoc/2026-10-03_backup-phase-b-validation}"
f=util/ad-hoc/2026-10-04_ml2115_fix_forward
r=util/ad-hoc/2026-10-04_backup-phase-b-round3
lane="the report file the lane wrote itself, in session 652c1204's scratch directory, on"
saved="the lane's final message, saved from its transcript by session c9277a65 on"
g=util/ad-hoc/2026-10-08_backup-phase-b-fold-in
q=util/ad-hoc/2026-10-08_backup-phase-b-round4
saved8="the lane's report, saved from its transcript by session 097ae87b on 2026-10-08"

ENTRIES=(
    "Round 2 — the common brief|$v/BRIEF_COMMON.md|the brief session 652c1204 wrote for round 2's lanes on 2026-10-03"
    "Round 2, lane A — option names, product behaviour, unit directives|$v/A.md|$lane 2026-10-03"
    "Round 2, lane B — consequence|$v/B.md|$lane 2026-10-03"
    "Round 2, lane C — run the things|$v/C.md|$lane 2026-10-03"
    "Round 2, the ml#2114 lane|$v/pr2114.md|$lane 2026-10-03"
    "Round 2, the ml#2115 lane|$v/pr2115.md|$lane 2026-10-03"
    "The 2026-10-03 handoff's validation|$v/handoff_validation.md|$lane 2026-10-04"
    "Fix-forward lane F1 — product fidelity|$f/F1.md|$saved 2026-10-04"
    "Fix-forward lane F2 — consequences and regressions|$f/F2.md|$saved 2026-10-04"
    "Round 3 — the common brief|$r/BRIEF_COMMON.md|the brief session c9277a65 wrote for round 3's lanes on 2026-10-04"
    "Round 3, lane A — fold-in fidelity|$r/R3A.md|$saved 2026-10-04"
    "Round 3, lane B — procedure consequences|$r/R3B.md|$saved 2026-10-05, after the lane was resumed from a usage-limit stop"
    "Round 3, lane C — run the things|$r/R3C.md|$saved 2026-10-04"
    "The 2026-10-04 handoff's validation|$r/HV.md|$saved 2026-10-05"
    "The 2026-10-04 handoff's re-validation|$r/HV2.md|$saved 2026-10-05"
    "The 2026-10-04 handoff's third validation|$r/HV3.md|$saved 2026-10-05"
    "Round 3's fold-in — the common brief|$g/BRIEF_COMMON.md|the brief session 097ae87b wrote for the fold-in lanes on 2026-10-08"
    "Round 3's fold-in, lane C1 — wrapper, installer, contract and units|$g/C1.md|$saved8"
    "Round 3's fold-in, lane C2 — re-key, gate and hand start|$g/C2.md|$saved8"
    "Round 3's fold-in, lane P — design and assessment prose|$g/P.md|$saved8"
    "Round 3's fold-in, lane P (second pass, the code lanes' prose)|$g/P_pass2.md|$saved8"
    "Round 4 — the common brief|$g/BRIEF_ROUND4.md|the brief session 097ae87b wrote for round 4's lanes on 2026-10-08 (round 5's lanes used it too)"
    "Round 4, lane A — fold-in fidelity|$q/R4A.md|$saved8"
    "Round 4, lane B — procedure consequences, the sole copy|$q/R4B.md|$saved8"
    "Round 4, lane C — run the things|$q/R4C.md|$saved8"
    "Round 4's fold-in, lane C1|$g/C1_round4.md|$saved8"
    "Round 4's fold-in, lane C2|$g/C2_round4.md|$saved8"
    "Round 4's fold-in, lane P|$g/P_round4.md|$saved8"
    "Round 4's fold-in, lane P (second pass, the code lanes' prose)|$g/P_round4b.md|$saved8"
    "Round 5, lane A — code confirmation|$q/R5A.md|$saved8"
    "Round 5, lane B — procedure confirmation|$q/R5B.md|$saved8"
    "Round 5's fold-in, lane C1|$g/C1_round5.md|$saved8"
    "Round 5's fold-in, lane C2|$g/C2_round5.md|$saved8"
    "Round 5's fold-in, lane P|$g/P_round5.md|$saved8"
    "Round 5's fold-in, lane P (second pass, the code lanes' prose)|$g/P_round5b.md|$saved8"
    "Round 6 — confirmation of round 5's fold-in|$q/R6.md|$saved8"
    "Round 6's fold-in, lane C1|$g/C1_round6.md|$saved8"
    "Round 6's fold-in, lane C2|$g/C2_round6.md|$saved8"
    "Round 6's fold-in, lane P|$g/P_round6.md|$saved8"
    "Round 7 — confirmation of round 6's fold-in|$q/R7.md|$saved8"
    "Round 7's fold-in, lane C2|$g/C2_round7.md|$saved8"
    "Round 7's fold-in, lane P|$g/P_round7.md|$saved8"
)

mode=record
passed=()
while (($#)); do
    case "$1" in
        --from-files) mode=files ;;
        --check | --allow-drop | --accept-header) passed+=("$1") ;;
        --replace)
            if (($# < 2)); then
                echo "--replace needs a heading" >&2
                exit 64
            fi
            passed+=(--replace "$2")
            shift
            ;;
        *)
            echo "usage: $0 [--from-files] [--check] [--allow-drop] [--accept-header] [--replace <heading>]..." >&2
            exit 64
            ;;
    esac
    shift
done

args=()
for entry in "${ENTRIES[@]}"; do
    IFS='|' read -r heading file origin <<< "$entry"
    if [[ -z "$heading" || -z "$file" || -z "$origin" ]]; then
        echo "malformed entry (want heading|file|origin): $entry" >&2
        exit 64
    fi
    args+=(--report "$heading=file:$file|$origin")
done
if [[ "$mode" == record ]]; then
    args+=(--prefer-record "$RECORD")
fi
PYTHONDONTWRITEBYTECODE=1 python3 "$ARCHIVER" --header "$HEADER" --out "$RECORD" "${passed[@]}" "${args[@]}"
