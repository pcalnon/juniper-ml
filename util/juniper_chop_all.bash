#!/usr/bin/env bash
###########################################################################################################################################################################################################
#
###########################################################################################################################################################################################################


###########################################################################################################################################################################################################
# Define Script env constants
###########################################################################################################################################################################################################
echo "Script Name, Called: ${BASH_SOURCE[0]}"
echo "Script Path, Full:   $(realpath "${BASH_SOURCE[0]}")"
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
echo "Script Path, Only:   ${SCRIPT_NAME}"
echo "[${SCRIPT_NAME}:${LINENO}] Beginning script run"


###########################################################################################################################################################################################################
# Define juniper-ml application constants
###########################################################################################################################################################################################################
JUNIPER_PROJECT_DIR="${HOME}/Development/python/Juniper"
JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_ML_CONDA="JuniperCascor"
JUNIPER_ML_SLEEPYTIME="10"
JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILE=\"${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}\""

CONDA="/opt/miniforge3/etc/profile.d/conda.sh"
PYTHON="/opt/miniforge3/envs/JuniperCanopy/bin/python"

# KILL_SIGNAL="-KILL"
KILL_SIGNAL="-SIGHUP"
# KILL_SIGNAL="-SIGTERM"


###########################################################################################################################################################################################################
# Initialize Conda prior to launching individual services
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] source \"${CONDA}\""
# shellcheck source=/dev/null
source "${CONDA}"

echo "[${SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_ML_CONDA}\""
conda activate "${JUNIPER_ML_CONDA}"


###########################################################################################################################################################################################################
# Launch Juniper Data service in Background
#     for JUNIPER_CANOPY_PIDFILE_LINE in $(cat "${JUNIPER_PROJECT_PID_FILE}" | awk -F " " '{print $2;}'); do
#     echo "for JUNIPER_PIDFILE_LINE in \$(cat \"${JUNIPER_PROJECT_PID_FILE}\"); do"
###########################################################################################################################################################################################################
OLD_IFS="${IFS}"
IFS=$'\n'
for JUNIPER_PIDFILE_LINE in $(cat "${JUNIPER_PROJECT_PID_FILE}"); do
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Pidfile Line: \"${JUNIPER_PIDFILE_LINE}\""
    JUNIPER_APPLICATION_NAME="$(echo "${JUNIPER_PIDFILE_LINE}" | awk -F " " '{print $1;}')"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Application Name: \"${JUNIPER_APPLICATION_NAME}\""
    JUNIPER_APPLICATION_PID="$( echo "${JUNIPER_PIDFILE_LINE}" | awk -F " " '{print $2;}')"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Application PID: \"${JUNIPER_APPLICATION_PID}\""
    echo "[${SCRIPT_NAME}:${LINENO}] Stopping ${JUNIPER_APPLICATION_NAME} pid ${JUNIPER_APPLICATION_PID}"
    echo "[${SCRIPT_NAME}:${LINENO}] kill \"${KILL_SIGNAL}\" \"${JUNIPER_APPLICATION_PID}\""
    kill "${KILL_SIGNAL}" "${JUNIPER_APPLICATION_PID}"
    echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_ML_SLEEPYTIME} sec"
    sleep "${JUNIPER_ML_SLEEPYTIME}"
done
IFS="${OLD_IFS}"


###########################################################################################################################################################################################################
# Save Pids for Juniper Project service in juniper-ml pidfile
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] conda deactivate"
conda deactivate
cat "${JUNIPER_PROJECT_PID_FILE}"

