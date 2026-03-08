#!/usr/bin/env bash

SCRIPT_PATH="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

DEFAULT_PROMPT="Hello World, Claude!"

echo "Launching Default Interactive session with Claude Code"

# echo "${SCRIPT_PATH}/wake_the_claude.bash --id --worktree --dangerously-skip-permissions --effort high --prompt \"${DEFAULT_PROMPT}\""
# "${SCRIPT_PATH}"/wake_the_claude.bash --id --worktree --dangerously-skip-permissions --effort high --prompt "${DEFAULT_PROMPT}"

# SCRIPT_PATH="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
# /home/pcalnon/.local/bin/claude --session-id 34ec3d30-1f3a-4289-b401-c85aa97ff8da --worktree --dangerously-skip-permissions --effort high "Hello World, Claude!"
echo "\"${SCRIPT_PATH}/wake_the_claude.bash\" --id --worktree --dangerously-skip-permissions --effort high --prompt \"${DEFAULT_PROMPT}\""
"${SCRIPT_PATH}/wake_the_claude.bash" --id --worktree --dangerously-skip-permissions --effort high --prompt "${DEFAULT_PROMPT}"

echo "Closed Default Interactive session with Claude Code"
