"""Regression tests for scripts/claude_interactive.bash (the `claudey` entry).

Pins the permission / remote-control / model-effort compose that
``default_interactive_session_claude_code.bash`` already covers for the older
launcher. ``claude_interactive.bash`` is the repo-root ``claudey`` symlink
target and ships with ``DEBUG=TRUE``, which *forces*
``--dangerously-skip-permissions`` even though the comment below that block
says the flag is opt-in only. That DEBUG→skip coupling is the blast-radius
regression this suite locks.

Convention note (script-local, inverted vs the default launcher):
  TRUE="0", FALSE="1"  — so ``CLAUDE_SKIP_PERMISSIONS=0`` means *enabled*.

Owner rulings, 2026-11-03 (juniper-ml#2396) and 2026-11-04:
  * the session id is OPT-IN: the shipped ``DEFAULT_ID`` is FALSE, and ``-i``
    or ``CLAUDE_ID`` turns it on;
  * worktree and remote control are ON by default (2026-11-04, replacing the
    2026-11-03 opt-in): ``DEFAULT_WORKTREE`` / ``DEFAULT_REMOTE_CONTROL`` are
    TRUE. The worktree goes bare, so Claude Code names it, unless ``-w`` names
    one; remote control never takes a value. ``--no-worktree`` /
    ``--no-remote-control``, or the matching ``CLAUDE_*`` set to FALSE, turn
    them off;
  * model and effort are FLAGS ONLY (``-m`` / ``-e``); a bare positional
    argument is rejected with the usage message.

Owner rulings, 2026-11-06:
  * ``-v``, ``-V``, ``--version`` and ``--claude-version`` report Claude
    Code's version, as ``claude -v`` does, through wake_the_claude.bash;
    claudey's own version is ``--script-version``;
  * ``--file`` / ``--path`` forward a prompt file to wake_the_claude.bash,
    and the default prompt is then not sent: wake_the_claude.bash prefers
    ``--prompt`` to a prompt file, so the default would discard the file.

Hermetic: copies the launcher into a temp ``scripts/`` dir beside a fake
``wake_the_claude.bash`` that only logs argv (same stack as
``DefaultInteractiveLauncherRuntimeTests`` in ``test_wake_the_claude.py``).
No network, no real Claude binary.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SRC = REPO_ROOT / "scripts" / "claude_interactive.bash"
CLAUDEY_LINK = REPO_ROOT / "claudey"

# Script-local boolean literals (TRUE="0", FALSE="1").
SCRIPT_TRUE = "0"
SCRIPT_FALSE = "1"

# Only `export NAME="..."` constant definitions -- never a line that runs anything.
_CONSTANT_DEF = re.compile(r"^export\s+[A-Z][A-Z0-9_]*=")

# The shipped default must still be a model the launcher actually knows about, so a
# typo'd or empty constant fails loudly instead of the assertions going tautological.
KNOWN_MODEL_ALIASES = frozenset({"fable", "opus", "sonnet", "haiku"})
KNOWN_EFFORT_LEVELS = frozenset({"auto", "max", "xhigh", "high", "medium", "low"})


def shipped_defaults(*names: str) -> dict[str, str]:
    """Resolve `DEFAULT_*` constants from claude_interactive.bash, as bash resolves them.

    The launcher switches its shipped defaults by commenting one assignment out and
    activating another::

        # export DEFAULT_MODEL="${MODEL_FABLE_ALIAS}"
        export DEFAULT_MODEL="${MODEL_OPUS_ALIAS}"

    Which model is active changes for account-usage and billing reasons, and the effort
    and prompt defaults use the same idiom. Re-declaring the expected value in this
    module would turn every such switch into a red build, so the script stays the single
    definitive source and these tests follow it.

    Evaluating the launcher itself would START A CLAUDE SESSION, so only the
    `export NAME="..."` constant lines are extracted and evaluated. That hands the
    commented-out variants and the `${MODEL_*_ALIAS}` indirection to bash itself rather
    than re-implementing shell semantics with a regex.
    """
    definitions = [line for line in LAUNCHER_SRC.read_text(encoding="utf-8").splitlines() if _CONSTANT_DEF.match(line)]
    probe = "\n".join(definitions) + "\n" + "\n".join(f'printf "%s\\n" "${{{name}?unset}}"' for name in names)
    result = subprocess.run(["/bin/bash", "-c", probe], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"could not resolve {names} from {LAUNCHER_SRC.name}: {result.stderr.strip()}")
    values = result.stdout.splitlines()
    return dict(zip(names, values, strict=True))


class ClaudeInteractiveLauncherRuntimeTests(unittest.TestCase):
    """Runtime tests for claude_interactive.bash argument compose."""

    def _install_fake_launcher_stack(
        self,
        temp_dir: str,
        *,
        debug: bool = True,
    ) -> tuple[Path, Path]:
        scripts_dir = Path(temp_dir) / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        text = LAUNCHER_SRC.read_text(encoding="utf-8")
        if not debug:
            # Flip only the shipped DEBUG default; leave the rest of the
            # script (including the TRUE/FALSE literals) untouched.
            old = 'DEBUG="${TRUE}"'
            new = 'DEBUG="${FALSE}"'
            self.assertIn(old, text, "DEBUG default marker drifted")
            text = text.replace(old, new, 1)
        launcher_path = scripts_dir / "claude_interactive.bash"
        launcher_path.write_text(text, encoding="utf-8")
        launcher_path.chmod(0o755)

        args_log = Path(temp_dir) / "claude_interactive_args.log"
        fake_wake = scripts_dir / "wake_the_claude.bash"
        fake_wake.write_text(
            "#!/usr/bin/env bash\n" "{\n" '  echo "__CALL__"\n' '  for arg in "$@"; do\n' "    printf 'ARG=%s\\n' \"$arg\"\n" "  done\n" '} >> "$WTC_WRAPPER_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_wake.chmod(0o755)
        return launcher_path, args_log

    @staticmethod
    def _extract_logged_args(args_log: Path) -> list[str]:
        if not args_log.exists():
            return []
        args: list[str] = []
        for line in args_log.read_text(encoding="utf-8").splitlines():
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    def _base_env(self, args_log: Path) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        for var in (
            "CLAUDE_SKIP_PERMISSIONS",
            "CLAUDE_REMOTE_CONTROL",
            "CLAUDE_MODEL",
            "CLAUDE_EFFORT",
            "CLAUDE_ID",
            "CLAUDE_WORKTREE",
            "CLAUDE_PROMPT",
            "CLAUDE_PROMPT_FILE",
            "CLAUDE_PROMPT_PATH",
            "BASH_ENV",
            "ENV",
        ):
            env.pop(var, None)
        env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)
        return env

    def _run_launcher(
        self,
        launcher_path: Path,
        temp_dir: str,
        env: RedactedEnv,
        extra_args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        # Bounded: a flag whose value is missing once left the parse loop spinning forever.
        return subprocess.run(
            ["bash", str(launcher_path), *(extra_args or [])],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )

    def test_script_and_claudey_symlink_exist(self) -> None:
        self.assertTrue(LAUNCHER_SRC.is_file(), f"missing: {LAUNCHER_SRC}")
        self.assertTrue(CLAUDEY_LINK.is_symlink(), f"claudey is not a symlink: {CLAUDEY_LINK}")
        self.assertEqual(
            CLAUDEY_LINK.readlink().as_posix(),
            "scripts/claude_interactive.bash",
            "claudey symlink target drifted",
        )

    def test_shipped_debug_true_forces_skip_permissions(self) -> None:
        """DEBUG=TRUE (shipped) forces --dangerously-skip-permissions.

        The comment above the opt-in block claims the flag is only added
        when explicitly requested; the DEBUG block above it overrides that
        for every interactive launch. Pin the force so a silent DEBUG flip
        or a comment-only "fix" cannot regress unnoticed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
            self.assertIn("--dangerously-skip-permissions", args)
            # Defaults that ride alongside the permission force. Read from the script
            # (see shipped_defaults) so switching the active model / effort / prompt is
            # never a red build -- what is pinned is that the launcher PASSES ON its own
            # shipped defaults, not which values they currently hold.
            defaults = shipped_defaults("DEFAULT_MODEL", "DEFAULT_EFFORT", "DEFAULT_PROMPT")
            self.assertEqual(args[args.index("--model") + 1], defaults["DEFAULT_MODEL"])
            self.assertEqual(args[args.index("--effort") + 1], defaults["DEFAULT_EFFORT"])
            # The session id is opt-in (owner ruling, 2026-11-03); worktree and remote control are on by default
            # (2026-11-04): a worktree of TRUE, so Claude Code names it, and a remote control with no value. Pinned
            # explicitly, so a silent flip of any of the three is a red build rather than a surprise.
            self.assertNotIn("--id", args)
            self.assertEqual(args[args.index("--worktree") + 1], SCRIPT_TRUE)
            self.assertEqual(args.count("--remote-control"), 1)
            self.assertTrue(args[args.index("--remote-control") + 1].startswith("-"), "--remote-control must not be given a value")
            # The prompt reaches wake_the_claude.bash as ONE argument, without literal quote characters.
            self.assertEqual(args[args.index("--prompt") + 1], defaults["DEFAULT_PROMPT"])

    def test_shipped_defaults_are_values_the_launcher_supports(self) -> None:
        """Guard against the switch itself being broken.

        ``test_shipped_debug_true_forces_skip_permissions`` compares the launcher's
        argv against the launcher's own constants, so it stays green through a model
        switch -- but it would also stay green if a constant were emptied or misspelled.
        This pins the values to what the launcher actually accepts, keeping the pair
        meaningful without re-declaring which model is currently selected.
        """
        defaults = shipped_defaults("DEFAULT_MODEL", "DEFAULT_EFFORT", "DEFAULT_PROMPT")
        self.assertIn(defaults["DEFAULT_MODEL"], KNOWN_MODEL_ALIASES)
        self.assertIn(defaults["DEFAULT_EFFORT"], KNOWN_EFFORT_LEVELS)
        self.assertTrue(defaults["DEFAULT_PROMPT"].strip(), "DEFAULT_PROMPT must not be empty")

    def test_debug_false_omits_skip_permissions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
            self.assertNotIn("--dangerously-skip-permissions", args)
            self.assertIn("--remote-control", args)  # on by default (owner ruling, 2026-11-04), DEBUG or not

    def test_debug_false_includes_skip_permissions_when_opted_in(self) -> None:
        """Explicit opt-in uses the script's TRUE=\"0\" convention."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_TRUE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertIn("--dangerously-skip-permissions", args)

    def test_skip_permissions_one_is_false_under_script_convention(self) -> None:
        """``CLAUDE_SKIP_PERMISSIONS=1`` means FALSE here (unlike the default launcher).

        The older ``default_interactive_session_claude_code.bash`` treats ``1``
        as opt-in. Crossing the conventions silently re-enables (or disables)
        skip-permissions; pin that ``1`` does *not* enable the flag when DEBUG
        is off.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_FALSE  # "1"

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_debug_true_overrides_explicit_skip_permissions_false(self) -> None:
        """Even an explicit FALSE cannot disarm the shipped DEBUG force."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_FALSE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertIn("--dangerously-skip-permissions", args)

    def test_remote_control_false_omits_flag(self) -> None:
        """Remote control is on by default; ``--no-remote-control`` or ``CLAUDE_REMOTE_CONTROL=1`` turns it off."""
        for extra_args, env_value in ((["--no-remote-control"], None), ([], SCRIPT_FALSE)):
            with self.subTest(extra_args=extra_args, env_value=env_value), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                if env_value is not None:
                    env["CLAUDE_REMOTE_CONTROL"] = env_value

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
                self.assertNotIn("--remote-control", args)

    def test_remote_control_opt_in_adds_flag(self) -> None:
        """The flag or ``CLAUDE_REMOTE_CONTROL=0`` asks for remote control (also the default), and it never takes a value."""
        for extra_args, env_value in ((["--remote-control"], None), (["-rc"], None), ([], SCRIPT_TRUE)):
            with self.subTest(extra_args=extra_args, env_value=env_value), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                if env_value is not None:
                    env["CLAUDE_REMOTE_CONTROL"] = env_value

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertEqual(args.count("--remote-control"), 1)
                self.assertTrue(args[args.index("--remote-control") + 1].startswith("-"), "--remote-control must not be given a value")

    def test_session_id_and_worktree_opt_in_flags(self) -> None:
        """``-i`` / ``-w`` forward their values to wake_the_claude.bash's ``--id`` / ``--worktree``."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env, ["-i", SCRIPT_TRUE, "-w", "feature-tree"])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertEqual(args[args.index("--id") + 1], SCRIPT_TRUE)
            self.assertEqual(args[args.index("--worktree") + 1], "feature-tree")

    def test_model_and_effort_flags(self) -> None:
        """``-m`` / ``-e`` (and their long forms) become ``--model`` / ``--effort``."""
        for extra_args in (["-m", "sonnet", "-e", "high"], ["--model", "sonnet", "--effort-level", "high"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertEqual(args[args.index("--model") + 1], "sonnet")
                self.assertEqual(args[args.index("--effort") + 1], "high")
                # Every flag value was consumed: nothing trails the prompt as a stray argument.
                self.assertEqual(args[-2], "--prompt")

    def test_positional_arguments_are_rejected(self) -> None:
        """Model and effort are flags only (owner ruling, 2026-11-03): a bare word fails with usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env, ["sonnet", "high"])
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Unknown argument: sonnet", result.stdout)
            self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

    def test_prompt_is_forwarded_as_one_argument(self) -> None:
        """A multi-word prompt with shell metacharacters reaches wake_the_claude.bash intact.

        The launcher once built a string and ``eval``-ed it: the default prompt arrived as
        ``"Hello`` / ``World,`` / ``Claude!"`` -- three arguments with literal quotes -- and a
        ``$(...)`` in a prompt would have run.
        """
        prompt = 'two words "quoted" $(echo injected) *.txt'
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env, ["-p", prompt])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertEqual(args[args.index("--prompt") + 1], prompt)
            self.assertEqual(args[-1], prompt)

    def test_resume_flag_forwards_explicit_true(self) -> None:
        """``-r`` forwards ``--resume 0``: wake_the_claude.bash rejects a ``--resume`` with nothing after it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env, ["-r"])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertEqual(args[args.index("--resume") + 1], SCRIPT_TRUE)

    def test_worktree_and_remote_control_turn_off_with_their_no_flags(self) -> None:
        """``--no-worktree`` / ``--no-remote-control``, ``-w 1``, or the ``CLAUDE_*`` variables at FALSE turn the defaults off."""
        cases: tuple[tuple[list[str], dict[str, str]], ...] = (
            (["--no-worktree", "--no-remote-control"], {}),
            (["-w", SCRIPT_FALSE, "--no-remote-control"], {}),
            ([], {"CLAUDE_WORKTREE": SCRIPT_FALSE, "CLAUDE_REMOTE_CONTROL": SCRIPT_FALSE}),
        )
        for extra_args, env_values in cases:
            with self.subTest(extra_args=extra_args, env_values=env_values), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env.update(env_values)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
                self.assertNotIn("--worktree", args)
                self.assertNotIn("--remote-control", args)

    def test_worktree_name_is_optional_and_never_the_next_flag(self) -> None:
        """``-w`` with no name -- the input ends, or a flag such as ``--prompt`` is next -- lets Claude Code name the worktree.

        The parser once took the next word whatever it was: ``-w --prompt hi`` named the worktree ``--prompt`` and then failed
        on ``hi``, and a trailing ``-w`` spun forever on a ``shift 2`` that could not shift.
        """
        cases = (
            (["-w"], SCRIPT_TRUE, None),
            (["--worktree", "--prompt", "hi"], SCRIPT_TRUE, "hi"),
            (["--worktree", "feature-tree", "--prompt", "hi"], "feature-tree", "hi"),
            (["--worktree-name", SCRIPT_TRUE], SCRIPT_TRUE, None),
        )
        for extra_args, worktree_value, prompt in cases:
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertEqual(args.count("--worktree"), 1)
                self.assertEqual(args[args.index("--worktree") + 1], worktree_value)
                if prompt is not None:
                    self.assertEqual(args[args.index("--prompt") + 1], prompt)

    def test_a_flag_missing_its_value_fails_instead_of_hanging(self) -> None:
        """``-m`` / ``--effort`` / ``--id`` / ``--prompt`` / ``--file`` / ``--path`` with nothing after them exit 1 with usage.

        Each ran ``shift 2`` on one remaining argument, which fails without shifting, so the parse loop never ended.
        """
        for flag in ("-m", "--effort", "--id", "--prompt", "--file", "--path"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, [flag])
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(f"Missing value for {flag}", result.stdout)
                self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

    def test_script_version_flag_reports_claudeys_own_version(self) -> None:
        """``--script-version`` prints claudey's version, the one its header states, without starting wake_the_claude.bash."""
        version = shipped_defaults("SCRIPT_VERSION")["SCRIPT_VERSION"]
        header = re.search(r"^# Version:\s+(\S+)$", LAUNCHER_SRC.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(header, msg="claude_interactive.bash's header must state its version")
        assert header is not None
        self.assertEqual(header.group(1), version)
        for extra_args in (["--script-version"], ["--no-worktree", "--script-version"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertEqual(result.stdout.strip(), version)
                self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

    def test_a_prompt_file_replaces_the_default_prompt(self) -> None:
        """``--file`` / ``--path`` reach wake_the_claude.bash, and the default prompt, which it would prefer to the file, is not sent."""
        cases: tuple[tuple[list[str], dict[str, str], list[tuple[str, str]]], ...] = (
            (["--file", "prompt.md"], {}, [("--file", "prompt.md")]),
            (["-f", "prompt.md"], {}, [("--file", "prompt.md")]),
            (["--path", "prompts/prompt.md"], {}, [("--path", "prompts/prompt.md")]),
            (["-l", "prompts", "--file-name", "prompt.md"], {}, [("--file", "prompt.md"), ("--path", "prompts")]),
            ([], {"CLAUDE_PROMPT_FILE": "prompt.md"}, [("--file", "prompt.md")]),
            ([], {"CLAUDE_PROMPT_PATH": "prompts/prompt.md"}, [("--path", "prompts/prompt.md")]),
            (["--file", "prompt.md"], {"CLAUDE_PROMPT": SCRIPT_FALSE}, [("--file", "prompt.md")]),
        )
        for extra_args, env_values, expected_pairs in cases:
            with self.subTest(extra_args=extra_args, env_values=env_values), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env.update(env_values)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertNotIn("--prompt", args)
                for flag, value in expected_pairs:
                    self.assertEqual(args.count(flag), 1)
                    self.assertEqual(args[args.index(flag) + 1], value)

    def test_a_prompt_and_a_prompt_file_are_refused_together(self) -> None:
        """An explicit prompt with ``--file`` / ``--path`` exits 1: wake_the_claude.bash would silently drop the file for the prompt."""
        cases: tuple[tuple[list[str], dict[str, str]], ...] = (
            (["--prompt", "hi", "--file", "prompt.md"], {}),
            (["--path", "prompt.md", "-p", "hi"], {}),
            (["--file", "prompt.md"], {"CLAUDE_PROMPT": "hi"}),
        )
        for extra_args, env_values in cases:
            with self.subTest(extra_args=extra_args, env_values=env_values), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                env.update(env_values)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("A prompt and a prompt file are exclusive", result.stdout)
                self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

    def test_a_prompt_file_flag_with_an_empty_value_is_refused(self) -> None:
        """``--file ''`` / ``--path ''`` exit 1: ``-f "${HANDOFF}"`` with the variable unset once launched with the default prompt."""
        for extra_args in (["--file", ""], ["--path", ""], ["-f", "", "--no-worktree"], ["-l", "", "-f", "prompt.md"]):
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(f"Missing value for {extra_args[0]}", result.stdout)
                self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

    def test_an_empty_word_is_parsed_not_the_end_of_the_input(self) -> None:
        """An empty word is refused, and ``-w ''`` is a bare ``-w``: the parse loop once stopped at an empty word.

        The words after it reached wake_the_claude.bash unparsed, after the default prompt, and it stops at an empty word as well,
        so ``-w '' --file f`` and ``'' --file f`` launched with the default prompt in place of the file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            result = self._run_launcher(launcher_path, temp_dir, env, ["", "--file", "prompt.md"])
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Unknown argument: (an empty word)", result.stdout)
            self.assertEqual(self._extract_logged_args(args_log), [], "wake_the_claude.bash must not be invoked")

        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            result = self._run_launcher(launcher_path, temp_dir, env, ["-w", "", "--file", "prompt.md"])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            args = self._extract_logged_args(args_log)
            self.assertEqual(args[args.index("--worktree") + 1], SCRIPT_TRUE)
            self.assertEqual(args[args.index("--file") + 1], "prompt.md")
            self.assertNotIn("--prompt", args)
            self.assertNotIn("", args)

    def test_claudey_exits_with_wake_the_claudes_status(self) -> None:
        """claudey's exit status is wake_the_claude.bash's: a launch it refused once ended in "Closed ..." and exit 0."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            fake_wake = launcher_path.parent / "wake_the_claude.bash"
            fake_wake.write_text(fake_wake.read_text(encoding="utf-8") + "exit 3\n", encoding="utf-8")
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env, [])
            self.assertEqual(result.returncode, 3, msg=result.stdout + result.stderr)
            self.assertTrue(self._extract_logged_args(args_log), "Expected wrapper to invoke wake_the_claude.bash")


class ClaudeInteractiveEndToEndTests(unittest.TestCase):
    """claudey, the REAL wake_the_claude.bash, and a stub claude that records the argv Claude Code itself is handed.

    The runtime tests above stop at wake_the_claude.bash's argv. Claude Code's own parser is where a bare flag with an
    optional value (``--worktree [name]``, ``--remote-control [name]``) would take the prompt as that value.
    """

    def _launch(self, temp_dir: str, extra_args: list[str], env_extra: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        scripts_dir = Path(temp_dir) / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for name in ("claude_interactive.bash", "wake_the_claude.bash"):
            target = scripts_dir / name
            target.write_text((REPO_ROOT / "scripts" / name).read_text(encoding="utf-8"), encoding="utf-8")
            target.chmod(0o755)
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(exist_ok=True)
        argv_log = Path(temp_dir) / "claude_argv.nul"
        argv_log.unlink(missing_ok=True)
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            '#!/usr/bin/env bash\nif [[ "$1" == "--version" ]]; then echo "claude-test-version"; exit 0; fi\nprintf \'%s\\0\' "$@" >> "$CLAUDE_ARGV_NUL_LOG"\n',
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)

        env = RedactedEnv(os.environ)
        for var in ("CLAUDE_SKIP_PERMISSIONS", "CLAUDE_REMOTE_CONTROL", "CLAUDE_MODEL", "CLAUDE_EFFORT", "CLAUDE_ID", "CLAUDE_WORKTREE", "CLAUDE_PROMPT", "CLAUDE_PROMPT_FILE", "CLAUDE_PROMPT_PATH", "WTC_DEBUG", "BASH_ENV", "ENV"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGV_NUL_LOG"] = str(argv_log)
        env["WTC_SESSIONS_DIR"] = str(Path(temp_dir) / "sessions")
        env["WTC_LOGS_DIR"] = str(Path(temp_dir) / "logs")
        env.update(env_extra or {})
        result = subprocess.run(
            ["bash", str(scripts_dir / "claude_interactive.bash"), *extra_args],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        argv = argv_log.read_bytes().decode("utf-8").split("\0")[:-1] if argv_log.exists() else []
        return result, argv

    def test_claude_gets_a_bare_worktree_and_remote_control_and_the_prompt_last(self) -> None:
        """Claude Code receives the worktree and remote control bare, and the prompt as its last argument, after ``--``."""
        defaults = shipped_defaults("DEFAULT_MODEL", "DEFAULT_EFFORT", "DEFAULT_PROMPT")
        cases: tuple[tuple[list[str], str, str | None], ...] = (
            ([], defaults["DEFAULT_PROMPT"], None),
            (["-w", "feature-tree", "-p", "two words, 'quoted'"], "two words, 'quoted'", "feature-tree"),
        )
        for extra_args, prompt, worktree_name in cases:
            with self.subTest(extra_args=extra_args), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertTrue(argv, "Expected claude to be invoked")

                self.assertEqual(argv[-2:], ["--", prompt])
                self.assertEqual(argv.count("--"), 1)
                self.assertFalse({"--prompt", "-p", "--prompt-string"} & set(argv[:-1]), "no prompt flag reaches claude")
                self.assertEqual(argv[argv.index("--model") + 1], defaults["DEFAULT_MODEL"])
                self.assertEqual(argv[argv.index("--effort") + 1], defaults["DEFAULT_EFFORT"])
                after_remote_control = argv[argv.index("--remote-control") + 1]
                self.assertTrue(after_remote_control.startswith("-"), f"--remote-control was given {after_remote_control!r}")
                after_worktree = argv[argv.index("--worktree") + 1]
                if worktree_name is None:
                    self.assertTrue(after_worktree.startswith("-"), f"--worktree was given {after_worktree!r}")
                else:
                    self.assertEqual(after_worktree, worktree_name)

    def test_a_prompt_that_reads_like_a_flag_does_not_undo_an_opt_out(self) -> None:
        """``--no-remote-control --prompt --remote-control`` keeps remote control off: the prompt is text (juniper-ml#2438 review)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result, argv = self._launch(temp_dir, ["--no-remote-control", "--prompt", "--remote-control"])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(argv[-2:], ["--", "--remote-control"])
            self.assertNotIn("--remote-control", argv[:-2])

    def test_version_flags_report_claude_codes_version(self) -> None:
        """``-v`` / ``-V`` / ``--version`` / ``--claude-version`` print Claude Code's version and start no session (2026-11-06).

        They printed claudey's own version until then, which ``--script-version`` now prints.
        """
        claudey_version = shipped_defaults("SCRIPT_VERSION")["SCRIPT_VERSION"]
        for flag in ("-v", "-V", "--version", "--claude-version"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temp_dir:
                result, argv = self._launch(temp_dir, [flag])
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn("claude-test-version", result.stdout)
                self.assertNotIn(claudey_version, result.stdout.split())
                self.assertNotIn("wake_the_claude.bash: ", result.stderr, "the version needs no debug log")
                self.assertEqual(argv, [], "no Claude Code session may start")

    def test_a_prompt_file_wake_the_claude_refuses_fails_claudey(self) -> None:
        """A missing or empty prompt file starts no session, claudey exits 1, as wake_the_claude.bash does, and stderr says why.

        With the debug log off (``WTC_DEBUG=1``), so the ``Error:`` line can only come from the errors themselves.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "empty.md").write_text("\n", encoding="utf-8")
            for extra_args in (["--file", "missing.md"], ["--file", "empty.md"], ["--path", "no-such-dir", "--file", "empty.md"]):
                with self.subTest(extra_args=extra_args):
                    result, argv = self._launch(temp_dir, extra_args, {"WTC_DEBUG": "1"})
                    self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                    self.assertNotIn("wake_the_claude.bash: ", result.stderr, "the debug log must be off")
                    self.assertIn("Error:", result.stderr)
                    self.assertEqual(argv, [], "no Claude Code session may start")

    def test_a_prompt_file_reaches_claude_as_the_prompt(self) -> None:
        """Claude Code receives the file's text as its prompt, after ``--``: claudey's default prompt does not displace it."""
        default_prompt = shipped_defaults("DEFAULT_PROMPT")["DEFAULT_PROMPT"]
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir()
            (prompt_dir / "handoff.md").write_text("---name: from the file\nsecond line\n", encoding="utf-8")
            for extra_args in (["--file", "prompts/handoff.md"], ["--path", "prompts/handoff.md"], ["--path", "prompts", "--file", "handoff.md"]):
                with self.subTest(extra_args=extra_args):
                    result, argv = self._launch(temp_dir, extra_args)
                    self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    self.assertEqual(argv[-2:], ["--", "---name: from the file\nsecond line"])
                    self.assertNotIn(default_prompt, argv)


if __name__ == "__main__":
    unittest.main()
