# D6: `epochs_completed` has ZERO spread — the blocker was a premise about load, and load does not move it

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-22
**Status**: D6's gate DISCHARGED. The measurement's own premise is REFUTED: neither ambient load nor thread width moves the count. The 2026-09-17 evidence is recovered and reproduced from a committed instrument. **The gate/no-gate decision itself remains the owner's** — this buys the measurement, as D6 said it would.
**License**: MIT License

---

## 0. What this document is

Owner decision **D6** of
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md)
ruled: *do not gate `epochs_completed` on exact match yet — characterise the spread under
controlled conditions first*, because round 1 had observed requested-100 → **52** and round 2
→ **68**, and *"a gate whose reference moves with ambient load is a flaky gate."*

This document discharges that gate, and reports that **the stated reason for the gate does not
survive measurement**.

Instrument: [`util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py`](../util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py).
Evidence: `~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260922/spread.json`.

---

## 1. The measurement was taken once already — and it is UNCOMMITTED, not lost

> **This section was WRONG in this document's first draft, and the correction is the more
> useful finding.** The draft said the 09-17 instrument "is in no commit, on no branch" and
> that nothing in `notes/` reported it, and drew the `/tmp`-script moral from that. An
> independent fact-check refuted all three claims. What follows is the corrected account.

`~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260917/spread.json` was written
**2026-09-17 19:43** and holds a complete 5 × 4 × 5 sweep. Its instrument and its write-up both
**exist**, and both are **untracked in a sibling worktree**:

| artifact | path | mtime |
|---|---|---|
| instrument | `.claude/worktrees/optimized-giggling-koala/util/ad-hoc/2026-09-17_epochs_completed_spread.py` | 19:43 |
| write-up | `.claude/worktrees/optimized-giggling-koala/notes/JUNIPER_2026-09-17_JUNIPER-ECOSYSTEM_PERF-LANE-EPOCHS-COMPLETED-SPREAD.md` | 19:44 |

That note is titled *"`epochs_completed` is deterministic: 100 runs, zero variance — an
exact-match gate is safe"*, and its §2 carries the same 10 / 50 / 68 / 68 table. **The 09-17
session reached this document's conclusion five days earlier and did the work properly** —
instrument under `util/ad-hoc/`, note under `notes/` with the canonical filename. It obeyed
every placement rule.

**What it did not do was commit.**
`git log --all -- <either path>` is empty; neither file is on any branch, and
`juniper-ml#1962` (the last perf-lane PR) carried the width sweep but not this. So the moral is
**not** the `phase4_consolidate.py` / `v2_citation_validate.py` one — nothing here was written
in `/tmp/`, and `AGENTS.md` § Script placement was followed to the letter. The narrower and
less obvious lesson:

> **`util/ad-hoc/` placement protects work from `/tmp` reaping; it does not protect it from
> never being committed.** To every consumer not standing in that one directory — `git`, the
> notes tree, CI, the next session, and the three searches this session ran — an uncommitted
> file in a sibling worktree is indistinguishable from a file that does not exist. The 09-11
> handoff records that `optimized-giggling-koala` is **locked and must not be removed**; that
> lock is now the only thing standing between this work and its loss.

**And the search that missed it is worth recording too.** This session grepped
`d6-epochs-spread` and `epochs_spread` — patterns drawn from the *evidence directory's* name.
The instrument is called `epochs_completed_spread`, of which neither is a substring. A sweep
whose pattern is derived from the artifact you already found will not find the artifact you did
not. Search the space of plausible names, not the name you happen to hold.

**ACTION FOR THE OWNER**: those two files should be committed from
`optimized-giggling-koala`, or deliberately retired in favour of this document's instrument.
This session did not take them — they are another session's uncommitted work in a locked
worktree, and moving them is that session's call, not this one's.

---

## 2. Result: zero spread, everywhere, at 1-minute load 32.26

5 thread widths × 4 epoch budgets × 5 repeats = **100 observations**, plus a do-nothing control
before and after.

| requested epochs | completed, at EVERY width (1, 2, 4, 8, 16) | distinct values observed | within-cell spread |
|---|---|---|---|
| 10 | 10 | {10} | **0** |
| 50 | 50 | {50} | **0** |
| 100 | **68** | {68} | **0** |
| 200 | **68** | {68} | **0** |

- **Max within-cell spread across all 20 cells: `0`.**
- **Every budget resolves to exactly one value across every width** — the width axis contributes
  nothing at all.
- **Control stable**: 68 before the sweep, 68 after. The run is interpretable.
- **1-minute load average: 32.26** (5-minute 20.06). This is the most heavily loaded host any
  measurement in this lane has run on — roughly 1.6× the 19.50 recorded in the 09-17 file, and
  well above the 9–20 band of the 09-11 evidence.

### 2.1 The width axis genuinely varied — this is not an inert-axis result

The obvious way for this table to be wrong is for the sweep to have changed nothing, so that the
constant output reflects a constant input. It did not. `omp_get_max_threads()`, read on the
training thread through `ctypes` at every cell, tracks the request exactly:

```
w1-* -> 1     w2-* -> 2     w4-* -> 4     w8-* -> 8     w16-* -> 16
```

So the input moved across a 16× range, the ICV confirms it moved, and the output did not. That
is a real invariance, not the failure PF-2's dataset axis suffered
([`JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`](JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md) §0).

### 2.2 Instrument discipline

`torch.get_num_threads()` is **never called**. It is not a passive read — it runs torch's
per-thread lazy init and re-pins the caller — and it has now destroyed two measurements in this
lane: the 2026-09-11 `icv-map` run (caught only by its do-nothing control) and the 2026-09-16
width sweep, which walked into the hazard six days after the same author documented it. Width is
read only through `ctypes.CDLL("libgomp.so.1").omp_get_max_threads()`, and a control arm runs
first and last so instrument perturbation would be visible rather than inferred.

---

## 3. D6's premise is refuted, and the 52 is still unexplained

D6 was not gated because the count *might* be unstable; it was gated on a specific causal story —
**ambient load moves the count.** That story is now refuted from two directions:

1. **Load does not move it.** 32.26 here, 19.50 in the 09-17 file, and both return the identical
   `{10, 50, 68, 68}`.
2. **Thread width does not move it either** — and width was the *mechanism* by which load would
   have had to act. `…SIX-OWNER-DECISIONS-RULED.md` §1 spells the chain out: thread count changes
   BLAS reduction order → floating-point results → where a patience-based loop terminates. The
   chain is real in general; it is **inert for this benchmark**, across 1 → 16.

**Therefore the historical `52` was not a load artifact, and treating it as one is unsupported.**
Two candidate explanations remain, and this measurement separates neither:

- a **different tree** — the round-1 observation predates the 3.13 → 3.14 environment rebuild and
  an unknown number of cascor commits; or
- a **different call** — round 1 may not have reproduced `test_epoch_scaling`'s exact
  construction (`torch.manual_seed(42)`, 100 samples, `input_size=2`, `lr=0.005`), which this
  instrument does reproduce verbatim.

Naming which one requires the round-1 conditions, and those were not recorded. **The honest
position is that `52` is an observation of unknown provenance, not evidence of instability.**

> **Do not write "the count is deterministic."** What is measured is that it is invariant to
> *load* and to *thread width*, on this tree, at this seed. It is a function of (code, seed,
> budget) — which is precisely the property that makes a gate possible — but "deterministic"
> claims invariance to things nobody tested, and one of them (the tree) is the leading suspect
> for the 52.

---

## 4. What this means for the gate — and the part that is NOT closed

**The gate D6 asked for is discharged: the reference does not move.** An exact-match gate on
`epochs_completed` would not be flaky for the reason D6 feared.

Three qualifications the owner should have before deciding to build it:

1. **Only 2 of the 4 cells would be real assertions.** At budgets 10 and 50 the count *equals the
   request* — those cells are budget-bound and a gate on them asserts a tautology. The emergent
   behaviour appears only at 100 and 200, where both land on 68. A four-cell gate is two tests
   and two decorations.
2. **The gate's reference is tree-sensitive by construction.** The count is invariant to the
   runtime environment but *not* to cascor's numerics — that is the whole reason it is emergent.
   So the gate will legitimately fire on any cascor change that moves candidate training, which
   is either its entire value (it detects silent numeric drift) or its entire cost (it fires on
   intended changes), depending on how often that happens. **This measurement does not say which**,
   and that is the real open question, not the spread.
3. **Scope is unchanged**: 1 of the 5 cascor micro files
   (`juniper-cascor/src/tests/performance/test_micro_candidate.py`). The other four are genuinely
   fixed-count and need no gate either way.

---

## 5. A side finding: the mapped libgomp has changed, and it is not the one the ICV note records

[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
**§1** (lines 55–57 — not §3, which begins at line 114) instructs that every ICV reading record
the libgomp path from `/proc/self/maps`, and records the then-current value as
`/opt/miniforge3/envs/JuniperCascor1/lib/libgomp.so.1.0.0`.

This run maps a **different library**:

```
/opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/torch/lib/libgomp.so.1
```

— torch's vendored copy, under the 3.14 site-packages tree created by the 2026-09-12 environment
rebuild.

**What this does and does not license.** It does *not* invalidate the 09-11 readings, and it is
not offered as a cause of anything. It does mean that **an ICV figure taken before the rebuild and
one taken after are readings of two different libraries**, so they are not automatically
comparable — exactly the situation the note's own record-the-path rule exists to make visible.
The rule worked. Anyone re-running the 09-11 instruments should record the path and expect this
value, not the one the note quotes.

---

## 6. Two independent instruments, five days apart, agreeing exactly

> The first draft headed this section *"Corroboration from the orphaned 09-17 evidence"* and
> argued the older artifact could be no more than corroboration because it had no instrument.
> It has one (§1). The two can therefore be **diffed**, which makes this agreement stronger
> than the draft allowed.

| | 2026-09-17 (uncommitted) | 2026-09-22 (this run) | independent re-run, 09-22 |
|---|---|---|---|
| widths × budgets × repeats | 5 × 4 × 5 | 5 × 4 × 5 | 2 × 2 × 3 |
| e10 / e50 / e100 / e200 | 10 / 50 / 68 / 68 | 10 / 50 / 68 / 68 | — / — / 68 / 68 |
| within-cell spread | 0 | 0 | 0 |
| **1-minute load** | **19.50** | **32.26** | **54.49** |
| torch / python | 2.11.0+cu130 / 3.14.7 | 2.11.0+cu130 / 3.14.7 | same |
| ICV verified per cell | not recorded | recorded (§2.1) | recorded |
| control arm | none | before and after, stable | stable |

**Three load levels spanning 2.8× — 19.50, 32.26, 54.49 — return the identical result.** The
third column is a re-run performed by a reviewer fact-checking this document, not by its author,
on an instrument they did not write. That is the strongest form the load-invariance claim takes,
and it is stronger than §3 states.

The two full instruments were written five days apart by different sessions and agree
key-for-key. They are **functionally equivalent in construction** — same seed, same shapes, the
same `train_detailed` call — which is *why* they agree, and is also the limit of what the
agreement proves: two instruments that build the benchmark the same way will make the same
mistake if that construction is wrong. What separates them is that this one records the ICV
actually in force and carries a do-nothing control, so it can tell "the axis did nothing" from
"the axis was never applied". The 09-17 instrument cannot.

So: agreement between two same-shaped instruments is **replication**, not independent
validation of the construction (`corpus agreement is NOT validation` — three candidate rules
once agreed on all 483 real series and two of them shipped defects). The construction is
validated by a different argument: it reproduces `test_epoch_scaling` verbatim, which is the
thing a gate would gate.

---

## 7. Reproduction

```bash
/opt/miniforge3/envs/JuniperCascor1/bin/python \
  util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py \
  --json ~/.local/state/juniper-experiments/suites/d6-epochs-spread-<YYYYMMDD>/spread.json
```

Defaults reproduce this run exactly (widths 1 2 4 8 16, budgets 10 50 100 200, 5 repeats,
seed 42). Read-only with respect to the cascor tree; `--cascor-src` overrides its location.

**Stop condition.** If `control.stable` is `false`, the instrument perturbed the measurement and
**no arm in that run is interpretable** — fix it before quoting anything. If
`max_spread_within_cell` is non-zero, the verdict above does not hold on that host and the gate
question reopens.

---

## 8. Provenance

Measured 2026-09-22 read-only from `JuniperCascor1` (Python 3.14.7, torch 2.11.0+cu130) against
the juniper-cascor primary checkout, whose HEAD was **`b35fab1` on branch `fix/serena-mcp-file`,
10 commits ahead of `main` (`70d5ca1`)** — *not* `main`, as this section first claimed.

**The numerics are nonetheless main's**: `git diff main..HEAD --name-only` touches
`.serena/project.yml`, CI workflows, requirements/lockfiles, `src/api/security.py` and
`util/check_image_no_secrets.py`, and **nothing under `candidate_unit/`** — the only tree this
measurement exercises. The correction is recorded rather than quietly fixed because §3 makes
*"a different tree"* the leading suspect for the historical 52, so a sloppy tree identifier in
this document is exactly the kind of thing that would make the next round unfalsifiable.

The 09-17 work was found during a state re-probe of
[`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md)
and is not this session's work.
