#!/usr/bin/env bash
###########################################################################################################################################################################################################
# juniper_chop_all.bash — Stop all Juniper microservices (host-level)
#
# Reads PIDs from the JuniperProject.pid file and sends graceful shutdown
# signals. Falls back to SIGKILL if processes don't terminate within the
# configurable timeout. Optionally cleans up orphaned worker processes.
#
# Environment overrides:
#   JUNIPER_PROJECT_DIR     — Root of Juniper ecosystem (default: ~/Development/python/Juniper)
#   SIGTERM_TIMEOUT         — Seconds to wait after SIGTERM before SIGKILL (default: 15)
#   KILL_WORKERS            — Set to "1" to also kill orphaned cascor worker processes (default: 0)
#   USE_SYSTEMD             — Set to "1" to use systemctl instead of PID files (default: 0)
#
# Flags:
#   --systemd               — Same as USE_SYSTEMD=1
###########################################################################################################################################################################################################
set -euo pipefail

###########################################################################################################################################################################################################
# Script metadata
###########################################################################################################################################################################################################
echo "Script Name, Called: ${BASH_SOURCE[0]}"
echo "Script Path, Full:   $(realpath "${BASH_SOURCE[0]}")"
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
echo "Script Path, Only:   ${SCRIPT_NAME}"
echo "[${SCRIPT_NAME}:${LINENO}] Beginning script run"


###########################################################################################################################################################################################################
# Define constants
###########################################################################################################################################################################################################
JUNIPER_PROJECT_DIR="${JUNIPER_PROJECT_DIR:-${HOME}/Development/python/Juniper}"
JUNIPER_ML_DIR="${JUNIPER_PROJECT_DIR}/juniper-ml"
JUNIPER_PROJECT_PID_FILENAME="JuniperProject.pid"
JUNIPER_PROJECT_PID_FILE="${JUNIPER_ML_DIR}/${JUNIPER_PROJECT_PID_FILENAME}"
echo "[${SCRIPT_NAME}:${LINENO}] JUNIPER_PROJECT_PID_FILE=\"${JUNIPER_PROJECT_PID_FILE}\""

SIGTERM_TIMEOUT="${SIGTERM_TIMEOUT:-15}"
KILL_WORKERS="${KILL_WORKERS:-0}"

# systemd mode: use systemctl --user instead of PID files
USE_SYSTEMD="${USE_SYSTEMD:-0}"
if [[ "${1:-}" == "--systemd" ]]; then
    USE_SYSTEMD=1
    shift
fi


###########################################################################################################################################################################################################
# systemd Mode (--systemd or USE_SYSTEMD=1)
###########################################################################################################################################################################################################
if [[ "${USE_SYSTEMD}" == "1" ]]; then
    echo "[${SCRIPT_NAME}:${LINENO}] === Stopping services via systemd ==="

    # Stop in reverse dependency order: canopy -> cascor -> data
    for svc in juniper-canopy juniper-cascor juniper-data; do
        echo "[${SCRIPT_NAME}:${LINENO}] Stopping ${svc}..."
        if systemctl --user stop "${svc}.service" 2>/dev/null; then
            echo "[${SCRIPT_NAME}:${LINENO}] ${svc} stopped."
        else
            echo "[${SCRIPT_NAME}:${LINENO}] ${svc} was not running or failed to stop."
        fi
    done

    echo ""
    echo "[${SCRIPT_NAME}:${LINENO}] === All Juniper services stopped via systemd ==="
    echo "[${SCRIPT_NAME}:${LINENO}] Ending script run"
    exit 0
fi


###########################################################################################################################################################################################################
# Utility Functions
###########################################################################################################################################################################################################

# Validate that a PID belongs to a Juniper process by checking /proc/<pid>/cmdline
validate_pid() {
    local pid="$1"
    local expected_name="$2"

    if [[ ! -d "/proc/${pid}" ]]; then
        echo "[${SCRIPT_NAME}:${LINENO}] WARNING: PID ${pid} (${expected_name}) is not running — already stopped or stale PID"
        return 1
    fi

    local cmdline
    cmdline="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null || echo "")"
    echo "[${SCRIPT_NAME}:${LINENO}] PID ${pid} cmdline: ${cmdline:0:200}"
    return 0
}

# Send SIGTERM then wait, escalate to SIGKILL if needed
graceful_stop() {
    local pid="$1"
    local service_name="$2"
    local timeout="${3:-${SIGTERM_TIMEOUT}}"

    echo "[${SCRIPT_NAME}:${LINENO}] Stopping ${service_name} (PID ${pid}) with SIGTERM (timeout: ${timeout}s)"

    # Send SIGTERM
    if ! kill -SIGTERM "${pid}" 2>/dev/null; then
        echo "[${SCRIPT_NAME}:${LINENO}] WARNING: Failed to send SIGTERM to PID ${pid} — process may have already exited"
        return 0
    fi

    # Wait for process to exit
    local elapsed=0
    while (( elapsed < timeout )); do
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "[${SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) stopped gracefully after ${elapsed}s"
            return 0
        fi
        sleep 1
        elapsed=$(( elapsed + 1 ))
    done

    # Process still alive — escalate to SIGKILL
    echo "[${SCRIPT_NAME}:${LINENO}] WARNING: ${service_name} (PID ${pid}) did not stop within ${timeout}s — sending SIGKILL"
    if kill -SIGKILL "${pid}" 2>/dev/null; then
        sleep 1
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "[${SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) killed with SIGKILL"
            return 0
        fi
        echo "[${SCRIPT_NAME}:${LINENO}] ERROR: ${service_name} (PID ${pid}) survived SIGKILL — manual intervention required"
        return 1
    else
        echo "[${SCRIPT_NAME}:${LINENO}] ${service_name} (PID ${pid}) exited during SIGKILL attempt"
        return 0
    fi
}


###########################################################################################################################################################################################################
# Check PID file exists
###########################################################################################################################################################################################################
if [[ ! -f "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    echo "[${SCRIPT_NAME}:${LINENO}] ERROR: PID file not found: ${JUNIPER_PROJECT_PID_FILE}"
    echo "[${SCRIPT_NAME}:${LINENO}] No services to stop. Was juniper_plant_all.bash run?"
    exit 1
fi

if [[ ! -s "${JUNIPER_PROJECT_PID_FILE}" ]]; then
    echo "[${SCRIPT_NAME}:${LINENO}] ERROR: PID file is empty: ${JUNIPER_PROJECT_PID_FILE}"
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
# Shutdown Juniper Project Services
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] === Stopping Juniper Services ==="
echo "[${SCRIPT_NAME}:${LINENO}] PID file contents:"
cat "${JUNIPER_PROJECT_PID_FILE}"
echo ""

STOP_FAILURES=0

while IFS= read -r JUNIPER_PIDFILE_LINE; do
    # Skip blank lines
    [[ -z "${JUNIPER_PIDFILE_LINE}" ]] && continue

    echo "[${SCRIPT_NAME}:${LINENO}] Juniper Pidfile Line: \"${JUNIPER_PIDFILE_LINE}\""
    # Format: "juniper-data:   12345" — split on colon, then trim whitespace from PID
    JUNIPER_APPLICATION_NAME="${JUNIPER_PIDFILE_LINE%%:*}"
    JUNIPER_APPLICATION_PID="$(echo "${JUNIPER_PIDFILE_LINE#*:}" | tr -d ' ')"

    # Validate PID is numeric
    if ! [[ "${JUNIPER_APPLICATION_PID}" =~ ^[0-9]+$ ]]; then
        echo "[${SCRIPT_NAME}:${LINENO}] WARNING: Invalid PID '${JUNIPER_APPLICATION_PID}' for ${JUNIPER_APPLICATION_NAME} — skipping"
        continue
    fi

    echo "[${SCRIPT_NAME}:${LINENO}] --- ${JUNIPER_APPLICATION_NAME} ---"

    if validate_pid "${JUNIPER_APPLICATION_PID}" "${JUNIPER_APPLICATION_NAME}"; then
        if ! graceful_stop "${JUNIPER_APPLICATION_PID}" "${JUNIPER_APPLICATION_NAME}"; then
            STOP_FAILURES=$(( STOP_FAILURES + 1 ))
        fi
    fi

    echo ""
done < "${JUNIPER_PROJECT_PID_FILE}"


###########################################################################################################################################################################################################
# Optionally clean up orphaned worker processes
###########################################################################################################################################################################################################
if [[ "${KILL_WORKERS}" == "1" ]]; then
    echo "[${SCRIPT_NAME}:${LINENO}] === Cleaning up orphaned worker processes ==="

    WORKER_PIDS=()
    while IFS= read -r line; do
        [[ -z "${line}" ]] && continue
        # pgrep -af outputs: PID CMDLINE
        worker_pid="$(echo "${line}" | awk '{print $1;}')"
        cmdline="$(echo "${line}" | cut -d' ' -f2-)"
        # Only match actual worker processes, not greps or log viewers
        if echo "${cmdline}" | grep -q "juniper.cascor.worker\|juniper_cascor_worker\|cascor.*worker"; then
            WORKER_PIDS+=("${worker_pid}")
            echo "[${SCRIPT_NAME}:${LINENO}] Found worker process: PID ${worker_pid} — ${cmdline:0:120}"
        fi
    done < <(pgrep -af "juniper.cascor" 2>/dev/null || true)

    if (( ${#WORKER_PIDS[@]} > 0 )); then
        echo "[${SCRIPT_NAME}:${LINENO}] Found ${#WORKER_PIDS[@]} worker process(es) to stop"
        for worker_pid in "${WORKER_PIDS[@]}"; do
            graceful_stop "${worker_pid}" "cascor-worker" 5
        done
    else
        echo "[${SCRIPT_NAME}:${LINENO}] No orphaned worker processes found"
    fi
fi


###########################################################################################################################################################################################################
# Clean up PID file and report results
###########################################################################################################################################################################################################
echo "[${SCRIPT_NAME}:${LINENO}] === Shutdown Summary ==="

if (( STOP_FAILURES > 0 )); then
    echo "[${SCRIPT_NAME}:${LINENO}] WARNING: ${STOP_FAILURES} service(s) failed to stop cleanly"
    echo "[${SCRIPT_NAME}:${LINENO}] PID file preserved at ${JUNIPER_PROJECT_PID_FILE} for investigation"
    exit 1
else
    echo "[${SCRIPT_NAME}:${LINENO}] All services stopped successfully"
    echo "[${SCRIPT_NAME}:${LINENO}] Clearing PID file"
    : > "${JUNIPER_PROJECT_PID_FILE}"
fi

echo "[${SCRIPT_NAME}:${LINENO}] Ending script run"
