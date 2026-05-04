"""Regression tests for util/reap_pytest_orphans.bash."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "reap_pytest_orphans.bash"
SCRIPT_TIMEOUT_SECONDS: int = 10


class ReapPytestOrphansTests(unittest.TestCase):
    def _run_with_fake_process_table(
        self,
        temp_dir: str,
        *,
        ps_output: str,
        proc_entries: dict[int, tuple[int, str]],
        proc_dirs: set[int] | None = None,
        args: list[str] | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        temp_path = Path(temp_dir)
        bin_dir = temp_path / "bin"
        bin_dir.mkdir()

        fake_ps_output = temp_path / "ps-output.txt"
        fake_ps_output.write_text(ps_output, encoding="utf-8")

        fake_id = bin_dir / "id"
        fake_id.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "-un" ]]; then\n'
            "  echo tester\n"
            "  exit 0\n"
            "fi\n"
            "exit 2\n",
            encoding="utf-8",
        )
        fake_id.chmod(0o755)

        fake_ps = bin_dir / "ps"
        fake_ps.write_text(
            "#!/usr/bin/env bash\n"
            'cat "$FAKE_PS_OUTPUT"\n',
            encoding="utf-8",
        )
        fake_ps.chmod(0o755)

        proc_root = temp_path / "proc"
        proc_root.mkdir()
        for pid in proc_dirs or set():
            (proc_root / str(pid)).mkdir()
        for pid, (ppid, cmdline) in proc_entries.items():
            pid_dir = proc_root / str(pid)
            pid_dir.mkdir(exist_ok=True)
            (pid_dir / "status").write_text(f"Name:\tpython\nPPid:\t{ppid}\n", encoding="utf-8")
            (pid_dir / "cmdline").write_bytes(cmdline.encode("utf-8") + b"\0")

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["FAKE_PS_OUTPUT"] = str(fake_ps_output)
        env["JUNIPER_REAP_PROC_ROOT"] = str(proc_root)
        if extra_env:
            env.update(extra_env)

        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *(args or [])],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            check=False,
        )

    def test_no_candidates_exits_successfully(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output="123 tester /usr/bin/python unrelated.py\n",
                proc_entries={},
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("No Juniper python processes found.", result.stdout)

    def test_ignores_juniper_python_processes_owned_by_other_users(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output="424200 otheruser /home/test/miniconda/envs/JuniperCascor/bin/python worker.py\n",
                proc_entries={},
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("No Juniper python processes found.", result.stdout)

    def test_dry_run_reaps_init_reparented_juniper_python_process(self) -> None:
        pid = 424242
        cmdline = "/home/test/miniconda/envs/JuniperCascor/bin/python worker.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output=f"{pid} tester {cmdline}\n",
                proc_entries={pid: (1, cmdline)},
                args=["--dry-run"],
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"WOULD REAP pid={pid} ppid=1", result.stdout)
        self.assertIn("Dry-run summary: 1 would be reaped, 0 kept (live parent), 0 skipped.", result.stdout)

    def test_non_dry_run_sends_sigkill_to_orphan(self) -> None:
        pid = 424250
        cmdline = "/home/test/miniconda/envs/JuniperCascor/bin/python worker.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            kill_log = Path(temp_dir) / "kill.log"
            fake_kill = Path(temp_dir) / "fake-kill"
            fake_kill.write_text(
                "#!/usr/bin/env bash\n"
                'printf "%s\\n" "$*" >> "$KILL_LOG"\n',
                encoding="utf-8",
            )
            fake_kill.chmod(0o755)
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output=f"{pid} tester {cmdline}\n",
                proc_entries={pid: (1, cmdline)},
                extra_env={
                    "JUNIPER_REAP_KILL_COMMAND": str(fake_kill),
                    "KILL_LOG": str(kill_log),
                },
            )

            kill_invocation = kill_log.read_text(encoding="utf-8").strip()

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"REAP       pid={pid} ppid=1", result.stdout)
        self.assertEqual(kill_invocation, f"-KILL {pid}")
        self.assertIn("Summary: 1 reaped, 0 kept (live parent), 0 skipped.", result.stdout)

    def test_verbose_dry_run_keeps_juniper_python_process_with_live_parent(self) -> None:
        parent_pid = 424300
        child_pid = 424301
        cmdline = "/home/test/Juniper/worktrees/juniper-cascor--branch/.venv/bin/python -m pytest"
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output=f"{child_pid} tester {cmdline}\n",
                proc_entries={child_pid: (parent_pid, cmdline)},
                proc_dirs={parent_pid},
                args=["--dry-run", "--verbose"],
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"KEEP       pid={child_pid} ppid={parent_pid} (live parent)", result.stdout)
        self.assertIn("Dry-run summary: 0 would be reaped, 1 kept (live parent), 0 skipped.", result.stdout)

    def test_dry_run_treats_systemd_user_parent_as_orphan(self) -> None:
        systemd_pid = 424400
        child_pid = 424401
        cmdline = "/home/test/Juniper/worktrees/juniper-cascor--branch/.venv/bin/python forkserver.py"
        ps_output = "\n".join(
            [
                f"{systemd_pid} tester /usr/lib/systemd/systemd --user",
                f"{child_pid} tester {cmdline}",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output=ps_output,
                proc_entries={child_pid: (systemd_pid, cmdline)},
                proc_dirs={systemd_pid},
                args=["--dry-run"],
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"WOULD REAP pid={child_pid} ppid={systemd_pid}", result.stdout)
        self.assertIn("Dry-run summary: 1 would be reaped, 0 kept (live parent), 0 skipped.", result.stdout)

    def test_disappeared_candidate_is_skipped(self) -> None:
        pid = 424500
        cmdline = "/home/test/miniconda/envs/JuniperCascor/bin/python worker.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output=f"{pid} tester {cmdline}\n",
                proc_entries={},
                args=["--dry-run"],
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Dry-run summary: 0 would be reaped, 0 kept (live parent), 1 skipped.", result.stdout)

    def test_unknown_argument_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self._run_with_fake_process_table(
                temp_dir,
                ps_output="",
                proc_entries={},
                args=["--bogus"],
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown argument: --bogus", result.stderr)
