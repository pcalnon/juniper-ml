#!/usr/bin/env bash
# Show that systemd gives none of its own API mount points a unit, mounted or not (the RCA §14 correction).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-08
# Status:     ad-hoc — investigation (claim check)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md (§3 L4, §4 RC-2, §14)
#             reports/2026-11-07_yamaguchi-securityfs-unmount/2026-11-08T0905Z_upstream-source-pins.txt
#             (systemd v259.5 src/core/mount.c mount_setup_unit() and mount_verify(), mount-setup.c mount_point_is_api())
#
# Until 2026-11-08 the RCA said securityfs, pstore and bpf "leave no unit behind once unmounted", i.e. their
# units are garbage-collected. After the remount all three were back in PID 1's mount table and STILL had no
# unit. systemd's source says why: it never creates a unit for an API mount point. This script tests that
# claim on the live host, for every mount point in systemd's mount_table, and uses the six unit-file API
# mounts as a positive control (each of them must be a loaded unit).
#
# For each mount point it prints the topmost mount id in /proc/1/mountinfo ("-" when not mounted), the unit
# name systemd would use, and systemctl's LoadState for that name. Read-only; needs no root.
#
# Usage: bash util/ad-hoc/2026-11-08_api_mount_units_check.bash
# Exit: 0 no mounted API point has a unit and all six unit-file mounts are loaded units; 1 otherwise.
set -uo pipefail

# systemd v259.5 src/shared/mount-setup.c, mount_table (lines 113-232): its distinct mount points, in order.
# /sys/fs/smackfs applies only under SMACK, and efivarfs only on an EFI boot.
API_POINTS=(/proc /sys /dev /sys/kernel/security /sys/fs/smackfs /dev/shm /dev/pts /run /sys/fs/cgroup
            /sys/fs/pstore /sys/firmware/efi/efivars /sys/fs/bpf)
# The API mounts systemd ships a .mount unit FILE for. Each must show up as a loaded unit.
UNIT_POINTS=(/sys/kernel/debug /sys/kernel/tracing /sys/kernel/config /sys/fs/fuse/connections /dev/hugepages /dev/mqueue)

mounted_api=0
api_with_unit=0
unit_loaded=0

row() {  # row KIND WHERE -> prints one line; sets LAST_MOUNT_ID and LAST_LOAD
    local kind="$1" where="$2" unit
    unit="$(systemd-escape --path --suffix=mount "$where")"
    LAST_MOUNT_ID="$(awk -v w="$where" '$5 == w { id = $1 } END { print (id == "" ? "-" : id) }' /proc/1/mountinfo)"
    LAST_LOAD="$(systemctl show -p LoadState --value "$unit" 2>&1)"
    printf '%-9s %-27s %-9s %-34s %s\n' "$kind" "$where" "$LAST_MOUNT_ID" "$unit" "$LAST_LOAD"
}

echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ) on $(hostname); $(systemctl --version | head -n 1)"
echo "# mount id: topmost mount at the point in /proc/1/mountinfo; LoadState: systemctl show -p LoadState --value <unit>"
printf '%-9s %-27s %-9s %-34s %s\n' KIND WHERE MOUNT_ID UNIT LOADSTATE
for where in "${API_POINTS[@]}"; do
    row api "$where"
    if [[ "$LAST_MOUNT_ID" != - ]]; then
        mounted_api=$((mounted_api + 1))
        [[ "$LAST_LOAD" == not-found ]] || api_with_unit=$((api_with_unit + 1))
    fi
done
for where in "${UNIT_POINTS[@]}"; do
    row unit-file "$where"
    [[ "$LAST_LOAD" == loaded ]] && unit_loaded=$((unit_loaded + 1))
done

echo "== mounted API points: ${mounted_api}; of them with a unit: ${api_with_unit} (claim: 0)"
echo "== unit-file API mounts that are loaded units: ${unit_loaded} of ${#UNIT_POINTS[@]} (claim: all)"
if [[ $api_with_unit -eq 0 && $unit_loaded -eq ${#UNIT_POINTS[@]} ]]; then
    echo "== PASS: systemd represents none of its mounted API points as a unit, and every unit-file mount as one"
    exit 0
fi
echo "== FAIL: the claim does not hold on this host"
exit 1
