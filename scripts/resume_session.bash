#!/usr/bin/env bash
########################################################################################################################################################################
# Resume a Claude Session
########################################################################################################################################################################
# ./scripts/wake_the_claude.bash --resume 2bde217d-7375-4329-a253-e611909dca5c --worktree binary-jingling-horizon --effort high --dangerously-skip-permissions
########################################################################################################################################################################


########################################################################################################################################################################
# Define Parameters
#     TODO: Update these parameters to your own values
#     TODO: Consider using conf file or command line parameters
########################################################################################################################################################################
# SESSION_ID_PARAM="3b3755b9-b379-411a-89e5-ba9f80abe1e2"
# SESSION_ID_PARAM="7bf590e8-204b-4e03-bc6c-5eef743365d8"
# SESSION_ID_PARAM="3a4f2d46-28c1-40b7-8c26-92ec5edfea3b"
 SESSION_ID_PARAM="da3f230a-90a8-4a08-a30d-b9721c4fd785"

# WORKTREE_NAME_PARAM="dynamic-drifting-newt"
# WORKTREE_NAME_PARAM="serene-splashing-meadow"
# WORKTREE_NAME_PARAM="calm-winding-stream"
WORKTREE_NAME_PARAM="clever-frolicking-beach"


########################################################################################################################################################################
# Infrequently Changed Parameters
#     TODO: Consider using conf file or command line parameters
########################################################################################################################################################################
EFFORT_LEVEL_PARAM="max"
PROMPT_PARAM="Hello World, Claude!"
REMOTE_CONTROL_PARAM="1"
DANGEROUSLY_SKIP_PERMISSIONS_PARAM="1"


########################################################################################################################################################################
# Define Environment Variables
########################################################################################################################################################################
export JUNIPER_PROJECT_NAME="Juniper"
export JUNIPER_ML_APP_NAME="juniper-ml"
export WORKTREES_DIR_NAME="worktrees"
export CLAUDE_WORKTREES_DIR_NAME=".claude/${WORKTREES_DIR_NAME}"


########################################################################################################################################################################
# Define Paths
########################################################################################################################################################################
export JUNIPER_PATH="${HOME}/Development/python/${JUNIPER_PROJECT_NAME}"
export JUNIPER_ML_PATH="${JUNIPER_PATH}/${JUNIPER_ML_APP_NAME}"

export SCRIPTS_DIR_NAME="scripts"
export JUNIPER_ML_SCRIPTS_PATH="${JUNIPER_ML_PATH}/${SCRIPTS_DIR_NAME}"


########################################################################################################################################################################
# Define Worktree Paths
########################################################################################################################################################################
export WORKTREE_HARNESS_PATH="${JUNIPER_ML_PATH}/${CLAUDE_WORKTREES_DIR_NAME}"
export WORKTREE_JUNIPER_PATH="${JUNIPER_PATH}/${WORKTREES_DIR_NAME}"


########################################################################################################################################################################
# Define Script Paths
########################################################################################################################################################################
export CLAUDE_LAUNCH_SCRIPT_NAME="wake_the_claude.bash"
export CLAUDE_LAUNCH_SCRIPT_PATH="${JUNIPER_ML_SCRIPTS_PATH}"
export CLAUDE_LAUNCH_SCRIPT="${CLAUDE_LAUNCH_SCRIPT_PATH}/${CLAUDE_LAUNCH_SCRIPT_NAME}"


########################################################################################################################################################################
# Define Session Variables
########################################################################################################################################################################

# Session ID
SESSION_ID="${SESSION_ID_PARAM}"
RESUME_FLAG="--resume"
RESUME_FLAGS=""
if [[ "${SESSION_ID}" != "" ]]; then
    RESUME_FLAGS+="${RESUME_FLAG} ${SESSION_ID}"
fi

# Worktree
WORKTREE_NAME="${WORKTREE_NAME_PARAM}"
WORKTREE_FLAG="--worktree"
WORKTREE_FLAGS=""
if [[ "${WORKTREE_NAME}" != "" ]]; then
    WORKTREE_FLAGS+="${WORKTREE_FLAG} ${WORKTREE_NAME}"
fi

# Effort
EFFORT_LEVEL="${EFFORT_LEVEL_PARAM}"
EFFORT_FLAG="--effort"
EFFORT_FLAGS=""
if [[ "${EFFORT_LEVEL}" != "" ]]; then
    EFFORT_FLAGS+="${EFFORT_FLAG} ${EFFORT_LEVEL}"
fi

# Prompt
PROMPT="${PROMPT_PARAM}"
PROMPT_FLAG="--prompt"
PROMPT_FLAGS=""
if [[ "${PROMPT}" != "" ]]; then
    PROMPT_FLAGS+="${PROMPT_FLAG} \"${PROMPT}\""
fi

# Remote Control
REMOTE_CONTROL="${REMOTE_CONTROL_PARAM}"
REMOTE_CONTROL_FLAG="--remote-control"
REMOTE_CONTROL_FLAGS=""

if [[ "${REMOTE_CONTROL}" == "1" ]]; then
    REMOTE_CONTROL_FLAGS+="${REMOTE_CONTROL_FLAG}"
fi

# Dangerously Skip Permissions
DANGEROUSLY_SKIP_PERMISSIONS="${DANGEROUSLY_SKIP_PERMISSIONS_PARAM}"
DANGEROUSLY_SKIP_PERMISSIONS_FLAG="--dangerously-skip-permissions"
PERMISSIONS_FLAGS=""

if [[ "${DANGEROUSLY_SKIP_PERMISSIONS}" == "1" ]]; then
    PERMISSIONS_FLAGS+="${DANGEROUSLY_SKIP_PERMISSIONS_FLAG}"
fi


########################################################################################################################################################################
# Resume the Session
########################################################################################################################################################################
# ${CLAUDE_LAUNCH_SCRIPT} ${RESUME_FLAGS} ${WORKTREE_FLAGS} ${EFFORT_FLAGS} ${PROMPT_FLAGS} -- ${PERMISSIONS_FLAGS} ${REMOTE_CONTROL_FLAGS}
${CLAUDE_LAUNCH_SCRIPT} ${RESUME_FLAGS} ${WORKTREE_FLAGS} ${EFFORT_FLAGS} ${PROMPT_FLAG} "${PROMPT}" -- ${PERMISSIONS_FLAGS} ${REMOTE_CONTROL_FLAGS}
