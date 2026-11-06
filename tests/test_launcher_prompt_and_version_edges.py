#!/usr/bin/env python3
"""Edges the launcher suites leave open around a prompt file and ``-v``.

``wake_the_claude.bash`` prefers an explicit ``--prompt`` to a ``--file`` /
``--path`` (the prompt is sent, the file is not read). Nothing else combines
the two, so swapping that preference — or letting a missing ``--file`` fail
the launch even though a prompt was given — stays green. ``--prompt 0`` is
boolean true and still wins: it sends the default prompt, not the file.
``--prompt 1`` is boolean false and leaves the file as the prompt.

``claude_interactive.bash`` (2026-11-06) has the same hazard one layer up, and
two sites that report Claude Code's version. The early site, when the flag is
the first argument, is already pinned. The parse-loop site is not: ``-v``
after another flag used to print this script's version and return. A prompt
file from ``CLAUDE_PROMPT_PATH`` must suppress the default prompt, and
``CLAUDE_PROMPT=0`` (TRUE) with a file is an explicit prompt and is refused.

Hermetic. No network and no real Claude binary.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
WAKE_SRC = REPO_ROOT / "scripts" / "wake_the_claude.bash"
LAUNCHER_SRC = REPO_ROOT / "scripts" / "claude_interactive.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"

# Script-local booleans (TRUE="0", FALSE="1"), shared by both launchers.
SCRIPT_TRUE = "0"
SCRIPT_FALSE = "1"

FILE_TEXT = "from the file\nsecond line\n"
FLAG_PROMPT = "from the flag"
EXCLUSIVE = "A prompt and a prompt file are exclusive"


def _default_prompt() -> str:
    match = re.search(r'^PROMPT_VALUE_DEFAULT="([^"]*)"$', WAKE_SRC.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise AssertionError("wake_the_claude.bash must define PROMPT_VALUE_DEFAULT")
    return match.group(1)


class WakePromptFilePrecedenceTests(unittest.TestCase):
    """The prompt ``wake_the_claude.bash`` actually hands to Claude Code."""

    def _run(self, temp_dir: str, args: list[str]) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(exist_ok=True)
        (Path(temp_dir) / "sessions").mkdir(exist_ok=True)
        (Path(temp_dir) / "logs").mkdir(exist_ok=True)
        argv_log = Path(temp_dir) / "claude_argv.nul"
        argv_log.unlink(missing_ok=True)
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n" "printf '%s\\0' \"$@\" >> \"$CLAUDE_ARGV_NUL_LOG\"\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGV_NUL_LOG"] = str(argv_log)
        env["WTC_SESSIONS_DIR"] = str(Path(temp_dir) / "sessions")
        env["WTC_LOGS_DIR"] = str(Path(temp_dir) / "logs")
        # Debug on, as the sibling suite leaves it: a session id then does not have to be saved.
        env["WTC_DEBUG"] = SCRIPT_TRUE
        result = subprocess.run(
            ["bash", str(WAKE_SRC), *args],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        argv = argv_log.read_bytes().decode("utf-8").split("\0")[:-1] if argv_log.exists() else []
        return result, argv

    def test_an_explicit_prompt_wins_over_a_prompt_file(self) -> None:
        """``--prompt`` is what Claude Code receives, whichever flag came first and whether the file exists.

        The file's text must not replace it. A missing ``--file`` must not fail the launch either: the
        post-parse guard rejects an unresolved file only when no prompt was given.
        """
        file_prompt = FILE_TEXT.rstrip("\n")
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "handoff.md"
            prompt_file.write_text(FILE_TEXT, encoding="utf-8")
            missing = str(Path(temp_dir) / "missing.md")
            cases = (
                ["--prompt", FLAG_PROMPT, "--file", str(prompt_file)],
                ["--file", str(prompt_file), "--prompt", FLAG_PROMPT],
                ["--prompt", FLAG_PROMPT, "--path", str(prompt_file)],
                ["--path", str(prompt_file), "--prompt", FLAG_PROMPT],
                ["--prompt", FLAG_PROMPT, "--file", missing],
                ["--file", missing, "--prompt", FLAG_PROMPT],
            )
            for args in cases:
                with self.subTest(args=args):
                    result, argv = self._run(temp_dir, ["--resume", VALID_UUID, *args])
                    self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    self.assertEqual(argv[-2:], ["--", FLAG_PROMPT])
                    self.assertNotIn(file_prompt, argv)
                    self.assertEqual(argv.count("--"), 1)

    def test_boolean_prompt_values_keep_or_yield_the_file(self) -> None:
        """``0`` (true) sends the default prompt, not the file; ``1`` (false) sends the file."""
        default_prompt = _default_prompt()
        file_prompt = FILE_TEXT.rstrip("\n")
        self.assertNotEqual(default_prompt, file_prompt)
        self.assertNotEqual(default_prompt, "")
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "handoff.md"
            prompt_file.write_text(FILE_TEXT, encoding="utf-8")
            cases = (
                (["--prompt", SCRIPT_TRUE, "--file", str(prompt_file)], default_prompt),
                (["--file", str(prompt_file), "--prompt", SCRIPT_TRUE], default_prompt),
                (["--prompt", SCRIPT_FALSE, "--file", str(prompt_file)], file_prompt),
                (["--path", str(prompt_file), "--prompt", SCRIPT_FALSE], file_prompt),
            )
            for args, expected in cases:
                with self.subTest(args=args):
                    result, argv = self._run(temp_dir, ["--resume", VALID_UUID, *args])
                    self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    self.assertEqual(argv[-2:], ["--", expected])


class ClaudeyPromptFileAndVersionEdgesTests(unittest.TestCase):
    """``claude_interactive.bash`` edges that a fake ``wake_the_claude.bash`` can see."""

    def _install(self, temp_dir: str) -> tuple[Path, Path]:
        scripts_dir = Path(temp_dir) / "scripts"
        scripts_dir.mkdir()
        text = LAUNCHER_SRC.read_text(encoding="utf-8")
        old = 'DEBUG="${TRUE}"'
        self.assertEqual(text.count(old), 1, "DEBUG default marker drifted")
        launcher_path = scripts_dir / "claude_interactive.bash"
        launcher_path.write_text(text.replace(old, 'DEBUG="${FALSE}"', 1), encoding="utf-8")
        launcher_path.chmod(0o755)
        args_log = Path(temp_dir) / "wake_args.log"
        fake_wake = scripts_dir / "wake_the_claude.bash"
        fake_wake.write_text(
            "#!/usr/bin/env bash\n"
            "{\n"
            '  echo "__CALL__"\n'
            '  for arg in "$@"; do\n'
            "    printf 'ARG=%s\\n' \"$arg\"\n"
            "  done\n"
            '} >> "$WTC_WRAPPER_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_wake.chmod(0o755)
        return launcher_path, args_log

    @staticmethod
    def _args(args_log: Path) -> list[str]:
        if not args_log.exists():
            return []
        return [line.removeprefix("ARG=") for line in args_log.read_text(encoding="utf-8").splitlines() if line.startswith("ARG=")]

    def _env(self, args_log: Path) -> RedactedEnv:
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
        ):
            env.pop(var, None)
        env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)
        return env

    def _run(self, temp_dir: str, extra_args: list[str], env_values: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        launcher_path, args_log = self._install(temp_dir)
        env = self._env(args_log)
        if env_values:
            env.update(env_values)
        try:
            result = subprocess.run(
                ["bash", str(launcher_path), *extra_args],
                cwd=temp_dir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"launcher did not exit for {extra_args!r}: {exc}")
        return result, self._args(args_log)

    def test_a_version_flag_after_another_flag_execs_wake_and_does_not_launch(self) -> None:
        """The parse loop, not only the first-argument site, reports Claude Code's version.

        Each alias execs ``wake_the_claude.bash --version`` and nothing else. A prompt parsed
        before the flag must not start a session, and the script's own version must not be printed.
        """
        script_version = re.search(r'^export SCRIPT_VERSION="([^"]*)"$', LAUNCHER_SRC.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(script_version, msg="claude_interactive.bash must export SCRIPT_VERSION")
        assert script_version is not None
        cases = (
            ["--no-worktree", "-v"],
            ["--no-worktree", "-V"],
            ["--no-worktree", "--version"],
            ["--no-worktree", "--claude-version"],
            ["--prompt", FLAG_PROMPT, "-v"],
            ["--file", "notes.md", "--version"],
        )
        for extra_args in cases:
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                result, args = self._run(temp_dir, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(args, ["--version"])
                self.assertNotIn(script_version.group(1), result.stdout.split())
                self.assertNotIn("Launching Default Interactive session", result.stdout)

    def test_prompt_path_from_the_environment_suppresses_the_default_prompt(self) -> None:
        """``CLAUDE_PROMPT_PATH`` is forwarded, alone and with ``CLAUDE_PROMPT_FILE``, and ``--prompt`` is not."""
        cases = (
            {"CLAUDE_PROMPT_PATH": "prompts/handoff.md"},
            {"CLAUDE_PROMPT_FILE": "handoff.md", "CLAUDE_PROMPT_PATH": "prompts"},
            {"CLAUDE_PROMPT_PATH": "prompts/handoff.md", "CLAUDE_PROMPT": SCRIPT_FALSE},
        )
        expected = (
            [("--path", "prompts/handoff.md")],
            [("--file", "handoff.md"), ("--path", "prompts")],
            [("--path", "prompts/handoff.md")],
        )
        for env_values, pairs in zip(cases, expected, strict=True):
            with self.subTest(env_values=env_values), tempfile.TemporaryDirectory() as temp_dir:
                result, args = self._run(temp_dir, [], env_values)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertNotIn("--prompt", args)
                for flag, value in pairs:
                    self.assertEqual(args.count(flag), 1)
                    self.assertEqual(args[args.index(flag) + 1], value)

    def test_boolean_true_prompt_with_a_file_is_refused(self) -> None:
        """``CLAUDE_PROMPT=0`` is an explicit prompt. With a file it must not reach wake, which would send the default instead."""
        cases = (
            ([], {"CLAUDE_PROMPT_PATH": "prompts/handoff.md", "CLAUDE_PROMPT": SCRIPT_TRUE}),
            (["--file", "handoff.md"], {"CLAUDE_PROMPT": SCRIPT_TRUE}),
            (["--path", "prompts"], {"CLAUDE_PROMPT_FILE": "handoff.md", "CLAUDE_PROMPT": SCRIPT_TRUE}),
        )
        for extra_args, env_values in cases:
            with self.subTest(extra_args=extra_args, env_values=env_values), tempfile.TemporaryDirectory() as temp_dir:
                result, args = self._run(temp_dir, extra_args, env_values)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(EXCLUSIVE, result.stdout)
                self.assertEqual(args, [])


if __name__ == "__main__":
    unittest.main()
