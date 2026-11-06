#!/usr/bin/env python3
"""The agent guard's brace expansion stops at exactly 64 alternatives.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``util/claude_agent_guard.py`` expands ``{a,b}`` and ``{1..3}`` so a credential
name hidden in the last alternative is still seen. The expansion is capped at
``MAX_BRACE_ALTERNATIVES`` (64): the last slot of a full list is kept, and one
past the cap is dropped. A numeric range applies that same cap inside
``_brace_range``, including when ``brace_expand`` is asked for a higher limit,
so ``{1..1000000}`` cannot materialize a million strings before the outer cap.

The source word under test does not contain the text ``.ssh``. The raw-command
regex therefore cannot be what denies it; the hit comes from the expanded
alternative.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("claude_agent_guard_brace_cap", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ssh_assembled_at(alternative_count: int) -> str:
    """``alternative_count`` alternatives; the last expands to ``.ssh`` and the source does not contain it."""
    fillers = [f"n{index}" for index in range(alternative_count - 1)]
    return "{" + ",".join(fillers + [".ss"]) + "}h"


class BraceExpansionCapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = _load_guard()
        self.assertEqual(self.guard.MAX_BRACE_ALTERNATIVES, 64)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.analyzer = self.guard.BashAnalyzer(self.guard.Context([self._tmp.name], self._tmp.name))

    def test_last_slot_of_a_full_list_assembles_ssh_and_is_denied(self) -> None:
        word = _ssh_assembled_at(self.guard.MAX_BRACE_ALTERNATIVES)
        self.assertNotIn(".ssh", word)
        expanded = self.guard.brace_expand(word)
        self.assertIn(".ssh", expanded)
        self.assertIn("n0h", expanded)
        hits = self.analyzer.analyze("echo " + word)
        self.assertIn("CRED-PATH-BASH", [hit.rule_id for hit in hits])

    def test_one_past_the_cap_drops_the_assembled_ssh_name(self) -> None:
        word = _ssh_assembled_at(self.guard.MAX_BRACE_ALTERNATIVES + 1)
        self.assertNotIn(".ssh", word)
        expanded = self.guard.brace_expand(word)
        self.assertNotIn(".ssh", expanded)
        self.assertIn("n0h", expanded)
        self.assertLessEqual(len(expanded), self.guard.MAX_BRACE_ALTERNATIVES + 1)
        hits = self.analyzer.analyze("echo " + word)
        self.assertNotIn("CRED-PATH-BASH", [hit.rule_id for hit in hits])

    def test_numeric_range_of_exactly_the_cap_includes_both_ends(self) -> None:
        cap = self.guard.MAX_BRACE_ALTERNATIVES
        ascending = self.guard._brace_range("1", str(cap))
        self.assertEqual(ascending[0], "1")
        self.assertEqual(ascending[-1], str(cap))
        self.assertEqual(len(ascending), cap)
        descending = self.guard._brace_range(str(cap), "1")
        self.assertEqual(descending[0], str(cap))
        self.assertEqual(descending[-1], "1")
        self.assertEqual(len(descending), cap)
        # The range cap holds even when the outer expander is asked for more.
        wide = self.guard.brace_expand("{1.." + str(cap) + "}", limit=cap * 2)
        self.assertIn("1", wide)
        self.assertIn(str(cap), wide)

    def test_numeric_range_one_past_the_cap_drops_the_far_end(self) -> None:
        cap = self.guard.MAX_BRACE_ALTERNATIVES
        ascending = self.guard._brace_range("1", str(cap + 1))
        self.assertEqual(len(ascending), cap)
        self.assertEqual(ascending[-1], str(cap))
        self.assertNotIn(str(cap + 1), ascending)
        descending = self.guard._brace_range(str(cap + 1), "1")
        self.assertEqual(len(descending), cap)
        self.assertEqual(descending[0], str(cap + 1))
        self.assertNotIn("1", descending)
        wide = self.guard.brace_expand("{1.." + str(cap + 1) + "}", limit=cap * 2)
        self.assertIn(str(cap), wide)
        self.assertNotIn(str(cap + 1), wide)


if __name__ == "__main__":
    unittest.main()
