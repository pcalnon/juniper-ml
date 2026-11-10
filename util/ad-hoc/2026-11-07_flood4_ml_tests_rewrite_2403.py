"""
Carry draft juniper-ml#2403's five wake_the_claude.bash tests, rewritten against current main.

#2403 (head 61cd7cd4) was written before juniper-ml#2438 put `--` in front of the prompt, so five of its
six tests expect `[..., "hello"]` where main sends `[..., "--", "hello"]` (10 failures with subtests on
the merged tree). Its insertion point also conflicts with a test main added since. This rebuilds the
file from origin/main's blob and inserts the block below directly after
`test_model_boolean_values_omit_or_default_the_model` -- the draft's own anchor -- so nothing main
gained is reverted.

What changed against the draft, and why:
- every expected argv carries the `--` main inserts before the prompt (#2438);
- the effort test keeps only its `--effort 1` (false) half. Its `--effort 0` half pinned `--effort auto`,
  which Claude Code 2.1.316-2.1.319 rejects ("Unknown --effort value 'auto'"); the script default
  (scripts/wake_the_claude.bash EFFORT_DEFAULT) is left to the owner (carrier validation, 2026-11-07);
- `test_missing_effort_value_fails_without_invoking_claude` is carried unchanged: it passes on main;
- the remote-control and permission alias tests keep their near-miss refusals (`--remote-controls`,
  `--dangerously-skip-permission`), which no main test pins; their alias loops now expect the `--`;
- docstrings claim only what the stub `claude` records (argv), never what Claude Code's own parser
  does with it: auto-memory reference_claude_cli_optional_flag_eats_the_prompt.md.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_rewrite_2403.py   (from the worktree root)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2403, #2438, #2468; HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md
"""

import subprocess
import sys
from pathlib import Path

TARGET = Path("tests/test_wake_the_claude.py")
ANCHOR = "    def test_prompt_file_that_never_resolves_says_why_with_debug_output_off(self) -> None:\n"
PREV = "    def test_model_boolean_values_omit_or_default_the_model(self) -> None:\n"

BLOCK = '''    def test_effort_false_omits_the_effort(self) -> None:
        """``--effort 1`` (false) omits effort from claude's argv instead of forwarding the ``1``.

        ``--effort 0`` (true) is deliberately not pinned: it sends the script default, ``EFFORT_DEFAULT`` (``auto`` today),
        and Claude Code 2.1.316-2.1.319 warns "Unknown --effort value 'auto'" and ignores it, so that default is an open
        question for the owner, not behaviour to lock in.
        """
        args = self._launch_and_get_args(["--resume", VALID_UUID, "--effort", "1", "--prompt", "hello"])
        self.assertEqual(args, ["--resume", VALID_UUID, "--", "hello"])

    def test_missing_effort_value_fails_without_invoking_claude(self) -> None:
        """A bare ``--effort``, or one whose next token is a flag, must not launch claude."""
        cases = (
            ["--resume", VALID_UUID, "--effort"],
            ["--resume", VALID_UUID, "--effort", "--prompt", "hello"],
        )
        for script_args in cases:
            with self.subTest(script_args=script_args):
                with tempfile.TemporaryDirectory() as temp_dir:
                    invocations_log, env = self._install_fake_claude(temp_dir)
                    result = self._run_script(script_args, cwd=temp_dir, env=env)
                    self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                    combined_output = result.stdout + result.stderr
                    self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
                    invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
                    self.assertEqual(invocations, [])

    def test_worktree_boolean_values_omit_or_let_claude_name(self) -> None:
        """``--worktree 1`` (false) drops the flag; ``--worktree 0`` (true) sends a bare ``--worktree``, and the prompt still follows ``--``."""
        args = self._launch_and_get_args(["--resume", VALID_UUID, "--worktree", "1", "--prompt", "hello"])
        self.assertEqual(args, ["--resume", VALID_UUID, "--", "hello"])

        args = self._launch_and_get_args(["--resume", VALID_UUID, "--worktree", "0", "--prompt", "hello"])
        self.assertEqual(args, ["--resume", VALID_UUID, "--worktree", "--", "hello"])

    def test_remote_control_aliases_forward_canonical_flag_without_consuming_the_next(self) -> None:
        """Every remote alias is sent as a bare ``--remote-control`` with the prompt after ``--``; a near-miss spelling does not launch."""
        for remote_flag in ("-c", "--remote", "--control", "--remote-control"):
            with self.subTest(remote_flag=remote_flag):
                args = self._launch_and_get_args(["--resume", VALID_UUID, remote_flag, "--prompt", "hello"])
                self.assertEqual(args, ["--resume", VALID_UUID, "--remote-control", "--", "hello"])

        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--remote-controls", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual((result.stdout + result.stderr).count("usage: wake_the_claude.bash"), 1)
            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_permission_aliases_forward_canonical_flag_without_consuming_the_next(self) -> None:
        """Skip-permission aliases are sent as ``--dangerously-skip-permissions`` with the prompt after ``--``; a near-miss does not launch."""
        for permissions_flag in ("-s", "--skip", "--skip-permissions", "--dangerously-skip-permissions"):
            with self.subTest(permissions_flag=permissions_flag):
                args = self._launch_and_get_args(["--resume", VALID_UUID, permissions_flag, "--prompt", "hello"])
                self.assertEqual(args, ["--resume", VALID_UUID, "--dangerously-skip-permissions", "--", "hello"])

        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--dangerously-skip-permission", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual((result.stdout + result.stderr).count("usage: wake_the_claude.bash"), 1)
            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

'''


def main() -> int:
    main_text = subprocess.run(["git", "show", "origin/main:" + TARGET.as_posix()], check=True, capture_output=True, text=True).stdout
    if main_text.count(ANCHOR) != 1 or main_text.count(PREV) != 1:
        print("anchor drifted: expected exactly one of each anchor in origin/main's file", file=sys.stderr)
        return 1
    if main_text.index(PREV) > main_text.index(ANCHOR):
        print("anchor order drifted", file=sys.stderr)
        return 1
    if "def test_effort_boolean_values_omit_or_default_the_effort" in main_text:
        print("main already carries the block", file=sys.stderr)
        return 1
    at = main_text.index(ANCHOR)
    TARGET.write_text(main_text[:at] + BLOCK + main_text[at:], encoding="utf-8")
    print(f"wrote {TARGET}: inserted {BLOCK.count(chr(10))} lines before {ANCHOR.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
