#!/usr/bin/env bash
# Deploy (or re-deploy) alerting candidate B: the Yamaguchi server-run backup watchdog on a user timer.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-26
# Status:     ad-hoc — one-off (Paul's 2026-08-26 pick: architecture B; re-runnable after a reboot or re-clone)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8.6-4);
#             notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (§7.6);
#             util/systemd/yamaguchi-watchdog.{service,timer}; util/ad-hoc/yamaguchi_watchdog.py
#
# Usage:      bash util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>
#
# --backup-id is REQUIRED and has no default. A rebuilt job is not id 2 (Procedure B's
# sqlite_sequence starts at 1), and a watchdog pointed at an id the server does not have alerts
# JOB_MISSING forever (design §7.6). Read the id from
# `python3 util/ad-hoc/yamaguchi_server_api.py status`. It is written to the drop-in
# yamaguchi-watchdog.service.d/backup-id.conf as Environment=YAMAGUCHI_BACKUP_ID=<id>, and the
# unit hands it to the watchdog as --backup-id.
#
# Idempotent. Copies the two units from the PRIMARY checkout (the unit's ExecStart names that
# checkout's script, so it must be synced to a main that carries the --backup-id unit first --
# refused otherwise), writes the drop-in, reloads, enables the timer persistently
# (WantedBy=timers.target, Persistent=true), runs one check now, and prints the durable status
# line. B depends on Linger=yes for the user -- a lingerless session is the 42-day-outage
# mechanism -- so that is asserted first.
set -euo pipefail

usage() {
    echo "usage: bash $0 --backup-id <id>   (the job's numeric id, from: python3 util/ad-hoc/yamaguchi_server_api.py status)" >&2
}

# --- arguments: refused before anything on the host is read or changed --------------------------
BACKUP_ID=""
while (($# > 0)); do
    case "$1" in
        --backup-id)
            if (($# < 2)); then
                usage
                exit 2
            fi
            BACKUP_ID="$2"
            shift 2
            ;;
        --backup-id=*)
            BACKUP_ID="${1#--backup-id=}"
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "REFUSE: unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done
if [[ -z "$BACKUP_ID" ]]; then
    echo "REFUSE: --backup-id is required and has no default -- a rebuilt job is not id 2" >&2
    usage
    exit 2
fi
if [[ ! "$BACKUP_ID" =~ ^[1-9][0-9]*$ ]]; then
    echo "REFUSE: --backup-id must be a positive integer (the job's id), got '$BACKUP_ID'" >&2
    exit 2
fi

PRIMARY=/home/pcalnon/Development/python/Juniper/juniper-ml
UNIT_DIR="$HOME/.config/systemd/user"
DROPIN_DIR="$UNIT_DIR/yamaguchi-watchdog.service.d"
STATE_DIR="$HOME/.local/state/duplicati"

if [ ! -f "$PRIMARY/util/ad-hoc/yamaguchi_watchdog.py" ]; then
    echo "REFUSE: $PRIMARY lacks util/ad-hoc/yamaguchi_watchdog.py -- sync the primary checkout to main first" >&2
    exit 2
fi
# The unit installed below must hand the id to the watchdog. A primary checkout that predates
# that ships a unit without it, and the watchdog -- which requires --backup-id -- would exit 2 on
# every fire without writing a record. The single quotes are deliberate: the unit file must
# contain the literal ${YAMAGUCHI_BACKUP_ID}, which systemd expands.
# shellcheck disable=SC2016
if ! grep -qF -- '--backup-id ${YAMAGUCHI_BACKUP_ID}' "$PRIMARY/util/systemd/yamaguchi-watchdog.service"; then
    echo "REFUSE: $PRIMARY/util/systemd/yamaguchi-watchdog.service does not pass --backup-id from YAMAGUCHI_BACKUP_ID -- sync the primary checkout to main first" >&2
    exit 2
fi
linger=$(loginctl show-user "$USER" -p Linger --value)
if [ "$linger" != "yes" ]; then
    echo "REFUSE: Linger=$linger for $USER -- the timer would not fire without a login session (loginctl enable-linger)" >&2
    exit 2
fi

install -m 0644 "$PRIMARY/util/systemd/yamaguchi-watchdog.service" "$PRIMARY/util/systemd/yamaguchi-watchdog.timer" "$UNIT_DIR/"
# The job id, as a drop-in: written whole and renamed into place, so a reload never reads half a file.
install -d -m 0755 "$DROPIN_DIR"
printf '[Service]\nEnvironment=YAMAGUCHI_BACKUP_ID=%s\n' "$BACKUP_ID" >"$DROPIN_DIR/backup-id.conf.tmp"
chmod 0644 "$DROPIN_DIR/backup-id.conf.tmp"
mv -f "$DROPIN_DIR/backup-id.conf.tmp" "$DROPIN_DIR/backup-id.conf"
systemctl --user daemon-reload
systemctl --user enable --now yamaguchi-watchdog.timer
# One check now. A non-zero exit IS the alert (the durable record is already written);
# keep going so the status line below is still printed.
if ! systemctl --user start yamaguchi-watchdog.service; then
    echo "ALERT: the first check did not read OK -- see $STATE_DIR/server-failures.log" >&2
fi
echo "== timer"
systemctl --user list-timers yamaguchi-watchdog.timer --no-pager
echo "== enabled: $(systemctl --user is-enabled yamaguchi-watchdog.timer)"
echo "== job id (drop-in): $(systemctl --user show yamaguchi-watchdog.service -p Environment --value)"
echo "== status"
cat "$STATE_DIR/server-watchdog.status"
