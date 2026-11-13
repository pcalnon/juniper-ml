#!/usr/bin/env python3
"""``util/ad-hoc/yamaguchi_acceptance_probe.py``: one verdict line per acceptance criterion, from fixed predicates.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

The backup design's acceptance criteria (section 9) were checked, through the Phase D sitting, by command blocks
written for one use. Four of those blocks were wrong in ways the probe's rules now exclude, and each rule has its
tests here:

1. **A marker is pinned against the code that writes it** (the sitting counted a log line the wrapper never writes).
   The watchdog-line parser is fed what ``yamaguchi_watchdog.record`` really writes; the snapshot's ``source :``
   pattern is matched against the script's own f-string, rendered from its source; the snapshot source path is the
   script's ``SRC``; note AC-12a's accepted set is read back from the design document.
2. **A time window is inclusive at its edge and tested at the edge** (a ``--since`` cut excluded the start it was
   for). Exactly 24 h of uptime, exactly 24 h after a dlist's write, exactly the exposure gate, exactly the count
   tolerance, a journal record exactly at the enable instant, a start exactly at the schedule slack.
3. **A warning is classified by its tag, never by its text** (a filter matched ``http`` and ``report`` in path text
   and mislabelled three file warnings). The text is consulted only for the ruled path scope, after the tag decided.
4. **An empty or unparseable input is ERROR, never PASS** (a parser met a BOM and reported 0 entries). An empty log,
   journal, listing, row set or export each has a case, and so does a BOM in front of each.

A fifth property is checked end to end: the probe never prints or stores a warning's text, a URL, the credential or
an option value outside its allow-list. No server is contacted (``tests/duplicati_api_stub.py``), no host command is
run (the collectors are replaced), and every file is in a temporary directory.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import io
import json
import os
import pwd
import stat
import subprocess
import tempfile
import unittest
import unittest.mock as mock
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, REPO_ROOT, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

probe = load_ad_hoc("yamaguchi_acceptance_probe")
api = probe.api
watchdog = load_ad_hoc("yamaguchi_watchdog")

UTC = dt.timezone.utc
JOB = "2"
NOW = dt.datetime(2026, 11, 12, 1, 0, 0, tzinfo=UTC)
HOME = "/srv/fixture-home/"
FIREFOX = HOME + ".mozilla/firefox/abc123.default-release/"
SCOPE = [HOME + probe.ALLOWED_WARNING_SCOPE]
# Values that must never reach a summary, a fact, stdout or a written file. None is a real secret.
URL_MARKER = "https://reports.invalid/hook?bearer=withheld-url-marker"
PATH_MARKER = "places-withheld-path-marker.sqlite"
VALUE_MARKER = "withheld-option-value-marker"
TAG_PREFIX = "Duplicati.Library.Main.Operation.Backup."
DESIGN = REPO_ROOT / "notes" / "JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md"
SNAPSHOT_SCRIPT = AD_HOC / "yamaguchi_server_db_snapshot.py"


# --- fixtures ---------------------------------------------------------------------------------------------------------
def unit_props(**overrides) -> dict:
    props = {"FragmentPath": "/etc/systemd/system/duplicati.service", "User": "duplicati", "ActiveState": "active", "SubState": "running", "NeedDaemonReload": "no", "NRestarts": "0", "ActiveEnterTimestamp": f"@{int((NOW - dt.timedelta(hours=111)).timestamp())}"}
    props.update(overrides)
    return props


def export(*, retention: str | None = None, drop: tuple[str, ...] = (), extra: dict | None = None, **backup_overrides) -> dict:
    values = {
        "allow-missing-source": "true",
        "asynchronous-upload-limit": "2",
        "blocksize": "1MB",
        "compression-module": "zip",
        "dblock-size": "500MB",
        "encryption-module": "aes",
        "no-auto-compact": "true",
        "tempdir": "/home/duplicati/.cache/duplicati-tmp",
        "run-script-before-required": probe.GUARD_PATH,
        "aes-version": "2",
        "send-http-url": URL_MARKER,
        "http-report-status-url": URL_MARKER,
    }
    if retention is not None:
        values["retention-policy"] = retention
    values.update(extra or {})
    settings = [{"Filter": "", "Name": ("--" if i % 2 else "") + name, "Value": value, "Argument": None} for i, (name, value) in enumerate(values.items()) if name not in drop]
    backup = {"ID": JOB, "Name": "Yamaguchi", "TargetURL": probe.EXPECTED_TARGET + "/", "DBPath": "/x/job.sqlite", "Sources": ["/srv/a/", "/srv/b.vdi"], "Filters": [{"Order": i, "Include": False, "Expression": f"/x{i}/"} for i in range(45)], "Settings": settings, "Metadata": {}}
    backup.update(backup_overrides)
    return {"CreatedByVersion": "2.4.0.0", "Schedule": {"ID": 1, "Time": "2026-09-17T14:00:00Z", "Repeat": "1D", "LastRun": "2026-11-11T14:00:00Z"}, "Backup": backup}


def watchdog_line(when: dt.datetime, verdict: str = "OK", code: str = "OK", backup: str = JOB, details: str = "newest backup 2026-11-08T14:00:00.1924253Z ParsedResult=Success age=4.0h") -> str:
    return f"{when.strftime('%Y-%m-%dT%H:%M:%S%z')} {verdict} {code} backup={backup} {details}"


CST = dt.timezone(dt.timedelta(hours=-6))


def noon(day: int) -> dt.datetime:
    return dt.datetime(2026, 11, day, 12, 0, 39, tzinfo=CST)


def journal(records: list[tuple[dt.datetime, str | None, str | None, str]]) -> str:
    return "".join(json.dumps({"__REALTIME_TIMESTAMP": str(int(when.timestamp() * 1e6)), "JOB_TYPE": job_type, "JOB_RESULT": result, "MESSAGE": message, "SYSLOG_IDENTIFIER": "x"}) + "\n" for when, job_type, result, message in records)


def snapshot_run(when: dt.datetime, source: str = probe.SNAPSHOT_SOURCE, result: str = "done") -> list[tuple[dt.datetime, str | None, str | None, str]]:
    return [
        (when, "start", None, "Starting yamaguchi-server-db-snapshot.service - Snapshot the Duplicati server DB..."),
        (when, None, None, f"source      : {source} (596.0 KiB)"),
        (when, None, None, "integrity   : ok (16 tables)"),
        (when + dt.timedelta(seconds=1), "start", result, "Finished yamaguchi-server-db-snapshot.service."),
    ]


def fire(day: int, second: int = 26) -> dt.datetime:
    return dt.datetime(2026, 11, day, 13, 45, second, tzinfo=UTC)


def four_days() -> str:
    return journal(snapshot_run(dt.datetime(2026, 11, 8, 19, 57, 32, tzinfo=UTC)) + snapshot_run(fire(9)) + snapshot_run(fire(10)) + snapshot_run(fire(11)))


def snapshot_file(when: dt.datetime | None = None, **overrides) -> dict:
    snapshot = {"size": 610304, "mtime": ((when or fire(11)) + dt.timedelta(seconds=1)).timestamp(), "mode": 0o600, "owner": "operator"}
    snapshot.update(overrides)
    return snapshot


def volume(name: str, *, owner: str = "operator", mode: int = 0o770, size: int = 1000, written: dt.datetime | None = None) -> dict:
    return {"name": name, "size": size, "mtime": (written or NOW - dt.timedelta(hours=7)).timestamp(), "mode": mode, "owner": owner, "group": "duplicati"}


def destination(newest_owner: str = "operator", newest_written: dt.datetime | None = None) -> list[dict]:
    entries = [volume(f"duplicati-b{i:04d}.dblock.zip.aes") for i in range(4)] + [volume(f"duplicati-i{i:04d}.dindex.zip.aes") for i in range(4)]
    entries += [volume("duplicati-20261110T140000Z.dlist.zip.aes"), volume("duplicati-20261111T140001Z.dlist.zip.aes", owner=newest_owner, mode=0o640, written=newest_written)]
    return entries


def all_synced(entries: list[dict], **overrides) -> dict:
    statuses = {e["name"]: "up to date" for e in entries}
    statuses.update(overrides)
    return statuses


def security_rows(extra_unset: tuple[str, ...] = (), drop_unset: tuple[str, ...] = ()) -> list[dict]:
    unset = (set(probe.ACCEPTED_UNSET) | set(extra_unset)) - set(drop_unset)
    names = sorted(unset) + [f"ProtectSomething{i}=" for i in range(66)]
    return [{"set": name not in unset, "name": name, "json_field": name.strip("="), "description": "x", "exposure": None if name not in unset else "0.1"} for name in names]


def overall_line(exposure: str = "1.7") -> str:
    return f"  NAME   DESCRIPTION   EXPOSURE\n\n→ Overall exposure level for duplicati.service: {exposure} OK \U0001f642\n"


def warning(key: str, path: str, verb: str = "Failed to process path") -> str:
    tag, _, message_id = key.rpartition("-")
    return f"2026-11-10 08:01:30 -06 - [Warning-{TAG_PREFIX}{tag}-{message_id}]: {verb}: {path}"


FIREFOX_WARNINGS = [
    warning("FilePreFilterProcess.FileEntry-PathNotFound", FIREFOX + PATH_MARKER),
    warning("MetadataGenerator.Metadata-MetadataProcessFailed", FIREFOX + PATH_MARKER, "Failed to process metadata for"),
    warning("FileBlockProcessor.FileEntry-PathNotFound", FIREFOX + PATH_MARKER),
]


def result_message(*, operation: str = "Backup", result: str = "Success", begin: dt.datetime | None = None, minutes: int = 50, examined: int = 2_000_000, examined_bytes: int = probe.BASELINE_BYTES, warnings: list | None = None, errors: list | None = None, drop: tuple[str, ...] = (), fraction: str = "1973595", **overrides) -> dict:
    """A run result as the job log stores it. `fraction` is the seven sub-second places .NET writes; the edge tests zero it."""
    begin = begin or dt.datetime(2026, 11, 11, 14, 0, 1, tzinfo=UTC)
    message = {
        "MainOperation": operation,
        "ParsedResult": result,
        "BeginTime": begin.strftime("%Y-%m-%dT%H:%M:%S.") + fraction + "Z",
        "EndTime": (begin + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S.") + fraction + "Z",
        "ExaminedFiles": examined,
        "SizeOfExaminedFiles": examined_bytes,
        "AddedFiles": 100,
        "ModifiedFiles": 10,
        "DeletedFiles": 1,
        "NotProcessedFiles": 0,
        "FilesWithError": 0,
        "PartialBackup": False,
        "Interrupted": False,
        "Warnings": warnings or [],
        "WarningsActualLength": len(warnings or []),
        "Errors": errors or [],
        "ErrorsActualLength": len(errors or []),
        "DeleteResults": None,
        "CompactResults": None,
        "TestResults": {"ParsedResult": "Success", "VerificationsActualLength": 3},
    }
    message.update(overrides)
    for key in drop:
        del message[key]
    return message


def log_entry(entry_id: int, **kwargs) -> dict:
    return {"ID": entry_id, "Type": "Result", "Message": json.dumps(result_message(**kwargs))}


def summarized(**kwargs) -> dict:
    return probe.summarize_entry(log_entry(1, **kwargs), SCOPE)


def never_leaks(test: unittest.TestCase, *texts: str) -> None:
    for text in texts:
        for marker in (URL_MARKER, "withheld-url-marker", PATH_MARKER, VALUE_MARKER, FIXTURE_MARKER, probe.EXPECTED_TARGET):
            test.assertNotIn(marker, text)


# --- small parsers ----------------------------------------------------------------------------------------------------
class ParserTest(unittest.TestCase):
    def test_dotnet_and_iso_stamps(self) -> None:
        expected = dt.datetime(2026, 11, 10, 14, 0, 0, 197359, tzinfo=UTC)
        self.assertEqual(probe.parse_iso("2026-11-10T14:00:00.1973595Z"), expected)
        self.assertEqual(probe.parse_iso("2026-11-10T08:00:00.1973595-06:00"), expected)
        self.assertEqual(probe.parse_iso("2026-09-17T14:00:00Z"), dt.datetime(2026, 9, 17, 14, 0, tzinfo=UTC))
        self.assertEqual(probe.parse_iso("2026-09-17T14:00:00"), dt.datetime(2026, 9, 17, 14, 0, tzinfo=UTC), "a naive stamp is read as UTC")
        for junk in (None, "", "   ", "yesterday", 5, "0001-99-99"):
            self.assertIsNone(probe.parse_iso(junk))

    def test_systemctl_properties_and_unix_stamps(self) -> None:
        props = probe.parse_properties("\ufeffActiveState=active\n\nExecStart={ path=/x ; argv[]=/x a=b }\nnot a property\n=orphan\nNRestarts=0\n")
        self.assertEqual(props, {"ActiveState": "active", "ExecStart": "{ path=/x ; argv[]=/x a=b }", "NRestarts": "0"})
        self.assertEqual(probe.parse_properties(""), {})
        self.assertEqual(probe.unix_property("@1794043744"), dt.datetime.fromtimestamp(1794043744, UTC))
        for unset in (None, "", "n/a", "@0", "0", "Sat 2026-11-07 03:29:04 CST"):
            self.assertIsNone(probe.unix_property(unset))

    def test_percent_guards_its_inputs(self) -> None:
        self.assertAlmostEqual(probe.percent(110, 100), 0.10)
        for new, old in ((None, 100), (100, None), (100, 0), (True, 100), ("110", 100), (100, -5)):
            self.assertIsNone(probe.percent(new, old))


# --- AC-1 -------------------------------------------------------------------------------------------------------------
class Ac1Test(unittest.TestCase):
    def test_the_recovered_unit_passes(self) -> None:
        finding = probe.judge_ac1(unit_props(), NOW)
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("up 111.0 h", finding.summary)

    def test_each_property_fails_by_name(self) -> None:
        for key, bad in (("FragmentPath", "/usr/lib/systemd/system/duplicati.service"), ("User", "root"), ("ActiveState", "failed"), ("SubState", "exited"), ("NeedDaemonReload", "yes"), ("NRestarts", "1")):
            with self.subTest(prop=key):
                finding = probe.judge_ac1(unit_props(**{key: bad}), NOW)
                self.assertEqual(finding.verdict, "FAIL")
                self.assertIn(f"{key}={bad}", finding.summary)

    def test_exactly_24_hours_is_over_24_hours(self) -> None:
        at = probe.judge_ac1(unit_props(ActiveEnterTimestamp=f"@{int((NOW - dt.timedelta(hours=24)).timestamp())}"), NOW)
        short = probe.judge_ac1(unit_props(ActiveEnterTimestamp=f"@{int((NOW - dt.timedelta(hours=24)).timestamp()) + 1}"), NOW)
        self.assertEqual((at.verdict, short.verdict), ("PASS", "PENDING"))
        self.assertIn("of the 24 h", short.summary)

    def test_no_evidence_is_not_a_pass(self) -> None:
        self.assertEqual(probe.judge_ac1({}, NOW).verdict, "ERROR")
        self.assertEqual(probe.judge_ac1(unit_props(ActiveEnterTimestamp=""), NOW).verdict, "FAIL")
        absent = unit_props()
        del absent["NRestarts"]
        self.assertIn("NRestarts=<absent>", probe.judge_ac1(absent, NOW).summary)


# --- the export: AC-2, AC-13, OPTIONS ---------------------------------------------------------------------------------
class ExportTest(unittest.TestCase):
    def test_ac2_passes_on_the_job_as_recorded(self) -> None:
        finding = probe.judge_ac2(export())
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("sources=2 filters=45 repeat=1D at 14:00:00Z (anchor date 2026-09-17) blocksize=1MB", finding.summary)

    def test_ac2_fails_for_each_deviation(self) -> None:
        cases = {
            "job name": export(Name="Other"),
            "TargetURL": export(TargetURL="file:///mnt/elsewhere/"),
            "1 sources": export(Sources=["/srv/a/"]),
            "44 filters": export(Filters=[{}] * 44),
            "blocksize": export(extra={"blocksize": "100KB"}),
            "None filters": export(Filters=None),
        }
        for needle, doc in cases.items():
            with self.subTest(case=needle):
                finding = probe.judge_ac2(doc)
                self.assertEqual(finding.verdict, "FAIL")
                self.assertIn(needle, finding.summary)
        repeat, moved = export(), export()
        repeat["Schedule"]["Repeat"] = "1W"
        moved["Schedule"]["Time"] = "2026-09-17T14:00:01Z"
        self.assertIn("Repeat='1W'", probe.judge_ac2(repeat).summary)
        self.assertIn("time of day is 14:00:01", probe.judge_ac2(moved).summary)

    def test_ac2_tolerates_what_the_ui_changes_harmlessly(self) -> None:
        doc = export(TargetURL=probe.EXPECTED_TARGET, extra={"blocksize": "1mb"})
        doc["Schedule"]["Time"] = "2026-09-18T14:00:00Z"  # the B3 save moved the anchor DATE; the time of day is what runs
        finding = probe.judge_ac2(doc)
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("anchor date 2026-09-18", finding.summary)

    def test_ac13_wants_the_guard_and_nothing_else(self) -> None:
        self.assertEqual(probe.judge_ac13(export()).verdict, "PASS")
        elsewhere = probe.judge_ac13(export(extra={"run-script-before-required": "/home/duplicati/x.sh"}))
        self.assertEqual(elsewhere.verdict, "FAIL")
        self.assertIn("/home/duplicati/x.sh", elsewhere.summary, "where the option points is the finding")
        second = probe.judge_ac13(export(extra={"run-script-after": "/usr/local/bin/notify"}))
        self.assertEqual(second.verdict, "FAIL")
        self.assertIn("run-script-after", second.summary)
        self.assertEqual(probe.judge_ac13(export(drop=("run-script-before-required",))).verdict, "FAIL")
        twice = export()
        twice["Backup"]["Settings"].append({"Name": "--run-script-before-required", "Value": probe.GUARD_PATH})
        self.assertEqual(probe.judge_ac13(twice).verdict, "FAIL")

    def test_options_pass_suspended_and_restored(self) -> None:
        suspended = probe.judge_options(export())
        self.assertEqual(suspended.verdict, "PASS")
        self.assertIn("12 option names", suspended.summary)
        self.assertIn("retention suspended", suspended.summary)
        restored = probe.judge_options(export(retention=probe.RULED_RETENTION), "restored")
        self.assertEqual(restored.verdict, "PASS")
        self.assertIn("13 option names", restored.summary)
        self.assertEqual(probe.retention_state(export()), "suspended")
        self.assertEqual(probe.retention_state(export(retention="x")), "restored")
        self.assertIsNone(probe.retention_state({}))

    def test_options_fail_for_each_deviation(self) -> None:
        cases = {
            "is not the ruled": (export(retention="1W:1D,1M:1W,1Y:1M,3Y:2M"), "either"),
            "retention is suspended, expected restored": (export(), "restored"),
            "retention is restored, expected suspended": (export(retention=probe.RULED_RETENTION), "suspended"),
            "keep-time=2Y is set": (export(extra={"keep-time": "2Y"}), "either"),
            "keep-versions=5 is set": (export(extra={"keep-versions": "5"}), "either"),
            "not in the recorded set: dry-run": (export(extra={"dry-run": "true"}), "either"),
            "now absent: no-auto-compact": (export(drop=("no-auto-compact",)), "either"),
            "tempdir=/home/other/.cache/duplicati-tmp (want": (export(extra={"tempdir": "/home/other/.cache/duplicati-tmp"}), "either"),
            "aes-version=3 (want 2)": (export(extra={"aes-version": "3"}), "either"),
            "no-auto-compact=false (want true)": (export(extra={"no-auto-compact": "false"}), "either"),
        }
        for needle, (doc, expectation) in cases.items():
            with self.subTest(case=needle):
                finding = probe.judge_options(doc, expectation)
                self.assertEqual(finding.verdict, "FAIL")
                self.assertIn(needle, finding.summary)
        twice = export()
        twice["Backup"]["Settings"].append({"Name": "blocksize", "Value": "1MB"})
        self.assertIn("set more than once: blocksize", probe.judge_options(twice).summary)

    def test_a_non_export_is_an_error_for_all_three(self) -> None:
        docs: list[object] = [{}, None, [], {"Backup": {}}, {"Backup": {"Settings": None}}, {"error": "x"}]
        for doc in docs:
            with self.subTest(doc=doc):
                self.assertEqual([judge(doc).verdict for judge in (probe.judge_ac2, probe.judge_ac13, probe.judge_options)], ["ERROR"] * 3)

    def test_no_url_and_no_value_outside_the_allow_list_is_ever_shown(self) -> None:
        doc = export(TargetURL=URL_MARKER, extra={"surprise-option": VALUE_MARKER, "compression-module": VALUE_MARKER, "passphrase": VALUE_MARKER})
        for judge in (probe.judge_ac2, probe.judge_ac13, probe.judge_options):
            finding = judge(doc)
            never_leaks(self, finding.summary, json.dumps(finding.as_dict()))
        named = probe.judge_options(doc)
        self.assertIn("surprise-option", named.summary, "the NAME of an unexpected option is the finding")
        self.assertIn("passphrase", named.summary)
        self.assertEqual(probe.shown("send-http-url", [URL_MARKER]), "send-http-url (value withheld)")
        self.assertTrue({"send-http-url", "http-report-status-url", "passphrase"}.isdisjoint(probe.PRINTABLE_VALUES))


# --- AC-5 -------------------------------------------------------------------------------------------------------------
class Ac5Test(unittest.TestCase):
    def judge(self, lines: list[str], now: dt.datetime | None = None, **kwargs):
        return probe.judge_ac5("\n".join(lines) + "\n", JOB, now or noon(11) + dt.timedelta(hours=7), **kwargs)

    def probe_line(self, day: int = 11) -> str:
        return watchdog_line(noon(day) + dt.timedelta(hours=1), "ALERT", "JOB_MISSING", "999", "backup id 999 not in server list ['2']")

    def test_the_parser_reads_what_the_watchdog_really_writes(self) -> None:
        # Rule 1. record() is the only writer of this log; its lines are parsed here, not a copy of its format.
        with tempfile.TemporaryDirectory() as tmp:
            for backup_id, verdict, code, details in ((JOB, "OK", "OK", "newest backup x ParsedResult=Success age=4.0h"), (JOB, "OK", "RUNNING", "task 46 for backup 2 running 4.0 h"), (JOB, "ALERT", "NOT_SUCCESS", "newest log entry Backup x ParsedResult=Warning"), ("999", "ALERT", "JOB_MISSING", "backup id 999 not in server list"), ("", "ALERT", "JOB_MISSING", "--backup-id is not a job id"), (JOB, "UNDETERMINED", "LOG_UNAVAILABLE", "log -> 500\nsecond line")):
                watchdog.record(argparse.Namespace(state_dir=tmp, backup_id=backup_id, notify=False), verdict, code, details)
            text = (Path(tmp) / probe.WATCHDOG_LOG).read_text()
        records, unparsed = probe.parse_watchdog_log(text)
        self.assertEqual(unparsed, 0)
        self.assertEqual([(verdict, code, backup) for _when, verdict, code, backup in records], [("OK", "OK", JOB), ("OK", "RUNNING", JOB), ("ALERT", "NOT_SUCCESS", JOB), ("ALERT", "JOB_MISSING", "999"), ("ALERT", "JOB_MISSING", "INVALID"), ("UNDETERMINED", "LOG_UNAVAILABLE", JOB)])
        self.assertTrue(all(when.tzinfo is not None for when, *_rest in records))
        self.assertEqual(watchdog_line(records[0][0], details="newest backup x ParsedResult=Success age=4.0h"), text.splitlines()[0], "this suite's line helper writes the watchdog's format")

    def test_three_ok_days_and_the_probe_pass(self) -> None:
        finding = self.judge([watchdog_line(noon(9)), watchdog_line(noon(10)), watchdog_line(noon(11)), self.probe_line()])
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("OK on 3 consecutive days", finding.summary)
        self.assertIn("JOB_MISSING fired for --backup-id 999", finding.summary)

    def test_the_sittings_own_sequence_is_one_day_pending(self) -> None:
        # 2026-11-08 to 11-11 as recorded: OK, RUNNING, ALERT NOT_SUCCESS, RUNNING. The handoff's grep could not show the ALERT.
        lines = [watchdog_line(noon(8)), watchdog_line(noon(9), code="RUNNING", details="task 43 for backup 2 running 4.0 h"), watchdog_line(noon(10), "ALERT", "NOT_SUCCESS", details="newest log entry Backup x ParsedResult=Warning [notify-send rc=0]"), watchdog_line(noon(11), code="RUNNING", details="task 46 for backup 2 running 4.0 h")]
        finding = self.judge(lines)
        self.assertEqual(finding.verdict, "PENDING")
        self.assertIn("OK on 1 consecutive day(s) of 3: 2026-11-11 RUNNING", finding.summary)
        self.assertEqual(finding.facts["running_days"], 1)
        self.assertIn("no JOB_MISSING record", finding.summary)

    def test_what_breaks_a_streak(self) -> None:
        ok = [watchdog_line(noon(9)), watchdog_line(noon(10)), watchdog_line(noon(11)), self.probe_line()]
        gap = [watchdog_line(noon(8)), watchdog_line(noon(9)), watchdog_line(noon(11)), self.probe_line()]
        self.assertEqual(self.judge(gap).facts["streak_days"], 1, "a day with no record is not a day that read OK")
        second_alert = ok + [watchdog_line(noon(10) + dt.timedelta(hours=3), "ALERT", "UNREACHABLE", details="login failed")]
        self.assertEqual(self.judge(second_alert).facts["streak_days"], 1, "every record of a day must read OK")
        undetermined = [watchdog_line(noon(9)), watchdog_line(noon(10), "UNDETERMINED", "LOG_UNAVAILABLE", details="log -> 500"), watchdog_line(noon(11)), self.probe_line()]
        self.assertEqual(self.judge(undetermined).facts["streak_days"], 1)
        newest_alert = ok + [watchdog_line(noon(11) + dt.timedelta(hours=2), "ALERT", "STALE", details="x")]
        failing = self.judge(newest_alert)
        self.assertEqual(failing.verdict, "FAIL")
        self.assertIn("reads ALERT STALE+OK OK", failing.summary)

    def test_other_jobs_records_neither_help_nor_hurt(self) -> None:
        lines = [watchdog_line(noon(9)), watchdog_line(noon(10)), watchdog_line(noon(11)), self.probe_line(), watchdog_line(noon(11), "ALERT", "JOB_MISSING", "INVALID", "x"), watchdog_line(noon(11) + dt.timedelta(minutes=5), backup="7")]
        self.assertEqual(self.judge(lines).verdict, "PASS", "the deliberate 999 check must not break the job's own streak")
        only_others = [watchdog_line(noon(11), backup="7"), self.probe_line()]
        self.assertEqual(self.judge(only_others).verdict, "ERROR", "no record for THIS job is not a pass")

    def test_the_job_missing_probe_counts_only_from_the_recovery_date(self) -> None:
        old = watchdog_line(dt.datetime(2026, 8, 26, 12, 0, tzinfo=CST), "ALERT", "JOB_MISSING", "999", "certification test")
        lines = [watchdog_line(noon(9)), watchdog_line(noon(10)), watchdog_line(noon(11))]
        self.assertEqual(self.judge([old] + lines).verdict, "PENDING")
        on_the_day = watchdog_line(dt.datetime(2026, 11, 7, 0, 0, 1, tzinfo=CST), "ALERT", "JOB_MISSING", "999", "x")
        self.assertEqual(self.judge([on_the_day] + lines).verdict, "PASS", "the recovery date itself counts")
        ok_999 = watchdog_line(noon(11), "OK", "OK", "999")
        self.assertEqual(self.judge(lines + [ok_999]).verdict, "PENDING", "only an ALERT JOB_MISSING is the probe firing")
        unreachable_999 = watchdog_line(noon(11), "ALERT", "UNREACHABLE", "999", "login failed")
        self.assertEqual(self.judge(lines + [unreachable_999]).verdict, "PENDING", "an ALERT of another kind for 999 proves nothing about JOB_MISSING")

    def test_a_silent_watchdog_fails_and_36_hours_is_the_edge(self) -> None:
        lines = [watchdog_line(noon(9)), watchdog_line(noon(10)), watchdog_line(noon(11)), self.probe_line(10)]
        at_edge = self.judge(lines, now=noon(11) + dt.timedelta(hours=36))
        past = self.judge(lines, now=noon(11) + dt.timedelta(hours=36, seconds=1))
        self.assertEqual((at_edge.verdict, past.verdict), ("PASS", "FAIL"))
        self.assertIn("the watchdog is not checking", past.summary)

    def test_a_day_is_the_logs_own_calendar_day(self) -> None:
        late = dt.datetime(2026, 11, 10, 23, 59, 30, tzinfo=CST)  # 05:59 UTC the next day
        early = dt.datetime(2026, 11, 11, 0, 0, 30, tzinfo=CST)
        finding = self.judge([watchdog_line(late), watchdog_line(early)], now=early + dt.timedelta(hours=1))
        self.assertEqual(finding.facts["streak_days"], 2)

    def test_empty_unreadable_and_decorated_logs(self) -> None:
        self.assertEqual(probe.judge_ac5(None, JOB, NOW).verdict, "ERROR")
        for text in ("", "\n\n", "\ufeff"):
            self.assertEqual(probe.judge_ac5(text, JOB, NOW).verdict, "ERROR")
        garbage = watchdog_line(noon(10)) + "\nnot a record\n2026-11-11 OK OK backup=2 x\n" + watchdog_line(noon(11)) + "\n"
        finding = probe.judge_ac5("\ufeff" + garbage, JOB, noon(11) + dt.timedelta(hours=1))
        self.assertEqual(finding.facts["unparsed_lines"], 2)
        self.assertEqual(finding.facts["streak_days"], 2, "a BOM in front of the file's FIRST record does not hide that record")


# --- AC-6a ------------------------------------------------------------------------------------------------------------
class Ac6aTest(unittest.TestCase):
    def judge(self, text: str | None = None, snapshot: dict | None = None, now: dt.datetime | None = None, **kwargs):
        return probe.judge_ac6a(snapshot_file() if snapshot is None else snapshot, four_days() if text is None else text, now or NOW, me="operator", **kwargs)

    def test_the_source_pattern_matches_the_scripts_own_line(self) -> None:
        # Rule 1: render the script's f-string from its source, and take SRC from its source too.
        tree = ast.parse(SNAPSHOT_SCRIPT.read_text(encoding="utf-8"))
        rendered: list[str] = []
        src = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SRC" for t in node.targets) and isinstance(node.value, ast.Constant):
                src = node.value.value
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print" and node.args and isinstance(node.args[0], ast.JoinedStr):
                parts = []
                for value in node.args[0].values:
                    if isinstance(value, ast.Constant):
                        parts.append(str(value.value))
                    elif isinstance(value, ast.FormattedValue):
                        parts.append({"args.src": "/data/x.sqlite"}.get(ast.unparse(value.value), "596.0 KiB"))
                rendered.append("".join(parts))
        matches = [m for m in (probe.SNAPSHOT_SOURCE_LINE.match(line) for line in rendered) if m]
        self.assertEqual([m.group(1) for m in matches], ["/data/x.sqlite"], rendered)
        self.assertEqual(src, probe.SNAPSHOT_SOURCE, "the lane's source is the service's data folder, as the script defaults it")

    def test_four_daily_runs_pass(self) -> None:
        finding = self.judge()
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("each of the last 4 days", finding.summary)
        self.assertEqual(finding.facts["consecutive_days"], 4)

    def test_one_day_is_not_yet_daily(self) -> None:
        only = journal(snapshot_run(fire(11)))
        self.assertEqual(self.judge(only).verdict, "PENDING")
        gap = journal(snapshot_run(fire(9)) + snapshot_run(fire(11)))
        self.assertEqual(self.judge(gap).facts["consecutive_days"], 1, "a missed day restarts the count")

    def test_the_due_fire_must_have_run_and_its_grace_is_inclusive(self) -> None:
        through_10 = journal(snapshot_run(fire(9)) + snapshot_run(fire(10)))
        due = dt.datetime(2026, 11, 11, 13, 45, tzinfo=UTC) + dt.timedelta(minutes=15)
        before = self.judge(through_10, snapshot_file(fire(10)), now=due - dt.timedelta(seconds=1))
        at = self.judge(through_10, snapshot_file(fire(10)), now=due)
        self.assertEqual(before.verdict, "PASS", "inside the grace, yesterday's fire is the newest one due")
        self.assertEqual(at.verdict, "FAIL")
        self.assertIn("the fire due at 2026-11-11T13:45:00Z has no successful run", at.summary)
        self.assertEqual(probe.last_due_fire(due), dt.datetime(2026, 11, 11, 13, 45, tzinfo=UTC))
        self.assertEqual(probe.last_due_fire(due - dt.timedelta(seconds=1)), dt.datetime(2026, 11, 10, 13, 45, tzinfo=UTC))

    def test_the_lane_must_read_the_services_data_folder(self) -> None:
        wrong = journal(snapshot_run(fire(9)) + snapshot_run(fire(10), source="/usr/lib/duplicati/data/Duplicati-server.sqlite") + snapshot_run(fire(11)))
        finding = self.judge(wrong)
        self.assertEqual(finding.verdict, "FAIL")
        self.assertIn("read another source", finding.summary)
        silent = journal([(when, job_type, result, message) for when, job_type, result, message in snapshot_run(fire(10)) + snapshot_run(fire(11)) if not message.startswith("source")])
        no_line = self.judge(silent)
        self.assertEqual(no_line.verdict, "ERROR", "no `source :` line is unread evidence, not a pass")
        self.assertIn("no `source :` line", no_line.summary)

    def test_records_before_the_enable_are_ignored_and_one_at_it_counts(self) -> None:
        stale = snapshot_run(dt.datetime(2026, 10, 9, 13, 45, tzinfo=UTC), source="/usr/lib/duplicati/data/Duplicati-server.sqlite")
        self.assertEqual(self.judge(journal(stale) + four_days()).verdict, "PASS")
        runs = journal(snapshot_run(fire(10)) + snapshot_run(fire(11)))
        finished = fire(10) + dt.timedelta(seconds=1)  # the instant the first run's start job reported `done`
        self.assertEqual(self.judge(runs, enabled=finished).facts["consecutive_days"], 2, "a run that finished AT the enable instant is inside the window")
        self.assertEqual(self.judge(runs, enabled=finished + dt.timedelta(seconds=1)).facts["consecutive_days"], 1)

    def test_the_snapshot_file_is_the_newest_runs(self) -> None:
        done = fire(11) + dt.timedelta(seconds=1)
        for label, snapshot, needle in (
            ("missing", None, "does not exist"),
            ("stale", snapshot_file(fire(10)), "is not the newest run's"),
            ("stub", snapshot_file(size=4096), "a stub"),
            ("loose mode", snapshot_file(mode=0o644), "mode 0644"),
            ("other owner", snapshot_file(owner="root"), "owner root"),
        ):
            with self.subTest(case=label):
                finding = probe.judge_ac6a(snapshot, four_days(), NOW, me="operator")
                self.assertEqual(finding.verdict, "FAIL")
                self.assertIn(needle, finding.summary)
        at_slack = snapshot_file(mtime=(done + dt.timedelta(seconds=180)).timestamp())
        past_slack = snapshot_file(mtime=(done + dt.timedelta(seconds=181)).timestamp())
        self.assertEqual((self.judge(snapshot=at_slack).verdict, self.judge(snapshot=past_slack).verdict), ("PASS", "FAIL"))

    def test_a_failed_newest_start_fails(self) -> None:
        text = journal(snapshot_run(fire(9)) + snapshot_run(fire(10)) + snapshot_run(fire(11), result="failed"))
        finding = self.judge(text, snapshot_file(fire(10)))
        self.assertEqual(finding.verdict, "FAIL")
        self.assertIn("the newest start job failed", finding.summary)

    def test_empty_and_unreadable_journals(self) -> None:
        self.assertEqual(probe.judge_ac6a(snapshot_file(), None, NOW).verdict, "ERROR")
        for text in ("", "\ufeff\n", "-- No entries --\n"):
            self.assertEqual(probe.judge_ac6a(snapshot_file(), text, NOW).verdict, "ERROR")
        records, unparsed = probe.parse_journal("\ufeff" + four_days() + "not json\n{}\n")
        self.assertEqual((len(records), unparsed), (16, 2))
        binary = json.dumps({"__REALTIME_TIMESTAMP": "1794404726000000", "MESSAGE": [115, 111]}) + "\n"
        self.assertEqual(probe.parse_journal(binary)[0][0][3], "", "a non-text MESSAGE is not a source line")


# --- AC-7 -------------------------------------------------------------------------------------------------------------
class Ac7Test(unittest.TestCase):
    GID = 139
    KEYS = "/mnt/disk/_keys"
    ROOTS = ["/mnt/disk/Dropbox"]

    def judge(self, entries: list[dict] | None = None, statuses: dict | None = None, daemons: list[dict] | None = None, **kwargs):
        entries = destination() if entries is None else entries
        daemons = [{"pid": 4242, "gids": {self.GID}, "groups": {4, 27, 1000}}] if daemons is None else daemons
        params: dict = {"now": NOW, "keys_dir_real": self.KEYS, "dropbox_roots": self.ROOTS, "service_user": "duplicati"}
        params.update(kwargs)
        return probe.judge_ac7(daemons, self.GID, entries, all_synced(entries) if statuses is None else statuses, **params)

    def test_proc_status_and_filestatus_parsers(self) -> None:
        gids, groups = probe.parse_proc_status("Name:\tdropbox\nUid:\t1000\t1000\t1000\t1000\nGid:\t139\t139\t139\t139\nGroups:\t4 24 27 1000 \nVmPeak:\t1 kB\n")
        self.assertEqual((gids, groups), ({139}, {4, 24, 27, 1000}))
        self.assertEqual(probe.parse_proc_status(""), (set(), set()))
        paths = ["/d/duplicati-20261111T140001Z.dlist.zip.aes", "/d/short.aes", "/d/odd: name.aes", "/d/gone.aes"]
        statuses = ["unsyncable", "up to date", "syncing", "File doesn't exist"]
        indent = max(len(p) + 1 for p in paths)
        text = "\ufeff" + "".join("%-*s %s\n" % (indent, p + ":", s) for p, s in zip(paths, statuses))  # the dropbox CLI's own format expression
        self.assertEqual(probe.parse_filestatus(text + "/elsewhere/x: up to date\nDropbox isn't running!\n", paths), dict(zip(paths, statuses)))
        self.assertEqual(probe.parse_filestatus("Dropbox isn't running!\n", paths), {})
        self.assertEqual(probe.parse_filestatus("", paths), {})

    def test_everything_synced_passes_by_either_route_to_the_group(self) -> None:
        primary = self.judge()
        self.assertEqual(primary.verdict, "PASS")
        self.assertIn("(primary)", primary.summary)
        supplementary = self.judge(daemons=[{"pid": 1, "gids": {1000}, "groups": {4, self.GID}}])
        self.assertIn("(supplementary)", supplementary.summary)

    def test_the_daemon_must_exist_and_carry_the_group(self) -> None:
        self.assertIn("no Dropbox daemon", self.judge(daemons=[]).summary)
        lacking = self.judge(daemons=[{"pid": 379016, "gids": {1000}, "groups": {4, 27, 1000}}])
        self.assertEqual(lacking.verdict, "FAIL")
        self.assertIn("pid 379016 does not carry gid 139", lacking.summary)

    def test_a_volume_the_service_still_owns_is_unsyncable_even_with_the_group(self) -> None:
        # Measured 2026-11-11: gid 139 on the daemon, and the three volumes of that day's run read `unsyncable`.
        entries = destination(newest_owner="duplicati") + [volume("duplicati-b9999.dblock.zip.aes", owner="duplicati", mode=0o640), volume("duplicati-i9999.dindex.zip.aes", owner="duplicati", mode=0o640)]
        statuses = all_synced(entries, **{"duplicati-20261111T140001Z.dlist.zip.aes": "unsyncable", "duplicati-b9999.dblock.zip.aes": "unsyncable", "duplicati-i9999.dindex.zip.aes": "unsyncable"})
        finding = self.judge(entries, statuses)
        self.assertEqual(finding.verdict, "FAIL")
        self.assertIn("3 volume(s) read `unsyncable` (1 dblock, 1 dindex, 1 dlist); 3 of them are owned by duplicati", finding.summary)
        self.assertEqual(finding.facts["unsyncable"]["dlists"], ["duplicati-20261111T140001Z.dlist.zip.aes"])

    def test_the_newest_dlist_has_24_hours_and_the_edge_is_inside(self) -> None:
        name = "duplicati-20261111T140001Z.dlist.zip.aes"
        for label, age, expected in (("inside", dt.timedelta(hours=23, minutes=59), "PENDING"), ("at the edge", dt.timedelta(hours=24), "PENDING"), ("past it", dt.timedelta(hours=24, seconds=30), "FAIL")):
            with self.subTest(case=label):
                entries = destination(newest_written=NOW - age)
                self.assertEqual(self.judge(entries, all_synced(entries, **{name: "syncing"})).verdict, expected)

    def test_the_newest_dlist_is_chosen_by_its_name_not_its_mtime(self) -> None:
        entries = destination()
        entries[-2]["mtime"] = NOW.timestamp()  # the OLDER fileset's file was touched last (a chown bumps nothing here, but a copy would)
        self.assertEqual(probe.newest_dlist(entries)["name"], "duplicati-20261111T140001Z.dlist.zip.aes")
        self.assertIsNone(probe.newest_dlist(entries[:8]))
        self.assertIsNone(probe.dlist_stamp("duplicati-b0001.dblock.zip.aes"))

    def test_unread_statuses_are_errors(self) -> None:
        entries = destination()
        self.assertEqual(self.judge(entries, {}).verdict, "ERROR")
        partial = all_synced(entries)
        del partial[entries[0]["name"]]
        finding = self.judge(entries, partial)
        self.assertEqual(finding.verdict, "ERROR")
        self.assertIn("no status for 1 of 10 files", finding.summary)
        self.assertEqual(self.judge([], {}).verdict, "ERROR")
        self.assertIn("holds no dlist", self.judge(destination()[:8]).summary)

    def test_the_keys_directory_must_exist_outside_dropbox(self) -> None:
        self.assertIn("inside the Dropbox root", self.judge(keys_dir_real="/mnt/disk/Dropbox/_keys").summary)
        self.assertEqual(self.judge(keys_dir_real="/mnt/disk/Dropbox-not/_keys").verdict, "PASS", "a sibling whose name merely starts the same is outside")
        self.assertIn("does not exist", self.judge(keys_dir_real=None).summary)
        self.assertEqual(self.judge(dropbox_roots=[]).verdict, "ERROR")


# --- AC-12 ------------------------------------------------------------------------------------------------------------
class Ac12Test(unittest.TestCase):
    def test_the_accepted_set_is_the_design_documents(self) -> None:
        note = next(line for line in DESIGN.read_text(encoding="utf-8").split("- **(AC-12a)**")[1].split("- **(AC-14a)**")[:1])
        self.assertEqual(len(probe.ACCEPTED_UNSET), 15)
        for name in probe.ACCEPTED_UNSET:
            self.assertIn(f"`{name}`", note, f"{name} is not in note AC-12a's accepted set")
        self.assertIn("**15**", note)

    def test_the_unit_as_measured_passes(self) -> None:
        finding = probe.judge_ac12(security_rows(), overall_line())
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("exposure 1.7 <= 2.0; 15 unset rows", finding.summary)

    def test_the_gate_is_inclusive(self) -> None:
        self.assertEqual(probe.judge_ac12(security_rows(), overall_line("2.0")).verdict, "PASS")
        above = probe.judge_ac12(security_rows(), overall_line("2.1"))
        self.assertEqual(above.verdict, "FAIL")
        self.assertIn("exposure 2.1 is above 2.0", above.summary)

    def test_a_dropped_directive_is_named(self) -> None:
        finding = probe.judge_ac12(security_rows(extra_unset=("ProtectClock=", "SystemCallFilter=~@mount")), overall_line("1.9"))
        self.assertEqual(finding.verdict, "FAIL")
        self.assertIn("outside note AC-12a's accepted set: ProtectClock=, SystemCallFilter=~@mount", finding.summary)
        tighter = probe.judge_ac12(security_rows(drop_unset=("RemoveIPC=",)), overall_line("1.6"))
        self.assertEqual(tighter.verdict, "PASS", "a row that became set is an improvement")
        self.assertIn("14 unset rows", tighter.summary)

    def test_unreadable_output_is_an_error(self) -> None:
        for rows in (None, [], security_rows()[:10], "rows"):
            self.assertEqual(probe.judge_ac12(rows, overall_line()).verdict, "ERROR")
        for text in ("", None, "Overall exposure level for duplicati.service: n/a"):
            self.assertEqual(probe.judge_ac12(security_rows(), text).verdict, "ERROR")
        odd = security_rows()
        odd[3] = {"name": "X=", "set": "no"}
        self.assertIn("JSON shape changed", probe.judge_ac12(odd, overall_line()).summary)


# --- RUN --------------------------------------------------------------------------------------------------------------
class WarningTest(unittest.TestCase):
    def test_the_key_comes_from_the_tag(self) -> None:
        self.assertEqual(probe.warning_key(FIREFOX_WARNINGS[0]), "FilePreFilterProcess.FileEntry-PathNotFound")
        self.assertEqual(probe.warning_key("[Warning-A.B.C-Id]: x"), "B.C-Id")
        self.assertEqual(probe.warning_key("[Warning-Single-Id]: x"), "Single-Id")
        for untagged in ("Failed to process path: /x", "[Warning-NoDash]: x", "[Error-A.B-Id]: x", None, 5, ""):
            self.assertIsNone(probe.warning_key(untagged))
        self.assertLessEqual(probe.ALLOWED_WARNING_TAGS, {probe.warning_key(w) for w in FIREFOX_WARNINGS})

    def test_the_three_firefox_warnings_of_the_ruling_are_allowed(self) -> None:
        got = probe.classify_warnings(FIREFOX_WARNINGS, 3, SCOPE)
        self.assertEqual((got["total"], got["allowed"], got["not_allowed"]), (3, 3, {}))
        self.assertEqual(set(got["by_key"]), set(probe.ALLOWED_WARNING_TAGS))

    def test_text_never_decides_the_class(self) -> None:
        # Rule 3, both directions. The 2026-11-08 filter matched `http` and `report` anywhere in the line.
        file_warning_with_report_words = warning("FileBlockProcessor.FileEntry-PathNotFound", FIREFOX + "storage/default/https+++reports.example.com/http-report.sqlite")
        report_warning_about_a_firefox_path = warning("Modules.Builtin.SendHttpMessage-HttpPostFailed", FIREFOX + "prefs.js", "Failed to send http message for")
        got = probe.classify_warnings([file_warning_with_report_words, report_warning_about_a_firefox_path], 2, SCOPE)
        self.assertEqual(got["allowed"], 1)
        self.assertEqual(got["not_allowed"], {"Builtin.SendHttpMessage-HttpPostFailed": 1})

    def test_a_bracket_in_the_path_is_never_the_tag(self) -> None:
        spoof = f"2026-11-10 - Failed to process path: {FIREFOX}[Warning-{TAG_PREFIX}FileBlockProcessor.FileEntry-PathNotFound]/x"
        self.assertEqual(probe.classify_warnings([spoof], 1, SCOPE)["not_allowed"], {"untagged": 1})
        tagged = warning("BackendManager.Remote-PutFailed", f"{FIREFOX}[Warning-{TAG_PREFIX}FileBlockProcessor.FileEntry-PathNotFound]/x")
        self.assertEqual(probe.classify_warnings([tagged], 1, SCOPE)["not_allowed"], {"BackendManager.Remote-PutFailed": 1})

    def test_an_allowed_tag_outside_the_ruled_path_is_not_allowed(self) -> None:
        elsewhere = [warning("FilePreFilterProcess.FileEntry-PathNotFound", HOME + ".ssh/known_hosts"), warning("MetadataGenerator.Metadata-MetadataProcessFailed", "/backup" + FIREFOX + "x"), warning("FileBlockProcessor.FileEntry-PathNotFound", HOME + ".mozilla/firefox-backup/x")]
        got = probe.classify_warnings(elsewhere, 3, SCOPE)
        self.assertEqual(got["allowed"], 0)
        self.assertEqual(sum(got["not_allowed"].values()), 3)
        self.assertTrue(all("outside the ruled path scope" in key for key in got["not_allowed"]))

    def test_what_cannot_be_classified_is_not_allowed(self) -> None:
        got = probe.classify_warnings(FIREFOX_WARNINGS + ["no tag at all", {"not": "text"}], 25, SCOPE)
        self.assertEqual((got["total"], got["allowed"]), (25, 3))
        self.assertEqual(got["not_allowed"], {"untagged": 1, "not listed in the result (truncated)": 21})
        self.assertEqual(probe.classify_warnings(None, None, SCOPE), {"total": 0, "allowed": 0, "by_key": {}, "not_allowed": {}})

    def test_a_summary_keeps_no_text(self) -> None:
        entry = log_entry(7, result="Warning", warnings=FIREFOX_WARNINGS + [warning("X.Y-Z", "/secret/" + PATH_MARKER)], errors=["boom " + PATH_MARKER + " " + URL_MARKER])
        summary = probe.summarize_entry(entry, SCOPE)
        never_leaks(self, json.dumps(summary, default=str))
        self.assertEqual((summary["warnings"]["total"], summary["errors"], summary["operation"]), (4, 1, "Backup"))
        bom = {"ID": 8, "Message": "\ufeff" + json.dumps(result_message())}
        self.assertEqual(probe.summarize_entry(bom, SCOPE)["operation"], "Backup")
        for old_format in ({"ID": 9, "Message": "plain text result"}, {"ID": 9}, "not an entry", {"ID": 9, "Message": "[1, 2]"}):
            self.assertIsNone(probe.summarize_entry(old_format, SCOPE)["operation"])


class RunTest(unittest.TestCase):
    def judge(self, newest: dict, previous: dict | None = None, retention: str | None = "suspended", **kwargs):
        return probe.judge_run([newest] + ([previous] if previous else []), retention, **kwargs)

    def test_a_clean_success_passes(self) -> None:
        finding = self.judge(summarized(), summarized(examined=1_950_000))
        self.assertEqual(finding.verdict, "PASS")
        self.assertIn("ParsedResult=Success, examined 2000000 (+2.6% vs the previous run)", finding.summary)
        self.assertIn("(0h50m)", finding.summary)

    def test_a_warning_result_passes_only_on_the_ruled_class(self) -> None:
        ruled = self.judge(summarized(result="Warning", warnings=FIREFOX_WARNINGS))
        self.assertEqual(ruled.verdict, "PASS")
        self.assertIn("all allow-listed by the 2026-11-08 ruling", ruled.summary)
        mixed = self.judge(summarized(result="Warning", warnings=FIREFOX_WARNINGS + [warning("BackendManager.Remote-PutFailed", "/x")]))
        self.assertEqual(mixed.verdict, "FAIL")
        self.assertIn("warnings outside the allow-list: BackendManager.Remote-PutFailed x1", mixed.summary)
        never_leaks(self, ruled.summary, mixed.summary, json.dumps(mixed.as_dict(), default=str))
        self.assertIn("no warning listed", self.judge(summarized(result="Warning")).summary)
        self.assertIn("ParsedResult=Success but 3 warning(s)", self.judge(summarized(warnings=FIREFOX_WARNINGS)).summary)

    def test_each_hard_failure(self) -> None:
        cases = {
            "ParsedResult=Error": summarized(result="Error"),
            "ParsedResult=Fatal": summarized(result="Fatal"),
            "ParsedResult=None": summarized(ParsedResult=None),
            "1 error(s)": summarized(errors=["x"]),
            "NotProcessedFiles=3": summarized(NotProcessedFiles=3),
            "FilesWithError=1": summarized(FilesWithError=1),
            "PartialBackup=True": summarized(PartialBackup=True),
            "Interrupted=True": summarized(Interrupted=True),
            "a compact ran": summarized(CompactResults={"DeletedFileCount": 1}),
            "verification reads Error": summarized(TestResults={"ParsedResult": "Error"}),
            "NotProcessedFiles is absent": summarized(drop=("NotProcessedFiles",)),
            "FilesWithError is absent": summarized(drop=("FilesWithError",)),
        }
        for needle, newest in cases.items():
            with self.subTest(case=needle):
                finding = self.judge(newest)
                self.assertEqual(finding.verdict, "FAIL")
                self.assertIn(needle, finding.summary)

    def test_deletions_are_a_failure_only_while_retention_is_suspended(self) -> None:
        deleting = summarized(DeleteResults={"DeletedSets": [{"Item1": 3, "Item2": "2026-09-18T14:00:00Z"}] * 8, "DeletedSetsActualLength": 8})
        suspended = self.judge(deleting, retention="suspended")
        self.assertEqual(suspended.verdict, "FAIL")
        self.assertIn("deleted 8 fileset(s) while retention is suspended", suspended.summary)
        self.assertEqual(self.judge(deleting, retention=None).verdict, "FAIL", "an unknown retention state excuses nothing")
        restored = self.judge(deleting, retention="restored")
        self.assertEqual(restored.verdict, "PASS")
        self.assertIn("retention deleted 8 fileset(s)", restored.summary)
        nested = summarized(DeleteResults={"DeletedSets": [], "CompactResults": {"x": 1}})
        self.assertIn("a compact ran", self.judge(nested).summary)

    def test_drift_is_attention_not_failure_and_its_edges_are_inside(self) -> None:
        previous = summarized(examined=1_000_000)
        at_edge = self.judge(summarized(examined=1_100_000), previous)
        past = self.judge(summarized(examined=1_100_001), previous)
        self.assertEqual((at_edge.verdict, past.verdict), ("PASS", "ATTN"))
        self.assertIn("question Q1 is unruled", past.summary)
        shrink = self.judge(summarized(examined=899_999), previous)
        self.assertEqual(shrink.verdict, "ATTN")
        size_edge = int(probe.BASELINE_BYTES * 1.05)
        self.assertEqual(self.judge(summarized(examined_bytes=size_edge)).verdict, "PASS")
        self.assertEqual(self.judge(summarized(examined_bytes=size_edge + probe.BASELINE_BYTES // 1000)).verdict, "ATTN")
        self.assertEqual(self.judge(summarized(result="Error", examined=5_000_000), previous).verdict, "FAIL", "a failure outranks attention")

    def test_a_backup_whose_log_entry_carries_an_exception_fails(self) -> None:
        entry = log_entry(9)
        entry["Exception"] = "System.IO.IOException: " + PATH_MARKER
        summary = probe.summarize_entry(entry, SCOPE)
        finding = self.judge(summary)
        self.assertEqual(finding.verdict, "FAIL")
        self.assertIn("carries an exception", finding.summary)
        never_leaks(self, finding.summary, json.dumps(summary, default=str))
        self.assertFalse(summarized()["exception"])

    def test_unreadable_entries_ahead_of_the_newest_backup_are_an_error(self) -> None:
        # A run that died may be logged as text, not as a result. The scan must not judge the backup before it instead.
        died = probe.summarize_entry({"ID": 12, "Message": "The operation Backup has failed", "Exception": "boom"}, SCOPE)
        text_only = probe.summarize_entry({"ID": 10, "Message": "old-format text"}, SCOPE)
        scan = [died, summarized(operation="ListFilesets"), text_only, summarized(), probe.summarize_entry({"ID": 1, "Message": "x"}, SCOPE)]
        self.assertEqual(probe.unreadable_before_first_backup(scan), 2, "entries OLDER than the newest backup are not counted")
        self.assertEqual(probe.unreadable_before_first_backup([summarized()]), 0)
        self.assertEqual(probe.unreadable_before_first_backup([]), 0)
        self.assertTrue(died["exception"])
        finding = self.judge(summarized(), unreadable_newer=2)
        self.assertEqual(finding.verdict, "ERROR")
        self.assertIn("2 log entries newer than this backup carry no readable result", finding.summary)
        self.assertIn("1 log entry newer", self.judge(summarized(), unreadable_newer=1).summary)
        self.assertEqual(self.judge(summarized(result="Error"), unreadable_newer=1).verdict, "FAIL", "a failure still outranks unread evidence")

    def test_a_daily_jobs_newest_backup_has_an_age_limit_and_its_edge_is_inside(self) -> None:
        begin = dt.datetime(2026, 11, 11, 14, 0, 1, tzinfo=UTC)
        newest = summarized(begin=begin, fraction="0000000")
        limit = dt.timedelta(hours=probe.MAX_RUN_AGE_HOURS)
        self.assertEqual(self.judge(newest, now=begin + limit).verdict, "PASS", "exactly the limit is inside it")
        late = self.judge(newest, now=begin + limit + dt.timedelta(seconds=1))
        self.assertEqual(late.verdict, "FAIL")
        self.assertIn("it began 26.0 h ago and no newer backup has finished (a daily job allows 26 h)", late.summary)
        # While a task runs, the newest FINISHED backup is the day before's: one day more, and no further.
        running = "task 46 for backup 2"
        self.assertEqual(self.judge(newest, now=begin + limit + dt.timedelta(hours=24), active_task=running).verdict, "PASS")
        stuck = self.judge(newest, now=begin + limit + dt.timedelta(hours=24, seconds=1), active_task=running)
        self.assertEqual(stuck.verdict, "FAIL")
        self.assertIn("a daily job allows 50 h while a task is active", stuck.summary)
        six_weeks = self.judge(newest, now=begin + dt.timedelta(weeks=6))
        self.assertEqual(six_weeks.verdict, "FAIL", "a clean run from six weeks ago is not the state of a daily job")
        self.assertEqual(six_weeks.facts["age_hours"], 1008.0)
        self.assertIsNone(self.judge(newest).facts["age_hours"], "without a clock nothing is claimed about its age")
        undated = self.judge(summarized(BeginTime="soon"), now=begin)
        self.assertEqual(undated.verdict, "ERROR")
        self.assertIn("no readable BeginTime", undated.summary)

    def test_the_age_limit_is_the_watchdogs(self) -> None:
        # Rule 1: the bound is the default of the watchdog's own --max-age-hours, read from its source.
        line = next(line for line in (AD_HOC / "yamaguchi_watchdog.py").read_text(encoding="utf-8").splitlines() if '"--max-age-hours"' in line)
        self.assertIn(f"default={probe.MAX_RUN_AGE_HOURS}", line)

    def test_no_backup_is_an_error_and_an_active_task_is_named(self) -> None:
        self.assertEqual(probe.judge_run([], "suspended").verdict, "ERROR")
        finding = self.judge(summarized(), active_task="task 46 for backup 2")
        self.assertIn("this is the newest FINISHED backup", finding.summary)


class ScheduleTest(unittest.TestCase):
    def at(self, day: int, hour: int, minute: int, second: int = 0, operation: str = "Backup") -> dict:
        return summarized(operation=operation, begin=dt.datetime(2026, 11, day, hour, minute, second, tzinfo=UTC), fraction="0000000")

    def test_runs_on_the_slot_pass_and_the_slack_is_inclusive(self) -> None:
        entries = [self.at(11, 14, 0, 1), self.at(10, 14, 5, 0), self.at(9, 13, 55, 0)]
        self.assertEqual(probe.judge_schedule(entries).verdict, "PASS")
        self.assertEqual(probe.judge_schedule([self.at(11, 14, 5, 1)]).verdict, "ATTN")
        self.assertEqual(probe.judge_schedule([self.at(11, 13, 54, 59)]).verdict, "ATTN")

    def test_the_two_runs_the_sitting_found_are_reported_with_what_came_before(self) -> None:
        entries = [
            self.at(11, 14, 0, 1),
            self.at(10, 14, 0, 0),
            self.at(10, 0, 36, 22),
            self.at(9, 14, 0, 1),
            self.at(8, 23, 41, 22),
            self.at(8, 23, 40, 51, "SearchFiles"),
            self.at(8, 23, 39, 34, "SearchFiles"),
            self.at(8, 23, 35, 38, "ListFilesets"),
            self.at(8, 23, 26, 22, "ListFolder"),
            self.at(8, 23, 26, 21, "ListFolder"),
            self.at(8, 23, 50, 0, "ListFilesets"),
            self.at(8, 14, 0, 1),
        ]
        finding = probe.judge_schedule(entries)
        self.assertEqual(finding.verdict, "ATTN")
        self.assertIn("2 of 6 backups began off the 14:00:00Z slot", finding.summary)
        by_begin = {o["begin"]: o["preceded_by"] for o in finding.facts["off_schedule"]}
        self.assertEqual(by_begin["2026-11-08T23:41:22Z"], {"ListFilesets": 1, "ListFolder": 1, "SearchFiles": 2}, "15 minutes exactly is inside; one second more, and anything after the start, is not")
        self.assertEqual(by_begin["2026-11-10T00:36:22Z"], {})
        self.assertIn("preceded by no logged operation", finding.summary)

    def test_the_slot_wraps_midnight(self) -> None:
        self.assertEqual(probe.seconds_off_schedule(dt.datetime(2026, 11, 10, 23, 59, 58, tzinfo=UTC), dt.time(0, 0, 0)), 2)
        self.assertEqual(probe.seconds_off_schedule(dt.datetime(2026, 11, 10, 0, 0, 3, tzinfo=UTC), dt.time(23, 59, 59)), 4)

    def test_backups_before_the_recovery_are_not_judged_and_none_is_an_error(self) -> None:
        old = summarized(begin=dt.datetime(2026, 9, 17, 22, 13, 44, tzinfo=UTC))
        self.assertEqual(probe.judge_schedule([old]).verdict, "ERROR")
        self.assertEqual(probe.judge_schedule([self.at(11, 14, 0, 1), old]).verdict, "PASS")
        self.assertEqual(probe.judge_schedule([]).verdict, "ERROR")


# --- CENSUS and MODES ---------------------------------------------------------------------------------------------------
class CensusAndModesTest(unittest.TestCase):
    def test_census_agrees_diverges_or_waits(self) -> None:
        entries = destination()
        metadata = {"TargetFilesCount": "10", "TargetFilesSize": 10000}
        agree = probe.judge_census(entries, metadata)
        self.assertEqual(agree.verdict, "PASS")
        self.assertIn("10 files = 2 dlist + 4 dblock + 4 dindex + 0 other, 10000 B; AGREE", agree.summary)
        off = {"TargetFilesCount": 9, "TargetFilesSize": "9000"}
        self.assertEqual(probe.judge_census(entries, off).verdict, "FAIL")
        self.assertEqual(probe.judge_census(entries, off, "task 46 for backup 2").verdict, "PENDING")
        unusable: list[object] = [None, {}, {"TargetFilesCount": "10"}]
        for incomplete in unusable:
            self.assertEqual(probe.judge_census(entries, incomplete).verdict, "ERROR")
        self.assertEqual(probe.judge_census([], {"TargetFilesCount": "0", "TargetFilesSize": "0"}).verdict, "ERROR", "an empty listing is unread evidence")

    def test_modes_record_classes_and_changes(self) -> None:
        entries = destination(newest_owner="duplicati")
        first = probe.judge_modes(entries)
        self.assertEqual(first.verdict, "INFO")
        self.assertIn("1 dlist 640 duplicati:duplicati", first.summary)
        self.assertIn("4 dblock 770 operator:duplicati", first.summary)
        entries[-1]["owner"] = "operator"
        second = probe.judge_modes(entries, first.facts["dlists"])
        self.assertEqual(second.facts["changed_since_previous"], ["duplicati-20261111T140001Z.dlist.zip.aes: 640 duplicati:duplicati -> 640 operator:duplicati"])
        self.assertEqual(probe.judge_modes([]).verdict, "ERROR")


# --- the server, through the stub ---------------------------------------------------------------------------------------
class _Stubbed(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.state_dir = self.dir / "state"
        self.cred = write_credential(self.dir / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        for patcher in (mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.cred)}), mock.patch("urllib.request.urlopen", self.fake.urlopen), mock.patch.object(api, "BASE", STUB_BASE)):
            patcher.start()
            self.addCleanup(patcher.stop)
        # main() judges the newest backup's age against the real clock, so the newest one here began at the last
        # 14:00:01Z slot. The others keep the sitting's shape: a Warning run a day earlier, an off-schedule one at
        # 00:36:22Z that day, a scheduled one the day before.
        slot = dt.datetime.now(UTC).replace(hour=14, minute=0, second=1, microsecond=0)
        if slot > dt.datetime.now(UTC):
            slot -= dt.timedelta(days=1)
        day = dt.timedelta(days=1)
        self.entries = [
            log_entry(60, begin=slot, minutes=244, examined=2_050_000),
            log_entry(59, operation="ListFilesets", begin=slot - dt.timedelta(hours=11)),
            log_entry(58, result="Warning", begin=slot - day - dt.timedelta(seconds=1), examined=2_000_000, warnings=FIREFOX_WARNINGS),
            log_entry(57, begin=slot - day - dt.timedelta(hours=13, minutes=23, seconds=39), examined=1_990_000),
            log_entry(56, begin=slot - 2 * day, examined=1_980_000),
        ]
        self.serve()

    def serve(self, *, state: dict | None = None, doc: dict | None = None, metadata: dict | None = None, log_status: int = 200) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, {"ProgramState": "Running", "ActiveTask": None, "SchedulerQueueIds": []} if state is None else state)
        self.fake.route("GET", f"/api/v1/backup/{JOB}", 200, {"Backup": {"ID": JOB, "TargetURL": "file:///mnt/dest/", "Metadata": {"TargetFilesCount": "10", "TargetFilesSize": "10000"} if metadata is None else metadata}})
        self.fake.route("GET", f"/api/v1/backup/{JOB}/export", 200, export() if doc is None else doc)

        def page(query: dict) -> tuple[int, object]:
            if log_status != 200:
                return log_status, {"Error": "log unavailable"}
            ids = [e["ID"] for e in self.entries]
            start = ids.index(int(query["offset"])) + 1 if "offset" in query else 0
            return 200, self.entries[start : start + 2]  # a server that pages two at a time, whatever pagesize asks

        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", handler=page)

    def paths(self) -> list[str]:
        return [f"{r.method} {r.path}" for r in self.fake.requests]


class ServerTest(_Stubbed):
    def test_one_collection_reads_everything_and_sends_nothing_that_changes_the_server(self) -> None:
        data = probe.collect_server(STUB_BASE, JOB, 3, SCOPE)
        self.assertNotIn("error", data)
        self.assertEqual((data["dest"], data["active_task"], data["program_state"]), ("/mnt/dest/", None, "Running"))
        self.assertEqual([e["operation"] for e in data["entries"]], ["Backup", "ListFilesets", "Backup", "Backup"], "paging stops once three backups are in hand")
        self.assertEqual(data["metadata"], {"TargetFilesCount": "10", "TargetFilesSize": "10000"})
        writes = [p for p in self.paths() if not p.startswith("GET ") and p not in ("POST /api/v1/auth/login", "POST /api/v1/auth/issuetoken/export")]
        self.assertEqual(writes, [], "only the login and the export token are POSTed")
        export_request = next(r for r in self.fake.requests if r.method == "GET" and r.path.endswith("/export"))
        self.assertEqual(export_request.query["export-passwords"], "false")
        never_leaks(self, json.dumps(data["entries"], default=str))

    def test_an_active_task_is_named(self) -> None:
        self.serve(state={"ProgramState": "Running", "ActiveTask": {"Item1": 46, "Item2": "2"}})
        self.assertEqual(probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["active_task"], "task 46 for backup 2")

    def test_failures_are_reasons_never_exceptions_and_never_the_credential(self) -> None:
        self.fake.route("POST", "/api/v1/auth/login", 401, {"Error": "Failed to log in: " + PATH_MARKER, "Code": 401})
        refused = probe.collect_server(STUB_BASE, JOB, 2, SCOPE)
        self.assertEqual(refused["error"], "the server refused the login (status 401); its answer is not printed")
        never_leaks(self, refused["error"])
        self.fake.route("POST", "/api/v1/auth/login", 200, {"AccessToken": self.fake.bearer})
        self.serve(log_status=500)
        self.assertIn("log -> 500", probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["error"])
        self.serve()
        self.fake.route("GET", f"/api/v1/backup/{JOB}/export", 500, {"Error": "x"})
        self.assertIn(f"export {JOB} -> 500", probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["error"])
        self.fake.route("GET", f"/api/v1/backup/{JOB}", 404, {"Error": "x"})
        self.assertIn(f"GET backup {JOB} -> 404", probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["error"])
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
            self.assertIn("cannot reach", probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["error"])
        os.chmod(self.cred, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0644: the mode the API client must refuse
        unsafe = probe.collect_server(STUB_BASE, JOB, 2, SCOPE)["error"]
        self.assertIn("credential refused: FATAL: web credential file", unsafe)
        self.assertIn("mode 0644", unsafe, "the client's own sentence -- a path, a mode, an owner -- is kept")
        never_leaks(self, unsafe)

    def test_the_login_failure_pattern_is_the_api_clients_own_line(self) -> None:
        # Rule 1: login()'s sys.exit f-string is rendered from the client's source, and the pattern must read its status.
        tree = ast.parse((AD_HOC / "yamaguchi_server_api.py").read_text(encoding="utf-8"))
        rendered: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "sys.exit" and node.args and isinstance(node.args[0], ast.JoinedStr):
                parts = []
                for value in node.args[0].values:
                    if isinstance(value, ast.Constant):
                        parts.append(str(value.value))
                    elif isinstance(value, ast.FormattedValue):
                        parts.append({"status": "401"}.get(ast.unparse(value.value), PATH_MARKER))
                rendered.append("".join(parts))
        logins = [line for line in rendered if probe.LOGIN_FAILED.match(line)]
        self.assertEqual(len(logins), 1, rendered)
        self.assertIn(PATH_MARKER, logins[0], "the client's message does carry the server's answer, which is why it is cut")
        self.assertEqual(probe.refusal_reason(SystemExit(logins[0])), "the server refused the login (status 401); its answer is not printed")
        self.assertEqual(probe.refusal_reason(SystemExit(2)), "the API client stopped; its message is not printed")
        self.assertEqual(probe.refusal_reason(SystemExit("another sentence " + PATH_MARKER)), "the API client stopped; its message is not printed")
        self.assertEqual(probe.refusal_reason(api.CredentialError("FATAL: web credential file /x is mode 0644")), "credential refused: FATAL: web credential file /x is mode 0644")
        self.assertEqual(len(probe.refusal_reason(api.CredentialError("x" * 500))), len("credential refused: ") + 200)

    def test_a_log_that_ignores_the_offset_ends_the_scan(self) -> None:
        self.fake.route("GET", f"/api/v1/backup/{JOB}/log", 200, self.entries[1:2])  # the same non-backup entry on every page
        status, entries = probe.fetch_log("tok", JOB, 5, SCOPE)
        self.assertEqual((status, len(entries)), (200, 1))
        self.assertLessEqual(len([p for p in self.paths() if p.endswith("/log")]), 2)


class MainTest(_Stubbed):
    def setUp(self) -> None:
        super().setUp()
        entries = destination()
        self.collectors = {
            "collect_unit": lambda: unit_props(ActiveEnterTimestamp=f"@{int((dt.datetime.now(UTC) - dt.timedelta(hours=111)).timestamp())}"),
            "collect_snapshot": lambda: None,
            "collect_snapshot_journal": lambda _now: None,
            "collect_destination": lambda _dest: entries,
            "collect_daemons": lambda: [{"pid": 4242, "gids": {139}, "groups": {4}}],
            "collect_filestatus": lambda _dest, names: dict.fromkeys(names, "up to date"),
            "collect_dropbox_roots": lambda: ["/mnt/disk/Dropbox"],
            "collect_security": lambda: (security_rows(), overall_line()),
        }
        for name, replacement in self.collectors.items():
            patcher = mock.patch.object(probe, name, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        for host_lookup in (mock.patch.object(probe.grp, "getgrnam", return_value=argparse.Namespace(gr_gid=139)), mock.patch.object(probe.os.path, "isdir", return_value=True)):
            host_lookup.start()
            self.addCleanup(host_lookup.stop)

    def run_probe(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = probe.main(list(argv))
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, out.getvalue(), err.getvalue()

    def lines(self, text: str) -> dict:
        return {line.split()[0]: line.split()[1] for line in text.splitlines() if line and line.split()[0] in ("AC-1", "AC-2", "AC-13", "OPTIONS", "AC-5", "AC-6a", "AC-6b", "AC-7", "AC-12", "RUN", "OFFSCHED", "CENSUS", "MODES")}

    def test_a_full_run_prints_one_line_per_criterion_and_writes_two_files(self) -> None:
        log = self.state_dir / probe.WATCHDOG_LOG
        self.state_dir.mkdir()
        today = dt.datetime.now(CST).replace(hour=12, minute=0, second=39, microsecond=0)
        if today > dt.datetime.now(CST):
            today -= dt.timedelta(days=1)
        log.write_text("".join(watchdog_line(today - dt.timedelta(days=d)) + "\n" for d in (2, 1, 0)) + watchdog_line(today, "ALERT", "JOB_MISSING", "999", "x") + "\n")
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--state-dir", str(self.state_dir), "--dest", "/mnt/dest")
        verdicts = self.lines(out)
        self.assertEqual(verdicts, {"AC-1": "PASS", "AC-2": "PASS", "AC-13": "PASS", "OPTIONS": "PASS", "AC-5": "PASS", "AC-6a": "ERROR", "AC-6b": "INFO", "AC-7": "PASS", "AC-12": "PASS", "RUN": "PASS", "OFFSCHED": "ATTN", "CENSUS": "PASS", "MODES": "INFO"}, out)
        self.assertEqual(code, probe.EXIT_ERROR, "an unreadable journal is UNDETERMINED: exit 2, not 0 and not 1")
        self.assertIn("RESULT: UNDETERMINED", out)
        self.assertEqual(out.count("\n  run 20"), 4)
        self.assertIn("OFF-SCHEDULE", out)
        document = json.loads((self.state_dir / "acceptance.json").read_text())
        self.assertEqual((document["schema"], document["backup_id"], document["result"], document["server"]), (probe.SCHEMA, JOB, "UNDETERMINED", "read"))
        self.assertEqual([c["id"] for c in document["criteria"]], list(verdicts))
        history = [json.loads(line) for line in (self.state_dir / "acceptance-history.jsonl").read_text().splitlines()]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["newest_backup"]["examined"], 2_050_000)
        self.assertEqual(os.stat(self.state_dir / "acceptance.json").st_mode & 0o777, 0o600)
        never_leaks(self, out, (self.state_dir / "acceptance.json").read_text(), (self.state_dir / "acceptance-history.jsonl").read_text())
        self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--state-dir", str(self.state_dir), "--dest", "/mnt/dest")
        self.assertEqual(len((self.state_dir / "acceptance-history.jsonl").read_text().splitlines()), 2, "one history line per run")

    def test_when_every_criterion_it_judges_passes_the_result_is_pass(self) -> None:
        # Until 2026-11-12 main() added `AC-6b SKIP` on every run, and any SKIP makes RESULT read INCOMPLETE: this
        # probe could not report PASS at all. Three criteria the fixture cannot satisfy are stood in for.
        for name, criterion in (("judge_ac5", "AC-5"), ("judge_ac6a", "AC-6a"), ("judge_schedule", "OFFSCHED")):
            patcher = mock.patch.object(probe, name, return_value=probe.Finding(criterion, "PASS", "stand-in"))
            patcher.start()
            self.addCleanup(patcher.stop)
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--no-write", "--state-dir", str(self.state_dir), "--dest", "/mnt/dest")
        verdicts = self.lines(out)
        self.assertEqual(verdicts["AC-6b"], "INFO")
        self.assertEqual(set(verdicts.values()), {"PASS", "INFO"}, out)
        self.assertIn("RESULT: PASS (", out)
        self.assertEqual(code, 0)

    def test_a_newest_backup_from_days_ago_fails_the_run(self) -> None:
        # main() hands judge_run the clock: the stub's log holds clean backups, none of them recent.
        stale = dt.datetime.now(UTC) - dt.timedelta(days=3)
        self.entries[:] = [log_entry(60, begin=stale, examined=2_050_000), log_entry(56, begin=stale - dt.timedelta(days=1), examined=2_000_000)]
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--no-write", "--state-dir", str(self.state_dir), "--dest", "/mnt/dest")
        self.assertEqual(self.lines(out)["RUN"], "FAIL")
        self.assertIn("it began 72.0 h ago and no newer backup has finished", out)
        self.assertEqual(code, probe.EXIT_FAIL)

    def test_no_server_sends_nothing_and_reads_no_credential(self) -> None:
        # The credential stays in place and the stub would answer: only the flag keeps the probe away from both.
        with mock.patch.object(api, "read_credential", side_effect=AssertionError("the credential was read under --no-server")):
            code, out, _err = self.run_probe("--backup-id", JOB, "--no-server", "--no-write", "--state-dir", str(self.state_dir))
        self.assertEqual(self.fake.requests, [])
        verdicts = self.lines(out)
        self.assertEqual({verdicts[c] for c in ("AC-2", "AC-13", "OPTIONS", "RUN", "OFFSCHED", "CENSUS")}, {"SKIP"})
        self.assertFalse(self.state_dir.exists(), "--no-write writes nothing, not even the directory")
        self.assertIn("no server", out.splitlines()[0])
        self.assertNotEqual(code, probe.EXIT_FAIL)

    def test_a_run_that_left_no_readable_result_is_not_passed_over(self) -> None:
        self.entries.insert(0, {"ID": 61, "Type": "Error", "Message": "The operation Backup has failed", "Exception": "System.Exception: " + PATH_MARKER})
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--no-write", "--state-dir", str(self.state_dir), "--dest", "/mnt/dest")
        self.assertEqual(self.lines(out)["RUN"], "ERROR")
        self.assertIn("1 log entry newer than this backup carry no readable result", out)
        self.assertEqual(code, probe.EXIT_ERROR)
        never_leaks(self, out)

    def test_an_unreachable_server_is_an_error_for_its_criteria_only(self) -> None:
        self.fake.route("POST", "/api/v1/auth/login", 401, {"Error": "Failed to log in"})
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--no-write", "--state-dir", str(self.state_dir))
        verdicts = self.lines(out)
        self.assertEqual({verdicts[c] for c in ("AC-2", "AC-13", "OPTIONS", "RUN", "OFFSCHED", "CENSUS")}, {"ERROR"})
        self.assertEqual((verdicts["AC-1"], verdicts["AC-12"]), ("PASS", "PASS"))
        self.assertEqual(code, probe.EXIT_ERROR)

    def test_a_failure_exits_1_and_step_5s_read_back_is_a_flag(self) -> None:
        code, out, _err = self.run_probe("--backup-id", JOB, "--base", STUB_BASE, "--no-write", "--state-dir", str(self.state_dir), "--expect-retention", "restored")
        self.assertEqual(code, probe.EXIT_FAIL)
        self.assertIn("retention is suspended, expected restored", out)
        self.assertIn("RESULT: FAIL", out)

    def test_usage_errors_exit_64_and_judge_nothing(self) -> None:
        for argv in ((), ("--backup-id", "two"), ("--backup-id", "0"), ("--backup-id", JOB, "--runs", "1"), ("--backup-id", JOB, "--recovered-on", "soon"), ("--backup-id", JOB, "--expect-retention", "maybe")):
            with self.subTest(argv=argv):
                code, out, _err = self.run_probe(*argv)
                self.assertEqual(code, 64)
                self.assertNotIn("RESULT:", out)
        self.assertEqual(self.fake.requests, [])

    def test_the_overall_result(self) -> None:
        def result(*verdicts: str) -> tuple[str, int]:
            return probe.overall([probe.Finding(f"C{i}", v, "x") for i, v in enumerate(verdicts)])

        self.assertEqual(result("PASS", "INFO"), ("PASS", 0))
        self.assertEqual(result("PASS", "PENDING"), ("INCOMPLETE", 0))
        self.assertEqual(result("PASS", "ATTN"), ("INCOMPLETE", 0))
        self.assertEqual(result("PASS", "SKIP"), ("INCOMPLETE", 0))
        self.assertEqual(result("PASS", "ERROR", "PENDING"), ("UNDETERMINED", 2))
        self.assertEqual(result("ERROR", "FAIL", "PASS"), ("FAIL", 1))
        with self.assertRaises(ValueError):
            probe.Finding("X", "MAYBE", "x")
        self.assertEqual(probe.settle(["f"], ["e"], ["p"], ["a"]), "FAIL")
        self.assertEqual(probe.settle((), ["e"], ["p"], ["a"]), "ERROR")
        self.assertEqual(probe.settle((), (), ["p"], ["a"]), "PENDING")
        self.assertEqual(probe.settle((), (), (), ["a"]), "ATTN")
        self.assertEqual(probe.settle(), "PASS")


# --- the timer units and their deploy script --------------------------------------------------------------------------
UNIT_FILE = REPO_ROOT / "util" / "systemd" / "yamaguchi-acceptance-probe.service"
TIMER_FILE = REPO_ROOT / "util" / "systemd" / "yamaguchi-acceptance-probe.timer"
DEPLOY = AD_HOC / "yamaguchi_acceptance_probe_deploy.bash"
ME = pwd.getpwuid(os.geteuid()).pw_name  # what `id -un` prints
STUB = """#!/bin/bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
case "$(basename "$0") $*" in
    "loginctl show-user"*) if [[ -n "${STUB_LOGINCTL_RC:-}" ]]; then exit "$STUB_LOGINCTL_RC"; fi; echo "${STUB_LINGER:-yes}" ;;
    "systemctl --user start"*) exit "${STUB_START_RC:-0}" ;;
    "systemctl --user is-enabled"*) echo enabled ;;
    "systemctl --user show"*) echo "YAMAGUCHI_BACKUP_ID=$(sed -n 's/^Environment=YAMAGUCHI_BACKUP_ID=//p' "$HOME/.config/systemd/user/yamaguchi-acceptance-probe.service.d/backup-id.conf")" ;;
    "journalctl"*) echo "AC-1     PASS     stub verdict line" ;;
esac
exit 0
"""


def directives(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]


class UnitFileTest(unittest.TestCase):
    def test_the_service_runs_the_deployed_copy_with_the_job_id_as_one_word(self) -> None:
        lines = directives(UNIT_FILE)
        self.assertIn("ExecStart=/usr/bin/python3 -I %h/.local/lib/yamaguchi-acceptance/yamaguchi_acceptance_probe.py --backup-id ${YAMAGUCHI_BACKUP_ID}", lines)
        self.assertIn("Type=oneshot", lines)
        self.assertEqual([line for line in lines if "Development" in line or "/home/" in line], [], "the unit names no checkout and no home directory")

    def test_the_timer_fires_daily_in_utc_and_catches_up(self) -> None:
        lines = directives(TIMER_FILE)
        self.assertIn("OnCalendar=*-*-* 23:30:00 UTC", lines)
        self.assertIn("Persistent=true", lines)
        self.assertIn("Unit=yamaguchi-acceptance-probe.service", lines)
        self.assertIn("WantedBy=timers.target", lines)


@unittest.skipIf(os.geteuid() == 0, "the deploy script refuses root, which is its own test below")
class DeployTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.home, self.bin, self.log = self.base / "home", self.base / "bin", self.base / "calls.log"
        self.home.mkdir()
        self.bin.mkdir()
        self.log.write_text("")
        for name in ("systemctl", "loginctl", "journalctl"):
            stub = self.bin / name
            stub.write_text(STUB)
            stub.chmod(0o755)
        self.lib = self.home / ".local" / "lib" / "yamaguchi-acceptance"
        self.units = self.home / ".config" / "systemd" / "user"

    def deploy(self, *argv: str, drop: tuple[str, ...] = (), **env: str):
        environment = {"HOME": str(self.home), "USER": "fixture", "PATH": f"{self.bin}:/usr/bin:/bin", "STUB_LOG": str(self.log), "LC_ALL": "C"}
        environment.update(env)
        for name in drop:
            del environment[name]
        return subprocess.run(["/bin/bash", str(DEPLOY), *argv], capture_output=True, text=True, env=environment, check=False)

    def calls(self) -> list[str]:
        return self.log.read_text().splitlines()

    def test_bad_arguments_are_refused_before_the_host_is_read(self) -> None:
        for argv in ((), ("--backup-id",), ("--backup-id", ""), ("--backup-id", "two"), ("--backup-id", "0"), ("--backup-id=-1",), ("--backup-id", "2", "--force")):
            with self.subTest(argv=argv):
                proc = self.deploy(*argv)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn("REFUSE" if argv != ("--backup-id",) else "usage", proc.stderr)
        self.assertEqual(self.calls(), [], "no systemctl, loginctl or journalctl call was made")
        self.assertFalse(self.lib.exists())

    def test_without_linger_nothing_is_installed(self) -> None:
        proc = self.deploy("--backup-id", "2", STUB_LINGER="no")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Linger=no", proc.stderr)
        self.assertFalse(self.lib.exists())
        self.assertFalse(self.units.exists())
        self.assertEqual(self.calls(), [f"loginctl show-user {ME} -p Linger --value"])

    def test_the_user_is_asked_of_the_system_not_of_the_environment(self) -> None:
        # The script read $USER, and under `set -u` an unset USER ended it on an unbound variable before any message.
        proc = self.deploy("--backup-id", "2", drop=("USER",))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.calls()[0], f"loginctl show-user {ME} -p Linger --value")
        self.assertNotEqual(ME, "fixture", "USER in this suite's environment names nobody, so a script that read it would show")

    def test_a_loginctl_that_fails_is_said_so_and_nothing_is_installed(self) -> None:
        proc = self.deploy("--backup-id", "2", STUB_LOGINCTL_RC="1")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(f"loginctl could not read Linger for {ME}", proc.stderr)
        self.assertFalse(self.lib.exists())
        self.assertFalse(self.units.exists())

    def test_it_installs_copies_the_job_id_and_the_timer(self) -> None:
        proc = self.deploy("--backup-id", "7")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("yamaguchi_acceptance_probe.py", "yamaguchi_server_api.py"):
            self.assertEqual((self.lib / name).read_bytes(), (AD_HOC / name).read_bytes())
            self.assertIn(f"sha256 {hashlib.sha256((AD_HOC / name).read_bytes()).hexdigest()} {self.lib / name}", proc.stdout)
        self.assertEqual(sorted(p.name for p in self.lib.iterdir()), ["yamaguchi_acceptance_probe.py", "yamaguchi_server_api.py"], "no .new file is left behind")
        self.assertEqual(os.stat(self.lib).st_mode & 0o777, 0o700)
        self.assertEqual((self.units / "yamaguchi-acceptance-probe.service").read_bytes(), UNIT_FILE.read_bytes())
        self.assertEqual((self.units / "yamaguchi-acceptance-probe.timer").read_bytes(), TIMER_FILE.read_bytes())
        self.assertEqual((self.units / "yamaguchi-acceptance-probe.service.d" / "backup-id.conf").read_text(), "[Service]\nEnvironment=YAMAGUCHI_BACKUP_ID=7\n")
        self.assertEqual(self.calls()[:4], [f"loginctl show-user {ME} -p Linger --value", "systemctl --user daemon-reload", "systemctl --user enable --now yamaguchi-acceptance-probe.timer", "systemctl --user start yamaguchi-acceptance-probe.service"])
        self.assertIn("== job id (drop-in): YAMAGUCHI_BACKUP_ID=7", proc.stdout)
        self.assertIn("stub verdict line", proc.stdout)
        again = self.deploy("--backup-id=8")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("YAMAGUCHI_BACKUP_ID=8", (self.units / "yamaguchi-acceptance-probe.service.d" / "backup-id.conf").read_text())
        if os.path.exists("/usr/bin/python3"):
            # The point of deploying copies: the two files run with nothing else from the checkout.
            isolated = subprocess.run(["/usr/bin/python3", "-I", str(self.lib / "yamaguchi_acceptance_probe.py"), "--help"], capture_output=True, text=True, cwd=str(self.base), env={"PATH": "/usr/bin:/bin"}, check=False)
            self.assertEqual(isolated.returncode, 0, isolated.stderr)
            self.assertIn("--expect-retention", isolated.stdout)

    def test_a_failing_first_run_does_not_abort_the_deploy(self) -> None:
        proc = self.deploy("--backup-id", "2", STUB_START_RC="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("the first run did not read PASS", proc.stderr)
        self.assertIn("== first run", proc.stdout)

    def test_it_never_names_a_checkout_and_refuses_root(self) -> None:
        code = "\n".join(line for line in DEPLOY.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#"))
        self.assertIn('if [[ "$(id -u)" -eq 0 ]]; then', code)
        self.assertNotIn("Development/python", code)
        self.assertNotIn("sudo", code)
        self.assertIn('HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"', code)


if __name__ == "__main__":
    unittest.main()
