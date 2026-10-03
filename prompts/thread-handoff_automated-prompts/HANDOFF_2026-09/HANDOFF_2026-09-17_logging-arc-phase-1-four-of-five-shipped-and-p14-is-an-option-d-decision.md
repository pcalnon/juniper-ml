# HANDOFF 2026-09-17 — logging arc: Phase 1 four-fifths shipped, and P1.4's second half is an Option D decision, not a wiring chore

Successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_logging-redesign-arc-documents-merged-no-phase-started.md`
(the **predecessor**; every bare "the predecessor" below means that file).

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`).

> **UPDATED 2026-09-21 — READ §0.0 FIRST.** This document was validated against both repos on
> 2026-09-21 by one independent agent plus a five-agent consensus review (Lane A ×3 distinct entry
> points, Lane B ×2 opposing briefs) per
> [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
> Its state claims all hold. **Five of its factual claims do not**, one whole remaining-work item
> (§0.5) is moot, and the measurement §0.1 step 2 asked for has been taken — and it **reframes the
> P1.4 decision**. §0.0 carries all of it. Where §0.0 and a later section disagree, §0.0 is current.
>
> **SUPERSEDED 2026-09-22 — the title of this document is now wrong.** P1.4's second half was
> **not** an Option D decision: §0.0.5(a) shows `log_if_enabled` is not §11's Option D at all. The
> owner ruled the hoisted-guard + `%`-args idiom on 2026-09-22 and **Phase 1 is complete**. See the
> banner at §0.1.

**A bare "§N" means a section OF this document.** Every reference to another file names it. This
document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`.
All dates UTC.

**The arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573), still OPEN.
Roadmap of record: `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
Design of record for P4: `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`.
Recon: ~~`notes/JUNIPER_2026-09-01_JUNIPER-CASCOR_LOGGING-RECON.md`~~ — **no such file; corrected
2026-09-21 to `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`**
(§0.0.2 correction 2).

**The one thing to hold in mind.** The predecessor handed over an arc blocked on six owner
decisions with no phase started. All six are now ruled and recorded in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, and Phase 1 is four-fifths
shipped. What remains of Phase 1 is **one half-step, and it is not mechanical**: the owner ruled
P1.4 as "**C — Adopt: fix the levels and wire it to a real call site**". The fix half is done and
checkpointed. The wire half, done the obvious way, **adopts migration-analysis Option D** — and
§11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` says Option D and a
queued P7 writer "**must not be adopted independently**". See §2. Do not treat it as a chore.

---

## 0.0 Update 2026-09-21 — verified, five corrections, and the measurement that reframes P1.4

Nothing in this arc moved between 2026-09-17 and 2026-09-21. No P1.4 PR was opened; the three
open `juniper-cascor` PRs are that morning's dependabot bumps (#655–#657).

### 0.0.1 Verified and still TRUE

Re-probed against both repos, not re-read from this document:

- All six PRs MERGED: #644, #647, #648, #652, #653, #654.
- `juniper-cascor` `main` working tree clean **except** `.serena/project.yml`, as §6 says.
- `wip/logging-p14-adopt-logging-utils` at `1b918e6`, pushed, **no PR open**, commit **unsigned**,
  touching exactly the three files §6 names.
- **47 passed, exit 0**, re-run 2026-09-21. Confirmed non-vacuous (47 tests actually collected).
- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) still OPEN — and it carries
  **zero comments**. See correction 3.
- **Every line number in §0.1 step 3 is exact**: `_display_training_progress` at `:728`, `debug` at
  `:730`/`:731`, the rare-branch `debug` pair at `:734`/`:735`, the frequency-gated `info` at
  `:740`, `verbose` at `:742`, `_tensor_brief` at `:702`. `self.logger = Logger` at `:187` — though
  there is a **second identical binding at `:296`** this document does not mention.
- `src/profiling/logging_utils.py` has **zero** production importers. `src/profiling/__init__.py`
  exports only `deterministic` and `memory`. It is dead code, exactly as §0.1 assumes.
- The `~872` figure reproduces **to the digit** at the census commit, by the method published in
  `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`.
- §0.3 (P6.4) and §0.4 (P0.1/P0.2) are both still unstarted — no artifacts exist for either.
- Trap §5.4, §5.5 and §5.6 all reproduced in the course of writing the benchmark below. §5.5's
  guard fired on its own first draft.

### 0.0.2 Five claims that are now FALSE or STALE

1. **§5.1 and §0.5 are obsolete — `JuniperCascor1` is REPAIRED.** torch **2.11.0+cu130** now
   imports cleanly under `lib/python3.14/site-packages`, **with or without** `env -u LD_LIBRARY_PATH
   -u LIBTORCH`. The two P1.4 suites run **47 passed, exit 0** under
   `/opt/miniforge3/envs/JuniperCascor1/bin/python`. The repair landed 2026-09-15 and is recorded in
   `Juniper/AGENTS.md` § Conda Environments. **§0.5 is therefore MOOT — do not ask the owner a
   fourth time; there is nothing left to rule.** The `/tmp/claude-1000/cascorenv` venv still works
   and is still what the benchmark below was run under, but it is no longer *required*, which
   removes this arc's dependency on a tmpfs path that a reboot would reap.
2. **The recon file named in the front matter does not exist.** There is no
   `notes/JUNIPER_2026-09-01_JUNIPER-CASCOR_LOGGING-RECON.md` anywhere in the repo, and the only
   reference to that name in the entire tree is this handoff. The evidence base is
   **`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`**, which §15
   of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` names as such.
3. **§4's "All are recorded canonically in §13.1" is FALSE for two of its four items.** §13.1 of
   `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` carries seven rulings.
   Decisions 5 and 6 there are §4's items 2 and 3. But **neither the P1.4 option-C ruling nor the
   blanket merge approval appears in §13.1, or anywhere else in that file** — grep for `P1.4`,
   `option C` and `merge approval` returns only the unrelated phase table at `:229`. Combined with
   cascor#573 having zero comments, **the P1.4 ruling this entire document turns on exists in no
   durable record.** Writing it down is now a remaining-work item (§0.0.6).
4. **§6's "up to date with origin" has drifted.** `juniper-cascor` `main` is one commit behind
   `origin/main`: `c6c848f` (#658) landed after this handoff was written.
5. **`~872` is 874 at current `main`** — +2 drift over 38 commits. The `~` keeps the phrasing
   defensible; do not restate `872` as a current number. Re-derived twice, independently, with
   `util/ad-hoc/2026-09-21_p14_suppressed_site_census.bash`: **872** at census commit `70edfc4`
   (reproducing every intermediate row published in
   `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`) and **874** at
   `main`. **Re-derivation trap**: `git grep` walks the *tracked* tree; `src/backups/check.py` is
   **untracked** and carries ~68 more `debug` sites, and the dead tree is
   `src/cascade_correlation/backups/`, **not** `src/backups/`. A plain `grep -r` over the working
   tree lands near 1,144 and reads as though the roadmap were wrong.

### 0.0.3 The WIP branch's own commit message is wrong where this document is right

`1b918e6`'s body says the target holds *"three UNGUARDED f-string log calls (two debug at
`:731-732`, one verbose at `:743`)"*. Both halves are wrong, and this handoff is right:

- **Off by one on every line**: the truth is `debug` at `:730`/`:731` and `verbose` at `:742`.
- **Not three f-strings — two.** `:730` is a **constant** string
  (`"CandidateUnit: _display_training_progress: Checking if training progress should be displayed"`).
  It costs a call, not an interpolation. The perf case for adoption rests on interpolation cost, and
  there is two-thirds as much of it as the commit message claims.

If a successor reconciles the two, **trust this document and re-derive from source; the commit
message is the stale artifact.**

### 0.0.4 The measurement §0.1 step 2 asked for — taken, and it inverts the question

Instrument: `util/ad-hoc/2026-09-21_p14_guard_idiom_bench.py` (named for the day it was written, not
the `2026-09-17` the step proposed). Independently re-created from scratch by a second agent as
`util/ad-hoc/2026-09-21_p14_independent_remeasure.py`. Both drive the **real** cascor `Logger`, bound
as a **class**, at a disabled configured level, with the real `:742` message.

Reconciled across three independent entry points — source-analytic, two separate instruments — in
ns per call, at the **disabled** level:

| idiom | ns/call | note |
| --- | --- | --- |
| hoisted boolean local | **~10–60** | the floor |
| `Logger.isEnabledFor()` alone | **~1,000–1,300** | **not memoised** |
| the f-string alone | **~1,017** | tensor `.shape` + `.dtype` |
| suppressed `verbose(CONST)` | **~1,353** | emit path, no interpolation |
| suppressed `verbose(f"…")` | **~2,300–2,700** | **today's code at this site** |
| `log_if_enabled(…, lambda: …)` | **~1,200–1,400** | Option D |
| closure allocation alone | **~80–240** | the cost §11 warned about |

**The closure allocation §11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
warns about is real but small — ~80–240 ns. It is not what matters here.** Two much larger things
were found instead, both verified directly at source:

- **`isEnabledFor` costs more than the interpolation it exists to prevent** (~1,000–1,300 ns vs
  ~1,017 ns). `logger.py:1098` is `cls.getLevelNumber(cls.get_level())` — five classmethod frames,
  three `.upper()` allocations and two linear scans to re-derive `"INFO" → 20`, **on every call,
  forever**. The `_level_number_cache` memo at `logger.py:235` is wired **only** into the emit
  filter `_filter_by_level`, never into the guard. Guarding a constant-string suppressed call
  therefore saves about **7 %**.
- **A suppressed call pays a frame capture and a `datetime.now()` unconditionally.**
  `logger.py:620` is
  `cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level=…, message=message, args=…)` — and
  `_frm`/`_tsp` (`logger.py:130-131`) are evaluated **as arguments**, before `_log_at_level` reaches
  its level test. `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`
  already records this as **NOT DONE**.

**The ladder at this site, per suppressed call** — this is what the decision is actually choosing
between:

| # | idiom | ns/call | note |
| --- | --- | --- | --- |
| 1 | unguarded f-string — **today** | **~2,300–2,700** | |
| 2 | unguarded, `%`-args | **~1,353** | interpolation deferred **inside** the filter |
| 3 | `log_if_enabled` + lambda — **Option D** | **~1,200–1,400** | |
| 4 | hoisted guard — **already used in this very file** | **~10–60** | |

Verified at source for row 2: `logger.py:578` is `message = message % args`, sitting **inside** the
`if cls._filter_by_level(...)` block opened at `:575`. So `%`-args genuinely defer interpolation for
a discarded record, exactly as §13.1 decision 6 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` found (at line numbers now
drifted ~+55).

**Option D buys ~10 % over simply writing `%`-args, and costs ~25× the idiom the same file already
ships.** `train_detailed` hoists `_log_debug`/`_log_trace` at `candidate_unit.py:595-596`, *outside*
the epoch loop at `:601`, and its guarded sites at `:598`, `:604` and `:629` use `%`-args, not
f-strings. **`_display_training_progress` is an unconverted island inside a caller that already
demonstrates the target idiom.** The pattern to copy is local, and it is not `logging_utils`.

**A correction this measurement forces on the record.** §13.1 decision 5 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` reports "1,079 bound sites
55–77 ns and 109 class sites 74–89 ns against today's 95–110". Those figures came from
`util/ad-hoc/2026-09-10_p41_a2_delegation_bench.py`, which times **five hand-written stub classes**
and **never imports juniper-cascor at all**; it also times `debug`, never `isEnabledFor`. The
script and `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md` are honest
— both say "real **signature**" — but the word *signature* drops out in the roadmap's rendering, and
a signature match reads as a claim about what cascor costs. **The A2-bind ruling still stands**: all
five stubs share one body, so the *deltas* (A2-bind −21 ns, delegator +146 ns) survive intact. What
does not survive is the absolute framing — against a real ~1,000–2,700 ns per-call cost, a 21–40 ns
dispatch saving is 1–3 %, not the proportion "faster than the status quo on every call site"
implies. Decision 5's line citations have also drifted ~+55 lines (`isEnabledFor` is at `:1085`,
not `:1026`).

### 0.0.5 Two findings that change the decision — both verified at source

**(a) `log_if_enabled` is NOT §11's Option D. This document's central premise is overstated.**

§2 says "**That lambda is Option D**". Read against the definition, it is not. §4 of
`notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` defines Option D
as *"Extend **the logger** to accept a zero-arg callable and invoke it only after the level check"*,
illustrated as `self.logger.trace(lambda: f"…")` — the callable **crosses the logger API boundary**.
That is what can later meet a queue.

`src/profiling/logging_utils.py:229-230` is a different shape:

```python
if logger.isEnabledFor(level):
    _emit(logger, level, msg_func())
```

`msg_func()` is evaluated **as an argument**, in the caller's frame, before `_emit` is entered. What
reaches `Logger.verbose` is a plain immutable `str`. **The closure never escapes**, so there is
nothing for a deferred writer to re-render differently. The same §4 says so in terms: *"For a
post-filter-but-immediate invocation this is safe; it becomes unsafe the moment anyone defers the
message further (e.g. into a queue…)."*

**Consequence: wiring `log_if_enabled` does not foreclose P7, and §0.2's "record the P7 Option D
foreclosure" is asking for a ruling on a conflict this change does not create.** The foreclosure
question arises only if someone later moves the callable into `Logger`'s own signature — a separate,
separately-reviewable change. §11's hazard is real; it just does not bind here.

**(b) The chosen adoption target is the one place this import cannot go.**

`src/candidate_unit/candidate_unit.py` is **byte-gated** into the published `juniper-cascor-model`
package, and `profiling/` is **not** an extracted tree:

- `juniper-cascor-model/tests/test_drift.py:27` —
  `_EXTRACTED_DIRS = ("candidate_unit", "utils", "log_config", "cascor_constants")`
- `juniper-cascor-model/profiling/` **does not exist**
- `juniper-cascor-model/pyproject.toml:59-65` includes only `juniper_cascor_model*`,
  `candidate_unit*`, `utils*`, `log_config*`, `cascor_constants*`

So adding `from profiling.logging_utils import log_if_enabled` to `candidate_unit.py` forces the
byte-gate to mirror that import into a package with no `profiling/` — **`ImportError` on importing
`candidate_unit`, in a package live on PyPI**, while `src/` stays green. This is precisely the §5.2
trap ("the byte-gate mirrors the CALLER; nothing mirrors the CALLEE") that nearly shipped in P1.3.
**If `log_if_enabled` is wired at all, the first site must be outside the four byte-gated trees.**

**(c) P1.3 and P1.5 do not cover this site, so the defect class here is absence, not mis-naming.**
The 8 guard sites P1.3 fixed are `:596,597,764,765,766,833,834,1046` — none in
`_display_training_progress`. `src/tests/unit/test_logger_per_level_exercise.py:109-110` drives only
`_multi_output_correlation` and `_get_correlations`. So §2's correctness argument (the level stated
twice, once wrong) is **not** the live argument at `:728`; "there is no guard, and nothing tests that
there isn't" is.

**(d) The highest-value line in this whole review, and it belongs to no option.** `isEnabledFor`
should route through the memo the emit path already uses. `logger.py:1098` calls
`getLevelNumber(get_level())` → `_is_valid_level_name` → `_get_level_number`, doing `.upper()` twice
and scanning an 8-entry dict twice, per call. `_filter_by_level` instead calls `_resolve_level_number`
(`logger.py:526-543`) — two dict lookups. **#598 memoised the emit path and left the guard behind, so
the guard is now slower than the filter it exists to skip.** Routing it through the same helper is a
one-line change that collapses ~1,000–1,300 ns to roughly the cost of two dict lookups — and it makes
*every* guarded site in the codebase cheaper, whichever idiom P1.4 picks.

### 0.0.6 Lane B verdict — two opposing briefs, and they converge

Run per
[`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
§2 Lane B: one agent briefed to argue **for** wiring, one **against**, each required to name the
fact that most weakens its own case. **They agree on every operative point**, which is the strongest
signal this review produced:

| both sides agree | |
| --- | --- |
| the un-memoised `isEnabledFor` is the **highest-value fix**, belongs to **no option**, and is ~one line | verified: `logger.py:1098` vs `_filter_by_level`'s `_resolve_level_number` at `:551-552` |
| the eager `_frm()`/`_tsp()` is a second logger-internal defect dominating the suppressed floor | verified at `logger.py:620`, `:130-131` |
| the byte-gate makes `_display_training_progress` the **wrong first site** | verified; see §0.0.5(b) |
| the cheapest correct fix here is hoisting `_log_verbose` beside the existing hoists at `candidate_unit.py:595-596` | the PRO brief named this as its own biggest weakness |
| the P1.4 ruling's absence from the record limits how much interpretive weight it can bear | §0.0.2 correction 3 |

**Where they part, and who is right.** The PRO brief's framing correction (§0.0.5(a)) stands: §11's
P7 hazard does **not** bind, because the closure never escapes. But the CON brief found a **different
foreclosure the PRO brief missed, and it is real**: `log_if_enabled` takes **no `*args`** — verified,
`logging_utils.py:215`, and `_emit` passes a single rendered string — so a site converted to it
**cannot carry `%`-args**. §13.1 decision 6 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` holds **P6.4 open**, and P6.4's
target population is exactly the `{name}` f-string sites at `:731`/`:742`. **Wiring Option D there
pre-empts an open owner decision — just not the one §11 names.**

**The altitude arithmetic**, which neither brief disputes: the wiring decision governs **3 call
sites**; the `isEnabledFor` memo governs **17 guard sites plus every guard P6.2/P6.3 will add**; the
eager frame/timestamp governs **~874**. Roughly **1 : 6 : 290** — and the two larger ones are
single-file fixes that are not started.

**Synthesis.** Almost all of Option D's measured ~1,200–1,400 ns **is** the un-memoised guard. Fix
`logger.py:1098` and every row of §0.0.4's ladder moves, so a ruling taken on today's numbers
over-attributes to *idiom choice* what belongs to a one-line logger defect — memory
`reference_instrument_answers_an_adjacent_question`. **Do the logger fix first, then re-measure, then
rule.**

---

## 0. Remaining work

### 0.1 P1.4 second half — wire `log_if_enabled`, or rule that it is not wired (BLOCKING Phase 1)

State: the **fix** half is complete, tested and checkpointed on branch
`wip/logging-p14-adopt-logging-utils` in `juniper-cascor` (§6). No PR is open. The **wire** half
is not started, and §2 argues it needs an owner ruling first.

> ## ✅ CLOSED 2026-09-22 — P1.4 is discharged and Phase 1 is complete
>
> **The owner ruled**: convert the three sites to the **hoisted-guard + `%`-args** idiom, **not**
> wire `log_if_enabled`. Shipped as
> [cascor#670](https://github.com/pcalnon/juniper-cascor/pull/670), on top of
> [cascor#667](https://github.com/pcalnon/juniper-cascor/pull/667) (the guard memo fix).
>
> - `src/profiling/logging_utils.py` stays **fixed-but-unwired, dead code** — that is the ruling's
>   substance. The fix half remains on `wip/logging-p14-adopt-logging-utils`, still unmerged.
> - **P7's queued writer stays open** (there was never a foreclosure — §0.0.5(a)), and **P6.4 stays
>   open**, which is the foreclosure the ruling avoided (§0.0.6).
> - Recorded as **decisions 10 and 11** in §13.1 of
>   `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
> - `%`-args output equivalence verified, not assumed —
>   `util/ad-hoc/2026-09-22_p14_percent_args_output_equivalence.py`. `residual_error.shape` is a
>   `torch.Size`, a **tuple subclass**, so §5's splat hazard was live at `:742`.
>
> **What remains of this arc is §0.3 (P6.4, owner-gated) and §0.4 (P0.1/P0.2, the corpus that gates
> P2 and P3).** Everything below is the working record that produced the ruling.

> **REVISED 2026-09-21 — read §0.0.4–§0.0.6 first.** Step 2 is **DONE**, and its result plus a
> five-agent consensus review changed what steps 1, 3 and 4 should be. The original steps are kept
> below the revision for the record.

**Revised steps, in order:**

1. ~~Ship the `isEnabledFor` memo fix first~~ — **DONE 2026-09-21,
   [cascor#667](https://github.com/pcalnon/juniper-cascor/pull/667)**. Measured **1,270 → 341 ns,
   3.73×**, with all **132 cells** of the (configured level × probe level) behaviour table identical
   across an unfixed and a fixed checkout driven in separate subprocesses
   (`util/ad-hoc/2026-09-21_p14_isenabledfor_memo_verify.py`). Three regression tests added to
   `src/tests/unit/test_logger_level_state_reconciliation.py`, pinning the **mechanism** rather than
   a wall-clock time; the mutation check fails exactly those two mechanism tests and **nothing else
   across four logger suites**. **Re-measure §0.0.4's ladder against this before ruling on P1.4** —
   almost all of Option D's ~1,200–1,400 ns was this defect.

   <details><summary>original step 1 text</summary>

   **Ship the `isEnabledFor` memo fix first — it belongs to no option and unblocks a clean ruling.**
   `logger.py:1098` re-derives the configured level on every guard call while `_filter_by_level`
   (`:551-552`) uses the memoised `_resolve_level_number` (`:526-543`). Route the guard through the
   same helper, preserving the `NOTSET` fallback. Both Lane B briefs independently named this the
   highest-value change available. **It moves every row of §0.0.4's ladder**, so ruling on today's
   numbers would attribute to idiom choice what belongs to this defect. Needs its own PR and its own
   mutation check; do not fold it into P1.4.

   </details>

2. ~~Measure before wiring.~~ **DONE 2026-09-21** — `util/ad-hoc/2026-09-21_p14_guard_idiom_bench.py`,
   independently re-created as `util/ad-hoc/2026-09-21_p14_independent_remeasure.py`. Results and
   reconciliation in §0.0.4. The prior recorded there ("(c) loses to (b) on speed, wins on
   correctness") was **right in direction and wrong in magnitude**: the gap is ~25×, not marginal,
   and the cause is the guard, not the closure.
3. **Re-measure after step 1, then put the reframed question to the owner.** Not "Option D yes/no"
   — §0.0.5(a) shows that framing is wrong — but: *given that `log_if_enabled` cannot carry `%`-args
   and therefore pre-empts the still-open P6.4, and given the byte-gate cost at the only located
   target, is P1.4 discharged by wiring a non-lazy helper somewhere coarse, or should the module be
   deleted?* Both branches are the roadmap's own text (`…ROADMAP.md:229`, "Adopt … **or delete**").
4. **Do not wire at `_display_training_progress`.** §0.0.5(b): the import breaks the published
   `juniper-cascor-model`, and §0.0.5(c): that site is P6.2's reserved work, scheduled after P2.
   Converting it to the hoisted-guard + `%`-args idiom its own caller already uses
   (`candidate_unit.py:595-596`, `:598`, `:604`, `:629`) is the right change **in the wrong phase**.
5. Lint with the **pinned** tools (§5.3), open the PR, **and ask before merging** — §4's merge
   approval was given to the 2026-09-11 session and does not carry forward (see §13.1 decision 9 of
   `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`).

<details>
<summary>Original steps as written 2026-09-17 (superseded; kept for the record)</summary>

1. Read §2 and decide whether to put the Option D question to the owner. Recommended: yes, as a
   short interactive question with the measurement in hand — the same shape the owner accepted for
   decisions 5 and 6.
2. Measure before wiring. Write `util/ad-hoc/2026-09-17_p14_guard_idiom_bench.py` comparing, at
   both a disabled and an enabled configured level, against the **real** cascor `Logger`:
   (a) today's unguarded `self.logger.verbose(f"…")`; (b) the hand-rolled hoisted guard
   `if _log_verbose:`; (c) `log_if_enabled(self.logger, Logger.VERBOSE, lambda: f"…")`.
   The interesting number is (c) − (b) at the **disabled** level, which is the per-call closure
   allocation §11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` warns
   about at ~872 suppressed sites. My prior is that (c) loses to (b) on speed and wins on
   correctness; do not ship the claim without the number.
3. The adoption target, already located: `CandidateUnit._display_training_progress`
   (`src/candidate_unit/candidate_unit.py:728`). It is the innermost per-epoch loop and holds
   **three unguarded log calls evaluated on every epoch of every candidate regardless of level** —
   `debug` at `:730` and `:731`, `verbose` at `:742`. (Two further `debug` calls at `:734`/`:735`
   sit inside a rare re-initialisation branch; the `info` at `:740` is already frequency-gated.)
   Its sibling `_tensor_brief` (`:702`) already carries the measured evidence that f-string
   interpolation of tensors in this loop cost ~33 % of candidate-worker self time.
4. Then: lint with the **pinned** tools (§5.3), open the PR from the existing branch, merge.
   Merge approval is granted for this arc (§4).

</details>

**On step 3's "~33 % of candidate-worker self time"**: that figure
(`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`) was measured at an
**ENABLED** level on **emitted** records — 2,262 attributed calls from the `info` at `:740`, not the
suppressed `verbose` at `:742` — and it is a cumulative-over-self-time ratio. The same document says
*"No amount of call-site guarding, lazy `%`-args or lazy callables recovers it, because the record is
emitted."* **It is not evidence for guarding the suppressed sites**, and `_tensor_brief` already
shipped in cascor#598.

### 0.2 Close out P1.4's bookkeeping

- Commit the P1.4 probes to `juniper-ml` under `util/ad-hoc/` (the pattern followed after P1.1,
  P1.2 and P1.3 — the latter two landed as juniper-ml#1948). At handoff time **no P1.4 probe
  exists yet**; the benchmark in 0.1 step 2 will be the first. P1.5 needed none.
- ~~Record the **P7 Option D foreclosure** as a decision in §13.1~~ — **PARTLY DONE 2026-09-21, and
  the framing changed.** §13.1 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` now carries three new
  entries: **decision 8** (the P1.4 option-C ruling, transcribed with its thin provenance stated and
  flagged for owner confirmation), **decision 9** (the blanket merge approval, marked expired for new
  sessions), and **decision 10** (the disposition question, left **OPEN** with the measurement
  attached). Per §0.0.5(a) there is **no P7 foreclosure to record** — the closure never escapes. The
  live foreclosure is **P6.4's**, per §0.0.6.

**Status of the probe commits (2026-09-21):** three now exist in `juniper-ml` —
`util/ad-hoc/2026-09-21_p14_guard_idiom_bench.py`,
`util/ad-hoc/2026-09-21_p14_independent_remeasure.py` (independent Lane A re-creation) and
`util/ad-hoc/2026-09-21_p14_suppressed_site_census.bash` (re-derives 872/874).

### 0.3 P6.4 — still open, owner has seen the evidence and not ruled

Decision 6 in §13.1 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
authorised P6.1–P6.3 and held P6.4. The owner asked for and received sample affected lines
(2026-09-09, from `util/ad-hoc/2026-09-09_p64_fstring_classify.py` in `juniper-ml`) and has not
ruled on the 507 mechanical `{name}` conversions. **Do not start P6.4.** Re-ask when convenient.

### 0.4 P0.1 / P0.2 — the post-merge corpus, which gates P2 and P3

Unstarted, and on the critical path: decision 1 in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` pre-authorised a **10 %**
threshold — below it P2 is cancelled and recorded as cancelled. Nothing can measure that threshold
until the corpus is re-baselined after the four merged Phase 1 PRs. §3.1 of that file carries the
standing caveat that P0.2 must not promise the construction cost of discarded records.

### 0.5 ~~`JuniperCascor1` environment repair~~ — **MOOT, CLOSED 2026-09-21**

**Do not ask. There is nothing to rule.** The environment was repaired 2026-09-15: torch
**2.11.0+cu130** imports under `lib/python3.14/site-packages`, with or without
`env -u LD_LIBRARY_PATH -u LIBTORCH`, and the two P1.4 suites run **47 passed, exit 0** under
`/opt/miniforge3/envs/JuniperCascor1/bin/python`. §0.0.2 correction 1 carries the evidence; §5.1 is
obsolete.

---

## 1. Verify starting state

```bash
# juniper-cascor — main must be clean except .serena/project.yml (not ours; serena MCP writes it)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git status --short && git log --oneline -5
git log --oneline -1 origin/wip/logging-p14-adopt-logging-utils   # expect 1b918e6

# the four merged Phase 1 PRs
gh pr view 644 --json state,title; gh pr view 648 --json state,title
gh pr view 652 --json state,title; gh pr view 653 --json state,title

# the P1.4 work in progress, restored onto a worktree (do NOT edit main)
git worktree add \
  ../worktrees/juniper-cascor--wip--logging-p14--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD) \
  wip/logging-p14-adopt-logging-utils

# run the P1.4 suites -- as of 2026-09-21 the CONDA ENV WORKS, so prefer it (§0.0.2 correction 1)
JUNIPER_CASCOR_LOG_DIR=/tmp/claude-1000/p14logs \
  /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest \
  src/tests/unit/test_logging_utils_extended.py src/tests/unit/test_profiling_module.py \
  -p no:cacheprovider --timeout=120        # expect 47 passed -- verified 2026-09-21, exit 0
```

**Check the count, not just the exit code** — pytest exits 0 on zero collected tests, and a
vacuous pass here would look identical (memory `reference_vacuous_pass_check_class`).

The old `/tmp/claude-1000/cascorenv` route still works if you prefer it —
`env -u LD_LIBRARY_PATH -u LIBTORCH /tmp/claude-1000/cascorenv/bin/python` — but it is no longer
required, and `/tmp` is tmpfs so a reboot reaps it (memory
`reference_tmp_is_tmpfs_reboot_kills_the_isolated_stack`). It survived as of 2026-09-21 (13 days'
uptime).

A worktree for the branch already exists as of 2026-09-21, so `git worktree add` above will fail
with "already exists" — use it rather than making a second one:
`/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--wip--logging-p14--20260921-0340--1b918e61`

---

## 2. The P1.4 decision the next session must not skip

> **CORRECTED 2026-09-21 — this section's central claim is overstated.** "**That lambda is Option
> D**" does not survive checking: §4 of
> `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` defines Option D
> as extending **the logger** to accept a callable, whereas `log_if_enabled` invokes it in the
> caller's frame and hands `Logger` a plain `str` — which that same §4 explicitly calls safe. See
> §0.0.5(a). The three options below are still the right menu, but **option 2 is not viable as
> written** (`SampledLogger` takes an *eager* string and never checks the level — §0.0.6), and the
> foreclosure that is actually live is **P6.4's, not P7's**.

The owner ruled P1.4 as **C — Adopt: fix the levels and wire it to a real call site**. The obvious
wiring is:

```python
log_if_enabled(self.logger, Logger.VERBOSE, lambda: f"… Residual Error: Shape: {residual_error.shape} …")
```

**That lambda is Option D.** §11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
records the conflict precisely: lazy message callables and a deferred/queued P7 writer are mutually
unsafe, because a closure captures by reference and a message evaluated after the fact can render a
**different value** than it would have at the call site. Adopting one forecloses the other. It also
names two further constraints: a lambda that raises must not take down a training run, so it needs
its own swallow-path; and it allocates a closure per call **even when suppressed**, at ~872 live
suppressed Path-A sites.

Three ways out, and the choice is the owner's:

- **Wire it as written, and record P7's queued writer as foreclosed.** Honest, cheap, and it makes
  `src/profiling/logging_utils.py` live code. Costs a closure per suppressed call at the site.
- **Wire only the non-lazy helpers** (`SampledLogger`, `log_timing`) and leave `log_if_enabled`
  fixed-but-unwired. Satisfies "wire it to a real call site" without taking the Option D decision.
  This was my stated intention before the conflict surfaced, and it is the narrower reading.
- **Convert the three sites to the hoisted-guard idiom instead** and rule P1.4 as "fix, do not
  wire". This contradicts the letter of ruling C and should only be proposed with the benchmark.

My recommendation: take option 2 to the owner alongside the benchmark from §0.1 step 2, because it
is the only one that discharges the ruling without spending a decision that belongs to P7.

The countervailing argument, which is real: the hand-rolled guard states the level **twice** —
`_log_verbose = isEnabledFor(8)` next to `self.logger.verbose(...)` — and in this very file that
two-place statement was **wrong in two of three cases** before P1.3 fixed it (`8` is not a level at
all; `5` is VERBOSE's number, not TRACE's). `log_if_enabled` states the level once and cannot
drift. That is the strongest case for wiring it, and it is a correctness argument, not a
performance one.

---

## 3. What this session did

Four PRs merged to `juniper-cascor`, all of Phase 1 except P1.4:

| PR | step | what it fixed |
| --- | --- | --- |
| **#644** | P1.1 | `set_level()` was a **no-op for emission**. `isEnabledFor` read `_log_level`; `_log_at_level`'s filter read `_level_logger_config`/`_level_logger_name`, assigned once in the class body and never written again. One configured level, two readers. Also fixed `is_valid_level`'s `level == level` typo, which returned `True` for `None` and `"BANANA"` alike. New `src/tests/unit/test_logger_level_state_reconciliation.py`, 9 tests |
| **#648** | P1.2 | Three numeric level tables became one. `logger.py`'s duplicate is now **derived** (`_level_numbers = dict(_LOGGER_LOG_LEVEL_NUMBERS_DICT)` — a copy, not an alias); `src/profiling/logging_utils.py`'s contradicting `TRACE = 5, VERBOSE = 15` was **deleted**; eight symbolic constants `Logger.TRACE … Logger.FATAL` exported without colliding with the `_level_trace = "TRACE"` string attributes |
| **#652** | P1.3 | The 8 `isEnabledFor` guard sites in `src/candidate_unit/candidate_unit.py` stop naming integers. Output-neutral, proven by arithmetic over the real table. **Also added the eight constants to `juniper-cascor-model/log_config/logger/logger.py`** — see §5.2, this was a near-miss |
| **#653** | P1.5 | `src/tests/unit/test_logger_per_level_exercise.py`, 4 tests / 8 subtests, the first test that reaches the guard sites once per level. Includes an explicitly anti-vacuous `test_trace_actually_emits_at_trace` |

Plus **#647**, which is not a Phase 1 step but was found while writing them: **146 unit tests
across 15 files never ran in CI**. CI selects with `pytest -m "unit and not slow"` and those files
carried no marker, so they were silently deselected. (I got this count wrong twice by grepping —
grep counts *files*, and it missed `src/tests/unit/api/`'s 41 tests entirely. 146/15 is the
verified figure.)

And **#654**, the open-PR budget alarm ported from `juniper-ml` — unrelated to this arc.

**Changed** in `juniper-ml` this session: `util/ad-hoc/2026-09-11_p11_level_constants_probe.py`,
`util/ad-hoc/2026-09-11_p11_setlevel_blast_radius.py`,
`util/ad-hoc/2026-09-11_p11_verify_patched_logger.py`,
`util/ad-hoc/2026-09-11_p11_run_regression_test.py`,
`util/ad-hoc/2026-09-11_cascor_unit_marker_gap.py`,
`util/ad-hoc/2026-09-11_cascor_add_unit_markers.py`,
`util/ad-hoc/2026-09-12_p12_level_table_equivalence.py`, `util/ad-hoc/2026-09-12_p12_verify.py`,
`util/ad-hoc/2026-09-15_p13_guard_integer_audit.py`,
`util/ad-hoc/2026-09-15_p13_verify_both_trees.py` (all merged, latterly by juniper-ml#1948); and
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` §13.1, which now carries all
seven rulings, and `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`
§9.1–§11, which carries the A2-bind ruling, its measurement and the implementation design. This
handoff adds
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`.

---

## 4. Owner rulings taken this session

~~All are recorded canonically in §13.1 of~~
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`. Do not re-litigate them.

> **CORRECTED 2026-09-21.** Items 2 and 3 below were in §13.1 (as decisions 5 and 6). **Items 1 and
> 4 were not, anywhere** — and [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
> carries zero comments, so they had no primary source at all. Both are now transcribed as §13.1
> **decisions 8 and 9**, with their thin provenance stated and flagged for owner confirmation. See
> §0.0.2 correction 3. Item 1's merge approval is recorded as **expired for new sessions**.

1. **Merge approval granted for all PRs this session and this work arc.** I still showed each PR
   before merging; keep doing that.
2. **Decision 5 → A2-bind with a `_default` setter.** Nine public attributes become class
   attributes bound to a default `BoundLogger`; `Logger._default = X` is a **data descriptor on
   the metaclass** (a plain `property` on the class only intercepts *instance* assignment) that
   rebinds all nine. Measured faster than the status quo at every call site. The A2 **delegator**
   form was measured and rejected at **+146 ns** — my own estimate for it was +45 ns, i.e. 3×
   wrong, so measure rather than estimate here. Nothing lands until P1.1, which is now shipped.
3. **Decision 6 → P6.1–P6.3 authorised, P6.4 held** (§0.3).
4. **P1.4 → option C, adopt** — the ruling §2 is about.

---

## 5. Traps

### 5.1 ~~`JuniperCascor1` is broken~~ — **OBSOLETE as of 2026-09-21, the env is REPAIRED**

> **This trap no longer applies.** torch 2.11.0+cu130 now imports under
> `lib/python3.14/site-packages`, with **and** without the `env -u` workaround, and the P1.4 suites
> pass 47/47 under `/opt/miniforge3/envs/JuniperCascor1/bin/python`. The `/tmp/claude-1000/cascorenv`
> venv below still works and is what the §0.0.4 benchmark was run under, but it is optional now. The
> paragraph is kept for the record of what was true 2026-09-11 → 2026-09-15.

The env moved Python 3.13.13 → **3.14.7**; torch 2.11.0 exists only under
`lib/python3.13/site-packages` and the 3.13 binary is gone. Separately
`LD_LIBRARY_PATH=…/rust_mudgeon/juniper/libs/libtorch/lib` shadows torch's own libs, and that
`libtorch_python.so` needs `_PyObject_NextNotImplemented`, **removed in Python 3.14**.
`Juniper/CLAUDE.md` still documents the env as 3.13.13 and is wrong. Workaround in use all
session: a private venv `/tmp/claude-1000/cascorenv` with `torch==2.14.0+cpu`, run with
`env -u LD_LIBRARY_PATH -u LIBTORCH`. Rebuild it if `/tmp` was reaped. Related memories:
`project_juniper_cascor_torch_env_broken`, `project_canopy_libtorch_python_collision_2026-05-07`.

### 5.2 The byte-gate mirrors the CALLER; nothing mirrors the CALLEE

`_EXTRACTED_DIRS` covers `candidate_unit`, `utils`, `log_config`, `cascor_constants` — but
`log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE` and is **not** byte-compared, and
there is a *reverse* guard asserting the copies DIFFER. So P1.3's mirrored `candidate_unit.py`
would have shipped `Logger.DEBUG` against a package logger that does not define it —
`AttributeError` on **every candidate construction**, in a package that is live on PyPI, while
`src/` stayed perfectly green. `util/ad-hoc/2026-09-15_p13_verify_both_trees.py` in `juniper-ml`
demonstrates the hazard negatively and now reports it CLOSED. Decision 4 in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` is to **converge** the two
trees and retire `_INTENTIONAL_DIVERGENCE` — that work is not started. Memory:
`reference_cascor_model_verbatim_extraction_drift`.

### 5.3 Lint with the PINNED tools, not the local ones

Local `black` is 26.5.1; the repo pins **25.1.0**, and the two disagree about two files in this
change set — I nearly shipped the churn. A venv at `/tmp/claude-1000/lintenv` carries
`black==25.1.0` and `flake8==7.1.1` plus plugins. Also: run `isort` with `--settings-path <repo>`
— run from a staging directory it loses `known_first_party` and merges the `pytest` and
`log_config` import groups.

### 5.4 A staging tree without `__init__.py` measures the file you did not patch

Cost me two probe runs (P1.2 and P1.3). The package resolves to the real checkout and the probe
reports on the unpatched file while looking like it worked. Related: `sys.path.insert(0, p)` in a
**loop** puts the LAST path first — use `sys.path[:0] = paths`. Both fixes are in
`util/ad-hoc/2026-09-15_p13_verify_both_trees.py`, which documents them in comments.

### 5.5 A probe must not reconstruct the code under test

The first `util/ad-hoc/2026-09-11_p11_verify_patched_logger.py` computed the **patched**
expression itself, so the baseline showed zero splits and the defect looked absent. Drive the real
function and capture its output. Its own guard caught this; keep that guard. Memory:
`reference_instrument_answers_an_adjacent_question`.

### 5.6 A MagicMock logger is where this class of defect hides

All five `logger.log(level, msg)` sites in `src/profiling/logging_utils.py` raised
`TypeError: Logger.log() missing 1 required positional argument: 'msg'` against the real logger —
cascor binds the **class** (`self.logger = Logger`, `src/candidate_unit/candidate_unit.py:187`),
so `10` binds to `self`. 31 tests at full line coverage never saw it because they inject mocks.
The new `TestAgainstRealLoggers` drives real objects. **Mutation-check every new "it works with
the real thing" test**: my first draft of `test_log_if_enabled_works_with_the_cascor_logger_CLASS`
passed against the broken code because `isEnabledFor(INFO)` happened to be False. After
strengthening it, the mutation (reverting `_emit` to a bare `logger.log`) fails 4 of 4
cascor-Logger tests, and the stdlib-fallback test correctly passes — `logger.log(level, msg)` *is*
right for a stdlib logger. Memories: `reference_vacuous_pass_check_class`,
`reference_mutation_check_stale_pyc_and_piped_exit`.

### 5.7 `gh` is 2.46.0

`gh pr checks --json` **does not exist** and **all** `gh pr edit` flags are broken. Use
`util/wait_for_checks.py`; edit PR bodies through the API. I hand-rolled a Monitor loop against
`gh pr checks --json`, fed jq an error string, and spun **50 minutes** — this was trap 7 in the
predecessor handoff and I walked into it anyway. Memories: `reference_ci_wait_for_checks`,
`reference_gh_246_breaks_all_pr_edit`.

### 5.8 Signing and rate limits

Local commit signing **hangs** headless (YubiKey touch). Land commits via the GitHub API —
`util/open_signed_pr.py` for branch+commit+PR, `util/ad-hoc/push_signed_commit.py` for a follow-up
on an existing branch (both send **whole files**: sync first). The WIP checkpoint on
`wip/logging-p14-adopt-logging-utils` was made with `--no-gpg-sign` deliberately — it is a
*backup*, not a mergeable commit; re-land its content through `util/open_signed_pr.py`. Separately,
GitHub's **secondary** rate limit rejects mutations while `gh api rate_limit` still reports
5000/5000; it once left a branch created with no commit on it, recovered with
`util/ad-hoc/push_signed_commit.py`. Memories:
`reference_headless_commit_signing_hangs_use_api_commits`,
`reference_open_signed_pr_whole_file_clobber`.

### 5.9 Two smaller ones

- `git grep -E` does not support `(?:…)` and returns an empty file list rather than an error.
- `str.format()` on a template containing f-string braces raises `KeyError`. Use
  `str.replace("@@SRC@@", …)`, as the probes in `juniper-ml/util/ad-hoc/` do.

---

## 6. Git status

> **As of 2026-09-21** — `juniper-cascor` `main` is **one commit behind `origin/main`** (`c6c848f`,
> #658, landed after this was written); the working tree is still clean except
> `.serena/project.yml`. `wip/logging-p14-adopt-logging-utils` is unchanged at `1b918e6`, still
> unsigned, still with **no PR**. A worktree for it now exists at
> `Juniper/worktrees/juniper-cascor--wip--logging-p14--20260921-0340--1b918e61`. The `juniper-ml`
> work has moved from the `luminous-shimmying-crab` worktree to **`cached-greeting-mochi`**. The
> `/tmp/claude-1000/` scratch below **survived** (13 days' uptime) but is no longer needed — §0.0.2
> correction 1.

**juniper-cascor** — `/home/pcalnon/Development/python/Juniper/juniper-cascor`

- Branch `main` at `70d5ca1`, up to date with origin. Working tree clean **except**
  `.serena/project.yml`, which was already modified when this session started and is written by
  the serena MCP tooling — **not ours, leave it**.
- Branch `wip/logging-p14-adopt-logging-utils` at `1b918e6`, pushed to origin. One unsigned WIP
  commit carrying the three P1.4 files: `src/profiling/logging_utils.py`,
  `src/tests/unit/test_logging_utils_extended.py`, `src/tests/unit/test_profiling_module.py`.
  **No PR is open for it.** Its commit message carries the full done/not-done inventory.
- This session edited `main` directly as a staging area and then checkpointed onto the branch. Do
  not repeat that — use a worktree (`Juniper/CLAUDE.md` § Worktree Procedures), as §1 shows.

**juniper-ml** — worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/luminous-shimmying-crab`

- Branch `main` at `b9862984` (`chore(util): the four probes behind P1.2 and P1.3 (#1948)`).
  Working tree clean apart from this document, which is new and uncommitted.

**Scratch that will not survive a reboot**: `/tmp/claude-1000/p14/` (staging copies, including
`logging_utils.GOOD.py` and `logging_utils.MUTANT.py`), `/tmp/claude-1000/cascorenv`,
`/tmp/claude-1000/lintenv`. The branch in `juniper-cascor` is the durable copy of the only content
that matters.

---

## 7. Corrections this session made to its own work

Listed because each is a claim a successor might otherwise inherit:

- **"12 files / 156 tests"** for the marker gap was wrong twice. Truth: **146 tests / 15 files**.
  Grep counts files, not tests; it missed `src/tests/unit/api/` entirely; and it conflated 10
  deliberate `slow` exclusions. Corrected in the PR body, the source comment and memory.
- **"P1.2 removed the third contradicting table"** was half true when I first said it. The named
  constants went, but the wrong numbers survived **inline** at `src/profiling/logging_utils.py:90`
  (`5`) and `:94` (`15`) with two tests pinning them. Both are now fixed on the P1.4 branch.
- **The A2 delegator estimate was 3× low** (+45 ns estimated, +146 ns measured). Recorded in §13.1
  of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
