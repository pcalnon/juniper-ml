<!-- markdownlint-disable -->

# Logging arc — round-1 validator reports, 2026-09-23 (verbatim)

Archived by `util/ad-hoc/2026-09-23_archive_consensus_reports_logging.py` from the session's subagent
transcripts. Each section is the agent's final report exactly as delivered. They are EVIDENCE, not
conclusions: the reconciliation, including where a report was itself corrected, is §8 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`.

## Lane A1 - git / GitHub state (sonnet)

*agent `a5b9c3c0ad46d0e9f` · last-assistant-text · 9965 chars*

# Lane A Report — Git/GitHub State Validation

Document: juniper-ml `7b226ca0`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md`

## Per-claim verdicts

**1. §2 table — cascor#667/#670/#675, ml#1976/#1995/#2004, "Merged"**
Verdict: **CONFIRMED** (all 6).
Evidence: `gh pr view <n> --repo pcalnon/<repo> --json state,mergedAt,mergeCommit,title` → all `state: MERGED`. Content cross-check via `git -C juniper-cascor diff-tree --no-commit-id --stat -r <sha>` / `git diff-tree ... -r <sha>` (ml, from cwd):
- #667 `c1de246a`: touches `src/log_config/logger/logger.py` (+18/−1) + `test_logger_level_state_reconciliation.py` (+82) — matches "the guard resolves through the memo… 3 regression tests."
- #670 `8065ca0f`: `candidate_unit.py` changed **identically** in both `src/` and the `juniper-cascor-model/` mirror (33/33 lines) — matches "mirrored."
- #675 `010d0359`: `candidate_unit.py`(×2 mirrors)+`cascade_correlation.py`+`conftest.py`, "4 files changed, 285 insertions(+), 264 deletions(-)" — matches "220 (41+179) … plus a conftest.py stub fix."
- ml#1976 `739a233c`: roadmap.md + predecessor handoff (+399 lines) + 4 new benchmark scripts — matches "5 corrections, the P1.4 measurement."
- ml#1995 `100fee5f`: roadmap.md + predecessor handoff + `2026-09-22_p14_percent_args_output_equivalence.py` — matches "P1.4 ruled; decisions 10–11" (roadmap text at 7b226ca0 contains literal "decision 10"/"decision 11" callouts, e.g. line 737 "cascor#667 (decision 11)").
- ml#2004 `3a4482dd`: roadmap.md + `reports/p01-logging-corpus-2026-09-22/` (exactly **7** files) + util scripts — matches "the corpus… reports/p01-logging-corpus-2026-09-22/."

**2. Phase 1 "P1.1 #644, P1.2 #648, P1.3 #652, P1.4 #670, P1.5 #653"**
Verdict: **CONFIRMED**. `gh pr view` on 644/648/652/653 all `MERGED`, titles literally tagged `(P1.1)`…`(P1.5)` matching the labels (e.g. #644 "set_level was a no-op for emission… (P1.1)").

**3. §7 "7 cascor PRs + 3 juniper-ml PRs all MERGED" vs §2's 3-row table**
Verdict: **CONFIRMED, not a contradiction**. The document names exactly 7 distinct cascor PR numbers total (644, 648, 652, 653 in the Phase-1 recap + 667, 670, 675 in §2's table) and 3 ml PRs (1976, 1995, 2004). All 10 independently confirmed `MERGED`. §2's table simply covers "this session's" 3; the other 4 come from the Phase-1 sentence two lines below it.

**4. §1 "main must contain 010d035 (P6.4) and c1de246 (#667)"**
Verdict: **CONFIRMED**. `git -C juniper-cascor merge-base --is-ancestor 010d0359… origin/main` → exit 0. Same for `c1de246a…` → exit 0. Also reran §1's own snippet: `git show origin/main:src/log_config/logger/logger.py | grep '_resolve_level_number(cls.get_level())'` → hit at line 1114 ("the memo fix is live"). Independently verified origin/main = `0d2d826` via `git log --oneline -5 origin/main`, with `010d035` exactly 2 commits back (`0d2d826`→`f9818b0`#674→`010d035`#675) — matches the task's own note.

**5. §5 "Branch wip/logging-p14-adopt-logging-utils at 1b918e6, pushed, no PR, unsigned"**
Verdict: **CONFIRMED** (all 3 clauses). `git ls-remote --heads origin wip/logging-p14-adopt-logging-utils` → `1b918e61096b8e286712237b28ad66c3b151c6cf` (pushed, exact SHA). `gh pr list --repo pcalnon/juniper-cascor --head wip/logging-p14-adopt-logging-utils --state all` → empty (no PR, ever). `gh api repos/pcalnon/juniper-cascor/commits/1b918e6 --jq .commit.verification` → `{"reason":"unsigned","verified":false}`.

**6. §5 five named worktrees — existence, merged-branch status, dirty check**
Verdict: **PARTIAL** — worktree *existence* CONFIRMED (all 5 present, exact paths, via `git -C juniper-cascor worktree list`); PR-merged status CONFIRMED for the 3 with PRs (`gh pr list --head` → #667/#670/#675, all MERGED). But **"all now merged or spent" understates the dirty state**: `git -C <path> status --short` shows **4 of 5** worktrees dirty, not the 1 disclosed:
- `…measure--p14-plus-memo…` — dirty, **disclosed** ("dirty by design"), matches (1 file, `logger.py`).
- `…fix--logging-isenabledfor-memo…` (HEAD `c6c848f` = unrelated PR #658, never advanced) — **undisclosed dirty**: staged diff "2 files changed, 99 insertions(+), 1 deletion(-)" across `logger.py`+test file, **byte-identical diffstat** to merged PR #667.
- `…fix--logging-p14-guard-display-progress…` — **undisclosed dirty**: mixed staged/unstaged, 33-line change matching PR #670.
- `…fix--logging-p64-hot-files…` (HEAD = `05c13d55…`, which is `origin/main~3`, i.e. the pre-#675 base — its own branch never advanced past its base) — **undisclosed dirty**: `git diff HEAD --stat` → "4 files changed, 285 insertions(+), 264 deletions(-)", **byte-identical diffstat** to merge commit `010d0359` (#675).
- `…p01--logging-corpus…` — clean (confirmed, matches implicit "not dirty").

Corrected statement: *Four of the five worktrees, not one, carry uncommitted local changes. In three of those four the working-tree diff is content-identical to the PR that already merged from that branch — consistent with those commits having been made via the GitHub API rather than a local `git commit` (a known pattern in this ecosystem: local HEAD never advances past the branch's creation-time base). A plain `git worktree remove` (no `--force`) will refuse on 4/5 trees, not the 1 the document names.*

**7. §5 raw 32 `.prof` blobs vs `prof_manifest.txt`**
Verdict: **CONFIRMED, exact match**. `ls -la ~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof/` → exactly 32 `.prof` files. Built sorted (size, name) listings of both the live directory and `git show 7b226ca0:reports/p01-logging-corpus-2026-09-22/prof_manifest.txt`; `diff` → exit 0 (byte-identical file set and sizes).

**8. cascor#573 "still OPEN… now carries a status comment (zero until 2026-09-22)"**
Verdict: **CONFIRMED**. `gh issue view 573 --repo pcalnon/juniper-cascor --json state,comments` → `state: OPEN`, exactly 1 comment, `createdAt: 2026-09-22T08:03:26Z`. Comment text: *"This issue has carried no comments… this is a partial discharge — P0.7 also wants P0.2's and P0.3's numbers, which are not taken yet"* — matches handoff §0.4 verbatim in substance.
Noteworthy but not a falsification: the comment (08:03Z) predates ml#2004's P0.2 resolution (merged 23:32Z, same day) — so by the time the handoff itself was finished, P0.2's number (16.70%) was in hand but never posted back to the issue thread. The handoff's own text is accurate about what the *comment* says; it just leaves this small residual (one follow-up comment) undone.

**9. §3 item 1 "P1.4 fix half… still on wip/logging-p14-adopt-logging-utils, unmerged, unsigned"**
Verdict: **CONFIRMED**. `git -C juniper-cascor merge-base --is-ancestor 1b918e61… origin/main` → exit 1 (not an ancestor = unmerged). Combined with #5's pushed/no-PR/unsigned findings, all three clauses hold.

**10. Sweep for other past-tense claims (filed/opened/archived/created/pushed)**
Grepped the full document text: no "filed" claims exist. "opened" only refers to "gate opened P2" (not a GH action) and issue state (already checked). "archived corpus" (×2) refers to the `.prof` corpus, already confirmed to exist and match. "created" → "Five cascor worktrees created this session" — all 5 confirmed to exist. "pushed" → the WIP branch, confirmed. Predecessor file `HANDOFF_2026-09-17_...md` confirmed to exist at `7b226ca0` with a matching title. Sanity-checked the P0.4 "no envelope test / no marker inventory" self-verification claim by grepping both trees: cascor has `envelope` files, but they're all API/HTTP-exception envelopes (`test_api_09_*`, `juniper-cascor-protocol/.../envelope/`), not a log-record envelope checker; juniper-ml `util/` has `marker` files, but they're pytest-marker tooling, not a log-message-text anchor inventory. Neither contradicts "P0.4 unstarted" — both are same-word, different-concept false leads, which corroborates rather than falsifies the claim.

## Findings ranked by consequence

1. **(Medium)** §5's worktree-cleanup claim: **4 of 5** "merged or spent" worktrees are actually dirty (not the 1 disclosed), and in 3 of those 4 the local branch HEAD never advanced past its pre-PR base — the merged content exists only as an uncommitted working-tree diff that happens to be byte-identical to the already-merged PR. **Risk if acted on wrong**: a fresh session following "clean them up per docs/REFERENCE.md § Worktree Procedures" will hit unexpected `git worktree remove` refusals on 3 undisclosed trees. The realistic danger isn't data loss (the content duplicates what's already on `origin/main`) but that the standard remedy for a "worktree remove fails" refusal in this repo's own memory is `--force` or manual deletion — exactly the move the ecosystem's memory (`worktree remove deletes ignored files`, `diverging worktree: converge`) warns against doing reflexively. A session should `git status --short` each worktree itself before trusting the "clean them up" line.
2. **(Low)** cascor#573's only comment is now stale on one specific point (P0.2's number "not taken yet") because it was posted ~15.5 hours before ml#2004 resolved P0.2 in the same session. Not wrong, just leaves P0.7 one follow-up comment short of what the handoff's own numbers already support.
3. **(Informational only)** Two PR merge timestamps landed 50 seconds out of the narrative order implied by their bodies (ml#1995, merged 07:59:18Z, describes cascor#670 as already "Shipped," but cascor#670 merged at 08:00:08Z) — an automerge/CI-queue artifact, not a claim the handoff itself makes, and both are confirmed MERGED by the time the handoff was written.
4. All other checked claims — the 6-PR merge table, the Phase-1 PR/label mapping, the "7+3" count, both ancestor checks, the WIP-branch pushed/no-PR/unsigned triple, the 32-file `.prof`/manifest match, and issue #573's open+1-comment state — **CONFIRMED** with no discrepancies from primary sources.

---

## Lane A2 - the cascor source tree at 0d2d826 (sonnet)

*agent `a80a1e8451bfcaf38` · last-assistant-text · 19498 chars*

## Lane A2 Validation Report — Source-Tree Entry Point (juniper-cascor)

Scope: every file:line citation and code-behavior claim in the HANDOFF (`7b226ca0`), grounded against `juniper-cascor` at `0d2d826` (current `origin/main`) and, where relevant, `010d035` (the handoff's pinned SHA). `log_config/`, `cascor_constants/`, `conf/` are byte-identical between the two SHAs; `src/api/observability.py` gained 21 lines but the cited formatter/handler lines (102–119) are unchanged at both.

### 1–2. §0.1(a)/(d) — P0.4's file:line citations for the record-prefix formatter

**Verdict: WRONG (path), WRONG (line), PARTIAL (copy count), CONFIRMED (sentinel location)**

- `constants_logging.py:157` — **WRONG PATH**. `src/log_config/constants_logging.py` does not exist at either SHA (`fatal: path ... does not exist`). Real path: `src/cascor_constants/constants_logging/constants_logging.py` (mirrored byte-gated at `juniper-cascor-model/cascor_constants/constants_logging/constants_logging.py`). `git log --follow` on the real path shows no ancestor at the cited path either — this looks like a wrong path, not drift.
- Content at the real path, lines 152–158 (identical at both SHAs):
  ```
  152:_LOGGER_LOG_FORMATTER_STRING_FILE_PREFIX = f"[{_LOGGER_PREFIX_FILENAME}: {_LOGGER_PREFIX_FUNCTION_NAME}:{_LOGGER_PREFIX_LINE_NUMBER}] ({_LOGGER_PREFIX_ASCTIME}) "
  153:_LOGGER_LOG_FORMATTER_STRING_FILE_CONTENT = f"[{_LOGGER_CONTENT_LEVELNAME}] {_LOGGER_CONTENT_MESSAGE}"
  156:_LOGGER_LOG_FORMATTER_STRING_CONSOLE_PREFIX = f"[{_LOGGER_PREFIX_FILENAME}: {_LOGGER_PREFIX_LINE_NUMBER}] ({_LOGGER_PREFIX_ASCTIME}) "
  157:_LOGGER_LOG_FORMATTER_STRING_CONSOLE_CONTENT = f"[{_LOGGER_CONTENT_LEVELNAME}] {_LOGGER_CONTENT_MESSAGE}"
  ```
  The function-name omission is visible comparing line **152** (file prefix, has `_LOGGER_PREFIX_FUNCTION_NAME`) to line **156** (console prefix, lacks it) — **not line 157**, which is the CONTENT half (levelname+message) and is identical in shape for both file and console. The claim's pointer is one line off from the line that actually shows the omission.
- `conf/logging_config.yaml:47` — **CONFIRMED exactly**: `format: "[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"`.
- `src/api/observability.py:119` — **WRONG line, right file**. Line 118 (both SHAs) is the formatter: `file_handler.setFormatter(logging.Formatter("[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"))`. Line 119 is `root.addHandler(file_handler)`.
- **Copy count: MORE than three.** Full-tree `git grep` for the bracket/asctime/levelname pattern across `src/`, `conf/`, `juniper-cascor-model/` found it in six files: `conf/logging_config.yaml` (44, 47), **`conf/logging_config-CANOPY.yaml`** (44, 47 — a **fourth, uncited copy**, not referenced by any loader I could find — `_PROJECT_LOG_CONFIG_FILE_NAME = "logging_config.yaml"` only), `constants_logging.py` in both `src/` and `juniper-cascor-model/` (comments only, at 149–150; the real constants are f-string-composed and don't literally contain `%(filename)s`), `log_config/logger/logger.py` in both trees (comment only, line 32), and `observability.py:118`. Even collapsing the byte-gated src/model mirror into one, that's **at least four** live copies, one of which (`logging_config-CANOPY.yaml`) the P0.4(d) option (i) proposal never mentions and a golden test scoped to the three cited files would not catch.
- **The `+` sentinel is added in CODE, not a formatter string**: `src/log_config/logger/logger.py:581-582` (identical both SHAs):
  ```
  581:            print(f"+{_console_message(frame, tsp, level, message)}")
  582:            _line = f"+{_file_message(frame, tsp, level, message)}\n"
  ```
  None of the three formatter-string constants contain `+`. An envelope checker that only diffs the formatter-string constants against a golden will never see the sentinel — it has to inspect captured stdout/file output, or the `_log_at_level` source around 581–582.

### 3. §0.2 — eager `_frm()`/`_tsp()` before the filter

**Verdict: CONFIRMED, exactly**

`git show 0d2d826:src/log_config/logger/logger.py`:
```
575:        if cls._filter_by_level(level=level, log_level=cls._log_level):
```
`cls._frm = currentframe` (`inspect.currentframe`, logger.py:130) and `cls._tsp = datetime.datetime.now` (:131). All eight emit methods call `_log_at_level` with `frame=cls._frm(), tsp=cls._tsp()` **as call-site arguments**, evaluated before `_log_at_level`'s body (hence before :575) runs:
```
612,620,628,636,644,652,660,668:  cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level=cls._level_..., message=message, args=args or None)
```
Exactly the eight lines the claim cites (`:612-668`), and `:620` (the `verbose` method) is exactly one of them. Identical at `010d035`.

### 4. §0.2 — `_frame_info` one-hop contract and the P2.1(c) prescription

**Verdict: CONFIRMED — citations exact, reasoning sound**

`src/tests/unit/test_logger_frame_resolution.py` (0d2d826), all line numbers verified exact: `_legacy_frame_info` at **53-55**; `_probe`'s comparison line at **79** (`return _read(_legacy_frame_info(frame)), _read(Logger._frame_info(frame=frame))`); `test_matches_legacy_at_several_depths` loops `for depth in (0, 1, 5, 12)` (**82**); `test_reports_the_caller_not_the_logger`'s wrapped call at **98** (`return Logger._frame_info(frame=currentframe())` inside `stands_in_for_logger_info`); docstring **90-96**, containing the exact quoted phrase "rather than calling `_frame_info` directly" (line 92) and "right behaviour and a wrong test" (line 96).

Traced the call stack concretely: `_frame_info` (logger.py:296-327) does `target = frame.f_back`. Today, `cls._frm()` executes textually inside each emit method (e.g. `info`), so `currentframe()` returns `info`'s frame; `_frame_info`'s one `.f_back` reaches the real application caller. If `cls._frm()` moves inside `_log_at_level` (P2.1) without compensation, `currentframe()` would instead return `_log_at_level`'s own frame — one level deeper — and `_frame_info`'s existing one-hop logic would land on `info`, not the real caller, breaking both test classes. Passing `cls._frm().f_back` from `_log_at_level` (taking the extra hop explicitly at the new call site, before handing the frame onward) reproduces exactly the frame shape `_frame_info` always received, so `_frame_info` needs no change and both tests keep passing unmodified. The prescription is correct.

### 5. P2.2 — "seven closures"

**Verdict: WRONG.** Six are real (with materially stale line numbers); the seventh does not exist as characterized.

Roadmap (§5) cites `_logging_message ×2 (logger.py:521,522)`, `_console_dict (:302,303)`, `_file_dict (:320,321)`, `_get_log_level's lambda (:391, built at :516)`. At 0d2d826 the six *real* per-emitted-record closures are:

```
579:            _console_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)
580:            _file_message = cls._logging_message(cls._formatter_string_file, cls._file_dict)
332:        _get_frame_info = cls._frame_info(frame=frame)      # inside _console_dict (def at 331)
333:        _time_info = cls._date(format=cls._date_format)     # inside _console_dict
350:        _get_frame_info = cls._frame_info(frame=frame)      # inside _file_dict (def at 349)
351:        _time_info = cls._date(format=cls._date_format)     # inside _file_dict
```
All six sit inside the `if cls._filter_by_level(...):` block (575-582) — i.e., all six are AFTER/inside the filter, matching "six closures per emitted record" exactly, but every cited line number is stale by 30-60 lines (511 is `_logging_message`'s own def, not 521/522).

The claimed 7th, "`_get_log_level`'s lambda... the last before the filter, so it is the most frequent of the seven," is **not a live closure in the guard or emit path at all**. `_get_log_level`/`_get_log_level_check` (logger.py:427,435-436, lambda at 432: `return lambda c: norm_lvl if c else config_lvl`) have **zero call sites** anywhere in `src/` or `juniper-cascor-model/` outside their own definitions and test files (`test_logger_coverage.py` ×2, both trees). `isEnabledFor` (logger.py:1085-1117, both current and pre-P1.4-fix at `c1de246^`) uses `cls._resolve_level_number(cls.get_level())` / `cls.getLevelNumber(cls.get_level())` — never `_get_log_level`. A source comment the roadmap itself should have caught, **logger.py:162-171**, states explicitly: *"Their deletion belongs with P2.2, which also removes `_get_log_level` / `_get_log_level_check` -- and is symbol loss, so it needs an enumerated `Allow-Symbol-Loss:` trailer."* — P2.2's own target list says this pair is slated for **removal**, not hoisting. This claim carries no "unverified" caveat in the handoff's §7 ledger (unlike the P0.4 citations) — it is stated as settled fact.

### 6. §4.1 — torch tensor 0-dim hazard

**Verdict: CONFIRMED, character-for-character**

Probe (`/tmp/claude-1000/.../scratchpad/laneA2/probe_tensor_format_v2.py`, full source below), run with `/opt/miniforge3/envs/JuniperCascor1/bin/python`:
```
0dim_float   same=False f='1.5'          pct='tensor(1.5000)'
0dim_int     same=False f='7'            pct='tensor(7)'
1dim         same=True  f='tensor([1., 2., 3.])' ...
2dim         same=True  ...
torch_size   same=True  f='torch.Size([2, 3])'   pct='torch.Size([2, 3])'
dtype        same=True  f='torch.float32'
device_cpu   same=True  f='cpu'
```
Reproduces the document's exact quoted values (`'1.5'` vs `'tensor(1.5000)'`) and confirms multi-dim/`torch.Size`/dtype/device are identical — **but only when %-args is exercised the way `logger.py:576` actually does it** (`message % args`, where `args` is always a tuple via `*args` collection). A naive `"%s" % value` (bare, unwrapped) raises `TypeError: not all arguments converted during string formatting` on `torch.Size`, since it's a tuple subclass and gets unpacked positionally — a probe artifact, not a defect in the document's claim, but a trap for anyone writing P0.4's hazard test naively.

Full probe source:
```python
"""Probe v2: faithful to logger.py's ACTUAL mechanism.
Logger._log_at_level does ``message = message % args`` where ``args`` is always a TUPLE
(collected via ``*args`` in trace/debug/info/etc.). Probe v1 (bare %) is not
representative and produced a misleading TypeError for torch.Size.
"""
import torch

cases = {
    "0dim_float": torch.tensor(1.5), "0dim_int": torch.tensor(7), "0dim_bool": torch.tensor(True),
    "1dim": torch.tensor([1.0, 2.0, 3.0]), "2dim": torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
    "torch_size": torch.Size([2, 3]), "dtype": torch.float32, "device_cpu": torch.device("cpu"),
    "python_float": 1.5, "python_int": 7,
}
print("--- single value: f'{x}' vs template %s %% (x,) [the real logger.py mechanism] ---")
for name, val in cases.items():
    f_style = f"{val}"
    pct_style = "%s" % (val,)
    print(f"{name:12s} same={str(f_style == pct_style):5s} f={f_style!r:40s} pct={pct_style!r}")
```

### 7. §4.4 — empty tensor error

**Verdict: CONFIRMED, exactly, both SHAs**
```
1671:            raise ValidationError(f"Parameter {param_name!r} cannot be an empty tensor")
```
Identical at `010d035` and `0d2d826`.

### 8. §0.4 — test_drift.py

**Verdict: CONFIRMED, exactly**
```
31:_INTENTIONAL_DIVERGENCE = frozenset({Path("log_config/logger/logger.py")})
104:    def test_intentional_divergences_actually_differ(self):
...
117:                )
```

### 9. conftest.py session-scoped `_log_at_level` stub

**Verdict: answered directly; roadmap's own citation for this (`:870-927`) is WRONG/stale**

Fixture: `@pytest.fixture(autouse=True, scope="session")` / `def _cache_logging_system():` at **891-892**; the actual patch is `Logger._log_at_level = _noop_log_at_level` at **948**; teardown restore at **952-955**. The roadmap's `:870-927` covers the tail of an unrelated fixture (`real_init_logging_system`'s docstring) plus all of `_warmup_torch` (876-888) plus only the first half of `_cache_logging_system` — it stops *before* line 937, missing the `_log_at_level` patch entirely.

**No marker or env-var opt-out exists for `_log_at_level` specifically.** Only `_init_logging_system` gets one: its original is saved to a **module-level global** (`_REAL_INIT_LOGGING_SYSTEM`, line 860) with a companion `real_init_logging_system` fixture (863-873) that hands it to tests on request. `_log_at_level`'s original is saved only to a **local closure variable** (`original_log_at_level`, line 942), never exposed; a test that wants real emission behavior must manually `@patch.object(Logger, "_log_at_level", ...)` itself (as the fixture's own docstring, lines 904-906, documents `test_logger_coverage.py` doing).

Same fixture also stubs: `CandidateUnit.__init__`/`__setstate__` → attach a hand-written `_NoOpLogger` instance (`_noop_logger = _NoOpLogger()`, conftest.py:829; `isEnabledFor` returns `level >= 30`). `test_logger_frame_resolution.py` is unaffected by any of this since it calls `Logger._frame_info`/`_console_dict`/`_file_dict` directly, never through `_log_at_level`.

### 10. `profiling/logging_utils.py` dead code

**Verdict: CONFIRMED, exactly.** Repo-wide `git grep` (`src/`, `juniper-cascor-model/`) found exactly two importers, both tests: `src/tests/unit/test_logging_utils_extended.py:23` and `src/tests/unit/test_profiling_module.py` (106,116,129,141,158,168,181,194,213,221,234,302,314,336). Zero production importers. `juniper-cascor-model/` has no `profiling/` directory at all.

### 11. §4.2 — the 6 JUNIPER_CASCOR_LOG_DIR-sensitive tests

**Verdict: CONFIRMED, exactly 6, mechanism traced**

`test_q6_log_dir_override.py` (4): `test_unset_falls_back_to_repo_logs` and `test_unset_keeps_checkout_relative_fallback`, each `@pytest.mark.parametrize("resolver,_name", _RESOLVERS)` over `[observability, service_launcher]` = 4 test IDs. Mechanism: both correctly `monkeypatch.delenv(_ENV, raising=False)`, but `_resolve_log_dir()`'s fallback does `from cascor_constants.constants import _PROJECT_LOG_DIR_DEFAULT` — a plain import that reuses the **already-cached** module. `constants.py:436`: `_PROJECT_LOG_DIR_OVERRIDE = os.environ.get("JUNIPER_CASCOR_LOG_DIR", "").strip()` is a **module-level statement**, frozen the first time anything imports `cascor_constants.constants` in the session (almost certainly before these tests run, at whatever ambient value the shell had). Per-test `monkeypatch.delenv` cannot retroactively change an already-executed module-level assignment.

`test_service_launcher.py` (2): `test_resolve_from_constants` (180-184) and `test_resolve_fallback_when_import_fails` (186-196) — **neither calls monkeypatch/os.environ at all**; if the ambient var is set, `_resolve_log_dir`'s override check short-circuits before either test's `sys.modules` mock is ever consulted.

Total: 4 + 2 = **6**, exactly as claimed, and by two genuinely different mechanisms (stale cached import vs. no env isolation at all).

### 12. P0.4 unstarted / no envelope test

**Verdict: CONFIRMED — no such test found anywhere**

Searched `src/tests/` and `juniper-cascor-model/tests/` for: `_LOGGER_LOG_FORMATTER_STRING`, `envelope`, `formatter_string`/`formatter_console`/`formatter_file`, the plus-sentinel pattern, `capsys`/`capfd`/`caplog` in the three logger test files, and any test opening `cls._logging_file`. Hits are either (a) unrelated HTTP-response "envelope" tests (`test_api_09_*`), or (b) generic getter/setter tests against **arbitrary mock strings** (`"%(message)s"`, `"test.log"`) in `test_logger_coverage.py`/`test_logger_extended.py`/`test_log_config_coverage.py` — none capture real stdout/file output or compare it to a golden envelope shape. Cascor's extensive "golden" regression system (`golden_support.py`, `test_golden_trajectory.py`, `test_golden_api_snapshots.py`) covers model trajectories and API JSON, never log formatting.

### 13. CI test selection

**Verdict: CONFIRMED — an unmarked test would run in NONE of the discovered lanes**

`.github/workflows/ci.yml:312-317` matches the citation embedded in `test_logger_frame_resolution.py:44` byte-for-byte:
```
312:          python -m pytest \
313:            -m "unit and not slow" \
314:            src/tests/unit \
315:            --verbose \
316:            --timeout=60 \
317:            --maxfail=5 \
```
Every other pytest invocation found (`scheduled-tests.yml`: `unit and slow`, `integration and slow`, `long`; `ci.yml`: `integration and not slow` ×2) also filters by marker; `main-verify.yml` doesn't invoke pytest directly. No workflow runs pytest without a marker expression, and cascor has **no** guard analogous to juniper-ml's `test_ci_test_wiring_drift.py` that would catch a new unmarked test file. A P0.4 test file without `pytestmark = pytest.mark.unit` would be silently collected-and-deselected in every lane, exactly as `test_logger_frame_resolution.py`'s own comment (lines 44-47) warns.

---

## Findings ranked by consequence for implementing P0.4, then P2.1

1. **[P0.4, highest]** The new harness file must carry `pytestmark = pytest.mark.unit` at module level. Nothing in cascor CI would catch its absence — every lane filters by marker, none run unmarked, and there is no wiring-drift guard. Skipping this makes the entire envelope+marker harness a silent no-op that still reports green.
2. **[P0.4, high]** The P0.4(d) "three copies, one golden test" plan is built on a broken path (`src/log_config/constants_logging.py` does not exist — real path `src/cascor_constants/constants_logging/constants_logging.py`), an off-by-one line (`observability.py:118`, not `:119`), a fourth uncounted copy (`conf/logging_config-CANOPY.yaml:44,47`), and a sentinel (`+`) that lives in `logger.py:581-582` code, not in any of the three cited formatter strings. A golden-string test built from the citations as written would fail to even resolve, then miss the sentinel and the fourth copy even if the path were fixed.
3. **[P2.1/P2.2, high]** P2.2's "seven closures" target list is wrong on its most distinctive claim: `_get_log_level`'s lambda is dead code (no call sites in the guard or emit path; a source comment at `logger.py:162-171` already marks it for deletion alongside P2.2, not hoisting). The real, verified target is six closures, all after the filter, at `logger.py:579,580,332,333,350,351` (0d2d826) — the roadmap's own line numbers for these are stale by 30-60 lines. Anyone implementing P2.2 from the roadmap's citations will look for a 7th hot-path closure that isn't there.
4. **[P2.1, medium-high, reassuring]** The P2.1(c) frame-hop fix prescription is correct and verified sound by concrete call-stack tracing; all `test_logger_frame_resolution.py` line citations in the handoff are exact. This part of the handoff can be trusted as written.
5. **[Context, medium]** The `_cache_logging_system` autouse fixture (conftest.py:891-955, patch at 948) has no opt-out for `_log_at_level` (unlike `_init_logging_system`, which has one). Anyone adding P0.4 tests that call `Logger.trace/info/...` directly (rather than `_frame_info`/`_console_dict` as the existing frame test does) must be aware this global session-scoped stub is active and will silently swallow their output unless they patch it back themselves.
6. **[Confirmatory, low risk]** Claims 3, 4, 6, 7, 8, 10, 11, 12, 13 all check out as stated (exact line numbers or exact behavior), giving reasonable confidence in the rest of the document's mechanical claims outside the two flagged clusters above.

---

## Lane A3 - re-running every instrument (sonnet)

*agent `a4502b6ce9a72ff4a` · last-assistant-text · 29459 chars*

## Lane A3 Report — Measurement Re-Creation (Independent Validator)

**Scope covered**: items 1–6 of the brief, all executed. Corpus confirmed at exactly 32 `.prof` files before use. All work in `/tmp/claude-1000/.../scratchpad/laneA3/`; no repo or worktree was modified (verified `git status --short` clean on both cascor worktrees touched). Frozen document read via `git show 7b226ca0:<path>` throughout.

---

### Item 1 — The gate: 16.70%, 37.00s, 6.18s/4,938,286 calls

**Command**: `git show 7b226ca0:util/ad-hoc/2026-09-22_p02_logging_share_decompose.py` → extracted (stdlib-only, no sibling imports, safe to run standalone) → run as `/opt/miniforge3/envs/JuniperCascor1/bin/python p02_logging_share_decompose.py ~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof`.
**Corpus**: 32 `.prof` files confirmed by `ls` before running (matches the claimed count exactly).
**Result**: `worker self time: 37.00 s` / `ATTRIBUTABLE logging self time: 6.18 s over 4,938,286 calls` / `share: 16.70 %` — **byte-for-byte identical** to my run, and to the archived `reports/p01-logging-corpus-2026-09-22/p02_logging_share_decomposition.txt` (diffed by eye, matches to 3 decimals: 36.9953s / 6.1767s / 16.6960%).
**Verdict: CONFIRMED** (exact reproduction, cross-checked two independent ways — the reviewed script, and my own from-scratch pstats aggregation).

---

### Item 2 — Instrument adequacy (the important one)

**Method**: independent pstats enumeration (`laneA3_enumerate.py`), caller attribution (`laneA3_callers.py`, `laneA3_single_check.py`), and a targeted over-inclusion sweep (`laneA3_overinclusion.py`), all against the same 32-file corpus, all bypassing the reviewed script entirely.

**Matched-function table** (all 23 labels `LOGGING_FUNCS` counts — full list, not top-30, since only 23 exist):

| self (s) | calls | function |
|---:|---:|---|
| 1.0243 | 611,871 | `logger.py:564(_log_at_level)` |
| 0.6916 | 611,870 | `logger.py:545(_filter_by_level)` |
| 0.5070 | 611,870 | `inspect.py:1660(currentframe)` |
| 0.5057 | 58,399 | `logger.py:330(_console_dict)` |
| 0.4795 | 116,798 | `logger.py:281(_frame_info)` |
| 0.4405 | 264,784 | `logger.py:606(trace)` |
| 0.4358 | 241,459 | `logger.py:622(debug)` |
| 0.4309 | 116,798 | `logger.py:511(<lambda>)` |
| 0.4265 | 58,399 | `logger.py:348(_file_dict)` |
| 0.3366 | 1,315,122 | `logger.py:525(_resolve_level_number)` |
| 0.2528 | 58,401 | `logger.py:630(info)` |
| 0.1620 | 291,995 | `logger.py:327(<lambda>)` |
| 0.1357 | 91,382 | `logger.py:1084(isEnabledFor)` |
| 0.0933 | 47,228 | `logger.py:614(verbose)` |
| 0.0806 | 116,798 | `logger.py:278(<lambda>)` |
| 0.0720 | 116,798 | `logger.py:503(_logging_message)` |
| 0.0524 | 91,382 | `logger.py:496(get_level)` |
| 0.0490 | 116,798 | `logger.py:276(_date)` |
| +5 more, each <0.001s | — | level-name/set_level helpers |

**Over-inclusion**: **NOT observed.** Explicit scan of all 751 distinct function labels for `logsumexp`, `log_softmax`, `logaddexp`, `catalog`, `dialog`, `logit`, `analog`, `epilog`, `syslog` → **zero hits**. Only one distinct file matches the `"logger.py:"` substring (cascor's own `log_config/logger/logger.py`); the `"log_config.py:"` entry in `LOGGING_FUNCS` never matches anything (dead, harmless — the real path is a directory `log_config/logger/logger.py`, not a file `log_config.py`). The matcher's *design* is fragile (bare substring, not anchored to a path component), but not realized as a defect on this corpus. Illustrative-only side finding: a naive matcher on the substring `"logging"` anywhere in the **full path** would sweep in ~6.94s of core CasCor training math (`_update_weights_and_bias`, `_calculate_correlation`, etc.) purely because this corpus's directory is named `p01-logging-corpus-...` — an artifact of where the corpus lives, not of the code, but a concrete demonstration of why unanchored substring matching is dangerous.

**Under-inclusion: CONFIRMED, material.** Two distinct causes, both verified by caller attribution (`git -C juniper-cascor show 8065ca0f:src/log_config/logger/logger.py`, confirms `_frm = currentframe`, `_tsp = datetime.datetime.now`, `_date` returns `lambda d: d.strftime(format)`, and `_log_at_level` is the sole call site for `print()`/`open()`/`.write()`):

| function | self time | calls | caller attribution | why missed |
|---|---:|---:|---|---|
| `datetime.now` (`_tsp`) | 0.5708s | 611,870 | 100% from logger.py's 4 emit methods | never in `LOGGING_FUNCS` at all — the exact sibling bug to eager `currentframe`, same eager-before-filter pattern, silently invisible |
| `datetime.date.strftime` (`_date`) | 0.9939s | 116,798 | 100% from `logger.py:278(<lambda>)` | `LOGGING_FUNCS`'s `"(strftime)"` pattern is **dead** — pstats labels this as `~:0(<method 'strftime' of 'datetime.date' objects>)`, not `file.py:N(strftime)`, so the substring never matches. The docstring's own "ATTRIBUTABLE" list names `strftime` — this is an implementation bug against the script's own stated intent |
| `_io.open` | 1.6113s | 58,463 | 99.8%+ from `_log_at_level` (0.2% contamination from stdlib `tokenize.py`) | never in `LOGGING_FUNCS` |
| `_io._IOBase.__exit__` | 1.2647s | 58,497 | ≥99.7% from `_log_at_level` | never in `LOGGING_FUNCS` |
| `_io._IOBase.__enter__` | 0.0481s | 58,497 | ≥99.7% from `_log_at_level` | never in `LOGGING_FUNCS` |
| `_io.TextIOWrapper.write` | 0.0232s | 58,399 | ≥99.9% from `_log_at_level` | never in `LOGGING_FUNCS` |
| `builtins.print` | 0.1187s | 58,399 | 100% from `_log_at_level` | never in `LOGGING_FUNCS` |

These are the file-sink open/write/close and console `print()` calls that `_log_at_level` makes on every **emitted** record (source confirmed at `logger.py:581-602`), plus the timestamp-capture sibling of the already-measured eager-frame bug. None of these are "discarded-record construction cost" (the caveat the document already states) — they are cost on the **emitted** path the instrument already partially measures, just not fully.

**Bounds** (`laneA3_final_bounds.py`, denominator fixed at 36.9953s for both):

| bound | logging self time | calls | share |
|---|---:|---:|---:|
| baseline (reviewed instrument) | 6.1767s | 4,938,286 | **16.70%** |
| STRICT (baseline + builtins ≥99.7% caller-attributable to logger.py) | 10.8075s | 5,959,209 | **29.21%** |
| LOOSE (+ tiny ambiguous format/traceback/stdlib-logging items) | 10.8564s | 5,975,066 | **29.35%** |

**Does "at or above 10%" survive both bounds? Yes — decisively, more so than the original number.** STRICT and LOOSE differ from each other by only 0.14 points because the omitted items are unambiguous (100%-caller-attributable), not boundary judgment calls — the real gap is baseline-vs-correct (~12.5 points), not strict-vs-loose. **This does not change the P2 decision** (16.70% already clears 10%), but the 16.70% figure understates the true attributable share by roughly 43% relative, beyond what its own "lower bound" caveat (which is framed around *unattributable discarded-record construction*) discloses.

**Denominator, confirmed precisely**: literally the sum of `tottime` over **every** function key in **every** profile — torch, numpy, stdlib, everything, not narrowed to cascor code. `torch.rand` alone is 5.73s (>15% of the denominator by itself, and larger than the entire attributable-logging figure).

---

### Item 3 — §0.2 / roadmap §13.1 decision 1 component figures

| claim | re-derived | verdict |
|---|---|---|
| eager `currentframe` 0.507s / 611,870 calls | 0.5070s / 611,870 — exact | **CONFIRMED** |
| `_log_at_level` 1.02s | 1.0243s | **CONFIRMED** |
| `_filter_by_level` 0.69s | 0.6916s | **CONFIRMED** |
| `Tensor.__format__` 0.13s / 2,912 calls | **self time is only 0.0114s**; **cumulative time is 0.1338s** — matches archived `reports/p01-logging-corpus-2026-09-22/format_caller_attribution.txt`, which explicitly labels it `"target cumulative time: 0.13 s over 2,912 calls"` | **CONFIRMED, but flag the unit**: this is a cumulative-time figure sitting in prose next to several self-time figures (`_log_at_level` 1.02s, `_filter_by_level` 0.69s) with no unit distinguishing them — a reader could wrongly compare them directly |
| "91% discarded" | precisely 90.4557% (58,399 emitted / 611,870 attempts) | **PARTIAL** — rounds conventionally to 90%, not 91%; immaterial to any decision but a real ~0.5pp overstatement |

---

### Item 4 — §0.3 P6.4 residue table

Both scripts are stdlib-only (safe standalone). **`2026-09-22_p64_hot_file_convert.py` hardcodes `REV = "origin/main"` at module scope with no CLI/env override** (unlike its sibling, which uses `P64_REV`/`P64_CASCOR` env vars) — I patched a **scratch copy only** (2-line diff, shown in the pasted source below) to add the same env-var convention, to test all three revisions without touching the tracked file.

Ran both scripts at `8065ca0f5b511121bfb0b4f14107b8dfe41ba82b`, `010d0359b4907d1df9d6ed50ee8e28f8050886c5`, and `origin/main` (resolved to `0d2d826b`, confirmed exactly two commits after 010d035: `010d035 → f9818b0 (#674) → 0d2d826 (#672)`).

| metric | pre (`8065ca0f`) | post (`010d035`) | post (`0d2d826`, current origin/main) |
|---|---:|---:|---:|
| whole-population live sites / MECHANICAL | 771 / 507 | 551 / 287 | 551 / 287 (identical) |
| hot-file total / MECHANICAL | 422 / 271 | 51 / 51 | 51 / 51 (identical) |
| hot-file CONVERTIBLE | 220 | 0 | 0 |

**All exact matches to the table.** Residue breakdown of the 51: counted directly from the `--report` reason list — 9 hazard-5 rows ×2 + 22 hazard-5 rows ×1 = **40**; 6 "implicit concatenation" + 3 `!r` fields + 2 `if`/`and` fields = **11**; 40+11=51 ✓. Outside-hot-files = 287−51 = **236** ✓. The document's own concern (§4.6, drift risk from origin/main moving) **did not in fact perturb these numbers** — verified, not assumed.
**Verdict: CONFIRMED**, exactly, at all three revisions, with the revision printed every time as required.

---

### Item 5 — Suppressed-site census

`util/ad-hoc/2026-09-21_p14_suppressed_site_census.bash` (bash, takes an optional `<rev>` arg, no modification needed) run at `70edfc4` and `main` (= `0d2d826b` in the shared cascor checkout, confirmed identical to `origin/main`):

- `70edfc4`: **872** ✓
- `main`: **874** ✓

**Verdict: CONFIRMED**, exactly.

---

### Item 6 (optional) — cascor#667 isEnabledFor memo

`util/ad-hoc/2026-09-21_p14_isenabledfor_memo_verify.py` (stdlib-only) run with `--old` = `juniper-cascor--wip--logging-p14--20260921-0340--1b918e61` (HEAD confirmed `1b918e61`, unmemoised) and `--new` = `juniper-cascor--p01--logging-corpus--20260922-0630--8065ca0f` (HEAD confirmed `8065ca0f`, memoised). Both worktrees confirmed `git status --short` clean after the run (untouched).

- Behavior: **132 cells compared (11×12), IDENTICAL in every cell** — matches "132/132" exactly.
- Timing: my run got **1,891.6 → 452.4 ns, 4.18×**, vs. the document's **1,270 → 341 ns, 3.73×**. Same order of magnitude and direction (~4× speedup, old in low-microsecond range, new in mid-hundreds-of-ns range); both sides of my measurement scaled up proportionally (~1.3–1.5×) versus the document's, consistent with ordinary system-load variance across different points in time, not a mechanism difference.
**Verdict: CONFIRMED** (behavior-cell count, exact) / **PARTIAL** (timing, directionally consistent, not numerically identical — expected per the brief).

---

## Findings ranked by consequence

1. **[Instrument accuracy, does not flip the gate]** The 16.70% gate figure is an exact, reproducible output of the reviewed script — but the script under-counts the *attributable* logging share by roughly 12.5 percentage points against a properly caller-attributed STRICT/LOOSE bound (~29.2–29.35%), due to one matcher bug (`"(strftime)"` never matches real pstats labels) and one scope gap (`datetime.now`, `print`, and per-record file open/write/close are never in `LOGGING_FUNCS` despite being ≥99.7–100% logger-exclusive by caller analysis). **The P2/gate decision is unaffected** — both 16.70% and ~29.3% clear the 10% threshold, and the corrected number makes the case for running P2 *stronger*, not weaker. But anyone using "16.70%" as a cost figure to prioritize *within* P2 is working from a number that is roughly 43% too low relative to a fair accounting.
2. **[Documentation precision, low stakes]** "0.13 s over 2,912 calls" for `Tensor.__format__` is correct but is a **cumulative**-time figure (confirmed against the archived `format_caller_attribution.txt`), presented in prose alongside several **self**-time figures with no unit distinguishing them. Self time for the same function set is only 0.0114s.
3. **[Cosmetic]** "91% discarded" is precisely 90.46%, conventionally rounds to 90%.
4. **[Clean bill]** §0.3's P6.4 residue table and §6/§7's suppressed-site census reproduce exactly at every cited revision, including at cascor's current `origin/main` (two commits past the document's `010d035`) — the drift this document itself worried about did not perturb any of these numbers this time.
5. **[Clean bill]** cascor#667's behavioral-equivalence claim (132/132) is exact; its timing claim is directionally confirmed only, as expected.

---

## Probe scripts (full source, as required)

**`laneA3_enumerate.py`**
```python
#!/usr/bin/env python3
"""
Lane A3 independent probe. No sibling imports (stdlib only: argparse, pstats, sys,
collections, pathlib) so it is safe to run standalone.

Loads every .prof in the corpus directly via pstats (bypassing the reviewed script
entirely) and prints:
  1. Aggregate totals (sanity cross-check against the reviewed script).
  2. EVERY distinct function label, with aggregate self time (tottime) and call
     count (ncalls), sorted by self time descending -- the full universe, not just
     what the reviewed matcher picked.
  3. Which of those the reviewed LOGGING_FUNCS matcher would count (flagged).
  4. Which look format/print/IO/frame/time related but are NOT counted (flagged).
"""
import pstats
import sys
from collections import Counter
from pathlib import Path

PROF_DIR = sys.argv[1] if len(sys.argv) > 1 else None
if not PROF_DIR:
    sys.exit("usage: laneA3_enumerate.py <PROF_DIR>")

# Exact copy of the reviewed matcher list, for cross-reference only.
LOGGING_FUNCS = [
    "logger.py:",
    "constants_logging.py:",
    "log_config.py:",
    "(strftime)",
    "(currentframe)",
]

profs = sorted(Path(PROF_DIR).glob("*.prof"))
if not profs:
    sys.exit(f"FATAL: no .prof under {PROF_DIR}")

total_self = 0.0
per_func_self = Counter()
per_func_calls = Counter()
per_func_primcalls = Counter()

for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, _callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        total_self += tt
        per_func_self[label] += tt
        per_func_calls[label] += nc
        per_func_primcalls[label] += cc

print(f"corpus: {len(profs)} profiles under {PROF_DIR}")
print(f"TOTAL self time (sum tottime over every function, every profile): {total_self:.4f} s")
print(f"TOTAL distinct function labels across corpus: {len(per_func_self)}")
print()


def matches(label, pats):
    return any(pat in label for pat in pats)


logging_self = sum(tt for lbl, tt in per_func_self.items() if matches(lbl, LOGGING_FUNCS))
logging_calls = sum(per_func_calls[lbl] for lbl in per_func_self if matches(lbl, LOGGING_FUNCS))
print(f"[cross-check] reviewed matcher LOGGING_FUNCS self time: {logging_self:.4f} s over {logging_calls:,} calls")
print(f"[cross-check] share: {100.0*logging_self/total_self:.4f} %")
print()

print("=== ALL functions matched by LOGGING_FUNCS (full list, no top-N cutoff) ===")
matched_rows = [(lbl, tt, per_func_calls[lbl]) for lbl, tt in per_func_self.items() if matches(lbl, LOGGING_FUNCS)]
for lbl, tt, nc in sorted(matched_rows, key=lambda r: -r[1]):
    print(f"  {tt:10.4f} s  {nc:>12,} calls  {lbl}")
print(f"  -- {len(matched_rows)} distinct matched labels --")
print()

print("=== TOP 60 functions overall by self time (whole corpus, unfiltered) ===")
all_rows = sorted(per_func_self.items(), key=lambda r: -r[1])[:60]
for lbl, tt in all_rows:
    flag = "MATCHED" if matches(lbl, LOGGING_FUNCS) else ""
    print(f"  {tt:10.4f} s  {per_func_calls[lbl]:>12,} calls  {flag:8s} {lbl}")
print()

print("=== candidate logging-adjacent functions NOT matched (substring scan) ===")
candidate_substrings = [
    "format", "__format__", "__str__", "__repr__", "print(", "write(", "TextIOWrapper",
    "_io.", "open(", "strftime", "strptime", "datetime", "currentframe", "getframe",
    "_getframe", "inspect.py", "logging", "log(", "warn", "getLogger", "Handler",
    "Formatter", "emit(", "flush(", "encode(", "StreamHandler", "FileHandler",
    "catalog", "dialog", "logsumexp", "log_softmax", "logaddexp", "(log)", ":log",
    "syslog", "analog", "epilogue", "logit",
]
seen = set()
for lbl, tt in per_func_self.items():
    low = lbl.lower()
    for sub in candidate_substrings:
        if sub.lower() in low and not matches(lbl, LOGGING_FUNCS):
            seen.add((lbl, tt, per_func_calls[lbl], sub))
for lbl, tt, nc, sub in sorted(seen, key=lambda r: -r[1]):
    print(f"  {tt:10.4f} s  {nc:>12,} calls  [hit:{sub:14s}]  {lbl}")
print(f"  -- {len(seen)} candidate rows found, NOT counted by LOGGING_FUNCS --")
print()

print("=== functions with '__format__' anywhere in label (any class) ===")
fmt_rows = [(lbl, tt, per_func_calls[lbl]) for lbl, tt in per_func_self.items() if "__format__" in lbl]
for lbl, tt, nc in sorted(fmt_rows, key=lambda r: -r[1]):
    print(f"  {tt:10.4f} s  {nc:>12,} calls  {lbl}")
print(f"  -- {len(fmt_rows)} distinct __format__ labels, sum self = "
      f"{sum(r[1] for r in fmt_rows):.4f} s over {sum(r[2] for r in fmt_rows):,} calls --")
print()

print("=== functions with 'tensor' (case-insens) anywhere in label ===")
tens_rows = [(lbl, tt, per_func_calls[lbl]) for lbl, tt in per_func_self.items() if "tensor" in lbl.lower()]
for lbl, tt, nc in sorted(tens_rows, key=lambda r: -r[1])[:40]:
    print(f"  {tt:10.4f} s  {nc:>12,} calls  {lbl}")
print(f"  -- {len(tens_rows)} distinct tensor-labeled functions total --")
```

**`laneA3_callers.py`**
```python
#!/usr/bin/env python3
"""
Lane A3 caller-attribution probe. Stdlib only (pstats, sys, pathlib, collections).
For each target function label substring, aggregate ALL its callers across the
32-profile corpus, so we can judge whether the function is exclusively invoked
by cascor's own logger (safe for a STRICT attribution bound) or shared with
unrelated code (must stay out of STRICT, arguable for LOOSE).
"""
import pstats
import sys
from collections import Counter
from pathlib import Path

PROF_DIR = sys.argv[1]
targets = [
    "(currentframe)",
    "<built-in method now>",
    "'strftime' of 'datetime.date'",
    "builtins.print",
    "_io.open>",
    "'__exit__' of '_io._IOBase'",
    "'__enter__' of '_io._IOBase'",
    "'write' of '_io.TextIOWrapper'",
    "getEffectiveLevel",
]

profs = sorted(Path(PROF_DIR).glob("*.prof"))
if not profs:
    sys.exit("no profiles")

caller_map = {t: Counter() for t in targets}
label_seen = {t: set() for t in targets}

for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        for t in targets:
            if t in label:
                label_seen[t].add(label)
                for ckey, cval in callers.items():
                    clabel = f"{ckey[0]}:{ckey[1]}({ckey[2]})"
                    ccalls = cval[1] if isinstance(cval, tuple) else cval
                    caller_map[t][clabel] += ccalls

for t in targets:
    print(f"=== callers of functions matching {t!r} ===")
    print(f"  resolved labels: {sorted(label_seen[t])}")
    total = sum(caller_map[t].values())
    for clabel, n in caller_map[t].most_common(10):
        pct = 100.0 * n / total if total else 0.0
        print(f"    {n:>12,} calls ({pct:5.1f}%)  <- {clabel}")
    print(f"    TOTAL calls attributed to callers: {total:,}")
    print()
```

**`laneA3_single_check.py`** (diagnostic dead-end kept for transparency — found a minor pstats `cc`/`nc` accounting quirk on the caller-edge tuple for a handful of profiles; confirmed via `cc` that it does not change the ≥99.7% attribution conclusion, so not chased further)
```python
#!/usr/bin/env python3
"""Diagnostic: for one .prof file, does the sum of caller nc match the function's own nc,
for the `_io.open` builtin? Stdlib only."""
import pstats
import sys
from pathlib import Path

PROF_DIR = sys.argv[1]
profs = sorted(Path(PROF_DIR).glob("*.prof"))

target = "_io.open>"
grand_self_nc = 0
grand_caller_nc = 0
for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        if target in label:
            grand_self_nc += nc
            csum = sum((cv[1] if isinstance(cv, tuple) else cv) for cv in callers.values())
            grand_caller_nc += csum
            if csum != nc:
                print(f"{p.name}: label={label} own_nc={nc} own_cc={cc} caller_sum_nc={csum} "
                      f"callers={ {f'{k[0]}:{k[1]}({k[2]})': v for k, v in callers.items()} }")

print(f"\nGRAND total own nc: {grand_self_nc}, GRAND total caller-sum nc: {grand_caller_nc}")
```

**`laneA3_format_check.py`**
```python
#!/usr/bin/env python3
"""Check self time (tt) AND cumulative time (ct) for every '__format__' labeled function,
to see whether the document's '0.13 s over 2,912 calls' is a cumulative-time figure rather
than self time. Stdlib only."""
import pstats
import sys
from collections import Counter
from pathlib import Path

PROF_DIR = sys.argv[1]
profs = sorted(Path(PROF_DIR).glob("*.prof"))

tt_sum = Counter()
ct_sum = Counter()
nc_sum = Counter()
cc_sum = Counter()
for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, _callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        if "__format__" in label:
            tt_sum[label] += tt
            ct_sum[label] += ct
            nc_sum[label] += nc
            cc_sum[label] += cc

print("label, self(tt), cumulative(ct), ncalls, primcalls")
grand_tt = grand_ct = grand_nc = 0
for lbl in tt_sum:
    print(f"  tt={tt_sum[lbl]:.4f}s ct={ct_sum[lbl]:.4f}s nc={nc_sum[lbl]:,} cc={cc_sum[lbl]:,}  {lbl}")
    grand_tt += tt_sum[lbl]
    grand_ct += ct_sum[lbl]
    grand_nc += nc_sum[lbl]
print(f"\nGRAND self(tt)={grand_tt:.4f}s  GRAND cumulative(ct)={grand_ct:.4f}s  GRAND calls={grand_nc:,}")
```

**`laneA3_overinclusion.py`**
```python
#!/usr/bin/env python3
"""Explicit over-inclusion scan across the FULL 751-label universe (not just top-60),
for the exact risk substrings named in the brief: logsumexp, log_softmax, catalog, dialog,
and any OTHER file matching 'logger.py:' / 'log_config.py:' besides cascor's own, and any
non-logging '(currentframe)' definition. Stdlib only."""
import pstats
import sys
from collections import Counter
from pathlib import Path

PROF_DIR = sys.argv[1]
profs = sorted(Path(PROF_DIR).glob("*.prof"))

LOGGING_FUNCS = ["logger.py:", "constants_logging.py:", "log_config.py:", "(strftime)", "(currentframe)"]

per_func_self = Counter()
per_func_calls = Counter()
for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        per_func_self[label] += tt
        per_func_calls[label] += nc

risk_subs = ["logsumexp", "log_softmax", "logaddexp", "catalog", "dialog", "logit", "analog",
             "epilog", "syslog", "logarithm", "np.log", "torch.log", "(log)", "loge"]
print("=== exact risk-substring scan (over-inclusion candidates named in the brief) ===")
hits = 0
for lbl in per_func_self:
    low = lbl.lower()
    for r in risk_subs:
        if r in low:
            print(f"  HIT [{r}] {lbl}  self={per_func_self[lbl]:.4f}s calls={per_func_calls[lbl]:,}")
            hits += 1
print(f"  total hits: {hits} (0 expected if this corpus has no such functions)")
print()

print("=== every distinct file matched by the 'logger.py:' substring pattern ===")
files = set()
for lbl in per_func_self:
    if "logger.py:" in lbl:
        files.add(lbl.split("(")[0])
print(f"  matched {len(files)} distinct file:line entries total (all lines counted separately)")
srcfiles = set()
for lbl in per_func_self:
    if "logger.py:" in lbl:
        prefix = lbl.rsplit(":", 1)[0]
        srcfiles.add(prefix)
for f in sorted(srcfiles):
    print(f"    {f}")
print()

print("=== every distinct file matched by 'log_config.py:' (note: real path is log_config/logger/logger.py) ===")
lc = [lbl for lbl in per_func_self if "log_config.py:" in lbl]
print(f"  {len(lc)} matches (0 expected -- cascor's package is a log_config/ DIRECTORY, not a log_config.py FILE)")
for lbl in lc:
    print(f"    {lbl}")
print()

print("=== every distinct '(currentframe)' definition site matched ===")
cf = set(lbl for lbl in per_func_self if "(currentframe)" in lbl)
for lbl in sorted(cf):
    print(f"    {lbl}  self={per_func_self[lbl]:.4f}s calls={per_func_calls[lbl]:,}")

print()
print("=== every distinct '(strftime)' PURE-PYTHON definition site matched (vs C-method form) ===")
sf = set(lbl for lbl in per_func_self if "(strftime)" in lbl)
print(f"  {len(sf)} matches (checking whether the pattern ever fires on real data)")
for lbl in sorted(sf):
    print(f"    {lbl}")
```

**`laneA3_final_bounds.py`**
```python
#!/usr/bin/env python3
"""Final precise arithmetic: the 91%-discarded claim, and STRICT/LOOSE attributable shares.
Stdlib only (pstats, collections, pathlib, sys)."""
import pstats
import sys
from collections import Counter
from pathlib import Path

PROF_DIR = sys.argv[1]
profs = sorted(Path(PROF_DIR).glob("*.prof"))

per_func_self = Counter()
per_func_calls = Counter()
for p in profs:
    st = pstats.Stats(str(p))
    for key, (cc, nc, tt, ct, _callers) in st.stats.items():
        label = f"{key[0]}:{key[1]}({key[2]})"
        per_func_self[label] += tt
        per_func_calls[label] += nc

total_self = sum(per_func_self.values())

def find(sub):
    for lbl in per_func_self:
        if sub in lbl:
            return per_func_self[lbl], per_func_calls[lbl], lbl
    return None

cf_self, cf_calls, _ = find("(currentframe)")
console_self, console_calls, _ = find("logger.py:330(_console_dict)")
attempts = cf_calls
emitted = console_calls
discarded_frac = 1 - emitted / attempts
print(f"attempts={attempts:,} emitted={emitted:,} discarded_frac={discarded_frac*100:.4f}%  "
      f"(rounds to {round(discarded_frac*100)}%)")
print()

LOGGING_FUNCS = ["logger.py:", "constants_logging.py:", "log_config.py:", "(strftime)", "(currentframe)"]
def matches(label, pats):
    return any(pat in label for pat in pats)
baseline = sum(tt for lbl, tt in per_func_self.items() if matches(lbl, LOGGING_FUNCS))
baseline_calls = sum(per_func_calls[lbl] for lbl in per_func_self if matches(lbl, LOGGING_FUNCS))
print(f"BASELINE (reviewed instrument)   : {baseline:.4f} s over {baseline_calls:,} calls  "
      f"share={100*baseline/total_self:.2f}%")

strict_extra_subs = [
    "<built-in method now>",
    "'strftime' of 'datetime.date'",
    "builtins.print",
    "_io.open>",
    "'__exit__' of '_io._IOBase'",
    "'__enter__' of '_io._IOBase'",
    "'write' of '_io.TextIOWrapper'",
]
strict_extra = 0.0
strict_calls = 0
for sub in strict_extra_subs:
    r = find(sub)
    if r:
        strict_extra += r[0]
        strict_calls += r[1]
        print(f"  + {sub:40s} {r[0]:.4f}s  {r[1]:,} calls")
strict_total = baseline + strict_extra
print(f"STRICT total                     : {strict_total:.4f} s over {baseline_calls+strict_calls:,} calls  "
      f"share={100*strict_total/total_self:.2f}%")
print()

loose_extra_subs = [
    "torch/_tensor.py:1144(__format__)",
    "<function Tensor.__format__",
    "'__format__' of 'float'",
    "getEffectiveLevel",
    "traceback.py:527(format_frame_summary)",
    "traceback.py:744(format)",
    "traceback.py:37(format_list)",
    "traceback.py:244(format_stack)",
]
loose_extra = 0.0
loose_calls = 0
for sub in loose_extra_subs:
    r = find(sub)
    if r:
        loose_extra += r[0]
        loose_calls += r[1]
        print(f"  + {sub:40s} {r[0]:.4f}s  {r[1]:,} calls")
loose_total = strict_total + loose_extra
print(f"LOOSE total                      : {loose_total:.4f} s over "
      f"{baseline_calls+strict_calls+loose_calls:,} calls  share={100*loose_total/total_self:.2f}%")
print()
print(f"total_self (denominator)         : {total_self:.4f} s")
print(f"gate threshold                   : 10 %")
print(f"baseline vs strict vs loose all >= 10%: "
      f"{100*baseline/total_self:.2f}% / {100*strict_total/total_self:.2f}% / {100*loose_total/total_self:.2f}%")
```

**Patch to the reviewed `2026-09-22_p64_hot_file_convert.py`** (scratch copy only, to add revision selection since the shipped version hardcodes it):
```diff
-CASCOR = "/home/pcalnon/Development/python/Juniper/juniper-cascor"
-REV = "origin/main"
+import os
+CASCOR = os.environ.get("P64_CASCOR", "/home/pcalnon/Development/python/Juniper/juniper-cascor")
+REV = os.environ.get("P64_REV", "origin/main")
```

Scratch artifacts (probes, patched copies, raw outputs) remain at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/laneA3/` for re-inspection.

---

## Lane B1 - refute the conclusions (opus)

*agent `a6559a9f754d8e7d4` · last-assistant-text · 22597 chars*

I have enough evidence for all five attacks. Final report follows.

# Lane B1 review: logging-arc handoff (juniper-ml `7b226ca0`), checked against cascor `0d2d826`

**Bottom line.** The handoff's central conclusion is that P0.4 comes before P2.1 because P0.4 protects P2.1. That doesn't hold up. P0.4 as specified cannot see P2.1's failure. The suite the handoff names as P2.1's "only detector" passes both wrong implementations and fails the one alternative whose output is correct. And P0.4's recommended enforcement (the (d)(i) golden) was unchanged under every deliberately broken record I built.

**Documents cited:**
- `HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md` (the handoff)
- `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` (the roadmap)
- `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md` (RECON)
- `JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md` (the P4 design)
- `reports/p01-logging-corpus-2026-09-22/README.md` and `p02_logging_share_decomposition.txt`

**Changed:** no repository files. Scratch only, under `…/scratchpad/laneB1/`.

## Attack 1 — "the next step is P0.4, not P2.1": REFUTED

**The argument.** P2.1's risk is not a change to a record's shape. It is wrong content in a field whose shape stays the same: `[file: func:line]` naming the wrong caller. Neither P0.4's envelope checker, its marker inventory, nor its formatter-string golden can see that.

**Probe** (`p21_variant_probe.py` + `emit_driver.py`, real un-stubbed emit path, 14 records per variant):

| variant of `logger.py` | `test_logger_frame_resolution.py` | callers in the records | P0.4(b) envelope | (d)(i) golden |
|---|---|---|---|---|
| V0 status quo | 6 pass | correct | pass | `034716e3ea95` |
| V1 prescribed `cls._frm().f_back` | 6 pass | correct, identical to V0 | pass | same |
| V2 forgot `.f_back` | **6 pass** | **every record is `logger.py:<method>:<line>`** | **pass** | same |
| V3 one hop too many | **6 pass** | every record names the caller's caller | **pass** | same |
| V4 `_frame_info` walks two hops, passed `cls._frm()` | **3 fail** | correct | pass | same |

**Why the suite can't see it.** The suite never calls an emit method or `_log_at_level`. It calls `_frame_info`, `_console_dict` and `_file_dict` directly (`test_logger_frame_resolution.py:79, 98, 112, 117, 126-127`). So it pins the prescribed *implementation*, not the emitted caller.

Two smaller errors in the handoff's description of the suite:
- "Both classes fail" under a two-hop walk is wrong. Only `TestFrameResolutionEquivalence` fails.
- Only depths 0 and 1 can detect a hop-count error. Depths 5 and 12 pass under V4 because `_probe` recurses from a single line (`:77`).

**Steelman, attempted and failed.** I looked for a P2.1 failure that only P0.4 catches:
- Moving `tsp` after the filter shifts its value by microseconds. At the second-resolution format (`constants.py:473`) the precision doesn't change, so P0.4 sees nothing.
- The only catches are careless side edits next to the changed lines: dropping the sentinel (M1) or changing precision (M3). P0.4(b) catches those only if it runs through the real emit path, which (d)(i) doesn't.
- Where P0.4 does have teeth is P2.2/P2.3, the format-assembly code. A console/file closure swap (M11) is caught on the file sink.

**What the handoff should say instead:** "P2.1 has no detector today. Land it with a caller-identity test through the real emit path, driving all eight methods. That test is about 30 lines using the existing `_load_private_logger` pattern in `test_logger_level_state_reconciliation.py`. Add the assertion 'the caller file is never `logger.py`', and make P2.1(d) a permanent AST test. P0.4 gates P2.2/P2.3 and P3, not P2.1."

## Attack 2 — the P0.4 spec cannot meet its own acceptance: REFUTED

**(i) Three stubs, not one, and the spec mentions none of them.**
- `conftest.py:832-857`: every network's logger becomes `_noop_logger`.
- `conftest.py:917-935`: `CandidateUnit.__init__` and `__setstate__` are patched the same way.
- `conftest.py:942-948`: the `_log_at_level` no-op. Its original is kept only in a fixture-local variable. It isn't exported the way `_REAL_INIT_LOGGING_SYSTEM` is (`:860-873`).
- A working escape already exists: private module loads, in `test_logger_level_state_reconciliation.py` and `test_logger_per_level_exercise.py`. The spec doesn't mention it.
- Without it, a naive checker passes on an empty capture. M5 produced 0 console records and still "all matched".

**(ii) Mutation probe** (`p04_mutation_probe.py`). The golden was `034716e3ea95` for every mutant:

| mutation (site at `0d2d826`) | golden | envelope checker (real path) |
|---|---|---|
| M1 drop the `+` sentinel. It is added in code at `logger.py:581` and `:582`, not in any formatter string | missed | fails on the file sink; **passes on console** (0 records, because the stream was selected by `+`) |
| M3 date format `.%f` (`constants.py:473`) | missed | fails |
| M5 `print` → stderr (`:581`) | missed | **passes** (vacuous, 0 records) |
| M11 console/file closure swap (`:579-580`) | missed | fails on the file sink |
| M12 drop the lazy `message % args` (`:578`) | missed | **passes** |

Also missed by every part (a)–(e):
- The file name: `constants.py:482`, and hardcoded at `observability.py:110`.
- Rotation: `observability.py:111-116`, `constants_logging.py:276-277`.
- Caller identity.

RECON N-4 lists five breaking surfaces. The fifth, filename plus rotation, is absent from P0.4 entirely. It is exactly what P3.3 and P3.4 change.

**"Covers all three copies of the prefix" is also wrong.** The golden omits the Path B console formatter (YAML `:44-45`), which writes into the redirected stdout that capture (a) is about. It also omits every `datefmt`. Identical format strings do not mean identical records (`datefmt_probe.py`):
- Path B file: `(2026-09-22 20:49:02)` (YAML `:48`)
- Path C file: `(… 20:49:02,180)` (`observability.py:118`, which sets no `datefmt`)
- Path B console: `(26-09-22 …)`

**(iii) A static marker inventory misses real cases at `0d2d826`.**
- `cascade_correlation.py:2247` has the template `…with %s processes.`, but the consumer regex is `…with \d+ processes`. A regex can't be checked against a template, and a literal-substring check can't verify the rendered number.
- The `Output Layer Training - Epoch` marker exists at INFO (`:2181`, display epochs) and at DEBUG (`:2182`). Delete `:2181` and the literal survives in source while an INFO run emits nothing.
- `fit: Training completed.` survives in dead code (`backups/cascade_correlation-ORIG.py:2079`).
- A dynamic check has to defeat all three stubs and run at INFO. The inventory itself lives in juniper-ml, so enforcing it in cascor requires vendoring it.

**(e) points at the wrong repo.** The recommended test lives in cascor, where an unmarked test is silently deselected (`-m "unit and not slow"`, cascor `ci.yml:313`). The spec only names juniper-ml's `test_ci_test_wiring_drift.py`.

## Attack 3 — the gate "16.70 % ≥ 10 %, so P2 runs": WEAKENED

**Where the handoff holds.** The rule fired correctly. Roadmap §13.1 decision 1 binds the 10 % to "what the instrument can attribute". I tried to refute this and failed.

**Where it doesn't.**
- **"Lower bound" is not established.** A lower bound only makes a GO safer if it really is one. cProfile inflates the discarded emit path 3.17× (`p21_value_probe.py`: 1.312 s unprofiled against 4.159 s tottime for 553,471 calls). `currentframe` costs 248 ns per call unprofiled, against the corpus's 829 ns (0.507 s / 611,870). Meanwhile the instrument omits the builtins (`datetime.now`, `print`, `open`, `strftime`). So the error is two-sided with an unknown sign, and the 1.67× margin sits inside a demonstrated ~3× bias. The framing errs in the dangerous direction for a GO.
- **The gate doesn't discriminate for P2.** About 1.03 s of the 6.18 s is `_filter_by_level` (0.692 s) plus `_resolve_level_number` (0.337 s). That is the very item decision 1 cited as a reason to doubt P2, and P2 explicitly doesn't touch it (P2.4 moved to P4.2).
- **P2.2 is smaller than the handoff says.** At `0d2d826`, P2.2's per-call "seventh closure" is gone from the emit path (`logger.py:427-436` has test callers only). The remaining six closures are paid only on the 58,399 emitted records.
- **Worker self time is not wall-clock.** It is the summed tottime of 32 parallel worker profiles, and it excludes the parent process. Unprofiled, P2.1 saves 0.669 s per corpus-equivalent, about 21 ms per candidate training. The same saving measured under cProfile reads 2.068 s, 3.1× larger. P2's acceptance ("re-measured delta against P0.1's corpus") would therefore overstate it about 3×.

**What the handoff should say instead:** "16.70 % is the profiled, attributable share. Its bias against the unprofiled cost is two-sided. Report P2's addressable ceiling, and measure P2's delta as an unprofiled wall-clock A/B (V0 against V1 on the P0.1 cell)."

## Attack 4 — prioritisation: WEAKENED

1. **P0.5 should come first.** The roadmap §2.3 calls it "free on day one". It determines whether a cascor-side P0.4 can run at all. The escape pattern already exists, and the stub's stated rationale (removing `getouterframes` overhead) is obsolete since #563.
2. **P2.1 doesn't need P0.4.** With its own caller-identity test it is better protected than roadmap guardrail P2-G1's gate. It is low severity: nothing parses the field, and unprofiled it halves the discarded-call cost (2,371 → 1,162 ns per call on this host).
3. **P0.4's real customer is P3.** It should be specified against P3's surfaces, and its live capture run can share one run with P0.3 (with distinct log dirs).
4. **P2.2** is a candidate to fold into P3.1, which replaces `:579-580` anyway.
5. **Decision 4's timing is unaddressed.** Converging the mirror before P2/P3 adds a mirror-plus-release obligation to every `logger.py` edit (roadmap §10).

Neither decision 7 nor the P6.4 residue is more urgent: the first is not a blocker, and the second needs an owner ruling.

## Attack 5 — the P2.1(c) prescription: SURVIVES at `0d2d826`, with a forward hazard

**Call stack.** User code → one of the eight methods, each calling `_log_at_level` directly (`logger.py:612, 620, 628, 636, 644, 652, 660, 668`) → `_log_at_level` (`:565`) → `_console_dict` / `_file_dict` (`:331`, `:349`) → `_frame_info` (`:316`, which takes `frame.f_back`). Inside `_log_at_level`, `cls._frm().f_back` is the emit method's frame. That is exactly what `_frame_info` receives today, so one hop is correct.

**Other paths:**
- No emit method calls another emit method.
- The inherited `log()` and the custom-level methods (`:1059-1063`) go through stdlib `_log`, never `_log_at_level`.
- The inherited `exception()` raises `TypeError` (`error()` rejects `exc_info`), and `warn()` names `logging/__init__.py:warn`. Both behave identically in V0 and V1, and no live Path-A caller uses either.
- V1 matches V0 on every tested entry path.

**Forward hazard.** P2.1 makes caller resolution depend on call depth. The ruled P4 prototype inserts `BoundLogger._emit` between the public method and emission (`2026-09-10_p41_a2bind_prototype.py:66-75`). That reproduces V2 on every record, and the named suite passes V2.

## Changes to the P0.4 design that would make it meet its own acceptance

1. **Define the acceptance mutation set:** M1 on both sinks, M3, every `datefmt`, M5, file rename, rotation parameters, M11, M12, a marker text edit at `:2247`, the `:2181` INFO→DEBUG move, and V2/V3. Each must fail the harness in cascor CI.
2. **Run through the real emit path,** via private load or a subprocess, with a liveness assertion that each sink produced a non-zero number of records.
3. **Use strict envelopes:** typed fields (line is `\d+`, exact date format), `+` required on both sinks, a func field only in the file sink, the caller-identity check, and "the caller is never `logger.py`".
4. **Golden the timestamp-masked rendered record from each path,** not source strings. At minimum, pin all format/`datefmt` pairs, the file name, the rotation parameters and the sentinel literals.
5. **Add N-4's filename-plus-rotation surface.**
6. **Vendor the consumers' regexes into cascor,** check them against rendered output at INFO with all three stubs defeated, and add a juniper-ml-side test that the vendored set still covers what the scripts compile.
7. **Capture stdout and stderr separately,** including Path B console records.
8. **Mark the test `unit`** so cascor CI doesn't deselect it.

## Side findings (stale claims in the frozen documents)

- The roadmap §5 "Why P2.1(c) matters" paragraph still says the suite "calls `_frame_info` directly". That is the framing the handoff's own §7 defect 1 retracted, but the roadmap was never corrected.
- The roadmap's P2.2 row and P4.2 both still cite the `_get_log_level` lambda at `:516`, which is gone from the emit path.
- RECON §3's claims that Path B timestamps are millisecond and that Paths B and C are indistinguishable on disk are contradicted by YAML `:48`. This undercuts P0.3(a)'s premise.
- Line drift at `0d2d826`: `observability.py:119` is now `:118`; the console prefix is at `constants_logging.py:156`, not `:157`; and that file actually lives at `src/cascor_constants/constants_logging/constants_logging.py`.

## Appendix — probe sources (verbatim)

Scratch root: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/laneB1/`. `base/` is `git archive 0d2d826 src/cascor_constants src/log_config conf src/tests/unit/test_logger_frame_resolution.py`. Run with `/opt/miniforge3/envs/JuniperCascor1/bin/python` and `env -u JUNIPER_CASCOR_LOG_DIR`.

**emit_driver.py**
```python
import contextlib, inspect, io, json, os, sys
from log_config.logger.logger import Logger
OUT = sys.argv[1]
if os.path.exists(OUT):
    os.remove(OUT)
Logger._logging_file = OUT
def _file_lines():
    if not os.path.exists(OUT):
        return []
    with open(OUT, encoding="utf-8") as f:
        return f.read().splitlines()
def run_case(name, fn, level="INFO"):
    Logger.set_level(level)
    before = len(_file_lines()); buf = io.StringIO(); exc = None; expected = None
    with contextlib.redirect_stdout(buf):
        try:
            expected = fn()
        except Exception as e:  # noqa: BLE001
            exc = f"{type(e).__name__}: {e}"
    return {"case": name, "expected": expected, "exception": exc,
            "console": [ln for ln in buf.getvalue().splitlines() if ln.startswith("+")],
            "file": _file_lines()[before:]}
def case_class_info():
    Logger.info("CASE1 class-bound info"); return [("case_class_info", inspect.currentframe().f_lineno)]
def case_all_eight():
    out = []
    Logger.trace("CASE2 trace"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.verbose("CASE2 verbose"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.debug("CASE2 debug"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.info("CASE2 info"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.warning("CASE2 warning"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.error("CASE2 error"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.critical("CASE2 critical"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    Logger.fatal("CASE2 fatal"); out.append(("case_all_eight", inspect.currentframe().f_lineno))
    return out
def case_instance_bound():
    inst = Logger.__new__(Logger)
    inst.info("CASE3 instance-bound info"); return [("case_instance_bound", inspect.currentframe().f_lineno)]
def case_alias():
    f = Logger.warning
    f("CASE4 aliased warning"); return [("case_alias", inspect.currentframe().f_lineno)]
def case_stdlib_warn():
    import warnings
    inst = Logger.__new__(Logger)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        inst.warn("CASE5 stdlib warn"); return [("case_stdlib_warn", inspect.currentframe().f_lineno)]
def case_stdlib_exception():
    inst = Logger.__new__(Logger)
    try:
        raise ValueError("boom")
    except ValueError:
        inst.exception("CASE6 stdlib exception"); return [("case_stdlib_exception", inspect.currentframe().f_lineno)]
def _nested_helper():
    Logger.error("CASE7 nested helper"); return [("_nested_helper", inspect.currentframe().f_lineno)]
def case_nested():
    return _nested_helper()
def case_percent_args():
    Logger.info("CASE8 percent %s", 5); return [("case_percent_args", inspect.currentframe().f_lineno)]
CASES = [("class_info", case_class_info, "INFO"), ("all_eight_at_TRACE", case_all_eight, "TRACE"),
         ("instance_bound", case_instance_bound, "INFO"), ("alias", case_alias, "INFO"),
         ("stdlib_warn", case_stdlib_warn, "INFO"), ("stdlib_exception", case_stdlib_exception, "INFO"),
         ("nested_helper", case_nested, "INFO"), ("percent_args", case_percent_args, "INFO")]
print(json.dumps({"driver": os.path.basename(__file__), "results": [run_case(n, f, lv) for n, f, lv in CASES]}))
```
(The docstring and `# noqa: E702` comments of the original are omitted; the code is otherwise identical. The line numbers in the table above refer to the original file.)

**p21_variant_probe.py** (core; the variant edits are exactly these)
```python
EMIT_OLD = "cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level="
EMIT_NEW = "cls._log_at_level(level="
FILTER_LINE = "        if cls._filter_by_level(level=level, log_level=cls._log_level):\n"
FRAME_INFO_OLD = "        target = frame.f_back if frame is not None else None\n"
FRAME_INFO_TWO_HOP = "        target = frame.f_back.f_back if frame is not None and frame.f_back is not None else None\n"
def make_variant(name, frame_expr, two_hop_frame_info=False):
    src = open(os.path.join(BASE, LOGGER_REL), encoding="utf-8").read()
    if frame_expr is not None:
        assert src.count(EMIT_OLD) == 8
        src = src.replace(EMIT_OLD, EMIT_NEW)
        src = src.replace(FILTER_LINE, FILTER_LINE + f"            frame = {frame_expr}\n" + "            tsp = cls._tsp()\n")
    if two_hop_frame_info:
        src = src.replace(FRAME_INFO_OLD, FRAME_INFO_TWO_HOP)
    ...  # copytree(BASE, variants/<name>) and write the modified logger.py
VARIANTS = [("V0_status_quo", None, False), ("V1_prescribed_f_back", "cls._frm().f_back", False),
            ("V2_forgot_f_back", "cls._frm()", False), ("V3_one_hop_too_many", "cls._frm().f_back.f_back", False),
            ("V4_two_hop_frame_info", "cls._frm()", True)]
ENV_FILE = re.compile(r"^\+\[(?P<file>[^:\]]+): (?P<func>[^:\]]+):(?P<line>[^\]]+)\] \((?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\) \[(?P<level>[A-Z]+)\] (?P<msg>.*)$")
ENV_CONSOLE = re.compile(r"^\+\[(?P<file>[^:\]]+): (?P<line>[^\]]+)\] \((?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\) \[(?P<level>[A-Z]+)\] (?P<msg>.*)$")
def golden(tree):  # (d)(i): constants_logging.py:152-158 + logging_config.yaml:47
    cl = open(os.path.join(tree, "src/cascor_constants/constants_logging/constants_logging.py")).read().splitlines()
    yml = open(os.path.join(tree, "conf/logging_config.yaml")).read().splitlines()
    return hashlib.sha256("\n".join(cl[151:158] + [yml[46]]).encode()).hexdigest()[:12]
# per variant: pytest -q -p no:cacheprovider -m unit <tree>/src/tests/unit/test_logger_frame_resolution.py
#   (PYTHONPATH=<tree>/src); run emit_driver.py; caller_identity_ok = every file record names
#   emit_driver.py:<expected func>:<expected line>
```

**p21_value_probe.py** (core)
```python
N_DISCARD = 553_471  # 611,870 - 58,399 (the corpus's own _console_dict count)
# load(variant): importlib spec_from_file_location under a private alias; _logging_file -> scratch; set_level("INFO")
def best_wall(fn, n):  # best of 5, unprofiled
    ... for _i in range(n): fn("discarded %s", 1)
def profiled(fn, n):
    pr = cProfile.Profile(); pr.enable()
    for _i in range(n): fn("discarded %s", 1)
    pr.disable(); st = pstats.Stats(pr)
    cf = sum(v[2] for k, v in st.stats.items() if k[2] == "currentframe")
    logger_tt = sum(v[2] for k, v in st.stats.items() if k[0].endswith("logger.py") or k[2] == "currentframe")
    return cf, logger_tt
# measured: v0.trace / v1.trace wall and tottime; plus inspect.currentframe() alone x N
```
Output: currentframe 248 ns/call; V0 2,371 ns/call; V1 1,162 ns/call; wall saving 0.669 s; profiled saving 2.068 s; inflation 3.17×.

**p04_mutation_probe.py** (the mutants; each `old` string asserted to occur exactly once)
```python
MUTANTS = {
 "M1_drop_plus_sentinel": [(LOGGER, 'print(f"+{_console_message', 'print(f"{_console_message'), (LOGGER, '_line = f"+{_file_message', '_line = f"{_file_message')],
 "M3_timestamp_precision": [(CONSTANTS, '_PROJECT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"', '_PROJECT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"')],
 "M5_console_to_stderr": [(LOGGER, 'print(f"+{_console_message(frame, tsp, level, message)}")', 'print(f"+{_console_message(frame, tsp, level, message)}", file=sys.stderr)')],
 "M11_console_file_swap": [(LOGGER, "_console_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)", "_console_message = cls._logging_message(cls._formatter_string_file, cls._file_dict)"), (LOGGER, "_file_message = cls._logging_message(cls._formatter_string_file, cls._file_dict)", "_file_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)")],
 "M12_drop_lazy_percent": [(LOGGER, "                message = message % args\n", "                pass\n")]}
# check: per-sink record counts; all(ENV_*.match(x)) per sink; "CASE8 percent 5" rendered; golden()
```

**datefmt_probe.py**
```python
cfg = yaml.safe_load(open("base/conf/logging_config.yaml")); fb = cfg["formatters"]["formatter_file"]; fc = cfg["formatters"]["formatter_console"]
PATH_C_FMT = "[%(filename)s: %(funcName)s:%(lineno)d] (%(asctime)s) [%(levelname)s] %(message)s"
rec = logging.LogRecord("juniper", logging.ERROR, "/x/cascade_correlation.py", 2247, "marker", None, None, func="train_candidates")
print(fb["format"] == PATH_C_FMT)                                   # True
print(logging.Formatter(fb["format"], fb.get("datefmt")).format(rec))  # (2026-09-22 20:49:02)
print(logging.Formatter(PATH_C_FMT).format(rec))                     # (2026-09-22 20:49:02,180)
print(logging.Formatter(fc["format"], fc.get("datefmt")).format(rec))  # (26-09-22 20:49:02)
```

---

## Lane B2 - omission, executability, receipts (opus)

*agent `afc362a636be462f4` · last-assistant-text · 21615 chars*

# Lane B2 adversarial review: HANDOFF_2026-09-22 (logging arc)

**What was reviewed:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md` (juniper-ml `7b226ca0`), checked against the predecessor handoff `HANDOFF_2026-09-17_…p14-is-an-option-d-decision.md`, the roadmap `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, the reconciliation doc `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`, cascor at `0d2d826` (which matches GitHub `main`), and GitHub state.

**Changed:** nothing in any repo. Probes live in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/laneB2/`. Their sources are at the end.

## Lens 1: residue loss

| Predecessor item | Class | Evidence | If DROPPED: does it exist elsewhere? |
|---|---|---|---|
| §0.1 P1.4 wire half | SHIPPED | cascor#670 (`8065ca0`); roadmap §13.1 decision 10 | |
| §0.1 step 1 memo fix | SHIPPED | cascor#667 (`c1de246`); `logger.py:1114` on main | |
| §0.1 step 3 re-measure, then rule | SHIPPED | decision 11 (post-fix Option D ~461 ns, guard ~31 ns) | |
| §0.1 step 5 "ask before merging" | CARRIED | new doc §3 item 4 | |
| §0.2 commit the P1.4 probes | SHIPPED | five `util/ad-hoc/2026-09-2[12]_p14_*` files at `7b226ca0` | |
| §0.2 transcribe decisions 8/9/10 | SHIPPED | ml#1976, ml#1995 | |
| §0.3 P6.4 ruling | SHIPPED in part (#675, hot files) | the ruling is only in #675's commit body; decision 6 still reads "P6.4 open … held" | the canonical §13.1 record is **not** updated |
| §0.4 P0.1/P0.2 | SHIPPED | ml#2004; decision 1 RESOLVED | |
| §0.4 caveat that 16.70 % is a lower bound | DROPPED | the new doc quotes 16.70 % bare | roadmap decision 1. Harmless for the ≥10 % gate |
| §0.5 env repair is moot | CARRIED | the reason is **true**: my probe imports torch 2.11.0+cu130 under py3.14.7 both with and without `env -u` | |
| §7 bullet 2: `logging_utils.py` still carries the wrong inline levels `5`/`15` and five `logger.log(level,msg)` sites that raise TypeError; **fixed only on the WIP branch** | **DROPPED** | on main, `logging_utils.py:90` passes `5` and `:94` passes `15`; `logger.log` is at `:82,:158,:161,:181,:199`. The fix exists only at `1b918e6` (unsigned, no PR) | **Only** in the predecessor, the WIP commit, and a stale memory file. The new doc, decision 10 and the #573 comment all say "fixed" |
| §5.8 "re-land the WIP content through `util/open_signed_pr.py`" | **DROPPED** | replaced by "decide whether to close it" | only in the predecessor |
| §0.0.3 the WIP commit message is wrong (line numbers, 2 f-strings not 3) | DROPPED | | only in the predecessor |
| §0.0.5(c) + §2 counter-argument: the guard idiom states the level twice, and nothing tests `_display_training_progress` per level | DROPPED | still true after #670: it added no test, and P1.5 (`test_logger_per_level_exercise.py:109-110`) drives only `_multi_output_correlation` and `_get_correlations` | only in the predecessor (roadmap P6-G1 states the general rule) |
| Decision 5 citations drifted ~+55 lines (`isEnabledFor` is `:1085`, not `:1026`) | DROPPED | | the roadmap still cites `:1026` in decision 5 and P4.1 |
| Re-derivation trap: untracked `src/backups/check.py`; `grep -r` gives ~1,144 | DROPPED | | partly in roadmap P6.1 |
| First wiring site must sit outside the byte-gated trees | CARRIED | the #573 comment says it; moot after decision 10 | |
| Decision 5 A2-bind: "nothing lands until P1.1, which is now shipped" | **DROPPED** from §0.4 "Ruled but unstarted" | P4.1–P4.3 are now unblocked. The §0.2 note "P2.4 belongs to P4.2" is kept while P4 itself is not listed | roadmap §7 and decision 5 |
| Decision 6: P6.1–P6.3 authorised | DROPPED | P6.1 is visibly not done: `src/cascade_correlation/backups/` still holds 5 tracked files at `0d2d826` | roadmap decision 6 |
| Trap 5.1 (env broken) | CARRIED as obsolete | | |
| Trap 5.2: the byte-gate mirrors the caller, not the callee; `logger.py` is on `_INTENTIONAL_DIVERGENCE` | DROPPED | directly relevant to P2 (edits `logger.py`) versus decision 4's convergence | roadmap traps 2 and 5; memory `reference_cascor_model_verbatim_extraction_drift` |
| Trap 5.3: lint with the pinned tools | DROPPED, **still live** | local `black` is 26.5.1, cascor pins 25.1.0; `/tmp/claude-1000/lintenv` still exists | memory ✓ |
| Trap 5.4: staging tree without `__init__.py`; `sys.path` loop order | DROPPED | | only in the predecessor and comments in `2026-09-15_p13_verify_both_trees.py` |
| Trap 5.5: a probe must not reconstruct the code under test | DROPPED | P0.4(d)(i) is exactly a constants check | memory ✓ |
| Trap 5.6: MagicMock hides defects; mutation-check | PARTIAL | "Mutation-check it" is kept; the conftest `_noop_logger` seam is not | memory project file |
| Trap 5.7: gh 2.46.0 | DROPPED, **still live** | `gh --version` = 2.46.0 | memory ✓ |
| Trap 5.8: headless signing hangs | DROPPED | | memory ✓ |
| Trap 5.9: `git grep -E (?:…)` returns empty silently | DROPPED | | only in the predecessor |
| §1 "check the count, not the exit code" (pytest) | DROPPED | the new §1 says "expect EXIT 0" | memory `reference_vacuous_pass_check_class` |
| #647 lesson: unmarked tests are silently deselected | DROPPED | directly relevant to P0.4's new cascor test | memory ✓ |
| §6 `.serena/project.yml` dirty on cascor main | SHIPPED | cascor main is clean now | |
| §1/§6 WIP worktree `juniper-cascor--wip--logging-p14--20260921-0340--1b918e61` | **DROPPED** | still exists, clean, and holds the branch | only in the predecessor |
| §6 scratch `/tmp/claude-1000/{p14,cascorenv,lintenv}` | DROPPED | all three still exist (tmpfs) | only in the predecessor |

## Lens 2: executability

### (a) Questions a fresh session must answer before writing P0.4 code

1. **Which repo does each part live in?** Parts (a)–(c) are never assigned. Part (e) implies a juniper-ml test exists, but option (d)(i) is cascor-side. That makes this a cross-repo task, and there is no worktree or merge-order guidance for that.
2. **Option (d)(i) does not cover the envelope's breaking elements.**
   - The `+` sentinel is hardcoded at `logger.py:581-582`.
   - Timestamp precision lives in `constants.py:473` (`_PROJECT_LOG_DATE_FORMAT`), in the YAML `datefmt` at `:45` (2-digit year) and `:48`, and in Path C's missing `datefmt` (so it gets default milliseconds).
   - None of these sit in the three named line-sets.
   - Citation errors: `api/observability.py:119` is `:118` at `70edfc4`, `010d035` and `0d2d826`. The console function-name omission is at `:156`, not `:157`. `constants_logging.py:248-271` holds decoy format constants in a different shape that the logger never uses.
3. **Option (d)(i) does not cover part (c)**, which the doc calls "the half that matters most." Where the marker inventory lives, and how it fails a cascor PR, is left open.
4. **What are the "~17 scripts"?** No artifact lists them. The reconciliation doc's N-4 gives only "~17". An obvious grep (`git grep -l -E "juniper[_-]cascor\.log" 7b226ca0 -- util/ scripts/ tests/`) returns **31** files, including launchers that write the log rather than parse it.
5. **How does a cascor test reach the real emit path?** `conftest.py:891-955` (session-scoped, autouse) turns `_log_at_level` into a no-op and swaps every CandidateUnit's logger for `_noop_logger`. The original method is not exposed. A working precedent exists and is not mentioned: a private module load in `test_logger_level_state_reconciliation.py:79-84` and `test_logger_per_level_exercise.py:71-75`.
6. **Marker and timeout.** CI runs `pytest -m "unit and not slow" src/tests/unit --timeout=60` (`ci.yml:312-316`). A new test needs `pytestmark = pytest.mark.unit`. The §1 local command uses `--timeout=900`, so a test that passes locally can time out in CI.
7. **What does "reference capture" mean?**
   - Both captures already exist, unarchived, from P0.1 at `8065ca0`:
     - redirected stdout: `~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/cli-01/direct_cli.log` (8.9 MB);
     - file sink: `…/cli-01/logs/juniper_cascor.log` (10.2 MB, 59,641 lines).
   - The file sink mixes 1,238 Path B lines that have **no `+`**, so an envelope checker must know which path wrote each line.
   - The direct-CLI arm never exercises Path C (0 millisecond timestamps), so it cannot cover "all three copies."
   - A new live capture needs a distinct `JUNIPER_CASCOR_LOG_DIR` and reaper protection. Neither is mentioned.
8. **P0.4 is already in flight.** A cascor worktree `feat/logging-p04-envelope-harness` exists at `0d2d826` (clean, no PR), and a juniper-ml branch `feat/logging-p04-marker-census` exists. §1 has no collision check.
9. **P2.1's "only detector" is not a detector** of P2.1's likely mistake (probe below). If P2.1 captures the frame in `_log_at_level` but forgets `.f_back`, every record reads `+[logger.py: 645]`. The frame-resolution suite still passes 6/6 plus 7 subtests. The envelope and marker checks would also pass, and N-4 says nothing parses that field.
10. **P2.2 is stale and under-specified.**
    - The "seventh closure" (`logger.py:516`, the one built before the filter) was present at `70edfc4` and gone from `bbdcbb6` (#644) onward.
    - The in-source note at `logger.py:162-171` says P2.2 must delete `_get_log_level`, `_get_log_level_check` and two attributes. That is symbol loss, so it needs an `Allow-Symbol-Loss:` trailer. It also breaks `util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` and `test_logger_coverage.py:676-690`.
    - P2's acceptance baseline is the P0.1 corpus at `8065ca0`, which predates #675, so a measured delta would mix P2 with #675.

### (b) §1 verification block, command by command

| Command | Verdict |
|---|---|
| `CASCOR=…` then `git -C "$CASCOR" …` | Fragile. Env vars do not persist across Bash calls, so an empty `$CASCOR` makes `git -C ""` silently use the cwd (juniper-ml) — confirmed in the git(1) man page. This sandbox also refuses `$VAR` in an option position. |
| `fetch` + `log --oneline -3 origin/main` | **Does not certify its label.** `c1de246` was never in the top 3, even at `010d035`. `010d035` drops out after one more merge. Needs `git merge-base --is-ancestor`. |
| Memo-fix grep | Works: prints `1114: configured_level = cls._resolve_level_number(cls.get_level())`. Certifies its label. |
| Byte-gate md5 | Prints `1` today, but **passes vacuously**: when both `git show` calls fail (exit 128, two 0-byte files) it still prints `1`. It also checks one file out of four gated trees. |
| Unit suite | **Not executable as written.** `bash -n` reports a syntax error at `<a cascor worktree> &&`. None of the listed worktrees is at main. "Expect EXIT 0" has no test-count check. Under the conftest stub it certifies nothing about emission (roadmap §1 claim 4). |
| P0.2 re-run | Same placeholder syntax error. The script and 32 `.prof` files exist. Left to Lane A3. |

### (c) §4 traps and §5 git status

- Traps §4.1–§4.7 are actionable. §4.7 lacks signing and the `gh` traps.
- §5 cleanup is **not actionable as written**:
  - Four of the five worktrees are dirty, not one.
  - My blob comparison shows the memo, P1.4-guard and P6.4 dirt is byte-identical to what merged, so it is spent but still needs `--force`.
  - The `--measure--` worktree's logger patch really differs from anything merged.
  - The `p01` worktree holds 5 ignored `cascor-snapshots/*.h5` files, which `git worktree remove` deletes.
  - The sixth worktree (the WIP one) is omitted. It blocks §7's `git worktree add … wip/…` and any branch deletion. It is also directly usable as the `--old` side of the #667 reproduction.
  - "docs/REFERENCE.md § Worktree Procedures" is ambiguous. Only juniper-ml has it ("…Reference"); cascor's procedure is `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.
- "Decide whether to close" the WIP branch would destroy the only copy of the `logging_utils` fix. It re-lands cleanly: main has not touched those 3 files since the merge base `70d5ca1`.

## Lens 3: what it claims it did

| Claim | Receipt | Verdict |
|---|---|---|
| Lane A agents died on the rate limit | none available | unverifiable |
| #573 "now carries a status comment" | 1 comment, 2026-09-22T08:03Z | ✓ but **stale**: says P6.4 is "held" and P0.1/P0.2 are open |
| §2: #667, #670, #675, ml#1976, ml#1995, ml#2004 merged | `gh`: all MERGED; content present | ✓ |
| "Phase 1 is complete" | `logging_utils.py:90,:94` still pass `5`/`15`; roadmap P1.4 says "Do not leave a third definition" | ✗ by the roadmap's own acceptance |
| §3 "Recorded in §13.1" | item 1 → decision 10 ✓; item 2 (P6.4 hot files) absent, decision 6 still says held ✗; item 3 partial; item 4 only as decision 9's principle | 1 of 4 true, 1 false, 2 partial — the defect it faulted its predecessor for |
| `logging_utils` "fixed-but-unwired" (§3; decision 10; #573) | fixed only on unmerged `1b918e6` | ✗ |
| WIP branch at `1b918e6`, pushed, unsigned, no PR | GitHub head `1b918e61…`, `%G?`=N, 0 PRs | ✓ |
| Five worktrees "merged or spent" | spent by content ✓; 4 of 5 dirty, one worktree omitted | partial |
| §6: decision 5's 55–110 ns came from stubs | §13.1 decision 5 (roadmap lines 665-670) still reads "faster than the status quo on every call site" | ✗ not applied to the source |
| §6: Option D was overstated | decision 10 ✓; decision 8 still says "§11's Option-D conflict is why"; memory project file still says it "forecloses P7" | partial |
| §6: 33 % figure overtaken | decision 1 ✓ | ✓ |
| §7 defect 1 "corrected" | roadmap §5 "Why P2.1(c) matters" (lines 284-288) still has the wrong claim. The correction also over-corrects: the test **does** call `_frame_info` directly (`:79, :98, :112, :117`) and never goes through an emit method, which is why it cannot detect the P2.1 slip | ✗ |
| §7 defect 3 "§7.1 now names its file" | the roadmap has no §7.1; it is `…LOGGING-REDESIGN-DESIGN.md` line 363 | ✗ the fix introduced a wrong pointer |
| §7 ✅ "§1 block runs as written" | `bash -n` syntax error | ✗ |
| §7 ✅ `:620`/`:575`, `:1671`, byte-gate, memo, env | re-checked | ✓ |
| §4.5 and §4.6 script behaviours | scripts read | ✓ |

## Top findings, ranked by consequence

1. **`logging_utils.py` is not fixed on main.** Handoff §3, roadmap decision 10 and the #573 comment all say "fixed-but-unwired," and all are wrong: the fix exists only on unsigned `1b918e6`, which §5 invites closing. "Phase 1 complete" fails the roadmap's P1.4 and P1.2 acceptance. The fix should be re-landed (clean) or the module deleted with a symbol-loss trailer.
2. **P2.1's only named detector cannot see P2.1's likely failure** (probe-verified), and P0.4 as specified cannot see it either. P2.1 needs a new caller-identity test that drives a real emit method through a private module load.
3. **§3's "Recorded in §13.1" is false for the P6.4 ruling.** The §6 corrections (decision 5 stubs) and §7 defect 1 were not applied to the roadmap, and #573's only comment is stale.
4. **The P0.4 spec as handed over would build the wrong harness.** Option (d)(i) misses the `+` sentinel, the timestamp precision and the marker inventory. The ~17 scripts are not enumerated. The conftest escape precedent, the unit marker, the 60 s timeout and the existing P0.1 captures all go unmentioned.
5. **The §1 block is a syntax error**, cannot certify `c1de246`, passes the byte-gate vacuously, and misroutes to the cwd if `$CASCOR` is lost between calls. The §7 claim that it "runs as written" is false.
6. **P2.2 is stale** (the seventh closure is gone since #644), and its symbol-loss trailer, probe breakage and pre-#675 baseline are all unflagged.
7. **Live traps were dropped:** pinned black, gh 2.46.0, headless signing, the byte-gate / `_INTENTIONAL_DIVERGENCE` interaction (P2 versus decision 4 ordering), and unmarked-test deselection.
8. **§5 cleanup cannot be followed:** four dirty worktrees, ignored `.h5` files, a sixth worktree omitted, and an ambiguous procedure pointer.
9. **§0.4 omits ruled, unblocked work:** decision 5 (P4.1–P4.3), decision 3/P5.1, and P6.1–P6.3. It also drops P6's gate on P0.4 and P2, even though #675 already shipped P6.4 ahead of that gate.
10. **The memory project file** still says the wire half is Option D and forecloses P7.

## Probe sources

**`probe_p21_detector.py`** (run with the JuniperCascor1 python):
```python
import io, os, shutil, subprocess, sys, tarfile
REPO = "/home/pcalnon/Development/python/Juniper/juniper-cascor"; REV = "0d2d826"
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "mut")
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
PATHS = ["src/log_config", "src/cascor_constants", "src/tests/unit/test_logger_frame_resolution.py"]
ANCHOR = "        if cls._filter_by_level(level=level, log_level=cls._log_level):\n"
MUTATIONS = {"base": None,
  "good": "        frame = cls._frm().f_back  # B2 probe: P2.1 done right\n",
  "wrong": "        frame = cls._frm()  # B2 probe: P2.1 with the .f_back forgotten\n"}
DRIVER = '''import contextlib, io, os, sys
root = sys.argv[1]
for k in ("JUNIPER_CASCOR_LOG_LEVEL", "CASCOR_LOG_LEVEL"):
    os.environ.pop(k, None)
os.environ["JUNIPER_CASCOR_LOG_DIR"] = os.path.join(root, "logs")
sys.path.insert(0, os.path.join(root, "src"))
from log_config.logger.logger import Logger


def caller_under_test():
    Logger.warning("B2 probe record")  # DRIVER_LINE


buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    caller_under_test()
print("configured level:", Logger._log_level)
print("console record  :", buf.getvalue().strip())
'''
def build(variant):
    dest = os.path.join(OUT, variant)
    if os.path.isdir(dest): shutil.rmtree(dest)
    os.makedirs(dest)
    blob = subprocess.run(["git", "-C", REPO, "archive", REV, *PATHS], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(blob)) as tf: tf.extractall(dest, filter="data")
    if MUTATIONS[variant] is not None:
        p = os.path.join(dest, "src/log_config/logger/logger.py"); src = open(p, encoding="utf-8").read()
        assert src.count(ANCHOR) == 1, "anchor moved; probe is stale"
        open(p, "w", encoding="utf-8").write(src.replace(ANCHOR, MUTATIONS[variant] + ANCHOR))
    return dest
def main():
    driver = os.path.join(OUT, "b2_driver.py"); os.makedirs(OUT, exist_ok=True)
    open(driver, "w", encoding="utf-8").write(DRIVER)
    for variant in MUTATIONS:
        dest = build(variant); test = os.path.join(dest, "src/tests/unit/test_logger_frame_resolution.py")
        env = dict(os.environ, PYTHONPATH=os.path.join(dest, "src"), JUNIPER_CASCOR_LOG_DIR=os.path.join(dest, "logs"))
        r = subprocess.run([PY, "-m", "pytest", test, "-q", "-p", "no:cacheprovider", "-o", "addopts=", "--rootdir", dest], capture_output=True, text=True, env=env, cwd=dest)
        print(variant, r.returncode, [l for l in r.stdout.splitlines() if l.strip()][-1:])
        print(subprocess.run([PY, driver, dest], capture_output=True, text=True).stdout)
if __name__ == "__main__": main()
```
Output:
- `base`, `good` and `wrong` all exit 0 with "6 passed, 7 subtests passed".
- `base` and `good` report `+[b2_driver.py: 11]`.
- `wrong` reports `+[logger.py: 645]`.

**`probe_bytegate_vacuous.bash`:**
```bash
D=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/74df1631-0e10-48e6-8e9a-8e0266961c91/scratchpad/laneB2
R=/home/pcalnon/Development/python/Juniper/juniper-cascor
git -C "$R" show origin/main:src/NO_SUCH_DIR/candidate_unit.py > "$D/c.py" 2>/dev/null; echo "first git show exit: $?"
git -C "$R" show origin/main:NO_SUCH_DIR/candidate_unit/candidate_unit.py > "$D/d.py" 2>/dev/null; echo "second git show exit: $?"
echo "sizes: $(stat -c %s "$D/c.py") $(stat -c %s "$D/d.py")"
md5sum "$D/c.py" "$D/d.py" | awk '{print $1}' | sort -u | wc -l
```
Output: exits 128 and 128, sizes 0 and 0, prints **1**.

**`probe_torch_import.py`:**
```python
import os, sys
print("python", sys.version.split()[0], sys.executable)
print("LD_LIBRARY_PATH =", os.environ.get("LD_LIBRARY_PATH"))
import torch
print("torch", torch.__version__, "from", torch.__file__); print("tensor ok:", float(torch.tensor(1.5) * 2))
```
Run with `-s`, once plain and once under `env -u LD_LIBRARY_PATH -u LIBTORCH`. Both runs show 2.11.0+cu130 working.

**`probe_worktree_dirt_vs_merged.py`:**
```python
import subprocess
CASCOR = "/home/pcalnon/Development/python/Juniper/juniper-cascor"; WT = "/home/pcalnon/Development/python/Juniper/worktrees/"
CASES = [("juniper-cascor--fix--logging-isenabledfor-memo--20260921-0400--c6c848f2", "c1de246", "#667"),
         ("juniper-cascor--fix--logging-p14-guard-display-progress--20260922-0530--0c14e92d", "8065ca0", "#670"),
         ("juniper-cascor--fix--logging-p64-hot-files--20260922-1815--05c13d55", "010d035", "#675"),
         ("juniper-cascor--measure--p14-plus-memo--20260921-0500--1b918e61", "c1de246", "#667 (nearest)")]
def git(*a, raw=False):
    out = subprocess.run(["git", *a], capture_output=True, text=True).stdout
    return out if raw else out.strip()
for name, merged, pr in CASES:
    wt = WT + name
    for p in [l[3:] for l in git("-C", wt, "status", "--porcelain", raw=True).splitlines() if l.strip()]:
        print(name, "SPENT" if git("-C", wt, "hash-object", p) == git("-C", CASCOR, "rev-parse", f"{merged}:{p}") else "DIFFERS", p)
```
Output: every file in the first three worktrees is SPENT; the `--measure--` worktree's `logger.py` DIFFERS.

`handoff_s1_block_verbatim.bash` is a verbatim copy of §1, used only for `bash -n` (syntax error at line 17).

---
