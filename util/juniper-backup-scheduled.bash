#!/usr/bin/env bash
# Decide whether a Juniper USB archive run is due and, if so, run util/juniper-backup.bash.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Invoked by juniper-backup.timer (cadence) and juniper-backup.path (a drive appeared).
#   * no configured drive mounted            -> SKIPPED, exit 0 (escalates to FAILED after STALE_DAYS)
#   * drives mounted but none due            -> SKIPPED, exit 0
#   * a due drive is mounted                 -> run the archive script; exit with its code;
#                                               stamp every mounted drive on exit 0
# "Due" = no success stamp for that drive newer than PERIOD_DAYS. State lives in
# ~/.local/state/juniper-backup/. The archive script itself decides which mounted drives
# receive copies (all of them); this wrapper only decides whether to run at all.
set -euo pipefail

RUNNER="${JUNIPER_BACKUP_RUNNER:-${HOME}/.local/bin/juniper-backup.bash}"
STATE_DIR="${JUNIPER_BACKUP_STATE_DIR:-${HOME}/.local/state/juniper-backup}"
MEDIA_ROOT="${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}"   # udisks2 >= 2.10.91 (design §4.5)
BACKUP_DIR="${JUNIPER_BACKUP_DIR:-Juniper-8.0.0.python}"
PERIOD_DAYS="${JUNIPER_BACKUP_PERIOD_DAYS:-7}"
STALE_DAYS="${JUNIPER_BACKUP_STALE_DAYS:-21}"
read -r -a DEVICES <<< "${JUNIPER_BACKUP_DEVICES:-EBC5-F0A3 DFF3-2782}"

mkdir -p "${STATE_DIR}"
STATUS_FILE="${STATE_DIR}/last-run.status"
LOCK_FILE="${STATE_DIR}/run.lock"
NOW="$(date +%s)"

log() { printf '%s %s\n' "$(date -Is)" "$*"; }
write_status() { printf 'result=%s\nwhen=%s\nreason=%s\n' "$1" "$(date -Is)" "$2" > "${STATUS_FILE}"; }

newest_success_age_days() {
    # Age in days of the newest success stamp across all devices; 100000 when none exists.
    local newest=0 f
    for f in "${STATE_DIR}"/last-success.*; do
        [[ -e "${f}" ]] || continue
        local m; m="$(stat -c '%Y' "${f}")"
        (( m > newest )) && newest="${m}"
    done
    if (( newest == 0 )); then echo 100000; else echo $(( (NOW - newest) / 86400 )); fi
}

skip_or_fail() {
    local reason="$1" age
    age="$(newest_success_age_days)"
    if (( age > STALE_DAYS )); then
        log "FAILED: ${reason}; no successful run in ${age} days (limit ${STALE_DAYS})"
        write_status FAILED "${reason}; stale ${age}d"
        exit 1
    fi
    log "SKIPPED: ${reason}"
    write_status SKIPPED "${reason}"
    exit 0
}

exec 9>"${LOCK_FILE}"
flock -n 9 || skip_or_fail "another run holds ${LOCK_FILE}"
[[ -x "${RUNNER}" ]] || { log "FATAL: runner missing: ${RUNNER}"; write_status FAILED "runner missing"; exit 1; }

mounted=()
unusable=()
due=()
for dev in "${DEVICES[@]}"; do
    root="${MEDIA_ROOT}/${dev}"
    mountpoint -q "${root}" || continue
    [[ -d "${root}/${BACKUP_DIR}" && -w "${root}/${BACKUP_DIR}" ]] || { log "WARN: ${root} mounted but ${BACKUP_DIR} missing or read-only"; unusable+=("${dev}"); continue; }
    mounted+=("${dev}")
    stamp="${STATE_DIR}/last-success.${dev}"
    if [[ ! -e "${stamp}" ]] || (( (NOW - $(stat -c '%Y' "${stamp}")) / 86400 >= PERIOD_DAYS )); then
        due+=("${dev}")
    fi
done

(( ${#mounted[@]} > 0 )) || skip_or_fail "no configured drive usable under ${MEDIA_ROOT} (wanted: ${DEVICES[*]}; mounted but unusable: ${unusable[*]:-none})"
(( ${#due[@]} > 0 )) || skip_or_fail "mounted (${mounted[*]}) but none due within ${PERIOD_DAYS} days"

log "running ${RUNNER}: mounted=${mounted[*]} due=${due[*]}"
set +e
"${RUNNER}" "$@"
rc=$?
set -e
if (( rc == 0 )); then
    for dev in "${mounted[@]}"; do touch "${STATE_DIR}/last-success.${dev}"; done
    write_status OK "devices ${mounted[*]}"
    log "OK (stamped ${mounted[*]})"
else
    write_status FAILED "runner rc=${rc}"
    log "FAILED rc=${rc} (no stamp written)"
fi
exit "${rc}"
