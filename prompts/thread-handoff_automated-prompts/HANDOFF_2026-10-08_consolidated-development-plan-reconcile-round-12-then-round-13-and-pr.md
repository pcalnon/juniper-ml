# Thread handoff: consolidated development plan, reconcile round 12 into v1.12.0, run round 13, then PR

**Written**: 2026-10-08 ~18:35Z by session `1d83ae70`, at the round-12 boundary, because the thread was long (a handoff instead of compaction).
**Supersedes**: `HANDOFF_2026-10-08_consolidated-development-plan-finish-round-10-reconcile-then-round-11-and-pr.md`, which the same session consumed (it gets a CONSUMED banner in the PR).

> **CONSUMED 2026-10-08 to 2026-10-10 by session `3e8595eb`.** It reconciled round 12 into v1.12.0 (frozen 2026-10-08T22:56Z), ran round 13 (1 BLOCKER, 16 MAJOR), and at the owner's request handed off before reconciling it.
> Its handoff is `HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`, on `main` through ml#2207. On 2026-10-10 the owner ruled to land the plan first as a record and re-baseline it as v1.13.0 after.
> Session `560c1ec5` landed v1.12.1, a record of v1.12.0 with round 13 unreconciled, in one PR that it opened and merged on the owner's approval given in that session. This file is kept as the archived mid-arc handoff.

Continue the consolidated-development-plan arc in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/unified-orbiting-fountain`
(branch `worktree-unified-orbiting-fountain` at `cf711cf4`; every PR file is UNTRACKED; never `git commit` locally).

## Merge approval

The owner granted merge approval in session `1d83ae70`. **It does not carry over: ask the owner again before running `util/safe_merge.py`.**

## Completed so far

- Plan `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`: rounds 1–11 reconciled. **v1.11.0 was frozen at 2026-10-08T17:28:52Z, sha256 `51cb559a84dcc4b2f1d2cb0758d11dd402da329678d50c7dfe25b94891c00609`**, and the worktree's plan is still exactly that file.
- `reports/2026-10-04_consolidated-development-plan/round11-reconciliation.md` (sha256 `92a2347b…`): 52 findings, all accepted (R11B1-02 in part).
- The four tools as frozen for round 12 (sha256 prefixes):
  - `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py` (the gate): `cb39019ad9e15f2b`; no rule changed since v7;
  - `util/ad-hoc/2026-10-05_gate_regression.py`: `4ff312599fe66031`, 181 cases;
  - `util/ad-hoc/2026-10-05_masked_finding_shape.py` (the line read): `dd2bc7f2d88ec947`;
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`: `275cc45d55a81fb4`.
- v1.11.0 took in the Cursor fleet's end. ml#2181 was closed at 16:10:16Z, ml#2184 merged at 16:40:27Z and ml#2185 (the flood-3 record) at 17:17:37Z, and no PR was open in the nine repositories at 17:26Z. XC-FLEET is rewritten as done, S0.7 is a check for a new flood, and A10 holds only ml#2183's limb.
- **Round 12 ran on v1.11.0** (lanes 17:32Z–18:30Z). The three reports are written and archive-headed, so add 4 to the line numbers the lanes cite inside their own reports:
  - `round12-laneA-reprobe.md`: 0 BLOCKER, 3 MAJOR, 3 MINOR, 9 NIT;
  - `round12-laneB1-safety.md`: 0 BLOCKER, 7 MAJOR, 5 MINOR, 2 NIT;
  - `round12-laneB2-schedule.md`: 0 BLOCKER, 4 MAJOR, 8 MINOR, 4 NIT.
  - That is 43 findings and 14 MAJORs, so the ending rule does not end validation: round 13 runs after v1.12.0.
- **Re-derived already (all confirmed):**
  - R12B2-01: `git show 81d3fbb3:docs/REFERENCE.md` L720 and L779 prescribe `yamaguchi_server_api.py resume` for PAUSED_WITH_QUEUE, and L691 says a resume starts a queued overdue run at once.
  - R12B2-02: plan L1024 offers "vehicle (a)'s release in the primary", which L646 forbids.
  - R12B2-03: juniper-recurrence has no `docs/` and no `REFERENCE` path, so W1.14's PR cannot correct juniper-ml's docs.
  - R12B2-04: H-22's "the fix" (L1163) can be read as W1.14 alone (L104).
  - R12A-01: mutants X3, X11, X12, X19 and X20 survive both checks, and X16 is caught only by chance. The run is `mutants_r12a.json` and `mut12a.txt` in the old scratchpad's `v8/`.
  - R12A-02 and R12B1-06, from the read's code: `mask_tail` prints every NAME_RE match through `_name`, `_B9` has no word boundary, and `_B9_FLAT` prints a flat B9 match whole. So a credential word inside a value prints in clear.
- **Not yet re-derived:** R12A-03 (with R12B2-09 and R12B1-09, the driver lines on `main`); R12B1-01..05, by rebuilding B1's surviving mutants and the openssl argv-list and `_authorization` spellings on synthetic files; and R12B1-07.

## Remaining work (in order)

1. **Set up.** Copy the worktree plan to your scratchpad as `plan_v1.11.0.md` and check its sha256. The old scratchpad is `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/1d83ae70-977d-4a39-adf3-7be0d97b8a27/scratchpad/`. It holds:
   - `main/plan_v1.*.md`, and `main/{gate_v7r11,read_r11,regression_r11,census_r11}.py`;
   - `round6/a1/cases/FP40/`, the 40 real files; read them only masked;
   - `v6/work/` (the verified scanner tarball);
   - `round12/brief-*.md`;
   - the PR drafts `main/pr_body_v112.md`, `main/commit_body_v112.md` and `main/banners-draft.md`.

   If that directory is gone, the plan and tools are in the worktree, and the gate re-downloads its pinned scanner. FP40 cannot be recovered, so skip that check and say so.
2. **Fix the read.** My recommendation is to **mask every run of letters and digits, names included**, so that no character prints in clear except blanks. B1's narrower fix keeps whole-token names in clear, so it still prints a value that is itself a credential word, the weak-password case R12A-02 calls realistic. Listing does not need the words: `names=N` and `markers=M` say why a line is listed. Also:
   - KEY mode prints each line of the key's range whole, masked, with the finding's character offset (R12B1-10). It refuses the way `_files` does, by `lstat`: a symlink or a non-regular file gets exit 3 (R12B1-04).
   - Markers: openssl's argv-list spellings (a quote, comma and quote between `-pass`, `-passin`, `-passout` or `-password` and `pass:`, and after `-k`); `-password`; and `authorization` after `_` (R12B1-05).
   - A hex rule for random-looking: 32 or more hex digits, or a UUID (R12B1-11).
   - The docstring: clause 3 says nothing prints in clear; clause 2 says "non-blank" (R12A-08); clause 4 adds KEY mode's refusals; R12B1-12's layouts and R12A-14's three are listed limits.
3. **Pin it.**
   - The contract check gets one case per survivor: Lane A's X3, X4, X11, X12, X16, X19 and X20 (its R12A-01 row), and B1's 16 (its R12B1-01..04 rows).
   - Add checks that no credential word of a value prints (R12A-02's and B1's values), a hex rule case, and `--all`'s count on a planted line.
   - KEY-mode checks compare against masked lines computed independently. Names no longer print, so the old `P in stdout` check must change.
   - Rebuild the mutation run: round 11's 23 (`v8/mutants_r11c.json`; retarget any whose text the redesign removes, such as M18), Lane A's 7, B1's 16, and "names printed in clear". All must be caught, and the baseline must pass.
   - Then run the full regression, FP40 (49 keys, equal to `v6/fp40-v6-keys.sorted`) and probe mode (32, 3, 31, 0). **Copy every snapshot only after the last edit**: R12A-11 is the third time a copy predated a final edit.
4. **Plan v1.12.0**, by finding (the lanes cite v1.11.0 lines):
   - R12B2-01 and R12A-05: H-23 names `docs/REFERENCE.md` L720 and L779 beside the watchdog's L231. S0.3 gets a small juniper-ml docs PR, under the pre-push scan, that corrects those two lines before sitting item 5 ("during H-23's hold, do not resume"). Item 5 gets "(H-23)".
   - R12B2-02: §9's host-leg row reads "a validated port to the primary's own commit (either vehicle), or under vehicle (b) the primary moved to `main` once everything that imports it takes wave 1; never the 0.5.1 tag's branch or wheel".
   - R12B2-03 and R12A-15: the correction to the section carried from ml#2152 is its own juniper-ml docs PR, opened by S0.11's actor after W1.14 merges. It keeps the operator rule for released 0.5.0, the primary, cascor and records already written until H-22 lifts. Fix XC-FLEET, S0.11 and §8. Every upload of that file meets the gate key `docs/REFERENCE.md:6200:121:juniper-header-refusal:617fbd3a74`, a placeholder (R12A-13).
   - R12B2-04: H-22 lifts per relay. Recurrence's relays lift once it runs W1.14. Cascor's and canopy's, and canopy's leg logs, lift once cascor runs the data-client fix or a cascor fix. Run records lift once both have. A relay whose fix A1 declines never lifts while the condition can recur. Apply the same rule to Wave 2's evidence rule.
   - R12A-03, R12B2-09 and R12B1-09: H-22 and Overview 2 name `acceptance.reasons`, `stats.json`, `summary.md`, the `error` field of `registry.jsonl`, the console reason and degraded lines, and `logs/run_experiment.log`, or point to that section's operator rule.
   - R12B1-07 and R12B2-08: XC-CRED's count search. A non-zero count settles the question, and a zero count leaves §12 open. S0.11's actor runs it before sitting item 6, over named directories.
   - Then the MINORs and NITs as each lane proposes them, the Round 12 section, the instruments, the drift (none to 18:22Z), the version, the Changed list, and round 13 marked pending.
5. **Write `round12-reconciliation.md`**, modelled on round 11's. Record R12A-11's and R12A-12's corrections to round 11's record there, not in place.
6. **Freeze and run round 13.** Run ID coverage, markdownlint and the structure check, and confirm no plan line is over 512. Take the v1.12.0 snapshots and diffs. Write round-13 briefs from round 12's, narrow, on round 12's corrections. Launch three lanes and reconcile. With no BLOCKER and no MAJOR, apply the MINORs and NITs and stop.
7. **PR.**
   - Fill the drafts, and give CONSUMED banners to this file and the round-10 handoff (draft text in `banners-draft.md`).
   - Gate all files, the commit message, the PR body and the path list, with the accepted key `reports/2026-10-04_consolidated-development-plan/round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`. Run `--names` and `--all`.
   - Run `/opt/miniforge3/bin/pre-commit run --files <all>` and `tests/test_thread_handoff_archive.py` (`prompts/` skips the hooks). In this worktree that test fails once, because the plan cites five handoffs that exist on `origin/main` but not at `cf711cf4`. A PR built on current `main` resolves them.
   - Then `util/open_signed_pr.py`, `util/wait_for_checks.py`, and `util/safe_merge.py` only with fresh approval.

## Key context

- Hard limits:
  - never run backup tooling, Duplicati, `systemctl` or service restarts, or touch the trio's ports;
  - never print secrets;
  - read real-file findings only through the masked read;
  - H-22 forbids pasting service bodies, logs or run records.
- Lane briefs must forbid printing the environment or secrets and any external send, and must require slips.
- The command guard refuses loops, `$(…)`, unquoted variables, and `{a, b}` literals or `<(` inside a heredoc. Use lists and `[<](`.
- The regression's names check catches none of the mutants: all of the pinning lives in the contract check.
- S0.13's read, and any juniper-ml docs PR the plan schedules, need the gate, which reaches `main` only with this plan's PR.

## Verify the starting state

- `git -C <worktree> status --porcelain=v1 --untracked-files=all | wc -l` gives 69: 65 PR files, three round-12 reports and this handoff. Nothing is staged and there are no local commits.
- `sha256sum` of the plan and the four tools gives the five prefixes above.
- `python3 -B util/ad-hoc/2026-10-05_ecosystem_live_census.py --since 2026-10-08T18:22:00Z` shows any drift since round 12's last census.
