#!/usr/bin/env bash

if [[ "${1}" == "" ]]; then
    echo -ne "\nError:  Worktree name not provided.  Exiting...\n"
    exit 1
elif [[ "$(echo "$(git worktree list)" | grep "${1}")" == "" ]]; then
    echo -ne "\nError: Provided Worktree is Invalid. Exiting...\n"
    exit 2
else
    echo -ne "\nReceived Valid Worktree. Beginning Cleanup:\n"
fi

while [[ "${*}" != "" ]]; do
    WORKTREE_NAME="$1"
    shift
    echo -ne "\nWorktree Cleanup: \"${WORKTREE_NAME}\"\n"

    echo -ne "\ngit worktree remove \"${WORKTREE_NAME}\"\n"
    git worktree remove "${WORKTREE_NAME}"

    echo -ne "\ngit branch -d \"worktree-${WORKTREE_NAME}\"\n"
    git branch -d "worktree-${WORKTREE_NAME}"

    echo -ne "\ngit worktree prune\n"
    git worktree prune

    echo -ne "\ngit worktree list\n"
    git worktree list

    echo -ne "\ngit branch\n"
    git branch

done
