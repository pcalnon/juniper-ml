#!/usr/bin/env python3
"""
Re-measure tests/test_claude_agent_guard_brace_cap.py's BASH_WORD_CASES on this host's bash: printf only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_r18-guard_bash_words.py (the printf-only bash runner it calls).

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_word_cases_check.py <scratch dir> <out.json>

Loads the suite's BASH_WORD_CASES (each a word as written and the words bash printed for it), asks bash for the
words again through ``bash_words`` (``printf '%s\\037' WORD`` in a scratch home with an empty PATH), and writes
each case whose words differ. The bash version is recorded. Nothing outside <scratch dir> is written.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 -- only `bash --version`
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list) -> int:
    scratch, out = Path(argv[1]).resolve(), Path(argv[2])
    suite = load(ROOT / "tests" / "test_claude_agent_guard_brace_cap.py", "brace_cap_suite")
    runner = load(ROOT / "util" / "ad-hoc" / "2026-11-16_flood4r2_r18-guard_bash_words.py", "bash_words_runner")
    cases = list(suite.BASH_WORD_CASES)
    printed = runner.bash_words([word for word, _ in cases], scratch)
    differ = [{"word": word, "expected": expected, "bash": got} for (word, expected), got in zip(cases, printed) if got.get("exit") != 0 or got.get("words") != expected]
    version = subprocess.run(["bash", "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0]  # nosec B603 B607
    out.write_text(json.dumps({"bash": version, "cases": len(cases), "differ": differ}, indent=1) + "\n", encoding="utf-8")
    print("%s: %d cases, %d differ" % (version, len(cases), len(differ)))
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
