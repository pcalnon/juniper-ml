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

JUNIPER_WORKER_SLEEPYTIME="2"
JUNIPER_CASCOR_WORKER_SEARCH_STRING="juniper-cascor"

JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILE=\"${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}\""

CONDA="/opt/miniforge3/etc/profile.d/conda.sh"
# PYTHON="/opt/miniforge3/envs/JuniperCanopy/bin/python"

# KILL_SIGNAL="-SIGHUP"
KILL_SIGNAL="-SIGTERM"
# KILL_SIGNAL="-KILL"


###########################################################################################################################################################################################################
# Initialize Conda prior to launching individual services
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] source \"${CONDA}\""
# shellcheck source=/dev/null
source "${CONDA}"

echo "[${SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_ML_CONDA}\""
conda activate "${JUNIPER_ML_CONDA}"

OLD_IFS="${IFS}"
IFS=$'\n'


#########################################################################################################################
# Check if PID file exists and has at least one PID
###########################################################################################################################################################################################################
if [[ ! -f "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    echo "[${SCRIPT_NAME}:${LINENO}] PID file not found: ${JUNIPER_PROJECT_PID_FILE}"
    exit 1
fi


###########################################################################################################################################################################################################
# Load Juniper Pid File Lines into array
###########################################################################################################################################################################################################
read -d '' -r -a JUNIPER_PIDS < "${JUNIPER_PROJECT_PID_FILE}"
echo -ne "[${SCRIPT_NAME}:${LINENO}] Juniper Project PID File Line Array:\n${JUNIPER_PIDS[*]}\n"

PID_COUNT="${#JUNIPER_PIDS[@]}"
echo "[${SCRIPT_NAME}:${LINENO}] Juniper Project PID Count: \"${PID_COUNT}\""

if (( PID_COUNT <= 0 )); then
    echo "[${SCRIPT_NAME}:${LINENO}] No PIDs found in \"${JUNIPER_PROJECT_PID_FILE}\""
    exit 1
fi


###########################################################################################################################################################################################################
# Shutdown Juniper Project Services:
#     Data service: running in Background
#     Cascor service: running in Background
#     Canopy service: running in Background
#
# Notes:
#     for JUNIPER_PIDFILE_LINE in "${JUNIPER_PIDS[@]}"; do
#     for JUNIPER_CANOPY_PIDFILE_LINE in $(cat "${JUNIPER_PROJECT_PID_FILE}" | awk -F " " '{print $2;}'); do
#     echo "for JUNIPER_PIDFILE_LINE in \$(cat \"${JUNIPER_PROJECT_PID_FILE}\"); do"
###########################################################################################################################################################################################################
for JUNIPER_PIDFILE_INDEX in "${!JUNIPER_PIDS[@]}"; do
    JUNIPER_PIDFILE_LINE="${JUNIPER_PIDS[${JUNIPER_PIDFILE_INDEX}]}"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Pidfile Line: \"${JUNIPER_PIDFILE_LINE}\""
    JUNIPER_APPLICATION_NAME="$(echo "${JUNIPER_PIDFILE_LINE}" | awk -F " " '{print $1;}')"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Application Name: \"${JUNIPER_APPLICATION_NAME}\""
    JUNIPER_APPLICATION_PID="$( echo "${JUNIPER_PIDFILE_LINE}" | awk -F " " '{print $2;}')"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Application PID: \"${JUNIPER_APPLICATION_PID}\""
    echo "[${SCRIPT_NAME}:${LINENO}] Stopping ${JUNIPER_APPLICATION_NAME} pid ${JUNIPER_APPLICATION_PID}"
    echo "[${SCRIPT_NAME}:${LINENO}] kill \"${KILL_SIGNAL}\" \"${JUNIPER_APPLICATION_PID}\""
    kill "${KILL_SIGNAL}" "${JUNIPER_APPLICATION_PID}"
    if (( ( JUNIPER_PIDFILE_INDEX + 1 ) < PID_COUNT )); then
        echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_ML_SLEEPYTIME} sec"
        sleep "${JUNIPER_ML_SLEEPYTIME}"
    fi
done


###########################################################################################################################################################################################################
# Find Juniper Cascor Workers
###########################################################################################################################################################################################################
mapfile -t JUNIPER_WORKER_PSAUX < <( ps aux | grep -v grep | grep "${JUNIPER_CASCOR_WORKER_SEARCH_STRING}" )
JUNIPER_WORKER_PID_COUNT="${#JUNIPER_WORKER_PSAUX[@]}"
echo "[${SCRIPT_NAME}:${LINENO}] Juniper Project Worker PID Count: \"${JUNIPER_WORKER_PID_COUNT}\""
if (( JUNIPER_WORKER_PID_COUNT <= 0 )); then
    echo "[${SCRIPT_NAME}:${LINENO}] No Juniper Cascor Workers found"
    exit 1
fi


###########################################################################################################################################################################################################
# Shutdown Juniper Cascor Workers once Cascor Service is shutdown:
#
# Notes:
#     for i in $(ps aux | grep -v grep | grep juniper-cascor | awk -F " " '{print $2;}'); do echo "${i}"; kill -SIGTERM ${i}; done
#     mapfile -t cascor_worker_pids < <( ps aux | grep -v grep | grep "python" );
#
###########################################################################################################################################################################################################
for JUNIPER_WORKER_PSAUX_INDEX in "${!JUNIPER_WORKER_PSAUX[@]}"; do
    JUNIPER_WORKER_PSAUX_LINE="${JUNIPER_WORKER_PSAUX[${JUNIPER_WORKER_PSAUX_INDEX}]}"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Worker Psaux Line: \"${JUNIPER_WORKER_PSAUX_LINE}\""
    JUNIPER_WORKER_PID="$( echo "${JUNIPER_WORKER_PSAUX_LINE}" | awk -F " " '{print $2;}')"
    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Worker PID: \"${JUNIPER_WORKER_PID}\""

    echo "[${SCRIPT_NAME}:${LINENO}] Stopping Juniper Cascor Worker, PID: ${JUNIPER_WORKER_PID}"
    echo "[${SCRIPT_NAME}:${LINENO}] kill \"${KILL_SIGNAL}\" \"${JUNIPER_WORKER_PID}\""
    kill "${KILL_SIGNAL}" "${JUNIPER_WORKER_PID}"

    if (( ( JUNIPER_WORKER_PSAUX_INDEX + 1 ) < JUNIPER_WORKER_PID_COUNT )); then
        echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_WORKER_SLEEPYTIME} sec"
        sleep "${JUNIPER_WORKER_SLEEPYTIME}"
    fi
done


###########################################################################################################################################################################################################
# Save Pids for Juniper Project service in juniper-ml pidfile
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] Restoring IFS=\"${OLD_IFS}\""
IFS="${OLD_IFS}"

echo "[${SCRIPT_NAME}:${LINENO}] conda deactivate"
conda deactivate

echo "[${SCRIPT_NAME}:${LINENO}] cat \"${JUNIPER_PROJECT_PID_FILE}\""
cat "${JUNIPER_PROJECT_PID_FILE}"

echo "[${SCRIPT_NAME}:${LINENO}] Ending script run"

