# `juniper-ci-tools` Extraction Playbook

**Last updated:** 2026-05-21
**Status:** Proven 3× — v0.1.0 (dep-docs generator), v0.2.0
(workflow-paths lint), v0.3.0 (agents-md-version lint).

This is the condensed how-to for extracting a duplicated CI script out
of the 6 consumer repos and into the shared `juniper-ci-tools` package.
For background, motivation, and the long-form per-wave plan see
[`JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`](JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md);
this file is the abridged operational sequence for future extractions.

---

## 1. When to extract (trigger)

Extract only when there is a **concrete drift incident on file**. A
duplicated script alone is not enough — the playbook costs one
package release + 6 PRs. Past triggers:

| Extraction | Concrete incident |
|---|---|
| v0.1.0 `juniper-generate-dep-docs` | cascor 2026-05-20 awk fix in [cascor#276](https://github.com/pcalnon/juniper-cascor/pull/276); 4 repos had stale sed pipeline that emitted invalid YAML |
| v0.2.0 `juniper-lint-workflow-paths` | 3 juniper-X CIs broke 2026-05-18 when a file referenced by `python <path>` in `ci.yml` was renamed |
| v0.3.0 `juniper-lint-agents-md-version` | juniper-ml#295 bumped pyproject 0.4.1 → 0.5.0 but left AGENTS.md `**Version**:` at 0.4.0 for ~6 days (fixed in juniper-ml#304) |

**Defer** when the script is a local-dev convenience tool with no
incident (e.g. `util/worktree_*.bash`, `util/requirements_drift_check.py`)
— see plan §2 non-goals.

---

## 2. Four-phase workflow

### Phase 1 — Canonicalize in juniper-ml

Add the regression test or script as `juniper-ml/tests/test_<name>.py`
(for unittest-style lints) or `juniper-ml/util/<name>.py` (for general
utilities). This is the dogfooded source of truth.

This phase is often already done by the time you decide to extract —
the script that exposed the drift incident often lived in juniper-ml
first. If so, skip to Phase 2.

### Phase 2 — Package extraction (single juniper-ml PR)

In juniper-ml, under `juniper-ci-tools/`:

1. Add the library module: `juniper_ci_tools/<name>.py` (importable
   API; no `sys.exit` calls; raise on failure).
2. Add the CLI shim: `juniper_ci_tools/cli_<name>.py` (`argparse` +
   `main()` that calls the library and translates exceptions to exit
   codes 0/1/2).
3. Register the console script in `juniper-ci-tools/pyproject.toml`:
   ```toml
   [project.scripts]
   juniper-<verb>-<name> = "juniper_ci_tools.cli_<name>:main"
   ```
4. Bump `juniper_ci_tools/_version.py` to `0.<N>.0`. Update
   `juniper-ci-tools/CHANGELOG.md`.
5. Add `juniper-ci-tools/tests/test_<name>.py` — unit tests for the
   library + smoke test for the CLI.
6. Update `juniper-ci-tools/README.md` with the new console script.
7. Widen juniper-ml's own pins in `.github/workflows/{ci,docs-full-check,lockfile-update}.yml`
   from `juniper-ci-tools>=...,<0.<N>.0` to `<0.<N+1>.0`.
8. Open + merge the PR (`feat(juniper-ci-tools): v0.<N>.0 — add
   juniper-<verb>-<name> console script`).

### Phase 3 — Publish

After the package PR merges, tag and push:

```bash
git tag juniper-ci-tools-v0.<N>.0
git push origin juniper-ci-tools-v0.<N>.0
```

The publish workflow waits at the **TestPyPI** environment approval
gate, then the **PyPI** environment approval gate. Both need manual
approval in the GitHub Actions UI. After PyPI publishes, verify:

```bash
curl -sf https://pypi.org/pypi/juniper-ci-tools/json |
  python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])"
```

### Phase 4 — Fan out to 6 consumers

The consumer repos are: `juniper-data-client`, `juniper-canopy`,
`juniper-cascor`, `juniper-cascor-client`, `juniper-cascor-worker`,
`juniper-data`. **Not** `juniper-ml` (its canonical inline test stays
put, see §3 below).

Each consumer PR is the same 2-file diff:

1. `.github/workflows/ci.yml`:
   - Widen the existing `juniper-ci-tools` pin(s) from `<0.<N>.0` to
     `<0.<N+1>.0` (use `replace_all: true` — there are usually 2
     pins, one for the lint install + one for the dep-docs install).
   - Replace the inline `python3 -m unittest -v util/test_<name>.py`
     invocation with the new console script name.
   - Refresh the comment block above the lint to point at the new
     console-script source (juniper-ml PR number).
   - Optionally rename the install step to enumerate all lints it
     covers (e.g. "Install juniper-ci-tools (workflow-path +
     agents-md lints)").
2. `util/test_<name>.py` — **deleted** (byte-identical to the package
   implementation).

Pre-validate locally:
```bash
pip install "juniper-ci-tools>=0.<N>.0,<0.<N+1>.0"
cd <consumer-repo> && juniper-<verb>-<name>   # should pass
```

The 6 PRs can be opened in parallel; each runs through its own CI
independently. The PR title pattern is:
`ci: adopt juniper-ci-tools v0.<N>.0 juniper-<verb>-<name> (Wave 4 fan-out)`.

---

## 3. Special rule: juniper-ml itself is a no-op

When fanning out, **do not** delete juniper-ml's canonical
`tests/test_<name>.py` and **do not** change juniper-ml's own
`ci.yml` invocation to the console script. Reasons:

- juniper-ml dogfoods the canonical regression test in-process,
  alongside the package's own test suite.
- Removing it would force juniper-ml's CI to depend on the published
  version of a script that lives in this repo — a circular tooling
  dependency.
- The pin in juniper-ml's own workflows is already wide enough
  (`>=0.1.0,<0.<N+1>.0` after Phase 2 step 7) to admit the new
  package version for the dep-docs / docs-full-check jobs.

This is the pattern established by Wave 4 (which left
`juniper-ml/tests/test_workflow_script_paths.py` untouched) and
re-confirmed for both extension series.

---

## 4. Cleanup gates

Worktrees + branches are removed only after **both** gates clear (per
the `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15`
project rule):

1. Paul explicitly says the PR is merged (for that specific PR).
2. `gh pr view <N> --repo <r> --json state,mergedAt` confirms
   `state=MERGED` with non-null `mergedAt`.

Then for each merged PR:

```bash
git -C <repo> fetch origin --prune
git -C <repo> checkout main && git -C <repo> pull origin main --ff-only
git -C <repo> worktree remove <worktree-path>
git -C <repo> branch -D <branch>
git -C <repo> push origin --delete <branch>
git -C <repo> worktree prune
```

---

## 5. Cross-cutting conventions

- **Branch name:** `ci/adopt-juniper-ci-tools-v0.<N>.0-<short-name>` in
  every consumer (same branch name across repos for grep-ability).
- **Worktree location:** `/home/pcalnon/Development/python/Juniper/worktrees/`
  per the centralized worktree convention.
- **Commit + PR body:** lead with "Wave 4 of the dep-docs PyPI migration
  plan (juniper-ml `notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`
  §3.4 v0.<N>.0 extension)"; include md5 of the deleted inline copy and
  the local pre-validation output.
- **Drift coverage:** the existing `juniper-ml/tests/test_ci_tools_drift.py`
  already covers any new console script — widening the upper bound in
  each consumer's `ci.yml` (Phase 4 step 1) is the only consumer-side
  change to the drift contract.
- **Plan doc:** add an entry to §7 of the plan doc when a new extension
  ships. Status line at the top should mention "(post-2026-05-21
  extension series)".
