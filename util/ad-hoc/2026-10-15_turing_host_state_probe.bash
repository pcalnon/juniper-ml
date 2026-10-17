#!/usr/bin/env bash
########################################################################################################################################################################################################
# Read-only host-state probe for the turing bring-up (hardware, OS, network, security posture, toolchain, git remotes/signing config).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-15
# Status:     ad-hoc — investigation (turing host bring-up evidence capture)
# Retire when: util/host_state_probe.bash lands (plan task T1.1) and supersedes it
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (Appendix A is this script's output)
#
########################################################################################################################################################################################################
# Notes and Warnings:
#
# - READ-ONLY. Changes nothing on the host.
# - Deliberately does NOT touch live credentials: no ssh-agent listing, no gh token status, no smartcard query.
#   Those are operator-run checks (plan §14.1) because they need the owner present (YubiKey PIN / touch).
# - macOS-only (sysctl/pmset/fdesetup/csrutil/networksetup).
#
# Usage:
#   bash util/ad-hoc/2026-10-15_turing_host_state_probe.bash [JUNIPER_ROOT]
#
########################################################################################################################################################################################################
set -u

JUNIPER_ROOT="${1:-${HOME}/Development/python/Juniper}"

section() { printf '\n== %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

section "hardware"
sysctl -n machdep.cpu.brand_string hw.ncpu hw.physicalcpu hw.memsize kern.hv_support
sw_vers
uname -m

section "disk"
df -h / /System/Volumes/Data
diskutil info / | grep -E "Solid State|Container Total|Container Free"

section "memory"
vm_stat | head -6
sysctl vm.swapusage
memory_pressure 2>/dev/null | tail -1

section "network"
for i in en0 en5 en6 en7; do
    printf '%s ip=%s %s\n' "$i" "$(ipconfig getifaddr "$i" 2>/dev/null)" "$(ifconfig "$i" 2>/dev/null | grep -E 'status|media' | tr '\n' ' ')"
done
networksetup -listallhardwareports

section "power"
pmset -g | grep -E "sleep|disksleep|womp|autorestart|powernap|standby"

section "security"
fdesetup status
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
csrutil status

section "toolchain"
for t in brew git gh gpg gpg-agent ykman pinentry-mac conda python3 uv pre-commit shellcheck markdownlint-cli2 yamllint sops age node jq yq actionlint timeout iperf3 VBoxManage docker kubectl helm claude; do
    if have "$t"; then
        printf '%-18s %-45s %s\n' "$t" "$(command -v "$t")" "$("$t" --version 2>/dev/null | head -1)"
    else
        printf '%-18s MISSING\n' "$t"
    fi
done

section "hypervisor"
have VBoxManage && { VBoxManage --version; VBoxManage list vms; VBoxManage list runningvms; }

section "conda"
have conda && conda env list | grep -v '^#'

section "git"
git config --global --list --show-origin | grep -v -i -E "token|password"
for r in "${JUNIPER_ROOT}"/juniper-*; do
    [[ -e "${r}/.git" ]] || { printf '%-24s not a git checkout\n' "$(basename "$r")"; continue; }
    printf '%-24s url=%-62s gpgsign=%-5s signingkey=%-8s last5sig=%s\n' \
        "$(basename "$r")" \
        "$(git -C "$r" remote get-url origin)" \
        "$(git -C "$r" config commit.gpgsign)" \
        "$(git -C "$r" config user.signingkey >/dev/null && echo set || echo unset)" \
        "$(git -C "$r" log -5 --format=%G? | tr -d '\n')"
done

section "ssh config (Host aliases only)"
grep -E '^\s*(Host|IdentityFile)\s' "${HOME}/.ssh/config"
stat -f '%Sp %N' "${HOME}/.ssh/config" "${HOME}/.ssh"/*.pem 2>/dev/null
