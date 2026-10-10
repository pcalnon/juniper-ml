#!/usr/bin/env python3
"""Mutation check for tests/test_gitleaks_secret_assignment_rule.py: each breakage of the config must turn it red.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc -- one-off (backup recovery B9 / design P0.5a item 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: .gitleaks.toml; .gitleaksignore; tests/test_gitleaks_secret_assignment_rule.py

A suite that stays green when the thing it guards is broken is a vacuous pass. This copies the suite and the files
it reads into a temporary tree, applies one breakage at a time to that COPY (never to the repository), runs the
suite there, and requires a failure for every mutant and a pass for the unmutated baseline. With --gitleaks the
RealEngine tests run too (GITLEAKS_PARITY_REQUIRED=1), so the binary has to notice each breakage as well.

Usage:
    python3 util/ad-hoc/2026-10-10_gitleaks_rule_mutation_check.py [--gitleaks BIN]
Exit 0 when the baseline passes and every mutant fails; 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 -- runs `python3 -m unittest` with a fixed argv
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITE = "tests/test_gitleaks_secret_assignment_rule.py"
COPIED = (SUITE, ".gitleaks.toml", ".gitleaksignore", ".pre-commit-config.yaml", ".github/workflows/ci.yml")

#: (label, file, old, new) -- `old` must occur exactly once in `file`.
MUTANTS = (
    ("drop [extend] useDefault (the zero-rule config)", ".gitleaks.toml", "[extend]\nuseDefault = true\n", ""),
    ("useDefault = false", ".gitleaks.toml", "[extend]\nuseDefault = true", "[extend]\nuseDefault = false"),
    ("value may not start with a digit (the 2026-09-20 literal did)", ".gitleaks.toml", "([A-Za-z0-9!#", "([A-Za-z!#"),
    ("value class stops at *", ".gitleaks.toml", "[^ \\t\\r\\n\"'`\\\\]{11,}", "[^ \\t\\r\\n\"'`\\\\*]{11,}"),
    ("drop the word boundary (TEST_PASSPHRASE= would fire)", ".gitleaks.toml", "regex = '''\\b(?:", "regex = '''(?:"),
    ("drop the systemd/argv names", ".gitleaks.toml", "|settings-encryption-key|", "|"),
    ("drop a keyword", ".gitleaks.toml", '  "webservice-password",\n', ""),
    ("drop the code allowlist", ".gitleaks.toml", "'''^[a-z_][a-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)+[(\\[]?[)\\],]*$''',", ""),
    ("code allowlist takes a bare name", ".gitleaks.toml", "[(\\[)\\],]+$'''", "[(\\[)\\],]*$'''"),
    ("drop the placeholder words", ".gitleaks.toml", "'''(?i)redacted|change[-_]?me|placeholder|example|dummy|synthetic|fixture|fake|sample''',", ""),
    # Review of ml#2203: the two exemptions that let human passphrases through must stay narrowed.
    ("re-widen the lowercase allowlist to joined words (diceware)", ".gitleaks.toml", "'''^[a-z]+$''',", "'''^[a-z]+(?:[-_.][a-z]+)*$''',"),
    ("re-add a short word-only allowlist", ".gitleaks.toml", "'''^[a-z]+$''',", "'''^[a-z]+$''',\n    '''^[A-Za-z0-9_.\\-]{12,15}$''',"),
    ("a file-scoped ignore", ".gitleaksignore", "6708cb287e346a7ce411f0b3b1372c6654422949:scripts/", "scripts/"),
    ("an ignore group cut off from its class comment", ".gitleaksignore", "# Hash: a juniper-cascor commit SHA passed to a file-content helper.\n", "# Hash: a juniper-cascor commit SHA passed to a file-content helper.\n\n"),
    ("hook rev drifts from CI", ".pre-commit-config.yaml", "rev: v8.24.3", "rev: v8.28.0"),
    ("CI engine drifts from the hook", ".github/workflows/ci.yml", 'GITLEAKS_VERSION: "8.24.3"', 'GITLEAKS_VERSION: "8.28.0"'),
)


def build_tree(dest: Path) -> None:
    for rel in COPIED:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, target)


def run_suite(tree: Path, gitleaks: str | None) -> int:
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    if gitleaks:
        env.update(GITLEAKS_BIN=gitleaks, GITLEAKS_PARITY_REQUIRED="1")
    res = subprocess.run([sys.executable, "-B", "-m", "unittest", SUITE], cwd=tree, env=env, capture_output=True, text=True, check=False)  # nosec B603
    return res.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gitleaks", help="gitleaks binary; when given, the RealEngine tests must run and are mutated too")
    args = ap.parse_args()
    bad = 0
    with tempfile.TemporaryDirectory(prefix="b9-mutation-") as tmp:
        base = Path(tmp) / "baseline"
        build_tree(base)
        rc = run_suite(base, args.gitleaks)
        print(f"{'PASS' if rc == 0 else 'FAIL'}  baseline (unmutated) -> exit {rc}")
        bad += rc != 0
        for i, (label, rel, old, new) in enumerate(MUTANTS):
            tree = Path(tmp) / f"mutant_{i:02d}"
            build_tree(tree)
            text = (tree / rel).read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"ERROR {label}: the text to mutate occurs {text.count(old)} times in {rel}")
                bad += 1
                continue
            (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
            rc = run_suite(tree, args.gitleaks)
            killed = rc != 0
            print(f"{'PASS' if killed else 'FAIL'}  {label} -> exit {rc} ({'caught' if killed else 'SURVIVED'})")
            bad += not killed
    print(f"\n{len(MUTANTS)} mutants; {'all caught' if bad == 0 else f'{bad} problem(s)'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
