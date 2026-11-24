# The stratum predictors, tested — all three fail, and the design could have found them

**Project**: juniper-ml
**Date**: 2026-09-09
**Status**: §8.2's three candidates refuted; one tempting grouped contrast shown to be circular
**Scope**: §8 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_soak-arc-outstanding-work.md`

---

## 1. The question

§8.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` calls
the predictor gap **"the actual blocker to decision support"**: two strata exist, and
nothing predicts which one a *new* fact lands in. It names three candidates and records
that none has been tested —

1. how findable the fact is by a plausible grep of the task's own vocabulary;
2. whether the task is completable correctly *without* the fact;
3. whether the fact contradicts a plausible default the agent already holds.

These need no Overtoad decision and spend no sessions: they run over the 15-probe registry
and its tasks, not over the 43 ledger rows. `util/ad-hoc/2026-09-09_soak_stratum_predictors.py`
tests them.

**Answer: all three fail, and the failure is informative because the design had the power
to detect them.**

## 2. Finding 1 — a grouped contrast that looks decisive and is CIRCULAR

An earlier draft of this document claimed a result here. It was wrong, it was wrong in a
tempting way, and the refutation is worth more than the claim was.

The claim: §9.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`
records that **not one probe's interval excludes 50%**, but the probe was never the unit a
relocation decision needs — the **stratum** is. Grouped:

| standard | never-follow | always-follow | disjoint? |
|---|---|---|---|
| as recorded | 3 probes, 0/11, Wilson [0.000, 0.259] | 9 probes, 21/21, [0.845, 1.000] | yes |
| mechanism-checked | 4 probes, 0/15, Wilson [0.000, 0.204] | 8 probes, 18/18, [0.824, 1.000] | yes |

**That is not evidence of anything.** The groups are *defined* by their observed outcomes —
"never-follow" means 0 follows, "always-follow" means all follows — and the intervals are
then computed from those same observations. Extremeness is guaranteed by the selection, not
discovered in the data.

Measured, rather than argued. Simulating the observed per-probe `n` under the **null that
all 15 probes share the pooled rate**, and applying the identical grouping rule:

```
== self-check 1: is the grouped contrast circular? ==
  null = all 15 probes share p=0.558, observed n held fixed
  grouping by extreme outcome gives DISJOINT intervals in 13615/20000 = 68.1% of trials
  => YES, circular. Selection makes the intervals extreme, not the data.
```

**Roughly seven times in ten, pure noise produces this "finding".** Any successor tempted
to report a grouped contrast over outcome-selected strata should read that number first.

> **CORRECTED 2026-09-09 after Lane A review.** This block previously read
> `13951/20000 = 69.8%` under `p=0.512`, and the surrounding text claimed `--validate`
> reproduced it. It did not: the figure came from an uncommitted draft of the simulation,
> and the shipped tool is seeded, so it prints a fixed number. Two Lane A reviewers caught
> the mismatch independently. The pooled rate also moved (0.512 → 0.558) when the
> classifier bug in §3 was fixed. **Quote the tool, never this block.**

What survives is §5's permutation test, which partitions nothing and is calibrated (§5).
§9.2's caution stands exactly as written.

## 3. Finding 2 — the mechanism-checked standard moves one probe

> **CORRECTED 2026-09-09 after Lane A review.** This section said P21 **and P24** both move
> to 0, on the basis that all three P24 runs read juniper-deploy's copy. That was an
> artefact of a classifier bug — the `cd` target was tested before the per-occurrence path
> prefix, so a subject working from the **ecosystem parent** had genuine reads of *our*
> file discarded. Two of the three P24 runs are that shape, and one of them opened the
> destination by name with `sed`. P24 does **not** move. The pooled mechanism rate was
> 51.2% and is **55.8%**. The bug was live in shipped code too; both are fixed and pinned.

Under the re-audit in `notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`
— which discards destination hits that are a filename-only grep result or a sibling repo's
same-named file — **P21 moves to 0**:

| probe | recorded f/n | mechanism f/n | |
|---|---|---|---|
| P21-pidfile-key-prefix-guard | 1/4 | **0/4** | its one follow was a `grep -rln` filename list |
| P24-grafana-port-3001-deliberate | 3/3 | **2/3** | one run genuinely foreign; two read juniper-ml's own copy |

The never-follow group therefore grows from 3 to **4** (P14, P15, P19, P21) and the
ambiguous middle from 2 to **3** (P02, P23, P24). This still matters for §4.1 of
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`, whose campaign
arithmetic (P21 needs n≥16, P23 n≥31) was computed to resolve **P21's** ambiguity — under
the mechanism standard P21 is no longer the ambiguous one.

**Do not over-read this.** 0/4 has Wilson [0.000, 0.490]. That *does* exclude 50%, but it is
one probe at n=4 and the stratum assignment is still a grouping, not a per-probe property.
What the mechanism standard changes is *which* probes sit in the ambiguous set.

## 4. Finding 3 — all three candidates fail, and that is not a power artefact

Each candidate was operationalised mechanically from the registry, before any test:

| §8.2 candidate | operationalisation |
|---|---|
| grep-findability from the task's vocabulary | does the `task` name an identifier the `fact` also names? (a single grep of the task's own words then lands on the implementation) |
| completable without the fact | does the `discriminator` require a **refusal**? (a refusal-shaped discriminator means the task as written cannot be completed correctly at all, so the fact is load-bearing) |
| contradicts a plausible default | does the `fact` carry a **rationale** marker (*deliberately*, *because*, *rather than*) or a **prohibition** marker (*must never*, *must not*)? |

Result, mechanism-checked standard, **4 never-follow vs 8 always-follow** (corrected — see §3):

| feature | never | always | Fisher p |
|---|---|---|---|
| `task_names_fact_ident` | 1/4 | 5/8 | 0.5455 |
| `discriminator_is_refusal` | 0/4 | 4/8 | 0.2081 |
| `fact_has_rationale` | 1/4 | 3/8 | 1.0000 |
| `fact_has_prohibition` | 0/4 | 3/8 | 0.4909 |
| `fact_points_to_source` | 0/4 | 0/8 | 1.0000 — **vacuous**, see below |

Nothing reaches 0.05. Under the recorded standard (3 vs 9) nothing reaches it either.

`fact_points_to_source` is **identically zero in every probe in both strata** once P24 moves
to `mixed`, so its 1.0000 is a vacuous pass, not a refutation: the feature is untestable on
this corpus rather than tested and found wanting. It is a fourth feature, so §1's "all three
fail" is unaffected.

**"No feature reached p<0.05" is unreadable without the detection floor**, so the tool
prints it:

| grouping | perfect split | one discordant probe |
|---|---|---|
| 4 vs 8 (mechanism) | p = **0.0020** | p = 0.0182 |
| 3 vs 9 (recorded) | p = **0.0045** | p = 0.0455 |

A predictor that actually worked **would** have been detected — even one allowed a single
discordant probe. So this is a refutation of the three candidates, not a shrug about
sample size. The best of them, `discriminator_is_refusal` at p=0.2081, points in the
sensible direction (refusal-shaped tasks are follow-dominant) but 0/4 vs 4/8 is not
enough.

**The correction in §3 weakened every p-value, and it did cost one half of the argument.**
Five features are tested, so a family-wise threshold matters: Bonferroni at alpha=0.05 gives
**0.01**. The perfect-split floor (0.0020) still clears it; the one-discordant floor moved
**0.0070 -> 0.0182** and no longer does. So the claim "even one discordant probe would have
been detected" holds only per-feature, not family-wise. The headline -- a *perfect* predictor
would have been found -- survives. Multiplicity was not mentioned before adversarial review
raised it.

## 5. Finding 4 — the heterogeneity p-value, measured as the label shuffle it claims to be

§9.3 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` reports
`permutation p-value = 0.0017`. §6 of
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` records that
this was a **parametric bootstrap mislabelled as a permutation test** — it resampled from
`Binomial(n, pooled)` rather than permuting observed labels — and predicts a true shuffle
would give p ≈ 0.0002–0.0006.

Measured here with a real label shuffle (reassign the observed run outcomes across probes,
each probe's `n` held fixed):

```
probes=15  runs=43  follows=24  pooled=0.558
heterogeneity=8.5213   permutation p=0.00000  (0 hits in 200,000 shuffles)
```

The direction §6 predicted is confirmed — the true p is far below 0.0017. The exact value
is not comparable to §6's estimate, because the heterogeneity statistic used here (the
n-weighted sum of squared deviations from the pooled rate) may differ from the one behind
the original figure; that statistic is not recorded in §9.3. **The claim to carry forward
is qualitative**: the probes do not share one rate, and the surviving `0.0017` in
`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` is still
labelled with the wrong test.

**This test is calibrated, and unlike §2 it is not circular** — it partitions nothing.
Checked against 12 synthetic datasets drawn from the null that all probes share the pooled
rate:

```
  p on 12 synthetic NULL datasets (want ~uniform, NOT all tiny):
    0.074 0.074 0.194 0.244 0.327 0.374 0.497 0.633 0.669 0.904 0.911 0.923
  fraction < 0.05: 0/12
```

Roughly uniform, and 0 of 12 below 0.05 — which is what a correct test does on null data at
this sample size. (Adversarial review found this block, like §2's, carrying draft values the
shipped seeded tool does not emit. **Run `--validate` and quote it; do not trust a fenced
block in prose.**)
So the real-corpus result is a real signal, and it is the **only** evidence in this
document that two strata exist.

**State it as a floor, not a measurement.** `permutation_p` returns `(hits + 1) / (draws + 1)`,
so 0 hits in 200,000 draws is **p ≤ 1/200001 ≈ 5.0e-6** — the smallest number this
instrument can emit at that draw count, not a value it resolved. At the default 20,000
draws the floor is 5.0e-**5**, an order of magnitude apart, so **always quote the draw
count alongside the p**. (Flagged by Lane A review; the earlier phrasing `p < 5e-6` read as
a measurement.)

## 6. Everything above is EXPLORATORY

The features were written with the outcomes visible. That is the correct way to *generate*
a hypothesis and the wrong way to *test* one. §15.3 of
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` is the model: state
the prediction, then run.

For the refutations in §4 this matters less — a feature that fails to separate the data it
was built on will not separate new data — but a future feature that *does* separate must
be pre-registered before it means anything.

**A practical constraint on doing that.** Registry rule 1 in `conf/soak_probes.json`
`_README` is *"FROZEN BEFORE OBSERVATION 1. Adding or editing a probe after runs begin
invalidates the arm. Add a new probe with a new id; never edit a run one."* So testing any
predictor against fresh probes is a **registry change** — Overtoad decision §7.1's
neighbourhood — not something a successor can do inside the existing 15.

## 7. What this does and does not change

**Does**: §8.2's three candidates are answered, with the detection floor that makes the
null readable. The mechanism standard moves two probes and shrinks the ambiguous set. And
§2 removes a grouped-contrast argument that noise reproduces 70% of the time — a successor
who re-derives it should stop.

**Does not**: it supplies no working predictor, so §8.2's gap — *nothing predicts the
stratum of a new fact* — **remains open**, and remains the blocker to decision support. It
touches none of the Overtoad decisions in §7 of
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`. No probe was
run and the ledger is unmodified.

## 8. Reproduce

```bash
python3 util/ad-hoc/2026-09-09_soak_stratum_predictors.py                    # both standards
python3 util/ad-hoc/2026-09-09_soak_stratum_predictors.py --standard mechanism --draws 200000
```

## 9. Changed files

- `util/ad-hoc/2026-09-09_soak_stratum_predictors.py` — **new**; the predictor test,
  the grouped-strata contrast, the true label-shuffle permutation test, and the
  detection floor.
- `notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md` — this document.

**Not changed**: `conf/soak_probes.json`, `reports/soak/pointer_follow_soak.jsonl`.
