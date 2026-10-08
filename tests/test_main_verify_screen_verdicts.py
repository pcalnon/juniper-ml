#!/usr/bin/env python3
"""YAML-extraction rehearsal for main-verify.yml's screen coverage vs cleanliness split.

The catch-up base ratchets on SCREENED, not on GREEN (2026-08-23). A compositional-loss
finding (exit 1) is a verdict: the window was screened, so the base must advance, and the
job must still go red. An invocation error (exit >=2) or a missing code is not a verdict:
the base must stay put, and the job must not go green.

``tests/test_main_verify_catchup_base.py`` pins the step names and that the screens step's
source does not contain the text ``exit 1``. It does not execute the three shells. Renaming
``-ge 2`` to ``-ge 1`` on the coverage step, or dropping ``set +e`` so a finding aborts the
screens step, leaves those pins green and restores the recurring-red defect.

This unittest extracts the workflow's OWN shells (not a reimplementation) and drives them
the way Actions does (``bash -eo pipefail``). The two console scripts and ``git`` are PATH
stubs. Neither shell is otherwise lint-gated for the exit-code split, so this unittest IS
the gate.

Run: python3 -m unittest -v tests/test_main_verify_screen_verdicts.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-10-05
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "main-verify.yml"
JOB_NAME = "symbol-screen"
SCREENS_STEP = "Run sequence-safety screens (symbol + docs)"
VERDICT_STEP = "Assert screens reached a verdict"
CLEAN_STEP = "Assert screens clean"

RESOLVABLE = "a" * 40
FALLBACK = "b" * 40
HEAD = "c" * 40
UNRESOLVABLE = "d" * 40


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


def _step_script(name: str) -> str:
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
    if not wf.is_file():
        raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
    doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
    steps = doc.get("jobs", {}).get(JOB_NAME, {}).get("steps", [])
    step = next((s for s in steps if s.get("name") == name), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {name!r} run step in {WORKFLOW_NAME}")
    return step["run"]


def _run_bash(script: str, env: RedactedEnv, cwd: Path) -> subprocess.CompletedProcess[str]:
    script_path = cwd / "step.sh"
    script_path.write_text(script, encoding="utf-8")
    # Actions' default shell is `bash -eo pipefail`. The screens step relies on its own
    # `set +e` to record a finding instead of aborting; invoking without -e would hide
    # the loss of that line.
    return subprocess.run(  # nosec B603 - workflow shell, fixed argv
        ["bash", "-eo", "pipefail", str(script_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )


def _outputs(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    parsed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key] = value
    return parsed


class ScreenVerdictRehearsalTest(unittest.TestCase):
    """Execute the two assert shells. A finding is coverage; it is not cleanliness."""

    verdict: str
    clean: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.verdict = _step_script(VERDICT_STEP)
        cls.clean = _step_script(CLEAN_STEP)

    def _assert(self, script: str, *, src: str | None, drc: str | None, head: str = HEAD) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as td:
            env = RedactedEnv(os.environ)
            env["HEAD_SHA"] = head
            if src is None:
                env.pop("SRC", None)
            else:
                env["SRC"] = src
            if drc is None:
                env.pop("DRC", None)
            else:
                env["DRC"] = drc
            proc = _run_bash(script, env, Path(td))
            return proc.returncode, proc.stdout + proc.stderr

    def test_a_clean_pair_is_screened_and_clean(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="0", drc="0")
        c_rc, c_out = self._assert(self.clean, src="0", drc="0")
        self.assertEqual(v_rc, 0, v_out)
        self.assertIn("this window IS screened", v_out)
        self.assertNotIn("NOT screened", v_out)
        self.assertEqual(c_rc, 0, c_out)
        self.assertIn(f"screens clean at {HEAD}", c_out)
        self.assertNotIn("compositional-loss", c_out)

    def test_a_symbol_finding_is_screened_and_still_fails_clean(self) -> None:
        """Exit 1 is a verdict. Treating it as an invocation error freezes the catch-up base."""
        v_rc, v_out = self._assert(self.verdict, src="1", drc="0")
        c_rc, c_out = self._assert(self.clean, src="1", drc="0")
        self.assertEqual(v_rc, 0, v_out)
        self.assertIn("this window IS screened", v_out)
        self.assertIn("symbol=1", v_out)
        self.assertEqual(c_rc, 1, c_out)
        self.assertIn(f"compositional-loss finding(s) at {HEAD}", c_out)

    def test_a_docs_finding_is_screened_and_still_fails_clean(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="0", drc="1")
        c_rc, c_out = self._assert(self.clean, src="0", drc="1")
        self.assertEqual(v_rc, 0, v_out)
        self.assertIn("this window IS screened", v_out)
        self.assertEqual(c_rc, 1, c_out)
        self.assertIn("compositional-loss finding", c_out)

    def test_both_findings_stay_screened(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="1", drc="1")
        c_rc, _c_out = self._assert(self.clean, src="1", drc="1")
        self.assertEqual(v_rc, 0, v_out)
        self.assertEqual(c_rc, 1)

    def test_a_symbol_invocation_error_is_not_screened_and_fails_clean(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="2", drc="0")
        c_rc, c_out = self._assert(self.clean, src="2", drc="0")
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("window NOT screened", v_out)
        self.assertIn("symbol=2", v_out)
        self.assertEqual(c_rc, 1, c_out)
        self.assertIn("compositional-loss finding", c_out)

    def test_a_docs_invocation_error_is_not_screened(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="0", drc="2")
        c_rc, _c_out = self._assert(self.clean, src="0", drc="2")
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("window NOT screened", v_out)
        self.assertIn("docs=2", v_out)
        self.assertEqual(c_rc, 1)

    def test_a_higher_invocation_code_is_not_screened(self) -> None:
        """The threshold is >=2, not exactly 2. An exit 99 is still no verdict."""
        v_rc, v_out = self._assert(self.verdict, src="99", drc="0")
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("window NOT screened", v_out)

    def test_an_absent_code_is_not_coverage_and_fails_clean(self) -> None:
        """A skipped screens step leaves the outputs unset. That is not a green window."""
        v_rc, v_out = self._assert(self.verdict, src=None, drc=None)
        c_rc, c_out = self._assert(self.clean, src=None, drc=None)
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("symbol=99", v_out)
        self.assertIn("docs=99", v_out)
        self.assertIn("window NOT screened", v_out)
        self.assertEqual(c_rc, 1, c_out)
        self.assertIn("compositional-loss finding", c_out)

    def test_an_empty_code_is_not_coverage(self) -> None:
        """`${SRC:-99}` treats an empty output the same as an unset one."""
        v_rc, v_out = self._assert(self.verdict, src="", drc="")
        c_rc, _c_out = self._assert(self.clean, src="", drc="")
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("window NOT screened", v_out)
        self.assertEqual(c_rc, 1)

    def test_one_missing_side_blocks_coverage_even_when_the_other_is_clean(self) -> None:
        v_rc, v_out = self._assert(self.verdict, src="0", drc=None)
        c_rc, _c_out = self._assert(self.clean, src="0", drc=None)
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("docs=99", v_out)
        self.assertEqual(c_rc, 1)

    def test_one_missing_side_blocks_coverage_even_when_the_other_found(self) -> None:
        """A finding on one screen does not excuse a missing code on the other."""
        v_rc, v_out = self._assert(self.verdict, src="1", drc=None)
        c_rc, _c_out = self._assert(self.clean, src="1", drc=None)
        self.assertEqual(v_rc, 2, v_out)
        self.assertIn("window NOT screened", v_out)
        self.assertEqual(c_rc, 1)


class ScreenRecordRehearsalTest(unittest.TestCase):
    """Execute the screens step. It records exit codes and always exits 0."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _step_script(SCREENS_STEP)

    def _run(
        self,
        *,
        base: str,
        symbol_exit: int = 0,
        docs_exit: int = 0,
    ) -> tuple[int, str, dict[str, str], list[str]]:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            cmd_log = td_path / "screens.log"
            stub_bin = td_path / "bin"
            stub_bin.mkdir()
            gh_out = td_path / "github_output.txt"
            gh_out.write_text("", encoding="utf-8")

            for cmd_name, exit_code in (
                ("juniper-symbol-loss-check", int(symbol_exit)),
                ("juniper-docs-additions-check", int(docs_exit)),
            ):
                stub = stub_bin / cmd_name
                stub_lines = (
                    "#!/usr/bin/env bash",
                    "set -euo pipefail",
                    f'printf "{cmd_name} %s\\n" "$*" >>"{cmd_log}"',
                    'case " $* " in',
                    '  *" --json "*) printf "%s\\n" "{}"; exit 0 ;;',
                    "esac",
                    f"exit {exit_code}",
                )
                stub.write_text("\n".join(stub_lines) + "\n", encoding="utf-8")
                stub.chmod(0o755)

            git = stub_bin / "git"
            # `--verify -q <rev>` exits 0 only for the resolvable base. HEAD^1 prints the
            # fallback sha; HEAD prints the head sha. Anything else is unresolvable.
            git_lines = (
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'if [ "${1:-}" = "rev-parse" ] && [ "${2:-}" = "--verify" ]; then',
                '  target="${4:-}"',
                f'  if [ "$target" = "{RESOLVABLE}^{{commit}}" ]; then exit 0; fi',
                f'  if [ "$target" = "HEAD^1" ]; then printf "%s\\n" "{FALLBACK}"; exit 0; fi',
                f'  if [ "$target" = "HEAD" ]; then printf "%s\\n" "{HEAD}"; exit 0; fi',
                "  exit 1",
                "fi",
                'printf "unexpected git argv: %s\\n" "$*" >&2',
                "exit 99",
            )
            git.write_text("\n".join(git_lines) + "\n", encoding="utf-8")
            git.chmod(0o755)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["GITHUB_OUTPUT"] = str(gh_out)
            env["BASE_REF"] = base
            env["HEAD_SHA"] = HEAD

            proc = _run_bash(self.script, env, td_path)
            combined = proc.stdout + proc.stderr
            log_lines = cmd_log.read_text(encoding="utf-8").splitlines() if cmd_log.is_file() else []
            return proc.returncode, combined, _outputs(gh_out), log_lines

    @staticmethod
    def _human(log: list[str]) -> list[str]:
        return [line for line in log if "--json" not in line]

    def test_a_finding_is_recorded_and_the_step_exits_zero(self) -> None:
        """If this step exits 1, Actions skips the coverage step and the base freezes."""
        rc, out, outputs, log = self._run(base=RESOLVABLE, symbol_exit=1, docs_exit=0)
        self.assertEqual(rc, 0, out)
        self.assertEqual(outputs.get("src"), "1")
        self.assertEqual(outputs.get("drc"), "0")
        human = self._human(log)
        self.assertEqual(len(human), 2, log)
        self.assertIn("--scope tests/*.py", human[0])
        self.assertIn("--scope util/**/*.py", human[0])
        self.assertIn("--scope util/**/*.bash", human[0])
        self.assertTrue(human[0].endswith(f"--base {RESOLVABLE} --head {HEAD}"), human[0])
        self.assertNotIn("--scope", human[1])
        self.assertTrue(human[1].endswith(f"--base {RESOLVABLE} --head {HEAD}"), human[1])
        self.assertNotIn("empty/unresolvable", out)

    def test_an_invocation_error_is_recorded_and_the_step_exits_zero(self) -> None:
        rc, out, outputs, log = self._run(base=RESOLVABLE, symbol_exit=0, docs_exit=2)
        self.assertEqual(rc, 0, out)
        self.assertEqual(outputs.get("src"), "0")
        self.assertEqual(outputs.get("drc"), "2")
        self.assertEqual(len(self._human(log)), 2, log)

    def test_the_json_arm_does_not_replace_the_human_exit(self) -> None:
        """The `--json` run is `|| true` and exits 0. The recorded code is the human run."""
        rc, out, outputs, log = self._run(base=RESOLVABLE, symbol_exit=1, docs_exit=1)
        self.assertEqual(rc, 0, out)
        self.assertEqual(outputs, {"src": "1", "drc": "1"})
        json_arms = [line for line in log if "--json" in line]
        self.assertEqual(len(json_arms), 2, log)

    def test_an_empty_base_falls_back_and_still_screens(self) -> None:
        rc, out, outputs, log = self._run(base="", symbol_exit=0, docs_exit=0)
        self.assertEqual(rc, 0, out)
        self.assertEqual(outputs.get("src"), "0")
        self.assertEqual(outputs.get("drc"), "0")
        self.assertIn(f"fallback = {FALLBACK}", out)
        human = self._human(log)
        self.assertEqual(len(human), 2, log)
        self.assertIn(f"--base {FALLBACK} --head {HEAD}", human[0])
        self.assertNotIn(RESOLVABLE, human[0])

    def test_an_unresolvable_base_falls_back_and_still_screens(self) -> None:
        rc, out, outputs, log = self._run(base=UNRESOLVABLE, symbol_exit=1, docs_exit=0)
        self.assertEqual(rc, 0, out)
        self.assertEqual(outputs.get("src"), "1")
        self.assertIn(f"fallback = {FALLBACK}", out)
        human = self._human(log)
        self.assertTrue(human[0].endswith(f"--base {FALLBACK} --head {HEAD}"), human[0])
        self.assertNotIn(UNRESOLVABLE, human[0])


if __name__ == "__main__":
    unittest.main()
