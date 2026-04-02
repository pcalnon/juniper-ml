#!/usr/bin/env bash

export TRUE="0"
export FALSE="1"

# Note: This function is a generic, posix compliant sourcing check, but doesn't check if [[great]grand]parent script was sourced
function is_sourced() {
    if [ -n "$ZSH_VERSION" ]; then
        case $ZSH_EVAL_CONTEXT in *:file:*) return ${TRUE};; esac
    else  # Add additional POSIX-compatible shell names here, if needed.
        case ${0##*/} in dash|-dash|bash|-bash|ksh|-ksh|sh|-sh) return ${TRUE};; esac
    fi
    return "${FALSE}"  # NOT sourced.
}


function activate_new_worktree() {
    if [[ "$(is_sourced)" == "${FALSE}" ]]; then
        echo "This function should not be launched manually.  It is intended to be sourced in .bashrc"
    elif [[ "${1}" == "" ]]; then
        echo "Error, Worktree Directory Not Specified!"
    elif [[ ! -d "${1}" ]]; then
        echo "Error, Worktree Directory Does not Exist!"
    else
        cd "${1}" || return
    fi
}
