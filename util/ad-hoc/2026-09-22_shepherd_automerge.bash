#!/usr/bin/env bash
# Shepherd a PR with NATIVE auto-merge already armed: sync it whenever it goes BEHIND, and exit
# when it reaches a terminal state.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- merge shepherding
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/safe_merge.py (the pinned-net form this exists to replace in a contended lane)
#
# WHY THIS EXISTS. juniper-ml's main sets strict_required_status_checks_policy=true, so every merge
# to main puts every other open PR BEHIND and forces a fresh CI cycle. main merges every ~10-28 min;
# CI takes ~10-25 min. util/safe_merge.py pins its auto-merge net to a SHA, so each re-sync strands
# the net -- it refused ml#1999 with "went BEHIND 3 times without a stable green head".
#
# GitHub's native auto-merge tracks the PR, not a SHA, so it survives an update-branch and completes
# the merge SERVER-SIDE the instant the last required check goes green -- no polling window for
# another session to slip into. The one thing it does NOT do is sync a BEHIND branch. That is this
# script's whole job.
#
# It does NOT arm anything and does NOT merge: arming is a separate, deliberate act, and a shepherd
# that could arm could arm the wrong thing. If the net is found disarmed it STOPS and says so,
# because a disarmed net means something rejected the merge and that deserves a human read.
set -uo pipefail

PR="${1:?usage: $0 <pr-number> [poll-seconds] [max-minutes]}"
INTERVAL="${2:-60}"
MAX_MIN="${3:-90}"
REPO="${REPO:-pcalnon/juniper-ml}"
OWNER="${REPO%%/*}"
NAME="${REPO##*/}"

deadline=$(( $(date +%s) + MAX_MIN * 60 ))
synced=0

while true; do
    raw="$(gh api "repos/${REPO}/pulls/${PR}" \
        --jq '"\(.state)\t\(.merged)\t\(.mergeable_state)\t\(.head.sha)"' 2>/dev/null)" || raw=""

    if [[ -z "${raw}" ]]; then
        # A transient API failure must not be read as a terminal state -- safe_merge exited 3 on
        # exactly this ("dial tcp ... i/o timeout") earlier in this same arc. Keep waiting.
        echo "  (api unreachable; retrying)"
        sleep "${INTERVAL}"
        continue
    fi

    IFS=$'\t' read -r state merged mstate sha <<< "${raw}"

    if [[ "${merged}" == "true" ]]; then
        echo "MERGED ${PR}: head was ${sha:0:8} (${synced} re-sync(s) performed)"
        exit 0
    fi
    if [[ "${state}" != "open" ]]; then
        echo "TERMINAL-NOT-MERGED ${PR}: state=${state} -- investigate, do not re-arm blindly"
        exit 2
    fi

    armed="$(gh api graphql -f query="{repository(owner:\"${OWNER}\",name:\"${NAME}\"){pullRequest(number:${PR}){autoMergeRequest{mergeMethod}}}}" \
        --jq '.data.repository.pullRequest.autoMergeRequest.mergeMethod // "NONE"' 2>/dev/null)" || armed="UNKNOWN"
    if [[ "${armed}" == "NONE" ]]; then
        echo "DISARMED ${PR}: auto-merge net is gone at ${sha:0:8} (mergeable_state=${mstate}) -- stopping"
        exit 3
    fi

    if [[ "${mstate}" == "behind" ]]; then
        echo "  BEHIND at ${sha:0:8} -- syncing (each sync costs a fresh CI cycle)"
        if gh api -X PUT "repos/${REPO}/pulls/${PR}/update-branch" >/dev/null 2>&1; then
            synced=$(( synced + 1 ))
        else
            echo "  (update-branch rejected; will retry)"
        fi
    else
        echo "  ${mstate} at ${sha:0:8} (auto-merge ${armed} armed)"
    fi

    if (( $(date +%s) >= deadline )); then
        echo "DEADLINE ${PR}: still open after ${MAX_MIN} min, net still ${armed} -- it may yet land"
        exit 4
    fi
    sleep "${INTERVAL}"
done
