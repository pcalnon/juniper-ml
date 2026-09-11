# Soak: the 10 unexplained pilot runs — the selection is principled, and it is conservative

**Date**: 2026-09-10
**Repo**: juniper-ml
**Author**: Paul Calnon
**Status**: closes §5's selection question; raises no new owner decision

Closes the item carried as §5 of
[`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md)
and listed there as work item 5: *"The 10 unexplained pilot runs — 17.5% of the pilot's probe
runs, absent from the corpus with no recorded basis. A selection question upstream of every
rate here."*

---

## 1. The census, reproduced

Re-derived 2026-09-10 from the transcript tree, using
`util/ad-hoc/2026-09-08_soak_label_to_transcript.py`'s own `discover_transcripts()` and
`bind()` rather than a second implementation.

| quantity | value |
|---|---|
| transcripts whose `meta.json` description begins with a probe id | **57** |
| of those, bound to a ledger observation | **40** |
| unbound | **17** |
| unbound **with** a recorded reason in `conf/soak_probes.json`'s `retired` block | **7** |
| unbound with **no** recorded basis | **10** — 17.5% of 57 |

The 7 retired-with-reason are P01, P04, P05, P09, P10, P13 (all `retired_on` 2026-08-21) and
**P17** (2026-08-22). The 10 unexplained are P06×3, P23×2, and one each of P14, P16, P18,
P20, P22.

Every figure matches the handoff, **including the P17 grouping** that its §10 records
adversarial review having corrected from an earlier draft's "17, ~30%, no recorded basis".
Reproducing that draft's error is easy: matching a transcript's 3-character description head
(`P17`) against the registry's full slugs (`P17-conda-activate-restore-arm`) fails silently
and reports all 17 as unexplained, at 29.8%. The number is only right if the id match is.

## 2. The finding: all 10 are contaminated

Running the contamination screen `util/ad-hoc/2026-08-21_soak_probe_evidence.py` over the 10:

| probe | run mtime | contaminated | retrieved | ledger |
|---|---|---|---|---|
| P06-expect-removals-scope | 2026-08-22T21:39 | **yes** | yes | — |
| P06-expect-removals-scope | 2026-08-22T21:44 | **yes** | yes | — |
| P06-expect-removals-scope | 2026-08-22T21:59 | **yes** | yes | filename |
| P14-per-run-timeout-ordering | 2026-08-21T21:10 | **yes** | yes | — |
| P16-editable-ambiguous-no-autopick | 2026-08-22T02:34 | **yes** | no | — |
| P18-health-interval-non-positive | 2026-08-22T21:53 | **yes** | yes | **CONTENT** |
| P20-chop-proc-root-tests-only | 2026-08-22T21:52 | **yes** | yes | **CONTENT** |
| P22-env-floor-highest-version | 2026-08-22T21:54 | **yes** | yes | — |
| P23-reaper-over-protection-bias | 2026-08-22T02:32 | **yes** | yes | — |
| P23-reaper-over-protection-bias | 2026-08-22T21:39 | **yes** | no | — |

**10 of 10 touched the answer key or the protocol document.** The discard was therefore
principled and matches what the tooling's docstring claims was done — *"8 pilot runs were
discarded for registry leakage"*. What is missing is a **per-run record of the reason**, not
a reason.

So the discrepancy §5 flags is a **documentation** defect with a **counting** error attached
(the docstring says 8; the set is 10), not evidence of arbitrary selection. `conf/soak_probes.json`'s
`retired` block records a reason per *probe*; nothing records one per *run*, and these 10 are
run-level discards of probes that remain live in the registry.

## 3. And the exclusion is conservative

The direction matters more than the count, because §5 raises this as a threat to every rate.

The 10 discarded runs have a mechanical retrieval rate of **8/10 = 80%**, against the scored
corpus's mechanism-checked **24/43 = 55.8%**. They skew **toward** retrieval — which is what
contamination would predict, since a run that has seen the answer key has seen a document
that names `docs/REFERENCE.md`.

**Had they been wrongly included, the pooled rate would be higher, not lower.** The exclusion
can only have moved the estimate away from the 0.75 boundary, never toward it. It is
therefore not a mechanism that could have manufactured the `BET-FAILING` verdict; if
anything it is the verdict's most conservative input.

Two qualifications, both real:

- **`retrieved` here is the screen's mechanical flag** (`dest_hits + via_output > 0`), not a
  ledger `outcome`. These runs were never scored, so no scored outcome exists for them. The
  comparison is like-for-like in mechanism but not in adjudication.
- **80% vs 55.8% is 10 runs against 43.** `wilson(8, 10)` is wide. The claim made here is
  about the *sign* of the effect, which does not need a tight interval; it is not a claim
  that the discarded population's true rate is 80%.

## 4. Side result: the ledger leak's live exposure is exactly one run

Running the same screen's new ledger check (item F′) over **all 57** probe-id transcripts
rather than only the 43 valid rows:

| scope | touched the ledger | read its **content** |
|---|---|---|
| scored corpus (43 valid rows) | 8 | **1** |
| all 57 probe-id transcripts | 13 | **3** |

The two extra content reads are **P18 (21:53) and P20 (21:52) — both already in the
discarded 10**, and both already excluded for answer-key contamination.

This tightens owner decision 8 of the 09-09 handoff — *whether the ledger leak invalidates
its runs*. The full-corpus exposure is 3 runs, but 2 are already out of the corpus on an
unrelated and stronger ground, so **the decision governs exactly one scored observation**:
`P18-health-interval-non-positive`, 2026-08-22T21:41:09Z, recorded `follow`.

That bounds what owner decision 8 can do. Computed with the repo's own
`util/soak_ledger.py` `wilson()` against its `DECISION_BOUNDARY = 0.75`:

| corpus | k/n | rate | Wilson 95% | terminal? |
|---|---|---|---|---|
| operative (as recorded), now | 26/43 | 60.5% | [0.4558, **0.7363**] | yes |
| operative, minus that one `follow` | 25/42 | 59.5% | [0.4449, **0.7296**] | yes |
| mechanism-checked, now | 24/43 | 55.8% | [0.4111, **0.6957**] | yes |
| mechanism-checked, minus that one `follow` | 23/42 | 54.8% | [0.3995, **0.6878**] | yes |

**Owner decision 8 does not flip the verdict under either standard**, which is worth knowing
before spending effort on it. Note this is a *different* question from §4.5 of
[`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`](JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md),
which remains live and unaffected: re-scoring a row the **other** way gives 27/43 →
[0.4786, **0.7562**], which is **not** terminal. Removing an observation and adding a follow
are not symmetric, because the first shrinks n as well.

## 4a. Side finding: the leak propagated into a notes document

`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md` quotes a
**full ledger record** in a fenced block — the prose `note` (which restates the answer),
`obs_id`, `outcome` and `pointer`. A subject that greps `notes/` for its subject matter and
gets that chunk back has seen the answer sheet exactly as if it had read the ledger.

So the content markers used above deliberately fire on **any** file that quotes a record, not
only on `reports/soak/pointer_follow_soak.jsonl`. Screening the ledger's own path alone would
have missed this, which is the same shape as the gap item F′ closes — and it is the
identifier-shaped-facts authoring rule violated a second time, in the document that
*documents* the first violation.

**Not redacted here.** The quoted record is that note's evidence for a claim it makes; removing
it would weaken the record to protect a measurement that has already been taken. Whether the
soak's own working documents should be excluded from probe-reachable paths, or written so a
subject's grep cannot hit them, is a registry/authoring decision in owner decision 1's
neighbourhood — raised, not ruled.

## 5. What this does not settle

- **Why the docstring said 8.** `util/ad-hoc/2026-09-08_soak_label_to_transcript.py`'s
  `bind()` docstring claimed *"8 pilot runs were discarded for registry leakage"*. It is 10;
  the docstring is **corrected here**, with the enumeration recorded next to it, because a
  tool that states the wrong count is where the next reader will get it. Where the figure 8
  originally came from is still not recorded, and is not chased.
- **Whether contamination should have been a *discard* rather than a scored outcome.** That
  is the same family as owner decision 1 (whether index-recovery becomes a scored outcome)
  and is untouched.
- **The 7 retired probes' runs.** Those have reasons; this note did not audit whether the
  reasons are good ones.
- **Nothing here re-scores anything.** The ledger and `conf/soak_probes.json` are unmodified
  and no probe was run.

## 6. Reproduction

Every table in this note is produced by one script:

```bash
# §1, §2, §3 and §4's second table, in one pass
python3 util/ad-hoc/2026-09-10_soak_stopping_rule/discarded_run_census.py

# the guard against the failure mode described in §1 -- exits 1 if the
# probe-number -> registry-slug resolution silently stops working
python3 util/ad-hoc/2026-09-10_soak_stopping_rule/discarded_run_census.py --self-check

# §4's first table, over the scored corpus only
python3 util/ad-hoc/2026-09-10_soak_stopping_rule/ledger_exposure_probe.py

# the Wilson bounds in §4, from the repo's own analyser
python3 -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('sl','util/soak_ledger.py'); m=importlib.util.module_from_spec(s); sys.modules['sl']=m; s.loader.exec_module(m); print(m.wilson(25,42), m.DECISION_BOUNDARY)"
```

`discarded_run_census.py` composes the binder's `discover_transcripts()` / `bind()` with the
screen's `scan()` rather than re-implementing either, so it cannot drift from the instruments
whose numbers it reports. It is read-only: it modifies no ledger and runs no probe.

**A caution about line-pinned citations, learned in this session.** The protocol document's
identifier-shaped-facts rule was at `:672` when the 09-09 handoff cited it and at `:693` two
days later, after ml#1883 inserted above it — the line reference survived, pointing at
unrelated prose. Citations to that rule in this note and in
`util/ad-hoc/2026-08-21_soak_probe_evidence.py` therefore quote the sentence instead.

## 7. Documents

- [`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md)
  — §5 (the open question), §3.F′ (the ledger leak), §6.8 (owner decision 8).
- [`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`](JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md)
  — the mechanism re-audit and the 24/43 figure this note compares against.
- [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
  — the protocol of record; §4 defines FOLLOW, and the identifier-shaped-facts authoring rule
  reads *"identifier-shaped facts must be stored in a form the subject's own grep cannot hit"*.
  Quoted rather than line-pinned: it was `:672` when the 09-09 handoff cited it and `:693` after
  ml#1883 inserted above it.
- [`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`](JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md)
  — §4.5 (the verdict is one observation deep), which §4 above bears on directly.
