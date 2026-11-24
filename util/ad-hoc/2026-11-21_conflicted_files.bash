#!/usr/bin/env bash
########################################################################################################################
# Author: Juniper ML Team
# Email: overtoad.research@gmail.com
# Date: 2026-11-21
# Version: 0.1.0
# Status: Development
# Tags: util, conflict, resolve
# Last Modified: 2026-11-21
# Last Modified by: Juniper ML Team
########################################################################################################################
# Description:
#     This script is used to resolve conflicts in the current branch.
########################################################################################################################
# Notes:
#     The script will resolve conflicts in the current branch by checking out the their version of the file and adding it to the index.
#     The script will then commit the changes and push them to the origin.
#     The script will then exit.
########################################################################################################################
# Usage:
#     ./util/conflicted_files.bash
########################################################################################################################
# Variables:
#     CURRENT_DIR: The current directory.
#     UTIL_DIR_NAME: The name of the util directory.
#     UTIL_DIR_PATH: The path to the util directory.
#     FILE_LIST_NAME: The name of the file list.
#     FILE_LIST_FILE: The path to the file list.
########################################################################################################################
# Notes:
#
########################################################################################################################
# References:
#     https://www.atlassian.com/git/tutorials/git-merge/git-merge-strategy-ours
#     https://www.atlassian.com/git/tutorials/git-merge/git-merge-strategy-theirs
########################################################################################################################

CURRENT_DIR=$(pwd)
UTIL_DIR_NAME="util"
UTIL_DIR_PATH="${CURRENT_DIR}/${UTIL_DIR_NAME}"

FILE_LIST_NAME="conflicted_files.txt"
FILE_LIST_FILE="${UTIL_DIR_PATH}/${FILE_LIST_NAME}"

if [[ -f "${FILE_LIST_FILE}" ]]; then
    echo "File ${FILE_LIST_FILE} exists"
else
    echo "File ${FILE_LIST_FILE} does not exist"
    exit 1
fi

CURRENT_BRANCH=$(git branch | grep '^[[:space:]]*\*' | awk '{print $2}')
echo "Resolving conflicts in branch ${CURRENT_BRANCH}"

while read -r file; do
    if [[ -f "${file}" ]]; then
        echo "File ${file} exists"
    else
        echo "File ${file} does not exist"
        exit 1
    fi

    # git checkout --ours "${file}"
    echo "git checkout --theirs \"${file}\""
    git checkout --theirs "${file}"

    echo "git add \"${file}\""
    git add "${file}"

    echo "git commit -m \"Resolve conflict in ${file}\""
    git commit -m "Resolve conflict in \"${file}\""

    echo "git push origin ${CURRENT_BRANCH}"
    git push origin "${CURRENT_BRANCH}"

done < "${FILE_LIST_FILE}"
