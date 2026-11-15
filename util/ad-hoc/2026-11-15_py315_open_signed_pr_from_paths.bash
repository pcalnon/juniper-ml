#!/usr/bin/env bash
# Open the Python 3.15 informational-leg PR for one repo through juniper-ml's util/open_signed_pr.py (GitHub-signed
# API commit), building the --add LOCAL:REPOPATH arguments from a paths file so no workflow path is typed by hand.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-15
# Status:     ad-hoc -- one-off (opened juniper-cascor#759 and juniper-cascor-worker#228)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/open_signed_pr.py; util/ad-hoc/2026-11-15_py315_freshness_check.bash (run it first: the tool
#             uploads WHOLE files) and 2026-11-15_py315_readback.bash (run it after)
#
# Usage: open_pr.bash <bare-repo> <worktree> <scratch-dir> [--dry-run]
#   <scratch-dir> holds paths.txt, commit-title.txt, commit-body.md, pr-title.txt and pr-body.md.
set -euo pipefail
repo="$1"; wt="$2"; d="$3"; shift 3
# The checkout this script sits in supplies the tool (util/ad-hoc/ -> util/), so no host path is baked in (G5).
tool="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/open_signed_pr.py"
adds=()
while IFS= read -r p; do
  [ -n "$p" ] || continue
  [ -f "${wt}/${p}" ] || { echo "missing local file: ${wt}/${p}" >&2; exit 2; }
  adds+=(--add "${wt}/${p}:${p}")
done < "${d}/paths.txt"
echo "repo=${repo} files=$(( ${#adds[@]} / 2 ))"
python3 "$tool" --repo "$repo" --branch ci/python-3-15-informational "${adds[@]}" \
  --message "$(cat "${d}/commit-title.txt")" --commit-body-file "${d}/commit-body.md" \
  --title "$(cat "${d}/pr-title.txt")" --body-file "${d}/pr-body.md" "$@"
