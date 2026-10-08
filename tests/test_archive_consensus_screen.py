#!/usr/bin/env python3
"""The consensus archiver's credential screen, which had no tests.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-09-22_archive_consensus_reports.py`` is what later archivers
call before a report is written into ``notes/``, which is committed to a public
repository. A validator that measured a secret file can quote the value. The
screen is the only check, and ``util/ad-hoc`` is outside every pre-commit Python
hook, so this suite is the gate.

Pins, each able to fail for the reason it exists:

* a free-standing 30- to 40-character token that contains ``*``, ``@``, ``$`` or
  ``%`` is a hit; 29 and 41 are not, and a mark-free hyphenated compound is not;
* a slash-prefixed path and a URL that happens to contain ``@`` are not hits
  (the screen's own "not a path or a URL" rule);
* ``enc-v1:`` needs eight payload characters, and a JWT needs the ``eyJ`` boundary,
  both dotted segments, and the trailing dot;
* the problem line names a count and never the matched text, so a refusal pasted
  into a PR cannot republish the value;
* ``final_report`` keeps the last assistant message (a draft is not the report)
  and ignores user turns, tool blocks, blank text and a broken JSON line;
* a hit refuses the whole archive (exit 2, nothing written) unless
  ``--allow-shaped``; ``--check`` writes nothing and does not bypass the screen.

Fixtures are built at runtime from repeated letters plus one mark. No credential
literal is stored in this file.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVER = REPO_ROOT / "util" / "ad-hoc" / "2026-09-22_archive_consensus_reports.py"


def _load():
    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {ARCHIVER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


archiver = _load()


def _token(mark: str, length: int) -> str:
    """``length`` characters of the screen's alphabet, ending in ``mark``."""
    return ("a" * (length - 1)) + mark


def _enc(payload: int) -> str:
    return "enc-" + "v1:" + ("A" * payload)


def _jwt(first: int = 10, second: int = 10, trailing_dot: bool = True) -> str:
    body = "ey" + "J" + ("a" * first) + "." + ("b" * second)
    return body + ("." if trailing_dot else "")


class ScreenTest(unittest.TestCase):
    """The three patterns, and the promise that a hit's text stays out of the message."""

    def _problems(self, body: str) -> list[str]:
        return archiver.screen("Lane B", body)

    def _assert_clean(self, body: str) -> None:
        self.assertEqual(self._problems(body), [])

    def _assert_one(self, body: str, label: str, secret: str) -> None:
        problems = self._problems(body)
        self.assertEqual(problems, [f"Lane B: 1 {label}(s) -- classify each before archiving"])
        self.assertNotIn(secret, problems[0])

    def test_each_mark_hits_at_both_ends_of_the_window(self) -> None:
        for mark in "*@$%":
            for length in (30, 40):
                token = _token(mark, length)
                with self.subTest(mark=mark, length=length):
                    self._assert_one(f"measured {token} today", "credential-shaped token", token)

    def test_one_shorter_or_one_longer_is_not_a_token(self) -> None:
        for length in (29, 41):
            token = _token("*", length)
            with self.subTest(length=length):
                self.assertEqual(len(token), length)
                self._assert_clean(f"measured {token} today")

    def test_a_mark_free_compound_is_not_a_token(self) -> None:
        compound = "well-known-" * 3  # 33 characters, inside the window, no * @ $ %
        self.assertEqual(len(compound), 33)
        self.assertGreaterEqual(len(compound), 30)
        self.assertLessEqual(len(compound), 40)
        self._assert_clean(f"the {compound} result")

    def test_a_path_and_a_url_are_not_tokens(self) -> None:
        token = _token("*", 32)
        self._assert_clean("/tmp/" + token)
        url = "https://user@example.com/abcdefghij"
        self.assertIn("@", url)
        self.assertGreaterEqual(len(url), 30)
        self.assertLessEqual(len(url), 40)
        self._assert_clean(url)

    def test_two_tokens_are_counted_and_neither_value_is_named(self) -> None:
        first, second = _token("*", 30), _token("@", 30)
        problems = self._problems(f"{first}\n{second}")
        self.assertEqual(problems, ["Lane B: 2 credential-shaped token(s) -- classify each before archiving"])
        self.assertNotIn(first, problems[0])
        self.assertNotIn(second, problems[0])

    def test_enc_v1_needs_eight_payload_characters(self) -> None:
        short, long = _enc(7), _enc(8)
        self._assert_clean(short)
        self._assert_one(long, "enc-v1 value", long)
        self._assert_clean("ENC-" + "v1:" + ("A" * 8))

    def test_a_jwt_needs_the_boundary_both_segments_and_the_trailing_dot(self) -> None:
        token = _jwt()
        self._assert_one(f"header {token} tail", "JWT", token)
        self._assert_clean(_jwt(first=9))
        self._assert_clean(_jwt(trailing_dot=False))
        self._assert_clean("h" + token)

    def test_a_token_and_a_jwt_are_both_reported(self) -> None:
        token, jwt = _token("%", 30), _jwt()
        problems = self._problems(f"{token} {jwt}")
        self.assertEqual(
            problems,
            [
                "Lane B: 1 credential-shaped token(s) -- classify each before archiving",
                "Lane B: 1 JWT(s) -- classify each before archiving",
            ],
        )
        for problem in problems:
            self.assertNotIn(token, problem)
            self.assertNotIn(jwt, problem)

    def test_ordinary_prose_is_clean(self) -> None:
        self._assert_clean("The well-known cross-validation result is negative, and the fold r2 is -0.115.")


class FinalReportTest(unittest.TestCase):
    """The archived text is the last assistant message, not an earlier draft."""

    def setUp(self) -> None:
        self._tasks = archiver.TASKS
        # A directory under the system temp, not the repo, so a crash cannot leave a transcript here.
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.addCleanup(setattr, archiver, "TASKS", self._tasks)
        archiver.TASKS = Path(self._dir.name)

    def _write(self, agent_id: str, rows: list[dict]) -> None:
        path = archiver.TASKS / f"agent-{agent_id}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_the_last_assistant_message_wins(self) -> None:
        self._write(
            "a1",
            [
                {"type": "assistant", "message": {"role": "assistant", "content": "DRAFT-ONE\n"}},
                {"type": "user", "message": {"role": "user", "content": "revise it"}},
                {"type": "assistant", "message": {"role": "assistant", "content": "  FINAL-TWO  \n"}},
            ],
        )
        # rstrip drops the trailing spaces; the leading indent of the report is kept.
        self.assertEqual(archiver.final_report("a1"), "  FINAL-TWO\n")

    def test_a_later_user_turn_does_not_replace_the_report(self) -> None:
        self._write(
            "a1",
            [
                {"type": "assistant", "message": {"role": "assistant", "content": "the report"}},
                {"type": "user", "message": {"role": "user", "content": "thanks"}},
            ],
        )
        self.assertEqual(archiver.final_report("a1"), "the report\n")

    def test_text_blocks_are_joined_and_tool_blocks_are_not_text(self) -> None:
        self._write(
            "a1",
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "read", "input": {"path": "secret"}},
                            {"type": "text", "text": "left "},
                            {"type": "text", "text": "right"},
                            "not-a-block",
                        ],
                    }
                }
            ],
        )
        self.assertEqual(archiver.final_report("a1"), "left right\n")

    def test_a_broken_json_line_is_skipped(self) -> None:
        path = archiver.TASKS / "agent-a1.jsonl"
        good = json.dumps({"type": "assistant", "message": {"content": "kept"}})
        path.write_text("{not json\n\n" + good + "\n", encoding="utf-8")
        self.assertEqual(archiver.final_report("a1"), "kept\n")

    def test_blank_assistant_text_is_not_a_report(self) -> None:
        self._write("a1", [{"type": "assistant", "message": {"content": "   \n"}}])
        with self.assertRaises(SystemExit) as caught:
            archiver.final_report("a1")
        self.assertIn("no assistant text", str(caught.exception))

    def test_a_missing_transcript_names_the_agent(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            archiver.final_report("missing-agent")
        message = str(caught.exception)
        self.assertIn("missing-agent", message)
        self.assertIn("no transcript", message)


class ArchiveRefusalTest(unittest.TestCase):
    """A hit refuses the whole archive. The value is not written and not printed."""

    def setUp(self) -> None:
        self._tasks = archiver.TASKS
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.addCleanup(setattr, archiver, "TASKS", self._tasks)
        root = Path(self._dir.name)
        archiver.TASKS = root / "tasks"
        archiver.TASKS.mkdir()
        self.out = root / "record.md"
        self.header = root / "header.md"
        self.header.write_text("# Record\n\nPreamble.\n", encoding="utf-8")

    def _agent(self, agent_id: str, text: str) -> None:
        path = archiver.TASKS / f"agent-{agent_id}.jsonl"
        row = {"type": "assistant", "message": {"role": "assistant", "content": text}}
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ["archive", "--out", str(self.out), "--header", str(self.header), *extra]
        with redirect_stdout(stdout), redirect_stderr(stderr), mock.patch.object(sys, "argv", argv):
            code = archiver.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_a_hit_refuses_the_whole_archive_and_prints_no_value(self) -> None:
        secret = _token("$", 34)
        self._agent("dirty", f"the probe printed {secret}")
        self._agent("clean", "a clean final report")
        code, stdout, stderr = self._run("--report", "Dirty=dirty", "--report", "Clean=clean")
        self.assertEqual(code, 2)
        self.assertFalse(self.out.exists())
        self.assertIn("Dirty: 1 credential-shaped token", stderr)
        self.assertIn("refusing to archive", stderr)
        self.assertNotIn(secret, stderr)
        self.assertNotIn(secret, stdout)
        self.assertIn("Clean:", stdout)

    def test_allow_shaped_writes_and_the_shaped_line_still_omits_the_value(self) -> None:
        secret = _token("%", 31)
        self._agent("dirty", secret)
        code, _stdout, stderr = self._run("--report", "Dirty=dirty", "--allow-shaped")
        self.assertEqual(code, 0)
        self.assertTrue(self.out.is_file())
        written = self.out.read_text(encoding="utf-8")
        self.assertIn("# Record", written)
        self.assertIn(secret, written, "allow-shaped archives the report verbatim")
        shaped = next(line for line in stderr.splitlines() if "SHAPED" in line)
        self.assertNotIn(secret, shaped)

    def test_check_writes_nothing_on_a_clean_report(self) -> None:
        self._agent("clean", "final report")
        code, stdout, stderr = self._run("--report", "Clean=clean", "--check")
        self.assertEqual(code, 0, stderr)
        self.assertFalse(self.out.exists())
        self.assertIn("nothing written", stdout)

    def test_check_does_not_bypass_a_hit(self) -> None:
        secret = _jwt()
        self._agent("dirty", secret)
        code, stdout, stderr = self._run("--report", "Dirty=dirty", "--check")
        self.assertEqual(code, 2)
        self.assertFalse(self.out.exists())
        self.assertNotIn(secret, stderr)
        self.assertNotIn(secret, stdout)
        self.assertNotIn("nothing written", stdout)

    def test_a_missing_transcript_writes_nothing(self) -> None:
        with self.assertRaises(SystemExit):
            self._run("--report", "Gone=no-such-agent")
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
