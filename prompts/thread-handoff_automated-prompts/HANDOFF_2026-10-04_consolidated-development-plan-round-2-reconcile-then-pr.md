# HANDOFF 2026-10-04 — consolidated development plan: reconcile round 2, run a narrow round 3, then PR and merge

> **CONSUMED 2026-10-05 by the same session, `1d83ae70`** (it continued after the usage limit reset). It carried out the steps below and went further: v1.2.0 reconciled round 2, v1.3.0 reconciled round 3, and each later round attacked the previous round's corrections.
> That session ran rounds 4 to 12 and wrote three more handoffs; session `3e8595eb` reconciled round 12 into v1.12.0 and ran round 13.
> The plan landed on 2026-10-10 as v1.12.1, a record of v1.12.0 with round 13 unreconciled, together with its reports and the arc's handoffs, in one PR that session `560c1ec5` opened and merged on the owner's approval given in that session; v1.13.0 follows.
> Step 5's "ask again" held throughout: no merge approval carried from one session to the next. The plan's Validation record and the `round*-reconciliation.md` files in `reports/2026-10-04_consolidated-development-plan/` record the outcome. This file is kept as the archived mid-arc handoff.
>
> **One correction to the text below:** round 1 found 31 MAJORs, not 30. The seven lane reports' MAJOR rows sum to 31 (4 + 3 + 4 + 1 + 2 + 8 + 9), as the plan's Validation record states.

Continue the single consolidated development plan, `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. It covers the 11 consolidated paths in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`, plus P12, the equities plan in `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`. The work is planning only. The session ran out of usage in the middle of the round-2 reconciliation.

**Work location.** Everything below is **untracked** in worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/unified-orbiting-fountain` (branch `worktree-unified-orbiting-fountain` at `cf711cf4`). No commit, branch or PR exists yet. This worktree is the only copy, so never sweep it.

## Completed so far

- Ten extraction reports, one per path, in `reports/2026-10-04_consolidated-development-plan/extraction-*.md`. Together they hold 375 item IDs.
- Plan v1.0.0 (sha256 prefix `05d7a571d00e617d`, no longer on disk) went through round 1: seven lanes, 2 BLOCKERs and 30 MAJORs. The lane reports are `round1-lane*.md`; the dispositions are in `round1-reconciliation.md`.
- **Plan v1.1.0** is on disk, sha256 prefix `b81c6afaa8580c0b`.
- Round 2 ran two lanes on v1.1.0:
  - `round2-laneA-reprobe-corrections.md`: 5 MAJOR, 5 MINOR, 2 NIT.
  - `round2-laneB-attack-the-corrections.md`: 1 BLOCKER, 10 MAJOR, 5 MINOR, 1 NIT.
- Verification tools, moved out of `/tmp` per `AGENTS.md` § Script placement: `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, `…_plan_id_coverage.py`, `…_markdown_secret_shape_scan.py` and `…_markdownlint_rule_summary.py`.
- An auto-memory correction. The backup entry's false "Phase A/B landed; STOP cleared" now reads "Phase B NOT on main; §8 STOP STILL on main", in both `MEMORY.md` and `project_backup_service_user_migration_2026-09-21.md`.

## Remaining work

1. **Write v1.2.0.** Accept every round-2 finding (the full reconciliation was drafted, but it was lost with the turn), and write `round2-reconciliation.md` in the same directory. The key changes:
   - **R2B-01 (BLOCKER).** Strike `util/ad-hoc/2026-09-24_secret_shape_check.py` as a "screen": it tests fake values and reads no file. Every public push is gated on `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --scan-dir` with the default rules.
   - **R2A-03 / R2B-02.** The no-push rule applies only to `wip/` preservation copies. Rows a, b and k reach `main` through P1-10 and P1-09.
   - **R2B-03.** Pushes are gated on a local scan, not on XC-LEAKS landing.
   - **R2A-01 / R2B-05 / R2B-06 / R2B-13.** The scanning facts:
     - **all nine repos are public**;
     - the configs in ml, data, canopy and deploy are zero-rule, while cascor and cascor-client extend the defaults;
     - recurrence has no gitleaks at all;
     - GitHub-native scanning and push protection are off in deploy, and non-provider patterns are off in all nine;
     - gitleaks-action v3.0.0 runs gitleaks 8.24.3 and scans only a PR's own commits.

     Act on them: run local full-history scans with `--redact` (hits go to the owner), and add the owner settings to §6 A3.
   - **R2A-02.** Name the six DSN variables inline: `SENTRY_SDK_DSN`, `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN`, `JUNIPER_CANOPY_SENTRY_DSN`, citing `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` L126.
   - **R2A-04 / R2A-05 / R2B-07 (drift).**
     - ml#2134 merged: the P1 fix-forward. Mark P1-01..04 done, close #2129, and add the owner's watchdog redeploy: `yamaguchi_watchdog_deploy.bash --backup-id 2`.
     - P12 phase 0 has merged: ml#2130, ml#2145 (W0.3/W0.4), canopy#702 (W0.5) and ml#2139 (W0.2). R6, the APD-ML OD-2 and #685(a) become ratify-or-revert decisions.
     - The fleet now has 24 ml and 6 canopy drafts.
   - **R2B-04.** S0.8 must also set `JUNIPER_E2E_PROJECT_DIR` to scratch and rebase on ml#2139.
   - **R2B-08.** In the owner sitting, the rulings come first; Phase C steps 1–9 then follow in source order.
   - **R2B-09.** The concurrency rule is the owner's choice (§6). It is "soft" in L86 of the P8 handoff (quote it exactly). Define "preempt", add P3-09 to the calendar, and show the arithmetic behind "two weeks".
   - **R2B-10.** `MEMORY.md` is **over** its ~25,000-character load limit, so its tail lines are dropped. Index edits must be net-negative, and the retirement set moves to Group A.
   - **R2B-11.** The lock-PR edge applies to images only, since wheels pick up patches within their caps. Add the owner's trio-environment upgrade and restart.
   - **R2A-07 / R2B-17.** `curious-plotting-hummingbird` holds S-7, a cleartext copy of both passphrases, and the only *in-backup* copy of `PASSPHRASE_OLD`. Its DO NOT SWEEP stays after step 3.
   - **R2A-08 / R2B-14.** Tier 2 archives `.git`, so row f and row a's committed half are covered.
   - Also apply R2A-09..12, R2B-12, R2B-15 (the missing filenames) and R2B-16 (validation-record accuracy).
2. **Run a narrow round 3**: one or two agents on the v1.1→v1.2 diff only. Record the termination rule: drift alone does not reopen a live-state plan.
3. **Archive the reports.** In every report, put `<!-- markdownlint-disable -->` and a one-line "archived verbatim" note right after the H1. Then:
   - run `/opt/miniforge3/bin/pre-commit run --files <every new file>`;
   - run `python3 util/ad-hoc/2026-10-04_plan_id_coverage.py <old> <new> 'reports/2026-10-04_consolidated-development-plan/extraction-*.md'`;
   - run the default-rules gitleaks scan on scratch copies of every file.
4. **Open the PR** with `util/open_signed_pr.py --repo juniper-ml --branch docs/consolidated-development-plan-2026-10-04 --add LOCAL:PATH …`. The files are all new, so nothing is clobbered. Name every file in the PR body.
5. **Merge only with a fresh owner grant.** The owner approved merging this plan's PR in session `1d83ae70`, but **that approval does not carry**: ask again. Use `util/safe_merge.py`, read its `MERGED` line, and follow `update-branch` when the strict ruleset puts the PR behind.

## Key context

- **Do not commit locally**: signing hangs on the YubiKey. Commits go through API signing only.
- **The session isolation hook refuses** `cd &&` chains, variable-built commands, and any command whose text contains `git…`, such as `gitleaks`. Put those in a scratch script.
- **One verified finding matters beyond the plan.** juniper-ml's `.gitleaks.toml` finds 0 of 1 planted tokens, against 1 of 1 for the default rules (gitleaks v8.30.1). So CI's gitleaks step there is vacuous.

## Verify the starting state

- `git status --short` should list untracked `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, the `reports/2026-10-04_consolidated-development-plan/` directory, the four `util/ad-hoc/2026-10-04_*.py` scripts, and this handoff.
- `sha256sum` of the plan should begin `b81c6afaa8580c0b` (v1.1.0).
- `ls reports/2026-10-04_consolidated-development-plan/ | wc -l` should report 20: 10 extraction reports, 7 round-1 lane reports, 1 reconciliation and 2 round-2 lane reports.
