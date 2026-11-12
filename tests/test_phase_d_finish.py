#!/usr/bin/env python3
"""``util/ad-hoc/2026-11-11_phase_d_finish.{py,bash}``: Phase D's remaining root steps as verbs with fixed predicates.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

The Phase D sitting (recovery plan section 6.4) ran until 2026-11-11 on command blocks written by hand for one use,
and four of its corrections were defects in those blocks. The finish tool moves the remaining root steps -- AC-4's
two restore drills, the retention aside copy, AC-6's fileset check -- into verbs whose every decision is a function
tested here. Five rules, one group of tests each:

1. **A marker is pinned against the code that writes it.** ``DrillLinePins`` renders the AC-4 driver's own
   f-strings from its source and requires the tool's pattern for each line to match, so a reworded driver line
   fails here instead of reading as "line absent" at the sitting. ``ServerTaskTest`` feeds the API client's real
   ``serverstate`` output to the reader that decides whether a backup is running.
2. **A time window is inclusive at its edge and is tested at the edge.** A fileset exactly at a retention frame's
   lower bound; a live snapshot written exactly at a fileset's start; an entry dated exactly at the timer's
   re-enable, and exactly when the fileset was complete.
3. **The pass rule is recomputed, never taken on trust.** A drill's verdict is rebuilt from its numbers with AC-4's
   own floors and must agree with the driver's ``RESULT`` line and exit code; each way it can disagree is a case.
4. **An empty or unparseable input is ERROR, never PASS.** An empty output, a fileset that yields no entries, an
   unreadable Dropbox root, a destination with no dlist, a dlist that cannot be opened.
5. **An output is one driver run or it is nothing.** Added 2026-11-12 after a review found three ways to a false
   PASS: a FATAL beside a RESULT, a second run appended to the file, and a sampled path with a newline in it that
   supplies the summary lines itself. Each is a case in ``StrictOutputTest``.

Nothing here needs root, a Duplicati binary, the destination or a secret: the driver is replaced by a function that
writes a canned output, and every path is a temporary directory.
"""

from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
import zipfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import load_ad_hoc

REPO_ROOT = Path(__file__).resolve().parents[1]
AD_HOC = REPO_ROOT / "util" / "ad-hoc"
TOOL = AD_HOC / "2026-11-11_phase_d_finish.py"
WRAPPER = AD_HOC / "2026-11-11_phase_d_finish.bash"
DRIVER = AD_HOC / "2026-11-09_ac4_restore_drill.py"
UTC = dt.timezone.utc


def load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


finish = load_by_path("phase_d_finish_under_test", TOOL)
retention = finish.load_module(finish.RETENTION_TABLE, "phase_d_retention_table_under_test")

DRILL1 = finish.DRILLS["1"]
FIXTURE_DEST = "/mnt/dest"
FINGERPRINT = "0123456789abcdef"
# The destination's sixteen dlists as they stood on 2026-11-11 (names only; the sitting's running record).
DLISTS_2026_11_11 = [
    "duplicati-20260825T102739Z.dlist.zip.aes",
    "duplicati-20260901T140000Z.dlist.zip.aes",
    "duplicati-20260908T140000Z.dlist.zip.aes",
    "duplicati-20260912T140000Z.dlist.zip.aes",
    "duplicati-20260915T085649Z.dlist.zip.aes",
    "duplicati-20260915T204850Z.dlist.zip.aes",
    "duplicati-20260916T183346Z.dlist.zip.aes",
    "duplicati-20260917T221344Z.dlist.zip.aes",
    "duplicati-20260918T140000Z.dlist.zip.aes",
    "duplicati-20261107T212908Z.dlist.zip.aes",
    "duplicati-20261108T140001Z.dlist.zip.aes",
    "duplicati-20261108T234122Z.dlist.zip.aes",
    "duplicati-20261109T140001Z.dlist.zip.aes",
    "duplicati-20261110T003622Z.dlist.zip.aes",
    "duplicati-20261110T140000Z.dlist.zip.aes",
    "duplicati-20261111T140001Z.dlist.zip.aes",
]
FIVE_PRE_RECOVERY = [f"duplicati-{stamp}.dlist.zip.aes" for stamp in ("20260912T140000Z", "20260915T085649Z", "20260916T183346Z", "20260917T221344Z", "20260918T140000Z")]


def dlist_name(when: dt.datetime) -> str:
    return f"duplicati-{when.strftime('%Y%m%dT%H%M%SZ')}.dlist.zip.aes"


def summary_lines(*, dlist=DRILL1, version=7, verified=18, picked=18, floor=15, live=18, contradiction=0, live_floor=5, absent=True, rejected=True, result="PASS") -> list[str]:
    """The five lines the driver ends on, in its own wording."""
    return [
        f"drilled     : {dlist} (--version={version})",
        f"VERIFIED    : {verified}/{picked} (SHA-256 + length vs the dlist manifest; AC-4 floor {floor})",
        f"live oracle : {live} match, {contradiction} contradiction (floor {live_floor})",
        f"negative    : not-in-fileset path absent={absent}; flipped-byte copy rejected={rejected}",
        f"RESULT: {result}",
    ]


def restore_line(rc=0, seconds=1234) -> str:
    return f"restore     : duplicati-cli rc={rc} in {seconds}s (0 ok, 1 nothing changed, 2 warnings, >=3 errors; log restore.log)"


def drill_output(*, dlist=DRILL1, version=7, rc=0, seconds=1234, run_dir="/root/phase-d-tmp/ac4-20260918T140000-20261112-010203", dest=FIXTURE_DEST, candidates=18, paths=None, destination_version=None, **summary) -> str:
    """A complete driver output, line for line in the driver's own wording (``DrillLinePins`` holds that wording true).

    ``paths`` replaces the sampled paths (one per candidate); ``summary`` goes to :func:`summary_lines`.
    """
    paths = paths if paths is not None else [f"/home/x/project/file{i}.py" for i in range(candidates)]
    lines = [
        "run root    : /root/phase-d-tmp on / (ext4), 301 GiB free",
        f"run dir     : {run_dir}",
        f"destination : {dest} (16 dlists); drilling {dlist} = --version={version if destination_version is None else destination_version}",
        "oracle epoch: 1789826400 (2026-09-18T14:00:00Z)",
        f"credential  : /x/env key=PASSPHRASE (sha256[:16]={FINGERPRINT})",
        "fileset     : 1164145 entries; eligible small=513163 multi=2008 large=6 empty=2019",
    ]
    lines += [f"  [small]        1024 B  static=True   {path}" for path in paths]
    lines += ["  [  neg] (not in fileset)  /home/x/.phase-d-ac4-negative-control-000000001.txt", restore_line(rc, seconds)]
    lines += [f"  [small] VERIFIED         live=match  {path}" for path in paths]
    lines += [""] + summary_lines(dlist=dlist, version=version, **summary)
    return "\n".join(lines) + "\n"


def quick_shred(path: str) -> tuple[int, list[str]]:
    """``shred_tree`` without the overwrite passes, for the verb tests: what is removed matters there, how does not.

    ``ShredTest`` and one test of each verb run the real ``shred``.
    """
    count = sum(len(names) for _root, _dirs, names in os.walk(path))
    shutil.rmtree(path)
    return count, []


def cached_sha256(path, dir_fd=None) -> tuple[str, bool]:
    """``media_sha256`` through the page cache, for the aside tests whose subject is not the read-back itself."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
    try:
        return finish.fd_sha256(fd), False
    finally:
        os.close(fd)


def judge(text: str, exit_code: int | None = 0, expect: str = DRILL1, dest: str = FIXTURE_DEST):
    return finish.judge_drill(finish.parse_drill_output(text), exit_code, expect, dest)


class DrillLinePins(unittest.TestCase):
    """Rule 1: every pattern the tool reads the driver's output with matches a line the driver's SOURCE can print."""

    SAMPLES = {
        "neg_a": "True",
        "neg_b": "False",
        "args.dlist": DRILL1,
        "run_dir": "/root/phase-d-tmp/ac4-x",
        "dest": FIXTURE_DEST,
        "c['stratum']": "small",
        "static(c)": "True",
        "c['path']": "/home/x/project/file.py",
        "hashlib.sha256(value.encode()).hexdigest()[:16]": FINGERPRINT,
    }

    rendered: list[str]
    constants: set[str]

    @classmethod
    def setUpClass(cls) -> None:
        tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
        cls.rendered = []
        cls.constants = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                cls.constants.add(node.value)
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print" and node.args and isinstance(node.args[0], ast.JoinedStr)):
                continue
            parts = []
            for value in node.args[0].values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif isinstance(value, ast.FormattedValue):
                    parts.append(cls.render(value))
            cls.rendered.append("".join(parts))

    @classmethod
    def render(cls, value: ast.FormattedValue) -> str:
        """A sample for one ``{...}``, padded by its format spec when the spec is a constant that fits a string."""
        text = cls.SAMPLES.get(ast.unparse(value.value), "7")
        spec = ""
        if isinstance(value.format_spec, ast.JoinedStr):
            for piece in value.format_spec.values:
                if not isinstance(piece, ast.Constant):
                    return text
                spec += str(piece.value)
        try:
            return format(text, spec)
        except ValueError:  # a numeric spec (.0f, 09d) on a sample string: the sample stands as it is
            return text

    def test_the_driver_source_was_read(self) -> None:
        # A parse that found nothing would let every other test here pass by vacuity.
        self.assertGreaterEqual(len(self.rendered), 12, self.rendered)

    def test_each_judged_line_is_one_the_driver_prints(self) -> None:
        for key in ("run_dir", "destination", "restore", "drilled", "verified", "live", "negative", "fatal"):
            with self.subTest(line=key):
                matches = [line for line in self.rendered if finish.DRILL_LINES[key].match(line)]
                self.assertTrue(matches, f"no line the driver prints matches DRILL_LINES[{key!r}]: {finish.DRILL_LINES[key].pattern}")

    def test_the_result_line_is_the_drivers_two_constants(self) -> None:
        for constant in ("RESULT: PASS", "RESULT: FAIL"):
            self.assertIn(constant, self.constants)
            self.assertIsNotNone(finish.DRILL_LINES["result"].match(constant))

    def test_the_driver_order_is_the_order_of_its_print_statements(self) -> None:
        # ast.walk is breadth-first, so order is read from line numbers instead.
        source = DRIVER.read_text(encoding="utf-8").splitlines()
        markers = {"run_dir": 'print(f"run dir     :', "destination": 'print(f"destination :', "restore": 'print(f"restore     :', "drilled": 'print(f"drilled     :', "verified": 'print(f"VERIFIED    :', "live": 'print(f"live oracle :', "negative": 'print(f"negative    :', "result": 'print("RESULT: PASS"'}
        where = {key: next(i for i, line in enumerate(source) if marker in line) for key, marker in markers.items()}
        self.assertEqual(tuple(sorted(where, key=lambda key: where[key])), finish.DRIVER_ORDER)
        self.assertEqual(where["result"], max(i for i, line in enumerate(source) if "print(" in line), "RESULT is the last line the driver prints")

    def test_the_candidate_line_is_the_one_printed_before_the_restore(self) -> None:
        matches = [line for line in self.rendered if finish.CANDIDATE_LINE.match(line)]
        self.assertEqual(len(matches), 1, self.rendered)
        self.assertIn("static=True ", matches[0])
        for other in ("  [small] VERIFIED         live=match  /home/x/project/file.py", "  [  neg] (not in fileset)  /home/x/.phase-d-ac4-negative-control-000000001.txt", " [small]        1024 B  static=True   /x"):
            self.assertIsNone(finish.CANDIDATE_LINE.match(other), other)

    def test_the_credential_line_carries_the_prefix_this_tool_withholds(self) -> None:
        lines = [line for line in self.rendered if line.startswith("credential  :")]
        self.assertEqual(len(lines), 1, self.rendered)
        self.assertIn(FINGERPRINT, lines[0])
        withheld = finish.withhold_fingerprint(lines[0])
        self.assertNotIn(FINGERPRINT, withheld)
        self.assertTrue(withheld.endswith(finish.FINGERPRINT_WITHHELD), withheld)
        self.assertEqual(finish.withhold_fingerprint("fileset     : 1164145 entries"), "fileset     : 1164145 entries")

    def test_the_canned_output_uses_the_drivers_wording(self) -> None:
        # The fixture every judge test stands on: each of its judged lines must also be a rendering of the source.
        parsed = finish.parse_drill_output(drill_output())
        self.assertEqual(tuple(parsed["order"]), finish.DRIVER_ORDER)
        self.assertEqual((parsed["candidates"], parsed["repeated"], parsed["trailing"]), (18, [], 0))
        prefixes = {line.split(":")[0] for line in self.rendered if ":" in line}
        for label in ("run dir     ", "destination ", "restore     ", "drilled     ", "VERIFIED    ", "live oracle ", "negative    ", "credential  "):
            self.assertIn(label, prefixes)

    def test_a_reworded_line_is_not_matched(self) -> None:
        # The negative control for this class: the pin must be able to fail.
        self.assertIsNone(finish.DRILL_LINES["verified"].match("VERIFIED: 18/18 files"))
        self.assertIsNone(finish.DRILL_LINES["negative"].match("negative    : not-in-fileset path absent=yes; flipped-byte copy rejected=yes"))


class JudgeDrillTest(unittest.TestCase):
    """Rule 3: the verdict is recomputed from the numbers and must agree with the driver."""

    def test_a_clean_drill_passes(self) -> None:
        verdict, reasons, numbers = judge(drill_output())
        self.assertEqual((verdict, reasons), ("PASS", []))
        self.assertEqual((numbers["verified"], numbers["picked"], numbers["live_match"], numbers["rc"], numbers["recomputed"], numbers["candidates"]), (18, 18, 18, 0, "PASS", 18))

    def test_an_adopted_output_passes_without_an_exit_code(self) -> None:
        self.assertEqual(judge(drill_output(), exit_code=None)[0], "PASS")

    def test_warnings_from_the_restore_do_not_fail_it(self) -> None:
        self.assertEqual(judge(drill_output(rc=2))[0], "PASS")

    def test_each_deviation_fails_for_its_own_reason(self) -> None:
        cases: dict[str, tuple[dict, int]] = {
            "rc=3": ({"rc": 3, "result": "FAIL"}, 1),
            "verified 17 of 18": ({"verified": 17, "result": "FAIL"}, 1),
            "verified 14 files": ({"verified": 14, "picked": 14, "candidates": 14, "result": "FAIL"}, 1),
            "contradict": ({"contradiction": 1, "result": "FAIL"}, 1),
            "live oracle engaged on 4": ({"live": 4, "result": "FAIL"}, 1),
            "negative control (a)": ({"absent": False, "result": "FAIL"}, 1),
            "negative control (b)": ({"rejected": False, "result": "FAIL"}, 1),
        }
        for needle, (overrides, exit_code) in cases.items():
            with self.subTest(case=needle):
                verdict, reasons, _numbers = judge(drill_output(**overrides), exit_code)
                self.assertEqual(verdict, "FAIL")
                self.assertTrue(any(needle in reason for reason in reasons), reasons)
                self.assertFalse(any("INCONSISTENT" in reason for reason in reasons), reasons)

    def test_a_restore_killed_by_a_signal_fails_though_the_driver_passes_it(self) -> None:
        # The driver's own rule is `rc < 3`, which a negative return code satisfies.
        verdict, reasons, numbers = judge(drill_output(rc=-9))
        self.assertEqual((verdict, numbers["rc"]), ("FAIL", -9))
        joined = " | ".join(reasons)
        self.assertIn("killed by a signal", joined)
        self.assertIn("INCONSISTENT: the driver says RESULT: PASS", joined)
        self.assertEqual(judge(drill_output(rc=0))[0], "PASS")
        self.assertEqual(judge(drill_output(rc=-1))[0], "FAIL", "the edge: the first return code below zero")

    def test_a_lowered_floor_cannot_pass(self) -> None:
        # `--min-verified 3` makes the driver print RESULT: PASS on three files. AC-4 asks for fifteen.
        verdict, reasons, _numbers = judge(drill_output(verified=3, picked=3, floor=3, candidates=3, live=3, live_floor=0))
        self.assertEqual(verdict, "FAIL")
        joined = " | ".join(reasons)
        self.assertIn("floor was lowered to 3", joined)
        self.assertIn("live-oracle floor was lowered to 0", joined)
        self.assertIn("INCONSISTENT", joined)

    def test_a_result_line_the_numbers_do_not_support_is_inconsistent(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(contradiction=2, result="PASS"))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("INCONSISTENT: the driver says RESULT: PASS" in reason for reason in reasons), reasons)

    def test_a_fail_line_over_passing_numbers_is_inconsistent(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(result="FAIL"), exit_code=1)
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("recompute to PASS" in reason for reason in reasons), reasons)

    def test_an_exit_code_that_contradicts_the_result_line_is_inconsistent(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(), exit_code=1)
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("exited 1 but printed RESULT: PASS" in reason for reason in reasons), reasons)

    def test_another_filesets_output_is_not_this_drills(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(dlist=finish.DRILLS["2"]))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("not " + DRILL1 in reason for reason in reasons), reasons)

    def test_a_restore_from_another_directory_is_not_this_drill(self) -> None:
        # A hand run with --dest pointing at a copy would otherwise pass AC-4 and unlock `aside`.
        verdict, reasons, _numbers = judge(drill_output(dest="/root/some-copy"))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("not from the destination " + FIXTURE_DEST in reason for reason in reasons), reasons)
        self.assertEqual(judge(drill_output(dest=FIXTURE_DEST + "/"))[0], "PASS", "a trailing slash is the same directory")
        self.assertEqual(judge(drill_output(), dest=FIXTURE_DEST + "-other")[0], "FAIL")

    def test_the_two_lines_that_name_the_fileset_must_agree(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(destination_version=8))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("name different filesets" in reason for reason in reasons), reasons)

    def test_the_sampled_file_count_must_be_the_verified_lines(self) -> None:
        verdict, reasons, _numbers = judge(drill_output(candidates=17))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("lists 17 sampled files but its VERIFIED line counts 18" in reason for reason in reasons), reasons)

    def test_an_empty_output_is_an_error_not_a_pass(self) -> None:
        for text in ("", "\n\n", finish.BOM):
            with self.subTest(text=repr(text)):
                verdict, reasons, numbers = judge(text, exit_code=None)
                self.assertEqual(verdict, "ERROR")
                self.assertIn("incomplete", reasons[0])
                self.assertEqual(numbers, {})

    def test_a_missing_judged_line_is_an_error(self) -> None:
        labels = (("run_dir", "run dir     :"), ("destination", "destination :"), ("restore", "restore     :"), ("drilled", "drilled     :"), ("verified", "VERIFIED    :"), ("live", "live oracle :"), ("negative", "negative    :"), ("result", "RESULT:"))
        self.assertEqual(tuple(key for key, _label in labels), finish.DRIVER_ORDER, "every line of the order is a case here")
        for key, label in labels:
            with self.subTest(missing=key):
                text = "\n".join(line for line in drill_output().splitlines() if not line.startswith(label)) + "\n"
                verdict, reasons, _numbers = judge(text)
                self.assertEqual(verdict, "ERROR")
                self.assertIn(f"no {key} line", reasons[0])

    def test_a_driver_that_stopped_is_an_error_with_its_own_message(self) -> None:
        text = "\n".join(drill_output().splitlines()[:8]) + "\nFATAL: the destination's dlist list changed during the restore; --version no longer names the drilled fileset -- rerun\n"
        verdict, reasons, _numbers = judge(text, exit_code=2)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("dlist list changed", reasons[0])
        self.assertNotIn("RESULT line is present too", reasons[0])

    def test_a_bom_and_crlf_do_not_hide_the_lines(self) -> None:
        # The BOM sits in front of a JUDGED line: an output need not open with the driver's `run root` line.
        body = "\n".join(drill_output().splitlines()[1:]) + "\n"
        self.assertTrue(body.startswith("run dir     :"))
        self.assertEqual(judge(finish.BOM + body.replace("\n", "\r\n"))[0], "PASS")
        self.assertEqual(len(finish.BOM), 1)
        self.assertEqual(ord(finish.BOM), 0xFEFF)


class StrictOutputTest(unittest.TestCase):
    """Rule 5: an output is one complete driver run, or nothing in it is judged."""

    SECOND_RUN = "run root    : /root/phase-d-tmp on / (ext4), 301 GiB free\nrun dir     : /root/phase-d-tmp/ac4-20260918T140000-20261112-020202\nFATAL: the destination's dlist list changed during the restore; rerun\n"

    def injected(self, *, tail: str = ".txt", first: bool = False) -> tuple[str, list[str]]:
        """A sampled path with newlines in it that spells out the lines after the restore, RESULT: PASS included."""
        fake = ["/home/x/a", restore_line(rc=0, seconds=1)] + summary_lines() + [tail]
        paths = [f"/home/x/project/file{i}.py" for i in range(17)]
        hostile = "\n".join(fake)
        return hostile, ([hostile] + paths if first else paths + [hostile])

    def test_a_fatal_beside_a_result_is_an_error(self) -> None:
        # A complete PASS run, then a second run that stopped: the first run's RESULT must not carry the file.
        parsed = finish.parse_drill_output(drill_output() + self.SECOND_RUN)
        verdict, reasons, numbers = finish.judge_drill(parsed, None, DRILL1, FIXTURE_DEST)
        self.assertEqual((verdict, numbers), ("ERROR", {}))
        self.assertIn("dlist list changed", reasons[0])
        self.assertIn("a RESULT line is present too", reasons[0])
        self.assertEqual(parsed["run_dir"]["run_dir"], "/root/phase-d-tmp/ac4-20260918T140000-20261112-010203", "the first run directory is the one named, never a later line's")

    def test_two_complete_runs_in_one_file_are_an_error(self) -> None:
        verdict, reasons, _numbers = judge(drill_output() + drill_output(verified=17, result="FAIL"), exit_code=None)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("more than one", reasons[0])
        self.assertIn("`result`", reasons[0])

    def test_a_second_run_dir_line_is_an_error_even_alone(self) -> None:
        text = drill_output().replace("oracle epoch:", "run dir     : /root/phase-d-tmp/ac4-other\noracle epoch:")
        verdict, reasons, _numbers = judge(text)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("`run_dir`", reasons[0])

    def test_a_newline_in_a_sampled_path_cannot_supply_the_lines_of_a_run_that_stopped(self) -> None:
        # The run is killed after its candidate listing, so the only restore..RESULT lines are the path's own.
        for first in (False, True):
            with self.subTest(hostile_path_first=first):
                _hostile, paths = self.injected(first=first)
                complete = drill_output(paths=paths)
                killed = complete[: complete.index("restore     : duplicati-cli rc=0 in 1234s")]
                parsed = finish.parse_drill_output(killed)
                self.assertEqual(tuple(parsed["order"]), finish.DRIVER_ORDER, "the injected lines do complete the set, in order")
                self.assertEqual(parsed["repeated"], [])
                verdict, reasons, numbers = finish.judge_drill(parsed, None, DRILL1, FIXTURE_DEST)
                self.assertEqual((verdict, numbers), ("ERROR", {}))
                self.assertIn("follow the RESULT line", reasons[0])

    def test_a_newline_in_a_sampled_path_cannot_hide_inside_a_complete_run(self) -> None:
        _hostile, paths = self.injected()
        verdict, reasons, _numbers = judge(drill_output(paths=paths, verified=3, result="FAIL"), exit_code=1)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("more than one", reasons[0])

    def test_anything_after_the_result_line_is_an_error(self) -> None:
        verdict, reasons, _numbers = judge(drill_output() + "exit=0\n", exit_code=None)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("1 line(s) follow the RESULT line", reasons[0])
        self.assertEqual(judge(drill_output() + "\n  \n\r\n")[0], "PASS", "blank lines are not content")

    def test_lines_out_of_the_drivers_order_are_an_error(self) -> None:
        lines = drill_output().splitlines()
        drilled = next(i for i, line in enumerate(lines) if line.startswith("drilled     :"))
        lines[drilled], lines[drilled + 1] = lines[drilled + 1], lines[drilled]
        verdict, reasons, _numbers = judge("\n".join(lines) + "\n")
        self.assertEqual(verdict, "ERROR")
        self.assertIn("not in the driver's order", reasons[0])

    def test_only_a_newline_ends_a_line(self) -> None:
        # str.splitlines() also breaks at a form feed and at U+2028; a path may hold either, and the driver prints it whole.
        for separator in (chr(0x0C), chr(0x2028), chr(0x85), "\r"):
            with self.subTest(separator=hex(ord(separator))):
                paths = [f"/home/x/project/file{i}.py" for i in range(17)] + [f"/home/x/a{separator}RESULT: PASS"]
                parsed = finish.parse_drill_output(drill_output(paths=paths))
                self.assertEqual((parsed["repeated"], parsed["candidates"]), ([], 18))
                self.assertEqual(finish.judge_drill(parsed, 0, DRILL1, FIXTURE_DEST)[0], "PASS")


class ShredTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "run-root"
        self.root.mkdir(mode=0o700)
        self.uid = os.geteuid()

    def make(self, name: str = "ac4-20260918T140000-20261112-010203") -> Path:
        run_dir = self.root / name
        (run_dir / "work").mkdir(parents=True)
        # One-character names: `shred -u` renames a file once per character of its name, syncing each time.
        (run_dir / "work" / "z").write_bytes(b"decrypted" * 100)
        (run_dir / "restored" / "a" / "b").mkdir(parents=True)
        (run_dir / "restored" / "a" / "b" / "f").write_text("x")
        return run_dir

    def test_a_run_directory_is_shredded_whole(self) -> None:
        run_dir = self.make()
        files, failures = finish.shred_tree(finish.check_run_dir(str(run_dir), str(self.root), self.uid))
        self.assertEqual((files, failures), (2, []))
        self.assertFalse(run_dir.exists())

    def test_a_symlink_inside_is_unlinked_not_followed(self) -> None:
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("keep me")
        run_dir = self.make()
        (run_dir / "work" / "link").symlink_to(outside)
        (run_dir / "dirlink").symlink_to(Path(self.tmp.name))
        _files, failures = finish.shred_tree(str(run_dir))
        self.assertEqual(failures, [])
        self.assertEqual(outside.read_text(), "keep me")
        self.assertFalse(run_dir.exists())

    def test_refusals(self) -> None:
        good = self.make()
        nested = good / "work"
        misnamed = self.root / "important-records"
        misnamed.mkdir()
        a_file = self.root / "ac4-file"
        a_file.write_text("x")
        link = self.root / "ac4-link"
        link.symlink_to(good)
        elsewhere = Path(self.tmp.name) / "ac4-elsewhere"
        elsewhere.mkdir()
        for path, needle in ((nested, "not directly under"), (misnamed, "not an ac4-* or ac6-*"), (a_file, "not a directory"), (link, "symlink"), (elsewhere, "not directly under"), (self.root, "not directly under")):
            with self.subTest(path=path.name):
                with self.assertRaises(finish.Refused) as caught:
                    finish.check_run_dir(str(path), str(self.root), self.uid)
                self.assertIn(needle, str(caught.exception))
        with self.assertRaises(finish.Refused) as caught:
            finish.check_run_dir(str(good), str(self.root), self.uid + 1)
        self.assertIn("not owned by uid", str(caught.exception))
        self.assertTrue(good.exists(), "a refusal must leave the directory alone")

    def test_a_directory_it_may_not_touch_is_reported_as_a_failure(self) -> None:
        elsewhere = Path(self.tmp.name) / "ac4-elsewhere"
        elsewhere.mkdir()
        files, failures = finish.shred_run_dir(str(elsewhere), str(self.root), self.uid)
        self.assertEqual(files, 0)
        self.assertEqual(len(failures), 1)
        self.assertIn("not directly under", failures[0])
        self.assertTrue(elsewhere.exists())


class ShredVerbTest(unittest.TestCase):
    """`shred`: the verb for a run directory that a failed drill, or the 2026-11-09 select-only run, left behind."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "run-root"
        self.root.mkdir(mode=0o700)
        os.chmod(self.root, 0o700)
        self.run_dir = self.root / "ac4-20260918T140000-20261109-050909"
        self.run_dir.mkdir()
        (self.run_dir / "z").write_bytes(b"decrypted")

    def shred(self, run_dir: Path) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = finish.cmd_shred(argparse.Namespace(run_root=str(self.root), run_dir=str(run_dir)), owner_uid=os.geteuid())
        return code, buffer.getvalue()

    def test_a_kept_run_directory_is_shredded(self) -> None:
        code, text = self.shred(self.run_dir)
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("shredded    : 1 file(s)", text)
        self.assertIn("VERDICT: PASS", text)
        self.assertFalse(self.run_dir.exists())

    def test_only_a_run_directory_of_a_private_run_root_is_shredded(self) -> None:
        other = self.root / "records"
        other.mkdir()
        with self.assertRaises(finish.Refused):
            self.shred(other)
        os.chmod(self.root, 0o740)
        try:
            with self.assertRaises(finish.Refused) as caught:
                self.shred(self.run_dir)
        finally:
            os.chmod(self.root, 0o700)
        self.assertIn("mode 0740", str(caught.exception))
        self.assertTrue((self.run_dir / "z").exists())

    def test_a_file_that_cannot_be_removed_is_an_error(self) -> None:
        with mock.patch.object(finish, "shred_tree", return_value=(0, [str(self.run_dir / "z")])):
            code, text = self.shred(self.run_dir)
        self.assertEqual(code, finish.EXIT_ERROR)
        self.assertIn("1 path(s) could NOT be removed", text)
        self.assertIn("VERDICT: ERROR", text)


class RunRootTest(unittest.TestCase):
    """Verdict records are read from the run root and decrypted dlists are written into it: it must be root's alone."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "run-root"
        self.root.mkdir(mode=0o700)
        os.chmod(self.root, 0o700)
        self.uid = os.geteuid()

    def test_a_private_directory_of_ours_is_accepted(self) -> None:
        self.assertEqual(finish.check_run_root(str(self.root), self.uid), os.path.realpath(self.root))

    def test_any_access_for_group_or_other_is_refused(self) -> None:
        for mode in (0o710, 0o750, 0o701, 0o705, 0o770, 0o777):
            with self.subTest(mode=oct(mode)):
                os.chmod(self.root, mode)
                with self.assertRaises(finish.Refused) as caught:
                    finish.check_run_root(str(self.root), self.uid)
                self.assertIn(f"mode {mode:04o}", str(caught.exception))
        os.chmod(self.root, 0o700)

    def test_another_owner_a_symlink_a_file_and_a_missing_path_are_refused(self) -> None:
        link, a_file = Path(self.tmp.name) / "link", Path(self.tmp.name) / "file"
        link.symlink_to(self.root)
        a_file.write_text("x")
        for path, uid, needle in ((self.root, self.uid + 1, "must be owned by uid"), (link, self.uid, "a symlink is refused"), (a_file, self.uid, "not a directory"), (Path(self.tmp.name) / "missing", self.uid, "does not exist")):
            with self.subTest(path=path.name):
                with self.assertRaises(finish.Refused) as caught:
                    finish.check_run_root(str(path), uid)
                self.assertIn(needle, str(caught.exception))

    def test_a_verdict_is_not_written_through_a_planted_symlink(self) -> None:
        target = Path(self.tmp.name) / "target.txt"
        target.write_text("keep me")
        (self.root / "ac4-drill1.verdict.json.new").symlink_to(target)
        with self.assertRaises(OSError):
            finish.write_verdict(str(self.root), "ac4-drill1", {"verdict": "PASS"})
        self.assertEqual(target.read_text(), "keep me")
        self.assertIsNone(finish.read_verdict(str(self.root), "ac4-drill1"))


class DrillVerbTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root, self.dest = base / "run-root", base / "dest"
        self.root.mkdir(mode=0o700)
        os.chmod(self.root, 0o700)
        self.dest.mkdir()
        for name in DLISTS_2026_11_11:
            (self.dest / name).write_bytes(b"x")
        self.run_dir = self.root / "ac4-20260918T140000-20261112-010203"
        self.out = self.root / "ac4-drill1.out"
        self.ran: list[str] = []
        self.quick = mock.patch.object(finish, "shred_tree", side_effect=quick_shred)
        self.quick.start()
        self.addCleanup(self.quick.stop)

    def args(self, **overrides) -> argparse.Namespace:
        values: dict = {"n": "1", "run_root": str(self.root), "dest": str(self.dest), "rerun": False, "allow_active_task": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def output(self, **overrides) -> str:
        values: dict = {"run_dir": str(self.run_dir), "dest": os.path.realpath(self.dest)}
        values.update(overrides)
        return drill_output(**values)

    def fake_run(self, text: str, exit_code: int = 0):
        def run(dlist, dest, run_root, out_path):
            self.ran.append(dlist)
            self.run_dir.mkdir(mode=0o700, exist_ok=True)
            (self.run_dir / "dlist.zip").write_bytes(b"decrypted")
            Path(out_path).write_text(text, encoding="utf-8")
            return exit_code

        return run

    def never_run(self, *_args):
        raise AssertionError("the driver must not run")

    def drill(self, args, *, run=None, task=None) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer), mock.patch.object(finish, "source_home", return_value="/nonexistent-home"):
            code = finish.cmd_drill(args, run=run or self.never_run, task=task or (lambda _home: ("idle", "no active task; ProgramState=Running")), owner_uid=os.geteuid())
        return code, buffer.getvalue()

    def record(self) -> dict:
        return json.loads((self.root / "ac4-drill1.verdict.json").read_text())

    def test_an_existing_output_is_adopted_and_the_driver_is_not_run(self) -> None:
        self.quick.stop()  # this one test of the verb runs the real shred
        self.run_dir.mkdir(mode=0o700)
        (self.run_dir / "dlist.zip").write_bytes(b"decrypted")
        self.out.write_text(self.output())
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("ADOPTED", text)
        self.assertIn("VERDICT: PASS", text)
        record = self.record()
        self.assertEqual((record["verdict"], record["adopted"], record["dlist"], record["run_dir"]), ("PASS", True, DRILL1, "shredded"))
        self.assertEqual((record["driver_ran_here"], record["schema"], record["tool_version"]), (False, "phase-d-drill/2", finish.VERSION))
        self.assertEqual(record["driver_sha256_when_judged"], hashlib.sha256(DRIVER.read_bytes()).hexdigest())
        self.assertFalse(self.run_dir.exists(), "a passed drill's run directory holds a decrypted dlist and is shredded")
        self.assertTrue(self.out.exists(), "the output is the evidence and stays")
        self.assertNotIn(FINGERPRINT, text, "an adopted output's lines are parsed, never printed")

    def test_the_summary_names_the_bytes_that_ran(self) -> None:
        self.out.write_text(self.output())
        _code, text = self.drill(self.args())
        summary = text[text.index("-- summary of drill 1") :]
        for label, path in (("tool        : ", TOOL), ("wrapper     : ", WRAPPER), ("driver      : ", DRIVER)):
            line = next(line for line in summary.splitlines() if line.startswith(label))
            self.assertIn(f"sha256[:16]={hashlib.sha256(path.read_bytes()).hexdigest()[:16]}", line)
        self.assertIn("source      : an ADOPTED output", summary)

    def test_an_adopted_failure_keeps_the_run_directory(self) -> None:
        self.run_dir.mkdir(mode=0o700)
        (self.run_dir / "restore.log").write_text("evidence")
        self.out.write_text(self.output(verified=17, result="FAIL"))
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_FAIL)
        self.assertIn("KEPT at", text)
        self.assertTrue((self.run_dir / "restore.log").exists())
        self.assertEqual(self.record()["verdict"], "FAIL")

    def test_two_runs_in_one_adopted_file_shred_nothing(self) -> None:
        # The file's first run passed and its second stopped. Read loosely, this was PASS with the SECOND run's
        # directory shredded and the first one's decrypted dlist left on disk under a record saying "shredded".
        second = self.root / "ac4-20260918T140000-20261112-020202"
        for run_dir in (self.run_dir, second):
            run_dir.mkdir(mode=0o700)
            (run_dir / "dlist.zip").write_bytes(b"decrypted")
        self.out.write_text(self.output() + f"run dir     : {second}\nFATAL: the destination's dlist list changed during the restore; rerun\n")
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_ERROR)
        self.assertIn("VERDICT: ERROR", text)
        self.assertTrue((self.run_dir / "dlist.zip").exists())
        self.assertTrue((second / "dlist.zip").exists())
        self.assertEqual(self.record()["run_dir"], str(self.run_dir), "the record names the directory that is still there")

    def test_a_stopped_run_is_an_error_and_rerun_moves_it_aside(self) -> None:
        self.out.write_text("run dir     : /nowhere\nFATAL: the destination's dlist list changed during the restore; rerun\n")
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_ERROR)
        self.assertIn("dlist list changed", text)
        code, text = self.drill(self.args(rerun=True), run=self.fake_run(self.output()))
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertEqual(self.ran, [DRILL1])
        moved = [p.name for p in self.root.iterdir() if p.name.startswith("ac4-drill1.out.")]
        self.assertEqual(len(moved), 1, "the earlier output is moved aside, never deleted")
        record = self.record()
        self.assertEqual((record["adopted"], record["driver_ran_here"]), (False, True))

    def test_a_refused_rerun_changes_nothing(self) -> None:
        # REFUSED prints "nothing was changed": the earlier output must still be under its own name.
        self.out.write_text("an earlier output")
        with self.assertRaises(finish.Refused):
            self.drill(self.args(rerun=True), task=lambda _home: ("active", "ActiveTask=..."))
        (self.dest / DRILL1).unlink()
        with self.assertRaises(finish.Refused):
            self.drill(self.args(rerun=True))
        self.assertEqual(self.out.read_text(), "an earlier output")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["ac4-drill1.out"])

    def test_the_driver_runs_when_nothing_was_run_before(self) -> None:
        code, text = self.drill(self.args(), run=self.fake_run(self.output()))
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertEqual(self.ran, [DRILL1])
        self.assertIn("running the driver now", text)
        self.assertIn("(exit 0)", text)
        self.assertIn("source      : the driver, run here", text)
        self.assertFalse(self.run_dir.exists())

    def test_the_driver_is_given_the_real_destination(self) -> None:
        seen: list[tuple[str, str]] = []

        def run(dlist, dest, run_root, out_path):
            seen.append((dest, run_root))
            Path(out_path).write_text(self.output(), encoding="utf-8")
            return 0

        link = Path(self.tmp.name) / "dest-link"
        link.symlink_to(self.dest)
        code, _text = self.drill(self.args(dest=str(link)), run=run)
        self.assertEqual(code, finish.EXIT_PASS, "the driver prints the real path, and that is what it is compared with")
        self.assertEqual(seen, [(os.path.realpath(self.dest), os.path.realpath(self.root))])

    def test_an_active_backup_refuses_the_drill(self) -> None:
        with self.assertRaises(finish.Refused) as caught:
            self.drill(self.args(), task=lambda _home: ("active", 'ActiveTask={"Item1": 46, "Item2": "2"}'))
        self.assertIn("a server task is active", str(caught.exception))
        self.assertFalse(self.out.exists())
        code, _text = self.drill(self.args(allow_active_task=True), run=self.fake_run(self.output()), task=lambda _home: ("active", "ActiveTask=..."))
        self.assertEqual(code, finish.EXIT_PASS)

    def test_an_unreadable_server_state_does_not_block_the_drill(self) -> None:
        # The driver's own check of the dlist list is the guard; the server question only saves a wasted run.
        code, text = self.drill(self.args(), run=self.fake_run(self.output()), task=lambda _home: ("unknown", "serverstate exited 1"))
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("serverstate exited 1 -- proceeding", text)

    def test_a_recorded_pass_is_not_drilled_again(self) -> None:
        finish.write_verdict(str(self.root), "ac4-drill1", {"verdict": "PASS", "dlist": DRILL1, "judged_at": "2026-11-12T02:00:00Z"})
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("nothing run", text)

    def test_a_dlist_that_is_not_in_the_destination_is_refused(self) -> None:
        (self.dest / DRILL1).unlink()
        with self.assertRaises(finish.Refused):
            self.drill(self.args())

    def test_a_run_root_that_others_can_reach_is_refused(self) -> None:
        self.out.write_text(self.output())
        os.chmod(self.root, 0o740)  # group-readable is already too much
        try:
            with self.assertRaises(finish.Refused) as caught:
                self.drill(self.args())
        finally:
            os.chmod(self.root, 0o700)
        self.assertIn("mode 0740", str(caught.exception))
        self.assertFalse((self.root / "ac4-drill1.verdict.json").exists())

    def test_a_pass_whose_run_directory_cannot_be_shredded_is_not_a_clean_pass(self) -> None:
        outside = Path(self.tmp.name) / "ac4-outside"
        outside.mkdir()
        (outside / "dlist.zip").write_bytes(b"decrypted")
        self.out.write_text(self.output(run_dir=str(outside)))
        code, text = self.drill(self.args())
        self.assertEqual(code, finish.EXIT_ERROR)
        self.assertIn("could NOT be removed", text)
        self.assertTrue((outside / "dlist.zip").exists(), "a path outside the run root is never touched")
        self.assertEqual(self.record()["run_dir"], "NOT shredded")

    def test_drill_two_is_the_first_post_recovery_fileset(self) -> None:
        self.assertEqual(finish.DRILLS, {"1": "duplicati-20260918T140000Z.dlist.zip.aes", "2": "duplicati-20261107T212908Z.dlist.zip.aes"})


class RunDriverTest(unittest.TestCase):
    """The one place the real driver is started: its output is teed to a 0600 file and its exit code returned."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def stand_in(self, body: str) -> Path:
        script = self.base / "stand_in_driver.py"
        script.write_text("import sys\n" + body, encoding="utf-8")
        return script

    @unittest.skipUnless(os.path.exists("/usr/bin/python3"), "run_driver starts /usr/bin/python3 by its full path")
    def test_stdout_and_stderr_are_teed_and_the_exit_code_is_returned(self) -> None:
        script = self.stand_in(f"print('ARGV ' + ' '.join(sys.argv[1:]))\nprint('credential  : /x/env key=PASSPHRASE (sha256[:16]={FINGERPRINT})')\nprint('RESULT: FAIL')\nprint('FATAL: on stderr', file=sys.stderr)\nsys.exit(1)\n")
        out_path = self.base / "ac4-drill1.out"
        shown = io.StringIO()
        with mock.patch.object(finish, "DRIVER", str(script)), redirect_stdout(shown):
            code = finish.run_driver(DRILL1, "/mnt/dest", "/root/run-root", str(out_path))
        self.assertEqual(code, 1)
        text = out_path.read_text(encoding="utf-8")
        self.assertIn(f"ARGV --dest /mnt/dest --dlist {DRILL1} --run-root /root/run-root", text)
        self.assertIn("RESULT: FAIL", text)
        self.assertIn("FATAL: on stderr", text, "stderr is where the driver writes FATAL, so it is teed too")
        self.assertEqual(shown.getvalue(), text, "the terminal and the file carry the same lines")
        self.assertEqual(os.stat(out_path).st_mode & 0o777, 0o600)
        self.assertNotIn(FINGERPRINT, text, "the passphrase's hash prefix reaches neither the file nor the terminal")
        self.assertIn(f"credential  : /x/env key=PASSPHRASE {finish.FINGERPRINT_WITHHELD}", text)

    @unittest.skipUnless(os.path.exists("/usr/bin/python3"), "run_driver starts /usr/bin/python3 by its full path")
    def test_an_existing_output_file_is_never_overwritten(self) -> None:
        out_path = self.base / "ac4-drill1.out"
        out_path.write_text("an earlier run")
        with mock.patch.object(finish, "DRIVER", str(self.stand_in("print('new')\n"))), self.assertRaises(FileExistsError):
            finish.run_driver(DRILL1, "/mnt/dest", "/root/run-root", str(out_path))
        self.assertEqual(out_path.read_text(), "an earlier run")

    @unittest.skipUnless(os.path.exists("/usr/bin/python3"), "run_driver starts /usr/bin/python3 by its full path")
    def test_the_lines_are_recorded_in_the_order_they_were_printed(self) -> None:
        # Into a pipe, a buffered stdout is flushed when the driver exits: its FATAL, written to stderr at once,
        # would be recorded ahead of the lines that led to it, and nothing would show on the terminal until the end.
        script = self.stand_in("print('run dir     : /x/ac4-first')\nprint('FATAL: the driver stopped here', file=sys.stderr)\nprint('printed after the stop')\n")
        out_path = self.base / "ac4-drill1.out"
        with mock.patch.object(finish, "DRIVER", str(script)), redirect_stdout(io.StringIO()):
            finish.run_driver(DRILL1, "/mnt/dest", "/root/run-root", str(out_path))
        self.assertEqual(out_path.read_text(encoding="utf-8").splitlines(), ["run dir     : /x/ac4-first", "FATAL: the driver stopped here", "printed after the stop"])


class PlanTest(unittest.TestCase):
    NOW = dt.datetime(2026, 11, 12, 1, 0, 0, tzinfo=UTC)
    OLD_SAMPLE_HOURS = (0, 2, 6, 12, 24, 36, 48, 60)  # what plan_first_pass evaluated until 2026-11-12
    # The review's counter-example: the nine pre-recovery filesets and seven plausible post-recovery ones.
    REVIEW_STAMPS = tuple(retention.EXISTING) + ("20261107T212908Z", "20261108T140000Z", "20261109T050500Z", "20261109T140000Z", "20261110T140000Z", "20261110T221500Z", "20261111T140000Z")
    REVIEW_NOW = dt.datetime(2026, 11, 22, 12, 0, 0, tzinfo=UTC)

    @staticmethod
    def union_at(names: list[str], instants: list[dt.datetime], policy_text: str = finish.POLICY) -> set[str]:
        """The names deleted at any of `instants`, computed straight from the port: the oracle for plan_first_pass."""
        policy = retention.parse_policy(policy_text)
        by_stamp = {retention.stamp(finish.stamp_of(name)): name for name in names}
        newest, found = max(by_stamp), set()
        for at in instants:
            run = max(at - dt.timedelta(seconds=1), newest + dt.timedelta(seconds=1))
            found |= {by_stamp[s] for s in retention.to_delete(list(by_stamp) + [run], max(at, run), policy) if s in by_stamp}
        return found

    def test_the_real_list_of_2026_11_11_loses_eight(self) -> None:
        plan = finish.plan_first_pass(DLISTS_2026_11_11, finish.POLICY, self.NOW, retention)
        post = ["duplicati-20261108T140001Z.dlist.zip.aes", "duplicati-20261109T140001Z.dlist.zip.aes", "duplicati-20261110T140000Z.dlist.zip.aes"]
        self.assertEqual(plan["delete"], sorted(FIVE_PRE_RECOVERY + post))
        self.assertEqual(plan["varies"], [], "no fileset meets a frame's edge in the next 60 hours")
        self.assertEqual([at for at, _names in plan["evaluated"]], [self.NOW, self.NOW + dt.timedelta(hours=60)], "so only the window's two ends are evaluated")
        self.assertEqual(len(plan["keep"]), 8)
        self.assertIn(finish.DRILLS["2"], plan["keep"], "drill 2's fileset survives the first pass")
        self.assertIn(finish.DRILLS["1"], plan["delete"], "drill 1's fileset does not -- which is why it is drilled first")

    def test_the_nine_alone_lose_the_five_the_recovery_plan_names(self) -> None:
        nine = DLISTS_2026_11_11[:9]
        plan = finish.plan_first_pass(nine, finish.POLICY, self.NOW, retention)
        self.assertEqual(plan["delete"], sorted(FIVE_PRE_RECOVERY))
        # ...and the port's own table agrees for the same date.
        kept = retention.outcome(dt.datetime(2026, 11, 12, 14, 30, tzinfo=UTC), retention.parse_policy(finish.POLICY), 2)
        self.assertEqual(len(kept), 4)
        self.assertEqual(sorted(kept), sorted(retention.short(retention.stamp(finish.stamp_of(name))) for name in plan["keep"]))

    def test_a_fileset_exactly_at_a_frames_lower_bound_is_inside_the_frame(self) -> None:
        # Rule 2. X is exactly 14 days before the pass and Y one hour after X. Inside the 2W frame X is kept and Y,
        # under a day later, is deleted. Were the bound exclusive, X would fall to the 6M frame and Y would survive.
        x = self.NOW - dt.timedelta(days=14)
        names = [dlist_name(x), dlist_name(x + dt.timedelta(hours=1))]
        plan = finish.plan_first_pass(names, "2W:1D,6M:1W", self.NOW, retention, horizon=dt.timedelta(0))
        self.assertEqual(plan["delete"], [names[1]])
        one_second_later = finish.plan_first_pass(names, "2W:1D,6M:1W", self.NOW + dt.timedelta(seconds=1), retention, horizon=dt.timedelta(0))
        self.assertEqual(one_second_later["delete"], [], "one second past the bound X leaves the frame and Y becomes its first member")

    def test_a_set_that_depends_on_the_pass_time_is_reported(self) -> None:
        # Until +4h X and Y are both inside the 2W frame, so Y (three hours after X) is deleted. From then on X has
        # aged out of it and Y has not, so Y is the frame's first member and is kept.
        x = self.NOW - dt.timedelta(days=13, hours=20)
        names = [dlist_name(x), dlist_name(x + dt.timedelta(hours=3))]
        plan = finish.plan_first_pass(names, "2W:1D,6M:1W", self.NOW, retention, horizon=dt.timedelta(hours=6))
        self.assertEqual(plan["varies"], [names[1]])
        self.assertEqual(plan["delete"], [names[1]], "the prediction is the union")
        self.assertEqual(plan["always"], [])
        edge = self.NOW + dt.timedelta(hours=4)
        self.assertEqual([at for at, _names in plan["evaluated"]], [self.NOW, edge, edge + dt.timedelta(seconds=1), self.NOW + dt.timedelta(hours=6)])
        self.assertEqual([names for _at, names in plan["evaluated"]], [[names[1]], [names[1]], [], []], "inside AT the edge, outside one second after it")

    def test_every_pass_time_is_covered_not_a_sample_of_them(self) -> None:
        # The 2026-11-12 review: 20261111T140000Z is deleted only between 2026-11-24T14:00Z and 22:15Z, which falls
        # between the old +48h and +60h sample points.
        names = [f"duplicati-{stamp}.dlist.zip.aes" for stamp in self.REVIEW_STAMPS]
        missed = "duplicati-20261111T140000Z.dlist.zip.aes"
        sampled = self.union_at(names, [self.REVIEW_NOW + dt.timedelta(hours=h) for h in self.OLD_SAMPLE_HOURS])
        self.assertNotIn(missed, sampled, "the fixture must be one the old sampling gets wrong, or this test proves nothing")
        plan = finish.plan_first_pass(names, finish.POLICY, self.REVIEW_NOW, retention)
        self.assertIn(missed, plan["delete"])
        self.assertIn(missed, plan["varies"])
        every_minute = self.union_at(names, [self.REVIEW_NOW + dt.timedelta(minutes=k) for k in range(finish.HORIZON_HOURS * 60 + 1)])
        self.assertEqual(set(plan["delete"]), every_minute, "the edges give exactly what a sweep of every minute of the window gives")

    def test_the_instants_are_each_edge_and_the_second_after_it_inside_the_window(self) -> None:
        policy = retention.parse_policy("2W:1D,6M:1W")
        day, second = dt.timedelta(days=1), dt.timedelta(seconds=1)
        horizon = dt.timedelta(hours=10)
        at_start, at_end, past_end, before = self.NOW - 14 * day, self.NOW + horizon - 14 * day, self.NOW + horizon + second - 14 * day, self.NOW - second - 14 * day
        self.assertEqual(finish.pass_instants([at_start], policy, self.NOW, horizon), [self.NOW, self.NOW + second, self.NOW + horizon], "an edge exactly at the window's start counts")
        self.assertEqual(finish.pass_instants([at_end], policy, self.NOW, horizon), [self.NOW, self.NOW + horizon], "an edge exactly at its end counts; the second after it lies outside")
        self.assertEqual(finish.pass_instants([past_end], policy, self.NOW, horizon), [self.NOW, self.NOW + horizon])
        self.assertEqual(finish.pass_instants([before], policy, self.NOW, horizon), [self.NOW, self.NOW + horizon], "one second before the window: only the second after the edge is in it, and it is the start")
        six_months = self.NOW + dt.timedelta(hours=5) - 180 * day
        self.assertIn(self.NOW + dt.timedelta(hours=5), finish.pass_instants([six_months], policy, self.NOW, horizon), "every frame of the policy has edges, not only the smallest")

    def test_a_policy_that_cannot_be_parsed_is_an_error(self) -> None:
        for policy in ("2W:1Q", "garbage", "2W", ""):
            with self.subTest(policy=policy):
                with self.assertRaises(finish.ToolError) as caught:
                    finish.plan_first_pass(DLISTS_2026_11_11, policy, self.NOW, retention)
                self.assertIn("cannot be parsed", str(caught.exception))

    def test_two_dlists_with_one_stamp_are_an_error(self) -> None:
        with self.assertRaises(finish.ToolError):
            finish.plan_first_pass(["duplicati-20260918T140000Z.dlist.zip.aes", "duplicati-20260918T140000Z.dlist.zip"], finish.POLICY, self.NOW, retention)

    def test_a_directory_without_a_dlist_is_an_error_not_an_empty_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "duplicati-b0123.dblock.zip.aes").write_bytes(b"x")
            (Path(tmp) / "notes.txt").write_text("x")
            with self.assertRaises(finish.ToolError) as caught:
                finish.list_dlists(tmp)
            self.assertIn("holds no dlist", str(caught.exception))
            with self.assertRaises(finish.ToolError):
                finish.list_dlists(os.path.join(tmp, "missing"))


class AsideTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.dropbox = base / "disk" / "Dropbox"
        self.dest = self.dropbox / "Backups" / "Yamaguchi"
        self.dest.mkdir(parents=True)
        self.aside = base / "disk" / "_retention_aside"
        self.root = base / "run-root"
        self.root.mkdir(mode=0o700)
        os.chmod(self.root, 0o700)
        self.home = base / "home"
        (self.home / ".dropbox").mkdir(parents=True)
        (self.home / ".dropbox" / "info.json").write_text(json.dumps({"personal": {"path": str(self.dropbox), "host": 1, "is_team": False}}))
        for i, name in enumerate(DLISTS_2026_11_11):
            (self.dest / name).write_bytes(hashlib.sha256(name.encode()).digest() * (40 + i))
            os.chmod(self.dest / name, 0o640 if i % 2 else 0o600)
            os.utime(self.dest / name, ns=(1_794_000_000_123_456_789 + i, 1_794_000_000_987_654_321 + i))
        self.uid = os.geteuid()
        # On a busy disk an fsync takes a third of a second and these tests make hundreds. They record the calls
        # and read copies back through the cache; test_a_copy_reaches_the_disk and the media-hash test use the real ones.
        self.synced: list[int] = []
        self.quick = (mock.patch.object(finish.os, "fsync", side_effect=self.synced.append), mock.patch.object(finish, "media_sha256", side_effect=cached_sha256))
        for patcher in self.quick:
            patcher.start()
            self.addCleanup(patcher.stop)

    def real_disk(self) -> None:
        for patcher in self.quick:
            patcher.stop()

    def args(self, **overrides) -> argparse.Namespace:
        values: dict = {"run_root": str(self.root), "dest": str(self.dest), "aside": str(self.aside), "policy": finish.POLICY, "allow_active_task": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def run_aside(self, task=None, **overrides) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer), mock.patch.object(finish, "source_home", return_value=str(self.home)), mock.patch.object(finish.dt, "datetime", wraps=dt.datetime) as clock:
            clock.now.return_value = dt.datetime(2026, 11, 12, 1, 0, 0, tzinfo=UTC)
            code = finish.cmd_aside(self.args(**overrides), task=task or (lambda _home: ("idle", "no active task; ProgramState=Running")), owner_uid=self.uid)
        return code, buffer.getvalue()

    def passed(self, **overrides) -> None:
        record = {"verdict": "PASS", "dlist": DRILL1, "judged_at": "2026-11-12T02:00:00Z"}
        record.update(overrides)
        finish.write_verdict(str(self.root), "ac4-drill1", record)

    @contextmanager
    def opened(self):
        fd = finish.open_aside_dir(str(self.aside), self.uid)
        try:
            yield fd
        finally:
            os.close(fd)

    def listed(self) -> dict[str, str]:
        listed: dict[str, str] = {}
        for line in (self.aside / finish.MANIFEST).read_text().splitlines():
            digest, name = line.split("  ")
            listed[name] = digest
        return listed

    def test_it_refuses_until_drill_one_has_passed(self) -> None:
        for label, setup in (("no record", lambda: None), ("a failed drill", lambda: self.passed(verdict="FAIL")), ("another fileset", lambda: self.passed(dlist=finish.DRILLS["2"]))):
            with self.subTest(case=label):
                setup()
                with self.assertRaises(finish.Refused) as caught:
                    self.run_aside()
                self.assertIn("drill 1 has no PASS verdict record", str(caught.exception))
                self.assertFalse(self.aside.exists(), "a refusal creates nothing")

    def test_it_copies_every_dlist_whatever_the_prediction_says_and_is_idempotent(self) -> None:
        self.passed()
        code, text = self.run_aside()
        self.assertEqual(code, finish.EXIT_PASS)
        copied = sorted(p.name for p in self.aside.iterdir() if p.name != finish.MANIFEST)
        self.assertEqual(copied, sorted(DLISTS_2026_11_11), "all sixteen, not the eight the prediction names")
        self.assertIn("predicted   : the first pass under 2W:1D,6M:1W,2Y:1M,5Y:2M deletes 8 of 16 dlists", text)
        self.assertEqual(os.stat(self.aside).st_mode & 0o777, 0o700)
        for name in copied:
            source, copy = os.stat(self.dest / name), os.stat(self.aside / name)
            self.assertEqual((self.aside / name).read_bytes(), (self.dest / name).read_bytes())
            # What `cp -p` keeps: timestamps to the nanosecond, mode, owner and group.
            self.assertEqual((copy.st_mtime_ns, copy.st_mode, copy.st_uid, copy.st_gid), (source.st_mtime_ns, source.st_mode, source.st_uid, source.st_gid))
        self.assertEqual(self.listed(), {name: hashlib.sha256((self.dest / name).read_bytes()).hexdigest() for name in DLISTS_2026_11_11})
        self.assertIn("16 new, 0 already current", text)
        code, text = self.run_aside()
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("0 new, 16 already current", text)

    def test_it_does_not_copy_while_a_backup_is_writing(self) -> None:
        # A backup writes its dlist last. Copied half-written, it would stop every later `aside` on a hash mismatch.
        self.passed()
        with self.assertRaises(finish.Refused) as caught:
            self.run_aside(task=lambda _home: ("active", 'ActiveTask={"Item1": 47, "Item2": "2"}'))
        self.assertIn("a server task is active: a dlist it is writing now", str(caught.exception))
        self.assertFalse(self.aside.exists(), "a refusal creates nothing")
        code, text = self.run_aside(task=lambda _home: ("active", "ActiveTask=..."), allow_active_task=True)
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("server      : ActiveTask=...", text)

    def test_an_unreadable_server_state_does_not_block_the_copy(self) -> None:
        self.passed()
        code, text = self.run_aside(task=lambda _home: ("unknown", "serverstate exited 1"))
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("server      : serverstate exited 1 -- proceeding", text)

    def test_a_prediction_that_cannot_be_made_does_not_stop_the_copy(self) -> None:
        # Two dlists with one stamp: the port cannot place them, and the copy needs no port.
        self.passed()
        twin = DRILL1.removesuffix(".aes")
        (self.dest / twin).write_bytes(b"an unencrypted dlist with the same stamp")
        code, text = self.run_aside()
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("predicted   : not available (two dlists carry the same stamp) -- the copy does not depend on it", text)
        self.assertEqual(set(self.listed()), set(DLISTS_2026_11_11) | {twin})

    def test_a_crashed_runs_half_copy_is_not_listed_as_a_dlist(self) -> None:
        self.aside.mkdir(mode=0o700)
        orphan = "duplicati-20260101T000000Z.dlist.zip.aes.partial"  # its source is gone, so no later run replaces it
        (self.aside / orphan).write_bytes(b"half a copy")
        with self.opened() as fd:
            self.assertEqual(finish.write_manifest(fd, finish.copy_aside(str(self.dest), fd, FIVE_PRE_RECOVERY[:1])), 1)
        self.assertEqual(set(self.listed()), {FIVE_PRE_RECOVERY[0]})
        self.assertTrue((self.aside / orphan).exists(), "it is left for the owner to see")

    def test_a_fileset_added_after_the_first_copy_is_taken_by_the_second(self) -> None:
        self.passed()
        self.run_aside()
        later = "duplicati-20261112T140000Z.dlist.zip.aes"
        (self.dest / later).write_bytes(b"the next backup's dlist")
        (self.dest / DLISTS_2026_11_11[3]).unlink()  # ...and a retention pass has deleted one the first copy holds
        code, text = self.run_aside()
        self.assertEqual(code, finish.EXIT_PASS)
        self.assertIn("1 new, 15 already current", text)
        self.assertEqual(set(self.listed()), set(DLISTS_2026_11_11) | {later}, "the manifest keeps the copy whose source is gone")

    def test_the_manifest_covers_every_dlist_in_the_directory(self) -> None:
        # A second `aside` (after a backup added a fileset) must not drop the first run's copies from the manifest.
        self.aside.mkdir(mode=0o700)
        earlier = "duplicati-20260101T000000Z.dlist.zip.aes"
        (self.aside / earlier).write_bytes(b"copied by an earlier run")
        (self.aside / "notes.txt").write_text("not a dlist")
        with self.opened() as fd:
            rows = finish.copy_aside(str(self.dest), fd, FIVE_PRE_RECOVERY[:2])
            self.assertEqual(finish.write_manifest(fd, rows), 3)
        listed = self.listed()
        self.assertEqual(set(listed), set(FIVE_PRE_RECOVERY[:2]) | {earlier})
        self.assertEqual(listed[earlier], hashlib.sha256(b"copied by an earlier run").hexdigest())
        self.assertEqual(os.stat(self.aside / finish.MANIFEST).st_mode & 0o777, 0o600)
        self.assertEqual(finish.read_manifest(str(self.aside)), sorted(listed))
        self.assertIsNone(finish.read_manifest(str(self.dest)))

    def test_an_existing_copy_with_other_content_is_never_overwritten(self) -> None:
        self.aside.mkdir(mode=0o700)
        name = FIVE_PRE_RECOVERY[0]
        (self.aside / name).write_bytes(b"something else")
        with self.opened() as fd, self.assertRaises(finish.ToolError) as caught:
            finish.copy_aside(str(self.dest), fd, [name])
        self.assertIn("not overwritten", str(caught.exception))
        self.assertEqual((self.aside / name).read_bytes(), b"something else")

    def test_a_failed_copy_leaves_no_partial_file(self) -> None:
        self.aside.mkdir(mode=0o700)
        with self.opened() as fd:
            with self.assertRaises(finish.ToolError):
                finish.copy_aside(str(self.dest), fd, ["duplicati-20990101T000000Z.dlist.zip.aes"])
            with mock.patch.object(finish, "media_sha256", return_value=("0" * 64, False)):
                with self.assertRaises(finish.ToolError) as caught:
                    finish.copy_aside(str(self.dest), fd, [FIVE_PRE_RECOVERY[0]])
            self.assertIn("does not match its source", str(caught.exception))
            with mock.patch.object(finish.os, "fchmod", side_effect=PermissionError(1, "Operation not permitted")):
                with self.assertRaises(finish.ToolError) as caught:
                    finish.copy_aside(str(self.dest), fd, [FIVE_PRE_RECOVERY[0]])
            self.assertIn("copying " + FIVE_PRE_RECOVERY[0] + " failed", str(caught.exception))
        self.assertEqual(list(self.aside.iterdir()), [])

    def test_a_leftover_partial_file_is_replaced_not_trusted(self) -> None:
        self.aside.mkdir(mode=0o700)
        name = FIVE_PRE_RECOVERY[0]
        (self.aside / (name + ".partial")).write_bytes(b"half a copy from an interrupted run")
        with self.opened() as fd:
            rows = finish.copy_aside(str(self.dest), fd, [name])
        self.assertEqual(rows[0]["state"], "copied")
        self.assertEqual((self.aside / name).read_bytes(), (self.dest / name).read_bytes())
        self.assertEqual(sorted(p.name for p in self.aside.iterdir()), [name])

    def test_a_source_that_is_a_symlink_is_not_copied(self) -> None:
        # Its directory is group-writable: a group member could swap a dlist for a link to any file root can read.
        self.aside.mkdir(mode=0o700)
        name = FIVE_PRE_RECOVERY[0]
        secret = Path(self.tmp.name) / "roots-own-file"
        secret.write_bytes(b"not a dlist")
        (self.dest / name).unlink()
        (self.dest / name).symlink_to(secret)
        with self.opened() as fd, self.assertRaises(finish.ToolError) as caught:
            finish.copy_aside(str(self.dest), fd, [name])
        self.assertIn("cannot be opened as a regular file", str(caught.exception))
        self.assertEqual(list(self.aside.iterdir()), [])

    def test_an_existing_copy_that_is_a_symlink_to_its_source_is_not_current(self) -> None:
        # Followed, it would hash equal to the source and read "current" -- and the "copy" would be the very file
        # the retention pass deletes.
        self.aside.mkdir(mode=0o700)
        name = FIVE_PRE_RECOVERY[0]
        (self.aside / name).symlink_to(self.dest / name)
        with self.opened() as fd, self.assertRaises(finish.ToolError) as caught:
            finish.copy_aside(str(self.dest), fd, [name])
        self.assertIn("cannot be opened as a regular file", str(caught.exception))
        self.assertTrue((self.aside / name).is_symlink(), "it is left for the owner to inspect")

    def test_a_directory_renamed_after_the_check_still_receives_the_copy(self) -> None:
        # The aside directory's parent is group-writable on the host, so its NAME can be given to a symlink after
        # any check. The copy goes through the descriptor, to the directory that was opened.
        decoy = Path(self.tmp.name) / "disk" / "decoy"
        decoy.mkdir()
        name = FIVE_PRE_RECOVERY[0]
        with self.opened() as fd:
            moved = self.aside.with_name("_moved_by_someone")
            self.aside.rename(moved)
            self.aside.symlink_to(decoy)
            rows = finish.copy_aside(str(self.dest), fd, [name])
            self.assertEqual(finish.write_manifest(fd, rows), 1)
        self.assertEqual(sorted(p.name for p in moved.iterdir()), sorted([name, finish.MANIFEST]))
        self.assertEqual(list(decoy.iterdir()), [], "nothing was written through the name")

    def test_the_aside_directory_must_lie_outside_dropbox_and_the_destination(self) -> None:
        roots = [os.path.realpath(self.dropbox)]
        for path in (self.dropbox / "_aside", self.dest / "_aside", self.dropbox):
            with self.subTest(path=str(path)):
                with self.assertRaises(finish.Refused) as caught:
                    finish.check_aside_location(str(path), roots, str(self.dest))
                self.assertIn("lies inside", str(caught.exception))
        self.assertEqual(finish.check_aside_location(str(self.aside), roots, str(self.dest)), os.path.realpath(self.aside))
        self.assertFalse(self.aside.exists(), "the location check creates nothing")
        self.assertEqual(finish.check_aside_location(str(self.dropbox) + "-sibling", roots, str(self.dest)), os.path.realpath(self.dropbox) + "-sibling", "a name that merely starts like the root is outside it")

    def test_the_aside_directory_must_be_ours_alone(self) -> None:
        disk = Path(self.tmp.name) / "disk"
        loose = disk / "_loose"
        loose.mkdir(mode=0o700)
        for mode in (0o740, 0o750, 0o701, 0o500):  # not exactly 0700, whatever the umask made of mkdir's mode
            with self.subTest(mode=oct(mode)):
                os.chmod(loose, mode)
                with self.assertRaises(finish.Refused) as caught:
                    finish.open_aside_dir(str(loose), self.uid)
                self.assertIn("mode 0700", str(caught.exception))
        os.chmod(loose, 0o700)
        link = disk / "_link"
        link.symlink_to(loose)
        with self.assertRaises(finish.Refused) as caught:
            finish.open_aside_dir(str(link), self.uid)
        self.assertIn("a symlink is refused", str(caught.exception))
        with self.assertRaises(finish.Refused) as caught:
            finish.open_aside_dir(str(loose), self.uid + 1)
        self.assertIn(f"owned by uid {self.uid + 1}", str(caught.exception))
        with self.assertRaises(finish.Refused):
            finish.open_aside_dir(str(disk / "no-such-parent" / "_aside"), self.uid)
        a_file = disk / "_file"
        a_file.write_text("x")
        with self.assertRaises(finish.Refused):
            finish.open_aside_dir(str(a_file), self.uid)

    def test_a_directory_this_run_created_and_then_finds_foreign_is_an_error_not_a_refusal(self) -> None:
        # REFUSED says nothing was changed. Here a directory was made, so the word would be untrue.
        with self.assertRaises(finish.ToolError) as caught:
            finish.open_aside_dir(str(self.aside), self.uid + 1)
        self.assertIn("this run created it", str(caught.exception))

    def test_too_little_room_refuses_before_anything_is_made(self) -> None:
        self.passed()
        with mock.patch.object(finish, "free_bytes", return_value=sum(os.path.getsize(self.dest / name) for name in DLISTS_2026_11_11) * 2 - 1):
            with self.assertRaises(finish.Refused) as caught:
                self.run_aside()
        self.assertIn("wants twice that", str(caught.exception))
        self.assertFalse(self.aside.exists())
        with mock.patch.object(finish, "free_bytes", return_value=sum(os.path.getsize(self.dest / name) for name in DLISTS_2026_11_11) * 2):
            self.assertEqual(self.run_aside()[0], finish.EXIT_PASS, "exactly twice the need is enough")

    def test_free_space_is_read_from_the_nearest_directory_that_exists(self) -> None:
        asked: list[str] = []

        def statvfs(path):
            asked.append(path)
            return argparse.Namespace(f_bavail=10, f_frsize=4096)

        with mock.patch.object(finish.os, "statvfs", side_effect=statvfs):
            self.assertEqual(finish.free_bytes(str(self.aside / "not" / "there" / "yet")), 40960)
            self.assertEqual(finish.free_bytes("a-relative-name-that-does-not-exist"), 40960, "a relative name ends at a directory too, not in a loop")
        self.assertEqual(asked, [str(self.aside.parent), os.getcwd()])

    def test_a_run_root_that_others_can_reach_is_refused(self) -> None:
        self.passed()
        os.chmod(self.root, 0o704)  # readable by others: a planted PASS record could not be told from root's
        try:
            with self.assertRaises(finish.Refused) as caught:
                self.run_aside()
        finally:
            os.chmod(self.root, 0o700)
        self.assertIn("mode 0704", str(caught.exception))
        self.assertFalse(self.aside.exists())

    def test_an_unreadable_dropbox_root_refuses(self) -> None:
        # Rule 4: "outside the Dropbox root" cannot be shown, so the copy does not happen.
        (self.home / ".dropbox" / "info.json").write_text("not json")
        with self.assertRaises(finish.Refused):
            finish.dropbox_roots(str(self.home))
        (self.home / ".dropbox" / "info.json").write_text("{}")
        with self.assertRaises(finish.Refused):
            finish.dropbox_roots(str(self.home))
        (self.home / ".dropbox" / "info.json").unlink()
        with self.assertRaises(finish.Refused):
            finish.dropbox_roots(str(self.home))

    def test_a_copy_reaches_the_disk(self) -> None:
        # The copy is synced before its hash is compared, the directory after the rename, the manifest and the
        # directory again: four calls for one new file, two of them on the directory this test holds open.
        self.aside.mkdir(mode=0o700)
        with self.opened() as fd:
            rows = finish.copy_aside(str(self.dest), fd, [FIVE_PRE_RECOVERY[0]])
            self.assertEqual(self.synced.count(fd), 1)
            self.assertEqual(len(self.synced), 2)
            finish.write_manifest(fd, rows)
            self.assertEqual(self.synced.count(fd), 2)
            self.assertEqual(len(self.synced), 4)
        # ...and once for real, with the read-back from the media.
        self.real_disk()
        with self.opened() as fd:
            rows = finish.copy_aside(str(self.dest), fd, FIVE_PRE_RECOVERY[1:3])
        self.assertEqual([row["state"] for row in rows], ["copied", "copied"])
        for row in rows:
            self.assertIsInstance(row["direct"], bool)
            self.assertEqual(row["sha256"], hashlib.sha256((self.aside / row["name"]).read_bytes()).hexdigest())

    def test_the_media_hash_equals_the_plain_hash(self) -> None:
        self.real_disk()
        path = self.dest / DLISTS_2026_11_11[0]
        digest, direct = finish.media_sha256(str(path))
        self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIsInstance(direct, bool)
        big = Path(self.tmp.name) / "big.bin"
        big.write_bytes(os.urandom(finish.CHUNK + 4097))  # more than one chunk, and not block-aligned at the end
        self.assertEqual(finish.media_sha256(str(big))[0], hashlib.sha256(big.read_bytes()).hexdigest())
        self.assertEqual(finish.file_sha256(str(big)), hashlib.sha256(big.read_bytes()).hexdigest())
        empty = Path(self.tmp.name) / "empty.bin"
        empty.write_bytes(b"")
        self.assertEqual(finish.media_sha256(str(empty))[0], hashlib.sha256(b"").hexdigest())
        link = Path(self.tmp.name) / "link.bin"
        link.symlink_to(big)
        with self.assertRaises(OSError):
            finish.media_sha256(str(link))

    def test_a_fifo_at_a_dlists_name_does_not_hang_the_copy(self) -> None:
        fifo = Path(self.tmp.name) / "fifo"
        os.mkfifo(fifo)
        with self.assertRaises(finish.ToolError) as caught:
            finish.open_regular(str(fifo))
        self.assertIn("is not a regular file", str(caught.exception))


class Ac6bTest(unittest.TestCase):
    PATH = "/srv/fixture-home/.local/state/duplicati-server-db/Duplicati-server.sqlite"
    FILESET = dt.datetime(2026, 11, 11, 14, 0, 1, tzinfo=UTC)
    COMPLETE = dt.datetime(2026, 11, 11, 18, 5, 0, tzinfo=UTC)
    WRITTEN = dt.datetime(2026, 11, 11, 13, 45, 27, 400000, tzinfo=UTC)  # the lane's write, with its sub-second part
    DIGEST = "q1w2e3r4t5y6u7i8o9p0aAsSdDfFgGhHjJkKlLzZxXc="

    def entry(self, **overrides) -> dict:
        entry = {"type": "File", "path": self.PATH, "size": 610304, "hash": self.DIGEST, "time": "20261111T134527Z"}
        entry.update(overrides)
        return entry

    def live(self, mtime: dt.datetime, size: int = 610304, digest: str | None = None) -> dict:
        return {"size": size, "mtime": mtime, "sha256_b64": digest or self.DIGEST}

    def test_the_generation_the_backup_read_is_compared_by_content(self) -> None:
        verdict, reasons, facts = finish.judge_ac6b(self.entry(), 2_000_000, self.FILESET, self.live(self.WRITTEN), self.COMPLETE)
        self.assertEqual((verdict, reasons, facts["compared"]), ("PASS", [], "content"))
        for label, live in (("another hash", self.live(self.WRITTEN, digest="other")), ("another size", self.live(self.WRITTEN, size=602112))):
            with self.subTest(case=label):
                self.assertEqual(finish.judge_ac6b(self.entry(), 2_000_000, self.FILESET, live, self.COMPLETE)[0], "FAIL")

    def test_a_live_file_written_exactly_at_the_filesets_start_is_still_compared_by_content(self) -> None:
        # Rule 2: `<=`. A snapshot written in the same second the backup began is the one the backup read.
        _verdict, _reasons, facts = finish.judge_ac6b(self.entry(), 10, self.FILESET, self.live(self.FILESET))
        self.assertEqual(facts["compared"], "content")
        _verdict, _reasons, facts = finish.judge_ac6b(self.entry(), 10, self.FILESET, self.live(self.FILESET + dt.timedelta(seconds=1)))
        self.assertEqual(facts["compared"], "time")

    def test_a_snapshot_written_while_the_backup_ran_is_the_same_generation_by_its_time(self) -> None:
        # The backup began 14:00:01 and read the file after the lane rewrote it at 14:30:00. The entry's time is the
        # live file's mtime, so the two are one generation and are compared by content. Until 2026-11-12 this was
        # FAIL: "dated after the fileset's own start", as if a backup read every file in its first second.
        rewritten = dt.datetime(2026, 11, 11, 14, 30, 0, 250000, tzinfo=UTC)
        verdict, reasons, facts = finish.judge_ac6b(self.entry(time="20261111T143000Z"), 10, self.FILESET, self.live(rewritten), self.COMPLETE)
        self.assertEqual((verdict, reasons, facts["compared"]), ("PASS", [], "content"))
        verdict, reasons, _facts = finish.judge_ac6b(self.entry(time="20261111T143000Z"), 10, self.FILESET, self.live(rewritten, digest="other"), self.COMPLETE)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("same generation", reasons[0])
        _verdict, _reasons, facts = finish.judge_ac6b(self.entry(time="20261111T142959Z"), 10, self.FILESET, self.live(rewritten), self.COMPLETE)
        self.assertEqual(facts["compared"], "time", "one second apart is another generation")

    def test_a_replaced_live_file_is_judged_by_the_entrys_time(self) -> None:
        newer = self.live(dt.datetime(2026, 11, 12, 13, 45, 30, tzinfo=UTC), size=614400, digest="newer")
        self.assertEqual(finish.judge_ac6b(self.entry(), 10, self.FILESET, newer, self.COMPLETE)[0], "PASS")
        verdict, reasons, _facts = finish.judge_ac6b(self.entry(time="20261009T134500Z"), 10, self.FILESET, newer, self.COMPLETE)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("stale pre-recovery snapshot", reasons[0])
        self.assertEqual(finish.judge_ac6b(self.entry(time=None), 10, self.FILESET, newer, self.COMPLETE)[0], "ERROR")
        self.assertEqual(finish.judge_ac6b(self.entry(time="yesterday"), 10, self.FILESET, newer, self.COMPLETE)[0], "ERROR")

    def test_an_entry_cannot_be_dated_after_the_fileset_was_complete(self) -> None:
        newer = self.live(dt.datetime(2026, 11, 12, 13, 45, 30, tzinfo=UTC))
        at = self.COMPLETE.strftime("%Y%m%dT%H%M%SZ")
        after = (self.COMPLETE + dt.timedelta(seconds=1)).strftime("%Y%m%dT%H%M%SZ")
        self.assertEqual(finish.judge_ac6b(self.entry(time=at), 10, self.FILESET, newer, self.COMPLETE)[0], "PASS", "exactly at the end is inside")
        verdict, reasons, _facts = finish.judge_ac6b(self.entry(time=after), 10, self.FILESET, newer, self.COMPLETE)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("after the fileset was complete", reasons[0])
        self.assertEqual(finish.judge_ac6b(self.entry(time=after), 10, self.FILESET, newer)[0], "PASS", "with no end known, nothing is claimed about it")

    def test_an_entry_dated_exactly_at_the_re_enable_counts(self) -> None:
        newer = self.live(dt.datetime(2026, 11, 12, 13, 45, 30, tzinfo=UTC))
        at = finish.SNAPSHOT_ENABLED.strftime("%Y%m%dT%H%M%SZ")
        before = (finish.SNAPSHOT_ENABLED - dt.timedelta(seconds=1)).strftime("%Y%m%dT%H%M%SZ")
        self.assertEqual(finish.judge_ac6b(self.entry(time=at), 10, self.FILESET, newer)[0], "PASS")
        self.assertEqual(finish.judge_ac6b(self.entry(time=before), 10, self.FILESET, newer)[0], "FAIL")

    def test_the_stale_pre_recovery_snapshot_does_not_pass_by_matching_itself(self) -> None:
        # The lane never ran after it was re-enabled: the live file is September's, and the newest fileset holds
        # the same bytes. Content alone says PASS; the generation's date says this is not AC-6's snapshot.
        september = dt.datetime(2026, 9, 17, 13, 50, 0, tzinfo=UTC)
        verdict, reasons, facts = finish.judge_ac6b(self.entry(time="20260917T135000Z"), 2_000_000, self.FILESET, self.live(september), self.COMPLETE)
        self.assertEqual((verdict, facts["compared"]), ("FAIL", "content"))
        self.assertEqual(len(reasons), 1, "one cause, one reason")
        self.assertIn("stale pre-recovery snapshot", reasons[0])
        # ...and when the entry carries no readable time, the live file's own date still says so.
        verdict, reasons, _facts = finish.judge_ac6b(self.entry(time=None), 2_000_000, self.FILESET, self.live(september), self.COMPLETE)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("the lane has not run since", reasons[0])
        at_enable = self.live(finish.SNAPSHOT_ENABLED)
        self.assertEqual(finish.judge_ac6b(self.entry(time=None), 10, self.FILESET, at_enable, self.COMPLETE)[0], "PASS", "a live file written exactly at the re-enable is the lane's")
        just_before = self.live(finish.SNAPSHOT_ENABLED - dt.timedelta(microseconds=1))
        self.assertEqual(finish.judge_ac6b(self.entry(time=None), 10, self.FILESET, just_before, self.COMPLETE)[0], "FAIL")

    def test_absence_emptiness_and_stubs(self) -> None:
        live = self.live(self.WRITTEN)
        self.assertEqual(finish.judge_ac6b(None, 2_000_000, self.FILESET, live)[0], "FAIL")
        verdict, reasons, _facts = finish.judge_ac6b(None, 0, self.FILESET, live)
        self.assertEqual(verdict, "ERROR")
        self.assertIn("no entries", reasons[0])
        self.assertEqual(finish.judge_ac6b(self.entry(size=4096), 10, self.FILESET, self.live(live["mtime"], size=4096))[0], "FAIL")
        self.assertEqual(finish.judge_ac6b(self.entry(size=4097), 10, self.FILESET, self.live(live["mtime"], size=4097))[0], "PASS")
        self.assertEqual(finish.judge_ac6b(self.entry(), 10, self.FILESET, None)[0], "ERROR")

    def test_find_entry_wants_a_file_at_exactly_that_path(self) -> None:
        entries = [{"type": "Folder", "path": self.PATH}, {"type": "File", "path": self.PATH + ".bak", "size": 1}, self.entry(), {"type": "File", "path": "/other", "size": 2}]
        found, total = finish.find_entry(iter(entries), self.PATH)
        self.assertEqual((found, total), (self.entry(), 4))
        self.assertEqual(finish.find_entry(iter(entries[:2]), self.PATH), (None, 2))
        self.assertEqual(finish.find_entry(iter([]), self.PATH), (None, 0))


class StubDriver:
    """Stands in for the AC-4 driver's three functions `ac6` uses. No cipher: the stub writes the zip itself."""

    def __init__(self, entries=None, *, decrypt=None) -> None:
        self.entries, self.decrypt = entries, decrypt

    def load_passphrase(self, path, key):
        with open(path, encoding="utf-8"):  # a missing file raises here, as the driver's own bare open() does
            pass
        print(f"credential  : {path} key={key} (sha256[:16]={FINGERPRINT})")
        return "fixture-archive-marker"

    def aescrypt_decrypt(self, src, dst, password):
        if self.decrypt is not None:
            self.decrypt(dst)
            return
        with zipfile.ZipFile(dst, "w") as zf:
            zf.writestr("manifest", "{}")
            zf.writestr("filelist.json", json.dumps(self.entries))

    @staticmethod
    def iter_json_array(stream):
        yield from json.load(stream)


class Ac6VerbTest(unittest.TestCase):
    """`ac6` end to end with a stand-in driver: what it prints, what it leaves on disk, and how it fails."""

    DLIST = DLISTS_2026_11_11[-1]  # started 2026-11-11T14:00:01Z

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root, self.dest, self.home = base / "run-root", base / "dest", base / "home"
        self.root.mkdir(mode=0o700)
        os.chmod(self.root, 0o700)
        self.dest.mkdir()
        for name in DLISTS_2026_11_11:
            (self.dest / name).write_bytes(b"encrypted")
        complete = dt.datetime(2026, 11, 11, 18, 5, 0, tzinfo=UTC).timestamp()
        os.utime(self.dest / self.DLIST, (complete, complete))
        self.snapshot = self.home / finish.SNAPSHOT_REL
        self.snapshot.parent.mkdir(parents=True)
        self.content = os.urandom(8192)
        self.snapshot.write_bytes(self.content)
        written = dt.datetime(2026, 11, 11, 13, 45, 27, tzinfo=UTC).timestamp()
        os.utime(self.snapshot, (written, written))
        self.cred = base / "env"
        self.cred.write_text("# the stand-in driver only opens this file; it holds no assignment\n")
        self.quick = mock.patch.object(finish, "shred_tree", side_effect=quick_shred)
        self.quick.start()
        self.addCleanup(self.quick.stop)

    def entry(self, **overrides) -> dict:
        entry = {"type": "File", "path": str(self.snapshot), "size": len(self.content), "hash": base64.b64encode(hashlib.sha256(self.content).digest()).decode(), "time": "20261111T134527Z"}
        entry.update(overrides)
        return entry

    def ac6(self, driver: StubDriver, **overrides) -> tuple[int, str]:
        values: dict = {"run_root": str(self.root), "dest": str(self.dest), "dlist": None, "cred_file": str(self.cred)}
        values.update(overrides)
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(io.StringIO()), mock.patch.object(finish, "source_home", return_value=str(self.home)), mock.patch.object(finish, "load_module", return_value=driver):
            code = finish.cmd_ac6(argparse.Namespace(**values), owner_uid=os.geteuid())
        return code, buffer.getvalue()

    def left_on_disk(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir())

    def record(self) -> dict:
        return json.loads((self.root / "ac6b.verdict.json").read_text())

    def test_the_snapshot_in_the_newest_fileset_passes(self) -> None:
        self.quick.stop()  # this one test of the verb runs the real shred
        code, text = self.ac6(StubDriver([{"type": "Folder", "path": str(self.home)}, self.entry()]))
        self.assertEqual(code, finish.EXIT_PASS, text)
        self.assertIn(f"== AC-6b: the server-DB snapshot in {self.DLIST}", text)
        self.assertIn("fileset     : 2 entries; started 2026-11-11T14:00:01Z, complete 2026-11-11T18:05:00Z", text)
        self.assertIn("compared by content", text)
        self.assertIn("VERDICT: PASS", text)
        self.assertNotIn(FINGERPRINT, text, "the loader's line, with the passphrase's hash prefix, is not printed")
        self.assertNotIn("credential  :", text)
        self.assertEqual(self.left_on_disk(), ["ac6b.verdict.json"], "the run directory held a decrypted dlist and is gone")
        record = self.record()
        self.assertEqual((record["verdict"], record["dlist"], record["schema"]), ("PASS", self.DLIST, "phase-d-ac6b/2"))

    def test_a_fileset_without_the_snapshot_fails(self) -> None:
        code, text = self.ac6(StubDriver([{"type": "File", "path": "/other", "size": 1}]))
        self.assertEqual(code, finish.EXIT_FAIL)
        self.assertIn("not among the fileset's 1 entries", text)
        self.assertEqual(self.left_on_disk(), ["ac6b.verdict.json"])

    def test_an_empty_file_list_is_an_error(self) -> None:
        code, text = self.ac6(StubDriver([]))
        self.assertEqual(code, finish.EXIT_ERROR)
        self.assertIn("no entries", text)

    def test_what_can_go_wrong_with_a_dlist_ends_in_a_verdict_not_a_traceback(self) -> None:
        def garbage(dst):
            Path(dst).write_bytes(b"this is not a zip archive")

        def no_file_list(dst):
            with zipfile.ZipFile(dst, "w") as zf:
                zf.writestr("manifest", "{}")

        def truncated(_dst):
            raise IndexError("index out of range")  # the driver's f.read(1)[0] on a truncated AES Crypt v2 file

        def driver_fatal(_dst):
            raise SystemExit(2)  # the driver's fail(): header HMAC mismatch, and the like

        cases: tuple[tuple[str, StubDriver, dict], ...] = (
            ("BadZipFile", StubDriver(decrypt=garbage), {}),
            ("KeyError", StubDriver(decrypt=no_file_list), {}),
            ("IndexError", StubDriver(decrypt=truncated), {}),
            ("stopped (exit 2)", StubDriver(decrypt=driver_fatal), {}),
            ("FileNotFoundError", StubDriver([self.entry()]), {"cred_file": str(self.cred) + ".missing"}),
        )
        for needle, driver, overrides in cases:
            with self.subTest(case=needle):
                code, text = self.ac6(driver, **overrides)
                self.assertEqual(code, finish.EXIT_ERROR)
                self.assertIn(needle, text)
                self.assertIn("VERDICT: ERROR", text)
                self.assertEqual(self.left_on_disk(), ["ac6b.verdict.json"], "whatever happened, no run directory is left")
                self.assertEqual(self.record()["verdict"], "ERROR")

    def test_a_named_dlist_is_judged_and_one_that_is_not_there_is_refused(self) -> None:
        earlier = DLISTS_2026_11_11[-2]  # began 2026-11-10T14:00:00Z
        complete = dt.datetime(2026, 11, 10, 14, 50, 0, tzinfo=UTC).timestamp()
        os.utime(self.dest / earlier, (complete, complete))
        code, text = self.ac6(StubDriver([self.entry()]), dlist=earlier)
        self.assertIn(f"snapshot in {earlier}", text)
        self.assertEqual(code, finish.EXIT_FAIL, "the entry is dated a day after that fileset was complete, so it cannot be in it")
        self.assertIn("after the fileset was complete (2026-11-10T14:50:00Z)", text)
        (self.root / "ac6b.verdict.json").unlink()
        with self.assertRaises(finish.Refused):
            self.ac6(StubDriver([self.entry()]), dlist="duplicati-20990101T000000Z.dlist.zip.aes")
        self.assertEqual(self.left_on_disk(), [], "a refusal makes no run directory and no record")

    def test_a_run_root_that_others_can_reach_is_refused(self) -> None:
        os.chmod(self.root, 0o740)
        try:
            with self.assertRaises(finish.Refused):
                self.ac6(StubDriver([self.entry()]))
        finally:
            os.chmod(self.root, 0o700)
        self.assertEqual(self.left_on_disk(), [])

    def test_a_run_directory_that_cannot_be_shredded_is_said_so(self) -> None:
        with mock.patch.object(finish, "shred_tree", return_value=(0, ["/somewhere/dlist.zip"])):
            code, text = self.ac6(StubDriver([self.entry()]))
        self.assertEqual(code, finish.EXIT_ERROR, "a PASS that leaves a decrypted dlist behind is not reported as a clean PASS")
        self.assertIn("could NOT be removed", text)
        self.assertIn("a decrypted dlist may still be on disk", text)


class ServerTaskTest(unittest.TestCase):
    """Rule 1 again: the reader is fed what ``yamaguchi_server_api.py serverstate`` really prints."""

    def real_output(self, state: dict) -> tuple[int, str]:
        api = load_ad_hoc("yamaguchi_server_api")
        buffer = io.StringIO()
        with mock.patch.object(api, "req", return_value=(200, state)), redirect_stdout(buffer), redirect_stderr(io.StringIO()):
            code = api._serverstate("fixture-bearer-marker")
        return code, buffer.getvalue()

    def test_an_idle_running_and_a_paused_server(self) -> None:
        for program, expected_code in (("Running", 0), ("Paused", 2)):
            with self.subTest(program=program):
                code, text = self.real_output({"ProgramState": program, "ActiveTask": None, "SchedulerQueueIds": [], "EstimatedPauseEnd": "0001-01-01T00:00:00Z", "ProposedSchedule": []})
                self.assertEqual(code, expected_code)
                state, detail = finish.read_server_task(code, text)
                self.assertEqual(state, "idle")
                self.assertIn(program, detail)

    def test_an_active_task(self) -> None:
        code, text = self.real_output({"ProgramState": "Running", "ActiveTask": {"Item1": 46, "Item2": "2"}, "SchedulerQueueIds": []})
        state, detail = finish.read_server_task(code, text)
        self.assertEqual(state, "active")
        self.assertIn("46", detail)

    def test_everything_else_is_unknown_never_idle(self) -> None:
        for code, text in ((1, ""), (0, ""), (0, "not json"), (0, "[]"), (0, json.dumps({"ProgramState": "Running"})), (64, "{}"), (1, json.dumps({"ProgramState": "Running", "ActiveTask": None}))):
            with self.subTest(code=code, text=text[:12]):
                self.assertEqual(finish.read_server_task(code, text)[0], "unknown")


class SourceUserHopTest(unittest.TestCase):
    """Root asks the server and runs the probe AS the Source's user: no privilege raised, nothing of root's inherited."""

    HOME = "/srv/fixture-home"

    def test_the_argv_drops_privilege_and_empties_the_environment(self) -> None:
        argv = finish.as_source_user(self.HOME, finish.API_CLIENT, "serverstate")
        self.assertEqual(argv[1:6], ["-u", finish.SOURCE_USER, "--", "/usr/bin/env", "-i"])
        self.assertIn(f"HOME={self.HOME}", argv)
        self.assertIn("PATH=/usr/bin:/bin", argv)
        self.assertEqual(argv[-4:], ["/usr/bin/python3", "-I", finish.API_CLIENT, "serverstate"])
        self.assertEqual([word for word in argv if word in ("sudo", "pkexec", "su")], [])

    def test_the_server_question_runs_from_the_root_directory(self) -> None:
        idle = argparse.Namespace(returncode=0, stdout=json.dumps({"ProgramState": "Running", "ActiveTask": None}))
        with mock.patch.object(finish.subprocess, "run", return_value=idle) as run:
            self.assertEqual(finish.server_task(self.HOME)[0], "idle")
        self.assertEqual(run.call_args.args[0], finish.as_source_user(self.HOME, finish.API_CLIENT, "serverstate"))
        self.assertEqual(run.call_args.kwargs["cwd"], "/", "root's own working directory may be one the Source's user cannot enter")
        with mock.patch.object(finish.subprocess, "run", side_effect=OSError("no runuser")):
            self.assertEqual(finish.server_task(self.HOME)[0], "unknown")

    def status(self, root: Path, aside: Path, dest: Path) -> tuple[int, str, mock.Mock]:
        args = argparse.Namespace(run_root=str(root), aside=str(aside), dest=str(dest), backup_id="2", expect_retention="restored")
        out = io.StringIO()
        with mock.patch.object(finish, "source_home", return_value=self.HOME), mock.patch.object(finish.subprocess, "run", return_value=argparse.Namespace(returncode=1)) as run, redirect_stdout(out):
            code = finish.cmd_status(args, owner_uid=os.geteuid())
        return code, out.getvalue(), run

    def test_status_lists_the_records_and_runs_the_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, aside, dest = Path(tmp) / "run-root", Path(tmp) / "aside", Path(tmp) / "dest"
            root.mkdir(mode=0o700)
            os.chmod(root, 0o700)
            (root / "ac4-20260918T140000-20261109-050909").mkdir()
            aside.mkdir()
            dest.mkdir()
            for name in FIVE_PRE_RECOVERY[:3]:
                (dest / name).write_bytes(b"x")
            finish.write_verdict(str(root), "ac4-drill1", {"verdict": "PASS", "dlist": DRILL1, "judged_at": "2026-11-12T02:00:00Z"})
            (aside / FIVE_PRE_RECOVERY[0]).write_bytes(b"x")
            (aside / finish.MANIFEST).write_text(f"{'0' * 64}  {FIVE_PRE_RECOVERY[0]}\n{'1' * 64}  {FIVE_PRE_RECOVERY[1]}\n")
            code, text, run = self.status(root, aside, dest)
            self.assertEqual(code, finish.EXIT_PASS)
            self.assertIn(f"ac4-drill1  : PASS for {DRILL1}", text)
            self.assertIn("ac4-drill2  : no verdict record", text)
            self.assertIn("run dirs    : 1 on disk", text)
            self.assertIn("lists 2 dlist(s); 1 missing from the directory; 1 dlist(s) now in the destination are not in it -- run `aside` again", text)
            self.assertIn("probe exit  : 1", text)
            self.assertEqual(run.call_args.args[0][-6:], ["-I", finish.PROBE, "--backup-id", "2", "--expect-retention", "restored"])
            self.assertEqual(run.call_args.kwargs["cwd"], "/")
            # Once the manifest covers the destination, the line says so and asks for nothing.
            (aside / finish.MANIFEST).write_text("".join(f"{'0' * 64}  {name}\n" for name in FIVE_PRE_RECOVERY[:3]))
            _code, text, _run = self.status(root, aside, dest)
            self.assertIn("0 dlist(s) now in the destination are not in it\n", text)
            (aside / finish.MANIFEST).unlink()
            _code, text, _run = self.status(root, aside, dest)
            self.assertIn("aside       : no manifest at", text)
            os.chmod(root, 0o744)
            with self.assertRaises(finish.Refused):
                self.status(root, aside, dest)
            os.chmod(root, 0o700)


class CommandLineTest(unittest.TestCase):
    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = finish.main(list(argv))
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, out.getvalue(), err.getvalue()

    @unittest.skipIf(os.geteuid() == 0, "the refusal under test is the one a non-root caller gets")
    def test_every_verb_but_plan_refuses_a_non_root_caller(self) -> None:
        for argv in (("drill", "1"), ("aside",), ("ac6",), ("status", "--backup-id", "2"), ("shred", "--run-dir", "/nonexistent/ac4-x")):
            with self.subTest(verb=argv[0]):
                code, out, err = self.run_main(*argv)
                self.assertEqual(code, finish.EXIT_REFUSED)
                self.assertIn("runs as root", err)
                self.assertIn("VERDICT: REFUSED (nothing was changed)", out)

    def test_usage_errors_exit_64(self) -> None:
        for argv in ((), ("drill", "3"), ("status",), ("status", "--backup-id", "two"), ("status", "--backup-id", "0"), ("nonsense",), ("plan", "--at", "tomorrow"), ("plan", "--at", "2026-11-12")):
            with self.subTest(argv=argv):
                self.assertEqual(self.run_main(*argv)[0], finish.EXIT_USAGE)

    def test_an_abbreviated_option_is_a_usage_error(self) -> None:
        # The wrapper reads --run-root by its full name to set TMPDIR. Were `--run /x` accepted here, TMPDIR and the
        # wrapper's check would name the default run root while the tool used /x.
        with tempfile.TemporaryDirectory() as tmp:
            for argv in (("--run", tmp, "plan"), ("--des", tmp, "plan"), ("drill", "1", "--re"), ("plan", "--a", "2026-11-12T01:00:00Z")):
                with self.subTest(argv=argv[:1] + argv[2:]):
                    self.assertEqual(self.run_main(*argv)[0], finish.EXIT_USAGE)

    def test_plan_reads_a_destination_as_any_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in DLISTS_2026_11_11:
                (Path(tmp) / name).write_bytes(b"x" * 10)
            # --at pins the pass time: the answer for these sixteen names depends on the date, as it must.
            code, out, _err = self.run_main("--dest", tmp, "plan", "--at", "2026-11-12T01:00:00Z")
            self.assertEqual(code, finish.EXIT_PASS)
            self.assertEqual(out.count("  DELETE  "), 8)
            self.assertIn("predicted   : 8 of 16 deleted (5 pre-recovery, 3 post-recovery), 80 B", out)
            self.assertIn("assumes     : every fileset is a full backup", out)
            self.assertIn(f"retention   : retention_table.py sha256[:16]={hashlib.sha256(Path(finish.RETENTION_TABLE).read_bytes()).hexdigest()[:16]}", out)
            code, later, _err = self.run_main("--dest", tmp, "plan", "--at", "2027-06-01T00:00:00Z")
            self.assertEqual(code, finish.EXIT_PASS)
            self.assertNotEqual(later.count("  DELETE  "), 8, "seven months on, the frames have moved and so has the answer")
            self.assertIn("from 2027-06-01T00:00:00Z", later)
            code, _out, err = self.run_main("--dest", os.path.join(tmp, "missing"), "plan")
            self.assertEqual(code, finish.EXIT_ERROR)
            self.assertIn("cannot list", err)

    def test_a_file_that_cannot_be_read_ends_in_a_verdict_not_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in DLISTS_2026_11_11[:-1]:
                (Path(tmp) / name).write_bytes(b"x")
            (Path(tmp) / DLISTS_2026_11_11[-1]).symlink_to(Path(tmp) / "gone")  # listed by name; its size cannot be read
            code, out, err = self.run_main("--dest", tmp, "plan", "--at", "2026-11-12T01:00:00Z")
            self.assertEqual(code, finish.EXIT_ERROR)
            self.assertIn("VERDICT: ERROR", out)
            self.assertIn("FileNotFoundError", err)

    def test_a_sibling_script_that_cannot_be_imported_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.py"
            broken.write_text("import a_module_that_is_not_installed_anywhere\n")
            with self.assertRaises(finish.ToolError) as caught:
                finish.load_module(str(broken), "phase_d_broken_fixture")
            self.assertIn("cannot import broken.py", str(caught.exception))


class WrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WRAPPER.read_text(encoding="utf-8")
        self.code = "\n".join(line for line in self.text.splitlines() if not line.lstrip().startswith("#"))

    def test_it_pins_the_interpreter_and_the_path(self) -> None:
        self.assertIn("PY=/usr/bin/python3", self.code)
        self.assertIn("ENV=/usr/bin/env", self.code)
        self.assertIn('exec "$ENV" -i "${keep[@]}" "$PY" -I "$TOOL" "$@"', self.code)
        self.assertNotIn("python3 ", self.code.replace("/usr/bin/python3", ""), "no interpreter is looked up on PATH")
        lines = self.code.splitlines()
        export = lines.index("export PATH=/usr/sbin:/usr/bin:/sbin:/bin")
        first_lookup = min(i for i, line in enumerate(lines) if "$(" in line)
        self.assertLess(export, first_lookup, "PATH is fixed before the first command is looked up")

    def test_the_environment_is_an_allow_list(self) -> None:
        self.assertIn('keep=("PATH=$PATH" LC_ALL=C.UTF-8 LANG=C.UTF-8)', self.code)
        self.assertIn("for name in HOME USER LOGNAME TERM; do", self.code)
        self.assertEqual(self.code.count("keep+=("), 3, "HOME and its three companions, then TMPDIR as root or as the caller has it")

    def test_as_root_tmpdir_is_the_run_root_and_no_privilege_is_raised(self) -> None:
        self.assertIn('keep+=("TMPDIR=$run_root")', self.code)
        self.assertIn("run_root=/root/phase-d-tmp", self.code)
        for word in ("sudo", "pkexec", "doas", "su -"):
            self.assertNotIn(word, self.code)
        self.assertNotIn("/tmp", self.code.replace("phase-d-tmp", ""))  # tmp-path-literal: allow

    @unittest.skipIf(os.geteuid() == 0, "as root the wrapper wants the real run root")
    def test_it_runs_the_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in DLISTS_2026_11_11:
                (Path(tmp) / name).write_bytes(b"x")
            env = dict(os.environ, PYTHONPATH="/nonexistent/should-be-ignored", PATH="/nonexistent:" + os.environ.get("PATH", ""))
            proc = subprocess.run(["/bin/bash", str(WRAPPER), "--dest", tmp, "plan", "--at", "2026-11-12T01:00:00Z"], capture_output=True, text=True, env=env, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("predicted   : 8 of 16 deleted", proc.stdout)
            proc = subprocess.run(["/bin/bash", str(WRAPPER), "aside"], capture_output=True, text=True, env=env, check=False)
            self.assertEqual(proc.returncode, finish.EXIT_REFUSED)
            self.assertIn("VERDICT: REFUSED", proc.stdout)

    @unittest.skipIf(os.geteuid() == 0, "as root the wrapper wants the real run root")
    @unittest.skipUnless(os.path.exists("/usr/bin/python3"), "the wrapper starts /usr/bin/python3 by its full path")
    def test_a_variable_outside_the_allow_list_does_not_reach_the_tool(self) -> None:
        # COLUMNS is the canary: argparse wraps its help to it. Given straight to the tool it narrows the help;
        # given to the wrapper it must change nothing.
        env = dict(os.environ, COLUMNS="30")
        direct = subprocess.run(["/usr/bin/python3", "-I", str(TOOL), "--help"], capture_output=True, text=True, env=env, check=False)
        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertLess(max(len(line) for line in direct.stdout.splitlines()), 50, "the canary must work, or the next assertion proves nothing")
        wrapped = subprocess.run(["/bin/bash", str(WRAPPER), "--help"], capture_output=True, text=True, env=env, check=False)
        self.assertEqual(wrapped.returncode, 0, wrapped.stderr)
        self.assertGreater(max(len(line) for line in wrapped.stdout.splitlines()), 60)


if __name__ == "__main__":
    unittest.main()
