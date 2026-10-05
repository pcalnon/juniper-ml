#!/usr/bin/env bash
###########################################################################################################################################################################################################
# experiment_stack.bash — per-run experiment stack launcher (CLI experimentation program, Wave 2.1)
#
# Brings up a THROWAWAY, PER-RUN juniper-data instance plus juniper-cascor and/or
# juniper-recurrence on ports drawn from the dedicated experiment ranges
# (data 8110-8139 / cascor 8230-8259 / recurrence 8260-8289), with every artifact
# confined to a per-run RUN_DIR, so concurrent experiment runs never collide with each
# other nor with the operator's on-host stack (8100 / 8200 / 8201 / 8210 / 8050).
#
# This script ENCODES the launcher contract designed in juniper-ml
# notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md
# §6.2 (behaviour table), §6.1 (canonical launch recipes), §6.4 (RUN_DIR layout),
# §7.2/§7.3 (Grafana bridge: target file + socat relay) and §9.3 (port ranges); that plan
# is the primary reference and this helper is deliberately mechanical. Binding preflight
# evidence lives in
# notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md.
#
# Hard invariants (plan §9.1/§9.2):
#   * JuniperProject.pid is NEVER read or written — that file belongs to
#     juniper_plant_all.bash / juniper_chop_all.bash (hazard H-10).
#   * No repo .env is ever created, edited, or deleted; all per-run config is process env
#     (hazard H-3 — cascor loads .env from CWD).
#   * juniper-canopy is never started, and 8050 / 8051 are never used.
#   * Teardown kills ONLY pids this run recorded (or the listener on a port this run
#     recorded), and never deletes artifacts/.
#
# Flags (exactly one action, plus options):
#   --up                 Allocate ports, launch data -> cascor -> recurrence (health-gated).
#                        Mid-bring-up / grafana-bridge failure tears the partial run down
#                        via teardown_run (no orphan listeners on the experiment ranges).
#                        Requires at least one app selector.
#     --cascor           Include juniper-cascor in the run (cascor arm = data + cascor).
#     --recurrence       Include juniper-recurrence (recurrence arm = data + recurrence).
#     --shared-data URL  Reuse an existing juniper-data at URL instead of launching one.
#     --config PATH      Stage an experiment YAML into the RUN_DIR (see CONFIG below).
#     --experiment NAME  Value for the Prometheus 'experiment' target label (§7.2).
#     --grafana-bridge   OPT-IN: start the socat relays + write the Prometheus target file.
#     --skip-env-preflight
#                        With --recurrence: still run the recurrence env preflight (see
#                        RECURRENCE ENV PREFLIGHT below), but report its findings as WARNINGs
#                        instead of refusing the leg. Emergencies only.
#   --down RUN_ID        Tear the run down (pidfile-first), release its port locks,
#                        remove its relays + target file. Keeps artifacts/.
#     --all-mine         With --down: tear down EVERY run under the run root.
#   --status [RUN_ID]    Probe a run (or list every run) — health, pids, scrape state.
#   --dry-run            PRINT every command with ports/paths expanded; create nothing,
#                        start nothing, kill nothing, write no target file, take no locks.
#   --help,-h            Print usage and exit 0.
#
# Environment overrides:
#   JUNIPER_EXP_RUN_ROOT        — run root (default: ${HOME}/.local/state/juniper-experiments)
#   JUNIPER_EXP_LOCK_ROOT       — port lockdir root (default: ${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments)
#   JUNIPER_EXP_PROJECT_DIR     — ecosystem root (default: derived from this script's
#                                 location, i.e. /home/pcalnon/Development/python/Juniper
#                                 for the canonical checkout; SET THIS when running the
#                                 launcher from a git worktree, where the derivation lands
#                                 inside worktrees/ instead)
#   JUNIPER_EXP_DEPLOY_DIR      — juniper-deploy checkout hosting prometheus/targets/ (F-3;
#                                 default: <ecosystem root>/juniper-deploy)
#   JUNIPER_EXP_CASCOR_SRC_DIR  — juniper-cascor src/ to launch uvicorn from (default:
#                                 <ecosystem root>/juniper-cascor/src). SET THIS to pin a
#                                 campaign to a WORKTREE instead of freezing the primary
#                                 checkout for the campaign's whole life. Pair it with
#                                 JUNIPER_EXP_PROJECT_DIR so run_suite resolves sibling
#                                 base_config paths out of the same tree, or the run gets
#                                 pinned CODE against the primary's CONFIG.
#   JUNIPER_EXP_CONDA_DIR       — miniforge/conda dir (default: /opt/miniforge3)
#   JUNIPER_EXP_DATA_CONDA      — juniper-data env       (default: JuniperData)
#   JUNIPER_EXP_CASCOR_CONDA    — juniper-cascor env     (default: JuniperCascor1)
#   JUNIPER_EXP_RECURRENCE_CONDA— juniper-recurrence env (default: JuniperCascor1)
#   JUNIPER_EXP_HEALTH_TIMEOUT  — per-service health wait, seconds (default: 90 — F-8 sizes
#                                 this for a COLD start; recurrence needs 10-15 s of import)
#   JUNIPER_EXP_KILL_TIMEOUT    — SIGTERM -> SIGKILL grace, seconds (default: 10)
#   JUNIPER_EXP_CONDA_ACTIVATE  — 1 to `conda activate` before launching instead of using the
#                                 env's bin/ directly (see CONDA below)
#   JUNIPER_EXP_SKIP_ENV_PREFLIGHT
#                               — 1 = --skip-env-preflight, for a caller that cannot pass the flag
#                                 (run_suite.py invokes --up with a fixed argv)
#
# CONDA: services are launched through direct env-bin paths
# (${JUNIPER_EXP_CONDA_DIR}/envs/<env>/bin/...), which is what the P0 evidence run used and
# is equivalent here because neither JuniperCascor1 nor JuniperData ships
# etc/conda/activate.d/ hooks (verified 2026-07-30). Set JUNIPER_EXP_CONDA_ACTIVATE=1 to go
# through `conda activate` instead, for an env that later grows activation hooks.
#
# CONFIG: --config PATH copies the YAML verbatim to $RUN_DIR/config/experiment.yaml (§6.4)
# and exports JUNIPER_CASCOR_CONFIG_FILE / JUNIPER_RECURRENCE_CONFIG_FILE at it (§6.2). The
# app-side YAML settings sources are LIVE (Wave 3.1 cascor#486 / Wave 3.3 recurrence#97):
# each app projects the file's service: block above env (§5.1). Neither launch passes an app
# --config flag — the env var is the threading mechanism, so the launcher CLI keeps owning
# the bind (§5.2).
#
# RECURRENCE ENV PREFLIGHT (W0.2 of juniper-ml
# notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md):
# before `serve`, recurrence_up runs util/recurrence_env_preflight.bash against the interpreter
# the console script will run under — `pip check` scoped to the recurrence closure, the model and
# service-core pins, and the `derive_full_split` import — and fails the leg on any finding, so the
# partial run is torn down like any other failed leg. The report goes to stdout AND to
# $RUN_DIR/logs/launch.log. The console script existing and /v1/health/ready were the only gates
# before, and on 2026-10-03 a stale JuniperCascor1 passed both (F-E1 / F-E2).
#
# RECURRENCE SERVICE ENV (W1.10 of the same plan): recurrence_up exports
# JUNIPER_RECURRENCE_SNAPSHOTS_DIR=$RUN_DIR/snapshots, the dir create_run_dir makes; unexported, the
# service fell back to its CWD-relative default and wrote $RUN_DIR/recurrence-snapshots (F-D9). It
# passes JUNIPER_RECURRENCE_LOG_LEVEL / JUNIPER_RECURRENCE_LOG_FORMAT through when they are set in
# this launcher's environment, and leaves an unset one out rather than exporting it empty (F-L11).
# Both log vars already reached `serve` by inheritance (the launch uses no `env -i`); naming them
# puts them in the announce line, env/launch.env and ports.json. PRECEDENCE: juniper-recurrence
# resolves its settings as init/CLI > the YAML `service:` block (via JUNIPER_RECURRENCE_CONFIG_FILE,
# i.e. --config) > env > defaults (settings.py settings_customise_sources), so a `service:` key for
# log_level, log_format or snapshots_dir in the staged config OUTRANKS the env value passed here.
# The env route is for a run whose YAML sets no such key.
#
# RECURRENCE LAUNCH RECORD (W1.9 of the same plan, F-D4): once the env preflight has passed,
# recurrence_up rewrites ports.json with a "recurrence_launch" object: conda_env, cli (the console
# script `serve` runs), python (the interpreter its shebang names; see console_script_python),
# model_version (juniper-recurrence-model as that interpreter resolves it, probed WITHOUT -s and
# from /, as `serve` imports it; null when the probe fails), snapshots_dir, log_level and log_format
# (null = not passed, so the service default or the YAML applies), and config_file.
# util/experiments/run_experiment.py's save_model re-run executes that cli instead of whatever
# `juniper-recurrence` is first on the driver's PATH, and refuses to run when the cli resolves a
# different interpreter, or the interpreter a different model version, than the served process.
###########################################################################################################################################################################################################
set -euo pipefail


###########################################################################################################################################################################################################
# Script + directory constants
###########################################################################################################################################################################################################
SCRIPT_NAME="$(basename "$(realpath "${BASH_SOURCE[0]}")")"
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# util/ -> juniper-ml -> Juniper (ecosystem root); override with JUNIPER_EXP_PROJECT_DIR.
JUNIPER_ML_DIR="$(dirname "${SCRIPT_DIR}")"
PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-$(dirname "${JUNIPER_ML_DIR}")}"

# juniper-data is launched as `python -m juniper_data` from its conda env, so no repo path
# is needed for it; cascor's uvicorn factory import DOES require its src/ as CWD (§6.1).
#
# Overridable on its own, independently of PROJECT_DIR, so a campaign can pin cascor to a
# WORKTREE while everything else stays canonical. Before this the path was derived, which made
# every campaign freeze the primary checkout for its whole life -- and any session running a
# stack out of the primary blocked every campaign (observed 2026-08-26: a live E2E stack on
# :8202 with cwd in the primary src). Pinning a worktree is safe: JuniperCascor1's editable
# install registers its finder with `sys.meta_path.append`, i.e. AFTER the default PathFinder,
# so CWD wins and the finder is only a fallback -- verified per-module by
# util/ad-hoc/2026-08-26_cascor_import_provenance.py, which asks the import system rather than
# trusting JUNIPER_CASCOR_GIT_SHA (that is stamped from the REQUESTED tree and so cannot fail).
CASCOR_SRC_DIR="${JUNIPER_EXP_CASCOR_SRC_DIR:-${PROJECT_DIR}/juniper-cascor/src}"
DEPLOY_DIR="${JUNIPER_EXP_DEPLOY_DIR:-${PROJECT_DIR}/juniper-deploy}"
# F-3: prometheus/targets/ is already inside the existing ./prometheus:/etc/prometheus:ro
# mount, so writing here needs no compose change at all.
TARGETS_DIR="${DEPLOY_DIR}/prometheus/targets"


###########################################################################################################################################################################################################
# Port ranges (plan §9.3) — contiguous, disjoint, and deliberately clear of every operator port
###########################################################################################################################################################################################################
DATA_PORT_MIN=8110
DATA_PORT_MAX=8139
CASCOR_PORT_MIN=8230
CASCOR_PORT_MAX=8259
RECURRENCE_PORT_MIN=8260
RECURRENCE_PORT_MAX=8289


###########################################################################################################################################################################################################
# Run identity + roots
###########################################################################################################################################################################################################
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
# A lock is ephemeral state, so it belongs in the runtime dir — NOT in RUN_ROOT, which is
# deliberately durable (H-15: results must survive a reaped sandbox).
LOCK_ROOT="${JUNIPER_EXP_LOCK_ROOT:-${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments}"

CONDA_DIR="${JUNIPER_EXP_CONDA_DIR:-/opt/miniforge3}"
CONDA_SH="${CONDA_DIR}/etc/profile.d/conda.sh"
DATA_CONDA="${JUNIPER_EXP_DATA_CONDA:-JuniperData}"
CASCOR_CONDA="${JUNIPER_EXP_CASCOR_CONDA:-JuniperCascor1}"
RECURRENCE_CONDA="${JUNIPER_EXP_RECURRENCE_CONDA:-JuniperCascor1}"

HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-90}"
KILL_TIMEOUT="${JUNIPER_EXP_KILL_TIMEOUT:-10}"
CONDA_ACTIVATE="${JUNIPER_EXP_CONDA_ACTIVATE:-0}"

# W0.2 recurrence env preflight (RECURRENCE ENV PREFLIGHT above). Run with `bash`: the script is
# committed 0644, because a GitHub-signed API commit carries no file mode.
ENV_PREFLIGHT="${SCRIPT_DIR}/recurrence_env_preflight.bash"
SKIP_ENV_PREFLIGHT="${JUNIPER_EXP_SKIP_ENV_PREFLIGHT:-0}"


###########################################################################################################################################################################################################
# Mutable run state
###########################################################################################################################################################################################################
DRY_RUN=0
ACTION=""
WANT_CASCOR=0
WANT_RECURRENCE=0
WANT_BRIDGE=0
ALL_MINE=0
CONFIG_PATH=""
EXPERIMENT=""
SHARED_DATA_URL=""
TARGET_RUN_ID=""

RUN_ID=""
RUN_DIR=""
LOG_DIR=""
DATA_PORT=""
CASCOR_PORT=""
RECURRENCE_PORT=""
DATA_URL=""
GATEWAY_IP=""
# W1.9: the "recurrence_launch" object, set by recurrence_up and rendered by write_ports_json.
RECURRENCE_LAUNCH_JSON=""

HELD_LOCK_PORTS=()
SCRAPE_TARGETS=()


###########################################################################################################################################################################################################
# Utility functions
###########################################################################################################################################################################################################
usage() {
    cat <<USAGE
${SCRIPT_NAME} — per-run experiment stack (data ${DATA_PORT_MIN}-${DATA_PORT_MAX} / cascor ${CASCOR_PORT_MIN}-${CASCOR_PORT_MAX} / recurrence ${RECURRENCE_PORT_MIN}-${RECURRENCE_PORT_MAX})

Usage: ${SCRIPT_NAME} --up (--cascor | --recurrence) [--shared-data URL] [--config PATH] [--experiment NAME] [--grafana-bridge] [--skip-env-preflight] [--dry-run]
       ${SCRIPT_NAME} --down (RUN_ID | --all-mine) [--dry-run]
       ${SCRIPT_NAME} --status [RUN_ID] [--dry-run]
       ${SCRIPT_NAME} --help

  --up               Allocate ports and launch data -> cascor -> recurrence (health-gated).
  --cascor           Include juniper-cascor (cascor arm = data + cascor).
  --recurrence       Include juniper-recurrence (recurrence arm = data + recurrence).
  --shared-data URL  Reuse an existing juniper-data instead of launching a per-run one.
  --config PATH      Stage an experiment YAML into the run dir; its service: block reaches the apps via JUNIPER_*_CONFIG_FILE (Waves 3.1/3.3).
  --experiment NAME  Prometheus 'experiment' target label (default: config basename).
  --grafana-bridge   OPT-IN: start socat relays and write the Prometheus target file.
  --skip-env-preflight
                     With --recurrence: run the recurrence env preflight but only WARN (stdout + logs/launch.log) instead of refusing a stale env.
                     Env equivalent: JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1. Emergencies only.
  --down RUN_ID      Tear down a run (pidfile-first); --all-mine tears down every run.
  --status [RUN_ID]  Probe a run, or list every run under the run root.
  --dry-run          Print every command without executing it (creates/kills nothing).
  --help,-h          Print this help.

Run root : ${RUN_ROOT}
Lock root: ${LOCK_ROOT}
Targets  : ${TARGETS_DIR}

See juniper-ml notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md §6.2 for the full contract.
USAGE
}

log() { echo "[${SCRIPT_NAME}] $*"; }

banner() {
    echo ""
    echo "[${SCRIPT_NAME}] === $* ==="
}

# Print a command line (prefixed with a literal '$'); callers guard side effects with is_dry.
announce() { echo "[${SCRIPT_NAME}] \$ $*"; }

is_dry() { [[ "${DRY_RUN}" == "1" ]]; }

require_cmd() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        log "ERROR: required command '${cmd}' not found in PATH"
        return 1
    fi
}

ensure_dir() {
    local dir="$1"
    [[ -d "${dir}" ]] || mkdir -p "${dir}"
}

# Absolute path to a binary inside a conda env (direct-bin launch form; see CONDA above).
env_bin() {
    local env_name="$1" bin_name="$2"
    printf '%s' "${CONDA_DIR}/envs/${env_name}/bin/${bin_name}"
}

# Source conda + activate an env (nounset-safe, matching juniper_plant_all.bash /
# isolated_stack.bash). Only reached under JUNIPER_EXP_CONDA_ACTIVATE=1.
#
# Fail-closed on ``source`` / ``conda activate``: callers invoke this as
# ``activate_conda … || return 1`` inside ``*_up || failed=1``, which disables
# ``set -e`` for the whole body (bash OR-list rule). A bare ``conda activate``
# failure followed by a successful ``set -u`` would otherwise return 0 and let
# the service launch on the ambient PATH.
activate_conda() {
    local env_name="$1"
    if [[ ! -f "${CONDA_SH}" ]]; then
        log "ERROR: conda not found at ${CONDA_SH} (set JUNIPER_EXP_CONDA_DIR)"
        return 1
    fi
    # shellcheck source=/dev/null
    source "${CONDA_SH}" || {
        log "ERROR: failed to source conda.sh at ${CONDA_SH}"
        return 1
    }
    # Conda activation scripts (e.g. activate-binutils_linux-64.sh) may
    # reference unset vars like ADDR2LINE; disable nounset for the call only.
    set +u
    if ! conda activate "${env_name}"; then
        set -u
        log "ERROR: conda activate '${env_name}' failed"
        return 1
    fi
    set -u
}

# Verify the launch env exists before promising a launch line that cannot run.
require_env_bin() {
    local env_name="$1" bin_name="$2" path
    path="$(env_bin "${env_name}" "${bin_name}")"
    if [[ ! -x "${path}" ]]; then
        log "ERROR: ${bin_name} not found in conda env '${env_name}' (${path})"
        return 1
    fi
}

# The interpreter a console script actually runs under: its shebang. pip writes a plain absolute
# one (`#!/opt/miniforge3/envs/JuniperCascor1/bin/python3.14` on this host, where bin/python is a
# symlink to that same file) unless the path is too long or holds a space, when it writes a
# /bin/sh trampoline instead; anything but a plain absolute python shebang falls back to the
# env's bin/python. A shebang naming an interpreter that no longer exists is returned as-is, so
# the preflight names it — the 2026-09-12 JuniperCascor1 3.13 -> 3.14 upgrade deleted the
# interpreter that older console scripts' shebangs still named.
console_script_python() {
    local script="$1" fallback="$2" first=""
    if [[ -r "${script}" ]]; then
        IFS= read -r first <"${script}" || true
    fi
    first="${first%$'\r'}"
    if [[ "${first}" == '#!/'* ]]; then
        first="${first:2}"
        first="${first%%[[:space:]]*}"
        if [[ "${first##*/}" == python* ]]; then
            printf '%s' "${first}"
            return 0
        fi
    fi
    printf '%s' "${fallback}"
}

# log() to stdout, plus the same line, timestamped, into the run's ${LOG_DIR}/launch.log. stdout
# is what run_suite.py captures, and it keeps only a 500-char tail of it, on failure only;
# launch.log is the copy that survives — where a --skip-env-preflight launch stays loud.
log_launch() {
    log "$*"
    if ! printf '%s [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${SCRIPT_NAME}" "$*" >>"${LOG_DIR}/launch.log" 2>/dev/null; then
        log "WARNING: could not append to ${LOG_DIR}/launch.log"
    fi
}

# W0.2: run the recurrence env preflight against the interpreter `serve` will run under, and fail
# on a finding. Every line of its report goes through log_launch.
#
# Explicit returns, not set -e: recurrence_up runs as ``recurrence_up || failed=1``, which
# disables set -e for this body too (bash OR-list rule). The script is run with `bash` because
# it is committed 0644; a missing or crashing script fails closed, like a refusal.
run_env_preflight() {
    local python_bin="$1" out="" rc=0 line
    local -a args=(--python "${python_bin}")
    if [[ "${SKIP_ENV_PREFLIGHT}" == "1" ]]; then
        args+=(--skip)
    fi
    log_launch "recurrence env preflight: bash ${ENV_PREFLIGHT} ${args[*]}"
    out="$(bash "${ENV_PREFLIGHT}" "${args[@]}" 2>&1)" || rc=$?
    while IFS= read -r line; do
        if [[ -n "${line}" ]]; then
            log_launch "${line}"
        fi
    done <<<"${out}"
    if (( rc != 0 )); then
        log_launch "ERROR: recurrence env preflight refused ${python_bin} (exit ${rc}); serve NOT started. Repair the env (plan W0.1), or pass --skip-env-preflight to launch it anyway."
        return 1
    fi
    return 0
}


###########################################################################################################################################################################################################
# Port helpers
###########################################################################################################################################################################################################
# PID of whatever holds the LISTEN socket on a TCP port (empty if nothing / ss unavailable).
port_listener_pid() {
    local port="$1" out
    out="$(ss -tlnpH "sport = :${port}" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -n1 | cut -d= -f2 || true)"
    printf '%s' "${out}"
}

# True when anything at all is listening on the port (no pid privileges required).
port_in_use() {
    local port="$1" out
    out="$(ss -tlnH "sport = :${port}" 2>/dev/null || true)"
    [[ -n "${out}" ]]
}

# Allocate the first free port in [min,max] and hold its lockdir for the run.
#
# Sets the global ALLOCATED_PORT (rather than printing) so the HELD_LOCK_PORTS append is
# not lost to a command-substitution subshell.
#
# `mkdir` is atomic, so the lockdir SERIALISES experiment launchers against each other.
# It cannot serialise us against a third party that is not participating in the protocol:
# a foreign process may still bind the port between our `ss` probe and the service's own
# bind. That residual race is deliberately NOT papered over — it surfaces as the service's
# own bind failure, which the health gate turns into a loud timeout (plan H-1).
ALLOCATED_PORT=""
allocate_port() {
    local svc="$1" min="$2" max="$3" port lockdir
    ALLOCATED_PORT=""
    port="${min}"
    while (( port <= max )); do
        lockdir="${LOCK_ROOT}/${port}.lock"
        if is_dry; then
            # A dry run takes NO lock and creates NO directory; it only reports which port
            # the live run would pick, using the same read-only ss probe.
            if [[ ! -d "${lockdir}" ]] && ! port_in_use "${port}"; then
                ALLOCATED_PORT="${port}"
                return 0
            fi
        elif mkdir "${lockdir}" 2>/dev/null; then
            if port_in_use "${port}"; then
                rmdir "${lockdir}" 2>/dev/null || true
            else
                HELD_LOCK_PORTS+=("${port}")
                ALLOCATED_PORT="${port}"
                return 0
            fi
        fi
        port=$(( port + 1 ))
    done
    log "ERROR: no free ${svc} port in ${min}-${max} (all locked or in use)"
    return 1
}

release_port_lock() {
    local port="$1"
    [[ -n "${port}" ]] || return 0
    announce "rmdir ${LOCK_ROOT}/${port}.lock   # release the port lock"
    if is_dry; then return 0; fi
    rmdir "${LOCK_ROOT}/${port}.lock" 2>/dev/null || true
}

release_held_locks() {
    local port
    for port in "${HELD_LOCK_PORTS[@]:-}"; do
        [[ -n "${port}" ]] || continue
        rmdir "${LOCK_ROOT}/${port}.lock" 2>/dev/null || true
    done
    HELD_LOCK_PORTS=()
}


###########################################################################################################################################################################################################
# Process helpers
###########################################################################################################################################################################################################
proc_cmdline() {
    local pid="$1"
    tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true
}

# Poll a health URL until 200 or timeout (live mode only).
#
# The optional 4th arg is a `pgrep -f` LIVENESS pattern for the process this gate is
# waiting on. A service that dies during startup (bad env, import error, port already
# bound) otherwise burns the whole HEALTH_TIMEOUT — 90s by default, per leg — before the
# operator learns anything, and the real cause is already sitting in the leg's log. With
# a pattern, two CONSECUTIVE misses end the wait immediately and name the log to read.
#
# Two misses, not one: the launch subshell returns before its child finishes exec'ing, so
# a single miss is a normal startup artifact. The first probe runs after the first sleep,
# giving fork+exec a >=4s grace before a death can be declared.
#
# F-6 stays intact: this pattern is only ever read (`pgrep`), never used to resolve a pid
# and never used to kill. Teardown still goes through the recorded listener pid + cmdline.
# A host without `pgrep` degrades to the pre-existing timeout-only behaviour rather than
# reporting a false death — an unavailable probe must never manufacture a failure.
wait_for_health() {
    local name="$1" url="$2" timeout="${3:-${HEALTH_TIMEOUT}}" liveness_pattern="${4-}" elapsed=0 misses=0
    if [[ -n "${liveness_pattern}" ]] && ! command -v pgrep >/dev/null 2>&1; then
        log "${name}: pgrep unavailable — health gate falls back to timeout-only (no dead-process fast-fail)"
        liveness_pattern=""
    fi
    log "Waiting for ${name} health at ${url} (timeout ${timeout}s)"
    while (( elapsed < timeout )); do
        if curl -sf --max-time 5 "${url}" >/dev/null 2>&1; then
            log "${name} is healthy (took ${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$(( elapsed + 2 ))
        if [[ -n "${liveness_pattern}" ]]; then
            if pgrep -f -- "${liveness_pattern}" >/dev/null 2>&1; then
                misses=0
            else
                misses=$(( misses + 1 ))
                if (( misses >= 2 )); then
                    log "ERROR: ${name} process is gone after ${elapsed}s (no process matches '${liveness_pattern}') — it died during startup; see ${LOG_DIR}/${name}.log"
                    return 1
                fi
            fi
        fi
    done
    log "ERROR: ${name} failed to become healthy within ${timeout}s (see ${LOG_DIR})"
    return 1
}

# Record the AUTHORITATIVE pid for a service, resolved from the LISTENER after the health
# gate has proven the port is bound.
#
# F-6 (P0 preflight evidence): `$!` taken after `( cd … && nohup <server> … & )` is the
# backgrounded SUBSHELL, not the server — during Wave 0 all three "recorded" pids died on
# signal while the servers lived on. So the launcher never records `$!` for a service; it
# asks `ss -tlnpH "sport = :<port>"` who actually owns the listening socket, and stores the
# process' cmdline alongside so teardown can prove identity before it kills anything.
record_listener_pid() {
    local svc="$1" port="$2" pid
    pid="$(port_listener_pid "${port}")"
    if [[ -z "${pid}" ]]; then
        log "ERROR: ${svc} answered health on ${port} but no listener pid resolved via ss"
        return 1
    fi
    printf '%s\n' "${pid}" >"${RUN_DIR}/${svc}.pid"
    proc_cmdline "${pid}" >"${RUN_DIR}/${svc}.cmdline"
    log "${svc}: listener pid ${pid} recorded -> ${RUN_DIR}/${svc}.pid"
}

# SIGTERM then a bounded SIGKILL, only after the pid is proven to be ours and unchanged.
terminate_pid() {
    local pid="$1" label="$2" waited=0
    log "Stopping ${label} (pid ${pid}) with SIGTERM"
    kill -TERM "${pid}" 2>/dev/null || true
    while (( waited < KILL_TIMEOUT )); do
        if ! kill -0 "${pid}" 2>/dev/null; then
            log "${label}: pid ${pid} exited after ${waited}s"
            return 0
        fi
        sleep 1
        waited=$(( waited + 1 ))
    done
    log "${label}: pid ${pid} still alive after ${KILL_TIMEOUT}s — sending SIGKILL"
    kill -KILL "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
        log "ERROR: ${label}: pid ${pid} survived SIGKILL"
        return 1
    fi
    return 0
}

# Kill a pid only if it is alive, owned by the current user, and still running the exact
# cmdline recorded at launch (pid-reuse guard). Returns 1 when it refuses, so the caller
# can fall back to the recorded port.
kill_verified_pid() {
    local pid="$1" label="$2" recorded="$3" owner live
    if [[ ! "${pid}" =~ ^[0-9]+$ ]]; then
        log "${label}: recorded pid '${pid}' is not a number — refusing to kill"
        return 1
    fi
    if ! kill -0 "${pid}" 2>/dev/null; then
        log "${label}: recorded pid ${pid} is not alive (already gone)"
        return 0
    fi
    owner="$(stat -c '%u' "/proc/${pid}" 2>/dev/null || true)"
    if [[ "${owner}" != "$(id -u)" ]]; then
        log "${label}: pid ${pid} is owned by uid '${owner:-unknown}', not $(id -u) — refusing to kill"
        return 1
    fi
    live="$(proc_cmdline "${pid}")"
    if [[ -n "${recorded}" && "${live}" != "${recorded}" ]]; then
        log "${label}: pid ${pid} cmdline changed since launch — refusing to kill (pid reuse)"
        return 1
    fi
    terminate_pid "${pid}" "${label}"
}


###########################################################################################################################################################################################################
# Run directory (§6.4)
###########################################################################################################################################################################################################
new_run_id() {
    local rand
    if command -v openssl >/dev/null 2>&1; then
        rand="$(openssl rand -hex 2)"
    else
        rand="$(printf '%04x' $(( RANDOM % 65536 )))"
    fi
    printf '%s-%s' "$(date -u +%Y%m%dT%H%M%SZ)" "${rand}"
}

create_run_dir() {
    announce "mkdir -p ${RUN_DIR}/{logs,relays,config,env,data,equities-cache,snapshots,artifacts/plots,artifacts/results}"
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}"
    ensure_dir "${LOG_DIR}"
    ensure_dir "${RUN_DIR}/relays"
    ensure_dir "${RUN_DIR}/config"
    ensure_dir "${RUN_DIR}/env"
    ensure_dir "${RUN_DIR}/data"
    ensure_dir "${RUN_DIR}/equities-cache"
    # Wave 5.3: per-run cascor snapshots home (W-6 JUNIPER_CASCOR_SNAPSHOTS_DIR target) —
    # retires the repo-shared src/snapshots .h5 debris (H-4; the F-P1-4 finding).
    ensure_dir "${RUN_DIR}/snapshots"
    ensure_dir "${RUN_DIR}/artifacts/plots"
    ensure_dir "${RUN_DIR}/artifacts/results"
}

stage_config() {
    [[ -n "${CONFIG_PATH}" ]] || return 0
    announce "cp ${CONFIG_PATH} ${RUN_DIR}/config/experiment.yaml"
    if is_dry; then return 0; fi
    if [[ ! -f "${CONFIG_PATH}" ]]; then
        log "ERROR: --config file not found: ${CONFIG_PATH}"
        return 1
    fi
    cp "${CONFIG_PATH}" "${RUN_DIR}/config/experiment.yaml"
}

json_number_or_null() {
    local value="$1"
    if [[ -n "${value}" ]]; then printf '%s' "${value}"; else printf 'null'; fi
}

# A JSON string literal, or null for an empty value. Backslash, double quote, newline, CR and tab
# are escaped: recurrence_launch records interpreter and script paths verbatim.
json_string_or_null() {
    local value="$1"
    if [[ -z "${value}" ]]; then
        printf 'null'
        return 0
    fi
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/\\r}"
    value="${value//$'\t'/\\t}"
    printf '"%s"' "${value}"
}

# W1.9: the "recurrence_launch" object ports.json records (RECURRENCE LAUNCH RECORD in the header).
# An empty argument renders as null: a log var the launcher did not pass, or a probe that failed.
recurrence_launch_json() {
    local conda_env="$1" cli="$2" python="$3" model_version="$4" snapshots_dir="$5" log_level="$6" log_format="$7" config_file="$8"
    printf '{\n'
    printf '    "conda_env": %s,\n' "$(json_string_or_null "${conda_env}")"
    printf '    "cli": %s,\n' "$(json_string_or_null "${cli}")"
    printf '    "python": %s,\n' "$(json_string_or_null "${python}")"
    printf '    "model_version": %s,\n' "$(json_string_or_null "${model_version}")"
    printf '    "snapshots_dir": %s,\n' "$(json_string_or_null "${snapshots_dir}")"
    printf '    "log_level": %s,\n' "$(json_string_or_null "${log_level}")"
    printf '    "log_format": %s,\n' "$(json_string_or_null "${log_format}")"
    printf '    "config_file": %s\n' "$(json_string_or_null "${config_file}")"
    printf '  }'
}

# ports.json is written BEFORE the launches so a bring-up that dies mid-flight still leaves
# teardown a record of exactly which ports this run may touch. recurrence_up writes it once more
# (W1.9), adding RECURRENCE_LAUNCH_JSON as "recurrence_launch" -- through this one writer, so the
# rewrite cannot drift from the first write on any other key. Each write goes to a temp file that
# is renamed over ports.json, so a concurrent reader (--status, list_runs.py) never sees it torn.
# RUN_ID / EXPERIMENT / WANT_BRIDGE carry `:-` defaults for cascor_up's reason: the regression
# harness extracts recurrence_up, which now calls this, without the file-scope globals.
write_ports_json() {
    local bridge="false" launch_member="" launch_note=""
    (( ${WANT_BRIDGE:-0} == 1 )) && bridge="true"
    if [[ -n "${RECURRENCE_LAUNCH_JSON:-}" ]]; then
        launch_member=$',\n  "recurrence_launch": '"${RECURRENCE_LAUNCH_JSON}"
        launch_note=" + recurrence_launch (W1.9)"
    fi
    announce "write ${RUN_DIR}/ports.json   # {\"data\":$(json_number_or_null "${DATA_PORT}"),\"cascor\":$(json_number_or_null "${CASCOR_PORT}"),\"recurrence\":$(json_number_or_null "${RECURRENCE_PORT}")}${launch_note}"
    if is_dry; then return 0; fi
    # Explicit returns: do_up and recurrence_up both call this as ``write_ports_json || …``, which
    # disables set -e in this body, and a failed write must not be renamed over the good file.
    render_ports_json "${bridge}" "${launch_member}" >"${RUN_DIR}/ports.json.tmp" || return 1
    mv -f "${RUN_DIR}/ports.json.tmp" "${RUN_DIR}/ports.json" || return 1
}

# The ports.json document, byte for byte what the earlier heredoc wrote. printf, not a heredoc: the
# regression harness extracts a function up to its first line holding only `}`, which the JSON's
# own closing brace inside a heredoc would be.
render_ports_json() {
    local bridge="$1" launch_member="$2"
    printf '{\n'
    printf '  "run_id": "%s",\n' "${RUN_ID:-}"
    printf '  "data": %s,\n' "$(json_number_or_null "${DATA_PORT}")"
    printf '  "cascor": %s,\n' "$(json_number_or_null "${CASCOR_PORT}")"
    printf '  "recurrence": %s,\n' "$(json_number_or_null "${RECURRENCE_PORT}")"
    printf '  "data_url": "%s",\n' "${DATA_URL}"
    printf '  "experiment": "%s",\n' "${EXPERIMENT:-}"
    printf '  "grafana_bridge": %s%s\n' "${bridge}" "${launch_member}"
    printf '}\n'
}

# Read one numeric port from a run's ports.json without a jq dependency.
read_run_port() {
    local file="$1" key="$2" value
    value="$(sed -n "s/^[[:space:]]*\"${key}\"[[:space:]]*:[[:space:]]*\([0-9]\{1,\}\).*/\1/p" "${file}" 2>/dev/null | head -n1 || true)"
    printf '%s' "${value}"
}

read_run_flag() {
    local file="$1" key="$2" value
    value="$(sed -n "s/^[[:space:]]*\"${key}\"[[:space:]]*:[[:space:]]*\(true\|false\).*/\1/p" "${file}" 2>/dev/null | head -n1 || true)"
    printf '%s' "${value}"
}

# The exact env each service was launched with (§6.4 env/launch.env). No secrets are ever
# placed in these variables, but the file is written 0600 to keep the habit.
record_launch_env() {
    local svc="$1"
    shift
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}/env"
    {
        printf '# %s\n' "${svc}"
        printf '%s\n' "$@"
    } >>"${RUN_DIR}/env/launch.env"
    chmod 600 "${RUN_DIR}/env/launch.env" 2>/dev/null || true
}


###########################################################################################################################################################################################################
# Bring-up: juniper-data (dedicated per-run instance, plan §6.1)
###########################################################################################################################################################################################################
data_up() {
    local python_bin
    python_bin="$(env_bin "${DATA_CONDA}" python)"
    banner "juniper-data  ->  http://127.0.0.1:${DATA_PORT}  (${DATA_CONDA}, per-run instance)"
    announce "cd ${RUN_DIR} && JUNIPER_DATA_STORAGE_PATH=${RUN_DIR}/data JUNIPER_DATA_METRICS_ENABLED=true JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache PYTHON_GIL=0 ${python_bin} -m juniper_data --host 127.0.0.1 --port ${DATA_PORT}   # nohup -> ${LOG_DIR}/juniper-data.log (+PYTHON_GIL=0 iff the run's python is a free-threaded build)"
    if is_dry; then return 0; fi

    # Explicit ``|| return 1``: do_up invokes this as ``data_up || failed=1``, which
    # disables set -e for the whole body (bash OR-list rule). Without these checks a
    # health-timeout with a live listener would fall through to record_listener_pid
    # (exit 0) and false-green the bring-up — orphaning the process with no teardown.
    require_env_bin "${DATA_CONDA}" python || return 1
    ensure_dir "${LOG_DIR}"
    # PYTHON_GIL=0 aborts a stock (non-free-threaded) CPython at startup — "Fatal Python
    # error: config_read_gil: Disabling the GIL is not supported by this build" — so the
    # toggle is passed only when THIS run's interpreter supports it (the host python3.14
    # lost its free-threaded build to OS updates, 2026-08-09 rehearsal). Probe ${python_bin}
    # itself, never the ambient python: the leg launches from that direct env-bin path.
    # Deliberately NO ``|| return 1`` — an unrunnable probe degrades to omitting the toggle
    # (always safe), and only a genuinely missing binary fails, via require_env_bin above.
    local -a gil_env=()
    local gil_record="PYTHON_GIL="
    if [[ "$("${python_bin}" -c 'import sysconfig; print(sysconfig.get_config_var("Py_GIL_DISABLED") or 0)' 2>/dev/null)" == "1" ]]; then
        gil_env=("PYTHON_GIL=0")
        gil_record="PYTHON_GIL=0"
    fi
    # env/launch.env is evidence: record the toggle only when it is actually passed.
    record_launch_env "juniper-data" \
        "JUNIPER_DATA_STORAGE_PATH=${RUN_DIR}/data" \
        "JUNIPER_DATA_METRICS_ENABLED=true" \
        "JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache" \
        "${gil_record}"
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${DATA_CONDA}" || return 1; fi
    (
        cd "${RUN_DIR}" || exit 1
        JUNIPER_DATA_STORAGE_PATH="${RUN_DIR}/data" \
            JUNIPER_DATA_METRICS_ENABLED=true \
            JUNIPER_DATA_EQUITIES_CACHE_DIR="${RUN_DIR}/equities-cache" \
            nohup env "${gil_env[@]}" "${python_bin}" -m juniper_data --host 127.0.0.1 --port "${DATA_PORT}" >"${LOG_DIR}/juniper-data.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6. The pid is resolved from the listener below.
    # The liveness pattern carries this run's port so it can never match a sibling run.
    wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" "${HEALTH_TIMEOUT}" "-m juniper_data .*--port ${DATA_PORT}" || return 1
    record_listener_pid "juniper-data" "${DATA_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Bring-up: juniper-cascor (uvicorn factory CLI owns the bind, plan §6.1)
###########################################################################################################################################################################################################
cascor_up() {
    local uvicorn_bin config_env="" git_sha
    uvicorn_bin="$(env_bin "${CASCOR_CONDA}" uvicorn)"
    [[ -n "${CONFIG_PATH}" ]] && config_env="JUNIPER_CASCOR_CONFIG_FILE=${RUN_DIR}/config/experiment.yaml "
    # D-C snapshot provenance. RUN_ID and EXPERIMENT are the launcher's own; CELL_ID and
    # DATASET_ID pass through from whoever knows them (run_suite exports CELL_ID) and are
    # simply blank otherwise, which cascor reads as "unset" rather than recording an
    # empty string. Named explicitly here rather than relying on env inheritance so the
    # values appear in the announce line and in record_launch_env — an operator reading
    # the run dir can see exactly what identity the process was given.
    #
    # The git SHA is resolved INLINE rather than through a helper: the regression
    # harness extracts this function body on its own, so anything it calls at file scope
    # is undefined there. Best-effort — no git, or a non-repo checkout, yields empty,
    # and cascor treats blank as unset rather than recording a lie.
    git_sha="$(git -C "${CASCOR_SRC_DIR}" rev-parse --short=12 HEAD 2>/dev/null || true)"
    # D2 (perf lane, owner-ruled 2026-09-11; route half of the gate measured 2026-09-17, the
    # epoch-count half never delivered — see `run_suite.runtime_block_env`): the `runtime:` block's
    # thread budget, made VISIBLE.
    #
    # Be precise about what this does, because the obvious reading is wrong: these variables
    # already REACH cascor without it. `run_suite.execute_cell` puts them in this launcher's own
    # environment, and the launch subshell does not use `env -i`, so uvicorn inherits them
    # regardless. **Delivery is by inheritance; this block adds RECORDING.** Without it the
    # announce line and `env/launch.env` describe a launch whose thread width is unstated — and
    # for a lane whose every finding is "record the width actually in force or the reading means
    # nothing", an unrecorded width is the whole problem. Naming them also makes the launch
    # explicit rather than ambient, which is the same argument the D-C block above makes.
    #
    # Blast radius worth knowing: because delivery IS inheritance, `data_up` and `recurrence_up`
    # receive the same variables. `runtime.blas_threads` pins juniper-data's BLAS too, not just
    # cascor's. That is usually what you want from a per-run budget; it is not what the key's
    # name suggests.
    #
    # Built ONCE and consumed at all three sites. The D-C/Q-6 vars above are triplicated by hand
    # and guarded by count-3 tests because hand-copied sites drift; an array cannot drift from
    # itself, so this needs no such test — only proof that all three sites consume it.
    #
    # Passed through an `env` ARRAY rather than a `VAR=${VAR:-}` prefix, for the same reason
    # `data_up` builds `gil_env`: an EMPTY `OMP_NUM_THREADS` is not the same as an unset one.
    # The prefix form would export `OMP_NUM_THREADS=` on every run that sets no budget — which
    # is most of them — turning "the caller said nothing" into "the caller said something
    # malformed". Only variables that are actually set are named.
    local -a runtime_env=()
    local _rv
    for _rv in OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS CASCOR_NUM_PROCESSES JUNIPER_CASCOR_EVAL_METRICS_ENABLED; do
        if [[ -n "${!_rv:-}" ]]; then runtime_env+=("${_rv}=${!_rv}"); fi
    done
    local runtime_announce=""
    if [[ ${#runtime_env[@]} -gt 0 ]]; then runtime_announce="${runtime_env[*]} "; fi
    banner "juniper-cascor  ->  http://127.0.0.1:${CASCOR_PORT}  (${CASCOR_CONDA})"
    announce "cd ${CASCOR_SRC_DIR} && ${runtime_announce}LD_LIBRARY_PATH= JUNIPER_CASCOR_METRICS_ENABLED=true JUNIPER_CASCOR_AUTO_START=false JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false JUNIPER_CASCOR_LOG_LEVEL=INFO JUNIPER_CASCOR_SNAPSHOTS_DIR=${RUN_DIR}/snapshots JUNIPER_CASCOR_LOG_DIR=${LOG_DIR} JUNIPER_DATA_URL=${DATA_URL} JUNIPER_CASCOR_RUN_ID=${RUN_ID:-} JUNIPER_CASCOR_EXPERIMENT=${JUNIPER_CASCOR_EXPERIMENT:-${EXPERIMENT:-}} JUNIPER_CASCOR_CELL_ID=${JUNIPER_CASCOR_CELL_ID:-} JUNIPER_CASCOR_DATASET_ID=${JUNIPER_CASCOR_DATASET_ID:-} JUNIPER_CASCOR_GIT_SHA=${git_sha} ${config_env}${uvicorn_bin} api.app:create_app --factory --host 127.0.0.1 --port ${CASCOR_PORT}   # nohup -> ${LOG_DIR}/juniper-cascor.log"
    if is_dry; then return 0; fi

    # See data_up: ``cascor_up || failed=1`` disables set -e inside this body.
    require_env_bin "${CASCOR_CONDA}" uvicorn || return 1
    ensure_dir "${LOG_DIR}"
    record_launch_env "juniper-cascor" \
        "LD_LIBRARY_PATH=" \
        "JUNIPER_CASCOR_METRICS_ENABLED=true" \
        "JUNIPER_CASCOR_AUTO_START=false" \
        "JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false" \
        "JUNIPER_CASCOR_LOG_LEVEL=INFO" \
        "JUNIPER_CASCOR_SNAPSHOTS_DIR=${RUN_DIR}/snapshots" \
        "JUNIPER_CASCOR_LOG_DIR=${LOG_DIR}" \
        "JUNIPER_DATA_URL=${DATA_URL}" \
        "JUNIPER_CASCOR_RUN_ID=${RUN_ID:-}" \
        "JUNIPER_CASCOR_EXPERIMENT=${JUNIPER_CASCOR_EXPERIMENT:-${EXPERIMENT:-}}" \
        "JUNIPER_CASCOR_CELL_ID=${JUNIPER_CASCOR_CELL_ID:-}" \
        "JUNIPER_CASCOR_DATASET_ID=${JUNIPER_CASCOR_DATASET_ID:-}" \
        "JUNIPER_CASCOR_GIT_SHA=${git_sha}" \
        "JUNIPER_CASCOR_CONFIG_FILE=${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}" \
        "${runtime_env[@]}"
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${CASCOR_CONDA}" || return 1; fi
    (
        cd "${CASCOR_SRC_DIR}" || exit 1
        LD_LIBRARY_PATH='' \
            JUNIPER_CASCOR_METRICS_ENABLED=true \
            JUNIPER_CASCOR_AUTO_START=false \
            JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false \
            JUNIPER_CASCOR_LOG_LEVEL=INFO \
            JUNIPER_CASCOR_SNAPSHOTS_DIR="${RUN_DIR}/snapshots" \
            JUNIPER_CASCOR_LOG_DIR="${LOG_DIR}" \
            JUNIPER_DATA_URL="${DATA_URL}" \
            JUNIPER_CASCOR_RUN_ID="${RUN_ID:-}" \
            JUNIPER_CASCOR_EXPERIMENT="${JUNIPER_CASCOR_EXPERIMENT:-${EXPERIMENT:-}}" \
            JUNIPER_CASCOR_CELL_ID="${JUNIPER_CASCOR_CELL_ID:-}" \
            JUNIPER_CASCOR_DATASET_ID="${JUNIPER_CASCOR_DATASET_ID:-}" \
            JUNIPER_CASCOR_GIT_SHA="${git_sha}" \
            JUNIPER_CASCOR_CONFIG_FILE="${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}" \
            nohup env "${runtime_env[@]}" "${uvicorn_bin}" api.app:create_app --factory --host 127.0.0.1 --port "${CASCOR_PORT}" >"${LOG_DIR}/juniper-cascor.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6.
    wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" "${HEALTH_TIMEOUT}" "api.app:create_app .*--port ${CASCOR_PORT}" || return 1
    record_listener_pid "juniper-cascor" "${CASCOR_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Bring-up: juniper-recurrence (console script, plan §6.1)
###########################################################################################################################################################################################################
recurrence_up() {
    local serve_bin python_bin snapshots_dir config_env="" skip_flag="" log_announce="" model_version="" _lv
    local -a log_env=()
    # W1.9: what model_version records. util/experiments/run_experiment.py runs the same probe
    # (RECURRENCE_MODEL_VERSION_PROBE) against the save_model re-run's interpreter.
    local model_version_probe='from importlib.metadata import version; print(version("juniper-recurrence-model"))'
    serve_bin="$(env_bin "${RECURRENCE_CONDA}" juniper-recurrence)"
    # The preflight must judge the interpreter `serve` actually runs under (console_script_python).
    python_bin="$(console_script_python "${serve_bin}" "$(env_bin "${RECURRENCE_CONDA}" python)")"
    # W1.10 (F-D9): the run's own snapshots dir, which create_run_dir makes for both apps (cascor
    # lists only *.h5 there, recurrence only *.npz).
    snapshots_dir="${RUN_DIR}/snapshots"
    # W1.10 (F-L11): the two log knobs, named only when this launcher's environment sets them -- an
    # array, not a `VAR=${VAR:-}` prefix, for the reason cascor_up gives for runtime_env: an EMPTY
    # value is not an unset one. They reached serve by inheritance already; naming them records them
    # (announce line, env/launch.env, ports.json). A `service:` key in the staged config still
    # outranks both (header: RECURRENCE SERVICE ENV).
    for _lv in JUNIPER_RECURRENCE_LOG_LEVEL JUNIPER_RECURRENCE_LOG_FORMAT; do
        if [[ -n "${!_lv:-}" ]]; then log_env+=("${_lv}=${!_lv}"); fi
    done
    if [[ ${#log_env[@]} -gt 0 ]]; then log_announce="${log_env[*]} "; fi
    [[ -n "${CONFIG_PATH}" ]] && config_env="JUNIPER_RECURRENCE_CONFIG_FILE=${RUN_DIR}/config/experiment.yaml "
    [[ "${SKIP_ENV_PREFLIGHT}" == "1" ]] && skip_flag=" --skip"
    banner "juniper-recurrence  ->  http://127.0.0.1:${RECURRENCE_PORT}  (${RECURRENCE_CONDA})"
    announce "bash ${ENV_PREFLIGHT} --python ${python_bin}${skip_flag}   # W0.2 recurrence env preflight: a finding refuses the leg; report -> ${LOG_DIR}/launch.log"
    announce "cd / && ${python_bin} -c '${model_version_probe}'   # W1.9 model_version (no -s: serve imports without it); then ports.json gains recurrence_launch (cli=${serve_bin})"
    announce "cd ${RUN_DIR} && JUNIPER_RECURRENCE_METRICS_ENABLED=true JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false JUNIPER_RECURRENCE_SNAPSHOTS_DIR=${snapshots_dir} JUNIPER_DATA_URL=${DATA_URL} ${log_announce}${config_env}${serve_bin} serve --host 127.0.0.1 --port ${RECURRENCE_PORT}   # nohup -> ${LOG_DIR}/juniper-recurrence.log"
    if is_dry; then return 0; fi

    # See data_up: ``recurrence_up || failed=1`` disables set -e inside this body.
    require_env_bin "${RECURRENCE_CONDA}" juniper-recurrence || return 1
    ensure_dir "${LOG_DIR}"
    # W0.2 (F-E2): refuse a stale env HERE, before serve. Readiness cannot: a stale model passes
    # /v1/health/ready and then fails every split="full" request (F-E1).
    run_env_preflight "${python_bin}" || return 1
    # W1.9: the model version serve will import -- without -s and from /, as a console script runs
    # (the preflight's -s is right for judging the env; serve does not pass it). Best-effort: output
    # that is not one version-shaped token records null, and the driver then reports model-version
    # parity as unverified instead of guessing.
    model_version="$(cd / && "${python_bin}" -c "${model_version_probe}" 2>/dev/null)" || model_version=""
    [[ "${model_version}" =~ ^[A-Za-z0-9.+!_-]+$ ]] || model_version=""
    record_launch_env "juniper-recurrence" \
        "JUNIPER_RECURRENCE_METRICS_ENABLED=true" \
        "JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false" \
        "JUNIPER_RECURRENCE_SNAPSHOTS_DIR=${snapshots_dir}" \
        "JUNIPER_DATA_URL=${DATA_URL}" \
        "JUNIPER_RECURRENCE_CONFIG_FILE=${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}" \
        "${log_env[@]}"
    # W1.9 (F-D4): record the resolved leg for run_experiment.py's save_model re-run. Fail closed: a
    # run that cannot record its launch would silently fall back to the driver's PATH.
    RECURRENCE_LAUNCH_JSON="$(recurrence_launch_json "${RECURRENCE_CONDA}" "${serve_bin}" "${python_bin}" "${model_version}" "${snapshots_dir}" "${JUNIPER_RECURRENCE_LOG_LEVEL:-}" "${JUNIPER_RECURRENCE_LOG_FORMAT:-}" "${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}")"
    write_ports_json || {
        log_launch "ERROR: could not record the recurrence launch in ${RUN_DIR}/ports.json; serve NOT started."
        return 1
    }
    if [[ "${CONDA_ACTIVATE}" == "1" ]]; then activate_conda "${RECURRENCE_CONDA}" || return 1; fi
    (
        cd "${RUN_DIR}" || exit 1
        # `env` adds only the log vars that are set (log_env); it execs nohup, which execs serve.
        JUNIPER_RECURRENCE_METRICS_ENABLED=true \
            JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false \
            JUNIPER_RECURRENCE_SNAPSHOTS_DIR="${snapshots_dir}" \
            JUNIPER_DATA_URL="${DATA_URL}" \
            JUNIPER_RECURRENCE_CONFIG_FILE="${CONFIG_PATH:+${RUN_DIR}/config/experiment.yaml}" \
            env "${log_env[@]}" nohup "${serve_bin}" serve --host 127.0.0.1 --port "${RECURRENCE_PORT}" >"${LOG_DIR}/juniper-recurrence.log" 2>&1 &
    )
    # No `$!` here on purpose — F-6.
    wait_for_health "juniper-recurrence" "http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready" "${HEALTH_TIMEOUT}" "juniper-recurrence serve .*--port ${RECURRENCE_PORT}" || return 1
    record_listener_pid "juniper-recurrence" "${RECURRENCE_PORT}" || return 1
}


###########################################################################################################################################################################################################
# Grafana bridge (OPT-IN, plan §7.2 / §7.3) — socat relays + the file_sd target file
###########################################################################################################################################################################################################
# Discover the gateway IP the relays bind. The monitoring network is found by SUFFIX, never
# by a hard-coded compose project name: a stack launched from a worktree renames the network
# (<project>_monitoring), while the pinned ipam keeps the gateway constant.
discover_gateway_ip() {
    local net ip
    GATEWAY_IP=""
    net="$(docker network ls --format '{{.Name}}' 2>/dev/null | grep -E '_monitoring$' | head -n1 || true)"
    if [[ -n "${net}" ]]; then
        ip="$(docker network inspect "${net}" --format '{{range .IPAM.Config}}{{.Gateway}} {{end}}' 2>/dev/null | awk '{print $1}' || true)"
        if [[ -n "${ip}" ]]; then
            GATEWAY_IP="${ip}"
            log "Monitoring network '${net}' gateway: ${GATEWAY_IP}"
            return 0
        fi
    fi
    ip="$(docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}} {{end}}' 2>/dev/null | awk '{print $1}' || true)"
    if [[ -z "${ip}" ]]; then
        log "ERROR: no monitoring network and no default-bridge gateway — cannot start the Grafana bridge"
        return 1
    fi
    GATEWAY_IP="${ip}"
    log "WARNING: no '*_monitoring' docker network found — falling back to the DEFAULT BRIDGE gateway ${GATEWAY_IP}."
    log "WARNING: prometheus maps host.docker.internal to the MONITORING gateway explicitly (F-2), so scrapes will NOT land until the observability stack is up."
}

relay_up() {
    local svc="$1" port="$2"
    announce "socat \"TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr\" \"TCP:127.0.0.1:${port}\"   # ${svc} relay -> ${RUN_DIR}/relays/${svc}.pid"
    if is_dry; then return 0; fi
    ensure_dir "${RUN_DIR}/relays"
    # socat is exec'd directly (no `cd &&` subshell), so `$!` IS the relay process here —
    # the F-6 wrapper-pid class does not apply. The relay also never binds 127.0.0.1, so
    # `ss -tlnpH "sport = :<port>"` could not disambiguate it from the app anyway.
    nohup socat "TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr" "TCP:127.0.0.1:${port}" >"${LOG_DIR}/relay-${svc}.log" 2>&1 &
    printf '%s\n' "$!" >"${RUN_DIR}/relays/${svc}.pid"
    proc_cmdline "$!" >"${RUN_DIR}/relays/${svc}.cmdline"
    log "${svc}: relay pid $(cat "${RUN_DIR}/relays/${svc}.pid") on ${GATEWAY_IP}:${port}"
}

# The §7.2 target file: one entry per scraped service, four labels, run-scoped.
render_target_file() {
    local first=1 entry svc port
    printf '[\n'
    for entry in "${SCRAPE_TARGETS[@]:-}"; do
        [[ -n "${entry}" ]] || continue
        svc="${entry%%:*}"
        port="${entry##*:}"
        (( first == 1 )) || printf ',\n'
        first=0
        printf '  {\n'
        printf '    "targets": ["host.docker.internal:%s"],\n' "${port}"
        printf '    "labels": {\n'
        printf '      "service": "%s",\n' "${svc}"
        printf '      "environment": "host-experiment",\n'
        printf '      "run_id": "%s",\n' "${RUN_ID}"
        printf '      "experiment": "%s"\n' "${EXPERIMENT}"
        printf '    }\n'
        printf '  }'
    done
    printf '\n]\n'
}

bridge_up() {
    local entry svc port
    banner "Grafana bridge (opt-in): relays + Prometheus target file"
    # Explicit ``|| return 1``: do_up invokes this as ``if ! bridge_up``, which
    # disables set -e for the whole body (bash conditional rule). Without these
    # checks a missing socat/docker would fall through and still write a target.
    require_cmd socat || return 1
    require_cmd docker || return 1
    if is_dry; then
        GATEWAY_IP="<monitoring-gateway>"
        announce "docker network ls --format '{{.Name}}' | grep -E '_monitoring\$'   # discover the monitoring network by SUFFIX"
    else
        # Explicit ``|| return 1``: callers that invoke bridge_up under ``if ! bridge_up``
        # (OR-list / conditional) disable set -e for this whole body. Without the guard a
        # discover failure leaves GATEWAY_IP empty and falls through to relay_up / target
        # write — a false-green bridge with a broken bind.
        discover_gateway_ip || return 1
    fi
    for entry in "${SCRAPE_TARGETS[@]:-}"; do
        [[ -n "${entry}" ]] || continue
        svc="${entry%%:*}"
        port="${entry##*:}"
        relay_up "${svc}" "${port}" || return 1
    done
    announce "write ${TARGETS_DIR}/${RUN_ID}.json   # file_sd target, labels: service/environment/run_id/experiment"
    if is_dry; then return 0; fi
    ensure_dir "${TARGETS_DIR}"
    render_target_file >"${TARGETS_DIR}/${RUN_ID}.json" || return 1
    render_target_file >"${RUN_DIR}/artifacts/prometheus_target.json" || return 1
    log "Prometheus target file: ${TARGETS_DIR}/${RUN_ID}.json (picked up within refresh_interval)"
}

bridge_down() {
    local pidfile svc pid recorded
    announce "rm -f ${TARGETS_DIR}/${TARGET_RUN_ID}.json   # stop scraping this run"
    if ! is_dry; then
        rm -f "${TARGETS_DIR}/${TARGET_RUN_ID}.json" || true
    fi
    [[ -d "${RUN_DIR}/relays" ]] || return 0
    for pidfile in "${RUN_DIR}"/relays/*.pid; do
        [[ -e "${pidfile}" ]] || continue
        svc="$(basename "${pidfile}" .pid)"
        announce "kill \$(cat ${pidfile})   # ${svc} relay"
        if is_dry; then continue; fi
        pid="$(cat "${pidfile}" 2>/dev/null || true)"
        recorded="$(cat "${RUN_DIR}/relays/${svc}.cmdline" 2>/dev/null || true)"
        kill_verified_pid "${pid}" "relay/${svc}" "${recorded}" || true
        rm -f "${pidfile}" "${RUN_DIR}/relays/${svc}.cmdline" || true
    done
}


###########################################################################################################################################################################################################
# Action: --up
###########################################################################################################################################################################################################
do_up() {
    RUN_ID="$(new_run_id)"
    RUN_DIR="${RUN_ROOT}/${RUN_ID}"
    LOG_DIR="${RUN_DIR}/logs"
    [[ -n "${EXPERIMENT}" ]] || EXPERIMENT="adhoc"

    banner "Bringing UP experiment run ${RUN_ID}"
    if is_dry; then log "DRY-RUN: printing commands only — no dirs, no locks, no processes, no target file"; fi
    log "run dir  : ${RUN_DIR}"
    log "lock root: ${LOCK_ROOT}"

    if ! is_dry; then
        require_cmd ss
        require_cmd curl
        ensure_dir "${RUN_ROOT}"
        ensure_dir "${LOCK_ROOT}"
    fi

    # --- port allocation (§9.3) ------------------------------------------------------
    # release_held_locks on allocate failure: a mid-range exhaustion under set -e used to
    # exit do_up while earlier *.lock dirs stayed behind (30-port ranges starve later --up).
    if [[ -n "${SHARED_DATA_URL}" ]]; then
        DATA_URL="${SHARED_DATA_URL}"
        log "Reusing shared juniper-data at ${DATA_URL} (no per-run data instance)"
    else
        allocate_port "juniper-data" "${DATA_PORT_MIN}" "${DATA_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        DATA_PORT="${ALLOCATED_PORT}"
        DATA_URL="http://127.0.0.1:${DATA_PORT}"
        log "allocated juniper-data port ${DATA_PORT} (range ${DATA_PORT_MIN}-${DATA_PORT_MAX})"
    fi
    if (( WANT_CASCOR == 1 )); then
        allocate_port "juniper-cascor" "${CASCOR_PORT_MIN}" "${CASCOR_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        CASCOR_PORT="${ALLOCATED_PORT}"
        log "allocated juniper-cascor port ${CASCOR_PORT} (range ${CASCOR_PORT_MIN}-${CASCOR_PORT_MAX})"
    fi
    if (( WANT_RECURRENCE == 1 )); then
        allocate_port "juniper-recurrence" "${RECURRENCE_PORT_MIN}" "${RECURRENCE_PORT_MAX}" || {
            release_held_locks
            return 1
        }
        RECURRENCE_PORT="${ALLOCATED_PORT}"
        log "allocated juniper-recurrence port ${RECURRENCE_PORT} (range ${RECURRENCE_PORT_MIN}-${RECURRENCE_PORT_MAX})"
    fi

    SCRAPE_TARGETS=()
    [[ -n "${DATA_PORT}" ]] && SCRAPE_TARGETS+=("juniper-data:${DATA_PORT}")
    [[ -n "${CASCOR_PORT}" ]] && SCRAPE_TARGETS+=("juniper-cascor:${CASCOR_PORT}")
    [[ -n "${RECURRENCE_PORT}" ]] && SCRAPE_TARGETS+=("juniper-recurrence:${RECURRENCE_PORT}")

    # release_held_locks on staging failure: under set -e a missing --config (or mkdir/cp
    # failure) used to exit do_up after allocate_port had already created *.lock dirs, and
    # ports.json was not written yet — so --down cannot recover the locks either. The
    # 30-port experiment ranges then starve later --up attempts until lockdirs are removed
    # by hand (or the runtime dir is reaped).
    create_run_dir || {
        release_held_locks
        return 1
    }
    stage_config || {
        release_held_locks
        return 1
    }
    write_ports_json || {
        release_held_locks
        return 1
    }

    # --- launches, in deterministic order data -> cascor -> recurrence ----------------
    local failed=0
    if [[ -z "${SHARED_DATA_URL}" ]]; then
        data_up || failed=1
    fi
    if (( failed == 0 && WANT_CASCOR == 1 )); then cascor_up || failed=1; fi
    if (( failed == 0 && WANT_RECURRENCE == 1 )); then recurrence_up || failed=1; fi

    if (( failed == 1 )); then
        log "ERROR: bring-up failed — tearing the partial run back down (logs kept under ${LOG_DIR})"
        if ! is_dry; then
            TARGET_RUN_ID="${RUN_ID}"
            teardown_run "${RUN_ID}"
        fi
        return 1
    fi

    # Bridge is post-success: a bare ``bridge_up`` failure under ``set -e`` would
    # abort the script without teardown_run, orphaning the already-healthy stack.
    if (( WANT_BRIDGE == 1 )); then
        if ! bridge_up; then
            log "ERROR: grafana bridge failed — tearing the run back down (logs kept under ${LOG_DIR})"
            if ! is_dry; then
                TARGET_RUN_ID="${RUN_ID}"
                teardown_run "${RUN_ID}"
            fi
            return 1
        fi
    else
        log "Grafana bridge OFF — this run is UNSCRAPED (no relay, no target file). Re-run with --grafana-bridge to publish it."
    fi

    banner "Experiment run ${RUN_ID} is up"
    log "run dir    : ${RUN_DIR}"
    [[ -n "${DATA_PORT}" ]] && log "data       : ${DATA_URL}/v1/health"
    [[ -z "${DATA_PORT}" ]] && log "data       : ${DATA_URL} (shared, not managed by this run)"
    [[ -n "${CASCOR_PORT}" ]] && log "cascor     : http://127.0.0.1:${CASCOR_PORT}/v1/health"
    [[ -n "${RECURRENCE_PORT}" ]] && log "recurrence : http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready"
    log "teardown   : ${SCRIPT_NAME} --down ${RUN_ID}"
}


###########################################################################################################################################################################################################
# Action: --down
###########################################################################################################################################################################################################
# Stop one service: recorded pid FIRST (verified), then kill-by-port as a fallback that is
# confined to the port this run recorded.
stop_service() {
    local svc="$1" port="$2"
    local pidfile="${RUN_DIR}/${svc}.pid"
    local pid recorded fallback_pid
    if [[ -f "${pidfile}" ]]; then
        pid="$(cat "${pidfile}" 2>/dev/null || true)"
        recorded="$(cat "${RUN_DIR}/${svc}.cmdline" 2>/dev/null || true)"
        announce "kill \$(cat ${pidfile})   # ${svc}: recorded listener pid first"
        if ! is_dry; then
            if kill_verified_pid "${pid}" "${svc}" "${recorded}"; then
                rm -f "${pidfile}" "${RUN_DIR}/${svc}.cmdline" || true
            else
                log "${svc}: pidfile path refused — falling back to the recorded port ${port:-none}"
            fi
        fi
    else
        log "${svc}: no pidfile recorded"
    fi

    [[ -n "${port}" ]] || return 0
    announce "kill \$(ss -tlnpH \"sport = :${port}\" | grep -oE 'pid=[0-9]+' | cut -d= -f2)   # ${svc}: fallback, ONLY this run's recorded port"
    if is_dry; then return 0; fi
    fallback_pid="$(port_listener_pid "${port}")"
    if [[ -n "${fallback_pid}" ]]; then
        kill_verified_pid "${fallback_pid}" "${svc} (by port ${port})" "" || true
    fi
    if port_in_use "${port}"; then
        log "WARNING: ${svc}: port ${port} still has a listener after teardown — inspect it before reusing the range"
    fi
}

write_teardown_json() {
    local stopped="$1" ports="$2"
    if is_dry; then return 0; fi
    [[ -d "${RUN_DIR}" ]] || return 0
    cat >"${RUN_DIR}/teardown.json" <<TEARDOWN
{
  "run_id": "${TARGET_RUN_ID}",
  "torn_down_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "services_stopped": [${stopped}],
  "ports_released": [${ports}],
  "target_file_removed": "${TARGETS_DIR}/${TARGET_RUN_ID}.json",
  "artifacts_kept": "${RUN_DIR}/artifacts"
}
TEARDOWN
}

teardown_run() {
    local run_id="$1" ports_file data_port cascor_port recurrence_port stopped=() released=()
    TARGET_RUN_ID="${run_id}"
    RUN_DIR="${RUN_ROOT}/${run_id}"
    LOG_DIR="${RUN_DIR}/logs"
    ports_file="${RUN_DIR}/ports.json"

    banner "Tearing DOWN experiment run ${run_id}"
    if [[ ! -d "${RUN_DIR}" ]]; then
        log "ERROR: no such run dir: ${RUN_DIR}"
        return 1
    fi
    if [[ ! -f "${ports_file}" ]]; then
        log "WARNING: ${run_id} has no ports.json — pidfile-only teardown"
    fi
    data_port="$(read_run_port "${ports_file}" data)"
    cascor_port="$(read_run_port "${ports_file}" cascor)"
    recurrence_port="$(read_run_port "${ports_file}" recurrence)"

    # Relays + target file first: stop publishing before the endpoints disappear.
    bridge_down

    # Reverse of bring-up order: recurrence -> cascor -> data.
    if [[ -n "${recurrence_port}" || -f "${RUN_DIR}/juniper-recurrence.pid" ]]; then
        stop_service "juniper-recurrence" "${recurrence_port}"
        stopped+=("\"juniper-recurrence\"")
    fi
    if [[ -n "${cascor_port}" || -f "${RUN_DIR}/juniper-cascor.pid" ]]; then
        stop_service "juniper-cascor" "${cascor_port}"
        stopped+=("\"juniper-cascor\"")
    fi
    if [[ -n "${data_port}" || -f "${RUN_DIR}/juniper-data.pid" ]]; then
        stop_service "juniper-data" "${data_port}"
        stopped+=("\"juniper-data\"")
    fi

    local port
    for port in "${data_port}" "${cascor_port}" "${recurrence_port}"; do
        [[ -n "${port}" ]] || continue
        release_port_lock "${port}"
        released+=("${port}")
    done

    write_teardown_json "$(join_by , "${stopped[@]:-}")" "$(join_by , "${released[@]:-}")"
    log "Teardown complete for ${run_id}; artifacts kept at ${RUN_DIR}/artifacts (never deleted)"
}

join_by() {
    local sep="$1" out="" item
    shift
    for item in "$@"; do
        [[ -n "${item}" ]] || continue
        if [[ -z "${out}" ]]; then out="${item}"; else out="${out}${sep}${item}"; fi
    done
    printf '%s' "${out}"
}

do_down() {
    local run_dir run_id rc=0
    if (( ALL_MINE == 1 )); then
        if [[ ! -d "${RUN_ROOT}" ]]; then
            log "No run root at ${RUN_ROOT} — nothing to tear down"
            return 0
        fi
        for run_dir in "${RUN_ROOT}"/*/; do
            [[ -d "${run_dir}" ]] || continue
            run_id="$(basename "${run_dir}")"
            [[ "${run_id}" == .* ]] && continue
            teardown_run "${run_id}" || rc=1
        done
        return "${rc}"
    fi
    teardown_run "${TARGET_RUN_ID}"
}


###########################################################################################################################################################################################################
# Action: --status
###########################################################################################################################################################################################################
probe_service() {
    local name="$1" url="$2" port="$3" pidfile="$4" code pid recorded
    announce "curl -s -o /dev/null -w '%{http_code}' ${url}   # ${name}"
    if is_dry; then return 0; fi
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${url}" 2>/dev/null || true)"
    pid="$(port_listener_pid "${port}")"
    recorded="$(cat "${pidfile}" 2>/dev/null || true)"
    log "${name}: health=${code:-000} port=${port} listener_pid=${pid:-none} recorded_pid=${recorded:-none}"
}

status_run() {
    local run_id="$1" ports_file data_port cascor_port recurrence_port bridge data_url
    RUN_DIR="${RUN_ROOT}/${run_id}"
    ports_file="${RUN_DIR}/ports.json"
    banner "Experiment run ${run_id}"
    if [[ ! -d "${RUN_DIR}" ]]; then
        log "ERROR: no such run dir: ${RUN_DIR}"
        return 1
    fi
    data_port="$(read_run_port "${ports_file}" data)"
    cascor_port="$(read_run_port "${ports_file}" cascor)"
    recurrence_port="$(read_run_port "${ports_file}" recurrence)"
    bridge="$(read_run_flag "${ports_file}" grafana_bridge)"
    data_url="$(sed -n 's/^[[:space:]]*"data_url"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' "${ports_file}" 2>/dev/null | head -n1 || true)"

    log "run dir: ${RUN_DIR}"
    [[ -n "${data_port}" ]] && probe_service "juniper-data" "http://127.0.0.1:${data_port}/v1/health" "${data_port}" "${RUN_DIR}/juniper-data.pid"
    [[ -z "${data_port}" && -n "${data_url}" ]] && log "juniper-data: shared instance at ${data_url} (not managed by this run)"
    [[ -n "${cascor_port}" ]] && probe_service "juniper-cascor" "http://127.0.0.1:${cascor_port}/v1/health" "${cascor_port}" "${RUN_DIR}/juniper-cascor.pid"
    [[ -n "${recurrence_port}" ]] && probe_service "juniper-recurrence" "http://127.0.0.1:${recurrence_port}/v1/health/ready" "${recurrence_port}" "${RUN_DIR}/juniper-recurrence.pid"

    if [[ "${bridge}" == "true" && -f "${TARGETS_DIR}/${run_id}.json" ]]; then
        log "scrape: PUBLISHED — ${TARGETS_DIR}/${run_id}.json"
    elif [[ "${bridge}" == "true" ]]; then
        log "scrape: bridge was requested but ${TARGETS_DIR}/${run_id}.json is MISSING — this run is UNSCRAPED"
    else
        log "scrape: DISABLED — this run is UNSCRAPED (no Grafana bridge; re-run --up with --grafana-bridge)"
    fi
}

do_status() {
    local run_dir run_id rc=0
    if [[ -n "${TARGET_RUN_ID}" ]]; then
        status_run "${TARGET_RUN_ID}"
        return $?
    fi
    banner "Experiment runs under ${RUN_ROOT}"
    if [[ ! -d "${RUN_ROOT}" ]]; then
        log "No run root at ${RUN_ROOT} — no runs recorded"
        return 0
    fi
    for run_dir in "${RUN_ROOT}"/*/; do
        [[ -d "${run_dir}" ]] || continue
        run_id="$(basename "${run_dir}")"
        [[ "${run_id}" == .* ]] && continue
        status_run "${run_id}" || rc=1
    done
    return "${rc}"
}


###########################################################################################################################################################################################################
# Argument parsing
###########################################################################################################################################################################################################
set_action() {
    if [[ -n "${ACTION}" ]]; then
        log "ERROR: choose exactly one of --up / --down / --status"
        usage
        exit 2
    fi
    ACTION="$1"
}

need_value() {
    local flag="$1" value="${2-}"
    if [[ -z "${value}" || "${value}" == --* ]]; then
        log "ERROR: ${flag} requires a value"
        usage
        exit 2
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --up) set_action up ;;
        --down) set_action down ;;
        --status) set_action status ;;
        --cascor) WANT_CASCOR=1 ;;
        --recurrence) WANT_RECURRENCE=1 ;;
        --grafana-bridge) WANT_BRIDGE=1 ;;
        --skip-env-preflight) SKIP_ENV_PREFLIGHT=1 ;;
        --all-mine) ALL_MINE=1 ;;
        --dry-run) DRY_RUN=1 ;;
        --config)
            need_value "--config" "${2-}"
            CONFIG_PATH="$2"
            shift
            ;;
        --experiment)
            need_value "--experiment" "${2-}"
            EXPERIMENT="$2"
            shift
            ;;
        --shared-data)
            need_value "--shared-data" "${2-}"
            SHARED_DATA_URL="$2"
            shift
            ;;
        --run-id)
            need_value "--run-id" "${2-}"
            TARGET_RUN_ID="$2"
            shift
            ;;
        --help | -h) usage; exit 0 ;;
        -*)
            log "ERROR: unknown argument '$1'"
            usage
            exit 2
            ;;
        *)
            if [[ -n "${TARGET_RUN_ID}" ]]; then
                log "ERROR: unexpected extra argument '$1'"
                usage
                exit 2
            fi
            TARGET_RUN_ID="$1"
            ;;
    esac
    shift
done

if [[ -z "${ACTION}" ]]; then
    log "ERROR: no action given (--up / --down / --status)"
    usage
    exit 2
fi

if [[ "${ACTION}" == "up" ]]; then
    if (( WANT_CASCOR == 0 && WANT_RECURRENCE == 0 )); then
        log "ERROR: --up needs at least one app selector (--cascor and/or --recurrence)"
        usage
        exit 2
    fi
    if [[ -n "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --up allocates its own run id; '${TARGET_RUN_ID}' is not accepted"
        usage
        exit 2
    fi
    if [[ -n "${CONFIG_PATH}" && -z "${EXPERIMENT}" ]]; then
        EXPERIMENT="$(basename "${CONFIG_PATH}")"
        EXPERIMENT="${EXPERIMENT%.*}"
    fi
fi

if [[ "${ACTION}" == "down" ]]; then
    if (( ALL_MINE == 0 )) && [[ -z "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --down needs a RUN_ID (or --all-mine)"
        usage
        exit 2
    fi
    if (( ALL_MINE == 1 )) && [[ -n "${TARGET_RUN_ID}" ]]; then
        log "ERROR: --down takes a RUN_ID or --all-mine, not both"
        usage
        exit 2
    fi
fi

case "${ACTION}" in
    up) do_up ;;
    down) do_down ;;
    status) do_status ;;
esac
