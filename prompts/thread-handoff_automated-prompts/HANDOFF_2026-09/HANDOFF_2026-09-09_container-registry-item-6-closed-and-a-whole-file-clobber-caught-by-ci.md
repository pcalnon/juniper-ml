# HANDOFF 2026-09-09 — Container registry: item 6 is closed, and a whole-file clobber was caught by CI

**Session**: container-registry rollout, follow-ups 6b–6g (the no-owner half of item 6)
**Predecessor**: `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue the **container-registry rollout**. **Every no-owner follow-up in item 6 is now closed or
verified-blocked**; what remains is **owner-gated** (items 1, 3, 4, 5, 7 of the predecessor) plus one
new owner gate this session found. Merge approval for this arc's PRs was granted on 2026-09-09 and is
**per-session** — obtain your own before merging anything. Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`
— it holds the design of record, the definition of done, every owner-gate command, and the traps this
document does not repeat.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/` — `cd` there first. Paths beginning
`notes/`, `prompts/` or `util/` are inside `juniper-ml/`; another repo's file is written `<repo>/path`.
**Times below are UTC**; worktree names carry LOCAL time (CDT, UTC−5).

### What this session shipped — item 6 is closed

All five merged. Item 6a was already closed on `main` in all five repos before this session began
(worker#178, data#391, cascor#637, recurrence#160 `c0dafa16`, canopy#608 `8f5b7b2b`).

| item | PR | merge SHA | what it does |
| --- | --- | --- | --- |
| 6b | juniper-cascor-worker#179 | `f2e221bc` | torch 2.12.0 → 2.14.0; CPU lock **derived** from the GPU lock; CI tests the shipped torch |
| 6c | juniper-cascor#641 | `a51b7c58` | `lockfile-update.yml` regenerates both locks in one signed commit |
| 6c | juniper-cascor-worker#180 | `8c4b8584` | same, **plus** converting its unsigned `git push` to `createCommitOnBranch` |
| 6e | juniper-recurrence#162 | `c9484581` | `juniper-recurrence/requirements.lock` — the app image's deps are pinned |
| 6g | juniper-ml#1869 | in CI at writing | `juniper-lint-workflow-paths` resolves paths against the job's working directory |

**6d is answered, not deferred: KEEP both, now on evidence.** The predecessor called the revisit due.
The `docker-build` jobs boot the container and probe `/v1/health` — cascor's against a real
juniper-data sidecar on a Docker network; `publish-image.yml`'s PR arm does **neither**, and instead
builds arm64 and asserts the CPU-only contract inside the image. Neither subsumes the other; the only
overlap is one duplicated amd64 `docker build`. No code change.

**6f remains blocked upstream, verified not assumed.** PyPI's newest starlette **is 1.6.0** — the
version whose `testclient` still touches the deprecated `anyio.abc.BlockingPortal` alias. The filter
recurrence#154 added must stay until a newer starlette ships.

### The finding that mattered most — the drift was already real, not prospective

The predecessor framed 6c as a *future* hazard ("each CPU lock drifts on the next dependabot bump").
**In the worker it had already happened**: `requirements.lock` and `requirements-cpu.lock` disagreed on
**10 of their 19 shared pins** — `setuptools` 70.2.0 vs 83.0.0, `numpy` 2.4.4 vs 2.5.1, `websockets`
16.0 vs 16.1.1, plus `filelock`, `fsspec`, `annotated-types`, `typing-extensions`,
`typing-inspection`, `pydantic`, `pydantic-core`.

**Why nothing went red, in both repos**: the CI lock checks (`Check requirements-cpu.lock contains
every pyproject dep` in the worker, `… contains every image dependency` in cascor) assert only that
every declared dependency is **present** in the CPU lock. Never that its version agrees with anything.
Both locks carried the same 19 *names*, so both checks passed for as long as the drift existed.

Three flags in the derivation are load-bearing, and the worker's recipe had none of them:

- **`--constraint requirements.lock`** — without it a fresh resolution takes the newest of everything
  and the two locks diverge by construction. A fresh (unconstrained) regen at torch 2.14.0 also drags
  `juniper-cascor-protocol` 0.1.0 → 0.2.0, a sibling-package bump the GPU lock does **not** have; the
  constrained one keeps 0.1.0. That is the difference between fixing the drift and inverting it.
- **`--index-strategy unsafe-best-match`** — uv's default stops at the *first* index holding a package,
  and the PyTorch CPU index ships its own older `setuptools`. Under the constraint that yields an
  unsatisfiable resolution rather than a quietly different pin.
- **`--python-version 3.14`** — the images are `python:3.14-slim` (recurrence: 3.13). Without it the
  lock is resolved for whatever interpreter ran uv, which locally is 3.13.

**Detection now exists where a check could not give it**:
`tests/test_dockerfile_cpu_torch_pin.py::test_cpu_lock_is_the_gpu_lock_minus_the_cuda_stack` asserts
exact pin-set equality, with `test_gpu_lock_still_pins_the_cuda_stack` guarding it against going
vacuous (if the GPU lock ever stops pinning CUDA wheels the two locks are the same file and parity
proves nothing). cascor already had the parity test; the worker now does too.

**Also corrected, and load-bearing if you touch the worker's pip-audit job**: worker `ci.yml` claims
"torch hard-pins `setuptools<82`". **PyPI torch 2.14.0 requires `setuptools>=77.0.3` with no upper
bound** — that comment is stale, and the constrained lock's `setuptools==83.0.0` is fine. Do not
re-derive a pin from that comment.

### The trap this session hit — read this before committing anything to a PR branch

**`util/open_signed_pr.py` and `util/ad-hoc/2026-08-26_commit_files_to_pr_branch.py` upload WHOLE
files.** The session's juniper-ml worktree was created at `8a2a8e94` and juniper-ml is the busiest
repo in the fleet: **7 commits landed on `main` during the session**. ml#1869's first commit therefore
uploaded a `docs/REFERENCE.md` seven commits stale, **reverting #1857 / #1868's soak corrections and
dropping an added systemd command block** — on a PR whose only intended change to that file is one
character.

**What caught it**: the sequence-safety docs screen, `[FAIL/deletion-run] docs/REFERENCE.md
{'deleted': 10, 'min_run': 5}` plus five `small-deletion` WARNs. Nothing else did — no other check
compares a PR's diff to what it claims to change.

**The rule**: before opening a PR with either helper, `git fetch` and confirm your worktree is current
with `origin/main` for **every** file in the `--add` set, not only the ones you edited. The cheap check
is `git diff --name-only HEAD origin/main` intersected with your `--add` paths — in this case that
named exactly one file. Repaired by rebuilding from `origin/main` (`a51fe617`) and re-applying the
one-line edit (`util/ad-hoc/2026-09-09_fix_ml6g_reference_clobber.bash`); the branch's diff against
`main` is now `docs/REFERENCE.md +1/-1` and Sequence Safety is SUCCESS.

**The other four PRs were audited for the same defect and are clean** — every deletion in each merge
commit is accounted for by an intended edit. Their worktrees were cut from `origin/main` minutes
before use, and those repos' `main` did not move underneath them.

### Remaining work — all owner-gated

The predecessor's items 1, 3, 4, 5 and 7 stand **unchanged**; go there for the commands. Current state
re-probed at 2026-09-10 ~01:00 UTC:

- **Item 4 (Wave 3 repin) still needs three Releases**: worker is still `v0.5.0`, canopy's newest tag
  is `v0.7.0` (cut *before* #603, so it can never carry an image), recurrence app is still
  `juniper-recurrence-v0.4.0`. Note **6b bumped the worker image to torch 2.14.0**, so the predecessor's
  item-3 Pi pull should target a post-#179 image, not `dispatch-9890a23`.
- **Item 1 (first publish in recurrence and canopy)** — unchanged, and both repos' `main` carries the
  corrected identity check.
- **NEW owner gate — `juniper-recurrence-model` v0.3.0 was never published.** Its Release was cut
  2026-09-09 07:22 UTC, but run **34323535743** has been `status=waiting` on the **`pypi` environment's
  approval gate** ever since (`gh api repos/pcalnon/juniper-recurrence/actions/runs/34323535743/pending_deployments`
  → `env=pypi approvers=pcalnon`). PyPI's latest is **0.2.0**. Approving a deploy is yours alone — do
  not approve it. Consequence: recurrence#162's new lock pins `juniper-recurrence-model==0.2.0`, which
  is correct for what PyPI serves today and is documented as known staleness in the lock's own header
  and in `juniper-recurrence/CHANGELOG.md`. **Regenerate that lock once 0.3.0 publishes** — `pyproject`
  allows `<0.4.0`, so it will be picked up.
- **NEW owner gate — the `juniper-ci-tools` 0.9.0 ceiling fan-out.** 6g is a MINOR bump (it adds public
  API), per the 2026-09-05 ruling that a downstream cap never understates a SemVer bump. juniper-ml's
  own 13 pin lines are widened to `<0.10.0` in ml#1869. **The other 8 repos still cap `<0.9.0`, so the
  0.9.0 wheel would reach none of them**: 3 workflow pin lines each in canopy, cascor, cascor-client,
  cascor-worker, data, data-client, deploy, and 5 in recurrence (`ci-recurrence-{app,client,model}.yml`,
  `main-verify.yml`, `sequence-safety.yml`), plus four `AGENTS.md` tables. Widen the **ceilings before**
  the Release is cut; raise **floors only after** the wheel is on PyPI. `notes/`, `reports/`, `prompts/`
  and `util/fleet_triage/predict_merge.py` also contain the old string and were deliberately left alone
  — historical records, not live pins.
- **Reported, not fixed — three repos still commit their lockfile regen UNSIGNED**: `juniper-ml`,
  `juniper-cascor-client`, `juniper-data-client`. Same defect worker#180 fixed: the
  `required_signatures` ruleset is `~DEFAULT_BRANCH`-scoped, so a plain `git push` to
  `dependabot/pip/**` *succeeds* and then leaves an unsigned commit that blocks the merge it exists to
  enable. juniper-data, juniper-canopy and juniper-cascor were converted earlier. None of the three has
  a CPU lock, so only the signature half applies.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper
gh pr view 179 --repo pcalnon/juniper-cascor-worker --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'   # MERGED f2e221bcbf04
gh pr view 180 --repo pcalnon/juniper-cascor-worker --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'   # MERGED 8c4b8584b9b0
gh pr view 641 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'          # MERGED a51b7c58f105
gh pr view 162 --repo pcalnon/juniper-recurrence --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12])"'      # MERGED c94845817f05
gh pr view 1869 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:12] // "-")"'

# The parity guard, and that it is not vacuous (run from each repo root)
cd juniper-cascor-worker && python -m pytest tests/test_dockerfile_cpu_torch_pin.py    # 28 passed
grep -c '^nvidia-\|^triton\|^cuda-' requirements.lock                                  # 19 -- the GPU lock still pins the stack
grep -c '^nvidia-\|^triton\|^cuda-' requirements-cpu.lock                              # 0
grep -n 'ARG TORCH_VERSION' Dockerfile                                                 # 2.14.0

# The worker image actually built and was censused on BOTH arches by #179's PR arm
gh api repos/pcalnon/juniper-cascor-worker/actions/jobs/102689246930/logs | grep -E 'cuda_stack=|contract holds'
#   machine=x86_64 python=3.14.7 torch=2.14.0+cpu (cuda=None) distributions=24 cuda_stack=0 expect=2.14.0+cpu
#   (job 102689246718 is the aarch64 half, same line with machine=aarch64)

# recurrence's new lock and its arm64 pre-flight
cd ../juniper-recurrence/juniper-recurrence && grep -c '^[^[:space:]#]' requirements.lock   # 31
python ../../juniper-ml/util/ad-hoc/2026-09-08_lock_wheel_availability.py requirements.lock --python 3.13 --arch aarch64   # OK -- 31 pins
python -m pytest tests/test_dockerfile_image_lock.py                                        # 9 passed

# 6f is still blocked: PyPI's newest starlette is the version with the deprecated alias
python3 -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/starlette/json'))['info']['version'])"   # 1.6.0

# The unpublished model release, and the ceiling fan-out 0.9.0 needs
gh api repos/pcalnon/juniper-recurrence/actions/runs/34323535743 --jq .status                          # waiting
gh api repos/pcalnon/juniper-recurrence/actions/runs/34323535743/pending_deployments --jq '.[].environment.name'   # pypi
grep -rln 'juniper-ci-tools>=0\.[0-9.]*,<0\.9\.0' juniper-*/.github/workflows/                         # the 8 repos to widen
```

**Local-environment caveat, so you do not chase it**: `juniper-recurrence/tests/test_app_smoke.py::test_docs_require_auth_when_enabled`
fails in `JuniperCascor1` and **reproduces identically on unmodified `main`**. That env carries
`juniper-service-core 0.5.0` / `starlette 1.0.0`, below the app's `>=0.6.0` floor (the new lock pins
0.7.0 / 1.6.0), and `juniper-recurrence/pyproject.toml` notes that this module's route expectations
depend on which service-core is installed. CI installs the right one. 185 passed / 1 failed on that
basis, not a regression.

### Git state

Local `main` is clean in every primary checkout. **No local branch was ever pushed**: every remote
commit in this session was created through the GitHub API and is GitHub-signed. Worktrees created this
session — leave them alone; cleanup is a separate, owner-signalled step, and `worktree remove` deletes
ignored files silently:

```
worktrees/juniper-cascor-worker--fix--torch-2-14-cpu-pin--20260909-1838--93f95e8b        [fix/torch-2-14-cpu-pin]            (#179 merged)
worktrees/juniper-cascor--ci--lockfile-update-both-locks--20260909-1855--53c0338b        [ci/lockfile-update-both-locks]     (#641 merged)
worktrees/juniper-recurrence--feat--lock-the-app-image--20260909-1910--2ff03047          [feat/lock-the-app-image]           (#162 merged)
worktrees/juniper-cascor-worker--ci--lockfile-update-both-locks--20260909-1911--f2e221bc [ci/lockfile-update-both-locks]     (#180 merged)
```

Plus the predecessor's eight arc worktrees, unchanged. The session's own juniper-ml worktree is
`juniper-ml/.claude/worktrees/tender-splashing-wigderson`, fast-forwarded to `a51fe617`, holding
ml#1869's 17 modified files and this handoff plus eight `util/ad-hoc/` scripts that land with it.

Host docker daemon gained one image: `recurrence-lock-check:local` (built to prove 6e's lock installs
and the census passes). The predecessor's inventory is otherwise unchanged; **none of it is dangling**,
so `docker image prune` reclaims nothing — remove by image id.

**Conventions for landing follow-ups** (predecessor): item 6 lands in worker / cascor / recurrence /
data / canopy, never juniper-ml — except 6g, which *is* juniper-ml because `juniper-ci-tools` lives
there. Read each target repo's `AGENTS.md`; worktrees per
`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`; PR base must be the default branch;
commits via the API helpers — **after** the staleness check above.

---

## Checkpoint — files changed this session

**juniper-cascor-worker** (#179): `requirements-cpu.lock`, `Dockerfile`, `.github/workflows/ci.yml`,
`tests/test_dockerfile_cpu_torch_pin.py`, `CHANGELOG.md`. (#180):
`.github/workflows/lockfile-update.yml`, `CHANGELOG.md`.

**juniper-cascor** (#641): `.github/workflows/lockfile-update.yml`, `requirements-cpu.lock`,
`CHANGELOG.md`.

**juniper-recurrence** (#162): `juniper-recurrence/requirements.lock` (new),
`juniper-recurrence/Dockerfile`, `juniper-recurrence/tests/test_dockerfile_image_lock.py` (new),
`juniper-recurrence/CHANGELOG.md`, `.github/workflows/publish-image.yml`.

**juniper-ml** (#1869): `juniper-ci-tools/juniper_ci_tools/lint_workflow_paths.py`,
`juniper-ci-tools/tests/test_lint_workflow_paths.py`, `juniper-ci-tools/juniper_ci_tools/_version.py`,
`juniper-ci-tools/pyproject.toml`, `juniper-ci-tools/CHANGELOG.md`, `tests/test_ci_tools_drift.py`,
`docs/REFERENCE.md`, and ten `.github/workflows/*.yml` ceiling widens.

**juniper-ml** (closing PR): this handoff, plus `util/ad-hoc/2026-09-09_open_worker_torch_pin_pr.bash`,
`util/ad-hoc/2026-09-09_open_cascor_lockfile_6c_pr.bash`,
`util/ad-hoc/2026-09-09_open_worker_lockfile_6c_pr.bash`,
`util/ad-hoc/2026-09-09_open_recurrence_lock_6e_pr.bash`,
`util/ad-hoc/2026-09-09_open_ml_lint_6g_pr.bash`,
`util/ad-hoc/2026-09-09_fix_ml6g_reference_clobber.bash`,
`util/ad-hoc/2026-09-09_open_closing_handoff_pr.bash` (which opens that closing PR) and
`util/ad-hoc/2026-09-09_add_closing_script_to_pr.bash` (which pushed the follow-up commit adding it).
The regress stops there: the final commit was made by a plain command, not a script.

The six `open_*` scripts exist because a worktree-isolated session's Bash classifier refuses a
multi-line command whose operands are computed at runtime; every path in them is a literal.

## Validation record

**Not independently validated.** The predecessor ran two rounds of three adversarial lanes per
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; this session did
not, because the standing instruction in effect forbade spawning subagents unasked. Treat the claims
here as author-verified only, and note where that verification is weakest:

- **Strong (executed, both directions)**: the 6g fix — pre-fix and post-fix modules both run against the
  real juniper-recurrence checkout, and the blast radius measured across all 9 repos with
  `.github/workflows/`. The two lock round-trips — the worker's reproduces `main`'s committed CPU lock
  **byte-identically**, cascor's reproduces all 53 pins with only the annotation-path normalisation
  differing. The 6e image — **built locally**, census `torch=absent distributions=36 cuda_stack=0`,
  imports and entrypoint OK. Both refusal paths of the new workflow step, exercised by hand. Every new
  guard **mutation-checked**: reverting `ci.yml` fails both new CI tests; restoring
  `pip install ".[observability]"` fails two of the nine new recurrence tests.
- **Strong (CI, not local)**: the worker's torch 2.14.0 image on **both** arches, from #179's own PR arm.
- **Weaker**: the two `lockfile-update.yml` changes have **never executed**. That workflow fires only on
  `dependabot/pip/**` pushes and on PRs touching `pyproject.toml`, and its Dependabot arm remains a
  loud green no-op until `CROSS_REPO_DISPATCH_TOKEN` is registered under Settings → Secrets →
  Dependabot. The round-trip evidence above tests the *recipe*, not the workflow. First real exercise
  is the next `pyproject.toml` PR in either repo — watch it.
- **Weaker**: 6d rests on reading the four repos' `docker-build` job steps, not on measuring runtime.
- **A claim already corrected once**: this session's first framing of 6c said the drift was prospective.
  It was live. The check that should have caught it was name-presence only — see § The finding.
