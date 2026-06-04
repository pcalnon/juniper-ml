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

WORKTREES_ROOT="${JUNIPER_WORKTREE_SWEEP_ROOT:-/home/pcalnon/Development/python/Juniper/worktrees}"
JUNIPER_SWEEP_PROJECT_DIR="${JUNIPER_SWEEP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"

declare -A REPO_OF=(
    [juniper-ml]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-ml"
    [juniper-canopy]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-canopy"
    [juniper-cascor]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-cascor"
    [juniper-data]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-data"
    [juniper-deploy]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-deploy"
    [juniper-cascor-worker]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-cascor-worker"
    [juniper-data-client]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-data-client"
    [juniper-cascor-client]="${JUNIPER_SWEEP_PROJECT_DIR}/juniper-cascor-client"
)

trim_field() {
    local value="${1:-}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

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
# Input format (tab-separated): STATUS<TAB>REPO_KEY<TAB>BEHIND<TAB>BRANCH<TAB>WORKTREE_NAME
while IFS=$'\t' read -r status repo_key _behind branch wt_name _extra; do
    status=$(trim_field "$status")
    repo_key=$(trim_field "$repo_key")
    branch=$(trim_field "$branch")
    wt_name=$(trim_field "$wt_name")

    [[ -z "${status:-}" ]] && continue
    [[ "$status" =~ ^# ]] && continue   # comment
    [[ "$status" == "STATUS" ]] && continue
    [[ "$status" =~ ^-+$ ]] && continue
    if [[ "$status" != "SAFE" ]]; then
        echo "skipped (${status}): ${wt_name:-?}"
        continue
    fi
    if [[ -z "$repo_key" || -z "$branch" || -z "$wt_name" ]]; then
        echo "skipped (malformed SAFE row): ${status} ${repo_key} ${branch} ${wt_name}"
        continue
    fi
    if [[ -z "${REPO_OF[$repo_key]+x}" ]]; then
        echo "skipped (unknown repo): $repo_key / $wt_name"
        continue
    fi
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
