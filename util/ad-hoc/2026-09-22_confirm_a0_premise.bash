#!/usr/bin/env bash
# Confirm that the 2026-09-18 fileset carries the server-DB snapshot Procedure A0 restores.
# Read-only: lists one path inside one fileset. Never writes to the destination.
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
# Temp index on ext4, NEVER tmpfs (rule 3): /tmp is tmpfs on this host.
WORKDIR="${YAMAGUCHI_WORKDIR:-${HOME}/.cache/yamaguchi-recovery}"
# --dbpath at a disposable COPY of the archived job index, NOT --no-local-db:
# util/ad-hoc/duplicati_drill_run.py records --no-local-db rebuilding the index from every
# dindex volume, ">30 minutes for a single small file here, without completing".
JOBDB="${YAMAGUCHI_JOB_DB:-/home/duplicati/.cache/root-data-folder-2026-09-22/BMXWPAOGLP.sqlite}"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
[[ -s "${JOBDB}" ]] || { echo "no job index at ${JOBDB} (run P0 step 1's freeze first)" >&2; exit 2; }
install -d -m 0700 "${WORKDIR}"
TMPDB="$(mktemp -u "${WORKDIR}/a0-probe-XXXXXX.sqlite")"
cp -p "${JOBDB}" "${TMPDB}"

# The credential file is PARSED, never SOURCED. The live PASSPHRASE is UNQUOTED and carries
# '$', '&', '@', '#' and '^' (util/ad-hoc/2026-09-22_credential_file_shape.py reports
# dot-sourceable=NO), so `set -a; . "${ENV_FILE}"` under `set -u` dies
# "<fragment>: unbound variable" -- printing a piece of the passphrase to stderr, the exact
# channel section 6 exists to close -- before duplicati-cli is ever reached; and the '&' makes
# the shell run the tail of the value as a command. util/ad-hoc/yamaguchi_build_job.py:57-63
# already parses this file the right way.
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
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv.
duplicati-cli list "${DEST}" --version=0 "--dbpath=${TMPDB}" '*duplicati-server-db*'
unset PASSPHRASE
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
