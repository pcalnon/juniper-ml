"""Show that R55's paragraph check is not vacuous: it fails on each mutant of the sentence and passes the controls.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4's ruling 48 (the Overtoad, 2026-11-24; R55 of
    notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md);
    tests/test_pyproject_extras.py ReferenceCompatibilityMatrixTest.test_paragraph_states_that_the_current_row_tracks_pyproject

Each case copies the files the suite reads into its own tree under the checkout's ``tmp/`` (the suite locates the
repository root from its own path), edits that copy of ``docs/REFERENCE.md``, and runs the suite there. Nothing in the
checkout is modified. A mutant must fail the new test; a control must pass it, and every case must leave the suite's
other tests as they are on the unmutated copy.

Usage: python3 util/ad-hoc/2026-11-24_flood4_s11_r55_mutation_check.py [--out tmp/flood4/session11/r55-mut]
Exit 0 when every mutant fails the new test and every control passes it; 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEW_TEST = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest.test_paragraph_states_that_the_current_row_tracks_pyproject"
SUITE = "tests.test_pyproject_extras"
FILES = ("pyproject.toml", "AGENTS.md", "README.md", "docs/QUICK_START.md", "docs/REFERENCE.md", "tests/test_pyproject_extras.py")
SENTENCE_START = "Between a PR that changes one of these pins and the release that publishes it,"
SENTENCE_END = "fails until it does."


def _sentence(text: str) -> str:
    start = text.index(SENTENCE_START)
    end = text.index(SENTENCE_END, start) + len(SENTENCE_END)
    return text[start:end]


def _drop(text: str) -> str:
    """M1: the sentence is gone from the paragraph."""
    s = _sentence(text)
    return text.replace(s + " ", "", 1)


def _move(text: str) -> str:
    """M2: the sentence leaves the paragraph for the release-train section, where the same rule is also told."""
    s = _sentence(text)
    text = text.replace(s + " ", "", 1)
    anchor = "Each cut from 0.11.0 to 0.11.4 rewrote whichever of these sites moved"
    assert text.count(anchor) == 1
    return text.replace(anchor, s + " " + anchor, 1)


def _reword(text: str) -> str:
    """M3: one word of the rule changes (track -> follow)."""
    s = _sentence(text)
    assert s.count(" track `pyproject.toml`") == 1
    return text.replace(s, s.replace(" track `pyproject.toml`", " follow `pyproject.toml`"), 1)


def _no_heading(text: str) -> str:
    """M4: the section heading the paragraph is read from is renamed."""
    assert text.count("\n## Ecosystem Compatibility\n") == 1
    return text.replace("\n## Ecosystem Compatibility\n", "\n## Ecosystem Pins\n", 1)


def _rewrap(text: str) -> str:
    """C1 (control): the paragraph is re-wrapped inside the sentence; the words are the same."""
    s = _sentence(text)
    return text.replace(s, s.replace(" the current series' row ", "\nthe current series' row ", 1), 1)


def _identity(text: str) -> str:
    """C0 (control): the unmutated copy."""
    return text


CASES = (
    ("C0_identity", _identity, True),
    ("C1_rewrap", _rewrap, True),
    ("M1_drop", _drop, False),
    ("M2_move_out_of_paragraph", _move, False),
    ("M3_reword_track_to_follow", _reword, False),
    ("M4_heading_renamed", _no_heading, False),
)


def _run(tree: Path, target: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", target], cwd=tree, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def _others(output: str) -> str:
    """The suite's summary line, e.g. 'Ran 21 tests' / 'FAILED (failures=1)'."""
    ran = re.search(r"Ran \d+ tests?", output)
    tail = output.strip().splitlines()[-1] if output.strip() else ""
    return f"{ran.group(0) if ran else '?'} / {tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", default="tmp/flood4/session11/r55-mut", help="directory for the case trees (under the checkout's tmp/)")
    args = parser.parse_args()
    out = (REPO / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    reference = (REPO / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    ok = True
    for name, mutate, should_pass in CASES:
        tree = out / name
        if tree.exists():
            shutil.rmtree(tree)
        (tree / ".github" / "workflows").mkdir(parents=True)
        for rel in FILES:
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, tree / rel)
        mutated = mutate(reference)
        if name != "C0_identity" and mutated == reference:
            print(f"{name}: MUTATION DID NOT APPLY")
            ok = False
            continue
        (tree / "docs" / "REFERENCE.md").write_text(mutated, encoding="utf-8")
        code, output = _run(tree, NEW_TEST)
        suite_code, suite_output = _run(tree, SUITE)
        passed = code == 0
        verdict = "as expected" if passed == should_pass else "UNEXPECTED"
        if passed != should_pass:
            ok = False
        (tree / "new_test.log").write_text(output, encoding="utf-8")
        (tree / "suite.log").write_text(suite_output, encoding="utf-8")
        print(f"{name}: new test {'PASS' if passed else 'FAIL'} ({verdict}); suite exit {suite_code}: {_others(suite_output)}")
    print("RESULT:", "every mutant fails, every control passes" if ok else "NOT AS EXPECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
