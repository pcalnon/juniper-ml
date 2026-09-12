#!/usr/bin/env python3
"""One-shot: add the docs/REFERENCE.md <-> ci.yml drift gate to the wiring-drift suite.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "tests" / "test_ci_test_wiring_drift.py"
ANCHOR = '''class ExtractorTest(unittest.TestCase):
    """Negative controls. A gate that cannot fail is not a gate."""'''

NEW = '''class OperatorListMatchesCiTest(unittest.TestCase):
    """The THIRD edge: the OPERATOR-FACING list must agree with ci.yml's.

    The two gates above pin ``tests/`` against ``ci.yml`` in both directions, so a suite
    cannot exist unwired and cannot be invoked without existing. Nothing pinned the list a
    HUMAN reads, and it drifted badly: on 2026-09-11 ``AGENTS.md`` named 115 of 164 gated
    suites -- 49 missing. A successor runs that block, sees every command pass, and
    reasonably concludes the area is green while 49 suites were never in what they ran.
    That is the ml#1254 / ml#1259 "indistinguishable from passing" failure one step further
    out: not a suite CI forgets, but a suite the human is never told to run.

    ml#1886 fixed the instance by RELOCATING the list to ``docs/REFERENCE.md``, because
    completing it in place left 534 chars of headroom under ``AGENTS.md``'s 38000-char
    memory-file ceiling -- below what a single docs PR has cost -- and
    ``conf/memory_budget.json`` says the answer to bulk in an always-loaded file is
    demotion, not growth. This gate pins the destination so it cannot drift the same way.

    WHY THE GATE LIVES HERE rather than in a new file: ``tests/`` and ``ci.yml`` are
    hand-reconciled, and a brand-new suite must be wired into ``ci.yml`` by hand or it
    never runs -- which is the very defect this file exists to catch. Adding a class to an
    already-wired suite sidesteps that bootstrap entirely.
    """

    DOC = "docs/REFERENCE.md"

    @classmethod
    def setUpClass(cls):
        cls.root = _repo_root()
        ci = (cls.root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        cls.invoked = sorted(set(_invoked_suites(_regression_run_script(ci))))
        cls.listed = sorted(set(_invoked_suites(
            (cls.root / cls.DOC).read_text(encoding="utf-8")
        )))

    def test_the_extraction_found_something(self):
        """Guard the guard, and it is not hypothetical here.

        A rename of the document, or a reformat of the command block into a table, empties
        this list and makes BOTH assertions below vacuously true -- the exact shape this
        file was written to prevent. The list has moved once already (AGENTS.md ->
        docs/REFERENCE.md, ml#1886), so a future move is the expected case, not a remote
        one; when it happens this assertion fails loudly instead of the gate going quiet.
        """
        self.assertGreater(
            len(self.listed), 50,
            f"extracted {len(self.listed)} invocations from {self.DOC} -- the extractor is "
            "broken, or the list moved again. Both assertions below would be vacuous.",
        )

    def test_every_ci_suite_is_in_the_operator_list(self):
        missing = sorted(set(self.invoked) - set(self.listed))
        self.assertEqual(
            missing, [],
            f"suites gated by ci.yml but ABSENT from {self.DOC}'s run-all-tests block:\\n"
            + "\\n".join(f"  {m}" for m in missing)
            + f"\\n\\nAn operator who runs that block believes they ran the suite. Add "
            f"`python3 -m unittest -v tests/<name>` to {self.DOC}.",
        )

    def test_the_operator_list_names_no_suite_ci_does_not_run(self):
        """The other direction, and NOT symmetric with the one above.

        A suite listed here that ci.yml does not gate is a command a successor will run and
        trust while no gate enforces it -- worse than an omission, because it reads as
        coverage. It also catches a doc that documents a suite before the suite lands.
        """
        extra = sorted(set(self.listed) - set(self.invoked))
        self.assertEqual(
            extra, [],
            f"{self.DOC} tells an operator to run suites ci.yml does not gate:\\n"
            + "\\n".join(f"  {e}" for e in extra)
            + "\\n\\nEither wire them in ci.yml or drop them from the document.",
        )


'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "OperatorListMatchesCiTest" in src:
        print("already applied")
        return 0
    if src.count(ANCHOR) != 1:
        print(f"REFUSING: anchor found {src.count(ANCHOR)} times (expected 1)", file=sys.stderr)
        return 1
    TARGET.write_text(src.replace(ANCHOR, NEW + ANCHOR), encoding="utf-8")
    print(f"applied to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
