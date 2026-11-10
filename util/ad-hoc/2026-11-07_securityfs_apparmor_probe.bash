#!/usr/bin/env bash
# Read-only evidence capture for the yamaguchi securityfs / AppArmor incident (2026-10-27 unmount, 2026-11-07 report).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-07
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md
#             notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md
#
# What it does
#   Prints, section by section, every host fact the root-cause analysis rests on: the kernel's
#   AppArmor state, which of systemd's API filesystems are mounted, systemd's own record of when
#   the /sys mounts changed state, the start times of the daemons that cached AppArmor support,
#   Docker's view, the AppArmor consumers that are failing (snap-confine, Docker, snapd refresh),
#   the Kubernetes install's state on this host, and the journal's retention. Each section prints
#   the command it ran, so the output can be re-derived by hand.
#
#   It is READ-ONLY and needs no root. It writes nothing but stdout. Run it before and after the
#   remediation in the runbook, and diff the two outputs.
#
# Usage
#   bash util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash > reports/<dir>/<UTC>_probe.txt
#
# Exit status: always 0 (a probe that cannot read something says so in its output).
set -uo pipefail

section() { printf '\n==== %s ====\n' "$*"; }
run() {
    # Print the command, then its output (stdout+stderr), then its exit code.
    printf '$ %s\n' "$*"
    "$@" 2>&1
    printf '[exit=%s]\n' "$?"
}

section "1. identity"
run date -u '+%Y-%m-%dT%H:%M:%SZ'
run hostname
run uname -r
run grep -E '^PRETTY_NAME=' /etc/os-release
run uptime -s
run systemctl --version
run docker version --format 'client={{.Client.Version}} server={{.Server.Version}} api={{.Server.APIVersion}}'
run snap version
run apparmor_parser --version

section "2. kernel AppArmor state (procfs and module parameter need no securityfs)"
run cat /sys/module/apparmor/parameters/enabled
run cat /proc/self/attr/apparmor/current
run grep -E '^CONFIG_(LSM|SECURITY_APPARMOR|SECURITYFS)=' "/boot/config-$(uname -r)"
# The kernel command line decides whether AppArmor is the active LSM (lsm= / apparmor= / security=).
# The root filesystem UUID is redacted: the output is committed to a public repository.
run sed -E 's/UUID=[^ ]+/UUID=<redacted>/g' /proc/cmdline

section "3. systemd API filesystems: expected vs mounted (from /proc/self/mountinfo)"
# where|fstype|origin. 'pid1' = mounted by PID 1's mount_setup() (src/shared/mount-setup.c, no unit
# file); 'unit' = a static unit file under /usr/lib/systemd/system. A 'pid1' row is only expected when
# its directory exists (pstore/bpf/efivarfs are conditional on kernel/firmware support).
printf '$ (awk over /proc/self/mountinfo for each expected API mount)\n'
printf '%-28s %-11s %-5s %-9s %-8s %s\n' WHERE FSTYPE FROM STATE MOUNT_ID PROPAGATION
for row in \
    "/sys/kernel/security|securityfs|pid1" \
    "/sys/fs/cgroup|cgroup2|pid1" \
    "/sys/fs/pstore|pstore|pid1" \
    "/sys/firmware/efi/efivars|efivarfs|pid1" \
    "/sys/fs/bpf|bpf|pid1" \
    "/sys/kernel/debug|debugfs|unit" \
    "/sys/kernel/tracing|tracefs|unit" \
    "/sys/kernel/config|configfs|unit" \
    "/sys/fs/fuse/connections|fusectl|unit" \
    "/dev/hugepages|hugetlbfs|unit" \
    "/dev/mqueue|mqueue|unit"; do
    IFS='|' read -r where fstype origin <<< "$row"
    line="$(awk -v w="$where" '$5 == w { print }' /proc/self/mountinfo | tail -n 1)"
    if [[ -n "$line" ]]; then
        id="$(awk '{ print $1 }' <<< "$line")"
        prop="$(awk '{ for (i = 7; i <= NF && $i != "-"; i++) printf "%s ", $i }' <<< "$line")"
        state=MOUNTED
    elif [[ ! -d "$where" ]]; then
        id=-; prop=-; state=N/A
    else
        id=-; prop=-; state=MISSING
    fi
    printf '%-28s %-11s %-5s %-9s %-8s %s\n' "$where" "$fstype" "$origin" "$state" "$id" "$prop"
done
run ls -la /sys/kernel/security/
run stat -c '%n %F mtime=%y' /sys/kernel/security /sys/kernel/security/apparmor/profiles
run findmnt -R /sys -o TARGET,FSTYPE,ID,PROPAGATION

section "4. systemd's record of the /sys and /dev API mount units (state-change times, UTC)"
run systemctl show --timestamp=us+utc -p Id -p LoadState -p ActiveState -p FragmentPath \
    -p InactiveEnterTimestamp -p ActiveEnterTimestamp \
    sys-kernel-security.mount sys-fs-pstore.mount sys-fs-bpf.mount sys-firmware-efi-efivars.mount \
    sys-kernel-debug.mount sys-kernel-tracing.mount sys-kernel-config.mount sys-fs-fuse-connections.mount \
    dev-hugepages.mount dev-mqueue.mount proc-sys-fs-binfmt_misc.automount snapd.mounts.target

section "5. start times of the processes that cache AppArmor support (and their neighbours)"
for name in systemd containerd dockerd snapd expressvpn-daemon; do
    for pid in $(pgrep -x "$name" 2>/dev/null | head -3); do
        printf 'pid=%-8s start=%-26s cmd=%s\n' "$pid" "$(ps -o lstart= -p "$pid")" "$(ps -o args= -p "$pid" | cut -c1-120)"
    done
done

section "6. Docker's view"
run docker info --format 'SecurityOptions={{json .SecurityOptions}} Warnings={{json .Warnings}}'
run docker ps -a --format '{{.Names}}\t{{.State}}\t{{.Status}}\t{{.CreatedAt}}'

section "7. failing AppArmor consumers (journal; unit-indexed queries only, so this stays fast)"
printf '$ journalctl -u snap.kubelet.daemon.service | grep -c aa_is_enabled ; first ; last\n'
journalctl -u snap.kubelet.daemon.service --no-pager -o short-iso 2>/dev/null | grep -c 'aa_is_enabled' || true
journalctl -u snap.kubelet.daemon.service --no-pager -o short-iso 2>/dev/null | grep -m1 'aa_is_enabled' | cut -c1-200
journalctl -u snap.kubelet.daemon.service --no-pager -o short-iso -n 50 2>/dev/null | grep 'aa_is_enabled' | tail -1 | cut -c1-200
printf '$ journalctl -u docker.service | grep -c "Could not check if docker-default" ; first ; last\n'
journalctl -u docker.service --no-pager -o short-iso 2>/dev/null | grep -c 'Could not check if docker-default' || true
journalctl -u docker.service --no-pager -o short-iso 2>/dev/null | grep -m1 'Could not check if docker-default' | cut -c1-220
journalctl -u docker.service --no-pager -o short-iso 2>/dev/null | grep 'Could not check if docker-default' | tail -1 | cut -c1-220
run snap changes

section "8. Kubernetes install state on this host (the remediation must leave this unchanged)"
run apt-mark showhold
printf '$ dpkg-query -W kubeadm kubelet kubectl kubernetes-cni containerd.io docker-ce\n'
dpkg-query -W -f='${Package} ${Version} ${db:Status-Abbrev}\n' kubeadm kubelet kubectl kubernetes-cni containerd.io docker-ce 2>&1
run systemctl show -p Id -p UnitFileState -p ActiveState -p SubState -p NRestarts kubelet.service containerd.service docker.service
printf '$ systemctl show (legacy snap k8s services)\n'
for unit in snap.kubelet.daemon snap.kube-apiserver.daemon snap.kube-proxy.daemon snap.kube-scheduler.daemon \
            snap.kube-controller-manager.daemon snap.etcd.etcd; do
    systemctl show "${unit}.service" -p Id -p UnitFileState -p ActiveState -p SubState -p Result -p NRestarts 2>&1 | paste -sd' '
done
run ls -la --time-style=full-iso /etc/kubernetes /etc/kubernetes/manifests /var/lib/kubelet
printf '$ ss -ltnH (k8s control-plane / node ports only)\n'
ss -ltnH 2>/dev/null | awk '{ print $4 }' | grep -E ':(6443|2379|2380|10248|10249|10250|10255|10256|10257|10259)$' || echo "(none listening)"

section "9. residual desktop FUSE mounts the same unmount took (user session)"
for where in "/run/user/$(id -u)/doc" "/run/user/$(id -u)/gvfs"; do
    if awk -v w="$where" '$5 == w { found = 1 } END { exit !found }' /proc/self/mountinfo; then
        printf '%-28s MOUNTED\n' "$where"
    else
        printf '%-28s MISSING\n' "$where"
    fi
done

section "10. journal retention (why the original actor left no log)"
run journalctl --disk-usage
printf '$ journalctl --no-pager -o short-iso | head -1   (oldest retained entry)\n'
journalctl --no-pager -o short-iso 2>/dev/null | head -1 | cut -c1-160
for unit in snap.kubelet.daemon.service fluent-bit.service; do
    printf '$ journalctl -u %s --since -1h | wc -l\n' "$unit"
    journalctl -u "$unit" --since -1h --no-pager 2>/dev/null | wc -l
done
run grep -hE '^\s*(SystemMaxUse|SystemKeepFree|MaxRetentionSec|MaxFileSec)=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d/

exit 0
