#!/usr/bin/env bash

TRUE="0"
FALSE="1"

OLD_IFS="${IFS}"
IFS=$'\n'

WORKTREE_NAME_IDENTIFIER_DEFAULT="fix--connect-canopy-cascor"
if [[ "${1}" == "" ]]; then
    WORKTREE_NAME_IDENTIFIER="${WORKTREE_NAME_IDENTIFIER_DEFAULT}"
else
    WORKTREE_NAME_IDENTIFIER="$1"
fi

FOUND="${FALSE}"
for i in $(git worktree list | grep "${WORKTREE_NAME_IDENTIFIER}" | awk -F " " '{print $1;}'); do
    if [[ "${i}" == "" ]]; then
        break
    else
        FOUND="${TRUE}"
        echo "removing ${i}"
        git worktree remove "${i}"
    fi
done

if [[ "${FOUND}" != "${TRUE}" ]]; then
    echo "Worktree Not Found.  Exiting..."
else
    echo "Worktree(s) Removed"
fi

IFS="${OLD_IFS}"
