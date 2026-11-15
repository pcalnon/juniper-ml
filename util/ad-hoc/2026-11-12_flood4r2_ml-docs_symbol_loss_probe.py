#!/usr/bin/env python3
"""
Probe the symbol-loss screen's WEAKENED rule on the line counts the carried docs state.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- investigation (claim evidence for the Cursor flood-4 round-2 docs carrier, draft juniper-ml#2483)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py (``classify_file``)

Imports ``juniper_ci_tools.symbol_loss_check`` from THIS checkout's ``juniper-ci-tools/`` source (an installed
juniper-ci-tools would otherwise shadow it; the report records the module's path) and calls ``py_symbols`` /
``bash_symbols`` / ``classify_file`` / ``apply_waivers`` on sources built here. No git, no subprocess.

Usage: 2026-11-12_flood4r2_ml-docs_symbol_loss_probe.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "juniper-ci-tools"))

from juniper_ci_tools import symbol_loss_check as slc  # noqa: E402  (this checkout's source, ahead of any installed copy)


def python_function(lines: int, name: str = "f") -> str:
    """A function whose source segment is exactly ``lines`` lines: the def line, then the body."""
    body = [f"    v{i} = {i}" for i in range(lines - 2)] + ["    return 0"]
    return f"def {name}():\n" + "\n".join(body[-(lines - 1) :]) + "\n"


def bash_function(lines: int, name: str = "f") -> str:
    return f"{name}() {{\n" + "".join("    echo x\n" for _ in range(lines - 2)) + "}\n"


def python_pair(base_lines: int, head_lines: int) -> dict:
    base = slc.py_symbols(python_function(base_lines))
    head = slc.py_symbols(python_function(head_lines))
    findings = slc.classify_file("tests/x.py", base, head, False)
    return {"base_lines": base["func:f"].lines, "head_lines": head["func:f"].lines, "findings": [{"symbol": f.symbol, "verdict": f.verdict, "severity": f.severity, "detail": f.detail} for f in findings]}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe the symbol-loss screen's WEAKENED rule.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    report: dict = {"module": str(Path(slc.__file__).resolve()), "module_is_this_checkout": str(Path(slc.__file__).resolve()).startswith(str(REPO)), "WEAKEN_RATIO": slc.WEAKEN_RATIO, "WEAKEN_MIN_DELTA": slc.WEAKEN_MIN_DELTA}
    report["products"] = {"0.6*10": 0.6 * 10, "0.6*15": 0.6 * 15, "0.6*7": 0.6 * 7, "0.6*4": 0.6 * 4}
    report["python_pairs"] = {f"{b}->{h}": python_pair(b, h) for b, h in ((10, 6), (7, 3), (15, 10), (7, 4), (7, 2), (4, 3), (10, 7), (5, 1))}

    same_base = slc.py_symbols("def f():\n    a = real()\n    b = other()\n    return a + b\n")
    same_head = slc.py_symbols("def f():\n    a = 0\n    b = 0\n    return a + b\n")
    report["same_length_gutting"] = [f.verdict for f in slc.classify_file("tests/x.py", same_base, same_head, False)]

    decorated = "import functools\n\n\n@functools.cache\ndef f():\n    a = 1\n    b = 2\n    c = 3\n    return a + b + c\n"
    report["decorated_function_lines"] = slc.py_symbols(decorated)["func:f"].lines

    bash_base = slc.bash_symbols(bash_function(10))
    bash_head = slc.bash_symbols(bash_function(6))
    report["bash_10_to_6"] = {"base_lines": bash_base["fn:f"].lines, "head_lines": bash_head["fn:f"].lines, "findings": [{"symbol": f.symbol, "verdict": f.verdict, "severity": f.severity} for f in slc.classify_file("util/x.bash", bash_base, bash_head, True)]}
    two = slc.bash_symbols("a() {\n    echo 1\n    echo 2\n}\nb() { echo 3; }\n")
    report["bash_line_count_is_the_distance_to_the_next_function_or_the_end"] = {key: sym.lines for key, sym in two.items()}

    class_base = "class C:\n    def m(self):\n" + "".join(f"        v{i} = {i}\n" for i in range(8)) + "        return 0\n"
    class_head = "class C:\n    def m(self):\n        return 0\n"
    findings = slc.classify_file("tests/x.py", slc.py_symbols(class_base), slc.py_symbols(class_head), False)
    report["gutted_method"] = [{"symbol": f.symbol, "verdict": f.verdict, "severity": f.severity, "detail": f.detail} for f in findings]

    def waived(tokens: set) -> dict:
        fresh = slc.classify_file("tests/x.py", slc.py_symbols(class_base), slc.py_symbols(class_head), False)
        slc.apply_waivers(fresh, tokens)
        return {f.symbol: f.severity for f in fresh}

    report["waivers"] = {"C.m": waived({"C.m"}), "method:C.m": waived({"method:C.m"}), "C.m + C": waived({"C.m", "C"}), "method:C.m + class:C": waived({"method:C.m", "class:C"})}

    lost = slc.classify_file("tests/x.py", slc.py_symbols(python_function(10)), slc.py_symbols("x = 1\n"), False)
    report["deleted_name"] = [(f.symbol, f.verdict, f.severity) for f in lost]
    twice = slc.classify_file("tests/x.py", slc.py_symbols(python_function(10)), slc.py_symbols(python_function(2) + "\n\n" + python_function(2)), False)
    report["name_twice_at_head"] = [(f.symbol, f.verdict, f.severity) for f in twice]
    const_base = slc.py_symbols("X = (\n    1,\n    2,\n    3,\n    4,\n    5,\n    6,\n    7,\n    8,\n)\nimport os\n")
    const_head = slc.py_symbols("X = (1,)\nimport os\n")
    report["constant_and_import_shrunk"] = [(f.symbol, f.verdict) for f in slc.classify_file("tests/x.py", const_base, const_head, False)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if report["module_is_this_checkout"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
