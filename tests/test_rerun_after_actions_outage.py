#!/usr/bin/env python3
"""Hermetic tests for the 2026-10-05 Actions-outage recovery helper.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-10-05_rerun_after_actions_outage.py`` waits until the Actions
status component is exactly ``operational`` (or exactly ``degraded_performance``
when ``--accept-degraded`` is passed, since helper 0.2.0), re-runs completed runs in
a fixed conclusion set, and can hand the PR to ``util/safe_merge.py --execute``. A
wrong status match merges during an outage; a wider conclusion set re-runs a green
workflow; ``--no-merge`` that still calls safe_merge merges a PR the operator
asked to leave. Nothing here talks to GitHub or the status page.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-10-05_rerun_after_actions_outage.py"
_spec = importlib.util.spec_from_file_location("rerun_after_actions_outage", _SCRIPT)
assert _spec is not None and _spec.loader is not None
rerun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerun)

_RERUN_IDS = ("11", "12", "13", "14")
_MIXED_RUNS = [
    {"databaseId": 11, "name": "CI", "status": "completed", "conclusion": "failure"},
    {"databaseId": 12, "name": "Docs", "status": "completed", "conclusion": "cancelled"},
    {"databaseId": 13, "name": "Slow", "status": "completed", "conclusion": "timed_out"},
    {"databaseId": 14, "name": "Boot", "status": "completed", "conclusion": "startup_failure"},
    {"databaseId": 15, "name": "OK", "status": "completed", "conclusion": "success"},
    {"databaseId": 16, "name": "Skip", "status": "completed", "conclusion": "skipped"},
    {"databaseId": 17, "name": "Neutral", "status": "completed", "conclusion": "neutral"},
    {"databaseId": 18, "name": "Need", "status": "completed", "conclusion": "action_required"},
    {"databaseId": 19, "name": "Stale", "status": "completed", "conclusion": "stale"},
    {"databaseId": 20, "name": "Case", "status": "completed", "conclusion": "Failure"},
    {"databaseId": 21, "name": "Empty", "status": "completed", "conclusion": ""},
    {"databaseId": 22, "name": "Null", "status": "completed", "conclusion": None},
    {"databaseId": 23, "name": "Live", "status": "in_progress", "conclusion": "failure"},
    {"databaseId": 24, "name": "Queue", "status": "queued", "conclusion": None},
    {"databaseId": 25, "name": "Absent", "status": "completed"},
]


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += float(seconds)


class _Proc:
    __slots__ = ("returncode",)

    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


class _Body:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_Body":
        return self

    def __exit__(self, *exc: object) -> None:
        """Never suppresses: an exception inside the ``with`` propagates, as with a real response."""


def _rerun_cmds(calls: dict) -> list[list[str]]:
    return [call["cmd"] for call in calls["run"] if "safe_merge.py" not in " ".join(call["cmd"])]


def _drive(argv: list[str], *, statuses: list[str], runs: object = None, head: str = "abcdef1234567890", merge_rc: int = 0, rerun_rc: int = 0, gh_reply=None, calls: dict | None = None):
    """Run ``main`` with the status page, ``gh``, and the clock replaced.

    ``calls`` is filled even when ``main`` raises, so a test can see that a bad payload
    produced no ``gh run rerun`` and no ``safe_merge``.
    """
    clock = _Clock()
    if calls is None:
        calls = {"gh": [], "run": []}
    else:
        calls.setdefault("gh", [])
        calls.setdefault("run", [])
    index = {"n": 0}

    def actions_status() -> str:
        status = statuses[min(index["n"], len(statuses) - 1)]
        index["n"] += 1
        return status

    def gh(*args: str) -> str:
        calls["gh"].append(args)
        if gh_reply is not None:
            return gh_reply(args)
        if args[:2] == ("pr", "view"):
            return json.dumps({"headRefOid": head})
        if args[:2] == ("run", "list"):
            return json.dumps([] if runs is None else runs)
        raise AssertionError(args)

    def run(cmd, check=False, **kwargs):
        calls["run"].append({"cmd": [str(part) for part in cmd], "check": check})
        rc = merge_rc if any(str(part).endswith("safe_merge.py") for part in cmd) else rerun_rc
        if check and rc != 0:
            raise subprocess.CalledProcessError(rc, cmd)
        return _Proc(rc)

    stdout = io.StringIO()
    with (
        patch.object(rerun, "actions_status", actions_status),
        patch.object(rerun, "gh", gh),
        patch.object(rerun.time, "time", clock.time),
        patch.object(rerun.time, "sleep", clock.sleep),
        patch.object(rerun.subprocess, "run", run),
        patch.object(sys, "argv", ["rerun", *argv]),
        contextlib.redirect_stdout(stdout),
    ):
        code = rerun.main()
    return code, calls, clock, stdout.getvalue()


class ActionsStatusTest(unittest.TestCase):
    """The status page is a gate, so a wrong shape must not read as operational."""

    def _status(self, payload: object) -> str:
        body = _Body(json.dumps(payload).encode())
        with patch.object(rerun.urllib.request, "urlopen", return_value=body) as opened:
            status = rerun.actions_status()
        opened.assert_called_once()
        self.assertEqual(opened.call_args.args[0], "https://www.githubstatus.com/api/v2/components.json")
        self.assertTrue(str(opened.call_args.args[0]).startswith("https://"))
        return status

    def test_only_the_actions_component_counts(self) -> None:
        self.assertEqual(rerun.STATUS_URL, "https://www.githubstatus.com/api/v2/components.json")
        status = self._status(
            {
                "components": [
                    {"name": "actions", "status": "operational"},
                    {"name": "GitHub Actions", "status": "operational"},
                    {"name": "Actions", "status": "major_outage"},
                ]
            }
        )
        self.assertEqual(status, "major_outage")

    def test_a_missing_component_or_status_is_not_operational(self) -> None:
        self.assertEqual(self._status({"components": []}), "unknown (no Actions component)")
        self.assertEqual(self._status({}), "unknown (no Actions component)")
        self.assertEqual(self._status({"components": [{"name": "Actions"}]}), "None")
        # The component walk sits outside the status-page try, so a components value that is
        # not a list of objects aborts. It must not be readable as operational.
        with self.assertRaises(AttributeError):
            self._status({"components": {"Actions": {"status": "operational"}}})

    def test_a_status_page_failure_is_not_operational(self) -> None:
        with patch.object(rerun.urllib.request, "urlopen", side_effect=urllib.error.URLError("operational")):
            self.assertEqual(rerun.actions_status(), "unknown (URLError)")
        with patch.object(rerun.urllib.request, "urlopen", side_effect=TimeoutError("operational")):
            self.assertEqual(rerun.actions_status(), "unknown (TimeoutError)")
        with patch.object(rerun.urllib.request, "urlopen", return_value=_Body(b"not-json")):
            self.assertEqual(rerun.actions_status(), "unknown (JSONDecodeError)")

    def test_the_conclusion_set_is_exactly_the_four_failure_classes(self) -> None:
        self.assertEqual(rerun.RERUN_CONCLUSIONS, {"failure", "cancelled", "timed_out", "startup_failure"})


class RerunSelectionTest(unittest.TestCase):
    """Which runs are re-run, and which flag actually merges."""

    def test_only_completed_failure_class_runs_are_rerun(self) -> None:
        code, calls, clock, _out = _drive(["--repo", "juniper-ml", "--pr", "2164", "--no-merge"], statuses=["operational"], runs=_MIXED_RUNS)
        self.assertEqual(code, 0)
        self.assertEqual(clock.slept, [])
        self.assertEqual(
            _rerun_cmds(calls),
            [["gh", "run", "rerun", run_id, "--repo", "pcalnon/juniper-ml"] for run_id in _RERUN_IDS],
        )
        self.assertTrue(all(call["check"] is False for call in calls["run"]))
        self.assertFalse(any("safe_merge.py" in " ".join(call["cmd"]) for call in calls["run"]))

    def test_a_failed_rerun_does_not_stop_the_rest_or_merge(self) -> None:
        runs = [
            {"databaseId": 11, "name": "CI", "status": "completed", "conclusion": "failure"},
            {"databaseId": 12, "name": "Docs", "status": "completed", "conclusion": "cancelled"},
        ]
        code, calls, _clock, _out = _drive(["--repo", "juniper-ml", "--pr", "2164", "--no-merge"], statuses=["operational"], runs=runs, rerun_rc=1)
        self.assertEqual(code, 0)
        self.assertEqual([cmd[3] for cmd in _rerun_cmds(calls)], ["11", "12"])

    def test_merge_returns_the_safe_merge_code_and_still_runs_with_nothing_to_rerun(self) -> None:
        code, calls, _clock, out = _drive(
            ["--owner", "octocat", "--repo", "juniper-recurrence", "--pr", "192", "--merge", "--merge-timeout", "90"],
            statuses=["operational"],
            runs=[],
            merge_rc=4,
        )
        self.assertEqual(code, 4)
        self.assertEqual(_rerun_cmds(calls), [])
        self.assertEqual(
            calls["run"][0]["cmd"],
            [sys.executable, str(REPO_ROOT / "util" / "safe_merge.py"), "--pr", "192", "--repo", "juniper-recurrence", "--owner", "octocat", "--execute", "--timeout", "90"],
        )
        self.assertIn("handing off to:", out)
        self.assertFalse(calls["run"][0]["check"])

    def test_the_run_list_is_the_pr_head(self) -> None:
        head = "0123456789abcdef"
        _code, calls, _clock, _out = _drive(["--owner", "octocat", "--repo", "juniper-ml", "--pr", "2164", "--no-merge"], statuses=["operational"], runs=[], head=head)
        view, listed = calls["gh"]
        self.assertEqual(view, ("pr", "view", "2164", "--repo", "octocat/juniper-ml", "--json", "headRefOid"))
        self.assertEqual(listed, ("run", "list", "--repo", "octocat/juniper-ml", "--commit", head, "--limit", "50", "--json", "databaseId,name,status,conclusion"))

    def test_a_missing_run_id_aborts_before_any_rerun_or_merge(self) -> None:
        runs = [{"name": "CI", "status": "completed", "conclusion": "failure"}]
        calls: dict = {}
        with self.assertRaises(KeyError):
            _drive(["--repo", "juniper-ml", "--pr", "2164", "--merge"], statuses=["operational"], runs=runs, calls=calls)
        self.assertEqual(calls["run"], [])

    def test_a_run_list_that_is_not_a_list_aborts_before_merge(self) -> None:
        calls: dict = {}
        with self.assertRaises(AttributeError):
            _drive(["--repo", "juniper-ml", "--pr", "2164", "--merge"], statuses=["operational"], runs={"databaseId": 11, "status": "completed", "conclusion": "failure"}, calls=calls)
        self.assertEqual(calls["run"], [])

    def test_a_head_payload_without_a_sha_aborts_before_merge(self) -> None:
        def reply(args: tuple) -> str:
            if args[:2] == ("pr", "view"):
                return "{}"
            raise AssertionError(args)

        calls: dict = {}
        with self.assertRaises(KeyError):
            _drive(["--repo", "juniper-ml", "--pr", "2164", "--merge"], statuses=["operational"], gh_reply=reply, calls=calls)
        self.assertEqual(calls["run"], [])


class WaitGateTest(unittest.TestCase):
    """Anything other than exactly ``operational`` must not re-run or merge, unless ``--accept-degraded`` admits ``degraded_performance``."""

    def test_non_operational_statuses_never_touch_gh(self) -> None:
        for status in ("major_outage", "partial_outage", "degraded_performance", "operational ", "Operational", "unknown (URLError)"):
            with self.subTest(status=status):
                code, calls, clock, out = _drive(
                    ["--repo", "juniper-ml", "--pr", "2164", "--no-merge", "--max-wait-seconds", "0", "--poll-seconds", "5"],
                    statuses=[status],
                    runs=_MIXED_RUNS,
                )
                self.assertEqual(code, 2)
                self.assertEqual(calls["gh"], [])
                self.assertEqual(calls["run"], [])
                self.assertEqual(clock.slept, [5.0])
                self.assertIn("GAVE UP", out)
                self.assertIn(status, out)

    def test_give_up_exits_2_and_does_not_merge(self) -> None:
        code, calls, clock, out = _drive(
            ["--repo", "juniper-ml", "--pr", "2164", "--merge", "--max-wait-seconds", "10", "--poll-seconds", "10"],
            statuses=["major_outage"],
            runs=_MIXED_RUNS,
        )
        self.assertEqual(code, 2)
        self.assertEqual(clock.slept, [10.0, 10.0])
        self.assertEqual(calls["gh"], [])
        self.assertEqual(calls["run"], [])
        self.assertIn("GAVE UP", out)
        self.assertNotIn("handing off", out)

    def test_elapsed_equal_to_the_budget_still_waits(self) -> None:
        """The give-up comparison is ``>``, so a poll that lands on the budget is not a give-up."""
        code, calls, clock, _out = _drive(
            ["--repo", "juniper-ml", "--pr", "2164", "--no-merge", "--max-wait-seconds", "10", "--poll-seconds", "10"],
            statuses=["major_outage", "major_outage", "operational"],
            runs=[],
        )
        self.assertEqual(code, 0)
        self.assertEqual(clock.slept, [10.0, 10.0])
        self.assertEqual(len(calls["gh"]), 2)

    def test_accept_degraded_ends_the_wait_on_degraded_performance(self) -> None:
        """0.2.0: ``--accept-degraded`` admits exactly ``degraded_performance`` (the 21:32Z state, when jobs ran again)."""
        code, calls, clock, out = _drive(
            ["--repo", "juniper-ml", "--pr", "2164", "--no-merge", "--accept-degraded", "--max-wait-seconds", "0", "--poll-seconds", "5"],
            statuses=["degraded_performance"],
            runs=_MIXED_RUNS,
        )
        self.assertEqual(code, 0)
        self.assertEqual(clock.slept, [])
        self.assertIn("degraded_performance (accepted)", out)
        self.assertEqual([cmd[3] for cmd in _rerun_cmds(calls)], list(_RERUN_IDS))
        self.assertFalse(any("safe_merge.py" in " ".join(call["cmd"]) for call in calls["run"]))

    def test_accept_degraded_admits_nothing_else(self) -> None:
        """The flag widens the gate by one exact state; an outage, a case change or a padded value still waits."""
        for status in ("partial_outage", "major_outage", "Degraded_performance", "degraded_performance ", "unknown (URLError)"):
            with self.subTest(status=status):
                code, calls, clock, out = _drive(
                    ["--repo", "juniper-ml", "--pr", "2164", "--merge", "--accept-degraded", "--max-wait-seconds", "0", "--poll-seconds", "5"],
                    statuses=[status],
                    runs=_MIXED_RUNS,
                )
                self.assertEqual(code, 2)
                self.assertEqual(calls["gh"], [])
                self.assertEqual(calls["run"], [])
                self.assertEqual(clock.slept, [5.0])
                self.assertIn("GAVE UP", out)

    def test_merge_and_no_merge_are_required_and_exclusive(self) -> None:
        for argv in (
            ["rerun", "--repo", "juniper-ml", "--pr", "1"],
            ["rerun", "--repo", "juniper-ml", "--pr", "1", "--merge", "--no-merge"],
            ["rerun", "--pr", "1", "--no-merge"],
        ):
            with self.subTest(argv=argv), patch.object(sys, "argv", argv), patch.object(rerun.urllib.request, "urlopen", side_effect=AssertionError("status page")), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    rerun.main()
            self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
