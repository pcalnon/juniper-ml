#!/usr/bin/env python3
"""
Server-run backup watchdog: alert when the Yamaguchi job did not run, did not succeed, is stuck, or is held by a pause.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — wip (candidate B for plan §7 criterion 4, "failure notification observed firing";
        promote to util/ + util/systemd/ once Paul picks the alerting architecture)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8, §8.22),
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (§7.6),
         util/duplicati_backup_failure.bash (the user lane's reporter this replaces for the server job)

WHY A POLLING WATCHDOG AND NOT ONLY --run-script-after
    "A backup that silently stops is indistinguishable from one that works." A
    job-level --run-script-after fires only when a run HAPPENS. It is silent in
    exactly the cases that produced the 2026-07-13 six-week blind spot: the
    scheduler never fired, the job definition vanished (the portable-mode /
    different-data-root restart trap presents as "job 2 does not exist"), the
    server is down, or a run hangs. This watchdog asks the server from the
    OUTSIDE, on its own timer, and alerts on any of:

      UNREACHABLE        login/serverstate failed (server down / not listening / the
                         credential below missing, unsafe, or refused with a 401)
      JOB_MISSING        backup --backup-id is not in the server's backup list, or the
                         id given is not a job id at all (the unit's drop-in is missing)
      PAUSED_WITH_QUEUE  ProgramState is Paused and SchedulerQueueIds is non-empty: a run
                         came due and the pause is holding it. Always a fault, whatever
                         the uptime (YAM §8.22.2) -- the 2026-08-30 42.6 h outage
      STATE_UNKNOWN      UNDETERMINED -- serverstate answered without a usable
                         ProgramState / SchedulerQueueIds, so the pause cannot be judged
      NO_RUNS            the job has no run log at all
      NOT_SUCCESS        the newest log entry of ANY operation, or the newest BACKUP, is
                         not ParsedResult=Success (a newer successful Test or Compact must
                         not hide a failed backup)
      STALE              the newest BACKUP began more than --max-age-hours ago, or no
                         Backup entry was found in the pages examined
      STUCK              a task is active and has been running longer than --max-run-hours
      (RUNNING           a task for this job is active and within --max-run-hours: OK, the
                         previous run's age is not judged while the next one is in progress)
      LOG_UNAVAILABLE    UNDETERMINED -- the run log could not be read, or its newest entry
                         is not a JSON run result
      EXCEPTION          UNDETERMINED -- any unexpected failure, still recorded durably

    Freshness is anchored on the newest **Backup** operation (design §7.6, YAM §8.22.3
    gap 2): the log is paged newest-first until a MainOperation=Backup entry appears,
    so a Compact or a Test run does not reset the backup clock. A Paused server with an
    EMPTY queue is not an alert -- a startup-delay pause looks exactly like that -- but
    the OK line names it, and an indefinite pause turns into PAUSED_WITH_QUEUE at the
    next check after a run comes due.

    Durable record FIRST (append-only log + a status file), desktop
    notification best-effort (notify-send may have no session bus). Exit 0 = OK,
    1 = ALERT, 2 = UNDETERMINED (also alerts: an undetermined backup is not a
    verified one), 64 = usage error (argparse's own 2 would read as UNDETERMINED).
    The record line is
        <when> <verdict> <code> backup=<id> <details>
    on one line; yamaguchi_reboot_verify.bash reads its first field as the timestamp.

    The job id has NO default: a rebuilt job is not id 2 (Procedure B's sqlite_sequence
    starts at 1), and a watchdog pointed at the wrong id alerts JOB_MISSING forever (design
    §7.6). The deployed unit passes it from the drop-in that
    util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id> writes. An ABSENT
    --backup-id is judged exactly like an empty one -- ALERT JOB_MISSING, recorded durably --
    and is not a usage error, because a usage error writes no record: when the primary
    checkout was synced past ml#2115 on 2026-10-03, the live timer ran this script through a
    unit that passes no --backup-id, and the 2026-10-04 12:00 check exited 2 with nothing
    written. Run the deploy script immediately after each such sync; it does not need the
    web credential (until that file exists every check records ALERT UNREACHABLE). The same
    rule makes a BARE manual run a real check: it records JOB_MISSING in the live state files
    and notifies, so pass --state-dir and --no-notify to look without touching them.

    The web-UI credential is read in-process from ~/.config/duplicati-backup/web-credential
    (0600) by yamaguchi_server_api.read_credential -- never from the primary checkout's .env,
    never on argv, never in the environment of the notify-send child.

    Not implemented: design §7.6's Dropbox check (`dropbox filestatus` of the newest dlist).
    It needs the dropbox CLI, which no test environment has.

PROVING IT (plan §7: "test it deliberately")
    --base http://127.0.0.1:1 --backup-id <id>   -> UNREACHABLE must alert
    --max-age-hours 0.001 --backup-id <id>       -> STALE must alert (the newest backup is older than ~4 s)
    --backup-id 999                              -> JOB_MISSING must alert
    Each forced alert must land in the log, the status file, and (with a session
    bus) as a critical desktop notification.

    python3 util/ad-hoc/yamaguchi_watchdog.py --backup-id <id>     # normal check
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

JOB_ID = re.compile(r"[1-9][0-9]*")  # always .fullmatch(): `$` would also accept "7\n"
LOG_PAGE_SIZE = 20
LOG_MAX_PAGES = 10


def parse_iso(s):
    """Duplicati timestamps: 2026-08-25T19:14:49.2056618Z or with a numeric offset."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # trim sub-microsecond digits (.NET gives 7) so fromisoformat accepts it
    if "." in s:
        head, tail = s.split(".", 1)
        frac = ""
        rest = ""
        for i, ch in enumerate(tail):
            if ch.isdigit():
                frac += ch
            else:
                rest = tail[i:]
                break
        s = f"{head}.{frac[:6]}{rest}"
    d = dt.datetime.fromisoformat(s)
    if d.tzinfo is None:  # a naive stamp would make the age arithmetic raise TypeError
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def _result(entry):
    """One log entry's parsed run result; {} when its Message is not a JSON result (the old format)."""
    m = entry.get("Message") if isinstance(entry, dict) else None
    if isinstance(m, str):
        try:
            m = json.loads(m)
        except ValueError:
            return {}
    return m if isinstance(m, dict) else {}


def scan_log(tok, backup_id):
    """Page the job's log newest-first until the newest Backup entry.

    Keyset paging, as the shipped web UI does it (LogService.js): ``pagesize=N&offset=<ID of the
    last entry seen>``. Stops at the first MainOperation=Backup entry, at an empty page, at a
    page that brings no entry not already seen (a server that ignores offset), at an entry with
    no ID, or after LOG_MAX_PAGES pages.

    Returns ``(status, examined, newest, newest_backup)``: ``status`` is the HTTP status of the
    last page requested, ``newest`` the parsed result of the newest entry of ANY operation and
    ``newest_backup`` that of the newest Backup -- None when not found.
    """
    newest = None
    examined = 0
    offset = None
    seen = set()
    status = 200
    for _ in range(LOG_MAX_PAGES):
        query = f"pagesize={LOG_PAGE_SIZE}" + ("" if offset is None else f"&offset={offset}")
        status, page = api.req("GET", f"/api/v1/backup/{backup_id}/log?{query}", tok)
        if status != 200 or not isinstance(page, list):
            return status, examined, newest, None
        progressed = False
        last_id = None
        for entry in page:
            entry_id = entry.get("ID") if isinstance(entry, dict) else None
            if entry_id is not None and entry_id in seen:
                continue
            progressed = True
            seen.add(entry_id)
            last_id = entry_id
            examined += 1
            result = _result(entry)
            if newest is None:
                newest = result
            if result.get("MainOperation") == "Backup":
                return status, examined, newest, result
        if not progressed or last_id is None:
            break
        offset = last_id
    return status, examined, newest, None


def _pause_end(state):
    end = state.get("EstimatedPauseEnd")
    if not end or str(end).startswith("0001-01-01"):
        return "indefinite"
    return f"until {end}"


def _run(result):
    return f"{result.get('MainOperation')} {result.get('BeginTime')} ParsedResult={result.get('ParsedResult')}"


def check(args):
    """Return (verdict, code, details) without side effects."""
    backup_id = str(args.backup_id)
    if not JOB_ID.fullmatch(backup_id):
        # Reached by the deployed unit when its drop-in is missing: ${YAMAGUCHI_BACKUP_ID}
        # expands to ONE empty argument. Judged before login -- nothing is read or sent.
        return "ALERT", "JOB_MISSING", f"--backup-id is not a job id (a positive integer; got {len(backup_id)} character(s)) -- redeploy with util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>"
    api.BASE = args.base
    try:
        tok = api.login()
    except SystemExit as exc:
        return "ALERT", "UNREACHABLE", f"login failed: {exc}"
    except Exception as exc:  # noqa: BLE001 -- any transport failure is the alert condition
        return "ALERT", "UNREACHABLE", f"login raised {type(exc).__name__}: {exc}"
    st, state = api.req("GET", "/api/v1/serverstate", tok)
    if st != 200:
        return "ALERT", "UNREACHABLE", f"serverstate -> {st}"
    st, backups = api.req("GET", "/api/v1/backups", tok)
    ids = {str((b.get("Backup", b)).get("ID")) for b in backups} if isinstance(backups, list) else set()
    if backup_id not in ids:
        return "ALERT", "JOB_MISSING", f"backup id {backup_id} not in server list {sorted(ids)} (different data root? see the portable-mode trap)"

    # YAM §8.22: Paused + a non-empty SchedulerQueueIds is always a fault -- the queue entry
    # proves the scheduler fired and the pause is what holds the run. Checked before the
    # active-task and log checks: a held run leaves the log looking merely old.
    program = state.get("ProgramState")
    queue = state.get("SchedulerQueueIds")
    if program not in ("Running", "Paused"):
        return "UNDETERMINED", "STATE_UNKNOWN", f"serverstate ProgramState={program!r} -- cannot tell whether the scheduler can run the job"
    if program == "Paused":
        if not isinstance(queue, list):
            return "UNDETERMINED", "STATE_UNKNOWN", f"ProgramState=Paused but SchedulerQueueIds={queue!r} is not a list -- cannot tell whether a run is being held"
        if queue:
            return "ALERT", "PAUSED_WITH_QUEUE", f"ProgramState=Paused pause={_pause_end(state)} SchedulerQueueIds={json.dumps(queue)} -- a queued run is held by the pause; resume with util/ad-hoc/yamaguchi_server_api.py resume"

    now = dt.datetime.now(dt.timezone.utc)
    active = state.get("ActiveTask")
    if active:
        # serverstate.ActiveTask is a (taskid, backupid) tuple serialized as Item1/Item2
        task_id = active.get("Item1") if isinstance(active, dict) else active
        task_backup = str(active.get("Item2")) if isinstance(active, dict) else None
        st, task = api.req("GET", f"/api/v1/task/{task_id}", tok)
        started = task.get("TaskStarted") if st == 200 else None
        if started:
            hours = (now - parse_iso(started)).total_seconds() / 3600
            if hours > args.max_run_hours:
                return "ALERT", "STUCK", f"task {task_id} (backup {task_backup}) running {hours:.1f} h > {args.max_run_hours} h"
            if task_backup == backup_id:
                # a run in progress is the healthy case; the newest LOG entry is still the
                # previous run and must not be judged stale while this one is going
                return "OK", "RUNNING", f"task {task_id} for backup {task_backup} running {hours:.1f} h"

    st, examined, newest, backup = scan_log(tok, backup_id)
    if newest is None:
        if st != 200:
            return "UNDETERMINED", "LOG_UNAVAILABLE", f"log -> {st}"
        return "ALERT", "NO_RUNS", "job has no run log"
    if not newest:
        # An old-format entry whose Message is not a JSON result: whether it succeeded is unknown.
        return "UNDETERMINED", "LOG_UNAVAILABLE", "the newest log entry carries no JSON run result"
    if newest.get("ParsedResult") != "Success":
        return "ALERT", "NOT_SUCCESS", f"newest log entry {_run(newest)}"
    if backup is None:
        if st != 200:
            return "UNDETERMINED", "LOG_UNAVAILABLE", f"log -> {st} before a Backup entry was found ({examined} entries examined)"
        return "ALERT", "STALE", f"no Backup operation among the newest {examined} log entries (newest is {_run(newest)})"
    result = backup.get("ParsedResult")
    begin = backup.get("BeginTime")
    age_h = (now - parse_iso(begin)).total_seconds() / 3600 if begin else None
    summary = f"newest backup {begin} ParsedResult={result} age={age_h:.1f}h" if age_h is not None else f"newest backup ParsedResult={result} (no BeginTime)"
    if newest is not backup:
        summary += f" (newest log entry: {_run(newest)})"
    if result != "Success":
        return "ALERT", "NOT_SUCCESS", summary
    if age_h is None or age_h > args.max_age_hours:
        return "ALERT", "STALE", f"{summary} > {args.max_age_hours} h"
    if program == "Paused":
        summary += f" ProgramState=Paused pause={_pause_end(state)} queue empty"
    return "OK", "OK", summary


def record(args, verdict, code, details):
    os.makedirs(args.state_dir, exist_ok=True)
    when = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    backup_id = str(args.backup_id) if JOB_ID.fullmatch(str(args.backup_id)) else "INVALID"
    # One record per line: the log is parsed line by line, and its first field is the timestamp.
    details = str(details).replace("\r", " ").replace("\n", " ")
    line = f"{when} {verdict} {code} backup={backup_id} {details}"
    with open(os.path.join(args.state_dir, "server-watchdog.log"), "a") as fh:
        fh.write(line + "\n")
    with open(os.path.join(args.state_dir, "server-watchdog.status"), "w") as fh:
        fh.write(line + "\n")
    if verdict != "OK":
        with open(os.path.join(args.state_dir, "server-failures.log"), "a") as fh:
            fh.write(line + "\n")
        if args.notify and shutil.which("notify-send"):
            # best-effort: no session bus is not a reason to lose the durable record above
            proc = subprocess.run(["notify-send", "--urgency=critical", "Duplicati (Yamaguchi) backup ALERT",
                                   f"{code}: {details}\n{when}\nsee {args.state_dir}/server-failures.log"],
                                  check=False, capture_output=True)
            line += f" [notify-send rc={proc.returncode}]"
    return line


class _UsageParser(argparse.ArgumentParser):
    """Usage errors exit 64 (EX_USAGE, the client's EXIT_USAGE), so that one never reads as UNDETERMINED (2)."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(api.EXIT_USAGE, f"{self.prog}: error: {message}\n")


def main(argv=None):
    ap = _UsageParser(description="alert when the server-run Yamaguchi backup did not run, did not succeed, is stuck, or is held by a pause")
    ap.add_argument("--base", default=api.BASE)
    ap.add_argument("--backup-id", default="", help="the job's numeric id -- no default job: a rebuilt job is not id 2, and an absent or empty id records ALERT JOB_MISSING. The deployed unit passes it from YAMAGUCHI_BACKUP_ID (util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>)")
    ap.add_argument("--max-age-hours", type=float, default=26.0, help="newest BACKUP older than this = STALE (daily job + slack)")
    ap.add_argument("--max-run-hours", type=float, default=6.0, help="an active task older than this = STUCK (full run was 2h12m)")
    ap.add_argument("--state-dir", default=os.path.expanduser("~/.local/state/duplicati"))
    ap.add_argument("--no-notify", dest="notify", action="store_false")
    args = ap.parse_args(argv)

    try:
        verdict, code, details = check(args)
    except Exception as exc:  # noqa: BLE001 -- an undetermined check must still leave a durable record
        verdict, code, details = "UNDETERMINED", "EXCEPTION", f"{type(exc).__name__}: {exc}"
    print(record(args, verdict, code, details))
    return 0 if verdict == "OK" else (1 if verdict == "ALERT" else 2)


if __name__ == "__main__":
    sys.exit(main())
