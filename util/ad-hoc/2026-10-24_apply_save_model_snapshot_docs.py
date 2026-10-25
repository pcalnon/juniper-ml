#!/usr/bin/env python3
"""Describe juniper-ml#2211's save_model snapshot path in CHANGELOG.md and the four docs that call it a re-fit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-24
Status: ad-hoc — one-off (the docs half of juniper-ml#2211; kept so a silent revert costs one re-run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/experiments/run_experiment.py _save_model_snapshot / _snapshots_dir;
         tests/test_recurrence_operation_identity_and_dataset_budget.py SaveModelSnapshotTest;
         util/ad-hoc/2026-10-21_apply_propose_readme_compat_changelog.py (the CHANGELOG insertion this reuses)

Why
---
``docs/REFERENCE.md``, ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``, ``docs/QUICK_START.md`` and
``docs/DOCUMENTATION_OVERVIEW.md`` say ``outputs.save_model`` re-runs the recurrence CLI. Since #2211 that is
the fallback for a train response without an ``operation_id``; the driver saves the scored model through
``POST /v1/model/snapshots``. ``CHANGELOG.md`` and ``docs/REFERENCE.md`` land from turing as whole files built
from a fresh ``origin/main`` copy, so every edit is anchored on text that must occur exactly once.

Usage
-----
    python3 util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py --root DIR [--check]

``--root`` is a tree holding the five files (default: this checkout). An edit already present is skipped, so a
re-run is a no-op. An anchor found zero times or more than once refuses the whole run before anything is
written. ``--check`` writes nothing and exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

CHANGELOG_MARKER = "- **`save_model` saves the recurrence model the run scored, instead of fitting a second one**"

CHANGELOG_ENTRY = """\
- **`save_model` saves the recurrence model the run scored, instead of fitting a second one** (juniper-ml#2211).
  `util/experiments/run_experiment.py` used to re-run the `juniper-recurrence train` CLI in a second process, for
  up to 600 s, and nothing proved that fit saw the run's data: a `dataset_id` does not pin content, and two mints
  of one `equities_seq` id 85 s apart differed (F-P8).
  - When `POST /v1/train` returns an `operation_id` (juniper-recurrence 0.6.0 and later; juniper-ml pins 0.8.0),
    the driver calls `POST /v1/model/snapshots` with it as `expect_operation_id`, so the service saves its
    in-memory model only if that operation produced it. The driver then copies `<snapshots_dir>/<id>.npz`
    (`recurrence_launch.snapshots_dir`, else `$RUN_DIR/snapshots`) to `artifacts/results/model.npz` and checks
    its size against the response's `size_bytes`.
  - A 409 (another caller trained or restored after this run's train) fails the phase (`degraded`, exit 1), and
    nothing re-fits a substitute. An unusable snapshot id or a size mismatch fails it too, and a copy the run
    cannot vouch for is removed. A snapshot this run cannot read is recorded with a note, not faked.
  - Only a train response without an `operation_id` (a pre-W1.5 service) still re-fits through the
    launcher-recorded CLI. The new `manifest.save_model` block names the path that ran: `source` is `snapshot`
    or `refit`.
  - `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/QUICK_START.md` and
    `docs/DOCUMENTATION_OVERVIEW.md` describe the snapshot path. Eight new tests in
    `tests/test_recurrence_operation_identity_and_dataset_budget.py`, all of which fail against `main`'s driver.
"""

#: (file, old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (
        "docs/REFERENCE.md",
        "`outputs.save_model: true` (G-18) re-runs the `juniper-recurrence train` CLI with `--dataset <dataset_id>` + identical hyperparam flags + `--out .../model.npz` as a manifest-recorded extra step (the CLI has no `--params` flag, so the dataset_id ref is the only faithful form).",
        "`outputs.save_model: true` (G-18) saves the model the run trained and scored (juniper-ml#2211): `POST /v1/model/snapshots` with the train response's `operation_id` as `expect_operation_id`, then a size-checked copy of `<snapshots_dir>/<id>.npz` to `.../model.npz`. A `409` (the service no longer holds this run's model) fails the phase, and nothing re-fits a substitute. Only a train response without an `operation_id` (a pre-W1.5 service) falls back to re-running the `juniper-recurrence train` CLI with `--dataset <dataset_id>` + identical hyperparam flags + `--out .../model.npz` (the CLI has no `--params` flag, so the dataset_id ref is the only faithful form); `manifest.save_model.source` names the path.",
    ),
    (
        "docs/REFERENCE.md",
        "a timed-out train and a busy 409 each leave a note in `manifest.operation`. No live services.",
        "a timed-out train and a busy 409 each leave a note in `manifest.operation`. `save_model` carries the same id on `POST /v1/model/snapshots` and copies the snapshot to `model.npz`, size-checked; a 409, an unusable id or a size mismatch fails the phase with no re-fit, a snapshot the run cannot see is recorded rather than faked, and only a train response without an id re-fits (juniper-ml#2211). No live services.",
    ),
    (
        "docs/REFERENCE.md",
        "The driver's `save_model` re-run executes `recurrence_launch.cli`.",
        "Since juniper-ml#2211 the driver's `save_model` saves the scored model through `POST /v1/model/snapshots` whenever `POST /v1/train` returned an `operation_id`, and copies it from `recurrence_launch.snapshots_dir` (`$RUN_DIR/snapshots` when the record has none) to `artifacts/results/model.npz`. `manifest.save_model` names the snapshot, the copy and its `sha256`, or says why no copy was made. The CLI re-run is the fallback for a service that returns no `operation_id`.\n\nThe driver's `save_model` re-run executes `recurrence_launch.cli`.",
    ),
    (
        "docs/REFERENCE.md",
        "jq '{outcome, phase: .phases.save_model, rerun: .save_model_rerun, launch: .ports.recurrence_launch}' \"$RUN_DIR/manifest.json\"",
        "jq '{outcome, phase: .phases.save_model, save: .save_model, rerun: .save_model_rerun, launch: .ports.recurrence_launch}' \"$RUN_DIR/manifest.json\"",
    ),
    (
        "docs/REFERENCE.md",
        "| `cli_source` is `path`, and another `juniper-recurrence` is earlier on `PATH` |",
        "| `save_model.source` is `snapshot` and `phases.save_model` is `ok` | The model the run scored was saved by identity, and `save_model.model_path` and `sha256` name the copy. No CLI ran, so the rows on `cli_source` and `parity` do not apply. |\n"
        "| `phases.save_model.error` starts `HTTP 409:` and names two operation ids | Another caller trained or restored after this run's train. Nothing was saved and nothing was re-fit (`degraded`, exit 1). |\n"
        "| `save_model.model_path` is `null` with a `note`, and the phase is `ok` | The service saved the snapshot where this run cannot read it: another host, or a staged `service.snapshots_dir`. |\n"
        "| `save_model.source` is `refit` | `POST /v1/train` returned no `operation_id` (a pre-W1.5 service), so the CLI re-fit ran; the rows below apply. |\n"
        "| `cli_source` is `path`, and another `juniper-recurrence` is earlier on `PATH` |",
    ),
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "Tip: `outputs.save_model: true` re-runs the `juniper-recurrence` CLI the launcher recorded (`ports.json` `recurrence_launch.cli`, W1.9), and only under rerun parity:",
        "Tip: `outputs.save_model: true` saves the recurrence model the run scored: `POST /v1/model/snapshots` with the train response's `operation_id` as `expect_operation_id`, copied to `model.npz` (juniper-ml#2211); a 409 is `outcome: degraded` (exit 1) with no re-fit. Only a service that returns no `operation_id` gets the old re-fit, which re-runs the `juniper-recurrence` CLI the launcher recorded (`ports.json` `recurrence_launch.cli`, W1.9), and only under rerun parity:",
    ),
    (
        "docs/QUICK_START.md",
        "-- `save_model` re-runs the launcher-recorded CLI under interpreter and model-version parity; per-run recurrence snapshots dir",
        "-- `save_model` saves the scored model by `operation_id` (a pre-W1.5 service re-runs the launcher-recorded CLI under interpreter and model-version parity instead); per-run recurrence snapshots dir",
    ),
    (
        "docs/DOCUMENTATION_OVERVIEW.md",
        "| **Read a recurrence `save_model` re-run** | [REFERENCE — Recurrence launch record and service env](REFERENCE.md#recurrence-launch-record-and-service-env) (launcher-recorded CLI under interpreter + model-version parity; a mismatch is `degraded`) |",
        "| **Read a recurrence `save_model` record** | [REFERENCE — Recurrence launch record and service env](REFERENCE.md#recurrence-launch-record-and-service-env) (the scored model saved by `operation_id`, or, for a pre-W1.5 service, the launcher-recorded CLI re-fit under interpreter + model-version parity; a 409 or a mismatch is `degraded`) |",
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
        site = f"{rel}: {old[:72]}..."
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
