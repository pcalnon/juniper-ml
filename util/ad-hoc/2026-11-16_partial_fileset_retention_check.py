#!/usr/bin/env python3
"""
Which partial-fileset flags explain a retention pass? Replays one pass against the acceptance probe's dlist lists.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-16
Status: ad-hoc — investigation (Phase D sitting, step 14: the first retention pass)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.3.1, Phase D),
         util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py (the all-full port this extends),
         util/ad-hoc/2026-11-11_phase_d_finish.py (`plan`, which uses that port),
         util/ad-hoc/yamaguchi_acceptance_probe.py (writes the history file this reads)

Why this exists
---------------
The first pass of the restored policy (the run of 2026-11-15 13:00Z) deleted four filesets where `plan` predicted
five. `plan` says why it can be wrong: it assumes every fileset is a FULL backup. Duplicati 2.4.0.0's DeleteHandler
keeps a PARTIAL fileset inside a frame and does not measure the next interval from it (`if (isFullBackup) { lastKept
= fileset; }`), and deletes a partial fileset older than every frame. A dlist's name cannot show the flag. This
script asks the converse question: which assignments of the flag to the filesets the pass KEPT reproduce exactly
the deletions observed? A deleted fileset is taken as full, because a partial one inside a frame is never deleted.

Inputs (read-only; nothing under the backup destination is opened, the server is not contacted)
------
The acceptance probe appends one JSON line per run to ``~/.local/state/duplicati/acceptance-history.jsonl``; each
line carries ``generated`` and ``dlists`` (the destination's dlist names). ``--before`` and ``--after`` name two
of those lines by their ``generated`` stamp: the last probe run before the backup and the first after it. The run's
own fileset is the one name the after-list adds. The pass runs near the end of the backup, so it is evaluated at
``--run`` plus ``--duration``, and the all-full port is also evaluated at every minute of the run to show that the
pass time does not change its answer.

Usage
-----
    python3 util/ad-hoc/2026-11-16_partial_fileset_retention_check.py
    python3 util/ad-hoc/2026-11-16_partial_fileset_retention_check.py --before 2026-11-15T23:30:00Z \\
        --after 2026-11-16T23:30:00Z --run 2026-11-16T13:00:00Z --duration 4h05m

The defaults replay the first pass (2026-11-15). The second form replays the next one, which is the test: every
assignment that explains the first pass predicts that the next pass deletes none of the pre-recovery filesets,
while the all-full port predicts it deletes 20260916T183346Z.

Exit codes: 0 = at least one assignment reproduces the observation; 1 = none does (the model cannot explain the
pass); 2 = the evidence could not be read; 64 = usage.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
POLICY = "2W:U,6M:1W,2Y:1M,5Y:2M"
DLIST = re.compile(r"duplicati-(\d{8}T\d{6}Z)\.dlist\.zip\.aes")
PORT = Path(__file__).resolve().parent / "2026-10-08_backup-phase-b-fold-in" / "retention_table.py"
MAX_UNKNOWN = 16  # 2**16 replays; more kept filesets than that outside a keep-all frame is not this question


class EvidenceError(Exception):
    """The history file cannot answer the question asked of it."""


def load_port():
    spec = importlib.util.spec_from_file_location("retention_table", PORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stamp_of(name: str) -> datetime:
    match = DLIST.fullmatch(name)
    if not match:
        raise EvidenceError(f"{name!r} is not a dlist name")
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def parse_instant(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def parse_duration(text: str) -> timedelta:
    match = re.fullmatch(r"(\d+)h(\d{1,2})m", text)
    if not match:
        raise argparse.ArgumentTypeError(f"{text!r} is not a duration like 4h05m")
    return timedelta(hours=int(match.group(1)), minutes=int(match.group(2)))


def history_lists(path: Path, wanted: list[str]) -> dict[str, set[str]]:
    """{generated stamp: set of dlist names} for each wanted stamp; EvidenceError if one is missing or ambiguous."""
    found: dict[str, list[set[str]]] = {stamp: [] for stamp in wanted}
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvidenceError(f"{path} line {number} is not JSON ({exc.msg})") from None
            stamp = doc.get("generated")
            if stamp in found:
                names = doc.get("dlists")
                if not isinstance(names, (dict, list)):
                    raise EvidenceError(f"{path} line {number} ({stamp}) carries no dlist list")
                found[stamp].append(set(names))
    for stamp, lists in found.items():
        if len(lists) != 1:
            raise EvidenceError(f"{path} holds {len(lists)} lines generated at {stamp}; exactly one is needed")
    return {stamp: lists[0] for stamp, lists in found.items()}


def to_delete_partial(filesets: list[datetime], now: datetime, policy, partial: set[datetime]) -> set[datetime]:
    """DeleteHandler's walk, with partial filesets: kept inside a frame, never the interval anchor, deleted outside."""
    remaining = sorted(filesets, reverse=True)[1:]  # the newest is set aside
    deleted: set[datetime] = set()
    for frame, interval in sorted(policy):
        lower = now - frame
        in_frame: list[datetime] = []
        while remaining and remaining[0] >= lower:
            in_frame.insert(0, remaining.pop(0))
        last = None
        for fileset in in_frame:
            full = fileset not in partial
            if last is None or interval <= timedelta(0) or fileset - last >= interval:
                if full:
                    last = fileset
            elif full:
                deleted.add(fileset)
    deleted.update(remaining)
    return deleted


def short(stamps) -> str:
    return ", ".join(f"{s:%Y%m%dT%H%M%SZ}" for s in sorted(stamps)) or "none"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state-dir", type=Path, default=Path.home() / ".local" / "state" / "duplicati", help="where the probe writes acceptance-history.jsonl")
    parser.add_argument("--before", default="2026-11-15T11:30:09Z", help="`generated` of the last probe line before the backup")
    parser.add_argument("--after", default="2026-11-15T23:30:00Z", help="`generated` of the first probe line after it")
    parser.add_argument("--run", type=parse_instant, default=parse_instant("2026-11-15T13:00:00Z"), help="the backup's start, UTC")
    parser.add_argument("--duration", type=parse_duration, default=parse_duration("4h05m"), help="the backup's duration, e.g. 4h05m")
    parser.add_argument("--policy", default=POLICY, help="the retention policy in force at the pass")
    args = parser.parse_args(argv)

    try:
        port = load_port()
        policy = port.parse_policy(args.policy)
        lists = history_lists(args.state_dir / "acceptance-history.jsonl", [args.before, args.after])
        before = {stamp_of(name): name for name in lists[args.before]}
        after = {stamp_of(name) for name in lists[args.after]}
    except (OSError, EvidenceError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 2

    added = after - set(before)
    if len(added) != 1:
        print(f"ERROR: the after-list adds {len(added)} filesets ({short(added)}); exactly one, the run's own, is expected")
        return 2
    own = next(iter(added))
    pre_pass = list(before) + [own]
    observed = set(before) - after
    pass_at = args.run + args.duration
    print(f"policy {args.policy}; pass evaluated at {pass_at:%Y-%m-%dT%H:%MZ} (run {args.run:%Y-%m-%dT%H:%M:%SZ} + {args.duration})")
    print(f"before: {len(before)} dlists (probe {args.before}); the run's own: {own:%Y%m%dT%H%M%SZ}; after: {len(after)} (probe {args.after})")
    print(f"observed: {len(observed)} deleted: {short(observed)}")

    answers = set()
    minute = args.run
    while minute <= pass_at + timedelta(minutes=10):
        answers.add(frozenset(port.to_delete(pre_pass, minute, policy)))
        minute += timedelta(minutes=1)
    for answer in sorted(answers, key=len):
        print(f"all-full port, pass anywhere in the run: {len(answer)} deleted: {short(answer)}")
    if frozenset(to_delete_partial(pre_pass, pass_at, policy, set())) != frozenset(port.to_delete(pre_pass, pass_at, policy)):
        print("ERROR: this script's walk disagrees with the port when no fileset is partial")
        return 2

    keep_all_lower = min((pass_at - frame for frame, interval in policy if interval <= timedelta(0)), default=pass_at)
    unknown = sorted(s for s in pre_pass if s != own and s not in observed and s < keep_all_lower)
    if len(unknown) > MAX_UNKNOWN:
        print(f"ERROR: {len(unknown)} kept filesets lie outside the keep-all frame; more than {MAX_UNKNOWN} is not replayed")
        return 2
    print(f"kept outside the keep-all frame, flag unknown: {len(unknown)}: {short(unknown)}")
    matches = []
    for size in range(len(unknown) + 1):
        for combo in itertools.combinations(unknown, size):
            if to_delete_partial(pre_pass, pass_at, policy, set(combo)) == observed:
                matches.append(set(combo))
    for combo in matches:
        print(f"  MATCH, partial = {short(combo)}")
    print(f"{len(matches)} of {2 ** len(unknown)} assignments reproduce the observed deletions")
    if not matches:
        return 1
    always = set.intersection(*matches)
    print(f"partial in every match: {short(always)}")
    print(f"full in every match: {short(set(unknown) - set.union(*matches))}")
    for first, second in itertools.combinations(unknown, 2):
        if all((first in combo) != (second in combo) for combo in matches):
            print(f"exactly one of {short([first, second])} is partial in every match")

    next_run = args.run + timedelta(days=1)
    next_list = sorted(after) + [next_run]
    next_at = next_run + args.duration
    print(f"next pass (a run at {next_run:%Y-%m-%dT%H:%M:%SZ}, evaluated at {next_at:%Y-%m-%dT%H:%MZ}):")
    print(f"  all-full port: {short(port.to_delete(next_list, next_at, policy))}")
    for prediction in sorted({frozenset(to_delete_partial(next_list, next_at, policy, combo)) for combo in matches}, key=len):
        print(f"  under a matching assignment: {short(prediction)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
