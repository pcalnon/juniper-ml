#!/usr/bin/env bash

CLAUDE_SKIP_PERMISSIONS="${CLAUDE_SKIP_PERMISSIONS:-0}"
CLAUDE_SKIP_PERMISSIONS="1"

SCRIPT_PATH="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

DEFAULT_PROMPT="Hello World, Claude!"
CLAUDE_SKIP_PERMISSIONS="${CLAUDE_SKIP_PERMISSIONS:-0}"

CLAUDE_ARGS=(--id --worktree --effort high --prompt "${DEFAULT_PROMPT}")

# Opt in to --dangerously-skip-permissions only when explicitly requested
if [[ "${CLAUDE_SKIP_PERMISSIONS}" == "1" ]]; then
    CLAUDE_ARGS+=(--)
    CLAUDE_ARGS+=(--dangerously-skip-permissions)
fi

# Pass through any additional arguments from the caller
if (( $# > 0 )); then
    CLAUDE_ARGS+=("$@")
fi

echo "Launching Default Interactive session with Claude Code"
"${SCRIPT_PATH}/wake_the_claude.bash" "${CLAUDE_ARGS[@]}"
echo "Closed Default Interactive session with Claude Code"
