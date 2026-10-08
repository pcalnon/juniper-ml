#!/usr/bin/env python3
"""Freshness edges of ``util/ad-hoc/yamaguchi_watchdog.py`` the B2 suite cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_watchdog.py`` pins Paused-with-a-queue, and a fresh backup that happens
to be paused with an empty queue. ``tests/test_yamaguchi_watchdog_active_task_scope.py`` pins
the active-task scope. Neither can see:

* a Paused server with an EMPTY queue still alerts STALE when the newest Backup is old -- the
  empty-queue exemption names a startup-delay pause, it does not excuse a missed backup;
* a Success backup with no BeginTime is STALE (an unknown age is not a fresh one);
* a naive BeginTime is judged as UTC, so the age arithmetic does not raise;
* serverstate non-200 is UNREACHABLE and the log is not read;
* a backup list entry that is not wrapped in ``Backup`` still finds the job;
* a queued pause with no EstimatedPauseEnd says indefinite, not ``until None``;
* a transport error at login is UNREACHABLE, the same verdict as a refused credential.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``'s router.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
import unittest
import unittest.mock as mock
import urllib.error
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

wd = load_ad_hoc("yamaguchi_watchdog")
api = wd.api

JOB = "7"


def ago(hours: float) -> str:
    when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    return when.strftime("%Y-%m-%dT%H:%M:%S.") + "1234567Z"


def entry(entry_id: int, operation: str, result: str, hours: float | None) -> dict:
    message: dict = {"MainOperation": operation, "ParsedResult": result}
    if hours is not None:
        message["BeginTime"] = ago(hours)
    return {"ID": entry_id, "Message": json.dumps(message)}


class PauseFreshnessTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
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

    def serve(self, state: dict | None = None, backups: list | None = None, log: list | None = None) -> None:
        if state is None:
            state = {"ProgramState": "Running", "SchedulerQueueIds": [], "EstimatedPauseEnd": "0001-01-01T00:00:00Z", "ActiveTask": None}
        self.fake.route("GET", "/api/v1/serverstate", 200, state)
        self.fake.route("GET", "/api/v1/backups", 200, [{"Backup": {"ID": JOB, "Name": "Yamaguchi"}}] if backups is None else backups)
        entries = [entry(10, "Backup", "Success", 2.0)] if log is None else log

        def page(query: dict) -> tuple[int, object]:
            size = int(query["pagesize"])
            start = 0
            if "offset" in query:
                ids = [e["ID"] for e in entries]
                start = ids.index(int(query["offset"])) + 1
            return 200, entries[start : start + size]

        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=page)

    def args(self, **overrides) -> argparse.Namespace:
        values = {"base": STUB_BASE, "backup_id": JOB, "max_age_hours": 26.0, "max_run_hours": 6.0, "state_dir": str(self.dir / "state"), "notify": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def check(self, **overrides) -> tuple[str, str, str]:
        verdict, code, details = wd.check(self.args(**overrides))
        self.assertNotIn(FIXTURE_MARKER, details)
        return verdict, code, details

    def log_requests(self) -> list:
        return [r for r in self.fake.requests if r.path == f"/api/v1/backup/{JOB}/log"]

    def test_an_empty_pause_queue_does_not_hide_a_stale_backup(self) -> None:
        """The empty-queue exemption is a startup-delay window, not a pass on a missed backup."""
        self.serve(
            state={"ProgramState": "Paused", "SchedulerQueueIds": [], "EstimatedPauseEnd": "2026-10-03T15:30:00Z", "ActiveTask": None},
            log=[entry(10, "Backup", "Success", 30.0)],
        )
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("age=30.0h", details)
        self.assertGreater(len(self.log_requests()), 0, "freshness is still judged; the pause did not return early")

    def test_a_success_with_no_begin_time_is_stale(self) -> None:
        self.serve(log=[entry(10, "Backup", "Success", None)])
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("no BeginTime", details)

    def test_a_naive_begin_time_is_judged_rather_than_raising(self) -> None:
        when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
        stamp = when.strftime("%Y-%m-%dT%H:%M:%S")
        self.serve(log=[{"ID": 10, "Message": json.dumps({"MainOperation": "Backup", "ParsedResult": "Success", "BeginTime": stamp})}])
        self.assertEqual(self.check()[:2], ("OK", "OK"))

    def test_a_failed_serverstate_is_unreachable_and_does_not_read_the_log(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 500, {"Error": "down"})
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "UNREACHABLE"))
        self.assertIn("serverstate -> 500", details)
        self.assertEqual(self.log_requests(), [])
        self.assertNotIn("/api/v1/backups", [r.path for r in self.fake.requests])

    def test_an_unwrapped_backup_list_still_finds_the_job(self) -> None:
        self.serve(backups=[{"ID": JOB, "Name": "Yamaguchi"}])
        self.assertEqual(self.check()[:2], ("OK", "OK"))

    def test_a_queued_pause_with_no_end_says_indefinite(self) -> None:
        self.serve(state={"ProgramState": "Paused", "SchedulerQueueIds": [{"Item1": 3, "Item2": JOB}], "ActiveTask": None})
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "PAUSED_WITH_QUEUE"))
        self.assertIn("pause=indefinite", details)
        self.assertNotIn("until None", details)
        self.assertEqual(self.log_requests(), [])

    def test_a_transport_error_at_login_is_unreachable(self) -> None:
        def refuse(request, timeout=None):
            raise urllib.error.URLError("refused")

        with mock.patch("urllib.request.urlopen", refuse):
            verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "UNREACHABLE"))
        self.assertIn("URLError", details)


if __name__ == "__main__":
    unittest.main()
