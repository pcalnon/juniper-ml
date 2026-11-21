#!/usr/bin/env bash
# Run the repository's pinned pre-commit inside a given worktree on the files a list names (claims lens, session 8).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-14
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
#
# Usage: <this> <worktree> <file listing one repo-relative path per line> <runenv.bash>
# The agent shell resets its working directory between calls, so the cd and the run must be in one process.
set -euo pipefail
tree="$1"
list="$2"
runenv="$3"
cd "$tree"
mapfile -t files < "$list"
echo "cwd: $(pwd)"
echo "files: ${#files[@]}"
exec bash "$runenv" pre-commit run --files "${files[@]}"
