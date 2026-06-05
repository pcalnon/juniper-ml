"""
Regression tests for the ad-hoc worktree sweep scripts.

The scripts are intentionally one-shot, but they plan destructive
worktree/branch cleanup. These tests pin the survey -> apply contract in
dry-run mode so a stale-worktree sweep cannot accidentally act on DIRTY or
ACTIVE rows, or lose the parent repo key needed for branch deletion.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SURVEY_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "worktree_sweep_survey.bash"
APPLY_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "worktree_sweep_apply.bash"
SCRIPT_TIMEOUT_SECONDS = 15


def _run_apply(input_text: str, *, worktrees_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["JUNIPER_WORKTREE_SWEEP_ROOT"] = str(worktrees_root)
    return subprocess.run(
        ["bash", str(APPLY_SCRIPT), "--dry-run"],
        input=input_text,
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _write_fake_git(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            cwd=""
            if [[ "${1-}" == "-C" ]]; then
                cwd="$2"
                shift 2
            fi

            cmd="${1-}"
            shift || true

            case "$cmd" in
                fetch)
                    exit 0
                    ;;
                status)
                    if [[ "$cwd" == *dirty* ]]; then
                        echo " M file.txt"
                    fi
                    exit 0
                    ;;
                rev-parse)
                    case "${1-}" in
                        --abbrev-ref)
                            echo "feature/safe"
                            ;;
                        HEAD)
                            echo "1111111111111111111111111111111111111111"
                            ;;
                        origin/main)
                            echo "2222222222222222222222222222222222222222"
                            ;;
                        --short)
                            echo "1111111"
                            ;;
                    esac
                    exit 0
                    ;;
                rev-list)
                    if [[ "$cwd" == *active* ]]; then
                        echo "2"
                    else
                        echo "0"
                    fi
                    exit 0
                    ;;
            esac

            echo "unexpected git invocation: $cmd $*" >&2
            exit 1
            """
        )
    )
    path.chmod(0o755)


class TestWorktreeSweepApplyDryRun(unittest.TestCase):
    def test_apply_dry_run_only_removes_safe_rows_from_survey_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "worktrees"
            safe = "juniper-ml--safe--20260531-1200--11111111"
            dirty = "juniper-ml--dirty--20260531-1200--22222222"
            active = "juniper-ml--active--20260531-1200--33333333"
            broken = "juniper-ml--broken--20260531-1200--44444444"
            for name in (safe, dirty, active, broken):
                (root / name).mkdir(parents=True)

            survey_output = textwrap.dedent(
                f"""\
                STATUS      \tREPO              \tBEHIND \tBRANCH                                            \tWORKTREE
                ----------------------------------------------------------------------------------------------------------------------------------
                SAFE        \tjuniper-ml        \t0      \tfeature/safe                                      \t{safe}
                DIRTY       \tjuniper-ml        \t?      \tfeature/dirty                                     \t{dirty}
                ACTIVE      \tjuniper-ml        \t2      \tfeature/active                                    \t{active}
                BROKEN      \tjuniper-ml        \t?      \tfeature/broken                                    \t{broken}
                """
            )

            result = _run_apply(survey_output, worktrees_root=root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        dry_lines = [line for line in result.stdout.splitlines() if line.startswith("DRY:")]
        self.assertEqual(dry_lines, [f"DRY: git -C juniper-ml worktree remove {root / safe} && branch -D feature/safe"])
        self.assertIn("done", result.stdout)


class TestWorktreeSweepSurveyContract(unittest.TestCase):
    def test_survey_output_feeds_apply_without_losing_repo_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            worktrees_root = base / "worktrees"
            safe = "juniper-ml--safe--20260531-1200--11111111"
            active = "juniper-ml--active--20260531-1200--22222222"
            (worktrees_root / safe).mkdir(parents=True)
            (worktrees_root / active).mkdir(parents=True)

            fake_bin = base / "bin"
            fake_bin.mkdir()
            _write_fake_git(fake_bin / "git")

            env = os.environ.copy()
            env["JUNIPER_WORKTREE_SWEEP_ROOT"] = str(worktrees_root)
            env["JUNIPER_SWEEP_PROJECT_DIR"] = str(base / "Juniper")
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

            survey = subprocess.run(
                ["bash", str(SURVEY_SCRIPT)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertEqual(survey.returncode, 0, msg=survey.stderr)
            self.assertIn("REPO", survey.stdout)
            self.assertRegex(survey.stdout, rf"SAFE\s+\tjuniper-ml\s+\t0\s+\tfeature/safe\s+\t{safe}")
            self.assertRegex(survey.stdout, rf"ACTIVE\s+\tjuniper-ml\s+\t2\s+\tfeature/safe\s+\t{active}")

            apply_result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--dry-run"],
                input=survey.stdout,
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

        self.assertEqual(apply_result.returncode, 0, msg=apply_result.stderr)
        dry_lines = [line for line in apply_result.stdout.splitlines() if line.startswith("DRY:")]
        self.assertEqual(dry_lines, [f"DRY: git -C juniper-ml worktree remove {worktrees_root / safe} && branch -D feature/safe"])


if __name__ == "__main__":
    unittest.main()
