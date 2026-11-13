#!/usr/bin/env python3
"""A later prompt-file flag replaces an earlier one, and an unresolved one does not launch.

``scripts/wake_the_claude.bash`` resolves ``--file`` / ``--path`` into ``PROMPT_FILE`` and, when the
name cannot be resolved yet, waits: a file name may be waiting on ``--path``, and a directory may be
waiting on ``--file``. The wait left the previous resolution in place. ``--file good.md --file
missing.md`` and ``--path good.md --path emptydir`` exited 0 and sent ``good.md``.

The later flag that does resolve is the prompt. ``--file <name> --path <dir>`` still resolves when
the file exists only in that directory.
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
EARLIER = "EARLIER_PROMPT"
LATER = "LATER_PROMPT"


class LaterPromptFileFlagTests(unittest.TestCase):
    """The prompt file is the one the last resolving flag named."""

    def _launch(self, temp_dir: str, args: list[str], files: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        root = Path(temp_dir)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        argv_log = root / "claude_argv.nul"
        fake = bin_dir / "claude"
        fake.write_text(
            "#!/usr/bin/env bash\n" 'if [[ "$1" == "--version" ]]; then echo "claude-test-version"; exit 0; fi\n' 'printf \'%s\\0\' "$@" >> "$CLAUDE_ARGV_NUL_LOG"\n',
            encoding="utf-8",
        )
        fake.chmod(0o755)
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        env = RedactedEnv(os.environ)
        for var in ("BASH_ENV", "ENV", "WTC_DEBUG", "CLAUDE_SKIP_PERMISSIONS", "CLAUDE_PROMPT", "CLAUDE_PROMPT_FILE", "CLAUDE_PROMPT_PATH"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["CLAUDE_ARGV_NUL_LOG"] = str(argv_log)
        env["WTC_SESSIONS_DIR"] = str(root / "sessions")
        env["WTC_LOGS_DIR"] = str(root / "logs")
        env["WTC_DEBUG"] = "1"  # debug log off, so a refusal cannot hide in it
        env["LC_ALL"] = "C"
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--resume", VALID_UUID, *args],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        argv = argv_log.read_bytes().decode("utf-8").split("\0")[:-1] if argv_log.exists() else []
        return result, argv

    def test_a_later_unresolved_flag_does_not_send_the_earlier_prompt(self) -> None:
        """A second ``--file`` or ``--path`` that does not resolve exits 1 and does not launch.

        The first flag's prompt used to be sent: the parser waited, and left ``PROMPT_FILE`` set.
        """
        cases = (
            ("--file", ["--file", "first.md", "--file", "missing.md"], "missing.md"),
            ("--file-name", ["--file-name", "first.md", "--file-name", "missing.md"], "missing.md"),
            ("-f", ["-f", "first.md", "-f", "missing.md"], "missing.md"),
            ("--path", ["--path", "first.md", "--path", "emptydir"], "emptydir"),
            ("--file-path", ["--file-path", "first.md", "--file-path", "emptydir"], "emptydir"),
            ("-l", ["-l", "first.md", "-l", "emptydir"], "emptydir"),
        )
        files = {"first.md": EARLIER, "emptydir/.keep": ""}
        for name, args, later in cases:
            with self.subTest(flag=name), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, args, files)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("no prompt file found", result.stderr)
                self.assertIn(later, result.stderr)
                self.assertNotIn(EARLIER, result.stdout + result.stderr)
                self.assertEqual(argv, [])

    def test_the_later_resolved_flag_is_the_prompt(self) -> None:
        """Two flags that both name a real file send the later file's text, not the earlier one's."""
        cases = (
            ["--file", "first.md", "--file", "second.md"],
            ["--path", "first.md", "--path", "second.md"],
            ["-f", "first.md", "--file-name", "second.md"],
            ["-l", "first.md", "--file-path", "second.md"],
        )
        files = {"first.md": EARLIER, "second.md": LATER}
        for args in cases:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, args, files)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(argv[-2:], ["--", LATER])
                self.assertNotIn(EARLIER, argv)

    def test_a_file_name_still_waits_for_its_directory(self) -> None:
        """``--file <name>`` and ``--path <dir>`` still resolve when the file exists only in that directory.

        The refusal above clears a resolution that did not happen. It must not clear the name the other flag joins.
        """
        files = {"prompts/only-in-dir.md": "DIR_PROMPT"}
        cases = (
            ["--file", "only-in-dir.md", "--path", "prompts"],
            ["--path", "prompts", "--file", "only-in-dir.md"],
            ["-l", "prompts/", "-f", "only-in-dir.md"],
        )
        for args in cases:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, args, files)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(argv[-2:], ["--", "DIR_PROMPT"])
                self.assertNotIn(EARLIER, argv)


if __name__ == "__main__":
    unittest.main()
