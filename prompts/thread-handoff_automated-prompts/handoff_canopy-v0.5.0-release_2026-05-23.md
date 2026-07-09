# Handoff — juniper-canopy v0.5.0 release-prep + release (2026-05-23, late evening UTC)

Continue the PyPI ↔ git tag lag fix initiative (juniper-ml ecosystem audit
2026-05-22). **juniper-cascor v0.5.0 has shipped** (PR #300 merged, v0.5.0 tag
cut, PyPI publish succeeded — releases on PyPI: `..., 0.3.17, 0.5.0`; 0.4.0
correctly skipped because it was never published). **juniper-canopy is the
remaining work** in the same lag-fix initiative.

## State right now

| Item                         | State                                                                                   |
|------------------------------|-----------------------------------------------------------------------------------------|
| juniper-cascor pyproject     | 0.5.0 ✅                                                                                |
| juniper-cascor tag           | v0.5.0 ✅                                                                               |
| juniper-cascor PyPI          | 0.5.0 ✅                                                                                |
| **juniper-canopy pyproject** | **0.4.0** ← bumped 2026-03-03, never released                                           |
| **juniper-canopy tag**       | **v0.3.0** ← last released stable; `v0.X-alpha` series above are pre-PyPI local tags    |
| **juniper-canopy PyPI**      | **0.3.0** ← matches tag                                                                 |
| juniper-canopy lag           | 983 commits since `v0.3.0`                                                              |
| Other lag cases              | juniper-cascor-client (0.4.0 in pyproject, 0.3.0 on PyPI) — **another agent owns this** |

## What's needed for canopy

Same playbook as cascor PR #300, but expect **more hardcoded-version landmines** because canopy scope is larger.

### Phase 1: release-prep PR

Mechanical bumps:

1. **`pyproject.toml`** — `version = "0.4.0"` → `"0.5.0"` (line 29) and `# Version: 0.4.0` header comment (line 7). Also line 142 has a comment `current release floor (0.4.0)` — **verify what this refers to** before touching; might be canopy's own current-floor self-reference (bump) or a dependency constraint (leave alone).
2. **`AGENTS.md`** — bump `**Version**: 0.4.0` → `0.5.0`. (Already on canonical schema with `**Last Updated**: 2026-05-22 or 23` from auto-bump; touch-up workflow will refresh to today's UTC date.)
3. **`conf/conda_environment_ci.yaml`** — bump line 7 (Version comment) and line 145 (`juniper-canopy==0.4.0`).
4. **Other conf files matching `0.4.0`** — pre-scan with `grep -rn "0\.4\.0" --include="*.yaml" --include="*.yml" conf/` to catch any I missed.
5. **`CHANGELOG.md`** — rename `[Unreleased]` to `[0.5.0] - 2026-05-22` (or today's UTC date) with the same "Note on version history" callout that cascor used:

   ```markdown
   ## [0.5.0] - 2026-05-22

   **Note on version history**: `pyproject.toml` was bumped 0.3.0 → 0.4.0 on
   2026-03-03 in preparation for a 0.4.0 release that was never cut to PyPI
   (the `[0.4.0]` section below documents the work that *would have*
   shipped). This 0.5.0 release rolls up both that work and the subsequent
   ~2.5 months of changes (983 commits since `v0.3.0`) into a single PyPI
   release.
   ```

6. **Hardcoded source versions** — already scanned, expect failures unless bumped:
   - `src/__init__.py:7` — `__version__ = "0.4.0"`
   - `src/main.py:100` — `APP_VERSION = "0.4.0"`
   - (Both will surface in CI as unit-test failures, like cascor's `_API_VERSION` did. Bump pre-emptively to save a CI cycle.)

7. **Hardcoded test versions** — 7+ sites, pre-scanned:
   - `src/tests/fixtures/cascor_response_fixtures.py:19, 32`
   - `src/tests/unit/test_observability.py:458, 482`
   - `src/tests/unit/test_r2_1_5_wire_compat.py:126`
   - `src/tests/unit/test_observability_coverage.py:183`
   - `src/tests/unit/test_response_normalization.py:758, 774, 801`
   - **Bulk replace**: `sed -i 's/"0\.4\.0"/"0.5.0"/g' <files>`. Cascor's experience suggests the test assertions need to match whatever the source ships.

Open PR; expect:

- **AGENTS.md Touch-Up workflow** to fire and bump Last Updated on each PR push (idempotent if already today's UTC date).
- **Update Lockfile (Dependabot) workflow** to push back a regenerated `requirements.lock` (canopy has this same workflow). May race with touch-up — rebase + push to resolve. Same dance as cascor #300.
- **CI/CD Pipeline failures** if any hardcoded version was missed. Iterate.

Merge with `gh pr merge <N> -R pcalnon/juniper-canopy --admin --squash --delete-branch`.

### Phase 2: release

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
gh release create v0.5.0 -R pcalnon/juniper-canopy --target main \
  --title "juniper-canopy v0.5.0" \
  --notes "<see cascor v0.5.0 release notes structure for a template; canopy CHANGELOG [0.5.0] section will be richer due to 983 commits>"
```

Triggers `publish.yml` (event: `release: published`) → TestPyPI publish (with install verify) → manual approval gate → PyPI publish via OIDC.

The PyPI environment requires manual approval (same as cascor and juniper-ci-tools v0.4.0 did). Paul has already approved the *initiative*; the per-release PyPI approval is the standing process. Approve via:

```bash
ENV_ID=$(gh api repos/pcalnon/juniper-canopy/actions/runs/<RUN_ID>/pending_deployments --jq '.[] | select(.environment.name == "pypi") | .environment.id')
gh api -X POST repos/pcalnon/juniper-canopy/actions/runs/<RUN_ID>/pending_deployments --input - <<EOF
{"environment_ids": [$ENV_ID], "state": "approved", "comment": "Phase 2 of PyPI/tag lag fix — release 0.5.0 supersedes the never-cut 0.4.0 pyproject bump from 2026-03-03."}
EOF
```

(or via the GitHub UI on the workflow run's "Review deployments" button — equivalent).

### Phase 3: verify

```bash
curl -s https://pypi.org/pypi/juniper-canopy/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# expect: 0.5.0
```

And the drift map (run from any worktree of juniper-ml):

```bash
for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client juniper-deploy; do
  cd /home/pcalnon/Development/python/Juniper/$r
  git fetch origin --tags >/dev/null 2>&1
  pyproject_v=$(git show origin/main:pyproject.toml 2>/dev/null | grep -E '^version = ' | head -1 | awk -F'"' '{print $2}')
  tag_v=$(git tag -l 'v*' --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
  printf "%-25s pyproject=%-7s  tag=%s\n" "$r" "${pyproject_v:-n/a}" "${tag_v:-(none)}"
done
```

After canopy releases, the *only* remaining lag case is juniper-cascor-client
(another agent owns it).

## Key context

- **Worktree**: this handoff was written from `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/validated-squishing-pond`. The actual canopy work happens in `/home/pcalnon/Development/python/Juniper/juniper-canopy` (main checkout) — branch off `origin/main` there for the release-prep PR.
- **Branch naming**: cascor used `release/v0.5.0` — use the same for canopy.
- **The `v0.X-alpha` tag series** in juniper-canopy + juniper-data are legacy local-only GitHub releases from before PyPI publishing started; ignore them as drift indicators. Stable releases use plain `vX.Y.Z`.
- **Auto-bump workflow + AGENTS.md schema lint are already adopted in canopy** (juniper-canopy#313 shipped 2026-05-22). They'll work transparently during the release-prep PR.
- **Other in-flight work**: juniper-cascor-client has a separate agent working on it. Don't touch.

## Why this was deferred

The session ran past midnight UTC. Cascor v0.5.0 was shipped cleanly as a single irreversible step (per Paul's "Cut cascor v0.5.0 release now, then stop" directive). Canopy has roughly equivalent landmines but more of them; ~30-45 min of work plus a second irreversible PyPI publish. Splitting at this checkpoint kept the irreversible blast radius small per session.

## Verification commands for the new thread (start here)

```bash
# 1. Confirm cascor is fully in sync (the prior session's deliverable)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git fetch origin --tags
git show origin/main:pyproject.toml | grep '^version' && \
git tag -l 'v0.5.0' && \
curl -s https://pypi.org/pypi/juniper-cascor/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"

# 2. Confirm canopy drift state (starting state for this thread's work)
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git fetch origin --tags
git show origin/main:pyproject.toml | grep '^version'  # expect 0.4.0
git tag -l 'v*' --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1  # expect v0.3.0
curl -s https://pypi.org/pypi/juniper-canopy/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"  # expect 0.3.0

# 3. Pre-scan hardcoded 0.4.0 in canopy (to plan the bump)
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
grep -rn '"0\.4\.0"' src/ --include="*.py" 2>/dev/null
grep -rn "0\.4\.0" --include="*.toml" --include="*.yaml" --include="*.yml" conf/ pyproject.toml 2>/dev/null
```

---
