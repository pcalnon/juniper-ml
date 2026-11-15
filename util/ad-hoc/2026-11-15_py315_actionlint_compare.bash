#!/usr/bin/env bash
# Run actionlint (schema + expression checks only; shellcheck and pyflakes off) on base and branch copies of
# a repo's changed workflows, and print the findings of each, with file paths stripped so the two compare.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-15
# Status:     ad-hoc -- investigation (verification for juniper-cascor#759 and juniper-cascor-worker#228)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-15_py315_compare_legs.bash (the same base/branch layout)
#
# Usage: actionlint_compare.bash <label> <base-dir> <worktree-workflows-dir> <out-dir> <file> [<file> ...]
#   As first run, the outputs went to this script's own directory; here they go to <out-dir> (use a tmp/ directory).
#   Negative control used with it: a copy with `matrix.experimental` misspelled must be flagged (it was, exit 1).
set -uo pipefail
AL=/opt/miniforge3/envs/JuniperCascor1/bin/actionlint
label="$1"; base="$2"; wt="$3"; out="$4"; shift 4
mkdir -p "$out"
for f in "$@"; do
  "$AL" -shellcheck= -pyflakes= -no-color "${base}/${f}" 2>&1 | sed -E "s#^${base}/##" > "$out/${label}-al-base-${f}.txt"; rb=${PIPESTATUS[0]}
  "$AL" -shellcheck= -pyflakes= -no-color "${wt}/${f}" 2>&1 | sed -E "s#^${wt}/##" > "$out/${label}-al-branch-${f}.txt"; rw=${PIPESTATUS[0]}
  echo "== ${f}: base exit=${rb} ($(command grep -c ':[0-9]*:[0-9]*:' "$out/${label}-al-base-${f}.txt") findings), branch exit=${rw} ($(command grep -c ':[0-9]*:[0-9]*:' "$out/${label}-al-branch-${f}.txt") findings)"
  echo "-- branch findings:"; command grep -E ':[0-9]+:[0-9]+:' "$out/${label}-al-branch-${f}.txt" | sed -E 's/^[^:]*:[0-9]+:[0-9]+: //' | sort | uniq -c || true
  echo "-- base findings:"; command grep -E ':[0-9]+:[0-9]+:' "$out/${label}-al-base-${f}.txt" | sed -E 's/^[^:]*:[0-9]+:[0-9]+: //' | sort | uniq -c || true
done
