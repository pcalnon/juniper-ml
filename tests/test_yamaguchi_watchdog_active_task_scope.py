#!/usr/bin/env python3
"""Active-task scope and mid-scan log failures for ``util/ad-hoc/yamaguchi_watchdog.py``.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_watchdog.py`` pins ProgramState, Backup freshness, keyset paging,
and an ``ActiveTask`` whose ``Item2`` is the watched job. Those fixtures keep the task
and the job on the same id, and a non-200 log status fails the first page, so ``newest``
stays unset. This suite pins the branches those fixtures cannot reach:

* a later log page that fails after a successful non-Backup page is ``LOG_UNAVAILABLE``,
  with the status and the number of entries already examined;
* a log entry that carries no ``ID`` ends the scan (the offset would otherwise be empty);
* a short task for a different job does not make a stale backup read ``OK``;
* a stuck task for a different job is still ``STUCK``, and the log is not consulted;
* a non-200 read of our own task falls through to the log;
* a bare task id (not an ``Item1``/``Item2`` dict) that has already run too long is ``STUCK``;
* ``main`` still writes the durable record when ``parse_iso`` raises.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``'s router.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

wd = load_ad_hoc("yamaguchi_watchdog")
api = wd.api

ZERO_DATE = "0001-01-01T00:00:00Z"
JOB = "7"


def ago(hours: float) -> str:
    """A Duplicati-shaped UTC stamp: seven fractional digits, as .NET writes them."""
    when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    return when.strftime("%Y-%m-%dT%H:%M:%S.") + "1234567Z"


def entry(entry_id: int, operation: str, result: str, hours: float) -> dict:
    message = {"MainOperation": operation, "ParsedResult": result, "BeginTime": ago(hours)}
    return {"ID": entry_id, "Type": "Result", "Message": json.dumps(message)}


def server_state(program: str = "Running", queue: list | None = None, end: str = ZERO_DATE, active: object = None) -> dict:
    return {"ProgramState": program, "SchedulerQueueIds": [] if queue is None else queue, "EstimatedPauseEnd": end, "ActiveTask": active}


class _Scope(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.state_dir = self.dir / "state"
        self.cred = write_credential(self.dir / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.cred)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(api, "BASE", STUB_BASE),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.serve()

    def serve(self, state: dict | None = None, log: list | None = None) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, server_state() if state is None else state)
        self.fake.route("GET", "/api/v1/backups", 200, [{"Backup": {"ID": JOB, "Name": "Yamaguchi"}}])
        entries = [entry(10, "Backup", "Success", 2.0)] if log is None else log

        def page(query: dict) -> tuple[int, object]:
            size = int(query["pagesize"])
            start = 0
            if "offset" in query:
                ids = [e["ID"] for e in entries]
                start = ids.index(int(query["offset"])) + 1
            return 200, entries[start : start + size]

        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=page)

    def args(self, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {"base": STUB_BASE, "backup_id": JOB, "max_age_hours": 26.0, "max_run_hours": 6.0, "state_dir": str(self.state_dir), "notify": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def check(self, **overrides: object) -> tuple[str, str, str]:
        verdict, code, details = wd.check(self.args(**overrides))
        self.assertNotIn(FIXTURE_MARKER, details)
        return verdict, code, details

    def log_requests(self) -> list:
        return [r for r in self.fake.requests if r.path == f"/api/v1/backup/{JOB}/log"]


class LogScanScopeTest(_Scope):
    def test_a_failed_later_log_page_is_undetermined(self) -> None:
        """The first page is a successful Test, so ``newest`` is set. The failure is the next page."""
        calls = {"n": 0}

        def page(query: dict) -> tuple[int, object]:
            calls["n"] += 1
            if calls["n"] == 1:
                return 200, [entry(i, "Test", "Success", 0.5) for i in range(40, 20, -1)]
            return 500, {"Error": "log unavailable"}

        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=page)
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("UNDETERMINED", "LOG_UNAVAILABLE"))
        self.assertIn("log -> 500", details)
        self.assertIn("20 entries examined", details)
        self.assertEqual(len(self.log_requests()), 2)

    def test_a_log_entry_with_no_id_ends_the_scan(self) -> None:
        body = {"Message": json.dumps({"MainOperation": "Test", "ParsedResult": "Success", "BeginTime": ago(1.0)})}
        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=lambda query: (200, [body]))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("newest 1 log entries", details)
        self.assertEqual(len(self.log_requests()), 1)


class ActiveTaskScopeTest(_Scope):
    def test_a_short_task_for_another_job_leaves_a_stale_backup_stale(self) -> None:
        self.serve(state=server_state(active={"Item1": 5, "Item2": "9"}), log=[entry(10, "Backup", "Success", 30.0)])
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": ago(1.0)})
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("age=30.0h", details)

    def test_a_stuck_task_for_another_job_alerts_before_the_log(self) -> None:
        self.serve(state=server_state(active={"Item1": 5, "Item2": "9"}), log=[entry(10, "Backup", "Success", 1.0)])
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": ago(7.0)})
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STUCK"))
        self.assertIn("task 5", details)
        self.assertIn("backup 9", details)
        self.assertEqual(self.log_requests(), [])

    def test_an_unreadable_task_falls_through_to_the_log(self) -> None:
        self.serve(state=server_state(active={"Item1": 5, "Item2": JOB}), log=[entry(10, "Backup", "Error", 1.0)])
        self.fake.route("GET", "/api/v1/task/5", 500, {"Error": "unavailable"})
        self.assertEqual(self.check()[:2], ("ALERT", "NOT_SUCCESS"))

    def test_a_bare_task_id_that_has_run_too_long_is_stuck(self) -> None:
        self.serve(state=server_state(active=5), log=[entry(10, "Backup", "Success", 1.0)])
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": ago(7.0)})
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STUCK"))
        self.assertIn("task 5", details)
        self.assertEqual(self.log_requests(), [])


class MainRecordTest(_Scope):
    def test_an_unparseable_task_start_still_leaves_a_record(self) -> None:
        self.serve(state=server_state(active={"Item1": 5, "Item2": JOB}))
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": "not-a-timestamp"})
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = wd.main(["--backup-id", JOB, "--base", STUB_BASE, "--state-dir", str(self.state_dir), "--no-notify"])
        self.assertEqual(rc, 2)
        status = (self.state_dir / "server-watchdog.status").read_text(encoding="utf-8")
        failures = (self.state_dir / "server-failures.log").read_text(encoding="utf-8")
        self.assertIn("UNDETERMINED EXCEPTION", status)
        self.assertIn("ValueError", status)
        self.assertIn("UNDETERMINED EXCEPTION", failures)
        self.assertNotIn(FIXTURE_MARKER, status + failures + out.getvalue() + err.getvalue())


if __name__ == "__main__":
    unittest.main()
