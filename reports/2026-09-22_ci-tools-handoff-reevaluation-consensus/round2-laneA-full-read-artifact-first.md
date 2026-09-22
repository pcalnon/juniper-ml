<!-- markdownlint-disable -->
# Round 2, lane R2-C (Lane A)

**Entry point:** the whole document, every claim re-derived from primary artifacts.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T20:42:05Z to 2026-09-22T21:19:31Z, read-only. Agent `agent-ae990ed940cc3d3f9`.

Both sections below are verbatim: the brief as sent, then the lane's final report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are the round-2 FULL-READ, artifact-first lens in an independent-agent consensus review. Earlier rounds were scoped; scoped rounds do not re-read unchanged text. Your brief is the WHOLE document, read end to end, with every number, SHA, date, count, path, run ID and PR number re-derived from primary artifacts (GitHub API via `gh`, PyPI JSON, GHCR registry API, local `ls` for host facts) — never from another document's prose. Then role-play a fresh session given ONLY this document and judge whether it can act correctly. "UNTRACEABLE" is allowed; default to REFUTED when you cannot re-derive.

READ-ONLY (hard): do not edit/create/delete any repo file; do not commit, push, comment, merge, close, approve anything, or approve deployments. Worktree-isolated harness: only read-only `git log`/`git show`/`git diff` inside the juniper-ml worktree below; `gh api` for all else; plain commands (no shell loops over variables touching gh/git; put multi-step logic into a python script under your scratch dir). Scratch: /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r2c/ . FROZEN for this review.

DOCUMENT: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` in the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl (identical to juniper-ml PR #2020 head 50430e02). Read ALL of it: header, the `## Status banner` (tables, notes a–g, Corrections 1–6, remaining-work lists, verification block), the original goal and every original section below it (What shipped, the traps, Remaining work, Verification commands, Git state, Checkpoint, Validation record) with their in-place 2026-09-22 notes. The `__VALIDATION_RECORD__` and `__ML_PR__` placeholders are intentional.

DO:
1. Build a claim ledger: every checkable fact in the document (banner AND original body). For each, re-derive and mark CONFIRMED / REFUTED / STALE-BUT-MARKED (an original claim now false but carrying an in-place correction or covered by the banner) / STALE-UNMARKED (now false and nothing in the document says so) / UNTRACEABLE. STALE-UNMARKED items in the original body are the most important output: they are what a reader who skips the banner would be misled by.
2. Execute EVERY command in the banner's `### Verification commands (use these, not the goal's)` block exactly as written, from /home/pcalnon/Development/python/Juniper (the census lines need the script from the worktree path instead: `python3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`; note whether the command AS WRITTEN works from the primary checkout). For each: runs as written? output matches its trailing comment?
3. Fresh-session role-play: given only this document, what would you do next, and would any instruction lead you to a wrong or unsafe action (merging without approval, approving a deploy, removing worktrees, trusting a wrong check, re-doing closed work, pasting the stale goal)? Is the path to the current work unambiguous?
4. Markdown hygiene: line lengths (MD013 = 512, table rows included), table integrity, unbalanced backticks, headings.

OUTPUT (final message only is returned): the ledger summarised (counts per verdict), then every REFUTED / STALE-UNMARKED / UNTRACEABLE item with evidence and a minimal fix, then the verification-block results, then the role-play verdict. Overall: PASS / PASS WITH FINDINGS / FAIL. Terse, no preamble.

## Final report

All L-numbers below refer to `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. It is byte-identical to the PR #2020 head (`50430e02`), sha256 `714e03f7…`.

## Ledger summary (about 176 checkable claims)

| verdict | count |
| --- | --- |
| CONFIRMED | 144 |
| STALE-BUT-MARKED | 10 |
| REFUTED | 5 |
| STALE-UNMARKED | 4 |
| UNTRACEABLE | 13 (none load-bearing) |

Every hard number was re-derived from primary artifacts:
- **SHAs:** 20 of 20 cited SHAs plus the 3 banner-supplied ones match their merge commits.
- **The "23":** it reproduces exactly (21 comments plus the two pins at `ci-cascor-model.yml:94` and `ci-protocol.yml:67`, both `>=0.6.0,<0.7.0`). I rebuilt all nine repos' `main` at 2026-09-11T20:00Z to get this.
- **Pass sizes:** the ceiling pass is 43 lines in 26 workflow files plus 4 in 4 `AGENTS.md` files, i.e. 47 lines in 30 files. The floor pass is 50 lines in 31 files.
- **Pin census:** 54 live pins, 13 of them in juniper-ml. The 19 stale lines split 2+2+3+2+2+8 across the six PRs.
- **Worktrees:** all 25 exist, and every one of their branches maps to a merged PR.
- **Other checks that matched:**
  - The five environments were created 19:45:59–19:46:21Z.
  - The data 0.15.0 wheel has 97 test members out of 201.
  - Running the worker image prints `0.4.0 0.6.0 2.14.0+cpu`.
  - The recurrence image census matches byte for byte.
  - starlette is still 1.6.0, uploaded 2026-08-08.
  - The ping, binfmt and hostname host facts all check out.

The 10 STALE-BUT-MARKED items:
- L294–297, the goal's opening claims.
- L313, the "2026-09-10" date.
- L322, "47 … identical in shape".
- L356–358, the floor-bump section.
- L397–405, the remaining-work list.
- L421–422, the two greps.
- L415 `# OK, 16 workflows`: recurrence now has 17.
- L430 `# v0.5.0`: now v0.6.0.
- L431 `# v0.7.0`: now v0.8.1.
- L498–503, the Weaker bullets.

The last three verification comments (L415, L430, L431) are covered only by the banner's blanket "use these, not the goal's" and the L393 note. They carry no in-place marker, unlike the greps.

## REFUTED

1. **L223, "data#401 changed arc_agi's task_type".** #401 is an issue, closed by commit `f3797634`. The change is PR data#402, merged 2026-09-15 23:21Z. The rest of the claim holds: arc_agi's `VERSION` is `"3.0.0"` at both v0.14.0 and v0.15.0, and `generate_dataset_id(generator, version, params)` therefore gives the same id.
   - Fix: "data#402 (closing issue #401)".
2. **L72–73, "no CI job pulls and runs the published images".** This is too broad. Every image repo's `publish-image.yml` pulls the pushed image by digest and runs the CPU-only, secrets and import checks inside it. That happens in both the build job ("Verify pushed image … (publish runs)") and the merge job. §5.1 of `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` relies on exactly that for the Pi waiver.
   - Fix: "no juniper-deploy CI job pulls the published images and runs the stack".
3. **L171, a quotation that is not verbatim.** Both files actually read "has never fired only because every run **so far** found the lockfile already current". That is cascor-client `lockfile-update.yml:113` and data-client `:132`.
   - Fix: quote the line exactly.
4. **L481–484 (Checkpoint), unmarked: "eight util/ad-hoc/ helpers" from #1888/#1891/#1897.**
   - It lists nine names, and those three PRs added only six (two in #1888, four in #1897).
   - `2026-09-11_append_cascor_{test_fix,waiver}.bash` landed in ml#1908.
   - `util/ad-hoc/2026-09-11_open_ml_floor_pr.bash` returns 404 on `main`.
   - Fix: an in-place note.
5. **L496–497 (Validation record), unmarked: "every changed line checked to be a pin or an AGENTS.md date … both passes".** In the floor pass, cascor#645 changes `test_sequence_safety_retired.py` (+23/−6), and ml#1897 adds four `util/ad-hoc` scripts.
   - Fix: an in-place qualifier.

## STALE-UNMARKED

1. **L23–26, "the containers session undertook to correct, in its own PR…".** That is done: juniper-ml#2019 merged 2026-09-22 at 20:53:12Z, 13 minutes after #2020 opened. It added a banner to `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` and corrected both stale-pin passages in `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
   - Fix: cite ml#2019 as done.
2. **L227–228, "is recording this in §5.2".** §5.2 of `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` on `main` now records it (via ml#2019). I also confirmed inside the image that yfinance is absent.
   - Fix: say it is recorded, and that what remains is the owner's decision on `--extra equities`.
3. **L124, "Both recorded failures (0.586 s and 0.743 s)".** There is now a third: 0.726 s on canopy#655, one of this banner's own PRs (run `35780782107`, job `106926744764`, failed at 20:41:48Z, re-run in progress). `reference_canopy_x7_timing_tests_flake_on_ci_runners.md` records it, along with a 0.696 s stall in the same module. The conclusion is unchanged.
   - Fix: "all three (0.586, 0.743, 0.726 s)".
4. **L458, "gained … `recurrence-lock-check:local`".** That image was gained in the 09-09 session (L202 of `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md` says so), and it is no longer on the host. Nothing is dangling.
   - Fix: a trivial in-place note.

## UNTRACEABLE (none load-bearing)

- Process and history claims: the per-session merge approval (L297), "local main clean" (L436), the "no subagents" instruction (L489), and "this banner's first draft" said #180 had not run (L160).
- Transient events: the PyPI aggregate lag and the "first try" (L350–351).
- Tooling claims:
  - That the release was cut by `ceremony.py --execute` (L316). The release body's "generated by the Juniper release-train" is consistent with it.
  - The mutation check (L373).
  - The commitBody growing from 1139 chars (L383). The final 1614 is consistent, since 64 + 1614 = 1678, the length of the merge commit message.
  - That `--auto` on an already-armed PR is a no-op (L381).
- Judgments: "on the owner's instruction" (L83), "Measured in both images" (L225), and "Creating the repository is the owner's call" (L218).

## Omissions and nits

Omissions:
- §10 of `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` lists a "drift gate for dockerhub" row (`test_publish_env_policy_drift.py` reads only `pypi`/`testpypi`). It is a non-owner item, and it is absent from both note c and the "Startable" list.
- Note g's 25 excludes the chain's two juniper-ml session worktrees, `.claude/worktrees/{luminous-inventing-crystal,tender-splashing-wigderson}`. Both exist, and `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` L458 records the first as holding untracked files.

Nits:
- L14 says "one of its verification commands" is wrong, but L417 shows both greps are.
- "starlette's deprecated `anyio.abc.BlockingPortal` alias" (L96–97): the alias belongs to anyio; starlette 1.6.0's testclient imports it.
- cascor#641 is called a "conversion", but cascor was already signed; #641 only added the CPU lock.
- L332 begins with `#163's`. markdownlint rule MD018 would flag it, but `prompts/` is excluded from linting.
- The L290 heading still says to paste the goal.

## Verification block results

These were run from `/home/pcalnon/Development/python/Juniper`.

| command | result |
| --- | --- |
| census `--self-test`, as written | **fails**: exit 2, file not found. As the comment anticipates, it needs #2020 merged and the primary checkout pulled. The primary is at `c4a67481`, 6 commits behind origin. |
| census `--self-test`, from the worktree path | `31 passed, 0 failed` ✓ |
| census, from the worktree path | exits 1; 54 live pins, one range; 18 stale lines named; 10 AMBIGUOUS ✓. Hand-judging all ten agrees that only `docs/REFERENCE.md:3023` is stale. |
| census against the six PR heads (simulated) | 0 stale, exit 0 ✓. #2020 and #655 are behind `main`, but only by commits that touch no ci-tools ranges. |
| job-log commands | `0.9.0` ✓ and `0.6.0` ✓ |
| `verified` checks | `true` ✓, `true` ✓ |
| tree checks | `[]` ✓, `[]` ✓ |
| cascor-client lockfile runs | `0` ✓ |
| dockerhub environment secrets | `0` in all five repos ✓ |
| starlette | `1.6.0` ✓ |
| PR 646 | `43785fe0 b374f285` ✓ |
| worktree `ls \| wc -l` | `25` ✓ |

## Role-play verdict

No instruction leads to an unsafe action. Merges, deploys and worktree cleanup are all gated on the owner, and the verification block is read-only. The path forward is unambiguous: go to `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`, whose ml#2019 banner agrees with this one, and use the "Startable" list here.

There are five ways a fresh session could go slightly wrong:
- It could re-record the equities finding, which ml#2019 already recorded.
- It could cite #401 instead of #402 in the juniper-data report.
- It could start tip item 1 without the caution in the ml#2019 banner of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`: a concurrent session was evaluating it, and the check must target liveness `/v1/health`, not `/ready`.
- It could bump the X7 bound and block without first diagnosing where the gap falls, which `reference_canopy_x7_timing_tests_flake_on_ci_runners.md` now requires.
- A cleanup of "the 25" would miss the two session worktrees.

## Markdown hygiene

- The longest line is 417 characters, under the 512 limit.
- Both tables have consistent columns.
- Backticks are balanced.
- The heading hierarchy is sound.
- The CI structure screen (`util/ad-hoc/2026-09-05_markdown_structure_check.py`) reports 0 problems.

**Overall: PASS WITH FINDINGS.**

**Changed:** no repository file. The review scripts are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r2c/`, including `grep_at_time.py` and `census_at_heads.py`.
