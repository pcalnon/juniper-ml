#!/usr/bin/env bash

ORIGINAL_PWD="$(pwd)"
echo "ORIGINAL_PWD: ${ORIGINAL_PWD}"
OLD_IFS="${IFS}"
IFS=$'\n'
NUMBER="$(echo "$(git branch | grep -e "^\+ worktree-")" | wc -l)"
COUNTER=0
for i in $(git branch | grep -e "^\+ worktree-"); do
    COUNTER="$(( COUNTER + 1 ))"
    echo "Updating branch: ${i} (${COUNTER} of ${NUMBER})"
    echo "ORIGINAL_PWD: ${ORIGINAL_PWD}"
    cd "${ORIGINAL_PWD}"
    echo "PWD: \"${PWD}\""
    echo "i: \"${i}\""
    WORK_DIRISH="${i/-/s\/}"
    echo "WORK_DIRISH: \"${WORK_DIRISH}\""
    WORK_DIR="${PWD}/.claude/${WORK_DIRISH:2}"
    echo "WORK_DIR: \"${WORK_DIR}\""
    if [[ -d "${WORK_DIR}" ]]; then
        echo "Found Valid Work Dir: \"${WORK_DIR}\""
        cd "${WORK_DIR}"
        echo "git status"
        git status 2>/dev/null
        echo "git add --all"
        git add --all 2>/dev/null
        echo "git pull origin main"
        git pull origin main 2>/dev/null
        echo "git push origin HEAD"
        git push origin HEAD 2>/dev/null
        echo "Valid Dir: ORIGINAL_PWD: ${ORIGINAL_PWD}"
    else
        echo "Skipping Invalid Work Dir: \"${WORK_DIR}\""
        continue
    fi
    echo -ne "\n"
done
