#!/usr/bin/env bash
########################################################################################################################################################################
# Author: Paul Calnon
# Date: 2026-03-12
# Version: 1.0.0
# Status: Development
# License: MIT
# Copyright: 2026 Paul Calnon
# Repository: https://github.com/paulcalnon/juniper-ml
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
########################################################################################################################################################################
# References:
#
########################################################################################################################################################################


########################################################################################################################################################################
# Define global Variables
########################################################################################################################################################################
TRUE="0"
FALSE="1"

# DEBUG="${FALSE}"
DEBUG="${TRUE}"

WTC_DEBUG="${WTC_DEBUG:-${DEBUG}}"
EXIT_AFTER_USAGE_DEFAULT="${TRUE}"
REQUIRE_SAVED_SESSION_ID="$(( ( WTC_DEBUG + 1 ) % 2 ))"  # Only require saving session ID when not in wtc debug mode

SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SESSIONS_DIR="${WTC_SESSIONS_DIR:-${REPO_ROOT}/scripts/sessions}"
LOGS_DIR="${WTC_LOGS_DIR:-${REPO_ROOT}/logs}"

mkdir -p "${SESSIONS_DIR}" "${LOGS_DIR}"


########################################################################################################################################################################
# Early function definitions (must precede top-level calls below)
########################################################################################################################################################################

function debug_log() {
    if [[ "${WTC_DEBUG}" == "${TRUE}" ]]; then
        echo "wake_the_claude: ${*}" 1>&2
    fi
}

function redact_uuid() {
    local value="$1"
    # if [[ ${#value} -ge 12 ]]; then
    if (( ${#value} >= 12 )); then
        echo "${value:0:8}...${value: -4}"
    else
        echo "[redacted]"
    fi
}


########################################################################################################################################################################
# Define Claude Code Models' names, aliases, and add them to validation checks array
#     NOTE: This is where you would add new model names and aliases
########################################################################################################################################################################

########################################################################################################################################################################
# Define Model Full Name Constants
debug_log "Define Model Name Constants"

# NOTE: Add new Model Full Name here
MODEL_FABLE_NAME="claude-fable-5"
MODEL_OPUS_NAME="claude-opus-4-8"
MODEL_SONNET_NAME="claude-sonnet-4-6"
MODEL_HAIKU_NAME="claud-haiku-4-5"

########################################################################################################################################################
# Define Model name Alias Constants
debug_log "Define Model Name Alias Constants"

# NOTE: Add new Model Name Alias here
MODEL_FABLE_ALIAS="fable"
MODEL_OPUS_ALIAS="opus"
MODEL_SONNET_ALIAS="sonnet"
MODEL_HAIKU_ALIAS="haiku"

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
# Claude Code parameter flags
########################################################################################################################################################################
debug_log "Define Claude Code parameter flags"
CLAUDE_PERMISSIONS_FLAGS="--dangerously-skip-permissions"
CLAUDE_REMOTE_CONTROL_FLAGS="--remote-control"
CLAUDE_SESSION_ID_FLAGS="--session-id"
CLAUDE_FORK_SESSION="--fork-session"
CLAUDE_WORKTREE_FLAGS="--worktree"
CLAUDE_VERSION_FLAGS="--version"
CLAUDE_HEADLESS_FLAGS="--print"
CLAUDE_RESUME_FLAGS="--resume"
CLAUDE_EFFORT_FLAGS="--effort"
CLAUDE_MODEL_FLAGS="--model"


########################################################################################################################################################################
# Claude Code Level of Effort Values
########################################################################################################################################################################
debug_log "Define Claude Code Effort values"
EFFORT_LOW="low"
EFFORT_MED="medium"
EFFORT_HIGH="high"
EFFORT_XHIGH="xhigh"
EFFORT_MAX="max"
EFFORT_AUTO="auto"


########################################################################################################################################################################
# Input parameter flags:
########################################################################################################################################################################
debug_log "Define Input parameter flags"
SPACER_FLAGS="--"
USAGE_FLAGS="-u | --usage"
HELP_FLAGS="-h | --help | -?"
FILE_FLAGS="-f | --file | --file-name"
PATH_FLAGS="-l | --path | --file-path"
PROMPT_FLAGS="-p | --prompt | --prompt-string"
WORKTREE_FLAGS="-w | ${CLAUDE_WORKTREE_FLAGS} | --work-tree | --working-tree"
VERSION_FLAGS="-v | ${CLAUDE_VERSION_FLAGS} | --claude-version"
EFFORT_FLAGS="-e | ${CLAUDE_EFFORT_FLAGS} | --effort-type | --effort-level"
HEADLESS_FLAGS="-a | ${CLAUDE_HEADLESS_FLAGS} | --agent | --silent | --headless"
REMOTE_CONTROL_FLAGS="-c | --remote | --control | ${CLAUDE_REMOTE_CONTROL_FLAGS}"
PERMISSIONS_FLAGS="-s | --slient | --skip | --skip-permissions | ${CLAUDE_PERMISSIONS_FLAGS}"
SESSION_ID_FLAGS="-i | --id | --session | ${CLAUDE_SESSION_ID_FLAGS} | --session-name | -t | --thread | --thread-name | --thread-id"
MODEL_FLAGS="-m | ${CLAUDE_MODEL_FLAGS} | --llm-model | --ai-model | --model-type"
RESUME_FLAGS="-r | ${CLAUDE_RESUME_FLAGS} | --resume-thread | --resume-session"
FORK_SESSION_FLAGS="--fork | ${CLAUDE_FORK_SESSION} | --resume-fork | --resume-fork_session"


########################################################################################################################################################################
# Initialize Parsed Param values
########################################################################################################################################################################
debug_log "Define Parsed Param values"
PATH_NAME=""
FILE_NAME=""
PROMPT_FILE=""
PROMPT_VALUE=""

# Define Parameter Flag and Value Arrays
debug_log "Define Parameter Flag and Value Arrays"
declare -a CLAUDE_EFFORT_VALUE
declare -a CLAUDE_FORK_SESSION_VALUE
declare -a CLAUDE_HEADLESS_VALUE
declare -a CLAUDE_MODEL_VALUE
declare -a CLAUDE_PERMISSIONS_VALUE
declare -a CLAUDE_REMOTE_CONTROL_VALUE
declare -a CLAUDE_RESUME_VALUE
declare -a CLAUDE_SESSION_ID_VALUE
declare -a CLAUDE_WORKTREE_VALUE

# Param values to be passed to Claude
debug_log "Define Param values to be passed to Claude"
CLAUDE_CODE_PROMPT=""
CLAUDE_CODE_PARAMS=()

# Valid Prompt Boolean Flags
debug_log "Define Valid Prompt Boolean Flags"
VALID_FILE_PARAM="${FALSE}"
VALID_PATH_PARAM="${FALSE}"
VALID_PROMPT_PARAM="${FALSE}"


########################################################################################################################################################################
# Define functions for wake_the_claude.bash script
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

# is_valid_uuid(): Validate UUID format (32 hex digits with optional hyphens)
function is_valid_uuid() {
    # example uuid="7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"
    local uuid="$1"
    # debug_log "Validating UUID format: ${uuid}"
    debug_log "Validating UUID format: $(redact_uuid "${uuid}")"
    if [[ ${uuid//-/} =~ ^[[:xdigit:]]{32}$ ]]; then
        debug_log "UUID is valid: $(redact_uuid "${uuid}")"
        return "${TRUE}"
    else
        debug_log "UUID is invalid"
        return "${FALSE}"
    fi
}

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

# save_session_id(): Extract session ID from value string and persist to file
function save_session_id() {
    local session_id_value="$1"
    local session_id="$2"
    debug_log "Extracting Session ID and saving to file"
    debug_log "Session ID Value: ${session_id_value}"
    debug_log "Session ID: ${session_id}"
    if [[ "${session_id}" == "" ]]; then
        session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
    fi
    debug_log "Parsed Session ID: ${session_id}"
    is_valid_uuid "${session_id}"
    RESULT="$?"
    if [[ "${RESULT}" != "${TRUE}" ]]; then
        debug_log "Error: Session ID is not a valid UUID — refusing to write file"
        return "${FALSE}"
    fi
    debug_log "Validated Parsed Session ID UUID: ${session_id}"
    local safe_filename
    safe_filename="$(basename "${session_id}").txt"
    debug_log "Safe Filename: ${safe_filename}"
    local target_path="${SESSIONS_DIR}/${safe_filename}"
    debug_log "Target Path: ${target_path}"
    if [[ -L "${target_path}" ]]; then
        # echo "Error: target file is a symlink — refusing to write"
        debug_log "Error: target file is a symlink — refusing to write"
        return "${FALSE}"
    fi
    debug_log "Validated Target Path: ${target_path}"
    echo "${session_id}" > "${target_path}"
    debug_log "Saved Session ID $(redact_uuid "${session_id}") to file: ${target_path}"
    return "${TRUE}"
}

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

function remove_generated_session_id_file() {
    # shellcheck disable=SC2317
    local session_id_filename="$1"
    # shellcheck disable=SC2317
    local session_id="$2"
    # shellcheck disable=SC2317
    local expected_filename="${session_id}.txt"
    # shellcheck disable=SC2317
    if [[ "${session_id_filename}" == "${expected_filename}" ]]; then
        debug_log "Removing generated session id file: \"${SESSIONS_DIR}/${session_id_filename}\""
        rm -f "${SESSIONS_DIR}/${session_id_filename}"
        debug_log "Completed removing generated session id file: \"${session_id_filename}\""
    else
        debug_log "Preserving session id file because filename is not generated by this script: \"${session_id_filename}\""
    fi
}

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

function validate_model() {
    MODEL_PARAM="${1,,}"
    VALID_MODEL="${FALSE}"
    debug_log "Validate Claude Code Model Param Value"
    for (( i=0; i<"${#MODEL_TEST_ARRAY[@]}"; )); do
        if [[ "${MODEL_PARAM}" == "${MODEL_TEST_ARRAY[${i}],,}" ]]; then
            debug_log "Model Valiated: ${MODEL_PARAM}"
            VALID_MODEL="${TRUE}"
            break
        fi
    done
    if [[ "${VALID_MODEL}" != "${TRUE}" ]]; then
        debug_log "Error: Specified Model is not Valid: ${MODEL_PARAM}"
        usage ${FALSE}
    fi
    return "${VALID_MODEL}"
}


function usage() {
    INPUT_PARAM="$1"
    SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
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
    echo -ne "\t\tFlags that allow a previously forked session to be resumed for use by the Claude Code model.\n"
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
    echo -ne "\t\tFlags that allow the level of supervision applied to Claude Code's actions to be specfied.\n"
    echo -ne "\t ${SPACER_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a spacer to be specified.  Spacer is used to separate flags and values in the input parameters.\n"

    [[ ( "${EXIT_AFTER}" == "${TRUE}" ) || ( "${EXIT_AFTER}" == "${FALSE}" ) ]] && exit "${EXIT_AFTER}" || exit "${FALSE}"
}


########################################################################################################################################################################
# Parse input parameters
########################################################################################################################################################################
debug_log "Verify that input parameters have been provided"
if [[ "${*}" != "" ]]; then
    debug_log "Input Params: [${#} args]"
    echo "Input Params: \"${*}\""
else
    debug_log "No input params provided."
    debug_log "Next time try these:"
    debug_log "${PARAMS_TEST}"
    usage "${FALSE}"
fi
debug_log "Completed verifying that input parameters have been provided"

debug_log "Parse input parameters"
while [[ "${TRUE}" != "${FALSE}" ]]; do

    # Parse current input param flag and break when all params complete
    CURRENT_ELEMENT="${1}"
    debug_log "Current Flag: \"${CURRENT_ELEMENT}\""
    shift

    # Process Input Param Flag
    if [[ "${CURRENT_ELEMENT}" == "" ]]; then
        debug_log "Completed parsing input params"
        break

    # Add Resume previous session flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${RESUME_FLAGS}"; then
        debug_log "Parsing resume flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            SESSION_ID="${1}"
            shift
            debug_log "Validating Session ID"
            SESSION_ID="$(validate_session_id "${SESSION_ID}")"
            RETURN_VALUE=$?
            if [[ ( "${RETURN_VALUE}" == "${TRUE}" ) && ( "${SESSION_ID}" != "" ) ]]; then
                debug_log "Session ID validated: $(redact_uuid "${SESSION_ID}")"
                CLAUDE_RESUME_VALUE=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")
                CLAUDE_SESSION_ID_VALUE=""
            else
                debug_log "Error: Session ID is invalid. Exiting..."
                usage "${FALSE}"
            fi
        else
            debug_log "Error: Received Resume Flag but no Valid Session ID to Resume. Exiting..."
            usage "${FALSE}"
        fi

    # Add Session ID flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${SESSION_ID_FLAGS}"; then
        debug_log "Parsing session id flags"

        # Parse and init Session ID param unless Resume Previous Session is in progress
        debug_log "Handle Session ID edge cases"
        SESSION_ID="${1}"
        # if [[ ( "${CLAUDE_RESUME_VALUE[@]}" == "" ) && ( "${SESSION_ID}" != "${FALSE}" ) ]]; then
        if [[ ( ( "${CLAUDE_RESUME_VALUE[*]}" == "" ) || ( "${#CLAUDE_RESUME_VALUE[@]}" == "0" ) ) && ( "${SESSION_ID}" != "${FALSE}" ) ]]; then
            # SESSION_ID="${1}"
            # Handle session id bool flag edge case
            if [[ "${SESSION_ID}" == "${TRUE}" ]]; then
                shift
                SESSION_ID=""
            fi

            # Validate Session ID
            debug_log "Validating Session ID"
            SESSION_ID="$(validate_session_id "${SESSION_ID}")"
            RETURN_VALUE=$?
            if [[ ( "${RETURN_VALUE}" == "${TRUE}" ) && ( "${SESSION_ID}" != "" ) ]]; then
                debug_log "Session ID validated: $(redact_uuid "${SESSION_ID}")"
                shift
            else
                debug_log "Warning: Received Session ID Flag but no Valid Session ID Name."
                debug_log "Session ID Value not Provided, Assigning a new UUID as Session ID."
                SESSION_ID="$(generate_uuid)"
                RESULT="$?"
                if [[ ( "${RESULT}" != "${TRUE}" ) || ( "${SESSION_ID}" == "" ) ]]; then
                    debug_log "Error: Failed to generate a valid UUID for Session ID."
                    usage "${FALSE}"
                fi
            fi
            CLAUDE_SESSION_ID_VALUE=("${CLAUDE_SESSION_ID_FLAGS}" "${SESSION_ID}")
            save_session_id "${CLAUDE_SESSION_ID_VALUE[@]}"
            RESULT="$?"
            if [[ ( "${RESULT}" != "${TRUE}" ) && ( "${REQUIRE_SAVED_SESSION_ID}" == "${TRUE}" ) ]]; then 
                debug_log "Error: Failed to Save Session ID value."
                usage "${FALSE}"
            elif [[ "${RESULT}" != "${TRUE}" ]]; then
                debug_log "Warning: Failed to Save Session ID value."
            fi
        else
            CLAUDE_SESSION_ID_VALUE=("")
            debug_log "Warning: Ignoring Session ID Value Param since ID Flagged as False or Resume Previous Thread has been specified."
        fi

    # Add worktree flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${WORKTREE_FLAGS}"; then
        debug_log "Parsing worktree flags"
        WORKTREE_VALUE="${1}"
        if [[ "${WORKTREE_VALUE}" == "${FALSE}" ]]; then
            CLAUDE_WORKTREE_VALUE=""
        elif [[ ( "${WORKTREE_VALUE}" == "" ) || ( "${1:0:2}" == "${SPACER_FLAGS}" ) || ( "${WORKTREE_VALUE}" == "${TRUE}" ) ]]; then
            # Handle Edgecase of worktree boolean true value
            debug_log "Warning: Received Worktree Flag but no valid Worktree Name. Letting Claude Code assign one."
            if [[ "${WORKTREE_VALUE}" == "${TRUE}" ]]; then
                shift
            fi
            CLAUDE_WORKTREE_VALUE="${CLAUDE_WORKTREE_FLAGS}"
        else
            shift
            CLAUDE_WORKTREE_VALUE=("${CLAUDE_WORKTREE_FLAGS}" "${WORKTREE_VALUE}")
        fi

    # Add Remote Control flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${REMOTE_CONTROL_FLAGS}"; then
        debug_log "Parsing remote control flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            REMOTE_CONTROL_VALUE="${1}"
            shift
            debug_log "Received Remote Control Value: \"${REMOTE_CONTROL_VALUE}\""
        else
            debug_log "Warning: Received Remote Control Flag but no Remote Control Name. Letting Claude Code assign one."
        fi
        CLAUDE_REMOTE_CONTROL_VALUE=("${CLAUDE_REMOTE_CONTROL_FLAGS}" "${REMOTE_CONTROL_VALUE}")

    # Add Effort Flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${EFFORT_FLAGS}"; then
        debug_log "Parsing effort flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) && ( ( "${1}" == "${EFFORT_LOW}" ) || ( "${1}" == "${EFFORT_MED}" ) || ( "${1}" == "${EFFORT_HIGH}" ) || ( "${1}" == "${EFFORT_XHIGH}" ) || ( "${1}" == "${EFFORT_MAX}" ) || ( "${1}" == "${EFFORT_AUTO}" ) ) ]]; then
            CLAUDE_EFFORT_VALUE=("${CLAUDE_EFFORT_FLAGS}" "${1}")
            shift
        else
            debug_log "Error: Received Effort Flag but no valid Effort Value. Exiting..."
            usage "${FALSE}"
        fi

    # Add Model Flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${MODEL_FLAGS}"; then
        debug_log "Parsing model flags"
        if [[ "${1}" != "" ]]; then
            CLAUDE_MODEL_NAME="${1}"
	    validate_model "${CLAUDE_MODEL_NAME}"
            VALID_MODEL_NAME="$?"
            if [[ "${VALID_MODEL_NAME}" != "${TRUE}" ]]; then
                debug_log "Error: Received an Ivalid Model Name. Exiting..."
                usage "${FALSE}"
            fi
            debug_log "Selected Model Name Validated"
            debug_log "Selected Claude Model: ${CLAUDE_MODEL_NAME}"
            CLAUDE_MODEL_VALUE=("${CLAUDE_MODEL_FLAGS}" "${CLAUDE_MODEL_NAME}")
            shift
        else
            debug_log "Error: Received Model Flag but no Model Name. Exiting..."
            usage "${FALSE}"
        fi

    # Add headless flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${HEADLESS_FLAGS}"; then
        debug_log "Parsing headless flags"
        CLAUDE_HEADLESS_VALUE="${CLAUDE_HEADLESS_FLAGS}"

    # Add fork session flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${FORK_SESSION_FLAGS}"; then
        debug_log "Parsing fork session flags"
        CLAUDE_FORK_SESSION_VALUE="${CLAUDE_FORK_SESSION}"

    # Add Permissions Flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${PERMISSIONS_FLAGS}"; then
        debug_log "Parsing permissions flags"
        CLAUDE_PERMISSIONS_VALUE="${CLAUDE_PERMISSIONS_FLAGS}"

    # Parse Command Line Provided Prompt
    elif matches_pattern "${CURRENT_ELEMENT}" "${PROMPT_FLAGS}"; then
        debug_log "Parsing prompt flags"
        if [[ "${1}" != "" ]]; then
            PROMPT_VALUE="${1}"
            shift
            VALID_PROMPT_PARAM="${TRUE}"
            debug_log "Received prompt [${#PROMPT_VALUE} chars]"
        else
            debug_log "Error: Did not receive a valid prompt string. Exiting..."
            usage "${FALSE}"
        fi

    # Parse prompt file flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${FILE_FLAGS}"; then
        debug_log "Parsing file flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            FILE_NAME="${1}"
            shift
        else
            debug_log "Error: Received File Flag but no File Value. Exiting..."
            usage "${FALSE}"
        fi

        if [[ -f "${FILE_NAME}" ]]; then
            VALID_FILE_PARAM="${TRUE}"
            PROMPT_FILE="${FILE_NAME}"
            debug_log "Provided Filename is a valid file"
        elif [[ ( "${PATH_NAME}" != "" ) && ( -f "${PATH_NAME}/${FILE_NAME}" ) ]]; then
            VALID_FILE_PARAM="${TRUE}"
            PROMPT_FILE="${PATH_NAME}/${FILE_NAME}"
            debug_log "Combined Pathname and Filename is a valid file"
        elif [[ ${PATH_NAME} == "" ]]; then
            debug_log "Filename not yet valid, Pathname has not yet been parsed"
            continue
        else
            debug_log "Error: received an invalid Prompt File. Exiting..."
            usage "${FALSE}"
        fi

    # Parse Prompt File Path Flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${PATH_FLAGS}"; then
        debug_log "Parsing path flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            PATH_NAME="${1}"
            shift
        else
            debug_log "Error: Received Path Flag but no Path Value. Exiting..."
            usage "${FALSE}"
        fi
        debug_log "Completed Parsing path value"
        if [[ "${PATH_NAME: -1}" == "/" ]]; then
            PATH_NAME="${PATH_NAME%\/*}"
            debug_log "Removed trailing slash from path"
        fi
        if [[ -f "${PATH_NAME}" ]]; then
            VALID_PATH_PARAM="${TRUE}"
            PROMPT_FILE="${PATH_NAME}"
            debug_log "Provided Pathname is a valid file"
        elif [[ -d "${PATH_NAME}" ]]; then
            debug_log "Provided Pathname is a valid directory"
            if [[ ( "${FILE_NAME}" != "" ) && ( -f "${PATH_NAME}/${FILE_NAME}" ) ]]; then
                VALID_PATH_PARAM="${TRUE}"
                PROMPT_FILE="${PATH_NAME}/${FILE_NAME}"
                debug_log "Combined Pathname and Filename is a valid file"
            elif [[ "${FILE_NAME}" == "" ]]; then
                debug_log "Filename has not yet been parsed"
                continue
            else
                debug_log "Error: Prompt file is invalid when Pathname is combined with Filename. Exiting..."
                usage "${FALSE}"
            fi
        else
            debug_log "Error: received an invalid Prompt File Path. Exiting..."
            usage "${FALSE}"
        fi

    # Skip input param Spacer flag
    elif matches_pattern "${CURRENT_ELEMENT}" "${SPACER_FLAGS}"; then
        debug_log "Received Spacer Flag"
        continue

    # Print claude version and exit
    elif matches_pattern "${CURRENT_ELEMENT}" "${VERSION_FLAGS}"; then
        debug_log "Parsing version flags"
        claude "${CLAUDE_VERSION_FLAGS}"
        exit "${TRUE}"

    # Print script usage and exit with fail
    elif matches_pattern "${CURRENT_ELEMENT}" "${USAGE_FLAGS}"; then
        usage "${FALSE}"

    # Print script usage (help) and exit with success
    elif matches_pattern "${CURRENT_ELEMENT}" "${HELP_FLAGS}"; then
        usage "${TRUE}"

    # Print script usage and exit with fail
    else
        debug_log "Error: Received Invalid Input Param: \"${CURRENT_ELEMENT}\""
        usage "${FALSE}"
    fi

    debug_log "Completed Parsing: \"${CURRENT_ELEMENT}\""
done

CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_WORKTREE_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_REMOTE_CONTROL_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_EFFORT_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_MODEL_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_HEADLESS_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_FORK_SESSION_VALUE[@]}")
CLAUDE_CODE_PARAMS+=("${CLAUDE_PERMISSIONS_VALUE[@]}")

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

if [[ "${CLAUDE_HEADLESS_VALUE}" != "" ]]; then
    NOHUP_LOG_FILE=""
    NOHUP_LOG_CANDIDATE="${LOGS_DIR}/wake_the_claude.nohup.log"
    if touch "${NOHUP_LOG_CANDIDATE}" 2>/dev/null; then
        NOHUP_LOG_FILE="${NOHUP_LOG_CANDIDATE}"
    else
        NOHUP_LOG_CANDIDATE="${HOME}/wake_the_claude.nohup.log"
        if touch "${NOHUP_LOG_CANDIDATE}" 2>/dev/null; then
            NOHUP_LOG_FILE="${NOHUP_LOG_CANDIDATE}"
        else
            echo "Error: Failed to open nohup log file at ${LOGS_DIR} or ${HOME}" >&2
            exit 1
        fi
    fi
    debug_log "Nohup log file: ${NOHUP_LOG_FILE}"
    echo "nohup claude ${CLAUDE_CODE_PARAMS[*]} >> ${NOHUP_LOG_FILE} 2>&1 &"
    nohup "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}" >> "${NOHUP_LOG_FILE}" 2>&1 &
else
    debug_log "\"${CLAUDE_BIN}\" ${CLAUDE_CODE_PARAMS[*]}"
    echo "\"${CLAUDE_BIN}\" ${CLAUDE_CODE_PARAMS[*]}"
    "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}"
fi
NOHUP_STATUS=$?
if [[ "${NOHUP_STATUS}" != "0" ]]; then
    debug_log "Error: Failed to launch claude with nohup"
    exit 1
fi
debug_log "Completed Executing Claude Code"
exit 0
