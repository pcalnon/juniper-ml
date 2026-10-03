#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Juniper USB-Archive (Tier 2) Timer Installer
# Author:       Paul Calnon
# Version:      1.0.0
# License:      MIT
############################################################################################################################################################
#
# Installs the `systemd --user` tier-2 lane of the backup design
# (notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.8, §8 P3 step 2):
#
#   ~/.local/bin/juniper-backup.bash                        the archive runner          <- util/juniper-backup.bash
#   ~/.local/bin/juniper-backup-scheduled.bash              the due-or-skip scheduler   <- util/juniper-backup-scheduled.bash
#   ~/.local/bin/duplicati-backup-failure.bash              the OnFailure reporter      <- util/duplicati_backup_failure.bash
#   ~/.config/systemd/user/juniper-backup.timer             the weekly window
#   ~/.config/systemd/user/juniper-backup.path              fires the service when a drive is mounted
#   ~/.config/systemd/user/juniper-backup.service           runs the scheduler
#   ~/.config/systemd/user/juniper-backup-failure.service   the service's OnFailure= target
#
# then `systemctl --user daemon-reload` and `systemctl --user enable --now juniper-backup.timer juniper-backup.path`.
# Every installed name is the one a unit's ExecStart= or the scheduler's default RUNNER already expects.
#
# Usage:
#     bash util/install_juniper_backup_timer.bash [--dry-run]
#
#     Invoke it through bash: a file added by an API-signed commit lands without the executable bit.
#
#     --dry-run   Run every read-only check, then print each action the real run would take and touch
#                 nothing: no directory, no file, no systemctl call. Exits as the real run would, so a
#                 non-zero dry run means the real run would refuse.
#
# Exit codes:
#     0  installed and enabled (under --dry-run: would install and enable)
#     1  refused before anything was written: running as root, a source file missing, systemctl
#        absent, or Linger not enabled
#     2  misuse (unknown argument)
#
# WHY THE SCRIPTS ARE COPIED RATHER THAN SYMLINKED
#   Same reason as util/install_duplicati_timer.bash: the canonical copies live in a git worktree, and a
#   symlink into one turns an ordinary `git worktree remove` or branch switch into a silent change of what
#   the timer runs. `install` also REPLACES a symlink already sitting at a destination instead of writing
#   through it into whatever checkout it points at -- which `cp` would do. Re-run this script to update.
#
# WHY THIS ONE ENABLES ITS TIMER WHEN install_duplicati_timer.bash DOES NOT
#   That installer holds its timer back because a second Duplicati run against the same local database,
#   while the first full backup is still in flight, could damage it. This lane has no such state: the
#   scheduler takes a non-blocking flock and SKIPs while another run holds it, and a run with no drive
#   mounted is a SKIP once the lane has succeeded. Before its first success, or STALE_DAYS after its last,
#   that same run is FAILED and OnFailure= fires -- the alert this lane lacked. The design's P3 step 2
#   enables both units at install time.
#
# THE REPORTER IS SHARED WITH THE DUPLICATI LANE
#   ~/.local/bin/duplicati-backup-failure.bash is also what install_duplicati_timer.bash installs, from the
#   same repository file, so whichever installer ran last wrote the same bytes. The two lanes are told
#   apart by the UNIT, not the script: juniper-backup-failure.service sets DUPLICATI_STATE_DIR to this
#   lane's state directory and passes juniper-backup.service as $1.
#
# REFUSES TO RUN AS ROOT
#   These are --user units under $HOME. Under sudo they would land in /root, root-owned, where the user's
#   manager never looks -- and `systemctl --user` as root talks to root's manager, not the user's.
############################################################################################################################################################

set -euo pipefail

DRY_RUN=0
while (( $# > 0 )); do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) sed -n '/^# Usage:/,/^# Exit codes:/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

REPO_UTIL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"
STATE_DIR="${HOME}/.local/state/juniper-backup"

# Parallel arrays: repository file under util/  ->  installed name under BIN_DIR. The reporter is renamed
# (underscores to hyphens) because juniper-backup-failure.service, like the Duplicati lane's unit, names
# the hyphenated form in its ExecStart=.
SCRIPT_SOURCES=( "juniper-backup.bash" "juniper-backup-scheduled.bash" "duplicati_backup_failure.bash" )
SCRIPT_TARGETS=( "juniper-backup.bash" "juniper-backup-scheduled.bash" "duplicati-backup-failure.bash" )
UNITS=( "juniper-backup.timer" "juniper-backup.path" "juniper-backup.service" "juniper-backup-failure.service" )
ENABLE_UNITS=( "juniper-backup.timer" "juniper-backup.path" )

say() { printf '%s\n' "$*"; }

refuse() {
    printf '!!  %s\n' "$*" >&2
    if (( DRY_RUN )); then
        printf '!!  (dry run: the real run would stop here, before writing anything)\n' >&2
    fi
    exit 1
}

# Run one action, or under --dry-run print it. Every word is %q-quoted, so a printed line is the exact
# command the real run executes and can be pasted as-is.
act() {
    if (( DRY_RUN )); then
        printf '[dry-run] would run:'
        printf ' %q' "$@"
        printf '\n'
    else
        "$@"
    fi
}

# What a copy will do to its destination. Read-only.
copy_state() {
    local src="$1" dst="$2"
    if [[ -L "${dst}" ]]; then
        echo "replaces a symlink"
    elif [[ ! -e "${dst}" ]]; then
        echo "new"
    elif cmp -s -- "${src}" "${dst}"; then
        echo "unchanged"
    else
        echo "changed"
    fi
}

# Create a directory only if it is absent. `install -d -m` re-modes a directory that already exists, and
# this installer has no business loosening (or tightening) ~/.config/systemd/user behind the user's back.
ensure_dir() {
    local dir="$1"
    if [[ -d "${dir}" ]]; then
        say "    ${dir} exists"
    else
        act install -d -m 0755 "${dir}"
    fi
}

if (( DRY_RUN )); then
    say "==> install_juniper_backup_timer.bash --dry-run: nothing will be written"
fi

#######################################################################################################################################################
# Preflight. Everything that can refuse is checked BEFORE the first write, so a refusal leaves nothing half-installed.
#######################################################################################################################################################
say "==> preflight"

uid="$(id -u)"
if (( uid == 0 )); then
    refuse "refusing to run as root (uid 0): these are systemd --user units under \$HOME. Run as the user whose backup this is, without sudo."
fi
say "    ok  not root (uid ${uid})"

for name in "${SCRIPT_SOURCES[@]}"; do
    [[ -r "${REPO_UTIL}/${name}" ]] || refuse "source missing: ${REPO_UTIL}/${name}"
done
for unit in "${UNITS[@]}"; do
    [[ -r "${REPO_UTIL}/systemd/${unit}" ]] || refuse "source missing: ${REPO_UTIL}/systemd/${unit}"
done
say "    ok  $(( ${#SCRIPT_SOURCES[@]} + ${#UNITS[@]} )) source files present under ${REPO_UTIL}"

command -v systemctl > /dev/null 2>&1 || refuse "systemctl not found: this lane needs a systemd --user manager"
say "    ok  systemctl found"

user_name="$(id -un)"
linger="$(loginctl show-user "${user_name}" --property=Linger --value 2> /dev/null || true)"
if [[ "${linger}" != "yes" ]]; then
    refuse "Linger is NOT enabled for ${user_name} (loginctl reported '${linger:-nothing}'). Without it the user manager exits at logout and the weekly timer does not fire. Fix with: loginctl enable-linger ${user_name}"
fi
say "    ok  Linger=yes for ${user_name}"

#######################################################################################################################################################
# Install.
#######################################################################################################################################################
say "==> scripts -> ${BIN_DIR}"
ensure_dir "${BIN_DIR}"
for i in "${!SCRIPT_SOURCES[@]}"; do
    src="${REPO_UTIL}/${SCRIPT_SOURCES[${i}]}"
    dst="${BIN_DIR}/${SCRIPT_TARGETS[${i}]}"
    state="$(copy_state "${src}" "${dst}")"
    say "    ${SCRIPT_TARGETS[${i}]}  (${state})"
    act install -m 0755 "${src}" "${dst}"
done

say "==> units -> ${UNIT_DIR}"
ensure_dir "${UNIT_DIR}"
for unit in "${UNITS[@]}"; do
    src="${REPO_UTIL}/systemd/${unit}"
    dst="${UNIT_DIR}/${unit}"
    state="$(copy_state "${src}" "${dst}")"
    say "    ${unit}  (${state})"
    act install -m 0644 "${src}" "${dst}"
done

say "==> systemctl --user daemon-reload"
act systemctl --user daemon-reload

say "==> systemctl --user enable --now ${ENABLE_UNITS[*]}"
act systemctl --user enable --now "${ENABLE_UNITS[@]}"

if (( DRY_RUN )); then
    say "[dry-run] nothing was written."
    exit 0
fi

say
say "Installed and enabled. Acceptance (design AC-10, §8 P3 step 2) reads ${STATE_DIR}/last-run.status."
say "Do the OK run FIRST. Until one run has succeeded, a run with no stick mounted reads result=FAILED, not"
say "SKIPPED: the scheduler counts 'never succeeded' as older than STALE_DAYS, and OnFailure= fires."
say "    systemctl --user list-timers juniper-backup.timer   # the weekly window is scheduled"
say "    # Mount a stick. The .path unit should start a due run (hours: every repo); if it does not, start"
say "    # juniper-backup.service by hand. Expect result=OK and verified archives on every mounted stick."
say "    systemctl --user status juniper-backup.path         # still active 30 s after the plug-in"
say "    systemctl --user start juniper-backup.service       # AFTER the OK run, no stick mounted -> result=SKIPPED"
say "    bash util/ad-hoc/2026-08-26_backup_restore_drill.bash   # the class-1 drill"
