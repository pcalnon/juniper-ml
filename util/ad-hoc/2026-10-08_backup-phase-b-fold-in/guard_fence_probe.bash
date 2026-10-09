#!/usr/bin/env bash
# Probe the design's P0 step 10 guard dry-run block (the clearing script's one FENCE_EDITS block) with stubs.
#
# Project:     juniper-ml
# Sub-Project: backup infrastructure
# Author:      Paul Calnon
# Created:     2026-10-08
# Status:      ad-hoc -- evidence for the round-3 fold-in (R3B NIT-7: `<id>` pasted unsubstituted)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py (fence_edit, P0 step 10)
#
# Usage: guard_fence_probe.bash <file-holding-the-block-body>
# Runs no guard, no API client and no sudo: `python3` (API calls only) and `sudo` are shell functions.
# An interactive shell DISCARDS a line that is a syntax error and runs the next; case "unsubstituted" models
# that by dropping the `id=<id>` line, with a stale `url` already in the session.
set -uo pipefail

body="${1:?usage: $0 <block-body-file>}"
mapfile -t L < "${body}"
[[ "${L[1]}" == "id=<id>" ]] || { echo "FATAL: line 2 is not id=<id>" >&2; exit 2; }
rest="$(printf '%s\n' "${L[@]:2}")"
# The stubs are shell TEXT for the child bash, so their expansions are meant to stay literal here.
# shellcheck disable=SC2016
stubs='sudo(){ echo "STUB guard ran with ${5:-?}"; return 0; }
python3(){ if [[ "$1" == -c ]]; then command python3 -I -c "$2"; elif [[ "${EXPORT_FAILS:-0}" == 1 ]]; then return 1; else echo "{\"Backup\":{\"TargetURL\":\"file:///real/job-$4\"}}"; fi; }'

run() {
    local name="$1" idline="$2"
    echo "--- ${name}"
    bash -c "${stubs}
url=file:///stale/typed-by-hand
${L[0]}
${idline}
${rest}" 2>&1
}
run "unsubstituted (line 2 discarded, stale url)" ""
run "id=7" "id=7"
run "id=abc" "id=abc"
EXPORT_FAILS=1 run "id=7, export fails" "id=7"
