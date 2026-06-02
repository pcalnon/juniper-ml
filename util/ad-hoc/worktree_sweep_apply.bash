#!/usr/bin/env bash
# File:    worktree_sweep_apply.bash
# Author:  Paul Calnon
# Created: 2026-05-31
# Purpose: Remove SAFE-classified stale worktrees from
#          /home/pcalnon/Development/python/Juniper/worktrees/. SAFE means:
#          (a) clean working tree (no uncommitted changes), and
#          (b) every commit on the worktree's branch is either:
#                - in origin/main directly (rev-list ahead == 0), OR
#                - the source side of a MERGED pull request on GitHub
#                  (i.e., squash-merged — the worktree's commit hash isn't
#                  in main's linear history but the work is already shipped).
#          For each SAFE worktree the script:
#              1. git -C <parent-repo> worktree remove <wt>
#              2. git -C <parent-repo> branch -D <branch>
#              3. git -C <parent-repo> worktree prune  (after the batch)
#          DIRTY / unresolvable rows are skipped with a warning.
#
# Run with --dry-run to print what would happen without acting.
# Default is to apply.
# Convention: ad-hoc one-shot script, lives under util/ad-hoc/ per
# CLAUDE.md "Script placement". Companion to worktree_sweep_survey.bash.

set -euo pipefail

DRY_RUN=0
if [[ "${1-}" == "--dry-run" ]]; then DRY_RUN=1; fi

WORKTREES_ROOT="/home/pcalnon/Development/python/Juniper/worktrees"

declare -A REPO_OF=(
    [juniper-ml]="/home/pcalnon/Development/python/Juniper/juniper-ml"
    [juniper-canopy]="/home/pcalnon/Development/python/Juniper/juniper-canopy"
    [juniper-cascor]="/home/pcalnon/Development/python/Juniper/juniper-cascor"
    [juniper-data]="/home/pcalnon/Development/python/Juniper/juniper-data"
    [juniper-deploy]="/home/pcalnon/Development/python/Juniper/juniper-deploy"
    [juniper-cascor-worker]="/home/pcalnon/Development/python/Juniper/juniper-cascor-worker"
    [juniper-data-client]="/home/pcalnon/Development/python/Juniper/juniper-data-client"
    [juniper-cascor-client]="/home/pcalnon/Development/python/Juniper/juniper-cascor-client"
)

remove_worktree() {
    local wt="$1" branch="$2" repo_key="$3"
    local repo="${REPO_OF[$repo_key]}"
    if (( DRY_RUN )); then
        echo "DRY: git -C $repo_key worktree remove $wt && branch -D $branch"
        return
    fi
    # Run from /tmp to avoid the CWD-trap if the caller is inside the wt.
    pushd /tmp >/dev/null
    if git -C "$repo" worktree remove "$wt" 2>/dev/null; then
        if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
            git -C "$repo" branch -D "$branch" >/dev/null 2>&1 || \
                echo "    warning: branch -D $branch failed (not a fast-forward?)"
        fi
        echo "removed: $repo_key / $branch"
    else
        echo "skipped (remove failed): $repo_key / $branch / $wt"
    fi
    popd >/dev/null
}

# Iterate the survey output. Survey is pre-fetched; this script just acts
# on SAFE rows + ACTIVE-but-PR-merged rows (passed in via stdin so we
# don't duplicate the pre-condition logic).
#
# Input format (tab-separated): STATUS<TAB>REPO_KEY<TAB>BRANCH<TAB>WORKTREE_NAME
while IFS=$'\t' read -r status repo_key branch wt_name; do
    [[ -z "${status:-}" ]] && continue
    [[ "$status" =~ ^# ]] && continue   # comment / header
    wt="$WORKTREES_ROOT/$wt_name"
    if [[ ! -d "$wt" ]]; then
        echo "skipped (missing dir): $wt_name"
        continue
    fi
    remove_worktree "$wt" "$branch" "$repo_key"
done

# Prune all repos once at the end so each repo's worktree metadata is clean.
for repo in "${REPO_OF[@]}"; do
    (( DRY_RUN )) || git -C "$repo" worktree prune >/dev/null 2>&1 || true
done
echo "done"
