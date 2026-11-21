#!/usr/bin/env bash
# List every file whose name contains a pattern (default "encryption.bash") under a search root.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (rewritten via Claude Code)
# Created:    2026-10-16
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task B9);
#             tests/test_find_encryption_readme_notes.py
#
# Each match prints as its absolute path, then "==> Valid" for a regular file or "==> Invalid" for
# anything else (a directory, a dangling symlink).
#
# The first version rode the unsigned branch of juniper-ml#2222 and never reached main. It built
# "ls -Fla ${i}" from find output and ran the string through eval, so a file NAMED
# '$(:>x)encryption.bash' was executed rather than listed (any whitespace-free command works). It
# also word-split find output, so a space broke a path; parsed ls columns; and hard-coded one host's
# home directory. This version passes every path NUL-delimited, never evaluates one, and defaults
# to a $HOME-relative root.
#
# Usage:
#   bash util/find_encryption_readme_notes.bash [--root DIR] [--name PATTERN]
#
# Exit codes:
#   0 -- at least one match, and every match is a regular file
#   1 -- no match, or a match that is not a regular file
#   2 -- usage or environment: unknown option, missing value, a PATTERN containing '/', or a root
#        that is not a directory
#
# Environment:
#   FIND -- the find binary (default: find); tests override it
set -euo pipefail

FIND="${FIND:-find}"

usage() {
    cat <<'EOF'
Usage: find_encryption_readme_notes.bash [--root DIR] [--name PATTERN]

List every file under DIR whose name contains PATTERN, as an absolute path followed by
"==> Valid" (a regular file) or "==> Invalid" (anything else).

  --root DIR      search root (default: $HOME/Development)
  --name PATTERN  find -name glob fragment, matched as *PATTERN* (default: encryption.bash)
  -h, --help      show this help

Exit codes: 0 matches found and all valid, 1 no match or an invalid match,
2 usage/environment error.
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

ROOT="${HOME}/Development"
PATTERN="encryption.bash"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        --root)
            [[ -n "${2:-}" ]] || die_usage "--root needs a directory"
            ROOT="$2"
            shift 2
            ;;
        --name)
            [[ -n "${2:-}" ]] || die_usage "--name needs a pattern"
            PATTERN="$2"
            shift 2
            ;;
        *)
            die_usage "unknown argument: $1"
            ;;
    esac
done

case "$PATTERN" in
    */*) die_usage "--name matches file names, so it cannot contain '/': $PATTERN" ;;
esac

if [[ ! -d "$ROOT" ]]; then
    echo "ERROR: search root is not a directory: $ROOT" >&2
    exit 2
fi
# Absolute, so every printed path is absolute and a leading '-' can't reach find as an option.
# CDPATH is cleared so cd neither resolves through it nor prints the directory into ROOT.
ROOT="$(CDPATH='' cd -- "$ROOT" && pwd)"

matches=0
invalid=0
while IFS= read -r -d '' path; do
    matches=$((matches + 1))
    if [[ -f "$path" ]]; then
        printf '%s\t==> Valid\n' "$path"
    else
        printf '%s\t==> Invalid\n' "$path"
        invalid=$((invalid + 1))
    fi
done < <("$FIND" "$ROOT" -name "*${PATTERN}*" -print0)

if [[ "$matches" -eq 0 ]]; then
    echo "no name containing '${PATTERN}' under ${ROOT}" >&2
    exit 1
fi
echo "${matches} match(es), ${invalid} invalid, under ${ROOT}" >&2
[[ "$invalid" -eq 0 ]] || exit 1
