#!/usr/bin/env python3
"""Hermetic gate for util/juniper_clone.bash (turing bring-up plan task A4, regression R-A4).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The helper it replaces (``util/git_clone_with_specified_id.bash``, which rode the unsigned branch of
juniper-ml#2222 and never reached main) cloned with ``GIT_SSH_COMMAND="ssh -i <key>" git clone
git@github.com:...``. The override lasted one clone; the persisted origin bypassed the
``github_juniper-<repo>`` Host alias, and every later fetch offered the wrong identity. That is how
juniper-k8s's origin broke on turing (``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``
§4.1).

The clone cases run real ``git``. A ``url.<local bare repo>.insteadOf`` entry in an isolated global
config redirects the alias URL to a local bare repository, so nothing touches the network or ssh, and
the persisted ``remote.origin.url`` is still the alias URL: insteadOf rewrites only at fetch time.
``ssh`` is a stub that answers ``ssh -G`` and refuses anything else.

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "juniper_clone.bash"
OLD_HELPER = REPO_ROOT / "util" / "git_clone_with_specified_id.bash"
TIMEOUT_SECONDS = 60

ALIAS_URL = "git@github_juniper-k8s:pcalnon/juniper-k8s.git"
BYPASS_URL = "git@github.com:pcalnon/juniper-k8s.git"

SSH_STUB = """\
#!/bin/bash
# ssh stub: answers `ssh -G <alias>` only. Aliases named in STUB_SSH_ALIASES resolve to
# ${STUB_SSH_HOSTNAME:-github.com}; anything else resolves to itself, as an undefined alias does.
printf '%s\\n' "$*" >> "$STUB_SSH_LOG"
if [ "${STUB_SSH_FAIL:-0}" = "1" ]; then
    echo "ssh: stub failure" >&2
    exit 255
fi
if [ "$1" != "-G" ] || [ "$#" -ne 2 ]; then
    echo "ssh stub: refusing argv: $*" >&2
    exit 99
fi
case " ${STUB_SSH_ALIASES:-} " in
    *" $2 "*) printf 'host %s\\nhostname %s\\nuser git\\n' "$2" "${STUB_SSH_HOSTNAME:-github.com}" ;;
    *) printf 'host %s\\nhostname %s\\nuser nobody\\n' "$2" "$2" ;;
esac
"""

# Runs the real git, then -- after a clone -- persists the alias-bypassing origin, the way the old
# helper left it. The script under test must catch that.
BAD_ORIGIN_GIT_WRAPPER = f"""\
#!/bin/bash
"$REAL_GIT" "$@" || exit $?
if [ "$1" = "clone" ]; then
    for last in "$@"; do :; done
    "$REAL_GIT" -C "$last" config remote.origin.url '{BYPASS_URL}'
fi
"""

# A git that must never run: --dry-run and every refusal happen before any git call.
FORBIDDEN_GIT = """\
#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_GIT_LOG"
exit 97
"""


def _write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


class _Fixture(unittest.TestCase):
    """Scratch HOME, JUNIPER_ROOT, a local bare 'remote', an ssh stub and an isolated git config."""

    def setUp(self) -> None:
        self.real_git = shutil.which("git")
        if self.real_git is None:
            self.skipTest("git not installed")
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.home = base / "home"
        self.juniper_root = base / "juniper"
        self.cwd = base / "cwd"
        self.bin = base / "bin"
        for d in (self.home, self.juniper_root, self.cwd, self.bin):
            d.mkdir()
        self.bare = base / "remote" / "juniper-k8s.git"
        self.bare.parent.mkdir()
        self.gitconfig = base / "gitconfig"
        self.ssh_log = base / "ssh.log"
        self.git_log = base / "git.log"
        self.ssh_stub = _write_exe(self.bin / "ssh-stub", SSH_STUB)
        self.forbidden_git = _write_exe(self.bin / "git-forbidden", FORBIDDEN_GIT)
        self.env = self._base_env()
        subprocess.run([self.real_git, "init", "--bare", "-q", str(self.bare)], env=self.env, check=True, capture_output=True, timeout=TIMEOUT_SECONDS)
        self.map_url(ALIAS_URL, self.bare)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _base_env(self) -> RedactedEnv:
        env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        env.update(
            HOME=str(self.home),
            PWD=str(self.cwd),
            JUNIPER_ROOT=str(self.juniper_root),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=str(self.gitconfig),
            GIT_TERMINAL_PROMPT="0",
            SSH=str(self.ssh_stub),
            STUB_SSH_LOG=str(self.ssh_log),
            STUB_SSH_ALIASES="github_juniper-k8s github_juniper-recurrence",
            STUB_GIT_LOG=str(self.git_log),
        )
        return env

    def map_url(self, url: str, target: Path) -> None:
        with self.gitconfig.open("a", encoding="utf-8") as fh:
            fh.write(f'[url "{target}"]\n\tinsteadOf = {url}\n')

    def run_script(self, *args: str, **env_overrides: str) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env.update(env_overrides)
        return subprocess.run(
            ["/bin/bash", str(SCRIPT_PATH), *args],
            cwd=self.cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )

    def persisted_origin(self, checkout: Path) -> str:
        proc = subprocess.run(
            [str(self.real_git), "-C", str(checkout), "config", "--get", "remote.origin.url"],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return proc.stdout.strip()

    def git_never_ran(self) -> bool:
        return not self.git_log.exists()


class CloneTest(_Fixture):
    def test_clone_persists_the_alias_origin(self) -> None:
        proc = self.run_script("k8s")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        dest = self.juniper_root / "juniper-k8s"
        self.assertTrue((dest / ".git").is_dir())
        self.assertEqual(self.persisted_origin(dest), ALIAS_URL)
        self.assertIn(f"origin {ALIAS_URL}", proc.stdout)

    def test_full_repo_name_is_accepted(self) -> None:
        proc = self.run_script("juniper-k8s")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.persisted_origin(self.juniper_root / "juniper-k8s"), ALIAS_URL)

    def test_dest_option(self) -> None:
        dest = self.cwd / "elsewhere" / "k8s-checkout"
        proc = self.run_script("--dest", str(dest), "k8s")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.persisted_origin(dest), ALIAS_URL)
        self.assertFalse((self.juniper_root / "juniper-k8s").exists())

    def test_ssh_is_used_only_to_resolve_configuration(self) -> None:
        proc = self.run_script("k8s")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.ssh_log.read_text(encoding="utf-8").splitlines(), ["-G github_juniper-k8s"])

    def test_ssh_github_com_alias_is_accepted(self) -> None:
        proc = self.run_script("--dry-run", "k8s", STUB_SSH_HOSTNAME="ssh.github.com")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("-> ssh.github.com", proc.stdout)


class FailureTest(_Fixture):
    def test_clone_failure_exits_1(self) -> None:
        self.gitconfig.write_text("", encoding="utf-8")
        self.map_url(ALIAS_URL, self.bare.parent / "missing.git")
        proc = self.run_script("k8s")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("git clone of", proc.stderr)
        self.assertFalse((self.juniper_root / "juniper-k8s").exists())

    def test_alias_bypassing_persisted_origin_exits_1(self) -> None:
        # R-A4: the exact state the old helper left behind must be caught, not reported as success.
        wrapper = _write_exe(self.bin / "git-bad-origin", BAD_ORIGIN_GIT_WRAPPER)
        proc = self.run_script("k8s", GIT=str(wrapper), REAL_GIT=str(self.real_git))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"persisted origin '{BYPASS_URL}'", proc.stderr)
        self.assertIn(f"expected '{ALIAS_URL}'", proc.stderr)
        self.assertIn("remote set-url origin", proc.stderr)

    def test_alias_that_does_not_resolve_to_github_exits_2(self) -> None:
        proc = self.run_script("k8s", GIT=str(self.forbidden_git), STUB_SSH_ALIASES="github_juniper-ml")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("resolves to 'github_juniper-k8s', not github.com", proc.stderr)
        self.assertIn("util/juniper_repo_ssh_setup.bash k8s", proc.stderr)
        self.assertTrue(self.git_never_ran())

    def test_ssh_config_evaluation_failure_exits_2(self) -> None:
        proc = self.run_script("k8s", GIT=str(self.forbidden_git), STUB_SSH_FAIL="1")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("cannot check the alias", proc.stderr)
        self.assertTrue(self.git_never_ran())

    def test_existing_destination_exits_2_and_is_untouched(self) -> None:
        dest = self.juniper_root / "juniper-k8s"
        dest.mkdir()
        (dest / "keep.txt").write_text("mine\n", encoding="utf-8")
        proc = self.run_script("k8s", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("already exists", proc.stderr)
        self.assertEqual(sorted(p.name for p in dest.iterdir()), ["keep.txt"])
        self.assertTrue(self.git_never_ran())

    def test_dangling_symlink_destination_exits_2(self) -> None:
        (self.juniper_root / "juniper-k8s").symlink_to(self.juniper_root / "gone")
        proc = self.run_script("k8s", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(self.git_never_ran())


class DryRunTest(_Fixture):
    def test_dry_run_writes_nothing_and_runs_no_git(self) -> None:
        proc = self.run_script("--dry-run", "k8s", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"DRY-RUN: would clone {ALIAS_URL}", proc.stdout)
        self.assertIn(str(self.juniper_root / "juniper-k8s"), proc.stdout)
        self.assertFalse((self.juniper_root / "juniper-k8s").exists())
        self.assertTrue(self.git_never_ran())

    def test_owner_option_shapes_the_url(self) -> None:
        proc = self.run_script("--dry-run", "--owner", "someone-else", "recurrence", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("would clone git@github_juniper-recurrence:someone-else/juniper-recurrence.git", proc.stdout)

    def test_default_root_is_home_relative(self) -> None:
        env = self.env.copy()
        del env["JUNIPER_ROOT"]
        env["GIT"] = str(self.forbidden_git)
        proc = subprocess.run(
            ["/bin/bash", str(SCRIPT_PATH), "--dry-run", "k8s"],
            cwd=self.cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(str(self.home / "Development" / "python" / "Juniper" / "juniper-k8s"), proc.stdout)


class UsageTest(_Fixture):
    def test_help_exits_0(self) -> None:
        proc = self.run_script("--help", GIT=str(self.forbidden_git))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Usage:", proc.stdout)
        self.assertTrue(self.git_never_ran())

    def test_bad_arguments_exit_2_before_any_git(self) -> None:
        cases = {
            "no repo": [],
            "unknown option": ["--frobnicate", "k8s"],
            "two repos": ["k8s", "ml"],
            "dest without value": ["k8s", "--dest"],
            "owner without value": ["k8s", "--owner"],
            "path traversal": ["../evil"],
            "uppercase": ["K8s"],
            "shell syntax": ["k8s;id"],
            "empty short name": ["juniper-"],
            "leading dash": ["-k8s"],
            "bad owner": ["--owner", "a/b", "k8s"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                proc = self.run_script(*argv, GIT=str(self.forbidden_git))
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn("ERROR:", proc.stderr)
        self.assertTrue(self.git_never_ran())
        self.assertFalse(self.ssh_log.exists(), "argument errors must be caught before ssh is consulted")


class SourceContractTest(unittest.TestCase):
    """Static pins. Comment lines are excluded; the header names the old defect on purpose."""

    text: str
    code: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.text.splitlines() if not line.lstrip().startswith("#"))

    def test_old_helper_is_not_in_the_tree(self) -> None:
        # A4 replaces it; the B9 re-land of juniper-ml#2222 must not bring it back.
        self.assertFalse(OLD_HELPER.exists(), f"{OLD_HELPER.name} persists an alias-bypassing origin")

    def test_never_overrides_the_ssh_identity_or_bypasses_the_alias(self) -> None:
        self.assertNotIn("GIT_SSH_COMMAND", self.code)
        self.assertIsNone(re.search(r"\bssh\s+-i\b", self.code))
        self.assertNotIn("git@github.com:", self.code)

    def test_origin_is_read_from_config_not_get_url(self) -> None:
        # `git remote get-url` expands insteadOf, which could report a rewritten URL over a bad one.
        self.assertIn("config --get remote.origin.url", self.code)
        self.assertNotIn("remote get-url", self.code)

    def test_strict_mode_and_overridable_tools(self) -> None:
        self.assertIn("set -euo pipefail", self.code)
        self.assertIn('GIT="${GIT:-git}"', self.code)
        self.assertIn('SSH="${SSH:-ssh}"', self.code)

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
