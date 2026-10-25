#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-25_juniper_backup_tier3_mutation_check.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-10-25
# Last Modified: 2026-10-25
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       backup design §7.9 and D-5 (notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md);
#                util/ad-hoc/2026-10-03_juniper_backup_tier2_mutation_check.py (the tier-2 check this follows)
#
# Description:
#    Mutation check for tests/test_juniper_backup_tier3_lane.py: does the gate go RED when the tier-3 lane regresses in each of the
#    ways it exists to catch -- the backup-dir rule in the runner and in the scheduler (and the two drifting apart), the scheduler's
#    use of the lane's environment and its argument hand-off, the four full units (state directory, drive, directory, period,
#    staleness, label, content, failure routing, path and timer), and the installer's --lane?
#
#    Each mutation is applied to a COPY of the lane (runner, scheduler, reporter, installer, the eight units, both suites and their
#    helper) under a temp dir, and the tier-3 suite alone is run there with `python3 -m unittest`. The live tree is never edited, so
#    an interrupted run cannot leave a mutant behind. Every mutation must match its anchor exactly once (a mutation that does not
#    apply is a harness failure, not a survivor). The control (no mutation) must be green; every mutation must be red. The W
#    mutations replace a whole file with its text at BASE_SHA, the commit this change was built on: the suite must fail against the
#    scripts as they were, not only against targeted mutants of them.
#
#    A SECOND CONTROL runs the unmutated suite under GNU coreutils, as on CI's ubuntu runner, where this host has uutils: a shim
#    directory maps each /usr/bin/gnu<name> to its plain name, ahead of /usr/bin on the fixture's PATH (the fixture lives in the
#    tier-2 suite, which the tier-3 suite imports). Skipped, and said so, where GNU's tools are not installed under those names.
#
#    Usage:  python3 util/ad-hoc/2026-10-25_juniper_backup_tier3_mutation_check.py [--jobs N]
#    Exit 0 = both controls green (or the GNU one skipped) and every mutation red.
#####################################################################################################################################################################################################
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNNER = "util/juniper-backup.bash"
SCHEDULER = "util/juniper-backup-scheduled.bash"
REPORTER = "util/duplicati_backup_failure.bash"
INSTALLER = "util/install_juniper_backup_timer.bash"
SERVICE = "util/systemd/juniper-backup-full.service"
FAILURE = "util/systemd/juniper-backup-full-failure.service"
PATH_UNIT = "util/systemd/juniper-backup-full.path"
TIMER = "util/systemd/juniper-backup-full.timer"
SUITE = "tests/test_juniper_backup_tier3_lane.py"
FIXTURE_SUITE = "tests/test_juniper_backup_tier2_lane.py"
COPIED = [
    RUNNER,
    SCHEDULER,
    REPORTER,
    INSTALLER,
    "util/systemd/juniper-backup.timer",
    "util/systemd/juniper-backup.path",
    "util/systemd/juniper-backup.service",
    "util/systemd/juniper-backup-failure.service",
    TIMER,
    PATH_UNIT,
    SERVICE,
    FAILURE,
    SUITE,
    FIXTURE_SUITE,
    "tests/redacted_env.py",
]

DIR_RE = "local components_re='^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$'"
DOT_TEST = '"/${dir}/" != *"/./"* && '
DOTDOT_TEST = ' && "/${dir}/" != *"/../"* ]]'
FULL_UNITS = '        UNITS=( "juniper-backup-full.timer" "juniper-backup-full.path" "juniper-backup-full.service" "juniper-backup-full-failure.service" )'
TIER2_UNITS = '        UNITS=( "juniper-backup.timer" "juniper-backup.path" "juniper-backup.service" "juniper-backup-failure.service" )'
FULL_ENABLE = '        ENABLE_UNITS=( "juniper-backup-full.timer" "juniper-backup-full.path" )'
UNKNOWN_LANE = '    *) echo "unknown lane: ${LANE} (want usb or full)" >&2; exit 2 ;;'

# (id, file, old, new, what the mutation models)
MUTATIONS = [
    # --- the backup-dir rule, in the runner -------------------------------------------------------------------------------------------
    ("T01", RUNNER, DIR_RE, "local components_re='^[A-Za-z0-9._-]+$'", "the runner keeps the one-component rule: Juniper/Backups is refused"),
    ("T02", RUNNER, DOTDOT_TEST, " ]]", "the runner accepts a .. component: a walk off the drive"),
    ("T03", RUNNER, DOT_TEST, "", "the runner accepts a . component"),
    ("T04", RUNNER, DIR_RE, "local components_re='^/?[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$'", "the runner accepts a leading slash: an absolute directory"),
    ("T05", RUNNER, DIR_RE, "local components_re='^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]*)*$'", "the runner accepts an empty component: a trailing or doubled slash"),
    ("T06", RUNNER, '    is_backup_dir "${BACKUP_DIR}" || {', "    true || {", "the runner does not check JUNIPER_BACKUP_DIR at all"),
    # --- the backup-dir rule, in the scheduler ----------------------------------------------------------------------------------------
    ("T07", SCHEDULER, 'is_backup_dir "${BACKUP_DIR}" || {', "true || {", "the scheduler checks nothing (its 1.0.0 behaviour)"),
    ("T08", SCHEDULER, DIR_RE, "local components_re='^[A-Za-z0-9._-]+$'", "the scheduler's copy of the rule drifts from the runner's"),
    ("T09", SCHEDULER, 'write_status FAILED "malformed JUNIPER_BACKUP_DIR"; exit 2;', 'write_status SKIPPED "malformed JUNIPER_BACKUP_DIR"; exit 0;', "a malformed directory is a quiet SKIP, so OnFailure= never fires"),
    # --- the scheduler's use of the lane's environment and arguments -----------------------------------------------------------------
    ("T10", SCHEDULER, 'STATE_DIR="${JUNIPER_BACKUP_STATE_DIR:-${HOME}/.local/state/juniper-backup}"', 'STATE_DIR="${HOME}/.local/state/juniper-backup"', "the scheduler ignores the lane's state dir: both lanes share one lock, status and stamp set"),
    ("T11", SCHEDULER, '"${RUNNER}" "$@"', '"${RUNNER}"', "the scheduler drops its arguments: no label, and the default ten repos"),
    ("T12", SCHEDULER, 'PERIOD_DAYS="${JUNIPER_BACKUP_PERIOD_DAYS:-7}"', "PERIOD_DAYS=7", "the scheduler ignores the lane's period"),
    ("T13", SCHEDULER, 'STALE_DAYS="${JUNIPER_BACKUP_STALE_DAYS:-21}"', "STALE_DAYS=21", "the scheduler ignores the lane's staleness limit"),
    # --- the full service --------------------------------------------------------------------------------------------------------------
    ("T14", SERVICE, "JUNIPER_BACKUP_STATE_DIR=%h/.local/state/juniper-backup-full", "JUNIPER_BACKUP_STATE_DIR=%h/.local/state/juniper-backup", "tier 3 shares tier 2's state dir"),
    ("T15", SERVICE, "Environment=JUNIPER_BACKUP_STATE_DIR=%h/.local/state/juniper-backup-full\n", "", "tier 3 sets no state dir, so it takes tier 2's default"),
    ("T16", SERVICE, "JUNIPER_BACKUP_DEVICES=dee46823-4119-4914-ac15-08194ee27d81", "JUNIPER_BACKUP_DEVICES=EBC5-F0A3", "tier 3 writes a tier-2 stick"),
    ("T17", SERVICE, "JUNIPER_BACKUP_DEVICES=dee46823-4119-4914-ac15-08194ee27d81", "JUNIPER_BACKUP_DEVICES=/mnt/JuniperArchive", "tier 3 keeps the superseded §7.9 path, which the fstab deprecates and the scheduler cannot read"),
    ("T18", SERVICE, "JUNIPER_BACKUP_DIR=Juniper/Backups", "JUNIPER_BACKUP_DIR=Juniper-8.0.0.python", "tier 3 writes tier 2's directory, not the owner's Juniper/Backups"),
    ("T19", SERVICE, "JUNIPER_BACKUP_PERIOD_DAYS=30", "JUNIPER_BACKUP_PERIOD_DAYS=31", "the period is not monthly's 30"),
    ("T20", SERVICE, "JUNIPER_BACKUP_STALE_DAYS=45", "JUNIPER_BACKUP_STALE_DAYS=21", "tier 3 keeps tier 2's 21-day limit, under its own 30-day period"),
    ("T21", SERVICE, " --label full", "", "the set is not labelled full"),
    ("T22", SERVICE, ' util backups"', ' util"', "the parent-level backups directory is left out"),
    ("T23", SERVICE, " juniper-slacker juniper-legacy ", " juniper-slacker ", "juniper-legacy is left out (it is in no other tier)"),
    ("T24", SERVICE, "OnFailure=juniper-backup-full-failure.service", "OnFailure=juniper-backup-failure.service", "a tier-3 failure is reported as tier 2's"),
    ("T25", SERVICE, "Environment=JUNIPER_BACKUP_STALE_DAYS=45\n", "Environment=JUNIPER_BACKUP_STALE_DAYS=45\nEnvironment=JUNIPER_BACKUP_MEDIA_ROOT=/mnt\n", "the unit pins the superseded /mnt root"),
    # --- the failure, path and timer units ---------------------------------------------------------------------------------------------
    ("T26", FAILURE, "DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup-full", "DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup", "the failure record lands in tier 2's log"),
    ("T27", FAILURE, "duplicati-backup-failure.bash juniper-backup-full.service", "duplicati-backup-failure.bash juniper-backup.service", "the record names, tails and titles tier 2's unit"),
    ("T28", PATH_UNIT, "PathChanged=/run/media/pcalnon", "PathExists=/run/media/pcalnon", "PathExists=, which re-triggers after every run until the path unit fails"),
    ("T29", PATH_UNIT, "Unit=juniper-backup-full.service", "Unit=juniper-backup.service", "the path unit starts tier 2"),
    ("T30", TIMER, "Unit=juniper-backup-full.service", "Unit=juniper-backup.service", "the timer starts tier 2"),
    ("T31", TIMER, "OnCalendar=*-*-01 04:00:00", "OnCalendar=Sun *-*-* 03:00:00", "the timer is weekly, on tier 2's window"),
    ("T32", TIMER, "Persistent=true", "Persistent=false", "a window missed while the host is off is skipped"),
    # --- the installer ---------------------------------------------------------------------------------------------------------------------
    ("T33", INSTALLER, FULL_UNITS, TIER2_UNITS, "--lane full installs tier 2's units"),
    ("T34", INSTALLER, FULL_ENABLE, '        ENABLE_UNITS=( "juniper-backup.timer" "juniper-backup.path" )', "--lane full enables tier 2's units"),
    ("T35", INSTALLER, FULL_ENABLE, '        ENABLE_UNITS=( "juniper-backup-full.timer" )', "the full lane's path unit is never enabled: no run on connection"),
    ("T36", INSTALLER, UNKNOWN_LANE, '    *) STATE_DIR="${HOME}/.local/state/juniper-backup"\n' + TIER2_UNITS + '\n        ENABLE_UNITS=( "juniper-backup.timer" "juniper-backup.path" ) ;;', "an unknown lane installs tier 2 instead of refusing"),
    ("T37", INSTALLER, 'LANE="usb"', 'LANE="full"', "no --lane installs tier 3: the tier-2 install changes"),
    ("T38", INSTALLER, '--lane requires usb or full" >&2; exit 2; }', '--lane requires usb or full" >&2; exit 0; }', "a --lane with no value exits 0"),
    ("T39", INSTALLER, 'if [[ "${LANE}" == "usb" ]]; then', "if true; then", "--lane full prints tier 2's acceptance notes"),
    ("T40", INSTALLER, '    say "  2. Disconnect the drive only after last-run.status reads result=OK (offline discipline, design §7.9)."\n', "", "the notes lose the offline-discipline step"),
    ("T41", INSTALLER, "/run/media/${user_name}/dee46823-4119-4914-ac15-08194ee27d81 and hold Juniper/Backups/", "/mnt/JuniperArchive and hold Juniper-8.0.0.python/", "the notes name the superseded drive and directory"),
    ("T42", INSTALLER, "systemctl --user start --no-block juniper-backup-full.service", "systemctl --user start juniper-backup-full.service", "the hand start blocks the operator's shell for hours"),
    ("T43", INSTALLER, '    say "     If the drive was already mounted when you installed, no mount event comes at all (PathChanged= does"\n', "", "the notes lose the already-mounted case, whose first run nothing triggers"),
]

# Whole-file mutations: the file as it stood at BASE_SHA, origin/main when this change was built.
BASE_SHA = "3ebf068939fafc10c47caf6bab5d3fa7d0aea1fe"
WHOLE_FILE_MUTATIONS = [
    ("W1", RUNNER, BASE_SHA, "the runner before this change: one-component JUNIPER_BACKUP_DIR"),
    ("W2", SCHEDULER, BASE_SHA, "the scheduler before this change: no JUNIPER_BACKUP_DIR check at all"),
    ("W3", INSTALLER, BASE_SHA, "the installer before this change: no --lane"),
]

# Mutations the suite is KNOWN not to catch. Empty: a future deliberate survivor has to be named here with its reason.
EXPECTED_SURVIVORS: set[str] = set()


def stage(dest: Path) -> None:
    for rel in COPIED:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, target)


def run_suite(root: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=str(root), capture_output=True, text=True, timeout=1800)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode == 0, (tail[-1] if tail else "")


def gnu_shim(dest: Path) -> Path | None:
    """A directory mapping /usr/bin/gnu<name> -> <name>, or None when GNU coreutils are not installed that way."""
    gnu = sorted(p for p in Path("/usr/bin").glob("gnu*") if not p.name.startswith("gnuplot"))
    if not any(p.name == "gnuinstall" for p in gnu):
        return None
    dest.mkdir(parents=True)
    for tool in gnu:
        (dest / tool.name[len("gnu") :]).symlink_to(tool)
    # Not vacuous: the shim's install(1) must actually BE GNU's, or this control proves nothing about CI.
    version = subprocess.run([str(dest / "install"), "--version"], capture_output=True, text=True, timeout=60).stdout
    if "GNU coreutils" not in version:
        raise SystemExit(f"GNU control: {dest / 'install'} is not GNU coreutils: {version.splitlines()[:1]}")
    return dest


def put_on_path(root: Path, shim: Path) -> None:
    """Patch the COPIED fixture so every subprocess resolves coreutils from the shim first."""
    suite = root / FIXTURE_SUITE
    text = suite.read_text(encoding="utf-8")
    anchor = 'env["PATH"] = f"{self.stub_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"'
    if text.count(anchor) != 1:
        raise SystemExit(f"GNU control: PATH anchor matched {text.count(anchor)} times in {FIXTURE_SUITE}")
    suite.write_text(text.replace(anchor, anchor.replace("{os.pathsep}/usr/bin", "{os.pathsep}" + str(shim) + "{os.pathsep}/usr/bin")), encoding="utf-8")


def file_at(sha: str, rel: str) -> bytes:
    return subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=str(REPO), capture_output=True, check=True, timeout=60).stdout


def apply_one(tmp: Path, mutation: tuple[str, str, str, str, str]) -> tuple[str, str, bool | None, str]:
    """Stage, mutate and run one mutant: (id, what it models, green or None when the anchor did not apply, the suite's last line)."""
    mid, rel, old, new, models = mutation
    root = tmp / mid
    stage(root)
    path = root / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        return mid, models, None, f"NOT APPLIED ({count} anchor matches in {rel})"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    green, summary = run_suite(root)
    return mid, models, green, summary


def apply_whole(tmp: Path, mutation: tuple[str, str, str, str]) -> tuple[str, str, bool | None, str]:
    mid, rel, sha, models = mutation
    root = tmp / mid
    stage(root)
    (root / rel).write_bytes(file_at(sha, rel))
    green, summary = run_suite(root)
    return mid, models, green, summary


def report(mid: str, models: str, green: bool | None, summary: str) -> int:
    """Print one mutation's verdict; return 1 if it is a problem (an unapplied anchor or an unexpected survivor)."""
    if green is None:
        print(f"{mid}  {summary}  {models}")
        return 1
    if green:
        verdict = "SURVIVED (expected)" if mid in EXPECTED_SURVIVORS else "SURVIVED"
        problem = 0 if mid in EXPECTED_SURVIVORS else 1
    else:
        verdict, problem = "killed", 0
    print(f"{mid}  {verdict:<19}  {summary:<40}  {models}")
    return problem


def main() -> int:
    parser = argparse.ArgumentParser(description="Mutation check for tests/test_juniper_backup_tier3_lane.py")
    parser.add_argument("--jobs", type=int, default=4, help="mutants run in parallel (default 4)")
    args = parser.parse_args()
    failures = 0
    with tempfile.TemporaryDirectory(prefix="t3-mutation-") as tmp_name:
        tmp = Path(tmp_name)
        control = tmp / "control"
        stage(control)
        green, summary = run_suite(control)
        print(f"CONTROL  {'GREEN' if green else 'RED  '}  {summary}")
        if not green:
            print("control is red: the suite fails on the unmutated lane, so no mutation result means anything")
            return 1
        shim = gnu_shim(tmp / "gnu-shim")
        if shim is None:
            print("CONTROL  skipped (no /usr/bin/gnuinstall: GNU coreutils not installed under gnu* names)")
        else:
            gnu_control = tmp / "control-gnu"
            stage(gnu_control)
            put_on_path(gnu_control, shim)
            green, summary = run_suite(gnu_control)
            print(f"CONTROL  {'GREEN' if green else 'RED  '}  {summary}  (GNU coreutils, as on CI)")
            if not green:
                print("GNU control is red: the suite fails under CI's coreutils")
                return 1
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            whole = [pool.submit(apply_whole, tmp, m) for m in WHOLE_FILE_MUTATIONS]
            targeted = [pool.submit(apply_one, tmp, m) for m in MUTATIONS]
            for future in [*whole, *targeted]:
                failures += report(*future.result())
    print(f"\n{len(WHOLE_FILE_MUTATIONS) + len(MUTATIONS)} mutation(s); {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
