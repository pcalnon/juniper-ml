# HANDOFF 2026-09-08 — Container registry rollout: Wave 2 landed, and the CUDA class came in three shapes

**Session**: container-registry rollout, item 1 (P0 worker CUDA fix) → Wave 2 (four publish workflows)
**Predecessor**: `HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md`
**Validation**: three independent lanes on the draft (A grounding, B1 executability + amputation, B2
refuter) per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`,
then a second round on the corrections — record in § Validation record at the end. **Round 1 found
two refuted claims of mine, two amputations, six executability majors and two real check gaps**, all
corrected below; the two check gaps are also fixed in code (§ item 6a). **Round 2 caught the owner
cutting three Releases under the document** (2026-09-09 07:15 UTC) — items 1 and 4 and § Where this
stands were rewritten from the live state, and round 2's other findings are folded in.

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. Item 1 and Wave 2 are done or landing; what remains is
**owner-gated** (items 1, 3, 4, 5, 7) plus follow-ups that need no owner (item 6). Merge approval
for this arc's PRs was granted on 2026-09-08 and is **per-session** — the successor must obtain its
own before merging anything. Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md`
— every "the predecessor" below means that file, and it holds the mechanisms this document only
summarises (the COPY-then-lock install order, the vacuous-fix shape, the tag-race analysis).

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/` — `cd` there first. Relative paths
below are from there, EXCEPT paths beginning `notes/`, `prompts/` or `util/` — the juniper-ml helpers
(`util/open_signed_pr.py`, `util/wait_for_checks.py`, `util/ad-hoc/…`) — which are inside
`juniper-ml/`. Another repo's file is always written `<repo>/path`; `<repo>/util/check_image_cpu_only.py`
means each repo's own copy of that script.
**The primary checkouts may be behind `origin/main`** (worker and recurrence were, by one commit,
when this was written): `git pull --ff-only` in a primary before reading files from it, or read via
`gh api repos/pcalnon/<repo>/contents/<path>?ref=main --jq .content | base64 -d`. **Times**: GitHub
timestamps are UTC; worktree names carry LOCAL time (the host is CDT, UTC−5) — "02:11" in a worktree
name is 07:11 UTC. Round 2 found this document mixing the two; every time below now says which.

**Design of record** (settled, do not re-litigate): juniper-ml
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` — D-1 publishing
lives in the owning repo on `release: published`; D-2 GHCR first, Docker Hub second; D-3 tags
`X.Y.Z` / `X.Y` / `latest`, release-only; D-4 `linux/amd64` + `linux/arm64`; D-5 GPU/CUDA out of scope.

**Definition of done for the arc** (carried from the predecessor): all five images publish on
`release: published`; `juniper-deploy/docker-compose.yml` pins released `X.Y.Z` refs; juniper-deploy's
pull-the-published-images integration test is green.

### Where this stands

**The worker image is CPU-only, published, and its publish path is proven end to end.**
`ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23` (built by `workflow_dispatch` run
**34294654855** from worker `main` `9890a23f`, the merge of worker#176) is a multi-arch index whose
merge job logged `references exactly the verified images` and `CPU-only contract holds`, and whose
amd64 image pulls anonymously and reports `torch=2.12.0+cpu (cuda=None) distributions=24
cuda_stack=0`. Sizes, with units: **312 MB compressed** (registry transfer, amd64; arm64 270 MB) and
**1.47 GB unpacked** on disk, against **2.86 GB compressed / 8.05 GB unpacked** for the predecessor's
CUDA image `dispatch-3d81f2c`, which is still in the registry (deleting a package version needs
`delete:packages`; owner action). `dispatch-8673396` (the first fixed publish, identical Dockerfile,
older workflow) also exists.

**The first two real release images exist, cut by the owner.** At 07:15 UTC on 2026-09-09 the owner
cut cascor v0.11.0 (tag on `5eb6f144`, after #634), data v0.14.0 (tag on `e769999d`, the #387 merge)
and canopy v0.7.0 (tag on `d8b1592d`, BEFORE #603). `publish-image.yml` ran on the first two — runs
**34322913368** (cascor) and **34322906608** (data), three jobs green each — and published
`ghcr.io/pcalnon/juniper-cascor:0.11.0` / `:0.11` / `:latest` and `ghcr.io/pcalnon/juniper-data:0.14.0`
/ `:0.14` / `:latest`, two linux arches each. Both merge jobs ran the UN-hardened check (item 6a had
not landed), so I pulled both and ran the HARDENED census inside them: data `torch=absent
distributions=60 cuda_stack=0`, cascor `torch=2.14.0+cpu (cuda=None) distributions=57 cuda_stack=0`,
both `CPU-only contract holds` (amd64 halves; the arm64 halves were checked by the release runs' own
per-arch steps). Canopy v0.7.0 shipped NO image (no workflow at the tag). The recurrence-model v0.3.0 and recurrence-client v0.3.0 Releases (07:22 / 07:31 UTC) fired
`publish-image.yml` and were SKIPPED end to end by the `juniper-recurrence-v` guard — the tag-guard
claim proven live.

**All five image-bearing repos carry `publish-image.yml`** from the worker template, each asserting the
CPU-only contract inside the image on the PR arm AND on the publish path. States below are as of
writing — **re-probe with `gh pr view <n> --repo pcalnon/<repo> --json state,mergeCommit` before
acting**; recurrence#160 and canopy#608 were still in CI with native auto-merge armed:

| repo | PRs | state at writing | image-specific facts |
| --- | --- | --- | --- |
| juniper-cascor-worker | #175 (P0 fix), #176 (merge-job digest fix) | both MERGED: `86733960`, `9890a23f` | torch pinned `2.12.0+cpu` (the lock header's version); ENTRYPOINT image |
| juniper-data | #385 (workflow), #387 (digest fix) | both MERGED: `0f177990`, `e769999d` | torch-free, check runs `EXPECT_TORCH=absent`; CMD-only |
| juniper-recurrence | #153 (workflow), #154 (anyio test fix) | both MERGED: `7d0291f1`, `63974b32` | `juniper-recurrence-v` guard REQUIRED; semver `match=` attribute; context `juniper-recurrence/`; version from `_version.py`; py3.13; torch-free; ENTRYPOINT image |
| juniper-cascor | #634 | MERGED `2798a2af` (one API-signed commit, rebased twice onto `main`, last onto the v0.11.0 release-PROPOSAL merge `3286b75` = #635; the v0.11.0 tag itself sits on `5eb6f144`) | `v` guard REQUIRED; NEW `requirements-cpu.lock`; torch pinned `2.14.0+cpu`; CMD-only |
| juniper-canopy | #603 | MERGED `134d375f` at 07:58 UTC (rebased to one commit `45f70228` onto the v0.7.0 release-proposal commit `d8b1592d` (#606) after its second conflict, then `update-branch` merged #601) | torch pinned `2.14.0+cpu` (installed for demo mode); `paths:` covers `conf/`; CMD-only |
| item 6a hardening | worker#178, data#391, cascor#637, recurrence#160 | opened 2026-09-09 07:18 UTC (02:18 CDT), auto-merge armed; #178 MERGED `fde50791`, #391 MERGED `910f7a55`, #637 MERGED `f96551e1`, #160 in CI behind a busy `main`; **canopy#608** opened 08:00 UTC after #603 merged, auto-merge armed | see item 6a |

Every PR arm built both arches natively (recurrence 58 s / 40 s, worker ~4 min per arch). Every
commit was **GitHub-signed via the API** (`util/open_signed_pr.py`; follow-ups via
`util/ad-hoc/2026-08-26_commit_files_to_pr_branch.py`): the signing key is on a hardware token and
`gpg: signing failed: Timeout` is the pinentry waiting for a touch, not a config error.

### The finding that widened item 1 — the CUDA class has three shapes (two shipped CUDA, one was unguarded)

1. **worker — re-resolution (shipped CUDA).** Unpinned CPU torch, then a lock install with no index
   flags. **The link this document's first draft dropped (the predecessor had it):** the lock pins
   `juniper-cascor-model==0.1.0`, whose metadata declares `torch>=2.10.0`, so torch is *in scope* for
   the lock install; a torch-free lock cannot exhibit this shape. The newest CPU wheel (2.14.0) requires
   `setuptools>=77.0.3` while the lock (compiled for 2.12.0) pins `70.2.0`, so pip rejected it,
   rejected PyPI's 2.14.0 and 2.13.0 for the same reason, and settled on PyPI's 2.12.1 — the CUDA
   build, the only index it had for torch. **pip's own log says so** (run 34028226714, job
   101472927917): `pip is looking at multiple versions of torch …`, then
   `Collecting cuda-toolkit==13.0.2 … (from torch>=2.10.0->juniper-cascor-model==0.1.0)`,
   `Collecting nvidia-cudnn-cu13==9.20.0.48`, `Collecting triton==3.7.1`, and finally `Successfully
   installed … cuda-bindings-13.3.1 cuda-pathfinder-1.8.1 cuda-toolkit-13.0.2 …`.
2. **cascor — the lock itself (shipped CUDA).** `requirements.lock` is compiled `--no-emit-package
   torch` but was RESOLVED against the CUDA torch, so it pins the CUDA stack **outright** — 19 lines:
   `nvidia-cublas==`, `nvidia-cudnn-cu13==`, `nvidia-nccl-cu13==`, `triton==`, `cuda-toolkit==` and
   friends (~3 GB of wheels, the figure `requirements-cpu.lock`'s header records). `pip install -r
   requirements.lock` installed them whether or not torch
   wanted them, while torch itself stayed CPU — which is exactly why a version check alone is blind
   to this shape. Fix: `requirements-cpu.lock` = the GPU lock minus the CUDA stack, derived with
   `--constraint requirements.lock`, so shared pins are identical by construction (53 vs 72 pins;
   diff of the non-CUDA pins empty; pinned by `test_cpu_lock_is_the_gpu_lock_minus_the_cuda_stack`).
3. **canopy — unpinned, unguarded (did NOT ship CUDA, and could not as written).** torch is a `[demo]`
   extra; the lock has no torch; the Dockerfile installs torch for demo mode from the CPU index
   unpinned, so the image changed with every PyTorch release and nothing asserted it. "Could not"
   rests on the `+cpu` wheel's metadata (no cuda / nvidia / triton requirement, x86_64 and aarch64),
   NOT on the index — the CPU index itself hosts `nvidia-*` / `cuda-*` wheels, so an unpinned install
   was one upstream metadata change away from pulling them. **The
   predecessor's "canopy: not torch-bearing" row was true of the package and false of the image.**

The fix, applied to the three torch-bearing images: pin `torch==X.Y.Z+cpu` in BOTH pip installs,
`--extra-index-url` to the CPU index on the lock install (never `--index-url`: it 403s most of PyPI),
`pip check` at the end of the builder, and `<repo>/util/check_image_cpu_only.py` run INSIDE the image
asserting the exact pinned `+cpu` version, `torch.version.cuda is None`, and no CUDA-stack
distribution. The census is the discriminating check: "install the CPU wheel last" swaps `torch` and
leaves the orphaned CUDA wheels in `site-packages` while `__version__` reads `+cpu`. data and
recurrence get the census only, with `EXPECT_TORCH=absent` (no `pip check`; recurrence has no lock).

### Remaining work

**1. OWNER GATE — the first publish in recurrence and canopy.** (data's and cascor's packages were
created at 07:15 UTC on 2026-09-09 by the owner's own Releases; the worker's exists since Wave 1.) A
first publish — a `workflow_dispatch` with `push: true`, or a Release — creates a new GHCR package,
and all three workflow-created so far (worker, cascor, data) came up **public** (GitHub's docs say a
package inherits the repo's permissions but NOT its visibility, so verify each new package's
visibility on its package page after the first publish rather than assuming). Confirm with the owner
first. **Precondition: the repo's `publish-image.yml` on `main` must carry the CORRECTED identity
check** (the merge job resolves each pushed digest with `imagetools inspect` before comparing; the
step text says `verified build digests resolve to`). Both recurrence and canopy `main` carry it now (canopy since #603 merged at
07:58 UTC; before that canopy had no workflow on `main` and a dispatch was simply refused — the
"writes the tag, then the merge job fails" mode was data's between #385 and #387, and the worker's
first dispatch). For a rehearsal that creates no release tags:

```bash
gh workflow run publish-image.yml --repo pcalnon/<repo> --ref main -f push=true
gh run list --repo pcalnon/<repo> --workflow publish-image.yml --limit 3 --json databaseId,event,status,conclusion,headSha   # pick the workflow_dispatch row whose headSha is main's
gh run view <run-id> --repo pcalnon/<repo> --json jobs --jq '.jobs[] | "\(.name)\t\(.conclusion)"'      # want: Build linux/amd64, Build linux/arm64, Publish manifest all success
```

The tag is `dispatch-<first 7 chars of main's sha>`. Then verify anonymously; the `docker run` form
depends on the image's entrypoint:

```bash
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/<repo>:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/<repo>/tags/list
# EXPECT_TORCH: data/recurrence `absent`; cascor/canopy `2.14.0+cpu`; worker `2.12.0+cpu`
#   (read `ARG TORCH_VERSION` in the Dockerfile AT THAT TAG rather than trusting this line)
# CMD-only images (data, cascor, canopy): the trailing command IS the python invocation
docker run --rm -i -e EXPECT_TORCH=absent ghcr.io/pcalnon/<repo>:dispatch-<sha> python - < <repo>/util/check_image_cpu_only.py
# ENTRYPOINT images (recurrence, worker): override the entrypoint, pass only `-`
docker run --rm -i -e EXPECT_TORCH=absent --entrypoint python ghcr.io/pcalnon/<repo>:dispatch-<sha> - < <repo>/util/check_image_cpu_only.py
```

Before a repo's first publish the token one-liner dies with `KeyError: 'token'` and `tags/list` reads
DENIED — that means "no package yet", not a permissions problem. **Do not register `publish-image`
as a required status check** — it is `paths:`-filtered and would orphan every unrelated PR.

**2. DONE — the worker's merge job is re-proven.** The first `push: true` dispatch on the fixed worker
(run **34292278641**) built and verified both arches but FAILED in `Publish manifest` at the new
"Verify published image is CPU-only" step, **after** the tag was written: it compared the digests the
build jobs pushed (per-arch OCI **indexes** — image + provenance attestation, because
`docker/build-push-action` attaches provenance by default) with the tag's `.manifests[]` entries (the
flattened **image manifests**). Those can never be equal. The correction (worker#176, data#387, and the
same block in #634 / #603 / recurrence `main`) resolves each pushed digest to the linux image it
carries — validated on the live registry against run 34292278641's own digests (tag
`dispatch-8673396`: `95e605af…` → `ee9064e2…` arm64, `ac848506…` → `ae1d5377…` amd64, exactly the
tag's *linux* entries; the tag also lists two attestation manifests, which the `os=="linux"` filter
drops on both sides). Run **34294654855** then passed all three jobs and published `dispatch-9890a23`
(its pushed digests `e00b18a3…` → `c5f5a1ad…` arm64 and `e02c9047…` → `0baf871c…` amd64, confirmed by
two round-2 lanes independently).

**3. OWNER GATE — Pi pull.** Self-contained (a Pi has no ecosystem checkout), on the newest image:

```bash
docker pull ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23 -c "import platform, torch; print(platform.machine(), torch.__version__, torch.version.cuda)"
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23 -c "import importlib.metadata as m; n=sorted(d.metadata['Name'] for d in m.distributions()); print([x for x in n if x.lower().startswith(('nvidia-','cuda-')) or x.lower()=='triton'])"
```

Expect `aarch64 2.12.0+cpu None` and `[]`, and a ~270 MB pull. Precondition: a **64-bit** Pi OS — the
index carries `linux/arm64` only (no `arm/v7`), so a 32-bit OS cannot pull it. Two notes: (a) item 6b bumps the image
to torch 2.14.0, so a pull today tests an image that bump supersedes — at ~270 MB a second pull is
cheap, but doing 6b first avoids it; (b) the predecessor made the Pi pull the gate for **Wave 3's
pin**, and that dependency stands: do not pin `docker-compose.yml` to a release nobody has run on a Pi.

**4. Wave 3 — juniper-deploy repin: BLOCKED** until all five repos cut a release; detect with
`gh release list --repo pcalnon/<repo> --limit 3`. **State at 2026-09-09 07:35 UTC**: cascor v0.11.0
(tag on `5eb6f144`, includes #634 → image published), data v0.14.0 (tag on `e769999d`, the #387
merge → image published), canopy v0.7.0 (tag on `d8b1592d`, BEFORE #603 → **no image**, and that tag
can never carry one), worker still v0.5.0 (the CPU fix and the workflow are unreleased — the image
exists only as `dispatch-*` tags), recurrence app still `juniper-recurrence-v0.4.0` (the model and
client v0.3.0 Releases of 07:22 / 07:31 UTC are not the app and were skipped by the guard). **Wave 3
therefore still needs three Releases — worker (> v0.5.0), canopy (any `v*` tag cut from `main` at or
after `134d375f`, i.e. after #603; the 0.7.0 tag can never carry an image), recurrence app
(`juniper-recurrence-v` > 0.4.0) — plus the Pi pull of item 3.** All owner actions.
cascor's and canopy's CHANGELOGs list the workflow under `[Unreleased]` although cascor's 0.11.0 tag
ships it — cosmetic, the release author's call. Carried from the predecessor (verified 2026-09-09):
`docker-compose.yml` has **13 `image:` lines, 9 Juniper, 5 unique** — canopy ×3 (L620/764/855, identical
`build:` args, differ in `environment:`), cascor ×2 (L197/391), data ×2 (L134 and L487), worker ×1
(L334), recurrence ×1 (L556); **`demo-seed` (L487) has no `build:`** and reuses the data image with an
`entrypoint:` override, so "keep `build:`" is inapplicable there and must be decided explicitly. The
unstated hazard in "keep `build:`": once `image:` is a release ref, a local `docker compose build`
stamps the **dev tree** with the **release tag** and `docker compose up` silently prefers it — what
`make doctor`'s stale-image detection exists to catch. Wave 3 also owes juniper-deploy's own
`Dockerfile.test` runner image (context at `docker-compose.yml:1061`) and the pull-the-published-images
integration test (plan D-1).

**5. Wave 4 — Docker Hub** as a second push target (D-2). Needs a `DOCKERHUB_TOKEN` secret per repo;
answer OQ-1 first. Not started; the worker workflow header still says "phase 2, not in this file".

**6. Follow-ups that need no owner (do these):**

- **6a. Harden the two checks** (found by the refuter lane; both real, both small):
  (i) `check_image_cpu_only.py` forbids `nvidia-*` and `triton` but **not `cuda-*`** — the real CUDA
  image also carried `cuda-toolkit`, `cuda-bindings` and `cuda-pathfinder` (~6.6 MB; no current lock
  pins them, but the contract says "no CUDA stack" and the verification grep below counts `^cuda-`).
  (ii) The identity step should assert **one linux image per pushed digest, with `architecture` equal
  to the digest file's name** (`/tmp/digests/<arch>`), so a multi-platform index could never count an
  image the census did not run on as verified. It applies when the pushed digest is an index
  (provenance on, the default); a bare image digest falls through to the plain identity comparison.
  Round 2 re-ran the hardened loop's logic on run 34294654855's real digests (no `variant` fields):
  it passes there and fails closed on the plausible bad shapes. Scripted, one identical change per repo:
  `util/ad-hoc/2026-09-08_harden_publish_image_checks.py --workflow … --census … [--tests …]`
  (`--tests` extends the census sample with `cuda-toolkit` / `cuda_bindings`, adds a regression test
  for the family and pins the per-digest assertion). **Done for four repos on 2026-09-09 — worker#178,
  data#391, cascor#637, recurrence#160, each from a fresh worktree off `origin/main`, auto-merge
  armed; worker#178 MERGED `fde50791`, data#391 MERGED `910f7a55`, cascor#637 MERGED `f96551e1`;
  recurrence#160 green but `update-branch`'d three times behind a busy `main` (model/client v0.3.0
  release proposals) and still in CI at writing**: workflow + census + a CHANGELOG `Fixed` bullet; worker/cascor pytest totals 21→23 / 24→26
  green (parametrized cases counted); recurrence also corrects the pyproject comment ("two" → three
  skipped-green runs). actionlint is clean on worker/cascor; data/recurrence show a PRE-EXISTING
  SC2129 style note on the provenance step (present on `main`, not a required check). The two release
  images of 07:15 UTC were verified by the UN-hardened check — see § Where this stands. **Canopy's
  landed too: #608**, opened 08:00 UTC once #603 was on `main` (the block the script rewrites is the
  one #603 added), from `worktrees/juniper-canopy--fix--harden-cpu-only-checks--20260909-0259--134d375f`:
  script with `--workflow --census --tests`, the same CHANGELOG bullet, `conda run -n JuniperCanopy1
  python -m pytest src/tests/unit/test_dockerfile_cpu_torch_pin.py` total 20→22, actionlint clean,
  auto-merge armed. Once #160 and #608 merge, item 6a is closed in all five repos: the census forbids
  `cuda-*` everywhere and every merge job asserts one linux image per pushed digest. If either has to
  be redone, the recipe is the other PRs' — the script refuses on a file that already carries the
  new block ("expected exactly one occurrence … found 0").
- **6b. Worker torch 2.12.0 vs CI's unpinned torch.** `ci.yml` tests against `pip install torch`
  (2.14.0 today) while the image pins the lock header's 2.12.0 — tested ≠ shipped. Bump the override in
  `requirements-cpu.lock`'s header recipe to 2.14.0, regenerate, and move `ARG TORCH_VERSION` with it
  (the drift test fails otherwise). Trap: the header recipe has no `--upgrade`, and `uv pip compile`
  reads the existing `-o` file as a constraint — delete or `--upgrade` first.
- **6c. `lockfile-update.yml` regenerates only `requirements.lock`** in the worker AND cascor, so each
  CPU lock drifts on the next dependabot bump. cascor's derivation is constraint-mode
  (`--constraint requirements.lock --override torch==X+cpu --extra-index-url <cpu>`), hence a
  deterministic second step; that workflow commits via GraphQL `createCommitOnBranch`, so the second
  file must go through the same signed path. The first releases (cascor 0.11.0, data 0.14.0) were cut
  with the CPU locks as they are; 6c stays open — the next dependabot bump on either repo drifts them.
- **6d. CI `docker-build` jobs** (canopy, cascor, data, recurrence-app) vs the new PR arms — decision
  this session: KEEP both (they test container start + health; publish-image tests both arches + the
  CPU contract); marginal cost is one extra amd64 build on PRs touching image inputs. Two real releases
  have now published (cascor 0.11.0, data 0.14.0), so the revisit is due.
- **6e. recurrence's Dockerfile installs from PyPI with no lock**, so its image changes when PyPI does.
  Do: compile `juniper-recurrence/requirements.lock` (`uv pip compile pyproject.toml --extra
  observability --python-version 3.13 -o requirements.lock`, run inside `juniper-recurrence/`; delete
  any existing output file first — uv reads it as a constraint), install it in the Dockerfile with
  `-r`, and run `util/ad-hoc/2026-09-08_lock_wheel_availability.py --python 3.13 --arch aarch64` on it
  before the PR arm builds arm64. Until then, re-run that pre-flight on a fresh resolution before any
  `juniper-recurrence-v*` Release.
- **6f. Drop the anyio filter** added by recurrence#154 once the resolved starlette imports
  `anyio.from_thread.BlockingPortal` (starlette `master` already does; wait for the release).
- **6g. `juniper-lint-workflow-paths` false positive** — filed as juniper-ml#1836. It flags
  `ci-recurrence-model.yml`'s `tests/test_readouts_mlp.py`, which **exists** at
  `juniper-recurrence-model/tests/test_readouts_mlp.py` and runs under the job's
  `working-directory`. **Do not "fix" it by prefixing the path in the workflow** — that breaks the lane.

**7. Owner decisions — surface, do not guess** (plan §6): OQ-1 Docker Hub posture; OQ-2 a `-cuda`
variant (the CUDA images were bugs, not OQ-2 being answered); OQ-3 Pi disk/bandwidth as well as RAM;
OQ-4 a versioned stack manifest.

### Key context — settled; do not re-litigate

- **Two load-bearing workflow properties** (predecessor): tags are written exactly once, by the merge
  job, from digests both arches pushed (no tag race); the `pull_request` arm builds both arches and
  pushes nothing. Do not simplify either when touching the five copies.
- **Tag guards on both jobs, everywhere.** `latest` is gated on the EVENT, not the tag, so a sibling
  package's release (`juniper-cascor-model-v*`, `juniper-recurrence-model-v*`) would republish
  `:latest` with the run reading SUCCESS. REQUIRED in cascor (`v`) and recurrence
  (`juniper-recurrence-v`), defensive elsewhere.
- **recurrence uses the `match` ATTRIBUTE on `type=semver`** (`match=juniper-recurrence-v(.*)`),
  verified in metadata-action `meta.ts` at the pinned SHA; `type=match` cannot emit
  `{{major}}.{{minor}}`. Because an unparseable tag only WARNS, every merge job **fails a release that
  produced no `X.Y.Z` tag**.
- **CMD vs ENTRYPOINT.** Only the worker and recurrence have an ENTRYPOINT (need `--entrypoint
  python`); cascor/canopy/data are CMD-only — `CMD ["python", "src/server.py"]` / `["python",
  "src/main.py"]` / `["python", "-m", "juniper_data"]` on `main` — and their `--help` assertion was
  replaced by importing the app (`import cascade_correlation, api, snapshots` / `import juniper_canopy`
  / `import juniper_data`).
- **`paths:` is per repo and covers everything the Dockerfile COPYs** — canopy's includes
  `conf/app_config.yaml`, `conf/logging_config.yaml`, `conf/layouts/**`.
- **arm64 is a download everywhere**: `util/ad-hoc/2026-09-08_lock_wheel_availability.py` checked every
  pin (canopy 59, data 56, cascor-CPU 53; for recurrence, which has no lock, the 31 distributions a
  `uv pip compile --extra observability --python-version 3.13` resolved to on 2026-09-08 — re-run it,
  the resolution is not preserved) for a cp31x/abi3 manylinux aarch64 wheel or pure Python. All OK.
- **A green CI run that SKIPPED its tests is not evidence.** recurrence's app tests were skipped by the
  `changes` filter on 2026-09-02, 09-06 (×2) and 09-07; the last real execution was 2026-08-31. anyio
  4.15.0 (2026-09-02T21:46Z) deprecated the `anyio.abc.BlockingPortal` alias via a lazy-import shim
  that starlette 1.6.0's `testclient` still touches at import; under `filterwarnings=error` every test
  module that imports `TestClient` died at collection (8 errors) on the first PRs to execute the suite
  again — #152, #153, #156. Fixed by recurrence#154 (message+category filter). #154's comment says
  "two" skipped-green runs; it was three since anyio 4.15.0 (6a fixes the comment).

### Traps that cost this session time

- **An API rebase that resets a PR branch to its base SHA auto-closes the PR** (head == base, zero
  commits) before the recommit lands; `gh pr reopen` recovers it. Use the temp-branch sequence instead:
  `POST git/refs` (temp at `main`) → commit all files there → `PATCH git/refs/heads/<pr-branch>
  -f sha=<FULL 40-char sha> -F force=true` → `DELETE` the temp ref. A 12-char sha is rejected (HTTP 422).
  Auto-merge survived the force-move.
- **A release-proposal commit on `main` dirties every open PR that touched `CHANGELOG.md` or
  `AGENTS.md`** — cascor#634 twice (#631, then the v0.11.0 proposal #635), canopy#603 (the v0.7.0
  proposal #606). `update-branch` cannot resolve it. Merge by hand and force-move: the PR's Unreleased
  entries go ABOVE the new version header — structurally: main's text through the blank line after
  `## [Unreleased]`, then the PR's entries, then main from its first `## [X.Y.Z]` header on (canopy's
  `[Unreleased]` is at line 10, cascor's at line 8: never copy line numbers between repos) —
  `AGENTS.md` keeps main's version line plus the PR's row; verify with two diffs (vs main
  shows only the additions; vs the PR branch shows only the header / version line), then the
  temp-branch sequence above. The proposals arrive minutes after the PR goes green, so re-probe
  `mergeStateStatus` right before acting — a watcher that reported GREEN can be stale by then.
- **Read the workflow header comments before editing `publish-image.yml`** — they carry the editing
  traps (why `--index-url` breaks the build, why tags are written once, why `latest` is event-gated),
  and the five copies must stay byte-identical except the per-repo lines. Two of those traps in one
  line each: **a digest push cannot carry a tag** (the build jobs push `push-by-digest=true,
  name-canonical=true` with empty `tags:`, so the merge job is the only tag writer — the mechanism
  behind load-bearing property 1); and **GitHub's `cond && 'a' || 'b'` is not a ternary** — an empty
  `'a'` falls through to `'b'`; the workflows use `enable=` / `if:` instead, keep it that way.
- **Tests run under each repo's conda env**: canopy `conda run -n JuniperCanopy1 python -m pytest …`
  (the unsuffixed `JuniperCanopy` does not exist), cascor `JuniperCascor1`; worker/data/recurrence
  under the active interpreter. **`pre-commit run --files <paths>` lints untracked files;
  `--all-files` silently skips them** and both print Passed — the handoff and the ad-hoc scripts are
  untracked until the closing PR lands.
- **`Verify AGENTS.md Last Updated` compares to the runner's UTC date** and is red on any PR that
  touched `AGENTS.md` and straddles midnight UTC (cascor#634 and canopy#603 went red on the rollover to
  2026-09-09). Not a required check in either repo; not worth a CI cycle.
- **The worktree-isolated Bash classifier is session-dependent.** This session was refused a `for`
  loop over `gh`, a heredoc chained with `&&`, and `M=…; sed … $M/file`; sibling `git -C` chains ran.
  Lane A's subagent was refused **every** `git -C <sibling>`. Do not rely on either posture.
- **A push-by-digest with provenance names an index, not an image** — see item 2.
- **`gh run list --limit 1` right after `gh workflow run` can return the previous run**; match on
  `headSha`. **`gh run view --log` intermittently returns empty** (predecessor): use
  `gh api repos/O/R/actions/jobs/<id>/logs` and `…/jobs/<id>` for step conclusions.
- **`docker image inspect --format {{.Size}}` and `docker images` disagree on this host** (312 MB vs
  1.47 GB for the same image: compressed content size vs unpacked). Say which you mean.

### Corrections to the predecessor

- The Wave 2 table's **"Torch-bearing? canopy: no"** described the package, not the image; the image
  installs torch and is now pinned. **"recurrence: check"** → resolved: no torch, by design.
- The predecessor's ruled fix was correct and sufficient for the WORKER shape; it does not cover the
  cascor shape (a lock that pins the CUDA stack outright), which needed a second lock.
- "A worktree-isolated session refuses `git -C <other repo>`" is not a stable rule — see traps.
- `IMAGE_NAME: ${{ github.repository }}` "derived and already correct everywhere" — confirmed for all four.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
# PR states (issue as separate plain commands in a worktree-isolated session)
gh pr view 175 --repo pcalnon/juniper-cascor-worker --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'   # MERGED 86733960e6ca
gh pr view 176 --repo pcalnon/juniper-cascor-worker --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'   # MERGED 9890a23f131c
gh pr view 385 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'            # MERGED 0f177990dff3
gh pr view 387 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12] // "-")"'
gh pr view 153 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'      # MERGED 7d0291f182c0
gh pr view 154 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'      # MERGED 63974b3294cb
gh pr view 634 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12] // "-")"'
gh pr view 603 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12] // "-")"'

# The published worker image, anonymously
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor-worker:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor-worker/tags/list    # dispatch-3d81f2c, dispatch-8673396, dispatch-9890a23
docker manifest inspect ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23 | grep -c '"architecture": "a'   # 2 (amd64, arm64; the two attestation entries are unknown/unknown)
docker run --rm -i -e EXPECT_TORCH=2.12.0+cpu --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:dispatch-9890a23 - < juniper-cascor-worker/util/check_image_cpu_only.py
gh run view 34294654855 --repo pcalnon/juniper-cascor-worker --json jobs --jq '.jobs[] | "\(.name)\t\(.conclusion)"'   # three rows, all success

# The first release images (cut by the owner 2026-09-09 07:15 UTC) and the guard proof
gh release list --repo pcalnon/juniper-cascor --limit 1      # v0.11.0  2026-09-09T07:15:09Z
gh release list --repo pcalnon/juniper-data --limit 1        # v0.14.0  2026-09-09T07:15:05Z
gh release list --repo pcalnon/juniper-canopy --limit 1      # v0.7.0   2026-09-09T07:15:13Z  (no image: #603 was not on main)
gh run list --repo pcalnon/juniper-cascor --workflow publish-image.yml --event release --limit 1 --json databaseId,conclusion --jq '.[] | "\(.databaseId) \(.conclusion)"'   # 34322913368 success
gh run list --repo pcalnon/juniper-data --workflow publish-image.yml --event release --limit 1 --json databaseId,conclusion --jq '.[] | "\(.databaseId) \(.conclusion)"'     # 34322906608 success
gh run list --repo pcalnon/juniper-recurrence --workflow publish-image.yml --event release --limit 2 --json conclusion --jq '.[].conclusion'   # skipped, skipped (model / client releases)
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor/tags/list           # 0.11.0, 0.11, latest
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-data:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-data/tags/list             # 0.14.0, 0.14, latest

# The three shapes, without pulling anything (pull the primaries first, or use gh api …?ref=main)
grep -c '^nvidia-\|^triton\|^cuda-' juniper-cascor/requirements.lock        # 19: the GPU lock pins the CUDA stack outright
gh api repos/pcalnon/juniper-cascor/contents/requirements-cpu.lock?ref=main --jq .content | base64 -d | grep -c '^nvidia-\|^triton\|^cuda-'   # 0 once #634 is on main
grep -n 'ARG TORCH_VERSION' juniper-cascor-worker/Dockerfile                # 41:ARG TORCH_VERSION=2.12.0
gh api repos/pcalnon/juniper-canopy/contents/Dockerfile?ref=main --jq .content | base64 -d | grep -n 'ARG TORCH_VERSION'   # 2.14.0 once #603 is on main
```

### Git state

Local `main` in every primary checkout is clean but **may be behind** (see the pull note at the top).
**No local branch was ever pushed**: every remote commit in this arc was created through the GitHub API
and is GitHub-signed. The five arc worktrees hold the same content as their PR branches but as
uncommitted changes (the worker's also has one unsigned local bookkeeping commit, `87380f5`, never
pushed, not the merged SHA). Leave them alone — cleanup is a separate, owner-signalled step, and
`worktree remove` deletes ignored files silently.

```
worktrees/juniper-cascor-worker--fix--cpu-only-torch-pin--20260908-0652--777e6578      [fix/cpu-only-torch-pin]        (#175 merged; remote branch deleted on merge; worktree also holds #176's content uncommitted)
worktrees/juniper-cascor--feat--publish-container-image--20260908-0708--d39d537e        [feat/publish-container-image]  (#634; local ref still at the fork point d39d537e)
worktrees/juniper-canopy--feat--publish-container-image--20260908-0708--eb05021d        [feat/publish-container-image]  (#603)
worktrees/juniper-data--feat--publish-container-image--20260908-0708--03b7548f          [feat/publish-container-image]  (#385 merged; worktree also holds #387's content uncommitted)
worktrees/juniper-recurrence--feat--publish-container-image--20260908-0708--e5679b00    [feat/publish-container-image]  (#153 merged)
```

The item-6a hardening worktrees, cut from each repo's `origin/main` on 2026-09-09 02:11 CDT (07:11
UTC; local branch `fix/harden-cpu-only-checks` in each, ZERO local commits ahead — the remote branch
of the same name holds the API-signed commit; the worktree files equal the PR content; they may be
BEHIND `origin/main` by the time you read this, which changes nothing):

```
worktrees/juniper-cascor-worker--fix--harden-cpu-only-checks--20260909-0211--9890a23f   (#178)
worktrees/juniper-data--fix--harden-cpu-only-checks--20260909-0211--e769999d            (#391)
worktrees/juniper-cascor--fix--harden-cpu-only-checks--20260909-0211--5eb6f144          (#637)
worktrees/juniper-recurrence--fix--harden-cpu-only-checks--20260909-0211--46f3faff      (#160)
worktrees/juniper-canopy--fix--harden-cpu-only-checks--20260909-0259--134d375f          (#608; cut 02:59 CDT after #603 merged)
```

Plus the predecessor's three arc worktrees and two older worker worktrees, unchanged. The worker
primary still has local branches `feat/publish-container-image`, `fix/publish-image-digest-tags` and
`fix/cpu-only-torch-pin`. Host docker daemon: scratch images `worker-cpu-check:local`,
`cascor-cpu-check:local`, `canopy-cpu-check:local` (1.47 / 1.73 / 1.92 GB unpacked), the pulled worker
tags `dispatch-8673396` and `dispatch-9890a23` (1.47 GB each), the two release images pulled for the
census (`ghcr.io/pcalnon/juniper-data:0.14.0` 785 MB, `ghcr.io/pcalnon/juniper-cascor:0.11.0` 1.73 GB),
and two `<none>`-tagged by-digest pulls of the worker — `ba60f1728c39` (8.05 GB, the CUDA image
`dispatch-3d81f2c` from the predecessor) and `ac84850668b6` (1.47 GB, the first dispatch's amd64
index). **Neither is dangling** (`docker images -f dangling=true` is empty), so `docker image prune`
reclaims nothing: remove them by image id (`docker rmi ba60f1728c39`). The juniper-deploy compose
builds also sit there untouched (`juniper-cascor:latest` at **8.7 GB** is the cascor CUDA shape, built
locally from the pre-#634 Dockerfile; `juniper-canopy:latest` 2.1 GB, `juniper-data:latest` 783 MB,
`juniper-cascor-worker:latest` 1.47 GB, `juniper-recurrence:latest` 361 MB) — not this arc's to delete.

juniper-ml: this handoff plus `util/ad-hoc/2026-09-08_lock_wheel_availability.py`,
`util/ad-hoc/2026-09-08_fix_publish_image_digest_identity.py` and
`util/ad-hoc/2026-09-08_harden_publish_image_checks.py` land via the closing PR on branch
`docs/handoff-2026-09-08-container-registry-wave-2` (find it with `gh pr list --repo pcalnon/juniper-ml
--head docs/handoff-2026-09-08-container-registry-wave-2 --state all`); the session's worktree is
`juniper-ml/.claude/worktrees/luminous-inventing-crystal`, on `main`, with those four files untracked.

**Conventions for landing follow-ups** (predecessor): item 6 lands in worker / cascor / recurrence /
data / canopy, never juniper-ml — read each target repo's `AGENTS.md`; worktrees per
`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`; PR base must be the default branch
(a required check enforces it); commits via the API helpers above.

---

## Validation record

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. Two
rounds, three lanes each; every lane read-only, briefed to refute, run as an independent subagent with
no access to this session's transcript. Reports came back as messages; the round-2 reports also exist as
files only in the session scratchpad (not archived).

**Round 1 — on the first draft, 2026-09-09 (UTC morning).** Lane A (grounding): **FAIL** — two refuted
claims: the recurrence lint "file does not exist" (a lint false positive: the file is under the job's
`working-directory`; filed juniper-ml#1836) and "two" skipped-green recurrence runs (three). Lane B1
(executability + amputation): **NOT SAFE on both** — six majors (the `docker run` form for ENTRYPOINT
images, a Pi command that needed a checkout, primaries behind origin, data's unstated dispatch
precondition, ambiguous owner-gate wording, no `gh run view --log` fallback) and two amputations (the
Definition of Done, Wave 4). Lane B2 (refuter): **conclusions SURVIVE** with precision fixes (two shapes
shipped CUDA, not three; the torch-dependent lock pin; "linux entries"; size units; commit counts) and
two real check gaps — the census let `cuda-*` through, and the identity step needed a one-image-per-digest
assertion — which became item 6a. The draft was rewritten wholesale.

**Round 2 — on the corrected document, launched ~07:10 UTC, back by ~07:50 UTC; brief: "the fix pass
is the least trustworthy part".** Lane A (grounding, 84 claims): **FAIL** — 78 CONFIRMED against primary
sources (pip-log lines verbatim, lock counts 19/72/53/0, sizes recomputed in SI units from registry
layer sums, test counts via `--collect-only`, compose line numbers, `match=` in `meta.ts`), 3 REFUTED:
the Release state (the owner cut cascor v0.11.0, data v0.14.0 and canopy v0.7.0 at 07:15 UTC, twelve
minutes before the save), "~02:30 UTC" (local time), and "`docker image prune` reclaims the 8.05 GB
image" (a by-digest pull, not dangling — needs `docker rmi <repo>@sha256:…`); 1 partly refuted (a
canopy dispatch before #603 is refused, it cannot "write the tag then fail"). Lane B (fold-in /
executability / amputation): **FOLD-IN NOT SAFE** (one major — the predecessor's filename sat outside
the paste region — and seven round-1 minors dropped at the summary stage), **EXECUTABILITY NOT SAFE**
(the same Release finding; `-e EXPECT_TORCH=<a | b>` is a redirect if pasted; the path rule missed
`util/`; `3286b75` is the proposal merge, not the tag; test-count phrasing; docker inventory),
**AMPUTATION SAFE conditional on the filename fix** (six mechanism trims accepted — the predecessor is
now named inside the paste region as their home); all 14 annotated verification expectations
reproduced, the CMD/ENTRYPOINT split confirmed for all five Dockerfiles and the published worker
image's config on both arches, the Pi commands valid. Lane C (refuter): **CONCLUSIONS SURVIVE** — twelve
findings, three major (the Release state; CDT/UTC mixing; the CHANGELOG merge recipe was canopy's
layout, not general) and nine minor (package visibility is observed, not inherited; the canopy dispatch
consequence; stale PR states; 6a(ii) applies to index digests only, and passes on run 34294654855's real
digests; canopy's "could not" rests on the wheel metadata, not the index; pip settled on 2.12.1 after
rejecting 2.14.0/2.13.0; ~3 GB not ~2.4 GB; a 32-bit Pi OS cannot pull; 6d is due; test totals include
parametrized cases). Every item from all three lanes is folded above or, for AMP-6/7, accepted with the
reason stated.

**Author's re-verification after round 2**: releases, release runs and GHCR tag lists re-probed (see
§ Verification commands); both release images pulled and the HARDENED census run inside them (data
`torch=absent distributions=60 cuda_stack=0`, cascor `torch=2.14.0+cpu (cuda=None) distributions=57
cuda_stack=0`, both "CPU-only contract holds"); `docker images -f dangling=true` is empty.

**Known deviation**: the goal statement is ~5,100 words against the ~1,200-word target. The arc spans
five repos with four owner gates and the successor cannot read this session; round 1's amputation lane
classified every predecessor trim as a loss, so I chose length over amputation. The successor may split it.
