#!/usr/bin/env bash
# Whole-file upload freshness check: after fetching origin/main in the primary, no commit in <base>..origin/main may
# touch any path that open_signed_pr.py is about to upload whole (it would silently revert that commit).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-15
# Status:     ad-hoc -- one-off (the pre-upload check for juniper-cascor#759 and juniper-cascor-worker#228)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    tmp/py315/ROLLOUT_BRIEF.md, "Mechanics" (the check this automates); util/open_signed_pr.py
#
# Usage: freshness_check.bash <primary> <base-sha> <paths-file>     Exit 0 = fresh, 1 = a path moved.
set -euo pipefail
primary="$1"; base="$2"; paths="$3"
git -C "$primary" fetch --quiet origin main
head="$(git -C "$primary" rev-parse origin/main)"
echo "base=${base:0:8} origin/main=${head:0:8}  commits since base (all paths): $(git -C "$primary" rev-list --count "${base}..origin/main")"
moved=0
while IFS= read -r p; do
  [ -n "$p" ] || continue
  out="$(git -C "$primary" log --oneline "${base}..origin/main" -- "$p")"
  if [ -n "$out" ]; then echo "MOVED: $p"; echo "$out" | sed 's/^/    /'; moved=1; else echo "fresh: $p"; fi
done < "$paths"
exit "$moved"
