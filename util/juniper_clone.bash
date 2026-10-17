#!/usr/bin/env bash
# Clone a Juniper repo through its per-repo SSH alias, so the persisted origin keeps working.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-16
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task A4, §4.1);
#             tests/test_juniper_clone.py
#
# Replaces util/git_clone_with_specified_id.bash, which never reached main (it rode the unsigned
# branch of juniper-ml#2222). That helper ran
#     GIT_SSH_COMMAND="ssh -i <key>" git clone git@github.com:pcalnon/<repo>.git
# The -i override applied to that one clone only. The persisted origin was the bare github.com
# URL, which bypasses the github_juniper-<repo> Host alias, so every later fetch and push offered
# the wrong identity. That is how juniper-k8s's origin broke on turing.
#
# This script clones from git@github_juniper-<repo>:<owner>/juniper-<repo>.git and then reads the
# origin back from the clone's own config (not `git remote get-url`, which expands insteadOf).
# It reads only the ssh client's resolved configuration (`ssh -G`). It never reads key material
# and never authenticates beyond what the clone itself does.
#
# Usage:
#   bash util/juniper_clone.bash [--dest DIR] [--owner OWNER] [--dry-run] <repo>
#   <repo> is the short name ("k8s") or the full name ("juniper-k8s").
#
# Exit codes:
#   0 -- cloned and the persisted origin is in alias form (with --dry-run: plan printed, nothing written)
#   1 -- the clone failed, or the persisted origin is not in alias form
#   2 -- usage or environment: bad argument, the destination exists, or the alias does not resolve to GitHub
#
# Environment:
#   JUNIPER_ROOT -- parent directory of the checkouts (default: $HOME/Development/python/Juniper)
#   GIT, SSH     -- the git and ssh binaries (default: git, ssh); tests override them
set -euo pipefail

GIT="${GIT:-git}"
SSH="${SSH:-ssh}"
JUNIPER_ROOT="${JUNIPER_ROOT:-${HOME}/Development/python/Juniper}"

usage() {
    cat <<'EOF'
Usage: juniper_clone.bash [--dest DIR] [--owner OWNER] [--dry-run] <repo>

Clone a Juniper repo through its per-repo SSH alias (github_juniper-<repo>), so the
persisted origin is git@github_juniper-<repo>:<owner>/juniper-<repo>.git.

  <repo>         short ("k8s") or full ("juniper-k8s") repository name
  --dest DIR     clone into DIR (default: $JUNIPER_ROOT/juniper-<repo>)
  --owner OWNER  GitHub owner (default: pcalnon)
  --dry-run      check and print the plan; write nothing
  -h, --help     show this help

Exit codes: 0 cloned (or dry-run OK), 1 clone failed or origin not in alias form,
2 usage/environment error.
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

OWNER="pcalnon"
DEST=""
DRY_RUN=0
REPO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        --dest)
            [[ -n "${2:-}" ]] || die_usage "--dest needs a directory"
            DEST="$2"
            shift 2
            ;;
        --owner)
            [[ -n "${2:-}" ]] || die_usage "--owner needs a value"
            OWNER="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -*)
            die_usage "unknown option: $1"
            ;;
        *)
            [[ -z "$REPO" ]] || die_usage "one repo per run (got '$REPO' and '$1')"
            REPO="$1"
            shift
            ;;
    esac
done

[[ -n "$REPO" ]] || die_usage "no repo given"

NAME="${REPO#juniper-}"
name_re='^[a-z0-9][a-z0-9-]*$'
owner_re='^[A-Za-z0-9][A-Za-z0-9-]*$'
[[ "$NAME" =~ $name_re ]] || die_usage "not a Juniper repo name: '$REPO' (expected e.g. k8s or juniper-k8s)"
[[ "$OWNER" =~ $owner_re ]] || die_usage "not a GitHub owner: '$OWNER'"

FULL="juniper-${NAME}"
ALIAS="github_${FULL}"
URL="git@${ALIAS}:${OWNER}/${FULL}.git"
[[ -n "$DEST" ]] || DEST="${JUNIPER_ROOT}/${FULL}"

if [[ -e "$DEST" || -L "$DEST" ]]; then
    echo "ERROR: destination already exists: $DEST" >&2
    echo "To repair an existing checkout's origin instead: ${GIT} -C '$DEST' remote set-url origin '$URL'" >&2
    exit 2
fi

# The alias must resolve to GitHub. `ssh -G` evaluates the client configuration (Include files
# and Match blocks too) without connecting. An undefined alias resolves to itself.
if ! resolved="$("$SSH" -G "$ALIAS" 2>/dev/null)"; then
    echo "ERROR: '${SSH} -G ${ALIAS}' failed; cannot check the alias." >&2
    exit 2
fi
resolved_host="$(printf '%s\n' "$resolved" | awk '$1 == "hostname" && !seen { print $2; seen = 1 }')"
case "$resolved_host" in
    github.com | ssh.github.com) ;;
    *)
        echo "ERROR: ssh alias '${ALIAS}' resolves to '${resolved_host:-<nothing>}', not github.com." >&2
        echo "Add its Host block (and the deploy key) first, e.g. with util/juniper_repo_ssh_setup.bash ${NAME}." >&2
        exit 2
        ;;
esac

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN: would clone ${URL}"
    echo "         into ${DEST}"
    echo "         alias ${ALIAS} -> ${resolved_host}"
    echo "(nothing written)"
    exit 0
fi

if ! "$GIT" clone -- "$URL" "$DEST"; then
    echo "ERROR: git clone of ${URL} failed." >&2
    exit 1
fi

# Read the persisted value. `git remote get-url` would expand insteadOf and could hide a bad origin.
origin="$("$GIT" -C "$DEST" config --get remote.origin.url || true)"
if [[ "$origin" != "$URL" ]]; then
    echo "ERROR: ${DEST} persisted origin '${origin:-<unset>}', expected '${URL}'." >&2
    echo "Repair: ${GIT} -C '$DEST' remote set-url origin '$URL'" >&2
    exit 1
fi

echo "cloned ${FULL} into ${DEST}"
echo "origin ${origin}"
