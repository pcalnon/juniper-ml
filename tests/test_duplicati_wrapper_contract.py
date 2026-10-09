#!/usr/bin/env python3
"""
Hermetic gate for the Duplicati service lane's contract files (the 2026-10-03 assessment's B5).

What the 2026-09 outage and the Phase B validation round showed cannot be left to a read-through:

* the wrapper's env-file grammar -- a name the allow-list refuses (``SETTINGS_ENCRYPTION_KEY_OLD``
  was on the live host's file for eleven days) is a FATAL exit 78 before any option is assembled;
  a security option (``--disable-db-encryption``) or a ``DUPLICATI__*`` export in the env file is
  refused too (Lane A: the server composes ``DUPLICATI__<OPTION>`` for every option, so that family
  was a silent second channel for the decrypt flag); a commented-out assignment is a secret on disk
  (AC-8's own count); the shipped contract ``util/systemd/duplicati-env.contract`` must itself pass
  the wrapper; ``--print-command`` redacts by option NAME (``password-init=`` slipped through);
* the installer's gates -- ``blessed_for`` returned 1 with no blessed file and ``set -e`` ended the
  first install silently (I-36); the never-blessed, no-drift, DRIFT, BEHAVIOUR CHANGE and
  kept-existing paths each get a ``--dry-run`` rehearsal here against a scratch tree
  (``DUPLICATI_INSTALL_PREFIX``), as a non-root user; and the "no secret in the contract" gate is
  mutation-checked on a scratch repository tree (Lane C: the first gate matched three names);
* the two recovery helpers -- the password-init hand start must refuse a group-readable secret
  file, a non-0700 data folder and a port in use, its parameters file must be shredded on every
  exit (proved with a stub server, as the current user), and the re-key's ``--dry-run`` must print
  the WHOLE step sequence in order -- the first test matched first occurrences and was blind to
  three dangerous re-orderings (Lane C) -- with ``rm`` of the drop-in and never ``systemctl revert``
  (which deletes the installed unit when a vendor unit exists: the round's BLOCKER);
* the re-key's exit gate ``util/ad-hoc/2026-10-03_rekey_gate.py`` on a scratch database: PASS under
  the right key, FAIL under another key, FAIL with one blob under another key in ANY of the five
  encrypted columns (``ConnectionString.BaseUrl`` is the one the product's own rewrite never
  touches), FAIL with the flag False or absent, FAIL with zero blobs.

None of these runs a Duplicati binary (``DUPLICATI_SERVER`` is ``/bin/true`` or a stub the test
writes), touches ``/etc``, ``/usr/local`` or a unit, or reads a secret file: every input is written
into a temporary directory the test owns.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "duplicati-wrapper.bash"
CONTRACT = REPO_ROOT / "util" / "systemd" / "duplicati-env.contract"
DEFAULTS = REPO_ROOT / "util" / "systemd" / "duplicati.default"
INSTALLER = REPO_ROOT / "util" / "install_duplicati_service.bash"
PASSWORD_INIT = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_password_init_hand_start.bash"
REKEY = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_rekey_settings_key.bash"
GATE = REPO_ROOT / "util" / "ad-hoc" / "2026-10-03_rekey_gate.py"

# Everything the installer reads from the repository, relative to its root (REPO_DIR = installer/..).
INSTALLER_SOURCES = (
    "util/install_duplicati_service.bash",
    "scripts/duplicati-wrapper.bash",
    "util/systemd/duplicati.service",
    "util/systemd/duplicati.default",
    "util/yamaguchi-pre-backup-guard.bash",
    "util/systemd/duplicati-env.contract",
    "util/ad-hoc/yamaguchi_server_db_snapshot.py",
    "util/systemd/yamaguchi-server-db-snapshot.service",
    "util/systemd/yamaguchi-server-db-snapshot.timer",
)
# The seven blessed destinations, relative to the install prefix, in the installer's PAIRS order.
BLESSED_DESTS = (
    "usr/local/lib/duplicati/duplicati-wrapper.bash",
    "etc/systemd/system/duplicati.service",
    "etc/default/duplicati",
    "usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash",
    "usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py",
    "etc/systemd/system/yamaguchi-server-db-snapshot.service",
    "etc/systemd/system/yamaguchi-server-db-snapshot.timer",
)
BLESSED_SOURCES = (
    "scripts/duplicati-wrapper.bash",
    "util/systemd/duplicati.service",
    "util/systemd/duplicati.default",
    "util/yamaguchi-pre-backup-guard.bash",
    "util/ad-hoc/yamaguchi_server_db_snapshot.py",
    "util/systemd/yamaguchi-server-db-snapshot.service",
    "util/systemd/yamaguchi-server-db-snapshot.timer",
)


def _run(cmd, env=None, cwd=None):
    return subprocess.run(cmd, cwd=cwd or REPO_ROOT, env=env, capture_output=True, text=True, check=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="wrapper-contract-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.data = self.tmp / "data"
        self.data.mkdir(mode=0o700)

    def wrapper_env(self, env_file: Path) -> RedactedEnv:
        return RedactedEnv(
            os.environ,
            DUPLICATI_ENV_FILE=str(env_file),
            DUPLICATI_DATA_FOLDER=str(self.data),
            DUPLICATI_REQUIRE_MOUNT="",
            DUPLICATI_SERVER="/bin/true",
            # The settings key must not leak in from the test runner's environment.
            SETTINGS_ENCRYPTION_KEY="",
        )

    def print_command(self, env_file: Path, *argv: str):
        return _run(["bash", str(WRAPPER), *argv, "--print-command"], env=self.wrapper_env(env_file))

    def env_file(self, text: str, name: str = "env") -> Path:
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p


class WrapperEnvContract(_Scratch):
    def test_shipped_contract_passes_the_wrapper(self):
        """util/systemd/duplicati-env.contract is what the installer deploys; the wrapper must accept it."""
        r = self.print_command(CONTRACT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would exec: /bin/true", r.stdout)
        self.assertIn("--webservice-port=8300", r.stdout)

    def test_shipped_contract_has_no_commented_assignment_and_no_key(self):
        """AC-8's own check: zero commented-out assignments; no SETTINGS_ENCRYPTION_KEY line at all."""
        lines = CONTRACT.read_text(encoding="utf-8").splitlines()
        # AC-8's shape: a comment whose first token is an assignment -- `# export NAME=value`,
        # `# NAME=value` or `# NAME = value` -- which is what the 2026-09-20 .env carried five of.
        # Any run of `#` (R3A N-5: `## KEY=value` slipped past a single `#?`).
        commented = [line for line in lines if re.match(r"^\s*#[#\s]*(export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*\S", line)]
        self.assertEqual(commented, [], "a commented-out KEY=VALUE line is a secret on disk")
        # A commented-out option line carrying a value (`# --webservice-password=...`) is one too.
        commented_opts = [line for line in lines if re.match(r"^\s*#[#\s]*--[A-Za-z0-9-]+=\S", line)]
        self.assertEqual(commented_opts, [], "a commented-out --option=value line is a value on disk")
        active = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(active, ["--webservice-port=8300"])
        self.assertFalse(any(line.lstrip().startswith(("SETTINGS_ENCRYPTION_KEY", "export SETTINGS_ENCRYPTION_KEY")) for line in lines))

    def test_old_key_name_is_fatal_before_any_option(self):
        """The live host's 2026-09-22 .env shape: exit 78 at the _OLD line, naming the key, never its value."""
        env_file = self.env_file("export SETTINGS_ENCRYPTION_KEY_OLD='dummy-old'\nexport SETTINGS_ENCRYPTION_KEY='dummy-new'\n")
        r = self.print_command(env_file)
        self.assertEqual(r.returncode, 78)
        self.assertIn("SETTINGS_ENCRYPTION_KEY_OLD is not an exportable name", r.stderr)
        self.assertNotIn("dummy-old", r.stderr + r.stdout)
        self.assertNotIn("would exec", r.stdout)

    def test_duplicati_env_family_is_not_exportable_from_the_env_file(self):
        """Lane A: DUPLICATI__DISABLE_DB_ENCRYPTION=true in the unblessed env file would decrypt the database silently."""
        r = self.print_command(self.env_file("export DUPLICATI__DISABLE_DB_ENCRYPTION=true\n"))
        self.assertEqual(r.returncode, 78)
        self.assertIn("DUPLICATI__DISABLE_DB_ENCRYPTION is not an exportable name", r.stderr)
        self.assertNotIn("would exec", r.stdout)

    # Every name ENV_OPTION_DENY must hold, written out here rather than parsed from the wrapper, so a
    # name dropped from the wrapper fails the set-equality test below instead of vanishing from both.
    DENIED = (
        "disable-db-encryption",
        "require-db-encryption-key",
        "settings-encryption-key",
        "allow-insecure-datafolder",
        "webservice-password",
        "webservice-password-init",
        "webservice-pre-auth-tokens",
        "webservice-reset-jwt-config",
        "webservice-disable-signin-tokens",
        "webservice-allowed-hostnames",
        "webservice-allowedhostnames",
        "webservice-interface",
        "server-datafolder",
        "parameters-file",
        "parameterfile",
        "webservice-enable-forever-token",
        "webservice-cors-origins",
    )
    ALLOWED = (
        "webservice-port",
        "webservice-token-duration",
        "webservice-timezone",
        "log-level",
        "log-retention",
        "ping-pong-keepalive",
        "disable-update-check",
        "webservice-suppress-welcome-page",
    )

    @staticmethod
    def _wrapper_list(var: str) -> set[str]:
        m = re.search(rf"^readonly {var}='\^--\(([^)]*)\)\(=\|\$\)'$", WRAPPER.read_text(encoding="utf-8"), re.M)
        assert m, f"{var} not found in the wrapper in its expected shape"
        return set(m.group(1).split("|"))

    @staticmethod
    def _server_options() -> list[list[str]]:
        """The PRODUCT's option table (canonical name, then aliases), vendored from Duplicati 2.4.0.0's source."""
        fixture = REPO_ROOT / "tests" / "fixtures" / "duplicati_2.4.0.0_server_options.txt"
        lines = fixture.read_text(encoding="utf-8").splitlines()
        assert any("v2.4.0.0_stable_2026-09-03" in line and "b3e9268c" in line for line in lines if line.startswith("#")), "fixture provenance missing"
        return [line.split() for line in lines if line.strip() and not line.startswith("#")]

    def test_deny_and_allow_lists_are_exactly_the_reviewed_names(self):
        """R3A D-1 / R3C D-3: parameters-file was missing; every entry is pinned by name, and the two lists are disjoint."""
        self.assertEqual(self._wrapper_list("ENV_OPTION_DENY"), set(self.DENIED))
        self.assertEqual(self._wrapper_list("ENV_OPTION_ALLOW"), set(self.ALLOWED))
        self.assertEqual(set(self.DENIED) & set(self.ALLOWED), set())

    def test_every_list_entry_is_a_real_server_option_and_every_alias_is_covered(self):
        """R4A D-2: 2.3.0 allowed `suppress-welcome-page`, which the server does not have -- a hand-copied list pinned by a
        hand-copied test. Both lists are checked against the product's own table, and an alias of a listed option must be
        listed the same way (the server honours either spelling)."""
        table = self._server_options()
        self.assertEqual(len(table), 50, "the fixture is the 47 SupportedCommands plus three secret-provider options")
        known = {name for row in table for name in row}
        for var in ("ENV_OPTION_DENY", "ENV_OPTION_ALLOW"):
            listed = self._wrapper_list(var)
            for name in sorted(listed):  # the WRAPPER's own entries, not this file's copy of them
                with self.subTest(list=var, name=name):
                    self.assertIn(name, known, f"{name} is not a Duplicati 2.4.0.0 server option or alias")
            for row in table:
                if listed & set(row):
                    with self.subTest(list=var, option=row[0]):
                        self.assertTrue(set(row) <= listed, f"{var} lists part of {row}; an alias is a second channel")

    def test_security_options_are_refused_from_the_env_file_in_any_case(self):
        """Every denied name, lower- and mixed-case, bare and with a value: exit 78 with the SECURITY message, never the value."""
        for name in self.DENIED:
            mixed = "-".join(part.capitalize() for part in name.split("-"))
            for line in (f"--{name}", f"--{name}=not-a-real-value", f"--{mixed}=not-a-real-value", f"  --{name.upper()}"):
                with self.subTest(line=line):
                    r = self.print_command(self.env_file(line + "\n"))
                    self.assertEqual(r.returncode, 78, r.stderr)
                    self.assertIn("may not be set from the env file (security option", r.stderr)
                    self.assertNotIn("not-a-real-value", r.stderr + r.stdout, "the refusal must not echo a value")
                    self.assertNotIn("would exec", r.stdout)

    def test_env_file_options_outside_the_allow_list_are_refused(self):
        """2.3.0: the deny list was the wrong shape (R3A D-1); anything not a reviewed tunable -- a typo included -- is refused."""
        for line in ("--log-file=/home/duplicati/.config/Duplicati/Duplicati-server.sqlite", "--register-remote-control=https://example.invalid/x", "--webservice-webroot=/", "--tempdir=/x", "--webservice-api-only=true", "--disable-default-secret-provider=true", "--webservice-prot=8301", "--help", "--log-level-extra=1", "--webservice-port2=8301"):
            with self.subTest(line=line):
                r = self.print_command(self.env_file(line + "\n"))
                self.assertEqual(r.returncode, 78, r.stderr)
                self.assertIn("is not an env-file tunable", r.stderr)
                self.assertNotIn("would exec", r.stdout)

    def test_every_allow_listed_tunable_passes_in_any_case(self):
        for name in self.ALLOWED:
            mixed = "-".join(part.capitalize() for part in name.split("-"))
            for line in (f"--{name}=1", f"--{mixed}=1"):
                with self.subTest(line=line):
                    r = self.print_command(self.env_file(line + "\n"))
                    self.assertEqual(r.returncode, 0, r.stderr)
                    # --print-command redacts by name, so token-duration's value prints as <redacted>.
                    self.assertIn(f" --{name}=", r.stdout)

    def test_settings_key_with_a_carriage_return_or_edge_whitespace_is_refused(self):
        """R3C N-2: the server uses the credential byte-for-byte; the hand start and the gate drop a CR -- one file, two keys."""
        creds = self.tmp / "creds"
        creds.mkdir()
        key_file = creds / "settings-key"
        cases = {
            "CRLF": (b"not-a-real-key-0123456789\r\n", 78),
            "CR inside": (b"not-a-real\rkey-0123456789", 78),
            "leading space": (b" not-a-real-key-0123456789", 78),
            "trailing tab": (b"not-a-real-key-0123456789\t", 78),
            "plain, trailing LF": (b"not-a-real-key-0123456789\n", 0),
        }
        for label, (content, code) in cases.items():
            with self.subTest(label=label):
                key_file.write_bytes(content)
                env = self.wrapper_env(CONTRACT)
                env["CREDENTIALS_DIRECTORY"] = str(creds)
                r = _run(["bash", str(WRAPPER), "--print-command"], env=env)
                self.assertEqual(r.returncode, code, r.stderr)
                self.assertNotIn("not-a-real", r.stdout + r.stderr)
        env = self.wrapper_env(CONTRACT)
        env["SETTINGS_ENCRYPTION_KEY"] = "not-a-real-key-0123456789\r"
        r = _run(["bash", str(WRAPPER), "--print-command"], env=env)
        self.assertEqual(r.returncode, 78, "the environment path is held to the same shape")
        self.assertIn("carriage return", r.stderr)

    def _wrapper_with_default_mount(self, mount: Path) -> Path:
        """A scratch copy of the wrapper whose DEFAULT mount is `mount` -- a host without /mnt/Backups, simulated."""
        text = WRAPPER.read_text(encoding="utf-8")
        pattern = r'"\$\{DUPLICATI_REQUIRE_MOUNT-[^}:]*\}"'  # whatever the default is, in the `-` (not `:-`) form
        self.assertEqual(len(re.findall(pattern, text)), 1, "the wrapper's mount default must use `-`, not `:-` (R4A D-1)")
        copy = self.tmp / "wrapper-nomount.bash"
        copy.write_text(re.sub(pattern, f'"${{DUPLICATI_REQUIRE_MOUNT-{mount}}}"', text), encoding="utf-8")
        return copy

    def test_unset_the_production_default_requires_mnt_backups(self):
        """R5A NIT-3 / F01: the default mount itself was unpinned (`${DUPLICATI_REQUIRE_MOUNT-}` survived). A PATH stub for
        `mountpoint` answers "not a mountpoint" and records what it was asked, so this holds on the owner's host (where
        /mnt/Backups IS mounted) and on CI (where it is not) alike, and never reads the real mount table."""
        bindir = self.tmp / "mp-bin"
        bindir.mkdir()
        asked = self.tmp / "mountpoint-asked"
        stub = bindir / "mountpoint"
        stub.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> {asked}\nexit 1\n', encoding="utf-8")
        stub.chmod(0o755)
        env = self.wrapper_env(CONTRACT)
        del env["DUPLICATI_REQUIRE_MOUNT"]
        env["PATH"] = f"{bindir}:{env.get('PATH', '/usr/bin:/bin')}"
        r = _run(["bash", str(WRAPPER), "--print-command"], env=env)
        self.assertEqual(r.returncode, 78, r.stderr)
        self.assertIn("FATAL: /mnt/Backups is not a mountpoint", r.stderr)
        self.assertEqual(asked.read_text(encoding="utf-8").split(), ["-q", "/mnt/Backups"])

    def test_an_empty_require_mount_switches_the_check_off_where_the_default_mount_is_absent(self):
        """R4A D-1 / R4C DEFECT-1: with `:-`, DUPLICATI_REQUIRE_MOUNT= still checked /mnt/Backups, so every suite and the
        installer's contract gate depended on this host's mount and would fail on a CI runner."""
        wrapper = self._wrapper_with_default_mount(self.tmp / "no-such-mount")
        env = self.wrapper_env(CONTRACT)
        r = _run(["bash", str(wrapper), "--print-command"], env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        del env["DUPLICATI_REQUIRE_MOUNT"]
        r = _run(["bash", str(wrapper), "--print-command"], env=env)
        self.assertEqual(r.returncode, 78, "unset, the default mount is still required")
        self.assertIn("is not a mountpoint", r.stderr)
        env["DUPLICATI_REQUIRE_MOUNT"] = str(self.tmp)
        r = _run(["bash", str(WRAPPER), "--print-command"], env=env)
        self.assertEqual(r.returncode, 78, "a named path that is not a mountpoint is refused")

    def _exec_env_of(self, env_text: str, **environ: str) -> subprocess.CompletedProcess:
        """Run the wrapper for real against a stub server that prints the TZ it was handed."""
        server = self.tmp / "server-stub"
        server.write_text('#!/usr/bin/env bash\nprintf "TZ=[%s]\\n" "${TZ-unset}"\nprintf "ARGV=[%s]\\n" "$*"\n', encoding="utf-8")
        server.chmod(0o755)
        env = self.wrapper_env(self.env_file(env_text))
        env["DUPLICATI_SERVER"] = str(server)
        env.pop("TZ", None)
        env.update(environ)
        return _run(["bash", str(WRAPPER)], env=env)

    def test_env_file_values_are_unquoted_and_never_override_the_environment(self):
        """R4C X10 / X11: matching quotes are stripped from a KEY=VALUE value; a variable systemd already set wins."""
        r = self._exec_env_of('TZ="Europe/Paris"\n')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("TZ=[Europe/Paris]", r.stdout)
        r = self._exec_env_of("export TZ='Europe/Paris'\n", TZ="UTC")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("TZ=[UTC]", r.stdout)
        self.assertIn("TZ already set in the environment; file value ignored", r.stderr)

    def test_crlf_lines_are_accepted_and_no_carriage_return_reaches_the_server(self):
        """R4C N-7 / X06: every trailing CR is stripped (2.3.0 stripped one); a CR inside a line is refused."""
        r = self._exec_env_of("TZ=UTC\r\n--webservice-port=8301\r\r\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("TZ=[UTC]", r.stdout)
        self.assertIn("--webservice-port=8301 ", r.stdout + " ")
        self.assertNotIn("\r", r.stdout)
        r = self.print_command(self.env_file("--log-level=x\ry\n"))
        self.assertEqual(r.returncode, 78, r.stderr)
        self.assertIn("a carriage return inside the line", r.stderr)

    def test_a_nul_byte_in_the_credential_is_refused(self):
        """R4C N-6: `$(<file)` drops a NUL that Python keeps -- one file, two keys."""
        creds = self.tmp / "creds"
        creds.mkdir()
        (creds / "settings-key").write_bytes(b"not-a-real\0key-0123456789\n")
        env = self.wrapper_env(CONTRACT)
        env["CREDENTIALS_DIRECTORY"] = str(creds)
        r = _run(["bash", str(WRAPPER), "--print-command"], env=env)
        self.assertEqual(r.returncode, 78, r.stderr)
        self.assertIn("contains a NUL byte", r.stderr)
        self.assertNotIn("not-a-real", r.stdout + r.stderr)

    def test_argv_still_carries_the_decrypt_flag_for_the_rekey_dropin(self):
        """Precedence 4 (argv) is the re-key's channel: the flag must pass there, and only there."""
        r = self.print_command(CONTRACT, "--disable-db-encryption")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.rstrip().endswith("--disable-db-encryption"), r.stdout)

    def test_print_command_redacts_by_option_name(self):
        """password-init= and pre-auth-tokens= slipped through a value-key substring match (Lane A)."""
        r = self.print_command(CONTRACT, "--webservice-password-init=not-a-real-pw", "--webservice-pre-auth-tokens=not-a-real-token")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("not-a-real", r.stdout + r.stderr)
        self.assertIn("--webservice-password-init=", r.stdout)
        self.assertIn("--webservice-pre-auth-tokens=", r.stdout)
        self.assertEqual(r.stdout.count("redacted"), 2)

    def test_option_names_dedup_case_insensitively(self):
        """The server's slim parser ignores case; a second spelling of the port is one option, the later one winning."""
        r = self.print_command(CONTRACT, "--Webservice-Port=8301")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("webservice-port"), 1, r.stdout)
        self.assertIn("--webservice-port=8301", r.stdout)

    def test_armed_daemon_opts_word_passes_through_as_an_unknown_option(self):
        """The vendor unit's armed argv word is tolerated by wrapper v2 (the 0700 gate, not argv, refuses the old folder)."""
        r = self.print_command(self.env_file("--webservice-port=8300\n"), '--daemon-opts="--webservice-port=8300"')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--daemon-opts=", r.stdout)
        self.assertIn("--webservice-port=8300", r.stdout)

    def test_default_env_path_is_outside_the_data_folder(self):
        """Round 3's D13: the wrapper's default is /etc/duplicati/env, never a file inside the 0700 data folder."""
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn('ENV_FILE="${DUPLICATI_ENV_FILE:-/etc/duplicati/env}"', text)
        self.assertNotIn("DUPLICATI_ENV_FILE:-/home/duplicati/.config/Duplicati/.env", text)

    def test_defaults_file_carries_the_ruled_flags_and_never_the_disable_flag(self):
        """D-1 and D-9 in DAEMON_OPTS; --disable-db-encryption satisfies the require flag and must never live here."""
        text = DEFAULTS.read_text(encoding="utf-8")
        opts = [line for line in text.splitlines() if line.startswith("DAEMON_OPTS=")]
        self.assertEqual(len(opts), 1)
        for flag in ("--require-db-encryption-key", "--webservice-disable-signin-tokens", "--webservice-allowed-hostnames=localhost", "--server-datafolder=/home/duplicati/.config/Duplicati"):
            self.assertIn(flag, opts[0])
        self.assertNotIn("--disable-db-encryption", opts[0])


class InstallerDriftGate(_Scratch):
    """Every path of the installer as a non-root --dry-run against a scratch install prefix."""

    def setUp(self):
        super().setUp()
        self.prefix = self.tmp / "prefix"
        self.prefix.mkdir()
        # R4C N-8: the dry run's ADVISORY `systemd-analyze verify` resolves units against the host's
        # /etc/systemd/system. A PATH stub keeps these tests off the host's unit tree (it is advisory, so
        # nothing here asserts its verdict).
        self.bindir = self.tmp / "bin"
        self.bindir.mkdir()
        stub = self.bindir / "systemd-analyze"
        stub.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)

    def installer(self, blessed: Path, *argv: str, script: Path = INSTALLER):
        env = RedactedEnv(os.environ, DUPLICATI_INSTALL_BLESSED=str(blessed), DUPLICATI_INSTALL_PREFIX=str(self.prefix), PYTHONDONTWRITEBYTECODE="1", PATH=f"{self.bindir}:{os.environ.get('PATH', '/usr/bin:/bin')}")
        return _run(["bash", str(script), "--dry-run", *argv], env=env)

    def blessed_equal_to_repo(self) -> Path:
        """A blessed file saying "installed == blessed == repository" for all seven destinations."""
        blessed = self.tmp / "blessed"
        lines = [f"{_sha256(REPO_ROOT / src)}  {self.prefix / dst}" for src, dst in zip(BLESSED_SOURCES, BLESSED_DESTS)]
        blessed.write_text("\n".join(lines) + "\n")
        return blessed

    def test_first_install_runs_to_the_end_without_a_blessed_file(self):
        """I-36: the never-blessed path must not end the script silently (it did, with status 1)."""
        r = self.installer(self.tmp / "absent")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("first install: no", r.stdout)
        self.assertIn("would: install -m 0755 -o root -g root scripts/duplicati-wrapper.bash", r.stdout)
        self.assertIn(f"would: install -m 0640 -o root -g duplicati util/systemd/duplicati-env.contract {self.prefix}/etc/duplicati/env", r.stdout)
        self.assertEqual(r.stdout.count("would: install -m "), 8, r.stdout)
        self.assertIn("would: write", r.stdout)
        self.assertIn("7 installed files", r.stdout)
        self.assertNotIn("restart duplicati.service", r.stdout, "the hint must say start, never restart")
        self.assertNotIn("DRIFT", r.stderr)

    def test_no_drift_when_installed_blessed_and_repository_agree(self):
        """Installed == blessed == repository: nothing to refuse (the installed copies are the repository files)."""
        for src, dst in zip(BLESSED_SOURCES, BLESSED_DESTS):
            target = self.prefix / dst
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / src, target)
        r = self.installer(self.blessed_equal_to_repo())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("DRIFT", r.stderr)
        self.assertNotIn("BEHAVIOUR CHANGE", r.stderr)
        self.assertNotIn("first install", r.stdout)

    def test_drift_of_an_installed_file_is_refused_and_kept_as_evidence_under_the_switch(self):
        """Someone edited the installed defaults file: refused without the switch; with it, copied aside before the install."""
        target = self.prefix / "etc/default/duplicati"
        target.parent.mkdir(parents=True)
        target.write_text('DAEMON_OPTS="--edited-by-hand"\n')
        blessed = self.blessed_equal_to_repo()
        r = self.installer(blessed)
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn(f"DRIFT: installed {target}", r.stderr)
        self.assertNotIn("BEHAVIOUR CHANGE", r.stderr)
        self.assertIn("Refusing to install", r.stderr)
        r2 = self.installer(blessed, "--update-backup-behavior")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertRegex(r2.stdout, rf"would: cp -p {re.escape(str(target))} {re.escape(str(target))}\.drifted-\d{{8}}T\d{{6}}Z")
        cp_line = r2.stdout.index("would: cp -p")
        install_line = r2.stdout.index(f"would: install -m 0644 -o root -g root util/systemd/duplicati.default {target}")
        self.assertLess(cp_line, install_line, "the drifted copy must be kept BEFORE it is overwritten")

    def test_behaviour_change_is_refused_without_the_switch_and_allowed_with_it(self):
        """A blessed checksum that matches neither the installed file nor the repository is a behaviour change."""
        blessed = self.tmp / "blessed"
        blessed.write_text("0" * 64 + f"  {self.prefix}/etc/default/duplicati\n")
        r = self.installer(blessed)
        self.assertEqual(r.returncode, 4)
        self.assertIn("BEHAVIOUR CHANGE", r.stderr)
        self.assertIn("Refusing to install", r.stderr)
        r2 = self.installer(blessed, "--update-backup-behavior")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("would: write", r2.stdout)
        self.assertNotIn("would: cp -p", r2.stdout, "nothing drifted, nothing to copy aside")

    def test_existing_env_contract_is_kept_not_overwritten(self):
        """An operator's tunables survive a re-install: the contract is installed only when absent."""
        env_dst = self.prefix / "etc/duplicati/env"
        env_dst.parent.mkdir(parents=True)
        env_dst.write_text("--webservice-port=8311\n")
        r = self.installer(self.tmp / "absent")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"kept existing {env_dst}", r.stdout)
        self.assertNotIn("would: install -m 0640", r.stdout)

    def test_dry_run_needs_no_root_and_rejects_unknown_arguments(self):
        r = self.installer(self.tmp / "absent", "--bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown argument", r.stderr)

    def test_dry_run_writes_no_pyc_into_the_checkout(self):
        """Lane C N-1: py_compile left a root-owned .pyc under util/ad-hoc/__pycache__ on every dry run."""
        pycache = REPO_ROOT / "util" / "ad-hoc" / "__pycache__"
        before = set(pycache.glob("yamaguchi_server_db_snapshot*")) if pycache.is_dir() else set()
        r = self.installer(self.tmp / "absent")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = set(pycache.glob("yamaguchi_server_db_snapshot*")) if pycache.is_dir() else set()
        self.assertEqual(after - before, set(), "the syntax check must not write bytecode")

    def _scratch_repo(self) -> Path:
        """A copy of everything the installer reads, so the contract can be mutated without touching the tree."""
        repo = self.tmp / "repo"
        for rel in INSTALLER_SOURCES:
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        return repo

    def test_contract_secret_gate_refuses_every_secret_shape(self):
        """Lane C: the 1.1.0 gate refused three names; the outage's own _OLD line and a commented key passed it."""
        repo = self._scratch_repo()
        contract = repo / "util/systemd/duplicati-env.contract"
        script = repo / "util/install_duplicati_service.bash"
        base = contract.read_text(encoding="utf-8")
        refused = {
            "active key": "SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop\n",
            "export quoted": "export SETTINGS_ENCRYPTION_KEY='abcdefghijklmnop'\n",
            "commented key": "# SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop\n",
            "the _OLD name": "SETTINGS_ENCRYPTION_KEY_OLD=abcdefghijklmnop\n",
            "duplicati__ passphrase": "DUPLICATI__PASSPHRASE=abcdefghijklmnop\n",
            "web credential": "DUPLICATI_WEB_CREDENTIAL=abcdefghijklmnop\n",
            "archive passphrase": "PASSPHRASE=abcdefghijklmnop\n",
            "spaced commented": "#  export MY_TOKEN = abcdefghijklmnop\n",
            "key option line": "--settings-encryption-key=abcdefghijklmnop\n",
            "password option line": "--webservice-password=abcdefghijklmnop\n",
            "decrypt flag": "--disable-db-encryption\n",
            "insecure folder": "--allow-insecure-datafolder=true\n",
            # R3A N-5: secrets behind more than one `#`, or on a commented option line.
            "double-hash key": "## SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop\n",
            "commented password option": "# --webservice-password=abcdefghijklmnop\n",
            "unspaced commented key option": "#--settings-encryption-key=abcdefghijklmnop\n",
            # R3C N-6: five lines the 1.2.0 installer passed and the wrapper refused at the next start.
            "reset-jwt-config": "--webservice-reset-jwt-config=true\n",
            "interface": "--webservice-interface=any\n",
            "server-datafolder": "--server-datafolder=/tmp/x\n",
            "allowed-hostnames": "--webservice-allowed-hostnames=*\n",
            "DUPLICATI__ export": "DUPLICATI__DISABLE_DB_ENCRYPTION=true\n",
            # 1.3.0: the wrapper's allow-list -- an option that is not a tunable never passes.
            "not a tunable": "--register-remote-control=https://example.invalid/x\n",
        }
        # Every denied name, lower- and mixed-case (R3A D-1 / R3C D-3: parameters-file was missing).
        for name in WrapperEnvContract.DENIED:
            mixed = "-".join(part.capitalize() for part in name.split("-"))
            refused[f"denied {name}"] = f"--{name}=/abcdefghijklmnop\n"
            refused[f"denied {mixed}"] = f"--{mixed}\n"
        for label, line in refused.items():
            with self.subTest(label=label):
                contract.write_text(base + line, encoding="utf-8")
                r = self.installer(self.tmp / "absent", script=script)
                self.assertEqual(r.returncode, 2, f"{label}: {r.stdout}\n{r.stderr}")
                self.assertIn("REFUSING", r.stderr)
                self.assertNotIn("abcdefghijklmnop", r.stderr + r.stdout)
        allowed = {
            "placeholder": "SETTINGS_ENCRYPTION_KEY=<from-credstore>\n",
            "variable": "SETTINGS_ENCRYPTION_KEY=$SETTINGS_ENCRYPTION_KEY\n",
            "empty": "SETTINGS_ENCRYPTION_KEY=\n",
            "port option": "--webservice-port=8301\n",
            "comment mentioning the flag": "# the re-key's drop-in carries --disable-db-encryption, never this file\n",
            # R3C N-6, the other direction: 1.2.0 refused a tunable the wrapper accepts ("token" in its name).
            "token-duration tunable": "--Webservice-Token-Duration=1h\n",
        }
        for label, line in allowed.items():
            with self.subTest(label=label):
                contract.write_text(base + line, encoding="utf-8")
                r = self.installer(self.tmp / "absent", script=script)
                self.assertEqual(r.returncode, 0, f"{label}: {r.stderr}")
        contract.write_text(base, encoding="utf-8")
        self.assertEqual(self.installer(self.tmp / "absent", script=script).returncode, 0)


class RecoveryHelperGates(_Scratch):
    def setUp(self):
        super().setUp()
        self.key = self.tmp / "key"
        self.pw = self.tmp / "pw"
        for f in (self.key, self.pw):
            f.write_text("dummy\n")
            f.chmod(0o600)
        self.me = subprocess.run(["id", "-un"], capture_output=True, text=True, check=True).stdout.strip()

    def pwinit(self, *argv: str, server: str | None = None, dry_run: bool = True):
        env = RedactedEnv(os.environ, DUPLICATI_RUN_AS=self.me, **({"DUPLICATI_SERVER": server} if server else {}))
        cmd = ["bash", str(PASSWORD_INIT), "--data-folder", str(self.data), "--settings-key-file", str(self.key), "--ui-password-file", str(self.pw), "--port", "1", *argv]
        if dry_run:
            cmd.append("--dry-run")
        return _run(cmd, env=env)

    def test_password_init_dry_run_names_the_hand_start_and_expects_102(self):
        r = self.pwinit()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--parameters-file=<file>", r.stderr)
        self.assertIn("expecting exit 102", r.stderr)
        self.assertNotIn("dummy", r.stderr + r.stdout)

    def test_password_init_refuses_a_group_readable_secret_file(self):
        self.pw.chmod(0o640)
        r = self.pwinit()
        self.assertEqual(r.returncode, 1)
        self.assertIn("must be mode 0600", r.stderr)

    def test_password_init_refuses_a_data_folder_that_is_not_0700(self):
        self.data.chmod(0o750)
        r = self.pwinit()
        self.assertEqual(r.returncode, 1)
        self.assertIn("mode 0700", r.stderr)

    def test_password_init_refuses_a_port_in_use(self):
        """The gate captures the listener list first: a `ss | grep -q` pipeline failed OPEN under pipefail (Lane C N-3)."""
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            s.listen()
            port = s.getsockname()[1]
            r = self.pwinit("--port", str(port))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn(f"port {port} is in use", r.stderr)

    def _stub_server(self, exit_code: int) -> Path:
        """A stand-in for duplicati-server: records that the parameters file existed and was 0600, then exits as told."""
        stub = self.tmp / f"server-{exit_code}"
        stub.write_text("#!/usr/bin/env bash\n" 'for a in "$@"; do case "$a" in --parameters-file=*) f="${a#--parameters-file=}";; esac; done\n' f"stat -c '%a' \"$f\" > {self.tmp}/seen-mode\n" f'wc -l < "$f" > {self.tmp}/seen-lines\n' f"exit {exit_code}\n")
        stub.chmod(0o700)
        return stub

    def test_password_init_shreds_the_parameters_file_on_every_exit(self):
        """The real path, as the current user, against a stub server: 102 → 0, 103 → 1 (A0 case), 200 → 1; the file is gone each time."""
        expected = {102: (0, "exit 102: UI password set"), 103: (1, "Procedure A0 case"), 200: (1, "single-instance lock")}
        for code, (rc, text) in expected.items():
            with self.subTest(server_exit=code):
                r = self.pwinit(server=str(self._stub_server(code)), dry_run=False)
                self.assertEqual(r.returncode, rc, r.stderr)
                self.assertIn(text, r.stderr)
                self.assertEqual((self.tmp / "seen-mode").read_text().strip(), "600")
                self.assertEqual((self.tmp / "seen-lines").read_text().strip(), "2")
                self.assertEqual(list(self.data.glob(".password-init-*")), [], "the parameters file must be shredded")
                self.assertNotIn("dummy", r.stderr + r.stdout)

    def test_password_init_refuses_a_secret_with_edge_whitespace(self):
        """The server trims every parameters-file line, so a value with edge whitespace would not survive verbatim."""
        self.pw.write_text(" dummy \n")
        r = self.pwinit(server=str(self._stub_server(102)), dry_run=False)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("whitespace", r.stderr)
        self.assertFalse((self.tmp / "seen-mode").exists(), "the server must not have been invoked")

    def test_password_init_dry_run_runs_the_secret_format_gate(self):
        """R3C N-1: the dry run said "gates passed" without the whitespace gate, which ran only on the real path.
        Every check is applied to BOTH files the hand start reads -- the settings key and the UI password
        (round 5, R5A NIT-4 F19: the NUL check was tested on the password only)."""
        for which in ("key", "pw"):
            for content, needle in ((" dummy \n", "whitespace"), ("dummy\r\n", "carriage return"), ("dum\0my\n", "NUL byte"), ("dummy\nsecond\n", "exactly one non-empty line")):
                with self.subTest(file=which, content=repr(content)):
                    for f in (self.key, self.pw):
                        f.write_text("dummy\n")
                    getattr(self, which).write_text(content, newline="")
                    r = self.pwinit()
                    self.assertEqual(r.returncode, 1, r.stderr)
                    self.assertIn(needle, r.stderr)
                    self.assertNotIn("gates passed", r.stderr)
                    self.assertNotIn("dummy", r.stderr + r.stdout)

    REKEY_STEPS = [
        ("refuse unless", "preflight"),
        ("install -d -m 0700", "workdir"),
        ("--unrewritten", "count-unrewritten"),
        ("yamaguchi_server_api.py serverstate", "serverstate"),
        ("yamaguchi_server_api.py pause", "pause"),
        ("yamaguchi_server_api.py serverstate", "serverstate"),
        ("systemctl stop duplicati.service", "stop"),
        ("--disable-db-encryption", "write-dropin"),
        ("systemctl daemon-reload", "daemon-reload"),
        ("systemctl start duplicati.service", "start"),
        ("wait for 'Server has started'", "wait"),
        ("systemctl stop duplicati.service", "stop"),
        ("cp -p {cred} {cred}.old", "swap-keys"),
        ("rm -f /run/systemd/system/duplicati.service.d/zz-rekey-disable-db-encryption.conf", "remove-dropin"),
        ("systemctl start duplicati.service", "start"),
        ("wait for 'Server has started'", "wait"),
        ("systemctl stop duplicati.service", "stop"),
        ("2026-10-03_rekey_gate.py", "gate"),
        ("PRAGMA wal_checkpoint(TRUNCATE); VACUUM;", "vacuum"),
        ("systemctl start duplicati.service", "start"),
        ("wait for 'Server has started'", "wait"),
        ("yamaguchi_server_api.py resume", "resume"),
        ("api serverstate (must read Running", "verify"),
    ]

    def rekey_dry_run(self):
        """The dry run with REKEY_INSTALLED_UNIT pointing at an ABSENT scratch path: the host's
        /etc/systemd/system/duplicati.service, once the installer has run there, must not change what it
        prints (round 3, R3C D-4); REKEY_CREDSTORE_DIR keeps it from stat-ing /etc/credstore (round 4,
        R4C NIT-8)."""
        self.installed_unit = self.tmp / "no-installed-unit" / "duplicati.service"
        self.cred = self.tmp / "no-credstore" / "duplicati-settings-key"
        env = RedactedEnv(os.environ, REKEY_INSTALLED_UNIT=str(self.installed_unit), REKEY_CREDSTORE_DIR=str(self.cred.parent), PYTHONDONTWRITEBYTECODE="1")
        return _run(["bash", str(REKEY), "--dry-run"], env=env)

    def test_rekey_dry_run_prints_the_whole_sequence_in_order_and_never_reverts(self):
        """Lane C: matching first occurrences was blind to three re-orderings; the BLOCKER was `systemctl revert`."""
        r = self.rekey_dry_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        would = [line.split("would: ", 1)[1] for line in r.stderr.splitlines() if "would: " in line]
        self.assertEqual(len(would), len(self.REKEY_STEPS), "\n".join(would))
        for (needle, label), line in zip(self.REKEY_STEPS, would):
            self.assertIn(needle.format(cred=self.cred), line, f"step {label!r}: {line}")
        self.assertNotIn("/etc/credstore", r.stderr)
        self.assertNotIn("systemctl revert", r.stderr)
        dropin = next(line for line in would if "--disable-db-encryption" in line)
        self.assertIn("/run/systemd/system/duplicati.service.d/", dropin)
        self.assertNotIn("/etc/default/duplicati", dropin, "the flag must ride a runtime drop-in, never the defaults file")
        remove = next(line for line in would if line.startswith("rm -f /run/systemd/system/duplicati.service.d/"))
        self.assertIn(f"assert FragmentPath is still {self.installed_unit}", remove)
        self.assertIn(f"mv -f {self.cred}.new {self.cred} ", "\n".join(would))
        self.assertIn("DRY RUN:", r.stderr, "the dry run must say when it substitutes the repository unit's ExecStart")
        self.assertIn("snapshot timer is neither enabled nor active", would[0], "R3B N-8: the timer must be inactive as well as not enabled")

    def test_rekey_dry_run_never_claims_a_start_happened(self):
        """R3C N-5: the dry run printed "decrypt start done: every field is now CLEARTEXT on disk"."""
        r = self.rekey_dry_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("decrypt start done", r.stderr)
        self.assertNotIn("is now CLEARTEXT", r.stderr)
        self.assertIn("would be CLEARTEXT on disk; nothing was started", r.stderr)

    def test_rekey_script_text_never_reverts(self):
        """`systemctl revert` deletes the installed unit when a vendor copy exists under /usr/lib (the round's BLOCKER)."""
        text = REKEY.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"^\s*(run\s+)?systemctl revert", "no code path may revert the unit")
        self.assertIn("trap cleanup EXIT", text)
        self.assertIn("ActiveTask", text)


class RekeyGate(unittest.TestCase):
    """util/ad-hoc/2026-10-03_rekey_gate.py against a scratch server database with enc-v1 blobs."""

    K1 = "dummy-key-one-not-a-real-secret"
    K2 = "dummy-key-two-not-a-real-secret"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rekey-gate-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    @staticmethod
    def blob(key: str, ciphertext: str = "deadbeef") -> str:
        return "enc-v1:" + hashlib.sha256(ciphertext.encode()).hexdigest() + hashlib.sha256(key.encode()).hexdigest() + ciphertext

    def database(self, flag="True", option_key=K1, backup_key=K1, source_key=K1, conn_key=K1, bturl_key=K1, blobs=True) -> Path:
        db = self.tmp / f"db-{len(list(self.tmp.iterdir()))}.sqlite"
        con = sqlite3.connect(db)
        con.executescript('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT);' 'CREATE TABLE "Backup" ("ID" INTEGER, "Name" TEXT, "TargetURL" TEXT, "DBPath" TEXT);' 'CREATE TABLE "Source" ("BackupID" INTEGER, "Path" TEXT);' 'CREATE TABLE "ConnectionString" ("ID" INTEGER, "BaseUrl" TEXT);' 'CREATE TABLE "BackupTargetUrl" ("ID" INTEGER, "BackupID" INTEGER, "TargetURL" TEXT);')
        if flag is not None:
            con.execute('INSERT INTO "Option" VALUES (-2, "", "encrypted-fields", ?)', (flag,))
        con.execute('INSERT INTO "Option" VALUES (-2, "", "startup-delay", "0")')
        if blobs:
            con.execute('INSERT INTO "Option" VALUES (2, "", "passphrase", ?)', (self.blob(option_key, "p"),))
            con.execute('INSERT INTO "Backup" VALUES (2, "Yamaguchi", ?, "x.sqlite")', (self.blob(backup_key, "t"),))
            con.execute('INSERT INTO "Source" VALUES (2, ?)', (self.blob(source_key, "s"),))
            con.execute('INSERT INTO "ConnectionString" VALUES (1, ?)', (self.blob(conn_key, "c"),))
            con.execute('INSERT INTO "BackupTargetUrl" VALUES (1, 2, ?)', (self.blob(bturl_key, "u"),))
        con.commit()
        con.close()
        return db

    def gate(self, db: Path, key: str):
        key_file = self.tmp / "keyfile"
        key_file.write_text(key + "\n")
        key_file.chmod(0o600)
        return _run(["python3", str(GATE), str(db), str(key_file)])

    def test_passes_under_the_right_key(self):
        r = self.gate(self.database(), self.K1)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("encrypted-fields=True blobs=5 under-this-key=5 under-another-key=0", r.stdout)
        self.assertIn("ConnectionString.BaseUrl=1", r.stdout)
        self.assertNotIn(self.K1, r.stdout + r.stderr)

    def test_fails_under_another_key(self):
        r = self.gate(self.database(), self.K2)
        self.assertEqual(r.returncode, 1)
        self.assertIn("GATE FAILED", r.stderr)

    def test_fails_when_one_blob_in_any_column_is_under_another_key(self):
        """ConnectionString.BaseUrl is the column the product's rewrite pass never touches (Lane A/C)."""
        for column in ("option_key", "backup_key", "source_key", "conn_key", "bturl_key"):
            with self.subTest(column=column):
                r = self.gate(self.database(**{column: self.K2}), self.K1)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("under-another-key=1", r.stdout)

    def test_fails_when_the_flag_is_false_or_absent(self):
        for flag in ("False", None):
            with self.subTest(flag=flag):
                r = self.gate(self.database(flag=flag), self.K1)
                self.assertEqual(r.returncode, 1, r.stdout)

    def test_fails_with_zero_blobs(self):
        """An empty result is a FAIL, never a vacuous pass."""
        r = self.gate(self.database(blobs=False), self.K1)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("blobs=0", r.stdout)

    def test_tolerates_an_absent_table_but_not_a_missing_key_file(self):
        db = self.database()
        con = sqlite3.connect(db)
        con.execute('DROP TABLE "ConnectionString"')
        con.commit()
        con.close()
        r = self.gate(db, self.K1)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ConnectionString.BaseUrl=absent", r.stdout)
        r2 = _run(["python3", str(GATE), str(db), str(self.tmp / "no-such-key")])
        self.assertEqual(r2.returncode, 2)
        self.assertEqual(stat.S_IMODE((self.tmp / "keyfile").stat().st_mode), 0o600)

    def test_a_blob_stored_as_sqlite_blob_type_is_judged_too(self):
        """R3C N-12: `str(bytes)` read b'enc-v1:…', so a BLOB-typed value under another key was skipped."""
        db = self.database()
        con = sqlite3.connect(db)
        con.execute('INSERT INTO "Source" VALUES (2, ?)', (self.blob(self.K2, "b").encode(),))
        con.commit()
        con.close()
        r = self.gate(db, self.K1)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("under-another-key=1", r.stdout)
        self.assertIn("Source.Path=2", r.stdout)

    def test_a_key_file_with_a_carriage_return_is_refused(self):
        """R3C N-2: the unit hands the server the CR; a text-mode read here dropped it and judged another key."""
        key_file = self.tmp / "crkey"
        key_file.write_bytes(self.K1.encode() + b"\r\n")
        r = _run(["python3", str(GATE), str(self.database()), str(key_file)])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("carriage return", r.stderr)

    def unrewritten(self, db: Path):
        return _run(["python3", str(GATE), "--unrewritten", str(db)])

    def test_unrewritten_counts_what_the_product_never_rewrites(self):
        """R3A D-5 / R3C D-2: the re-key's pre-flight. ConnectionString is never rewritten; a BackupTargetUrl row
        of a live backup is (LoadChildren + AddOrUpdateBackup), one of no backup is not."""
        r = self.unrewritten(self.database())
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ConnectionString.BaseUrl=1", r.stdout)
        self.assertIn("BackupTargetUrl.TargetURL orphaned=0 attached=1", r.stdout)
        con_db = self.database()
        con = sqlite3.connect(con_db)
        con.execute('DELETE FROM "ConnectionString"')
        con.commit()
        con.close()
        r = self.unrewritten(con_db)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ConnectionString.BaseUrl=0 Option.Value orphaned=0 attached=1 Source.Path orphaned=0 attached=1 BackupTargetUrl.TargetURL orphaned=0 attached=1", r.stdout)
        con = sqlite3.connect(con_db)
        con.execute('UPDATE "BackupTargetUrl" SET "BackupID" = 77')
        con.commit()
        con.close()
        r = self.unrewritten(con_db)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BackupTargetUrl.TargetURL orphaned=1 attached=0", r.stdout)
        self.assertNotIn("deadbeef", r.stdout + r.stderr)

    def test_unrewritten_counts_orphaned_option_and_source_but_not_the_settings_rows(self):
        """R4C DEFECT-2: Option and Source have no FK (Schema.sql 44-45, 72-73), so a row of a deleted job keeps
        its blob and the product's rewrite never reaches it. Option rows at -1 (ANY_BACKUP_ID, re-saved at
        Connection.cs 145) and -2 (SERVER_SETTINGS_ID, re-saved through the EncryptedFields setter) are not orphans."""
        base = self.database()
        con = sqlite3.connect(base)
        con.execute('DELETE FROM "ConnectionString"')
        con.execute('INSERT INTO "Option" VALUES (-1, ?, ?, ?)', ("", "passphrase", self.blob(self.K1, "any")))
        con.execute('INSERT INTO "Option" VALUES (-2, ?, ?, ?)', ("", "pbkdf-config", self.blob(self.K1, "srv")))
        con.commit()
        con.close()
        r = self.unrewritten(base)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Option.Value orphaned=0 attached=3", r.stdout)
        for table, sql, needle in (("Option", 'INSERT INTO "Option" VALUES (7, ?, ?, ?)', "Option.Value orphaned=1"), ("Source", 'INSERT INTO "Source" VALUES (7, ?)', "Source.Path orphaned=1")):
            with self.subTest(table=table):
                db = self.tmp / f"orphan-{table}.sqlite"
                shutil.copy(base, db)
                con = sqlite3.connect(db)
                con.execute(sql, ("", "passphrase", self.blob(self.K2, "o")) if table == "Option" else (self.blob(self.K2, "o"),))
                con.commit()
                con.close()
                r = self.unrewritten(db)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn(needle, r.stdout)

    def test_unrewritten_counts_a_source_row_at_a_settings_id_as_orphaned(self):
        """R5A NIT-5 F14: -1/-2 are settings ids for Option only; SetSources writes per backup, so a Source row
        at -1 or -2 is never re-saved."""
        for bid in (-1, -2):
            with self.subTest(backup_id=bid):
                db = self.database()
                con = sqlite3.connect(db)
                con.execute('DELETE FROM "ConnectionString"')
                con.execute('INSERT INTO "Source" VALUES (?, ?)', (bid, self.blob(self.K2, "s")))
                con.commit()
                con.close()
                r = self.unrewritten(db)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("Source.Path orphaned=1 attached=1", r.stdout)

    def test_unrewritten_with_no_backup_table_counts_every_child_row_as_orphaned(self):
        db = self.database()
        con = sqlite3.connect(db)
        con.execute('DELETE FROM "ConnectionString"')
        con.execute('DROP TABLE "Backup"')
        con.commit()
        con.close()
        r = self.unrewritten(db)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Option.Value orphaned=1 attached=0 Source.Path orphaned=1 attached=0", r.stdout)

    def test_a_key_file_with_a_nul_is_refused(self):
        """R4C NIT-6: the wrapper's `$(<file)` drops a NUL, so the server would get a different key than judged here."""
        key_file = self.tmp / "nulkey"
        key_file.write_bytes(self.K1.encode()[:5] + b"\0" + self.K1.encode()[5:] + b"\n")
        r = _run(["python3", str(GATE), str(self.database()), str(key_file)])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("NUL", r.stderr)

    def test_unrewritten_tolerates_absent_tables_and_refuses_an_unreadable_copy(self):
        db = self.database()
        con = sqlite3.connect(db)
        con.execute('DROP TABLE "ConnectionString"')
        con.execute('DROP TABLE "BackupTargetUrl"')
        con.commit()
        con.close()
        r = self.unrewritten(db)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ConnectionString.BaseUrl=absent", r.stdout)
        self.assertIn("BackupTargetUrl.TargetURL=absent", r.stdout)
        bad = self.tmp / "not-a-db.sqlite"
        bad.write_text("not a database")
        self.assertEqual(self.unrewritten(bad).returncode, 2)


if __name__ == "__main__":
    unittest.main()
