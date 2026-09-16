#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Regression tests for ``util/ad-hoc/2026-09-05_md_structure_check.py`` -- the STANDALONE
structure verifier, which is wired into no CI gate and must not be used as one.

Why a suite for a tool nothing calls: its blind spots were *documented* on 2026-09-08 and
still present on 2026-09-15, and the handoff that carried them forward recorded them as
"DOCUMENTED, NOT FIXED" three times without anyone noticing that C3 had the same defect as
C2. A documented defect is still a defect, and prose in a docstring does not fail when the
behaviour regresses. These tests do.

Each test below pins one of the five fixes, and every fix has a negative control so that
"the check no longer fires" cannot pass for "the check was removed".

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest **is** the gate for that module.
"""

from __future__ import annotations

import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "ad-hoc" / "2026-09-05_md_structure_check.py"

CLEAN_TABLE = "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
BROKEN_TABLE = "| A | B |\n| 1 | 2 |\n"


def _vcs(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120, check=False)  # nosec B603 - fixed argv


def _repo(root: Path) -> None:
    _vcs(root, "init", "-q", "-b", "main")
    _vcs(root, "config", "user.email", "test@example.invalid")
    _vcs(root, "config", "user.name", "Test")
    # required_signatures is fleet-wide, so every Juniper machine sets commit.gpgsign
    # globally and a temp repo inherits it -- making this suite pass or fail on GPG AGENT
    # STATE that no test controls, and green on CI (no key) while red locally. Pinned, as
    # tests/test_markdown_structure_delta.py does for the same reason.
    _vcs(root, "config", "commit.gpgsign", "false")
    _vcs(root, "config", "tag.gpgsign", "false")


def _commit(root: Path, message: str) -> str:
    _vcs(root, "add", "-A")
    _vcs(root, "commit", "-q", "--no-verify", "-m", message)
    return _vcs(root, "rev-parse", "HEAD").stdout.strip()


def _screen(root: Path, *args: str) -> tuple[int, str]:
    """Run the checker as its real CLI, from inside `root`, and return (exit code, output).

    Deliberately a subprocess rather than an import: the exit code IS the contract here --
    four of the five fixes are about a run exiting 0 when it had examined nothing.
    """
    proc = subprocess.run(  # nosec B603 - fixed argv
        [sys.executable, str(MODULE_PATH), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


class VacuousRunsNowRefuseTest(unittest.TestCase):
    """Examining nothing used to print OK and exit 0 -- on four separate paths."""

    def test_an_unresolvable_base_exits_two_before_reading_anything(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text("# D\n\nprose\n", encoding="utf-8")
            _commit(root, "init")
            code, out = _screen(root, "--base", "no/such/ref", "d.md")
        self.assertEqual(code, 2, out)
        self.assertIn("does not resolve", out)

    def test_an_unreadable_path_exits_two_rather_than_certifying_its_siblings(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text("# D\n\nprose\n", encoding="utf-8")
            base = _commit(root, "init")
            code, out = _screen(root, "--base", base, "d.md", "gone.md")
        self.assertEqual(code, 2, out)
        self.assertIn("could not be read", out)

    def test_examining_zero_paths_exits_two(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text("# D\n", encoding="utf-8")
            base = _commit(root, "init")
            # Every argument unreadable: the run has examined nothing at all.
            code, out = _screen(root, "--base", base, "nope.md")
        self.assertEqual(code, 2, out)

    def test_a_clean_run_still_exits_zero(self):
        # Negative control for this whole class: refusing must not become refusing always.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text("# D\n\nprose\n", encoding="utf-8")
            base = _commit(root, "init")
            (root / "d.md").write_text("# D\n\nprose and more\n", encoding="utf-8")
            code, out = _screen(root, "--base", base, "d.md")
        self.assertEqual(code, 0, out)
        self.assertIn("no structural regression", out)


class AddedFileIsCheckedAbsolutelyTest(unittest.TestCase):
    """A file the PR ADDS has no base -- which is not a reason to skip it."""

    def _added(self, body: str) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "seed.md").write_text("# S\n", encoding="utf-8")
            base = _commit(root, "init")
            (root / "new.md").write_text(body, encoding="utf-8")
            return _screen(root, "--base", base, "new.md")

    def test_a_new_file_with_a_headless_table_FAILS(self):
        code, out = self._added(f"# N\n\nprose\n\n{BROKEN_TABLE}")
        self.assertEqual(code, 1, out)
        self.assertIn("C3", out)

    def test_a_new_file_with_an_odd_fence_count_FAILS(self):
        code, out = self._added("# N\n\n```bash\necho hi\n")
        self.assertEqual(code, 1, out)
        self.assertIn("C1", out)

    def test_a_clean_new_file_passes(self):
        # Negative control: absolute checking must not fail every added file.
        code, out = self._added(f"# N\n\nprose\n\n{CLEAN_TABLE}")
        self.assertEqual(code, 0, out)
        self.assertIn("C1/C3 checked absolutely", out)


class MultiplicityAndNonNettingTest(unittest.TestCase):
    """C2/C3 were set membership; C4 was a net count. All three cancelled real damage."""

    def _change(self, before: str, after: str) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text(before, encoding="utf-8")
            base = _commit(root, "init")
            (root / "d.md").write_text(after, encoding="utf-8")
            return _screen(root, "--base", base, "d.md")

    def test_C2_counts_multiplicity_so_duplicated_commands_are_seen(self):
        # The base legitimately carries ONE unfenced command line; the head carries three.
        # Set membership passed this, which is how a duplicated block stayed invisible.
        before = "# D\n\npip install x\n"
        after = "# D\n\npip install x\npip install x\npip install x\n"
        code, out = self._change(before, after)
        self.assertEqual(code, 1, out)
        self.assertIn("C2 2 NEW command line(s)", out)

    def test_C2_does_not_fire_when_the_count_is_unchanged(self):
        # Negative control: an unchanged pre-existing unfenced command is not a finding.
        code, out = self._change("# D\n\npip install x\n", "# D\n\npip install x\n\nmore\n")
        self.assertEqual(code, 0, out)

    def test_C3_counts_multiplicity_like_C2(self):
        # C3 had the identical defect one line below C2 and was not in the documented list.
        before = f"# D\n\n{BROKEN_TABLE}"
        after = f"# D\n\n{BROKEN_TABLE}\nprose\n\n{BROKEN_TABLE}"
        code, out = self._change(before, after)
        self.assertEqual(code, 1, out)
        self.assertIn("C3 1 NEW table row(s)", out)

    def test_C4_reports_a_lost_heading_even_when_another_is_gained(self):
        # The netting defect: one heading lost, one gained, count unchanged, old check silent.
        before = "# D\n\n## Alpha\n\ntext\n\n## Beta\n\ntext\n"
        after = "# D\n\n## Alpha\n\ntext\n\n## Gamma\n\ntext\n"
        code, out = self._change(before, after)
        self.assertEqual(code, 1, out)
        self.assertIn("C4 1 heading(s) LOST", out)
        self.assertIn("Beta", out)

    def test_C4_does_not_fire_when_headings_are_only_added(self):
        # Negative control: gaining headings is not a loss.
        before = "# D\n\n## Alpha\n\ntext\n"
        after = "# D\n\n## Alpha\n\ntext\n\n## Beta\n\ntext\n"
        code, out = self._change(before, after)
        self.assertEqual(code, 0, out)


class CodeyAlternationCoversTheVcsCommandTest(unittest.TestCase):
    """The measured ~7% hole: the VCS command was invisible to the unfenced-command count."""

    def _change(self, before: str, after: str) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "d.md").write_text(before, encoding="utf-8")
            base = _commit(root, "init")
            (root / "d.md").write_text(after, encoding="utf-8")
            return _screen(root, "--base", base, "d.md")

    def test_a_vcs_command_left_outside_a_fence_is_now_reported(self):
        code, out = self._change("# D\n\nprose\n", "# D\n\nprose\n\ngit status\n")
        self.assertEqual(code, 1, out)
        self.assertIn("C2", out)

    def test_an_added_sibling_command_is_reported_too(self):
        code, out = self._change("# D\n\nprose\n", "# D\n\nprose\n\npytest -q\n")
        self.assertEqual(code, 1, out)
        self.assertIn("C2", out)

    def test_ordinary_prose_beginning_with_a_covered_word_is_still_prose(self):
        # Negative control on the alternation's word boundary: the bar for adding a name is
        # that it does not plausibly begin an English sentence. `make` is the standing
        # counterexample already in the list, so pin that it needs the word boundary.
        code, out = self._change("# D\n\nprose\n", "# D\n\nprose\n\nmakeshift solutions\n")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
