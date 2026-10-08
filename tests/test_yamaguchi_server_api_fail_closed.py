#!/usr/bin/env python3
"""Fail-closed edges of ``util/ad-hoc/yamaguchi_server_api.py`` the B2 suite does not reach.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_yamaguchi_server_api.py`` pins the happy path of pause/resume, a job id required
before login, and a failed export. It cannot see the branches below. Each one is a way the
operator client goes wrong while still looking like it worked:

* ``delete`` without ``--remote-files`` must not send ``delete-remote-files`` (that query
  deletes the uploaded volumes); a 204 with an empty body is still success, and a 500 leaves
  stdout empty;
* a pause or resume whose POST returned 200 is still a failure when the read-back failed or
  was not an object -- a 200 alone does not prove the scheduler moved;
* a login 200 that is not an object, or an object with no ``AccessToken``, exits before the
  verb and sends nothing else;
* ``log`` refuses a non-200 and a non-list body (it must not iterate an error object) and
  still prints a Message that is already an object or is null;
* ``progress`` does not call ``progressstate`` when nothing is running, and an active task's
  line omits keys the caller did not ask for;
* ``status`` prints a backup that is not wrapped in ``Backup``, including its metadata, and
  does not invent a backup line from an error object;
* ``task`` / ``abort`` / ``import`` failures leave stdout empty, and a task line is only the
  five status keys;
* ``serverstate`` exits 1 on a 200 that is not an object, and a Paused state with no
  ``EstimatedPauseEnd`` is indefinite (not ``until None``);
* ``req`` caps an error body at 500 characters and turns an empty or whitespace success body
  into ``{}``.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``'s router.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

api = load_ad_hoc("yamaguchi_server_api")

TARGET = "file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
LOGIN = ("POST", "/api/v1/auth/login")
# Fixture values, never credentials: a login body carrying the wrong field, and a task field the
# client must not print. Held in names so the literals do not sit under a "Token" / "Secret" key.
WRONG_FIELD_MARKER = "not-the-access-marker"
UNLISTED_FIELD_MARKER = "should-not-print"


def state(program="Running", active=None, end="0001-01-01T00:00:00Z"):
    body = {"ProgramState": program, "SchedulerQueueIds": [], "ActiveTask": active, "ProposedSchedule": []}
    if end is not None:
        body["EstimatedPauseEnd"] = end
    return body


class _Cli(unittest.TestCase):
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

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = api.main(list(argv))
            except SystemExit as exc:
                if isinstance(exc.code, str):
                    err.write(exc.code + "\n")
                    rc = 1
                else:
                    rc = 0 if exc.code is None else exc.code
        self.assertNotIn(FIXTURE_MARKER, out.getvalue() + err.getvalue(), "the password must never be printed")
        return rc, out.getvalue(), err.getvalue()


class DeleteDoesNotImplyRemoteFilesTest(_Cli):
    def test_delete_without_remote_files_sends_no_remote_query(self) -> None:
        """The flag is opt-in. Always appending it would delete the uploaded volumes."""
        self.fake.route("DELETE", "/api/v1/backup/7", 204, None)
        rc, out, _ = self.run_cli("delete", "--backup-id", "7", "--yes")
        self.assertEqual(rc, 0)
        self.assertIn("delete backup 7 (remote=False): 204", out)
        delete = self.fake.requests[-1]
        self.assertEqual(delete.query, {})
        self.assertNotIn("delete-remote-files", delete.url)

    def test_a_refused_delete_leaves_stdout_empty(self) -> None:
        self.fake.route("DELETE", "/api/v1/backup/7", 500, {"Error": "busy"})
        rc, out, err = self.run_cli("delete", "7", "--yes")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("delete backup 7 failed 500", err)
        self.assertNotIn("delete-remote-files", self.fake.requests[-1].url)


class ReadBackFailureTest(_Cli):
    def test_a_pause_whose_read_back_failed_exits_1(self) -> None:
        """POST 200 is not proof the scheduler moved. A failed read-back must not exit 0."""
        self.fake.route("POST", "/api/v1/serverstate/pause", 200, {"Status": "OK"})
        self.fake.route("GET", "/api/v1/serverstate", 500, {"Error": "unavailable"})
        rc, out, err = self.run_cli("pause")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("serverstate failed 500", err)
        self.assertEqual(self.fake.paths(), [LOGIN, ("POST", "/api/v1/serverstate/pause"), ("GET", "/api/v1/serverstate")])

    def test_a_resume_whose_read_back_is_not_an_object_exits_1(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/resume", 200, {})
        self.fake.route("GET", "/api/v1/serverstate", 200, ["Paused"])
        rc, out, err = self.run_cli("resume")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("serverstate failed 200", err)


class LoginShapeTest(_Cli):
    def test_a_login_200_without_a_token_never_calls_the_verb(self) -> None:
        cases = ({"Token": WRONG_FIELD_MARKER}, ["not-an-object"])
        for body in cases:
            with self.subTest(body=body):
                self.fake.requests.clear()
                self.fake.route("POST", "/api/v1/auth/login", 200, body)
                self.fake.route("GET", "/api/v1/serverstate", 200, state())
                rc, out, err = self.run_cli("serverstate")
                self.assertEqual((rc, out), (1, ""))
                self.assertIn("FATAL: login failed (200)", err)
                self.assertEqual(self.fake.paths(), [LOGIN])


class LogShapeTest(_Cli):
    def test_a_non_list_log_exits_1_with_empty_stdout(self) -> None:
        """An error object must not be iterated as log entries."""
        for status, payload in ((500, {"Error": "down"}), (200, {"Message": "not a list"})):
            with self.subTest(status=status):
                self.fake.route("GET", "/api/v1/backup/7/log", status, payload)
                rc, out, err = self.run_cli("log", "--backup-id", "7")
                self.assertEqual((rc, out), (1, ""))
                self.assertIn(f"log failed {status}", err)

    def test_a_dict_message_and_a_null_message_still_print(self) -> None:
        self.fake.route(
            "GET",
            "/api/v1/backup/7/log",
            200,
            [
                {"ID": 2, "Message": {"ParsedResult": "Success", "MainOperation": "Backup", "BeginTime": "2026-10-01T00:00:00Z"}},
                {"ID": 1, "Message": None},
            ],
        )
        rc, out, _ = self.run_cli("log", "7")
        self.assertEqual(rc, 0)
        rows = [json.loads(line) for line in out.splitlines()]
        self.assertEqual(rows[0]["ParsedResult"], "Success")
        self.assertEqual(rows[0]["MainOperation"], "Backup")
        self.assertIsNone(rows[1]["ParsedResult"])
        self.assertFalse(rows[1]["DeleteResults"])


class ProgressAndStatusShapeTest(_Cli):
    def test_idle_progress_does_not_call_progressstate(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        rc, out, _ = self.run_cli("progress")
        self.assertEqual((rc, out.strip()), (0, "no active task"))
        self.assertNotIn(("GET", "/api/v1/progressstate"), self.fake.paths())

    def test_an_active_task_prints_phase_and_omits_extra_keys(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state(active={"Item1": 9, "Item2": "7"}))
        self.fake.route("GET", "/api/v1/progressstate", 200, {"Phase": "Backup_ProcessingFiles", "BackupID": "7", "InternalNote": "hidden"})
        rc, out, _ = self.run_cli("progress")
        self.assertEqual(rc, 0)
        shown = json.loads(out)
        self.assertEqual(shown["Phase"], "Backup_ProcessingFiles")
        self.assertEqual(shown["BackupID"], "7")
        self.assertNotIn("InternalNote", shown)
        self.assertIn(("GET", "/api/v1/progressstate"), self.fake.paths())

    def test_status_prints_an_unwrapped_backup_and_its_metadata(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        self.fake.route(
            "GET",
            "/api/v1/backups",
            200,
            [
                {
                    "ID": "7",
                    "Name": "Yamaguchi",
                    "TargetURL": TARGET,
                    "Metadata": {"LastBackupDate": "2026-10-01T00:00:00Z", "SourceFilesSize": 10},
                }
            ],
        )
        rc, out, _ = self.run_cli("status")
        self.assertEqual(rc, 0)
        self.assertIn(f"backup id=7 name='Yamaguchi' target={TARGET}", out)
        self.assertIn("LastBackupDate=2026-10-01T00:00:00Z", out)
        self.assertIn("SourceSize=10", out)

    def test_a_non_list_backup_body_does_not_invent_a_backup_line(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        self.fake.route("GET", "/api/v1/backups", 500, {"Error": "no"})
        rc, out, _ = self.run_cli("status")
        self.assertEqual(rc, 0)
        self.assertIn('"ProgramState": "Running"', out)
        self.assertNotIn("backup id=", out)


class VerbFailureStdoutTest(_Cli):
    def test_task_prints_only_the_five_keys(self) -> None:
        self.fake.route(
            "GET",
            "/api/v1/task/12",
            200,
            {
                "Status": "Running",
                "ID": 12,
                "TaskStarted": "2026-10-04T00:00:00Z",
                "TaskFinished": None,
                "ErrorMessage": None,
                "Secret": UNLISTED_FIELD_MARKER,
            },
        )
        rc, out, _ = self.run_cli("task", "12")
        self.assertEqual(rc, 0)
        self.assertEqual(set(json.loads(out)), {"Status", "ID", "TaskStarted", "TaskFinished", "ErrorMessage"})
        self.assertNotIn(UNLISTED_FIELD_MARKER, out)

    def test_failed_task_abort_and_import_leave_stdout_empty(self) -> None:
        self.fake.route("GET", "/api/v1/task/12", 500, {"Error": "no"})
        rc, out, err = self.run_cli("task", "12")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("task 12 failed 500", err)

        self.fake.route("POST", "/api/v1/task/12/abort", 500, {"Error": "no"})
        rc, out, err = self.run_cli("abort", "12")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("abort task 12 failed 500", err)

        exported = self.dir / "job.json"
        exported.write_text("{}", encoding="utf-8")
        self.fake.route("POST", "/api/v1/backups", 500, {"Error": "no"})
        rc, out, err = self.run_cli("import", str(exported))
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("import failed 500", err)


class ServerStateShapeTest(_Cli):
    def test_a_non_object_serverstate_exits_1(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, ["Running"])
        rc, out, err = self.run_cli("serverstate")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("serverstate failed 200", err)

    def test_a_paused_state_with_no_end_is_indefinite(self) -> None:
        """Missing EstimatedPauseEnd is 'no expiry', the same as the zero DateTime. Not 'until None'."""
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Paused", end=None))
        rc, out, _ = self.run_cli("serverstate")
        self.assertEqual(rc, 2)
        shown = json.loads(out)
        self.assertTrue(shown["Pause"].startswith("indefinite"), shown["Pause"])
        self.assertNotIn("None", shown["Pause"])


class ReqBodyBoundTest(_Cli):
    def test_an_error_body_is_capped_and_an_empty_success_is_an_object(self) -> None:
        marker = "TAIL-MARKER-NOT-IN-THE-PREFIX"
        self.fake.route("GET", "/api/v1/serverstate", 500, "A" * 800 + marker)
        status, body = api.req("GET", "/api/v1/serverstate")
        self.assertEqual(status, 500)
        self.assertLessEqual(len(body["error"]), 500)
        self.assertNotIn(marker, body["error"])
        self.assertIn("A", body["error"])

        for payload in (None, b" \n\t"):
            with self.subTest(payload=payload):
                self.fake.route("GET", "/api/v1/serverstate", 200, payload)
                status, body = api.req("GET", "/api/v1/serverstate")
                self.assertEqual((status, body), (200, {}))


if __name__ == "__main__":
    unittest.main()
