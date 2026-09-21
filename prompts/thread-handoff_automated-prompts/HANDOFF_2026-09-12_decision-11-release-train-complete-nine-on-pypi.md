# HANDOFF — decision 11's release train is COMPLETE; nine packages on PyPI, verified from the wheels

**Date**: 2026-09-12 (re-verified 2026-09-15; **re-evaluated 2026-09-21 — see §8, which
OVERTURNS §0.2 and §1's "the arc is DONE / next actions: none"**) ·
**Session**: <https://claude.ai/code/session_01NJpynt9LppyG42HASEYnJN>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/immutable-orbiting-thimble`
**Branch**: `main` (no branch of its own — every change shipped as an API-signed PR)
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md`
(this document **closes** its §1–§4; its §5 dispositions were re-derived and are restated below)

**Documents REFERENCED** (ecosystem convention — more than one cited, so every reference carries its filename):

- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — **§10 is the release record**
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — design of record
- `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` — §11, the release ceremony
- `docs/REFERENCE.md` § *Train / Val / Test Partition Contract*; `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` `:317`/`:769`
- `util/release_train/{registry.yaml,detect.py,propose.py,ceremony.py}` — the instrument

**Documents CHANGED by this session** (all juniper-ml unless noted): `docs/REFERENCE.md`,
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`,
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`, `pyproject.toml`,
`tests/test_pyproject_extras.py`, `AGENTS.md`, `README.md`, `docs/QUICK_START.md`, `CHANGELOG.md`,
`juniper-model-core/{CHANGELOG.md,juniper_model_core/_version.py}`,
`util/release_train/notes_render.py`, `tests/test_release_train_ceremony.py`,
`util/ad-hoc/{2026-09-10_restore_lock_header.py,2026-09-10_verify_published_wheels.py,2026-09-10_bump_extras_table.py,2026-09-11_cascor_client_guard_boundary.py}`,
`notes/releases/RELEASE_NOTES_{v0.8.0,juniper-model-core_v0.3.2,juniper-recurrence_v0.5.0}.md`,
and this file. Sibling: `juniper-recurrence/juniper-recurrence/{pyproject.toml,CHANGELOG.md,requirements.lock,juniper_recurrence/_version.py}`,
`juniper-recurrence/AGENTS.md`. Unversioned: `/home/pcalnon/Development/python/Juniper/AGENTS.md` § Data Contract.

---

## 0. PREFLIGHT

1. **Local `git commit` HANGS** (`commit.gpgsign=true`, YubiKey). Every commit went through the
   GitHub API: `util/open_signed_pr.py` for a new branch, `util/ad-hoc/push_signed_commit.py` for a
   follow-up. Never `git commit` / `git tag` / `git push` locally.
2. **The arc is DONE.** Nothing here is blocked or owed. Items below are *carried forward*, not
   in-flight.
3. **`gh` GraphQL has a SECONDARY (abuse) limit that `gh api rate_limit` does not report.** It
   read `5000/5000` while `createCommitOnBranch` failed with *"API rate limit already exceeded"*.
   It clears in minutes. **A failed `open_signed_pr.py` can leave the branch created with no
   commit and no PR** — delete the ref before retrying, or you get a bare branch at main.
4. **`JuniperCascor1` was rebuilt 3.13 -> 3.14.7 on 2026-09-12 and is now REPAIRED.** For a window
   it had 56 packages against the old tree's 419, and TEN Juniper console scripts were dead on a
   `#!/.../python3.13` shebang -- including `juniper-check-doc-links` (a pre-commit hook) and both
   sequence-safety screens, `juniper-symbol-loss-check` / `juniper-docs-additions-check`. **A screen
   that cannot run looks exactly like a screen that passed.** Verified repaired 2026-09-15: 448
   packages, all ten scripts execute, and the six editable siblings are back at their POST-decision-11
   versions (cascor 0.11.0, data 0.14.0, data-client 0.5.0, recurrence 0.5.0, recurrence-client 0.3.0,
   cascor-client 0.8.0). Still stale as non-editable pins in that env: `juniper-ml==0.6.0`,
   `juniper-model-core==0.2.0`, `juniper-canopy==0.5.0`, `juniper-ci-tools==0.8.0`,
   `juniper-doc-tools==0.1.1`. `Juniper/AGENTS.md` still documents the env as Python **3.13.13**.
5. **Use NATIVE auto-merge, not `safe_merge.py`, on juniper-ml.** `strict_required_status_checks_policy`
   means every other session's merge restarts your CI; `safe_merge` pins to a SHA and loses.
   Observed here: #1899's pending count went 13→8→3→1→**6**. `gh pr merge N --squash --auto` tracks
   the PR. (`safe_merge` also exits **0** while refusing.)

---

## 1. Goal statement

**Decision 11 is released. Nine packages are on PyPI and verified from the published wheels.**

| package | version | package | version |
| --- | --- | --- | --- |
| juniper-data | 0.14.0 | juniper-recurrence-model | 0.3.0 |
| juniper-data-client | 0.5.0 | juniper-recurrence-client | 0.3.0 |
| juniper-cascor | 0.11.0 | juniper-recurrence | 0.5.0 |
| juniper-canopy | 0.7.0 | juniper-model-core | 0.3.2 |
| | | **juniper-ml** | **0.8.0** |

`detect` reads `UP_TO_DATE` for all nine. Verification is behavioural, from a clean venv, not the
checkout — `util/ad-hoc/2026-09-10_verify_published_wheels.py`.

**Merged this session (12)**: ml#1865 (straggler currency), #1873 (model-core 0.3.2 bump), #1874 /
#1901 / #1907 (release-notes archives), #1875 (renderer fix), #1876 (eight floors), #1899 (0.8.0
bump), #1906 + #1915 (the §10 release record and its correction); juniper-recurrence#163 (model
floor + re-lock) and #164 (0.5.0 bump).

**Next actions: none for this arc.** Pick up §3.

---

## 2. Two defects found and fixed that the predecessor did not know about

- **The archive renderer failed EVERY archive PR's own pre-commit.**
  `util/release_train/notes_render.py` returned `"\n".join(lines) + "\n"` over a list already ending
  in `""`, so a final body ended `\n\n`; `end-of-file-fixer` rewrote it and the hook exited 1
  (ml#1874: three Pre-commit jobs + Quality Gate red on **one byte**). Fixed in ml#1875 —
  `rstrip("\n") + "\n"`, three tests, mutation-checked. **Confirmed in production**: ml#1901's and
  ml#1907's archives ended with exactly one `\n` and merged clean.
- **juniper-recurrence#162 added a `requirements.lock` two days before the floor bump.** Its
  `Dockerfile` runs `pip install -r requirements.lock` then `pip check`, and the lock pinned
  `juniper-recurrence-model==0.2.0` — the version the new floor forbids. Bumping the floor alone
  would have been a hard **image-build** failure. Re-locked in the same PR (#163): exactly two pins
  moved, count unchanged at 31, arm64 pre-flight re-run clean.

---

## 3. Carried forward — each RE-DERIVED, not transcribed

| item | state (verified 2026-09-11/12) |
| --- | --- |
| **S-1 hf/kaggle stores** | STILL TWO-WAY. `juniper_data/storage/hf_store.py:110` / `kaggle_store.py:212` cut `X[:n_train]`,`X[n_train:]`; write `X_full`/`y_full` at `:147`/`:244`; emit **no `X_val`**. Product decision open. |
| **Decision 12** (`partition_provenance`) | UNIMPLEMENTED. Zero Python hits ecosystem-wide; every match is documentation. |
| **Plan §9 S-7** | juniper-canopy#559, **OPEN**. |
| **`juniper-model-core` floor** | `[tools]` pins `>=0.1.0,<0.4.0`. A fresh install gets **0.3.2**; the cap does not *forbid* 0.3.1 (pinning it alongside `juniper-ml[tools]==0.8.0` resolves). Left deliberately. |
| **`juniper-cascor-client`** | floored at `>=0.8.0` — the **measured** guard boundary (0.5.0/0.6.0/0.7.0 all unguarded; probe: `util/ad-hoc/2026-09-11_cascor_client_guard_boundary.py`). |

**Other sessions' post-release state, surfaced not touched**: juniper-canopy is
**`BUMPED_NOT_RELEASED` at 0.8.0**; juniper-cascor has 6 unreleased ship items; juniper-data 2;
juniper-data-client has an `[Unreleased]` entry its version does not reflect.

---

## 4. The traps worth the next session's time

- **`detect.py` CANNOT SEE a docs-only staleness in a published package.** It discounts those diffs
  (`0/0/3`, all *discounted*) and scores `UP_TO_DATE`, so the ceremony never proposes the release.
  That is how model-core served a retired contract under an unchanged `0.3.1` for four days. **No
  instrument will raise it** — a docs fix to a published package needs its patch release decided at
  fix time.
- **A merged bump is NOT a release.** model-core 0.3.2 was bumped in ml#1873 and then left
  unreleased for most of the arc — no tag, no Release, PyPI on 0.3.1 — because the session moved on.
  It was caught only by a final `curl` sweep (404 against eight 200s) after being reported as
  published for hours. **Re-probe the registry; never trust the tally.**
- **A held-open PR accumulates the whole contention window.** ml#1876 waited on an owner gate and
  collected five merges into its seven files, going `DIRTY`. Whole-file API uploads would have
  reverted them. Recovery: reset to `origin/main`, re-run the edit *scripts*, prove with
  `git diff --stat origin/main`. **Hand edits cannot be replayed that way** — that is the real
  argument for scripting a multi-file bump.
- **Two colliding `S-1…S-8` schemes.** Plan §9 numbers *design findings*; the 2026-09-09 handoff §5
  numbers *release stragglers*, and its table uses both — asserting S-7 is open and fixed. Both true,
  different S-7s. Establish the scheme before acting.

---

## 5. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/immutable-orbiting-thimble
git fetch -q origin && git status --short && git log --oneline -1 origin/main
# All nine UP_TO_DATE (exit 1 whenever anything is not -- expect 1 here because SIBLINGS have moved):
python3 util/release_train/detect.py --repo-root . --ecosystem-root /home/pcalnon/Development/python/Juniper \
  --package juniper-ml --package juniper-model-core --package juniper-data-client --package juniper-data \
  --package juniper-cascor --package juniper-canopy --package juniper-recurrence \
  --package juniper-recurrence-model --package juniper-recurrence-client
# PyPI truth -- all nine must be 200:
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ml/0.8.0/json
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-model-core/0.3.2/json
# Behavioural, from the PUBLISHED wheels (the only check that distinguishes repo from deployment):
python3 -m venv /tmp/v && /tmp/v/bin/pip install -q "juniper-ml[clients,tools,recurrence]==0.8.0"
/tmp/v/bin/python util/ad-hoc/2026-09-10_verify_published_wheels.py   # expect ALL ... PASSED
```

---

## 6. Git status at handoff

This worktree is clean on `main` at `origin/main`. No local branch carries work; every change
merged. No worktrees were created by this session. The three `*--feature--drop-full-family--20260905-*`
worktrees under `Juniper/worktrees/` were left alone, as before.

---

## 7. What this evidence cannot support

- **The behavioural verification covers two packages, not nine.** `derive_full_split` (recurrence-model
  0.3.0) and `NPZ_SPLITS` (data-client 0.5.0) were exercised on real arrays; the other seven were
  verified by *resolution* (the floors resolve, the wheels install) and by reading published metadata
  — not by running their code.
- **Nothing here re-measured the decision-11 CONTRACT itself.** This arc released what earlier arcs
  built; `X_val` correctness, R-5, and the normaliser leak are all upstream findings taken as given.
- **The "four days" figure for model-core's staleness** is from ml#1829's merge date to 0.3.2's
  release, not from the moment the docstring became wrong.

---

## 8. RE-EVALUATION 2026-09-21 — the arc is NOT done

**Session**: <https://claude.ai/code/session_013rU7NHHRozgkhNqBFnAHYA> ·
**Worktree**: `juniper-ml/.claude/worktrees/mellow-hugging-dahl` · **Branch**: `main` at `d721fc78`

**§0.2 and §1 are now FALSE.** "The arc is DONE. Nothing here is blocked or owed" and
"Next actions: none for this arc" were true on 2026-09-15 and are not true today. The
release itself still holds — all nine packages return HTTP 200 at the stated versions —
but four untracked decision-11 defects have surfaced, one of them a live consumer break.

### 8.1 Still true, each RE-DERIVED (not transcribed)

| item | verdict 2026-09-21 |
| --- | --- |
| Nine packages on PyPI at §1's versions | **HOLDS** — all nine HTTP 200 |
| S-1 hf/kaggle stores two-way | **UNCHANGED in the repo — but §3's row UNDERSTATES it. See N-5.** |
| Decision 12 `partition_provenance` | **UNCHANGED** — zero hits in any non-markdown file ecosystem-wide; 7 `.md` files |
| Plan §9 S-7 → juniper-canopy#559 | **STILL OPEN**, untouched since 2026-09-01 |
| `juniper-model-core` floor `>=0.1.0,<0.4.0` | **UNCHANGED**, still deliberate |
| `juniper-cascor-client>=0.8.0` | **UNCHANGED** |
| §2's two fixes (`notes_render.py`, recurrence lock) | **INTACT** |

### 8.2 Resolved since — do not re-do

- **juniper-canopy's `BUMPED_NOT_RELEASED at 0.8.0` is CLOSED.** 0.8.0 *and* 0.8.1 are
  published; `detect` reads `UP_TO_DATE`.
- **§0.4's "`Juniper/AGENTS.md` still documents the env as Python 3.13.13" is FIXED** —
  `/home/pcalnon/Development/python/Juniper/AGENTS.md` now reads **3.14.7**. (The
  `JuniperCanopy1` row still says 3.13.13; different environment, unverified.)
- **juniper-data-client needs NO release**, closing §3's last row: its `[Unreleased]` entry
  is a `lockfile-update.yml` fix and workflows are not packaged, and `detect`'s single
  discounted diff is genuinely test-extra-only (`pyyaml` under `[test]`; the published
  0.5.0 `METADATA` runtime deps match `pyproject.toml` exactly). §4's docs-only-staleness
  trap did **not** fire here.
- **juniper-ml needs NO release for its own `[Unreleased]`** — the 0.8.0 wheel is
  metadata-only (five `dist-info` files, no modules), so perf-lane notes and
  `util/ad-hoc/` scripts ship nothing.
- cascor's 7 and juniper-recurrence's 7 unreleased ship items contain **no** decision-11
  content (partial-data / truncation, and model snapshots, respectively).

### 8.3 Corrections to documents of record

1. **`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §9 S-7
   cites a pin that has moved.** It reads `juniper-data-client>=0.4.1,<0.5.0` at
   `juniper-canopy/pyproject.toml:148`; that line now reads **`<0.6.0`**. The cap was
   widened, so decision-11's data-client **is** admissible by canopy — there is no
   meta-package resolution conflict. The widening makes **canopy#559 stronger, not weaker**:
   `juniper-canopy/src/demo_mode.py:1974` still says `validate_npz_contract` is "absent from
   the pinned / published juniper-data-client (0.4.x)", and that symbol **is** present in the
   published 0.5.0 wheel (`juniper_data_client/contract.py:45`), now inside canopy's declared
   range.
2. **A recorded package version does not tell you what code an env serves.** `JuniperData`
   records `juniper-data-client 0.4.2` and `JuniperCascor1` records `0.5.0`, but **both**
   resolve `juniper_data_client` to the repo working tree and yield
   `NPZ_SPLITS == ('train','val','test')`. Any claim that decision 11 "is not deployed" in
   those envs is an artifact of reading `pip list`. Only `JuniperCanopy1` runs a real
   non-editable 0.4.1 — and that is exactly its **declared floor**, not below it.
3. **`NPZ_SPLITS` is not on the top-level package namespace at 0.5.0 either.** It lives in
   `juniper_data_client.constants` (re-exported into `contract`). A probe reading
   `juniper_data_client.NPZ_SPLITS` returns `ABSENT` for the *correct* version and cannot
   discriminate. Use `from juniper_data_client.constants import NPZ_SPLITS`.

### 8.4 NEW outstanding work — none of it tracked by any issue or PR

**N-1 — juniper-recurrence's bench harness is BROKEN by decision 11, and CI cannot see it.**
`juniper-recurrence/bench/datasets.py:52` is `return np.asarray(out[f"{key}_full"])` — a bare
subscript, called for `X`/`y`/`dt`/`target_dt` across all 7 bench datasets, against output
from real juniper-data generators. Proven end-to-end, not inferred:
`datasets.irregular_sine(n_steps=200, lookback=8)` → **`KeyError: 'X_full'`**, and the
generator emits exactly the three partitions with no `_full`. **Why no one saw it:** the
`test` job in `juniper-recurrence/.github/workflows/ci-recurrence-bench.yml` is
`if: needs.changes.outputs.bench == 'true'`, and decision 11 changed *juniper-data*, not
`bench/` — so the job has been **skipped** while the aggregate `Bench required checks`
reports **success** (verified on run 35573944068, 2026-09-21). The aggregate treats `skipped`
as a pass **by documented design** so it can be a required check; that is not the defect.
*A path-scoped lane cannot detect a break introduced by a dependency.* This is the only
remaining hard `_full` require in the repo — `juniper_recurrence_model/data.py:116` *writes*
the derived key and is correct. Fix: concatenate `train|val|test`, via
`derive_full_split` so the `equities`/`equities_seq` entity-major order is preserved.

**N-2 — juniper-data carries two BREAKING `generator_version` majors, merged and UNRELEASED.**
Published `juniper-data` 0.14.0 serves `equities` and `equities_seq` at `VERSION = "3.0.0"`
(read from the wheel, not the checkout); `main` has both at **`"5.0.0"`**. The
`[Unreleased]` changelog carries #395 (→4.0.0, causal share history) and #404 (→5.0.0, the
opening-filing scale typo: AIZ 990×, EOG 428×). `/home/pcalnon/Development/python/Juniper/AGENTS.md`
documents 5.0.0 as the live contract; `pip install juniper-data` does not deliver it.
**Severity is deployment divergence, not live corruption** — no container is running, nothing
listens on `:8100`, and the `JuniperData` env resolves the 5.0.0 checkout, so PyPI carries
neither the 4.0.0 regression nor the 5.0.0 fix. This is §4's "a merged bump is NOT a release"
firing again. **Owner-gated: release ceremony is Paul's.**

**N-3 — `juniper-ml[servers]` floors a wheel that cannot import itself.** `pyproject.toml:47`
reads `juniper-canopy>=0.7.0`. Every canopy wheel **0.5.0–0.8.0** publishes **zero** top-level
modules (`juniper_canopy/` holds only `__init__.py`; `import demo_mode` →
`ModuleNotFoundError`); **0.8.1** ships all 19. canopy#631 closed 2026-09-17. A default resolve
takes 0.8.1, so the floor *admits* rather than *delivers* the broken wheels — the same shape as
the `juniper-model-core` row in §3, but with the opposite conclusion, because there the
difference was docs-only and here the admitted wheel is non-functional. **Recommend raising to
`>=0.8.1`; not done here, because it is a floor-policy change that wants an owner call.**

**N-4 — `README.md`'s second pin table shipped to PyPI stale. FIXED THIS SESSION.** The file
carries two pin tables; `tests/test_pyproject_extras.py` guarded only the "Available Extras"
one. The flat `| Package | Pin |` table still advertised the **0.6.0** floors — naming that
version in its own lead-in — with five stale pins and five packages missing. `README.md` is the
`long_description`, so those rows were live on pypi.org for 0.8.0: the published `METADATA`
says "matching `juniper-ml` 0.6.0" at line 82 and lists the correct `[servers]` floors at line
136, in one document.

**N-5 — S-1 is not just a split shape: the PUBLISHED wheel ships it, stamps it BELOW the floor,
persists it, and a shipped test PINS it.** §3's S-1 row records the two-way cut and calls the
product decision open. Four facts it does not record, all read from the published
`juniper_data-0.14.0-py3-none-any.whl`, not the checkout:

1. `juniper_data/storage/hf_store.py:121` stamps `generator_version="1.0.0"` — **below decision
   11's 3.0.0 floor**, on a path `pkgutil.iter_modules` never reaches because it is not under
   `juniper_data.generators`, so `test_val_emission_guards.py` cannot see it.
2. `:142-149` emits `X_train`/`y_train`/`X_test`/`y_test`/`X_full`/`y_full` — the retired family,
   and **no `X_val`**.
3. `:151` `self._cache_store.save(...)` **persists** those keys into an artifact.
4. The wheel's own `juniper_data/tests/unit/test_hf_store.py:149` is `assert "X_full" in arrays`,
   and it **passes** — the defect is pinned by a green test, so any fix breaks it. (Fixture
   encodes the defect.)

**Bounding it, because two reviewers overstated this.** `_cache_store` defaults to a per-instance
`InMemoryDatasetStore` (`:50`), **not** the shared on-disk cache the generators serve from — a
caller must inject that. And the only references to `get_hf_store` / `get_kaggle_store` anywhere
in the wheel are export plumbing in `storage/__init__.py`: **no route and no service path calls
them**. So this is a non-conforming *public API surface*, reachable by an external caller, not a
live production emission. The `1.0.0` stamp also means the `dataset_id` hash keeps these from
ever being served against a 3.0.0-contract request — the floor protects by accident.

**N-6 (minor, cascor)** — `juniper_cascor.__version__` is the string `"0.6.0"` while the
distribution is **0.11.0**: a hardcoded literal drifting from `pyproject.toml`. canopy fixed this
class by reading `importlib.metadata`.

### 8.5 §7 L-1 is now substantially CLOSED

§7 conceded "the behavioural verification covers two packages, not nine". A Lane A pass entering
from the published wheels closed most of that gap:
`util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py` (new) runs **37 import-guarded checks**
against wheels installed into clean venvs — **19 PASS / 0 FAIL** in a
`juniper-ml[clients,tools,recurrence]==0.8.0` venv and **24 PASS / 0 FAIL** in a servers venv
(the split is required: `[servers]` is not in the meta-package install). Skips are labelled and
counted, never silently passed. The wheel's own shipped suites were also run: 155 passed across
`test_val_emission_guards` / `test_partition_sizing` / `test_meta_dispatch` / `test_split` /
`test_normaliser_fit_scope`, plus 25 in `test_hf_store`.

**Now verified BEHAVIOURALLY (7 of 9)**: juniper-ml, juniper-model-core, juniper-data,
juniper-data-client, juniper-cascor, juniper-recurrence, juniper-recurrence-model. Highlights:
cascor's `_resolve_validation_split` exercised on all three §6.1 rules — rule 3 refuses **even
with `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT=true`**; `data_provider` tolerates a legacy
`_full`, requires it never, and forbids it never; juniper-data's full `POST /v1/datasets` →
`GET /artifact` roundtrip through the real ASGI app served exactly six keys at
`generator_version=3.0.0`, validated by data-client 0.5.0.
**Still NOT behaviourally verified (2 of 9)**: `juniper-canopy` **0.7.0** — its wheel is
unimportable (N-3), so only inspection was possible, and 0.8.1 was exercised instead; and
`juniper-recurrence-client` 0.3.0 — import and signature only, since a request needs a live
service. Also unverified: the **producer** side of the equities entity-major exception (those
generators need network / raise `InputTooLargeError` at default params), so only the consumer
side (`derive_full_split`) is proven.

### 8.6 Consensus record (procedure §7)

`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
**Lanes**: 2 Lane A (live-system re-probe; document-chain omission hunt) + 1 Lane B
(adversarial conclusion attack) + 1 Lane A from a distinct entry point (published wheels).
**Iterations**: 1 complete (4 lanes, all reported); §8.3 and the dissent list below are its output, each
re-derived by the reconciler before being written here.
**Convergence — the signal a finding is real, per §2**: **N-3** was reached independently three
times, from three entry points (reconciler via wheel download; omission hunt via the doc chain;
wheel lane via `import backend.service_backend` failing). **N-2** twice. **N-5** twice (omission
hunt from the enforcement surface, wheel lane from executing the store).
**Dissent not resolved in the reporters' favour, recorded per §5.3** — every one re-derived by
the reconciler before being written or rejected:

- The omission hunt called `test_val_emission_guards.py`'s `>= 3` assert "subsumed and dead" and
  its allow-list a defect. **Rejected**: the floor assert fires first with its own message, and
  the allow-list is deliberate — the test's own text is "a generator that moves on its own needs
  its reason recorded here". The parent `AGENTS.md` describes both halves accurately.
- The same lane attributed N-1's invisibility to `pytest.importorskip`. **Corrected**: the
  `[bench]` extra *does* install juniper-data, so it would not skip; the real cause is the
  job-level path filter. Symptom right, mechanism wrong — the documented pattern.
- Both the omission hunt and the wheel lane placed N-5's writes in "the same cache the generators
  serve from". **Bounded**: `_cache_store` defaults to a per-instance `InMemoryDatasetStore`, and
  no route calls these stores at all.
- The adversarial lane cited a live `pytest` process in `JuniperData` as evidence another session
  was mid-run. **It was this session's own** `test_val_emission_guards.py` run. Its conclusion
  stands on its other grounds; that evidence does not support it.
- The reconciler's own first `NPZ_SPLITS` probe read the top-level package namespace, where the
  symbol is absent **at 0.5.0 too** — non-discriminating. Re-probed against `constants`.

**What this evidence cannot support**: N-2's severity rests on nothing running *now* — it says
nothing about artifacts minted while a 4.0.0 deployment was live. N-1 was proven end-to-end for
`irregular_sine` and for the other six by shared call site, not by running each. The **producer**
side of the equities entity-major exception is still unverified (network / `InputTooLargeError`),
so only `derive_full_split`'s consumer side is proven. `juniper-canopy` 0.7.0 and
`juniper-recurrence-client` 0.3.0 remain un-exercised (§8.5). Nothing here re-measures the
decision-11 contract itself; §7's L-2 and L-3 stand unchanged.
