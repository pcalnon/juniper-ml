#!/usr/bin/env python3
"""Close APD-DATA-052 and file two new rows in the ecosystem defect register.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc register maintenance
Author:      Paul Calnon
Version:     1.0.0
License:     MIT

WHAT THIS DOES
--------------
One register edit, three changes, because they all touch the same counts and a
second PR would collide on every one of them.

1. **Closes `APD-DATA-052`** (juniper-data#418) -- ``allow_truncation`` is now a
   tri-state, so a caller can refuse truncation where the operator enabled it.
   Four touches, not five: the row has no section-3 detail entry.

2. **Files `APD-ECO-008`** -- the fourth `APIKeyAuth` copy. Closing
   `APD-CASCOR-005` ported the non-short-circuiting compare into juniper-data,
   juniper-cascor and juniper-service-core, and left juniper-canopy's copy
   short-circuiting. The drift gate **structurally cannot** name it, so nothing
   will notice. Filed against `APD-ECO` rather than a canopy prefix because
   the register reserves canopy findings for the `F-CANOPY-*` E2E ledger, and
   because this is a cross-repo drift row, not a canopy behaviour row.

3. **Files `APD-DATA-053` as FIXED** (juniper-data#417) -- three unresolved
   merge-conflict blocks committed to `docs/DEVELOPER_CHEATSHEET.md` on `main`.
   Filed-and-closed in one edit; `APD-DATA-050` set that precedent.

WHY A SCRIPT AND NOT AN EDITOR
------------------------------
Every replacement below asserts it matched **exactly once** and rolls the whole
file back otherwise. A register edit that half-applies is worse than one that
fails: the counts and the prose disagree while every count-based check still
passes, which is the failure the five-touch protocol exists to prevent.

This script does NOT compute the new open count. It rewrites the prose and then
the operator re-derives with ``util/ad-hoc/register_open_set.py`` and
``util/ad-hoc/register_status_crosscheck.py``, which is the protocol's own
instruction ("re-derive rather than read").

Run from the repo root; ``--dry-run`` prints the plan and writes nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

PR_TRISTATE = "[juniper-data#418](https://github.com/pcalnon/juniper-data/pull/418)"
PR_MARKERS = "[juniper-data#417](https://github.com/pcalnon/juniper-data/pull/417)"

# ---- touch 1: the section-4.9 table row for APD-DATA-052 --------------------

ROW_052_OLD = "| APD-DATA-052 | **A caller cannot refuse truncation where the operator enabled it.**"
ROW_052_NEW = f"| APD-DATA-052 | **FIXED ({PR_TRISTATE})** — **a caller could not refuse truncation where the operator enabled it.**"

# The row's Source cell named the test by its pre-inversion name. Renaming it in
# place keeps the cell resolvable: the old name exists nowhere on main any more.
ROW_052_SRC_OLD = "`tests/unit/test_csv_import_generator.py::test_request_cannot_opt_out_of_deployment_allow_truncation` | — | High |"
ROW_052_SRC_NEW = (
    "`tests/unit/test_csv_import_generator.py::test_request_can_opt_out_of_deployment_allow_truncation` "
    "(**inverted, not deleted** — the surviving half is `test_omitted_allow_truncation_still_defers_to_the_deployment`) | — | High |"
)

# ---- touch 2: the two new section-4.9 rows ----------------------------------

ROW_CASCOR_013_ANCHOR = "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**"

ROW_ECO_008 = (
    "| APD-ECO-008 | **There is a FOURTH `APIKeyAuth`, and the drift gate cannot express it.** "
    "Closing `APD-CASCOR-005` ([juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659)"
    " / [juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974)) ported juniper-data's "
    "non-short-circuiting `matched`-flag compare into juniper-cascor and juniper-service-core. "
    "**`juniper-canopy/src/security.py:74` is still `any(hmac.compare_digest(api_key, k) for k in self._api_keys)`** "
    "— it short-circuits, so the number of comparisons depends on where the matching key falls. "
    "The row is filed for the SECOND half, which outlives the timing question: "
    "`tests/test_service_fork_drift.py` declares `_FORK_REPOS = (\"juniper-data\", \"juniper-cascor\")` at `:59`, "
    "and `test_every_guard_is_well_formed` asserts `site.repo in _FORK_REPOS` at `:285` — so a canopy site is "
    "rejected by the gate's own structural check and **no guard can reference canopy even in principle**. "
    "Widening `_FORK_REPOS` asserts every EXISTING guard against canopy too, which is a real blast radius, "
    "not a one-line edit. Canopy also diverges at `:53` — `set(api_keys) if api_keys else set()`, with no "
    "blank-key filter anywhere in the constructor, where the other three carry "
    "`{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}`. That second divergence is "
    "**probably not an auth bypass** (its only caller maps `\"\"` to `None`, disabling auth, and "
    "`enforce_auth_posture` fails the boot when `require_auth` is set) — but that reading has never been "
    "independently refuted, so it is recorded as the best current reading and not as a settled fact "
    "| M | `juniper-canopy/src/security.py` (`:53` constructor, `:74` compare); "
    "`juniper-ml/tests/test_service_fork_drift.py` (`_FORK_REPOS` at `:59`, the assertion at `:285`) | — | High |"
)

ROW_DATA_053 = (
    f"| APD-DATA-053 | **FIXED ({PR_MARKERS})** — **three unresolved merge-conflict blocks were committed to "
    "`docs/DEVELOPER_CHEATSHEET.md` and rendered verbatim on `main`**: nine literal `<<<<<<<` / `=======` / "
    "`>>>>>>>` marker lines citing `03b3b94c` (twice) and `8d9b71ea`. All three were purely ADDITIVE — each "
    "side was distinct content (`## Empty-train shape metadata` vs `## Equities symbol cap`; "
    "`## Standalone generator imports` vs ``## DatasetMeta `n_val` ``; three troubleshooting rows vs three "
    "more) — so nothing had to be chosen between and no content was dropped. Found while auditing "
    "`allow_truncation` documentation surfaces for `APD-DATA-052`, which is the point worth keeping: **no "
    "check in this repo looks for conflict markers**, and markdownlint does not flag them. The defect "
    "survived every required check on the PR that introduced it and on every PR since "
    "| M | `docs/DEVELOPER_CHEATSHEET.md` (blocks at `:180`, `:222`, `:300` as committed) | — | High |"
)

# ---- touch 3: the section-5.1 verification rows ------------------------------

V51_ANCHOR = "| APD-DATA-018 | No async job pattern — generation runs inside the request |"

V51_ROWS = (
    f"| APD-DATA-052 | A caller cannot refuse truncation where the operator enabled it | {PR_TRISTATE} | "
    "`allow_truncation` is `bool | None` defaulting to `None`; the three `or settings.*` sites became "
    "`settings.X if params.allow_truncation is None else params.allow_truncation`. **The third site is the one "
    "worth naming**: `_resolve_incomplete_policy` reads the flag independently of `_resolve_bounds`, so porting "
    "the tri-state to the two cap sites alone would have let a caller refuse an over-cap universe while still "
    "being served fabricated fundamentals. Verified NON-VACUOUS by "
    "`util/ad-hoc/2026-09-22_verify_tristate_tests_are_not_vacuous.py` (juniper-data), which runs two mutations "
    "because one cannot screen both halves: reverting the sites to the OR reddens exactly the three "
    "\"explicit false refuses\" tests and leaves the three deference tests green (`None or settings.X == "
    "settings.X`), while reverting the schemas to a plain `bool` reddens exactly the three deference tests and "
    "leaves the opt-out tests green. Each mutation is caught by the tests that should see it **and by no "
    "others**. `test_request_cannot_opt_out_of_deployment_allow_truncation` was INVERTED, not deleted, and its "
    "same-file rename needed an `Allow-Symbol-Loss:` trailer — the AST screen cannot distinguish an in-file "
    "rename from a deletion. **No `dataset_id` churn**: `bind_deployment_defaults` stores the resolved opt-in, "
    "which is unchanged for every request that does not send an explicit `false`. |\n"
    f"| APD-DATA-053 | Three merge-conflict blocks committed to `docs/DEVELOPER_CHEATSHEET.md` | {PR_MARKERS} | "
    "Nine marker lines removed; both halves of all three conflicts retained. Blocks 1 and 2 each join two `##` "
    "sections and gained the `---` separator the document uses between sections; block 3's halves are rows of "
    "one table and were left contiguous, because a separator there would have cut the table in two. Diff is "
    "`-9 / +6` in one file. |"
)

# ---- touch 4: the section-2 status paragraph ---------------------------------

S2_OLD = "and (2026-09-15) `APD-DATA-050` ([juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)) and (2026-09-21, RATIFIED — a decision, no PR) `APD-DATA-047` — and seven are open"
S2_NEW = (
    "and (2026-09-15) `APD-DATA-050` ([juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)) "
    "and (2026-09-21, RATIFIED — a decision, no PR) `APD-DATA-047` "
    f"and (2026-09-22) `APD-DATA-052` ({PR_TRISTATE}) / `APD-DATA-053` ({PR_MARKERS}) — and eight are open"
)

S2_COUNT_OLD = "twenty-two filed, of which"
S2_COUNT_NEW = "twenty-four filed, of which"

# The two new rows are NOT from the round-37 validation the 4.9 preamble describes.
S49_PREAMBLE_OLD = """Rows the primer never contained, filed from later work — here, the independent-agent validation of the
round-37 defect-register handoff (six lanes, 2026-09-08; record in
`reports/2026-09-08_round-37-consensus/`)."""
S49_PREAMBLE_NEW = """Rows the primer never contained, filed from later work — here, the independent-agent validation of the
round-37 defect-register handoff (six lanes, 2026-09-08; record in
`reports/2026-09-08_round-37-consensus/`). **Two rows below have a different provenance and say so in
their own text**: `APD-ECO-008` and `APD-DATA-053` were both found on 2026-09-22 while implementing
`APD-DATA-052` — the first is the residue of closing `APD-CASCOR-005` (a fourth copy the drift gate
cannot name), the second was found by auditing that implementation's own documentation surfaces.
Neither came from a validation round, which is worth recording: **the two defects nearest a fix are
the one it did not reach and the one its own audit walks past.**"""

HEADER_OLD = "**Last Updated**: 2026-09-21"
HEADER_NEW = "**Last Updated**: 2026-09-22"


def substitute(text: str, old: str, new: str, label: str) -> str:
    """Replace ``old`` with ``new``, refusing unless it matched exactly once."""
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"REFUSED [{label}]: pattern matched {count} times (expected 1).\n  {old[:140]}")
    return text.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the plan; write nothing")
    args = parser.parse_args()

    original = REGISTER.read_text(encoding="utf-8")
    text = original

    text = substitute(text, ROW_052_OLD, ROW_052_NEW, "4.9 row APD-DATA-052 status")
    text = substitute(text, ROW_052_SRC_OLD, ROW_052_SRC_NEW, "4.9 row APD-DATA-052 source cell")
    text = substitute(text, ROW_CASCOR_013_ANCHOR, f"{ROW_ECO_008}\n{ROW_DATA_053}\n{ROW_CASCOR_013_ANCHOR}", "4.9 two new rows")
    text = substitute(text, V51_ANCHOR, f"{V51_ROWS}\n{V51_ANCHOR}", "5.1 verification rows")
    text = substitute(text, S2_OLD, S2_NEW, "2 status list")
    text = substitute(text, S2_COUNT_OLD, S2_COUNT_NEW, "2 filed count")
    text = substitute(text, S49_PREAMBLE_OLD, S49_PREAMBLE_NEW, "4.9 preamble provenance")
    text = substitute(text, HEADER_OLD, HEADER_NEW, "header Last Updated")

    if args.dry_run:
        print("dry run: 8 substitutions all matched exactly once; nothing written.")
        print(f"  would grow the register by {len(text) - len(original)} bytes")
        return 0

    REGISTER.write_text(text, encoding="utf-8")
    print(f"wrote {REGISTER.relative_to(REPO)} (+{len(text) - len(original)} bytes)")
    print("\nNOW RE-DERIVE -- this script does not compute the open count:")
    print("  python3 util/ad-hoc/register_open_set.py")
    print("  python3 util/ad-hoc/register_status_crosscheck.py")
    print("  grep -n 'APD-DATA-052' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md   # and READ every hit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
