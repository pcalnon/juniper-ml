#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Complementary gate for ``util/soak_run_probe.py``'s stopping rule.

``tests/test_soak_run_probe.py`` already pins the helper and a BET-FAILING
``--dry-run`` walk through ``main()``. Those members cannot see:

* a ``main()`` that always passes ``dry_run=True`` into the helper -- every
  existing test stays green and a real run keeps spending sessions after a
  terminal verdict;
* the live ledger's exit codes. ``soak_ledger.py status`` returns 1 for
  ``BET-FAILING`` *and* for ``INCONCLUSIVE`` with escalations, and 2 for
  ``DEGRADED`` / ``NO-DATA`` / ``NO-SEEDED-DATA``. The existing suite stubs
  ``rc=0``, so ``if st.returncode: return 2`` is invisible;
* ``verdict_is_terminal`` being prefix-only and case-sensitive.

Hermetic: ``dispatch`` is stubbed. Nothing here launches ``claude`` or
reads the live ledger.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
import unittest.mock as mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe_stopping_rule", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


class _ReachedDispatch(Exception):
    """Sentinel: the spend control let the invocation through to dispatch."""


def _ledger_py(verdict_line: str, ledger_rc: int):
    def fake_py(*args, **kwargs):
        if args and args[0] == str(mod.LEDGER_TOOL):
            return subprocess.CompletedProcess(args=list(args), returncode=ledger_rc, stdout=verdict_line, stderr="")
        raise AssertionError(f"unexpected _py call: {args!r}")

    return fake_py


def _reached_dispatch(*_a, **_k):
    raise _ReachedDispatch()


class VerdictIsTerminalPrefixOnly(unittest.TestCase):
    """``startswith``, not ``in``. A substring match would refuse on chatter."""

    def test_the_two_terminal_names(self) -> None:
        self.assertTrue(mod.verdict_is_terminal("BET-FAILING"))
        self.assertTrue(mod.verdict_is_terminal("HOLDS-AT-0.75"))
        self.assertTrue(mod.verdict_is_terminal("HOLDS-AT-"))

    def test_a_substring_is_not_enough(self) -> None:
        for verdict in ("NOT-BET-FAILING", "PRE-BET-FAILING", "X-BET-FAILING"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))

    def test_holds_at_requires_the_trailing_hyphen(self) -> None:
        for verdict in ("HOLDS-AT", "HOLDS-AT0.75", "HOLDS"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))

    def test_case_is_significant(self) -> None:
        self.assertFalse(mod.verdict_is_terminal("bet-failing"))
        self.assertFalse(mod.verdict_is_terminal("holds-at-0.75"))

    def test_ledger_non_answers_are_not_terminal(self) -> None:
        """Still true, and deliberately unchanged: none of these is an ANSWER.

        The fail-open fix went into a second predicate rather than in here. Folding
        the non-answers into ``verdict_is_terminal`` would have been the smaller
        diff and the wrong one: it would make the ``--dry-run`` NOTE tell an
        operator the soak had reached a conclusion when the ledger is simply
        unreadable, and it would redden these prefix pins for a property the
        tokens do not have.
        """
        for verdict in ("INCONCLUSIVE", "DEGRADED", "NO-DATA", "NO-SEEDED-DATA", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))

    def test_unreadable_states_refuse_through_the_second_predicate(self) -> None:
        """INCONCLUSIVE is runnable; the other four are not.

        The distinction the exit code cannot make: ``soak_ledger.py status`` exits
        2 for DEGRADED / NO-DATA / NO-SEEDED-DATA, but it also exits 2 for argparse
        misuse -- and exits 1 for BOTH a real crash and a perfectly runnable
        INCONCLUSIVE soak with an open escalation.
        """
        for verdict in ("DEGRADED", "NO-DATA", "NO-SEEDED-DATA", ""):
            with self.subTest(verdict=verdict):
                self.assertTrue(mod.verdict_is_unusable(verdict))
                self.assertTrue(mod.refuses_unusable_verdict(verdict, force=False, dry_run=False))
        self.assertFalse(mod.verdict_is_unusable("INCONCLUSIVE"))
        self.assertFalse(mod.refuses_unusable_verdict("INCONCLUSIVE", force=False, dry_run=False))

    def test_the_two_exemptions_apply_to_the_unusable_rule_too(self) -> None:
        """--force is an override and --dry-run spends nothing. Same as terminal."""
        for verdict in ("DEGRADED", "NO-DATA", "NO-SEEDED-DATA", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.refuses_unusable_verdict(verdict, force=True, dry_run=False))
                self.assertFalse(mod.refuses_unusable_verdict(verdict, force=False, dry_run=True))

    def test_unusable_is_exact_membership_not_a_prefix(self) -> None:
        """``HOLDS-AT-`` needs a prefix test; these names do not, and must not get one.

        A prefix test would silently give a future ``NO-DATA-EVER`` the meaning of
        ``NO-DATA``. It also keeps the two rules structurally different, which is
        the honest description of them.
        """
        for near_miss in ("NO-DATA-EVER", "DEGRADED-PARTIAL", "NO-SEEDED", "NODATA"):
            with self.subTest(verdict=near_miss):
                self.assertFalse(mod.verdict_is_unusable(near_miss))


class RealRunIsGatedThroughMain(unittest.TestCase):
    """#1690's e2e only drives ``--dry-run``. The spend control is the real run."""

    def _invoke(
        self,
        argv: list[str],
        verdict_line: str,
        *,
        ledger_rc: int = 0,
        dispatch=None,
    ) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        dispatch_impl = dispatch if dispatch is not None else mock.Mock(side_effect=AssertionError("dispatch must not run on this path"))
        with (
            mock.patch.object(mod, "_py", _ledger_py(verdict_line, ledger_rc)),
            mock.patch.object(mod, "dispatch", dispatch_impl),
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            rc = mod.main()
        return rc, out.getvalue(), err.getvalue()

    def test_a_real_run_under_bet_failing_refuses_before_dispatch(self) -> None:
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "BET-FAILING  seeded=43/35 rate=60.5% ci=[0.456, 0.736]\n",
            ledger_rc=1,
        )
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("REFUSING", err)
        self.assertIn("BET-FAILING", err)

    def test_a_real_run_under_holds_at_refuses_before_dispatch(self) -> None:
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "HOLDS-AT-0.75  seeded=40/35 rate=82.0%\n",
        )
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("REFUSING", err)
        self.assertIn("HOLDS-AT-0.75", err)

    def test_force_reaches_dispatch_under_a_terminal_verdict(self) -> None:
        """``--probe-id`` and ``--reason`` are now part of the override (D3).

        This test read ``["--force"]`` alone until 2026-09-17. That was the
        contract then and is not the contract now: owner decision D3 admits the
        override only for a NAMED probe with the reason recorded. The scoped form
        must still reach dispatch, or D3 has repealed ``--force`` instead of
        narrowing it -- which is the failure this case now pins.
        """
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py", "--force", "--probe-id", "P23", "--reason", "re-baseline"],
                "BET-FAILING  seeded=43/35 rate=60.5%\n",
                ledger_rc=1,
                dispatch=_reached_dispatch,
            )

    def test_dry_run_under_holds_at_notes_and_proceeds(self) -> None:
        rc, out, err = self._invoke(
            ["soak_run_probe.py", "--dry-run"],
            "HOLDS-AT-0.75  seeded=40/35 rate=82.0%\n",
            dispatch=mock.Mock(return_value=("P-TEST", "secret task must not leak")),
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertIn("HOLDS-AT-0.75", err)
        self.assertIn("priming", out.lower())
        self.assertNotIn("secret task must not leak", out)

    def test_inconclusive_with_ledger_exit_1_does_not_refuse(self) -> None:
        """Live ``status`` returns 1 when escalations are open, even if INCONCLUSIVE.

        Existing tests stub rc=0, so they cannot see a ``if st.returncode: return 2``
        that would refuse every escalated soak -- a spend-control false positive.
        """
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "INCONCLUSIVE  seeded=40/35 rate=65.0% escalations=1\n",
                ledger_rc=1,
                dispatch=_reached_dispatch,
            )

    def test_bet_failing_refuses_because_of_the_token_not_the_exit_code(self) -> None:
        """Same rc=1 as the INCONCLUSIVE+escalations case; only the token differs."""
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "BET-FAILING  seeded=43/35 rate=60.5%\n",
            ledger_rc=1,
        )
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("REFUSING", err)

    def test_degraded_refuses_on_a_real_run(self) -> None:
        """INVERTED 2026-09-10. This pin previously asserted the fail-open.

        It was a deliberate marker, not an accident: #1690 deferred fail-closed and
        pinned the deferral so it stayed visible instead of decaying into an
        unexamined default. Closing the gap is what inverts it. A successor reading
        the history should not mistake this for a regression -- the old assertion
        and this one cannot both be green, and that was the point of writing it.

        The rename is a symbol REMOVAL to the per-PR sequence-safety screen, which
        reported both inverted pins as ``FAIL/LOST`` -- correctly: a same-file rename
        is indistinguishable from a deletion to a screen that matches on names. It is
        waived by an enumerated ``Allow-Symbol-Loss:`` commit trailer naming both
        methods, never by the ``allow-symbol-loss`` label, which downgrades the whole
        screen to WARN-only for the run and would hide any *unintended* loss in the
        same PR.
        """
        for verdict in ("DEGRADED", "NO-DATA", "NO-SEEDED-DATA"):
            with self.subTest(verdict=verdict):
                rc, _, err = self._invoke(
                    ["soak_run_probe.py"],
                    f"{verdict}  seeded=0/35 rate=n/a\n",
                    ledger_rc=2,
                )
                self.assertEqual(rc, mod.RC_REFUSED)
                self.assertIn("REFUSING", err)
                self.assertIn(verdict, err)
                self.assertNotIn("terminal", err)

    def test_a_ledger_tool_crash_refuses(self) -> None:
        """INVERTED 2026-09-10, same deferral as above.

        Empty stdout + rc=2 is what a crashed ledger tool produces, and ``""`` is
        the token ``status_verdict`` returns for it. The refusal message must not
        print a bare empty string where the verdict goes, or the operator is told
        ``soak verdict is  --`` and has to read the source to find out what broke.
        """
        rc, _, err = self._invoke(["soak_run_probe.py"], "", ledger_rc=2)
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("REFUSING", err)
        self.assertIn("empty", err)
        self.assertNotIn("terminal", err)

    def test_force_reaches_dispatch_under_an_unreadable_ledger(self) -> None:
        """The override has to work on the new refusal too, or it is a dead end."""
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py", "--force", "--probe-id", "P23", "--reason", "ledger repair"],
                "NO-DATA  seeded=0/35 rate=n/a\n",
                ledger_rc=2,
                dispatch=_reached_dispatch,
            )

    def test_dry_run_under_an_unreadable_ledger_notes_and_proceeds(self) -> None:
        """#1690's exemption, extended to the second rule and NOT quietly dropped.

        A dry run spends nothing, so the spend control was never in scope for it.
        The NOTE must say the state is unreadable rather than ``terminal``: those
        are opposite conditions and an operator acts differently on each.
        """
        rc, out, err = self._invoke(
            ["soak_run_probe.py", "--dry-run"],
            "NO-DATA  seeded=0/35 rate=n/a\n",
            ledger_rc=2,
            dispatch=mock.Mock(return_value=("P-TEST", "secret task must not leak")),
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertIn("NO-DATA", err)
        self.assertIn("not a readable state", err)
        self.assertNotIn("secret task must not leak", out)

    def test_inconclusive_with_no_escalations_still_reaches_dispatch(self) -> None:
        """The negative control for the whole change.

        If the fix had been written as an allow-list, or keyed on the exit code,
        the ordinary runnable state is what it would have broken -- and every other
        test here asserts a refusal, so nothing else would have caught it.
        """
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "INCONCLUSIVE  seeded=40/35 rate=65.0% escalations=0\n",
                ledger_rc=0,
                dispatch=_reached_dispatch,
            )

    def test_a_prefixed_status_line_is_not_a_verdict(self) -> None:
        """Only ``stdout.split()[0]`` is consulted. A leading label hides the token."""
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "NOTE: BET-FAILING  seeded=43/35 rate=60.5%\n",
                dispatch=_reached_dispatch,
            )


class ForceIsNarrowedToANamedProbe(unittest.TestCase):
    """Owner decisions D1/D3, ruled 2026-09-17, enforced rather than written down.

    ``notes/JUNIPER_2026-09-17_JUNIPER-ML_SOAK-TEN-OWNER-DECISIONS-RULED.md``:
    D1 authorises a named probe on request and declines the campaign; D3 admits
    ``--force`` only for that named probe, one run, reason recorded.

    The gap being closed is specific. Every path refuses today only because the
    verdict is terminal, so ``--force`` is the sole way any run happens -- and a
    bare ``--force`` dispatched ``dispatch(None)``, the least-covered-first
    campaign D1 declined. The override that was meant to authorise ONE run
    re-opened the default one.
    """

    def test_a_scoped_force_is_in_scope(self) -> None:
        self.assertIsNone(mod.force_scope_refusal("P23", "re-baseline after rung 1", force=True, dry_run=False))

    def test_force_without_a_probe_id_is_refused(self) -> None:
        why = mod.force_scope_refusal(None, "a reason", force=True, dry_run=False)
        self.assertIsNotNone(why)
        self.assertIn("--probe-id", why)

    def test_force_without_a_reason_is_refused(self) -> None:
        why = mod.force_scope_refusal("P23", None, force=True, dry_run=False)
        self.assertIsNotNone(why)
        self.assertIn("--reason", why)

    def test_a_whitespace_reason_is_not_a_reason(self) -> None:
        """``--reason ' '`` satisfies ``is not None`` and records nothing."""
        self.assertIsNotNone(mod.force_scope_refusal("P23", "   ", force=True, dry_run=False))

    def test_an_unforced_run_is_not_this_predicate_s_business(self) -> None:
        """Without ``--force`` the verdict governs. Returning a refusal here would
        make every ordinary run demand a ``--reason`` it has no use for."""
        self.assertIsNone(mod.force_scope_refusal(None, None, force=False, dry_run=False))

    def test_a_dry_run_is_exempt_like_the_two_spend_controls(self) -> None:
        self.assertIsNone(mod.force_scope_refusal(None, None, force=True, dry_run=True))

    def test_the_refusal_names_which_half_is_missing(self) -> None:
        """One message for two faults sends the operator to the source to find out
        which one they hit. The predicate returns the string for that reason."""
        self.assertNotEqual(
            mod.force_scope_refusal(None, "r", force=True, dry_run=False),
            mod.force_scope_refusal("P23", None, force=True, dry_run=False),
        )


class ForceScopeRefusalIsReachedBeforeTheSpendControls(unittest.TestCase):
    """Ordering, and it is the whole point: ``--force`` DISARMS the two controls.

    Checked after them, an unscoped override sails through both -- they return
    ``False`` on ``force`` -- and the campaign D1 declined runs anyway. The
    refusal must land before dispatch AND before a session is spent.
    """

    def _invoke(self, argv: list[str], verdict_line: str, *, ledger_rc: int = 1) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(mod, "_py", _ledger_py(verdict_line, ledger_rc)),
            mock.patch.object(mod, "dispatch", mock.Mock(side_effect=AssertionError("dispatch must not run"))),
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            rc = mod.main()
        return rc, err.getvalue()

    def test_bare_force_under_a_terminal_verdict_refuses(self) -> None:
        rc, err = self._invoke(
            ["soak_run_probe.py", "--force"],
            "BET-FAILING  seeded=42/35 rate=59.5%\n",
        )
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("REFUSING", err)
        self.assertIn("--probe-id", err)

    def test_the_refusal_cites_the_ruling(self) -> None:
        """An operator hitting this is being told a decision was made, not that a
        flag is malformed. The message has to say where to read it."""
        _, err = self._invoke(["soak_run_probe.py", "--force"], "BET-FAILING  seeded=42/35\n")
        self.assertIn("SOAK-TEN-OWNER-DECISIONS-RULED", err)

    def test_named_but_unexplained_force_refuses_too(self) -> None:
        rc, err = self._invoke(
            ["soak_run_probe.py", "--force", "--probe-id", "P23"],
            "BET-FAILING  seeded=42/35 rate=59.5%\n",
        )
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertIn("--reason", err)

    def test_the_refusal_is_the_reserved_code_not_a_hard_error(self) -> None:
        """``RC_REFUSED`` is whitelisted by ``SuccessExitStatus=3`` in the unit.

        Returning 1 or 2 here would make a by-design refusal fire
        ``OnFailure=`` and append a strike to ``logs/soak_probe_failures.log``
        -- the exact confusion #1884 built the code to prevent.
        """
        rc, _ = self._invoke(["soak_run_probe.py", "--force"], "BET-FAILING  seeded=42/35\n")
        self.assertEqual(rc, mod.RC_REFUSED)
        self.assertNotIn(rc, (1, 2))


class LedgerVerdictsAreAllClassified(unittest.TestCase):
    """Every verdict ``soak_ledger.py`` can emit is classified by the guard.

    THE RESIDUAL THIS CLOSES. The fix is a deny-list -- refuse on four named
    tokens -- so a verdict added to the ledger and not named here still fails
    open, which is the same defect class the fix itself repairs. An allow-list
    would have been fail-closed for the unknown, but it would also have destroyed
    ``test_a_prefixed_status_line_is_not_a_verdict``: that test's whole subject is
    a token the guard does not recognise reaching dispatch.

    So the drift is caught here instead. The verdict names are read out of
    ``soak_ledger.py``'s AST rather than copied, because a copied list is exactly
    the thing that goes stale silently.
    """

    LEDGER = REPO_ROOT / "util" / "soak_ledger.py"

    # Runnable states: the soak has no answer YET, and a run can still change that.
    KNOWN_RUNNABLE = frozenset({"IN-PROGRESS", "INCONCLUSIVE"})

    @staticmethod
    def _emitted_verdicts(src: str) -> set[str]:
        """Verdict names from ``verdict, note = <name>, ...`` assignments.

        ``HOLDS-AT-{DECISION_BOUNDARY}`` is an f-string: its literal head is what
        ``verdict_is_terminal`` prefix-matches, so the head is what we collect.
        """
        import ast

        found: set[str] = set()
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Assign):
                continue
            targets = [t for t in node.targets if isinstance(t, ast.Tuple) and t.elts and isinstance(t.elts[0], ast.Name) and t.elts[0].id == "verdict"]
            if not targets or not isinstance(node.value, ast.Tuple) or not node.value.elts:
                continue
            head = node.value.elts[0]
            if isinstance(head, ast.Constant) and isinstance(head.value, str):
                found.add(head.value)
            elif isinstance(head, ast.JoinedStr) and head.values:
                lead = head.values[0]
                if isinstance(lead, ast.Constant) and isinstance(lead.value, str):
                    found.add(lead.value)
        return found

    def test_the_extractor_finds_the_verdicts_it_is_supposed_to(self) -> None:
        """Negative control. A silently-empty extractor would pass every test below.

        This is the ``[[reference_vacuous_pass_check_class]]`` failure: an AST walk
        that matches nothing returns an empty set, and "every element is
        classified" is then trivially true forever.
        """
        found = self._emitted_verdicts(self.LEDGER.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(found), 6, f"extractor went blind: {found}")
        self.assertIn("BET-FAILING", found)
        self.assertIn("NO-DATA", found)

    def test_every_emitted_verdict_is_terminal_unusable_or_known_runnable(self) -> None:
        """Add a verdict to the ledger without classifying it here and this reddens."""
        for verdict in sorted(self._emitted_verdicts(self.LEDGER.read_text(encoding="utf-8"))):
            with self.subTest(verdict=verdict):
                classes = [
                    name
                    for name, hit in (
                        ("terminal", mod.verdict_is_terminal(verdict)),
                        ("unusable", mod.verdict_is_unusable(verdict)),
                        ("runnable", verdict in self.KNOWN_RUNNABLE),
                    )
                    if hit
                ]
                self.assertEqual(
                    len(classes),
                    1,
                    f"{verdict!r} is classified {classes or 'NOT AT ALL'}; it must be " f"exactly one of terminal / unusable / runnable. An unclassified " f"verdict FAILS OPEN and spends a session.",
                )


class RefusalExitCodeSurvivesToTheProcess(unittest.TestCase):
    """The refusal code as a REAL subprocess exit status, with nothing mocked.

    Every other test here calls ``main()`` and reads its return value. systemd does
    not: it reads the process's wait status, and ``SuccessExitStatus=3`` is checked
    against that. ``raise SystemExit(main())`` makes the two equal today, and this
    is the test that would notice if it ever stopped being -- an ``except
    SystemExit`` swallowing it, a wrapper shell, an ``os._exit``.

    Hermetic by relocation rather than by mocking. ``ROOT`` is derived from
    ``__file__``, so a copy of the script in a throwaway ``util/`` directory finds
    a STUB ledger next to it, and the live ``reports/soak/pointer_follow_soak.jsonl``
    is never read or moved. That is what §10 of the 09-08 evidence-recovery note
    recorded as not exercisable; it is exercisable this way.
    """

    STUB = "#!/usr/bin/env python3\n" "import sys\n" "sys.stdout.write({stdout!r})\n" "raise SystemExit({rc})\n"

    def _run(self, argv: list[str], *, stdout: str, rc: int) -> subprocess.CompletedProcess:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "util").mkdir()
            (root / "util" / "soak_run_probe.py").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            (root / "util" / "soak_ledger.py").write_text(self.STUB.format(stdout=stdout, rc=rc), encoding="utf-8")
            return subprocess.run(  # nosec B603 - fixed argv, no shell
                [sys.executable, str(root / "util" / "soak_run_probe.py"), *argv],
                capture_output=True,
                text=True,
                timeout=60,
            )

    def test_a_terminal_verdict_exits_with_the_refusal_code(self) -> None:
        r = self._run([], stdout="BET-FAILING  seeded=43/35 rate=60.5%\n", rc=1)
        self.assertEqual(r.returncode, mod.RC_REFUSED)
        self.assertIn("REFUSING", r.stderr)

    def test_an_empty_ledger_exits_with_the_refusal_code(self) -> None:
        """THE CONTROL §3.A names: a readable but EMPTY ledger.

        ``soak_ledger.py status`` on an empty file prints ``NO-DATA ...`` and exits
        2 -- re-measured 2026-09-10. Before this change the wrapper read the token,
        found it non-terminal, ignored ``st.returncode`` entirely, and dispatched a
        billed session against a corpus with nothing in it.
        """
        r = self._run([], stdout="NO-DATA  seeded=0/35 rate=n/a ci=n/a escalations=0\n", rc=2)
        self.assertEqual(r.returncode, mod.RC_REFUSED)
        self.assertIn("NO-DATA", r.stderr)
        self.assertIn("cannot be read", r.stderr)

    def test_a_crashed_ledger_tool_exits_with_the_refusal_code(self) -> None:
        """Empty stdout. rc 1, not 2 -- a traceback exits 1, which is also what a
        perfectly runnable INCONCLUSIVE-with-escalations soak returns. The token is
        what discriminates, so the stub's rc is deliberately the ambiguous one."""
        r = self._run([], stdout="", rc=1)
        self.assertEqual(r.returncode, mod.RC_REFUSED)
        self.assertIn("empty", r.stderr)

    def test_argparse_misuse_still_exits_2_and_is_not_whitelisted(self) -> None:
        """The other half of why the code is 3. If misuse and refusal shared a code,
        `SuccessExitStatus` could not whitelist one without the other."""
        r = self._run(["--no-such-flag"], stdout="INCONCLUSIVE  seeded=40/35\n", rc=0)
        self.assertEqual(r.returncode, 2)
        self.assertNotEqual(r.returncode, mod.RC_REFUSED)


class UnitFileWhitelistsTheRefusalCode(unittest.TestCase):
    """The systemd half of the same defect, and the first test to read a unit file.

    Nothing in the repo parsed one before this class, which is why the missing
    ``SuccessExitStatus=`` survived: the guard and the unit have to agree on what
    a refusal looks like, and no test could see both halves at once.
    """

    UNIT = REPO_ROOT / "util" / "systemd" / "juniper-soak-probe.service"
    lines: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.lines = [ln.strip() for ln in cls.UNIT.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]

    def _directive(self, key: str) -> list[str]:
        return [ln.split("=", 1)[1] for ln in self.lines if ln.startswith(f"{key}=")]

    def test_the_unit_whitelists_exactly_the_guards_refusal_code(self) -> None:
        """Not a hardcoded 3: read the constant, so the two move together."""
        self.assertEqual(self._directive("SuccessExitStatus"), [str(mod.RC_REFUSED)])

    def test_the_unit_does_not_whitelist_argparse_misuse(self) -> None:
        """``SuccessExitStatus=2`` is the trap this whole exit code exists to avoid.

        The wrapper returns 2 for argparse misuse, so whitelisting it would make a
        typo in ``ExecStart=`` read as success forever -- on the unattended path,
        firing every ~6h, with `OnFailure=` silenced for the one case it is for.
        """
        whitelisted = {code for value in self._directive("SuccessExitStatus") for code in value.replace(",", " ").split()}
        self.assertNotIn("2", whitelisted)
        self.assertNotIn("1", whitelisted)

    def test_the_refusal_code_collides_with_nothing_the_unit_must_still_catch(self) -> None:
        """The property, not the literal: 3 must differ from argparse's 2 and error 1."""
        self.assertNotIn(mod.RC_REFUSED, (0, 1, 2))

    def test_the_failure_handler_is_still_armed(self) -> None:
        """Whitelisting the refusal must not have disarmed real-failure reporting."""
        self.assertEqual(self._directive("OnFailure"), ["juniper-soak-probe-failed.service"])
        self.assertEqual(self._directive("Type"), ["oneshot"])


if __name__ == "__main__":
    unittest.main()
