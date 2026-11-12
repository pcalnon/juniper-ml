"""
Tests for util/reap_pytest_orphans.bash.

The orphan reaper is safety-critical because a false positive can kill an active
test run. These tests use a fake process table, fake proc tree, and fake kill
command so the reaping decisions are deterministic and never touch real PIDs.
"""

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "reap_pytest_orphans.bash"
SCRIPT_TIMEOUT_SECONDS: int = 30


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    path.chmod(0o755)


class FakeProcessFixture:
    """Build a deterministic process environment for reap_pytest_orphans.bash."""

    def __init__(self, tmpdir: str, ps_rows: list[str]):
        self.root = Path(tmpdir)
        self.bin_dir = self.root / "bin"
        self.proc_root = self.root / "proc"
        self.kill_log = self.root / "kill.log"
        # Redirected so a test never reads the real run roots — a live campaign
        # on this workstation must not be able to change a test's verdict. The
        # legacy roots (read-only since 2026-10-26) are redirected too: the fixed
        # one through its test seam, the TMPDIR-derived one through TMPDIR.
        self.exp_run_root = self.root / "exp-run-root"
        self.e2e_run_dir = self.root / "e2e-run-dir"
        self.legacy_e2e_run_dir = self.root / "legacy-e2e-run-dir"
        self.tmpdir = self.root / "session-tmpdir"
        self.bin_dir.mkdir()
        self.proc_root.mkdir()
        self.tmpdir.mkdir()

        self._write_fake_id()
        self._write_fake_ps(ps_rows)
        self._write_fake_kill()

    def add_experiment_pidfile(self, run_id: str, service: str, pid: int) -> None:
        """Record ``pid`` the way ``experiment_stack.bash`` does (P1 key)."""
        run_dir = self.exp_run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / f"{service}.pid").write_text(f"{pid}\n", encoding="utf-8")

    def _write_fake_id(self) -> None:
        write_executable(
            self.bin_dir / "id",
            """
            #!/usr/bin/env bash
            if [[ "$1" == "-un" ]]; then
                echo testuser
                exit 0
            fi
            exit 1
            """,
        )

    def _write_fake_ps(self, rows: list[str]) -> None:
        output = "\n".join(rows)
        write_executable(
            self.bin_dir / "ps",
            f"""
            #!/usr/bin/env bash
            cat <<'EOF'
            {output}
            EOF
            """,
        )

    def _write_fake_kill(self) -> None:
        write_executable(
            self.bin_dir / "fake-kill",
            """
            #!/usr/bin/env bash
            printf '%s\\n' "$*" >> "${KILL_LOG}"
            """,
        )

    def add_process(self, pid: int, ppid: int, cmdline: list[str]) -> None:
        process_dir = self.proc_root / str(pid)
        process_dir.mkdir()
        (process_dir / "status").write_text(f"Name:\tpython\nPPid:\t{ppid}\n", encoding="utf-8")
        (process_dir / "cmdline").write_bytes(b"\0".join(part.encode("utf-8") for part in cmdline) + b"\0")

    def add_parent(self, pid: int) -> None:
        (self.proc_root / str(pid)).mkdir()

    def env(self) -> dict[str, str]:
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env['PATH']}"
        env["KILL_LOG"] = str(self.kill_log)
        env["JUNIPER_REAP_KILL_CMD"] = str(self.bin_dir / "fake-kill")
        env["JUNIPER_REAP_PROC_ROOT"] = str(self.proc_root)
        env["JUNIPER_EXP_RUN_ROOT"] = str(self.exp_run_root)
        env["JUNIPER_E2E_RUN_DIR"] = str(self.e2e_run_dir)
        env["JUNIPER_REAP_LEGACY_E2E_RUN_DIR"] = str(self.legacy_e2e_run_dir)
        env["TMPDIR"] = str(self.tmpdir)
        return env


def run_script(fixture: FakeProcessFixture, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=fixture.env(),
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestReapPytestOrphans(unittest.TestCase):
    def test_dry_run_reaps_init_systemd_and_missing_parent_orphans_without_killing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "101 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "102 testuser /home/pcalnon/Development/python/Juniper/worktrees/repo/.venv/bin/python -c worker",
                    "103 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(101, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(102, 50, ["/home/pcalnon/Development/python/Juniper/worktrees/repo/.venv/bin/python", "-c", "worker"])
            fixture.add_process(103, 999, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WOULD REAP pid=101 ppid=1", result.stdout)
            self.assertIn("WOULD REAP pid=102 ppid=50", result.stdout)
            self.assertIn("WOULD REAP pid=103 ppid=999", result.stdout)
            self.assertIn("Dry-run summary: 3 would be reaped, 0 kept (live parent), 0 protected (live experiment), 0 skipped.", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_verbose_dry_run_keeps_juniper_python_process_with_live_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "201 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(201, 200, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_parent(200)

            result = run_script(fixture, "--dry-run", "--verbose")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("KEEP       pid=201 ppid=200 (live parent)", result.stdout)
            self.assertIn("Dry-run summary: 0 would be reaped, 1 kept (live parent), 0 protected (live experiment), 0 skipped.", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_real_mode_kills_only_orphaned_juniper_python_processes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "301 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "302 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(301, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(302, 300, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_parent(300)

            result = run_script(fixture)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("REAP       pid=301 ppid=1", result.stdout)
            self.assertIn("Summary: 1 reaped, 1 kept (live parent), 0 protected (live experiment), 0 skipped.", result.stdout)
            self.assertEqual(fixture.kill_log.read_text(encoding="utf-8"), "-KILL 301\n")

    def test_kill_failure_does_not_abort_and_still_counts_reaped(self):
        """``kill ... || true`` must keep set -e from aborting mid-loop.

        A vanished PID between decision and kill is normal (race with the OS
        reaper). Without ``|| true``, ``set -euo pipefail`` would exit before
        later orphans are considered — leaving RSS held. Fake-kill exits 1.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "401 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "402 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(401, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(402, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            write_executable(
                fixture.bin_dir / "fake-kill",
                """
                #!/usr/bin/env bash
                printf '%s\\n' "$*" >> "${KILL_LOG}"
                exit 1
                """,
            )

            result = run_script(fixture)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("REAP       pid=401 ppid=1", result.stdout)
            self.assertIn("REAP       pid=402 ppid=1", result.stdout)
            self.assertIn("Summary: 2 reaped, 0 kept (live parent), 0 protected (live experiment), 0 skipped.", result.stdout)
            self.assertEqual(
                fixture.kill_log.read_text(encoding="utf-8"),
                "-KILL 401\n-KILL 402\n",
            )

    def test_candidate_filter_excludes_all_when_no_juniper_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "501 otheruser /opt/conda/envs/JuniperCascor1/bin/python -m pytest",
                    "502 testuser /usr/bin/python -m pytest",
                ],
            )

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No Juniper python processes found.", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_candidate_filter_excludes_other_user_and_non_juniper_python(self):
        """Awk candidate gate: current-user + JuniperC*/worktrees only.

        Loosening this filter is the false-positive class that kills foreign
        sessions or plain ``python -m pytest`` runs outside Juniper.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    # Other user's Juniper python must never be a candidate.
                    "401 otheruser /opt/conda/envs/JuniperCascor1/bin/python -m pytest",
                    # Same user, but no JuniperC* env / worktrees path.
                    "402 testuser /usr/bin/python -m pytest",
                    # Sole legitimate candidate (orphan under init).
                    "403 testuser /opt/conda/envs/JuniperCascor1/bin/python -m pytest",
                ],
            )
            fixture.add_process(
                403,
                1,
                ["/opt/conda/envs/JuniperCascor1/bin/python", "-m", "pytest"],
            )

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WOULD REAP pid=403 ppid=1", result.stdout)
            self.assertNotIn("pid=401", result.stdout)
            self.assertNotIn("pid=402", result.stdout)
            self.assertIn(
                "Dry-run summary: 1 would be reaped, 0 kept (live parent), 0 protected (live experiment), 0 skipped.",
                result.stdout,
            )
            self.assertFalse(fixture.kill_log.exists())

    def test_disappeared_process_is_skipped(self):
        """ps→gone race: candidate listed but /proc/<pid> already missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "601 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            # Deliberately do not create PROC_ROOT/601.

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertIn(
                "Dry-run summary: 0 would be reaped, 0 kept (live parent), 0 protected (live experiment), 1 skipped.",
                result.stdout,
            )
            self.assertFalse(fixture.kill_log.exists())

    def test_missing_ppid_status_is_skipped(self):
        """Unreadable / incomplete status (no PPid:) must skip, not reap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "701 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            process_dir = fixture.proc_root / "701"
            process_dir.mkdir()
            # Status without PPid: — the awk extract yields empty → SKIPPED.
            (process_dir / "status").write_text("Name:\tpython\n", encoding="utf-8")
            (process_dir / "cmdline").write_bytes(b"\0".join(part.encode("utf-8") for part in ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"]) + b"\0")

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertIn(
                "Dry-run summary: 0 would be reaped, 0 kept (live parent), 0 protected (live experiment), 1 skipped.",
                result.stdout,
            )
            self.assertFalse(fixture.kill_log.exists())


class TestLiveExperimentProtection(unittest.TestCase):
    """A live experiment stack / campaign must never be reaped.

    ``experiment_stack.bash`` launches its services with ``nohup`` inside a
    subshell, so they reparent to ``systemd --user`` — the reaper's own orphan
    predicate. Observed live on 2026-08-16 against campaign
    ``e-j-h2h-wide-cap6``: a ``--dry-run`` classified the campaign
    orchestrator, the experiment cascor service, and the follow-on watchdog
    all as ``WOULD REAP`` while every one of them was healthy and wanted.

    The shapes below reproduce those three processes.
    """

    CASCOR_SERVICE = [
        "/opt/miniforge3/envs/JuniperCascor1/bin/python3.13",
        "/opt/miniforge3/envs/JuniperCascor1/bin/uvicorn",
        "api.app:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        "8230",
    ]
    CASCOR_SERVICE_PS = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.13 /opt/miniforge3/envs/JuniperCascor1/bin/uvicorn api.app:create_app --factory --port 8230"
    WORKTREE_PY = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--exp--h2h--3909d275/src"

    def test_pidfiled_experiment_service_is_protected_not_reaped(self):
        """P1: the service carries a run-dir pidfile, so parentage is irrelevant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    f"977934 testuser {self.CASCOR_SERVICE_PS}",
                ],
            )
            # Reparented to systemd --user — the orphan predicate fires.
            fixture.add_process(977934, 50, self.CASCOR_SERVICE)
            fixture.add_experiment_pidfile("20260816T161315Z-84c0", "juniper-cascor", 977934)

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=977934 ppid=50 (live experiment)", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertIn(
                "Dry-run summary: 0 would be reaped, 0 kept (live parent), 1 protected (live experiment), 0 skipped.",
                result.stdout,
            )
            self.assertFalse(fixture.kill_log.exists())

    def test_campaign_orchestrator_referencing_run_root_is_protected(self):
        """P2: orchestrators and watchdogs carry no pidfile — the cmdline is the key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    f"553615 testuser bash h2h_orchestrate.bash {self.WORKTREE_PY}",
                    f"1765020 testuser bash -c watchdog {self.WORKTREE_PY}",
                ],
            )
            suite_dir = f"{fixture.exp_run_root}/suites/e-j-h2h-wide-cap64-20260816T125456Z"
            fixture.add_process(553615, 50, ["bash", "h2h_orchestrate.bash", suite_dir, self.WORKTREE_PY])
            fixture.add_process(
                1765020,
                50,
                ["bash", "-c", f"while kill -0 553615; do sleep 60; done; exec bash h2h_init_control.bash {fixture.exp_run_root}/h2h-wide/cli {self.WORKTREE_PY}"],
            )

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=553615 ppid=50 (live experiment)", result.stdout)
            self.assertIn("PROTECT    pid=1765020 ppid=50 (live experiment)", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)
            self.assertIn(
                "Dry-run summary: 0 would be reaped, 0 kept (live parent), 2 protected (live experiment), 0 skipped.",
                result.stdout,
            )

    def test_isolated_stack_run_dir_is_also_protected(self):
        """The isolated E2E stack's run dir (JUNIPER_E2E_RUN_DIR) protects too."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    f"8202 testuser /opt/miniforge3/envs/JuniperCascor1/bin/python -m uvicorn {self.WORKTREE_PY}",
                ],
            )
            fixture.add_process(
                8202,
                50,
                ["/opt/miniforge3/envs/JuniperCascor1/bin/python", "-m", "uvicorn", f"--log-config={fixture.e2e_run_dir}/logs/cascor.json"],
            )

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=8202 ppid=50 (live experiment)", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)

    def test_real_mode_kills_the_orphan_but_never_the_protected_service(self):
        """The load-bearing arm: live mode, mixed set, only the true orphan dies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    f"977934 testuser {self.CASCOR_SERVICE_PS}",
                    "888 testuser /opt/conda/envs/JuniperCaa/bin/python -c forkserver",
                ],
            )
            fixture.add_process(977934, 50, self.CASCOR_SERVICE)
            fixture.add_experiment_pidfile("20260816T161315Z-84c0", "juniper-cascor", 977934)
            # A genuine crashed-pytest orphan: same parentage, no pidfile, no
            # run-root reference. Protection must not swallow it.
            fixture.add_process(888, 50, ["/opt/conda/envs/JuniperCaa/bin/python", "-c", "forkserver"])

            result = run_script(fixture)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=977934 ppid=50 (live experiment)", result.stdout)
            self.assertIn("REAP       pid=888 ppid=50", result.stdout)
            self.assertIn(
                "Summary: 1 reaped, 0 kept (live parent), 1 protected (live experiment), 0 skipped.",
                result.stdout,
            )
            self.assertEqual(fixture.kill_log.read_text(encoding="utf-8"), "-KILL 888\n")

    def test_stale_pidfile_protects_conservatively(self):
        """A torn-down run's leftover pidfile errs toward keeping, never killing.

        Over-protection costs one retained orphan until the next sweep; a false
        reap costs a multi-hour campaign. The asymmetry is deliberate.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "4242 testuser /opt/conda/envs/JuniperCaa/bin/python -c forkserver",
                ],
            )
            fixture.add_process(4242, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-c", "forkserver"])
            fixture.add_experiment_pidfile("20260101T000000Z-dead", "juniper-cascor", 4242)

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=4242 ppid=1 (live experiment)", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_malformed_pidfile_does_not_abort_the_sweep(self):
        """A non-numeric / empty pidfile is ignored, not fatal under set -euo pipefail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "909 testuser /opt/conda/envs/JuniperCaa/bin/python -c forkserver",
                ],
            )
            fixture.add_process(909, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-c", "forkserver"])
            run_dir = fixture.exp_run_root / "20260816T000000Z-bad"
            run_dir.mkdir(parents=True)
            (run_dir / "juniper-data.pid").write_text("", encoding="utf-8")
            (run_dir / "juniper-cascor.pid").write_text("not-a-pid\n", encoding="utf-8")

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WOULD REAP pid=909 ppid=1", result.stdout)
            self.assertIn(
                "Dry-run summary: 1 would be reaped, 0 kept (live parent), 0 protected (live experiment), 0 skipped.",
                result.stdout,
            )


class TestIsolatedStackRunDirRoots(unittest.TestCase):
    """The 2026-10-26 repo tmp/ rule moved the isolated stack's run dir out of the system temp dir.

    Its default is now FIXED -- the juniper-ml primary checkout's ``tmp/juniper-e2e``, the path
    ``util/isolated_stack.bash`` defaults to -- because a root derived from ``TMPDIR`` protects nothing
    when the stack was launched under a different ``TMPDIR``, and every session sets one now. The run
    dirs older checkouts defaulted to stay protected, read-only: a stack they launched may still run.
    """

    ORPHAN = ["/opt/conda/envs/JuniperCaa/bin/python", "-c", "forkserver"]
    ORPHAN_PS = "/opt/conda/envs/JuniperCaa/bin/python -c forkserver"

    @staticmethod
    def _pidfile(directory: Path, name: str, pid: int) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{name}.pid").write_text(f"{pid}\n", encoding="utf-8")

    def _copied_checkout(self, fixture: FakeProcessFixture, *, git_init: bool) -> tuple[Path, dict[str, str]]:
        """The reaper and its helper copied into a fresh checkout (or a plain directory) under the fixture."""
        checkout = fixture.root / ("checkout" if git_init else "plain")
        (checkout / "util").mkdir(parents=True)
        for name in ("reap_pytest_orphans.bash", "juniper_repo_tmp.bash"):
            shutil.copy2(SCRIPT_PATH.parent / name, checkout / "util" / name)
        env = {k: v for k, v in fixture.env().items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_CEILING_DIRECTORIES=str(fixture.root))
        del env["JUNIPER_E2E_RUN_DIR"]
        if git_init:
            subprocess.run(["git", "init", "-q", str(checkout)], env=env, check=True, capture_output=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        return checkout, env

    def _run(self, script: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)

    def test_a_pidfile_in_the_legacy_fixed_root_is_protected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, ["50 testuser /usr/lib/systemd/systemd --user", f"8202 testuser {self.ORPHAN_PS}"])
            fixture.add_process(8202, 50, self.ORPHAN)
            self._pidfile(fixture.legacy_e2e_run_dir, "juniper-cascor", 8202)
            result = run_script(fixture, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=8202 ppid=50 (live experiment)", result.stdout)
            self.assertNotIn("WOULD REAP", result.stdout)

    def test_a_pidfile_in_the_tmpdir_derived_legacy_root_is_protected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, ["50 testuser /usr/lib/systemd/systemd --user", f"8051 testuser {self.ORPHAN_PS}"])
            fixture.add_process(8051, 50, self.ORPHAN)
            self._pidfile(fixture.tmpdir / "juniper-e2e", "juniper-canopy", 8051)
            result = run_script(fixture, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=8051 ppid=50 (live experiment)", result.stdout)

    def test_a_cmdline_naming_a_legacy_root_is_protected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, ["50 testuser /usr/lib/systemd/systemd --user", f"8101 testuser {self.ORPHAN_PS}"])
            fixture.add_process(8101, 50, [f"{fixture.legacy_e2e_run_dir}/.venv-data/bin/python", "-m", "juniper_data", "JuniperCaa"])
            result = run_script(fixture, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=8101 ppid=50 (live experiment)", result.stdout)

    def test_the_legacy_roots_protect_only_what_they_hold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, ["50 testuser /usr/lib/systemd/systemd --user", f"777 testuser {self.ORPHAN_PS}"])
            fixture.add_process(777, 50, self.ORPHAN)
            self._pidfile(fixture.legacy_e2e_run_dir, "juniper-cascor", 999)
            result = run_script(fixture, "--dry-run")
            self.assertIn("WOULD REAP pid=777 ppid=50", result.stdout)

    def test_the_default_run_dir_is_the_checkouts_tmp_and_not_tmpdir(self):
        """JUNIPER_E2E_RUN_DIR unset: the copied reaper protects the checkout's tmp/juniper-e2e, whatever TMPDIR says."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                ["50 testuser /usr/lib/systemd/systemd --user", f"8202 testuser {self.ORPHAN_PS}", f"8888 testuser {self.ORPHAN_PS}"],
            )
            fixture.add_process(8202, 50, self.ORPHAN)
            fixture.add_process(8888, 50, self.ORPHAN)
            checkout, env = self._copied_checkout(fixture, git_init=True)
            self._pidfile(checkout / "tmp" / "juniper-e2e", "juniper-cascor", 8202)
            result = self._run(checkout / "util" / "reap_pytest_orphans.bash", env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTECT    pid=8202 ppid=50 (live experiment)", result.stdout)
            self.assertIn("WOULD REAP pid=8888 ppid=50", result.stdout)
            self.assertNotEqual(Path(env["TMPDIR"]), checkout / "tmp")

    def test_an_unresolvable_default_exits_1_and_reaps_nothing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, ["50 testuser /usr/lib/systemd/systemd --user", f"888 testuser {self.ORPHAN_PS}"])
            fixture.add_process(888, 50, self.ORPHAN)
            plain, env = self._copied_checkout(fixture, git_init=False)
            result = self._run(plain / "util" / "reap_pytest_orphans.bash", env)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("nothing reaped", result.stderr)
            self.assertNotIn("REAP", result.stdout)
            self.assertFalse(fixture.kill_log.exists())
            self.assertFalse((plain / "tmp").exists())

    def test_help_names_the_legacy_roots_without_resolving_the_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(tmpdir, [])
            plain, env = self._copied_checkout(fixture, git_init=False)
            result = self._run(plain / "util" / "reap_pytest_orphans.bash", env, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(fixture.legacy_e2e_run_dir), result.stdout)
            self.assertIn(f"{fixture.tmpdir}/juniper-e2e", result.stdout)
            self.assertIn("never derived from TMPDIR", result.stdout)

    def test_the_legacy_literal_is_the_only_one_and_carries_the_pragma(self):
        lines = [line for line in SCRIPT_PATH.read_text(encoding="utf-8").splitlines() if "juniper-e2e" in line and "${TMPDIR" not in line and "JUNIPER_REAP_LEGACY_E2E_RUN_DIR:-" in line]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("tmp-path-literal: allow", lines[0])


if __name__ == "__main__":
    unittest.main()
