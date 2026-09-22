#!/usr/bin/env bash
# Emit one line per regression check as it reaches a terminal state, then exit.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- CI observation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/wait_for_checks.py (the blocking form; this one streams events instead)
#
# Written because the worktree isolation shim refuses a compound inline poll loop, and because a
# monitor that greps only for success is silent through a crash -- so this emits on EVERY
# terminal bucket (pass, fail, cancel, skipping), not just pass.
set -uo pipefail

PR="${1:?usage: $0 <pr-number> [name-filter-regex]}"
FILTER="${2:-Regression}"
prev=""

while true; do
    s="$(gh pr checks "${PR}" --json name,bucket 2>/dev/null)" || s='[]'
    cur="$(jq -r --arg f "${FILTER}" \
        '.[] | select(.name|test($f)) | select(.bucket!="pending") | "\(.name): \(.bucket)"' \
        <<< "${s}" | sort)"
    comm -13 <(printf '%s\n' "${prev}") <(printf '%s\n' "${cur}")
    prev="${cur}"
    if jq -e --arg f "${FILTER}" \
        '[.[] | select(.name|test($f))] | (length > 0) and (all(.[]; .bucket != "pending"))' \
        <<< "${s}" > /dev/null 2>&1; then
        echo "ALL-TERMINAL: every check matching /${FILTER}/ has finished"
        break
    fi
    sleep 30
done
