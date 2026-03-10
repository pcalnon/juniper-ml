#!/usr/bin/env bash

CURRENT_PWD="$(pwd)"
for i in $(git branch | grep -v -e "^+\ worktree" | grep "worktree*"); do
    TREE_DIR="${CURRENT_PWD}/.claude/${i/-/s\/}"
    if [[ -d "${TREE_DIR}" ]]; then
        echo "${TREE_DIR}"
        cd ${TREE_DIR}
        git status
    else
        echo "Not Found: ${TREE_DIR} -- closing branch"
        git branch -d ${i}
    fi
done

