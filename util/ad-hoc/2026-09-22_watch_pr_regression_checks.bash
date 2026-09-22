#!/usr/bin/env bash
# Emit one line per PR check as it reaches a terminal state, then exit when none are pending.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- CI observation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/wait_for_checks.py (the blocking form; this one streams events instead)
#
# TWO traps this encodes, both hit on 2026-09-22:
#
#   1. `gh pr checks --json` DOES NOT EXIST in gh 2.46.0, the version installed here (the same
#      version whose `gh pr edit` is broken). A watcher written against --json fails every poll,
#      falls back to an empty result, and therefore NEVER FIRES -- a silent no-op that is
#      indistinguishable from "nothing has finished yet". Parse the plain tab-separated output.
#
#   2. A monitor that greps only for success is silent through a failure. This emits on EVERY
#      terminal bucket -- pass, fail, cancel, skipping -- so a red check is an event, not a
#      continued silence.
#
# Plain `gh pr checks` output is TAB-separated: name, bucket, elapsed, url.
set -uo pipefail

PR="${1:?usage: $0 <pr-number> [name-filter-regex]}"
FILTER="${2:-.}"
INTERVAL="${WATCH_INTERVAL:-30}"
prev=""

while true; do
    raw="$(gh pr checks "${PR}" 2>/dev/null)" || raw=""
    if [[ -z "${raw}" ]]; then
        # No checks reported yet (a fresh head), or gh failed. Either way, keep waiting rather
        # than declaring victory on an empty set -- an empty set is not "all terminal".
        sleep "${INTERVAL}"
        continue
    fi

    cur="$(awk -F'\t' -v f="${FILTER}" \
        '$1 ~ f && $2 != "pending" { printf "%s: %s\n", $1, $2 }' <<< "${raw}" | sort)"
    comm -13 <(printf '%s\n' "${prev}") <(printf '%s\n' "${cur}")
    prev="${cur}"

    pending="$(awk -F'\t' -v f="${FILTER}" '$1 ~ f && $2 == "pending"' <<< "${raw}" | wc -l)"
    total="$(awk -F'\t' -v f="${FILTER}" '$1 ~ f' <<< "${raw}" | wc -l)"

    # A PARTIALLY POPULATED set looks terminal. Right after a push, GitHub reports only the
    # workflows that have registered so far -- on 2026-09-22 that was a single check, which
    # passed, and a "total > 0 && pending == 0" test declared the whole run finished while
    # twenty more were still queuing. Require the check COUNT to be stable across two
    # consecutive polls as well, so a still-growing set cannot be mistaken for a finished one.
    if (( total > 0 && pending == 0 )) && [[ "${total}" == "${last_total:-}" ]]; then
        failed="$(awk -F'\t' -v f="${FILTER}" '$1 ~ f && $2 == "fail"' <<< "${raw}" | wc -l)"
        echo "ALL-TERMINAL: ${total} check(s) finished and the count is stable, ${failed} failing"
        break
    fi
    last_total="${total}"
    sleep "${INTERVAL}"
done
