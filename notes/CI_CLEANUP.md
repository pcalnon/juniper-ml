# CI Cleanup, Next Steps

most recent evaluation of remaning next steps:

```bash
  ┌──────────────┬──────────────────────────────────────────────────┬──────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  Option      │  Item                                            │  Effort      │  Why                                                                                                                                                                                                                                                                │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  1.          │ Tackle deferred cascor/data pre-commit failures  │ 30 min – 1   │ You explicitly deferred these to a separate session. They've been red for days. Root cause is the conf/conda_environment_ci_2026-05-18_17:21:29.yaml / _17:21:50.yaml filenames — yamllint chokes on the colons-in-filenames + invalid YAML inside. Probably       │
  │              │                                                  │ hr           │ either rename or .yamllintignore them.                                                                                                                                                                                                                             │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  2.          │ Manually verify §5 weekly job end-to-end         │ 10 min       │ Trigger docs-full-check.yml via workflow_dispatch now (vs. waiting for Monday 06:00 UTC). Validates the §5.1 lint + §5.2 downstream integration against fresh clones in the real CI environment. No code; just a button.                                           │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  3.          │ Port test_workflow_script_paths.py to consumer   │ 1 hr         │ Plan §5 specifically called it "copy-and-paste portable into the other Juniper repos' tests/". Multiplies the §5 protection: catches the same "workflow references missing script" class in canopy/cascor/data CI directly, instead of relying on juniper-ml's     │
  │              │   repos                                          │              │ weekly lint.                                                                                                                                                                                                                                                       │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  4.          │ Wave 3 — pre-commit hook adoption                │ 30 min       │ Optional in plan. Adds juniper-check-doc-links to .pre-commit-config.yaml so devs catch broken doc links before push. Local-dev quality-of-life; not a CI guarantee.                                                                                               │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  5.          │ Pattern-hunt for other inline-script duplication │ 1–2 hr       │ The migration's value was eliminating drift between 8 inline copies of one script. Are there other utility scripts duplicated across the ecosystem that would benefit from the same treatment? worktree_*.bash, reap_pytest_orphans.bash, etc.                     │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  6.          │ Worktree hygiene sweep                           │ 15 min       │ The worktrees/ dir still has ~15 stale worktrees from older sessions (frontend-issues/pr-*, etc.). Could audit + clean up the obviously-stale ones.                                                                                                                │
  ├──────────────┬──────────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │  7.          │ Wrap session                                     │ 0            │ Migration arc is fully closed. Defer everything else.                                                                                                                                                                                                              │
  └──────────────┬──────────────────────────────────────────────────┴──────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

```

item 1  is in progress

---

| CI: push | CI: PR  | Check Description                                    |
|:--------:|:-------:|:-----------------------------------------------------|
| Success  | Success | Pre-commit (Python 3.12)                             |
| Success  | Success | Pre-commit (Python 3.13)                             |
| Success  | Success | Pre-commit (Python 3.14)                             |
| Success  | Success | Documentation Links                                  |
| Success  | Success | Async-route audit (BUG-JD-10 class)                  |
| Success  | Success | Lockfile Freshness                                   |
| Success  | Success | Unit Tests + Coverage (Python 3.12 on ubuntu-latest) |
| Success  | Success | Unit Tests + Coverage (Python 3.13 on ubuntu-latest) |
| Success  | Success | Unit Tests + Coverage (Python 3.14 on ubuntu-latest) |
| Success  | Success | Unit Tests + Coverage (Python 3.12 on macos-latest)  |
| Success  | Success | Integration Tests (Python 3.12)                      |
| Success  | Success | Integration Tests (Python 3.13)                      |
| Success  | Success | Integration Tests (Python 3.14)                      |
| Failure  | Failure | Security Scans                                       |
| Success  | Success | Build Package                                        |
| Failure  | Failure | Dependency Documentation                             |
| Failure  | Failure | Quality Gate                                         |
| Skipped  | Skipped | Notify Downstream Repos                              |

---

**Other items (from notes/CI_CLEANUP.md)**:

1. Cascor / data deferred pre-commit failures — explicitly deferred; root cause is conda_environment_ci_2026-05-18_17:21:29.yaml filename (colons-in-filenames choke yamllint).
2. Manually trigger docs-full-check.yml — 10-min validation that §5.1 / §5.2 drift lints work in real CI vs. the just-shipped v0.2.0.
3. Bump juniper-ml/pyproject.toml — juniper-ci-tools>=0.1.0 → >=0.2.0 so the meta-package's [tools] extra delivers the new console script. Small but real.
4. Worktree hygiene sweep — ~15+ stale frontend-issues worktrees in worktrees/.
5. Pattern-hunt for other inline-script duplication — worktree_*.bash, reap_pytest_orphans.bash, etc.

---

Outstanding follow-ups (none release-blocking)

**Tier 1 — worth doing soon (post-ship verification):**

1. Fresh-env install verification per runbook §8. Five commands; ~10 minutes wall time (the [all] install pulls ~2 GB). Confirms the published metadata actually resolves end-to-end before any user hits a problem. Low cost, high signal.
2. Manual smoke-test of the three install paths the user originally reported as broken: pip install juniper-ml[servers], [tools], [all] on the actual JuniperCanopy1 env (or a throwaway). Closes the loop on the original ticket.

**Tier 2 — hardening, can defer:**

3. Extend TestPyPI verify to also install [tools]. It's nearly as light as [clients] (no torch — observability + doc-tools + ci-tools are all small) and would catch a broken [tools] at publish time. Costs ~20s of CI per release. Runbook §7 documented the gap; this closes it.
4. Downstream consumer pin bumps. If any of the 7 sibling repos consume juniper-ml in their dev/test workflows, they can now bump to >=0.5.0 to gain access to [servers] for integration tests. Worth a quick grep across sibling repos.

**Tier 3 — deferred until natural trigger:**

5. JR-ML- ID assignment.* Waits for the next snapshot refresh (per notes/META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md §4). Not actionable until then.
6. [servers] test-installation in CI. Heavy (~2 GB with torch via cascor); would only justify itself if a [servers] regression actually shipped. Schema lint covers the typo class.

---

Reasonable next-step candidates:

| # | Item                                                                                                                                                                                                        | Effort                  | Why                                                                                          |
|:--|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------|:---------------------------------------------------------------------------------------------|
| A | Write thread handoff doc for the next agent (per AGENTS.md policy + prior session's pattern at handoff_ci-hygiene-completion_2026-05-21.md)                                                                 | 5 min                   | Captures this session's 11 PRs, the canonical lint, and open watchpoints so continuity holds |
| B | Drift-class hunt — apply same playbook, find ecosystem drift surfaces: **Last Updated**: headers, juniper-ci-tools pin currency in juniper-ml/cascor/canopy (Wave 4 fanout incomplete), PyPI-vs-git-tag lag | 30–60 min               | Multiplies the strategic-fix value                                                           |
| C | Watch for fallout from in-flight cascor API-09 PR 3/3 — once it lands, downstream juniper-cascor-client may need an adapter update                                                                          | 10–15 min once it lands | Direct downstream-consumer risk                                                              |
| D | Stop here — ecosystem is in a uniquely clean state; let Paul drive the next directive                                                                                                                       | 0                       | Conservative                                                                                 |
| E | CI_CLEANUP item #4 (pre-commit juniper-check-doc-links adoption)                                                                                                                                            | 30 min                  | Optional, originally flagged as quality-of-life                                              |


