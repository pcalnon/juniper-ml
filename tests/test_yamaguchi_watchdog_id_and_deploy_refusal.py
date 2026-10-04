#!/usr/bin/env python3
"""Illegal job ids recorded by the watchdog, and the deploy script's argument gate, executed.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_watchdog.py`` rejects ``0``, ``abc`` and ``7\\n`` through ``check()``,
which returns a verdict and writes nothing. The absent and empty ids are the only ones
``main()`` records. An id that is present but illegal -- including one that contains a
newline -- has to come out as a single ``backup=INVALID`` line, or the append-only log
that ``yamaguchi_reboot_verify.bash`` reads field-by-field splits in two.

The same suite checks the deploy script statically and never runs it, because a regex-valid
``--backup-id`` continues into ``systemctl --user``. This file runs only the argument
refusals, which exit before that, and reads the gate's pattern to confirm ``2`` (the interim
id, until the web credential exists) is still accepted. It does not execute a valid id.

No server is contacted.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

wd = load_ad_hoc("yamaguchi_watchdog")
api = wd.api

DEPLOY = AD_HOC / "yamaguchi_watchdog_deploy.bash"
_HOST_MARKERS = ("systemctl", "daemon-reload", "loginctl", "enable-linger", "install -m")


def _deploy_id_pattern() -> re.Pattern[str]:
    """The executable ``BACKUP_ID`` gate, not a copy of it in a comment."""
    for line in DEPLOY.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith('if [[ ! "$BACKUP_ID" =~ '):
            pattern = stripped.split("=~ ", 1)[1].removesuffix(" ]]; then")
            return re.compile(pattern)
    raise AssertionError("yamaguchi_watchdog_deploy.bash no longer has the BACKUP_ID regex gate")


class IllegalIdRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        cred = write_credential(self.dir / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(cred)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(api, "BASE", STUB_BASE),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = wd.main(list(argv))
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
        self.assertNotIn(FIXTURE_MARKER, out.getvalue() + err.getvalue())
        return rc, out.getvalue(), err.getvalue()

    def test_an_illegal_id_is_recorded_on_one_line_and_sends_nothing(self) -> None:
        """Present but not a positive integer: ALERT, durable, one line, no request."""
        illegal = ("0", "07", "7\n8", "2/../serverstate", " 7", "7 ")
        for bad in illegal:
            with self.subTest(backup_id=bad):
                self.fake.requests.clear()
                state = self.dir / bad.encode().hex()
                rc, out, _ = self.run_main("--backup-id", bad, "--state-dir", str(state), "--no-notify")
                self.assertEqual(rc, 1)
                raw = (state / "server-watchdog.status").read_text(encoding="utf-8")
                self.assertEqual(raw.count("\n"), 1, raw)
                self.assertRegex(raw, r"^\S+ ALERT JOB_MISSING backup=INVALID --backup-id is not a job id ")
                self.assertIn(f"got {len(bad)} character(s)", raw)
                self.assertEqual((state / "server-failures.log").read_text(encoding="utf-8"), raw)
                self.assertEqual((state / "server-watchdog.log").read_text(encoding="utf-8"), raw)
                self.assertEqual(out.strip(), raw.strip())
                self.assertEqual(self.fake.requests, [])


class DeployArgumentRefusalTest(unittest.TestCase):
    """Execute the deploy script's argument gate only. A regex-valid id is never passed."""

    def test_the_gate_accepts_the_interim_id_two(self) -> None:
        """Procedures A0/A/A2 keep job 2 until the web credential exists. Do not run that id."""
        pattern = _deploy_id_pattern()
        self.assertIsNotNone(pattern.fullmatch("2"))
        self.assertIsNotNone(pattern.fullmatch("10"))
        for rejected in ("0", "07", "2a", "", "2/../serverstate"):
            self.assertIsNone(pattern.fullmatch(rejected), rejected)

    def test_a_bad_id_exits_2_before_the_host_is_touched(self) -> None:
        cases = (
            ([], "is required"),
            (["--backup-id"], "usage:"),
            (["--backup-id", ""], "is required"),
            (["--backup-id="], "is required"),
            (["--backup-id", "0"], "positive integer"),
            (["--backup-id", "07"], "positive integer"),
            (["--backup-id=0"], "positive integer"),
            (["--backup-id", "-1"], "positive integer"),
            (["--backup-id", "2/../serverstate"], "positive integer"),
            (["--force"], "unknown argument"),
        )
        pattern = _deploy_id_pattern()
        for argv, snippet in cases:
            with self.subTest(argv=argv):
                for arg in argv:
                    self.assertIsNone(pattern.fullmatch(arg), f"refusing to execute a valid id: {arg!r}")
                result = subprocess.run(["bash", str(DEPLOY), *argv], capture_output=True, text=True, timeout=20, check=False)
                blob = result.stdout + result.stderr
                self.assertEqual(result.returncode, 2, blob)
                self.assertIn(snippet, blob)
                for marker in _HOST_MARKERS:
                    self.assertNotIn(marker, blob)

    def test_help_exits_0_without_touching_the_host(self) -> None:
        for argv in (["--help"], ["-h"]):
            with self.subTest(argv=argv):
                result = subprocess.run(["bash", str(DEPLOY), *argv], capture_output=True, text=True, timeout=20, check=False)
                blob = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, blob)
                self.assertIn("usage:", blob)
                for marker in _HOST_MARKERS:
                    self.assertNotIn(marker, blob)


if __name__ == "__main__":
    unittest.main()
