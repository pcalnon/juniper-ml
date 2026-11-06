"""An exported empty prompt-file variable must not launch with the default prompt.

``--file ''`` and ``--path ''`` already exit 1 (``tests/test_claude_interactive.py``):
``-f "${HANDOFF}"`` with ``HANDOFF`` unset once sent the default prompt, which
``wake_the_claude.bash`` prefers to a prompt file. ``CLAUDE_PROMPT_FILE`` and
``CLAUDE_PROMPT_PATH`` are the same door. ``${var:-}`` collapses an exported
empty value the way it collapses an unset one, so ``CLAUDE_PROMPT_FILE=""``
used to launch with the default prompt too.

Unset stays unset. A value of one space is a value. A ``--file`` on the
command line still replaces an empty variable. No Claude binary.
"""

from __future__ import annotations

import tempfile
import unittest

import tests.test_claude_interactive as claudey_tests


class EmptyPromptFileEnvTests(unittest.TestCase):
    """``CLAUDE_PROMPT_FILE`` / ``CLAUDE_PROMPT_PATH`` set to the empty string."""

    def setUp(self) -> None:
        # The class stays on its own module: importing it here would make this file re-run that suite.
        self._host = claudey_tests.ClaudeInteractiveLauncherRuntimeTests()

    def _run(self, extra_args: list[str] | None = None, **env_values: str):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        launcher_path, args_log = self._host._install_fake_launcher_stack(temp.name, debug=False)
        env = self._host._base_env(args_log)
        env.update(env_values)
        result = self._host._run_launcher(launcher_path, temp.name, env, extra_args)
        return result, self._host._extract_logged_args(args_log)

    def test_an_exported_empty_name_is_refused(self) -> None:
        """Empty is missing. A real value on the other variable does not hide it."""
        cases = (
            {"CLAUDE_PROMPT_FILE": ""},
            {"CLAUDE_PROMPT_PATH": ""},
            {"CLAUDE_PROMPT_FILE": "", "CLAUDE_PROMPT_PATH": ""},
            {"CLAUDE_PROMPT_FILE": "", "CLAUDE_PROMPT_PATH": "prompts/prompt.md"},
            {"CLAUDE_PROMPT_PATH": "", "CLAUDE_PROMPT_FILE": "prompt.md"},
        )
        for env_values in cases:
            with self.subTest(env_values=env_values):
                result, args = self._run(**env_values)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                if env_values.get("CLAUDE_PROMPT_FILE") == "":
                    self.assertIn("Missing value for --file", result.stdout)
                else:
                    self.assertIn("Missing value for --path", result.stdout)
                self.assertEqual(args, [], "wake_the_claude.bash must not be invoked")

    def test_a_flag_replaces_an_empty_variable(self) -> None:
        """``--file prompt.md`` overwrites an exported empty ``CLAUDE_PROMPT_FILE`` and sends no default prompt."""
        result, args = self._run(["--file", "prompt.md"], CLAUDE_PROMPT_FILE="")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(args[args.index("--file") + 1], "prompt.md")
        self.assertEqual(args.count("--file"), 1)
        self.assertNotIn("--prompt", args)

    def test_one_space_is_a_value(self) -> None:
        """Only the empty string is missing. A space is forwarded, and the default prompt is not sent."""
        result, args = self._run(CLAUDE_PROMPT_FILE=" ")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(args[args.index("--file") + 1], " ")
        self.assertNotIn("--prompt", args)

    def test_both_set_are_forwarded_and_both_unset_keep_the_default(self) -> None:
        """The refusal must not drop a real pair, and must not fire when the variables were never exported."""
        result, args = self._run(CLAUDE_PROMPT_FILE="prompt.md", CLAUDE_PROMPT_PATH="prompts")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(args[args.index("--file") + 1], "prompt.md")
        self.assertEqual(args[args.index("--path") + 1], "prompts")
        self.assertNotIn("--prompt", args)

        default_prompt = claudey_tests.shipped_defaults("DEFAULT_PROMPT")["DEFAULT_PROMPT"]
        result, args = self._run()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(args[args.index("--prompt") + 1], default_prompt)
        self.assertNotIn("--file", args)
        self.assertNotIn("--path", args)


if __name__ == "__main__":
    unittest.main()
