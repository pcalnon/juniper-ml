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
# is REMOVABLE when it is clean AND (it has no unique commits OR its PR is MERGED).
#
# Usage
# -----
#   bash util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash            # report only
#   bash util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash --remove   # also remove REMOVABLE trees
#
# --remove uses `git worktree remove` WITHOUT --force, and then `git worktree prune`.
# It never deletes a branch. `worktree remove` is not a sufficient dirt backstop:
# it deletes ignored files without --force, and when status.showUntrackedFiles=no
# it also deletes untracked files (git 2.43). Probes and the remove itself force
# status.showUntrackedFiles=normal. Ignored paths outside the archived tmp/ are
# KEEP. A failed fetch, status, or origin/main comparison is KEEP, not "clean".

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

# Portable (bash 3.2 / macOS find): true when root contains at least one regular file.
has_regular_file() {
    local root="$1" found
    [[ -d "$root" ]] || return 1
    found=$(find "$root" -type f | head -n 1)
    [[ -n "$found" ]]
}

# Ignored porcelain lines whose path is not the archived tmp/ tree.
extra_ignored_outside_tmp() {
    local line rel
    while IFS= read -r line; do
        [[ "$line" == '!! '* ]] || continue
        rel="${line#!! }"
        if [[ "$rel" == \"*\" ]]; then
            rel=${rel#\"}
            rel=${rel%\"}
        fi
        case "$rel" in
            tmp|tmp/*) ;;
            *) printf '%s\n' "$line" ;;
        esac
    done
}

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
    if ! git -C "$path" fetch -q origin main; then
        echo "   KEEP: fetch of origin/main failed (refusing to treat that as no unique commits)"
        continue
    fi
    if ! branch=$(git -C "$path" rev-parse --abbrev-ref HEAD); then
        echo "   KEEP: cannot read HEAD"
        continue
    fi
    # -uall so an untracked file inside a directory is visible. -c overrides a
    # local or global status.showUntrackedFiles=no, which makes plain porcelain
    # empty while `worktree remove` still deletes those files.
    if ! dirty=$(git -C "$path" -c status.showUntrackedFiles=normal --no-optional-locks status --porcelain -uall); then
        echo "   KEEP: git status failed (refusing to treat that as clean)"
        continue
    fi
    if ! ignored=$(git -C "$path" -c status.showUntrackedFiles=normal --no-optional-locks status --porcelain --ignored -uall); then
        echo "   KEEP: git status --ignored failed"
        continue
    fi
    extra_ignored=$(printf '%s\n' "$ignored" | extra_ignored_outside_tmp)
    if ! unique=$(git -C "$path" log --oneline origin/main..HEAD); then
        echo "   KEEP: cannot compare HEAD to origin/main (refusing to treat that as no unique commits)"
        continue
    fi
    if ! pr=$(gh pr list --repo "pcalnon/$repo" --head "$branch" --state all --json number,state --jq 'map("#\(.number) \(.state)") | join(", ")'); then
        pr=""
        echo "   (pr lookup failed; a merged PR will not be assumed)"
    fi
    echo "   branch:  $branch"
    echo "   PR(s):   ${pr:-none}"
    echo "   dirty:   $([[ -z "$dirty" ]] && echo no || echo YES)"
    [[ -n "$dirty" ]] && sed 's/^/            /' <<<"$dirty"
    echo "   ignored outside archived tmp/: $([[ -z "$extra_ignored" ]] && echo no || echo YES)"
    [[ -n "$extra_ignored" ]] && sed 's/^/            /' <<<"$extra_ignored"
    echo "   unique commits vs origin/main: $(grep -c . <<<"$unique" || true)"
    [[ -n "$unique" ]] && sed 's/^/            /' <<<"$unique"

    archive_ok=1
    if has_regular_file "$path/tmp"; then
        if ! has_regular_file "$ARCHIVE/$archive"; then
            archive_ok=0
            echo "   KEEP: tmp/ has files but the archive has none"
        fi
    fi

    removable=0
    if [[ -z "$dirty" && -z "$extra_ignored" && "$archive_ok" == 1 ]]; then
        if [[ -z "$unique" ]]; then
            removable=1
        elif grep -q "MERGED" <<<"$pr"; then
            removable=1
        fi
    fi
    if (( removable )); then
        echo "   -> REMOVABLE"
        if (( REMOVE )); then
            if ! main_repo=$(git -C "$path" rev-parse --path-format=absolute --git-common-dir); then
                echo "   KEEP: cannot resolve the git common dir"
                continue
            fi
            if git -c status.showUntrackedFiles=normal --git-dir="$main_repo" worktree remove "$path"; then
                echo "   removed"
                git -c status.showUntrackedFiles=normal --git-dir="$main_repo" worktree prune
            else
                echo "   KEEP: git worktree remove refused"
            fi
        fi
    else
        echo "   -> KEEP (dirty, ignored files outside archived tmp/, empty archive, or unique commits without a merged PR)"
    fi
done
