#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Juniper USB-Archive (Tier 2) and Full-Set (Tier 3) Timer Installer
# Author:       Paul Calnon
# Version:      1.1.0
# License:      MIT
############################################################################################################################################################
#
# Installs one `systemd --user` lane of the backup design
# (notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.8 and §7.9, §8 P3 steps 2 and 3).
# Both lanes run the same three scripts:
#
#   ~/.local/bin/juniper-backup.bash                        the archive runner          <- util/juniper-backup.bash
#   ~/.local/bin/juniper-backup-scheduled.bash              the due-or-skip scheduler   <- util/juniper-backup-scheduled.bash
#   ~/.local/bin/duplicati-backup-failure.bash              the OnFailure reporter      <- util/duplicati_backup_failure.bash
#
# and each has its own four units in ~/.config/systemd/user/. --lane usb, the default (tier 2, §7.8):
#
#   juniper-backup.timer                                    the weekly window
#   juniper-backup.path                                     fires the service when a drive is mounted
#   juniper-backup.service                                  runs the scheduler
#   juniper-backup-failure.service                          the service's OnFailure= target
#
# --lane full (tier 3, §7.9): juniper-backup-full.{timer,path,service} and juniper-backup-full-failure.service, the
# same four roles for the monthly full set on the offline drive. Its service sets the lane's environment (its own
# state directory, ~/.local/state/juniper-backup-full) and passes --label full --repos "..." through the scheduler.
#
# It then runs `systemctl --user daemon-reload` and `systemctl --user enable --now` on the lane's timer and path unit.
# Every installed name is the one a unit's ExecStart= or the scheduler's default RUNNER already expects.
# Installing either lane rewrites the three shared scripts, so it updates what the other lane runs too.
#
# Usage:
#     bash util/install_juniper_backup_timer.bash [--lane usb|full] [--dry-run]
#
#     Invoke it through bash: a file added by an API-signed commit lands without the executable bit.
#
#     --lane usb  Tier 2, the default: the weekly per-repo archive to the two USB sticks. The same as no --lane.
#     --lane full Tier 3: the monthly full set (label full) to the offline external drive. Installs nothing
#                 of tier 2's units, and changes none of them.
#     --dry-run   Run every read-only check, then print each action the real run would take and touch
#                 nothing: no directory, no file, no systemctl call. Exits as the real run would, so a
#                 non-zero dry run means the real run would refuse.
#
# Exit codes:
#     0  installed and enabled (under --dry-run: would install and enable)
#     1  refused before anything was written: running as root, a source file missing, systemctl
#        absent, or Linger not enabled
#     2  misuse (unknown argument, or a --lane other than usb or full)
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
#   lane's state directory and passes juniper-backup.service as $1. Tier 3's juniper-backup-full-failure.service
#   does the same for ~/.local/state/juniper-backup-full and juniper-backup-full.service.
#
# RE-INSTALLING WHILE A RUN IS IN PROGRESS
#   install(1) replaces a destination with a new inode (GNU coreutils 9.7 and uutils 0.10.0 both, measured
#   2026-10-25) rather than rewriting it in place, so a scheduler or runner that bash is still reading keeps
#   its own copy: installing one lane during the other lane's hours-long run does not change that run.
#
# REFUSES TO RUN AS ROOT
#   These are --user units under $HOME. Under sudo they would land in /root, root-owned, where the user's
#   manager never looks -- and `systemctl --user` as root talks to root's manager, not the user's.
############################################################################################################################################################

set -euo pipefail

DRY_RUN=0
LANE="usb"
while (( $# > 0 )); do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --lane)
            [[ $# -ge 2 && -n "$2" ]] || { echo "--lane requires usb or full" >&2; exit 2; }
            LANE="$2"; shift 2 ;;
        -h|--help) sed -n '/^# Usage:/,/^# Exit codes:/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

REPO_UTIL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"

# Parallel arrays: repository file under util/  ->  installed name under BIN_DIR. The reporter is renamed
# (underscores to hyphens) because juniper-backup-failure.service, like the Duplicati lane's unit, names
# the hyphenated form in its ExecStart=. Both lanes run these three scripts.
SCRIPT_SOURCES=( "juniper-backup.bash" "juniper-backup-scheduled.bash" "duplicati_backup_failure.bash" )
SCRIPT_TARGETS=( "juniper-backup.bash" "juniper-backup-scheduled.bash" "duplicati-backup-failure.bash" )

# The lane's units and its state directory. STATE_DIR here only names where the acceptance notes look: each
# lane's scheduler takes it from its service (tier 2's default; tier 3's Environment=JUNIPER_BACKUP_STATE_DIR).
case "${LANE}" in
    usb)
        STATE_DIR="${HOME}/.local/state/juniper-backup"
        UNITS=( "juniper-backup.timer" "juniper-backup.path" "juniper-backup.service" "juniper-backup-failure.service" )
        ENABLE_UNITS=( "juniper-backup.timer" "juniper-backup.path" )
        ;;
    full)
        STATE_DIR="${HOME}/.local/state/juniper-backup-full"
        UNITS=( "juniper-backup-full.timer" "juniper-backup-full.path" "juniper-backup-full.service" "juniper-backup-full-failure.service" )
        ENABLE_UNITS=( "juniper-backup-full.timer" "juniper-backup-full.path" )
        ;;
    *) echo "unknown lane: ${LANE} (want usb or full)" >&2; exit 2 ;;
esac

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

# The acceptance notes print in BOTH modes: the dry run is the preview an operator reads first.
if (( DRY_RUN )); then
    say "[dry-run] nothing was written. What follows applies after a real run."
else
    say
    say "Installed and enabled."
fi
if [[ "${LANE}" == "usb" ]]; then
    say "Acceptance (design AC-10, §8 P3 step 2) reads ${STATE_DIR}/last-run.status. In this order:"
    say "  1. Do the OK run FIRST, with BOTH configured sticks mounted (by default EBC5-F0A3 and DFF3-2782). One"
    say "     stick is not enough: the runner writes it and exits 4 (PARTIAL), the scheduler records"
    say "     result=FAILED and stamps nothing, and the next plug-in rebuilds the whole set. The .path unit"
    say "     should start a due run (hours: every repo); if it does not, start juniper-backup.service by hand."
    say "       systemctl --user status juniper-backup.path         # still active 30 s after the plug-in"
    say "  2. Then, with no stick mounted: result=SKIPPED. Before any success, the same run reads result=FAILED"
    say "     (the scheduler counts 'never succeeded' as older than STALE_DAYS) and OnFailure= fires."
    say "       systemctl --user start juniper-backup.service"
    say "  3. The class-1 drill: bash util/ad-hoc/2026-08-26_backup_restore_drill.bash"
    say "  The weekly window: systemctl --user list-timers juniper-backup.timer"
else
    say "Acceptance (design AC-11, §8 P3 step 3) reads ${STATE_DIR}/last-run.status. In this order:"
    say "  1. Do the OK run FIRST. Connect the tier-3 drive, Ext WD Passport \"Blackbox Part 1\": it must mount at"
    say "     /run/media/${user_name}/dee46823-4119-4914-ac15-08194ee27d81 and hold Juniper/Backups/. The .path"
    say "     unit should start the run (hours: 15 archives, label full). If last-run.status has not been written a"
    say "     minute after the mount, the trigger may have come before the mount completed; start the run by hand,"
    say "     without waiting on it (a oneshot start blocks until the run ends):"
    say "       systemctl --user start --no-block juniper-backup-full.service"
    say "       journalctl --user -u juniper-backup-full.service -f"
    say "     If the drive was already mounted when you installed, no mount event comes at all (PathChanged= does"
    say "     not fire when the path unit starts), so start that first run by hand the same way."
    say "  2. Disconnect the drive only after last-run.status reads result=OK (offline discipline, design §7.9)."
    say "     The unplug starts this lane's check again; it reads result=SKIPPED, and the success stamp stays."
    say "  3. Until that first success, a run with the drive detached reads result=FAILED and OnFailure= fires,"
    say "     and every plug-in or unplug of any drive, a tier-2 stick included, runs this lane's check. Step 1 first."
    say "  4. AC-11: restore one archive of the set and compare it with the live tree (the YubiKey decrypts):"
    say "       gpg -d Juniper_full_<name>_<uuid>_<stamp>.tbz2.gpg | tar -xjf - -C <an empty scratch directory>"
    say "  A set is due 30 days after the last success; a drive connected sooner reads SKIPPED (none due)."
    say "  Retention is MANUAL: keep the last three full sets, and delete an older set (every archive bearing its"
    say "  UUID) only after a restore drill of the newest passes. Nothing prunes."
    say "  The monthly window: systemctl --user list-timers juniper-backup-full.timer"
fi
say "Never run juniper-backup-scheduled.bash with --dry-run by hand. It passes the flag to the runner, the"
say "preview exits 0, and the scheduler then stamps a success and writes result=OK with no archive written."
