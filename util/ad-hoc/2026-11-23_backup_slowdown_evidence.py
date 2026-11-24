#!/usr/bin/env python3
"""
Why did the backup job's runs stretch from hours to days after 2026-11-18? A read-only evidence digest.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-23
Status: ad-hoc — investigation (backup Phase D follow-up: AC-5 and the slow runs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.3.1),
         util/ad-hoc/yamaguchi_acceptance_probe.py (writes the history file this reads),
         util/ad-hoc/2026-11-16_partial_fileset_retention_check.py (replays a retention pass from the same file)

What it reads (nothing is written, the server is not contacted, nothing under the backup destination is opened)
-------------
1. The acceptance probe's history, ``~/.local/state/duplicati/acceptance-history.jsonl``: per probe run, the dlist
   count, the dlists added and removed since the previous run, the volume classes (type, mode, owner) and the RUN,
   AC-5, AC-7 and CENSUS verdicts.
2. The watchdog's log, ``~/.local/state/duplicati/server-watchdog.log``, from ``--since`` on.
3. sysstat's daily files ``/var/log/sysstat/saDD``: per day, the average %iowait, %idle, swap used, 15-minute load
   and blocked tasks, over the whole day and over ``--window`` (local time), and each disk's average %util over the
   window when it reaches ``--util-floor``.
4. Now: the kernel's pressure-stall averages, ``duplicati.service``'s scheduling properties and the devices that
   hold ``--source`` and ``--dest`` (``findmnt -T`` stats the path; it opens nothing beneath it).

Usage
-----
    python3 -I util/ad-hoc/2026-11-23_backup_slowdown_evidence.py
    python3 -I util/ad-hoc/2026-11-23_backup_slowdown_evidence.py --since 2026-11-14 --window 07:00:00-19:00:00

Exit codes: 0 = printed; 2 = the history file could not be read; 64 = usage.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

STATE = Path.home() / ".local" / "state" / "duplicati"
HISTORY = STATE / "acceptance-history.jsonl"
WATCHDOG = STATE / "server-watchdog.log"
SYSSTAT = Path("/var/log/sysstat")
URL = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+")
DISKS = ("sda", "sdb", "nvme0n1")  # sdb: /home (source, server data); sda: /mnt/Backups (destination); nvme0n1: root, swap
WIDTH = 320


def clean(text: object) -> str:
    """One line, no URL (the probe never prints one; this makes the digest safe to paste regardless)."""
    return URL.sub("<url>", " ".join(str(text).split()))[:WIDTH]


def history_digest(path: Path) -> None:
    print(f"== 1. acceptance-history ({path})")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    previous: set[str] = set()
    for row in rows:
        names = set(row.get("dlists") or {})
        stamps = lambda group: sorted(re.sub(r"^duplicati-|\.dlist\.zip\.aes$", "", n) for n in group)  # noqa: E731
        added, removed = stamps(names - previous), stamps(previous - names)
        print(f"{row.get('generated')} result={clean(row.get('result'))} dlists={len(names)}" + (f" +{added}" if previous else "") + (f" -{removed}" if removed else ""))
        classes = row.get("classes") or {}
        if classes:
            print("   classes: " + ", ".join(f"{k}={v}" for k, v in sorted(classes.items())))
        verdicts = row.get("verdicts") or {}
        for key in ("RUN", "AC-5", "AC-7", "CENSUS"):
            if key in verdicts:
                print(f"   {key:<6} {clean(verdicts[key])}")
        previous = names


def watchdog_digest(path: Path, since: str) -> None:
    print(f"\n== 2. watchdog log from {since} ({path})")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line[:10] >= since:
            print(clean(line))


def sar(args: list[str]) -> list[str]:
    """sar with C-locale, 24-hour (ISO) times; `env` sets the two variables without copying the environment."""
    done = subprocess.run(["env", "LC_ALL=C", "S_TIME_FORMAT=ISO", "sar", *args], capture_output=True, text=True, timeout=120, check=False)
    return done.stdout.splitlines()


def averages(lines: list[str]) -> list[dict[str, str]]:
    """Map each `Average:` row onto the most recent header row's column names."""
    header: list[str] = []
    rows = []
    for line in lines:
        tokens = line.split()
        if len(tokens) < 2:
            continue
        if re.fullmatch(r"\d\d:\d\d:\d\d", tokens[0]) and any(t.startswith("%") or t.startswith("ldavg") or t.startswith("kbswp") for t in tokens[1:]):
            header = tokens[1:]
        elif tokens[0] == "Average:" and header and len(tokens) - 1 == len(header):
            rows.append(dict(zip(header, tokens[1:])))
    return rows


def sar_day(path: Path, window: tuple[str, str], util_floor: float) -> None:
    head = sar(["-u", "-f", str(path), "-s", "00:00:00", "-e", "00:00:30"])
    date = next((m.group(0) for line in head[:3] for m in [re.search(r"\d\d/\d\d/\d{4}|\d{4}-\d\d-\d\d", line)] if m), path.name)
    cells = []
    for label, span in (("day", []), ("window", ["-s", window[0], "-e", window[1]])):
        cpu = averages(sar(["-u", "-f", str(path), *span]))
        swap = averages(sar(["-S", "-f", str(path), *span]))
        load = averages(sar(["-q", "-f", str(path), *span]))
        c = cpu[0] if cpu else {}
        s = swap[0] if swap else {}
        q = load[0] if load else {}
        cells.append(f"{label}: iowait={c.get('%iowait', '?')}% idle={c.get('%idle', '?')}% swpused={s.get('%swpused', '?')}% ldavg15={q.get('ldavg-15', '?')} blocked={q.get('blocked', '?')}")
    disks = averages(sar(["-d", "-p", "-f", str(path), "-s", window[0], "-e", window[1]]))
    busy = [f"{d.get('DEV')}={d.get('%util')}%" for d in disks if _num(d.get("%util")) >= util_floor]
    print(f"{date} ({path.name})  " + "  |  ".join(cells) + (f"  |  window %util>={util_floor:g}: " + ", ".join(busy) if busy else ""))
    day = averages(sar(["-d", "-p", "-f", str(path)]))
    rates = [f"{d.get('DEV')} r={_num(d.get('rkB/s')) / 1024:.1f} w={_num(d.get('wkB/s')) / 1024:.1f} util={d.get('%util')}%" for d in day if d.get("DEV") in DISKS]
    if rates:
        print("      day average, MiB/s: " + "; ".join(rates))


def _num(text: str | None) -> float:
    try:
        return float(text or "nan")
    except ValueError:
        return float("nan")


def now_digest(source: str, dest: str) -> None:
    print("\n== 4. now")
    for resource in ("cpu", "memory", "io"):
        try:
            print(f"pressure {resource}: " + " | ".join((Path("/proc/pressure") / resource).read_text(encoding="ascii").splitlines()))
        except OSError as exc:
            print(f"pressure {resource}: unreadable ({exc.__class__.__name__})")
    props = "Nice,IOSchedulingClass,IOSchedulingPriority,CPUWeight,IOWeight,MemoryHigh,MemoryMax,ActiveEnterTimestamp,UMask"
    done = subprocess.run(["systemctl", "show", "duplicati.service", "-p", props, "--no-pager"], capture_output=True, text=True, timeout=30, check=False)
    print("duplicati.service: " + " ".join(done.stdout.split()))
    for label, target in (("source", source), ("dest", dest)):
        found = subprocess.run(["findmnt", "-n", "-o", "SOURCE,TARGET,FSTYPE", "-T", target], capture_output=True, text=True, timeout=30, check=False)
        print(f"{label} {target}: {' '.join(found.stdout.split()) or 'not found'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", default="2026-11-14", help="first watchdog date to print (YYYY-MM-DD, local)")
    parser.add_argument("--window", default="07:00:00-19:00:00", help="local-time window for the sar averages (HH:MM:SS-HH:MM:SS)")
    parser.add_argument("--util-floor", type=float, default=20.0, help="print a disk's window %%util only at or above this")
    parser.add_argument("--source", default=str(Path.home()), help="a backup source path, to name its device")
    parser.add_argument("--dest", default="/mnt/Backups/Ubuntu", help="the backup destination, to name its device (stat only)")
    args = parser.parse_args(argv)
    match = re.fullmatch(r"(\d\d:\d\d:\d\d)-(\d\d:\d\d:\d\d)", args.window)
    if not match:
        parser.error("--window must read HH:MM:SS-HH:MM:SS")
        return 64
    try:
        history_digest(HISTORY)
    except (OSError, ValueError) as exc:
        print(f"history unreadable: {exc.__class__.__name__}", file=sys.stderr)
        return 2
    watchdog_digest(WATCHDOG, args.since)
    print(f"\n== 3. sysstat, local time; window {args.window}")
    for path in sorted(SYSSTAT.glob("sa[0-9][0-9]")):
        sar_day(path, (match.group(1), match.group(2)), args.util_floor)
    now_digest(args.source, args.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
