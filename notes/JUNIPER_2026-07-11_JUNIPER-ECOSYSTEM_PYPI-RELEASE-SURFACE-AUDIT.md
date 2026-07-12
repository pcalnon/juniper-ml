# Juniper Ecosystem — PyPI Release-Surface & Undeployed-Change Drift Audit

**Project**: Juniper ML Research Platform
**Repository**: cross-repo (`ECOSYSTEM`) — authored in `pcalnon/juniper-ml`
**Author**: auditor agent (systematic findings reviewer)
**License**: MIT License
**Version**: n/a (audit report)
**Last Updated**: 2026-07-11

---

## Scope

Empirical grounding for a follow-on planner that will design a recurring, automated "release train". Answers, with
evidence: (1) the complete inventory of publishable packages; (2) which have changes needing a PyPI deploy *now*;
(3) how each publishes (workflow, trigger, TestPyPI/PyPI jobs, environment gates); (4) where practice drifts from the
release convention (cut a GitHub Release + archive notes under `notes/releases/` — never a bare tag).

**Write target / repo root**: the juniper-ml session worktree at
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sorted-tumbling-dahl`. Sibling repos at
`/home/pcalnon/Development/python/Juniper/<repo>` were treated **strictly read-only** (reads + read-only
`git ls-remote` / `git log` / `gh api`; no fetch, no writes).

## Evidence method (reproducible)

- **pyproject version**: `[project].version` from each `pyproject.toml`, or the `dynamic=["version"]` attr target
  `_version.py` (`grep __version__`).
- **PyPI latest + upload time**: `curl -s https://pypi.org/pypi/<name>/json` → `info.version` + latest release file
  `upload_time_iso_8601`. Network was live; all 18 packages resolved.
- **Freshness**: `git -C <repo> rev-parse origin/main` vs `git -C <repo> ls-remote origin refs/heads/main`.
- **Tags**: `git ls-remote --tags origin`. **Releases**: `gh release list -R pcalnon/<repo>` / `gh release view <tag>`.
- **Commits since tag**: FRESH siblings via local `git log <tag>..origin/main -- <path>`; the STALE juniper-ml worktree
  via `gh api repos/pcalnon/juniper-ml/commits?sha=main&path=<subdir>&since=<tagdate>` and `gh api .../compare/<tag>...main`
  (remote-authoritative).
- **Workflows / environments**: file greps of `.github/workflows/*.yml`; `gh api repos/pcalnon/<repo>/environments`.

**Freshness caveat (a finding in itself)**: the juniper-ml worktree's `origin/main` is **STALE** — local
`77e4b872` vs remote `1e158a4f`. All juniper-ml package facts below use remote-authoritative `gh api`. All eight
sibling git repos were verified **FRESH** (local `origin/main` == remote), so their local `git log` is exact.

---

## 1. Consolidated decision table

Gate column is uniform for every publishing repo (see §3): `pypi` env = **5-min wait_timer + required reviewer
`pcalnon`**; `testpypi` env = **no protection**. Trigger: `rel` = `release: published`; `tag` = `push: tags`.
Verify: `strict` = TestPyPI `--no-deps`, no pypi.org fallback; `fallb` = `--extra-index-url https://pypi.org/simple/`.

| # | Package | Repo | Package path | pyproj | PyPI | Trig | Verify | Classification | Drift flags |
|---|---------|------|--------------|--------|------|------|--------|----------------|-------------|
| 1 | juniper-ml | juniper-ml | `.` (root) | 0.6.0 | 0.6.0 | rel | fallb | **UNRELEASED_CHANGES** | — |
| 2 | juniper-ci-tools | juniper-ml | `juniper-ci-tools/` | 0.6.0 | 0.6.0 | rel | fallb | UP_TO_DATE | — |
| 3 | juniper-config-tools | juniper-ml | `juniper-config-tools/` | 0.1.0 | 0.1.0 | rel | strict | UP_TO_DATE | — |
| 4 | juniper-doc-tools | juniper-ml | `juniper-doc-tools/` | 0.1.1 | 0.1.1 | rel | strict | UP_TO_DATE | **TAG_ONLY**, **NOTES_MISSING** |
| 5 | juniper-model-core | juniper-ml | `juniper-model-core/` | 0.3.0 | 0.3.0 | rel | strict | UP_TO_DATE | — |
| 6 | juniper-observability | juniper-ml | `juniper-observability/` | 0.4.0 | 0.4.0 | rel | fallb | UP_TO_DATE | **TAG_ONLY**, **NOTES_MISSING** |
| 7 | juniper-service-core | juniper-ml | `juniper-service-core/` | 0.4.0 | 0.4.0 | rel | strict | **UNRELEASED_CHANGES** | — |
| 8 | juniper-cascor | juniper-cascor | `.` (minus subpkgs) | 0.5.0 | 0.5.0 | rel | fallb | **UNRELEASED_CHANGES** | — |
| 9 | juniper-cascor-model | juniper-cascor | `juniper-cascor-model/` | 0.1.0 | 0.1.0 | tag | strict | UP_TO_DATE | — |
| 10 | juniper-cascor-protocol | juniper-cascor | `juniper-cascor-protocol/` | 0.1.0 | 0.1.0 | tag | fallb | UP_TO_DATE | **TAG_ONLY**, **NOTES_MISSING** |
| 11 | juniper-canopy | juniper-canopy | `.` | 0.5.0 | 0.5.0 | rel | strict | **UNRELEASED_CHANGES** | **NOTES_MISSING** |
| 12 | juniper-cascor-client | juniper-cascor-client | `.` | 0.6.0 | 0.6.0 | rel | fallb | UP_TO_DATE | — |
| 13 | juniper-cascor-worker | juniper-cascor-worker | `.` | 0.4.0 | 0.4.0 | rel | fallb | **UNRELEASED_CHANGES** | **NOTES_MISSING** |
| 14 | juniper-data | juniper-data | `.` | 0.9.0 | 0.9.0 | rel | fallb | UP_TO_DATE | — |
| 15 | juniper-data-client | juniper-data-client | `.` | 0.4.2 | 0.4.2 | rel | fallb | UP_TO_DATE | — |
| 16 | juniper-recurrence | juniper-recurrence | `juniper-recurrence/` | 0.2.0 | 0.2.0 | tag | strict | **UNRELEASED_CHANGES** | — |
| 17 | juniper-recurrence-client | juniper-recurrence | `juniper-recurrence-client/` | 0.2.0 | 0.2.0 | tag | strict | UP_TO_DATE | — |
| 18 | juniper-recurrence-model | juniper-recurrence | `juniper-recurrence-model/` | 0.1.5 | 0.1.5 | tag | strict | **UNRELEASED_CHANGES** | — |
| — | juniper-deploy | juniper-deploy | `.` | *none* | not on PyPI | — | — | **NOT_A_PACKAGE** | — |
| — | juniper-slacker | juniper-slacker | `.` | *none* | not on PyPI | — | — | **NOT_A_PACKAGE** | — |

**Headline**: pyproject version == PyPI latest for **all 18** packages → **zero BUMPED_NOT_RELEASED**, **zero
NEVER_RELEASED**. Version-compare alone would report the whole fleet "up to date"; the real drift is **7 packages with
release-worthy commits since their last release tag whose version has not been bumped** (UNRELEASED_CHANGES), plus
orthogonal release-hygiene drift (3 TAG_ONLY, 5 NOTES_MISSING).

---

## 2. Inventory verification (vs pre-scouted list)

18 publishable packages confirmed across 8 repos + 2 non-packages. Two-package/three-package repos verified:
`juniper-cascor` hosts `juniper-cascor-model/` + `juniper-cascor-protocol/`; `juniper-recurrence` hosts
`juniper-recurrence/` + `juniper-recurrence-client/` + `juniper-recurrence-model/`; `juniper-ml` hosts 6 sub-packages.
Nothing missed vs the pre-scout. Dynamic-version packages (`dynamic=["version"]` → `_version.py`): model-core
(`juniper-model-core/juniper_model_core/_version.py:3` = 0.3.0), recurrence app (`.../juniper_recurrence/_version.py:9`
= 0.2.0), recurrence-client (`.../_version.py:7` = 0.2.0), recurrence-model (`.../_version.py:7` = 0.1.5). All others
are static `[project].version`.

- **juniper-deploy = NOT_A_PACKAGE**: `juniper-deploy/pyproject.toml` contains only `[tool.pytest.ini_options]` — **no
  `[project]` table, no build-system, no name/version**; no `publish*.yml`; `curl .../juniper-deploy/json` → not on
  PyPI. It is the Docker/Helm stack orchestrator. It *does* cut GitHub Releases (`v0.2.1` "Helm Chart Convergence",
  2026-04-10) for the stack, but those are not PyPI deploys.
- **juniper-slacker = NOT_A_PACKAGE**: on-disk contents are `juniper_bridge.py`, `parser.py`, `handlers/`,
  `requirements.txt`, `juniper-slack-bridge-plan.md` — **no `pyproject.toml`/`setup.py`/`setup.cfg`** anywhere (depth-3
  find), no publish workflow, no GitHub Releases, not on PyPI. Out of scope (a plain script project).

---

## 3. Publish mechanics (trigger / jobs / environment gates)

### 3.1 Two trigger models (a key planner input)

- **`release: published` (13 workflows)** — juniper-ml meta `publish.yml` + its 6 sub-package workflows; plus
  `juniper-cascor/publish.yml`, `juniper-canopy/publish.yml`, `juniper-cascor-client/publish.yml`,
  `juniper-cascor-worker/publish.yml`, `juniper-data/publish.yml`, `juniper-data-client/publish.yml`. These **enforce
  the Release-cut convention structurally**: no GitHub Release ⇒ no publish. Each is guarded so one Release event only
  fires the matching workflow — meta `publish.yml:45` `if: … startsWith(github.event.release.tag_name, 'v')`; each ml
  sub-package `if: … startsWith(…, 'juniper-<pkg>-v')` (e.g. `publish-service-core.yml:65`); `juniper-cascor/publish.yml:15`
  guards `'v'`. All 7 ml workflows + service-core carry the `# never a bare git push <tag>` header and a
  `#555` note explaining they dropped `push: tags` to avoid a double-fire race.
- **`push: tags` (5 workflows)** — `juniper-cascor/publish-cascor-model.yml:35` (`- "juniper-cascor-model-v*"`),
  `juniper-cascor/publish-protocol.yml:28` (`- "juniper-cascor-protocol-v*"`),
  `juniper-recurrence/publish-recurrence-app.yml:41` (`- "juniper-recurrence-v*"`),
  `.../publish-recurrence-client.yml:39` (`- "juniper-recurrence-client-v*"`),
  `.../publish-recurrence-model.yml:40` (`- "juniper-recurrence-model-v*"`). These publish on a **bare tag push** — they
  **structurally permit the TAG_ONLY convention violation** (a `git push <tag>` with no Release still publishes).
  In practice the recurrence trio all had Releases cut (the Release also creates the tag), but the mechanism does not
  require it.

### 3.2 Jobs (uniform two-stage shape)

Every publish workflow: build+twine-check → **TestPyPI publish (`environment: testpypi`) + install-verify** →
**PyPI publish (`environment: pypi`)**. OIDC trusted publishing (no API tokens). TestPyPI `repository-url:
https://test.pypi.org/legacy/` in all 18.

### 3.3 Environment protection gates (`gh api repos/pcalnon/<repo>/environments`) — MUST remain untouched

**Uniform across all 8 publishing repos** (juniper-ml, juniper-cascor, juniper-recurrence, juniper-canopy,
juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client):

- **`pypi`**: two protection rules — `required_reviewers` = `[pcalnon]` **and** `wait_timer` = `5` (minutes).
- **`testpypi`**: **no** protection rules (auto-publishes for pre-flight verification).

(juniper-ml and juniper-cascor also carry an unrelated `copilot` environment with no rules.) This dual PyPI gate
(human approval by Paul + 5-min timer) is the load-bearing guardrail any automation must preserve; TestPyPI's
lack-of-gate is intentional (it is the smoke-test stage before the gated promotion).

### 3.4 TestPyPI verify — inconsistent no-fallback policy (a drift)

The ratified policy (juniper-ml#384; documented in `publish-model-core.yml:20-25` and `publish-service-core.yml:150-157`)
is: verify the **target** package from **TestPyPI only** (`--no-deps`, single `--index-url`, **no** production-PyPI
`--extra-index-url`), so a squatted same-name package on public PyPI cannot shadow the verification.

- **strict (`--no-deps`, no fallback) — 9 workflows**: doc-tools (`publish-doc-tools.yml:136`), config-tools (`:138`),
  model-core (`:141`), service-core (`:156`), cascor-model (`publish-cascor-model.yml:126`), canopy
  (`publish.yml:96`), recurrence-app (`:145`), recurrence-client (`:136`), recurrence-model (`:144`).
- **fallback (`--extra-index-url https://pypi.org/simple/`) — 9 workflows**: meta juniper-ml (`publish.yml:103/113/120`
  — **intentional**: the meta must resolve its real sub-package deps to verify `[clients]`/`[tools]` extras),
  ci-tools (`publish-ci-tools.yml:137`), observability (`publish-observability.yml:142`), cascor-protocol
  (`publish-protocol.yml:127`), cascor (`publish.yml:45`), cascor-client (`:41`), cascor-worker (`:41`), data (`:41`),
  data-client (`:43`). Excluding the meta's documented exception, **8 workflows still use the fallback pattern the
  policy warns against** (the older single-package/cascor-family/ci-tools/observability workflows predate the strict
  refactor).

---

## 4. Per-package evidence

### 4.A UNRELEASED_CHANGES (7) — release-worthy commits since last release tag, version not bumped

**1 · juniper-ml (meta) 0.6.0** — PyPI 0.6.0 uploaded **2026-05-23** (`.../juniper-ml/json` info.version=0.6.0). Release
`v0.6.0` exists (2026-05-23). Root `pyproject.toml` changed **many times since** the tag (`gh api commits?path=pyproject.toml`):
`34f44864` (service-core floor→0.4.0), `4f01797b` (recurrence model floor→0.1.5), `2950ba90`/`1029ffc4` (**new
`[recurrence]` extra**), `73100874`/`38f40cea` (model-core into `[tools]`), `668e7123` (cascor-client→0.5.0). The
published 0.6.0 **predates the `[recurrence]` extra entirely** — `pip install juniper-ml[recurrence]` does not resolve
from PyPI today. CHANGELOG `[Unreleased]` carries the full extras-rewrite backlog (R5 recurrence extra, WS-2/WS-3
wiring, DP-3 pin bumps). Release-worthy = root `pyproject.toml` `[project.optional-dependencies]`/floors.

**7 · juniper-service-core 0.4.0** — PyPI 0.4.0 uploaded **2026-07-01**; Release `juniper-service-core-v0.4.0`
(2026-07-01T23:06). Commit **`87346d6e` (2026-07-03)** "feat(service-core): add enforce_auth_posture() boot check
(SEC-F01)" lands **after** the tag and adds shipping source: `juniper_service_core/auth_posture.py` (new module) +
`__init__.py` (+ test + CHANGELOG). CHANGELOG `[Unreleased] ### Added` documents `enforce_auth_posture(...)`. Filter:
new `.py` under the import package = release-worthy.

**8 · juniper-cascor 0.5.0** — PyPI 0.5.0 uploaded **2026-05-23**; Release `v0.5.0`. `git log v0.5.0..origin/main`
(excluding the two subpkg dirs) = **101 commits, 128 files under `src/`** + `pyproject.toml` + `requirements.lock`.
CHANGELOG `[Unreleased]` is large and security-bearing: SEC-F22 startup bind-guard (`enforce_bind_attestation_guard`),
SEC-F19 WS connection caps, build provenance on `/v1/health`, `.dockerignore`. Major.

**11 · juniper-canopy 0.5.0** — PyPI 0.5.0 uploaded **2026-05-23**; Release `v0.5.0`. `git log v0.5.0..origin/main` =
**126 commits, 126 files under `src/`** + `pyproject.toml`. CHANGELOG `[Unreleased]` = **41 bullet entries** across
Changed/Tests/Added/Fixed/Security. Corroborated by known June–July canopy work (training-start fixes, recurrence
integration, control buttons, CSRF). Major. Also NOTES_MISSING (see §5).

**13 · juniper-cascor-worker 0.4.0** — PyPI 0.4.0 uploaded **2026-05-23**; Release `v0.4.0`. `git diff --stat
v0.4.0..origin/main -- juniper_cascor_worker/ pyproject.toml` = real source changes: `config.py` (+104), `cli.py`
(+27), `task_executor.py`, `http_health.py`, `worker.py`, `__init__.py`, `pyproject.toml` (+12). CHANGELOG
`[Unreleased] ### Added` = build provenance on `/v1/health`. Also NOTES_MISSING.

**16 · juniper-recurrence 0.2.0** — PyPI 0.2.0 uploaded **2026-06-24**; Release `juniper-recurrence-v0.2.0`. `git log
juniper-recurrence-v0.2.0..origin/main -- juniper-recurrence/` = **12 commits** touching shipping source: `app.py`,
`main.py`, `settings.py`, `logging_config.py`, `metrics.py`, `provenance.py`, `routers/{crossval,predict,training}.py`
+ `pyproject.toml`. CHANGELOG `[Unreleased] ### Added` = H1 startup logging (via service-core 0.3.0 `create_app(lifespan=)`).

**18 · juniper-recurrence-model 0.1.5** — PyPI 0.1.5 uploaded **2026-06-24**; Release `juniper-recurrence-model-v0.1.5`.
`git diff juniper-recurrence-model-v0.1.5..origin/main -- .../juniper_recurrence_model/` = **functional** source
changes: `data.py` adds `if not np.all(np.isfinite(X)): raise ValueError(...)` (and the same for `dt` gaps) — new
NaN/Inf input validation — plus `readouts.py` (+2), `units/lmu_varstep.py` (+6). **Caveat**: the visible top of the
CHANGELOG `[Unreleased]` documents only the C-5 coverage gate ("No coverage lift required"); the validation additions
may be under-documented — flag for the release author.

### 4.B UP_TO_DATE (11) — no release-worthy change since the last release

**2 · juniper-ci-tools 0.6.0** (PyPI 2026-07-01; Release `juniper-ci-tools-v0.6.0`): post-tag commits are docs/notes/tests
only. `16250cc6` "test(ci-tools)…" touches only `tests/test_lint_agents_md_header.py` + `tests/test_lint_agents_md_version.py`.
`[Unreleased]` empty.

**3 · juniper-config-tools 0.1.0** (PyPI 2026-05-22; Release `juniper-config-tools-v0.1.0`): post-tag = notes +
`0ea55270` ruff governance (touched only `juniper-config-tools/pyproject.toml` + `tests/…`) + `6ddb436b` pytest config.
No import-source change. `[Unreleased]` empty.

**4 · juniper-doc-tools 0.1.1** (PyPI 2026-05-19; **no Release**): after the `0.1.1` fix (`566e2613`), post-tag commits
are docs/readme, `ac93d6e3` test-coverage, `0ea55270` ruff CI. No shipping-source change. `[Unreleased]` documents only
CI-gate + test-suite expansion. Content UP_TO_DATE but TAG_ONLY + NOTES_MISSING (§5).

**5 · juniper-model-core 0.3.0** (PyPI 2026-06-19; Release `juniper-model-core-v0.3.0`): the only post-0.3.0 source
touch is `0ea55270` (ruff) editing `juniper_model_core/validation.py` — the patch is `zip(seqs, seqs[1:])` →
`zip(seqs, seqs[1:], strict=False)`, a **behavior-preserving B905 lint fix**. `[Unreleased]` empty. UP_TO_DATE.

**6 · juniper-observability 0.4.0** (PyPI 2026-06-14; **no Release**): after `330d0643` (the 0.4.0 build-provenance
feature), post-tag = `b269efa7` test, docs/readme, `0ea55270` ruff CI. No shipping-source change. `[Unreleased]` empty.
Content UP_TO_DATE but TAG_ONLY + NOTES_MISSING (§5).

**9 · juniper-cascor-model 0.1.0** (PyPI 2026-06-14; Release `juniper-cascor-model-v0.1.0`): `git log
juniper-cascor-model-v0.1.0..origin/main` = 2 commits. The single "source" change,
`cascor_constants/constants_api/constants_api_defaults.py`, is a **1-line doc-comment link edit** from the 2026-07-04
notes-rename (`CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` → `JUNIPER_2026-04-08_…-INTERFACE-ROADMAP.md`); the rest is
tests + CHANGELOG. `[Unreleased]` = CI gate + test lift. No functional change. UP_TO_DATE.

**10 · juniper-cascor-protocol 0.1.0** (PyPI 2026-04-30; **no Release**): `git rev-list --count
juniper-cascor-protocol-v0.1.0..origin/main -- juniper-cascor-protocol/` = **0 commits**. UP_TO_DATE, but TAG_ONLY +
NOTES_MISSING (§5).

**12 · juniper-cascor-client 0.6.0** (PyPI **2026-07-11** — released today; Release `v0.6.0`): tag `v0.6.0` == local
`origin/main` HEAD `292c520c`; `git rev-list --count v0.6.0..origin/main` = **0 commits**. `[Unreleased]` empty. UP_TO_DATE.

**14 · juniper-data 0.9.0** (PyPI 2026-06-22; Release `v0.9.0`): `git diff --stat v0.9.0..origin/main -- juniper_data/`
= 15 files, but **12 are `juniper_data/tests/unit/…`** (coverage work, +500 lines) and the 3 non-test files
(`generators/_sequence.py`, `_synthetic.py`, `equities_seq/generator.py`) are each a **1-line notes-rename comment
edit** (2 changed lines total). `[Unreleased]` = Changed(CI gate) + Tests only. No functional change. UP_TO_DATE.

**15 · juniper-data-client 0.4.2** (PyPI 2026-06-18; Release `v0.4.2`): 21 commits since tag, but source diff =
`juniper_data_client/contract.py` **1 line** (from `ec59ac1` "chore(docs): update juniper-ml notes/ links") +
`pyproject.toml` **1 line** (from `ff528ba` "chore(pytest): add --strict-config"). No functional/ runtime-dep change.
UP_TO_DATE.

**17 · juniper-recurrence-client 0.2.0** (PyPI 2026-06-24; Release `juniper-recurrence-client-v0.2.0`): 3 commits, no
import-source change; only `AGENTS/README/CHANGELOG`, `tests/…`, and `pyproject.toml` (adds `juniper-observability` to
the **`test` extra** + `filterwarnings=["error"]`). CHANGELOG `[Unreleased]` self-declares **"Tests / CI /
packaging-extra only — no runtime change, no version bump."** UP_TO_DATE.

### 4.C NOT_A_PACKAGE (2)

**juniper-deploy** and **juniper-slacker** — see §2.

---

## 5. Convention-drift findings

### F-1 (major) · TAG_ONLY_RELEASE — published with no surviving GitHub Release (3 packages)

`gh release view <tag>` returns **"release not found"** for `juniper-doc-tools-v0.1.1`, `juniper-observability-v0.4.0`
(also `-v0.3.1`/`-v0.3.0`/`-v0.2.0`), and `juniper-cascor-protocol-v0.1.0` — yet the tags exist (`git ls-remote --tags`)
and the versions are on PyPI. These violate the mandatory "cut a GitHub Release, never a bare tag" convention
(`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md:474-479` explicitly names this drift). Positive
control: `gh release view juniper-ci-tools-v0.6.0` returns JSON. **Mechanism could-not-fully-verify**: plausibly the
early `push: tags` trigger era or a `workflow_dispatch`, or a later-deleted Release — the current doc-tools/observability
workflows are now `release: published`, so this is legacy residue, but cascor-protocol's workflow is *still* tag-push
(§3.1) and can reproduce it.

### F-2 (major) · NOTES_ARCHIVE_MISSING for the latest released version (5 packages)

No `RELEASE_NOTES_*` archive for the current version of: **juniper-doc-tools 0.1.1** (no doc-tools notes anywhere),
**juniper-observability 0.4.0** (`notes/releases/` stops at `…_v0.1.1a`), **juniper-cascor-protocol 0.1.0** (none;
`juniper-cascor/notes/releases/` does not exist), **juniper-canopy 0.5.0** (`juniper-canopy/notes/releases/` holds only
old `v0.14–v0.25-alpha` notes from the pre-renumber line), **juniper-cascor-worker 0.4.0**
(`juniper-cascor-worker/notes/releases/` stops at `v0.3.0`). Contrast: data 0.9.0, data-client 0.4.2, cascor-client
0.6.0, and the recurrence trio all have matching archives.

### F-3 (major) · Central-archive convention (§11.3) only partially followed

`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md:497-509` mandates a **central** archive in
`juniper-ml/notes/releases/` for **every** package, including those cut from other repos, using
`RELEASE_NOTES_<pkg>_v<ver>.md`. Reality is split: the meta + 6 ml sub-packages archive centrally (with `_v` separator),
and a few cross-repo notes were centralized (`RELEASE_NOTES_juniper-cascor_v0.5.0.md`,
`RELEASE_NOTES_juniper-cascor-model_v0.1.0.md`, `RELEASE_NOTES_juniper-recurrence-model_v0.1.0…0.1.2.md`) — but the app
repos (**canopy, data, data-client, cascor-client, cascor-worker, all 3 recurrence packages, deploy**) archive in their
**own** `notes/releases/`. The central archive is therefore **stale for recurrence** (juniper-ml has recurrence-model
only through `_v0.1.2`; the repo itself has through `-v0.1.5` + `-v0.2.0`), and recurrence uses a `-v` separator
(`RELEASE_NOTES_juniper-recurrence-model-v0.1.5.md`) vs the doc's `_v`.

### F-4 (minor) · Trigger-model inconsistency enables the TAG_ONLY class

5 workflows are `push: tags` (§3.1); juniper-ml already migrated its sub-packages off that to `release: published` to
enforce the Release-cut convention and dodge the `#555` double-fire race. cascor-model/protocol and the 3 recurrence
workflows have not migrated — the one structural loophole for F-1.

### F-5 (minor) · TestPyPI no-fallback policy applied to only ~half the leaf workflows

8 leaf workflows still use the production-PyPI `--extra-index-url` fallback the ml#384 policy warns against (§3.4).
Standardizing on `--no-deps` (as canopy/recurrence/4 ml sub-packages already do) is a mechanical, high-value
consolidation for the release-train.

### F-6 (minor) · juniper-ml worktree local `origin/main` is stale

Local `77e4b872` vs remote `1e158a4f` (all 8 siblings FRESH). Any automation computing "commits since tag" from a local
checkout will **under-count** for juniper-ml. Automation must fetch or use remote-authoritative `gh api` (as this audit
did). This is not a package defect — it is a detector-correctness constraint.

---

## 6. Convention sources a workflow plan must build on (existence verified)

- **`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`** (616 lines). **§11 "Cutting a Release
  (End-to-End)"** (`:470`) is the ceremony of record: **11.1** bump `pyproject.toml` version (`:481`); **11.2** commit +
  push (`:489`); **11.3** author notes from the template and **archive centrally in `juniper-ml/notes/releases/`**
  (`:497`, meta `RELEASE_NOTES_v<ver>.md`, others `RELEASE_NOTES_<pkg>_v<ver>.md`); **11.4** **cut the GitHub Release —
  "this is the deploy — never a bare tag"** (`:511`; CLI `gh release create <tag> --notes-file … [--latest|--latest=false]`);
  **11.5** monitor `gh run` (`:538`); **11.6** verify `pip install` (`:547`). The `:474-479` banner names the exact
  drift this audit found (F-1). §10.4 (`:456`) documents the environment setup behind §3.3's gates.
- **`templates/TEMPLATE_RELEASE_NOTES.md`** (267 lines) — required structure for standard release notes; names the
  `RELEASE_NOTES_v[VERSION].md` convention and the `notes/releases/` location.
- **`templates/TEMPLATE_SECURITY_RELEASE_NOTES.md`** (139 lines) — the security-patch variant (used when a release is a
  security fix; several UNRELEASED_CHANGES items — cascor SEC-F19/F22, service-core SEC-F01 — are security-bearing).
- **`releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`** and
  **`releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md`** — the two worked
  end-to-end release precedents (single-package and coupled meta+sub-package).
- **`.github/workflows/docs-full-check.yml`** (328 lines) — the **ecosystem-wide automation precedent**: weekly
  `schedule: cron "0 6 * * 1"` + `workflow_dispatch` (`:63-65`), a hard-coded `REPOS`/`CONSUMERS` list cloned via
  `git clone --depth 1 https://github.com/${owner}/$repo.git` (`:73-105`) with per-repo failure tolerance. **Precedent
  gap for a release-train**: its clone lists (`:76-81`, `:172-177`, `:266-270`) enumerate data/cascor/canopy/data-client/
  cascor-client/cascor-worker but **omit `juniper-recurrence`** and do **not** model the multi-package repos
  (cascor/recurrence sub-dirs) — a release-train reusing this scaffold must add recurrence and per-subdir logic.
- **TestPyPI no-fallback install-verify policy** — encoded inline in the strict workflows (`publish-model-core.yml:20-25`,
  `publish-service-core.yml:150-157`): resolve the target from TestPyPI only, `--no-deps`, single `--index-url`, no
  pypi.org `--extra-index-url` (anti-target-squatting). Applied unevenly (§3.4 / F-5).
- Naming convention for this report: `JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`.

---

## 7. Inputs the workflow plan needs (reusable detection signals + gaps)

**Detection signals (the automated release-train's per-package "needs deploy?" pipeline):**

1. **Version compare is necessary but insufficient.** All 18 have `pyproject == PyPI`, so a pure version diff finds
   nothing. The train must compare **commits since the last release tag**, not versions.
2. **Version source per package**: static `[project].version` for 14; `dynamic=["version"]` → `_version.py __version__`
   for model-core + the 3 recurrence packages. The detector must read `_version.py` for those.
3. **Last-release-tag patterns** (for the `<tag>..main` diff base): meta `v*`; ml sub-packages
   `juniper-<pkg>-v*`; cascor app `v*` + `juniper-cascor-{model,protocol}-v*`; recurrence
   `juniper-recurrence[-client|-model]-v*`; single-package siblings `v*`. Prefer the tag that matches the current PyPI
   version.
4. **Remote-authoritative diffing.** Local checkouts can be stale (F-6 — the ml worktree was). Use `gh api
   compare/<tag>...main` (note the **300-file page cap**; for large diffs page or use `commits?path=&since=`) or a fresh
   fetch. Path-scope subdir packages (e.g. `-- juniper-ci-tools/`); for cascor the app is "repo minus the two subpkg
   dirs".
5. **Release-worthy vs non-shipping filter** (validated per package above):
   - **SHIP**: files under the import package dir (`juniper_<pkg>/`, `src/`, `cascor_constants/`, …); `pyproject.toml`
     **`[project].dependencies` / runtime floors / version**.
   - **NON-SHIP**: `notes/`, `docs/`, `README/CHANGELOG/AGENTS.md`, `.github/` (CI), **`tests/` including in-package
     `juniper_data/tests/`**, `pyproject.toml` **`test`-extra deps** and **pytest config** (`filterwarnings`,
     `--strict-config`), **ruff-only lint reformats** (e.g. `strict=False`), and — a live false-positive trap — the
     **2026-07-04 notes-rename 1-line doc-comment/link edits** that touched shipping `.py` files in **data, data-client,
     cascor-model** (and likely more). A naive "any `.py` under the package changed" rule would misclassify 4 UP_TO_DATE
     packages as needing a deploy; require a substantive (non-comment) hunk.
6. **CHANGELOG `[Unreleased]` as a corroborating signal**: feature/fix/security bullets ⇒ release-worthy (juniper-ml,
   service-core, cascor, canopy, cascor-worker, recurrence). CI/test/docs-only bullets ⇒ not (doc-tools, cascor-model,
   data). recurrence-client's Unreleased even self-declares "no version bump" — machine-readable intent. Note the
   inverse risk: recurrence-model's real validation change is under-documented there (don't rely on Unreleased alone).
7. **Release-hygiene checks** (orthogonal to "needs deploy"): `gh release view <tag>` == "release not found" ⇒
   TAG_ONLY; `notes/releases/RELEASE_NOTES_*<ver>*` present in **both** the central ml archive **and** the owning repo ⇒
   NOTES_MISSING check (per F-3 the train should converge on the §11.3 central archive).
8. **Invariants to preserve**: never touch the `pypi` env gate (5-min wait + `pcalnon` review) or the OIDC trusted-publish
   config; `testpypi` intentionally ungated; keep the `release: published` guard `if:` conditions.

**Gaps / normalization work the plan should absorb:**

- Migrate the 5 `push: tags` workflows to `release: published` (F-4) to make the Release-cut convention enforceable
  fleet-wide.
- Standardize TestPyPI verify on strict `--no-deps` for the 8 fallback leaf workflows (F-5; keep the meta's documented
  exception).
- Extend/replace the `docs-full-check.yml` clone scaffold to include `juniper-recurrence` and model the 3 multi-package
  repos (§6).
- Reconcile the central vs per-repo `notes/releases/` split and the `_v` vs `-v` separator (F-3).
- Backfill the 3 TAG_ONLY releases and 5 missing note archives, or explicitly accept them as legacy.

---

## 8. Summary

- **Publishable packages**: 18 (7 in juniper-ml, 3 in juniper-cascor, 3 in juniper-recurrence, 5 standalone siblings).
  **Non-packages**: 2 (juniper-deploy, juniper-slacker).
- **Classification**: **UNRELEASED_CHANGES = 7** (juniper-ml meta, service-core, cascor, canopy, cascor-worker,
  recurrence, recurrence-model); **UP_TO_DATE = 11**; **BUMPED_NOT_RELEASED = 0**; **NEVER_RELEASED = 0**.
- **Drift flags**: **TAG_ONLY_RELEASE = 3** (doc-tools, observability, cascor-protocol); **NOTES_ARCHIVE_MISSING = 5**
  (doc-tools, observability, cascor-protocol, canopy, cascor-worker); **CHANGELOG_STALE = 0** (every top version-heading
  matches PyPI; minor day-off date discrepancies only, e.g. cascor-model `2026-06-04` vs release `2026-06-14`).
- **Findings by severity**: major = F-1, F-2, F-3; minor = F-4, F-5, F-6.
- **Gates (must-not-touch), verified uniform on all 8 publishing repos**: `pypi` = wait_timer 5 + reviewer `pcalnon`;
  `testpypi` = none.

### Could not fully verify (stated, not asserted)

- **Exact mechanism of each TAG_ONLY publish** (early tag-push trigger vs `workflow_dispatch` vs later-deleted Release):
  the empirical facts (tag present, on PyPI, no Release now) are certain; the how is not, and would require the publish
  workflows' git history + Actions run logs.
- **recurrence-model `[Unreleased]` completeness**: the NaN/Inf validation source change is certain (diff); whether the
  CHANGELOG fully documents it below the visible C-5 entry was not exhaustively read.
- **Whether every 1-line "source" hunk in data / data-client is purely a notes-link edit**: verified for the sampled
  files (contract.py, the two data generators, cascor-model constants) — all notes-rename comment edits; a full
  hunk-by-hunk pass across the fleet was not done (the filter in §7.5 mitigates the residual risk).
