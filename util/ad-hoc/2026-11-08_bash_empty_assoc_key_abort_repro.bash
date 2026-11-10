#!/usr/bin/env bash
# Reproduce why the remount validator's first baseline gate PASSED a file that is not a fingerprint.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-08
# Status:     ad-hoc — investigation (defect reproduction)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-07_securityfs_remount_validate.bash (baseline_problem),
#             util/ad-hoc/2026-11-08_remount_validate_baseline_gate_check.py (cases C3 and C10 caught it),
#             notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md (§14)
#
# The first gate collected each line's key, the text before its first "=", into a bash associative array.
# The probe's report has section headers such as "==== 1. identity ====", whose key is the empty string.
# This script runs that same loop over three lines, the middle one a header, inside a command substitution,
# as the gate did. If bash rejects the empty subscript by abandoning the function, "reached the end" never
# prints and the captured output is empty. An empty answer was the gate's "no problem", so it passed.
#
# Usage: bash util/ad-hoc/2026-11-08_bash_empty_assoc_key_abort_repro.bash
# Prints what happened. Exit 0 always (it reports, it does not judge).
set -uo pipefail

collect_keys() {
    local -A present=()
    local line
    while IFS= read -r line; do
        [[ "$line" == *=* ]] && present["${line%%=*}"]=1
    done <<< "$(printf 'hold=a\n==== 1. identity ====\npid.dockerd=1\n')"
    echo "reached the end: ${#present[@]} keys collected"
}

echo "bash ${BASH_VERSION}"
captured="$(collect_keys 2>&1)"
echo "command substitution exit status: $?"
echo "captured output: [${captured}]"
if [[ "$captured" == *"reached the end"* ]]; then
    echo "RESULT: the function ran to its end; an empty key did not abort it"
else
    echo "RESULT: the function was abandoned before its last line; only the text above came back"
fi
