"""
Show that tests/test_git_remote_alias_check.py kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up G2 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G2, gate
         G-ALIAS, regressions R-G2a/b/c); util/git_remote_alias_check.py;
         tests/test_git_remote_alias_check.py; util/ad-hoc/2026-10-16_turing_a4_b9_mutation_check.py
         (the pattern this follows)

Each mutant re-introduces one defect into a COPY of the script: a dropped check, a loosened regex,
a loosened mode test, a dry run that writes, an unverified rewrite, hook variables leaking into
foreign checkouts, and so on. The suite then runs against that copy in a scratch tree that mirrors
the repo layout (the suite locates the script relative to its own file).

A mutant is KILLED when the suite fails. The report names the tests that failed. A kill counts as
BEHAVIOURAL when at least one of those tests runs the script; SourceContractTest's pins are static.
The unmutated control must pass, or the run is void.

Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once. Nothing in the repository
is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed behaviourally and the control passed
    1  a mutant survived, a kill was static only, or the control failed
    2  a mutant's anchor text did not occur exactly once (the script changed; update the mutant),
       or setup failed

Usage:
    python3 util/ad-hoc/2026-10-17_turing_g2_mutation_check.py [--jobs N]
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
SCRIPT = "util/git_remote_alias_check.py"
SUITE = "tests/test_git_remote_alias_check.py"
STAGED = (SCRIPT, SUITE, "tests/redacted_env.py")
STATIC_CLASS = "SourceContractTest"
SUITE_TIMEOUT = 1800

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("G1", "origin read through insteadOf (remote get-url)", [('return self(checkout, "config", "--get", "remote.origin.url")', 'return self(checkout, "remote", "get-url", "origin")')]),
    ("G2", "origin regex loosened to a substring match", [(r'return re.fullmatch(rf"git@github_juniper-{n}:{OWNER}/juniper-{n}\.git", url)', r'return re.search(rf"git@github_juniper-{n}:{OWNER}/juniper-{n}\.git", url)')]),
    ("G3", "AddKeysToAgent checked as the config keyword, not ssh -G's value", [('if addkeystoagent != "false":', 'if addkeystoagent == "yes":')]),
    ("G4", "a missing Host block reads as a hostname mismatch", [("if hostname.lower() == alias:", "if False:")]),
    ("G5", "the 600 test loosened to 'no group or other bits' (0400 and 0700 pass)", [("if mode != 0o600:", "if mode & 0o077:")]),
    ("G6", "IdentitiesOnly not checked", [('if identitiesonly != "yes":', "if False:")]),
    ("G7", "--fix --dry-run still rewrites", [("if dry_run:", "if False:")]),
    ("G8", "--fix trusts set-url without re-reading the persisted origin", [('after = reread.stdout.strip() if reread.returncode == 0 else ""', "after = expected")]),
    ("G9", "a hook's GIT_DIR and relatives leak into foreign checkouts", [("return _without(names)", "return dict(os.environ)")]),
    ("G10", "--if-configured counts a commented-out Host line", [("match = _HOST_LINE_RE.fullmatch(raw.strip())", "match = _HOST_LINE_RE.search(raw.strip())")]),
    ("G11", "--if-configured counts an alias inside a trailing comment", [('if pattern.startswith("#"):', "if False:")]),
    ("G12", "--fix rewrites an origin that names another repository", [("if not same_repository(url, name):", "if False:")]),
    ("G13", "an extra identity file is accepted", [("if offered != [want_key]:", "if want_key not in offered:")]),
    ("G14", "a directory inside another repo reads (and --fix rewrites) the parent's origin", [("if os.path.realpath(toplevel) != os.path.realpath(checkout):", "if False:")]),
    ("G15", "a pushurl that bypasses the alias is not checked", [("bad_push = [p for p in pushurls if not is_alias_origin(p, name)]", "bad_push = []")]),
    ("G16", "the key check dropped", [("            check_key(home, name),\n", "")]),
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
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw)
        stage(tree, script_text)
        proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
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
    print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, run_suite(mutated[mutant[0]])), MUTANTS))

    killed = behavioural = 0
    for (mid, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {defect}")
            continue
        killed += 1
        dynamic = [name for name in failures if not name.startswith(f"{STATIC_CLASS}.")]
        behavioural += 1 if dynamic else 0
        shown = ", ".join((dynamic or failures)[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {defect} -- {len(failures)} failing test(s){'' if dynamic else ' (STATIC ONLY)'}: {shown}")

    total = len(MUTANTS)
    print(f"\n{killed} of {total} mutants killed ({behavioural} behaviourally)")
    return 0 if killed == total and behavioural == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
