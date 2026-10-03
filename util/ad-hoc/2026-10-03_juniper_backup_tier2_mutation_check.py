#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-03_juniper_backup_tier2_mutation_check.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-10-03
# Last Modified: 2026-10-03
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       recovery plan B6 / I-20 (notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md)
#
# Description:
#    Mutation check for tests/test_juniper_backup_tier2_lane.py: does the gate go RED when the tier-2 lane regresses in each of the
#    ways it exists to catch -- the runner's mount root, the absolute device form, the mount guard, the drive bound (DRIVE_PARENTS),
#    --dry-run, the installer's refusals, copies and acceptance notes, the failure unit's routing and the notification's title?
#    M23-M29 were added for the review of PR #2114 (validation lane PB, 2026-10-03): each models one finding it raised.
#
#    Each mutation is applied to a COPY of the lane (runner, scheduler, reporter, installer, the four units, the suite and its
#    helper) under a temp dir, and the suite is run there with `python3 -m unittest`. The live tree is never edited, so an
#    interrupted run cannot leave a mutant behind. Every mutation must match its anchor exactly once (a mutation that does not
#    apply is a harness failure, not a survivor). The control (no mutation) must be green; every mutation must be red.
#
#    A SECOND CONTROL runs the unmutated suite under GNU coreutils. This host's coreutils are uutils (Rust), while CI's
#    ubuntu-latest runner has GNU, and the lane leans on install(1), stat(1), du(1), df(1) and date(1). Where GNU's tools are
#    present as /usr/bin/gnu<name> (Ubuntu's coreutils-from-gnu layout), a shim directory maps each to its plain name and
#    the copied suite's PATH puts it ahead of /usr/bin. Where they are not present, that control is reported as skipped.
#
#    Usage:  python3 util/ad-hoc/2026-10-03_juniper_backup_tier2_mutation_check.py
#    Exit 0 = both controls green (or the GNU one skipped) and every mutation red.
#####################################################################################################################################################################################################
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNNER = "util/juniper-backup.bash"
SCHEDULER = "util/juniper-backup-scheduled.bash"
REPORTER = "util/duplicati_backup_failure.bash"
INSTALLER = "util/install_juniper_backup_timer.bash"
FAILURE_UNIT = "util/systemd/juniper-backup-failure.service"
SUITE = "tests/test_juniper_backup_tier2_lane.py"
COPIED = [
    RUNNER,
    SCHEDULER,
    REPORTER,
    INSTALLER,
    "util/systemd/juniper-backup.timer",
    "util/systemd/juniper-backup.path",
    "util/systemd/juniper-backup.service",
    FAILURE_UNIT,
    SUITE,
    "tests/redacted_env.py",
]

# (id, file, old, new, what the mutation models)
MUTATIONS = [
    ("M01", RUNNER, "/run/media/${USER:-$(id -un)}}", "/media/pcalnon}", "the runner's default root reverts to the retired /media/pcalnon (the 2026-09-07 regression)"),
    ("M02", RUNNER, '"${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER:-$(id -un)}}"', '"/run/media/${USER:-$(id -un)}"', "the runner ignores the root the scheduler reads"),
    ("M03", RUNNER, 'read -r -a MEDIA_NAMES <<< "${JUNIPER_BACKUP_DEVICES:-EBC5-F0A3 DFF3-2782}"', 'MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )', "the runner ignores the device list the scheduler reads"),
    ("M04", RUNNER, '    if [[ "${media_name}" == /* ]]; then\n        printf', "    if false; then\n        printf", "an absolute entry is prefixed with the root instead of used as-is"),
    ("M05", RUNNER, '    if ! mountpoint -q "${mount_root}" 2>/dev/null; then', '    if [[ "${media_name}" != /* ]] && ! mountpoint -q "${mount_root}" 2>/dev/null; then', "an absolute entry bypasses the mount guard"),
    ("M06", RUNNER, 'if [[ -z "${DEST_OVERRIDE}" ]]; then\n    [[ "${MEDIA_ROOT}" == /* ]]', 'if false; then\n    [[ "${MEDIA_ROOT}" == /* ]]', "the environment's path values are not validated"),
    ("M07", RUNNER, 'if [[ -z "${DEST_OVERRIDE}" ]]; then\n    [[ "${MEDIA_ROOT}" == /* ]]', 'if true; then\n    [[ "${MEDIA_ROOT}" == /* ]]', "a malformed device list blocks a --dest run that never reads it"),
    ("M08", RUNNER, "/run/media/${USER:-$(id -un)}}", "/run/media/${USER}}", "a hand run with USER unset dies on set -u"),
    ("M09", RUNNER, '    echo "[dry-run] no archives were written."\n    exit 0', '    echo "[dry-run] no archives were written."', "--dry-run falls through into the build"),
    ("M10", INSTALLER, "    if (( DRY_RUN )); then\n        printf '[dry-run] would run:'", "    if false; then\n        printf '[dry-run] would run:'", "--dry-run executes every action"),
    ("M11", INSTALLER, "if (( uid == 0 )); then", "if false; then", "the installer runs as root"),
    ("M12", INSTALLER, 'if [[ "${linger}" != "yes" ]]; then', "if false; then", "Linger is not checked"),
    ("M13", INSTALLER, '    act install -m 0755 "${src}" "${dst}"', '    act cp -- "${src}" "${dst}"', "cp, which writes through a symlink into a checkout and keeps the source mode"),
    ("M14", INSTALLER, 'act systemctl --user enable --now "${ENABLE_UNITS[@]}"', ":", "nothing is enabled"),
    ("M15", INSTALLER, 'ENABLE_UNITS=( "juniper-backup.timer" "juniper-backup.path" )', 'ENABLE_UNITS=( "juniper-backup.timer" )', "the path unit is not enabled"),
    ("M16", INSTALLER, ' "juniper-backup.service" "juniper-backup-failure.service" )', ' "juniper-backup.service" )', "the failure unit is not installed"),
    ("M17", INSTALLER, ' "duplicati_backup_failure.bash" )', " )", "the reporter is not installed"),
    ("M18", INSTALLER, '    if [[ -d "${dir}" ]]; then\n        say "    ${dir} exists"', '    if false; then\n        say "    ${dir} exists"', "an existing directory is re-moded by install -d -m"),
    ("M19", FAILURE_UNIT, "Environment=DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup\n", "", "the failure unit writes into the Duplicati lane's state dir"),
    ("M20", FAILURE_UNIT, "duplicati-backup-failure.bash juniper-backup.service", "duplicati-backup-failure.bash duplicati-backup.service", "the record names (and tails) the wrong unit"),
    ("M21", FAILURE_UNIT, "%h/.local/state/juniper-backup", "%h/.local/state/duplicati", "the state dir points at the other lane"),
    ("M22", SCHEDULER, '"${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}"', '"${JUNIPER_BACKUP_MEDIA_ROOT:-/media/${USER}}"', "the scheduler's root drifts away from the runner's"),
    ("M23", RUNNER, '        is_drive_mount_root "${_mount_root}" || {', "        true || {", "no drive bound: a mounted system path (/, /home, /run/user/<uid>) is a destination"),
    ("M24", RUNNER, '        is_drive_mount_root "${_mount_root}" || {', '        [[ "${_media}" != /* ]] || is_drive_mount_root "${_mount_root}" || {', "the bound covers absolute entries only, not the relative form through a root"),
    ("M25", RUNNER, ' && "${rest}/" != *"/../"* ]]', " ]]", "a walk out of the bound (/mnt/../home) is accepted"),
    ("M26", RUNNER, "[[ \"${JUNIPER_BACKUP_DEVICES-}\" != *$'\\n'* ]] ||", "true ||", "a newline in the device list is read past, silently dropping every device after it"),
    ("M27", REPORTER, '"Backup FAILED: ${UNIT}"', '"Duplicati backup FAILED"', "a tier-2 failure is announced as the Duplicati lane's"),
    ("M28", INSTALLER, '    say "[dry-run] nothing was written. What follows applies after a real run."', '    say "[dry-run] nothing was written. What follows applies after a real run."\n    exit 0', "the dry run exits before the acceptance notes"),
    ("M29", INSTALLER, "Do the OK run FIRST, with BOTH configured sticks mounted (by default EBC5-F0A3 and DFF3-2782). One", "Do the OK run FIRST: mount a stick. One", "the acceptance note goes back to 'mount a stick', which is rc 4 -> FAILED"),
]

# Whole-file mutations: the file as it stood at a pinned commit. M00 is the runner this change replaces (the branch's base,
# origin/main on 2026-10-03), which forced /media/pcalnon/<name> -- the suite must fail against the real regression, not only
# against a targeted mutant of it.
BASE_SHA = "79dc36d5a3b86b436beddc567a565ddf427de3e7"
WHOLE_FILE_MUTATIONS = [
    ("M00", RUNNER, BASE_SHA, "the runner exactly as it was before this change (hard-coded /media/pcalnon, no shared settings)"),
]

# Mutations the suite is KNOWN not to catch. Empty: nothing is expected to survive, and a future deliberate survivor has to be
# named here with its reason.
EXPECTED_SURVIVORS: set[str] = set()


def stage(dest: Path) -> None:
    for rel in COPIED:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, target)


def run_suite(root: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=str(root), capture_output=True, text=True, timeout=900)
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
    """Patch the COPIED suite so every subprocess resolves coreutils from the shim first."""
    suite = root / SUITE
    text = suite.read_text(encoding="utf-8")
    anchor = 'env["PATH"] = f"{self.stub_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"'
    if text.count(anchor) != 1:
        raise SystemExit(f"GNU control: PATH anchor matched {text.count(anchor)} times in {SUITE}")
    suite.write_text(text.replace(anchor, anchor.replace("{os.pathsep}/usr/bin", "{os.pathsep}" + str(shim) + "{os.pathsep}/usr/bin")), encoding="utf-8")


def file_at(sha: str, rel: str) -> bytes:
    return subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=str(REPO), capture_output=True, check=True, timeout=60).stdout


def report(mid: str, green: bool, summary: str, models: str) -> int:
    """Print one mutation's verdict; return 1 if it is a problem (an unexpected survivor)."""
    problem = 0
    if green:
        verdict = "SURVIVED (expected)" if mid in EXPECTED_SURVIVORS else "SURVIVED"
        problem = 0 if mid in EXPECTED_SURVIVORS else 1
    else:
        verdict = "killed"
    print(f"{mid}  {verdict:<19}  {summary:<40}  {models}")
    return problem


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="b6-mutation-") as tmp:
        control = Path(tmp) / "control"
        stage(control)
        green, summary = run_suite(control)
        print(f"CONTROL  {'GREEN' if green else 'RED  '}  {summary}")
        if not green:
            print("control is red: the suite fails on the unmutated lane, so no mutation result means anything")
            return 1
        shim = gnu_shim(Path(tmp) / "gnu-shim")
        if shim is None:
            print("CONTROL  skipped (no /usr/bin/gnuinstall: GNU coreutils not installed under gnu* names)")
        else:
            gnu_control = Path(tmp) / "control-gnu"
            stage(gnu_control)
            put_on_path(gnu_control, shim)
            green, summary = run_suite(gnu_control)
            print(f"CONTROL  {'GREEN' if green else 'RED  '}  {summary}  (GNU coreutils, as on CI)")
            if not green:
                print("GNU control is red: the suite fails under CI's coreutils")
                return 1
        for mid, rel, sha, models in WHOLE_FILE_MUTATIONS:
            root = Path(tmp) / mid
            stage(root)
            (root / rel).write_bytes(file_at(sha, rel))
            green, summary = run_suite(root)
            failures += report(mid, green, summary, models)
        for mid, rel, old, new, models in MUTATIONS:
            root = Path(tmp) / mid
            stage(root)
            path = root / rel
            text = path.read_text(encoding="utf-8")
            count = text.count(old)
            if count != 1:
                print(f"{mid}  NOT APPLIED ({count} anchor matches in {rel})  {models}")
                failures += 1
                continue
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            green, summary = run_suite(root)
            failures += report(mid, green, summary, models)
    print(f"\n{len(WHOLE_FILE_MUTATIONS) + len(MUTATIONS)} mutation(s); {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
