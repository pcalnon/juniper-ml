#!/usr/bin/env bash
# Apply the §7.4 permission model to the T1 destination tree. Run with sudo. Idempotent.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-21
# Status:     ad-hoc — migration
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.4
set -euo pipefail
ROOT=/mnt/Backups/Ubuntu/Dropbox/Backups
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
mountpoint -q /mnt/Backups || { echo "/mnt/Backups is not a mountpoint; refusing" >&2; exit 3; }
[[ -d "${ROOT}" ]] || { echo "${ROOT} missing; refusing" >&2; exit 3; }
# D-14 RULED 2026-09-22: the READ-ONLY model. pcalnon and Dropbox read through the group; only
# the service writes. The two mount parents keep 2750, and the Dropbox root keeps 2770 because
# the sync daemon runs as pcalnon and must write its own root -- narrowing that would break sync,
# not harden it. See section 10.1 and note D-14b.
chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2750 /mnt/Backups /mnt/Backups/Ubuntu
chmod 2770 /mnt/Backups/Ubuntu/Dropbox
# The destination tree passes to the service user. This chown is the step that makes a cloud-side
# or accidental local delete FAIL: unlinking a volume needs write on its directory, and after this
# only duplicati has it.
chown -R duplicati:duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2750 {} +
find "${ROOT}" -type f -exec chmod 0640 {} +
setfacl -R -m g:duplicati:rX -m d:g:duplicati:rX "${ROOT}"
if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    # Strip the named ACL entry the recursive setfacl above just applied here. chmod sets the
    # ACL MASK, not the entry, so `g:duplicati:rwX` would survive with an empty mask and any
    # later `chmod g+rx` would silently re-enable the service user's access.
    setfacl -R -b "${ROOT}/_yamaguchi_keys"
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    # The find above set every regular file to 0640; the escrow env must not be group-readable
    # by the service user at all (design section 6, S-4).
    [[ -e "${ROOT}/_yamaguchi_keys/env" ]] && chmod 0600 "${ROOT}/_yamaguchi_keys/env"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- copy it out (design §6 S-4)" >&2
fi
echo "done; verify with: getfacl ${ROOT}/Yamaguchi | head; sudo -u duplicati test -w ${ROOT}/Yamaguchi && echo service-can-write"
