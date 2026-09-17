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
secrets. Last state refresh: 2026-09-15.

> **The worker release is worth a note before anyone reads its version number as a code change.**
> Across `v0.5.0...main` there were 43 commits and 23 files with **zero** inside the packaged
> source (`juniper_cascor_worker/`) and zero in `pyproject.toml`, so the 0.6.0 PyPI wheel is
> byte-identical to 0.5.0's apart from the version string, and `util/release_train/detect.py`
> classifies the package `UP_TO_DATE` — correctly. It was released because `release: published`
> fires **both** `publish.yml` and `publish-image.yml`, and Wave 3 needs a released `X.Y.Z` image
> ref. That overloading is a property of D-1 and will recur whenever an image input moves without
> a library change; worth an OQ if it happens a third time.
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
| 1 (pilot) | juniper-cascor-worker | **in flight** — juniper-cascor-worker#172 |
| — | *verify: pull and run on a Pi node* | **WAIVED as a Wave 3 gate, owner, 2026-09-15 (§5.1).** Re-filed as the gate on **first Pi deployment** and on **OQ-3**, which is what it actually tests. Target: `ghcr.io/pcalnon/juniper-cascor-worker:0.6.0`, the first **post-#179** image. Do **not** use `dispatch-9890a23`; it predates the torch 2.12.0 → 2.14.0 bump |
| 2 | juniper-cascor | pending |
| 2 | juniper-canopy | pending |
| 2 | juniper-data | pending |
| 2 | juniper-recurrence | pending — build context is **nested** (`juniper-recurrence/juniper-recurrence/`) |
| 3 | juniper-deploy — pin `image:` to registry refs, keep `build:` for local dev | **COMPLETE 2026-09-17.** Pin (#215, 9 lines) + D-1 check (#217) + `Dockerfile.test` runner published as `ghcr.io/pcalnon/juniper-deploy-test:0.3.0` (#219 / #220 / #221, Release `v0.3.0`) = **10** pinned lines. Sibling fix: helm `values.yaml` (#216) |
| 4 | Docker Hub as a second push target (D-2 phase 2) | **committed** — OQ-1 ruled 2026-09-11; blocked on the five `DOCKERHUB_TOKEN` secrets (§6 OQ-1) |

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
2. **Wave 3's artifact has no Pi consumer.** juniper-deploy contains **zero** `arm64` / `aarch64` /
   `raspberry` / `pi` references, `docker-compose.yml` declares no `platform:` keys, and its docs
   target Compose plus k8s (kind / minikube / EKS / GKE / AKS). The pin cannot deliver an arm64
   risk to a Pi, because nothing points a Pi at that file.

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

## 6. Open questions

- **OQ-1 — RULED 2026-09-11: yes, proceed to Wave 4.** Owner decision. The grounding, so a
  later reader can re-check it rather than inherit it:

  | posture | value (docs.docker.com, read 2026-09-11) |
  | --- | --- |
  | public repositories, Personal (free) | **unlimited** (5 are needed) |
  | private repositories, Personal | 1 — irrelevant; all five are public |
  | pull rate, authenticated Personal | **200 per 6 hours** |
  | pull rate, unauthenticated | **100 per 6 hours** per IPv4 address **or IPv6 /64 subnet** |
  | how a pull is counted | **once per architecture** — a 2-arch index pulled on both arches is 2 |
  | storage cap | none stated for public repositories |

  **The size objection is gone**: the CPU-only images are 270–312 MB compressed, not the
  multi-GB CUDA images the original caution was written against (see the D-2 note above).

  **The live constraint is the anonymous rate, not storage.** 100 per 6 h is scoped to an
  IPv4 address *or an IPv6 /64* — so every Pi node behind one household connection shares
  one bucket, and a 2-arch image costs one pull per arch. Wave 4 should therefore log
  **authenticated** pulls on the Pi nodes (200/6 h) rather than rely on the anonymous
  allowance, and that is a deployment note, not a workflow change. It also bears on OQ-3,
  which until now was framed as a RAM question only.

  **Owner action before any Wave 4 workflow change**: register a `DOCKERHUB_TOKEN` (and
  `DOCKERHUB_USERNAME`) repository secret in each of the five image repos —
  juniper-cascor, juniper-cascor-worker, juniper-canopy, juniper-data, juniper-recurrence.
  Until those exist the second login+push cannot be added, and adding it early would fail
  every release. Scope the token to **Read & Write**, not Admin.
- **OQ-2.** Should a `:X.Y.Z-cuda` variant exist for cascor / cascor-worker, and if so is it
  built on release or on demand? (D-5.)
- **OQ-3.** Do the Pi nodes have enough RAM to run a torch-bearing worker in practice? This
  is a capacity question, not an architecture one — the image will run. **The Pi pull is now
  this question's gate** (§5.1), having been waived as Wave 3's; it is also the check that
  proves the 64-bit-OS precondition on the actual nodes, which no CI runner can answer.
- **OQ-4.** Should juniper-deploy publish a versioned "stack manifest" (a pinned tag set)
  alongside the compose file, so a host can reproduce an exact stack from one identifier?
