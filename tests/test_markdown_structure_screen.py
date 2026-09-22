#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Hermetic tests for ``util/ad-hoc/2026-09-05_markdown_structure_check.py`` -- the SCREEN that
``util/markdown_structure_delta.py`` (the CI gate) imports and calls per file.

The screen's ``check()`` was already exercised indirectly through the delta gate's suite.
Its ``main()`` was not, and that is where it under-reported: the file-selection predicate was

    if not p.is_file() or p.suffix.lower() != ".md":
        continue

``Path.is_file()`` FOLLOWS SYMLINKS, so a **dangling** symlink answers ``False`` and was
skipped -- silently, without being counted. ``main`` carried ten such links (nine under
``notes/legacy/`` pointing at a ``regressions/`` directory that is not on ``main``, one under
``notes/development/``), so a whole-tree run examined 1024 of 1034 paths while printing a
total that read as though it had covered all of them. The ten scored clean by never being
looked at.

The 2026-09-10 structure repair RETARGETED all ten -- ``432ed644`` had renamed both ends and a symlink body is opaque
text, so nothing rewrote it -- and the fixtures below are synthetic, so they keep pinning the
behaviour now that no live dangling link remains to demonstrate it. That same change added the
SYMLINK-ALIAS rule: once the links resolved, eleven tracked paths pointed at a file another
path already covered and the whole-tree count rose by 2 with no markdown edited.

That is the same **vacuous pass** shape the delta gate already guards -- a correct predicate
run over an incomplete site enumeration -- turned on the screen itself. Three behaviours are
pinned here:

* a markdown path that cannot be read is COUNTED and exits ``2``, never silently skipped;
* examining ZERO paths exits ``2``, so a run that filtered everything away cannot report
  success;
* a genuinely clean file still exits ``0``, and a file with a real structural problem still
  exits ``1`` -- the fix must not turn the screen into a permanent refusal.

Every fixture is a temp dir. Nothing reads the live tree.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "ad-hoc" / "2026-09-05_markdown_structure_check.py"

_spec = importlib.util.spec_from_file_location("markdown_structure_check", MODULE_PATH)
assert _spec and _spec.loader
screen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(screen)


CLEAN = "# Title\n\nSome prose.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
BROKEN_TABLE = "# Title\n\nprose\n\n| a | b |\n| 1 | 2 |\n"


def run(argv):
    """Call main(argv), returning (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = screen.main(argv)
    return code, out.getvalue(), err.getvalue()


class ScreenExitCodeTest(unittest.TestCase):
    def test_a_clean_markdown_file_exits_zero(self):
        with TemporaryDirectory() as td:
            p = Path(td, "clean.md")
            p.write_text(CLEAN)
            code, out, _err = run([str(p)])
        self.assertEqual(code, 0)
        self.assertIn("examined 1 of 1", out)

    def test_a_structural_problem_still_exits_one(self):
        # The vacuity guard must not swallow the finding the screen exists for.
        with TemporaryDirectory() as td:
            p = Path(td, "broken.md")
            p.write_text(BROKEN_TABLE)
            code, out, _err = run([str(p)])
        self.assertEqual(code, 1)
        self.assertIn("has no separator row", out)

    def test_no_arguments_exits_two(self):
        code, _out, _err = run([])
        self.assertEqual(code, 2)


class DanglingSymlinkTest(unittest.TestCase):
    """The ten links on `main` that used to score clean by never being read."""

    def _dangling(self, td):
        link = Path(td, "dangling.md")
        link.symlink_to(Path(td, "regressions", "gone.md"))
        return link

    def test_a_dangling_symlink_is_counted_and_refuses(self):
        with TemporaryDirectory() as td:
            link = self._dangling(td)
            self.assertFalse(link.is_file(), "fixture must be a dangling link")
            code, _out, err = run([str(link)])
        self.assertEqual(code, 2, "a markdown path that cannot be read must not pass")
        self.assertIn("could not read 1 markdown path", err)
        self.assertIn("refusing to report on a partial examination", err)

    def test_one_dangling_link_beside_nine_readable_files_still_refuses(self):
        # The precise regression: skipping without counting meant nine readable files
        # reported success and said nothing about the tenth.
        with TemporaryDirectory() as td:
            paths = []
            for i in range(9):
                p = Path(td, f"ok{i}.md")
                p.write_text(CLEAN)
                paths.append(str(p))
            paths.append(str(self._dangling(td)))
            code, out, err = run(paths)
        self.assertEqual(code, 2)
        self.assertIn("examined 9 of 10", out)
        self.assertIn("could not read 1", err)

    def test_a_symlink_that_RESOLVES_is_examined_normally(self):
        # Not every symlink is broken -- the fix must not refuse the working ones.
        with TemporaryDirectory() as td:
            real = Path(td, "real.md")
            real.write_text(CLEAN)
            link = Path(td, "link.md")
            link.symlink_to(real)
            code, out, _err = run([str(link)])
        self.assertEqual(code, 0)
        self.assertIn("examined 1 of 1", out)


class VacuousExaminationTest(unittest.TestCase):
    def test_all_paths_filtered_as_non_markdown_exits_two(self):
        with TemporaryDirectory() as td:
            a, b = Path(td, "setup.py"), Path(td, "conf.toml")
            a.write_text("x = 1\n")
            b.write_text("k = 1\n")
            code, _out, err = run([str(a), str(b)])
        self.assertEqual(code, 2, "examining nothing must not report success")
        self.assertIn("examined 0 of 2", err)

    def test_a_non_markdown_path_beside_a_real_one_is_reported_not_fatal(self):
        # Mixed globs are the normal calling convention; filtering is legitimate as long
        # as it is COUNTED and at least one file was actually examined.
        with TemporaryDirectory() as td:
            md = Path(td, "clean.md")
            md.write_text(CLEAN)
            other = Path(td, "notes.txt")
            other.write_text("hello\n")
            code, out, _err = run([str(md), str(other)])
        self.assertEqual(code, 0)
        self.assertIn("skipped 1 non-markdown", out)


class DeltaGateStillLoadsTheScreenTest(unittest.TestCase):
    """`util/markdown_structure_delta.py` imports this module by path and calls `check()`.

    The vacuity fix touched `main()` only, but the gate is a required CI check, so the
    import contract is pinned here rather than discovered on `main`.
    """

    def test_the_gate_can_load_the_screen_and_call_check(self):
        gate_path = REPO_ROOT / "util" / "markdown_structure_delta.py"
        spec = importlib.util.spec_from_file_location("markdown_structure_delta", gate_path)
        assert spec and spec.loader
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        loaded = gate._load_screen()
        self.assertTrue(hasattr(loaded, "check"), "the gate depends on check()")
        with TemporaryDirectory() as td:
            p = Path(td, "x.md")
            p.write_text(BROKEN_TABLE)
            self.assertEqual(len(loaded.check(p)), 1)


class SeparatorAcceptsValidGfmDelimitersTest(unittest.TestCase):
    """GFM needs ONE hyphen per delimiter cell; the pattern demanded two until 2026-09-10.

    This was a REQUIRED-GATE defect, not a counting error. `util/markdown_structure_delta.py`
    grades a file the PR ADDS against a baseline of zero, and its step runs in ci.yml's
    `docs` job -- whose NAME, `Documentation Links`, is the required status context. So a PR
    adding any markdown file with a `| - |` or `|:-:|` delimiter row failed a required check
    for a defect that did not exist.
    """

    def _findings(self, body):
        with TemporaryDirectory() as td:
            p = Path(td, "t.md")
            p.write_text(body)
            return screen.check(p)

    def test_single_hyphen_delimiter_is_a_table(self):
        self.assertEqual(self._findings("# T\n\n| A | B |\n| - | - |\n| 1 | 2 |\n"), [])

    def test_single_hyphen_with_alignment_colons_is_a_table(self):
        self.assertEqual(self._findings("# T\n\n| C | D |\n|:-:|:-:|\n| 3 | 4 |\n"), [])

    def test_multi_hyphen_delimiter_still_accepted(self):
        self.assertEqual(self._findings("# T\n\n| E | F |\n| --- | --- |\n| 5 | 6 |\n"), [])

    def test_a_genuinely_missing_separator_is_STILL_reported(self):
        # The negative control. Relaxing the pattern must not blind the check it exists for.
        found = self._findings(BROKEN_TABLE)
        self.assertEqual(len(found), 1)
        self.assertIn("has no separator row", found[0])


class FenceWalkerFollowsCommonMarkTest(unittest.TestCase):
    """The boolean toggle disagreed with every real renderer; these pin the three rules.

    Cost of the toggle, on the record: two agents reported "three unclosed fences on main"
    in the 2026-09-09 review and the reviewer confirmed it by re-running this screen -- the
    instrument under suspicion, used as its own witness. The true count is two.
    """

    def _findings(self, body):
        with TemporaryDirectory() as td:
            p = Path(td, "t.md")
            p.write_text(body)
            return screen.check(p)

    def test_an_info_string_fence_cannot_close_a_block(self):
        # ```bash is an opener or content -- never a closer. Under the toggle it ENDED the
        # enclosing block, so the heading after it read as swallowed by a bare fence. This
        # is the ml#1746-era shape that the toggle reports and CommonMark does not.
        body = "# T\n\n````markdown\n```bash\necho hi\n```\n## Sample heading\n````\n"
        self.assertEqual(self._findings(body), [])

    def test_a_short_fence_cannot_close_a_longer_one(self):
        # Under the toggle the inner ``` closed the ```` block and the final ```` re-opened
        # one, reporting a phantom UNCLOSED fence at EOF.
        body = "# T\n\n````markdown\n## A\n```\n## B\n````\n"
        self.assertEqual(self._findings(body), [])

    def test_tilde_and_backtick_fences_do_not_close_each_other(self):
        body = "# T\n\n~~~\n```\n~~~\n\nprose\n"
        self.assertEqual(self._findings(body), [])

    def test_a_really_unclosed_fence_is_still_reported(self):
        # The negative control for the whole rewrite.
        found = self._findings("# T\n\n```bash\necho hi\n")
        self.assertEqual(len(found), 1)
        self.assertIn("UNCLOSED code fence opened at line 3", found[0])

    def test_an_H2_swallowed_by_a_lost_fence_is_still_reported(self):
        # ml#1746's actual damage: a dropped closer absorbing every heading after it.
        found = self._findings("# T\n\n```bash\necho hi\n\n## Swallowed\n")
        self.assertTrue(any("H2 swallowed" in f for f in found), found)

    def test_a_markdown_sample_may_hold_H2s_at_any_fence_length(self):
        self.assertEqual(self._findings("# T\n\n````md\n## Sample heading\n````\n"), [])

    def test_a_TILDE_markdown_sample_is_exempt(self):
        # `_is_markdown_example` stripped only backticks, so ~~~markdown read as the info
        # string "~~~markdown" and was never exempt. The old toggle never reached this at
        # all -- it ignored ~~~ entirely -- so the pairing below is what gives it meaning.
        self.assertEqual(self._findings("# T\n\n~~~markdown\n## Sample heading\n~~~\n"), [])

    def test_a_TILDE_bare_fence_still_swallows(self):
        # The paired positive control. Without it, the exemption above is indistinguishable
        # from the screen simply not modelling tilde fences -- which is exactly what the
        # code it replaced did, and why that assertion alone proves nothing.
        #
        # FIXTURE CHANGED 2026-09-15, purpose unchanged. This was `~~~bash`, which the
        # H2-in-fence narrowing now exempts along with every other CLOSED, explicitly-typed
        # fence. A BARE `~~~` keeps the control sharp and in fact tightens it: both fences
        # here are CLOSED tilde fences and differ only in their info string, so a screen
        # that did not model tilde fences at all would report neither.
        found = self._findings("# T\n\n~~~\n## Swallowed\n~~~\n")
        self.assertTrue(any("H2 swallowed" in f for f in found), found)

    def test_a_TILDE_unclosed_fence_still_swallows(self):
        # The other half of the tilde walk: an unclosed tilde fence is reportable whatever
        # it claims to contain, which is what keeps real damage visible after the narrowing.
        found = self._findings("# T\n\n~~~bash\n## Swallowed\n")
        self.assertTrue(any("H2 swallowed" in f for f in found), found)
        self.assertTrue(any("UNCLOSED" in f for f in found), found)


class SymlinkAliasIsCountedNotSilentlySkippedTest(unittest.TestCase):
    """A link and its target are two tracked paths and ONE file.

    Repointing the ten broken notes links (2026-09-10) made
    `notes/development/...V7-IMPLEMENTATION-ROADMAP.md` resolve onto
    `notes/JUNIPER_2026-05-25_...`, which already carried two findings -- so the whole-tree
    total rose 63 -> 65 without a character of markdown changing.

    The dedup must stay LOUD. A silent skip is precisely the failure this screen was built
    to catch, and adding one here to tidy a number would reintroduce it one level up.
    """

    def test_a_link_and_its_target_are_counted_once_and_the_alias_is_named(self):
        with TemporaryDirectory() as td:
            real = Path(td, "real.md")
            real.write_text(BROKEN_TABLE)
            link = Path(td, "link.md")
            link.symlink_to(real)
            code, out, _err = run([str(real), str(link)])
        self.assertEqual(code, 1)
        self.assertIn("structural problems: 1", out)  # not 2
        self.assertIn("1 symlink alias(es)", out)  # and it is SAID
        self.assertIn("alias:", out)

    def test_the_alias_is_reported_even_when_the_file_is_clean(self):
        with TemporaryDirectory() as td:
            real = Path(td, "real.md")
            real.write_text(CLEAN)
            link = Path(td, "link.md")
            link.symlink_to(real)
            code, out, _err = run([str(real), str(link)])
        self.assertEqual(code, 0)
        self.assertIn("1 symlink alias(es)", out)

    def test_a_lone_resolving_link_is_still_examined(self):
        # Dedup must not turn a link passed WITHOUT its target into a skip.
        with TemporaryDirectory() as td:
            real = Path(td, "real.md")
            real.write_text(BROKEN_TABLE)
            link = Path(td, "link.md")
            link.symlink_to(real)
            code, out, _err = run([str(link)])
        self.assertEqual(code, 1)
        self.assertIn("examined 1 of 1", out)
        self.assertNotIn("alias", out)

    def test_a_dangling_link_still_refuses_rather_than_aliasing(self):
        # The resolve() that finds aliases must not swallow the unreadable-path guard.
        with TemporaryDirectory() as td:
            link = Path(td, "dangling.md")
            link.symlink_to(Path(td, "regressions", "gone.md"))
            code, _out, err = run([str(link)])
        self.assertEqual(code, 2)
        self.assertIn("refusing to report on a partial examination", err)


class H2InFenceIsNarrowedToUnclosedOrBareTest(unittest.TestCase):
    """An H2 inside a CLOSED, explicitly-typed fence is not a finding (narrowed 2026-09-15).

    The previous rule -- "anything but ```markdown has no business containing an H2" --
    produced 17 of the 17 problems the whole-tree census reported on `main`, and every one
    was a false positive: a ```text ASCII banner whose border is `#`, and a ````jinja2
    template whose `## Overview` is template OUTPUT.

    Same REQUIRED-GATE shape as `SeparatorAcceptsValidGfmDelimitersTest` above: the delta
    gate grades an ADDED file against a baseline of zero, and its step runs in the `docs`
    job whose name, `Documentation Links`, is a required status context. An eleven-line new
    note with an ordinary ```text banner failed a required check for a defect that was not
    in the PR.
    """

    def _findings(self, body):
        with TemporaryDirectory() as td:
            p = Path(td, "t.md")
            p.write_text(body)
            return screen.check(p)

    def test_text_fence_holding_an_ascii_banner_is_not_a_finding(self):
        body = "# N\n\n```text\n######\n##  BUILD FAILED\n##  reason: missing key\n######\n```\n\ntail\n"
        self.assertEqual(self._findings(body), [])

    def test_jinja2_fence_holding_a_template_is_not_a_finding(self):
        # Four backticks so the block can quote a three-backtick one, as on `main`.
        body = "# N\n\n````jinja2\n{% block body %}\n## Overview\n\n{{ overview }}\n{% endblock %}\n````\n\ntail\n"
        self.assertEqual(self._findings(body), [])

    def test_python_fence_with_a_comment_heading_is_not_a_finding(self):
        body = "# N\n\n```python\n## step two\nx = 1\n```\n\ntail\n"
        self.assertEqual(self._findings(body), [])

    def test_an_UNCLOSED_fence_swallowing_an_h2_is_STILL_reported(self):
        # Negative control 1. Narrowing must not blind the check to real damage.
        found = self._findings("# N\n\n```bash\necho hi\n\n## Swallowed\n\nmore\n")
        self.assertTrue(any("H2 swallowed" in f for f in found), found)
        self.assertTrue(any("UNCLOSED" in f for f in found), found)

    def test_a_BARE_closed_fence_containing_an_h2_is_STILL_reported(self):
        # Negative control 2. NOT the juniper-ml#1746 shape -- this comment used to say it
        # was, and that error is what made the narrowing look safe. ml#1749's own commit
        # body (`7a4b1cb4`) records the lost line as "the close of the ``text`` block at
        # REFERENCE.md:1522": a TYPED fence. The real shape is pinned in
        # AbsorbedOpenerRestoresDroppedCloserDetectionTest below.
        found = self._findings("# N\n\n```\n## Swallowed By Bare Fence\n```\n\ntail\n")
        self.assertEqual(len(found), 1, found)
        self.assertIn("H2 swallowed", found[0])

    def test_a_markdown_sample_fence_stays_exempt(self):
        self.assertEqual(self._findings("# N\n\n```markdown\n## Sample\n```\n\ntail\n"), [])

    def test_predicate_unclosed_beats_an_explicit_info_string(self):
        # An unclosed fence is reportable whatever it claims to contain.
        self.assertTrue(screen._can_swallow_headings("```text", is_unclosed=True))
        self.assertFalse(screen._can_swallow_headings("```text", is_unclosed=False))
        self.assertTrue(screen._can_swallow_headings("```", is_unclosed=False))
        self.assertFalse(screen._can_swallow_headings("```markdown", is_unclosed=False))


class AbsorbedOpenerRestoresDroppedCloserDetectionTest(unittest.TestCase):
    """The 2026-09-15 narrowing blinded this screen to the incident that created it.

    Its safety argument was: *"a dropped closer leaves the fence UNCLOSED, which is reported
    in its own right."* That only holds in a document with nothing after the damage. In a
    real file the NEXT block's opener is absorbed -- a delimiter carrying an info string
    cannot close anything -- and the following bare delimiter re-closes the damaged span.
    Fence polarity is restored, no UNCLOSED finding exists, and with the opener typed the
    narrowed rule exempted the whole span. Every heading between them was silently inside a
    code block, reported by nothing.

    Measured on the real damaged blob, `bcc89c45:docs/REFERENCE.md` (ml#1746): the
    pre-narrowing screen reported 2, the narrowed screen reported 0 and exit 0, and the
    corrected screen reports 2 again. `util/markdown_structure_delta.py` execs this file
    inside the `Documentation Links` REQUIRED check, so that damage would have shipped with
    every check green -- the exact failure ml#1749 was opened to prevent.

    The narrowing's premise was also factually wrong: its commit message says ml#1746's
    fence "was bare", while ml#1749's own body records the lost line as the close of a
    ```text block. Typed -- the class the narrowing exempts.

    Each arm here fails against the narrowed-only predicate. The exemptions the narrowing
    bought are kept, and pinned below as controls: neither absorbs a sibling opener.
    """

    def _findings(self, body):
        with TemporaryDirectory() as td:
            p = Path(td, "t.md")
            p.write_text(body)
            return screen.check(p)

    def _doc(self, *lines):
        """Join fixture lines explicitly.

        Written as a join rather than adjacent string literals because black (line length
        512) collapses a parenthesised group onto one line, which turns it into implicit
        string concatenation -- the pattern CodeQL flags and that has blocked merges in this
        repo before. A list of lines survives reformatting unchanged.
        """
        return "\n".join(lines) + "\n"

    def test_a_dropped_closer_that_absorbs_a_typed_opener_is_reported(self):
        """The ml#1746 shape: ```text loses its closer and eats the next ```python opener."""
        body = self._doc(
            "# N",
            "",
            "```text",
            "banner",
            # the closing ``` belongs HERE and is dropped
            "",
            "## Swallowed One",
            "",
            "```python",  # absorbed: it carries an info string, so it cannot close
            "x = 1",
            "```",  # bare, so it re-closes the DAMAGED fence -- polarity restored
            "",
            "tail",
        )
        found = self._findings(body)
        self.assertTrue(any("H2 swallowed" in f for f in found), found)

    def test_two_closes_lost_with_typed_openers_is_reported(self):
        """Balanced-but-wrong: the heuristic the narrowing kept only for BARE fences."""
        body = self._doc(
            "# N",
            "",
            "```text",
            "banner",
            "",
            "## Swallowed One",
            "",
            "```bash",
            "echo hi",
            "",
            "## Swallowed Two",
            "",
            "```yaml",
            "k: v",
            "```",
            "",
            "tail",
        )
        found = self._findings(body)
        self.assertTrue(any("H2 swallowed" in f for f in found), found)

    def test_a_four_backtick_block_that_absorbs_a_four_backtick_opener_is_reported(self):
        """Length is compared, not assumed: an absorbed run must be able to open a sibling."""
        body = self._doc(
            "# N",
            "",
            "````text",
            "banner",
            "",
            "## Swallowed",
            "",
            "````python",
            "x = 1",
            "````",
            "",
            "tail",
        )
        found = self._findings(body)
        self.assertTrue(any("H2 swallowed" in f for f in found), found)

    def test_the_document_is_NOT_unclosed_so_nothing_else_would_report_it(self):
        """Proves the arm is load-bearing, not a duplicate of the UNCLOSED check.

        If the damaged span were merely unclosed, the pre-existing arm would already catch
        it and this class would be redundant. It is not: polarity is even.
        """
        body = "# N\n\n```text\nbanner\n\n## Swallowed\n\n```python\nx = 1\n```\n\ntail\n"
        lines = body.split("\n")
        _spans, unclosed = screen._fence_spans(lines)
        self.assertIsNone(unclosed)
        self.assertTrue(any("H2 swallowed" in f for f in self._findings(body)))

    # --- controls: the 17 false positives must STAY cleared -----------------------------

    def test_the_ascii_banner_absorbs_nothing_and_stays_exempt(self):
        body = "# N\n\n```text\n######\n##  BUILD FAILED\n######\n```\n\n```python\nx = 1\n```\n\ntail\n"
        self.assertEqual(self._findings(body), [])

    def test_a_jinja2_template_quoting_a_SHORTER_fence_stays_exempt(self):
        """A ```` block legitimately quotes ``` runs; they cannot open a sibling of it."""
        body = "# N\n\n````jinja2\n{% block b %}\n## Overview\n```\ncode\n```\n{% endblock %}\n````\n\ntail\n"
        self.assertEqual(self._findings(body), [])

    def test_a_markdown_sample_stays_exempt_even_when_it_quotes_a_typed_opener(self):
        """The markdown-example exemption is checked BEFORE the absorbed arm, by design."""
        body = "# N\n\n```markdown\n## Sample\n```python\ncode\n```\n\ntail\n"
        self.assertEqual(self._findings(body), [])


if __name__ == "__main__":
    unittest.main()
