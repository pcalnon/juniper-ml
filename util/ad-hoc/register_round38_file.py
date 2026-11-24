#!/usr/bin/env python3
"""
Round-38 defect-register filing: §4.9 post-primer rows, three closes, two precision withdrawals
and the stale §2 operating-rule paragraph -- exact-match edits that refuse on any miss.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once on 2026-09-08; re-runnable with --dry-run as the statement of what changed)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md;
         reports/2026-09-08_round-37-consensus/ (the six lanes whose findings these rows file);
         util/ad-hoc/register_open_set.py and register_status_crosscheck.py (run on the result before writing)

What it does
------------
1. `Last Updated` -> 2026-09-08.
2. Withdraws the four-significant-figure "114.8x / 92.9x" JD-PERF-02 speed-ups at the two sites
   that still carried them (the `APD-DATA-019` row and the §4.1 correction note); only the order is
   quotable (re-measurements 96.6-180.1x and 77.4-173.2x).
3. Rewrites the §2 paragraph that still said "Both unparked rows" and named the withdrawn `total`
   remedy; adds a dated note that the §4.9 actionable rows end the "empty set" of 2026-09-03.
4. §2 status line: "Seventy-nine of the 96", the post-primer clause naming the three new FIXED ids,
   "28 open in all".
5. Inserts §4.9 "Filed after the primer" (14 rows, APD-DATA-037..044 and APD-CASCOR-007..012) with
   the row-level park / actionable sentences, before the §5 heading.
6. Inserts the three §5.1 verification rows.

It refuses to mark a row FIXED unless `gh pr view` reports the cited PR MERGED (skipped with a
warning under --dry-run), and runs the two checkers on the edited text before writing.
Usage (from the repo root or anywhere):  python3 util/ad-hoc/register_round38_file.py [--dry-run [--dry-run-out PATH]]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"


def pr_state(repo: str, number: int) -> dict:
    out = subprocess.run(["gh", "pr", "view", str(number), "--repo", f"pcalnon/{repo}", "--json", "state,mergedAt,mergeCommit"], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dry-run-out", default=None, help="under --dry-run, also write the edited text here")
    args = parser.parse_args()
    dry = args.dry_run

    states = {
        "data#388": pr_state("juniper-data", 388),
        "cascor#633": pr_state("juniper-cascor", 633),
        "canopy#605": pr_state("juniper-canopy", 605),
    }
    for key in ("data#388", "cascor#633"):
        if states[key]["state"] != "MERGED":
            if dry:
                print(f"WARNING (dry run): {key} is {states[key]['state']}, not MERGED")
                continue
            sys.exit(f"REFUSED: {key} is {states[key]['state']}, not MERGED -- cannot mark its rows FIXED")
    canopy_note = "closed by [juniper-canopy#605](https://github.com/pcalnon/juniper-canopy/pull/605)" if states["canopy#605"]["state"] == "MERGED" else "fix in flight as [juniper-canopy#605](https://github.com/pcalnon/juniper-canopy/pull/605)"
    print({k: v["state"] for k, v in states.items()})

    text = REG.read_text()

    def replace_once(old: str, new: str) -> None:
        nonlocal text
        n = text.count(old)
        if n != 1:
            sys.exit(f"FAIL: expected 1 match, found {n} for:\n---\n{old[:240]}\n---")
        text = text.replace(old, new)
        print(f"edited: {old.splitlines()[0][:70]!r}")

    # 1. Header date.
    replace_once("**Last Updated**: 2026-09-04\n", "**Last Updated**: 2026-09-08\n")

    # 2. The two withdrawn-precision sites (the APD-DATA-019 row and the §4.1 correction note).
    replace_once(
        "(114.8x at N=100)",
        "(of order 100× at N=100 — 96.6–180.1× across the round-37 and 2026-09-08 re-measurements, machine- and instrument-specific, so only the order is quotable)",
    )
    replace_once(
        "Measured after: **114.8× at N=100**, **92.9×\n  > at N=1,000**.",
        "Measured after: **of order 100× at N=100 and at N=1,000** (re-measured 2026-09-07/08 at 96.6–180.1× and\n  > 77.4–173.2×; the four-significant-figure values this note carried until 2026-09-08 were one run on one machine and are withdrawn).",
    )
    if "114.8" in text or "92.9×" in text:
        sys.exit("FAIL: a withdrawn-precision claim survives outside the two known sites")

    # 3. The stale §2 operating-rule paragraph (ml#1813 edited only the §4.1 bullet).
    replace_once(
        "Both unparked rows still\n"
        "require an Overtoad decision before any code can be written — `-018`'s cap is a rejection-vs-truncation\n"
        "and rows-vs-bytes question, `-019`'s remedy needs `total` estimated, cached or absent, and the last\n"
        "is a response-shape change for existing clients.",
        "The one unparked primer row, `APD-DATA-019`, still\n"
        "requires an Overtoad decision before any code can be written — its remedy, re-scoped 2026-09-07 onto\n"
        "`list_all_metadata()`, is a per-store filter/sort/limit pushdown or sidecar index, and which stores get\n"
        "one is the decision (`total` was the wrong target and is no longer part of it; `-018` closed 2026-09-04).",
    )
    replace_once(
        "been worked, not an obstacle to route around.\n",
        "been worked, not an obstacle to route around.\n"
        "\n"
        "> *(2026-09-08: the post-primer rows filed in [§4.9](#49-filed-after-the-primer) carry their own\n"
        "> row-level park / actionable sentences, stated under that table. They do not change the primer-row\n"
        "> position above — 17 primer rows open, one of them (`APD-DATA-019`) unparked — but they do end the\n"
        "> empty set: the §4.9 rows marked actionable (`APD-DATA-039`'s cache-key half, `APD-CASCOR-009` /\n"
        "> `APD-CASCOR-010` / `APD-CASCOR-012`) are the first a session may work without asking first, because\n"
        "> the Overtoad-issued round-37 handoff listed them as remaining work.)*\n",
    )

    # 4. The §2 status line: the three post-primer closes, on the SAME line the crosscheck reads.
    replace_once(
        "**Seventy-nine have since been fixed** — ",
        "**Seventy-nine of the 96 have since been fixed** — ",
    )
    replace_once(
        "leaving **17 open**; each is marked at its detail entry and in its §4 table row, and all seventy-nine are recorded in [§5](#5-fixed-findings-before-and-since-the-primer) with their PR and verification.",
        "leaving **17 open** of the primer rows; each is marked at its detail entry and in its §4 table row, and all seventy-nine are recorded in [§5](#5-fixed-findings-before-and-since-the-primer) with their PR and verification. "
        "**Post-primer rows** ([§4.9](#49-filed-after-the-primer), filed 2026-09-08 from the round-37/38 handoff validation, not counted in the 96): fourteen filed, of which (2026-09-08) `APD-DATA-037` / `APD-DATA-038` ([juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388)) and `APD-CASCOR-007` ([juniper-cascor#633](https://github.com/pcalnon/juniper-cascor/pull/633)) are FIXED and eleven are open — **28 open in all**, 17 primer + 11 post-primer.",
    )

    # 5. §4.9 — the post-primer table, before the §5 heading.
    section_49 = """### 4.9 Filed after the primer

Rows the primer never contained, filed from later work — here, the independent-agent validation of the
round-37 defect-register handoff (six lanes, 2026-09-08; record in
`reports/2026-09-08_round-37-consensus/`). They are **not counted in the 96** above, the `Primer` column
is `—`, and each row's park status is stated in its own row-level sentence below the table (the
"Parked has three shapes" rule applies). Ids continue each repository's sequence; retired ids are never
reused. canopy findings from the same validation live in the canopy E2E ledger (`F-CANOPY-*`), not here —
the two namespaces are deliberately unrelated: the explicit-`allow_truncation: false`-on-every-apply
defect and the `val_ratio` / `INFRASTRUCTURE_FIELDS` drift are recorded in
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md`
(the former CANOPY_NOTE).

| ID | Finding | Sev | Source | Primer | Conf |
|---|---|---|---|---|---|
| APD-DATA-037 | **FIXED ([juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388))** — `equities_seq` bound no deployment defaults: `dataset_id` hashed the schema defaults, so two requests under different truncation policies collided on one id (proven by execution: identical ids under `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` off vs on) | C | `generators/equities_seq/generator.py` (`bind_deployment_defaults`), `api/routes/datasets.py` (the `getattr` binder hook) | — | High |
| APD-DATA-038 | **FIXED ([juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388))** — `equities_seq` never applied the fail / accept / drop policy: an unrescued ticker shipped with fabricated `total_shares` / `market_cap`, no refusal, no `data_quality` annotation, whatever `allow_truncation` said; its own test fixtures were silently exercising the gap | C | `generators/equities_seq/generator.py` (`generate`), `generators/equities/generator.py` (`_apply_incomplete_policy`) | — | High |
| APD-DATA-039 | SEC shares cache key is CIK-only — no version, TTL or mtime; a warm hit skips the concept loop and the rescue ladder and erases `quality` / `origin` provenance, so a `degraded` annotation fires on the cold day and vanishes the next while `end_date=None` mints a new `dataset_id` daily | R | `generators/equities/generator.py` (`_fetch_shares`: `_CACHE_DIR / "shares" / f"{int(cik):010d}.json"`, `if use_cache and cache.exists()`) | — | High |
| APD-DATA-040 | `_fetch_shares` keeps the latest-filed fact per period end, so a same-value re-statement re-dates history: 162 of 485 cached CIKs affected, 17,569 rows, ADM in the default prefix off by up to +11.55%; the same dedup defers the first available count for 9 CIKs (EXPE: 521 rows NaN where the figure was public) | C | `generators/equities/generator.py` (`_fetch_shares` — sort by `(end, filed)`, last write wins); instruments `util/ad-hoc/2026-09-08_equities_shares_cache_census/` | — | High |
| APD-DATA-041 | `adj_close` is a default feature column built with `auto_adjust=False`, so `close / adj_close` is a monotone channel of future cumulative dividends (91 distinct steps on cached AAPL) — a look-ahead by the module's own rule that no quantity unknowable at a row's date may reach that row | C | `generators/equities/generator.py` (`yf.download(..., auto_adjust=False)`, `"Adj Close": "adj_close"`), `equities/defaults.py` (`EQUITIES_FEATURE_COLUMNS`) | — | Med |
| APD-DATA-042 | `cost_basis` is a per-ticker constant written to every row, inert only at the default `purchase_date`; any later date is a full future-price leak, and `purchase_date` is a plain public request field (a text input in canopy's sidebar) | C | `generators/equities/generator.py` (`cost_basis` via `on_or_before(purchase_date)`), `equities/params.py` (`purchase_date`) | — | High |
| APD-DATA-043 | `_SHARES_OUTLIER_FACTOR` filters share points against a whole-history median, so which points survive depends on filings made after the affected rows (61 of 485 cached CIKs lose ≥1 point; 15 or 16 keep a different set under a causal median, definition-dependent); the `median > 0` guard also disables the filter for all-zero payloads | C | `generators/equities/generator.py` (`_SHARES_OUTLIER_FACTOR`, the median filter in `_fetch_shares`) | — | High |
| APD-DATA-044 | Six cached payloads carry placeholder share counts (TAP `0,0,0`; DDOG; CVNA; FOX/FOXA `val=1`; PSKY `[1000, 1000, real]`; BRK.B at Class-A scale) that pass every guard — not NaN, so `fundamentals_fill`, the empty-units guard and `data_quality` are all silent and `market_cap` is 0.0 or nonsense | R | `generators/equities/generator.py` (`_fetch_shares`, `_condition_one`); cache `~/.cache/juniper_data/equities/shares/` | — | High |
| APD-CASCOR-007 | **FIXED ([juniper-cascor#633](https://github.com/pcalnon/juniper-cascor/pull/633))** — `dataset_shortfall.accepted_via_allow_truncated_datasets` was the raw service setting, so it read `false` on a run training on partial data accepted by the caller's params or by the producer's own deployment default — an annotation denying the acceptance it annotated | C | `src/api/lifecycle/manager.py` (`_build_dataset_shortfall`, `_reload_dataset`) | — | High |
| APD-CASCOR-008 | `_PROJECT_API_TRUNCATABLE_GENERATORS` duplicates knowledge juniper-data owns, and two of its three members are unreachable: cascor's `dataset_type` Literal excludes `csv_import` and `equities_seq` | M | `src/cascor_constants/constants_api/constants_api_defaults.py`, `src/api/models/training.py` (the Literal) | — | High |
| APD-CASCOR-009 | `_auto_start_training` bypasses `_reload_dataset`: it never sets `dataset_shortfall` (an auto-started run on partial data reports `null`), forwards no truncation opt-in, and swallows its failure (`except Exception: logger.exception`), leaving the service healthy with no training | C | `src/api/app.py` (`_auto_start_training`) | — | High |
| APD-CASCOR-010 | `get_metrics()` / `/v1/metrics` carry no shortfall annotation, so a metric read without the status route carries no mark of the data behind it | E | `src/api/lifecycle/manager.py` (`get_metrics`) | — | High |
| APD-CASCOR-011 | `--allow-truncated-datasets` is inert on `main.py`'s own run path — it only exports the env var, and that entry point reaches only the in-process `spiral` problem, which cannot be partial | E | `src/main.py` (the flag), `src/api/lifecycle/manager.py` (the only reader) | — | High |
| APD-CASCOR-012 | No operator-facing document names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` or `--allow-truncated-datasets`: absent from `AGENTS.md`'s env-var table, `.env.example` and every `docs/*.md` (only `CHANGELOG.md` records the field) | E | `AGENTS.md`, `.env.example` | — | High |

**Park / actionable status of the open post-primer rows** (row-level sentences; a sentence here parks
or unparks its row and nothing else):

- `APD-DATA-039` — **actionable** for the versioned key + TTL; **the refresh horizon (how far back to
  regenerate) is an Overtoad decision.**
- `APD-DATA-040`, `APD-DATA-041`, `APD-DATA-042`, `APD-DATA-043` — **parked: Overtoad decision.** Each changes
  the artifact's content and needs a `generator_version` bump; first-publication vs latest-filed
  (`-040`) is a design choice, not a bug fix.
- `APD-DATA-044` — **parked: Overtoad decision**, in the same batch as `-040`…`-043`: treating an all-zero or
  placeholder series as `unrescued` (like the empty-units case) is the obvious remedy, but it changes which
  universes pass the default `fail` policy, so it ships with the same `generator_version` bump.
- `APD-CASCOR-008` — **parked: Overtoad decision** (derive the set from juniper-data's `/v1/generators`, or
  keep the list and narrow it to the reachable member).
- `APD-CASCOR-009`, `APD-CASCOR-010`, `APD-CASCOR-012` — **actionable**; one PR, the cascor#624 follow-ups.
- `APD-CASCOR-011` — **parked: design question** (drop the flag from `main.py`, or make that path reach
  a truncatable generator); file, do not silently remove.

"""
    replace_once("---\n\n## 5. Fixed findings (before and since the primer)\n", section_49 + "---\n\n## 5. Fixed findings (before and since the primer)\n")
    text = text.replace("(the former CANOPY_NOTE)", f"({canopy_note})")

    # 6. §5.1 verification rows, inserted right after the §5.1 table's separator line.
    start = text.index("### 5.1 ")
    sep = "| --- | --- | --- | --- |\n"
    sep_at = text.index(sep, start)
    rows_51 = (
        "| APD-DATA-037 | `equities_seq` bound no deployment defaults, so its `dataset_id` collided across truncation policies | [juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388) | `EquitiesSeqGenerator.bind_deployment_defaults` delegates to the flat generator's binder (`model_copy` keeps the subclass). Pinned by `test_equities_seq_deployment_policy.py`: env off vs on now yield different ids, the unbound dump still collides (the statement of what the binder fixes). Deliberate consequence recorded in the CHANGELOG: every `equities_seq` id changes once. |\n"
        "| APD-DATA-038 | `equities_seq` never applied the fail / accept / drop contract | [juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388) | The classify / resolve / fail-or-drop / annotate block is one shared helper, `EquitiesGenerator._apply_incomplete_policy`, called by both generators (seq: after conditioning, before the normaliser fit and windowing). Pinned: default refusal, accept annotates, drop removes the ticker from every window with `rows_affected == 0`, drop-that-empties still fails, clean carries no annotation. The seq fixtures' filings were unreachable inside the mocked frame — every seq test had been running on all-NaN fundamentals — and were moved inside it rather than opting the tests into truncation. 228 passed across the equities / seq / leakage / csv_import suites. |\n"
        "| APD-CASCOR-007 | `accepted_via_allow_truncated_datasets` denied the acceptance it annotated | [juniper-cascor#633](https://github.com/pcalnon/juniper-cascor/pull/633) | The annotation carries `accepted_by_this_run` and `acceptance_source` (`request_params` / `allow_truncated_datasets` / `producer`), derived from what cascor SENT (the producer's descriptor has no authority field); the original field keeps its literal meaning. Three arms run `_reload_dataset` to the annotation and stop; the `producer` arm is the regression. Also: the refusal keys its remedy off the wire stance (a caller's explicit `false` used to get the bare fetch-failed line) and opens with `[dataset_shortfall_refused]`. 28 passed in `test_allow_truncated_datasets.py`; the `juniper-cascor-model` mirror keeps the drift test green. |\n"
    )
    text = text[: sep_at + len(sep)] + rows_51 + text[sep_at + len(sep):]
    print("inserted 3 §5.1 rows")

    sys.path.insert(0, str(HERE))
    from register_open_set import format_report, parse_register  # noqa: E402
    from register_status_crosscheck import crosscheck  # noqa: E402

    seen, fixed = parse_register(text)
    print("open-set:", format_report(seen, fixed).splitlines()[0])
    if crosscheck(text) != 0:
        sys.exit("FAIL: crosscheck DISAGREE on the edited text")
    for needle in ("17 open", "eventy-nine", "28 open", "114.8", "Both unparked"):
        hits = [i + 1 for i, line in enumerate(text.splitlines()) if needle in line]
        print(f"needle {needle!r}: lines {hits}")
    if dry:
        if args.dry_run_out:
            Path(args.dry_run_out).write_text(text)
            print(f"(dry run: nothing written to the register; result at {args.dry_run_out})")
        else:
            print("(dry run: nothing written to the register)")
        return 0
    REG.write_text(text)
    print("REGISTER WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
