# Container Registry Publishing — Design of Record

**Project:** Juniper (ecosystem-wide)
**Author:** Paul Calnon
**Date:** 2026-09-05
**Status:** ACCEPTED — decisions ratified by the owner 2026-09-05. **Waves 1 and 2 complete**
(all five repos carry `publish-image.yml`). **ALL FIVE release images are published** —
`juniper-cascor:0.11.0`, `juniper-data:0.14.0`, `juniper-recurrence:0.5.0`,
`juniper-canopy:0.8.0` (cut 2026-09-12, also item 1's first publish — package came up
**public**, confirmed by an anonymous pull), `juniper-cascor-worker:0.6.0` (cut 2026-09-15,
publish run 35033610624 all three jobs green; censused from the pulled image:
`torch=2.14.0+cpu (cuda=None) distributions=24 cuda_stack=0`, *CPU-only contract holds*).
**WAVE 3 IS COMPLETE (2026-09-17).** All three of its items shipped, and
`juniper-deploy/docker-compose.yml` now carries **ten** Juniper `image:` lines, every one a
published registry ref and none a local build-output tag:

| item | PR | what |
| --- | --- | --- |
| the pin | juniper-deploy#215 | all 9 sites → `ghcr.io/pcalnon/<name>:X.Y.Z` |
| D-1 integration check | juniper-deploy#217 | `Published Image Refs` CI job + `scripts/verify_published_images.py`, 6 negative controls |
| `Dockerfile.test` runner | juniper-deploy#219, #220, #221 | `ghcr.io/pcalnon/juniper-deploy-test:0.3.0`, published by Release `v0.3.0` |

The **Pi-pull gate was WAIVED by the owner 2026-09-15** — see §5.1, which also settles a
contradiction the archived chain had left open.

**Two defects were found by RUNNING the artifacts, not reading them**, and neither would have
surfaced from the pin alone:

- **The containerized test runner had run ZERO tests since 2026-03-13.** Commit `65def44`
  (*"fix: resolve conftest import errors in test suite"*) added `tests/conftest.py`'s
  `from constants import ...` **and** `pyproject.toml`'s `pythonpath = ["tests"]` together;
  `Dockerfile.test` never copied `pyproject.toml`, so the container died at conftest import every
  time while the host path was fine. Six months, unnoticed, because nothing asserted the suite was
  runnable — which is why the publish path now asserts exactly that (juniper-deploy#219).
- **juniper-deploy's build context holds `secrets/` with eight live credential files, and there was
  no `.dockerignore`.** Docker does not honour `.gitignore`. Nothing had leaked, but the context
  was about to be published publicly. Fixed with an explicit COPY allowlist *and* a `.dockerignore`,
  with CI asserting no `secrets/` or `.git` reaches the image.

A sibling defect found while auditing the pin's consumers is fixed in juniper-deploy#216:
`k8s/helm/juniper/values.yaml` rendered its four Juniper images with **no registry** (`registry: ""`
→ `juniper-data:0.6.0`, which Kubernetes resolves against `docker.io/library`) and tags 3–8 minor
versions stale. Fixed **per block**, not via `global.imageRegistry` — that key is a Bitnami
convention the bundled redis subchart also honours, and setting it rewrites redis to
`ghcr.io/pcalnon/bitnami/redis:...`, which does not exist and makes `helm template` fail outright.

> **juniper-deploy's release notes are NOT in `notes/releases/`, deliberately.** They live on the
> GitHub Release (`v0.3.0`). The archive convention is scoped to *"Every PyPI deploy"*, and
> juniper-deploy publishes no PyPI package — `util/release_train/registry.yaml` holds only the 18
> publishable packages, so `util/release_train/archive_guard.py` (a **REQUIRED** status check)
> rejects `RELEASE_NOTES_juniper-deploy_v0.3.0.md` as naming an unregistered package. The guard is
> right; do not register a non-PyPI repo to work around it.
**Wave 4 committed** (OQ-1 ruled 2026-09-11, §6), blocked on the five `DOCKERHUB_TOKEN`
secrets. Those are now **environment** secrets in a tag-restricted `dockerhub` environment, not
repository secrets. The owner ruled this on 2026-09-22 (§3 of
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`). Last state refresh: **2026-09-22** — the §5 wave table's Wave 1 and Wave 2 rows had
gone stale against this Status line and are now correct, and canopy's pin has already drifted
(see the note under §5). **New §5.2** records the image hardening: both publish-trap classes
swept 2026-09-21 and now enforced in CI across all five image repos, plus the root-anchoring
finding that swept up 766 authkey-bearing files in juniper-cascor.

> **The worker release is worth a note before anyone reads its version number as a code change.**
> Across `v0.5.0...main` there were 43 commits and 23 files with **zero** inside the packaged
> source (`juniper_cascor_worker/`) and zero in `pyproject.toml`, so the 0.6.0 PyPI wheel is
> byte-identical to 0.5.0's apart from the version string, and `util/release_train/detect.py`
> classifies the package `UP_TO_DATE` — correctly. It was released because `release: published`
> fires **both** `publish.yml` and `publish-image.yml`, and Wave 3 needs a released `X.Y.Z` image
> ref. That overloading is a property of D-1 and will recur whenever an image input moves without
> a library change; worth an OQ if it happens a third time.
>
> **The wheel SHIPPED 2026-09-17, and the claim above now holds against the published bytes**
> rather than the git diff that predicted it — which matters, because a checkout is not a
> deployment (juniper-model-core 0.3.1 shipped stale under an unchanged version while the repo
> was already correct). PyPI serves `juniper-cascor-worker` **0.6.0**; run `35033610592` is
> `completed/success`. Both wheels were downloaded and compared member-by-member by SHA-256
> (`util/ad-hoc/2026-09-17_verify_worker_060_wheel.py`): **all 10 packaged module files are
> byte-identical**, 16 members each, and only `METADATA` / `WHEEL` / `RECORD` differ. The check
> fails if the metadata is *also* identical, since that would mean the two downloads are the
> same artifact and the comparison proved nothing.
>
> **The wheel was also screened for the canopy packaging-omission class and is clean**
> (`util/ad-hoc/2026-09-17_wheel_import_completeness.py`). Three flags were raised and all three
> run to ground: `candidate_unit.candidate_unit` and `utils.activation` are provided by the
> declared `juniper-cascor-model` dependency (whose import names are not its PyPI name — the
> screen's known false-positive class), and `cascade_correlation.cascade_correlation` is
> **deliberately optional**, imported inside `try/except ImportError` at `worker.py:746` and
> `:774` and re-raised as *"CasCor codebase not found. Ensure the JuniperCascor src directory is
> on sys.path"*. That is consistent with the ecosystem map's "architectural only — no code import
> dependency": it is a deployment-time path, not a packaging one.
>
> **The screen is calibrated, not assumed.** Its first version keyed only on imports prefixed
> with the distribution's own package name and found **1** of canopy 0.8.0's ten known omissions,
> because a module a wheel forgot to ship cannot appear in that wheel's own name set. The current
> version resolves bare imports against `Requires-Dist` and finds **11** genuine canopy omissions
> (`canopy_constants`, `settings`, `model_registry`, …) alongside ~6 third-party false positives.
> It is a **screen, not a proof**, and it over-reports by design; run its canopy positive control
> (`--expect-missing`) before believing a clean verdict from it.
**Scope:** publishing the five Juniper service images to container registries

---

## 1. Why this exists

`juniper-deploy/docker-compose.yml` carries nine `image:` lines, every one of them
`<name>:latest`, and every one paired with a `build:` stanza pointing at a **sibling
working copy** (`context: ../juniper-canopy`). Nothing is published anywhere.

That has three consequences worth naming, because only the first is obvious:

1. **The stack cannot be run on a machine that is not this workstation.** Every host needs
   all sibling repos checked out at compatible commits before `docker compose up` means
   anything.
2. **`:latest` is not a version.** It names whatever the local build produced, so two hosts
   running "the same stack" have no way to discover that they are not.
3. **The tag pin that was filed as the fix is not one.** The deferred item entering this
   work read *"`image: juniper-canopy:latest` wants a pinned release tag."* It does not:
   with no registry, `juniper-canopy:latest` is a **local build-output tag**, and renaming it
   `v0.9.0` would change nothing about what the build contains. The real question was
   whether Juniper should publish images at all, which is what this document answers.

## 2. What already exists (the work is smaller than it looks)

Measured 2026-09-05, not assumed:

| Fact | Consequence |
| --- | --- |
| Nine `image:` lines are **five unique images** (canopy ×3 full/demo/dev, cascor ×2 main/demo) | Five workflows, not nine |
| canopy, cascor, data and recurrence-app **already build their image in CI**, smoke-test it, and discard it | This is "keep the artifact", not "add a build" |
| Dockerfiles already carry full OCI labels, incl. `org.opencontainers.image.source` | GHCR repo-linking works with no Dockerfile change |
| Dockerfiles already accept `GIT_SHA` / `BUILD_DATE` / `APP_VERSION` build args | Provenance is already wired; compose already passes them |
| All repos are **public**; every service repo publishes to PyPI on `release: published` | GHCR is free, and a uniform release event already exists |
| juniper-deploy has **no service Dockerfiles** — only `Dockerfile.test` | It is a consumer, not a producer, of service images |

## 3. Decisions

### D-1 — Publishing lives in the **owning repo**, not in juniper-deploy

Each service repo publishes its own image on its own `release: published` event.

**Why.** The deciding question is not where credentials live, it is **what a tag means**.
The repos already have release-driven versioning: Release → tag → `publish.yml` → PyPI.
Publishing images on that same event makes **image tag ≡ PyPI version ≡ git tag by
construction**, not by a convention someone must remember.

juniper-deploy cannot do that. It does not know when canopy cuts a release, so publishing
from there yields either tags meaning "whatever main was that day", or a cross-repo
dispatch mechanism to learn about releases — machinery whose only purpose would be to
recover information the owning repo already has.

Two supporting reasons: the `org.opencontainers.image.source` label already names the
owning repo (publishing elsewhere would either misstate provenance or require changing it),
and GHCR from the owning repo needs **no secret at all** — `GITHUB_TOKEN` with
`packages: write`.

**The rejected alternative's one real advantage** was centralising the *Docker Hub*
credential in a single repo instead of four. That is genuine but small: GHCR needs none,
and four `gh secret set` calls are scriptable for rotation.

**juniper-deploy keeps a real role:** it publishes its own `Dockerfile.test` runner, pins
the consumed tags, and becomes the natural home for an integration test that pulls the
**published** images — a stronger check than building from `../sibling` paths.

### D-2 — GHCR first, Docker Hub second

Phase 1 targets `ghcr.io/pcalnon/<image>` only. Phase 2 adds a second login+push to
`docker.io/<user>/<image>` in the same workflow.

**Why.** GHCR needs no provisioned secret, so phase 1 proves the whole pipeline —
multi-arch build, digest merge, manifest verification, consumption from compose — with
zero credential surface. Docker Hub then becomes a second push target against a tagging
scheme already settled, rather than a variable in the same experiment.

Note for phase 2: cascor and cascor-worker are torch-bearing and therefore multi-GB.
Docker Hub's storage and pull-rate posture for a personal account should be checked before
that push is added, not after.

> **Superseded in part, 2026-09-11.** "Multi-GB" was true of the CUDA images, which were
> **bugs** — see the three-shape CUDA finding. The published CPU-only worker is **312 MB
> compressed** (amd64; 270 MB arm64), not 2.86 GB. The size premise behind OQ-1's caution
> no longer holds, which is why OQ-1 could be ruled rather than deferred again. The
> pull-rate posture was checked (numbers in §6 OQ-1) and is the part that still matters.

### D-3 — Release-only trigger; tags `X.Y.Z`, `X.Y`, `latest`

**Why.** Mirrors the PyPI discipline exactly: only released code is published, so nothing
unreviewed reaches a registry and every tag is reproducible from a git tag. A `:main` /
`:edge` arm was considered and rejected for now — it would push multi-GB torch images on
every merge for a consumer that does not yet exist.

### D-4 — `linux/amd64` **and** `linux/arm64`, for all five images

**Why — the fleet requires it.** The consuming hosts are:

| Host | Arch | Role |
| --- | --- | --- |
| Raspberry Pi cluster, 8+ nodes (Ubuntu RasPi image or 64-bit RaspiOS) | arm64 | cascor-workers; ideally **any** stack component |
| This workstation (Ubuntu) | amd64 | multiple isolated full stacks; **GPU, natively** |
| Intel MacBook (macOS ≤ Sequoia) | amd64 | full stack; multiple workers |
| Additional server (Ubuntu server/workstation) | amd64 | full stack, components, or workers |

An amd64-only worker image simply would not run on the cluster the component exists to
feed. Uniform multi-arch is chosen over "arm64 only where it is cheap" because the Pi nodes
should be able to run any component, and a two-tier rule is one nobody remembers.

**Why it is cheap — this was the objection, and it was measured before being accepted.**
The natural fear is that torch compiles for hours under QEMU. Both halves are false:

* `torch-2.11.0+cpu-cp314-cp314-manylinux_2_28_aarch64.whl` **exists** on the PyTorch CPU
  index and matches the images' `python:3.14-slim` ABI. torch is downloaded, never built.
* The two pins that could **not** fall back to a source build both ship cp314 aarch64
  wheels: `pydantic-core==2.46.4` — which needs Rust, absent from a slim image, so a
  missing wheel would be a *hard failure* rather than a slow one — and `numpy==2.4.4`.
* `requirements-cpu.lock` carries no `platform_machine` markers and no arch-specific pins.
* There is **no emulation at all**: `ubuntu-24.04-arm` is GA and free for public repos, so
  each arch builds on its own native runner and the digests are merged afterwards.

### D-5 — GPU is out of scope, and that is not a deferral of something already working

Nothing in the container path touches GPU today: `docker-compose.yml` has no `runtime:
nvidia`, no device reservations, and the cascor / worker Dockerfiles install CPU-only torch
*deliberately* (`# Install CPU-only PyTorch first (avoids pulling CUDA which is ~4 GB)`).
Workstation GPU work runs natively in conda envs.

So multi-arch CPU images regress nothing. A `:X.Y.Z-cuda` variant is a **separate
decision**: it doubles the build matrix for the two torch images and adds multi-GB CUDA
layers, in exchange for a containerised GPU path that does not exist yet.

## 4. The workflow pattern

Reference implementation:
`juniper-cascor-worker/.github/workflows/publish-image.yml` (juniper-cascor-worker#172).

```
on:
  release: [published]      -> build BOTH arches, push by digest, merge, tag
  pull_request:             -> build BOTH arches, push NOTHING, smoke-test each
  workflow_dispatch:        -> opt-in push for a manual dry run

permissions: { contents: read, packages: write }     # no secrets

build   (matrix: ubuntu-24.04 / ubuntu-24.04-arm)    push-by-digest
merge   (needs: build)                               imagetools create + verify
```

Two properties are load-bearing and should survive replication:

**Tags are written exactly once.** Both arch jobs push **by digest**; only the `merge` job
applies tags. Two jobs pushing the same tag would race, and the loser's arch would vanish —
leaving a single-arch image wearing a multi-arch tag, which fails only on the host that
needs the other arch.

**The `pull_request` arm is not decoration.** A release-only workflow's first run is
otherwise also its first test: a broken Dockerfile or a missing arm64 wheel would surface
*on the tag*, at deploy time, with no way to fix it in place. Building both arches on every
PR that touches image inputs makes the build the test and leaves only the push gated on the
release.

The merge job additionally inspects the manifest and fails unless it lists exactly
`amd64,arm64`. A manifest that exists is not a manifest that is complete, and the place not
to discover that is on a Pi.

## 5. Rollout

| Wave | Repo | Status |
| --- | --- | --- |
| 1 (pilot) | juniper-cascor-worker | **COMPLETE.** `publish-image.yml` landed as worker#172; the CUDA-contamination fix as worker#175. Image `ghcr.io/pcalnon/juniper-cascor-worker:0.6.0` published 2026-09-15 (run `35033610624`, three jobs green), censused CPU-only from the pulled artifact |
| — | *verify: pull and run on a Pi node* | **WAIVED as a Wave 3 gate, owner, 2026-09-15 (§5.1).** Re-filed as the gate on **first Pi deployment** and on **OQ-3**, which is what it actually tests. Target: `ghcr.io/pcalnon/juniper-cascor-worker:0.6.0`, the first **post-#179** image. Do **not** use `dispatch-9890a23`; it predates the torch 2.12.0 → 2.14.0 bump |
| 2 | juniper-cascor | **COMPLETE** — cascor#634; `juniper-cascor:0.11.0` published 2026-09-09 |
| 2 | juniper-canopy | **COMPLETE** — canopy#603; `juniper-canopy:0.8.0` published 2026-09-12, item 1's first publish (package came up **public**, proven by an anonymous pull). **Superseded by `0.8.1`** 2026-09-18 — see the pin-drift note below |
| 2 | juniper-data | **COMPLETE** — data#385; `juniper-data:0.14.0` published 2026-09-09 |
| 2 | juniper-recurrence | **COMPLETE** — recurrence#153; `juniper-recurrence:0.5.0` published 2026-09-10. Build context is **nested** (`juniper-recurrence/juniper-recurrence/`, via `APP_DIR`), which also means its `.dockerignore` lives in that subdirectory and **not** at the repo root — a repo-root sweep false-positives here |
| 3 | juniper-deploy — pin `image:` to registry refs, keep `build:` for local dev | **COMPLETE 2026-09-17.** Pin (#215, 9 lines) + D-1 check (#217) + `Dockerfile.test` runner published as `ghcr.io/pcalnon/juniper-deploy-test:0.3.0` (#219 / #220 / #221, Release `v0.3.0`) = **10** pinned lines. Sibling fix: helm `values.yaml` (#216) |
| 4 | Docker Hub as a second push target (D-2 phase 2) | **committed** — OQ-1 ruled 2026-09-11; blocked on the five `DOCKERHUB_TOKEN` secrets, `dockerhub` **environment** secrets per the 2026-09-22 ruling (§6 OQ-1). The five `dockerhub` environments were **created 2026-09-22** (tags only, no secrets yet) |

> **Wave 3's pin DRIFTED the day after it was declared complete, and no gate can see it.**
> juniper-canopy cut **`v0.8.1` on 2026-09-18** — the fix for canopy#631, this arc's own
> side-finding, where every published canopy wheel back to 0.5.0 omitted ten top-level
> `src/*.py` modules that thirteen of its own shipped files import. Wave 3 had pinned `0.8.0`
> on 09-17. Proposed fix: juniper-deploy#225, moving all four sites
> (`docker-compose.yml:656,800,891` + `k8s/helm/juniper/values.yaml:220`) to `0.8.1`.
>
> **The D-1 gate cannot catch this class.** `Published Image Refs` asserts that a pinned ref
> **resolves**; it does not assert the ref is the **newest release**. Those are different
> properties and only the first is checked — so the stack pinned a superseded canopy for three
> days with every required check green and nothing naming it. A **resolution** gate is not a
> **currency** gate. Comparing `gh release list` against the pins is a separate check that does
> not exist; it is deliberately not added here, because a currency gate goes red on every
> upstream release including ones this repo has not yet chosen to adopt. Until someone decides
> that trade-off, **re-probe the pins against `gh release list` whenever this plan is opened**.

The worker is the pilot because it has the only committed arm64 consumer and carries the
constraint most likely to break arm64. Proving it there de-risks the other four.

**Wave 3 is deliberately low-risk.** Compose keeps both keys: `image:` becomes the pinned
registry ref and `build:` stays. `docker compose build` then tags the local build with the
registry name, and `docker compose pull` fetches the published one — both workflows keep
working, and local development does not require a registry round-trip.

> **The kept `build:` has a silent trap, now stated in the compose file itself.** Once `image:`
> is a release ref, `docker compose build` stamps the **dev tree** with the **release tag**, and
> `docker compose up` then prefers that local image over the published one. Nothing in Docker
> warns. `make doctor` / `make image-preflight` are the detectors — both read each image's
> `org.opencontainers.image.revision` label and compare it against the source checkout's HEAD.
> **That mitigation was verified to survive the pin, not assumed to**: run offline against the
> before and after renders with matched provenance maps, `scripts/doctor.sh` produced identical
> classifications (same 8 built services, `STALE ×3 / FRESH ×1 / UNKNOWN ×4`). It derives its
> service set from `docker compose config --format json` and pairs `image:` with `build:`, so it
> follows the pin instead of breaking on it.

### 5.1 The Pi-pull gate — WAIVED for Wave 3, owner, 2026-09-15

**The contradiction, and which reading governed.** The archived chain disagreed with itself about
what the Pi pull gated, and the disagreement was inside a single document:

| source | says |
| --- | --- |
| §5 wave table, as written 2026-09-05 | *"gate before **Wave 2**"* |
| `HANDOFF_2026-09-07_…wave-1-complete.md` **L26** | *"Item 2 gates **Wave 3's pin**, not Wave 2. Do not pull the current 3 GB image to eight nodes only to replace it."* |
| the same 2026-09-07 handoff, **L111** | *"OWNER GATE — pull the image on a Raspberry Pi node. **Gates Wave 2**."* |
| `HANDOFF_2026-09-08_…wave-2-opened….md` **L194** | *"the predecessor made the Pi pull the gate for **Wave 3's pin**, and that dependency stands"* |

L26 is an explicit reassignment **with a stated reason**, L111 is the superseded phrasing left in
place, and L194 restates L26. So the reading that governed was **Wave 3, not Wave 2** — and the
tempting "Wave 2 shipped without it, therefore the gate lapsed" argument rests on the wording L26
had already replaced. The gate was *moved* precisely so the pull would land on a release image
rather than a dispatch image about to be replaced; `0.6.0` satisfies that.

**Why it was nonetheless waived.** Two facts postdate the gate's authors:

1. **The published arm64 image has already been pulled by digest and executed on native arm64
   hardware.** Release run `35033610624`, job `Build linux/arm64` on `ubuntu-24.04-arm`, step 9
   *Verify pushed image is CPU-only (publish runs)* → **success**. That step pulls
   `ghcr.io/…@<digest>` and runs `util/check_image_cpu_only.py` **inside the pushed image**. So
   *"a release nobody has run on a Pi"* is true; *"a release nobody has run on arm64"* is false.
2. **Wave 3's artifact has no Pi consumer.** `docker-compose.yml` declares no `platform:` keys
   and its docs target Compose plus k8s (kind / minikube / EKS / GKE / AKS), so the pin cannot
   deliver an arm64 risk to a Pi — nothing points a Pi at that file.

   > **Stated precisely, 2026-09-21.** This bullet previously read *"juniper-deploy contains
   > **zero** `arm64` / `aarch64` / `raspberry` / `pi` references"*. That is **false as written**:
   > `docker-compose.yml:39,46` carry the words in explanatory comments, and
   > `.github/workflows/publish-image.yml:110` names `ubuntu-24.04-arm` — juniper-deploy's own
   > arm64 build for `juniper-deploy-test`, which did not exist when the sentence was written.
   > **None of the three is a Pi consumer**, so the waiver's reasoning is unaffected and the
   > decision stands. Corrected because an arc that insists on *"measured, not assumed"* should
   > not rest a ruling on a claim that fails its own grep.

Everything the Pi pull still buys — real Pi silicon and page size versus a cloud Neoverse runner,
the 64-bit-OS precondition on the actual nodes, RAM and disk in practice, registry reachability and
authentication from the Pi LAN — is a **fleet-readiness** fact, not an **image** fact. It is
therefore re-filed against **first Pi deployment** and **OQ-3**, which are the things it tests.

**This is a waiver, not a retirement.** The pull still owes before any Pi node runs a Juniper
image, and the command is unchanged:

```bash
docker pull ghcr.io/pcalnon/juniper-cascor-worker:0.6.0
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:0.6.0 -c \
  "import platform, torch; print(platform.machine(), torch.__version__, torch.version.cuda)"
```

Expect `aarch64 2.14.0+cpu None`, ~270 MB. **Precondition: a 64-bit Pi OS** — the index carries
`linux/arm64` only, so a 32-bit OS cannot pull it.

### 5.2 Image hardening — both publish-trap classes swept, 2026-09-21

`memory/reference_juniper_deploy_image_publish_traps.md` named **two** classes to check in every
repo before its next image change. Both were swept on 2026-09-21 and both are now enforced in CI,
in all five image repos: **juniper-cascor#661, juniper-canopy#642, juniper-data#408,
juniper-cascor-worker#191, juniper-recurrence#176.** Each carries three layers — the
`.dockerignore` fix, `util/check_image_no_secrets.py`, and that checker wired into **both** the
smoke and the publish steps of `publish-image.yml`.

**Neither class repeats.** But the survey found something the original framing did not anticipate,
and it is the part worth carrying forward.

**`.dockerignore` is ROOT-ANCHORED, and a directory allowlist is not a file allowlist.** Docker
matches every pattern with Go `filepath.Match` relative to the **context root**, so a pattern
without `**/` is inert against a nested path. Every Juniper Dockerfile uses `COPY <dir>/ ./<dir>/`,
which ships everything tracked beneath it. In juniper-cascor the two combined:
`.dockerignore`'s `cascor_snapshots/` never matched `src/cascor_snapshots/` — **766 `.h5` files,
all 766 carrying a plaintext 32-byte multiprocessing authkey** (288 distinct), sitting directly
under a shipping `COPY src/`.

**What actually kept them out of the published images was `.gitignore` plus `actions/checkout`** —
CI builds from a clean checkout, so only COMMITTED files can reach an image. Not the allowlist,
and not `.dockerignore`. That distinction matters because the protection is narrower than it
looks: a credential *committed* under a shipped directory would sail through, and a **local**
`docker compose build` honours neither, so it would have baked all 766 into an image stamped with
the RELEASED tag (juniper-deploy deliberately pairs `build:` with the published `image:`).

**Three traps for whoever hardens the next repo:**

- **A `/app` top-level check passes VACUOUSLY** on juniper-data, juniper-cascor-worker and
  juniper-recurrence, whose `/app` holds only a runtime directory while the code lives in
  `site-packages`. The checker walks `/app` **and** every installed `juniper*` package, and exits
  2 if it finds no root or walks zero files, so it cannot silently become a no-op.
- **Do not blanket-add `**/logs/` or `**/data/`.** juniper-canopy's `src/logs` is a **symlink**
  that the published image carries pointing at `/app/logs`; excluding it would have silently
  broken the container's logging path. Check the published image before twinning any
  runtime-writable directory name.
- **On the publish path, CI asserted the least.** The import smoke was gated
  `if: github.event_name != 'release' && !inputs.push`, so a release executed only
  `check_image_cpu_only.py` — a distribution census that never imports the application. All five
  now assert the import on the path that ships.

**The class-2 defect, and why a source read could not find it.**
`juniper-cascor-worker:0.6.0` reported `__version__ == "0.4.0"` while `importlib.metadata.version()`
and `pyproject.toml` both said `0.6.0`; `__init__.py` was never bumped, so **two** releases shipped
a package misreporting itself, and `__version__` is in `__all__`. `pyproject.toml` alone looks
correct — only comparing the two *inside the artifact* reveals it. Fixed in
juniper-cascor-worker#192 by deriving from installed metadata. **The published image still answers
`0.4.0` and will until the next worker release**, which is owner-gated.

**Instruments** (juniper-ml, `util/ad-hoc/`): `2026-09-21_image_build_context_sweep.py` (class 1,
including root-anchoring detection) and `2026-09-21_image_does_its_job_sweep.py` (class 2: import
+ `__version__`-vs-metadata + entrypoint + serve). Re-run these rather than repeating the survey.

**Still open here:** nothing in juniper-deploy detects a **stale pin**.
`scripts/verify_published_images.py` asserts existence and architecture, never **currency**, so it
ran green throughout the three days `docker-compose.yml` pinned `juniper-canopy:0.8.0` after
`0.8.1` had shipped (closed by juniper-deploy#225, but only for that one drift).

## 6. Open questions

- **OQ-1 — RULED 2026-09-11: yes, proceed to Wave 4.** Owner decision. The grounding, so a
  later reader can re-check it rather than inherit it:

  | posture | value (docs.docker.com, read 2026-09-11) |
  | --- | --- |
  | public repositories, Personal (free) | **unlimited** (5 are needed) |
  | private repositories, Personal | 1 — irrelevant; all five are public |
  | pull rate, authenticated Personal | **200 per 6 hours** |
  | pull rate, unauthenticated | **100 per 6 hours** per IPv4 address **or IPv6 /64 subnet** |
  | how a pull is counted | **once per architecture** — a 2-arch index pulled on both arches is 2. **Not confirmed on re-read 2026-09-22**: the usage page does not state it (procedure §9) |
  | storage cap | none stated for public repositories |

  **The size objection is gone**: the CPU-only images are 270–312 MB compressed, not the
  multi-GB CUDA images the original caution was written against (see the D-2 note above).

  **The live constraint is the anonymous rate, not storage.** 100 per 6 h is scoped to an
  IPv4 address *or an IPv6 /64* — so every Pi node behind one household connection shares
  one bucket, and a 2-arch image may cost one pull per arch (unconfirmed, see the table). Wave 4 should therefore log
  **authenticated** pulls on the Pi nodes (200/6 h) rather than rely on the anonymous
  allowance, and that is a deployment note, not a workflow change. It also bears on OQ-3,
  which until now was framed as a RAM question only.

  **Owner action before any Wave 4 workflow change**: register a `DOCKERHUB_TOKEN` (and
  `DOCKERHUB_USERNAME`) secret in each of the five image repos —
  juniper-cascor, juniper-cascor-worker, juniper-canopy, juniper-data, juniper-recurrence.
  Until those exist the second login+push cannot be added, and adding it early would fail
  every release. Scope the token to **Read & Write**, not Admin.

  **Scope RULED 2026-09-22: an environment secret, not a repository secret.** The owner chose
  Option B of §3 of `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
  In each repository the secrets live in a `dockerhub` environment restricted to release tags,
  with no reviewer and no wait timer. A repository secret would be readable by every workflow on
  every ref. Registration steps are in that procedure's §5.2B. **The ruling constrains the
  workflow change.** `publish-image.yml`'s `build` job also runs on pull requests and dispatches,
  and its `merge` job also runs on `push=true` dispatches. A tags-only environment named
  unconditionally on either job therefore rejects those runs. Wave 4 must name the environment
  only where the run is a release. The procedure's §3 and §7 give the two ways to do that.
- **OQ-2.** Should a `:X.Y.Z-cuda` variant exist for cascor / cascor-worker, and if so is it
  built on release or on demand? (D-5.)
- **OQ-3.** Do the Pi nodes have enough RAM to run a torch-bearing worker in practice? This
  is a capacity question, not an architecture one — the image will run. **The Pi pull is now
  this question's gate** (§5.1), having been waived as Wave 3's; it is also the check that
  proves the 64-bit-OS precondition on the actual nodes, which no CI runner can answer.
- **OQ-4.** Should juniper-deploy publish a versioned "stack manifest" (a pinned tag set)
  alongside the compose file, so a host can reproduce an exact stack from one identifier?
