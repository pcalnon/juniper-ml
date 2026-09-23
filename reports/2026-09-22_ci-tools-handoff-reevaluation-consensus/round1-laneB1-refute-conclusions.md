<!-- markdownlint-disable -->
# Round 1, lane B1

**Entry point:** adversarial: attack the conclusions.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T19:55:30Z to 2026-09-22T20:23:08Z, read-only. Agent `agent-a753c781479614bca`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are Lane B1 (analysis review, ADVERSARIAL) in an independent-agent consensus review. Your brief is to REFUTE. A finding that the reasoning is sound is worth nothing; find where it fails. Attack CONCLUSIONS while granting the premises only after you have checked them against primary sources (GitHub API via `gh`, PyPI/GHCR via `curl`/`python3`, repo contents via `gh api .../contents/...`). A peer's prose is a claim, not evidence.

READ-ONLY RULES (hard): do not edit/create/delete files in any repo; do not commit, push, comment on, merge, close or approve anything. Worktree-isolated harness: do NOT run `git` against any repo except read-only `git diff`/`git log`/`git show` inside the juniper-ml worktree below; use `gh api` for other repos. The harness refuses shell loops over variables touching gh/git; write plain commands. Scratch dir: /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/b1/.

ARTIFACTS (all frozen for this review):
1. juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl — `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`: the new `## Status banner (added 2026-09-22 ...)` section, its header lines and four in-place notes (`git diff` shows them). The `__VALIDATION_RECORD__` placeholder is intentional.
2. juniper-deploy#227 and juniper-canopy#655 (`gh pr view`/`gh pr diff`): their PR bodies and CHANGELOG/commit text make claims too.

ATTACK THESE CONCLUSIONS, each separately:
(a) "Wave 3 ... CLOSED" and "Every item it lists is closed, waived, or now owned by a later document" — is anything the original goal asked for silently dropped or mis-dispositioned? Read the original document's goal and its predecessor's item list (`HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`) and the later chain (`HANDOFF_2026-09-11_container-registry-oq1-ruled-...`, `HANDOFF_2026-09-15_...`, `HANDOFF_2026-09-17_...`, `HANDOFF_2026-09-22_ten-prs-landed-...`, all in `prompts/thread-handoff_automated-prompts/`).
(b) "The two client repos' lockfile-signing conversions cannot execute" — is "cannot" true, or only "has not"? Read each repo's `.github/workflows/lockfile-update.yml` at main and decide what the commit step actually does with no lockfile; is "correct and dormant" earned, or could the workflow misbehave (e.g. fail loudly, commit something else) on the first run?
(c) "CONFIRMED by a CI log, not by reasoning" for "the floor bump is inert because pip resolves the newest match" — does one pre-floor job log installing 0.9.0 prove the claim as the ORIGINAL document stated it ("all nine repos began installing 0.9.0 the moment it published")? Is the banner over-claiming?
(d) The X7 row: "Not addressed, and the advice stands" — check the test file and history yourself (`src/tests/regression/test_x7_sites_outside_main_gate.py` in juniper-canopy, canopy#649, canopy#585). Is "the advice stands" a defensible recommendation?
(e) The census-based claim that only three documents were stale (juniper-ml REFERENCE.md, predict_merge.py, canopy AGENTS.md) — is that a universal claim the instrument cannot support?
(f) "Not owner-gated" for the author's own PRs, and "startable and belongs to the tip" for item 1 — defensible? Is anything the banner calls owner-gated actually doable without the owner, or vice versa?
(g) deploy#227: is pinning data 0.15.0 safe for the deployed stack (juniper-cascor 0.11.0, juniper-canopy 0.8.1, demo-seed) given data 0.15.0's CHANGELOG (fetch `gh api repos/pcalnon/juniper-data/contents/CHANGELOG.md`)? Attack its claims "the one changed combination is unreachable on the shipped stack" and "demo-seed requests spiral only, so neither change reaches it". Is adding a retroactive CHANGELOG entry for deploy#226 and editing the canopy entry's last sentence appropriate?
(h) Self-serving framing: does the banner present the author's own work more favourably than the evidence supports anywhere?

OUTPUT (final message only is returned): numbered findings — the conclusion attacked, verdict (SURVIVES / PARTIALLY REFUTED / REFUTED), severity (CRITICAL/MAJOR/MINOR), evidence with commands/quotes, and the minimal correction you propose. Then an overall verdict. Terse, no preamble.

## Final report

**Lane B1 (adversarial): findings**

**1. (a) "Wave 3 … CLOSED" and "Every item it lists is closed, waived, or now owned by a later document"**
Verdict: **PARTIALLY REFUTED**. Severity: **MAJOR**.
- The Wave 3 closure survives. Canopy `v0.8.0` was cut 09-12T21:50Z and `v0.8.1` 09-18T00:38Z. Worker `v0.6.0` was cut 09-15T22:59Z and uploaded to PyPI 09-18T00:18Z. GHCR `tags/list` shows the tags the banner claims. deploy#215 merged 09-16T00:30Z and deploy#221 merged 09-17T00:16Z.
- The "every item" sentence is false. The banner's own X7 row says **"Not addressed"**, which is not closed, waived or owned by anyone:
  - The only document tracking it is item 10 of `HANDOFF_2026-09-12_canopy-selection-…md`, which says "Fixed in **canopy#649**".
  - `gh pr view 649 --json files` shows #649 changed only `test_x7_loop_responsiveness.py`, so this test is orphaned.
- **6f was silently dropped.**
  - The predecessor `HANDOFF_2026-09-09_…md` says "6f remains blocked upstream".
  - This document's goal says "Every follow-up in item 6 is closed", and the banner never corrects that.
  - Grepping the four later handoffs and the plan for `6f|anyio|starlette` finds nothing.
  - PyPI starlette is still 1.6.0, and the filter is still at recurrence `pyproject.toml:186`. The only record of the to-do is the comment at `:180-181`.
- **Item 1 is not dispositioned.** The goal lists "items 1, 3, 4, 5 and 7", but the table has rows only for 3, 4, 5 and 7.
  - The only "item 1" the banner names is "the tip handoff's re-scoped item 1". That is a different item.
- The D-1 row calls "the D-1 pull test" CLOSED, but #217 deliberately does not pull.
  - deploy `ci.yml` says: "WHY A MANIFEST QUERY AND NOT `docker pull`".
  - The live-stack tests skip in CI (the deploy#227 body reports "42 skipped").
  - So no CI job pulls and exercises the published images.
- **Correction:**
  - Add rows for item 1 (CLOSED: canopy 0.8.0, package public) and 6f (BLOCKED upstream; tracked only in recurrence `pyproject.toml`).
  - Re-disposition X7 as OPEN and unowned.
  - Mark D-1 as "closed as re-scoped (refs resolve; nothing pulls)".
  - Change the headline to "…closed, waived, owner-gated or owned — except X7 and 6f".

**2. (b) "The two client repos' lockfile-signing conversions cannot execute … both are correct and dormant"**
Verdict: **PARTIALLY REFUTED**. Severity: **MINOR**.
- data-client has an explicit guard (`lockfile-update.yml:108`, `:148`). Run 35604787525 logged "No requirements.lock in this repo — skipping regeneration". It is dormant by design.
- cascor-client has **no guard**. At `:99` it runs `uv pip compile pyproject.toml --extra dev --upgrade -o requirements.lock` unconditionally, so it creates a brand-new lockfile.
- Then `:126`, `if git diff --quiet -- requirements.lock`, cannot see an untracked file. It exits 0 and logs **"Lockfile already up to date — no commit needed"**, which is false.
- The commit is unreachable only by accident. "Correct" is not earned.
- "Has never run" means "has not", not "cannot":
  - `dependabot.yml` configures `package-ecosystem: "pip"`.
  - `gh api repos/pcalnon/juniper-cascor-client/dependabot/secrets` returns `["CROSS_REPO_DISPATCH_TOKEN"]`, so the gate would proceed.
  - A Dependabot security update would fire it.
- Both `main` branches still carry a false in-code comment: "has never fired only because every run so far found the lockfile already current" (cascor-client `:113`, data-client `:132`).
  - cascor-client has 0 runs, and data-client's runs found no lockfile at all.
  - The banner corrects the handoff's sentence but leaves these comments standing.
- **Correction:** "The signed-commit path is unreachable: by guard in data-client, and by accident in cascor-client, whose first run will print a false 'already up to date'. Neither is proven correct. Both carry a false causal comment on `main`."

**3. (c) "CONFIRMED by a CI log, not by reasoning"**
Verdict: **PARTIALLY REFUTED** (over-claim). Severity: **MAJOR**.
- The original claim was "Every pin is a range `>=X,<0.10.0` … so all nine repos began installing 0.9.0 the moment it published".
- **The very push the banner cites refutes it.**
  - Run 34588125858 (`ci-cascor-model.yml`, same `bbdcbb6a`, created 10:13:11Z), job 103226938137, ran `pip install "juniper-ci-tools>=0.6.0,<0.7.0"`.
  - It logged `Successfully installed juniper-ci-tools-0.6.0` at 10:14:44Z, one minute after the cited job installed 0.9.0.
  - The banner's own Correction 1 names that same line (`ci-cascor-model.yml:94`).
- "Inert" also holds only in fresh environments. pip keeps an installed version that already satisfies the range.
  - `JuniperCascor1/lib/python3.14/site-packages/juniper_ci_tools-0.8.0.dist-info` exists, and JuniperCanopy1 holds 0.6.0.
  - There, only the floor forces 0.9.0.
- "The moment it published" was not tested: the upload was 08:46Z and the cited log is 10:13Z.
- **Correction:** "Confirmed only for a fresh hosted runner on a correctly ranged pin. False as written: cascor's two `<0.7.0` jobs installed 0.6.0 on the same push, and any pre-populated environment keeps 0.8.x unless the floor moves."

**4. (d) X7: "Not addressed, and the advice stands"**
Verdict: **PARTIALLY REFUTED**. Severity: **MINOR**.
- The facts check out:
  - One commit only, `5a2f982a` (#585, 09-05).
  - `BLOCK_SECONDS = 0.4` and `STALL_SECONDS = BLOCK_SECONDS * 0.5` (L71–74).
  - #649 touched only the sibling module.
- "Do not chase it in the PR" is defensible as advice for triaging a PR. As the disposition of the item it is not:
  - The flake is unowned (see finding 1).
  - Memory `reference_canopy_x7_timing_tests_flake_on_ci_runners.md` says "A fix belongs in the tests' tolerance … Not done".
- #649's fix cannot be copied here. Both recorded stalls exceed the stub's own block:
  - 0.586 s (memory, `main` at `95284f37`) and 0.743 s (this document), against `BLOCK_SECONDS = 0.4`.
  - No stall threshold below the block clears them without also passing a genuinely blocked loop.
  - The fix is structural: raise `BLOCK_SECONDS` and the stall bound together, plus a #649-style guard that keeps them from crossing.
- **Correction:** "OPEN, unowned, not owner-gated, startable. The fix is structural, not a threshold bump." List it under startable work.

**5. (e) "The census found them" (the banner's "two more places"; canopy#655's "one of two ecosystem-wide current-state documents")**
Verdict: **REFUTED**. Severity: **MAJOR**.
- `SPEC_RE = juniper-ci-tools\s*(CLAUSE…)` requires the specifier to follow the package name directly. It cannot see the parenthesized and prose forms.
- Missed stale **current-state document**: `juniper-cascor-client/docs/REFERENCE.md:715` says "Runs the shared `juniper-ci-tools` (`>=0.8.0,<0.9.0`)", while its workflow installs `>=0.9.0,<0.10.0` (`sequence-safety.yml:122`).
- Missed stale **workflow header comments**, the exact class worker#193 fixed ("header comments … described `>=0.8.0,<0.9.0`"):

  | repo | file:line |
  | --- | --- |
  | cascor | `sequence-safety.yml:60`, `main-verify.yml:64` |
  | data-client | `sequence-safety.yml:28`, `main-verify.yml:28` |
  | deploy | `sequence-safety.yml:72`, `main-verify.yml:69` |
  | cascor-client | `sequence-safety.yml:28` |
  | canopy | `sequence-safety.yml:27` (the same repo canopy#655 edits) |

- Misclassified: `juniper-ml/tests/test_coverage_gap_mapper_drift.py:53` is an operator instruction, `pip install "juniper-ci-tools>=0.6.0,<0.7.0"`, which the census counts as FIXTURE.
- Latent gap: `LOCK_RE` matches `.lock` files, but `TEXT_SUFFIXES` omits `.lock`, so those files are never read. No `.lock` file pins ci-tools today.
- Consequence: after canopy#655 and this PR merge, the census will exit 0 while at least 10 stale lines remain.
- **Correction:**
  - Widen the regex so it catches a specifier near the package name, not only directly after it.
  - Add `.lock` to the suffixes.
  - Either fix or list the lines above, and scope both claims to "forms the census's regex can see".

**6. (f) "Not owner-gated" for the author's own PRs; item 1 "startable and belongs to the tip"**
Verdict: **PARTIALLY REFUTED**. Severity: **MINOR**.
- Opening the PRs was not owner-gated; merging them is. The headless-merge policy says "headless merges proceed only on his explicit approval", and the document itself says "obtain your own before merging anything". The census's exit 0 depends on those merges.
- Wave 4 is narrowed to "register the token":
  - Procedure §7 exists "so the registration is not mistaken for completion".
  - Where Wave 4 names the environment is still undecided (§10).
  - The empty-environment-name behaviour is "Unverified … Test it in a throwaway repository first". That test is startable now without the owner.
  - The tip also says "Wave 4 is not only two secrets" (authenticated Pi pulls, plan §6 OQ-1). The banner omits all of this.
- Item 1: the re-scope is the banner's own, not the tip's.
  - The tip's text is stale. `cascor/publish-image.yml:210-238` now runs `check_image_no_secrets.py` and an import on the publish path.
  - The name also collides with this document's own item 1.
- The worker v0.6.1 release proposal (worker#194, opened 09-22T19:44:34Z) is not mentioned among "the Releases that would deliver two fixes".
- **Correction:**
  - Use three buckets: owner-gated, startable, and authored-but-awaiting-merge-approval.
  - Add the Wave 4 workflow change and the throwaway-repo test.
  - Name worker#194.
  - Call it "the tip's item 1, re-scoped here".

**7. (g) deploy#227: "the one changed combination is unreachable", "demo-seed requests spiral only", and the CHANGELOG edits**
Verdict: **SURVIVES** (conclusions); **PARTIALLY REFUTED** (reasoning). Severity: **MINOR**.
- Verified:
  - The juniper-data `environment:` block in compose is an explicit list with no truncation variable and no `env_file:`.
  - The defaults are `False` (`juniper_data/core/limits.py:138-139`), and grepping the deploy repo for `ALLOW_TRUNCATION` finds nothing.
  - The demo-seed entrypoint posts `'generator': 'spiral'` only.
- "Nothing in this repo requests equities" is the wrong test:
  - The stack runs `juniper-recurrence:0.5.0` in every profile with `JUNIPER_DATA_URL=http://juniper-data:8100`.
  - `juniper_recurrence/data.py:1` reads "juniper-data-client → 3-D `equities_seq` NPZ".
  - Recurrence is missing from both the PR's consumer list and this brief's.
- Equities is moot here for a reason the PR never states:
  - The data image lock is compiled `--extra api --extra observability --extra mnist` (`requirements.lock:2` at `v0.15.0`, zero yfinance lines).
  - So `EQUITIES_DEPS_AVAILABLE=False` (`generators/equities/generator.py:62-70`), and the backend/data networks are `internal: true`.
  - `arc_agi` is likewise not installed.
  - The result is a pre-existing gap: the stack cannot serve `equities_seq` to recurrence at 0.14.0 either.
- The retroactive #226 CHANGELOG entry is accurate. I checked `--fail-on-stale`, `--no-currency`, the `::warning::` output, the `tags/list` read and the int-tuple comparison in `verify_published_images.py`.
  - #226 merged 09-22T08:34Z, after `v0.3.0` (09-17), so `[Unreleased]` is the right home.
  - Editing the unreleased canopy sentence that #226 made false is appropriate.
- **Correction:** replace the equities rationale with "the image cannot generate equities (no yfinance in its lock; internal-only networks)", and note recurrence as an affected consumer of that existing gap.

**8. (h) Self-serving framing**
Verdict: **PARTIALLY REFUTED**. Severity: **MAJOR** (every error leans toward closure).
- "The census … found the same class in two more places, **now fixed too**":
  - canopy#655 is OPEN (`mergedAt: null`).
  - The juniper-ml fixes are uncommitted in this worktree (`M docs/REFERENCE.md`, `M util/fleet_triage/predict_merge.py`).
  - The census under-counts (finding 5).
- "Not by reasoning" oversells a single job's log as proof of a universal claim (finding 3).
- "Both conversions are correct" certifies the arc's own unexecuted work (finding 2).
- The banner retracts the document's verification command but not its headline claims, even though its own Correction 1 shows two live no-owner stale pins on `main` when it was written:
  - "Nothing is left that does not need the owner".
  - "ran to completion across all nine repos".
  - The title, "every-no-owner-item-is-closed".
  - Compare the 09-17 banner, which says outright that its title was WRONG.
- **Correction:** write "fixed in open PRs", and add a Correction 4 retracting the title and goal claims.

**9. Smaller defects** (all **MINOR**)
- **Verification command path does not exist yet.** It runs `juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` from the ecosystem root, but `ls` on the primary checkout finds no such file. The script exists only untracked in this worktree. This is the trap recorded in the 09-17 handoff ("A worktree is not a checkout"). Add "after this PR merges and juniper-ml is pulled".
- **PR count.** "22 PRs re-read" should be 23: juniper-ml#1869 also has no SHA (its merge is `ee57a892`). All 23 SHAs otherwise match.
- **Worktree count.** "All fifteen" leaves out the 10 arc worktrees from 09-08, which the document includes by "Plus the predecessor's arc worktrees". All 10 still exist.
- **OQ-3 narrowed again.** The banner describes it as "Pi RAM + 64-bit OS", dropping 09-08's "disk/bandwidth" and 09-11's pull-rate point. The 09-17 validation lanes already flagged this same narrowing.

**Overall verdict: PARTIALLY REFUTED. The banner should not merge as written.** The facts I could check hold up: SHAs, runs, tags, dates, environments, secrets and the wheel counts. The failures are in its conclusions:
- the census completeness claim (REFUTED);
- the "CONFIRMED" universal, refuted by the cited push itself;
- "every item closed", which misses X7 and 6f and never dispositions item 1;
- "correct and dormant" for cascor-client;
- presenting its own unmerged work as fixed.

deploy#227 is safe to merge; only its equities rationale needs rewording. canopy#655's diff is correct, but its body's completeness claim is false.
