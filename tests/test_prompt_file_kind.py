#!/usr/bin/env python3
"""A directory is not a prompt file; a symlink to a regular file is.

``wake_the_claude.bash`` accepts ``--path`` as either the prompt file or the
directory that holds ``--file``. ``is_valid_file`` is ``-f`` (a regular file,
following symlinks) and ``is_valid_dir`` is ``-d``. A directory, or a symlink
to one, sets no ``PROMPT_FILE``. The check after parsing must then refuse the
launch: dropping the ``PATH_NAME`` half of that check would start claude with
no prompt. One trailing slash on ``--path`` is stripped before the refusal is
named. A symlink to a regular file is followed. Session-id writes refuse a
symlink target; prompt loading must not copy that refusal.

Run: python3 -m unittest -v tests/test_prompt_file_kind.py
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
PROMPT_TEXT = "prompt reached through a symlink"


class PromptFileKindTests(unittest.TestCase):
    def _env(self, temp_dir: Path) -> tuple[Path, dict[str, str]]:
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        (temp_dir / "sessions").mkdir()
        (temp_dir / "logs").mkdir()
        invocations_log = temp_dir / "claude_invocations.log"
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "--version" ]]; then\n'
            '  echo "claude-test-version"\n'
            "  exit 0\n"
            "fi\n"
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
        for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGS_LOG"] = str(invocations_log)
        env["WTC_SESSIONS_DIR"] = str(temp_dir / "sessions")
        env["WTC_LOGS_DIR"] = str(temp_dir / "logs")
        env["WTC_DEBUG"] = "1"
        return invocations_log, env

    def _run(self, args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def _args(invocations_log: Path) -> list[str]:
        if not invocations_log.exists():
            return []
        args: list[str] = []
        for line in invocations_log.read_text(encoding="utf-8").splitlines():
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    def test_a_directory_is_refused_and_does_not_launch(self) -> None:
        """A directory is not a prompt file, including through a symlink and one trailing slash.

        The parser's ``-f`` check leaves ``PROMPT_FILE`` empty, so the post-parse
        refusal names ``no prompt file found``. Treating the directory as a file
        (``-e`` or ``-d``) would instead report that it could not be read.
        """
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            prompts = temp_dir / "prompts"
            prompts.mkdir()
            (prompts / "note.md").write_text(PROMPT_TEXT, encoding="utf-8")
            link_to_dir = temp_dir / "link-to-dir"
            link_to_dir.symlink_to(prompts, target_is_directory=True)
            invocations_log, env = self._env(temp_dir)
            cases = (
                ("path-directory", ["--path", str(prompts)], "", str(prompts)),
                ("path-trailing-slash", ["--path", str(prompts) + "/"], "", str(prompts)),
                ("file-directory", ["--file", str(prompts)], str(prompts), ""),
                ("path-symlink-directory", ["--path", str(link_to_dir)], "", str(link_to_dir)),
                ("file-symlink-directory", ["--file", str(link_to_dir)], str(link_to_dir), ""),
            )
            for label, flag_args, file_part, path_part in cases:
                with self.subTest(case=label):
                    result = self._run(["--resume", VALID_UUID, *flag_args], temp_dir, env)
                    self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                    self.assertIn(
                        f'Error: no prompt file found for --file "{file_part}" and --path "{path_part}"',
                        result.stderr,
                    )
                    self.assertNotIn("could not be read", result.stderr)
            self.assertEqual(self._args(invocations_log), [])

    def test_a_symlink_to_a_regular_file_is_the_prompt(self) -> None:
        """Prompt loading follows a symlink to a regular file. Session-id writes do not."""
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            prompts = temp_dir / "prompts"
            prompts.mkdir()
            note = prompts / "note.md"
            note.write_text(PROMPT_TEXT, encoding="utf-8")
            link_to_file = temp_dir / "link-to-file.md"
            link_to_file.symlink_to(note)
            link_to_dir = temp_dir / "link-to-dir"
            link_to_dir.symlink_to(prompts, target_is_directory=True)
            invocations_log, env = self._env(temp_dir)
            cases = (
                ["--file", str(link_to_file)],
                ["--path", str(link_to_file)],
                ["--path", str(link_to_dir), "--file", "note.md"],
            )
            for flag_args in cases:
                with self.subTest(args=flag_args):
                    invocations_log.unlink(missing_ok=True)
                    result = self._run(["--resume", VALID_UUID, *flag_args], temp_dir, env)
                    self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    self.assertEqual(
                        self._args(invocations_log),
                        ["--resume", VALID_UUID, "--", PROMPT_TEXT],
                    )


if __name__ == "__main__":
    unittest.main()
