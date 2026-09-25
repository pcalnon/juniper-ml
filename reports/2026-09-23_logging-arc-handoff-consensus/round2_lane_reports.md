<!-- markdownlint-disable -->

# Logging arc — round-2 validator reports, 2026-09-23 (verbatim)

Archived by `util/ad-hoc/2026-09-23_archive_consensus_reports_logging.py` from the session's subagent
transcripts. Each section is the agent's final report exactly as delivered. They are EVIDENCE, not
conclusions: the reconciliation, including where a report was itself corrected, is §8 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`.

## Lane A (round 2) - re-derive the corrections (sonnet)

*agent `ac18b6aaebf3eae7c` · last-assistant-text · 15216 chars*

# Lane A (measurement), round 2 — Independent re-derivation report

Scratch artifacts: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/round2/laneA/` (`full_diff.txt`, `logger_e052ef8.py`, `test_logger_frame_resolution_0d2d826.py`, `p41_prototype.py`, `logging_utils_main.py`, `census_e052ef8.json`, `marker_inventory.json`, `repo_snapshot/` — a reconstructed tree of `f93c347f` used to run the census instrument with correct `REPO_ROOT` resolution).

## 1. Claim-by-claim table

| # | claim (doc + quote + line at f93c347f) | verdict | evidence |
|---|---|---|---|
| 1 | RECON §3: YAML `datefmt: "%Y-%m-%d %H:%M:%S"` at `conf/logging_config.yaml:48` (Path B, no ms) | **CONFIRMED** | `git -C cascor show e052ef8:conf/logging_config.yaml \| cat -n` → line 48 `datefmt: "%Y-%m-%d %H:%M:%S"` |
| 2 | RECON §3: Path C `RotatingFileHandler` sets no `datefmt`, `api/observability.py:118` | **CONFIRMED** | `git -C cascor show e052ef8:src/api/observability.py \| cat -n` → line 118 `file_handler.setFormatter(logging.Formatter("[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"))` — no `datefmt` arg at all |
| 3 | RECON §3: `formatter_console` has two-digit year `%y` | **CONFIRMED** | same file, line 45: `datefmt: "%y-%m-%d %H:%M:%S"` |
| 4 | RECON §3 supersession: "FORMAT strings are identical but the `datefmt` is not" | **CONFIRMED** | `conf/logging_config.yaml:47` and `api/observability.py:118` format strings are byte-identical (`"[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"`); datefmt present vs absent, per #1/#2 |
| 5 | N-4: three scripts anchor on `func:LINE]` — 8 anchors in `h2h_collect.py`, `h2h_marker_sentinel.bash`, `h2h_pair_compare.py` | **CONFIRMED (exact)** | Re-ran `util/ad-hoc/2026-09-22_p04_log_marker_census.py --rev e052ef8` from a reconstructed `f93c347f` tree: `ENVELOPE_FUNC_LINE=8`, all 8 from exactly those 3 files. Also cross-checked against cascor PR #680's shipped `src/tests/fixtures/log_envelope/marker_inventory.json` → `envelope_consumers.ENVELOPE_FUNC_LINE` lists the same 8 entries from the same 3 scripts |
| 6 | N-4/roadmap (c): "35 markers from 18 scripts, 10 GONE (8 DIAG + 2 `_reload_dataset:`)" | **CONFIRMED (exact)**, with caveat on file count | My re-run gives 37 "names a log" / 21 "carry anchors" / 117 anchors *before* excluding 3 scripts added later in the same PR for P0.4/#679 tooling (`2026-09-22_p04_harness_mutation_check.py`, `2026-09-22_p04_reference_capture_excerpt.py`, `2026-09-23_logconfig_custom_level_binding_repro.py` — none in the script's own `EXCLUDED_FILES`). Excluding those 3: **104 anchors, 18 files carrying anchors** (exact), **10 GONE MESSAGE anchors = exactly 8 `DIAG`-fragment + 2 `_reload_dataset:`-fragment** (exact), **35 unique LIVE fragment-sets** (exact — matches `marker_inventory.json`'s 35 entries exactly, `cascor_rev: e052ef80b4...`). Only the **"33 files" headline reproduces as 34**, not 33 — the one sub-figure I could not reconcile |
| 7 | RECON §3: fourth copy `conf/logging_config-CANOPY.yaml`, "no loader reads" | **CONFIRMED** | File exists at e052ef8 (`git -C cascor ls-tree`); repo-wide `git -C cascor grep -n "logging_config-CANOPY" e052ef8` finds it **only** in `notes/history/CODEBASE_ANALYSIS_2026-03-12.md` — no `.py` loader references it |
| 8 | RECON §3: `+` sentinel written by code, not a formatter string, `logger.py:581-582` | **CONFIRMED (exact)** | `src/log_config/logger/logger.py:581` = `print(f"+{_console_message(...)}")`, `:582` = `_line = f"+{_file_message(...)}\n"` |
| 9 | RECON §3: Path A file/console prefixes `constants_logging.py:152` / `:156` | **CONFIRMED (exact)** | Real path is `src/cascor_constants/constants_logging/constants_logging.py`; `:152` = `_LOGGER_LOG_FORMATTER_STRING_FILE_PREFIX` (has `funcName`), `:156` = `_LOGGER_LOG_FORMATTER_STRING_CONSOLE_PREFIX` (omits it) |
| 10 | Roadmap §0.1(d)/§8.1 row 1: citations wrong at `e052ef8` — real file `src/cascor_constants/constants_logging/constants_logging.py`, console prefix `:156` not `:157`, Path C `observability.py:118` | **CONFIRMED** | Same evidence as #2, #9 |
| 11 | Roadmap STATUS: cascor#680 = `test_log_record_envelope_contract.py` + fixtures/README under `src/tests/fixtures/log_envelope/` | **CONFIRMED (exact)** | `gh api repos/pcalnon/juniper-cascor/pulls/680/files` lists exactly that test file plus `README.md`, `envelope_golden.json`, `marker_inventory.json`, `reference_captures.json`, 4× `reference_*_sink.txt`, 2 helper files |
| 12 | Roadmap STATUS: inventory generated by `util/ad-hoc/2026-09-22_p04_log_marker_census.py`, resolved at `e052ef8` | **CONFIRMED** | `marker_inventory.json`: `"generated_by": "juniper-ml/util/ad-hoc/2026-09-22_p04_log_marker_census.py"`, `"cascor_rev": "e052ef80b4dc486d2aeec60671c39ea9ed60f26a"` |
| 13 | Roadmap §5 P2.1(c) CORRECTION: `test_logger_frame_resolution.py` "never drives an emit method" | **CONFIRMED** | `grep -nE "Logger\.(info\|debug\|...)\(\|logger\.(info\|debug\|...)\("` over the whole file at `0d2d826` → **zero matches** |
| 14 | same: the 4 `_frame_info` calls sit at `:79`, `:98`, `:112`, `:117` at cascor `0d2d826` | **CONFIRMED (exact)** | Direct read of `test_logger_frame_resolution.py` at `0d2d826`: line 79 `Logger._frame_info(frame=frame)`, line 98 `Logger._frame_info(frame=currentframe())`, line 112 `Logger._frame_info(frame=None)`, line 117 `Logger._frame_info(frame=currentframe())` — all 4 are direct calls |
| 15 | same: docstring says the test "models the real contract rather than calling `_frame_info` directly" (§7 defect 1's original over-correction) | **CONFIRMED the correction is right** | Lines 90-94's docstring makes that claim, but the code at line 98 is `Logger._frame_info(frame=currentframe())` — a direct call. The doc-string's own claim about itself is false; the correction ("original claim was right in substance") is right |
| 16 | Roadmap §5 P4 forward hazard / P4.1 ADDED: `BoundLogger.info()` calls `self._emit(...)`, `util/ad-hoc/2026-09-10_p41_a2bind_prototype.py:66-75` | **CONFIRMED (exact)** | Lines 66-69: `def info(...): ... return self._emit(INFO, message, args)`; lines 74-75: `def _emit(self, level, message, args): return message % args if args else message` |
| 17 | Roadmap §5 P2.2 CORRECTION: SIX closures, `logger.py:579,:580` (`_logging_message` ×2), `:332,:333` (`_console_dict`), `:350,:351` (`_file_dict`), all inside `if cls._filter_by_level(...)` | **CONFIRMED (exact, every line)** | `logger.py` at `e052ef8`: line 575 `if cls._filter_by_level(level=level, log_level=cls._log_level):`; 579-580 the two `_logging_message(...)` calls; 332-333 and 350-351 the closure-construction lines inside `_console_dict`/`_file_dict`, which are only invoked from 579-580 — i.e. structurally gated by the same `if` |
| 18 | same: `_get_log_level`/`_get_log_level_check` have no production caller | **CONFIRMED** | `git -C cascor grep -n "_get_log_level" e052ef8 -- src` → every hit besides the definitions (`:427`, `:435-436`) is in `src/tests/unit/test_log_config_coverage.py` or `test_logger_coverage.py` |
| 19 | same: note at `logger.py:162-171` | **CONFIRMED verbatim** | Lines 162-171 read exactly as quoted, including "removes `_get_log_level` / `_get_log_level_check` -- and is symbol loss, so it needs an enumerated `Allow-Symbol-Loss:` trailer" |
| 20 | same: `_log_at_level` now filters on `cls._log_level` directly (P1.1, cascor#644) | **CONFIRMED** | Line 575 reads `cls._log_level` directly; `gh api .../pulls/644` → merged, title "fix(logging): set_level was a no-op for emission — one configured level, two readers (P1.1)" |
| 21 | Roadmap §13.1 decision-6 UPDATE: cascor#675, 220 sites, two hot files | **CONFIRMED** | `gh api .../pulls/675` → `merged:true`, title literally "perf(logging): %-args at 220 mechanical sites in the two hot files (P6.4)" |
| 22 | same: "P6.1 remains authorised and undone: `src/cascade_correlation/backups/` is still tracked" | **CONFIRMED, and still true at `origin/main`** | `git -C cascor ls-tree -r --name-only origin/main \| grep cascade_correlation/backups` → 5 tracked files |
| 23 | Roadmap §13.1 logging_utils CORRECTION: "main still carried five `logger.log(level, msg)` sites" at the pinned state | **CONFIRMED at `e052ef8`** | `git -C cascor grep -n "logger\.log(" e052ef8 -- src/profiling/logging_utils.py` → exactly 5 raw call sites: `:82`, `:158`, `:161`, `:181`, `:199` |
| 24 | same: "SampledLogger.trace/.verbose passing 5/15" | **WRONG** | `cascor_constants/constants.py:542-543` → `_PROJECT_LOG_LEVEL_NUMBER_VERBOSE = 5`, `_PROJECT_LOG_LEVEL_NUMBER_TRACE = 1`; `logger.py:265-266` → `Logger.TRACE = _level_numbers["TRACE"]`, `Logger.VERBOSE = _level_numbers["VERBOSE"]`. `SampledLogger.trace()`/`.verbose()` pass `Logger.TRACE`/`Logger.VERBOSE` symbolically — i.e. **1 and 5**, not 5 and 15. `5`/`15` were the values of an already-**dead** local module table (`# TRACE = 5` / `# VERBOSE = 15`, deleted by an earlier fix, P1.2/#648, and present at `e052ef8` only as a comment explaining the deletion) — the correction appears to have conflated that dead table with what `SampledLogger` actually passes |
| 25 | same: "Re-landed unchanged (plus isort) as cascor#681" | **CONFIRMED (files), STALE (status)** | `gh api .../pulls/681/files` → exactly `logging_utils.py`, `test_logging_utils_extended.py`, `test_profiling_module.py`, `CHANGELOG.md`. But PR #681 is **now merged**: `merge_commit_sha: f6ee8de392c8350ea599659d262afa13403b30d6`, `merged_at: 2026-09-23T06:15:08Z`. `git -C cascor log --oneline -3 origin/main -- src/profiling/logging_utils.py` shows `f6ee8de ... (#681)` as the top commit, and `origin/main`'s current file already uses the fixed `_emit()` dispatch-by-name and has deleted the dead `TRACE=5`/`VERBOSE=15` block entirely |
| 26 | HANDOFF §8 banner / row 12 / §2 row 13: "not until cascor#681 merges — P1.4's fix half was never on `main`" ⇒ "Phase 1 is complete" is false | **STALE** | Same as #25 — the blocking condition (#681 unmerged) is resolved as of `merged_at: 2026-09-23T06:15:08Z`, i.e. some time on document-freeze day. This was true when the correction was written; it is no longer true against `origin/main` |
| 27 | HANDOFF §8: "found cascor#679... found while building P0.4" | **CONFIRMED** | `gh api repos/pcalnon/juniper-cascor/issues/679` → body matches the paragraph nearly verbatim: `LogConfig.__init__` binds custom-level closures via `__get__`, the logger becomes the message, VERBOSE/TRACE raises inside logging and the record is lost |
| 28 | cascor#680 head `f36d277a`, open/unmerged | **CONFIRMED** | `gh api .../pulls/680` → `head_sha: f36d277a5905f5dfdd3b0f76afb99b839b6b8bed`, `state: open`, `merged: false` |
| 29 | Pinned revisions `e052ef8`, `0d2d826` exist and resolve as described | **CONFIRMED** | `git -C cascor log --oneline -1 <sha>` for both resolved cleanly to the expected commits |

## 2. WRONG / STALE, ranked by consequence

1. **STALE — highest consequence.** Row 26 (HANDOFF §8 banner, §8.1 row 12/13, roadmap §13.1 correction): "logging_utils not fixed on `main`... Phase 1 not complete until cascor#681 merges." **cascor#681 merged at 2026-09-23T06:15:08Z** (merge commit `f6ee8de`), and the fix is now live on `origin/main`. This flips a **disposition**: whichever downstream action was gated on "Phase 1 incomplete pending #681" is now stale. This is a live document describing a moving target — worth an immediate follow-up correction, since it's the kind of thing a reader would act on (e.g., holding back other work "until #681 merges").
2. **WRONG — moderate consequence, numeric.** Row 24: "SampledLogger.trace/.verbose passing 5/15" should be **1/5** (`Logger.TRACE=1`, `Logger.VERBOSE=5`, confirmed three independent ways: `cascor_constants`, `logger.py`'s own class-attribute derivation, and `logging_utils.py`'s own docstring). This doesn't change the gate decision (the module was still broken at `e052ef8` regardless of which numbers), but it is a factual number in a document meant to be re-derivable, and it's wrong.
3. **WRONG — low consequence, headline count.** Row 6: "33 files [name a cascor log]" reproduces as **34** in a from-source re-run once the same 3 late-added P0.4/#679 tooling scripts are excluded (the sub-figures that matter operationally — 18 anchor-carrying files, 104 anchors, 35 live markers, 10 GONE split 8+2 — all reproduce **exactly**). Does not change any disposition; flagged because the instructions say not to soften a WRONG.

Everything else checked (24 of the 29 rows above) reproduced **exactly** against primary sources, including every `logger.py` line citation for P2.2's six closures and the `+`-sentinel code, both `test_logger_frame_resolution.py`'s four call sites, the P4 prototype's hop, the `func:LINE` 8-anchor/3-script claim, the Path B/Path C `datefmt` split, and cascor PR/issue numbers #644, #675, #679, #680, #681.

## 3. What I did NOT check

- **P0.2 profiling figures** (roadmap §13.1 decision-1 correction): 28.25%, 29.2% (Lane A3), 0.571 s `datetime.now`, 0.994 s `strftime`, ≈2.52 s `open`+`__exit__`, 0.119 s `print`, cProfile's claimed 3.17× inflation (1.31 s vs 4.16 s/553,471 calls), `Tensor.__format__` cumulative-vs-self (0.13 s / 0.011 s), and the 90.46% (58,399/611,870) discard rate. I did not run `util/ad-hoc/2026-09-23_p02_matcher_adequacy_check.py` — ran out of budget before reaching it.
- **P6.4 residue counts**: "51 hot-file sites refused (40 by hazard-5, 11 other), 236 outside hot files." Only confirmed cascor#675 is merged and its title states 220 sites; did not re-run the f-string classifier for the residue breakdown.
- **`util/ad-hoc/2026-09-22_p04_harness_mutation_check.py`**: did not execute it, so "14 mutations applied, all 14 fail, both controls pass" is unverified this round.
- **`util/ad-hoc/2026-09-22_p04_log_shape_survey.py`** and its cited numbers (77,796 Path A / 10,351 Path B / 24 Path C in the `.1` file; 1,218 Path B records in the P0.1 run) — not re-run; no access to the underlying log capture files was established.
- **`conftest.py`'s session-scoped `_cache_logging_system`** no-op claim, and the "golden probed against five breaks caught none" claim (Lane B1) — not independently re-probed; the roadmap text itself already flags the latter as "single-lane, not re-derived."
- **cascor#680's actual test file contents** — I confirmed the file exists in the PR's file list but did not open `test_log_record_envelope_contract.py` to confirm the specific test name `test_path_a_resolves_the_real_caller` or the 14-mutation/AST-caller-identity mechanics.
- **HANDOFF §8.1 rows 5, 9, 11, 14, 15, 16, 17, 18, 19, 20, 23** (the "breaks all four assertions" / 3-failure claim, `Tensor.__format__` cumulative-vs-self, discard-rate rounding, #667 timing reproduction, §3/§5 worktree-state claims, the verification-block syntax-error claim, decision-7 section-reference claim, ruled-but-unstarted list, dropped trap list, #573's staleness) — not independently checked this round.
- **§8.2 minimum-record claims** (iteration count, unresolved-dissent framing) — narrative, not independently checkable against a primary source.

---

## Lane B (round 2) - find what the fix pass broke (opus)

*agent `ae0bb1423f180f96f` · last-assistant-text · 15546 chars*

I found 20 defects in the fix pass, all verified against the PR bodies, the prototype, the corpus and #680's inventory. Four matter most:
- **The 28.25 % in the decision-1 correction comes from a measuring defect.** Lane A3's 29.2 % is the right figure.
- **The P4 forward-hazard text is wrong:** under the ruled design, cascor#680 would catch that failure.
- **cascor#680 is still open,** and no document says it must merge before P2.1.
- **Several corrected facts still stand in their old form** elsewhere in the same documents.

Documents, cited by filename at f93c347f:
- `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` (…ROADMAP.md)
- `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md` (…RECONCILIATION.md)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md` (HANDOFF_2026-09-22_…)
- `reports/2026-09-23_logging-arc-handoff-consensus/round1_lane_reports.md` (round1_lane_reports.md)

**Changed:** nothing in any repo. My probe scripts and outputs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/round2/laneB/`.

## Findings

**1. The 28.25 % is a weighting defect; Lane A3's 29.2 % is correct.** Severity: changes-a-number.
- **Where:** …ROADMAP.md:718, 723–725; HANDOFF_2026-09-22_… §8.1 row 8 (:422) and §8.2 "Unresolved dissent" (:453–454).
- **Defect:** `util/ad-hoc/2026-09-23_p02_matcher_adequacy_check.py` shares each builtin's time out by the call counts on its pstats caller edges. In some profiles those counts are broken.
- **Evidence (I re-ran the frozen script on the corpus):**
  - Output: `<built-in method _io.open> 1.6113 s … 1.3119 s` and `__exit__ 1.2647 s … 1.2080 s`, giving `10.4512 s = 28.25 %`.
  - My per-profile probe: `worker-1443178-df56f058.prof` has 2,558 own calls, a caller-edge count sum of **1**, and **0** logger-edge calls. Yet 0.0694 s of its 0.0704 s is on the logger edge.
  - Summed over the corpus: `38,106 calls (99.8 %) edge-tt 1.6071 s <- …logger.py:564(_log_at_level)`, and `__exit__` edge-tt 1.2628 s from the same caller.
  - A3 flagged this quirk itself (round1_lane_reports.md:572). A3's 29.21 % is its **STRICT** bound (round1_lane_reports.md:326), not a "looser" one.
- **Fix, at …ROADMAP.md:723–725:** "`open` + `__exit__` ≈ 2.87 s … Attributing each builtin by the self time on its `logger.py` caller edge, the share is **29.2 %** (≈10.80 s), matching Lane A3's STRICT bound. The adequacy script's call-count weighting reads 28.25 % because pstats' caller-edge call counts are degenerate in some profiles." Then close §8.2's dissent in A3's favour. The gate's decision does not change.

**2. "Neither detector would see it" is wrong under the ruled A2-bind design.** Severity: changes-an-action.
- **Where:** …ROADMAP.md:351–354 and :502–504; HANDOFF_2026-09-22_… :461–464.
- **Evidence:**
  - Decision 5 (…ROADMAP.md:768–771): "The nine public attributes … become class attributes bound to a default `BoundLogger`."
  - The prototype on main rebinds them: `type.__setattr__(cls, name, getattr(bound, name))` (:128).
  - cascor#680's emitter calls `Logger.trace(...)` through `Logger.fatal(...)` inside `emit_path_a`, and its test asserts `funcs == ["emit_path_a"]`.
  - So once P4.1 lands, the emitter's calls go through `BoundLogger.<m>` and then `_emit`. An extra hop would name the BoundLogger method and fail `test_path_a_resolves_the_real_caller`.
- **Why it matters:** the prescribed "extend the emitter" is aimed at the wrong thing. The real risk is P4.1 "fixing" #680's failing expectation, which is the same trap as P2.1(c).
- **Fix:** "cascor#680 WOULD see it — under A2-bind `Logger.<level>` is `_default`'s bound `BoundLogger` method. P4.1 must keep `test_path_a_resolves_the_real_caller` green without editing its expectations. Optionally add a `Logger.for_name(...)` case. `test_logger_frame_resolution.py` still cannot see it."

**3. The P4.1 obligation is wrongly tied to P2.1 shipping first.** Severity: changes-an-action.
- **Where:** …ROADMAP.md:498 ("once P2.1 has shipped").
- **Evidence:** P4.1 depends only on P1.1 (…ROADMAP.md:485), and row 19 calls P4.1–P4.3 "unblocked since P1.1 shipped". So P4.1 can ship before P2.1. The hazard exists whenever the frame is captured below the public method, for example if `_emit` evaluates `cls._frm()`.
- **Fix:** "P4.1 carries a frame-depth obligation whether or not P2.1 has shipped."

**4. The 35 markers come from 14 consumer scripts, not 18.** Severity: changes-a-number.
- **Where:** …ROADMAP.md:197; …RECONCILIATION.md:465; HANDOFF_2026-09-22_… row 21 (:435).
- **Evidence:**
  - `marker_inventory.json` at #680's head `7a2189fe` has 35 markers and **14** distinct consumer paths. Its `envelope_consumers` adds none.
  - The census's "18 carry anchors" counts every file with any anchor. That includes files whose anchors the census itself curates as OTHER or MESSAGE_EXTERNAL, such as `2026-08-10_ea_aggregate_clean.py` and `2026-08-26_census_post588_run.bash`.
- **Fix:** "35 live markers consumed by 14 scripts; 18 files carry some extracted anchor."

**5. "Phase 1 is not complete until cascor#681 merges" overstates what #681 settles.** Severity: changes-a-disposition.
- **Where:** HANDOFF_2026-09-22_… row 13 (:427).
- **Evidence:**
  - #681 merged at 2026-09-23T06:15:08Z, about two minutes after the freeze commit (06:12:53Z). The condition is now met.
  - B2 reported that nothing tests `_display_training_progress` per level: "still true after #670 … P1.5 … drives only `_multi_output_correlation` and `_get_correlations`" (round1_lane_reports.md:1132).
  - cascor#679 is open and describes itself as "the level system (roadmap Phase 1's territory)".
- **Fix:** say the P1.4 fix half landed with #681. State that the #670 sites' per-level gap and #679 keep "complete" open until the owner rules on them.

**6. P2's Acceptance line contradicts the measurement correction, and a reader meets it first.** Severity: changes-an-action.
- **Where:** …ROADMAP.md:372–373, "a re-measured delta against P0.1's corpus". The contradicting correction is at :729–730: "never as a delta against this corpus".
- **Evidence:** B1 flagged this exact line (round1_lane_reports.md:917). B2 added that the corpus predates #675 (round1_lane_reports.md:1179).
- **Fix:** "an unprofiled wall-clock A/B against the change's parent commit (§13.1 decision 1 CORRECTION); never a delta against P0.1's corpus."

**7. P0.3(a) still says Paths B and C need instrumentation to separate.** Severity: changes-an-action.
- **Where:** …ROADMAP.md:147: "B and C are byte-identical on disk (RECON §3), so a per-path split needs instrumentation".
- **Evidence:** …RECONCILIATION.md:178–179 now says "P0.3(a) can split B from C without instrumentation."
- **Fix:** "B (seconds) and C (`,mmm`) are separable by timestamp precision (RECON §3 CORRECTION)."

**8. The reconciliation's "nothing parses func:LINE" survives in three places, and one of them is a verdict.** Severity: changes-a-disposition.
- **Where:** …RECONCILIATION.md:270, :634 and :638–639, with no pointers to the correction.
- **Evidence:**
  - :270 is the §4 verdict on design §6-a: "PARTIALLY WRONG … **Wrong only about `[file.py: func:LINE]`** — nothing parses it". With three scripts anchoring on it, the design was right.
  - :634 lists "the absence of any `[file.py: func:LINE]` parser" as re-derived.
  - :638 records it as a tested universal quantifier.
  - Row 22 still says "Both corrected at source".
- **Fix:** change :270's verdict to **RIGHT** (corrected 2026-09-23) and mark :638 as "FALSIFIED 2026-09-23".

**9. The handoff's "next step" section is outside the banner's scope and was never corrected.** Severity: changes-an-action.
- **Where:** HANDOFF_2026-09-22_… :1 (the title), :47–58 ("P0.4 … is unstarted"; "So the next step is **P0.4, not P2.1**"), and the banner at :7 ("READ §8 BEFORE ACTING ON §0–§5").
- **Evidence:** B1's "Attack 1 … REFUTED" (round1_lane_reports.md:843) appears only in the lane table at :404. There is no §8.1 row for it, and §8 never states the actual next step.
- **Fix:** widen the banner to cover everything below it. Add row 24: the order survives only because #680 added caller identity beyond the spec. Next step: merge cascor#680, then P2.1.

**10. cascor#680 is open, but the documents treat its detector as available.** Severity: changes-an-action.
- **Where:** …ROADMAP.md:179 ("BUILT") and :207 ("Acceptance met"). The acceptance at :212–214 says "in cascor CI".
- **Evidence:** `gh pr view 680`: OPEN, mergedAt null, mergeStateStatus BLOCKED. When I read its check list, "Pre-commit (Python 3.12)" had no conclusion and there was no unit-test check at all. Nothing states that #680 must merge before P2.1. P2-G1 (…ROADMAP.md:387) implies it.
- **Fix:** relabel as "BUILT, NOT MERGED". Say acceptance was met locally, and in cascor CI only once #680 merges.

**11. Row 19 calls P6.2 and P6.3 unblocked; they are not.** Severity: changes-an-action.
- **Where:** HANDOFF_2026-09-22_… row 19 (:433).
- **Evidence:** P6.2 depends on P1 and P2 (…ROADMAP.md:589), and P6.3 depends on P6.2 (:590). Only P6.1 has no dependency (:588). Decision 6's own UPDATE names only P6.1 (:798).
- **Fix:** "…and P6.1; P6.2–P6.3 remain gated on P2."

**12. Residue: P6.4 shipped ahead of its gates, and nothing records it.** Severity: changes-a-disposition.
- **Where:** B2's "drops P6's gate on P0.4 and P2, even though #675 already shipped P6.4 ahead of that gate" (round1_lane_reports.md:1235) is absent from §8.1 and from the decision-6 UPDATE (…ROADMAP.md:792–799).
- **Evidence:** P6.4 depends on P6.2 (:591), and P6 gates on P0.4, P1 and P2 (:69).
- **Fix:** record the owner's hot-files ruling as the waiver.

**13. Residue: the decision-5 stubs correction was never applied to the roadmap.** Severity: changes-a-number.
- **Where:** …ROADMAP.md:771–773 still says "Measured faster than the status quo on every call site — 1,079 bound sites 55–77 ns …".
- **Evidence:** the handoff's own §6 (:318–321) says those figures describe stubs. B2 flagged the gap (round1_lane_reports.md:1216, :1229). No §8.1 row carries it.
- **Fix:** add a CORRECTION under decision 5 quoting §6.

**14. Residue: B1's gate critique and its effect-size numbers were dropped.** Severity: changes-an-action.
- **Where:** round1_lane_reports.md:915–919 and :1079. Row 8 and the decision-1 correction carry only the 3.17×.
- **Evidence (B1's words):**
  - "About 1.03 s of the 6.18 s is `_filter_by_level` … plus `_resolve_level_number` … P2 explicitly doesn't touch it."
  - "Report P2's addressable ceiling."
  - B1 already ran an unprofiled A/B: V0 2,371 → V1 1,162 ns per call, 0.669 s wall per corpus-equivalent, about 21 ms per candidate training.
- **Fix:** add these to the decision-1 correction.

**15. Residue: row 17 carries only part of B2's §1 findings.** Severity: changes-an-action.
- **Where:** row 17 (:431), and no corrected §1 block is supplied.
- **Evidence (B2's findings missing from the row):**
  - "'Expect EXIT 0' has no test-count check. Under the conftest stub it certifies nothing about emission."
  - An empty `$CASCOR` makes `git -C ""` run in the current directory.
  - The byte-gate check covers one file of the four gated trees.
  - The local `--timeout=900` versus CI's 60 s (round1_lane_reports.md:1166, 1185, 1188–1189).

**16. Stale copies left in the roadmap with no pointer to the correction.** Severity: mostly cosmetic; the P4.2 item changes an action.
- **P4.2 (:486) and P2.4 (:368–370)** still say P4.2 "subsumes the per-record `_get_log_level_check` lambda (`logger.py:394`, called at `:516`)". B1 flagged it (round1_lane_reports.md:957), and that helper is now dead. The P2.2 correction also assigns its deletion to P2.2, so the two sections now disagree on who owns it.
- **The P2.2 row (:314)** still says "most frequent of the seven" with old line numbers. The correction is 42 lines lower with no pointer.
- **The SWOT (:382)** still says "The test suite is the only detector".
- **The scope table (:34)** still says "seven".
- **`conftest.py:870-927` (:54, :149)** is stale. Lane A2 put the fixture at 891–892 and the patch at 948 (round1_lane_reports.md:204).
- **`logger.py:1026` (:493, :769)** should be `:1085` (round1_lane_reports.md:1133).
- **`:521-526` (:380)** should be `:579-580`.
- **Bare "§7.1" (:149, :700)** points at a section the roadmap does not have (row 18's defect, in this file).
- **Decision 8 (:822–824)** still has the fix half on the WIP branch and "§11's Option-D conflict is why".

**17. A reconciliation sentence right after its own correction still lumps Path B with Path C.** Severity: cosmetic.
- **Where:** …RECONCILIATION.md:477–478: "Path A and Path B/C emit different timestamp formats".
- **Fix:** "Path A and Path B emit seconds; Path C emits `,mmm`; 3 of 6 parsers cannot read Path C's form."

**18. Convergence is overstated for the one-hop-too-many variant.** Severity: cosmetic.
- **Where:** …ROADMAP.md:329–330 ("6/6 pass in both variants") and row 3's "B1, B2 convergent".
- **Evidence:** B2 probed only base, good and wrong-without-`.f_back` (round1_lane_reports.md:1248–1250), so the one-hop-too-many variant is B1's alone.
- **Also:** B1's V4 (a two-hop `_frame_info`) produced correct callers, so "would *weaken* it" leaves out that the suite rejects a correct implementation.

**19. The "at or above the level" rule is not universal.** Severity: cosmetic.
- **Where:** …ROADMAP.md:199–201.
- **Evidence:** `stop_requested` in `src/api/lifecycle/manager.py` has `required_level: null`, so it is checked for presence only.

**20. Leftover record-keeping gaps.** Severity: cosmetic.
- HANDOFF_2026-09-22_… §6 (:322) still reads "0.13 s over 2,912 calls" (cumulative time). It sits outside the banner's declared scope, and row 9 cites only §7.
- The #679 note (:439–442) leaves out its second defect: "the record never reaches the file sink".
- Both notes still read `Last Updated: 2026-09-02`.
- The roadmap's §14 still ends "Round 3 is not warranted" (…ROADMAP.md:942–943), with no record of the 2026-09-23 round.
- Further residue with no recorded rejection:
  - B1's point that the P0.5 stub's rationale is "obsolete since #563".
  - B2's dropped traps 5.4, 5.5 and 5.9.
  - B1's proposed juniper-ml-side test for consumer drift. `--check-inventory` is not wired into any CI.

## Not checked
- I did not re-run the census, so the 104 anchors, 33 files and "10 GONE (8 DIAG + 2 `_reload_dataset:`)" are unverified.
- I did not run #680's test or the mutation check, because the mutation check would modify a worktree.
- I did not re-derive the shape-survey counts (77,796 / 10,351 / 24 / 1,218). B2's 1,238 "lines" against 1,218 "records" is unreconciled.
- I did not verify the `fit:1918`/`fit:1936` dead-anchor claim, B1's 3.17×, or V4's 3 failures.
- The "~17 glob consumers" copies (…ROADMAP.md:116, 409, 456, 646; …RECONCILIATION.md:441) are leads only. The census found 33 files naming the log, 7 of them excluded.
- I did not review the handoff's §0–§5 line by line beyond the items above, since the banner declares that area superseded.
- I did not check reconciliation §6 N-2/N-9 or §7, the #670/#675/#644 diffs, or #573's comment.
- Checked and clean: the logger, hot-file and config paths are unchanged between cascor `0d2d826` and `e052ef8`, so both SHAs are safe to cite. The design doc's §7.1 is at `:363`, so row 18 is correct.

---
