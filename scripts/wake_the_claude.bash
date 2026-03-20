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

SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SESSIONS_DIR="${WTC_SESSIONS_DIR:-${REPO_ROOT}/scripts/sessions}"
LOGS_DIR="${WTC_LOGS_DIR:-${REPO_ROOT}/logs}"

mkdir -p "${SESSIONS_DIR}" "${LOGS_DIR}"


########################################################################################################################################################################
# Early function definitions (must precede top-level calls below)
########################################################################################################################################################################

# TODO: this isn't going to stderr?????

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
# Claude Code parameter flags
########################################################################################################################################################################
debug_log "Define Claude Code parameter flags"

CLAUDE_PERMISSIONS_FLAGS="--dangerously-skip-permissions"
CLAUDE_SESSION_ID_FLAGS="--session-id"
CLAUDE_FORK_SESSION="--fork-session"
CLAUDE_WORKTREE_FLAGS="--worktree"
CLAUDE_VERSION_FLAGS="--version"
CLAUDE_HEADLESS_FLAGS="--print"
CLAUDE_RESUME_FLAGS="--resume"
CLAUDE_EFFORT_FLAGS="--effort"
CLAUDE_MODEL_FLAGS="--model"

debug_log "Define Claude Code Effort values"
EFFORT_LOW="low"
EFFORT_MED="medium"
EFFORT_HIGH="high"


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
PERMISSIONS_FLAGS="-s | --slient | --skip | --skip-permissions | ${CLAUDE_PERMISSIONS_FLAGS}"
SESSION_ID_FLAGS="-i | --id | --session | ${CLAUDE_SESSION_ID_FLAGS} | --session-name | -t | --thread | --thread-name | --thread-id"
MODEL_FLAGS="-m | ${CLAUDE_MODEL_FLAGS} | --llm-model | --ai-model | --model-type"
RESUME_FLAGS="-r | ${CLAUDE_RESUME_FLAGS} | --resume-thread | --resume-session"
FORK_SESSION_FLAGS="--fork | ${CLAUDE_FORK_SESSION} | --resume-fork | --resume-fork_session"


########################################################################################################################################################################
# Define Test Input parameters
########################################################################################################################################################################
debug_log "Define Test Input parameters"

# PARAMS_TEST="--prompt \"Hello Claude!\" -- --effort high --print"
PARAMS_TEST="--id --worktree --skip-permissions --path \"../../../Juniper/juniper-ml/scripts/test_prompt.md\" -- --effort high --print"
debug_log "Default Testing Input parameters: \"${PARAMS_TEST}\""


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
    debug_log "Validating UUID format"
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
    if [[ "${generated_uuid}" == "" ]]; then
        debug_log "Error: No valid UUID generated"
        return "${FALSE}"
    elif ! is_valid_uuid "${generated_uuid}"; then
        debug_log "Error: Generated UUID is not a valid UUID"
        return "${FALSE}"
    fi
    debug_log "Generated UUID: ${generated_uuid}"
    echo "${generated_uuid}"
    return "${TRUE}"
}


# save_session_id(): Extract session ID from value string and persist to file
function save_session_id() {
    local session_id_value="$1"
    debug_log "Extracting Session ID and saving to file"
    local session_id
    session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
    if ! is_valid_uuid "${session_id}"; then
        echo "Error: Session ID is not a valid UUID — refusing to write file"
        return "${FALSE}"
    fi
    local safe_filename
    safe_filename="$(basename "${session_id}").txt"
    local target_path="${SESSIONS_DIR}/${safe_filename}"
    if [[ -L "${target_path}" ]]; then
        echo "Error: target file is a symlink — refusing to write"
        return "${FALSE}"
    fi
    echo "${session_id}" > "${target_path}"
    debug_log "Saved Session ID $(redact_uuid "${session_id}") to file: ${target_path}"
    return "${TRUE}"
}


# retrieve_session_id(): Read session ID from a file in SESSIONS_DIR
function retrieve_session_id() {
    # local session_id_filename="$1"
    local session_id_file="$1"
    # debug_log "Retrieving Session ID from file: ${SESSIONS_DIR}/${session_id_filename}"
    debug_log "Retrieving Session ID from file: ${session_id_file}"
    local session_id
    # session_id="$(cat "${SESSIONS_DIR}/${session_id_filename}")"
    session_id="$(cat "${session_id_file}")"
    # debug_log "Completed retrieving Session ID from file: \"${session_id_filename}\""
    debug_log "Completed retrieving Session ID from file: \"${session_id_file}\""
    echo "${session_id}"
    return "${TRUE}"
}


function maybe_remove_generated_session_id_file() {
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
    echo -ne "\t\tNOTE: Effort value must be one of the following: ${EFFORT_LOW}, ${EFFORT_MED}, or ${EFFORT_HIGH}.\n"
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
    echo -ne "\t ${PERMISSIONS_FLAGS}:\n"
    echo -ne "\t\tFlags that allow the level of supervision applied to Claude Code's actions to be specfied.\n"
    echo -ne "\t ${SPACER_FLAGS}:\n"
    echo -ne "\t\tFlags that allow a spacer to be specified.  Spacer is used to separate flags and values in the input parameters.\n"

    set -e
    [[ ( "${EXIT_AFTER}" == "${TRUE}" ) || ( "${EXIT_AFTER}" == "${FALSE}" ) ]] && exit "${EXIT_AFTER}" || exit "${FALSE}"
}


########################################################################################################################################################################
# Valid Prompt Boolean Flags
########################################################################################################################################################################
debug_log "Define Valid Prompt Boolean Flags"

VALID_FILE_PARAM="${FALSE}"
VALID_PATH_PARAM="${FALSE}"
VALID_PROMPT_PARAM="${FALSE}"


########################################################################################################################################################################
# Parsed Param values
########################################################################################################################################################################
debug_log "Define Parsed Param values"

PATH_NAME=""
FILE_NAME=""

PROMPT_FILE=""
PROMPT_VALUE=""

# MODEL_VALUE=""
# RESUME_VALUE=""
# EFFORT_VALUE=""
WORKTREE_VALUE=""
HEADLESS_VALUE=""
SESSION_ID_VALUE=""
PERMISSIONS_VALUE=""


########################################################################################################################################################################
# Param values to be passed to Claude
########################################################################################################################################################################
debug_log "Define Param values to be passed to Claude"

CLAUDE_CODE_PROMPT=""
CLAUDE_CODE_PARAMS=()


########################################################################################################################################################################
# Parse input parameters
########################################################################################################################################################################
debug_log "Verify that input parameters have been provided"
if [[ "${*}" != "" ]]; then
    debug_log "Input Params: [${#} args]"
else
    debug_log "No input params provided."
    debug_log "Next time try these:"
    debug_log "${PARAMS_TEST}"
    usage "${FALSE}"
fi
debug_log "Completed verifying that input parameters have been provided"

debug_log "Parse input parameters"
while [[ "${TRUE}" != "${FALSE}" ]]; do

    if [[ "${1}" != "" ]]; then
        CURRENT_ELEMENT="${1}"
        shift
        debug_log "Current Flag: \"${CURRENT_ELEMENT}\""
    else
        debug_log "Completed parsing input params"
        break
    fi
    if matches_pattern "${CURRENT_ELEMENT}" "${PATH_FLAGS}"; then
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
                CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")
                debug_log "Completed parsing resume, ${#CLAUDE_CODE_PARAMS[@]} args"
            else
                debug_log "Error: Session ID is invalid. Exiting..."
                usage "${FALSE}"
            fi
        else
            debug_log "Error: Received Resume Flag but no Valid Session ID to Resume. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${SESSION_ID_FLAGS}"; then
        debug_log "Parsing session id flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            SESSION_ID_VALUE="${CLAUDE_SESSION_ID_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_FLAGS}" "${1}")
            shift
            debug_log "Received Session ID, ${#CLAUDE_CODE_PARAMS[@]} args"
        else
            debug_log "Warning: Received Session ID Flag but no Session ID Name."
            debug_log "Session ID Value not Provided, Assigning a new UUID as Session ID."
            generated_uuid="$(generate_uuid)"
            if [[ ( "$?" != "${TRUE}" ) || ( "${generated_uuid}" == "" ) ]]; then
                debug_log "Error: Failed to generate a valid UUID for Session ID."
                usage "${FALSE}"
            fi
            SESSION_ID_VALUE="${CLAUDE_SESSION_ID_FLAGS} ${generated_uuid}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_FLAGS}" "${generated_uuid}")
            debug_log "Generated new Session ID: $(redact_uuid "${generated_uuid}"), ${#CLAUDE_CODE_PARAMS[@]} args"
        fi
        if ! save_session_id "${SESSION_ID_VALUE}"; then

            debug_log "Error: Session ID value is invalid. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${WORKTREE_FLAGS}"; then
        debug_log "Parsing worktree flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            # WORKTREE_VALUE="${CLAUDE_WORKTREE_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_WORKTREE_FLAGS}" "${1}")
            shift
            debug_log "Received Worktree Value, ${#CLAUDE_CODE_PARAMS[@]} args"
        else
            debug_log "Warning: Received Worktree Flag but no Worktree Name. Letting Claude Code assign one."
            WORKTREE_VALUE="${CLAUDE_WORKTREE_FLAGS}"
            CLAUDE_CODE_PARAMS+=("${WORKTREE_VALUE}")
            debug_log "Received Worktree Flag (no value), ${#CLAUDE_CODE_PARAMS[@]} args"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${EFFORT_FLAGS}"; then
        debug_log "Parsing effort flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) && ( ( "${1}" == "${EFFORT_LOW}" ) || ( "${1}" == "${EFFORT_MED}" ) || ( "${1}" == "${EFFORT_HIGH}" ) ) ]]; then
            # EFFORT_VALUE="${CLAUDE_EFFORT_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_EFFORT_FLAGS}" "${1}")
            shift
            debug_log "Received Effort Value, ${#CLAUDE_CODE_PARAMS[@]} args"
        else
            debug_log "Error: Received Effort Flag but no valid Effort Value. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${MODEL_FLAGS}"; then
        debug_log "Parsing model flags"
        if [[ "${1}" != "" ]]; then
            # TODO: Validate Model value
            # MODEL_VALUE="${CLAUDE_MODEL_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_MODEL_FLAGS}" "${1}")
            shift
            debug_log "Received Model Value, ${#CLAUDE_CODE_PARAMS[@]} args"
        else
            debug_log "Error: Received Model Flag but no Model Name. Exiting..."
            usage "${FALSE}"
        fi
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
    elif matches_pattern "${CURRENT_ELEMENT}" "${VERSION_FLAGS}"; then
        debug_log "Parsing version flags"
        claude "${CLAUDE_VERSION_FLAGS}"
        exit "${TRUE}"
    elif matches_pattern "${CURRENT_ELEMENT}" "${HEADLESS_FLAGS}"; then
        debug_log "Parsing headless flags"
        HEADLESS_VALUE="${CLAUDE_HEADLESS_FLAGS}"
        CLAUDE_CODE_PARAMS+=("${HEADLESS_VALUE}")
        debug_log "Received Headless Flag, ${#CLAUDE_CODE_PARAMS[@]} args"
    elif matches_pattern "${CURRENT_ELEMENT}" "${FORK_SESSION_FLAGS}"; then
        debug_log "Parsing fork session flags"
        FORK_SESSION_VALUE="${FORK_SESSION_FLAGS}"
        CLAUDE_CODE_PARAMS+=("${FORK_SESSION_VALUE}")
        debug_log "Received Fork Session FLag, ${#CLAUDE_CODE_PARAMS[@]} args"
    elif matches_pattern "${CURRENT_ELEMENT}" "${PERMISSIONS_FLAGS}"; then
        debug_log "Parsing permissions flags"
        PERMISSIONS_VALUE="${CLAUDE_PERMISSIONS_FLAGS}"
        CLAUDE_CODE_PARAMS+=("${PERMISSIONS_VALUE}")
        debug_log "Received Permissions Flag, ${#CLAUDE_CODE_PARAMS[@]} args"
    elif matches_pattern "${CURRENT_ELEMENT}" "${SPACER_FLAGS}"; then
        debug_log "Received Spacer Flag"
        continue
    elif matches_pattern "${CURRENT_ELEMENT}" "${USAGE_FLAGS}"; then
        usage "${FALSE}"
    elif matches_pattern "${CURRENT_ELEMENT}" "${HELP_FLAGS}"; then
        usage "${TRUE}"
    else
        debug_log "Error: Received Invalid Input Param: \"${CURRENT_ELEMENT}\""
        usage "${FALSE}"
    fi
    debug_log "Completed Parsing: \"${CURRENT_ELEMENT}\", ${#CLAUDE_CODE_PARAMS[@]} args"
done
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

if [[ "${HEADLESS_VALUE}" != "" ]]; then
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
    "${CLAUDE_BIN}" "${CLAUDE_CODE_PARAMS[@]}"
fi
NOHUP_STATUS=$?
if [[ "${NOHUP_STATUS}" != "0" ]]; then
    debug_log "Error: Failed to launch claude with nohup"
    exit 1
fi
debug_log "Completed Executing Claude Code"
exit 0
