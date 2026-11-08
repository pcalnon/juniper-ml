#!/usr/bin/env bash
# Fetch, at the exact versions running on yamaguchi, the upstream source lines the securityfs RCA cites.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-07
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md
#
# Why: every mechanism claim in the RCA ("dockerd caches AppArmor support once", "snap-confine dies
# on ENOENT", "securityfs/pstore/bpf have no unit file; PID 1 mounts them", "a PID 1 re-exec runs
# mount_setup() again", and, from 2026-11-08, "systemd never gives an API mount point a unit") is pinned here to a resolved commit SHA and a line range, so a reader can
# check the code rather than the prose. Versions are the ones installed on the host on 2026-11-07:
# docker-ce 29.7.2 (moby tag docker-v29.7.2), systemd 259.5, snapd 2.77.1.
#
# Read-only: GitHub API GETs through `gh api`. Prints to stdout.
#
# Usage: bash util/ad-hoc/2026-11-07_upstream_source_pins.bash > reports/<dir>/<UTC>_upstream-source-pins.txt
set -euo pipefail

pin() {
    # pin OWNER/REPO REF PATH FIRST LAST WHY
    local repo="$1" ref="$2" path="$3" first="$4" last="$5" why="$6" sha
    sha="$(gh api "repos/${repo}/commits/${ref}" --jq .sha)"
    printf '\n---- %s @ %s (%s) : %s lines %s-%s\n---- why: %s\n' "$repo" "$ref" "$sha" "$path" "$first" "$last" "$why"
    gh api "repos/${repo}/contents/${path}?ref=${sha}" -H 'Accept: application/vnd.github.raw' \
        | awk -v a="$first" -v b="$last" 'NR >= a && NR <= b { printf "%6d  %s\n", NR, $0 }'
}

printf 'Fetched %s by %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$(basename "$0")"

pin moby/moby docker-v29.7.2 daemon/oci_linux.go 124 150 \
    "every non-privileged container start without an explicit profile calls loadDefaultAppArmorProfileIfMissing() when appArmorSupported() is true"
pin moby/moby docker-v29.7.2 daemon/apparmor_default.go 26 40 \
    "the exact error text: 'Could not check if docker-default AppArmor profile was loaded: <open error>'"
pin moby/moby docker-v29.7.2 daemon/apparmor_linux.go 1 16 \
    "appArmorSupported() is containerd's apparmor.HostSupports()"
pin moby/moby docker-v29.7.2 vendor/github.com/containerd/containerd/v2/pkg/apparmor/apparmor_linux.go 17 45 \
    "HostSupports is computed ONCE per process (sync.Once): a dockerd started while securityfs was mounted keeps answering true after it is unmounted"
pin moby/moby docker-v29.7.2 vendor/github.com/moby/profiles/apparmor/apparmor.go 110 120 \
    "IsLoaded opens /sys/kernel/security/apparmor/profiles -- the ENOENT in the reported error"
pin systemd/systemd v259.5 src/shared/mount-setup.c 112 140 \
    "mount_table: securityfs is mounted by PID 1 itself (no unit file)"
pin systemd/systemd v259.5 src/shared/mount-setup.c 205 232 \
    "pstore, efivarfs (EFI boots only) and bpf are also PID 1 table entries with no unit file"
pin systemd/systemd v259.5 src/core/main.c 3184 3195 \
    "mount_setup() runs on every PID 1 start, a re-exec (daemon-reexec) included; skip_setup only changes propagation handling"
pin systemd/systemd v259.5 src/core/main.c 3005 3019 \
    "skip_setup is true exactly when PID 1 is deserializing (a re-exec)"
# Added 2026-11-08, after the remount: the three filesystems were back in PID 1's mount table yet still had
# no unit. These lines are why -- systemd never represents an API mount point as a unit, mounted or not.
pin systemd/systemd v259.5 src/shared/mount-setup.c 245 254 \
    "mount_point_is_api(): every mount_table entry (securityfs, pstore, bpf, cgroup2, /proc, /sys, /dev, /run ...) is an API mount point"
pin systemd/systemd v259.5 src/core/mount.c 1869 1893 \
    "mount_setup_unit() skips API mount points: no unit is ever synthesized from /proc/self/mountinfo for them, so systemctl never lists them"
pin systemd/systemd v259.5 src/core/mount.c 526 549 \
    "mount_verify() refuses a unit FILE for an API mount point: 'Cannot create mount unit for API file system'"
pin canonical/snapd 2.77.1 cmd/libsnap-confine-private/apparmor-support.c 44 76 \
    "snap-confine dies on aa_is_enabled() ENOENT: 'aa_is_enabled() failed unexpectedly' -- every snap app and snap service start fails"
