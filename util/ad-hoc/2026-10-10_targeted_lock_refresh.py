#!/usr/bin/env python3
"""Regenerate a uv-compiled lockfile so that ONLY the named packages move, keeping its header.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off (flood-3 follow-up item 3: deliver juniper-observability 0.4.1 and
        juniper-service-core 0.7.1 to the juniper-data / -cascor / -canopy / -recurrence locks)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §8

Why
---
A full ``--upgrade`` regeneration moves every transitive pin, so a security-delivery PR built
that way also ships whatever PyPI released since the last weekly regen. ``uv pip compile`` reads
an existing ``-o`` file as soft preferences, so compiling onto a COPY of the current lock with
``--upgrade-package <name>`` frees exactly the named packages and keeps every other pin. uv
rewrites the header with its own command line; the original header (every line before the
first pin) is restored verbatim, because two of the locks carry a hand-written recipe that a
test or a workflow reads.

Modes
-----
refresh  Compile onto a copy of the lock with ``--upgrade-package``; write the original header
         plus the new body back to the lock. Exit 1, writing nothing, if any package other
         than the named ones changed (``--allow-collateral`` overrides).
check    Replay the constraint-mode ``Lockfile Freshness`` gate: compile with
         ``--constraint <lock>`` to a fresh path and compare the sorted pin lines. Exit 1 on
         any difference.

Usage
-----
    2026-10-10_targeted_lock_refresh.py refresh --project-dir <dir with pyproject.toml> \
        [--lock requirements.lock] --uv-args "--extra api --extra observability" \
        [--python-version 3.14] --upgrade-package juniper-observability \
        --upgrade-package juniper-service-core
    2026-10-10_targeted_lock_refresh.py check --project-dir <dir> --uv-args "..." [--python-version 3.14]
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import tempfile
from pathlib import Path


def _is_pin(line: str) -> bool:
    return bool(line) and not line.startswith((" ", "\t", "#"))


def _split_header(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _is_pin(line):
            return lines[:i], lines[i:]
    return lines, []


def _pins(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if _is_pin(line) and "==" in line:
            name, _, version = line.partition("==")
            out[name.strip().lower().replace("_", "-")] = version.strip()
    return out


def _uv_compile(project_dir: Path, uv_args: list[str], python_version: str | None, extra: list[str], out: Path) -> None:
    cmd = ["uv", "pip", "compile", "pyproject.toml", *uv_args]
    if python_version:
        cmd += ["--python-version", python_version]
    cmd += [*extra, "-o", str(out)]
    print("+ (cd " + str(project_dir) + " && " + shlex.join(cmd) + ")", flush=True)
    proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)  # nosec B603
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(f"uv pip compile failed (exit {proc.returncode})")


def refresh(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    lock = project_dir / args.lock
    original = lock.read_text(encoding="utf-8")
    header, _ = _split_header(original)
    if not header:
        raise SystemExit(f"{lock} has no leading comment header; refusing (it would be lost)")
    targets = {p.lower().replace("_", "-") for p in args.upgrade_package}
    extra = []
    for name in args.upgrade_package:
        extra += ["--upgrade-package", name]
    with tempfile.TemporaryDirectory(prefix="lock-refresh-") as tmp:
        work = Path(tmp) / lock.name
        shutil.copyfile(lock, work)  # the copy is uv's preference source
        _uv_compile(project_dir, shlex.split(args.uv_args), args.python_version, extra, work)
        _, body = _split_header(work.read_text(encoding="utf-8"))
    if not body:
        raise SystemExit("uv produced no pins")
    new_text = "\n".join(header + body) + "\n"
    old, new = _pins(original), _pins(new_text)
    changed = sorted(n for n in set(old) | set(new) if old.get(n) != new.get(n))
    for name in changed:
        print(f"  {name}: {old.get(name, '(absent)')} -> {new.get(name, '(absent)')}")
    collateral = [n for n in changed if n not in targets]
    if collateral and not args.allow_collateral:
        print(f"REFUSED: packages outside the upgrade set changed: {collateral}", file=sys.stderr)
        return 1
    if not changed:
        print("no pin changed")
    lock.write_text(new_text, encoding="utf-8")
    print(f"wrote {lock} ({len(changed)} pin(s) changed)")
    return 0


def check(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    lock = project_dir / args.lock
    with tempfile.TemporaryDirectory(prefix="lock-check-") as tmp:
        fresh = Path(tmp) / "requirements.lock.check"
        _uv_compile(project_dir, shlex.split(args.uv_args), args.python_version, ["--constraint", str(lock)], fresh)
        lock_pins = sorted(line for line in lock.read_text(encoding="utf-8").splitlines() if _is_pin(line))
        check_pins = sorted(line for line in fresh.read_text(encoding="utf-8").splitlines() if _is_pin(line))
    if lock_pins == check_pins:
        print(f"FRESH: {lock} satisfies the constraint-mode gate ({len(lock_pins)} pins)")
        return 0
    only_lock = sorted(set(lock_pins) - set(check_pins))
    only_check = sorted(set(check_pins) - set(lock_pins))
    print(f"STALE: lock-only {only_lock}; resolution-only {only_check}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    for mode in ("refresh", "check"):
        p = sub.add_parser(mode)
        p.add_argument("--project-dir", required=True)
        p.add_argument("--lock", default="requirements.lock")
        p.add_argument("--uv-args", default="", help="extra uv pip compile arguments, one shell-quoted string")
        p.add_argument("--python-version", default=None)
        if mode == "refresh":
            p.add_argument("--upgrade-package", action="append", required=True)
            p.add_argument("--allow-collateral", action="store_true")
    args = ap.parse_args(argv)
    return refresh(args) if args.mode == "refresh" else check(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
