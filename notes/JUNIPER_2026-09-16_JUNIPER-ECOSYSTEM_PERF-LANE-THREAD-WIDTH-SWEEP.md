# Thread-width sweep: only width 16 is distinguishable, the environment route DOES work, and cascor#531's penalty does not reproduce

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-16, **substantially corrected 2026-09-17**
**Status**: D1 ANSWERED (no evidence to change 2; widths 2–8 are below this host's resolution). D2's gate ANSWERED IN THE ROUTE'S FAVOUR — the environment route works and the feared penalty does not appear. The §5 residual is CLOSED, and closing it invalidated the first run.
**License**: MIT License

---

## 0. What this document is

The measurement gating owner decisions **D1** and **D2** of
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md).

- **D1**: is width 2 actually optimal for the *later* output passes, or merely what cascor's
  constructor formula `max(2, worker_thread_count * 2)` happens to produce?
- **D2**: ruled "implement the `runtime:` block via the environment-variable route", **gated on**
  a sweep of cap *values*, on current code, with both phases measured.

Instrument: `util/ad-hoc/2026-09-16_thread_width_arm.py`, driven by
`2026-09-16_thread_width_sweep.py`. 6 widths × 2 mechanisms × 3 repeats + an untouched control,
**order reshuffled every repeat** from a recorded seed. Evidence:
`~/.local/state/juniper-experiments/suites/d1-d2-width-sweep-20260917-corrected/`.

> ## ⚠ THE FIRST RUN WAS INVALID, AND ITS CONCLUSIONS ARE WITHDRAWN
>
> The 2026-09-16 run's arm called **`torch.get_num_threads()` on the training thread** before
> training. That getter is **not a passive read** — it runs torch's per-thread lazy init and
> **re-pins the caller to the global** — which this lane established and documented on 2026-09-11
> (`JUNIPER_2026-09-11_..._ICV-INSTRUMENT.md` §1.1). It re-pinned every `env` and `none` arm to
> the constructor's 2 **before any training ran**.
>
> **It corrupted only SOME arms, which is why it survived review.** In the `thread` arms
> `set_num_threads(W)` had already made the global `W`, so the getter re-pinned to the value that
> was wanted anyway and left no trace. The `env` and `none` arms had no such protection and were
> silently flattened.
>
> Proof, one line apart, same host, same day:
>
> | arm | `icv_in` at initial pass | initial pass |
> |---|---|---|
> | `none`, **with** the getter | 2 | 2.67–2.83 s |
> | `none`, **without** it | **16** | **4.31 s** |
>
> The withdrawn conclusion was "the environment-variable route binds nothing". **It was measuring
> the instrument.** §2 below is the corrected result and it says the opposite.

---

## 1. D1 — only width 16 is distinguishable; 2–8 are below this host's resolution

Later output passes, median of 3, `thread` mechanism. **Two independent runs, both valid** (the
`thread` arms were not affected by the getter defect):

| width | run 1 (09-16) | run 2 (09-17) | run-1 rank | run-2 rank |
|---|---|---|---|---|
| 2 | 1.542 | 1.970 | **1st** | 4th |
| 4 | 1.669 | 1.833 | 2nd | 2nd |
| 6 | 1.789 | 1.970 | 4th | 3rd |
| 8 | 1.828 | **1.736** | 5th | **1st** |
| 10 | 1.782 | 2.457 | 3rd | 5th |
| 16 | 11.439 | 9.799 | 6th | 6th |

**The rank order of 2, 4, 6 and 8 completely reverses between runs.** Run 2's spreads show why:
w2 spans 1.510–2.117 and w8 spans 1.698–1.775 — they overlap, as do 4 and 6. The 8–19% gaps that
looked monotone in run 1 sit inside this host's known drift band (13–20.5%), so they are **not
measurable here**.

**What IS robust**: width **16** is 5–7× worse in both runs, by a margin no amount of drift
explains. Width 10 is worse than 2–8 in run 2 but not in run 1, so even 10 is unproven.

**D1's answer**: there is **no evidence to change 2**, and no evidence that 2 is specifically
optimal either. The honest statement is that any width in 2–8 performs the same on this host, so
the constructor's 2 is a perfectly good choice and widening it buys nothing. D1's premise was
right — nobody had validated 2 — but the validation returns "indistinguishable", not "optimal".

> **Run 1 alone would have produced a confident, monotone, wrong story.** Its spreads were tight
> (w2 1.539–1.610) and the ordering looked clean. Only the second run revealed it as noise. One
> run of a wall-clock sweep on a contended host is an anecdote.

---

## 2. D2 — the environment route WORKS, and cascor#531's penalty does not reproduce

> ## ⚠ CORRECTION 2026-09-22 — the column headed "initial pass" IS NOT THE INITIAL PASS
>
> `util/ad-hoc/2026-09-16_thread_width_arm.py:229-231` computes
> `initial = [s for s in stages if s["stage"] == "train_output_layer"]` and sums **all** of
> them. cascor emits that stage name **once per output pass, not once per run** — every
> evidence file carries **five** of them — so `initial_pass_seconds` is
> *first pass + every later pass*, i.e. total output-training time. Verified on the raw
> records, where it reconciles to four decimal places:
>
> | arm | reported "initial pass" | TRUE first pass | reported `later_passes_seconds` | first + later |
> |---|---|---|---|---|
> | `none` (control) | 8.2453 | **6.3594** | 1.8864 | 8.2458 |
> | `env w2` | 3.2333 | **1.1833** | 2.0505 | 3.2338 |
> | `env w16` | 3.6470 | **2.0404** | 1.6070 | 3.6474 |
> | `thread w16` | 11.9759 | **2.1772** | 9.7991 | 11.9763 |
>
> **What survives.** `later_passes_seconds` and `candidate_seconds` filter on different stage
> names and are **clean**, so §1 (D1's width comparison) and §2's point 3 (cascor#531's penalty
> does not reproduce) are unaffected. So is point 1 — `icv_in` is read per stage and is not a
> duration at all. **The route still works, and capping still helps.**
>
> **What changes.**
> - **Point 2's "−33%" is measured on the wrong quantity, and it UNDERSTATES the effect.**
>   Capping is a bigger win on the true initial pass than the note claims, not a smaller one.
>   The medians behind the −33% are totals; do not re-quote the percentage until it is
>   recomputed from first-pass figures.
> - **§2.1's "3.3× gap at identical OpenMP width" does not evidence what it is used for.**
>   `thread w16`'s 12.295 s is dominated by its own 9.799 s of later passes. On the **true
>   first pass** the two arms are 2.1772 (`thread w16`) and 2.0404 (`env w16`) — within noise.
>   The mechanism claim itself (only `thread` also moves torch's *global*) is **not** refuted,
>   and `thread w16` really is far slower overall — but the slowness lives in the **later
>   passes**, not the initial one, and §2.1 attributes it to the initial one.
>
> This is the *instrument answers an adjacent question* class: the metric was correctly
> computed and incorrectly named, and every reader inherited the name. Found while re-probing
> this note for
> [`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`](JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md).
>
> **A second, independent gap in the same instrument**: D1's gate demanded *"epoch count and
> total wall time"* and D2's item 4 demanded *"epoch counts per phase"*. The arm emits
> `later_pass_count` and `candidate_phase_count`, which count **stages**, and the string
> `epoch` appears in **none of the 40 evidence files** — though the arm's own docstring
> (`:54`) claims it reports *"epochs completed and the final accuracy"*. Point 3's
> "does not reproduce" therefore rests on candidate-phase **wall time** alone, which cannot
> separate *no effect* from *two effects cancelling* — and §1 of
> [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md)
> records exactly two channels moving in opposite directions.

Corrected run. `init_icv_in` is the OpenMP width **actually in force during the initial pass**,
read per stage:

| arm | `icv_in` | initial pass (med) | spread | candidate phase (med) | spread |
|---|---|---|---|---|---|
| env w2 | **2** | **2.705** | 2.64–3.23 | 2.945 | 2.88–3.49 |
| env w4 | **4** | 2.878 | 2.75–3.01 | 3.111 | 3.00–3.25 |
| env w6 | **6** | 2.911 | 2.78–3.01 | 3.492 | 3.13–3.59 |
| env w8 | **8** | 2.928 | 2.84–3.50 | 3.267 | 2.94–3.78 |
| env w10 | **10** | 3.964 | 2.90–4.23 | 3.789 | 3.07–3.93 |
| env w16 | **16** | 3.777 | 3.65–8.25 | 3.030 | 2.97–3.44 |
| **none** (unset) | **16** | **4.060** | 3.76–8.25 | 3.046 | 3.04–3.96 |

**1. The route works.** `icv_in` equals the requested width in every arm — the BLAS variables do
set the training thread's width for the initial pass. This is the direct refutation of the
withdrawn §2.

**2. Capping helps the phase it was meant to help.** The untouched control runs the initial pass
at **4.060 s**; capped at 2 it runs at **2.705 s** — a **33% reduction**, and the control's width
is 16, exactly the unpinned burst this lane has been chasing since 2026-09-10.

**3. cascor#531's candidate-phase penalty DOES NOT REPRODUCE.** Across an 8× cap range the
candidate phase spans 2.945 → 3.492 s with spreads that all overlap (e.g. w2 2.88–3.49 against
w16 2.97–3.44). **There is no detectable cost at any cap**, least of all the 1.52× that was the
stated reason to investigate before implementing.

**Why not, most likely**: the candidate workers pin *themselves* at
`cascade_correlation.py:4153` from `worker_thread_count`, so the inherited environment does not
govern their width. cascor#531 measured a different tree; this is not a refutation of that
measurement, it is a statement about current code.

### 2.1 The two mechanisms are not interchangeable, and the difference is visible

`thread` w16 and `env` w16 both run the initial pass at `icv_in` 16, yet take **12.295 s** and
**3.777 s** respectively — a 3.3× gap at identical OpenMP width. The difference is torch's
**global**: `thread` sets it to 16, `env` leaves it at the constructor's 2. So two widths are in
play — torch's intra-op count and libgomp's per-thread ICV — and only `thread` moves both.

**Consequence**: `thread` w16 is an artificial worst case that no production configuration
produces, and it should not be read as "what the burst costs". The realistic burst is the
**`none`** row (4.060 s against 2.705 s capped).

---

## 3. What this means for the two decisions

**D1**: closed, with a weaker claim than run 1 suggested. Keep 2. No tuning headroom exists, and
none of 4/6/8 is distinguishable from it on this host.

**D2**: **the gate passes.** The owner chose the environment-variable route for its flexibility and
gated it on this investigation. The route **does** control the initial-pass width, capping **does**
remove the burst it was aimed at (−33%), and the penalty that justified the gate **does not appear
at any cap value on current code**. Nothing here argues against implementing it.

> **This reverses what I reported on 2026-09-16.** That report said the route was inert and put the
> decision back to the owner. It was wrong, for the instrument reason in §0, and the correction is
> in the route's favour.

---

## 4. What is NOT claimed

- **Not** that cascor#531 was wrong — different tree, different comparison (§2).
- **Not** that 2 is optimal — only that nothing in 2–8 beats it measurably (§1).
- **Not** a run-tier figure. 1-minute load ~5–6 with a `clamscan` competing throughout.
- **Not** a claim about the service. Every arm is one process constructing on main and training on
  a worker — the service's *shape*, not the service.
- **Not** "the candidate phase is unaffected by thread budget" in general — only that no effect is
  detectable across caps 2–16 in this configuration, with overlapping spreads at n=3.

---

## 5. Residual from the 2026-09-16 draft — CLOSED

That draft recorded a disagreement between this sweep and the 2026-09-11 ICV work about whether
the unpinned case bursts, and guessed the difference was the BLAS variables being set versus unset.

**Both halves of that were wrong.** The `none` control has the variables *unset* and was corrupted
identically, so the variables were never the difference; and re-running the 09-11 instrument
unchanged on the current environment reproduces the burst exactly (`icv` 16 through
`train_output_layer`). The difference was the getter call in §0 — **my instrument, not the system**.
Nothing about the 3.13 → 3.14 environment upgrade changed the burst.

**The lesson worth keeping**: this hazard was discovered by this lane, written into its own note,
and recorded in project memory — and the next instrument written by the same author walked into it
six days later. Prose warnings do not bind. The guard belongs *inside* a shared helper that
instruments cannot bypass.
