#!/usr/bin/env python3
"""``util/ad-hoc/yamaguchi_server_api.py``: the pause/resume/serverstate verbs and the mandatory job id.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

P0 step 10 of the backup design pauses the scheduler, edits the job, dry-runs the pre-backup
guard with the TargetURL read from ``export <id>``, resumes, and samples ``serverstate`` before
and after. The STOP of 2026-09-24 (item 3) found the client had no ``pause``/``resume``, and when
the client fails the dry run's TargetURL is EMPTY -- and the guard compares TargetURL only when
it is non-empty. B2 adds the verbs and makes the job id mandatory (a rebuilt job is not id 2).

Pins, each able to fail for the reason it exists:

* ``serverstate`` exits 0 Running / 2 Paused / 1 otherwise, and usage errors exit 64 so 2 is
  unambiguous; it prints ProgramState, the pause and the queue;
* ``pause`` / ``resume`` POST the vendor's endpoints with no query and no body, then READ BACK the
  state -- a 200 alone does not prove the scheduler moved;
* every job-scoped verb refuses a missing, malformed or contradictory id BEFORE reading the
  credential or sending anything, and server-wide verbs refuse an id;
* ``export`` first POSTs ``/api/v1/auth/issuetoken/export`` and passes that token as the
  ``token`` query parameter (2.4.0.0's export route ignores the Bearer header and 400s
  without it). The operation token is not printed. A failed ``export`` leaves stdout
  EMPTY and exits 1 (its stdout feeds ``json.load``);
* the strings the bash callers grep (``"ActiveTask": null``, ``"SchedulerQueueIds": []``,
  ``target=``, ``"ParsedResult": "Success"``) are unchanged;
* the password is sent only as the login body and printed nowhere.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``'s router, and
the subprocess cases all stop before the network.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, STUB_BASE, STUB_BEARER_MARKER, FakeDuplicati, load_ad_hoc, write_credential
from tests.redacted_env import RedactedEnv

api = load_ad_hoc("yamaguchi_server_api")

SCRIPT = AD_HOC / "yamaguchi_server_api.py"
SCRIPT_TIMEOUT_SECONDS = 20
LOGIN = ("POST", "/api/v1/auth/login")
ZERO_DATE = "0001-01-01T00:00:00Z"
TARGET = "file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
# Distinct from the stub bearer: the export route rejects an access token in the query.
OP_TOKEN = "single-op-export-token"


def state(program="Running", queue=None, end=ZERO_DATE, active=None):
    return {"ProgramState": program, "EstimatedPauseEnd": end, "SchedulerQueueIds": [] if queue is None else queue, "ActiveTask": active, "ProposedSchedule": [{"Item1": "7", "Item2": "2026-10-04T14:00:00Z"}]}


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
                if isinstance(exc.code, str):  # sys.exit("message") -- the interpreter would print it and exit 1
                    err.write(exc.code + "\n")
                    rc = 1
                else:
                    rc = 0 if exc.code is None else exc.code
        self.assertNotIn(FIXTURE_MARKER, out.getvalue() + err.getvalue(), "the password must never be printed")
        return rc, out.getvalue(), err.getvalue()

    def assert_nothing_sent(self) -> None:
        self.assertEqual(self.fake.requests, [], "this path must refuse before reading the credential or contacting the server")


class ServerStateVerbTest(_Cli):
    def test_running_exits_0_and_prints_the_state(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        rc, out, _ = self.run_cli("serverstate")
        self.assertEqual(rc, 0)
        shown = json.loads(out)
        self.assertEqual(shown["ProgramState"], "Running")
        self.assertEqual(shown["Pause"], "none")
        self.assertEqual(shown["SchedulerQueueIds"], [])
        self.assertEqual(self.fake.paths(), [LOGIN, ("GET", "/api/v1/serverstate")])
        get = self.fake.requests[1]
        self.assertEqual(get.headers.get("authorization"), f"Bearer {STUB_BEARER_MARKER}")
        self.assertEqual((get.query, get.body), ({}, None))

    def test_an_indefinite_pause_exits_2_and_shows_the_held_queue(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Paused", [{"Item1": 12, "Item2": "7"}]))
        rc, out, _ = self.run_cli("serverstate")
        self.assertEqual(rc, 2)
        shown = json.loads(out)
        self.assertTrue(shown["Pause"].startswith("indefinite"), shown["Pause"])
        self.assertIn("paused-until", shown["Pause"])
        self.assertEqual(shown["SchedulerQueueIds"], [{"Item1": 12, "Item2": "7"}])

    def test_a_timed_pause_exits_2_and_shows_its_end(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Paused", end="2026-10-03T15:30:00Z"))
        rc, out, _ = self.run_cli("serverstate")
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["Pause"], "until 2026-10-03T15:30:00Z")

    def test_an_unexpected_state_exits_1(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, {"ActiveTask": None})
        rc, _, err = self.run_cli("serverstate")
        self.assertEqual(rc, 1)
        self.assertIn("unexpected ProgramState None", err)

    def test_a_failed_request_exits_1_with_nothing_on_stdout(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 500, {"Error": "boom"})
        rc, out, err = self.run_cli("serverstate")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("serverstate failed 500", err)

    def test_server_wide_verbs_refuse_an_id(self) -> None:
        for argv in (("serverstate", "7"), ("pause", "7"), ("pause", "--backup-id", "7"), ("resume", "7"), ("status", "7"), ("progress", "--backup-id", "7")):
            with self.subTest(argv=argv):
                rc, out, err = self.run_cli(*argv)
                self.assertEqual((rc, out), (api.EXIT_USAGE, ""))
                self.assertIn("error:", err)
        self.assert_nothing_sent()


class PauseResumeTest(_Cli):
    def test_pause_posts_the_vendor_endpoint_then_reads_paused(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/pause", 200, {"Status": "OK"})
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Paused"))
        rc, out, _ = self.run_cli("pause")
        self.assertEqual(rc, 0)
        self.assertEqual(self.fake.paths(), [LOGIN, ("POST", "/api/v1/serverstate/pause"), ("GET", "/api/v1/serverstate")])
        post = self.fake.requests[1]
        self.assertEqual(post.query, {}, "no duration: the pause is indefinite, as P0 step 10 needs")
        self.assertIsNone(post.body)
        self.assertEqual(post.headers.get("authorization"), f"Bearer {STUB_BEARER_MARKER}")
        self.assertEqual(json.loads(out)["ProgramState"], "Paused")

    def test_pause_that_did_not_take_exits_1(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/pause", 200, {})
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Running"))
        rc, _, err = self.run_cli("pause")
        self.assertEqual(rc, 1)
        self.assertIn("not 'Paused'", err)

    def test_a_refused_pause_exits_1_without_reading_back(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/pause", 500, {"Error": "no"})
        rc, out, err = self.run_cli("pause")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("pause failed 500", err)
        self.assertEqual(self.fake.paths(), [LOGIN, ("POST", "/api/v1/serverstate/pause")])

    def test_resume_posts_the_vendor_endpoint_then_reads_running(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/resume", 200, {})
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Running"))
        rc, _, _ = self.run_cli("resume")
        self.assertEqual(rc, 0)
        self.assertEqual(self.fake.paths(), [LOGIN, ("POST", "/api/v1/serverstate/resume"), ("GET", "/api/v1/serverstate")])
        self.assertEqual((self.fake.requests[1].query, self.fake.requests[1].body), ({}, None))

    def test_resume_that_left_it_paused_exits_1(self) -> None:
        self.fake.route("POST", "/api/v1/serverstate/resume", 200, {})
        self.fake.route("GET", "/api/v1/serverstate", 200, state("Paused"))
        rc, _, err = self.run_cli("resume")
        self.assertEqual(rc, 1)
        self.assertIn("not 'Running'", err)

    def test_help_says_the_pause_survives_restarts(self) -> None:
        rc, out, _ = self.run_cli("--help")
        self.assertEqual(rc, 0)
        for needle in ("serverstate", "pause", "resume", "paused-until", "restores it on every restart", "--backup-id", "no default"):
            self.assertIn(needle, out)


class JobIdRequiredTest(_Cli):
    def test_job_verbs_refuse_a_missing_id_before_reading_the_credential(self) -> None:
        with mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.dir / "absent")}):
            for verb in api.JOB_VERBS:
                with self.subTest(verb=verb):
                    rc, out, err = self.run_cli(verb, "--yes")
                    self.assertEqual((rc, out), (api.EXIT_USAGE, ""))
                    self.assertIn("--backup-id", err)
                    self.assertIn("no default", err)
        self.assert_nothing_sent()

    def test_malformed_or_contradictory_ids_are_refused(self) -> None:
        cases = [("export", "0"), ("export", "07"), ("export", "-1"), ("export", "abc"), ("export", "2/../serverstate"), ("export", "7\n"), ("run", "--backup-id", "7 "), ("log", "7", "--backup-id", "8"), ("delete", "--backup-id", "", "--yes"), ("abort", "12\n")]
        for argv in cases:
            with self.subTest(argv=argv):
                rc, out, _ = self.run_cli(*argv)
                self.assertEqual((rc, out), (api.EXIT_USAGE, ""))
        self.assert_nothing_sent()

    def test_export_by_flag_or_position_prints_only_the_json(self) -> None:
        config = {"Backup": {"ID": "7", "TargetURL": TARGET}, "Schedule": {"Repeat": "1D"}}
        self.fake.route("POST", "/api/v1/auth/issuetoken/export", 200, {"Token": OP_TOKEN})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, config)
        for argv in (("export", "--backup-id", "7"), ("export", "7"), ("export", "7", "--backup-id", "7")):
            with self.subTest(argv=argv):
                self.fake.requests.clear()
                rc, out, err = self.run_cli(*argv)
                self.assertEqual(rc, 0)
                self.assertEqual(json.loads(out), config, "stdout must be exactly the JSON the design's guard dry-run parses")
                self.assertNotIn(OP_TOKEN, out)
                self.assertNotIn(OP_TOKEN, err)
                issued = [r for r in self.fake.requests if r.path == "/api/v1/auth/issuetoken/export"]
                self.assertEqual(len(issued), 1)
                self.assertIsNone(issued[0].body)
                self.assertEqual(issued[0].headers.get("authorization"), f"Bearer {STUB_BEARER_MARKER}")
                download = self.fake.requests[-1]
                self.assertEqual((download.method, download.path), ("GET", "/api/v1/backup/7/export"))
                self.assertEqual(download.query, {"export-passwords": "false", "token": OP_TOKEN})
                self.assertNotEqual(download.query["token"], STUB_BEARER_MARKER)

    def test_export_accepts_a_lowercase_token_field(self) -> None:
        """Newtonsoft emits ``Token``. A camelCase body must still be used, and not dumped to stderr."""
        config = {"Backup": {"ID": "7", "TargetURL": TARGET}}
        self.fake.route("POST", "/api/v1/auth/issuetoken/export", 200, {"token": OP_TOKEN})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, config)
        rc, out, err = self.run_cli("export", "7")
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out), config)
        self.assertEqual(self.fake.requests[-1].query["token"], OP_TOKEN)
        self.assertNotIn(OP_TOKEN, err)

    def test_a_failed_export_leaves_stdout_empty(self) -> None:
        """An empty TargetURL makes the guard skip its TargetURL check (STOP item 3): fail LOUDLY and print no JSON."""
        self.fake.route("POST", "/api/v1/auth/issuetoken/export", 200, {"Token": OP_TOKEN})
        rc, out, err = self.run_cli("export", "--backup-id", "7")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("export 7 failed 404", err)
        self.assertNotIn(OP_TOKEN, err)
        self.assertNotIn(OP_TOKEN, out)

    def test_a_failed_issuetoken_does_not_download_and_leaves_stdout_empty(self) -> None:
        """No operation token: do not call the export route (it would 400) and print nothing the guard could parse."""
        self.fake.route("GET", "/api/v1/backup/7/export", 200, {"Backup": {"TargetURL": TARGET}})
        rc, out, err = self.run_cli("export", "--backup-id", "7")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("export 7 failed 404", err)
        self.assertIn(("POST", "/api/v1/auth/issuetoken/export"), self.fake.paths())
        self.assertNotIn(("GET", "/api/v1/backup/7/export"), self.fake.paths())
        self.assertNotIn(FIXTURE_MARKER, err)

    def test_an_issuetoken_body_without_a_token_is_not_echoed(self) -> None:
        self.fake.route("POST", "/api/v1/auth/issuetoken/export", 200, {"Unexpected": OP_TOKEN})
        rc, out, err = self.run_cli("export", "7")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("no Token", err)
        self.assertNotIn(OP_TOKEN, err)
        self.assertNotIn(("GET", "/api/v1/backup/7/export"), self.fake.paths())

    def test_run_posts_and_reports_failure(self) -> None:
        self.fake.route("POST", "/api/v1/backup/7/run", 200, {"Status": "OK", "ID": 31})
        rc, out, _ = self.run_cli("run", "--backup-id", "7")
        self.assertEqual(rc, 0)
        self.assertIn("run backup 7: 200", out)
        self.fake.route("POST", "/api/v1/backup/7/run", 500, {"Error": "busy"})
        rc, out, err = self.run_cli("run", "7")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("run backup 7 failed 500", err)

    def test_delete_still_needs_yes_and_refuses_before_login(self) -> None:
        rc, _, err = self.run_cli("delete", "--backup-id", "7")
        self.assertEqual(rc, 1)
        self.assertIn("requires --yes", err)
        self.assert_nothing_sent()
        self.fake.route("DELETE", "/api/v1/backup/7", 200, {"Status": "OK"})
        rc, _, _ = self.run_cli("delete", "--backup-id", "7", "--yes", "--remote-files")
        self.assertEqual(rc, 0)
        self.assertEqual(self.fake.requests[-1].query, {"delete-remote-files": "true"})

    def test_log_keeps_the_line_the_retirement_gate_greps(self) -> None:
        message = json.dumps({"ParsedResult": "Success", "MainOperation": "Backup", "BeginTime": "2026-09-18T14:00:00Z"})
        self.fake.route("GET", "/api/v1/backup/7/log", 200, [{"ID": 9, "Message": message}])
        rc, out, _ = self.run_cli("log", "--backup-id", "7")
        self.assertEqual(rc, 0)
        self.assertIn('"ParsedResult": "Success"', out.splitlines()[0])
        self.assertEqual(self.fake.requests[-1].query, {"pagesize": "5"})

    def test_task_verbs_take_a_task_id_not_a_backup_id(self) -> None:
        for argv in (("abort",), ("abort", "x"), ("task",), ("abort", "12", "--backup-id", "7")):
            with self.subTest(argv=argv):
                rc, _, _ = self.run_cli(*argv)
                self.assertEqual(rc, api.EXIT_USAGE)
        self.assert_nothing_sent()
        self.fake.route("POST", "/api/v1/task/12/abort", 200, {})
        self.assertEqual(self.run_cli("abort", "12")[0], 0)
        self.assertEqual(self.run_cli("task", "13")[0], 1, "an unrouted task is a 404, which must exit 1")

    def test_import_reads_its_file_before_login(self) -> None:
        self.assertEqual(self.run_cli("import")[0], api.EXIT_USAGE)
        rc, _, err = self.run_cli("import", str(self.dir / "absent.json"))
        self.assertEqual(rc, 1)
        self.assertIn("cannot read", err)
        self.assert_nothing_sent()
        exported = self.dir / "job.json"
        exported.write_text(json.dumps({"Backup": {"Name": "Yamaguchi"}}), encoding="utf-8")
        self.fake.route("POST", "/api/v1/backups", 200, {"ID": "1"})
        self.assertEqual(self.run_cli("import", str(exported))[0], 0)
        self.assertEqual(self.fake.requests[-1].body, {"Backup": {"Name": "Yamaguchi"}})
        self.assertEqual(self.fake.requests[-1].query, {"temporary": "false"})


class CallerContractTest(_Cli):
    """The bash callers (retire_tier1/2, migrate_copy, narrow_bind, reboot_verify) grep `status` output."""

    def test_status_output_is_unchanged(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        self.fake.route("GET", "/api/v1/backups", 200, [{"Backup": {"ID": "7", "Name": "Yamaguchi", "TargetURL": TARGET}}])
        rc, out, _ = self.run_cli("status")
        self.assertEqual(rc, 0)
        self.assertIn('"ActiveTask": null', out)
        self.assertIn('"SchedulerQueueIds": []', out)
        self.assertIn(f"backup id=7 name='Yamaguchi' target={TARGET}", out)


class LoginAndTransportTest(_Cli):
    def test_a_rejected_login_exits_1_without_echoing_the_password(self) -> None:
        self.fake.route("POST", "/api/v1/auth/login", 401, {"Error": "Invalid password"})
        rc, out, err = self.run_cli("serverstate")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("FATAL: login failed (401)", err)
        self.assertEqual(self.fake.paths(), [LOGIN])

    def test_an_unsafe_credential_file_sends_nothing(self) -> None:
        os.chmod(self.cred, 0o640)  # group-readable is enough to be refused
        rc, out, err = self.run_cli("serverstate")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn("mode 0640", err)
        self.assert_nothing_sent()

    def test_an_unreachable_server_exits_1(self) -> None:
        def refuse(request, timeout=None):
            raise urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))

        with mock.patch("urllib.request.urlopen", refuse):
            rc, out, err = self.run_cli("serverstate")
        self.assertEqual((rc, out), (1, ""))
        self.assertIn(f"cannot reach {STUB_BASE}", err)

    def test_the_password_travels_only_as_the_login_body(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, state())
        self.fake.route("POST", "/api/v1/serverstate/pause", 200, {})
        self.fake.route("POST", "/api/v1/auth/issuetoken/export", 200, {"Token": OP_TOKEN})
        self.fake.route("GET", "/api/v1/backup/7/export", 200, {"Backup": {"ID": "7"}})
        for argv in (("serverstate",), ("pause",), ("export", "7")):
            self.run_cli(*argv)
        logins = [r for r in self.fake.requests if (r.method, r.path) == LOGIN]
        self.assertEqual(len(logins), 3)
        for r in self.fake.requests:
            self.assertNotIn(FIXTURE_MARKER, r.url)
            self.assertNotIn(FIXTURE_MARKER, json.dumps(r.headers))
            if (r.method, r.path) == LOGIN:
                self.assertEqual(r.body, {"Password": FIXTURE_MARKER, "RememberMe": False})
            else:
                self.assertNotIn(FIXTURE_MARKER, json.dumps(r.body))


class ScriptEntryTest(unittest.TestCase):
    """As a script: the sibling import resolves and the refusals happen before any network."""

    def run_script(self, *argv: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            env = RedactedEnv(os.environ)
            env[api.CRED_FILE_ENV] = str(Path(tmp) / "absent")  # a regression that logs in first fails here, unsent
            return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS, check=False)

    def test_help_lists_the_new_verbs(self) -> None:
        result = self.run_script("--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        for verb in ("serverstate", "pause", "resume"):
            self.assertIn(verb, result.stdout)

    def test_a_missing_job_id_exits_64_with_empty_stdout(self) -> None:
        """64, literally: argparse's own 2 would be indistinguishable from `serverstate` reading Paused."""
        result = self.run_script("export")
        self.assertEqual(result.returncode, 64, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("--backup-id", result.stderr)

    def test_pause_takes_no_job_id(self) -> None:
        result = self.run_script("pause", "2")
        self.assertEqual(result.returncode, 64, msg=result.stderr)
        self.assertIn("server-wide", result.stderr)

    def test_an_unknown_verb_is_a_usage_error_not_2(self) -> None:
        result = self.run_script("serverstat")
        self.assertEqual(result.returncode, 64, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
