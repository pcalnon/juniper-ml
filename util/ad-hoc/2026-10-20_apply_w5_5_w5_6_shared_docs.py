#!/usr/bin/env python3
"""Re-apply the W5.5 / W5.6 edits to the three shared docs on a fresh copy of the merged branch head (juniper-ml#2273).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (the #2273 landing; kept so a silent revert costs one re-run plus a small PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2273 (W5.5 + W5.6); juniper-ml#2272 (G5, which moved main under #2273 and conflicted on the two
         contended files below); util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py (the --check shape this follows)

Why
---
AGENTS.md's suite-count line and the top of CHANGELOG.md's ``### Added`` are contended lines -- every suite-adding PR
edits them -- so a second such PR in flight conflicts there, and a whole-file upload cannot clear a git-level conflict
on a line both sides changed. The landing recipe for #2273: push main's verbatim copies of the two files so they equal
main's side, let GitHub's update-branch merge, then re-apply the edits on the merged head with this script and push
the result pinned to that head. It also corrects the suite count the run-list intro sentence in docs/REFERENCE.md
states: G5 made it 214 before W5.5 / W5.6 made it 216.

Usage
-----
    python3 util/ad-hoc/2026-10-20_apply_w5_5_w5_6_shared_docs.py --root DIR [--check]

``--root`` holds ``AGENTS.md``, ``CHANGELOG.md`` and ``docs/REFERENCE.md`` as taken from the merged branch head (or from
origin/main after the merge). Every anchor must match exactly once or the script refuses and writes nothing; an edit
whose new text is already present is skipped, so a re-run is a no-op. ``--check`` reports applied / pending per file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

CHANGELOG_ENTRIES = """\
- **`stats.json` / `summary.md` carry a per-split regression target summary** (W5.5 of
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`; F-D8). The audited
  `stats.json` reported the sequence dimensions and a `class_distribution` of `null`, and nothing about the target the
  equities fit predicts.
  - `util/experiments/stats_summary.py` gains the stdlib `regression_target_summary`: per split, `n`, `n_finite`,
    `finite_fraction`, `mean`, `std` (population, ddof=0), `min`, `max`, plus a `basis` string; NaN and ±Inf count
    toward `n` and against the fraction and stay out of the moments; an empty split reports `finite_fraction: null`.
    `build_stats` writes it as `dataset.target_summary` (`null` when absent) and turns a reader error into a
    `provenance.degraded_notes` entry; `summary.md` prints one line per split.
  - `util/experiments/run_experiment.py` fetches the dataset artifact once after the dataset phase (the body the plot
    set already reads) and summarises every `y_reg_<split>` array; numpy is imported lazily, and a host without it, a
    failed fetch or an unreadable body is a degraded note, never a run failure. Both kinds pass it to `build_stats`.
  - `tests/test_stats_summary_target_summary.py` (new, 22 tests) pins the arithmetic, the carriage, the rendering and
    the driver reader on the committed audited artifact (1346 / 176 / 176 windows, every one finite); wired into
    `ci.yml` and `docs/REFERENCE.md`.

- **`util/experiment_stack.bash --shared-equities-cache DIR`, the experimentation plan's H-9 opt-in** (W5.6 of the same
  plan; F-D6), with a `run_suite.py` passthrough. The data leg launched with
  `JUNIPER_DATA_EQUITIES_CACHE_DIR=$RUN_DIR/equities-cache` and nothing else, so every cell of an equities suite paid the
  cold Yahoo / SEC fetch again.
  - The flag (or `JUNIPER_EXP_SHARED_EQUITIES_CACHE=DIR`) launches the data leg with that directory instead -- one that
    outlives the run. Absolute paths only (exit 2 before any port is allocated: the leg launches from the run dir, so a
    relative path would be per-run again); created if absent; never removed by teardown; inert with `--shared-data`. The
    default stays per-run, storage stays `$RUN_DIR/data`, and `dataset_id`s are unchanged.
  - Evidence: the announce line, `env/launch.env`, and `ports.json`'s new `equities_cache_dir` / `equities_cache_shared`.
  - `util/experiments/run_suite.py --shared-equities-cache DIR` passes it to every cell's `--up` (the env knob is honoured
    and passed explicitly) and records it on each registry row and in `suite_manifest.json`; cell ids and
    `config_sha256` are unchanged, as with the Grafana bridge.
  - `docs/REFERENCE.md` gains the runbook subsection (sharing is read-mostly, not race-free: juniper-data's cache writes
    are plain writes, so keep sharing to runs that do not overlap on cold symbols).
  - `tests/test_experiment_stack_shared_equities_cache.py` (new, 25 tests): the contract text, the misuse matrix, dry
    run, live `data_up` (PATH stubs), the `ports.json` record and the suite passthrough; wired into `ci.yml` and
    `docs/REFERENCE.md` (216 suites).

"""

# (relative path, anchor, replacement, presence marker) -- the marker is a substring that exists only once the edit is in.
EDITS: list[tuple[str, str, str, str]] = [
    (
        "AGENTS.md",
        "# Run all tests -- the full ordered list of 214 `python3 -m unittest`",
        "# Run all tests -- the full ordered list of 216 `python3 -m unittest`",
        "# Run all tests -- the full ordered list of 216 `python3 -m unittest`",
    ),
    (
        "CHANGELOG.md",
        "### Added\n\n- **`util/home_path_literal_check.py`, the G-PATH gate**",
        "### Added\n\n" + CHANGELOG_ENTRIES + "- **`util/home_path_literal_check.py`, the G-PATH gate**",
        "- **`stats.json` / `summary.md` carry a per-split regression target summary**",
    ),
    (
        "docs/REFERENCE.md",
        "**213** with W5.4's `tests/test_run_suite_acceptance.py`, **215** on 2026-10-20 with W5.5 / W5.6's",
        "**213** with W5.4's `tests/test_run_suite_acceptance.py`, **214** with G5's `tests/test_home_path_literal_check.py`, **216** on 2026-10-20 with W5.5 / W5.6's",
        "**214** with G5's `tests/test_home_path_literal_check.py`, **216** on 2026-10-20 with W5.5 / W5.6's",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, required=True, help="directory holding AGENTS.md, CHANGELOG.md and docs/REFERENCE.md")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rc = 0
    for rel, old, new, marker in EDITS:
        path: Path = args.root / rel
        text = path.read_text(encoding="utf-8")
        if marker in text:
            print(f"{rel}: applied")
            continue
        n = text.count(old)
        if n != 1:
            print(f"{rel}: REFUSED, anchor matched {n} times (expected 1): {old[:90]!r}")
            rc = 1
            continue
        if args.check:
            print(f"{rel}: pending")
            continue
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"{rel}: edited")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
