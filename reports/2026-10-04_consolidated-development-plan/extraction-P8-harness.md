# Extraction — P8 dynamic-workflow harness design

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:54:15Z – 21:02:07Z (UTC). Worktree `unified-orbiting-fountain` at `cf711cf4` = `origin/main` (REST `commits/main` → `cf711cf4`, 2026-10-04T19:36:58Z).

Short names used below: **HANDOFF** = `HANDOFF_2026-10-03_dynamic-workflow-harness-consolidated.md`; **PRED** = `HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md`; **DESIGN** = `notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md`; **R1** / **R2** = `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-{1,2}-RECORD.md`; **V3** = `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`; **CON** = `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

## 0. Sources read

| File | Read |
|---|---|
| HANDOFF (`prompts/thread-handoff_automated-prompts/`) | full, l.1–224 |
| `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` | full |
| PRED | full |
| DESIGN (v3) | l.1–70, 172–355, 417–486, 540–758 (header, §0–§1, §3–§5, §6.1, §6.3–§7.4, §9–§13, App. A–E). §2, the §6.2 script and §8 were read only through grep hits |
| R1 | l.1–72 (both reconciliations, composition); report headings only |
| R2 | full (header only; no reports) |
| `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md` | diff against the worktree copy only |
| V3 | l.6–12, 1031–1066 (Status, §10 open questions) |
| CON | headings; §4 |
| `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` | APD-ML-005 row :1295; park notes :1310–1322, :1428–1432 |
| `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` | Status line |
| `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` | V3 references only (a table repair, not ratification) |
| P9 / P10 consolidated handoffs | grep for overlap only |
| `util/push_signed_commit.py` :1–60; `util/open_signed_pr.py` (grep, :83–84, :274–278); `scripts/claude_interactive.bash` :17, :84 | as listed |
| memory `project_dynamic_workflow_harness_design_2026-09-23.md`; `MEMORY.md` l.2 | full; one line |
| **Not read**: SUITE, the HANDOFF procedure, SOAK §20, `…CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` | all exist on main (`ls`). They are inputs to round 2 and carry no open work |

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P8-01 | Run `git status --short` in `structured-inventing-fairy`, then retire its now-redundant copies or worktree per the cleanup procedure | HANDOFF l.9, item 5 | [VERIFIED 2026-10-04: `cmp` on all six files against main gives 4 identical. The other 2 differ only by the 3 link rewrites and the 1 trailing newline that HANDOFF l.3 describes. The worktree still exists] | STARTABLE (needs a session allowed to run git there) | — | juniper-ml | S | HYGIENE |
| P8-02 | Relaunch round 2: one Lane A agent (execute the corrections) and one Lane B agent (refute them), at most 3 agents, with the design frozen | HANDOFF item 1; DESIGN §12 | [VERIFIED 2026-10-04: R2 on main is header only, and only 901c9dfd (#2110) touched it. REST search finds no PR or issue after #2110. Of the 28 transcripts touched in the last 35 h, none launched harness lanes] | WAIT-QUIET-WINDOW | P8-03; every path (usage windows) | juniper-ml | M | UNBLOCKER |
| P8-03 | Before launch, add three post-v3 facts to the round-2 briefs: `push_signed_commit.py` (#2036), CLI 2.1.289, and the shipped pilot task | live probe (§5 rows 2, 4, 5) | [VERIFIED 2026-10-04: see §5] | STARTABLE | — | juniper-ml | S | UNBLOCKER |
| P8-04 | Archive both reports with `2026-09-23_archive_subagent_reports.py`, finding the slug with `ls -d ~/.claude/projects/*/<sid>`; write the CON §5 Reconciliation | HANDOFF item 2 | [VERIFIED 2026-10-04: the archiver is on main and byte-identical to the worktree copy. Not started] | BLOCKED-ON P8-02 | P8-02 | juniper-ml | M | UNBLOCKER |
| P8-05 | Fold v4 in one pass: Appendix F, header Version/Status, §0 table, a round-2 row in §12 and the CON §7 minimum record; fix §5 rows 7–8; update R2's date and freeze line | HANDOFF item 2; DESIGN §12 l.614 | [VERIFIED 2026-10-04: the header still reads "v3 … round 2 on the corrections pending"] | BLOCKED-ON P8-04 | P8-04 | juniper-ml | M | UNBLOCKER |
| P8-06 | Run round 3 only if round 2 changed a number, a disposition or an action | HANDOFF item 2; CON §4 | [NOT RE-PROBED — conditional] | BLOCKED-ON P8-05 | P8-05 | juniper-ml | M | RESEARCH |
| P8-07 | Run the gates: structure check on the 4 notes and HANDOFF; links; even fence count; recreate the §6.2 `node --check` wrapper under `util/ad-hoc/`; `juniper-check-doc-links … --cross-repo skip` | HANDOFF item 3 | [VERIFIED 2026-10-04: node v24.13.1, jq 1.8.1, the `juniper-check-doc-links` binary and `util/ad-hoc/2026-09-05_markdown_structure_check.py` are all present] | BLOCKED-ON P8-05 | P8-05 | juniper-ml | S | UNBLOCKER |
| P8-08 | Open the v4 **update** PR via `open_signed_pr.py` on `design/dynamic-workflow-harness`. The body names every document, puts D-1..D-12 as the ask, and states that no JR id applies. Do not merge | HANDOFF item 4 | [VERIFIED 2026-10-04: the branch is absent on origin (REST 404) and locally. Still true: existing branch refused (:276), DUP-GUARD at :175/:251, base read at :83–84] | BLOCKED-ON P8-07; the merge is OWNER-ACTION | P8-07 | juniper-ml | S | UNBLOCKER |
| P8-09 | Rewrite the memory file and `MEMORY.md` l.2: v3 is on main (#2110) with D-1..D-12; add the v4 PR number later | HANDOFF item 5 | [CHANGED SINCE HANDOFF: staler. It still says "v2", "UNTRACKED in worktree" and "D-1..D-10", but the files have been tracked since #2110] | STARTABLE (the correction now; the PR number after P8-08) | all paths: `MEMORY.md` is over budget, so re-read it before writing | `~/.claude` | S | HYGIENE |
| P8-10 | Verify that R1's five reports are verbatim against the predecessor's transcripts before those expire (~2026-10-22) | HANDOFF l.36, l.49 | [VERIFIED 2026-10-04: 12 subagent transcripts sit under the main-repo slug `…/bb39e9fe-…/subagents/` (5 dated 09-22, 7 dated 09-23). `cleanupPeriodDays` is unset, so the 30-day default applies] | STARTABLE (deadline ~10-22) | — | juniper-ml | S | DATA-INTEGRITY |
| P8-11 | Get the owner's rulings on D-1..D-12 and record them in DESIGN §10.1 ("to be added") with the chosen and rejected options | HANDOFF item 6; DESIGN §10 | [VERIFIED 2026-10-04: §10 is unchanged and there is no §10.1] | OWNER-DECISION | P8-08 (the ask) | juniper-ml | S | UNBLOCKER |
| P8-12 | Get the owner's ratification of the seed re-scopings "agents" (R6) and "reassigned" (R8); "met" is already inside D-5 | DESIGN §1.2; R1 l.46 | [VERIFIED 2026-10-04: no D-row names R6 or R8] | OWNER-DECISION | P8-08 | juniper-ml | S | UNBLOCKER |
| P8-13 | Re-pick D-9's pilot set. DP-CASCOR-001/T1 (logging P0.4) has already shipped; DP-ECOSYSTEM-001/T1 (APD-ML-005) "needs [a ruling] before code" | DESIGN §4.1–§4.2, D-9 | [CHANGED SINCE HANDOFF: cascor#680 (P0.4) merged 2026-09-23T06:46:30Z. APD-ML-005 is still open (register :1295, :1430)] | OWNER-DECISION, plus a v4 text fix | P7 and P3 paths | juniper-ml | S | UNBLOCKER |
| P8-14 | Build roadmap P0: `statusline_usage_writer.bash`, `usage_state.py`, `calibrate.py`, `heartbeat.bash`, `install_agents.bash --install-statusline` and 2 tests | DESIGN §11 P0; §0 exemption | [VERIFIED 2026-10-04: none exists. `util/dispatch/` is absent; the installer has 0 hits for `--install-statusline`; there is no `statusLine` in `~/.claude/settings.json`; `~/.claude/juniper-dispatch/` is absent] | STARTABLE per DESIGN §0. Installing the user status line and running calibration bursts is OWNER-ACTION | best after P8-02, because Lane B items 2 and 8 attack §5.1 and §5.3 | juniper-ml, `~/.claude` | M | RESEARCH |
| P8-15 | Rule D-10 (go/no-go) from `k_7d`, at least 3 weekly windows of `u_7d`, and `c_M` | DESIGN §10 D-10 | [VERIFIED 2026-10-04: no inputs exist because P0 is unbuilt] | OWNER-DECISION | P8-14 plus at least 3 weeks elapsed | — | S | UNBLOCKER |
| P8-16 | Roadmap P1: the three `conf/` files, `design_path_ledger.py reconcile [--check]`, and its test | DESIGN §11 | [VERIFIED 2026-10-04: `conf/design_paths.yaml` and `conf/dispatch.yaml` are absent] | BLOCKED-ON P8-02, P8-11 (D-3, D-9), P8-13 | — | juniper-ml | M | UNBLOCKER |
| P8-17 | Roadmap P2: `dispatch_tick.py`, `apply_report.py`, three schemas, and tick tests | DESIGN §11 | [VERIFIED 2026-10-04: unbuilt] | BLOCKED-ON P8-14, P8-16, D-5 | — | juniper-ml | L | UNBLOCKER |
| P8-18 | Roadmap P3: the `juniper-cycle.js` docs pilot, `--append`, `secret_screen.py`, and the script test | DESIGN §11 | [VERIFIED 2026-10-04: `.claude/workflows/` is absent and `--append` is absent. But see §5 row 5] | BLOCKED-ON P8-17 | — | juniper-ml | M | USER-FACING (owner tooling) |
| P8-19 | Roadmap P4: `dispatch-executor`, the Execute stage, `--expect-base` and `--reuse`, the manifest test, and a sandbox task | DESIGN §11 | [VERIFIED 2026-10-04: both flags are absent] | BLOCKED-ON P8-18, P8-15 | — | juniper-ml (and task repos) | L | USER-FACING |
| P8-20 | Roadmap P5: the Verify stage (`lensesFor`, `VERIFY_PENDING`, retries) | DESIGN §11 | [NOT RE-PROBED — unbuilt by construction] | BLOCKED-ON P8-19 | — | juniper-ml | M | USER-FACING |
| P8-21 | Roadmap P6: `reap_worktrees.py --dry-run` covering V3 G1–G5, B1, B4, the veto, the manifest gate and the patch-id test, with tmp-repo tests | DESIGN §11 | [NOT RE-PROBED — unbuilt] | BLOCKED-ON P8-19, D-4, D-12 | P8-25 | juniper-ml | M | SAFETY |
| P8-22 | Roadmap P7: systemd units (`SuccessExitStatus=3`), the standby child, the owner message and its delivery, and heartbeat scheduling; then a dry week | DESIGN §11 | [NOT RE-PROBED — unbuilt] | BLOCKED-ON P8-17..P8-20, D-1, D-6 | — | juniper-ml, host | M | USER-FACING |
| P8-23 | Roadmap P8: measured medians, the `predict_merge` screen, and a retention cap for `~/.claude/juniper-dispatch/` | DESIGN §11 | [NOT RE-PROBED] | BLOCKED-ON P8-22 (20 cycles) | — | juniper-ml | S | RESEARCH |
| P8-24 | Roadmap P9: `reap_worktrees.py --execute` | DESIGN §11 | [NOT RE-PROBED] | BLOCKED-ON P8-25, D-4 | — | juniper-ml | S | SAFETY |
| P8-25 | Ratify V3 as amended (D-12's patch-id B3), including V3 §10 Q3–Q8 | DESIGN §0, §7.3, §13; V3 §10 | [VERIFIED 2026-10-04: V3's Status is "DESIGN, revision 2" with "Supersedes (on ratification)"; Q3–Q8 are all OPEN; no consolidated path carries it] | OWNER-DECISION | P8-02 (Lane A item 3 tests the amendment) | juniper-ml | M | SAFETY |
| P8-26 | Decide whether to delete the seed branch `design/dynamic-workflow` (`27ea09a1`) after the design merges | HANDOFF item 4 (PR body) | [VERIFIED 2026-10-04: it exists on origin (REST) and locally at `27ea09a1`] | OWNER-ACTION | P8-08 | juniper-ml | S | HYGIENE |
| P8-27 | Resolve, or record in §12, the R1 residuals the round-2 briefs omit: the cost of calibration bursts and whether 5 per window suffice; the compare-endpoint cost of `--expect-base` | R1 l.30, l.50 | [NOT RE-PROBED — research] | Record in P8-05; measure in P8-14 / P8-19 | — | juniper-ml | S | RESEARCH |

## 2. Owner decisions pending

| ID | Question | Options; source recommendation | Blocks | Source |
|---|---|---|---|---|
| D-1 | Controller surface | (a) interactive `/loop` (v2) vs (b) a systemd timer plus a `-p` child (v3). **Recommends (b)**, with `--dangerously-skip-permissions`, teams off and `ultracode` off. This loses the `/workflows` live view | P8-22 | DESIGN §10 |
| D-2 | Worktrees under `Juniper/worktrees/`, acknowledging that native `isolation: worktree` puts trees inside the repo | **As specified** | P8-19 | same |
| D-3 | Ledger shape (three `conf/` files) | **As specified** | P8-16 | same |
| D-4 | Removal dry-run only until V3 as amended is ratified | **Dry-run only now** | P8-21, P8-24 | same |
| D-5 | `reserve` 10/15, `slack` 5/5, `dispatch_windows`; "met" means the binding window reaches its target | **Defaults; windows = the owner's sleeping hours** | P8-17 | same |
| D-6 | Decision delivery: cycle record, cross-session message, push | **All three** | P8-22 | same |
| D-7 | Retired | — | — | same |
| D-8 | Call-time `effort` overrides vs relaxing the six frontmatter pins | **Call-time only for the pilot** | P8-18 onward | same |
| D-9 | Pilot goal set | **The two §4.1 entries**. This is now STALE (see P8-13) | P8-16 | same |
| D-10 | Go/no-go after measurement | **Measure first**; below about one M task per day, stop at P0–P3 | P8-19..P8-23 | same |
| D-11 | Allow `/template-agent` (`disable-model-invocation: true`) to be invoked from an unattended agent | **Allow for the dispatcher only** | P8-18 | same |
| D-12 | Amend V3's B3 to the patch-id landed test | **Amend** | P8-21, P8-24 | same |
| RS-1 | Ratify the R6 "agents" re-scoping: only editing agents get worktrees, and a blocked task's redo reuses its tree | As written in §1.2 | P8-19 | DESIGN §1.2; R1 l.46 |
| RS-2 | Ratify the R8 "reassigned" re-scoping: freed cost goes to a standby task in the same cycle | As written | P8-18, P8-22 | same |
| V3-Q3..Q8 | V3's own questions: delete or rename `remove_stale_worktrees.bash`; backup filters; commit `reports/soak/runs/` (Q5, which V3 calls "the question that actually matters"); a restore drill; peer sweeps; ecosystem scope | No single recommendation; §7.2 argues for owner-plus-veto (Q6) | P8-25, then P8-24 | V3 §10 |
| B-1 | Delete the seed branch after merge | "owner's call" | — | HANDOFF item 4 |

## 3. Cross-path dependencies

- **P8-02 / P8-06 → all paths (soft, usage windows).** At 20:33Z today, session `652c1204` (P1 backup) was running "Lane A/B/C" rounds. This planning fan-out of 10 agents is running now. According to the INDEX, rounds are also pending in P2 (Y2 wave 2, round 15), P3 (owed validations), P7 (round-2 reconciliation) and P9 (round-6 follow-up).
- **P8-13 ↔ P7 (logging).** Pilot task T1 targets P7's roadmap. P0.4 has shipped (cascor#680), and P7's next step is P2.1. Any re-picked pilot on P7 must be coordinated with that path.
- **P8-13 ↔ P3 (register) and P6 (perf lane).** Pilot task DP-ECOSYSTEM-001/T1 is APD-ML-005. That row lives in P3's register and concerns `util/experiments/`, which is P6's quiet-window zone. The register says no row may be actioned without asking the owner.
- **P8-18 / P8-19 ↔ P9 / P10.** Both of those handoffs cite `util/push_signed_commit.py` (ml#2036) as the signed-append tool, while P8 plans new modes for `open_signed_pr.py`. There is no conflict today. [VERIFIED 2026-10-04: since `25b78f55`, no commit touched `open_signed_pr.py`, the worktree-cleanup scripts, `install_agents.bash`, V3, `claude_interactive.bash` or `task-executor.md`, and none of the 8 open juniper-ml PRs (#2119–#2129) touches them or the harness notes.]
- **P8-21 / P8-24 / D-12 → V3 ratification (P8-25)**, which no path carries. V3's Q4 and Q8 (Duplicati filters, restore drill) overlap with P1 (backup).
- **P8-09 ↔ all paths**: every path edits the over-budget `MEMORY.md`.
- P8 blocks no other path.

## 4. Hazards

- **The six squash-merged branches are Lane A's §7.3 fixtures.** All are present [VERIFIED 2026-10-04: `git branch --list`, plus REST merge commits `e075f440`, `dccd564b`, `4afaf5e6`, `5194a925`, `afcd8498`, `94e24934`, all matching]. `arc/canopy-e2e-phase1-seg10` is checked out in worktree `eager-rolling-sun`. A branch prune, or a cleanup of that worktree, before round 2 destroys the evidence.
- **`structured-inventing-fairy` is no longer a sole copy, but `git status` has never been run there.** `git worktree remove` deletes ignored files. Never run `util/remove_stale_worktrees.bash`. `.claude/worktrees/` is hidden from sweeps that start at the repo root.
- **The account is limit-bound.** Run at most 3 agents at once. After a 429, `SendMessage` the same agent ids within the same session; a new session cannot resume them.
- **Freeze the design while lanes run, and fold all findings in one pass.**
- **Signed commits go only through the API.** `open_signed_pr.py` refuses an existing branch; `push_signed_commit.py` needs the full 40-hex `--expected-head`. Whole-file uploads from a stale base clobber other work.
- **The isolation shim refuses variable-built `find` and `gh` commands and loops** [VERIFIED 2026-10-04: two refusals in this session]. Put such commands in a scratch script.
- **P0 writes a user-level `statusLine` and `subagentPromptCacheTtl` into `~/.claude/settings.json`, which affects every session.** Never put `autoContinueAtUsageLimit` in project settings, because there it turns auto-continue off [VERIFIED 2026-10-04: neither key is in user settings, and no project `settings.json` exists].
- **The stale memory line ("v2 UNTRACKED") misdirects any session that reads it.**

## 5. Discrepancies

1. `origin/docs/handoff-dynamic-workflow-harness-round-2` (#2090's head): HANDOFF says "at `5085cfba`". [CHANGED: REST returns 404; the branch is deleted.] Harmless.
2. Claude Code version: HANDOFF says 2.1.288 (the design was measured at 2.1.280). [CHANGED: `claude --version` → 2.1.289.] Lane B items 1, 2 and 9 must be answered against 2.1.289.
3. Commits on `main` since `25b78f55`: HANDOFF says 74. [CHANGED: 87.]
4. **D-9 pilot task DP-CASCOR-001/T1 ("P0.4 … produce and validate the implementation prompt") is already done.** [CHANGED: cascor#680, titled "enforce the log-record envelope and named-marker contract in cascor CI (P0.4)", merged 2026-09-23T06:46:30Z, about 22 min after v3's last save at 06:24Z.] The ledger example's `handoff:` field also points to a 09-22 logging handoff that has since been superseded. Neither HANDOFF nor PRED notices this.
5. **`util/push_signed_commit.py` already does what P3 plans to build.** It landed via ml#2036, merged 2026-09-23T06:21:06Z, 3 min before v3's last save. It adds a signed commit to an existing branch, pinned by `--expected-head`. DESIGN §6.5 assigns that same capability to a new `open_signed_pr.py --append` (P3), but mentions `push_signed_commit.py` 0 times. The round-2 briefs do not name it either. HANDOFF item 4 suggests "e.g. a GraphQL `createCommitOnBranch` commit", as if no such tool existed.
6. The memory file: HANDOFF called it stale ("v2 … D-1..D-10"). [CHANGED: further stale. It still calls the files untracked, but they have been tracked on main since #2110.]
7. DESIGN §11's heading says "P0, P1 and P3 can run in parallel now". This contradicts its own P3 row ("Depends on P2") and §0 ("no step … except … P0 may start before round 2 reports"). Lane B item 10 checks Appendix E row 19, which records this claim.
8. DESIGN §12 lists the unresolved dissent as "Appendix E rows marked 'recorded'", but no Appendix E row is so marked. The "recorded" items are in R1 l.46–47, and Appendix D row 25 reads "dissent overturned".
9. HANDOFF's verification commands now return post-#2110 values. `grep -c DYNAMIC-WORKFLOW-HARNESS` returns 4, not the stated 0, and the PR search returns #2090 and #2110. This is expected, not an error.

## 6. Residue (open items that HANDOFF does not carry)

- The R6 "agents" and R8 "reassigned" re-scopings, which R1 l.46 "recorded … for the owner to ratify by name". They have no D-row → P8-12.
- P0 is exempt from the round-2 gate (DESIGN §0, §11) and can start now. HANDOFF mentions it only inside D-10 → P8-14.
- Roadmap steps P1–P9 are carried only by reference → P8-16..P8-24.
- V3's ratification and its §10 Q3–Q8 → P8-25.
- R1's residual uncertainties that the round-2 briefs omit (R1 l.30, l.50): the calibration-burst cost, the compare-endpoint cost, and the `WorktreeCreate`-hook identity check. The last is possibly moot, because v3 drops `isolation` → P8-27.
- R2's header lines "Date: 2026-09-23" and "Subject frozen at: design v3 … 06:4xZ" must be updated at the relaunch → P8-05.
- DESIGN §10.1 Rulings ("to be added") → P8-11.

## 7. Path assessment

- **Urgency: low.** The sole-copy risk is closed [VERIFIED 2026-10-04: #2110 merged 2026-10-03T10:00:27Z, and `cmp` shows main identical apart from the two declared lint fixes]. Two things are time-bound: P8-10 (the transcripts expire around 10-22), and D-10's lead time of at least 3 weekly windows, which only starts once P0 is installed.
- **Leverage**: potentially high, since the design is limit-paced automated dispatch for every path, but conditional on D-10. Near-term leverage is low: no path waits on P8.
- **Cost**: round 2 is 2 agents in a quiet window, so usage is the binding cost. The v4 fold is M. P0 is M plus at least 3 weeks of elapsed time. P1–P9 are several L-sized PRs, and only worth building if D-10 says go.

**Recommended next actions**, in order:

1. **P8-03, then P8-02**: amend the briefs and launch round 2 once this planning fan-out has finished and no other path is mid-round.
2. **P8-04 → P8-05 → P8-07 → P8-08**: archive, reconcile, fold v4 (including the stale pilot and §5 rows 4, 5, 7 and 8), run the gates, and open the v4 PR. That PR asks for D-1..D-12 and RS-1/RS-2.
3. **Owner (P8-14 / P8-15)**: decide whether P0 starts as soon as round 2 reports, since D-10 cannot be ruled until P0 has collected at least 3 weekly windows of data.

The cheap side items can run at any time: P8-10 (before ~10-22), P8-09 and P8-01.

## 8. What this report cannot support

- Any technical claim in DESIGN §2, §5, §6.2 or §8. These were not re-derived; that is round 2's job.
- The current usage headroom. There is no status line. Transcripts touched in the last 72 h contain no synthetic `quotaLimits` record, but that cannot prove "no hit" (DESIGN §5.2).
- Whether `structured-inventing-fairy` holds untracked work beyond the 8 files HANDOFF lists. Running git there was not permitted, and the mtime test did not discriminate.
- Whether the six evidence branches are absent from origin. Only their local presence was checked.
- Whether R1's reports are verbatim.
- D-8's "six CI tests". A loose grep finds 8 files; the 2 I inspected only use those names as fixtures or launcher aliases. That is consistent with six but does not prove it.
- Whether another session will start a consensus round in the next few hours.
