# HANDOFF 2026-09-23/24 — defect register round 42: everything merged, the owner's sweeper, fix-forward follow-ups

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md`
**Register**: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (every § below is that file's unless named otherwise)
**Merge approval**: granted by the owner for this arc's PRs. **The PR sweeper that un-drafts and arms open PRs as `pcalnon` is the OWNER's** (confirmed 2026-09-24: "Mine: fix forward"). Its merges are intended: do NOT draft or disarm to hold a PR. Validate after the merge and fix forward. Memory: `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`.

## Goal

Continue the defect-register arc: land the three fix-forward follow-ups, then ONE register PR (closes plus new rows), then the API-primer correction, then the later arc items.

### Merged this round (all post-merge `main` CI green)

| PR | Squash | What | Validation state |
|---|---|---|---|
| data#428 | `af7831be` | D-B: ETags / conditional requests / counters out (`APD-DATA-017/-029/-032`). Round-2 fixes (ReDoS-safe linear grammar with an 8192 cap, lock-atomicity tests, `InvalidDatasetIdError`, orphan-artifact preconditions, a write-side If-None-Match that fails closed); harness `PASS: 34 mutations`; 56 tests; 1837 unit | round-3 post-merge validator RUNNING |
| canopy#660 + canopy#678 | `3a6dea95`, `05f2dfc2` | the `APD-ECO-008` code half, and its disclosure follow-up (56/27/26 route figures, WARNING in lifespan, per-source wording) | #678 validated: claims hold; 2 MEDIUM + 2 LOW + 2 NIT, being fixed forward (below) |
| ml#2032 | `8541f4fe` | register rulings X-A / X-B / ECO-008, rounds 1-3 | round-3 corrections NOT independently validated |
| ml#2059 | `f5222f9d` | fork-drift gate: canopy + service-core sites, `SharedPackageGuardTest` | NOT independently validated (self-verified: cross-repo 11/11, negative control, 3 mutations) |
| cascor#678 | `0e016a7c` | X-A + X-B | validated post-merge: 1 gap (ruled, below) + 5 LOW + 2 NIT, being fixed forward |

**Owner ruling 2026-09-24** (extends `APD-CASCOR-013`): **"Keep while fetched splits stay."** The fetch's `dataset_shortfall`, and `current_dataset`, stay while ANY partition of that fetch is still loaded. They clear only once train, val and test have all been replaced. The gap it closes: a train-only inline start after a partial fetch kept the fetched val/test (retain-on-omit, cascor#582) while both fields said null.

### STOPPED at wrap-up (2026-09-24): two follow-ups have partial, UNVALIDATED work, and nothing was pushed

The owner stopped the last three agents to close the session. None of them opened a PR or pushed a
branch. Their uncommitted work is kept in place, and also saved as patches:

| Follow-up | Worktree (KEEP; it holds WIP) | Patch in `reports/2026-09-24_defect-register-round-42/` | Scope still to do |
|---|---|---|---|
| cascor | `juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c` (branch `fix/shortfall-mixed-provenance-and-678-followups`, base `0e016a7`; `src/api/app.py` and `src/api/lifecycle/manager.py`, +289/−101, NO tests yet) | `wip-cascor-followup-base-0e016a7c.patch` | the 2026-09-24 ruling, plus the 7 findings in `cascor678-postmerge-validation.md` |
| canopy | `juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227` (branch `fix/blank-key-678-followups`; `src/main.py`, `src/secrets_util.py` and `src/security.py`, +211/−70, plus two untracked `util/ad-hoc/2026-09-24_*` probes, included in the patch) | `wip-canopy-followup-base-e9053227.patch` | the 6 items in `canopy678-postmerge-validation.md`, including the pre-existing KEY LEAK into logs and Sentry |
| data#428 round-3 validation | none; it was read-only | — | re-run from scratch against `af7831be` or later |

Both worktrees sit in `/home/pcalnon/Development/python/Juniper/worktrees/`. Resume either follow-up
from its worktree, or apply its patch to a fresh branch. **Re-verify the WIP before trusting it**: it
was stopped mid-implementation and never tested.

**Every subagent report of this round is archived verbatim** in
`reports/2026-09-24_defect-register-round-42/`. The `/tmp` task outputs are reaped at session end. The
archive covers:
- ml#2032 round 3;
- canopy#660 round 2;
- the cascor#678 implementation and its post-merge validation;
- the data#428 round-2 validation and fix report;
- the canopy#678 implementation and its post-merge validation.

Also open: **data#435**, which deletes the duplicate `## [0.16.0]` heading that filed #428's entries
under the released 0.16.0. It is a one-hunk PR.

**Cleaned at wrap-up:** the worktrees and local branches of data#428, canopy#660, canopy#678 and
cascor#678 were removed. Each was verified clean, or its edits byte-identical to the merged squash,
first. Their remote branches were already deleted on merge.

### Remaining work, in order

1. **The follow-ups.** Resume the cascor and canopy follow-ups from their kept worktrees (above):
   finish, test, mutation-check, then open each PR with `util/open_signed_pr.py`. Then run an
   independent validation and fix forward. Re-run the data#428 round-3 validation of `af7831be`,
   starting with the ReDoS fix.
2. **Validate ml#2032 (round-3 corrections) and ml#2059 post-merge** with one agent for both.
3. **ONE register PR** (whole-file; start from `origin/main`).
   - **Close `APD-ECO-008`** with the five touches:
     - the §4.9 row gets `**FIXED ([juniper-canopy#660](…) + [juniper-ml#2059](…); disclosure: [juniper-canopy#678](…))** —`;
     - its park/rulings entry;
     - a §5.1 verification row. The evidence: the gate markers at canopy `src/security.py:82,112,116`; the cross-repo run 11/11 against every sibling `main`; the pre-#660 control (`48074653`) failing exactly the two canopy guards; `util/ad-hoc/2026-09-23_verify_shared_package_guard_sites_are_not_vacuous.py` giving `PASS: 3 mutations`;
     - the §2 post-primer FIXED list and counts;
     - the header date.
     Then flip the now-false sentences: §2.3's "(juniper-service-core's copy of the compare is not a gate site at all)", the "…is open" parenthetical near §2's closing, and the ECO-008 entry's "service-core's `matched` loop is watched by nothing" and "not yet filed as rows". Record that `main`'s messages for `3a6dea95` and `0e016a7` are stale: the default or arm-time body.
   - **File five rows in §4.9**, each with a park sentence in the block below the table. The recommended status for all five is *awaiting an owner ruling*. Re-verify every anchor on current `main` first.
     - `APD-ECO-009`: canopy `RequestBodyLimitMiddleware` reads `Content-Length` only (`src/middleware.py`, ~`:59-74` at `48074653`). A chunked or under-declared body bypasses the cap under both parsers; CL+TE passes 64 B under h11 and gets a 400 on httptools. This is the `streaming-body-cap` / `APD-DATA-002` shape. Sev M, Conf High.
     - `APD-ECO-010`: canopy has no failed-auth throttle. That is the `pre-auth-throttle` / `APD-DATA-001` shape; siblings use `FailedAuthThrottle`. Sev M, Conf High.
     - `APD-ECO-011`: canopy's auth-OFF profile. Routes outside `/api/train/*` have no Origin check, and `/api/dataset/generate` reads JSON whatever the `Content-Type` (`src/main.py` ~`:1642`). A cross-site `text/plain` POST from any page therefore regenerates the dataset (measured 200). juniper-deploy's demo and dev canopy set no key. It was found validating ECO-008's fix: say so, and cross-reference it for the `F-CANOPY-*` ledger. Sev M, Conf High.
     - `APD-DATA-054`: the artifact `ETag` is weak because `checksum` = sha256 of an UNCOMPRESSED key-sorted `np.savez`, while stores serve `savez_compressed`. A strong validator needs a served-bytes digest. This is the known gap the owner ruled 2026-09-23 ("option 1 now, document the gap"). Sev L, Conf High.
     - `APD-DATA-055`: `DELETE /v1/datasets/{id}` does not evaluate `If-Match` (a stale tag still deletes; RFC 9110 §13.1.1), and `/batch-tags` ignores both headers. The PATCH concurrency is per host: Redis, Postgres and `CachedDatasetStore` hold only a per-process lock. It is documented by data#428, not fixed. Sev M, Conf High.
   - **Update the §2 counts.** `util/ad-hoc/register_open_set.py` must print `131 rows | 100 fixed | 31 open`, and `register_status_crosscheck.py` must AGREE.
     - "thirty filed" becomes thirty-five; "twelve are open" becomes sixteen.
     - "27 open in all, 15 primer + 12 post-primer" becomes 31 = 15 + 16. Append "and 12 → 16 on 2026-09-24".
     - §4.9's intro: "SEVEN rows below have a different provenance" becomes TWELVE; add a sentence for the five.
     - Run `tests/test_register_status_crosscheck.py`, `tests/test_register_open_set.py` and `tests/test_register_close_protocol.py`.
   - Close `APD-DATA-017/-029/-032` and `APD-CASCOR-008/-013` only AFTER their follow-ups and validations land. -013 needs the mixed-provenance fix.
4. **API primer** (`notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`): correct its checksum premise and its `immutable` prescription. `dataset_id` hashes the REQUEST, so the artifact is not content-addressed.
5. **Later arc items:** C-A (relaunch fresh; the killed forks cannot be resumed cross-session), C-B, C-C, D-C, D-D, D-E, D-F, D-G (048/049/051). **D-F collides with data#428** on `storage/base.py`: `update_tags(…, precondition)` and `InvalidDatasetIdError`.
6. **`MEMORY.md` compaction:** it is at the 24.4 KB read limit. The owner's target is 20 KB; retire entries, never strip hooks (`feedback_memory_index_target_is_20kb.md`). Other sessions edit it concurrently.

### Traps learned this round

- **The sweeper's arms store the DEFAULT squash body.** Put any waiver trailer (`Allow-Symbol-Loss:`) in a COMMIT body in the range; main-verify's MULTILINE regex finds it there.
- **A CHANGELOG built on a release cut BEFORE update-branch mis-files silently.** The 3-way merge duplicated `## [0.16.0]` with no conflict. The safe order is update-branch first, then push the corrected file.
- **Worktree-isolated sandbox refusals:** backticks inside a heredoc, `$(...)` feeding `gh` / `git`, variables in `git` / `tar` / `gh`, and loops around `git`. `--commit-body "$(cat f)"` to the pushers IS accepted.
- **Subagents die at the usage limit.** Resume them with `SendMessage` from the SAME session; a new session cannot.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -e mixed-provenance -e blank-key-678   # the two kept WIP worktrees
python3 util/ad-hoc/register_open_set.py | head -1          # 126 rows | 99 fixed | 27 open (before the register PR)
python3 util/ad-hoc/register_status_crosscheck.py | tail -1 # AGREE
gh pr list --repo pcalnon/juniper-cascor --head fix/shortfall-mixed-provenance-and-678-followups --state all
gh pr list --repo pcalnon/juniper-canopy --head fix/blank-key-678-followups --state all
gh pr view 435 --repo pcalnon/juniper-data --json state,mergedAt
```

## Git status at handoff

At wrap-up, the juniper-ml worktree `happy-skipping-hollerith` (branch `worktree-happy-skipping-hollerith`)
was at `f9c81d80` (= `origin/main`, 2026-09-24). Its only changes were this handoff and
`reports/2026-09-24_defect-register-round-42/`, which land together in one `docs(handoff)` PR opened
at wrap-up. The two WIP worktrees above are the only uncommitted work of this arc.

**Changed by the predecessor thread** (beyond the PRs): the memories `reference_contended_merge_lane_use_native_automerge.md` and `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`, and three `MEMORY.md` index hooks.
