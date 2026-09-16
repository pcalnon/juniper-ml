# HANDOFF 2026-09-15 — All five images are published, and the Pi gate Wave 3 still owes

**Session**: container-registry rollout — the worker Release, plus an environment repair and a memory pass
**Predecessor**: `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. **All five release images now exist**, which was the
arc's long pole — but **Wave 3 is not cleanly unblocked**, and the reason is the first thing to
settle. Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md`'s
own predecessor chain; the design of record is
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, whose `Status:`
line was refreshed 2026-09-15 and is accurate — read it first.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`,
`prompts/` or `util/` are inside `juniper-ml/`. **Times are UTC.**

### The five images, all verified

| repo | image | cut |
| --- | --- | --- |
| juniper-cascor | `0.11.0` | 09-09 |
| juniper-data | `0.14.0` | 09-09 |
| juniper-recurrence | `0.5.0` | 09-10 |
| juniper-canopy | `0.8.0` | 09-12 — also **item 1's first publish**; package came up **public** |
| juniper-cascor-worker | `0.6.0` | **09-15**, run `35033610624`, three jobs green |

The worker image was censused from the pulled artifact, not inferred:
`torch=2.14.0+cpu (cuda=None) distributions=24 cuda_stack=0` / *CPU-only contract holds*.
`EXPECT_TORCH` came from `ARG TORCH_VERSION` **at the tag**, never a doc. `cuda_stack=0` is the
discriminating half — a version check alone cannot separate a real CPU build from one where the CPU
wheel was installed last over orphaned CUDA wheels. The worker is an **ENTRYPOINT** image, so the
census needs `--entrypoint python` and a bare `-`.

### A verified image does not mean a sound release — canopy

A concurrent session found, the same day, that **every published `juniper-canopy` wheel back to
0.5.0 omits 10 top-level `src/*.py` modules** that 13 of its own 49 shipped files import, so
`pip install juniper-canopy` cannot import its dashboard: `packages.find` collects packages only and
there is no `py-modules` entry. See `project_canopy_wheel_omits_toplevel_modules_2026-09-15.md`.

Nothing above is wrong — canopy `0.8.0`'s **image** was verified and is fine — but the two artifacts
of one Release have independent health, and **the container is exactly what hid this for four
releases**: it runs from the source tree with `PYTHONPATH=/app/src`, so the missing modules resolve
there and only there. Wave 3 pins images and is unaffected. Do not generalise "the image is
verified" into "the release is good", in either direction.

### Settle this before touching juniper-deploy

**The record disagrees with itself about whether the Pi pull gates Wave 3.**

- The plan's wave table (line 196) calls the Pi verify a *"gate before Wave 2"* — and Wave 2
  shipped without it, so on that reading the gate lapsed.
- The 2026-09-08 handoff says the opposite, in terms: *"the predecessor made the Pi pull the gate
  for **Wave 3's pin**, and that dependency stands: **do not pin `docker-compose.yml` to a release
  nobody has run on a Pi**."*

Both are in the archived chain and neither supersedes the other explicitly. **Do not resolve this by
picking the convenient one.** Either run the Pi pull first, or get the owner to waive it on the
record — and whichever happens, fix the plan so the next reader is not handed the same contradiction.
The pull is cheap (~270 MB, arm64) and the target finally exists:

```bash
docker pull ghcr.io/pcalnon/juniper-cascor-worker:0.6.0
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:0.6.0 -c \
  "import platform, torch; print(platform.machine(), torch.__version__, torch.version.cuda)"
```

Expect `aarch64 2.14.0+cpu None`. **Precondition: a 64-bit Pi OS** — the index carries `linux/arm64`
only, so a 32-bit OS cannot pull it. **Do not use `dispatch-9890a23`**: it predates the torch
2.12.0 → 2.14.0 bump and is not a valid target for this check.

### Wave 3 itself, when it is unblocked

`juniper-deploy/docker-compose.yml` carries **9 Juniper `image:` lines, all `<name>:latest` with no
registry prefix**, at L134, 197, 334, 391, 487, 556, 620, 764, 855 — re-censused 2026-09-15 and
identical to the original survey, so none of this work has started. Five unique images.

Two things in it are decisions, not mechanics:

- **`demo-seed` (L487) has no `build:` stanza.** It reuses the data image with an `entrypoint:`
  override, so the plan's "keep `build:` for local dev" is *inapplicable* there and needs an explicit
  call.
- **The unstated hazard in "keep `build:`"**: once `image:` is a release ref, a local
  `docker compose build` stamps the **dev tree** with the **release tag**, and `docker compose up`
  then silently prefers it. That is exactly what `make doctor`'s stale-image detection exists to
  catch.

Wave 3 also owes juniper-deploy's own `Dockerfile.test` runner image (context at
`docker-compose.yml:1061`) and the pull-the-published-images integration test (plan D-1).

### Still owner-gated

- **The worker's PyPI publish has NOT happened.** Run `35033610592` is `waiting` on the `pypi`
  environment gate and PyPI's latest is still **0.5.0** — checked against the index, not inferred
  from the Release. When it is approved, note the 0.6.0 wheel is **byte-identical to 0.5.0's** apart
  from the version string: 43 commits and 23 files across `v0.5.0...main` with **zero** in
  `juniper_cascor_worker/` or `pyproject.toml`. Nothing is wrong; the Release exists for the image.
- **Wave 4 (item 5)** is committed (OQ-1 ruled 09-11) and blocked on the owner registering
  `DOCKERHUB_TOKEN` + `DOCKERHUB_USERNAME`, **Read & Write**, in all five image repos.
- **OQ-2 / OQ-3 / OQ-4** remain open. OQ-1's finding bears on OQ-3, which was framed as RAM only:
  Docker Hub's anonymous limit is **100 pulls / 6 h per IPv4 *or IPv6 /64*, counted once per
  architecture**, so Pi nodes behind one connection share a bucket. Authenticate those pulls.

### Traps this session paid for

- **A merged release *proposal* is not a Release.** worker#184 and canopy#620 both merged 09-12;
  canopy's Release was cut and the worker's was not. For three days `pyproject.toml` read `0.6.0`
  while the newest tag was `v0.5.0` and the registry held only `dispatch-*`. Re-probe
  `gh release list` and `tags/list`; never infer the registry from a merge.
- **`gh release create --target` rejects an abbreviated SHA** (`Release.target_commitish is
  invalid`) — pass the full 40 characters. That failure returned through a pipe, so the shell
  reported `exit=0`; read gh's own message, not `$?` after a pipe.
- **Tags appearing is not success.** `publish-image.yml` writes tags and *then* verifies; the
  worker's first-ever dispatch failed that verification **after** the tag existed. Wait for
  `Publish manifest: completed/success`.
- **`safe_merge.py` can report exit 0 without merging** — read its `MERGED` line.
- **A wedged CI job** (`steps=0` + a named runner + `BlobNotFound` logs) ignores `gh run cancel`;
  append a commit to supersede the run instead.
- **`gh api rate_limit` lies about GraphQL** — ask GraphQL for its own `rateLimit { resetAt }`; the
  window is a full hour and is shared with every concurrent session here.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
gh release list --repo pcalnon/juniper-cascor-worker --limit 1     # v0.6.0
gh release list --repo pcalnon/juniper-canopy        --limit 1     # v0.8.0

# all five images, anonymously (repeat per repo)
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor-worker:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor-worker/tags/list   # 0.6.0, 0.6, latest

# the census that actually discriminates (worker is ENTRYPOINT)
docker run --rm -i -e EXPECT_TORCH=2.14.0+cpu --entrypoint python \
  ghcr.io/pcalnon/juniper-cascor-worker:0.6.0 - < juniper-cascor-worker/util/check_image_cpu_only.py

# the PyPI half, which is NOT done
gh api repos/pcalnon/juniper-cascor-worker/actions/runs/35033610592 --jq .status    # waiting
python3 -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-cascor-worker/json'))['info']['version'])"   # 0.5.0

# Wave 3's untouched target
grep -n 'image:' juniper-deploy/docker-compose.yml | grep -i juniper   # 9 lines, all :latest
```

### Git state

Local `main` is clean in every primary checkout. **No local branch was ever pushed** — every remote
commit was created through the GitHub API (`util/open_signed_pr.py`) and is GitHub-signed. This
session's juniper-ml worktree is `juniper-ml/.claude/worktrees/bright-kindling-kahan`, converged
clean to `29e6ea6d`. It created **no** sibling worktrees. `worktree remove` deletes ignored files
silently.

**Conventions**: PR base must be the default branch; commits via `util/open_signed_pr.py` (first
commit) or `util/ad-hoc/2026-09-08_append_signed_commit.py` (follow-ups). **Run the staleness
pre-flight immediately before every push** — `git fetch && git diff --name-only HEAD origin/main`
intersected with your `--add` paths; these helpers upload WHOLE files and juniper-ml takes commits
by the hour. The release-notes **archive PR must stay single-purpose** —
`util/release_train/archive_guard.py` fails any diff mixing `notes/releases/RELEASE_NOTES_*.md`
with anything else.

---

## Checkpoint — files changed this session

**juniper-cascor-worker**: Release `v0.6.0` on `763826bb` (no file changes; the proposal had
already merged as #184).
**juniper-ml** (#1929): `util/ad-hoc/2026-09-12_repair_junipercascor1_py314.py`,
`util/ad-hoc/2026-09-12_memory_index_linkset.py`.
**juniper-ml** (#1937): `util/ad-hoc/2026-09-12_memory_index_linkset.py`.
**juniper-ml** (#1939): `notes/releases/RELEASE_NOTES_juniper-cascor-worker_v0.6.0.md`.
**juniper-ml** (#1940): `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
**juniper-ml** (closing PR): this handoff.

**Outside git** — the harness memory directory: 41 notes retired to `memory/retired/` with a
`README.md` manifest (301 → 261 active), `MEMORY.md` 22,764 → ~21,500 B with **zero pointers
dropped**, and four new memories —
`feedback_wedged_ci_job_append_commit_not_cancel.md`,
`project_junipercascor1_python314_upgrade_broke_console_scripts.md`,
`project_release_event_publishes_wheel_and_image.md`,
`feedback_memory_index_target_is_20kb.md`.

**Also repaired**: `JuniperCascor1` had been moved 3.13 → 3.14 by a CUDA conda install, stranding
192 pip packages and 63 console scripts. Repaired and verified — `pre-commit` and `flake8` run
again, torch 2.11.0 computes with CUDA available, all six editable installs resolve. The parent
`Juniper/CLAUDE.md` conda table still says **3.13.13** and is stale; that file is outside any git
repo, so the correction carries no PR.

## Validation record

**Not independently validated** — no adversarial lanes; the standing instruction forbids spawning
subagents unasked. Author-verified. Where that is strong and where it is not:

- **Strong (executed)**: the worker image — pulled and censused inside the container, with
  `EXPECT_TORCH` read from the tag. The canopy publish — all three jobs read back green and the
  package's public visibility proven by an **anonymous** pull. The manifest index inspected directly
  (`linux/amd64` + `linux/arm64` + two attestation manifests, exactly the documented shape). Every
  merge confirmed against the API, never from an exit code.
- **Strong (measured, not reasoned)**: the Wave 3 census — all 9 compose lines read, not sampled.
  The worker's empty ship-path diff — the full 23-file list read.
- **Weaker**: the environment repair is verified by tool behaviour (`pre-commit`, `flake8`, a torch
  matmul, a CUDA probe), **not** by running cascor's suite, which has its own prerequisites. Three
  packages resolve from user site rather than the env.
- **Weaker**: Docker Hub's limits are read off docs.docker.com, never exercised against an account.
- **Open contradiction, deliberately not resolved**: the Pi-pull gate — see § Settle this. It is
  recorded rather than decided because deciding it alone would have meant choosing the reading that
  let the work continue.
