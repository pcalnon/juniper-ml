#!/usr/bin/env bash
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-11-04
# Status: ad-hoc -- one-off (the P12 worktree cleanup; owner approved the forced removal 2026-11-04)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash (kept these five as dirty),
#          util/ad-hoc/2026-11-04_dirty_worktree_files_landed_check.py (showed every dirty file landed)
#
# Why
# ---
# The cleanup check keeps a dirty tree. These five were dirty only with content already on main, or in a commit of
# their merged PR (canopy#776, canopy#777); every tmp/ was archived to
# juniper-ml/tmp/worktree-cleanup-2026-11-03-p12/. The owner approved `git worktree remove --force` for exactly
# these five. The script refuses a tree whose archive is missing. It never deletes a branch.

set -u

ARCHIVE="${HOME}/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-03-p12"
WT="${HOME}/Development/python/Juniper/worktrees"
ML="${HOME}/Development/python/Juniper/juniper-ml/.claude/worktrees"

TARGETS=(
    "$WT/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f|canopy--declared-param-staging-735-736"
    "$WT/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f|canopy--juniper-data-schema-drift-check"
    "$ML/keen-popping-wilkes|ml--keen-popping-wilkes"
    "$ML/cosmic-puzzling-lovelace|ml--cosmic-puzzling-lovelace"
    "$ML/declarative-snuggling-sparrow|ml--declarative-snuggling-sparrow"
)

for entry in "${TARGETS[@]}"; do
    IFS='|' read -r path archive <<<"$entry"
    echo "== $path"
    if [[ ! -d "$path" ]]; then
        echo "   absent (already removed)"
        continue
    fi
    if [[ ! -d "$ARCHIVE/$archive" ]]; then
        echo "   KEEP: no archive at $ARCHIVE/$archive"
        continue
    fi
    if ! common=$(git -C "$path" rev-parse --path-format=absolute --git-common-dir); then
        echo "   KEEP: cannot resolve the repository"
        continue
    fi
    git --git-dir="$common" worktree remove --force "$path" && echo "   removed" && git --git-dir="$common" worktree prune
done
