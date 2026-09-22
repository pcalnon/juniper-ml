#!/usr/bin/env bash
# Duplicati --run-script-before-required hook for the Yamaguchi job.
# Exit 0: proceed. Any other exit: Duplicati aborts the operation before touching the
# destination. 5 is used deliberately ("error, do not run" in the run-script contract), and an
# unexpected failure inside this script is converted to 5 too, so a bug here can only stop a
# backup, never wave one through.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
set -euo pipefail
trap 'exit 5' ERR

# Duplicati's RunScript exports EVERY job option into this script's environment, unfiltered and
# prefixed DUPLICATI__ -- the job passphrase among them -- and the wrapper's exported settings
# key is inherited too. Both would then pass to every child (mountpoint, find, id). Drop them
# before anything else runs. (Lane B3 F-4.)
# A DENYLIST CANNOT BE COMPLETE over a set the comment above calls "every job option,
# unfiltered" -- section 8 Procedure A2 alone names passphrase, jwt-config, pbkdf-config,
# remote-control-config and the ssl cert fields, and jwt-config is the server's JWT signing
# key (with it, mint any API token, then set --run-script-before to anything). Keep only what
# this guard uses, the same POSITIVE shape the wrapper uses in section 7.3.3.
_keep_op="${DUPLICATI__OPERATIONNAME:-unknown}"
_keep_url="${DUPLICATI__REMOTEURL:-}"
while IFS='=' read -r _n _; do
    case "${_n}" in DUPLICATI__*) unset "${_n}" ;; esac
done < <(env)
unset SETTINGS_ENCRYPTION_KEY _n _
# This does NOT put the settings key out of reach: $CREDENTIALS_DIRECTORY is inherited and
# /run/credentials/duplicati.service is a fixed path, readable by every process in the unit
# (man systemd.exec). Section 7.3.2 records that residual; the secret-provider channel
# (section 7.3.5) is what removes it. `unset` also does not rewrite /proc/<pid>/environ, so
# the original block persists for this process's lifetime -- no NEW exposure, but not the
# clean slate the word "unset" suggests.
# STDOUT IS NOT A LOG. Duplicati parses a run-script's stdout as OPTION OVERRIDES
# (--option=value lines change the running job). Every message below goes to stderr; never
# add an echo to stdout, and never set -x.

DEST_MOUNT="${YAMAGUCHI_DEST_MOUNT:-/mnt/Backups}"
DEST_DIR="${YAMAGUCHI_DEST_DIR:-/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
# Duplicati exports the job's remote URL to run-scripts as DUPLICATI__REMOTEURL.
REMOTE_URL="${_keep_url}"
OPERATION="${_keep_op}"

fail() { echo "GUARD(${OPERATION}): $*" >&2; exit 5; }

mountpoint -q "${DEST_MOUNT}" || fail "${DEST_MOUNT} is not a mountpoint"
[[ -d "${DEST_DIR}" ]] || fail "${DEST_DIR} does not exist"
[[ -w "${DEST_DIR}" && -x "${DEST_DIR}" ]] || fail "${DEST_DIR} is not writable by $(id -un)"
if [[ -n "${REMOTE_URL}" ]]; then
    case "${REMOTE_URL%/}" in
        "file://${DEST_DIR}") ;;
        # Print a SHAPE, never the URL. This branch fires exactly when the TargetURL has
        # been changed -- and a non-file:// backend URL routinely embeds credentials
        # (--auth-password is a real option across the Backend assemblies), so echoing it
        # would write a credential into the job log and from there into whatever
        # additional-report-url POSTs (S-8). The guard's own diagnostic must not be the leak.
        *) fail "job TargetURL does not match the guarded destination file://${DEST_DIR}; got scheme='${REMOTE_URL%%:*}' length=${#REMOTE_URL} sha256-8=$(printf '%s' "${REMOTE_URL}" | sha256sum | cut -c1-8)" ;;
    esac
fi
# duplicati-verification.json is allow-listed: the job does not set
# --upload-verification-file today, so the file is not written -- but enabling that option
# later would otherwise make this guard refuse every run. (Lane B2 D19.)
stray="$(find "${DEST_DIR}" -mindepth 1 -maxdepth 1 \
    ! -name 'duplicati-*.dblock.zip.aes' \
    ! -name 'duplicati-*.dindex.zip.aes' \
    ! -name 'duplicati-*.dlist.zip.aes' \
    ! -name 'duplicati-verification.json' \
    -print -quit)"
# The stray's NAME is attacker-chosen and reaches the job log; sanitise it to a character
# class so it cannot inject newlines or control sequences (open item O-13 asks whether
# SendStdOutToLogs stores stderr verbatim -- this makes the answer not matter).
[[ -z "${stray}" ]] || fail "foreign entry in destination, name sanitised: $(printf '%s' "${stray##*/}" | LC_ALL=C tr -cd 'A-Za-z0-9._-' | cut -c1-64)"
exit 0
