"""Drift gate: the shared ``/ws/training`` resume answer table is byte-identical in juniper-ml and juniper-cascor.

juniper-service-core's ``/ws/training`` handler is the de-cascored core of juniper-cascor's, and the two answer a
resume frame the same way (juniper-cascor#754's four cursor rules, taken by service-core on the owner's rulings of
2026-11-12 and 2026-11-13). One table of resume frames and the answers a client reads off the wire, per server
state, holds that: it is DATA, not code, and each repository keeps a copy that its own test drives its own handler
against over a real WebSocket:

- juniper-ml: ``juniper-service-core/tests/fixtures/ws_resume_answers.json``, driven by
  ``juniper-service-core/tests/test_websocket_resume_answer_table.py``;
- juniper-cascor: ``src/tests/fixtures/ws_resume_answers.json``, driven by
  ``src/tests/unit/api/test_websocket_resume_answer_table.py``.

So a handler whose answer to any row changes fails its own repository's suite, and a row edited in one copy
without its handler fails there too. What neither suite can see is a deliberate one-sided change, the row and
the handler edited together in one repository: that is this gate. It compares the two copies byte for byte.
There is no legitimate divergence to tolerate (the table names, in its ``not_compared`` list, every field that
differs between the services, and neither test compares those), so a whole-file comparison is the right check
here, where ``test_service_fork_drift.py`` needs named markers.

Cadence and gating mirror ``test_service_fork_drift.py``: the comparison runs under ``GITHUB_ACTIONS=true`` (the
weekly ``docs-full-check`` job clones the siblings; in per-PR ``ci.yml`` no sibling is checked out, so it skips
there) or locally with ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` (the sibling checkout must be at ``origin/main``).
A sibling checkout that is present without the copy FAILS rather than skips: a skip would pass for as long as
the copy stayed deleted. The checks of this checkout's own copy, and the decision function's controls, always run.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

# The repo this file lives in, and its copy. Read from THIS checkout, never from
# ``<ecosystem root>/juniper-ml``: in a session worktree that path is the main checkout.
_SELF_COPY = "juniper-service-core/tests/fixtures/ws_resume_answers.json"
_SIBLING_REPO = "juniper-cascor"
_SIBLING_COPY = "src/tests/fixtures/ws_resume_answers.json"
_THIS_FILE = "tests/test_ws_resume_answer_table_drift.py"

_STATES = ["fresh", "buffered5", "evicted", "disabled"]
_FRAME_COUNT = 60
_LABEL = re.compile(r"resume_ok\(replayed_count=\d+\)|resume_failed\([a-z_]+\)|initial_status|state|initial_metrics\(current_seq=\d+\)|[a-z_]+#\d+|close\(\d+\)")

PASS, SKIP, FAIL = "pass", "skip", "fail"


def _juniper_ml_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_ecosystem_root(start: Path, levels: int = 6) -> Path | None:
    """The nearest ancestor of ``start``, at most ``levels`` up, that holds a ``juniper-cascor`` directory.

    Six levels, as ``test_service_fork_drift.py`` walks, so a nested session worktree
    (``juniper-ml/.claude/worktrees/<name>``) still finds the root four levels up.
    """
    candidate = start
    for _ in range(levels):
        candidate = candidate.parent
        if candidate == candidate.parent:
            break
        try:
            if (candidate / _SIBLING_REPO).is_dir():
                return candidate
        except OSError:
            continue
    return None


def first_difference(mine: str, theirs: str) -> str | None:
    """``None`` when the two texts are identical; otherwise where they first differ, by frame id when they parse."""
    if mine == theirs:
        return None
    try:
        left, right = json.loads(mine), json.loads(theirs)
    except json.JSONDecodeError as error:
        return f"one copy is not valid JSON ({error})"
    if left == right:
        mine_lines, theirs_lines = mine.splitlines(keepends=True), theirs.splitlines(keepends=True)
        line = next((number for number, (a, b) in enumerate(zip(mine_lines, theirs_lines), start=1) if a != b), min(len(mine_lines), len(theirs_lines)) + 1)
        return f"the copies hold the same data but differ in their bytes, first at line {line}"
    for key in sorted(set(left) | set(right)):
        if key != "frames" and left.get(key) != right.get(key):
            return f"the {key!r} section differs"
    left_rows = {row.get("id"): row for row in left.get("frames", [])}
    right_rows = {row.get("id"): row for row in right.get("frames", [])}
    for frame_id in [*left_rows, *(fid for fid in right_rows if fid not in left_rows)]:
        if left_rows.get(frame_id) != right_rows.get(frame_id):
            return f"frame {frame_id!r} differs: here {left_rows.get(frame_id)!r}, there {right_rows.get(frame_id)!r}"
    return "the frames are listed in a different order"


def sibling_copy_verdict(ecosystem_root: Path | None, mine: str) -> tuple[str, str]:
    """``(PASS|SKIP|FAIL, why)`` for juniper-cascor's copy against this checkout's text ``mine``."""
    if ecosystem_root is None or not (ecosystem_root / _SIBLING_REPO).is_dir():
        return SKIP, f"no {_SIBLING_REPO} checkout beside this one (per-PR CI clones no sibling; the weekly docs-full-check job does)"
    path = ecosystem_root / _SIBLING_REPO / _SIBLING_COPY
    if not path.is_file():
        return FAIL, (f"{_SIBLING_REPO}/{_SIBLING_COPY} does not exist, so the two copies of the shared resume table cannot be compared. " f"Restore it, or remove the table from both repositories and this gate with it. This fails rather than skips on purpose: " f"a skip would pass for as long as the copy stayed deleted.")
    difference = first_difference(mine, path.read_text(encoding="utf-8"))
    if difference is not None:
        return FAIL, (f"{_SELF_COPY} (juniper-ml) and {_SIBLING_REPO}/{_SIBLING_COPY} differ: {difference}. " f"The two copies are one table: change both in the same pair of pull requests, each with its own handler's test.")
    return PASS, ""


class SharedTableStructureTest(unittest.TestCase):
    """This checkout's copy, on every run. No sibling checkout is needed."""

    @classmethod
    def setUpClass(cls):
        cls.path = _juniper_ml_root() / _SELF_COPY
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.table = json.loads(cls.text)

    def test_the_copy_holds_sixty_frames_answered_in_four_states(self):
        self.assertEqual(list(self.table["states"]), _STATES)
        ids = [row["id"] for row in self.table["frames"]]
        self.assertEqual(len(ids), _FRAME_COUNT)
        self.assertEqual(len(set(ids)), _FRAME_COUNT, "frame ids must be unique")
        for row in self.table["frames"]:
            with self.subTest(frame=row["id"]):
                self.assertEqual(list(row["answers"]), _STATES)
                for state, answer in row["answers"].items():
                    self.assertEqual(list(answer), ["handshake", "live"], state)
                    for item in [*answer["handshake"], *answer["live"]]:
                        self.assertIsNotNone(_LABEL.fullmatch(item), (state, item))

    def test_the_copy_names_both_copies_their_tests_and_this_gate(self):
        about = "\n".join(self.table["about"])
        for name in (_SELF_COPY, _SIBLING_COPY, _THIS_FILE, "juniper-service-core/tests/test_websocket_resume_answer_table.py", "src/tests/unit/api/test_websocket_resume_answer_table.py"):
            self.assertIn(name, about)

    def test_the_copy_ends_in_one_newline(self):
        self.assertTrue(self.text.endswith("}\n") and not self.text.endswith("\n\n"))


class SiblingCopyVerdictTest(unittest.TestCase):
    """The decision the cross-repository test makes, on synthetic ecosystem roots. Always runs."""

    @classmethod
    def setUpClass(cls):
        cls.text = (_juniper_ml_root() / _SELF_COPY).read_text(encoding="utf-8")

    def _root_with(self, scratch: Path, sibling_text: str | None) -> Path:
        (scratch / _SIBLING_REPO).mkdir()
        if sibling_text is not None:
            copy = scratch / _SIBLING_REPO / _SIBLING_COPY
            copy.parent.mkdir(parents=True)
            copy.write_text(sibling_text, encoding="utf-8")
        return scratch

    def test_no_sibling_checkout_skips(self):
        self.assertEqual(sibling_copy_verdict(None, self.text)[0], SKIP)
        with tempfile.TemporaryDirectory() as scratch:
            self.assertEqual(sibling_copy_verdict(Path(scratch), self.text)[0], SKIP)

    def test_a_sibling_checkout_without_the_copy_fails(self):
        with tempfile.TemporaryDirectory() as scratch:
            verdict, why = sibling_copy_verdict(self._root_with(Path(scratch), None), self.text)
        self.assertEqual(verdict, FAIL)
        self.assertIn(_SIBLING_COPY, why)

    def test_an_identical_copy_passes(self):
        with tempfile.TemporaryDirectory() as scratch:
            self.assertEqual(sibling_copy_verdict(self._root_with(Path(scratch), self.text), self.text), (PASS, ""))

    def test_a_row_edited_in_one_copy_fails_and_names_the_row(self):
        table = json.loads(self.text)
        row = table["frames"][5]
        row["answers"]["buffered5"]["handshake"] = ["resume_ok(replayed_count=0)"]
        with tempfile.TemporaryDirectory() as scratch:
            verdict, why = sibling_copy_verdict(self._root_with(Path(scratch), json.dumps(table, indent=2) + "\n"), self.text)
        self.assertEqual(verdict, FAIL)
        self.assertIn(repr(row["id"]), why)

    def test_a_copy_that_differs_only_in_its_bytes_fails(self):
        with tempfile.TemporaryDirectory() as scratch:
            verdict, why = sibling_copy_verdict(self._root_with(Path(scratch), self.text.rstrip("\n")), self.text)
        self.assertEqual(verdict, FAIL)
        self.assertIn("same data", why)

    def test_the_root_is_the_nearest_ancestor_holding_the_sibling(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / _SIBLING_REPO).mkdir()
            start = root / "juniper-ml" / ".claude" / "worktrees" / "name"
            start.mkdir(parents=True)
            self.assertEqual(find_ecosystem_root(start), root)
            self.assertIsNone(find_ecosystem_root(start, levels=2))


class CrossRepoCopyIdentityTest(unittest.TestCase):
    """juniper-cascor's copy against this checkout's, where the sibling is checked out."""

    def test_juniper_cascors_copy_is_byte_identical_to_this_one(self):
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override; siblings must be `git pull`ed to origin/main first)")
        juniper_ml_root = _juniper_ml_root()
        verdict, why = sibling_copy_verdict(find_ecosystem_root(juniper_ml_root), (juniper_ml_root / _SELF_COPY).read_text(encoding="utf-8"))
        if verdict == SKIP:
            self.skipTest(why)
        self.assertEqual(verdict, PASS, why)


if __name__ == "__main__":
    unittest.main()
