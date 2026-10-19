#!/usr/bin/env python3
"""Plan v1.7.4: record that W5.10 landed (juniper-recurrence#208) and the W5.9 contract it set.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.3 -> v1.7.4);
         juniper-recurrence#208 (W5.10); util/ad-hoc/2026-10-19_plan_v1_7_3_compose_pin_followed.py (the revision this follows,
         a concurrent session's -- it claimed 1.7.3 first, so this one is 1.7.4)

Why this exists
---------------
Concurrent sessions edit the plan, so a revision is applied as exact-string edits that each must match once,
re-runnable after a fast-forward. The merge SHA is a parameter because the script is written before the merge.

Usage
-----
    python3 util/ad-hoc/2026-10-18_plan_v1_7_4_w5_10_landed.py --merge-sha <8+ hex> [--check]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_FIELDS = "`readout`, `theta` (the data-driven value a `theta=None` request became, per fold), `ridge_mode` / `ridge_selected` (the λ GCV chose), `gamma` (the median-heuristic RFF bandwidth) and the `gcv_at_edge` / `null_model` flags"
_CONTRACT = "the fitted readout exposes `gcv_at_edge_` and `null_model_` (trailing-underscore fit diagnostics, as the MLP rung's `n_epochs_` / `stopped_reason_`), which `juniper_recurrence._readout.readout_diagnostics` reads in preference to its own derivation; until the model sets them the service derives `gcv_at_edge` from the grid bounds and reports `null_model: null` (*not determined*, never *false*)"


def edits(sha: str) -> list[tuple[str, str]]:
    pr = f"juniper-recurrence#208, `{sha}`"
    return [
        ("- **Version**: 1.7.3", "- **Version**: 1.7.4"),
        # Status line.
        (
            "(v1.7.3: juniper-deploy#251, `b645acfd`, ruled and merged 2026-10-19 UTC; **every M1 landing is on `main`**).",
            f"(v1.7.3: juniper-deploy#251, `b645acfd`, ruled and merged 2026-10-19 UTC; **every M1 landing is on `main`**); **P5 started — W5.10 landed** (v1.7.4: {pr}, 2026-10-18; `POST /v1/train` and every fold of `POST /v1/crossval` carry a `diagnostics` block with {_FIELDS}; in `[Unreleased]`, ships in the next 0.6.x).",
        ),
        # W5.10 work-item row: header cell and acceptance cell.
        (
            "| W5.10 | F-S7 (response half); **proposed 2026-10-05; accepted 2026-10-18** (first in the order of work; may ship in a 0.6.x ahead of W5.8) | juniper-recurrence |",
            f"| W5.10 | F-S7 (response half); **proposed 2026-10-05; accepted 2026-10-18; landed 2026-10-18** ({pr}; in `[Unreleased]`, ships in the next 0.6.x ahead of W5.8) | juniper-recurrence |",
        ),
        (
            "| Route test: the E-H crossval response carries the per-fold diagnostics; schema test. | S |",
            "| Route test: the E-H crossval response carries the per-fold diagnostics; schema test. **Done**: `juniper-recurrence/tests/test_readout_diagnostics.py` (21 tests, 23 cases) pins the block on both routes, the status re-serve, the OpenAPI schema and the `train` CLI on the suite's synthetic artifact, end to end through the real fold executor; the first E-H run after the merge is the live check. | S |",
        ),
        # W5.9 row: the attribute contract W5.10 set.
        (
            "Detect and report an at-ceiling / null-model selection (model WARNING plus a flag the response can carry via W5.10); do not extend the grid. |",
            f"Detect and report an at-ceiling / null-model selection (model WARNING plus a flag the response can carry via W5.10); do not extend the grid. **Contract set by W5.10 (2026-10-18)**: {_CONTRACT}. |",
        ),
        # P5 status row.
        (
            "| **P5** | Safe service default and per-fold diagnostics: W5.10 first, then W5.8 (B) + W5.9; W5.11 declined | Accepted 2026-10-18 (owner ruling); not started | 5 | recurrence 0.7.0, model 0.5.0 |",
            f"| **P5** | Safe service default and per-fold diagnostics: W5.10 first, then W5.8 (B) + W5.9; W5.11 declined | In Progress — **W5.10 Done** ({pr}, 2026-10-18; in `[Unreleased]`); W5.8 (B) + W5.9 next | 5 | W5.10 in the next recurrence 0.6.x; W5.8 (B) + W5.9 in recurrence 0.7.0, model 0.5.0 |",
        ),
        # Dependency row: W5.8 (B) is unblocked.
        (
            "**Ruled 2026-10-18**: recurrence 0.7.0 / model 0.5.0, CHANGELOG \"Changed\" with the measured numbers; W5.10 may ship earlier in a 0.6.x if it is ready first |",
            f"**Ruled 2026-10-18**: recurrence 0.7.0 / model 0.5.0, CHANGELOG \"Changed\" with the measured numbers; W5.10 may ship earlier in a 0.6.x if it is ready first. **W5.10 landed 2026-10-18** ({pr}): the response announces the selected λ, so W5.8 (B) is unblocked |",
        ),
        # Progress: a new 2026-10-18 block after the deploy-smokes session's.
        (
            "(canopy 0.9.x work; this arc only annotates).\n",
            "(canopy 0.9.x work; this arc only annotates).\n"
            "\n"
            "  **Progress 2026-10-18, turing W5.10 session** (every commit through the GitHub-signed API path):\n"
            f"  - **W5.10 landed**: {pr}. `juniper_recurrence._readout.readout_diagnostics(model)` reads a fitted model's resolved hyperparameters once, for both routes and the CLI; the crossval route keeps each fold's model at the factory seam (the executor's `FoldResult` carries metrics only) and reads the block off it after the run; `AppState.set_crossval` / `crossval_status` carry the per-fold blocks so the status route re-serves them; `TrainResponse` and `CrossValFoldModel` gain a required `diagnostics: ReadoutDiagnostics`. Additive on the wire; the model package is unchanged; no number changes. Suite on turing: 339 passed, coverage 98.29 % (gate 90 %); ruff clean.\n"
            f"  - **W5.9's contract set**: {_CONTRACT}.\n"
            "  - **Not run here**: the E-H crossval itself (no juniper-data on turing); the suite's synthetic artifact pins the contract end to end through the real fold executor and `LMURegressor`.\n"
            "  - **Next**: W5.8 (B) + W5.9 for recurrence 0.7.0 / model 0.5.0; W5.2 and W5.4; W5.7. The W0.1 service-core half and the parent `Juniper/AGENTS.md` paragraph stay open (the Compose pin followed in juniper-deploy#251, v1.7.3).\n",
        ),
    ]


#: The 1.7.3 row's tail (juniper-ml#2246): the 1.7.4 row goes right after it.
_ROW_ANCHOR = "the owner's W0.1 service-core half and the parent AGENTS.md paragraph; the open follow-ups. | Paul Calnon |\n"

_CHANGELOG_ROW = (
    "| 2026-10-19 | 1.7.4 | **W5.10 landed** ({pr}; merged 2026-10-19 00:50Z; the owner's 2026-10-18 acceptance, first in the P5 order of work). "
    "`POST /v1/train` and every fold of `POST /v1/crossval` carry a `diagnostics` block ({fields}); `GET /v1/crossval/status` re-serves it; the `train` CLI prints it. "
    "Read off the fitted model after the solve, changes no number, additive on the wire; in `[Unreleased]`, ships in the next 0.6.x. "
    "W5.9's attribute contract recorded (`gcv_at_edge_` / `null_model_` on the fitted readout). "
    "Updated: Status line, W5.10 row (both cells), W5.9 row, P5 status row, the W5.8 (B) dependency row, a new Progress 2026-10-18 (turing W5.10 session) block. "
    "Owed: W5.8 (B) + W5.9 (recurrence 0.7.0 / model 0.5.0); W5.2, W5.4; W5.7; W0.1's service-core half; the parent AGENTS.md paragraph. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-sha", required=True, help="the squash-merge SHA of juniper-recurrence#208 (8+ hex)")
    ap.add_argument("--check", action="store_true", help="report which edits are applied / pending; write nothing")
    args = ap.parse_args()
    sha = args.merge_sha.strip()
    if not re.fullmatch(r"[0-9a-f]{8,40}", sha):
        print(f"REFUSED: --merge-sha must be 8+ lowercase hex, got {sha!r}")
        return 2
    sha = sha[:8]

    text = _PLAN.read_text(encoding="utf-8")
    pending: list[tuple[str, str]] = []
    done = 0
    for old, new in edits(sha):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))

    row = _CHANGELOG_ROW.format(pr=f"juniper-recurrence#208, `{sha}`", fields=_FIELDS)
    row_pending = row not in text
    if row_pending:
        anchor = _ROW_ANCHOR
        i = text.rfind(anchor)
        if i < 0 or text.count(anchor) != 1:
            print(f"REFUSED: change-log anchor matched {text.count(anchor)} times (expected 1)")
            return 1

    if args.check:
        print(f"applied {done}, pending {len(pending)}, change-log row {'pending' if row_pending else 'present'}")
        return 0 if not pending and not row_pending else 1

    for old, new in pending:
        text = text.replace(old, new, 1)
    if row_pending:
        anchor = _ROW_ANCHOR
        i = text.index(anchor) + len(anchor)
        text = text[:i] + row + text[i:]
    _PLAN.write_text(text, encoding="utf-8")
    print(f"applied {len(pending)} edits (+ change-log row: {row_pending}); {done} were already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
