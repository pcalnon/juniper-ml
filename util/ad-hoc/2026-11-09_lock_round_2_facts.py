#!/usr/bin/env python3
"""Report, per consumer tree, the facts the second lock round needs before it touches a lock.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

For each tree fetched by ``2026-11-09_lock_round_2_fetch_consumers.py`` it prints:

* every ``requirements*.lock`` (searching the tree with ``tmp/`` excluded), its header (the
  lines before the first pin) and the pins this round cares about: the two it moves, and the
  ones the per-lock probe records (FastAPI, Starlette, sentry-sdk, pytest, every
  ``opentelemetry-*``);
* every workflow line that runs ``uv pip compile`` (the recipe CI's freshness gate replays);
* every non-test source line that passes FastAPI a ``telemetry=`` argument;
* the first lines of ``CHANGELOG.md``'s ``[Unreleased]`` section.

Usage: python3 util/ad-hoc/2026-11-09_lock_round_2_facts.py tmp/lr2/src/juniper-data [...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WATCH = re.compile(r"^(juniper-observability|juniper-service-core|fastapi|starlette|sentry-sdk|pytest|opentelemetry-[a-z0-9-]+)==", re.I)


def _is_pin(line: str) -> bool:
    return bool(line) and not line.startswith((" ", "\t", "#"))


def _locks(root: Path) -> list[Path]:
    found = []
    for path in sorted(root.rglob("requirements*.lock")):
        rel = path.relative_to(root)
        if rel.parts[0] == "tmp":
            continue
        found.append(path)
    return found


def _report_lock(root: Path, lock: Path) -> None:
    lines = lock.read_text().splitlines()
    header: list[str] = []
    pins: list[str] = []
    for i, line in enumerate(lines):
        if _is_pin(line):
            header = lines[:i]
            pins = [entry for entry in lines[i:] if _is_pin(entry)]
            break
    print(f"  LOCK {lock.relative_to(root)}: {len(pins)} pins, {len(header)} header lines")
    for line in header:
        print(f"    | {line}")
    for pin in pins:
        if WATCH.match(pin):
            print(f"    pin {pin.split(' ')[0]}")


def _report_workflows(root: Path) -> None:
    wf = root / ".github" / "workflows"
    if not wf.is_dir():
        return
    for path in sorted(wf.glob("*.y*ml")):
        lines = path.read_text().splitlines()
        number = 0
        while number < len(lines):
            line = lines[number]
            if line.strip().startswith("uv pip compile"):
                block = [line.strip()]
                while lines[number].rstrip().endswith("\\") and number + 1 < len(lines):
                    number += 1
                    block.append(lines[number].strip())
                print(f"  WF {path.name}:{number + 1}: {' '.join(block)[:700]}")
            number += 1


def _report_telemetry(root: Path) -> None:
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if rel.parts[0] == "tmp" or "tests" in rel.parts or rel.name.startswith("test_"):
            continue
        text = path.read_text(errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if "telemetry=" in line or "FastAPI(" in line:
                print(f"  SRC {rel}:{number}: {line.strip()[:200]}")


def _report_changelog(root: Path) -> None:
    for log in sorted(root.rglob("CHANGELOG.md")):
        rel = log.relative_to(root)
        if rel.parts[0] == "tmp" or len(rel.parts) > 2:
            continue
        lines = log.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith("## [Unreleased]"):
                print(f"  CHANGELOG {rel}:{i + 1}")
                for entry in lines[i + 1 : i + 12]:
                    print(f"    > {entry[:160]}")
                break


def main(argv: list[str]) -> int:
    for arg in argv:
        root = Path(arg)
        print(f"== {root.name}")
        for lock in _locks(root):
            _report_lock(root, lock)
        _report_workflows(root)
        _report_telemetry(root)
        _report_changelog(root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
