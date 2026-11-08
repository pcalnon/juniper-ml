#!/usr/bin/env python3
"""
Check that a Linux host still has the API filesystems systemd mounted at boot.

Project: juniper-ml
Sub-Project: host tooling
Author: Paul Calnon
Created: 2026-11-07
Related: notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md
         notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md
Tests: tests/test_host_api_filesystems_check.py

Why this exists
---------------
On 2026-10-27 a root ``umount -a``-like event on yamaguchi unmounted every filesystem not in use.
The same-day repair restarted what ``systemctl`` could see -- ``snapd.mounts.target`` and the six
API mounts that have unit files -- and stopped there. Three more had gone:

* ``securityfs`` on ``/sys/kernel/security`` (the AppArmor interface),
* ``pstore`` on ``/sys/fs/pstore``,
* ``bpf`` on ``/sys/fs/bpf``.

systemd's PID 1 mounts those itself, from a table in ``src/shared/mount-setup.c``. They have no
unit file, so once one is unmounted its unit is garbage-collected: ``systemctl list-units --all``
cannot list it, and nothing remounts it. Eleven days later every ``docker compose up`` failed with
``Could not check if docker-default AppArmor profile was loaded``, and every snap -- the k8s
component snaps included -- died in snap-confine with ``aa_is_enabled() failed unexpectedly``.

This check reads ``/proc/self/mountinfo`` instead of systemd's unit list, so it sees those
mounts.

What it checks
--------------
1. Each API filesystem PID 1 mounts (``securityfs``, ``cgroup2``, ``pstore``, ``efivarfs``, ``bpf``)
   and each one systemd mounts through a unit file (``debugfs``, ``tracefs``, ``configfs``,
   ``fusectl``, ``hugetlbfs``, ``mqueue``), at its mount point, with its filesystem type. An entry
   is only expected where the kernel or firmware provides it: ``pstore`` / ``bpf`` / the unit-file
   mounts when their mount-point directory exists, ``efivarfs`` only on an EFI boot.
2. That AppArmor's interface is reachable whenever the kernel reports AppArmor enabled
   (``/sys/module/apparmor/parameters/enabled`` is ``Y``): ``/sys/kernel/security/apparmor/profiles``
   must exist. When it does not, Docker (which caches AppArmor support once, at daemon start) fails
   every container start, snap-confine fails every snap, and snapd cannot refresh.

It is read-only. It prints the remedy for each missing mount (with systemd's own options) but runs
nothing.

Exit codes: 0 every expected mount present and AppArmor consistent; 1 at least one problem;
2 usage error or unreadable input.

Usage
-----
    python3 util/host_api_filesystems_check.py            # report
    python3 util/host_api_filesystems_check.py --json     # machine-readable
    # hermetic (tests): judge a saved mountinfo against a fake root
    python3 util/host_api_filesystems_check.py --mountinfo FILE --root DIR
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# origin "pid1": PID 1's mount_setup() table (systemd src/shared/mount-setup.c, v259.5); no unit file.
# origin "unit": a static unit file shipped by systemd. `options` are systemd's for that mount.
# `applies_if` is the path whose existence makes the entry expected ("" = always expected).
API_MOUNTS = (
    {"where": "/sys/kernel/security", "fstype": "securityfs", "origin": "pid1", "options": "nosuid,nodev,noexec", "applies_if": "", "unit": "sys-kernel-security.mount"},
    {"where": "/sys/fs/cgroup", "fstype": "cgroup2", "origin": "pid1", "options": "nosuid,nodev,noexec,nsdelegate,memory_recursiveprot", "applies_if": "", "unit": "sys-fs-cgroup.mount"},
    {"where": "/sys/fs/pstore", "fstype": "pstore", "origin": "pid1", "options": "nosuid,nodev,noexec", "applies_if": "/sys/fs/pstore", "unit": "sys-fs-pstore.mount"},
    {"where": "/sys/firmware/efi/efivars", "fstype": "efivarfs", "origin": "pid1", "options": "nosuid,nodev,noexec", "applies_if": "/sys/firmware/efi", "unit": "sys-firmware-efi-efivars.mount"},
    {"where": "/sys/fs/bpf", "fstype": "bpf", "origin": "pid1", "options": "nosuid,nodev,noexec,mode=0700", "applies_if": "/sys/fs/bpf", "unit": "sys-fs-bpf.mount"},
    {"where": "/sys/kernel/debug", "fstype": "debugfs", "origin": "unit", "options": "", "applies_if": "/sys/kernel/debug", "unit": "sys-kernel-debug.mount"},
    {"where": "/sys/kernel/tracing", "fstype": "tracefs", "origin": "unit", "options": "", "applies_if": "/sys/kernel/tracing", "unit": "sys-kernel-tracing.mount"},
    {"where": "/sys/kernel/config", "fstype": "configfs", "origin": "unit", "options": "", "applies_if": "/sys/kernel/config", "unit": "sys-kernel-config.mount"},
    {"where": "/sys/fs/fuse/connections", "fstype": "fusectl", "origin": "unit", "options": "", "applies_if": "/sys/fs/fuse/connections", "unit": "sys-fs-fuse-connections.mount"},
    {"where": "/dev/hugepages", "fstype": "hugetlbfs", "origin": "unit", "options": "", "applies_if": "/dev/hugepages", "unit": "dev-hugepages.mount"},
    {"where": "/dev/mqueue", "fstype": "mqueue", "origin": "unit", "options": "", "applies_if": "/dev/mqueue", "unit": "dev-mqueue.mount"},
)

APPARMOR_ENABLED = "/sys/module/apparmor/parameters/enabled"
APPARMOR_PROFILES = "/sys/kernel/security/apparmor/profiles"

_OCTAL = re.compile(r"\\([0-7]{3})")


@dataclass
class Mount:
    mount_id: str
    where: str
    fstype: str
    propagation: str


@dataclass
class Entry:
    where: str
    fstype: str
    origin: str
    state: str  # MOUNTED | MISSING | WRONG-FSTYPE | N/A
    mount_id: str = ""
    found_fstype: str = ""
    propagation: str = ""
    remedy: str = ""


@dataclass
class Report:
    host_ok: bool
    problems: int
    entries: list[Entry] = field(default_factory=list)
    apparmor: dict = field(default_factory=dict)


def unescape(path: str) -> str:
    """mountinfo escapes space, tab, newline and backslash as \\ooo."""
    return _OCTAL.sub(lambda m: chr(int(m.group(1), 8)), path)


def parse_mountinfo(text: str) -> list[Mount]:
    """Parse /proc/<pid>/mountinfo (proc(5)): fields up to ' - ' then fstype, source, super options."""
    mounts = []
    for line in text.splitlines():
        if not line.strip():
            continue
        left, sep, right = line.partition(" - ")
        if not sep:
            raise ValueError(f"not a mountinfo line (no ' - ' separator): {line[:120]!r}")
        fields = left.split()
        rest = right.split()
        if len(fields) < 6 or not rest:
            raise ValueError(f"not a mountinfo line (too few fields): {line[:120]!r}")
        mounts.append(Mount(mount_id=fields[0], where=unescape(fields[4]), fstype=rest[0], propagation=" ".join(fields[6:])))
    return mounts


def remedy_for(spec: dict) -> str:
    if spec["origin"] == "pid1":
        return f"sudo mount -t {spec['fstype']} -o {spec['options']} {spec['fstype']} {spec['where']}"
    return f"sudo systemctl start {spec['unit']}"


def judge(mounts: list[Mount], root: Path) -> Report:
    # The LAST mount listed at a mount point is the one a path lookup reaches (it is mounted on top).
    top: dict[str, Mount] = {}
    for mount in mounts:
        top[mount.where] = mount

    def exists(path: str) -> bool:
        return (root / path.lstrip("/")).exists()

    entries = []
    for spec in API_MOUNTS:
        entry = Entry(where=spec["where"], fstype=spec["fstype"], origin=spec["origin"], state="")
        mount = top.get(spec["where"])
        if spec["applies_if"] and not exists(spec["applies_if"]) and mount is None:
            entry.state = "N/A"
        elif mount is None:
            entry.state = "MISSING"
            entry.remedy = remedy_for(spec)
        elif mount.fstype != spec["fstype"]:
            entry.state = "WRONG-FSTYPE"
            entry.found_fstype = mount.fstype
            entry.mount_id = mount.mount_id
            entry.remedy = f"inspect: findmnt {spec['where']} (expected {spec['fstype']}, found {mount.fstype})"
        else:
            entry.state = "MOUNTED"
            entry.mount_id = mount.mount_id
            entry.propagation = mount.propagation
        entries.append(entry)

    enabled_file = root / APPARMOR_ENABLED.lstrip("/")
    try:
        enabled_raw = enabled_file.read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        enabled_raw = ""
    enabled = enabled_raw.startswith("Y")
    interface = exists(APPARMOR_PROFILES)
    consistent = interface or not enabled
    apparmor = {
        "module_enabled": enabled,
        "module_enabled_raw": enabled_raw or None,
        "interface_present": interface,
        "consistent": consistent,
    }
    if not consistent:
        apparmor["consequence"] = (
            "AppArmor is enabled in the kernel but its securityfs interface is unreachable: Docker fails every "
            "container start ('Could not check if docker-default AppArmor profile was loaded'), snap-confine fails "
            "every snap ('aa_is_enabled() failed unexpectedly'), snapd cannot refresh, apparmor_parser cannot load."
        )
    problems = sum(1 for entry in entries if entry.state in ("MISSING", "WRONG-FSTYPE")) + (0 if consistent else 1)
    return Report(host_ok=problems == 0, problems=problems, entries=entries, apparmor=apparmor)


def render(report: Report) -> str:
    lines = [f"{'WHERE':<28} {'FSTYPE':<11} {'ORIGIN':<6} {'STATE':<13} {'ID':<7} PROPAGATION"]
    for entry in report.entries:
        lines.append(f"{entry.where:<28} {entry.fstype:<11} {entry.origin:<6} {entry.state:<13} {entry.mount_id or '-':<7} {entry.propagation or '-'}")
    aa = report.apparmor
    lines.append("")
    lines.append(f"AppArmor: module enabled={aa['module_enabled_raw'] or 'absent'}  interface ({APPARMOR_PROFILES}) {'present' if aa['interface_present'] else 'MISSING'}  -> {'consistent' if aa['consistent'] else 'INCONSISTENT'}")
    if not aa["consistent"]:
        lines.append(f"  {aa['consequence']}")
    remedies = [entry for entry in report.entries if entry.remedy]
    if remedies:
        lines.append("")
        lines.append("Remedy (not run by this check; see the runbook before running any of it on a host with a k8s install):")
        for entry in remedies:
            lines.append(f"  {entry.remedy}")
        if any(entry.origin == "pid1" and entry.state == "MISSING" for entry in report.entries):
            lines.append("  ('pid1' mounts have no unit file: PID 1 mounts them once at boot, so systemctl cannot list or restart them.)")
    lines.append("")
    lines.append(f"host_api_filesystems_check: {'OK' if report.host_ok else f'{report.problems} problem(s)'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip().splitlines()[-1])
    parser.add_argument("--mountinfo", default="/proc/self/mountinfo", help="mountinfo file to judge (default: /proc/self/mountinfo)")
    parser.add_argument("--root", default="/", help="prefix for the existence checks (default: /); tests point it at a fake tree")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0

    try:
        with open(args.mountinfo, encoding="utf-8", errors="surrogateescape") as handle:
            text = handle.read()
        mounts = parse_mountinfo(text)
    except (OSError, ValueError) as exc:
        print(f"host_api_filesystems_check: cannot read {args.mountinfo}: {exc}", file=sys.stderr)
        return 2
    root = Path(args.root)
    if not root.is_dir():
        print(f"host_api_filesystems_check: --root {args.root} is not a directory", file=sys.stderr)
        return 2

    report = judge(mounts, root)
    if args.json:
        payload = asdict(report)
        payload["mountinfo"] = os.path.abspath(args.mountinfo)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render(report))
    return 0 if report.host_ok else 1


if __name__ == "__main__":
    sys.exit(main())
