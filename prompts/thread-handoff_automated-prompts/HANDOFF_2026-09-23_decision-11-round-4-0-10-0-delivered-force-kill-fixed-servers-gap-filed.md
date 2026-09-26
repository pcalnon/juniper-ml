# HANDOFF — decision 11 round 4: juniper-ml 0.10.0 delivered, #2046 fixed at the class level, and the `[servers]` extra found hollow

**Date**: 2026-09-23 · **Session**: <https://claude.ai/code/session_01YU3r6fhJViZTi7af6DzqeZ>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/wiggly-imagining-pine`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_decision-11-round-3-0-10-0-cut-and-every-record-closed.md`
(merged as ml#2053; §A below dispositions **every** item it carried, checked against source)

---

## THE GOAL — paste this into the new thread

> **Continue the decision-11 release arc. Only owner actions and optional follow-ups remain.**
>
> **Completed so far**
>
> - **juniper-ml 0.10.0 is on PyPI, and is delivered, not only published.** Paul approved the `pypi`
>   gate: `gh api repos/pcalnon/juniper-ml/actions/runs/35879664979/approvals` lists `pcalnon`,
>   `approved`. That run finished its PyPI job at 19:54:47Z. Over an installed juniper-data 0.14.0,
>   `uv pip install --dry-run "juniper-ml[servers]==0.10.0"` plans `- juniper-data==0.14.0` /
>   `+ 0.15.0`. As the negative control, 0.9.0 plans no juniper-data change. That evidence was
>   scratch and is not committed; re-run both commands in a venv holding `juniper-data==0.14.0`.
> - **juniper-ml#2046 is fixed, as a defect class** (ml#2061, merged 21:04:36Z as `e94a2e11`). Ten hand-copied `_force_kill` helpers read
>   `killpg`'s `ProcessLookupError` as "already dead", which it also is for a live pid that leads no
>   group. A census of every call site found two copies broken in practice: 8 stubs outlived their
>   tests per run, and one of those copies was not in the issue. Five copies now call one
>   `tests/process_cleanup.py::force_kill`, which stops the process, then kills its descendants and
>   group and waits for all of them. It also kills the in-flight `mv` writer that #2046's suggested
>   fix orphaned in 20 of 100 constructed runs.
> - **The wheel-contract probe no longer scores SKIP as a pass**, and it holds **39/39 over the published
>   0.10.0 set** (ml#2063, merged 21:12:25Z as `6848e11d`; evidence in
>   `reports/2026-09-23_decision11-wheel-contract-probe-0.10.0/`).
> - **Filed:** ml#2062 (`[servers]` installs no Juniper client) and ml#2065 (six test files hide 109
>   test methods from direct execution).
>
> **Remaining work, in order**
>
> 1. **Only once Paul says the token is scoped** (add `pcalnon/juniper-recurrence`, Contents: Read and
>    write, to the fine-grained PAT behind `CROSS_REPO_DISPATCH_TOKEN` in juniper-data). A session
>    cannot inspect that PAT's scope, so wait for his word. An early run only repeats the 403: one
>    `curl` step, about 12 s, with no side effects. Then run
>    `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.15.0`, confirm a green
>    `repository_dispatch` run of `CI — bench harness` in juniper-recurrence, and close
>    juniper-recurrence#178. The only attempt is still run 35808713744 (403, 02:01Z). Its two residual
>    gaps (the concurrency group, and a missing listener reading as success) are recorded in #178 as
>    non-blocking.
> 2. **ml#2062 is Paul's decision.** Options (a) and (b) change `[servers]` and need a juniper-ml release;
>    (c) is docs only. `tests/test_pyproject_extras.py:150-152` pins the bare form today.
> 3. **ml#2065** is mechanical and optional: in six files, keep one `__main__` block, last.
> 4. **Worktree cleanup, per `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.**
>    First, `cryptic-juggling-truffle`: its session looks ended (unlocked, still at `f4795f17`), but check
>    that no process runs from it and that its staged copies are on `main` (§A, last row). Second, this
>    session's `wiggly-imagining-pine`, but only after this handoff's PR merges. §D lists what it holds.
> 5. Carried unchanged, all owner or design questions: juniper-data#409 (the equities defaults),
>    juniper-cascor#582 (tier parity), Decision 12 (juniper-data#423; a v1 spec that round 1 rated
>    unsound, and zero code) and the model-core cap (`juniper-model-core>=0.1.0,<0.4.0`, kept
>    deliberately). All still stand. #409, #582 and #423 are OPEN, last active 09-21, 08-29 and 09-23
>    (14:15Z) respectively.
> 6. **Seven packages hold unreleased changes. Each release is Paul's call.** From an unscoped
>    `util/release_train/detect.py` at 21:19Z, by SHIP count: juniper-cascor 17 (plus 1 uncertain),
>    juniper-canopy 14, juniper-data 7, juniper-cascor-model 7, juniper-recurrence 7,
>    juniper-observability 2, juniper-service-core 1. juniper-data is new to the list since 0.15.0.
>    Hygiene: TAG_ONLY=0, NOTES_MISSING=0.
>
> **Key context**
>
> - **Releases and deploy gates are Paul's.** "Merge approval granted" covered this arc's PRs, nothing more.
> - **Run anything that imports cascor with `env -u LD_LIBRARY_PATH`.** The rust_mudgeon libtorch on it
>   makes torch fail with `undefined symbol: _PyCode_SetExtra`, which reads like a wheel defect.
> - **Never write `killpg(getpgid(pid))` in a test helper.** A nohup'd stub shares the test runner's own
>   process group. The five `_force_kill` copies left are handed only `setsid` leaders, which is correct
>   by construction.
> - **Closed on `main` but unreleased:** juniper-data#422, canopy#663, cascor#672. The probe sees two of
>   them in the published wheels: JD-6/7 for data#422, and CC-5 for cascor#672. No check covers
>   canopy#663.
> - **Before any release cut** (for example, if ml#2062 goes to option (a) or (b)): run
>   `util/ad-hoc/2026-09-23_released_section_drift.py` against the previous release's archive. Run the
>   ceremony from a clean worktree at `origin/main`, because it reads its own code and the CHANGELOG
>   from `--repo-root`, and it dates sections in UTC. The daily `release-train.yml` cron cannot cut
>   anything: `RELEASE_TRAIN_MODE` still returns 404, and today's run 35864666965 skipped both the
>   proposal and ceremony jobs.

---

**Documents REFERENCED** (more than one, so every reference carries its filename):

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_decision-11-round-3-0-10-0-cut-and-every-record-closed.md`: the predecessor
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md`: §3 "Known and bounded", which the predecessor carried as item 5
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`: §10, the release record
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`: the protocol this file follows
- `/home/pcalnon/Development/python/Juniper/AGENTS.md`: § Data Contract. Unversioned, edited directly.

**Documents CHANGED**:

- ml#2061: `tests/process_cleanup.py` (new), `tests/test_isolated_stack_script.py`,
  `tests/test_experiment_stack_script.py`, `CHANGELOG.md`, and three new `util/ad-hoc/` scripts:
  `2026-09-23_force_kill_orphan_writer_race.py`, `…_force_kill_survivor_census.py` and
  `…_force_kill_mutation_check.py`.
- ml#2063: `util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py`, plus
  `reports/2026-09-23_decision11-wheel-contract-probe-0.10.0/` (new, 11 files; 12 in the PR with the script).
- This handoff's PR: this file, and `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`
  (§10: the 0.10.0 row, plus a "delivered, not only published" note).
- Unversioned: `/home/pcalnon/Development/python/Juniper/AGENTS.md` (the 0.10.0 bullet, plus #2062), and
  the memory file `project_decision_11_released_2026-09-11.md`.

---

## A. Every predecessor item, dispositioned against source

| item | disposition | evidence |
| --- | --- | --- |
| 1. land ml#2050 / #2051 / #2052 | Already merged before this session began: 15:22, 15:37 and 15:58Z. | `gh pr view N --json mergedAt` |
| 2. verify PyPI + the `[servers]` upgrade | Done. `/pypi/juniper-ml/0.10.0/json` returns 200. The dry run over 0.14.0 plans 0.15.0, and 0.9.0 does not. | run 35879664979 (3/3 jobs success) |
| 3. token scope + notify-consumers | **Blocked on Paul.** No new run since 35808713744. | `gh run list -R pcalnon/juniper-data --workflow notify-consumers.yml` |
| 4. ml#2046 `_force_kill` | Fixed in ml#2061, and widened, because the issue named 2 of 10 copies and missed a broken one. | census before/after; 5/5 mutants |
| 5a. wheel-contract probe re-run | Done in ml#2063: 39/39 PASS, 0 UNCOVERED. The scoring is fixed, and ML-2 (which compared nothing) is fixed. | `reports/2026-09-23_decision11-wheel-contract-probe-0.10.0/` |
| 5b. data#409, cascor#582 | Untouched; still OPEN. Both are owner/design questions. | `gh issue view` |
| 5c. cascor-client `[Unreleased]` lockfile bullet | **Dispositioned: no release needed**, the same as data-client. Since `v0.8.0` nothing under `juniper_cascor_client/` changed. The only packaged-metadata delta is `pyyaml>=6.0.1` in the `[test]` extra. | `gh api …/compare/v0.8.0...main` (13 files, no package code) |
| 5d. the other §3 "known and bounded" items | Unchanged, with no action implied: the 0.15.0 wheel ships its tests; the stale conda pins (do not sweep shared envs); `NPZ_SPLITS` lives in `.constants`. | predecessor's predecessor §3 |
| C-4 Decision 12 | Unchanged. juniper-data#423 is OPEN. Its only activity today is the 14:15Z comment announcing the v1 spec, which predates this session. There is still zero code. | `gh issue view 423 -R pcalnon/juniper-data` |
| C-5 model-core cap | Unchanged, as decided: `juniper-model-core>=0.1.0,<0.4.0`. | `pyproject.toml` `[tools]` |
| "6 UNRELEASED_CHANGES" | Now **7**: juniper-data rejoined after 0.15.0 (7 SHIP). By the predecessor's figures (unit unstated there), cascor went 15 → 17 and canopy 10 → 14 SHIP. | unscoped `detect.py`, 21:19Z (Remaining work item 6) |
| release-cut cautions (predecessor's Key context) | Carried into Key context, with the cron claim re-probed. | variable 404; run 35864666965 jobs |
| §D: the `cryptic-juggling-truffle` copies | **Not done, and now Remaining work item 4.** At session start that worktree was `locked` at `f4795f17`, not the `b6580529` the predecessor recorded. By this handoff the lock is gone, so its session has probably ended. Its staged copies were not inspected: an isolated session cannot run git there. Everything they held should be on `main` (#2049–#2052, merged); confirm that before cleanup. | `git worktree list` |

## B. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch -q origin
gh pr view 2061 --json state,mergedAt; gh pr view 2063 --json state,mergedAt; gh issue view 2046 --json state
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ml/0.10.0/json          # 200
gh run list -R pcalnon/juniper-data --workflow notify-consumers.yml --limit 3                    # only 35808713744 unless the token moved
gh issue view 2062 --json state; gh issue view 2065 --json state                                 # OPEN, OPEN
python3 -m unittest tests/test_isolated_stack_script.py tests/test_experiment_stack_script.py    # Ran 170, OK
# direct execution, UNPIPED so $? is unittest's, not tail's:
PYTHONPATH=. python3 tests/test_isolated_stack_script.py > /tmp/direct.log 2>&1; echo "exit=$?"; tail -3 /tmp/direct.log   # exit=0, Ran 78
# release state; needs network; exit 1 is NORMAL for detect.py:
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper | tail -2
#   18 packages: UNRELEASED_CHANGES=7, UP_TO_DATE=11 / hygiene: TAG_ONLY=0, NOTES_MISSING=0
```

## C. Traps this session hit

1. **`open_signed_pr.py` hit HTTP 502 after creating the branch.** That left an empty ref at the base
   SHA, so a retry would have been refused as a duplicate. Recovery: `util/push_signed_commit.py
   --expected-head <base>`, then `gh pr create`. Check the ref before retrying.
2. **A whole-file upload nearly clobbered #2056's CHANGELOG entry.** `main` moved under the branch
   between two fetches. `git log <base>..origin/main -- <paths>`, run immediately before the upload,
   caught it. The CHANGELOG was rebuilt on `main`'s version with the new bullet re-inserted.
3. **CodeQL blocked the merge on eight empty `except: pass` clauses while every required check was
   green.** Adding a reason comment to each fixed the code. The threads still had to be resolved by
   GraphQL, after `code-scanning/alerts?ref=refs/pull/N/merge` showed them `fixed`.
4. **Squash with two commits:** `squash_merge_commit_message` is `COMMIT_MESSAGES`, and the
   symbol-loss screen regex-matches `Allow-Symbol-Loss:` on every line of `git log --format=%B`. So a
   waiver in commit 1 still counts when it is not the last paragraph. Git's own trailer parser would
   not count it, and other waiver readers may use that parser.
5. **Wrong counts caught before publishing:** "six" copies converted (the truth is five), and "26
   class/def blocks" (counted after the LAST `__main__` block, when direct execution stops at the
   FIRST). Both were in my own text. Publish the criterion beside the count.
6. **`MEMORY.md` is oscillating around its ~25,000-character load limit.** It measured 25,031
   characters. A concurrent session folded 25 pointers into a digest file (22,671), and all 25 stayed
   reachable (checked). Then another session undid it: the digest file is **gone**, and the long
   "Verification discipline" line is back. The index read 25,078 characters at about 21:10Z and
   24,966 at 21:20Z. Over the limit, new sessions silently lose the last line or two. This session's
   own net change is −26 characters. It did not touch other arcs' lines, because two sessions
   compacting one unlocked file only make it worse. **For Paul.** Measure with `wc -m`, not `wc -c`.

## D. Git state

Written from `gh`, `git ls-tree` and `git hash-object` output after both merges, at about 21:20Z.

- **Merged this session:** ml#2061 → `e94a2e11` (21:04:36Z) and ml#2063 → `6848e11d` (21:12:25Z).
  Both head branches are deleted (`git/matching-refs` returns 0 for each). On `main`, `e94a2e11`'s CI/CD
  Pipeline, CodeQL Analysis and Post-Merge Main Verification all succeeded, and so did `6848e11d`'s.
  Both squashes carry their `Allow-Symbol-Loss:` line.
- **Filed:** ml#2062 and ml#2065, both OPEN. A closing note with the two corrections is posted on #2046.
- **This worktree** (`worktree-wiggly-imagining-pine`, locked by its own session) sits at `7fb40892`,
  behind `origin/main`. It holds 21 changed paths. **19 are byte-identical to `origin/main`**, checked
  blob by blob with `git hash-object` against `git ls-tree origin/main`. They are the copies uploaded
  to #2061 and #2063, including the three `probe_*.txt` files that show untracked. The other two are
  unique: the §10 edit to `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`,
  and this file. Both ship in the handoff PR from branch `docs/handoff-decision-11-round-4`. Once that
  PR merges, nothing here is unique, and the worktree can be cleaned up (Remaining work item 4).
- **Validation is incomplete.** Three round-1 lanes ran: a fact-check, a residue-loss audit and a
  fresh-session procedure audit. Their accepted findings are applied. The single round-2 lane, which
  was to check those corrections, **died at the weekly usage limit (HTTP 429) before reporting**, and
  by the owner's instruction the document was archived without re-validation. Treat the round-1
  corrections as unchecked: Remaining work items 4–6, Key context's release-cut cautions, the §A rows
  for C-4, C-5 and UNRELEASED_CHANGES, and this section.
- **Nothing is running.** The session's CI watchers and merge nets have all completed. The scratch
  venvs and dry-run logs lived in the session scratchpad on tmpfs. The committed evidence is in
  `reports/2026-09-23_decision11-wheel-contract-probe-0.10.0/`.
