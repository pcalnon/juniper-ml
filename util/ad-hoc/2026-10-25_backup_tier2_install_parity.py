"""
Show that the installer's default lane is the tier-2 install of BASE_SHA: same output, same systemctl calls, same installed tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — investigation (the tier-3 lane's "existing tier-2 behaviour must not change" constraint)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/install_juniper_backup_timer.bash 1.1.0 (--lane); tests/test_juniper_backup_tier3_lane.py;
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.9

What it does: stages the lane with tests/test_juniper_backup_tier2_lane.py's fixture (scratch HOME, PATH stubs for
systemctl and loginctl, nothing real touched), then runs the installer twice from that one staged util/ directory --
once as it stood at BASE_SHA (`git show`), once as the checkout has it -- with no --lane, in --dry-run and in a real
run, and with --lane usb. Both copies install the same staged scripts and units, so any difference is the installer's.
The scratch path is replaced by <tmp> before comparing. Stdout, stderr, the exit code, the systemctl calls and the
installed tree (type, mode and sha256 of every entry) must match.

Usage:
    python3 util/ad-hoc/2026-10-25_backup_tier2_install_parity.py [--base SHA]

Exit 0 = every comparison identical; 1 = a difference (printed as a unified diff).
"""

import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALLER_REL = "util/install_juniper_backup_timer.bash"
RUNNER_REL = "util/juniper-backup.bash"
BASE_SHA = "3ebf068939fafc10c47caf6bab5d3fa7d0aea1fe"

sys.path.insert(0, str(REPO))
from tests.test_juniper_backup_tier2_lane import _snapshot, _Tier2Fixture  # noqa: E402


def observe(installer_text: bytes | None, args: list[str]) -> dict[str, list[str]]:
    """Run one installer copy in a fresh fixture: what it printed, what it called and what it left behind."""
    with tempfile.TemporaryDirectory() as tmp:
        fx = _Tier2Fixture(tmp)
        # The fixture's staged runner carries ITS OWN temp path in DRIVE_PARENTS, so its bytes differ between any two
        # fixtures; this comparison is about the installer, so it installs the repository's unmodified runner instead.
        (fx.stage / RUNNER_REL).write_bytes((REPO / RUNNER_REL).read_bytes())
        installer = fx.stage / INSTALLER_REL
        if installer_text is not None:
            installer.write_bytes(installer_text)
        result = fx.run(["bash", str(installer), *args])
        calls = fx.systemctl_log.read_text(encoding="utf-8").splitlines() if fx.systemctl_log.exists() else []
        return {
            "rc": [str(result.returncode)],
            "stdout": result.stdout.replace(tmp, "<tmp>").splitlines(),
            "stderr": result.stderr.replace(tmp, "<tmp>").splitlines(),
            "systemctl": calls,
            "tree": [line.replace(tmp, "<tmp>") for line in _snapshot(fx.home)],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="the installer's default lane against the tier-2 install of a base commit")
    parser.add_argument("--base", default=BASE_SHA)
    args = parser.parse_args()
    base_text = subprocess.run(["git", "show", f"{args.base}:{INSTALLER_REL}"], cwd=str(REPO), capture_output=True, check=True, timeout=60).stdout
    problems = 0
    for label, base_args, new_args in (
        ("no --lane, real run", [], []),
        ("no --lane, --dry-run", ["--dry-run"], ["--dry-run"]),
        ("--lane usb, real run", [], ["--lane", "usb"]),
        ("--lane usb, --dry-run", ["--dry-run"], ["--lane", "usb", "--dry-run"]),
    ):
        base = observe(base_text, base_args)
        new = observe(None, new_args)
        differing = [key for key in base if base[key] != new[key]]
        summary = f"{len(new['stdout'])} stdout line(s), {len(new['tree'])} installed entr(ies), systemctl {new['systemctl']}"
        print(f"{'IDENTICAL' if not differing else 'DIFFERS  '}  {label:<24} {summary}")
        for key in differing:
            problems += 1
            for line in difflib.unified_diff(base[key], new[key], f"base:{key}", f"new:{key}", lineterm="", n=1):
                print(f"    {line}")
    print(f"\n{problems} difference(s) against {args.base[:8]}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
