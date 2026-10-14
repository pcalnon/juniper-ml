#!/usr/bin/env bash


FILENAME="encryption.bash"
WORKING_DIR="/Users/pcalnon/Development"

cd "${WORKING_DIR}"
for i in $(find . | grep "${FILENAME}"); do
    CMD="ls -Fla ${i}"
    echo -ne "${CMD}:\t"
    FILEPATH="$(eval "${CMD}" | awk -F " " '{print $9;}')"
    FULL_FILEPATH="${WORKING_DIR}/${FILEPATH#*\/}"
    echo -ne "${FULL_FILEPATH}\t==> "
    # Validate found files
    if [[ -f "${i}" ]]; then
        echo -ne "Valid\n"
    else
        echo -ne "Invalid\n"
    fi
done

