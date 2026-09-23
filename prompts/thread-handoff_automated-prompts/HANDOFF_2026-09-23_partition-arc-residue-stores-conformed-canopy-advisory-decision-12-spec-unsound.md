# Thread handoff: partition-arc residue. The stores are conformed, canopy's check is advisory, and the Decision 12 spec v1 is unsound at round 1

**Date**: 2026-09-23 ·
**Session**: <https://claude.ai/code/session_01WGFQ3uJtGMBygmuwxSSat4> ·
**Worktree**: `juniper-ml/.claude/worktrees/rippling-wobbling-torvalds` ·
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md`.
Its §10 is this session's full re-evaluation; the goal below does not repeat it.

**Documents REFERENCED** (more than one, so every reference carries its filename):

- the predecessor above, and its §10 in particular;
- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`, the Decision 12 spec. Its §14 holds review round 1's findings;
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`, the partition plan (§9 precedent, §10 release record);
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`, the design of record;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md`, the predecessor's first successor.

**Documents CHANGED** (all shipped in juniper-ml#2043):

- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`: new;
- `util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py`: new;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md`: header, and a new §10;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md`: a correction under its §8.4;
- `docs/REFERENCE.md`: the Decision 12 and hf/kaggle bullets under "What actually remains";
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`: a dated update after §10's "Still open" list;
- this file: new.

---

## 1. Goal for the next thread

```text
Continue the partition-arc residue in the Juniper ecosystem. Its state of record is §10 of juniper-ml
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md.
Read it first, then this file (HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md).

Completed (2026-09-22/23):
- juniper-data#422: the HF and Kaggle stores conform to decisions 11 and 7 (three partitions,
  VERSION 3.0.0, ids via generate_dataset_id, train-only scaling). Merged 2026-09-23 as
  ce436819, closing #411; not released. It is BREAKING
  for store callers: a lone train_ratio=0.9 now raises before any download.
- juniper-canopy#663: validate_npz_contract runs as a warn-only second check (canopy#559).
  Merged 2026-09-23 as cc3588a8, closing #559; not released.
- juniper-cascor#672 (version single-sourced) and juniper-recurrence#179 (bench caps <0.16.0):
  both merged.
- The Decision 12 spec v1, notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md,
  published in juniper-ml#2043. Review round 1 rated it UNSOUND as written. Its §14 records 14 unfolded
  findings: B-1..B-7 and R-1..R-7, with blockers B-1, B-2, B-3 and R-1.
- Filed: juniper-data#423 (Decision 12), #424 (the §6.2 shortfall), #429 (arc_agi unloadable);
  juniper-ml#2034 (decision 4); juniper-cascor#677 (V-3); juniper-data-client#211 (bare curl).

Remaining, agent-doable (merge approval is per-session: ask the owner for it again):
1. Spec v2. Fold §14 into §1-§13 of the spec, then run a FRESH consensus round on v2. Freeze the
   artifact while the round runs, and aim at least one lane at identity/versioning/legality.
   Do not ask the owner to rule on OQ-1..OQ-6 until v2 survives.
2. juniper-data#429. Store arc_agi's task_ids as np.str_, and add a fleet test that loads every
   generator's artifact with np.load(allow_pickle=False). Bump arc_agi's VERSION to a target that
   does not collide with the spec's §7.3 (see §14 R-4). cached.py's contextlib.suppress swallows
   the error today (see the comment on #429).
3. juniper-recurrence#178's residual gaps: key the concurrency group by the dispatch payload
   version, and poll for the dispatched run after the 204.
4. juniper-data-client#211: replace the bare curl -X POST with curl --fail-with-body.
5. juniper-ml#2034 (decision 4 re-baseline) and juniper-cascor#677 (the V-3 measurement).

Owner-only (never do these, and never approve deploy gates):
- Release cuts: juniper-cascor (ships #672), juniper-data (ships #422, BREAKING for stores),
  juniper-canopy (ships #663), juniper-ml 0.10.0 (ships #2033).
- Widen CROSS_REPO_DISPATCH_TOKEN (the PAT in juniper-data) to pcalnon/juniper-recurrence with
  Contents: Read and write. Run 35808713744 got a 403. Then re-run
  `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.15.0`.
- juniper-data#424: does §6.2's generate-shortfall survive decision 9?
- Close juniper-cascor#582, with #677 as its residue?

Key context:
- A local git commit hangs on YubiKey signing. New branch: util/open_signed_pr.py. Follow-up
  commit: util/push_signed_commit.py --expected-head <FULL 40-char sha>. It was promoted out of
  util/ad-hoc/ on 2026-09-23, and it refuses a short sha. Build a whole-file upload from the
  BRANCH's current content, or it reverts other PRs' CHANGELOG entries.
- canopy's CI unit lane has NO juniper-data-client. src/tests/conftest.py injects a stub, so a
  test that imports a client helper passes on this box and fails in CI. Use a faithful fake plus
  a fake-versus-real agreement test that skips with a reason. Simulate the lane locally with an
  import shim on PYTHONPATH.
- Until #422, only the generator route hashed generator_version into dataset_id; the stores have
  done so since #422 (on main, unreleased). That is why the 09-12 claim "the floor protects by
  accident" was false when it was written, and why every released wheel up to 0.15.0 still
  behaves the old way.
```

## 2. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch -q origin && git log --oneline -1 origin/main
gh pr view 422 --repo pcalnon/juniper-data   --json state,mergedAt --jq '"\(.state) \(.mergedAt)"'
gh pr view 663 --repo pcalnon/juniper-canopy --json state,mergedAt --jq '"\(.state) \(.mergedAt)"'
gh issue view 178 --repo pcalnon/juniper-recurrence --json state --jq .state          # OPEN until the token is widened
gh run list -R pcalnon/juniper-recurrence --event repository_dispatch --limit 1      # empty until then
git show origin/main:notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md | grep -c '^\*\*B-[1-7]\.\|^\*\*R-[14]\.'   # 9 detail headings in §14
for p in juniper-ml juniper-data juniper-cascor juniper-canopy; do printf '%s ' "$p"; curl -s "https://pypi.org/pypi/$p/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"; done
# expected until the owner cuts releases: juniper-ml 0.9.0, juniper-data 0.15.0, juniper-cascor 0.11.0, juniper-canopy 0.8.1
```

## 3. Git status at handoff

- Branch `worktree-rippling-wobbling-torvalds`, based on `origin/main` `ba035cc9`. Nothing is committed locally: every change shipped through API-signed PRs.
- The working tree still shows this session's edits to the files listed under **Documents CHANGED**, as uncommitted modifications. They are identical to what juniper-ml#2043 merged. Three new files (the spec, its script and this handoff) were added to the index with `git add -N` (intent to add) so pre-commit would see them.
- Scratch (session-local, disposable): `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ca1055b2-4023-4eac-827c-b44baf9a2861/scratchpad/`.

## 4. Traps this session hit

- **Rival implementations.** recurrence#180 and data#425 were written in parallel with another session's recurrence#181 and data#426, which merged first. Check for an open or just-merged PR on the same issue before starting, and again before merging.
- **A PR body goes stale with every follow-up commit.** Both code PRs' bodies were re-verified and patched before merge: canopy#663's mutation count went from 8 of 9 to 8 of 10, and its suite count from 177 to 178.
- **A found defect can change a spec's ground truth under review.** F-2's fix in #422 made the spec's §5.3 store row stale while the review round was still running (§14 B-1). Record it; do not silently re-edit the frozen text.
- **A target file moved on `main` while the session worked.** `docs/REFERENCE.md` gained 15 lines (the `push_signed_commit.py` docs) between the worktree base `ba035cc9` and the upload. It was rebuilt from the tip before the whole-file upload. Diff every target path from base to tip immediately before uploading.
- **State can move during a validation lane.** #422 merged while lane H1 was running, so the lane reported every "once #422 merges" line as stale. After a lane reports, re-read live state, not only its findings.
- **"No end-to-end run" and "an end-to-end run failed" are different facts.** The 09-09 §10 said the first until another session's 403 comment on recurrence#178 was read.

## 5. What this evidence cannot support

- **#422's stores ran only against mocked sources.** No real Hub or Kaggle download ran.
- **The spec's script passes (15 PASS) exercise encoding, digest and tamper detection.** They say nothing about §14's defects, which are in gate logic that exists only as prose.
- **"Merged" is not "released".** None of #422, #663, #672 or #2033 is on PyPI until the owner cuts the releases.
