#!/usr/bin/env bash

# OLD_IFS="${IFS}"; IFS=$'{\n}'; for i in $(grep --exclude-dir logs --exclude-dir reports  -rnI "juniper-cascor" ./*); do FILE="$(echo "${i}" | awk -F ":" '{print $1;}')"; echo "${FILE}"; sed -i 's/juniper-cascor/juniper-cascor/g' "${FILE}";  done; IFS="${OLD_IFS}"

# Old Value
PASCAL_CASE_TEXT="juniper-cascor"

# New Value
KIBAB_CASE_TEXT="juniper-cascor"

OLD_IFS="${IFS}"
IFS=$'{\n}'

for i in $(grep --exclude-dir logs --exclude-dir reports  -rnI "${PASCAL_CASE_TEXT}" ./*); do
    FILE="$(echo "${i}" | awk -F ":" '{print $1;}')"
    echo "${FILE}"

    sed -i "s/${PASCAL_CASE_TEXT}/${KIBAB_CASE_TEXT}/g" "${FILE}"
done

IFS="${OLD_IFS}"



