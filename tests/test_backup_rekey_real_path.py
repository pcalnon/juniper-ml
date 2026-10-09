#!/usr/bin/env python3
"""The re-key's NON-dry-run path and every state its EXIT trap can be left in, against stubs.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-10-03_rekey_settings_key.bash`` was only ever run with ``--dry-run``, whose "would:"
lines are literals separate from the commands they describe: 8 of its 9 mutants survived the suites
(Phase B round 3, R3C D-5), and its EXIT trap printed wrong recovery text in four states (R3A D-4,
R3B N-11, R3C D-1). Built from round 3 lane C's harness
(``util/ad-hoc/2026-10-04_backup-phase-b-round3/r3c-harness/``: ``mkstubs.bash``, ``t4_rekey_trap.py``,
``t4_rerun.py``, ``t4_timer_state.py``).

How it is hermetic:

* the script runs from a COPY whose credential folder and drop-in folder (``CRED_DIR``,
  ``DROPIN_DIR``) are rewritten into a per-test scratch root -- each anchor must occur exactly once, and
  the copy must name no ``/etc/credstore`` or ``/run/systemd`` assignment afterwards; the installed unit
  comes through the script's own ``REKEY_INSTALLED_UNIT`` hook, the data folder through
  ``DUPLICATI_DATA_FOLDER``, the work folder through ``REKEY_WORKDIR``;
* ``systemctl``, ``journalctl``, ``sudo``, ``id``, ``stat``, ``chown``, ``chmod``, ``sleep`` and
  ``install`` are PATH stubs; the ``install`` stub refuses any host path; the API client is a stub;
* ``systemctl start`` runs a FAKE SERVER on the scratch database that does what 2.4.0.0's
  ``ReWriteAllFieldsIfEncryptionChanged`` does at the level the gate can see: with the drop-in's
  ``--disable-db-encryption`` it decrypts every rewritten field and sets ``encrypted-fields`` False;
  without it, when the flag disagrees, it encrypts them under the key at the credential path. Like
  the product (Connection.cs 131-153) it rewrites the settings rows at BackupID -1 and -2 and each
  EXISTING backup with its Option, Source and BackupTargetUrl rows, and never touches
  ``ConnectionString`` or an Option/Source/BackupTargetUrl row whose BackupID names no backup (round 4,
  R4C DEFECT-2: the first version rewrote every Option and Source row, which hid that gap);
* the REAL exit gate (``util/ad-hoc/2026-10-03_rekey_gate.py``) judges the copy. Keys are fake.

Nothing touches ``/etc``, ``/run``, a unit, a Duplicati binary or a secret file: the dry-run test sets
``REKEY_CREDSTORE_DIR`` (honoured under ``--dry-run`` only) as well as ``REKEY_INSTALLED_UNIT`` (round 4,
R4C NIT-8: it used to stat ``/etc/credstore``).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
REKEY = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_rekey_settings_key.bash"
GATE = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_rekey_gate.py"
REPO_UNIT = REPO_ROOT / "util" / "systemd" / "duplicati.service"

OLD = "OLDKEY-fake-not-a-secret-0001"
NEW = "NEWKEY-fake-not-a-secret-0002"
VENDOR = "/usr/lib/systemd/system/duplicati.service"
PREFIX = "enc-v1:"

# Rewrites of the script copy: each anchor must be unique, so a renamed variable fails loudly here.
ANCHORS = {
    "CRED_DIR=/etc/credstore\n": "CRED_DIR={root}/etc/credstore\n",
    "DROPIN_DIR=/run/systemd/system/${UNIT}.d\n": "DROPIN_DIR={root}/run/systemd/system/${{UNIT}}.d\n",
}


def blob(key: str, plaintext: str) -> str:
    return PREFIX + hashlib.sha256(plaintext.encode()).hexdigest().upper() + hashlib.sha256(key.encode()).hexdigest().upper() + plaintext


FAKE_SERVER = r"""
import hashlib, os, sqlite3, sys
PREFIX = "enc-v1:"
db, cred, dropin = sys.argv[1:4]
key = open(cred, encoding="utf-8", newline="").read().rstrip("\n")
disable = os.path.exists(dropin) and "--disable-db-encryption" in open(dropin).read()
want_encrypted = not disable
khash = hashlib.sha256(key.encode()).hexdigest().upper()
def dec(v):
    if v and v.startswith(PREFIX) and v[len(PREFIX) + 64:len(PREFIX) + 128] == khash:
        return v[len(PREFIX) + 128:]
    return v
def enc(v):
    if not v or v.startswith(PREFIX):
        return v
    return PREFIX + hashlib.sha256(v.encode()).hexdigest().upper() + khash + v
con = sqlite3.connect(db)
row = con.execute('SELECT "Value" FROM "Option" WHERE "BackupID" = -2 AND "Name" = ?', ("encrypted-fields",)).fetchone()
flag = bool(row) and row[0] == "True"
if flag != want_encrypted:
    f = enc if want_encrypted else dec
    # Like the product: settings -1/-2 and each EXISTING backup's children are re-saved; an orphan is not.
    live = ' AND ("BackupID" IN (-1, -2) OR "BackupID" IN (SELECT "ID" FROM "Backup"))'
    for rid, v in con.execute('SELECT rowid, "Value" FROM "Option" WHERE "Name" IN (?, ?)' + live, ("passphrase", "pbkdf-config")).fetchall():
        con.execute('UPDATE "Option" SET "Value" = ? WHERE rowid = ?', (f(dec(v)), rid))
    child = ' WHERE "BackupID" IN (SELECT "ID" FROM "Backup")'
    for table, col, where in (("Backup", "TargetURL", ""), ("Source", "Path", child), ("BackupTargetUrl", "TargetURL", child)):
        for rid, v in con.execute(f'SELECT rowid, "{col}" FROM "{table}"{where}').fetchall():
            con.execute(f'UPDATE "{table}" SET "{col}" = ? WHERE rowid = ?', (f(dec(v)), rid))
    con.execute('DELETE FROM "Option" WHERE "BackupID" = -2 AND "Name" = ?', ("encrypted-fields",))
    con.execute('INSERT INTO "Option" VALUES (-2, \'\', ?, ?)', ("encrypted-fields", "True" if want_encrypted else "False"))
    con.commit()
con.close()
"""

SYSTEMCTL = r"""
import os, subprocess, sys
root = os.environ["STUB_ROOT"]
log = os.path.join(root, "stub.log")
args = sys.argv[1:]
line = " ".join(args)
with open(log, "a") as fh:
    fh.write("SYSTEMCTL " + line + "\n")
def count(prefix):
    return sum(1 for x in open(log) if x.startswith(prefix))
state_file = os.path.join(root, "unit_state")
state = open(state_file).read().strip() if os.path.exists(state_file) else "active"
fail = os.environ.get("STUB_SYSTEMCTL_FAIL", "")
if fail and fail in line:
    sys.exit(1)
verb = args[0] if args else ""
unit = args[-1] if args else ""
if verb == "stop" and unit == "duplicati.service":
    if str(count("SYSTEMCTL stop duplicati.service")) == os.environ.get("STUB_FAIL_NTH_STOP", ""):
        sys.exit(1)
    open(state_file, "w").write("inactive")
elif verb == "start" and unit == "duplicati.service":
    n = count("SYSTEMCTL start duplicati.service")
    dropin = os.environ["STUB_DROPIN"]
    with open(log, "a") as fh:
        fh.write("DROPIN-AT-START " + ("present" if os.path.exists(dropin) else "absent") + "\n")
    if os.path.exists(dropin):
        with open(dropin) as src, open(os.path.join(root, f"dropin-at-start-{n}"), "w") as dst:
            dst.write(src.read())
    if str(n) not in os.environ.get("STUB_SERVER_INERT_FOR", "").split():
        subprocess.run([sys.executable, os.path.join(root, "fake_server.py"), os.environ["STUB_DB"], os.environ["STUB_CRED"], dropin], check=True)
    open(state_file, "w").write("active")
elif verb == "show" and "FragmentPath" in line:
    later = os.environ.get("STUB_FRAGMENT_AFTER_RELOADS")
    if later and count("SYSTEMCTL daemon-reload") >= int(later):
        print(os.environ["STUB_FRAGMENT_LATER"])
    else:
        print(os.environ.get("STUB_FRAGMENT", ""))
elif verb == "is-active":
    print(state if unit == "duplicati.service" else os.environ.get("STUB_TIMER_ACTIVE", "inactive"))
elif verb == "is-enabled":
    print(os.environ.get("STUB_TIMER_ENABLED", "disabled"))
sys.exit(0)
"""

JOURNALCTL = r"""
import os, sys
root = os.environ["STUB_ROOT"]
log = os.path.join(root, "stub.log")
n = sum(1 for x in open(log) if x.startswith("SYSTEMCTL start duplicati.service"))
if str(n) in os.environ.get("STUB_START_LINE_FOR", "1 2 3 4 5 6 7 8 9").split():
    print("Oct 08 duplicati-server[1]: Server has started")
"""

API_STUB = r"""#!/usr/bin/env python3
import json, os, sys
root = os.environ["STUB_ROOT"]
log = os.path.join(root, "stub.log")
args = sys.argv[1:]
if args[:1] == ["--help"]:
    print("usage: yamaguchi_server_api.py {status,serverstate,pause,resume,export}")
    sys.exit(0)
verb = args[0] if args else ""
with open(log, "a") as fh:
    fh.write("API " + " ".join(args) + "\n")
if verb in os.environ.get("STUB_API_FAIL", "").split():
    sys.exit(1)
state_file = os.path.join(root, "api_state")
paused = os.path.exists(state_file) and open(state_file).read().strip() == "Paused"
if verb == "pause":
    open(state_file, "w").write("Paused")
elif verb == "resume":
    open(state_file, "w").write("Running")
elif verb == "serverstate":
    if os.environ.get("STUB_FAIL_SERVERSTATE_AFTER_RESUME") and "API resume" in open(log).read():
        sys.exit(1)
    active = os.environ.get("STUB_ACTIVE_TASK") or None
    print(json.dumps({"ProgramState": "Paused" if paused else "Running", "ActiveTask": {"Item1": 2, "Item2": active} if active else None}))
    sys.exit(2 if paused else 0)
"""

SHELL_STUBS = {
    "sudo": 'printf "SUDO %s\\n" "$*" >> "${STUB_ROOT}/stub.log"\nwhile (( $# )); do case "$1" in -u) shift 2 ;; --) shift; break ;; -*) shift ;; *) break ;; esac; done\nexec "$@"\n',
    "id": 'if [[ "$#" -eq 1 && "$1" == "-u" ]]; then echo "${STUB_UID:-0}"; exit 0; fi\nexec /usr/bin/id "$@"\n',
    "chown": 'printf "CHOWN %s\\n" "$*" >> "${STUB_ROOT}/stub.log"\n',
    "sleep": ":\n",
    "stat": 'if [[ "$#" -eq 3 && "$1" == "-c" && "$2" == "%U:%a" && "$3" == "${STUB_ROOT}/etc/credstore/"* && -e "$3" ]]; then printf "root:%s\\n" "$(/usr/bin/stat -c %a "$3")"; exit 0; fi\nexec /usr/bin/stat "$@"\n',
    "mv": 'if [[ "${STUB_MV_FAIL:-0}" == 1 ]]; then echo "mv stub: refused" >&2; exit 1; fi\nexec /usr/bin/mv "$@"\n',
    "chmod": 'if [[ "${STUB_CHMOD_FAIL_AFTER_MV:-0}" == 1 && "$#" -eq 2 && "$2" == "${STUB_CRED}" && ! -e "${STUB_CRED}.new" ]]; then exit 1; fi\nexec /usr/bin/chmod "$@"\n',
    "install": 'for a in "$@"; do case "$a" in /etc/*|/usr/*|/run/*|/root*|/home/duplicati*) echo "install stub REFUSES a host path: $a" >&2; exit 97 ;; esac; done\nexec /usr/bin/install "$@"\n',
}


class _RekeyRun(unittest.TestCase):
    """A scratch root with the script copy, the stubs, two fake keys and a database under the OLD key."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="rekey-real-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.script = self.make_script(self.root)
        repo_adhoc = self.root / "repo" / "util" / "ad-hoc"
        (repo_adhoc / "yamaguchi_server_api.py").write_text(API_STUB)
        shutil.copy(GATE, repo_adhoc / GATE.name)
        (self.root / "repo" / "util" / "systemd").mkdir(parents=True)
        shutil.copy(REPO_UNIT, self.root / "repo" / "util" / "systemd" / "duplicati.service")
        self.installed = self.root / "etc" / "systemd" / "system" / "duplicati.service"
        self.installed.parent.mkdir(parents=True)
        shutil.copy(REPO_UNIT, self.installed)
        self.cred = self.root / "etc" / "credstore" / "duplicati-settings-key"
        self.cred_new = self.cred.with_name(self.cred.name + ".new")
        self.cred_old = self.cred.with_name(self.cred.name + ".old")
        self.cred.parent.mkdir(parents=True)
        for path, value in ((self.cred, OLD), (self.cred_new, NEW)):
            path.write_text(value + "\n")
            path.chmod(0o600)
        self.dropin = self.root / "run" / "systemd" / "system" / "duplicati.service.d" / "zz-rekey-disable-db-encryption.conf"
        (self.root / "run" / "systemd" / "system").mkdir(parents=True)
        self.data = self.root / "data"
        self.data.mkdir(mode=0o700)
        self.db = self.data / "Duplicati-server.sqlite"
        self.make_db()
        (self.root / "fake_server.py").write_text(FAKE_SERVER)
        bindir = self.root / "stubbin"
        bindir.mkdir()
        for name, body in (("systemctl", SYSTEMCTL), ("journalctl", JOURNALCTL)):
            (bindir / name).write_text(f"#!{sys.executable}\n" + body)
        for name, body in SHELL_STUBS.items():
            (bindir / name).write_text("#!/usr/bin/env bash\n" + body)
        for f in bindir.iterdir():
            f.chmod(0o755)

    @staticmethod
    def make_script(root: Path) -> Path:
        text = REKEY.read_text(encoding="utf-8")
        for anchor, replacement in ANCHORS.items():
            if text.count(anchor) != 1:
                raise AssertionError(f"rewrite anchor not unique in {REKEY.name}: {anchor!r} ({text.count(anchor)}x)")
            text = text.replace(anchor, replacement.format(root=root))
        for host in ("CRED_DIR=/etc/", "CRED=/etc/", "CRED_NEW=/etc/", "DROPIN_DIR=/run/"):
            if host in text:
                raise AssertionError(f"the copy still assigns a host path: {host}")
        adhoc = root / "repo" / "util" / "ad-hoc"
        adhoc.mkdir(parents=True)
        script = adhoc / "rekey.bash"
        script.write_text(text, encoding="utf-8")
        return script

    def make_db(self, connection_string: bool = False, orphan_target: bool = False, orphan_option: bool = False, orphan_source: bool = False) -> None:
        con = sqlite3.connect(self.db)
        con.executescript('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT);' 'CREATE TABLE "Backup" ("ID" INTEGER, "Name" TEXT, "TargetURL" TEXT, "DBPath" TEXT);' 'CREATE TABLE "Source" ("BackupID" INTEGER, "Path" TEXT);' 'CREATE TABLE "ConnectionString" ("ID" INTEGER, "BaseUrl" TEXT);' 'CREATE TABLE "BackupTargetUrl" ("ID" INTEGER, "BackupID" INTEGER, "TargetURL" TEXT);')
        con.execute("INSERT INTO \"Option\" VALUES (-2, '', ?, ?)", ("encrypted-fields", "True"))
        con.execute("INSERT INTO \"Option\" VALUES (-2, '', ?, ?)", ("pbkdf-config", blob(OLD, "pbkdf")))
        con.execute("INSERT INTO \"Option\" VALUES (-1, '', ?, ?)", ("passphrase", blob(OLD, "anybackup")))  # ANY_BACKUP_ID: rewritten, not an orphan
        con.execute("INSERT INTO \"Option\" VALUES (2, '', ?, ?)", ("passphrase", blob(OLD, "pass")))
        con.execute('INSERT INTO "Backup" VALUES (2, ?, ?, ?)', ("Yamaguchi", blob(OLD, "target"), "x.sqlite"))
        con.execute('INSERT INTO "Source" VALUES (2, ?)', (blob(OLD, "source"),))
        con.execute('INSERT INTO "BackupTargetUrl" VALUES (1, 2, ?)', (blob(OLD, "attached"),))
        if connection_string:
            con.execute('INSERT INTO "ConnectionString" VALUES (1, ?)', (blob(OLD, "conn"),))
        if orphan_target:
            con.execute('INSERT INTO "BackupTargetUrl" VALUES (2, 99, ?)', (blob(OLD, "orphan"),))
        if orphan_option:  # no FK on Option (Schema.sql 44-45): a deleted job's options can outlive it
            con.execute("INSERT INTO \"Option\" VALUES (7, '', ?, ?)", ("passphrase", blob(OLD, "orphan-option")))
        if orphan_source:  # no FK on Source (Schema.sql 72-73)
            con.execute('INSERT INTO "Source" VALUES (7, ?)', (blob(OLD, "orphan-source"),))
        con.commit()
        con.close()

    def env(self, **extra: str) -> RedactedEnv:
        env = RedactedEnv(
            os.environ,
            PATH=f"{self.root / 'stubbin'}:{os.environ['PATH']}",
            STUB_ROOT=str(self.root),
            STUB_DB=str(self.db),
            STUB_CRED=str(self.cred),
            STUB_DROPIN=str(self.dropin),
            STUB_FRAGMENT=str(self.installed),
            REKEY_INSTALLED_UNIT=str(self.installed),
            REKEY_WORKDIR=str(self.root / "workdir"),
            DUPLICATI_DATA_FOLDER=str(self.data),
            PYTHONDONTWRITEBYTECODE="1",
        )
        env.pop("SUDO_USER", None)
        env.update(extra)
        return env

    def rekey(self, **extra: str) -> subprocess.CompletedProcess:
        r = subprocess.run(["bash", str(self.script)], env=self.env(**extra), capture_output=True, text=True, timeout=300, check=False)
        self.assertNotIn(OLD, r.stdout + r.stderr, "a key value was printed")
        self.assertNotIn(NEW, r.stdout + r.stderr, "a key value was printed")
        return r

    def systemctl(self, *args: str, **extra: str) -> None:
        subprocess.run([str(self.root / "stubbin" / "systemctl"), *args], env=self.env(**extra), check=True)

    def gate(self, key_file: Path) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(GATE), str(self.db), str(key_file)], capture_output=True, text=True, check=False)

    def tag(self, path: Path) -> str:
        if not path.exists():
            return "absent"
        v = path.read_text().rstrip("\n")
        return {OLD: "OLD", NEW: "NEW"}.get(v, "other")

    def keys(self) -> tuple[str, str, str]:
        return self.tag(self.cred), self.tag(self.cred_old), self.tag(self.cred_new)

    def log(self) -> list[str]:
        p = self.root / "stub.log"
        return p.read_text().splitlines() if p.exists() else []

    def count(self, prefix: str) -> int:
        return sum(1 for x in self.log() if x.startswith(prefix))

    def unit_state(self) -> str:
        p = self.root / "unit_state"
        return p.read_text().strip() if p.exists() else "active"

    def flag(self) -> str | None:
        con = sqlite3.connect(self.db)
        try:
            row = con.execute('SELECT "Value" FROM "Option" WHERE "BackupID" = -2 AND "Name" = ?', ("encrypted-fields",)).fetchone()
        finally:
            con.close()
        return row[0] if row else None

    def recovery(self, r: subprocess.CompletedProcess) -> str:
        """The trap's RECOVERY text, continuation lines included."""
        lines, keep = [], False
        for ln in r.stderr.splitlines():
            body = ln.split(": ", 1)[1] if ": " in ln else ln
            if body.startswith("RECOVERY"):
                keep = True
            elif not body.startswith(" "):
                keep = False
            if keep:
                lines.append(body)
        return "\n".join(lines)


class HappyPath(_RekeyRun):
    def test_full_run_leaves_the_database_under_the_new_key_and_nothing_behind(self):
        r = self.rekey()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.keys(), ("NEW", "absent", "absent"), "the swap must be a move, and the old key shredded at the end")
        self.assertFalse(self.dropin.exists())
        self.assertEqual(self.flag(), "True")
        g = self.gate(self.cred)
        self.assertEqual(g.returncode, 0, g.stdout + g.stderr)
        self.assertIn("under-another-key=0", g.stdout)
        self.assertEqual([x for x in self.log() if x.startswith("DROPIN-AT-START")], ["DROPIN-AT-START present", "DROPIN-AT-START absent", "DROPIN-AT-START absent"])
        execstart = next(ln for ln in self.installed.read_text().splitlines() if ln.startswith("ExecStart=")).split("=", 1)[1]
        self.assertEqual((self.root / "dropin-at-start-1").read_text(), f"[Service]\nExecStart=\nExecStart={execstart} --disable-db-encryption\n", "the drop-in must RESET ExecStart before re-declaring it (without the empty line systemd refuses a second ExecStart=)")
        self.assertEqual(self.count("SYSTEMCTL revert"), 0)
        self.assertEqual((self.root / "api_state").read_text(), "Running")
        self.assertIn("never-rewritten enc-v1 blobs: ConnectionString.BaseUrl=0", r.stderr)
        self.assertIn("exit gate PASSED", r.stderr)
        self.assertNotIn("ABORTED", r.stderr)
        self.assertEqual(list((self.root / "workdir").iterdir()), [], "every database copy is shredded")

    def test_attached_backup_target_urls_do_not_refuse(self):
        """A BackupTargetUrl row of a live backup IS rewritten by the product (Backup.cs 54, Connection.cs 892-893)."""
        r = self.rekey()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("BackupTargetUrl.TargetURL orphaned=0 attached=1", r.stderr)
        # The settings rows at -1 and -2 are the product's to rewrite (Connection.cs 145; ServerSettings.cs 851-855):
        self.assertIn("Option.Value orphaned=0 attached=3", r.stderr)


class PreflightRefusals(_RekeyRun):
    """Every refusal comes before the pause: nothing stopped, started or moved, and no RECOVERY text."""

    def assert_refused_untouched(self, r, needle):
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn(needle, r.stderr)
        self.assertIn("REFUSED with status 1 before any change", r.stderr)
        self.assertNotIn("ABORTED", r.stderr)
        self.assertNotIn("RECOVERY", r.stderr)
        self.assertEqual(self.count("SYSTEMCTL stop"), 0)
        self.assertEqual(self.count("SYSTEMCTL start"), 0)
        self.assertEqual(self.count("API pause"), 0)
        self.assertEqual(self.keys(), ("OLD", "absent", "NEW"))
        self.assertEqual(list((self.root / "workdir").glob("*")) if (self.root / "workdir").exists() else [], [], "the pre-flight copy is shredded")

    def test_refuses_a_connection_string_blob_the_product_never_rewrites(self):
        """R3A D-5 / R3C D-2: it would stay under the OLD key and fail the gate only AFTER the swap."""
        self.db.unlink()
        self.make_db(connection_string=True)
        r = self.rekey()
        self.assert_refused_untouched(r, "ConnectionString.BaseUrl=1")
        self.assertIn("never rewrites", r.stderr)

    def test_refuses_an_orphaned_backup_target_url_blob(self):
        self.db.unlink()
        self.make_db(orphan_target=True)
        r = self.rekey()
        self.assert_refused_untouched(r, "BackupTargetUrl.TargetURL orphaned=1")

    def test_refuses_an_orphaned_option_or_source_blob(self):
        """R4C DEFECT-2: neither table has an FK, the product's rewrite never reaches such a row, and the exit
        gate then failed AFTER the swap. Shown first without the refusal: the fake server, like the product,
        leaves the orphan under the OLD key."""
        for kind, needle in (("orphan_option", "Option.Value orphaned=1"), ("orphan_source", "Source.Path orphaned=1")):
            with self.subTest(kind=kind):
                self.db.unlink()
                self.make_db(**{kind: True})
                (self.root / "stub.log").unlink(missing_ok=True)
                self.assert_refused_untouched(self.rekey(), needle)
        # Why it must refuse: a start under each key leaves the orphan where it was, and the gate fails.
        self.systemctl("start", "duplicati.service")  # no drop-in, flag already True: nothing rewritten
        self.dropin.parent.mkdir(parents=True, exist_ok=True)
        self.dropin.write_text("[Service]\nExecStart=\nExecStart=x --disable-db-encryption\n")
        self.systemctl("start", "duplicati.service")  # decrypt: every LIVE field cleartext
        self.dropin.unlink()
        self.cred.write_text(NEW + "\n")
        self.systemctl("start", "duplicati.service")  # encrypt under NEW
        g = self.gate(self.cred)
        self.assertEqual(g.returncode, 1, g.stdout)
        self.assertIn("under-another-key=1", g.stdout)

    def test_refuses_when_the_count_itself_fails(self):
        """R4C X25: an `--unrewritten` crash (exit 2) must refuse, not pass as 'nothing found'."""
        self.db.write_bytes(b"this is not a sqlite database at all" * 64)
        r = self.rekey()
        self.assert_refused_untouched(r, "cannot count the never-rewritten blobs")
        self.assertIn("gate exit 2", r.stderr)

    def test_refuses_every_timer_state_that_can_fire(self):
        """R3B N-8 / R3C N-4: `is-enabled != enabled` let enabled-runtime, linked and disabled-but-active through."""
        cases = {
            ("enabled", "inactive"): "is-enabled reports 'enabled'",
            ("enabled-runtime", "inactive"): "is-enabled reports 'enabled-runtime'",
            ("linked", "inactive"): "is-enabled reports 'linked'",
            ("disabled", "active"): "is-active reports 'active'",
            # R4C X26: only 'inactive' passes -- not 'anything but active'.
            ("disabled", "activating"): "is-active reports 'activating'",
            ("disabled", "reloading"): "is-active reports 'reloading'",
        }
        for (enabled, active), needle in cases.items():
            with self.subTest(enabled=enabled, active=active):
                (self.root / "stub.log").unlink(missing_ok=True)
                r = self.rekey(STUB_TIMER_ENABLED=enabled, STUB_TIMER_ACTIVE=active)
                self.assert_refused_untouched(r, needle)

    def test_refuses_an_active_task_and_the_vendor_unit(self):
        for env, needle in (({"STUB_ACTIVE_TASK": "Backup"}, "a task is ACTIVE"), ({"STUB_FRAGMENT": VENDOR}, f"systemd loads {VENDOR}")):
            with self.subTest(needle=needle):
                (self.root / "stub.log").unlink(missing_ok=True)
                self.assert_refused_untouched(self.rekey(**env), needle)

    def test_refuses_identical_keys_and_a_foreign_old_key(self):
        self.cred_new.write_text(OLD + "\n")
        self.assert_refused_untouched_keys(self.rekey(), "hold the SAME key")
        self.cred_new.write_text(NEW + "\n")
        self.cred_old.write_text("some-other-fake-key\n")
        self.cred_old.chmod(0o600)
        r = self.rekey()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn(".old exists and is not the key at", r.stderr)
        self.assertEqual(self.count("API pause"), 0)

    def assert_refused_untouched_keys(self, r, needle):
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn(needle, r.stderr)
        self.assertEqual(self.count("API pause"), 0)

    def test_a_rerun_after_the_swap_never_advises_moving_the_old_key_back(self):
        """R3C D-1 (R1): the old trap printed 'under the OLD key ... keys: old key at …key' and 'move …key.old back'."""
        self.cred.write_text(NEW + "\n")
        self.cred_old.write_text(OLD + "\n")
        self.cred_old.chmod(0o600)
        self.cred_new.unlink()
        r = self.rekey()
        self.assertEqual(r.returncode, 1)
        self.assertIn("credential file missing or empty", r.stderr)
        self.assertIn("Do NOT move", r.stderr)
        self.assertNotIn(f"move {self.cred_old} back to {self.cred}", r.stderr)
        self.assertNotIn("under the OLD key", r.stderr)
        self.assertEqual(self.keys(), ("NEW", "OLD", "absent"))

    def test_not_root_refuses_before_anything(self):
        self.assert_refused_untouched(self.rekey(STUB_UID="1000"), "run with sudo")

    def test_an_empty_credstore_override_is_ignored(self):
        """R5A NIT-5 F21: set but EMPTY means unset -- never CRED=/duplicati-settings-key. A real run then
        reaches the ordinary refusals (here: not root, exit 1), not the hook's exit 2. Run on the scratch copy,
        so even the trap's look at `…-key.old` stays off /etc."""
        r = self.rekey(STUB_UID="1000", REKEY_CREDSTORE_DIR="")
        self.assert_refused_untouched(r, "run with sudo")
        self.assertNotIn("honoured under --dry-run only", r.stderr)


class TrapStates(_RekeyRun):
    """Each failure point: the state the trap prints must be the state on disk, and only one recovery branch."""

    def assert_one_branch(self, r):
        self.assertEqual(self.recovery(r).count("RECOVERY:"), 1 + ("RECOVERY, FIRST" in r.stderr), self.recovery(r))

    def test_pause_fails_nothing_else_changed(self):
        r = self.rekey(STUB_API_FAIL="pause")
        self.assertEqual(r.returncode, 1)
        self.assertIn("database under the OLD key (no start with the drop-in was made)", r.stderr)
        self.assertIn("keys UNSWAPPED", r.stderr)
        self.assertIn("nothing but the pause changed", self.recovery(r))
        self.assertIn("scheduler is PAUSED, or may be", r.stderr)
        self.assert_one_branch(r)

    def test_decrypt_start_times_out_after_the_server_decrypted(self):
        """R3A D-4 / R3B N-11: the rewrite runs before 'Server has started'; the trap must stop the unit and say UNKNOWN."""
        r = self.rekey(STUB_START_LINE_FOR="")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no 'Server has started' within 120 s", r.stderr)
        self.assertEqual(self.flag(), "False", "the fake server did decrypt")
        self.assertIn("database UNKNOWN -- a decrypt start was attempted", r.stderr)
        self.assertNotIn("nothing changed yet", r.stderr)
        self.assertIn("stopping duplicati.service first", r.stderr)
        self.assertEqual(self.unit_state(), "inactive", "the trap must stop a unit started with --disable-db-encryption")
        self.assertFalse(self.dropin.exists())
        self.assertIn("keys were NOT swapped", self.recovery(r))
        self.assert_one_branch(r)
        self.follow_unswapped_recovery()

    def follow_unswapped_recovery(self):
        """Do what the printed branch says: start the unit, then re-run from the top. It must complete."""
        self.systemctl("start", "duplicati.service")
        self.assertEqual(self.flag(), "True")
        self.assertEqual(self.gate(self.cred).returncode, 0, "a start under the OLD key re-encrypts under it")
        r = self.rekey()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.keys(), ("NEW", "absent", "absent"))
        self.assertEqual(self.gate(self.cred).returncode, 0)

    def test_copy_done_move_failed_reads_as_unswapped_and_recovers(self):
        """R4C X24: `cp` of the old key succeeded and the `mv` failed -- `.old` holds the OLD key beside an
        unswapped pair. That is 'not swapped', not an unexpected layout, and a re-run is allowed."""
        r = self.rekey(STUB_MV_FAIL="1")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.keys(), ("OLD", "OLD", "NEW"))
        self.assertIn("keys UNSWAPPED", r.stderr)
        self.assertIn("keys were NOT swapped", self.recovery(r))
        self.assertNotIn("UNEXPECTED layout", r.stderr)
        self.assert_one_branch(r)
        self.follow_unswapped_recovery()

    def test_trap_stop_fails_prints_stop_first(self):
        """R4C X40: the decrypt start timed out and the trap's own stop failed, so the unit still runs with
        --disable-db-encryption in its argv: the FIRST recovery line must say to stop it."""
        r = self.rekey(STUB_START_LINE_FOR="", STUB_FAIL_NTH_STOP="2")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.unit_state(), "active")
        rec = self.recovery(r)
        self.assertTrue(rec.startswith("RECOVERY, FIRST: duplicati.service is still active"), rec)
        self.assertIn("systemctl stop duplicati.service", rec.splitlines()[0])
        self.assertIn("keys were NOT swapped", rec)

    def test_decrypt_start_command_fails(self):
        r = self.rekey(STUB_SYSTEMCTL_FAIL="start duplicati.service")
        self.assertEqual(r.returncode, 1)
        self.assertIn("database UNKNOWN -- a decrypt start was attempted", r.stderr)
        self.assertFalse(self.dropin.exists())
        self.assertIn("keys were NOT swapped", self.recovery(r))

    def test_stop_after_the_decrypt_start_fails(self):
        """R3C D-1 (F2): the old trap said 'leave the NEW key at …key' -- it was not there -- and left the unit running."""
        r = self.rekey(STUB_FAIL_NTH_STOP="2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("database CLEARTEXT (the decrypt start completed)", r.stderr)
        self.assertEqual(self.keys(), ("OLD", "absent", "NEW"))
        self.assertIn("keys UNSWAPPED", r.stderr)
        self.assertEqual(self.unit_state(), "inactive")
        self.assertNotIn("leave the NEW key", self.recovery(r))
        self.assertIn("keys were NOT swapped", self.recovery(r))
        self.assert_one_branch(r)
        self.follow_unswapped_recovery()

    def test_chmod_after_the_move_fails_reads_as_swapped(self):
        """R3C D-1 (F2b): the old trap reported the keys unswapped after a completed mv."""
        r = self.rekey(STUB_CHMOD_FAIL_AFTER_MV="1")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.keys(), ("NEW", "OLD", "absent"))
        self.assertIn("keys SWAPPED", r.stderr)
        self.assertIn("the keys WERE swapped", self.recovery(r))
        self.assert_one_branch(r)

    def test_vendor_unit_after_the_dropin_removal_never_says_start_first(self):
        """R3C D-1 (F3): 'do NOT start the unit' was followed by '... and start the unit'."""
        r = self.rekey(STUB_FRAGMENT_AFTER_RELOADS="2", STUB_FRAGMENT_LATER=VENDOR)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.count("SYSTEMCTL start"), 1, "no encrypt start under the vendor unit")
        rec = self.recovery(r)
        self.assertTrue(rec.startswith("RECOVERY: do NOT start duplicati.service"), rec)
        self.assertIn("Re-run the installer", rec)
        self.assertIn("keys SWAPPED", r.stderr)
        self.assertIn("database CLEARTEXT", r.stderr)
        # Then the branch's own sequence (installer re-run modelled by the fragment being right again):
        self.systemctl("start", "duplicati.service")
        self.assertEqual(self.gate(self.cred).returncode, 0, "a start under the NEW key encrypts the cleartext database under it")

    def test_encrypt_start_never_logs_started(self):
        r = self.rekey(STUB_START_LINE_FOR="1 3")
        self.assertEqual(r.returncode, 1)
        self.assertIn("database UNKNOWN -- an encrypt start was attempted", r.stderr)
        self.assertIn("keys SWAPPED", r.stderr)
        self.assertIn("the keys WERE swapped", self.recovery(r))
        self.assertNotIn("do NOT start", self.recovery(r))

    def test_gate_failure_prints_the_counts_and_not_under_the_new_key(self):
        """R3C D-1 (F4): 'GATE FAILED' was followed by 'database under the NEW key (the encrypt start completed …)'."""
        r = self.rekey(STUB_SERVER_INERT_FOR="2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("GATE FAILED", r.stderr)
        self.assertIn("STATE: gate counts: encrypted-fields=False", r.stderr)
        self.assertIn("database NOT verified: the exit gate FAILED", r.stderr)
        self.assertNotIn("under the NEW key (the encrypt start completed", r.stderr)
        self.assertIn("do NOT shred", self.recovery(r))
        self.assertEqual(self.keys(), ("NEW", "OLD", "absent"), "the old key is kept")
        self.assert_one_branch(r)

    def test_failure_after_the_gate_passed(self):
        r = self.rekey(STUB_FAIL_SERVERSTATE_AFTER_RESUME="1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("database under the NEW key (verified by the gate on a copy)", r.stderr)
        self.assertIn("only then shred", self.recovery(r))
        self.assertEqual(self.keys(), ("NEW", "OLD", "absent"))
        self.assertNotIn("scheduler is PAUSED", r.stderr, "the resume returned")
        self.assert_one_branch(r)


class DryRunHermetic(unittest.TestCase):
    """R3C D-4 / R4C NIT-8: REKEY_INSTALLED_UNIT and REKEY_CREDSTORE_DIR keep the dry run off /etc."""

    def test_installed_unit_and_credstore_overrides_are_read(self):
        with tempfile.TemporaryDirectory(prefix="rekey-dry-") as tmp:
            unit = Path(tmp) / "duplicati.service"
            unit.write_text(textwrap.dedent("""\
                [Service]
                ExecStart=/opt/marker/duplicati-wrapper.bash --marker
                """))
            credstore = Path(tmp) / "credstore"
            env = RedactedEnv(os.environ, REKEY_INSTALLED_UNIT=str(unit), REKEY_CREDSTORE_DIR=str(credstore), PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run(["bash", str(REKEY), "--dry-run"], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ExecStart=/opt/marker/duplicati-wrapper.bash --marker --disable-db-encryption", r.stderr)
        self.assertNotIn("DRY RUN:", r.stderr)
        self.assertIn(f"cp -p {credstore}/duplicati-settings-key {credstore}/duplicati-settings-key.old", r.stderr)
        self.assertNotIn("/etc/credstore", r.stderr)

    def test_credstore_override_is_refused_on_a_real_run(self):
        """The unit's LoadCredential= reads /etc/credstore regardless, so a real run must not honour the hook."""
        env = RedactedEnv(os.environ, REKEY_CREDSTORE_DIR="/nonexistent/credstore", PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run(["bash", str(REKEY)], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("honoured under --dry-run only", r.stderr)


if __name__ == "__main__":
    unittest.main()
