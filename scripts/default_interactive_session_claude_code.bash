#!/usr/bin/env bash

SCRIPT_PATH="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

DEFAULT_PROMPT="Hello World, Claude!"

echo "Launching Default Interactive session with Claude Code"

echo "${SCRIPT_PATH}/wake_the_claude.bash --id --worktree --dangerously-skip-permissions --effort high --prompt \"${DEFAULT_PROMPT}\""
"${SCRIPT_PATH}"/wake_the_claude.bash --id --worktree --dangerously-skip-permissions --effort high --prompt "${DEFAULT_PROMPT}"

echo "Closed Default Interactive session with Claude Code"
