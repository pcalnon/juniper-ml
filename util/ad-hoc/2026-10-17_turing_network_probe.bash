#!/usr/bin/env bash
########################################################################################################################################################################################################
# Read-only network-path probe for a macOS host: the Wi-Fi radio link, the local hop, the internet path, and loaded capacity.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon (authored via Claude Code)
# Created:    2026-10-17
# Status:     ad-hoc — investigation (why large createCommitOnBranch uploads from turing fail with HTTP 499)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§2.2 network; task F2, gate G-NET);
#             util/ad-hoc/2026-10-17_push_signed_with_retry.py (the uploads that failed)
#
########################################################################################################################################################################################################
# Notes and Warnings:
#
# - READ-ONLY, no sudo, no credentials. It runs route, ifconfig, system_profiler, ping and (unless --no-load) networkQuality.
#   networkQuality saturates the link for about 20 s; don't run it while landing commits.
# - It prints no network names. Other radios are matched against the current SSID and reported by band, channel and level.
# - Run it on two hosts (say turing on Wi-Fi and yamaguchi) to compare the same path from each.
#
# Usage:
#   bash util/ad-hoc/2026-10-17_turing_network_probe.bash [--pings N] [--no-load]
#
########################################################################################################################################################################################################
set -uo pipefail

PINGS=50
LOAD=1
while [ $# -gt 0 ]; do
    case "$1" in
        --pings) PINGS="${2:-}"; shift 2 ;;
        --no-load) LOAD=0; shift ;;
        -h|--help) sed -n '/^# Usage:/,/^####/p' "$0" | sed -e 's/^# \{0,1\}//' -e '/^####/d'; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
    esac
done
case "$PINGS" in ''|*[!0-9]*) echo "ERROR: --pings needs a whole number" >&2; exit 2 ;; esac

section() { printf '\n== %s\n' "$1"; }

section "host"
printf '%s  %s  %s\n' "$(hostname -s)" "$(sw_vers -productVersion 2>/dev/null)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

section "routes"
gw="$(route -n get default 2>/dev/null | awk '/gateway:/{print $2}')"
gw_if="$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')"
gh_if="$(route -n get api.github.com 2>/dev/null | awk '/interface:/{print $2}')"
echo "default via ${gw:-?} on ${gw_if:-?}; api.github.com via ${gh_if:-?}"
for i in $(ifconfig -l); do
    addr="$(ifconfig "$i" 2>/dev/null | awk '/inet /{print $2; exit}')"
    [ -n "$addr" ] || continue
    mtu="$(ifconfig "$i" 2>/dev/null | awk '/mtu/{for (k = 1; k < NF; k++) if ($k == "mtu") print $(k + 1); exit}')"
    media="$(ifconfig "$i" 2>/dev/null | awk -F': ' '/media:/{print $2; exit}')"
    printf '  %-7s %-16s mtu %-6s %s\n' "$i" "$addr" "$mtu" "$media"
done

section "Wi-Fi radio link"
system_profiler SPAirPortDataType 2>/dev/null | python3 -c '
import re, sys
text = sys.stdin.read()
if "Current Network Information:" not in text:
    print("not associated to Wi-Fi"); sys.exit(0)
cur = text.split("Current Network Information:", 1)[1]
ssid = cur.strip().splitlines()[0].strip().rstrip(":")
body = cur.split("Other Local Wi-Fi Networks:", 1)[0]
def field(name, src):
    m = re.search(rf"{name}: (.*)", src)
    return m.group(1).strip() if m else "?"
sn = re.search(r"Signal / Noise: (-?\d+) dBm / (-?\d+) dBm", body)
snr = f"{int(sn.group(1)) - int(sn.group(2))} dB" if sn else "?"
phy, chan, level, rate, mcs = (field(k, body) for k in ("PHY Mode", "Channel", "Signal / Noise", "Transmit Rate", "MCS Index"))
security = field("Security", body)
print(f"current: {phy}, channel {chan}, signal/noise {level} (SNR {snr}), tx rate {rate} Mbps, MCS {mcs}, security {security}")
others = cur.split("Other Local Wi-Fi Networks:", 1)[1] if "Other Local Wi-Fi Networks:" in cur else ""
own = []
foreign = 0
for name, blk in re.findall(r"^\s{12}(\S.*?):\n(.*?)(?=^\s{12}\S.*?:\n|\Z)", others, re.M | re.S):
    ch = re.search(r"Channel: (\d+) \((\dGHz)", blk)
    s = re.search(r"Signal / Noise: (-?\d+) dBm / (-?\d+) dBm", blk)
    if name.strip() != ssid:
        foreign += 1
        continue
    if ch and s:
        own.append((int(s.group(1)), int(s.group(2)), ch.group(1), ch.group(2), field("PHY Mode", blk), field("Security", blk)))
print(f"other radios with the same network name: {len(own)}; foreign networks visible: {foreign}")
for sig, noise, chan, band, rphy, rsec in sorted(own, reverse=True):
    print(f"  {band} channel {chan:>3}: signal/noise {sig}/{noise} dBm (SNR {sig - noise} dB), {rphy}, {rsec}")
'

section "local hop: ping the gateway ${gw:-?} (${PINGS} at 0.2 s)"
[ -n "$gw" ] && ping -c "$PINGS" -i 0.2 -q "$gw" 2>&1 | tail -2
section "internet path: ping 1.1.1.1 (${PINGS} at 0.2 s)"
ping -c "$PINGS" -i 0.2 -q 1.1.1.1 2>&1 | tail -2

if [ "$LOAD" -eq 1 ]; then
    section "loaded capacity and responsiveness (networkQuality -s)"
    networkQuality -s 2>&1 | grep -E 'capacity|Responsiveness|Idle Latency' || echo "networkQuality unavailable"
fi
