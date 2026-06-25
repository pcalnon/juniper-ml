#!/usr/bin/env bash
#
# install_agents.bash -- mirror this project's .claude/{agents,skills} into ~/.claude
# so the Juniper custom-agent suite is available from any repo / worktree (design D-6).
#
# The mirror is by SYMLINK (the project stays the source of truth -- OQ-6): each agent
# .md and each skill directory is linked into ~/.claude/{agents,skills}/ individually, so
# the mirror coexists with any other agents/skills the user already has there.
#
# Idempotent (re-run safe), reversible (--reverse removes only the links it owns), and
# --dry-run previews. Overrides for tests / unusual layouts:
#   JUNIPER_ML_REPO_ROOT   source repo root          (default: one dir above this script)
#   JUNIPER_CLAUDE_HOME    mirror target             (default: $HOME/.claude)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${JUNIPER_ML_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
TARGET="${JUNIPER_CLAUDE_HOME:-${HOME}/.claude}"

MODE="install"
DRY_RUN=0

usage() {
    cat <<'USAGE'
Usage: util/install_agents.bash [--reverse|--uninstall] [--dry-run] [-h|--help]

  (default)            symlink .claude/{agents,skills}/* into ~/.claude/{agents,skills}/
  --reverse,--uninstall  remove only the symlinks that point back into this repo
  --dry-run            print what would change; touch nothing
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reverse | --uninstall) MODE="reverse" ;;
        --dry-run) DRY_RUN=1 ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "install_agents: unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
    shift
done

SRC_AGENTS="${REPO_ROOT}/.claude/agents"
SRC_SKILLS="${REPO_ROOT}/.claude/skills"

log() { echo "[install_agents] $*"; }

# link_one <src> <dst>: idempotently symlink src -> dst, never clobbering a non-symlink.
link_one() {
    local src="$1" dst="$2" cur
    if [[ -L "$dst" ]]; then
        cur="$(readlink "$dst")"
        if [[ "$cur" == "$src" ]]; then
            log "ok (already linked): ${dst}"
            return 0
        fi
        log "relink: ${dst} (${cur} -> ${src})"
        if [[ $DRY_RUN -eq 0 ]]; then ln -sfn "$src" "$dst"; fi
        return 0
    fi
    if [[ -e "$dst" ]]; then
        log "SKIP (exists, not a symlink -- refusing to clobber): ${dst}"
        return 0
    fi
    log "link: ${dst} -> ${src}"
    if [[ $DRY_RUN -eq 0 ]]; then ln -s "$src" "$dst"; fi
}

# unlink_one <dst>: remove dst only if it is a symlink pointing into this repo's .claude.
unlink_one() {
    local dst="$1" cur
    [[ -L "$dst" ]] || return 0
    cur="$(readlink "$dst")"
    case "$cur" in
        "${REPO_ROOT}/.claude/"*)
            log "unlink: ${dst}"
            if [[ $DRY_RUN -eq 0 ]]; then rm -f "$dst"; fi
            ;;
        *) log "skip (not ours): ${dst} -> ${cur}" ;;
    esac
}

if [[ "$MODE" == "install" ]]; then
    if [[ $DRY_RUN -eq 0 ]]; then mkdir -p "${TARGET}/agents" "${TARGET}/skills"; fi
    if [[ -d "$SRC_AGENTS" ]]; then
        for f in "$SRC_AGENTS"/*.md; do
            [[ -e "$f" ]] || continue
            link_one "$f" "${TARGET}/agents/$(basename "$f")"
        done
    fi
    if [[ -d "$SRC_SKILLS" ]]; then
        for d in "$SRC_SKILLS"/*/; do
            [[ -d "$d" ]] || continue
            link_one "${d%/}" "${TARGET}/skills/$(basename "$d")"
        done
    fi
    log "done (mirror -> ${TARGET}; source ${REPO_ROOT}/.claude)"
else
    if [[ -d "${TARGET}/agents" ]]; then
        for l in "${TARGET}/agents"/*; do
            [[ -L "$l" ]] || continue
            unlink_one "$l"
        done
    fi
    if [[ -d "${TARGET}/skills" ]]; then
        for l in "${TARGET}/skills"/*; do
            [[ -L "$l" ]] || continue
            unlink_one "$l"
        done
    fi
    log "done (reverse; ${TARGET})"
fi
