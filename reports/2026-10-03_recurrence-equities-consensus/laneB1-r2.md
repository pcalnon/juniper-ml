# Lane B — Round 2

**Date:** 2026-10-03  
**Lens:** sequencing, gating, actionability, and self-serving framing

## Q1 — P0 forward dependencies

The challenged P0 rows survive as executable P0 work. W0.2 has an intra-phase order, not a forward dependency: "W0.2 preflight refusing | W0.1 env repair" and the risk mitigation says "Land W0.1 first." W0.3 deliberately reserves semantics for W5.4 but does not need that facility: it derives `degraded` "from those records, **not** from `acceptance.ok`." W0.7 defines the current constant and says "W5.3 adds scopes." W0.8 can run "shadowed by hand" and does not require W1.0.

There is a packaging smell: W0.8 acceptance requires "write as §1 of the W5.1 note," so P0 creates part of a nominal P5 deliverable. That does not prevent execution, because the note can be opened early. The actual contradiction between replay and matrix gating is addressed under Q4, not a technical forward dependency here.

**Severity: HELD.** Quoted evidence: "W0.8 can run shadowed by hand; W1.0 needs the repaired env and the CLI to drive it."

## Q2 — W1.0 independence

The independence claim is false as written. W1.0 says "Independent of W1.1–W1.12" and Details says "The rest of P1 does not wait for it." But W1.1(a)'s normative bundle includes "`normalize_features` per W1.0's finding." W1.1(a) therefore cannot be finalized as specified before W1.0.

M1 also explicitly depends on W1.0: "P1 merged: W1.0 go/no-go issued." Thus even if most implementation rows can proceed in parallel, M1 cannot complete independently of W1.0. Replace the blanket independence claim with a dependency exception for W1.1(a) and M1.

**Severity: MAJOR.** Quoted evidence: "Independent of W1.1–W1.12" versus "`normalize_features` per W1.0's finding."

## Q3 — PyPI release as a hard M1 gate

Requiring a published artifact is defensible for a milestone named "contract deployed": a checkout cannot prove the deployed path. The problem is schedule actionability. W1.11 makes an external release train a hard gate — "**M1 requires this item**" — but supplies no slip rule, fallback milestone, or revised-date trigger. The dependency table merely repeats that floors and pins follow publish.

If 0.17.0, GHCR, a pin PR, or the published-image smoke slips, M1 slips wholesale; the plan never says whether runnable code may earn a partial milestone or how the date is rebaselined. With one owner, this is a brittle all-or-nothing gate rather than a managed dependency.

**Severity: MAJOR.** Quoted evidence: "PyPI 0.17.0 probe ... smoke passes on published images. **M1 requires this item.**"

## Q4 — W0.8 versus W1.0

Steelman B2: one replay distinguishes only whether one E-H configuration blows up. It cannot isolate readout, ridge, normalization, or theta. The plan concedes that W5.1's "content [is] gated by W1.0's verdict" and R5 waits for the matrix. Therefore W1.0, not W0.8, is the scientific gate. Calling P0 the phase that "measure[s] the real thing" while deferring the deciding measurement is structurally misleading.

Steelman the plan: W0.8 is a cheap triage measurement. P0 first repairs the environment and adds CLI params; only then can a controlled matrix run unattended. Keeping the larger M-sized experiment out of the truthful-path repair limits P0 scope, while P1 "opens with" W1.0.

B2 is stronger. The prerequisites are themselves P0, so the matrix can close P0 after them. More importantly, the plan declares all of P5 gated on W1.0. Phase placement should follow the gate, not the experiment's size. At minimum, M0 should include the matrix verdict or be renamed as preliminary measurement only.

**Severity: MAJOR.** Quoted evidence: "Phase 5 ... gated on W1.0's go/no-go" and "W0.8 (one replay, one hour) is the P0 item."

## Q5 — R4 converted to a note

This attack does not land. The note gives a technical invariant, not an unexplained owner preference: producer normalization is fitted on pooled train data, while early CV folds evaluate rows inside that pool, so those fold statistics leak. Its remedy is equally scoped: preprocessing added for CV must fit only fold-train rows. It also preserves producer normalization as a convenience rather than banning it.

Converting that invariant into a note is not self-serving merely because the author resolved it. An owner ruling would be appropriate only if there were competing valid leakage policies; none is offered here.

**Severity: HELD.** Quoted evidence: "its statistics leak into the early folds whose eval rows are inside that partition" and "must be fitted on the fold's train rows."

## Q6 — Outcome and exit semantics

The ordinary cases are consistent: R6 makes `degraded` non-zero, `flagged` report-only with unchanged exit, and gate failure `failed` with non-zero exit. W0.3 also correctly forbids deriving `degraded` from acceptance.

The missing-metric case is not consistent or actionable. W5.4 acceptance says unconditionally "missing metric → `flagged (metric absent)`" while Details says "`mode: gate` failing → row `failed` and non-zero exit." A missing required gate metric is either a gate failure or a flag; the text assigns both semantics depending on which sentence implementers follow. R6 does not resolve absence. Specify missing metric by mode.

**Severity: MAJOR.** Quoted evidence: "missing metric → `flagged (metric absent)`" versus "`mode: gate` failing → row `failed` and non-zero exit."

## Q7 — M1 date credibility

M1 on 2026-11-07 is not credible as a five-week, one-owner target when M0 consumes the first two weeks and P1 then has roughly three weeks. P1 contains W1.0 (M matrix), W1.2 (M), W1.4 (M), W1.5 (L across three repos), W1.8 (S–M), W1.11 (M release/ops), plus seven S/S–M rows and W1.12's restart persistence smoke.

The milestone also names releases of recurrence 0.6.0, model 0.4.0, data-client 0.6.0, canopy 0.9.0, and data 0.17.0. Only the data release is an explicit work item. Cross-repo review, release publication, image publication, pin PRs, and the authenticated smoke are not represented by enough schedule slack. Agents parallelize drafting, not owner review and release authority.

**Severity: MAJOR.** Quoted evidence: "Staffing assumption: one owner ..." and "M1 ... 2026-11-07 ... requires W1.11 ... and W1.12."

## Q8 — Recording the B2 dissent

The paragraph records B2's requested disposition accurately — "the full W1.0 matrix should itself be P0" — but softens the reason. It calls the retained choice a "reconciled position" although dissent remains, and substitutes an automation rationale for B2's gating rationale. Since W0.1 and W0.6 are P0 prerequisites, "once the env and CLI can run it unattended" does not explain why the matrix must be P1 rather than the end of P0.

Record that B2 considered W1.0 the real P5/R5 gate and rejected one replay as insufficient, rather than only recording the requested row move.

**Severity: MINOR.** Quoted evidence: "the reconciled position is that W0.8 ... is the P0 item and the matrix follows once the env and the CLI can run it unattended."

## Q9 — Compact rows versus Details

There are two normative contradictions.

First, W5.2's row says "window embargo ≥ `lookback` + `embargo_days`," combining a window count and a duration. Details instead says "Embargo stays in windows and must be ≥ `lookback`" and "`embargo_days` is a separately named duration gap." Because Details is normative, the compact row describes a different and dimensionally invalid contract.

Second, W5.4's row makes a missing metric always `flagged`, while Details makes a failing gate `failed`; this is the Q6 ambiguity in compact-versus-detail form. W1.1 also advertises part (a) "now" while Details makes one bundle value depend on W1.0, but that is a dependency contradiction rather than abbreviation.

**Severity: MAJOR.** Quoted evidence: "window embargo ≥ `lookback` + `embargo_days`" versus "Embargo stays in windows ... `embargo_days` is a separately named duration gap."

## Q10 — Breakage introduced by reordering

Moving W1.11 into P1 turned M1 into an incompletely specified multi-release gate. W1.11 Details says data pins move now and recurrence/canopy pins move "when those ship," while acceptance requires a smoke on "published images." Yet no P1 row owns publication of recurrence 0.6.0 or canopy 0.9.0, despite M1 naming both versions. The moved gate therefore references release predecessors that the phase does not schedule.

A second sequencing defect remains: W5.6 acceptance says the new shared-cache switch is "documented in W4.1," but W4.1 is completed in P4 before W5.6 is implemented in P5, and W4.1 Details does not include that switch. Either move the documentation into W5.6 or add a later W4.1 amendment.

Finally, W3.0a says it "Shares the W3.2 fixture," while W3.1 must "Land first in P3" and the dependency table says W3.2 comes after W3.1. The numbering implies 3.0a first, but its fixture predecessor is later. State the executable order as W3.1 → W3.2 fixture → W3.0a.

**Severity: MAJOR.** Quoted evidence: "to recurrence 0.6.0 / canopy 0.9.0 when those ship" and "W5.6 ... documented in W4.1."

## Tally

<!-- markdownlint-disable-next-line MD036 -->
**FATAL 0 / MAJOR 7 / MINOR 1 / HELD 2**

## Dissent I would record

I would retain B2's dissent in stronger form: W1.0 is the plan's actual scientific gate because it controls W5.1, R5, and W5.4. A one-configuration replay is useful triage but cannot carry a go/no-go disposition. Put W1.0 at the end of P0 after W0.1/W0.6, or explicitly make M0 preliminary and prevent P1/M1 claims from implying that the scientific gate is independent. I would also dissent from M1's date until every required release has an owned work item and a slip policy.
