#!/usr/bin/env bash
#####################################################################################################################################################################################################################################################
#
#####################################################################################################################################################################################################################################################


#####################################################################################################################################################################################################################################################
# Define script constants

export TRUE=0
export FALSE=1


#####################################################################################################################################################################################################################################################
# Define Script Variables
export USERNAME="pcalnon"

export DEVICE_SDA="/dev/sda"
export DEVICE_SDA1="/dev/sda1"
export DEVICE_SDB="/dev/sdb"
export DEVICE_SDB1="/dev/sdb1"
export DEVICE_SDB2="/dev/sdb2"
export DEVICE_SDC="/dev/sdc"
export DEVICE_SDC1="/dev/sdc1"
export DEVICE_SDC2="/dev/sdc2"
export DEVICE_SDC3="/dev/sdc3"
export DEVICE_SDC4="/dev/sdc4"
export DEVICE_SDD="/dev/sdd"
export DEVICE_SDD1="/dev/sdd1"
export DEVICE_SDD1="/dev/sdd1"
export CURRENT_DEVICE="${DEVICE_SDA}"
export DEVICE_LABEL="${CURRENT_DEVICE##*/}"

export TEST_TYPE_SHORT="short"
export TEST_TYPE_LONG="long"
export CURRENT_TEST_TYPE="${TEST_TYPE_LONG}"

DATE_STAMP="$(date +%F)" || { echo "Error: Failed to get date stamp"; exit 1; }
TIME_STAMP="$(date +%T)" || { echo "Error: Failed to get time stamp"; exit 1; }
export TIMESTAMP="${DATE_STAMP}_${TIME_STAMP}"

export OUTPUT_FILE_EXT="out"


#####################################################################################################################################################################################################################################################
# Define Environment Constants

# Define Directory Name Constants
export HOME_DIR_NAME="home"
export USER_DIR_NAME="${USERNAME}"
export DEVELOPMENT_DIR_NAME="Development"
export LANGUAGE_DIR_NAME="python"
export PROJECT_DIR_NAME="Juniper"
export APPLICATION_DIR_NAME="juniper-ml"
export REPORTS_DIR_NAME="reports"
export SMART_CHECKS_DIR_NAME="smart"

# Define Directory Constants
export HOME_DIR="/${HOME_DIR_NAME}"
export USER_DIR="${HOME_DIR}/${USER_DIR_NAME}"
export DEVELOPMENT_DIR="${USER_DIR}/${DEVELOPMENT_DIR_NAME}"
export LANGUAGE_DIR="${DEVELOPMENT_DIR}/${LANGUAGE_DIR_NAME}"
export PROJECT_DIR="${LANGUAGE_DIR}/${PROJECT_DIR_NAME}"
export APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_DIR_NAME}"
export REPORTS_DIR="${APPLICATION_DIR}/${REPORTS_DIR_NAME}"
export SMART_CHECKS_DIR="${REPORTS_DIR}/${SMART_CHECKS_DIR_NAME}"

# Define output file constants
export START_TESTS_FILENAME_ROOT="smart-t-${CURRENT_TEST_TYPE}-${DEVICE_LABEL}"
export CHECK_RESULT_FILENAME_ROOT="smart-xall_results-${DEVICE_LABEL}"

export START_TESTS_FILENAME="${START_TESTS_FILENAME_ROOT}_${TIMESTAMP}.${OUTPUT_FILE_EXT}"
export CHECK_RESULT_FILENAME="${CHECK_RESULT_FILENAME_ROOT}_${TIMESTAMP}.${OUTPUT_FILE_EXT}"

export START_TESTS_FILE="${SMART_CHECKS_DIR}/${START_TESTS_FILENAME}"
export CHECK_RESULT_FILE="${SMART_CHECKS_DIR}/${CHECK_RESULT_FILENAME}"


#####################################################################################################################################################################################################################################################
# Define functions

function not() {
    local value="${1}"
    local result="$(( ( value  + 1 ) % 2  ))"
    echo "${result}"
}


#####################################################################################################################################################################################################################################################
# START_TESTS="${TRUE}"
START_TESTS="${FALSE}"

CHECK_RESULT="$(not "${START_TESTS}")"


#####################################################################################################################################################################################################################################################
# Perform current smart test task

if [[ "${START_TESTS}" == "${TRUE}" ]]; then

    # Start the SMART tests
    smartctl -t "${CURRENT_TEST_TYPE}" "${CURRENT_DEVICE}" > "${START_TESTS_FILE}" 2>&1
    chown "${USERNAME}":"${USERNAME}" "${START_TESTS_FILE}"
elif [[ "${CHECK_RESULT}" == "${TRUE}" ]]; then

    # display the results of the SMART tests
    smartctl --xall "${CURRENT_DEVICE}" > "${CHECK_RESULT_FILE}" 2>&1
    chown "${USERNAME}":"${USERNAME}" "${CHECK_RESULT_FILE}"
elif [[ ( ( "${START_TESTS}" == "${FALSE}" ) && ( "${CHECK_RESULT}" == "${FALSE}" ) ) || ( ( "${START_TESTS}" == "${TRUE}" ) && ( "${CHECK_RESULT}" == "${TRUE}" ) ) ]]; then
    echo "Error: No valid task specified."
else
    echo "Error: This code should be unreachable."
fi
