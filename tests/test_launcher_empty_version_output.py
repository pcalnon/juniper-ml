#!/usr/bin/env python3
"""Empty Claude Code version output, and claudey keeping a requested debug log.

``parse_model_version_flags`` now prints an error on stderr when ``claude --version``
prints nothing. With ``WTC_DEBUG=1`` that used to be a bare exit 1. A version of one
character still counts: command substitution strips trailing newlines, so ``0\\n`` is
``0`` and a newline alone is empty.

``claude_interactive.bash`` asks ``wake_the_claude.bash`` for the version with debug
off unless the caller already set ``WTC_DEBUG``. ``0`` is that script's TRUE.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
WAKE_SCRIPT = REPO_ROOT / "scripts" / "wake_the_claude.bash"
CLAUDEY_SCRIPT = REPO_ROOT / "scripts" / "claude_interactive.bash"
VERSION_FLAGS = ("-v", "--version", "-V", "--claude-version")


class EmptyVersionOutputTests(unittest.TestCase):
    """An executable ``claude`` that prints no version must say so, and must not start a session."""

    def _run_wake(self, temp_dir: str, flag: str, *, version_stdout: str, version_status: str) -> subprocess.CompletedProcess[str]:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir()
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "--version" ]]; then\n'
            '  printf %s "$VERSION_STDOUT"\n'
            '  exit "$VERSION_STATUS"\n'
            "fi\n"
            '{ echo "__CALL__"; } >> "$CLAUDE_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        env = RedactedEnv(os.environ)
        for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV", "WTC_DEBUG"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["VERSION_STDOUT"] = version_stdout
        env["VERSION_STATUS"] = version_status
        env["WTC_DEBUG"] = "1"
        env["CLAUDE_ARGS_LOG"] = str(Path(temp_dir) / "claude_invocations.log")
        env["WTC_SESSIONS_DIR"] = str(Path(temp_dir) / "sessions")
        env["WTC_LOGS_DIR"] = str(Path(temp_dir) / "logs")
        return subprocess.run(
            ["bash", str(WAKE_SCRIPT), flag],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_no_version_text_is_refused_on_stderr_with_debug_output_off(self) -> None:
        """Empty stdout and a newline alone are no version. Exit 1 names the binary; no session starts.

        A non-zero status from ``claude`` is not what decides this: empty text with exit 0 is still refused.
        ``0`` followed by a newline is a version, including from ``-v``, which used to print this script's version.
        """
        refusals = [(flag, stdout, status) for flag in VERSION_FLAGS for stdout, status in (("", "0"),)]
        refusals.append(("--version", "\n", "0"))
        refusals.append(("--version", "", "3"))
        for flag, version_stdout, version_status in refusals:
            with self.subTest(flag=flag, version_stdout=repr(version_stdout), version_status=version_status), tempfile.TemporaryDirectory() as temp_dir:
                result = self._run_wake(temp_dir, flag, version_stdout=version_stdout, version_status=version_status)
                claude = str(Path(temp_dir) / "bin" / "claude")
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(f'Error: "{claude} --version" printed no version', result.stderr)
                self.assertNotIn("wake_the_claude.bash: ", result.stderr)
                self.assertEqual(result.stdout.strip(), "")
                self.assertFalse((Path(temp_dir) / "claude_invocations.log").exists())

        for flag in ("--version", "-v"):
            with self.subTest(flag=flag, version_stdout="'0\\n'"), tempfile.TemporaryDirectory() as temp_dir:
                result = self._run_wake(temp_dir, flag, version_stdout="0\n", version_status="0")
                claude = str(Path(temp_dir) / "bin" / "claude")
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn(f"{claude} 0", result.stdout)
                self.assertNotIn("printed no version", result.stderr)
                self.assertFalse((Path(temp_dir) / "claude_invocations.log").exists())


class ClaudeyVersionDebugTests(unittest.TestCase):
    """claudey turns debug off for a version request unless the caller already set ``WTC_DEBUG``."""

    def test_an_explicit_debug_request_is_kept_for_the_version(self) -> None:
        """``WTC_DEBUG=0`` (TRUE) still prints ``wake_the_claude.bash``'s debug log. Forcing it off would drop that log."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = Path(temp_dir) / "bin"
            bin_dir.mkdir()
            fake_claude = bin_dir / "claude"
            fake_claude.write_text(
                "#!/usr/bin/env bash\n"
                'if [[ "$1" == "--version" ]]; then echo "claude-test-version"; exit 0; fi\n'
                '{ echo "__CALL__"; } >> "$CLAUDE_ARGS_LOG"\n',
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            env = RedactedEnv(os.environ)
            for var in (
                "CLAUDE_SKIP_PERMISSIONS",
                "CLAUDE_REMOTE_CONTROL",
                "CLAUDE_MODEL",
                "CLAUDE_EFFORT",
                "CLAUDE_ID",
                "CLAUDE_WORKTREE",
                "CLAUDE_PROMPT",
                "CLAUDE_PROMPT_FILE",
                "CLAUDE_PROMPT_PATH",
                "BASH_ENV",
                "ENV",
                "WTC_DEBUG",
            ):
                env.pop(var, None)
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["WTC_DEBUG"] = "0"
            env["CLAUDE_ARGS_LOG"] = str(Path(temp_dir) / "claude_invocations.log")
            env["WTC_SESSIONS_DIR"] = str(Path(temp_dir) / "sessions")
            env["WTC_LOGS_DIR"] = str(Path(temp_dir) / "logs")
            result = subprocess.run(
                ["bash", str(CLAUDEY_SCRIPT), "-v"],
                cwd=temp_dir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("claude-test-version", result.stdout)
            self.assertIn("wake_the_claude.bash: ", result.stderr)
            self.assertFalse((Path(temp_dir) / "claude_invocations.log").exists())


if __name__ == "__main__":
    unittest.main()
