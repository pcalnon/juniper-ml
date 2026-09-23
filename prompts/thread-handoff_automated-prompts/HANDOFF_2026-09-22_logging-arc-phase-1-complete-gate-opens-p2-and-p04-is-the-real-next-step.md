# HANDOFF 2026-09-22 — logging arc: Phase 1 complete, the gate opened P2, and P0.4 is the real next step

Successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`
(the **predecessor**; every bare "the predecessor" below means that file).

> ## ⚠ VALIDATION STATUS: INDEPENDENT CONSENSUS DID **NOT** RUN — VALIDATE THIS BEFORE TRUSTING IT
>
> Consensus was attempted per
> [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md):
> **Lane A ×3 on distinct entry points** (git/GitHub; the source tree; re-derivation of every
> number), to be followed by **Lane B ×2 opposing briefs**. **All three Lane A agents died on the
> account's weekly API rate limit** (resets 2026-09-23 22:00 America/Chicago) before returning a
> report. **Lane B never started.**
>
> What replaced it is **author self-verification**, which the procedure's §2 explicitly rates as
> not equivalent — *"an agent that produced a measurement is the worst possible reviewer of what it
> means."* Every claim I re-derived myself is marked ✅ in §7; everything else is **unverified**.
>
> **Self-checking did still find three defects in my own draft** (§7), so treat the unverified
> remainder as likely to contain more. **Run Lane A and Lane B against this document when the limit
> resets.** Memory: `feedback_validate_handoff_prompts_independently`.

**A bare "§N" means a section OF this document.** Every reference to another file names it. This
document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`.
All dates UTC.

**The arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573), still OPEN, and it
now carries a status comment (it had **zero** until 2026-09-22).
Roadmap of record: `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
Evidence base: `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`.
Design of record for P4: `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`.
Call-site options: `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`.

---

## The one thing to hold in mind

**P0.2's gate opened P2 — and P2 cannot start.** §13.1 decision 1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` pre-authorised a 10 %
threshold; the measured share is **16.70 %**, so P2 runs. But **both** of P2's real steps say
`depends on P0.4` in that file's §5 table, and **P0.4 — the envelope + marker harness — is
unstarted**. Verified: no envelope test exists in `juniper-cascor`, and no marker inventory exists
in `juniper-ml/util/`.

So the next step is **P0.4, not P2.1**. Taking P2.1 first means changing the emit path with no
harness able to detect that a record's shape changed — which is the exact failure class §3.1 of
that file built P0.4 to prevent.

---

## 0. Remaining work

### 0.1 P0.4 — the envelope + marker harness (BLOCKS P2.1 and P2.2)

§3.1 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` specifies it in full.
Five parts, and (c) and (d) are the ones with teeth:

- **(a) two reference captures, not one** — the file sink and the redirected-stdout sink differ: the
  console formatter omits the function name (`constants_logging.py:157`), and `print()` into a
  redirected fd is block-buffered while the file path opens and closes per record.
- **(b) an envelope checker**: `+` sentinel, bracket prefix, `(TIMESTAMP)` **including precision**,
  `[LEVEL]`, message.
- **(c) a named-marker inventory** — the half that matters most. RECON N-4 rates anchored **message
  text** BREAKING for ~17 `juniper-ml` scripts, and an envelope check **passes** a message-text
  change. Enumerate every marker string those scripts anchor on and assert each is still emitted.
- **(d) the enforcement mechanism.** A test sited in `juniper-ml` **cannot fail a cascor PR**.
  §3.1 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` recommends
  **option (i)**: a cascor-side test asserting the formatter strings in
  `constants_logging.py:152-158`, `conf/logging_config.yaml:47` and `api/observability.py:119`
  against a checked-in golden — it covers **all three copies of the prefix**.
- **(e) CI wiring in the same PR.** `juniper-ml`'s CI test list is hand-maintained;
  `tests/test_ci_test_wiring_drift.py` fails any `tests/test_*.py` not invoked by `ci.yml`.

**Acceptance**: the harness fails a deliberately-broken record in cascor CI. Mutation-check it.

### 0.2 P2.1 / P2.2 — only after P0.4

P2.1 moves `frame`/`tsp` inside `_log_at_level`. The corpus says why: eager `currentframe` is
**0.507 s over 611,870 calls**, paid on every call including the 91 % discarded, because
`logger.py:620` evaluates `cls._frm()` and `cls._tsp()` as **arguments** before the filter at `:575`.

> **P2.1(c) is a trap with one detector. Read the test before you touch `_frame_info`** — I
> mis-stated this and the source corrected me (§6).
>
> `_frame_info` reports **`f_back`: exactly one hop** from the frame it is handed.
> `src/tests/unit/test_logger_frame_resolution.py` pins that two independent ways:
>
> - `TestFrameResolutionEquivalence._probe` (`:79`) applies **both** `_legacy_frame_info` — a local
>   reimplementation of the old `getouterframes(frame)[1]` at `:53-55` — and `Logger._frame_info` to
>   the **same** frame, and `test_matches_legacy_at_several_depths` asserts equality at depths
>   **0, 1, 5, 12**.
> - `test_reports_the_caller_not_the_logger` (`:98`) wraps the call in a `stands_in_for_logger_info()`
>   helper so the caller relationship matches production.
>
> **The test's own docstring (`:90-96`) warns against the obvious "fix":** it models the real
> contract *"rather than calling `_frame_info` directly"*, because handing it the test method's own
> frame reports unittest's `_callTestMethod` — *"right behaviour and a wrong test"*.
>
> So: make `_frame_info` walk two hops and both classes fail. **Pass `cls._frm().f_back` from
> `_log_at_level` and leave `_frame_info` alone.** The SWOT in §5 of
> `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` names this suite as the
> step's **only** detector, because no consumer parses the `file:func:line` field — so "fixing" the
> test to accommodate the change leaves P2.1 with no detector at all.

P2.2 hoists **seven** closures, not the two that F-4a of
`notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md` names — and the two it names
are the two *cheapest*. §5 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
enumerates all seven. **P2.4 is deliberately absent**; it belongs to P4.2.

### 0.3 P6.4 residue

The hot files are done (220 sites, cascor#675). Re-derived at `origin/main` (`010d0359`)
2026-09-22 — the arithmetic closes against the pre-merge figures, which is the check that matters:

| | pre-#675 (`8065ca0f`) | post-#675 (`010d0359`) |
| --- | ---: | ---: |
| live Path-A f-string sites | 771 | **551** (−220 ✓) |
| of which MECHANICAL | 507 | **287** (−220 ✓) |
| hot-file mechanical | 271 | **51** |
| hot-file CONVERTIBLE | 220 | **0** |

Still unconverted:

- **51 mechanical sites remain in the two hot files** — **40** refused by the hazard-5 screen
  (§4.1), **11** for other reasons (6 implicit string concatenation, 3 carrying `!r`, 2 carrying an
  `if`/`and` expression). Convertible is **0**: every safely-convertible hot-file site is done.
- **236 mechanical sites outside** the two hot files (287 − 51). The owner authorised **hot files
  only** on 2026-09-22, so widening needs a fresh ruling.
- Re-derive with `util/ad-hoc/2026-09-22_p64_hot_file_convert.py --report` (hot files) and
  `util/ad-hoc/2026-09-09_p64_fstring_classify.py` (whole population); both read `origin/main` and
  print the revision.

### 0.4 Ruled but unstarted

- **Decision 4 — converge the mirror.** Re-extract `log_config/logger/logger.py` into
  `juniper-cascor-model` and retire `_INTENTIONAL_DIVERGENCE` (`test_drift.py:31`), deleting
  `test_intentional_divergences_actually_differ` (`:104-117`) in the same PR.
- **Decision 7 — the swallowed-pytest investigation** (§7.1 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`). Concurred, not started. P0.5 has a
  candidate mechanism: `conftest.py`'s session-scoped `_log_at_level` no-op.
- **P0.3** (volume census) and **P0.5**/**P0.6** — P0.6 is *decided* (decision 4) but its work is
  the bullet above. P0.7 is **partially** discharged by the cascor#573 comment; it still wants
  P0.2's and P0.3's numbers.

---

## 1. Verify starting state

```bash
CASCOR=/home/pcalnon/Development/python/Juniper/juniper-cascor

# cascor — main must contain 010d035 (P6.4) and c1de246 (#667)
git -C "$CASCOR" fetch origin
git -C "$CASCOR" log --oneline -3 origin/main

# the guard memo fix is live
git -C "$CASCOR" show origin/main:src/log_config/logger/logger.py | grep -n '_resolve_level_number(cls.get_level())'

# the byte-gate still holds after P6.4 (must print 1)
git -C "$CASCOR" show origin/main:src/candidate_unit/candidate_unit.py > /tmp/a.py
git -C "$CASCOR" show origin/main:juniper-cascor-model/candidate_unit/candidate_unit.py > /tmp/b.py
md5sum /tmp/a.py /tmp/b.py | awk '{print $1}' | sort -u | wc -l

# cascor unit suite — MUST unset the log-dir var (§4.2), else 6 unrelated tests fail.
# Run from a cascor WORKTREE, not the shared checkout: other sessions move it between branches.
( cd <a cascor worktree> && \
  env -u JUNIPER_CASCOR_LOG_DIR /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest \
      src/tests/unit -m "unit and not slow" -p no:cacheprovider --timeout=900 -q )   # expect EXIT 0

# re-run P0.2 over the archived corpus (expect 16.70 %) — from a juniper-ml checkout
( cd <a juniper-ml checkout> && \
  /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-09-22_p02_logging_share_decompose.py \
      ~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof )
```

**`JuniperCascor1` works** — torch 2.11.0+cu130 imports with **and** without `env -u LD_LIBRARY_PATH
-u LIBTORCH`. The predecessor's §5.1 (broken env, private `/tmp` venv) is **obsolete**; its §0.5
owner question is **moot**.

---

## 2. What this session did

**Merged**, all verified on `main` by content, not by merge status:

| PR | what |
| --- | --- |
| **cascor#667** | `isEnabledFor` resolves through the memo `_filter_by_level` already used. **1,270 → 341 ns, 3.73×**, 132/132 behaviour cells identical. 3 regression tests pin the **mechanism**, not a wall-clock |
| **cascor#670** | P1.4's wire half — hoisted guards + `%`-args at the three per-epoch sites in `_display_training_progress`, mirrored |
| **cascor#675** | P6.4 hot files — 220 mechanical `%`-args conversions (41 + 179), plus a `conftest.py` stub fix |
| **ml#1976** | predecessor validated: 5 corrections, the P1.4 measurement, roadmap §13.1 decisions 8–10 |
| **ml#1995** | P1.4 ruled; decisions 10–11 |
| **ml#2004** | P0.1/P0.2 — the corpus, the 16.70 % gate, `reports/p01-logging-corpus-2026-09-22/` |

**Phase 1 is complete.** P1.1 #644, P1.2 #648, P1.3 #652, P1.4 #670, P1.5 #653.

---

## 3. Owner rulings taken this session

Recorded in §13.1 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.

1. **P1.4 → hoisted guard + `%`-args**, *not* `log_if_enabled` (decision 10). So
   `src/profiling/logging_utils.py` stays **fixed-but-unwired dead code** — that is the ruling's
   substance, not an oversight. Its fix half is still on `wip/logging-p14-adopt-logging-utils`,
   unmerged, unsigned.
2. **P6.4 → hot files only** (2026-09-22). Widening needs a fresh ruling.
3. **P0.1 → launch**; decision 1's gate then resolved at 16.70 %.
4. **Merge approval granted** for this session. **Treat it as expired** — §13.1 decision 9 records
   that approval does not carry across sessions.

---

## 4. Traps

### 4.1 Hazard 5 — `%`-args change 0-dim tensor output, and the obvious check cannot see it

`f"{x}"` calls `format(x, "")`; `"%s" % x` calls `str(x)`. For a **0-dim torch tensor** they differ:
`f"{torch.tensor(1.5)}"` → `'1.5'`, `"%s" % torch.tensor(1.5)` → `'tensor(1.5000)'`. Multi-dim
tensors, `torch.Size`, dtypes and devices are identical — only the 0-dim scalar case, which is
exactly a correlation, a loss or an accuracy. **This is not among the four hazards in §5 of
`notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`.**

**A template-level render check passes it.** Mine reported 0/260 mismatches and was wrong about ~40,
because the divergence lives in the *value's type*, not the template. Screen on the field's
**trailing** identifier (so `residual_error.shape` keys on `shape`, not `error`). Memory:
`reference_percent_args_0dim_tensor_renders_differently`.

### 4.2 `JUNIPER_CASCOR_LOG_DIR` fails 6 tests that assert its unset fallback

`src/tests/unit/api/test_q6_log_dir_override.py` (4) and `test_service_launcher.py` (2). They arrive
in the same run as whatever you changed and read as your regression. Run with
`env -u JUNIPER_CASCOR_LOG_DIR`. Memory: `reference_cascor_log_dir_env_fails_six_tests`.

### 4.3 A cell is not a suite

`util/experiments/suites/` holds **suite** files. Putting a **cell** (`experiment.yaml` schema)
there fails `tests/test_experiment_suite_yamls.py` with *"unknown top-level suite keys"* — 1 failure
plus 3 errors in the contract tests that iterate the same set. It reddened ml#2004. Cells belong in
`util/ad-hoc/`.

### 4.4 The August cell cannot run, and P0.1 is a re-baseline

Two distinct refusals, both verified: juniper-data rejects `0.8 + 0.1 + 0.2 = 1.1` (the cell
predates the val split); and `val_ratio: 0.0` gets **past** juniper-data, which emits an **empty**
`X_val`, and cascor then refuses it at `cascade_correlation.py:1671`. **The CLI tolerates a
*missing* val, not an *empty* one.** Cell used: `0.8 / 0.1 / 0.1`, train held at August's value.
The generator version has moved, so `dataset_id` differs — this is a **re-baseline, not a repeat**.

### 4.5 A zero-profile corpus exits 0

Two of three P0.1 attempts produced **0 `.prof` files** and still exited 0. Only the explicit control
caught it. `util/ad-hoc/2026-09-22_p01_logging_corpus_run.bash` prints the count and refuses a cascor
tree not containing `8065ca0`. **Check the count, never the exit code.**

### 4.6 A stale checkout returns a plausible number

`util/ad-hoc/2026-09-09_p64_fstring_classify.py` read `HEAD` of the **shared** `juniper-cascor`
checkout, which sits on whatever branch another session left it on. A 2026-09-22 re-run reported
counts byte-identical to 2026-09-09 — which read as *confirmation*. It was not: cascor#670 was
invisible. It now defaults to `origin/main` and **prints the revision**. Memory:
`reference_stub_benchmark_became_a_real_system_claim` is the same shape at one remove.

### 4.7 Merge mechanics that cost time here

`safe_merge.py` **exits 0 without merging** — read the `MERGED` line. ml#2004 went BEHIND three
times in a contended lane; the documented escape is native auto-merge (`gh pr merge --auto`) **after**
`safe_merge` refuses. CodeQL review threads block a merge with every check green. And
`pre-commit run --files` works off the **index** — stage first, and re-stage after a hook rewrites a
file (P1-G2: re-sync a byte-gated mirror **after** the final lint, because Black covers `src/` only).

---

## 5. Git status

- **juniper-cascor** — `origin/main` at `010d035`. Branch
  `wip/logging-p14-adopt-logging-utils` at `1b918e6`, pushed, **no PR, unsigned**, and now
  **superseded**: decision 10 ruled its helper unwired. Decide whether to close it or keep it as the
  record of the P1.4 fix half.
- **juniper-ml** — `origin/main` at `a7568f78`; this session's work merged through ml#2004. Working
  worktree `.claude/worktrees/cached-greeting-mochi`, branch `worktree-cached-greeting-mochi`.
- **Five cascor worktrees created this session**, all now merged or spent — clean them up per
  `docs/REFERENCE.md` § Worktree Procedures:
  `…--fix--logging-isenabledfor-memo--20260921-0400--c6c848f2`,
  `…--fix--logging-p14-guard-display-progress--20260922-0530--0c14e92d`,
  `…--fix--logging-p64-hot-files--20260922-1815--05c13d55`,
  `…--measure--p14-plus-memo--20260921-0500--1b918e61` (dirty by design — carries an uncommitted
  one-line memo patch used for the post-fix ladder),
  `…--p01--logging-corpus--20260922-0630--8065ca0f`.
  **Never run `util/remove_stale_worktrees.bash`** — it has no staleness predicate (memory
  `project_worktree_branch_cleanup_playbook`).
- **The raw 32 `.prof` blobs are not in git.** They live at
  `~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof/`, which is not backed up.
  `reports/p01-logging-corpus-2026-09-22/prof_manifest.txt` is what survives.

---

## 6. Corrections this session made to earlier work

Listed because each is a claim a successor might otherwise inherit.

- **"That lambda is Option D" was overstated.** §4 of
  `notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` defines Option D
  as extending **the logger** to accept a callable. `log_if_enabled` invokes its lambda in the
  caller's frame and hands `Logger` a plain `str` — which that same §4 calls **safe**. **There was
  no P7 foreclosure.** The live one was **P6.4's**: `log_if_enabled` takes no `*args`.
- **§13.1 decision 5's "55–110 ns" describes stubs, not cascor.**
  `util/ad-hoc/2026-09-10_p41_a2_delegation_bench.py` times five hand-written stub classes and
  **never imports juniper-cascor**, and times `debug`, never `isEnabledFor`. **The A2-bind ruling
  stands** — all five share one body, so the deltas survive. The absolute framing does not.
- **The August 33 % `Tensor.__format__` headline is overtaken**: now **0.13 s over 2,912 calls**.
- **`~872` is 874** at `main`; re-derived at both revisions with
  `util/ad-hoc/2026-09-21_p14_suppressed_site_census.bash`.
- **The predecessor's "recorded canonically in §13.1"** was false for 2 of its 4 items; both are now
  transcribed as decisions 8 and 9 with their thin provenance stated.
- **I told the owner the hoisted-guard option had "zero mirror cost". That was wrong** —
  `candidate_unit.py` **is** byte-gated, so #670 mirrors it. What is true is that it needs no *new*
  package surface, since `Logger.DEBUG`/`VERBOSE` were added by P1.3.

---

## 7. Validation ledger — what was actually checked, and by whom

**Independent consensus did not run** (see the banner at the top). This is author self-verification.
It is recorded at this granularity so the next session knows exactly which claims still need a
second pair of eyes rather than having to re-check everything or trust all of it.

### ✅ Re-derived from primary artifacts by the author

| claim | how |
| --- | --- |
| 7 cascor PRs + 3 juniper-ml PRs all MERGED | `gh pr view <n> --json state` on each |
| `origin/main` = `010d035` (cascor), `a7568f78` (ml) | `git log origin/main` |
| the memo fix is live | `git show origin/main:…/logger.py \| grep '_resolve_level_number(cls.get_level())'` → 1 |
| **byte-gate holds after P6.4** | md5 of `git show` for both `candidate_unit.py` copies → identical |
| eager `_frm()`/`_tsp()` at `:620`, filter at `:575` | `git show`; all **eight** emit methods at `:612-668` |
| `cascade_correlation.py:1671` raises "cannot be an empty tensor" | `git show … \| sed -n '1671p'` |
| `logging_utils` is dead code | repo-wide search → only 2 test importers |
| P6.4 residue: 551 / 287 / 51 / 0, and **236** outside | classifier + converter at `origin/main`, cross-checked against the pre-#675 figures |
| `872` at `70edfc4`, `874` at `main` | `util/ad-hoc/2026-09-21_p14_suppressed_site_census.bash` at both revs |
| the `--measure--` worktree is dirty | `git status --short` |
| P0.4 is unstarted | searched both repos for an envelope checker / marker inventory → none |
| the §1 verification block runs as written | executed it |

### ❌ NOT verified — a successor should treat these as claims, not facts

- **16.70 %, 37.00 s, 6.18 s / 4,938,286 calls.** Re-derivable by re-running
  `util/ad-hoc/2026-09-22_p02_logging_share_decompose.py` over the archived corpus — **do that
  before quoting the gate.** The instrument's own matcher was never independently reviewed, and it
  is the number a whole phase decision rests on. Lane A3 was asked to judge whether its
  `LOGGING_FUNCS` substring matcher is over- or under-inclusive and **died before answering**.
- **1,270 → 341 ns, 3.73×, 132/132 cells** (#667). **Cannot be re-run from the worktrees named in
  §5** — both now carry the fix. To reproduce, make a worktree at a commit **before** `c1de246`
  (`wip/logging-p14-adopt-logging-utils` at `1b918e6` qualifies) and pass it as `--old` to
  `util/ad-hoc/2026-09-21_p14_isenabledfor_memo_verify.py`.
- **0.13 s / 2,912 calls** for `Tensor.__format__`, and the §0.2 per-function figures.
- **The §0.1 P0.4 file:line citations** (`constants_logging.py:152-158`, `conf/logging_config.yaml:47`,
  `api/observability.py:119`) — inherited from §3.1 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` and **not** re-checked.
  Line numbers in that file have drifted before (§13.1 decision 5's citations were ~55 lines stale).
- **RECON N-4's "~17 juniper-ml scripts"** anchoring on message text.

### Defects self-verification found in this document

Listed because they are evidence the unverified remainder is not clean:

1. **§0.2's P2.1(c) trap was wrong.** I wrote that
   `src/tests/unit/test_logger_frame_resolution.py` "calls `_frame_info` **directly** (`:71`, `:90`,
   `:104`, `:109`)". The line numbers are wrong, and the test's own docstring at `:90-96` says it
   models the contract *"rather than calling `_frame_info` directly"* — close to the opposite. I had
   inherited the framing without opening the file. Corrected in §0.2; the *prescription*
   (pass `cls._frm().f_back`) was right.
2. **§0.3 said "~247 mechanical sites outside the hot files". It is 236** (287 − 51), and the
   arithmetic now closes against the pre-#675 figures in the table there.
3. **Three ambiguous section references.** A bare `§N` means a section of *this* document, and
   `§5`, `§3.1` and `§7.1` were used for the roadmap's sections — where this document's `§5` is Git
   status. All three now name their file. One role-only reference ("the design") likewise.
