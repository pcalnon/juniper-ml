# Owner decision #7 — the trigger fired on 2026-09-07 and nothing has happened since

**Project**: juniper-ml
**Date**: 2026-09-11
**Status**: DECISION BRIEF — assembles the evidence; decides nothing
**For**: owner decision #7 of `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md:654`

---

## 1. Why this document exists

`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` prescribes one action on
a failed bet: **"Revisit owner decision #7. Never re-inline."** The verdict turned
`BET-FAILING` on 2026-09-07, and `python3 util/soak_ledger.py status` has printed that
instruction on every invocation since. Neither the plan nor the ledger has been touched.

That is not neglect so much as friction: revisiting #7 requires assembling evidence from
seven documents, three of which were corrected in the last four days. This brief does the
assembly. **It rules nothing** — #7 is the owner's, and so are the eight decisions listed in
§7 of the 2026-09-09 handoff.

## 2. What decision #7 actually says

> | 7 | Keep A's skills as a later probe? | **Optional, deferred** — revisit only if the P3 soak shows a real pointer-follow problem |

**"A's skills"** is option A from the same plan's carrier comparison: relocate `AGENTS.md`
content into `.claude/` **skills**, loaded on demand, rather than into `docs/REFERENCE.md`
behind a pointer (option C, which shipped alongside D's `notes/` inbox).

A was rejected on **three axes** (§"The three axes that do decide"), and it is worth being
precise about which of them the soak can speak to:

| axis | why A lost | does the soak bear on it? |
|---|---|---|
| **Worst case, not average** | C's content leaves the memory system unconditionally (−83.3%); A's skills can all be pulled into one wide-ranging session (−3.5%) | **No.** The soak measures retrieval, not context cost. |
| **Compaction** | A's carriers sit in the "lost until re-triggered" row; C's residual is re-injected from disk | **No.** Untested by the soak. |
| **Content-loss screen** | `in_docs_scope` returns **False** for every `.claude/` destination, so A's corpus leaves the only mechanical content-loss alarm the fleet has | **No.** Mechanical, and unchanged. |

## 3. The trigger fired — and this is exactly what it licenses

`main` is `BET-FAILING seeded=43/35 rate=60.5% ci=[0.456, 0.736]`, upper bound below the
0.75 boundary. Under the mechanism-checked re-audit
(`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`) it is
**24/43 = 55.8%**. Either way the bet failed: **agents do not reliably follow the pointer.**

**That licenses revisiting #7. It does not answer it**, and the distinction is the whole
point of this brief:

- The soak measured whether a fresh session retrieves a fact from **`docs/REFERENCE.md`**.
  It says **nothing** about whether the same session would load a **skill**. No probe has
  ever tested A's carrier. "The pointer bet failed, therefore skills" is not an inference
  this evidence supports — it is a hypothesis the evidence makes *worth testing*.
- All three reasons A was rejected are **untouched** (§2). A failed pointer bet does not
  repair a carrier that leaves the content-loss screen.

## 4. What the evidence shows that #7's framing predates

**The harm #7 hedges against has largely not materialised.** #7 asks whether to try another
carrier because facts might become unreachable. Measured on the 43-row corpus:

| | |
|---|---|
| answers correct | **41 / 43** |
| wrong answers | **2**, and **both are P15** |

And P15 is a probe the arc itself classifies as **invalid**:
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md:709` lists it under
*"the discriminator is stricter than the source rule"*, one of the three ways a probe can be
invalid. Its own scoring note says so directly — REFERENCE.md's *"converge, not remove"*
governs **diverging (live)** worktrees, while for genuinely dead ones removal via the gated
cleaner is defensible, *"so the discriminator may be over-strict."* One of the two is
**retrieval-positive**: it read the document and was still scored wrong.

So the failure mode is **source-recovery, not loss**. Sessions reach the right answer from
code and tests instead of the relocated prose. That is a different problem from the one #7
was reserved against, and it points at a different remedy.

**Caveat that cuts the other way**: retention (95.3%) and correctness (41/43) are the *same
number by construction* — "retention" is the fraction that did not miss, and in practice a
miss is a wrong answer. Do not quote them as two corroborating figures. And 95.3% is
one-way: `RESCORE_OUTCOMES = ("source-recovered",)` can only raise it, and the corpus was
**74.4%** as originally recorded.

**The gap that blocks a per-fact answer.** Two strata exist — heterogeneity far beyond
binomial noise — but `notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md`
tested all three candidate predictors and **all three fail**, at a sample size where a
perfect split would have been found. **Nothing predicts which stratum a new fact lands in.**
So "use skills for the facts that need them" is not currently expressible: there is no test
for which facts those are.

## 5. The options, and what each costs

1. **Close #7 as answered — no skills probe.** The three rejection reasons stand untouched,
   and the observed failure is source-recovery rather than loss. Cost: none. Risk: the
   hypothesis that a different carrier does better is never tested.
2. **Probe A's skills.** Cost is not small: the registry is **frozen** (`conf/soak_probes.json`
   rule 1 — *"Add a new probe with a new id; never edit a run one"*), so this needs new probe
   ids, i.e. the registry change that is owner decision §7.1 of the 09-09 handoff — **and** a
   skills carrier to test against, which does not exist. It would also need a ruling on
   whether `--force` may run at all (§7.5), since the verdict is terminal.
3. **Re-aim at the real finding.** The arc's own design document calls the predictor gap
   *"the actual blocker to decision support"*. Neither carrier can be chosen per-fact until
   something predicts membership. This defers #7 again, but for a stated reason rather than
   by omission.

## 6. What this brief does not do

It does not rule #7, and it does not touch the seven other owner decisions in §6 of
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md`.
It changes no code, runs no probe, and leaves `reports/soak/pointer_follow_soak.jsonl` and
`conf/soak_probes.json` unmodified.

Whichever option is taken, the ledger's second instruction is unconditional and unaffected:
**never re-inline.**
