#!/usr/bin/env python3
"""Describe juniper-ml#2210's per_run_timeout_seconds budget check in CHANGELOG.md and the two docs that state the old rule.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (the docs half of juniper-ml#2210; kept so a silent revert costs one re-run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/experiments/run_experiment.py worst_case_budget; util/experiments/run_suite.py driver_budgets /
         check_per_run_timeout; util/ad-hoc/2026-10-25_driver_budget_survey.py;
         util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py (the pattern this follows)

Why
---
``docs/REFERENCE.md`` and ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`` say ``per_run_timeout_seconds`` must sit
above the driver's WALL budget. Since #2210 it must exceed each cell's worst-case driver budget, the sum of every
phase bound, and run_suite refuses a suite that misses it. ``CHANGELOG.md`` and ``docs/REFERENCE.md`` land from
turing as whole files built from a fresh ``origin/main`` copy, so every edit is anchored on text that must occur
exactly once.

Usage
-----
    python3 util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --root DIR [--check]

``--root`` is a tree holding the three files (default: this checkout). An edit already present is skipped, so a
re-run is a no-op. An anchor found zero times or more than once refuses the whole run before anything is
written. ``--check`` writes nothing and exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

CHANGELOG_MARKER = "- **`run_suite` refuses a `per_run_timeout_seconds` the driver's own budgets can outrun**"

CHANGELOG_ENTRY = """\
- **`run_suite` refuses a `per_run_timeout_seconds` the driver's own budgets can outrun** (juniper-ml#2210).
  The subprocess ceiling was compared, in a test only, with the wall budget alone, but the driver's other
  budgets add to that one: two 90 s health waits, dataset creation, and on recurrence a fresh wall budget for
  predict and for crossval plus `save_model`. A suite could pass the test and still be killed from outside:
  `timed_out` with `exit_code: null`, no `manifest.json`, and a re-run on `--resume`.
  - `util/experiments/run_experiment.py` gains `worst_case_budget`, the sum of the bound the driver puts on each
    phase a config runs. `save_model` counts the larger of its two paths: the wall-bounded snapshot `POST`, or
    the 60 s version probe plus the 600 s CLI re-fit for a service that returns no `operation_id`. Those two
    timeouts and cascor's `snapshot_at_end` timeout become named constants.
  - `util/experiments/run_suite.py` sums it per cell after materialisation and exits 2 before the first `--up`
    when `per_run_timeout_seconds` (default 3600) does not exceed it, naming the largest cell and its terms.
    `load_suite` stays structural, so CI's suite gate still needs no sibling repo (D5).
  - The nine recurrence suites sat under their 3900 s budget and now carry `per_run_timeout_seconds: 4500`;
    the 20 cascor suites already cleared theirs (`util/ad-hoc/2026-10-25_driver_budget_survey.py`).
  - The R-6 gate in `tests/test_experiment_suite_yamls.py` sums the same budget. New tests in
    `tests/test_run_experiment.py` and `tests/test_run_suite.py`, including the first to drive the subprocess
    kill. `docs/REFERENCE.md` gains § Suite timeout budget, and it and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
    state the new rule.
"""

SECTION = """\
#### Suite timeout budget

`run_suite` refuses a suite (exit 2, before the first `--up`) when `execution.per_run_timeout_seconds` (default `3600`) does not exceed every runnable cell's worst-case driver budget (juniper-ml#2210): a kill at or below it can land before the driver writes `manifest.json`. The driver computes the budget itself. `run_experiment.worst_case_budget` reads the cell's normalised config and the flags the suite forwards, and sums the bound it puts on each phase it will run, one after another:

| Term | App | Bound |
|------|-----|-------|
| `health_wait` | both | 2 × `--health-timeout`, 180 s (`run_suite` never forwards the flag) |
| `dataset_create` | both | The dataset budget: `execution.dataset_create_timeout_seconds` > `outputs.dataset_create_timeout_seconds` > 120 s |
| `drive` | cascor | The wall budget: `execution.max_wall_seconds` > `outputs.max_wall_seconds` > 3600 s |
| `teardown_preempt` | cascor | 30 s, the settle a drive that ran out its budget gets before collect |
| `snapshot_at_end` | cascor | 120 s, when `outputs.snapshot_at_end` is on |
| `train`, `predict`, `crossval` | recurrence | The whole wall budget each (`predict` / `crossval` when enabled): each phase is its own socket timeout, not a share of one |
| `save_model` | recurrence | When `outputs.save_model` is on, the larger of the wall budget (the snapshot `POST`) and 660 s (the 60 s version probe + the 600 s CLI re-fit, for a service that returns no `operation_id`) |

Per-request timeouts on single quick calls and the local epilogue (plots, stats, the manifest) are not counted: they take seconds. The check is `>`, not `>=`. A recurrence cell on the shared `irregular-sine-rff.yaml` base (900 s wall; predict, crossval and save_model on) comes to 3900 s, so the nine shipped recurrence suites carry `per_run_timeout_seconds: 4500`. `python3 util/ad-hoc/2026-10-25_driver_budget_survey.py --project-dir <Juniper root>` runs the same check over every shipped suite.

"""

LINK = "([§ Suite timeout budget](#suite-timeout-budget))"

#: (file, old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (
        "docs/REFERENCE.md",
        "Fourth contract: `execution.per_run_timeout_seconds` must sit **above** the wall budget (`>` not `>=`) so the driver writes the honest manifest — `perf/pf5` shipped 900/900 and was raised to 1800.",
        "Fourth contract: `execution.per_run_timeout_seconds` must sit **above** every cell's worst-case driver budget (`>` not `>=`) so the driver writes the honest manifest — `perf/pf5` shipped 900/900 and was raised to 1800. Since juniper-ml#2210 that budget is the driver's whole sum, not its wall alone, and the nine recurrence suites carry 4500 against 3900 " + LINK + ".",
    ),
    (
        "docs/REFERENCE.md",
        "- **Fourth contract — `per_run_timeout_seconds` > driver wall** (`>` not `>=`): equal destroys the manifest (subprocess kill before the driver writes). Both apps.",
        "- **Fourth contract — `per_run_timeout_seconds` > the worst-case driver budget** (`>` not `>=`): equal destroys the manifest (subprocess kill before the driver writes). Both apps. The budget is the driver's whole sum, not its wall alone, and `run_suite` refuses a suite that misses it before the first `--up` (juniper-ml#2210).",
    ),
    (
        "docs/REFERENCE.md",
        "`load_suite` plus oversize-stall / wall-pin / timeout-ordering. Operator surface: [P4 Campaign Suites](#p4-campaign-suites).",
        "`load_suite` plus oversize-stall / wall-pin / timeout-ordering, the last against each cell's worst-case driver budget since juniper-ml#2210 " + LINK + ". Operator surface: [P4 Campaign Suites](#p4-campaign-suites).",
    ),
    (
        "docs/REFERENCE.md",
        "`--compare-baseline` is reporting-only (missing tag and FAIL verdict still exit 0). Operator surface: [Suite Report Gate Inputs](#suite-report-gate-inputs).",
        "`--compare-baseline` is reporting-only (missing tag and FAIL verdict still exit 0). `PerRunTimeoutBudgetTest` (juniper-ml#2210): a `per_run_timeout_seconds` at or below a cell's worst-case driver budget exits 2 before any `--up`, naming the largest cell and its terms; `ExecuteCellTimeoutTest` drives the subprocess kill itself (a `timed_out` row with no `run_dir`, phases or metrics, and the stack still torn down). Operator surface: [Suite Report Gate Inputs](#suite-report-gate-inputs).",
    ),
    (
        "docs/REFERENCE.md",
        "Size `per_run_timeout_seconds` ABOVE the wall budget so the driver is the one that stops.",
        "Size `per_run_timeout_seconds` ABOVE the cell's worst-case driver budget so the driver is the one that stops; `run_suite` refuses the suite otherwise " + LINK + ".",
    ),
    (
        "docs/REFERENCE.md",
        "Size `per_run_timeout_seconds` **above** the wall budget so the driver is the one that stops. The Q-2 stall detector",
        "Size `per_run_timeout_seconds` **above** the cell's worst-case driver budget so the driver is the one that stops; `run_suite` refuses the suite otherwise " + LINK + ". The Q-2 stall detector",
    ),
    (
        "docs/REFERENCE.md",
        "(and size `per_run_timeout_seconds` above the wall)",
        "(and size `per_run_timeout_seconds` above the worst-case driver budget)",
    ),
    (
        "docs/REFERENCE.md",
        "| PF-3 `timed_out` with `exit_code: null` and no manifest | `per_run_timeout_seconds` ≤ wall budget. The suite subprocess killed the driver. |",
        "| PF-3 `timed_out` with `exit_code: null` and no manifest | `per_run_timeout_seconds` ≤ the worst-case driver budget. The suite subprocess killed the driver. `run_suite` refuses that ordering before launch since juniper-ml#2210, so on a current tree the driver ran past every bound it enforces. |",
    ),
    (
        "docs/REFERENCE.md",
        "Size `per_run_timeout_seconds` **above** the wall budget. The outer timeout records `timed_out` with no honest driver `manifest.json`.",
        "Size `per_run_timeout_seconds` **above** every cell's worst-case driver budget, or `run_suite` refuses the suite before the first `--up` " + LINK + ". The outer timeout records `timed_out` with no honest driver `manifest.json`.",
    ),
    (
        "docs/REFERENCE.md",
        "\n### Parallel cascor floor (Q-6 / H-7)\n",
        "\n" + SECTION + "### Parallel cascor floor (Q-6 / H-7)\n",
    ),
    (
        "docs/REFERENCE.md",
        "| Timeout ordering | `execution.per_run_timeout_seconds` **>** the driver wall (`>` not `>=`) | The timeout is run_suite's **subprocess** ceiling. Equal or below: the driver is killed before it writes `manifest.json` (`run_suite.py:350-354`). E-A `wide-pool-long` is 5400 wall / 7200 timeout. |",
        "| Timeout ordering | `execution.per_run_timeout_seconds` **>** every cell's worst-case driver budget (`>` not `>=`; juniper-ml#2210) | The timeout is run_suite's **subprocess** ceiling. Equal or below: the driver is killed before it writes `manifest.json` (`execute_cell`'s `TimeoutExpired` arm), so `run_suite` refuses the suite before launch. E-A `wide-pool-long` is a 5850 s budget (5400 wall) / 7200 timeout. |",
    ),
    (
        "docs/REFERENCE.md",
        "| `timed_out` with `exit_code: null` / no `manifest.json` | `per_run_timeout_seconds` ≤ driver wall. Raise the subprocess ceiling, not the wall, so the driver writes the honest row. |",
        "| `timed_out` with `exit_code: null` / no `manifest.json` | `per_run_timeout_seconds` ≤ the cell's worst-case driver budget, which `run_suite` refuses before launch since juniper-ml#2210; on a current tree the driver ran past every bound it enforces. Raise the subprocess ceiling, not the wall, so the driver writes the honest row. |",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "`per_run_timeout_seconds` must sit **above** the driver wall (equal loses the manifest).",
        "`per_run_timeout_seconds` must sit **above** each cell's worst-case driver budget (equal loses the manifest); `run_suite` refuses the suite otherwise (juniper-ml#2210).",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "| P4 `timed_out` with no `manifest.json` | `per_run_timeout_seconds` ≤ driver wall — raise the subprocess ceiling. |",
        "| P4 `timed_out` with no `manifest.json` | `per_run_timeout_seconds` ≤ the worst-case driver budget — raise the subprocess ceiling. A current `run_suite` refuses that before launch (juniper-ml#2210). |",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "| PF-3 `timed_out` / `exit_code: null` / no manifest | `per_run_timeout_seconds` ≤ wall budget — suite killed the driver. |",
        "| PF-3 `timed_out` / `exit_code: null` / no manifest | `per_run_timeout_seconds` ≤ the worst-case driver budget — suite killed the driver (refused before launch since juniper-ml#2210). |",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "size `per_run_timeout_seconds` above the wall. |",
        "size `per_run_timeout_seconds` above the worst-case driver budget. |",
    ),
]


def insert_changelog_entry(text: str) -> "tuple[str | None, str]":
    """(new text, status): first under [Unreleased]'s ``### Fixed``, adding that heading when it is missing."""
    if CHANGELOG_MARKER in text:
        return None, "applied"
    start = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.MULTILINE)
    if start is None:
        return None, "REFUSED, no ## [Unreleased] heading"
    nxt = re.search(r"^## \[", text[start.end() :], re.MULTILINE)
    end = start.end() + nxt.start() if nxt else len(text)
    section = text[start.end() : end]
    fixed = list(re.finditer(r"^### Fixed[ \t]*\n\n", section, re.MULTILINE))
    if len(fixed) > 1:
        return None, f"REFUSED, [Unreleased] holds {len(fixed)} '### Fixed' headings (expected at most 1)"
    if fixed:
        at = start.end() + fixed[0].end()
        return text[:at] + CHANGELOG_ENTRY + "\n" + text[at:], "pending"
    security = re.search(r"^### Security[ \t]*\n", section, re.MULTILINE)
    at = start.end() + security.start() if security else end
    return text[:at].rstrip("\n") + "\n\n### Fixed\n\n" + CHANGELOG_ENTRY + "\n" + text[at:].lstrip("\n"), "pending"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    texts: dict = {}
    pending: list = []
    refused: list = []

    def text_of(rel: str) -> str:
        if rel not in texts:
            texts[rel] = (args.root / rel).read_text(encoding="utf-8")
        return texts[rel]

    new_changelog, status = insert_changelog_entry(text_of("CHANGELOG.md"))
    print(f"CHANGELOG.md [Unreleased] entry: {status}")
    if status.startswith("REFUSED"):
        refused.append("CHANGELOG.md")
    elif new_changelog is not None:
        texts["CHANGELOG.md"] = new_changelog
        pending.append("CHANGELOG.md")

    for rel, old, new in REPLACEMENTS:
        text = text_of(rel)
        site = f"{rel}: {old.strip()[:72]}..."
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion before an anchor); applied means each old sits inside a new.
            print(f"  = {site} already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site} REFUSED: found {text.count(old)} times, expected 1")
            refused.append(rel)
            continue
        texts[rel] = text.replace(old, new, 1)
        pending.append(rel)
        print(f"  ~ {site} {'pending' if args.check else 'applied now'}")

    if refused:
        print(f"REFUSED: {', '.join(sorted(set(refused)))}; nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    for rel in sorted(set(pending)):
        (args.root / rel).write_text(texts[rel], encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
