#!/usr/bin/env bash

PARAMS_TEST="--prompt \"Hello Claude!\" -- --effort high --print"

if [[ "${@}" != "" ]]; then
    echo "Input Params: \"${@}\""
else
    echo "No input params provided."
    echo "Next time try these:"
    echo -ne "\t${PARAMS_TEST}\n"
    exit 0
fi

PROMPT_PARAM=0
COUNTER=0
PARAMS_LIST=""
CURRENT_PROMPT=""

while [[ "${1}" != "" ]]; do
    CURRENT_PARAM="${1}"
    shift
    if [[ "${CURRENT_PARAM}" == "--" ]]; then
        echo "Found Param Spacer: \"${CURRENT_PARAM}\""
        continue
    elif [[ "${CURRENT_PARAM}" == "--prompt" ]]; then
        echo "Found Prompt Param: \"${CURRENT_PARAM}\""
        # PARAMS_LIST="${PARAMS_LIST}${CURRENT_PARAM} "
        PROMPT_PARAM=1
    elif [[ "${PROMPT_PARAM}" == 1 ]]; then
        # PARAMS_LIST="${PARAMS_LIST}\"${CURRENT_PARAM}\" "
        CURRENT_PROMPT="${CURRENT_PARAM}"
        PROMPT_PARAM=2
    else
        PARAMS_LIST="${PARAMS_LIST}${CURRENT_PARAM} "
    fi
    COUNTER="$(( COUNTER + 1 ))"
    echo "Current Param ${COUNTER}: \"${CURRENT_PARAM}\", Params List: \"${PARAMS_LIST}\""
done

if [[ "${PROMPT_PARAM}" == "2" ]]; then
    PARAMS_LIST="${PARAMS_LIST}\"${CURRENT_PROMPT}\""
fi
echo "Completed Parsing ${COUNTER} input params: \"${PARAMS_LIST}\""

echo "claude ${PARAMS_LIST}"
claude ${PARAMS_LIST}
