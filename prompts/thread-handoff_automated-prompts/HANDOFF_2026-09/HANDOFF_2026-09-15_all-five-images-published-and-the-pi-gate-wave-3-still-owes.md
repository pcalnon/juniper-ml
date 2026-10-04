# HANDOFF 2026-09-15 — All five images are published, and the Pi gate Wave 3 still owes

**Session**: container-registry rollout — the worker Release, plus an environment repair and a memory pass
**Predecessor**: `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`
**Successor**: `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md`
**Status**: **SUPERSEDED / CONSUMED 2026-09-17** — re-verified against the live ecosystem 2026-09-21.

---

## Status banner (added 2026-09-21 — read this before the goal below)

**Do not paste the goal below as a new thread's prompt.** Every actionable item in it has
shipped. It is retained as the arc's record, not as live work. The successor is
`HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md`;
the design of record is
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, whose
`Status:` line was refreshed 2026-09-17 — but see the §5-table caveat under *Residuals* below.

**This banner was adversarially validated** by three independent lenses on 2026-09-21 (factual
re-probe; attack-the-conclusion; amputation / unsupported-closure). It is published **after**
their corrections, not before: the first draft asserted a stale juniper-deploy checkout, an
unverifiable control count, and an over-broad mechanism for the build-context sweep. All three
are corrected below and each correction was re-derived in source by this author, not accepted
from the agent that reported it — one agent claim was itself wrong and is recorded as such.

### What this document asked for, and where each ask landed

| this document's ask | state, verified 2026-09-21 |
| --- | --- |
| Settle the Pi-gate contradiction without picking the convenient reading | **CLOSED** — owner **WAIVED** it for Wave 3 on 2026-09-15; recorded with the full L26-vs-L111 adjudication as §5.1 of the plan (juniper-ml#1943). Re-filed against first Pi deployment and OQ-3 |
| Fix the plan so the next reader is not handed the same contradiction | **CLOSED** — §5.1 of the plan document names all four conflicting sources and which governed |
| Wave 3 — pin `docker-compose.yml`'s 9 `image:` lines | **CLOSED** — juniper-deploy#215. `juniper-deploy/docker-compose.yml` now carries **10** `ghcr.io/pcalnon/…:X.Y.Z` refs (L164, 227, 364, 421, 517, 592, 656, 800, 891, 1109), zero `:latest`. Re-counted 2026-09-21: 17 `image:` occurrences = these 10 + 4 third-party (prometheus, alertmanager, grafana, redis) + 3 in comments |
| `demo-seed` (then L487) needs an explicit call, having no `build:` | **CLOSED** — it is now L517 and carries a six-line comment stating the reuse, the bump-together rule, and why `make doctor` skips it by design |
| State the "keep `build:`" stale-image hazard | **CLOSED** — stated in the compose file itself; `make doctor` / `make image-preflight` are the detectors, verified to survive the pin |
| `Dockerfile.test` runner image | **CLOSED** — `ghcr.io/pcalnon/juniper-deploy-test:0.3.0`, Release `v0.3.0` (juniper-deploy#219 / #220 / #221) |
| D-1 pull-the-published-images integration test | **CLOSED** — `Published Image Refs` CI job + `scripts/verify_published_images.py` (juniper-deploy#217). **Caveat**: the "6 negative controls" figure repeated in the plan, the CHANGELOG and both prior handoffs is **not re-derivable from the committed code** — `tests/test_published_image_refs.py` defines **5** test functions and no `parametrize`. The gate itself works (re-run live 2026-09-21; all 6 refs resolve amd64+arm64); only the count is unsourced |
| The worker's PyPI publish (owner-gated when written) | **CLOSED 2026-09-17** — PyPI serves `juniper-cascor-worker` **0.6.0**; run `35033610592` is `completed/success`. Re-confirmed 2026-09-21 against the index, not the Release |
| The canopy wheel omission flagged as a side-finding | **CLOSED** — juniper-canopy#631, closed 2026-09-17, and **shipped as `v0.8.1` on 2026-09-18** (see *Residuals*) |

### What remains owner-gated

- **Wave 4 (Docker Hub, D-2 phase 2)** — committed, OQ-1 ruled 2026-09-11. Blocked on the owner
  registering `DOCKERHUB_TOKEN` + `DOCKERHUB_USERNAME`, **Read & Write**, in all five image repos.
  **Re-verified 2026-09-21**: `gh secret list` on juniper-cascor, juniper-cascor-worker,
  juniper-data, juniper-canopy and juniper-recurrence returns **no `DOCKERHUB_*` secret in any of
  the five** — they hold only `CROSS_REPO_DISPATCH_TOKEN` / `SOPS_AGE_KEY`, and juniper-recurrence
  holds none at all (confirmed as genuine zero, not an access failure).
  > **"Owner-gated" is narrower than it looks, and the next reader should know it.** No Docker Hub
  > scaffolding exists in any of the five `publish-image.yml` files. A second login+push guarded by
  > `if: ${{ secrets.DOCKERHUB_TOKEN != '' }}` is a provable no-op while the secrets are absent, so
  > it *could* be written and merged before they exist — which would reduce the owner's eventual
  > action from "register five secrets, then wait for a five-repo PR cycle" to "register five
  > secrets". **Not done here**, because the successor handoff says explicitly not to open
  > speculative work against owner-gated items. Recorded as an option, not a recommendation.
- **OQ-2 / OQ-3 / OQ-4** remain open. **OQ-3's gate — the Pi pull — is still un-runnable from this
  workstation**, re-probed 2026-09-21: `turing` does not answer ICMP, and **`yamaguchi` is this
  workstation itself** (`hostname` = `yamaguchi`, `uname -m` = `x86_64`, and 192.168.50.192 is one
  of this box's own addresses), so its refusing SSH on :22 is a local sshd fact and not a second
  candidate host. No arm64 `binfmt_misc` handler is registered here, so the image cannot be
  emulated either. OQ-2 and OQ-4 are pure design questions needing neither a Pi nor a credential;
  no analysis exists for either anywhere in `notes/`.

### Residuals found on 2026-09-21 that nothing else records

1. **The compose pin has already drifted, one day after Wave 3 was declared complete.**
   juniper-canopy released **`v0.8.1` on 2026-09-18** — the fix for this arc's own side-finding
   (canopy#631) — and its GHCR image is published and multi-arch (`linux/amd64` + `linux/arm64`
   + 2 attestation manifests). `juniper-deploy/docker-compose.yml` still pins
   `ghcr.io/pcalnon/juniper-canopy:0.8.0` at **L656, L800, L891**. **The D-1 gate cannot catch
   this**: it asserts that a pinned ref *resolves*, not that it is *current*, so nothing will
   surface the drift until someone looks. The three sites must move together — `test_shared_images_are_pinned_to_one_version`
   enforces exactly that.
2. **The plan's §5 wave table contradicts its own `Status:` line.** Rows for Wave 1 (*"in flight —
   juniper-cascor-worker#172"*) and all four Wave 2 rows (*"pending"*) were never updated, while
   the Pi-verify, Wave 3 and Wave 4 rows in the same table were. The prose banner and the live
   registry govern — all five images are published and resolve today. Low consequence, but it is
   the same self-contradicting shape §5.1 exists to prevent.
3. **The waiver's supporting claim fails a literal grep.** The plan (§5.1) and the 09-17 handoff
   both state juniper-deploy contains *"zero `arm64`/`aarch64`/`raspberry`/`pi` references"*.
   `docker-compose.yml:39,46` (comments) and `.github/workflows/publish-image.yml:110`
   (`ubuntu-24.04-arm`, juniper-deploy's own arm64 build) all match. **None is a Pi consumer**, so
   the waiver's reasoning survives intact; the prose is imprecise, the decision is not.
4. **`juniper-cascor-worker/docs/REFERENCE.md:504,626` and `docs/DEVELOPER_CHEATSHEET.md:231,233`
   still document `juniper-ci-tools>=0.6.0,<0.7.0`** while the live workflow pin is
   `>=0.9.0,<0.10.0`. Flagged in the 2026-09-11 handoff as *"reported, not fixed"* and never
   mentioned again. Outside this arc, but genuinely forgotten.

### The build-context sweep — executed, with the mechanism corrected

`HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md`
left one non-owner-gated action open: *"The build context holds `secrets/` with eight live
credential files, and there was no `.dockerignore` … **Check the other repos before their next
image change.**"* That sweep has been run across all five service image repos.

**No credential reaches any published image.** That conclusion holds. But the mechanism first
written for it — *"all five use an explicit COPY allowlist"* — **is wrong**, and the real one
matters more:

**The load-bearing mechanism is the clean checkout, not the allowlist.** A CI publish builds from
a fresh checkout, so **only committed files can reach a published image**. That, not the COPY
list, is what makes the juniper-deploy class non-reproducible here — juniper-deploy's exposure
was possible because its `secrets/` files sat in a *working tree* the build context swept up.

What that re-framing costs, measured **inside the published artifacts** rather than reasoned:

| published image | committed test files shipped | how |
| --- | --- | --- |
| `juniper-cascor:0.11.0` | **268** | `COPY src/ ./src/` (`Dockerfile:48`, `:86`); `.dockerignore` has no `tests/` rule |
| `juniper-data:0.14.0` | **22** | `COPY juniper_data/ ./juniper_data/` (`Dockerfile:30`); bare `reports/` matches the context root only |
| `juniper-canopy:0.8.0` | **0** — `/app/src/tests` absent | `.dockerignore:39` is `src/tests/`, correctly multi-segment |

So **cascor's and data's allowlists are directory-grained, not file-grained**: they copy a
directory whose `.dockerignore` does not exclude the nested test subtree. canopy is the negative
control that proves the check discriminates. worker and recurrence do not share the gap — their
packaged directories contain no nested `tests/`.

**A credential committed anywhere under `juniper-cascor/src/tests/` or
`juniper-data/juniper_data/tests/` would ship into a published production image**, and no
Docker-level control would stop it. Today none exists — scanned for credential-shaped filenames
*and* live value patterns (AWS, GitHub, Slack, PEM, `sk-`), zero hits. The only backstops are
CI-level gitleaks (present for cascor / data / canopy / worker, **absent from juniper-recurrence's
workflows**) and a pre-commit hook whose `files` regex `^\.env(\.secrets)?$` is anchored to the
repo root and would not fire on a nested fixture. **Latent, not live** — and worth a `**/tests/`
rule in those two `.dockerignore` files.

**One agent claim in this validation was itself wrong, and is recorded so it is not re-inherited.**
The attack-the-conclusion lens reported that cascor's 119 local coverage-report files under
`src/tests/reports/` "ship into both stages". They do not: `.gitignore:236` is `**/reports/`,
`git ls-files src/tests/reports/` returns **0**, and the published image has no `reports` subtree.
They are local-only artifacts and can reach a **local** `docker compose build` — never a CI
publish. Re-probe before acting on an agent verdict.

Two smaller facts, recorded so they are not re-derived:

- **The check unit matters.** Four repos build with `context: .`; **juniper-recurrence builds from
  the nested `juniper-recurrence/juniper-recurrence/`** (`APP_DIR`, `publish-image.yml:77,147`),
  and Docker reads `.dockerignore` from the **context** root. Its repo root has none — its context
  does. A repo-root sweep reports a false positive here.
- **canopy's `.dockerignore:86` is `.env`**, which matches that exact path only and does **not**
  match the tracked `.env.prod` / `.env.dev` beside it. Moot under the current allowlist, and both
  files are non-secret configuration (hosts, ports, log levels, URLs, rate-limit toggles).
- **`ci.yml` in cascor / data / canopy and `ci-recurrence-app.yml` in recurrence also run
  `docker build`** — a second build site the "one Dockerfile per repo" framing does not name. All
  four use the same context and default Dockerfile, and none pushes; the images are smoke-tested
  and discarded. Not a wider surface, but the count of build sites is six, not five.
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
