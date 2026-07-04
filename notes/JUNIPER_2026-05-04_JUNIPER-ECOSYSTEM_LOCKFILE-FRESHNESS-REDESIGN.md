# Lockfile Freshness Redesign — 2026-05-04

**Status**: in progress
**Author**: Paul Calnon (executed by Claude Code)
**Scope**: All 8 active Juniper ecosystem repositories
**Related**:

- `notes/DEPENDENCY_UPDATE_WORKFLOW.md`
- juniper-data commit `1fca801` (2026-04-25) — first constraint-satisfaction adoption
- juniper-cascor PR #210 main-branch breakage (2026-05-04) — trigger for this redesign

---

## 1. Problem statement

The `Lockfile Freshness` CI gate has produced a recurring stream of false-positive failures across the Juniper ecosystem: the gate flags `requirements.lock` as "stale" even when `pyproject.toml` is unchanged and the committed pins still satisfy every direct-dependency specifier.
Each occurrence requires a manual lockfile regeneration commit just to turn CI green again. Recent examples:

| Date           | Repo                  | Failure                             | Resolution commit           |
|----------------|-----------------------|-------------------------------------|-----------------------------|
| 2026-04-25     | juniper-data          | header drift + transitive bumps     | `1fca801` (constraint mode) |
| 2026-04-29     | juniper-canopy        | bundled lockfile + tests            | `7089bdf`                   |
| 2026-05-01     | juniper-data          | follow-up repair                    | `223b062`                   |
| 2026-05-03     | juniper-canopy        | juniper-data-client 0.4.0→0.4.1     | `b34c34b` (P-14)            |
| 2026-05-03     | juniper-cascor-worker | lockfile stale on arrival           | `2dce8f3` (P-18)            |
| **2026-05-04** | **juniper-cascor**    | **`sentry-sdk==2.58.0` → `2.59.0`** | (this redesign)             |

The pattern: a transitive dependency releases a new patch on PyPI, the byte-for-byte CI gate sees the diff, main goes red, an engineer regenerates the lockfile, lather, rinse, repeat.
The juniper-data team solved this on 2026-04-25 by switching to a constraint-satisfaction model — but the fix was never propagated to juniper-cascor or juniper-cascor-worker, which still run the original byte-for-byte check.

This document is the ecosystem-wide fix.

---

## 2. Audit of current state (2026-05-04)

| Repo                  | Has `requirements.lock` | Has freshness gate | Verification model | Has `lockfile-update.yml`                      | uv pinned |
|-----------------------|-------------------------|--------------------|--------------------|------------------------------------------------|-----------|
| juniper-cascor        | ✓                       | ✓ (in `ci.yml`)    | **byte-for-byte**  | ✓ (Dependabot push)                            | ✗         |
| juniper-cascor-worker | ✓                       | ✓ (in `ci.yml`)    | **byte-for-byte**  | ✓ (Dependabot push)                            | ✗         |
| juniper-data          | ✓                       | ✓ (in `ci.yml`)    | **constraint** ✓   | ✓ (Dependabot push)                            | ✗         |
| juniper-canopy        | ✓                       | ✓ (in `ci.yml`)    | **constraint** ✓   | ✓ (Dependabot push)                            | ✗         |
| juniper-data-client   | — (client lib)          | ✗                  | n/a                | ✓ (template, gated `[ -f requirements.lock ]`) | ✗         |
| juniper-cascor-client | — (client lib)          | ✗                  | n/a                | ✓ (template)                                   | ✗         |
| juniper-ml            | — (meta-pkg)            | ✗                  | n/a                | ✓ (cron + PR)                                  | ✗         |
| juniper-deploy        | — (infra)               | ✗                  | n/a                | ✗                                              | n/a       |

**Two verification models are in use simultaneously:**

- **Byte-for-byte (cascor, cascor-worker)**: re-run `uv pip compile` and `diff -u` the full output against the committed file (minus the 2-line header).
- **Constraint-satisfaction (data, canopy)**: re-run `uv pip compile --constraint requirements.lock`, then `diff` the sorted pin lines only.

The byte-for-byte model is the source of the recurring failures.

---

## 3. Root-cause analysis

### 3.1 Primary cause — Byte-for-byte fails on transient PyPI churn

`uv pip compile` without `--constraint` always resolves to the *newest compatible* versions on PyPI at compile time.
If a transitive dependency (e.g. `sentry-sdk`, `cuda-pathfinder`, `filelock`) releases a patch between the lockfile commit and the next CI run, the byte-for-byte diff fails — even though no engineer changed anything in the repo.
The 2026-05-04 cascor failure is the canonical case:

```diff
-sentry-sdk==2.58.0
+sentry-sdk==2.59.0
```

`pyproject.toml` says `"sentry-sdk>=2.0.0"`. Both `2.58.0` and `2.59.0` satisfy that spec.
The committed lockfile is *not actually broken* — it is being judged by the wrong criterion.

### 3.2 Secondary cause — uv self-pin trap

When regenerating `requirements.lock` via `uv pip compile pyproject.toml -o requirements.lock`, **uv reads the existing target file and treats its pins as soft constraints**, even with `--refresh`.
Local regen sticks to the same versions; CI's `/tmp/...check` regen produces fresh versions; the diff fails.
This was hit on juniper-cascor-worker PR #45 (2026-05-03) and forced a `rm requirements.lock` workaround.

The constraint-satisfaction model makes this trap irrelevant — it relies on the constraint behavior intentionally rather than fighting it.

### 3.3 Tertiary cause — uv version drift

All 7 lockfile-touching workflows use `pip install uv` (unpinned).
Between runs uv can publish a release that subtly changes resolver output (header format, sort order, sentinel comments).
With unpinned uv, the freshness check can flip from green to red without any repo change — purely from a remote uv release.
uv 0.9 → 0.10 → 0.11 has shipped resolution changes within the past quarter.

### 3.4 Tertiary cause — Python version drift

`lockfile-update.yml` uses Python 3.12 in juniper-cascor and juniper-cascor-worker; `ci.yml` lockfile-check uses Python 3.14 (`PYTHON_TEST_VERSION` env).
Different Python versions can resolve different markers (`python_version >= "3.13"`-gated wheels) and produce different sort orders.
juniper-data and juniper-canopy use 3.14 in both places — they don't suffer this.

### 3.5 Tertiary cause — Dependabot does not regenerate the lockfile

Dependabot opens PRs against `pyproject.toml` (and `conf/requirements*.txt` files).
The `lockfile-update.yml` workflow listens for `dependabot/pip/**` pushes and regenerates, but that workflow does not block the PR's own merge.
If the PR merges before regeneration completes (or if regeneration silently fails), main goes red. PR #210 in juniper-cascor on 2026-05-04 is exactly this scenario.

---

## 4. Design — comprehensive fix

### 4.1 Adopt constraint-satisfaction model in cascor and cascor-worker

Replace the byte-for-byte gate with the proven juniper-data pattern:

```yaml
- name: Check lockfile freshness
  run: |
    # Resolve pyproject.toml using the committed lockfile as constraints.
    # Passes when the pinned versions still satisfy pyproject.toml.
    # Does NOT fail just because newer versions exist on PyPI — that is
    # the whole point of pinning. Fails only when pyproject.toml has
    # drifted from what the lockfile can support (new dep added, min
    # bumped past pin, entry removed).
    uv pip compile pyproject.toml \
      <repo-specific --extra flags> \
      <repo-specific --no-emit-package / --index-strategy flags> \
      --constraint requirements.lock \
      -o /tmp/requirements.lock.check

    # Compare only the resolved pin lines (pkg==version), ignoring
    # comments and uv's "# -c requirements.lock" annotations and the
    # autogenerated header that embeds the -o path.
    grep '^[^[:space:]#]' requirements.lock | sort > /tmp/lock_pins
    grep '^[^[:space:]#]' /tmp/requirements.lock.check | sort > /tmp/check_pins

    if ! diff -u /tmp/lock_pins /tmp/check_pins; then
      echo "::error::requirements.lock no longer satisfies pyproject.toml — refresh with: uv pip compile pyproject.toml <flags> --upgrade -o requirements.lock"
      exit 1
    fi
    echo "::notice::requirements.lock satisfies pyproject.toml ✓"
```

This removes the failure mode in §3.1 (transient PyPI churn) and makes §3.2 (uv self-pin) a *feature* rather than a bug — `--constraint` deliberately reads the existing pins.

### 4.2 Pin uv version

In all 7 workflows that invoke `uv pip compile`, replace `pip install uv` with a fixed version: `pip install uv==0.11.8` (current latest stable on 2026-05-04).
Dependabot's `pip` ecosystem already monitors this; bumps will arrive as ordinary PRs.

This eliminates §3.3 (uv-release-induced drift).

### 4.3 Standardize Python version

Both `lockfile-update.yml` and `ci.yml` lockfile-check should use the *same* Python version.
juniper-data and juniper-canopy already standardize on 3.14; juniper-cascor and juniper-cascor-worker will follow.

This eliminates §3.4 (Python-version-induced drift).

### 4.4 Defer §3.5 (Dependabot regen race)

The `lockfile-update.yml` Dependabot push hook is the right architecture; the failure mode is timing-dependent and rare.
The constraint-satisfaction model removes the penalty: if Dependabot bumps a transitive that's still satisfied by the pin, the gate no longer fails.
Only direct-dep bumps (which Dependabot announces by editing `pyproject.toml`) need a follow-up regen, and those are visible.

If we observe further regen-race failures *after* §4.1–§4.3 ship, the next step is to make the lockfile-update workflow a *required* check on Dependabot PRs (currently advisory).
Out of scope for this redesign.

---

## 5. Rollout plan

| Order | Repo                  | Change                                                  | PR    |
|-------|-----------------------|---------------------------------------------------------|-------|
| 1     | juniper-cascor        | Regen lockfile (sentry 2.59) + constraint mode + pin uv | (TBD) |
| 2     | juniper-cascor-worker | Constraint mode + pin uv                                | (TBD) |
| 3     | juniper-data          | Pin uv (already constraint-mode)                        | (TBD) |
| 4     | juniper-canopy        | Pin uv (already constraint-mode)                        | (TBD) |
| 5     | juniper-ml            | Pin uv in `lockfile-update.yml`                         | (TBD) |
| 6     | juniper-data-client   | Pin uv in `lockfile-update.yml`                         | (TBD) |
| 7     | juniper-cascor-client | Pin uv in `lockfile-update.yml`                         | (TBD) |

juniper-deploy is unaffected — no Python lockfile.

---

## 6. Validation

After all PRs merge, the success criteria are:

1. **Cascor main back to green** — the immediate blocker.
2. **No byte-for-byte gates remain** — `grep -r "tail -n +3 requirements.lock" .github/workflows/` returns nothing across all 4 lockfile-having repos.
3. **uv pinned everywhere** — `grep -r "pip install uv$" .github/workflows/` returns nothing across all 7 workflow-having repos.
4. **The 2026-05-04 sentry-sdk failure mode no longer fails CI** — verify by re-running cascor `Lockfile Freshness` on the post-fix main and confirming green.

---

## 7. Future work (out of scope)

- Centralize compile flags in `[tool.uv]` blocks in `pyproject.toml` rather than CI workflow `--extra` lists. Reduces 4 separate workflow edits to 1 config edit.
- Make `lockfile-update.yml` a required check on Dependabot PRs.
- Consider replacing `pip install uv==X.Y.Z` with `astral-sh/setup-uv@vN` action for faster install + automated cache.
