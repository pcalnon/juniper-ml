<!-- markdownlint-disable -->
# Round 1, lane A1

**Entry point:** the GitHub API only.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T19:54:39Z to 2026-09-22T20:16:59Z, read-only. Agent `agent-ab67cf757891b6f8f`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are Lane A1 (measurement re-creation) in an independent-agent consensus review. Your entry point is the GitHub API ONLY (`gh api`, `gh pr view`, `gh run`, GraphQL). Do NOT trust prose; re-derive every value yourself from the API. "UNTRACEABLE" and "NO ARTIFACT" are allowed, expected answers — never reconstruct a value from the narrative. Default to REFUTED or UNTRACEABLE when you cannot re-derive a claim.

READ-ONLY RULES (hard): do not edit, create or delete any file in any repo; do not commit, push, comment on, merge, close or approve anything; do not approve deployments. The session is worktree-isolated: do NOT run `git` against any repo other than the juniper-ml worktree below (the harness refuses it). Use `gh`, `curl`, `python3`, `cat`, `grep`. Put any downloads under /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a1/ (create it). The harness refuses shell loops over variables that touch `gh`/git; write one plain command per repo, or put GraphQL in a file and use `gh api graphql -F query=@file`.

THE ARTIFACT: in the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl read
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`, specifically the new header lines (`**Successor**`, `**Status**`) and the section `## Status banner (added 2026-09-22 ...)` down to `## Handoff goal`, plus four short in-place notes marked 2026-09-22 further down (run `git diff` in that worktree to see exactly what was added; the tree is frozen for this review). The `__VALIDATION_RECORD__` placeholder is intentional. Also read the two in-place SHA corrections in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` (see `git diff`).

YOUR JOB:
1. For EVERY factual claim in the banner's table and its "Corrections to this document" section that GitHub can answer — PR numbers and their merge state/merge commit SHAs/merge dates (e.g. canopy#619 a5cbdcd1, cascor#645 63a29e87, cascor#646 merge 43785fe0 vs head b374f285, ml#1909 4f566d37, deploy#215/216/217/219/220/221/225/226, worker#192/#193, data#420, canopy#649/#585, ml#2007/#2009), the claim "Every merge SHA in that section matches the PR's mergeCommit.oid (22 PRs re-read)" (re-read the ORIGINAL "What shipped" section's SHAs and check each one yourself), run IDs (34579752944, 34461928708, 34588125830 + job 103226938997, 35604787525), release dates (canopy v0.8.0/v0.8.1, worker v0.6.0, deploy v0.3.0), the `dockerhub` environments (existence in the five image repos juniper-cascor / juniper-data / juniper-canopy / juniper-cascor-worker / juniper-recurrence, created_at, tag policies, zero secrets), absence of DOCKERHUB_* repo secrets, cascor-client lockfile-update.yml total runs = 0, the two client repos having no requirements.lock at main, signed commit d7b5ea1f on cascor#664, the "eight ceiling PRs merged 2026-09-11 between 01:32 and 01:52 UTC" date claim, the X7 test facts (`test_initialize_sync_does_not_block_the_loop`, STALL_SECONDS, unchanged since canopy#585; canopy#649 touched a sibling test) — re-derive it and report CONFIRMED / REFUTED / PARTIAL / UNTRACEABLE with the command and an output excerpt.
2. EXECUTE every command in the banner's "### Verification commands (use these, not the goal's)" block exactly as written (from /home/pcalnon/Development/python/Juniper), and report for each: did it run as written (quoting/jq errors?), and does its real output match the stated expected value in its trailing comment? A command that errors or whose output differs from its comment is a finding. (The census script there downloads repo tarballs through the API; it is expected to exit 1 right now — report what it prints.)
3. Instrument adequacy: for each "zero"/"absent"/"never" claim, say whether your probe could have produced a non-zero answer (e.g. does `total_count` on a workflow's runs endpoint really cover all history; does a git tree listing at main prove no lock file exists anywhere).

OUTPUT (your final message is the only thing returned): a numbered findings list; each item = quoted claim, verdict, severity (CRITICAL / MAJOR / MINOR / NONE), evidence (command + short output). Then a one-paragraph overall verdict (PASS / PASS WITH FINDINGS / FAIL). Be terse; no preamble.

## Final report

**Lane A1 findings for `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` (the banner) and `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` (the successor)**

Every value below was re-derived from `gh api`, GraphQL, anonymous GHCR `tags/list`, PyPI JSON, or a local `ls`/`ping`. Nothing is taken from either document's prose.

1. **"`python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` … exits 1"** (the banner's first verification command). **REFUTED as written. MAJOR.**
   - Running it from `/home/pcalnon/Development/python/Juniper` gives `can't open file …/juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py: [Errno 2]` and exits 2.
   - The script is not on `main` (contents API returns 404). It exists only as an untracked file (`??`) in `jolly-wibbling-pearl`, so the banner's PR must add it.
   - Run from the worktree path, it matches its comment. It exits 1 and prints `live pins: 54`, `distinct live ranges: {'<0.10.0,>=0.9.0': 54}`.
   - It names 7 stale doc lines: ml `docs/REFERENCE.md` lines 3754, 6392 and 7072; ml `util/fleet_triage/predict_merge.py` lines 57, 180 and 234; canopy `AGENTS.md` line 517.
   - The worktree diff plus canopy#655 fix all 7. Re-scanning the fixed worktree files finds nothing stale, so "after both it should exit 0" holds.

2. **"The worker's (#180) has not [run], because none of its recent Dependabot PRs is a pip update."** (Corrections 2). **REFUTED. MAJOR.**
   - The worker's `lockfile-update.yml` also triggers on `pull_request: paths: [pyproject.toml]`.
   - It has run 4 times since #180 merged. Two of those runs made verified signed commits:
     - `695d64e8` at 2026-09-11 22:45:34Z (`verified: true`). It is the **head** of worker#184, which merged: `gh pr view 184` → `bee7b86aa3a3 head=695d64e8939c`.
     - `bca33c99` at 2026-09-22 19:44:46Z (`verified: true`), on open worker#194.
   - Evidence: `…/jobs/103446457642/logs` → `Signed lockfile commit: …/695d64e8…`.
   - The premise holds (0 Dependabot pip PRs), but that probe cannot see the `pull_request` trigger.

3. **"canopy#619 and cascor#645 are listed without SHAs"** and **"22 PRs re-read"**. **PARTIAL. MINOR.**
   - All 20 SHAs in "What shipped" match `mergeCommit.oid`: 615 436fe87d, 642 cc0d1630, 160 033fc9a1, 181 dcafd220, 392 4d072da7, 196 dcdd2c78, 209 6eaec040, 166 aff3860d, 1891 81a5fe21, 163 0e1b6971, 183 cb6e171f, 394 20cd6788, 199 534b7999, 211 5f2c1116, 168 c6367c92, 1897 18d21a8c, 165 bea3dfb, 161 1b8c337c, 197 cf73c884, 1888 1b31df7d.
   - The missing SHAs a5cbdcd1 (canopy#619) and 63a29e87 (cascor#645) are also correct.
   - The section cites 23 PRs, not 22. ml#1869 is also SHA-less (merge `ee57a892`, 2026-09-10 00:55Z), and the banner does not mention it. Its "13 lines" claim is confirmed: 13 widened workflow pins across 10 files.

4. **"§ What shipped … CONFIRMED"**, as it covers "47 pin lines across 26 files per pass, both passes identical". **PARTIAL. MINOR.**
   - Counted from the PR patches, the ceiling pass is 47 lines across 30 files. Of those, 43 lines sit in 26 workflow files and 4 in `AGENTS.md`.
   - The floor pass is 50 lines across 31 files; it adds 3 lines in cascor's test file.
   - So "47 across 26" pairs a line count and a file count from different scopes. The two passes are identical only for workflows (43 lines / 26 files each).

5. **Table row: "…the same class in two more places, now fixed too"**. **REFUTED as of review. MINOR.** canopy#655 is `OPEN` and the juniper-ml fixes are uncommitted. The census on remote `main` still flags all 7 lines, which the banner's own verification comment admits. The claim that worker#193 fixed its docs is **CONFIRMED** (merged 2026-09-22 18:59Z; `>=0.6.0,<0.7.0` → `>=0.9.0,<0.10.0` in `docs/REFERENCE.md` and `DEVELOPER_CHEATSHEET.md`).

6. **"None of it comes from a local checkout"**. **PARTIAL. MINOR.** The worktree-debris row and the turing / binfmt / yamaguchi facts come from local-host probes. The worktree listing is literally a listing of local checkouts.

7. **Census instrument coverage.** **MINOR, latent.**
   - It reads only its text suffixes (`TEXT_SUFFIXES`), so it never reads `.lock` files, `Dockerfile*` or `Makefile`, even though `LOCK_RE` targets `requirements*.lock` and the banner says it sorts "lock pins".
   - Its specifier regex (`SPEC_RE`) needs a version, so an unpinned install is invisible to it.
   - A supplementary probe of 20 such files across 6 repos found no `juniper-ci-tools` mention, and no workflow has an unpinned install. The "54 live pins" result therefore stands today.

8. **The verification block under-tests its own claims.** **MINOR.**
   - It probes the `dockerhub` environment of 1 repo, not all 5, and never checks repo-level secrets.
   - `ls … | wc -l` counts 8 of the 15 worktrees.
   - The two `git/trees` commands ignore `.truncated`. That is harmless here: `truncated:false`, and a case-insensitive `lock` search finds only the workflow file and a test file.

9. **The goal's "items 1, 3, 4, 5 and 7"**. **PARTIAL. MINOR.** The table has no row for this document's own item 1 ("first publish in recurrence and canopy"). It is closed in fact: GHCR has canopy 0.8.0 and 0.8.1 and recurrence 0.5.0. The banner's only "item 1" is the tip handoff's re-scoped item, which uses different numbering.

10. **Verification commands 2–9, run exactly as written.** All ran with no quoting or jq errors, and each output matches its comment. **NONE.**
    - Log grep → `Successfully installed juniper-ci-tools-0.9.0 packaging-26.3`
    - Both client tree listings → `[]`
    - cascor-client lockfile runs → `0`
    - d7b5ea1f → `true`
    - cascor `dockerhub` secrets → `0`
    - cascor#646 → `43785fe0 b374f285`
    - Ceiling worktrees → `8`

11. **Corrections 1: "returned 23: 21 comments and 2 live … ci-cascor-model.yml:94, ci-protocol.yml:67 `>=0.6.0,<0.7.0`"**. **CONFIRMED. NONE.**
    - I re-ran both greps over every workflow file on remote `main` as of 2026-09-11 19:49Z and 22:20Z. grep1 gives 0; grep2 gives 23 (21 comment lines plus those exact 2 live pins).
    - Caveat: this reconstructs remote `main`, not the author's local checkouts.
    - The fan-out helpers' regexes do match only `<0.9.0` and `<0.10.0`.
    - cascor#646's diff is exactly the two pins plus one `AGENTS.md` line.
    - "25 of 54 live pins": the pre-#1909 guard's files held 25 of the 54 live pins. After #1909 it globs every `*.yml` across 8 consumer repos.

12. **The successor's SHA corrections.** **CONFIRMED. NONE.** `.mergeCommit.oid[0:12]` → `43785fe0428e`, and `headRefOid` is `b374f285d173`. No `b374f285` remains in any handoff. The successor's other SHAs are also correct: 1909, 1910, 620, 184.

13. **Corrections 2, client repos.** **CONFIRMED. NONE.**
    - data-client run 35604787525 (a dependabot push, 2026-09-21) logged `##[notice]No requirements.lock to commit — skipping.`; that workflow has 48 runs.
    - The cascor-client workflow (id 267109918, active since 2026-04-27, push-only trigger) has `total_count` 0. All 61 of its Dependabot PRs ever are `github_actions` updates.
    - Its commit step uses `git diff --quiet`, which ignores an untracked file, so "cannot execute" holds. The PAT is present in the Dependabot secret store.
    - The endpoint can return non-zero (it gives 48 for data-client). Manually deleted runs would be unobservable.
    - cascor d7b5ea1f is confirmed: exact message, `verified` / `valid`, 2026-09-21 22:32Z. `commits/d7b5ea1f/pulls` → #664, and run 35662982649 logged `Signed lockfile commit: …/d7b5ea1f…`.

14. **Corrections 3: "eight ceiling PRs merged 2026-09-11 between 01:32 and 01:52 UTC"**. **CONFIRMED. NONE.** The range is 209 at 01:32:15Z to 615 at 01:52:28Z. ml#1869 is the exception: it merged 2026-09-10 in UTC.

15. **The floor-bump CI evidence.** **CONFIRMED (one repo, one job). NONE.**
    - Run 34588125830 was a push to `main` at `bbdcbb6a`, 10:13:11Z, and succeeded.
    - Job 103226938997, "Documentation Links", belongs to it. Its log has `pip install "juniper-ci-tools>=0.8.0,<0.10.0"`.
    - 0.9.0 was published at 08:33Z, and cascor#645 merged at 19:44:57Z, 9h31m after the run. Log retention is 90 days.

16. **Runs, releases and GHCR.** **CONFIRMED. NONE.**
    - Runs: 34579752944 finished with 3 of 3 jobs successful; 34461928708 likewise.
    - Releases:
      - canopy v0.8.0 published 2026-09-12 21:50Z; v0.8.1 published 2026-09-18 00:38Z.
      - worker v0.6.0 Release published 2026-09-15 22:59Z. Its PyPI publish finished 2026-09-18 00:18Z (the upload is at 00:18:32Z).
      - deploy v0.3.0 published 2026-09-17 00:11Z.
    - GHCR tags: cascor 0.11.0; data 0.14.0 and 0.15.0; canopy 0.8.0 and 0.8.1; worker 0.6.0; recurrence 0.5.0.

17. **The deploy row.** **CONFIRMED. NONE.**
    - #215, #216, #217, #219, #220 and #221 merged between 2026-09-16 00:30Z and 2026-09-17 00:16Z. #217 adds the job `name: Published Image Refs`.
    - #225 is merged. #226 makes staleness a `::warning::` by default, with `--fail-on-stale` optional.
    - #227 is OPEN (created 2026-09-22 19:43Z), and compose on `main` still pins `juniper-data:0.14.0`.
    - No artifact shows #226's check actually flagging data 0.15.0: no `main` run has happened since 18:55Z.

18. **Items 3, 5 and 7.** **CONFIRMED. NONE.**
    - `dockerhub` exists in exactly the five image repos. Created 19:45:59Z–19:46:21Z; each has only the tag policies `v*` and `juniper-*-v*`; each holds 0 secrets.
    - No `DOCKERHUB_*` secret exists in any of the 9 repos' Actions secrets or in any environment.
    - ml#2007 added the procedure note, and ml#2009 recorded "§3 RULED 2026-09-22: Option B".
    - The plan says "OQ-1 — RULED 2026-09-11" and records the Pi-pull waiver on 2026-09-15 (§5.1).
    - At worker tag v0.6.0 the lock header pins `torch==2.14.0+cpu` and `__version__ = "0.4.0"`. worker#192 is 6 commits ahead of that tag.
    - data#420 merged after the v0.15.0 tag (1 commit ahead). The PyPI 0.15.0 wheel has 201 members, 97 of them under `tests/`.
    - Local checks: this host is x86_64 and named `yamaguchi`; `binfmt_misc` has only python handlers; `192.168.50.222` has 100% packet loss.

19. **The X7 test and the worktrees.** **CONFIRMED. NONE.**
    - The test lives in `src/tests/regression/test_x7_sites_outside_main_gate.py`, with `BLOCK_SECONDS = 0.4` and `STALL_SECONDS = BLOCK_SECONDS * 0.5`. That file's only commit on `main` is 5a2f982a (#585, 2026-09-05).
    - canopy#649 touched only `test_x7_loop_responsiveness.py`, changing `HEALTH_DEADLINE_SECONDS` from 0.5 to 1.0.
    - All 15 worktree directories exist, and every PR they served is merged, including recurrence#162.
    - The successor chain (09-15, 09-17, tip) is on `main`, and each file names the previous one as its predecessor.

**Overall verdict: PASS WITH FINDINGS.** Nearly every measurable claim in the banner, its Corrections and the successor's two SHA fixes checks out exactly against the API. That includes the historical "23 = 21 comments + 2 live pins" figure, which I rebuilt from remote `main` as of 2026-09-11. There are no CRITICAL findings and two MAJOR ones:
- The banner's lead verification command fails as written, because the census script is untracked and absent from `main` and the primary checkout. The banner's PR has to add it.
- The Corrections section's claim that the worker's #180 conversion has never run is false. It made two verified signed commits, one of them the head of the merged worker#184.

The MINOR findings are completeness and unit-consistency issues: ml#1869 omitted, "47 across 26" mixing scopes, "now fixed too" for fixes still in open PRs, "none from a local checkout", census file-type blind spots, and a verification block that under-tests its own claims.

**Changed:** no repo files. My query files and outputs are under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a1/`.
