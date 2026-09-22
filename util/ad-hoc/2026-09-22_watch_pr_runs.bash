#!/usr/bin/env bash
# Emit one line per WORKFLOW RUN on a branch as it completes; exit when none are in flight.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- CI observation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-09-22_watch_pr_regression_checks.bash (the check-level form, and why it is wrong)
#
# WHY RUNS AND NOT CHECKS. A check entry appears only once its job starts reporting, so a queued
# workflow contributes NOTHING to `gh pr checks`. On 2026-09-22 that made a check-level watcher
# declare a 25-check pipeline finished twice: once on a single passing check, and again on a
# "stable" count of two while the whole CI/CD Pipeline sat queued with no entries at all. The
# run list shows a queued workflow as `queued`/`in_progress`, so it cannot be fooled the same way.
#
# Also emits on EVERY terminal conclusion, not just success -- a watcher that greps for green is
# silent through a red run, and silence is indistinguishable from "still going".
set -uo pipefail

BRANCH="${1:?usage: $0 <branch> [poll-seconds]}"
INTERVAL="${2:-30}"
REPO="${REPO:-pcalnon/juniper-ml}"
prev=""

while true; do
    raw="$(gh api "repos/${REPO}/actions/runs?branch=${BRANCH}&per_page=40" \
        --jq '.workflow_runs[] | "\(.id)\t\(.name)\t\(.status)\t\(.conclusion // "-")"' 2>/dev/null)" || raw=""

    if [[ -z "${raw}" ]]; then
        sleep "${INTERVAL}"
        continue
    fi

    cur="$(awk -F'\t' '$3 == "completed" { printf "%s: %s\n", $2, $4 }' <<< "${raw}" | sort -u)"
    comm -13 <(printf '%s\n' "${prev}") <(printf '%s\n' "${cur}")
    prev="${cur}"

    inflight="$(awk -F'\t' '$3 != "completed"' <<< "${raw}" | wc -l)"
    if (( inflight == 0 )); then
        failed="$(awk -F'\t' '$3 == "completed" && $4 != "success" && $4 != "skipped" && $4 != "neutral"' <<< "${raw}" | wc -l)"
        echo "ALL-RUNS-COMPLETE: ${failed} run(s) not successful"
        break
    fi
    sleep "${INTERVAL}"
done
