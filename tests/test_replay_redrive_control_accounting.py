#!/usr/bin/env python3
"""What the CAN-015 replay re-drive counts as a control, and when a read has settled.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-10-04_replay_redrive.py`` decides the echo-loop and F-CANOPY-056
verdicts from ``control_requests``: the status codes of ``POST /replay/control`` lines
in cascor's uvicorn log. A counter that also matches ``/v1/training/start``, a GET, or
an unquoted lookalike makes an idle player look busy (or a real control look absent).
A missing log that comes back as no requests is the same false idle. ``poll`` is how
every DOM reading settles; a read that raises is a reading, and a miss stops at the
deadline rather than spinning.

No browser, no cascor, no socket. ``requests`` is imported by the script and is not
used by these functions; a missing install is stubbed so the import still loads.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
import unittest.mock as mock
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-10-04_replay_redrive.py"


def load_redrive():
    """Import the ad-hoc script even when ``requests`` is not installed.

    CI's test job does not install ``requests``. The stand-in must carry ``Session``: before
    Python 3.14 a return annotation is evaluated when its function is defined, and the script's
    ``api_session() -> tuple[requests.Session, ...]`` is, so a bare module fails the import on
    3.12 and 3.13 with ``AttributeError``. The stand-in is visible only while the script loads.
    """
    stand_ins: dict[str, types.ModuleType] = {}
    if importlib.util.find_spec("requests") is None:
        stand_in = types.ModuleType("requests")
        stand_in.Session = object
        stand_ins["requests"] = stand_in
    spec = importlib.util.spec_from_file_location("replay_redrive_under_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, stand_ins):
        spec.loader.exec_module(module)
    return module


class _Clock:
    """``time.time`` / ``time.sleep`` that advance together, and refuse to spin."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start
        self.slept: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds
        if len(self.slept) > 20:
            raise AssertionError("poll ignored its deadline")


class ControlAccountingTest(unittest.TestCase):
    mod: types.ModuleType

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_redrive()

    def write_log(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "juniper-cascor.log"
        path.write_text(text, encoding="utf-8")
        return path

    def test_only_quoted_control_posts_count_and_order_is_kept(self) -> None:
        """The echo-loop window is the length of this list. Neighbours must not change it."""
        log = self.write_log(
            "\n".join(
                (
                    'INFO: 127.0.0.1:9 - "POST /v1/snapshots/abc-def/replay/control HTTP/1.1" 200 OK',
                    'INFO: 127.0.0.1:9 - "GET /v1/snapshots/abc-def/replay/control HTTP/1.1" 200 OK',
                    'INFO: 127.0.0.1:9 - "POST /v1/snapshots/abc-def/replay HTTP/1.1" 200 OK',
                    'INFO: 127.0.0.1:9 - "POST /v1/snapshots/a/b/replay/control HTTP/1.1" 200 OK',
                    'INFO: 127.0.0.1:9 - "POST /v1/training/start HTTP/1.1" 200 OK',
                    "noise POST /v1/snapshots/abc-def/replay/control HTTP/1.1 200",
                    'INFO: 127.0.0.1:9 - "POST /v1/snapshots/abc-def/replay/control HTTP/1.1" 500 Internal Server Error',
                )
            )
            + "\n"
        )
        self.assertEqual(self.mod.control_requests(log), ["200", "500"])

    def test_a_missing_log_raises_rather_than_looking_idle(self) -> None:
        """An empty list is what an idle player produces. A missing file must not look like one."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        missing = Path(directory.name) / "absent.log"
        with self.assertRaises(FileNotFoundError):
            self.mod.control_requests(missing)

    def test_an_undecodable_byte_does_not_drop_a_control_line(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "juniper-cascor.log"
        path.write_bytes(b'before \xff still open\nINFO: "POST /v1/snapshots/snap-1/replay/control HTTP/1.1" 204\n')
        self.assertEqual(self.mod.control_requests(path), ["204"])

    def test_poll_returns_on_the_first_accepted_reading(self) -> None:
        clock = _Clock()
        readings = iter([0, 0, 7])
        with mock.patch.object(self.mod.time, "time", clock.time), mock.patch.object(self.mod.time, "sleep", clock.sleep):
            ok, value = self.mod.poll(lambda: next(readings), lambda item: item == 7, 30.0, 0.25)
        self.assertEqual((ok, value), (True, 7))
        self.assertEqual(clock.slept, [0.25, 0.25])

    def test_a_failed_read_is_a_reading_and_a_miss_stops_at_the_deadline(self) -> None:
        clock = _Clock()
        calls = {"n": 0}

        def read():
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("socket down")
            return "later"

        with mock.patch.object(self.mod.time, "time", clock.time), mock.patch.object(self.mod.time, "sleep", clock.sleep):
            ok, value = self.mod.poll(read, lambda item: isinstance(item, str) and item.startswith("<error "), 5.0, 1.0)
        self.assertEqual(ok, True)
        self.assertIn("TimeoutError", value)
        self.assertIn("socket down", value)
        self.assertEqual(clock.slept, [])

        clock = _Clock()
        with mock.patch.object(self.mod.time, "time", clock.time), mock.patch.object(self.mod.time, "sleep", clock.sleep):
            ok, value = self.mod.poll(lambda: "no", lambda item: False, 1.0, 0.4)
        self.assertEqual((ok, value), (False, "no"))
        self.assertEqual(clock.slept, [0.4, 0.4, 0.4])
        self.assertGreater(clock.now, 1_001.0)
        self.assertLess(clock.now, 1_001.0 + 0.4)

    def test_evidence_save_writes_rows_and_stringifies_a_non_json_detail(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        out = Path(directory.name)
        evidence = self.mod.Evidence(out)
        with redirect_stdout(io.StringIO()):
            evidence.row("echo loop", "FAIL", {"during_15s_idle": 3})
            evidence.row("stamp", "PASS", dt.datetime(2026, 10, 4, 1, 2, 3, tzinfo=dt.timezone.utc))
            evidence.save()
        text = (out / "verdicts.json").read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"))
        body = json.loads(text)
        self.assertEqual(body["rows"][0]["check"], "echo loop")
        self.assertEqual(body["rows"][0]["verdict"], "FAIL")
        self.assertEqual(body["rows"][0]["detail"], {"during_15s_idle": 3})
        self.assertTrue(body["rows"][0]["at"].endswith("Z"))
        self.assertEqual(body["rows"][1]["detail"], "2026-10-04 01:02:03+00:00")
        self.assertIn("started", body["notes"])
        self.assertIn("finished", body["notes"])


if __name__ == "__main__":
    unittest.main()
