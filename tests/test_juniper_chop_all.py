"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser block in a subshell. Static-text assertions guard the grep
tightening change.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_chop_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 10


class TestSyntax(unittest.TestCase):
    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestPidParser(unittest.TestCase):
    """The parser block must accept both `=` and `:` delimiters."""

    PARSER_HARNESS = """
        set -euo pipefail
        raw="$1"
        if [[ "${raw}" == *=* ]]; then
            name="${raw%%=*}"
            pid="${raw#*=}"
        else
            name="${raw%%:*}"
            pid="$(echo "${raw#*:}" | tr -d ' ')"
        fi
        name="${name## }"
        name="${name%% }"
        echo "name=${name} pid=${pid}"
    """

    def _parse(self, line: str) -> str:
        result = subprocess.run(
            ["bash", "-c", self.PARSER_HARNESS, "_", line],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout.strip()

    def test_new_format_simple(self) -> None:
        self.assertEqual(self._parse("juniper-data=12345"), "name=juniper-data pid=12345")

    def test_new_format_with_dashes_in_name(self) -> None:
        self.assertEqual(
            self._parse("juniper-cascor-worker=98765"),
            "name=juniper-cascor-worker pid=98765",
        )

    def test_legacy_colon_format(self) -> None:
        self.assertEqual(
            self._parse("juniper-data:           12345"),
            "name=juniper-data pid=12345",
        )

    def test_legacy_colon_format_with_single_space(self) -> None:
        self.assertEqual(
            self._parse("juniper-cascor: 9999"),
            "name=juniper-cascor pid=9999",
        )


class TestParserBlockMatchesHarness(unittest.TestCase):
    """The parser block in the script must contain the dual-delimiter logic."""

    def test_equals_branch_present(self) -> None:
        self.assertIn('if [[ "${JUNIPER_PIDFILE_LINE_RAW}" == *=* ]]; then', SCRIPT_TEXT)

    def test_legacy_branch_present(self) -> None:
        # The else-branch with the colon-and-tr fallback.
        self.assertIn("${JUNIPER_PIDFILE_LINE_RAW#*:}", SCRIPT_TEXT)


class TestWorkerGrepTightening(unittest.TestCase):
    """Audit fix #11 — over-greedy `cascor.*worker` alternative removed."""

    def test_overgreedy_alternative_removed(self) -> None:
        # The old grep contained `cascor.*worker` as a third alternative
        # inside a quoted regex. That live alternation must not appear in the
        # active grep call. (The comment block above the grep call still
        # references the term to explain the rationale; that's intentional.)
        self.assertNotIn("cascor.*worker\\|", SCRIPT_TEXT)
        self.assertNotIn("\\|cascor.*worker", SCRIPT_TEXT)

    def test_strict_variants_present(self) -> None:
        # The dash and underscore variants must still be matched.
        self.assertIn("juniper-cascor-worker", SCRIPT_TEXT)
        self.assertIn("juniper_cascor_worker", SCRIPT_TEXT)


class TestSystemdModePreserved(unittest.TestCase):
    """Pass 2 must not touch the systemd codepath in chop."""

    def test_systemd_loop_intact(self) -> None:
        self.assertIn(
            "for svc in juniper-cascor-worker juniper-canopy juniper-cascor juniper-data",
            SCRIPT_TEXT,
        )


class TestIntentionalEchoDuplicatesPreserved(unittest.TestCase):
    """Per memory `feedback_chop_all_echo_debug`, duplicate echo lines around
    SIGTERM_TIMEOUT / KILL_WORKERS are intentional placeholders. The audit
    must NOT have removed them."""

    def test_sigterm_echo_appears_at_least_twice(self) -> None:
        count = SCRIPT_TEXT.count('SIGTERM_TIMEOUT=\\"${SIGTERM_TIMEOUT}\\"')
        self.assertGreaterEqual(count, 2, "intentional duplicate echo lines were removed")


if __name__ == "__main__":
    unittest.main()
