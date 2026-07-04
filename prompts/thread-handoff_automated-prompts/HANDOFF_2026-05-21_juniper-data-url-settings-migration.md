# Juniper Data URL Settings Migration

## Reference Thread

Continuing work from thread T-019e4c54-2699-76b9-a1b5-0c48b10b618f (which itself continued from T-019e4983-fa63-75be-9936-85daece45be4). When you lack specific information, use read_thread to fetch it.

## Working Document

@notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md

## Description

I have been working through a sequence of configuration and API contract items from the v7 roadmap in juniper-cascor.

### Completed Work

**Completed in the immediately prior session:**

- CFG-04 (juniper-cascor PR #297, awaiting merge):
  - Added Settings.juniper_data_url: str | None field to src/api/settings.py with AliasChoices("juniper_data_url", "JUNIPER_DATA_URL", "JUNIPER_CASCOR_JUNIPER_DATA_URL") (canonical first)
  - Migrated all 8 raw os.environ.get/os.getenv call sites across:
    - src/api/app.py (×3)
    - src/api/routes/health.py
    - src/api/lifecycle/manager.py
    - src/main.py
    - src/spiral_problem/spiral_problem.py
    - src/spiral_problem/data_provider.py

- Diverged from CFG-03/05 — this is not a deprecation since JUNIPER_DATA_URL remains the canonical ecosystem-wide name:
  - no env-var rename
  - no DeprecationWarning
  - no removal timeline

- New 7-case regression suite at src/tests/unit/test_cfg_04_juniper_data_url_settings.py.

- Updated 1 existing test to pass juniper_data_url= kwarg instead of post-Settings env patching:
  - test_api_app_coverage_deep.py::test_auto_start_uses_environment_variables

**Completed earlier (full sequence: CFG-03 → CFG-05 → API-09 → CFG-04):**

- CFG-03 (PR #287): Converged SENTRY_SDK_DSN → JUNIPER_CASCOR_SENTRY_DSN with deprecation period.
- CFG-05 (PR #289): Converged CASCOR_LOG_LEVEL → JUNIPER_CASCOR_LOG_LEVEL with deprecation period.
- API-09 (PRs #293, juniper-cascor-client #59, #296): Migrated HTTPException responses to ResponseEnvelope shape in 3 PRs (handler with dual-shape alias → client regression coverage → drop alias).

**Established patterns (carry forward):**

- Deprecation pattern (CFG-03/05):
  - Helper function preferring prefixed name
  - falling back to legacy with DeprecationWarning
  - emitting stderr line if both differ
  - Regression test pins precedence

- Convergence-without-deprecation pattern (CFG-04):
  - When the env var is already canonical/ecosystem-wide, add a Settings field via AliasChoices listing the canonical name first plus the prefixed form as a per-service override.
  - No DeprecationWarning, no removal timeline.
  - CHANGELOG entry under ### Changed, not ### Deprecated.

- Design-First:
  - For complex items (API-09 scale), write a design doc first to validate rollout strategy.
  - CFG-04 was mechanical enough to skip this.

- Roadmap Staleness:
  - The v7 roadmap is ~50% stale.
  - Always re-verify line numbers and implementation status via rg/grep/git blame before starting work.

- Cleanup Gate:
  - Only delete local/remote branches after the user says "PR merged" AND I verify the MERGED state via gh pr view <N> --json state,mergedAt.
  - Worktrees in /home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--<timestamp>--<hash>/.

- Editable-install rot:
  - The juniper_data_client editable install pointed to a deleted worktree
  - re-installed from /home/pcalnon/Development/python/Juniper/juniper-data-client/ during testing
  - Watch for similar rot on other Juniper packages.

## Next steps

- Wait for PR #297 (CFG-04) merge confirmation from the user.
- Once merged, clean up the following:
  - worktree at /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--cfg-04-juniper-data-url-settings--20260521-1559--b1f9ea3a/
  - branch fix/cfg-04-juniper-data-url-settings (local + remote)
  - ask the user for the next roadmap item in the configuration / API contract series.

## Active git state

- Repo: /home/pcalnon/Development/python/Juniper/juniper-cascor/ (main, clean, at b1f9ea3 pre-CFG-04)
- Open branch: fix/cfg-04-juniper-data-url-settings at ef9c27a, pushed to origin
- Open worktree: /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--cfg-04-juniper-data-url-settings--20260521-1559--b1f9ea3a/
- Open PR: <https://github.com/pcalnon/juniper-cascor/pull/297>

## Verification on entry

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git fetch origin --prune && git log --oneline -3 origin/main
gh pr view 297 --json state,mergedAt,headRefName
```

---
