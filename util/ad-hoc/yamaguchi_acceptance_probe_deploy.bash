#!/usr/bin/env bash
# Deploy (or re-deploy) the Yamaguchi acceptance probe on a daily user timer.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-11-11
# Status:     ad-hoc — recovery (Phase D sitting, step 14, and the acceptance window after it)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/yamaguchi_acceptance_probe.py; util/systemd/yamaguchi-acceptance-probe.{service,timer};
#             notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (section 9);
#             util/ad-hoc/yamaguchi_watchdog_deploy.bash (the pattern this follows, with one difference below);
#             tests/test_yamaguchi_acceptance_probe.py
#
# Usage:      bash util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash --backup-id <id>
#
# Run it as the user who owns the web credential and the Dropbox daemon -- never as root. It is
# idempotent, and re-running it is how a new version of the probe is taken.
#
# --backup-id is REQUIRED and has no default, for the watchdog's reason: a rebuilt job is not id 2.
# It is written to the drop-in yamaguchi-acceptance-probe.service.d/backup-id.conf.
#
# The one difference from the watchdog's deploy: the probe and the API client it imports are COPIED
# to ~/.local/lib/yamaguchi-acceptance/ and the unit runs the copies. The watchdog's unit runs the
# primary checkout's script, so it changes at every merge and breaks whenever that checkout is on a
# branch without the script (on 2026-11-11 it was). The copies are taken from the directory this
# script is in, whatever checkout or worktree that is; their SHA-256 is printed so the record can
# name what was deployed.
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
if [[ "$(id -u)" -eq 0 ]]; then
    echo "REFUSE: run this as the user who owns the web credential, not as root -- it installs a USER timer" >&2
    exit 2
fi

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
UNITS="$(cd -- "$HERE/../systemd" && pwd -P)"
LIB="$HOME/.local/lib/yamaguchi-acceptance"
UNIT_DIR="$HOME/.config/systemd/user"
DROPIN_DIR="$UNIT_DIR/yamaguchi-acceptance-probe.service.d"
FILES=(yamaguchi_acceptance_probe.py yamaguchi_server_api.py)

for name in "${FILES[@]}"; do
    if [[ ! -f "$HERE/$name" ]]; then
        echo "REFUSE: $HERE lacks $name -- run this script from a checkout that holds the probe" >&2
        exit 2
    fi
done
for name in yamaguchi-acceptance-probe.service yamaguchi-acceptance-probe.timer; do
    if [[ ! -f "$UNITS/$name" ]]; then
        echo "REFUSE: $UNITS lacks $name" >&2
        exit 2
    fi
done
# `id -un`, not $USER: under `set -u` an unset USER would end the script on an unbound variable.
ME="$(id -un)"
if ! linger="$(loginctl show-user "$ME" -p Linger --value)"; then
    echo "REFUSE: loginctl could not read Linger for $ME -- without it the timer cannot be shown to fire outside a login session" >&2
    exit 2
fi
if [[ "$linger" != "yes" ]]; then
    echo "REFUSE: Linger=$linger for $ME -- the timer would not fire without a login session (loginctl enable-linger)" >&2
    exit 2
fi

install -d -m 0700 "$LIB"
for name in "${FILES[@]}"; do
    # Written beside the target and renamed into place, so a fire never reads half a file.
    install -m 0644 "$HERE/$name" "$LIB/$name.new"
    mv -f "$LIB/$name.new" "$LIB/$name"
done
install -d -m 0755 "$UNIT_DIR" "$DROPIN_DIR"
install -m 0644 "$UNITS/yamaguchi-acceptance-probe.service" "$UNITS/yamaguchi-acceptance-probe.timer" "$UNIT_DIR/"
printf '[Service]\nEnvironment=YAMAGUCHI_BACKUP_ID=%s\n' "$BACKUP_ID" >"$DROPIN_DIR/backup-id.conf.new"
chmod 0644 "$DROPIN_DIR/backup-id.conf.new"
mv -f "$DROPIN_DIR/backup-id.conf.new" "$DROPIN_DIR/backup-id.conf"
systemctl --user daemon-reload
systemctl --user enable --now yamaguchi-acceptance-probe.timer
# One run now. A non-zero exit is a FAIL or an unreadable piece of evidence, which is what the
# probe is for; keep going so the verdict lines below are still printed.
if ! systemctl --user start yamaguchi-acceptance-probe.service; then
    echo "NOTE: the first run did not read PASS -- its verdict lines are below" >&2
fi
echo "== deployed"
for name in "${FILES[@]}"; do
    echo "sha256 $(sha256sum "$LIB/$name" | cut -d' ' -f1) $LIB/$name"
done
echo "== timer"
systemctl --user list-timers yamaguchi-acceptance-probe.timer --no-pager
echo "== enabled: $(systemctl --user is-enabled yamaguchi-acceptance-probe.timer)"
echo "== job id (drop-in): $(systemctl --user show yamaguchi-acceptance-probe.service -p Environment --value)"
echo "== first run"
journalctl --user -u yamaguchi-acceptance-probe.service -n 40 --no-pager -o cat
