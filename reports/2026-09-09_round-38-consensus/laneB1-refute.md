# Round 2, Lane B1 — REFUTATION (verbatim, 2026-09-09)

*(As returned by the lane, with its own attack-8 retraction folded in as it requested. The lane's
harness refused to let it write this file, so the orchestrating session transcribed it; its evidence
artifacts remain in the lane scratch dir. Three of its results were re-derived by the orchestrating
session before being acted on; see `README.md` § Reconciliation.)*

**3 SUCCEEDED / 4 PARTIALLY SUCCEEDED / 1 FAILED**

Tree note that conditions everything: the **primary `juniper-data` checkout is stale** —
`HEAD e769999 (#387)` while `origin/main` is `d7f4be5` (#388). The canopy checkout is behind too.
Cascor is current. Any lane reading "main today" from the juniper-data checkout is reading pre-#388
code. All juniper-data and canopy cells below were judged against `origin/main`.

## Attack 1 — "`model_fields_set` … a presence guard is portable" — **SUCCEEDED**

`bind_deployment_defaults` ends in `model_copy(update=…)` (`equities/generator.py:525-526`), and
pydantic 2.12.5 **adds** updated keys to `model_fields_set`. Probed on the real `EquitiesParams`:

```
BEFORE bind: omitted set = []            explicit_false set = ['allow_truncation']
AFTER  bind: omitted set = ['allow_truncation','max_symbols']
AFTER  bind: explicit_false set = ['allow_truncation','max_symbols']   distinguishable? False
```

The route binds at `api/routes/datasets.py:146-148`, **before** `generate` at `:186`. So a presence
guard at any of the three OR sites (`generator.py:471`, `:501`, `:552`) is a constant-`True` guard.
The construction site (`datasets.py:131`) preserves the distinction — the binder two lines later
destroys it. §4's "a one-line presence guard before binding would honour a caller's refusal" is true
only *inside the route above line 148*, i.e. not the portable remedy claimed.

Worse, the precedent §4 cites says the opposite. `csv_import/generator.py:136-140`, verbatim:

> The subtler half is why ``model_fields_set`` alone cannot carry this: **a generated client that
> serialises schema defaults sends ``max_bytes=134217728`` on every request**, which marks the field
> as explicitly set…

That read (`:151`) is safe only because it is **clamped** at `:152`. A boolean has no clamp. And the
hazard is live: `juniper-canopy/src/frontend/dashboard_manager.py:2942` pre-populates the checkbox
from the schema default and `:2972` drops only `None`/`""`, so `_collect_generator_params` returns
`{'allow_truncation': False, 'max_symbols': 14}` on **every** equities stage. A presence guard would
read canopy's untouched default as a deliberate refusal.

## Attack 2 — "one line" / "fires at Start" — **PARTIALLY SUCCEEDED**

*"Already polls at 1 Hz"* — **failed to refute.** `status_cache.py:102` `REFRESH_INTERVAL_SECONDS = 1.0`;
`:288-297` an ungated `while True` started in the lifespan (`main.py:443`), normalised through the
whitelist at issue (`main.py:183`). Not run-gated, not browser-gated. Round 37 was wrong.

*"the prompt fires at Start"* — **failed to refute.** The modal's sole opening Input is
`Input("training-control-action","data")` (`dashboard_manager.py:4805-4812`); the handler hard-gates
on `action.get("command") != "start"` (`:7745`). No poll Input, no apply-time Input.

*"one line"* — **refuted.** The whitelist is one statement (`service_backend.py:314`, `+6/-0`), but
that alone renders nothing. Surfacing it cost **28 added / 1 deleted lines of production code across
3 files** — `protocol.py:80`, `dashboard_manager.py:6963` (+6), `:7057` (+18), `:7086` (+2/-1) —
inside an +819/-28, 10-file PR that also needed `dataset_schema.py +20/-3` and 3 manifest rows.
Sub-claim "24 new tests" is imprecise: the new suite has 23 test functions collecting **28** items.

## Attack 3 — "needs a finite artifact or cascor#630 refuses first" — **PARTIALLY SUCCEEDED**

**The ordering is the other way.** In `_reload_dataset` (`manager.py:3963`): stance read `:4034`,
acceptance source `:4058-4062`, producer call `:4065`, logged `:4075`, and `self._dataset_shortfall`
written **`:4094`** — twenty-one lines *before* `_artifact_to_tensors` at `:4096`, whose finiteness
refusal is at `:3958-3960`. The acceptance path is fully exercised and observable on
`/v1/training/status` even on an artifact #630 then rejects.

The second limb **failed**: a default-parameter equities artifact is *not* finite.
`equities/defaults.py:17` `START_DATE="2000-01-01"`, `:46` `FUNDAMENTALS_FILL="nan"`, and the `"nan"`
branch fills nothing (`equities/generator.py:740-751`). Cascor's own comment (`manager.py:3947-3949`)
puts it at 43.1% non-finite.

## Attack 4 — the fourteen §4.9 rows — **PARTIALLY SUCCEEDED**

**Cascor rows at `main 44dafe0`. 007, 008, 010, 012 — refutation FAILED**; every Source cell is
valid. `.env.example` exists (zero `truncat` hits); `AGENTS.md:137`ff lists 37 `JUNIPER_CASCOR_*`
vars, not this one; `_PROJECT_API_TRUNCATABLE_GENERATORS` at `constants_api_defaults.py:139` is
`{"equities","equities_seq","csv_import"}`; the sole `dataset_type` Literal
(`api/models/training.py:235`) excludes two of them; the constant is read at exactly one site,
`manager.py:4036`. `get_metrics` (`:2824-2881`) carries no shortfall key; #633 touched no `routes/`,
no docs.

**Two rows PARTIALLY refuted:**

- **APD-CASCOR-009** — "bypasses `_reload_dataset`" is over-stated. `_auto_start_training`
  (`app.py:482-557`) does its own fetch at `:511-521`, but calls `lifecycle.start_training` at
  `:553`, which reaches `_reload_dataset` at `manager.py:2338-2340` when `_pending_dataset_config`
  is set. True of the fetch, not of the call graph. The swallow is verbatim (`app.py:556-557`).
- **APD-CASCOR-011** — "in-process `spiral`" is factually wrong: `SpiralProblem` goes over HTTP via
  `SpiralDataProvider` (`src/spiral_problem/data_provider.py:189`). The generator is hardcoded
  `"spiral"`, so the operative inertness claim stands; the words "in-process" must go.

**Data rows (against `origin/main` `d7f4be5`):**

- **APD-DATA-041 — two wording refutations.** "Monotone" is **false**: 3246 increases / 3349
  decreases raw; monotone non-increasing only above a 3e-6 tolerance. "91 distinct steps" is a
  **6-dp rounding artifact** — `nunique` is 91 at 6dp, 1997 at 8dp, 6157 raw; the economically real
  figure is **56** down-steps. The look-ahead *core* survives, and more sharply: a window ending
  2023-12-29 has `close/adj_close = 1.01131927` on its **last** row, and Yahoo anchors at the
  download date, so narrowing the window does not remove it. `close` is fully split-adjusted even at
  `auto_adjust=False`, so splits cancel and the channel is pure cumulative dividends — the
  "past-splits artifact" alternative is refuted. `auto_adjust=False` at `generator.py:841`
  **overrides yfinance 1.4.1's own default of `True`**. Exploitability is *not* shown:
  `corr(ratio, next-day return) = 0.0036`.
- **APD-DATA-043 — the `median > 0` clause is inert. PARTIAL REFUTATION SUCCEEDED.** For an all-zero
  series the bounds are `[0, 0]` and every zero satisfies both, so the filter keeps them whether or
  not the guard runs. Removing the guard changes the kept set for exactly **one** of 485 payloads
  (DDOG) and makes it worse. The 61/485 figure reproduced **exactly**. Bonus, which makes the row
  *worse* than written: for PSKY the filter fires and deletes the only correct count
  (`[1000, 1000, 1071666977]` → median 1000 → bounds `[10, 100000]` → delivers `[1000, 1000]`) — and
  that contradicts APD-DATA-044's "passes every guard".
- **APD-DATA-044 — BRK.B is not a placeholder. PARTIAL.** The series is a real, correctly declining
  **Class-A** count; the defect is that one CIK serves both classes while `market_cap` prices it
  against the Class-B close. FOX/FOXA `val=1` confirmed literal. The "silent through every guard"
  claim is **confirmed by execution**: all six pass `_fetch_shares` with `quality=point_in_time`, and
  `_apply_incomplete_policy` returns `NO REFUSAL`, `quality_meta: None`. Delivered `market_cap`:
  TAP/DDOG/CVNA 0, FOX 60, FOXA 67, PSKY 10,980, BRK.B 442,769,108 against a truth of ~1.1e12.

**Severity — two indefensible gradings.**
- **`APD-CASCOR-010 = E` is under-graded.** `_build_dataset_shortfall`'s own docstring
  (`manager.py:3712-3714`) says the contract requires accept and drop to annotate progress,
  **metrics** and results. A declared contract met on two surfaces of three is C by the same logic
  that grades `-007` as C.
- **`APD-DATA-044 = R` is not defensible; it should be C.** The comparator is three rows up:
  `APD-DATA-038`, graded **C**, is the same sentence with "unrescued" for "placeholder" — and -044 is
  worse, because a plausible value cannot be caught by the `SHARES_QUALITY_UNRESCUED` path -038
  installed. `R` here means a missing bound; this is a wrong number in a shipped feature column.
- Not indefensible: `-008 = M`, `-011 = E`, `-041 = C`, `-043 = C`, `-007 = C` all match precedent.

**A contradiction inside §4.9's own preamble.** It says canopy findings "live in the canopy E2E
ledger (`F-CANOPY-*`), not here", then records them in an **unarchived draft handoff**.
`grep -rln INFRASTRUCTURE_FIELDS notes/` returns the register alone.

## Attack 5 — the arithmetic — **FAILED**

My own parser, which section-maps every heading and reads only a §4.x row's **status cell**,
reproduces the document exactly: 110 §4 rows; 96 primer / 14 post-primer; 82 FIXED (79 / 3); 28 OPEN
(17 / 11). No vacuous-agree vector fires: `ids with a row in §5 but NOT in §4 → []`; whole-line
`**FIXED` minus status-cell `**FIXED` → `[]`; `ROW_RE` matches 189 raw lines but **110 unique ids**;
`prose − fixed → []`, `fixed − prose → []`, `§5.1 − fixed → []`; tables after §5.2 → 0.

**But an adjacent required test is red.** The register cites a handoff not in the archive, so
`tests/test_thread_handoff_archive.py::test_top_level_note_references_to_thread_handoffs_resolve`
**FAILS today**. §1's verify block lists only the two checkers and the grep, none of which sees this.
A successor following §1 verbatim reads green on a register that reddens CI.

## Attack 6 — §5.2's "re-applying on main's file does NOT clear it" — **SUCCEEDED**

Scratch git repo, using the writing session's own captured files. Experiment 1 (base + entry, merged
against main) reproduces the observed DIRTY state, validating the reconstruction:

```
=== EXPERIMENT 1: merge main into (base + entry) ===  exit=1
CONFLICT (content): Merge conflict in CHANGELOG.md
```

Experiment 2 is the exact operation §5.2 says fails — main's file + the entry, merged against main:

```
=== EXPERIMENT 2: merge main into (base + entry RE-APPLIED ON MAIN'S FILE) ===
exit=0   tree=2b53098a873ebf0ffe9062944732af787c1394db
--- conflict report ---            (empty)
result vs cascor_changelog_merged.md diff lines: 0
```

**Clean, and byte-identical to the intended file.** Git's 3-way merge takes the identical
release-move hunk once from both sides and applies only the branch-side entry; the merge base being
old is irrelevant when both sides carry the same change. §5.2's doctrine is **false**, and the
API-rebase-through-a-temp-ref ceremony was unnecessary for the CHANGELOG half.

**"A force-update alone may fire no CI" is contradicted by this episode's own receipts.**

```
runs?head_sha=aecd0bb8… → total_count: 7   (all seven contexts, 2026-09-09T00:35:28Z)
   model success | CodeQL success | Base-Branch Guard success
   CI/CD cancelled | Sequence Safety cancelled | Conformance cancelled | Golden Regression cancelled
runs?head_sha=5179bca2… → total_count: 12  (7 pull_request runs, all success, 00:35:49Z)
```

The force-update fired **all seven**; four were cancelled by concurrency 21 seconds later.

**And §2's account of the branch is stale.** `gh pr view 633 --json commits` shows **nine** commits,
final head `0c1a0f84`, including two ordinary **`Merge branch 'main'`** commits — i.e. the DIRTY
state was later cleared by a plain merge, the very thing §5.2's doctrine says will not work.

## Attack 7 — the register's §2 note — **SUCCEEDED**

**The sentence under attack:**

> *(2026-09-09: … they do end the empty set: the §4.9 rows marked actionable (`APD-DATA-039`'s
> cache-key half, `APD-CASCOR-009` / `-010` / `-012`) are the first a session may work without asking
> first, because the Overtoad-issued round-37 handoff listed them as remaining work.)*

**It contradicts three of the register's own §2 rules, quoted verbatim:**

> **Operating rule: all three shapes park a row.** … The conservative reading can only ever *prevent*
> unilateral action, never license it, so it is the one that fails safe.

> **This does not license the reverse, either.** Unparked ≠ actionable.

> **As of 2026-09-03 the set of rows a session may action without asking the Overtoad first is empty**,
> and that is a fact about how far this register has been worked, **not an obstacle to route around**.

The note asserts exactly the unparked-⇒-actionable equivalence §2 rejects — with `APD-DATA-019`
standing in the *same paragraph* as the living counter-example. §2 enumerates three park shapes, all
of them *register* sentences; "a handoff listed it" is a fourth shape invented here, and it is a
licensing mechanism, which §2 says the rule set does not contain.

**"Owner-issued" holds only for the merge, not the content.** The round-37 handoff's commit is an
Overtoad-merged archive of a machine-generated document produced under the thread-handoff protocol —
not an Overtoad instruction. Round 37's own **§3 "Owner rulings — do not re-litigate"** table has eight
dated rows and **not one concerns any of the four**.

### Per-row verdict, against the exact round-37 §0 text

**`APD-CASCOR-009`, `-010`, `-012` — listed, but the authority is a PR body.** Round 37 §0.5 reads:

> **5. Four cascor follow-ups, filed in cascor#624's PR body and still unbuilt:** …

So the three are genuinely enumerated — **the "listed as remaining work" half is TRUE for these
three.** But the stated provenance is a prior Claude session's own PR text: a to-do list a machine
wrote about itself.

**`APD-CASCOR-012` additionally rests on a claim the round-38 document has just retracted** — its own
§4 grades that bullet *"Literally false"*. Authorization drawn from a sentence the same document
declares false. **Circular; -012's licence should not stand on this.**

**`APD-DATA-039` — NOT listed as remaining work at all. The weakest of the four.** Round 37 §0.9 is a
hazard description with three consequence bullets; it proposes no fix, asks for no work, assigns no
Overtoad, and is in neither §0.5's "still unbuilt" list nor §0.11's parked list. Worse, the round-38
document's **own §0.4** places that very bullet under *"Owner decisions, each blocking a row — do not
action without a ruling."* **Unsupported, and self-contradicted by the shipping document.**

**All four, additionally: round 37 could not have unparked rows that did not exist.** §0.11 says the
other 16 open rows *"are PARKED and need Overtoad unparking before any session may action them"*. The
§4.9 rows were filed 2026-09-09, two days after round 37 was written. Retroactive
self-authorization, and §0.11 is round 37 saying the opposite of what the note attributes to it.

**Recommendation:** not defensible as written. The cleanest fix is to delete the licensing clause and
let the four rows carry ordinary `parked: Overtoad decision` sentences until the Overtoad rules.

**One more inconsistency:** §0.2 of the handoff tells the successor to build "one PR" from four
bullets **including** the `-011` flag — which §4.9 **parks** as a design question.

## Attack 8 — "0 empty, three all-zero, six placeholders" — **PARTIALLY SUCCEEDED** *(downgraded)*

**Retraction first.** My initial scan reported "at least five more placeholder CIKs". **That was
wrong.** I scanned *raw payloads*; the row is about what `_fetch_shares` **delivers**. The median
filter drops a leading `100` or `1` when the median is ~7e8, so those series arrive clean. Over all
485 *delivered* series, the union of `latest == 0` and `0 < latest < 1e6` is **exactly the six
named**; widening to `< 5e6` adds only NVR (a genuine count). **The six are exhaustive.** Same
correction to TAP: 5 raw points dedup to **3 delivered**.

**What survives:**
- **"0 of 485 empty" — CONFIRMED** under four independent definitions, including the generator's own
  predicate at `generator.py:951`.
- **"three all-zero" — right at the delivered level, wrong at the payload level (2).** Only TAP and
  CVNA are all-zero payloads; DDOG holds `78,180,606 @2018-12-31`. Three is correct under two other
  readings: 3 payloads have `median == 0`, and 3 tickers deliver `total_shares == 0` for **100%** of
  rows after `_condition_one` (DDOG's real value is unreachable because both facts were first filed
  the same day and the later `end` wins).
- **The surviving defect is the noun.** "Six **cached payloads**" asserts payload-level counts the row
  does not have. Restate at the delivered level and quote a predicate rather than a list.

## New findings not in the document

1. **cascor#633 merged with `Test (Python 3.12)` RED**, step "Run unit tests with coverage (incl. src
   drift-guard)", completed 17:46:58Z; the PR merged at 17:57:06Z.
2. **A stale-annotation defect covered by none of the six cascor rows.** `self._dataset_shortfall` is
   written at exactly one line (`manager.py:4094`) and never cleared. A run started through the
   inline path with no pending dataset config keeps the **previous** run's annotation, naming a
   foreign `dataset_id`. Same family as `APD-CASCOR-007`.
3. **`Settings.auto_dataset` (`settings.py:574`) is a bare `str`, not a Literal**, so
   `JUNIPER_CASCOR_AUTO_DATASET=equities_seq` *does* reach juniper-data — via `_auto_start_training`,
   which never consults `_PROJECT_API_TRUNCATABLE_GENERATORS`. Strengthens `-008` and `-009`.
4. **Cascor's own comment `manager.py:3951-3953`** — "flat `equities` requests are post-2009" — is
   false for the canopy path, whose `start_date` widget is pre-filled with `"2000-01-01"`.
5. **A staleness class larger than -044.** 26 of 485 payloads deliver a last as-of date before
   2025-06-01, forward-filled for years — SPG `@2009-09-30` (16.7 years), CMCSA `@2009-12-31`, V,
   UPS, CME, ACN, MA, F, IBKR, REGN, NWS/NWSA, HSY, NKE. Median last-as-of 2026-04-24; 14 predate
   2015. Separately, AAPL carries **2401 of 6642 rows (36.1%) at `total_shares = 0`**, because SEC
   XBRL begins ~2009 while the default price window begins 2000. No §4.9 row covers this.
6. **The PSKY inversion** (attack 4): the filter deletes the only correct count and keeps the
   placeholders.
7. **Two canopy findings are recorded nowhere durable.**

## What the evidence cannot support

- Whether the `Test (Python 3.12)` failure was the drift assertion or coverage — the log was not read.
- Whether the six placeholder payloads are placeholders *at SEC* or cache artifacts: no network.
- The `adj_close` step dates could not be cross-checked against a dividend column.
- Harm magnitude of the `adj_close` channel: `corr(ratio, next-day return) = 0.0036`; the -0.871
  correlation with `next_close` is a time trend, not edge.
- The 43.1% non-finite figure is **cascor's recorded number**, not my measurement.
- Round-37's line-number corrections: the frozen SHA is not the local checkout's state.
- **Three §4 corrections I checked are correct and I failed to refute them:** the ml#1813/#1818
  timings, the three juniper-data stash entries, and the three-SHAs / six-PRs miscounts.
