#!/usr/bin/env bash
###########################################################################################################################################################################################################
#
###########################################################################################################################################################################################################

###########################################################################################################################################################################################################
# Define Script env constants
###########################################################################################################################################################################################################
JUNIPER_PROJECT_DIR="${HOME}/Development/python/Juniper"
JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"

CONDA="/opt/miniconda3/etc/profile.d/conda.sh"
PYTHON="/opt/miniforge3/envs/JuniperCanopy/bin/python"

CASCOR_SERVICE_URL="http://localhost:8201" python main.py
LOGGING_TIMESTAMP="$(data +%F_%H%M)"


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


###########################################################################################################################################################################################################
# Initialize Conda prior to launching individual services
###########################################################################################################################################################################################################
source "${CONDA}"

###########################################################################################################################################################################################################
# Launch Juniper Data service in Background
###########################################################################################################################################################################################################
cd "${JUNIPER_DATA_DIR}"
conda activate "${JUNIPER_DATA_CONDA}"
nohup PYTHON_GIL=0 uvicorn juniper_data.api.app:app --host "${JUNIPER_DATA_HOST}" --port "${JUNIPER_DATA_PORT}" >"${JUNIPER_DATA_LOG}" 2>&1 &
JUNIPER_DATA_PID=$?


###########################################################################################################################################################################################################
# Launch Juniper Cascor service in Background
###########################################################################################################################################################################################################
cd "${JUNIPER_CASCOR_SRC_DIR}"
conda activate "${JUNIPER_CASCOR_CONDA}"
nohup JUNIPER_CASCOR_PORT="${JUNIPER_CASCOR_PORT}" "${PYTHON}" "${JUNIPER_CASCOR_MODULE}" >"${JUNIPER_CASCOR_LOG}" 2>&1 &
JUNIPER_CASCOR_PID=$?


###########################################################################################################################################################################################################
# Launch Juniper Canopy service in Background
###########################################################################################################################################################################################################
cd "${JUNIPER_CANOPY_SRC_DIR}"
conda activate "${JUNIPER_CANOPY_CONDA}"
nohup CASCOR_SERVICE_URL="${JUNIPER_CASCOR_URL}" "${PYTHON}" "${JUNIPER_CANOPY_MODULE}" >"${JUNIPER_CANOPY_LOG}" 2>&1 &
JUNIPER_CANOPY_PID=$?


###########################################################################################################################################################################################################
# Save Pids for Juniper Project service in juniper-ml pidfile
###########################################################################################################################################################################################################
conda deactivate

if [[ -f "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    cat /dev/null >"${JUNIPER_PROJECT_PID_FILE}"
else
    touch "${JUNIPER_PROJECT_PID_FILE}"
fi

echo "${JUNIPER_DATA_PID}" >>"juniper-data   ${JUNIPER_PROJECT_PID_FILE}"
echo "${JUNIPER_CASCOR_PID}" >>"juniper-cascor ${JUNIPER_PROJECT_PID_FILE}"
echo "${JUNIPER_CANOPY_PID}" >>"juniper-canopy ${JUNIPER_PROJECT_PID_FILE}"

cat "${JUNIPER_PROJECT_PID_FILE}"

