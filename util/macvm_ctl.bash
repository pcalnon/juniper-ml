#!/usr/bin/env bash
# Start, stop or inspect turing's k8s worker VM behind the G-MEM memory gate.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-17
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task F5a;
#             D1, D7; gate G-MEM in §9.3; regression R-F5); tests/test_macvm_ctl.py
#
# turing has 16 GiB of soldered RAM and was 13.7 of 15.4 GB into swap at probe time (plan §2.1).
# D1 sizes the VM at 4 vCPU / 6 GiB, node mode only, and falls back to admin-only whenever G-MEM
# fails. So `start` evaluates G-MEM first and never calls `VBoxManage startvm` unless all three
# conditions hold:
#   memory  free + inactive >= VM memory + reserve (default 6 GiB + 4 GiB)
#   swap    swap used <= the limit (default 2 GiB)
#   docker  Docker Desktop is not running (D7: its own VM takes 2-4 GB)
# F7 runs `start` from a LaunchDaemon, so start is non-interactive and idempotent.
#
# Memory accounting (vm_stat). The page size comes from the header ("page size of N bytes": 4096
# on Intel, 16384 on arm64). free = "Pages free" + "Pages speculative": vm_stat prints the kernel's
# free count minus the speculative pages, which are read-ahead file cache and reclaimed first.
# inactive = "Pages inactive". Purgeable, file-backed and compressor pages are not added: they
# overlap those queues or are not reclaimable at once, so leaving them out errs toward macOS. The
# gate's VM size is the larger of --vm-mem-gib and the VM's configured memory (showvminfo
# memory=), so a VM resized later cannot slip past a stale default. All arithmetic is integer MiB:
# available memory rounds down and swap used rounds up, so each comparison against an integer-MiB
# threshold is exact and never rounds in the VM's favour.
#
# Docker Desktop counts as running when `pgrep -x` finds any of com.docker.backend (the engine
# backend), "Docker Desktop" (the app) or Docker (the 2021-era main process, still on turing).
# com.docker.vmnetd is deliberately not probed: it is a privileged launchd helper that stays up
# after Docker Desktop quits.
#
# Usage:
#   bash util/macvm_ctl.bash {start|stop|status} [--vm NAME] [--vm-mem-gib N] [--reserve-gib N]
#        [--max-swap-gib N] [--timeout SECONDS] [--force] [--dry-run]
#
# Exit codes:
#   0 -- start: started, or already running; stop: powered off, or was not running; status: the
#        report printed, even when G-MEM fails; --dry-run: the real run would succeed
#   1 -- start: G-MEM failed (startvm never called) or startvm failed; stop: still running at the
#        timeout without --force, or the ACPI request or the forced poweroff failed
#   2 -- usage or environment: a bad argument, VBoxManage missing, the VM not registered for this
#        user, a VM state start cannot act on, or a G-MEM input that cannot be measured (start
#        fails closed). status exits 2 for the environment cases too, but only after printing
#        the whole G-MEM evaluation: before F4 creates the VM it is still the headroom reading.
#
# Environment:
#   VBOXMANAGE, VM_STAT, SYSCTL, PGREP -- tool paths (defaults /usr/local/bin/VBoxManage,
#       /usr/bin/vm_stat, /usr/sbin/sysctl, /usr/bin/pgrep). Absolute because launchd's PATH (F7)
#       lacks /usr/local/bin; tests override them.
#   POLL_INTERVAL -- seconds between VMState polls while stop waits (default 5; tests use 0)
set -euo pipefail

VBOXMANAGE="${VBOXMANAGE:-/usr/local/bin/VBoxManage}"
VM_STAT="${VM_STAT:-/usr/bin/vm_stat}"
SYSCTL="${SYSCTL:-/usr/sbin/sysctl}"
PGREP="${PGREP:-/usr/bin/pgrep}"
POLL_INTERVAL="${POLL_INTERVAL:-5}"

usage() {
    cat <<'EOF'
Usage: macvm_ctl.bash {start|stop|status} [options]

Gated lifecycle for the k8s worker VM (VirtualBox, headless). start refuses unless
G-MEM passes:
  memory  vm_stat free + speculative + inactive >= VM memory + reserve
  swap    sysctl vm.swapusage used <= the swap limit
  docker  Docker Desktop not running (pgrep -x com.docker.backend, "Docker Desktop", Docker)

Commands:
  start   start the VM headless if G-MEM passes; exit 0 if it is already running
  stop    press the ACPI power button, then wait for the VM to power off
  status  print VMState and the full G-MEM evaluation (read-only)

Options:
  --vm NAME           VM name or UUID (default: juniper-macvm)
  --vm-mem-gib N      VM memory for the gate, GiB (default: 6); the VM's configured
                      memory is used instead when it is larger
  --reserve-gib N     headroom macOS keeps on top of the VM, GiB (default: 4)
  --max-swap-gib N    most swap in use that still passes, GiB (default: 2)
  --timeout SECONDS   stop: how long to wait for the power-off (default: 120)
  --force             stop: power the VM off hard after the timeout
  --dry-run           start, stop: print the gate result and the commands; change nothing
  -h, --help          show this help

Environment: VBOXMANAGE, VM_STAT, SYSCTL, PGREP override the tool paths;
POLL_INTERVAL (default 5) sets stop's poll period in seconds.

Exit codes: 0 OK (status: printed, even when G-MEM fails); 1 G-MEM failed, startvm
failed, or stop timed out; 2 usage or environment error (VBoxManage missing, VM not
registered, a G-MEM input that cannot be measured).
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

CMD=""
VM="juniper-macvm"
VM_MEM_GIB=6
RESERVE_GIB=4
MAX_SWAP_GIB=2
TIMEOUT=120
TIMEOUT_SET=0
FORCE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        --vm)
            [[ -n "${2:-}" ]] || die_usage "--vm needs a name"
            VM="$2"
            shift 2
            ;;
        --vm-mem-gib)
            [[ -n "${2:-}" ]] || die_usage "--vm-mem-gib needs a value"
            VM_MEM_GIB="$2"
            shift 2
            ;;
        --reserve-gib)
            [[ -n "${2:-}" ]] || die_usage "--reserve-gib needs a value"
            RESERVE_GIB="$2"
            shift 2
            ;;
        --max-swap-gib)
            [[ -n "${2:-}" ]] || die_usage "--max-swap-gib needs a value"
            MAX_SWAP_GIB="$2"
            shift 2
            ;;
        --timeout)
            [[ -n "${2:-}" ]] || die_usage "--timeout needs a number of seconds"
            TIMEOUT="$2"
            TIMEOUT_SET=1
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -*)
            die_usage "unknown option: $1"
            ;;
        *)
            [[ -z "$CMD" ]] || die_usage "one command per run (got '$CMD' and '$1')"
            CMD="$1"
            shift
            ;;
    esac
done

case "$CMD" in
    start | stop | status) ;;
    "") die_usage "no command given (start, stop or status)" ;;
    *) die_usage "unknown command: '$CMD' (expected start, stop or status)" ;;
esac

# Whole numbers without a leading zero, so bash arithmetic never reads them as octal.
int_re='^(0|[1-9][0-9]{0,5})$'
check_int() {
    [[ "$2" =~ $int_re ]] || die_usage "$1 needs a whole number (got '$2')"
    [[ "$2" -ge "$3" ]] || die_usage "$1 must be at least $3 (got '$2')"
}
vm_re='^[A-Za-z0-9][A-Za-z0-9._-]*$'
[[ "$VM" =~ $vm_re ]] || die_usage "not a VM name or UUID: '$VM'"
check_int --vm-mem-gib "$VM_MEM_GIB" 1
check_int --reserve-gib "$RESERVE_GIB" 0
check_int --max-swap-gib "$MAX_SWAP_GIB" 0
check_int --timeout "$TIMEOUT" 0
[[ "$POLL_INTERVAL" =~ $int_re ]] || die_usage "POLL_INTERVAL must be a whole number of seconds (got '$POLL_INTERVAL')"
if [[ "$CMD" != "stop" ]]; then
    [[ "$TIMEOUT_SET" -eq 0 ]] || die_usage "--timeout applies to stop only"
    [[ "$FORCE" -eq 0 ]] || die_usage "--force applies to stop only"
fi

# A command line, each word shell-quoted, so a printed command can be pasted.
render() {
    local out="" word
    for word in "$@"; do
        out="${out:+$out }$(printf '%q' "$word")"
    done
    printf '%s\n' "$out"
}

indent() {
    local line
    while IFS= read -r line; do
        printf '    %s\n' "$line"
    done <<<"$1"
}

# VirtualBox VMState values in which the VM process is down and its memory released.
is_off_state() {
    case "$1" in
        poweroff | saved | aborted | aborted-saved | teleported) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------------------------------------------------------------------------------------------
# VM state: VMState="..." (and memory=<MiB>) from `showvminfo --machinereadable`, a read-only call.
# ---------------------------------------------------------------------------------------------
VM_STATE=""
VM_CONF_MIB=""
VBOX_OUT=""
VBOX_PROBLEM=""

query_vm() {
    local rc=0
    VM_STATE=""
    VM_CONF_MIB=""
    if ! command -v "$VBOXMANAGE" >/dev/null 2>&1; then
        VBOX_PROBLEM="missing"
        return 1
    fi
    VBOX_OUT="$("$VBOXMANAGE" showvminfo "$VM" --machinereadable 2>&1)" || rc=$?
    if [[ "$rc" -ne 0 ]]; then
        case "$VBOX_OUT" in
            *"Could not find a registered machine"*) VBOX_PROBLEM="unregistered" ;;
            *) VBOX_PROBLEM="exited ${rc}" ;;
        esac
        return 1
    fi
    VM_STATE="$(printf '%s\n' "$VBOX_OUT" | awk -F'"' '$1 == "VMState=" && !seen { print $2; seen = 1 }')"
    VM_CONF_MIB="$(printf '%s\n' "$VBOX_OUT" | awk -F= '$1 == "memory" && !seen { print $2; seen = 1 }')"
    if [[ -z "$VM_STATE" ]]; then
        VBOX_PROBLEM="printed no VMState line"
        return 1
    fi
    return 0
}

# One line for status; the detail goes to stderr.
vm_problem_summary() {
    case "$VBOX_PROBLEM" in
        missing) echo "unknown (VBoxManage not found: ${VBOXMANAGE})" ;;
        unregistered) echo "not registered for user $(id -un 2>/dev/null || echo '?')" ;;
        *) echo "unknown (showvminfo ${VBOX_PROBLEM})" ;;
    esac
}

vm_problem_detail() {
    case "$VBOX_PROBLEM" in
        missing)
            echo "ERROR: VBoxManage not found or not executable: ${VBOXMANAGE} (set VBOXMANAGE to its path)." >&2
            ;;
        unregistered)
            echo "ERROR: VM '${VM}' is not registered with VirtualBox for user $(id -un 2>/dev/null || echo '?')." >&2
            echo "VirtualBox keeps one registry per user (F7 runs as pcalnon, not root). VBoxManage said:" >&2
            indent "$VBOX_OUT" >&2
            ;;
        *)
            echo "ERROR: '$(render "$VBOXMANAGE" showvminfo "$VM" --machinereadable)' ${VBOX_PROBLEM}:" >&2
            indent "$VBOX_OUT" >&2
            ;;
    esac
}

# ---------------------------------------------------------------------------------------------
# G-MEM inputs. Each measure_* returns non-zero when its input cannot be measured; the gate then
# reports UNKNOWN for that condition and fails closed.
# ---------------------------------------------------------------------------------------------
measure_memory() {
    local out rc=0 parsed v count_re='^[0-9]{1,11}$' size_re='^[1-9][0-9]{0,5}$'
    MEM_ERR=""
    out="$("$VM_STAT" 2>&1)" || rc=$?
    if [[ "$rc" -ne 0 ]]; then
        MEM_ERR="'${VM_STAT}' exited ${rc}: ${out%%$'\n'*}"
        return 1
    fi
    parsed="$(printf '%s\n' "$out" | awk '
        function count(v) { sub(/\.$/, "", v); return v }
        /^Mach Virtual Memory Statistics:/ && ps == "" { for (i = 1; i < NF; i++) if ($i == "of") ps = $(i + 1) }
        $1 == "Pages" && $2 == "free:" { free = count($3) }
        $1 == "Pages" && $2 == "speculative:" { spec = count($3) }
        $1 == "Pages" && $2 == "inactive:" { inact = count($3) }
        END { printf "%s %s %s %s\n", (ps == "" ? "-" : ps), (free == "" ? "-" : free), (spec == "" ? "-" : spec), (inact == "" ? "-" : inact) }')"
    read -r MEM_PAGE_SIZE MEM_FREE_PAGES MEM_SPEC_PAGES MEM_INACTIVE_PAGES <<<"$parsed"
    if [[ ! "$MEM_PAGE_SIZE" =~ $size_re ]]; then
        MEM_ERR="no 'page size of N bytes' header in ${VM_STAT} output"
        return 1
    fi
    for v in "$MEM_FREE_PAGES" "$MEM_SPEC_PAGES" "$MEM_INACTIVE_PAGES"; do
        if [[ ! "$v" =~ $count_re ]]; then
            MEM_ERR="${VM_STAT} output lacks a 'Pages free', 'Pages speculative' or 'Pages inactive' count"
            return 1
        fi
    done
    FREE_PAGES=$((10#$MEM_FREE_PAGES + 10#$MEM_SPEC_PAGES))
    FREE_MIB=$((FREE_PAGES * MEM_PAGE_SIZE / 1048576))
    INACTIVE_MIB=$((10#$MEM_INACTIVE_PAGES * MEM_PAGE_SIZE / 1048576))
    AVAIL_MIB=$(((FREE_PAGES + 10#$MEM_INACTIVE_PAGES) * MEM_PAGE_SIZE / 1048576))
    return 0
}

measure_swap() {
    local out rc=0 ip fp unit scale digits n swap_re='^([0-9]{1,9})(\.([0-9]{1,6}))?([KMG])$'
    SWAP_ERR=""
    out="$("$SYSCTL" vm.swapusage 2>&1)" || rc=$?
    if [[ "$rc" -ne 0 ]]; then
        SWAP_ERR="'${SYSCTL} vm.swapusage' exited ${rc}: ${out%%$'\n'*}"
        return 1
    fi
    SWAP_RAW="$(printf '%s\n' "$out" | awk '{ for (i = 1; i <= NF - 2; i++) if ($i == "used" && $(i + 1) == "=" && tok == "") tok = $(i + 2) } END { print tok }')"
    if [[ ! "$SWAP_RAW" =~ $swap_re ]]; then
        SWAP_ERR="no 'used = <number>K|M|G' in: ${out%%$'\n'*}"
        return 1
    fi
    ip="${BASH_REMATCH[1]}"
    fp="${BASH_REMATCH[3]}"
    unit="${BASH_REMATCH[4]}"
    # n = the value times scale, exactly; then round up to whole MiB.
    scale=1
    digits=${#fp}
    while [[ "$digits" -gt 0 ]]; do
        scale=$((scale * 10))
        digits=$((digits - 1))
    done
    n=$((10#$ip * scale + 10#${fp:-0}))
    case "$unit" in
        K) SWAP_USED_MIB=$(((n + 1024 * scale - 1) / (1024 * scale))) ;;
        M) SWAP_USED_MIB=$(((n + scale - 1) / scale)) ;;
        G) SWAP_USED_MIB=$(((n * 1024 + scale - 1) / scale)) ;;
    esac
    return 0
}

measure_docker() {
    local name pids rc
    DOCKER_HITS=""
    DOCKER_ERR=""
    for name in com.docker.backend "Docker Desktop" Docker; do
        rc=0
        pids="$("$PGREP" -x "$name" 2>/dev/null)" || rc=$?
        case "$rc" in
            0) DOCKER_HITS="${DOCKER_HITS:+$DOCKER_HITS, }${name} (pid ${pids//$'\n'/ })" ;;
            1) ;;
            *)
                DOCKER_ERR="'${PGREP} -x ${name}' exited ${rc}"
                return 1
                ;;
        esac
    done
    return 0
}

# ---------------------------------------------------------------------------------------------
# G-MEM: print every input and every condition; leave the counts in GATE_FAILED / GATE_UNKNOWN
# and one line per failed or unmeasured condition in GATE_REASONS.
# ---------------------------------------------------------------------------------------------
report_condition() {
    printf '  %-7s %s: %s\n' "$1" "$2" "$3"
    case "$1" in
        FAIL) GATE_FAILED=$((GATE_FAILED + 1)) ;;
        UNKNOWN) GATE_UNKNOWN=$((GATE_UNKNOWN + 1)) ;;
        *) return 0 ;;
    esac
    GATE_REASONS="${GATE_REASONS}  $2: $3"$'\n'
}

evaluate_gate() {
    local mib_re='^[0-9]{1,9}$' vm_src mem_verdict mem_text swap_verdict swap_text docker_verdict docker_text
    VM_MIB=$((VM_MEM_GIB * 1024))
    vm_src="--vm-mem-gib ${VM_MEM_GIB}"
    if [[ "$VM_CONF_MIB" =~ $mib_re ]] && [[ $((10#$VM_CONF_MIB)) -gt "$VM_MIB" ]]; then
        VM_MIB=$((10#$VM_CONF_MIB))
        vm_src="the VM's configured memory, larger than --vm-mem-gib ${VM_MEM_GIB}"
    fi
    RESERVE_MIB=$((RESERVE_GIB * 1024))
    NEED_MIB=$((VM_MIB + RESERVE_MIB))
    MAX_SWAP_MIB=$((MAX_SWAP_GIB * 1024))
    GATE_FAILED=0
    GATE_UNKNOWN=0
    GATE_REASONS=""

    echo "G-MEM inputs:"
    if measure_memory; then
        printf '  %-15s %s\n' "page size" "${MEM_PAGE_SIZE} B (vm_stat header)"
        printf '  %-15s %s\n' "free" "${FREE_PAGES} pages = ${FREE_MIB} MiB (Pages free ${MEM_FREE_PAGES} + Pages speculative ${MEM_SPEC_PAGES})"
        printf '  %-15s %s\n' "inactive" "${MEM_INACTIVE_PAGES} pages = ${INACTIVE_MIB} MiB (Pages inactive)"
        if [[ "$AVAIL_MIB" -ge "$NEED_MIB" ]]; then
            mem_verdict=PASS
            mem_text="free + inactive ${AVAIL_MIB} MiB >= ${NEED_MIB} MiB required (VM ${VM_MIB} MiB + reserve ${RESERVE_MIB} MiB)"
        else
            mem_verdict=FAIL
            mem_text="free + inactive ${AVAIL_MIB} MiB < ${NEED_MIB} MiB required (VM ${VM_MIB} MiB + reserve ${RESERVE_MIB} MiB)"
        fi
    else
        printf '  %-15s %s\n' "vm_stat" "UNMEASURED: ${MEM_ERR}"
        mem_verdict=UNKNOWN
        mem_text="cannot measure free + inactive: ${MEM_ERR}"
    fi
    printf '  %-15s %s\n' "VM memory" "${VM_MIB} MiB (${vm_src})"
    printf '  %-15s %s\n' "reserve" "${RESERVE_MIB} MiB (--reserve-gib ${RESERVE_GIB})"
    if measure_swap; then
        printf '  %-15s %s\n' "swap used" "${SWAP_USED_MIB} MiB (vm.swapusage used = ${SWAP_RAW}, rounded up)"
        if [[ "$SWAP_USED_MIB" -le "$MAX_SWAP_MIB" ]]; then
            swap_verdict=PASS
            swap_text="used ${SWAP_USED_MIB} MiB <= ${MAX_SWAP_MIB} MiB allowed"
        else
            swap_verdict=FAIL
            swap_text="used ${SWAP_USED_MIB} MiB > ${MAX_SWAP_MIB} MiB allowed"
        fi
    else
        printf '  %-15s %s\n' "swap used" "UNMEASURED: ${SWAP_ERR}"
        swap_verdict=UNKNOWN
        swap_text="cannot measure swap used: ${SWAP_ERR}"
    fi
    printf '  %-15s %s\n' "swap limit" "${MAX_SWAP_MIB} MiB (--max-swap-gib ${MAX_SWAP_GIB})"
    if measure_docker; then
        if [[ -z "$DOCKER_HITS" ]]; then
            printf '  %-15s %s\n' "Docker Desktop" "not running (pgrep -x com.docker.backend, \"Docker Desktop\", Docker)"
            docker_verdict=PASS
            docker_text="Docker Desktop is not running"
        else
            printf '  %-15s %s\n' "Docker Desktop" "running: ${DOCKER_HITS}"
            docker_verdict=FAIL
            docker_text="Docker Desktop is running: ${DOCKER_HITS}; quit it before node mode (D7)"
        fi
    else
        printf '  %-15s %s\n' "Docker Desktop" "UNMEASURED: ${DOCKER_ERR}"
        docker_verdict=UNKNOWN
        docker_text="cannot tell whether Docker Desktop is running: ${DOCKER_ERR}"
    fi

    echo "G-MEM conditions:"
    report_condition "$mem_verdict" memory "$mem_text"
    report_condition "$swap_verdict" swap "$swap_text"
    report_condition "$docker_verdict" docker "$docker_text"
    if [[ "$GATE_UNKNOWN" -gt 0 ]]; then
        echo "G-MEM: UNKNOWN (${GATE_UNKNOWN} of 3 conditions could not be measured; start fails closed)"
    elif [[ "$GATE_FAILED" -gt 0 ]]; then
        echo "G-MEM: FAIL (${GATE_FAILED} of 3 conditions failed)"
    else
        echo "G-MEM: PASS"
    fi
}

# ---------------------------------------------------------------------------------------------
# stop's wait: poll every POLL_INTERVAL seconds until VMState is an off state or $1 seconds pass.
# A loop on bash's SECONDS, not timeout(1) (absent from stock macOS). 0 off, 1 timed out,
# 2 the state could not be read.
# ---------------------------------------------------------------------------------------------
wait_until_off() {
    local limit="$1" started="$SECONDS"
    while :; do
        query_vm || return 2
        if is_off_state "$VM_STATE"; then
            return 0
        fi
        if [[ $((SECONDS - started)) -ge "$limit" ]]; then
            return 1
        fi
        sleep "$POLL_INTERVAL"
    done
}

force_off() {
    local rc=0
    echo "--force: powering ${VM} off hard: $(render "$VBOXMANAGE" controlvm "$VM" poweroff)"
    if ! "$VBOXMANAGE" controlvm "$VM" poweroff; then
        echo "ERROR: poweroff failed for VM ${VM}." >&2
        exit 1
    fi
    wait_until_off "$TIMEOUT" || rc=$?
    case "$rc" in
        0)
            echo "VM ${VM} is off (VMState=${VM_STATE})."
            exit 0
            ;;
        2)
            vm_problem_detail
            exit 2
            ;;
    esac
    echo "ERROR: VM ${VM} is still ${VM_STATE} ${TIMEOUT} s after poweroff." >&2
    exit 1
}

# ---------------------------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------------------------
cmd_status() {
    local env_error=0
    if query_vm; then
        echo "VM ${VM}: VMState=${VM_STATE}"
    else
        env_error=1
        echo "VM ${VM}: $(vm_problem_summary)"
        vm_problem_detail
    fi
    evaluate_gate
    [[ "$GATE_UNKNOWN" -eq 0 ]] || env_error=1
    [[ "$env_error" -eq 0 ]] || exit 2
    exit 0
}

cmd_start() {
    if ! query_vm; then
        vm_problem_detail
        exit 2
    fi
    if [[ "$VM_STATE" == "running" ]]; then
        echo "VM ${VM} is already running; nothing to do (G-MEM not evaluated)."
        exit 0
    fi
    if ! is_off_state "$VM_STATE"; then
        echo "ERROR: VM ${VM} is in state '${VM_STATE}'. start acts only on a stopped VM (poweroff, saved, aborted, aborted-saved, teleported)." >&2
        echo "Inspect it with $(render "$VBOXMANAGE" showvminfo "$VM"), then resume or power it off by hand." >&2
        exit 2
    fi
    echo "VM ${VM}: VMState=${VM_STATE}"
    evaluate_gate
    if [[ "$GATE_UNKNOWN" -gt 0 || "$GATE_FAILED" -gt 0 ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            echo "DRY-RUN: start would refuse; VBoxManage startvm would not be called for ${VM}:" >&2
        else
            echo "REFUSED: G-MEM did not pass; VBoxManage startvm was not called for ${VM}:" >&2
        fi
        printf '%s' "$GATE_REASONS" >&2
        echo "Per D1 the host stays admin-only while G-MEM fails; retry once it has headroom." >&2
        [[ "$GATE_UNKNOWN" -eq 0 ]] || exit 2
        exit 1
    fi
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "DRY-RUN: G-MEM passed; would run: $(render "$VBOXMANAGE" startvm "$VM" --type headless)"
        echo "(nothing started)"
        exit 0
    fi
    echo "G-MEM passed; starting: $(render "$VBOXMANAGE" startvm "$VM" --type headless)"
    if "$VBOXMANAGE" startvm "$VM" --type headless; then
        echo "started ${VM}"
        exit 0
    fi
    echo "ERROR: VBoxManage startvm failed for ${VM}." >&2
    exit 1
}

cmd_stop() {
    local rc=0 poweroff
    if ! query_vm; then
        vm_problem_detail
        exit 2
    fi
    if is_off_state "$VM_STATE"; then
        echo "VM ${VM} is not running (VMState=${VM_STATE}); nothing to do."
        exit 0
    fi
    # False positive in ShellCheck 0.11.0 only: it calls render "defined later" (SC2218) on this
    # line. 0.10, the pre-commit pin, is clean; render is defined near the top.
    # shellcheck disable=SC2218
    poweroff="$(render "$VBOXMANAGE" controlvm "$VM" poweroff)"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "DRY-RUN: VM ${VM} is ${VM_STATE}; would run: $(render "$VBOXMANAGE" controlvm "$VM" acpipowerbutton)"
        echo "DRY-RUN: then poll VMState every ${POLL_INTERVAL} s for up to ${TIMEOUT} s"
        if [[ "$FORCE" -eq 1 ]]; then
            echo "DRY-RUN: and on timeout run: ${poweroff}"
        else
            echo "DRY-RUN: and on timeout exit 1 without powering off (--force would run: ${poweroff})"
        fi
        echo "(nothing changed)"
        exit 0
    fi
    echo "VM ${VM} is ${VM_STATE}; pressing the ACPI power button: $(render "$VBOXMANAGE" controlvm "$VM" acpipowerbutton)"
    if ! "$VBOXMANAGE" controlvm "$VM" acpipowerbutton; then
        echo "ERROR: acpipowerbutton failed for VM ${VM} (VMState=${VM_STATE})." >&2
        [[ "$FORCE" -eq 0 ]] || force_off
        echo "To power it off hard (unclean, like pulling the plug): ${poweroff}" >&2
        exit 1
    fi
    wait_until_off "$TIMEOUT" || rc=$?
    case "$rc" in
        0)
            echo "VM ${VM} stopped (VMState=${VM_STATE})."
            exit 0
            ;;
        2)
            vm_problem_detail
            exit 2
            ;;
    esac
    if [[ "$FORCE" -eq 1 ]]; then
        echo "VM ${VM} is still ${VM_STATE} after ${TIMEOUT} s."
        force_off
    fi
    echo "ERROR: VM ${VM} is still ${VM_STATE} after ${TIMEOUT} s; not powering it off without --force." >&2
    echo "To power it off hard (unclean, like pulling the plug): ${poweroff}" >&2
    exit 1
}

case "$CMD" in
    status) cmd_status ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
esac
