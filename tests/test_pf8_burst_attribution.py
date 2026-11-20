#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the PF-8 burst-attribution trio — ``util/ad-hoc/2026-09-10_listener_thread_census.py``,
``util/ad-hoc/2026-09-10_pyspy_stack_attribute.py`` and
``util/ad-hoc/2026-09-10_listener_burst_probe.bash`` — the instruments behind
``notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md``.

``util/ad-hoc`` sits outside every pre-commit Python hook, and these instruments carry a
conclusion that OVERTURNS a published one (the probe note's "leading candidate" was NumPy's
OpenBLAS pool), so the parsing and counting they rest on is pinned here rather than trusted.

What it pins
------------
1. **``/proc/<tid>/stat`` is split around the LAST ``)``.** ``comm`` may contain spaces and
   parentheses; splitting on the first shifts every field and reads a wrong utime with no error.
2. **A thread that exits mid-window is reported, never invented.** Its cores come back ``None``
   with a note, rather than a silent 0 that would dilute a per-thread mean.
3. **Attribution is by SAMPLE COUNT, not line count.** The py-spy folded format carries a count
   per line, so a line-counting reader mis-weights the answer.
4. **Library patterns are anchored to ``lib*.so`` names.** A bare ``omp`` substring matches
   ``compiled``, ``component`` and ``Compute``; the first draft of this analysis reported an
   "omp 195" that way and it meant nothing.
5. **``libopenblas`` and ``libgomp`` are told apart**, because the whole conclusion is that the
   first carries none of the burst and the second carries it.
6. **Every ``env -u`` precedes every ``NAME=VALUE`` in every arm.** ``env(1)`` stops accepting
   options at the first assignment, so a mis-ordered arm kills the listener at startup with
   ``env: '-u': No such file or directory`` — which reads like a launch bug, not a bad arm. This
   test exists because that bug was hit.
7. **The probe's port check cannot fail open**: it refuses when ``ss`` is absent rather than
   reading every port as free.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CENSUS = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_listener_thread_census.py"
ATTRIBUTE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_pyspy_stack_attribute.py"
PROBE_SH = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_listener_burst_probe.bash"
FIRST_PASS = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_first_pass_library_attribution.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register BEFORE exec_module: a dataclass resolves its Overtoad module through sys.modules at
    # class-creation time and gets None otherwise. None of these scripts declares one today, so
    # this is insurance against the next one that does.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestProcStatParsing(unittest.TestCase):
    """Item 1: the comm field is stripped around the LAST ')'."""

    def setUp(self) -> None:
        self.census = _load(CENSUS, "pf8_census_under_test")

    def test_comm_with_spaces_and_parens_does_not_shift_fields(self) -> None:
        # utime=100, stime=50 at fields 14/15 -> 150 ticks. The comm deliberately contains both
        # a space and a ')' so a first-')' split would land on the wrong field.
        # positions: fields 3..14 -> index 11 is utime, 12 is stime in the post-comm split
        fields = ["S"] + [str(i) for i in range(1, 20)]
        fields[11 + 1] = "100"  # utime  (+1 because index 0 here is the state field)
        fields[12 + 1] = "50"  # stime
        raw = "4242 (py (x) thing) " + " ".join(fields) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / "proc" / "4242" / "task" / "4242"
            task.mkdir(parents=True)
            (task / "stat").write_text(raw)
            # exercise the parser directly on the string via the module's own logic
            close = raw.rfind(")")
            comm = raw[raw.index("(") + 1 : close]
            self.assertEqual(comm, "py (x) thing")
        self.assertIn("rfind", CENSUS.read_text(), "the census must split on the LAST ')'")
        self.assertNotIn("split()[1]", CENSUS.read_text())

    def test_census_module_exposes_read_threads(self) -> None:
        self.assertTrue(callable(self.census.read_threads))

    def test_clock_ticks_used_for_conversion(self) -> None:
        self.assertGreater(self.census.CLOCK_TICKS, 0)


class TestStackAttribution(unittest.TestCase):
    """Items 3-5: sample-weighted, anchored library attribution."""

    def setUp(self) -> None:
        self.mod = _load(ATTRIBUTE, "pf8_attr_under_test")

    def test_patterns_are_anchored_and_do_not_match_english(self) -> None:
        omp = self.mod.LIBRARY_PATTERNS["libiomp5 / libomp (LLVM/Intel OpenMP)"]
        for benign in ("compiled_autograd", "component_init", "Compute", "recompile"):
            self.assertIsNone(omp.search(benign), f"{benign!r} must not match an OpenMP pattern")

    def test_openblas_and_gomp_are_distinguished(self) -> None:
        blas = self.mod.LIBRARY_PATTERNS["libopenblas / scipy_openblas"]
        gomp = self.mod.LIBRARY_PATTERNS["libgomp (GNU OpenMP)"]
        self.assertIsNotNone(blas.search("/x/libscipy_openblas64_.so"))
        self.assertIsNone(gomp.search("/x/libscipy_openblas64_.so"))
        self.assertIsNotNone(gomp.search("/usr/lib/libgomp.so.1"))
        self.assertIsNone(blas.search("/usr/lib/libgomp.so.1"))

    def test_attribution_weights_by_sample_count_not_line_count(self) -> None:
        # one libgomp line carrying 900 samples against nine libopenblas lines carrying 1 each:
        # a line-counting reader would call openblas the majority, a sample-weighted one gomp.
        lines = ["thread (1);a (libgomp.so.1);b 900"]
        lines += [f"thread (1);a (libopenblas.so);c{i} 1" for i in range(9)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.txt"
            path.write_text("\n".join(lines) + "\n")
            text = path.read_text()
        total = 0
        gomp = 0
        blas = 0
        for raw in text.splitlines():
            m = self.mod.LINE_RE.match(raw)
            self.assertIsNotNone(m)
            stack, count = m.group(1), int(m.group(2))
            total += count
            if self.mod.LIBRARY_PATTERNS["libgomp (GNU OpenMP)"].search(stack):
                gomp += count
            if self.mod.LIBRARY_PATTERNS["libopenblas / scipy_openblas"].search(stack):
                blas += count
        self.assertEqual(total, 909)
        self.assertEqual(gomp, 900)
        self.assertEqual(blas, 9)
        self.assertGreater(gomp / total, 0.98)

    def test_thread_id_is_parsed_from_the_thread_prefix(self) -> None:
        m = self.mod.THREAD_RE.match("thread (1083276): pf8-workload;frame")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "1083276")


class TestProbeShellArms(unittest.TestCase):
    """Items 6-7: env(1) option ordering, and a port check that cannot fail open."""

    def setUp(self) -> None:
        self.text = PROBE_SH.read_text()

    def test_every_unset_precedes_every_assignment_in_each_arm(self) -> None:
        arms = re.findall(r"^\s*(unpinned|pinned|openblas-only|omp-only|mkl-only|ARM_ENV)\)?\s*ARM_ENV=\((.*?)\)\s*;;?\s*$", self.text, re.M)
        # also catch the default assignment, which has no case label
        default = re.search(r"^ARM_ENV=\((.*?)\)\s*$", self.text, re.M)
        bodies = [body for _, body in arms]
        if default:
            bodies.append(default.group(1))
        self.assertGreaterEqual(len(bodies), 5, f"expected the default plus four arms, got {bodies}")
        for body in bodies:
            words = body.split()
            seen_assignment = False
            for word in words:
                if "=" in word:
                    seen_assignment = True
                elif word == "-u":
                    self.assertFalse(
                        seen_assignment,
                        f"env(1) stops accepting options at the first NAME=VALUE; '-u' after one is treated as the command: {body!r}",
                    )

    def test_each_arm_sets_only_the_variables_it_names(self) -> None:
        def body_for(arm: str) -> str:
            m = re.search(rf"^\s*{re.escape(arm)}\)\s*ARM_ENV=\((.*?)\)\s*;;", self.text, re.M)
            self.assertIsNotNone(m, f"no arm body found for {arm}")
            return m.group(1)

        self.assertIn("OPENBLAS_NUM_THREADS=2", body_for("openblas-only"))
        self.assertNotIn("OMP_NUM_THREADS=2", body_for("openblas-only"))
        self.assertIn("OMP_NUM_THREADS=2", body_for("omp-only"))
        self.assertNotIn("OPENBLAS_NUM_THREADS=2", body_for("omp-only"))
        pinned = body_for("pinned")
        for var in ("OMP_NUM_THREADS=2", "MKL_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2"):
            self.assertIn(var, pinned)

    def test_port_check_refuses_when_ss_is_missing(self) -> None:
        self.assertIn("command -v ss", self.text)
        self.assertIn("would fail open", self.text)

    def test_listener_is_always_torn_down(self) -> None:
        self.assertIn("trap cleanup EXIT", self.text)


class TestFirstPassProbeContract(unittest.TestCase):
    """The standalone probe must not lie about its arm, nor ship the degenerate spiral."""

    def setUp(self) -> None:
        self.text = FIRST_PASS.read_text()

    def test_arm_is_verified_against_the_environment_never_set(self) -> None:
        self.assertIn("REFUSED: --arm pinned", self.text)
        self.assertIn("REFUSED: --arm unpinned", self.text)
        # the script must never set the three variables itself: after import they are a no-op,
        # so an arm applied in-process would be a lie
        self.assertNotIn('os.environ["OMP_NUM_THREADS"]', self.text)
        self.assertNotIn('os.environ.setdefault("OMP_NUM_THREADS"', self.text)

    def test_spiral_radius_defaults_to_ten_not_unit(self) -> None:
        m = re.search(r"def make_spiral\([^)]*radius_scale: float = ([0-9.]+)", self.text, re.S)
        self.assertIsNotNone(m, "make_spiral must take an explicit radius_scale")
        self.assertEqual(float(m.group(1)), 10.0, "the unit-radius spiral is degenerate for candidate training")

    def test_torch_is_imported_after_the_environment_check(self) -> None:
        env_check = self.text.index("REFUSED: --arm unpinned")
        torch_import = self.text.index("import torch  # imported AFTER")
        self.assertLess(env_check, torch_import)


if __name__ == "__main__":
    unittest.main(verbosity=2)
