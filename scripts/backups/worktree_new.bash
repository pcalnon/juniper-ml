#!/usr/bin/env bash

TRUE="0"
FALSE="1"

JUNIPER_PROJECT_WORKTREE_DIR="${HOME}/Development/python/Juniper/worktrees"
JUNIPER_WORKTREE_NAME="juniper-canopy-cascor--fix--connect-canopy-cascor--$(date +%Y%m%d-%H%M)--$(uuidgen)"

JUNIPER_WORKTREE_NEW="${JUNIPER_PROJECT_WORKTREE_DIR}/${JUNIPER_WORKTREE_NAME}"


# Note: This function is a generic, posix compliant sourcing check, but doesn't check if [[great]grand]parent script was sourced
function is_sourced() {
    if [ -n "$ZSH_VERSION" ]; then 
        case $ZSH_EVAL_CONTEXT in *:file:*) return ${TRUE};; esac
    else  # Add additional POSIX-compatible shell names here, if needed.
        case ${0##*/} in dash|-dash|bash|-bash|ksh|-ksh|sh|-sh) return ${TRUE};; esac
    fi
    return "${FALSE}"  # NOT sourced.
}

# Verify worktree doesn't already exist
if [[ ( -d "${JUNIPER_WORKTREE_NEW}" ) && ( "$(is_sourced)" == "${FALSE}" ) ]]; then
    # if script is sourced, don't do anything hasty, just let it end
    echo "Error: Unable to add new worktree: \"${JUNIPER_WORKTREE_NAME}\"."
    echo "Error: Worktree directory already exists: \"${JUNIPER_WORKTREE_NEW}}\""
    exit 1

# Create the new worktree
elif [[ ! -d "${JUNIPER_WORKTREE_NEW}" ]]; then

    echo "git worktree add \"${JUNIPER_WORKTREE_NEW}\""
    git worktree add "${JUNIPER_WORKTREE_NEW}"

    # Verify new worktree
    if [[ ! ( ( -d "${JUNIPER_WORKTREE_NEW}" ) || ( "$(is_sourced)" == "${TRUE}" ) ) ]]; then
        # if script is sourced, don't do anything hasty, just let it end
        echo "Error: Failed to Add New Worktree: \"${JUNIPER_WORKTREE_NAME}\"."
        exit 1
    elif [[ ( -d "${JUNIPER_WORKTREE_NEW}" ) && ( "$(is_sourced)" == "${TRUE}" ) ]]; then
        cd "${JUNIPER_WORKTREE_NEW}"
    elif [[ -d "${JUNIPER_WORKTREE_NEW}" ]]; then
        echo "Successfully added new worktreee: ${JUNIPER_WORKTREE_NAME}"
        cd "${JUNIPER_WORKTREE_NEW}"
        # activate_new_worktree "${JUNIPER_WORKTREE_NEW}"
    else
        # Note: failed to create: script is sourced
        sleep 0
    fi

else
    # Note: worktree already exists: script is sourced
    sleep 0
fi

exec ${SHELL}
