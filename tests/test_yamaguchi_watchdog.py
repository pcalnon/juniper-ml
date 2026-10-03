#!/usr/bin/env python3
"""``util/ad-hoc/yamaguchi_watchdog.py``: the §7.6 checks, the mandatory job id, and its deploy path.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

YAM §8.22 recorded a 42.6 h outage that the watchdog could not see: the server sat ``Paused``
with the day's run queued, and the watchdog never looked at ``ProgramState``. The same section
found it anchored freshness on the newest log entry of ANY operation, so a Compact would reset
the backup clock. Design §7.6 adds both checks; B2 of the 2026-10-03 recovery plan makes the job
id mandatory, because the deployed unit took none and a rebuilt job is not id 2.

Pins, each able to fail for the reason it exists:

* ``Paused`` + a non-empty ``SchedulerQueueIds`` is ``ALERT PAUSED_WITH_QUEUE`` -- for any job,
  for a timed pause too -- while ``Paused`` with an empty queue (a startup-delay window) is not;
  an unreadable state is ``UNDETERMINED STATE_UNKNOWN``, never a silent pass;
* freshness comes from the newest **Backup**: a newer Compact does not refresh it, a newer
  successful Test does not hide a failed backup, and the log is keyset-paged (``offset=<ID>``)
  with a bounded budget that stops on a server that ignores ``offset``;
* the pre-B2 verdicts keep their codes and meaning (NO_RUNS, LOG_UNAVAILABLE, JOB_MISSING,
  RUNNING, STUCK, NOT_SUCCESS on the newest entry);
* ``--backup-id`` is required; an EMPTY one (the unit without its drop-in) leaves a durable
  ``JOB_MISSING`` record and sends nothing;
* the record line keeps ``<when> <verdict> <code> backup=<id> <details>`` on one line, and the
  notify-send child sees neither the password nor a variable carrying it;
* the unit hands the id over braced (one argv word) and the deploy script refuses, before touching
  the host, to deploy without one. The deploy script is checked statically and never executed.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``'s router.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, REPO_ROOT, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

wd = load_ad_hoc("yamaguchi_watchdog")
api = wd.api

UNIT = REPO_ROOT / "util" / "systemd" / "yamaguchi-watchdog.service"
DEPLOY = AD_HOC / "yamaguchi_watchdog_deploy.bash"
ZERO_DATE = "0001-01-01T00:00:00Z"
JOB = "7"


def ago(hours: float) -> str:
    """A Duplicati-shaped UTC stamp: seven fractional digits, as .NET writes them."""
    when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    return when.strftime("%Y-%m-%dT%H:%M:%S.") + "1234567Z"


def entry(entry_id: int, operation: str, result: str, hours: float) -> dict:
    message = {"MainOperation": operation, "ParsedResult": result, "BeginTime": ago(hours)}
    return {"ID": entry_id, "Type": "Result", "Message": json.dumps(message)}


def server_state(program="Running", queue=None, end=ZERO_DATE, active=None) -> dict:
    return {"ProgramState": program, "SchedulerQueueIds": [] if queue is None else queue, "EstimatedPauseEnd": end, "ActiveTask": active}


class _Watchdog(unittest.TestCase):
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
            mock.patch.object(api, "BASE", STUB_BASE),  # check() assigns it; this restores it
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.serve()

    def serve(self, state: dict | None = None, backups: list | None = None, log: list | None = None, log_status: int = 200) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, server_state() if state is None else state)
        self.fake.route("GET", "/api/v1/backups", 200, [{"Backup": {"ID": JOB, "Name": "Yamaguchi"}}] if backups is None else backups)
        entries = [entry(10, "Backup", "Success", 2.0)] if log is None else log

        def page(query: dict) -> tuple[int, object]:
            if log_status != 200:
                return log_status, {"Error": "log unavailable"}
            size = int(query["pagesize"])
            start = 0
            if "offset" in query:
                ids = [e["ID"] for e in entries]
                start = ids.index(int(query["offset"])) + 1
            return 200, entries[start : start + size]

        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=page)

    def args(self, **overrides) -> argparse.Namespace:
        values = {"base": STUB_BASE, "backup_id": JOB, "max_age_hours": 26.0, "max_run_hours": 6.0, "state_dir": str(self.state_dir), "notify": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def check(self, **overrides) -> tuple[str, str, str]:
        verdict, code, details = wd.check(self.args(**overrides))
        self.assertNotIn(FIXTURE_MARKER, details)
        return verdict, code, details

    def log_requests(self) -> list:
        return [r for r in self.fake.requests if r.path == f"/api/v1/backup/{JOB}/log"]


class ProgramStateTest(_Watchdog):
    def test_a_fresh_successful_backup_reads_ok(self) -> None:
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("OK", "OK"))
        self.assertIn("newest backup", details)
        self.assertIn("age=2.0h", details)

    def test_paused_with_a_queued_run_alerts(self) -> None:
        self.serve(state=server_state("Paused", [{"Item1": 3, "Item2": JOB}]))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "PAUSED_WITH_QUEUE"))
        self.assertIn("pause=indefinite", details)
        self.assertIn('"Item2": "7"', details)
        self.assertEqual(self.log_requests(), [], "a held run is judged before the log, which would only look old")

    def test_any_queued_job_counts(self) -> None:
        self.serve(state=server_state("Paused", [{"Item1": 4, "Item2": "9"}]))
        self.assertEqual(self.check()[:2], ("ALERT", "PAUSED_WITH_QUEUE"))

    def test_a_timed_pause_holding_a_run_still_alerts(self) -> None:
        """YAM §8.22.2: always a fault, whatever the uptime."""
        self.serve(state=server_state("Paused", [{"Item1": 5, "Item2": JOB}], end="2026-10-03T15:30:00Z"))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "PAUSED_WITH_QUEUE"))
        self.assertIn("pause=until 2026-10-03T15:30:00Z", details)

    def test_paused_with_an_empty_queue_is_named_but_not_an_alert(self) -> None:
        self.serve(state=server_state("Paused", [], end="2026-10-03T15:30:00Z"))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("OK", "OK"))
        self.assertIn("ProgramState=Paused", details)

    def test_an_unreadable_state_is_undetermined_not_a_pass(self) -> None:
        states: list[dict] = [{"SchedulerQueueIds": []}, server_state("Suspended"), {"ProgramState": "Paused", "SchedulerQueueIds": None}]
        for state in states:
            with self.subTest(state=state):
                self.serve(state=state)
                self.assertEqual(self.check()[:2], ("UNDETERMINED", "STATE_UNKNOWN"))


class BackupFreshnessTest(_Watchdog):
    def test_a_newer_compact_does_not_refresh_the_backup_clock(self) -> None:
        """YAM §8.22.3 gap 2: the pre-B2 check read the Compact's age (1 h) and said OK."""
        self.serve(log=[entry(11, "Compact", "Success", 1.0), entry(10, "Backup", "Success", 30.0)])
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("age=30.0h", details)
        self.assertIn("newest log entry: Compact", details)
        self.assertEqual(self.check(max_age_hours=48.0)[:2], ("OK", "OK"), "control: the alert is the backup's age")

    def test_a_newer_successful_test_does_not_hide_a_failed_backup(self) -> None:
        self.serve(log=[entry(11, "Test", "Success", 1.0), entry(10, "Backup", "Error", 5.0)])
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "NOT_SUCCESS"))
        self.assertIn("ParsedResult=Error", details)

    def test_a_failed_newest_entry_of_any_operation_still_alerts(self) -> None:
        self.serve(log=[entry(11, "Compact", "Warning", 1.0), entry(10, "Backup", "Success", 3.0)])
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "NOT_SUCCESS"))
        self.assertIn("Compact", details)

    def test_the_log_is_keyset_paged_to_the_newest_backup(self) -> None:
        tests = [entry(i, "Test", "Success", 0.5) for i in range(100, 75, -1)]  # IDs 100..76
        self.serve(log=[*tests, entry(75, "Backup", "Success", 3.0)])
        self.assertEqual(self.check()[:2], ("OK", "OK"))
        queries = [r.query for r in self.log_requests()]
        self.assertEqual(queries, [{"pagesize": "20"}, {"pagesize": "20", "offset": "81"}])

    def test_a_server_that_ignores_offset_ends_the_scan(self) -> None:
        first_page = [entry(i, "Test", "Success", 0.5) for i in range(100, 80, -1)]
        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=lambda query: (200, first_page))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertIn("no Backup operation among the newest 20 log entries", details)
        self.assertEqual(len(self.log_requests()), 2)

    def test_the_page_budget_is_bounded(self) -> None:
        counter = iter(range(10**6, 0, -1))
        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=lambda query: (200, [entry(next(counter), "Test", "Success", 0.5) for _ in range(20)]))
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "STALE"))
        self.assertEqual(len(self.log_requests()), wd.LOG_MAX_PAGES)
        self.assertIn(f"newest {wd.LOG_MAX_PAGES * wd.LOG_PAGE_SIZE} log entries", details)

    def test_preserved_verdicts(self) -> None:
        self.serve(log=[])
        self.assertEqual(self.check()[:2], ("ALERT", "NO_RUNS"))
        self.serve(log_status=500)
        self.assertEqual(self.check()[:2], ("UNDETERMINED", "LOG_UNAVAILABLE"))
        self.serve(log=[{"ID": 3, "Message": "an old-format, non-JSON entry"}])
        self.assertEqual(self.check()[:2], ("UNDETERMINED", "LOG_UNAVAILABLE"))
        self.serve(backups=[{"Backup": {"ID": "1", "Name": "Yamaguchi"}}])
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "JOB_MISSING"))
        self.assertIn("backup id 7 not in server list ['1']", details)

    def test_running_and_stuck_are_preserved(self) -> None:
        self.serve(state=server_state(active={"Item1": 5, "Item2": JOB}))
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": ago(1.0)})
        self.assertEqual(self.check()[:2], ("OK", "RUNNING"))
        self.fake.route("GET", "/api/v1/task/5", 200, {"TaskStarted": ago(7.0)})
        self.assertEqual(self.check()[:2], ("ALERT", "STUCK"))


class CredentialAndIdTest(_Watchdog):
    def test_an_invalid_id_alerts_without_contacting_the_server(self) -> None:
        with mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.dir / "absent")}):
            for bad in ("", "abc", "0", "7\n", "2/../serverstate"):
                with self.subTest(backup_id=bad):
                    verdict, code, details = self.check(backup_id=bad)
                    self.assertEqual((verdict, code), ("ALERT", "JOB_MISSING"))
                    self.assertIn("yamaguchi_watchdog_deploy.bash --backup-id", details)
        self.assertEqual(self.fake.requests, [])

    def test_an_unsafe_credential_reads_unreachable_and_sends_nothing(self) -> None:
        os.chmod(self.cred, 0o640)  # group-readable is enough to be refused
        verdict, code, details = self.check()
        self.assertEqual((verdict, code), ("ALERT", "UNREACHABLE"))
        self.assertIn("mode 0640", details)
        self.assertEqual(self.fake.requests, [])


class MainAndRecordTest(_Watchdog):
    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = wd.main(list(argv))
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
        self.assertNotIn(FIXTURE_MARKER, out.getvalue() + err.getvalue())
        return rc, out.getvalue(), err.getvalue()

    def read_state(self, name: str) -> list[str]:
        path = self.state_dir / name
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def test_backup_id_is_required(self) -> None:
        rc, _, err = self.run_main("--state-dir", str(self.state_dir), "--no-notify")
        self.assertEqual(rc, 2)
        self.assertIn("--backup-id", err)
        self.assertFalse(self.state_dir.exists(), "a usage error writes no record")
        self.assertEqual(self.fake.requests, [])

    def test_the_unit_without_its_drop_in_leaves_a_durable_record(self) -> None:
        """systemd expands an unset ${YAMAGUCHI_BACKUP_ID} to ONE empty argument."""
        rc, out, _ = self.run_main("--backup-id", "", "--state-dir", str(self.state_dir), "--no-notify")
        self.assertEqual(rc, 1)
        status = self.read_state("server-watchdog.status")
        self.assertEqual(len(status), 1)
        self.assertRegex(status[0], r"^\S+ ALERT JOB_MISSING backup=INVALID --backup-id is not a job id")
        self.assertEqual(len(self.read_state("server-watchdog.log")), 1)
        self.assertEqual(len(self.read_state("server-failures.log")), 1)
        self.assertEqual(out.strip(), status[0])
        self.assertEqual(self.fake.requests, [])

    def test_the_record_line_format_is_unchanged(self) -> None:
        rc, _, _ = self.run_main("--backup-id", JOB, "--base", STUB_BASE, "--state-dir", str(self.state_dir), "--no-notify")
        self.assertEqual(rc, 0)
        (line,) = self.read_state("server-watchdog.status")
        match = re.match(r"^(\S+) OK OK backup=7 newest backup ", line)
        self.assertIsNotNone(match, line)
        assert match is not None
        # yamaguchi_reboot_verify.bash reads field 1 with `date -d`; it must stay a full timestamp.
        dt.datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(self.read_state("server-failures.log"), [], "an OK is not a failure record")

    def test_details_are_flattened_to_one_line(self) -> None:
        line = wd.record(self.args(), "ALERT", "EXCEPTION", "first\nsecond\rthird")
        self.assertNotIn("\n", line)
        self.assertEqual(len(self.read_state("server-watchdog.log")), 1)

    def test_the_notify_child_gets_no_password(self) -> None:
        bindir = self.dir / "bin"
        bindir.mkdir()
        trace = self.dir / "notify-send.json"
        stub = bindir / "notify-send"
        # The stub judges its own argv and environment and records booleans and variable NAMES
        # only: a raw `env` dump would put the developer's real environment into a failure message.
        stub.write_text(
            textwrap.dedent(f"""\
                #!{sys.executable}
                import json, os, sys
                marker = {FIXTURE_MARKER!r}
                seen = {{
                    "argv": sys.argv[1:],
                    "argv_has_marker": any(marker in a for a in sys.argv),
                    "env_has_marker": any(marker in v for v in os.environ.values()),
                    "duplicati_names": sorted(n for n in os.environ if "DUPLICATI" in n),
                }}
                with open({str(trace)!r}, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(seen) + "\\n")
                """),
            encoding="utf-8",
        )
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.serve(state=server_state("Paused", [{"Item1": 3, "Item2": JOB}]))
        with mock.patch.dict(os.environ, {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}):
            rc, out, _ = self.run_main("--backup-id", JOB, "--base", STUB_BASE, "--state-dir", str(self.state_dir))
        self.assertEqual(rc, 1)
        self.assertIn("[notify-send rc=0]", out)
        (seen,) = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any("PAUSED_WITH_QUEUE" in a for a in seen["argv"]), "control: the stub really ran with the alert")
        self.assertFalse(seen["argv_has_marker"])
        self.assertFalse(seen["env_has_marker"])
        self.assertNotIn(api.CRED_KEY, seen["duplicati_names"], "the password is never exported under its key name")


class UnitAndDeployContractTest(unittest.TestCase):
    """Static only: the deploy script changes systemd user units, so no test executes it."""

    unit: str
    deploy: str
    deploy_lines: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.unit = UNIT.read_text(encoding="utf-8")
        cls.deploy = DEPLOY.read_text(encoding="utf-8")
        cls.deploy_lines = cls.deploy.splitlines()

    def first_line(self, predicate) -> int:
        for number, line in enumerate(self.deploy_lines):
            if predicate(line.strip()):
                return number
        raise AssertionError("no matching line in the deploy script")

    def test_the_unit_passes_the_id_as_one_braced_word(self) -> None:
        exec_lines = [line for line in self.unit.splitlines() if line.startswith("ExecStart=")]
        self.assertEqual(len(exec_lines), 1)
        self.assertTrue(exec_lines[0].endswith("/util/ad-hoc/yamaguchi_watchdog.py --backup-id ${YAMAGUCHI_BACKUP_ID}"), exec_lines[0])
        self.assertNotIn("from the repo .env", self.unit)
        self.assertIn("web-credential", self.unit)

    def test_the_deploy_script_parses(self) -> None:
        result = subprocess.run(["bash", "-n", str(DEPLOY)], capture_output=True, text=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_the_id_is_refused_before_the_host_is_touched(self) -> None:
        required = self.first_line(lambda s: "--backup-id is required" in s)
        validated = self.first_line(lambda s: "^[1-9][0-9]*$" in s)
        host = self.first_line(lambda s: re.match(r"^(if \[ ! -f|if ! grep|linger=\$\(loginctl|install |systemctl |printf .*>)", s) is not None)
        self.assertLess(required, host)
        self.assertLess(validated, host)
        self.assertIn("exit 2", "\n".join(self.deploy_lines[required : required + 3]))

    def test_there_is_no_default_id(self) -> None:
        self.assertIn('BACKUP_ID=""', self.deploy)
        self.assertNotRegex(self.deploy, r"BACKUP_ID=['\"]?[0-9]")
        self.assertNotIn(":-2}", self.deploy)

    def test_the_drop_in_sets_the_variable_the_unit_reads(self) -> None:
        variable = re.search(r"\$\{([A-Z_]+)\}\s*$", [line for line in self.unit.splitlines() if line.startswith("ExecStart=")][0])
        assert variable is not None
        self.assertIn(f"Environment={variable.group(1)}=%s", self.deploy)
        self.assertIn('DROPIN_DIR="$UNIT_DIR/yamaguchi-watchdog.service.d"', self.deploy)
        self.assertIn("backup-id.conf", self.deploy)

    def test_a_stale_primary_unit_is_refused_before_install(self) -> None:
        guard = self.first_line(lambda s: s.startswith("if ! grep -qF -- '--backup-id ${YAMAGUCHI_BACKUP_ID}'"))
        install = self.first_line(lambda s: s.startswith("install -m 0644"))
        self.assertLess(guard, install)


if __name__ == "__main__":
    unittest.main()
