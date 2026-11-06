#!/usr/bin/env python3
"""Pin ANSI-C quoting in util/claude_agent_guard.py.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``tests/test_claude_agent_guard.py`` denies ``cat ~/.$'\\x73'sh/config``. It does
not exercise ``\\u``, ``\\U`` or octal, and it does not pin the U+10FFFF ceiling
in ``_ansi_c``. A code point of exactly 0x10FFFF stays that character, so
``~/.$'\\U0010FFFF'sh`` is not ``.ssh``. One past it (0x110000) is replaced with
``?``, and ``~/.?sh`` is a glob of ``.ssh``. Dropping the out-of-range code
point instead would concatenate to ``~/.sh`` and let the read through.

The guard's production source is not modified. Payloads go through the hook
the way Claude Code sends them, with ``JUNIPER_GUARD_HOME`` pointed at a temp
directory that has its own ``.ssh``, so the real home is never read.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess  # nosec B404 - drives the hook as a subprocess, the same path Claude Code uses
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
# util/claude_agent_guard.py: chr(value) if value <= 0x10FFFF else "?". Hardcoded so the ceiling cannot drift unnoticed.
UNICODE_CEILING = 0x10FFFF


def _load_guard():
    spec = importlib.util.spec_from_file_location("claude_agent_guard_ansi_escapes", GUARD)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load %s" % GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AnsiCEscapeTest(unittest.TestCase):
    """``\\u``, ``\\U`` and octal that spell ``.ssh`` are denied. U+10FFFF is not ``?``."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="guard-ansi-c-")
        cls.home = Path(cls._tmp.name)
        ssh = cls.home / ".ssh"
        ssh.mkdir()
        (ssh / "config").write_text("Host example\n", encoding="utf-8")
        cls.cwd = cls.home / "work"
        cls.cwd.mkdir()
        cls.guard = _load_guard()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _run(self, command: str) -> tuple:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(self.cwd),
        }
        env = RedactedEnv(os.environ)
        env["JUNIPER_GUARD_HOME"] = str(self.home)
        env["HOME"] = str(self.home)
        env.pop("CLAUDE_PROJECT_DIR", None)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home, no shell
            [sys.executable, "-I", str(GUARD)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            cwd=str(self.cwd),
            timeout=30,
            check=False,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def _assert_denied(self, command: str) -> None:
        code, out, err = self._run(command)
        self.assertEqual(err, "", command)
        self.assertEqual(code, 0, command)
        self.assertEqual(out.count("\n"), 1, out)
        spec = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(spec["permissionDecision"], "deny")
        self.assertIn("CRED-PATH-BASH", spec["permissionDecisionReason"])
        self.assertIn("OWNER-run", spec["permissionDecisionReason"])

    def test_unicode_and_octal_escapes_that_spell_ssh_are_denied(self) -> None:
        # Each body is the letter s. The raw command does not contain ".ssh".
        commands = (
            r"cat ~/.$'\u73'sh/config",  # shortest \u
            r"cat ~/.$'\u0073'sh/config",  # four hex digits, the \u maximum
            r"cat ~/.$'\U73'sh/config",  # shortest \U
            r"cat ~/.$'\U00000073'sh/config",  # eight hex digits, the \U maximum
            r"cat ~/.$'\163'sh/config",  # three octal digits, the octal maximum
        )
        for command in commands:
            with self.subTest(command=command):
                self._assert_denied(command)

    def test_the_last_unicode_code_point_does_not_become_a_glob(self) -> None:
        code, out, err = self._run(r"cat ~/.$'\U0010FFFF'sh/config")
        self.assertEqual((code, out, err), (0, "", ""))

    def test_one_past_the_unicode_ceiling_is_a_question_mark_and_matches_ssh(self) -> None:
        self._assert_denied(r"cat ~/.$'\U00110000'sh/config")

    def test_the_decoder_keeps_the_ceiling_and_replaces_one_past_it(self) -> None:
        text, end = self.guard._ansi_c(r"\U0010FFFF'", 0)
        self.assertEqual(text, chr(UNICODE_CEILING))
        self.assertEqual(end, len(r"\U0010FFFF'"))
        text, end = self.guard._ansi_c(r"\U00110000'", 0)
        self.assertEqual(text, "?")
        self.assertEqual(end, len(r"\U00110000'"))


if __name__ == "__main__":
    unittest.main()
