#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/soak_run_probe.py``. ``util/`` is outside every pre-commit Python
hook, so this suite is the only check on it.

Hermetic: nothing here launches ``claude`` or spends a probe. The event parser is
exercised against synthetic ``stream-json``.

What it pins
------------
1. **The task never reaches this script's own stdout.** ``soak_next_probe.py``
   protects the *dispatch* path; this wrapper is a second place the task passes
   through, and its stdout is read by the operator who will later SCORE the run.
   Echoing the task there re-introduces priming at the far end of the pipeline,
   after the dispatcher was careful about the near end.
2. **The retrieval channel is mechanical and honest about its limits.** A pointer
   miss is consistent with BOTH source-recovered and miss; the wrapper must not
   collapse that into a scored outcome, because correctness against the frozen
   discriminator is the judgement the protocol reserves for a scorer.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"
PROBES = REPO_ROOT / "conf" / "soak_probes.json"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def probes() -> list[dict]:
    return json.loads(PROBES.read_text(encoding="utf-8"))["probes"]


class DryRunDoesNotLeakTheTask(unittest.TestCase):
    def test_dry_run_stdout_contains_no_probe_task(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(r.returncode, 0)
        for p in probes():
            self.assertNotIn(p["task"].strip(), r.stdout)

    def test_dry_run_stdout_contains_no_fact_or_discriminator(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        for p in probes():
            for field in ("fact", "discriminator"):
                val = p.get(field)
                if isinstance(val, str) and val.strip():
                    self.assertNotIn(val.strip(), r.stdout)

    def test_dry_run_says_why_the_task_is_withheld(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertIn("priming", r.stdout.lower())


class RetrievalChannel(unittest.TestCase):
    def test_pointer_hit_is_detected_from_tool_inputs(self) -> None:
        parsed = {"tool_inputs": [json.dumps({"file_path": "docs/REFERENCE.md"})], "answer": ""}
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_pointer_absence_does_not_assert_a_miss(self) -> None:
        # The load-bearing honesty: no pointer hit is consistent with a CORRECT
        # source-recovered answer as well as with a wrong one.
        parsed = {"tool_inputs": [json.dumps({"file_path": "util/assert_release_tag.bash"})], "answer": ""}
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertFalse(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "source-recovered-or-miss")
        self.assertNotEqual(ch["suggests"], "miss")

    def test_channel_carries_its_own_caveat(self) -> None:
        ch = mod.retrieval_channel({"tool_inputs": [], "answer": ""}, "docs/REFERENCE.md#x")
        self.assertIn("MECHANICAL ONLY", ch["note"])
        self.assertIn("judgement", ch["note"].lower())

    def test_anchor_is_stripped_before_matching(self) -> None:
        ch = mod.retrieval_channel({"tool_inputs": [], "answer": ""}, "docs/REFERENCE.md#deep-anchor")
        self.assertEqual(ch["pointer_doc"], "docs/REFERENCE.md")

    def test_pointer_path_in_a_command_arg_currently_counts_as_a_hit(self) -> None:
        # P06 false-positive (PR #1616): the probe constructs a command containing
        # `--dest docs/REFERENCE.md`, so the pointer path appears in tool_inputs
        # whether or not the document was Read. The channel is over-inclusive;
        # pin that so a future narrowing is a deliberate test break, not a silent
        # flip of follow vs source-recovered.
        parsed = {
            "tool_inputs": [json.dumps({"command": "some-tool --dest docs/REFERENCE.md"})],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_a_sibling_repos_same_named_file_is_not_a_hit(self) -> None:
        # Measured on all three P24 runs (2026-09-08 re-audit): the session ran
        # `cd .../juniper-deploy && grep -rn 3001 .` and matched juniper-deploy's
        # OWN docs/REFERENCE.md. 7 of the 8 sibling repos ship one. The fact under
        # test is in juniper-ml's copy. Only THIS run has a sibling hit and
        # nothing else; the other two P24 runs also read juniper-ml's own file
        # and are follows, so the sibling test must decide per occurrence.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cd /home/pcalnon/Development/python/Juniper/juniper-deploy " "&& grep -rn 3001 docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#ecosystem-compatibility")
        self.assertFalse(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "source-recovered-or-miss")

    def test_naming_the_ledger_in_metadata_does_not_suppress_a_real_read(self) -> None:
        # REGRESSION PIN FOR A WITHDRAWN CHANGE, 2026-09-12. A guard was proposed
        # that suppressed the pointer hit whenever the soak ledger's path appeared
        # anywhere in the same tool input, on the theory that reading the ledger is
        # reaching a different document. Consensus refuted it and it was withdrawn.
        #
        # This pins the worst of the four measured reasons: the guard destroyed the
        # CANONICAL positive. `{"file_path": "docs/REFERENCE.md"}` is what
        # test_pointer_hit_is_detected_from_tool_inputs pins as THE unambiguous
        # open -- and EVERY Claude Code Bash/Read input also carries a
        # `description`, so prose in a metadata field flipped a genuine read to
        # MISS. That is the same false-negative class as the `cd`-ordering bug that
        # produced the wrong 51.2% mechanism-checked headline (true figure 55.8%).
        #
        # The other three reasons, for anyone tempted to re-add it: the selector was
        # one hard-coded path, so the identical shape aimed at README.md still
        # scored `follow`; Sec 3 of
        # notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md
        # defines the `ledger` class as "the match is INSIDE the soak ledger's own
        # JSON", so a match inside a shell COMMAND is Sec 3's `filename` class --
        # owner decision 7, not a defect; and the shape has 0 occurrences in 49
        # bound transcripts while all 7 real ledger sightings are RESULT-side, which
        # this channel cannot see (see WiredChannelSeesToolInputsOnly).
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "file_path": "docs/REFERENCE.md",
                        "description": "compare against "
                        "reports/soak/pointer_follow_soak.jsonl",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

        # Same class, shell shape: a ledger read and a genuine unqualified read in
        # one command. The read is real and must survive.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cat reports/soak/pointer_follow_soak.jsonl "
                        "&& sed -n 10,40p docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertTrue(ch["pointer_doc_referenced"])

    def test_an_absolute_sibling_path_is_not_a_hit(self) -> None:
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "file_path": "/home/pcalnon/Development/python/Juniper/juniper-canopy/docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertFalse(ch["pointer_doc_referenced"])

    def test_a_real_hit_still_counts_when_a_sibling_hit_comes_first(self) -> None:
        # Order must not decide it. Returning on the FIRST occurrence would let a
        # sibling-repo path seen early suppress a genuine read of this repo's copy
        # later in the same run -- trading a false positive for a false negative.
        parsed = {
            "tool_inputs": [
                json.dumps({"command": "grep -rn x /home/x/juniper-deploy/docs/REFERENCE.md"}),
                json.dumps({"file_path": "docs/REFERENCE.md"}),
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_a_read_from_the_ecosystem_parent_is_still_a_hit(self) -> None:
        # THE FALSE-NEGATIVE THIS CLASS EXISTS TO PREVENT. A subject that works
        # from the ecosystem parent and names our file explicitly has read it:
        #     cd /…/Juniper && sed -n '145,175p' juniper-ml/docs/REFERENCE.md
        # The parent directory matches no `juniper-ml` root segment, so testing
        # the cd target FIRST discarded the whole input and threw the read away.
        # Two of the three P24 runs are this shape, and the discarded reads are
        # what produced the original 51.2% mechanism-checked headline (the true
        # figure is 55.8%). An explicitly qualified path outranks the cwd.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cd /home/pcalnon/Development/python/Juniper " "&& sed -n '145,175p' juniper-ml/docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#ecosystem-compatibility")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_a_sibling_named_from_the_ecosystem_parent_is_still_not_a_hit(self) -> None:
        # The other direction of the same rule: an explicitly qualified SIBLING
        # path stays foreign even though the cwd is neutral.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cd /home/pcalnon/Development/python/Juniper " "&& grep -rn 3001 juniper-deploy/docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#ecosystem-compatibility")
        self.assertFalse(ch["pointer_doc_referenced"])

    def test_our_path_as_a_grep_PATTERN_is_not_a_hit(self) -> None:
        # Adversarial review found this: the first fix compared a fixed-width
        # TEXT window, not a path. A subject reading juniper-deploy's file while
        # SEARCHING FOR our path string scored as a read of ours.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cd /home/pcalnon/Development/python/Juniper/juniper-deploy " "&& grep -rn 'juniper-ml/docs' docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertFalse(ch["pointer_doc_referenced"])

    def test_a_repo_whose_name_merely_starts_with_juniper_ml_is_not_ours(self) -> None:
        # `/juniper-ml` without a terminator is a PREFIX: it matched
        # `juniper-mlx` and `juniper-ml-scratch`. Both segment forms now end at
        # a boundary.
        for other in ("juniper-mlx", "juniper-ml-scratch"):
            parsed = {
                "tool_inputs": [
                    json.dumps(
                        {
                            "command": "cd /home/pcalnon/Development/python/Juniper/juniper-deploy " f"&& sed -n 1p /home/pcalnon/Development/python/Juniper/{other}/docs/REFERENCE.md",
                        }
                    )
                ],
                "answer": "",
            }
            ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
            self.assertFalse(ch["pointer_doc_referenced"], other)

    def test_reading_both_copies_in_one_command_counts_as_a_hit(self) -> None:
        # Precedence must be by PROXIMITY to the match, not by which segment
        # list is tested first. Testing the sibling list first over a shared
        # window made this False.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "command": "cd /home/pcalnon/Development/python/Juniper && diff " "juniper-deploy/docs/REFERENCE.md juniper-ml/docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertTrue(ch["pointer_doc_referenced"])

    def test_this_repos_own_worktree_path_is_still_a_hit(self) -> None:
        # A worktree of juniper-ml is the SAME document. Only a sibling repo is
        # a different one.
        parsed = {
            "tool_inputs": [
                json.dumps(
                    {
                        "file_path": "/home/pcalnon/Development/python/Juniper/juniper-ml/" ".claude/worktrees/giggly-marinating-backus/docs/REFERENCE.md",
                    }
                )
            ],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertTrue(ch["pointer_doc_referenced"])


class EventParsing(unittest.TestCase):
    def _log(self, lines: list[dict]) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        return p

    def test_extracts_answer_and_tool_calls(self) -> None:
        log = self._log(
            [
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {"file_path": "util/x.bash"}},
                        ]
                    },
                },
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "the answer"}]}},
                {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("the answer", out["answer"])
        self.assertEqual(out["tool_calls"], ["Read"])
        self.assertFalse(out["result"]["is_error"])

    def test_malformed_lines_do_not_abort_the_parse(self) -> None:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text('not json\n{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n', encoding="utf-8")
        self.assertIn("ok", mod.parse_events(p)["answer"])

    def test_empty_log_yields_no_answer_rather_than_crashing(self) -> None:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text("", encoding="utf-8")
        out = mod.parse_events(p)
        self.assertEqual(out["answer"], "")
        self.assertEqual(out["tool_calls"], [])

    def test_non_object_json_lines_do_not_abort(self) -> None:
        # Same failure class as a string `message`: a JSON array / string /
        # number is valid JSON so JSONDecodeError does not skip it, then
        # `ev.get` raises AttributeError and the rest of a spent session is lost.
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text(
            '["not","an","object"]\n' '"bare string"\n' "42\n" '{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n',
            encoding="utf-8",
        )
        self.assertIn("ok", mod.parse_events(p)["answer"])

    def test_null_and_list_message_do_not_abort(self) -> None:
        log = self._log(
            [
                {"type": "assistant", "message": None},
                {"type": "assistant", "message": []},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("ok", out["answer"])

    def test_result_event_with_string_message_still_records_result_meta(self) -> None:
        # Result handling is BEFORE the type-guard. Moving the guard above it
        # would drop is_error / duration_ms after a spent session.
        log = self._log(
            [
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "duration_ms": 1234,
                    "num_turns": 3,
                    "session_id": "s1",
                    "message": "done",
                    "result": "final answer from result field",
                },
            ]
        )
        out = mod.parse_events(log)
        self.assertFalse(out["result"]["is_error"])
        self.assertEqual(out["result"]["duration_ms"], 1234)
        self.assertEqual(out["result"]["num_turns"], 3)
        self.assertIn("final answer from result field", out["answer"])

    def test_string_message_between_valid_events_does_not_drop_the_later(self) -> None:
        # Skip must be continue, not break / raise. A later tool_use after a
        # string-message event is still extracted -- otherwise a mid-stream
        # system event would silently drop the retrieval evidence.
        log = self._log(
            [
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "first"}]}},
                {"type": "system", "message": "not an object"},
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {"file_path": "docs/REFERENCE.md"}},
                        ]
                    },
                },
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("first", out["answer"])
        self.assertEqual(out["tool_calls"], ["Read"])

    def test_string_message_does_not_abort_the_parse(self) -> None:
        # Live defect (PR #1616): some stream-json events carry `message` as a
        # bare string. `ev.get("message") or {}` yielded the string, then `.get`
        # raised AttributeError AFTER the session was spent. The P21 run was
        # recovered only because stream.jsonl was kept. Existing tests never
        # constructed a non-dict message, so they passed both before and after.
        log = self._log(
            [
                {"type": "system", "message": "session started"},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "survived"}]}},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("survived", out["answer"])


class TerminalVerdictDoesNotGateADryRun(unittest.TestCase):
    """The stopping rule rations billed sessions, so it must not fire on a dry run.

    Regression pin for the ordering hazard that broke CI on ml#1644 with NO code
    change: the guard ran before the --dry-run branch, so the moment three
    non-follow rows pushed the Wilson upper bound under 0.75 the dry run began
    exiting 2 with empty stdout.

    Every member here drives either the predicate directly or `main()` with the
    verdict STUBBED. Neither reads the live ledger, deliberately: the corpus is
    currently INCONCLUSIVE, so any test that shells out and asserts rc==0 passes
    whether or not the fix is present. The first version of the end-to-end member
    did exactly that and pinned nothing -- it survived a full revert.
    """

    def test_a_terminal_verdict_refuses_a_real_run(self) -> None:
        for verdict in ("BET-FAILING", "HOLDS-AT-0.75"):
            with self.subTest(verdict=verdict):
                self.assertTrue(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))

    def test_a_terminal_verdict_does_not_refuse_a_dry_run(self) -> None:
        for verdict in ("BET-FAILING", "HOLDS-AT-0.75"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=True))

    def test_force_still_overrides_a_real_run(self) -> None:
        self.assertFalse(mod.refuses_terminal_verdict("BET-FAILING", force=True, dry_run=False))

    def test_a_non_terminal_verdict_never_refuses(self) -> None:
        for verdict in ("INCONCLUSIVE", "IN-PROGRESS", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))

    def _dry_run_under(self, verdict_line: str) -> tuple[int, str, str]:
        """Drive `main()` with the ledger's verdict STUBBED, leaving dispatch real.

        The verdict must be injected rather than read. An earlier version of this
        test shelled out to the real script and asserted rc==0, which passes
        against ANY corpus whose verdict is not terminal -- i.e. it passed with
        the fix fully reverted, pinning nothing. The stub is what makes it a test
        of the ordering rather than a test of today's ledger.

        `_py` is patched selectively: the ledger call is faked, dispatch still
        runs for real, so the dry-run branch is exercised end to end.
        """
        real_py = mod._py

        def fake_py(*args, **kwargs):
            if args and args[0] == str(mod.LEDGER_TOOL):
                return subprocess.CompletedProcess(args=list(args), returncode=0, stdout=verdict_line, stderr="")
            return real_py(*args, **kwargs)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mod, "_py", fake_py), mock.patch.object(sys, "argv", ["soak_run_probe.py", "--dry-run"]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = mod.main()
        return rc, out.getvalue(), err.getvalue()

    def test_dry_run_survives_a_terminal_verdict_end_to_end(self) -> None:
        """A terminal verdict must not stop the dry run reaching its own branch."""
        rc, out, err = self._dry_run_under("BET-FAILING  seeded=43/35 rate=60.5% ci=[0.456, 0.736]\n")
        self.assertEqual(rc, 0, f"dry run refused under a terminal verdict; stderr={err!r}")
        self.assertIn("priming", out.lower())

    def test_dry_run_under_a_terminal_verdict_still_reports_it(self) -> None:
        """Proceeding is not the same as concealing.

        The dry run is exempt from the stopping rule, so it must SAY that a real
        run would refuse -- otherwise the operator reads a clean dry run and
        learns nothing about the state. Pinned because deleting the notice leaves
        every other test in this file green.
        """
        rc, out, err = self._dry_run_under("BET-FAILING  seeded=43/35 rate=60.5%\n")
        # rc and the absence of REFUSING are what separate the NOTE from the guard's
        # own message -- that message ALSO names the verdict and --force, so asserting
        # only on those two strings passes against the unfixed script.
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertIn("BET-FAILING", err)
        self.assertIn("--force", err)
        self.assertNotIn("BET-FAILING", out, "verdict chatter must not pollute the scorer's stdout")

    def test_a_non_terminal_verdict_produces_no_notice(self) -> None:
        _, _, err = self._dry_run_under("INCONCLUSIVE  seeded=40/35 rate=65.0%\n")
        self.assertNotIn("terminal", err.lower())


class RetrievalChannelIgnoresAnswerText(unittest.TestCase):
    """A mention of the pointer in PROSE is not retrieval.

    Regression, found live on 2026-09-04 by probe P15. The first version of
    `retrieval_channel` searched tool inputs AND the answer text, so a run whose
    answer merely said "before the docs/REFERENCE.md relocation cut it to ~35k"
    scored as a follow -- while zero tool calls had touched the document.

    That is the worst possible direction for this instrument to fail in: a model
    reciting the pointer's path without opening it is the strongest example of
    NOT following the pointer, and the channel credited it as the opposite.
    """

    def test_answer_mention_alone_is_not_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [json.dumps({"file_path": "util/some_helper.bash"})],
            "answer": "I checked; before the docs/REFERENCE.md relocation this was larger.",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#some-anchor")
        self.assertFalse(
            ch["pointer_doc_referenced"],
            "naming the pointer in prose must not count as retrieving it",
        )
        self.assertEqual(ch["suggests"], "source-recovered-or-miss")

    def test_tool_input_hit_is_still_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [json.dumps({"command": "sed -n '10,40p' docs/REFERENCE.md"})],
            "answer": "no mention of the doc here at all",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#some-anchor")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_empty_tool_inputs_with_rich_answer_is_not_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [],
            "answer": "docs/REFERENCE.md docs/REFERENCE.md docs/REFERENCE.md",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertFalse(ch["pointer_doc_referenced"])


class WiredChannelSeesToolInputsOnly(unittest.TestCase):
    """Which of §3.E's false-positive mechanisms can reach the WIRED channel.

    Work item 4 of the 2026-09-09 soak handoff says *"two false-positive mechanisms
    remain in `util/soak_run_probe.py` -- the path that scores real runs"*. They do
    not. The two §3.E leaves open -- a ``grep -rln`` FILENAME LIST and the soak
    ledger's own NOTE -- are both things that arrive in a tool RESULT, and this
    module reads tool INPUTS only. They can reach the UNWIRED screen
    (``util/ad-hoc/2026-08-21_soak_probe_evidence.py``, which does scan results) and
    nothing else. Measured 2026-09-10 by
    ``util/ad-hoc/2026-09-10_soak_stopping_rule/wired_channel_mechanism_probe.py``.

    THIS CLASS IS A STANDARD PIN, NOT A BUG PIN, and it is meant to go red one day.
    §3.D records that wiring ``tool_result`` into ``parse_events`` **changes the
    retrieval standard** and is owner-decision territory rather than a plumbing fix.
    If someone wires it, the two mechanism cases below start firing and this reddens
    -- which is the point: the change becomes visible as a standard change instead of
    arriving as a silent widening of what counts as a follow.
    """

    DOC = "docs/REFERENCE.md"

    def test_a_filename_list_command_does_not_reach_this_channel(self) -> None:
        """`grep -rln <term> .` returns paths in its OUTPUT; the command names none."""
        self.assertFalse(mod._own_repo_occurrence(["grep -rln per_run_timeout_seconds ."], self.DOC))

    def test_reading_the_ledger_does_not_reach_this_channel(self) -> None:
        """The ledger's `note` quotes the pointer -- in the RESULT, not the command."""
        self.assertFalse(mod._own_repo_occurrence(["cat reports/soak/pointer_follow_soak.jsonl"], self.DOC))

    def test_no_soak_script_reads_tool_results(self) -> None:
        """The structural fact the two assertions above rest on.

        Asserted over the SOURCE rather than inferred from behaviour: the two cases
        above would also pass if `_own_repo_occurrence` were simply broken, and this
        is what distinguishes "cannot see results" from "saw nothing this time".
        """
        for name in ("soak_run_probe.py", "soak_next_probe.py", "soak_ledger.py"):
            with self.subTest(script=name):
                src = (REPO_ROOT / "util" / name).read_text(encoding="utf-8")
                self.assertNotIn("tool_result", src)

    def test_a_genuine_read_still_scores(self) -> None:
        """Negative control. Without it, a guard that returned False for everything
        would satisfy both mechanism assertions above."""
        self.assertTrue(mod._own_repo_occurrence(["sed -n 145,175p docs/REFERENCE.md"], self.DOC))


if __name__ == "__main__":
    # LAST IN THE FILE, DELIBERATELY. It sat at :508 with a test class below it
    # until 2026-09-11, so `python3 tests/test_soak_run_probe.py` ran 32 tests while
    # `-m unittest` ran 35 -- the three invisible ones being
    # `RetrievalChannelIgnoresAnswerText`, which pins the ml#1644 defect where a
    # prose mention of the pointer scored as retrieval. CI uses the `-m unittest`
    # form and so was never affected, which is exactly why it went unnoticed.
    unittest.main()
