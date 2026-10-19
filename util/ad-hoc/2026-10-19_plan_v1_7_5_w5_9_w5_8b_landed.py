#!/usr/bin/env python3
"""Plan v1.7.5: record that W5.9 and the W5.8 (B) model half landed, model 0.5.0 was cut, and the service half is open.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.4 -> v1.7.5);
         juniper-recurrence#209 (W5.9 + the W5.8 (B) model half), #210 (the model 0.5.0 proposal), the service PR;
         util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py (the revision this follows);
         util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py, util/ad-hoc/2026-10-19_apply_w5_8b_service.py,
         util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py (the measurement quoted)

Why this exists
---------------
Concurrent sessions edit the plan, so a revision is applied as exact-string edits that each must match once,
re-runnable after a fast-forward. The service PR number and the release's state are parameters because the
script is written while both are in flight.

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_5_w5_9_w5_8b_landed.py --service-pr N --release "<state>" [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

MODEL_PR = "juniper-recurrence#209, `d6a81eb4`"
PROPOSAL_PR = "juniper-recurrence#210, `99ae4a7b`"
MEASURED = "measured on the E-H artifact through the route's own per-fold path (`util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py`, five expanding folds): the old `0.0` default aggregates **−2.1e4** eval r² (embargo 2; −2.3e4 with the route's default embargo 0), `\"gcv\"` on model 0.5.0 **−0.195** (−0.190), with λ = 1000 at the grid ceiling and `null_model: true` in every fold — the consensus re-derivation's −0.195 reproduced"


def edits(service_pr: int, release: str) -> list[tuple[str, str]]:
    svc = f"juniper-recurrence#{service_pr}"
    return [
        ("- **Version**: 1.7.4", "- **Version**: 1.7.5"),
        # Status line.
        (
            "and the `gcv_at_edge` / `null_model` flags; in `[Unreleased]`, ships in the next 0.6.x). The v1.4.0 plan edits follow that record",
            f"and the `gcv_at_edge` / `null_model` flags; in `[Unreleased]`, ships in the next 0.6.x); **W5.9 and the W5.8 (B) model half landed, model 0.5.0 cut** (v1.7.5: {MODEL_PR}, 2026-10-19 — the linear rung standardises the train fold for any non-zero ridge, the `ridge = 0` path byte-identical, and a GCV fit exposes `gcv_at_edge_` / `null_model_`; proposal {PROPOSAL_PR}; {release}; the service half — `default_ridge: \"gcv\"`, floor `>=0.5.0` — is {svc} for recurrence 0.7.0, {MEASURED}). The v1.4.0 plan edits follow that record",
        ),
        # W5.8 row: header and acceptance cells.
        (
            "(B) accepted by the owner 2026-10-18** — ships in recurrence 0.7.0 / model 0.5.0 as CHANGELOG \"Changed\" | juniper-recurrence + model |",
            f"(B) accepted by the owner 2026-10-18; model half landed 2026-10-19** ({MODEL_PR}; model 0.5.0 via {PROPOSAL_PR}); **service half {svc}** (recurrence 0.7.0; floor `>=0.5.0`) — CHANGELOG \"Changed\" in both | juniper-recurrence + model |",
        ),
        (
            "model test: the linear rung standardises train-fold-only and the `ridge = 0` path is byte-identical to today's. | M |",
            f"model test: the linear rung standardises train-fold-only and the `ridge = 0` path is byte-identical to today's. **Done 2026-10-19**: {MEASURED}; `juniper-recurrence-model/tests/test_readouts.py` pins the train-fold statistics, the persisted `mean` / `std`, column-scale invariance of a fixed ridge, and the `ridge = 0` coefficients equal to a raw `lstsq`; the service's `test_readout_diagnostics.py` pins the bare request on both routes reporting `ridge_mode: gcv` and its λ. | M |",
        ),
        # W5.9 row: header and acceptance cells.
        (
            "| W5.9 | F-SCI1 (GCV ceiling); **proposed by W0.9, rewritten 2026-10-05; accepted 2026-10-18** | juniper-recurrence-model |",
            f"| W5.9 | F-SCI1 (GCV ceiling); **proposed by W0.9, rewritten 2026-10-05; accepted 2026-10-18; landed 2026-10-19** ({MODEL_PR}; model 0.5.0) | juniper-recurrence-model |",
        ),
        (
            "Unit test: a fold whose GCV optimum is the null model is reported as such; the E-H GCV cells report it in folds 0 / 3 / 4. | S |",
            "Unit test: a fold whose GCV optimum is the null model is reported as such; the E-H GCV cells report it in folds 0 / 3 / 4. **Done 2026-10-19**: `_gcv_select` evaluates the intercept-only GCV `n·‖yc‖² / (n − 1)²` (the λ → ∞ limit), returns `at_edge` / `null_model` beside the fit and logs a WARNING on either; `LinearReadout` / `RFFReadout` set `gcv_at_edge_` / `null_model_` after a GCV fit (`None` after a fixed-ridge fit and after `from_state`; not persisted); `_GCV_GRID` unchanged. Pinned on pure noise (the null model at the ceiling), an exact target (the floor, not the null model) and an interior optimum. On the E-H artifact the standardised linear rung reports the null model in all five folds. | S |",
        ),
        # P5 status row.
        (
            "| In Progress — **W5.10 Done** (juniper-recurrence#208, `ac329d57`, 2026-10-18; in `[Unreleased]`); W5.8 (B) + W5.9 next | 5 | W5.10 in the next recurrence 0.6.x; W5.8 (B) + W5.9 in recurrence 0.7.0, model 0.5.0 |",
            f"| In Progress — **W5.10 Done** (juniper-recurrence#208, `ac329d57`, 2026-10-18; in `[Unreleased]`); **W5.9 + the W5.8 (B) model half Done** ({MODEL_PR}, 2026-10-19; model 0.5.0 proposed in {PROPOSAL_PR}; {release}); the W5.8 (B) service half is {svc} | 5 | W5.9 and the standardisation in model 0.5.0; W5.10 and the W5.8 (B) default in recurrence 0.7.0 (floor `>=0.5.0`) |",
        ),
        # Dependency row.
        (
            "**W5.10 landed 2026-10-18** (juniper-recurrence#208, `ac329d57`): the response announces the selected λ, so W5.8 (B) is unblocked |",
            f"**W5.10 landed 2026-10-18** (juniper-recurrence#208, `ac329d57`): the response announces the selected λ, so W5.8 (B) is unblocked. **W5.9 + the model half landed 2026-10-19** ({MODEL_PR}); the service half ({svc}) raises the floor to `>=0.5.0` because `\"gcv\"` on the raw block is the −247 configuration |",
        ),
        # Progress: a new 2026-10-19 block after the W5.10 session's.
        (
            "  - **Next**: W5.8 (B) + W5.9 for recurrence 0.7.0 / model 0.5.0; W5.2 and W5.4; W5.7. The W0.1 service-core half and the parent `Juniper/AGENTS.md` paragraph stay open (the Compose pin followed in juniper-deploy#251, v1.7.3).\n",
            "  - **Next**: W5.8 (B) + W5.9 for recurrence 0.7.0 / model 0.5.0; W5.2 and W5.4; W5.7. The W0.1 service-core half and the parent `Juniper/AGENTS.md` paragraph stay open (the Compose pin followed in juniper-deploy#251, v1.7.3).\n"
            "\n"
            "  **Progress 2026-10-19, turing W5.9 / W5.8 (B) session** (every commit through the GitHub-signed API path; the owner's checkout untouched — the work was done on a scratch copy overlaid with `main`):\n"
            f"  - **W5.9 + the W5.8 (B) model half landed**: {MODEL_PR}. `_gcv_select` returns a `_GCVSelection` with the intercept-only GCV and the two flags, logging a WARNING at an edge or a null-model optimum; `LinearReadout` standardises `M` with the train-fold statistics for `ridge > 0` and `\"gcv\"` (persisted as `mean` / `std` beside `coef`, a `standardized` descriptor flag; a pre-0.5.0 state predicts on the raw block), and both readouts expose `gcv_at_edge_` / `null_model_`. `ridge = 0.0` is byte-identical to 0.4.0 (pinned against a raw `lstsq` at readout and model level). Model suite: 215 passed, coverage 98.30 %; ruff clean.\n"
            f"  - **Model 0.5.0 cut**: proposal {PROPOSAL_PR} (`util/release_train/propose.py --execute --cross-repo` on the tree at `d6a81eb4`; the follow-on ceiling-bump PR #211 it also opened was closed as superseded by the floor raise); ceremony `--execute --cross-repo --target-sha 99ae4a7b…` on the tree at that commit; {release}.\n"
            f"  - **W5.8 (B) service half opened**: {svc} — `Settings.default_ridge: \"gcv\"`, the floor `juniper-recurrence-model>=0.5.0,<0.6.0` (base, `[torch]`, `[bench-torch]`, the image lock `==0.5.0`), `conf/experiments/irregular-sine-rff.yaml` `service.default_ridge: gcv`, README and CHANGELOG Changed; the W5.10 tests now take the model's flags verbatim. App suite on model 0.5.0: all passed, coverage 98.29 %; ruff clean. Its CI needs 0.5.0 on PyPI (the app lane installs the model from the index).\n"
            f"  - **Acceptance**: {MEASURED}. The E-H artifact is on turing under `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/`.\n"
            "  - **Next**: merge the service PR once 0.5.0 is on PyPI, then cut recurrence 0.7.0 (proposal → ceremony → the owner's `pypi` gate); W5.2 and W5.4 (round 3 of the CV-blowup note's review first); W5.7. The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes on the 0.6.1 image and the client-docstring follow-up stay open.\n",
        ),
    ]


#: The 1.7.4 row's tail: the 1.7.5 row goes right after it.
_ROW_ANCHOR = "Owed: W5.8 (B) + W5.9 (recurrence 0.7.0 / model 0.5.0); W5.2, W5.4; W5.7; W0.1's service-core half; the parent AGENTS.md paragraph. | Paul Calnon |\n"

_CHANGELOG_ROW = (
    "| 2026-10-19 | 1.7.5 | **W5.9 and the W5.8 (B) model half landed; model 0.5.0 cut; the service half opened** ({model_pr}; proposal {proposal_pr}; {release}; service {svc}). "
    "The linear rung standardises the memory block with the train-fold statistics for any non-zero ridge (the `ridge = 0` path byte-identical to 0.4.0; statistics persisted); `_gcv_select` evaluates the intercept-only GCV and a GCV fit exposes `gcv_at_edge_` / `null_model_` with a WARNING at an edge or a null-model optimum. "
    "The service's `default_ridge` becomes `\"gcv\"` with the floor at `>=0.5.0` (recurrence 0.7.0). "
    "Acceptance {measured}. "
    "Updated: Status line, W5.8 and W5.9 rows (both cells), P5 status row, the W5.8 (B) dependency row, a new Progress 2026-10-19 (turing W5.9 / W5.8 (B) session) block. "
    "Owed: the service PR's merge and recurrence 0.7.0 once 0.5.0 is on PyPI; W5.2, W5.4; W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.6.1 image. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service-pr", type=int, required=True, help="the juniper-recurrence PR number of the W5.8 (B) service half")
    ap.add_argument("--release", required=True, help="the model 0.5.0 release's state, e.g. 'Release juniper-recurrence-model-v0.5.0 cut, publish run NNN parked at the pypi gate'")
    ap.add_argument("--check", action="store_true", help="report which edits are applied / pending; write nothing")
    args = ap.parse_args()

    text = _PLAN.read_text(encoding="utf-8")
    pending: list[tuple[str, str]] = []
    done = 0
    for old, new in edits(args.service_pr, args.release):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))

    row = _CHANGELOG_ROW.format(model_pr=MODEL_PR, proposal_pr=PROPOSAL_PR, release=args.release, svc=f"juniper-recurrence#{args.service_pr}", measured=MEASURED)
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
    _PLAN.write_text(text, encoding="utf-8")
    print(f"applied {done + len(pending)} edits; change-log row {'added' if row_pending else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
