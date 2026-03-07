#!/usr/bin/env python3
"""Regression tests for wake_the_claude resume/session-id handling."""

import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wake_the_claude.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


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
            "{\n"
            "  echo \"__CALL__\"\n"
            "  echo \"ARGC=$#\"\n"
            "  for arg in \"$@\"; do\n"
            "    printf 'ARG=%s\\n' \"$arg\"\n"
            "  done\n"
            "} >> \"$CLAUDE_ARGS_LOG\"\n",
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

    def _wait_for_invocations(self, invocations_log: Path, timeout_seconds: float = 2.0) -> list[list[str]]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if invocations_log.exists():
                content = invocations_log.read_text(encoding="utf-8").strip()
                if content:
                    blocks: list[list[str]] = []
                    current_block: list[str] = []
                    for line in content.splitlines():
                        if line == "__CALL__":
                            if current_block:
                                blocks.append(current_block)
                            current_block = []
                            continue
                        current_block.append(line)
                    if current_block:
                        blocks.append(current_block)
                    if blocks:
                        return blocks
            time.sleep(0.05)
        return []

    @staticmethod
    def _extract_args(invocation_block: list[str]) -> list[str]:
        args: list[str] = []
        for line in invocation_block:
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

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
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_alias_flag_passes_session_id_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume-session", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_with_filename_loads_uuid_and_preserves_file(self) -> None:
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
            self.assertTrue(session_file.exists(), msg="Expected session id file to remain after read-only resume")

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

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
            self.assertTrue(session_file.exists(), msg="Expected invalid session id file to remain after rejection")

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
            self.assertNotIn("invalid-content", combined_output)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_rejects_filename_with_path_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            nested_dir = Path(temp_dir) / "nested"
            nested_dir.mkdir(parents=True, exist_ok=True)
            nested_file = nested_dir / "session-id.txt"
            nested_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", "nested/session-id.txt", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_rejects_non_txt_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "session-id.dat"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_with_filename_works_when_debug_logging_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env["WTC_DEBUG"] = "1"
            session_file = Path(temp_dir) / "session-id.txt"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_flag_without_value_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "--", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Received Resume Flag but no Valid Session ID to Resume. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_session_id_save_rejects_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            symlink_target = Path(temp_dir) / "sensitive-target.txt"
            symlink_target.write_text("ORIGINAL", encoding="utf-8")
            symlink_path = Path(temp_dir) / f"{VALID_UUID}.txt"
            symlink_path.symlink_to(symlink_target)

            result = self._run_script(
                ["--id", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(symlink_path.is_symlink())
            self.assertEqual(symlink_target.read_text(encoding="utf-8"), "ORIGINAL")
            self.assertIn("symlink", result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", VALID_UUID, "hello"])

    def test_prompt_with_shell_tokens_is_passed_as_single_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_text = "hello ; --model injected $(whoami) with spaces"

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", prompt_text],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, prompt_text])
            self.assertNotIn("--model", last_invocation_args)

    def test_existing_nohup_out_is_not_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            nohup_file = Path(temp_dir) / "nohup.out"
            original_nohup_content = "existing process output\n"
            nohup_file.write_text(original_nohup_content, encoding="utf-8")

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(nohup_file.exists(), msg="Expected existing nohup.out to be preserved")
            self.assertEqual(
                nohup_file.read_text(encoding="utf-8"),
                original_nohup_content,
                msg="Expected existing nohup.out contents to remain unchanged",
            )

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])


if __name__ == "__main__":
    unittest.main()
