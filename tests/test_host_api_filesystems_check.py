#!/usr/bin/env python3
"""
Regression suite for util/host_api_filesystems_check.py.

Project: juniper-ml
Author: Paul Calnon
Created: 2026-11-07
Related: notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md

The failure class it pins: on 2026-10-27 yamaguchi lost securityfs, pstore and bpffs to a root
``umount -a``-like event. A repair scoped by ``systemctl``'s unit list put back only the mounts that
have unit files, because PID 1's own API mounts leave no unit behind once unmounted. The check
must read the mount table, so the INCIDENT FIXTURE below is yamaguchi's real /proc/self/mountinfo
lines, captured 2026-11-08 (reports/2026-11-07_yamaguchi-securityfs-unmount/).

Hermetic: every case but the live smoke judges a fixture mountinfo against a temporary fake root.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Overridable only so util/ad-hoc/2026-11-07_host_api_fs_check_mutation_check.py can run this suite on mutants.
SCRIPT = Path(os.environ.get("HOST_API_FS_CHECK_SCRIPT", str(REPO / "util" / "host_api_filesystems_check.py")))
PINS = REPO / "reports" / "2026-11-07_yamaguchi-securityfs-unmount" / "2026-11-08T0110Z_upstream-source-pins.txt"


def _load():
    spec = importlib.util.spec_from_file_location("host_api_filesystems_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(module)
    return module


CHECK = _load()

# yamaguchi, 2026-11-08 (incident state): /sys keeps sysfs and cgroup2; securityfs, pstore and bpf are gone;
# the six unit-file mounts carry the high mount ids of their 2026-10-28 remount.
INCIDENT_LINES = """\
28 33 0:25 / /sys rw,nosuid,nodev,noexec,relatime shared:6 - sysfs sysfs rw
29 33 0:26 / /proc rw,nosuid,nodev,noexec,relatime shared:11 - proc proc rw
30 33 0:7 / /dev rw,nosuid,relatime shared:2 - devtmpfs udev rw,size=48299920k,nr_inodes=12074980,mode=755,inode64
31 30 0:27 / /dev/pts rw,nosuid,noexec,relatime shared:3 - devpts devpts rw,gid=5,mode=600,ptmxmode=000
32 33 0:28 / /run rw,nosuid,nodev,noexec,relatime shared:5 - tmpfs tmpfs rw,size=9670088k,mode=755,inode64
33 2 259:5 / / rw,relatime shared:1 - ext4 /dev/nvme0n1p5 rw
35 30 0:29 / /dev/shm rw,nosuid,nodev shared:4 - tmpfs tmpfs rw,inode64,usrquota
36 28 0:30 / /sys/fs/cgroup rw,nosuid,nodev,noexec,relatime shared:8 - cgroup2 cgroup2 rw,nsdelegate,memory_recursiveprot,memory_hugetlb_accounting
14679 28 0:14 / /sys/kernel/tracing rw,nosuid,nodev,noexec,relatime shared:8172 - tracefs tracefs rw
14709 28 0:9 / /sys/kernel/debug rw,nosuid,nodev,noexec,relatime shared:8191 - debugfs debugfs rw
14739 28 0:21 / /sys/kernel/config rw,nosuid,nodev,noexec,relatime shared:8210 - configfs configfs rw
14769 28 0:36 / /sys/fs/fuse/connections rw,nosuid,nodev,noexec,relatime shared:8229 - fusectl fusectl rw
14799 30 0:72 / /dev/hugepages rw,nosuid,nodev,relatime shared:8248 - hugetlbfs hugetlbfs rw,pagesize=2M
14825 30 0:23 / /dev/mqueue rw,nosuid,nodev,noexec,relatime shared:8263 - mqueue mqueue rw
"""

# The three PID 1 mounts as a boot would have them (ids are illustrative; the check does not read them).
RESTORED_LINES = """\
40 28 0:8 / /sys/kernel/security rw,nosuid,nodev,noexec,relatime shared:7 - securityfs securityfs rw
41 28 0:31 / /sys/fs/pstore rw,nosuid,nodev,noexec,relatime shared:9 - pstore pstore rw
42 28 0:32 / /sys/fs/bpf rw,nosuid,nodev,noexec,relatime shared:10 - bpf bpf rw,mode=700
"""

HEALTHY_LINES = INCIDENT_LINES + RESTORED_LINES

# yamaguchi's applicable mount points (it boots BIOS, so no /sys/firmware/efi).
YAMAGUCHI_DIRS = (
    "sys/kernel/security",
    "sys/fs/cgroup",
    "sys/fs/pstore",
    "sys/fs/bpf",
    "sys/kernel/debug",
    "sys/kernel/tracing",
    "sys/kernel/config",
    "sys/fs/fuse/connections",
    "dev/hugepages",
    "dev/mqueue",
)


class FakeHost:
    """A temporary root with the directories, module parameter and (optionally) AppArmor interface."""

    def __init__(self, testcase: unittest.TestCase, *, dirs=YAMAGUCHI_DIRS, apparmor_enabled: str | None = "Y\n", interface: bool = True, efi: bool = False):
        self._tmp = tempfile.TemporaryDirectory()
        testcase.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        for rel in dirs:
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        if efi:
            (self.root / "sys/firmware/efi").mkdir(parents=True, exist_ok=True)
        if apparmor_enabled is not None:
            param = self.root / "sys/module/apparmor/parameters/enabled"
            param.parent.mkdir(parents=True, exist_ok=True)
            param.write_text(apparmor_enabled, encoding="ascii")
        if interface:
            profiles = self.root / "sys/kernel/security/apparmor/profiles"
            profiles.parent.mkdir(parents=True, exist_ok=True)
            profiles.write_text("docker-default (enforce)\n", encoding="ascii")

    def mountinfo(self, text: str) -> Path:
        path = self.root / "mountinfo"
        path.write_text(text, encoding="utf-8")
        return path

    def judge(self, text: str):
        return CHECK.judge(CHECK.parse_mountinfo(text), self.root)


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60, check=False)


def states(report) -> dict[str, str]:
    return {entry.fstype: entry.state for entry in report.entries}


class HealthyAndIncidentTest(unittest.TestCase):
    def test_healthy_host_passes(self):
        host = FakeHost(self)
        report = host.judge(HEALTHY_LINES)
        self.assertTrue(report.host_ok, CHECK.render(report))
        self.assertEqual(report.problems, 0)
        expected = dict.fromkeys(("securityfs", "cgroup2", "pstore", "bpf", "debugfs", "tracefs", "configfs", "fusectl", "hugetlbfs", "mqueue"), "MOUNTED")
        expected["efivarfs"] = "N/A"
        self.assertEqual(states(report), expected)
        self.assertTrue(report.apparmor["consistent"])
        self.assertNotIn("Remedy", CHECK.render(report))

    def test_incident_fails_on_exactly_the_three_pid1_mounts_and_apparmor(self):
        host = FakeHost(self, interface=False)  # securityfs gone => the AppArmor interface file is gone too
        report = host.judge(INCIDENT_LINES)
        self.assertFalse(report.host_ok)
        missing = sorted(entry.fstype for entry in report.entries if entry.state == "MISSING")
        self.assertEqual(missing, ["bpf", "pstore", "securityfs"])
        self.assertFalse(report.apparmor["consistent"])
        self.assertIn("Could not check if docker-default AppArmor profile was loaded", report.apparmor["consequence"])
        self.assertIn("aa_is_enabled() failed unexpectedly", report.apparmor["consequence"])
        self.assertEqual(report.problems, 4)

    def test_incident_remedies_use_systemds_own_mount_options(self):
        host = FakeHost(self, interface=False)
        remedies = {entry.fstype: entry.remedy for entry in host.judge(INCIDENT_LINES).entries if entry.remedy}
        self.assertEqual(
            remedies,
            {
                "securityfs": "sudo mount -t securityfs -o nosuid,nodev,noexec securityfs /sys/kernel/security",
                "pstore": "sudo mount -t pstore -o nosuid,nodev,noexec pstore /sys/fs/pstore",
                "bpf": "sudo mount -t bpf -o nosuid,nodev,noexec,mode=0700 bpf /sys/fs/bpf",
            },
        )

    def test_incident_cli_exit_1_and_text(self):
        host = FakeHost(self, interface=False)
        result = run_cli("--mountinfo", str(host.mountinfo(INCIDENT_LINES)), "--root", str(host.root))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("/sys/kernel/security         securityfs  pid1   MISSING", result.stdout)
        self.assertIn("INCONSISTENT", result.stdout)
        self.assertIn("no unit file", result.stdout)
        self.assertIn("host_api_filesystems_check: 4 problem(s)", result.stdout)

    def test_healthy_cli_exit_0(self):
        host = FakeHost(self)
        result = run_cli("--mountinfo", str(host.mountinfo(HEALTHY_LINES)), "--root", str(host.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("host_api_filesystems_check: OK", result.stdout)

    def test_systemctl_visible_repair_alone_is_not_enough(self):
        """The 2026-10-27 repair (snapd.mounts.target + the six unit-file mounts) leaves the host failing."""
        host = FakeHost(self, interface=False)
        report = host.judge(INCIDENT_LINES)  # the six unit-file mounts ARE present in this fixture
        unit_rows = {entry.fstype: entry.state for entry in report.entries if entry.origin == "unit"}
        self.assertEqual(set(unit_rows.values()), {"MOUNTED"})
        self.assertFalse(report.host_ok)


class ApplicabilityTest(unittest.TestCase):
    def test_unit_file_mount_missing_suggests_systemctl_start(self):
        host = FakeHost(self)
        text = "".join(line + "\n" for line in HEALTHY_LINES.splitlines() if " /sys/kernel/debug " not in line)
        report = host.judge(text)
        entry = next(entry for entry in report.entries if entry.fstype == "debugfs")
        self.assertEqual(entry.state, "MISSING")
        self.assertEqual(entry.remedy, "sudo systemctl start sys-kernel-debug.mount")
        self.assertEqual(report.problems, 1)

    def test_efi_boot_expects_efivarfs(self):
        host = FakeHost(self, efi=True)
        report = host.judge(HEALTHY_LINES)
        entry = next(entry for entry in report.entries if entry.fstype == "efivarfs")
        self.assertEqual(entry.state, "MISSING")
        self.assertEqual(entry.remedy, "sudo mount -t efivarfs -o nosuid,nodev,noexec efivarfs /sys/firmware/efi/efivars")
        line = "43 28 0:33 / /sys/firmware/efi/efivars rw,nosuid,nodev,noexec,relatime shared:12 - efivarfs efivarfs rw\n"
        self.assertTrue(host.judge(HEALTHY_LINES + line).host_ok)

    def test_optional_mounts_are_not_applicable_without_their_directory(self):
        dirs = tuple(rel for rel in YAMAGUCHI_DIRS if rel not in ("sys/fs/pstore", "sys/fs/bpf"))
        host = FakeHost(self, dirs=dirs)
        text = "".join(line + "\n" for line in HEALTHY_LINES.splitlines() if " - pstore " not in line and " - bpf " not in line)
        report = host.judge(text)
        self.assertEqual(states(report)["pstore"], "N/A")
        self.assertEqual(states(report)["bpf"], "N/A")
        self.assertTrue(report.host_ok, CHECK.render(report))

    def test_securityfs_and_cgroup2_are_always_expected(self):
        host = FakeHost(self, dirs=(), interface=False)
        text = "28 33 0:25 / /sys rw,nosuid,nodev,noexec,relatime shared:6 - sysfs sysfs rw\n"
        report = host.judge(text)
        self.assertEqual(states(report)["securityfs"], "MISSING")
        self.assertEqual(states(report)["cgroup2"], "MISSING")

    def test_wrong_fstype_is_a_problem(self):
        host = FakeHost(self)
        line = "50 28 0:99 / /sys/kernel/security rw,nosuid,nodev,noexec,relatime shared:99 - tmpfs tmpfs rw\n"
        text = INCIDENT_LINES + line + RESTORED_LINES.replace("/sys/kernel/security", "/sys/kernel/security-ignored")
        report = host.judge(text)
        entry = next(entry for entry in report.entries if entry.where == "/sys/kernel/security")
        self.assertEqual(entry.state, "WRONG-FSTYPE")
        self.assertEqual(entry.found_fstype, "tmpfs")
        self.assertFalse(report.host_ok)

    def test_the_filesystem_type_decides_not_the_source_name(self):
        """`mount -t securityfs none ...` names its source `none`; a tmpfs may be named `securityfs`."""
        host = FakeHost(self)
        by_type = INCIDENT_LINES + "40 28 0:8 / /sys/kernel/security rw shared:7 - securityfs none rw\n" + "".join(line + "\n" for line in RESTORED_LINES.splitlines()[1:])
        self.assertEqual(states(host.judge(by_type))["securityfs"], "MOUNTED")
        decoy = INCIDENT_LINES + "40 28 0:99 / /sys/kernel/security rw shared:7 - tmpfs securityfs rw\n"
        self.assertEqual(states(host.judge(decoy))["securityfs"], "WRONG-FSTYPE")

    def test_topmost_mount_wins(self):
        host = FakeHost(self)
        tmpfs = "50 28 0:99 / /sys/kernel/security rw shared:99 - tmpfs tmpfs rw\n"
        securityfs = RESTORED_LINES.splitlines()[0] + "\n"
        others = "".join(line + "\n" for line in RESTORED_LINES.splitlines()[1:])
        self.assertEqual(states(host.judge(INCIDENT_LINES + tmpfs + securityfs + others))["securityfs"], "MOUNTED")
        self.assertEqual(states(host.judge(INCIDENT_LINES + securityfs + tmpfs + others))["securityfs"], "WRONG-FSTYPE")


class AppArmorConsistencyTest(unittest.TestCase):
    def test_apparmor_disabled_needs_no_interface(self):
        host = FakeHost(self, apparmor_enabled="N\n", interface=False)
        report = host.judge(HEALTHY_LINES)
        self.assertTrue(report.apparmor["consistent"])
        self.assertTrue(report.host_ok)

    def test_apparmor_module_absent_is_consistent(self):
        host = FakeHost(self, apparmor_enabled=None, interface=False)
        report = host.judge(HEALTHY_LINES)
        self.assertFalse(report.apparmor["module_enabled"])
        self.assertIsNone(report.apparmor["module_enabled_raw"])
        self.assertTrue(report.apparmor["consistent"])

    def test_enabled_with_securityfs_mounted_but_no_apparmor_dir_is_inconsistent(self):
        host = FakeHost(self, interface=False)
        report = host.judge(HEALTHY_LINES)
        self.assertEqual(states(report)["securityfs"], "MOUNTED")
        self.assertFalse(report.apparmor["consistent"])
        self.assertEqual(report.problems, 1)


class ParsingAndCliTest(unittest.TestCase):
    def test_octal_escapes_are_decoded(self):
        mounts = CHECK.parse_mountinfo("90 32 8:1 / /run/media/user/My\\040Disk rw shared:50 - exfat /dev/sdj1 rw\n")
        self.assertEqual(mounts[0].where, "/run/media/user/My Disk")
        self.assertEqual(mounts[0].fstype, "exfat")

    def test_optional_fields_become_the_propagation(self):
        mounts = CHECK.parse_mountinfo("36 28 0:30 / /sys/fs/cgroup rw shared:8 master:1 - cgroup2 cgroup2 rw\n")
        self.assertEqual(mounts[0].propagation, "shared:8 master:1")

    def test_json_schema(self):
        host = FakeHost(self, interface=False)
        result = run_cli("--json", "--mountinfo", str(host.mountinfo(INCIDENT_LINES)), "--root", str(host.root))
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"host_ok", "problems", "entries", "apparmor", "mountinfo"})
        self.assertFalse(payload["host_ok"])
        self.assertEqual(payload["problems"], 4)
        self.assertEqual(set(payload["apparmor"]), {"module_enabled", "module_enabled_raw", "interface_present", "consistent", "consequence"})
        for entry in payload["entries"]:
            self.assertEqual(set(entry), {"where", "fstype", "origin", "state", "mount_id", "found_fstype", "propagation", "remedy"})
            self.assertIn(entry["state"], {"MOUNTED", "MISSING", "WRONG-FSTYPE", "N/A"})

    def test_unreadable_mountinfo_exits_2(self):
        host = FakeHost(self)
        result = run_cli("--mountinfo", str(host.root / "absent"), "--root", str(host.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    def test_garbage_mountinfo_exits_2(self):
        host = FakeHost(self)
        result = run_cli("--mountinfo", str(host.mountinfo("this is not mountinfo\n")), "--root", str(host.root))
        self.assertEqual(result.returncode, 2)

    def test_root_must_be_a_directory(self):
        host = FakeHost(self)
        result = run_cli("--mountinfo", str(host.mountinfo(HEALTHY_LINES)), "--root", str(host.root / "mountinfo"))
        self.assertEqual(result.returncode, 2)

    def test_unknown_flag_exits_2(self):
        self.assertEqual(run_cli("--no-such-flag").returncode, 2)

    @unittest.skipUnless(os.path.exists("/proc/self/mountinfo"), "needs a Linux /proc")
    def test_live_host_smoke(self):
        """The real host: exit 0 or 1 (its state is the host's), never 2, and well-formed JSON."""
        result = run_cli("--json")
        self.assertIn(result.returncode, (0, 1), result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["host_ok"], result.returncode == 0)


class TablePinnedToSystemdTest(unittest.TestCase):
    """The pid1 rows must match systemd v259.5's mount_table, as pinned in the RCA's evidence file."""

    FLAGS = {"MS_NOSUID": "nosuid", "MS_NODEV": "nodev", "MS_NOEXEC": "noexec"}

    def _pinned_table(self) -> dict[str, tuple[str, str]]:
        text = PINS.read_text(encoding="utf-8")
        entries: dict[str, dict[str, str]] = {}
        current: dict[str, str] = {}
        for line in text.splitlines():
            match = re.match(r"\s*\d+\s+\.(what|where|type|options|flags)\s*=\s*(.+?),?\s*$", line)
            if not match:
                if line.strip().endswith("},") and current.get("type"):
                    entries[current["type"]] = current
                    current = {}
                continue
            current[match.group(1)] = match.group(2).strip().strip('"')
        table = {}
        for fstype, entry in entries.items():
            flags = [self.FLAGS[flag] for flag in ("MS_NOSUID", "MS_NODEV", "MS_NOEXEC") if flag in entry.get("flags", "")]
            options = ",".join(flags + ([entry["options"]] if "options" in entry and "TMPFS_LIMITS" not in entry["options"] else []))
            table[fstype] = (entry["where"], options)
        return table

    def test_pid1_rows_equal_the_pinned_systemd_table(self):
        pinned = self._pinned_table()
        for fstype in ("securityfs", "pstore", "efivarfs", "bpf"):
            with self.subTest(fstype=fstype):
                row = next(spec for spec in CHECK.API_MOUNTS if spec["fstype"] == fstype)
                self.assertEqual(row["origin"], "pid1")
                self.assertEqual((row["where"], row["options"]), pinned[fstype])


if __name__ == "__main__":
    unittest.main()
