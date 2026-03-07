#!/usr/bin/env python3
"""Regression tests for wake_the_claude resume/session-id handling."""

import os
import re
import shutil
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
    def _install_fake_claude(self, temp_dir: str, *, failing_uuidgen: bool = False) -> tuple[Path, dict[str, str]]:
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

        if failing_uuidgen:
            fake_uuidgen = bin_dir / "uuidgen"
            fake_uuidgen.write_text(
                "#!/usr/bin/env bash\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake_uuidgen.chmod(0o755)

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

    @staticmethod
    def _install_fake_command(temp_dir: str, name: str, script_body: str) -> None:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        fake_command = bin_dir / name
        fake_command.write_text(script_body, encoding="utf-8")
        fake_command.chmod(0o755)

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

    def test_session_id_trailing_alias_flag_passes_value_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--thread-id", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            saved_session_file = Path(temp_dir) / f"{VALID_UUID}.txt"
            self.assertTrue(saved_session_file.exists(), msg="Expected session id file to be created")
            self.assertEqual(saved_session_file.read_text(encoding="utf-8").strip(), VALID_UUID)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", VALID_UUID, "hello"])

    def test_permissions_trailing_alias_flag_is_forwarded_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                [
                    "--resume",
                    VALID_UUID,
                    "--dangerously-skip-permissions",
                    "--prompt",
                    "hello",
                ],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(
                last_invocation_args,
                ["--resume", VALID_UUID, "--dangerously-skip-permissions", "hello"],
            )

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

    def test_resume_with_missing_txt_file_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            missing_session_file = Path(temp_dir) / "missing-session-id.txt"

            result = self._run_script(
                ["--resume", missing_session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertFalse(
                missing_session_file.exists(),
                msg="Expected script not to create missing resume source file",
            )

            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_with_empty_txt_file_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            empty_session_file = Path(temp_dir) / "empty-session-id.txt"
            empty_session_file.write_text("", encoding="utf-8")

            result = self._run_script(
                ["--resume", empty_session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(
                empty_session_file.exists(),
                msg="Expected empty resume source file to be preserved after rejection",
            )

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

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(symlink_path.is_symlink())
            self.assertEqual(symlink_target.read_text(encoding="utf-8"), "ORIGINAL")
            combined_output = result.stdout + result.stderr
            self.assertIn("symlink", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

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

    def test_session_id_without_value_uses_uuid_fallback_when_uuidgen_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            fallback_uuid = "11111111-2222-3333-4444-555555555555"
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n"
                f"if [[ \"$1\" == \"/proc/sys/kernel/random/uuid\" ]]; then\n"
                f"  echo \"{fallback_uuid}\"\n"
                "  exit 0\n"
                "fi\n"
                "/usr/bin/cat \"$@\"\n",
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            saved_session_file = Path(temp_dir) / f"{fallback_uuid}.txt"
            self.assertTrue(saved_session_file.exists(), msg="Expected generated session id file to be created")
            self.assertEqual(saved_session_file.read_text(encoding="utf-8").strip(), fallback_uuid)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", fallback_uuid, "hello"])

    def test_session_id_without_value_uses_python_fallback_when_uuidgen_and_proc_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            python_fallback_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == \"/proc/sys/kernel/random/uuid\" ]]; then\n"
                "  echo \"not-a-uuid\"\n"
                "  exit 0\n"
                "fi\n"
                "/usr/bin/cat \"$@\"\n",
            )
            self._install_fake_command(
                temp_dir,
                "python3",
                "#!/usr/bin/env bash\n"
                f"echo \"{python_fallback_uuid}\"\n",
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", python_fallback_uuid, "hello"])

    def test_session_id_without_value_fails_when_all_uuid_fallbacks_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == \"/proc/sys/kernel/random/uuid\" ]]; then\n"
                "  echo \"still-not-a-uuid\"\n"
                "  exit 0\n"
                "fi\n"
                "/usr/bin/cat \"$@\"\n",
            )
            self._install_fake_command(
                temp_dir,
                "python3",
                "#!/usr/bin/env bash\n"
                "echo \"bad-python-uuid-output\"\n",
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Failed to generate a valid UUID for Session ID.", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_non_writable_cwd_falls_back_to_home_log_and_still_launches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            home_dir = Path(temp_dir) / "home"
            home_dir.mkdir(parents=True, exist_ok=True)
            env["HOME"] = str(home_dir)

            read_only_dir = Path(temp_dir) / "read-only"
            read_only_dir.mkdir(parents=True, exist_ok=True)
            read_only_dir.chmod(0o555)
            try:
                result = self._run_script(
                    ["--resume", VALID_UUID, "--prompt", "hello"],
                    cwd=str(read_only_dir),
                    env=env,
                )
            finally:
                # Restore permissions so TemporaryDirectory cleanup can remove it.
                read_only_dir.chmod(0o755)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertFalse((read_only_dir / "wake_the_claude.nohup.log").exists())
            self.assertTrue((home_dir / "wake_the_claude.nohup.log").exists())

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_no_writable_log_location_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            read_only_dir = Path(temp_dir) / "read-only"
            read_only_dir.mkdir(parents=True, exist_ok=True)
            read_only_dir.chmod(0o555)

            read_only_home = Path(temp_dir) / "read-only-home"
            read_only_home.mkdir(parents=True, exist_ok=True)
            read_only_home.chmod(0o555)
            env["HOME"] = str(read_only_home)

            try:
                result = self._run_script(
                    ["--resume", VALID_UUID, "--prompt", "hello"],
                    cwd=str(read_only_dir),
                    env=env,
                )
            finally:
                # Restore permissions so TemporaryDirectory cleanup can remove them.
                read_only_dir.chmod(0o755)
                read_only_home.chmod(0o755)

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Failed to open nohup log file", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_missing_claude_binary_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log = Path(temp_dir) / "claude_invocations.log"
            isolated_bin = Path(temp_dir) / "isolated-bin"
            isolated_bin.mkdir(parents=True, exist_ok=True)

            bash_path = shutil.which("bash")
            self.assertIsNotNone(bash_path, msg="bash must be discoverable for this test")
            os.symlink(str(Path(bash_path)), str(isolated_bin / "bash"))

            env = os.environ.copy()
            env["PATH"] = str(isolated_bin)
            env["HOME"] = temp_dir
            env["CLAUDE_ARGS_LOG"] = str(invocations_log)

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("claude command not found in PATH", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_exported_claude_function_without_binary_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log = Path(temp_dir) / "claude_invocations.log"
            isolated_bin = Path(temp_dir) / "isolated-bin"
            isolated_bin.mkdir(parents=True, exist_ok=True)

            bash_path = shutil.which("bash")
            self.assertIsNotNone(bash_path, msg="bash must be discoverable for this test")
            os.symlink(str(Path(bash_path)), str(isolated_bin / "bash"))

            env = os.environ.copy()
            env["PATH"] = str(isolated_bin)
            env["HOME"] = temp_dir
            env["CLAUDE_ARGS_LOG"] = str(invocations_log)
            env["BASH_FUNC_claude%%"] = "() { echo wrapper-function; }"

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("claude command not found in PATH", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])

    def test_resume_with_generated_filename_but_invalid_content_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / f"{VALID_UUID}.txt"
            session_file.write_text("invalid-content", encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(
                session_file.exists(),
                msg="Expected generated-style session id file to be preserved when content is invalid",
            )

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=0.3)
            self.assertEqual(invocations, [])


if __name__ == "__main__":
    unittest.main()
