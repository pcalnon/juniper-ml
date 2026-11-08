#!/usr/bin/env python3
"""Edges of the D11 signing deny that the main guard table does not name.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies ``git -c commit.gpgsign=true`` and
``git commit -S``, and allows one ``commit.gpgsign=false``. Two holes sit beside that:

* Git's last ``-c`` wins. ``git -c commit.gpgsign=false -c commit.gpgsign=true commit``
  signs (verified on git 2.43: the second assignment is the value ``config --get``
  returns). A guard that stops at the first ``gpgsign`` key would allow the command,
  and the single-off case would stay green.
* ``git pull -S``, ``git am -S``, ``git revert -S``, ``git cherry-pick -S`` and
  ``git commit-tree -S`` are signing forms (``git pull -h`` / ``git am -h`` list
  ``-S, --gpg-sign``). They are on ``GIT_SIGN_SUBCOMMANDS``, but no suite names the
  full flag, so dropping ``pull`` leaves ``git commit -S`` green.

``git commit -mS x`` is a message of ``S`` (git 2.43 committed it unsigned). It must
stay allowed, or the cluster walk is treating every ``S`` as a signature.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - drives the hook as a subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
TIMEOUT_SECONDS = 60

# An earlier off-switch, then an on-switch. Git applies the last -c.
_LATER_ON = (
    "git -c commit.gpgsign=false -c commit.gpgsign=true commit -m x",
    "git -c commit.gpgsign=false -c tag.gpgsign=true tag -a v1 -m x",
    "git -c tag.gpgsign=false -c commit.gpgsign=yes commit -m x",
    "git -c commit.gpgsign=no -c commit.gpgsign=on commit -m x",
)

# The same off-switch alone does not sign. These stay allowed so a deny-everything
# change cannot satisfy the cases above.
_OFF_ALONE = (
    "git -c commit.gpgsign=false commit -m x",
    "git -c tag.gpgsign=off tag -a v1 -m x",
)

# Subcommands whose -S / --gpg-sign creates a signature. None of these spellings are
# in the main guard table.
_SIGNING_SUBCOMMANDS = (
    "git pull -S origin main",
    "git pull --gpg-sign origin main",
    "git am -S mbox",
    "git am --gpg-sign mbox",
    "git revert -S HEAD",
    "git cherry-pick -S abc",
    "git commit-tree -S abc",
    "git commit -Sm -m x",
)

# The same commands with no signing flag, plus a message that merely contains S.
_UNSIGNED = (
    "git pull origin main",
    "git am mbox",
    "git revert HEAD",
    "git cherry-pick abc",
    "git commit-tree abc",
    "git commit -mS x",
)


class GuardSignEdgesTest(unittest.TestCase):
    """PreToolUse payloads against a temp home. The real ``~/.claude`` is never read."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="guard-sign-edges-")
        root = Path(self._tmp.name)
        self.home = root / "home"
        self.repo = root / "repo"
        for name in (".ssh", ".gnupg", ".claude"):
            (self.home / name).mkdir(parents=True)
        self.repo.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _decide(self, command: str) -> tuple[int, str, str]:
        payload = {
            "session_id": "test-session",
            "transcript_path": "/dev/null",
            "hook_event_name": "PreToolUse",
            "permission_mode": "bypassPermissions",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(self.repo),
            "tool_use_id": "toolu_test",
        }
        env = RedactedEnv(os.environ)
        env["JUNIPER_GUARD_HOME"] = str(self.home)
        env["HOME"] = str(self.home)
        env.pop("CLAUDE_PROJECT_DIR", None)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home
            [sys.executable, "-I", str(GUARD)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            cwd=str(self.repo),
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def assert_denied(self, command: str) -> None:
        code, out, err = self._decide(command)
        self.assertEqual(code, 0, "exit %d stderr %s" % (code, err))
        self.assertTrue(out.strip(), "expected a deny, got no output")
        self.assertEqual(out.count("\n"), 1, "a deny is exactly one JSON line")
        decision = json.loads(out)
        spec = decision["hookSpecificOutput"]
        self.assertEqual(spec["permissionDecision"], "deny")
        self.assertIn("GPG-SIGN", spec["permissionDecisionReason"])
        self.assertIn("OWNER-run", spec["permissionDecisionReason"])

    def assert_allowed(self, command: str) -> None:
        code, out, err = self._decide(command)
        self.assertEqual((code, out), (0, ""), "must pass silently; stderr: %s" % err)

    def test_a_later_gpgsign_on_switch_is_denied(self) -> None:
        """The first ``gpgsign=false`` must not hide a later on-switch. Git uses the last ``-c``."""
        for command in _LATER_ON:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_an_off_switch_with_nothing_after_it_stays_allowed(self) -> None:
        for command in _OFF_ALONE:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_pull_am_revert_cherry_pick_and_commit_tree_sign_flags_are_denied(self) -> None:
        for command in _SIGNING_SUBCOMMANDS:
            with self.subTest(command=command):
                self.assert_denied(command)

    def test_the_same_subcommands_without_a_sign_flag_stay_allowed(self) -> None:
        """``git commit -mS x`` is the message ``S``, not ``-S``. Git 2.43 committed it unsigned."""
        for command in _UNSIGNED:
            with self.subTest(command=command):
                self.assert_allowed(command)


if __name__ == "__main__":
    unittest.main()
