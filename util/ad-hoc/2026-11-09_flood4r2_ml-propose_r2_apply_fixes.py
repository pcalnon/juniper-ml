#!/usr/bin/env python3
"""Apply the round-2 validators' findings to the flood-4 round-2 "ml-propose" carrier, as exact once-only replacements.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (the Cursor flood-4 round-2 "ml-propose" carrier, second build after validation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; Overtoad ruling "Carry + extend propose.py"; the claims-lens and code-lens findings
         (tmp/flood4r2-val/ml-propose-{claims,code}-lens/findings.json in the orchestrator's worktree);
         tmp/flood4r2/ml-propose/r2/dispositions.json in the carrier's worktree (what each row answers)

Each ``EDITS`` row is ``(finding ids, repo-relative path, old, new)``. ``old`` must occur exactly once in the file
as it stands after the rows before it. A row whose ``new`` is already present was applied by an earlier run and is
reported "already applied" (checked first: an appending row's ``new`` contains its ``old``). Any other miss aborts
the run before a single file is written. Each touched file's sha256 is printed before and after.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-propose_r2_apply_fixes.py --worktree <carrier root> [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

PROPOSE = "util/release_train/propose.py"
TESTS = "tests/test_release_train_propose.py"
REFERENCE = "docs/REFERENCE.md"
CHANGELOG = "CHANGELOG.md"
RUNBOOK = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
PROVE = "util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py"
MUTATE = "util/ad-hoc/2026-11-08_flood4r2_ml-propose_mutation_check.py"
MANIFEST = "util/ad-hoc/2026-11-08_flood4r2_ml-propose_manifest.py"

EDITS: list = []


def edit(ids: str, path: str, old: str, new: str) -> None:
    EDITS.append((ids, path, old, new))


# ── util/release_train/propose.py ────────────────────────────────────────────

edit(
    "claims F2 F4 F5 F15; code F1",
    PROPOSE,
    r'''  * the four ``docs/REFERENCE.md`` sites that name the meta-package's release and the pins it declares,
    which juniper-ml#2507's ``ReferenceCompatibilityMatrixTest`` pins to ``pyproject.toml`` (step 5b-v): the
    "Package Overview" **Version** cell, the "`juniper-ml` X.Y.Z declares the following pins" sentence, the
    compatibility matrix's current-series row, and the "X.Y.Z sets them to" clause, the only record of the
    three ``[recurrence]`` pins. A new minor ADDS its ``0.N.x`` row and never rewrites the previous series'
    row, which describes published releases; a patch rewrites its own series' row in place. All four are
    rendered from the ``pyproject.toml`` the proposal leaves behind, so an escaping in-repo pin with a matrix
    column moves its cell too. Every cut from 0.11.0 to 0.11.4 wrote them with a one-off script. The
    paragraph's history (which release raised which floor) stays a REVIEW item on the co-change checklist:
    no gate reads it, and the train never writes it;''',
    r'''  * the four ``docs/REFERENCE.md`` sites that name the meta-package's release and the pins it declares,
    which ``ReferenceCompatibilityMatrixTest`` (added by juniper-ml#2507's tests, carried in the round-2
    tests carrier) pins to ``pyproject.toml`` (step 5b-v): the "Package Overview" **Version** cell, the
    "`juniper-ml` X.Y.Z declares the following pins" sentence, the compatibility matrix's current-series
    row, and the "X.Y.Z sets them to" clause, the only record of the three ``[recurrence]`` pins. A new
    minor ADDS its ``0.N.x`` row and never touches the previous series' row, which should describe
    published releases; a column pin that moved since that series' last release rewrote it in place (the
    gate makes it), so the checklist asks the reviewer to restore it. A patch rewrites its own series' row
    in place. All four are rendered from the ``pyproject.toml`` the proposal leaves behind, so an escaping
    in-repo pin with a matrix column moves its cell too. Every cut from 0.11.0 to 0.11.4 rewrote whichever
    of them moved with a one-off script. The paragraph's history (which release raised which floor) stays
    a REVIEW item on the co-change checklist: no gate reads it, the train never writes it, and renaming the
    clause's release hands any words after its pins to the new release;''',
)

edit(
    "claims F5",
    PROPOSE,
    r'''# ``pyproject.toml`` decides. juniper-ml#2507's ``ReferenceCompatibilityMatrixTest`` pins each one:''',
    r'''# ``pyproject.toml`` decides. ``ReferenceCompatibilityMatrixTest`` in tests/test_pyproject_extras.py (added by
# juniper-ml#2507's tests, carried in the round-2 tests carrier) pins each one:''',
)

edit(
    "claims F1 F2 F4 F10 F15; code F1 F3",
    PROPOSE,
    r'''# Every juniper-ml cut from 0.11.0 to 0.11.4 moved them by hand with a one-off script
# (util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py and its four successors). Each helper below keeps
# the ``set_agents_version`` honesty contract: an anchor that is absent, or present more than once (which the
# gate refuses too), returns the text untouched with ``old=None`` (``absent`` / ``unexpected`` for the matrix
# row), never a half-edit. The paragraph's HISTORY -- which release raised which floor, "The `0.N.x` row is
# X's" -- is prose no gate reads. The train never writes it, and the co-change checklist asks the reviewer to.
#
# The series rule. A NEW series (the first proposal of a minor or a major) gets a NEW row, rendered from
# pyproject.toml and appended below the newest one. The previous series' row is never renamed or rewritten:
# it describes releases already on PyPI. That is the rule #1991 stated when it added the 0.8.x row "rather than
# rewritten", and the shape of the 0.11.0 cut (#2306). A release inside the current series (a patch) rewrites
# that series' row in place, as the 0.11.1 and 0.11.2 cuts did (#2319, #2339), and the prose records what the
# earlier patches published.''',
    r'''# Every juniper-ml cut from 0.11.0 to 0.11.4 rewrote whichever of them moved, by hand, with a one-off script
# (util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py and its four successors). Each helper below keeps
# the ``set_agents_version`` honesty contract: an anchor that is absent, or present more than once (the gate
# refuses a doubled cell, sentence or clause; it keeps the last of two series rows), returns the text
# untouched with ``old=None`` (``absent`` / ``unexpected`` for the matrix row), never a half-edit. The
# paragraph's HISTORY -- which release raised which floor, "The `0.N.x` row is X's" -- is prose no gate
# reads. The train never writes it, and the co-change checklist asks the reviewer to. Renaming the clause's
# release also hands any words after its pins (": it raises ...") to the new release, so the checklist names
# the clause whenever it moves.
#
# The series rule. A NEW series (the first proposal of a minor or a major) gets a NEW row, rendered from
# pyproject.toml and appended below the newest one. The previous series' row is never renamed or rewritten by
# the train (the checklist asks the reviewer to restore it if a PR rewrote it in place since its last
# release): it should describe releases already on PyPI. That is the rule #1991 stated when it added the 0.9.x
# row: the 0.8.x row is "ADDED TO rather than rewritten", and the shape of the 0.11.0 cut (#2306). It holds
# unless a column pin moved since that series' last release: ReferenceCompatibilityMatrixTest makes such a move
# (an escaping in-repo pin, or a hand floor raise) rewrite the then-current row in place. A release inside the
# current series (a patch) rewrites that series' row in place, as the 0.11.1 and 0.11.2 cuts did (#2319,
# #2339), and the prose records what the earlier patches published.''',
)

edit(
    "claims F2; code F1",
    PROPOSE,
    r'''      in the header's column widths is appended below the newest row, which stays as it is: it describes
      releases already on PyPI (the series rule above).''',
    r'''      in the header's column widths is appended below the newest row, which the train never touches (the
      series rule above: the checklist asks the reviewer to check it).''',
)

edit(
    "claims F4; code F5 (the release the clause note names)",
    PROPOSE,
    r'''"recurrence": "absent", "series": None, "moved": []''',
    r'''"recurrence": "absent", "version": None, "series": None, "moved": []''',
)

edit(
    "claims F4; code F5",
    PROPOSE,
    r'''    :func:`set_reference_matrix_row` status. It also holds what the co-change checklist names: the row's
    ``series``, its ``moved`` cells (``pkg: old -> new``, for an in-place edit) and the pins the clause held
    before (``recurrence_old``). Rendered from the FINAL pyproject text, so the meta's own bump names its
    ``to_version``, and an escaping in-repo pin's raised ceiling reaches that package's matrix column."""''',
    r'''    :func:`set_reference_matrix_row` status. It also holds what the co-change checklist names: the release
    (``version``), the row's ``series``, its ``moved`` cells (``pkg: old -> new``, for an in-place edit) and
    the pins the clause held before (``recurrence_old``). Rendered from the FINAL pyproject text, so the
    meta's own bump names its ``to_version``, and an escaping in-repo pin's raised ceiling reaches that
    package's matrix column."""''',
)

edit(
    "claims F4; code F5",
    PROPOSE,
    r'''    series = _series_label(version)
    report["series"] = series''',
    r'''    series = _series_label(version)
    report["version"] = version
    report["series"] = series''',
)

edit(
    "claims F2 F4; code F1 F5 F7",
    PROPOSE,
    r'''    At most three: what the train moved (included), what it could not (REQUIRED: on the meta's own bump every
    site, otherwise only a matrix row a moved pin could not be rendered into), and the paragraph's history,
    which no gate reads and the train never writes (REVIEW: on the meta's own bump, and after any in-place row
    edit). ``report`` is ``None`` for a package outside juniper-ml."""''',
    r'''    At most three: what the train moved (included), what it could not (REQUIRED: on the meta's own bump every
    site, otherwise only a matrix row a moved pin could not be rendered into), and the paragraph's history,
    which no gate reads and the train never writes (REVIEW: on the meta's own bump, and whenever a site moved).
    The REVIEW line names what to check: a row moved in place, a clause that now names this release or holds
    new pins (words after its pins describe whatever it names), and, on a new series, the previous series'
    row, which the train never touches but a PR since that series' last release may have rewritten in place.
    ``report`` is ``None`` for a package outside juniper-ml."""''',
)

edit(
    "claims F2; code F1",
    PROPOSE,
    r'''            done.append(f"a new `{series}` matrix row (the older rows stay: they describe published releases)")''',
    r'''            done.append(f"a new `{series}` matrix row (the older rows are not touched)")''',
)

edit(
    "claims F2 F4 F12; code F1 F5 F7",
    PROPOSE,
    r'''    if meta_bump or report.get("matrix_row") == "edited":
        notes = ["the train renders the release, the pins and the current series' row, and never the paragraph's history (which release raised which floor, and \"The `0.N.x` row is X's\")"]
        if report.get("matrix_row") == "edited":
            notes.append(f"the `{series}` row moved in place, so record what the earlier {series} releases published")
        if report.get("recurrence_moved"):
            notes.append("the [recurrence] pins moved (the clause held " + ", ".join(f"`{pin}`" for pin in report.get("recurrence_old") or []) + "), so record those as history")
        items.append("docs/REFERENCE.md \"Ecosystem Compatibility\" prose (REVIEW by hand in this PR): " + "; ".join(notes) + " -- util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py is the latest cut's wording.")''',
    r'''    if meta_bump or done:
        notes = ["the train renders the release, the pins and the current series' row, and never the paragraph's history (which release raised which floor, and \"The `0.N.x` row is X's\")"]
        if report.get("matrix_row") == "edited":
            notes.append(f"the `{series}` row moved in place, so record what the earlier {series} releases published")
        if report.get("matrix_row") == "added":
            notes.append("the previous series' row is not touched: if a PR since that series' last release rewrote it in place (an escaping column pin, or a hand floor raise that ReferenceCompatibilityMatrixTest made move the then-current row), restore the pins that series published")
        if report.get("recurrence") == "edited":
            named = report.get("version")
            notes.append(f"the [recurrence] clause now names {named}, so words after its pins that say what a release changed (': it raises ...') now describe {named}: reword them, or move them into the history")
        if report.get("recurrence_moved"):
            notes.append("the [recurrence] pins moved (the clause held " + ", ".join(f"`{pin}`" for pin in report.get("recurrence_old") or []) + "), so record those as history")
        items.append("docs/REFERENCE.md \"Ecosystem Compatibility\" prose (REVIEW by hand in this PR): " + "; ".join(notes) + " -- util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py is the 0.11.4 cut's wording.")''',
)

# ── tests/test_release_train_propose.py ──────────────────────────────────────

edit(
    "claims F5; code F1 F5",
    TESTS,
    r'''  * docs/REFERENCE.md's four release sites (step 5b-v; juniper-ml#2507's ``ReferenceCompatibilityMatrixTest``
    pins them): the Package Overview **Version** cell, the "declares the following pins" sentence, the
    current series' matrix row and the [recurrence] "sets them to" clause. A patch rewrites its series' row in
    place, a new minor ADDS a row and never rewrites the previous series', an escaping pin with a matrix
    column moves its cell in the one REFERENCE edit, an absent or doubled site is never invented or guessed
    at (REQUIRED on the meta's own bump), and every anchor is found in the live file''',
    r'''  * docs/REFERENCE.md's four release sites (step 5b-v; ``ReferenceCompatibilityMatrixTest``, added by
    juniper-ml#2507's tests and carried in the round-2 tests carrier, pins them): the Package Overview
    **Version** cell, the "declares the following pins" sentence, the current series' matrix row and the
    [recurrence] "sets them to" clause. A patch rewrites its series' row in place, a new minor ADDS a row and
    never touches the previous series' (the REVIEW line names it), an escaping pin with a matrix column moves
    its cell in the one REFERENCE edit, an absent or doubled site is never invented or guessed at (REQUIRED
    on the meta's own bump), a moved clause is named for review, and every anchor is found in the live file''',
)

edit(
    "claims F5",
    TESTS,
    r'''# docs/REFERENCE.md's four RELEASE sites -- the ones juniper-ml#2507's ReferenceCompatibilityMatrixTest pins to''',
    r'''# docs/REFERENCE.md's four RELEASE sites -- the ones ReferenceCompatibilityMatrixTest (juniper-ml#2507's tests, carried in the round-2 tests carrier) pins to''',
)

edit(
    "claims F5 F15",
    TESTS,
    r'''    Each 0.11.x cut rewrote these four sites with a one-off script, and juniper-ml#2507's tests pin them to
    pyproject.toml.''',
    r'''    Each 0.11.x cut rewrote whichever of these four sites moved with a one-off script, and
    ReferenceCompatibilityMatrixTest (juniper-ml#2507's tests, carried in the round-2 tests carrier) pins them to
    pyproject.toml.''',
)

edit(
    "code F2 (lower-value survivor VM3)",
    TESTS,
    r'''        self.assertEqual(pr.set_reference_version_cell(indented, "0.7.0"), (indented, None), "the gate anchors the row at column 0")''',
    r'''        self.assertEqual(pr.set_reference_version_cell(indented, "0.7.0"), (indented, None), "the gate anchors the row at column 0")
        annotated = "| **Version** | `0.6.0` (pre-release) |\n"
        self.assertEqual(pr.set_reference_version_cell(annotated, "0.7.0"), (annotated, None), "a cell holding text beside its backticked version is not the gate's cell")''',
)

edit(
    "code F2 (lower-value survivor DM3)",
    TESTS,
    r'''        self.assertEqual(pr.set_reference_declares_version(twice, "0.7.0"), (twice, None))''',
    r'''        self.assertEqual(pr.set_reference_declares_version(twice, "0.7.0"), (twice, None))
        no_period = "`juniper-ml` 0.6.0 declares the following pins:\n"
        self.assertEqual(pr.set_reference_declares_version(no_period, "0.7.0"), (no_period, None), "the gate reads the sentence only with its period")''',
)

edit(
    "code F2 (CM4)",
    TESTS,
    r'''        self.assertEqual(pr.set_reference_recurrence_clause(_COMPAT_REFERENCE, "0.7.0", ["juniper-recurrence~=0.5"]), (_COMPAT_REFERENCE, None))''',
    r'''        self.assertEqual(pr.set_reference_recurrence_clause(_COMPAT_REFERENCE, "0.7.0", ["juniper-recurrence~=0.5"]), (_COMPAT_REFERENCE, None))
        self.assertEqual(pr.set_reference_recurrence_clause(_COMPAT_REFERENCE, "0.7.0", [*pins, "juniper-recurrence-model~=0.3"]), (_COMPAT_REFERENCE, None), "one unreadable pin refuses the whole clause")''',
)

edit(
    "code F2 (RM5)",
    TESTS,
    r'''            "a newer series already in the table":''',
    r'''            "a series row wider than the header": (_COMPAT_REFERENCE.replace(_COMPAT_ROW_06, _COMPAT_ROW_06.rstrip("\n") + " extra |\n"), "0.6.1", dict(_COMPAT_SPECS, **{"juniper-observability": ">=0.3.0"})),
            "a newer series already in the table":''',
)

edit(
    "claims F4; code F5 (clause note on the meta's patch)",
    TESTS,
    r'''        self.assertEqual(len(self._items(prop, "prose (REVIEW by hand in this PR)")), 1, "the paragraph's history is the reviewer's")''',
    r'''        review = self._items(prop, "prose (REVIEW by hand in this PR)")
        self.assertEqual(len(review), 1, "the paragraph's history is the reviewer's")
        self.assertIn("the [recurrence] clause now names 0.6.1, so words after its pins", review[0], "the renamed clause hands ': it raises ...' to this release")
        self.assertNotIn("previous series' row", review[0], "a patch adds no row")''',
)

edit(
    "code F1 (assertion + flow test); claims F2",
    TESTS,
    r'''        self.assertTrue(any("a new `0.7.x` matrix row" in item for item in self._items(prop, "(included in this PR)")))

    def test_meta_bump_after_a_recurrence_floor_raise_moves_the_clause(self):''',
    r'''        self.assertTrue(any("a new `0.7.x` matrix row (the older rows are not touched)" in item for item in self._items(prop, "(included in this PR)")))
        review = self._items(prop, "prose (REVIEW by hand in this PR)")
        self.assertEqual(len(review), 1)
        self.assertIn("the previous series' row is not touched: if a PR since that series' last release rewrote it in place", review[0])

    def test_meta_minor_after_an_in_place_row_raise_flags_the_previous_row_for_review(self):
        """The flow ReferenceCompatibilityMatrixTest forces: a hand floor raise between releases must rewrite the
        then-current 0.6.x row in place (here the observability floor), so the next minor adds 0.7.x and leaves
        0.6.x stating a floor no 0.6.x release published. The train cannot tell which pins a series published, so
        the checklist vouches for no older row, and the REVIEW line names the previous series' row."""
        raised_row = "| 0.6.x      | >=0.1.0,<0.2.0     | >=0.3.0               |\n"
        (self.repo_root / "pyproject.toml").write_text(_COMPAT_PYPROJECT.replace("juniper-observability>=0.2.0", "juniper-observability>=0.3.0"))
        (self.repo_root / "docs" / "REFERENCE.md").write_text(_COMPAT_REFERENCE.replace(_COMPAT_ROW_06, raised_row).replace("`>=0.2.0`         |", "`>=0.3.0`         |"))
        prop = self._propose("juniper-ml", "0.7.0")
        ref = self._reference(prop)
        self.assertIn(_COMPAT_ROW_05 + raised_row + "| 0.7.x      | >=0.1.0,<0.2.0     | >=0.3.0               |\n", ref, "the train leaves the previous row as the raise left it")
        self.assertFalse(any("describe published releases" in item for item in prop.co_change_checklist), "the checklist must not vouch for a row the train did not check")
        review = self._items(prop, "prose (REVIEW by hand in this PR)")
        self.assertEqual(len(review), 1)
        self.assertIn("the previous series' row is not touched", review[0])
        self.assertIn("restore the pins that series published", review[0])

    def test_meta_bump_after_a_recurrence_floor_raise_moves_the_clause(self):''',
)

edit(
    "claims F3 F13",
    TESTS,
    r'''        """The 0.11.4 shape (juniper-ml#2482): a hand PR raised a [recurrence] floor, which has no column, and the
        clause is that pin's only record."""''',
    r'''        """The 0.11.4 shape (the raise juniper-ml#2473, then the cut juniper-ml#2482): a hand PR raised a [recurrence]
        floor, which has no column, and the clause is that pin's only record. Under ReferenceCompatibilityMatrixTest
        such a raise is red until it rewrites the clause itself, so this REFERENCE (the clause still at the old pin)
        cannot reach main through a green merge: the test pins the REVIEW note for a REFERENCE that drifted anyway."""''',
)

edit(
    "code F7 (a sub-package proposal that moves only the clause)",
    TESTS,
    r'''        self.assertEqual(self._items(prop, "prose (REVIEW"), [])

    def test_meta_bump_on_a_current_reference_emits_no_reference_edit(self):''',
    r'''        self.assertEqual(self._items(prop, "prose (REVIEW"), [])

    def test_subpackage_bump_that_moves_only_the_clause_gets_the_review_line(self):
        """A sub-package proposal renders the four sites too. On a REFERENCE that drifted from pyproject (a
        [recurrence] floor its clause does not name yet) only the clause moves, and the REVIEW line comes with it:
        a sub-package bump gets one whenever a site moved, not only for an in-place row edit."""
        (self.repo_root / "pyproject.toml").write_text(_COMPAT_PYPROJECT.replace("juniper-recurrence>=0.2.0,<0.5.0", "juniper-recurrence>=0.2.1,<0.5.0"))
        _write_pkg(self.repo_root, "juniper-service-core/", name="juniper-service-core", version="0.4.0", changelog=_CHANGELOG)
        prop = self._propose("juniper-service-core", "0.4.1", path="juniper-service-core/", from_version="0.4.0")
        ref = self._reference(prop)
        self.assertIn("0.6.0 sets them to `juniper-recurrence-model>=0.1.5,<0.3.0` and `juniper-recurrence>=0.2.1,<0.5.0`", ref)
        self.assertIn("| **Version**            | `0.6.0`      |", ref, "a sub-package bump names no new meta release")
        included = self._items(prop, "release sites (included in this PR)")
        self.assertEqual(len(included), 1)
        self.assertIn("sets them to", included[0])
        review = self._items(prop, "prose (REVIEW by hand in this PR)")
        self.assertEqual(len(review), 1, "a moved site always comes with the history review")
        self.assertIn("the [recurrence] clause now names 0.6.0", review[0])
        self.assertIn("the [recurrence] pins moved (the clause held `juniper-recurrence-model>=0.1.5,<0.3.0`, `juniper-recurrence>=0.2.0,<0.5.0`)", review[0])
        self.assertEqual(self._items(prop, "REQUIRED --"), [], "a sub-package bump owes no release site")

    def test_meta_bump_on_a_current_reference_emits_no_reference_edit(self):''',
)

edit(
    "claims F4; code F5 (no clause note when the clause did not move)",
    TESTS,
    r'''        self.assertEqual(self._items(prop, "docs/REFERENCE.md release sites"), [])

    def test_meta_bump_with_a_doubled_site_flags_only_that_one_required(self):''',
    r'''        self.assertEqual(self._items(prop, "docs/REFERENCE.md release sites"), [])
        review = self._items(prop, "prose (REVIEW by hand in this PR)")
        self.assertEqual(len(review), 1, "the meta's own bump always asks for the history review")
        self.assertNotIn("clause now names", review[0], "a clause already at the release was not renamed")
        self.assertNotIn("previous series' row", review[0], "a patch adds no row")

    def test_meta_bump_with_a_doubled_site_flags_only_that_one_required(self):''',
)

edit(
    "code F2 (lower-value survivor LM1)",
    TESTS,
    r'''        self.assertTrue(any("In-repo meta consumer pin" in item for item in prop.co_change_checklist))

    def test_doc_tools_bump_updates_both_extras(self):''',
    r'''        self.assertTrue(any("In-repo meta consumer pin" in item for item in prop.co_change_checklist))
        self.assertEqual([item for item in prop.co_change_checklist if "release sites (REQUIRED" in item], [], "a sub-package bump owes none of the meta's release sites")

    def test_doc_tools_bump_updates_both_extras(self):''',
)

# ── docs/REFERENCE.md ────────────────────────────────────────────────────────

edit(
    "code F1 F2 F5 F7 (Test Suite Reference entry)",
    REFERENCE,
    r'''a patch that moves a floor rewrites its series' row in place, a new minor adds a row and keeps the previous series', and an escaping column pin moves its cell in the one REFERENCE edit. The never-guess cases are left untouched: an unpinned or conflicting column, a doubled row or sentence, a row of the wrong width, a newer series, a version that is not N.N.N. An absent or unreadable site is `REQUIRED` on the meta's own bump, and every anchor is found in the live file.''',
    r'''a patch that moves a floor rewrites its series' row in place, a new minor adds a row and leaves the previous series' alone, and an escaping column pin moves its cell in the one REFERENCE edit. The never-guess cases are left untouched: an unpinned or conflicting column, a doubled row or sentence, a row narrower or wider than the header, a newer series, a version that is not N.N.N, a **Version** cell holding more than the version, a sentence without its period, and a clause with one unreadable pin. An absent or unreadable site is `REQUIRED` on the meta's own bump and never on a sub-package's. The `REVIEW` line comes whenever a site moved: it names a renamed clause (words after its pins now describe the new release) and, on a minor, the previous series' row, which a floor raise since that series' last release may have rewritten in place. Every anchor is found in the live file.''',
)

edit(
    "claims F1 F2 F3 F4 F5 F6 F15; code F1",
    REFERENCE,
    r'''  - This file's four release sites (step 5b-v), which juniper-ml#2507's `ReferenceCompatibilityMatrixTest` pins to `pyproject.toml`: the Package Overview **Version** cell, the "`juniper-ml` X.Y.Z declares the following pins" sentence, the [Ecosystem Compatibility](#ecosystem-compatibility) matrix's current-series row, and the `[recurrence]` "sets them to" clause. They are rendered from the `pyproject.toml` the proposal leaves behind, and they compose with the extras-table true-up into ONE `docs/REFERENCE.md` `FileEdit`. A new minor **adds** its `0.N.x` row and never rewrites the previous series' row, which describes published releases (the #1991 rule; the 0.11.0 cut). A patch rewrites its own series' row in place (the 0.11.1 and 0.11.2 cuts). An absent or doubled site is left untouched and flagged `REQUIRED` on the meta's own bump. The paragraph's history is a checklist `REVIEW` item, never generated. Each cut from 0.11.0 to 0.11.4 wrote these sites with a one-off `util/ad-hoc/*_cut_cochanges.py` script.''',
    r'''  - This file's four release sites (step 5b-v), which `ReferenceCompatibilityMatrixTest` in `tests/test_pyproject_extras.py` (added by juniper-ml#2507's tests, carried in the round-2 tests carrier) pins to `pyproject.toml`: the Package Overview **Version** cell, the "`juniper-ml` X.Y.Z declares the following pins" sentence, the [Ecosystem Compatibility](#ecosystem-compatibility) matrix's current-series row, and the `[recurrence]` "sets them to" clause. They are rendered from the `pyproject.toml` the proposal leaves behind, and they compose with the extras-table true-up into ONE `docs/REFERENCE.md` `FileEdit`. A new minor **adds** its `0.N.x` row and never touches the previous series' row, which should describe published releases (the #1991 rule; the 0.11.0 cut; the checklist asks the reviewer to restore it after an in-place edit). A patch rewrites its own series' row in place (the 0.11.1 and 0.11.2 cuts). An absent or doubled site is left untouched and flagged `REQUIRED` on the meta's own bump. The paragraph's history is a checklist `REVIEW` item, never generated, and renaming the clause's release hands any words after its pins (": it raises ...") to the new release, so the `REVIEW` line names the clause whenever it moves. **A floor raise between releases** (a matrix column or a `[recurrence]` pin) fails `ReferenceCompatibilityMatrixTest` until the same PR rewrites the current series' row or the clause's pins in place (`apply_reference_compat_cochanges` renders both from the raised `pyproject.toml`). A row rewritten that way then states pins no published release of its series carries, and the meta's next proposal finds the sites current, so only the `REVIEW` line's notes prompt the reviewer. A raise that also bumps the version and adds the new series' row (the #1991 shape) keeps every published row true, but that PR must render all four sites itself: the bumped package is `BUMPED_NOT_RELEASED`, which `propose.py` never proposes. Each cut from 0.11.0 to 0.11.4 rewrote whichever of these sites moved with a one-off `util/ad-hoc/*_cut_cochanges.py` script.''',
)

edit(
    "claims F7; code F6",
    REFERENCE,
    r'''Header 0.6.63 and footer 0.6.62 reconciled. |''',
    r'''Header 0.6.63 and footer 0.6.62 reconciled. |
| 0.6.65  | 2026-11-09 | Release-train step 5b-v (Overtoad ruling on juniper-ml#2507, "Carry + extend propose.py"): `propose.py` renders the four Ecosystem Compatibility release sites (the **Version** cell, the "declares" sentence, the current-series row, the `[recurrence]` clause) from `pyproject.toml`. The propose suite gains `ReferenceCompatHelperTest` and `BuildProposalReferenceCompatTest`; the Test Suite Reference and `propose.py` entries describe the step, its `REVIEW` notes and the floor-raise obligation `ReferenceCompatibilityMatrixTest` creates. |''',
)

# ── CHANGELOG.md ─────────────────────────────────────────────────────────────

edit(
    "claims F1 F2 F3 F4 F5 F8 F9 F15; code F1 F3 F4 F5",
    CHANGELOG,
    r'''- **The release-train proposal rewrites the four `docs/REFERENCE.md` sites that name the meta-package's release
  (Overtoad ruling on juniper-ml#2507: "Carry + extend propose.py").** #2507's tests pin the Package Overview Version
  cell, the "`juniper-ml` X.Y.Z declares the following pins" sentence, the Ecosystem Compatibility matrix's
  current-series row and the `[recurrence]` "sets them to" clause to `pyproject.toml`.
  `util/release_train/propose.py` edited none of them, and every cut from 0.11.0 to 0.11.4 wrote them with a
  one-off `util/ad-hoc/*_cut_cochanges.py` script. With those tests carried, every proposal would have failed CI
  until someone edited REFERENCE by hand.
  - New step 5b-v renders the four sites from the `pyproject.toml` the proposal leaves behind:
    `set_reference_version_cell`, `set_reference_declares_version`, `set_reference_matrix_row` and
    `set_reference_recurrence_clause`, composed by `apply_reference_compat_cochanges`. They share one REFERENCE edit
    with the extras-table true-up, so an escaping in-repo pin with a matrix column (doc-tools, ci-tools,
    observability) moves its cell as well.
  - **The series rule.** A new minor adds its `0.N.x` row and never rewrites the previous series' row, which
    describes releases already on PyPI: #1991 added the 0.8.x row "rather than rewritten", and the 0.11.0 cut
    (#2306) did the same. A patch rewrites its own series' row in place, as the 0.11.1 and 0.11.2 cuts did.
  - Each helper keeps `set_agents_version`'s contract: an absent or doubled site is left untouched, and the
    co-change checklist marks it REQUIRED on the meta's own bump. The paragraph's history (which release raised
    which floor) is prose that no gate reads. The train never writes it, and the checklist asks the reviewer to.
  - **Measured on `main`'s files with #2507's tests installed**
    (`util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py`). The unextended script's patch
    proposal fails 3 of #2507's 8 tests, its minor proposal 4, and its proposal after a hand `[recurrence]` floor
    raise 3. All three pass with this change, and none of the 18 suites the simulator runs regresses.
    `tests/test_release_train_propose.py` gains 29 tests (156 to 185), and all 26 mutants of the new code are
    killed. `docs/REFERENCE.md` describes the step.''',
    r'''- **The release-train proposal rewrites the four `docs/REFERENCE.md` sites that name the meta-package's release
  (Overtoad ruling on juniper-ml#2507: "Carry + extend propose.py").** `ReferenceCompatibilityMatrixTest` (added by
  juniper-ml#2507's tests, carried in the round-2 tests carrier) pins the Package Overview Version cell, the
  "`juniper-ml` X.Y.Z declares the following pins" sentence, the Ecosystem Compatibility matrix's current-series
  row and the `[recurrence]` "sets them to" clause to `pyproject.toml`. `util/release_train/propose.py` edited
  none of them, and every cut from 0.11.0 to 0.11.4 rewrote whichever of them moved with a one-off
  `util/ad-hoc/*_cut_cochanges.py` script. With those tests carried, every juniper-ml release proposal, and a
  sub-package proposal that moves a matrix column (today only a juniper-doc-tools bump past its `<0.2.0`
  ceiling), would have failed CI until someone edited REFERENCE by hand.
  - New step 5b-v renders the four sites from the `pyproject.toml` the proposal leaves behind:
    `set_reference_version_cell`, `set_reference_declares_version`, `set_reference_matrix_row` and
    `set_reference_recurrence_clause`, composed by `apply_reference_compat_cochanges`. They share one REFERENCE edit
    with the extras-table true-up, and 5b-v renders from the final pyproject, so an escaping in-repo pin with a
    matrix column (today only doc-tools: ci-tools and observability carry no ceiling to escape) moves its cell
    as well.
  - **The series rule.** A new minor adds its `0.N.x` row and never touches the previous series' row, which
    should describe releases already on PyPI: #1991 added the 0.9.x row and kept the 0.8.x row, "ADDED TO rather
    than rewritten", and the 0.11.0 cut (#2306) did the same. A patch rewrites its own series' row in place, as
    the 0.11.1 and 0.11.2 cuts did. The previous row stays true only if no column pin moved since its series'
    last release: `ReferenceCompatibilityMatrixTest` makes such a move (an escaping in-repo pin, or a hand floor
    raise) rewrite the then-current row in place, so on a minor the checklist's REVIEW line asks the reviewer to
    restore the pins that series published.
  - Each helper keeps `set_agents_version`'s contract: an absent or doubled site is left untouched, and the
    co-change checklist marks it REQUIRED on the meta's own bump. The paragraph's history (which release raised
    which floor) is prose that no gate reads. The train never writes it, and the checklist asks the reviewer to.
    Renaming the clause's release also hands any explanation after it to the new release (from today's file,
    "0.12.0 sets them to ...: it raises `juniper-recurrence` to `>=0.8.1`"), so the generated paragraph is not
    correct until that review. The REVIEW line names the clause whenever it moves.
  - The REVIEW line also names a cell this proposal moved in place (an escaping in-repo pin) and any
    `[recurrence]` pins it replaced. A hand floor raise must rewrite those sites itself to pass
    `ReferenceCompatibilityMatrixTest`, so the meta's own proposal then finds them current and names neither:
    the history, the renamed clause and, on a minor, the previous series' row are what its REVIEW line asks about.
  - **Measured on `main`'s files with #2507's tests installed**
    (`util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py`). The unextended script's patch
    proposal fails 3 of #2507's 8 tests and its minor proposal 4. After a hand `[recurrence]` floor raise that
    also rewrites the clause (the raise those tests let merge), its patch proposal fails 3. All pass with this
    change, and none of the 18 suites the simulator runs regresses. `tests/test_release_train_propose.py` gains
    31 tests (156 to 187), and all 38 mutants of the new code are killed. `docs/REFERENCE.md` and the
    release-train runbook (§3.2) describe the step.''',
)

# ── notes/...RELEASE-TRAIN-OPERATOR-RUNBOOK.md (claims F14) ───────────────────

edit("claims F14 (stamp, once from main's 1.2.4)", RUNBOOK, "**Version**: 1.2.4\n**Last Updated**: 2026-10-26\n", "**Version**: 1.2.5\n**Last Updated**: 2026-11-09\n")

edit(
    "claims F14 F6",
    RUNBOOK,
    r'''#### Gate 1 — Phase 4.2 dependency order + consumer ceiling-bump follow-ons''',
    r'''#### Gate 1 review: `docs/REFERENCE.md` release sites (juniper-ml#2507)

`ReferenceCompatibilityMatrixTest` in `tests/test_pyproject_extras.py` (added by juniper-ml#2507's tests, carried
in the round-2 tests carrier) pins four `docs/REFERENCE.md` sites to the root `pyproject.toml`: the Package
Overview **Version** cell, the "`juniper-ml` X.Y.Z declares the following pins" sentence, the Ecosystem
Compatibility matrix's current-series row and the `[recurrence]` "sets them to" clause. `propose.py` step 5b-v
renders them for every in-repo proposal (`apply_reference_compat_cochanges`), in the one `docs/REFERENCE.md` file
edit, and `_reference_compat_items` writes up to three checklist lines:

| Signal in the proposal PR | Meaning | Operator action |
|---|---|---|
| `docs/REFERENCE.md release sites (included in this PR)` | The train moved the named sites. On the meta's own bump: the Version cell, the sentence and the clause, plus a new `0.N.x` row on a minor (the older rows are not touched) or, on a patch that moves a cell, the series row in place. On a sub-package bump: a cell its escaping pin moved, or a site a drifted REFERENCE left stale | Merge when the rest looks right |
| `docs/REFERENCE.md release sites (REQUIRED -- ...)` | A site is absent or doubled, or cannot be rendered from `pyproject.toml` (an unpinned or conflicting column, a series row of the wrong width, a newer series, a version that is not N.N.N). The train left it byte-untouched | Edit the named site by hand in the same PR; `ReferenceCompatibilityMatrixTest` stays red until then |
| `docs/REFERENCE.md "Ecosystem Compatibility" prose (REVIEW by hand in this PR)` | The paragraph's history is prose no gate reads. The line names what to check: a clause renamed to this release (words after its pins, such as ": it raises ...", now describe it), a row moved in place, replaced `[recurrence]` pins, and on a minor the previous series' row | Reword the history in the same PR. On a minor, if a PR since the previous series' last release rewrote that row in place, restore the pins the series published (`git log -p -- docs/REFERENCE.md` shows them) |

A floor raise between releases (a column or a `[recurrence]` pin) fails `ReferenceCompatibilityMatrixTest` until
its own PR rewrites the current series' row or the clause's pins, so the meta's next proposal finds those sites
current; the REVIEW line's notes are then the only prompt. Hermetic coverage: `tests/test_release_train_propose.py`
(`ReferenceCompatHelperTest` + `BuildProposalReferenceCompatTest`).

#### Gate 1 — Phase 4.2 dependency order + consumer ceiling-bump follow-ons''',
)

# ── the carrier's own helper scripts (kept consistent with the final code) ────

edit(
    "claims F3 (a floor-raise scenario that can reach main)",
    PROVE,
    r'''Three scenarios, each on a fresh copy of each tree:''',
    r'''Four scenarios, each on a fresh copy of each tree:''',
)

edit(
    "claims F3",
    PROVE,
    r'''  moved with propose.py's own editors, as juniper-ml#2473 did), and then the next patch is proposed. The
  recurrence pins have no matrix column, so the clause is their only record in REFERENCE.''',
    r'''  moved with propose.py's own editors, as juniper-ml#2473 did), and then the next patch is proposed. The
  recurrence pins have no matrix column, so the clause is their only record in REFERENCE. #2507's tests refuse
  this raise on its own (its "before" state fails them), so no green merge reaches it;
* ``recurrence-raise-mergeable`` (added 2026-11-09, after round-2 validation): the same raise, which also moves
  the pin inside REFERENCE's "sets them to" clause and nowhere else in the paragraph. That is the floor raise
  #2507's tests let merge, so its "before" state must pass them.''',
)

edit(
    "claims F3",
    PROVE,
    r'''_GATE_RAN = re.compile(r"^Ran (\d+) tests? in ")''',
    r'''_GATE_RAN = re.compile(r"^Ran (\d+) tests? in ")
# REFERENCE's "X.Y.Z sets them to `pin`, `pin` and `pin`" clause, read here rather than through propose.py so the
# hand raise is the same edit in both trees.
_CLAUSE = re.compile(r"\d+\.\d+\.\d+ sets them to (?:`[^`]+`(?:, | and )?)+")''',
)

edit(
    "claims F3",
    PROVE,
    r'''def _child_raise(tree: Path, package: str, old_req: str, new_req: str) -> int:
    """The hand floor raise, with every lockstep surface tests/test_pyproject_extras.py holds the pin to."""''',
    r'''def _child_raise(tree: Path, package: str, old_req: str, new_req: str, rewrite_clause: bool = False) -> int:
    """The hand floor raise, with every lockstep surface tests/test_pyproject_extras.py holds the pin to.

    ``rewrite_clause`` also moves the pin inside REFERENCE's "sets them to" clause (only there): the raise
    ReferenceCompatibilityMatrixTest lets merge, since the clause must name pyproject's [recurrence] pins."""''',
)

edit(
    "claims F3",
    PROVE,
    r'''        changed.append(propose._REFERENCE_EXTRAS_REL)
    print(json.dumps({"raised": f"{old_req} -> {new_req}", "changed": changed}))''',
    r'''        changed.append(propose._REFERENCE_EXTRAS_REL)
    if rewrite_clause:
        text = path.read_text(encoding="utf-8")
        clauses = list(_CLAUSE.finditer(text))
        needle = f"`{old_req}`"
        if len(clauses) != 1 or text.count(needle, clauses[0].start(), clauses[0].end()) != 1:
            print(json.dumps({"refused": f"expected one 'sets them to' clause naming {needle} once"}))
            return 2
        m = clauses[0]
        path.write_text(text[: m.start()] + m.group(0).replace(needle, f"`{new_req}`") + text[m.end() :], encoding="utf-8")
        changed.append(f"{propose._REFERENCE_EXTRAS_REL} (the 'sets them to' clause)")
    print(json.dumps({"raised": f"{old_req} -> {new_req}", "changed": changed}))''',
)

edit(
    "claims F3",
    PROVE,
    r'''    ap.add_argument("--bump")
    args = ap.parse_args(argv)
    tree = Path(args.tree).resolve()
    if args.raise_from:
        return _child_raise(tree, args.package, args.raise_from, args.raise_to)''',
    r'''    ap.add_argument("--bump")
    ap.add_argument("--rewrite-clause", action="store_true")
    args = ap.parse_args(argv)
    tree = Path(args.tree).resolve()
    if args.raise_from:
        return _child_raise(tree, args.package, args.raise_from, args.raise_to, args.rewrite_clause)''',
)

edit(
    "claims F3",
    PROVE,
    r'''    scenarios = {
        "patch": (f"{major}.{minor}.{patch + 1}", "patch", None),
        "minor": (f"{major}.{minor + 1}.0", "minor", None),
        "recurrence-raise": (f"{major}.{minor}.{patch + 1}", "patch", (raise_from, raise_to)),
    }''',
    r'''    # (to_version, bump, the hand raise or None, whether that raise also moves the clause's pin)
    scenarios = {
        "patch": (f"{major}.{minor}.{patch + 1}", "patch", None, False),
        "minor": (f"{major}.{minor + 1}.0", "minor", None, False),
        "recurrence-raise": (f"{major}.{minor}.{patch + 1}", "patch", (raise_from, raise_to), False),
        "recurrence-raise-mergeable": (f"{major}.{minor}.{patch + 1}", "patch", (raise_from, raise_to), True),
    }''',
)

edit("claims F3", PROVE, r'''    for scenario, (to_version, bump, raised) in scenarios.items():''', r'''    for scenario, (to_version, bump, raised, rewrite_clause) in scenarios.items():''')

edit(
    "claims F3",
    PROVE,
    r'''"--raise-from", raised[0], "--raise-to", raised[1]], capture_output=True''',
    r'''"--raise-from", raised[0], "--raise-to", raised[1], *(["--rewrite-clause"] if rewrite_clause else [])], capture_output=True''',
)

edit(
    "claims F3",
    PROVE,
    r'''            if variant == "extended" and regressed:
                failures.append(f"{name}: the proposal regressed {regressed}")''',
    r'''            if variant == "extended" and regressed:
                failures.append(f"{name}: the proposal regressed {regressed}")
            if rewrite_clause and not before_gate["passed"]:
                failures.append(f"{name}: #2507's class failed BEFORE the proposal; the mergeable raise must leave it green")''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''    ap.add_argument("--carrier-root", required=True, help="the carrier's checkout (the git repo the refs resolve in)")''',
    r'''    ap.add_argument("--carrier-root", required=True, help="the carrier's checkout (the git repo the refs resolve in)")
    ap.add_argument("--git-root", help="the checkout git runs in (default: --carrier-root); any worktree of the same repository resolves the refs")''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''    root = Path(args.carrier_root).resolve()
    sim = Path(args.sim_dir).resolve()''',
    r'''    root = Path(args.carrier_root).resolve()
    git_root = Path(args.git_root).resolve() if args.git_root else root
    sim = Path(args.sim_dir).resolve()''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''    base_sha = _git(root, "rev-parse", args.base_ref)
    gate_sha = _git(root, "rev-parse", args.gate_ref)
    merge_base = _git(root, "merge-base", base_sha, gate_sha)
    base_blob = _git(root, "rev-parse", f"{base_sha}:{GATE_FILE}")
    fork_blob = _git(root, "rev-parse", f"{merge_base}:{GATE_FILE}")''',
    r'''    base_sha = _git(git_root, "rev-parse", args.base_ref)
    gate_sha = _git(git_root, "rev-parse", args.gate_ref)
    merge_base = _git(git_root, "merge-base", base_sha, gate_sha)
    base_blob = _git(git_root, "rev-parse", f"{base_sha}:{GATE_FILE}")
    fork_blob = _git(git_root, "rev-parse", f"{merge_base}:{GATE_FILE}")''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''    gate_text = _git(root, "show", f"{gate_sha}:{GATE_FILE}", binary=True)''',
    r'''    gate_text = _git(git_root, "show", f"{gate_sha}:{GATE_FILE}", binary=True)''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''    archive = _git(root, "archive", "--format=tar", base_sha, binary=True)''',
    r'''    archive = _git(git_root, "archive", "--format=tar", base_sha, binary=True)''',
)

edit(
    "harness: git runs in the caller's own worktree",
    PROVE,
    r'''"gate_blob": _git(root, "rev-parse", f"{gate_sha}:{GATE_FILE}")''',
    r'''"gate_blob": _git(git_root, "rev-parse", f"{gate_sha}:{GATE_FILE}")''',
)

edit(
    "code F2 F1 F5 F7 (the mutation check covers the round-2 code)",
    MUTATE,
    r'''1. the selection is the carrier's own tests -- the two new classes and the one existing test whose assertion the
   carrier changed -- so a kill is credited to them, not to the rest of the suite;''',
    r'''1. the selection is the carrier's own tests -- the two new classes and the two existing tests whose assertions the
   carrier changed or added -- so a kill is credited to them, not to the rest of the suite;''',
)

edit(
    "code F2 F1 F5 F7",
    MUTATE,
    r'''Writes ``<out-dir>/mutation_results.json`` and one log per mutant. Exit 0 when every mutant is killed.''',
    r'''Writes ``<out-dir>/mutation_results.json`` and one log per mutant. Exit 0 when every mutant is killed.

Revised 2026-11-09 after round-2 validation: L1 follows the REVIEW gate's new form (``meta_bump or done``); CM4,
RM5, VM3, DM3 and LM1 are the code-lens validator's survivors (util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_mutants.py),
now killed by the tests that round added; L3-L9 cover the round-2 checklist code (the REVIEW gate, the previous-row
note, the renamed-clause note, the release it names, and the "included" line's wording).''',
)

edit(
    "code F2 (LM1's test joins the selection)",
    MUTATE,
    r'''    "tests.test_release_train_propose.BuildProposalConsumerPinTest.test_meta_self_bump_moves_the_readme_compat_lead_in",
)''',
    r'''    "tests.test_release_train_propose.BuildProposalConsumerPinTest.test_meta_self_bump_moves_the_readme_compat_lead_in",
    "tests.test_release_train_propose.BuildProposalConsumerPinTest.test_escaping_minor_bump_emits_all_three_cochanges",
)''',
)

edit(
    "code F7 (L1 follows the new REVIEW gate)",
    MUTATE,
    r'''    ("L1", "_reference_compat_items", '    if meta_bump or report.get("matrix_row") == "edited":\n        notes = [', "    if meta_bump:\n        notes = ["),''',
    r'''    ("L1", "_reference_compat_items", "    if meta_bump or done:\n        notes = [", "    if meta_bump:\n        notes = ["),''',
)

edit(
    "code F1 F2 F5 F7",
    MUTATE,
    r'''    ("W3", "build_proposal step 5b-ii (REFERENCE composed once)", "                    ref_new = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)", "                    _ = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)"),
)''',
    r'''    ("W3", "build_proposal step 5b-ii (REFERENCE composed once)", "                    ref_new = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)", "                    _ = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)"),
    # Round 2 (2026-11-09): the code-lens validator's survivors, then the round-2 checklist code.
    ("CM4", "set_reference_recurrence_clause (one unreadable pin among readable ones)", "    if not pins or any(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):", "    if not pins or all(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):"),
    ("RM5", "set_reference_matrix_row (a series row wider than the header)", "        if len(raw) != len(header) + 2:", "        if len(raw) < len(header) + 2:"),
    ("VM3", "set_reference_version_cell (a cell holding more than the version)", '        m = re.fullmatch(r"`([^`]+)`", raw[2].strip())', '        m = re.search(r"`([^`]+)`", raw[2].strip())'),
    ("DM3", "set_reference_declares_version (_REFERENCE_DECLARES: the sentence's period)", r"( declares the following pins\.)", r"( declares the following pins)"),
    ("LM1", "_reference_compat_items (a sub-package bump owes no release site)", '(meta_bump and report.get(key) not in ("edited", "added", "current"))', '(True and report.get(key) not in ("edited", "added", "current"))'),
    ("L3", "_reference_compat_items (REVIEW whenever a site moved, code F7)", "    if meta_bump or done:\n        notes = [", '    if meta_bump or report.get("matrix_row") == "edited":\n        notes = ['),
    ("L4", "_reference_compat_items (the previous-row note, code F1)", '        if report.get("matrix_row") == "added":\n            notes.append("the previous series', '        if report.get("matrix_row") == "never":\n            notes.append("the previous series'),
    ("L5", "_reference_compat_items (the previous-row note on every proposal)", '        if report.get("matrix_row") == "added":\n            notes.append("the previous series', '        if True:\n            notes.append("the previous series'),
    ("L6", "_reference_compat_items (the renamed-clause note, code F5)", '        if report.get("recurrence") == "edited":\n            named', '        if report.get("recurrence") == "never":\n            named'),
    ("L7", "_reference_compat_items (the renamed-clause note on every proposal)", '        if report.get("recurrence") == "edited":\n            named', "        if True:\n            named"),
    ("L8", "apply_reference_compat_cochanges (the release the clause note names)", '    report["version"] = version\n', '    report["version"] = None\n'),
    ("L9", "_reference_compat_items (the included line vouches for the older rows, code F1)", "(the older rows are not touched)", "(the older rows stay: they describe published releases)"),
)''',
)

edit(
    "brief: manifest.json carries sha256s",
    MANIFEST,
    r'''Usage: python3 util/ad-hoc/2026-11-08_flood4r2_ml-propose_manifest.py <scratch-dir> <worktree> <base-sha>
"""''',
    r'''Usage: python3 util/ad-hoc/2026-11-08_flood4r2_ml-propose_manifest.py <scratch-dir> <worktree> <base-sha>

Revised 2026-11-09 after round-2 validation: each file row carries the worktree file's sha256, and the manifest
points at ``<scratch>/dispositions.json``, the record of what was done with each validator finding.
"""''',
)

edit("brief: manifest.json carries sha256s", MANIFEST, "import json\nimport sys\n", "import hashlib\nimport json\nimport sys\n")

edit(
    "brief: manifest.json carries sha256s",
    MANIFEST,
    r'''        files.append({"path": path, "status": STATUS.get(code[:1], code)})''',
    r'''        target = worktree / path
        sha = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        files.append({"path": path, "status": STATUS.get(code[:1], code), "sha256": sha})''',
)

edit(
    "brief: manifest.json carries sha256s",
    MANIFEST,
    r'''        "open_questions": _load(scratch / "open_questions.json"),
    }''',
    r'''        "open_questions": _load(scratch / "open_questions.json"),
        "dispositions": str(scratch / "dispositions.json"),
    }''',
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.worktree).resolve()
    texts: dict = {}
    originals: dict = {}
    problems = []
    for ids, rel, old, new in EDITS:
        if rel not in texts:
            path = root / rel
            if not path.is_file():
                problems.append(f"{rel}: missing")
                texts[rel] = None
                continue
            originals[rel] = path.read_bytes()
            texts[rel] = originals[rel].decode("utf-8")
        text = texts[rel]
        if text is None:
            continue
        count = text.count(old)
        # ``new`` first: an appending row's ``new`` CONTAINS its ``old``, so "old still present" does not mean
        # "not applied yet" (a second run duplicated those rows until this check came first).
        if new in text:
            print(f"already {rel}: [{ids}] {old.strip().splitlines()[0][:70]!r}")
        elif count == 1:
            texts[rel] = text.replace(old, new, 1)
            print(f"apply   {rel}: [{ids}] {old.strip().splitlines()[0][:70]!r}")
        else:
            problems.append(f"{rel}: [{ids}] old text occurs {count} times: {old.strip().splitlines()[0][:90]!r}")
    if problems:
        for problem in problems:
            print("ERROR:", problem, file=sys.stderr)
        print("nothing written", file=sys.stderr)
        return 1
    for rel, text in texts.items():
        new_bytes = text.encode("utf-8")
        before, after = _sha(originals[rel]), _sha(new_bytes)
        print(f"{rel}: sha256 {before} -> {after}{' (unchanged)' if before == after else ''}")
        if not args.dry_run and before != after:
            (root / rel).write_bytes(new_bytes)
    print(f"{len(EDITS)} rows over {len(texts)} files{' (dry run: nothing written)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
