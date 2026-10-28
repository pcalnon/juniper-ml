#!/usr/bin/env python3
"""Plan v1.7.23: juniper-recurrence-client 0.3.1 is published, and the arc's follow-ups of 2026-10-26/27 are closed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-27
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.22 -> v1.7.23);
         util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py (the consolidated plan's matching revision);
         util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py (the wheel probe the record cites)

Why
---
v1.7.22's **Next** named the juniper-recurrence-client 0.3.1 cut and the 0.11.2 erratum as open. Session "recurrence
equities 2" (2026-10-26/27) cut the client up to its `pypi` gate and closed juniper-deploy#250 and juniper-canopy#735-#737;
session "draft PRs" made the erratum; and the owner approved the client's gate on 2026-10-27. Its handoff,
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_recurrence-equities-followups-closed-client-0-3-1-at-pypi-gate.md``,
left both plans unrevised. Every merge below was re-probed here (``gh pr view``), the publish against PyPI's and
TestPyPI's version JSON and the run's jobs and approvals, and the wheel with the probe named above. The 8/8 smoke results,
the owner's acceptance of canopy#776's behaviour change and `detect.py`'s 0.4.0 are that session's record, as marked.

The Status line takes a summary (``STATUS_RECORD``); the Progress bullet and the revision row take the whole record
(``RECORD``). W1.2's and W1.12's status rows, the turing deploy-smokes note and the juniper-ml#2227 ruling note each get their closure appended; nothing
already written is rewritten except the head of **Next**, as in v1.7.22.

Usage
-----
    python3 util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py [--plan PATH] [--check]

``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every anchor must match exactly
once, or the script refuses and writes nothing. ``--check`` reports what is applied / pending without writing, and
exits 1 while an edit is owed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "juniper-recurrence-client 0.3.1 published; the arc's follow-ups closed"

_CLIENT = (
    "**juniper-recurrence-client 0.3.1 is published.** The proposal juniper-recurrence#227 merged as `717f2a80` "
    "(`util/release_train/detect.py` proposed 0.4.0, from the repo-wide `feat` confound, and the manifest's "
    "`proposed_version` override made it 0.3.1, as that session records). Release `juniper-recurrence-client-v0.3.1` was "
    "published at 2026-10-26 23:10:24Z with its tag at `717f2a80`, and its archive juniper-ml#2367 merged as `edcbb024`. "
    "The owner approved the `pypi` gate of publish run 40417898021, and `Publish to PyPI` succeeded at 2026-10-27 "
    "10:20:22Z. `https://pypi.org/pypi/juniper-recurrence-client/0.3.1/json` serves the wheel (10:20:18Z) and the sdist "
    "(10:20:20Z), each with the sha256 TestPyPI took at 2026-10-26 23:21Z, and the same `requires_dist`. "
    "`util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py`, run on that wheel installed from PyPI "
    "against a stub server, passes: `crossval` called without `embargo` sends no `embargo` key, so recurrence 0.8.0's "
    "look-back default (W5.2) applies, and `embargo=0` and `embargo=7` are sent as given. The 0.3.0 control fails, "
    "because it sends `embargo: 0`. "
)
_FOLLOWUPS = (
    "**The follow-ups are closed.** juniper-deploy#264 (merged as `0d9c71f6`) fixes juniper-deploy#250: "
    "`scripts/test_recurrence_snapshots.sh` pulls an image it does not have (three attempts), stops with exit 2 on one it "
    "can neither find nor pull, and passes `--no-build` to both `up` calls (8/8 on the local-image path and on the pull "
    "path, as that session records; still so on deploy `main` after juniper-deploy#263, re-read here). "
    "juniper-canopy#776 (merged as `c7846b4e`) closes juniper-canopy#735 and #736: the cascor staging path for flat "
    "`equities` gets W1.2's declared-param filter, from a declaration captured from the published juniper-data 0.17.1 "
    "wheel, and the restart modal renders and re-stages its typed dataset fields per type: all four for spiral, none for "
    "flat `equities` or a sequence generator, and Samples and Noise for the other rank-2 types. It keeps the "
    "owner's ruling of 2026-09-22 that Confirm re-stages exactly what the modal displays, and fixes a breach of it: an "
    "untouched Confirm after the `enabled[0]` swap re-staged nothing. The owner accepted that behaviour change (that "
    "session's record). juniper-cascor#729 (`5b7d10dc`) corrects the comment in "
    "`TrainingLifecycleManager._translate_staged_config` (flat `equities` declares neither `n_samples` nor `noise`) and "
    "leaves the translation alone, so no `dataset_id` moves. juniper-canopy#777 (merged as `33619d6d`) closes "
    "juniper-canopy#737: `util/check_juniper_data_generator_schemas.py` and the `juniper-data Schema Drift` workflow "
    "(daily at 07:17Z, and on `repository_dispatch` `juniper-data-published`) compare canopy's committed generator "
    "snapshots with the latest juniper-data on PyPI. Its first `workflow_dispatch` on `main` (run 40430795877) and its "
    "first scheduled run (run 40468348513, 2026-10-27) found no drift against 0.17.1. Neither canopy PR is in a canopy "
    "release yet: PyPI's latest canopy is 0.9.0. "
)
_RULINGS = (
    "**The owner's rulings of 2026-10-26 are carried out.** The release-train archive cap `ARCHIVE_B64_MAX_DEFAULT` is "
    "1,000,000 B (juniper-ml#2364, `ecc05079`), after a GitHub-hosted runner accepted every GraphQL body it tried, 12 "
    "sizes from 100,000 B to 16,777,216 B (run 40410086979; `reports/2026-10-26_graphql-body-cap-probe/`). The false "
    "`succeeded` row of run "
    "`20261003T091414Z-4ba6` in `~/.local/state/juniper-experiments/index.jsonl` (line 477) is annotated by an appended "
    "correction row (line 482). That row records `degraded`, the outcome today's driver "
    "(`util/experiments/run_experiment.py`) assigns to such a run (train and predict succeeded; crossval failed with a "
    "422 on `X_full`), where the owner's option, as that session records, named `failed`. The 0.11.2 "
    "erratum was made by session \"draft PRs\": juniper-ml#2362 (`682e72fb`; the v0.11.2 notes, with a v0.11.3 "
    "clarification), #2363 (`40815bb4`; `CHANGELOG.md`) and both Release bodies (v0.11.2 and v0.11.3, edited 2026-10-26 "
    "22:25:54Z and 22:25:55Z). "
)
_OUTSIDE = (
    "**Also landed, outside this arc**: juniper-ml#2369 (`8467225b`; APD-ML-002's cascor train / val half, under the owner's four "
    "rulings of 2026-10-26) makes a NaN or infinite value fail every W5.4 acceptance band. Before it, NaN passed every "
    "band, `+inf` a `min` band and `-inf` a `max` band. "
)
_CONSOLIDATED = (
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` records the publish, the follow-ups, the "
    "rulings and the erratum (v1.15.5)"
)

RECORD = _CLIENT + _FOLLOWUPS + _RULINGS + _OUTSIDE + _CONSOLIDATED

STATUS_RECORD = (
    "juniper-recurrence-client 0.3.1 is on PyPI from 2026-10-27 10:20Z (publish run 40417898021, its `pypi` gate approved "
    "by the owner), and its wheel, probed from PyPI against a failing 0.3.0 control, no longer sends `embargo: 0`; "
    "juniper-deploy#250 and juniper-canopy#735–#737 are closed (juniper-deploy#264; juniper-canopy#776 and #777), and "
    "juniper-cascor#729 corrects cascor's staging comment; the owner's rulings of 2026-10-26 on the archive cap (juniper-ml#2364) and the false "
    "`succeeded` index row are carried out, and the 0.11.2 erratum is made (juniper-ml#2362, #2363); juniper-ml#2369 "
    "makes a non-finite value fail every W5.4 band. " + _CONSOLIDATED
)

_STATUS_ANCHOR = "records the same publish (v1.15.4)). The v1.4.0 plan edits follow that record"

NEXT_OLD = (
    "  - **Next**: whether 0.11.2's notes take an erratum for the patch path is the owner's call (v1.7.21). The "
    "juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries "
    "W5.7 (owner's cut); W5.7 changes a default, so whether a patch release may carry it is the owner's call too. A "
    "juniper-config-tools 0.2.0 cut (the owner's call) needs its `[Unreleased]` backfilled first. The W0.1 service-core "
    "half stays open, and the next real recurrence run with `save_model` enabled is the snapshot path's first live "
    "exercise."
)
NEXT_NEW = (
    "  - **Next**: juniper-data's next release carries W5.7 (the owner's cut; R-DATA-2 in "
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §5, which names 0.17.2); W5.7 changes a default, so whether a "
    "patch release may carry it is the owner's call too. That release turns juniper-canopy#777's drift job red, because "
    "juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`: re-capture both snapshots "
    "then (the job prints the commands). Adding juniper-canopy to juniper-data's `notify-consumers.yml` matrix is the "
    "owner's (the diff is in juniper-canopy#777's body; only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers "
    "canopy), and once that change merges, a `workflow_dispatch` with version `0.17.1` settles it. Whether the `index.jsonl` "
    "correction row should say `failed` rather than `degraded` is the owner's to say. A juniper-config-tools 0.2.0 cut "
    "(the owner's call) needs its `[Unreleased]` backfilled first. The W0.1 service-core half stays open, and the next "
    "real recurrence run with `save_model` enabled is the snapshot path's first live exercise; it waits on W0.1, since "
    "`util/recurrence_env_preflight.bash` still refuses `JuniperCascor1` (2 findings, re-run 2026-10-27). Left out of "
    "juniper-canopy#776: the restart modal still shows Noise for `mnist`, which does not declare it, and its training "
    "fields are still cascor-only and shown under recurrence."
)

W12_OLD = "CI does not notice juniper-data param drift (the preview and a Start WARNING do) | 1 | canopy 0.9.0 |"
W12_NEW = (
    "CI does not notice juniper-data param drift (the preview and a Start WARNING do). **All three closed** (v1.7.23): "
    "juniper-canopy#776 (`c7846b4e`, 2026-10-27; #735, #736) makes the restart modal render and re-stage its typed fields "
    "per type (none for a sequence generator or flat `equities`) and gives flat `equities` on the cascor path the "
    "declared-param filter; juniper-canopy#777 (`33619d6d`; #737) adds a daily drift check against juniper-data on PyPI. "
    "Neither is in a canopy release yet | 1 | canopy 0.9.0 |"
)

W112_OLD = "so a fresh clone passes the preflight) | 1 | juniper-deploy |"
W112_NEW = (
    "so a fresh clone passes the preflight). Since juniper-deploy#264 (2026-10-26; juniper-deploy#250) the smoke pulls "
    "an image it does not have and never builds one (v1.7.23) | 1 | juniper-deploy |"
)

RULING_2227_OLD = "re-archive canopy 0.9.0's full notes in place of the condensed file (juniper-ml#2234)."
RULING_2227_NEW = (
    "re-archive canopy 0.9.0's full notes in place of the condensed file (juniper-ml#2234). **The runner-side "
    "measurement ran on 2026-10-26** (run 40410086979 accepted every body it tried, up to 16,777,216 B), and "
    "juniper-ml#2364 raised the default to 1,000,000 B by the owner's ruling of that day (v1.7.23)."
)

TURING_OLD = "beside a worktree; juniper-deploy#250)"
TURING_NEW = (
    "beside a worktree; juniper-deploy#250, fixed by juniper-deploy#264 on 2026-10-26: the smoke now pulls a missing "
    "image itself and never builds one)"
)

_ROW_ANCHOR_START = "| 2026-10-26 | 1.7.22 | **juniper-ml 0.11.3 published**:"
_ROW_START = "| 2026-10-27 | 1.7.23 | "
_ROW_UPDATED = (
    "Updated: Status line (a summary of this record), the Progress block (a session bullet before **Next**, and **Next** "
    "rewritten), W1.2's and W1.12's status rows, the turing deploy-smokes note and the juniper-ml#2227 ruling note (each closure appended). | Paul Calnon |"
)


def edits() -> list[tuple[str, str]]:
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-26/27)**: {RECORD}.\n"
    status_new = _STATUS_ANCHOR.replace("(v1.15.4)). The v1.4.0", f"(v1.15.4)); **{_HEADLINE}** (v1.7.23: {STATUS_RECORD}). The v1.4.0")
    return [
        ("- **Version**: 1.7.22", "- **Version**: 1.7.23"),
        (_STATUS_ANCHOR, status_new),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (NEXT_OLD, bullet + NEXT_NEW),
        (W12_OLD, W12_NEW),
        (W112_OLD, W112_NEW),
        (TURING_OLD, TURING_NEW),
        (RULING_2227_OLD, RULING_2227_NEW),
    ]


def row() -> str:
    return f"{_ROW_START}**{_HEADLINE}**: {RECORD}. {_ROW_UPDATED}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's own copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()

    for text_piece in (RECORD, STATUS_RECORD, NEXT_NEW, W12_NEW, W112_NEW, TURING_NEW, RULING_2227_NEW):
        if "|" in text_piece.replace(" | 1 | canopy 0.9.0 |", "").replace(" | 1 | juniper-deploy |", "") or "\n" in text_piece:
            raise SystemExit(f"ERROR: a record text carries a table pipe or a newline: {text_piece[:90]!r}")

    text = args.plan.read_text(encoding="utf-8")
    original = text
    owed = 0
    for old, new in edits():
        # ``new`` may contain ``old`` (the juniper-ml#2227 note is appended after its anchor), so applied means every
        # ``old`` sits inside a ``new`` -- v1.7.22's ``old not in text`` would re-apply such an edit on every run.
        if new in text and text.count(old) <= text.count(new):
            print(f"  = already applied: {new[:80]!r}")
            continue
        if text.count(old) != 1:
            raise SystemExit(f"ERROR: expected exactly one occurrence of {old[:90]!r}, found {text.count(old)}")
        owed += 1
        print(f"  {'~ WOULD apply' if args.check else '+ applied'}: {old[:80]!r}")
        text = text.replace(old, new, 1)

    if _ROW_START in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.22 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row() + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.22")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
