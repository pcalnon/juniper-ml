#!/usr/bin/env bash
########################################################################################################################################################################
# Author: Paul Calnon
# Date: 2026-03-12
# Version: 1.0.0
# Status: Development
# License: MIT
# Copyright: 2026 Paul Calnon
# Repository: https://github.com/pcalnon/juniper-ml
#
# Description:
#    this script is a wrapper for the claude code agent.
#    this script is not intended to be used directly.
#    this script performs the actual call to launch the claude code agent.
#    it is used to launch the claude code agent with the appropriate parameters.
#    it is also used to validate the session id and resume the session.
#    it is also used to save the session id to a file.
#    it is also used to retrieve the session id from a file.
########################################################################################################################################################################
# Notes:
#
#   Old Index Assignment Syntax:
#     MODEL_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     EFFORT_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     SESSION_ID_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     WORKTREE_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     REMOTE_CONTROL_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     PERMISSIONS_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     RESUME_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     SPACER_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     PROMPT_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     PATH_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     FILE_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     HEADLESS_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     FORK_SESSION_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     MODEL_VERSION_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     SCRIPT_VERSION_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     HELP_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#     USAGE_FLAGS_INDEX="${INITIAL_INDEX}" && INITIAL_INDEX=$((INITIAL_INDEX + 1))
#
########################################################################################################################################################################
# References:
#
#    echo "0. Script Call"
#    echo "1. Initial Script Params: \"${*}\""
#
#    declare -a PARAMS=("${@}")
#    echo "2. Script Params: \"${PARAMS[*]}\""
#
#    declare -a PPARAMS=()
#    declare -a SPPARAMS=()
#    declare -a FPARAMS=()
#    declare -a SFPARAMS=()
#
#    echo "3. Function Definition"
#    function bla() {
#        FPARAMS=("${@}")
#        echo "5.0. Function Param 1: \"${1}\""
#        echo "5.1. Function Params: \"${FPARAMS[*]}\""
#        shift 2
#        echo "5.1.1. Function Param 1: \"${1}\""
#        echo "5.2. Shifted Function Params: \"${*}\""
#        SFPARAMS=("${@}")
#        echo "5.3. Shifted Function Params: \"${SFPARAMS[*]}\""
#        set "${PARAMS[@]}"
#        echo "5.3.1. Function Param 1: \"${1}\""
#        echo "5.4. Set Script Params: \"${*}\""
#        PPARAMS=("${@}")
#        echo "5.5. Parent Params: \"${PPARAMS[*]}\""
#        shift 2
#        SPPARAMS=("${@}")
#        echo "5.5.1. Shifted Parent Param 1: \"${1}\""
#        echo "5.6. Shifted Parent Params: \"${*}\""
#        echo "5.7. Shifted Parent Params: \"${SPPARAMS[*]}\""
#        set "${SFPARAMS[@]}"
#        echo "5.7. Shifted Function Params: \"${*}\""
#        shift 2
#        echo "5.7.1. Function Param 1: \"${1}\""
#        echo "5.8. Double Shifted Function Params: \"${*}\""
#    }
#
#    echo "4. Function Call"
#    echo "5. bla 0 1 2 3 4 5 6 7 8 9"
#    bla 0 1 2 3 4 5 6 7 8 9
#
#    echo "6. Final Script Params \"${*}\""
#    echo "6.1. Script Param 1: \"${1}\""
#    set "${SPPARAMS[@]}"
#    echo "7. Function Params: \"${SFPARAMS[*]}\""
#    echo "7.1. Final Script Params \"${*}\""
#    echo "7.2. Script Param 1: \"${1}\""
#    echo "8. Shifted Function Params: \"${SFPARAMS[*]}\""
#    echo "9. Shifted Parent Params: \"${SPPARAMS[*]}\""
#
#    elif [[ ( ( "${CLAUDE_RESUME_VALUE[*]}" == "" ) || ( "${#CLAUDE_RESUME_VALUE[@]}" == "0" ) ) && ( ( "${session_id}" != "${FALSE}" ) || ( "${session_id}" == "" ) ) ]]; then
#    elif [[ ( "${CLAUDE_RESUME_VALUE[*]}" == "" ) || ( "${#CLAUDE_RESUME_VALUE[@]}" == "0" ) ]]; then
#
########################################################################################################################################################################


########################################################################################################################################################################
# Define global Variables
########################################################################################################################################################################
TRUE="0"
FALSE="1"
UNSAFE_TARGET="2"  # Distinct save_session_id() status for a security refusal (e.g. a symlink target)

DEBUG="${TRUE}"

WTC_DEBUG="${WTC_DEBUG:-${DEBUG}}"
EXIT_AFTER_USAGE_DEFAULT="${TRUE}"

# Only require a successful session-ID save when NOT in wtc debug mode. Explicit comparison
# (robust to non-numeric/empty WTC_DEBUG, unlike the previous parity arithmetic).
export REQUIRE_SAVED_SESSION_ID="${TRUE}"
if [[ "${WTC_DEBUG}" == "${TRUE}" ]]; then
    export REQUIRE_SAVED_SESSION_ID="${FALSE}"
fi

SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
# set -x
# PS4="+ ${SCRIPT_NAME}: ${FUNCNAME[1]}(${LINENO}): ${PS4}: "
# PS4="+ ${SCRIPT_NAME}: ${FUNCNAME[1]}(${LINENO}): "
# export PS4
# set +x

########################################################################################################################################################################
# Early function definitions (must precede top-level calls below)
########################################################################################################################################################################
function get_line_number() {
    [[ "${1:-""}" != "" ]] && { echo "${1%% *}" && return 0; } || { echo "-1" && return 1; }
}

function debug_log() {
    if [[ "${WTC_DEBUG}" == "${TRUE}" ]]; then
        local line && line="$( get_line_number "$( caller )" )"
        echo "${SCRIPT_NAME}: ${FUNCNAME[1]}(${line}): ${*}" 1>&2
    fi
}

function redact_uuid() {
    local value="$1"
    if (( ${#value} >= 12 )); then
        echo "${value:0:8}...${value: -4}"
    else
        echo "[redacted]"
    fi
}


########################################################################################################################################################################
# Define Script Directory Constants
########################################################################################################################################################################
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SESSIONS_DIR="${WTC_SESSIONS_DIR:-${REPO_ROOT}/scripts/sessions}"
LOGS_DIR="${WTC_LOGS_DIR:-${REPO_ROOT}/logs}"

PROMPT_DIR_NAME_DEFAULT="prompts"
PROMPT_DIR_DEFAULT="${WTC_PROMPT_DIR_DEFAULT:-${REPO_ROOT}/${PROMPT_DIR_NAME_DEFAULT}}"
export PROMPT_DIR_DEFAULT

mkdir -p "${SESSIONS_DIR}" "${LOGS_DIR}"


########################################################################################################################################################################
# Define Claude Parameter Arrays index values
########################################################################################################################################################################
# Define array variable to save script input parameters as they are parsed
declare -a UPDATED_PARAMS=()

export PARAM_FLAG_INDEX="0"
export PARAM_VALUE_INDEX="1"

SESSION_ID_FILE=""


########################################################################################################################################################################
# Define Model Name Constants
#     NOTE: This is where you would add new model names and aliases
########################################################################################################################################################################

########################################################################################################################################################################
# Define Model Full Name Constants
debug_log "Define Model Name Constants"
# NOTE: Add new Model Full Name here
MODEL_FABLE_NAME="claude-fable-5"
MODEL_OPUS_NAME="claude-opus-5"
MODEL_SONNET_NAME="claude-sonnet-4-6"
MODEL_HAIKU_NAME="claude-haiku-4-5"


########################################################################################################################################################
# Define Model Name Array
debug_log "Define Model Name Array"
declare -a MODEL_NAME_ARRAY
MODEL_NAME_ARRAY+=("${MODEL_OPUS_NAME}")
MODEL_NAME_ARRAY+=("${MODEL_HAIKU_NAME}")
MODEL_NAME_ARRAY+=("${MODEL_SONNET_NAME}")
MODEL_NAME_ARRAY+=("${MODEL_FABLE_NAME}")


########################################################################################################################################################
# Define Model name Alias Constants
debug_log "Define Model Name Alias Constants"
# NOTE: Add new Model Name Alias here
MODEL_FABLE_ALIAS="fable"
MODEL_OPUS_ALIAS="opus"
MODEL_SONNET_ALIAS="sonnet"
MODEL_HAIKU_ALIAS="haiku"

MODEL_DEFAULT="${MODEL_OPUS_ALIAS}"
export MODEL_DEFAULT


########################################################################################################################################################
# Define Model Alias Array
debug_log "Define Model Alias Array"
declare -a MODEL_ALIAS_ARRAY
MODEL_ALIAS_ARRAY+=("${MODEL_OPUS_ALIAS}")
MODEL_ALIAS_ARRAY+=("${MODEL_HAIKU_ALIAS}")
MODEL_ALIAS_ARRAY+=("${MODEL_SONNET_ALIAS}")
MODEL_ALIAS_ARRAY+=("${MODEL_FABLE_ALIAS}")


########################################################################################################################################################
# Define Array for Model Name and Alias Validation Checks
debug_log "Define Model Name and Alias Validation Array"
declare -a MODEL_TEST_ARRAY
# NOTE: Add new Model Name and Alias to Validation Array
MODEL_TEST_ARRAY+=("${MODEL_OPUS_NAME}")
MODEL_TEST_ARRAY+=("${MODEL_HAIKU_NAME}")
MODEL_TEST_ARRAY+=("${MODEL_SONNET_NAME}")
MODEL_TEST_ARRAY+=("${MODEL_FABLE_NAME}")
MODEL_TEST_ARRAY+=("${MODEL_OPUS_ALIAS}")
MODEL_TEST_ARRAY+=("${MODEL_HAIKU_ALIAS}")
MODEL_TEST_ARRAY+=("${MODEL_SONNET_ALIAS}")
MODEL_TEST_ARRAY+=("${MODEL_FABLE_ALIAS}")


########################################################################################################################################################################
# Define Claude Code Level of Effort Values Constants
########################################################################################################################################################################

########################################################################################################################################################################
# Define Claude Code Effort Values Constants
debug_log "Define Effort values"
EFFORT_LOW="low"
EFFORT_MED="medium"
EFFORT_HIGH="high"
EFFORT_XHIGH="xhigh"
EFFORT_MAX="max"
EFFORT_AUTO="auto"

# EFFORT_DEFAULT="${EFFORT_MAX}"
EFFORT_DEFAULT="${EFFORT_AUTO}"
export EFFORT_DEFAULT


########################################################################################################################################################################
# Define Claude Code Effort Array
debug_log "Define Effort Array"
declare -a EFFORT_ARRAY
EFFORT_ARRAY+=("${EFFORT_LOW}")
EFFORT_ARRAY+=("${EFFORT_MED}")
EFFORT_ARRAY+=("${EFFORT_HIGH}")
EFFORT_ARRAY+=("${EFFORT_XHIGH}")
EFFORT_ARRAY+=("${EFFORT_MAX}")
EFFORT_ARRAY+=("${EFFORT_AUTO}")


########################################################################################################################################################################
# Initialize Parsed Param values
########################################################################################################################################################################

########################################################################################################################################################################
# Define prompt parameter values
debug_log "Define Parsed Param values"
PATH_NAME=""
FILE_NAME=""
PROMPT_FILE=""
PROMPT_VALUE=""

PROMPT_VALUE_DEFAULT="Hello World, Claude!"
export PROMPT_VALUE_DEFAULT

PROMPT_FILE_DEFAULT="./${PROMPT_FILE_NAME_DEFAULT}"
export PROMPT_FILE_DEFAULT

PROMPT_PATH_DEFAULT="${PROMPT_PATH_DIR_DEFAULT}/${PROMPT_FILE_NAME_DEFAULT}"
export PROMPT_PATH_DEFAULT


########################################################################################################################################################################
# Define Parameter Flag and Value Arrays
debug_log "Define Parameter Flag and Value Arrays"
declare -a CLAUDE_MODEL_VALUE
declare -a CLAUDE_EFFORT_VALUE
declare -a CLAUDE_WORKTREE_VALUE
declare -a CLAUDE_REMOTE_CONTROL_VALUE
declare -a CLAUDE_SESSION_ID_VALUE
declare -a CLAUDE_PERMISSIONS_VALUE
declare -a CLAUDE_RESUME_VALUE
declare -a CLAUDE_PROMPT_VALUE
declare -a CLAUDE_PROMPT_FILE_VALUE
declare -a CLAUDE_PROMPT_PATH_VALUE
declare -a CLAUDE_HEADLESS_VALUE
declare -a CLAUDE_FORK_SESSION_VALUE


########################################################################################################################################################################
# Param values to be passed to Claude
debug_log "Define Param values to be passed to Claude"
CLAUDE_CODE_PROMPT=""
CLAUDE_CODE_PARAMS=()


########################################################################################################################################################################
# Valid Prompt Boolean Flags
debug_log "Define Valid Prompt Boolean Flags"
VALID_FILE_PARAM="${FALSE}"
VALID_PATH_PARAM="${FALSE}"
VALID_PROMPT_PARAM="${FALSE}"

PROMPT_DEFAULT="Hello World, Claude!"
export PROMPT_DEFAULT


########################################################################################################################################################################
# Define Input parameter flags
########################################################################################################################################################################

########################################################################################################################################################################
# Define Claude Code parameter flags
debug_log "Define Claude Code parameter flags"
CLAUDE_PERMISSIONS_FLAGS="--dangerously-skip-permissions"
CLAUDE_REMOTE_CONTROL_FLAGS="--remote-control"
CLAUDE_FORK_SESSION_FLAGS="--fork-session"
CLAUDE_PROMPT_FILE_FLAGS="--prompt-file"
CLAUDE_PROMPT_PATH_FLAGS="--prompt-path"
CLAUDE_SESSION_ID_FLAGS="--session-id"
CLAUDE_WORKTREE_FLAGS="--worktree"
CLAUDE_VERSION_FLAGS="--version"
CLAUDE_HEADLESS_FLAGS="--print"
CLAUDE_RESUME_FLAGS="--resume"
CLAUDE_EFFORT_FLAGS="--effort"
CLAUDE_MODEL_FLAGS="--model"
CLAUDE_PROMPT_FLAGS="--prompt"


########################################################################################################################################################################
# Define all valid Script Input parameter flags:
debug_log "Define Input parameter flags"
SPACER_FLAGS="--"
USAGE_FLAGS="-u | --usage"
HELP_FLAGS="-h | --help | -?"
FILE_FLAGS="-f | --file | --file-name"
PATH_FLAGS="-l | --path | --file-path"
PROMPT_FLAGS="-p | --prompt | --prompt-string"
WORKTREE_FLAGS="-w | ${CLAUDE_WORKTREE_FLAGS} | --work-tree | --working-tree"
MODEL_VERSION_FLAGS="-V | ${CLAUDE_VERSION_FLAGS} | --claude-version"
SCRIPT_VERSION_FLAGS="-v | --version"
EFFORT_FLAGS="-e | ${CLAUDE_EFFORT_FLAGS} | --effort-type | --effort-level"
HEADLESS_FLAGS="-a | ${CLAUDE_HEADLESS_FLAGS} | --agent | --silent | --headless"
REMOTE_CONTROL_FLAGS="-c | --remote | --control | ${CLAUDE_REMOTE_CONTROL_FLAGS}"
PERMISSIONS_FLAGS="-s | --skip | --skip-permissions | ${CLAUDE_PERMISSIONS_FLAGS}"
SESSION_ID_FLAGS="-i | --id | --session | ${CLAUDE_SESSION_ID_FLAGS} | --session-name | -t | --thread | --thread-name | --thread-id"
MODEL_FLAGS="-m | ${CLAUDE_MODEL_FLAGS} | --llm-model | --ai-model | --model-type"
RESUME_FLAGS="-r | ${CLAUDE_RESUME_FLAGS} | --resume-thread | --resume-session"
FORK_SESSION_FLAGS="--fork | ${CLAUDE_FORK_SESSION_FLAGS} | --resume-fork | --resume-fork_session"


########################################################################################################################################################################
# Initialize Index values for Valid Patterns Array
debug_log "Define Index values for Valid Patterns Array"
INITIAL_INDEX=0
MODEL_FLAGS_INDEX="${INITIAL_INDEX}";          INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "MODEL_FLAGS_INDEX: ${MODEL_FLAGS_INDEX}"
EFFORT_FLAGS_INDEX="${INITIAL_INDEX}";         INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "EFFORT_FLAGS_INDEX: ${EFFORT_FLAGS_INDEX}"
WORKTREE_FLAGS_INDEX="${INITIAL_INDEX}";       INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "WORKTREE_FLAGS_INDEX: ${WORKTREE_FLAGS_INDEX}"
REMOTE_CONTROL_FLAGS_INDEX="${INITIAL_INDEX}"; INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "REMOTE_CONTROL_FLAGS_INDEX: ${REMOTE_CONTROL_FLAGS_INDEX}"
SESSION_ID_FLAGS_INDEX="${INITIAL_INDEX}";     INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "SESSION_ID_FLAGS_INDEX: ${SESSION_ID_FLAGS_INDEX}"
PERMISSIONS_FLAGS_INDEX="${INITIAL_INDEX}";    INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "PERMISSIONS_FLAGS_INDEX: ${PERMISSIONS_FLAGS_INDEX}"
RESUME_FLAGS_INDEX="${INITIAL_INDEX}";         INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "RESUME_FLAGS_INDEX: ${RESUME_FLAGS_INDEX}"
SPACER_FLAGS_INDEX="${INITIAL_INDEX}";         INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "SPACER_FLAGS_INDEX: ${SPACER_FLAGS_INDEX}"
PROMPT_FLAGS_INDEX="${INITIAL_INDEX}";         INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "PROMPT_FLAGS_INDEX: ${PROMPT_FLAGS_INDEX}"
PATH_FLAGS_INDEX="${INITIAL_INDEX}";           INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "PATH_FLAGS_INDEX: ${PATH_FLAGS_INDEX}"
FILE_FLAGS_INDEX="${INITIAL_INDEX}";           INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "FILE_FLAGS_INDEX: ${FILE_FLAGS_INDEX}"
HEADLESS_FLAGS_INDEX="${INITIAL_INDEX}";       INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "HEADLESS_FLAGS_INDEX: ${HEADLESS_FLAGS_INDEX}"
FORK_SESSION_FLAGS_INDEX="${INITIAL_INDEX}";   INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "FORK_SESSION_FLAGS_INDEX: ${FORK_SESSION_FLAGS_INDEX}"
MODEL_VERSION_FLAGS_INDEX="${INITIAL_INDEX}";  INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "MODEL_VERSION_FLAGS_INDEX: ${MODEL_VERSION_FLAGS_INDEX}"
SCRIPT_VERSION_FLAGS_INDEX="${INITIAL_INDEX}"; INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "SCRIPT_VERSION_FLAGS_INDEX: ${SCRIPT_VERSION_FLAGS_INDEX}"
HELP_FLAGS_INDEX="${INITIAL_INDEX}";           INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "HELP_FLAGS_INDEX: ${HELP_FLAGS_INDEX}"
USAGE_FLAGS_INDEX="${INITIAL_INDEX}";          INITIAL_INDEX=$((INITIAL_INDEX + 1)); debug_log "USAGE_FLAGS_INDEX: ${USAGE_FLAGS_INDEX}"


########################################################################################################################################################################
# Initialize Parsed Param values
debug_log "Define Valid Patterns Array"
declare -a VALID_PATTERNS

VALID_PATTERNS[MODEL_FLAGS_INDEX]="${MODEL_FLAGS}"
VALID_PATTERNS[EFFORT_FLAGS_INDEX]="${EFFORT_FLAGS}"
VALID_PATTERNS[WORKTREE_FLAGS_INDEX]="${WORKTREE_FLAGS}"
VALID_PATTERNS[REMOTE_CONTROL_FLAGS_INDEX]="${REMOTE_CONTROL_FLAGS}"
VALID_PATTERNS[SESSION_ID_FLAGS_INDEX]="${SESSION_ID_FLAGS}"
VALID_PATTERNS[PERMISSIONS_FLAGS_INDEX]="${PERMISSIONS_FLAGS}"
VALID_PATTERNS[RESUME_FLAGS_INDEX]="${RESUME_FLAGS}"
VALID_PATTERNS[SPACER_FLAGS_INDEX]="${SPACER_FLAGS}"
VALID_PATTERNS[PROMPT_FLAGS_INDEX]="${PROMPT_FLAGS}"
VALID_PATTERNS[PATH_FLAGS_INDEX]="${PATH_FLAGS}"
VALID_PATTERNS[FILE_FLAGS_INDEX]="${FILE_FLAGS}"
VALID_PATTERNS[HEADLESS_FLAGS_INDEX]="${HEADLESS_FLAGS}"
VALID_PATTERNS[FORK_SESSION_FLAGS_INDEX]="${FORK_SESSION_FLAGS}"
VALID_PATTERNS[MODEL_VERSION_FLAGS_INDEX]="${MODEL_VERSION_FLAGS}"
VALID_PATTERNS[SCRIPT_VERSION_FLAGS_INDEX]="${SCRIPT_VERSION_FLAGS}"
VALID_PATTERNS[HELP_FLAGS_INDEX]="${HELP_FLAGS}"
VALID_PATTERNS[USAGE_FLAGS_INDEX]="${USAGE_FLAGS}"


########################################################################################################################################################################
# Define functions for wake_the_claude.bash script
########################################################################################################################################################################

########################################################################################################################################################################
# matches_pattern(): Match a value against a pipe-delimited pattern string
function matches_pattern() {
    local ip_value="$1"
    local pattern="$2"
    local IFS='|'
    local -a candidates=()
    local candidate
    read -r -a candidates <<< "${pattern}"
    for candidate in "${candidates[@]}"; do
        candidate="${candidate#"${candidate%%[![:space:]]*}"}"
        candidate="${candidate%"${candidate##*[![:space:]]}"}"
        [[ "${ip_value}" == "${candidate}" ]] && return "${TRUE}"
    done
    return "${FALSE}"
}

########################################################################################################################################################################
# is_valid_uuid(): Validate UUID format (32 hex digits with optional hyphens)
function is_valid_uuid() {
    # example uuid="7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"
    local uuid="$1"
    debug_log "Validating UUID format: $(redact_uuid "${uuid}")"
    if [[ ${uuid//-/} =~ ^[[:xdigit:]]{32}$ ]]; then
        debug_log "UUID is valid: $(redact_uuid "${uuid}")"
        return "${TRUE}"
    else
        debug_log "UUID is invalid"
        return "${FALSE}"
    fi
}

########################################################################################################################################################################
# Generate UUID with fallbacks for environments without uuidgen
function generate_uuid() {
    local generated_uuid=""
    if [[ ( "${generated_uuid}" == "" ) && ( -x "$(command -v uuidgen)" ) ]]; then
        generated_uuid="$(uuidgen 2>/dev/null)"
        if ! is_valid_uuid "${generated_uuid}"; then
            generated_uuid=""
        fi
    fi
    if [[ ( "${generated_uuid}" == "" ) && ( -r "/proc/sys/kernel/random/uuid" ) ]]; then
        generated_uuid="$(cat "/proc/sys/kernel/random/uuid" 2>/dev/null)"
        if ! is_valid_uuid "${generated_uuid}"; then
            generated_uuid=""
        fi
    fi
    if [[ ( "${generated_uuid}" == "" ) && ( -x "$(command -v python3)" ) ]]; then
        generated_uuid="$(python3 -c 'import uuid; print(uuid.uuid4())' 2>/dev/null)"
        if ! is_valid_uuid "${generated_uuid}"; then
            generated_uuid=""
        fi
    fi
    debug_log "Freshly Generated UUID: ${generated_uuid}"
    if [[ "${generated_uuid}" == "" ]]; then
        debug_log "Error: No valid UUID generated"
        return "${FALSE}"
    elif ! is_valid_uuid "${generated_uuid}"; then
        debug_log "Error: Generated UUID is not a valid UUID"
        return "${FALSE}"
    fi
    debug_log "Validated the Generated UUID: ${generated_uuid}"
    echo "${generated_uuid}"
    return "${TRUE}"
}

########################################################################################################################################################################
# is_valid_file(): Check if a file is valid
function is_valid_file() {
    debug_log "Checking if file is valid"
    local current_file="${1:-""}"
    debug_log "Current File: \"${current_file}\""
    local result_value="${TRUE}"

    if [[ ! -f "${current_file}" ]]; then
        debug_log "File is not valid: \"${current_file}\""
        result_value="${FALSE}"
    else
        debug_log "File is valid: \"${current_file}\""
    fi
    debug_log "Result Value: \"${result_value}\""

    return "${result_value}"
}

########################################################################################################################################################################
# is_valid_dir(): Check if a directory is valid
function is_valid_dir() {
    debug_log "Checking if directory is valid"
    local current_dir="${1:-""}"
    debug_log "Current Directory: \"${current_dir}\""
    local result_value="${TRUE}"

    if [[ ! -d "${current_dir}" ]]; then
        debug_log "Directory is not valid: \"${current_dir}\""
        result_value="${FALSE}"
    else
        debug_log "Directory is valid: \"${current_dir}\""
    fi
    debug_log "Result Value: \"${result_value}\""

    return "${result_value}"
}

########################################################################################################################################################################
# get_valid_session_id_file(): Get a valid session id file path to save current session id
function get_valid_session_id_file() {
    local session_id="$1" && shift
    debug_log "Session ID: ${session_id}"
    local safe_filename
    safe_filename="$(basename "${session_id}").txt"
    debug_log "Safe Filename: ${safe_filename}"
    local target_path="${SESSIONS_DIR}/${safe_filename}"
    debug_log "Target Path: ${target_path}"
    if [[ -L "${target_path}" ]]; then
        debug_log "Error: target file is a symlink — refusing to write"
        return "${UNSAFE_TARGET}"
    fi
    debug_log "Validated Target Path: ${target_path}"
    echo "${target_path}"
    return "${TRUE}"
}

########################################################################################################################################################################
# save_session_id(): Extract session ID from value string and persist to file
function save_session_id() {
    local session_id_value="$1"
    local session_id="$2"
    debug_log "Extracting Session ID and saving to file"
    debug_log "Session ID Value: \"${session_id_value}\""
    debug_log "Session ID: \"${session_id}\""
    if [[ "${session_id}" == "" ]]; then
        session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
    fi
    debug_log "Parsed Session ID: \"${session_id}\""
    is_valid_uuid "${session_id}"
    RESULT="$?"
    if [[ "${RESULT}" != "${TRUE}" ]]; then
        debug_log "Error: Session ID is not a valid UUID — refusing to write file"
        return "${FALSE}"
    fi
    debug_log "Validated Parsed Session ID UUID: \"${session_id}\""
    local target_path
    if [[ "$(target_path="$(get_valid_session_id_file "${session_id_value}" "${session_id}")")" != "${TRUE}" ]]; then
        debug_log "Error: Failed to get a valid session id file path."
        return "${UNSAFE_TARGET}"
    fi
    debug_log "Target Path: \"${target_path}\""
    echo "${session_id}" > "${target_path}"
    debug_log "Saved Session ID $(redact_uuid "${session_id}") to file: \"${target_path}\""
    SESSION_ID_FILE="${target_path}"
    return "${TRUE}"
}

########################################################################################################################################################################
# retrieve_session_id(): Read session ID from a file in SESSIONS_DIR
function retrieve_session_id() {
    local session_id_file="$1"
    debug_log "Retrieving Session ID from file: ${session_id_file}"
    local session_id
    session_id="$(cat "${session_id_file}")"
    debug_log "Completed retrieving Session ID from file: \"${session_id_file}\""
    echo "${session_id}"
    return "${TRUE}"
}

########################################################################################################################################################################
# validate_session_id(): Validate session ID as UUID or resolve from session file
function validate_session_id() {
    local session_id="$1"
    local session_id_filename="${session_id}"
    local session_id_file="${SESSIONS_DIR}/${session_id_filename}"

    # 1st Pass: Check if the session id is empty or invalid
    debug_log "Validating Session ID, 1st Pass: \"$(redact_uuid "${session_id}")\""
    if [[ "${session_id}" == "" ]]; then
        debug_log "Session ID validation, 1st Pass: Failed for empty session id"
        return "${FALSE}"
    elif is_valid_uuid "${session_id}"; then
        debug_log "Session ID validation, 1st Pass: Input is a valid UUID"
        echo "${session_id}"
        return "${TRUE}"
    elif [[ "${session_id_filename}" == */* ]]; then
        debug_log "Session ID validation, 1st Pass: Failed for session id filename containing path separators"
        return "${FALSE}"
    elif [[ "${session_id_filename}" != *.txt ]]; then
        debug_log "Session ID validation, 1st Pass: Failed for session id filename not having .txt extension"
        return "${FALSE}"
    else
        debug_log "Session ID validation, 1st Pass: Succeeded for \"$(redact_uuid "${session_id}")\""
    fi

    # 2nd Pass: Step 1: Check if the session id is a file and retrieve the session id from the file
    if [[ -f "${session_id_file}" ]]; then
        debug_log "Session ID is a file: \"${session_id_file}\""
        session_id="$(retrieve_session_id "${session_id_file}")"
        debug_log "Completed retrieving Session ID from file: \"$(redact_uuid "${session_id}")\""
    else
        debug_log "Verified Session ID is not a file, Checking for valid UUID: \"$(redact_uuid "${session_id}")\""
    fi

    # 2nd Pass: Step 2: Check if the session id is a valid uuid
    if is_valid_uuid "${session_id}"; then
        debug_log "Session ID is valid: \"$(redact_uuid "${session_id}")\""
    else
        debug_log "Session ID file did not contain a valid UUID"
        return "${FALSE}"
    fi

    # Return the validated session id
    debug_log "Session ID validation, 2nd Pass: Succeeded for \"$(redact_uuid "${session_id}")\""
    echo "${session_id}"
    return "${TRUE}"
}

########################################################################################################################################################################
# Validate Model parameter value
function validate_model() {
    debug_log "Validating Model parameter value"
    local model_param="${1,,}"
    debug_log "Model parameter value: ${model_param}"
    local valid_model="${TRUE}"
    debug_log "1. Valid Model parameter value: ${valid_model}"

    debug_log "Validate Claude Code Model Param Value: ${model_param}"
    for current_model in "${MODEL_TEST_ARRAY[@]}"; do
        if [[ "${model_param}" == "${current_model,,}" ]]; then
            debug_log "Model Validated: ${model_param}"
            break
        fi
    done
    debug_log "2. Valid Model parameter value: ${valid_model}"
    if [[ "${valid_model}" != "${TRUE}" ]]; then
        debug_log "Error: Specified Model is not Valid: ${model_param}"
        valid_model="${FALSE}"
    else
        debug_log "Successfully Validated Claude Code Model Param Value: ${model_param}"
    fi
    debug_log "3. Valid Model parameter value: ${valid_model}"
    return "${valid_model}"
}

########################################################################################################################################################################
# Validate Effort parameter value
function validate_effort() {
    local EFFORT_PARAM="${1,,}"
    local VALID_EFFORT="${FALSE}"
    debug_log "Validate Claude Code Effort Param Value: ${EFFORT_PARAM}"
    for CURRENT_EFFORT in "${EFFORT_ARRAY[@]}"; do
        if [[ "${EFFORT_PARAM}" == "${CURRENT_EFFORT,,}" ]]; then
            debug_log "Effort Validated: ${EFFORT_PARAM}"
            VALID_EFFORT="${TRUE}"
            break
        fi
    done
    if [[ "${VALID_EFFORT}" != "${TRUE}" ]]; then
        debug_log "Error: Specified Effort is not Valid: ${EFFORT_PARAM}"
        usage "${FALSE}"
    fi
    debug_log "Validated Claude Code Effort Param Value: ${EFFORT_PARAM}"
    return "${VALID_EFFORT}"
}


########################################################################################################################################################################
# Define functions to parse and process each input parameter flag type
########################################################################################################################################################################

########################################################################################################################################################################
# Add session id flags
function parse_session_id_flags() {
    debug_log "Parsing session id flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local session_id="${2:-""}"
    debug_log "Session ID: \"${session_id}\""
    local resume_session_id=""
    local result_value="${TRUE}"

    # Check if a Previous session is being resumed
    # Scenario 1: No Session ID Flag or Value Provided
    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Session ID Flag."
        result_value="${UNSAFE_TARGET}"
        return "${result_value}"
    # Scenario 2: this scenario means: we are resuming a previous session and the resume value is apparently a valid session id
    elif (( "${#CLAUDE_RESUME_VALUE[*]}" >= PARAM_VALUE_INDEX )) && [[ ( "${CLAUDE_RESUME_VALUE[1]}" != "" ) && ( "${CLAUDE_RESUME_VALUE[1]}" != "${FALSE}" ) ]]; then
        resume_session_id="${CLAUDE_RESUME_VALUE[PARAM_VALUE_INDEX]}"
        debug_log "Resume Session ID: ${resume_session_id}"
        if [[ "$(validate_session_id "${resume_session_id}")" != "${TRUE}" ]]; then
            # This scenario means: we are resuming a previous session but the resume session id value is invalid
            debug_log "Warning: Failed to validate Resume Session ID: \"${resume_session_id}\"."
            resume_session_id=""
        else
            # This scenario means: we are resuming a previous session and the resume value is apparently valid
            debug_log "Resume Session ID validated: $(redact_uuid "${resume_session_id}")"
        fi
    # Scenario 3: this scenario means: we are not resuming a previous session
    else
        debug_log "A Previous session is NOT being resumed."
    fi
    # Check if a New, Valid Session ID has been provided, needs to be created, or will not be created
    # Scenario 1: this scenario means: we are not creating a new session id
    if [[ "${session_id}" == "${FALSE}" ]]; then
        debug_log "Warning: Received False Session ID Value."
        session_id="" && shift 2  # shift to consume the session id flag and session id boolean false value
    # Scenario 2: this scenario means: we have not been provided with a new session id and one must be created
    elif [[ ( "${session_id}" == "" ) || ( "${session_id:0:2}" == "${SPACER_FLAGS}" ) || ( "${session_id}" == "${TRUE}" ) ]]; then
        # Handle edge case where the session id is true and we need to shift to the next parameter to consume the true value
        if [[ "${session_id}" == "${TRUE}" ]]; then
            debug_log "Warning: Received True Session ID Value. Shifting to next parameter."
            shift 2  # shift to consume the session id flag and session id boolean true value
        else
            debug_log "Warning: Received Empty Session ID Value."
            shift  # shift to only consume the session id flag
        fi
        # Generate a new session id and validate it
        session_id="$(generate_uuid)" && result_value="$?"
        if [[ "${result_value}" != "${TRUE}" ]]; then
            debug_log "Error: Failed to generate a valid UUID for Session ID."
            result_value="${FALSE}"
        elif [[ "$(validate_session_id "${session_id}")" != "${TRUE}" ]]; then
            debug_log "Error: Failed to validate Session ID."
            result_value="${FALSE}"
        else
            debug_log "New Session ID generated and validated: $(redact_uuid "${session_id}")"
        fi
    # Scenario 3: this scenario means: we have received a valid session id
    elif validate_session_id "${session_id}"; then
        debug_log "Session ID validated: $(redact_uuid "${session_id}")"
        shift 2  # shift to consume the session id flag and valid session id value
    # Scenario 4: this scenario means: we have received an invalid but non-edgecase session id
    else
        debug_log "Warning: Received Invalid Session ID Value: \"${session_id}\"."
        # Attempt to Retrieve the session id from the file
        local session_id_file="${SESSION_ID_FILE}"
        if [[ "${session_id_file}" == "" ]]; then
            debug_log "Warning: No Session ID File provided."
            debug_log "Skipping Session ID retrieval."
        else
            debug_log "Retrieving Session ID from file: ${session_id_file}"
            session_id="$(retrieve_session_id "${session_id_file}")" && result_value="$?"
            if [[ "${result_value}" != "${TRUE}" ]]; then
                debug_log "Warning: Failed to retrieve Session ID from file."
                debug_log "Skipping Session ID retrieval."
            else
                debug_log "Session ID retrieved: $(redact_uuid "${session_id}")"
            fi
        fi
    fi
    # Determine wich potential session id value to use
    if [[ ( "${resume_session_id}" == "" ) && ( "${session_id}" == "" ) ]]; then
        debug_log "Warning: No valid Session ID or Resume Session ID value provided."
        debug_log "Calling claude code without a session id"
    elif [[ "${resume_session_id}" != "" ]]; then
        debug_log "Calling claude code with a resume session id: $(redact_uuid "${resume_session_id}")"
        session_id="${resume_session_id}"
    elif [[ "${session_id}" != "" ]]; then
        debug_log "Calling claude code with a new session id: $(redact_uuid "${session_id}")"
    else
        debug_log "Error: Unable to evaluate Session ID and Resume Session ID values."
        result_value="${FALSE}"
        return "${result_value}"
    fi
    # Set the session id value in claude code parameters array
    debug_log "Setting Session ID Value in Claude Code Parameters Array: $(redact_uuid "${session_id}")"
    CLAUDE_SESSION_ID_VALUE=("${CLAUDE_SESSION_ID_FLAGS}" "${session_id}")
    debug_log "Claude Code Parameters Array: $(redact_uuid "${CLAUDE_SESSION_ID_VALUE[@]}")"
    # Save the session id to the file
    debug_log "Saving Session ID to File: $(redact_uuid "${session_id}")"
    if [[ "$(save_session_id "${CLAUDE_SESSION_ID_VALUE[@]}")" != "${TRUE}" ]]; then
        debug_log "Error: Failed to save Session ID value."
        result_value="${FALSE}"
    else
        debug_log "Session ID saved: $(redact_uuid "${session_id}")"
    fi

    # Update the current params array
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: $(redact_uuid "${CURRENT_PARAMS[@]}")"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: $(redact_uuid "${UPDATED_PARAMS[@]}")"

    return "${result_value}"
}

########################################################################################################################################################################
# parse_resume_flags(): Parse resume flags
function parse_resume_flags() {
    debug_log "Parsing resume flags"
    local resume_flag="${1:-""}"
    debug_log "Resume Flag: \"${resume_flag}\""
    local resume_value="${2:-""}"
    debug_log "Resume Value: \"${resume_value}\""
    local result_value="${TRUE}"

    # Scenario 1: this scenario means: we have received an empty resume flag
    if [[ "${resume_flag}" == "" ]]; then
        debug_log "Error: Received Empty Resume Flag. Exiting..."
        result_value="${FALSE}"
    # Scenario 2: this scenario means: we have received a false boolean resume value
    elif [[ "${resume_value}" == "${FALSE}" ]]; then
        debug_log "Warning: Received False Resume Value."
        shift 2  # shift to consume the resume flag and resume boolean false value
        # Note: this means we are NOT resuming a previous session
        CLAUDE_RESUME_VALUE=()
    # Scenario 3: this scenario means: we have received an empty or a true boolean resume value
    elif [[ ( "${resume_value}" == "${TRUE}" ) || ( "${resume_value}" == "" ) ]]; then
        debug_log "Warning: Received Resume Flag with empty or true boolean value instead of a valid Resume Session ID."
        shift  # shift to consume the resume flag
        if [[ "${resume_value}" == "${TRUE}" ]]; then
            shift  # shift to consume the resume boolean true value
        fi
        local session_id=""
        if (( ${#CLAUDE_SESSION_ID_VALUE[*]} >= ( PARAM_VALUE_INDEX + 1 ) )); then
            debug_log "Session ID already assigned: $(redact_uuid "${CLAUDE_SESSION_ID_VALUE[@]}")"
            session_id="${CLAUDE_SESSION_ID_VALUE[PARAM_VALUE_INDEX]}"
            debug_log "Validating Session ID: $(redact_uuid "${session_id}")"
            if validate_session_id "${session_id}"; then
                debug_log "Session ID validated: $(redact_uuid "${session_id}")"
                CLAUDE_RESUME_VALUE=("${CLAUDE_RESUME_FLAGS}" "${session_id}")
                debug_log "Resume Value: $(redact_uuid "${CLAUDE_RESUME_VALUE[@]}")"
            else
                debug_log "Error: Received an Invalid Session ID: \"${session_id}\"."
                CLAUDE_RESUME_VALUE=("${CLAUDE_RESUME_FLAGS}")
            fi
        else
            debug_log "Warning: The Claude Code Session ID Parameter is uninitialized: \"${CLAUDE_SESSION_ID_VALUE[*]}\"."
            CLAUDE_RESUME_VALUE=("${CLAUDE_RESUME_FLAGS}")
        fi
        debug_log "Initialized Claude Code Resume Parameters Array: $(redact_uuid "${CLAUDE_RESUME_VALUE[@]}")"
    # Scenario 5: this scenario means: we have received a valid resume value
    elif [[ ( "${resume_value:0:1}" != "-" ) ]] && validate_session_id "${resume_value}"; then
        debug_log "Session ID validated: $(redact_uuid "${resume_value}")"
        shift 2 # shift to consume the resume flag and resume value
        CLAUDE_RESUME_VALUE=("${CLAUDE_RESUME_FLAGS}" "${resume_value}")
    # Scenario 7: this scenario means: we have received a valid resume flag and an invalid resume value
    else
        debug_log "Error: Received Invalid Resume Value: \"${resume_value}\". Skipping Resume Flag and Value."
        shift 2 # shift to consume the resume flag and resume value
        result_value="${FALSE}"
    fi
    debug_log "Claude Resume Value: [${CLAUDE_RESUME_VALUE[*]}]"
    debug_log "Result Value: \"${result_value}\""

    # Update current params array
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################
# Add Model Flag
function parse_add_model_flags() {
    debug_log "Parsing add model flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_model="${2:-""}"
    debug_log "Current Model: \"${current_model}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Model Flag."
        CLAUDE_MODEL_VALUE=()
        result_value="${UNSAFE_TARGET}"
    elif [[ "${current_model}" == "${FALSE}" ]]; then
        debug_log "Warning: Received False Boolean as Model Name."
        debug_log "Model not included in claude code parameters array"
        CLAUDE_MODEL_VALUE=() && shift 2  # shift to consume the model flag and model boolean false value
    elif [[ ( "${current_model}" == "${TRUE}" ) || ( "${current_model}" == "" ) || ( "${current_model:0:2}" == "${SPACER_FLAGS}" ) ]]; then
        debug_log "Warning: Received an Edge Case Model Name: \"${current_model}\"."
        shift  # shift to consume the model flag
        if [[ "${current_model}" == "${TRUE}" ]]; then
            debug_log "Warning: Received True Boolean as Model Name."
            shift  # shift to consume the model boolean true value
        elif [[ "${current_model}" == "" ]]; then
            debug_log "Warning: Received Empty Model Name."
            # Do not shift parameters: Current Model Value is empty
        elif [[ "${current_model:0:2}" == "${SPACER_FLAGS}" ]]; then
            debug_log "Warning: Received Spacer Flags as Model Name."
            shift  # shift to consume the spacer flag value
        else
            debug_log "Warning: Received an Edge Case Model Name that has an invalid value: \"${current_model}\"."
            shift  # shift to consume the invalid model value
            result_value="${FALSE}"
        fi
        debug_log "Setting Default Model Name: \"${current_model}\""
        current_model="${MODEL_DEFAULT}"
        debug_log "Setting Claude Model Value: \"${CLAUDE_MODEL_FLAGS}\" \"${current_model}\""
        CLAUDE_MODEL_VALUE=("${CLAUDE_MODEL_FLAGS}" "${current_model}")
        debug_log "Claude Model Value: [${CLAUDE_MODEL_VALUE[*]}]"
    elif validate_model "${current_model}"; then
        # TODO: this check succeeds in validate_model() function but is failing here
        debug_log "Selected Model Name validated: \"${current_model}\""
        CLAUDE_MODEL_VALUE=("${CLAUDE_MODEL_FLAGS}" "${current_model}") && shift 2 # shift to consume the model flag and model name
    else
        debug_log "Warning: Received an Invalid but Non-Edgecase Model Name: \"${current_model}\"."
        current_model="${MODEL_DEFAULT}" && shift 2 # shift to consume the model flag and invalid model name
        debug_log "Setting Default Model Name: \"${current_model}\""
        debug_log "Setting Claude Model Value: \"${CLAUDE_MODEL_FLAGS}\" \"${current_model}\""
        CLAUDE_MODEL_VALUE=("${CLAUDE_MODEL_FLAGS}" "${current_model}")
        debug_log "Claude Model Value: [${CLAUDE_MODEL_VALUE[*]}]"
        result_value="${FALSE}"
    fi
    debug_log "Claude Model Value: \"${CLAUDE_MODEL_VALUE[*]}\""
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Add Effort Flag
function parse_add_effort_flags() {
    debug_log "Parsing effort flags"
    local current_flag=""
    current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_effort=""
    current_effort="${2:-""}"
    debug_log "Current Effort: \"${current_effort}\""
    # local valid_effort_name="${FALSE}"
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Effort Flag. Exiting..."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_EFFORT_VALUE=()
    elif matches_pattern "${current_flag}" "${CLAUDE_EFFORT_FLAGS}"; then
        debug_log "Received a Valid Effort Flag"
        shift  # shift to consume the effort flag

        if [[ "${current_effort}" == "${FALSE}" ]]; then
            debug_log "Warning: Received False Effort Value."
            CLAUDE_EFFORT_VALUE=() && shift  # shift to consume the effort boolean false value
        elif [[ ( "${current_effort}" == "${TRUE}" ) || ( "${current_effort}" == "" ) || ( "${current_effort:0:2}" == "${SPACER_FLAGS}" ) ]]; then
            debug_log "Warning: Received an Edge Case Effort Value: \"${current_effort}\"."
            if [[ "${current_effort}" == "${TRUE}" ]]; then
                shift  # shift to consume the effort boolean true value
            fi
            current_effort="${EFFORT_DEFAULT}"
            debug_log "Setting Claude Effort Value: \"${CLAUDE_EFFORT_FLAGS}\" \"${current_effort}\""
            CLAUDE_EFFORT_VALUE=("${CLAUDE_EFFORT_FLAGS}" "${current_effort}")
        elif validate_effort "${current_effort}"; then
            debug_log "Current Effort Name validated: \"${current_effort}\""
            CLAUDE_EFFORT_VALUE=("${CLAUDE_EFFORT_FLAGS}" "${current_effort}") && shift  # shift to consume the effort name
        else
            debug_log "Warning: Received an Invalid but Non-empty Edge Case Effort Name: \"${current_effort}\"."
            current_effort="${EFFORT_DEFAULT}"
            debug_log "Setting Claude Effort Value: \"${CLAUDE_EFFORT_FLAGS}\" \"${current_effort}\""
            CLAUDE_EFFORT_VALUE=("${CLAUDE_EFFORT_FLAGS}" "${current_effort}")
            result_value="${FALSE}"
        fi
        debug_log "Claude Effort Value: [${CLAUDE_EFFORT_VALUE[*]}]"
        debug_log "Result Value: \"${result_value}\""
    else
        debug_log "Warning: Received a non-empty but Invalid Effort flag: \"${current_flag}\"."
        # TODO: this might need a more sophisticated approach to handle the current effort value
        CLAUDE_EFFORT_VALUE=() && shift 2  # shift to consume the effort flag and effort boolean false value
        result_value="${FALSE}"
    fi
    debug_log "Effort Value: \"${CLAUDE_EFFORT_VALUE[*]}\""
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Add Permissions Flag
function parse_add_permissions_flags() {
    debug_log "Parsing add permissions flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_permissions="${2:-""}"
    debug_log "Current Permissions: \"${current_permissions}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Permissions Flag."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_PERMISSIONS_VALUE=()
    elif matches_pattern "${current_flag}" "${PERMISSIONS_FLAGS}"; then
        debug_log "Received Valid Permissions Flag: \"${current_flag}\""
        shift  # shift to consume the permissions flag
        if [[ "${current_permissions}" == "" ]]; then
            debug_log "Warning: Received Empty Permissions Value."
            # Do not shift parameters: Current Permissions Value is empty
        elif [[ "${current_permissions:0:2}" == "${SPACER_FLAGS}" ]]; then
            debug_log "Warning: Received Spacer Flags as Permissions Value."
            # Do not shift parameters: Current Permissions Value is a spacer flag
        elif matches_pattern "${current_permissions}" "${PERMISSIONS_FLAGS}"; then
            debug_log "Received Valid Permissions Value: \"${current_permissions}\""
            shift  # shift to consume the permissions value
        else
            debug_log "Warning: Received a non-edgecase but Invalid Permissions Value: \"${current_permissions}\"."
            result_value="${FALSE}" && shift  # shift to consume the invalid permissions value
        fi
        CLAUDE_PERMISSIONS_VALUE=("${CLAUDE_PERMISSIONS_FLAGS}")
    else
        debug_log "Warning: Received an Invalid Permissions Flag: \"${current_flag}\"."
        result_value="${FALSE}" && shift  # shift to consume the permissions flag
        if matches_pattern "${current_permissions}" "${PERMISSIONS_FLAGS}"; then
            debug_log "Received Valid Permissions Value: \"${current_permissions}\""
            shift  # shift to consume the permissions value
            CLAUDE_PERMISSIONS_VALUE=("${CLAUDE_PERMISSIONS_FLAGS}")
        else
            if [[ "${current_permissions}" == "" ]]; then
                debug_log "Warning: Received Empty Permissions Value."
                # Do not shift parameters: Current Permissions Value is empty
                result_value="${FALSE}"
            elif [[ "${current_permissions:0:2}" == "${SPACER_FLAGS}" ]]; then
                debug_log "Warning: Received Spacer Flags as Permissions Value."
                # Do not shift parameters: Current Permissions Value is a spacer flag
                result_value="${FALSE}"
            elif [[ "${current_permissions}" == "${FALSE}" ]]; then
                debug_log "Warning: Received False Permissions Value."
                shift  # shift to consume the permissions boolean false value
            elif [[ "${current_permissions}" == "${TRUE}" ]]; then
                debug_log "Warning: Received Boolean True as Permissions Value, but without a valid permissions flag."
                result_value="${FALSE}"
                shift  # shift to consume the permissions boolean true value
            else
                debug_log "Warning: Received a non-edgecase but Invalid Permissions Value: \"${current_permissions}\"."
                shift  # shift to consume the invalid permissions value
                result_value="${FALSE}"
            fi
            CLAUDE_PERMISSIONS_VALUE=()
        fi
    fi
    debug_log "Result Value: \"${result_value}\""
    debug_log "Permissions Value: \"${CLAUDE_PERMISSIONS_VALUE[*]}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################
# Add worktree flag
function parse_add_worktree_flags() {
    debug_log "Parsing add worktree flags"
    local worktree_flag="${1:-""}"
    debug_log "Worktree Flag: \"${worktree_flag}\""
    local worktree_value="${2:-""}"
    debug_log "Worktree Value: \"${worktree_value}\""
    local result_value="${TRUE}"

    if [[ "${worktree_flag}" == "" ]]; then
        debug_log "Error: Received Empty Worktree Flag. Exiting..."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_WORKTREE_VALUE=()
    elif [[ "${worktree_value}" == "${FALSE}" ]]; then
        debug_log "Warning: Received False Worktree Value."
        shift 2 # shift to consume the worktree flag and worktree boolean false value
        CLAUDE_WORKTREE_VALUE=()
    elif [[ ( "${worktree_value}" == "${TRUE}" ) || ( "${worktree_value}" == "" ) ]]; then
        debug_log "Warning: Received Worktree Flag with empty or true boolean value instead of a valid Worktree Name."
        shift  # shift to consume the worktree flag
        if [[ "${worktree_value}" == "${TRUE}" ]]; then
            shift  # shift to consume the worktree boolean true value
        fi
        CLAUDE_WORKTREE_VALUE=("${CLAUDE_WORKTREE_FLAGS}")
    elif validate_worktree "${worktree_value}"; then
        debug_log "Selected Worktree Name validated: \"${worktree_value}\""
        CLAUDE_WORKTREE_VALUE=("${CLAUDE_WORKTREE_FLAGS}" "${worktree_value}") && shift 2  # shift to consume the worktree flag and worktree name
    else
        debug_log "Warning: Received an Invalid but Non-Edgecase Worktree Name: \"${worktree_value}\"."
        CLAUDE_WORKTREE_VALUE=() && shift 2  # shift to consume the worktree flag and worktree boolean false value
        result_value="${FALSE}"
    fi
    debug_log "Result Value: \"${result_value}\""
    debug_log "Worktree Value: \"${CLAUDE_WORKTREE_VALUE[*]}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Add Remote Control flag
function parse_add_remote_control_flags() {
    debug_log "Parsing add remote control flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Remote Control Flag."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${REMOTE_CONTROL_FLAGS}"; then
        debug_log "Received Remote Control Flag: \"${current_flag}\""
        shift  # shift to consume the remote control flag
    else
        debug_log "Error: Received an Invalid Remote Control Flag: \"${current_flag}\"."
        result_value="${FALSE}" && shift  # shift to consume the invalid remote control flag
    fi
    debug_log "Result Value: \"${result_value}\""

    if [[ "${result_value}" == "${TRUE}" ]]; then
        debug_log "Remote Control parameter Flag Value: \"${current_flag}\""
        CLAUDE_REMOTE_CONTROL_VALUE=("${CLAUDE_REMOTE_CONTROL_FLAGS}")
    else
        debug_log "Warning: Received an Invalid Remote Control Flag: \"${current_flag}\". Setting Remote Control parameter Flag Value to empty array."
        CLAUDE_REMOTE_CONTROL_VALUE=()
    fi
    debug_log "Remote Control Value: \"${CLAUDE_REMOTE_CONTROL_VALUE[*]}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Add headless flag
function parse_add_headless_flags() {
    debug_log "Parsing add headless flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Headless Flag. Exiting..."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${HEADLESS_FLAGS}"; then
        debug_log "Received Headless Flag: \"${current_flag}\""
        shift  # shift to consume the headless flag
    else
        debug_log "Error: Received an Invalid Headless Flag: \"${current_flag}\"."
        result_value="${FALSE}" && shift  # shift to consume the invalid headless flag
    fi
    debug_log "Headless Value: \"${current_flag}\""
    if [[ "${result_value}" == "${TRUE}" ]]; then
        debug_log "Headless parameter Flag Value: \"${current_flag}\""
        CLAUDE_HEADLESS_VALUE=("${CLAUDE_HEADLESS_FLAGS}")
    else
        debug_log "Warning: Received an Invalid Headless Flag: \"${current_flag}\". Setting Headless parameter Flag Value to empty array."
        CLAUDE_HEADLESS_VALUE=()
    fi
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Add fork session flag
function parse_add_fork_session_flags() {
    debug_log "Parsing add fork session flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Fork Session Flag."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${FORK_SESSION_FLAGS}"; then
        debug_log "Received Fork Session Flag: \"${current_flag}\""
        shift  # shift to consume the fork session flag
    else
        debug_log "Error: Received an Invalid Fork Session Flag: \"${current_flag}\"."
        result_value="${FALSE}" && shift  # shift to consume the invalid fork session flag
    fi
    debug_log "Result Value: \"${result_value}\""
    if [[ "${result_value}" == "${TRUE}" ]]; then
        debug_log "Fork Session parameter Flag Value: \"${current_flag}\""
        CLAUDE_FORK_SESSION_VALUE=("${CLAUDE_FORK_SESSION_FLAGS}")
    else
        debug_log "Warning: Received an Invalid Fork Session Flag: \"${current_flag}\". Setting Fork Session parameter Flag Value to empty array."
        CLAUDE_FORK_SESSION_VALUE=()
    fi
    debug_log "Fork Session Value: \"${CLAUDE_FORK_SESSION_VALUE[*]}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################################################################################
# Skip input param Spacer flag
function parse_spacer_flags() {
    debug_log "Received Spacer Flag"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Spacer Flag."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${SPACER_FLAGS}"; then
        debug_log "Received Spacer Flag: \"${current_flag}\""
        shift  # shift to consume the spacer flag
    else
        debug_log "Error: Received an Invalid Spacer Flag: \"${current_flag}\"."
        result_value="${FALSE}" && shift  # shift to consume the invalid spacer flag
    fi
    debug_log "Result Value: \"${result_value}\""
    # Note: This flag is not being added to the updated Claude Code params because it is not a revelvant flag for claude code

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################
# Parse Command Line Provided Prompt
# NOTE: the "--prompt" flag is not added to updated Claude Code params because it's not a valid flag for claude code
function parse_prompt_value_flags() {
    debug_log "Parsing prompt value flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_prompt="${2:-""}"
    debug_log "Current Prompt: \"${current_prompt}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Prompt Value Flag."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_PROMPT_VALUE=()
    elif matches_pattern "${current_flag}" "${PROMPT_FLAGS}"; then
        debug_log "Received Prompt Value Flag: \"${current_flag}\""
        shift  # shift to consume the prompt value flag

        if [[ "${current_prompt}" == "${FALSE}" ]]; then
            debug_log "Warning: Received False Prompt Value."
            result_value="${UNSAFE_TARGET}"
            CLAUDE_PROMPT_VALUE=() && shift  # shift to consume the prompt boolean false value
        elif [[ ( "${current_prompt}" == "${TRUE}" ) || ( "${current_prompt}" == "" ) || ( "${current_prompt:0:2}" == "${SPACER_FLAGS}" ) ]]; then
            debug_log "Warning: Received an Edge Case Prompt Value: \"${current_prompt}\"."
            if [[ "${current_prompt}" == "${TRUE}" ]]; then
                shift  # shift to consume the prompt boolean true value
            fi
            debug_log "Warning: Received an Edge Case Prompt Value: \"${current_prompt}\"."
            debug_log "Setting Default Prompt Value: \"${PROMPT_VALUE_DEFAULT}\""
            # CLAUDE_PROMPT_VALUE=("${CLAUDE_PROMPT_FLAGS}" "${PROMPT_VALUE_DEFAULT}")
            CLAUDE_PROMPT_VALUE=("${PROMPT_VALUE_DEFAULT}")
        else
            debug_log "Received an apparent valid Prompt Value: \"${current_prompt}\"."
            debug_log "Setting Prompt Value: \"${current_prompt}\""
            # CLAUDE_PROMPT_VALUE=("${CLAUDE_PROMPT_FLAGS}" "${current_prompt}") && shift  # shift to consume the prompt value
            CLAUDE_PROMPT_VALUE=("${current_prompt}") && shift  # shift to consume the prompt value
        fi
    else
        debug_log "Error: Received an Invalid Prompt Flag: \"${current_flag}\"."
        result_value="${FALSE}"
        CLAUDE_PROMPT_VALUE=() && shift  # shift to consume the invalid prompt flag
    fi
    debug_log "Prompt Value: \"${CLAUDE_PROMPT_VALUE[*]}\""
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################
# Parse Prompt File Path Flag
# TODO: cat the output of the prompt file into the prompt value
function parse_prompt_path_flags() {
    debug_log "Parsing prompt path flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_path="${2:-""}"
    debug_log "Current Path: \"${current_path}\""
    local current_file_name=""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Prompt Path Flag."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_PROMPT_PATH_VALUE=()
    elif matches_pattern "${current_flag}" "${PROMPT_FLAGS}"; then
        debug_log "Received Prompt Value Flag: \"${current_flag}\""
        shift  # shift to consume the prompt value flag

        if [[ "${current_prompt}" == "${FALSE}" ]]; then
            debug_log "Warning: Received False Prompt Path."
            result_value="${UNSAFE_TARGET}"
            CLAUDE_PROMPT_PATH_VALUE=() && shift  # shift to consume the prompt path boolean false value
        elif [[ ( "${current_path}" == "${TRUE}" ) || ( "${current_path}" == "" ) || ( "${current_path:0:2}" == "${SPACER_FLAGS}" ) ]]; then
            debug_log "Warning: Received an Edge Case Prompt Path: \"${current_path}\"."
            if [[ "${current_path}" == "${TRUE}" ]]; then
                shift  # shift to consume the prompt path boolean true value
            fi
            debug_log "Warning: Received an Edge Case Prompt Path: \"${current_path}\"."
            debug_log "Setting Default Prompt Path: \"${PROMPT_PATH_DEFAULT}\""
            CLAUDE_PROMPT_PATH_VALUE=("${CLAUDE_PROMPT_PATH_FLAGS}" "${PROMPT_PATH_DEFAULT}") && shift  # shift to consume the prompt flag and prompt path value
        elif is_valid_file "${current_path}"; then
            debug_log "Received an apparent valid Prompt Path: \"${current_path}\"."
            debug_log "Setting Prompt Path: \"${current_path}\""
            CLAUDE_PROMPT_PATH_VALUE=("${CLAUDE_PROMPT_PATH_FLAGS}" "${current_path}") && shift  # shift to consume the prompt flag and prompt path value
        elif is_valid_dir "${current_path}"; then
            debug_log "Received a valid Prompt directory Path: \"${current_path}\"."
            current_file_name="${PROMPT_FILE_NAME_DEFAULT}"
            debug_log "Using default prompt file name: \"${current_file_name}\""
            current_prompt_path="${current_path}/${current_file_name}"
            debug_log "Current Prompt Path: \"${current_prompt_path}\""
            if is_valid_file "${current_prompt_path}"; then
                debug_log "Found default prompt file name: \"${current_file_name}\" in the provided prompt directory: \"${current_path}\"."
                debug_log "Setting Prompt Path: \"${current_prompt_path}\""
                CLAUDE_PROMPT_PATH_VALUE=("${CLAUDE_PROMPT_PATH_FLAGS}" "${current_prompt_path}") && shift  # shift to consume the prompt flag and prompt path value
            else
                debug_log "Warning: Unable to find default prompt file name: \"${current_file_name}\" in the provided prompt directory: \"${current_path}\"."
                result_value="${FALSE}"
                CLAUDE_PROMPT_PATH_VALUE=("${CLAUDE_PROMPT_PATH_FLAGS}" "${PROMPT_PATH_DEFAULT}") && shift  # shift to consume the invalid prompt path value
            fi
        else
            debug_log "Warning: Received an Invalid Prompt Path: \"${current_path}\"."
            result_value="${FALSE}"
            debug_log "Setting Default Prompt Path: \"${PROMPT_PATH_DEFAULT}\""
            CLAUDE_PROMPT_PATH_VALUE=("${CLAUDE_PROMPT_PATH_FLAGS}" "${PROMPT_PATH_DEFAULT}") && shift  # shift to consume the invalid prompt path value
        fi
    else
        debug_log "Error: Received an Invalid Prompt Flag: \"${current_flag}\"."
        result_value="${FALSE}"
        CLAUDE_PROMPT_PATH_VALUE=() && shift  # shift to consume the invalid prompt path flag
    fi
    debug_log "Prompt Path: \"${CLAUDE_PROMPT_PATH_VALUE[*]}\""
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}

########################################################################################################################################################################
# Parse prompt file flag
# TODO: cat the output of the prompt file into the prompt value
function parse_prompt_file_flags() {
    debug_log "Parsing prompt file flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local current_file="${2:-""}"
    debug_log "Current File: \"${current_file}\""
    local current_file_name=""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Prompt File Flag."
        result_value="${UNSAFE_TARGET}"
        CLAUDE_PROMPT_FILE_VALUE=()
    elif matches_pattern "${current_flag}" "${PROMPT_FLAGS}"; then
        debug_log "Received Prompt Value Flag: \"${current_flag}\""
        shift  # shift to consume the prompt value flag

        if [[ "${current_prompt}" == "${FALSE}" ]]; then
            debug_log "Warning: Received False Prompt File."
            result_value="${UNSAFE_TARGET}"
            CLAUDE_PROMPT_FILE_VALUE=() && shift  # shift to consume the prompt file boolean false value
        elif [[ ( "${current_file}" == "${TRUE}" ) || ( "${current_file}" == "" ) || ( "${current_file:0:2}" == "${SPACER_FLAGS}" ) ]]; then
            debug_log "Warning: Received an Edge Case Prompt File: \"${current_file}\"."
            if [[ "${current_file}" == "${TRUE}" ]]; then
                shift  # shift to consume the prompt file boolean true value
            fi
            debug_log "Warning: Received an Edge Case Prompt File: \"${current_file}\"."
            debug_log "Setting Default Prompt File: \"${PROMPT_FILE_DEFAULT}\""
            CLAUDE_PROMPT_FILE_VALUE=("${CLAUDE_PROMPT_FILE_FLAGS}" "${PROMPT_FILE_DEFAULT}") && shift  # shift to consume the prompt flag and prompt file value
        elif is_valid_file "${current_file}"; then
            debug_log "Received an apparent valid Prompt File: \"${current_file}\"."
            debug_log "Setting Prompt File: \"${current_file}\""
            CLAUDE_PROMPT_FILE_VALUE=("${CLAUDE_PROMPT_FILE_FLAGS}" "${current_file}") && shift  # shift to consume the prompt flag and prompt file value
        elif is_valid_dir "${current_file}"; then
            debug_log "Received a valid Prompt directory File: \"${current_file}\"."
            current_file_name="${PROMPT_FILE_NAME_DEFAULT}"
            debug_log "Using default prompt file name: \"${current_file_name}\""
            current_prompt_file="${current_file}/${current_file_name}"
            debug_log "Current Prompt File: \"${current_prompt_file}\""
            if is_valid_file "${current_prompt_file}"; then
                debug_log "Found default prompt file name: \"${current_file_name}\" in the provided prompt directory: \"${current_file}\"."
                debug_log "Setting Prompt File: \"${current_prompt_file}\""
                CLAUDE_PROMPT_FILE_VALUE=("${CLAUDE_PROMPT_FILE_FLAGS}" "${current_prompt_file}") && shift  # shift to consume the prompt flag and prompt file value
            else
                debug_log "Warning: Unable to find default prompt file name: \"${current_file_name}\" in the provided prompt directory: \"${current_file}\"."
                result_value="${FALSE}"
                CLAUDE_PROMPT_FILE_VALUE=("${CLAUDE_PROMPT_FILE_FLAGS}" "${PROMPT_FILE_DEFAULT}") && shift  # shift to consume the invalid prompt file value
            fi
        else
            debug_log "Warning: Received an Invalid Prompt File: \"${current_file}\"."
            result_value="${FALSE}"
            debug_log "Setting Default Prompt File: \"${PROMPT_FILE_DEFAULT}\""
            CLAUDE_PROMPT_FILE_VALUE=("${CLAUDE_PROMPT_FILE_FLAGS}" "${PROMPT_FILE_DEFAULT}") && shift  # shift to consume the invalid prompt file value
        fi
    else
        debug_log "Error: Received an Invalid Prompt Flag: \"${current_flag}\"."
        result_value="${FALSE}"
        CLAUDE_PROMPT_FILE_VALUE=() && shift  # shift to consume the invalid prompt file flag
    fi
    debug_log "Prompt File: \"${CLAUDE_PROMPT_FILE_VALUE[*]}\""
    debug_log "Result Value: \"${result_value}\""

    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    return "${result_value}"
}


########################################################################################################################################################################
# Parse active Claude Code version flags
function parse_model_version_flags() {
    debug_log "Parsing Model version flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    debug_log "Searching for claude command in PATH"
    local version_bin=""
    version_bin="$(type -P claude 2>/dev/null || true)"
    debug_log "Version Bin: \"${version_bin}\""
    local result_value="${TRUE}"
    local current_version="0"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Model Version Flag. Exiting..."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${CLAUDE_VERSION_FLAGS}"; then
        debug_log "Received Model Version Flag: \"${current_flag}\""
        shift
        if [[ ( "${version_bin}" == "" ) || ( ! -x "${version_bin}" ) ]]; then
            debug_log "Error: claude command not found in PATH"
            result_value="${FALSE}"
        elif [[ -x "${version_bin}" ]]; then
            current_version="$("${version_bin}" ${CLAUDE_VERSION_FLAGS})"
            debug_log "Current Version: \"${current_version}\""
            if [[ "${current_version}" == "" ]]; then
                debug_log "Error: Unable to retrieve Model Version. Exiting..."
                result_value="${FALSE}"
            else
                debug_log "Model Version: \"${version_bin} ${CLAUDE_VERSION_FLAGS}\": \"${current_version}\""
                echo -ne "\n${version_bin} ${current_version}\n\n"
            fi
        else
            debug_log "Error: claude command found in PATH but is not executable"
            result_value="${FALSE}"
        fi
    else
        debug_log "Warning: Received a non-empty but Invalid Model Version Flag: \"${current_flag}\"."
        shift  # shift to consume the invalid model version flag
        result_value="${FALSE}"
    fi
    debug_log "Result Value: \"${result_value}\""

    # Update current params array
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    set -e
    exit "${result_value}"
}

########################################################################################################################################################################
# Parse this script's version flags
function parse_script_version_flags() {
    debug_log "Parsing Script version flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local version_value="${SCRIPT_VERSION}"
    debug_log "Script Version: \"${version_value}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Script Version Flag."
        result_value="${UNSAFE_TARGET}"
    elif [[ "${version_value}" == "" ]]; then
        debug_log "Error: Unable to retrieve Script Version."
        shift  # shift to consume the script version flag
        result_value="${FALSE}"
    elif matches_pattern "${current_flag}" "${SCRIPT_VERSION_FLAGS}"; then
        debug_log "Received Script Version Flag: \"${current_flag}\""
        shift  # shift to consume the script version flag
    else
        debug_log "Error: Received an Invalid Script Version Flag: \"${current_flag}\"."
        shift  # shift to consume the invalid script version flag
        result_value="${FALSE}"
    fi
    debug_log "Result Value: \"${result_value}\""
    if [[ "${result_value}" == "${TRUE}" ]]; then
        debug_log "Displaying Script Version"
        echo -ne "\n${SCRIPT_NAME} ${version_value}\n\n"
        debug_log "${SCRIPT_NAME} ${version_value}"
    fi
    debug_log "Result Value: \"${result_value}\""

    # Update current params array
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    set -e
    exit "${result_value}"
}

########################################################################################################################################################################################################################################
# Print script usage and exit with fail
function parse_usage_flags() {
    debug_log "Received Usage Flag"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Usage Flag."
        result_value="${UNSAFE_TARGET}"
    elif matches_pattern "${current_flag}" "${USAGE_FLAGS}"; then
        debug_log "Received Usage Flag: \"${current_flag}\""
        shift
    else
        debug_log "Error: Received an Invalid Usage Flag: \"${current_flag}\"."
        result_value="${FALSE}"
        shift
    fi
    debug_log "Result Value: \"${result_value}\""

    # Doing this here to ensure that the current params are updated in case the usage function fails and the function returns a non-zero value
    # Update current params array
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    usage "${result_value}" || return "${result_value}"
}

########################################################################################################################################################################################################################################
# Print script usage (help) and exit with success
function parse_help_flags() {
    debug_log "Parsing help flags"
    local current_flag="${1:-""}"
    debug_log "Current Flag: \"${current_flag}\""
    local result_value="${TRUE}"

    # Validate current flag
    if [[ "${current_flag}" == "" ]]; then
        debug_log "Error: Received Empty Help Flag."
        result_value="${UNSAFE_TARGET}"
    # Verify that the current flag is the help flag
    elif matches_pattern "${current_flag}" "${HELP_FLAGS}"; then
        debug_log "Received Help Flag: \"${current_flag}\""
        shift
    # If the current flag is not the help flag, return an error
    else
        debug_log "Error: Received an Invalid Help Flag: \"${current_flag}\"."
        result_value="${FALSE}"
        shift
    fi
    debug_log "Result Value: \"${result_value}\""

    # Doing this here to ensure that the current params are updated in case the usage function fails and the function returns a non-zero value
    debug_log "Updating Current Params"
    CURRENT_PARAMS=("${@}")
    debug_log "Current Params: size: ${#CURRENT_PARAMS[*]}, values: [${CURRENT_PARAMS[*]}]"
    UPDATED_PARAMS=("${CURRENT_PARAMS[@]}")
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: [${UPDATED_PARAMS[*]}]"

    usage "${result_value}" || return "${result_value}"
}


########################################################################################################################################################################################################################################
# Define general purpose functions
########################################################################################################################################################################################################################################

########################################################################################################################################################################################################################################
# get_pattern_index(): Get the index into the valid patterns array of the pattern that matches the current element
# TODO: Verify this function works properly with debug log statements.
function get_pattern_index() {
    debug_log "Parsing Pattern Index"
    local current_element="$1"
    debug_log "Current Element: \"${current_element}\""
    local pattern_index=-1
    local result_value="${TRUE}"
    debug_log "Valid Patterns: size: ${#VALID_PATTERNS[@]}, values: [${VALID_PATTERNS[*]}]"

    debug_log "Getting Pattern Index for Current Element: \"${current_element}\""
    for i in "${!VALID_PATTERNS[@]}"; do
        if matches_pattern "${current_element}" "${VALID_PATTERNS[$i]}"; then
            pattern_index=$i
            break
        fi
    done
    debug_log "Pattern Index: \"${pattern_index}\""
    echo "${pattern_index}"
    return "${result_value}"
}


########################################################################################################################################################################################################################################
# usage(): Display usage statement and exit
#     TODO: this needs to be updated to add the new flags and their descriptions
function usage() {
    INPUT_PARAM="$1"
    # SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
    EXIT_AFTER="${EXIT_AFTER_USAGE_DEFAULT}"
    if [[ ( "${INPUT_PARAM}" == "${TRUE}") || ( "${INPUT_PARAM}" == "${FALSE}" ) ]]; then
        EXIT_AFTER="${INPUT_PARAM}"
    fi
    echo -ne "usage: ${SCRIPT_NAME}\n"
    echo -ne "\t ${USAGE_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the display of this Usage statement.\n"
    echo -ne "\t ${HELP_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the Display of this Help statement.\n"
    echo -ne "\t ${VERSION_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the version of the Claude Code model to be displayed.\n"
    echo -ne "\t ${FILE_FLAGS}:\n"
    echo -ne "\t\tFlags to allow a filename to be specified for this script.\n"
    echo -ne "\t\tNOTE: Prompt string can be provided either as a string of text or as a file name or pathname to a file containing the prompt string.\n"
    echo -ne "\t ${PATH_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a path to be specified.  Path can be an absolute or relative path to a file, or path can be combined with a received filename.\n"
    echo -ne "\t\tNOTE: Prompt string can be provided either as a string of text or as a file name or pathname to a file containing the prompt string.\n"
    echo -ne "\t ${EFFORT_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the effort used by the Claude Code model to be specified.\n"
    echo -ne "\t\tNOTE: Effort value must be one of the following: ${EFFORT_LOW}, ${EFFORT_MED}, ${EFFORT_HIGH}, ${EFFORT_XHIGH}, ${EFFORT_MAX}, or ${EFFORT_AUTO}.\n"
    echo -ne "\t ${WORKTREE_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the worktree to be specified for use by the Claude Code model.\n"
    echo -ne "\t\tNOTE: Worktree value must be a valid worktree name.  If no worktree name is provided, Claude Code will assign a new worktree name.\n"
    echo -ne "\t ${RESUME_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a previously created session to be resumed for use by the Claude Code model.\n"
    echo -ne "\t\tNOTE: Session value must be a valid session id.  If no session id is provided, operation will not continue.\n"
    echo -ne "\t ${FORK_SESSION_FLAGS}:\n"
    echo -ne "\t\tFlags that fork the resumed session into a new session id (use together with --resume; the original session is left untouched).\n"
    echo -ne "\t ${PROMPT_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a prompt string to be specified for use by the Claude Code model.\n"
    echo -ne "\t\tNOTE: Prompt string can be provided either as a string of text or as a file name or pathname to a file containing the prompt string.\n"
    echo -ne "\t ${MODEL_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the specific anthropic model, used by Claude Code, to be specified.\n"
    echo -ne "\t ${SESSION_ID_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the session id to be specified for use by the Claude Code model.\n"
    echo -ne "\t\tNOTE: Session ID value must be a valid session id (i.e., a UUID); if no session id is provided, this script will generate and assign a new UUID as the session id.\n"
    echo -ne "\t ${HEADLESS_FLAGS}:\n"
    echo -ne "\t\tFlags that allow Claude Code's operating mode to be specified--either headless if headless flag is provided or interactive if headless flag is omitted.\n"
    echo -ne "\t ${REMOTE_CONTROL_FLAGS}:\n"
    echo -ne "\t\tFlags that allow Claude Code's remote control to be specified--either remote if remote control flag is provided or local if remote control flag is omitted.\n"
    echo -ne "\t\tNOTE: Remote control value must be a valid remote control name.  If no remote control name is provided, Claude Code will assign a new remote control name.\n"
    echo -ne "\t ${PERMISSIONS_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the level of supervision applied to Claude Code's actions to be specified.\n"
    echo -ne "\t ${SPACER_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a spacer to be specified.  Spacer is used to separate flags and values in the input parameters.\n"

    [[ ( "${EXIT_AFTER}" == "${TRUE}" ) || ( "${EXIT_AFTER}" == "${FALSE}" ) ]] && exit "${EXIT_AFTER}" || exit "${FALSE}"
}


########################################################################################################################################################################
# Begin Main Script Execution
#
# Example:
#   ./scripts/wake_the_claude.bash --id 0 --worktree 0 --model opus --effort max --file prompts/thread-handoff_automated-prompts/HANDOFF_2026-06-21_precommit-testing-audit-remediation.md -- --dangerously-skip-permissions --remote-control
#
# Notes:
#   input parameters cannot include both --prompt and --file
#   input parameters cannot include both --prompt and --path
#   if input parameters include both --file and --path, the --path value and --file value are assumed to be the full path to the file
#
########################################################################################################################################################################

########################################################################################################################################################################
# Parse input parameters
########################################################################################################################################################################
debug_log "Verify that input parameters have been provided"
if [[ "${*}" != "" ]]; then
    debug_log "Input Params: [${#} args]"
    # echo "Input Params: \"${*}\""
else
    debug_log "No input params provided."
    usage "${FALSE}"
fi
debug_log "Completed verifying that input parameters have been provided"


debug_log "Parse input parameters"
while (( ${#*} > 0 )); do

    # Parse current input param flag and break when all params complete
    CURRENT_ELEMENT="${1}" && shift
    debug_log "Current Flag: \"${CURRENT_ELEMENT}\""
    debug_log "Remaining Params: size: ${#*}, values: [${*}]"

    # Validate Input Param Flag
    debug_log "Validating Input Param Flag: \"${CURRENT_ELEMENT}\""
    if [[ "${CURRENT_ELEMENT}" == "" ]]; then
        debug_log "Completed parsing input params"
        break || return "${FALSE}"
    fi
    debug_log "Validated Input Param Flag: \"${CURRENT_ELEMENT}\""

    # Save current state of input parameters
    debug_log "Saving current state of input parameters"
    UPDATED_PARAMS=("${@}")
    debug_log "Remaining Params: size: ${#*}, values: [${*}]"
    # debug_log "Updated Params: size: ${#UPDATED_PARAMS[@]}, values: $(redact_uuid "${UPDATED_PARAMS[@]}")"
    debug_log "Updated Params: size: ${#UPDATED_PARAMS[*]}, values: [${UPDATED_PARAMS[*]}]"

    # Add Resume previous session flag
    debug_log "Parsing Input Param Flag: \"${CURRENT_ELEMENT}\""
    PATTERN_INDEX="$(get_pattern_index "${CURRENT_ELEMENT}")"
    debug_log "Pattern Index: ${PATTERN_INDEX}"

    case "${PATTERN_INDEX}" in
        "${EFFORT_FLAGS_INDEX}")         parse_add_effort_flags         "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${FILE_FLAGS_INDEX}")           parse_prompt_file_flags        "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${FORK_SESSION_FLAGS_INDEX}")   parse_add_fork_session_flags   "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${HEADLESS_FLAGS_INDEX}")       parse_add_headless_flags       "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${HELP_FLAGS_INDEX}")           parse_help_flags               "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${MODEL_FLAGS_INDEX}")          parse_add_model_flags          "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${MODEL_VERSION_FLAGS_INDEX}")  parse_model_version_flags      "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${PERMISSIONS_FLAGS_INDEX}")    parse_add_permissions_flags    "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${PROMPT_FLAGS_INDEX}")         parse_prompt_value_flags       "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[*]}" ;;
        "${PATH_FLAGS_INDEX}")           parse_prompt_path_flags        "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${REMOTE_CONTROL_FLAGS_INDEX}") parse_add_remote_control_flags "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${RESUME_FLAGS_INDEX}")         parse_resume_flags             "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${SCRIPT_VERSION_FLAGS_INDEX}") parse_script_version_flags     "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${SESSION_ID_FLAGS_INDEX}")     parse_session_id_flags         "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${SPACER_FLAGS_INDEX}")         parse_spacer_flags             "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${USAGE_FLAGS_INDEX}")          parse_usage_flags              "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        "${WORKTREE_FLAGS_INDEX}")       parse_add_worktree_flags       "${CURRENT_ELEMENT}" "${UPDATED_PARAMS[@]}" ;;
        *)
            debug_log "Error: Invalid pattern index: ${PATTERN_INDEX}"
            usage "${FALSE}"
        ;;
    esac

    # Restore Updated Input Parameter for Script
    debug_log "Completed Parsing: \"${CURRENT_ELEMENT}\""
    debug_log "Setting Updated Params"
    set -- "${UPDATED_PARAMS[@]}"
    debug_log "Remaining Params: size: ${#*}, values: [${*}]" || return "${FALSE}"
done

CLAUDE_CODE_PARAMS+=("${CLAUDE_MODEL_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_EFFORT_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_WORKTREE_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_REMOTE_CONTROL_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_HEADLESS_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_FORK_SESSION_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_PERMISSIONS_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_PROMPT_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_PROMPT_FILE_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_PROMPT_PATH_VALUE[@]}")

debug_log "Completed Appending Claude Code Params: ${#CLAUDE_CODE_PARAMS[@]}"
debug_log "Claude Code Params: ${CLAUDE_CODE_PARAMS[*]}"
debug_log "Completed Parsing input parameters"


########################################################################################################################################################################
# Build Claude Code Prompt
########################################################################################################################################################################
debug_log "Build Claude Code Prompt"

if [[ ( "${PROMPT_VALUE}" != "" ) && ( "${VALID_PROMPT_PARAM}" == "${TRUE}" ) ]]; then
    CLAUDE_CODE_PROMPT="${PROMPT_VALUE}"
elif [[ ( "${PROMPT_FILE}" != "" ) && ( ( "${VALID_FILE_PARAM}" == "${TRUE}" ) || ( "${VALID_PATH_PARAM}" == "${TRUE}" ) ) ]]; then
    CLAUDE_CODE_PROMPT="$(cat "${PROMPT_FILE}")"
fi

if [[ "${CLAUDE_CODE_PROMPT}" != "" ]]; then
    CLAUDE_CODE_PARAMS+=("${CLAUDE_CODE_PROMPT}")
    debug_log "Prompt loaded [${#CLAUDE_CODE_PROMPT} chars]"
fi
debug_log "Completed building prompt, ${#CLAUDE_CODE_PARAMS[@]} total args"


########################################################################################################################################################################
# Execute Claude Code
########################################################################################################################################################################
debug_log "Executing claude with ${#CLAUDE_CODE_PARAMS[@]} args"

CLAUDE_BIN="$(type -P claude 2>/dev/null || true)"
if [[ "${CLAUDE_BIN}" == "" ]] || [[ ! -x "${CLAUDE_BIN}" ]]; then
    debug_log "Error: claude command not found in PATH"
    exit 1
fi

if [[ "${CLAUDE_HEADLESS_VALUE[*]}" != "" ]]; then
    NOHUP_LOG_FILE=""
    NOHUP_LOG_CANDIDATE="${LOGS_DIR}/wake_the_claude.nohup.log"
    if touch "${NOHUP_LOG_CANDIDATE}" 2>/dev/null; then
        NOHUP_LOG_FILE="${NOHUP_LOG_CANDIDATE}"
    else
        NOHUP_LOG_CANDIDATE="${HOME}/wake_the_claude.nohup.log"
        if touch "${NOHUP_LOG_CANDIDATE}" 2>/dev/null; then
            NOHUP_LOG_FILE="${NOHUP_LOG_CANDIDATE}"
        else
            # echo "Error: Failed to open nohup log file at ${LOGS_DIR} or ${HOME}" >&2
            debug_log "Error: Failed to open nohup log file at ${LOGS_DIR} or ${HOME}"
            exit 1
        fi
    fi
    debug_log "Nohup log file: ${NOHUP_LOG_FILE}"
    echo "nohup claude ${CLAUDE_CODE_PARAMS[*]} >> ${NOHUP_LOG_FILE} 2>&1 &"
    nohup "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}" >> "${NOHUP_LOG_FILE}" 2>&1 &
    debug_log "Launched claude headless via nohup (pid $!)"
else
    debug_log "\"${CLAUDE_BIN}\" ${CLAUDE_CODE_PARAMS[*]}"
    echo "\"${CLAUDE_BIN}\" ${CLAUDE_CODE_PARAMS[*]}"
    "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}"
    CLAUDE_STATUS=$?
    if [[ "${CLAUDE_STATUS}" != "0" ]]; then
        debug_log "Error: claude exited with non-zero status ${CLAUDE_STATUS}"
        exit "${CLAUDE_STATUS}"
    fi
fi

debug_log "Completed Executing Claude Code"
exit 0


