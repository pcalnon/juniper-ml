#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License

Minimal authenticated client for the Duplicati 2.4.0.0 server REST API on the
Yamaguchi host service (http://127.0.0.1:8300). Exists because
duplicati-server-util exposes no task-abort and no backup-delete verbs, and
takes its secrets on argv, where /proc/*/cmdline shows them to every user.

Auth: POST /api/v1/auth/login with the web-UI password, read in-process from
the credential file below -- never argv, never the environment of this process
or of a child, never printed. The JWT access token is held in memory only and
sent as a Bearer header; every verb goes through login() and req().

CREDENTIAL FILE (B2 of the 2026-10-03 recovery plan; design section 7.6)
    ~/.config/duplicati-backup/web-credential -- mode 0600, owned by the
    operator, who rotates it. DUPLICATI_WEB_CREDENTIAL_FILE overrides the path
    (tests). util/ad-hoc/duplicati_api.py reads the same file through
    read_credential() below: one path, one parser, for both clients.

    Format: the KEY=VALUE line this client used to parse out of the primary
    checkout's world-readable .env (exposure S-5), so the line moves over as is:

        DUPLICATI_WEB_CREDENTIAL=<the web-UI password>

    Exactly one such line; an `export ` prefix is tolerated; blank lines,
    `#` comments and other lines are ignored. The value is literal -- no shell
    expansion, no inline comment -- with surrounding whitespace dropped and ONE
    matching pair of surrounding quotes removed (quote a value whose edges are
    whitespace). Refused, naming the path, mode and owner but never the
    content: a file with ANY group or other permission bit, anything but a
    regular file, more than 64 KiB, no such line, two such lines, an empty
    value.

    This is the WEB-UI password, not the archive passphrase, which lives in
    ~/.config/duplicati-backup/env. Mixing them up fails as a 401 here and as
    "Bad session key" in a restore -- a wrong secret, not a corrupt archive.

Endpoint paths and parameters were checked against the installed 2.4.0.0
assemblies (util/ad-hoc/2026-09-22_duplicati_literal_scan.py finds
/api/v1/serverstate, /serverstate/pause and /serverstate/resume in
Duplicati.WebserverCore.dll), the shipped web UI (ServerStatus.js) and the
vendor client (CommandLine/ServerUtil/Connection.cs at the 2.4.0.0 tag).
None of them was learned by running the server.

Safety: talks only to 127.0.0.1:8300; delete requires --yes; nothing here can
touch files under subdirectories of the destination (Duplicati file backends
list non-recursively, so a job whose TargetURL is the folder root cannot see
or delete Ubuntu/ or the scratch dirs).
"""

import argparse
import json
import os
import pwd
import re
import stat
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8300"
CRED_FILE = "~/.config/duplicati-backup/web-credential"
CRED_FILE_ENV = "DUPLICATI_WEB_CREDENTIAL_FILE"
CRED_KEY = "DUPLICATI_WEB_CREDENTIAL"
CRED_MAX_BYTES = 64 * 1024
_CRED_LINE = re.compile(rf"^(?:export\s+)?{CRED_KEY}=(.*)$")

JOB_VERBS = ("export", "delete", "run", "log")
TASK_VERBS = ("abort", "task")
VERBS = ("status", "serverstate", "pause", "resume", "export", "abort", "delete", "import", "run", "progress", "log", "task")
# Always .fullmatch(): a `$` anchor also matches before a trailing newline, so "7\n" would pass.
JOB_ID = re.compile(r"[1-9][0-9]*")
TASK_ID = re.compile(r"[0-9]+")
EXIT_USAGE = 64  # EX_USAGE -- not argparse's 2, which `serverstate` uses for Paused

VERB_HELP = """\
verbs (exit 0 = done, 1 = the request failed or was refused, 64 = usage error):
  status              server state + running/scheduled tasks + backup list
  serverstate         GET /api/v1/serverstate: ProgramState, the pause (EstimatedPauseEnd),
                      SchedulerQueueIds and ActiveTask. Exit 0 Running, 2 Paused, 1 otherwise.
  pause               POST /api/v1/serverstate/pause -- an INDEFINITE pause. 2.4.0.0 persists
                      it as the server setting paused-until and restores it on every restart
                      and reboot until `resume`: a session that ends between the two leaves
                      the scheduler stopped (the 42.6 h class; the watchdog alerts
                      PAUSED_WITH_QUEUE once a run is queued). Exit 0 only if Paused after.
  resume              POST /api/v1/serverstate/resume -- a queued overdue run starts at once.
                      Exit 0 only if Running after.
  export <id>         the job's configuration JSON on stdout, and nothing else on stdout
  delete <id>         delete a job; --remote-files also deletes its volumes; needs --yes
  run <id>            start the job
  log <id>            newest run results, one JSON line each
  abort <taskid>      abort a task
  task <taskid>       one task's status
  import <file>       create a job from an export-format JSON file
  progress            live progress line of the running task

The job id of export/delete/run/log is REQUIRED and has no default -- a rebuilt job is
not id 2 (Procedure B's sqlite_sequence starts at 1). Give it positionally (`export 7`, as
the design's commands do) or as --backup-id 7.
"""


class CredentialError(SystemExit):
    """The web-credential file is missing, unsafe or malformed.

    A SystemExit subclass on purpose: an importer that lets it propagate exits 1 with the
    message, exactly as the old sys.exit("FATAL: ...") did. The message names the path, the
    mode and the owner -- never any of the file's content.
    """


def credential_path():
    """The credential file both clients read: $DUPLICATI_WEB_CREDENTIAL_FILE, else the 0600 default."""
    return os.environ.get(CRED_FILE_ENV) or os.path.expanduser(CRED_FILE)


def _owner(uid):
    try:
        return f"{pwd.getpwuid(uid).pw_name} (uid {uid})"
    except KeyError:
        return f"uid {uid}"


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    return value


def read_credential(path=None):
    """Return the web-UI password from the credential file; see the module docstring for the contract.

    The mode is checked on the OPENED descriptor before a byte is read, so the check and the read
    are about the same file. O_NONBLOCK keeps a FIFO planted at the path from hanging the caller;
    it is then refused as not a regular file.
    """
    path = path or credential_path()
    flags = os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOCTTY", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        raise CredentialError(f"FATAL: web credential file {path} does not exist -- write it 0600 with one line {CRED_KEY}=<password> (design section 8, P0 step 9)") from None
    except OSError as exc:
        raise CredentialError(f"FATAL: cannot open web credential file {path}: {exc.strerror}") from None
    try:
        # Raw descriptor throughout: os.fdopen would itself raise on a directory, before this check.
        st = os.fstat(fd)
        mode = stat.S_IMODE(st.st_mode)
        if not stat.S_ISREG(st.st_mode):
            raise CredentialError(f"FATAL: web credential file {path} is not a regular file (mode {mode:04o}, owner {_owner(st.st_uid)})")
        if mode & 0o077:
            raise CredentialError(f"FATAL: web credential file {path} is mode {mode:04o}, owner {_owner(st.st_uid)} -- refusing a group- or world-accessible credential; chmod 0600 it, and rotate the password if anyone else could have read it")
        if st.st_size > CRED_MAX_BYTES:
            raise CredentialError(f"FATAL: web credential file {path} is {st.st_size} bytes; it holds one line")
        chunks = []
        while chunk := os.read(fd, CRED_MAX_BYTES + 1):
            chunks.append(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # The exception's own text quotes the offending byte -- a byte of the secret.
        raise CredentialError(f"FATAL: web credential file {path} is not UTF-8 text") from None
    values = [_unquote(m.group(1)) for m in (_CRED_LINE.match(line.strip()) for line in text.splitlines()) if m]
    if len(values) != 1:
        raise CredentialError(f"FATAL: web credential file {path} has {len(values)} {CRED_KEY}= lines; it must have exactly one")
    if not values[0]:
        raise CredentialError(f"FATAL: web credential file {path} has an empty {CRED_KEY}= value")
    return values[0]


def req(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, {"error": exc.read().decode(errors="replace")[:500]}
        finally:
            exc.close()


def login():
    status, body = req("POST", "/api/v1/auth/login", body={"Password": read_credential(), "RememberMe": False})
    if status != 200 or not isinstance(body, dict) or "AccessToken" not in body:
        sys.exit(f"FATAL: login failed ({status}): {json.dumps(body)[:300]}")
    return body["AccessToken"]


class _Parser(argparse.ArgumentParser):
    """Usage errors exit 64, so that exit 2 from `serverstate` can only mean Paused."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def _ok(status):
    return 200 <= status < 300


def _failed(what, status, body):
    """A refused or failed request: the reason on stderr, NOTHING on stdout, exit 1."""
    print(f"{what} failed {status}: {json.dumps(body)[:400]}", file=sys.stderr)
    return 1


def _job_id(ap, args):
    given = {v for v in (args.arg, args.backup_id) if v is not None}
    if not given:
        ap.error(f"{args.cmd} needs the job id -- `{args.cmd} <id>` or `{args.cmd} --backup-id <id>`; there is no default (a rebuilt job is not id 2)")
    if len(given) > 1:
        ap.error(f"{args.cmd}: the positional id {args.arg!r} and --backup-id {args.backup_id!r} disagree")
    (bid,) = given
    if not JOB_ID.fullmatch(bid):
        ap.error(f"{args.cmd}: the job id must be a positive integer, got {bid!r}")
    return bid


def _target(ap, args):
    """Validate the verb's argument BEFORE login, so a usage error reads no credential and sends nothing."""
    if args.cmd in JOB_VERBS:
        return _job_id(ap, args)
    if args.backup_id is not None:
        ap.error(f"{args.cmd} takes no --backup-id")
    if args.cmd in TASK_VERBS:
        if args.arg is None or not TASK_ID.fullmatch(args.arg):
            ap.error(f"{args.cmd} needs a numeric task id, got {args.arg!r}")
        return args.arg
    if args.cmd == "import":
        if args.arg is None:
            ap.error("import needs an export-format JSON file")
        return args.arg
    if args.arg is not None:
        ap.error(f"{args.cmd} is server-wide and takes no argument, got {args.arg!r}")
    return None


def _pause_kind(state):
    """The pause as the API reports it. 2.4.0.0 serialises "no expiry" as the zero DateTime."""
    if state.get("ProgramState") != "Paused":
        return "none"
    end = state.get("EstimatedPauseEnd")
    if not end or str(end).startswith("0001-01-01"):
        return "indefinite -- persisted as paused-until; survives restarts until resume"
    return f"until {end}"


def _show_state(tok):
    """GET /api/v1/serverstate and print it; None when the request failed."""
    status, state = req("GET", "/api/v1/serverstate", tok)
    if status != 200 or not isinstance(state, dict):
        _failed("serverstate", status, state)
        return None
    keys = ("ProgramState", "EstimatedPauseEnd", "SchedulerQueueIds", "ActiveTask", "ProposedSchedule")
    shown = {k: state.get(k) for k in keys}
    shown["Pause"] = _pause_kind(state)
    print(json.dumps(shown, indent=1))
    return state


def _serverstate(tok):
    state = _show_state(tok)
    if state is None:
        return 1
    program = state.get("ProgramState")
    if program == "Running":
        return 0
    if program == "Paused":
        return 2
    print(f"serverstate: unexpected ProgramState {program!r}", file=sys.stderr)
    return 1


def _set_state(tok, verb, want):
    """POST pause/resume, then read the state back: a 200 alone does not prove the scheduler moved."""
    status, body = req("POST", f"/api/v1/serverstate/{verb}", tok)
    if not _ok(status):
        return _failed(verb, status, body)
    state = _show_state(tok)
    if state is None:
        return 1
    if state.get("ProgramState") != want:
        print(f"{verb}: the server answered {status} but ProgramState is {state.get('ProgramState')!r}, not {want!r}", file=sys.stderr)
        return 1
    return 0


def _dispatch(args, target, tok, cfg):
    if args.cmd == "status":
        _, state = req("GET", "/api/v1/serverstate", tok)
        print(json.dumps({k: state.get(k) for k in ("ProgramState", "ActiveTask", "SchedulerQueueIds", "ProposedSchedule")}, indent=1))
        _, backups = req("GET", "/api/v1/backups", tok)
        for b in backups if isinstance(backups, list) else []:
            bb = b.get("Backup", b)
            print(f"backup id={bb.get('ID')} name={bb.get('Name')!r} target={bb.get('TargetURL')}")
            meta = bb.get("Metadata") or {}
            if meta:
                print(f"  meta: LastBackupDate={meta.get('LastBackupDate')} SourceSize={meta.get('SourceFilesSize')}")
        return 0

    if args.cmd == "serverstate":
        return _serverstate(tok)

    if args.cmd == "pause":
        return _set_state(tok, "pause", "Paused")

    if args.cmd == "resume":
        return _set_state(tok, "resume", "Running")

    if args.cmd == "export":
        # stdout is consumed by `json.load` in the design's guard dry-run (P0 step 10), and an
        # empty TargetURL there makes the guard skip its TargetURL check -- so a failure must
        # leave stdout EMPTY and exit non-zero, never print a message where the JSON goes.
        status, body = req("GET", f"/api/v1/backup/{target}/export?export-passwords=false", tok)
        if status != 200:
            return _failed(f"export {target}", status, body)
        print(json.dumps(body, indent=1))
        return 0

    if args.cmd == "abort":
        status, body = req("POST", f"/api/v1/task/{target}/abort", tok)
        if not _ok(status):
            return _failed(f"abort task {target}", status, body)
        print(f"abort task {target}: {status} {body}")
        return 0

    if args.cmd == "delete":
        q = "?delete-remote-files=true" if args.remote_files else ""
        status, body = req("DELETE", f"/api/v1/backup/{target}{q}", tok)
        if not _ok(status):
            return _failed(f"delete backup {target}", status, body)
        print(f"delete backup {target} (remote={args.remote_files}): {status} {body}")
        return 0

    if args.cmd == "import":
        status, body = req("POST", "/api/v1/backups?temporary=false", tok, body=cfg)
        if not _ok(status):
            return _failed("import", status, body)
        print(f"import: {status} {json.dumps(body)[:400]}")
        return 0

    if args.cmd == "run":
        status, body = req("POST", f"/api/v1/backup/{target}/run", tok)
        if not _ok(status):
            return _failed(f"run backup {target}", status, body)
        print(f"run backup {target}: {status} {body}")
        return 0

    if args.cmd == "log":
        # newest-first backup run results for the job; each entry's Message
        # is the serialized result (ParsedResult, ExaminedFiles, Delete/Compact
        # phases, ...) -- the mechanism for verifying retention behavior and
        # per-run outcomes without UI access.
        status, log = req("GET", f"/api/v1/backup/{target}/log?pagesize=5", tok)
        if status != 200 or not isinstance(log, list):
            sys.exit(f"log failed {status}: {log}")
        for entry in log:
            m = entry.get("Message")
            m = json.loads(m) if isinstance(m, str) else (m or {})
            keys = ("ParsedResult", "MainOperation", "BeginTime", "ExaminedFiles",
                    "AddedFiles", "ModifiedFiles", "PartialBackup", "Interrupted")
            row = {k: m.get(k) for k in keys}
            row["DeleteResults"] = bool(m.get("DeleteResults"))
            row["CompactResults"] = bool(m.get("CompactResults"))
            print(json.dumps(row))
        return 0

    if args.cmd == "task":
        status, task = req("GET", f"/api/v1/task/{target}", tok)
        if status != 200:
            return _failed(f"task {target}", status, task)
        print(json.dumps({k: task.get(k) for k in ("Status", "ID", "TaskStarted", "TaskFinished", "ErrorMessage")}, indent=1))
        return 0

    # progress
    _, state = req("GET", "/api/v1/serverstate", tok)
    active = state.get("ActiveTask")
    if not active:
        print("no active task")
        return 0
    _, prog = req("GET", "/api/v1/progressstate", tok)
    keys = ("BackupID", "TaskID", "Phase", "ProcessedFileCount", "ProcessedFileSize", "TotalFileCount", "TotalFileSize", "CurrentFilename", "BackendSpeed")
    print(json.dumps({k: prog.get(k) for k in keys}, indent=1))
    return 0


def main(argv=None):
    ap = _Parser(description="Authenticated client for the Yamaguchi Duplicati server (127.0.0.1:8300).", epilog=VERB_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=VERBS)
    ap.add_argument("arg", nargs="?", help="job id (export/delete/run/log), task id (abort/task) or file (import)")
    ap.add_argument("--backup-id", help="the job id for export/delete/run/log -- required for those verbs (here or positionally), no default")
    ap.add_argument("--remote-files", action="store_true", help="delete: also remove uploaded volumes")
    ap.add_argument("--yes", action="store_true", help="required for delete")
    args = ap.parse_args(argv)
    target = _target(ap, args)

    # Refusals that need no server come before login: no credential read, nothing sent.
    if args.cmd == "delete" and not args.yes:
        sys.exit("refusing: delete requires --yes")
    cfg = None
    if args.cmd == "import":
        try:
            with open(target) as fh:
                cfg = json.load(fh)
        except (OSError, ValueError) as exc:
            sys.exit(f"FATAL: cannot read {target}: {exc}")

    try:
        tok = login()
        return _dispatch(args, target, tok, cfg)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        print(f"FATAL: cannot reach {BASE}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
