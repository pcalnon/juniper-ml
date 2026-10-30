#!/usr/bin/env python3
"""
Procedure A's key write: put the form of the moved-aside service .env's active SETTINGS_ENCRYPTION_KEY that
the frozen server database is encrypted under at /etc/credstore/duplicati-settings-key -- verified against
the database before the write and read back after it, never printed, never on an argv.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Version: 1.3.0 (2026-10-29: Phase D round-3 fold-in -- see HISTORY)
Status: ad-hoc — recovery (Phase D, Procedure A only)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md
         ("the assessment") section 6.4 steps 7 and 9; notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-
         INFRASTRUCTURE-INTEGRATED-DESIGN.md ("D") section 8 P0 steps 3, 5 and 8;
         util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py (the parser and the variants this
         mirrors; tests/test_write_matched_settings_key.py pins the parity by running the probe);
         util/ad-hoc/2026-10-03_rekey_gate.py (its five columns and read_key).

WHEN. Only on Procedure A: the assessment's step 7 probe matched an ENV_ACTIVE_KEY variant of the moved-aside
.env (O-1/O-2, ruled 2026-10-25), and step 9 must place that key at the credential path before step 9 shreds
the .env -- the .env is then the key's only holder. Run --dry-run at step 7, straight after the probe, so an
undeliverable form is known before Procedure A's folder is placed. No document gave a command for the write:
the probe names the matching variant, but D and the assessment say only "write the accepted key", and every
hand-typed form of that puts the key on a terminal, in a root shell's history or on sudo's argv (round-4
B14: sudo logs its argv as COMMAND= in the journal and /var/log/auth.log).

WHY A TOOL. The wrapper reads the credential with `$(<file)`, which drops every trailing newline, and refuses
a NUL, a carriage return or edge whitespace; it keeps quotes. So the form to write is the matching variant's
own text: a `noquote` match is written without its quotes and a quoted `raw` match keeps them, while a match
only on the probe's `newline` variant cannot be delivered through the file at all (the server would be handed
the text without its newline, and every start would fail with the I-38 mismatch). This tool re-derives the
match from the database itself rather than trusting a hand-copied variant name.

WHAT IT DOES, in order. Any refusal exits 1, writes nothing and leaves the .env alone:
  1. opens --out's directory without following a symlink and refuses unless that directory is owned by the
     effective user and writable by nobody else (/etc/credstore is 0700 root:root), and unless --out does not
     exist (no file, no symlink);
  2. reads --env (a regular file, no symlink, never a FIFO; strict UTF-8) with the probe's own parser: the
     LAST uncommented `SETTINGS_ENCRYPTION_KEY=` line, every trailing carriage return stripped; refuses when
     there is none or its value is empty (SETTINGS_ENCRYPTION_KEY_OLD is a different name and never matches);
  3. reads --db read-only with the probe's two queries and refuses unless at least one enc-v1 blob was found,
     every blob's content hash verifies (the layout parse is right), and the blobs carry exactly ONE key hash;
     a query error refuses and names only the error's class (Python's decode error quotes the column's text);
  4. computes the probe's variants of that value and keeps those whose SHA-256 is the database's key hash;
     no match refuses (after a probe match that is a disagreement to stop on, never a route to A0);
  5. refuses unless every enc-v1 blob in the exit gate's five columns carries that same key hash -- the
     probe reads two, and a blob under another key elsewhere would fail step 13's exit gate; the scan reads
     with double-quoted string literals off, so a missing column is an error, never read as text;
  6. refuses a matched form the credential file cannot deliver: a NUL, a carriage return, any newline, or
     leading or trailing whitespace (any Unicode whitespace: stricter than the wrapper, never looser);
  7. creates --out in that directory with O_CREAT|O_EXCL|O_NOFOLLOW, mode 0600, owner the effective user
     (root), no trailing newline, and fsyncs the file and the directory -- never over an existing key (the
     A0/A2/B line's `test ! -e`);
  8. reads the file back twice -- with util/ad-hoc/2026-10-03_rekey_gate.py's read_key (what the gate will
     judge; loaded before the write, with bytecode writing off so root leaves no .pyc in the checkout) and with
     bash's `$(<file)` (what the wrapper hands the server) -- and requires both to hash to the database's key
     hash. A failed read-back removes the file it created.
--dry-run runs steps 1 to 6 and writes nothing, and refuses everything the real run would refuse up to there.

SIGNALS. SIGINT, SIGTERM, SIGHUP and SIGQUIT are deferred (blocked) from just before the create until the file
is either verified or removed, so an interruption -- a closed terminal, a Ctrl-C, a kill -- lands after that
decision, never between the create and it. Only SIGKILL cannot be deferred. So trust the tool's last DECISION
line, whatever follows it (a traceback, a signal's exit status): "wrote ... both match" means written and
verified; "removed ..." means nothing is left. A run ended by a signal (status 128 or more) with neither line
printed was a SIGKILL inside the window: `ls -la` the directory and remove a key file there before a re-run,
because it is unverified. Core dumps are off for the whole run (RLIMIT_CORE 0), so a SIGQUIT -- whose default
action dumps core into the working directory, here the checkout -- cannot write the key's memory to disk.

WHAT IT PRINTS: candidate labels, counts, the matched variant labels, the value's length and the outcome --
never the value, never a hash. Exit 0 written (or dry run passed), 1 refused, 2 usage or I/O error; a deferred
signal may end the process with its own status once the decision is printed.

Usage, in the owner's root shell, from a checkout at origin/main, after step 7's probe matched an
ENV_ACTIVE_KEY label (step 7: --dry-run; step 9, after the installer: the real run):
    python3 util/ad-hoc/2026-10-29_write_matched_settings_key.py --dry-run \
        --env /home/duplicati/.config/Duplicati.empty-2026-09-20/.env \
        --db /root/phase-d-tmp/probe/Duplicati-server.sqlite \
        --out /etc/credstore/duplicati-settings-key
--db is the probe's scratch copy of the freeze's Duplicati-server.sqlite (never the freeze itself), the same
file the probe matched against.

HISTORY
  1.0.0  2026-10-29  first version (Phase D's design, before step 0).
  1.1.0  2026-10-29  Phase D round-1 fold-in (lane B): a query error names its class only (B-2); the gate is
                     loaded before the write and every interruption after the create removes the file (B-4);
                     the whitespace message no longer claims the wrapper refuses every Unicode space (B-6);
                     no .pyc (B-7); --env must be a regular file and is opened non-blocking (B-8); --out is
                     created through an O_NOFOLLOW directory descriptor (B-9); the gate's five columns must
                     carry the one key hash (B-10); "no match" says to stop after a probe match (B-12, C-2).
  1.2.0  2026-10-29  Phase D round-2 fold-in (lane R2-A): SIGINT/SIGTERM/SIGHUP/SIGQUIT are deferred from before
                     the create until the keep-or-remove decision (R2A-2: SIGTERM or SIGHUP in the read-back, or an
                     interrupt just after the open, left an unverified key); the five-column scan reads with
                     double-quoted string literals off (R2A-6); "the exit gate would fail", not "the first start"
                     (R2A-7); the removal goes through the directory descriptor (R2A-8).
  1.3.0  2026-10-29  Phase D round-3 fold-in (lane R3): core dumps off for the run (R3-6: SIGQUIT's default action
                     dumped core, with the key in memory, into the working directory); the docstring's "last
                     decision line" rule (R3-3).
"""
import argparse
import hashlib
import importlib.util
import os
import re
import resource
import signal
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "2026-10-03_rekey_gate.py"
LABEL = "ENV_ACTIVE_KEY"

# The probe's two queries (util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py), verbatim.
PROBE_SQL = (
    "SELECT TargetURL FROM Backup",
    "SELECT Value FROM Option WHERE Name IN ('passphrase','--passphrase','jwt-config','pbkdf-config')",
)
# The probe's .env patterns, verbatim: a commented line for these names is a candidate of its own, never the
# active key; the active key is the last uncommented SETTINGS_ENCRYPTION_KEY= line.
COMMENTED = re.compile(r"^\s*#\s*(export\s+)?(PASSPHRASE|PASSPHRASE_OLD|SETTINGS_ENCRYPTION_KEY)=(.*)$")
ACTIVE = re.compile(r"^\s*(export\s+)?SETTINGS_ENCRYPTION_KEY=(.*)$")
# What the wrapper (scripts/duplicati-wrapper.bash, load_settings_key) does to the file: `$(<file)`.
BASH_READ = 'k="$(<"$1")" && printf %s "$k" | sha256sum'
# The signals an interruption arrives as, deferred across the write (see SIGNALS above); SIGKILL cannot be.
DEFERRED = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)


class Refused(Exception):
    """A refusal: printed as one line, exit 1, nothing written."""


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


# strip_quotes and variants are the probe's, verbatim; tests/test_write_matched_settings_key.py compares them
# with the probe's own definitions on a corpus, and runs the probe itself on the same inputs.
def strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        return v[1:-1]
    return v


def variants(v: str):
    out = {"raw": v, "noquote": strip_quotes(v)}
    b = strip_quotes(v)
    out["unesc"] = b.replace("\\$", "$").replace("\\&", "&").replace("\\\\", "\\").replace("\\%", "%")
    out["no_dollar_star"] = b.replace("$*", "")
    out["no_dollar_at"] = b.replace("$@", "")
    out["no_dollar_star_at"] = b.replace("$*", "").replace("$@", "")
    out["pct_doubled"] = b.replace("%", "%%")
    out["newline"] = b + "\n"
    out["cr"] = b.rstrip("\r")
    out["stripped"] = b.strip()
    # bash double-quote expansion of $* / $@ with no positional params, and of ${...}
    out["bash_dq"] = re.sub(r"\$(\*|@|[0-9]|[A-Za-z_][A-Za-z0-9_]*|\{[^}]*\})", "", b)
    return out


def read_regular_file(path: Path) -> bytes:
    """The bytes of a regular file: a symlink, a FIFO, a device or a directory is refused (a FIFO would hang)."""
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise Refused(f"cannot stat {path}: {exc.strerror}") from None
    if not stat.S_ISREG(st.st_mode):
        raise Refused(f"{path} is not a regular file (a symlink, FIFO or device is refused)")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Refused(f"{path} is not a regular file")
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(fd)


def active_key(env_path: Path) -> str:
    """The probe's ENV_ACTIVE_KEY for this file: split on newlines, trailing CRs stripped, last match wins."""
    try:
        text = read_regular_file(env_path).decode("utf-8")
    except UnicodeDecodeError:
        raise Refused(f"{env_path} is not valid UTF-8; the probe would not have read it as this tool does") from None
    value = None
    for line in text.split("\n"):
        s = line.rstrip("\r")
        if COMMENTED.match(s):
            continue
        m = ACTIVE.match(s)
        if m:
            value = m.group(2)
    if value is None:
        raise Refused(f"{env_path} has no uncommented SETTINGS_ENCRYPTION_KEY= line: no {LABEL} candidate (is this the moved-aside service .env?)")
    if not value:
        raise Refused(f"{env_path}'s last SETTINGS_ENCRYPTION_KEY= line is empty")
    return value


def connect_ro(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)


def db_key_hash(db_path: Path) -> str:
    """The one key hash the probe's queries find; refuses unless the parse verifies on every blob and exactly one
    key hash is present."""
    if not db_path.is_file():
        raise Refused(f"no database at {db_path}")
    con = connect_ro(db_path)
    blobs = []
    try:
        for sql in PROBE_SQL:
            try:
                blobs += [r[0] for r in con.execute(sql) if r[0] and str(r[0]).startswith("enc-v1:")]
            except sqlite3.Error as exc:
                # The class only: Python's "Could not decode to UTF-8 column ... with text '...'" quotes the value.
                raise Refused(f"query error on {db_path} ({type(exc).__name__}; text not shown): a server database copy is expected -- the job index BMXWPAOGLP.sqlite has no such tables") from None
    finally:
        con.close()
    if not blobs:
        raise Refused(f"{db_path} holds no enc-v1 blob in the probe's columns: nothing to match against (wrong file, or a cleartext database)")
    parse_ok = 0
    keyhashes = set()
    for b in blobs:
        body = str(b)[len("enc-v1:"):]
        ch, kh, content = body[:64], body[64:128], body[128:]
        if ch.upper() == sha(content):
            parse_ok += 1
        keyhashes.add(kh.upper())
    print(f"database: encrypted blobs={len(blobs)} content-hash-verified={parse_ok} distinct-key-hashes={len(keyhashes)}")
    if parse_ok != len(blobs):
        raise Refused("not every blob's content hash verifies: the layout parse is wrong for this file, so no key hash can be trusted")
    if len(keyhashes) != 1:
        raise Refused("the blobs carry more than one key hash: no single settings key opens this database")
    return next(iter(keyhashes))


def other_key_blobs(db_path: Path, gate, target: str) -> tuple[int, int, str]:
    """(blobs in the gate's five columns, how many carry another key hash, per-column counts). Values are read
    as bytes and decoded with errors='replace' (the gate's as_text), so no decode error can quote one."""
    con = connect_ro(db_path)
    con.text_factory = bytes
    # Off: SQLite would otherwise read a missing double-quoted column ("BaseUrl") as the string 'BaseUrl', so a
    # table without it would count 0 blobs instead of failing (lane R2-A, measured on 3.46.1 and 3.53.4).
    con.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)
    total = other = 0
    parts = []
    try:
        for sql, name in gate.COLUMNS:
            try:
                found = gate.blobs_of(con, sql)
            except sqlite3.Error as exc:
                # Only a missing table is "absent", as in the gate; any other error refuses, by class only.
                if isinstance(exc, sqlite3.OperationalError) and str(exc).startswith("no such table"):
                    parts.append(f"{name}=absent")
                    continue
                raise Refused(f"query error on {db_path} reading {name} ({type(exc).__name__}; text not shown)") from None
            bad = sum(1 for b in found if gate.key_hash_of(b) != target)
            parts.append(f"{name}={len(found)}" + (f" ({bad} under another key)" if bad else ""))
            total += len(found)
            other += bad
    finally:
        con.close()
    return total, other, " ".join(parts)


def undeliverable(v: str):
    """Why the credential file cannot hand the server exactly this text, or None."""
    if "\0" in v:
        return "it holds a NUL byte (the wrapper refuses one; `$(<file)` would drop it)"
    if "\r" in v:
        return "it holds a carriage return (the wrapper refuses one)"
    if "\n" in v:
        return "it holds a newline (`$(<file)` drops a trailing one, and the gate refuses a multi-line key)"
    if v != v.strip():
        return "it begins or ends with whitespace (the wrapper refuses ASCII whitespace there; this tool refuses any, so it is never looser)"
    return None


def open_out_dir(out: Path) -> int:
    """An O_NOFOLLOW descriptor on --out's directory, after checking it and that --out does not exist."""
    try:
        dfd = os.open(out.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        raise Refused(f"cannot open {out.parent} as a directory without following a symlink: {exc.strerror}") from None
    try:
        st = os.fstat(dfd)
        if st.st_uid != os.geteuid():
            raise Refused(f"{out.parent} is not owned by the effective user (uid {os.geteuid()}); /etc/credstore is root's")
        if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise Refused(f"{out.parent} is writable by its group or by others")
        try:
            os.stat(out.name, dir_fd=dfd, follow_symlinks=False)
        except FileNotFoundError:
            return dfd
        raise Refused(f"{out} already exists: never write over a key (a re-run must not replace a key the database may already be under)")
    except BaseException:
        os.close(dfd)
        raise


def write_exclusive(dfd: int, name: str, data: bytes) -> None:
    """Create name in dfd (never over an existing entry), write data, fsync it and the directory. On any failure
    after the create, the file is removed before the error propagates, so no partial key is left behind."""
    old = os.umask(0o077)
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dfd)
    finally:
        os.umask(old)
    try:
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
            os.fchmod(fd, 0o600)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(dfd)
    except BaseException:
        os.unlink(name, dir_fd=dfd)
        raise


def load_gate():
    sys.dont_write_bytecode = True   # run as root from pcalnon's checkout: no root-owned __pycache__ there
    spec = importlib.util.spec_from_file_location("rekey_gate", GATE)
    if spec is None or spec.loader is None:
        raise Refused(f"cannot load {GATE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_back(out: Path, target: str, gate) -> None:
    """Both reads must hash to the database's key hash; raises Refused otherwise."""
    key = gate.read_key(str(out))
    if key is None or sha(key) != target:
        raise Refused("read-back through the gate's read_key does not match the database's key hash")
    r = subprocess.run(["bash", "-c", BASH_READ, "bash", str(out)], capture_output=True, text=True, check=False)
    got = r.stdout.split()[0].upper() if r.returncode == 0 and r.stdout.split() else ""
    if got != target:
        raise Refused(f"read-back through bash's $(<file) does not match the database's key hash (bash exit {r.returncode})")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Procedure A only: write the matched form of the moved-aside .env's settings key to the credential path, verified, never printed.")
    ap.add_argument("--env", required=True, type=Path, help="the moved-aside service .env (step 6's /home/duplicati/.config/Duplicati.empty-2026-09-20/.env)")
    ap.add_argument("--db", required=True, type=Path, help="the probe's scratch COPY of the freeze's Duplicati-server.sqlite")
    ap.add_argument("--out", required=True, type=Path, help="the credential path (/etc/credstore/duplicati-settings-key); must not exist")
    ap.add_argument("--dry-run", action="store_true", help="verify the match and the form; write nothing")
    args = ap.parse_args(argv[1:])
    # No core file can carry the key's memory: SIGQUIT's default action dumps core into the working directory.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    dfd = None
    try:
        dfd = open_out_dir(args.out)
        key = active_key(args.env)
        print(f"candidates loaded: ['{LABEL}'] ({len(key)} chars as written in the file)")
        target = db_key_hash(args.db)
        forms = variants(key)
        matched = sorted(name for name, value in forms.items() if value and sha(value) == target)
        if not matched:
            raise Refused(f"key-hash match: NONE of the {LABEL} variants. If step 7's probe reported an {LABEL} match, STOP: the two disagree "
                          f"(are --env and --db the probe's own paths?) -- never route to A0 on this line, and keep the .env. "
                          f"If the probe reported no match either, this is Procedure A0")
        print(f"key-hash match: {[f'{LABEL}/{name}' for name in matched]}")
        gate = load_gate()
        total, other, report = other_key_blobs(args.db, gate, target)
        print(f"the gate's five columns: blobs={total} under-another-key={other} [{report}]")
        if other:
            raise Refused("blobs in the gate's columns carry another key hash: no single key opens this database, and step 13's exit gate would fail. STOP; ask the owner (A0 is the fallback)")
        value = forms[matched[0]]
        why = undeliverable(value)
        if why:
            raise Refused(f"the matched form cannot be delivered through the credential file: {why}. STOP: Procedure A cannot run on this key; ask the owner (A0 is the fallback)")
        print(f"deliverable through the credential file: yes ({len(value)} chars, written without a trailing newline)")
        if args.dry_run:
            print(f"dry run: would write {args.out} (0600, owner uid {os.geteuid()}); nothing written")
            return 0
        # From just before the create until the keep-or-remove decision is printed, an interruption waits: a
        # SIGTERM or SIGHUP would otherwise end the process with an unverified key at the credential path, and a
        # Ctrl-C landing just after the open would leave an empty one (lane R2-A, R2A-2). SIGKILL cannot wait.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, DEFERRED)
        try:
            write_exclusive(dfd, args.out.name, value.encode("utf-8"))
            try:
                read_back(args.out, target, gate)
            except BaseException:
                # Refused or an I/O error: an unverified key must not stay at the credential path.
                remove_created(dfd, args.out)
                raise
            st = os.stat(args.out)
            print(f"wrote {args.out}: mode {stat.S_IMODE(st.st_mode):04o}, uid {st.st_uid}, gid {st.st_gid}, {st.st_size} bytes; read back through the gate's read_key and through bash's $(<file): both match the database's key hash")
            return 0
        finally:
            # The decision is made and printed: only now may a deferred signal end the process.
            sys.stdout.flush()
            sys.stderr.flush()
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"FATAL: {exc.strerror} ({exc.filename})", file=sys.stderr)
        return 2
    finally:
        if dfd is not None:
            os.close(dfd)


def remove_created(dfd: int, out: Path) -> None:
    """After a failed read-back, remove the key file this run created, through the directory it was created in: an
    unverified key at the credential path is what brings back I-38's mismatch loop at the next start."""
    try:
        os.unlink(out.name, dir_fd=dfd)
        print(f"removed {out}, which this run created; nothing is left at the credential path", file=sys.stderr)
    except OSError as exc:
        print(f"WARNING: could not remove {out}, which this run created: {exc.strerror} -- remove it before any start", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
