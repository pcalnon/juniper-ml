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

Owner rulings, 2026-11-03 (juniper-ml#2396):
  * session id, worktree and remote control are OPT-IN: the shipped
    ``DEFAULT_ID`` / ``DEFAULT_WORKTREE`` / ``DEFAULT_REMOTE_CONTROL`` are
    FALSE, and the flags (``-i`` / ``-w`` / ``-rc``) or the matching
    ``CLAUDE_*`` environment variables turn them on;
  * model and effort are FLAGS ONLY (``-m`` / ``-e``); a bare positional
    argument is rejected with the usage message.

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
        return subprocess.run(
            ["bash", str(launcher_path), *(extra_args or [])],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
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
            # Session id, worktree and remote control are opt-in (owner ruling, 2026-11-03): pinned
            # explicitly, so a silent flip back to always-on is a red build rather than a surprise.
            self.assertNotIn("--remote-control", args)
            self.assertNotIn("--id", args)
            self.assertNotIn("--worktree", args)
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
            self.assertNotIn("--remote-control", args)

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
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_REMOTE_CONTROL"] = SCRIPT_FALSE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertNotIn("--remote-control", args)

    def test_remote_control_opt_in_adds_flag(self) -> None:
        """Remote control is off by default; the flag or ``CLAUDE_REMOTE_CONTROL=0`` turns it on."""
        for extra_args, env_value in ((["--remote-control"], None), (["-rc"], None), ([], SCRIPT_TRUE)):
            with self.subTest(extra_args=extra_args, env_value=env_value), tempfile.TemporaryDirectory() as temp_dir:
                launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
                env = self._base_env(args_log)
                if env_value is not None:
                    env["CLAUDE_REMOTE_CONTROL"] = env_value

                result = self._run_launcher(launcher_path, temp_dir, env, extra_args)
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                args = self._extract_logged_args(args_log)
                self.assertIn("--remote-control", args)

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


if __name__ == "__main__":
    unittest.main()
