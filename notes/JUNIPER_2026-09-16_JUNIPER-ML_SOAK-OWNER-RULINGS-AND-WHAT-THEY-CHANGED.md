# Soak arc — owner rulings 2026-09-15/16, and exactly what each changed

**Date**: 2026-09-16
**Repo**: juniper-ml
**Author**: Paul Calnon
**Status**: RECORD of owner rulings and their implementation. Validated by independent consensus,
which **rejected one ruling's implementation outright** (§4) and narrowed another (§1).

Ledger of record: `reports/soak/pointer_follow_soak.jsonl`.
Protocol: [`JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md).
Evidence the rulings were taken against:
[`JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`](JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md).

---

## 0. Net effect on the instrument

| | before | after |
|---|---|---|
| `soak_ledger.py status` | `BET-FAILING seeded=43/35 rate=60.5% ci=[0.456, 0.736]` | `BET-FAILING seeded=42/35 rate=59.5% ci=[0.445, 0.730]` |
| valid observations | 43 | **42** |
| margin to the 0.75 boundary | 0.0137 | **0.0204** |
| ledger rows appended | — | **exactly one** (an `invalidate`) |

**The verdict did not move, and no ruling could have moved it**: every candidate standard's Wilson
upper bound is below 0.75 (0.736 / 0.730 / 0.696 / 0.688 / 0.567).

---

## 1. Which retrieval standard binds — RULED: MECHANISM-CHECKED

Handoff §6 item 7. The menu, all recomputed with the repo's own `wilson()`:

| standard | rate | Wilson 95% | margin |
|---|---|---|---|
| as recorded | 26/43 = 60.5% | [0.4558, 0.7363] | 0.0137 |
| **mechanism-checked** | 24/43 = 55.8% | [0.4111, 0.6957] | 0.0543 |
| input-only floor | 18/43 = 41.9% | [0.2838, 0.5667] | 0.1833 |

Mechanism-checked is not a third standard: it applies the protocol's own §4 definition
(inputs ∪ results) and then discards hits that are not the destination document at all.

**What shipped: the schema change only.** Expressing the standard requires moving a `follow`
DOWN, and `cmd_rescore` rejected anything whose outcome was not `miss`. `RESCORABLE_FROM =
("miss", "follow")` now permits it; `RESCORE_OUTCOMES` stays `("source-recovered",)`.

**What did NOT ship, and why.** §7 of the recovery note lists item 1 (which standard binds) and
item 2 (**whether the §4 rows are re-scored**) as *separate* owner questions. Only item 1 was
ruled. Two re-scores were made on item 1's authority and **reverted 2026-09-16** on the owner's
ruling — *keep the widening, revert the edits*. The standard is therefore **expressible and
prospectively binding**; the historical corpus is untouched pending an item-2 ruling. Revert
script: `util/ad-hoc/2026-09-15_soak_decisions/revert_unauthorised_rescores.py`.

### 1.1 The widening is NOT "monotone in the safe direction" — three consequences

An earlier draft claimed it was. Consensus refuted that, measured. What is actually guaranteed:
no re-score can produce a `follow`, so none can raise `rate` or turn a failing verdict into
`HOLDS-AT-`. What runs the other way:

1. **It desensitises the rung-3 area detector.** `pooled_miss = 1 - rate` is the null for the
   Bonferroni area test, so lowering `rate` *raises* the null and makes the test *less* likely
   to fire. Measured: area `worktrees` (2/4) moved p 0.51675 → 0.61290 across the two re-scores.
   Latent only because 2 < `AREA_MIN_MISSES`.
2. **It entrenches a terminal verdict.** Consecutive follows needed to lift the Wilson upper back
   over the boundary went **3 → 10** with no new data — and the probe refuses to generate that
   data on a terminal verdict without `--force`.
3. **`retention` cannot fall.** `follow → source-recovered` leaves it unchanged, so retention only
   rises or holds while `rate` can be driven arbitrarily low. A reporting hazard, not a control
   hazard; nothing gates on retention.

The 2026-08-31 guard's wording is *"any inconvenient row to any **convenient** column"* — full
stop. An earlier draft of this work inserted the gloss *"and convenient means verdict-rescuing"*,
which appears nowhere in the original, and then showed the change fell outside the gloss. That
gloss is withdrawn. Widening the margin that keeps a billed study terminal **is** a convenient
column under the guard's actual wording, which is why item 2 remains the owner's.

---

## 2. Does the ledger leak invalidate its runs — RULED: only the demonstrated content read

Handoff §6 item 8. **Implemented.** Denominator 43 → 42.

The row: `e504a64c-032b-4c27-9470-d3b53725ad91`, P18-health-interval-non-positive,
2026-08-22T21:41:09Z, recorded `follow`.

**Identification was measured, not inferred.** Two P18 rows exist, both `follow`, both dated
2026-08-22, and §5 does not disambiguate them. The binder's `ledger=N` column cannot settle it —
`LEDGER_MARKERS` includes the bare filename stem, so it is not a content count. The screen's
three-valued `ledger_exposure` (keyed on `"obs_id"`, `"scored_by"`, `"discriminator_ok"`,
`"miss_class"` — fields that appear only if a ledger *record* came back) gives:

> **8 runs touched the ledger; exactly 1 read its contents; 7 saw the filename alone.**

independently reproducing §5. Probe: `util/ad-hoc/2026-09-15_soak_decisions/which_run_read_the_ledger.py`.

`invalidate` is the correct verb: it means *"the observation should never have counted"*, it is an
append (the original row stays), and precedent covers non-probe-defect retirement —
`dd1e25ba` retires a CONTAMINATED run, `6fc75bb0` a MIS-SCORED one. `cmd_invalidate`'s docstring
said *"whose PROBE was defective"* and was already false when written; corrected.

### 2.1 This created a fail-open cliff, now guarded

`analyse` tests the `IN-PROGRESS` branch **above** the terminal ones, and `probes_run` is built
from in-scope rows — so an invalidate that drops distinct live probes below
`MIN_DISTINCT_PROBES` converts a terminal verdict to IN-PROGRESS, at which point
`refuses_terminal_verdict` returns False and **the spend control stops refusing billed runs**.

Live margin after this invalidation: distinct probes **= 15 = `MIN_DISTINCT_PROBES` exactly**, and
P18 is down to **one** live run. One further invalidation of that row opens the gate.

**Ruled 2026-09-16: add a `--force` guard.** `cmd_invalidate` now refuses when the invalidate
would flip the verdict *into* `IN-PROGRESS`, naming the transition, unless `--force` is passed.
It tests the transition rather than membership of a terminal set, because that set lives in
`util/soak_run_probe.py` and copying it down would be a second definition free to drift.

**`invalidate`, not `rescore`, is the non-monotone verb.** The 2026-09-15 safety analysis
discussed only `rescore` and never mentioned this.

---

## 3. Contamination screen — RULED: wire it REPORT-ONLY

Item F. `conf/soak_probes.json`'s `_README` has said since the pilot that scoring MUST run the
screen; nothing did. **Implemented** as `contamination_screen()` in `util/soak_run_probe.py`.

- **Report-only**, because the screen's own retrieval verdict is a bare `DEST in blob` substring
  test that credits a `grep -rln` filename sighting, a sibling repo's same-named file, and a
  match inside the ledger's own JSON. Gating on it would invalidate genuine runs today.
- **Output goes to `status.json` and operator stdout, never `scoring_packet.md`.** The packet
  already redacts corpus progress because the scorer has no stake in it; a contamination field in
  front of the scorer is the same leak, and shipping one was the specific defect that sank the
  2026-09-12 `ledger_touched` attempt. Pinned by
  `tests/test_soak_run_probe.py::test_the_screen_never_reaches_the_scoring_packet`.
- **The screen's naive `dest_hits` IS carried — on the operator's record only.** Disagreement
  between it and the mechanism-checked channel is the cheapest available flag for *"this row needs
  a mechanism check"*, and comparing the two is how P21 and P24 were found at all.
- **It catches `BaseException`, not `Exception`.** The call sits ahead of `status.json`,
  `answer.md` and `scoring_packet.md`; the screen lives under `util/ad-hoc/`, which `ci.yml`
  notes is not pre-commit-lint-gated, and `exec_module` runs its module body. One import-time
  `sys.exit` there raises `SystemExit`, which `except Exception` does not catch, and a
  900-second billed run would lose its entire artifact set.
- **A screen that cannot run reports `available: False` with the reason.** Absent keys read as
  clean; a check that could not run is not a pass.

---

## 4. Escalation ladder — RULED "apply the ladder only"; NO ACTION WAS DUE

**The implementation was withdrawn in full.** This is the substantive finding of the round.

The reasoning that produced an action was wrong four ways, and consensus caught all four:

1. **Rung 1 for P15 was already executed on 2026-08-31.** §15.2 of the ledger protocol records
   four index rows added to the auto-memory `MEMORY.md`, P15 among them, and that row is **live
   today**.
2. **Every P15 miss predates it.** The three miss rows are 2026-08-21T21:15:04Z,
   2026-08-22T21:41:09Z and 2026-08-22T21:49:00Z. The **only** post-intervention run,
   2026-09-04T09:50:23Z, scored `source-recovered` — the fact *was* obtained. **The ladder
   already worked.**
3. **The instrument raised no escalation.** `analyse()["escalations"] == []`. P15 is severity
   `reference` (no rung 2), and area `worktrees` has 2 misses against `AREA_MIN_MISSES = 3` (no
   rung 3). The action was manufactured by pooling pre- and post-intervention runs, which §15.4
   forbids in terms, and §15.3 says the ladder must not be re-run on that reasoning.
4. **The implementation re-inlined the fact.** P15 declares
   `must_be_absent_from_source: ["converge", "liveness probe"]`, and the added `AGENTS.md` row
   contained *"CONVERGED"*, which lowercases to contain `converge`. `soak_ledger.py verify-probes`
   went red — and `ci.yml:621` runs it. By the repo's own residency gate the row **was**
   re-inlining, the thing the plan forbids absolutely, and it destroyed P15 as a probe.

**Correct disposition: nothing is due.** The ladder is discharged for P15 and the post-intervention
evidence shows the intervention worked. Any further rung-1 action for P15 is a **new** owner
decision, belongs in `MEMORY.md` (which the residency gate does not read), and must be worded to
survive `must_be_absent_from_source`.

---

## 5. What is still the owner's

- **§7 item 2** — whether the two §4 rows are re-scored. The standard binds prospectively; the
  historical corpus is unchanged until this is ruled.
- Handoff §6 items 1–6, unchanged.
- Whether to re-run P18 to restore the distinct-probe margin (costs a billed session and needs
  `--force` past a terminal verdict, which is §6 item 5).

## 6. Documents changed

**Modified**: `util/soak_ledger.py`, `util/soak_run_probe.py`, `tests/test_soak_ledger.py`,
`tests/test_soak_run_probe.py`, `reports/soak/pointer_follow_soak.jsonl` (one appended
`invalidate`).
**Added**: this file; `util/ad-hoc/2026-09-15_soak_decisions/{which_run_read_the_ledger.py,
revert_unauthorised_rescores.py, prove_the_guard_test_discriminates.py}`.
**Reverted to unchanged**: `AGENTS.md`.
