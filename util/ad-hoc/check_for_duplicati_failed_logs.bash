#!/usr/bin/env bash
################################################################################################################################################################################################################
#
################################################################################################################################################################################################################
# Descriptionn:
#     searches the latest tmp/tmp*** dir for state/failure.log from duplicati.
#     
#     TODO: This needs to search all valid dirs or take a date time staamp.
#
################################################################################################################################################################################################################
# Notes:
#
################################################################################################################################################################################################################
# References:
#
#     A=""; while true; do A="$(l -tr | awk -F " " '{print $9;}' | grep tmp | tail -1)state/"; ls -Fla "${A}" 2>/dev/null && break || echo "Latest invalid tmp dir: ${A}"; done
#     LOG_DIR="$(ls -Flatr | awk -F " " '{print $9;}' | grep "${DIRNAME_PREFIX}" | tail -1)${SUB_DIR}/"; ls -Fla "${A}" 2>/dev/null && break
#
#     LOG_DIR="$(ls -Flatr . | awk -F " " '{print $9;}' | grep -e "^${DIRNAME_PREFIX}" | tail -1)${SUB_DIR}/"; ls -Fla "${A}" 2>/dev/null && {  FOUND="${TRUE}"; break; }
#     LOG_DIR="${ROOT_DIR}/$(ls -Fladtr ${ROOT_DIR}/*/ | awk -F " " '{print $9;}' | awk -F "/" '{print $9;}' | grep -e "^${DIRNAME_PREFIX}" | tail -1)/${SUB_DIR}/";
#
#     echo "$(ls -Fladtr ${ROOT_DIR}/*/ | awk -F " " '{print $9;}' | awk -F "/" '{print $9;}' | grep -e "^${DIRNAME_PREFIX}" | tail -1)/${SUB_DIR}/"
#    #ls -Fla "${LOG_DIR}" 2>/dev/null && {  FOUND="${TRUE}"; break; } || echo "Log Dir: \"${LOG_DIR}\""
#
################################################################################################################################################################################################################


################################################################################################################################################################################################################
# Define global script constants
#
TRUE=0
FALSE=1

# DEBUG="${TRUE}"
DEBUG="${FALSE}"

MAX_CHECKS=10

# Set to number of seconds per check if desired
SLEEPY_TIME=0
# SLEEPY_TIME=1


################################################################################################################################################################################################################
# Define Environment Constants
#
ROOT_DIR="${HOME}/Development/python/Juniper/juniper-ml/tmp"
PARENT_DIR="tmp"
DIRNAME_PREFIX="${PARENT_DIR}"
SUB_DIR="state"


################################################################################################################################################################################################################
# Define Script Variables
#
LOG_DIR=""
TOTAL_CHECKS=0

FOUND="${FALSE}"


################################################################################################################################################################################################################
# Check for volitile tmp dir for duplicati failure logs
#
while true; do

    if (( TOTAL_CHECKS < MAX_CHECKS )); then
        TOTAL_CHECKS="$(( TOTAL_CHECKS + 1 ))"
    else
        break
    fi

    if (( SLEEPY_TIME > 0 )); then
        sleep "${SLEEPY_TIME}"
    fi

    LOG_DIR_NAME="$(ls -Fladtr ${ROOT_DIR}/*/ | awk -F " " '{print $9;}' | awk -F "/" '{print $9;}' | grep -e "^${DIRNAME_PREFIX}" | tail -1)/${SUB_DIR}/";
    LOG_DIR="${ROOT_DIR}/${LOG_DIR_NAME}"

    ls -Fla "${LOG_DIR}" 2>/dev/null && {  FOUND="${TRUE}"; break; }

    if [[ "${DEBUG}" == "${TRUE}" ]]; then
        echo "LOG_DIR=\"\$(ls -Fladtr ${ROOT_DIR}/*/ | awk -F \" \" '{print \$9;}' | awk -F \"/\" '{print \$9;}' | grep -e \"^${DIRNAME_PREFIX}\" | tail -1)/${SUB_DIR}/\"\; ls -Fla \"${LOG_DIR}\" 2>/dev/null"
        echo "${LOG_DIR_NAME}"
    elif [[ "${LOG_DIR_NAME}" == "${SUB_DIR}/" ]]; then
        echo -ne "."
        continue
    fi
    echo -ne "\nLatest invalid ${PARENT_DIR} dir: ${LOG_DIR_NAME}\n"

done

echo -ne "\nPerformed ${TOTAL_CHECKS} checks:\n"

if [[ "${FOUND}" == "${TRUE}" ]]; then
    echo "Found Valid Duplicati failed log dir: ${LOG_DIR}"
else
    echo "No Duplicati failed log dirs Found"
fi
