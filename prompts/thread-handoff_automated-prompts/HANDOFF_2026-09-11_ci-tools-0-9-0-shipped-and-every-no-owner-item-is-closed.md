# HANDOFF 2026-09-11 — juniper-ci-tools 0.9.0 shipped end to end, and every no-owner item is closed

**Session**: container-registry rollout — item 6 tail, then the juniper-ci-tools 0.9.0 release train
**Predecessor**: `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
**Successor**: `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`. The arc then runs through `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md` and `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` to its current tip, `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`.
**Status**: **SUPERSEDED / CONSUMED 2026-09-11**, re-evaluated against the live ecosystem on 2026-09-22. **The title is wrong**: see Corrections 5.

---

## Status banner (added 2026-09-22 — read this before the goal below)

**Do not paste the goal below as a new thread's prompt.** Its title and opening claim that nothing
is left without the owner. That was false when written (Corrections 5), and one of its
verification commands measures the wrong thing (Corrections 1). Continue the arc from
`HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`, subject to the
caveat just below. The design of record is
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.

> **That tip handoff is itself partly stale.** Its items 3 and 4 are done (juniper-data#420,
> juniper-cascor-worker#193). Half of its item 1 has shipped too: since the 09-21 hardening
> wave, every `publish-image.yml` imports its application on the publish path. What remains of
> item 1 is a `/v1/health` serve check for the four HTTP images and a `__version__`-vs-metadata
> check. On 2026-09-22 the containers session undertook to correct, in its own PR, both
> `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` and the
> two passages of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`
> that say no stale-pin check exists. juniper-deploy#226 added that check.

Every repository fact below was re-probed on 2026-09-22 through the GitHub API, PyPI or GHCR, never
from a local checkout. The host facts (the Pi probe and the worktree directories) come from this
workstation.

### What this document asked for, and where each ask landed

Item numbers are this document's goal's numbering, which is its predecessor's. The tip handoff
numbers its items differently.

| item | state, 2026-09-22 |
| --- | --- |
| **1**: first publish in recurrence and canopy | **CLOSED.** recurrence `0.5.0` (2026-09-10, recorded below); canopy's first image with `v0.8.0` (2026-09-12), whose package came up public |
| **3**: the Pi pull, against a post-#179 image | **WAIVED** as a Wave 3 gate by the owner (2026-09-15), re-filed against first Pi deployment and OQ-3. Still owed; not runnable here (note a) |
| **4**: Wave 3 | **CLOSED**, with its D-1 test **re-scoped** (note b) |
| **5**: Wave 4, Docker Hub | **IN PROGRESS, owner-gated** (note c) |
| **6**: "Every follow-up in item 6 is closed" | **6f is OPEN**, blocked upstream (note d) |
| **7**: OQ-1 … OQ-4 | OQ-1 **CLOSED** 2026-09-11. OQ-2, OQ-3 and OQ-4 are **OPEN**, each awaiting an owner design ruling (note e) |

| this document's claim | state, 2026-09-22 |
| --- | --- |
| § What shipped: the ceilings, the Release, the floors | **CONFIRMED.** All 20 cited merge SHAs match `mergeCommit.oid`. The three PRs listed without one are canopy#619 `a5cbdcd1`, cascor#645 `63a29e87` and ml#1869 `ee57a892`. Publish runs `34579752944` and `34461928708` succeeded |
| "47 pin lines across 26 files per pass" | **MIXES TWO SCOPES** (Corrections 4) |
| "no stale ceiling and no stale floor anywhere (want 0 and 0)" | **WRONG AS WRITTEN** (Corrections 1) |
| *Weaker*: the floor bump is inert because pip resolves the newest match | **PARTLY TRUE** (Corrections 6) |
| *Weaker*: the cascor-client#161 / data-client#197 conversions have never executed | **TRUE, and as the repos stand they cannot** (Corrections 2) |
| canopy's X7 flake: "Do not chase it in the PR" | **Sound advice for a PR. The flake itself is OPEN and unowned** (note f) |
| the worktree debris "to clean up when the owner signals" | **STILL PRESENT**: all 25 of the chain's worktrees exist (note g) |

**a. The Pi pull.** A valid target now exists: `ghcr.io/pcalnon/juniper-cascor-worker:0.6.0`, torch
`2.14.0+cpu`. It cannot run from here. `turing` (192.168.50.222) shows 100% ping loss, this host has
no arm64 `binfmt_misc` handler, and `yamaguchi` is this x86_64 workstation, not a candidate. The
waiver is §5.1 of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
The pull is still owed before any Pi node runs a Juniper image.

**b. Wave 3.**
- **Releases.** canopy cut `v0.8.0` (2026-09-12), then `v0.8.1` (2026-09-18). The worker cut
  `v0.6.0` on 2026-09-15 and reached PyPI at 2026-09-18 00:18 UTC. In CDT that is 09-17, the date
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` and
  `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` give.
- **Images.** GHCR serves a release image for all five: cascor `0.11.0`; data `0.14.0` and
  `0.15.0`; canopy `0.8.0` and `0.8.1`; worker `0.6.0`; recurrence `0.5.0`.
- **juniper-deploy.** The compose repin, Helm fix, runner image and D-1 gate landed 2026-09-16/17:
  juniper-deploy#215, #216, #219/#220/#221 and #217.
- **D-1 is re-scoped, not done as written.** #217's `Published Image Refs` job checks that each ref
  resolves on both arches by querying the registry manifest, deliberately without `docker pull`.
  The live-stack tests skip in CI, so no CI job pulls and runs the published images.
- **The pins have fallen behind twice since.** canopy `0.8.1` was closed by juniper-deploy#225.
  data `0.15.0` is juniper-deploy#227, open. juniper-deploy#226 now warns on a stale pin.

**c. Wave 4.**
- **Rulings.** OQ-1 was ruled on 2026-09-11. The procedure is
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` (ml#2007).
  On 2026-09-22 the owner ruled its §3 **Option B** (ml#2009): an environment secret, in a `dockerhub`
  environment restricted to tags.
- **Done so far.** The containers session created the five environments at 2026-09-22
  19:45:59–19:46:21 UTC, on the owner's instruction. That is §5.2B steps 1–2, recorded in ml#2011.
  Each carries the tag policies `v*` and `juniper-*-v*` and holds **no secret yet**. No repo holds a
  `DOCKERHUB_*` repository secret.
- **Left.** Step 3 (the token and username, which are the owner's), then the procedure's §6
  verification, then its §7 workflow change. Its §10 leaves open whether that change is a
  release-only job or a conditional environment name, plus the Docker Hub account, the token's
  expiry, whether `juniper-deploy-test` also publishes, and Pi-node `docker login`.
- **Not only the token.** §6 OQ-1 of
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` also has Pi nodes
  log authenticated pulls rather than use the shared anonymous limit.

**d. 6f.**
- **What it is.** `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
  recorded "6f remains blocked upstream". recurrence#154 added a `filterwarnings` entry for
  starlette's deprecated `anyio.abc.BlockingPortal` alias, and it must stay until a starlette
  release stops importing that alias.
- **Still blocked.** PyPI's newest starlette is still `1.6.0` (uploaded 2026-08-08).
- **Dropped from the record.** This document's goal then called item 6 closed, and no later handoff
  or plan section carries 6f. Its only record is the comment above `filterwarnings` in
  `juniper-recurrence/juniper-recurrence/pyproject.toml`.
- **Next step.** Nothing, until starlette ships.

**e. OQ-2, OQ-3, OQ-4**, as §6 of
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` states them:
- **OQ-2** asks whether a `:X.Y.Z-cuda` variant should exist.
- **OQ-3** asks whether the Pi nodes have enough RAM to run a torch-bearing worker. Its gate is the
  Pi pull, which is also the only check that proves the 64-bit-OS precondition. Earlier documents
  framed it more widely:
  - `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`
    summarised it as "Pi disk/bandwidth".
  - `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` added the
    pull-rate point: authenticate the Pi pulls.
- **OQ-4** asks whether juniper-deploy should publish a versioned stack manifest.

**f. The X7 flake.** The test is `test_initialize_sync_does_not_block_the_loop`, in
`src/tests/regression/test_x7_sites_outside_main_gate.py`.
- **Unchanged since 2026-09-05.** It still asserts a stall bound of `BLOCK_SECONDS * 0.5` (0.2 s)
  against a 0.4 s stub block, as canopy#585 left it.
- **Why nobody owns it.** `HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md`
  item 10 records the X7 flake as fixed by canopy#649. That is true of the module the item names,
  `test_x7_loop_responsiveness.py`. canopy#649 did not touch this test's file.
- **A threshold bump cannot fix it.** Both recorded failures (0.586 s and 0.743 s) exceed the
  stub's own 0.4 s block, so no bound below the block can separate that noise from a genuinely
  blocked loop.
- **The fix.** It is structural: raise the block and the bound together, with a guard like
  canopy#649's so they cannot cross. Not owner-gated.

**g. Worktrees.** 25 in all:
- the eleven named in § Git state below;
- the four of `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`;
- the ten of `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`.

Every PR they served is merged. Cleanup waits for the owner's explicit signal, and
`worktree remove` deletes ignored files silently.

### Corrections to this document

1. **The pin check wanted 0 and got 23.** `grep -rh 'juniper-ci-tools>=' … | grep -cv '>=0\.9\.0,<0\.10\.0'`
   counts every non-matching **line**, comments included. On 2026-09-11 it returned 23: 21
   comments and **2 live, stale pins**. Both were in juniper-cascor, at `ci-cascor-model.yml:94`
   and `ci-protocol.yml:67`, pinned `>=0.6.0,<0.7.0`.
   - Both fan-out passes missed them, because each pass searched for the ceiling string it was
     replacing (`<0.9.0`, then `<0.10.0`). The first grep has the mirror-image blind spot, since it
     matches only `<0.9.0`.
   - `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md` found
     both, and juniper-cascor#646 (merge `43785fe0`) fixed them. That document had recorded
     `b374f285`, the PR's head commit, in its table and in its `.mergeCommit.oid` check. Both
     entries were corrected there on 2026-09-22.
   - juniper-ml#1909 (`4f566d37`) then widened the drift guard from 25 of the 54 live pins to all 54.
   - **Use the census instead**: `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, added by
     this banner's PR. It reads each repo's remote `main` and judges prose as well as pins.
2. **The lockfile-signing conversions.** Of the four this arc converted, two have now executed and
   two cannot yet.
   - **juniper-cascor (#641)**: it made signed commit `d7b5ea1f` on cascor#664 (2026-09-21),
     `verified: true`.
   - **juniper-cascor-worker (#180) has run.**
     `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`
     and this banner's first draft both said it had not. Its `lockfile-update.yml` also triggers on
     pull requests that touch `pyproject.toml`. It made signed commit `695d64e8`, the head of the
     merged worker#184, and `bca33c99` on the open worker#194.
   - **juniper-cascor-client (#161) and juniper-data-client (#197)**: neither repo tracks a
     `requirements.lock`, so the signed path cannot fire.
     - data-client's workflow runs, and takes its "No requirements.lock" branches (run
       `35604787525`).
     - cascor-client's has never run: 0 runs, and no Dependabot pip branch. If it did run, its regen
       step would write an untracked lockfile, which `git diff --quiet` cannot see, so it would log
       "already up to date".
     - Both are unexercised, so their correctness is unproven. Both repos' comments claimed the defect
       "never fired only because every run found the lockfile already current". juniper-cascor-client#170
       and juniper-data-client#210 correct those comments.
3. **Dates.** "Ceilings → `<0.10.0` (2026-09-10)" gives the local (CDT) date. This document says its
   times are UTC, and in UTC the eight ceiling PRs merged on 2026-09-11 between 01:32 and 01:52.
   juniper-ml#1869 merged on 2026-09-10 in UTC.
4. **"47 pin lines across 26 files per pass" mixes two scopes.** Counting added lines that carry
   `juniper-ci-tools` in each PR's diff:
   - the ceiling pass changed 43 pin lines in 26 workflow files, plus 4 in 4 `AGENTS.md` files, for
     47 lines in 30 files;
   - the floor pass changed those same 47, plus 3 in cascor's `test_sequence_safety_retired.py`, for
     50 lines in 31 files.

   So the 47 and the 26 count different things. The census's "54 live pins" is a third quantity:
   every live workflow pin across all nine repos, juniper-ml's 13 included.
5. **The title and goal were false when written.** "Nothing is left that does not need the owner",
   "every no-owner item is closed" and "ran to completion across all nine repos" all failed on
   2026-09-11:
   - two live juniper-cascor pins were still `>=0.6.0,<0.7.0` (Corrections 1);
   - 6f was open (note d);
   - the X7 flake had no owner (note f).
6. **"The floor bump is inert … all nine repos began installing 0.9.0 the moment it published" is
   only partly true.**
   - **True on a fresh hosted runner with a correctly ranged pin.** cascor `main` run `34588125830`
     (`bbdcbb6a`, 2026-09-11 10:13 UTC), job *Documentation Links* (`103226938997`), installed
     0.9.0 under `>=0.8.0,<0.10.0`. That was nine and a half hours before cascor#645 raised the
     floor.
   - **False on the same push for cascor's stale pins.** Job `103226938137`, from
     `ci-cascor-model.yml`, installed **0.6.0** under its stale `>=0.6.0,<0.7.0` (Corrections 1).
   - **False for an environment that already holds an older release.** pip does not upgrade a
     requirement that is already satisfied. `JuniperCascor1` holds `juniper-ci-tools` 0.8.0 and
     `JuniperCanopy1` 0.6.0 today; only a floor moves them.

### Where the remaining work lives

**Owner-gated:**
- Wave 4 step 3, then its verification and workflow change (note c).
- The Pi pull, once `turing` is reachable (note a).
- Rulings on OQ-2, OQ-3 and OQ-4 (note e).
- The releases that would deliver fixes already on `main`:
  - **the worker's**: inside the published `0.6.0` image, `__version__` still reads `0.4.0`.
    worker#192 fixed it on `main`, and worker#194 (the `v0.6.1` release proposal) is open.
  - **data's**: the `0.15.0` wheel ships 97 of its 201 members as tests. data#420 fixed it after the
    tag was cut.
- The worktree-cleanup signal (note g).
- The throwaway repository that
  `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` needs in
  order to prove the empty-environment-name behaviour. It is needed only if that change takes its
  conditional shape. Creating the repository is the owner's call.

**Startable, not owner-gated:**
- The tip handoff's item 1, re-scoped here: a serve check and a version check on the publish path.
- canopy's X7 structural fix (note f).
- Report to juniper-data: data#401 changed arc_agi's `task_type` without bumping its generator
  version, so a seeded arc_agi request resolves to the same `dataset_id` under 0.14.0 and 0.15.0,
  and a cached artifact keeps the fabricated class metadata. Measured in both images.
- Report on the stack: it cannot generate equities data. The data image has no `yfinance`, while
  the stack's juniper-recurrence reads `equities_seq` from it. The containers session is recording
  this in §5.2 of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
- `docs/QUICK_START.md`'s "Expected output" block dates from juniper-ml 0.6.0 (it shows, for
  example, `juniper-ci-tools 0.4.x` and `juniper-ml 0.6.0`). It is stale throughout.
- 6f: watch for a starlette release (note d).

**Authored on 2026-09-22 by the session that wrote this banner, awaiting merge.** Each merge still
needs the owner's explicit approval in the session doing it:
- juniper-deploy#227: the data `0.15.0` pin.
- juniper-deploy#228, juniper-cascor#673, juniper-cascor-client#170, juniper-data-client#210,
  juniper-canopy#655 and this banner's own juniper-ml PR (__ML_PR__). Together they fix:
  - 19 current-state lines that described an older `juniper-ci-tools` range, the class
    juniper-cascor-worker#193 fixed;
  - one test docstring;
  - the two client repos' lockfile comments.

### Verification commands (use these, not the goal's)

```bash
cd /home/pcalnon/Development/python/Juniper
# The census. Run it from any juniper-ml checkout at or after this banner's PR merge commit --
# the primary checkout needs `git pull --ff-only` first, since a worktree is not a checkout.
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test   # 31 passed, 0 failed
python3 juniper-ml/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py
#   live pins: 54, one distinct range. It exits 1 and names each stale line until the six range
#   PRs above merge (all but juniper-deploy#227), then exits 0. Read the AMBIGUOUS list either way: its ten entries are ranges the
#   census cannot attribute, and all ten were judged by hand on 2026-09-22 (only
#   docs/REFERENCE.md:3023 was stale, and this banner's PR fixes it).

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

# note g: 25 until the owner signals cleanup
ls -d worktrees/*--widen-ci-tools-ceiling--* worktrees/*--close-recurrence-model-staleness-note--* worktrees/*--sign-the-lockfile-regen-commit--* worktrees/*--torch-2-14-cpu-pin--* worktrees/*--lockfile-update-both-locks--* worktrees/*--lock-the-app-image--* worktrees/*--cpu-only-torch-pin--20260908* worktrees/*--publish-container-image--20260908* worktrees/*--harden-cpu-only-checks--2026090* | wc -l
```

### Validation record for this banner

__VALIDATION_RECORD__

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

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

**47 pin lines across 26 files per pass**, both passes identical in shape.

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

> **Still present 2026-09-22.** All 25 of the chain's worktrees exist (Status banner, note g).

The directory names still say `widen-ci-tools-ceiling` while the branch says `raise-ci-tools-floor` —
deliberate reuse, not a mistake, but do not read the directory name as the branch.
Plus the predecessor's arc worktrees, unchanged. `worktree remove` deletes ignored files silently.

Host docker daemon gained `ghcr.io/pcalnon/juniper-recurrence:0.5.0` and the local
`recurrence-lock-check:local`; nothing is dangling, so `docker image prune` reclaims nothing.

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
- **Weaker**: the claim that a floor bump is "inert because pip resolves newest" is reasoning about
  pip's behaviour, not an observation of a CI run installing 0.9.0. The next green CI run in any of the
  nine repos settles it — check one before relying on it.
- **Weaker**: the two `lockfile-update.yml` signing conversions (cascor-client, data-client) have
  **never executed**, exactly as the predecessor flagged for worker/cascor. The trigger needs a
  dependency bump that actually moves a lockfile.
  > **Settled 2026-09-22** (Status banner, Corrections 2 and 6): neither client repo has a lockfile,
  > so these two conversions cannot execute yet, while the worker's (#180) has run. The floor-bump
  > bullet above is only partly true.
- **A claim corrected mid-session**: "three repos commit their lockfile regen unsigned" was wrong about
  **juniper-ml**, which uses `peter-evans/create-pull-request` on a schedule — a different mechanism.
  Only the two client repos had the plain-push defect. The hazard was also narrower than first stated:
  an unsigned commit is harmless under **squash** (GitHub authors and signs that commit) and bites only
  on **merge-commit or rebase**, which all three repos allow. It had never fired.
