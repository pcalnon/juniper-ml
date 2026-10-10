#!/usr/bin/env python3
"""
Hermetic gate for the backup design's clearing script
(``util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py``; Phase B round 3, R3C D-5).

The backup design (``notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md``)
is GENERATED: ``origin/main``'s copy, then ``2026-09-22_stage_design_artifacts.py --from-repo``, then this
script's prose edits. Round 3 mutated the script's fence gate, its ``ml#FIXFWD`` check and its ``FENCE_EDITS``
declaration, and every mutant survived the suites -- nothing in CI ran the script. This suite does, in a
scratch copy of the repository layout (the design, the script, its wrap helper), never in the checkout:

* the committed design is the script's own output -- a run over it is "no change";
* a design with one edit not yet applied is written, the result equals the committed design byte-for-byte,
  and a second run is "no change" (idempotent);
* an edit whose anchor sits inside a fenced block (a stray fence change) is refused, exit 3, nothing written;
* an edit that pushes a table row over 512 characters is refused, exit 3, nothing written;
* ``FIXFWD_PR`` other than ``ml#<digits>`` -- the placeholder, empty, lower-case -- is refused, exit 3 (R3C N-3);
* a deleted marker that main REWORDED is refused instead of passing as "already applied" (R3C N-11);
* a STOP block that differs from the one the script replaces is refused instead of dropped (R3C N-11).

``CLEAR_STOP_SCRIPT`` points the suite at another copy of the script (a mutant, or the pre-fix version) --
test use only.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_REL = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
SCRIPT_REL = Path("util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py")
HELPER_REL = Path("util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py")
SCRIPT = Path(os.environ.get("CLEAR_STOP_SCRIPT", str(REPO_ROOT / SCRIPT_REL)))

# One short, single-line prose edit whose result is never re-wrapped: the vehicle for the write-path tests.
VEHICLE = "P2 step 4: the watchdog redeploy names the job id (R3B NIT-4)"
# A table-row edit (table rows are never wrapped, so only the width gate stands between it and the file).
ROW_EDIT = "AC-6: provable the day after P0 (round-4 B18)"


def load_script():
    spec = importlib.util.spec_from_file_location("clear_stop_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClearStopScript(unittest.TestCase):
    edits: dict[str, tuple[str, str, int]]
    committed: str

    @classmethod
    def setUpClass(cls):
        cls.mod = load_script()
        cls.edits = {tag: (old, new, count) for tag, old, new, count in cls.mod.EDITS}
        cls.committed = (REPO_ROOT / DESIGN_REL).read_text(encoding="utf-8")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="clear-stop-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for rel, src in ((SCRIPT_REL, SCRIPT), (HELPER_REL, REPO_ROOT / HELPER_REL)):
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, self.tmp / rel)
        (self.tmp / DESIGN_REL).parent.mkdir(parents=True, exist_ok=True)

    # -- helpers ---------------------------------------------------------------------------------------

    def place(self, text: str) -> Path:
        path = self.tmp / DESIGN_REL
        path.write_text(text, encoding="utf-8")
        return path

    def run_script(self, **env_overrides: str) -> subprocess.CompletedProcess:
        env = RedactedEnv(os.environ, PYTHONDONTWRITEBYTECODE="1", **env_overrides)
        if "FIXFWD_PR" not in env_overrides:
            env.pop("FIXFWD_PR", None)
        return subprocess.run([sys.executable, str(SCRIPT_REL)], cwd=self.tmp, env=env, capture_output=True, text=True, timeout=120, check=False)

    def unapplied(self, tag: str) -> str:
        """The committed design with one edit reverted -- the input of a run that must apply exactly that edit."""
        old, new, _count = self.edits[tag]
        self.assertEqual(self.committed.count(new), 1, f"edit {tag!r} is not in the committed design exactly once")
        return self.committed.replace(new, old)

    def assertRefused(self, proc, before: str, code: int, needle: str):
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        self.assertIn(needle, proc.stderr)
        self.assertIn("NOTHING written", proc.stderr)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), before, "the design was written")

    # -- the tests -------------------------------------------------------------------------------------

    def test_committed_design_is_current(self):
        self.place(self.committed)
        proc = self.run_script()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no change", proc.stdout)

    def test_write_then_idempotent(self):
        self.place(self.unapplied(VEHICLE))
        first = self.run_script()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIn("applied 1,", first.stdout)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), self.committed)
        second = self.run_script()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("no change", second.stdout)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), self.committed)

    def test_stray_fence_change_refused(self):
        old, new, _count = self.edits[VEHICLE]
        text = self.committed.replace(new, "4. Watchdog changes (§7.6) -- moved into a fence by this test.")
        fence = text.index("```text\n") + len("```text\n")
        before = self.place(text[:fence] + "   " + old + "\n" + text[fence:]).read_text(encoding="utf-8")
        self.assertRefused(self.run_script(), before, 3, "fenced code block changed beyond FENCE_EDITS")

    def test_over_width_row_refused(self):
        old, new, _count = self.edits[ROW_EDIT]
        self.assertGreater(len(new), len(old))
        text = self.unapplied(ROW_EDIT)
        lines = text.split("\n")
        (i,) = [n for n, line in enumerate(lines) if line.startswith(old)]
        pad = 512 - len(lines[i])
        self.assertGreater(pad, 0)
        lines[i] = old + "x" * pad + lines[i][len(old) :]  # the row is now exactly 512: legal before the edit
        before = self.place("\n".join(lines)).read_text(encoding="utf-8")
        self.assertRefused(self.run_script(), before, 3, "OVER-WIDTH")

    def test_fixfwd_must_be_a_pr_number(self):
        before = self.place(self.unapplied(VEHICLE)).read_text(encoding="utf-8")
        for value in ("ml#FIXFWD", "", "ml#fixfwd", "ml#21x", "ml#"):
            with self.subTest(FIXFWD_PR=value):
                self.assertRefused(self.run_script(FIXFWD_PR=value), before, 3, "FIXFWD_PR")

    def test_reworded_deleted_marker_refused(self):
        anchor = "### P1 — secrets"
        self.assertEqual(self.committed.count(anchor), 1)
        text = self.committed.replace(anchor, "*Held by the STOP at the top of §8 (note 10.1h).*\n\n" + anchor)
        before = self.place(text).read_text(encoding="utf-8")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("`gone` pattern still matches", proc.stderr)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), before)

    def test_marker_reworded_without_held_refused(self):
        """Round 4 (R4C NIT-1, mutant X33): a rewording that drops "held" must not pass as already applied."""
        anchor = "### P1 — secrets"
        for marker in ("*Blocked behind the STOP at the top of §8 (note 10.1g).*", "*Items 2 and 4 wait for the STOP at the top of §8; items 1, 5, 6 and 7 are released.*"):
            with self.subTest(marker=marker):
                before = self.place(self.committed.replace(anchor, marker + "\n\n" + anchor)).read_text(encoding="utf-8")
                proc = self.run_script()
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("`gone` pattern still matches", proc.stderr)
                self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), before)

    def test_unterminated_stop_block_refused(self):
        """Round 4 (R4C mutant X31): a STOP block with no end is refused by the digest gate, not by a crash later."""
        cleared = self.mod.CLEARED
        before = self.place(self.committed.replace(cleared, self.mod.STOP_START + "\n> 1. an item\n")).read_text(encoding="utf-8")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("STOP block differs", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), before)

    def test_changed_stop_block_refused(self):
        cleared = self.mod.CLEARED
        self.assertEqual(self.committed.count(cleared), 1)
        stop = self.mod.STOP_START + "\n>\n> 1. an item as main wrote it\n> 2. an item main added later\n" + self.mod.STOP_END
        before = self.place(self.committed.replace(cleared, stop)).read_text(encoding="utf-8")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("STOP block differs", proc.stderr)
        self.assertEqual((self.tmp / DESIGN_REL).read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
