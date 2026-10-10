# Round 1 — Lane A1 (residue, P1–P3)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-1 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round1-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- **Instrument**: I read the five source handoffs in full, then:
  - `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` ("A"), in full;
  - from `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("D"): §8 STOP, §10, S-7a and Appendix C;
  - the ledger's Phase 9 still-owed list, and the register's 136 §4 rows (36 open);
  - the Phase B lane reports in the `cached-swinging-summit` worktree.

  I built my item list before reading `extraction-P1-backup.md`, `extraction-P2-canopy.md`, `extraction-P3-defect-register.md` and the plan (sha256 `05d7a571d00e617d`). Live checks used `gh api` REST, grep and `ls`. No scripts, tests or host actions.
- **Entry point**: the source handoffs and their references.
- **Sample**:
  - About 150 source items: P1 ≈35; P2 ≈45, including ledger items 0–17; P3 ≈35 work and decision items plus 36 open register rows. All were checked.
  - Appendix A places every extraction row: P1 26/26, P2 41/41, P3 37/37.
  - 15 findings: 1 BLOCKER, 4 MAJOR, 9 MINOR and 1 NIT.

## Findings

Abbreviations: "Plan" is `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. "Backup-cons" is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-arc-consolidated.md`. "P3-HO" is `…/HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`. "CONS" is `…/HANDOFF_2026-10-03_canopy-consolidated.md`.

| ID | Severity | Item (from source) | Source (file §/line) | In extraction report? | In plan? (where) | Evidence | Proposed correction |
|---|---|---|---|---|---|---|---|
| A1-01 | BLOCKER | `juniper-ml/.claude/worktrees/curious-plotting-hummingbird` is DO NOT SWEEP. It holds S-7 (cleartext `PASSPHRASE`/`PASSPHRASE_OLD`). Only its `.env` is removed, by the owner, after the S-7a fingerprint check | Backup-cons L283; D L499 (S-7a: "Remove the file, never clean the directory") | No (grep 0 in all ten reports) | No (grep 0). XC-CLEAN (L209–214) and H-6 (L559) carry no exemption | Worktree exists (`ls`). Memory `reference_worktree_sweep_hazards_2026-09-12.md` L14–22: `PASSPHRASE_OLD` "has no surviving out-of-band copy", and the worktree passes `scripts/cleanup_session_worktrees.py`'s gates. That script has no exemption for it (grep 0) | Add to XC-CLEAN, XC-PRESERVE and H-6: never remove this worktree; the owner removes only its `.env`, at Phase C step 3, after S-7a |
| A1-02 | MAJOR | The STOP clears only when the follow-up "settles each open question in its last paragraph" (P0.5b's need, which is O-7). B1 and B8 embed O-8 (where the D-1 flag lives) and O-12 (the `.env` mode/path) | D L1735–1736, L1782–1787; `extraction-P1-backup.md` §2 O-7/O-8/O-12, each marked "Blocks P1-10" | Yes | Mis-sequenced. P1-10 is in Wave 1 (L277); A3 (L355) asks only O-6. O-7/O-8/O-12 are in Group B, "before Phase D" (L364–369), and the header says that sitting "gates T2 and T5" | Extraction's Blocks column vs Plan §6 | Move O-7, O-8 and O-12 into A3, or make P1-10 wait for them. State that P1-10 cannot clear the STOP before O-7 is ruled |
| A1-03 | MAJOR | Release limit 2: no transcript is purged until "every validation round of the arc … [is] archived verbatim into a record merged to `main`" | D L1746–1749, note 10.1g L2456–2458 | Partly. §4 hazard 6 states the rule, but P1-09 archives only Phase B | No. XC-PRESERVE j (L148) covers P8's transcripts only | A's own round 1 (three lanes) and Phase A's narrow lane are archived nowhere: ml#2111's files are the assessment plus the handoff; ml#2113's body only summarizes its lane; the round-4 record holds rounds 4–8. No `cleanupPeriodDays` override exists, and the oldest transcript directory is 09-04 (30-day pruning), so these 10-03 transcripts go about 11-02 | Add XC-PRESERVE row k: extract both rounds verbatim, after a secret screen, into P1-09's round record before about 11-02 |
| A1-04 | MAJOR | Ledger item 17 / O3: a replay silently replaces cascor's live, possibly unsaved, network, while canopy's modal promises "a read-only playback session" | Ledger L9779–9785; CONS A3 L186–189 | Yes (P2-23, DATA-INTEGRITY) | Mis-tiered. O3 is in Group B (L385). R-CANOPY-A (L326), recommended first (L333), has no O3 gate, and it is the release that makes the player work | P2-23 verified at canopy `1b2dd438` (`hdf5_snapshots_panel.py:533`, `main.py:3016`) | Move O3 to A5. Make the wording fix, or an explicit owner acceptance, a gate or rider of R-CANOPY-A |
| A1-05 | MAJOR | Screen archived reports for secrets before any commit. Never copy anything into `…/Backups/Yamaguchi/`; nothing under `/mnt/Backups/Ubuntu/` moves | Backup-cons L123, L282 | Yes (P1 hazards) | Contradicted by XC-PRESERVE "How" (L152–153): "secret-scan it (gitleaks) and push it to a `wip/preserve-…` branch", otherwise "a second disk" | `command -v gitleaks` finds nothing (also A L84). `gh api repos/pcalnon/juniper-ml` → `visibility=public`, so the push publishes. The only other large disk is `sda1`, which holds the sole T1 copy and the Dropbox-synced tree (D §10.2b) | Name an installed screen (`util/ad-hoc/2026-09-24_secret_shape_check.py`, the archivers' credential screen) or land B9 first. Say that the push publishes. Exclude `/mnt/Backups/Ubuntu/**` as a target and prefer `/` (nvme) |
| A1-06 | MINOR | Tier-2 first run: OK first, with both sticks. One stick gives `FAILED` rc 4, writes no stamp, and rebuilds the full set on every plug-in | `pr2114.md` BLOCKER-1 L13–25 | Yes (§5 item 7) | Wave 0 item 1 (L228) says "both", but it cites A §6.3 step 8, whose `main` text (L255) prescribes SKIPPED first and one stick. §10's P1 bullets omit this | A L255; installer on `main` L206 "Do the OK run FIRST, with BOTH" | Cite the installer message instead. Add A:255 and D:2277/:2306 to §10 |
| A1-07 | MINOR | The P3 archiver re-verifies every archived report against its transcript. The P3-02 brief model is a transcript (`agent-a46e715a6801b98ca.jsonl`) | P3-HO L115–121, L176, L360 | No (only P3-02's tmpfs files) | No (XC-PRESERVE g covers tmpfs only) | `util/ad-hoc/2026-09-24_archive_round42_reports.py` L73–76 and L206–217: a missing transcript raises `SystemExit` before step 2. The cited sessions date from 09-23/24, so they go about 10-24 | Archive P3's new reports before about 10-23, or harvest those transcripts and make the archiver skip pruned ones |
| A1-08 | MINOR | Keep the data worktree until P3-03 and the cascor shortfall worktree until P3-05. Diff the four older dirty worktrees (1, 16, 1 and 5 entries) before asking | P3-HO L403–407 | Partly: P3-29 keeps both; dirty contents were "not probed" | Dropped. XC-CLEAN is gated only on XC-PRESERVE and O2 (L211); "dirty" greps 0 | — | Carry P3-29's keep-until conditions and its diff-first rule into XC-CLEAN |
| A1-09 | MINOR | Only one register or primer PR may be open at a time, built from fresh `main`. The primer is edited in place only | P3-HO L38, L105 | Yes (§4) | No §8 row (L441–452), although P3-10..15, P3-33/P6-33 and P3-35 all upload these files | — | Add an §8 row for the register and the primer |
| A1-10 | MINOR | P2 residue: R8 (A-N2 O6–O8), R10 (Phase 6 items 1b and 4), R11 (the WS-migration plan still gates on the F-036 decision), R12 (canopy#552) | `extraction-P2-canopy.md` §6 L132–136 | Yes, but without IDs | Not placed: Appendix A places IDs only, and greps return 0 | canopy#552 is OPEN since 08-31 (REST). `JUNIPER_2026-08-27_…WS-MIGRATION-PLAN-JR-CAN-PERF-004.md:265,279` still gate on it | Give each an ID and a tier, or record the drop with a reason |
| A1-11 | MINOR | Unexplained: an explicit save taken after two quick Start/Stop cycles held no loss arrays, and automatic snapshots carry no training history | Ledger L9201–9206; 10-04 handoff L58–60 | No (grep 0) | No (grep 0) | Sibling of F-CASCOR-002 (cascor#602, OPEN) | Add a P2 lead beside P2-17: re-derive it in cascor, then file it or explain it |
| A1-12 | MINOR | F-061/062 become FIXED-BY #685 "only after item 3 validates" | P3-HO L42, L63 | Yes (P3 §5 item 6) | Flagged in §10 (L506) but not resolved. Neither P2-01 in Wave 1 (L279) nor §9 carries the gate | — | Add a §9 row "P2-01 (061/062) after P3-06" |
| A1-13 | MINOR | D-10 covers the nine parked rows, including canopy's severity-S rows APD-ECO-009/-010/-011 (and -012) | P3-HO L323; register L1298–1300, L1306 | Yes (P3-22, SAFETY) | In Group B (L371), while R-CANOPY-A is in Group A | — | Ask the four canopy rows in A4 beside D-04, or record that the release ships with them open |
| A1-14 | MINOR | Tier 1 (all of `/home/pcalnon`) stays down until Phase D. Tier 2 archives only the Juniper repos | A §2 L39–41 | Yes (P1-08 SAFETY; P3-05 USER-FACING) | §7.1 queues P1-08 sixth (L411), behind P3-01 and P3-05 (L409–410). That contradicts §1.2's criterion 1 | — | Run P1-08 as soon as P1-05..07 land, ahead of P3-05 |
| A1-15 | NIT | Packet consistency | — | — | Several places | N-1 is asked in A3 (L355), yet S0.2 already implements it (L248). N-4 (Group C, L389) duplicates A2. P2's O15 is in no group. P2-12 (RESEARCH, M) sits in T6 (L616). §9's "Pick one owner" (L469) omits the 2c→2a→2b merge order (CONS L343–347) | Tidy each one |

## Checked and holds

- **P1**: every item is placed, and O-1..O-14 and N-1..N-6 all sit in §6. That covers P1-01..04 (with #2129's partial scope), the fleet drafts, P1-05..07 with residue R1–R6, round N+1, the Phase B PR, B9, B11, Phase C, Tier 2, O-10, TestPyPI, Phases D and E, Appendix C (B1 F14 is item 9) and D-12a. The memory fix holds: `MEMORY.md` L42 reads "§8 STOP STILL on main".
- **P1 source findings**: pr2114's BLOCKER-1 and DEFECT-1..3 are fixed on `main`. pr2115's B-1/D-1/N-1/N-2/N-5 map to P1-01, P1-02 and P1-25. The Phase B lanes' BLOCKERs and DEFECTs are in the fold-in's fixed list. Consolidated item 8 is done on `main`.
- **P2**: all 41 rows are placed, and ledger items 0–17 map to rows. H-8 covers the trio. Lane B's trees are XC-PRESERVE e; provenance is f plus A5. F-CASCOR-001/002 map to P2-17 (cascor#590 and #602 OPEN).
- **P3**: all 37 rows are placed, and all 36 open register rows map to items. F2–F10 map to P3-07/08/09, validated before branching (S0.3). R-OBS-SC follows P3-07 (§9). Live: branch `94ce8b1f` has no PR, no validation reports exist, the three S rows are unfiled, and `before_send_transaction` is absent.
- **Reverse check**: the plan closes no P1–P3 item without evidence.

## Could not check

- Host state: the watchdog, Phase C, the sticks and the timer.
- The 24 subagent files of session `652c1204`. I did not open them, because transcripts are a secret sink.
- The contents of the four dirty worktrees.
- Which session ran Phase A's validation lane.
- Whether a cleanup executor would actually run `cleanup_session_worktrees.py`.

## What this report cannot support

- Severities and deadlines are judgement. The 30-day pruning is inferred from defaults and directory dates.
- P4–P12 were not validated.
- I read the ledger and the register only in their open-item sections, so residue buried in older phases may remain.
- I ran no repository script or test.
