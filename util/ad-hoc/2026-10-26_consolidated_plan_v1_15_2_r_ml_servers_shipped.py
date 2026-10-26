#!/usr/bin/env python3
"""Consolidated development plan v1.15.1 -> v1.15.2: juniper-ml 0.11.2 ships R-ML-SERVERS; ml#2330 ruled, fixed by ml#2345.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2339 (the 0.11.2 proposal, e8d38732), #2341 (its archive), publish run 40247789317;
         juniper-ml#2330 and its fix juniper-ml#2345;
         util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py (the recurrence plan's matching revision)

Why
---
v1.15.1 lists R-ML-SERVERS as the next cut and ml#2330 as an open question. On 2026-10-26 the owner approved
0.11.2's ``pypi`` gate, so R-ML-SERVERS shipped, and chose ml#2330's option 1 (in a turing session; relayed), whose fix
is ml#2345. The owner approved this revision on 2026-10-26, on the condition that every line stays within 512
characters. v1.15.1 left three lines over that (XC-P12's bullet, P12's milestone row and the R-ML-SERVERS row); this
revision rewrites all three, so the whole plan is back under the limit, and the script refuses if any line is over.

Usage
-----
    python3 util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py [--fix-sha <8+ hex>] [--root DIR] [--check]

``--fix-sha`` is ml#2345's squash merge; without it ml#2345 is recorded as open and armed. An edit already present is
skipped, so a re-run is a no-op. An anchor found zero times or more than once, or a line over 512 characters after
the edits, refuses the whole run before anything is written. ``--check`` writes nothing and exits 1 while an edit is
pending.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512
_SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")

# v1.15.1's three lines over 512 characters, each replaced whole.
_XC_P12_OLD = (
    "- **juniper-ml 0.11.0 and 0.11.1** carry the meta-package's floors (2026-10-21, 2026-10-25; §5). The driver follow-ups filed on 2026-10-10 merged: ml#2211 as ml#2316, and ml#2210 as ml#2320. ml#2316's post-merge re-check passed on `main` `899796d2`. "
    "ml#2320 (`f7a1442d`, 2026-10-25T18:12Z; v1.15.1) makes `run_suite` refuse a suite, before its first `--up`, whose `per_run_timeout_seconds` does not exceed a cell's worst-case driver budget. "
    "The driver's `worst_case_budget` sums the health waits, dataset creation, every wall-bounded phase and `save_model`, or cascor's teardown settle and `snapshot_at_end`. "
    "The nine recurrence suites, at 3900 s against 1200–1800, now carry 4500; the 20 cascor suites already cleared theirs. "
    "Its post-merge re-check passed on `main` `c86a5e5e`, four merges later. Its out-of-scope finding, E-C's wall budget, is ml#2330 (§6 Group C).\n"
)
_XC_P12_NEW = (
    "- **juniper-ml 0.11.0, 0.11.1 and 0.11.2** carry the meta-package's floors (2026-10-21, 2026-10-25 and 2026-10-26; §5). The driver follow-ups filed on 2026-10-10 merged: ml#2211 as ml#2316, and ml#2210 as ml#2320. ml#2316's post-merge re-check passed on `main` `899796d2`.\n"
    "  ml#2320 (`f7a1442d`, 2026-10-25T18:12Z; v1.15.1) makes `run_suite` refuse a suite, before its first `--up`, whose `per_run_timeout_seconds` does not exceed a cell's worst-case driver budget. "
    "The driver's `worst_case_budget` sums the health waits, dataset creation, every wall-bounded phase and `save_model`, or cascor's teardown settle and `snapshot_at_end`.\n"
    "  The nine recurrence suites, at 3900 s against 1200–1800, now carry 4500; the 20 cascor suites already cleared theirs. "
    "Its post-merge re-check passed on `main` `c86a5e5e`, four merges later. Its out-of-scope finding, E-C's wall budget, is ml#2330 (§6 Group C).\n"
    "  The owner chose ml#2330's option 1 on 2026-10-26 (v1.15.2). ml#2345 (FIX_STATE) sets E-C's `execution.max_wall_seconds` to 5400, so its worst-case driver budget is 5,850 s against a 7,200 s `per_run_timeout_seconds`; its cell ids and `config_sha256` are unchanged, and a CI test pins both bounds.\n"
)

_P12_ROW_OLD = (
    "| P12 equities | M0 closes on its date (10-24); W0.1's service-core half is an owner follow-up · Phase 1 done (10-17) → M1 (11-21; the W1.11/W1.12 smokes owed on 0.8.0) · W1.1b not commissioned · W5.4 done · "
    "R-ML-SERVERS's floors merged (ml#2326) · next: the juniper-ml 0.11.2 cut (owner ruling 2026-10-25) | "
    "The F-S10 data-client patch comes from a `v0.5.0` branch (§5) and is forward-ported to `main` for a 0.6.x patch (0.6.0 was cut without it). "
    "Annotate the false `succeeded` row (`20261003T091414Z-4ba6`) in `~/.local/state/juniper-experiments/index.jsonl` (residue) |\n"
)
_P12_ROW_NEW = (
    "| P12 equities | M0 closes on its date (10-24); W0.1's service-core half: owner · Phase 1 done (10-17) → M1 (11-21; W1.11/W1.12 smokes passed on 0.8.0, 10-25) · W1.1b not commissioned · W5.4 done · "
    "R-ML-SERVERS shipped (juniper-ml 0.11.2, 10-26) | "
    "The F-S10 data-client patch comes from a `v0.5.0` branch (§5) and is forward-ported to `main` for a 0.6.x patch (0.6.0 was cut without it). "
    "Annotate the false `succeeded` row (`20261003T091414Z-4ba6`) in `~/.local/state/juniper-experiments/index.jsonl` (residue) |\n"
)

_SERVERS_ROW_OLD = (
    "| **R-ML-SERVERS** (floors merged as ml#2326, `f823b0b7`; the cut is juniper-ml **0.11.2** by the owner's ruling of 2026-10-25, over `detect.py`'s 0.12.0; v1.15.1): a juniper-ml patch | "
    "The `[servers]` floors `juniper-data>=0.17.1` and `juniper-cascor>=0.12.0`, which floor the shared security patches; ml#2062's fix if it is ready (ml#2333, open on 2026-10-25) | "
    "Both on PyPI (met: data 2026-10-23, cascor 2026-10-25). The floors PR first, pre-flighted for `[servers]` and `[all]` against real PyPI; then the owner's cut, gate and rating | "
    "`[servers]` and `[all]` users whose upgrade keeps data 0.17.0 or cascor 0.11.0 |\n"
)
_SERVERS_ROW_NEW = (
    "| **R-ML-SERVERS** (shipped as juniper-ml 0.11.2, 2026-10-26; note below) | "
    "The `[servers]` floors `juniper-data>=0.17.1` and `juniper-cascor>=0.12.0` (ml#2326), which floor the shared security patches. Rated as 0.11.1 (owner, 2026-10-25) | "
    "Both on PyPI (met: data 2026-10-23, cascor 2026-10-25); proposal ml#2339, archive ml#2341; the owner approved the gate (run 40247789317) | "
    "`[servers]` and `[all]` users whose upgrade kept data 0.17.0 or cascor 0.11.0 |\n"
)

# Multi-line texts are bound to names here rather than written inside the REPLACEMENTS display: adjacent literals inside
# a list or tuple trip CodeQL's py/implicit-string-concatenation-in-list, whose unresolved thread blocks a merge.
_STATUS_ANCHOR = "over the 0.12.0 that `util/release_train/detect.py` proposes (§5). Like v1.15.0, no round checks it.\n"
_STATUS_ADD = "  - v1.15.2 (2026-10-26) records juniper-ml 0.11.2's publish, which ships R-ML-SERVERS (§5), and the owner's ruling on ml#2330 with its fix, ml#2345 (XC-P12; §6 Group C). Like v1.15.0, no round checks it.\n"

_FURTHER_P12_OLD = "Further P12 work follows `…0-11-1-published-servers-floors-next.md`: the juniper-ml 0.11.2 cut (§5; R-ML-SERVERS's floors merged as ml#2326; v1.15.1), the recurrence-client 0.3.1 cut, the W1.11 and W1.12 smokes on the 0.8.0 image, and the owner's open items (§6 A1, A9)."
_FURTHER_P12_NEW = (
    "Further P12 work follows the **Next** bullet of `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.20): the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9). "
    "The juniper-ml 0.11.2 cut is done (R-ML-SERVERS; v1.15.2), and the W1.11 and W1.12 smokes passed on the 0.8.0 image (2026-10-25; that plan's v1.7.17)."
)

_RML_NOTES_OLD = "R-ML-TOOLS followed as 0.11.1 (2026-10-25).\n- There is still no forward-port"
_RML_NOTES_NEW = (
    "R-ML-TOOLS followed as 0.11.1 (2026-10-25), and R-ML-SERVERS as 0.11.2 (2026-10-26).\n"
    "- R-ML-SERVERS shipped in 0.11.2 under the owner's ruling of 2026-10-25 (`detect.py` proposed 0.12.0), with ml#2062's fix (ml#2333) left out. PyPI's 0.11.2 metadata carries both floors under `extra == \"servers\"`, and the published `[servers]` and `[all]` resolve against real PyPI in 62 and 96 packages (2026-10-26). `[servers]` still installs no Juniper client (ml#2062).\n"
    "- There is still no forward-port"
)

_VALIDATION_ANCHOR = "its facts cite those PRs and `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py`.\n"
_VALIDATION_ADD = "  - v1.15.2 is a record of juniper-ml 0.11.2's publish (2026-10-26), which ships R-ML-SERVERS, and of ml#2330's ruling and its fix, ml#2345. No round checks it (owner ruling 2026-10-24); its facts cite PyPI's 0.11.2 metadata, publish run 40247789317, ml#2345's diff and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`.\n"

_SCRIPTS_ANCHOR = "then, with v1.15.0's PR, `2026-10-25_p12_arc_state_reprobe.py` and `2026-10-25_consolidated_plan_v1_15_0_p12_arc.py`;\n"
_SCRIPTS_ADD = "    - with v1.15.1's PR, `2026-10-25_consolidated_plan_v1_15_1_session_record.py`; and with v1.15.2's, `2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`;\n"

_MEMORY_ANCHOR = "  - by session `2988c32a` (2026-10-25), with v1.15.0: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"
_MEMORY_ADD = "  - by session `53dbcc4b` (2026-10-26), with v1.15.2: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.2), and `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (
        "P12's rows and the releases they name re-probed 2026-10-25)\n",
        "P12's rows and the releases they name re-probed 2026-10-25; juniper-ml 0.11.2's publish probed 2026-10-26)\n",
    ),
    ("- **Version**: 1.15.1\n", "- **Version**: 1.15.2\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (
        "and juniper-ml 0.11.0 and 0.11.1. R-OBS-SC-2 and R-DATA-2 are owed. P4's Wave 4 waits on Docker Hub secrets (10-10). | §5 (the fix-forwards; R-ML-SERVERS) | T1 |",
        "and juniper-ml 0.11.0, 0.11.1 and 0.11.2 (10-26). R-OBS-SC-2 and R-DATA-2 are owed. P4's Wave 4 waits on Docker Hub secrets (10-10). | §5 (the fix-forwards) | T1 |",
    ),
    (
        "juniper-ml 0.11.0 and 0.11.1 carry the floors. W0.1's service-core half: owner (XC-P12). | §5 R-ML-SERVERS; client 0.3.1 (owner); §6 A1, A9's rest | T1/T2 |",
        "juniper-ml 0.11.0 to 0.11.2 (10-26) carry the floors. W0.1's service-core half: owner (XC-P12). | client 0.3.1 (owner); §6 A1, A9's rest | T1/T2 |",
    ),
    (_XC_P12_OLD, _XC_P12_NEW),
    (_FURTHER_P12_OLD, _FURTHER_P12_NEW),
    (_P12_ROW_OLD, _P12_ROW_NEW),
    (_SERVERS_ROW_OLD, _SERVERS_ROW_NEW),
    (_RML_NOTES_OLD, _RML_NOTES_NEW),
    (
        "7. R-ML-SERVERS: its floors merged as ml#2326 (2026-10-25), and the owner ruled the cut **0.11.2** (2026-10-25; `detect.py` proposed 0.12.0). The cut waits on none of the steps above (v1.15.1).\n",
        "7. R-ML-SERVERS: shipped as juniper-ml **0.11.2** (2026-10-26; v1.15.2), its floors from ml#2326 and its version by the owner's ruling of 2026-10-25 (`detect.py` proposed 0.12.0).\n",
    ),
    (
        "  Opened with the owner on 2026-10-25.\n",
        "  Opened with the owner on 2026-10-25. **Ruled 2026-10-26: option 1** (in a turing session; v1.15.2). Its fix is ml#2345, FIX_STATE.\n",
    ),
    (
        "with the `[tools]` floors (ml#2314), released as 0.11.0 and 0.11.1; next, R-ML-SERVERS (§5) |",
        "with the `[tools]` floors (ml#2314), released as 0.11.0 and 0.11.1, and the `[servers]` floors (ml#2326), released as 0.11.2 (R-ML-SERVERS, §5) |",
    ),
    (_VALIDATION_ANCHOR, _VALIDATION_ANCHOR + _VALIDATION_ADD),
    (_SCRIPTS_ANCHOR, _SCRIPTS_ANCHOR + _SCRIPTS_ADD),
    (_MEMORY_ANCHOR, _MEMORY_ANCHOR + _MEMORY_ADD),
]


def replacements(fix_sha: "str | None") -> list[tuple[str, str]]:
    state = f"merged as `{fix_sha[:8]}`" if fix_sha else "open and armed on 2026-10-26"
    return [(old, new.replace("FIX_STATE", state)) for old, new in REPLACEMENTS]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix-sha", help="ml#2345's squash merge, once it has merged")
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.fix_sha and not _SHA_RE.match(args.fix_sha):
        raise SystemExit(f"ERROR: --fix-sha must be 8-40 lowercase hex, got {args.fix_sha!r}")

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in replacements(args.fix_sha):
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    long_lines = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]
    for n, width in long_lines:
        print(f"  ! line {n} is {width} characters, over {MAX_LINE}")
    if refused or long_lines:
        print(f"REFUSED: {refused} anchor(s), {len(long_lines)} long line(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
