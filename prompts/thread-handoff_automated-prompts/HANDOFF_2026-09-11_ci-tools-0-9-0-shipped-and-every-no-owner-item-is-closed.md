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
`HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`. Its own status banner
(juniper-ml#2019, brought up to date by juniper-ml#2025) agrees with this one. The design of record
is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.

> **What has moved since `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`
> was written.**
> - Items 3 and 4 of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` are done
>   (juniper-data#420, juniper-cascor-worker#193).
> - Half of item 1 of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` has shipped.
>   - Since the 2026-09-21 hardening wave, each `publish-image.yml` imports its application
>     package on the publish path. For cascor that package is `cascade_correlation` alone. Its
>     `api` service module is imported only by the build-only smoke step, which also imports
>     `snapshots`.
>   - What remains is a serve check for the four HTTP images and a `__version__`-vs-metadata
>     check.
>   - The serve check must probe liveness, `/v1/health`. The 2026-09-21 image sweep found that
>     standalone cascor correctly answers 503 on `/v1/health/ready`.
> - juniper-ml#2019 recorded all of this in the status banner of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`.
>   It also corrected the two passages of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` that said
>   no stale-pin check exists; juniper-deploy#226 added one.
> - **The "published image is wrong right now" section of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`
>   is resolved for the image.** juniper-ml#2025 recorded that in
>   `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` too.
>   - **Release.** juniper-cascor-worker#194 merged at 22:56 UTC (`38f39cb8`). The `v0.6.1`
>     Release was published at 23:03 UTC, and the image tag at about 23:08 UTC.
>   - **Version.** `ghcr.io/pcalnon/juniper-cascor-worker:0.6.1` (index `sha256:c1576472…`)
>     reports `__version__` `0.6.1`. Since worker#192 that value derives from the installed
>     metadata, so it cannot disagree with it. What discriminates is the revision label,
>     `38f39cb8`, which is the `v0.6.1` tag. A pre-#192 build printed `0.4.0`.
>   - **Wheel.** The `0.6.1` wheel was not on PyPI at 2026-09-23 00:35 UTC. Its publish run,
>     `35795531350`, waits on the owner's `pypi` deployment approval.
>   - **Pins.** juniper-deploy still pins worker `0.6.0`, in `docker-compose.yml` and in the
>     Helm values. The repin is claimed (see the Startable list below).

Every repository fact below was re-probed on 2026-09-22 through the GitHub API, PyPI or GHCR, never
from a local checkout. The Pi probe, the worktree directories, the conda environments and the
container measurements all come from this workstation.

### What this document asked for, and where each ask landed

The item numbers are this document's goal's numbering, which it inherited from
`HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`.
`HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` numbers its items
differently.

| item | state, 2026-09-22 |
| --- | --- |
| **1**: first publish in recurrence and canopy | **CLOSED.** recurrence `0.5.0` (2026-09-10, recorded below); canopy's first image with `v0.8.0` (2026-09-12), whose package came up public |
| **3**: the Pi pull, against a post-#179 image | **WAIVED** as a Wave 3 gate by the owner (2026-09-15), re-filed against first Pi deployment and OQ-3. Still owed; not runnable here (note a) |
| **4**: Wave 3 | **CLOSED**; its D-1 gate is closed **as re-scoped** (note b) |
| **5**: Wave 4, Docker Hub | **IN PROGRESS, owner-gated** (note c) |
| **6**: "Every follow-up in item 6 is closed" | **6f is OPEN**, blocked upstream (note d) |
| **7**: OQ-1 … OQ-4 | OQ-1 **CLOSED** 2026-09-11. OQ-2 and OQ-4 await an owner design ruling; OQ-3's gate is the Pi pull (note e) |

| this document's claim | state, 2026-09-22 |
| --- | --- |
| § What shipped: the ceilings, the Release, the floors | **CONFIRMED.** All 20 cited merge SHAs match `mergeCommit.oid`. The three PRs listed without one are canopy#619 `a5cbdcd1`, cascor#645 `63a29e87` and ml#1869 `ee57a892`. Publish runs `34579752944` and `34461928708` succeeded |
| "47 pin lines across 26 files per pass" | **MIXES TWO SCOPES** (Corrections 4) |
| "no stale ceiling and no stale floor anywhere (want 0 and 0)" | **WRONG AS WRITTEN** (Corrections 1) |
| *Weaker*: the floor bump is inert because pip resolves the newest match | **PARTLY TRUE** (Corrections 6) |
| *Weaker*: the cascor-client#161 / data-client#197 conversions have never executed | **Their signed-commit path has never fired, and as the repos stand it cannot** (Corrections 2) |
| canopy's X7 flake: "Do not chase it in the PR" | **Sound advice for a PR. The flake itself is OPEN, unowned and undiagnosed** (note f) |
| the worktree debris "to clean up when the owner signals" | **STILL PRESENT**, and wider than listed (note g) |

**a. The Pi pull.** A valid target now exists: `ghcr.io/pcalnon/juniper-cascor-worker:0.6.0`, with
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
  `0.6.1` (the repin is claimed; see the Startable list below). juniper-deploy#226 now warns on a
  stale pin.

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

  Its only record is the comment above `filterwarnings` in
  `juniper-recurrence/juniper-recurrence/pyproject.toml`.

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
- **The test.** `test_initialize_sync_does_not_block_the_loop`
  (`src/tests/regression/test_x7_sites_outside_main_gate.py`) asserts a stall bound of
  `BLOCK_SECONDS * 0.5` (0.2 s) against a 0.4 s stub block. It is unchanged since canopy#585
  (2026-09-05).
- **The evidence.** It has failed at least five times in canopy CI since then:
  - 0.715 s: run `34154880308`, a Dependabot branch, Python 3.12 on macOS (2026-09-07);
  - 0.807 s: run `34397237323`, on `main` at `95284f37` (2026-09-09);
  - 0.586 s: run `34418776436`, branch `fix/y5-generators-proxy-api-key` (2026-09-09);
  - 0.743 s: run `34600043077`, canopy#619 (2026-09-11);
  - 0.726 s: run `35780782107`, canopy#655, a docs-only PR from this banner's own set
    (2026-09-22).

  The same module's `test_relay_cascade_add_does_not_block_the_loop` failed at 0.696 s (run
  `34292213310`, canopy#601). Four of the five failing runs went green on a re-run. The one on
  `main` was never re-run. The job logs expire about 90 days after each run.
- **What the readings cannot tell apart.** Every stall exceeds the stub's 0.4 s block, and that
  does not rule the defect out.
  - A blocking call on the loop leaves a gap of at least the whole block. The file's own
    sensitivity control asserts `worst_gap >= BLOCK_SECONDS * 0.8`.
  - So a 0.6–0.8 s reading fits an on-loop call plus 0.2–0.4 s of other delay. It fits equally
    an off-loop call plus runner suspension.
  - The green re-runs rule out only a deterministic regression.
- **How to diagnose.** Record where in the timeline the worst gap falls: before the stub starts,
  while it runs, or after it returns. Only then decide between re-tuning and a fix.
- **Who owns it.** `HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md` has two item 10s.
  - **This test is unowned.** The table row records the X7 flake as fixed by canopy#649, which
    is true of the module it names, `test_x7_loop_responsiveness.py`. canopy#649 did not touch
    this test's file.
  - **The keepalive test it also names is owned.**
    `test_main_import_and_lifespan.py::test_keepalive_loop_survives_broadcast_error` is carried
    by §E item 13 of `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md`, which names
    it by its lines, `:349-362`.

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
     - **What it does.** It reads each repo's remote `main`, or a `--ref`. It attributes ranges
       written in prose, judges prose ranges as sets of releases and live pins as text, and fails
       when `--expect` excludes the latest release.
     - **What it established.** On this corpus an independent instrument agreed with it. After the
       six range PRs, the one stale line left was `docs/QUICK_START.md:92`, and this banner's PR
       fixes that too. The instrument's report is `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round3-laneA-census-adequacy.md`.
     - **Its self-test** has 93 cases. They include exit-code scenarios run through `run()`.
     - **Its mutation check.** `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` kills each
       of its 24 chosen mutants.
       - The 24 are not exhaustive. Round-3 lanes wrote 47 more, and 36 of those survived the
         81-case self-test.
       - This PR then added cases, and nine mutants, for the fail-open ones among them: the exit
         code, the lag, the run guards. It did the same for the history paths and for the repo's
         own extra.
       - The rest still survive. The docstring of `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` names them.
     - **Its limits.** An exit 0 means "none of the shapes it parses", not "clean". Its own
       docstring lists the shapes it drops without any output, including:
       - a range whose nearest name is a repo;
       - a range cut off from its name by a bare `#` line;
       - a bare release in any word order but one;
       - floor-only prose;
       - string literals under `tests/`.
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
3. **Dates.** "Ceilings → `<0.10.0` (2026-09-10)" gives the local (CDT) date. This document says its
   times are UTC. In UTC the eight ceiling PRs merged on 2026-09-11, between 01:32 and 01:52;
   juniper-ml#1869 merged on 2026-09-10.
4. **"47 pin lines across 26 files per pass" mixes two scopes.** Counting the added lines that
   carry `juniper-ci-tools` in each PR's diff:
   - The ceiling pass changed 43 lines in 26 workflow files, plus 4 in 4 `AGENTS.md` files: 47
     lines in 30 files. Of the 43, 39 are live pins and 4 are header comments.
   - The floor pass changed those same 47, plus 3 in cascor's `test_sequence_safety_retired.py`: 50
     lines in 31 files.
   - The "54 live pins" of `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` is a third quantity. It is 13 (juniper-ml) + 39 + cascor's two stale
     pins, which neither pass touched.
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
   - **False for any environment that already holds an older release.** pip does not upgrade a
     requirement that is already satisfied. `JuniperCascor1` holds `juniper-ci-tools` 0.8.0 and
     `JuniperCanopy1` holds 0.6.0 today; only a floor moves them.

### Where the remaining work lives

**Owner-gated:**
- Wave 4 (note c): step 3 of §5.2B of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`,
  then the verification in §6 and the workflow change in §7 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
- The Pi pull, once `turing` is reachable (note a).
- The rulings on OQ-2 and OQ-4 (note e).
- Whether the juniper-data image should carry the equities extra. The stack cannot generate equities
  data: the image has no `yfinance`, while the stack's juniper-recurrence reads `equities_seq` from
  it. juniper-ml#2019 records this in §5.2 of
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
- The releases that would deliver fixes already on `main`:
  - **the worker's wheel.** `v0.6.1` is cut and its image is fixed (the blockquote above). The
    `0.6.1` wheel waits on the owner's `pypi` deployment approval (run `35795531350`).
  - **data's.** The `0.15.0` wheel ships 97 of its 201 members as tests. data#420 fixed it after
    the tag was cut.
- The worktree-cleanup signal (note g).
- If Wave 4 takes the conditional shape: creating the throwaway repository that
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` needs, to
  prove how an empty environment name behaves.

**Startable, not owner-gated:**
- **The serve check and the version check**, the half of item 1 of
  `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` that remains.
  `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` records a concurrent session
  evaluating it on 2026-09-22. Before starting it, check the five image repos for an open PR.
- **Diagnose the X7 flake** (note f) before any change to a bound.
- **The `dockerhub` drift gate**, the open row in §10 of
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
- **A report to juniper-data about arc_agi.** juniper-data#402, which closed issue #401, changed
  arc_agi's `task_type` without bumping its generator version. So an arc_agi request with the
  default seed (42, since juniper-data#319) or any explicit seed, but not an explicit `seed: null`,
  resolves to the same `dataset_id` under 0.14.0 and 0.15.0, and a cached artifact keeps the
  fabricated class metadata. This was measured in both images.
- **Watching 6f** for a starlette release (note d).
- **Claimed: the juniper-deploy repin to worker `0.6.1`** (compose and Helm values).
  - The session that wrote this banner took it on 2026-09-22.
  - It is sequenced after juniper-deploy#227, which edits the same two files.
  - Do not open a second one.

**Authored 2026-09-22 by the session that wrote this banner, awaiting merge.** Each merge still needs
the owner's explicit approval in the session doing it.
- **juniper-deploy#227**: the data `0.15.0` pin.
- **Six PRs covering all 23 of the census's current-state lines** that name a `juniper-ci-tools`
  range or release CI no longer installs (the class juniper-cascor-worker#193 fixed):
  - juniper-ml#2020 (this banner's PR);
  - juniper-canopy#655;
  - juniper-cascor#673;
  - juniper-cascor-client#170;
  - juniper-data-client#210;
  - juniper-deploy#228.

  juniper-ml#2020 also rewrites the "Expected output" block of `docs/QUICK_START.md`, which dated
  from juniper-ml 0.6.0. The two client-repo PRs also correct their lockfile comments.

### Verification commands (use these, not the goal's)

```bash
cd /home/pcalnon/Development/python/Juniper
# The census. Run it from any juniper-ml checkout at or after juniper-ml#2020's merge commit.
# The primary checkout needs `git pull --ff-only` first: a worktree is not a checkout.
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test   # 93 passed, 0 failed
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py      # 24 of 24 mutations killed
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py
#   live pins: 54, one distinct range. Until the six range PRs above merge, it exits 1 and names
#   each stale line. After they merge it exits 0, and it lists two AMBIGUOUS lines that pass. An
#   exit 0 is not proof of clean text (Corrections 1).

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
Each lane's brief and report are archived verbatim in
`reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`. The rows below were checked against
those reports, not written from memory.

**Sizing (§3 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).**
- **Criticality is high.** This is a document of record, and seven merges hang on it.
- **Uncertainty is high after the escalators.**
  - The banner overturns claims this document made.
  - The census is a new instrument, and it was wrong in round 1.
  - Several claims were universals: "every", "exactly", "all nine".
- **That is the top-right cell.** It asks for 3+ Lane A with distinct entry points, 2+ Lane B with
  opposing briefs, and at least two iterations.
- **Lanes run.**

  | round | Lane A | Lane B |
  | --- | --- | --- |
  | 1 | three: A1, A2, A3 | two: B1, B2 |
  | 2 | two: R2-B, R2-C | one: R2-A |
  | 3 | two: R3-B, R3-C | one: R3-A |

- **Two deviations from §2 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.**
  - **No lane argued the ship side.** Every Lane B brief asked for refutation. So the review could
    find what a fix got wrong or missed, but no lane was asked whether a fix went too far.
  - **Lane A and Lane B ran concurrently in every round.** §2 asks for Lane A first.

**Conduct.**
- **Read-only, with two exceptions.** Every lane was briefed read-only. Two stepped outside that,
  and neither changed a reviewed file:
  - B2's `py_compile` wrote two gitignored `.pyc` files, which its report discloses;
  - R2-A ran `git fetch` in the worktree.
- **No reviewed file or PR changed while a round ran.** The windows were:
  - round 1: 19:54–20:23 UTC;
  - round 2: 20:41–21:19 UTC;
  - round 3: 23:28 UTC to 00:46 UTC. A usage limit stopped its three lanes at 23:52; they resumed
    in place at 00:31.
- **In round 2, my own writes reached two lanes mid-round.**
  - At 20:44:54 UTC I appended the X7 conclusion to an unversioned memory file. R2-A read it at
    20:50, before writing its X7 finding.
  - At 20:55 UTC I edited a second memory file, which R2-C read at 20:57.
  - At 20:54 UTC I re-ran canopy#655's failed CI jobs. That changed its checks, not its content.
  - So R2-A's X7 finding was not independent of the author. Round 3 re-derived the X7 evidence
    from 312 canopy runs, in two lanes, and the finding changed.
- **In round 3, I edited two memory files mid-round.** No round-3 lane read either; I checked
  their transcripts.

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
| 3 | R3-B (A): census adequacy, its own instrument and 26 mutations | ADEQUATE WITH FIXES | its independent list misses nothing the census misses on this corpus; silent drops remain in natural shapes; a surviving mutant turned the post-merge run into exit 0 |
| 3 | R3-C (A): the record and every new number, from primary sources, about 118 claims | PASS WITH FINDINGS | the conduct claim hid my round-2 writes; the seedless-nonce explanation was wrong; 30 worktrees, not 28; the repin was already claimed |

**Reconciliation (§5 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).**
- **Lone findings.** Every load-bearing finding that only one round-3 lane reported was re-derived
  before it was applied. The sources were the CI logs, the lane transcripts, the test file, both
  data images and the census itself.
- **Two lone round-2 findings had not been re-derived.** They were R2-A's X7 mechanism and its
  "equally unowned" for the keepalive test. Round 3 refuted both.
- **One measurement dispute.** B1 said arc_agi is not installed in the data image; A2 measured it
  in both images. Opening the image settled it for A2: `HF_AVAILABLE` is True in both.
- **One of my own measurements was wrong, and so was my first explanation of it.**
  - My first probe found arc_agi's `dataset_id` differing between the images, and I blamed a
    seedless nonce.
  - In fact the probe hashed a raw params dict. The service validates params through
    `ArcAgiParams` first, and its `seed` defaults to 42 (juniper-data#319). Only an explicit
    `seed: null` draws a nonce.
  - Through the params class, a default request gives `arc_agi-3.0.0-5cbabfa9a9026f82` in both
    images.
- **Declined.** A line in § What shipped begins `#163's` without a repo name. It is original text,
  and this banner does not rewrite the original.
- **Unresolved dissent.** B1 held that creating the throwaway repository for Wave 4's
  conditional-shape test is startable. This banner files it as owner-gated, because it creates a
  repository in the owner's account.

**Instrument.** The census is `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, in its third
version.
- **Its self-test** passes 93 of 93 cases, including the exit-code scenarios run through `run()`.
- **Its mutation check**, `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`, kills 24
  of 24 chosen mutants. The mutants that survive are named in that script's docstring.
- **It can give a different answer.** At `main` today it exits 1 and names 23 stale lines.
- **Sample.** Nine repositories' remote `main`: 54 live pins, one distinct range.
- **Its limits** are in Corrections 1 and in its own docstring.

**What this cannot support:**
- that no stale `juniper-ci-tools` text survives outside the shapes the census reads;
- any cause for the X7 flake;
- any Docker Hub rate-limit arithmetic, which comes from Docker's documentation, not from a pull;
- what the missing equities extra costs a real juniper-recurrence run. That was inferred from the
  image's lock and the compose file, not observed.

**Round 4:** pending. This line is replaced when round 4 reports.

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
  > **2026-09-22.** The advice holds for a PR. The flake itself is open, unowned and undiagnosed, and
  > every recorded stall exceeds the stub's own block (Status banner, note f).

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
