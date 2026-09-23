#!/usr/bin/env bash
#####################################################################################################################################################################################################################################################
#
#####################################################################################################################################################################################################################################################


#####################################################################################################################################################################################################################################################
# Define script constants

TRUE=0
FALSE=1


#####################################################################################################################################################################################################################################################
# Define Script Variables
USERNAME="pcalnon"

DEVICE_SDA="/dev/sda"
DEVICE_SDA1="/dev/sda1"
DEVICE_SDB="/dev/sdb"
DEVICE_SDB1="/dev/sdb1"
DEVICE_SDB2="/dev/sdb2"
DEVICE_SDC="/dev/sdc"
DEVICE_SDC1="/dev/sdc1"
DEVICE_SDC2="/dev/sdc2"
DEVICE_SDC3="/dev/sdc3"
DEVICE_SDC4="/dev/sdc4"
DEVICE_SDD="/dev/sdd"
DEVICE_SDD1="/dev/sdd1"
CURRENT_DEVICE="${DEVICE_SDA}"
DEVICE_LABEL="${CURRENT_DEVICE##*/}"

TEST_TYPE_SHORT="short"
TEST_TYPE_LONG="long"
CURRENT_TEST_TYPE="${TEST_TYPE_LONG}"

TIMESTAMP="$(date +%F_%T)"

OUTPUT_FILE_EXT="out"


#####################################################################################################################################################################################################################################################
# Define Environment Constants

# Define Directory Name Constants
HOME_DIR_NAME="home"
USER_DIR_NAME="${USERNAME}"
DEVELOPMENT_DIR_NAME="Development"
LANGUAGE_DIR_NAME="python"
PROJECT_DIR_NAME="Juniper"
APPLICATION_DIR_NAME="juniper-ml"
REPORTS_DIR_NAME="reports"
SMART_CHECKS_DIR_NAME="smart"

# Define Directory Constants
HOME_DIR="/${HOME_DIR_NAME}"
USER_DIR="${HOME_DIR}/${USER_DIR_NAME}"
DEVELOPMENT_DIR="${USER_DIR}/${DEVELOPMENT_DIR_NAME}"
LANGUAGE_DIR="${DEVELOPMENT_DIR}/${LANGUAGE_DIR_NAME}"
PROJECT_DIR="${LANGUAGE_DIR}/${PROJECT_DIR_NAME}"
APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_DIR_NAME}"
REPORTS_DIR="${APPLICATION_DIR}/${REPORTS_DIR_NAME}"
SMART_CHECKS_DIR="${REPORTS_DIR}/${SMART_CHECKS_DIR_NAME}"

# Define output file constants
START_TESTS_FILENAME_ROOT="smart-t-${CURRENT_TEST_TYPE}-${DEVICE_LABEL}"
CHECK_RESULT_FILENAME_ROOT="smart-xall_results-${DEVICE_LABEL}"

START_TESTS_FILENAME="${START_TESTS_FILENAME_ROOT}_${TIMESTAMP}.${OUTPUT_FILE_EXT}"
CHECK_RESULT_FILENAME="${CHECK_RESULT_FILENAME_ROOT}_${TIMESTAMP}.${OUTPUT_FILE_EXT}"

START_TESTS_FILE="${SMART_CHECKS_DIR}/${START_TESTS_FILENAME}"
CHECK_RESULT_FILE="${SMART_CHECKS_DIR}/${CHECK_RESULT_FILENAME}"


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
    # Start the tests
    smartctl -t "${CURRENT_TEST_TYPE}" "${CURRENT_DEVICE}" > "${START_TESTS_FILE}" 2>&1
    chown "${USERNAME}":"${USERNAME}" "${START_TESTS_FILE}"
elif [[ "${CHECK_RESULT}" == "${TRUE}" ]]; then
    # display the results of the smart tests 
    smartctl --xall "${CURRENT_DEVICE}" > "${CHECK_RESULT_FILE}" 2>&1
    chown "${USERNAME}":"${USERNAME}" "${CHECK_RESULT_FILE}"
elif [[ ( ( "${START_TESTS}" == "${FALSE}" ) && ( "${CHECK_RESULT}" == "${FALSE}" ) ) || ( ( "${START_TESTS}" == "${TRUE}" ) && ( "${CHECK_RESULT}" == "${TRUE}" ) ) ]]; then
    echo "Error: No valid task specified."
else
    echo "Error: This code should be unreachable."
fi


