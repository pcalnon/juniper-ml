#!/usr/bin/env python3
"""
Apply round-2 validation's corrections to the round-38 register filing.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (third and last of the round-38 register scripts)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/register_round38_file.py and register_round38_dates.py (the first two);
         reports/2026-09-09_round-38-consensus/ (the three lanes whose findings these apply);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md

Every change below was RE-DERIVED by the orchestrating session before being applied; a lane
finding is evidence, not an instruction. Two lane findings were themselves refuted and are NOT
applied (the "stale KO/ABT comment", which is the corrective comment data#388 added quoting the
claim it retracts; and a claimed latent bandit failure, which bandit 1.9.4 does not have because
B105 walks ``ast.Assign`` only).

The corrections:
  1. §2 note — DELETE the licensing clause. It asserted the unparked-implies-actionable
     equivalence §2 explicitly rejects, and drew authority from a machine-written handoff.
  2. §5.1 APD-CASCOR-007 — the mirror did NOT keep the drift test green; it broke it.
  3. §5.1 APD-DATA-038 — 228 passed was unreachable; the nine suites total 220.
  4. §4.9 APD-DATA-041 — "monotone" and "91 distinct steps" both withdrawn.
  5. §4.9 APD-DATA-043 — the inert ``median > 0`` clause out, the PSKY inversion in.
  6. §4.9 APD-DATA-044 — R -> C, restated at the DELIVERED level, BRK.B reclassified.
  7. §4.9 APD-CASCOR-009 — "bypasses _reload_dataset" narrowed to the fetch.
  8. §4.9 APD-CASCOR-010 — E -> C (the contract names metrics as a surface it must annotate).
  9. §4.9 APD-CASCOR-011 — "in-process spiral" is wrong; spiral goes over HTTP.
 10. Two new rows: APD-DATA-045 (stale forward-filled share counts) and APD-CASCOR-013
     (``_dataset_shortfall`` is never cleared).
 11. §4.9 preamble — the canopy findings are in a draft handoff, not in any ledger.
 12. The §2 status line — sixteen filed, thirteen open, 30 open in all.
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
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n} for:\n---\n{old[:260]}\n---")
    text = text.replace(old, new)
    print(f"  ok  {label}")


# ---- 1. The licensing clause comes out entirely. --------------------------------------------
sub(
    "\n"
    "> *(2026-09-09: the post-primer rows filed in [§4.9](#49-filed-after-the-primer) carry their own\n"
    "> row-level park / actionable sentences, stated under that table. They do not change the primer-row\n"
    "> position above — 17 primer rows open, one of them (`APD-DATA-019`) unparked — but they do end the\n"
    "> empty set: the §4.9 rows marked actionable (`APD-DATA-039`'s cache-key half, `APD-CASCOR-009` /\n"
    "> `APD-CASCOR-010` / `APD-CASCOR-012`) are the first a session may work without asking first, because\n"
    "> the Overtoad-issued round-37 handoff listed them as remaining work.)*\n",
    "\n"
    "> *(2026-09-09: the post-primer rows filed in [§4.9](#49-filed-after-the-primer) carry their own\n"
    "> row-level park sentences, stated under that table. They do not change the position above — 17\n"
    "> primer rows open, one of them (`APD-DATA-019`) unparked — and they do **not** end the empty set.\n"
    "> An earlier draft of this note claimed they did, on the grounds that the round-37 handoff had\n"
    "> listed four of them as remaining work. That was withdrawn the same day, by the round-2 validation\n"
    "> of the handoff that proposed it, and the reasoning is worth keeping because it is the exact\n"
    "> failure this section's rules exist to prevent. A handoff is not a fourth park shape: the three\n"
    "> shapes above are all **register** sentences, and \"a handoff listed it\" is a licensing mechanism,\n"
    "> which the rule above says the rule set does not contain. The four rows' provenance was a prior\n"
    "> session's own PR body (cascor#624's), so the claim reduced to a machine authorising its own\n"
    "> backlog. One of the four, `APD-DATA-039`, was never listed as work at all — round 37 described\n"
    "> the hazard and proposed no fix, and that same handoff's own §0.4 parks it under \"do not action\n"
    "> without a ruling\". And a document written 2026-09-07 cannot authorise rows filed 2026-09-09.\n"
    "> **The set of rows a session may action without asking the Overtoad first is still empty.**)*\n",
    "1. §2 licensing clause deleted",
)

# ---- 2. The false drift receipt. -------------------------------------------------------------
sub(
    "28 passed in `test_allow_truncated_datasets.py`; the `juniper-cascor-model` mirror keeps the drift test green. |",
    "28 passed in `test_allow_truncated_datasets.py`. **The mirror did not stay green, and this row said it did.** "
    "The PR's constants edit was mirrored, but a later CodeQL remedy on the same branch added a second `__all__` mid-file to the "
    "`juniper-cascor-model/` copy only, so `CI — juniper-cascor-model` went red on `main` at `44dafe0` and stayed there — "
    "and the remedy did not work either, the module already ending with its own complete `__all__` that never named the four "
    "constants. Found by round-2 validation 2026-09-09 (`reports/2026-09-09_round-38-consensus/`), repaired in "
    "[juniper-cascor#639](https://github.com/pcalnon/juniper-cascor/pull/639). `Test (Python 3.12)` was already failing when #633 merged, "
    "so it is not a required check on that repo — a red mirror is invisible at merge time. |",
    "2. drift receipt corrected",
)

# ---- 3. The unreachable test count. ----------------------------------------------------------
sub(
    "228 passed across the equities / seq / leakage / csv_import suites. |",
    "**220 passed** across the nine equities / seq / leakage / csv_import test files (93+50+19+19+12+9+8+6+4), re-run on `main` "
    "2026-09-09. This row first said 228, which no subset of those files can produce. |",
    "3. 228 -> 220",
)

# ---- 4. APD-DATA-041's two withdrawn numbers. ------------------------------------------------
sub(
    "`adj_close` is a default feature column built with `auto_adjust=False`, so `close / adj_close` is a monotone channel of future cumulative dividends (91 distinct steps on cached AAPL) — a look-ahead by the module's own rule that no quantity unknowable at a row's date may reach that row",
    "`adj_close` is a default feature column built with `auto_adjust=False` — which overrides yfinance's own default of `True`, so this line alone creates the channel. `close / adj_close` declines to exactly 1.0 at the download date and carries a **1.13% adjustment on the last row of a window ending 2023-12-29**, a level fixed by dividends paid after that row: a look-ahead by the module's own rule that no quantity unknowable at a row's date may reach it. Splits cancel (`close` is split-adjusted even at `auto_adjust=False`), so the channel is cumulative dividends, not a splits artifact. *(Two figures withdrawn 2026-09-09: the series is **not** monotone — 3246 up-steps against 3349 down — and \"91 distinct steps\" was a 6-decimal rounding artifact, the raw count being ~6,100. Harm is unmeasured: correlation with the next-day return is 0.004.)*",
    "4. APD-DATA-041 restated",
)

# ---- 5. APD-DATA-043: the inert clause out, the real inversion in. ---------------------------
sub(
    "(61 of 485 cached CIKs lose ≥1 point; 15 or 16 keep a different set under a causal median, definition-dependent); the `median > 0` guard also disables the filter for all-zero payloads",
    "(61 of 485 cached CIKs lose ≥1 point; 15 or 16 keep a different set under a causal median, definition-dependent). Sharpest instance: for PSKY the filter **deletes the only correct count** — `[1000, 1000, 1071666977]` has median 1000, so the bounds `[10, 100000]` keep the two placeholders and drop the real figure. *(The `median > 0` guard was cited here until 2026-09-09 as a second defect; it is inert — an all-zero series gets bounds `[0, 0]`, which every zero satisfies, so removing the guard changes the kept set for one payload of 485 and makes it worse.)*",
    "5. APD-DATA-043 restated",
)

# ---- 6. APD-DATA-044: severity and level of description. -------------------------------------
sub(
    "| APD-DATA-044 | Six cached payloads carry placeholder share counts (TAP `0,0,0`; DDOG; CVNA; FOX/FOXA `val=1`; PSKY `[1000, 1000, real]`; BRK.B at Class-A scale) that pass every guard — not NaN, so `fundamentals_fill`, the empty-units guard and `data_quality` are all silent and `market_cap` is 0.0 or nonsense | R |",
    "| APD-DATA-044 | Six **delivered** share series (what `_fetch_shares` returns, not the raw payload) carry unusable counts and pass every guard — not NaN, so `fundamentals_fill`, the empty-units guard and `data_quality` are all silent. Three deliver `total_shares == 0` for 100% of rows (TAP, CVNA, DDOG — DDOG's one real fact is unreachable because both were first filed the same day and the later `end` wins); FOX/FOXA deliver `val=1` from a spin-off registration; PSKY delivers `[1000, 1000]` after the outlier filter drops its real count (see `APD-DATA-043`). Delivered `market_cap`: 0 for the first three, 60 and 67 for FOX/FOXA, 10,980 for PSKY. **BRK.B is a different defect and not a placeholder** — the series is a correct, declining Class-A count, but one CIK serves both classes and `market_cap` prices it against the Class-B close (442,769,108 against a truth of ~1.1e12) | C |",
    "6. APD-DATA-044 restated, R -> C",
)

# ---- 7-9. The three cascor row corrections. ---------------------------------------------------
sub(
    "| APD-CASCOR-009 | `_auto_start_training` bypasses `_reload_dataset`: it never sets `dataset_shortfall`",
    "| APD-CASCOR-009 | `_auto_start_training` fetches the dataset **itself** rather than through `_reload_dataset` (it does later call `start_training`, which reaches `_reload_dataset` only when a pending config is staged), so on its own path it never sets `dataset_shortfall`",
    "7. APD-CASCOR-009 narrowed",
)
sub(
    "| APD-CASCOR-010 | `get_metrics()` / `/v1/metrics` carry no shortfall annotation, so a metric read without the status route carries no mark of the data behind it | E |",
    "| APD-CASCOR-010 | `get_metrics()` / `/v1/metrics` carry no shortfall annotation, so a metric read without the status route carries no mark of the data behind it. Graded `C`, not `E`, because `_build_dataset_shortfall`'s own docstring states the contract requires the accept and drop options to annotate progress, **metrics** and results: this is a declared contract met on two surfaces of three | C |",
    "8. APD-CASCOR-010 E -> C",
)
sub(
    "`--allow-truncated-datasets` is inert on `main.py`'s own run path — it only exports the env var, and that entry point reaches only the in-process `spiral` problem, which cannot be partial",
    "`--allow-truncated-datasets` is inert on `main.py`'s own run path — it only exports the env var, and that entry point reaches only the `spiral` generator, which cannot be partial. *(Corrected 2026-09-09: `spiral` is fetched over HTTP through `JuniperDataClient`, not in-process as this row first said; what makes the flag inert is that the generator is hardcoded, not that the data is local.)*",
    "9. APD-CASCOR-011 corrected",
)

# ---- 10. Two new rows, appended after APD-CASCOR-012. ----------------------------------------
NEW_ROWS = (
    "| APD-DATA-045 | Share counts go stale silently and are forward-filled for years: **26 of 485** delivered series have a last as-of date before 2025-06-01 (SPG stops at 2009-09-30, 16.7 years back; CMCSA at 2009-12-31; 14 predate 2015) against a cache-wide median of 2026-04-24, and every later row reuses the last value. Strictly harder to catch than `APD-DATA-044`'s zeros, because the resulting `market_cap` is plausible. Separately, SEC XBRL begins ~2009 while the default price window begins 2000, so even a healthy ticker ships a long zero-shares prefix (AAPL: 2,401 of 6,642 rows) | C | `generators/equities/generator.py` (`_fetch_shares`, and the forward-fill in `_condition_one`); cache `~/.cache/juniper_data/equities/shares/` | — | High |\n"
    "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared** — not on a new run, not on reset. A run started through the inline path with no staged dataset config keeps the previous run's annotation on `/v1/training/status`, naming a foreign `dataset_id`. Same family as `APD-CASCOR-007`: the annotation describes data this run is not training on | C | `src/api/lifecycle/manager.py` (init, the single write in `_reload_dataset`, the read in `get_status`) | — | High |\n"
)
sub(
    "| APD-CASCOR-012 | No operator-facing document names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` or `--allow-truncated-datasets`: absent from `AGENTS.md`'s env-var table, `.env.example` and every `docs/*.md` (only `CHANGELOG.md` records the field) | E | `AGENTS.md`, `.env.example` | — | High |\n",
    "| APD-CASCOR-012 | No operator-facing document names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` or `--allow-truncated-datasets`: absent from `AGENTS.md`'s env-var table, `.env.example` and every `docs/*.md` (only `CHANGELOG.md` records the field) | E | `AGENTS.md`, `.env.example` | — | High |\n" + NEW_ROWS,
    "10. two new rows filed",
)

# The park sentences for the two new rows.
sub(
    "- `APD-CASCOR-011` — **parked: design question** (drop the flag from `main.py`, or make that path reach\n"
    "  a truncatable generator); file, do not silently remove.\n",
    "- `APD-CASCOR-011` — **parked: design question** (drop the flag from `main.py`, or make that path reach\n"
    "  a truncatable generator); file, do not silently remove.\n"
    "- `APD-DATA-045` — **parked: Overtoad decision**, with `APD-DATA-039`, whose cache-key half is its\n"
    "  mechanism: a staleness bound is exactly the refresh-horizon question the Overtoad has not ruled on.\n"
    "- `APD-CASCOR-013` — **parked: Overtoad decision.** Clearing the annotation is one line, but *when* it\n"
    "  clears is a contract question (at every start, or only when a new dataset is fetched), and the\n"
    "  answer changes what a client polling `/v1/training/status` sees between runs.\n",
    "10b. park sentences for the new rows",
)

# ---- 11. The preamble's canopy-findings sentence. ---------------------------------------------
sub(
    "canopy findings from the same validation live in the canopy E2E ledger (`F-CANOPY-*`), not here —\n"
    "the two namespaces are deliberately unrelated: the explicit-`allow_truncation: false`-on-every-apply\n"
    "defect and the `val_ratio` / `INFRASTRUCTURE_FIELDS` drift are recorded in",
    "canopy findings from the same validation belong in the canopy E2E ledger (`F-CANOPY-*`), not here —\n"
    "the two namespaces are deliberately unrelated. **Two of them are in neither, and that is a gap, not a\n"
    "decision** (noted 2026-09-09): the explicit-`allow_truncation: false`-on-every-apply defect and the\n"
    "`val_ratio` / `INFRASTRUCTURE_FIELDS` drift are so far written down only in",
    "11. preamble corrected",
)

# ---- 12. The status line's post-primer arithmetic. --------------------------------------------
sub(
    "fourteen filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038`",
    "sixteen filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038`",
    "12a. fourteen -> sixteen",
)
sub(
    "are FIXED and eleven are open — **28 open in all**, 17 primer + 11 post-primer.",
    "are FIXED and thirteen are open — **30 open in all**, 17 primer + 13 post-primer.",
    "12b. counts updated",
)

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
rc = crosscheck(text)
for needle in ("114.8", "228 passed", "keeps the drift test green", "end the empty set", "monotone channel"):
    hits = [i + 1 for i, line in enumerate(text.splitlines()) if needle in line]
    print(f"  {needle!r}: {hits or 'gone'}")
raise SystemExit(rc)
