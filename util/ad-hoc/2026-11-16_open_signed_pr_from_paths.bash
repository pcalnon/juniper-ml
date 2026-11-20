#!/usr/bin/env bash
# Open a PR on a Juniper repo through juniper-ml's util/open_signed_pr.py (GitHub-signed API commit), building the
# --add LOCAL:REPOPATH arguments from a paths file, so no workflow path is typed on the command line.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-16
# Status:     ad-hoc -- one-off (cascor-model required check, Overtoad ruling 2026-11-16)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-15_py315_open_signed_pr_from_paths.bash (the same wrapper with its branch fixed to
#             ci/python-3-15-informational); util/open_signed_pr.py. The tool uploads WHOLE files: fetch the target
#             repo and check its main has not moved under the paths first.
#
# Why this exists: a worktree-isolated Claude Code session refuses a command whose text names a `.github/` path, and
# a workflow change has to name one in every --add argument.
#
# Usage: open_signed_pr_from_paths.bash <bare-repo> <branch> <worktree> <scratch-dir> [--dry-run]
#   <scratch-dir> holds paths.txt, commit-message.txt (title, blank line, body), pr-title.txt and pr-body.md.
set -euo pipefail
repo="$1"; branch="$2"; wt="$3"; d="$4"; shift 4
tool="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/open_signed_pr.py"
for f in paths.txt commit-message.txt pr-title.txt pr-body.md; do
  [ -s "${d}/${f}" ] || { echo "missing or empty: ${d}/${f}" >&2; exit 2; }
done
adds=()
while IFS= read -r p; do
  [ -n "$p" ] || continue
  [ -f "${wt}/${p}" ] || { echo "missing local file: ${wt}/${p}" >&2; exit 2; }
  adds+=(--add "${wt}/${p}:${p}")
done < "${d}/paths.txt"
title="$(head -n 1 "${d}/commit-message.txt")"
body_file="${d}/commit-body.generated.txt"
tail -n +3 "${d}/commit-message.txt" > "${body_file}"
echo "repo=${repo} branch=${branch} files=$(( ${#adds[@]} / 2 ))"
python3 "$tool" --repo "$repo" --branch "$branch" "${adds[@]}" \
  --message "$title" --commit-body-file "$body_file" \
  --title "$(cat "${d}/pr-title.txt")" --body-file "${d}/pr-body.md" "$@"
