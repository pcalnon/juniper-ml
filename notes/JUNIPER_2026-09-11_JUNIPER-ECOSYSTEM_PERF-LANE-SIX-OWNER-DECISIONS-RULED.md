# Perf lane: the six open owner decisions, RULED 2026-09-11

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-11
**Status**: all six RULED by the owner in session; four carry an execution gate before they land
**License**: MIT License

---

## 0. What this document is

The six decisions that had accumulated across
[`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
("the P2 plan") and four successive handoffs, put to the owner and ruled in one sitting. Each entry
records **the ruling, the gate that must clear before it lands, and what the ruling does not
decide**.

Sources for the background on each: the P2 plan rows 2.1 / 2.2 / 4.2;
[`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md)
§4 (the `runtime:` block);
[`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md)
and
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
(the thread-pin defect); `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`
§3.3 (`epochs_completed` — its **only** home before this document);
[`JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`](JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md)
§1.5 (the CI hazard).

---

## 1. The correction that reframed two of the rulings

**cascor#531's candidate-phase penalty is `1.52×` — a 52% slowdown — not 1.52%.** It was put to the
owner as a percentage in the first pass and corrected before the ruling. `parallelism/blas_threads.py`
carries the decomposition:

- the capped path's candidate phase ran **1.52×** the uncapped path's; the cap itself accounted for
  **1.30×** of that;
- through **two** channels — throughput **1.26× → 1.14×** and epoch count **1.21× → 1.03×**;
- the epoch-count channel is the subtle one: thread count changes BLAS reduction order, hence
  floating-point results, hence where a **patience-based** candidate early-stopping loop terminates.
  A tighter cap therefore did not merely slow each epoch, it caused **more epochs to be run**.

**Both channels shrink as the budget rises** (1.26 → 1.14 and 1.21 → 1.03). So 1.52× is the
**worst case at a tight cap**, not a flat tax on the environment-variable mechanism. That is the
single most important fact for D2's investigation, and it is why that investigation must sweep cap
*values* rather than compare capped against uncapped.

---

## 2. The rulings

### D1 — the cascor thread-pin defect: MEASURE FIRST, then repair

**Ruled**: do not pick a repair yet. **First measure the later output passes at thread widths
greater than 2** — 4, 6, 8, 10 as appropriate — because the whole arc has assumed 2 is correct
merely because that is what the constructor formula `max(2, worker_thread_count * 2)` produces.
The 16-wide burst is established as pathological; **that does not establish 2 as optimal.**

**Gate before any repair lands**: the width sweep, reporting **epoch count and total wall time**,
never ms/epoch — §1's epoch-count channel means a width that is faster per epoch can run more
epochs and lose overall.

**Not decided**: which repair mechanism (training-thread pin vs process-wide default). That follows
from the sweep.

### D2 — the `runtime:` block: IMPLEMENT via the environment-variable route, GATED on investigation

**Ruled**: implement, and implement it as the **launcher exporting the BLAS variables** at cascor
bring-up — the process-tree-wide route — because that flexibility is what the owner wants. **Gated
on a rigorous re-investigation of the candidate-phase penalty first.**

The alternative was put to the owner explicitly and declined: routing the same flexibility through
`torch.set_num_threads` on the training thread would be **decoupled** — cascor's two width
mechanisms are independent, and only the environment-variable one reaches the candidate workers
(they inherit the ancestor's pool through `forkserver`; each child sets its own width at
`cascade_correlation.py:4153` from `worker_thread_count`, and `blas_threads.py` states that the
oversubscription guard does not depend on the variables at all). The owner's position: the
process-tree-wide knob is the more flexible one, and the trade-off should be **re-opened only if
the penalty proves impossible to decouple from the width setting**.

**Gate before it lands — what the investigation must measure:**

1. **Both phases**, output and candidate, under the same budget. cascor#531 measured the candidate
   phase only, and the initial output pass moves the *other* way.
2. **A sweep of cap values**, not cap-vs-uncapped — because §1 shows both penalty channels shrink
   as the budget rises. The question is not "does a cap cost 52%" but "at which cap does the cost
   become acceptable".
3. **On current code.** cascor#531 predates the tree as it stands.
4. **Epoch counts per phase**, for the same reason as D1.

**Not decided**: the key's final name, and whether a second per-thread knob is also offered.

### D3 — PF-3: UNBLOCK VIA D2, still await a quiet host

**Ruled**: once D2 lands, re-express PF-3's second axis against the key that actually binds, then
hold for a quiet window. **Verify with a one-cell dry run that the cell's `thread_env` is non-null
before committing the ~6.7 h matrix** — that is the check whose absence let the inert axis survive
approval in the first place.

**Still gated on**: a 1-minute load under 3, which has not occurred in four sessions.

### D4 — PF-2: RETARGET at the candidate phase, and ADD TWO AXES

**Ruled**: the owner concurs that points-per-spiral is meaningless **in the 250 → 2000 range**, and
retargets the scenario at the candidate phase — varying **candidate pool size** and **candidate
epochs**, where the work genuinely is emergent. Two additions, both the owner's:

1. **Wall-time characterisation over a far wider dataset range — 250 → 500,000 points per spiral.**
   Worth having in its own right even though the 8× range was inert; the inertness finding bounds
   only the range that was measured.
2. **Number of spirals per dataset is likely the more interesting axis.** The spiral problem becomes
   intractable quickly as spirals increase, so the evaluatable range is expected to be small —
   **certainly ≤ 10 and probably ≤ 6**. A short axis with real dynamic range beats a long one that
   measures an invariant.

**Not decided**: the exact cell counts and budgets; these need the usual floor/wall calibration
(clear the scrapeability floor at the smallest cell, stay inside `max_wall_seconds` at the largest)
rather than a guessed number.

### D5 — the CI hazard: MOVE THE FLOOR CHECK to the execution path

**Ruled**: relocate the cascor version-floor check out of `run_suite.load_suite` and onto the
execution path — **still before any cell launches, still fail-closed, still reported by
`--dry-run`**. Structural validation (what the R-6 drift gate exercises) then no longer needs a
cascor sibling, so a parallel cascor suite can live under `suites/perf/` without reddening CI.

The two alternatives were declined: keeping the arm in `util/ad-hoc/` contradicts §3 of the P1
design, and giving the gate a fixture tree "teaches the gate to lie about the tree that would
launch".

**Gate**: the relocated guard protects run evidence, so it ships with **its own negative tests** —
a suite that would launch against a below-floor tree must still be refused, and that refusal must
be proven by test rather than assumed.

### D6 — `epochs_completed` exact-match gate: RE-MEASURE FIRST

**Ruled**: do not gate yet. The *thesis* is established — `epochs_completed` is emergent for the
candidate micro-benchmarks, structurally like `step_count` — but the reference value is not stable
enough to gate on equality: round 1 observed requested-100 → **52**, round 2 → **68**. A gate whose
reference moves with ambient load is a flaky gate.

**Gate**: characterise the spread under controlled conditions, then decide whether exact-match is
safe. Only **1 of the 5** cascor micro files is affected (`test_micro_candidate.py`); the other four
are genuinely fixed-count and need no gate either way.

**Not decided**: whether the gate is built. This ruling buys the measurement, not the gate.

---

## 3. What is executable now, and what is host-bound

| decision | next action | host-sensitive? |
|---|---|---|
| D5 | relocate the floor check + negative tests | **no** — pure code |
| D4 | re-specify the scenario (axes, calibration plan) | **no** — document work |
| D1 | thread-width sweep of the later output passes | **yes** — timing |
| D2 | two-phase cap sweep on current code | **yes** — timing |
| D6 | `epochs_completed` spread characterisation | **yes** — that *is* the measurement |
| D3 | blocked on D2, then a quiet host | **yes** |

**The host has not been quiet in four sessions** (1-minute load 9–20 across this session's own
evidence files, with a 21-hour `clamscan` running). The three timing measurements must therefore be
designed for a **loaded** host — interleaved or randomised arm ordering with enough repeats to
separate signal from ambient drift — or they will measure the shell. Structural discriminations
(thread counts, which library, which stage) are load-insensitive; **wall-clock magnitudes are not.**

---

## 4. Provenance

Put to the owner and ruled 2026-09-11, in the session that shipped
`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`
(`juniper-ml#1896`, merged `4b13f318`). D1 and D4 were ruled as free-text direction rather than a
menu selection, and are transcribed here in the owner's own terms. D2's ruling was given **after**
the decoupling alternative and the 1.52× correction were both put; it is a reaffirmation, not an
uninformed choice.
