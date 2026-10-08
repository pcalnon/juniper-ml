"""Refusal gates in the CAN-015 replay re-drive stack wrapper.

``util/ad-hoc/2026-10-04_replay_redrive_stack.bash`` (merged with the live re-drive,
ml#2120) is the only thing standing between that re-drive and the shared trio. It
hard-sets its own ports, refuses ``--up`` while one of them is already listening, and
refuses ``--down`` for a listener whose pid this run did not record. A miss tears down
somebody else's stack. No other suite executes this script.

The listener table is a ``ss`` stub. The one ``--down`` that is allowed through execs
the real ``util/isolated_stack.bash``, which kills by pid: the stub reports a pid that
is not alive, and the run dir is a temp ecosystem, so a fall-through cannot signal a
live process or delete a real checkout.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT = Path(__file__).resolve().parent.parent / "util" / "ad-hoc" / "2026-10-04_replay_redrive_stack.bash"
STACK_NOT_REACHED = ("Bringing UP the isolated E2E trio", "Bringing DOWN the isolated E2E trio", "Isolated E2E trio status")


def _dead_pid() -> str:
    """A pid ``kill`` cannot reach. ProcessLookupError means it is not alive."""
    candidate = 2_100_000_000
    while candidate > 2:
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return str(candidate)
        except PermissionError:
            candidate -= 1
            continue
        candidate -= 1
    raise RuntimeError("no unused pid")


DEAD_PID = _dead_pid()


class ReplayRedriveStackRefusalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stub_bin = self.root / "bin"
        self.stub_bin.mkdir()
        self.ss_config = self.root / "ss.conf"
        self.ss_config.write_text("", encoding="utf-8")
        self._write_ss_stub()
        with self.assertRaises(ProcessLookupError):
            os.kill(int(DEAD_PID), 0)

    def _write_ss_stub(self) -> None:
        stub = self.stub_bin / "ss"
        stub.write_text(
            textwrap.dedent(f"""\
                #!/usr/bin/env bash
                mode="any"
                port=""
                for arg in "$@"; do
                    case "$arg" in
                        -tlnpH) mode="pid" ;;
                        -tlnH) mode="any" ;;
                        "sport = :"*) port="${{arg#sport = :}}" ;;
                    esac
                done
                [[ -f "{self.ss_config}" ]] || exit 0
                while read -r listed pid; do
                    [[ "$listed" == "$port" ]] || continue
                    if [[ "$mode" == "any" ]]; then
                        printf 'LISTEN %s\\n' "$port"
                    elif [[ -n "$pid" && "$pid" != "-" ]]; then
                        printf 'pid=%s\\n' "$pid"
                    fi
                    exit 0
                done < "{self.ss_config}"
                exit 0
                """),
            encoding="utf-8",
        )
        stub.chmod(0o755)

    def _listeners(self, rows: dict[str, str]) -> None:
        """Map port -> pid. A pid of ``-`` is a listener whose pid ``ss -p`` hides."""
        self.ss_config.write_text("".join(f"{port} {pid}\n" for port, pid in rows.items()), encoding="utf-8")

    def _eco(self, path: Path | None = None, legs: tuple[str, ...] = ("juniper-data", "juniper-cascor", "juniper-canopy")) -> Path:
        eco = path if path is not None else self.root / "eco"
        for leg in legs:
            (eco / leg).mkdir(parents=True, exist_ok=True)
        return eco

    def _run(
        self,
        *args: str,
        eco: str | None = "",
        cwd: Path | None = None,
        extra: dict[str, str] | None = None,
        script: Path = SCRIPT,
    ) -> subprocess.CompletedProcess[str]:
        env = RedactedEnv(
            os.environ,
            PATH=f"{self.stub_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            JUNIPER_REDRIVE_ECO="" if eco is None else eco,
        )
        if extra:
            env.update(extra)
        return subprocess.run(
            ["bash", str(script), *args],
            cwd=cwd or self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def _assert_refused(self, result: subprocess.CompletedProcess[str], needle: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(needle, result.stderr)
        blob = result.stdout + result.stderr
        for marker in STACK_NOT_REACHED:
            self.assertNotIn(marker, blob)

    def _script_rooted_at(self, ecosystem_root: Path) -> Path:
        """The real wrapper with only its primary-tree constant pointed at a temp dir.

        ``/home/pcalnon/...`` is not creatable here, and the refusal happens before the
        wrapper execs ``isolated_stack.bash``, so the copy's own path does not matter.
        The comparison itself is the committed one.
        """
        canonical = "/home/pcalnon/Development/python/Juniper"
        text = SCRIPT.read_text(encoding="utf-8")
        needle = f'ECOSYSTEM_ROOT="{canonical}"'
        self.assertEqual(text.count(needle), 1)
        copy = self.root / "replay-redrive-stack.bash"
        copy.write_text(text.replace(needle, f'ECOSYSTEM_ROOT="{ecosystem_root}"', 1), encoding="utf-8")
        return copy

    def test_an_empty_eco_refuses_before_any_port_work(self) -> None:
        result = self._run("--dry-run", "--status", eco="")
        self._assert_refused(result, "JUNIPER_REDRIVE_ECO is empty")

    def test_a_missing_eco_refuses(self) -> None:
        missing = self.root / "no-such-eco"
        result = self._run("--status", eco=str(missing))
        self._assert_refused(result, "JUNIPER_REDRIVE_ECO does not exist")

    def test_a_missing_leg_is_named(self) -> None:
        eco = self._eco(legs=("juniper-data", "juniper-cascor"))
        result = self._run("--dry-run", "--up", eco=str(eco))
        self._assert_refused(result, f"{eco}/juniper-canopy is missing")

    def test_an_eco_inside_the_real_ecosystem_root_refuses_including_via_symlink(self) -> None:
        primary = self.root / "primaries"
        primary.mkdir()
        inside = primary / "checkout"
        inside.mkdir()
        script = self._script_rooted_at(primary)
        direct = self._run("--dry-run", "--status", eco=str(inside), script=script)
        self._assert_refused(direct, "inside the real ecosystem root")
        same = self._run("--dry-run", "--status", eco=str(primary), script=script)
        self._assert_refused(same, "inside the real ecosystem root")
        link = self.root / "eco-link"
        link.symlink_to(inside, target_is_directory=True)
        via_link = self._run("--dry-run", "--up", eco=str(link), script=script)
        self._assert_refused(via_link, "inside the real ecosystem root")

    def test_a_lookalike_directory_outside_that_root_is_not_the_primary_tree(self) -> None:
        eco = self._eco(self.root / "Juniper" / "eco")
        result = self._run("--dry-run", "--status", eco=str(eco))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("REFUSING", result.stderr)
        self.assertIn("Isolated E2E trio status", result.stdout)

    def test_a_relative_eco_is_resolved_from_the_callers_directory(self) -> None:
        eco = self._eco(self.root / "relative-eco")
        result = self._run("--dry-run", "--status", eco=eco.name, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(str(eco), result.stdout)

    def test_caller_exported_default_ports_cannot_move_a_leg_onto_the_shared_trio(self) -> None:
        eco = self._eco()
        result = self._run(
            "--dry-run",
            "--status",
            eco=str(eco),
            extra={
                "JUNIPER_E2E_DATA_PORT": "8101",
                "JUNIPER_E2E_CASCOR_PORT": "8202",
                "JUNIPER_E2E_CANOPY_PORT": "8051",
                "JUNIPER_E2E_RECURRENCE_PORT": "8211",
            },
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ports: data=8113 cascor=8214 canopy=8063", result.stdout)
        for port in ("8113", "8214", "8063", "8223"):
            self.assertIn(f"127.0.0.1:{port}", result.stdout)
        for stolen in ("8101", "8202", "8051", "8211"):
            self.assertNotIn(f"127.0.0.1:{stolen}", result.stdout)

    def test_the_hard_set_ports_stay_disjoint_from_the_forbidden_list(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        forbidden = set(re.search(r"^FORBIDDEN_PORTS=\(([^)]*)\)", text, re.M).group(1).split())
        exports = dict(re.findall(r"^export (JUNIPER_E2E_(?:DATA|CASCOR|CANOPY|RECURRENCE)_PORT)=(\d+)$", text, re.M))
        self.assertEqual(
            set(exports),
            {"JUNIPER_E2E_DATA_PORT", "JUNIPER_E2E_CASCOR_PORT", "JUNIPER_E2E_CANOPY_PORT", "JUNIPER_E2E_RECURRENCE_PORT"},
        )
        self.assertLessEqual({"8101", "8202", "8051"}, forbidden)
        self.assertTrue(set(exports.values()).isdisjoint(forbidden))

    def test_with_recurrence_is_refused_and_the_stack_is_not_started(self) -> None:
        eco = self._eco()
        result = self._run("--dry-run", "--up", "--with-recurrence", eco=str(eco))
        self._assert_refused(result, "--with-recurrence is not needed")

    def test_no_action_refuses(self) -> None:
        eco = self._eco()
        result = self._run("--dry-run", eco=str(eco))
        self._assert_refused(result, "one of --up / --status / --down is required")

    def test_up_refuses_a_listener_on_the_recurrence_port_and_creates_nothing(self) -> None:
        eco = self._eco()
        self._listeners({"8223": DEAD_PID})
        result = self._run("--up", eco=str(eco))
        self._assert_refused(result, f"--up: port 8223 already has a listener (pid {DEAD_PID})")
        self.assertFalse((eco / "run" / "cascor-snapshots").exists())

    def test_dry_run_up_does_not_treat_a_taken_port_as_a_refusal(self) -> None:
        eco = self._eco()
        self._listeners({"8113": DEAD_PID})
        result = self._run("--dry-run", "--up", eco=str(eco))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DRY-RUN: printing commands only, launching nothing", result.stdout)
        self.assertNotIn("REFUSING", result.stderr)
        self.assertFalse((eco / "run" / "cascor-snapshots").exists())
        self.assertIn("8113", result.stdout)

    def test_down_refuses_a_listener_this_run_did_not_record(self) -> None:
        eco = self._eco()
        snapshots = eco / "juniper-canopy" / "src" / "snapshots"
        snapshots.mkdir(parents=True)
        sentinel = snapshots / "snapshot_probe.h5"
        sentinel.write_text("keep", encoding="utf-8")
        self._listeners({"8214": DEAD_PID})
        result = self._run("--down", eco=str(eco))
        self._assert_refused(result, f"--down: port 8214 is held by pid {DEAD_PID}, which this run did not record")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        with self.assertRaises(ProcessLookupError):
            os.kill(int(DEAD_PID), 0)

    def test_a_blank_pidfile_and_a_prefix_of_the_listener_do_not_count_as_ownership(self) -> None:
        eco = self._eco()
        run = eco / "run"
        run.mkdir()
        (run / "blank.pid").write_text("   \n", encoding="utf-8")
        (run / "prefix.pid").write_text(DEAD_PID[:-1] + "\n", encoding="utf-8")
        self._listeners({"8063": DEAD_PID})
        result = self._run("--down", eco=str(eco))
        self._assert_refused(result, f"--down: port 8063 is held by pid {DEAD_PID}, which this run did not record")

    def test_down_refuses_a_listener_whose_pid_is_not_visible(self) -> None:
        eco = self._eco()
        self._listeners({"8113": "-"})
        result = self._run("--down", eco=str(eco))
        self._assert_refused(result, "--down: port 8113 has a listener whose pid is not visible")

    def test_down_allows_a_whitespace_padded_recorded_pid_and_sweeps_only_h5(self) -> None:
        eco = self._eco()
        run = eco / "run"
        run.mkdir()
        (run / "juniper-cascor.pid").write_text(f"  {DEAD_PID} \n", encoding="utf-8")
        snapshots = eco / "juniper-canopy" / "src" / "snapshots"
        snapshots.mkdir(parents=True)
        h5 = snapshots / "snapshot_probe.h5"
        module = snapshots / "snapshot_probe.py"
        h5.write_text("artifact", encoding="utf-8")
        module.write_text("package", encoding="utf-8")
        self._listeners({"8113": DEAD_PID})
        result = self._run("--down", eco=str(eco))
        blob = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, blob)
        self.assertIn("Bringing DOWN the isolated E2E trio", result.stdout)
        self.assertIn("Teardown complete", result.stdout)
        self.assertIn(f"Stopping juniper-data (pid {DEAD_PID}) on port 8113", result.stdout)
        self.assertNotIn("REFUSING", result.stderr)
        self.assertFalse(h5.exists())
        self.assertEqual(module.read_text(encoding="utf-8"), "package")
        self.assertIn(str(eco / "juniper-canopy" / "src"), result.stdout)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(DEAD_PID), 0)

    def test_two_actions_are_rejected_by_the_stack_and_do_not_tear_down(self) -> None:
        eco = self._eco()
        snapshots = eco / "juniper-canopy" / "src" / "snapshots"
        snapshots.mkdir(parents=True)
        sentinel = snapshots / "snapshot_probe.h5"
        sentinel.write_text("keep", encoding="utf-8")
        result = self._run("--up", "--down", eco=str(eco))
        blob = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, blob)
        self.assertIn("choose exactly one of --up / --down / --status", blob)
        self.assertNotIn("REFUSING", result.stderr)
        self.assertNotIn("Teardown complete", blob)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
