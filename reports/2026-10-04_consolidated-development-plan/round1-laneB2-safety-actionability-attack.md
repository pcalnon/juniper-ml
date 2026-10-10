# Round 1 — Lane B2 (actionability, authority and safety attack)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-1 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round1-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- **Instrument**:
  - **Read**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` in full (sha256 `05d7a571d00e617d`, re-verified after writing), plus §4 of all ten `EX/extraction-*.md`.
  - **Re-checked live**:
    - GitHub REST: visibility, rulesets, #2129 and #2130;
    - triggers, `.gitattributes` and five `.gitleaks.toml` files;
    - gitleaks' README;
    - the scripts and the `…RECOVERY-PLAN.md` / `…fold-in-pending.md` lines cited below;
    - the memory files, read-only.
  - **Scans**: count-only greps on rows a, i and j, with no values printed.
  - **Executed**: nothing but reads.
- **Entry point**: the plan's instructions as a successor would execute them, Wave 0 first.

Aliases (filename fragments):

- `…RECOVERY-PLAN.md` = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
- `…fold-in-pending.md` = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md`
- `EX/` = `reports/2026-10-04_consolidated-development-plan/`

Every § in the Location column belongs to the plan.

## Findings

| ID | Severity | Plan location | Instruction / claim | How a successor is misled or harm results (evidence) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| B2-01 | **BLOCKER** | §3 XC-PRESERVE "How" | "secret-scan it (gitleaks) and push it to a `wip/preserve-…` branch" | juniper-ml, juniper-data and juniper-canopy are **public** (REST), so the push publishes, irreversibly. Its only gate does not work: gitleaks is not on PATH (`…RECOVERY-PLAN.md` :84). The ml, data, canopy and deploy `.gitleaks.toml` files have no `[extend] useDefault` and no rules (cascor's has `useDefault` at :16–17). gitleaks' README says a custom config means "default rules do not apply", so the file's own usage line, or any repo-rooted scan, runs with no rules. Even the default rules lack B9's rule for `PASSPHRASE=` / `SETTINGS_ENCRYPTION_KEY=` (:135, :227), a class present in row a's A.md and C.md (3 matches; values unread). Row i is deliberately git-excluded Yahoo/SEC-derived data, with `/home/` paths in 20 of its files | No push for rows a, b, i or j without an owner ruling. If pushed, use a private repo or an age-encrypted archive. Scan outside the repo root with a config that extends the defaults and adds B9. The owner approves the file list. Transcripts never go to a repo |
| B2-02 | MAJOR | §3 XC-PRESERVE; §11 H-5 | "signed API commit and **no PR**" | No repo tool does this. `util/push_signed_commit.py:211` needs an EXISTING branch. `util/open_signed_pr.py` always runs a non-draft `gh pr create` (:291) and has no no-PR flag. For row a, an accidental PR *is* the Phase B PR: the sweeper arms it (H-1), and merging it lifts the owner's STOP (P1-10). Its stale whole-file `ci.yml`, `REFERENCE.md`, `AGENTS.md` and `CHANGELOG.md` would also revert `main` (`EX/extraction-P1-backup.md` §4 hazard 4) | Specify the mechanism: REST `POST git/refs` at a pinned base, then `createCommitOnBranch` with `expectedHeadOid` set to that 40-hex SHA. Forbid `open_signed_pr.py` here |
| B2-03 | MAJOR | §4 S0.1; §3 rows a, c–f | "One session works through rows a–j"; "Until every row is done" | (1) **Not executable.** Isolated sessions are refused git in other worktrees (`EX/extraction-P5-partition.md` P5-31; `EX/extraction-P8-harness.md` P8-01; this session too). Rows a and c–f need git. (2) **Wrong tool for row f.** An API commit gets a new SHA, which defeats O2. (3) **Vacuous completion.** Pushing `wip/backup-phase-a` saves only `6a1514e4`, not the 14+8 uncommitted files. "Branch exists" and a zero-rule scan both read clean | Assign each row to a session started in that worktree, or to the owner. Define "done" per row as a sha256 manifest matched against the preserved copy. Route row f through O2 |
| B2-04 | MAJOR | §4 S0.2 step 1 | "Finish or supersede #2129" | #2129 is open, a draft by `cursor[bot]`, with red CI and `behind` (REST). The sweeper un-drafts and arms PRs (H-1), and red CI is all that holds #2129. Finishing it in place turns it green before P1-03's validation lane runs, and the push races the bot on its own branch | Supersede only: validate on a new branch, open it, then ask the owner to close #2129. Rename to `*_MARKER`; never `# nosec` |
| B2-05 | MAJOR | §4 S0.7 | "Fix F-ML-002 … SAFETY, effort S", with no hazard stated | Testing a `--down` fix means running `--down`. With default env it kills 8051, 8211, 8202 and 8101, which includes the trio (`util/isolated_stack.bash:84–95`, `:500–508`). Stopping the trio is owner-reserved (O13; Out of Scope). It also deletes the primary checkout's `juniper-canopy/src/snapshots/snapshot_*.h5` (:78, :512). `EX/extraction-P2-canopy.md` §4 says so; the plan drops it | State the hazard. Set all four `JUNIPER_E2E_*_PORT` and `JUNIPER_E2E_RUN_DIR` to scratch values, and run `--dry-run` first |
| B2-06 | MAJOR | §11 (absent); S0.3; Wave 1 P3-05; §7.2 | — | `~/.bashrc:152` exports `SENTRY_SDK_DSN` into every session (names checked, values not printed). cascor `src/main.py:184` falls back to it. F4 is unfixed, and round 42 already sent test events to live Sentry (D-06). P3-08, the P3-05 lanes, PF-3, P7-17, P5-13 and P6-02 all inherit it. `EX/extraction-P3-defect-register.md` §4 says "set the six DSN variables to `""` (never unset)" | Add an H-14 with that rule, covering every service launch and suite run |
| B2-07 | MAJOR | §10 P1; Wave 0 ("mechanics are in its path handoff") | — | `…fold-in-pending.md:9`, the manual the plan sends P1 successors to, says "Merge approval for this arc's PRs was granted by the owner on 2026-10-03". §10 does not correct it. P1-03's "merge under that session's grant" invites reading that line as the grant | Add to §10 P1: line 9 does not carry; P1-03 and P1-10 each need an in-session grant |
| B2-08 | MAJOR | §6 A1 | "Merge grants for each path session that asks" | This asks the owner, in one sitting, for grants on behalf of future sessions. That is exactly the forward-carried approval that H-2 and XC-GRANT forbid. A recorded "A1: yes" becomes a citable blanket grant | Make A1 read "none: each session asks in its own first turn" |
| B2-09 | MAJOR | §3 XC-P12; Wave 2 P12; §7.2 | "Route three owner rulings to that session"; "Do not dispatch W0.1–W0.7 again"; "P12-08 → P12-09 (T4)" | (1) **Peer relay launders authority.** An agent message is never owner consent (H-2), and no session id or mechanism is given. (2) **Overtaken.** #2130 (opened 21:34:49Z, armed) reports W0.8 and W0.9 measured at 21:03Z, and the W0.3+W0.4 PRs are being opened. (3) **Mislabelled.** W0.1, which repairs the shared `JuniperCascor1`, is OWNER-ACTION (host) per `EX/extraction-P12-equities.md` P12-01, yet the plan lists it as dispatchable | The owner rules directly to that session or on its PRs. Add W0.8 and W0.9 to the do-not-dispatch list. Put W0.1's host change before the owner |
| B2-10 | MAJOR | §11 H-6 | "`util/juniper_chop_all.bash` (with `KILL_WORKERS=1`)" | The parenthetical narrows the ban. A default run "Stop[s] all Juniper microservices (host-level)" (script :2), and `EX/extraction-P6-perf.md` §4 says never run it at all | Drop the parenthetical |
| B2-11 | MINOR | §3 XC-PRESERVE "How" | "a second disk or the Tier-2 sticks after P1-15" | The sticks are the only backup media; the owner mounts them, and the scheduler archives into them (`util/juniper-backup-scheduled.bash:22–26`, `:66–75`). An unnamed "second disk" may be `/mnt/Backups/Ubuntu/`, where "nothing … moves" (`EX/extraction-P1-backup.md` §4 hazard 6) | The owner names the target. Sessions never write to backup media |
| B2-12 | MINOR | §4 Wave 0 items 1 and 3; §10 P1 | "both sticks", citing `…RECOVERY-PLAN.md` §6.3 step 8; "Purge nothing" | The cited source still says a one-stick run is OK (:255), and §10 omits that correction (`EX/extraction-P1-backup.md` §5 item 7). Item 3's summary also hides two deletions: `sudo rm -r /home/duplicati/bin` (:247) and `rm …/curious-plotting-hummingbird/.env` (:249) | Add both corrections to §10; name the deletions in item 3 |
| B2-13 | MINOR | §4 S0.9; §1.3; Wave 2 P1-11; XC-FLEET | "It is read-only"; the authority list; "merge, fix, hold or close" | P9-13's all-OK branch opens a PR, and its other branch says "do not re-pin" (OD-2, owner). §1.3 omits repository settings, Actions secrets and branch deletion. P1-11's `secret_scanning_non_provider_patterns` is OWNER-ACTION (`EX/extraction-P1-backup.md` P1-11). "Hold" has no mechanism, since drafting is not a hold (H-1) | Say "report only; re-pins wait for OD-2". Complete the authority list. Mark the P1-11 setting as owner-only. Drop "hold" |
| B2-14 | MINOR | §3 XC-MEM; "Changed by this plan" | "24.2–25.2 KB against a 24.4 KB read limit" | `MEMORY.md` is now 25,455 B / 25,251 chars (mtime 21:28Z; a later writer appended an entry), past both figures, so net-zero is not holding. The correction reaches only new sessions: this agent's inherited context still reads "Phase A/B landed, STOP cleared" | Re-measure. Note that running sessions keep the stale line |
| B2-15 | MINOR | §12 Assumptions; Scope "Inputs" | "checked by the consensus rounds in the validation record"; "all read …, which followed their references" | The validation record is empty. Key references were read only in part or by grep (§0 of `EX/extraction-P1-backup.md`, `EX/extraction-P2-canopy.md` and `EX/extraction-P12-equities.md`) | Put the check in the future tense, and say "partially" |
| B2-16 | MINOR | Throughout | The naming rule (`AGENTS.md` § Conventions) | References with no filename: "the 2026-10-03 state assessment", "the register" (Overview); "The same file's" (Wave 0 item 3); "the recovery plan", MATRIX, LEDGER, CONS, "the spec", "the ROADMAP", DESIGN, "the archiver" (§10); "the design's D-3", V3 (§6); R2-6 (Wave 2); "the owner's 2026-09-15 ruling" (XC-MEM) | Add the filenames |
| B2-17 | MINOR | Wave 0 header vs §11 header | Two different hazard pointers | Wave 0 points to the path handoffs, but the hazards found on 10-04 live only in the reports' §4. Examples: `stage_design_artifacts.py --check` exits 0 on drift (P1 hazard 5); `JUNIPER_EXP_PROJECT_DIR`; and APD-ML-002's one-level unwrap that "looks fixed" (`EX/extraction-P6-perf.md` §4), which bears on W0.4 | Point Wave 0 at both |

## Checked and holds

- **CI and rulesets.** The ml, data and canopy CI pushes fire only on `main` and `develop`, and the ml rulesets are `~DEFAULT_BRANCH`-only. A `wip/*` ref therefore triggers no CI and needs no signature.
- **LFS and size.** `.gitattributes` tracks images only. The `.npz` (133 KB), the evidence (2.4 MB) and the `.prof` files (2.0 MB) break no LFS rule and no size limit.
- **Authority framing.** These hold:
  - Out of Scope, XC-GRANT and XC-CLEAN;
  - P1-10's explicit OK;
  - owner-only cuts, and H-9 with `--target-sha`;
  - "DRAFT … carries no approval".
- **Hedging.** "Watchdog probably dark" is hedged enough.
- **Memory correction.** It is dated, sourced to `cf711cf4`, append-only, and also fixes #2114/#2115. It is appropriately scoped.
- **"Created" list.** It matched the ten reports when this lane started.
- **Count-only probes.** None of row j's 24 transcript files holds a token-shaped string, and row i has no credential-shaped assignment.

## Could not check

- **gitleaks with zero rules.** It is not installed, so I could not see whether it errors or passes; the conclusion is inferred from its README and the configs. If it holds, the CI Gitleaks steps in ml, data, canopy and deploy are vacuous too.
- **Not observed**: the A.md and C.md values; rows b and g, which are on tmpfs; the sweeper's code; the real `MEMORY.md` load limit; Yahoo and SEC terms.
- **The plan's "net −25 bytes"**: the file has been rewritten since.

## What this report cannot support

- That any secret is present in rows a, b, i or j.
- Host state.
- Other sessions' intent.
- The severities, which are judgement.

**Changed**: this file only (`reports/2026-10-04_consolidated-development-plan/round1-laneB2-safety-actionability-attack.md`).
