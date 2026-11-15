#!/usr/bin/env bash
# Compare the matrix legs (check names + continue-on-error) of a repo's workflows: base copy vs worktree.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-15
# Status:     ad-hoc -- investigation (verification for juniper-cascor#759 and juniper-cascor-worker#228)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-15_py315_expand_matrix_legs.py (the expansion it runs twice)
#
# Usage: compare_legs.bash <label> <base-dir> <worktree-workflows-dir> <out-dir> <file> [<file> ...]
#   <base-dir> holds copies of the files at the PR's base (`git show origin/main:<path> > ...`). As first run, the
#   outputs went to this script's own directory; here they go to <out-dir> (use a tmp/ directory).
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd)"
PY=/opt/miniforge3/envs/JuniperCascor1/bin/python3.14
label="$1"; base="$2"; wt="$3"; out="$4"; shift 4
mkdir -p "$out"
b=(); w=()
for f in "$@"; do b+=("${base}/${f}"); w+=("${wt}/${f}"); done
"$PY" "$S/2026-11-15_py315_expand_matrix_legs.py" "${b[@]}" > "$out/${label}-legs-base.txt"
"$PY" "$S/2026-11-15_py315_expand_matrix_legs.py" "${w[@]}" > "$out/${label}-legs-branch.txt"
echo "######## BASE"; cat "$out/${label}-legs-base.txt"
echo "######## BRANCH"; cat "$out/${label}-legs-branch.txt"
echo "######## base leg lines missing from the branch (job headers may differ; leg lines must not):"
command grep -F -x -v -f "$out/${label}-legs-branch.txt" "$out/${label}-legs-base.txt" || echo "(none)"
echo "######## lines new in the branch:"
command grep -F -x -v -f "$out/${label}-legs-base.txt" "$out/${label}-legs-branch.txt" || echo "(none)"
