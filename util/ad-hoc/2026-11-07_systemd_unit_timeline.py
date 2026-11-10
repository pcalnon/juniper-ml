#!/usr/bin/env python3
"""
Print every systemd unit state-change timestamp that falls inside a time window.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md

Why this exists
---------------
systemd keeps, per loaded unit, the wall-clock time of its last transitions
(``ActiveEnterTimestamp``, ``ActiveExitTimestamp``, ``InactiveEnterTimestamp``,
``InactiveExitTimestamp``, ``StateChangeTimestamp``; timers add
``LastTriggerUSec``). PID 1 holds them in memory for as long as the unit stays
loaded -- independently of journald, whose files rotate. On yamaguchi the journal,
syslog and auth.log all begin after the 2026-10-27 22:55:28Z unmount, so these
in-memory timestamps are the surviving record of what changed state then.

Limits (read before concluding anything from an absence):

* Only LOADED units are visible. A unit that went inactive and had no unit file
  (``sys-kernel-security.mount``, ``sys-fs-bpf.mount``, a transient
  ``docker-<id>.scope``) is garbage-collected and leaves nothing.
* Each field holds only the LAST transition of that kind, so a unit that changed
  again later overwrote the earlier time.

Read-only: it runs ``systemctl list-units`` and ``systemctl show`` only.

Usage
-----
    python3 util/ad-hoc/2026-11-07_systemd_unit_timeline.py \\
        --since 2026-10-27T22:50:00Z --until 2026-10-27T23:00:00Z [--user] [--public]

``--public`` drops device units named by hardware identity (USB serials, partition UUIDs, port
paths); the committed evidence for the RCA was produced with it, because juniper-ml is public.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone

FIELDS = [
    "ActiveEnterTimestamp",
    "ActiveExitTimestamp",
    "InactiveEnterTimestamp",
    "InactiveExitTimestamp",
    "StateChangeTimestamp",
    "LastTriggerUSec",
]


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_systemd_ts(value: str) -> datetime | None:
    """Parse systemctl's ``--timestamp=us+utc`` form, e.g. ``Tue 2026-10-27 22:55:28.266715 UTC``."""
    value = value.strip()
    if not value or value in ("n/a", "0"):
        return None
    parts = value.split()
    if len(parts) < 3 or parts[-1] != "UTC":
        return None
    stamp = " ".join(parts[1:3]) if len(parts) >= 4 else " ".join(parts[0:2])
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(stamp, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def systemctl(user: bool, *args: str) -> str:
    cmd = ["systemctl"] + (["--user"] if user else []) + list(args)
    return subprocess.run(cmd, check=False, capture_output=True, text=True).stdout


def list_units(user: bool) -> list[str]:
    out = systemctl(user, "list-units", "--all", "--plain", "--no-legend", "--no-pager")
    units = []
    for line in out.splitlines():
        fields = line.split()
        if fields:
            units.append(fields[0])
    return units


def show_units(user: bool, units: list[str], batch: int = 200):
    props = ["-p", "Id", "-p", "Where", "-p", "What", "-p", "ActiveState"] + [arg for field in FIELDS for arg in ("-p", field)]
    for start in range(0, len(units), batch):
        chunk = units[start : start + batch]
        out = systemctl(user, "show", "--timestamp=us+utc", *props, "--", *chunk)
        record: dict[str, str] = {}
        for line in out.splitlines() + [""]:
            if not line.strip():
                if record:
                    yield record
                    record = {}
                continue
            key, _, value = line.partition("=")
            record[key] = value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--user", action="store_true", help="query the user manager instead of PID 1")
    parser.add_argument(
        "--public",
        action="store_true",
        help="omit device units named by hardware identity (by-id / by-uuid / by-partuuid / by-path / by-diskseq / by-loop-* aliases and sys-devices-* paths), "
        "which carry serial numbers and port topology; kernel-named units (dev-sdj1.device, dev-loop0.device) stay. Use for output committed to a public repo.",
    )
    args = parser.parse_args(argv)
    since, until = parse_iso(args.since), parse_iso(args.until)

    units = list_units(args.user)
    if args.public:
        # Any udev alias unit (dev-disk-by-*, dev-input-by-*, dev-serial-by-*, ...) and any sysfs device path.
        identity = re.compile(r"(by\\x2d|^sys-devices-)")
        units = [unit for unit in units if not identity.search(unit)]
    rows = []
    for record in show_units(args.user, units):
        for field in FIELDS:
            ts = parse_systemd_ts(record.get(field, ""))
            if ts is not None and since <= ts <= until:
                rows.append((ts, record.get("Id", "?"), field, record.get("ActiveState", ""), record.get("Where", ""), record.get("What", "")))
    rows.sort()
    scope = "user" if args.user else "system"
    print(f"# manager={scope} loaded_units={len(units)} public={args.public} window=[{since.isoformat()} .. {until.isoformat()}] rows={len(rows)}")
    print("# columns: utc_timestamp, field, unit, active_state_NOW, where (mounts), what (mounts)")
    for ts, unit, field, state, where, what in rows:
        print(f"{ts.strftime('%Y-%m-%dT%H:%M:%S.%f')}Z\t{field}\t{unit}\tnow={state}\t{where}\t{what}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
