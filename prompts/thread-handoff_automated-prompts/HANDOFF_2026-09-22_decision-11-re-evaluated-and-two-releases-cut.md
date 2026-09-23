# HANDOFF — decision 11 re-evaluated, two releases cut, and four records left naming the versions they superseded

**Date**: 2026-09-22 · **Session**: <https://claude.ai/code/session_013rU7NHHRozgkhNqBFnAHYA>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mellow-hugging-dahl`
**Branch**: `worktree-mellow-hugging-dahl` at `origin/main` — every change shipped as an API-signed PR
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md`
(this document **closes** its §8.4 N-1/N-2/N-3/N-4 and **carries** N-5, N-6 and §8.1's two floor rows)

---

## THE GOAL — paste this into the new thread

> **Continue the decision-11 release arc. Two releases shipped; their surrounding RECORDS did not.**
>
> **Completed so far**
>
> - **juniper-ml 0.9.0** and **juniper-data 0.15.0** are published and verified from the registries
>   (PyPI version-specific endpoints 200; `ghcr.io/pcalnon/juniper-data:0.15.0` + `:0.15`). The
>   published 0.15.0 wheel carries `equities`/`equities_seq` at `VERSION = "5.0.0"`.
> - Both were **explicitly approved by Paul** at the `pypi` environment gate (see PREFLIGHT 2).
> - Ten PRs merged; four issues filed; juniper-data#410 closed.
>
> **Remaining work — in priority order**
>
> 1. **Update four records that still name superseded versions** (§3 R-1..R-4). Highest value,
>    lowest risk, and they are the exact class this session spent the day catching in other
>    documents: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §10
>    and its §9 S-7 pin, `/home/pcalnon/Development/python/Juniper/AGENTS.md:189-190`, and the
>    memory file `project_decision_11_released_2026-09-11.md`.
> 2. **Decide `juniper-ml[servers]`' `juniper-data>=0.14.0` floor** (§3 R-5). 0.15.0 carries a
>    BREAKING generator major; the floor still admits the version serving the old contract. This
>    is N-3's exact shape, and N-3 was ruled "raise it". **Owner decision.**
> 3. **Write the release-ceremony lesson into the procedure** (§3 R-6). Four failure shapes fired
>    this session; all four live only in this archived prompt.
> 4. Then the carried tickets: juniper-data#411, juniper-recurrence#178, juniper-cascor#668,
>    juniper-canopy#559, and Decision 12 (§3 C-1..C-5).
>
> **Key context**
>
> - **Releases are Paul's to authorise.** He approved these two in-session. Do **not** cut another
>   without an explicit instruction — a Release body is not re-cuttable.
> - The **published juniper-data 0.15.0 wheel ships its test suite** (97 of 201 members). Fixed by
>   juniper-data#420, merged three minutes after the tag, so **0.16.0 will not carry it and 0.15.0
>   always will**. Not worth re-cutting; worth knowing.
> - `juniper-ml`'s `util/` Python is linted by **CodeQL alone**, so a clean local `pre-commit`
>   cannot predict a merge block. See PREFLIGHT 3.

---

**Documents REFERENCED** (more than one, so every reference carries its filename):

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md` — the predecessor; its §8 is this session's output
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — §9 S-7 (design findings), §10 the release record
- `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` — §11 documents the **manual** bump/tag/Release path **only**; it contains no mention of `release_train`, `ceremony.py` or `propose.py`
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — the protocol this document follows
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — §3 sizing, §5 reconciler, §7 record
- `/home/pcalnon/Development/python/Juniper/AGENTS.md` — § Data Contract (unversioned; no PR, no CI)
- `util/release_train/{registry.yaml,detect.py,propose.py,ceremony.py,notes_render.py}` — the instrument

**Documents CHANGED** — juniper-ml: `CHANGELOG.md`, `README.md`, `AGENTS.md`, `pyproject.toml`,
`docs/QUICK_START.md`, `docs/REFERENCE.md`, `tests/test_pyproject_extras.py`,
`tests/test_release_train_ceremony.py`, `util/release_train/notes_render.py`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md`,
`notes/releases/RELEASE_NOTES_v0.9.0.md`, `notes/releases/RELEASE_NOTES_juniper-data_v0.15.0.md`,
and eleven `util/ad-hoc/` scripts named individually in §5. Siblings —
juniper-recurrence: `bench/datasets.py`, `bench/test_bench_smoke.py`; juniper-data:
`CHANGELOG.md`, `pyproject.toml`, `AGENTS.md`.

---

## 0. PREFLIGHT

1. **Local `git commit` HANGS** (`commit.gpgsign=true`, YubiKey). Use `util/open_signed_pr.py`
   for a new branch, `util/ad-hoc/push_signed_commit.py` for a follow-up. Never commit, tag or
   push locally.
2. **Releases are the OWNER's.** The `pypi` environment gate is a 5-minute timer plus reviewer
   `pcalnon`. `current_user_can_approve` reads **true** for an agent — approving anyway defeats
   the gate's entire purpose. Drive to `PENDING_PYPI_APPROVAL`, hand over the run URL, stop.
   Paul approved 0.9.0 and 0.15.0 in-session; that authorisation does **not** extend to a third.
3. **`util/` Python on juniper-ml is linted by CodeQL ALONE.** The flake8 hook both
   `--extend-ignore`s **F401** and is scoped `files: ^(scripts|tests)/.*\.py$`. A clean local
   `pre-commit` therefore cannot predict a CodeQL block on a `util/` script; it cost two
   round-trips here. Read new `util/` scripts for dead imports and mixed import forms first.
4. **An unresolved CodeQL thread blocks the merge with all 17 required contexts GREEN and nothing
   in the checks list naming it.** Diagnose, then resolve, with:

   ```bash
   gh api graphql -f query='query { repository(owner:"pcalnon", name:"juniper-ml") {
     pullRequest(number:N) { mergeStateStatus
       reviewThreads(first:50){nodes{id isResolved path line comments(first:1){nodes{body}}}} } } }'
   gh api repos/pcalnon/juniper-ml/contents/<path>?ref=<branch> --jq '.content' | base64 -d   # prove it is fixed
   gh api graphql -f query='mutation { resolveReviewThread(input:{threadId:"<id>"}) { thread { isResolved } } }'
   ```

   The thread does **not** auto-resolve or go outdated. `BLOCKED` → `CLEAN` on resolution alone.
5. **strict ruleset: ARM auto-merge, THEN `update-branch`** — in that order. An armed net on a
   BEHIND PR waits forever, and a failed `gh pr merge` **disarms** auto-merge silently.
6. **GitHub can wedge the PR object.** After a `createCommitOnBranch` raced an in-flight
   `update-branch`, the ref was at the new commit while REST *and* GraphQL reported the old head,
   and `merge` failed with "head branch is out of date" — a different problem than the real one.
   `git merge-base --is-ancestor` proved the branch correct; **close + reopen** forced the re-sync.
7. **The network was flaky** — two `dial tcp … i/o timeout` / `Connection reset by peer`, one
   mid-ceremony-planning. Dry runs create nothing, so retry. After `--execute`, **verify effects
   and never re-cut**.

---

## 1. What shipped

| package | version | evidence |
| --- | --- | --- |
| **juniper-ml** | **0.9.0** | PyPI `/pypi/juniper-ml/0.9.0/json` → 200; 3/3 publish jobs success |
| **juniper-data** | **0.15.0** | PyPI → 200; **plus** `ghcr.io/pcalnon/juniper-data:0.15.0` and `:0.15` |

**Merged (10)**: ml#1972 (README pin table stale on PyPI + the wheel-contract probe), #1991
(canopy floor `>=0.8.1` + 0.9.0 bump), #1992 (predecessor §8.7/§8.8), #1997 (0.9.0 changelog +
mis-placed-entry repair + the breaking-field fix), #2006 / #2008 (central archives);
juniper-recurrence#177 (the bench `*_full` break); juniper-data#415 (changelog backfill), #416
(0.15.0 proposal), #419 (fold #418). **Closed**: juniper-data#410.

**Releases and archives verified**: tags `v0.9.0` → `abfdfecf`, juniper-data `v0.15.0` →
`46894ba1`; `notes/releases/RELEASE_NOTES_v0.9.0.md` and
`notes/releases/RELEASE_NOTES_juniper-data_v0.15.0.md` both on `origin/main`; `detect` hygiene
`TAG_ONLY=0, NOTES_MISSING=0`.

---

## 2. Four defects reached the same permanent artifact — three unrelated causes, TWO controls needed

`ceremony.py` renders **both** the published Release body and the archived notes from the
CHANGELOG's `## [<version>]` section, and **a Release body is not re-cuttable**. Nothing checks
that the section describes the release. Preview before `--execute` with
`util/ad-hoc/2026-09-12_ceremony_notes_preview.py` — `ceremony.py --dry-run --json` reports the
four planned actions but **omits `plan.archive_content`**, the one artefact worth reading.

**Two controls, not one.** The preview shows what **is** in the changelog; it cannot see a commit
that never reached it. So also diff the tag window (§2 item 4's command). Instance 2 was found that
way and the preview would have missed it entirely.

**And the causes are genuinely unrelated** — do not file them under one label. Instance 1 is an
unbounded `str.partition` in an ad-hoc editor and would have corrupted the changelog even if
`ceremony.py` did not exist; instance 2 is an authoring gap; instance 3 is a defect in the release
train itself. They share a blast radius, not a mechanism. (The numbered "trap N" labels used in
session chatter are **not** defined in any document of record — do not rely on them.)

1. **A mis-placed entry, mine.** `util/ad-hoc/2026-09-21_add_canopy_floor_changelog.py`
   partitioned on the whole rest of the file rather than the `[Unreleased]` slice, so its
   `### Changed` search matched the first such heading anywhere below — inside the
   **already-released `## [0.8.0]`**. It shipped in ml#1991 as `+23` lines of plausible prose.
   The 0.9.0 notes would have **omitted the release's entire point**. Repaired by
   `util/ad-hoc/2026-09-22_relocate_canopy_floor_changelog_entry.py`.
2. **Three image changes absent from juniper-data's `[Unreleased]`** (#405, #408, #392/#394),
   found by diffing `git log v0.14.0..HEAD` against the section. A juniper-data Release mints a
   **container image** as well as a wheel. Backfilled by
   `util/ad-hoc/2026-09-22_backfill_juniper_data_changelog.py`.
3. **`notes_render.py` derived "Breaking changes" solely from a `### Removed` section.** The
   pre-1.0 convention (`detect.py:827`) maps breaking → MINOR, so a breaking change lands under
   `Changed`. juniper-data 0.15.0 would have published **"Breaking changes: NO"** directly above
   *"BREAKING (contract): … `generator_version` 4.0.0"*. Now also honours an uppercase `BREAKING`
   marker (`_is_breaking`, logic at `:259-261`); 5 tests, mutation-checked.
   **The fix is measured only on the two releases it was built for, and does NOT generalise:**
   `juniper-canopy/CHANGELOG.md` has **zero** uppercase `BREAKING` and **six** title-case
   `Breaking Change:` bullets (`:4015`, `:4144`, `:4263`, `:4268`, `:4410`, `:4509`), juniper-deploy
   puts the marker in the section *heading*, and a bullet saying `NON-BREAKING` flips it to YES.
   The five tests were drawn from the found instances, so they encode the same blind spot.
   **Normalise the marker before canopy's next release, or R-7's backfill will reproduce this
   exact defect in the repo this document flags as next up.**
4. **A merge landed between the bump PR and `--execute`.** juniper-data#418 filed under
   `[Unreleased]` — correct normally, wrong here, because **a Release tags the current branch
   head**. Its generator code shipped in 0.15.0 regardless. Folded in by #419. **Always re-check:**

   ```bash
   cd <repo> && git log --oneline <last-tag>..HEAD          # every commit the tag will carry
   sed -n '/^## \[<version>\]/,/^## \[/p' CHANGELOG.md | grep -oE '#[0-9]{3,4}' | sort -u
   ```

**Why 0.15.0's notes name both 4.0.0 and 5.0.0**: it folds two unreleased majors — #395 took
`equities`/`equities_seq` to 4.0.0, #404 to 5.0.0. Both entries are in the section, correctly.

---

## 3. Outstanding work

### Records that still name superseded versions — do these first

| id | where | what to do |
| --- | --- | --- |
| **R-1** | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §10 table, lines ~445 and ~448 | Reads `juniper-data` **0.14.0**, `juniper-canopy` **0.7.0**, `juniper-ml (meta)` **0.8.0**. This is the decision-11 **release record**, and its own closing lesson is "re-probe the registry, never trust the tally". Update to 0.15.0 / 0.8.1 / 0.9.0. |
| **R-2** | the same file, §9 S-7, line **415** | Still cites canopy's pin as `juniper-data-client>=0.4.1,<0.5.0`. It is now **`>=0.5.0,<0.6.0`** (`juniper-canopy/pyproject.toml:192`, raised by canopy#647 on 2026-09-21). The predecessor's §8.3 recorded a correction to `<0.6.0` and **never applied it, and it too is now out of date.** Record the current pin and that S-7's false-comment half is fixed — see C-3. |
| **R-3** | `/home/pcalnon/Development/python/Juniper/AGENTS.md` lines **189-190** | Still says `pip install` serves juniper-data **0.14.0** and juniper-canopy **0.7.0**. Unversioned file: no PR, no CI, invisible to other machines — so it only changes if someone does it deliberately. |
| **R-4** | memory `project_decision_11_released_2026-09-11.md` | Records juniper-data 0.14.0 / juniper-ml 0.8.0 and points at plan §10 as the full record. Both now wrong. |

### Decisions only the owner can take

| id | item |
| --- | --- |
| **R-5** | **`juniper-ml[servers]` floors `juniper-data>=0.14.0`, and that falsifies the headline anyone will quote from this release.** 0.14.0 serves `equities` at `3.0.0`. Proven in a clean venv: install `juniper-data==0.14.0`, then `juniper-ml[servers]==0.9.0` — data stays at **0.14.0**, because `>=0.14.0` is already satisfied. So "5.0.0 is what `pip install` serves" is true only for a **fresh, unconstrained** install. Identical in shape to N-3 (the canopy floor), ruled "raise it" the same day; not applied to data because ml 0.9.0 published at 09:24Z and data 0.15.0 at 18:55Z. **And `tests/test_pyproject_extras.py` now pins `"juniper-data>=0.14.0"`, so a green test guards the stale floor** — the fixture encodes the gap. Raising it means another juniper-ml release. |
| **R-6** | **The release-ceremony lessons are unwritten.** All four §2 shapes belong in `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11.3/§11.4 — which is where they fired and which has been unmodified since 2026-08-29. Right now they live only in this archived prompt. |
| **R-7** | **juniper-recurrence#178** — the path-scoped CI blind spot that hid a 12-failure bench break for 15 days. Four options costed, none picked; the scheduled run is cheapest. |

### Carried tickets — all verified OPEN on 2026-09-22

| id | item |
| --- | --- |
| **C-1** | **juniper-data#411** (predecessor N-5, design S-1 in `…PARTITION-IMPLEMENTATION-PLAN.md` §9). `juniper_data/storage/{hf_store,kaggle_store}.py` emit `X_full`/`y_full`, no `X_val`, `generator_version="1.0.0"` (below floor), and persist it. **Bounding that two reviewers got wrong**: `_cache_store` defaults to a per-instance `InMemoryDatasetStore`, **not** the shared cache, and no route calls them. The shipped `juniper-data/juniper_data/tests/unit/test_hf_store.py:149` asserts `"X_full" in arrays` and passes — **any fix breaks a green test**. Product decision open. |
| **C-2** | **juniper-cascor#668** (predecessor N-6). `juniper_cascor.__version__` is a hardcoded `"0.6.0"`; the distribution is `0.11.0`. |
| **C-3** | **juniper-canopy#559** (`…PARTITION-IMPLEMENTATION-PLAN.md` §9 S-7) — **half of it is already FIXED, and an earlier draft of this handoff got that backwards.** canopy#647 (`e65ea938`, 2026-09-21) corrected the false comment and raised the floor to `juniper-data-client>=0.5.0,<0.6.0` (`juniper-canopy/pyproject.toml:192`); `src/demo_mode.py:1973-1991` now says so itself and cites the issue. The **issue** is untouched since 2026-09-01 (0 comments) but what remains open is only the narrower question its own comment flags: whether `validate_npz_contract` should *also* run as a second, advisory check. Do not re-report the comment as false. |
| **C-4** | **Decision 12 (`partition_provenance`) is UNIMPLEMENTED** — **zero hits in any non-markdown file, ecosystem-wide.** That is the only stable fact here; **do not quote a markdown total.** It measures documents *discussing* the arc, and it moved **28 → 87 → 143 within this one session** as ~20 concurrent sessions created and destroyed worktrees. Three ways to get it wrong, all hit here: the sweep emits `worktrees/…` with **no leading `./`**, so `grep -v '/worktrees/'` matches nothing and silently returns the unfiltered figure (a filter that matches nothing reads exactly like one that changed nothing); `wc -l` / `grep -c` undercount a capture with no trailing newline; and run from inside a worktree it counts the handoff you are writing. **Enumerate, do not count.** Filtering `worktrees/` properly leaves **7 real files**, all in the primary juniper-ml checkout: `docs/REFERENCE.md`, the design, the plan, and four handoffs. |
| **C-5** | **juniper-ml `[tools]` pins `juniper-model-core>=0.1.0,<0.4.0`** — admits 0.3.1 without requiring 0.3.2. Left deliberately (docs-only difference); re-shipped unchanged inside 0.9.0. `juniper-cascor-client>=0.8.0` is the measured guard boundary and unchanged. |

### Known and bounded — no action implied

- **The published juniper-data 0.15.0 wheel ships its test suite**: 97 of 201 members. Fixed by
  juniper-data#420, merged 19:05:53Z — three minutes after the archive PR and **after** the tag,
  so 0.16.0 is clean and 0.15.0 permanently is not. Distinct from #405, which fixed the *image*.
- **Seven packages read `UNRELEASED_CHANGES`, not three.** An earlier draft said three because the
  §4 command is `--package`-scoped. Run `detect.py` **unscoped** — 18 packages, 7 unreleased:
  juniper-cascor (8), **juniper-cascor-model (7)**, juniper-recurrence (7), juniper-canopy (6),
  juniper-observability (2), juniper-service-core (1), **juniper-cascor-worker (1)**. The two in
  bold were never asked about, and cascor-model carries as many ship items as juniper-recurrence.
  This is the ecosystem `AGENTS.md` lesson again: *a repo absent from the sweep's scope is absent
  from its answer.* **`juniper-canopy` and `juniper-cascor-worker` both raise
  `! changelog … under-documented`** — §2's completeness failure is pre-armed for two packages, not
  one. Use `util/ad-hoc/2026-09-22_backfill_juniper_data_changelog.py` as the pattern, and read §2
  item 3 first: the breaking-field fix will **not** catch canopy's house style.
- **Three more open issues on-topic and unnamed until now**: **juniper-data#409** (equities /
  equities_seq at bare defaults produce data consumers cannot train on — about the generators this
  release exists to ship), **juniper-cascor#582** (the service promotes `X_test` to in-loop
  validation while the CLI trains with no val at all), and **juniper-cascor-client** carrying the
  byte-identical `[Unreleased]` lockfile-signing bullet dispositioned below for data-client — the
  disposition was applied to one of two identical cases.
- **juniper-data-client needs no release** — its `[Unreleased]` is a `lockfile-update.yml` fix and
  workflows are not packaged. Dispositioned, not outstanding.
- **Behavioural coverage, with a caveat about its own instrument.**
  `util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py` covered 7 of 9 decision-11 packages
  on 2026-09-21. **The "37 checks" figure is not reproducible without naming the environment** —
  re-run in the ambient `JuniperCascor1` it reads `PASS=24 FAIL=10 SKIP=4` against stale local
  pins, not the published wheels. It needs **two purpose-built venvs** (`[servers]` is not in the
  meta-package install), and **`main()` returns `n_fail` only, so SKIP scores as success** — a venv
  missing everything exits 0. Re-run it against 0.9.0/0.15.0 before trusting the coverage claim;
  the `[servers]` floor changed under it. **Not** covered then or now: `juniper-canopy` 0.7.0
  (wheel unimportable — 0.8.1 is fine) and `juniper-recurrence-client` 0.3.0 (needs a live
  service); the **producer** side of the equities entity-major exception is also unverified.
- **Stale conda pins**: `JuniperCascor1` has `juniper-recurrence-model 0.1.5` and
  `juniper-service-core 0.5.0`, both below juniper-recurrence 0.5.0's floors. Self-heals on the
  documented `pip install -e "juniper-recurrence/.[test,observability]"`. **`pip check` is not a
  pass/fail signal here** — that env also has two unrelated `cuda-python` conflicts, so it exits 1
  either way. Do **not** sweep shared envs; ~20 sessions run concurrently.
- **A recorded package version does not tell you what code an env serves.** `JuniperData` records
  data-client 0.4.2 and `JuniperCascor1` records 0.5.0, but both resolve to the repo working tree.
  Read the module path, not `pip list`.
- **`NPZ_SPLITS` is not on the top-level `juniper_data_client` namespace at 0.5.0 either** — it
  lives in `.constants`. A probe reading the top level returns ABSENT for the *correct* version
  and cannot discriminate. This one re-fired on the reconciler mid-session.

---

## 4. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mellow-hugging-dahl
git fetch -q origin && git status --short && git log --oneline -1 origin/main   # expect: clean, at origin/main
# Both releases live -- version-specific endpoint; the AGGREGATE lags via Fastly and is not evidence:
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ml/0.9.0/json      # 200
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-data/0.15.0/json   # 200
# The image half. `gh api .../packages/...` 403s without read:packages; GHCR reads anonymously:
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:pcalnon/juniper-data:pull" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
curl -s -H "Authorization: Bearer $TOKEN" https://ghcr.io/v2/pcalnon/juniper-data/tags/list   # includes 0.15.0, 0.15
# Release state. UNSCOPED -- the scoped form under-reports (see section 3). Needs network; exit 1 is NORMAL:
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper
# 18 packages: UNRELEASED_CHANGES=7, UP_TO_DATE=11; hygiene TAG_ONLY=0, NOTES_MISSING=0
python3 -m unittest tests.test_release_train_ceremony tests.test_pyproject_extras   # Ran 120 tests, OK
```

Two expected surprises: the unittest line emits `WARNING: release-train ceremony: could NOT file
the HALT issue for juniper-service-core … HTTP 403` — **pre-existing, not a HALT you caused**; and
`detect.py` resolves released versions from PyPI, so a network blip reads like a release regression.

**To run a ceremony at all** (undocumented in the publish procedure, which covers only the manual
path): `detect.py --json > manifest.json` → `ceremony.py --manifest manifest.json --package <pkg>
--repo-root . --ecosystem-root … --dry-run` → preview the notes → re-run with `--execute`, adding
`--cross-repo` for a sibling repo. `--dry-run` overrides `--execute`. `--manifest` is required.

---

## 5. Git status, and every script this session added

Worktree clean on `worktree-mellow-hugging-dahl` at `origin/main` except this file and
`util/ad-hoc/2026-09-22_fold_pr418_into_juniper_data_0_15_0.py`, **which ship together in the
handoff PR — opening that PR is the one unfinished action of this session.** No *session* branch
carries unmerged work; all were auto-deleted on merge (juniper-ml has 100+ unrelated branches, so
read that claim narrowly). CI on `main` verified green after every merge in all three repos.

**Sibling checkouts**: `juniper-recurrence` is clean at `origin/main`. **`juniper-data` is clean
but ONE COMMIT BEHIND** — `origin/main` is `6c81cc4` (juniper-data#420, the wheel-ships-tests fix,
merged 19:05:52Z), while the local checkout sits at `46894ba` = the `v0.15.0` tag. `pull` before
running `propose.py`/`ceremony.py` there, or a whole-file API commit will carry stale content.
`detect.py` is unaffected — it diffs `<tag>..origin/main`, not the checkout.

Eleven `util/ad-hoc/` scripts, ten committed:

| script | purpose | safe to re-run? |
| --- | --- | --- |
| `2026-09-21_sync_readme_compat_table.py` | regenerates README's Ecosystem Compatibility table from `pyproject.toml` | yes — idempotent, `--check` mode |
| `2026-09-21_add_readme_compat_guard.py` | inserts `ReadmeCompatTableTest` into `tests/test_pyproject_extras.py` | yes — detects its own guard |
| `2026-09-21_add_changelog_entry.py` | the README-fix changelog entry | yes — marker-guarded |
| `2026-09-21_decision11_wheel_contract_probe.py` | 37 behavioural checks over the published wheels | yes — read-only; needs two venvs |
| `2026-09-21_raise_canopy_floor_0_8_1.py` | the ten-site canopy floor raise **+ version bump** | **NO** — would re-bump post-release |
| `2026-09-21_add_canopy_floor_changelog.py` | **the one with the partition bug** (§2 item 1) | **NO** — superseded; do not reuse the pattern |
| `2026-09-21_fix_bench_full_derivation.py` | patches juniper-recurrence's `bench/datasets.py` | cross-repo mutator; `--root` copy only |
| `2026-09-22_relocate_canopy_floor_changelog_entry.py` | moves the mis-placed entry into `[Unreleased]` | yes — no-ops once moved |
| `2026-09-22_open_juniper_ml_0_9_0_changelog_section.py` | opens `## [0.9.0]` from `[Unreleased]` | yes — no-ops if the section exists |
| `2026-09-22_backfill_juniper_data_changelog.py` | **the pattern for R-7's canopy/worker backfill** | yes — marker-guarded, `--root` copy |
| `2026-09-22_fold_pr418_into_juniper_data_0_15_0.py` | folds a post-bump merge into the release section | yes — no-ops when `[Unreleased]` is empty |

---

## 6. What this evidence cannot support

- **"Both releases are correct" is narrower than it sounds.** Verified: versions resolve, wheels
  install, the published 0.15.0 wheel reads `5.0.0`, and the notes describe every shippable
  commit. **Not** verified: that 0.15.0's runtime behaviour is correct. No service was started
  against it and the equities generators need network.
- **The image shipped BEFORE the wheel**, because `publish-image.yml` has no approval gate and
  `publish.yml` does. There was a window where `ghcr.io/…:0.15.0` existed and
  `pip install juniper-data==0.15.0` did not. Inherent to a two-artifact release.
- **Nothing here re-measured the decision-11 contract itself.** `X_val` correctness and the
  normaliser leak (juniper-data#314/#323) remain upstream findings taken as given. The
  predecessor's `R-5` reference is **unresolvable** — at least three colliding `R-5` schemes exist
  in `prompts/`, and one is recorded closed; do not chase it without a filename.
- **The seven `UNRELEASED_CHANGES` packages were surfaced, not audited.** Counts come from
  `detect`; nobody diffed their changelogs against their commits — the check that found three
  defects here.
- **Consensus record** (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §7).
  **Instruments**: 3 Lane A (live-system re-probe; fresh-session procedure audit; omission hunt
  reconstructed from the repos, not the document) + 1 Lane B (adversarial conclusion attack), one
  round, on a **draft** of this file. Every load-bearing finding was re-derived by the reconciler
  before acceptance — which mattered, because the lanes disagreed and one was wrong.
  **What round 1 changed**: it added the goal statement and the release-authorisation posture (the
  two things that made this a handoff rather than a status report), R-1..R-7, the per-script table
  and the ceremony pipeline; and it corrected the ad-hoc script count (8 → 11, a glob matching 50
  files replaced by names), `UNRELEASED_CHANGES` (3 → 7), C-3 (canopy#559's comment half is
  **already fixed** — the draft had it backwards), C-4, R-5 and §5's sibling-clean claim.
  **Dissent resolved by measurement, not by vote**: two lanes disagreed on whether excluding
  worktrees changes the `partition_provenance` sweep. The procedure auditor measured "28 either
  way, the exclusion is inert"; the factual re-prober measured 7. **The re-prober is right** — the
  auditor's `grep -v '/worktrees/'` never matched, because the sweep emits `worktrees/…` with no
  leading `./`. A silently-failing filter and an inert filter are indistinguishable from the
  output alone.
  **Dissent resolved against a reporter**: "six session branches remain undeleted" — **refuted**,
  `git/matching-refs` returns 0 for each.
  **Not verified**: the per-repo breakdown of the worktree-copy mentions (the pruned sweep exceeded
  280 s twice, and the total is unstable anyway — see C-4). **No round 2 was run on these
  corrections**, and the procedure warns the fix pass is the least trustworthy part of any
  document; treat §2 item 3's marker-normalisation claim and C-3's disposition as the two most
  worth re-checking.
