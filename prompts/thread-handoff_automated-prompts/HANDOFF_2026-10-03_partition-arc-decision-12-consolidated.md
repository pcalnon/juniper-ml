# HANDOFF 2026-10-03 — Partition arc / Decision 12 spec (CONSOLIDATED): spec v3 is the next step; #431, #434, #212 and #2066 all merged, and #431/#434 shipped in juniper-data 0.16.0

**Consolidated sources**:

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-recorded-v3-next-three-prs-await-0-16-0.md`. This is the assigned source. It **declares no validation round**: it has no "Validation" line, and only its §5 caveats were checked by hand. Every claim in it that was not re-probed below is tagged `[UNVERIFIED — from HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-…md, which was not validated]`.
- **Required predecessor**, read in full and carried: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md`. It declares no validation round either.
- **Carried by reference**: §10.2 and §10.5 of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md`. The 09-23 handoff names that §10 as the arc's state of record. That §10 was validated in a consensus round, recorded in its §10.7.

**Supersedes**: `HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-recorded-v3-next-three-prs-await-0-16-0.md`. That file carries a SUPERSEDED banner. Its predecessors were already superseded by it and are not edited.

**Aliases used below**:

- **H-0909** is `HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md`.
- **H-0923** is `HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md`.
- **H-0924** is `HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-recorded-v3-next-three-prs-await-0-16-0.md`.
- **SPEC** is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`.
- **DESIGN** is `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`.

**Live probe**: 2026-10-03, approximately 05:00–05:30 UTC. Tools: `gh` REST/GraphQL, PyPI JSON, `git fetch origin` in this worktree, and read-only `cat`/`grep` of local worktrees.

**Documents referenced in this handoff** (each is named in full at every use):

- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`, the Decision 12 spec. It is on main at v0.2.0, with §14 (round 1), §15 (round 2) and an empty §16 ruling record.
- `reports/partition-provenance-spec-v2-review-2026-09-23/` (`README.md`, `S1-grounding.md`, `S2-soundness.md`, `S3-executability.md`, `S4-fold-completeness.md`), round 2's lane reports, archived verbatim.
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`, the design of record. Decision 12 rests on its §9.6.3 and §9.6.6.
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`, the plan. Its §9 holds the record-don't-re-edit precedent and its §10 the release record.
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`, which records V-2 as measured.
- The three handoffs above.

---

## Goal statement (paste as the new thread's first prompt)

```text
Continue the partition-arc residue / Decision 12 spec work in the Juniper ecosystem. Read
juniper-ml prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_partition-arc-decision-12-consolidated.md
in full first. It replaces the 09-23 and 09-24 partition-arc handoffs, so you do not need to open them.

Completed so far (all VERIFIED 2026-10-03 unless noted):
- Spec v1 (juniper-ml#2043, 8b8d5d94) was rated UNSOUND at review round 1. Spec v2 (juniper-ml#2060,
  0f269c2b, v0.2.0) folded all 14 round-1 findings. Review round 2 (four lanes, frozen at 8c9d65f)
  rated v2 NOT RATIFIABLE: ten MAJOR clusters, R2-1..R2-10, are recorded in §15 of
  notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md. The lane reports are under
  reports/partition-provenance-spec-v2-review-2026-09-23/. #2060's post-merge runs are all green.
- juniper-data#422 (stores conformed, ce436819), #430 (arc_agi 4.0.0, 90ad035e), #431 (notify-consumers
  waits for the consumer's run, 35b44cc1) and #434 (arc_agi review round, 3a76a4c5) are all merged,
  and ALL FOUR SHIPPED IN juniper-data 0.16.0. The tag is 39d1cab2, which is #435's fold commit, and the
  release has been on PyPI since 2026-09-24 18:35Z. #429, #427 and #411 are closed.
- juniper-data-client#212 (fail loudly on a failed dispatch, cabc40bf) closed #211. juniper-recurrence#185
  (the concurrency group keyed on version, ca9609f0) is merged. juniper-canopy#663 (advisory
  validate_npz_contract, cc3588a8) and juniper-cascor#672 (version single-sourced) are merged, and
  neither is released.
- juniper-ml#2066 (decision-4 pre-switch markers, f9c81d80) is merged. The juniper-ml#2034 step-1
  inventory, the V-3 plan on juniper-cascor#677, and round 2's outcome on juniper-data#423 are all posted.

Remaining work, in order:
1. [agent] Spec v3. Nothing has started: main still holds v0.2.0 and no branch exists.
   Fold §15 (R2-1..R2-10, then every MINOR and NIT, each traced to its lane id in the archived reports)
   into §1-§13, and add a round-2 disposition table in the style of §14. v3 must carry these decisions:
   (a) the release that carries the block is NOT 0.16.0, and is probably not 0.17.0 either (see
       Context, "R2-6 recurs"). Write the floor as "the first juniper-data release whose wheel emits the
       block", and pin the number only when it is cut;
   (b) W10's precondition is a juniper-recurrence RELEASE that carries W4's widened juniper-data-client
       cap, plus an `[all]` dry-run resolve;
   (c) W11 and FIRST_EMITTING_VERSION are conditional on OQ-1 = yes, and the "no" branch is written out;
       bump each generator's VERSION in the same PR as its emission, and fill W11 from W6's own
       verified list (R2-5);
   (d) drop the "0.6.1 is a PATCH" argument: release 0.7.0, or put the question to the owner in §16;
   (e) name the status, override and caveat surfaces per consumer, under both OQ-2 answers, and add
       a canopy line to §16 (R2-10);
   (f) restate S1-F3: recurrence main caps juniper-data <0.17.0 in [bench] (recurrence#188,
       2026-10-02, unreleased). PyPI 0.5.0 caps <0.12.0, in the bench extras only. S1-F3's <0.16.0
       described main at review time and is now stale.
   Update util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py with a vector per R2
   cluster, notably R2-1: an unknown scheme with a changed core must be `unverifiable`, not refused.
   Re-pin util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py to the current main heads.
   Then run review ROUND 3 with fresh lanes on frozen text. Only after that, ask the owner to rule (§16).
2. [agent] A juniper-data follow-up PR carrying #434's round-3 NITs. They were never committed: the
   strict exc_info assertions in juniper_data/tests/unit/test_cached_store.py, and the CHANGELOG
   /versions?name= wording, which now sits in the RELEASED [0.16.0] section, so word the fix as a new
   [Unreleased] note or drop it. The diff is still uncommitted in the #434 worktree; that branch is
   merged, so open a new branch from main.
3. [agent] juniper-ml#2064: surface eval_metrics.final (with its split and n_samples) in
   util/experiments/stats_summary.py (eval_scalars, ~:225) and plots_cascor.py (render_eval_metrics,
   ~:195), label the in-loop scores, and add tests. This unblocks #2034 step 3, the re-measurement,
   which must pin sizing_mode: carve. [ALSO P6: same util/experiments area]
4. [agent, gated on the perf lane being quiet] V-3 compute, following the plan on juniper-cascor#677.
   [ALSO P6]
5. [agent, optional] juniper-data-client follow-ups to #212: the comment should read "a later run in
   the receiver's concurrency group"; the three POSTs get a --max-time. juniper-data-client#213 is open
   and has no owner.
6. [agent, minor, not ticketed] Stale fallback __version__ literals (juniper-data, cascor-worker);
   recurrence data.py:69-77 promises ValueError, but a KeyError can escape from data-client's
   contract.py:72; cascor publish.yml's TestPyPI check imports from the checkout.

Owner-only (never do these; never approve deploy gates; merge approval is per-session, so ask again):
- **DONE 2026-10-03.** The owner widened the token. Verified the same day: notify-consumers run 37114403856 in juniper-data was green, and the `repository_dispatch` bench run it started in juniper-recurrence (37114410788) was green too. The original item follows, for context.
  Widen CROSS_REPO_DISPATCH_TOKEN (the PAT in juniper-data) to pcalnon/juniper-recurrence with
  Contents: Read and write, AND Actions: Read. #431's confirm step needs Actions: Read. 0.16.0's
  notify job got a 403 again on 2026-09-24. recurrence#178 is OPEN; close it once a release's own
  notify job and the bench run it starts are both green. [ALSO P4]
- Release cuts: juniper-cascor (ships #672), juniper-canopy (ships #663), juniper-data's next release
  (X8 (#437), #436, #438 and #440), and a juniper-recurrence release carrying the <0.17.0 cap. [ALSO P4]
- juniper-data#424: does DESIGN §6.2's generate-shortfall survive decision 9, or should canopy's
  disabled option be retired? canopy src/validation_gate.py:50 disables "Fill synthetically" pending
  the ruling. Also: close juniper-cascor#582, with #677 as its residue? After round 3, rule on spec
  ratification and OQ-1, 2, 3, 5 and 6.

Key context: see "Context the remaining work needs" in this file. Its traps are binding: negated
closing keywords, safe_merge exit 0, a release cut under an open PR, and freezing the artifact.
```

---

## Dependencies on other paths

- **P5 spec v3, item 1(a), depends on P4 (juniper-data releases).** juniper-data 0.16.0 is published `[VERIFIED 2026-10-03: PyPI JSON 0.16.0 uploaded 2026-09-24T18:35:40]` and carries no provenance block. The next data release will carry X8 (#437), #436, #438 and #440, which all merged after the tag commit `[VERIFIED 2026-10-03: data CHANGELOG on main]`. If P4 cuts it before W6 lands, the block-bearing release moves to 0.18.0 or later.
- **P5 owner item "widen CROSS_REPO_DISPATCH_TOKEN" is shared with P4**, where it gates Wave 4. The grant is pcalnon/juniper-recurrence with Contents: Read and write and Actions: Read (H-0924 §1). One owner action closes both. recurrence#178 closes only after a release's own notify job goes green.
- **P5 W10 (the meta-package floors) depends on P4's juniper-recurrence release.** The <0.17.0 data cap is only on recurrence main (#188, 2026-10-02). The client cap `juniper-data-client>=0.4.2,<0.6.0` is still on main `[VERIFIED 2026-10-03: recurrence pyproject on main]`. canopy main also still caps `juniper-data-client>=0.5.0,<0.6.0` `[VERIFIED 2026-10-03: canopy pyproject:192 on main]`.
- **P5 items 3–4 touch P6 (perf lane).** #2064 edits `util/experiments/`, which is in P6's residue area. V-3 compute must wait for P6's lane to be quiet, because the 09-23 plan on cascor#677 notes that PF-1 holds the box.
- **P5 owner release cuts (cascor #672, canopy #663) are P4's release-train items.**

## Context the remaining work needs

### Spec v3 inputs

- **The spec and its §15 are untouched since round 2** `[VERIFIED 2026-10-03: origin/main spec Version 0.2.0, 10 R2 rows, §16 all "—" except OQ-4]`. No v3 branch exists on origin `[VERIFIED 2026-10-03: git branch -r]`.
- The **R2 clusters** are verbatim in §15 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`. In short:
  - R2-1: G0 ordering breaks the unknown-scheme path;
  - R2-2: the schema_version increment rule was lost;
  - R2-3: class rows are keyed on name, not version;
  - R2-4: the store-prefix table is closed;
  - R2-5: the body decides OQ-1;
  - R2-6: 0.16.0 is taken;
  - R2-7: `[all]` is unresolvable;
  - R2-8: data CI installs the client from git main;
  - R2-9: the 0.6.1 PATCH argument;
  - R2-10: consumer status/override/caveat surfaces are unnamed.

  The MINORs and NITs, with lane ids, are listed in that §15. The full text is in `reports/partition-provenance-spec-v2-review-2026-09-23/S{1..4}-*.md`.
- **Store ids before and after 0.16.0 (bears on R2-4).** Until #422, only the generator route hashed `generator_version` into `dataset_id`. The stores built `hf-<name>-<rows>`, so every released wheel up to 0.15.0 behaves the old way. 0.16.0 is the first wheel with the stores on `generate_dataset_id` `[NOT RE-PROBED — from H-0923 Key context and H-0909 §10.4, validated by H-0909's §10.7 consensus]`.
- **R2-6 recurs.** Round 2 moved the block to "0.17.0" because #433 had taken 0.16.0. But juniper-data main already holds unreleased X8 (#437, equities_seq 6.0.0), #436, #438 and #440, both unrelated to the block, and the owner's release cadence is days. v3 should not hard-code 0.17.0, and a `>=X` floor must name a release whose wheel is proven to emit the block (read it from the wheel). This is a new observation from this consolidation; no round has reviewed it.
- **§11.2's data-client "0.6.0" still holds**: data-client PyPI is 0.5.0 `[VERIFIED 2026-10-03: PyPI JSON]`.
- **Pins for the citation checker**:
  - v2's pins: data `90ad035e`, data-client `9bc8870a`, cascor `f7a6d573`, canopy `894a2cc7`, recurrence `9b240253`, ml `c2bcb96c`;
  - main heads today: data `1c67f8d6`, data-client `0ec4b301`, cascor `b2921712`, canopy `58b467ca`, recurrence `be081fae` `[VERIFIED 2026-10-03: gh api commits/main]`;
  - the 09-24 source said cascor main moved at `0e016a7c`, shifting `manager.py` lines `[UNVERIFIED — from HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-…md, which was not validated]`. Re-pin to fresh heads in any case.
- **Reference-gate run** (the 09-24 source reports 52 PASS / 0 FAIL / 0 SKIP at data `90ad035e`) `[UNVERIFIED — from HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-…md, which was not validated; not re-run here, since no test runs are allowed in this consolidation]`. It runs in env `JuniperData` against the pin worktree `worktrees/juniper-data--verify--spec-v2-pin--20260923-1545--90ad035e`, which still exists `[VERIFIED 2026-10-03: ls]`.
- **What the reference gate cannot support**: it implements v2's text, not a shipped gate, and round 2 found defects (R2-1) that its vectors did not cover.
- **Process rules for the round** (owner precedent, from both handoffs):
  - freeze the artifact while lanes review it; the 09-24 thread broke this on #434 at 4e38930;
  - aim at least one lane at identity, versioning and legality;
  - record the findings in a new section, and do not re-edit the frozen text (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §9 precedent);
  - after a lane reports, re-read live state;
  - archive every lane report verbatim. Round 3 of the three PRs (lane D) was **not archived**; its findings exist only as summarised in H-0924. Those findings were: #434 MERGE, #431 MERGE-WITH-FIXES, #212 MERGE `[UNVERIFIED — from H-0924, which was not validated]`.
- **Mirror rulings and round outcomes on juniper-data#423.** Round 2's outcome is posted there, and v3's must be posted too.

### #434 residue (item 2)

- juniper-data main has **one** weak assertion: `assert warnings[0].exc_info is not None` at `test_cached_store.py:187` `[VERIFIED 2026-10-03: contents API on main]`.
- The #434 worktree `worktrees/juniper-data--fix--arc-agi-task-ids-unicode-429--20260923-1422--ce436819` still holds the uncommitted strict form at `:188` and `:238` (`exc_info and exc_info[0] is not None`, with a comment explaining why) `[VERIFIED 2026-10-03: grep of the worktree file]`. Its CHANGELOG wording says that `/versions?name=` returns every version, while `/latest` returns only the newest.
- According to the 09-24 source, the test file passes 30 tests and the four exc_info mutants are killed `[UNVERIFIED — from HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-…md, which was not validated]`.
- The trap: `exc_info=False` passes `record.exc_info is not None` (lane D's M09 mutant survived it).
- The third round-3 NIT, the unlocked warned-id set, was judged benign and left unfixed `[UNVERIFIED — from H-0924, which was not validated]`.

### Traps (binding)

- **A negated closing keyword still closes.** #185's "Neither closes #178" shut recurrence#178. The keywords are close, closes, closed, fix, fixes, fixed, resolve, resolves and resolved. A bare `#N` means the PR's own repo. Scan every PR body before merge (memory `reference_negated_closing_keyword_still_closes.md`).
- **`util/safe_merge.py` can exit 0 having refused** ("went BEHIND 3 times"). Read its log for `MERGED`. In a contended lane, arm native auto-merge (SQUASH, `commitBody` null, `--match-head-commit`), then run `update-branch` once.
- **A release proposal merged under an open PR moves that PR's `[Unreleased]` bullet into the released heading, with no conflict.** This happened twice in this arc: #433 under #431 and #434, and #428's duplicate `[0.16.0]` heading, which #435 folded. The ceremony now has `--target-sha` (juniper-ml#2071) `[VERIFIED 2026-10-03: ml main log]`.
- **The owner's PR sweeper merges and un-drafts unseen.** #431 and #434 were drafted to wait for the cut, and both merged within an hour (22:58Z and 23:22Z on 09-23). Both precede v0.16.0's tagged commit `39d1cab2` (#435, dated 08:14:12Z on 09-24; the Release was published 08:52:14Z), so they shipped in it `[VERIFIED 2026-10-03: compare API, both ancestors of 39d1cab2]`. Drafting is not a hold.
- **Rival implementations.** Check for an open or just-merged PR on the same issue before starting, and again before merging (H-0923 §4: recurrence#180 and data#425 lost to parallel recurrence#181 and data#426).
- **A PR body goes stale with every follow-up commit.** canopy#663's mutation and suite counts had to be re-patched before merge (H-0923 §4). Re-verify the body before merging item 2's PR and #2064's.
- **A red `Notify consumer repos` job follows every juniper-data release until the token is widened.** The `pypi` job, not the run, is the publish verdict (H-0909 §10.5).
- **Sequence Safety counts a same-file test rename as a LOST test.** Restore the name; do not rely on a waiver.
- **Headless commits**: a local commit hangs on YubiKey signing. Use `util/open_signed_pr.py` for a new branch and `util/push_signed_commit.py --expected-head <40-char sha>` for a follow-up. Build whole-file uploads from the BRANCH's current content, and diff each target from base to tip just before uploading.
- **canopy's CI unit lane has no juniper-data-client.** `src/tests/conftest.py` stubs it, so use a faithful fake plus an agreement test.
- **jq exits 0 on an empty body.** Use `jq -e` with a shape test.
- **A runner transient** (`git clone … server certificate verification failed`) looks like a PR failure. `gh run rerun --failed` fixes it.
- **The memory index is near its load limit.** Add a pointer only with an equal trim (`feedback_memory_index_target_is_20kb.md`).
- **"Merged" is not "released"**: #663 and #672 are on main only. `[VERIFIED 2026-10-03: PyPI canopy 0.8.1, cascor 0.11.0, both pre-merge]`

### Owner rulings in force (carried)

- **2026-09-22: conform the stores.** Implemented by #422.
- **2026-09-22: canopy runs `validate_npz_contract` as advisory only** (canopy#559 / #663).
- **2026-09-05: a downstream cap never lowers a SemVer bump** (cascor-client#155, canopy#584). This is the rule behind R2-9.
- **2026-09-24: #428, #431 and #434 fold into the one `[0.16.0]` section, with `[Unreleased]` left empty** (#435 body).
- **Decision 12 was ruled 2026-09-03 but is unspecified.** The owner asked on 2026-09-22 for it to be specified before it is built. OQ-4 is answered by #422; OQ-1, 2, 3, 5 and 6 are open.

### Evidence that cannot be over-read

- #422's stores ran only against mocked sources.
- #431's confirmation step has never run green in Actions. 0.16.0's notify job failed at the Dispatch step (403), so "Confirm the consumer started a run" was skipped `[VERIFIED 2026-10-03: job 107777269559 steps]`.
- The recurrence bench run 36046705575 (success, 2026-09-24T19:13Z) was a **manual replay** by the owner's account, not the sender `[VERIFIED 2026-10-03: run actor + P4 handoff HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-…md]`.
- V-3's "arm A = arm B's network" rests on reading the code `[UNVERIFIED — from H-0924 §5, which was not validated]`.
- The #2034 inventory is one agent's sweep; only two of its claims were re-checked `[UNVERIFIED — from H-0924 §5, which was not validated]`. One of them is T6's `split: "validation"` with no `final` block. The other is #2064's figures: 0.9187 in-loop against 0.8997 held-out.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch -q origin && git log --oneline -1 origin/main
git show origin/main:notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md | grep -m1 '^\*\*Version\*\*'   # 0.2.0 until v3 lands
git show origin/main:notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md | grep -c '^| \*\*R2-'         # 10
git branch -r | grep -i provenance        # only docs/partition-provenance-spec-v2 (merged) until v3 starts
# One plain gh command per item (a worktree-isolated session refuses loops over gh):
gh issue view 178  -R pcalnon/juniper-recurrence --json state --jq .state       # OPEN
gh issue view 423  -R pcalnon/juniper-data       --json state --jq .state       # OPEN
gh issue view 2064 -R pcalnon/juniper-ml         --json state --jq .state       # OPEN
gh issue view 677  -R pcalnon/juniper-cascor     --json state --jq .state       # OPEN
gh release list -R pcalnon/juniper-data --limit 2                               # v0.16.0 latest as of 2026-10-03
gh api "repos/pcalnon/juniper-data/contents/juniper_data/tests/unit/test_cached_store.py?ref=main" -H "Accept: application/vnd.github.raw" | grep -n exc_info   # one weak line until item 2 lands
grep -n exc_info /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--arc-agi-task-ids-unicode-429--20260923-1422--ce436819/juniper_data/tests/unit/test_cached_store.py   # the uncommitted strict form
curl -s https://pypi.org/pypi/juniper-data/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"   # repeat per package
# expected 2026-10-03: juniper-ml 0.10.0, juniper-data 0.16.0, juniper-cascor 0.11.0, juniper-canopy 0.8.1,
#                      juniper-data-client 0.5.0, juniper-recurrence 0.5.0
/opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py --data-checkout /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--verify--spec-v2-pin--20260923-1545--90ad035e | tail -1   # expect 52 PASS (unverified)
python3 util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py | tail -1   # 0 failures at the v2 pins
```

## Dispositioned / closed items

| item | source | disposition | evidence |
| --- | --- | --- | --- |
| Spec v2: fold round-1's 14 findings and run a fresh round | H-0923 item 1 | Done. v2 merged and round 2 recorded; v3 is now open item 1 | juniper-ml#2060 merged 0f269c2b `[VERIFIED 2026-10-03: GraphQL]` |
| juniper-data#429: arc_agi task_ids as unicode, plus a fleet allow_pickle=False test | H-0923 item 2 | Merged; #429 and #427 closed | #430 merged 90ad035e `[VERIFIED 2026-10-03: GraphQL]` |
| recurrence#178 gap 1: concurrency group per version | H-0923 item 3 | Merged | recurrence#185 ca9609f0 `[VERIFIED 2026-10-03: GraphQL]` |
| recurrence#178 gap 2: poll for the dispatched run after the 204 | H-0923 item 3 | Merged and released in 0.16.0. Never exercised green (token 403) | data#431 35b44cc1, an ancestor of v0.16.0 `[VERIFIED 2026-10-03: compare API]` |
| juniper-data-client#211: bare curl | H-0923 item 4 | Merged; #211 closed. Optional NITs are carried as item 5 | data-client#212 cabc40bf `[VERIFIED 2026-10-03: GraphQL]` |
| Merge data#431, then #434, only after the v0.16.0 cut | H-0924 item 2 | **Moot.** `[CHANGED SINCE HANDOFF: both merged 2026-09-23 (22:58Z, 23:22Z), before the cut, and shipped IN 0.16.0. #435's owner-ruled fold put their entries in [0.16.0]]` | GraphQL mergedAt; compare API; data#435 body |
| Commit and push #434's round-3 NITs before `gh pr ready` | H-0924 §3 | **Not done.** `[CHANGED SINCE HANDOFF: #434 merged at head ae5a3b18 without them]`. Re-scoped as open item 2 | main `test_cached_store.py:187` weak form; worktree holds the strict form |
| Merge data-client#212 | H-0924 item 3 | Merged 2026-09-23 22:30Z | GraphQL |
| Merge juniper-ml#2066; check #2060's post-merge run | H-0924 item 4 | Both done. #2066 merged f9c81d80. #2060's Post-Merge Main Verification run 35922423838 succeeded | GraphQL; `gh run list --commit 0f269c2b` `[VERIFIED 2026-10-03]` |
| juniper-ml#2034 step 1 (inventory) and step 2 (markers) | H-0923 item 5 / H-0924 §1 | Done. Step 3 (the re-measurement) waits on #2064 (item 3) | #2066 merged; #2034 OPEN |
| Release cut juniper-data 0.16.0 | H-0923 / H-0924 owner list | Done | PyPI 0.16.0 2026-09-24T18:35:40 `[VERIFIED 2026-10-03]` |
| Release cut juniper-ml 0.10.0 | H-0923 owner list | Done | PyPI 0.10.0 `[VERIFIED 2026-10-03]` |
| Re-run `notify-consumers.yml -f version=0.15.0` after the token is widened | H-0923 / H-0924 owner list | Superseded. The next release's own notify job is the test. 0.16.0's notify job got a 403 again, and the owner replayed by hand (run 36046705575, success). The token item stays open | job 107777269559 log; recurrence run API `[VERIFIED 2026-10-03]` |
| hf/kaggle stores conform (S-1) | H-0909 §10.2 | Merged as #422; released in 0.16.0 | PyPI and changelog `[VERIFIED 2026-10-03]` |
| canopy#559 advisory check | H-0909 §10.2 | Merged as #663; **unreleased**. The cut is carried as an owner item | GraphQL; PyPI canopy 0.8.1 |
| Rival-implementation check: look for an open or just-merged PR on the same issue before starting and again before merging | H-0923 §4 | A standing practice, carried into the traps | — |
| `docs/REFERENCE.md` and plan §10 updates once #422 merged | H-0909 §10.5 | Done in juniper-ml#2043 | H-0909 §10.5 `[NOT RE-PROBED — from HANDOFF_2026-09-09_…md, validated by its §10.7 consensus]` |
| V-2 | H-0909 §10.4 | Measured 2026-08-29 (+0.0088, 95 % CI [−0.0136, +0.0311]); only V-3 is owed | `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md` `[NOT RE-PROBED — from HANDOFF_2026-09-09_…md §10.4, validated by consensus]` |
| juniper-data-client#213 (dispatch runs cancelled by receivers' pushes) | H-0924 Completed | Correction posted; the issue is still OPEN with no work item. Carried in item 5 as "no owner" | GraphQL `[VERIFIED 2026-10-03]` |

## Git state

- **This worktree** (`.claude/worktrees/snappy-strolling-waterfall`, branch `docs/handoff-consolidation-2026-10-03`): this file, plus the banner on the 09-24 source. Nothing is committed.
- **juniper-ml `.claude/worktrees/warm-prancing-yeti`**: at `5c87a14c` on `docs/handoff-partition-arc-2026-09-24`. That branch's PR, juniper-ml#2095, merged 2026-09-26 as `5c3661e5` `[VERIFIED 2026-10-03: git worktree list; PR API]`. Its dirty state was not probed, since this session is git-isolated. It is a cleanup candidate only with an explicit merge signal, which #2095 provides.
- **juniper-ml `.claude/worktrees/rippling-wobbling-torvalds`**: at `ba035cc9`. It holds the 09-23 session's uncommitted copies of files that #2043 merged. It is a cleanup candidate, but check it first.
- **juniper-data worktrees**, all existing as of today `[VERIFIED 2026-10-03: ls]`:
  - `worktrees/juniper-data--ci--notify-consumers-confirm-run-started-178--20260923-1500--ce436819`: #431, merged. Cleanup candidate.
  - `worktrees/juniper-data--fix--arc-agi-task-ids-unicode-429--20260923-1422--ce436819`: #434, merged. It **holds the uncommitted item-2 diff**, so harvest that diff before any cleanup.
  - `worktrees/juniper-data--verify--spec-v2-pin--20260923-1545--90ad035e`: detached and read-only. **Keep it for v3's reference gate.**
- **juniper-data-client worktree** `worktrees/juniper-data-client--ci--notify-downstream-fail-loudly-211--20260923-1500--9bc8870f`: #212, merged. Cleanup candidate `[VERIFIED 2026-10-03: ls]`.
- **Remote branches still present on juniper-ml**: `docs/partition-provenance-spec-v2`, `docs/partition-arc-decision-12-spec-v1-and-09-09-reevaluation`, `docs/decision-4-pre-switch-markers` and `docs/handoff-partition-arc-2026-09-24`. All four are merged and none needs action `[VERIFIED 2026-10-03: git branch -r]`.
