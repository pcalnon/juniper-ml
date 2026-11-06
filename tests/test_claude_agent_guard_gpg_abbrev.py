#!/usr/bin/env python3
"""Pin GnuPG long-option abbreviations at the guard's 4-character floor.

``util/claude_agent_guard.py`` treats a long option as a secret or sign option when the
name is an exact table entry, or when it is at least ``GPG_MIN_ABBREV`` (4) characters
and a table entry starts with it. The existing ``tests/test_claude_agent_guard.py`` cases
use full names and longer prefixes (``--list-secret``, ``--card-status``), which stay
denied if that floor moves. This file pins the floor itself, and the exact ``export``
allowance that sits next to it: ``--export`` is a prefix of ``export-secret-keys`` and
must stay allowed, while ``--expo`` must not.

The hook runs as a subprocess with ``JUNIPER_GUARD_HOME`` and ``HOME`` on a temp home.
A deny is one JSON line naming the rule; an allow prints nothing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404 - drives the hook as a subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
OVERRIDE_ENV = "JUNIPER_GUARD_HOME"
PROJECT_DIR_ENV = "CLAUDE_PROJECT_DIR"
_RULE = re.compile(r"Rule ([A-Z0-9-]+):")


class GpgAbbrevFloorTests(unittest.TestCase):
    """Exactly four characters is a prefix; three is not. ``export`` stays exact."""

    _tmp: tempfile.TemporaryDirectory
    home: Path
    repo: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.home = root / "home"
        cls.repo = root / "repo"
        for name in (".ssh", ".gnupg", ".claude"):
            (cls.home / name).mkdir(parents=True)
        cls.repo.mkdir()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def decide(self, command: str) -> tuple[int, str, str]:
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
        env[OVERRIDE_ENV] = str(self.home)
        env["HOME"] = str(self.home)
        env.pop(PROJECT_DIR_ENV, None)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home
            [sys.executable, "-I", str(GUARD)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            cwd=str(self.repo),
            timeout=60,
            check=False,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def assert_denied(self, command: str, rule_id: str) -> None:
        code, out, err = self.decide(command)
        self.assertEqual(code, 0, "%s: exit %d, stderr %s" % (command, code, err))
        self.assertEqual(out.count("\n"), 1, "%s: a deny is one JSON line, got %r" % (command, out))
        decision = json.loads(out)
        reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny", reason)
        named = _RULE.search(reason)
        self.assertIsNotNone(named, reason)
        self.assertEqual(named.group(1), rule_id, "%s: %s" % (command, reason))

    def assert_allowed(self, command: str) -> None:
        code, out, err = self.decide(command)
        self.assertEqual((code, out), (0, ""), "%s must pass silently; stderr: %s" % (command, err))

    def test_four_character_secret_prefix_is_denied(self) -> None:
        """``list`` and ``expo`` are prefixes of secret options; the value after ``=`` does not count."""
        for command in ("gpg --list", "gpg --expo", "gpg --LIST", "gpg --list=keys"):
            with self.subTest(command=command):
                self.assert_denied(command, "GPG-SECRET")

    def test_four_character_sign_prefix_is_denied(self) -> None:
        """``clea`` is not itself a table entry; only the length floor makes it ``clearsign``."""
        self.assert_denied("gpg --clea", "GPG-SIGN")

    def test_three_character_prefix_is_allowed(self) -> None:
        for command in ("gpg --lis", "gpg --exp", "gpg --cle", "gpg --LIS", "gpg --lis=secret"):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_exact_export_stays_allowed(self) -> None:
        """``export`` is a prefix of ``export-secret-keys`` and is allowed only as that exact word."""
        self.assert_allowed("gpg --export KEYID")


if __name__ == "__main__":
    unittest.main()
