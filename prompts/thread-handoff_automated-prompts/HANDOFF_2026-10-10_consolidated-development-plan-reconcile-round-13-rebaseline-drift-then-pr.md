# Thread handoff: consolidated development plan, reconcile round 13 and the drift into v1.13.0, then PR

**Written**: 2026-10-10 ~10:50Z by session `3e8595eb` (Claude session `session_016ZArnaAiHH5SUAEBj71fEJ`), at the round-13 boundary, on the owner's request.
**Supersedes**: `HANDOFF_2026-10-08_consolidated-development-plan-reconcile-round-12-then-round-13-and-pr.md`, which this session consumed (it gets a CONSUMED banner in the plan's PR). That file, like every plan file, is still UNTRACKED. This handoff alone lands on `main`, through its own docs PR, opened from `origin/main` by the session that wrote it.

Continue the consolidated-development-plan arc in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/concurrent-gathering-biscuit`
(branch `worktree-concurrent-gathering-biscuit` at `81d3fbb3`, 16 commits behind `origin/main` (`be3314dc`) at 10:45Z on 2026-10-10). Never `git commit` there: land through `util/open_signed_pr.py`, building on `origin/main`.

Short forms: `EX/` = `reports/2026-10-04_consolidated-development-plan/`; `HO/` = `prompts/thread-handoff_automated-prompts/`; "the gate" = `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py` (the pre-push scan); "the read" = `util/ad-hoc/2026-10-05_masked_finding_shape.py`.

## Where the work is (read first)

- **81 untracked files**: the plan PR's 74 (`S/main/prfiles-v112.txt` lists them), the three round-13 lane reports, their three mutant files (`EX/round13-mutants-*.json`), and this handoff. All but this handoff exist ONLY in this worktree. The plan PR's path list must add the six round-13 files and, after reconciliation, `round13-reconciliation.md`.
  - The copies in `.claude/worktrees/unified-orbiting-fountain` are stale (round-11 state); never use them. Land the plan PR early: a sweep or a mistaken cleanup loses months of work.
- **Scratchpads are tmpfs** (`/tmp`), so a reboot empties them:
  - this session's, `S/` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/3e8595eb-854b-456a-98d4-2816eb0364d4/scratchpad/`, holds `main/plan_v1.11.0.md` and `plan_v1.12.0.md`, the `plan_v1.11_to_v1.12.diff`, the frozen tool copies with their round-11 diffs, `pushcheck-v112/files/`, `wd/` (the verified scanner tarball), `round13/brief-*.md` and `round13/<lane>/`;
  - the earlier session's, `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/1d83ae70-977d-4a39-adf3-7be0d97b8a27/scratchpad/`, holds `round6/a1/cases/FP40/` (40 real backup files: read them only through the gate and the masked read), `v6/fp40-v6-keys.sorted`, `main/pr_body_v112.md`, `main/commit_body_v112.md` and `main/banners-draft.md`.
  - If either is gone: the plan file in the worktree IS v1.12.0 (sha256 below), the tools are in `util/ad-hoc/`, the gate re-downloads its pinned scanner, and FP40 cannot be recovered, so skip that check and say so. Rebuild the PR drafts from round 12's reconciliation and the plan's Validation record.

## Completed so far

- **Round 12 reconciled → v1.12.0**, frozen 2026-10-08T22:56Z, sha256 `d7d07c3f8931b2122c6300a5c9f259055ee3f31607a3d15358bb81613b319b25`. All 45 findings were accepted (R12B1-05 in part), and every MAJOR was re-derived first. The predecessor handoff's "43 findings" was a miscount.
- **`reports/2026-10-04_consolidated-development-plan/round12-reconciliation.md`** (sha256 `0631d4d8…`), modelled on round 11's, records R12A-11's and R12A-12's corrections to round 11's record.
- **The line read was redesigned:** it masks names too, prints KEY ranges as whole lines with an `offset=`, refuses by `lstat`, has widened openssl and `authorization` markers and counts hex keys and UUIDs. The read, the regression, the gate (docstring only) and the plan agree on it.
- **New instruments**:
  - `util/ad-hoc/2026-10-08_line_read_mutation_run.py`, the mutation harness, takes `--mutants`, `--out` and `--workdir`;
  - `util/ad-hoc/2026-10-08_build_round12_mutants.py` rebuilds `EX/round12-mutants.json` (57 entries) byte for byte;
  - `util/ad-hoc/2026-10-08_pr_printed_line_screen.py` screens the read's printed lines.
- **Frozen tool hashes** (sha256 prefix): gate `4e2158c8b6fc15e8`, regression `e2814ee7be5f5ccc`, read `f0fbf134da7f3a5b`, census `275cc45d55a81fb4`, harness `31451d79ebce51a8`, mutants `6189cc197f1a2806`.
- **Measured on those tools**: the regression passes 181 of 181; the mutation run catches 57 of 57 (Lane A reproduced it in about 3 minutes); FP40 gives 49 keys, identical to v6's; probe mode gives 32/3/31/0. This PR's 74 files gate exit 0 with the one accepted key `reports/2026-10-04_consolidated-development-plan/round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`. `--names` gives 309/160/957; `--all` counts 1,085 tokens, all classified.
- **Round 13 ran on v1.12.0** (2026-10-08, 22:57Z–23:40Z). Its reports are written but **not yet archive-headed**:

| Report | BLOCKER | MAJOR | MINOR | NIT |
| --- | --- | --- | --- | --- |
| `round13-laneA-reprobe.md` | 0 | 4 | 2 | 7 |
| `round13-laneB1-safety.md` | 1 | 9 | 6 | 1 |
| `round13-laneB2-schedule.md` | 0 | 3 | 7 | 6 |

  That is 46 findings, 1 BLOCKER and 16 MAJORs, so the ending rule does not end validation. None is re-derived yet.

## Open questions for the owner (ask before step 3)

1. **Re-baseline or land as a record?** Since round 13's freeze, much of the plan's own Wave 0/1 has happened outside it (drift below). Recommendation: land the plan as v1.13.0 with the drift taken in, and run one narrow round 14. Alternatively, land it now as the validated v1.12.0 record, with round 13 archived unreconciled and a v2 re-plan opened.
2. **Release order.** observability 0.4.1 and service-core 0.7.1 (R-OBS-SC) shipped before P3-07 was validated, which §9's R-OBS-SC row says "ships F2's leak and F10's false sentence"; data 0.17.0 (R-DATA) shipped against §5's gates of P3-03 and P3-09. Whether a fix-forward release is owed is the owner's ruling, not the plan's.
3. **H-23 after ml#2199.** Phase B merged with retention SUSPENDED through recovery, to be restored as `2W:1D,6M:1W,2Y:1M,5Y:2M` only after AC-4's first drill (owner ruling); it has not been restored yet. H-23, S0.3's two-line `docs/REFERENCE.md` PR, the fold-in items and A2's DEFECT-1 ask are probably obsolete or changed. Re-derive from ml#2199 and `HO/HANDOFF_*` of ml#2201 before editing them.
4. **Ending rule.** Rounds 10–13 each found MAJORs in the read's pins (mutants). If round 14 again finds only read-pin MAJORs, the owner may accept the plan with them recorded as listed limits.

## Remaining work (in order)

1. **Verify the start** (commands below). Ask question 1 first; its answer sets steps 3–6.
2. **Take in the drift** since 2026-10-08T22:16Z. Re-run the census with `--since 2026-10-08T22:16:00Z`; at 10:45Z on 2026-10-10 it showed:
   - **ml#2199** (Phase B merged, the STOP cleared, retention suspended) and **ml#2201** (its handoff);
   - **releases**: ml#2186, ml#2188, ml#2189, ml#2193 and data#477/ml#2191, with juniper-observability 0.4.1, juniper-service-core 0.7.1 and juniper-data 0.17.0 now on PyPI (R-OBS-SC and R-DATA, cut outside the plan);
   - **deploy#243 merged** (the data 0.17.0 pin, W1.11);
   - **ml#2187** (four flood-3 defects fixed, the cleanup tool's empty lost-commit list among them: XC-CLEAN and S0.6 change), plus cascor and data `FailedAuthThrottle` fixes and seven "Sequence Safety is required" docs PRs;
   - **ml#2194** merged and **ml#2206** open, the flood-3 record's follow-ups (the latter's title: "secrets in all seven repos");
   - **ml#2203 open**, "gitleaks loaded zero rules; add the backup-credential…": XC-LEAKS step 3, done by another session out of the plan's order. The plan puts step 3 after step 1's history scans and step 2's owner rotation of every hit, because a history rescan in CI publishes each hit's file, line and URL; ml#2203 also pins gitleaks 8.24.3 where step 3 asks for 8.30.1. Read it, record the conflict for the owner, and do not duplicate it;
   - **ml#2195**, the W1.5 driver half; **ml#2196**, canopy#731's pacer evidence;
   - **ml#2197/2198**, the equities plan v1.5.x;
   - **canopy#731** (F-055/058/068) and canopy's recurrence fit fixes;
   - **ml#2190 open**, the `[servers]` floor; **deploy#245 open**, a canopy→recurrence→data smoke test;
   - **ml#2204** merged, ci-tools 0.9.1, with its GitHub Release; **ml#2205** (its release notes) and **ml#2206** (a flood-3 record status) open; ml#2192/#2202, docs.
   - Rewrite the affected rows (§2, Wave 0/1, §5, §6, §9, H-22, H-23, XC-LEAKS, XC-FLEET, XC-CLEAN, the risk table and Appendix A) from their sources, not from this list.
3. **Reconcile round 13.** Archive-head the three reports with `util/ad-hoc/2026-10-05_archive_report_headers.py`. Re-derive the BLOCKER and every MAJOR before accepting. Their substance:
   - **R13B1-01 BLOCKER (conditional on F-S10's key condition), with R13B2-01:** H-22's lift is keyed to the running service, not to when text was written. The lanes' remedies differ:
     - R13B1-01 keeps earlier records banned until the key is rotated, since the gate catches only the three refusal texts;
     - R13B2-01 allows publishing them after the gate, `--names` and `--all`.
     - Recommendation: R13B1-01's, as the stricter.
   - **R13B2-02:** canopy's own data-client relay (`src/demo_mode.py` at v0.8.1) is missing; canopy closes it only with #683/#685's outbound-key screen.
   - **R13B2-03:** XC-CRED's search is assigned to S0.11's actor, but S0.11 waits for A1 (sitting item 8). Fix: make it its own Wave 0 item.
   - **R13B1-02:** row q still names `unified-orbiting-fountain`.
   - **The read's own leaks**, all MAJOR under clause 3:
     - `len=` and `offset=` print a value-dependent count (R13B1-04);
     - `names=` reveals credential words inside a value (R13B1-09);
     - a malformed KEY is echoed in clear (R13B1-10).
   - **R13B1-08:** names the gate reads that `--names` does not list (`__API_KEY__:`, a bare `_TOKEN=`).
   - **17 mutants that survive both checks**: Lane A's 7 (R13A-01..04) and Lane B1's 10 (R13B1-03..07). Among them:
     - `-passin`/`-passout` unpinned; bare `TOKEN`/`PASSWORD`/`SECRET`;
     - `..` and outside-root KEY paths; a line-0 KEY; a symlinked root in KEY mode;
     - "each line once"; refusals not naming the file; NUL-refusal bytes and stderr.
     - Their replacements are in `EX/round13-mutants-laneA.json` (7 entries) and `EX/round13-mutants-laneB1.json` plus `-2.json` (9 + 3; these include one empty entry and one already-caught M2, so 19 entries give 17 survivors).
     - Merge them into `EX/round13-mutants.json` and dedupe by built text: R13A-05 found that round 12's 57 entries build only 53 distinct reads, so correct the plan's "23" and "57".
     - Make the harness report the entries it drops (R13B1-12), fix the read, add one contract case per survivor, and require every mutant caught.
   - Then the MINORs and NITs as each lane proposes them, in the plan as v1.13.0. Write `round13-reconciliation.md`. Re-run the regression, the mutation run, FP40, probe mode, ID coverage, markdownlint, the structure check and the ≤512-character line check, and **copy the push snapshots only after the last edit** (R13A-07 is the fourth time a copy predated an edit).
4. **Round 14, token-lean.** Keep it narrow: round 13's corrections and the drift only. One Lane A (re-derive) plus one Lane B (attack the read's new pins and H-22/H-23), unless the drift rewrite is large. Reuse `S/round13/brief-common.md` with updated paths, hashes and severity, and give each lane a hard sample size (about 80 claims) instead of "at least". With no BLOCKER and no MAJOR, apply its MINORs and NITs and stop; otherwise ask the owner (question 4).
5. **The plan PR**:
   - Fill the drafts. Give CONSUMED banners to the round-7 handoff (draft text), the round-10 and round-12 handoffs, and refresh the round-2 one.
   - Gate every file, the commit message, the PR body and the path list, with the accepted key, and run `--names` and `--all`.
   - Run `/opt/miniforge3/bin/pre-commit run --files <all>` and `tests/test_thread_handoff_archive.py`.
   - Then `util/open_signed_pr.py`, `util/wait_for_checks.py` and `util/safe_merge.py`, the last only with the owner's fresh approval.
   - Do not re-add this handoff once its own docs PR has merged: check `git show origin/main:HO/<this file>` first. `tests/test_thread_handoff_archive.py` passes at `81d3fbb3` with every untracked file present; re-run it on the PR's tree.

## Key context

- **Hard limits**:
  - never run backup tooling, Duplicati, `systemctl` or service restarts, and never touch ports 8100/8101/8050/8051/8201/8202;
  - never print secrets or environment output;
  - read real-file findings only through the masked read;
  - H-22 forbids pasting service bodies, logs or run records;
  - lane briefs forbid all of the above and every external send, and require slips.
- **The command guard** refuses: loops; `$(…)`; unquoted variables; any command whose text pairs the scanner's tool name or `git show` with variables or heredocs; awk programs; and `git -C` into other worktrees. Use literal paths and separate commands, or the file tool for edits.
- **Script placement**: any script that produces or analyses repository content goes in `util/ad-hoc/`, never `/tmp` (this session moved two there).
- **The regression's names check catches no mutant**: all pinning is in `contract_check`.

## Verify the starting state

- `git status --porcelain=v1 --untracked-files=all | wc -l` gives 81 (80 plus this handoff; 80 once the worktree's HEAD holds the merged handoff), nothing staged; then `git fetch origin main`.
- `sha256sum notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md util/ad-hoc/2026-10-05_masked_finding_shape.py util/ad-hoc/2026-10-05_gate_regression.py` gives `d7d07c3f…`, `f0fbf134…` and `e2814ee7…`.
- `python3 -B util/ad-hoc/2026-10-05_ecosystem_live_census.py --since 2026-10-10T10:45:00Z` gives the drift after this handoff.
