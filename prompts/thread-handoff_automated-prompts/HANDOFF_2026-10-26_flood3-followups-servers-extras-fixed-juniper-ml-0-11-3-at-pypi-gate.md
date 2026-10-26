# Handoff — Cursor flood-3 follow-ups: fixes delivered, juniper-ml#2062 fixed (ml#2333), juniper-ml 0.11.3 at the PyPI gate

**Date**: 2026-10-26 (UTC)
**Arc**: Cursor flood-3 disposition (2026-10-08) and the owner-requested follow-ups (2026-10-08 to 2026-10-26)
**Record of the arc**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, written `…FLOOD-3-DISPOSITION.md` below. Its §4 lists the defects, §8 the open items and §9 the files changed. juniper-ml#2352, which lands this file, makes its fifth update.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-10_flood3-followups-released-ci-tools-0-9-1-at-pypi-gate.md` (ml#2208), written `HANDOFF_2026-10-10_…gate.md` below. § Residue closes or carries each of its six items.
**Host**: the Linux host, session worktree `.claude/worktrees/enchanted-sniffing-popcorn`. Commits go only through GraphQL `createCommitOnBranch` (`util/open_signed_pr.py`, `util/push_signed_commit.py`); a local `git commit` hangs on the YubiKey.
**Validated**: in two rounds by five independent lanes. Round 1 used a rubric lane against `prompts/agent_templates/RUBRIC.md`, an adversarial fact-check and a fresh-session procedure audit. Round 2 checked what the rewrite broke and attacked the correction. Every finding was re-probed before it was applied (§ Validation).

---

## Goal

Continue the flood-3 follow-up arc. Everything the owner asked for is done except:

- **the juniper-ml 0.11.3 `pypi` gate** (publish run 40306687867), which only the owner approves;
- **after it publishes:** check the published metadata and record the release (Remaining work, item 2).

The open §4 defects in `…FLOOD-3-DISPOSITION.md` stay backlog; the owner has not asked for them.

The owner's last request in this arc, verbatim: "let's publish ml#2062 changes once 0.11.2 deployment is complete. then let's get an updated handoff prompt for this work arc, commit, push, PR, and merge it. merge approval granted." Their rulings for it (2026-10-25): ml#2062's fix is option "(a+) each server's own extras", and its version is "0.11.3, patch".

## Completed (verified on `main`, GitHub or PyPI)

- **Delivering the released fixes**: item 3 of `HANDOFF_2026-10-10_…gate.md`, requested by the owner on 2026-10-10. Their ruling was "cascor+data now; canopy/recurrence via W1.13", where W1.13 is a task in `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`. `…FLOOD-3-DISPOSITION.md` §8 "Delivered" has the detail. In short:
  - **Locks.** juniper-recurrence#199, juniper-canopy#739, juniper-data#478 and juniper-cascor#711 move only the two pins.
  - **Floors and releases.**
    - The floors rode juniper-data#479 and juniper-cascor#712, and canopy 0.9.0 through W1.13.
    - juniper-data 0.17.1 reached PyPI on 2026-10-23 at 23:49Z (juniper-data run 38084468369).
    - juniper-cascor 0.12.0 reached PyPI on 2026-10-25 at 18:13Z (juniper-cascor run 38085392643).
    - The owner approved both gates. The archives are juniper-ml#2215 and #2216.
  - **Images.** juniper-deploy#258 pins data 0.17.1 and cascor 0.12.0, beside canopy 0.9.0 and recurrence 0.8.0.
- **The meta-package floors.**
  - `[tools]`: juniper-ml#2314, in 0.11.1. Another session cut 0.11.1 (#2319, #2321); it reached PyPI on 2026-10-25 at 18:03Z.
  - `[servers]`: juniper-ml#2326 (squash `f823b0b7`; R-ML-SERVERS in §5 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`) floors `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1`.
    - The recurrence-arc session cut it as 0.11.2 (#2339, #2341). 0.11.2 reached PyPI on 2026-10-26 at 08:38:39Z, after the owner approved run 40247789317.
    - **The two security patches have reached `[servers]` since 0.11.0, through canopy 0.9.0's unconditional floors** (see § Corrections).
- **juniper-ml#2062 is fixed by juniper-ml#2333.** It squash-merged as `da5e8de3` at 2026-10-26 09:10:06Z, with option (a+), and did not ride 0.11.2.
  - `[servers]` is now:
    - `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`
    - `juniper-cascor[api,juniper-data]>=0.12.0`
    - `juniper-data[api]>=0.17.1`
  - Each client now comes from its server's own extra, inside that server's caps. `[api]` is the web runtime, and torch stays out.
  - data's own `[api]` floors now apply too; the same floor versions already arrived through canopy and cascor.
  - **Measured** with `util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash`:
    - against the published 0.11.1 and 0.11.2, JD-8, CC-2 and CC-3 SKIP, and canopy's `backend.service_backend` cannot be imported;
    - with the fix, all four pass.
  - **Re-cut after 0.11.2 published:** one signed commit, `98f86dd6`, on `2dceceec`.
    - It replays `util/ad-hoc/2026-10-25_servers_own_extras_ml2062.py` and is placed by `util/ad-hoc/2026-10-08_fleet_flood3_reset_pr_branch.py`.
    - Local regression: 224 of 225 suites pass. The failure is `tests/test_duplicati_scheduled_backup.py`, host-only because `/tmp` is tmpfs here.
- **juniper-ml 0.11.3** (a patch with no security content). The outcomes are in `…FLOOD-3-DISPOSITION.md` §8 and §9. The mechanics are in memory `reference_release_train_ceremony_traps_2026-09-09.md`, in its 2026-10-25 and two 2026-10-26 sections.
  - **Proposal ml#2349**, squash `a771a5b8`, 10:07:19Z.
    - Cut from `278c6139`. `detect.py --local-git` proposed the patch unaided.
    - Its co-change commit `b864b50b` comes from `util/ad-hoc/2026-10-26_juniper_ml_0_11_3_cut_cochanges.py`.
  - **Release `v0.11.3`**:
    - published 2026-10-26 10:20:47Z, with its tag at `a771a5b8`, and it is the repo's latest;
    - cut after that commit's `ci.yml` run 40304903536 went green;
    - its notes are one `### Fixed` section (#2062 and #2330), labelled PATCH.
  - **Archive ml#2350** (`notes/releases/RELEASE_NOTES_v0.11.3.md`) merged by its armed auto-merge at 10:31:48Z as `8b2221d3`. The archive on `main` matches the Release body (`diff -B`).
  - **Publish run 40306687867**: Build and Validate and Publish to TestPyPI succeeded, and Publish to PyPI is `waiting`. `pending_deployments` lists `pypi` (environment id 12341743943), and the ceremony's second `--execute` reported `PENDING_PYPI_APPROVAL`.
  - **Two `[Unreleased]` PRs were open at the cut.** Each was settled with its owner, a turing session, by message:
    - ml#2345 re-applied its entry under #2333's `### Fixed` and merged first (`278c6139`), so it rides 0.11.3;
    - ml#2346 reverted its CHANGELOG change until after the cut, then merged as `89f5af48`, with its entry under `[Unreleased]`.
- **Records:**
  - `…FLOOD-3-DISPOSITION.md`: its fifth update rides ml#2352, this file's PR.
  - The parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` RELEASED paragraph: its juniper-ml bullet now says 0.11.3 waits at the gate, #2333 is on `main`, and the patches reach `[servers]` through canopy (corrected).

## Remaining work

1. **Owner: approve the `pypi` gate of publish run 40306687867** (<https://github.com/pcalnon/juniper-ml/actions/runs/40306687867>).
   - Never approve it from a session, even though `current_user_can_approve` reads `true` (memory `feedback_deploy_approvals_paul_manages.md`).
   - The run was created at 2026-10-26 10:20:49Z. It can be re-run until 2026-11-25 10:20:49Z (day 30), and GitHub cancels it on 2026-11-30 10:20:49Z (day 35).
   - **Missing both deadlines does not lose the release.** `gh workflow run publish.yml --repo pcalnon/juniper-ml --ref v0.11.3` starts a fresh run (`publish.yml` has `workflow_dispatch` for this).
     - Its TestPyPI leg no-ops (`skip-existing: true`), and it waits at a new `pypi` gate.
     - A new version is needed only if PyPI took a partial upload.
2. **After it publishes.** The merge approval does not carry over (Key context), so a new session needs the owner's approval for any merge here.
   - Read the run's `Publish to PyPI` job as `success`.
   - Probe the version endpoint, `https://pypi.org/pypi/juniper-ml/0.11.3/json`, for 200. The project JSON and pip's index lag behind it: pip's index first served 0.11.2 to a 60-second poll at 08:51:38Z, 13 minutes after the upload.
   - Run the `requires_dist` check in § Verification. It must print exactly the three `[servers]` lines.
   - Optional re-measure: `PIP_NO_CACHE_DIR=1 bash util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash <workdir> 0.11.3`.
     - Its control venv installs the published `juniper-ml[servers]==0.11.3`, with CPU torch and `LD_LIBRARY_PATH` unset.
     - pip caches the simple index for 600 s (memory `project_pypi_cache_lag_post_publish.md`): disable the cache, or wait 10 minutes after the publish.
     - Expect the control's JD-8, CC-2 and CC-3 to PASS, and its CP-1 to read `backend.service_backend imported`.
   - Update the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` juniper-ml bullet: 0.11.3 is the latest, and #2062's fix is on PyPI.
     - Re-read the bullet first: peer sessions edit this unversioned file.
     - The recurrence arc's `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-published-plans-v1-7-20-v1-15-2.md` leaves the 0.11.3 records to this arc.
   - Update `…FLOOD-3-DISPOSITION.md` in three places, in one signed docs PR edited from a fresh `origin/main` worktree. The session worktree's copy is old.
     - the header `**Updated**` line, which says 0.11.3 "waits at the owner's `pypi` gate";
     - §8's "**Owner's:**" gate bullet under "Resolved (2026-10-26)";
     - §9: a line naming that PR.
3. **Backlog, unrequested.** This session fixed none of it and did not re-probe it. The authority is `…FLOOD-3-DISPOSITION.md`:
   - **§4**: its 14 rows whose status reads open (5), open (low) (8) or open (latent) (1), and the "Still open (low)" `claude.yml` header clause in its `ANTHROPIC_API_KEY` row;
   - **§8**: the "Not done, deliberately" `tests/test_service_fork_drift.py` guard, which first needs an `APD-` row in §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`;
   - also APD-ML-002, tracked in that same register.
4. **Cleanup, the owner's.** § Cleanup inventory lists every worktree and branch, and which ones to leave alone. Run it from each repo's primary checkout, and inspect each worktree before forcing its removal: most are dirty.
5. **Owner decision: errata to published release notes** (§ Corrections has the evidence). A Release body cannot be re-cut, but `gh release edit` can change it, and this arc used that command to fill placeholders. Nothing was edited here.
   - **juniper-ml 0.11.2 is security-relevant and under-warns.** Its Priority line reads: "upgrade every environment installed through `juniper-ml[servers]` without `[tools]`; `[tools]` and `[all]` already floor both patches, since 0.11.1". Its intro says "only juniper-cascor 0.12.0 floors them unconditionally".
     - In fact canopy 0.9.0 has carried both shared patches into `[servers]` and `[all]` since 0.11.0.
     - 0.11.2's real security content is cascor 0.12.0's **own** fixes: #689, #710, and `APIKeyAuth` checking every key.
     - An `[all]` install, or a `[servers]`+`[tools]` one, at 0.11.0 or 0.11.1 can still hold cascor 0.11.0. The notes tell those users they are covered.
     - The Medium rating and the CWE-201/755/770 list still hold, on that basis.
     - The text appears in the Release v0.11.2 body, `notes/releases/RELEASE_NOTES_v0.11.2.md` and `CHANGELOG.md`'s `[0.11.2]` entry.
     - The owner gave the 0.11.2 rating ruling ("Same as 0.11.1", 2026-10-25) while this session was reporting the false premise. The rating still holds, on cascor's own fixes.
   - **juniper-ml 0.11.3 is milder.** "which `[servers]` now applies for the first time" holds for data's own requirement, but reads as if the patch floors were new. It appears in `CHANGELOG.md`, the Release v0.11.3 body and `notes/releases/RELEASE_NOTES_v0.11.3.md`.
   - **juniper-ml 0.11.1 over-warns `[all]` users**, who gained nothing over 0.11.0. This is harmless.
6. **Not this arc's.** The recurrence arc's owner items, listed in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-published-plans-v1-7-20-v1-15-2.md`, stay with that arc. So do its plans' copies of the false claim; § Corrections lists them, and that session has been told.

## Corrections

**"Through 0.11.2, `[servers]` got the security patches only through cascor 0.12.0" was wrong.** This session wrote it on 2026-10-25, in ml#2326's body.
- **What is true:**
  - juniper-canopy 0.9.0 floors `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1` unconditionally (`requires_dist` with no extra marker).
  - juniper-ml `[servers]` has required `juniper-canopy>=0.9.0` since 0.11.0; 0.10.0 required `>=0.8.1`.
  - Besides canopy 0.9.0 and cascor 0.12.0, no member of `[servers]`, `[clients]`, `[worker]` or `[recurrence]` floors observability. juniper-recurrence 0.8.0 floors service-core.
- **Who caught it:** the round-1 rubric lane, which read canopy's `requires_dist`. A round-2 lane found every remaining copy.
- **Fixed by this session:**
  - the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md`;
  - `…FLOOD-3-DISPOSITION.md` (header, §4, and §8's fourth-update text);
  - memories `project_juniper_data_registry_needs_api_extra.md` (with its `MEMORY.md` line) and `project_recurrence_equities_p0_arc_2026-10-04.md`;
  - this file;
  - correction comments on ml#2326 (the origin) and ml#2333.
- **Left to the owner** (Remaining work, item 5): the published notes of 0.11.2, and more mildly 0.11.3 and 0.11.1, with the `CHANGELOG.md` entries that match them.
- **Left to the recurrence arc**, whose session was told on 2026-10-26:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, around lines 705 and 963;
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, around lines 922-923.
- **Left as history:**
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_recurrence-equities-servers-floors-landed-smokes-pass-0-11-2-cut-next.md`, line 42;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-published-plans-v1-7-20-v1-15-2.md`, line 50.

## Key context and traps

- **Merge approval.** The owner's "merge approval granted" (2026-10-25) covered ml#2333, the 0.11.3 proposal and archive, and ml#2352, this file's PR. It ended with this session. A new session needs the owner's approval for any merge (memory `feedback_headless_merge_approval_policy.md`).
- **Never approve a `pypi` gate from a session.** Never put a secret in argv.
- **A release cut under open `[Unreleased]` PRs** (memory `reference_release_cut_under_an_open_pr_changelog_automerges_silently.md`). Right before the proposal merges, every open PR touching `CHANGELOG.md` must have merged already, or carry no CHANGELOG change. The unsafe sequence is a re-cut before the proposal merges and a merge after it: update-branch then files the bullet under the released heading.
- **Re-cutting a PR onto a moved `main`.** Replay its apply script in a fresh `origin/main` worktree, then run `util/ad-hoc/2026-10-08_fleet_flood3_reset_pr_branch.py`. It makes one signed commit on a temporary branch, then force-moves the PR ref, guarded on the old tip. A whole-file upload onto a stale branch reverts `main`.
- **0.11.x cut mechanics:** memory `reference_release_train_ceremony_traps_2026-09-09.md` (2026-10-25 and 2026-10-26 sections).
  - Run `detect.py --local-git`; memory `reference_release_train_detect_repo_wide_feat.md` says why.
  - The release tools run without `python3 -I`, and need an explicit `--release-date`.
  - Run `ceremony.py --target-sha <proposal merge>` only after that commit's push CI is green.
  - Simulate first with `util/ad-hoc/2026-10-21_simulate_release_proposal.py`.
  - Preview the notes with `util/ad-hoc/2026-09-12_ceremony_notes_preview.py`. Pass it `--released-version`, or it labels the release MINOR.
  - Since #2333, cut scripts must strip extras markers.
- **Commit size** (memory `reference_signed_commit_api_499_on_large_payloads.md`). Split large uploads into commits of about 300 KB. After any 499 or 502, check the ref; a branch can exist at the base with no commit.
  - #2333's re-cut was one call of 1.62 MB raw (about 2.16 MB base64), with `docs/REFERENCE.md` at 1.07 MB, and it succeeded. That is one data point, and a single file that large cannot be split.
- **CP-1 is a defect probe.** It records PASS either way, so its text is the measurement. Its "(module omitted from the wheel)" suffix is hard-coded from canopy#631 and is wrong for canopy 0.9.0.
- **Worktree-isolated session limits vary by session; prefer plain single commands.**
  - Refused here:
    - `$(…)` and loops around `git` / `gh`;
    - an awk filter on `gh` output;
    - a `python -c` that runs `git`;
    - piping into `gh`;
    - `cd <shared checkout> && git …`;
    - `git -C` into sibling juniper-ml worktrees.
  - Allowed: `cd <centralized worktree> && git …`, `git worktree add|remove <literal path>`, `gh … --jq`, `grep -P` / `cut` on `gh` output, and small `python3 -I` pollers in the scratchpad.
- **The Cursor fleet keeps running**, by owner decision (`…FLOOD-3-DISPOSITION.md` §8). Docs PRs conflict by construction, so consolidation stays the default disposition.

## Verification

Run these first. If any output differs from its annotation, or a cited fact does not re-probe, stop and report it instead of proceeding.

```bash
git fetch origin
git log --oneline -5 origin/main
gh pr view 2333 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'   # MERGED da5e8de3db34…
gh pr view 2350 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'   # MERGED 8b2221d3e952… (the archive)
gh release view v0.11.3 --repo pcalnon/juniper-ml --json tagName,targetCommitish,publishedAt --jq '"\(.tagName) \(.targetCommitish) \(.publishedAt)"'   # v0.11.3 a771a5b86378418b16861a66f30247783a248382 2026-10-26T10:20:47Z
gh run view 40306687867 --repo pcalnon/juniper-ml --json jobs --jq '.jobs[] | .name + " " + .status + " " + (.conclusion // "")'   # Publish to PyPI: waiting until the owner approves
gh api repos/pcalnon/juniper-ml/actions/runs/40306687867/pending_deployments --jq '.[].environment.name'   # pypi (empty once approved)
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ml/0.11.3/json   # 404 until published, then 200
python3 -I -c "import json,urllib.request as u; r=json.load(u.urlopen('https://pypi.org/pypi/juniper-ml/0.11.3/json'))['info']['requires_dist']; s=[x for x in r if 'extra == \"servers\"' in x]; print(s); assert len(s)==3 and all('[' in x.split(';')[0] for x in s), s"   # after publish: exactly the three [servers] lines, each with its extras marker (0.11.2 fails the assert)
gh pr list --repo pcalnon/juniper-ml --state open
```

## Residue: the six items of `HANDOFF_2026-10-10_…gate.md`

Checked item by item against git, GitHub and PyPI on 2026-10-26:

1. **juniper-ci-tools 0.9.1's `pypi` gate**: closed. The owner approved it, and it has been on PyPI since 2026-10-21 21:53Z.
2. **The touch of `…FLOOD-3-DISPOSITION.md`**: closed, and since exceeded. ml#2315 was its third update, ml#2326 the fourth, and ml#2352 is the fifth.
3. **Delivering the released fixes**: closed (§ Completed).
   - The fixes it listed as "on `main` but in no release" have shipped: cascor#689 and #710 are ancestors of cascor's `v0.12.0` tag, and canopy `v0.9.0` compares key bytes.
   - canopy 0.9.0 and recurrence 0.6.0 shipped through W1.13 (in `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`) on 2026-10-17.
4. **The §4 backlog**: carried, with `…FLOOD-3-DISPOSITION.md` as the authority (Remaining work, item 3).
   - The "widen the `base64` row" instruction is done: the row names six repos.
   - So is "fix the five-touch wording" in §8.
5. **Cleanup**: still the owner's.
   - All 14 targets are still listed by `git worktree list`; the rubric lane found their HEADs unchanged.
   - `melodic-hugging-rabin` is now unlocked.
   - The optional `cursor/*` branches and the leave-alone worktrees are carried in § Cleanup inventory.
6. **ml#2190**: merged as squash `cad7f613` on 2026-10-10.

## Git status at handoff

- juniper-ml `main` will be at ml#2352's merge or later.
- **The session worktree, `.claude/worktrees/enchanted-sniffing-popcorn`**: local branch `worktree-enchanted-sniffing-popcorn` at `2a69b817`. Nothing is staged, and every change landed through the API.
  - Its modified `…FLOOD-3-DISPOSITION.md` is an old copy (ml#2315's blob `ae42ab26`). Never upload it.
  - Its three untracked `util/ad-hoc/2026-10-10_*` scripts are byte-identical to `main`'s.
- No remote branch or armed auto-merge of this arc remains once ml#2352 merges.
- Local branches that remain:
  - the session worktree's;
  - the ten `worktree-agent-*` branches of `HANDOFF_2026-10-10_…gate.md`'s targets, all at `d3971e10`, which its cleanup loop deletes.

## Cleanup inventory

- Run it from each repo's primary checkout; a worktree-isolated session cannot `git -C` sibling worktrees.
- 13 of this arc's 18 centralized worktrees are dirty, so `git worktree remove` will need `--force`. Inspect each before forcing (memory `reference_worktree_remove_deletes_ignored_files.md`).
- **The 14 targets of item 5 in `HANDOFF_2026-10-10_…gate.md`**, using its commands:
  - its ten-`agent-*` loop;
  - `agent-a621808cfbc0e59b3` and `agent-a8cedcf5971b0575b`;
  - `../worktrees/juniper-ml--flood3-docs-assembly--20261008`. It is dirty, with 9 staged and unstaged paths, so its command without `--force` will be refused. Inspect it first.
  - `melodic-hugging-rabin`, which is no longer locked, so use plain `git worktree remove --force`.
  - The validation lanes could not inspect the ten `agent-*` worktrees: the isolation guard refused `cd` into them.
- **This arc's centralized worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`.** All are detached, so there are no branches to delete. Their edits landed through the PRs named in `…FLOOD-3-DISPOSITION.md` §9; `juniper-ml--fix--servers-own-extras-2062--20261025-1658--fc65c2d7` holds #2333's first cut, which the re-cut superseded.
  - juniper-ml:
    - `juniper-ml--release-ceremony--20261010-1506--d14b86e5`
    - `juniper-ml--deps--meta-security-floors--20261023-1800--821003a5`
    - `juniper-ml--deps--servers-security-floors--20261025-1553--3ebf0689`
    - `juniper-ml--fix--servers-own-extras-2062--20261025-1658--fc65c2d7`
    - `juniper-ml--fix--servers-own-extras-2062--20261026-0340--2dceceec`
    - `juniper-ml--release--juniper-ml-v0.11.3--20261026-0410--da5e8de3`
    - `juniper-ml--release--juniper-ml-v0.11.3--20261026-0441--278c6139`
    - `juniper-ml--ceremony--v0.11.3--20261026-0507--a771a5b8`
    - `juniper-ml--docs--handoff-flood3-0-11-3--20261026-0523--89f5af48`: only after ml#2352 has merged, because until then it holds that PR's only local copy.
  - juniper-data:
    - `juniper-data--deps--shared-security-floors--20261010-1444--f13a83ee`
    - `juniper-data--release--juniper-data-v0.17.1--20261010-1520--96f26ca7`
    - `juniper-data--ceremony--v0.17.1--20261010-1532--381e660b`
  - juniper-cascor:
    - `juniper-cascor--deps--shared-security-floors--20261010-1444--3d49f0f8`
    - `juniper-cascor--release--juniper-cascor-v0.12.0--20261010-1530--9e7fdf3b`
    - `juniper-cascor--ceremony--v0.12.0--20261010-1545--41ea53e5`
  - juniper-canopy: `juniper-canopy--deps--shared-security-floors--20261010-1444--25c5c887`
  - juniper-recurrence: `juniper-recurrence--deps--shared-security-floors--20261010-1444--9f76fbfc`
  - juniper-deploy: `juniper-deploy--chore--pin-data-0.17.1-cascor-0.12.0--20261023-1739--11d7017b`
- **This session's worktree, `.claude/worktrees/enchanted-sniffing-popcorn`**, is locked to the session while it lives. Afterwards:
  1. Run `git worktree unlock` if it is still locked.
  2. Run `git worktree remove --force`.
  3. Run `git branch -d worktree-enchanted-sniffing-popcorn`; its head `2a69b817` is on `main`.
- **Optional, the owner's call:** the 91 `cursor/*` head branches of closed flood-3 PRs that `HANDOFF_2026-10-10_…gate.md` counted. The repos now hold more `cursor/*` branches from later floods, so today's totals are not comparable.
- **Leave these alone; they are not this arc's:**
  - `.claude/worktrees/agent-adf6f6f72c38b89d8`. The predecessor's other leave-alone worktree, `agent-a0cc83f337e9b068d`, is gone.
  - `juniper-canopy--control--pre-731-main--20261010-0600--4f69524b`;
  - `juniper-canopy--verify--pacer-731-merged--20261010-0600--25c5c887`, which shares its short hash with a cleanup target;
  - `juniper-canopy--fix--gitleaks-zero-rule-config--20261025-1604--afed03f0`;
  - `juniper-data--fix--gitleaks-zero-rule-config--20261025-1604--d4358fc1`;
  - `juniper-deploy--fix--gitleaks-zero-rule-config--20261025-1604--11aae789`.

## Documents created or modified

- **This final stretch:**
  - ml#2333: `pyproject.toml`, `tests/test_pyproject_extras.py`, `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`, `README.md`, `AGENTS.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `CHANGELOG.md`. New: `util/ad-hoc/2026-10-25_servers_own_extras_ml2062.py` and `util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash`.
  - ml#2349:
    - from `propose.py`: `pyproject.toml`, `CHANGELOG.md`, `README.md` and `AGENTS.md`;
    - from the co-change commit: `docs/REFERENCE.md` and `CHANGELOG.md`;
    - new: `util/ad-hoc/2026-10-26_juniper_ml_0_11_3_cut_cochanges.py`.
  - ml#2350: `notes/releases/RELEASE_NOTES_v0.11.3.md` (new).
  - ml#2352, this file's PR:
    - this file (new);
    - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, the fifth update: header, §4, §7, §8 and §9, including the canopy correction and §9's ml#2315 backfill.
  - Unversioned files on this host, with no history:
    - `/home/pcalnon/Development/python/Juniper/AGENTS.md` (the juniper-ml bullet);
    - memory files:
      - `reference_release_train_ceremony_traps_2026-09-09.md` (0.11.3 section);
      - `reference_release_cut_under_an_open_pr_changelog_automerges_silently.md` (0.11.3 section);
      - `project_juniper_data_registry_needs_api_extra.md` and `project_recurrence_equities_p0_arc_2026-10-04.md` (the canopy correction);
      - `project_pypi_publish_workflow_dual_gate.md` (a run past its deadlines is recoverable by `workflow_dispatch`);
      - `MEMORY.md` (one line).
- **Earlier in the arc:** every PR and file is in `…FLOOD-3-DISPOSITION.md` §9.
- **Referenced:**
  - `HANDOFF_2026-10-10_…gate.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-cut-parked-at-pypi-gate-plan-v1-7-19.md` (the 0.11.2 cut) and its successor `…-0-11-2-published-plans-v1-7-20-v1-15-2.md` (ml#2347);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`;
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).

## Validation

Each lane was told to refute, and none edited anything. The author re-probed each finding against PyPI, GitHub or git before applying it.

| Round | Lens | Result |
|---|---|---|
| 1 | Rubric R1–R5 (`prompt-validator`) | FAIL: 2 blockers (an unfilled marker; the false "patches only through cascor" claim), 2 major, 3 minor |
| 1 | Adversarial fact-check | No critical. The marker, the archive's stale status, the one-liner's fourth match, and 11 minor |
| 1 | Fresh-session procedure audit | Not ready: 6 major (marker, archive status, approval wording, record-touch scope, the one-liner, the backlog pointer) and 11 minor |
| 2 | What the rewrite broke | Ship with fixes: 2 major (the day-30 recovery claim; § Corrections missed the origin and 0.11.2's notes) and 7 minor |
| 2 | Attack on the correction | The correction is right but was incomplete. About 12 more copies, and 0.11.2's Priority line under-warns `[all]` |

**Applied.** Everything above, after re-probing:
- canopy 0.9.0's, recurrence 0.8.0's and juniper-ml 0.10.0–0.11.2's `requires_dist`;
- `publish.yml`'s `workflow_dispatch` and `skip-existing`;
- the new one-liner, against 0.11.2;
- §4's 14 open rows;
- worktree locks and the dirty count;
- cascor#689 and #710 as ancestors of `v0.12.0`;
- canopy `v0.9.0`'s byte compare;
- cascor 0.12.0's own security fixes in its Release body.

**Settled, not applied:**
- **"The simulator verdict on `278c6139` was not saved."** The author saw that run print "0 suite(s) regressed by the proposal".
- **Command refusals.** The lanes saw different refusals for the same command forms, so the trap now says refusals vary by session.
- **Length.** The goal statement (Goal, Completed and Remaining work) is about 1,430 words, above the ~1,200-word target of `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`; the document is about 3,500. Most of the excess is the owner's erratum decision. The cleanup inventory now has its own section.
