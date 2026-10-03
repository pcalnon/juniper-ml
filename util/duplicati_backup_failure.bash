#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Duplicati Backup Failure Reporter
# Author:       Paul Calnon
# Version:      1.1.0
# License:      MIT
############################################################################################################################################################
#
# Invoked through `OnFailure=` by two lanes, each with its own reporter unit:
#   duplicati-backup-failure.service  for duplicati-backup.service (the default $1 and state dir)
#   juniper-backup-failure.service    for juniper-backup.service (tier 2; its unit points
#                                     DUPLICATI_STATE_DIR at ~/.local/state/juniper-backup)
# $1 is the failed unit. It heads the record, selects the journal tail and titles the
# notification, so a report always names the lane that actually failed.
#
# HISTORY
#   1.1.0  2026-10-03  The notification is titled with $1. It read "Duplicati backup FAILED"
#                      for every caller, so a tier-2 failure was announced as the Duplicati
#                      lane's: a report about a lane that had not failed.
#
# WHY THIS EXISTS
#   "A backup that silently stops is indistinguishable from one that works."
#   The 2026-07-13 damage went unnoticed for six weeks because nothing reported
#   anything. This is the reporting half of that fix.
#
# DESIGN
#   The durable record comes FIRST and has no dependencies. The desktop
#   notification is strictly best-effort: under `Linger=yes` with no graphical
#   session there is no session bus to talk to, and a notification that cannot be
#   delivered must never mask the failure record. Hence `|| true` on notify-send
#   but not on the log write.
############################################################################################################################################################

set -uo pipefail

STATE_DIR="${DUPLICATI_STATE_DIR:-${HOME}/.local/state/duplicati}"
FAILURE_LOG="${STATE_DIR}/failures.log"
STATUS_FILE="${STATE_DIR}/last-run.status"
UNIT="${1:-duplicati-backup.service}"

mkdir -p "${STATE_DIR}"

WHEN="$(date -Is)"

{
    printf '=== %s  FAILURE  unit=%s ===\n' "${WHEN}" "${UNIT}"
    if [[ -r "${STATUS_FILE}" ]]; then
        printf -- '--- last-run.status ---\n'
        cat "${STATUS_FILE}"
    else
        printf -- '--- no last-run.status present (the runner died before writing one) ---\n'
    fi
    printf -- '--- journal tail ---\n'
    journalctl --user -u "${UNIT}" -n 40 --no-pager 2>/dev/null \
        || printf '(journal unavailable)\n'
    printf '\n'
} >> "${FAILURE_LOG}"

# Best-effort desktop notification. Never allowed to affect the exit status.
if command -v notify-send > /dev/null 2>&1; then
    notify-send --urgency=critical \
        "Backup FAILED: ${UNIT}" \
        "${WHEN}
See ${FAILURE_LOG}" > /dev/null 2>&1 || true
fi

# Exit 0: this reporter succeeded at reporting. The failure itself is already
# recorded on the failed unit, and a non-zero here would only add a second,
# confusing failed unit.
exit 0
