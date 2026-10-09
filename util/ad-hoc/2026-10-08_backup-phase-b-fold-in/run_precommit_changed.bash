#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File:          2026-10-08_backup-phase-b-fold-in/run_precommit_changed.bash
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
# -----------------------------------------------------------------------------
# Purpose: run every pre-commit hook over the files this branch changes against
# origin/main (a worktree-isolated session cannot pass a computed file list to
# pre-commit inline). Uses /opt/miniforge3/bin/pre-commit, because the pre-commit
# on PATH may be a shim whose interpreter was removed (Juniper/AGENTS.md).
#
# Usage: bash util/ad-hoc/2026-10-08_backup-phase-b-fold-in/run_precommit_changed.bash [base]
# -----------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/../../.."
base="${1:-origin/main}"
mapfile -t files < <(git diff --name-only --diff-filter=d "${base}")
echo "# ${#files[@]} changed file(s) against ${base}"
/opt/miniforge3/bin/pre-commit run --files "${files[@]}"
