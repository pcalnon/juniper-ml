#!/usr/bin/env bash
# Run the sequence-safety symbol-loss screen against ml#1909's branch, locally.
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-09-11
# Status: ad-hoc -- investigation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: juniper-ml#1909 (renames the module constant _ML_OWN_WORKFLOWS, a same-file rename)
#
# Why: a same-file rename reads as a LOST symbol to the AST screen, so the rename of
# _ML_OWN_WORKFLOWS -> _ML_REQUIRED_PIN_WORKFLOWS needs checking BEFORE relying on the
# armed auto-merge -- which carries an EMPTY commit body and would drop any waiver trailer.
set -uo pipefail

# Usage: 2026-09-11_symbol_loss_check_pr1909.bash [BRANCH] [BASE]
# Defaults reproduce the ml#1909 check; pass a branch to screen any other PR.
BRANCH="${1:-test/widen-ci-tools-drift-guard-scope}"
BASE="${2:-origin/main}"

# The console scripts come from the PUBLISHED package, matching what CI installs.
# Resolve them from PATH if present, else build a throwaway venv -- an earlier
# revision hardcoded a session scratchpad path, which is reaped when the session
# ends and left the script unrunnable for the next reader.
if command -v juniper-symbol-loss-check >/dev/null 2>&1; then
  BIN=""
else
  VENV="$(mktemp -d)/v"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q 'juniper-ci-tools>=0.9.0,<0.10.0'
  BIN="$VENV/bin/"
fi

git fetch origin "$BRANCH" --quiet
echo "=== symbol-loss (juniper-ml's exact CI scope) ==="
"${BIN}juniper-symbol-loss-check" \
  --base "$BASE" --head FETCH_HEAD \
  --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'
echo "=== symbol-loss exit=$? ==="

echo
echo "=== docs deletion-magnitude (default scope) ==="
"${BIN}juniper-docs-additions-check" --base "$BASE" --head FETCH_HEAD
echo "=== docs exit=$? ==="
