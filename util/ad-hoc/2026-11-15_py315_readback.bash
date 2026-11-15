#!/usr/bin/env bash
# Read every uploaded file back from the PR branch (contents API) and compare its sha256 with the local copy.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-15
# Status:     ad-hoc -- one-off (the post-upload check for juniper-cascor#759 and juniper-cascor-worker#228)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    tmp/py315/ROLLOUT_BRIEF.md, "Mechanics" (the read-back this automates); util/open_signed_pr.py
#
# Usage: readback.bash <bare-repo> <worktree> <paths-file> [<ref>]     Exit 0 = all identical.
set -uo pipefail
repo="$1"; wt="$2"; paths="$3"; ref="${4:-ci/python-3-15-informational}"
bad=0
while IFS= read -r p; do
  [ -n "$p" ] || continue
  remote="$(gh api "repos/pcalnon/${repo}/contents/${p}?ref=${ref}" --jq .content | base64 -d | sha256sum | cut -d' ' -f1)"
  local_="$(sha256sum "${wt}/${p}" | cut -d' ' -f1)"
  if [ "$remote" = "$local_" ]; then echo "same   ${local_:0:16}  $p"; else echo "DIFFER remote=${remote:0:16} local=${local_:0:16}  $p"; bad=1; fi
done < "$paths"
exit "$bad"
