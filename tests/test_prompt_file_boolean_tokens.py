#!/usr/bin/env python3
"""A prompt file of wake_the_claude.bash's own booleans is still that prompt.

The launcher's true value is ``0`` and its false value is ``1``. A prompt file is
read with ``$(cat)``, which strips trailing newlines, so a file that holds one of
those tokens plus a newline becomes exactly the token. That text must reach claude
as the prompt. Reading it as the flag boolean would send the default prompt, or none.

A file of only carriage return, vertical tab, or form feed holds no prompt. The
blank-file case already in ``tests/test_wake_the_claude.py`` is space, tab, and
newline together, so a space class narrowed to those three would stay green.
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
SCRIPT_PATH = REPO_ROOT / "scripts" / "wake_the_claude.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"


def _assignment(name: str) -> str:
    match = re.search(rf'^{name}="([^"]*)"', SCRIPT_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise AssertionError(f"{name} is not assigned in {SCRIPT_PATH.name}")
    return match.group(1)


class PromptFileBooleanTokenTests(unittest.TestCase):
    """The prompt file's text is not interpreted with the flag boolean convention."""

    def _launch(self, temp_dir: str, content: str, flag: str) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        root = Path(temp_dir)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        argv_log = root / "claude_argv.nul"
        fake = bin_dir / "claude"
        fake.write_text(
            "#!/usr/bin/env bash\n" 'if [[ "$1" == "--version" ]]; then echo "claude-test-version"; exit 0; fi\n' "printf '%s\\0' \"$@\" >> \"$CLAUDE_ARGV_NUL_LOG\"\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        (root / "prompt.md").write_text(content, encoding="utf-8")
        env = RedactedEnv(os.environ)
        for var in ("BASH_ENV", "ENV", "WTC_DEBUG", "CLAUDE_SKIP_PERMISSIONS"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["CLAUDE_ARGV_NUL_LOG"] = str(argv_log)
        env["WTC_SESSIONS_DIR"] = str(root / "sessions")
        env["WTC_LOGS_DIR"] = str(root / "logs")
        env["WTC_DEBUG"] = "1"  # debug log off; FALSE in the script's own convention
        env["LC_ALL"] = "C"
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--resume", VALID_UUID, flag, "prompt.md"],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        argv = argv_log.read_bytes().decode("utf-8").split("\0")[:-1] if argv_log.exists() else []
        return result, argv

    def test_true_and_false_tokens_are_sent_as_the_prompt(self) -> None:
        """``0`` and ``1`` from a prompt file reach claude as that prompt, trailing newlines stripped."""
        true_token = _assignment("TRUE")
        false_token = _assignment("FALSE")
        default_prompt = _assignment("PROMPT_VALUE_DEFAULT")
        self.assertNotEqual(true_token, false_token)
        self.assertNotEqual(true_token, default_prompt)
        self.assertNotEqual(false_token, default_prompt)
        cases = (
            (true_token, true_token, "--file"),
            (true_token + "\n", true_token, "--file"),
            (false_token, false_token, "--path"),
            (false_token + "\n\n", false_token, "--path"),
        )
        for content, expected, flag in cases:
            with self.subTest(flag=flag, expected=expected, trailing_newlines=content.count("\n")), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, content, flag)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(argv[-2:], ["--", expected])
                self.assertNotIn(default_prompt, argv)
                self.assertNotIn("--prompt", argv)

    def test_other_posix_whitespace_holds_no_prompt(self) -> None:
        """Carriage return, vertical tab, and form feed are whitespace: the file holds no prompt and claude does not start."""
        cases = (
            ("cr", "\r"),
            ("vt", "\v"),
            ("ff", "\f"),
            ("crlf", "\r\n"),
        )
        for name, content in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, content, "--file")
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("holds no prompt", result.stderr)
                self.assertIn("prompt.md", result.stderr)
                self.assertEqual(argv, [])


if __name__ == "__main__":
    unittest.main()
