# HANDOFF 2026-09-22 — Ten PRs landed on 09-21, and the published worker still reports 0.4.0

**Session**: container-registry rollout — evaluating the 09-15 handoff, closing its sweep, and the residuals four validation lanes found
**Predecessor**: `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` — **read it from `main`, not from a worktree** (see the first trap below)

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. Wave 3 is complete, its pin drift is closed, and a
five-repo hardening sweep shipped 2026-09-21 — but **a published image is wrong right now**, and
**three concrete items are startable today without any owner input**. Design of record:
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`,
`prompts/` or `util/` are inside `juniper-ml/`. **Times are UTC**; the host is CDT (UTC−5).

### READ THIS FIRST — the trap that produced the first draft of this handoff

**A worktree checkout is not the record, and the gap is not small.** This handoff's first draft was
written from `juniper-ml/.claude/worktrees/linear-watching-sunrise`, whose copy of the predecessor
is **12,371 bytes** against **45,064** on `main` — less than a third. The draft therefore missed
five merged PRs, a live image defect and an unenforced control, and had to be rewritten. **Read
every document of record through the API**, not from the checkout you happen to be sitting in:

```bash
gh api repos/pcalnon/juniper-ml/contents/<path> --jq '.content' | base64 -d
```

At least seven sessions run here concurrently. **Re-probe a repo's HEAD before acting on any claim
about it, including one written an hour ago.**

### Startable today — no owner input required

1. **Wire the "image does its job" sweep into the release path.** `util/ad-hoc/2026-09-21_image_does_its_job_sweep.py`
   exists and was run once by hand. In every `publish-image.yml` the import smoke is gated
   `if: github.event_name != 'release' && !inputs.push`, so **on the publish path the only
   in-image execution is `check_image_cpu_only.py`** — a distribution census that never imports
   the app. The `/v1/health` probe lives only in `ci.yml`, against a **locally built** image.
   Nothing in CI asserts that a *published* service image serves. Today they all happen to.
2. ~~**Propagate the 09-21 sweep's findings out of the predecessor handoff.**~~ **DONE
   2026-09-22 — juniper-ml#1996.** Both halves: the design of record now carries them as **§5.2**
   of `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, and
   `memory/reference_juniper_deploy_image_publish_traps.md` has been rewritten so its class-1
   section no longer instructs a reader to run a survey that has been run — both sections now
   record what the sweep FOUND rather than what it was looking for.
3. **`juniper-data`'s PyPI wheel ships its test suite.** New finding, this session, not in any
   prior document: `juniper_data-0.14.0-py3-none-any.whl` carries **95 of its 199 members** under
   `juniper_data/tests/`. Cause is `pyproject.toml:150` — `include = ["juniper_data*"]` with no
   `exclude`, and the glob matches `juniper_data.tests`. **`.dockerignore` cannot fix this**; it
   governs Docker build contexts, not wheels. The fix is
   `exclude = ["juniper_data.tests*"]`. Negative controls: `juniper-cascor 0.11.0` (207 members,
   **0** tests) and `juniper-canopy 0.8.1` (73, **0**) are clean — this is data-specific.
4. *(smaller)* **`juniper-cascor-worker/docs/REFERENCE.md:504,626` and
   `docs/DEVELOPER_CHEATSHEET.md:231,233`** document `juniper-ci-tools>=0.6.0,<0.7.0` against a
   live pin of `>=0.9.0,<0.10.0` (`ci.yml:155,336,510`). Flagged 2026-09-11 as "reported, not
   fixed"; still true.

### A published image is wrong right now

**`ghcr.io/pcalnon/juniper-cascor-worker:0.6.0` reports `__version__ == "0.4.0"` while
`importlib.metadata` says `0.6.0`.** `__init__.py:15` was never bumped, so **two** releases
(0.5.0, 0.6.0) shipped a stale in-package version; anything reading `__version__` — provenance
stamps, logs, telemetry — reports 0.4.0. Re-probed **2026-09-22, still wrong**:

```bash
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:0.6.0 \
  -c "import juniper_cascor_worker as w, importlib.metadata as m; print(w.__version__, m.version('juniper-cascor-worker'))"
```

**Source is fixed on `main`** (worker#192 `c5e15e33`, deriving from installed metadata), **but a
merge is not a delivery** — the published artifact stays wrong until `0.6.1`/`0.7.0` ships. Note
`docker-compose.yml:364` pins exactly this image, so "zero pin drift" is true by *tag* and the
artifact behind it is still internally wrong. **Tag currency is not artifact correctness.**

### Merged 2026-09-21 — ten PRs, two waves

Mine (13:11–16:25): juniper-deploy#225 (canopy `0.8.0`→`0.8.1`, four sites), juniper-cascor#660 and
juniper-data#405 (`**/tests/` + `**/reports/`), juniper-ml#1975 (supersede-banner on the 09-15
handoff), juniper-ml#1978 (plan wave table, arm64 claim, drift note).

A concurrent session's (18:50–19:23), the five-repo credential hardening: juniper-cascor-worker#191,
juniper-recurrence#176, juniper-data#408, juniper-cascor#661, juniper-canopy#642 — each adding
`util/check_image_no_secrets.py` and wiring it into the smoke **and** publish paths. cascor#661 also
fixed a root-anchored `cascor_snapshots/` rule that was inert against `src/cascor_snapshots/`,
leaving **766 `.h5` files, each carrying a plaintext 32-byte multiprocessing authkey**, one
`docker compose build` from a release-tagged local image.

### Still owner-gated — do not start unprompted

- **Wave 4.** Register `DOCKERHUB_TOKEN` + `DOCKERHUB_USERNAME` (**Read & Write**) in all five image
  repos; verified absent at repo, org and environment scope, re-probed 2026-09-22. **Wave 4 is not
  only two secrets** — plan §6 OQ-1 also requires Pi nodes to log **authenticated** pulls (200/6 h)
  rather than the anonymous 100/6 h, which is shared per IPv4 *or IPv6 /64* and counted once per
  architecture.
- **OQ-2 / OQ-3 / OQ-4** need an **owner design ruling**, not legwork — that is what gates them,
  not a credential. **OQ-3 is not "Pi RAM" alone**: it is also the only check that proves the
  **64-bit-OS precondition** on the real nodes, which no CI runner can answer. Its gate is the Pi
  pull, still un-runnable here — `turing` is down, no arm64 `binfmt_misc` handler exists, and
  **`yamaguchi` is this workstation** (x86_64, 192.168.50.192), not a second candidate host.
- **The Pi-pull waiver is a waiver, not a retirement** (plan §5.1): the pull **still owes before
  any Pi node runs a Juniper image**.

### Known gaps that no gate will catch

- ~~**Pin currency.**~~ **CLOSED 2026-09-22 — juniper-deploy#226** (`13ee87aa`).
  `scripts/verify_published_images.py` now asks the currency question it never asked, which is why
  it ran green throughout the three days canopy's pin was stale.
  **Advisory by default** — a `::warning::` and exit 0 — with `--fail-on-stale` for a scheduled job
  and `--no-currency` to restore the old behaviour. Existence and currency have different blast
  radii: a missing ref breaks `up` for everyone, a stale one ships an older but working stack, so
  failing by default would block every unrelated PR the moment any upstream release landed. A test
  pins that policy so it cannot drift.
  > **The warning above about `releases/latest` is why it queries the REGISTRY, not the Releases
  > API.** `/v2/<repo>/tags/list` answers "what could this compose file pull today"; a Release can
  > exist whose image publish failed, and — as this bullet recorded — `releases/latest` is stale
  > for 3 of 5 repos. Versions also compare as tuples of ints, since `"0.10.0" < "0.9.0"`
  > lexicographically. Verified live (6/6 current) and by negative control with canopy downgraded.
- **SLSA provenance publishes build-arg values verbatim** — `externalParameters.request.args` in
  the public in-toto blob carries `APP_VERSION`/`BUILD_DATE`/`GIT_SHA`. Benign today; it makes
  "never pass a secret as `--build-arg`" load-bearing and **currently unenforced**.
- **`juniper-cascor-worker/.env.example:9` ships `CASCOR_AUTHKEY=juniper`** — a non-blank
  credential-shaped default in a copy-me template, inconsistent with every other `.env.example`.

### Mechanisms worth keeping

- **Only COMMITTED files reach a CI-published image**, because a publish builds from
  `actions/checkout`. That — not the COPY allowlist — is why juniper-deploy's working-tree
  `secrets/` class does not reproduce. Verified across all **six** `publish-image.yml` files (the
  five service repos **plus juniper-deploy's** test-runner).
- **A bare `.dockerignore` pattern matches the CONTEXT ROOT only.** Proven by build, with a
  control: `**/tests/` copied only the module file; bare `tests/` copied the nested test files too.
  This is why data's pre-existing `reports/` never protected `juniper_data/tests/reports/`, and why
  cascor's `cascor_snapshots/` was inert against `src/cascor_snapshots/`.
- **The check unit is the CONTEXT root, not the repo root.** juniper-recurrence builds from nested
  `juniper-recurrence/juniper-recurrence/` (`APP_DIR`), so its `.dockerignore` lives there; a
  repo-root sweep false-positives on it.

### Conventions — needed before you touch anything

PR base must be the default branch. Commits go through the API and are GitHub-signed:
`util/open_signed_pr.py` (first commit), `util/ad-hoc/2026-09-08_append_signed_commit.py`
(follow-ups). **Run the staleness pre-flight immediately before every push** —
`git fetch && git diff --name-only HEAD origin/main` intersected with your `--add` paths; these
helpers upload **WHOLE files** and juniper-ml takes commits by the hour.

**In a worktree-isolated session the harness REFUSES cross-repo `git` outright** ("a
worktree-isolated session's git operations must target its own worktree"), and also refuses shell
loops over variables alongside `git`/`.github` paths, and `docker run … sh -c`. Plain `gh`, `grep`,
`cat` and `--entrypoint find` against sibling repos all work. Write one plain command per repo.

### Traps this session paid for

- **`safe_merge.py` printed `REFUSED … exit 0` and DISARMED the auto-merge net on its way out.**
  Read the `MERGED` line and confirm against the API.
- **juniper-ml's ruleset sets `strict: true`, so an ARMED net on a `BEHIND` PR waits forever** —
  `MERGEABLE/BEHIND` + `ARMED` + **zero failing checks**, indefinitely. `gh api repos/.../branches/main/protection` returns **404 "Branch not protected"**; the repo uses
  **rulesets**, so query `/rules/branches/main`. The fix is arm, then `update-branch`, **one PR at
  a time**: CI is **~10 min** against `main`'s **~1 commit / 23 min**, so a cycle is winnable —
  safe_merge's "CI budget: 2800s" is a ceiling, not a duration, and its "main moves faster than CI"
  diagnosis was wrong by 2×.
- **`2>&1 | wc -l` on a first `docker run` counts the PULL PROGRESS.** That is how this session
  produced a bogus "22 test files" figure for juniper-data — pull output, not a measurement. The
  real count is **190** under `site-packages/juniper_data/tests` (95 `.py`, 87 `test_*.py`); a
  concurrent session had already corrected it in `juniper-data/.dockerignore`. **Pull the image
  first, measure second, and never fold stderr into a count.**
- **`find … | wc -l` cannot distinguish absent from unreadable.** A missing path and a
  permission-denied path both print one line, and a present-but-empty directory prints zero.
  **Read the text or the exit code, never the line count.**
- **Re-probe an agent verdict before acting on it.** One lane reported cascor's 119 local coverage
  files ship into the image; they are VCS-ignored, `ls-files` returns 0, and they are absent.

---

## Checkpoint — files changed this session

**juniper-deploy** (#225): `docker-compose.yml`, `k8s/helm/juniper/values.yaml`, `CHANGELOG.md`.
**juniper-cascor** (#660): `.dockerignore`.
**juniper-data** (#405): `.dockerignore`.
**juniper-ml** (#1975):
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md`.
**juniper-ml** (#1978): `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`.
**juniper-ml** (this PR): this handoff.

**Closed without merging**: juniper-ml#1971, superseded by #1975 after a second commit corrected the
first — the shape in `memory/feedback_squash_merge_first_commit_only.md`.

**Outside git** — harness memory: `project_container_registry_rollout_2026-09-08.md`,
`reference_contended_merge_lane_use_native_automerge.md`, `MEMORY.md`. Linkset gate 222 → 224,
**zero dropped**. **Owner ruled 2026-09-21: do not retire live memories** to meet the 20 KB target;
the index stays over budget deliberately.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
grep -c 'ghcr.io/pcalnon' juniper-deploy/docker-compose.yml                       # 10
grep -c '^\*\*/tests/' juniper-cascor/.dockerignore juniper-data/.dockerignore    # 1 each

# the live defect -- expect "0.4.0 0.6.0" until the next worker release
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-cascor-worker:0.6.0 \
  -c "import juniper_cascor_worker as w, importlib.metadata as m; print(w.__version__, m.version('juniper-cascor-worker'))"

# the data wheel still ships tests -- expect 95 of 199
python3 - <<'EOF'
import io, json, urllib.request, zipfile
d = json.load(urllib.request.urlopen("https://pypi.org/pypi/juniper-data/json"))
w = next(u for u in d["urls"] if u["filename"].endswith(".whl"))
n = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(w["url"]).read())).namelist()
print(d["info"]["version"], len(n), sum("/tests/" in x for x in n))
EOF

# pin currency -- one plain command per repo; releases/latest is STALE here
gh release list --repo pcalnon/juniper-canopy --limit 1        # v0.8.1
gh release list --repo pcalnon/juniper-cascor --limit 1        # v0.11.0
gh release list --repo pcalnon/juniper-data   --limit 1        # v0.14.0
gh release list --repo pcalnon/juniper-recurrence --limit 1    # v0.5.0
gh release list --repo pcalnon/juniper-cascor-worker --limit 1 # v0.6.0

# what GHCR actually serves (never infer the registry from a merge)
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor:pull&service=ghcr.io" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor/tags/list

gh secret list --repo pcalnon/juniper-cascor                   # no DOCKERHUB_*
```

## Git state

All five of this session's PRs merged; juniper-ml `origin/main` was `887b91f6` at write time.
**No local branch was ever pushed** — every remote commit was created through the GitHub API and is
GitHub-signed. This session's worktree is `juniper-ml/.claude/worktrees/linear-watching-sunrise`,
HEAD `52571621`, tracked tree clean with **this handoff as the only untracked file**. It is far
behind `main` and **its copies of the notes and handoffs are stale** — see the first trap. It
created **no** sibling worktrees.

## Validation record

**Validated by four independent agents** under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, sized per §3
at high criticality × medium uncertainty → **2 Lane A + 2 Lane B**. Lane A re-derived every asserted
fact from two distinct entry points (remote APIs; local checkouts + an empirical Docker build).
Lane B attacked the conclusions on opposing briefs (actionability; amputation and over-claim).

**The first draft FAILED and was rewritten.** What the lanes caught, all since fixed above:

| defect | severity |
| --- | --- |
| Missed **five merged PRs**, a live image defect and an unenforced control — the whole 09-21 hardening wave — by reading the predecessor from a **stale worktree** | CRITICAL |
| `find … \| wc -l` guidance self-contradicted *and* both halves were wrong | CRITICAL |
| Staleness-preflight and push-safety sat **outside** the block the reader is told to paste | CRITICAL |
| Claimed almost nothing was startable; **three items were**, and are now named first | CRITICAL |
| "22 test files" for juniper-data — `docker pull` progress counted as data; real figure **190** | MAJOR |
| OQ-2/OQ-4 labelled owner-gated while described as needing neither Pi nor credential — the gate is an **owner ruling** | MAJOR |
| Cross-repo `git` refusal in a worktree session undocumented | MAJOR |

**Two agent claims were themselves wrong and were re-probed rather than accepted**: that cascor's
119 local coverage files ship into its image (they are VCS-ignored and absent), and that
`/app/juniper_data/tests` holds the data image's tests (that path does not exist; they are in
site-packages). **Where this is weakest**: the "startable today" items are scoped from documents and
static inspection, not from attempting them; and the SLSA and `.env.example` items are carried
forward from the predecessor on `main` without independent re-derivation.
