#!/usr/bin/env python3
"""Plan v1.7.10: W5.5 (the regression target summary) and W5.6 (the shared equities cache opt-in) built as juniper-ml#2273.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.9 -> v1.7.10);
         juniper-ml#2273 (W5.5 + W5.6); util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-20_plan_v1_7_10_w5_5_w5_6_landed.py --pr-state "<juniper-ml#2273 state>" [--plan PATH] [--check]

``--pr-state`` is the state of juniper-ml#2273 at the time of the revision, e.g. "merged as `1a2b3c4d`" or "open, CI green".
``--plan`` points the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the API, so
the upload is built on main's current file); the default is the repo's own copy. Every anchor must match exactly once, or
the script refuses and writes nothing; ``--check`` reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

PR = "juniper-ml#2273"
W55 = (
    "`stats_summary.regression_target_summary` summarises every `y_reg_<split>` array of the dataset artifact per split "
    "(`n`, `n_finite`, `finite_fraction`, `mean`, population `std`, `min`, `max`, and a `basis` string; NaN / ±Inf count toward `n` and against the fraction and stay out of the moments; an empty split is `null`, not 0/0); "
    "`build_stats` writes it as `dataset.target_summary` and turns a reader failure into a degraded-mode note; "
    "the driver fetches the artifact once after the dataset phase on both paths (lazy numpy — a host without it, a failed fetch or an unreadable body is a note, never a run failure; no `y_reg_*`, as for every classification generator, is a silent `null`); "
    "on the audited artifact (`equities_seq-6.0.0-15505731cba5b86d`, the mint the −18,081 was solved on) 1346 / 176 / 176 windows, every one finite, train mean 0.000929 and std 0.01824"
)
W56 = (
    "`util/experiment_stack.bash --shared-equities-cache DIR` (env equivalent `JUNIPER_EXP_SHARED_EQUITIES_CACHE=DIR`) launches the data leg with that cache instead of the per-run `${RUN_DIR}/equities-cache` — "
    "absolute path or exit 2 before any port is allocated (the leg launches from the run dir); created if absent; never removed by teardown; inert with `--shared-data`; the flag wins over the env knob; "
    "`ports.json` records `equities_cache_dir` / `equities_cache_shared`; storage stays per-run and `dataset_id`s are unchanged. "
    "`run_suite.py --shared-equities-cache DIR` passes it to every cell's `--up` and records it on the registry row and in `suite_manifest.json` (a launcher flag, not a suite key: cell ids and `config_sha256` unchanged, as for the Grafana bridge). "
    "`docs/REFERENCE.md` § Shared equities cache (W5.6, opt-in) is the runbook section the row required: the default and its cost, the rule table, the evidence, and the honest concurrency statement (juniper-data's cache writes are plain writes, so sharing is read-mostly, not race-free — sequential cells only)"
)
TESTED = (
    "`tests/test_stats_summary_target_summary.py` (22) and `tests/test_experiment_stack_shared_equities_cache.py` (25, incl. the live `data_up` compose) pass on turing; "
    "the sibling launcher / driver suites' 31 red tests are the host's pre-existing macOS set (bash 3.2's empty-array expansion, no `/proc`, `/private/var` realpaths, BSD sed, a script-shebang console script), identical on a pristine `origin/main` export; pre-commit clean"
)


def edits(state: str) -> list[tuple[str, str]]:
    return [
        ("- **Version**: 1.7.9", "- **Version**: 1.7.10"),
        # Status line: the v1.7.10 clause, after the v1.7.9 one.
        (
            ". The v1.4.0 plan edits follow that record",
            f"; **W5.5 / W5.6 built** (v1.7.10: {PR}, {state} — W5.5: {W55}. W5.6: {W56}). The v1.4.0 plan edits follow that record",
        ),
        # F-D6 / F-D8 rows: closed.
        (
            "the plan's `--shared-equities-cache` opt-in (H-9) is not implemented. |",
            f"the plan's `--shared-equities-cache` opt-in (H-9) is not implemented. **Closed 2026-10-20** (W5.6, {PR}, {state}). |",
        ),
        (
            '(plan requires "class balance or target summary stats"). |',
            f'(plan requires "class balance or target summary stats"). **Closed 2026-10-20** (W5.5, {PR}, {state}). |',
        ),
        # W5.5 / W5.6 rows: both cells.
        (
            "| W5.5 | F-D8 | juniper-ml | `stats_summary.py`: regression target summary (mean/std/min/max/finite fraction) per split. | Unit test on the audited artifact. | S |",
            f"| W5.5 | F-D8; **built 2026-10-20** ({PR}, {state}) | juniper-ml | `stats_summary.py`: regression target summary (mean/std/min/max/finite fraction) per split. **Built** ({PR}): {W55}. | Unit test on the audited artifact. **Done**: `tests/test_stats_summary_target_summary.py` loads the committed `equities_seq-6.0.0-15505731cba5b86d.npz` through the driver's reader and pins the counts, the finite fraction and the numpy-reference moments, plus the arithmetic, the carriage and the rendering; {TESTED}. | S |",
        ),
        (
            "| W5.6 | F-D6 | juniper-ml | Implement `--shared-equities-cache <dir>` (plan H-9) as an explicit opt-in; default stays per-run; this item adds its own runbook section (W4.1 lands earlier and cannot document it). | Launcher test; runbook section present in the same PR. | S |",
            f"| W5.6 | F-D6; **built 2026-10-20** ({PR}, {state}) | juniper-ml | Implement `--shared-equities-cache <dir>` (plan H-9) as an explicit opt-in; default stays per-run; this item adds its own runbook section (W4.1 lands earlier and cannot document it). **Built** ({PR}): {W56}. | Launcher test; runbook section present in the same PR. **Done**: `tests/test_experiment_stack_shared_equities_cache.py` (the contract text, the misuse matrix, dry run, live `data_up`, the `ports.json` record, the suite passthrough) and the `docs/REFERENCE.md` runbook subsection, both in {PR}. | S |",
        ),
        # Roadmap P5 row.
        (
            "| **P5** | Target summary, shared cache, producer guards (W5.5–W5.7) | **In progress** (W5.7 built 2026-10-19, juniper-data#486, merged as `58c013e3`; W5.5 / W5.6 planned) | 5 | — |",
            f"| **P5** | Target summary, shared cache, producer guards (W5.5–W5.7) | **Done in code** (W5.7 built 2026-10-19, juniper-data#486, merged as `58c013e3`; W5.5 / W5.6 built 2026-10-20, {PR}, {state}; juniper-data's release carrying W5.7 is the owner's cut) | 5 | — |",
        ),
        # Progress block: a W5.5 / W5.6 bullet before Next, and Next updated.
        (
            "  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then juniper-recurrence#219; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); juniper-data's next release carries W5.7 (owner's cut). W5.5 / W5.6 (juniper-ml) are the remaining P5 rows. The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
            f"  - **W5.5 / W5.6 built (turing session 4, 2026-10-20)**: {PR} ({state}) — W5.5: {W55}. W5.6: {W56}. {TESTED}. P5 is complete in code; juniper-data's next release (the owner's cut) carries W5.7. The model 0.6.0 `pypi` gate (run 39197693617) was still parked at the end of the session, so #215, 0.8.0, #219 and the 0.8.0 pins still wait on it.\n  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then juniper-recurrence#219; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
        ),
    ]


_ROW_ANCHOR = "Owed: the model 0.6.0 gate, then #215 / 0.8.0 / #219 and the 0.8.0 pins; juniper-data's next release (W5.7); W5.5 / W5.6; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.7.0 image. | Paul Calnon |\n"
_ROW = (
    "| 2026-10-20 | 1.7.10 | **W5.5 / W5.6 built**: {pr} ({state}) — W5.5: {w55}. W5.6: {w56}. {tested}. "
    "Updated: Status line, F-D6 and F-D8 rows, W5.5 and W5.6 rows (both cells), the roadmap P5 status row, the Progress 2026-10-19 block. "
    "Owed: the model 0.6.0 gate, then #215 / 0.8.0 / #219 and the 0.8.0 pins; juniper-data's next release (W5.7); W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.7.0 image. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pr-state", required=True, help="juniper-ml#2273's state, e.g. 'merged as `1a2b3c4d`' or 'open, CI green'")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's copy)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    plan: Path = args.plan
    text = plan.read_text(encoding="utf-8")
    pending = []
    done = 0
    for old, new in edits(args.pr_state):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))
    row = _ROW.format(pr=PR, state=args.pr_state, w55=W55, w56=W56, tested=TESTED)
    row_pending = row not in text
    if row_pending and text.count(_ROW_ANCHOR) != 1:
        print(f"REFUSED: change-log anchor matched {text.count(_ROW_ANCHOR)} times (expected 1)")
        return 1
    if args.check:
        print(f"applied {done}, pending {len(pending)}, change-log row {'pending' if row_pending else 'present'}")
        return 0
    for old, new in pending:
        text = text.replace(old, new, 1)
    if row_pending:
        i = text.index(_ROW_ANCHOR) + len(_ROW_ANCHOR)
        text = text[:i] + row + text[i:]
    plan.write_text(text, encoding="utf-8")
    print(f"applied {done + len(pending)} edits; change-log row {'added' if row_pending else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
