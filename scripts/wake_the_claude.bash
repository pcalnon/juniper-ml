#!/usr/bin/env bash
########################################################################################################################################################################
# Description:
#    this script performs the actual call to launch the claude code agent.
#    this script is not intended to be used directly.
########################################################################################################################################################################

########################################################################################################################################################################
# Define global Variables
########################################################################################################################################################################
echo "Define global Variables"

TRUE="0"
FALSE="1"
EXIT_AFTER_USAGE_DEFAULT="${TRUE}"


########################################################################################################################################################################
# Claude Code parameter flags
########################################################################################################################################################################
echo "Define Claude Code parameter flags"

CLAUDE_PERMISSIONS_FLAGS="--dangerously-skip-permissions"
CLAUDE_SESSION_ID_FLAGS="--session-id"
CLAUDE_WORKTREE_FLAGS="--worktree"
CLAUDE_VERSION_FLAGS="--version"
CLAUDE_HEADLESS_FLAGS="--print"
CLAUDE_RESUME_FLAGS="--resume"
CLAUDE_EFFORT_FLAGS="--effort"
CLAUDE_MODEL_FLAGS="--model"

echo "Define Claude Code Effort values"
EFFORT_LOW="low"
EFFORT_MED="medium"
EFFORT_HIGH="high"


########################################################################################################################################################################
# Input parameter flags:
########################################################################################################################################################################
echo "Define Input parameter flags"

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


########################################################################################################################################################################
# Define Test Input parameters
########################################################################################################################################################################
echo "Define Test Input parameters"

# PARAMS_TEST="--prompt \"Hello Claude!\" -- --effort high --print"
PARAMS_TEST="--id --worktree --skip-permissions --path \"../../../Juniper/juniper-ml/scripts/test_prompt.md\" -- --effort high --print"
echo "Default Testing Input parameters: \"${PARAMS_TEST}\""


########################################################################################################################################################################
# Define functions for wake_the_claude.bash script
########################################################################################################################################################################
echo "Define functions for wake_the_claude.bash script"

function matches_pattern() {
    # shellcheck disable=SC2034
    local ip_value="$1"
    local pattern="$2"
    eval "case \"\${ip_value}\" in ${pattern}) return 0;; *) return 1;; esac"
}

# Validate UUID
function is_valid_uuid() {
    # example uuid="7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"
    local uuid="$1"
    echo "Validating UUID format" >&2
    if [[ ${uuid//-/} =~ ^[[:xdigit:]]{32}$ ]]; then
        echo "UUID is valid" >&2
        return 0
    else
        echo "UUID is invalid" >&2
        return 1
    fi
}

# Save Session ID to file
function save_session_id() {
    local session_id_value="$1"
    echo "Extract Session ID from Session ID Value: \"${session_id_value}\" and save to file"
    local session_id
    session_id="$(echo "${session_id_value}" | awk -F " " '{print $2;}')"
    if ! is_valid_uuid "${session_id}"; then
        echo "Error: Session ID is not a valid UUID — refusing to write file" >&2
        return "${FALSE}"
    fi
    local safe_filename
    safe_filename="$(basename "${session_id}").txt"
    echo "${session_id}" > "./${safe_filename}"
    echo "Completed extracting Session ID: \"${session_id}\" from Session ID Value: \"${session_id_value}\""
}

# Retrieve Session ID from file
function retrieve_session_id() {
    local session_id_filename="$1"
    echo "Retrieve saved Session ID from file: ${session_id_filename}" >&2
    local session_id
    session_id="$(cat "./${session_id_filename}")"
    echo "Completed retrieving saved Session ID from file: \"${session_id_filename}\"" >&2
    echo "${session_id}"
}

function validate_session_id() {
    local session_id="$1"
    local session_id_filename=""
    echo "Validating Session ID: \"${session_id}\"" >&2
    if [[ "${session_id}" == "" ]]; then
        echo "Session ID is empty" >&2
        return "${FALSE}"
    elif is_valid_uuid "${session_id}"; then
        echo "Session ID is valid: \"${session_id}\"" >&2
    elif [[ "${session_id}" == */* ]]; then
        echo "Session ID filename contains path separators — rejected" >&2
        return "${FALSE}"
    elif [[ "${session_id}" != *.txt ]]; then
        echo "Session ID filename must have .txt extension — rejected" >&2
        return "${FALSE}"
    elif [[ -f "./${session_id}" ]]; then
        session_id_filename="${session_id}"
        echo "Session ID is a file: \"${session_id_filename}\"" >&2
        session_id="$(retrieve_session_id "${session_id_filename}")"
        echo "Completed retrieving Session ID from file: \"${session_id_filename}\"" >&2
        if is_valid_uuid "${session_id}"; then
            echo "Session ID is valid: \"${session_id}\"" >&2
        else
            echo "Session ID file did not contain a valid UUID" >&2
            return "${FALSE}"
        fi
    else
        echo "Session ID is invalid: \"${session_id}\"" >&2
        return "${FALSE}"
    fi
    echo "${session_id}"
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
echo "Define Valid Prompt Boolean Flags"

VALID_FILE_PARAM="${FALSE}"
VALID_PATH_PARAM="${FALSE}"
VALID_PROMPT_PARAM="${FALSE}"


########################################################################################################################################################################
# Parsed Param values
########################################################################################################################################################################
echo "Define Parsed Param values"

PATH_NAME=""
FILE_NAME=""

PROMPT_FILE=""
PROMPT_VALUE=""

MODEL_VALUE=""
RESUME_VALUE=""
EFFORT_VALUE=""
WORKTREE_VALUE=""
HEADLESS_VALUE=""
SESSION_ID_VALUE=""
PERMISSIONS_VALUE=""


########################################################################################################################################################################
# Param values to be passed to Claude
########################################################################################################################################################################
echo "Define Param values to be passed to Claude"

CLAUDE_CODE_PROMPT=""
CLAUDE_CODE_PARAMS=()


########################################################################################################################################################################
# Parse input parameters
########################################################################################################################################################################
echo "Verify that input parameters have been provided"
if [[ "${*}" != "" ]]; then
    echo "Input Params: \"${*}\""
else
    echo "No input params provided."
    echo "Next time try these:"
    echo -ne "\t${PARAMS_TEST}\n"
    usage "${FALSE}"
fi
echo "Completed verifying that input parameters have been provided"

echo "Parse input parameters"
while [[ "${TRUE}" != "${FALSE}" ]]; do

    echo "Validate input parameter: \"${1}\""
    if [[ "${1}" != "" ]]; then
        CURRENT_ELEMENT="${1}"
        shift
        echo "Current Flag: \"${CURRENT_ELEMENT}\""
    else
        echo "Completed parsing input params"
        break
    fi

    echo "Parsing input parameter: \"${CURRENT_ELEMENT}\""
    if matches_pattern "${CURRENT_ELEMENT}" "${PATH_FLAGS}"; then
        echo "Parsing path flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            echo "Parsing path value: \"${1}\""
            PATH_NAME="${1}"
            shift
        else
            echo "Error: Received Path Flag but no Path Value"
            echo "Path Value not Provided, Exiting..."
            usage "${FALSE}"
        fi
        echo "Completed Parsing path value: \"${PATH_NAME}\""
        # Remove trailing slash from path if slash is present
        echo "Check if trailing slash is present in path: \"${PATH_NAME}\""
        if [[ "${PATH_NAME: -1}" == "/" ]]; then
            echo "Removing trailing slash from path: \"${PATH_NAME}\""
            PATH_NAME="${PATH_NAME%\/*}"
            echo "Completed Removing trailing slash from path: \"${PATH_NAME}\""
        fi
        echo "Check if pathname is a valid file"
        if [[ -f "${PATH_NAME}" ]]; then
            VALID_PATH_PARAM="${TRUE}"
            PROMPT_FILE="${PATH_NAME}"
            echo "Provided Pathname is a valid file: \"${PROMPT_FILE}\""
        elif [[ -d "${PATH_NAME}" ]]; then
            echo "Provided Pathname is a valid directory: \"${PATH_NAME}\""
            if [[ ( "${FILE_NAME}" != "" ) && ( -f "${PATH_NAME}/${FILE_NAME}" ) ]]; then
                VALID_PATH_PARAM="${TRUE}"
                PROMPT_FILE="${PATH_NAME}/${FILE_NAME}"
                echo "Combining the Provided Pathname: ${PATH_NAME} and Filename: ${FILE_NAME} is a valid file: ${PROMPT_FILE}"
            elif [[ "${FILE_NAME}" == "" ]]; then
                echo "Pathname is not a Valid file: \"${PATH_NAME}\" but Filename has not yet been parsed"
                continue
            else
                echo "Pathname is a valid directory: \"${PATH_NAME}\", but the Combined Pathname/Filename: \"${PATH_NAME}/${FILE_NAME}\" is not a valid file"
                echo "Error: Prompt file is invalid when Pathname is combined with Filename. Exiting..."
                usage "${FALSE}"
            fi
        else
            echo "Provided Pathname is NOT a valid directory: \"${PATH_NAME}\""
            echo "Error: received an invalid Prompt File Path. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${FILE_FLAGS}"; then
        echo "Parsing file flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            echo "Parsing file value: \"${1}\""
            FILE_NAME="${1}"
            shift
        else
            echo "Error: Received File Flag but no File Value"
            echo "File Value not Provided, Exiting..."
            usage "${FALSE}"
        fi

        if [[ -f "${FILE_NAME}" ]]; then
            VALID_FILE_PARAM="${TRUE}"
            PROMPT_FILE="${FILE_NAME}"
            echo "Provided Filename is a valid file: ${PROMPT_FILE}"
        elif [[ ( "${PATH_NAME}" != "" ) && ( -f "${PATH_NAME}/${FILE_NAME}" ) ]]; then
            VALID_FILE_PARAM="${TRUE}"
            PROMPT_FILE="${PATH_NAME}/${FILE_NAME}"
            echo "Combining the Provided Pathname: ${PATH_NAME} and Filename: ${FILE_NAME} is a valid file: ${PROMPT_FILE}"
        elif [[ ${PATH_NAME} == "" ]]; then
            echo "Filename is not a Valid file: \"${FILE_NAME}\" but Pathname has not yet been parsed"
            continue
        else
            echo "Neither Filename: \"${FILE_NAME}\", Pathname: \"${PATH_NAME}\", nor Combined path and file: \"${PATH_NAME}/${FILE_NAME}\" is a valid file."
            echo "Error: received an invalid Prompt File.  Exiting"
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${RESUME_FLAGS}"; then
        echo "Parsing resume flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            echo "Parsing resume session id value: \"${1}\""
            SESSION_ID="${1}"
            shift
            echo "Validating Session ID: \"${SESSION_ID}\""
            SESSION_ID="$(validate_session_id "${SESSION_ID}")"
            RETURN_VALUE=$?
            if [[ ( "${RETURN_VALUE}" == "${TRUE}" ) && ( "${SESSION_ID}" != "" ) ]]; then
                echo "Session ID is valid: \"${SESSION_ID}\""
                echo "Completed validating Session ID: \"${SESSION_ID}\""
                RESUME_VALUE="${CLAUDE_RESUME_FLAGS} ${SESSION_ID}"
                echo "Received a Valid Resume Param: \"${RESUME_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
                CLAUDE_CODE_PARAMS+=("${CLAUDE_RESUME_FLAGS}" "${SESSION_ID}")
                echo "Completed parsing resume session id value: \"${SESSION_ID}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
            else
                echo "Session ID is invalid: \"${SESSION_ID}\""
                echo "Error: Session ID is invalid. Exiting..."
                usage "${FALSE}"
            fi
        else
            echo "Valid Session ID to Resume was not Provided, Operation cannot continue.  Exiting..."
            echo "Error: Received Resume Flag but no Valid Session ID to Resume."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${SESSION_ID_FLAGS}"; then
        echo "Parsing session id flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            echo "Parsing session id value: \"${1}\""
            SESSION_ID_VALUE="${CLAUDE_SESSION_ID_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_FLAGS}" "${1}")
            shift
            echo "Received a Session ID Value Param: \"${SESSION_ID_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        else
            echo "Warning: Received Session ID Flag but no Session ID Name."
            echo "Session ID Value not Provided, Assigning a new UUID as Session ID."
            # SESSION_ID_VALUE="${CLAUDE_SESSION_ID_FLAGS} $(uuidgen | tr -d '-')"
            local generated_uuid
            generated_uuid="$(uuidgen)"
            SESSION_ID_VALUE="${CLAUDE_SESSION_ID_FLAGS} ${generated_uuid}"
            echo "Continuing with new Session ID value: \"${SESSION_ID_VALUE}\""
            CLAUDE_CODE_PARAMS+=("${CLAUDE_SESSION_ID_FLAGS}" "${generated_uuid}")
            echo "Received a new Session ID Param: \"${SESSION_ID_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        fi
        save_session_id "${SESSION_ID_VALUE}"
    elif matches_pattern "${CURRENT_ELEMENT}" "${WORKTREE_FLAGS}"; then
        echo "Parsing worktree flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) ]]; then
            echo "Parsing worktree value: \"${1}\""
            WORKTREE_VALUE="${CLAUDE_WORKTREE_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_WORKTREE_FLAGS}" "${1}")
            shift
            echo "Received a Worktree Value Param: \"${WORKTREE_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        else
            echo "Worktree Value not Provided, Letting Claude Code Assign a worktree name."
            echo "Warning: Received Worktree Flag but no Worktree Name"
            WORKTREE_VALUE="${CLAUDE_WORKTREE_FLAGS}"
            echo "Continuing without Worktree Name, Worktree value: \"${WORKTREE_VALUE}\""
            CLAUDE_CODE_PARAMS+=("${WORKTREE_VALUE}")
            echo "Received a Worktree Param: \"${WORKTREE_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${EFFORT_FLAGS}"; then
        echo "Parsing effort flags"
        if [[ ( "${1}" != "" ) && ( "${1:0:2}" != "${SPACER_FLAGS}" ) && ( ( "${1}" == "${EFFORT_LOW}" ) || ( "${1}" == "${EFFORT_MED}" ) || ( "${1}" == "${EFFORT_HIGH}" ) ) ]]; then
            echo "Parsing effort value: \"${1}\""
            EFFORT_VALUE="${CLAUDE_EFFORT_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_EFFORT_FLAGS}" "${1}")
            shift
            echo "Received an Effort Value Param: \"${EFFORT_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        else
            echo "Error:  Received Effort flag but no valid Effort Value"
            echo "Effort Value not Provided or Invalid. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${MODEL_FLAGS}"; then
        echo "Parsing model flags"
        if [[ "${1}" != "" ]]; then
            # TODO: Validate Model value
            MODEL_VALUE="${CLAUDE_MODEL_FLAGS} ${1}"
            CLAUDE_CODE_PARAMS+=("${CLAUDE_MODEL_FLAGS}" "${1}")
            shift
            echo "Received a Model Value Param: \"${MODEL_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
        else
            echo "Model Value not Provided"
            echo "Error: Received Model Flag but no Model Name"
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${PROMPT_FLAGS}"; then
        echo "Parsing prompt flags"
        if [[ "${1}" != "" ]]; then
            PROMPT_VALUE="${1}"
            shift
            VALID_PROMPT_PARAM="${TRUE}"
        else
            echo "Prompt String was NOT provided"
            echo "Error: Did not receive an valid prompt string. Exiting..."
            usage "${FALSE}"
        fi
    elif matches_pattern "${CURRENT_ELEMENT}" "${VERSION_FLAGS}"; then
        echo "Parsing version flags"
        echo "User requested version information for Claude Code model"
        echo "Calling claude with Version Flags: \"${CLAUDE_VERSION_FLAGS}\""
        claude "${CLAUDE_VERSION_FLAGS}"
        echo "Completed calling claude with Version Flags: \"${CLAUDE_VERSION_FLAGS}\". Exiting..."
        exit "${TRUE}"
    elif matches_pattern "${CURRENT_ELEMENT}" "${HEADLESS_FLAGS}"; then
        echo "Parsing headless flags"
        HEADLESS_VALUE="${CLAUDE_HEADLESS_FLAGS}"
        CLAUDE_CODE_PARAMS+=("${HEADLESS_VALUE}")
        echo "Received a Headless Value Param: \"${HEADLESS_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
    elif matches_pattern "${CURRENT_ELEMENT}" "${PERMISSIONS_FLAGS}"; then
        echo "Parsing permissions flags"
        PERMISSIONS_VALUE="${CLAUDE_PERMISSIONS_FLAGS}"
        CLAUDE_CODE_PARAMS+=("${PERMISSIONS_VALUE}")
        echo "Received a Permissions Value Param: \"${PERMISSIONS_VALUE}\", Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
    elif matches_pattern "${CURRENT_ELEMENT}" "${SPACER_FLAGS}"; then
        echo "Parsing spacer flags"
        echo "Received a Spacer Flag: \"${CURRENT_ELEMENT}\""
        continue
    elif matches_pattern "${CURRENT_ELEMENT}" "${USAGE_FLAGS}"; then
        echo "Parsing usage flags"
        echo "Calling usage function with Exit After: \"${FALSE}\""
        usage "${FALSE}"
    elif matches_pattern "${CURRENT_ELEMENT}" "${HELP_FLAGS}"; then
        echo "Parsing help flags"
        echo "User requested help with function with Exit After: \"${TRUE}\""
        usage "${TRUE}"
    else
        echo "Parsing invalid input param"
        echo "Received Invalid Input Param: \"${CURRENT_ELEMENT}\""
        echo "Calling usage function with Exit After: \"${FALSE}\""
        usage "${FALSE}"
        # continue
    fi
    echo "Completed Parsing input parameter: \"${CURRENT_ELEMENT}\""
    echo "Current Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\", Prompt Value: \"${PROMPT_VALUE}\", Prompt File: \"${PROMPT_FILE}\", Valid File Param: \"${VALID_FILE_PARAM}\", Valid Path Param: \"${VALID_PATH_PARAM}\", Valid Prompt Param: \"${VALID_PROMPT_PARAM}\""
done
echo "Completed Parsing input parameters"


########################################################################################################################################################################
# Build Claude Code Prompt
########################################################################################################################################################################
echo "Build Claude Code Prompt"

if [[ ( "${PROMPT_VALUE}" != "" ) && ( "${VALID_PROMPT_PARAM}" == "${TRUE}" ) ]]; then
    CLAUDE_CODE_PROMPT="${PROMPT_VALUE}"
elif [[ ( "${PROMPT_FILE}" != "" ) && ( ( "${VALID_FILE_PARAM}" == "${TRUE}" ) || ( "${VALID_PATH_PARAM}" == "${TRUE}" ) ) ]]; then 
    CLAUDE_CODE_PROMPT="$(cat "${PROMPT_FILE}")"
fi

if [[ "${CLAUDE_CODE_PROMPT}" != "" ]]; then
    CLAUDE_CODE_PARAMS+=("${CLAUDE_CODE_PROMPT}")
fi
if [[ ( "${VALID_FILE_PARAM}" == "${TRUE}" ) || ( "${VALID_PATH_PARAM}" == "${TRUE}" ) || ( "${VALID_PROMPT_PARAM}" == "${TRUE}" ) ]]; then
    echo "Received Valid Script Input Params"
    echo "Final Claude Code Params: \"${CLAUDE_CODE_PARAMS[*]}\""
fi
echo "Completed Building Claude Code Prompt"


########################################################################################################################################################################
# Execute Claude Code
########################################################################################################################################################################
echo "Execute Claude Code"

NOHUP_LOG_FILE="wake_the_claude.nohup.log"
if ! : >> "${NOHUP_LOG_FILE}" 2>/dev/null; then
    if [[ "${HOME}" != "" ]]; then
        NOHUP_LOG_FILE="${HOME}/wake_the_claude.nohup.log"
    fi
    if ! : >> "${NOHUP_LOG_FILE}" 2>/dev/null; then
        echo "Error: Failed to open nohup log file: \"${NOHUP_LOG_FILE}\"" >&2
        exit 1
    fi
fi
echo "nohup claude ${CLAUDE_CODE_PARAMS[*]} >> ${NOHUP_LOG_FILE} 2>&1 &"
nohup claude "${CLAUDE_CODE_PARAMS[@]}" >> "${NOHUP_LOG_FILE}" 2>&1 &
NOHUP_STATUS=$?
if [[ "${NOHUP_STATUS}" != "0" ]]; then
    echo "Error: Failed to launch claude with nohup" >&2
    exit 1
fi
echo "Completed Executing Claude Code"
exit 0
