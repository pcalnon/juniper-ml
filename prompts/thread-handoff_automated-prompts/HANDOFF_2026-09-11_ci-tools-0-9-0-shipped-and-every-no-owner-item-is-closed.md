# HANDOFF 2026-09-11 — juniper-ci-tools 0.9.0 shipped end to end, and every no-owner item is closed

**Session**: container-registry rollout — item 6 tail, then the juniper-ci-tools 0.9.0 release train
**Predecessor**: `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
**Successor**: `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`. The arc then runs through `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md` and `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` to its current tip, `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`.
**Status**: **SUPERSEDED / CONSUMED 2026-09-11**, re-evaluated against the live ecosystem 2026-09-22. **The title is wrong**: see Corrections 5.

---

## Status banner (added 2026-09-22 — read this before the goal below)

**Do not paste the goal below as a new thread's prompt.** Its title and opening claim that nothing
is left that does not need the owner. That was false when written (Corrections 5), and two of its
verification commands, the pin greps, measure the wrong thing (Corrections 1). Continue the arc from
`HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`.
The status banner of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`
(juniper-ml#2019, then juniper-ml#2025) agrees with this one. It does not carry the open items this
banner found, and those are now filed as issues (below). The design of record is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.

> **In one minute.**
> - **Superseded.** This handoff's title and goal were false when written. Do not paste the goal,
>   and do not run its two pin greps (Corrections 1 and 5).
> - **Continue from `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`.**
>   Its banner is current as of juniper-ml#2025.
> - **Filed from this re-evaluation, 2026-09-23:**
>   - the X7 flake: juniper-canopy#661;
>   - the 6f watch: juniper-recurrence#182;
>   - arc_agi's unchanged `dataset_id`: juniper-data#427.
>   The `dockerhub` drift gate is the open row in §10 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
> - **In flight when this was written:**
>   - juniper-cascor#673 (docs);
>   - juniper-deploy#229 (the worker `0.6.1` repin);
>   - juniper-ml#2020 (this banner's PR).
>   Do not duplicate them. Every merge needs the owner's explicit approval in your session.
> - **For stale ci-tools text, the census is a first pass.** An exit 0 means "none of the shapes it
>   parses", not "clean" (Corrections 1).

Every repository fact below was re-probed between 2026-09-22 19:54 UTC and 2026-09-23 01:50 UTC,
through the GitHub API, PyPI or GHCR, never from a local checkout. Later moves are not reflected. The Pi probe, the worktree directories, the conda environments and the
container measurements all come from this workstation.

### What this document asked for, and where each ask landed

The item numbers are this document's goal's numbering, which it inherited from
`HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`.
`HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` numbers its items
differently.

| item | state, 2026-09-22/23 |
| --- | --- |
| **1**: first publish in recurrence and canopy | **CLOSED.** recurrence `0.5.0` (2026-09-10, recorded below); canopy's first image with `v0.8.0` (2026-09-12), whose package came up public |
| **3**: the Pi pull, against a post-#179 image | **WAIVED** as a Wave 3 gate by the owner (2026-09-15), re-filed against first Pi deployment and OQ-3. Still owed; not runnable here (note a) |
| **4**: Wave 3 | **CLOSED**; its D-1 gate is closed **as re-scoped** (note b) |
| **5**: Wave 4, Docker Hub | **IN PROGRESS, owner-gated** (note c) |
| **6**: "Every follow-up in item 6 is closed" | **6f is OPEN**, blocked upstream; tracked as juniper-recurrence#182 (note d) |
| **7**: OQ-1 … OQ-4 | OQ-1 **CLOSED** 2026-09-11. OQ-2 and OQ-4 await an owner design ruling; OQ-3's gate is the Pi pull (note e) |

| this document's claim | state, 2026-09-22/23 |
| --- | --- |
| § What shipped: the ceilings, the Release, the floors | **CONFIRMED.** All 20 cited merge SHAs match `mergeCommit.oid`. The three PRs listed without one are canopy#619 `a5cbdcd1`, cascor#645 `63a29e87` and ml#1869 `ee57a892`. Publish runs `34579752944` and `34461928708` succeeded |
| "47 pin lines across 26 files per pass" | **MIXES TWO SCOPES** (Corrections 4) |
| "no stale ceiling and no stale floor anywhere (want 0 and 0)" | **WRONG AS WRITTEN** (Corrections 1) |
| *Weaker*: the floor bump is inert because pip resolves the newest match | **PARTLY TRUE** (Corrections 6) |
| *Weaker*: the cascor-client#161 / data-client#197 conversions have never executed | **Their signed-commit path has never fired, and as the repos stand it cannot** (Corrections 2) |
| canopy's X7 flake: "Do not chase it in the PR" | **Sound advice for a PR. The flake itself is OPEN and undiagnosed**, tracked as juniper-canopy#661 (note f) |
| the worktree debris "to clean up when the owner signals" | **STILL PRESENT**, and wider than listed (note g) |

**a. The Pi pull.** A valid target now exists: `ghcr.io/pcalnon/juniper-cascor-worker:0.6.1`, with
torch `2.14.0+cpu`. It cannot run from here:
- `turing` (192.168.50.222) shows 100% ping loss.
- This host has no arm64 `binfmt_misc` handler.
- `yamaguchi` is this x86_64 workstation, not a candidate.

The waiver is §5.1 of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`,
and the pull is still owed before any Pi node runs a Juniper image.

**b. Wave 3.**
- **Releases.** canopy cut `v0.8.0` (2026-09-12), then `v0.8.1` (2026-09-18). The worker cut
  `v0.6.0` on 2026-09-15 and reached PyPI at 2026-09-18 00:18 UTC. That is 09-17 in CDT, the date
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` and
  `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` give.
- **Images.** GHCR serves a release image for all five: cascor `0.11.0`; data `0.14.0` and `0.15.0`;
  canopy `0.8.0` and `0.8.1`; worker `0.6.0` and, since about 23:08 UTC on 2026-09-22, `0.6.1`;
  recurrence `0.5.0`.
- **Worker `0.6.1`.**
  - juniper-cascor-worker#194 merged at 2026-09-22 22:56 UTC (`38f39cb8`). The Release was
    published at 23:03 UTC, and the image tag at about 23:08 UTC. The wheel reached PyPI at
    00:37 UTC on 09-23.
  - The image's revision label, `38f39cb8` (the `v0.6.1` tag), is what identifies the build.
    `__version__` cannot: since worker#192 it derives from the installed metadata. A pre-#192 build
    printed `0.4.0`.
- **juniper-deploy.** The compose repin, the Helm fix, the runner image and the D-1 gate landed on
  2026-09-16/17: juniper-deploy#215, #216, #219/#220/#221 and #217.
- **D-1.** `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md` marks
  D-1 closed by #217, and it is closed as built. #217's `Published Image Refs` job resolves each
  pinned ref's manifest on both arches; deliberately, it does not `docker pull`. Two things do pull:
  each image's own `publish-image.yml` pulls its pushed image by digest and checks it, and the
  juniper-deploy runner image is checked the same way. **No juniper-deploy CI job brings up the
  published stack.** The live-stack tests skip in CI.
- **Pin drift, three times since.** The pins have fallen behind three times: canopy `0.8.1` (closed
  by juniper-deploy#225), data `0.15.0` (juniper-deploy#227) and, since 2026-09-22, worker
  `0.6.1` (juniper-deploy#229, open). juniper-deploy#226 now warns on a stale pin.

**c. Wave 4.**
- **The ruling.** OQ-1 was ruled on 2026-09-11. The procedure is
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` (ml#2007).
  On 2026-09-22 the owner ruled **Option B** of §3 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`
  (ml#2009): an environment secret in a `dockerhub` environment restricted to tags.
- **The environments.** The containers session created all five at 2026-09-22
  19:45:59–19:46:21 UTC. This was steps 1–2 of §5.2B of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`,
  recorded in ml#2011. Each environment carries the tag policies `v*` and `juniper-*-v*`, and none
  holds a secret yet. No repo holds a `DOCKERHUB_*` repository secret.
- **What remains of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.**
  1. Step 3 of §5.2B of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`: the token and
     username, which are the owner's.
  2. The verification in §6 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
  3. The workflow change in §7 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
- **What §10 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` leaves open.**
  - The shape of that workflow change: a release-only job, or a conditional environment name.
  - The Docker Hub account.
  - The token's expiry.
  - Whether `juniper-deploy-test` also publishes there.
  - Pi-node `docker login`.
  - A drift gate for `dockerhub`: `tests/test_publish_env_policy_drift.py` reads only `pypi` and
    `testpypi`.
- **Wave 4 is more than the token.** §6 OQ-1 of
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` also has Pi nodes
  log authenticated pulls.

**d. 6f.**
- **What was recorded.**
  `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
  recorded "6f remains blocked upstream". recurrence#154's `filterwarnings` entry silences anyio's
  deprecated `anyio.abc.BlockingPortal` alias, which starlette 1.6.0's `testclient` still imports. The
  entry must stay until a starlette release stops importing it.
- **Still blocked.** PyPI's newest starlette is still `1.6.0` (uploaded 2026-08-08).
- **The record dropped it.** This document's goal called item 6 closed, and none of the later
  documents carries 6f (checked on `main`, 2026-09-23):
  - `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`;
  - `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md`;
  - `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md`;
  - `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`;
  - `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.

  Its only record was the comment above `filterwarnings` in
  `juniper-recurrence/juniper-recurrence/pyproject.toml`. Since 2026-09-23 it is tracked as
  juniper-recurrence#182.

**e. OQ-2, OQ-3, OQ-4**, as §6 of
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` states them:
- **OQ-2**: should a `:X.Y.Z-cuda` variant exist?
- **OQ-3**: do the Pi nodes have enough RAM for a torch-bearing worker? Its gate is the Pi pull,
  which is also the only check that proves the 64-bit-OS precondition. Earlier documents framed it
  more widely:
  - `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`
    framed it as "disk/bandwidth as well as RAM".
  - `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` added
    the pull-rate point: authenticate the Pi pulls.
- **OQ-4**: should juniper-deploy publish a versioned stack manifest?

**f. The X7 flake. The cause is undiagnosed, so do not change a bound until it is diagnosed.**
- **Tracked since 2026-09-23 as juniper-canopy#661**, which carries the run list and the argument.
- **The test.** `test_initialize_sync_does_not_block_the_loop`
  (`src/tests/regression/test_x7_sites_outside_main_gate.py`) asserts a stall bound of
  `BLOCK_SECONDS * 0.5` (0.2 s) against a 0.4 s stub block. It is unchanged since canopy#585.
- **The evidence.** It has failed in CI at least five times since 2026-09-05: 0.715 s, 0.807 s on
  `main`, 0.586 s, 0.743 s and 0.726 s. The last failure was on canopy#655, a docs-only PR from this
  banner's own set. Four of the five went green on a re-run.
- **What the readings cannot tell apart.**
  - A blocking call on the loop leaves a gap of at least the whole 0.4 s block. The test file's
    sensitivity control asserts `worst_gap >= BLOCK_SECONDS * 0.8`.
  - So every reading fits an on-loop call plus 0.19–0.41 s of other delay. It fits just as well
    an off-loop call plus runner suspension.
  - The green re-runs rule out only a deterministic regression.
- **How to diagnose.** Record where in the timeline the worst gap falls: before the stub starts,
  while it runs, or after it returns.
- **Ownership.** Before juniper-canopy#661 nothing tracked this test. `HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md` has two item
  10s:
  - one covers the sibling module, `test_x7_loop_responsiveness.py`, which canopy#649 fixed;
  - one covers `test_main_import_and_lifespan.py::test_keepalive_loop_survives_broadcast_error`,
    which item 13 of §E of `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` carries.

**g. Worktrees.** All of the following exist: 30 sibling worktrees and two session worktrees.
Every PR the sibling worktrees served is merged; the two session worktrees served no PR.
- **The eleven named in § Git state below.**
- **Four from `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`.**
- **Fifteen from `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`.**
  - Ten `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` opened itself.
  - Three `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` carried from `HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md`.
  - Two are older juniper-cascor-worker worktrees that `HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md` names:
    - `worktrees/juniper-cascor-worker--docs--handoff-word-count--20260830-2339--44358bf0`
      (worker#166);
    - `worktrees/juniper-cascor-worker--fix--mv-screened-base--20260902` (worker#171).
- **Two juniper-ml session worktrees**, `.claude/worktrees/luminous-inventing-crystal` and
  `.claude/worktrees/tender-splashing-wigderson`. The first holds untracked files, per
  `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`.

Cleanup waits for the owner's explicit signal, and `worktree remove` deletes ignored files silently.

### Corrections to this document

1. **The pin check wanted 0 and got 23.**
   `grep -rh 'juniper-ci-tools>=' … | grep -cv '>=0\.9\.0,<0\.10\.0'` counts every non-matching
   **line**, comments included. On 2026-09-11 it returned 23: 21 comments and **2 live, stale
   pins**. Both were in juniper-cascor, at `ci-cascor-model.yml:94` and `ci-protocol.yml:67`,
   pinned `>=0.6.0,<0.7.0`.
   - **Why both passes missed them.** Each fan-out pass searched for the ceiling string it was
     replacing: `<0.9.0`, then `<0.10.0`. The first grep has the mirror-image blind spot, because
     it matches only `<0.9.0`.
   - **The fix.** `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`
     found both, and juniper-cascor#646 (merge `43785fe0`) fixed them.
     `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` had recorded `b374f285`,
     the PR's head commit. The table and the `.mergeCommit.oid` check in `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`
     were corrected on 2026-09-22.
   - **The drift guard.** juniper-ml#1909 (`4f566d37`) then widened it from 25 of the 54 live pins
     to all 54. It still reads only the live-pin shape, `juniper-ci-tools>=X,<Y`.
   - **Use the census as a first pass, not as proof.** This banner's PR adds
     `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`.
     - **What it does.** It reads each repo's remote `main`, or a `--ref` or `--local` tree. It
       attributes ranges written in prose, judges prose ranges as sets of releases and live pins as
       text, and fails when `--expect` excludes the latest release.
     - **What it established.** On this corpus, round 3's independent instrument found no stale line
       that the census missed, judged by the census's own rules. Its report is
       `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round3-laneA-census-adequacy.md`.
       - After the six range PRs, the one stale line left was `docs/QUICK_START.md:92`. This
         banner's PR fixes it.
       - The same instrument listed five floor-only lines that the census passes by design. One is
         juniper-ml's `.github/workflows/main-verify.yml:72`, `(PyPI >=0.8.0)`. These lines state a
         floor below CI's, and they are not rewritten here.
     - **What its tests prove.** `--self-test` has 99 cases, and `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` has
       34 chosen mutants, all killed. Together they guard only the rules they name.
       The review lanes' own mutants still find survivors, and the docstring of `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`
       and the lane reports list them.
     - **Its limits.** An exit 0 means "none of the shapes it parses", not "clean". The docstring of
       `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` lists what the census drops without output, what
       it counts and passes, and what it refuses.
2. **The lockfile workflows this arc touched.** There were three conversions to the signed path
   (worker#180, cascor-client#161, data-client#197). cascor#641 is different: it extended cascor's
   already-signed step to both of its locks.
   - **cascor#641 has run.** It made signed commit `d7b5ea1f` on cascor#664 (2026-09-21),
     `verified: true`.
   - **worker#180 has run.**
     `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
     and this banner's first draft both said it had not. Its `lockfile-update.yml` also triggers on
     pull requests that touch `pyproject.toml`. It made signed commit `695d64e8`, which is the head
     of the merged worker#184, and `bca33c99`, the head of worker#194 (merged 2026-09-22
     22:56 UTC).
   - **cascor-client#161 and data-client#197.** Neither repo tracks a `requirements.lock`, so the
     signed-commit path cannot fire.
     - data-client's converted workflow has been triggered 9 times since #197. The 5 runs that executed
       all logged "No requirements.lock to commit — skipping." (for example, run `35604787525`). The
       other 4 were skipped.
     - cascor-client's has never run: 0 runs, and no Dependabot pip branch has ever been pushed. If
       it ever does run, its regen step would write an untracked lockfile, which `git diff --quiet`
       cannot see, so it would log "Lockfile already up to date".
     - Neither signed path is exercised, so its correctness is unproven. Both repos' comments said
       the defect "has never fired only because every run so far found the lockfile already
       current". juniper-cascor-client#170 and juniper-data-client#210 correct them.
3. **Dates.** "(2026-09-10)" is the local (CDT) date. In UTC the eight ceiling PRs merged on
   2026-09-11; the in-place note at § What shipped has the times.
4. **"47 pin lines across 26 files per pass" mixes two scopes.** It is 47 lines in 30 files per pass,
   43 of them in 26 workflow files. The in-place note at § What shipped has the breakdown.
5. **The title and goal were false when written.** "Nothing is left that does not need the owner",
   "every no-owner item is closed" and "ran to completion across all nine repos" all failed on
   2026-09-11:
   - two live juniper-cascor pins were still `>=0.6.0,<0.7.0` (Corrections 1);
   - 6f was open (note d);
   - the X7 flake had no owner (note f).
6. **"The floor bump is inert … all nine repos began installing 0.9.0 the moment it published" is
   only partly true.**
   - **True on a fresh hosted runner with a correctly ranged pin.** cascor `main` run `34588125830`
     (`bbdcbb6a`, 2026-09-11 10:13 UTC), job *Documentation Links* (`103226938997`), installed 0.9.0
     under `>=0.8.0,<0.10.0`. That was nine and a half hours before cascor#645 raised the floor.
   - **False on the same push, for the stale pins.** Job `103226938137`, from
     `ci-cascor-model.yml`, installed **0.6.0** under its stale `>=0.6.0,<0.7.0` (Corrections 1).
   - **Separately, outside CI.** pip does not upgrade a requirement that is already satisfied, so a
     pre-populated environment keeps its release until someone installs under the new floor.
     `JuniperCascor1` holds `juniper-ci-tools` 0.8.0 and `JuniperCanopy1` holds 0.6.0 today.

### Where the remaining work lives

**Owner-gated:**
- Wave 4 (note c): step 3 of §5.2B of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`,
  then the verification in §6 and the workflow change in §7 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
- The Pi pull, once `turing` is reachable (note a).
- The rulings on OQ-2 and OQ-4 (note e).
- **The next juniper-data release.** It ships two fixes already on `main`:
  - data#420's wheel without the test suite. The `0.15.0` wheel ships 97 of its 201 members as
    tests.
  - data#421's image that can generate equities. It merged 2026-09-23 00:56 UTC (`68c3cd7c`) on the
    owner's 2026-09-22 ruling.

  Until that release, the stack's juniper-recurrence cannot get `equities_seq` from the image.
- The worktree-cleanup signal (note g).
- If Wave 4 takes the conditional shape: creating the throwaway repository that
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` needs, to
  prove how an empty environment name behaves.

**Startable, not owner-gated:**
- **The serve check and the version check**, the half of item 1 of
  `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` that remains.
  `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` records a concurrent session
  evaluating it on 2026-09-22. Before starting it, check the five image repos for an open PR.
  - Each `publish-image.yml` already imports its application package on the publish path. For
    cascor that is `cascade_correlation` alone; its `api` module is imported only by the build-only
    smoke step.
  - The serve check must probe liveness, `/v1/health`. A standalone cascor correctly answers 503 on
    `/v1/health/ready`.
- **Diagnose the X7 flake** (note f; juniper-canopy#661) before any change to a bound.
- **The `dockerhub` drift gate**, the open row in §10 of
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
- **arc_agi's generator version**, filed as juniper-data#427.
  - juniper-data#402 (closing issue #401) changed arc_agi's `task_type` without bumping its
    generator version.
  - So any seeded arc_agi request resolves to the same `dataset_id` under 0.14.0 and 0.15.0, and a
    cached artifact keeps the fabricated class metadata. That includes a default request, whose seed
    is `DEFAULT_GENERATOR_SEED`: 42 unless `JUNIPER_DATA_DEFAULT_GENERATOR_SEED` overrides it
    (juniper-data#322). Only an explicit `seed: null` escapes it.
  - Measured in both images.
- **Watching 6f** (note d; juniper-recurrence#182) for a starlette release.
- **The juniper-deploy repin to worker `0.6.1`** is open as juniper-deploy#229. Do not open a
  second one.

**Authored 2026-09-22/23 by the session that wrote this banner.** Each merge still needs the owner's
explicit approval in the session doing it. This is the state at 2026-09-23 01:50 UTC.
- **Pins.**
  - juniper-deploy#227 (data `0.15.0`): merged, `a725f69b`.
  - juniper-deploy#229 (worker `0.6.1`): open.
- **Six PRs covering all 23 of the census's current-state lines** that name a `juniper-ci-tools`
  range or release CI no longer installs. This is the class juniper-cascor-worker#193 fixed.
  - juniper-canopy#655: merged, `26e0546f`.
  - juniper-cascor-client#170: merged, `346d11b8`.
  - juniper-data-client#210: merged, `9bc8870a`.
  - juniper-deploy#228: merged, `fc21de93`.
  - juniper-cascor#673: open.
  - juniper-ml#2020: this banner's PR. It also rewrites the "Expected output" block of
    `docs/QUICK_START.md`, which dated from juniper-ml 0.6.0.

  The two client-repo PRs also correct their lockfile comments.
- **Issues:** juniper-canopy#661, juniper-recurrence#182 and juniper-data#427.

### Verification commands (use these, not the goal's)

```bash
cd /home/pcalnon/Development/python/Juniper
# util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py: run it from any juniper-ml checkout at or
# after juniper-ml#2020's merge commit.
# The primary checkout needs `git pull --ff-only` first: a worktree is not a checkout.
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test   # 99 passed, 0 failed
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py      # 34 of 34 mutations killed
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py
#   live pins: 54, one distinct range. Once juniper-ml#2020 and juniper-cascor#673 have merged, it
#   exits 0 and lists two AMBIGUOUS lines that pass. An exit 0 is not proof of clean text
#   (Corrections 1).

# Corrections 6, both halves (the job logs expire about 90 days after 2026-09-11)
gh api repos/pcalnon/juniper-cascor/actions/jobs/103226938997/logs | grep 'Successfully installed juniper-ci-tools'   # 0.9.0
gh api repos/pcalnon/juniper-cascor/actions/jobs/103226938137/logs | grep 'Successfully installed juniper-ci-tools'   # 0.6.0

# Corrections 2
gh api repos/pcalnon/juniper-cascor-worker/commits/695d64e8 --jq .commit.verification.verified   # true (head of worker#184)
gh api repos/pcalnon/juniper-cascor/commits/d7b5ea1f --jq .commit.verification.verified           # true
gh api "repos/pcalnon/juniper-data-client/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("requirements.*lock"))]'     # []
gh api "repos/pcalnon/juniper-cascor-client/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("requirements.*lock"))]'   # []
gh api repos/pcalnon/juniper-cascor-client/actions/workflows/lockfile-update.yml/runs --jq .total_count                            # 0

# note c: each prints 0 until the owner registers the token
gh api repos/pcalnon/juniper-cascor/environments/dockerhub/secrets --jq .total_count
gh api repos/pcalnon/juniper-data/environments/dockerhub/secrets --jq .total_count
gh api repos/pcalnon/juniper-canopy/environments/dockerhub/secrets --jq .total_count
gh api repos/pcalnon/juniper-cascor-worker/environments/dockerhub/secrets --jq .total_count
gh api repos/pcalnon/juniper-recurrence/environments/dockerhub/secrets --jq .total_count

# note d: 6f stays blocked while this prints 1.6.0
python3 -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/starlette/json'))['info']['version'])"

# Corrections 1: cascor#646's merge commit and its head
gh pr view 646 --repo pcalnon/juniper-cascor --json mergeCommit,headRefOid --jq '"\(.mergeCommit.oid[0:8]) \(.headRefOid[0:8])"'   # 43785fe0 b374f285

# note g: 30 sibling worktrees, then the 2 juniper-ml session worktrees, until the owner signals cleanup
ls -d worktrees/*--widen-ci-tools-ceiling--* worktrees/*--close-recurrence-model-staleness-note--* \
  worktrees/*--sign-the-lockfile-regen-commit--* worktrees/*--torch-2-14-cpu-pin--* worktrees/*--lockfile-update-both-locks--* \
  worktrees/*--lock-the-app-image--* worktrees/*--cpu-only-torch-pin--20260908* worktrees/*--publish-container-image--20260908* \
  worktrees/*--harden-cpu-only-checks--2026090* worktrees/*--publish-container-image--20260905* \
  worktrees/*--changelog-section-order--20260905* worktrees/*--pin-cascor-client-floor--20260905* \
  worktrees/juniper-cascor-worker--docs--handoff-word-count--20260830-2339--44358bf0 \
  worktrees/juniper-cascor-worker--fix--mv-screened-base--20260902 | wc -l   # 30
ls -d juniper-ml/.claude/worktrees/luminous-inventing-crystal juniper-ml/.claude/worktrees/tender-splashing-wigderson | wc -l   # 2
```

### Validation record for this banner

Validated under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
Each lane's brief, any mid-run message and its report are archived verbatim in
`reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`. The rows below were checked against
those reports, not written from memory.

**Sizing (§3 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).**
- **Criticality is high.** This is a document of record. Seven PRs were reviewed alongside it,
  though none depends on it.
- **Uncertainty was high at the start.**
  - The banner overturns claims this document made.
  - The census was a new instrument, and it was wrong in round 1.
  - Several claims were universals: "every", "exactly", "all nine".
- **That is the top-right cell.** It asks for 3+ Lane A with distinct entry points, 2+ Lane B with
  opposing briefs, and at least two iterations.
- **The one de-escalator was met in round 3.** Independent instruments reproduced two results
  end-to-end:
  - the census's post-merge result, in
    `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round3-laneA-census-adequacy.md`;
  - the X7 run list, twice, in
    `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round3-laneB-attack-the-round2-fix-pass.md`
    and `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round3-laneA-record-and-new-numbers.md`.

  Later rounds re-ran instruments rather than re-deriving those results.
- **Lanes run.**

  | round | Lane A | Lane B |
  | --- | --- | --- |
  | 1 | three: A1, A2, A3 | two: B1, B2 |
  | 2 | two: R2-B, R2-C | one: R2-A |
  | 3 | two: R3-B, R3-C | one: R3-A |
  | 4 | none | two: R4-A (refute), R4-B (ship side) |

- **Deviations from §2 and §3 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.**
  - **Pool size.** Rounds 2–4 each ran below the cell's 3+ Lane A and 2+ Lane B.
  - **Opposing briefs.** Only round 4 ran a ship-side lane, R4-B. Rounds 1–3 asked every Lane B to
    refute.
  - **Order.** Lane A and Lane B ran concurrently in every round. §2 asks for Lane A first.

**Conduct.**
- **Read-only, with two exceptions.** Neither changed a reviewed file.
  - B2's `py_compile` wrote two gitignored `.pyc` files, which
    `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round1-laneB2-amputation-executability.md`
    discloses.
  - R2-A ran `git fetch` in the worktree.
- **Round windows (UTC).**
  - Round 1: 19:54–20:23.
  - Round 2: 20:41–21:19.
  - Round 3: 23:28–00:46. A usage limit stopped its lanes at 23:52, and they resumed in place at
    00:31.
  - Round 4: 01:02–01:43.
- **In round 2, my own writes reached two lanes mid-round.**
  - I appended the X7 conclusion to `project_container_registry_rollout_2026-09-08.md`, in the
    unversioned memory directory. R2-A read it before writing its X7 finding, so that finding was
    not independent of me.
  - I edited `reference_canopy_x7_timing_tests_flake_on_ci_runners.md` in the same directory, and
    R2-C read it.
  - I re-ran canopy#655's failed CI jobs, which changed its checks but not its content.
  - Round 3 re-derived the X7 evidence independently, and the finding changed.
- **In round 3, I edited two memory files mid-round**: `reference_prose_form_version_ranges_evade_pin_regexes.md`
  and `MEMORY.md`. No round-3 lane read either. R3-C did read this session's own log, as its brief
  asked, and the log narrates those edits.
- **In round 4, the artifacts moved under the lanes.**
  - An auto-merge sweep running as `pcalnon`, which this session did not run, merged five reviewed
    PRs mid-round: juniper-cascor-client#170, juniper-data-client#210, juniper-deploy#227,
    juniper-deploy#228 and juniper-canopy#655.
  - Each landed byte-identical to its reviewed head.
  - The sweep also armed juniper-ml#2020. I disarmed it twice and converted it to draft.
  - I opened juniper-deploy#229 mid-round. It is a new PR, not one under review.

| round | lane (type): entry point | verdict | what it found that changed this banner or a PR |
| --- | --- | --- | --- |
| 1 | A1 (A): the GitHub API only | PASS WITH FINDINGS | worker#180 had run; the census was not on `main`; ml#1869 had no SHA; "47 across 26" mixed scopes |
| 1 | A2 (A): published artifacts (PyPI, GHCR, the images) | PASS WITH FINDINGS | the `__version__` check was tautological; arc_agi keeps its `dataset_id` across the `task_type` change; deploy#227's CHANGELOG did not name data#404 |
| 1 | A3 (A): repository contents, its own census first | PASS WITH FINDINGS | the census missed ranges not written straight after the name: two docs and ten workflow comments; `QUICK_START.md:92` |
| 1 | B1 (B): attack the conclusions | PARTIALLY REFUTED ("should not merge as written") | 6f dropped; X7 unowned; item 1 never dispositioned; the floor "confirmation" refuted by the push it cited; the stack cannot generate equities |
| 1 | B2 (B): amputation and executability | SAFE WITH FIXES | "not owner-gated" said of unmerged PRs; "now fixed" said of open PRs; `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` stale; references without filenames |
| 2 | R2-A (B): attack the round-1 fix pass | SAFE WITH FIXES | the X7 prescription contradicted its own evidence; canopy's "ci-tools 0.8.0 is already installed" was invisible to the census |
| 2 | R2-B (A): census adequacy, its own instrument and 16 mutations | ADEQUATE WITH FIXES | `--expect` never checked against the latest release; the self-test never reached the verdicts; `tests/` exempt; ranges dropped past links, tables and paragraph breaks; the clean post-merge run hid `QUICK_START.md:92` |
| 2 | R2-C (A): the whole document, artifact-first, about 176 claims | PASS WITH FINDINGS | 5 refuted (among them data#401 cited for data#402) and 4 stale but unmarked |
| 3 | R3-A (B): attack the round-2 fix pass, plus a ledger of every earlier finding | SAFE WITH FIXES | five X7 failures, not three, and the X7 mechanism was a lone round-2 claim applied unchecked; the keepalive test is owned; the census's limits and "15 of 15" over-stated; the PR title still said 19 |
| 3 | R3-B (A): census adequacy, its own instrument and 26 mutations | ADEQUATE WITH FIXES | under its own rules the census misses nothing the independent instrument finds; silent drops remain in natural shapes; a surviving mutant turned the post-merge run into exit 0 |
| 3 | R3-C (A): the record and every new number, from primary sources, about 118 claims | PASS WITH FINDINGS | the conduct claim hid my round-2 writes; the seedless-nonce explanation was wrong; 30 worktrees, not 28; the repin was already claimed |
| 4 | R4-A (B): attack the round-3 fix pass, plus a ledger of every round-3 finding | SAFE WITH FIXES | the new zero-live-pins guard refused a repo whose installs are unpinned; the worker wheel and the equities ruling were already done; the `run()` scenarios missed six mutants; the stored squash body was stale |
| 4 | R4-B (B, ship side): argue the merge, find over-correction | SHIP WITH CHANGES | the three open items lived only in this banner; the first screen restated `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`; bookkeeping corrections gated nothing |

**Reconciliation (§5 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).**
- **Lone findings, rounds 3 and 4.** Every load-bearing finding that only one lane reported was
  re-derived before it was applied. The sources were the CI logs, the lane transcripts, the test
  file, both data images, PyPI, the census, and the lanes' own crafted cases.
- **Two lone round-2 findings had not been re-derived.** They were R2-A's X7 mechanism and its
  "equally unowned" for the keepalive test, findings 1 and 13 of
  `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round2-laneB-attack-the-fix-pass.md`.
  Round 3 refuted both.
- **One measurement dispute.** It was about arc_agi:
  - B1 said it is not installed in the data image
    (`reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round1-laneB1-refute-conclusions.md`);
  - A2 measured it in both images
    (`reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round1-laneA2-published-artifacts.md`);
  - opening the image settled it for A2: `HF_AVAILABLE` is True in both.
- **One of my own measurements was wrong, and so was my first explanation of it.**
  - My first probe found arc_agi's `dataset_id` differing between the images, and I blamed a
    seedless nonce.
  - In fact the probe hashed a raw params dict. The service validates params through
    `ArcAgiParams` first, whose `seed` defaults to `DEFAULT_GENERATOR_SEED`: 42, unless
    `JUNIPER_DATA_DEFAULT_GENERATOR_SEED` overrides it (juniper-data#322). Only an explicit
    `seed: null` draws a nonce.
  - Through the params class, a default request gives `arc_agi-3.0.0-5cbabfa9a9026f82` in both
    images.
- **Round 4's lanes disagreed on stopping.**
  - R4-A held that its findings change dispositions and actions, so the fix pass needs its own
    round.
  - R4-B held that the fixes are pointer, date and structure edits of measured facts, which §3
    sizes as a self-check.
  - **Resolved:**
    - round 5 is one narrow lane on this fix pass's census code and new claims;
    - the pointer and date edits were self-checked, by re-running the verification block and
      re-probing each fact.
- **Declined.**
  - A line in § What shipped begins `#163's` without a repo name. It is original text, and this
    banner does not rewrite the original.
  - R4-B asked to drop the X7 flake from Corrections 5. The original itself named the flake ("Do
    not chase it in the PR"), and it was an item left that did not need the owner.
  - Some census gaps are documented as limits of an ad-hoc tool, not closed:
    - R3-B's attribution shapes;
    - R4-A's tarball-level stubs.
- **Unresolved dissent.** B1 held that creating the throwaway repository for Wave 4's
  conditional-shape test is startable. This banner files it as owner-gated, because it creates a
  repository in the owner's account.

**Instrument.** The census is `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, in its third
version.
- **Its self-test** passes 99 of 99 cases. They include exit-code scenarios run through `run()`,
  and one run through the command line.
- **Its mutation check**, `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`, kills 34
  of 34 chosen mutants. The lanes' own mutants still find survivors, and that script's docstring
  lists their kinds.
- **It can give a different answer.** At `main` on 2026-09-23 it exits 1 and names 13 stale
  lines: the 11 that juniper-ml#2020 fixes and the 2 that juniper-cascor#673 fixes.
- **Sample.** Nine repositories, with 54 live pins and one distinct range.
- **Its limits** are in Corrections 1 and in the docstring of
  `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`.

**What this cannot support:**
- that no stale `juniper-ci-tools` text survives outside the shapes the census reads;
- any cause for the X7 flake;
- any Docker Hub rate-limit arithmetic, which comes from Docker's documentation, not from a pull;
- what the missing equities capability cost a real juniper-recurrence run. That was inferred from
  the image's lock and the compose file, not observed. The next juniper-data release carries the
  fix.

**Round 5:** pending. This line is replaced when round 5 reports.

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

> **Do not paste it (2026-09-22).** It is superseded; see the Status banner above.

---

Continue the **container-registry rollout**. **Nothing is left that does not need the owner.** Every
follow-up in item 6 is closed, the `juniper-ci-tools` 0.9.0 release train ran to completion across all
nine repos, and the recurrence image is published. What remains is items 1, 3, 4, 5 and 7 of the
predecessor, all owner-gated. Merge approval for this arc was granted per-session on 2026-09-09/10/11
— **obtain your own before merging anything**. Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
— it holds the design of record, the definition of done, and the traps this document does not repeat.

> **Corrected 2026-09-22**: false when written. See the Status banner, Corrections 5.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/` — `cd` there first. Paths beginning
`notes/`, `prompts/` or `util/` are inside `juniper-ml/`. **Times are UTC**; worktree names carry LOCAL
time (CDT, UTC−5).

### What shipped

**`juniper-ci-tools` 0.8.0 → 0.9.0, the full ordered sequence.** The 2026-09-05 SemVer ruling says
version from the change and fix what the number breaks, in a strict order. All three steps are done:

1. **Ceilings → `<0.10.0`** (2026-09-10): 8 sibling PRs — canopy#615 `436fe87d`, cascor#642 `cc0d1630`,
   cascor-client#160 `033fc9a1`, worker#181 `dcafd220`, data#392 `4d072da7`, data-client#196 `dcdd2c78`,
   deploy#209 `6eaec040`, recurrence#166 `aff3860d` — plus juniper-ml's own 13 lines in #1869.
2. **Release** (2026-09-11): `juniper-ci-tools-v0.9.0`, cut by `util/release_train/ceremony.py --execute`
   (not by hand), archive PR ml#1891 `81a5fe21`, publish run **34579752944** all three jobs green.
3. **Floors → `>=0.9.0`** (2026-09-11): cascor-client#163 `0e1b6971`, worker#183 `cb6e171f`,
   data#394 `20cd6788`, data-client#199 `534b7999`, deploy#211 `5f2c1116`, recurrence#168 `c6367c92`,
   juniper-ml#1897 `18d21a8c`, plus canopy#619 and cascor#645.

> **Corrected 2026-09-22.** Step 1's date is CDT: in UTC the eight ceiling PRs merged on 2026-09-11.
> The PRs listed without SHAs are canopy#619 `a5cbdcd1`, cascor#645 `63a29e87` and ml#1869
> `ee57a892` (Status banner, Corrections 3).

**47 pin lines across 26 files per pass**, both passes identical in shape.

> **Corrected 2026-09-22.** The two numbers count different scopes. The ceiling pass changed 43 lines in 26
> workflow files (39 live pins and 4 comments) plus 4 in 4 `AGENTS.md` files: 47 lines in 30 files.
> The floor pass changed 50 lines in 31 files (Status banner, Corrections 4).

**The recurrence image is published.** `juniper-recurrence-v0.5.0` (cut 09-10 09:36) fired
`publish-image.yml` run **34461928708**, all three jobs green →
`ghcr.io/pcalnon/juniper-recurrence:0.5.0` / `:0.5` / `:latest`, two arches. Pulled and censused:
`machine=x86_64 python=3.13.15 torch=absent distributions=36 cuda_stack=0`, "CPU-only contract holds",
and it carries **`juniper-recurrence-model 0.3.0`** — the release whose PyPI gate the owner approved.
That closes the recurrence legs of items 1 and 4.

**Also landed**: recurrence#165 `bea3dfb` (the v0.5.0 CHANGELOG asserted its lock pinned 0.2.0 when
#163's re-lock in the same release made it 0.3.0); cascor-client#161 `1b8c337c` and data-client#197
`cf73c884` (lockfile regen commits converted to the signed `createCommitOnBranch` path); ml#1888
`1b31df7d` (fan-out helpers archived).

### Verify the published wheel, not the checkout — and beware the probe

0.9.0 was checked by installing it from PyPI into a clean venv: it carries
`extract_script_references`, `ScriptReference` and `LintFinding.working_directory`; run against the
real juniper-recurrence tree — the one 0.8.0 false-positived on — it reports **ok, 16 workflows,
0 missing**; the console script runs clean on cascor.

**Two traps on the way, both worth knowing before you verify anything published:**

- **The first probe said the fix was MISSING from a perfectly good wheel.**
  `juniper_ci_tools/__init__.py` re-exports the *function* `lint_workflow_paths`, which shadows the
  submodule of the same name, so `from juniper_ci_tools import lint_workflow_paths` binds a function
  and every `hasattr` interrogates it. Use `importlib.import_module("pkg.module")`. The tell is
  `AttributeError: 'function' object has no attribute …`, not a missing symbol.
- **PyPI's aggregate JSON served 0.8.0 after `Publish to PyPI` went `success`** — the Fastly edge lag.
  `/pypi/juniper-ci-tools/0.9.0/json` answered correctly on the first try. A stale aggregate is not a
  failed publish.

### What the floor bump is actually worth — say this plainly, do not oversell it

Every pin is a range `>=X,<0.10.0` and pip resolves the newest match, so **all nine repos began
installing 0.9.0 the moment it published**, floor or no floor. The floor records the *requirement*, not
the resolution.

> **Corrected 2026-09-22.** This is only partly true. On the same push, cascor's `ci-cascor-model.yml` installed
> 0.6.0, and a pre-populated environment keeps its old release (Status banner, Corrections 6).

And a census of who could actually hit the bug: **only juniper-cascor** both runs
`juniper-lint-workflow-paths` and has `working-directory` jobs. canopy, cascor-client, worker, data and
data-client run the lint with **zero** working-directory usage; recurrence has 7 such files but does
not run the lint at all (which is why nobody noticed the false positive for so long). So no consumer
had a live false positive — 0.9.0 is preventive, and the fan-out is bookkeeping that makes the
requirement legible.

### The three failures the fan-out exposed, and what each taught

- **cascor's pin guard failed a legitimate floor bump** (all four unit-test legs).
  `test_sequence_safety_retired.py` asserted the pin range **contains** `0.8.0`; `>=0.9.0,<0.10.0` does
  not contain it, though the screens install fine from 0.9.0. `_CI_TOOLS_MIN` means "first release
  carrying the console scripts and `--scope`", so the predicate now asserts no pin can resolve **below**
  it. Mutation-checked: reverting to `>=0.7.0` still fails. The constant stays `(0, 8, 0)` — a fact
  about juniper-ci-tools' history, not about what cascor pins — **so future floor bumps no longer touch
  it**. This is the hidden-test-pin class in a shape a literal-string grep misses: the test matches on
  the parsed *range*. Only cascor carries it.
- **Renaming that test tripped sequence-safety** — `[FAIL/LOST] …test_screen_workflow_pins_admit_packaged_version`.
  A same-file rename is a LOST symbol, correctly. Waived with an `Allow-Symbol-Loss:` trailer.
  **Then the real trap**: the armed auto-merge's `commitBody` did **not** contain the trailer, and a
  squash drops what is not in that body — `main` would have reddened at Post-Merge Verification and
  nowhere earlier. `gh pr merge --auto` on an **already-armed** PR is a **no-op**; you must
  `--disable-auto` first, then re-arm with the trailer-bearing `--body-file`. Confirmed by reading
  `autoMergeRequest.commitBody` back (1139 → 1614 chars, `hasTrailer` false → true).
- **canopy's X7 timing test flaked**, `test_initialize_sync_does_not_block_the_loop`,
  `0.743s` against a `0.2s` bound, shape `1 failed, 6366 passed`. The recorded memory names this exact
  test and bound and records it failing on `main` itself. canopy `main` was green; re-ran the job.
  **Do not chase it in the PR.**
  > **2026-09-22.** The advice holds for a PR. The flake itself is open and undiagnosed. Since
  > 2026-09-23 it is tracked as juniper-canopy#661 (Status banner, note f).

### Remaining work — all owner-gated

The predecessor's items 1, 3, 4, 5 and 7 stand; go there for the commands.

> **Re-evaluated 2026-09-22.** Wave 3 is CLOSED, the Pi pull is WAIVED as a Wave 3 gate, Wave 4 is in
> progress and owner-gated, OQ-1 is closed, and 6f is open. See the Status banner at the top before
> acting on anything below.

- **Wave 3 (item 4) needs two more Releases.** Three of five images exist: cascor `0.11.0`, data
  `0.14.0`, recurrence `0.5.0`. **worker** is still `v0.5.0` and its registry holds only
  `dispatch-3d81f2c` / `dispatch-8673396` / `dispatch-9890a23` — no release image. **canopy** is still
  `v0.7.0`, cut *before* #603, so that tag can never carry one. Until both cut, `juniper-deploy`'s
  `docker-compose.yml` repin, its `Dockerfile.test` runner image and the pull-the-published-images
  integration test (plan D-1) stay blocked.
- **Item 3, the Pi pull** — and note 6b moved the worker image to torch 2.14.0, so target a post-#179
  image, not `dispatch-9890a23`.
- **Item 5 (Wave 4, Docker Hub)** and **item 7 (OQ-1…OQ-4)** — unchanged, both need decisions.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
# the release, and that the WHEEL carries the fix (not the checkout)
python3 -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ci-tools/0.9.0/json'))['info']['version'])"   # 0.9.0
python3 -m venv /tmp/v && /tmp/v/bin/pip install -q juniper-ci-tools==0.9.0
/tmp/v/bin/python -c "import importlib;m=importlib.import_module('juniper_ci_tools.lint_workflow_paths');print(hasattr(m,'extract_script_references'), list(m.LintFinding.__dataclass_fields__))"
/tmp/v/bin/juniper-lint-workflow-paths --repo-root juniper-recurrence    # OK, 16 workflows
# 2026-09-22: juniper-recurrence now carries 17 workflow files.

# CORRECTED 2026-09-22 -- these two greps do NOT measure what the next comment claims. The second
# also counts comment lines (on 2026-09-11 it answered 23, two of them real stale pins), and the
# first cannot see a pin below <0.9.0. Use util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py.
# no stale ceiling and no stale floor anywhere (want 0 and 0)
grep -rl 'juniper-ci-tools>=0\.[0-9.]*,<0\.9\.0' juniper-*/.github/workflows/ | wc -l
grep -rh 'juniper-ci-tools>=' juniper-*/.github/workflows/ | grep -cv '>=0\.9\.0,<0\.10\.0'

# the recurrence image, anonymously
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-recurrence:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-recurrence/tags/list    # 0.5.0, 0.5, latest
docker run --rm -i -e EXPECT_TORCH=absent --entrypoint python ghcr.io/pcalnon/juniper-recurrence:0.5.0 - < juniper-recurrence/util/check_image_cpu_only.py

# Wave 3's two missing Releases
gh release list --repo pcalnon/juniper-cascor-worker --limit 1   # v0.5.0 -- needs > this
gh release list --repo pcalnon/juniper-canopy --limit 1          # v0.7.0 -- predates #603, needs a new tag
# 2026-09-23: now v0.6.1 (cut 2026-09-22 23:03 UTC) and v0.8.1 -- Wave 3 is complete (Status banner, note b).
```

### Git state

Local `main` is clean in every primary checkout. **No local branch was ever pushed**: every remote
commit this session was created through the GitHub API and is GitHub-signed. The session's juniper-ml
worktree is `juniper-ml/.claude/worktrees/tender-splashing-wigderson`.

**Worktree debris to clean up when the owner signals** — the eight sibling worktrees created for the
ceiling fan-out were **reused** for the floor fan-out (reset to `origin/main` on branch
`chore/raise-ci-tools-floor`), so there are eight, not sixteen:

```
worktrees/juniper-<repo>--chore--widen-ci-tools-ceiling--20260910-2021--<sha>   [chore/raise-ci-tools-floor]
    for repo in canopy, cascor, cascor-client, cascor-worker, data, data-client, deploy, recurrence
worktrees/juniper-recurrence--docs--close-recurrence-model-staleness-note--20260910-2016--4f601b1a
worktrees/juniper-cascor-client--ci--sign-the-lockfile-regen-commit--20260910-2100--66311349
worktrees/juniper-data-client--ci--sign-the-lockfile-regen-commit--20260910-2100--25a18dfb
```

> **Still present 2026-09-22.** All 30 of the chain's sibling worktrees exist, and so do two juniper-ml
> session worktrees (Status banner, note g).

The directory names still say `widen-ci-tools-ceiling` while the branch says `raise-ci-tools-floor` —
deliberate reuse, not a mistake, but do not read the directory name as the branch.
Plus the predecessor's arc worktrees, unchanged. `worktree remove` deletes ignored files silently.

Host docker daemon gained `ghcr.io/pcalnon/juniper-recurrence:0.5.0` and the local
`recurrence-lock-check:local`; nothing is dangling, so `docker image prune` reclaims nothing.

> **2026-09-22.** `recurrence-lock-check:local` was gained in the 09-09 session (`HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`), not this
> one, and it is no longer on this host.

**Conventions**: worktrees per `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`; PR
base must be the default branch; commits via `util/open_signed_pr.py` (first commit) or
`util/ad-hoc/2026-09-08_append_signed_commit.py` (follow-ups — `open_signed_pr.py`'s DUP-GUARD refuses
once a PR exists, and the append helper verifies its own write). **Run the staleness pre-flight
immediately before every push** — `git fetch && git diff --name-only HEAD origin/main`, intersected
with your `--add` paths — these helpers upload WHOLE files and juniper-ml takes commits by the hour.

---

## Checkpoint — files changed this session

**juniper-cascor** (#642, #645): `.github/workflows/{ci,main-verify,sequence-safety}.yml`, `AGENTS.md`,
`src/tests/unit/test_sequence_safety_retired.py`.
**juniper-canopy** (#615, #619), **juniper-cascor-client** (#160, #163), **juniper-cascor-worker**
(#181, #183), **juniper-data** (#392, #394), **juniper-data-client** (#196, #199), **juniper-deploy**
(#209, #211), **juniper-recurrence** (#166, #168): the same three or five workflow files, plus
`AGENTS.md` where present.
**juniper-cascor-client** (#161) / **juniper-data-client** (#197):
`.github/workflows/lockfile-update.yml`, `CHANGELOG.md`.
**juniper-recurrence** (#165): `juniper-recurrence/CHANGELOG.md`.
**juniper-ml** (#1888, #1891, #1897): ten `.github/workflows/*.yml`,
`notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.9.0.md`, and eight `util/ad-hoc/` helpers —
`2026-09-10_{widen_ci_tools_ceiling.py,open_ci_tools_ceiling_prs.py,open_ml_tools_archive_pr.bash,open_signed_lockfile_prs.bash}`,
`2026-09-11_{raise_ci_tools_floor.py,open_ci_tools_floor_prs.py,open_ml_floor_pr.bash,append_cascor_test_fix.bash,append_cascor_waiver.bash}`.

> **Corrected 2026-09-22.** The list has nine names, not eight:
> - #1888 added two of them;
> - #1897 added four;
> - this document's own PR, #1908, added the two `append_cascor_*` scripts;
> - `2026-09-11_open_ml_floor_pr.bash` never landed on `main`.

## Validation record

**Not independently validated.** As with the predecessor, no adversarial lanes were run — the standing
instruction forbade spawning subagents unasked. Author-verified only; here is where that is strong and
where it is not:

- **Strong (executed, both directions)**: the published wheel, installed from PyPI in a clean venv and
  run against the tree that reproduced the original defect. The cascor predicate fix,
  mutation-checked. The waiver trailer, read back off the commit *and* out of
  `autoMergeRequest.commitBody`. The recurrence image, pulled and censused.
- **Strong (measured, not reasoned)**: the ceiling and floor diffs — every changed line checked to be a
  pin or an `AGENTS.md` date, across all nine repos, both passes.
  > **Corrected 2026-09-22.** Not every changed line was a pin or a date. Each pass also changed 4
  > comments, and the floor pass changed cascor's `test_sequence_safety_retired.py` (+23/−6). ml#1897
  > also added `util/ad-hoc/` helpers.
- **Weaker**: the claim that a floor bump is "inert because pip resolves newest" is reasoning about
  pip's behaviour, not an observation of a CI run installing 0.9.0. The next green CI run in any of the
  nine repos settles it — check one before relying on it.
- **Weaker**: the two `lockfile-update.yml` signing conversions (cascor-client, data-client) have
  **never executed**, exactly as the predecessor flagged for worker/cascor. The trigger needs a
  dependency bump that actually moves a lockfile.
  > **Settled 2026-09-22** (Status banner, Corrections 2 and 6). Neither client repo tracks a lockfile,
  > so their signed-commit path cannot fire yet. data-client's workflow runs and takes its
  > no-lockfile branches. The worker's conversion (#180) has run. The floor-bump bullet above is only
  > partly true.
- **A claim corrected mid-session**: "three repos commit their lockfile regen unsigned" was wrong about
  **juniper-ml**, which uses `peter-evans/create-pull-request` on a schedule — a different mechanism.
  Only the two client repos had the plain-push defect. The hazard was also narrower than first stated:
  an unsigned commit is harmless under **squash** (GitHub authors and signs that commit) and bites only
  on **merge-commit or rebase**, which all three repos allow. It had never fired.
