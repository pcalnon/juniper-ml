#!/usr/bin/env python3
"""Regression tests for wake_the_claude resume/session-id handling."""

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wake_the_claude.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"


class WakeTheClaudeResumeTests(unittest.TestCase):
    def _install_fake_claude(self, temp_dir: str) -> tuple[Path, dict[str, str]]:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        invocations_log = Path(temp_dir) / "claude_invocations.log"
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n"
            "if [[ \"$1\" == \"--version\" ]]; then\n"
            "  echo \"claude-test-version\"\n"
            "  exit 0\n"
            "fi\n"
            "printf '%s\\n' \"$*\" >> \"$CLAUDE_ARGS_LOG\"\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGS_LOG"] = str(invocations_log)
        return invocations_log, env

    def _run_script(self, args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _wait_for_invocations(self, invocations_log: Path, timeout_seconds: float = 2.0) -> list[str]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if invocations_log.exists():
                content = invocations_log.read_text(encoding="utf-8").strip()
                if content:
                    return content.splitlines()
            time.sleep(0.05)
        return []

    def test_resume_with_uuid_passes_session_id_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            self.assertIn(f"--resume {VALID_UUID}", invocations[-1])

    def test_resume_with_filename_loads_uuid_and_preserves_non_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "session-id.txt"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(
                session_file.exists(),
                msg="Expected non-generated session id file to be preserved",
            )

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            self.assertIn(f"--resume {VALID_UUID}", invocations[-1])

    def test_resume_with_generated_session_file_loads_uuid_and_deletes_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / f"{VALID_UUID}.txt"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertFalse(
                session_file.exists(),
                msg="Expected generated session id file to be consumed and removed",
            )

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            self.assertIn(f"--resume {VALID_UUID}", invocations[-1])

    def test_resume_with_invalid_uuid_fails_once_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "not-a-uuid", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_with_file_containing_invalid_uuid_fails_and_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "session-id.txt"
            session_file.write_text("invalid-content", encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(
                session_file.exists(),
                msg="Expected invalid session id file to be preserved",
            )

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])


if __name__ == "__main__":
    unittest.main()
