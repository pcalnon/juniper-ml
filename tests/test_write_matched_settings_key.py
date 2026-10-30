#!/usr/bin/env python3
"""Procedure A's key write puts the probe's matched form at the credential path -- and nothing else, ever.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-10-29_write_matched_settings_key.py`` is the one command that places the 2026-09-18 settings
key on Procedure A (the 2026-10-03 assessment's section 6.4 step 9). It re-derives the step-7 probe's match
from the database copy and writes the matched variant's own text. Its two dangerous mistakes both brought back
I-38's mismatch loop: the wrong form written (a quoted ``raw`` match written without its quotes, a ``noquote``
match written with them), and a form the credential file cannot deliver (the probe's ``newline`` variant, or
edge whitespace, which the wrapper's ``$(<file)`` and its shape check alter or refuse).

Pins:

* the written bytes are the matched variant's text, without a trailing newline, mode 0600, and the real
  wrapper (``--print-command``) accepts them through ``$CREDENTIALS_DIRECTORY`` at the expected length;
* a quoted value keeps its quotes only on a ``raw`` match; a ``newline``-only or edge-whitespace match is
  refused; no match is refused, saying to stop after a probe match;
* never over an existing file or a symlink, even when one appears between the check and the create (O_EXCL);
  never into a directory owned by another user or writable by its group; nothing is written on any refusal or
  under ``--dry-run``; a failed or interrupted write or read-back removes the file it created; both read-backs
  are load-bearing;
* the .env is a regular file (a FIFO is refused, never waited on) and the parser is the probe's: CRLF lines,
  leading whitespace, ``export`` with a tab, a Unicode line separator inside the value, the LAST active line
  wins, ``_OLD`` and commented lines never match -- and the matched labels equal the probe's own verdict, run
  on the same inputs;
* ``strip_quotes``, ``variants`` and ``sha`` are the probe's, statement for statement (AST equality);
* a database the probe would misread (no blob, a content-hash mismatch, two key hashes, the job index's
  tables), or one with a blob under another key in a column the probe does not read, is refused;
* neither the value nor its hash ever reaches stdout or stderr, a decode error's quoted text included.

Hermetic: temporary files only; the "server database" is a small SQLite file built here, and the wrapper
runs with ``DUPLICATI_SERVER=/bin/true``. No Duplicati binary, no ``/etc/credstore``, no real key.
"""

from __future__ import annotations

import ast
import errno
import hashlib
import importlib.util
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import unittest.mock
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "util" / "ad-hoc" / "2026-10-29_write_matched_settings_key.py"
PROBE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-21_duplicati_settings_key_hash_probe.py"
GATE = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_rekey_gate.py"
WRAPPER = REPO_ROOT / "scripts" / "duplicati-wrapper.bash"
CONTRACT = REPO_ROOT / "util" / "systemd" / "duplicati-env.contract"

# Stand-in keys, 64 characters with shell-hostile characters; named *_MARKER so bandit B105 does not read
# them as credentials.
KEY_MARKER = "A" * 20 + "b$c&d@e#f^g%h" + "Z" * 31
OTHER_MARKER = "Q" * 64
COMMENTED_MARKER = "commented-out-value-marker"
OLD_NAME_MARKER = "old-name-value-marker"
LEAK_MARKER = "leak-probe-marker-text"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def _blob(content: str, under: str) -> str:
    """The enc-v1 layout the probe parses: content hash, key hash, content -- the content need not be real ciphertext."""
    return "enc-v1:" + _sha(content) + _sha(under) + content


def _run(cmd, env=None, stdin=None):
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, input=stdin, capture_output=True, text=True, check=False, timeout=120)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="matched-key-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.creds = self.tmp / "credstore"
        self.creds.mkdir(mode=0o700)
        self.out = self.creds / "duplicati-settings-key"

    def env_file(self, text: str, name: str = "service.env") -> Path:
        p = self.tmp / name
        p.write_bytes(text.encode("utf-8"))
        return p

    def server_db(
        self,
        key: str | None,
        *,
        name: str = "Duplicati-server.sqlite",
        second_key: str | None = None,
        tamper: bool = False,
        source_key: str | None = None,
        blob_typed_key: str | None = None,
        connection_key: str | None = None,
        target_url_key: str | None = None,
        connection_without_base_url: bool = False,
    ) -> Path:
        """A server-database stand-in: the probe's two columns with enc-v1 blobs under `key`; a Source.Path blob, and
        optionally a BLOB-typed Option value, a ConnectionString.BaseUrl or a BackupTargetUrl.TargetURL blob (columns
        only the gate reads) under another key -- or a ConnectionString table missing its BaseUrl column."""
        p = self.tmp / name
        con = sqlite3.connect(p)
        try:
            con.execute('CREATE TABLE "Backup" ("ID" INTEGER PRIMARY KEY, "Name" TEXT, "TargetURL" TEXT)')
            con.execute('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT)')
            con.execute('CREATE TABLE "Source" ("BackupID" INTEGER, "Path" TEXT)')
            if connection_without_base_url:
                con.execute('CREATE TABLE "ConnectionString" ("ID" INTEGER PRIMARY KEY, "Name" TEXT)')
                con.execute('INSERT INTO "ConnectionString" VALUES (1, ?)', (_blob("connection-stand-in", OTHER_MARKER),))
            else:
                con.execute('CREATE TABLE "ConnectionString" ("ID" INTEGER PRIMARY KEY, "Name" TEXT, "BaseUrl" TEXT)')
            con.execute('CREATE TABLE "BackupTargetUrl" ("BackupID" INTEGER, "TargetURL" TEXT)')
            if key is not None and not connection_without_base_url:
                con.execute('INSERT INTO "ConnectionString" VALUES (1, ?, ?)', ("saved", _blob("connection-stand-in", connection_key or key)))
            if key is not None:
                con.execute('INSERT INTO "BackupTargetUrl" VALUES (2, ?)', (_blob("target-history-stand-in", target_url_key or key),))
            if key is not None:
                target = _blob("target-url-stand-in", key)
                if tamper:
                    target = target[:-1] + ("A" if target[-1] != "A" else "B")
                con.execute('INSERT INTO "Backup" VALUES (2, ?, ?)', ("Yamaguchi", target))
                con.execute('INSERT INTO "Option" VALUES (2, ?, ?, ?)', ("", "passphrase", _blob("job-option-stand-in", key)))
                con.execute('INSERT INTO "Option" VALUES (-2, ?, ?, ?)', ("", "pbkdf-config", _blob("pbkdf-config-stand-in", second_key or key)))
                con.execute('INSERT INTO "Option" VALUES (-2, ?, ?, ?)', ("", "encrypted-fields", "True"))
                con.execute('INSERT INTO "Source" VALUES (2, ?)', (_blob("source-path-stand-in", source_key or key),))
                if blob_typed_key is not None:
                    con.execute('INSERT INTO "Option" VALUES (2, ?, ?, ?)', ("", "some-secret-option", _blob("blob-typed-stand-in", blob_typed_key).encode("utf-8")))
            con.commit()
        finally:
            con.close()
        return p

    def tool(self, env: Path, db: Path, *extra: str, out: Path | None = None):
        r = _run([sys.executable, str(TOOL), "--env", str(env), "--db", str(db), "--out", str(out or self.out), *extra])
        self.assert_no_leak(r.stdout + r.stderr)
        return r

    def assert_no_leak(self, text: str):
        for secret in (KEY_MARKER, _sha(KEY_MARKER), _sha(KEY_MARKER).lower(), _sha(f'"{KEY_MARKER}"'), LEAK_MARKER):
            self.assertNotIn(secret, text, "a value, a hash or a decode error's quoted text reached the output")

    def tool_main(self, env: Path, db: Path, *extra: str):
        """The tool in-process (for fault injection); its output is swallowed."""
        tool = _load(TOOL, "write_matched_settings_key")
        with unittest.mock.patch("sys.stdout"), unittest.mock.patch("sys.stderr"):
            return tool, tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out), *extra])

    def probe_labels(self, env_text: str, db: Path) -> set[str]:
        """The probe's own verdict on the same inputs: the ENV_ACTIVE_KEY labels it reports as matching."""
        wrapper = self.tmp / "wrapper-without-marker.bash"
        wrapper.write_text("# no committed literal here\n", encoding="utf-8")
        pc_env = self.tmp / "pcalnon-credential-env"
        pc_env.write_text("", encoding="utf-8")
        r = _run([sys.executable, str(PROBE), str(wrapper), str(pc_env), f"copy={db}"], stdin=env_text)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [line for line in r.stdout.splitlines() if "key-hash match:" in line]
        self.assertEqual(len(lines), 1, r.stdout)
        if "NONE of the candidates" in lines[0]:
            return set()
        return {label for label in ast.literal_eval(lines[0].split("key-hash match:", 1)[1].strip()) if label.startswith("ENV_ACTIVE_KEY/")}

    @staticmethod
    def tool_labels(r) -> set[str]:
        for line in r.stdout.splitlines():
            if line.startswith("key-hash match:"):
                return set(ast.literal_eval(line.split(":", 1)[1].strip()))
        return set()


class TestWritesTheMatchedForm(_Scratch):
    def test_unquoted_value_is_written_verbatim_without_a_newline(self):
        env = self.env_file(f"# service env\nSETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n")
        r = self.tool(env, self.server_db(KEY_MARKER))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.out.read_bytes(), KEY_MARKER.encode("utf-8"))
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o600)
        self.assertIn("both match the database's key hash", r.stdout)
        self.assertIn("under-another-key=0", r.stdout)

    def test_a_noquote_match_is_written_without_its_quotes(self):
        env = self.env_file(f'SETTINGS_ENCRYPTION_KEY="{KEY_MARKER}"\n')
        r = self.tool(env, self.server_db(KEY_MARKER))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ENV_ACTIVE_KEY/noquote", self.tool_labels(r))
        self.assertNotIn("ENV_ACTIVE_KEY/raw", self.tool_labels(r))
        self.assertEqual(self.out.read_bytes(), KEY_MARKER.encode("utf-8"))

    def test_a_quoted_raw_match_keeps_its_quotes(self):
        env = self.env_file(f'SETTINGS_ENCRYPTION_KEY="{KEY_MARKER}"\n')
        r = self.tool(env, self.server_db(f'"{KEY_MARKER}"'))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.tool_labels(r), {"ENV_ACTIVE_KEY/raw"})
        self.assertEqual(self.out.read_bytes(), f'"{KEY_MARKER}"'.encode("utf-8"))

    def test_no_pyc_is_written_beside_the_gate(self):
        """Run as root from pcalnon's checkout, an imported gate would leave a root-owned __pycache__ there. A private
        copy of the tool and the gate, with every bytecode-suppressing variable removed, shows whether the tool
        suppresses it itself."""
        adhoc = self.tmp / "ad-hoc"
        adhoc.mkdir()
        shutil.copy(TOOL, adhoc / TOOL.name)
        shutil.copy(GATE, adhoc / GATE.name)
        env = RedactedEnv(os.environ)
        for name in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"):
            env.pop(name, None)
        e, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        r = _run([sys.executable, str(adhoc / TOOL.name), "--env", str(e), "--db", str(db), "--out", str(self.out)], env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((adhoc / "__pycache__").exists(), "the tool must load the gate with bytecode writing off")

    def test_the_real_wrapper_accepts_the_written_file_at_the_expected_length(self):
        for label, env_text, db_key, want_len in (
            ("unquoted", f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", KEY_MARKER, 64),
            ("quoted raw", f"SETTINGS_ENCRYPTION_KEY='{KEY_MARKER}'\n", f"'{KEY_MARKER}'", 66),
        ):
            with self.subTest(label=label):
                if self.out.exists():
                    self.out.unlink()
                r = self.tool(self.env_file(env_text), self.server_db(db_key, name=f"{label}.sqlite"))
                self.assertEqual(r.returncode, 0, r.stderr)
                creds_dir = self.tmp / f"creds-{label.replace(' ', '-')}"
                creds_dir.mkdir()
                shutil.copyfile(self.out, creds_dir / "settings-key")
                data = self.tmp / f"data-{label.replace(' ', '-')}"
                data.mkdir(mode=0o700)
                wenv = RedactedEnv(
                    os.environ,
                    CREDENTIALS_DIRECTORY=str(creds_dir),
                    DUPLICATI_ENV_FILE=str(CONTRACT),
                    DUPLICATI_DATA_FOLDER=str(data),
                    DUPLICATI_REQUIRE_MOUNT="",
                    DUPLICATI_SERVER="/bin/true",
                    SETTINGS_ENCRYPTION_KEY="",
                )
                w = _run(["bash", str(WRAPPER), "--print-command"], env=wenv)
                self.assertEqual(w.returncode, 0, w.stderr)
                self.assertIn(f"systemd credential settings-key ({want_len} chars)", w.stderr)
                self.assert_no_leak(w.stdout + w.stderr)


class TestRefusesWhatCannotBeDelivered(_Scratch):
    def test_a_match_only_on_the_newline_variant_is_refused_by_the_dry_run_too(self):
        """Step 7's route decision is the dry run's exit status, so the dry run must refuse whatever the real run would."""
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER + "\n")
        for extra in ((), ("--dry-run",)):
            with self.subTest(extra=extra):
                r = self.tool(env, db, *extra)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertEqual(self.tool_labels(r), {"ENV_ACTIVE_KEY/newline"})
                self.assertIn("cannot be delivered", r.stderr)
                self.assertFalse(os.path.lexists(self.out))

    def test_edge_whitespace_is_stripped_on_a_noquote_match_and_refused_on_a_raw_one(self):
        env = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}   \n")
        r = self.tool(env, self.server_db(KEY_MARKER, name="stripped.sqlite"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.out.read_bytes(), KEY_MARKER.encode("utf-8"))
        self.out.unlink()
        r = self.tool(env, self.server_db(KEY_MARKER + "   ", name="raw-spaces.sqlite"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.tool_labels(r), {"ENV_ACTIVE_KEY/raw"})
        self.assertIn("whitespace", r.stderr)
        self.assertFalse(os.path.lexists(self.out))

    def test_undeliverable_names_every_form_the_file_cannot_carry(self):
        undeliverable = _load(TOOL, "write_matched_settings_key").undeliverable
        cases = {
            "NUL": ("abc\0def", "NUL"),
            "CR": ("abc\rdef", "carriage return"),
            "inner newline": ("abc\ndef", "newline"),
            "trailing newline": ("abcdef\n", "newline"),
            "leading space": (" abcdef", "whitespace"),
            "trailing tab": ("abcdef\t", "whitespace"),
            "trailing no-break space": ("abcdef ", "whitespace"),
        }
        for label, (value, needle) in cases.items():
            with self.subTest(label=label):
                why = undeliverable(value)
                self.assertIsNotNone(why)
                self.assertIn(needle, why)
        self.assertIsNone(undeliverable(KEY_MARKER))
        self.assertIsNone(undeliverable(f'"{KEY_MARKER}"'))

    def test_no_match_is_refused_and_says_to_stop_after_a_probe_match(self):
        env = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n")
        r = self.tool(env, self.server_db(OTHER_MARKER))
        self.assertEqual(r.returncode, 1)
        self.assertIn("STOP", r.stderr)
        self.assertIn("keep the .env", r.stderr)
        self.assertIn("this is Procedure A0", r.stderr)
        self.assertFalse(os.path.lexists(self.out))


class TestNeverOverwritesOrLeavesAKeyBehind(_Scratch):
    def test_an_existing_file_is_refused_and_left_untouched_even_on_a_dry_run(self):
        self.out.write_bytes(b"an existing key\n")
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        for extra in ((), ("--dry-run",)):
            with self.subTest(extra=extra):
                r = self.tool(env, db, *extra)
                self.assertEqual(r.returncode, 1)
                self.assertIn("already exists", r.stderr)
                self.assertEqual(self.out.read_bytes(), b"an existing key\n")

    def test_a_file_that_appears_after_the_check_is_never_overwritten(self):
        """O_EXCL: the existence check and the create are two system calls; a key placed between them survives."""
        tool = _load(TOOL, "write_matched_settings_key")
        real_open_out_dir = tool.open_out_dir

        def racing_open_out_dir(out):
            dfd = real_open_out_dir(out)
            out.write_bytes(b"a key that appeared in the gap, ninety-two bytes long" + b"x" * 39)
            return dfd

        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        with unittest.mock.patch.object(tool, "open_out_dir", side_effect=racing_open_out_dir):
            with unittest.mock.patch("sys.stdout"), unittest.mock.patch("sys.stderr"):
                rc = tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out)])
        self.assertNotEqual(rc, 0)
        self.assertEqual(self.out.read_bytes(), b"a key that appeared in the gap, ninety-two bytes long" + b"x" * 39)

    def test_a_dangling_symlink_at_the_path_is_refused(self):
        self.out.symlink_to(self.tmp / "elsewhere")
        r = self.tool(self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER))
        self.assertEqual(r.returncode, 1)
        self.assertFalse((self.tmp / "elsewhere").exists())

    def test_a_symlinked_directory_is_refused(self):
        real = self.tmp / "real-credstore"
        real.mkdir(mode=0o700)
        link = self.tmp / "linked-credstore"
        link.symlink_to(real)
        r = self.tool(self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER), out=link / "duplicati-settings-key")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(list(real.iterdir()), [])

    def test_a_group_writable_or_foreign_directory_is_refused(self):
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        self.creds.chmod(0o770)
        r = self.tool(env, db)
        self.assertEqual(r.returncode, 1)
        self.assertIn("writable by its group or by others", r.stderr)
        self.creds.chmod(0o700)
        with unittest.mock.patch("os.geteuid", return_value=os.geteuid() + 1):
            _, rc = self.tool_main(env, db)
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.lexists(self.out))

    def test_a_dry_run_writes_nothing(self):
        r = self.tool(self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER), "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("dry run", r.stdout)
        self.assertFalse(os.path.lexists(self.out))

    def test_a_failed_or_interrupted_read_back_removes_the_file_it_created(self):
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        tool = _load(TOOL, "write_matched_settings_key")
        for label, effect in (("refused", tool.Refused("simulated read-back mismatch")), ("interrupted", KeyboardInterrupt())):
            with self.subTest(label=label):
                with unittest.mock.patch.object(tool, "read_back", side_effect=effect):
                    with unittest.mock.patch("sys.stdout"), unittest.mock.patch("sys.stderr"):
                        if isinstance(effect, KeyboardInterrupt):
                            with self.assertRaises(KeyboardInterrupt):
                                tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out)])
                        else:
                            self.assertEqual(tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out)]), 1)
                self.assertFalse(os.path.lexists(self.out))

    def test_a_termination_during_the_write_or_the_read_back_lands_after_the_decision(self):
        """1.2.0 (R2A-2), round 3 (R3-2, R3-6) and round 4 (R4-3, R4-4): SIGTERM, SIGHUP, SIGINT and SIGQUIT wait from
        before the create until the key is verified or removed. A driver sends each, in turn, to the tool's own process
        inside the write (from its first fsync, after the create) and in the middle of its read-back. With the deferral
        the decision is made, the verified key stays and its line is printed before the signal ends the process; without
        it -- for any one of the four, or with the block moved after the create -- the process dies before the decision
        and prints no such line. The core limit is (0, 0) before the key is read, so no core can carry it."""
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        driver = self.tmp / "driver.py"
        driver_lines = (
            "import importlib.util, os, resource, signal, sys",
            f"spec = importlib.util.spec_from_file_location('tool', {str(TOOL)!r})",
            "tool = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(tool)",
            "which, where = sys.argv[1], sys.argv[2]",
            "# Inherited dispositions must not decide the result: nohup hands SIGHUP over ignored, and a background job",
            "# starts with SIGINT and SIGQUIT ignored (lane R4, R4-4). Restore what a terminal session starts with.",
            "SIGNALS = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]",
            "for number in SIGNALS:",
            "    signal.signal(number, signal.default_int_handler if number == signal.SIGINT else signal.SIG_DFL)",
            "signal.pthread_sigmask(signal.SIG_UNBLOCK, SIGNALS)",
            "core_limits_set = []",
            "real_setrlimit = resource.setrlimit",
            "def recording_setrlimit(limit, values):",
            "    if limit == resource.RLIMIT_CORE:",
            "        core_limits_set.append(tuple(values))",
            "    return real_setrlimit(limit, values)",
            "resource.setrlimit = recording_setrlimit",
            "real_active_key = tool.active_key",
            "def recording_active_key(*args, **kwargs):",
            "    print('before the key is read:', core_limits_set, resource.getrlimit(resource.RLIMIT_CORE), flush=True)",
            "    return real_active_key(*args, **kwargs)",
            "tool.active_key = recording_active_key",
            "def interrupt():",
            "    if which != 'NONE':",
            "        os.kill(os.getpid(), getattr(signal, which))",
            "real_fsync, real_read_back = os.fsync, tool.read_back",
            "def interrupted_mid_write(fd):",
            "    os.fsync = real_fsync",
            "    interrupt()",
            "    return real_fsync(fd)",
            "def interrupted_mid_read_back(*args, **kwargs):",
            "    interrupt()",
            "    return real_read_back(*args, **kwargs)",
            "if where == 'write':",
            "    os.fsync = interrupted_mid_write",
            "else:",
            "    tool.read_back = interrupted_mid_read_back",
            "rc = tool.main(['tool'] + sys.argv[3:])",
            "print('core-limit', resource.getrlimit(resource.RLIMIT_CORE))",
            "sys.exit(rc)",
        )
        driver.write_text("\n".join(driver_lines) + "\n")
        cwd = self.tmp / "cwd"
        cwd.mkdir()
        # Every deferred signal in both places, and a run with none (which shows the core limit the tool left). The pins
        # on the core limit are the two (0, 0) lines; the empty working directory is a backstop, since at the usual
        # inherited soft limit of 0 no core would land there anyway (R4-3).
        cases = [(where, which) for where in ("write", "read-back") for which in ("SIGTERM", "SIGINT", "SIGHUP", "SIGQUIT")]
        for where, which in cases + [("read-back", "NONE")]:
            with self.subTest(where=where, signal=which):
                if self.out.exists():
                    self.out.unlink()
                cmd = [sys.executable, str(driver), which, where, "--env", str(env), "--db", str(db), "--out", str(self.out)]
                r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, timeout=120)
                self.assert_no_leak(r.stdout + r.stderr)
                expected = 0 if which == "NONE" else -getattr(signal, which)
                self.assertEqual(r.returncode, expected, r.stderr)
                self.assertIn("both match the database's key hash", r.stdout)
                self.assertEqual(self.out.read_bytes(), KEY_MARKER.encode("utf-8"))
                self.assertIn("before the key is read: [(0, 0)] (0, 0)", r.stdout)
                if which == "NONE":
                    self.assertIn("core-limit (0, 0)", r.stdout)
                self.assertEqual(list(cwd.iterdir()), [], "no core file")

    def test_both_read_backs_are_load_bearing(self):
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        gate = _load(GATE, "rekey_gate")
        tool = _load(TOOL, "write_matched_settings_key")
        with unittest.mock.patch.object(gate, "read_key", return_value=OTHER_MARKER), unittest.mock.patch.object(tool, "load_gate", return_value=gate):
            with unittest.mock.patch("sys.stdout"), unittest.mock.patch("sys.stderr"):
                self.assertEqual(tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out)]), 1)
        self.assertFalse(os.path.lexists(self.out), "the gate-style read-back")
        tool = _load(TOOL, "write_matched_settings_key")
        with unittest.mock.patch.object(tool, "BASH_READ", 'printf "%s  -\\n" 0000'):
            with unittest.mock.patch("sys.stdout"), unittest.mock.patch("sys.stderr"):
                self.assertEqual(tool.main(["tool", "--env", str(env), "--db", str(db), "--out", str(self.out)]), 1)
        self.assertFalse(os.path.lexists(self.out), "the bash $(<file) read-back")

    def test_a_failure_inside_the_write_removes_the_file(self):
        env, db = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER)
        with unittest.mock.patch("os.fsync", side_effect=OSError(errno.EIO, "simulated I/O error")):
            _, rc = self.tool_main(env, db)
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.lexists(self.out))


class TestTheProbesParserAndDatabaseChecks(_Scratch):
    def test_crlf_lines_the_last_active_line_old_and_commented_lines(self):
        lines = (
            f"# SETTINGS_ENCRYPTION_KEY={COMMENTED_MARKER}",
            f"SETTINGS_ENCRYPTION_KEY={OTHER_MARKER}",
            f"SETTINGS_ENCRYPTION_KEY_OLD={OLD_NAME_MARKER}",
            f"export SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\r",
        )
        env = self.env_file("\r\n".join(lines) + "\r\n")
        r = self.tool(env, self.server_db(KEY_MARKER))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.out.read_bytes(), KEY_MARKER.encode("utf-8"))

    def test_an_env_without_an_active_line_or_not_a_regular_utf8_file_is_refused(self):
        """Each refusal names its own reason. The non-UTF-8 case is keyed so that only the strict decode refuses it:
        the database is under the text a lenient decode would produce, so a lenient tool would match and write."""
        fifo = self.tmp / "fifo.env"
        os.mkfifo(fifo)
        bad = self.tmp / "latin1.env"
        raw_value = b"caf\xe9-not-utf8-value-and-long"
        bad.write_bytes(b"SETTINGS_ENCRYPTION_KEY=" + raw_value + b"\n")
        cases = {
            "none": (self.env_file("PASSPHRASE=x\n", name="none.env"), KEY_MARKER, "no uncommented SETTINGS_ENCRYPTION_KEY= line"),
            "only _OLD": (self.env_file("SETTINGS_ENCRYPTION_KEY_OLD=x\n", name="old.env"), KEY_MARKER, "no uncommented SETTINGS_ENCRYPTION_KEY= line"),
            "empty": (self.env_file("SETTINGS_ENCRYPTION_KEY=\n", name="empty.env"), KEY_MARKER, "is empty"),
            "a FIFO": (fifo, KEY_MARKER, "not a regular file"),
            "not UTF-8": (bad, raw_value.decode("utf-8", errors="replace"), "not valid UTF-8"),
        }
        for label, (env, db_key, reason) in cases.items():
            with self.subTest(label=label):
                r = self.tool(env, self.server_db(db_key, name=f"{label.replace(' ', '_')}.sqlite"))
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn(reason, r.stderr)
                self.assertFalse(os.path.lexists(self.out))

    def test_databases_the_probe_would_misread_are_refused(self):
        env = self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n")
        index = self.tmp / "BMXWPAOGLP.sqlite"
        con = sqlite3.connect(index)
        con.execute('CREATE TABLE "Block" ("ID" INTEGER PRIMARY KEY, "Hash" TEXT)')
        con.close()
        cases = {
            "no blob": (self.server_db(None, name="empty.sqlite"), "no enc-v1 blob"),
            "content hash mismatch": (self.server_db(KEY_MARKER, name="tampered.sqlite", tamper=True), "content hash verifies"),
            "two key hashes": (self.server_db(KEY_MARKER, name="two-keys.sqlite", second_key=OTHER_MARKER), "more than one key hash"),
            "the job index": (index, "query error"),
            "a Source.Path blob under another key": (self.server_db(KEY_MARKER, name="source.sqlite", source_key=OTHER_MARKER), "another key hash"),
            "a BLOB-typed Option value under another key": (self.server_db(KEY_MARKER, name="blob-typed.sqlite", blob_typed_key=OTHER_MARKER), "another key hash"),
            "a ConnectionString blob under another key": (self.server_db(KEY_MARKER, name="connection.sqlite", connection_key=OTHER_MARKER), "another key hash"),
            "a BackupTargetUrl blob under another key": (self.server_db(KEY_MARKER, name="target-history.sqlite", target_url_key=OTHER_MARKER), "another key hash"),
            "a ConnectionString table without its BaseUrl column": (self.server_db(KEY_MARKER, name="no-base-url.sqlite", connection_without_base_url=True), "query error"),
        }
        for label, (db, message) in cases.items():
            for extra in ((), ("--dry-run",)):
                with self.subTest(label=label, extra=extra):
                    r = self.tool(env, db, *extra)
                    self.assertEqual(r.returncode, 1, r.stdout)
                    self.assertIn(message, r.stderr)
                    self.assertFalse(os.path.lexists(self.out))

    def test_every_one_of_the_gates_five_columns_is_read_and_a_one_key_database_passes(self):
        r = self.tool(self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), self.server_db(KEY_MARKER), "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        for column in ("Option.Value=", "Backup.TargetURL=", "Source.Path=", "ConnectionString.BaseUrl=", "BackupTargetUrl.TargetURL="):
            self.assertIn(column, r.stdout)
        self.assertNotIn("absent", r.stdout)
        self.assertIn("under-another-key=0", r.stdout)

    def test_a_decode_error_never_quotes_the_column(self):
        """Python's sqlite3 says 'Could not decode to UTF-8 column ... with text ...': only the class may print."""
        db = self.server_db(KEY_MARKER, name="undecodable.sqlite")
        con = sqlite3.connect(db)
        con.execute('INSERT INTO "Backup" VALUES (3, ?, CAST(? AS TEXT))', ("stray", LEAK_MARKER.encode("utf-8") + b"\xff\xfe"))
        con.commit()
        con.close()
        r = self.tool(self.env_file(f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n"), db)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("text not shown", r.stderr)
        self.assertFalse(os.path.lexists(self.out))

    def test_the_matched_labels_equal_the_probes_own_verdict(self):
        separator_key = "L" * 30 + " " + "S" * 33
        cases = {
            "unquoted": (f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", KEY_MARKER),
            "quoted, noquote match": (f'SETTINGS_ENCRYPTION_KEY="{KEY_MARKER}"\n', KEY_MARKER),
            "quoted, raw match": (f'SETTINGS_ENCRYPTION_KEY="{KEY_MARKER}"\n', f'"{KEY_MARKER}"'),
            "newline": (f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", KEY_MARKER + "\n"),
            "percent doubled": (f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", KEY_MARKER.replace("%", "%%")),
            "crlf, last line wins": (f"SETTINGS_ENCRYPTION_KEY={OTHER_MARKER}\r\nSETTINGS_ENCRYPTION_KEY={KEY_MARKER}\r\n", KEY_MARKER),
            "leading whitespace, export and a tab": (f"  \texport\tSETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", KEY_MARKER),
            "a line separator inside the value": (f"SETTINGS_ENCRYPTION_KEY={separator_key}\n", separator_key),
            "no match": (f"SETTINGS_ENCRYPTION_KEY={KEY_MARKER}\n", OTHER_MARKER),
        }
        for n, (label, (env_text, db_key)) in enumerate(cases.items()):
            with self.subTest(label=label):
                db = self.server_db(db_key, name=f"parity-{n}.sqlite")
                r = self.tool(self.env_file(env_text, name="parity.env"), db, "--dry-run")
                self.assertEqual(self.tool_labels(r), self.probe_labels(env_text, db))

    def test_strip_quotes_variants_and_sha_are_the_probes_statement_for_statement(self):
        def functions(path: Path) -> dict[str, str]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            return {n.name: ast.dump(n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"sha", "strip_quotes", "variants"}}

        probe, tool = functions(PROBE), functions(TOOL)
        self.assertEqual(set(probe), {"sha", "strip_quotes", "variants"})
        self.assertEqual(probe, tool)


if __name__ == "__main__":
    unittest.main()
