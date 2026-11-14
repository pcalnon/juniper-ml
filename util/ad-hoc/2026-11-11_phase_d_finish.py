#!/usr/bin/env python3
"""
Phase D's remaining root steps as verbs with fixed predicates: the AC-4 drills, the retention aside copy, AC-6b.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — recovery (Phase D sitting, step 14)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.4 step 14),
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (section 9: AC-4, AC-6),
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md ("Process change"),
         util/ad-hoc/2026-11-09_ac4_restore_drill.py (the AC-4 driver this runs and judges),
         util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py (the retention port this reuses),
         util/ad-hoc/2026-11-11_phase_d_finish.bash (the wrapper to run it through), tests/test_phase_d_finish.py

Run it through the wrapper, which pins the interpreter (the root shell of this sitting had conda's python first on
PATH three times), empties the environment down to an allow-list and points TMPDIR at the run root:

    bash util/ad-hoc/2026-11-11_phase_d_finish.bash plan [--at INSTANT]   any user; read-only
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash drill 1            root
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash aside              root; refuses until drill 1 has PASSED
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash drill 2            root
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash ac6                root
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash status --backup-id 2    root; runs the probe as the Source's user
    bash util/ad-hoc/2026-11-11_phase_d_finish.bash shred --run-dir DIR     root; a run directory kept after a failure

VERBS
    plan     A PREDICTION of which of the destination's existing filesets the first retention pass deletes once
             `retention-policy` is restored. It reads the dlist names (no file is opened) and applies the port of
             Duplicati 2.4.0.0's RetentionPolicyRemover in retention_table.py to the real list. The pass is evaluated
             at every instant of the next 60 hours at which a fileset meets a frame's edge, not at a sample of
             times. It assumes every fileset is a full backup and that no clock change lies between a fileset and
             the pass: Duplicati keeps a partial fileset inside a frame without measuring the next interval from it,
             and it compares its own DateTime values. Names cannot show either, so `aside` does not depend on it.

    drill N  AC-4's drill N (1 = duplicati-20260918T140000Z, pre-recovery; 2 = duplicati-20261107T212908Z, the first
             post-recovery fileset). If <run-root>/ac4-drillN.out exists it is ADOPTED, never re-run: the owner may
             have run the driver by hand. Otherwise the driver runs, unless the server reports an active task (the
             driver refuses its own result when a dlist lands mid-restore, so a drill started during a backup is
             wasted). Either way the output is read strictly: one driver run prints each of its lines once, in a
             fixed order, RESULT last, and never a FATAL beside a RESULT -- an output that breaks any of that is an
             ERROR and nothing in it is judged. Then the pass rule is RECOMPUTED from the parsed numbers and must
             agree with the driver's own RESULT line and exit code, and a verdict record is written. On PASS the run
             directory, which holds the decrypted dlist and the restored sample, is shredded; on anything else it is
             kept as evidence.

    aside    Copies EVERY dlist in the destination to a root-only 0700 directory outside the Dropbox root, keeping
             what `cp -p` keeps (owner, group, mode, timestamps), then compares SHA-256 on both sides -- the copy's
             read back from the media where the filesystem allows O_DIRECT -- and writes MANIFEST.sha256. Every
             dlist, not the predicted list: a superset needs no model to be right. It never overwrites: an existing
             copy with the same hash is current, one with another hash stops the run. It works through descriptors
             on the opened directory and the opened source, so a rename or a swapped file after a check cannot
             redirect a read or a write. It refuses unless drill 1's verdict record reads PASS for the 2026-09-18
             fileset, because the first pass deletes that fileset; and while the server reports an active task,
             because a backup writes its dlist last and a half-written one must not be copied.

    ac6      AC-6's second half, "the snapshot appears in the next fileset". Decrypts the newest dlist (or --dlist)
             into a run directory, finds the server-DB snapshot's path in it, and compares size and SHA-256 with the
             live snapshot when the live file is the generation that fileset holds. Shreds the run directory.

    status   The verdict records in the run root, the aside manifest against the destination's dlists, and then the
             acceptance probe, run as the Source's user (the web credential and the Dropbox socket are that user's).

    shred    Shreds one run directory that a failed drill left behind. Refuses any path that is not a directory
             directly under the run root named ac4-* or ac6-*.

EXIT CODES
    0 = the verb's verdict is PASS (or, for `plan` and `status`, it ran); 1 = FAIL; 2 = ERROR, the evidence could
    not be read or a tool failed; 3 = REFUSED, nothing was changed; 64 = usage.

TRUST
    Root runs this file, the driver and retention_table.py from the checkout they sit in, which the Source's user can
    write. Each verb prints the SHA-256 prefix of every file it executes or imports as root, so the pasted summary
    shows which bytes ran. The run root must be a directory owned by root with no access for group or other.

SECRETS
    The passphrase is read by the driver's own loader and reaches duplicati-cli only through its environment. The
    driver prints a 16-hex-digit SHA-256 prefix of the passphrase on its `credential` line; this tool withholds that
    prefix from the terminal and from the output file it writes, and does not print it in `ac6`. An ADOPTED output
    file was written by hand and still holds it (root-only, 0600). This tool prints dlist names, counts, sizes and
    SHA-256 values of ENCRYPTED volumes, and nothing from a decrypted one.
"""

import argparse
import base64
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import mmap
import os
import pwd
import re
import shutil
import stat
import subprocess
import sys
import zipfile

VERSION = "1.1.0"
UTC = dt.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
WRAPPER = os.path.join(HERE, "2026-11-11_phase_d_finish.bash")
DRIVER = os.path.join(HERE, "2026-11-09_ac4_restore_drill.py")
RETENTION_TABLE = os.path.join(HERE, "2026-10-08_backup-phase-b-fold-in", "retention_table.py")
PROBE = os.path.join(HERE, "yamaguchi_acceptance_probe.py")
API_CLIENT = os.path.join(HERE, "yamaguchi_server_api.py")

SOURCE_USER = "pcalnon"  # the backup Source is this user's home, and the web credential is this user's
DEST = "/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi"
ASIDE = "/mnt/Backups/Ubuntu/_yamaguchi_retention_aside"
RUN_ROOT = "/root/phase-d-tmp"
POLICY = "2W:1D,6M:1W,2Y:1M,5Y:2M"  # owner ruling 2026-10-08
DRILLS = {"1": "duplicati-20260918T140000Z.dlist.zip.aes", "2": "duplicati-20261107T212908Z.dlist.zip.aes"}
AC4_MIN_VERIFIED = 15  # design AC-4: "SHA-256 and length match on >= 15 files"
AC4_LIVE_FLOOR = 5  # the driver's reviewed default
HORIZON_HOURS = 60  # the first pass runs at the end of the next backup; the slowest run of this sitting took 8 h 46 m
SNAPSHOT_REL = ".local/state/duplicati-server-db/Duplicati-server.sqlite"
SNAPSHOT_ENABLED = dt.datetime(2026, 11, 8, 19, 57, 0, tzinfo=UTC)  # step 13's `enable --now`
MANIFEST = "MANIFEST.sha256"
RUN_DIR_NAME = re.compile(r"ac[46]-[0-9A-Za-z._-]+")
DLIST_NAME = re.compile(r"duplicati-(\d{8}T\d{6}Z)\.dlist\.[A-Za-z0-9.]+")
CHUNK = 8 * 1024 * 1024  # a multiple of every logical block size O_DIRECT can require; an mmap of it is page-aligned
BOM = chr(0xFEFF)  # built, not typed: an escape typed here once reached this file as the invisible character itself

EXIT_PASS, EXIT_FAIL, EXIT_ERROR, EXIT_REFUSED, EXIT_USAGE = 0, 1, 2, 3, 64

# One anchored pattern per line the AC-4 driver prints. tests/test_phase_d_finish.py renders each of the driver's
# own f-strings and requires its pattern here to match, so a reworded line fails a test instead of reading as absent.
DRILL_LINES = {
    "run_dir": re.compile(r"^run dir     : (?P<run_dir>\S.*)$"),
    "destination": re.compile(r"^destination : (?P<dest>.+) \((?P<dlists>\d+) dlists\); drilling (?P<dlist>\S+) = --version=(?P<version>\d+)$"),
    "restore": re.compile(r"^restore     : duplicati-cli rc=(?P<rc>-?\d+) in (?P<seconds>\d+)s "),
    "drilled": re.compile(r"^drilled     : (?P<dlist>\S+) \(--version=(?P<version>\d+)\)$"),
    "verified": re.compile(r"^VERIFIED    : (?P<verified>\d+)/(?P<picked>\d+) \(SHA-256 \+ length vs the dlist manifest; AC-4 floor (?P<floor>\d+)\)$"),
    "live": re.compile(r"^live oracle : (?P<match>\d+) match, (?P<contradiction>\d+) contradiction \(floor (?P<floor>\d+)\)$"),
    "negative": re.compile(r"^negative    : not-in-fileset path absent=(?P<absent>True|False); flipped-byte copy rejected=(?P<rejected>True|False)$"),
    "result": re.compile(r"^RESULT: (?P<result>PASS|FAIL)$"),
    "fatal": re.compile(r"^FATAL: (?P<message>.*)$"),
}
# The order in which one driver run prints them. RESULT is the last line it prints, and it never prints a FATAL
# after any of the last six.
DRIVER_ORDER = ("run_dir", "destination", "restore", "drilled", "verified", "live", "negative", "result")
# One line per sampled file, printed before the restore: `  [small]        1024 B  static=True   <path>`.
CANDIDATE_LINE = re.compile(r"^  \[ *(?:small|multi|large|empty)\] +\d+ B  static=(?:True |False)  \S")
# The driver's `credential` line ends with a SHA-256 prefix of the passphrase.
CREDENTIAL_FINGERPRINT = re.compile(r"\(sha256\[:16\]=[0-9a-f]{16}\)")
FINGERPRINT_WITHHELD = "(sha256[:16] withheld)"


class Refused(Exception):
    """A precondition does not hold. Nothing was changed."""


class ToolError(Exception):
    """The evidence could not be read, or a tool this step depends on failed."""


def load_module(path, name):
    """Import a sibling script by path (its file name is not an identifier). Registered before it executes."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ToolError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:  # the driver imports `cryptography`, which an interpreter other than the pinned one may lack
        raise ToolError(f"cannot import {os.path.basename(path)}: {exc}") from None
    return module


def utc_stamp(when):
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fd_sha256(fd):
    """SHA-256 of an open file, read from its start."""
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        block = os.read(fd, 1 << 20)
        if not block:
            return digest.hexdigest()
        digest.update(block)


def file_sha256(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        return fd_sha256(fd)
    finally:
        os.close(fd)


def open_regular(path, dir_fd=None):
    """A read-only descriptor on a regular file that is not reached through a symlink; ToolError for anything else.

    O_NONBLOCK keeps a FIFO planted at the path from hanging the caller; it is then refused as not a regular file.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    except OSError as exc:
        raise ToolError(f"{path} cannot be opened as a regular file: {exc.strerror}") from None
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ToolError(f"{path} is not a regular file")
    return fd


def media_sha256(path, dir_fd=None):
    """(sha256 hex, direct) of a file read past the page cache when the filesystem allows O_DIRECT.

    A hash read back through the page cache proves the copy ran, not that the bytes reached the device. Where
    O_DIRECT is refused (tmpfs, some network filesystems) the file is hashed after an fsync and `direct` is False,
    which the caller prints. A symlink at the path is refused either way.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECT | os.O_NOFOLLOW, dir_fd=dir_fd)
    except OSError:
        fd = None
    if fd is not None:
        digest, buf = hashlib.sha256(), mmap.mmap(-1, CHUNK)
        try:
            while True:
                n = os.readv(fd, [buf])
                if n == 0:
                    return digest.hexdigest(), True
                digest.update(buf[:n])
                if n < CHUNK:  # a short read ends the file; the next offset would not be block-aligned
                    return digest.hexdigest(), True
        except OSError:
            pass  # refused at read time: fall through to the cached read, and say so
        finally:
            os.close(fd)
            buf.close()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
    try:
        os.fsync(fd)
        return fd_sha256(fd), False
    finally:
        os.close(fd)


def source_home(user=SOURCE_USER):
    try:
        return pwd.getpwnam(user).pw_dir.rstrip("/")
    except KeyError:
        raise Refused(f"this host has no user {user}") from None


def check_run_root(run_root, owner_uid):
    """The real path of the run root, which must be a directory owned by `owner_uid` with no access for anyone else.

    Verdict records are read from it (`aside` acts on drill 1's) and decrypted dlists are written into it, so a
    directory another user can write is refused. A symlink is refused: lstat reads the name itself.
    """
    try:
        st = os.lstat(run_root)
    except OSError:
        raise Refused(f"the run root {run_root} does not exist (create it 0700, owned by root)") from None
    if not stat.S_ISDIR(st.st_mode):
        raise Refused(f"the run root {run_root} is not a directory (a symlink is refused)")
    if st.st_uid != owner_uid or st.st_mode & 0o077:
        raise Refused(f"the run root {run_root} must be owned by uid {owner_uid} with mode 0700 (it is uid {st.st_uid}, mode {stat.S_IMODE(st.st_mode):04o})")
    return os.path.realpath(run_root)


def provenance(*paths):
    """One line per file this run executes or imports as root, so a pasted summary shows which bytes ran."""
    lines = [f"tool        : {os.path.basename(__file__)} {VERSION} sha256[:16]={file_sha256(os.path.abspath(__file__))[:16]} at {utc_stamp(dt.datetime.now(UTC))}"]
    for label, path in (("wrapper", WRAPPER),) + tuple(paths):
        try:
            lines.append(f"{label:<12}: {os.path.basename(path)} sha256[:16]={file_sha256(path)[:16]}")
        except OSError:
            lines.append(f"{label:<12}: {os.path.basename(path)} is not readable")
    return lines


def header(title, *paths):
    print(f"== {title}")
    for line in provenance(*paths):
        print(line)


# --- the destination's filesets and the first retention pass --------------------------------------------------------
def list_dlists(dest):
    """Sorted dlist file names in `dest`. Names only; nothing is opened."""
    try:
        names = os.listdir(dest)
    except OSError as exc:
        raise ToolError(f"cannot list {dest}: {exc.strerror}") from None
    dlists = sorted(name for name in names if DLIST_NAME.fullmatch(name))
    if not dlists:
        raise ToolError(f"{dest} holds no dlist -- wrong directory, or the destination is not mounted")
    return dlists


def stamp_of(name):
    m = DLIST_NAME.fullmatch(name)
    if not m:
        raise ToolError(f"{name} is not a dlist name")
    return m.group(1)


def pass_instants(stamps, policy, now, horizon):
    """Every instant in [now, now + horizon] at which the pass's result can change, with both ends.

    A fileset stamped s is inside a frame of length T while the pass time is at or before s + T (the lower bound is
    inclusive) and outside it from then on; nothing else about a pass depends on its time. The result is therefore
    constant between two consecutive values of s + T, and evaluating at each of them and one second after it covers
    every pass time in the window. A fixed sample of times does not: on 2026-11-12 a review found a fileset deleted
    only between two of the eight sample points this function replaced.
    """
    end = now + horizon
    instants = {now, end}
    for stamp in stamps:
        for frame, _interval in policy:
            for at in (stamp + frame, stamp + frame + dt.timedelta(seconds=1)):
                if now <= at <= end:
                    instants.add(at)
    return sorted(instants)


def plan_first_pass(dlists, policy_text, now, retention, horizon=dt.timedelta(hours=HORIZON_HOURS)):
    """What the first retention pass is predicted to delete from the EXISTING dlists.

    The pass runs at the end of the next backup. That backup's own fileset is the newest and is set aside, so its
    stamp cannot change the others' fate; the pass TIME can, through each frame's lower bound, so the pass is
    evaluated at every instant pass_instants() names. Returns {'delete': union, 'always': intersection, 'varies':
    union - intersection, 'keep': the rest, 'evaluated': [(pass time, [names])]}.
    """
    try:
        policy = retention.parse_policy(policy_text)
    except (KeyError, ValueError, IndexError):
        raise ToolError(f"the retention policy {policy_text!r} cannot be parsed") from None
    by_stamp = {retention.stamp(stamp_of(name)): name for name in dlists}
    if len(by_stamp) != len(dlists):
        raise ToolError("two dlists carry the same stamp")
    newest_existing = max(by_stamp)
    evaluated, union, always = [], set(), None
    for at in pass_instants(by_stamp, policy, now, horizon):
        run = max(at - dt.timedelta(seconds=1), newest_existing + dt.timedelta(seconds=1))  # the pass's own fileset: newest
        gone = retention.to_delete(list(by_stamp) + [run], max(at, run), policy)
        names = sorted(by_stamp[s] for s in gone if s in by_stamp)
        evaluated.append((at, names))
        union |= set(names)
        always = set(names) if always is None else always & set(names)
    always = always or set()
    return {"delete": sorted(union), "always": sorted(always), "varies": sorted(union - always), "keep": sorted(set(dlists) - union), "evaluated": evaluated}


# --- AC-4: the drill's output, parsed and judged --------------------------------------------------------------------
def parse_drill_output(text):
    """What the driver printed, read strictly.

    {line key: {group: value}} for the FIRST occurrence of each line in DRILL_LINES, plus:
      'order'       the keys in the order they first appear;
      'repeated'    the keys that occur again (one driver run prints each line once);
      'candidates'  how many sampled-file lines the output holds;
      'trailing'    how many non-blank lines follow the first RESULT line (the driver prints nothing after it).

    Only a newline ends a line: the driver prints sampled paths as they are, and str.splitlines() would also break
    a line at a form feed or a Unicode line separator inside a path.
    """
    parsed, order, repeated, candidates, trailing = {}, [], [], 0, 0
    for raw in text.lstrip(BOM).split("\n"):
        line = raw.rstrip("\r")
        if "result" in parsed and line.strip():
            trailing += 1
        for key, pattern in DRILL_LINES.items():
            m = pattern.match(line)
            if not m:
                continue
            if key in parsed:
                repeated.append(key)
            else:
                parsed[key] = m.groupdict()
                order.append(key)
        if CANDIDATE_LINE.match(line):
            candidates += 1
    parsed.update({"order": order, "repeated": repeated, "candidates": candidates, "trailing": trailing})
    return parsed


def judge_drill(parsed, exit_code, expect_dlist, expect_dest):
    """(verdict, reasons, numbers): PASS, FAIL or ERROR for one drill's parsed output.

    `exit_code` is the driver's, or None for an adopted output (a hand-run block echoed it to the terminal only).
    First the output must be ONE complete driver run: no FATAL line, no line twice, every line present and in the
    driver's order, nothing after RESULT. Anything else is ERROR and no number in it is trusted -- a second run
    appended to the file, or a sampled path that contains a newline, could otherwise supply the lines. Then the
    pass rule is recomputed from the numbers, with AC-4's own floors, and must agree with the driver.
    """
    numbers = {}
    if "fatal" in parsed:
        also = " -- and a RESULT line is present too, which one run never prints beside a FATAL" if "result" in parsed else ""
        return "ERROR", [f"the driver stopped: {parsed['fatal']['message']}{also}"], numbers
    if parsed["repeated"]:
        return "ERROR", [f"the output holds more than one `{'`, `'.join(sorted(set(parsed['repeated'])))}` line: two runs in one file, or a line the driver did not print -- nothing in it is judged"], numbers
    missing = [key for key in DRIVER_ORDER if key not in parsed]
    if missing:
        return "ERROR", [f"the output is incomplete -- no {', '.join(missing)} line" + (f" (driver exit {exit_code})" if exit_code is not None else "")], numbers
    if parsed["order"] != list(DRIVER_ORDER):
        return "ERROR", [f"the lines are not in the driver's order ({', '.join(parsed['order'])}) -- nothing in it is judged"], numbers
    if parsed["trailing"]:
        return "ERROR", [f"{parsed['trailing']} line(s) follow the RESULT line; the driver prints nothing after it -- nothing in it is judged"], numbers
    numbers = {
        "rc": int(parsed["restore"]["rc"]), "seconds": int(parsed["restore"]["seconds"]), "verified": int(parsed["verified"]["verified"]), "picked": int(parsed["verified"]["picked"]),
        "floor": int(parsed["verified"]["floor"]), "live_match": int(parsed["live"]["match"]), "contradiction": int(parsed["live"]["contradiction"]), "live_floor": int(parsed["live"]["floor"]),
        "negative_absent": parsed["negative"]["absent"] == "True", "negative_rejected": parsed["negative"]["rejected"] == "True", "version": int(parsed["drilled"]["version"]),
        "dlist": parsed["drilled"]["dlist"], "dest": parsed["destination"]["dest"], "candidates": parsed["candidates"], "driver_result": parsed["result"]["result"], "driver_exit": exit_code,
    }
    n = numbers
    reasons = []
    if n["dlist"] != expect_dlist:
        reasons.append(f"the output drills {n['dlist']}, not {expect_dlist}")
    if parsed["destination"]["dlist"] != n["dlist"] or parsed["destination"]["version"] != parsed["drilled"]["version"]:
        reasons.append("the `destination` and `drilled` lines name different filesets")
    if os.path.normpath(n["dest"]) != os.path.normpath(expect_dest):
        reasons.append(f"the output restores from {n['dest']!r}, not from the destination {expect_dest}")
    if n["rc"] < 0 or n["rc"] >= 3:
        reasons.append(f"duplicati-cli rc={n['rc']} (3 and above are errors; below 0 it was killed by a signal)")
    if n["candidates"] != n["picked"]:
        reasons.append(f"the output lists {n['candidates']} sampled files but its VERIFIED line counts {n['picked']}")
    if n["floor"] < AC4_MIN_VERIFIED:
        reasons.append(f"the run's own floor was lowered to {n['floor']} (AC-4 needs {AC4_MIN_VERIFIED})")
    if n["live_floor"] < AC4_LIVE_FLOOR:
        reasons.append(f"the run's live-oracle floor was lowered to {n['live_floor']} (reviewed default {AC4_LIVE_FLOOR})")
    if n["verified"] != n["picked"]:
        reasons.append(f"verified {n['verified']} of {n['picked']} candidates")
    if n["verified"] < AC4_MIN_VERIFIED:
        reasons.append(f"verified {n['verified']} files (AC-4 needs {AC4_MIN_VERIFIED})")
    if n["contradiction"]:
        reasons.append(f"{n['contradiction']} restored file(s) contradict an unchanged live copy")
    if n["live_match"] < AC4_LIVE_FLOOR:
        reasons.append(f"the live oracle engaged on {n['live_match']} files (floor {AC4_LIVE_FLOOR})")
    if not n["negative_absent"]:
        reasons.append("negative control (a): the path that is not in the fileset WAS restored")
    if not n["negative_rejected"]:
        reasons.append("negative control (b): the flipped-byte copy was NOT rejected")
    recomputed = "FAIL" if reasons else "PASS"
    numbers["recomputed"] = recomputed
    if recomputed != n["driver_result"]:
        reasons.append(f"INCONSISTENT: the driver says RESULT: {n['driver_result']}, the numbers recompute to {recomputed}")
    if exit_code is not None and (exit_code == 0) != (n["driver_result"] == "PASS"):
        reasons.append(f"INCONSISTENT: the driver exited {exit_code} but printed RESULT: {n['driver_result']}")
    return ("FAIL" if reasons else "PASS"), reasons, numbers


def withhold_fingerprint(line):
    """A line of the driver's output with the passphrase's SHA-256 prefix taken out of its `credential` line.

    Sixty-four bits of an unsalted hash confirm an offline guess of a weak passphrase. The line is otherwise kept.
    """
    return CREDENTIAL_FINGERPRINT.sub(FINGERPRINT_WITHHELD, line)


def verdict_path(run_root, label):
    return os.path.join(run_root, f"{label}.verdict.json")


def write_verdict(run_root, label, record):
    path = verdict_path(run_root, label)
    fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(path + ".new", path)
    return path


def read_verdict(run_root, label):
    """The verdict record, or None when there is none or it is not a JSON object."""
    try:
        with open(verdict_path(run_root, label), encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


# --- shredding a run directory --------------------------------------------------------------------------------------
def check_run_dir(path, run_root, owner_uid):
    """The real path of a run directory this tool may shred; raises Refused for anything else."""
    if os.path.islink(path):
        raise Refused(f"{path} is a symlink")
    real, root = os.path.realpath(path), os.path.realpath(run_root)
    if os.path.dirname(real) != root:
        raise Refused(f"{path} is not directly under the run root {root}")
    if not RUN_DIR_NAME.fullmatch(os.path.basename(real)):
        raise Refused(f"{os.path.basename(real)} is not an ac4-* or ac6-* run directory")
    if not os.path.isdir(real):
        raise Refused(f"{path} is not a directory")
    if os.lstat(real).st_uid != owner_uid:
        raise Refused(f"{path} is not owned by uid {owner_uid}")
    return real


def shred_tree(path):
    """Shred every regular file under `path`, then remove the tree. Returns (files shredded, failures)."""
    shred = shutil.which("shred") or "/usr/bin/shred"
    files, failures = 0, []
    for root, dirs, names in os.walk(path, topdown=False):
        for name in names:
            target = os.path.join(root, name)
            if os.path.islink(target) or not os.path.isfile(target):
                os.unlink(target)
                continue
            proc = subprocess.run([shred, "-u", "--", target], capture_output=True, text=True, check=False)
            if proc.returncode == 0 and not os.path.lexists(target):
                files += 1
            else:
                failures.append(target)
        for name in dirs:
            target = os.path.join(root, name)
            if os.path.islink(target):
                os.unlink(target)
            else:
                try:
                    os.rmdir(target)
                except OSError:
                    failures.append(target)
    if not failures:
        try:
            os.rmdir(path)
        except OSError:
            failures.append(path)
    return files, failures


def shred_run_dir(run_dir, run_root, owner_uid):
    """(files shredded, failures) for a run directory; a directory this tool may not touch is reported as a failure."""
    try:
        return shred_tree(check_run_dir(run_dir, run_root, owner_uid))
    except Refused as exc:
        return 0, [f"{run_dir}: {exc}"]


# --- the aside copy ---------------------------------------------------------------------------------------------------
def dropbox_roots(home):
    """Real paths of the Dropbox roots named in the Source user's info.json; raises Refused when it cannot be read."""
    path = os.path.join(home, ".dropbox", "info.json")
    try:
        with open(path, encoding="utf-8-sig") as fh:
            info = json.load(fh)
    except (OSError, ValueError):
        raise Refused(f"cannot read the Dropbox root from {path} -- the aside directory cannot be shown to lie outside it") from None
    roots = [account.get("path") for account in info.values() if isinstance(account, dict)] if isinstance(info, dict) else []
    roots = [os.path.realpath(root) for root in roots if isinstance(root, str) and root]
    if not roots:
        raise Refused(f"{path} names no Dropbox root")
    return roots


def check_aside_location(aside, roots, dest):
    """The real path of the aside directory; Refused when it would lie inside a Dropbox root or the destination."""
    real = os.path.realpath(aside)
    for root in roots + [os.path.realpath(dest)]:
        if os.path.commonpath([real, root]) == root:
            raise Refused(f"the aside directory {aside} lies inside {root}")
    return real


def free_bytes(path):
    """Bytes available to an unprivileged writer on the filesystem that holds `path` or its nearest existing parent."""
    probe = os.path.abspath(path)
    while not os.path.exists(probe):  # ends at "/" at the latest
        probe = os.path.dirname(probe)
    st = os.statvfs(probe)
    return st.f_bavail * st.f_frsize


def open_aside_dir(aside, owner_uid):
    """A descriptor on the aside directory, created 0700 if absent. Everything `aside` writes goes through it.

    The directory's parent is group-writable on this host, so the path can be renamed, and a symlink put in its
    place, after any check of the path. The descriptor cannot: it names the directory that was opened, which is
    then shown to be a directory owned by `owner_uid` with mode 0700.
    """
    created = False
    try:
        os.mkdir(aside, 0o700)
        created = True
    except FileExistsError:
        pass  # something has that name already: what it is, and whose, is settled on the opened descriptor below
    except OSError as exc:
        raise Refused(f"the aside directory {aside} cannot be created: {exc.strerror}") from None
    try:
        fd = os.open(aside, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        problem = f"{aside} cannot be opened as a directory (a symlink is refused): {exc.strerror}"
        raise (ToolError(problem) if created else Refused(problem)) from None
    st = os.fstat(fd)
    if st.st_uid != owner_uid or stat.S_IMODE(st.st_mode) != 0o700:
        os.close(fd)
        problem = f"{aside} must be a directory owned by uid {owner_uid} with mode 0700 (it is uid {st.st_uid}, mode {stat.S_IMODE(st.st_mode):04o})"
        raise (ToolError(problem + " -- and this run created it, so something replaced it") if created else Refused(problem))
    return fd


def entry_exists(dir_fd, name):
    try:
        os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def copy_through(src_fd, src_st, aside_fd, partial, name):
    """Copy an open source file to `partial` in the aside directory; returns the SHA-256 of the bytes read.

    The source is read once, so the bytes hashed are the bytes written. Owner, group, mode and timestamps are
    carried over: what `cp -p` keeps.
    """
    try:
        os.unlink(partial, dir_fd=aside_fd)  # an interrupted run's leftover
    except FileNotFoundError:
        pass  # the usual case: no earlier run left one
    digest = hashlib.sha256()
    try:
        out_fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=aside_fd)
        try:
            os.lseek(src_fd, 0, os.SEEK_SET)
            while True:
                block = os.read(src_fd, 1 << 20)
                if not block:
                    break
                digest.update(block)
                view = memoryview(block)
                while view:
                    view = view[os.write(out_fd, view):]
            os.fchown(out_fd, src_st.st_uid, src_st.st_gid)
            os.fchmod(out_fd, stat.S_IMODE(src_st.st_mode))
            os.utime(out_fd, ns=(src_st.st_atime_ns, src_st.st_mtime_ns))
            os.fsync(out_fd)
        finally:
            os.close(out_fd)
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.unlink(partial, dir_fd=aside_fd)
        raise ToolError(f"copying {name} failed: {exc.strerror}") from None
    return digest.hexdigest()


def copy_aside(dest, aside_fd, names):
    """Copy each named dlist into the opened aside directory, compare SHA-256 on both sides, never overwrite.

    A row is {'name', 'size', 'sha256', 'state': 'copied' | 'current', 'direct': bool}. Raises ToolError on a
    mismatch or a failed copy, leaving no partial file behind; every earlier row's copy stays in place. A source
    or an existing copy that is a symlink, or not a regular file, is an error: it is opened without following.
    """
    rows = []
    for name in names:
        partial = name + ".partial"
        src_fd = open_regular(os.path.join(dest, name))
        try:
            src_st = os.fstat(src_fd)
            if entry_exists(aside_fd, name):
                os.close(open_regular(name, dir_fd=aside_fd))
                want = fd_sha256(src_fd)
                have, direct = media_sha256(name, dir_fd=aside_fd)
                if have != want:
                    raise ToolError(f"{name} already exists in the aside directory with another SHA-256 than its source -- not overwritten; inspect it")
                state = "current"
            else:
                want = copy_through(src_fd, src_st, aside_fd, partial, name)
                have, direct = media_sha256(partial, dir_fd=aside_fd)
                if have != want or os.stat(partial, dir_fd=aside_fd, follow_symlinks=False).st_size != src_st.st_size:
                    os.unlink(partial, dir_fd=aside_fd)
                    raise ToolError(f"the copy of {name} does not match its source -- removed")
                os.replace(partial, name, src_dir_fd=aside_fd, dst_dir_fd=aside_fd)
                state = "copied"
            rows.append({"name": name, "size": src_st.st_size, "sha256": have, "state": state, "direct": direct})
        finally:
            os.close(src_fd)
    os.fsync(aside_fd)
    return rows


def write_manifest(aside_fd, rows):
    """MANIFEST.sha256 in `sha256sum` format, covering every dlist in the aside directory (earlier runs' included)."""
    entries = {row["name"]: row["sha256"] for row in rows}
    for name in sorted(os.listdir(aside_fd)):
        if DLIST_NAME.fullmatch(name) and not name.endswith(".partial") and name not in entries:  # a crashed run's half copy is no dlist
            fd = open_regular(name, dir_fd=aside_fd)
            try:
                entries[name] = fd_sha256(fd)
            finally:
                os.close(fd)
    fd = os.open(MANIFEST + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600, dir_fd=aside_fd)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for name in sorted(entries):
            fh.write(f"{entries[name]}  {name}\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(MANIFEST + ".new", MANIFEST, src_dir_fd=aside_fd, dst_dir_fd=aside_fd)
    os.fsync(aside_fd)
    return len(entries)


def read_manifest(aside):
    """The dlist names MANIFEST.sha256 lists, or None when there is no readable manifest."""
    try:
        with open(os.path.join(aside, MANIFEST), encoding="utf-8") as fh:
            return [line.split()[-1] for line in fh if line.strip()]
    except OSError:
        return None


# --- AC-6b: the snapshot in a fileset ---------------------------------------------------------------------------------
def parse_entry_time(value):
    """A filelist entry's `time` as an aware datetime; None when absent or in a form not recognised."""
    if not isinstance(value, str):
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def find_entry(entries, path):
    """(the File entry whose path is `path` or None, how many entries were read)."""
    found, total = None, 0
    for entry in entries:
        total += 1
        if found is None and isinstance(entry, dict) and entry.get("type") == "File" and entry.get("path") == path:
            found = entry
    return found, total


def judge_ac6b(entry, total, fileset_start, live, fileset_end=None, enabled=SNAPSHOT_ENABLED):
    """(verdict, reasons, facts). `live` is None or {'size', 'mtime' (aware datetime), 'sha256_b64'}.

    `fileset_start` is the dlist's stamp, when the backup began. `fileset_end` is when the dlist was written (its
    mtime) or None: a backup reads files for hours, so an entry may be dated after the start, never after the end.

    The fileset's copy and the live file are the same generation -- and are compared by content -- when the live
    file was last written at or before the backup began, or when the entry's own time is the live file's mtime.
    Otherwise a newer snapshot has replaced the live file and only the entry's time can be judged. Either way a
    generation written before the timer was re-enabled is the stale pre-recovery snapshot, not AC-6's.
    """
    facts = {"entries": total, "fileset": utc_stamp(fileset_start)}
    if total == 0:
        return "ERROR", ["the fileset's file list yielded no entries -- a parser fault, not an empty fileset"], facts
    if entry is None:
        return "FAIL", [f"the snapshot's path is not among the fileset's {total} entries"], facts
    size, digest, when = entry.get("size"), entry.get("hash"), parse_entry_time(entry.get("time"))
    facts.update({"entry_size": size, "entry_time": utc_stamp(when) if when else None})
    reasons = []
    if not isinstance(size, int) or isinstance(size, bool) or size <= 4096:
        reasons.append(f"the fileset's copy is {size} bytes -- a stub, not a database")
    stale = when is not None and when < enabled
    if stale:
        reasons.append(f"the fileset's copy is dated {utc_stamp(when)}, before the timer was re-enabled ({utc_stamp(enabled)}): the stale pre-recovery snapshot")
    if when is not None and fileset_end is not None and when > fileset_end:
        reasons.append(f"the fileset's copy is dated {utc_stamp(when)}, after the fileset was complete ({utc_stamp(fileset_end)})")
    if live is None:
        return ("FAIL" if reasons else "ERROR"), reasons + ["the live snapshot could not be read, so there is nothing to compare with"], facts
    facts.update({"live_size": live["size"], "live_mtime": utc_stamp(live["mtime"])})
    if live["mtime"] <= fileset_start or (when is not None and when == live["mtime"].replace(microsecond=0)):
        facts["compared"] = "content"
        if live["mtime"] < enabled and not stale:
            reasons.append(f"the live snapshot was last written {utc_stamp(live['mtime'])}, before the timer was re-enabled ({utc_stamp(enabled)}): the lane has not run since, and this is the stale pre-recovery snapshot")
        if size != live["size"] or digest != live["sha256_b64"]:
            reasons.append("the fileset's copy differs from the live snapshot of the same generation (size or SHA-256)")
    else:
        facts["compared"] = "time"
        if when is None:
            return ("FAIL" if reasons else "ERROR"), reasons + ["a newer snapshot has replaced the live file and the entry carries no readable time -- run this before the next 13:45 UTC"], facts
    return ("FAIL" if reasons else "PASS"), reasons, facts


# --- verbs ------------------------------------------------------------------------------------------------------------
PLAN_ASSUMES = "every fileset is a full backup, and no clock change lies between a fileset and the pass -- names show neither, so `aside` copies every dlist"


def cmd_plan(args):
    retention = load_module(RETENTION_TABLE, "phase_d_retention_table")
    dlists = list_dlists(args.dest)
    now = args.at or dt.datetime.now(UTC)
    plan = plan_first_pass(dlists, args.policy, now, retention)
    header(f"first retention pass, policy {args.policy}, over the {len(dlists)} dlists in {args.dest}", ("retention", RETENTION_TABLE))
    print(f"evaluated   : every pass time from {utc_stamp(now)} to +{HORIZON_HOURS}h ({len(plan['evaluated'])} instants: both ends and each one where a fileset meets a frame's edge)")
    recovery = "20261107T000000Z"
    for name in dlists:
        mark = "DELETE" if name in plan["delete"] else "keep  "
        note = "  (only at some pass times)" if name in plan["varies"] else ""
        print(f"  {mark}  {name}  {os.path.getsize(os.path.join(args.dest, name)):>12} B{note}")
    pre = sum(1 for name in plan["delete"] if stamp_of(name) < recovery)
    total = sum(os.path.getsize(os.path.join(args.dest, name)) for name in plan["delete"])
    print(f"predicted   : {len(plan['delete'])} of {len(dlists)} deleted ({pre} pre-recovery, {len(plan['delete']) - pre} post-recovery), {total} B")
    print("stability   : the same set at every pass time in the window" if not plan["varies"] else f"stability   : {len(plan['varies'])} dlist(s) are deleted only at some pass times")
    print(f"assumes     : {PLAN_ASSUMES}")
    print("caveat      : a backup that finishes before retention is restored adds a fileset this list does not hold -- re-run then")
    return EXIT_PASS


def as_source_user(home, script, *args):
    """argv that runs one of this directory's scripts as the Source's user: no privilege, an empty environment.

    The web credential and the Dropbox socket are found through HOME, so HOME is that user's. The caller starts it
    with cwd="/": root's own working directory may be one that user cannot enter.
    """
    runuser = shutil.which("runuser") or "/usr/sbin/runuser"
    return [runuser, "-u", SOURCE_USER, "--", "/usr/bin/env", "-i", f"HOME={home}", f"USER={SOURCE_USER}", f"LOGNAME={SOURCE_USER}", "PATH=/usr/bin:/bin", "LANG=C.UTF-8", "/usr/bin/python3", "-I", script, *args]


def server_task(home):
    """('active', detail) | ('idle', detail) | ('unknown', why): the server's ActiveTask, asked as the Source's user."""
    try:
        proc = subprocess.run(as_source_user(home, API_CLIENT, "serverstate"), capture_output=True, text=True, timeout=60, check=False, cwd="/")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "unknown", f"serverstate could not be run ({type(exc).__name__})"
    return read_server_task(proc.returncode, proc.stdout)


def read_server_task(returncode, stdout):
    """Judge `yamaguchi_server_api.py serverstate`: exit 0 Running, 2 Paused, JSON with ActiveTask on stdout."""
    if returncode not in (0, 2):
        return "unknown", f"serverstate exited {returncode}"
    try:
        state = json.loads(stdout)
    except ValueError:
        return "unknown", "serverstate printed no JSON"
    if not isinstance(state, dict) or "ActiveTask" not in state:
        return "unknown", "serverstate's JSON carries no ActiveTask"
    if state["ActiveTask"]:
        return "active", f"ActiveTask={json.dumps(state['ActiveTask'])}"
    return "idle", f"no active task; ProgramState={state.get('ProgramState')}"


def run_driver(dlist, dest, run_root, out_path):
    """Run the AC-4 driver, its output teed to `out_path` (0600) and to the terminal. Returns its exit code.

    Both copies carry the driver's lines as printed, less the passphrase's SHA-256 prefix (withhold_fingerprint).
    The driver runs unbuffered (-u): a drill takes many minutes and its lines should appear as they are printed, and
    with a buffered stdout a FATAL on stderr would be recorded ahead of the lines that led to it.
    """
    argv = ["/usr/bin/python3", "-I", "-u", DRIVER, "--dest", dest, "--dlist", dlist, "--run-root", run_root]
    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace") as proc:
            for line in proc.stdout or ():
                line = withhold_fingerprint(line)
                sys.stdout.write(line)
                sys.stdout.flush()
                out.write(line)
            return proc.wait()


def cmd_drill(args, *, run=run_driver, task=server_task, owner_uid=0):
    dlist, label = DRILLS[args.n], f"ac4-drill{args.n}"
    header(f"AC-4 drill {args.n}: {dlist}", ("driver", DRIVER))
    run_root = check_run_root(args.run_root, owner_uid)
    out_path = os.path.join(run_root, f"{label}.out")
    dest = os.path.realpath(args.dest)
    previous = read_verdict(run_root, label)
    if previous and previous.get("verdict") == "PASS" and not args.rerun:
        print(f"already     : PASSED, judged {previous.get('judged_at')} -- nothing run (pass --rerun to drill again)")
        print("VERDICT: PASS")
        return EXIT_PASS
    exit_code, adopted = None, os.path.lexists(out_path) and not args.rerun
    if adopted:
        print(f"source      : ADOPTED {out_path} (mtime {utc_stamp(dt.datetime.fromtimestamp(os.path.getmtime(out_path), UTC))}); the driver was not run")
    else:
        # Every refusal comes before the earlier output is moved: REFUSED means nothing was changed.
        if dlist not in list_dlists(dest):
            raise Refused(f"{dlist} is not in {dest}")
        state, detail = task(source_home())
        print(f"server      : {detail}" + ("" if state != "unknown" else " -- proceeding: the driver refuses its own result if a dlist lands mid-restore"))
        if state == "active" and not args.allow_active_task:
            raise Refused("a server task is active: a dlist that lands mid-restore makes the driver refuse its own result -- run this after the backup finishes (or pass --allow-active-task)")
        if os.path.lexists(out_path):
            kept = f"{out_path}.{dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
            os.replace(out_path, kept)
            print(f"earlier out : moved to {kept}")
        print("source      : running the driver now")
        exit_code = run(dlist, dest, run_root, out_path)
    with open(out_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    parsed = parse_drill_output(text)
    verdict, reasons, numbers = judge_drill(parsed, exit_code, dlist, dest)
    run_dir = parsed.get("run_dir", {}).get("run_dir")
    record = {"schema": "phase-d-drill/2", "tool_version": VERSION, "drill": args.n, "dlist": dlist, "verdict": verdict, "reasons": reasons, "numbers": numbers, "adopted": adopted, "out_file": out_path,
              "out_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(), "judged_at": utc_stamp(dt.datetime.now(UTC)),
              # For an adopted output this is the driver as it is NOW, which need not be the one that wrote the output.
              "driver_sha256_when_judged": file_sha256(DRIVER), "driver_ran_here": not adopted}
    print(f"-- summary of drill {args.n} (paste from this line to VERDICT) --")
    for line in provenance(("driver", DRIVER)):
        print(line)
    print(f"source      : {'an ADOPTED output; the driver was not run here' if adopted else 'the driver, run here'}")
    if numbers:
        n = numbers
        print(f"restore     : duplicati-cli rc={n['rc']} in {n['seconds']}s; --version={n['version']}")
        print(f"verified    : {n['verified']}/{n['picked']} (AC-4 floor {AC4_MIN_VERIFIED}; the run's own floor {n['floor']})")
        print(f"live oracle : {n['live_match']} match, {n['contradiction']} contradiction (floor {AC4_LIVE_FLOOR})")
        print(f"negatives   : not-in-fileset absent={n['negative_absent']}; flipped-byte rejected={n['negative_rejected']}")
        print(f"driver says : RESULT: {n['driver_result']}" + (f" (exit {exit_code})" if exit_code is not None else " (exit code not recorded in an adopted output)"))
        print(f"recomputed  : {n['recomputed']}")
    for reason in reasons:
        print(f"reason      : {reason}")
    if verdict == "PASS" and run_dir and os.path.lexists(run_dir):
        files, failures = shred_run_dir(run_dir, run_root, owner_uid)
        record["run_dir"] = "shredded" if not failures else "NOT shredded"
        print(f"run dir     : shredded {files} file(s) from {run_dir!r}" + (f"; {len(failures)} path(s) could NOT be removed -- the decrypted dlist may still be on disk" if failures else ""))
        if failures:
            verdict, record["verdict"] = "ERROR", "ERROR"
            record["reasons"] = reasons + ["the drill passed, but its run directory could not be shredded: " + "; ".join(failures)]
    elif run_dir and os.path.lexists(run_dir):
        record["run_dir"] = run_dir
        print(f"run dir     : KEPT at {run_dir!r} (restore.log is the evidence); shred it with the `shred` verb once read")
    else:
        record["run_dir"] = "absent"
        print("run dir     : none on disk")
    print(f"record      : {write_verdict(run_root, label, record)}")
    if adopted and verdict != "PASS":
        print(f"next        : `drill {args.n} --rerun` runs the driver again; this output is moved aside, not deleted")
    print(f"VERDICT: {verdict}")
    return {"PASS": EXIT_PASS, "FAIL": EXIT_FAIL}.get(verdict, EXIT_ERROR)


def predicted_line(dlists, policy_text, now):
    """`aside`'s one line about the prediction. Best effort: the copy takes every dlist and must not wait on a model."""
    try:
        plan = plan_first_pass(dlists, policy_text, now, load_module(RETENTION_TABLE, "phase_d_retention_table"))
    except ToolError as exc:
        return f"predicted   : not available ({exc}) -- the copy does not depend on it"
    return f"predicted   : the first pass under {policy_text} deletes {len(plan['delete'])} of {len(dlists)} dlists (it assumes {PLAN_ASSUMES})"


def cmd_aside(args, *, task=server_task, owner_uid=0):
    header(f"retention aside copy to {args.aside}", ("retention", RETENTION_TABLE))
    run_root = check_run_root(args.run_root, owner_uid)
    drill = read_verdict(run_root, "ac4-drill1")
    if not drill or drill.get("verdict") != "PASS" or drill.get("dlist") != DRILLS["1"]:
        raise Refused(f"drill 1 has no PASS verdict record for {DRILLS['1']} in {run_root} -- the first retention pass deletes that fileset, so it is drilled first")
    print(f"drill 1     : PASS, judged {drill.get('judged_at')}")
    home = source_home()
    state, detail = task(home)
    print(f"server      : {detail}" + ("" if state != "unknown" else " -- proceeding"))
    if state == "active" and not args.allow_active_task:
        raise Refused("a server task is active: a dlist it is writing now would be copied half-written -- run this after the backup finishes (or pass --allow-active-task)")
    dlists = list_dlists(args.dest)
    print(predicted_line(dlists, args.policy, dt.datetime.now(UTC)))
    check_aside_location(args.aside, dropbox_roots(home), args.dest)
    need = sum(os.path.getsize(os.path.join(args.dest, name)) for name in dlists if not os.path.lexists(os.path.join(args.aside, name)))
    free = free_bytes(args.aside)
    if free < need * 2:
        raise Refused(f"the filesystem of {args.aside} has {free} B free; the copy needs {need} B and this tool wants twice that")
    aside_fd = open_aside_dir(args.aside, owner_uid)
    try:
        rows = copy_aside(args.dest, aside_fd, dlists)
        for row in rows:
            print(f"  {row['state']:<7} {row['name']}  {row['size']:>12} B  sha256={row['sha256'][:16]} match ({'read back from the media' if row['direct'] else 'cached read after fsync'})")
        count = write_manifest(aside_fd, rows)
    finally:
        os.close(aside_fd)
    print(f"manifest    : {os.path.join(args.aside, MANIFEST)} lists {count} dlist(s)")
    print(f"copied      : all {len(rows)} dlists of the destination -- {sum(1 for r in rows if r['state'] == 'copied')} new, {sum(1 for r in rows if r['state'] == 'current')} already current, {sum(r['size'] for r in rows)} B in all")
    print("next        : restore retention-policy in the UI BEFORE the next backup starts; if a backup finishes first, run `aside` again (`status` says whether one has)")
    print("VERDICT: PASS")
    return EXIT_PASS


def cmd_ac6(args, *, owner_uid=0):
    dlists = list_dlists(args.dest)
    dlist = args.dlist or dlists[-1]
    if dlist not in dlists:
        raise Refused(f"{dlist} is not in {args.dest}")
    header(f"AC-6b: the server-DB snapshot in {dlist}", ("driver", DRIVER))
    run_root = check_run_root(args.run_root, owner_uid)
    home = source_home()  # before the driver is imported: it resolves the same user at import time
    driver = load_module(DRIVER, "phase_d_ac4_driver")
    snapshot = os.path.join(home, SNAPSHOT_REL)
    source = os.path.join(args.dest, dlist)
    fileset_start = dt.datetime.strptime(stamp_of(dlist), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    fileset_end = dt.datetime.fromtimestamp(os.stat(source).st_mtime, UTC)
    run_dir = os.path.join(run_root, f"ac6-{stamp_of(dlist)}-{dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}")
    os.mkdir(run_dir, 0o700)
    stopped = None
    verdict, reasons, facts = "ERROR", [], {"entries": 0, "fileset": utc_stamp(fileset_start)}
    try:
        plain = os.path.join(run_dir, "dlist.zip")
        with contextlib.redirect_stdout(io.StringIO()):  # the loader prints a SHA-256 prefix of the passphrase
            passphrase = driver.load_passphrase(args.cred_file or os.path.join(home, ".config", "duplicati-backup", "env"), "PASSPHRASE")
        driver.aescrypt_decrypt(source, plain, passphrase)
        with zipfile.ZipFile(plain) as zf, zf.open("filelist.json") as stream:
            entry, total = find_entry(driver.iter_json_array(stream), snapshot)
        try:
            with open(snapshot, "rb") as fh:  # size, mtime and bytes of ONE generation: the lane may replace the file at 13:45 UTC
                st = os.fstat(fh.fileno())
                digest = hashlib.sha256(fh.read()).digest()
            live = {"size": st.st_size, "mtime": dt.datetime.fromtimestamp(st.st_mtime, UTC), "sha256_b64": base64.b64encode(digest).decode()}
        except OSError:
            live = None
        verdict, reasons, facts = judge_ac6b(entry, total, fileset_start, live, fileset_end)
    except SystemExit as exc:  # the driver's fail(): its own FATAL line is already on stderr
        stopped = f"the driver's decrypt or parse stopped (exit {exc.code}); its FATAL line is above"
    except (OSError, zipfile.BadZipFile, KeyError, IndexError, ValueError, EOFError) as exc:  # no credential file, a truncated volume, a zip without a file list
        stopped = f"the dlist could not be read ({type(exc).__name__}); nothing was judged"
    finally:
        files, failures = shred_run_dir(run_dir, run_root, owner_uid)
    if stopped is not None:
        reasons = [stopped]
    print(f"fileset     : {facts['entries']} entries; started {facts['fileset']}, complete {utc_stamp(fileset_end)}")
    if "entry_size" in facts:
        print(f"in fileset  : {SNAPSHOT_REL} present, {facts['entry_size']} B, time {facts['entry_time']}")
    if "live_size" in facts:
        print(f"live        : {facts['live_size']} B, mtime {facts['live_mtime']}; compared by {facts.get('compared')}")
    for reason in reasons:
        print(f"reason      : {reason}")
    print(f"run dir     : shredded {files} file(s)" + (f"; {len(failures)} path(s) could NOT be removed from {run_dir} -- a decrypted dlist may still be on disk" if failures else ""))
    if failures and verdict == "PASS":
        verdict = "ERROR"
    record = {"schema": "phase-d-ac6b/2", "tool_version": VERSION, "dlist": dlist, "verdict": verdict, "reasons": reasons, "facts": facts, "judged_at": utc_stamp(dt.datetime.now(UTC))}
    print(f"record      : {write_verdict(run_root, 'ac6b', record)}")
    print(f"VERDICT: {verdict}")
    return {"PASS": EXIT_PASS, "FAIL": EXIT_FAIL}.get(verdict, EXIT_ERROR)


def leftover_run_dirs(run_root):
    """Run directories still on disk under the run root: each holds a decrypted dlist until it is shredded."""
    try:
        return sorted(name for name in os.listdir(run_root) if RUN_DIR_NAME.fullmatch(name) and os.path.isdir(os.path.join(run_root, name)) and not os.path.islink(os.path.join(run_root, name)))
    except OSError:
        return []


def aside_coverage(aside, dest):
    """One line: what the aside manifest lists, what is missing from the directory, what the destination holds beyond it."""
    listed = read_manifest(aside)
    if listed is None:
        return f"aside       : no manifest at {os.path.join(aside, MANIFEST)}"
    missing = [name for name in listed if not os.path.isfile(os.path.join(aside, name))]
    try:
        beyond = [name for name in list_dlists(dest) if name not in listed]
        tail = f"{len(beyond)} dlist(s) now in the destination are not in it" + (" -- run `aside` again before retention is restored" if beyond else "")
    except ToolError as exc:
        tail = f"the destination could not be listed ({exc})"
    return f"aside       : {os.path.join(aside, MANIFEST)} lists {len(listed)} dlist(s); {len(missing)} missing from the directory; {tail}"


def cmd_status(args, *, owner_uid=0):
    header("Phase D step 14: root-side records, then the acceptance probe")
    run_root = check_run_root(args.run_root, owner_uid)
    leftovers = leftover_run_dirs(run_root)
    print(f"run dirs    : {len(leftovers)} on disk" + (f" -- each holds a decrypted dlist; shred with the `shred` verb: {', '.join(leftovers)}" if leftovers else ""))
    for label in ("ac4-drill1", "ac4-drill2", "ac6b"):
        record = read_verdict(run_root, label)
        print(f"{label:<11} : " + (f"{record.get('verdict')} for {record.get('dlist')}, judged {record.get('judged_at')}" if record else "no verdict record"))
    print(aside_coverage(args.aside, args.dest))
    extra = ["--expect-retention", args.expect_retention] if args.expect_retention else []
    argv = as_source_user(source_home(), PROBE, "--backup-id", args.backup_id, *extra)
    print(f"probe       : as {SOURCE_USER}")
    sys.stdout.flush()
    code = subprocess.run(argv, check=False, cwd="/").returncode
    print(f"probe exit  : {code}")
    return EXIT_PASS


def cmd_shred(args, *, owner_uid=0):
    header(f"shred {args.run_dir}")
    run_root = check_run_root(args.run_root, owner_uid)
    files, failures = shred_tree(check_run_dir(args.run_dir, run_root, owner_uid))
    print(f"shredded    : {files} file(s)" + (f"; {len(failures)} path(s) could NOT be removed" if failures else ""))
    print(f"VERDICT: {'PASS' if not failures else 'ERROR'}")
    return EXIT_PASS if not failures else EXIT_ERROR


ROOT_VERBS = {"drill": cmd_drill, "aside": cmd_aside, "ac6": cmd_ac6, "status": cmd_status, "shred": cmd_shred}


def job_id(text):
    if not re.fullmatch(r"[1-9][0-9]*", text):
        raise argparse.ArgumentTypeError(f"the job id must be a positive integer, got {text!r}")
    return text


def utc_instant(text):
    try:
        return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        raise argparse.ArgumentTypeError(f"an instant is written YYYY-MM-DDTHH:MM:SSZ, got {text!r}") from None


class _Parser(argparse.ArgumentParser):
    """Usage errors exit 64. No abbreviations: the wrapper reads --run-root by its full name to set TMPDIR."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def build_parser():
    ap = _Parser(description="Phase D's remaining root steps: the AC-4 drills, the retention aside copy, AC-6b")
    ap.add_argument("--dest", default=DEST, help="the destination directory")
    ap.add_argument("--run-root", default=RUN_ROOT, help="root-only scratch (0700, owned by root); verdict records are kept here")
    ap.add_argument("--aside", default=ASIDE, help="the retention aside directory")
    ap.add_argument("--policy", default=POLICY, help="the retention policy to be restored")
    sub = ap.add_subparsers(dest="verb", required=True, parser_class=_Parser)
    plan = sub.add_parser("plan", help="a prediction of what the first retention pass deletes (any user, read-only)")
    plan.add_argument("--at", type=utc_instant, default=None, help="evaluate the pass from this instant instead of now, as YYYY-MM-DDTHH:MM:SSZ")
    drill = sub.add_parser("drill", help="AC-4 drill 1 or 2 (root)")
    drill.add_argument("n", choices=sorted(DRILLS))
    drill.add_argument("--rerun", action="store_true", help="run the driver again; an earlier output is moved aside, never deleted")
    drill.add_argument("--allow-active-task", action="store_true", help="run even though the server reports an active task")
    aside = sub.add_parser("aside", help="copy every dlist of the destination to the aside directory (root)")
    aside.add_argument("--allow-active-task", action="store_true", help="copy even though the server reports an active task")
    ac6 = sub.add_parser("ac6", help="AC-6b: the snapshot in the newest fileset (root)")
    ac6.add_argument("--dlist", default=None, help="default: the newest dlist")
    ac6.add_argument("--cred-file", default=None, help="default: the Source user's ~/.config/duplicati-backup/env")
    status = sub.add_parser("status", help="verdict records, then the probe as the Source's user (root)")
    status.add_argument("--backup-id", required=True, type=job_id, help="the job's numeric id; no default")
    status.add_argument("--expect-retention", choices=("suspended", "restored"), default=None)
    shred = sub.add_parser("shred", help="shred a kept run directory (root)")
    shred.add_argument("--run-dir", required=True)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.verb == "plan":
            return cmd_plan(args)
        if os.geteuid() != 0:
            raise Refused(f"`{args.verb}` runs as root (the run root, the 0640 volumes and the aside directory are root's to read and write)")
        return ROOT_VERBS[args.verb](args)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        print("VERDICT: REFUSED (nothing was changed)")
        return EXIT_REFUSED
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("VERDICT: ERROR")
        return EXIT_ERROR
    except OSError as exc:  # a file this verb needs could not be read or written: a verdict line, not a traceback
        print(f"ERROR: {type(exc).__name__}: {exc.strerror or exc}" + (f" ({exc.filename})" if exc.filename else ""), file=sys.stderr)
        print("VERDICT: ERROR")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
