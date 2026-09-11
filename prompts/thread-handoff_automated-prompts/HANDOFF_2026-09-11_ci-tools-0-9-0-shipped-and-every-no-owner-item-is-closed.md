# HANDOFF 2026-09-11 — juniper-ci-tools 0.9.0 shipped end to end, and every no-owner item is closed

**Session**: container-registry rollout — item 6 tail, then the juniper-ci-tools 0.9.0 release train
**Predecessor**: `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md`

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
- **A claim corrected mid-session**: "three repos commit their lockfile regen unsigned" was wrong about
  **juniper-ml**, which uses `peter-evans/create-pull-request` on a schedule — a different mechanism.
  Only the two client repos had the plain-push defect. The hazard was also narrower than first stated:
  an unsigned commit is harmless under **squash** (GitHub authors and signs that commit) and bites only
  on **merge-commit or rebase**, which all three repos allow. It had never fired.
