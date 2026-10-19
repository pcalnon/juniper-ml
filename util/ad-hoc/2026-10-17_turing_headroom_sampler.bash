#!/usr/bin/env bash
########################################################################################################################################################################################################
# Sample turing's memory headroom at a fixed interval, for the F3 baseline (dev mode or node mode).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-17
# Status:     ad-hoc — investigation (turing bring-up task F3: memory-headroom baseline)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§6 F3, §9.3 G-MEM, D1);
#             util/ad-hoc/2026-10-17_turing_headroom_summarize.py turns the samples into p5/p50/p95.
#
########################################################################################################################################################################################################
# Notes and Warnings:
#
# - READ-ONLY on the host. It runs vm_stat, sysctl, memory_pressure -Q and pgrep, each bounded by `timeout` (task D0).
# - F3 wants at least 480 samples per mode at 60 s: 8 hours each. "node" mode means desktop apps and Docker Desktop
#   are quit and no VM is running; the owner sets that state, this script only labels the rows.
# - Output is one tab-separated row per sample, with a header row when the file is new:
#     ts_utc mode page_size pages_free pages_speculative pages_inactive pages_active pages_wired pages_compressor
#     swap_total_mib swap_used_mib free_pct docker
#   A probe that fails or times out records an empty field rather than stopping the run.
#
# Usage:
#   bash util/ad-hoc/2026-10-17_turing_headroom_sampler.bash --mode dev|node [--out FILE] [--interval 60] [--samples 480]
#
#   The default FILE is $HOME/.local/state/juniper/turing-headroom/<mode>.tsv, outside any checkout, so the run
#   survives a worktree being removed. Exit 0 after the last sample, 2 for usage errors or a missing tool.
#
########################################################################################################################################################################################################
# Deliberately not -e or pipefail: the first 2026-10-17 run died silently after 307 of 480 samples, with no reboot,
# sleep or kill on record. Every probe below already tolerates its own failure, so an error must never end the run.
# The EXIT trap leaves a line in the log for any exit, so an early stop can be explained.
set -u

VM_STAT="${VM_STAT:-vm_stat}"
SYSCTL="${SYSCTL:-/usr/sbin/sysctl}"
MEMORY_PRESSURE="${MEMORY_PRESSURE:-/usr/bin/memory_pressure}"
PGREP="${PGREP:-/usr/bin/pgrep}"
TIMEOUT="${TIMEOUT:-timeout}"
PROBE_SECONDS="${PROBE_SECONDS:-15}"

# One vm_stat field by its label ("Pages free", ...), without the trailing dot. Empty when absent.
vm_field() {
    printf '%s\n' "$1" | awk -v label="$2" -F: '$1 == label { gsub(/[ .]/, "", $2); print $2; exit }'
}

# vm.swapusage "total = 15360.00M  used = 13684.00M ..." -> the named value in whole MiB. Empty when absent.
swap_mib() {
    printf '%s\n' "$1" | awk -v key="$2" '{
        for (i = 1; i < NF; i++) {
            if ($i == key && $(i + 1) == "=") {
                v = $(i + 2); unit = substr(v, length(v), 1); n = substr(v, 1, length(v) - 1) + 0
                if (unit == "G") n = n * 1024; else if (unit == "K") n = n / 1024
                printf "%d\n", n; exit
            }
        }
    }'
}

usage() {
    sed -n '/^# Usage:/,/^####/p' "$0" | sed -e 's/^# \{0,1\}//' -e '/^####/d'
}

mode=""
out=""
interval=60
samples=480
while [ $# -gt 0 ]; do
    case "$1" in
        --mode) mode="${2:-}"; shift 2 ;;
        --out) out="${2:-}"; shift 2 ;;
        --interval) interval="${2:-}"; shift 2 ;;
        --samples) samples="${2:-}"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

case "$mode" in
    dev|node) ;;
    *) echo "ERROR: --mode must be dev or node" >&2; exit 2 ;;
esac
case "$interval$samples" in
    *[!0-9]*|"") echo "ERROR: --interval and --samples must be positive integers" >&2; exit 2 ;;
esac
if [ "$interval" -lt 1 ] || [ "$samples" -lt 1 ]; then
    echo "ERROR: --interval and --samples must be positive integers" >&2
    exit 2
fi
for tool in "$TIMEOUT" "$VM_STAT" "$SYSCTL"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "ERROR: required tool not found: $tool" >&2
        exit 2
    fi
done

out="${out:-$HOME/.local/state/juniper/turing-headroom/${mode}.tsv}"
mkdir -p "$(dirname "$out")"
if [ ! -s "$out" ]; then
    printf 'ts_utc\tmode\tpage_size\tpages_free\tpages_speculative\tpages_inactive\tpages_active\tpages_wired\tpages_compressor\tswap_total_mib\tswap_used_mib\tfree_pct\tdocker\n' >"$out"
fi

taken=0
trap 'echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) sampler exiting (rc=$?) after ${taken} of ${samples} sample(s) to ${out}" >&2' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
while [ "$taken" -lt "$samples" ]; do
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    vm="$("$TIMEOUT" "$PROBE_SECONDS" "$VM_STAT" 2>/dev/null || true)"
    swap="$("$TIMEOUT" "$PROBE_SECONDS" "$SYSCTL" -n vm.swapusage 2>/dev/null || true)"
    pressure="$("$TIMEOUT" "$PROBE_SECONDS" "$MEMORY_PRESSURE" -Q 2>/dev/null || true)"
    page_size="$(printf '%s\n' "$vm" | sed -n 's/.*page size of \([0-9][0-9]*\) bytes.*/\1/p' | head -n 1)"
    free_pct="$(printf '%s\n' "$pressure" | sed -n 's/.*free percentage: \([0-9][0-9]*\)%.*/\1/p' | head -n 1)"
    docker=0
    if "$TIMEOUT" "$PROBE_SECONDS" "$PGREP" -x "Docker Desktop" >/dev/null 2>&1 || "$TIMEOUT" "$PROBE_SECONDS" "$PGREP" -f com.docker.backend >/dev/null 2>&1; then
        docker=1
    fi
    p_free="$(vm_field "$vm" "Pages free")"
    p_spec="$(vm_field "$vm" "Pages speculative")"
    p_inact="$(vm_field "$vm" "Pages inactive")"
    p_act="$(vm_field "$vm" "Pages active")"
    p_wired="$(vm_field "$vm" "Pages wired down")"
    p_comp="$(vm_field "$vm" "Pages occupied by compressor")"
    s_total="$(swap_mib "$swap" total)"
    s_used="$(swap_mib "$swap" used)"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$ts" "$mode" "$page_size" \
        "$p_free" "$p_spec" "$p_inact" "$p_act" "$p_wired" "$p_comp" "$s_total" "$s_used" "$free_pct" "$docker" >>"$out"
    taken=$((taken + 1))
    if [ "$taken" -lt "$samples" ]; then
        sleep "$interval"
    fi
done
echo "wrote $taken sample(s) to $out"
