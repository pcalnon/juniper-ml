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
chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2770 /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chgrp -R duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2770 {} +
find "${ROOT}" -type f -exec chmod 0660 {} +
setfacl -R -m g:duplicati:rwX -m d:g:duplicati:rwX "${ROOT}"
if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    # Strip the named ACL entry the recursive setfacl above just applied here. chmod sets the
    # ACL MASK, not the entry, so `g:duplicati:rwX` would survive with an empty mask and any
    # later `chmod g+rx` would silently re-enable the service user's access.
    setfacl -R -b "${ROOT}/_yamaguchi_keys"
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    # The find above set every regular file to 0660; the escrow env must not be group-readable
    # by the service user (design section 6, S-4).
    [[ -e "${ROOT}/_yamaguchi_keys/env" ]] && chmod 0600 "${ROOT}/_yamaguchi_keys/env"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- copy it out (design §6 S-4)" >&2
fi
echo "done; verify with: getfacl ${ROOT}/Yamaguchi | head; sudo -u duplicati test -w ${ROOT}/Yamaguchi && echo service-can-write"
