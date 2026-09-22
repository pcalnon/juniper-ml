#!/usr/bin/env bash
# Run every `python3 -m unittest` invocation that ci.yml's regression step runs, locally.
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: CI parity
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
# Status:      ad-hoc -- investigation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     juniper-ml#2002
#
# WHY: juniper-ml's CI regression list is HAND-MAINTAINED (see docs/REFERENCE.md § Test Suite
# Reference), so "the suites I touched pass" is not "CI passes". On #2002 a change to
# tests/test_run_suite.py was caught by tests/test_env_repr_safety.py -- a suite in the CI list
# that the author had no reason to run, because it lints OTHER test files rather than testing
# the code under change. That class is invisible to any locally-chosen subset.
#
# Prints a PASS/FAIL line per suite and exits non-zero if any failed.
#
# TWO CAVEATS -- this is CI PARITY, not CI:
#
#   1. `/tmp` is tmpfs on this host, and at least one suite legitimately refuses to run there.
#      `tests/test_duplicati_scheduled_backup.py` fails locally with "…/_duplicati_tmp is tmpfs
#      (RAM-backed); refusing to stage 500 MB volumes in memory" -- the guard working as
#      designed, on a disk-backed CI runner it passes. Before blaming a local failure on your
#      change, diff the suite and its subject against origin/main; if both are identical, it is
#      the host.
#   2. A long-lived worktree drifts BEHIND main, and these suites run against whatever the
#      worktree holds. This one was 44 files behind when the script was written. A green run
#      here does not prove a green run on a branch cut from current main.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 2
WORKFLOW=".github/workflows/ci.yml"
[[ -f "${WORKFLOW}" ]] || { echo "no ${WORKFLOW} here" >&2; exit 2; }

mapfile -t suites < <(grep -oE 'python3 -m unittest (-v )?tests/[A-Za-z0-9_]+\.py' "${WORKFLOW}" |
    grep -oE 'tests/[A-Za-z0-9_]+\.py' | sort -u)

echo "ci.yml regression list: ${#suites[@]} suites"
failed=0
for suite in "${suites[@]}"; do
    if [[ ! -f "${suite}" ]]; then
        printf 'MISSING %s\n' "${suite}"
        failed=$((failed + 1))
        continue
    fi
    mod="${suite%.py}"
    mod="${mod//\//.}"
    if out=$(python3 -m unittest "${mod}" 2>&1); then
        printf 'pass    %-58s %s\n' "${suite}" "$(echo "${out}" | grep -oE '^Ran [0-9]+ tests' || true)"
    else
        printf 'FAIL    %-58s\n' "${suite}"
        echo "${out}" | grep -E '^(FAIL|ERROR):' | sed 's/^/          /'
        failed=$((failed + 1))
    fi
done

echo "-----"
if ((failed)); then
    echo "${failed} suite(s) FAILED"
    exit 1
fi
echo "all ${#suites[@]} suites passed"
