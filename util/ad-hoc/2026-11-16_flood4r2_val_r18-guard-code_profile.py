"""
Profile one guard copy (in-process run_hook, cProfile) on one timing shape, and count how often the hot helpers are
entered, to locate a cost blowup (validator JL1, r18-guard code lens, item 4).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_timing.py (the shapes)

Usage: python3 <this file> <scratch dir> <guard copy> <shape name> [<top N>]
The guard only judges a payload; nothing is executed.
"""

import cProfile
import importlib.util
import io
import json
import os
import pstats
import sys
import time
from pathlib import Path


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list) -> int:
    scratch = Path(argv[0]).resolve()
    guard = load(Path(argv[1]).resolve(), "jl1_prof_guard")
    timing = load(Path(__file__).with_name("2026-11-16_flood4r2_val_r18-guard-code_timing.py"), "jl1_prof_timing")
    command = timing.SHAPES[argv[2]]()
    top = int(argv[3]) if len(argv) > 3 else 12
    home = str(scratch / "scratch_home")
    os.environ.pop("CLAUDE_PROJECT_DIR", None)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": home}).encode()
    scans = []
    original = guard.BashAnalyzer._scan

    def counted(self, text, depth, bases):
        scans.append((depth, len(text)))
        return original(self, text, depth, bases)

    guard.BashAnalyzer._scan = counted
    prof = cProfile.Profile()
    t0 = time.perf_counter()
    prof.enable()
    code, out, _err = guard.run_hook(payload, homes=[home], project_dir="")
    prof.disable()
    took = time.perf_counter() - t0
    print("shape %s, %d bytes: %.2fs, exit %d, %s" % (argv[2], len(command), took, code, "DENY" if out else "no deny"))
    by_depth = {}
    for depth, _length in scans:
        by_depth[depth] = by_depth.get(depth, 0) + 1
    print("_scan calls: %d; by depth %s" % (len(scans), dict(sorted(by_depth.items()))))
    stream = io.StringIO()
    pstats.Stats(prof, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(top)
    print("\n".join(line for line in stream.getvalue().splitlines() if line.strip())[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
