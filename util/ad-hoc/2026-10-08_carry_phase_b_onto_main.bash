#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File:          2026-10-08_carry_phase_b_onto_main.bash
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
# -----------------------------------------------------------------------------
# Purpose: carry the frozen Phase B commit (c3d0e890, local-only, never pushed)
# onto a branch cut from current origin/main, in THIS worktree.
#
# Phase B's files fall into three groups:
#   - hot files main has moved since Phase B's base e509353e (CHANGELOG.md,
#     docs/REFERENCE.md, ci.yml, AGENTS.md): NOT taken; their Phase B hunks are
#     re-applied by hand onto main's copies;
#   - files that #2179 landed on main ahead of Phase B (the record, its header,
#     the archiver and two helpers): main's copy is newer and is kept -- the
#     2026-10-04 handoff forbids restoring them from c3d0e890;
#   - everything else: unmoved on main, so c3d0e890's copy is checked out.
#
# Usage: bash util/ad-hoc/2026-10-08_carry_phase_b_onto_main.bash [--dry-run]
# -----------------------------------------------------------------------------
set -euo pipefail

FROZEN=c3d0e890
BASE=e509353e
DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

SKIP_RE='^(\.github/workflows/ci\.yml|AGENTS\.md|CHANGELOG\.md|docs/REFERENCE\.md|notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD\.md|util/ad-hoc/2026-10-04_archive_phase_b_round_reports\.py|util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER\.md\.in|util/ad-hoc/2026-10-04_save_subagent_report\.py|util/ad-hoc/2026-10-04_wip_worktree_delta\.py)$'

mapfile -t all < <(git diff --name-only "$BASE" "$FROZEN")
take=()
for f in "${all[@]}"; do
    if [[ "$f" =~ $SKIP_RE ]]; then
        echo "skip  $f"
        continue
    fi
    # Refuse if main moved the file since Phase B's base: it would be reverted.
    if [[ -n "$(git log --oneline "$BASE..origin/main" -- "$f")" ]]; then
        echo "REFUSE $f: moved on origin/main since $BASE" >&2
        exit 2
    fi
    take+=("$f")
    echo "take  $f"
done

echo "# ${#take[@]} file(s) to take from $FROZEN"
if (( DRY == 0 )); then
    git checkout "$FROZEN" -- "${take[@]}"
    git reset -q -- "${take[@]}"
fi
