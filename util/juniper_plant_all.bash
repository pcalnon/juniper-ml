#!/usr/bin/env bash
###########################################################################################################################################################################################################
# juniper_plant_all.bash — Start all Juniper microservices (host-level)
#
# Starts juniper-data, juniper-cascor, juniper-canopy, and juniper-cascor-worker
# sequentially with health check verification after each service (where
# applicable). Writes PIDs to a pidfile for use by juniper_chop_all.bash.
#
# Environment overrides:
#   JUNIPER_PROJECT_DIR     — Root of Juniper ecosystem (default: ~/Development/python/Juniper)
#   JUNIPER_CONDA_DIR       — Miniforge/conda install dir (default: /opt/miniforge3)
#   JUNIPER_DATA_PORT       — juniper-data listen port (default: 8100)
#   JUNIPER_CASCOR_PORT     — juniper-cascor listen port (default: 8201)
#   JUNIPER_CANOPY_PORT     — juniper-canopy listen port (default: 8050)
#   HEALTH_CHECK_TIMEOUT    — Max seconds to wait for each service health (default: 60)
#   HEALTH_CHECK_INTERVAL   — Seconds between health polls (default: 2)
#   USE_SYSTEMD             — Set to "1" to use systemctl instead of nohup (default: 0)
#
# Flags:
#   --systemd               — Same as USE_SYSTEMD=1
###########################################################################################################################################################################################################
set -euo pipefail


###########################################################################################################################################################################################################
# Define global Script and Directory constants
###########################################################################################################################################################################################################
JUNIPER_SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Beginning script run"

JUNIPER_SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
JUNIPER_SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Name:      ${JUNIPER_SCRIPT_NAME}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Path:      ${JUNIPER_SCRIPT_PATH}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Script Dir:       ${JUNIPER_SCRIPT_DIR}"


###########################################################################################################################################################################################################
# Define global Project and Directory constants
###########################################################################################################################################################################################################
JUNIPER_UTIL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
JUNIPER_APPLICATION_DIR="$(dirname "${JUNIPER_UTIL_DIR}")"
JUNIPER_PROJECT_DIR="$(dirname "${JUNIPER_APPLICATION_DIR}")"

JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_DATA_DIR="${JUNIPER_PROJECT_DIR}/juniper-data"
JUNIPER_CASCOR_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor"
JUNIPER_CANOPY_DIR="${JUNIPER_PROJECT_DIR}/juniper-canopy"
JUNIPER_WORKER_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor-worker"


###########################################################################################################################################################################################################
# Define Global Project Constants
###########################################################################################################################################################################################################
JUNIPER_CONDA_DIR="${JUNIPER_CONDA_DIR:-/opt/miniforge3}"
CONDA="${JUNIPER_CONDA_DIR}/etc/profile.d/conda.sh"

HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-2}"

JUNIPER_LOGGING_TIMESTAMP="$(date +%F_%H%M)"

JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILE=\"${JUNIPER_PROJECT_PID_FILE}\""

# systemd mode: use systemctl --user instead of nohup/PID files
USE_SYSTEMD="${USE_SYSTEMD:-0}"
if [[ "${1:-}" == "--systemd" ]]; then
    USE_SYSTEMD=1
    shift
fi

# Track started PIDs for cleanup on failure
STARTED_PIDS=()


###########################################################################################################################################################################################################
# Juniper Data Service Constants
###########################################################################################################################################################################################################
JUNIPER_DATA_DIR="${JUNIPER_PROJECT_DIR}/juniper-data"
JUNIPER_DATA_LOG_DIR="${JUNIPER_DATA_DIR}/logs"
JUNIPER_DATA_LOGNAME="juniper-data_${JUNIPER_LOGGING_TIMESTAMP}.log"
JUNIPER_DATA_LOG="${JUNIPER_DATA_LOG_DIR}/${JUNIPER_DATA_LOGNAME}"
JUNIPER_DATA_HOST="0.0.0.0"
JUNIPER_DATA_PORT="${JUNIPER_DATA_PORT:-8100}"
JUNIPER_DATA_CONDA="JuniperData"


###########################################################################################################################################################################################################
# Juniper Cascor Service Constants
###########################################################################################################################################################################################################
JUNIPER_CASCOR_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor"
JUNIPER_CASCOR_SRC_DIR="${JUNIPER_CASCOR_DIR}/src"
JUNIPER_CASCOR_LOG_DIR="${JUNIPER_CASCOR_DIR}/logs"
JUNIPER_CASCOR_LOGNAME="juniper-cascor_${JUNIPER_LOGGING_TIMESTAMP}.log"
JUNIPER_CASCOR_LOG="${JUNIPER_CASCOR_LOG_DIR}/${JUNIPER_CASCOR_LOGNAME}"
JUNIPER_CASCOR_MODULE="server.py"
JUNIPER_CASCOR_HOST="localhost"
JUNIPER_CASCOR_PORT="${JUNIPER_CASCOR_PORT:-8201}"
JUNIPER_CASCOR_URL="http://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}"
JUNIPER_CASCOR_CONDA="JuniperCascor"
JUNIPER_CASCOR_PYTHON="${JUNIPER_CONDA_DIR}/envs/${JUNIPER_CASCOR_CONDA}/bin/python"


###########################################################################################################################################################################################################
# Juniper Canopy Service Constants
###########################################################################################################################################################################################################
JUNIPER_CANOPY_DIR="${JUNIPER_PROJECT_DIR}/juniper-canopy"
JUNIPER_CANOPY_SRC_DIR="${JUNIPER_CANOPY_DIR}/src"
JUNIPER_CANOPY_LOG_DIR="${JUNIPER_CANOPY_DIR}/logs"
JUNIPER_CANOPY_LOGNAME="juniper-canopy_${JUNIPER_LOGGING_TIMESTAMP}.log"
JUNIPER_CANOPY_LOG="${JUNIPER_CANOPY_LOG_DIR}/${JUNIPER_CANOPY_LOGNAME}"
JUNIPER_CANOPY_MODULE="main.py"
JUNIPER_CANOPY_PORT="${JUNIPER_CANOPY_PORT:-8050}"
JUNIPER_CANOPY_CONDA="JuniperCanopy"
JUNIPER_CANOPY_PYTHON="${JUNIPER_CONDA_DIR}/envs/${JUNIPER_CANOPY_CONDA}/bin/python"


###########################################################################################################################################################################################################
# Juniper CasCor Worker Service Constants
###########################################################################################################################################################################################################
JUNIPER_WORKER_DIR="${JUNIPER_PROJECT_DIR}/juniper-cascor-worker"
JUNIPER_WORKER_LOG_DIR="${JUNIPER_WORKER_DIR}/logs"
JUNIPER_WORKER_LOGNAME="juniper-cascor-worker_${JUNIPER_LOGGING_TIMESTAMP}.log"
JUNIPER_WORKER_LOG="${JUNIPER_WORKER_LOG_DIR}/${JUNIPER_WORKER_LOGNAME}"
JUNIPER_WORKER_CONDA="JuniperCascor"
JUNIPER_WORKER_BIN="${JUNIPER_CONDA_DIR}/envs/${JUNIPER_WORKER_CONDA}/bin/juniper-cascor-worker"


###########################################################################################################################################################################################################
# Utility Functions
###########################################################################################################################################################################################################

# Check if a port is available (not in use)
function check_port_available() {
    local port="$1"
    local service_name="$2"
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Port ${port} is already in use (needed by ${service_name})"
        ss -tlnp 2>/dev/null | grep ":${port} "
        return 1
    fi
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Port ${port} is available for ${service_name}"
    return 0
}

# Validate that a conda environment exists
function validate_conda_env() {
    local env_name="$1"
    local env_path="${JUNIPER_CONDA_DIR}/envs/${env_name}"
    if [[ ! -d "${env_path}" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Conda environment '${env_name}' not found at ${env_path}"
        return 1
    fi
    local python_bin="${env_path}/bin/python"
    if [[ ! -x "${python_bin}" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Python binary not found or not executable at ${python_bin}"
        return 1
    fi
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Conda environment '${env_name}' validated at ${env_path}"
    return 0
}

# Ensure a directory exists
function ensure_dir() {
    local dir="$1"
    if [[ ! -d "${dir}" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Creating directory: ${dir}"
        mkdir -p "${dir}"
    fi
}

# Wait for a service to become healthy by polling its health endpoint
function wait_for_health() {
    local service_name="$1"
    local health_url="$2"
    local timeout="${3:-${HEALTH_CHECK_TIMEOUT}}"
    local interval="${4:-${HEALTH_CHECK_INTERVAL}}"
    local elapsed=0

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Waiting for ${service_name} health at ${health_url} (timeout: ${timeout}s)"

    while (( elapsed < timeout )); do
        if curl -sf --max-time 5 "${health_url}" >/dev/null 2>&1; then
            echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ${service_name} is healthy (took ${elapsed}s)"
            return 0
        fi
        sleep "${interval}"
        elapsed=$(( elapsed + interval ))
    done

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: ${service_name} failed to become healthy within ${timeout}s"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Check log for details"
    return 1
}

# Clean up all started services on failure
function cleanup_on_failure() {
    # Disable traps to prevent recursion
    trap - ERR EXIT
    set +e

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] FAILURE: Cleaning up started Juniper Project services..."
    set +u
    if (( ${#STARTED_PIDS[@]} > 0 )); then
        for pid in "${STARTED_PIDS[@]}"; do
            if kill -0 "${pid}" 2>/dev/null; then
                echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Sending SIGTERM to PID ${pid}"
                kill -SIGTERM "${pid}" 2>/dev/null || true
            fi
        done
        sleep 3
        for pid in "${STARTED_PIDS[@]}"; do
            if kill -0 "${pid}" 2>/dev/null; then
                echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Sending SIGKILL to PID ${pid}"
                kill -SIGKILL "${pid}" 2>/dev/null || true
            fi
        done
    fi
    rm -f "${JUNIPER_PROJECT_PID_FILE}"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Cleanup complete. Juniper Project Startup aborted."
    exit 1
}

trap cleanup_on_failure ERR


###########################################################################################################################################################################################################
# systemd Mode (--systemd or USE_SYSTEMD=1)
###########################################################################################################################################################################################################
if [[ "${USE_SYSTEMD}" == "1" ]]; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Starting services via systemd ==="

    # Validate curl is available for health checks
    if ! command -v curl >/dev/null 2>&1; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: 'curl' not found in PATH (needed for health checks)"
        exit 1
    fi

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Starting juniper-data..."
    systemctl --user start juniper-data.service
    wait_for_health "juniper-data" "http://localhost:${JUNIPER_DATA_PORT}/v1/health"

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Starting juniper-cascor..."
    systemctl --user start juniper-cascor.service
    wait_for_health "juniper-cascor" "http://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}/v1/health"

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Starting juniper-canopy..."
    systemctl --user start juniper-canopy.service
    wait_for_health "juniper-canopy" "http://localhost:${JUNIPER_CANOPY_PORT}/v1/health"

    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Starting juniper-cascor-worker..."
    systemctl --user start juniper-cascor-worker.service
    # Worker has no HTTP endpoint — verify process started via systemd
    sleep 2
    if systemctl --user is-active juniper-cascor-worker.service >/dev/null 2>&1; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] juniper-cascor-worker is active"
    else
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: juniper-cascor-worker failed to start"
        systemctl --user status juniper-cascor-worker.service --no-pager || true
    fi

    # Disable ERR trap since startup succeeded
    trap - ERR

    echo ""
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === All Juniper services started via systemd ==="
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   Use 'systemctl --user status juniper-{data,cascor,canopy,cascor-worker}' to check status"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   Use 'journalctl --user -u juniper-{data,cascor,canopy,cascor-worker} -f' for logs"
    exit 0
fi


###########################################################################################################################################################################################################
# Pre-flight Checks
###########################################################################################################################################################################################################
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Pre-flight Checks ==="

# Validate required external commands
for cmd in curl ss uvicorn; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Required command '${cmd}' not found in PATH"
        exit 1
    fi
done

# Validate conda installation
if [[ ! -f "${CONDA}" ]]; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Conda not found at ${CONDA}"
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Set JUNIPER_CONDA_DIR to your conda installation directory"
    exit 1
fi

# Validate all conda environments
validate_conda_env "${JUNIPER_DATA_CONDA}"
validate_conda_env "${JUNIPER_CASCOR_CONDA}"
validate_conda_env "${JUNIPER_CANOPY_CONDA}"

# Check all required ports are available
check_port_available "${JUNIPER_DATA_PORT}" "juniper-data"
check_port_available "${JUNIPER_CASCOR_PORT}" "juniper-cascor"
check_port_available "${JUNIPER_CANOPY_PORT}" "juniper-canopy"

# Ensure log directories exist
ensure_dir "${JUNIPER_DATA_LOG_DIR}"
ensure_dir "${JUNIPER_CASCOR_LOG_DIR}"
ensure_dir "${JUNIPER_CANOPY_LOG_DIR}"

# Validate project directories exist
for dir in "${JUNIPER_DATA_DIR}" "${JUNIPER_CASCOR_SRC_DIR}" "${JUNIPER_CANOPY_SRC_DIR}"; do
    if [[ ! -d "${dir}" ]]; then
        echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] ERROR: Required directory not found: ${dir}"
        exit 1
    fi
done

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Pre-flight Checks Passed ==="


###########################################################################################################################################################################################################
# Initialize Conda prior to launching individual services
###########################################################################################################################################################################################################
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] source \"${CONDA}\""
# shellcheck source=/dev/null
source "${CONDA}"

# Conda activation wrapper: conda's activation scripts (e.g.,
# activate-binutils_linux-64.sh in JuniperCanopy) reference variables
# like ADDR2LINE that may not be set, causing failures under set -u.
# This wrapper temporarily disables nounset for the activation call.
safe_conda_activate() {
    local env_name="$1"
    set +u
    conda activate "${env_name}"
    set -u
}


###########################################################################################################################################################################################################
# Launch Juniper Data service in Background
###########################################################################################################################################################################################################
echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Starting juniper-data ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_DATA_DIR}\""
cd "${JUNIPER_DATA_DIR}" || exit 1
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_DATA_CONDA}\""
safe_conda_activate "${JUNIPER_DATA_CONDA}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] PYTHON_GIL=0 nohup uvicorn juniper_data.api.app:app --host \"${JUNIPER_DATA_HOST}\" --port \"${JUNIPER_DATA_PORT}\" >\"${JUNIPER_DATA_LOG}\" 2>&1 &"
PYTHON_GIL=0 nohup uvicorn juniper_data.api.app:app --host "${JUNIPER_DATA_HOST}" --port "${JUNIPER_DATA_PORT}" >"${JUNIPER_DATA_LOG}" 2>&1 &
JUNIPER_DATA_PID=$!
STARTED_PIDS+=("${JUNIPER_DATA_PID}")
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_DATA_PID=${JUNIPER_DATA_PID}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Log: ${JUNIPER_DATA_LOG}"
wait_for_health "juniper-data" "http://localhost:${JUNIPER_DATA_PORT}/v1/health"


###########################################################################################################################################################################################################
# Launch Juniper Cascor service in Background
###########################################################################################################################################################################################################
echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Starting juniper-cascor ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_CASCOR_SRC_DIR}\""
cd "${JUNIPER_CASCOR_SRC_DIR}" || exit 1
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_CASCOR_CONDA}\""
safe_conda_activate "${JUNIPER_CASCOR_CONDA}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CASCOR_PORT=\"${JUNIPER_CASCOR_PORT}\" nohup \"${JUNIPER_CASCOR_PYTHON}\" \"${JUNIPER_CASCOR_MODULE}\" >\"${JUNIPER_CASCOR_LOG}\" 2>&1 &"
JUNIPER_CASCOR_PORT="${JUNIPER_CASCOR_PORT}" nohup "${JUNIPER_CASCOR_PYTHON}" "${JUNIPER_CASCOR_MODULE}" >"${JUNIPER_CASCOR_LOG}" 2>&1 &
JUNIPER_CASCOR_PID=$!
STARTED_PIDS+=("${JUNIPER_CASCOR_PID}")
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CASCOR_PID=\"${JUNIPER_CASCOR_PID}\""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Log: ${JUNIPER_CASCOR_LOG}"
wait_for_health "juniper-cascor" "http://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}/v1/health"


###########################################################################################################################################################################################################
# Launch Juniper Canopy service in Background
###########################################################################################################################################################################################################
echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Starting juniper-canopy ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] cd \"${JUNIPER_CANOPY_SRC_DIR}\""
cd "${JUNIPER_CANOPY_SRC_DIR}" || exit 1
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_CANOPY_CONDA}\""
safe_conda_activate "${JUNIPER_CANOPY_CONDA}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] CASCOR_SERVICE_URL=\"${JUNIPER_CASCOR_URL}\" nohup \"${JUNIPER_CANOPY_PYTHON}\" \"${JUNIPER_CANOPY_MODULE}\" >\"${JUNIPER_CANOPY_LOG}\" 2>&1 &"
CASCOR_SERVICE_URL="${JUNIPER_CASCOR_URL}" nohup "${JUNIPER_CANOPY_PYTHON}" "${JUNIPER_CANOPY_MODULE}" >"${JUNIPER_CANOPY_LOG}" 2>&1 &
JUNIPER_CANOPY_PID=$!
STARTED_PIDS+=("${JUNIPER_CANOPY_PID}")
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_CANOPY_PID=${JUNIPER_CANOPY_PID}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Log: ${JUNIPER_CANOPY_LOG}"
wait_for_health "juniper-canopy" "http://localhost:${JUNIPER_CANOPY_PORT}/v1/health"


###########################################################################################################################################################################################################
# Launch Juniper CasCor Worker in Background
###########################################################################################################################################################################################################
echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Starting juniper-cascor-worker ==="
ensure_dir "${JUNIPER_WORKER_LOG_DIR}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] conda activate \"${JUNIPER_WORKER_CONDA}\""
safe_conda_activate "${JUNIPER_WORKER_CONDA}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] nohup \"${JUNIPER_WORKER_BIN}\" >\"${JUNIPER_WORKER_LOG}\" 2>&1 &"
nohup "${JUNIPER_WORKER_BIN}" >"${JUNIPER_WORKER_LOG}" 2>&1 &
JUNIPER_WORKER_PID=$!
STARTED_PIDS+=("${JUNIPER_WORKER_PID}")
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] JUNIPER_WORKER_PID=${JUNIPER_WORKER_PID}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] Log: ${JUNIPER_WORKER_LOG}"
# Worker has no HTTP health endpoint — verify process started
sleep 2
if kill -0 "${JUNIPER_WORKER_PID}" 2>/dev/null; then
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] juniper-cascor-worker process started (PID ${JUNIPER_WORKER_PID})"
else
    echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] WARNING: juniper-cascor-worker process exited immediately — check ${JUNIPER_WORKER_LOG}"
fi


###########################################################################################################################################################################################################
# Save PIDs for Juniper Project services to pidfile
###########################################################################################################################################################################################################
echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === Writing PID File ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] conda deactivate"
set +u
conda deactivate
set -u

# Disable ERR trap since startup succeeded
trap - ERR

: > "${JUNIPER_PROJECT_PID_FILE}"
{
    echo "juniper-data:           ${JUNIPER_DATA_PID}"
    echo "juniper-cascor:         ${JUNIPER_CASCOR_PID}"
    echo "juniper-canopy:         ${JUNIPER_CANOPY_PID}"
    echo "juniper-cascor-worker:  ${JUNIPER_WORKER_PID}"
} >> "${JUNIPER_PROJECT_PID_FILE}"

echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] PID file written to ${JUNIPER_PROJECT_PID_FILE}:"
cat "${JUNIPER_PROJECT_PID_FILE}"

echo ""
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}] === All Juniper services started successfully ==="
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   juniper-data          : PID ${JUNIPER_DATA_PID}   @ http://localhost:${JUNIPER_DATA_PORT}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   juniper-cascor        : PID ${JUNIPER_CASCOR_PID} @ http://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   juniper-canopy        : PID ${JUNIPER_CANOPY_PID} @ http://localhost:${JUNIPER_CANOPY_PORT}"
echo "[${JUNIPER_SCRIPT_NAME}:${LINENO}]   juniper-cascor-worker : PID ${JUNIPER_WORKER_PID} (WebSocket client)"
