#!/usr/bin/env python3
"""
Record the Overtoad's rulings of 2026-09-09 on the open post-primer rows, and file the one new row
they produced.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md;
         util/ad-hoc/register_close_cascor640.py

Thirteen rulings, taken interactively. They END the empty set for the rows named below: a ruling
from the Overtoad is the thing §2 says is required, and unlike the note withdrawn earlier today it is
not derived from a handoff or a PR body.

The rulings, and the evidence each was taken against:
  * `-039` + `-045`  versioned key + TTL + a staleness ANNOTATION, bound **365 days**. Chosen from
    the measured distribution (median last-as-of age 138 days, p90 180; 365d flags 27 of 485, and
    the curve is flat from 270d to 730d, so the exact number stops mattering).
  * `-040`  as-of join on FILED date: each trading row sees the latest fact filed on or before it.
  * `-041`  drop `adj_close` from the default feature columns; it stays requestable.
  * `-042`  make `cost_basis` causal — no basis on rows before `purchase_date`.
  * `-043`  causal (expanding-window) median PLUS an absolute floor.
  * `-044`  closed by that floor rather than a rule of its own. Floor = **100,000 shares**, chosen
    to sit above PSKY's 1,000 placeholders and below Berkshire's genuine Class-A low of 941,481.
  * `-046`  NEW, and the reason `-044` does not cover everything: Berkshire's numbers are REAL, so
    no floor can catch them. Filed now; the class-aware lookup is recorded as its remedy, deferred.
  * `-019`  implement filter/sort/limit pushdown in ALL stores.
  * `APD-CASCOR-008`  derive the truncatable set from juniper-data's `/v1/generators`.
  * `APD-CASCOR-011`  keep as cascor#640 shipped it; CLOSED as WON'T FIX, marker included.
  * `APD-CASCOR-013`  clear the annotation at the start of every run.

Not recorded here because it is a contract change rather than a defect row: option 3 becomes a
caller right via an explicit tri-state `allow_truncation: true | false | null`. That reverses the
premise of juniper-data's `test_request_cannot_opt_out_of_deployment_allow_truncation`, which pins
the behaviour the Overtoad has now overruled — see the handoff and the partial-data arc memory.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REG.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n} for:\n---\n{old[:200]}\n---")
    text = text.replace(old, new)
    print(f"  ok  {label}")


# ---- 1. The park block becomes a rulings block. ----------------------------------------------
sub(
    "- `APD-DATA-039` — **actionable** for the versioned key + TTL; **the refresh horizon (how far back to\n"
    "  regenerate) is an Overtoad decision.**\n"
    "- `APD-DATA-040`, `APD-DATA-041`, `APD-DATA-042`, `APD-DATA-043` — **parked: Overtoad decision.** Each changes\n"
    "  the artifact's content and needs a `generator_version` bump; first-publication vs latest-filed\n"
    "  (`-040`) is a design choice, not a bug fix.\n"
    "- `APD-DATA-044` — **parked: Overtoad decision**, in the same batch as `-040`…`-043`: treating an all-zero or\n"
    "  placeholder series as `unrescued` (like the empty-units case) is the obvious remedy, but it changes which\n"
    "  universes pass the default `fail` policy, so it ships with the same `generator_version` bump.\n"
    "- `APD-CASCOR-008` — **parked: Overtoad decision** (derive the set from juniper-data's `/v1/generators`, or\n"
    "  keep the list and narrow it to the reachable member).\n",
    "> **OWNER RULINGS, 2026-09-09.** Taken interactively, on evidence re-derived in the same session.\n"
    "> These **end the empty set** for the rows below — a ruling from the Overtoad is exactly what §2 requires,\n"
    "> and unlike the note withdrawn earlier the same day it is not derived from a handoff or a PR body.\n"
    "> Every one of them changes artifact content, so they ship together behind one `generator_version`\n"
    "> bump on `equities` / `equities_seq`.\n"
    "\n"
    "- `APD-DATA-039` + `APD-DATA-045` — **RULED: actionable.** Versioned cache key, a TTL, and a staleness\n"
    "  **annotation** rather than a silent forward-fill. **Bound: 365 days.** Chosen against the measured\n"
    "  distribution — median last-as-of age 138 days, p90 180, and 365d flags 27 of 485 while the curve is\n"
    "  flat from 270d to 730d, so the exact figure is not load-bearing. Anything tighter than ~200 days\n"
    "  measures cache age rather than issuer staleness (120d would flag 95% of the universe).\n"
    "- `APD-DATA-040` — **RULED: actionable.** As-of join on the FILED date: each trading row uses the latest\n"
    "  fact filed on or before that row's date. Neither first-publication nor latest-filed, both of which\n"
    "  were offered; the as-of join is the one that lets a row see corrections without seeing its own future.\n"
    "- `APD-DATA-041` — **RULED: actionable.** Drop `adj_close` from `EQUITIES_FEATURE_COLUMNS`; it stays\n"
    "  requestable for anyone who asks for it explicitly. Rejected: switching to `auto_adjust=True`, which\n"
    "  would change what every price column means for every existing consumer.\n"
    "- `APD-DATA-042` — **RULED: actionable.** Make `cost_basis` causal — no basis on rows before\n"
    "  `purchase_date`, the constant only from that date on. Fixes the leak at EVERY `purchase_date` rather\n"
    "  than only the default, and keeps the feature rather than deleting it.\n"
    "- `APD-DATA-043` — **RULED: actionable.** Causal (expanding-window) median **plus** an absolute\n"
    "  plausibility floor. The causal median removes the look-ahead; the floor is what actually rescues\n"
    "  PSKY, whose early placeholders otherwise dominate the window that judges its real count.\n"
    "- `APD-DATA-044` — **RULED: closed by `-043`'s floor**, not by a rule of its own. **Floor = 100,000\n"
    "  shares**, sited above PSKY's 1,000 placeholders and below Berkshire's genuine Class-A low of 941,481\n"
    "  (the smallest ordinary issuer in the cache, NVR, is 2,699,292). Five of the six series die there.\n"
    "  **The sixth does not, and that is `APD-DATA-046`** — Berkshire's counts are real.\n"
    "- `APD-CASCOR-008` — **RULED: actionable.** Derive the truncatable set from juniper-data's\n"
    "  `/v1/generators` — one source of truth, no drift. Rejected: widening cascor's `dataset_type` Literal,\n"
    "  and narrowing the constant to its one reachable member. The startup dependency this introduces is a\n"
    "  design constraint on the implementation, not a reason to revisit the ruling.\n",
    "1. data + cascor-008 rulings",
)

sub(
    "- `APD-CASCOR-011` — **parked: design question** (drop the flag from `main.py`, or make that path reach\n"
    "  a truncatable generator); file, do not silently remove.\n",
    "- `APD-CASCOR-011` — **RULED: keep as cascor#640 shipped it, and close the row.** The export IS the\n"
    "  flag's purpose (it configures a service this process may launch) and the inertness is now stated in\n"
    "  `--help`, in a WARNING on use, and in the operator docs. Rejected: dropping it from `main.py`, and\n"
    "  rewiring that path to reach a truncatable generator.\n",
    "2. -011 ruling",
)
sub(
    "- `APD-DATA-045` — **parked: Overtoad decision**, with `APD-DATA-039`, whose cache-key half is its\n"
    "  mechanism: a staleness bound is exactly the refresh-horizon question the Overtoad has not ruled on.\n",
    "- `APD-DATA-046` — **filed 2026-09-09, deferred by the same ruling.** The remedy of record is a\n"
    "  share-class-aware lookup (resolve the count for the requested ticker's class, not the CIK's\n"
    "  default); the Overtoad ruled to file it now and do it later in this development path.\n",
    "3. -045 line replaced by -046",
)
sub(
    "- `APD-CASCOR-013` — **parked: Overtoad decision.** Clearing the annotation is one line, but *when* it\n"
    "  clears is a contract question (at every start, or only when a new dataset is fetched), and the\n"
    "  answer changes what a client polling `/v1/training/status` sees between runs.\n",
    "- `APD-CASCOR-013` — **RULED: actionable.** Clear the annotation at the **start of every run**. The\n"
    "  field is named for what THIS run trained on, so it describes this run or it is null; a run that\n"
    "  fetched nothing correctly reports nothing. Rejected: clearing only on a new fetch, and documenting\n"
    "  the current keep-until-reset behaviour.\n",
    "4. -013 ruling",
)

# ---- 2. The new row. --------------------------------------------------------------------------
sub(
    "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**",
    "| APD-DATA-046 | One CIK serves both of an issuer's share classes, so a **genuine** count is priced against the wrong class's close: Berkshire's Class-A series (941,481–1,103,764) is multiplied by the Class-B close, giving a `market_cap` of 442,769,108 against a truth near 1.1e12. No plausibility floor can catch it — the number is real, and only the pairing is wrong. Distinct from `APD-DATA-044`, whose six series are placeholders | C | `generators/equities/generator.py` (`_fetch_shares` keys on CIK; `_condition_one` multiplies by the requested ticker's close) | — | High |\n"
    "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**",
    "5. APD-DATA-046 filed",
)

# ---- 3. APD-CASCOR-011 closes, WON'T FIX with the marker inside. ------------------------------
sub(
    "| APD-CASCOR-011 | `--allow-truncated-datasets` is inert on `main.py`'s own run path",
    "| APD-CASCOR-011 | **FIXED (WON'T FIX — Overtoad ruled 2026-09-09 to keep the flag; the inertness is now documented, not silent, by [juniper-cascor#640](https://github.com/pcalnon/juniper-cascor/pull/640))** — `--allow-truncated-datasets` is inert on `main.py`'s own run path",
    "6. -011 closed",
)

# ---- 4. APD-DATA-019's ruling, on the row itself. ---------------------------------------------
sub(
    "storage index still open, latent at the deployed N=21",
    "storage index **RULED 2026-09-09: implement the pushdown in ALL stores** (one Postgres pushdown, LocalFS and Redis index builds, four delegations) rather than deferring on the latent cost — still open, latent at the deployed N=21",
    "7. -019 ruling",
)

# ---- 5. The §2 status line. -------------------------------------------------------------------
sub(
    "and `APD-CASCOR-009` / `APD-CASCOR-010` / `APD-CASCOR-012` ([juniper-cascor#640](https://github.com/pcalnon/juniper-cascor/pull/640)) are FIXED and ten are open — **27 open in all**, 17 primer + 10 post-primer.",
    "`APD-CASCOR-009` / `APD-CASCOR-010` / `APD-CASCOR-012` and (WON'T FIX) `APD-CASCOR-011` ([juniper-cascor#640](https://github.com/pcalnon/juniper-cascor/pull/640)) are FIXED and ten are open — **27 open in all**, 17 primer + 10 post-primer. "
    "**Ten of those carry Overtoad rulings taken 2026-09-09** and are actionable; see the rulings block under [§4.9](#49-filed-after-the-primer).",
    "8. §2 status line",
)

sub("**Last Updated**: 2026-09-09\n", "**Last Updated**: 2026-09-09 (Overtoad rulings)\n", "9. header date")

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
raise SystemExit(crosscheck(text))
