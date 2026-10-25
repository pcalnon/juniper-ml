#!/usr/bin/env python3
"""Plan v1.7.17: juniper-ml 0.11.1 published, juniper-ml#2210 closed, the 0.8.0 smokes pass, and R-ML-SERVERS is unblocked.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.16 -> v1.7.17);
         util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py (the revision this follows);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.0, R-ML-SERVERS in §5)

Usage
-----
    python3 util/ad-hoc/2026-10-25_plan_v1_7_17_juniper_ml_0_11_1_published.py \
        [--servers-pr <N> [--servers-sha <8+ hex>]] [--plan PATH] [--check]

``--servers-pr`` is the R-ML-SERVERS ``[servers]`` floors PR and ``--servers-sha`` its squash merge. Without
``--servers-pr`` the PR is recorded as held by another session; without ``--servers-sha`` it is recorded as open.
``--plan`` points the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the
API); the default is the repo's own copy. Every anchor must match exactly once, or the script refuses and writes
nothing; ``--check`` reports what is applied / pending without writing.

Every fact below was re-probed on 2026-10-25 against PyPI, ``gh`` and the published wheels, not taken from the
handoff that asked for this revision.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

RECORD = (
    "juniper-ml 0.11.1 is on PyPI (2026-10-25 18:03Z). It carries juniper-ml#2314's `[tools]` security floors, "
    "`juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0`: the proposal juniper-ml#2319 merged as "
    "`d7a1908d`, the archive juniper-ml#2321 as `d64ffcec`, and the owner approved publish run 40178692483's `pypi` gate. "
    "Its notes rate it Medium (CWE-201, CWE-755, CWE-770), priority High. juniper-ml#2210 closed with juniper-ml#2320 "
    "(merged as `f7a1442d`, 18:12Z): `run_suite` refuses a `per_run_timeout_seconds` the driver's worst-case budget can "
    "outrun, and the nine recurrence suites carry 4500 s. Its docs edits were re-checked on `main` `3ebf0689` "
    "(`util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --check`, exit 0). juniper-cascor 0.12.0 (PyPI 2026-10-25 "
    "18:13Z; the owner approved run 38085392643's `pypi` gate) and juniper-data 0.17.1 (PyPI 2026-10-23 23:49Z) are "
    "served, which unblocks R-ML-SERVERS: the `[servers]` floors `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1`, "
    "then a 0.11.2 cut. SERVERS_STATE. The owner ruled on 2026-10-25 that this arc cuts 0.11.2 and stops at "
    "`PENDING_PYPI_APPROVAL`, with 0.11.1's rating (Medium; CWE-201, CWE-755, CWE-770; priority High), and that "
    "juniper-ml#2062's fix does not ride it. Measured on the published wheels, data 0.17.1 differs from 0.17.0 only "
    "in its version and its two floors (the builder's setuptools version aside), and both floors sit under its `[api]` "
    "extra. `[servers]` installs bare "
    "`juniper-data`, so a `[servers]` install gets the patches through cascor 0.12.0, whose floors are unconditional. "
    "The W1.12 and W1.11 smokes, owed on the 0.8.0 image since juniper-deploy#257, pass on juniper-deploy `main` "
    "`11aae789` (2026-10-25, Linux host), each image run by the digest GHCR serves for its tag and its revision label "
    "the commit of its release tag: the snapshot smoke 8/8 on recurrence 0.8.0 (`sha256:f3bc2a4c…`), and the canopy -> "
    "recurrence -> data smoke 3/3 on data 0.17.1, recurrence 0.8.0, canopy 0.9.0 and cascor 0.12.0. Both outputs are "
    "on juniper-deploy#258 (comment 6403282322). The consolidated plan records the arc to here at v1.15.0 (juniper-ml#2325, merged as `3ebf0689`), and the parent "
    "`Juniper/AGENTS.md` RELEASED paragraph was brought up to date on 2026-10-25: it names 0.11.1 as the latest release "
    "and both server releases as served"
)

NEXT_OLD = (
    "  - **Next**: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; the owner's, since that file is not on turing). "
    "juniper-ml#2210 is the next driver task: `per_run_timeout_seconds` against the summed driver budgets, where `save_model` is now one `max_wall`-bounded HTTP call on the "
    "snapshot path and the 600 s re-fit only for a pre-W1.5 service. A juniper-config-tools 0.2.0 cut (the owner's call) needs its `[Unreleased]` backfilled first. "
    "The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half "
    "and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open, and the next real recurrence run with `save_model` enabled is the "
    "snapshot path's first live exercise."
)

NEXT_NEW = (
    "  - **Next**: R-ML-SERVERS: SERVERS_NEXT the 0.11.2 cut, driven to `PENDING_PYPI_APPROVAL` with 0.11.1's rating, as the owner ruled; its `pypi` gate stays the "
    "owner's. juniper-ml#2062's fix (`[servers]` installs no client) gets its own PR and a later release. The juniper-recurrence-client 0.3.1 release "
    "(owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut); W5.7 changes a default, so whether a patch release may carry it is "
    "the owner's call too. A juniper-config-tools 0.2.0 cut (the owner's call) needs its `[Unreleased]` backfilled first. The W0.1 service-core half stays open, "
    "and the next real recurrence run with `save_model` enabled is the snapshot path's first live exercise."
)

_HEADLINE = "juniper-ml 0.11.1 published, juniper-ml#2210 closed, the 0.8.0 smokes pass; R-ML-SERVERS unblocked"
_STATUS_ANCHOR = "apply_save_model_snapshot_docs.py`)). The v1.4.0 plan edits follow that record"
_ROW_ANCHOR_START = "| 2026-10-24 | 1.7.16 | **save_model saves the scored model**:"
_SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")


def _servers(servers_pr: "str | None", servers_sha: "str | None") -> tuple[str, str, str]:
    """(SERVERS_STATE for the record, SERVERS_NEXT for the Next bullet, the revision row's owed prefix)."""
    if servers_pr is None:
        return (
            "Its floors PR is with another session, to which the owner assigned it (as that session relayed)",
            "the `[servers]` floors PR, which another session holds, and then",
            "the `[servers]` floors PR; ",
        )
    if servers_sha is None:
        return (f"Its floors PR is juniper-ml#{servers_pr}, open", f"juniper-ml#{servers_pr}, the `[servers]` floors PR, merges, and then", f"juniper-ml#{servers_pr}'s merge; ")
    return (
        f"Its floors landed as juniper-ml#{servers_pr} (merged as `{servers_sha}`)",
        f"the `[servers]` floors are on `main` (juniper-ml#{servers_pr}), so what remains is",
        "",
    )


def _record(servers_pr: "str | None", servers_sha: "str | None") -> str:
    return RECORD.replace("SERVERS_STATE", _servers(servers_pr, servers_sha)[0])


def edits(servers_pr: "str | None", servers_sha: "str | None") -> list[tuple[str, str]]:
    record = _record(servers_pr, servers_sha)
    next_new = NEXT_NEW.replace("SERVERS_NEXT", _servers(servers_pr, servers_sha)[1])
    return [
        ("- **Version**: 1.7.16", "- **Version**: 1.7.17"),
        # Status line: the v1.7.17 clause, after the v1.7.16 one.
        (_STATUS_ANCHOR, _STATUS_ANCHOR.replace("`)). The v1.4.0", f"`)); **{_HEADLINE}** (v1.7.17: {record}). The v1.4.0")),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (NEXT_OLD, f"  - **{_HEADLINE} (Linux host, 2026-10-25)**: {record}.\n{next_new}"),
    ]


def row(servers_pr: "str | None", servers_sha: "str | None") -> str:
    record = _record(servers_pr, servers_sha)
    owed_servers = _servers(servers_pr, servers_sha)[2]
    return (
        f"| 2026-10-25 | 1.7.17 | **{_HEADLINE}**: {record}. "
        "Updated: Status line, the Progress block (2026-10-25 bullet, Next rewritten). "
        f"Owed: {owed_servers}the 0.11.2 cut (owner-approved, to `PENDING_PYPI_APPROVAL`) and its `pypi` gate (owner); juniper-ml#2062 (its own PR); "
        "the client 0.3.1 release; juniper-data's next release (W5.7); "
        "juniper-config-tools 0.2.0 (owner); W0.1's service-core half; the first live exercise of `save_model`'s snapshot path. | Paul Calnon |\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--servers-pr", help="the R-ML-SERVERS [servers] floors PR number, once it is open")
    ap.add_argument("--servers-sha", help="that PR's squash-merge sha (8 or more hex), once it has landed")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    if args.servers_sha and not args.servers_pr:
        raise SystemExit("ERROR: --servers-sha needs --servers-pr")
    if args.servers_pr and not args.servers_pr.isdigit():
        raise SystemExit(f"ERROR: --servers-pr must be a PR number, got {args.servers_pr!r}")
    if args.servers_sha and not _SHA_RE.match(args.servers_sha):
        raise SystemExit(f"ERROR: --servers-sha must be 8 to 40 lowercase hex, got {args.servers_sha!r}")
    facts = (args.servers_pr, args.servers_sha[:8] if args.servers_sha else None)
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(*facts):
        # `new` contains `old` for the Status-line clause, so "new present" is the test.
        if new in text:
            print(f"  = already applied: {old[:70]!r}")
            continue
        if text.count(old) != 1:
            raise SystemExit(f"ERROR: expected exactly one occurrence of {old[:90]!r}, found {text.count(old)}")
        pending += 1
        if not args.check:
            text = text.replace(old, new, 1)
            print(f"  + applied: {old[:70]!r}")
        else:
            print(f"  ~ WOULD apply: {old[:70]!r}")

    if "| 2026-10-25 | 1.7.17 |" in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.16 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row(*facts) + text[end:]
            print("  + revision row added after v1.7.16")
        else:
            print("  ~ WOULD add the revision row after v1.7.16")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
