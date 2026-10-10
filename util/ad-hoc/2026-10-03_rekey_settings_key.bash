#!/usr/bin/env bash
# P0.5b / P1 step 1 for PROCEDURE A ONLY: re-key the Duplicati server database from the
# accepted 2026-09-18 settings key to the new random key, in two server starts, without ever
# leaving `--disable-db-encryption` behind and without the overdue job firing in the window.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-10-03
# Version:    1.3.0 (2026-10-08: Phase B round-4 fold-in -- see HISTORY)
# Status:     ad-hoc -- recovery (the assessment's B4; issues I-15, I-28, I-38, I-39)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md
#             ("the assessment"; its section 6.4 is the P0 checklist whose step numbers this file cites);
#             notes/JUNIPER_2026-09-21_...INTEGRATED-DESIGN.md ("D") section 8 P0.5b, P1 step 1;
#             util/ad-hoc/2026-10-03_rekey_gate.py (the pre-flight count, step 1, and the exit gate, step 8);
#             tests/test_backup_rekey_real_path.py (the non-dry-run path and every EXIT-trap state, stubbed).
#
# WHEN. Only after Procedure A (assessment step 7 found the 2026-09-18 key and step 9 placed the
# recovered folder, which is encrypted under that key, with the accepted key at /etc/credstore/
# duplicati-settings-key and the new random key at /etc/credstore/duplicati-settings-key.new), and
# INSIDE assessment step 11 (D's P0 step 10): after the unit's first start, the UI password and the
# web credential exist, and after that step's tempdir/schedule edits -- IN PLACE OF the operator's
# `resume`. This script's own final `resume` is what fires the overdue daily job, so run it before
# any backup has started; it refuses while a task is active. On the A0, A2 and B paths the placed
# database is encrypted under the NEW key by the unit's first start and this script is NOT needed
# (assessment step 10).
#
# WHAT IT DOES, in order -- every step is printed, and `--dry-run` prints them all and does nothing:
#   1. pre-flight: both credential files present (0600 root) and DIFFERENT, and no `…-key.old` other
#      than a copy of the accepted key; the INSTALLED unit at /etc/systemd/system/duplicati.service is
#      the one systemd loads; the unit active; no task active (API `serverstate`: ActiveTask null); the
#      API client in this checkout understands serverstate/pause/resume (the assessment's B2, ml#2115);
#      the snapshot timer neither enabled (any `enabled*`, `linked*`, `static`, … state) nor ACTIVE
#      (a timer disabled without `--now` still fires: a 13:45 UTC fire in the cleartext window would
#      copy a cleartext database into the backup Source -- STOP item 4); no stale drop-in; and, on a
#      COPY of the database (shredded at once), NO `enc-v1:` blob in a table the product's
#      re-encryption never rewrites -- ConnectionString, and the Option, Source and BackupTargetUrl
#      rows of no backup (an Option row at -1 or -2 is the settings, which ARE rewritten)
#      (`2026-10-03_rekey_gate.py --unrewritten`). Such a blob would stay under the OLD key, fail the
#      exit gate AFTER the swap, and no re-run could pass it; so the script refuses here, before
#      anything changes, and refuses too when the count itself fails (any exit but 0) (round 3,
#      R3A D-5 / R3C D-2; round 4, R4C DEFECT-2; the remedy is in the refusal);
#   2. API `pause`: 2.4.0.0 persists an indefinite pause as `paused-until` and restores it at every
#      start, so ONE pause spans both starts. Restoring it at a start does start the scheduler, which
#      may QUEUE the overdue job (Scheduler.cs 121-124, 396; an overdue schedule is queued at every
#      start), but the queue runner is paused first (Program.cs 1305), so nothing RUNS while the fields
#      are cleartext (Lane B B-9; round 3, R3A N-2);
#   3. `systemctl stop duplicati.service`;
#   4. a RUNTIME drop-in (/run/systemd/system/duplicati.service.d/, gone at reboot) that re-declares
#      ExecStart with `--disable-db-encryption` appended. NEVER in /etc/default/duplicati: that flag
#      SATISFIES --require-db-encryption-key (Server/Program.cs: `require && !(hasValidKey ||
#      disable)`), suppresses the "unencrypted database" notice, and would decrypt the database
#      silently on every later start; AC-14 cannot see it (I-28). It also trips D-6's drift gate;
#   5. the DECRYPT start, with the OLD key still at the credential path (STOP item 2: the first
#      draft overwrote the key first and re-locked the database); wait for "Server has started";
#   6. `systemctl stop`; swap the keys: COPY the old key to `…-key.old` (0600), then ONE atomic
#      `mv` of `…-key.new` onto the credential path -- there is no instant at which the path is
#      absent, and the old key stays beside it until the exit gate passes, then is shredded;
#   7. REMOVE THE DROP-IN with `rm` and `daemon-reload` -- NEVER `systemctl revert`. This host has a
#      vendor unit under /usr/lib/systemd/system/ (dpkg-owned), so the installed D-6 unit is an
#      OVERRIDE of it, and `revert` "removes … any user-configured unit file that overrides a
#      matching vendor supplied unit file" (systemctl(1)): the hardened unit would be deleted and the
#      encrypt start would run the vendor unit -- no LoadCredential=, no confinement, Restart=always
#      -- on a cleartext database with the keys already swapped (Phase B validation, all three
#      lanes). After the removal the script asserts systemd still loads the installed unit;
#      then the ENCRYPT start; wait for "Server has started";
#   8. `systemctl stop`; EXIT GATE on a COPY of the database (2026-10-03_rekey_gate.py):
#      `encrypted-fields` is True and every `enc-v1:` blob in all five encrypted columns carries
#      sha256(new key); only counts are printed; and no drop-in is present;
#   9. `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` on the live database with the server STOPPED, so no
#      cleartext page survives in free pages or the WAL (D section 7.3.5);
#  10. start the unit; API `resume`; `serverstate` must read Running.
#
# IF IT DIES. An EXIT trap reports what is ON DISK, not what the script believed (round 3: R3A D-4,
# R3B N-11, R3C D-1). A refusal before step 2 says so and nothing else -- nothing was changed. After
# that the trap:
#   * if a drop-in is present, STOPS the unit first (a process started with --disable-db-encryption
#     keeps that argv however long it runs), then removes the drop-in and reloads;
#   * shreds any database copy;
#   * names the keys by HASH: it hashed both key files in the pre-flight, and now reports which of
#     `…-key`, `…-key.old` and `…-key.new` holds the OLD key, the NEW key, another, or nothing --
#     "swapped", "not swapped", or an unexpected layout;
#   * names the database's state from how far the run got: under the OLD key before the decrypt
#     start; UNKNOWN once a decrypt or an encrypt start was attempted and its "Server has started"
#     was not seen (the rewrite runs BEFORE that line); CLEARTEXT after the decrypt start; with the
#     gate's own counts when the gate failed;
#   * prints the ONE recovery branch that applies -- never "start the unit" after a FragmentPath
#     refusal (DO_NOT_START: re-run the installer first) -- and the scheduler's PAUSED state.
# It never moves a key back by itself: after the swap the next start under the NEW key encrypts a
# cleartext database correctly, and a database already under the new key must not meet the old one.
#
# The snapshot timer stays as it was (disabled); assessment step 13 re-enables it after this gate.
#
# TEST HOOK. REKEY_INSTALLED_UNIT replaces the installed unit's path, for the hermetic suites only
# (round 3, R3C D-4: once the installer has run on a host, the dry-run test read the real
# /etc/systemd/system/duplicati.service and failed). On a real run it can only make the pre-flight
# refuse: systemd's FragmentPath is compared with it. REKEY_CREDSTORE_DIR replaces /etc/credstore, and
# is honoured under --dry-run ONLY (a real run with it set exits 2), so a dry-run test stats nothing
# under /etc (round 4, R4C NIT-8).
#
# HISTORY
#   1.0.0  2026-10-03  first version (the assessment's B4).
#   1.1.0  2026-10-03  Phase B validation fold-in: `systemctl revert` replaced by rm + daemon-reload
#                      (BLOCKER, lanes A/B/C); EXIT trap; copy-then-atomic-mv key swap; "no task
#                      active" pre-flight through B2's serverstate; the gate moved to
#                      2026-10-03_rekey_gate.py and widened to all five encrypted columns; the API
#                      verb check runs under --dry-run too; the dry run says when it substitutes the
#                      repository unit's ExecStart; placement moved before the operator's `resume`.
#   1.2.0  2026-10-08  round-3 fold-in: the EXIT trap derives the key state from the files by hash,
#                      stops the unit when a drop-in is present, reports UNKNOWN after an attempted
#                      start, prints the gate's counts and only the branch that applies, and never says
#                      "start" after a FragmentPath refusal; the pre-flight counts never-rewritten
#                      `enc-v1:` blobs on a copy and refuses, requires the snapshot timer inactive as
#                      well as not enabled, refuses identical key files or a foreign `…-key.old`; the
#                      dry run no longer says the decrypt start happened; REKEY_INSTALLED_UNIT.
#   1.3.0  2026-10-08  round-4 fold-in: the pre-flight count also refuses orphaned Option/Source blobs
#                      (through the gate, R4C DEFECT-2); REKEY_CREDSTORE_DIR (dry run only, R4C NIT-8).
set -euo pipefail

UNIT=duplicati.service
TIMER=yamaguchi-server-db-snapshot.timer
INSTALLED_UNIT="${REKEY_INSTALLED_UNIT:-/etc/systemd/system/${UNIT}}"
CRED_DIR=/etc/credstore
DATA_FOLDER="${DUPLICATI_DATA_FOLDER:-/home/duplicati/.config/Duplicati}"
DB="${DATA_FOLDER}/Duplicati-server.sqlite"
DROPIN_DIR=/run/systemd/system/${UNIT}.d
DROPIN=${DROPIN_DIR}/zz-rekey-disable-db-encryption.conf
API_USER="${SUDO_USER:-pcalnon}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API="${REPO_DIR}/util/ad-hoc/yamaguchi_server_api.py"
GATE="${REPO_DIR}/util/ad-hoc/2026-10-03_rekey_gate.py"
REPO_UNIT="${REPO_DIR}/util/systemd/${UNIT}"
WORKDIR="${REKEY_WORKDIR:-/root/.cache/duplicati-rekey}"
DRY_RUN=0
for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=1 ;;
        *) echo "usage: sudo bash $0 [--dry-run]" >&2; exit 2 ;;
    esac
done
if [[ -n "${REKEY_CREDSTORE_DIR:-}" ]]; then
    # Test hook, --dry-run ONLY: the unit's LoadCredential= reads /etc/credstore whatever this says, so a
    # real run with another key folder would swap keys the server never sees.
    if (( DRY_RUN == 0 )); then echo "FATAL: REKEY_CREDSTORE_DIR is honoured under --dry-run only" >&2; exit 2; fi
    CRED_DIR="${REKEY_CREDSTORE_DIR}"
fi
CRED=${CRED_DIR}/duplicati-settings-key
CRED_NEW=${CRED}.new

log() { printf '%s: %s\n' "${0##*/}" "$*" >&2; }
die() { log "FATAL: $*"; exit 1; }
run() {
    # run <command...>: print, then execute unless --dry-run.
    if (( DRY_RUN )); then log "would: $*"; else log "run: $*"; "$@"; fi
}
api() {
    # The API client runs as the invoking user: its credential file is that user's 0600 file.
    run sudo -u "${API_USER}" -- python3 "${API}" "$@"
}
wait_started() {
    # Wait for the server's own start line in the journal since a timestamp; never read values.
    local since="$1" n=0
    if (( DRY_RUN )); then log "would: wait for 'Server has started' in journalctl -u ${UNIT} --since '${since}'"; return 0; fi
    while (( n < 60 )); do
        if [[ "$(journalctl -u "${UNIT}" --since "${since}" --no-pager -q 2>/dev/null | grep -c 'Server has started')" -ge 1 ]]; then
            if [[ "$(journalctl -u "${UNIT}" --since "${since}" --no-pager -q 2>/dev/null | grep -c -e 'Unknown option supplied' -e 'SettingsEncryptionKey')" -ne 0 ]]; then
                die "the start logged an unknown option or a settings-key exception; read the journal before continuing"
            fi
            return 0
        fi
        sleep 2; n=$((n + 1))
    done
    die "no 'Server has started' within 120 s of the start at ${since}"
}
copy_db() {
    # copy_db <dest>: the database with its -wal/-shm siblings (a copy of the main file alone can
    # miss every page still in the WAL).
    cp -p "${DB}" "$1"
    if [[ -e "${DB}-wal" ]]; then cp -p "${DB}-wal" "$1-wal"; fi
    if [[ -e "${DB}-shm" ]]; then cp -p "${DB}-shm" "$1-shm"; fi
}
shred_copy() {
    if [[ -n "${COPY}" ]]; then
        shred -u "${COPY}" "${COPY}-wal" "${COPY}-shm" 2>/dev/null || rm -f "${COPY}" "${COPY}-wal" "${COPY}-shm"
        COPY=""
    fi
}

# --- state for the EXIT trap: what the run ATTEMPTED; the key files are read again at trap time ------
OLD_H=""                # sha256 of the key at ${CRED} at pre-flight (the accepted, OLD key)
NEW_H=""                # sha256 of the key at ${CRED_NEW} at pre-flight (the NEW key)
STARTED=0               # set when the pause is attempted: from here on the run may have changed something
PAUSED=0                # 1 from the pause attempt until a resume returns
DECRYPT_ATTEMPTED=0
DECRYPT_DONE=0
ENCRYPT_ATTEMPTED=0
ENCRYPT_DONE=0
GATE_PASSED=0
GATE_FAILED=0
GATE_REPORT=""
VACUUM_DONE=0
DO_NOT_START=0          # set by a FragmentPath refusal: systemd would start a unit other than the installed one
FRAGMENT_SEEN=""
COPY=""
DONE=0
key_tag() {
    # key_tag <file>: OLD / NEW (by hash against the pre-flight's), other, absent or unreadable. Never prints a key.
    local h
    if [[ ! -e "$1" ]]; then echo absent; return 0; fi
    h="$(sha256sum < "$1" 2>/dev/null)" || { echo unreadable; return 0; }
    h="${h%% *}"
    if [[ -n "${OLD_H}" && "${h}" == "${OLD_H}" ]]; then echo OLD
    elif [[ -n "${NEW_H}" && "${h}" == "${NEW_H}" ]]; then echo NEW
    else echo other; fi
}
remove_dropin() {
    # rm + daemon-reload, never `systemctl revert` (see step 7 above).
    if (( DRY_RUN )); then
        log "would: rm -f ${DROPIN}; rmdir ${DROPIN_DIR}; systemctl daemon-reload; assert FragmentPath is still ${INSTALLED_UNIT}"
        return 0
    fi
    rm -f "${DROPIN}"
    rmdir "${DROPIN_DIR}" 2>/dev/null || true
    systemctl daemon-reload
    [[ ! -e "${DROPIN}" ]] || die "drop-in still present after removal: ${DROPIN}"
    FRAGMENT_SEEN="$(systemctl show -p FragmentPath --value "${UNIT}")"
    if [[ "${FRAGMENT_SEEN}" != "${INSTALLED_UNIT}" ]]; then
        DO_NOT_START=1
        die "systemd now loads ${FRAGMENT_SEEN:-<nothing>}, not ${INSTALLED_UNIT}: do NOT start the unit; re-run the installer first"
    fi
}
cleanup() {
    local status=$? c o n keys unit db
    trap - EXIT
    set +e
    if (( DONE )); then return 0; fi
    if (( DRY_RUN )); then
        log "dry run ended with status ${status}; nothing was done"
        return 0
    fi
    shred_copy
    if (( ! STARTED )); then
        log "REFUSED with status ${status} before any change: the scheduler was not paused, the unit not stopped, no key moved"
        if [[ -e "${CRED}.old" && ! -e "${CRED_NEW}" ]]; then
            log "WARNING: ${CRED}.old exists and ${CRED_NEW} does not -- the layout a PREVIOUS run leaves AFTER its key swap."
            log "         The database is then cleartext or under the key now at ${CRED}. Do NOT move ${CRED}.old back."
            log "         Follow that run's printed recovery, or gate a copy (with its -wal/-shm): sudo python3 ${GATE} <copy> ${CRED}"
        fi
        return 0
    fi
    log "ABORTED with status ${status} -- cleaning up and reporting the state"
    if [[ -e "${DROPIN}" ]]; then
        log "a drop-in is present: stopping ${UNIT} first, so no process keeps --disable-db-encryption in its argv"
        systemctl stop "${UNIT}" || log "WARNING: systemctl stop ${UNIT} FAILED"
        rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null
        systemctl daemon-reload || log "WARNING: systemctl daemon-reload FAILED"
        log "the drop-in is removed"
    fi
    unit="$(systemctl is-active "${UNIT}" 2>/dev/null)"
    c="$(key_tag "${CRED}")"; o="$(key_tag "${CRED}.old")"; n="$(key_tag "${CRED_NEW}")"
    if [[ "${c}" == OLD && "${n}" == NEW && ( "${o}" == absent || "${o}" == OLD ) ]]; then keys=UNSWAPPED
    elif [[ "${c}" == NEW && "${o}" == OLD && "${n}" == absent ]]; then keys=SWAPPED
    else keys=INCONSISTENT; fi
    if (( GATE_PASSED )); then db="under the NEW key (verified by the gate on a copy)"
    elif (( GATE_FAILED )); then db="NOT verified: the exit gate FAILED on a copy"
    elif (( ENCRYPT_DONE )); then db="under the NEW key per the start log; NOT yet verified by the gate"
    elif (( ENCRYPT_ATTEMPTED )); then db="UNKNOWN -- an encrypt start was attempted: CLEARTEXT, or (partly) under the NEW key"
    elif (( DECRYPT_DONE )); then db="CLEARTEXT (the decrypt start completed)"
    elif (( DECRYPT_ATTEMPTED )); then db="UNKNOWN -- a decrypt start was attempted: under the OLD key, or (partly) CLEARTEXT"
    else db="under the OLD key (no start with the drop-in was made)"; fi
    log "STATE: database ${db}"
    if [[ -n "${GATE_REPORT}" ]]; then log "STATE: gate counts: ${GATE_REPORT}"; fi
    log "STATE: keys ${keys}: ${CRED} holds ${c}; ${CRED}.old holds ${o}; ${CRED_NEW} holds ${n}"
    log "STATE: unit ${unit:-unknown}; drop-in $([[ -e "${DROPIN}" ]] && echo PRESENT || echo absent)"
    if (( PAUSED )); then
        log "STATE: the scheduler is PAUSED, or may be (the pause persists across restarts). Resume ONLY as the last recovery step:"
        log "       sudo -u ${API_USER} python3 ${API} resume"
    fi
    if [[ "${unit}" == active && ( ${DECRYPT_ATTEMPTED} -eq 1 && ${ENCRYPT_ATTEMPTED} -eq 0 ) ]]; then
        log "RECOVERY, FIRST: ${UNIT} is still active and may carry --disable-db-encryption in its argv: systemctl stop ${UNIT}"
    fi
    if (( GATE_PASSED )); then
        (( VACUUM_DONE )) || log "RECOVERY: with the server STOPPED, run step 9's checkpoint + VACUUM on ${DB} (no cleartext page may survive)."
        log "RECOVERY: the database is under the NEW key. Start ${UNIT} if it is not active, resume, confirm serverstate reads Running;"
        log "          only then shred ${CRED}.old."
    elif (( GATE_FAILED )); then
        log "RECOVERY: do NOT shred ${CRED}.old and do NOT resume. The counts above say which case this is:"
        log "          encrypted-fields not True -- the encrypt start did not finish re-encrypting: read the journal;"
        log "          under-another-key > 0 -- gate the same kind of copy against ${CRED}.old to see whether they are under the OLD key."
        log "          The pre-flight refused blobs the product never rewrites (ConnectionString, orphaned rows); one there now was written during this run."
    elif [[ "${keys}" == UNSWAPPED ]]; then
        if (( DECRYPT_ATTEMPTED == 0 )) && [[ "${unit}" == active ]]; then
            log "RECOVERY: nothing but the pause changed. Re-run this script, or resume to back out."
        else
            log "RECOVERY: the keys were NOT swapped: the OLD key is at ${CRED}. Start ${UNIT} (no drop-in is left): a start with the key"
            log "          that encrypted the database re-encrypts a cleartext one under it. Then re-run this script from the top:"
            log "          its decrypt start rewrites every field, whatever the interrupted start left."
        fi
    elif [[ "${keys}" == SWAPPED ]] && (( DECRYPT_DONE )); then
        if (( DO_NOT_START )); then
            log "RECOVERY: do NOT start ${UNIT}: systemd loads ${FRAGMENT_SEEN:-another unit}, not ${INSTALLED_UNIT}. Re-run the installer"
            log "          (assessment step 9) and daemon-reload, confirm 'systemctl show -p FragmentPath --value ${UNIT}' prints"
            log "          ${INSTALLED_UNIT}, and only then continue with the next line."
        fi
        log "RECOVERY: the keys WERE swapped. Leave the NEW key at ${CRED} and ${CRED}.old where it is. Start ${UNIT}: the first start"
        log "          with --require-db-encryption-key encrypts a cleartext database under the NEW key. Then stop it and gate a copy"
        log "          (with its -wal/-shm): sudo python3 ${GATE} <copy> ${CRED}. On PASS: step 9's checkpoint + VACUUM with the server"
        log "          stopped, start, resume, and only then shred ${CRED}.old."
    else
        log "RECOVERY: the key files are in an UNEXPECTED layout (above). Do NOT start ${UNIT} and do NOT move a key:"
        log "          compare the files with the escrowed copies first."
    fi
}
trap cleanup EXIT

# --- 1. pre-flight ----------------------------------------------------------------------------
if (( DRY_RUN == 0 )); then
    [[ "$(id -u)" -eq 0 ]] || die "run with sudo (or --dry-run)"
fi
for f in "${CRED}" "${CRED_NEW}"; do
    if (( DRY_RUN )) && [[ ! -e "${f}" ]]; then log "dry run: ${f} not visible (absent, or ${CRED_DIR} is 0700 and this is not root)"; continue; fi
    [[ -s "${f}" ]] || die "credential file missing or empty: ${f} (Procedure A places the accepted key at ${CRED} and the new key at ${CRED_NEW})"
    [[ "$(stat -c '%U:%a' "${f}")" == "root:600" ]] || die "${f} must be root-owned mode 0600"
done
[[ -f "${GATE}" ]] || die "exit gate missing: ${GATE}"
python3 "${API}" --help 2>&1 | grep -q 'serverstate' || die "${API} has no serverstate/pause/resume verbs (the assessment's B2, ml#2115, must be merged into this checkout first)"
if (( DRY_RUN == 0 )); then
    OLD_H="$(sha256sum < "${CRED}")"; OLD_H="${OLD_H%% *}"
    NEW_H="$(sha256sum < "${CRED_NEW}")"; NEW_H="${NEW_H%% *}"
    [[ "${OLD_H}" != "${NEW_H}" ]] || die "${CRED} and ${CRED_NEW} hold the SAME key: nothing to re-key to"
    if [[ -e "${CRED}.old" && "$(key_tag "${CRED}.old")" != OLD ]]; then
        die "${CRED}.old exists and is not the key at ${CRED}: a previous run's? Inspect it (compare with the escrowed keys) before retrying"
    fi
    [[ -r "${INSTALLED_UNIT}" ]] || die "no installed unit at ${INSTALLED_UNIT}: the installer has not run (assessment step 9)"
    [[ "$(systemctl show -p FragmentPath --value "${UNIT}")" == "${INSTALLED_UNIT}" ]] || die "systemd loads $(systemctl show -p FragmentPath --value "${UNIT}"), not ${INSTALLED_UNIT}: run the installer and daemon-reload first"
    [[ "$(systemctl is-active "${UNIT}")" == "active" ]] || die "${UNIT} is not active; this script expects the recovered server running (assessment step 10) so it can pause the scheduler first"
    # The snapshot timer: not enabled in ANY form (enabled-runtime and linked pass an `!= enabled` test;
    # round 3, R3B N-8 / R3C N-4) and not ACTIVE (a timer disabled without --now still fires).
    timer_enabled="$(systemctl is-enabled "${TIMER}" 2>/dev/null || true)"
    case "${timer_enabled}" in
        disabled|masked|masked-runtime|not-found|"") ;;
        *) die "${TIMER} is-enabled reports '${timer_enabled}'; disable it first (assessment step 1) -- a fire in the cleartext window copies a cleartext database into the backup Source" ;;
    esac
    timer_active="$(systemctl is-active "${TIMER}" 2>/dev/null || true)"
    [[ "${timer_active}" == "inactive" ]] || die "${TIMER} is-active reports '${timer_active}'; stop it first (systemctl stop ${TIMER}) -- a disabled timer that is still active fires in the cleartext window"
    [[ ! -e "${DROPIN}" ]] || die "a previous run's drop-in is still present: ${DROPIN} -- remove it (rm, then systemctl daemon-reload; NEVER systemctl revert) and inspect before retrying"
    [[ -s "${DB}" ]] || die "no server database at ${DB}"
    # No task may be active: `pause` would freeze a running backup and `systemctl stop` would kill it.
    state_json="$(sudo -u "${API_USER}" -- python3 "${API}" serverstate 2>/dev/null || true)"
    [[ -n "${state_json}" ]] || die "cannot read the server state through ${API}; is the web credential in place (assessment step 11)?"
    printf '%s' "${state_json}" | python3 -c 'import json, sys; s = json.load(sys.stdin); sys.exit(3 if s.get("ActiveTask") else 0)' \
        || die "a task is ACTIVE on the server; let it finish (or abort it) before re-keying -- this script must not stop a running backup"
else
    log "would: refuse unless ${INSTALLED_UNIT} is what systemd loads, the unit is active, the snapshot timer is neither enabled nor active, no drop-in exists, and serverstate reports no ActiveTask"
fi
run install -d -m 0700 "${WORKDIR}"
# Blobs the product's re-encryption never rewrites, counted on a COPY before anything is stopped.
if (( DRY_RUN )); then
    log "would: copy ${DB} (+ -wal/-shm) to ${WORKDIR} and run ${GATE##*/} --unrewritten on the copy: refuse if any enc-v1 blob sits where the product's re-encryption never rewrites it (ConnectionString; Option, Source and BackupTargetUrl rows of no backup), or if the count fails"
else
    COPY="${WORKDIR}/preflight-$(date +%s).sqlite"
    copy_db "${COPY}"
    count_rc=0
    UNREWRITTEN="$(python3 "${GATE}" --unrewritten "${COPY}")" || count_rc=$?
    shred_copy
    case "${count_rc}" in
        0) log "pre-flight: ${UNREWRITTEN}" ;;
        1) die "pre-flight: ${UNREWRITTEN}. The product's re-encryption never rewrites these (Connection.cs 131-153), so they would stay
       under the OLD key, fail the exit gate AFTER the key swap, and no re-run could pass it. Nothing has changed. Remedy, by
       the owner: record each saved connection string's destination, delete them through the web UI, re-run this script, then
       re-create them (they are then written under the NEW key). An ORPHANED row (Option at a BackupID other than -1, -2 or a
       backup's; Source or BackupTargetUrl of no backup) belongs to no job and the UI cannot reach it: with the server
       stopped and a copy kept, delete it with sqlite3 (WHERE BackupID NOT IN (SELECT ID FROM Backup), and for Option also
       NOT IN (-1, -2)), start the unit, then re-run." ;;
        *) die "pre-flight: cannot count the never-rewritten blobs on a copy of ${DB} (gate exit ${count_rc}); refusing rather than guessing" ;;
    esac
fi

# --- 2. pause the scheduler (persists across both starts) ------------------------------------
api serverstate || true
STARTED=1; PAUSED=1   # before the call: a pause that errors may still have paused
api pause
api serverstate || true   # expected: Paused (exit 2) -- informational

# --- 3-5. decrypt start under a runtime drop-in, OLD key in place ----------------------------
run systemctl stop "${UNIT}"
# The ExecStart to re-declare comes from the INSTALLED unit text (the D-6 copy), not from
# `systemctl show`, whose argv rendering escapes quotes; the wrapper takes argv words after
# DAEMON_OPTS as options (precedence 4), so the appended flag reaches the server.
EXECSTART=""
if [[ -r "${INSTALLED_UNIT}" ]]; then
    EXECSTART="$(grep -m1 '^ExecStart=' "${INSTALLED_UNIT}" | cut -d= -f2-)"
fi
if [[ -z "${EXECSTART}" ]]; then
    (( DRY_RUN )) || die "no ExecStart= in ${INSTALLED_UNIT}: the installer has not run (assessment step 9)"
    EXECSTART="$(grep -m1 '^ExecStart=' "${REPO_UNIT}" | cut -d= -f2-)"
    log "DRY RUN: ${INSTALLED_UNIT} is absent or unreadable here; using the REPOSITORY unit's ExecStart (${REPO_UNIT})"
fi
if (( DRY_RUN )); then
    log "would: write ${DROPIN} with [Service] ExecStart= / ExecStart=${EXECSTART} --disable-db-encryption"
else
    install -d -m 0755 "${DROPIN_DIR}"
    printf '[Service]\nExecStart=\nExecStart=%s --disable-db-encryption\n' "${EXECSTART}" > "${DROPIN}"
    chmod 0644 "${DROPIN}"
fi
run systemctl daemon-reload
T1="$(date '+%Y-%m-%d %H:%M:%S')"
DECRYPT_ATTEMPTED=1
run systemctl start "${UNIT}"
wait_started "${T1}"
DECRYPT_DONE=1
if (( DRY_RUN )); then
    log "dry run: after the decrypt start every field would be CLEARTEXT on disk; nothing was started"
else
    log "decrypt start done: every field is now CLEARTEXT on disk; proceeding immediately"
fi

# --- 6-7. stop, swap keys, remove the drop-in, encrypt start ----------------------------------
run systemctl stop "${UNIT}"
if (( DRY_RUN )); then
    log "would: cp -p ${CRED} ${CRED}.old (0600) ; mv -f ${CRED_NEW} ${CRED} (one atomic rename)"
else
    cp -p "${CRED}" "${CRED}.old"; chmod 0600 "${CRED}.old"; chown root:root "${CRED}.old"
    mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"; chown root:root "${CRED}"
fi
remove_dropin
T2="$(date '+%Y-%m-%d %H:%M:%S')"
ENCRYPT_ATTEMPTED=1
run systemctl start "${UNIT}"
wait_started "${T2}"
ENCRYPT_DONE=1

# --- 8. exit gate on a COPY ---------------------------------------------------------------------
run systemctl stop "${UNIT}"
if (( DRY_RUN )); then
    log "would: copy ${DB} (+ -wal/-shm) to ${WORKDIR} and run ${GATE##*/} on the copy: encrypted-fields=True, every enc-v1 blob in all five columns carries sha256(new key); then assert no drop-in"
else
    COPY="${WORKDIR}/gate-$(date +%s).sqlite"
    copy_db "${COPY}"
    gate_rc=0
    GATE_REPORT="$(python3 "${GATE}" "${COPY}" "${CRED}")" || gate_rc=$?
    shred_copy
    if (( gate_rc )); then
        GATE_FAILED=1
        die "the exit gate FAILED (exit ${gate_rc}): ${GATE_REPORT:-no report; see above}"
    fi
    GATE_PASSED=1
    log "exit gate PASSED: ${GATE_REPORT}"
    [[ ! -e "${DROPIN}" ]] || die "drop-in present at the gate: ${DROPIN}"
fi

# --- 9. checkpoint and vacuum with the server stopped -----------------------------------------
if (( DRY_RUN )); then
    log "would: python3 sqlite3 'PRAGMA wal_checkpoint(TRUNCATE); VACUUM;' on ${DB} (server stopped)"
else
    sudo -u duplicati -- python3 - "${DB}" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
con.execute("VACUUM")
con.close()
print("checkpoint + VACUUM done")
PY
fi
VACUUM_DONE=1

# --- 10. start, resume, verify ------------------------------------------------------------------
T3="$(date '+%Y-%m-%d %H:%M:%S')"
run systemctl start "${UNIT}"
wait_started "${T3}"
api resume
PAUSED=0
if (( DRY_RUN )); then
    log "would: api serverstate (must read Running, exit 0); shred ${CRED}.old"
else
    api serverstate || die "serverstate is not Running after resume"
    shred -u "${CRED}.old" 2>/dev/null || rm -f "${CRED}.old"
    log "re-key complete: the old key is shredded; escrow the NEW key now if not already done (I-40)"
fi
DONE=1
