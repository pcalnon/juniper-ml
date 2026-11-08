#!/usr/bin/env bash
# Validate the yamaguchi API-filesystem remount: capture state before, then prove efficacy and no regression after.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-07
# Status:     ad-hoc — remediation validation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md (§3, §5)
#             notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md
#             util/ad-hoc/2026-11-08_remount_validate_baseline_gate_check.py (checks the baseline gate below)
#
# Modes
#   capture FILE   Write a fingerprint of everything the remount must NOT change -- the Kubernetes install
#                  (held kubeadm/kubelet/kubectl, kubelet.service, /etc/kubernetes, /var/lib/kubelet,
#                  containerd's config, k8s listening ports, the juniper-k8s checkout), the daemons that
#                  must not restart (containerd, dockerd, PID 1), and the legacy snap k8s services -- to FILE.
#                  Then apply the baseline gate to FILE, so a capture that did not land is caught at once.
#   check FILE     Apply only the baseline gate to FILE. Reads FILE and nothing else.
#   verify FILE    Apply the baseline gate, run the efficacy checks, recapture the fingerprint, and diff it
#                  against FILE.
#
# Baseline gate (all three modes): FILE must be readable, not empty, and carry every key the fingerprint
# prints whatever the host's state (REQUIRED_KEYS). Otherwise check and verify refuse it, exit 2, before
# anything else runs. The gate fails closed: only the check's explicit "none" passes, so a check that dies
# is a refusal. A file that is not a fingerprint makes the diff report every current value as a
# difference. On 2026-11-08, runbook step 4 was run against an empty file: the probe's output file, left
# empty by the shell's redirect because the probe script was not there yet. It printed 22 "UNEXPECTED"
# lines for a host on which nothing unexpected had changed (RCA §14).
#
# Efficacy checks (verify):
#   E1  util/host_api_filesystems_check.py exits 0: every systemd API filesystem is mounted, AppArmor consistent
#   E2  /sys/kernel/security/apparmor/profiles exists (what dockerd opens before every start)
#   E3  juniper-deploy's scripts/preflight_apparmor.sh exits 0 ([OK]), when that checkout carries it
#   E4  a throwaway container (no network, removed on exit) runs CONFINED: its /proc/self/attr/current reads
#       "docker-default (enforce)" -- the start succeeds AND AppArmor is applied, not merely tolerated
#   E5  snap-confine works: `snap run helm version` succeeds (helm is a snap on yamaguchi, and its
#       failure is why juniper-deploy's 17 helm tests fail during the incident). Plain `version`, not
#       `--short`: the check is about snap-confine, so it must not depend on one helm major's flags.
#
# Regression check (verify): every fingerprint key must be unchanged, except the keys the runbook changes
# on purpose -- snap_service.* (runbook step 2 stops and disables the legacy snap k8s services) and
# mount.* (the remount itself). Those differences are printed as EXPECTED; any other is UNEXPECTED.
#
# Read-only except E4, which starts and removes one container with no network. Needs no root.
# Writes only FILE (capture).
# Exit: 0 pass; 1 an efficacy check failed, an UNEXPECTED difference, or a capture that is not a usable
# baseline; 2 usage, or FILE is not a usable baseline (check, verify).
set -uo pipefail

JUNIPER="${JUNIPER_ROOT:-$HOME/Development/python/Juniper}"
ML="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY="${JUNIPER_DEPLOY_DIR:-$JUNIPER/juniper-deploy}"
IMAGE="${VALIDATE_IMAGE:-ghcr.io/pcalnon/juniper-recurrence:0.8.0}"
SNAP_K8S_SERVICES=(snap.kubelet.daemon snap.kube-apiserver.daemon snap.kube-proxy.daemon snap.kube-scheduler.daemon
                   snap.kube-controller-manager.daemon snap.etcd.etcd)
API_MOUNT_POINTS=(/sys/kernel/security /sys/fs/pstore /sys/fs/bpf)

# The keys fingerprint() prints whatever the host's state: its printf lines. The dpkg-query and tree.* lines
# are left out, because they depend on what is installed. Built from the same arrays fingerprint() loops over.
REQUIRED_KEYS=(hold unit.kubelet containerd_config_sha256 k8s_listeners juniper_k8s_head pid.systemd pid.containerd pid.dockerd)
for unit in "${SNAP_K8S_SERVICES[@]}"; do REQUIRED_KEYS+=("snap_service.$unit"); done
for where in "${API_MOUNT_POINTS[@]}"; do REQUIRED_KEYS+=("mount.$where"); done

fingerprint() {
    printf 'hold=%s\n' "$(apt-mark showhold 2>/dev/null | sort | paste -sd,)"
    dpkg-query -W -f='pkg.${Package}=${Version} ${db:Status-Abbrev}\n' kubeadm kubelet kubectl kubernetes-cni containerd.io docker-ce 2>/dev/null
    printf 'unit.kubelet=%s/%s\n' "$(systemctl is-enabled kubelet.service 2>/dev/null)" "$(systemctl is-active kubelet.service 2>/dev/null)"
    for dir in /etc/kubernetes /var/lib/kubelet; do
        find "$dir" -printf "tree.%p=%y %m %s %TY-%Tm-%Td_%TH:%TM\n" 2>&1 | sort
    done
    printf 'containerd_config_sha256=%s\n' "$(sha256sum /etc/containerd/config.toml 2>/dev/null | cut -d' ' -f1)"
    printf 'k8s_listeners=%s\n' "$(ss -ltnH 2>/dev/null | awk '{ print $4 }' | grep -E ':(6443|2379|2380|10248|10249|10250|10255|10256|10257|10259)$' | sort | paste -sd, )"
    printf 'juniper_k8s_head=%s\n' "$(git -C "$JUNIPER/juniper-k8s" rev-parse HEAD 2>/dev/null)"
    printf 'pid.systemd=%s\n' "$(ps -o lstart= -p 1)"
    printf 'pid.containerd=%s\n' "$(pgrep -xo containerd)"
    printf 'pid.dockerd=%s\n' "$(pgrep -xo dockerd)"
    for unit in "${SNAP_K8S_SERVICES[@]}"; do
        printf 'snap_service.%s=%s/%s\n' "$unit" "$(systemctl is-enabled "${unit}.service" 2>/dev/null)" "$(systemctl is-active "${unit}.service" 2>/dev/null)"
    done
    for where in "${API_MOUNT_POINTS[@]}"; do
        printf 'mount.%s=%s\n' "$where" "$(findmnt -no FSTYPE,OPTIONS --mountpoint "$where" 2>/dev/null)"
    done
}

baseline_problem() {  # baseline_problem FILE: print why FILE is not a usable baseline, or "none" if it is one
    local file="$1" missing
    local -a absent
    if [[ ! -r "$file" ]]; then echo "no such file"; return; fi
    if [[ ! -s "$file" ]]; then echo "empty file"; return; fi
    # awk, not a bash associative array. A line that starts with "=" has an empty key, which bash rejects
    # ("bad array subscript") by abandoning the whole function. Its output is then empty, which the first
    # version of this gate read as "no problem", so it passed the probe's report, whose section headers
    # start with "====" (util/ad-hoc/2026-11-08_bash_empty_assoc_key_abort_repro.bash; RCA §14).
    missing="$(awk -F= -v keys="${REQUIRED_KEYS[*]}" '
        BEGIN { n = split(keys, want, " ") }
        index($0, "=") { have[$1] = 1 }
        END { for (i = 1; i <= n; i++) if (!(want[i] in have)) print want[i] }' "$file")" \
        || { echo "the key check itself failed"; return; }
    if [[ -n "$missing" ]]; then
        mapfile -t absent <<< "$missing"
        echo "not a fingerprint: ${#absent[@]} of ${#REQUIRED_KEYS[@]} required keys missing, the first being ${absent[0]}"
        return
    fi
    echo none
}

refuse() {  # refuse MODE FILE PROBLEM: say why FILE cannot be a baseline, and exit 2
    echo "$1: $2: $3" >&2
    echo "  A baseline is the file 'capture' writes BEFORE the remount (runbook step 1). The probe's report is" >&2
    echo "  not one. If no baseline was captured, runbook step 4 names the fallback." >&2
    exit 2  # refuse: not a usable baseline
}

gate() {  # gate MODE FILE: refuse FILE unless it is a usable baseline. Fails closed: only an explicit
          # "none" passes, so a check that died and printed nothing is a refusal, not a pass.
    local problem
    problem="$(baseline_problem "$2")"
    [[ "$problem" == none ]] || refuse "$1" "$2" "${problem:-the baseline check printed nothing}"
}

usage() { sed -n '2,/^set -uo/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//; /^set -uo/d'; }

mode="${1:-}"
file="${2:-}"
if [[ -z "$mode" || -z "$file" ]]; then
    usage >&2
    exit 2
fi

case "$mode" in
    capture)
        fingerprint > "$file"
        problem="$(baseline_problem "$file")"
        if [[ "$problem" != none ]]; then
            echo "capture: $file: ${problem:-the baseline check printed nothing} -- this capture is NOT a usable baseline" >&2
            exit 1
        fi
        echo "captured $(wc -l < "$file") fingerprint lines to $file (a usable baseline: all ${#REQUIRED_KEYS[@]} required keys)"
        exit 0
        ;;
    check)
        gate check "$file"
        echo "check: $file is a usable baseline ($(wc -l < "$file") lines, all ${#REQUIRED_KEYS[@]} required keys)"
        exit 0
        ;;
    verify)
        gate verify "$file"
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

failures=0
check() {  # check NAME COMMAND...  (prints PASS/FAIL with the command's last line)
    local name="$1"; shift
    local out rc
    out="$("$@" 2>&1)"; rc=$?
    if [[ $rc -eq 0 ]]; then
        printf '[PASS] %s  (%s)\n' "$name" "$(tail -n 1 <<< "$out")"
    else
        printf '[FAIL] %s  (exit %s: %s)\n' "$name" "$rc" "$(tail -n 1 <<< "$out")"
        failures=$((failures + 1))
    fi
}

echo "== efficacy"
check "E1 API filesystems mounted, AppArmor consistent" python3 "$ML/util/host_api_filesystems_check.py"
check "E2 AppArmor interface present" test -e /sys/kernel/security/apparmor/profiles
if [[ -f "$DEPLOY/scripts/preflight_apparmor.sh" ]]; then
    check "E3 juniper-deploy AppArmor preflight" bash "$DEPLOY/scripts/preflight_apparmor.sh"
else
    echo "[SKIP] E3 juniper-deploy AppArmor preflight (not in $DEPLOY yet: merge juniper-deploy's PR and pull)"
fi
label="$(docker run --rm --pull=never --network none --entrypoint cat "$IMAGE" /proc/self/attr/current 2>&1)"
if [[ "$label" == "docker-default (enforce)" ]]; then
    echo "[PASS] E4 a container starts confined  ($label)"
else
    echo "[FAIL] E4 a container starts confined  (got: $label)"
    failures=$((failures + 1))
fi
check "E5 snap-confine runs a snap" snap run helm version

echo "== regression (fingerprint vs $file)"
after="$(fingerprint)"
diffs="$(diff <(sort "$file") <(sort <<< "$after"))"
if [[ -z "$diffs" ]]; then
    echo "[PASS] fingerprint unchanged"
else
    unexpected=0
    while IFS= read -r line; do
        [[ "$line" =~ ^[\<\>]\  ]] || continue
        key="${line:2}"; key="${key%%=*}"
        if [[ "$key" == snap_service.* || "$key" == mount.* ]]; then
            echo "  EXPECTED   $line"
        else
            echo "  UNEXPECTED $line"
            unexpected=$((unexpected + 1))
        fi
    done <<< "$diffs"
    if [[ $unexpected -gt 0 ]]; then
        echo "[FAIL] $unexpected unexpected fingerprint difference(s)"
        failures=$((failures + 1))
    else
        echo "[PASS] only the runbook's intended differences"
    fi
fi

echo "== $( [[ $failures -eq 0 ]] && echo PASS || echo "FAIL ($failures)" )"
exit $(( failures == 0 ? 0 : 1 ))
