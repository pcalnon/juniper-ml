"""Regression tests for util/reap_pytest_orphans.bash."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "reap_pytest_orphans.bash"
SCRIPT_TIMEOUT_SECONDS = 30


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _fake_command_env(fake_bin: Path, ps_output_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["FAKE_PS_OUTPUT"] = str(ps_output_file)
    return env


def _run_script_with_fake_process_table(ps_output: str, *args: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_bin = temp_path / "bin"
        fake_bin.mkdir()
        ps_output_file = temp_path / "ps-output.txt"
        ps_output_file.write_text(ps_output, encoding="utf-8")

        _write_executable(
            fake_bin / "id",
            """#!/usr/bin/env bash
if [[ "$1" == "-un" ]]; then
    echo tester
else
    /usr/bin/id "$@"
fi
""",
        )
        _write_executable(
            fake_bin / "ps",
            """#!/usr/bin/env bash
cat "$FAKE_PS_OUTPUT"
""",
        )

        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            env=_fake_command_env(fake_bin, ps_output_file),
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )


def _process_exists(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def _read_ppid(pid: int) -> int | None:
    status_path = Path(f"/proc/{pid}/status")
    if not status_path.exists():
        return None

    for line in status_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("PPid:"):
            return int(line.split()[1])
    return None


def _wait_for_ppid(pid: int, expected_ppid: int, timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _read_ppid(pid) == expected_ppid:
            return
        time.sleep(0.05)
    raise AssertionError(f"pid {pid} was not reparented to {expected_ppid}; current ppid={_read_ppid(pid)}")


class ReapPytestOrphansArgumentTests(unittest.TestCase):
    def test_unknown_argument_prints_usage_and_exits_with_argument_error(self):
        result = _run_script_with_fake_process_table("", "--bogus")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown argument: --bogus", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_help_prints_usage_without_scanning_process_table(self):
        result = _run_script_with_fake_process_table("", "--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--dry-run", result.stdout)


class ReapPytestOrphansSafetyTests(unittest.TestCase):
    def test_no_candidates_exits_successfully_without_summary_noise(self):
        result = _run_script_with_fake_process_table("123 tester /bin/bash unrelated\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "No Juniper python processes found.")
        self.assertEqual(result.stderr, "")

    def test_verbose_dry_run_keeps_candidate_with_live_parent(self):
        proc = subprocess.Popen(["sleep", "30"])
        try:
            ps_output = f"{proc.pid} tester python /home/pcalnon/Development/python/Juniper/worktrees/repo/test_worker.py\n"

            result = _run_script_with_fake_process_table(ps_output, "--dry-run", "--verbose")

            self.assertEqual(result.returncode, 0)
            self.assertIn(f"KEEP       pid={proc.pid}", result.stdout)
            self.assertIn("(live parent)", result.stdout)
            self.assertIn("Dry-run summary: 0 would be reaped, 1 kept (live parent), 0 skipped.", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertIsNone(proc.poll(), "dry-run should not terminate live-parent candidates")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    def test_dry_run_reports_reparented_candidate_without_killing_it(self):
        launcher = subprocess.run(
            ["bash", "-c", "sleep 30 </dev/null >/dev/null 2>&1 & echo $!"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        orphan_pid = int(launcher.stdout.strip())

        try:
            _wait_for_ppid(orphan_pid, 1)
            ps_output = f"{orphan_pid} tester python /home/pcalnon/Development/python/Juniper/worktrees/repo/test_worker.py\n"

            result = _run_script_with_fake_process_table(ps_output, "--dry-run")

            self.assertEqual(result.returncode, 0)
            self.assertIn(f"WOULD REAP pid={orphan_pid} ppid=1", result.stdout)
            self.assertIn("Dry-run summary: 1 would be reaped, 0 kept (live parent), 0 skipped.", result.stdout)
            self.assertTrue(_process_exists(orphan_pid), "dry-run should not kill reparented candidates")
        finally:
            if _process_exists(orphan_pid):
                subprocess.run(["kill", "-KILL", str(orphan_pid)], check=False, timeout=SCRIPT_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
