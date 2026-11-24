#!/usr/bin/env python3
"""
Check the agent guard 1.4.0 claim that ``brace_expand`` (used for Glob, Grep and Serena patterns) is unchanged: run
the base and the staged module's ``brace_expand`` on the same words and compare every result.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py (brace_expand)

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_brace_expand_diff.py <base guard> <staged guard> <tests dir>
        <out.json>

Pure string work in process: the two guard copies are imported as modules (their hook code runs only under
``__main__``), and nothing is executed beyond ``brace_expand``.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def outcome(module, text: str):
    try:
        return ["ok", module.brace_expand(text)]
    except module.MalformedInput as exc:
        return ["refused", str(exc)[:80]]
    except RecursionError:
        return ["recursion", ""]


def main(argv: list) -> int:
    base, new = load(argv[1], "guard_base_mod"), load(argv[2], "guard_new_mod")
    words = set()
    for name in ("test_claude_agent_guard.py", "test_claude_agent_guard_brace_cap.py"):
        for node in ast.walk(ast.parse((Path(argv[3]) / name).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 400:
                words.add(node.value)
    alphabet = "{},.a$()`\"'\\ 1-"
    for length in range(1, 6):
        for combo in itertools.product("{},.a\\", repeat=length):
            words.add("".join(combo))
    rng = random.Random(20261123)
    for _ in range(30000):
        words.add("".join(rng.choice(alphabet) for _ in range(rng.randint(1, 14))))
    diffs = []
    for text in sorted(words):
        a, b = outcome(base, text), outcome(new, text)
        if a != b:
            diffs.append({"text": text, "base": a, "new": b})
    Path(argv[4]).write_text(json.dumps({"words": len(words), "differences": len(diffs), "examples": diffs[:20]}, indent=1) + "\n", encoding="utf-8")
    print("words %d, differences %d" % (len(words), len(diffs)))
    for d in diffs[:5]:
        print(json.dumps(d)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
