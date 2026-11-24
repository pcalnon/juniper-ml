#!/usr/bin/env python3
"""Hermetic gate for util/juniper_repo_ssh_setup.bash (turing bring-up plan task A5).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The script provisions one repo's deploy key (``id_ed25519_github_juniper-<repo>``) and its
``github_juniper-<repo>`` Host block, prints the GitHub web-UI step that registers the key, and checks
the alias with ``ssh -G`` (``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``
task A5, decision D2, §13). The acceptance criterion: a second run is a no-op.

Hermetic by construction. ``HOME`` is a scratch home and every run passes ``--ssh-dir`` (the scratch
``$HOME/.ssh``, or a second scratch directory), so the real ``~/.ssh`` is never read or written.
``ssh-keygen`` is a stub that writes placeholder files, never key material, and answers ``-lf`` with a
fixed fingerprint. ``ssh`` is a stub that answers ``ssh [-F FILE] -G ALIAS`` from the alias's Host
block and refuses anything else. ``uname`` is a stub, so the Darwin and the Linux block are both tested
on either host. The candidate config must be a temp file in the ssh directory itself (``mv`` is atomic
only within one filesystem): the ssh log pins its path, and ``TMPDIR`` names a directory that does not
exist, so GNU ``mktemp`` without a template fails outright (macOS ``mktemp`` falls back to its per-user
temp directory instead). No test reads a private key's bytes, placeholder or real.

``RealToolsTest`` runs the real ``ssh-keygen`` and ``ssh -G -F`` against the second scratch directory
when they are installed. Its negative control shows why the block leaves UseKeychain out off Darwin
instead of carrying ``IgnoreUnknown UseKeychain``; it runs only where ssh does not know UseKeychain
(upstream OpenSSH, as on Linux CI), and skips on Apple's ssh.

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor).
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "juniper_repo_ssh_setup.bash"
TIMEOUT_SECONDS = 60

ALIAS = "github_juniper-k8s"
KEY_NAME = "id_ed25519_github_juniper-k8s"
STUB_FINGERPRINT = "256 SHA256:stub-fingerprint-for-tests Deploy Key - Turing (ED25519)"

# turing's existing block form (plan §2.4) with plan A8's AddKeysToAgent no. Written out byte for byte,
# so a bug in the block() helper cannot hide a bug in the script.
TURING_K8S_BLOCK = "Host github_juniper-k8s\n" "  HostName github.com\n" "  User git\n" "  IdentityFile ~/.ssh/id_ed25519_github_juniper-k8s\n" "  IdentitiesOnly yes\n" "  AddKeysToAgent no\n" "  UseKeychain yes\n"

# Content the script must carry over verbatim: other Host blocks (one still pre-A8), a Match block,
# tabs, a comment, and three names that only resemble the alias. It ends without a newline.
OTHER_CONTENT = "# Juniper per-repo deploy-key aliases\n" "Host *\n" "\tServerAliveInterval 60\n" "\n" "Host github_juniper-ml\n" "  HostName github.com\n" "  User git\n" "  IdentityFile ~/.ssh/id_ed25519_github_juniper-ml\n" "  IdentitiesOnly yes\n" "  AddKeysToAgent yes\n" "\n" "Match host example.org\n" "  User someone\n" "Host github_juniper-k8s-old xgithub_juniper-k8s\n" "  HostName example.invalid\n" "Host=github_juniper-k8\n" "  HostName example.invalid"

# ssh-keygen stub. Generation writes PLACEHOLDER files (never key material); -lf prints a fixed
# fingerprint. Every call is logged as one line of bracketed arguments, so empty ones show.
KEYGEN_STUB = """\
#!/bin/bash
{ for a in "$@"; do printf '[%s]' "$a"; done; printf '\\n'; } >> "$STUB_KEYGEN_LOG"
if [ "$1" = "-lf" ] && [ "$#" -eq 2 ]; then
    if [ "${STUB_KEYGEN_LF_FAIL:-0}" = "1" ] || [ ! -f "$2" ]; then
        echo "$2 is not a public key file." >&2
        exit 255
    fi
    echo "@FINGERPRINT@"
    exit 0
fi
path=""
comment=""
while [ "$#" -gt 0 ]; do
    [ "$#" -ge 2 ] || { echo "ssh-keygen stub: dangling argument: $1" >&2; exit 98; }
    case "$1" in
        -t | -N) ;;
        -C) comment="$2" ;;
        -f) path="$2" ;;
        *) echo "ssh-keygen stub: unexpected argument: $1" >&2; exit 98 ;;
    esac
    shift 2
done
if [ "${STUB_KEYGEN_FAIL:-0}" = "1" ] || [ -z "$path" ]; then
    echo "ssh-keygen stub: failure" >&2
    exit 1
fi
printf 'placeholder private key written by the test stub\\n' > "$path"
chmod "${STUB_KEYGEN_PRIV_MODE:-600}" "$path"
if [ "${STUB_KEYGEN_NO_PUB:-0}" != "1" ]; then
    printf 'ssh-ed25519 AAAA-placeholder-public-key %s\\n' "$comment" > "$path.pub"
    chmod "${STUB_KEYGEN_PUB_MODE:-644}" "$path.pub"
fi
echo "Your identification has been saved in $path"
""".replace("@FINGERPRINT@", STUB_FINGERPRINT)

# ssh stub: answers `ssh [-F FILE] -G ALIAS` only. It evaluates the first Host block naming ALIAS in
# FILE (default $HOME/.ssh/config): a small model of ssh -G with no patterns, Match or Include. Like
# Apple's ssh it writes a notice to stderr even on success. STUB_SSH_OUTPUT replaces the evaluation
# with a fixture; STUB_SSH_REJECT_USEKEYCHAIN plays an upstream OpenSSH, which rejects UseKeychain.
SSH_STUB = """\
#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_SSH_LOG"
cfg="$HOME/.ssh/config"
if [ "$1" = "-F" ] && [ "$#" -ge 2 ]; then
    cfg="$2"
    shift 2
fi
if [ "$1" != "-G" ] || [ "$#" -ne 2 ]; then
    echo "ssh stub: refusing argv: $*" >&2
    exit 99
fi
echo "Pseudo-terminal will not be allocated because stdin is not a terminal." >&2
if [ "${STUB_SSH_FAIL:-0}" = "1" ]; then
    echo "ssh: stub failure" >&2
    exit 255
fi
if [ -n "${STUB_SSH_OUTPUT:-}" ]; then
    cat "$STUB_SSH_OUTPUT"
    exit 0
fi
[ -f "$cfg" ] || cfg=/dev/null
if [ "${STUB_SSH_REJECT_USEKEYCHAIN:-0}" = "1" ] && grep -qi '^[[:space:]]*usekeychain' "$cfg"; then
    echo "$cfg: line 7: Bad configuration option: usekeychain" >&2
    echo "$cfg: terminating, 1 bad configuration options" >&2
    exit 255
fi
awk -v alias="$2" '
    { s = $0; sub(/^[ \\t]+/, "", s) }
    s == "" || substr(s, 1, 1) == "#" { next }
    { kw = s; sub(/[ \\t=].*$/, "", kw); kw = tolower(kw); val = substr(s, length(kw) + 1); sub(/^[ \\t]*=?[ \\t]*/, "", val) }
    kw == "host" { active = 0; n = split(val, p, "[ \\t]+"); for (i = 1; i <= n; i++) if (p[i] == alias) active = 1; next }
    kw == "match" { active = 0; next }
    !active { next }
    kw == "hostname" && hostname == "" { hostname = val }
    kw == "identitiesonly" && only == "" { only = val }
    kw == "identityfile" { ids[++n_ids] = val }
    END {
        print "host " alias
        print "user git"
        print "hostname " (hostname == "" ? alias : hostname)
        print "identitiesonly " (only == "" ? "no" : only)
        if (n_ids == 0) { print "identityfile ~/.ssh/id_rsa"; print "identityfile ~/.ssh/id_ed25519" }
        for (i = 1; i <= n_ids; i++) print "identityfile " ids[i]
    }
' "$cfg"
"""

UNAME_STUB = """\
#!/bin/bash
case "$*" in
    -s) printf '%s\\n' "${STUB_UNAME_S-Darwin}" ;;
    -n) printf '%s\\n' "${STUB_UNAME_N-turing.midcoip.net}" ;;
    *) echo "uname stub: refusing argv: $*" >&2; exit 99 ;;
esac
"""

# A tool that must never run: --dry-run and every refusal happen before it would be called.
FORBIDDEN_TOOL = """\
#!/bin/bash
printf '%s %s\\n' "$0" "$*" >> "$STUB_FORBIDDEN_LOG"
exit 97
"""

REAL_SSH = shutil.which("ssh")
REAL_KEYGEN = shutil.which("ssh-keygen")
REAL_UNAME = shutil.which("uname")


def _write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def block(identity: str = "~/.ssh/" + KEY_NAME, *, darwin: bool = True, full: str = "juniper-k8s") -> str:
    lines = [f"Host github_{full}", "  HostName github.com", "  User git", f"  IdentityFile {identity}", "  IdentitiesOnly yes", "  AddKeysToAgent no"]
    if darwin:
        lines.append("  UseKeychain yes")
    return "\n".join(lines) + "\n"


class _Fixture(unittest.TestCase):
    """A scratch HOME with an empty $HOME/.ssh, a second ssh directory, and stub ssh-keygen, ssh, uname."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.home = self.base / "home"
        self.ssh_dir = self.home / ".ssh"  # == $HOME/.ssh: IdentityFile ~/.ssh/..., ssh -G without -F
        self.alt_dir = self.base / "alt-ssh"  # any other directory: absolute IdentityFile, ssh -F
        self.bin = self.base / "bin"
        for d in (self.home, self.ssh_dir, self.alt_dir, self.bin):
            d.mkdir(mode=0o700)
        self.keygen_log = self.base / "keygen.log"
        self.ssh_log = self.base / "ssh.log"
        self.forbidden_log = self.base / "forbidden.log"
        self.keygen_stub = _write_exe(self.bin / "ssh-keygen-stub", KEYGEN_STUB)
        self.ssh_stub = _write_exe(self.bin / "ssh-stub", SSH_STUB)
        self.uname_stub = _write_exe(self.bin / "uname-stub", UNAME_STUB)
        self.forbidden = str(_write_exe(self.bin / "forbidden-tool", FORBIDDEN_TOOL))
        self.env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "SSH", "STUB_", "UNAME"))})
        self.env.update(
            HOME=str(self.home),
            TMPDIR=str(self.base / "no-such-tmpdir"),
            SSH_KEYGEN=str(self.keygen_stub),
            SSH=str(self.ssh_stub),
            UNAME=str(self.uname_stub),
            STUB_KEYGEN_LOG=str(self.keygen_log),
            STUB_SSH_LOG=str(self.ssh_log),
            STUB_FORBIDDEN_LOG=str(self.forbidden_log),
        )

    def tearDown(self) -> None:
        for d in (self.ssh_dir, self.alt_dir):
            if d.is_dir():
                d.chmod(0o700)  # a test may leave one unwritable
        self._tmp.cleanup()

    def run_script(self, *args: str, **overrides: str) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env.update(overrides)
        return self.run_with_env(env, *args)

    def run_with_env(self, env: RedactedEnv, *args: str) -> subprocess.CompletedProcess[str]:
        home = env.get("HOME")
        self.assertTrue(home is None or home.startswith(str(self.base)), "a test must never run with the real HOME")
        return subprocess.run(["/bin/bash", str(SCRIPT_PATH), *args], cwd=self.base, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def run_setup(self, *args: str, ssh_dir: Path | None = None, repo: str = "k8s", **overrides: str) -> subprocess.CompletedProcess[str]:
        return self.run_script("--ssh-dir", str(ssh_dir or self.ssh_dir), *args, repo, **overrides)

    def key(self, d: Path | None = None) -> Path:
        return (d or self.ssh_dir) / KEY_NAME

    def pub(self, d: Path | None = None) -> Path:
        return (d or self.ssh_dir) / f"{KEY_NAME}.pub"

    def config(self, d: Path | None = None) -> Path:
        return (d or self.ssh_dir) / "config"

    def write_config(self, text: str, d: Path | None = None, file_mode: int = 0o600) -> Path:
        cfg = self.config(d)
        cfg.write_bytes(text.encode("utf-8"))
        cfg.chmod(file_mode)
        return cfg

    def make_key(self, d: Path | None = None, *, key_mode: int = 0o600, pub_mode: int | None = 0o644) -> None:
        """A placeholder pair, as an earlier run (or turing's 2026-05-07 setup) would have left it."""
        key = self.key(d)
        key.write_text("placeholder private key written by the test\n", encoding="utf-8")
        key.chmod(key_mode)
        if pub_mode is not None:
            pub = self.pub(d)
            pub.write_text("ssh-ed25519 AAAA-placeholder-public-key Deploy Key - Turing\n", encoding="utf-8")
            pub.chmod(pub_mode)

    def configured(self, d: Path | None = None) -> None:
        self.write_config(TURING_K8S_BLOCK if d is None else block(str(self.key(d))), d)
        self.make_key(d)

    def snapshot(self, d: Path) -> dict[str, tuple[int, int, int, int]]:
        """Mode, size, mtime and inode of every entry (lstat). Contents are compared separately, and a key's never."""
        snap = {}
        for p in sorted(d.iterdir()):
            st = p.lstat()
            snap[p.name] = (stat.S_IMODE(st.st_mode), st.st_size, st.st_mtime_ns, st.st_ino)
        return snap

    def reset(self) -> None:
        for d in (self.ssh_dir, self.alt_dir):
            d.chmod(0o700)
            for p in d.iterdir():
                if p.is_dir() and not p.is_symlink():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        for log in (self.keygen_log, self.ssh_log, self.forbidden_log):
            log.unlink(missing_ok=True)

    def keygen_calls(self) -> list[list[str]]:
        if not self.keygen_log.exists():
            return []
        return [re.findall(r"\[([^\]]*)\]", line) for line in self.keygen_log.read_text(encoding="utf-8").splitlines()]

    def ssh_calls(self) -> list[str]:
        if not self.ssh_log.exists():
            return []
        return self.ssh_log.read_text(encoding="utf-8").splitlines()

    def forbidden_never_ran(self) -> bool:
        return not self.forbidden_log.exists()

    def temp_files(self, d: Path) -> list[str]:
        return [p.name for p in d.iterdir() if p.name.startswith(".config.")]


class CreateTest(_Fixture):
    def test_fresh_run_creates_the_key_and_the_canonical_block(self) -> None:
        self.assertEqual(block(), TURING_K8S_BLOCK, "the block() helper must agree with the literal")
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(mode(self.key()), 0o600)
        self.assertEqual(mode(self.pub()), 0o644)
        self.assertEqual(self.config().read_text(encoding="utf-8"), TURING_K8S_BLOCK)
        self.assertEqual(mode(self.config()), 0o600)
        self.assertEqual(sorted(p.name for p in self.ssh_dir.iterdir()), sorted([KEY_NAME, f"{KEY_NAME}.pub", "config"]), "no temp file may survive")
        self.assertIn("OK: juniper-k8s configured (created: key, Host block).", proc.stdout)

    def test_keygen_gets_the_exact_argv_and_only_the_pub_is_fingerprinted(self) -> None:
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(
            self.keygen_calls(),
            [["-t", "ed25519", "-N", "", "-C", "Deploy Key - Turing", "-f", str(self.key())], ["-lf", str(self.pub())]],
        )

    def test_ssh_only_evaluates_configuration(self) -> None:
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        calls = self.ssh_calls()
        self.assertEqual(len(calls), 2, calls)
        # The candidate file is evaluated before it replaces the config; then the default directory is
        # checked the way ssh itself reads it, without -F.
        self.assertRegex(calls[0], rf"^-F {re.escape(str(self.ssh_dir))}/\.config\.juniper_repo_ssh_setup\.\w+ -G {ALIAS}$")
        self.assertEqual(calls[1], f"-G {ALIAS}")

    def test_owner_web_ui_step_is_printed(self) -> None:
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for text in (
            "https://github.com/pcalnon/juniper-k8s/settings/keys/new",
            "Title  Deploy Key - Turing",
            '"Allow write access"',
            f"Fingerprint (must equal the one GitHub lists): {STUB_FINGERPRINT}",
            f"paste the contents of {self.pub()}",
        ):
            self.assertIn(text, proc.stdout)
        warning = [line for line in proc.stdout.splitlines() if "gh repo deploy-key add" in line]
        self.assertEqual(len(warning), 1, proc.stdout)
        self.assertTrue(warning[0].lstrip().startswith("Never use"), warning[0])
        self.assertIn("deleted when that token is revoked", proc.stdout)

    def test_new_key_modes_are_set_whatever_keygen_leaves(self) -> None:
        proc = self.run_setup(STUB_KEYGEN_PRIV_MODE="644", STUB_KEYGEN_PUB_MODE="600")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(mode(self.key()), 0o600)
        self.assertEqual(mode(self.pub()), 0o644)

    def test_full_repo_name_is_accepted(self) -> None:
        proc = self.run_setup(repo="juniper-k8s")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.config().read_text(encoding="utf-8"), TURING_K8S_BLOCK)

    def test_title_is_the_capitalized_short_hostname_unless_given(self) -> None:
        cases = {
            "fully qualified": ([], "hopper.example.org", "Deploy Key - Hopper"),
            "bare": ([], "turing", "Deploy Key - Turing"),
            "--title": (["--title", "Deploy Key - Lab 2"], "turing.midcoip.net", "Deploy Key - Lab 2"),
        }
        for label, (args, hostname, title) in cases.items():
            with self.subTest(label):
                self.reset()
                proc = self.run_setup(*args, STUB_UNAME_N=hostname)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(self.keygen_calls()[0][5], title)
                self.assertIn(f"Title  {title}", proc.stdout)

    def test_owner_option_shapes_the_url(self) -> None:
        proc = self.run_setup("--owner", "someone-else")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("https://github.com/someone-else/juniper-k8s/settings/keys/new", proc.stdout)


class IdempotencyTest(_Fixture):
    def assert_second_run_is_a_noop(self, ssh_dir: Path, expected_check: str) -> None:
        first = self.run_setup(ssh_dir=ssh_dir)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = self.snapshot(ssh_dir)
        config_bytes = self.config(ssh_dir).read_bytes()
        self.keygen_log.unlink()
        self.ssh_log.unlink()
        second = self.run_setup(ssh_dir=ssh_dir)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("OK: juniper-k8s already configured; nothing written.", second.stdout)
        self.assertEqual(self.config(ssh_dir).read_bytes(), config_bytes)
        self.assertEqual(self.snapshot(ssh_dir), before, "mode, size, mtime and inode of every file, and no new file")
        self.assertEqual(self.keygen_calls(), [["-lf", str(self.pub(ssh_dir))]], "the second run only fingerprints the .pub")
        self.assertEqual(self.ssh_calls(), [expected_check])

    def test_second_run_is_a_noop(self) -> None:
        self.assert_second_run_is_a_noop(self.ssh_dir, f"-G {ALIAS}")

    def test_second_run_is_a_noop_in_another_ssh_dir(self) -> None:
        self.assert_second_run_is_a_noop(self.alt_dir, f"-F {self.config(self.alt_dir)} -G {ALIAS}")

    def test_existing_compliant_block_and_key_are_left_alone(self) -> None:
        cfg = self.write_config(OTHER_CONTENT + "\n\n" + TURING_K8S_BLOCK + "\n# next\nHost after\n  HostName example.invalid\n")
        self.make_key()
        config_bytes = cfg.read_bytes()
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("block present and canonical -- left untouched", proc.stdout)
        self.assertIn("OK: juniper-k8s already configured; nothing written.", proc.stdout)
        self.assertEqual(cfg.read_bytes(), config_bytes)
        self.assertEqual(self.snapshot(self.ssh_dir), before)

    def test_compliant_block_without_a_key_creates_only_the_key(self) -> None:
        cfg = self.write_config(TURING_K8S_BLOCK)
        before = cfg.lstat()
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK: juniper-k8s configured (created: key).", proc.stdout)
        self.assertEqual(cfg.read_text(encoding="utf-8"), TURING_K8S_BLOCK)
        self.assertEqual((cfg.lstat().st_ino, cfg.lstat().st_mtime_ns), (before.st_ino, before.st_mtime_ns))
        self.assertEqual((mode(self.key()), mode(self.pub())), (0o600, 0o644))
        self.assertEqual(self.ssh_calls(), [f"-G {ALIAS}"], "nothing was appended, so there is no candidate to check")


class NonCompliantTest(_Fixture):
    """Non-compliant existing state is reported (exit 1), never fixed, and nothing at all is written."""

    def assert_reported_and_untouched(self, proc: subprocess.CompletedProcess[str], before: dict[str, tuple[int, int, int, int]], *messages: str) -> None:
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for message in messages:
            self.assertIn(message, proc.stderr)
        self.assertIn("nothing was written", proc.stderr)
        self.assertEqual(self.snapshot(self.ssh_dir), before)
        self.assertNotIn("OK:", proc.stdout)

    def test_turings_pre_a8_block_is_reported_with_a_diff(self) -> None:
        cfg = self.write_config(OTHER_CONTENT + "\n\n" + TURING_K8S_BLOCK.replace("AddKeysToAgent no", "AddKeysToAgent yes"))
        config_bytes = cfg.read_bytes()
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, "is not the canonical form", "-  AddKeysToAgent no\n", "+  AddKeysToAgent yes\n")
        self.assertEqual(cfg.read_bytes(), config_bytes)
        self.assertTrue(self.forbidden_never_ran(), "no key is created and ssh is not consulted")

    def test_duplicate_blocks_are_reported(self) -> None:
        self.write_config(TURING_K8S_BLOCK + "\n" + TURING_K8S_BLOCK)
        self.make_key()
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, f"has 2 Host blocks naming {ALIAS}")

    def test_a_multi_pattern_host_line_is_an_existing_block(self) -> None:
        self.write_config(TURING_K8S_BLOCK.replace("Host github_juniper-k8s", "Host github_juniper-ml github_juniper-k8s"))
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, "+Host github_juniper-ml github_juniper-k8s\n")

    def test_existing_key_not_at_600_is_reported_not_fixed(self) -> None:
        self.make_key(key_mode=0o644)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, f"{self.key()} is not mode 600", f"Fix: chmod 600 '{self.key()}'")
        self.assertEqual(mode(self.key()), 0o644)
        self.assertFalse(self.config().exists(), "the block is not appended either")

    def test_existing_pub_not_at_644_is_reported_not_fixed(self) -> None:
        self.make_key(pub_mode=0o666)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, f"Fix: chmod 644 '{self.pub()}'")
        self.assertEqual(mode(self.pub()), 0o666)

    def test_key_without_its_pub_is_not_regenerated(self) -> None:
        self.make_key(pub_mode=None)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, f"{self.pub()} is missing", "Not regenerating it")
        self.assertFalse(self.pub().exists())
        self.assertTrue(self.forbidden_never_ran())

    def test_pub_without_its_key_is_not_overwritten(self) -> None:
        self.pub().write_text("ssh-ed25519 AAAA-placeholder-registered-key old\n", encoding="utf-8")
        self.pub().chmod(0o644)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, "exists without its key")
        self.assertEqual(self.pub().read_text(encoding="utf-8"), "ssh-ed25519 AAAA-placeholder-registered-key old\n")

    def test_a_symlinked_key_is_reported(self) -> None:
        target = self.base / "key-elsewhere"
        target.write_text("placeholder private key written by the test\n", encoding="utf-8")
        target.chmod(0o600)
        self.key().symlink_to(target)
        self.pub().write_text("ssh-ed25519 AAAA-placeholder-public-key x\n", encoding="utf-8")
        self.pub().chmod(0o644)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, "is a symlink")

    def test_an_unreadable_existing_pub_stops_the_run_before_any_write(self) -> None:
        self.make_key()  # no config: the run would otherwise write one
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(STUB_KEYGEN_LF_FAIL="1", SSH=self.forbidden)
        self.assert_reported_and_untouched(proc, before, "is not a public key ssh-keygen can read")
        self.assertFalse(self.config().exists())


class ConfigPreservationTest(_Fixture):
    def test_existing_content_is_kept_byte_for_byte(self) -> None:
        cases = {
            "no trailing newline": (OTHER_CONTENT, "\n\n"),
            "trailing newline": (OTHER_CONTENT + "\n", "\n"),
            "trailing blank line": (OTHER_CONTENT + "\n\n", ""),
            "empty file": ("", ""),
        }
        for label, (prefix, separator) in cases.items():
            with self.subTest(label):
                self.reset()
                cfg = self.write_config(prefix)
                inode = cfg.lstat().st_ino
                proc = self.run_setup()
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(cfg.read_bytes(), (prefix + separator + TURING_K8S_BLOCK).encode("utf-8"))
                self.assertEqual(mode(cfg), 0o600)
                self.assertNotEqual(cfg.lstat().st_ino, inode, "the config is replaced by rename (temp file + mv), never rewritten in place")
                self.assertEqual(self.temp_files(self.ssh_dir), [])

    def test_a_644_config_is_rewritten_at_600_and_says_so(self) -> None:
        cfg = self.write_config(OTHER_CONTENT + "\n", file_mode=0o644)
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(mode(cfg), 0o600)
        self.assertIn("it was not mode 600 before", proc.stdout)

    def test_a_symlinked_config_is_never_replaced(self) -> None:
        target = self.base / "dotfiles-ssh-config"
        target.write_text(OTHER_CONTENT + "\n", encoding="utf-8")
        target.chmod(0o600)
        self.config().symlink_to(target)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("Append this block to its target by hand", proc.stderr)
        self.assertIn(TURING_K8S_BLOCK, proc.stderr)
        self.assertTrue(self.config().is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), OTHER_CONTENT + "\n")
        self.assertFalse(self.key().exists())
        self.assertTrue(self.forbidden_never_ran())

    def test_a_symlinked_config_that_is_already_compliant_is_only_read(self) -> None:
        target = self.base / "dotfiles-ssh-config"
        target.write_text(TURING_K8S_BLOCK, encoding="utf-8")
        target.chmod(0o600)
        self.config().symlink_to(target)
        self.make_key()
        proc = self.run_setup()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("already configured", proc.stdout)
        self.assertTrue(self.config().is_symlink())

    @unittest.skipIf(os.geteuid() == 0, "root ignores file modes")
    def test_a_read_only_config_is_not_replaced(self) -> None:
        cfg = self.write_config(OTHER_CONTENT + "\n", file_mode=0o400)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("is read-only", proc.stderr)
        self.assertEqual((cfg.read_text(encoding="utf-8"), mode(cfg)), (OTHER_CONTENT + "\n", 0o400))
        self.assertTrue(self.forbidden_never_ran())


class UseKeychainPortabilityTest(_Fixture):
    """UseKeychain is written on Darwin only. The script header gives the reason it is not IgnoreUnknown."""

    def test_darwin_block_carries_usekeychain(self) -> None:
        proc = self.run_setup(STUB_UNAME_S="Darwin")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = self.config().read_text(encoding="utf-8")
        self.assertEqual(text, TURING_K8S_BLOCK)
        self.assertNotIn("IgnoreUnknown", text)

    def test_linux_block_has_neither_usekeychain_nor_ignoreunknown(self) -> None:
        proc = self.run_setup(STUB_UNAME_S="Linux")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = self.config().read_text(encoding="utf-8")
        self.assertEqual(text, block(darwin=False))
        self.assertNotIn("UseKeychain", text)
        self.assertNotIn("IgnoreUnknown", text)

    def test_a_darwin_block_is_not_canonical_on_linux(self) -> None:
        self.configured()
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(STUB_UNAME_S="Linux", SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("+  UseKeychain yes\n", proc.stderr)
        self.assertEqual(self.snapshot(self.ssh_dir), before)

    def test_a_config_this_ssh_cannot_parse_is_never_installed(self) -> None:
        # A Darwin host whose ssh is upstream OpenSSH (Homebrew's openssh, say) rejects UseKeychain.
        prefix = "Host github_juniper-ml\n  HostName github.com\n"
        cfg = self.write_config(prefix)
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup(STUB_UNAME_S="Darwin", STUB_SSH_REJECT_USEKEYCHAIN="1")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("Bad configuration option: usekeychain", proc.stderr)
        self.assertIn("left unchanged, no key created", proc.stderr)
        self.assertEqual(cfg.read_text(encoding="utf-8"), prefix)
        self.assertEqual(self.snapshot(self.ssh_dir), before, "no key, no temp file, config untouched")


class VerifyTest(_Fixture):
    def ssh_output(self, *lines: str) -> str:
        fixture = self.base / "ssh-G-output"
        fixture.write_text("\n".join([f"host {ALIAS}", *lines]) + "\n", encoding="utf-8")
        return str(fixture)

    def test_another_ssh_dir_gets_an_absolute_identity_and_ssh_dash_F(self) -> None:
        proc = self.run_setup(ssh_dir=self.alt_dir)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.config(self.alt_dir).read_text(encoding="utf-8"), block(str(self.key(self.alt_dir))))
        calls = self.ssh_calls()
        self.assertEqual(len(calls), 2, calls)
        self.assertRegex(calls[0], rf"^-F {re.escape(str(self.alt_dir))}/\.config\.juniper_repo_ssh_setup\.\w+ -G {ALIAS}$")
        self.assertEqual(calls[1], f"-F {self.config(self.alt_dir)} -G {ALIAS}")
        self.assertEqual(list(self.ssh_dir.iterdir()), [], "the default directory is not touched")

    def test_existing_state_that_resolves_elsewhere_exits_1(self) -> None:
        ours = f"identityfile ~/.ssh/{KEY_NAME}"
        cases = {
            "hostname": (["hostname gitlab.com", "identitiesonly yes", ours], "resolves hostname 'gitlab.com', not github.com"),
            "identitiesonly": (["hostname github.com", "identitiesonly no", ours], "resolves identitiesonly 'no', not yes"),
            "an earlier identity": (["hostname github.com", "identitiesonly yes", "identityfile ~/.ssh/id_other", ours], f"resolves identityfile [~/.ssh/id_other,~/.ssh/{KEY_NAME}], not exactly"),
            "only the defaults": (["hostname github.com", "identitiesonly yes", "identityfile ~/.ssh/id_rsa"], "resolves identityfile [~/.ssh/id_rsa], not exactly"),
        }
        self.configured()
        before = self.snapshot(self.ssh_dir)
        for label, (lines, message) in cases.items():
            with self.subTest(label):
                proc = self.run_setup(STUB_SSH_OUTPUT=self.ssh_output(*lines))
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn(f"MISMATCH: ssh -G {ALIAS} {message}", proc.stderr)
                self.assertNotIn("OK:", proc.stdout)
                self.assertEqual(self.snapshot(self.ssh_dir), before)

    def test_a_candidate_that_resolves_elsewhere_is_never_installed(self) -> None:
        proc = self.run_setup(STUB_SSH_OUTPUT=self.ssh_output("hostname gitlab.com", "identitiesonly yes", f"identityfile ~/.ssh/{KEY_NAME}"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("left unchanged, no key created", proc.stderr)
        self.assertEqual(list(self.ssh_dir.iterdir()), [], "no key, no config, no temp file")
        self.assertEqual(self.keygen_calls(), [])

    def test_ssh_that_cannot_evaluate_the_configuration_exits_2(self) -> None:
        with self.subTest("existing state"):
            self.configured()
            before = self.snapshot(self.ssh_dir)
            proc = self.run_setup(STUB_SSH_FAIL="1")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("ssh cannot evaluate the configuration", proc.stderr)
            self.assertIn("ssh: stub failure", proc.stderr)
            self.assertEqual(self.snapshot(self.ssh_dir), before)
        with self.subTest("fresh"):
            self.reset()
            proc = self.run_setup(STUB_SSH_FAIL="1")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(list(self.ssh_dir.iterdir()), [])

    def test_an_ssh_dir_whose_path_needs_quoting_exits_2(self) -> None:
        spaced = self.base / "alt ssh"
        spaced.mkdir(mode=0o700)
        proc = self.run_setup(ssh_dir=spaced, SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("would need quoting in ssh_config", proc.stderr)
        self.assertEqual(list(spaced.iterdir()), [])
        self.assertTrue(self.forbidden_never_ran())


class DryRunTest(_Fixture):
    def test_dry_run_writes_nothing_and_runs_neither_keygen_nor_ssh(self) -> None:
        proc = self.run_setup("--dry-run", SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"DRY-RUN: would run: {self.forbidden} -t ed25519 -N '' -C 'Deploy Key - Turing' -f '{self.key()}'", proc.stdout)
        self.assertIn(TURING_K8S_BLOCK, proc.stdout)
        self.assertIn(f"DRY-RUN: would check: {self.forbidden} -G {ALIAS}", proc.stdout)
        self.assertIn("(nothing written)", proc.stdout)
        self.assertEqual(list(self.ssh_dir.iterdir()), [])
        self.assertTrue(self.forbidden_never_ran())

    def test_dry_run_on_a_configured_host(self) -> None:
        self.configured()
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup("--dry-run", SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("DRY-RUN: juniper-k8s already configured; nothing to write", proc.stdout)
        self.assertEqual(self.snapshot(self.ssh_dir), before)
        self.assertTrue(self.forbidden_never_ran())

    def test_dry_run_reports_noncompliance(self) -> None:
        self.write_config(TURING_K8S_BLOCK.replace("AddKeysToAgent no", "AddKeysToAgent yes"))
        before = self.snapshot(self.ssh_dir)
        proc = self.run_setup("--dry-run", SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(self.ssh_dir), before)
        self.assertTrue(self.forbidden_never_ran())


class UsageTest(_Fixture):
    def all_forbidden(self) -> dict[str, str]:
        return {"SSH_KEYGEN": self.forbidden, "SSH": self.forbidden, "UNAME": self.forbidden}

    def test_help_exits_0(self) -> None:
        proc = self.run_script("--help", **self.all_forbidden())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Usage:", proc.stdout)
        self.assertTrue(self.forbidden_never_ran())

    def test_bad_arguments_exit_2_before_any_tool_runs(self) -> None:
        cases = {
            "no repo": [],
            "unknown option": ["--frobnicate", "k8s"],
            "two repos": ["k8s", "ml"],
            "owner without value": ["k8s", "--owner"],
            "title without value": ["k8s", "--title"],
            "empty title": ["--title", "", "k8s"],
            "ssh-dir without value": ["k8s", "--ssh-dir"],
            "path traversal": ["../evil"],
            "slash": ["k8s/x"],
            "uppercase": ["K8s"],
            "shell syntax": ["k8s;id"],
            "empty short name": ["juniper-"],
            "leading dash": ["-k8s"],
            "bad owner": ["--owner", "a/b", "k8s"],
            "title with a quote": ["--title", 'Deploy "Key"', "k8s"],
            "title with a newline": ["--title", "Deploy\nKey", "k8s"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                proc = self.run_script("--ssh-dir", str(self.ssh_dir), *argv, **self.all_forbidden())
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn("ERROR:", proc.stderr)
        self.assertTrue(self.forbidden_never_ran(), "argument errors are caught before any tool runs")
        self.assertEqual(list(self.ssh_dir.iterdir()), [])

    def test_environment_errors_exit_2(self) -> None:
        a_file = self.base / "a-file"
        a_file.write_text("not a directory\n", encoding="utf-8")
        cases = {
            "ssh-keygen missing": ([], {"SSH_KEYGEN": str(self.base / "no-such-ssh-keygen")}, "required tool not found"),
            "ssh missing": ([], {"SSH": str(self.base / "no-such-ssh")}, "required tool not found"),
            "uname missing": ([], {"UNAME": str(self.base / "no-such-uname")}, "required tool not found"),
            "empty hostname": ([], {"STUB_UNAME_N": ""}, "cannot derive a key title"),
            "unusable hostname": ([], {"STUB_UNAME_N": "bad_name!.example.org"}, "cannot derive a key title"),
            "ssh dir missing": (["--ssh-dir", str(self.base / "no-such-dir")], {}, "mkdir -m 700"),
            "ssh dir is a file": (["--ssh-dir", str(a_file)], {}, "not a directory"),
            "keygen fails": ([], {"STUB_KEYGEN_FAIL": "1"}, "failed; "),
            "keygen leaves no .pub": ([], {"STUB_KEYGEN_NO_PUB": "1"}, "did not leave both"),
        }
        for label, (args, env, message) in cases.items():
            with self.subTest(label):
                self.reset()
                proc = self.run_script(*(args or ["--ssh-dir", str(self.ssh_dir)]), "k8s", **env)
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn(message, proc.stderr)
                self.assertFalse(self.config().exists(), "the config is never installed")
                self.assertEqual(self.temp_files(self.ssh_dir), [])

    def test_home_unset_without_ssh_dir_exits_2(self) -> None:
        env = self.env.copy()
        del env["HOME"]
        proc = self.run_with_env(env, "k8s")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("HOME is not set", proc.stderr)

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory modes")
    def test_an_unwritable_ssh_dir_exits_2(self) -> None:
        self.ssh_dir.chmod(0o500)
        proc = self.run_setup(SSH_KEYGEN=self.forbidden, SSH=self.forbidden)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("ssh directory is not writable", proc.stderr)
        self.assertTrue(self.forbidden_never_ran())


@unittest.skipUnless(REAL_SSH and REAL_KEYGEN and REAL_UNAME, "the real ssh, ssh-keygen and uname are not all installed")
class RealToolsTest(_Fixture):
    """The real ssh-keygen and `ssh -G -F`, in the second scratch directory only.

    That directory is not $HOME/.ssh, so every ssh call carries -F and the real ~/.ssh/config is never
    consulted (ssh resolves ~ from the password database, not $HOME, so the scratch HOME would not be
    enough on its own). The generated key lives and dies in the scratch tree, and is never read.
    """

    def real(self) -> dict[str, str]:
        return {"SSH_KEYGEN": str(REAL_KEYGEN), "SSH": str(REAL_SSH), "UNAME": str(REAL_UNAME)}

    def real_ssh_g(self, cfg: Path, alias: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(REAL_SSH), "-F", str(cfg), "-G", alias], env=self.env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def test_end_to_end_then_a_noop(self) -> None:
        proc = self.run_setup("--title", "Deploy Key - Ci", ssh_dir=self.alt_dir, **self.real())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((mode(self.key(self.alt_dir)), mode(self.pub(self.alt_dir))), (0o600, 0o644))
        darwin = platform.system() == "Darwin"
        self.assertEqual(self.config(self.alt_dir).read_text(encoding="utf-8"), block(str(self.key(self.alt_dir)), darwin=darwin))
        self.assertIn("SHA256:", proc.stdout)
        before = self.snapshot(self.alt_dir)
        second = self.run_setup("--title", "Deploy Key - Ci", ssh_dir=self.alt_dir, **self.real())
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("already configured", second.stdout)
        self.assertEqual(self.snapshot(self.alt_dir), before)

    def test_an_earlier_host_star_identity_is_caught_before_install(self) -> None:
        cfg = self.write_config(f"Host *\n  IdentityFile {self.alt_dir / 'id_other'}\n", self.alt_dir)
        before = self.snapshot(self.alt_dir)
        proc = self.run_setup("--title", "Deploy Key - Ci", ssh_dir=self.alt_dir, **self.real())
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"MISMATCH: ssh -G {ALIAS} resolves identityfile [{self.alt_dir / 'id_other'},", proc.stderr)
        self.assertEqual(self.snapshot(self.alt_dir), before)
        self.assertEqual(cfg.read_text(encoding="utf-8"), f"Host *\n  IdentityFile {self.alt_dir / 'id_other'}\n")

    def test_negative_control_ignoreunknown_inside_a_block_breaks_every_other_host(self) -> None:
        probe = self.alt_dir / "probe-config"
        probe.write_text("Host probe\n  UseKeychain yes\n", encoding="utf-8")
        probe.chmod(0o600)
        if self.real_ssh_g(probe, "probe").returncode == 0:
            self.skipTest("this ssh knows UseKeychain (Apple's); the failure exists only on upstream OpenSSH")
        cfg = self.alt_dir / "ignoreunknown-config"
        cfg.write_text(f"Host {ALIAS}\n  HostName github.com\n  IgnoreUnknown UseKeychain\n  UseKeychain yes\n", encoding="utf-8")
        cfg.chmod(0o600)
        own = self.real_ssh_g(cfg, ALIAS)
        self.assertEqual(own.returncode, 0, f"IgnoreUnknown does cover the block's own alias: {own.stderr}")
        other = self.real_ssh_g(cfg, "github_juniper-ml")
        self.assertNotEqual(other.returncode, 0, "an unknown keyword in a non-matching block is still fatal")
        self.assertIn("usekeychain", other.stderr.lower())


class SourceContractTest(unittest.TestCase):
    """Static pins. Comment lines are excluded; the header discusses what the code must not do."""

    text: str
    code: str
    code_lines: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.code_lines = [line for line in cls.text.splitlines() if not line.lstrip().startswith("#")]
        cls.code = "\n".join(cls.code_lines)

    def test_strict_mode_umask_and_overridable_tools(self) -> None:
        for snippet in ("set -euo pipefail", "umask 077", 'SSH_KEYGEN="${SSH_KEYGEN:-ssh-keygen}"', 'SSH="${SSH:-ssh}"', 'UNAME="${UNAME:-uname}"'):
            self.assertIn(snippet, self.code)

    def test_portable_to_bash_32_and_bsd_userland(self) -> None:
        forbidden = {
            "stat -c": r"\bstat\s+-c\b",
            "stat -f": r"\bstat\s+-f\b",
            "mapfile": r"\bmapfile\b",
            "readarray": r"\breadarray\b",
            "associative array": r"\b(declare|local|typeset)\s+-A\b",
            "case modification": r"\$\{[A-Za-z_][A-Za-z0-9_]*(,,|\^\^|,|\^)\}",
            "[[ -v": r"\[\[\s+-v\b",
            "|&": r"\|&",
            "coproc": r"\bcoproc\b",
            "sed -i": r"\bsed\s+-i\b",
            "readlink -f": r"\breadlink\s+-f\b",
            "realpath": r"\brealpath\b",
            "grep -P": r"\bgrep\s+-[A-Za-z]*P",
            "date -d": r"\bdate\s+-d\b",
        }
        for label, pattern in forbidden.items():
            with self.subTest(label):
                self.assertIsNone(re.search(pattern, self.code), label)

    def test_ssh_is_only_asked_to_evaluate_configuration(self) -> None:
        calls = [line for line in self.code_lines if re.search(r'(\$\(|^\s*)"\$SSH"\s', line)]
        self.assertEqual(len(calls), 2, calls)
        for line in calls:
            self.assertIn(" -G ", line)
        self.assertIsNone(re.search(r"\bssh\s+-T\b|\bssh-add\b", self.code))

    def test_never_registers_keys_through_gh(self) -> None:
        mentions = [line for line in self.code_lines if re.search(r"\bgh\s+(repo|api|auth|pr|secret)\b", line)]
        self.assertTrue(mentions, "the printed warning against gh repo deploy-key add must stay")
        for line in mentions:
            self.assertTrue(line.lstrip().startswith("echo "), f"gh may only be mentioned in printed text: {line}")

    def test_canonical_block_says_addkeystoagent_no(self) -> None:
        self.assertIn("  AddKeysToAgent no", self.code)
        self.assertNotIn("AddKeysToAgent yes", self.code)

    def test_private_key_is_never_read(self) -> None:
        self.assertIsNone(re.search(r"\b(cat|head|tail|less|more|od|xxd|base64|openssl|grep|awk|sed|cp|dd)\b[^\n]*\"\$\{?KEY\}?\"", self.code))
        self.assertIsNone(re.search(r"<\s*\"\$\{?KEY\}?\"", self.code))
        self.assertIsNone(re.search(r"-lf\s+\"\$\{?KEY\}?\"", self.code))
        self.assertIsNone(re.search(r"\s-y\s", self.code), "ssh-keygen -y reads the private key")

    def test_no_host_specific_home_literal(self) -> None:
        self.assertNotRegex(self.text, r"/Users/|/home/", "use a $HOME-relative path (plan D12)")

    def test_shellcheck_clean_when_available(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("shellcheck not installed (CI's pre-commit runs it)")
        proc = subprocess.run([shellcheck, str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
