#!/usr/bin/env python3
"""Pin the nesting cap in util/claude_agent_guard.py.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``BashAnalyzer._scan`` refuses a command whose shell ``-c`` / ``eval`` /
substitution nesting is deeper than ``MAX_DEPTH``. The comparison is strict:
a depth equal to the cap is still analysed, and one past it fails closed
(exit 2, empty stdout). Each leading ``eval`` adds one depth, so the fixture
stays a few dozen bytes.

The guard's production source is not modified. Payloads go through the hook
the way Claude Code sends them, with ``JUNIPER_GUARD_HOME`` pointed at a temp
directory so the real home is never read.
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
NEST_CAP = 12  # util/claude_agent_guard.py MAX_DEPTH. Hardcoded so raising the constant fails this file.


def _load_guard():
    spec = importlib.util.spec_from_file_location("claude_agent_guard_nest_depth", GUARD)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load %s" % GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _nested_eval(depth: int, command: str) -> str:
    """``depth`` leading evals, then ``command``. The innermost scan runs at that depth."""
    if depth < 0:
        raise ValueError(depth)
    return ("eval " * depth) + command


class NestDepthCapTest(unittest.TestCase):
    """Depth 12 is still judged. Depth 13 is refused before the inner command runs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="guard-nest-depth-")
        cls.home = cls._tmp.name
        cls.guard = _load_guard()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_the_cap_constant_is_twelve(self) -> None:
        self.assertEqual(self.guard.MAX_DEPTH, NEST_CAP)

    def _run(self, command: str) -> tuple:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": self.home,
        }
        env = RedactedEnv(os.environ)
        env["JUNIPER_GUARD_HOME"] = self.home
        env["HOME"] = self.home
        env.pop("CLAUDE_PROJECT_DIR", None)
        proc = subprocess.run(  # nosec B603 - fixed argv, temp home, no shell
            [sys.executable, "-I", str(GUARD)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            cwd=self.home,
            timeout=30,
            check=False,
        )
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def test_exactly_at_the_cap_still_denies_sudo(self) -> None:
        code, out, err = self._run(_nested_eval(NEST_CAP, "sudo id"))
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("\n"), 1, out)
        decision = json.loads(out)
        spec = decision["hookSpecificOutput"]
        self.assertEqual(spec["permissionDecision"], "deny")
        self.assertIn("PRIV-ESCALATION", spec["permissionDecisionReason"])
        self.assertIn("OWNER-run", spec["permissionDecisionReason"])

    def test_exactly_at_the_cap_still_allows_a_harmless_command(self) -> None:
        code, out, err = self._run(_nested_eval(NEST_CAP, "true"))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_one_past_the_cap_fails_closed_and_does_not_allow_sudo(self) -> None:
        code, out, err = self._run(_nested_eval(NEST_CAP + 1, "sudo id"))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("fail closed", err)
        self.assertIn("more than %d deep" % NEST_CAP, err)


if __name__ == "__main__":
    unittest.main()
