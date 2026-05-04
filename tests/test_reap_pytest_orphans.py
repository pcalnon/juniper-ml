"""Regression tests for util/reap_pytest_orphans.bash."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "reap_pytest_orphans.bash"
SCRIPT_TIMEOUT_SECONDS: int = 30


def run_script(*args: str) -> subprocess.CompletedProcess:
    """Run reap_pytest_orphans.bash with the given arguments."""
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestArgumentParsing(unittest.TestCase):
    """Test argument parsing and usage output."""

    def test_help_flag_prints_usage(self):
        result = run_script("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--verbose", result.stdout)

    def test_unknown_argument_fails_without_scanning_processes(self):
        result = run_script("--bogus-flag")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown argument: --bogus-flag", result.stderr)
        self.assertIn("Usage:", result.stderr)


class TestLiveParentSafety(unittest.TestCase):
    """Test the critical safety rule: never reap a process with a live parent."""

    def test_verbose_dry_run_keeps_matching_python_process_with_live_parent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = f"{temp_dir}/Juniper/worktrees/live-parent"
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import time; time.sleep(60)",
                    marker,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                self._wait_until_cmdline_contains(child.pid, marker)

                result = run_script("--dry-run", "--verbose")

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"KEEP       pid={child.pid}", result.stdout)
                self.assertIn("(live parent)", result.stdout)
                self.assertNotIn(f"WOULD REAP pid={child.pid}", result.stdout)
                self.assertIsNone(child.poll(), "live-parent candidate should still be running")
            finally:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)

    def _wait_until_cmdline_contains(self, pid: int, expected: str) -> None:
        cmdline_path = Path(f"/proc/{pid}/cmdline")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if cmdline_path.exists() and expected.encode("utf-8") in cmdline_path.read_bytes():
                return
            time.sleep(0.05)
        self.fail(f"child process {pid} command line never exposed {expected!r}")


if __name__ == "__main__":
    unittest.main()
