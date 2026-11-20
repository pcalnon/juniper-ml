#!/usr/bin/env python3
"""
Apply the ml-tests carrier's edits to docs/REFERENCE.md and AGENTS.md that are not suite registrations.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: BRIEF_COMMON_R2 rules 7, 8 and 10; juniper-ml#2512 (its ERROR-row hunk), #2481 and #2512 (their tree lines)

Edits, each by an exact anchor that must occur exactly once (nothing is written otherwise; a file whose
edit is already present is left as it is):
  docs/REFERENCE.md  -- the `Running every suite` tally gains the 247 entry naming the fifteen suites;
                        #2512's ERROR-row sentence (re-derived: an ERROR row's gates are `absent`);
                        #2481's and #2512's Repository Structure tree lines after test_predict_merge.py;
                        the doc stamp, once, from main's 0.6.65 to 0.6.66 (header + footer + history row).
  AGENTS.md          -- the suite count 232 -> 247, and **Last Updated** set to the build's UTC date.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_shared_edits.py   (run from the worktree root)
"""

import sys
from pathlib import Path

TODAY = "2026-11-09"
SUITES = (
    "tests/test_claude_agent_guard_nest_depth.py",
    "tests/test_claude_agent_guard_push_signed.py",
    "tests/test_claude_agent_guard_ansi_escapes.py",
    "tests/test_claude_agent_guard_gpgsign_off.py",
    "tests/test_claude_agent_guard_sign_edges.py",
    "tests/test_launcher_empty_version_output.py",
    "tests/test_prompt_file_boolean_tokens.py",
    "tests/test_prompt_file_kind.py",
    "tests/test_wake_spacer_flags.py",
    "tests/test_launcher_prompt_and_version_edges.py",
    "tests/test_predict_merge_scratch_edges.py",
    "tests/test_predict_merge_shallow_worktree.py",
    "tests/test_predict_merge_guard_edges.py",
    "tests/test_predict_merge_error_screen.py",
    "tests/test_cascor_eval_zero_and_enabled.py",
)
_NAMED = ", ".join(f"`{s}`" for s in SUITES)

REF_EDITS = [
    (
        "`tests/test_host_state_gate_boundaries.py`); the drift script above counts",
        f"`tests/test_host_state_gate_boundaries.py`), **247** on {TODAY} with the fifteen flood-4 round-2 suites ({_NAMED}); the drift script above counts",
    ),
    (
        "| `ERROR` | `--batch` only: soft-fail row when a single PR cannot be simulated (e.g. unresolvable `origin/<headRefName>`); `true_delta=[]` and the rest of the open-PR set still runs |",
        "| `ERROR` | `--batch` only: soft-fail row when a single PR cannot be simulated (e.g. unresolvable `origin/<headRefName>`); `true_delta=[]`, `gates` empty, and the rest of the open-PR set still runs. `screen_coverage` counts each of that row's gates as `absent`: the row stays in the denominator and out of `evaluated`, so an all-`ERROR` batch reports a screened fraction of 0. It is not a pass, and not `unscreened` |",
    ),
    (
        "│   ├── test_predict_merge.py             # Behavioral: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)\n",
        "│   ├── test_predict_merge.py             # Behavioral: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)\n"
        "│   ├── test_predict_merge_scratch_edges.py # Behavioral: a shallow worktree's common objects, a sha256 scratch, each LFS protection alone\n"
        "│   ├── test_predict_merge_error_screen.py # screen_coverage: an ERROR row's empty gates are absent, not a pass; empty batch does not divide by zero\n",
    ),
    ("**Version:** 0.6.65\n**Status:** Active\n", "**Version:** 0.6.66\n**Status:** Active\n"),
    ("**Last Updated:** 2026-11-09\n**Version:** 0.6.65\n**Maintainer:**", "**Last Updated:** 2026-11-09\n**Version:** 0.6.66\n**Maintainer:**"),
]
HISTORY_ANCHOR = "\n| 0.6.65  | 2026-11-09 | The paused-fit wedge is fixed on `main`"
HISTORY_ROW = (
    "| 0.6.66  | 2026-11-09 | Cursor flood-4 round-2 tests carrier: fifteen suites registered (247 in all) and juniper-ml#2507's "
    "Ecosystem Compatibility pins added to `tests/test_pyproject_extras.py`; the predict_merge `ERROR` row says how "
    "`screen_coverage` counts it; two Repository Structure tree lines. |"
)

AGENTS_EDITS = [
    ("# Run all tests -- the full ordered list of 232 `python3 -m unittest`", "# Run all tests -- the full ordered list of 247 `python3 -m unittest`"),
    ("**Last Updated**: 2026-11-08\n", f"**Last Updated**: {TODAY}\n"),
]


def _apply(text: str, edits: list, name: str) -> str:
    for old, new in edits:
        if new in text and old not in text:
            continue
        if text.count(old) != 1:
            raise SystemExit(f"{name}: anchor found {text.count(old)} times: {old[:90]!r}")
        text = text.replace(old, new)
    return text


def main() -> int:
    ref_path, agents_path = Path("docs/REFERENCE.md"), Path("AGENTS.md")
    ref = _apply(ref_path.read_text(encoding="utf-8"), REF_EDITS, "REFERENCE")
    if HISTORY_ROW not in ref:
        start = ref.find(HISTORY_ANCHOR)
        if start < 0 or ref.count(HISTORY_ANCHOR) != 1:
            raise SystemExit("REFERENCE: 0.6.65 history row not found exactly once")
        eol = ref.index("\n", start + 1)
        ref = ref[: eol + 1] + HISTORY_ROW + "\n" + ref[eol + 1 :]
    agents = _apply(agents_path.read_text(encoding="utf-8"), AGENTS_EDITS, "AGENTS")
    ref_path.write_text(ref, encoding="utf-8")
    agents_path.write_text(agents, encoding="utf-8")
    print("REFERENCE.md and AGENTS.md edited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
