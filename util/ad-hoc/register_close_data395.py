#!/usr/bin/env python3
"""
Close the seven equities rows that juniper-data#395 fixed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc — one-off (refuses until juniper-data#395 reads MERGED)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#395; the owner rulings of 2026-09-09 in register §4.9

APD-DATA-039, -040, -041, -042, -043, -044 and -045. Four touches each (none has a §3 entry):
the §4.9 row, a §5.1 verification row, the §2 status line, and the header date.

APD-DATA-046 (Berkshire's dual-class mismatch) stays OPEN and is the reason -044's close is
bounded: the floor retires five placeholder series, and the sixth is a genuine Class-A count that
no plausibility bound can catch.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PR = "[juniper-data#395](https://github.com/pcalnon/juniper-data/pull/395)"

state = json.loads(subprocess.run(["gh", "pr", "view", "395", "--repo", "pcalnon/juniper-data", "--json", "state,mergedAt"], check=True, capture_output=True, text=True).stdout)
if state["state"] != "MERGED":
    sys.exit(f"REFUSED: juniper-data#395 is {state['state']}")
print(f"juniper-data#395 MERGED {state['mergedAt']}")

text = REG.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} matches for:\n{old[:160]}")
    text = text.replace(old, new)
    print(f"  ok  {label}")


ROWS = {
    "APD-DATA-039": "SEC shares cache key is CIK-only",
    "APD-DATA-040": "`_fetch_shares` keeps the latest-filed fact per period end",
    "APD-DATA-041": "`adj_close` is a default feature column",
    "APD-DATA-042": "`cost_basis` is a per-ticker constant",
    "APD-DATA-043": "`_SHARES_OUTLIER_FACTOR` filters share points",
    "APD-DATA-044": "Six **delivered** share series",
    "APD-DATA-045": "Share counts go stale silently",
}
for row_id, opener in ROWS.items():
    sub(f"| {row_id} | {opener}", f"| {row_id} | **FIXED ({PR})** — {opener}", f"§4.9 row {row_id}")

VERIFICATION = {
    "APD-DATA-039": "Versioned cache key (`shares/v{N}/`) plus a 7-day TTL; an unreadable mtime is treated as expired, because failing towards a network call costs a request while failing towards the cache can serve a year-old figure forever. Existing payloads are orphaned by the new key, which is correct for a shape change and is carried as migration work.",
    "APD-DATA-040": "Every SEC fact is now an observation keyed by `(end, filed)` rather than one latest-filed value per period end, so the publication history survives and `_condition_one`'s existing as-of join — which was always correct — stops being fed a rewritten past. Pinned by a regression asserting BOTH the original publication and the restatement survive.",
    "APD-DATA-041": "Removed from `EQUITIES_FEATURE_COLUMNS`; the matrix is 15 columns. **Bounded close:** the column is still produced but there is now no way to request it into a dataset, because `EquitiesParams` has no feature-column parameter — the option was described to the owner as leaving it requestable, and that was wrong. Restoring the capability is carried as work.",
    "APD-DATA-042": "Rows before `purchase_date` carry no basis. Pinned by a regression asserting the absent values form a strict PREFIX, since causality is an ordering claim and a scattered set of NaNs would satisfy a naive count assertion while meaning something else.",
    "APD-DATA-043": "Expanding-window median over facts already filed, plus an absolute floor at 100,000 shares. Pinned by a regression whose two payloads share a prefix and differ only in later filings; an earlier version of that test passed against the OLD filter too, and was rebuilt with numbers where the two genuinely disagree. An absolute ceiling at 1e13 was added in the same change and is NOT part of the ruling — see `APD-DATA-047`.",
    "APD-DATA-044": "Closed by `-043`'s floor: TAP, CVNA and FOX/FOXA now return no shares at all and route into the incomplete-data contract, and PSKY and DDOG recover real counts the old filter and the old dedup respectively destroyed. **Bounded close:** Berkshire is untouched and is `APD-DATA-046` — its numbers are genuine, so no floor can reach it.",
    "APD-DATA-045": "A series with more than 365 days of silence before its window ends is annotated `degraded` with the affected row count. Measured per SERIES: a first implementation measured per row, which flags the tail of every gap — an annual filer produces a 365-day gap by definition — and was caught when it made a deliberately-clean fixture dirty.",
}

start = text.index("### 5.1 ")
sep = "| --- | --- | --- | --- |\n"
at = text.index(sep, start) + len(sep)
rows = "".join(f"| {rid} | {ROWS[rid].replace('**', '')} | {PR} | {VERIFICATION[rid]} |\n" for rid in ROWS)
text = text[:at] + rows + text[at:]
print(f"  ok  {len(ROWS)} §5.1 verification rows")

sub(
    "and ten are open — **27 open in all**, 17 primer + 10 post-primer.",
    f"`APD-DATA-039` / `-040` / `-041` / `-042` / `-043` / `-044` / `-045` ({PR}) and three are open — **20 open in all**, 17 primer + 3 post-primer.",
    "§2 status line",
)
sub("**Last Updated**: 2026-09-09 (owner rulings)\n", "**Last Updated**: 2026-09-15\n", "header date")

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
raise SystemExit(crosscheck(text))
