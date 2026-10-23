"""
Show that tests/test_home_path_literal_check.py kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up G5 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G5, gate
         G-PATH, decision D12); util/home_path_literal_check.py; tests/test_home_path_literal_check.py;
         util/ad-hoc/2026-10-17_turing_g2_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of the script: an off-by-one ratchet, an ignored or
file-wide pragma, a narrowed or widened scope, symlinks or untracked files counted, a baseline edit
that is not re-checked against the tree, a dry run that writes, a missing or malformed baseline that
passes silently, and so on. The suite's hermetic classes then run against that copy in a scratch tree
that mirrors the repo layout (the suite locates the script relative to its own file).

TestThisCheckout is left out: it reads this checkout's baseline, pre-commit config and ci.yml, which
the scratch tree does not hold. Every mutant must be killed by the behavioural classes alone.

A mutant is KILLED when the suite fails; the report names the tests that failed. The unmutated
control must pass, or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants
run at once. Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (the script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-20_turing_g5_mutation_check.py [--jobs N]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/home_path_literal_check.py"
SUITE = "tests/test_home_path_literal_check.py"
STAGED = (SCRIPT, SUITE, "tests/redacted_env.py")
CLASSES = ("TestCheck", "TestNamedFiles", "TestEnvironment", "TestUpdateBaseline")
SUITE_TIMEOUT = 900

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("M1", "a count equal to its baseline fails (>= for >)", [("if len(hits) > allowed.get(rel, 0)]", "if len(hits) >= allowed.get(rel, 0)]")]),
    ("M2", "an over-baseline file exits 0", [("        print(FIX)\n        return 1\n", "        print(FIX)\n        return 0\n")]),
    ("M3", "the pragma is ignored", [("if needle in raw and pragma not in raw]", "if needle in raw]")]),
    ("M4", "the pragma exempts the whole file", [("if needle in raw and pragma not in raw]", "if needle in raw and pragma not in data]")]),
    ("M5", ".yml dropped from the scope", [('SCOPE_SUFFIXES = (".bash", ".sh", ".py", ".yml")', 'SCOPE_SUFFIXES = (".bash", ".sh", ".py")')]),
    ("M6", ".github dropped from the scope", [('SCOPE_DIRS = ("util", "scripts", ".github")', 'SCOPE_DIRS = ("util", "scripts")')]),
    ("M7", "a scope directory matches at any depth", [("parts[0] in SCOPE_DIRS", "any(part in SCOPE_DIRS for part in parts[:-1])")]),
    ("M8", "any suffix is in scope", [("rel.endswith(SCOPE_SUFFIXES)", '"." in parts[-1]')]),
    ("M9", "symlinks are counted", [("if not (root / rel).is_symlink() and (root / rel).is_file()]", "if (root / rel).is_file()]")]),
    ("M10", "untracked files are counted", [('"ls-files", "-z", "--"', '"ls-files", "-z", "--cached", "--others", "--"')]),
    ("M11", "naming the baseline does not re-check the whole scope", [("whole = not files or relative(str(baseline), root) in named", "whole = not files")]),
    ("M12", "a path through a symlinked directory falls outside the root", [("real = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))", "real = path")]),
    ("M13", "a below-baseline count prints no NOTE", [("if len(found.get(rel, ())) < n]", "if False]")]),
    ("M14", "--dry-run writes the baseline", [("    elif dry_run:\n", "    elif False:\n")]),
    ("M15", "--update-baseline rewrites an unchanged file", [("    if text == current:\n", "    if False:\n")]),
    ("M16", "--update-baseline records zero counts", [("        if hits:\n            found[rel] = hits\n", "        found[rel] = hits\n")]),
    ("M17", "a missing baseline passes as empty", [('raise EnvError(f"baseline {path} not found; create it with --update-baseline") from None', "return {}")]),
    ("M18", "a boolean count is accepted", [("isinstance(n, int) and not isinstance(n, bool) and n > 0", "isinstance(n, int) and n > 0")]),
    ("M19", "a zero count is accepted", [("isinstance(n, int) and not isinstance(n, bool) and n > 0", "isinstance(n, int) and not isinstance(n, bool) and n >= 0")]),
    ("M20", "a failed git ls-files reads as an empty scope", [("    if proc.returncode != 0:\n        raise EnvError", "    if False:\n        raise EnvError")]),
    ("M21", "undecodable bytes crash the check", [('raw.decode("utf-8", "replace")', 'raw.decode("utf-8")')]),
    ("M22", "--update-baseline accepts FILE arguments", [('        parser.error("--update-baseline always recounts the whole scope; drop the FILE arguments")\n', "        pass\n")]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, script_text: str | None = None) -> None:
    """Mirror the files the suite needs; optionally replace the script with a mutant."""
    for rel in STAGED:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)
    if script_text is not None:
        (tree / SCRIPT).write_text(script_text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(script_text: str | None) -> tuple[bool, list[str], str]:
    module = SUITE[:-3].replace("/", ".")
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw)
        stage(tree, script_text)
        proc = subprocess.run([sys.executable, "-m", "unittest", *(f"{module}.{cls}" for cls in CLASSES)], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, failed_tests(output), output


def mutate(original: str, edits: list[tuple[str, str]]) -> str | None:
    mutated = original
    for anchor, replacement in edits:
        if mutated.count(anchor) != 1:
            return None
        mutated = mutated.replace(anchor, replacement)
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="mutants to run at once (default: up to 4)")
    args = parser.parse_args()

    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    mutated: dict[str, str] = {}
    for mid, _, edits in MUTANTS:
        text = mutate(original, edits)
        if text is None or text == original:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {SCRIPT}; update the mutant")
            return 2
        mutated[mid] = text

    passed, failures, output = run_suite(None)
    if not passed:
        print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT}: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {SUITE} ({', '.join(CLASSES)}) passes on the unmutated {SCRIPT}")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, run_suite(mutated[mutant[0]])), MUTANTS))

    killed = 0
    for (mid, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {defect}")
            continue
        killed += 1
        shown = ", ".join(failures[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {defect} -- {len(failures)} failing test(s): {shown}")

    print(f"\n{killed} of {len(MUTANTS)} mutants killed")
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
