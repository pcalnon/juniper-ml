#!/usr/bin/env python3
"""Exercise the PR's correction script's build() without git: is --check re-runnable, and is its proof sound?

Scratch instrument for round-2 Lane B. Loads the head copy of
util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py from the extracted PR tree (never the
worktree), and:

  A. build(base primer) must reproduce the head primer byte-for-byte (what --check proved pre-commit);
  B. build(head primer) -- what `git show HEAD:` returns on the PR branch after commit, and on main
     after merge -- shows whether --check can re-verify the committed artifact;
  C. negative control on the script's own "none moved" proof: put a newline inside one declared
     replacement and see whether build() still prints "none moved" while the output gains a line;
  D. the same with `python -O` semantics: assert statements are the proof, and -O removes them.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "head/util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py"
base = (HERE / "primer_base.md").read_text(encoding="utf-8")
head = (HERE / "primer_head.md").read_text(encoding="utf-8")


def load():
    spec = importlib.util.spec_from_file_location("corr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = load()
print("A. build(base) == head primer:", end=" ")
out = mod.build(base)
print(out == head)

print("B. build(head):", end=" ")
try:
    mod.build(head)
    print("returned (unexpected)")
except SystemExit as e:
    print("SystemExit ->", str(e)[:110])

print("C. newline smuggled into one declared rewrite:")
mod = load()
i = next(k for k, s in enumerate(mod.SUBS) if s[0] == 3639)
ln, old, new = mod.SUBS[i]
mod.SUBS[i] = (ln, old, new + "\n")
try:
    out = mod.build(base)
    n_before_appendix = out.split("\n## Appendix E")[0].count("\n")
    print("   build() completed; lines before Appendix E heading:", n_before_appendix, "(base has 9866 + 1 blank)")
except SystemExit as e:
    print("   SystemExit ->", str(e)[:120])
except AssertionError as e:
    print("   AssertionError", e)
sys.exit(0)
