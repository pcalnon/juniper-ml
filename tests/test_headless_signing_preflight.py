#!/usr/bin/env python3
"""Hermetic gate for util/headless_signing_preflight.bash (turing bring-up plan task B7).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The preflight reports whether a host is set up to sign git commits, using non-credential checks
only (``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` task B7,
decisions D3 and D11). It pins two regressions:

- R-B7a: a ``user.signingkey`` without the trailing ``!`` (the 2026-07-16 ambiguity class).
- R-B7b: a curses or tty pinentry, which cannot prompt from a GUI or headless process.

Fixtures:

- a stub ``gpgconf`` (``GPGCONF``) that prints a temp homedir, a socket path and a default pinentry;
- a temp ``GNUPGHOME`` holding a fixture ``gpg-agent.conf``;
- stub pinentries that answer the Assuan ``GETINFO flavor`` probe and record every line sent;
- a real git repository with an isolated global config, whose ``gpg.program`` is a stub that only
  verifies (a signed HEAD is a hand-built commit object, so nothing is ever signed);
- a real Unix socket (AF_UNIX bind) under a short ``/tmp`` path, since macOS caps ``sun_path`` at
  104 bytes.

Tripwire ``gpg``, ``gpg2``, ``gpgconf``, ``pinentry``, ``ssh-add``, ``ykman`` and friends lead
``PATH``; ``tearDown`` fails any case in which one ran.

The child environment drops every ``GIT_*``, ``GNUPG*``, ``GPG*``, ``PINENTRY*`` and ``SSH_A*``
variable. Agent sessions on turing carry the D11 override (``GIT_CONFIG_COUNT`` with
``GIT_CONFIG_KEY_n=commit.gpgsign`` / ``GIT_CONFIG_VALUE_n=false``), and only the D11 cases set it
back, deliberately. The real ``~/.gnupg`` is never touched.

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor).
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from collections.abc import Mapping
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "headless_signing_preflight.bash"
TIMEOUT_SECONDS = 60

# Fixture key material is fake: no such key exists anywhere.
FAKE_FPR = "0123456789ABCDEF0123456789ABCDEF01234567"
FAKE_KEYID = FAKE_FPR[-16:]

# The checks that pass or fail on every run. head-signature joins them under --require-signed-head.
CHECK_IDS = ["signing-key", "commit-gpgsign", "pinentry", "agent-socket", "external-cache"]

SCRUBBED_PREFIXES = ("GIT_", "GNUPG", "GPG", "PINENTRY", "SSH_A")

# The override turing's agent sessions carry (plan D11 item 1).
D11_ENV = {
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "commit.gpgsign",
    "GIT_CONFIG_VALUE_0": "false",
    "GIT_CONFIG_KEY_1": "tag.gpgsign",
    "GIT_CONFIG_VALUE_1": "false",
}

GPGCONF_STUB = """\
#!/bin/bash
# gpgconf stub: answers --list-dirs homedir|agent-socket and --list-components from STUB_* values.
printf '%s\\n' "$*" >> "$STUB_GPGCONF_LOG"
if [ -n "${STUB_GPGCONF_FAIL:-}" ]; then
    echo "gpgconf: stub failure" >&2
    exit 2
fi
case "$*" in
    "--list-dirs homedir") printf '%s\\n' "${STUB_GPGCONF_HOMEDIR:-}" ;;
    "--list-dirs agent-socket") printf '%s\\n' "${STUB_GPGCONF_SOCKET:-}" ;;
    "--list-components")
        printf 'gpg:OpenPGP:/nonexistent/bin/gpg\\n'
        printf 'gpg-agent:Private Keys:/nonexistent/bin/gpg-agent\\n'
        if [ -n "${STUB_GPGCONF_PINENTRY:-}" ]; then
            printf 'pinentry:Passphrase Entry:%s\\n' "$STUB_GPGCONF_PINENTRY"
        fi
        ;;
    *)
        echo "gpgconf stub: refusing argv: $*" >&2
        exit 99
        ;;
esac
"""

# git's gpg.program. It only verifies: it consumes the payload and prints the status lines of
# STUB_GPG_RESULT. Anything but --verify is recorded and refused (tearDown checks the record).
GPG_VERIFY_STUB = f"""\
#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_GPG_LOG"
case " $* " in
    *" --verify "*) ;;
    *)
        echo "gpg stub: refusing argv: $*" >&2
        exit 99
        ;;
esac
cat >/dev/null
case "${{STUB_GPG_RESULT:-good}}" in
    good)
        echo "[GNUPG:] NEWSIG"
        echo "[GNUPG:] GOODSIG {FAKE_KEYID} Preflight Test <preflight@example.invalid>"
        echo "[GNUPG:] VALIDSIG {FAKE_FPR} 2026-10-17 1760000000 0 4 0 22 10 00 {FAKE_FPR}"
        echo "[GNUPG:] TRUST_ULTIMATE 0 pgp"
        ;;
    errsig)
        echo "[GNUPG:] NEWSIG"
        echo "[GNUPG:] ERRSIG {FAKE_KEYID} 22 10 00 1760000000 9 -"
        echo "[GNUPG:] NO_PUBKEY {FAKE_KEYID}"
        exit 2
        ;;
esac
"""

# A tool the preflight must never run. Records the call and fails.
TRIPWIRE = """\
#!/bin/bash
printf '%s %s\\n' "${0##*/}" "$*" >> "$STUB_TRIPWIRE_LOG"
exit 97
"""
TRIPWIRES = ("gpg", "gpg2", "gpgconf", "gpg-agent", "gpg-connect-agent", "scdaemon", "pinentry", "pinentry-mac", "ssh-add", "ykman")

# A git that must never run: argument errors exit before any tool is consulted.
FORBIDDEN_GIT = """\
#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_GIT_LOG"
exit 97
"""

NOT_A_PINENTRY = """\
#!/bin/bash
cat >/dev/null
echo "hello"
"""

HANGING_PINENTRY = """\
#!/bin/bash
exec sleep 15
"""


def pinentry_stub(flavor: str) -> str:
    """Speaks just enough Assuan to answer ``GETINFO flavor``; records each line it is sent."""
    return f"""\
#!/bin/bash
echo "OK Pleased to meet you, process $$"
while IFS= read -r line; do
    printf '%s %s\\n' "{flavor}" "$line" >> "$STUB_PINENTRY_LOG"
    case "$line" in
        "GETINFO flavor") echo "D {flavor}"; echo "OK" ;;
        BYE) echo "OK closing connection"; exit 0 ;;
        *) echo "ERR 83886355 Unknown IPC command" ;;
    esac
done
"""


def _write_exe(path: Path, body: str, mode: int = 0o755) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(mode)
    return path


class _Fixture(unittest.TestCase):
    """A host on which every check passes: a pinned key, gpgsign on, a GUI pinentry, the socket, the cache line."""

    def setUp(self) -> None:
        real_git = shutil.which("git")
        if real_git is None:
            self.skipTest("git not installed")
        self.real_git = real_git
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.home = self.base / "home"
        self.gnupghome = self.base / "gnupghome"
        self.bin = self.base / "bin"
        self.trip = self.base / "trip"
        self.logs = self.base / "logs"
        self.repo = self.base / "repo"
        self.elsewhere = self.base / "elsewhere"
        for d in (self.home, self.gnupghome, self.bin, self.trip, self.logs, self.elsewhere):
            d.mkdir()
        self.gitconfig = self.base / "gitconfig"
        self.agent_conf = self.gnupghome / "gpg-agent.conf"
        self.socket_path = self._make_socket()

        self.gpgconf = _write_exe(self.bin / "gpgconf-stub", GPGCONF_STUB)
        self.gpg_verify = _write_exe(self.bin / "gpg-verify-stub", GPG_VERIFY_STUB)
        self.forbidden_git = _write_exe(self.bin / "git-forbidden", FORBIDDEN_GIT)
        for name in TRIPWIRES:
            _write_exe(self.trip / name, TRIPWIRE)
        self.pinentry = self.make_pinentry("pinentry-gui", "mac")
        self.write_agent_conf(f"pinentry-program {self.pinentry}", "no-allow-external-cache")
        self.write_gitconfig()

        self.env = self._base_env()
        self.git("init", "-q", str(self.repo))
        self.git("-C", str(self.repo), "commit", "-q", "--allow-empty", "--no-gpg-sign", "-m", "fixture: unsigned")

    def tearDown(self) -> None:
        tripped = self.read_log("tripwire.log")
        self.assertEqual(tripped, [], "the preflight ran a tool it must never run")
        for call in self.read_log("gpg.log"):
            self.assertIn("--verify", call.split(), f"git asked gpg for more than a verification: {call}")

    # -- fixture builders -------------------------------------------------------------------------

    def _make_socket(self) -> Path:
        # TMPDIR on macOS is already about 50 bytes long, so the socket gets a short directory of its own.
        sock_dir = tempfile.mkdtemp(prefix="hsp-", dir="/tmp" if os.path.isdir("/tmp") else None)
        self.addCleanup(shutil.rmtree, sock_dir, True)
        path = Path(sock_dir) / "S.gpg-agent"
        if len(os.fsencode(path)) >= 100:
            self.skipTest(f"no directory short enough for a Unix socket: {path}")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.bind(str(path))
        return path

    def _base_env(self) -> RedactedEnv:
        env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith(SCRUBBED_PREFIXES)})
        env.update(
            HOME=str(self.home),
            LC_ALL="C",
            PATH=f"{self.trip}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=str(self.gitconfig),
            GIT_TERMINAL_PROMPT="0",
            GIT_CEILING_DIRECTORIES=str(self.base),
            GNUPGHOME=str(self.gnupghome),
            GPGCONF=str(self.gpgconf),
            STUB_GPGCONF_HOMEDIR=str(self.gnupghome),
            STUB_GPGCONF_SOCKET=str(self.socket_path),
            STUB_GPGCONF_LOG=str(self.logs / "gpgconf.log"),
            STUB_PINENTRY_LOG=str(self.logs / "pinentry.log"),
            STUB_GPG_LOG=str(self.logs / "gpg.log"),
            STUB_TRIPWIRE_LOG=str(self.logs / "tripwire.log"),
            STUB_GIT_LOG=str(self.logs / "git.log"),
        )
        return env

    def make_pinentry(self, name: str, flavor: str) -> Path:
        return _write_exe(self.bin / name, pinentry_stub(flavor))

    def write_agent_conf(self, *lines: str) -> None:
        self.agent_conf.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")

    def write_gitconfig(self, *, signingkey: str | None = f"{FAKE_FPR}!", commit_gpgsign: str | None = "true", tag_gpgsign: str | None = "true") -> None:
        lines = ["[init]", "\tdefaultBranch = main", "[user]", "\tname = Preflight Test", "\temail = preflight@example.invalid"]
        if signingkey is not None:
            lines.append(f"\tsigningkey = {signingkey}")
        if commit_gpgsign is not None:
            lines += ["[commit]", f"\tgpgsign = {commit_gpgsign}"]
        if tag_gpgsign is not None:
            lines += ["[tag]", f"\tgpgsign = {tag_gpgsign}"]
        lines += ["[gpg]", f"\tprogram = {self.gpg_verify}"]
        self.gitconfig.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def git(self, *args: str, stdin: str | None = None) -> str:
        proc = subprocess.run([self.real_git, *args], env=self.env, input=stdin, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=True)
        return proc.stdout.strip()

    def make_signed_head(self) -> None:
        """Point HEAD at a commit that carries a signature block, built by hand: nothing is signed."""
        repo = str(self.repo)
        header = "gpgsig" if self.git("-C", repo, "rev-parse", "--show-object-format") == "sha1" else "gpgsig-sha256"
        tree = self.git("-C", repo, "hash-object", "-t", "tree", "-w", "--stdin", stdin="")
        parent = self.git("-C", repo, "rev-parse", "HEAD")
        body = "\n".join(
            [
                f"tree {tree}",
                f"parent {parent}",
                "author Preflight Test <preflight@example.invalid> 1760000000 +0000",
                "committer Preflight Test <preflight@example.invalid> 1760000000 +0000",
                f"{header} -----BEGIN PGP SIGNATURE-----",
                " ",
                " iHUEABYKAB0WIQRmaXh0dXJlIGJsb2NrLCBub3QgYSBzaWduYXR1cmUA",
                " =fake",
                " -----END PGP SIGNATURE-----",
                "",
                "fixture: a signature block for the gpg stub to verify; nothing was signed",
                "",
            ]
        )
        commit = self.git("-C", repo, "hash-object", "-t", "commit", "-w", "--stdin", stdin=body)
        self.git("-C", repo, "update-ref", "HEAD", commit)

    # -- running and reading ----------------------------------------------------------------------

    def run_script(self, *args: str, cwd: Path | None = None, unset: tuple[str, ...] = (), extra_env: Mapping[str, str] | None = None, **env_overrides: str) -> subprocess.CompletedProcess[str]:
        where = cwd or self.repo
        env = self.env.copy()
        for name in unset:
            env.pop(name, None)
        env.update(extra_env or {})
        env.update(env_overrides)
        env["PWD"] = str(where)
        return subprocess.run(["/bin/bash", str(SCRIPT_PATH), *args], cwd=where, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def read_log(self, name: str) -> list[str]:
        path = self.logs / name
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    @staticmethod
    def report_lines(proc: subprocess.CompletedProcess[str]) -> list[tuple[str, str, str]]:
        lines = []
        for line in proc.stdout.splitlines():
            match = re.match(r"^(PASS|FAIL|INFO)  (\S+)\s+(.*)$", line)
            if match:
                lines.append((match.group(1), match.group(2), match.group(3)))
        return lines

    def report_of(self, proc: subprocess.CompletedProcess[str], check_id: str) -> tuple[str, str]:
        for status, cid, detail in self.report_lines(proc):
            if cid == check_id:
                return status, detail
        raise AssertionError(f"no report line for {check_id}:\n{proc.stdout}")

    def ids_with(self, proc: subprocess.CompletedProcess[str], status: str) -> list[str]:
        return [cid for st, cid, _ in self.report_lines(proc) if st == status]

    @staticmethod
    def listed_failures(proc: subprocess.CompletedProcess[str]) -> list[str]:
        return [line[4:].split(":", 1)[0] for line in proc.stderr.splitlines() if line.startswith("  - ")]

    def assert_all_pass(self, proc: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.ids_with(proc, "FAIL"), [], proc.stdout)
        for check_id in CHECK_IDS:
            self.assertEqual(self.report_of(proc, check_id)[0], "PASS", check_id)
        self.assertRegex(proc.stdout, r"RESULT: OK -- all [56] checks passed")
        self.assertEqual(proc.stderr, "")

    def assert_only_failures(self, proc: subprocess.CompletedProcess[str], *expected: str) -> None:
        """Exit 1; exactly these checks FAIL, in order; every other check still PASSes; stderr lists them."""
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        failed = self.ids_with(proc, "FAIL")
        passed = self.ids_with(proc, "PASS")
        self.assertEqual(failed, list(expected), proc.stdout)
        self.assertTrue(set(CHECK_IDS) <= set(failed + passed), proc.stdout)
        self.assertEqual(self.listed_failures(proc), list(expected), proc.stderr)
        self.assertIn(f"RESULT: FAILED -- {len(failed)} of {len(failed) + len(passed)} checks failed:", proc.stderr)


class HappyPathTest(_Fixture):
    def test_every_check_passes_and_exits_0(self) -> None:
        proc = self.run_script()
        self.assert_all_pass(proc)
        self.assertIn("RESULT: OK -- all 5 checks passed", proc.stdout)
        self.assertEqual(self.report_of(proc, "signing-key"), ("PASS", f"user.signingkey={FAKE_FPR}! (pinned)"))
        self.assertEqual(self.report_of(proc, "commit-gpgsign"), ("PASS", "commit.gpgsign=true"))
        self.assertEqual(self.report_of(proc, "tag-gpgsign"), ("INFO", "tag.gpgsign=true"))
        self.assertIn(f"{self.pinentry} reports flavor 'mac' (pinentry-program in {self.agent_conf})", proc.stdout)
        self.assertIn(f"{self.socket_path} is a socket", proc.stdout)
        self.assertIn(f"no-allow-external-cache is set in {self.agent_conf}", proc.stdout)
        status, detail = self.report_of(proc, "head-signature")
        self.assertEqual(status, "INFO")
        self.assertRegex(detail, r"^HEAD [0-9a-f]{7,} %G\?=N: no signature$")
        self.assertIn("non-credential checks only", proc.stdout)

    def test_probe_sends_only_getinfo_flavor_and_bye(self) -> None:
        # GETINFO never prompts. A GETPIN or CONFIRM here would put a dialog in front of the owner.
        self.assert_all_pass(self.run_script())
        self.assertEqual(self.read_log("pinentry.log"), ["mac GETINFO flavor", "mac BYE"])

    def test_repo_option_from_outside_the_repository(self) -> None:
        proc = self.run_script("--repo", str(self.repo), cwd=self.elsewhere)
        self.assert_all_pass(proc)
        toplevel = self.git("-C", str(self.repo), "rev-parse", "--show-toplevel")
        self.assertIn(f"repo       {toplevel}\n", proc.stdout)


class HomedirTest(_Fixture):
    def test_gnupghome_wins_over_gpgconf(self) -> None:
        decoy = self.base / "decoy"
        decoy.mkdir()
        (decoy / "gpg-agent.conf").write_text("pinentry-program /nonexistent/pinentry-curses\n", encoding="utf-8")
        proc = self.run_script(STUB_GPGCONF_HOMEDIR=str(decoy))
        self.assert_all_pass(proc)
        self.assertIn(f"gnupghome  {self.gnupghome} (from GNUPGHOME)", proc.stdout)
        self.assertNotIn("--list-dirs homedir", self.read_log("gpgconf.log"))

    def test_gpgconf_names_the_homedir_when_gnupghome_is_unset(self) -> None:
        proc = self.run_script(unset=("GNUPGHOME",))
        self.assert_all_pass(proc)
        self.assertIn(f"gnupghome  {self.gnupghome} (from {self.gpgconf} --list-dirs homedir)", proc.stdout)
        self.assertIn("--list-dirs homedir", self.read_log("gpgconf.log"))


class SigningKeyTest(_Fixture):
    def test_r_b7a_signingkey_without_the_pin_fails(self) -> None:
        for key in (FAKE_FPR, FAKE_KEYID):
            with self.subTest(key):
                self.write_gitconfig(signingkey=key)
                proc = self.run_script()
                self.assert_only_failures(proc, "signing-key")
                detail = self.report_of(proc, "signing-key")[1]
                self.assertIn(f"user.signingkey={key} is not pinned", detail)
                self.assertIn("trailing '!'", detail)
                self.assertIn("R-B7a", detail)

    def test_r_b7a_unset_signingkey_fails(self) -> None:
        self.write_gitconfig(signingkey=None)
        proc = self.run_script()
        self.assert_only_failures(proc, "signing-key")
        self.assertIn("user.signingkey is unset", self.report_of(proc, "signing-key")[1])

    def test_repository_config_overrides_a_pinned_global_key(self) -> None:
        # The check reads the key a commit in this repository would use, not the global value alone.
        self.git("-C", str(self.repo), "config", "user.signingkey", FAKE_KEYID)
        proc = self.run_script()
        self.assert_only_failures(proc, "signing-key")
        self.assertIn(f"user.signingkey={FAKE_KEYID} is not pinned", proc.stdout)

    def test_pinned_key_forms_pass(self) -> None:
        # The 16-hex form is plan task B4's own target; the 40-hex form is yamaguchi's.
        for key in (f"{FAKE_KEYID}!", f"0x{FAKE_KEYID}!", f"{FAKE_FPR.lower()}!", "ab" * 32 + "!"):
            with self.subTest(key):
                self.write_gitconfig(signingkey=key)
                proc = self.run_script()
                self.assert_all_pass(proc)
                self.assertEqual(self.report_of(proc, "signing-key"), ("PASS", f"user.signingkey={key} (pinned)"))

    def test_malformed_pinned_values_fail(self) -> None:
        for key in ("!", "preflight@example.invalid!", "89ABCDEF!", f"{FAKE_FPR}!!", f"{FAKE_FPR[:-1]}!"):
            with self.subTest(key):
                self.write_gitconfig(signingkey=key)
                proc = self.run_script()
                self.assert_only_failures(proc, "signing-key")
                self.assertIn("16-hex key id or a 40- or 64-hex fingerprint", self.report_of(proc, "signing-key")[1])


class CommitGpgsignTest(_Fixture):
    def test_d11_override_fails_with_the_d11_message(self) -> None:
        proc = self.run_script(extra_env=D11_ENV)
        self.assert_only_failures(proc, "commit-gpgsign")
        detail = self.report_of(proc, "commit-gpgsign")[1]
        self.assertIn("signing disabled by construction (D11): GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false", detail)
        self.assertIn("cannot sign", detail)
        self.assertIn("signing disabled by construction (D11)", proc.stderr)
        status, tag = self.report_of(proc, "tag-gpgsign")
        self.assertEqual(status, "INFO")
        self.assertEqual(tag, "tag.gpgsign=false (disabled by construction, D11: GIT_CONFIG_KEY_1=tag.gpgsign, GIT_CONFIG_VALUE_1=false)")

    def test_d11_detection_follows_git(self) -> None:
        cases = {
            "key without case, value 'off'": ({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "Commit.GpgSign", "GIT_CONFIG_VALUE_0": "off"}, 1),
            "a later entry re-enables signing": ({"GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "commit.gpgsign", "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "commit.gpgsign", "GIT_CONFIG_VALUE_1": "true"}, 0),
            "an entry past the count does not apply": ({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "tag.gpgsign", "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "commit.gpgsign", "GIT_CONFIG_VALUE_1": "false"}, 0),
        }
        for label, (env, rc) in cases.items():
            with self.subTest(label):
                proc = self.run_script(extra_env=env)
                if rc == 0:
                    self.assert_all_pass(proc)
                else:
                    self.assert_only_failures(proc, "commit-gpgsign")
                    self.assertIn("signing disabled by construction (D11)", proc.stdout)

    def test_commit_gpgsign_not_true_fails_without_the_d11_message(self) -> None:
        for value, shown in (("false", "false"), (None, "unset"), ("maybe", "not a boolean")):
            with self.subTest(value):
                self.write_gitconfig(commit_gpgsign=value)
                proc = self.run_script()
                self.assert_only_failures(proc, "commit-gpgsign")
                detail = self.report_of(proc, "commit-gpgsign")[1]
                self.assertEqual(detail, f"commit.gpgsign is {shown}; it must be true (plan task B4)")
                self.assertNotIn("D11", detail)

    def test_tag_gpgsign_is_reported_not_checked(self) -> None:
        self.write_gitconfig(tag_gpgsign=None)
        proc = self.run_script()
        self.assert_all_pass(proc)
        self.assertEqual(self.report_of(proc, "tag-gpgsign"), ("INFO", "tag.gpgsign=unset"))


class PinentryTest(_Fixture):
    def use_conf_pinentry(self, prog: Path | str) -> None:
        self.write_agent_conf(f"pinentry-program {prog}", "no-allow-external-cache")

    def test_r_b7b_terminal_pinentries_fail(self) -> None:
        for flavor in ("curses", "tty", "emacs"):
            with self.subTest(flavor):
                prog = self.make_pinentry(f"pinentry-{flavor}", flavor)
                self.use_conf_pinentry(prog)
                proc = self.run_script()
                self.assert_only_failures(proc, "pinentry")
                detail = self.report_of(proc, "pinentry")[1]
                self.assertIn(f"{prog} (pinentry-program in {self.agent_conf}) is the '{flavor}' pinentry", detail)
                self.assertIn("R-B7b", detail)

    def test_gui_pinentries_pass(self) -> None:
        for flavor in ("mac", "qt", "gnome3", "gtk-2"):
            with self.subTest(flavor):
                prog = self.make_pinentry(f"pinentry-{flavor}", flavor)
                self.use_conf_pinentry(prog)
                proc = self.run_script()
                self.assert_all_pass(proc)
                self.assertIn(f"reports flavor '{flavor}'", self.report_of(proc, "pinentry")[1])

    def test_gui_build_that_falls_back_to_curses_fails(self) -> None:
        # pinentry-gtk-2 with no display reports "gtk-2:curses" and prompts on the terminal.
        prog = self.make_pinentry("pinentry-gtk-2", "gtk-2:curses")
        self.use_conf_pinentry(prog)
        proc = self.run_script()
        self.assert_only_failures(proc, "pinentry")
        self.assertIn("reports 'gtk-2:curses': this GUI build falls back to curses here", self.report_of(proc, "pinentry")[1])

    def test_r_b7b_missing_or_unusable_program_fails(self) -> None:
        not_executable = _write_exe(self.bin / "pinentry-noexec", pinentry_stub("mac"), mode=0o644)
        cases = {"missing": self.bin / "pinentry-absent", "not executable": not_executable, "a directory": self.bin}
        for label, prog in cases.items():
            with self.subTest(label):
                self.use_conf_pinentry(prog)
                proc = self.run_script()
                self.assert_only_failures(proc, "pinentry")
                self.assertIn(f"{prog} (pinentry-program in {self.agent_conf}) is missing or not executable", self.report_of(proc, "pinentry")[1])
        self.assertEqual(self.read_log("pinentry.log"), [], "a non-executable pinentry must not be run")

    def test_a_program_that_is_not_a_pinentry_fails(self) -> None:
        self.use_conf_pinentry(_write_exe(self.bin / "not-a-pinentry", NOT_A_PINENTRY))
        proc = self.run_script()
        self.assert_only_failures(proc, "pinentry")
        self.assertIn("reported no flavor", self.report_of(proc, "pinentry")[1])

    def test_a_hanging_pinentry_is_stopped_by_the_timeout(self) -> None:
        self.use_conf_pinentry(_write_exe(self.bin / "pinentry-hang", HANGING_PINENTRY))
        started = time.monotonic()
        proc = self.run_script("--timeout", "1")
        elapsed = time.monotonic() - started
        self.assert_only_failures(proc, "pinentry")
        self.assertIn("did not answer 'GETINFO flavor' within 1s", self.report_of(proc, "pinentry")[1])
        self.assertLess(elapsed, 10, "the probe must be killed at the timeout, not waited out")

    def test_pinentry_override_beats_the_configuration(self) -> None:
        self.use_conf_pinentry(self.make_pinentry("pinentry-curses", "curses"))
        gui = self.make_pinentry("pinentry-qt", "qt")
        proc = self.run_script(PINENTRY=str(gui))
        self.assert_all_pass(proc)
        self.assertEqual(self.report_of(proc, "pinentry")[1], f"{gui} reports flavor 'qt' (the PINENTRY override)")
        self.assertEqual(self.read_log("pinentry.log"), ["qt GETINFO flavor", "qt BYE"])

    def test_configuration_parsing(self) -> None:
        curses = self.make_pinentry("pinentry-curses", "curses")
        gui = self.make_pinentry("pinentry-gnome3", "gnome3")
        cases = {
            "the last active line wins; a comment does not count": [f"pinentry-program {curses}", f"pinentry-program {gui}", f"# pinentry-program {curses}", f"#pinentry-program {curses}", "no-allow-external-cache"],
            "indented, quoted, CRLF": [f'   pinentry-program   "{gui}"  \r', "no-allow-external-cache\r"],
        }
        for label, lines in cases.items():
            with self.subTest(label):
                self.write_agent_conf(*lines)
                proc = self.run_script()
                self.assert_all_pass(proc)
                self.assertEqual(self.report_of(proc, "pinentry")[1], f"{gui} reports flavor 'gnome3' (pinentry-program in {self.agent_conf})")

    def test_relative_pinentry_program_fails(self) -> None:
        # gpg-agent starts the program with execv: no PATH search, so a bare name never runs.
        self.use_conf_pinentry("pinentry-mac")
        proc = self.run_script()
        self.assert_only_failures(proc, "pinentry")
        self.assertIn("pinentry-program 'pinentry-mac'", self.report_of(proc, "pinentry")[1])
        self.assertIn("is not an absolute path", self.report_of(proc, "pinentry")[1])

    def test_unset_pinentry_program_uses_gnupgs_default_not_path(self) -> None:
        # A tripwire named pinentry leads PATH; tearDown fails the case if it ran.
        default = self.make_pinentry("pinentry-default", "gnome3")
        self.write_agent_conf("no-allow-external-cache")
        proc = self.run_script(STUB_GPGCONF_PINENTRY=str(default))
        self.assert_all_pass(proc)
        detail = self.report_of(proc, "pinentry")[1]
        self.assertEqual(detail, f"{default} reports flavor 'gnome3' (GnuPG's default from '{self.gpgconf} --list-components'; pinentry-program is unset)")
        self.assertIn("--list-components", self.read_log("gpgconf.log"))

    def test_unset_pinentry_program_without_a_default_fails(self) -> None:
        self.write_agent_conf("no-allow-external-cache")
        proc = self.run_script()
        self.assert_only_failures(proc, "pinentry")
        self.assertIn("names no default pinentry", self.report_of(proc, "pinentry")[1])


class AgentSocketTest(_Fixture):
    def test_missing_socket_fails(self) -> None:
        gone = self.base / "S.gpg-agent"
        proc = self.run_script(STUB_GPGCONF_SOCKET=str(gone))
        self.assert_only_failures(proc, "agent-socket")
        detail = self.report_of(proc, "agent-socket")[1]
        self.assertIn(f"no socket at {gone}: gpg-agent is not running", detail)
        self.assertIn("--launch gpg-agent", detail)

    def test_a_regular_file_is_not_a_socket(self) -> None:
        fake = self.base / "S.not-a-socket"
        fake.write_text("", encoding="utf-8")
        proc = self.run_script(STUB_GPGCONF_SOCKET=str(fake))
        self.assert_only_failures(proc, "agent-socket")
        self.assertIn(f"{fake} exists but is not a socket", self.report_of(proc, "agent-socket")[1])


class ExternalCacheTest(_Fixture):
    def test_missing_line_fails(self) -> None:
        self.write_agent_conf(f"pinentry-program {self.pinentry}")
        proc = self.run_script()
        self.assert_only_failures(proc, "external-cache")
        self.assertIn("has no no-allow-external-cache line", self.report_of(proc, "external-cache")[1])

    def test_commented_out_line_does_not_count(self) -> None:
        for comment in ("# no-allow-external-cache", "#no-allow-external-cache", "   # no-allow-external-cache"):
            with self.subTest(comment):
                self.write_agent_conf(f"pinentry-program {self.pinentry}", comment)
                proc = self.run_script()
                self.assert_only_failures(proc, "external-cache")
                self.assertIn("is commented out", self.report_of(proc, "external-cache")[1])

    def test_indented_line_counts(self) -> None:
        self.write_agent_conf(f"pinentry-program {self.pinentry}", "\t  no-allow-external-cache  ")
        self.assert_all_pass(self.run_script())

    def test_missing_gpg_agent_conf(self) -> None:
        # Without the file there is no cache line; the pinentry falls back to GnuPG's default.
        self.agent_conf.unlink()
        default = self.make_pinentry("pinentry-default", "mac")
        proc = self.run_script(STUB_GPGCONF_PINENTRY=str(default))
        self.assert_only_failures(proc, "external-cache")
        self.assertIn(f"no readable {self.agent_conf}", self.report_of(proc, "external-cache")[1])
        self.assertIn("pinentry-program is unset", self.report_of(proc, "pinentry")[1])


class HeadSignatureTest(_Fixture):
    def test_unsigned_head_is_informational(self) -> None:
        proc = self.run_script()
        self.assert_all_pass(proc)
        self.assertEqual(self.report_of(proc, "head-signature")[0], "INFO")
        self.assertEqual(self.read_log("gpg.log"), [], "an unsigned commit needs no verification")

    def test_require_signed_head_fails_an_unsigned_head(self) -> None:
        proc = self.run_script("--require-signed-head")
        self.assert_only_failures(proc, "head-signature")
        self.assertRegex(self.report_of(proc, "head-signature")[1], r"%G\?=N: no signature \(--require-signed-head needs G\)$")

    def test_require_signed_head_passes_a_good_signature(self) -> None:
        self.make_signed_head()
        proc = self.run_script("--require-signed-head")
        self.assert_all_pass(proc)
        self.assertIn("RESULT: OK -- all 6 checks passed", proc.stdout)
        status, detail = self.report_of(proc, "head-signature")
        self.assertEqual(status, "PASS")
        self.assertRegex(detail, rf"^HEAD [0-9a-f]{{7,}} %G\?=G: a good signature, key {FAKE_KEYID}$")
        self.assertEqual(len(self.read_log("gpg.log")), 1, "one verification, through git's gpg.program")

    def test_unverifiable_signature_is_reported_not_trusted(self) -> None:
        self.make_signed_head()
        proc = self.run_script(STUB_GPG_RESULT="errsig")
        self.assert_all_pass(proc)
        status, detail = self.report_of(proc, "head-signature")
        self.assertEqual(status, "INFO")
        self.assertIn("%G?=E: a signature that cannot be checked", detail)
        proc = self.run_script("--require-signed-head", STUB_GPG_RESULT="errsig")
        self.assert_only_failures(proc, "head-signature")

    def test_repository_without_commits(self) -> None:
        empty = self.base / "empty-repo"
        self.git("init", "-q", str(empty))
        proc = self.run_script("--repo", str(empty))
        self.assert_all_pass(proc)
        self.assertEqual(self.report_of(proc, "head-signature"), ("INFO", "HEAD has no commit to check"))
        proc = self.run_script("--repo", str(empty), "--require-signed-head")
        self.assert_only_failures(proc, "head-signature")


class AllFailuresListedTest(_Fixture):
    def test_every_failure_is_reported_and_listed(self) -> None:
        self.write_gitconfig(signingkey=FAKE_KEYID)
        self.write_agent_conf(f"pinentry-program {self.make_pinentry('pinentry-curses', 'curses')}")
        proc = self.run_script("--require-signed-head", extra_env=D11_ENV, STUB_GPGCONF_SOCKET=str(self.base / "gone"))
        expected = ["signing-key", "commit-gpgsign", "pinentry", "agent-socket", "external-cache", "head-signature"]
        self.assert_only_failures(proc, *expected)
        self.assertIn("RESULT: FAILED -- 6 of 6 checks failed:", proc.stderr)
        self.assertNotIn("RESULT: OK", proc.stdout)


class UsageAndEnvironmentTest(_Fixture):
    def test_help_exits_0_and_documents_d11_and_the_owner_run_card_checks(self) -> None:
        proc = self.run_script("--help", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Usage:", proc.stdout)
        text = " ".join(proc.stdout.split())
        self.assertIn('reports "signing disabled by construction (D11)" and FAILS (exit 1)', text)
        self.assertIn("GIT_CONFIG_KEY_n=commit.gpgsign and GIT_CONFIG_VALUE_n=false", text)
        self.assertIn("Owner-run, not implemented here (plan D11): the card checks of the original design, --card-timeout", text)
        self.assertIn("PATH is never searched", text)
        self.assertIn("Exit codes: 0 every check passed; 1 a check failed (all failures are listed); 2 usage or environment error", text)
        self.assertEqual(self.read_log("git.log"), [])
        self.assertEqual(self.read_log("gpgconf.log"), [])

    def test_bad_arguments_exit_2_before_any_tool_runs(self) -> None:
        cases = {
            "unknown option": ["--frobnicate"],
            "positional argument": ["extra"],
            "repo without value": ["--repo"],
            "timeout without value": ["--timeout"],
            "timeout not a number": ["--timeout", "abc"],
            "timeout zero": ["--timeout", "0"],
            "timeout negative": ["--timeout", "-1"],
            "timeout fractional": ["--timeout", "1.5"],
            "timeout too large": ["--timeout", "10000"],
            "card checks": ["--card-timeout", "15"],
            "card checks, joined": ["--card-timeout=15"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                proc = self.run_script(*argv, GIT=str(self.forbidden_git))
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn("ERROR:", proc.stderr)
                self.assertEqual(proc.stdout, "")
        self.assertEqual(self.read_log("git.log"), [], "argument errors must be caught before git runs")
        self.assertEqual(self.read_log("gpgconf.log"), [], "argument errors must be caught before gpgconf runs")

    def test_card_timeout_is_refused_as_owner_run(self) -> None:
        proc = self.run_script("--card-timeout", "15")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("card and PIN checks are owner-run (plan D11", proc.stderr)

    def test_missing_tools_exit_2(self) -> None:
        cases = {"git": ({"GIT": str(self.base / "no-such-git")}, "git not found"), "gpgconf": ({"GPGCONF": str(self.base / "no-such-gpgconf")}, "gpgconf not found")}
        for label, (env, message) in cases.items():
            with self.subTest(label):
                proc = self.run_script(extra_env=env)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(message, proc.stderr)

    def test_not_a_repository_exits_2(self) -> None:
        for label, (args, cwd) in {"cwd": ((), self.elsewhere), "--repo": (("--repo", str(self.base / "missing")), self.repo)}.items():
            with self.subTest(label):
                proc = self.run_script(*args, cwd=cwd)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("not a git repository", proc.stderr)
                self.assertEqual(self.read_log("gpgconf.log"), [])

    def test_gpgconf_failures_exit_2(self) -> None:
        cases = {
            "agent-socket query fails": ({"STUB_GPGCONF_FAIL": "1"}, (), "--list-dirs agent-socket' failed or printed nothing"),
            "homedir query fails": ({"STUB_GPGCONF_FAIL": "1"}, ("GNUPGHOME",), "--list-dirs homedir' failed or printed nothing"),
            "socket path empty": ({"STUB_GPGCONF_SOCKET": ""}, (), "--list-dirs agent-socket' failed or printed nothing"),
            "homedir empty": ({"STUB_GPGCONF_HOMEDIR": ""}, ("GNUPGHOME",), "--list-dirs homedir' failed or printed nothing"),
        }
        for label, (env, unset, message) in cases.items():
            with self.subTest(label):
                proc = self.run_script(unset=unset, extra_env=env)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(message, proc.stderr)


class SourceContractTest(unittest.TestCase):
    """Static pins. ``code`` excludes comment lines; ``text`` is the whole file, help text included."""

    text: str
    code: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.text.splitlines() if not line.lstrip().startswith("#"))

    def test_strict_mode_and_overridable_tools(self) -> None:
        self.assertTrue(self.text.startswith("#!/usr/bin/env bash\n"))
        self.assertIn("set -euo pipefail", self.code)
        self.assertIn('GIT="${GIT:-git}"', self.code)
        self.assertIn('GPGCONF="${GPGCONF:-gpgconf}"', self.code)
        self.assertIn('PINENTRY="${PINENTRY:-}"', self.code)

    def test_no_credential_operation_anywhere_in_the_file(self) -> None:
        # Plan D11: card and PIN checks are owner-run. The file must not run, or even spell, these.
        for token in ("--card-status", "--clearsign", "--detach-sign", "--list-secret-keys", "--pinentry-mode", "ssh-add", "ykman", "gpg-connect-agent", "private-keys-v1.d", "GETPIN", "learn --force"):
            with self.subTest(token):
                self.assertNotIn(token, self.text)
        self.assertIsNone(re.search(r"\bgpg2?\s+-K\b", self.text))

    def test_git_is_only_read(self) -> None:
        git_lines = [line for line in self.code.splitlines() if '"$GIT"' in line and "command -v" not in line]
        self.assertTrue(git_lines)
        for line in git_lines:
            with self.subTest(line.strip()):
                self.assertRegex(line, r'"\$GIT" -C "\$REPO" (rev-parse|config (--type=bool )?--get|--no-pager log -1 )')

    def test_no_key_id_literal(self) -> None:
        # The check is the pin, not a particular key: a hard-coded id goes stale at rotation (R-B8's class).
        self.assertIsNone(re.search(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{16,}(?![0-9A-Fa-f])", self.text))

    def test_bash_3_2_compatible(self) -> None:
        for construct in ("declare -A", "local -A", "mapfile", "readarray", ",,}", "^^}", "wait -n", "|&", "coproc", ";;&"):
            with self.subTest(construct):
                self.assertNotIn(construct, self.code)

    def test_no_host_specific_home_literal(self) -> None:
        self.assertNotRegex(self.text, r"/Users/|/home/", "use a $HOME-relative path (plan D12)")

    def test_bash_syntax(self) -> None:
        proc = subprocess.run(["/bin/bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_shellcheck_clean_when_available(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("shellcheck not installed (CI's pre-commit runs it)")
        # --severity=warning is the pre-commit gate's level. SC2218 is excluded because shellcheck
        # 0.11.0 raises it for helpers that ARE defined above their callers (0.10.0, the gate's
        # pinned version, does not); a real use-before-definition would fail every case above.
        proc = subprocess.run([shellcheck, "--severity=warning", "--exclude=SC2218", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
