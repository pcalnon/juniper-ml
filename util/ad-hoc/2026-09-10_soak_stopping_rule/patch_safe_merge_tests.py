#!/usr/bin/env python3
"""One-shot edit: add the stored-auto-merge-body suite to tests/test_safe_merge.py.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parents[3] / "tests" / "test_safe_merge.py"
ANCHOR = 'if __name__ == "__main__":'

NEW = '''class StoredAutoMergeBodyTest(SafeMergeTestBase):
    """The THREE states of a stored auto-merge `commitBody`, and what each means.

    Established 2026-09-11 by independent consensus over 1877 PRs. The states are not
    equally safe and two of them are indistinguishable through the check the superseded
    guidance prescribed (`commitBody | length`, which is 0 for both `null` and `""`):

    * ``null``  -- OMITTED at arm time. `squash_merge_commit_message` (COMMIT_MESSAGES on
      all nine repos) resolves at MERGE time, so post-arm commits still land. Measured:
      60 post-arm commits over 48 PRs, zero losses, lags to 40.7 hours. This is what
      `gh pr merge --auto --<method>` with no body flags produces, and therefore what
      `safe_merge` produces -- it has never passed `--body-file` in any version.
    * ``""``    -- an actual empty string. Overrides the repo default; the squash lands
      with NO body. Real: 8 PRs here, e.g. ml#1831, whose landed commit is one line.
    * non-empty -- an ARM-TIME SNAPSHOT. Binds when the net fires; 23 of the 29 PRs with a
      post-arm single-parent commit lost that commit's body. ml#1228 lost an
      `Allow-Symbol-Loss:` waiver this way and reddened `main` three seconds after merge;
      ml#1877 silently lost nine commit messages.

    WHAT THIS SUITE CANNOT DO, stated rather than implied. It is hermetic -- `_gh` and
    `pr_state` are recorders -- so it can pin the tool's REACTION to each state and nothing
    else. It cannot demonstrate that GitHub snapshots the body, cannot reproduce the
    silent no-op when `--auto` is re-issued against an already-armed PR, and cannot
    reproduce the immediate merge that a disarm/re-arm triggers on a mergeable PR. Those
    are server behaviours, measured in the consensus record, not here. A green run of this
    file is evidence about `safe_merge`, not about GitHub.
    """

    def _armed(self, body):
        """A CLEAN, mergeable PR carrying a foreign net with `body` stored."""
        return _state(autoMergeRequest={"commitBody": body})

    def test_an_empty_string_body_refuses(self) -> None:
        """The destructive state, and the one `length` cannot tell from the safe one."""
        h = Harness([self._armed("")])
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(h)
        msg = str(ctx.exception).lower()
        self.assertIn("empty commit body", msg)
        self.assertIn("no body at all", msg)
        self.assertEqual([c for c in h.calls if c[:2] == ["pr", "merge"]], [],
                         "a refusal must never degrade into a merge")

    def test_a_null_body_proceeds(self) -> None:
        """THE NEGATIVE CONTROL, and the reason this suite is not vacuous.

        `null` is the state `safe_merge` itself produces on every run. A guard that
        refused here would refuse every ordinary merge -- which is a far worse failure
        than the one being guarded against, and it is exactly what a predicate keyed on
        `length` rather than on the value would do.
        """
        h = Harness([self._armed(None)])
        self.assertIsNone(safe_merge.stale_snapshot_refusal(self._armed(None)))
        self.run_merge(h)
        self.assertTrue([c for c in h.calls if c[:2] == ["pr", "merge"]],
                        "a null body is the SAFE state and must not block the merge")

    def test_no_net_at_all_proceeds(self) -> None:
        """The other negative control: an unarmed PR has no stored body to judge."""
        self.assertIsNone(safe_merge.stale_snapshot_refusal(_state()))
        self.assertIsNone(safe_merge.stale_snapshot_refusal(_state(autoMergeRequest=None)))

    def test_a_non_empty_snapshot_does_not_refuse(self) -> None:
        """DELIBERATE, and the narrowest part of the design.

        A stored body is not wrong in itself -- supplied AFTER the last commit it is
        correct, and is the only way to guarantee a waiver trailer's exact text; twelve
        PRs here carry a curated message, and the alternative on a large PR is ml#1797's
        26,052-character auto-concatenation. Whether a non-empty snapshot is STALE depends
        on commits this predicate cannot see, so judging it here would refuse a legitimate
        practice on a guess. The staleness measurement lives in
        `util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py`, which
        compares the snapshot against the PR's actual commits.
        """
        self.assertIsNone(safe_merge.stale_snapshot_refusal(self._armed("a curated body")))

    def test_the_predicate_reads_the_value_not_its_length(self) -> None:
        """The specific defect that produced the superseded diagnosis.

        `len(None)` raises and `len("")` is 0, so any predicate written as a length test
        either crashes on the safe state or cannot separate it from the destructive one.
        This pins that `None` and `""` reach DIFFERENT outcomes.
        """
        self.assertIsNone(safe_merge.stale_snapshot_refusal(self._armed(None)))
        self.assertIsNotNone(safe_merge.stale_snapshot_refusal(self._armed("")))

    def test_pr_state_actually_requests_the_field(self) -> None:
        """Guard the guard. Every assertion above feeds `stale_snapshot_refusal` a dict
        built by hand; if `pr_state` stopped asking GitHub for `autoMergeRequest`, the key
        would simply be absent at runtime, the predicate would return None for every PR,
        and this whole suite would still pass. Assert the field is in the request."""
        captured = {}

        def fake_gh(args, timeout=120):
            captured["args"] = list(args)
            return '{"state":"OPEN"}'

        self.monkey(safe_merge, "_gh", fake_gh)
        safe_merge.pr_state("o", "r", 1)
        joined = " ".join(captured["args"])
        self.assertIn("autoMergeRequest", joined)


'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "StoredAutoMergeBodyTest" in src:
        print("already applied")
        return 0
    if src.count(ANCHOR) != 1:
        print(f"REFUSING: anchor found {src.count(ANCHOR)} times (expected 1)", file=sys.stderr)
        return 1
    TARGET.write_text(src.replace(ANCHOR, NEW + ANCHOR), encoding="utf-8")
    print(f"applied to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
