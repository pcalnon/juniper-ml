#!/usr/bin/env python3
"""
Daily acceptance probe for the Yamaguchi backup service: one verdict line per criterion, from fixed predicates.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — recovery (Phase D sitting, step 14, and the acceptance window after it)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (section 9: AC-1, AC-2, AC-5, AC-6, AC-7, AC-12, AC-13),
         notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.4 step 14),
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md ("Process change"),
         util/ad-hoc/yamaguchi_server_api.py (the only module this one imports), tests/test_yamaguchi_acceptance_probe.py

WHY THIS EXISTS
    Until 2026-11-11 every check of the Phase D sitting was a command block written by hand for one use, and about a
    third of the sitting's corrections were defects in those blocks, not in the host:

      * a count of a log line the wrapper never writes ("via systemd credential"), read as a failed start;
      * a `--since` cut placed after the event it was meant to include;
      * a warning classifier that matched path text ("http", "report") and mislabelled three file warnings;
      * a parser that met a UTF-8 BOM, read to the end of the stream and reported 0 entries without an error.

    Each predicate below is therefore a pure function with a hermetic test, and four rules hold throughout:

      1. A marker this tool looks for is pinned, in the test suite, against the code that writes it.
      2. A time window is inclusive at its edge and is tested AT the edge.
      3. A warning is classified by its `[Warning-<tag>]` tag, never by the text after it.
      4. An empty or unparseable input is ERROR. It is never PASS and never a count of zero.

WHAT IT JUDGES (design section 9 unless noted; "server" = needs the web API on 127.0.0.1:8300)
    AC-1      the /etc/systemd/system unit, active as `duplicati`, NeedDaemonReload=no, NRestarts=0, up for 24 h
    AC-2      server: job name, TargetURL, 2 sources, 45 filters, schedule 1D at 14:00 UTC, blocksize 1MB
    AC-13     server: run-script-before-required is the installed guard and no other run-script option is set
    OPTIONS   server: the job's option NAMES against the recorded set; retention suspended or restored as ruled;
              keep-time and keep-versions absent; tempdir, aes-version and no-auto-compact as step 11 left them
    AC-5      the watchdog log: three consecutive days whose every record reads OK, and a JOB_MISSING record for a
              deliberate `--backup-id 999` on or after the recovery date
    AC-6a     the snapshot lane: reads the service's data folder, one successful run per day, file mtime = newest run
    AC-6b     NOT judged here, and printed as INFO: "the snapshot appears in the next fileset" needs the dlist,
              which is root's and the passphrase's (util/ad-hoc/2026-11-11_phase_d_finish.bash ac6)
    AC-7      the Dropbox daemon carries the service group; no destination volume reads `unsyncable`; the newest dlist
              is `up to date` within 24 h of its write; the keys directory sits outside the Dropbox root
    AC-12     systemd-analyze security: exposure at or below 2.0 and no unset row outside note AC-12a's accepted set
    RUN       server: the newest finished backup -- its age (26 h, the watchdog's bound; a day more while a task is
              active), its result, its warnings by tag against the 2026-11-08 allow-list, its counts against the
              previous run -- and every backup that began off the schedule
    CENSUS    server: the destination's file count and bytes against the job's own metadata (AGREE or DIVERGE)
    MODES     the destination's (kind, mode, owner) classes, and which dlists changed class since the last run

    Verdicts: PASS, FAIL, PENDING (cannot be proven yet -- it needs more days), ATTN (outside a tolerance the owner has
    not ruled, or an unexplained observation), SKIP (not judged in this run), ERROR (the evidence could not be read),
    INFO. RESULT is FAIL on any FAIL, UNDETERMINED on any ERROR, INCOMPLETE on any PENDING, ATTN or SKIP, else PASS.
    Exit 0 = no FAIL and no ERROR, 1 = at least one FAIL, 2 = at least one ERROR and no FAIL, 64 = usage error.

WHAT IT NEVER PRINTS OR STORES
    A warning's or an error's text (the server's answer to a refused login included), any URL (TargetURL and
    send-http-url included; the latter carries a bearer token), the web credential, or an option value outside
    PRINTABLE_VALUES. It prints counts, tags, option names, file names
    of destination volumes, modes, owners and timestamps. The same holds for the two files it writes.

WHAT IT WRITES (unless --no-write)
    <state-dir>/acceptance.json            the verdicts of this run, replaced atomically
    <state-dir>/acceptance-history.jsonl   one line per run: the snapshot's mtime, the destination's classes, each
                                           dlist's mode and owner, the newest backup's counts
    Nothing else changes anywhere. It starts no unit, runs no Duplicati binary and sends the server only GET requests
    plus the login and the export-token POSTs the read-only export needs.

USAGE
    python3 -I util/ad-hoc/yamaguchi_acceptance_probe.py --backup-id 2
    python3 -I util/ad-hoc/yamaguchi_acceptance_probe.py --backup-id 2 --expect-retention restored   # step 5 read-back
    python3 -I util/ad-hoc/yamaguchi_acceptance_probe.py --backup-id 2 --no-server --no-write       # local criteria only

    The job id has no default, for the watchdog's reason: a rebuilt job is not id 2.
"""

import argparse
import collections
import datetime as dt
import grp
import json
import os
import pwd
import re
import shutil
import socket
import stat
import subprocess
import sys
import urllib.error
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

VERSION = "1.1.0"
SCHEMA = "yamaguchi-acceptance/1"
UTC = dt.timezone.utc

# --- what the design and the sitting's record fix ---------------------------------------------------------------
UNIT = "duplicati.service"
EXPECTED_UNIT_PATH = "/etc/systemd/system/duplicati.service"
SERVICE_USER = "duplicati"
SERVICE_GROUP = "duplicati"
JOB_NAME = "Yamaguchi"
EXPECTED_TARGET = "file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
EXPECTED_SOURCES = 2
EXPECTED_FILTERS = 45
EXPECTED_REPEAT = "1D"
EXPECTED_TIME_OF_DAY = dt.time(14, 0, 0)
GUARD_PATH = "/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash"
RULED_RETENTION = "2W:1D,6M:1W,2Y:1M,5Y:2M"  # owner ruling 2026-10-08
RETENTION_COMBINERS = ("keep-time", "keep-versions")  # never restored: they combine with the policy
# The job's option names after step 11 (running record, 2026-11-07 B6 and 2026-11-08 "12 option names"): the nine
# of B1 less retention-policy, plus the two the sitting set and the two the UI's save added.
BASE_OPTION_NAMES = frozenset({
    "allow-missing-source", "asynchronous-upload-limit", "blocksize", "compression-module", "dblock-size", "encryption-module",
    "no-auto-compact", "tempdir", "run-script-before-required", "aes-version", "send-http-url", "http-report-status-url",
})
# Values step 11 set or AC-2 fixes. no-auto-compact is here because the retention plan depends on it: with it, a
# retention pass deletes dlists only.
EXPECTED_VALUES = {"blocksize": "1MB", "tempdir": "/home/duplicati/.cache/duplicati-tmp", "aes-version": "2", "no-auto-compact": "true"}
# The only option values this tool ever prints. Everything else is a name.
PRINTABLE_VALUES = frozenset({"blocksize", "tempdir", "aes-version", "no-auto-compact", "run-script-before-required", "retention-policy", "keep-time", "keep-versions"})
TRUE_WORDS = frozenset({"true", "1", "on", "yes"})

RECOVERY_DATE = dt.date(2026, 11, 7)  # the service's first start under the new unit; step 10
WATCHDOG_LOG = "server-watchdog.log"
WATCHDOG_LINE = re.compile(r"^(\S+) (OK|ALERT|UNDETERMINED) ([A-Z_]+) backup=(\S+)(?: (.*))?$")
JOB_MISSING_PROBE_ID = "999"

SNAPSHOT_UNIT = "yamaguchi-server-db-snapshot.service"
SNAPSHOT_FILE = "~/.local/state/duplicati-server-db/Duplicati-server.sqlite"
SNAPSHOT_SOURCE = "/home/duplicati/.config/Duplicati/Duplicati-server.sqlite"  # "the new data folder"
SNAPSHOT_SOURCE_LINE = re.compile(r"^source\s*: (.+) \([^()]*\)$")  # yamaguchi_server_db_snapshot.py:110
SNAPSHOT_ENABLED = dt.datetime(2026, 11, 8, 19, 57, 0, tzinfo=UTC)  # step 13's `enable --now`
SNAPSHOT_FIRE = dt.time(13, 45, 0)  # the timer's OnCalendar, UTC

KEYS_DIR = "/mnt/Backups/Ubuntu/_yamaguchi_keys"
DROPBOX_INFO = "~/.dropbox/info.json"
DROPBOX_PIDFILE = "~/.dropbox/dropbox.pid"
FILESTATUS_BATCH = 150

# Note AC-12a's accepted set, as the design lists it.
ACCEPTED_UNSET = frozenset({
    "AmbientCapabilities=", "CapabilityBoundingSet=~CAP_(DAC_*|FOWNER|IPC_OWNER)", "SystemCallFilter=~@privileged", "SystemCallFilter=~@resources",
    "RestrictAddressFamilies=~AF_UNIX", "RestrictAddressFamilies=~AF_(INET|INET6)", "PrivateNetwork=", "PrivateUsers=", "ProtectHome=",
    "RootDirectory=/RootImage=", "RemoveIPC=", "MemoryDenyWriteExecute=", "DeviceAllow=", "IPAddressDeny=", "UMask=",
})
EXPOSURE_GATE = 2.0
EXPOSURE_LINE = re.compile(r"Overall exposure level for \S+: ([0-9]+(?:\.[0-9]+)?)")
MIN_SECURITY_ROWS = 40  # the unit reports 81; far fewer means the output was not what this parser expects

# Owner ruling 2026-11-08 (AC-3): "the Firefox-profile PathNotFound / MetadataProcessFailed class allow-listed".
# A key is the last two dotted segments of the log tag plus the message id, as the sitting's record names them.
ALLOWED_WARNING_TAGS = frozenset({"FilePreFilterProcess.FileEntry-PathNotFound", "MetadataGenerator.Metadata-MetadataProcessFailed", "FileBlockProcessor.FileEntry-PathNotFound"})
ALLOWED_WARNING_SCOPE = ".mozilla/firefox/"  # relative to the backup Source's home
# Duplicati writes "<yyyy-MM-dd HH:mm:ss zz> - [<Level>-<tag>-<id>]: <message>". The tag is accepted only where no `[`
# and no `/` precedes it, so a bracket inside a path (which follows the tag and starts with `/`) is never the tag.
WARNING_TAG = re.compile(r"^[^\[/]*\[Warning-([^\]\s]+)\]:")
BASELINE_BYTES = 301_072_989_629  # run 20261107T212908Z, the AC-3 rebaseline (owner ruling 2026-11-08)
COUNT_TOLERANCE = 0.10  # per run, against the previous run -- open question Q1, not yet ruled
SIZE_TOLERANCE = 0.05  # against the baseline -- AC-3's own size tolerance
MAX_RUN_AGE_HOURS = 26.0  # the watchdog's --max-age-hours default: a daily job plus slack
SCHEDULE_SLACK = dt.timedelta(minutes=5)
PRECEDING_WINDOW = dt.timedelta(minutes=15)
# yamaguchi_server_api.login()'s refusal: `FATAL: login failed (<status>): <the server's answer>`. Only the status is kept.
LOGIN_FAILED = re.compile(r"^FATAL: login failed \(([^()\s]+)\)")
LOG_PAGE_SIZE = 20
LOG_MAX_PAGES = 40

VERDICTS = ("PASS", "FAIL", "PENDING", "ATTN", "SKIP", "ERROR", "INFO")
EXIT_FAIL, EXIT_ERROR = 1, 2


class Finding:
    """One criterion's verdict: what a reader pastes, and the facts behind it."""

    __slots__ = ("criterion", "verdict", "summary", "facts")

    def __init__(self, criterion, verdict, summary, facts=None):
        if verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {verdict!r}")
        self.criterion, self.verdict, self.summary, self.facts = criterion, verdict, summary, facts or {}

    def as_dict(self):
        return {"id": self.criterion, "verdict": self.verdict, "summary": self.summary, "facts": self.facts}

    def line(self):
        return f"{self.criterion:<8} {self.verdict:<8} {self.summary}"


def settle(fails=(), errors=(), pending=(), attn=()):
    """The verdict a criterion earns: a failure outranks unread evidence, which outranks "not yet"."""
    if fails:
        return "FAIL"
    if errors:
        return "ERROR"
    if pending:
        return "PENDING"
    if attn:
        return "ATTN"
    return "PASS"


def parse_iso(text):
    """A .NET or ISO-8601 stamp as an aware datetime; None when it is not one. Seven fractional digits are cut to six."""
    if not isinstance(text, str) or not text.strip():
        return None
    s = text.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    m = re.match(r"^(.*?\.\d{6})\d*(.*)$", s)
    if m:
        s = m.group(1) + m.group(2)
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo is not None else d.replace(tzinfo=UTC)


def utc_stamp(when):
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if when else "unknown"


def hours_minutes(seconds):
    if seconds is None:
        return "unknown"
    seconds = int(seconds)
    return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m"


def parse_properties(text):
    """`systemctl show` output as a dict. A BOM and blank lines are dropped; a line without `=` is ignored."""
    props = {}
    for line in text.lstrip("\ufeff").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip():
            props[key.strip()] = value.strip()
    return props


def unix_property(value):
    """`@1794043744` (systemctl --timestamp=unix) as an aware datetime; None for an unset or unreadable stamp."""
    m = re.fullmatch(r"@(\d+)(?:\.\d+)?", value or "")
    return dt.datetime.fromtimestamp(int(m.group(1)), UTC) if m and int(m.group(1)) > 0 else None


# --- AC-1 ---------------------------------------------------------------------------------------------------------
def judge_ac1(props, now, min_hours=24.0):
    if not props:
        return Finding("AC-1", "ERROR", f"systemctl show {UNIT} returned no properties")
    fails, pending = [], []
    want = {"FragmentPath": EXPECTED_UNIT_PATH, "User": SERVICE_USER, "ActiveState": "active", "SubState": "running", "NeedDaemonReload": "no", "NRestarts": "0"}
    for key, expected in want.items():
        if props.get(key) != expected:
            fails.append(f"{key}={props.get(key, '<absent>')} (want {expected})")
    since = unix_property(props.get("ActiveEnterTimestamp"))
    hours = None
    if since is None:
        fails.append("ActiveEnterTimestamp is unset or unreadable")
    else:
        hours = (now - since).total_seconds() / 3600
        if hours < min_hours:  # exactly 24 h satisfies "over 24 h"
            pending.append(f"up {hours:.1f} h of the {min_hours:g} h AC-1 asks for")
    facts = {"properties": {k: props.get(k) for k in want}, "active_since": utc_stamp(since), "up_hours": None if hours is None else round(hours, 2)}
    if fails or pending:
        return Finding("AC-1", settle(fails, pending=pending), "; ".join(fails + pending), facts)
    return Finding("AC-1", "PASS", f"unit {EXPECTED_UNIT_PATH}, user {SERVICE_USER}, active/running, NeedDaemonReload=no, NRestarts=0, up {hours:.1f} h (>= {min_hours:g})", facts)


# --- the job's export: AC-2, AC-13, OPTIONS -------------------------------------------------------------------------
def option_map(export):
    """Option name (leading dashes dropped, lower case) -> every value the job stores under it."""
    backup = export.get("Backup") if isinstance(export, dict) else None
    settings = backup.get("Settings") if isinstance(backup, dict) else None
    options = {}
    for setting in settings if isinstance(settings, list) else []:
        name = setting.get("Name") if isinstance(setting, dict) else None
        if isinstance(name, str) and name.strip("-").strip():
            options.setdefault(name.strip().lstrip("-").lower(), []).append(setting.get("Value"))
    return options


def _is_export(export):
    return isinstance(export, dict) and isinstance(export.get("Backup"), dict) and isinstance(export["Backup"].get("Settings"), list)


def shown(name, values):
    """An option for a summary line: the value only where PRINTABLE_VALUES allows it."""
    if name in PRINTABLE_VALUES:
        return f"{name}={values[0] if len(values) == 1 else values}"
    return f"{name} (value withheld)"


def judge_ac2(export):
    if not _is_export(export):
        return Finding("AC-2", "ERROR", "the export carries no Backup.Settings list -- not a job export")
    backup, schedule, options = export["Backup"], export.get("Schedule") or {}, option_map(export)
    fails = []
    if backup.get("Name") != JOB_NAME:
        fails.append(f"job name is not {JOB_NAME!r}")
    target = backup.get("TargetURL")
    target_ok = isinstance(target, str) and target.rstrip("/") == EXPECTED_TARGET
    if not target_ok:
        fails.append("TargetURL is not the design's destination (value withheld)")
    sources, filters = backup.get("Sources"), backup.get("Filters")
    n_sources = len(sources) if isinstance(sources, list) else None
    n_filters = len(filters) if isinstance(filters, list) else None
    if n_sources != EXPECTED_SOURCES:
        fails.append(f"{n_sources} sources (want {EXPECTED_SOURCES})")
    if n_filters != EXPECTED_FILTERS:
        fails.append(f"{n_filters} filters (want {EXPECTED_FILTERS})")
    if schedule.get("Repeat") != EXPECTED_REPEAT:
        fails.append(f"schedule Repeat={schedule.get('Repeat')!r} (want {EXPECTED_REPEAT})")
    anchor = parse_iso(schedule.get("Time"))
    time_of_day = anchor.astimezone(UTC).time().replace(microsecond=0) if anchor else None
    if time_of_day != EXPECTED_TIME_OF_DAY:
        fails.append(f"schedule time of day is {time_of_day} UTC (want {EXPECTED_TIME_OF_DAY})")
    blocksize = options.get("blocksize")
    if blocksize is None or len(blocksize) != 1 or str(blocksize[0]).strip().upper() != EXPECTED_VALUES["blocksize"].upper():
        fails.append(f"blocksize is {blocksize} (want {EXPECTED_VALUES['blocksize']})")
    facts = {"name_ok": backup.get("Name") == JOB_NAME, "target_ok": target_ok, "sources": n_sources, "filters": n_filters, "repeat": schedule.get("Repeat"),
             "time_of_day_utc": str(time_of_day) if time_of_day else None, "schedule_anchor_date": anchor.astimezone(UTC).date().isoformat() if anchor else None, "blocksize": blocksize}
    if fails:
        return Finding("AC-2", "FAIL", "; ".join(fails), facts)
    return Finding("AC-2", "PASS", f"name={JOB_NAME} target=match sources={n_sources} filters={n_filters} repeat={EXPECTED_REPEAT} at {time_of_day}Z (anchor date {facts['schedule_anchor_date']}) blocksize={blocksize[0]}", facts)


def judge_ac13(export):
    if not _is_export(export):
        return Finding("AC-13", "ERROR", "the export carries no Backup.Settings list -- not a job export")
    options = option_map(export)
    run_scripts = sorted(name for name in options if name.startswith("run-script-"))
    required = options.get("run-script-before-required")
    fails = []
    if required != [GUARD_PATH]:
        fails.append(f"run-script-before-required is {required} (want exactly {GUARD_PATH})")
    others = [name for name in run_scripts if name != "run-script-before-required"]
    if others:
        fails.append(f"other run-script options are set: {', '.join(others)}")
    facts = {"run_script_options": run_scripts, "required": required}
    if fails:
        return Finding("AC-13", "FAIL", "; ".join(fails), facts)
    return Finding("AC-13", "PASS", f"run-script-before-required={GUARD_PATH}; no other run-script option among {len(options)} option names", facts)


def retention_state(export):
    """'restored' when the job carries retention-policy, else 'suspended'; None when the export is unusable."""
    if not _is_export(export):
        return None
    return "restored" if "retention-policy" in option_map(export) else "suspended"


def judge_options(export, expect_retention="either"):
    if not _is_export(export):
        return Finding("OPTIONS", "ERROR", "the export carries no Backup.Settings list -- not a job export")
    options = option_map(export)
    names = set(options)
    fails = []
    duplicated = sorted(name for name, values in options.items() if len(values) > 1)
    if duplicated:
        fails.append(f"set more than once: {', '.join(duplicated)}")
    for name in RETENTION_COMBINERS:
        if name in names:
            fails.append(f"{shown(name, options[name])} is set -- it combines with the policy and is never restored")
    state = "restored" if "retention-policy" in names else "suspended"
    if state == "restored" and options["retention-policy"] != [RULED_RETENTION]:
        fails.append(f"{shown('retention-policy', options['retention-policy'])} is not the ruled {RULED_RETENTION}")
    if expect_retention in ("suspended", "restored") and state != expect_retention:
        fails.append(f"retention is {state}, expected {expect_retention}")
    unexpected = sorted(names - BASE_OPTION_NAMES - {"retention-policy"} - set(RETENTION_COMBINERS))
    missing = sorted(BASE_OPTION_NAMES - names)
    if unexpected:
        fails.append(f"option names not in the recorded set: {', '.join(unexpected)}")
    if missing:
        fails.append(f"recorded option names now absent: {', '.join(missing)}")
    for name, expected in EXPECTED_VALUES.items():
        values = options.get(name)
        if values is None:
            continue  # absent: reported once, by the missing-names check
        actual = str(values[0]).strip() if len(values) == 1 else None
        if name == "no-auto-compact":
            good = actual is not None and actual.lower() in TRUE_WORDS
        else:
            good = actual is not None and actual.lower() == expected.lower()
        if not good:
            fails.append(f"{shown(name, values)} (want {expected})")
    facts = {"names": sorted(names), "retention": state, "unexpected": unexpected, "missing": missing, "duplicated": duplicated,
             "values": {name: options[name] for name in sorted(names & PRINTABLE_VALUES)}}
    if fails:
        return Finding("OPTIONS", "FAIL", "; ".join(fails), facts)
    tail = f"retention-policy={RULED_RETENTION}" if state == "restored" else "retention suspended (no retention-policy)"
    return Finding("OPTIONS", "PASS", f"{len(names)} option names, all in the recorded set; {tail}; keep-time and keep-versions absent; tempdir, aes-version, no-auto-compact as set", facts)


# --- AC-5 -----------------------------------------------------------------------------------------------------------
def parse_watchdog_log(text):
    """(records, unparsed): each record is (when, verdict, code, backup). `when` keeps the log's own UTC offset."""
    records, unparsed = [], 0
    for line in text.lstrip("\ufeff").splitlines():
        if not line.strip():
            continue
        m = WATCHDOG_LINE.match(line)
        when = None
        if m:
            try:
                when = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                when = None
        if when is None:
            unparsed += 1
            continue
        records.append((when, m.group(2), m.group(3), m.group(4)))
    return records, unparsed


def judge_ac5(log_text, backup_id, now, need_days=3, probe_id=JOB_MISSING_PROBE_ID, recovered_on=RECOVERY_DATE, max_gap_hours=36.0):
    if log_text is None:
        return Finding("AC-5", "ERROR", f"the watchdog log {WATCHDOG_LOG} could not be read")
    records, unparsed = parse_watchdog_log(log_text)
    mine = [r for r in records if r[3] == str(backup_id)]
    if not mine:
        return Finding("AC-5", "ERROR", f"no watchdog record for backup={backup_id} ({len(records)} records, {unparsed} unparsed lines)", {"records": len(records), "unparsed": unparsed})
    by_day = collections.defaultdict(list)
    for when, verdict, code, _backup in mine:
        by_day[when.date()].append((verdict, code))
    newest_when = max(r[0] for r in mine)
    newest_day = newest_when.date()
    streak, days, day = 0, [], newest_day
    while day in by_day and all(verdict == "OK" for verdict, _code in by_day[day]):
        streak += 1
        days.append(f"{day.isoformat()} {'+'.join(sorted({code for _verdict, code in by_day[day]}))}")
        day -= dt.timedelta(days=1)
    probe_seen = sorted(utc_stamp(when) for when, verdict, code, backup in records if verdict == "ALERT" and code == "JOB_MISSING" and backup == str(probe_id) and when.date() >= recovered_on)
    age_h = (now - newest_when).total_seconds() / 3600
    newest_codes = "+".join(sorted({f"{verdict} {code}" for verdict, code in by_day[newest_day]}))
    facts = {"streak_days": streak, "days": days, "newest_record": utc_stamp(newest_when), "newest_reads": newest_codes, "job_missing_probe": probe_seen, "unparsed_lines": unparsed,
             "running_days": sum(1 for d in days if "RUNNING" in d)}
    fails, pending = [], []
    if age_h > max_gap_hours:
        fails.append(f"the newest record is {age_h:.1f} h old (> {max_gap_hours:g} h): the watchdog is not checking")
    if streak == 0:
        fails.append(f"the newest check, {newest_day.isoformat()}, reads {newest_codes}")
    elif streak < need_days:
        pending.append(f"OK on {streak} consecutive day(s) of {need_days}: {', '.join(reversed(days))}")
    if not probe_seen:
        pending.append(f"no JOB_MISSING record for a deliberate --backup-id {probe_id} since {recovered_on.isoformat()}")
    if fails or pending:
        return Finding("AC-5", settle(fails, pending=pending), "; ".join(fails + pending), facts)
    return Finding("AC-5", "PASS", f"OK on {streak} consecutive days ({', '.join(reversed(days[:need_days]))}); JOB_MISSING fired for --backup-id {probe_id} at {probe_seen[-1]}", facts)


# --- AC-6a ----------------------------------------------------------------------------------------------------------
def parse_journal(text):
    """journalctl -o json lines as (when, job_type, job_result, message) tuples; (records, unparsed)."""
    records, unparsed = [], 0
    for line in text.lstrip("\ufeff").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            when = dt.datetime.fromtimestamp(int(row["__REALTIME_TIMESTAMP"]) / 1e6, UTC)
        except (ValueError, KeyError, TypeError):
            unparsed += 1
            continue
        message = row.get("MESSAGE")
        records.append((when, row.get("JOB_TYPE"), row.get("JOB_RESULT"), message if isinstance(message, str) else ""))
    return records, unparsed


def last_due_fire(now, fire=SNAPSHOT_FIRE, grace=dt.timedelta(minutes=15)):
    """The newest daily fire that must have finished by `now`: today's once `grace` has passed, else yesterday's."""
    today = dt.datetime.combine(now.astimezone(UTC).date(), fire, UTC)
    return today if now >= today + grace else today - dt.timedelta(days=1)


def judge_ac6a(snapshot, journal_text, now, expected_source=SNAPSHOT_SOURCE, enabled=SNAPSHOT_ENABLED, min_days=2, mtime_slack=180.0, me=None):
    """`snapshot` is None (no file) or a dict: size, mtime (epoch), mode, owner."""
    if journal_text is None:
        return Finding("AC-6a", "ERROR", f"the journal of {SNAPSHOT_UNIT} could not be read")
    records, unparsed = parse_journal(journal_text)
    records = [r for r in records if r[0] >= enabled]  # inclusive: a run AT the enable instant counts
    if not records:
        return Finding("AC-6a", "ERROR", f"no journal record of {SNAPSHOT_UNIT} since {utc_stamp(enabled)} ({unparsed} unparsed lines)")
    done = sorted(when for when, job_type, result, _msg in records if job_type == "start" and result == "done")
    failed = sorted(when for when, job_type, result, _msg in records if job_type == "start" and result not in (None, "done"))
    sources = [(when, m.group(1)) for when, _t, _r, msg in records for m in [SNAPSHOT_SOURCE_LINE.match(msg)] if m]
    fails, errors, pending = [], [], []
    if not sources:
        errors.append("no `source :` line in the journal -- the script's output format changed, or its output is not journalled")
    wrong = sorted({path for _when, path in sources if path != expected_source})
    if wrong:
        fails.append(f"{len(wrong)} run(s) read another source than {expected_source}")
    due = last_due_fire(now)
    streak = 0
    if not done:
        fails.append("no successful run in the journal")
    else:
        if done[-1] < due:
            fails.append(f"the fire due at {utc_stamp(due)} has no successful run (newest {utc_stamp(done[-1])})")
        ran = {when.date() for when in done}
        day = done[-1].date()
        while day in ran:
            streak += 1
            day -= dt.timedelta(days=1)
        if streak < min_days:
            pending.append(f"{streak} consecutive day(s) with a successful run; `advances daily` needs {min_days}")
    if failed and (not done or failed[-1] > done[-1]):
        fails.append(f"the newest start job failed at {utc_stamp(failed[-1])}")
    facts = {"successful_runs": [utc_stamp(w) for w in done[-10:]], "failed_runs": [utc_stamp(w) for w in failed[-10:]], "consecutive_days": streak,
             "sources_seen": len(sources), "source_ok": bool(sources) and not wrong, "due": utc_stamp(due), "unparsed_lines": unparsed}
    if snapshot is None:
        fails.append("the snapshot file does not exist")
    else:
        mtime = dt.datetime.fromtimestamp(snapshot["mtime"], UTC)
        facts["snapshot"] = {"size": snapshot["size"], "mtime": utc_stamp(mtime), "mode": f"{snapshot['mode']:04o}", "owner": snapshot["owner"]}
        if done and abs((mtime - done[-1]).total_seconds()) > mtime_slack:  # exactly the slack still matches
            fails.append(f"the snapshot's mtime {utc_stamp(mtime)} is not the newest run's ({utc_stamp(done[-1])})")
        if snapshot["size"] <= 4096:
            fails.append(f"the snapshot is {snapshot['size']} bytes -- a stub, not a database")
        if snapshot["mode"] != 0o600 or (me is not None and snapshot["owner"] != me):
            fails.append(f"the snapshot is mode {snapshot['mode']:04o} owner {snapshot['owner']} (the lane writes 0600, owner {me})")
    if fails or errors or pending:
        return Finding("AC-6a", settle(fails, errors, pending), "; ".join(fails + errors + pending), facts)
    snap = facts["snapshot"]
    return Finding("AC-6a", "PASS", f"reads {expected_source}; a successful run on each of the last {streak} days, newest {utc_stamp(done[-1])}; snapshot {snap['size']} B, mtime {snap['mtime']}, {snap['mode']} {snap['owner']}", facts)


# --- AC-7 -----------------------------------------------------------------------------------------------------------
def parse_proc_status(text):
    """(gids, groups) from /proc/<pid>/status: the four Gid fields and the supplementary Groups, as int sets."""
    gids, groups = set(), set()
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        if key == "Gid":
            gids = {int(v) for v in value.split() if v.isdigit()}
        elif key == "Groups":
            groups = {int(v) for v in value.split() if v.isdigit()}
    return gids, groups


def parse_filestatus(text, paths):
    """`dropbox filestatus FILE...` output -> {path: status} for the paths asked about.

    The CLI prints "%-*s %s" % (indent, path + ':', status) per file. No status contains a colon, so the LAST colon
    of a line is the format's own, whatever the path holds. A line that names no requested path is ignored.
    """
    wanted, statuses = set(paths), {}
    for line in text.lstrip("\ufeff").splitlines():
        head, sep, tail = line.rpartition(":")
        if sep and head in wanted and tail.strip():
            statuses[head] = tail.strip()
    return statuses


def kind_of(name):
    for kind in ("dlist", "dblock", "dindex"):
        if f".{kind}." in name:
            return kind
    return "other"


def dlist_stamp(name):
    """The UTC start stamp a dlist's name carries; None for any other file."""
    m = re.fullmatch(r"duplicati-(\d{8}T\d{6})Z\.dlist\..+", name)
    return dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=UTC) if m else None


def newest_dlist(entries):
    """The entry of the dlist with the newest name stamp; None when the listing holds no dlist."""
    dlists = [(dlist_stamp(e["name"]), e) for e in entries if dlist_stamp(e["name"]) is not None]
    return max(dlists, key=lambda pair: pair[0])[1] if dlists else None


def judge_ac7(daemons, service_gid, entries, statuses, now, keys_dir_real, dropbox_roots, service_user=SERVICE_USER, grace_hours=24.0):
    """`daemons`: [{pid, gids, groups}]; `entries`: destination files (name, mtime, owner); `statuses`: {name: status}."""
    fails, errors, pending = [], [], []
    facts = {"daemons": [{"pid": d["pid"], "via": "primary" if service_gid in d["gids"] else ("supplementary" if service_gid in d["groups"] else "absent")} for d in daemons]}
    if not daemons:
        fails.append("no Dropbox daemon is running for this user")
    lacking = [d["pid"] for d in daemons if service_gid not in d["gids"] | d["groups"]]
    if lacking:
        fails.append(f"Dropbox daemon pid {', '.join(map(str, lacking))} does not carry gid {service_gid} ({SERVICE_GROUP})")
    if not entries:
        errors.append("the destination listing is empty")
    known = {e["name"]: statuses[e["name"]] for e in entries if e["name"] in statuses}
    histogram = collections.Counter(known.values())
    unread = len(entries) - len(known)
    facts.update({"files": len(entries), "status_counts": dict(sorted(histogram.items())), "status_unread": unread})
    if entries and not known:
        errors.append("`dropbox filestatus` returned a status for none of the destination's files")
    elif unread:
        errors.append(f"`dropbox filestatus` returned no status for {unread} of {len(entries)} files")
    unsyncable = [e for e in entries if known.get(e["name"]) == "unsyncable"]
    if unsyncable:
        by_kind = collections.Counter(kind_of(e["name"]) for e in unsyncable)
        service_owned = sum(1 for e in unsyncable if e["owner"] == service_user)
        facts["unsyncable"] = {"by_kind": dict(sorted(by_kind.items())), "owned_by_service_user": service_owned, "dlists": sorted(e["name"] for e in unsyncable if kind_of(e["name"]) == "dlist")}
        fails.append(f"{len(unsyncable)} volume(s) read `unsyncable` ({', '.join(f'{n} {k}' for k, n in sorted(by_kind.items()))}); {service_owned} of them are owned by {service_user}")
    newest = newest_dlist(entries)
    if newest is None:
        if entries:
            errors.append("the destination holds no dlist")
    else:
        status = known.get(newest["name"])
        age_h = (now - dt.datetime.fromtimestamp(newest["mtime"], UTC)).total_seconds() / 3600
        facts["newest_dlist"] = {"name": newest["name"], "status": status, "age_hours": round(age_h, 2), "owner": newest["owner"]}
        if status == "up to date":
            pass
        elif status == "unsyncable":
            pass  # already a failure above; no window makes an unsyncable file sync
        elif status is None:
            pass  # already an error above
        elif age_h <= grace_hours:  # exactly 24 h is still inside "within 24 h of its write"
            pending.append(f"the newest dlist reads `{status}` {age_h:.1f} h after its write (it has {grace_hours:g} h)")
        else:
            fails.append(f"the newest dlist reads `{status}` {age_h:.1f} h after its write (> {grace_hours:g} h)")
    facts["keys_dir"] = keys_dir_real
    if keys_dir_real is None:
        fails.append(f"{KEYS_DIR} does not exist")
    elif not dropbox_roots:
        errors.append(f"no Dropbox root could be read from {DROPBOX_INFO}")
    else:
        inside = [root for root in dropbox_roots if os.path.commonpath([keys_dir_real, root]) == root]
        if inside:
            fails.append("the keys directory is inside the Dropbox root")
    if fails or errors or pending:
        return Finding("AC-7", settle(fails, errors, pending), "; ".join(fails + errors + pending), facts)
    via = ", ".join(sorted({d["via"] for d in facts["daemons"]}))
    return Finding("AC-7", "PASS", f"daemon carries gid {service_gid} ({via}); {len(entries)} volumes, 0 unsyncable; newest dlist {newest['name']} is up to date; keys directory outside the Dropbox root", facts)


# --- AC-12 ----------------------------------------------------------------------------------------------------------
def judge_ac12(rows, overall_text, gate=EXPOSURE_GATE, accepted=ACCEPTED_UNSET):
    """`rows` is the parsed `systemd-analyze security --json=short` list; `overall_text` the plain form's output."""
    if not isinstance(rows, list) or len(rows) < MIN_SECURITY_ROWS:
        return Finding("AC-12", "ERROR", f"systemd-analyze returned {len(rows) if isinstance(rows, list) else 'no'} rows (expected at least {MIN_SECURITY_ROWS})")
    odd = [r for r in rows if not isinstance(r, dict) or not isinstance(r.get("name"), str) or not isinstance(r.get("set"), bool)]
    if odd:
        return Finding("AC-12", "ERROR", f"{len(odd)} of {len(rows)} rows carry no boolean `set` or no `name` -- the JSON shape changed")
    m = EXPOSURE_LINE.search(overall_text or "")
    if not m:
        return Finding("AC-12", "ERROR", "no `Overall exposure level` line in systemd-analyze's output")
    exposure = float(m.group(1))
    unset = sorted(r["name"] for r in rows if r["set"] is False)
    outside = sorted(set(unset) - accepted)
    fails = []
    if exposure > gate:  # "at or below 2.0": exactly the gate passes
        fails.append(f"exposure {exposure} is above {gate}")
    if outside:
        fails.append(f"unset rows outside note AC-12a's accepted set: {', '.join(outside)}")
    facts = {"exposure": exposure, "rows": len(rows), "unset": unset, "outside_accepted": outside}
    if fails:
        return Finding("AC-12", "FAIL", "; ".join(fails), facts)
    return Finding("AC-12", "PASS", f"exposure {exposure} <= {gate}; {len(unset)} unset rows, all in note AC-12a's accepted set of {len(accepted)}", facts)


# --- RUN ------------------------------------------------------------------------------------------------------------
def warning_key(text):
    """`FilePreFilterProcess.FileEntry-PathNotFound` from a warning's `[Warning-<tag>-<id>]`; None without a tag.

    The key is taken from the tag alone. Nothing after the closing bracket is read here.
    """
    m = WARNING_TAG.match(text) if isinstance(text, str) else None
    if not m:
        return None
    tag, sep, message_id = m.group(1).rpartition("-")
    if not sep or not tag or not message_id:
        return None
    return ".".join(tag.split(".")[-2:]) + "-" + message_id


def classify_warnings(warnings, actual_length, scope_paths):
    """Counts only: {'total', 'allowed', 'by_key': {key: n}, 'not_allowed': {key: n}}.

    A warning is allowed when its TAG is in ALLOWED_WARNING_TAGS and the path it names lies under one of
    `scope_paths` (the ruling covers the Firefox profile, not every vanished file). The text is consulted for that
    one path test, after the tag has decided the class, and is never returned.
    """
    listed = [w for w in warnings if isinstance(w, str)] if isinstance(warnings, list) else []
    total = actual_length if isinstance(actual_length, int) and actual_length > len(listed) else len(listed)
    by_key, not_allowed, allowed = collections.Counter(), collections.Counter(), 0
    for text in listed:
        key = warning_key(text)
        label = key or "untagged"
        by_key[label] += 1
        body = text[WARNING_TAG.match(text).end():] if key else ""
        in_scope = any(re.search(r"(?<![\w./-])" + re.escape(scope), body) for scope in scope_paths)
        if key in ALLOWED_WARNING_TAGS and in_scope:
            allowed += 1
        else:
            not_allowed[label if key not in ALLOWED_WARNING_TAGS else f"{label} (outside the ruled path scope)"] += 1
    if total > len(listed):
        not_allowed["not listed in the result (truncated)"] += total - len(listed)
    return {"total": total, "allowed": allowed, "by_key": dict(sorted(by_key.items())), "not_allowed": dict(sorted(not_allowed.items()))}


def summarize_entry(entry, scope_paths):
    """One job-log entry reduced to what the predicates need. Warning and error TEXT does not survive this call."""
    message = entry.get("Message") if isinstance(entry, dict) else None
    if isinstance(message, str):
        try:
            message = json.loads(message.lstrip("\ufeff"))
        except ValueError:
            message = None
    raised = bool(entry.get("Exception")) if isinstance(entry, dict) else False  # its presence; the text is never kept
    if not isinstance(message, dict):
        return {"id": entry.get("ID") if isinstance(entry, dict) else None, "operation": None, "exception": raised}
    begin, end = parse_iso(message.get("BeginTime")), parse_iso(message.get("EndTime"))
    errors, errors_actual = message.get("Errors"), message.get("ErrorsActualLength")
    n_errors = max(len(errors) if isinstance(errors, list) else 0, errors_actual if isinstance(errors_actual, int) else 0)
    delete = message.get("DeleteResults") if isinstance(message.get("DeleteResults"), dict) else {}
    deleted_sets = delete.get("DeletedSets")
    n_deleted_sets = max(len(deleted_sets) if isinstance(deleted_sets, list) else 0, delete.get("DeletedSetsActualLength") if isinstance(delete.get("DeletedSetsActualLength"), int) else 0)
    test = message.get("TestResults") if isinstance(message.get("TestResults"), dict) else {}
    return {
        "id": entry.get("ID"), "operation": message.get("MainOperation"), "result": message.get("ParsedResult"), "begin": begin, "end": end,
        "seconds": (end - begin).total_seconds() if begin and end else None,
        "examined": message.get("ExaminedFiles"), "examined_bytes": message.get("SizeOfExaminedFiles"), "added": message.get("AddedFiles"), "modified": message.get("ModifiedFiles"),
        "deleted": message.get("DeletedFiles"), "not_processed": message.get("NotProcessedFiles"), "files_with_error": message.get("FilesWithError"),
        "partial": message.get("PartialBackup"), "interrupted": message.get("Interrupted"),
        "warnings": classify_warnings(message.get("Warnings"), message.get("WarningsActualLength"), scope_paths), "errors": n_errors, "deleted_sets": n_deleted_sets,
        "compact": bool(message.get("CompactResults")) or bool(delete.get("CompactResults")), "test_result": test.get("ParsedResult"), "exception": raised,
    }


def unreadable_before_first_backup(entries):
    """How many of the newest log entries, ahead of the newest Backup, carry no readable result.

    A run that died may be logged as text rather than as a result. Such an entry is not a Backup to the scan, so
    the newest readable Backup would be judged in its place and a failed run would pass unseen.
    """
    count = 0
    for entry in entries:
        if entry.get("operation") == "Backup":
            break
        count += entry.get("operation") is None
    return count


def percent(new, old):
    return None if not isinstance(new, int) or not isinstance(old, int) or isinstance(new, bool) or isinstance(old, bool) or old <= 0 else (new - old) / old


def judge_run(backups, retention, active_task=None, unreadable_newer=0, baseline_bytes=BASELINE_BYTES, count_tolerance=COUNT_TOLERANCE, size_tolerance=SIZE_TOLERANCE, now=None, max_age_hours=MAX_RUN_AGE_HOURS):
    """`backups`: summarize_entry() results with operation == 'Backup', newest first. `retention`: suspended/restored/None.

    `unreadable_newer`: unreadable_before_first_backup() of the whole scan. `now`: when given, the newest finished
    backup must have begun within `max_age_hours`, or one day more while a task is active (a running backup has no
    result yet, so the newest FINISHED one is the day before's). Without it a clean run from weeks ago would pass.
    """
    if not backups:
        return Finding("RUN", "ERROR", "no finished Backup among the job-log entries examined")
    newest, previous = backups[0], backups[1] if len(backups) > 1 else None
    w = newest["warnings"]
    fails, errors, attn, notes = [], [], [], []
    age_hours = None
    if now is not None and newest["begin"] is None:
        errors.append("the newest backup carries no readable BeginTime, so its age cannot be judged")
    elif now is not None:
        age_hours = (now - newest["begin"]).total_seconds() / 3600
        limit = max_age_hours + (24.0 if active_task else 0.0)
        if age_hours > limit:  # exactly the limit is inside it
            fails.append(f"it began {age_hours:.1f} h ago and no newer backup has finished (a daily job allows {limit:.0f} h{' while a task is active' if active_task else ''})")
    if unreadable_newer:
        errors.append(f"{unreadable_newer} log entr{'y' if unreadable_newer == 1 else 'ies'} newer than this backup carry no readable result -- a run that died may be among them")
    if newest.get("exception"):
        fails.append("the backup's log entry carries an exception")
    if newest["result"] == "Success":
        if w["total"]:
            fails.append(f"ParsedResult=Success but {w['total']} warning(s) are recorded")
    elif newest["result"] == "Warning":
        if w["total"] and not w["not_allowed"]:
            notes.append(f"{w['allowed']} warning(s), all allow-listed by the 2026-11-08 ruling ({', '.join(f'{k} x{n}' for k, n in w['by_key'].items())})")
        elif w["not_allowed"]:
            fails.append("warnings outside the allow-list: " + ", ".join(f"{k} x{n}" for k, n in w["not_allowed"].items()))
        else:
            fails.append("ParsedResult=Warning with no warning listed in the result")
    else:
        fails.append(f"ParsedResult={newest['result']}")
    if newest["errors"]:
        fails.append(f"{newest['errors']} error(s)")
    for key, label in (("not_processed", "NotProcessedFiles"), ("files_with_error", "FilesWithError")):
        if newest[key] not in (0, None):
            fails.append(f"{label}={newest[key]}")
        elif newest[key] is None:
            fails.append(f"{label} is absent from the result")
    if newest["partial"] or newest["interrupted"]:
        fails.append(f"PartialBackup={newest['partial']} Interrupted={newest['interrupted']}")
    if newest["compact"]:
        fails.append("a compact ran (the job sets no-auto-compact)")
    if newest["test_result"] not in (None, "Success"):
        fails.append(f"the post-backup verification reads {newest['test_result']}")
    if newest["deleted_sets"] and retention != "restored":
        fails.append(f"the run deleted {newest['deleted_sets']} fileset(s) while retention is {retention or 'unknown'}")
    elif newest["deleted_sets"]:
        notes.append(f"retention deleted {newest['deleted_sets']} fileset(s)")
    drift = percent(newest["examined"], previous["examined"]) if previous else None
    size_drift = percent(newest["examined_bytes"], baseline_bytes)
    if drift is not None and abs(drift) > count_tolerance:  # exactly the tolerance is inside it
        attn.append(f"examined files moved {drift:+.1%} against the previous run (provisional tolerance {count_tolerance:.0%}; question Q1 is unruled)")
    if size_drift is not None and abs(size_drift) > size_tolerance:
        attn.append(f"examined bytes are {size_drift:+.1%} against the 2026-11-08 baseline (AC-3's {size_tolerance:.0%}; question Q1 is unruled)")
    facts = {"begin": utc_stamp(newest["begin"]), "duration": hours_minutes(newest["seconds"]), "result": newest["result"], "warnings": w, "errors": newest["errors"],
             "examined": newest["examined"], "examined_bytes": newest["examined_bytes"], "count_drift": None if drift is None else round(drift, 4),
             "size_vs_baseline": None if size_drift is None else round(size_drift, 4), "deleted_sets": newest["deleted_sets"], "test_result": newest["test_result"],
             "active_task": active_task, "retention": retention, "age_hours": None if age_hours is None else round(age_hours, 2)}
    head = f"backup {utc_stamp(newest['begin'])} ({hours_minutes(newest['seconds'])}) ParsedResult={newest['result']}, examined {newest['examined']}"
    if drift is not None:
        head += f" ({drift:+.1%} vs the previous run)"
    if active_task:
        notes.append(f"a task is active now ({active_task}); this is the newest FINISHED backup")
    return Finding("RUN", settle(fails, errors, attn=attn), "; ".join([head] + fails + errors + attn + notes), facts)


def seconds_off_schedule(begin, time_of_day):
    """How far a start is from the daily slot, in seconds, around the clock (23:59:58 is 2 s from 00:00:00)."""
    slot = dt.datetime.combine(begin.astimezone(UTC).date(), time_of_day, UTC)
    delta = abs((begin - slot).total_seconds()) % 86400
    return min(delta, 86400 - delta)


def judge_schedule(entries, time_of_day=EXPECTED_TIME_OF_DAY, since=RECOVERY_DATE, slack=SCHEDULE_SLACK, window=PRECEDING_WINDOW):
    """Backups that began off the daily slot, each with the operations logged in the 15 minutes before it.

    `entries`: summarize_entry() results of EVERY operation examined, newest first.
    """
    backups = [e for e in entries if e.get("operation") == "Backup" and e.get("begin") and e["begin"].date() >= since]
    if not backups:
        return Finding("OFFSCHED", "ERROR", f"no Backup since {since.isoformat()} among the job-log entries examined")
    off = []
    for run in backups:
        if seconds_off_schedule(run["begin"], time_of_day) <= slack.total_seconds():  # exactly the slack is on schedule
            continue
        before = collections.Counter(str(e.get("operation")) for e in entries if e is not run and e.get("begin") and run["begin"] - window <= e["begin"] <= run["begin"] and e.get("operation") != "Backup")
        off.append({"begin": utc_stamp(run["begin"]), "result": run["result"], "preceded_by": dict(sorted(before.items()))})
    facts = {"backups_examined": len(backups), "off_schedule": off}
    if not off:
        return Finding("OFFSCHED", "PASS", f"all {len(backups)} backups examined since {since.isoformat()} began within {int(slack.total_seconds() // 60)} min of {time_of_day}Z", facts)
    parts = [f"{o['begin']} (preceded by {', '.join(f'{k} x{n}' for k, n in o['preceded_by'].items()) or 'no logged operation'})" for o in off]
    return Finding("OFFSCHED", "ATTN", f"{len(off)} of {len(backups)} backups began off the {time_of_day}Z slot: " + "; ".join(parts), facts)


# --- CENSUS and MODES -----------------------------------------------------------------------------------------------
def judge_census(entries, metadata, active_task=None):
    if not entries:
        return Finding("CENSUS", "ERROR", "the destination listing is empty")
    if not isinstance(metadata, dict) or metadata.get("TargetFilesCount") is None or metadata.get("TargetFilesSize") is None:
        return Finding("CENSUS", "ERROR", "the job's metadata carries no TargetFilesCount / TargetFilesSize")
    n_files, n_bytes = len(entries), sum(e["size"] for e in entries)
    kinds = collections.Counter(kind_of(e["name"]) for e in entries)
    agree = str(metadata["TargetFilesCount"]) == str(n_files) and str(metadata["TargetFilesSize"]) == str(n_bytes)
    facts = {"files": n_files, "bytes": n_bytes, "kinds": dict(sorted(kinds.items())), "server_files": str(metadata["TargetFilesCount"]), "server_bytes": str(metadata["TargetFilesSize"]), "agree": agree}
    head = f"{n_files} files = {kinds['dlist']} dlist + {kinds['dblock']} dblock + {kinds['dindex']} dindex + {kinds['other']} other, {n_bytes} B"
    if agree:
        return Finding("CENSUS", "PASS", f"{head}; AGREE with the job's metadata", facts)
    if active_task:
        return Finding("CENSUS", "PENDING", f"{head}; differs from the job's metadata while a task is active ({active_task}) -- judged after it finishes", facts)
    return Finding("CENSUS", "FAIL", f"{head}; DIVERGE from the job's metadata ({facts['server_files']} files, {facts['server_bytes']} B)", facts)


def file_class(entry):
    return f"{entry['mode']:o} {entry['owner']}:{entry['group']}"


def judge_modes(entries, previous_dlists=None):
    """INFO: the destination's classes, and the dlists whose class differs from the previous run's record."""
    if not entries:
        return Finding("MODES", "ERROR", "the destination listing is empty")
    classes = collections.Counter(f"{kind_of(e['name'])} {file_class(e)}" for e in entries)
    dlists = {e["name"]: file_class(e) for e in entries if kind_of(e["name"]) == "dlist"}
    changed = sorted(f"{name}: {previous_dlists[name]} -> {cls}" for name, cls in dlists.items() if previous_dlists and name in previous_dlists and previous_dlists[name] != cls)
    facts = {"classes": dict(sorted(classes.items())), "dlists": dlists, "changed_since_previous": changed}
    summary = "; ".join(f"{n} {cls}" for cls, n in sorted(classes.items()))
    if changed:
        summary += f"; {len(changed)} dlist(s) changed class since the previous run: " + ", ".join(changed)
    return Finding("MODES", "INFO", summary, facts)


# --- collectors: everything below reads the host; nothing below decides a verdict ------------------------------------
def run_cmd(argv, timeout=120):
    """(rc, stdout, stderr); rc is None when the binary is missing or the call timed out. Never raises."""
    env = dict(os.environ, LC_ALL="C.UTF-8", LANG="C.UTF-8", SYSTEMD_PAGER="", SYSTEMD_COLORS="0", NO_COLOR="1")
    try:
        proc = subprocess.run(argv, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, check=False, env=env)
    except FileNotFoundError:
        return None, "", f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return None, "", f"{argv[0]}: timed out after {timeout}s"
    return proc.returncode, proc.stdout, proc.stderr


def tool(name):
    return shutil.which(name) or f"/usr/bin/{name}"


def collect_unit():
    rc, out, _err = run_cmd([tool("systemctl"), "show", UNIT, "--timestamp=unix", "-p", "FragmentPath", "-p", "User", "-p", "NeedDaemonReload", "-p", "NRestarts", "-p", "ActiveState", "-p", "SubState", "-p", "ActiveEnterTimestamp"])
    return parse_properties(out) if rc == 0 else {}


def collect_watchdog_log(state_dir):
    try:
        with open(os.path.join(state_dir, WATCHDOG_LOG), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def collect_snapshot():
    path = os.path.expanduser(SNAPSHOT_FILE)
    try:
        st = os.stat(path)
    except OSError:
        return None
    return {"size": st.st_size, "mtime": st.st_mtime, "mode": stat.S_IMODE(st.st_mode), "owner": user_name(st.st_uid)}


def collect_snapshot_journal(now):
    # The cut is a day before the first record the predicate keeps; the predicate applies the real, inclusive bound.
    since = (min(SNAPSHOT_ENABLED, now - dt.timedelta(days=15)) - dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S UTC")
    rc, out, _err = run_cmd([tool("journalctl"), "-u", SNAPSHOT_UNIT, f"--since={since}", "-o", "json", "--no-pager"])
    return out if rc == 0 else None


def user_name(uid):
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def group_name(gid):
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def collect_destination(dest):
    """Names and metadata of the destination's files. No file there is opened."""
    entries = []
    try:
        with os.scandir(dest) as it:
            for item in it:
                st = item.stat(follow_symlinks=False)
                if stat.S_ISREG(st.st_mode):
                    entries.append({"name": item.name, "size": st.st_size, "mtime": st.st_mtime, "mode": stat.S_IMODE(st.st_mode), "owner": user_name(st.st_uid), "group": group_name(st.st_gid)})
    except OSError:
        return []
    return sorted(entries, key=lambda e: e["name"])


def collect_daemons():
    """Dropbox daemons of this user: the pidfile's pid and any process whose comm is `dropbox`."""
    pids = set()
    try:
        with open(os.path.expanduser(DROPBOX_PIDFILE), encoding="ascii", errors="replace") as fh:
            pids.add(int(fh.read().strip()))
    except (OSError, ValueError):
        pass  # no pidfile, or not a number: the /proc scan below still finds a running daemon
    try:
        candidates = [name for name in os.listdir("/proc") if name.isdigit()]
    except OSError:
        candidates = []
    me = os.getuid()
    for name in candidates:
        try:
            if os.stat(f"/proc/{name}").st_uid != me:
                continue
            with open(f"/proc/{name}/comm", encoding="utf-8", errors="replace") as fh:
                if fh.read().strip() == "dropbox":
                    pids.add(int(name))
        except OSError:
            continue
    daemons = []
    for pid in sorted(pids):
        try:
            with open(f"/proc/{pid}/comm", encoding="utf-8", errors="replace") as fh:
                if fh.read().strip() != "dropbox":
                    continue  # a stale pidfile naming a recycled pid
            with open(f"/proc/{pid}/status", encoding="utf-8", errors="replace") as fh:
                gids, groups = parse_proc_status(fh.read())
        except OSError:
            continue
        daemons.append({"pid": pid, "gids": gids, "groups": groups})
    return daemons


def collect_filestatus(dest, names):
    statuses = {}
    for start in range(0, len(names), FILESTATUS_BATCH):
        paths = [os.path.join(dest, name) for name in names[start:start + FILESTATUS_BATCH]]
        rc, out, _err = run_cmd([tool("dropbox"), "filestatus", *paths])
        if rc != 0:
            continue
        for path, status in parse_filestatus(out, paths).items():
            statuses[os.path.basename(path)] = status
    return statuses


def collect_dropbox_roots():
    try:
        with open(os.path.expanduser(DROPBOX_INFO), encoding="utf-8-sig") as fh:
            info = json.load(fh)
    except (OSError, ValueError):
        return []
    roots = [account.get("path") for account in info.values() if isinstance(account, dict)] if isinstance(info, dict) else []
    return [os.path.realpath(root) for root in roots if isinstance(root, str) and root]


def collect_security():
    rc_json, out_json, _err = run_cmd([tool("systemd-analyze"), "security", "--no-pager", "--json=short", UNIT])
    rc_text, out_text, _err = run_cmd([tool("systemd-analyze"), "security", "--no-pager", UNIT])
    try:
        rows = json.loads(out_json.lstrip("\ufeff")) if rc_json == 0 and out_json.strip() else None
    except ValueError:
        rows = None
    return rows, out_text if rc_text == 0 else ""


def fetch_export(tok, backup_id):
    """(status, body) of the job's export with passwords withheld. Mirrors yamaguchi_server_api._export; prints nothing."""
    status, op, _body = api._single_operation_token(tok, "export")
    if not op:
        return status, None
    query = urllib.parse.urlencode({"export-passwords": "false", "token": op})
    status, body = api.req("GET", f"/api/v1/backup/{backup_id}/export?{query}", tok)
    return status, body if status == 200 else None


def fetch_log(tok, backup_id, want_backups, scope_paths, page_size=LOG_PAGE_SIZE, max_pages=LOG_MAX_PAGES):
    """Summaries of the job log, newest first, until `want_backups` Backup entries are in hand. Keyset paging, bounded."""
    entries, seen, offset, backups = [], set(), None, 0
    for _ in range(max_pages):
        query = f"pagesize={page_size}" + ("" if offset is None else f"&offset={offset}")
        status, page = api.req("GET", f"/api/v1/backup/{backup_id}/log?{query}", tok)
        if status != 200 or not isinstance(page, list):
            return status, entries
        progressed, last_id = False, None
        for entry in page:
            entry_id = entry.get("ID") if isinstance(entry, dict) else None
            if entry_id is None or entry_id in seen:
                continue
            seen.add(entry_id)
            progressed, last_id = True, entry_id
            summary = summarize_entry(entry, scope_paths)
            entries.append(summary)
            backups += summary.get("operation") == "Backup"
        if backups >= want_backups or not progressed or last_id is None:
            break
        offset = last_id
    return 200, entries


def refusal_reason(exc):
    """Why the API client stopped, without anything the SERVER wrote.

    A credential refusal is the client's own sentence -- a path, a mode, an owner, never the file's content -- and is
    kept. A failed login carries the server's answer after the status; that answer is dropped, like every other
    error text this probe meets.
    """
    text = exc.code if isinstance(exc.code, str) else ""
    if isinstance(exc, api.CredentialError):
        return f"credential refused: {text[:200]}"
    m = LOGIN_FAILED.match(text)
    if m:
        return f"the server refused the login (status {m.group(1)}); its answer is not printed"
    return "the API client stopped; its message is not printed"


def collect_server(base, backup_id, want_backups, scope_paths):
    """Everything the server-side criteria read, or {'error': reason}. The credential never leaves the API client."""
    api.BASE = base
    try:
        tok = api.login()
        status, state = api.req("GET", "/api/v1/serverstate", tok)
        if status != 200 or not isinstance(state, dict):
            return {"error": f"serverstate -> {status}"}
        status, cfg = api.req("GET", f"/api/v1/backup/{backup_id}", tok)
        if status != 200 or not isinstance(cfg, dict) or not isinstance(cfg.get("Backup"), dict):
            return {"error": f"GET backup {backup_id} -> {status}"}
        status, export = fetch_export(tok, backup_id)
        if export is None:
            return {"error": f"export {backup_id} -> {status}"}
        status, entries = fetch_log(tok, backup_id, want_backups, scope_paths)
        if status != 200:
            return {"error": f"log -> {status} after {len(entries)} entries"}
    except SystemExit as exc:  # the API client's refusals: a missing or unsafe credential file, a failed login
        return {"error": refusal_reason(exc)}
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as exc:
        return {"error": f"cannot reach {base}: {type(exc).__name__}"}
    active = state.get("ActiveTask")
    task = f"task {active.get('Item1')} for backup {active.get('Item2')}" if isinstance(active, dict) else (str(active) if active else None)
    target = cfg["Backup"].get("TargetURL")
    return {"export": export, "entries": entries, "metadata": cfg["Backup"].get("Metadata") or {}, "active_task": task, "program_state": state.get("ProgramState"),
            "dest": urllib.parse.unquote(urllib.parse.urlparse(target).path) if isinstance(target, str) and target.startswith("file://") else None}


# --- assembly -------------------------------------------------------------------------------------------------------
def overall(findings):
    verdicts = {f.verdict for f in findings}
    if "FAIL" in verdicts:
        return "FAIL", EXIT_FAIL
    if "ERROR" in verdicts:
        return "UNDETERMINED", EXIT_ERROR
    if verdicts & {"PENDING", "ATTN", "SKIP"}:
        return "INCOMPLETE", 0
    return "PASS", 0


def read_previous_dlists(state_dir):
    """The dlist classes the previous run recorded; None when there is no usable previous record."""
    try:
        with open(os.path.join(state_dir, "acceptance-history.jsonl"), encoding="utf-8") as fh:
            lines = [line for line in fh if line.strip()]
        return json.loads(lines[-1]).get("dlists") if lines else None
    except (OSError, ValueError, AttributeError):
        return None


def write_outputs(state_dir, document, history_row):
    os.makedirs(state_dir, mode=0o700, exist_ok=True)
    path = os.path.join(state_dir, "acceptance.json")
    fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(document, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(path + ".new", path)
    fd = os.open(os.path.join(state_dir, "acceptance-history.jsonl"), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(history_row, sort_keys=True) + "\n")


def run_table(backups, limit):
    lines = []
    for i, run in enumerate(backups[:limit]):
        older = backups[i + 1] if i + 1 < len(backups) else None
        drift = percent(run["examined"], older["examined"]) if older else None
        w = run["warnings"]
        warn = f"W={w['total']}" + (f" (allow-listed {w['allowed']})" if w["total"] else "")
        slot = "scheduled" if run["begin"] and seconds_off_schedule(run["begin"], EXPECTED_TIME_OF_DAY) <= SCHEDULE_SLACK.total_seconds() else "OFF-SCHEDULE"
        lines.append(f"  run {utc_stamp(run['begin'])}  {hours_minutes(run['seconds']):>7}  {str(run['result']):<8} {warn:<22} E={run['errors']}  examined={run['examined']}" + (f" ({drift:+.1%})" if drift is not None else "") + f"  {slot}")
    return lines


class _UsageParser(argparse.ArgumentParser):
    """Usage errors exit 64, so that 1 can only mean FAIL and 2 only UNDETERMINED."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(api.EXIT_USAGE, f"{self.prog}: error: {message}\n")


def main(argv=None):
    ap = _UsageParser(description="one verdict line per acceptance criterion of the Yamaguchi backup service (read-only)")
    ap.add_argument("--backup-id", required=True, help="the job's numeric id -- no default: a rebuilt job is not id 2")
    ap.add_argument("--base", default=api.BASE)
    ap.add_argument("--no-server", action="store_true", help="skip the criteria that need the web API (AC-2, AC-13, OPTIONS, RUN, OFFSCHED, CENSUS)")
    ap.add_argument("--expect-retention", choices=("either", "suspended", "restored"), default="either", help="step 5's read-back passes `restored`")
    ap.add_argument("--dest", default=None, help="destination directory; default: derived from the job's TargetURL, or the design's path with --no-server")
    ap.add_argument("--state-dir", default=os.path.expanduser("~/.local/state/duplicati"))
    ap.add_argument("--no-write", action="store_true", help="print only: write neither acceptance.json nor the history line")
    ap.add_argument("--runs", type=int, default=8, help="how many finished backups to list and to scan for off-schedule starts")
    ap.add_argument("--recovered-on", default=RECOVERY_DATE.isoformat(), help="a JOB_MISSING record counts for AC-5 from this date")
    args = ap.parse_args(argv)
    if not api.JOB_ID.fullmatch(str(args.backup_id)):
        ap.error(f"--backup-id must be a positive integer, got {args.backup_id!r}")
    if args.runs < 2:
        ap.error("--runs must be at least 2: the newest backup is judged against the previous one")
    try:
        recovered_on = dt.date.fromisoformat(args.recovered_on)
    except ValueError:
        ap.error(f"--recovered-on must be YYYY-MM-DD, got {args.recovered_on!r}")

    now = dt.datetime.now(UTC)
    me = user_name(os.getuid())
    home = os.path.expanduser("~").rstrip("/") + "/"
    scope_paths = [home + ALLOWED_WARNING_SCOPE]
    print(f"== yamaguchi acceptance probe {VERSION} at {utc_stamp(now)} on {socket.gethostname()} as {me} (backup id {args.backup_id}{', no server' if args.no_server else ''})")

    server = {"error": "--no-server"} if args.no_server else collect_server(args.base, args.backup_id, args.runs, scope_paths)
    findings = [judge_ac1(collect_unit(), now)]
    backups = []
    if "error" in server:
        verdict = "SKIP" if args.no_server else "ERROR"
        for criterion in ("AC-2", "AC-13", "OPTIONS"):
            findings.append(Finding(criterion, verdict, f"not judged: {server['error']}"))
    else:
        findings += [judge_ac2(server["export"]), judge_ac13(server["export"]), judge_options(server["export"], args.expect_retention)]
        backups = [e for e in server["entries"] if e.get("operation") == "Backup"]
    findings.append(judge_ac5(collect_watchdog_log(args.state_dir), args.backup_id, now, recovered_on=recovered_on))
    snapshot = collect_snapshot()
    findings.append(judge_ac6a(snapshot, collect_snapshot_journal(now), now, me=me))
    # INFO, not SKIP: this probe can never judge it, and a SKIP on every run would hold RESULT at INCOMPLETE for good.
    findings.append(Finding("AC-6b", "INFO", "root's to judge, not this probe's: `the snapshot appears in the next fileset` reads a dlist -- util/ad-hoc/2026-11-11_phase_d_finish.bash ac6"))

    dest = args.dest or server.get("dest") or urllib.parse.urlparse(EXPECTED_TARGET).path
    entries = collect_destination(dest)
    try:
        service_gid = grp.getgrnam(SERVICE_GROUP).gr_gid
    except KeyError:
        service_gid = None
    if service_gid is None:
        findings.append(Finding("AC-7", "ERROR", f"this host has no group {SERVICE_GROUP}"))
    else:
        keys_real = os.path.realpath(KEYS_DIR) if os.path.isdir(KEYS_DIR) else None
        findings.append(judge_ac7(collect_daemons(), service_gid, entries, collect_filestatus(dest, [e["name"] for e in entries]), now, keys_real, collect_dropbox_roots()))
    findings.append(judge_ac12(*collect_security()))
    if "error" in server:
        verdict = "SKIP" if args.no_server else "ERROR"
        for criterion in ("RUN", "OFFSCHED", "CENSUS"):
            findings.append(Finding(criterion, verdict, f"not judged: {server['error']}"))
    else:
        findings.append(judge_run(backups, retention_state(server["export"]), server["active_task"], unreadable_before_first_backup(server["entries"]), now=now))
        findings.append(judge_schedule(server["entries"], since=recovered_on))
        findings.append(judge_census(entries, server["metadata"], server["active_task"]))
    findings.append(judge_modes(entries, read_previous_dlists(args.state_dir)))

    for finding in findings:
        print(finding.line())
    for line in run_table(backups, args.runs):
        print(line)
    result, code = overall(findings)
    counts = collections.Counter(f.verdict for f in findings)
    print(f"RESULT: {result} ({', '.join(f'{counts[v]} {v}' for v in VERDICTS if counts[v])})")

    if not args.no_write:
        document = {"schema": SCHEMA, "version": VERSION, "generated": utc_stamp(now), "host": socket.gethostname(), "backup_id": str(args.backup_id), "result": result,
                    "server": "skipped" if args.no_server else ("error" if "error" in server else "read"), "criteria": [f.as_dict() for f in findings]}
        newest = backups[0] if backups else None
        history = {"generated": utc_stamp(now), "result": result, "verdicts": {f.criterion: f.verdict for f in findings},
                   "snapshot": None if snapshot is None else {"size": snapshot["size"], "mtime": utc_stamp(dt.datetime.fromtimestamp(snapshot["mtime"], UTC))},
                   "classes": dict(collections.Counter(f"{kind_of(e['name'])} {file_class(e)}" for e in entries)),
                   "dlists": {e["name"]: file_class(e) for e in entries if kind_of(e["name"]) == "dlist"},
                   "newest_backup": None if newest is None else {"begin": utc_stamp(newest["begin"]), "result": newest["result"], "examined": newest["examined"], "examined_bytes": newest["examined_bytes"], "seconds": newest["seconds"]}}
        write_outputs(args.state_dir, document, history)
        print(f"wrote {os.path.join(args.state_dir, 'acceptance.json')} and one history line")
    return code


if __name__ == "__main__":
    sys.exit(main())
