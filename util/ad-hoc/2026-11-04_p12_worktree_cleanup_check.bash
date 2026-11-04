#!/usr/bin/env bash
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-11-04
# Status: ad-hoc -- one-off (the P12 worktree cleanup the owner ruled on 2026-11-03)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
#
# Why
# ---
# Owner ruling 2026-11-03 (recurrence x equities arc, session ff40b833): archive each
# worktree's tmp/ to juniper-ml/tmp/worktree-cleanup-2026-11-03-p12/, check each tree
# against main, then remove five worktrees. The archive was made on 2026-11-04 (sizes
# matched). A worktree-isolated session may not run git against another worktree, so
# the owner runs this.
#
# For each target it prints the branch, the uncommitted files (tmp/ is gitignored and
# already archived), the commits not on origin/main, and the branch's PR state.
# Squash merges leave origin/main..HEAD non-empty even after the PR merged, so a tree
# is REMOVABLE when it is clean AND (it has no unique commits OR a PR on its branch is
# MERGED and none is still OPEN). A git or gh read that fails keeps the tree (fail closed).
#
# Usage
# -----
#   bash util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash            # report only
#   bash util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash --remove   # also remove REMOVABLE trees
#
# --remove uses `git worktree remove` WITHOUT --force, so git itself refuses a dirty
# tree, and then `git worktree prune`. It never deletes a branch.

set -u

REMOVE=0
[[ "${1:-}" == "--remove" ]] && REMOVE=1

ARCHIVE="${HOME}/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-03-p12"
WT="${HOME}/Development/python/Juniper/worktrees"
ML="${HOME}/Development/python/Juniper/juniper-ml/.claude/worktrees"

# path | GitHub repo | archive subdirectory
TARGETS=(
    "$WT/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f|juniper-canopy|canopy--declared-param-staging-735-736"
    "$WT/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f|juniper-canopy|canopy--juniper-data-schema-drift-check"
    "$WT/juniper-canopy--fix--mnist-declared-params-778--20261103-0825--63fe4b6d|juniper-canopy|canopy--mnist-declared-params-778"
    "$ML/keen-popping-wilkes|juniper-ml|ml--keen-popping-wilkes"
    "$ML/cosmic-puzzling-lovelace|juniper-ml|ml--cosmic-puzzling-lovelace"
    "$ML/declarative-snuggling-sparrow|juniper-ml|ml--declarative-snuggling-sparrow"
)

for entry in "${TARGETS[@]}"; do
    IFS='|' read -r path repo archive <<<"$entry"
    echo "== $path"
    if [[ ! -d "$path" ]]; then
        echo "   absent (already removed)"
        continue
    fi
    if [[ ! -d "$ARCHIVE/$archive" ]]; then
        echo "   KEEP: no archive at $ARCHIVE/$archive"
        continue
    fi
    git -C "$path" fetch -q origin main || echo "   (fetch failed; origin/main may be stale)"
    if ! branch=$(git -C "$path" rev-parse --abbrev-ref HEAD); then
        echo "   KEEP: cannot read the branch"
        continue
    fi
    if ! dirty=$(git -C "$path" status --porcelain); then
        echo "   KEEP: git status failed"
        continue
    fi
    if ! unique=$(git -C "$path" log --oneline origin/main..HEAD); then
        echo "   KEEP: cannot resolve origin/main..HEAD"
        continue
    fi
    pr_ok=1
    pr=$(gh pr list --repo "pcalnon/$repo" --head "$branch" --state all --json number,state --jq 'map("#\(.number) \(.state)") | join(", ")' 2>/dev/null) || pr_ok=0
    echo "   branch:  $branch"
    echo "   PR(s):   ${pr:-none}$( (( pr_ok )) || echo ' (gh failed)')"
    echo "   dirty:   $([[ -z "$dirty" ]] && echo no || echo YES)"
    [[ -n "$dirty" ]] && sed 's/^/            /' <<<"$dirty"
    echo "   unique commits vs origin/main: $(grep -c . <<<"$unique")"
    [[ -n "$unique" ]] && sed 's/^/            /' <<<"$unique"

    # Merged only when gh answered, a PR on the branch is MERGED and none is still OPEN.
    merged=0
    if (( pr_ok )) && grep -q "MERGED" <<<"$pr" && ! grep -q "OPEN" <<<"$pr"; then
        merged=1
    fi
    removable=0
    if [[ -z "$dirty" ]] && { [[ -z "$unique" ]] || (( merged )); }; then
        removable=1
    fi
    if (( removable )); then
        echo "   -> REMOVABLE"
        if (( REMOVE )); then
            main_repo=$(git -C "$path" rev-parse --path-format=absolute --git-common-dir)
            git --git-dir="$main_repo" worktree remove "$path" && echo "   removed" && git --git-dir="$main_repo" worktree prune
        fi
    else
        echo "   -> KEEP (dirty, or unique commits without a merged PR): needs a look"
    fi
done
