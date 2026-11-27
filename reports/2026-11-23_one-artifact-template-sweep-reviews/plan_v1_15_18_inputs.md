# Inputs for plan v1.15.18 (collected by session ffffd3, worktree ethereal-munching-peacock)

## From session `r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next` [9660dc] (2222e504, worktree `curried-frolicking-boot`), received 2026-11-23 ~20:05Z

Verbatim substance of its message (it touches neither the plan nor any publish*.yml). Its handoff, landing in a juniper-ml
PR: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_r-obs-sc-2-owner-items-recurrence-pin-0-8-1-seven-worktrees-archived.md`.
Verify each claim against that handoff and `gh` before writing it into the plan.

The Overtoad ruled 2026-11-23: (1) "Six finished worktrees, data worktree + 4 branches"; (2) "Move it now" for deploy's
recurrence pin.

- juniper-deploy#284 pins juniper-recurrence 0.8.1 ("merging once green"). It closes plan v1.15.17 `:1166`/`:1256`'s
  "whether juniper-recurrence:0.8.0 … moves". Runtime unchanged (same lock and Dockerfile; the image still holds
  observability 0.4.1 and service-core 0.7.1). `--fail-on-stale` goes from exit 1 to exit 0.
- Removed after a file-by-file check against main: worktrees logical-percolating-sparkle, foamy-squishing-floyd,
  toasty-prancing-karp, agent-a4c8d9de35bfc0d67, buzzing-growing-whale, humble-humming-flask, plus the never-opened
  juniper-data worktree; and the cascor/canopy primaries' merged branches fix/fastapi-telemetry-opt-out and
  fix/rate-limit-retry-after-round-up. Each `tmp/` was MOVED to `juniper-ml/tmp/worktree-archive-2026-11-23/` (946 MB,
  README + manifests).
- NOT touched: giggly-foraging-sunbeam, sparkling-percolating-meadow, agent-a54a0a279acc3a863 (eligible since ml#2610,
  need the Overtoad's word), and ethereal-munching-peacock.
- The parent AGENTS.md backups (`juniper-ml/tmp/2026-11-1[45]-parent-agents-md-backup/`) had been rewritten by the blind
  pass; restored to their recorded sha256 (90df2783, f3f69b34, 3009c3f4), so the plan's "the parent's prior copy is safe"
  holds again.
- sentry-sdk 3.0.0 (2026-11-23 09:30Z) breaks `configure_sentry` when a DSN is set (`send_default_pii` removed; unknown
  options raise TypeError). ml#2608 caps it.

### Second message from [9660dc], received 2026-11-23 ~20:10Z

- A remaining-task inventory of the R-OBS-SC-2 arc is merging as juniper-ml#2619:
  `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`, 65 tasks with sources and lanes.
  - THIS lane: its group C, R28-R41.
  - Its group E (R58-R65): entries v1.15.17 holds open that are done or superseded; v1.15.18 should record them.
  - Its §4 "Gaps" items 1-9 are also this lane's.
- It notes (already known here) that cascor#772 merged from the rebuilt head `31136d64`, while
  `cascor-r3/work-after772` was built on `1e6e877a`: the pre-landing diff is where any difference shows. Fix pass 3's
  brief (`tmp/sweep/FIXPASS3_BRIEF.md`) already requires the base-B account against `work-after772`.

## From this arc (handoff `HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md`, item 4)

- The sweep PR, reviews 1, 2, 4 and 5 with fix passes 1, 2 and 3, the ports.
- SWEEP item 28 (`REVIEW_DISPOSITIONS.md` M5): the install check tests the tag's version; cascor's build has no
  tag==version assert; juniper-ml's assert step is the model.
- SWEEP item 29 (N6): the republish gate runs after the `pypi` approval.
- `jobs?filter=latest` VERIFIED (plan v1.15.17 already records it).
- cascor#772 merged 2026-11-23 19:35:14Z as `e9c86f83` (squash of head `31136d64`, not the `1e6e877a` round 3 tested).
- The three client rename PRs data-client#267, cascor-client#201, cascor-worker#234 merged 12:30Z with NO publish-file
  edits (checked 2026-11-23 ~20:00Z). data#547 MERGED 2026-11-23 20:39:16Z (`2ad7b7b5`, verified with `gh`): its only
  publish-area change is 2 person-rename docstring lines in `juniper_data/tests/unit/test_publish_one_artifact.py`
  (per the rename session 9d3fff65); no `publish*.yml`. Build the data port on data `main`, which carries it.
- The rename session's ml#2606 rebuild keeps `.github/workflows/publish*.yml` and `tests/test_publish_one_artifact.py`
  at main's bytes (disjoint from the ml port); it will message before arming/merging #2606; not uploaded yet (waits on
  flood-4 session 10's guard 1.4.0).
- The cascor sweep PR: juniper-cascor#777, opened 2026-11-24 ~00:30Z, head `a12b2c5f` on `36dd6f2d` (signed, verified;
  readback 11/11 same); fix-up `74971d3a` (three date lines, `--date 2026-11-24`, for the AGENTS.md Last Updated check);
  MERGED 2026-11-24 00:56:52Z as `f5ed3017` (verified, waiver in the squash message). Details:
  `tmp/sweep/REVIEW_DISPOSITIONS.md` § "Landed".
- Reviews: round 5 (1 MAJOR in the checker, 5 MINOR, 2 NIT; cascor's tree sound), fix pass 4 (the checker becomes a
  positive allow-list, `ebeb7556…`), round 6 (1 BLOCKER: a line continuation `$\`+newline hides a `$(…)`; a NUL byte
  likewise), fix pass 5 (`6b2443c6…`: continuations need an unescaped blank before the backslash, no NUL or
  non-printable characters, line checks on the build window too; 15/15 simulations, 289/289 proof), round 7 launched
  2026-11-24 ~02:30Z (report `tmp/r7review/ROUND7_REPORT.md`).
- The handoff: juniper-ml#2620, merged 2026-11-24 01:33:52Z (`ca976240`).
- An unattributed write under `/tmp`: `/tmp/vFI4WZy/` (created 2026-11-24 00:28:39.88Z), two byte-identical copies of
  juniper-ml's `.gitignore` named `4.1.1` and `5.1.1`. This session's `TMPDIR` was the repo's `tmp/`; none of
  open_signed_pr.py, push_signed_commit.py, the gate tools or wait_for_checks.py write that shape. Left in place as
  evidence; the owner's G-TMP rule says nothing writes there.
- juniper-ml#2632 (the technical-owner sweep) MERGED 2026-11-24 13:20:45Z (`c93914a7`); this lane held juniper-ml merges for its window. Its finding for the recurrence port (line 22 `Overtoad = pcalnon` -> `owner = pcalnon` in the three recurrence publishers) is recorded in `tmp/sweep/REVIEW_DISPOSITIONS.md`.

### From flood-4 session 11 [17d26a], received 2026-11-24 ~14:55Z (verify with gh before writing into the plan)

- juniper-ml#2635 MERGED 2026-11-24 14:51:35Z (`0a7c602c`): `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` §8 now runs to ruling 48 and records ruling 17 as one ruling over its four fixes (R54).
- Two plan lines go stale with it: `:120` ("§8 lists rulings 1-14" or similar) and `:1159` (the "what is left: §8 stops at ruling 14" sub-bullet under the ruling-17 finding). Fix both in v1.15.18.
- R55 = flood-4 ruling 48 landed as juniper-ml#2631 (`9a9ef3fb`): the paragraph check above `docs/REFERENCE.md`'s compatibility matrix.
- SWEEP item 28 (M5) gained a concrete path in round 10 (R10-7): with no tag==version tie, a 0.14.1 artifact left by an extra job could be published from a v0.14.0 run by 'Re-run failed jobs'. The checker now refuses extra jobs (fix pass 9), but the template-level tie is still deferred: record in v1.15.18.
