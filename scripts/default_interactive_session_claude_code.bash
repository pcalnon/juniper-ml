#!/usr/bin/env bash
########################################################################################################################################################################
# Description:
#    Default interactive session launcher for Claude Code.
#    This script provides sensible defaults for an interactive (non-headless) Claude Code session
#    and delegates to wake_the_claude.bash for actual flag parsing and execution.
#
# Usage:
#    bash scripts/default_interactive_session_claude_code.bash --prompt "Your prompt here"
#    bash scripts/default_interactive_session_claude_code.bash --path /path/to/prompt_file.md
#    bash scripts/default_interactive_session_claude_code.bash --prompt "Your prompt" --effort low
#
# Default flags applied (can be overridden by user-supplied arguments):
#    --id          Auto-generate a session UUID
#    --worktree    Let Claude Code assign a worktree
#    --effort high Default to high effort
#
# Interactive mode is the default (no --print flag). Permissions are supervised (no --skip-permissions).
########################################################################################################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAKE_SCRIPT="${SCRIPT_DIR}/wake_the_claude.bash"

if [[ ! -f "${WAKE_SCRIPT}" ]]; then
    echo "Error: wake_the_claude.bash not found at: ${WAKE_SCRIPT}" >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    echo "Error: No arguments provided." >&2
    echo "" >&2
    echo "Usage: $(basename "${BASH_SOURCE[0]}") [--prompt \"text\" | --path /path/to/file | --file name] [options...]" >&2
    echo "" >&2
    echo "This script launches an interactive Claude Code session with default settings:" >&2
    echo "  --id           Auto-generate a session UUID" >&2
    echo "  --worktree     Let Claude Code assign a worktree" >&2
    echo "  --effort high  Default effort level" >&2
    echo "" >&2
    echo "Additional flags are forwarded to wake_the_claude.bash." >&2
    echo "Run 'bash ${WAKE_SCRIPT} --help' for all available options." >&2
    exit 1
fi

# Default interactive session flags.
# User-supplied arguments are appended after the spacer, allowing wake_the_claude.bash
# to process them in order. Because wake_the_claude.bash uses last-parsed-wins semantics,
# user flags (e.g., --effort low) override defaults.
DEFAULT_FLAGS=(--id --worktree --effort high)

exec bash "${WAKE_SCRIPT}" "${DEFAULT_FLAGS[@]}" -- "$@"
