"""
Carry draft juniper-ml#2407's claudey tests, rewritten against current main (after #2438 and #2468).

#2407 (head 15b3937e) conflicts with main's tests/test_claude_interactive.py, fails mypy at its line 435
(`cases` needs an annotation: a tuple holding an empty dict literal), and pins two behaviours #2468
changed: `-v` / `--version` now report Claude Code's version (claudey's own is `--script-version`), and
remote control is ON by default (DEFAULT_REMOTE_CONTROL). This rebuilds the file from origin/main's
blob and re-applies the draft's content as edits:

- `_base_env` also drops an inherited CLAUDE_RESUME (the draft's one-line hunk), so an operator's
  environment cannot turn `--resume` on under the suite;
- the five tests go at the end of ClaudeInteractiveLauncherRuntimeTests (the draft appended to that
  class; main has since added a second class after it). Changes against the draft:
  * test_boolean_flags_do_not_consume_the_following_prompt and
    test_boolean_false_omits_the_option_instead_of_substituting_the_default set CLAUDE_REMOTE_CONTROL=1,
    so remote control is present only when a flag asks for it (main's default is on);
  * `cases` is annotated (the mypy error);
  * the version test now pins `--script-version` against an inherited SCRIPT_VERSION -- the part no
    main test covers; main's test_version_flags_report_claude_codes_version already pins `-v`;
  * the help test expects claudey's own usage line (`Usage: claude_interactive.bash`), not
    `Usage: wake_the_claude.bash`, which claudey never prints.
These are runtime tests: a fake wake_the_claude.bash records claudey's argv, so they claim nothing about
what Claude Code's own parser does (auto-memory reference_claude_cli_optional_flag_eats_the_prompt.md);
ClaudeInteractiveEndToEndTests on main covers that layer.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_rewrite_2407.py   (from the worktree root)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2407, #2438, #2468; HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md
"""

import subprocess
import sys
from pathlib import Path

TARGET = Path("tests/test_claude_interactive.py")
ENV_OLD = '            "CLAUDE_PROMPT_PATH",\n            "BASH_ENV",\n'
ENV_NEW = '            "CLAUDE_PROMPT_PATH",\n            "CLAUDE_RESUME",\n            "BASH_ENV",\n'
CLASS_END = "\n\nclass ClaudeInteractiveEndToEndTests(unittest.TestCase):\n"

BLOCK = '''
    def test_boolean_flags_do_not_consume_the_following_prompt(self) -> None:
        """Permission, resume, and remote-control flags shift once, so the prompt after them still arrives whole.

        With DEBUG off, ``--dangerously-skip-permissions`` is added only when one of these flags asks for it. Remote control is
        on by default, so ``CLAUDE_REMOTE_CONTROL=1`` turns it off here and only the flag turns it back on. A ``shift 2`` on any
        of them would swallow ``-p`` and either launch without that prompt or not launch at all.
        """
        prompt = 'two words "quoted" $(echo injected)'
        cases = (
            ("-sp", True, False, False),
            ("--skip-permissions", True, False, False),
            ("--dangerously-skip-permissions", True, False, False),
            ("-r", False, True, False),
            ("--resume", False, True, False),
            ("-rs", False, True, False),
            ("-rc", False, False, True),
            ("--remote-control", False, False, True),
            ("--remote-control-session", False, False, True),
        )
        for flag, expect_skip, expect_resume, expect_remote in cases:
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env["CLAUDE_REMOTE_CONTROL"] = SCRIPT_FALSE

                result = self._run_launcher(launcher_path, temp_dir, env, [flag, "-p", prompt])
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertEqual(args[args.index("--prompt") + 1], prompt)
                self.assertEqual(args[-1], prompt)
                self.assertLess(args.index("--effort"), args.index("--"))
                self.assertLess(args.index("--"), args.index("--prompt"))
                if expect_skip:
                    skip_at = args.index("--dangerously-skip-permissions")
                    self.assertLess(args.index("--"), skip_at)
                    self.assertNotEqual(args[skip_at + 1], prompt)
                else:
                    self.assertNotIn("--dangerously-skip-permissions", args)
                if expect_resume:
                    self.assertEqual(args[args.index("--resume") + 1], SCRIPT_TRUE)
                else:
                    self.assertNotIn("--resume", args)
                if expect_remote:
                    remote_at = args.index("--remote-control")
                    self.assertLess(args.index("--"), remote_at)
                    self.assertNotEqual(args[remote_at + 1], prompt)
                else:
                    self.assertNotIn("--remote-control", args)

    def test_boolean_false_omits_the_option_instead_of_substituting_the_default(self) -> None:
        """``1`` is FALSE here: the option is omitted, and the shipped default is not put in its place.

        ``CLAUDE_RESUME=0`` still forwards ``--resume 0``. No valued option was added, so the ``--`` separator,
        which claudey appends only after a valued option, is absent. Remote control, on by default, is held off.
        """
        flag_args = ["--model", SCRIPT_FALSE, "--effort", SCRIPT_FALSE, "--id", SCRIPT_FALSE, "--worktree", SCRIPT_FALSE, "-p", SCRIPT_FALSE]
        env_false = {
            "CLAUDE_MODEL": SCRIPT_FALSE,
            "CLAUDE_EFFORT": SCRIPT_FALSE,
            "CLAUDE_ID": SCRIPT_FALSE,
            "CLAUDE_WORKTREE": SCRIPT_FALSE,
            "CLAUDE_PROMPT": SCRIPT_FALSE,
        }
        cases: tuple[tuple[str, list[str], dict[str, str]], ...] = (
            ("flags", flag_args, {}),
            ("environment", [], env_false),
            ("resume-env", [], {**env_false, "CLAUDE_RESUME": SCRIPT_TRUE}),
        )
        defaults = shipped_defaults("DEFAULT_MODEL", "DEFAULT_EFFORT", "DEFAULT_PROMPT")
        for name, extra_args, env_extra in cases:
            with self.subTest(source=name), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env["CLAUDE_REMOTE_CONTROL"] = SCRIPT_FALSE
                env.update(env_extra)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn("__CALL__", args_log.read_text(encoding="utf-8"))

                args = self._extract_logged_args(args_log)
                for value in defaults.values():
                    self.assertNotIn(value, args)
                self.assertNotIn("--model", args)
                self.assertNotIn("--effort", args)
                self.assertNotIn("--id", args)
                self.assertNotIn("--worktree", args)
                self.assertNotIn("--prompt", args)
                self.assertNotIn("--", args)
                if name == "resume-env":
                    self.assertEqual(args, ["--resume", SCRIPT_TRUE])
                else:
                    self.assertEqual(args, [])

    def test_environment_values_are_one_argument_and_a_flag_overrides_only_that_setting(self) -> None:
        """Environment values reach wake_the_claude.bash unsplit; ``-m`` replaces the model and leaves the rest."""
        prompt = 'env "prompt" $(echo injected) *.txt'
        for extra_args, expected_model in (([], "haiku"), (["-m", "sonnet"], "sonnet")):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env["CLAUDE_MODEL"] = "haiku"
                env["CLAUDE_EFFORT"] = "low"
                env["CLAUDE_PROMPT"] = prompt

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertEqual(args[args.index("--model") + 1], expected_model)
                self.assertEqual(args[args.index("--effort") + 1], "low")
                self.assertEqual(args[args.index("--prompt") + 1], prompt)
                self.assertEqual(args[-1], prompt)
                self.assertLess(args.index("--effort"), args.index("--"))
                self.assertLess(args.index("--"), args.index("--prompt"))

    def test_script_version_ignores_an_inherited_script_version_and_does_not_launch(self) -> None:
        """``--script-version`` prints the version in claudey's header, not a ``SCRIPT_VERSION`` inherited from the environment.

        The assignment is unconditional, including when ``--script-version`` is not the first argument, and it must not start
        a session. (``-v`` / ``--version`` report Claude Code's version since 2026-11-06: test_version_flags_report_claude_codes_version.)
        """
        header = re.search(r"^# Version:\\s+(\\S+)\\s*$", LAUNCHER_SRC.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(header, msg="claude_interactive.bash's header must state its version")
        assert header is not None
        self.assertEqual(shipped_defaults("SCRIPT_VERSION")["SCRIPT_VERSION"], header.group(1))
        inherited_version = "9.9.9-inherited-from-the-environment"
        for extra_args in (["--script-version"], ["-m", "sonnet", "--script-version"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
                env = self._base_env(args_log)
                env["SCRIPT_VERSION"] = inherited_version

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(result.stdout, f"{header.group(1)}\\n")
                self.assertNotIn(inherited_version, result.stdout)
                self.assertFalse(args_log.exists(), "wake_the_claude.bash must not be invoked")

    def test_help_flags_print_usage_and_do_not_launch(self) -> None:
        """``--help`` exits 0 with claudey's usage text and does not start a session, including after another flag."""
        for extra_args in (["--help"], ["-h"], ["-?"], ["-m", "sonnet", "--help"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn(f"Usage: {launcher_path.name} ", result.stdout)
                self.assertNotIn("Unknown argument", result.stdout)
                self.assertFalse(args_log.exists(), "wake_the_claude.bash must not be invoked")
'''


def main() -> int:
    text = subprocess.run(["git", "show", "origin/main:" + TARGET.as_posix()], check=True, capture_output=True, text=True).stdout
    if text.count(ENV_OLD) != 1 or text.count(CLASS_END) != 1:
        print("anchor drifted in origin/main's file", file=sys.stderr)
        return 1
    if "def test_boolean_flags_do_not_consume_the_following_prompt" in text:
        print("main already carries the block", file=sys.stderr)
        return 1
    text = text.replace(ENV_OLD, ENV_NEW, 1)
    at = text.index(CLASS_END)
    # text[:at] ends in the last method's newline and BLOCK opens with a blank line: one blank line between methods, two before the class.
    TARGET.write_text(text[:at] + BLOCK.rstrip("\n") + "\n" + text[at:], encoding="utf-8")
    print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
