#!/usr/bin/env bash
# CONFIRMATION ONLY -- the discriminator is the offline hash probe
# (2026-09-21_duplicati_settings_key_hash_probe.py). Try ONE candidate settings key against a
# COPY of the abandoned root data folder's server DB. Never touches /usr/lib/duplicati/data or
# the live service. Run with sudo.
#   sudo bash 2026-09-21_probe_settings_key_on_copy.bash /path/to/file-holding-the-candidate
#
# Four containments, each of which this script lacked in the design's first revision:
#   1. copy the -wal and -shm siblings, not the main file alone: the folder's last writers died
#      on exceptions, so a WAL-mode database left by process death keeps its frames in -wal and
#      a main-file-only copy is an older or torn state;
#   2. assert the copy is ALREADY encrypted before starting anything -- on a copy whose
#      encrypted-fields flag is False, Program.cs's ReWriteAllFieldsIfEncryptionChanged
#      encrypts it under WHATEVER key is supplied and prints "Server has started", i.e. a
#      vacuous pass that also poisons the copy;
#   3. run a NEGATIVE CONTROL first: a random key MUST be rejected, or the test proves nothing;
#   4. neuter the copy before any server touches it -- DELETE FROM Schedule, and confine the
#      probe with systemd-run so it cannot reach the real destination or the real data folder
#      even if a schedule survives.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-21
# Status:     ad-hoc — migration
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
# Default to the P0 step 1 DATA-FOLDER FREEZE, not the live folder: the step that introduces
# this script says "the copy from step 1", and a default pointing at /usr/lib/duplicati/data
# would silently re-copy from the original instead.
SRCDIR="${SRCDIR:-/home/duplicati/.cache/root-data-folder-2026-09-22}"
WORK="${WORK:-/home/duplicati/.cache/keyprobe}"
PORT="${PORT:-8399}"
KEYFILE="${1:?usage: $0 <file-containing-candidate-key>}"
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
# sqlite3 is NOT installed on this host by default. Without it the two containment queries
# below return EMPTY, and the refusal then misreports a query failure as "the copy is
# cleartext" -- which sections 4.2, 5.4 and 11 have primed the operator to read as "the second
# key-free recovery source has been found". Fail loudly instead.
command -v sqlite3 > /dev/null || {
    echo "sqlite3 is not installed; containments (2) and (4) cannot run. Install it first." >&2
    exit 2
}
[[ -s "${SRCDIR}/Duplicati-server.sqlite" ]] || { echo "source DB missing under ${SRCDIR}" >&2; exit 2; }

rm -rf "${WORK}"; install -d -m 0700 -o duplicati -g duplicati "${WORK}"
# (1) main file PLUS its siblings.
for f in Duplicati-server.sqlite Duplicati-server.sqlite-wal Duplicati-server.sqlite-shm; do
    [[ -e "${SRCDIR}/${f}" ]] && cp -p "${SRCDIR}/${f}" "${WORK}/${f}"
done
chown -R duplicati:duplicati "${WORK}"

# (2) the copy must already be encrypted, or a "pass" means nothing.
flag="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \
    "SELECT Value FROM Option WHERE BackupID=-2 AND Name='encrypted-fields';" || true)"
url="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \
    "SELECT substr(TargetURL,1,7) FROM Backup LIMIT 1;" || true)"
if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: the copy does not read as encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "EMPTY values mean the QUERY failed, not that the copy is cleartext -- check the copy." >&2
    echo "A probe against a genuinely unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi
# (4) a schedule in the past would otherwise let the probe server start the overdue run.
sqlite3 "${WORK}/Duplicati-server.sqlite" "DELETE FROM Schedule;"

# The key is delivered by a 0600 EnvironmentFile, NEVER on argv: `-p Environment=<secret>` is
# world-readable in /proc/*/cmdline and is recorded by systemd -- the same exposure 7.3.6 bans
# for `duplicati-server-util --password`. (A `SETTINGS_ENCRYPTION_KEY=` prefix on `timeout`
# would also be dead: a transient unit does not inherit the caller's environment.)
try_key() {
    local key="$1" label="$2" log="${WORK}/probe-${2}.log" envf="${WORK}/probe-${2}.env" rc=0
    printf 'probing: %s\n' "${label}" >&2
    ( umask 077; printf 'SETTINGS_ENCRYPTION_KEY=%s\n' "${key}" > "${envf}" )
    chown duplicati:duplicati "${envf}"
    set +e
    timeout -k 10 90 \
        systemd-run --wait --quiet --collect --pipe \
            --uid=duplicati \
            -p InaccessiblePaths=/mnt/Backups \
            -p InaccessiblePaths="${SRCDIR}" \
            -p "EnvironmentFile=${envf}" \
            /usr/bin/duplicati-server "--server-datafolder=${WORK}" \
            --webservice-interface=loopback "--webservice-port=${PORT}" \
            --webservice-disable-signin-tokens > "${log}" 2>&1
    rc=$?
    set -e
    shred -u "${envf}" 2> /dev/null || rm -f "${envf}"
    # A verdict needs a POSITIVE signal for BOTH outcomes. A harness failure -- timeout 124, a
    # systemd-run property this host rejects, a missing binary -- is neither, and must never
    # read as "rejected": that is the direction that discards a CORRECT key and routes the
    # recovery to A2 (destructive) or B (new job id, every downstream default wrong).
    if grep -q 'Server has started' "${log}"; then return 0; fi
    if grep -qE 'SettingsEncryptionKeyMismatchException|does not match current key' "${log}"; then return 1; fi
    echo "INDETERMINATE (${label}): rc=${rc}; neither 'Server has started' nor a Mismatch in ${log}" >&2
    echo "The probe did not run. Fix the harness before reading any verdict." >&2
    exit 5
}

# (3) negative control -- meaningful only because try_key now distinguishes "rejected" from
# "did not run".
if try_key "$(head -c 32 /dev/urandom | base64 | tr -d '\n')" control; then
    echo "REFUSING: a RANDOM key was accepted -- this probe is not discriminating." >&2
    exit 4
fi
echo "negative control rejected the random key (good)"

key="$(<"${KEYFILE}")"
[[ -n "${key}" ]] || { echo "candidate file is empty" >&2; exit 2; }
if try_key "${key}" candidate; then
    echo "KEY ACCEPTED (${#key} chars): the copy opened; keep this candidate"
    exit 0
fi
echo "KEY REJECTED (${#key} chars):"
grep -E 'Exception|encrypt|version' "${WORK}/probe-candidate.log" | head -5
exit 1
