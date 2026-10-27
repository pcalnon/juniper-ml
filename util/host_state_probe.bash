#!/usr/bin/env bash
# Collect a macOS host's state, read-only, for util/host_state_check.py (turing bring-up task G1).
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-20
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1; the
#             gates of §9.3; the script conventions of §8); util/host_state_check.py, which evaluates this
#             output against conf/hosts/<host>/expected.yaml; tests/test_host_state_probe.py. It graduates
#             util/ad-hoc/2026-10-15_turing_host_state_probe.bash, whose output is the plan's Appendix A.
#
# The probe collects and judges nothing. Each fact is the raw output of one command, captured with its
# argv, exit code and stderr. util/host_state_check.py parses those captures, and an agent's report
# (plan task H3) can be compared against exactly what the host printed.
#
# What it never does (plan §8 and D11):
#   - read a key file. Under ~/.ssh and ~/.gnupg it uses find(1) name and permission tests only;
#   - run a credential probe: no ssh -T, ssh-add, gpg --card-status, gpg -K or gh auth status. The
#     signing section's pinentry check (headless_signing_preflight.bash) sends the Assuan query
#     'GETINFO flavor', which never prompts;
#   - write anything outside its own temp directory.
#
# Sections (default: all, in this order). The gate that reads each one is in brackets.
#   hardware  sysctl -n machdep.cpu.brand_string, hw.ncpu, hw.physicalcpu, hw.memsize, kern.hv_support;
#             sw_vers -productVersion and -buildVersion; uname -m  [the check's identity test]
#   memory    vm_stat; sysctl vm.swapusage; pgrep -x for each Docker Desktop process name that
#             util/macvm_ctl.bash probes  [G-MEM]
#   vm        VBoxManage --version, list vms, showvminfo <vm> --machinereadable  [G-MEM: the VM's size]
#   network   ifconfig -a; networksetup -listallhardwareports  [G-NET]
#   power     pmset -g  [no gate: task C7]
#   security  fdesetup status; socketfilterfw --getglobalstate, --getblockall and --getstealthmode; csrutil status and
#             authenticated-root status; the names of *.asc and *recovery* files under ~/.ssh and
#             ~/.gnupg; the files directly in ~/.ssh, public ones aside, with any group or other
#             permission bit  [G-SEC]
#   tools     for each tool, what `command -v` resolves and the entry in ~/.local/bin; kubectl version
#             --client -o json  [G-TOOLS]
#   env       conda env list; whether <root>/AGENTS.md (the parent AGENTS.md) exists, and its sha256
#             [G-ENV]
#   alias     python3 util/git_remote_alias_check.py --json --root <root>  [G-ALIAS]
#   signing   python3 util/configure_commit_signing.py --check --json --root <root>; bash
#             util/headless_signing_preflight.bash --repo <this checkout>  [G-SIGN]
#
# Usage:
#   bash util/host_state_probe.bash [--json] [--section NAME]... [--tool NAME]... [--root DIR]
#        [--vm NAME] [--timeout SECONDS]
#
# Exit codes:
#   0 -- the probe ran. A command that is missing, fails or times out is recorded, never fatal.
#   2 -- usage or environment: a bad argument, HOME unset, or no temp directory.
#   It never exits 1, because it evaluates nothing.
#
# Environment:
#   SYSCTL SW_VERS UNAME VM_STAT PGREP VBOXMANAGE IFCONFIG NETWORKSETUP PMSET FDESETUP SOCKETFILTERFW
#   CSRUTIL FIND KUBECTL CONDA SHASUM PYTHON -- the programs, overridable because tests cannot
#       PATH-stub an absolute path. The macOS system tools default to their absolute paths.
#   ALIAS_CHECK SIGNING_CHECK SIGNING_PREFLIGHT -- the repo tools the alias and signing sections run
#       (default: the copies next to this script)
#   JUNIPER_ROOT -- the Juniper root (see --root)
#   Every command runs with LC_ALL=C, so their output does not depend on the caller's locale.
#
# JSON (--json): one object. "schema" is bumped on any incompatible change.
#   {
#     "schema": 1,
#     "probe": "util/host_state_probe.bash",
#     "collected_at": "YYYY-MM-DDTHH:MM:SSZ",   (UTC)
#     "node": str, "kernel": str,               (uname -n, uname -s)
#     "home": str, "root": str, "repo": str,    (absolute: HOME, the Juniper root, this checkout)
#     "timeout_seconds": int,
#     "sections": [str],                        (the sections collected, in the order above)
#     "<section>": {...}                        (one object per collected section, below)
#   }
#   CAPTURE = {"argv": [str], "found": bool, "rc": int|null, "timed_out": bool, "stdout": str, "stderr": str}
#     found false: the program is missing or not executable, so nothing ran and rc is null.
#     timed_out true: the command was killed after timeout_seconds; rc is whatever the kill left.
#     stdout and stderr are verbatim, except that control characters other than tab, LF and CR are dropped.
#   hardware  {cpu_brand, ncpu, physicalcpu, memsize, hv_support, os_version, os_build, arch: CAPTURE}
#   memory    {vm_stat: CAPTURE, swapusage: CAPTURE, docker: [{"name": str, "pgrep": CAPTURE}]}
#   vm        {name: str, version: CAPTURE, list_vms: CAPTURE, showvminfo: CAPTURE}
#   network   {ifconfig: CAPTURE, hardware_ports: CAPTURE}
#   power     {pmset: CAPTURE}
#   security  {filevault, firewall, blockall, stealth, sip, authenticated_root: CAPTURE,
#              key_exports: {"dirs": [str], "find": CAPTURE|null},   (null when no dir exists)
#              ssh_loose: {"dir": str, "find": CAPTURE|null}}        (null when ~/.ssh does not exist)
#   tools     {local_bin: str,
#              resolved: {<tool>: {"path": str|null, "local_bin": {"exists": bool, "executable": bool, "link": str|null}}},
#              kubectl_version: CAPTURE}
#   env       {conda: CAPTURE, parent_agents_md: {"path": str, "exists": bool, "sha256": CAPTURE|null}}
#   alias     {check: CAPTURE}
#   signing   {config: CAPTURE, preflight: CAPTURE}
set -euo pipefail
export LC_ALL=C

SYSCTL="${SYSCTL:-/usr/sbin/sysctl}"
SW_VERS="${SW_VERS:-/usr/bin/sw_vers}"
UNAME="${UNAME:-/usr/bin/uname}"
VM_STAT="${VM_STAT:-/usr/bin/vm_stat}"
PGREP="${PGREP:-/usr/bin/pgrep}"
VBOXMANAGE="${VBOXMANAGE:-/usr/local/bin/VBoxManage}"
IFCONFIG="${IFCONFIG:-/sbin/ifconfig}"
NETWORKSETUP="${NETWORKSETUP:-/usr/sbin/networksetup}"
PMSET="${PMSET:-/usr/bin/pmset}"
FDESETUP="${FDESETUP:-/usr/bin/fdesetup}"
SOCKETFILTERFW="${SOCKETFILTERFW:-/usr/libexec/ApplicationFirewall/socketfilterfw}"
CSRUTIL="${CSRUTIL:-/usr/bin/csrutil}"
FIND="${FIND:-find}"
KUBECTL="${KUBECTL:-kubectl}"
CONDA="${CONDA:-conda}"
SHASUM="${SHASUM:-shasum}"
PYTHON="${PYTHON:-python3}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$HERE")"
ALIAS_CHECK="${ALIAS_CHECK:-${HERE}/git_remote_alias_check.py}"
SIGNING_CHECK="${SIGNING_CHECK:-${HERE}/configure_commit_signing.py}"
SIGNING_PREFLIGHT="${SIGNING_PREFLIGHT:-${HERE}/headless_signing_preflight.bash}"

ALL_SECTIONS=(hardware memory vm network power security tools env alias signing)
# The ad-hoc probe's sweep (plan Appendix A), plus every tool conf/hosts/turing/hosttools-environment.yml
# names. --tool adds more.
DEFAULT_TOOLS=(brew git gh gpg gpg-agent pinentry-mac ykman conda mamba python3 uv pre-commit shellcheck
    markdownlint-cli2 yamllint actionlint sops age age-keygen node jq yq timeout iperf3 VBoxManage docker
    kubectl helm claude)
# Docker Desktop's processes, as util/macvm_ctl.bash probes them for G-MEM.
DOCKER_NAMES=(com.docker.backend "Docker Desktop" Docker)

usage() {
    cat <<'EOF'
Usage: host_state_probe.bash [--json] [--section NAME]... [--tool NAME]... [--root DIR]
                             [--vm NAME] [--timeout SECONDS]

Collect this host's state, read-only, as raw command captures. util/host_state_check.py
evaluates them against conf/hosts/<host>/expected.yaml (turing bring-up task G1, the
gates of plan §9.3). The probe judges nothing.

Sections (default: all):
  hardware  sysctl CPU and memory facts, sw_vers, uname -m
  memory    vm_stat, sysctl vm.swapusage, pgrep -x for Docker Desktop (G-MEM)
  vm        VBoxManage --version, list vms, showvminfo <vm> --machinereadable (G-MEM)
  network   ifconfig -a, networksetup -listallhardwareports (G-NET)
  power     pmset -g (task C7)
  security  fdesetup, socketfilterfw, csrutil; key-export file names under ~/.ssh and
            ~/.gnupg; ~/.ssh files open to group or others (G-SEC). Names and
            permission bits only: no key file is ever read.
  tools     command -v and the ~/.local/bin entry per tool; kubectl's client version (G-TOOLS)
  env       conda env list; the sha256 of <root>/AGENTS.md (G-ENV)
  alias     util/git_remote_alias_check.py --json (G-ALIAS)
  signing   util/configure_commit_signing.py --check --json and
            util/headless_signing_preflight.bash (G-SIGN)

Options:
  --json             print one JSON object (the schema is in this script's header)
  --section NAME     collect only this section; repeatable
  --tool NAME        resolve this tool too (tools section); repeatable
  --root DIR         the Juniper root (default: $JUNIPER_ROOT, else ~/Development/python/Juniper)
  --vm NAME          the VM the vm section asks about (default: juniper-macvm)
  --timeout SECONDS  kill a command that runs longer than this (default: 60)
  -h, --help         show this help

No credential probe runs: no ssh -T, ssh-add, gpg --card-status, gpg -K or gh auth.

Exit codes: 0 the probe ran (a missing, failing or hung command is recorded, never
fatal); 2 usage or environment error. It never exits 1: it evaluates nothing.

Environment: SYSCTL, SW_VERS, UNAME, VM_STAT, PGREP, VBOXMANAGE, IFCONFIG,
NETWORKSETUP, PMSET, FDESETUP, SOCKETFILTERFW, CSRUTIL, FIND, KUBECTL, CONDA,
SHASUM and PYTHON name the programs; ALIAS_CHECK, SIGNING_CHECK and
SIGNING_PREFLIGHT name the repo tools. Commands run with LC_ALL=C.
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

die_env() {
    echo "ERROR: $1" >&2
    exit 2
}

JSON=0
ROOT="${JUNIPER_ROOT:-}"
VM="juniper-macvm"
TIMEOUT=60
WANT_SECTIONS=()
EXTRA_TOOLS=()

# A function rather than a top-level loop: ShellCheck 0.11 reports every later call of die_usage as
# SC2218 ("only defined later") after a top-level loop that can exit. 0.10, the pre-commit pin, does not.
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --json)
                JSON=1
                shift
                ;;
            --section)
                [[ -n "${2:-}" ]] || die_usage "--section needs a name"
                WANT_SECTIONS+=("$2")
                shift 2
                ;;
            --tool)
                [[ -n "${2:-}" ]] || die_usage "--tool needs a name"
                EXTRA_TOOLS+=("$2")
                shift 2
                ;;
            --root)
                [[ -n "${2:-}" ]] || die_usage "--root needs a directory"
                ROOT="$2"
                shift 2
                ;;
            --vm)
                [[ -n "${2:-}" ]] || die_usage "--vm needs a name"
                VM="$2"
                shift 2
                ;;
            --timeout)
                [[ -n "${2:-}" ]] || die_usage "--timeout needs a number of seconds"
                TIMEOUT="$2"
                shift 2
                ;;
            -*)
                die_usage "unknown option: $1"
                ;;
            *)
                die_usage "unexpected argument: $1"
                ;;
        esac
    done
}
parse_args "$@"

timeout_re='^[1-9][0-9]{0,3}$'
[[ "$TIMEOUT" =~ $timeout_re ]] && [[ "$TIMEOUT" -le 3600 ]] || die_usage "--timeout needs whole seconds from 1 to 3600 (got '${TIMEOUT}')"
vm_re='^[A-Za-z0-9][A-Za-z0-9._-]*$'
[[ "$VM" =~ $vm_re ]] || die_usage "not a VM name or UUID: '${VM}'"
tool_re='^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$'

# Sections in canonical order, each once.
SECTIONS=()
if [[ "${#WANT_SECTIONS[@]}" -eq 0 ]]; then
    SECTIONS=("${ALL_SECTIONS[@]}")
else
    for want in "${WANT_SECTIONS[@]}"; do
        case " ${ALL_SECTIONS[*]} " in
            *" ${want} "*) ;;
            *) die_usage "unknown section: '${want}' (known: ${ALL_SECTIONS[*]})" ;;
        esac
    done
    for name in "${ALL_SECTIONS[@]}"; do
        case " ${WANT_SECTIONS[*]} " in
            *" ${name} "*) SECTIONS+=("$name") ;;
        esac
    done
fi

# Tools in order, each once: the defaults, then --tool.
TOOLS=()
for tool in "${DEFAULT_TOOLS[@]}" ${EXTRA_TOOLS[@]+"${EXTRA_TOOLS[@]}"}; do
    [[ "$tool" =~ $tool_re ]] || die_usage "not a tool name: '${tool}'"
    case " ${TOOLS[*]-} " in
        *" ${tool} "*) ;;
        *) TOOLS+=("$tool") ;;
    esac
done

[[ -n "${HOME:-}" ]] || die_env "HOME is not set"
[[ -n "$ROOT" ]] || ROOT="${HOME}/Development/python/Juniper"
[[ "$ROOT" == /* ]] || ROOT="${PWD}/${ROOT}"

# Scratch for this run, removed on exit: under TMPDIR, else this checkout's gitignored tmp/ -- never
# the system temp dir (2026-10-26 rule). Derived from the script's own path: the probe never runs git.
if [[ -n "${TMPDIR:-}" ]]; then
    SCRATCH_ROOT="${TMPDIR%/}"
else
    SCRATCH_ROOT="$(dirname "$HERE")/tmp"
    mkdir -p "$SCRATCH_ROOT" || die_env "cannot create ${SCRATCH_ROOT}"
fi
TMP_DIR="$(mktemp -d "${SCRATCH_ROOT}/host-state-probe.XXXXXX")" || die_env "mktemp failed"
trap 'rm -rf "$TMP_DIR"' EXIT

# ---------------------------------------------------------------------------------------------
# JSON output. Members are written as they are collected; J_FIRST tracks the comma per level.
# ---------------------------------------------------------------------------------------------
J_DEPTH=0
J_FIRST=(1)

json_string() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\t'/\\t}
    s=${s//$'\r'/\\r}
    s=${s//$'\n'/\\n}
    printf '"%s"' "$s"
}

# A file's bytes as a JSON string. tr drops the control characters JSON cannot hold raw (tab, LF and
# CR are escaped instead). The trailing X keeps the command substitution from eating final newlines.
json_file() {
    local s
    s="$(tr -d '\000-\010\013\014\016-\037' <"$1"; printf X)"
    json_string "${s%X}"
}

json_bool() {
    if [[ "$1" -eq 1 ]]; then printf 'true'; else printf 'false'; fi
}

# A string, or null when it is empty.
json_opt() {
    if [[ -n "$1" ]]; then json_string "$1"; else printf 'null'; fi
}

j_sep() {
    if [[ "${J_FIRST[$J_DEPTH]}" -eq 1 ]]; then
        J_FIRST[J_DEPTH]=0
    else
        printf ','
    fi
}

j_open() {
    printf '%s' "$1"
    J_DEPTH=$((J_DEPTH + 1))
    J_FIRST[J_DEPTH]=1
}

j_close() {
    printf '%s' "$1"
    J_DEPTH=$((J_DEPTH - 1))
}

# Start a member: the separator, the quoted key and the colon. The caller prints the value.
j_key() {
    j_sep
    json_string "$1"
    printf ':'
}

json_strings() {
    local s
    j_open '['
    for s in "$@"; do
        j_sep
        json_string "$s"
    done
    j_close ']'
}

# A command line, each word shell-quoted, for the text report.
render() {
    local out="" word
    for word in "$@"; do
        out="${out:+$out }$(printf '%q' "$word")"
    done
    printf '%s' "$out"
}

# ---------------------------------------------------------------------------------------------
# Running a command: stdin from /dev/null, stdout and stderr to files, killed after TIMEOUT seconds.
# bash 3.2 has no timeout builtin, and stock macOS has no timeout(1). Sets CAP_FOUND, CAP_RC,
# CAP_TIMED_OUT, CAP_OUT and CAP_ERR.
# ---------------------------------------------------------------------------------------------
CAPTURE_N=0

program_found() {
    if [[ "$1" == */* ]]; then
        [[ -f "$1" && -x "$1" ]]
    else
        command -v "$1" >/dev/null 2>&1
    fi
}

run_capture() {
    local pid ticks=0 limit=$((TIMEOUT * 50))
    CAPTURE_N=$((CAPTURE_N + 1))
    CAP_OUT="${TMP_DIR}/${CAPTURE_N}.out"
    CAP_ERR="${TMP_DIR}/${CAPTURE_N}.err"
    : >"$CAP_OUT"
    : >"$CAP_ERR"
    CAP_FOUND=1
    CAP_RC=""
    CAP_TIMED_OUT=0
    if ! program_found "$1"; then
        CAP_FOUND=0
        return 0
    fi
    "$@" </dev/null >"$CAP_OUT" 2>"$CAP_ERR" &
    pid=$!
    CAP_RC=0
    # bash reports a job that a signal ended ("Terminated: 15") on its own stderr. The group keeps
    # that notice out of the probe's output: the exit code records it.
    {
        while kill -0 "$pid"; do
            if [[ "$ticks" -ge "$limit" ]]; then
                kill -TERM "$pid" || true
                sleep 1
                kill -KILL "$pid" || true
                CAP_TIMED_OUT=1
                break
            fi
            ticks=$((ticks + 1))
            sleep 0.02
        done
        wait "$pid" || CAP_RC=$?
    } 2>/dev/null
}

# Print the last capture as a CAPTURE object (the argv is passed again).
emit_capture_json() {
    j_open '{'
    j_key argv
    json_strings "$@"
    j_key found
    json_bool "$CAP_FOUND"
    j_key rc
    printf '%s' "${CAP_RC:-null}"
    j_key timed_out
    json_bool "$CAP_TIMED_OUT"
    j_key stdout
    json_file "$CAP_OUT"
    j_key stderr
    json_file "$CAP_ERR"
    j_close '}'
}

emit_capture_text() {
    local label="$1" status=""
    shift
    if [[ "$CAP_FOUND" -eq 0 ]]; then
        status="  [not found]"
    elif [[ "$CAP_TIMED_OUT" -eq 1 ]]; then
        status="  [timed out after ${TIMEOUT}s]"
    elif [[ "$CAP_RC" != 0 ]]; then
        status="  [exit ${CAP_RC}]"
    fi
    printf -- '-- %s: %s%s\n' "$label" "$(render "$@")" "$status"
    if [[ -s "$CAP_OUT" ]]; then
        cat "$CAP_OUT"
        [[ -z "$(tail -c 1 "$CAP_OUT")" ]] || echo
    fi
    if [[ -s "$CAP_ERR" ]]; then
        sed 's/^/   stderr: /' "$CAP_ERR"
        [[ -z "$(tail -c 1 "$CAP_ERR")" ]] || echo
    fi
}

# capture KEY ARGV...: run ARGV and write it as member KEY of the current object.
capture() {
    local key="$1"
    shift
    run_capture "$@"
    if [[ "$JSON" -eq 1 ]]; then
        j_key "$key"
        emit_capture_json "$@"
    else
        emit_capture_text "$key" "$@"
    fi
}

section_begin() {
    if [[ "$JSON" -eq 1 ]]; then
        j_key "$1"
        j_open '{'
    else
        printf '\n== %s\n' "$1"
    fi
}

section_end() {
    if [[ "$JSON" -eq 1 ]]; then
        j_close '}'
    fi
}

# A member whose value is a plain string (JSON) or a "key: value" line (text).
plain() {
    if [[ "$JSON" -eq 1 ]]; then
        j_key "$1"
        json_string "$2"
    else
        printf -- '-- %s: %s\n' "$1" "$2"
    fi
}

# ---------------------------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------------------------
section_hardware() {
    section_begin hardware
    capture cpu_brand "$SYSCTL" -n machdep.cpu.brand_string
    capture ncpu "$SYSCTL" -n hw.ncpu
    capture physicalcpu "$SYSCTL" -n hw.physicalcpu
    capture memsize "$SYSCTL" -n hw.memsize
    capture hv_support "$SYSCTL" -n kern.hv_support
    capture os_version "$SW_VERS" -productVersion
    capture os_build "$SW_VERS" -buildVersion
    capture arch "$UNAME" -m
    section_end
}

section_memory() {
    local name
    section_begin memory
    capture vm_stat "$VM_STAT"
    capture swapusage "$SYSCTL" vm.swapusage
    if [[ "$JSON" -eq 1 ]]; then
        j_key docker
        j_open '['
        for name in "${DOCKER_NAMES[@]}"; do
            j_sep
            run_capture "$PGREP" -x "$name"
            j_open '{'
            j_key name
            json_string "$name"
            j_key pgrep
            emit_capture_json "$PGREP" -x "$name"
            j_close '}'
        done
        j_close ']'
    else
        for name in "${DOCKER_NAMES[@]}"; do
            capture "docker: ${name}" "$PGREP" -x "$name"
        done
    fi
    section_end
}

section_vm() {
    section_begin vm
    plain name "$VM"
    capture version "$VBOXMANAGE" --version
    capture list_vms "$VBOXMANAGE" list vms
    capture showvminfo "$VBOXMANAGE" showvminfo "$VM" --machinereadable
    section_end
}

section_network() {
    section_begin network
    capture ifconfig "$IFCONFIG" -a
    capture hardware_ports "$NETWORKSETUP" -listallhardwareports
    section_end
}

section_power() {
    section_begin power
    capture pmset "$PMSET" -g
    section_end
}

section_security() {
    local ssh_dir="${HOME}/.ssh" dir
    local dirs=()
    section_begin security
    capture filevault "$FDESETUP" status
    capture firewall "$SOCKETFILTERFW" --getglobalstate
    capture blockall "$SOCKETFILTERFW" --getblockall
    capture stealth "$SOCKETFILTERFW" --getstealthmode
    capture sip "$CSRUTIL" status
    capture authenticated_root "$CSRUTIL" authenticated-root status
    for dir in "${HOME}/.ssh" "${HOME}/.gnupg"; do
        if [[ -d "$dir" ]]; then
            dirs+=("$dir")
        fi
    done
    # Names only: -iname and -perm read the directory and the inode, never a file's contents.
    if [[ "$JSON" -eq 1 ]]; then
        j_key key_exports
        j_open '{'
        j_key dirs
        json_strings ${dirs[@]+"${dirs[@]}"}
        j_key find
        if [[ "${#dirs[@]}" -gt 0 ]]; then
            run_capture "$FIND" "${dirs[@]}" -maxdepth 4 \( -type f -o -type l \) \( -iname '*.asc' -o -iname '*recovery*' \) -print
            emit_capture_json "$FIND" "${dirs[@]}" -maxdepth 4 \( -type f -o -type l \) \( -iname '*.asc' -o -iname '*recovery*' \) -print
        else
            printf 'null'
        fi
        j_close '}'
        j_key ssh_loose
        j_open '{'
        j_key dir
        json_string "$ssh_dir"
        j_key find
        if [[ -d "$ssh_dir" ]]; then
            run_capture "$FIND" "$ssh_dir" -maxdepth 1 -type f ! -name '*.pub' ! -name 'known_hosts*' ! -name 'authorized_keys*' \( -perm -040 -o -perm -020 -o -perm -010 -o -perm -004 -o -perm -002 -o -perm -001 \) -print
            emit_capture_json "$FIND" "$ssh_dir" -maxdepth 1 -type f ! -name '*.pub' ! -name 'known_hosts*' ! -name 'authorized_keys*' \( -perm -040 -o -perm -020 -o -perm -010 -o -perm -004 -o -perm -002 -o -perm -001 \) -print
        else
            printf 'null'
        fi
        j_close '}'
    else
        if [[ "${#dirs[@]}" -gt 0 ]]; then
            capture key_exports "$FIND" "${dirs[@]}" -maxdepth 4 \( -type f -o -type l \) \( -iname '*.asc' -o -iname '*recovery*' \) -print
        else
            plain key_exports "neither ${HOME}/.ssh nor ${HOME}/.gnupg exists"
        fi
        if [[ -d "$ssh_dir" ]]; then
            capture ssh_loose "$FIND" "$ssh_dir" -maxdepth 1 -type f ! -name '*.pub' ! -name 'known_hosts*' ! -name 'authorized_keys*' \( -perm -040 -o -perm -020 -o -perm -010 -o -perm -004 -o -perm -002 -o -perm -001 \) -print
        else
            plain ssh_loose "${ssh_dir} does not exist"
        fi
    fi
    section_end
}

section_tools() {
    local local_bin="${HOME}/.local/bin" tool path entry exists executable link
    section_begin tools
    if [[ "$JSON" -eq 1 ]]; then
        j_key local_bin
        json_string "$local_bin"
        j_key resolved
        j_open '{'
    else
        printf '%-18s %-52s %s\n' "tool" "command -v" "${local_bin}/<tool>"
    fi
    for tool in "${TOOLS[@]}"; do
        path="$(command -v "$tool" 2>/dev/null || true)"
        entry="${local_bin}/${tool}"
        exists=0
        executable=0
        link=""
        if [[ -e "$entry" || -L "$entry" ]]; then
            exists=1
        fi
        if [[ -f "$entry" && -x "$entry" ]]; then
            executable=1
        fi
        if [[ -L "$entry" ]]; then
            link="$(readlink "$entry" 2>/dev/null || true)"
        fi
        if [[ "$JSON" -eq 1 ]]; then
            j_key "$tool"
            j_open '{'
            j_key path
            json_opt "$path"
            j_key local_bin
            j_open '{'
            j_key exists
            json_bool "$exists"
            j_key executable
            json_bool "$executable"
            j_key link
            json_opt "$link"
            j_close '}'
            j_close '}'
        else
            if [[ "$exists" -eq 0 ]]; then
                entry="absent"
            elif [[ "$executable" -eq 0 ]]; then
                entry="present, not executable${link:+ (-> ${link})}"
            else
                entry="executable${link:+ (-> ${link})}"
            fi
            printf '%-18s %-52s %s\n' "$tool" "${path:-MISSING}" "$entry"
        fi
    done
    if [[ "$JSON" -eq 1 ]]; then
        j_close '}'
    fi
    capture kubectl_version "$KUBECTL" version --client -o json
    section_end
}

section_env() {
    local agents_md="${ROOT}/AGENTS.md" exists=0
    section_begin env
    capture conda "$CONDA" env list
    if [[ -f "$agents_md" ]]; then
        exists=1
    fi
    if [[ "$JSON" -eq 1 ]]; then
        j_key parent_agents_md
        j_open '{'
        j_key path
        json_string "$agents_md"
        j_key exists
        json_bool "$exists"
        j_key sha256
        if [[ "$exists" -eq 1 ]]; then
            run_capture "$SHASUM" -a 256 "$agents_md"
            emit_capture_json "$SHASUM" -a 256 "$agents_md"
        else
            printf 'null'
        fi
        j_close '}'
    elif [[ "$exists" -eq 1 ]]; then
        capture parent_agents_md "$SHASUM" -a 256 "$agents_md"
    else
        plain parent_agents_md "${agents_md} does not exist"
    fi
    section_end
}

section_alias() {
    section_begin alias
    capture check "$PYTHON" "$ALIAS_CHECK" --json --root "$ROOT"
    section_end
}

section_signing() {
    section_begin signing
    capture config "$PYTHON" "$SIGNING_CHECK" --check --json --root "$ROOT"
    capture preflight "${BASH:-bash}" "$SIGNING_PREFLIGHT" --repo "$REPO_DIR"
    section_end
}

# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------
NODE="$("$UNAME" -n 2>/dev/null || true)"
KERNEL="$("$UNAME" -s 2>/dev/null || true)"
COLLECTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ "$JSON" -eq 1 ]]; then
    j_open '{'
    j_key schema
    printf '1'
    j_key probe
    json_string "util/host_state_probe.bash"
    j_key collected_at
    json_string "$COLLECTED_AT"
    j_key node
    json_string "$NODE"
    j_key kernel
    json_string "$KERNEL"
    j_key home
    json_string "$HOME"
    j_key root
    json_string "$ROOT"
    j_key repo
    json_string "$REPO_DIR"
    j_key timeout_seconds
    printf '%s' "$TIMEOUT"
    j_key sections
    json_strings "${SECTIONS[@]}"
else
    echo "host state probe: read-only; names and permission bits only under ~/.ssh and ~/.gnupg"
    echo "node       ${NODE:-unknown} (${KERNEL:-unknown})"
    echo "collected  ${COLLECTED_AT}"
    echo "root       ${ROOT}"
    echo "sections   ${SECTIONS[*]}"
fi

for name in "${SECTIONS[@]}"; do
    "section_${name}"
done

if [[ "$JSON" -eq 1 ]]; then
    j_close '}'
    echo
fi
exit 0
