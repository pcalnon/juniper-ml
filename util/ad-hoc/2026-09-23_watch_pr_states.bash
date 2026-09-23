#!/usr/bin/env bash
# Emit ONE line per PR each time its merge-relevant state changes; exit when every PR is closed.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-23
# Status:     ad-hoc -- merge shepherding (a `Monitor` event source)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-09-22_shepherd_automerge.bash (syncs ONE PR whenever it goes BEHIND)
#
# WHY NOT THE SHEPHERD. With several armed PRs in one strict-checks repo, running one shepherd per
# PR re-syncs EVERY PR each time any of them merges, so all of them re-run CI at once and all but one
# go BEHIND again when the first lands. This script only REPORTS; the operator syncs one PR at a
# time, in a chosen order, as each merge lands.
#
# It does not arm, sync, or merge. It reads the REST pull object (`auto_merge` is on it, so no
# GraphQL budget is spent) and prints a line only when (state, merged, mergeable_state, head, armed)
# changes. A transient API failure is not a state: that PR is skipped for the round.
#
# NOT A CHECKS WAITER. "mergeable_state" is GitHub's summary, not the required-context set; use
# util/wait_for_checks.py (anchored on the ruleset's required contexts) when the question is
# "are the checks done".
#
# Usage:  util/ad-hoc/2026-09-23_watch_pr_states.bash juniper-canopy:664 juniper-ml:2036 ...
# Env:    OWNER (default pcalnon), INTERVAL seconds (default 60)
set -uo pipefail

OWNER="${OWNER:-pcalnon}"
INTERVAL="${INTERVAL:-60}"

if (( $# == 0 )); then
    echo "usage: $0 <repo>:<pr> [<repo>:<pr> ...]" >&2
    exit 2
fi

declare -A last=()
declare -A done_=()

while true; do
    open_count=0
    for spec in "$@"; do
        [[ -n "${done_[${spec}]:-}" ]] && continue
        repo="${spec%%:*}"
        pr="${spec##*:}"
        raw="$(gh api "repos/${OWNER}/${repo}/pulls/${pr}" \
            --jq '"\(.state)\t\(.merged)\t\(.mergeable_state)\t\(.head.sha[0:8])\t\(.auto_merge != null)"' 2>/dev/null)" || raw=""
        if [[ -z "${raw}" ]]; then
            open_count=$(( open_count + 1 ))
            continue
        fi
        IFS=$'\t' read -r state merged mstate sha armed <<< "${raw}"
        if [[ "${raw}" != "${last[${spec}]:-}" ]]; then
            if [[ "${merged}" == "true" ]]; then
                echo "$(date -u +%H:%M:%SZ) ${spec} MERGED (head ${sha})"
            elif [[ "${state}" != "open" ]]; then
                echo "$(date -u +%H:%M:%SZ) ${spec} CLOSED-UNMERGED (head ${sha}) -- investigate"
            else
                echo "$(date -u +%H:%M:%SZ) ${spec} ${mstate} head=${sha} armed=${armed}"
            fi
            last[${spec}]="${raw}"
        fi
        if [[ "${state}" != "open" ]]; then
            done_[${spec}]=1
        else
            open_count=$(( open_count + 1 ))
        fi
    done
    if (( open_count == 0 )); then
        echo "ALL-CLOSED"
        exit 0
    fi
    sleep "${INTERVAL}"
done
