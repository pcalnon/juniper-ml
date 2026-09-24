# Perf lane: the six open owner decisions, RULED 2026-09-11

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-11
**Status**: all six RULED by the owner in session; four carry an execution gate before they land. **The four `Not decided:` clauses were RULED 2026-09-22/23 — §5.**
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

> **RULED 2026-09-23 (§5): the process-wide default, but only AFTER the epoch-count debt is
> paid.** The default is set only when the variables are unset, so a width the D2 launcher
> exports still wins. The mechanism already exists and currently defaults to "do nothing" for
> cascor#531's reason, so the ruling reverses that policy, and it lands only if an epoch-count
> measurement shows the cap does not move the count.

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

> **RULED 2026-09-22 (§5): ratified as-is** (`blas_threads`, `num_processes`,
> `eval_metrics_enabled`), and **no second knob**.

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

> **Axis 2's RANGE was RULED 2026-09-22 (§5)**: 250 → 10,000 on the suite path now. The top end
> goes through cascor's in-process generator later, and only if the curve shows a knee. The cell
> counts and budgets stay a calibration, as stated above. **The suite path's real ceiling turned
> out to be 5,882, not 10,000** (§5.3), so the suite built from this ruling stops at 5,800.

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

> **RULED 2026-09-22 (§5): build it ADVISORY first.** It never fails a build; it counts how often
> it fires on real cascor PRs, and that count decides whether it later blocks.

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

---

## 5. The four `Not decided:` clauses, RULED 2026-09-22/23

Four of §2's rulings ended with an explicit **Not decided** clause. The 09-22 handoff
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md`
§1) found all four still open. Reading "ruled" as "closed" had hidden that for eleven days. They
were put to the owner as a menu on 2026-09-22 and ruled in one sitting, except D1, which was
put a second time and ruled 2026-09-23 (§5.2). The table records the
options that were put **and declined**, so each ruling reads as a choice rather than a default.

| | clause | ruling | put and declined |
|---|---|---|---|
| **D2** | the key's final name; whether a second per-thread knob is offered | **Ratified as-is**: `runtime.blas_threads`, `runtime.num_processes`, `runtime.eval_metrics_enabled`. **No second knob.** | rename the width key and keep a deprecated alias; add a per-thread knob that pins only the training thread |
| **D1** | which repair mechanism | **Process default, after the debt is paid.** cascor's existing `configure_blas_threads()` (called at both entrypoints, before anything imports BLAS) changes its default from "do nothing" to **2** for `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS`, still **only if unset**. It lands **only after** the width-sweep arm emits `epochs_completed` per phase and the count does not move with the cap (§5.2) | flip the default now, on wall time alone; pin on the training thread; leave the defect unrepaired |
| **D4** | the range of axis 2 | **10,000 now, in-process later.** Sweep 250 → 10,000 points per spiral on the suite path now, and probe the top end through cascor's in-process generator **only if** that curve shows a knee | cap at 10,000 with no follow-up; raise `MAX_POINTS` in juniper-data; in-process only |
| **D6** | whether the gate is built | **Advisory first.** Build it non-blocking, count how often it fires on real cascor PRs, then decide whether it blocks | build it blocking; do not build it |

### 5.1 D2: what ratification buys

- **Nothing migrates.** The three names already have committed users:
  `juniper-cascor/conf/experiments/{spiral-smoke,spiral-baseline,xor-staged}.yaml`, seven
  `util/ad-hoc/*.yaml` suites, and `reports/p01-logging-corpus-2026-09-22/cell.yaml`. The
  deadline pressure that made this urgent (every new user raises the cost of a rename) is gone.
- **"No second knob" leaves §2 D2 as it was.** A per-thread knob would reach the training
  thread and never the candidate workers. That decoupling is why the environment route was chosen
  in the first place.

### 5.2 D1: constraints the repair must honour

- **It was ruled twice, and the second ruling is the one that stands.** The first menu described
  the process default as new work. It is not: `juniper-cascor/src/parallelism/blas_threads.py`
  already provides `configure_blas_threads()`, which `main.py` and `api/__init__.py` both call
  before anything imports BLAS. It is opt-in through `JUNIPER_CASCOR_BLAS_THREADS`, it only sets
  variables that are unset, and it defaults to **"do nothing"** on purpose. That default exists
  because cascor#531 measured the capped candidate phase at 1.52×, and
  `tests/unit/test_blas_thread_policy.py::test_default_is_a_no_op` pins it. The session caught
  the omission, put the corrected question on 2026-09-22, and on 2026-09-23 the owner ruled **"pay the debt,
  then flip"**.
- **The debt is the D1/D2 gate's missing epoch counts.** Both gates required epoch counts per
  phase, and `util/ad-hoc/2026-09-16_thread_width_arm.py` emitted **stage** counts instead. The
  09-16 finding that "#531's penalty does not reproduce" therefore rests on wall time alone, which
  cannot tell *no effect* from *two effects cancelling*. #531's second channel was epoch count:
  the cap changed BLAS reduction order and so moved where patience-based early stopping
  terminated. So: add per-phase `epochs_completed` to the arm, re-run the sweep, and flip the
  default only if the count does not move with the cap. The count is structural, so this can run
  on a loaded host.
- **"Only if unset" is load-bearing.** The D2 launcher delivers `runtime.blas_threads` to the
  cascor process through the inherited environment. An unconditional assignment in cascor would
  silently override the width every suite names, which is exactly the class of defect D2 closed.
- **Size the benefit against one phase.** The defect costs the **initial output pass only**: the
  training thread is re-pinned to 2 during the first candidate-result collection and stays there.
  Capping that pass is worth **−49.2%** of it (2.2838 s → 1.1593 s, medians of 3; the width
  sweep's §2 correction in
  [`JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`](JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md)).
  It is not a whole-run regime.
- **The width value is already answered, though not by §2.** §2 ruled only "measure first". The
  width sweep did the measuring and found 2 to 8 indistinguishable, so its verdict was "keep 2"
  (its §1): no evidence to change 2, which is weaker than evidence that 2 is optimal. What happens
  to the constructor pin at `cascade_correlation.py:1180`
  (`max(2, worker_thread_count * 2)`) once a process default exists is an implementation question.
  The cascor PR must answer it rather than leave two mechanisms that disagree.

### 5.3 D4 axis 2: what the ruling does not relax

- **The suite path stops at 5,882, not at the 10,000 the ruling was given.** The driver stages
  its dataset through juniper-data, whose `MAX_POINTS` (10,000) is a Pydantic bound. See §1 of
  [`JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`](JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md).
  The menu put to the owner, and that document, both treated 10,000 as the request ceiling. **It
  bounds the TOTAL rows per spiral.** juniper-data's additive sizing treats the request as the
  train count and adds val and test on top: 1.7× at the suite's split, so a request of 10,000
  becomes an internal 17,000 and is rejected. Bisected 2026-09-23: 5,882 accepted, 5,883
  rejected. The rejection is a 400 "Invalid request parameters" with the cause logged only at
  DEBUG, so the cell reads `torn_down_early` after about 18 s. **The built suite
  (`util/experiments/suites/perf/pf2-axis2-cascor-dataset-range.yaml`) therefore stops at 5,800**,
  a range of about 23×. That is still roughly three times wider than the 8× range that measured an
  invariant, but it is not the 40× that was ruled on. The in-process follow-up is unaffected: it
  never touches juniper-data.
- **The PF-2 re-spec's §3 obligations still hold**: `continue_on_failure: true`, a raised
  `max_wall_seconds`, and any breach reported explicitly in the aggregate. The same document's
  section on the wall-ordering survey applies too.
- **An in-process follow-up measures cascor's own generator, not juniper-data's.** They are
  separate implementations (re-spec §1), so those figures must never be quoted as juniper-data
  figures.

### 5.4 D6: what "advisory" means here

- **Scope**: `juniper-cascor/src/tests/performance/test_micro_candidate.py`, budgets **100 and 200
  only**. At 10 and 50 the count equals the request, so a gate there asserts a tautology.
- **The reference records the cascor SHA and the thread pin.** Without them, an intended numeric
  change reads as a flake, which is how work gates get switched off.
- **The advisory period answers the question D6's measurement could not.** §4 of
  [`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`](JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md)
  asks whether the gate's tree-sensitivity is its value (it catches silent numeric drift) or its
  cost (it fires on intended changes). How often it fires on real PRs is that answer.

> **COUNT, 2026-09-23 (first reading, cascor#682 + ~8 h): 0 firings on 6 head SHAs / 28
> `Unit Tests` legs.** Instrument: `util/ad-hoc/2026-09-23_d6_advisory_firing_count.py`. It
> enumerates workflow runs, not PR commits, because a PR's commit list forgets force-pushed heads,
> and cascor#683 was force-moved. A leg counts only if its tree contains the advisory and the leg
> actually ran; cancelled matrix placeholders are excluded. The six are #682's two heads, #683's
> head, #678's head and two `main` pushes. Only #683 and #678 are PRs other than the advisory's
> own, so **this is far too few to decide blocking**. It is a baseline, not a rate.
>
> **The zero is not vacuous: a positive control fired.** The annotation had never been seen in
> CI, so a zero could not yet tell "no drift" apart from "the annotation never reaches the
> runner". A throwaway branch (`ci-probe/d6-advisory-positive-control-20260923`, cascor `47d15dd`,
> run once through `workflow_dispatch`, then deleted) drifted the budget-100 reference to 67.
> **All 4 legs carried exactly one `D6 advisory - epochs_completed drift` annotation and all 4
> passed.** The counter excludes `workflow_dispatch` and `ci-probe/*` runs, so the control can
> never enter the count.
>
> **A cross-platform datum the reference did not have.** The reference was taken on Linux
> x86_64, Python 3.14.7 and torch 2.11.0+cu130. CI observed the same **68** on CPU-only
> **torch 2.14.0+cpu** under Python 3.12, 3.13 and 3.14 on Ubuntu, and under Python 3.12 on
> macOS. So the count survived a torch minor-version change and a platform change. Its
> tree-sensitivity is still untested: no PR in the window changed candidate numerics.

---

## 6. Three scheduling and instrument rulings, 2026-09-24

The 2026-09-23 handoff
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_perf-lane-d1-debt-clear-flip-pf1-rebaselined-pf2-axis2-ceiling-5882.md`)
left PF-3's host time and the micro timing cut as open items. Its residue check found a third:
PF-2 axis 1, which was ruled in §2 D4 and then dropped from two successive work lists. All three
were put to the owner as one menu on 2026-09-23/24. As in §5, the declined options are recorded
beside each ruling.

| | question | ruling | put and declined |
|---|---|---|---|
| **PF-3 host time** | the matrix needs ~7 h per pass (~21 h for 3 round-robin passes), and it measures wall-clock speedup up to 16 processes | **Wait for a quiet window**: hold until the two `clamscan` processes finish and the 1-minute load stays under ~6 | run now on the loaded host, round-robin; the owner frees the host and signals |
| **Micro timing cut (PF-4)** | never cut under Python 3.14; seven sessions deferred it waiting for an idle host | **Cut now, labelled LOADED.** It is report-only, it records its own load average, and a later quiet cut supersedes it by number | keep waiting |
| **PF-2 axis 1 instrument** | the axis needs each candidate's `epochs_completed` per cell, but no structured suite artifact carries it; only the log does, and only for candidates that stop early (PF-2 re-spec §2 note) | **Publish it in cascor**: a structured per-phase record, e.g. a `metrics_history` entry carrying each candidate's `epochs_completed` | parse the cascor log (absence is load-bearing, and log formats are mid-redesign); defer axis 1 |

**The window opened and closed within minutes, and PF-3 did not launch.**

- **02:39 local, 2026-09-24**: both `clamscan`s had exited and the load was 4.20 / 4.09 / 3.48.
- The micro cut took the window first, because the two measurements must not overlap:
  `Linux-CPython-3.14-64bit/0001`, cascor `0e016a7`, 1-minute load 5.54–6.55 while it ran.
- **Minutes later** a peer session's juniper-data unit-test run put the 1-minute load at
  **8.97**. That fails "stays under ~6", so PF-3 was held, as ruled.

The lesson for the next attempt: **"quiet" at night is still not unattended.** Peer sessions run
test suites around the clock. A single ~7 h pass needs the load watched at launch and recorded
throughout; `util/ad-hoc/2026-09-08_loadavg_sampler.py` alongside the suite does that.
