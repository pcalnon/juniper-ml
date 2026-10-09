#!/usr/bin/env bash
# Procedure A0: restore the cleartext server database from the 2026-09-18 fileset.
# Read-only against the destination; writes only into the restore directory given as $1.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- recovery
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
ENV_FILE="${YAMAGUCHI_ENV_FILE:-${HOME}/.config/duplicati-backup/env}"
DEST="${YAMAGUCHI_DEST_URL:-file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
OUT="${1:?usage: $0 <restore-directory>}"
SNAP_PATH='/home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite'
WORKDIR="${YAMAGUCHI_WORKDIR:-${HOME}/.cache/yamaguchi-recovery}"
JOBDB="${YAMAGUCHI_JOB_DB:-/home/duplicati/.cache/root-data-folder-2026-09-22/BMXWPAOGLP.sqlite}"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
[[ -s "${JOBDB}" ]] || { echo "no job index at ${JOBDB} (run P0 step 1's freeze first)" >&2; exit 2; }

# The restored file is a CLEARTEXT server database carrying the job passphrase (rule 8,
# Appendix C item 3). It must not land inside the backup Source, or the next run archives it --
# the S-7 shape, and the rule P4 step 1 states for the analogous tar.
# `realpath -m` canonicalises whether or not the path exists, resolving every symlink on the part that does.
# `readlink -f` printed NOTHING when two or more trailing levels were missing, so `/home/pcalnon/a0/out`
# passed this refusal and `install -d` then created it inside the Source (2026-10-08, round 6 R6 DEFECT-2).
# YAMAGUCHI_SOURCE_ROOT exists so the suite can point the refusal at a scratch root.
SOURCE_ROOT="$(realpath -m -- "${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}")"
OUT_REAL="$(realpath -m -- "${OUT}")"
[[ -n "${SOURCE_ROOT}" && -n "${OUT_REAL}" ]] || { echo "refusing: cannot resolve ${OUT}" >&2; exit 2; }
case "${OUT_REAL}/" in
    "${SOURCE_ROOT}"/*) echo "refusing: ${OUT} is inside the backup Source (${SOURCE_ROOT})" >&2; exit 2 ;;
esac
install -d -m 0700 "${OUT}"
install -d -m 0700 "${WORKDIR}"
TMPDB="$(mktemp -u "${WORKDIR}/a0-restore-XXXXXX.sqlite")"
cp -p "${JOBDB}" "${TMPDB}"
# A -wal or hot -journal beside the frozen index holds pages the main file lacks; SQLite applies it
# at the first open only if it sits beside the copy under the copy's name (2026-10-08, round 4 R4B N-8).
for sfx in -wal -journal; do
    if [[ -e "${JOBDB}${sfx}" ]]; then cp -p "${JOBDB}${sfx}" "${TMPDB}${sfx}"; fi
done

# PARSED, never SOURCED -- see the premise-check script for why (dot-sourceable=NO).
PASSPHRASE="$(
    python3 - "${ENV_FILE}" <<'PY'
import re, sys
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$", line.rstrip("\n"))
    if m and m.group(1).strip():
        sys.stdout.write(m.group(1).strip().strip('"').strip("'"))
        break
else:
    sys.exit("FATAL: no PASSPHRASE in " + sys.argv[1])
PY
)"
[[ -n "${PASSPHRASE}" ]] || { echo "no PASSPHRASE parsed from ${ENV_FILE}" >&2; exit 2; }
export PASSPHRASE
duplicati-cli restore "${DEST}" "${SNAP_PATH}" \
    --version=0 "--dbpath=${TMPDB}" "--restore-path=${OUT}"
unset PASSPHRASE
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
echo "restored under ${OUT}; verify it with the forensics script before installing it."
echo "SHRED ${OUT} once step 8 has installed the database -- it is cleartext key material."
