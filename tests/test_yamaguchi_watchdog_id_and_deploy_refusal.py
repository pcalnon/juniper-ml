#!/usr/bin/env python3
"""Illegal job ids recorded by the watchdog, and the deploy script's argument gate, read statically.

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

The deploy script is never executed here, for the reason that suite gives: it changes systemd
user units, so no test runs it. Its argument gate is READ instead. That suite pins the gate's
ordering and the empty-id branch's ``exit 2``; this file pins the rest of the gate -- every
refusal branch before the first host-touching line ends in ``exit 2`` rather than printing and
falling through into the deploy -- and that the gate's pattern still accepts ``2``, the interim
id until the web credential exists.

No server is contacted, and no script is run.
"""

from __future__ import annotations

import io
import os
import re
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

wd = load_ad_hoc("yamaguchi_watchdog")
api = wd.api

DEPLOY = AD_HOC / "yamaguchi_watchdog_deploy.bash"
# The first line that reads or changes the host: the same predicate as
# tests/test_yamaguchi_watchdog.py's test_the_id_is_refused_before_the_host_is_touched.
_HOST_LINE = re.compile(r"^(if \[ ! -f|if ! grep|linger=\$\(loginctl|install |systemctl |printf .*>)")
_EXIT = re.compile(r"^exit \d+$")


def _deploy_id_pattern() -> re.Pattern[str]:
    """The executable ``BACKUP_ID`` gate, not a copy of it in a comment."""
    for line in DEPLOY.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith('if [[ ! "$BACKUP_ID" =~ '):
            pattern = stripped.split("=~ ", 1)[1].removesuffix(" ]]; then")
            return re.compile(pattern)
    raise AssertionError("yamaguchi_watchdog_deploy.bash no longer has the BACKUP_ID regex gate")


def _deploy_gate() -> list[str]:
    """The argument gate as stripped lines: from ``BACKUP_ID=""`` up to the first host-touching line."""
    lines = [line.strip() for line in DEPLOY.read_text(encoding="utf-8").splitlines()]
    if 'BACKUP_ID=""' not in lines:
        raise AssertionError('yamaguchi_watchdog_deploy.bash no longer starts its gate with BACKUP_ID=""')
    start = lines.index('BACKUP_ID=""')
    end = next((i for i in range(start, len(lines)) if _HOST_LINE.match(lines[i])), None)
    if end is None:
        raise AssertionError("no host-touching line after the argument gate -- the predicate needs updating")
    return lines[start:end]


def _branch_end(gate: list[str], index: int) -> str:
    """How the branch holding ``gate[index]`` ends: its first ``exit N``, ``fi`` or ``;;``."""
    for line in gate[index + 1 :]:
        if _EXIT.match(line) or line in ("fi", ";;"):
            return line
    return "<end of gate>"


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


class DeployArgumentGateTest(unittest.TestCase):
    """Static only, like tests/test_yamaguchi_watchdog.py: the deploy script is read, never run."""

    def test_the_gate_accepts_the_interim_id_two(self) -> None:
        """Procedures A0/A/A2 keep job 2 until the web credential exists."""
        pattern = _deploy_id_pattern()
        self.assertIsNotNone(pattern.fullmatch("2"))
        self.assertIsNotNone(pattern.fullmatch("10"))
        for rejected in ("0", "07", "-1", "2a", "", "2/../serverstate"):
            self.assertIsNone(pattern.fullmatch(rejected), rejected)

    def test_every_refusal_in_the_gate_exits_2(self) -> None:
        """A refusal that prints and falls through would go on to deploy the id it just refused.

        Every ``echo "REFUSE: ...`` and every ``usage`` call before the first host-touching line
        must end its branch with ``exit 2``; only the ``-h | --help`` arm exits 0. The sibling
        suite checks the ordering and the empty-id branch's ``exit 2`` only, so a positive-integer,
        unknown-argument or missing-value branch that lost its exit would pass it.
        """
        gate = _deploy_gate()
        self.assertTrue(any(line.startswith('if [[ ! "$BACKUP_ID" =~ ') for line in gate), "the positive-integer check is not in the gate")
        refusals = [line for line in gate if line.startswith('echo "REFUSE:')]
        for needle in ("unknown argument", "is required", "must be a positive integer"):
            self.assertTrue(any(needle in line for line in refusals), f"no {needle!r} refusal before the first host-touching line")
        self.assertIn("-h | --help)", gate)
        help_start = gate.index("-h | --help)")
        help_end = gate.index(";;", help_start)
        refusing = [i for i, line in enumerate(gate) if line.startswith('echo "REFUSE:') or line == "usage"]
        for i in refusing:
            want = "exit 0" if help_start < i < help_end else "exit 2"
            with self.subTest(line=gate[i]):
                self.assertEqual(_branch_end(gate, i), want)


if __name__ == "__main__":
    unittest.main()
