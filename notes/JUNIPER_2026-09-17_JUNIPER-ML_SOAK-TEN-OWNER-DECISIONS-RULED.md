# The pointer-follow soak's ten open owner decisions — RULED

**Project**: juniper-ml
**Date**: 2026-09-17
**Status**: decisions of record — all ten ruled by the owner in one interactive pass
**Supersedes**: §6 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md`, and decision #7 of `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`
**Companion, not superseded**: `notes/JUNIPER_2026-09-16_JUNIPER-ML_SOAK-OWNER-RULINGS-AND-WHAT-THEY-CHANGED.md`

---

## 0. Why this document exists, and how it sits beside the 09-16 record

The arc reached a state where **every remaining item needed a ruling and none could be
advanced without one**. Eight decisions sat in the 2026-09-09 handoff's §6, decision #7 of
the shared-session-memory plan had a fired trigger and no action for ten days, and §15.3's
pre-registration was unadjudicated.

They were ruled in one pass on 2026-09-17. This is the record.

**`notes/JUNIPER_2026-09-16_JUNIPER-ML_SOAK-OWNER-RULINGS-AND-WHAT-THEY-CHANGED.md` (ml#1952)
already records four rulings from 2026-09-15/16, and it stands unchanged.** Two of them are
D2 and D5 here, reached independently and identically; this document notes that per decision
rather than silently absorbing it, and adds nothing to their implementation. Its other two —
wire the contamination screen report-only, and "apply the escalation ladder" (where **no
action was due** and the implementation was withdrawn in full) — are outside the ten and are
not re-opened here.

Read that document for what the instrument does; read this one for what the owner decided.
Where both speak, they agree.

## 1. The rulings

| # | decision | ruling | state |
|---|---|---|---|
| D1 | Does the per-probe campaign run? | **Named probe only, on request** — no default or timer campaign | policy; recorded here |
| D2 | Which retrieval standard binds? | **Mechanism-checked** — 24/43 = 55.8% as published, 23/42 = 54.8% post-D5 | **implemented, ml#1952** — schema only |
| D3 | May `--force` run past a terminal verdict? | **Yes, narrowly**: named `--probe-id`, one run per invocation, reason logged | **implemented here** — `force_scope_refusal()` |
| D4 | Pooled or post-intervention verdict? | **Keep pooled** | **no change needed** — already pooled |
| D5 | Does the ledger leak invalidate its run? | **Invalidate the one demonstrated content read** | **implemented, ml#1952** |
| D6 | Index-recovery as a scored outcome? | **No** — record in `--note` only | no change needed |
| D7 | P06's discriminator | **Leave it, flagged** | no change needed |
| D8 | Adjudicate §15.3's pre-registration | **Insufficient data**; "materially non-zero" was never defined | recorded here |
| D9 | Keep A's skills as a later probe? (plan #7) | **Closed — no probe** | recorded here + plan updated |
| D10 | Does BET-FAILING feed relocation policy? | **Continue, and record WHY it is safe** | recorded here |

## 2. The reasoning that is worth keeping

### D1 — named probe only

§4.1 of `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` shows the
n≈8–10 campaign **cannot resolve its targets**: P23 needs n≥31, and inside 8–10 the Wilson
resolving threshold never leaves `k≤1`, so runs 9 and 10 *lower* the chance of an answer.
`--probe-id` stays available for a specific relocation decision; the default and timer paths
do not run.

### D2 — mechanism-checked, and what it does NOT license

Binding standard is the mechanism-checked reading — **24/43 = 55.8%** [0.411, 0.696] as the
re-audit published it, **23/42 = 54.8%** [0.399, 0.688] once D5 removed its row.
**ml#1952 shipped it as a schema change only, and reverted two data edits made on its
authority — correctly.** §7 of
`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md` lists
*"which standard binds"* and *"whether the §4 rows are re-scored"* as **separate** owner
questions. Only the first was ruled. **The standard binds prospectively; the historical
corpus is untouched.**

That separation was not visible when D2 was put to the owner — the question as framed
implied the corpus would follow. It does not, and re-scoring the §4 rows remains unruled.

**A consequence found by ml#1952 that no earlier document records:** a downward re-score
*desensitises* the rung-3 area detector, because `pooled_miss = 1 - rate` is the Bonferroni
null (measured: area `worktrees` p 0.51675 → 0.61290), and it entrenches — consecutive
follows needed to reopen went 3 → 10 with no new data. Any future re-scoring ruling must
weigh that.

### D3 — `--force`, narrowly, and enforced rather than written down

D1 authorises named-probe runs, and a named probe under a terminal verdict cannot run
without `--force`. So "never" was incompatible with D1. Scope: explicit `--probe-id`, **one
run per invocation**, reason recorded. The default and timer paths keep refusing — which is
what makes this narrow rather than a repeal.

**Writing that down would not have held, and the gap is specific.** Every path refuses today
*only* because the verdict is terminal, so `--force` is the sole way any run happens — and a
bare `--force` dispatched `dispatch(None)`, the least-covered-first campaign D1 declined.
The override meant to authorise **one** run re-opened the **default** one. D1 was
unenforceable while that was true.

Implemented as `force_scope_refusal()` in `util/soak_run_probe.py`: `--force` requires
`--probe-id` **and** a non-blank `--reason`, refusing with `RC_REFUSED` (3, the code the
systemd unit whitelists — a by-design refusal must not fire `OnFailure=`). "One run per
invocation" needs no check; the wrapper has always dispatched exactly one.

Two details that are load-bearing rather than tidy:

- **The check runs BEFORE both spend controls.** They return `False` on `force` — that is
  what `--force` *is* — so a check placed after them is unreachable, and an unscoped
  override would sail through to dispatch.
- **`forced` is written to `meta.json` unconditionally, as a bool.** Recording it only on
  forced runs would make "not forced" and "forced, key lost" the same absent key to every
  later reader, and attributability after the fact is the whole point of logging a reason.

`tests/test_soak_run_probe_stopping_rule.py` pins both — `ForceIsNarrowedToANamedProbe` and
`ForceScopeRefusalIsReachedBeforeTheSpendControls`. Two existing cases that drove a bare
`--force` were updated to the scoped form: that was the contract then, and is not now.

### D4 — pooled

§15.4 forbids pooling, which makes the post-only slice look like the correct corpus. It is a
trap: post-only reads `IN-PROGRESS` from an **OR of two n-gates** (`runs < 35` **or**
`distinct probes < 15`; at 8 runs over 7 probes both fire), so wiring the stopper to it
would make the spend control stop refusing — ~27 billed runs, no `--force`. That directly
contradicts D1.

### D5 — one row, and it did not move the verdict

8 runs *touched* `reports/soak/pointer_follow_soak.jsonl`; **exactly one read its contents**.
That row — `P18-health-interval-non-positive`, 2026-08-22, recorded **follow** — is
invalidated. Corpus 43 → 42, `status` now
`BET-FAILING seeded=42/35 rate=59.5% ci=[0.445, 0.730]`. It removed a **follow**, so the
verdict is reinforced, not destabilised — and it could not have moved in any case, since
every candidate standard's Wilson upper is below 0.75.

Every derived figure moved with it, and they were **re-run, not adjusted by hand**
(`util/ad-hoc/2026-09-17_soak_post_ruling_recount.py`):

| figure | 43-row | 42-row |
|---|---|---|
| pooled follow rate | 26/43 = 60.5% [0.456, 0.736] | **25/42 = 59.5%** [0.445, 0.730] |
| pre-intervention | 24/35 = 68.6% [0.520, 0.814] | **23/34 = 67.6%** [0.508, 0.809] |
| post-intervention | 2/8 = 25.0% [0.071, 0.591] | unchanged |
| mechanism-checked (D2) | 24/43 = 55.8% [0.411, 0.696] | **23/42 = 54.8%** [0.399, 0.688] |
| answers correct | 41/43 = 95.3% | **40/42 = 95.2%** [0.842, 0.987] |
| retention as ORIGINALLY recorded | 74.4% | **73.8%** (31/42) [0.589, 0.847] |

The per-probe intervals `docs/REFERENCE.md` quotes are unaffected — P18 is not among them —
and **both remaining misses are still P15**, which is what D9 turns on.

### D8 — the pre-registration cannot be adjudicated, and that is the finding

§15.3 predicted rung 1 would not move the follow rate on **P14 / P15 / P19 / P23**.
Post-intervention they went **0, 0, 0, FOLLOW** — one of four moved, and P23's follow
survives the mechanism standard. But n=4 and `wilson(1,4) = [0.046, 0.699]`, and **§15.3
never defined "materially non-zero"**. Neither outcome is reachable from this evidence.

Recorded as insufficient rather than resolved either way. The undefined term is the lesson:
a falsification condition that does not state its threshold cannot be adjudicated, and
re-reading a fired condition as noise is the move pre-registration exists to prevent.

### D9 — decision #7 closed

The trigger fired (`BET-FAILING`), and that **licensed revisiting #7 without answering it**.
The soak measured retrieval from `docs/REFERENCE.md`; option A's **skills carrier has never
been probed**, so "the pointer bet failed, therefore skills" was never an available
inference. All three reasons A was rejected — worst-case context, compaction, and
`in_docs_scope` returning False for every `.claude/` destination — are untouched by a failed
pointer bet.

And the harm #7 hedged against did not materialise: **40 of 42 answers correct**, both
failures on P15, a probe the ledger files under *"the discriminator is stricter than the
source rule"*. Closed: no skills probe.

`util/soak_ledger.py`'s `status` message is updated accordingly. It told every operator to
"revisit owner decision 7" — completed work — and that wording is what left the instruction
unactioned for ten days.

### D10 — relocation continues, for a stated reason

Relocation continues and **"never re-inline" stands**. Policy now records *why* it is safe:
**facts are recovered from code, not because pointers are followed.** The bet failed on
pointer-following; the outcome is nonetheless 40/42 correct.

**Retention and correctness are the same number by construction** — retention is the
fraction that did not miss, a miss is in practice a wrong answer, 40/42 = 95.2%. They must
never be cited as two corroborating figures, and retention is one-way besides
(`RESCORE_OUTCOMES = ("source-recovered",)`; the corpus was **73.8%** as originally
recorded).

## 3. What remains open

Ruling these ten does **not** close the arc. Still open, and untouched here:

- **The predictor gap.** §8.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`
  calls it *"the actual blocker to decision support"*. All three candidates were refuted in
  `notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md` at a sample size
  where a perfect split would have been found. **Nothing predicts which stratum a new fact
  lands in**, so D10's policy cannot be narrowed per-fact.
- **Whether the §4 rows are re-scored** (D2's sibling question, never put to the owner).
- **Item C** — `analyse()` has no era filter. Building it is inert; wiring it was D4, now ruled.
- **Item D** — no soak script reads `tool_result`, so half of what §4 calls a FOLLOW is
  invisible. Changing that changes the standard D2 just fixed.
- **Whether to re-run P18**, raised by §5 of
  `notes/JUNIPER_2026-09-16_JUNIPER-ML_SOAK-OWNER-RULINGS-AND-WHAT-THEY-CHANGED.md`. D5's
  invalidation left P18 at 1 run and the corpus at exactly `MIN_DISTINCT_PROBES` — **live
  margin zero**. D3 removes the *procedural* obstacle that question was blocked on
  (`--force` past a terminal verdict is now authorised, narrowly), so what remains is only
  whether the billed session is worth spending. That is still the owner's, and it is the one
  place where these rulings make a previously-blocked action possible.

**D3 does NOT close the fail-open cliff**, and it should not be read as doing so. That cliff
is `analyse()` testing `IN-PROGRESS` *above* the terminal branches: drop distinct live probes
below `MIN_DISTINCT_PROBES` and a terminal verdict becomes `IN-PROGRESS`, at which point
`refuses_terminal_verdict` stops refusing — with **no `--force` involved**, so
`force_scope_refusal` never fires. `cmd_invalidate`'s guard (ml#1952) is what covers it.

## 4. Changed by this document's PR

| file | change |
|---|---|
| `notes/JUNIPER_2026-09-17_JUNIPER-ML_SOAK-TEN-OWNER-DECISIONS-RULED.md` | **new** — this document |
| `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` | decision #7 row: *Optional, deferred* → **CLOSED**, with the reasoning |
| `util/soak_ledger.py` | the `BET-FAILING` next-action message no longer sends operators to redo D9 |
| `util/soak_run_probe.py` | **D3 enforced** — `force_scope_refusal()`, `--reason`, `forced`/`force_reason` in `meta.json` |
| `tests/test_soak_run_probe_stopping_rule.py` | 11 new cases; 2 existing `--force` cases moved to the scoped form |
| `docs/REFERENCE.md` | D1/D2/D3/D4/D6/D7/D10 on the operator surface; post-D5 figures; five shipped errors below |
| `util/ad-hoc/2026-09-17_soak_post_ruling_recount.py` | **new** — re-derives every figure `docs/REFERENCE.md` quotes |

**Five errors in shipped `docs/REFERENCE.md` corrected at source**, found while applying the
rulings rather than looked for. Four of the five are the same shape — **a section updated
while an older statement of the same fact was left standing elsewhere on the page** — which
is what a 800KB reference does to anyone who edits only where they are looking:

1. The era table's single **"terminal?"** column read *yes (`BET-FAILING`)* for the
   post-only slice while the paragraph directly below it said that slice reads
   `IN-PROGRESS`. Both are true of different questions — the interval clears the boundary;
   `analyse()` never reaches the boundary test — and one column cannot say both. Split.
2. **Exit codes contradicted themselves four lines apart**: *"`2` … or a real-run terminal
   refuse"* against the `RC_REFUSED = 3` paragraph above it and the unit's
   `SuccessExitStatus=3`. An operator or unit author acting on the `2` gets the failure
   #1884 built the code to prevent.
3. The `IN-PROGRESS` explanation said *"purely the `runs < TARGET_PROBE_RUNS` n-gate"*. It
   is an **OR of two** — at 8 runs over 7 probes the distinct-probes gate fires as well —
   and "purely" invites closing the wrong one.
4. **Two bullets in the same systemd list contradicted each other.** One says
   `SuccessExitStatus=3` is set (true, ml#1884); two below it, *"`Type=oneshot` with **no**
   `SuccessExitStatus=`… every timer firing marks `failed`"* — the pre-#1884 state. An
   operator reconciling them by removing the line reintroduces the strike-per-6h failure.
5. **"Known-not-fixed" described a fail-open that had been closed for a week.** It said
   `DEGRADED` and `NO-SEEDED-DATA` *"pass the spend control"* and closing it was *"out of
   scope for #1690"* — while the section two above it documents `refuses_unusable_verdict`
   (2026-09-10) refusing exactly those. The genuine residual is narrower and is now stated
   as such: an **unclassified** verdict token still fails open, and
   `LedgerVerdictsAreAllClassified` is what catches that. The section also now names the one
   fail-open that really is open — `analyse()` testing `IN-PROGRESS` above the terminal
   branches, live margin zero.

**Not changed**: `reports/soak/pointer_follow_soak.jsonl`, `conf/soak_probes.json`. **No
probe was run**, and no historical row was re-scored (see D2).
