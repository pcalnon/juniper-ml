#!/usr/bin/env python3
"""Gate for ci.yml's host-tooling-macos job (turing bring-up task G4).

Project:     Juniper
Sub-Project: juniper-ml
Application: CI workflow regression tests
Author:      Paul Calnon
License:     MIT License

Task G4 of ``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` runs the host-tooling
suites on ``macos-latest``, under BSD userland and ``/bin/bash`` 3.2, which Linux CI cannot show. Its shape is
fixed by the plan:

- no ``on.paths`` filter. A change-detection step sets ``relevant``, and every later step is ``if:``-gated on
  it, so the job reports success when nothing relevant changed. It fires on ``merge_group`` too;
- the suites themselves call ``/bin/bash``, and a step asserts that the runner's ``/bin/bash`` is 3.x and that
  ``brew --prefix`` is not turing's Intel ``/usr/local``, so a green run shows prefix independence;
- required through the Quality Gate. It was advisory until 2026-10-20, when, after 12 consecutive green push
  runs on main, it joined ``required-checks.needs`` with its own ``!= success`` arm, never as a separate
  ruleset context. ``test_the_job_is_required_through_the_quality_gate`` pins that.

Neither the workflow YAML nor the detection shell is otherwise gated, so this suite is the gate. The detection
step is extracted from ci.yml and run under a stub ``git``, the idiom of ``tests/test_ci_precommit_g4.py``.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - runs the workflow's own extracted shell under a stub git
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
JOB = "host-tooling-macos"
DETECT_STEP = "Detect host-tooling changes"
TIMEOUT_SECONDS = 60

# The turing bring-up suites whose scripts run on the host (plan §8).
SUITES = {
    "juniper_clone",
    "find_encryption_readme_notes",
    "macvm_ctl",
    "claude_agent_guard",
    "git_remote_alias_check",
    "headless_signing_preflight",
    "juniper_repo_ssh_setup",
    "home_path_literal_check",
    "configure_commit_signing",  # commit-signing plan K2
    "host_state_probe",  # G1
    "host_state_check",  # G1
}


def load_workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)  # nosec B506 - BaseLoader keeps `on:` a string key


class JobShapeTest(unittest.TestCase):
    workflow: dict
    job: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = load_workflow()
        cls.job = cls.workflow["jobs"][JOB]

    def test_the_job_runs_on_macos_latest(self) -> None:
        self.assertEqual(self.job["runs-on"], "macos-latest")
        self.assertEqual(self.job["name"], "Host Tooling (macOS)")
        self.assertEqual(self.job["permissions"], {"contents": "read"})

    def test_the_workflow_has_no_path_filter_and_fires_on_merge_group(self) -> None:
        triggers = self.workflow["on"]
        self.assertIn("merge_group", triggers)
        for event in ("push", "pull_request", "merge_group"):
            spec = triggers.get(event) or {}
            self.assertNotIn("paths", spec, f"{event}: a path filter would skip all of ci.yml, not just this job")
            self.assertNotIn("paths-ignore", spec, event)

    def test_the_job_is_not_skipped_by_event(self) -> None:
        self.assertNotIn("if", self.job, "a job-level if would leave the context unreported, which a future required check cannot tolerate")

    def test_every_step_after_detection_is_gated_on_it(self) -> None:
        steps = self.job["steps"]
        names = [step.get("name") for step in steps]
        self.assertIn(DETECT_STEP, names)
        detect = names.index(DETECT_STEP)
        self.assertEqual(steps[detect].get("id"), "changes")
        self.assertEqual(names[:detect], ["Checkout Code (full history)"])
        self.assertEqual(steps[0]["with"]["fetch-depth"], "0")
        gated = steps[detect + 1 :]
        self.assertGreaterEqual(len(gated), 4)
        for step in gated:
            with self.subTest(step=step.get("name")):
                self.assertIn("steps.changes.outputs.relevant", step.get("if", ""))
        skip = [step for step in gated if step.get("if", "").replace(" ", "") == "steps.changes.outputs.relevant!='true'"]
        self.assertEqual(len(skip), 1, "exactly one step reports the skip")

    def test_the_suites_are_the_host_tooling_set_and_exist(self) -> None:
        listed = set(self.job["env"]["HOST_TOOLING_SUITES"].split())
        self.assertEqual(listed, SUITES)
        for suite in listed:
            self.assertTrue((REPO_ROOT / "tests" / f"test_{suite}.py").is_file(), suite)

    def test_every_listed_path_exists(self) -> None:
        for rel in self.job["env"]["HOST_TOOLING_PATHS"].split():
            with self.subTest(rel=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), rel)

    def test_each_suite_also_runs_in_the_linux_regression_step(self) -> None:
        step = next(s for s in self.workflow["jobs"]["tests"]["steps"] if s.get("name") == "Run Python regression tests")
        for suite in SUITES:
            self.assertRegex(step["run"], rf"(?m)^\s*python3 -m unittest -v tests/test_{suite}\.py$")

    def test_the_userland_assertion_checks_bash_3_and_the_brew_prefix(self) -> None:
        step = next(s for s in self.job["steps"] if s.get("name") == "Assert the macOS userland under test")
        self.assertIn("/bin/bash -c 'echo \"${BASH_VERSINFO[0]}\"'", step["run"])
        self.assertIn('[ "$bash_major" = 3 ]', step["run"])
        self.assertIn('prefix="$(brew --prefix)"', step["run"])
        self.assertIn('[ "$prefix" != /usr/local ]', step["run"])

    def test_the_suites_run_one_by_one_and_every_failure_is_reported(self) -> None:
        step = next(s for s in self.job["steps"] if s.get("name") == "Run the host-tooling suites")
        self.assertIn("for suite in $HOST_TOOLING_SUITES; do", step["run"])
        self.assertIn('python3 -m unittest -v "tests/test_${suite}.py"', step["run"])
        self.assertIn('failed="$failed $suite"', step["run"])

    def test_the_job_is_required_through_the_quality_gate(self) -> None:
        # Promoted 2026-10-20 after 12 consecutive green push runs (plan G4). A need with no arm gates nothing.
        gate = self.workflow["jobs"]["required-checks"]
        self.assertIn(JOB, gate["needs"])
        script = next(s for s in gate["steps"] if s.get("name") == "Check Quality Gate Status")["run"]
        self.assertIn('if [[ "${{ needs.host-tooling-macos.result }}" != "success" ]]; then', script)


class DetectionRehearsalTest(unittest.TestCase):
    """Run the workflow's own detection shell over the event matrix with a stub git."""

    script: str
    env_block: dict
    job_env: dict

    @classmethod
    def setUpClass(cls) -> None:
        job = load_workflow()["jobs"][JOB]
        step = next(s for s in job["steps"] if s.get("name") == DETECT_STEP)
        cls.script = step["run"]
        cls.env_block = step["env"]
        cls.job_env = job["env"]

    def detect(self, event: str, changed: list[str], *, have_base: bool = True) -> tuple[str, str, list[str]]:
        """Return (relevant, output, git argv log)."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "bin").mkdir()
            log = tmp / "git.log"
            (tmp / "changed.txt").write_text("".join(f"{rel}\n" for rel in changed), encoding="utf-8")
            git = tmp / "bin" / "git"
            git.write_text(
                "#!/bin/bash\n" f'printf "%s\\n" "$*" >> "{log}"\n' 'case "$1" in\n' f"  cat-file) exit {0 if have_base else 1} ;;\n" "  fetch) exit 0 ;;\n" f'  diff) cat "{tmp / "changed.txt"}" ;;\n' '  *) echo "unexpected git argv: $*" >&2; exit 99 ;;\n' "esac\n",
                encoding="utf-8",
            )
            git.chmod(0o700)
            output = tmp / "github_output"
            output.touch()
            env = RedactedEnv(
                os.environ,
                PATH=f"{tmp / 'bin'}:{os.environ['PATH']}",
                GITHUB_OUTPUT=str(output),
                EVENT_NAME=event,
                PR_BASE_SHA="prbase1111111111111111111111111111111111",
                MG_BASE_SHA="mgbase2222222222222222222222222222222222",
                HOST_TOOLING_SUITES=self.job_env["HOST_TOOLING_SUITES"],
                HOST_TOOLING_PATHS=self.job_env["HOST_TOOLING_PATHS"],
            )
            proc = subprocess.run(["bash", "-e", "-c", self.script], cwd=tmp, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            lines = output.read_text(encoding="utf-8").splitlines()
            calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertEqual(len(lines), 1, lines)
        match = re.fullmatch(r"relevant=(true|false)", lines[0])
        self.assertIsNotNone(match, lines)
        return match.group(1), proc.stdout, calls

    def test_the_env_wires_the_event_and_both_base_shas(self) -> None:
        self.assertEqual(self.env_block, {"EVENT_NAME": "${{ github.event_name }}", "PR_BASE_SHA": "${{ github.event.pull_request.base.sha }}", "MG_BASE_SHA": "${{ github.event.merge_group.base_sha }}"})

    def test_push_and_dispatch_always_run_without_diffing(self) -> None:
        for event in ("push", "workflow_dispatch"):
            with self.subTest(event=event):
                relevant, _, calls = self.detect(event, [])
                self.assertEqual(relevant, "true")
                self.assertEqual(calls, [])

    def test_an_unrelated_pull_request_skips(self) -> None:
        relevant, out, calls = self.detect("pull_request", ["docs/REFERENCE.md", "util/run_suite.py", "tests/test_run_suite.py", "util/ad-hoc/2026-10-20_x.py"])
        self.assertEqual(relevant, "false")
        self.assertIn("diff --name-only prbase1111111111111111111111111111111111 HEAD", calls)
        self.assertIn("no host-tooling path changed", out)

    def test_a_suite_a_script_or_the_workflow_makes_it_run(self) -> None:
        paths = [f"tests/test_{suite}.py" for suite in sorted(SUITES)] + self.job_env["HOST_TOOLING_PATHS"].split() + ["tests/redacted_env.py", ".github/workflows/ci.yml"]
        for rel in paths:
            with self.subTest(rel=rel):
                relevant, out, _ = self.detect("pull_request", ["docs/x.md", rel])
                self.assertEqual(relevant, "true")
                self.assertIn(rel, out)

    def test_a_near_miss_path_does_not_count(self) -> None:
        for rel in ("tests/test_macvm_ctl.py.orig", "util/macvm_ctl.bash.bak", "docs/util/macvm_ctl.bash", "tests/test_macvm_ctl_extra.py"):
            with self.subTest(rel=rel):
                self.assertEqual(self.detect("pull_request", [rel])[0], "false")

    def test_merge_group_diffs_against_its_own_base(self) -> None:
        relevant, _, calls = self.detect("merge_group", ["util/macvm_ctl.bash"])
        self.assertEqual(relevant, "true")
        self.assertIn("diff --name-only mgbase2222222222222222222222222222222222 HEAD", calls)

    def test_a_missing_base_is_fetched_first(self) -> None:
        _, _, calls = self.detect("pull_request", ["util/macvm_ctl.bash"], have_base=False)
        self.assertEqual(calls[1], "fetch --no-tags --depth=1 origin prbase1111111111111111111111111111111111")


if __name__ == "__main__":
    unittest.main()
