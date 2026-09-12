# HANDOFF 2026-09-11 — Container registry: OQ-1 ruled, Wave 3 prepared, and two pins no sweep could see

**Session**: container-registry rollout — the owner-gated tail, plus a defect found by running the
predecessor's own verification command
**Predecessor**: `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. **Wave 3 is now prepared but not cut**: both blocking
Releases have open proposal PRs awaiting the owner, and **OQ-1 is ruled — Docker Hub is in**. What
remains is items 1, 3, 4, 5 and 7 of the design of record, every one owner-gated. Merge approval for
this arc is **per-session** — obtain your own before merging anything. Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`;
the design of record is
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` (refreshed this
session — read its `Status:` line first, it is now accurate).

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`, `prompts/`
or `util/` are inside `juniper-ml/`. **Times are UTC**; worktree names carry LOCAL time (CDT, UTC−5).

### What the owner ruled this session

- **juniper-cascor-worker releases as 0.6.0 (minor), not 0.5.1.** Reasoning recorded in worker#184.
- **OQ-1 — Docker Hub is in; Wave 4 is committed.** Recorded in the plan's §6 and its wave table.

### What shipped

| PR | merge SHA | what |
| --- | --- | --- |
| juniper-cascor#646 | `b374f285` | the last two stale `juniper-ci-tools` pins → `>=0.9.0,<0.10.0`, plus one `AGENTS.md` line #645 left behind |
| juniper-ml#1909 | `4f566d37` | the ci-tools drift guard widened (25 of 54 live pins → 54 of 54) **and** the doc-tools sibling's matching false exclusion |
| juniper-ml#1910 | `364cb568` | the OQ-1 ruling + a refreshed plan `Status:` + `util/ad-hoc/2026-09-11_materialize_release_proposal.py` |
| juniper-canopy#620 | `4006e749` | release **proposal** v0.7.0 → 0.8.0 |
| juniper-cascor-worker#184 | `bee7b86a` | release **proposal** v0.5.0 → 0.6.0 |

### The defect the predecessor's own verification command exposed

That handoff's check — `grep -rh 'juniper-ci-tools>=' … | grep -cv '>=0\.9\.0,<0\.10\.0'` — was
documented as wanting **0** and answered **23**. Twenty-one were comments. **Two were live pins**, on
`main`, in juniper-cascor: `ci-cascor-model.yml:94` and `ci-protocol.yml:67`, both
`>=0.6.0,<0.7.0` — three minors stale, install `juniper-coverage-gap-map`, green the whole time.

**Why three separate mechanisms all missed them, which is the part worth carrying forward:**

- **Both fan-out passes.** The ceiling pass matched `<0.9.0`, the floor pass the widened `<0.10.0`.
  A pin at `<0.7.0` matches neither — the sweep pattern was drawn from the instances the sweep had
  already found.
- **cascor's own guard, correctly.** `test_sequence_safety_retired.py` scopes `_SCREEN_WORKFLOWS` to
  `sequence-safety.yml` + `main-verify.yml`. It guards the screens; these are not the screens. Not a
  defect — do not widen it.
- **juniper-ml's drift guard, structurally.** It read **exactly one file per consumer repo**,
  `ci.yml`, over a **six**-repo list. The check unit did not match the identity guarded. Consequences,
  measured with `util/ad-hoc/2026-09-11_ci_tools_pin_census.py`: **29 of 54 live pins unguarded**;
  **juniper-recurrence has no `ci.yml` at all** (monorepo: `ci-recurrence-{app,client,model}.yml`), so
  a name-keyed read could never cover its 6; **juniper-deploy** was excluded by a comment reading
  "does not depend on juniper-ci-tools", which is false — it has 3.

**A pin reaches pip in three shapes and a `pip install`-keyed scan sees two.** The third is canopy's
workflow-level `env: CI_TOOLS_PIN:` installed via `"$CI_TOOLS_PIN"`. My first census missed it and
under-counted 54 as 52. The widened guard matches the pin string, not the install verb.

**The sibling guard was already right, which is the sharpest part.** `docs/REFERENCE.md` calls
`test_ci_tools_drift.py` a mirror of `test_doc_tools_drift.py`. The doc-tools copy already globs every
workflow **and** carries a recurrence-shaped regression test for a repo whose pin is not in `ci.yml`.
The ci-tools copy had diverged from its own stated mirror on precisely the axis that mattered — so
"mirrors X" in a docstring is a claim to re-check, not inherit. Auditing the sibling found one shared
defect: **both** excluded juniper-deploy on a comment reading "does not depend on juniper-<x>-tools",
false in both cases (deploy has 3 ci-tools pins and 1 doc-tools pin). The doc-tools half was
**latent** — all 10 doc-tools pins in the fleet are `>=0.1.0,<0.2.0`, so nothing was stale and it
would have bitten on the first 0.2.0. Fixed in the same PR (`+8/-2`), verified against the live fleet
(8 repos, 8 pins, all admitting current 0.1.2).

**Impact, stated honestly: nothing was broken.** `--enforce` has existed since 0.6.0 and both jobs
were green. 0.6.0 and 0.9.0 were installed from PyPI into clean venvs and run on synthetic
`coverage.json` in both directions — exit 0 / exit 1 identical, report text **byte-identical**. This
was version skew and a maintenance hazard, not a live failure.

### Wave 3 — the proposals MERGED, the Releases are NOT cut. Read this distinction.

**Both proposal PRs are on `main`, and that is not a release.** Verified 2026-09-12:
`gh release list` still shows **worker `v0.5.0`** and **canopy `v0.7.0`**, the worker registry still
holds only `dispatch-*`, and canopy's `tags/list` still answers **`NAME_UNKNOWN`**. So both repos now
declare `0.6.0` / `0.8.0` in `pyproject.toml`, `CHANGELOG.md` and `AGENTS.md` while the newest tag is
the previous version — the normal intermediate state, but it means **Wave 3 is exactly as blocked as
before**. Cutting the two Releases is the owner's step and nothing else substitutes for it: it is the
only event that fires `publish-image.yml`.

Both proposals were hand-verified to the exact three-file shape (`pyproject.toml`, `CHANGELOG.md`,
`AGENTS.md`) and built from files fetched from each sibling's `main` **via the API**, never a local
checkout.

- **juniper-canopy — v0.8.0** (minor; the release train proposed it, 9 shippable commits).
  Canopy has **no GHCR package at all** — `tags/list` answers `NAME_UNKNOWN`. `v0.7.0` was cut before
  #603 and can never carry an image. So cutting this tag is **both item 1** (first publish — *check
  the package page's visibility afterwards; GitHub does not inherit repo visibility, and the first
  `push=true` per repo creates a **PUBLIC** package*) **and half of item 4**.
- **juniper-cascor-worker — v0.6.0**, hand-authored, because **the release train will not propose
  it and is right not to**. Measured across `v0.5.0...main`: 43 commits, 23 files, **zero** in the
  registry `ship_paths` (`juniper_cascor_worker/`) and **zero** in `pyproject.toml`. The wheel is
  byte-identical to 0.5.0's apart from the version string. It is cut anyway because a Release fires
  **both** `publish.yml` (PyPI) and `publish-image.yml` (GHCR), and Wave 3 needs a released `X.Y.Z`
  image. Drafted notes are a comment on worker#184.

**Release notes are drafted but NOT archived.** `notes/releases/RELEASE_NOTES_juniper-canopy_v0.8.0.md`
and `..._juniper-cascor-worker_v0.6.0.md` do not exist yet; archiving is the later *exempt* ceremony
step, and `util/release_train/archive_guard.py` requires that PR be **single-purpose** — every path in
its diff a flat `notes/releases/RELEASE_NOTES_*.md`, add-only. Do not bundle the archive with anything
else. Canopy's draft is in canopy#620's body; the worker's is a comment on worker#184; both regenerate
deterministically from `util/release_train/notes_render.py --final`.

> **Recorded, not absorbed**: `release: published` is **overloaded** — "publish the library" and
> "publish the image" are one event, and here only the second had anything to say. That is a property
> of plan D-1 and will recur whenever an image input moves without a library change. Worth an OQ if
> it happens twice.

### Remaining work — all owner-gated

- **Item 4 (Wave 3)**: the proposals are merged; **cut both Releases and approve both `pypi` gates**.
  Then `juniper-deploy`'s `docker-compose.yml` repin, its `Dockerfile.test` runner image, and the
  pull-the-published-images test (D-1) unblock. Re-probe first — a merged proposal looks like progress
  and changes nothing about the registry.
- **Item 3 (Pi pull)**: **no post-#179 image exists.** The registry holds only `dispatch-3d81f2c` /
  `dispatch-8673396` / `dispatch-9890a23`, all pre-torch-2.14.0. Cutting worker v0.6.0 mints the
  first valid target — do not pull `dispatch-9890a23` and call it done.
- **Item 5 (Wave 4)**: committed. **Blocked on the owner registering `DOCKERHUB_TOKEN` +
  `DOCKERHUB_USERNAME` (Read & Write, not Admin) in all five image repos.** Adding the second
  login+push first would fail every release.
- **Item 7**: OQ-1 **CLOSED**. OQ-2 / OQ-3 / OQ-4 still open — surface, do not guess. Note OQ-1's
  finding bears on OQ-3, which was framed as RAM only: Docker Hub's anonymous limit is **100 pulls /
  6 h per IPv4 address *or IPv6 /64 subnet*, counted once per architecture**, so Pi nodes behind one
  connection share a single bucket and a 2-arch index costs two. Authenticate the Pi pulls.

### One operational trap worth carrying

**A juniper-ml CI job wedged and did not respond to cancel.** `Regression Tests (Python 3.14)` on
ml#1909 sat `in_progress` for 25+ minutes against a **~6-minute baseline** on `main` (all three legs,
run 34641488821), with `steps=0`, a runner assigned, and **no log blob** — `.../jobs/<id>/logs`
answered `BlobNotFound`. `gh run cancel` was accepted and the run stayed `in_progress`. The discriminator
is `steps=0` **plus** a named runner: a merely queued job has `started_at: null` and no runner, so that
pair means "assigned and not executing", not "slow". What cleared it was **appending a commit** — a new
head SHA supersedes the run, and checks started on the new SHA within seconds. Prefer that to fighting
the cancel; `gh --version` here is **2.46.0**, so `gh pr edit` is broken and a PR body/title update must
go through `gh api -X PATCH repos/<owner>/<repo>/pulls/<n>`.

**And the canopy timing-flake class recurred, on a PR that changes three literal strings.**
canopy#620's `UI Sub-suite (Playwright)` failed
`test_ws_silent_poll_liveness.py::test_metrics_store_polls_on_long_lived_tab_with_ws_silent[chromium]`
— *"metrics-store poll starved under WS-silent state"* — shape **`1 failed, 32 passed`**. That PR's
entire diff is a version string, a CHANGELOG heading and an `AGENTS.md` line; it cannot move a runtime
poll. Playwright passed on canopy `main` in each of its last two runs, so the "main is red too"
dismissal does **not** apply here — the applicable memory is the wall-clock/iteration-count family
([[canopy-x7-timing-tests-flake-on-ci-runners]]), which this fits exactly. `gh run rerun --failed`
is the remedy but **refuses while the run is still in progress** (`"cannot be rerun; its workflow
file may be broken"` is what that refusal looks like — not a broken workflow). Re-run it once the run
completes. Separately, canopy `main`'s newest CI run **is** red on `Unit Tests + Coverage (3.12
ubuntu)` + `Quality Gate` — the exact inherited pair that memory records.

### Reported, not fixed

`juniper-cascor-worker/docs/REFERENCE.md:504,626` and `docs/DEVELOPER_CHEATSHEET.md:231,233` state CI
installs `juniper-ci-tools>=0.6.0,<0.7.0` for `juniper-coverage-gap-map`. Its workflows are at
`>=0.9.0,<0.10.0`. Stale docs, opposite direction to the cascor defect, no functional impact.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
gh pr view 646  --repo pcalnon/juniper-cascor        --json mergeCommit --jq .mergeCommit.oid[0:12]   # b374f285d173
gh pr view 1909 --repo pcalnon/juniper-ml            --json mergeCommit --jq .mergeCommit.oid[0:12]   # 4f566d379cb5
gh pr view 1910 --repo pcalnon/juniper-ml            --json mergeCommit --jq .mergeCommit.oid[0:12]   # 364cb5682a5f
gh pr view 620  --repo pcalnon/juniper-canopy        --json mergeCommit --jq .mergeCommit.oid[0:12]   # 4006e749d05c
gh pr view 184  --repo pcalnon/juniper-cascor-worker --json mergeCommit --jq .mergeCommit.oid[0:12]   # bee7b86aa3a3

# THE RELEASES, which the merged proposals are NOT. Both must move for Wave 3.
gh release list --repo pcalnon/juniper-cascor-worker --limit 1   # v0.5.0 today -- want > this
gh release list --repo pcalnon/juniper-canopy        --limit 1   # v0.7.0 today -- want > this

# every live pin, under BOTH guard models (pull the siblings first -- local trees lag)
python3 juniper-ml/util/ad-hoc/2026-09-11_ci_tools_pin_census.py .
#   live pins: 54
#     OLD guard (one ci.yml per repo, 6 repos):  guarded 25   UNGUARDED 29
#     NEW guard (every workflow, 8 repos + ml):  guarded 54   UNGUARDED 0
#   distinct ranges in use: ['>=0.9.0,<0.10.0']   <- one entry only; two means a pin went stale

# drive the cross-repo assertion for real (it auto-skips from a worktree: the sibling
# search walks only two levels up, so the widened scope would go unexercised)
python3 juniper-ml/util/ad-hoc/2026-09-11_drive_ci_tools_drift_cross_repo.py     # OK, 41 consumer pins
cd juniper-ml && python3 -m unittest tests.test_ci_tools_drift                   # 21 tests, 1 skip

# the two images Wave 3 still needs (both must stop being empty/dispatch-only)
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-canopy:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token','NONE'))")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-canopy/tags/list   # today: NAME_UNKNOWN
T=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-cascor-worker:pull&service=ghcr.io" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token','NONE'))")
curl -s -H "Authorization: Bearer $T" https://ghcr.io/v2/pcalnon/juniper-cascor-worker/tags/list   # today: dispatch-* only
```

### Git state

Local `main` is clean in every primary checkout; `juniper-cascor` was `git pull`ed this session to
pick up #646. **No local branch was ever pushed** — every remote commit was created through the
GitHub API (`util/open_signed_pr.py`) and is GitHub-signed. This session's juniper-ml worktree is
`juniper-ml/.claude/worktrees/bright-kindling-kahan`. It created **no** sibling worktrees; the
predecessor's twelve are untouched, and `worktree remove` deletes ignored files silently.

**Conventions**: PR base must be the default branch; commits via `util/open_signed_pr.py` (first
commit) or `util/ad-hoc/2026-09-08_append_signed_commit.py` (follow-ups). **Run the staleness
pre-flight immediately before every push** — `git fetch && git diff --name-only HEAD origin/main`
intersected with your `--add` paths; these helpers upload WHOLE files and juniper-ml takes commits by
the hour. **The archive-only PR must stay single-purpose** — `util/release_train/archive_guard.py`
fails any diff that mixes `notes/releases/RELEASE_NOTES_*.md` with anything else, which is why this
session's plan-doc edit went in its own PR rather than alongside the drafted notes.

---

## Checkpoint — files changed this session

**juniper-cascor** (#646): `.github/workflows/ci-cascor-model.yml`,
`.github/workflows/ci-protocol.yml`, `AGENTS.md`.
**juniper-canopy** (#620): `pyproject.toml`, `CHANGELOG.md`, `AGENTS.md`.
**juniper-cascor-worker** (#184): `pyproject.toml`, `CHANGELOG.md`, `AGENTS.md`.
**juniper-ml** (#1909): `tests/test_ci_tools_drift.py`, `tests/test_doc_tools_drift.py`,
`docs/REFERENCE.md`, `util/ad-hoc/2026-09-11_ci_tools_pin_census.py`,
`util/ad-hoc/2026-09-11_drive_ci_tools_drift_cross_repo.py`.
**juniper-ml** (#1910): `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`,
`util/ad-hoc/2026-09-11_materialize_release_proposal.py`.
**juniper-ml** (closing PR): this handoff, plus
`util/ad-hoc/2026-09-11_symbol_loss_check_pr1909.bash` and a correction to
`util/ad-hoc/2026-09-11_ci_tools_pin_census.py` — as first landed it encoded only the pre-#1909 guard
scope, so run after the fix it would have reported `UNGUARDED 29` while this document claimed `0`. It
now prints **both** models, which is the number that actually carries the finding.

## Validation record

**Not independently validated** — no adversarial lanes were run; the standing instruction forbade
spawning subagents unasked. Author-verified only. Where that is strong and where it is not:

- **Strong (executed, both directions)**: the 0.6.0-vs-0.9.0 `juniper-coverage-gap-map` equivalence —
  both installed from PyPI into clean venvs, run on a passing and a failing synthetic `coverage.json`,
  exit codes and report text compared. The widened guard, **red then green on the live fleet**: it
  failed on exactly the two stale pins naming file and range, and passed after #646 merged and the
  sibling was pulled. The census, cross-checked against the guard's own scan (41 + 13 = 54).
- **Strong (measured, not reasoned)**: the worker's empty ship-path diff — the full 23-file
  `v0.5.0...main` list read, not sampled. Every PR's diff read back after opening (`+1/-1` per file
  where one line was intended), which is the whole-file-clobber guard.
- **Weaker**: Docker Hub's limits are **read off docs.docker.com**, not exercised against an account.
  The per-architecture counting rule especially — it changes the Pi arithmetic and nothing here has
  pulled from Docker Hub at all.
- **Weaker**: the claim that the worker's PyPI wheel would be byte-identical rests on the changed-file
  list, not on building both wheels and diffing them. `pyproject.toml` and every `ship_paths` file are
  unchanged, so the inference is tight — but it is an inference.
- **Untested**: both release-proposal PRs are merged, but **no Release has been cut**, so
  `publish-image.yml`'s release arm remains unexercised in canopy and the worker. Canopy's first cut
  would be its **first ever** package creation, and the first `push=true` per repo creates a **public**
  package — confirm the package page's visibility afterwards rather than assuming it inherits the
  repo's.
- **A correction made late, worth the warning**: this document first recorded the two proposals as
  "awaiting the owner" and, when they merged, the tempting reading was that Wave 3 had advanced. It
  had not — `gh release list` and `tags/list` were both unchanged. A merged release-*proposal* moves
  three version strings; only a Release moves the registry. Re-probe the registry, never infer it from
  a merge.
