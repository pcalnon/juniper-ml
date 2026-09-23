#!/usr/bin/env bash
# Install the duplicati.service lane from this repository: wrapper, unit, defaults file.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Copies, never symlinks: a symlink into a git checkout turns a branch switch or a worktree
# removal into a silent change of what the service executes. Run with sudo. Does NOT restart
# the service; prints the verification commands instead.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER_SRC="${REPO_DIR}/scripts/duplicati-wrapper.bash"
UNIT_SRC="${REPO_DIR}/util/systemd/duplicati.service"
DEFAULTS_SRC="${REPO_DIR}/util/systemd/duplicati.default"
GUARD_SRC="${REPO_DIR}/util/yamaguchi-pre-backup-guard.bash"
WRAPPER_DST=/usr/local/lib/duplicati/duplicati-wrapper.bash
UNIT_DST=/etc/systemd/system/duplicati.service
DEFAULTS_DST=/etc/default/duplicati
GUARD_DST=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash
DATA_FOLDER=/home/duplicati/.config/Duplicati
CRED_DST=/etc/credstore/duplicati-settings-key

[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
for f in "${WRAPPER_SRC}" "${UNIT_SRC}" "${DEFAULTS_SRC}" "${GUARD_SRC}"; do
    [[ -f "${f}" ]] || { echo "missing source: ${f}" >&2; exit 2; }
done
bash -n "${WRAPPER_SRC}"
bash -n "${GUARD_SRC}"

# --- D-6 drift gate (RULED 2026-09-22) -----------------------------------------------------
# The repository is canonical and what the unit executes is a COPY. Two different things can
# therefore drift, and they mean OPPOSITE things:
#
#   * the INSTALLED file no longer matches what was blessed -> someone edited /usr/local/lib
#     outside this installer. Never overwrite that silently; it is the only evidence.
#   * the REPOSITORY no longer matches what was blessed -> an intended behaviour change. That
#     is legitimate, and is exactly what --update-backup-behavior authorises.
#
# A symlink into the checkout was considered for this job and rejected: on a fresh host the
# checkout does not exist yet, so ExecStart= would resolve to a dangling target and the service
# would not start -- failing in the bare-metal recovery case the symlink was proposed for.
BLESSED=/usr/local/lib/duplicati/.blessed.sha256
UPDATE_BEHAVIOR=0
for arg in "$@"; do
    [[ "${arg}" == "--update-backup-behavior" ]] && UPDATE_BEHAVIOR=1
done

blessed_for() { [[ -s "${BLESSED}" ]] && awk -v d="$1" '$2 == d { print $1 }' "${BLESSED}"; }

drift=0
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    want="$(blessed_for "${dst}")"
    [[ -n "${want}" ]] || continue          # never blessed: first install, nothing to compare
    if [[ -f "${dst}" ]] && [[ "$(sha256sum "${dst}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "DRIFT: installed ${dst} does not match its blessed checksum -- changed outside this installer" >&2
        drift=1
    fi
    if [[ "$(sha256sum "${src}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "BEHAVIOUR CHANGE: ${src} differs from the blessed checksum" >&2
        drift=1
    fi
done
if (( drift == 1 && UPDATE_BEHAVIOR == 0 )); then
    echo "Refusing to install. Inspect the differences, then re-run with --update-backup-behavior" >&2
    echo "to bless the current repository contents as what this host executes." >&2
    exit 4
fi

install -d -m 0755 -o root -g root /usr/local/lib/duplicati
install -d -m 0700 -o root -g root /etc/credstore
install -m 0755 -o root -g root "${WRAPPER_SRC}" "${WRAPPER_DST}"
install -m 0644 -o root -g root "${UNIT_SRC}" "${UNIT_DST}"
install -m 0644 -o root -g root "${DEFAULTS_SRC}" "${DEFAULTS_DST}"
# The guard is --run-script-before-REQUIRED: a missing file aborts every backup. It must be
# installed by the same script that installs the unit, or the first post-recovery run fails.
install -m 0755 -o root -g root "${GUARD_SRC}" "${GUARD_DST}"

# 2.4.0.0 refuses a pre-existing data folder with any group or other bit, at EVERY start.
install -d -m 0700 -o duplicati -g duplicati "${DATA_FOLDER}"
if [[ "$(stat -c '%U:%a' "${DATA_FOLDER}")" != "duplicati:700" ]]; then
    echo "${DATA_FOLDER} must be duplicati-owned mode 0700 (Duplicati refuses anything else)" >&2
    exit 1
fi

: > "${BLESSED}.new"
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
    printf '%s  %s\n' "$(sha256sum "${dst}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"
    echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
done
# Bless only after every copy verified. A blessed file written earlier would record a state that
# a later failure never reached, and the next run would compare against a fiction.
install -m 0644 -o root -g root "${BLESSED}.new" "${BLESSED}"
rm -f "${BLESSED}.new"
echo "blessed ${BLESSED} (re-bless deliberately with --update-backup-behavior)"

if [[ ! -s "${CRED_DST}" ]]; then
    printf '%s\n' "NOTE: ${CRED_DST} is absent or empty. Create it before starting:" \
        "      umask 077; openssl rand -base64 48 | tr -d '\\n' > ${CRED_DST}; chmod 0600 ${CRED_DST}" \
        "      and escrow it with the passphrases (it is a third key)." >&2
else
    [[ "$(stat -c '%U:%a' "${CRED_DST}")" == "root:600" ]] || { echo "${CRED_DST} must be root-owned mode 0600" >&2; exit 1; }
fi

systemctl daemon-reload
systemd-analyze verify "${UNIT_DST}"
echo
echo "Next: sudo -u duplicati ${WRAPPER_DST} --print-command  (dry run, no server started)"
echo "      sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi \\"
echo "           ${GUARD_DST}; echo \"guard exit=\$?\"   (must be 0 BEFORE the job is resumed)"
echo "      systemctl restart duplicati.service && journalctl -u duplicati.service -n 20"
echo "      systemd-analyze security duplicati.service"
