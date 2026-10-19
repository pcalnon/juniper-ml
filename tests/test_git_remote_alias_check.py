#!/usr/bin/env python3
"""Hermetic gate for util/git_remote_alias_check.py (turing bring-up task G2; regressions R-G2a/b/c).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

Gate G-ALIAS (``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` §9.3) asks
three things of every active checkout:

- an origin in ``git@github_juniper-<repo>:`` form;
- an alias whose resolved ssh config is pinned to that repo's deploy key with ``AddKeysToAgent no``;
- a key at mode 600.

On turing two origins bypassed the alias: juniper-k8s used ``git@github.com:`` (R-G2a) and
juniper-recurrence used ``https://`` (R-G2b). R-G2c is an alias with no Host block, or one with
``AddKeysToAgent yes``.

How the suite stays hermetic:

- Real ``git`` runs on temp repos under a temp root. Every ``GIT_*`` variable is scrubbed, the
  session's ``GIT_CONFIG_COUNT`` signing guard included. ``GIT_CONFIG_NOSYSTEM=1``, an isolated
  ``GIT_CONFIG_GLOBAL`` and a temp ``HOME`` make it behave the same here and on Linux CI.
- ``ssh`` is a stub. It answers ``ssh -G <alias>`` from per-alias recordings, which keep the shape of
  OpenSSH 9.9's real output (trimmed), and it refuses any other argv. An alias with no recording gets
  the recorded shape of an undefined alias: ``hostname`` equal to the alias itself.
- Keys are placeholder files with chosen modes under the temp HOME. Nothing reads the real ``~/.ssh``.

The pre-push cases run the script from a real git hook in a linked worktree, where git exports
``GIT_DIR``. A negative control shows that a naive ``git -C`` read there returns the pushing
repository's origin. The read-contract cases run the script under a Python audit hook that records
every file it opens.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - drives the checker and real git on temp repos
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "git_remote_alias_check.py"
TIMEOUT_SECONDS = 120

ACTIVE = ("canopy", "cascor", "cascor-client", "cascor-worker", "data", "data-client", "deploy", "k8s", "ml", "recurrence")
CHECKS = ("origin", "alias", "key")
R_G2A_URL = "git@github.com:pcalnon/juniper-k8s.git"
R_G2B_URL = "https://github.com/pcalnon/juniper-recurrence.git"
SETUP_HINT = "bash util/juniper_repo_ssh_setup.bash"

TOP_KEYS = {"schema", "mode", "root", "ssh_config", "skipped", "skip_reason", "ok", "exit_code", "summary", "failures", "repos"}
REPO_KEYS = {"repo", "checkout", "alias", "ok", "checks"}
COMMON_CHECK_KEYS = {"status", "ok", "message", "remediation"}
CHECK_KEYS = {
    "origin": COMMON_CHECK_KEYS | {"expected_url", "url", "pushurls", "fix"},
    "alias": COMMON_CHECK_KEYS | {"hostname", "identityfile", "identitiesonly", "addkeystoagent", "expected_identityfile"},
    "key": COMMON_CHECK_KEYS | {"path", "exists", "regular_file", "mode"},
}
FIX_KEYS = {"from", "to", "applied", "error"}

GITCONFIG = "[init]\n\tdefaultBranch = main\n[user]\n\tname = G2 Test\n\temail = g2-test@example.invalid\n[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n"

SSH_STUB = r"""#!/bin/bash
# ssh stub: answers `ssh -G <alias>` from the recording $STUB_SSH_DIR/<alias>. An alias with no
# recording gets the recorded shape of an undefined alias (OpenSSH 9.9): hostname = the alias itself.
# Aliases named in STUB_SSH_FAIL fail the way a broken config does. Any other argv is refused.
printf '%s\n' "$*" >> "$STUB_SSH_LOG"
if [ "$#" -ne 2 ] || [ "$1" != "-G" ]; then
    echo "ssh stub: refusing argv: $*" >&2
    exit 99
fi
case " ${STUB_SSH_FAIL:-} " in
    *" $2 "*)
        echo "$HOME/.ssh/config line 7: Bad configuration option: identitesonly" >&2
        exit 255
        ;;
esac
# turing's ssh prints this on every non-tty call; a passing check must ignore it.
echo "Pseudo-terminal will not be allocated because stdin is not a terminal." >&2
if [ -f "$STUB_SSH_DIR/$2" ]; then
    cat "$STUB_SSH_DIR/$2"
    exit 0
fi
printf 'host %s\nhostname %s\nport 22\nidentitiesonly no\n' "$2" "$2"
for f in id_rsa id_ecdsa id_ecdsa_sk id_ed25519 id_ed25519_sk id_xmss id_dsa; do
    printf 'identityfile ~/.ssh/%s\n' "$f"
done
printf 'addkeystoagent false\n'
"""

# Logs argv, then runs the real git. STUB_GIT_MODE=forbid refuses every call. noop-set-url and
# fail-set-url sabotage `remote set-url`, so the script's re-read has to catch it.
GIT_WRAPPER = r"""#!/bin/bash
printf '%s\n' "$*" >> "$STUB_GIT_LOG"
if [ "${STUB_GIT_MODE:-}" = "forbid" ]; then
    echo "git wrapper: no git call was expected" >&2
    exit 97
fi
case " $* " in
    *" remote set-url "*)
        case "${STUB_GIT_MODE:-}" in
            noop-set-url) exit 0 ;;
            fail-set-url)
                echo "error: could not lock config file .git/config: File exists" >&2
                exit 4
                ;;
        esac
        ;;
esac
exec "$REAL_GIT" "$@"
"""

# Task G6's shape: the check runs from git's pre-push hook with only its two flags. The hook first
# records whether git exported GIT_DIR, and what a naive `git -C <checkout>` read returns under it
# (the negative control).
PRE_PUSH_HOOK = r"""#!/bin/sh
printf '%s\n' "${GIT_DIR:-<unset>}" > "$HOOK_GIT_DIR"
"$REAL_GIT" -C "$HOOK_ROOT/juniper-k8s" config --get remote.origin.url > "$HOOK_NAIVE" 2>&1
"$HOOK_PYTHON" "$HOOK_SCRIPT" --check --if-configured > "$HOOK_OUT" 2>&1
"""

# Runs the script with an audit hook that logs every file opened or changed in-process. The
# sentinel proves the hook is live before the script starts.
AUDIT_WRAPPER = r"""
import os
import runpy
import sys

sys.dont_write_bytecode = True
_fd = os.open(os.environ["AUDIT_LOG"], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
_WATCH = {"open", "os.chmod", "os.chown", "os.link", "os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.symlink", "os.truncate", "os.utime", "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.move", "shutil.rmtree"}


def _hook(event, args):
    if event in _WATCH and args and isinstance(args[0], (str, bytes, os.PathLike)):
        mode = args[1] if event == "open" and len(args) > 1 else None
        os.write(_fd, ("%s\t%s\t%r\n" % (event, os.fsdecode(args[0]), mode)).encode("utf-8", "replace"))


sys.addaudithook(_hook)
with open(os.environ["AUDIT_LOG"] + ".sentinel", "w"):
    pass
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def alias_url(name: str) -> str:
    return f"git@github_juniper-{name}:pcalnon/juniper-{name}.git"


def ssh_g_recording(alias: str, *, hostname: str = "github.com", identityfiles: tuple[str, ...] | None = None, identitiesonly: str | None = "yes", addkeystoagent: str | None = "false") -> str:
    """What `ssh -G <alias>` prints for a configured Host block.

    Recorded from OpenSSH_9.9p2 (LibreSSL 3.3.6) on turing, 2026-10-17, and trimmed. It keeps the
    real order, the repeated ``sendenv`` and the unexpanded ``~`` in ``identityfile``. ``None``
    drops a line.
    """
    if identityfiles is None:
        identityfiles = (f"~/.ssh/id_ed25519_{alias}",)
    lines = [f"host {alias}", "user git", f"hostname {hostname}", "port 22", "addressfamily any", "batchmode no", "canonicalizehostname false", "checkhostip no", "compression no", "controlmaster false", "forwardx11 no", "hashknownhosts no"]
    if identitiesonly is not None:
        lines.append(f"identitiesonly {identitiesonly}")
    lines += ["kbdinteractiveauthentication yes", "passwordauthentication yes", "pubkeyauthentication true", "requesttty auto", "stricthostkeychecking ask", "tcpkeepalive yes", "connectionattempts 1", "loglevel INFO", "xauthlocation /usr/X11R6/bin/xauth"]
    lines += [f"identityfile {path}" for path in identityfiles]
    lines += ["canonicaldomains none", "globalknownhostsfile /etc/ssh/ssh_known_hosts /etc/ssh/ssh_known_hosts2", "userknownhostsfile ~/.ssh/known_hosts ~/.ssh/known_hosts2", "sendenv LANG", "sendenv LC_*", "logverbose none"]
    if addkeystoagent is not None:
        lines.append(f"addkeystoagent {addkeystoagent}")
    lines += ["forwardagent no", "connecttimeout none", "controlpersist no", "escapechar ~", "streamlocalbindmask 0177", "syslogfacility USER"]
    return "\n".join(lines) + "\n"


def hermetic_env(home: Path, gitconfig: Path, **overrides: str) -> RedactedEnv:
    """The caller's environment without any GIT_* variable (the session's GIT_CONFIG_COUNT guard included)."""
    env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in ("JUNIPER_ROOT", "SSH", "XDG_CONFIG_HOME")})
    env.update(HOME=str(home), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(gitconfig), GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    env.update(overrides)
    return env


def parse_report(stdout: str) -> tuple[dict[tuple[str, str], tuple[str, str]], str]:
    """``{(repo, check): (STATUS, detail)}`` and the summary line, from the human report."""
    rows: dict[tuple[str, str], tuple[str, str]] = {}
    summary = ""
    for line in stdout.splitlines():
        if line.startswith(("summary: ", "skipped: ")):
            summary = line
            continue
        status, repo, check, detail = line.split(None, 3)
        rows[(repo, check)] = (status, detail)
    return rows, summary


def _write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


class _Template:
    """Ten checkouts with alias-form origins, built once per module and copied into each test."""

    git = ""
    root = Path()
    tmp: tempfile.TemporaryDirectory[str] | None = None


def setUpModule() -> None:
    git = shutil.which("git")
    if git is None:
        raise unittest.SkipTest("git not installed")
    _Template.tmp = tempfile.TemporaryDirectory()
    base = Path(_Template.tmp.name)
    (base / "home").mkdir()
    (base / "empty-template").mkdir()
    gitconfig = base / "gitconfig"
    gitconfig.write_text(GITCONFIG, encoding="utf-8")
    env = hermetic_env(base / "home", gitconfig)
    for name in ACTIVE:
        repo = base / "root" / f"juniper-{name}"
        for argv in (["init", "-q", f"--template={base / 'empty-template'}", str(repo)], ["-C", str(repo), "remote", "add", "origin", alias_url(name)]):
            subprocess.run([git, *argv], env=env, check=True, capture_output=True, timeout=TIMEOUT_SECONDS)
    _Template.git = git
    _Template.root = base / "root"


def tearDownModule() -> None:
    if _Template.tmp is not None:
        _Template.tmp.cleanup()


class _Fixture(unittest.TestCase):
    """A temp HOME with ten good checkouts, ten recorded aliases and ten keys at 600."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.home = self.base / "home"
        self.ssh_dir = self.home / ".ssh"
        self.ssh_dir.mkdir(parents=True)
        self.ssh_dir.chmod(0o700)
        self.ssh_config = self.ssh_dir / "config"
        self.root = self.home / "Development" / "python" / "Juniper"
        shutil.copytree(_Template.root, self.root, symlinks=True)
        self.cwd = self.base / "cwd"
        self.cwd.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.recordings = self.base / "ssh-recordings"
        self.recordings.mkdir()
        self.ssh_log = self.base / "ssh.log"
        self.git_log = self.base / "git.log"
        self.gitconfig = self.base / "gitconfig"
        self.gitconfig.write_text(GITCONFIG, encoding="utf-8")
        ssh_stub = _write_exe(self.bin / "ssh-stub", SSH_STUB)
        git_wrapper = _write_exe(self.bin / "git-wrapper", GIT_WRAPPER)
        for name in ACTIVE:
            self.record(name)
            self.make_key(name)
        self.env = hermetic_env(
            self.home,
            self.gitconfig,
            JUNIPER_ROOT=str(self.root),
            GIT=str(git_wrapper),
            REAL_GIT=_Template.git,
            SSH=str(ssh_stub),
            STUB_SSH_DIR=str(self.recordings),
            STUB_SSH_LOG=str(self.ssh_log),
            STUB_GIT_LOG=str(self.git_log),
        )

    # --- fixture state -----------------------------------------------------------------------

    def record(self, name: str, **shape: object) -> None:
        alias = f"github_juniper-{name}"
        (self.recordings / alias).write_text(ssh_g_recording(alias, **shape), encoding="utf-8")  # type: ignore[arg-type]

    def unrecord(self, name: str) -> None:
        (self.recordings / f"github_juniper-{name}").unlink()

    def key(self, name: str) -> Path:
        return self.ssh_dir / f"id_ed25519_github_juniper-{name}"

    def make_key(self, name: str, mode: int = 0o600) -> Path:
        path = self.key(name)
        path.write_text("placeholder for a deploy key; not key material\n", encoding="utf-8")
        path.chmod(mode)
        return path

    def checkout(self, name: str) -> Path:
        return self.root / f"juniper-{name}"

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """The real git under the hermetic env, for setup and read-back."""
        return subprocess.run([_Template.git, *args], env=self.env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=check)

    def set_origin(self, name: str, url: str) -> None:
        self.git("-C", str(self.checkout(name)), "remote", "set-url", "origin", url)

    def persisted(self, name: str) -> str:
        return self.git("-C", str(self.checkout(name)), "config", "--get", "remote.origin.url", check=False).stdout.strip()

    def config_bytes(self) -> dict[str, bytes]:
        return {name: (self.checkout(name) / ".git" / "config").read_bytes() for name in ACTIVE}

    def ssh_tree(self) -> dict[str, tuple[int, int, int]]:
        """Mode, size and mtime of everything under ~/.ssh, by lstat; no file is read."""
        tree: dict[str, tuple[int, int, int]] = {}
        for path in [self.ssh_dir, *sorted(self.ssh_dir.rglob("*"))]:
            info = os.lstat(path)
            tree[str(path.relative_to(self.home))] = (info.st_mode, info.st_size, info.st_mtime_ns)
        return tree

    # --- running ------------------------------------------------------------------------------

    def run_check(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        run_env = self.env.copy()
        run_env.update(env)
        return subprocess.run([sys.executable, str(SCRIPT_PATH), *args], cwd=self.cwd, env=run_env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def calls(self, log: Path) -> list[str]:
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def set_url_calls(self) -> list[str]:
        return [call for call in self.calls(self.git_log) if " remote set-url " in f" {call} "]

    def row(self, proc: subprocess.CompletedProcess[str], name: str, check: str) -> tuple[str, str]:
        rows, _ = parse_report(proc.stdout)
        self.assertIn((f"juniper-{name}", check), rows, proc.stdout + proc.stderr)
        return rows[(f"juniper-{name}", check)]

    def not_passing(self, proc: subprocess.CompletedProcess[str]) -> set[tuple[str, str]]:
        rows, _ = parse_report(proc.stdout)
        return {key for key, (status, _) in rows.items() if status != "PASS"}


class HappyPathTest(_Fixture):
    def test_all_ten_checkouts_pass(self) -> None:
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        rows, summary = parse_report(proc.stdout)
        self.assertEqual(list(rows), [(f"juniper-{name}", check) for name in ACTIVE for check in CHECKS], "one line per check per repo, in canonical order")
        self.assertEqual({status for status, _ in rows.values()}, {"PASS"})
        self.assertEqual(summary, "summary: 30 of 30 checks passed")
        self.assertEqual(rows[("juniper-k8s", "origin")][1], alias_url("k8s"))
        self.assertEqual(rows[("juniper-k8s", "alias")][1], "github_juniper-k8s -> github.com; identityfile ~/.ssh/id_ed25519_github_juniper-k8s; identitiesonly yes; addkeystoagent false")
        self.assertEqual(rows[("juniper-k8s", "key")][1], f"{self.key('k8s')} (regular file, mode 600)")
        self.assertEqual(proc.stderr, "")

    def test_juniper_legacy_is_never_checked(self) -> None:
        legacy = self.root / "juniper-legacy"
        legacy.mkdir()
        (legacy / "README.md").write_text("archive\n", encoding="utf-8")
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("legacy", proc.stdout)
        self.assertNotIn("legacy", "\n".join(self.calls(self.ssh_log) + self.calls(self.git_log)))

    def test_ssh_is_only_asked_to_evaluate_its_configuration(self) -> None:
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.calls(self.ssh_log), [f"-G github_juniper-{name}" for name in ACTIVE])

    def test_check_mode_runs_only_read_only_git(self) -> None:
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        expected = ["rev-parse --local-env-vars"]
        for name in ACTIVE:
            checkout = self.checkout(name)
            expected += [f"-C {checkout} rev-parse --show-toplevel", f"-C {checkout} config --get remote.origin.url", f"-C {checkout} config --get-all remote.origin.pushurl"]
        self.assertEqual(self.calls(self.git_log), expected)

    def test_an_expanded_identityfile_names_the_same_key(self) -> None:
        # Some OpenSSH builds print IdentityFile expanded; both forms name the same file.
        self.record("ml", identityfiles=(str(self.key("ml")),))
        proc = self.run_check("--repo", "ml")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_the_port_443_endpoint_is_accepted(self) -> None:
        # util/juniper_clone.bash accepts ssh.github.com; the two tools must agree.
        self.record("ml", hostname="ssh.github.com")
        proc = self.run_check("--repo", "ml")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("github_juniper-ml -> ssh.github.com", self.row(proc, "ml", "alias")[1])

    def test_a_key_symlinked_to_a_600_file_passes(self) -> None:
        target = self.ssh_dir / "vault" / "id_ed25519_github_juniper-ml"
        target.parent.mkdir()
        target.write_text("placeholder\n", encoding="utf-8")
        target.chmod(0o600)
        self.key("ml").unlink()
        self.key("ml").symlink_to(target)
        proc = self.run_check("--repo", "ml")
        self.assertEqual(proc.returncode, 0, proc.stdout)


class OriginTest(_Fixture):
    def test_r_g2a_github_com_origin_fails(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        status, detail = self.row(proc, "k8s", "origin")
        self.assertEqual(status, "FAIL")
        self.assertEqual(detail, f"origin {R_G2A_URL!r} bypasses the alias; want {alias_url('k8s')!r} -- fix: git -C {self.checkout('k8s')} remote set-url origin {alias_url('k8s')} (or rerun with --fix)")
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 29 of 30 checks passed; 1 failed: juniper-k8s origin")

    def test_r_g2b_https_origin_fails(self) -> None:
        self.set_origin("recurrence", R_G2B_URL)
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        status, detail = self.row(proc, "recurrence", "origin")
        self.assertEqual(status, "FAIL")
        self.assertIn(f"origin {R_G2B_URL!r} bypasses the alias", detail)
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 29 of 30 checks passed; 1 failed: juniper-recurrence origin")

    def test_turings_two_bad_origins_are_both_listed(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.set_origin("recurrence", R_G2B_URL)
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.not_passing(proc), {("juniper-k8s", "origin"), ("juniper-recurrence", "origin")})
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 28 of 30 checks passed; 2 failed: juniper-k8s origin, juniper-recurrence origin")

    def test_insteadof_cannot_mask_a_bypass_origin(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        with self.gitconfig.open("a", encoding="utf-8") as fh:
            fh.write(f'[url "{alias_url("k8s")}"]\n\tinsteadOf = {R_G2A_URL}\n')
        # Negative control: the insteadOf is live, so `remote get-url` shows alias form over the bypass URL.
        self.assertEqual(self.git("-C", str(self.checkout("k8s")), "remote", "get-url", "origin").stdout.strip(), alias_url("k8s"))
        proc = self.run_check("--repo", "k8s")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "k8s", "origin")[0], "FAIL")

    def test_near_miss_origins_fail(self) -> None:
        near_misses = {
            "no .git suffix": "git@github_juniper-k8s:pcalnon/juniper-k8s",
            "trailing slash": "git@github_juniper-k8s:pcalnon/juniper-k8s.git/",
            "leading junk": "xgit@github_juniper-k8s:pcalnon/juniper-k8s.git",
            "ssh:// form of the alias": "ssh://git@github_juniper-k8s/pcalnon/juniper-k8s.git",
            "another repo's alias": "git@github_juniper-ml:pcalnon/juniper-k8s.git",
            "another owner": "git@github_juniper-k8s:someone/juniper-k8s.git",
            "another user": "deploy@github_juniper-k8s:pcalnon/juniper-k8s.git",
            "upper-case alias": "git@github_juniper-K8S:pcalnon/juniper-k8s.git",
        }
        for label, url in near_misses.items():
            with self.subTest(label):
                self.set_origin("k8s", url)
                proc = self.run_check("--repo", "k8s")
                self.assertEqual(proc.returncode, 1, f"{label}: {proc.stdout}")
                self.assertEqual(self.row(proc, "k8s", "origin")[0], "FAIL")

    def test_a_pushurl_must_use_the_alias_too(self) -> None:
        checkout = str(self.checkout("k8s"))
        self.git("-C", checkout, "config", "remote.origin.pushurl", R_G2A_URL)
        proc = self.run_check("--repo", "k8s")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        status, detail = self.row(proc, "k8s", "origin")
        self.assertEqual(status, "FAIL")
        self.assertIn(f"pushurl {R_G2A_URL!r} bypasses the alias for pushes", detail)
        self.assertIn(f"-- fix: git -C {checkout} config --unset-all remote.origin.pushurl", detail)
        self.git("-C", checkout, "config", "remote.origin.pushurl", alias_url("k8s"))
        self.assertEqual(self.run_check("--repo", "k8s").returncode, 0, "an alias-form pushurl passes")

    def test_a_missing_checkout_is_named(self) -> None:
        shutil.rmtree(self.checkout("deploy"))
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "deploy", "origin"), ("FAIL", f"no checkout: {self.checkout('deploy')} does not exist -- fix: bash util/juniper_clone.bash deploy"))
        self.assertEqual(self.not_passing(proc), {("juniper-deploy", "origin")})

    def test_a_file_where_the_checkout_belongs_is_named(self) -> None:
        # juniper_clone.bash refuses an existing destination, so the remediation moves it aside first.
        shutil.rmtree(self.checkout("deploy"))
        self.checkout("deploy").write_text("not a checkout\n", encoding="utf-8")
        proc = self.run_check("--repo", "deploy")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "deploy", "origin"), ("FAIL", f"no checkout: {self.checkout('deploy')} is not a directory -- fix: move {self.checkout('deploy')} aside, then: bash util/juniper_clone.bash deploy"))

    def test_a_plain_directory_is_not_a_checkout(self) -> None:
        shutil.rmtree(self.checkout("deploy"))
        self.checkout("deploy").mkdir()
        proc = self.run_check("--repo", "deploy")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        status, detail = self.row(proc, "deploy", "origin")
        self.assertEqual(status, "FAIL")
        self.assertIn(f"{self.checkout('deploy')} is not a git checkout", detail)

    def test_a_directory_inside_another_repository_is_not_its_checkout(self) -> None:
        # The root is itself a repository whose origin looks like deploy's. A naive read would report
        # that origin, and --fix would rewrite the parent's config.
        self.git("init", "-q", str(self.root))
        self.git("-C", str(self.root), "remote", "add", "origin", "git@github.com:pcalnon/juniper-deploy.git")
        shutil.rmtree(self.checkout("deploy"))
        self.checkout("deploy").mkdir()
        parent_config = (self.root / ".git" / "config").read_bytes()
        for args in ((), ("--fix",)):
            with self.subTest(args=args):
                proc = self.run_check("--repo", "deploy", *args)
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn("is not a git checkout; it is a directory inside", self.row(proc, "deploy", "origin")[1])
                self.assertEqual((self.root / ".git" / "config").read_bytes(), parent_config)
        self.assertEqual(self.set_url_calls(), [])

    def test_a_missing_origin_is_named(self) -> None:
        self.git("-C", str(self.checkout("data")), "remote", "remove", "origin")
        proc = self.run_check("--repo", "data")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "data", "origin"), ("FAIL", f"no origin remote (remote.origin.url is unset) -- fix: git -C {self.checkout('data')} remote add origin {alias_url('data')}"))

    def test_an_https_token_is_never_printed(self) -> None:
        token = "tok" + "en-value-" + "x" * 12  # assembled at run time; not a credential shape
        self.set_origin("recurrence", f"https://x-access-token:{token}@github.com/pcalnon/juniper-recurrence.git")
        redacted = "https://***@github.com/pcalnon/juniper-recurrence.git"
        for args in ((), ("--json",), ("--fix", "--dry-run"), ("--fix", "--json")):
            with self.subTest(args=args):
                proc = self.run_check("--repo", "recurrence", *args)
                self.assertNotIn(token, proc.stdout + proc.stderr)
                self.assertIn(redacted, proc.stdout)
        self.assertEqual(self.persisted("recurrence"), alias_url("recurrence"), "the last --fix rewrote the token-bearing origin")


class AliasTest(_Fixture):
    def test_r_g2c_missing_host_block(self) -> None:
        self.unrecord("k8s")
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "k8s", "alias"), ("FAIL", f"no Host block for github_juniper-k8s (hostname resolves to the alias itself) -- fix: {SETUP_HINT} k8s"))
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 29 of 30 checks passed; 1 failed: juniper-k8s alias")

    def test_r_g2c_addkeystoagent_yes(self) -> None:
        self.record("ml", addkeystoagent="true")
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        status, detail = self.row(proc, "ml", "alias")
        self.assertEqual(status, "FAIL")
        self.assertEqual(detail, f"addkeystoagent true, want false -- fix: in the Host github_juniper-ml block of {self.ssh_config}, set AddKeysToAgent no")
        self.assertEqual(self.not_passing(proc), {("juniper-ml", "alias")})

    def test_addkeystoagent_must_be_false(self) -> None:
        for value in ("ask", "confirm", "3600", None):
            with self.subTest(addkeystoagent=value):
                self.record("ml", addkeystoagent=value)
                proc = self.run_check("--repo", "ml")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn("AddKeysToAgent no", self.row(proc, "ml", "alias")[1])

    def test_identitiesonly_must_be_yes(self) -> None:
        for value in ("no", None):
            with self.subTest(identitiesonly=value):
                self.record("ml", identitiesonly=value)
                proc = self.run_check("--repo", "ml")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn("IdentitiesOnly yes", self.row(proc, "ml", "alias")[1])

    def test_identityfile_must_be_exactly_the_repos_key(self) -> None:
        cases = {
            "another repo's key": ("~/.ssh/id_ed25519_github_juniper-ml",),
            "the default key": ("~/.ssh/id_ed25519",),
            "an extra key": ("~/.ssh/id_ed25519_github_juniper-k8s", "~/.ssh/id_rsa"),
            "no key": (),
        }
        for label, files in cases.items():
            with self.subTest(label):
                self.record("k8s", identityfiles=files)
                proc = self.run_check("--repo", "k8s")
                self.assertEqual(proc.returncode, 1, f"{label}: {proc.stdout}")
                self.assertIn("want only ~/.ssh/id_ed25519_github_juniper-k8s", self.row(proc, "k8s", "alias")[1])

    def test_hostname_must_be_github(self) -> None:
        for host in ("gitlab.com", "github.com.example.invalid"):
            with self.subTest(host=host):
                self.record("k8s", hostname=host)
                proc = self.run_check("--repo", "k8s")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn("HostName github.com", self.row(proc, "k8s", "alias")[1])

    def test_every_alias_problem_is_named_on_one_line(self) -> None:
        self.record("k8s", hostname="gitlab.com", identityfiles=("~/.ssh/id_rsa",), identitiesonly="no", addkeystoagent="true")
        proc = self.run_check("--repo", "k8s")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(len(proc.stdout.splitlines()), 4, "three check lines and the summary")
        detail = self.row(proc, "k8s", "alias")[1]
        for needle in ("hostname gitlab.com", "identityfile ~/.ssh/id_rsa", "identitiesonly no", "addkeystoagent true", "HostName github.com", "IdentitiesOnly yes", "AddKeysToAgent no"):
            self.assertIn(needle, detail)

    def test_a_failed_ssh_evaluation_exits_2(self) -> None:
        proc = self.run_check(STUB_SSH_FAIL="github_juniper-data")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        status, detail = self.row(proc, "data", "alias")
        self.assertEqual(status, "ERROR")
        self.assertIn("'ssh -G github_juniper-data' could not evaluate the ssh configuration (exit 255)", detail)
        self.assertIn("Bad configuration option", detail)
        self.assertEqual(self.not_passing(proc), {("juniper-data", "alias")}, "every other check still runs")
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 29 of 30 checks passed; 1 could not be evaluated: juniper-data alias")

    def test_empty_ssh_output_exits_2(self) -> None:
        (self.recordings / "github_juniper-data").write_text("", encoding="utf-8")
        proc = self.run_check("--repo", "data")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(self.row(proc, "data", "alias"), ("ERROR", "'ssh -G github_juniper-data' reported no hostname"))

    def test_an_error_outranks_a_failure(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        proc = self.run_check(STUB_SSH_FAIL="github_juniper-data")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertEqual(self.row(proc, "k8s", "origin")[0], "FAIL")
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 28 of 30 checks passed; 1 failed: juniper-k8s origin; 1 could not be evaluated: juniper-data alias")


class KeyTest(_Fixture):
    def test_a_key_at_mode_644_fails(self) -> None:
        self.key("recurrence").chmod(0o644)
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        key = self.key("recurrence")
        self.assertEqual(self.row(proc, "recurrence", "key"), ("FAIL", f"{key} is mode 644, want 600 -- fix: chmod 600 {key}"))
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 29 of 30 checks passed; 1 failed: juniper-recurrence key")

    def test_only_mode_600_passes(self) -> None:
        for mode in (0o640, 0o604, 0o660, 0o400, 0o700, 0o755):
            with self.subTest(mode=oct(mode)):
                self.key("ml").chmod(mode)
                proc = self.run_check("--repo", "ml")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn(f"is mode {mode:03o}, want 600", self.row(proc, "ml", "key")[1])

    def test_a_missing_key_fails(self) -> None:
        self.key("cascor").unlink()
        proc = self.run_check()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "cascor", "key"), ("FAIL", f"{self.key('cascor')} is missing -- fix: {SETUP_HINT} cascor"))
        self.assertEqual(self.not_passing(proc), {("juniper-cascor", "key")})

    def test_a_dangling_symlink_counts_as_missing(self) -> None:
        self.key("cascor").unlink()
        self.key("cascor").symlink_to(self.ssh_dir / "gone")
        proc = self.run_check("--repo", "cascor")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("is missing", self.row(proc, "cascor", "key")[1])

    def test_a_directory_at_the_key_path_fails_even_at_600(self) -> None:
        key = self.key("cascor")
        key.unlink()
        key.mkdir()
        key.chmod(0o600)
        self.addCleanup(key.chmod, 0o700)
        proc = self.run_check("--repo", "cascor")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"{key} is not a regular file", self.row(proc, "cascor", "key")[1])


class FixTest(_Fixture):
    def test_fix_rewrites_both_turing_origins_and_rereads_them(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.set_origin("recurrence", R_G2B_URL)
        proc = self.run_check("--fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.row(proc, "k8s", "origin"), ("FIXED", f"rewrote {R_G2A_URL!r} -> {alias_url('k8s')!r} (persisted value re-read)"))
        self.assertEqual(self.row(proc, "recurrence", "origin"), ("FIXED", f"rewrote {R_G2B_URL!r} -> {alias_url('recurrence')!r} (persisted value re-read)"))
        self.assertEqual(self.persisted("k8s"), alias_url("k8s"))
        self.assertEqual(self.persisted("recurrence"), alias_url("recurrence"))
        self.assertEqual(self.set_url_calls(), [f"-C {self.checkout(name)} remote set-url origin {alias_url(name)}" for name in ("k8s", "recurrence")])
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 30 of 30 checks passed; --fix rewrote 2 origins")

    def test_fix_is_idempotent(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.set_origin("recurrence", R_G2B_URL)
        first = self.run_check("--fix")
        self.assertEqual(first.returncode, 0, first.stdout)
        after_first = self.config_bytes()
        self.git_log.unlink()
        second = self.run_check("--fix")
        self.assertEqual(second.returncode, 0, second.stdout)
        self.assertEqual(self.not_passing(second), set())
        self.assertEqual(parse_report(second.stdout)[1], "summary: 30 of 30 checks passed")
        self.assertEqual(self.set_url_calls(), [], "a second --fix has nothing to rewrite")
        self.assertEqual(self.config_bytes(), after_first)

    def test_fix_dry_run_writes_nothing(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.set_origin("recurrence", R_G2B_URL)
        before = self.config_bytes()
        mtimes = {name: os.stat(self.checkout(name) / ".git" / "config").st_mtime_ns for name in ACTIVE}
        proc = self.run_check("--fix", "--dry-run")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        status, detail = self.row(proc, "k8s", "origin")
        self.assertEqual(status, "FAIL")
        self.assertTrue(detail.endswith(f" -- DRY-RUN: would run: git -C {self.checkout('k8s')} remote set-url origin {alias_url('k8s')}"), detail)
        self.assertNotIn("-- fix:", detail)
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 28 of 30 checks passed; 2 failed: juniper-k8s origin, juniper-recurrence origin; DRY-RUN: would rewrite 2 origins, nothing written")
        self.assertEqual(self.config_bytes(), before)
        self.assertEqual({name: os.stat(self.checkout(name) / ".git" / "config").st_mtime_ns for name in ACTIVE}, mtimes)
        self.assertEqual(self.set_url_calls(), [])
        self.assertEqual(self.persisted("k8s"), R_G2A_URL)

    def test_fix_leaves_ssh_and_key_failures_to_the_owner(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.unrecord("k8s")
        self.record("ml", addkeystoagent="true")
        self.key("recurrence").chmod(0o644)
        self.key("cascor").unlink()
        config_text = "Host github_juniper-ml\n  AddKeysToAgent yes\n"
        self.ssh_config.write_text(config_text, encoding="utf-8")
        before = self.ssh_tree()
        proc = self.run_check("--fix")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.row(proc, "k8s", "origin")[0], "FIXED")
        self.assertTrue(self.row(proc, "k8s", "alias")[1].endswith(f"-- fix: {SETUP_HINT} k8s"))
        self.assertTrue(self.row(proc, "ml", "alias")[1].endswith("set AddKeysToAgent no"))
        self.assertTrue(self.row(proc, "recurrence", "key")[1].endswith(f"-- fix: chmod 600 {self.key('recurrence')}"))
        self.assertTrue(self.row(proc, "cascor", "key")[1].endswith(f"-- fix: {SETUP_HINT} cascor"))
        self.assertEqual(self.not_passing(proc), {("juniper-k8s", "origin"), ("juniper-k8s", "alias"), ("juniper-ml", "alias"), ("juniper-recurrence", "key"), ("juniper-cascor", "key")})
        self.assertEqual(self.ssh_tree(), before, "--fix never edits the ssh config, chmods or creates a key")
        self.assertEqual(self.ssh_config.read_text(encoding="utf-8"), config_text)

    def test_fix_refuses_an_origin_that_names_another_repository(self) -> None:
        cases = {
            "another owner": "git@github.com:someone/juniper-k8s.git",
            "another repository": "git@github.com:pcalnon/juniper-ml.git",
            "another host": "git@gitlab.com:pcalnon/juniper-k8s.git",
            "a local mirror": str(self.base / "mirrors" / "juniper-k8s.git"),
        }
        for label, url in cases.items():
            with self.subTest(label):
                self.set_origin("k8s", url)
                proc = self.run_check("--fix", "--repo", "k8s")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn("names another repository; --fix refused", self.row(proc, "k8s", "origin")[1])
                self.assertEqual(self.persisted("k8s"), url)
        self.assertEqual(self.set_url_calls(), [])

    def test_fix_rewrites_every_transport_of_the_same_repository(self) -> None:
        forms = (
            R_G2A_URL,
            "https://github.com/pcalnon/juniper-k8s",
            "https://github.com/pcalnon/juniper-k8s.git/",
            "ssh://git@github.com/pcalnon/juniper-k8s.git",
            "ssh://git@ssh.github.com:443/pcalnon/juniper-k8s.git",
            "git@github_juniper-ml:pcalnon/juniper-k8s.git",
            "git@github_juniper-k8s:pcalnon/juniper-k8s",
            "git@github.com:PCalnon/Juniper-K8s.git",
        )
        for url in forms:
            with self.subTest(url=url):
                self.set_origin("k8s", url)
                proc = self.run_check("--fix", "--repo", "k8s")
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertEqual(self.persisted("k8s"), alias_url("k8s"))

    def test_fix_rereads_the_persisted_origin(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        proc = self.run_check("--fix", "--repo", "k8s", STUB_GIT_MODE="noop-set-url")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"--fix ran git remote set-url, but the persisted origin is {R_G2A_URL!r}", self.row(proc, "k8s", "origin")[1])

    def test_fix_reports_a_failed_set_url(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        proc = self.run_check("--fix", "--repo", "k8s", STUB_GIT_MODE="fail-set-url")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("--fix: git remote set-url failed (exit 4): error: could not lock config file", self.row(proc, "k8s", "origin")[1])

    def test_fix_does_not_add_a_missing_origin(self) -> None:
        self.git("-C", str(self.checkout("data")), "remote", "remove", "origin")
        proc = self.run_check("--fix", "--repo", "data")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.persisted("data"), "")
        self.assertFalse([call for call in self.calls(self.git_log) if " remote add " in f" {call} "])

    def test_fix_respects_the_repo_filter(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.set_origin("recurrence", R_G2B_URL)
        proc = self.run_check("--fix", "--repo", "k8s")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.persisted("k8s"), alias_url("k8s"))
        self.assertEqual(self.persisted("recurrence"), R_G2B_URL)

    def test_fix_json_records_the_rewrite(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        dry = json.loads(self.run_check("--fix", "--dry-run", "--json", "--repo", "k8s").stdout)
        origin = dry["repos"][0]["checks"]["origin"]
        self.assertEqual((dry["mode"], dry["exit_code"], origin["status"]), ("fix-dry-run", 1, "fail"))
        self.assertEqual(origin["fix"], {"from": R_G2A_URL, "to": alias_url("k8s"), "applied": False, "error": None})
        done = json.loads(self.run_check("--fix", "--json", "--repo", "k8s").stdout)
        origin = done["repos"][0]["checks"]["origin"]
        self.assertEqual((done["mode"], done["exit_code"], origin["status"], origin["ok"], origin["url"]), ("fix", 0, "fixed", True, alias_url("k8s")))
        self.assertEqual(origin["fix"], {"from": R_G2A_URL, "to": alias_url("k8s"), "applied": True, "error": None})


class RepositoryVariablesTest(_Fixture):
    """git exports GIT_DIR and its relatives to hooks. None of them may redirect a read or a --fix."""

    def setUp(self) -> None:
        super().setUp()
        decoy = self.base / "decoy"
        self.git("init", "-q", str(decoy))
        self.git("-C", str(decoy), "remote", "add", "origin", "git@github.com:pcalnon/juniper-decoy.git")
        self.decoy_config = decoy / ".git" / "config"
        self.decoy_bytes = self.decoy_config.read_bytes()
        self.leaky = {
            "GIT_DIR": str(decoy / ".git"),
            "GIT_WORK_TREE": str(decoy),
            "GIT_COMMON_DIR": str(decoy / ".git"),
            "GIT_INDEX_FILE": str(decoy / ".git" / "index"),
            "GIT_OBJECT_DIRECTORY": str(decoy / ".git" / "objects"),
            "GIT_PREFIX": "",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "remote.origin.url",
            "GIT_CONFIG_VALUE_0": alias_url("k8s"),
            "GIT_CONFIG_PARAMETERS": f"'remote.origin.url'='{alias_url('k8s')}'",
        }
        self.set_origin("k8s", R_G2A_URL)

    def test_repository_variables_do_not_redirect_the_checks(self) -> None:
        proc = self.run_check(**self.leaky)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.not_passing(proc), {("juniper-k8s", "origin")})
        self.assertIn(f"origin {R_G2A_URL!r} bypasses the alias", self.row(proc, "k8s", "origin")[1])

    def test_repository_variables_do_not_redirect_fix(self) -> None:
        proc = self.run_check("--fix", **self.leaky)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(self.persisted("k8s"), alias_url("k8s"))
        self.assertEqual(self.decoy_config.read_bytes(), self.decoy_bytes)


class PrePushHookTest(_Fixture):
    """G6 runs the check from git's pre-push hook. From a linked worktree, git exports GIT_DIR."""

    def setUp(self) -> None:
        super().setUp()
        self.remote = self.base / "pushed.git"
        self.git("init", "--bare", "-q", str(self.remote))
        pusher = self.base / "pusher"
        self.git("init", "-q", str(pusher))
        (pusher / "README.md").write_text("pusher\n", encoding="utf-8")
        self.git("-C", str(pusher), "add", "README.md")
        self.git("-C", str(pusher), "commit", "-q", "-m", "seed")
        self.git("-C", str(pusher), "remote", "add", "origin", str(self.remote))
        self.linked = self.base / "linked"
        self.git("-C", str(pusher), "worktree", "add", "-q", "-b", "work", str(self.linked))
        hooks = pusher / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        _write_exe(hooks / "pre-push", PRE_PUSH_HOOK)
        self.hook_out = self.base / "hook.out"
        self.hook_naive = self.base / "hook.naive"
        self.hook_git_dir = self.base / "hook.git_dir"

    def push(self) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        del env["JUNIPER_ROOT"]  # G6 passes no --root; the default root under HOME is the fixture's
        env.update(HOOK_PYTHON=sys.executable, HOOK_SCRIPT=str(SCRIPT_PATH), HOOK_ROOT=str(self.root), HOOK_OUT=str(self.hook_out), HOOK_NAIVE=str(self.hook_naive), HOOK_GIT_DIR=str(self.hook_git_dir))
        return subprocess.run([_Template.git, "-C", str(self.linked), "push", "-q", "origin", "HEAD:refs/heads/work"], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def pushed(self) -> bool:
        return self.git("--git-dir", str(self.remote), "rev-parse", "--verify", "-q", "refs/heads/work", check=False).returncode == 0

    def test_the_hook_reads_each_checkouts_own_origin(self) -> None:
        self.ssh_config.write_text("Host github_juniper-k8s\n  HostName github.com\n", encoding="utf-8")
        proc = self.push()
        out = self.hook_out.read_text(encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr + out)
        self.assertEqual(parse_report(out)[1], "summary: 30 of 30 checks passed")
        self.assertTrue(self.pushed())
        # Negative control: git did export GIT_DIR, and under it a naive read returns the pushing repo's origin.
        self.assertTrue(self.hook_git_dir.read_text(encoding="utf-8").strip().endswith(os.path.join("worktrees", "linked")))
        self.assertEqual(self.hook_naive.read_text(encoding="utf-8").strip(), str(self.remote))

    def test_the_hook_blocks_a_push_while_an_origin_bypasses_the_alias(self) -> None:
        self.ssh_config.write_text("Host github_juniper-k8s\n  HostName github.com\n", encoding="utf-8")
        self.set_origin("k8s", R_G2A_URL)
        proc = self.push()
        out = self.hook_out.read_text(encoding="utf-8")
        self.assertNotEqual(proc.returncode, 0, out)
        self.assertEqual(parse_report(out)[1], "summary: 29 of 30 checks passed; 1 failed: juniper-k8s origin")
        self.assertFalse(self.pushed())

    def test_the_hook_passes_on_a_host_without_aliases(self) -> None:
        proc = self.push()
        out = self.hook_out.read_text(encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr + out)
        self.assertEqual(out, f"skipped: no github_juniper-* Host alias in {self.ssh_config}\n")
        self.assertTrue(self.pushed())


class IfConfiguredTest(_Fixture):
    def skip_line(self, path: Path) -> str:
        return f"skipped: no github_juniper-* Host alias in {path}\n"

    def test_no_ssh_config_skips_without_running_git_or_ssh(self) -> None:
        proc = self.run_check("--if-configured", STUB_GIT_MODE="forbid")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout, self.skip_line(self.ssh_config))
        self.assertEqual(proc.stderr, "")
        self.assertEqual(self.calls(self.git_log), [])
        self.assertEqual(self.calls(self.ssh_log), [])

    def test_a_config_without_an_alias_host_line_skips(self) -> None:
        texts = {
            "empty": "",
            "other hosts": "Host github.com\n  User git\n\nHost *\n  ServerAliveInterval 60\n",
            "commented alias": "# Host github_juniper-ml\n#Host github_juniper-k8s\n  # Host github_juniper-data\n",
            "alias in a trailing comment": "Host bastion # github_juniper-ml (retired)\n",
            "alias in a trailing comment, no space": "Host bastion #github_juniper-ml\n",
            "alias outside a Host line": "Host *\n  IdentityFile ~/.ssh/id_ed25519_github_juniper-ml\n",
            "HostName, not Host": "Host gh\n  HostName github_juniper-ml\n",
            "negated pattern": "Host !github_juniper-ml *.example.invalid\n",
        }
        for label, text in texts.items():
            with self.subTest(label):
                self.ssh_config.write_text(text, encoding="utf-8")
                proc = self.run_check("--if-configured", STUB_GIT_MODE="forbid")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout, self.skip_line(self.ssh_config))
        self.assertEqual(self.calls(self.git_log), [])

    def test_an_alias_host_line_runs_every_check(self) -> None:
        texts = {
            "plain": "Host github_juniper-ml\n",
            "lower case with =": "host=github_juniper-ml\n",
            "indented, several patterns": "  HOST  bastion github_juniper-k8s\n",
            "quoted": 'Host "github_juniper-ml"\n',
            "wildcard": "Host github_juniper-*\n",
            "before a trailing comment": "Host github_juniper-ml # the ml deploy key\n",
            "after other blocks": "Host github.com\n  User git\n\nHost github_juniper-recurrence\n  HostName github.com\n",
        }
        for label, text in texts.items():
            with self.subTest(label):
                self.ssh_config.write_text(text, encoding="utf-8")
                proc = self.run_check("--if-configured", "--repo", "ml")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(parse_report(proc.stdout)[1], "summary: 3 of 3 checks passed")
        self.assertEqual(parse_report(self.run_check("--if-configured").stdout)[1], "summary: 30 of 30 checks passed")

    def test_a_configured_host_still_fails_on_a_defect(self) -> None:
        self.ssh_config.write_text("Host github_juniper-k8s\n", encoding="utf-8")
        self.set_origin("k8s", R_G2A_URL)
        proc = self.run_check("--if-configured")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual(self.not_passing(proc), {("juniper-k8s", "origin")})

    def test_the_ssh_config_option_names_the_file(self) -> None:
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        named = elsewhere / "ssh_config"
        named.write_text("Host github_juniper-ml\n", encoding="utf-8")
        proc = self.run_check("--if-configured", "--ssh-config", str(named))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(parse_report(proc.stdout)[1], "summary: 30 of 30 checks passed", "an alias in the named file runs the checks")
        self.ssh_config.write_text("Host github_juniper-ml\n", encoding="utf-8")
        missing = elsewhere / "missing"
        proc = self.run_check("--if-configured", "--ssh-config", str(missing), STUB_GIT_MODE="forbid")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout, self.skip_line(missing), "a named file that does not exist skips, even with an alias in ~/.ssh/config")

    def test_an_unreadable_ssh_config_exits_2(self) -> None:
        self.ssh_config.mkdir()
        proc = self.run_check("--if-configured", STUB_GIT_MODE="forbid")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(f"ERROR: cannot read the ssh config {self.ssh_config}", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_the_ssh_config_is_not_read_without_if_configured(self) -> None:
        # A directory where the config belongs cannot be read as text, so only --if-configured may try.
        self.ssh_config.mkdir()
        proc = self.run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_skip_in_json(self) -> None:
        proc = self.run_check("--if-configured", "--json", STUB_GIT_MODE="forbid")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(set(doc), TOP_KEYS)
        reason = f"no github_juniper-* Host alias in {self.ssh_config}"
        expected = {"skipped": True, "skip_reason": reason, "ok": True, "exit_code": 0, "summary": f"skipped: {reason}", "failures": [], "repos": [], "mode": "check"}
        self.assertEqual({key: doc[key] for key in expected}, expected)


class JsonTest(_Fixture):
    def test_the_schema_of_a_clean_run(self) -> None:
        proc = self.run_check("--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(set(doc), TOP_KEYS)
        head = {"schema": 1, "mode": "check", "root": str(self.root), "ssh_config": str(self.ssh_config), "skipped": False, "skip_reason": None, "ok": True, "exit_code": 0, "failures": [], "summary": "summary: 30 of 30 checks passed"}
        self.assertEqual({key: doc[key] for key in head}, head)
        self.assertEqual([repo["repo"] for repo in doc["repos"]], [f"juniper-{name}" for name in ACTIVE])
        for repo in doc["repos"]:
            self.assertEqual(set(repo), REPO_KEYS)
            self.assertEqual(list(repo["checks"]), list(CHECKS))
            self.assertIs(repo["ok"], True)
            for name, check in repo["checks"].items():
                self.assertEqual(set(check), CHECK_KEYS[name], name)
                self.assertEqual((check["status"], check["ok"], check["remediation"]), ("pass", True, None))
        k8s = doc["repos"][ACTIVE.index("k8s")]
        self.assertEqual((k8s["checkout"], k8s["alias"]), (str(self.checkout("k8s")), "github_juniper-k8s"))
        origin, alias, key = (k8s["checks"][name] for name in CHECKS)
        self.assertEqual((origin["expected_url"], origin["url"], origin["pushurls"], origin["fix"]), (alias_url("k8s"), alias_url("k8s"), [], None))
        self.assertEqual(
            (alias["hostname"], alias["identityfile"], alias["identitiesonly"], alias["addkeystoagent"], alias["expected_identityfile"]),
            ("github.com", ["~/.ssh/id_ed25519_github_juniper-k8s"], "yes", "false", str(self.key("k8s"))),
        )
        self.assertEqual((key["path"], key["exists"], key["regular_file"], key["mode"]), (str(self.key("k8s")), True, True, "600"))

    def test_failures_are_listed_by_repo_and_check(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.record("ml", addkeystoagent="true")
        self.key("recurrence").chmod(0o644)
        self.key("cascor").unlink()
        proc = self.run_check("--json")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertEqual((doc["ok"], doc["exit_code"]), (False, 1))
        self.assertEqual(
            doc["failures"],
            [
                {"repo": "juniper-cascor", "check": "key", "status": "fail"},
                {"repo": "juniper-k8s", "check": "origin", "status": "fail"},
                {"repo": "juniper-ml", "check": "alias", "status": "fail"},
                {"repo": "juniper-recurrence", "check": "key", "status": "fail"},
            ],
        )
        repos = {repo["repo"]: repo for repo in doc["repos"]}
        self.assertEqual(repos["juniper-k8s"]["checks"]["origin"]["url"], R_G2A_URL)
        self.assertIn("remote set-url origin", repos["juniper-k8s"]["checks"]["origin"]["remediation"])
        self.assertEqual(repos["juniper-ml"]["checks"]["alias"]["addkeystoagent"], "true")
        self.assertEqual(repos["juniper-recurrence"]["checks"]["key"]["mode"], "644")
        self.assertEqual(repos["juniper-recurrence"]["checks"]["key"]["remediation"], f"chmod 600 {self.key('recurrence')}")
        self.assertEqual((repos["juniper-cascor"]["checks"]["key"]["exists"], repos["juniper-cascor"]["checks"]["key"]["mode"]), (False, None))
        self.assertIs(repos["juniper-canopy"]["ok"], True)
        self.assertIs(repos["juniper-k8s"]["ok"], False)

    def test_an_error_is_listed_with_its_status(self) -> None:
        proc = self.run_check("--json", STUB_SSH_FAIL="github_juniper-data")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertEqual((doc["exit_code"], doc["failures"]), (2, [{"repo": "juniper-data", "check": "alias", "status": "error"}]))

    def test_every_emitted_key_is_documented_in_the_module_docstring(self) -> None:
        doc = ast.get_docstring(ast.parse(SCRIPT_PATH.read_text(encoding="utf-8"))) or ""
        documented = TOP_KEYS | REPO_KEYS | FIX_KEYS | set().union(*CHECK_KEYS.values())
        for key in sorted(documented):
            with self.subTest(key=key):
                self.assertIn(f'"{key}"', doc)


class ReadContractTest(_Fixture):
    """The script stats keys and never opens them. It reads the ssh config only under --if-configured."""

    def run_audited(self, *args: str) -> tuple[subprocess.CompletedProcess[str], list[tuple[str, str, str]]]:
        log = self.base / "audit.log"
        log.unlink(missing_ok=True)
        env = self.env.copy()
        env["AUDIT_LOG"] = str(log)
        proc = subprocess.run([sys.executable, "-c", AUDIT_WRAPPER, str(SCRIPT_PATH), *args], cwd=self.cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        events: list[tuple[str, str, str]] = []
        for line in log.read_text(encoding="utf-8").splitlines():
            event, path, mode = line.split("\t", 2)
            events.append((event, os.path.realpath(path), mode))
        self.assertIn(("open", os.path.realpath(f"{log}.sentinel"), "'w'"), events, "the audit hook is not live")
        return proc, events

    def under(self, path: str, directory: Path) -> bool:
        top = os.path.realpath(directory)
        return path == top or path.startswith(top + os.sep)

    def test_keys_and_the_ssh_config_are_never_opened_without_if_configured(self) -> None:
        self.ssh_config.write_text("Host github_juniper-ml\n", encoding="utf-8")
        self.key("recurrence").chmod(0o644)
        self.set_origin("k8s", R_G2A_URL)
        for args in ((), ("--fix",)):
            with self.subTest(args=args):
                proc, events = self.run_audited(*args)
                self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
                self.assertEqual([event for event in events if self.under(event[1], self.ssh_dir)], [])
                changes = [event for event in events if event[0] != "open" and self.under(event[1], self.base)]
                self.assertEqual(changes, [], "the script itself changes no file; --fix writes only through git")

    def test_if_configured_opens_only_the_ssh_config_and_only_to_read_it(self) -> None:
        self.ssh_config.write_text("Host github_juniper-ml\n", encoding="utf-8")
        proc, events = self.run_audited("--if-configured")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual([event for event in events if self.under(event[1], self.ssh_dir)], [("open", os.path.realpath(self.ssh_config), "'r'")])


class UsageTest(_Fixture):
    def test_help_exits_0_without_running_anything(self) -> None:
        proc = self.run_check("--help", STUB_GIT_MODE="forbid")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("usage:", proc.stdout)
        self.assertIn("--if-configured", proc.stdout)
        self.assertEqual((self.calls(self.git_log), self.calls(self.ssh_log)), ([], []))

    def test_bad_arguments_exit_2_before_any_git_or_ssh(self) -> None:
        cases = {
            "unknown option": ["--frobnicate"],
            "repo without a value": ["--repo"],
            "root without a value": ["--root"],
            "unknown repo": ["--repo", "bogus"],
            "empty short name": ["--repo", "juniper-"],
            "path traversal": ["--repo", "../k8s"],
            "upper case": ["--repo", "K8S"],
            "archived repo": ["--repo", "legacy"],
            "archived repo, full name": ["--repo", "juniper-legacy"],
            "dry run without fix": ["--dry-run"],
            "fix and check together": ["--fix", "--check"],
            "ssh config without if-configured": ["--ssh-config", "x"],
            "a positional argument": ["k8s"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                proc = self.run_check(*argv, STUB_GIT_MODE="forbid")
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertTrue(proc.stderr.startswith("ERROR: "), proc.stderr)
                self.assertIn("Run with --help for usage.", proc.stderr)
                self.assertEqual(proc.stdout, "")
        self.assertEqual((self.calls(self.git_log), self.calls(self.ssh_log)), ([], []))

    def test_the_archive_is_refused_by_name(self) -> None:
        proc = self.run_check("--repo", "legacy")
        self.assertIn("ERROR: juniper-legacy is an archive, not a git checkout; it is never checked", proc.stderr)

    def test_the_repo_filter_takes_short_and_full_names(self) -> None:
        proc = self.run_check("--repo", "recurrence", "--repo", "juniper-k8s")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        rows, summary = parse_report(proc.stdout)
        self.assertEqual(list(rows), [(f"juniper-{name}", check) for name in ("k8s", "recurrence") for check in CHECKS])
        self.assertEqual(self.calls(self.ssh_log), ["-G github_juniper-k8s", "-G github_juniper-recurrence"])
        self.assertEqual(summary, "summary: 6 of 6 checks passed")

    def test_a_repeated_repo_is_checked_once(self) -> None:
        proc = self.run_check("--repo", "k8s", "--repo", "juniper-k8s")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(len(parse_report(proc.stdout)[0]), 3)

    def test_the_repo_filter_scopes_the_verdict(self) -> None:
        self.set_origin("k8s", R_G2A_URL)
        self.assertEqual(self.run_check("--repo", "ml").returncode, 0)
        self.assertEqual(self.run_check("--repo", "ml", "--repo", "k8s").returncode, 1)

    def test_root_precedence(self) -> None:
        missing = self.base / "no-such-root"
        env = self.env.copy()
        del env["JUNIPER_ROOT"]
        cases = [
            ("the default is under HOME", env, [], 0),
            ("JUNIPER_ROOT is honoured", RedactedEnv(env, JUNIPER_ROOT=str(missing)), [], 2),
            ("--root beats JUNIPER_ROOT", RedactedEnv(env, JUNIPER_ROOT=str(missing)), ["--root", str(self.root)], 0),
        ]
        for label, case_env, argv, code in cases:
            with self.subTest(label):
                proc = subprocess.run([sys.executable, str(SCRIPT_PATH), *argv], cwd=self.cwd, env=case_env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
                self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
                if code == 2:
                    self.assertIn(f"ERROR: the Juniper root {missing} is not a directory", proc.stderr)

    def test_a_missing_git_or_ssh_exits_2(self) -> None:
        for var in ("GIT", "SSH"):
            with self.subTest(var):
                proc = self.run_check(**{var: str(self.base / "no-such-program")})
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(f"ERROR: {var.lower()} not found ({var}={self.base / 'no-such-program'})", proc.stderr)
                self.assertEqual(proc.stdout, "")
        self.assertEqual((self.calls(self.git_log), self.calls(self.ssh_log)), ([], []))

    def test_the_default_programs_come_from_path(self) -> None:
        tools = self.base / "tools"
        tools.mkdir()
        _write_exe(tools / "ssh", SSH_STUB)
        _write_exe(tools / "git", GIT_WRAPPER)
        env = self.env.copy()
        del env["GIT"], env["SSH"]
        env["PATH"] = f"{tools}{os.pathsep}{env['PATH']}"
        proc = subprocess.run([sys.executable, str(SCRIPT_PATH)], cwd=self.cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(self.calls(self.ssh_log)), len(ACTIVE))
        self.assertIn(f"-C {self.checkout('k8s')} config --get remote.origin.url", self.calls(self.git_log))


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


class SourceContractTest(unittest.TestCase):
    """Static pins on the script's source."""

    text: str
    tree: ast.Module

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def string_constants(self) -> set[str]:
        return {node.value for node in ast.walk(self.tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}

    def test_the_only_file_read_is_the_ssh_config_line_match(self) -> None:
        readers = {"open", "read_text", "read_bytes", "fdopen", "open_code"}
        owners = [fn.name for fn in ast.walk(self.tree) if isinstance(fn, ast.FunctionDef) for node in ast.walk(fn) if isinstance(node, ast.Call) and _call_name(node) in readers]
        self.assertEqual(owners, ["ssh_config_has_alias"])
        self.assertEqual(sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.Call) and _call_name(node) in readers), 1, "no read outside a function either")

    def test_the_script_changes_no_file_itself(self) -> None:
        writers = {"chmod", "lchmod", "fchmod", "chown", "write_text", "write_bytes", "unlink", "remove", "rename", "replace", "mkdir", "makedirs", "symlink", "symlink_to", "rmtree", "copy", "copy2", "copyfile", "move", "touch", "truncate", "utime"}
        self.assertEqual(sorted({_call_name(node) for node in ast.walk(self.tree) if isinstance(node, ast.Call)} & writers), [])

    def test_ssh_is_only_asked_for_its_configuration(self) -> None:
        constants = self.string_constants()
        self.assertIn("-G", constants)
        for probe in ("-T", "ssh-add", "ssh-keygen", "gh", "gpg", "gpg2", "--card-status", "-K"):
            self.assertNotIn(probe, constants, "credential probes belong to the owner's checklist (plan §14.1)")

    def test_the_origin_is_read_from_config_not_get_url(self) -> None:
        self.assertIn('"config", "--get", "remote.origin.url"', self.text)
        self.assertNotIn("get-url", self.string_constants())

    def test_the_repository_variable_floor_names_what_hooks_export(self) -> None:
        assigned = next(node for node in ast.walk(self.tree) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GIT_LOCAL_ENV_VARS" for t in node.targets))
        floor = {node.value for node in ast.walk(assigned.value) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertLessEqual({"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_PREFIX", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"}, floor)
        self.assertIn('"rev-parse", "--local-env-vars"', self.text, "the installed git's own list is added at run time")

    def test_the_programs_are_overridable(self) -> None:
        self.assertIn('os.environ.get("GIT") or "git"', self.text)
        self.assertIn('os.environ.get("SSH") or "ssh"', self.text)

    def test_no_host_specific_home_literal(self) -> None:
        self.assertNotRegex(self.text, r"/Users/|/home/", "use a $HOME-relative path (plan D12)")

    def test_the_docstring_carries_the_contract(self) -> None:
        doc = ast.get_docstring(self.tree) or ""
        for needle in ("R-G2a", "R-G2b", "R-G2c", "Exit codes", "JSON schema", "--if-configured", "never opens a key", "GIT_DIR", "bash util/juniper_repo_ssh_setup.bash <repo>", "chmod 600 <key>", "AddKeysToAgent no"):
            self.assertIn(needle, doc)

    def test_flake8_clean_when_available(self) -> None:
        if importlib.util.find_spec("flake8") is None:
            self.skipTest("flake8 not installed (util/ is outside the pre-commit Python hooks, so this is the lint gate where it runs)")
        proc = subprocess.run([sys.executable, "-m", "flake8", "--max-line-length=512", "--extend-ignore=E203,W503", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
