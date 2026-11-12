#!/usr/bin/env python3
"""The caller's ``--`` is a spacer, not the end of this launcher's options.

``scripts/wake_the_claude.bash`` lists ``--`` in ``SPACER_FLAGS`` and consumes
it, then keeps parsing. Flags after it still apply, including
``--dangerously-skip-permissions``, and the spacer is not an argument
``claude`` receives. The script inserts its own ``--`` only immediately before
a prompt. A bare word after the spacer is an unknown flag: the launch stops
and ``claude`` is not started. Treating the spacer as POSIX end-of-options
would either drop a later permissions flag or append the following words to
``claude``'s argv.

``tests/test_wake_the_claude.py`` passes ``--`` only as the missing value of
``--resume``, which returns before this success path runs.

Run: python3 -m unittest -v tests/test_wake_spacer_flags.py
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wake_the_claude.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"


class WakeSpacerFlagTests(unittest.TestCase):
    def _install_fake_claude(self, temp_dir: str) -> tuple[Path, dict[str, str]]:
        root = Path(temp_dir)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        (root / "sessions").mkdir()
        (root / "logs").mkdir()
        invocations_log = root / "claude_invocations.log"
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n"
            "{\n"
            '  echo "__CALL__"\n'
            '  echo "ARGC=$#"\n'
            '  for arg in "$@"; do\n'
            "    printf 'ARG=%s\\n' \"$arg\"\n"
            "  done\n"
            '} >> "$CLAUDE_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        env = RedactedEnv(os.environ)
        for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV", "WTC_DEBUG"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGS_LOG"] = str(invocations_log)
        env["WTC_SESSIONS_DIR"] = str(root / "sessions")
        env["WTC_LOGS_DIR"] = str(root / "logs")
        return invocations_log, env

    def _run(self, args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def _argv(invocations_log: Path) -> list[str]:
        if not invocations_log.exists():
            return []
        args: list[str] = []
        for line in invocations_log.read_text(encoding="utf-8").splitlines():
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    def test_flags_after_the_spacer_still_apply_and_the_spacer_is_not_forwarded(self) -> None:
        """Flags after ``--`` are this script's flags. ``claude`` never receives that spacer.

        With no prompt, the script inserts no ``--`` of its own, so a forwarded spacer would be the
        only one in argv and would hide ``--dangerously-skip-permissions`` from Claude Code.
        """
        cases = (
            (["--", "--dangerously-skip-permissions", "--prompt", "hello"], ["--dangerously-skip-permissions", "--", "hello"]),
            (["--", "-s", "--prompt", "hello"], ["--dangerously-skip-permissions", "--", "hello"]),
            (["--prompt", "hello", "--", "--remote-control"], ["--remote-control", "--", "hello"]),
            (["--", "--dangerously-skip-permissions"], ["--dangerously-skip-permissions"]),
            (["--resume", VALID_UUID, "--"], ["--resume", VALID_UUID]),
        )
        for script_args, expected in cases:
            with self.subTest(script_args=script_args), tempfile.TemporaryDirectory() as temp_dir:
                invocations_log, env = self._install_fake_claude(temp_dir)
                result = self._run(script_args, temp_dir, env)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(self._argv(invocations_log), expected)
                self.assertEqual(invocations_log.read_text(encoding="utf-8").count("__CALL__"), 1)

    def test_a_bare_word_after_the_spacer_does_not_launch(self) -> None:
        """A word after ``--`` is still parsed here. It is not appended to ``claude``'s argv."""
        cases = (
            ["--", "hello"],
            ["--prompt", "hello", "--", "not-a-flag"],
            ["--", "--dangerously-skip-permissions", "not-a-flag"],
        )
        for script_args in cases:
            with self.subTest(script_args=script_args), tempfile.TemporaryDirectory() as temp_dir:
                invocations_log, env = self._install_fake_claude(temp_dir)
                result = self._run(script_args, temp_dir, env)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertEqual(result.stdout.count("usage: wake_the_claude.bash"), 1)
                self.assertEqual(self._argv(invocations_log), [])


if __name__ == "__main__":
    unittest.main()
