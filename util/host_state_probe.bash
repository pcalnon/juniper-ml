#!/usr/bin/env bash
# Collect this host's state for the turing bring-up gates, read-only, as a text report or one JSON object.
#
# Project:    juniper-ml
# Sub-Project: host tooling (turing bring-up)
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-20
# Status:     permanent utility
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1; §8; the gates
#             in §9.3, as revised by §16.3 E-D6 and §19.2 E-G-SIGN); util/host_state_check.py, which evaluates
#             this probe's JSON against conf/hosts/<host>/expected.yaml; tests/test_host_state_probe.py.
#             It graduates util/ad-hoc/2026-10-15_turing_host_state_probe.bash, whose output is the plan's
#             Appendix A.
#
# The probe collects and judges nothing. Each item it collects is a "capture": one command's exit code,
# stdout and stderr, kept raw, so util/host_state_check.py does all the parsing and a saved probe can be
# evaluated again later. Captures are grouped in sections:
#   hardware    sysctl (machdep.cpu.brand_string hw.ncpu hw.physicalcpu hw.memsize kern.hv_support),
#               sw_vers, uname-m
#   memory      vm_stat, swapusage (sysctl vm.swapusage)
#   docker      pgrep:com.docker.backend, "pgrep:Docker Desktop", pgrep:Docker (pgrep -x each; the names
#               util/macvm_ctl.bash probes)
#   hypervisor  vboxmanage-version, vboxmanage-list-vms, vboxmanage-showvminfo (the --vm VM)
#   disk        df (df -k / and, where it exists, /System/Volumes/Data)
#   power       pmset (pmset -g)
#   network     ifconfig (ifconfig -a)
#   security    csrutil-status, csrutil-authenticated-root, fdesetup-status, firewall-globalstate,
#               firewall-stealthmode, key-material-names, ssh-loose-files
#   toolchain   command-v:<tool> per tool (type -P, the PATH lookup `command -v` makes for an
#               executable), kubectl-version (kubectl version --client -o json)
#   env         conda-env-list (conda env list), parent-agents-md (shasum -a 256 <root>/AGENTS.md)
#   git         git-remote-alias-check (util/git_remote_alias_check.py --json)
#   signing     configure-commit-signing (util/configure_commit_signing.py --check --json),
#               headless-signing-preflight (util/headless_signing_preflight.bash --repo <root>/juniper-ml)
#
# Credentials. The probe reads names and modes, never contents. key-material-names lists the names under
# ~/.ssh and ~/.gnupg that match *.asc or *recovery* (gate G-SEC). ssh-loose-files lists the regular files
# under ~/.ssh, other than *.pub and known_hosts*, that group or others may read, write or execute; it
# tests the mode with `find -perm`, never `stat`. No capture opens a file under ~/.ssh or ~/.gnupg, runs
# ssh or ssh-add, asks gh for a token, or talks to a card. The signing captures are the two non-credential
# tools of plan tasks B7 and K2; the preflight probes the pinentry with 'GETINFO flavor', which never
# prompts.
#
# Usage:
#   bash util/host_state_probe.bash [--json] [--section NAME]... [--root DIR] [--tool NAME]...
#        [--vm NAME] [--timeout SECONDS]
#
# Exit codes:
#   0 -- collected. A command that failed, timed out or is missing is recorded in its capture, not an error.
#   1 -- never: the probe judges nothing (util/host_state_check.py does).
#   2 -- usage or environment: a bad argument, or no temporary directory.
#
# Environment:
#   SYSCTL SW_VERS UNAME VM_STAT PGREP VBOXMANAGE DF PMSET IFCONFIG CSRUTIL FDESETUP SOCKETFILTERFW FIND
#   KUBECTL CONDA SHASUM HOSTNAME_BIN PYTHON -- the commands the captures run. The macOS tools default to
#       absolute paths, so tests override the variables rather than PATH.
#   ALIAS_CHECK, SIGNING_CHECK, SIGNING_PREFLIGHT -- the three sibling tools (default: next to this script)
#   JUNIPER_ROOT -- the Juniper root when --root is not given (then ~/Development/python/Juniper)
#   HOME -- locates ~/.ssh and ~/.gnupg
#
# JSON (--json), schema 1. Every capture is one object; a skipped capture ran nothing and says why.
#   {
#     "schema": 1,
#     "tool": "util/host_state_probe.bash",
#     "host": str,               # hostname -s, as printed
#     "collected_at": str,       # UTC, YYYY-MM-DDTHH:MM:SSZ
#     "bash_version": str,       # the bash that ran the probe
#     "home": str, "path": str,  # $HOME and $PATH, which the captures resolve against
#     "root": str,               # the Juniper root
#     "vm": str,                 # the VM whose configuration vboxmanage-showvminfo reads
#     "timeout_seconds": int,    # the per-capture limit
#     "sections": [str],         # the sections collected, in the order above
#     "captures": [{
#       "section": str, "name": str,
#       "command": str,          # the argv, each word shell-quoted
#       "exit_code": int | null, # null when skipped; 137 or so when killed at the timeout
#       "timed_out": bool,
#       "skipped": str | null,   # the reason nothing ran, e.g. "absent: <path>"
#       "stdout": str, "stderr": str   # trailing newlines removed; C0 controls other than tab, CR, LF dropped
#     }]
#   }
set -euo pipefail

SYSCTL="${SYSCTL:-/usr/sbin/sysctl}"
SW_VERS="${SW_VERS:-/usr/bin/sw_vers}"
UNAME="${UNAME:-uname}"
VM_STAT="${VM_STAT:-/usr/bin/vm_stat}"
PGREP="${PGREP:-/usr/bin/pgrep}"
VBOXMANAGE="${VBOXMANAGE:-/usr/local/bin/VBoxManage}"
DF="${DF:-df}"
PMSET="${PMSET:-/usr/bin/pmset}"
IFCONFIG="${IFCONFIG:-/sbin/ifconfig}"
CSRUTIL="${CSRUTIL:-/usr/bin/csrutil}"
FDESETUP="${FDESETUP:-/usr/bin/fdesetup}"
SOCKETFILTERFW="${SOCKETFILTERFW:-/usr/libexec/ApplicationFirewall/socketfilterfw}"
FIND="${FIND:-find}"
KUBECTL="${KUBECTL:-kubectl}"
CONDA="${CONDA:-conda}"
SHASUM="${SHASUM:-shasum}"
HOSTNAME_BIN="${HOSTNAME_BIN:-hostname}"
PYTHON="${PYTHON:-python3}"
UTIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIAS_CHECK="${ALIAS_CHECK:-${UTIL_DIR}/git_remote_alias_check.py}"
SIGNING_CHECK="${SIGNING_CHECK:-${UTIL_DIR}/configure_commit_signing.py}"
SIGNING_PREFLIGHT="${SIGNING_PREFLIGHT:-${UTIL_DIR}/headless_signing_preflight.bash}"

ALL_SECTIONS="hardware memory docker hypervisor disk power network security toolchain env git signing"
# The ad-hoc probe's list, plus the tools of conf/hosts/turing/hosttools-environment.yml (E-D6).
DEFAULT_TOOLS="brew git gh gpg gpg-agent pinentry-mac ykman conda mamba python3 uv pre-commit gitleaks shellcheck markdownlint-cli2 yamllint actionlint sops age age-keygen yq jq node timeout iperf3 VBoxManage docker kubectl helm claude"

usage() {
    cat <<'EOF'
Usage: host_state_probe.bash [--json] [--section NAME]... [--root DIR] [--tool NAME]...
                             [--vm NAME] [--timeout SECONDS]

Collect this host's state for the turing bring-up gates (plan §9.3), read-only. Each
item is one command's raw exit code, stdout and stderr; util/host_state_check.py
parses and judges them. Names and modes only: nothing under ~/.ssh or ~/.gnupg is
opened, and no credential is touched.

Sections (all by default, in this order):
  hardware memory docker hypervisor disk power network security toolchain env git signing

  --json             print one JSON object (schema 1, in the script header)
  --section NAME     collect only this section; repeatable
  --root DIR         the Juniper root (default: $JUNIPER_ROOT, then ~/Development/python/Juniper)
  --tool NAME        also look up this tool in the toolchain section; repeatable
  --vm NAME          the VM whose configured memory is read (default: juniper-macvm)
  --timeout SECONDS  kill a capture that runs longer than this (default: 60)
  -h, --help         show this help

Exit codes: 0 collected (a failed or missing command is recorded, not an error);
2 usage or environment error. The probe never exits 1: it judges nothing.

Environment: SYSCTL SW_VERS UNAME VM_STAT PGREP VBOXMANAGE DF PMSET IFCONFIG CSRUTIL
FDESETUP SOCKETFILTERFW FIND KUBECTL CONDA SHASUM HOSTNAME_BIN PYTHON name the commands;
ALIAS_CHECK, SIGNING_CHECK and SIGNING_PREFLIGHT the sibling tools.
EOF
}

die_usage() {
    echo "ERROR: $1" >&2
    echo "Run with --help for usage." >&2
    exit 2
}

JSON=0
WANT=""
ROOT=""
EXTRA_TOOLS=""
VM="juniper-macvm"
TIMEOUT=60

section_re='^[a-z]+$'
tool_re='^[A-Za-z0-9][A-Za-z0-9._+-]*$'
vm_re='^[A-Za-z0-9][A-Za-z0-9._-]*$'
timeout_re='^[1-9][0-9]{0,3}$'

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
            [[ "$2" =~ $section_re ]] || die_usage "unknown section: '$2' (expected one of: ${ALL_SECTIONS})"
            case " ${ALL_SECTIONS} " in
                *" $2 "*) ;;
                *) die_usage "unknown section: '$2' (expected one of: ${ALL_SECTIONS})" ;;
            esac
            WANT="${WANT} $2"
            shift 2
            ;;
        --root)
            [[ -n "${2:-}" ]] || die_usage "--root needs a directory"
            ROOT="$2"
            shift 2
            ;;
        --tool)
            [[ -n "${2:-}" ]] || die_usage "--tool needs a name"
            [[ "$2" =~ $tool_re ]] || die_usage "not a tool name: '$2'"
            EXTRA_TOOLS="${EXTRA_TOOLS} $2"
            shift 2
            ;;
        --vm)
            [[ -n "${2:-}" ]] || die_usage "--vm needs a name"
            [[ "$2" =~ $vm_re ]] || die_usage "not a VM name or UUID: '$2'"
            VM="$2"
            shift 2
            ;;
        --timeout)
            [[ "${2:-}" =~ $timeout_re ]] || die_usage "--timeout needs whole seconds from 1 to 9999 (got '${2:-}')"
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            die_usage "unknown argument: $1"
            ;;
    esac
done

if [[ -z "$ROOT" ]]; then
    ROOT="${JUNIPER_ROOT:-${HOME}/Development/python/Juniper}"
fi

SECTIONS=""
for s in $ALL_SECTIONS; do
    if [[ -z "$WANT" ]]; then
        SECTIONS="${SECTIONS:+$SECTIONS }$s"
    else
        case "$WANT " in
            *" $s "*) SECTIONS="${SECTIONS:+$SECTIONS }$s" ;;
        esac
    fi
done

# Tools in first-seen order, each once.
TOOLS=""
for t in $DEFAULT_TOOLS $EXTRA_TOOLS; do
    case " $TOOLS " in
        *" $t "*) ;;
        *) TOOLS="${TOOLS:+$TOOLS }$t" ;;
    esac
done

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/host_state_probe.XXXXXX" 2>/dev/null)" || {
    echo "ERROR: cannot create a temporary directory under ${TMPDIR:-/tmp}" >&2
    exit 2
}
trap 'rm -rf "$TMP_DIR"' EXIT

# ---------------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------------
# One awk pass per string, a character at a time. bash's own ${s//...} is quadratic in bash 3.2
# (36 s for the 19 KB alias-check capture), and its replacement quoting differs between 3.2 and
# 4.3+ and again under 5.2's patsub_replacement. awk's gsub differs between awks in how it reads
# backslashes, so this uses neither. LC_ALL=C makes awk work on bytes, so UTF-8 passes through.
# shellcheck disable=SC2016 # $0 and the escapes are awk's, not the shell's
JSON_AWK='
    NR > 1 { printf "%s", "\\n" }
    {
        n = length($0)
        for (i = 1; i <= n; i++) {
            c = substr($0, i, 1)
            if (c == "\\") printf "%s", "\\\\"
            else if (c == "\"") printf "%s", "\\\""
            else if (c == "\t") printf "%s", "\\t"
            else if (c == "\r") printf "%s", "\\r"
            else if (c >= " ") printf "%s", c
        }
    }'

json_str() {
    printf '"'
    printf '%s' "$1" | LC_ALL=C awk "$JSON_AWK"
    printf '"'
}

# A command line, each word shell-quoted, so a printed command can be pasted.
render() {
    local out="" word
    for word in "$@"; do
        out="${out:+$out }$(printf '%q' "$word")"
    done
    printf '%s' "$out"
}

FIRST_CAPTURE=1

# emit SECTION NAME COMMAND EXIT_CODE TIMED_OUT SKIPPED STDOUT STDERR (EXIT_CODE "" when skipped).
emit() {
    local section="$1" name="$2" command="$3" rc="$4" timed_out="$5" skipped="$6" out="$7" err="$8" line
    if [[ "$JSON" -eq 1 ]]; then
        if [[ "$FIRST_CAPTURE" -eq 1 ]]; then
            FIRST_CAPTURE=0
        else
            printf ',\n'
        fi
        printf '    {"section": %s, "name": %s, "command": %s, ' "$(json_str "$section")" "$(json_str "$name")" "$(json_str "$command")"
        if [[ -n "$skipped" ]]; then
            printf '"exit_code": null, "timed_out": false, "skipped": %s, ' "$(json_str "$skipped")"
        else
            printf '"exit_code": %s, "timed_out": %s, "skipped": null, ' "$rc" "$timed_out"
        fi
        printf '"stdout": %s, "stderr": %s}' "$(json_str "$out")" "$(json_str "$err")"
        return 0
    fi
    if [[ -n "$skipped" ]]; then
        printf -- '-- %s: skipped: %s\n' "$name" "$skipped"
        return 0
    fi
    if [[ "$timed_out" == true ]]; then
        printf -- '-- %s: %s (timed out after %ss; exit %s)\n' "$name" "$command" "$TIMEOUT" "$rc"
    else
        printf -- '-- %s: %s (exit %s)\n' "$name" "$command" "$rc"
    fi
    [[ -z "$out" ]] || printf '%s\n' "$out"
    if [[ -n "$err" ]]; then
        while IFS= read -r line; do
            printf 'stderr: %s\n' "$line"
        done <<<"$err"
    fi
}

begin_section() {
    [[ "$JSON" -eq 1 ]] || printf '\n== %s\n' "$1"
}

skip() {
    emit "$1" "$2" "$3" "" false "$4" "" ""
}

# capture SECTION NAME COMMAND... -- run it with stdin from /dev/null, kill it after TIMEOUT
# seconds, and emit the result. Bash 3.2 has no timeout builtin, hence the poll (the pattern of
# util/headless_signing_preflight.bash's run_bounded). It counts centiseconds and polls every
# 10 ms for the first 0.2 s, where most commands finish, then every 100 ms.
capture() {
    local section="$1" name="$2" command pid waited=0 limit rc=0 timed_out=false out err
    shift 2
    command="$(render "$@")"
    # bash 3.2 reports a background job's failed exec as exit 1, not 127, so a program that is
    # missing or not executable is recorded here with the code a foreground run gives it.
    if ! command -v "$1" >/dev/null 2>&1; then
        emit "$section" "$name" "$command" 127 false "" "" "${1}: command not found"
        return 0
    fi
    limit=$((TIMEOUT * 100))
    "$@" </dev/null >"${TMP_DIR}/out" 2>"${TMP_DIR}/err" &
    pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        if [[ "$waited" -ge "$limit" ]]; then
            kill -KILL "$pid" 2>/dev/null || true
            timed_out=true
            break
        fi
        if [[ "$waited" -lt 20 ]]; then
            sleep 0.01
            waited=$((waited + 1))
        else
            sleep 0.1
            waited=$((waited + 10))
        fi
    done
    wait "$pid" 2>/dev/null || rc=$?
    out="$(<"${TMP_DIR}/out")"
    err="$(<"${TMP_DIR}/err")"
    emit "$section" "$name" "$command" "$rc" "$timed_out" "" "$out" "$err"
}

# ---------------------------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------------------------
probe_hardware() {
    capture hardware sysctl "$SYSCTL" machdep.cpu.brand_string hw.ncpu hw.physicalcpu hw.memsize kern.hv_support
    capture hardware sw_vers "$SW_VERS"
    capture hardware uname-m "$UNAME" -m
}

probe_memory() {
    capture memory vm_stat "$VM_STAT"
    capture memory swapusage "$SYSCTL" vm.swapusage
}

probe_docker() {
    capture docker pgrep:com.docker.backend "$PGREP" -x com.docker.backend
    capture docker "pgrep:Docker Desktop" "$PGREP" -x "Docker Desktop"
    capture docker pgrep:Docker "$PGREP" -x Docker
}

probe_hypervisor() {
    capture hypervisor vboxmanage-version "$VBOXMANAGE" --version
    capture hypervisor vboxmanage-list-vms "$VBOXMANAGE" list vms
    capture hypervisor vboxmanage-showvminfo "$VBOXMANAGE" showvminfo "$VM" --machinereadable
}

probe_disk() {
    if [[ -d /System/Volumes/Data ]]; then
        capture disk df "$DF" -k / /System/Volumes/Data
    else
        capture disk df "$DF" -k /
    fi
}

probe_power() {
    capture power pmset "$PMSET" -g
}

probe_network() {
    capture network ifconfig "$IFCONFIG" -a
}

probe_security() {
    local dirs=() d
    capture security csrutil-status "$CSRUTIL" status
    capture security csrutil-authenticated-root "$CSRUTIL" authenticated-root status
    capture security fdesetup-status "$FDESETUP" status
    capture security firewall-globalstate "$SOCKETFILTERFW" --getglobalstate
    capture security firewall-stealthmode "$SOCKETFILTERFW" --getstealthmode
    for d in "${HOME}/.ssh" "${HOME}/.gnupg"; do
        [[ ! -d "$d" ]] || dirs+=("$d")
    done
    if [[ "${#dirs[@]}" -eq 0 ]]; then
        skip security key-material-names "$(render "$FIND" "${HOME}/.ssh" "${HOME}/.gnupg")" "absent: ${HOME}/.ssh and ${HOME}/.gnupg"
    else
        capture security key-material-names "$FIND" -H "${dirs[@]}" "(" -name "*.asc" -o -iname "*recovery*" ")" -print
    fi
    if [[ -d "${HOME}/.ssh" ]]; then
        capture security ssh-loose-files "$FIND" -H "${HOME}/.ssh" -type f ! -name "*.pub" ! -name "known_hosts*" \
            "(" -perm -040 -o -perm -020 -o -perm -010 -o -perm -004 -o -perm -002 -o -perm -001 ")" -print
    else
        skip security ssh-loose-files "$(render "$FIND" "${HOME}/.ssh")" "absent: ${HOME}/.ssh"
    fi
}

probe_toolchain() {
    local t found rc
    for t in $TOOLS; do
        rc=0
        found="$(type -P "$t")" || rc=$?
        emit toolchain "command-v:${t}" "type -P ${t}" "$rc" false "" "$found" ""
    done
    capture toolchain kubectl-version "$KUBECTL" version --client -o json
}

probe_env() {
    capture env conda-env-list "$CONDA" env list
    if [[ -f "${ROOT}/AGENTS.md" ]]; then
        capture env parent-agents-md "$SHASUM" -a 256 "${ROOT}/AGENTS.md"
    else
        skip env parent-agents-md "$(render "$SHASUM" -a 256 "${ROOT}/AGENTS.md")" "absent: ${ROOT}/AGENTS.md"
    fi
}

probe_git() {
    if [[ -f "$ALIAS_CHECK" ]]; then
        capture git git-remote-alias-check "$PYTHON" -I "$ALIAS_CHECK" --json --root "$ROOT"
    else
        skip git git-remote-alias-check "$(render "$PYTHON" -I "$ALIAS_CHECK" --json --root "$ROOT")" "absent: ${ALIAS_CHECK}"
    fi
}

probe_signing() {
    if [[ -f "$SIGNING_CHECK" ]]; then
        capture signing configure-commit-signing "$PYTHON" -I "$SIGNING_CHECK" --check --json --root "$ROOT"
    else
        skip signing configure-commit-signing "$(render "$PYTHON" -I "$SIGNING_CHECK" --check --json --root "$ROOT")" "absent: ${SIGNING_CHECK}"
    fi
    if [[ ! -f "$SIGNING_PREFLIGHT" ]]; then
        skip signing headless-signing-preflight "$(render "$BASH" "$SIGNING_PREFLIGHT" --repo "${ROOT}/juniper-ml")" "absent: ${SIGNING_PREFLIGHT}"
    elif [[ ! -d "${ROOT}/juniper-ml" ]]; then
        skip signing headless-signing-preflight "$(render "$BASH" "$SIGNING_PREFLIGHT" --repo "${ROOT}/juniper-ml")" "absent: ${ROOT}/juniper-ml"
    else
        capture signing headless-signing-preflight "$BASH" "$SIGNING_PREFLIGHT" --repo "${ROOT}/juniper-ml"
    fi
}

# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------
HOST="$("$HOSTNAME_BIN" -s 2>/dev/null)" || HOST=""
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ "$JSON" -eq 1 ]]; then
    printf '{\n'
    printf '  "schema": 1,\n'
    printf '  "tool": "util/host_state_probe.bash",\n'
    printf '  "host": %s,\n' "$(json_str "$HOST")"
    printf '  "collected_at": %s,\n' "$(json_str "$NOW")"
    printf '  "bash_version": %s,\n' "$(json_str "$BASH_VERSION")"
    printf '  "home": %s,\n' "$(json_str "$HOME")"
    printf '  "path": %s,\n' "$(json_str "$PATH")"
    printf '  "root": %s,\n' "$(json_str "$ROOT")"
    printf '  "vm": %s,\n' "$(json_str "$VM")"
    printf '  "timeout_seconds": %s,\n' "$TIMEOUT"
    printf '  "sections": ['
    sep=""
    for s in $SECTIONS; do
        printf '%s%s' "$sep" "$(json_str "$s")"
        sep=", "
    done
    printf '],\n'
    printf '  "captures": [\n'
else
    printf 'host state probe (read-only): %s at %s\n' "${HOST:-?}" "$NOW"
    printf 'bash      %s\n' "$BASH_VERSION"
    printf 'root      %s\n' "$ROOT"
    printf 'sections  %s\n' "$SECTIONS"
fi

for s in $SECTIONS; do
    begin_section "$s"
    "probe_${s}"
done

if [[ "$JSON" -eq 1 ]]; then
    [[ "$FIRST_CAPTURE" -eq 1 ]] || printf '\n'
    printf '  ]\n'
    printf '}\n'
fi
