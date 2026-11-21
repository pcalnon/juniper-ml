#!/usr/bin/env bash


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

while read -r file < "${FILE_LIST_FILE}"; do
    if [[ -f "${file}" ]]; then
        echo "File ${file} exists"
    else
        echo "File ${file} does not exist"
        exit 1
    fi

    git checkout --ours "${file}"
    git add "${file}"

    git commit -m "Resolve conflict in ${file}"

    git push origin
done
