#!/usr/bin/env bash
# Read-only probe: on THIS host, do the scheduler and the runner resolve tier 3's drive and directory from juniper-backup-full.service's own settings?
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon (authored via Claude Code)
# Created:     2026-10-25
# Status:      ad-hoc — investigation (the tier-3 lane, owner ruling D-5 on §7.9 of the backup design)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.9;
#              util/systemd/juniper-backup-full.service; tests/test_juniper_backup_tier3_lane.py (the hermetic half)
#
# WHAT IT ANSWERS
#     The suite proves the lane against scratch drives. This asks the host: with the unit's Environment= and ExecStart=
#     arguments exactly as written, and the default JUNIPER_BACKUP_MEDIA_ROOT, does the CHECKOUT's scheduler judge the real
#     drive mounted, usable and due, and does the checkout's runner, under --dry-run, name <drive>/Juniper/Backups as its
#     build target? Nothing is installed and no unit is started.
#
# SAFETY
#     - The runner always gets --dry-run, which exits before its build loop and writes nothing.
#     - JUNIPER_BACKUP_STATE_DIR is a scratch directory (the scheduler stamps a dry run's exit 0 as a success, which is
#       why this must never point at ~/.local/state/juniper-backup-full).
#     - gpg is a PATH stub that answers --list-keys and refuses anything else, so no keyring is read.
#     - The drive is only probed: mountpoint(1), test -d / -w (access(2)) and df(1). Its target directory's listing and
#       mtime are compared before and after, and a difference fails the probe.
#     - --source is a scratch tree holding the fifteen entry names, unless --real-source is given; the real tree is then
#       only read, by du(1), to report what a full set would archive (slow: every entry is sized).
#
# USAGE
#     bash util/ad-hoc/2026-10-25_backup_tier3_host_resolution_probe.bash [--real-source]
#     Exit 0 = resolved, due, previewed and nothing on the drive changed; 1 = any of those failed; 2 = misuse.
set -euo pipefail

REAL_SOURCE=0
case "${1:-}" in
    "") ;;
    --real-source) REAL_SOURCE=1 ;;
    *) echo "usage: $0 [--real-source]" >&2; exit 2 ;;
esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT="${REPO}/util/systemd/juniper-backup-full.service"
WORK="$(mktemp -d -t juniper-tier3-probe-XXXXXXXX)"
trap 'rm -rf "${WORK}"' EXIT

# The unit's Environment= lines, %h expanded, one unquoted NAME=VALUE each (the suite pins that shape).
declare -A UNIT_ENV=()
while IFS= read -r line; do
    assignment="${line#Environment=}"
    UNIT_ENV["${assignment%%=*}"]="${assignment#*=}"
done < <(grep '^Environment=' "${UNIT}" | sed "s|%h|${HOME}|g")
device="${UNIT_ENV[JUNIPER_BACKUP_DEVICES]}"
backup_dir="${UNIT_ENV[JUNIPER_BACKUP_DIR]}"
# The ExecStart= arguments after the scheduler path: --label full --repos "<entries>".
exec_line="$(sed -n 's/^ExecStart=//p' "${UNIT}")"
label="$(sed -n 's/.*--label \([^ ]*\) .*/\1/p' <<< "${exec_line}")"
repos="$(sed -n 's/.*--repos "\([^"]*\)".*/\1/p' <<< "${exec_line}")"
[[ -n "${device}" && -n "${backup_dir}" && -n "${label}" && -n "${repos}" ]] || { echo "FAIL: could not read the unit's settings from ${UNIT}" >&2; exit 1; }

media_root="/run/media/${USER:-$(id -un)}"   # the default both scripts use; the unit sets none
target="${media_root}/${device}/${backup_dir}"
echo "unit:    ${UNIT}"
echo "device:  ${device}    dir: ${backup_dir}    label: ${label}"
echo "entries: ${repos}"
echo "target:  ${target}"

mkdir -p "${WORK}/stubs" "${WORK}/state" "${WORK}/source"
cat > "${WORK}/stubs/gpg" <<'STUB'
#!/usr/bin/env bash
[[ "${1:-}" == "--list-keys" ]] && exit 0
echo "gpg stub: refused: $*" >&2
exit 97
STUB
chmod 0755 "${WORK}/stubs/gpg"
if (( REAL_SOURCE )); then
    source_dir="${HOME}/Development/python/Juniper"
else
    source_dir="${WORK}/source"
    read -r -a entries <<< "${repos}"
    for entry in "${entries[@]}"; do mkdir -p "${source_dir}/${entry}"; printf 'probe\n' > "${source_dir}/${entry}/probe.txt"; done
fi
echo "source:  ${source_dir}"

before="$(stat -c '%Y %a %U:%G' "${target}" 2>&1; ls -A "${target}" 2>&1)"
set +e
PATH="${WORK}/stubs:${PATH}" \
    JUNIPER_BACKUP_RUNNER="${REPO}/util/juniper-backup.bash" \
    JUNIPER_BACKUP_STATE_DIR="${WORK}/state" \
    JUNIPER_BACKUP_DEVICES="${device}" \
    JUNIPER_BACKUP_DIR="${backup_dir}" \
    JUNIPER_BACKUP_PERIOD_DAYS="${UNIT_ENV[JUNIPER_BACKUP_PERIOD_DAYS]}" \
    JUNIPER_BACKUP_STALE_DAYS="${UNIT_ENV[JUNIPER_BACKUP_STALE_DAYS]}" \
    bash "${REPO}/util/juniper-backup-scheduled.bash" --label "${label}" --repos "${repos}" --dry-run --source "${source_dir}" > "${WORK}/out.txt" 2>&1
rc=$?
set -e
after="$(stat -c '%Y %a %U:%G' "${target}" 2>&1; ls -A "${target}" 2>&1)"

grep -E '^[0-9T:+-]+ (running|SKIPPED|FAILED|OK|WARN|FATAL)|OK   |SKIP |would archive|build  ->|no archives were written|free: ' "${WORK}/out.txt" | sed 's/^/    /' | head -60
failures=0
# check <description> <command...>: run the command, PASS on exit 0. No eval: every argument is a word as written.
check() {
    local description="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "PASS  ${description}"
    else
        echo "FAIL  ${description}"
        failures=$(( failures + 1 ))
    fi
}
check "the scheduler exited 0 (rc ${rc})" test "${rc}" -eq 0
check "the scheduler judged ${device} mounted and due" grep -q "mounted=${device} due=${device}" "${WORK}/out.txt"
check "the runner found the device usable" grep -q "  OK   ${device}" "${WORK}/out.txt"
check "the runner's build target is ${target}" grep -q "build  -> ${target}/Juniper_${label}_" "${WORK}/out.txt"
check "the runner wrote nothing" grep -q "no archives were written" "${WORK}/out.txt"
check "the drive's target directory is unchanged" test "${before}" = "${after}"
echo
if (( failures )); then
    echo "RESULT: ${failures} check(s) failed; full output follows" >&2
    cat "${WORK}/out.txt" >&2
    exit 1
fi
echo "RESULT: the unit's settings resolve ${target} for the scheduler and the runner on this host; nothing was written."
