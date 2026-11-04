#!/usr/bin/env bash
#####################################################################################################################################################################################################################################
# Script:   claude_interactive
# File:     claude_interactive.bash
# Author:   Paul Calnon
# Email:    overtoad.research@gmail.com
# Created:  2026-03-07
# Modified: 2026-11-04
# Version:  0.1.1
#####################################################################################################################################################################################################################################
# Description:
#     Interactively launch a Claude Code session
#
# Usage:
#    ./claude_interactive.bash [<model> [<effort> [prompt]]]
#
# Example:
#    ./claude_interactive.bash fable auto
#
#####################################################################################################################################################################################################################################
# Notes:
#
#     This script is a wrapper for the wake_the_claude.bash script.
#     It is used to interactively launch a Claude Code session.
#
#     export USAGE_MESSAGE="Usage: ${WAKE_THE_CLAUDE_SCRIPT_NAME} [<model alias: ${MODEL_FABLE_ALIAS}|${MODEL_OPUS_ALIAS}|${MODEL_SONNET_ALIAS}|${MODEL_HAIKU_ALIAS}>] [<effort: ${AUTO}|${MAX}|${XHIGH}|${HIGH}|${MEDIUM}|${LOW}>] [<id: ${TRUE}|${FALSE}>] [<resume: ${TRUE}|${FALSE}>] [<worktree: ${TRUE}|${FALSE}>] [<remote-control: ${TRUE}|${FALSE}>] [<skip-permissions: ${TRUE}|${FALSE}>] [<prompt: 'your prompt here'>]"
#     CLAUDE_MODEL="${1}" && shift
#     CLAUDE_EFFORT="${1}" && shift || true
#     CLAUDE_ID="${1}" && shift || true
#     CLAUDE_WORKTREE="${1}" && shift || true
#     CLAUDE_RESUME="${1}" && shift || true
#     CLAUDE_REMOTE_CONTROL="${1}" && shift || true
#     CLAUDE_SKIP_PERMISSIONS="${1}" && shift || true
#     CLAUDE_PROMPT="${1}" && shift || true
#
########################################################################################################################################################################################################


########################################################################################################################################################################################################
# Define Script Global Constants
########################################################################################################################################################################################################
export TRUE="0"
export FALSE="1"

export DEBUG="${TRUE}"
# export DEBUG="${FALSE}"

export SCRIPT_VERSION="0.1.1"


########################################################################################################################################################################################################
# Define Script Environment Constants
########################################################################################################################################################################################################
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
export SCRIPT_NAME

SCRIPT_PATH="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
export SCRIPT_PATH


########################################################################################################################################################################################################
# Define Script Constants for Wake The Claude script
########################################################################################################################################################################################################
export WAKE_THE_CLAUDE_SCRIPT_NAME="wake_the_claude.bash"
export WAKE_THE_CLAUDE_SCRIPT="${SCRIPT_PATH}/${WAKE_THE_CLAUDE_SCRIPT_NAME}"


########################################################################################################################################################################################################
# Define Claude Code Command Line Flags for Interactive Session Arguments
########################################################################################################################################################################################################
export CLAUDE_SKIP_PERMISSIONS_FLAG="--dangerously-skip-permissions"
export CLAUDE_REMOTE_CONTROL_FLAG="--remote-control"
export CLAUDE_WORKTREE_FLAG="--worktree"
export CLAUDE_PROMPT_FLAG="--prompt"
export CLAUDE_RESUME_FLAG="--resume"
export CLAUDE_EFFORT_FLAG="--effort"
export CLAUDE_MODEL_FLAG="--model"
export CLAUDE_SEPERATOR_FLAG="--"
export CLAUDE_ID_FLAG="--id"


########################################################################################################################################################################################################
# Define Script Constants for Claude Code interaction
########################################################################################################################################################################################################
export MODEL_FABLE_NAME="claude-fable-5"
export MODEL_OPUS_NAME="claude-opus-5"
export MODEL_SONNET_NAME="claude-sonnet-4-6"
export MODEL_HAIKU_NAME="claud-haiku-4-5"

export MODEL_FABLE_ALIAS="fable"
export MODEL_OPUS_ALIAS="opus"
export MODEL_SONNET_ALIAS="sonnet"
export MODEL_HAIKU_ALIAS="haiku"

export AUTO="auto"
export MAX="max"
export XHIGH="xhigh"
export HIGH="high"
export MEDIUM="medium"
export LOW="low"


########################################################################################################################################################################################################
# Define Script Defaults
########################################################################################################################################################################################################
# export DEFAULT_MODEL="${MODEL_FABLE_ALIAS}"
export DEFAULT_MODEL="${MODEL_OPUS_ALIAS}"

# export DEFAULT_EFFORT="${AUTO}"
# export DEFAULT_EFFORT="${HIGH}"
export DEFAULT_EFFORT="${MAX}"

export DEFAULT_ID="${FALSE}"
export DEFAULT_RESUME="${FALSE}"
# Worktree and remote control are ON by default (owner ruling, 2026-11-04): a bare --worktree, so Claude Code names the worktree, and a
# bare --remote-control, which never takes a value. --no-worktree / --no-remote-control, or CLAUDE_WORKTREE / CLAUDE_REMOTE_CONTROL set
# to ${FALSE}, turn them off.
export DEFAULT_WORKTREE="${TRUE}"
export DEFAULT_REMOTE_CONTROL="${TRUE}"
export DEFAULT_SKIP_PERMISSIONS="${FALSE}"

export DEFAULT_PROMPT="Hello World, Claude!"


########################################################################################################################################################################################################
# Define Usage Message
########################################################################################################################################################################################################
export USAGE_MESSAGE_PREFIX="Usage: ${WAKE_THE_CLAUDE_SCRIPT_NAME}"

export USAGE_MESSAGE_MODEL="[--model-alias|--model|-m <${MODEL_FABLE_ALIAS}|${MODEL_OPUS_ALIAS}|${MODEL_SONNET_ALIAS}|${MODEL_HAIKU_ALIAS}>]"
export USAGE_MESSAGE_EFFORT="[--effort-level|--effort|-e <${AUTO}|${MAX}|${XHIGH}|${HIGH}|${MEDIUM}|${LOW}>]"
export USAGE_MESSAGE_ID="[--session-id|--session|--id|-s|-i <SESSION_ID|${FALSE}>]"
export USAGE_MESSAGE_WORKTREE="[--worktree-name|--worktree|-w [WORKTREE_NAME|${TRUE}|${FALSE}]] [--no-worktree]"
export USAGE_MESSAGE_RESUME="[--resume-session|--resume|-rs|-r]"
export USAGE_MESSAGE_REMOTE_CONTROL="[--remote-control-session|--remote-control|-rc] [--no-remote-control]"
export USAGE_MESSAGE_SKIP_PERMISSIONS="[--dangerously-skip-permissions|--skip-permissions|-sp]"
export USAGE_MESSAGE_PROMPT="[--initial-prompt|--prompt|-p <YOUR_INITIAL_PROMPT_HERE>]"

export USAGE_MESSAGE="${USAGE_MESSAGE_PREFIX} ${USAGE_MESSAGE_MODEL} ${USAGE_MESSAGE_EFFORT} ${USAGE_MESSAGE_ID} ${USAGE_MESSAGE_RESUME} ${USAGE_MESSAGE_WORKTREE} ${USAGE_MESSAGE_REMOTE_CONTROL} ${USAGE_MESSAGE_SKIP_PERMISSIONS} ${USAGE_MESSAGE_PROMPT}"


########################################################################################################################################################################################################
# Define Usage Message and Exit
########################################################################################################################################################################################################
function usage {
    local exit_code="${1:-1}"
    local message="${2}"

    [[ "${message}" != "" ]] && echo -ne "\n${message}\n\n" || true
    echo -ne "${USAGE_MESSAGE}\n\n" || true
    set -e
    exit "${exit_code}"
}

# A flag that takes a value must be given one: "shift 2" fails on a missing value, and the parse loop below then never ends.
function require_value {
    (( $# >= 2 )) || usage 1 "Missing value for ${1}"
}


########################################################################################################################################################################################################
# Parse Command Line Input Parameters if provided
########################################################################################################################################################################################################
# Display Usage Message and Exit if --help, -h, or -? is provided
if [[ "${1}" == "--help" || "${1}" == "-h" || "${1}" == "-?" ]]; then
    usage 0
elif [[ "${1}" == "--version" || "${1}" == "-v" ]]; then
    echo "${SCRIPT_VERSION}"
    exit 0
fi

# Parse Optional Command Line Input Parameters if provided
while [[ "${1}" != "" ]]; do
    case "${1}" in
        "--help" | "-h" | "-?") usage 0 ;;
        "--version" | "-v") echo "${SCRIPT_VERSION}" && exit 0 ;;
        "--model-alias" | "--model" | "-m") require_value "${@}" && CLAUDE_MODEL="${2}" && shift 2 ;;
        "--effort-level" | "--effort" | "-e") require_value "${@}" && CLAUDE_EFFORT="${2}" && shift 2 ;;
        "--session-id" | "--session" | "--id" | "-s" | "-i") require_value "${@}" && CLAUDE_ID="${2}" && shift 2 ;;
        # The worktree name is optional: with none (the input ends, or a flag is next, such as --prompt) Claude Code names the worktree
        "--worktree-name" | "--worktree" | "-w")
            if [[ ( "${2:-""}" == "" ) || ( "${2:0:1}" == "-" ) ]]; then
                CLAUDE_WORKTREE="${TRUE}" && shift
            else
                CLAUDE_WORKTREE="${2}" && shift 2
            fi ;;
        "--no-worktree") CLAUDE_WORKTREE="${FALSE}" && shift ;;
        "--resume-session" | "--resume" | "-rs" | "-r") CLAUDE_RESUME="${TRUE}" && shift ;;
        # Remote control never takes a value (owner ruling, 2026-11-04)
        "--remote-control-session" | "--remote-control" | "-rc") CLAUDE_REMOTE_CONTROL="${TRUE}" && shift ;;
        "--no-remote-control") CLAUDE_REMOTE_CONTROL="${FALSE}" && shift ;;
        "--dangerously-skip-permissions" | "--skip-permissions" | "-sp") CLAUDE_SKIP_PERMISSIONS="${TRUE}" && shift ;;
        "--initial-prompt" | "--prompt" | "-p") require_value "${@}" && CLAUDE_PROMPT="${2}" && shift 2 ;;
        *) usage 1 "Unknown argument: ${1}";;
    esac
done


########################################################################################################################################################################################################
# Define Script Constants for Claude Code interaction
########################################################################################################################################################################################################
CLAUDE_SKIP_PERMISSIONS_PARAM="${CLAUDE_SKIP_PERMISSIONS:-${DEFAULT_SKIP_PERMISSIONS}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_SKIP_PERMISSIONS_PARAM: ${CLAUDE_SKIP_PERMISSIONS_PARAM}" || true
CLAUDE_REMOTE_CONTROL_PARAM="${CLAUDE_REMOTE_CONTROL:-${DEFAULT_REMOTE_CONTROL}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_REMOTE_CONTROL_PARAM: ${CLAUDE_REMOTE_CONTROL_PARAM}" || true
CLAUDE_WORKTREE_PARAM="${CLAUDE_WORKTREE:-${DEFAULT_WORKTREE}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_WORKTREE_PARAM: ${CLAUDE_WORKTREE_PARAM}" || true
CLAUDE_PROMPT_PARAM="${CLAUDE_PROMPT:-${DEFAULT_PROMPT}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_PROMPT_PARAM: ${CLAUDE_PROMPT_PARAM}" || true
CLAUDE_EFFORT_PARAM="${CLAUDE_EFFORT:-${DEFAULT_EFFORT}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_EFFORT_PARAM: ${CLAUDE_EFFORT_PARAM}" || true
CLAUDE_RESUME_PARAM="${CLAUDE_RESUME:-${DEFAULT_RESUME}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_RESUME_PARAM: ${CLAUDE_RESUME_PARAM}" || true
CLAUDE_MODEL_PARAM="${CLAUDE_MODEL:-${DEFAULT_MODEL}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_MODEL_PARAM: ${CLAUDE_MODEL_PARAM}" || true
CLAUDE_ID_PARAM="${CLAUDE_ID:-${DEFAULT_ID}}"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "CLAUDE_ID_PARAM: ${CLAUDE_ID_PARAM}" || true


########################################################################################################################################################################################################
# Define the full parameter list for the Claude Code interactive session
########################################################################################################################################################################################################
# Built as an array and passed to wake_the_claude.bash as-is (no eval): every value stays exactly one argument, so a
# multi-word prompt arrives as one prompt with no literal quote characters, and no value is re-parsed by the shell.
CLAUDE_ARGS=()

[[ "${CLAUDE_MODEL_PARAM}" != "${FALSE}" ]] && CLAUDE_ARGS+=("${CLAUDE_MODEL_FLAG}" "${CLAUDE_MODEL_PARAM}")                                            # Add the model alias parameter if provided
[[ "${CLAUDE_EFFORT_PARAM}" != "${FALSE}" ]] && CLAUDE_ARGS+=("${CLAUDE_EFFORT_FLAG}" "${CLAUDE_EFFORT_PARAM}")                                         # Add the effort parameter if provided
[[ "${CLAUDE_ID_PARAM}" != "${FALSE}" ]] && CLAUDE_ARGS+=("${CLAUDE_ID_FLAG}" "${CLAUDE_ID_PARAM}")                                                     # Add the id parameter if provided
[[ "${CLAUDE_WORKTREE_PARAM}" != "${FALSE}" ]] && CLAUDE_ARGS+=("${CLAUDE_WORKTREE_FLAG}" "${CLAUDE_WORKTREE_PARAM}")                                   # Add the worktree: a name, or ${TRUE} for a bare --worktree

(( ${#CLAUDE_ARGS[@]} > 0 )) && CLAUDE_ARGS+=("${CLAUDE_SEPERATOR_FLAG}")                                                                              # Add the seperator flag if any "[--flag <parameter>]" arguments have been added

[[ "${CLAUDE_REMOTE_CONTROL_PARAM}" == "${TRUE}" ]] && CLAUDE_ARGS+=("${CLAUDE_REMOTE_CONTROL_FLAG}")                                                  # Add a bare --remote-control: on by default, and it never takes a value
[[ "${CLAUDE_RESUME_PARAM}" == "${TRUE}" ]] && CLAUDE_ARGS+=("${CLAUDE_RESUME_FLAG}" "${TRUE}")                                                        # Opt in to --resume when requested (wake_the_claude.bash needs a session id or a boolean after --resume)
[[ "${DEBUG}" == "${TRUE}" || "${CLAUDE_SKIP_PERMISSIONS_PARAM}" == "${TRUE}" ]] && CLAUDE_ARGS+=("${CLAUDE_SKIP_PERMISSIONS_FLAG}")                   # Opt in to --dangerously-skip-permissions only when explicitly requested or in debug mode
[[ "${CLAUDE_PROMPT_PARAM}" != "" && "${CLAUDE_PROMPT_PARAM}" != "${FALSE}" ]] && CLAUDE_ARGS+=("${CLAUDE_PROMPT_FLAG}" "${CLAUDE_PROMPT_PARAM}")      # Add the initial prompt if provided


########################################################################################################################################################################################################
# Pass through any additional arguments from the caller
if (( $# > 0 )); then
    CLAUDE_ARGS+=("${@}")
    [[ "${DEBUG}" == "${TRUE}" ]] && echo "${CLAUDE_ARGS[@]}" || true
fi


########################################################################################################################################################################################################
# Call Wake The Claude script with params
echo "Launching Default Interactive session with Claude Code"
[[ "${DEBUG}" == "${TRUE}" ]] && echo "${WAKE_THE_CLAUDE_SCRIPT} ${CLAUDE_ARGS[*]}" || true

"${WAKE_THE_CLAUDE_SCRIPT}" "${CLAUDE_ARGS[@]}"

echo "Closed Default Interactive session with Claude Code"

exit 0
