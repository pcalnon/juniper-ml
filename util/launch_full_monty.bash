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

JUNIPER_PROJECT_DIR="${HOME}/Development/python/Juniper"
JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"

CONDA="/opt/miniforge3/etc/profile.d/conda.sh"
PYTHON="/opt/miniforge3/envs/JuniperCanopy/bin/python"

LOGGING_TIMESTAMP="$(date +%F_%H%M)"


###########################################################################################################################################################################################################
# Juniper Data Service Constants
###########################################################################################################################################################################################################
JUNIPER_DATA_DIR="${JUNIPER_PROJECT_DIR}/juniper-data"
JUNIPER_DATA_LOG_DIR="${JUNIPER_DATA_DIR}/logs"
JUNIPER_DATA_LOGNAME="juniper-data_${LOGGING_TIMESTAMP}.log"
JUNIPER_DATA_LOG="${JUNIPER_DATA_LOG_DIR}/${JUNIPER_DATA_LOGNAME}"
JUNIPER_DATA_HOST="0.0.0.0"
JUNIPER_DATA_PORT="8100"
JUNIPER_DATA_CONDA="JuniperData"
JUNIPER_DATA_SLEEPYTIME="10"


###########################################################################################################################################################################################################
# Juniper Cascor Service Constants
###########################################################################################################################################################################################################
JUNIPER_CASCOR_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor"
JUNIPER_CASCOR_SRC_DIR="${JUNIPER_CASCOR_DIR}/src"
JUNIPER_CASCOR_LOG_DIR="${JUNIPER_CASCOR_DIR}/logs"
JUNIPER_CASCOR_LOGNAME="juniper-cascor_${LOGGING_TIMESTAMP}.log"
JUNIPER_CASCOR_LOG="${JUNIPER_CASCOR_LOG_DIR}/${JUNIPER_CASCOR_LOGNAME}"
JUNIPER_CASCOR_MODULE="server.py"
JUNIPER_CASCOR_HOST="localhost"
JUNIPER_CASCOR_PORT="8201"
JUNIPER_CASCOR_URL="http://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}"
JUNIPER_CASCOR_CONDA="JuniperCascor"
JUNIPER_CASCOR_SLEEPYTIME="30"


###########################################################################################################################################################################################################
# Juniper Canopy Service Constants
###########################################################################################################################################################################################################
JUNIPER_CANOPY_DIR="${JUNIPER_PROJECT_DIR}/juniper-canopy"
JUNIPER_CANOPY_SRC_DIR="${JUNIPER_CANOPY_DIR}/src"
JUNIPER_CANOPY_LOG_DIR="${JUNIPER_CANOPY_DIR}/logs"
JUNIPER_CANOPY_LOGNAME="juniper-canopy_${LOGGING_TIMESTAMP}.log"
JUNIPER_CANOPY_LOG="${JUNIPER_CANOPY_LOG_DIR}/${JUNIPER_CANOPY_LOGNAME}"
JUNIPER_CANOPY_MODULE="main.py"
JUNIPER_CANOPY_CONDA="JuniperCanopy"
JUNIPER_CANOPY_SLEEPYTIME="10"


###########################################################################################################################################################################################################
# Initialize Conda prior to launching individual services
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] source \"${CONDA}\""
source "${CONDA}"


###########################################################################################################################################################################################################
# Launch Juniper Data service in Background
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_DATA_DIR}\""
cd "${JUNIPER_DATA_DIR}"
echo "[${SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_DATA_CONDA}\""
conda activate "${JUNIPER_DATA_CONDA}"
echo "[${SCRIPT_NAME}:${LINENO}] PYTHON_GIL=0 nohup uvicorn juniper_data.api.app:app --host \"${JUNIPER_DATA_HOST}\" --port \"${JUNIPER_DATA_PORT}\" >\"${JUNIPER_DATA_LOG}\" 2>&1 &"
PYTHON_GIL=0 nohup uvicorn juniper_data.api.app:app --host "${JUNIPER_DATA_HOST}" --port "${JUNIPER_DATA_PORT}" >"${JUNIPER_DATA_LOG}" 2>&1 &
JUNIPER_DATA_PID=$!
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_DATA_PID=${JUNIPER_DATA_PID}"
echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_DATA_SLEEPYTIME} sec"
sleep "${JUNIPER_DATA_SLEEPYTIME}"


###########################################################################################################################################################################################################
# Launch Juniper Cascor service in Background
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_CASCOR_SRC_DIR}\""
cd "${JUNIPER_CASCOR_SRC_DIR}"
echo "[${SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_CASCOR_CONDA}\""
conda activate "${JUNIPER_CASCOR_CONDA}"
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_CASCOR_PORT=\"${JUNIPER_CASCOR_PORT}\" nohup \"${PYTHON}\" \"${JUNIPER_CASCOR_MODULE}\" >\"${JUNIPER_CASCOR_LOG}\" 2>&1 &"
JUNIPER_CASCOR_PORT="${JUNIPER_CASCOR_PORT}" nohup "${PYTHON}" "${JUNIPER_CASCOR_MODULE}" >"${JUNIPER_CASCOR_LOG}" 2>&1 &
JUNIPER_CASCOR_PID=$!
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_CASCOR_PID=\"${JUNIPER_CASCOR_PID}\""
echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_CASCOR_SLEEPYTIME} sec"
sleep "${JUNIPER_CASCOR_SLEEPYTIME}"


###########################################################################################################################################################################################################
# Launch Juniper Canopy service in Background
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_CANOPY_SRC_DIR}\""
cd "${JUNIPER_CANOPY_SRC_DIR}"
echo "[${SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_CANOPY_CONDA}\""
conda activate "${JUNIPER_CANOPY_CONDA}"

echo "[${SCRIPT_NAME}:${LINENO}] CASCOR_SERVICE_URL=\"${JUNIPER_CASCOR_URL}\" nohup \"${PYTHON}\" \"${JUNIPER_CANOPY_MODULE}\" >\"${JUNIPER_CANOPY_LOG}\" 2>&1 &"

# /opt/miniforge3/envs/JuniperCanopy/bin/python: can't open file '/home/pcalnon/Development/python/Juniper/juniper-ml/main.py': [Errno 2] No such file or directory
CASCOR_SERVICE_URL="${JUNIPER_CASCOR_URL}" nohup "${PYTHON}" "${JUNIPER_CANOPY_MODULE}" >"${JUNIPER_CANOPY_LOG}" 2>&1 &

JUNIPER_CANOPY_PID=$!

echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_CANOPY_PID=${JUNIPER_CANOPY_PID}"
echo "[${SCRIPT_NAME}:${LINENO}] Sleeping for ${JUNIPER_CANOPY_SLEEPYTIME} sec"
sleep "${JUNIPER_CANOPY_SLEEPYTIME}"


###########################################################################################################################################################################################################
# Save Pids for Juniper Project service in juniper-ml pidfile
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] conda deactivate"
conda deactivate

if [[ -f "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    cat /dev/null >"${JUNIPER_PROJECT_PID_FILE}"
else
    touch "${JUNIPER_PROJECT_PID_FILE}"
fi

echo "juniper-data:   ${JUNIPER_DATA_PID}"   >> ${JUNIPER_PROJECT_PID_FILE}
echo "juniper-cascor: ${JUNIPER_CASCOR_PID}" >> ${JUNIPER_PROJECT_PID_FILE}
echo "juniper-canopy: ${JUNIPER_CANOPY_PID}" >> ${JUNIPER_PROJECT_PID_FILE}

cat "${JUNIPER_PROJECT_PID_FILE}"

