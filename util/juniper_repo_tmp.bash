#!/usr/bin/env bash
# Print a Juniper repo's temp root -- the PRIMARY checkout's gitignored tmp/ -- creating it.
#
# Project:    juniper-ml
# Sub-Project: harness tooling (the 2026-10-26 repo tmp/ rule)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-26
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md;
#             tests/test_juniper_repo_tmp.py
#
# No file is ever written under the system temp directory (owner directive, 2026-10-26). On the
# Linux host it is a tmpfs that systemd-tmpfiles-clean ages daily, deleting files a live process
# still uses; it emptied a live E2E stack's pid files and venv three times in one week. Each repo
# writes its temp files to its own gitignored tmp/. This helper names that directory for a path,
# so a script can keep state another process must find (pid files, run dirs, locks) at a FIXED
# path derived from where the script lives -- never from TMPDIR, which every session now sets.
#
# The PRIMARY checkout's tmp/, not a linked worktree's: a worktree is removed when its task ends,
# the primary is not. The primary is the directory holding the checkout's common .git. When the
# common git dir is not a .git directory (a submodule, a --separate-git-dir clone), the checkout's
# own top level stands in.
#
# Usage, run:
#   bash util/juniper_repo_tmp.bash [DIR]   # prints the primary checkout's tmp/; DIR defaults to $PWD
# Usage, sourced (defines the two functions; sets no shell option):
#   source util/juniper_repo_tmp.bash
#   juniper_repo_primary [DIR]              # prints the primary checkout's root; creates nothing
#   juniper_repo_tmp [DIR]                  # prints the primary checkout's tmp/, creating it
#
# Exit codes (each function, and the run form):
#   0 -- the path was printed
#   1 -- DIR is in no git checkout (or git is missing), or tmp/ cannot be created; the reason goes
#        to stderr and nothing goes to stdout
#   2 -- the run form only: a usage error
#
# GIT_DIR, GIT_WORK_TREE and GIT_COMMON_DIR are ignored, because the answer is the checkout that
# holds DIR. Written for bash 3.2 too (macOS /bin/bash).

juniper_repo_primary() {
    local dir="${1:-$PWD}" common="" top=""
    common="$(unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR; git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || common=""
    case "$common" in
        */.git)
            top="${common%/.git}"
            ;;
        *)
            top="$(unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR; git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || top=""
            ;;
    esac
    # A checkout at / would make its tmp/ the very directory this helper exists to avoid.
    if [ -z "$top" ] || [ "$top" = "/" ]; then
        echo "juniper_repo_tmp: ${dir} is not in a git checkout" >&2
        return 1
    fi
    printf '%s\n' "$top"
}

juniper_repo_tmp() {
    local primary=""
    primary="$(juniper_repo_primary "${1:-$PWD}")" || return 1
    if ! mkdir -p "${primary}/tmp" 2>/dev/null; then
        echo "juniper_repo_tmp: cannot create ${primary}/tmp" >&2
        return 1
    fi
    printf '%s/tmp\n' "$primary"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    set -euo pipefail
    case "${1:-}" in
        -h | --help)
            echo "usage: bash ${0##*/} [DIR]   # print the primary checkout's tmp/ for DIR (default: \$PWD), creating it"
            exit 0
            ;;
    esac
    if [ "$#" -gt 1 ]; then
        echo "usage: bash ${0##*/} [DIR]" >&2
        exit 2
    fi
    juniper_repo_tmp "${1:-$PWD}"
fi
