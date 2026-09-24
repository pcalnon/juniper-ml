#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-09-23_thread_width_mutation_check.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-23
# Last Modified: 2026-09-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Mutation check for tests/test_thread_width.py: does the gate go RED when the helper (or the
#    gate's own scanner) regresses in each of the ways it exists to catch?
#
#    Each mutation is applied to a COPY of the relevant tree under a temp dir -- util/thread_width.py,
#    tests/test_thread_width.py, and the two scanned directories -- and the suite is run there with
#    `python3 -m unittest`. The live tree is never edited, so an interrupted run cannot leave a
#    mutant behind. The control (no mutation) must be green; every mutation must be red.
#
#    Usage:  python3 util/ad-hoc/2026-09-23_thread_width_mutation_check.py
#    Exit 0 = control green and every mutation red.
#####################################################################################################################################################################################################
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = "util/thread_width.py"
SUITE = "tests/test_thread_width.py"

# (id, file, old, new, what the mutation models)
MUTATIONS = [
    ("M01", HELPER, "        raise ThreadWidthHazard(", "        original(*args, **kwargs)\n        raise ThreadWidthHazard(", "guard calls through, THEN raises (the thread is already re-pinned)"),
    ("M02", HELPER, "        raise ThreadWidthHazard(", "        return original(*args, **kwargs)\n        raise ThreadWidthHazard(", "guard never raises off the main thread"),
    ("M03", HELPER, 'if caller == "torch" or caller.startswith("torch."):', 'if caller.startswith("torch"):', "exemption matches any module NAMED like torch"),
    ("M04", HELPER, "mode=os.RTLD_NOLOAD | os.RTLD_LAZY", "mode=os.RTLD_LAZY", "the handle may load a second runtime"),
    ("M05", HELPER, "(?:-[0-9a-f]{6,})?", "", "parser misses a manylinux-renamed libgomp-<hash>.so.1"),
    ("M06", HELPER, "            if len(mapped) > 1:", "            if len(mapped) > 99:", "ambiguity is resolved by guessing mapped[0]"),
    ("M07", HELPER, "        if torch_module.get_num_threads is guarded_get_num_threads:\n            torch_module.get_num_threads = original", "        torch_module.get_num_threads = original", "uninstall clobbers a later replacement"),
    ("M08", HELPER, "        elif path not in mapped:", "        elif False:", "an unmapped path is opened when named"),
    ("M09", HELPER, "    if getattr(current, GUARD_MARKER, False):\n        return lambda: None", "", "a second install wraps the guard in another guard"),
    ("M10", SUITE, '        elif isinstance(node, ast.Name) and node.id == "get_num_threads":\n            getter_line = node.lineno\n', "", "scanner misses `from torch import get_num_threads`"),
    ("M11", SUITE, '        if isinstance(node, ast.Attribute) and node.attr == "get_num_threads":\n            getter_line = node.lineno\n        elif', "        if", "scanner misses `raw = torch.get_num_threads` and `torch.get_num_threads()`"),
    ("M12", SUITE, "    return sorted(rel for rel in entries if not violations(read(rel)))", "    return []", "the grandfather list may rot: a converted file stays exempt"),
]

# The first run of this harness had M12 remove the staleness check at its call site, and it
# SURVIVED: no grandfathered file is stale today, so the real input could never exercise it. The
# check now lives in `stale_entries`, with a synthetic test that makes it fire. Nothing is expected
# to survive; the set is kept so a future deliberate survivor has to be named.
EXPECTED_SURVIVORS: set[str] = set()


def _copy_tree(dest: Path) -> None:
    for rel in (HELPER, SUITE):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest / rel)
    for rel in ("util/ad-hoc", "util/experiments"):
        shutil.copytree(REPO / rel, dest / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _run(dest: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", SUITE.replace("/", ".")[:-3]], cwd=dest, capture_output=True, text=True, check=False)
    tail = (proc.stderr.strip().splitlines() or ["?"])[-1]
    return proc.returncode == 0, tail


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory(prefix="thread-width-mut-") as tmp:
        root = Path(tmp)
        control = root / "control"
        _copy_tree(control)
        (control / "tests" / "__init__.py").touch()
        green, tail = _run(control)
        print(f"control  {'GREEN' if green else 'RED  '}  {tail}")
        ok &= green
        for mid, rel, old, new, what in MUTATIONS:
            dest = root / mid
            _copy_tree(dest)
            (dest / "tests" / "__init__.py").touch()
            target = dest / rel
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"{mid}      ANCHOR {text.count(old)}x -- mutation not applied: {what}")
                ok = False
                continue
            target.write_text(text.replace(old, new), encoding="utf-8")
            green, tail = _run(dest)
            expected_green = mid in EXPECTED_SURVIVORS
            verdict = "caught" if not green else ("survives (expected)" if expected_green else "SURVIVED")
            ok &= (not green) or expected_green
            print(f"{mid}      {'GREEN' if green else 'RED  '}  {verdict:<20} {what}   [{tail}]")
    print("\nall mutations caught" if ok else "\nA MUTATION SURVIVED or an anchor moved -- the gate does not pin what it claims")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
