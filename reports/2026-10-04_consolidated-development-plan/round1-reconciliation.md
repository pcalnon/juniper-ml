# Round 1 — reconciliation of seven lanes into plan v1.1.0

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.0.0 (sha256 prefix `05d7a571d00e617d`) → v1.1.0.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §5. Measurement disputes were settled by opening the artifact. Any load-bearing finding that only one lane reported was re-derived by the reconciler before it was accepted.
- **Lane reports, in this directory**: `round1-laneA1-residue-P1-P3.md`, `round1-laneA2-residue-P4-P5-P11-P12.md`, `round1-laneA3-residue-P6-P10.md`, `round1-laneA4-live-census.md`, `round1-laneA5-citation-fidelity.md`, `round1-laneB1-prioritization-attack.md`, `round1-laneB2-safety-actionability-attack.md`.
- **ID coverage**: checked mechanically, with ranges and slash lists expanded. v1.0 placed all 375 extraction IDs. v1.1 places all 375 plus the IDs that validation added, and drops none.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Lane(s) | Re-derivation | Result |
| --- | --- | --- | --- |
| juniper-ml, juniper-data and juniper-canopy are public | B2, A1, B1 | `gh api repos/pcalnon/<repo> --jq .visibility` | public ×3 |
| juniper-ml's `.gitleaks.toml` runs with zero rules | B2 (inferred) | A scratch probe with the gitleaks v8.30.1 binary and one planted fake GitHub-PAT-shaped string | Repo config: 0 found. Default rules: 1 found. **Confirmed** |
| The shell exports `SENTRY_SDK_DSN` | B2, B1, P3 | `grep -n -o '^export SENTRY_[A-Z_]*' ~/.bashrc` (names only) | Line 152 |
| `HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md` L9 states a merge grant | B2 | `awk 'NR==9'` | "Merge approval for this arc's PRs was granted by the owner on 2026-10-03." |
| Consumer images install observability and service-core from their locks | B1 | juniper-data `Dockerfile:32-33`; `requirements.lock:88/:90` | Pinned to 0.4.0 / 0.7.0 |
| Phase C is ordered "In this order"; step 3 removes the S-7 `.env` | A5, A1 | `JUNIPER_2026-10-03_…RECOVERY-PLAN.md` L245–262 | Confirmed. Step 8's text prescribes SKIPPED first, with one stick |
| PF-3 is one ~7 h pass, run only when quiet | A3 | `util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml` header | Confirmed. Round-robin on a loaded host was declined |
| Tier 2 is encrypted and excludes `.claude`, `.amp` and `reports` | B1 | `util/juniper-backup.bash` L18–24, L142 | Confirmed |
| An installed secret screen exists | A1 | `ls util/ad-hoc/2026-09-24_secret_shape_check.py` | Present |

## Dispositions

"Applied" names the v1.1.0 section that changed.

| Finding | Sev | Disposition | Applied |
| --- | --- | --- | --- |
| A1-01 `curious-plotting-hummingbird` DO NOT SWEEP | BLOCKER | Accepted | XC-CLEAN KEEP list; H-16; Wave 0 step 1; Overview |
| A1-02 O-7/O-8/O-12 gate P1-10 | MAJOR | Accepted | §6 A2; §9 P1-10 row; Wave 1 |
| A1-03 Two rounds archived nowhere (release limit 2) | MAJOR | Accepted | XC-PRESERVE row k |
| A1-04 O3 mis-tiered | MAJOR | Accepted | §6 A5; §5 R-CANOPY-A gate |
| A1-05 Preservation route contradicts the backup rules | MAJOR | Accepted (with B2-01) | XC-PRESERVE method; H-18, H-20 |
| A1-06 Step-8 citation contradicts the cited text | MINOR | Accepted | Wave 0 step 2; §10 P1 |
| A1-07 P3's archiver needs transcripts that expire about 10-23 | MINOR | Accepted | XC-PRESERVE row l; Wave 2 P3 lane |
| A1-08 P3-29 keep-until conditions and diff-first rule | MINOR | Accepted | XC-CLEAN gates |
| A1-09 One register or primer PR at a time | MINOR | Accepted | §8 row |
| A1-10 P2 residue R8, R10–R12 lack IDs | MINOR | Accepted | Appendix A, P2-R8/R10/R11/R12 |
| A1-11 Explicit save with no loss arrays | MINOR | Accepted | Appendix A, P2-R13; Wave 2 P2 lane |
| A1-12 F-061/062 FIXED-BY gate | MINOR | Accepted | §9 row; Wave 1 |
| A1-13 Parked canopy S rows before R-CANOPY-A | MINOR | Accepted | §6 A4; §5 |
| A1-14 P1-08 ranked below P3-05 | MINOR | Accepted | §7.1 order |
| A1-15 Packet tidiness | NIT | Accepted | §6 groups; §9 2c→2a→2b; P2-12 moved to T2 |
| A2-01 W10 floors mis-merged into R-ML | MAJOR | Accepted | §5 R-ML-a/R-ML-b; §8; Appendix B row 6 |
| A2-02 DC-0.6 must rule the cap width | MAJOR | Accepted | §5 DC-0.6; §9 conditional edge |
| A2-03 Canopy 0.9.0 number collision | MAJOR | Accepted (with A5-10, B1-10) | §5: the P12 chain is named by content |
| A2-04 Pre-cut rules | MINOR | Accepted | §5 "Every cut" |
| A2-05 R-DATA "unblocks P5 W-series" | MINOR | Accepted | §5 R-DATA |
| A2-06 W3.5 trigger gap | MINOR | Accepted | §10 P12 |
| A2-07 P12-20 log half and P12-48 rest dropped by the merge | MINOR | Accepted | Appendix A P12 T5 |
| A2-08 Pi-pull gates | MINOR | Accepted | Wave 4; Appendix A P4-27 |
| A2-09 `JuniperCascor1` env collision | MINOR | Accepted | §8 row |
| A2-10 Verify rows for the unverified worktrees | MINOR | Accepted | XC-PRESERVE row p; XC-CLEAN pre-check |
| A2-11 Tier and label consistency | NIT | Accepted | Appendix A; Appendix B row 17; §6 D-11 |
| A2-12 Net-zero rule scoped to the index | NIT | Accepted | XC-MEM; H-11 |
| A3-F1 PF-3 ruling | MAJOR | Accepted (re-derived) | §1.3; §7.2; §10 P6 |
| A3-F2 More single-copy state | MAJOR | Accepted | XC-PRESERVE rows m, n, o |
| A3-F3 Cleanup keep-conditions | MAJOR | Accepted | XC-CLEAN gates and KEEP list |
| A3-F4 The experiment stack's PROJECT_DIR from worktrees | MAJOR | Accepted | H-15; §7.2 launch rules |
| A3-F5 One arc mid-round at a time | MINOR | Accepted | §1.3; §7.1; deviation recorded |
| A3-F6 Inventory transcripts | MINOR | Accepted | XC-PRESERVE row j; Wave 2 P8 |
| A3-F7 Fix the hook-text gates before compaction | MINOR | Accepted | XC-MEM order |
| A3-F8 P2.1 heads the critical path | MINOR | Accepted | Wave 2 P7 lane; Appendix A P7-16 to T2 |
| A3-F9 cascor-client lockfile latent defect | MINOR | Accepted | Appendix A P10-11 *(v)* |
| A3-F10 Start roadmap P0 now? | MINOR | Accepted | §6 Group B (P8) |
| A3-F11 T4 completeness; LOG_DIR rule | MINOR | Accepted | §7.2 |
| A3-F12 Send P6-08's trap with the ruling | MINOR | Accepted | XC-P12 |
| A3-F13 P4-10 → P10-10 edge | MINOR | Accepted | §9 row |
| A3-F14 Tier consistency | NIT | Accepted | Appendix A |
| A4-1 P12 has advanced (#189, #190, ml#2130) | MAJOR | Accepted | §2; XC-P12; §7.1; §7.2; Appendix A P12 |
| A4-2 The canopy drafts' suites never ran | MINOR | Accepted | XC-FLEET |
| A4-3 Order dispositions per file | MINOR | Accepted | XC-FLEET |
| A4-4 Unreleased-package count | MINOR | Accepted (with A5-05) | Success metrics |
| A4-5 Fifth P0 branch; persisting worktree | NIT | Accepted | XC-P12 (state); XC-CLEAN |
| A5-01 Step-8 citation | MAJOR | Accepted (with A1-06) | Wave 0 step 2; §10 P1 |
| A5-02 §2 P5 points at the wrong row | MAJOR | Accepted | §2 P5 row |
| A5-03 "Two of those fixes" | MINOR | Accepted | Overview point 2; §2 P3 |
| A5-04 "about 26" | MINOR | Accepted | §2 P2; §10 P2 |
| A5-05 ml has nothing shippable | MINOR | Accepted | Success metrics |
| A5-06 Memory figures | MINOR | Accepted | XC-MEM |
| A5-07 39 is a static replication | MINOR | Accepted | §2 P7; §10 P7 |
| A5-08 "There are no backups" | MINOR | Accepted | Overview point 1 |
| A5-09 Appendix B row 17 includes P5-19 | MINOR | Accepted | Appendix B row 17 |
| A5-10 R-CANOPY-B 0.9.0 | MINOR | Accepted (with A2-03) | §5 |
| A5-11 P3 has 37 IDs | NIT | Accepted | Scope "Size" |
| A5-12 Row wording | NIT | Accepted | XC-PRESERVE; Appendix B row 16 |
| A5-13 Owner-step reorder unexplained | NIT | Accepted: source order restored | Wave 0 owner sitting |
| A5-14 W5/W11 numbering | NIT | Accepted | §5 DC-0.6 |
| A5-15 P5-13 / P12-09 classes | NIT | Accepted | §7.2 |
| A5-16 Round 6 "never ran"; "every run" | NIT | Accepted | §2 P9/P5; §10 P9 |
| B1-01 No interim Sentry mitigation | MAJOR | Accepted | XC-SENTRY *(v)*; Wave 0; §6 A3 |
| B1-02 Consumer images re-ship the leak | MAJOR | Accepted (re-derived) | §5 "Ready when"; §9 first row; Overview |
| B1-03 Push route can publish credentials | MAJOR | Accepted (with B2-01) | XC-PRESERVE; XC-LEAKS; P1-11 moved to T0 |
| B1-04 Group B holds P1-10's gates | MAJOR | Accepted (with A1-02) | §6 A2; §9 |
| B1-05 XC-P12 race; no hold | MAJOR | Accepted | XC-P12 actions 1–2; §6 A1 first |
| B1-06 P5-11 dependency cycle | MAJOR | Accepted | Wave 1; §8 per-file rows; §9 |
| B1-07 The calendar breaks the agent limit | MAJOR | Accepted | §1.3; §7.1 |
| B1-08 O3 buried | MAJOR | Accepted (with A1-04) | §6 A5; §5 |
| B1-09 Group A not minimal | MINOR | Partially accepted: fleet dispositions moved to the mid-wave sitting; triage stays in Wave 0 | §6 |
| B1-10 Canopy 0.9.0 contested | MINOR | Accepted (with A2-03) | §5 |
| B1-11 `[bench]` cap after R-DATA | MINOR | Accepted | §5 R-DATA; Wave 1 |
| B1-12 R-ML always last; no second cascor release | MINOR | Accepted | §5 R-ML-a/b, R-CASCOR-2 |
| B1-13 "Two weeks" unfalsifiable | MINOR | Accepted | Scope; Wave 1 exit; Wave 2 exits |
| B1-14 DSN rule; row j after XC-CRED | MINOR | Accepted | H-14; XC-PRESERVE method |
| B1-15 Text and placement | NIT | Accepted | §2; Appendix A P5-09; XC-GRANT; §7.2; XC-PRESERVE row q |
| B2-01 Public push behind a zero-rule scan | BLOCKER | Accepted (re-derived empirically) | XC-PRESERVE method; XC-LEAKS *(v)*; H-17, H-18 |
| B2-02 No tool for "signed commit, no PR" | MAJOR | Accepted | XC-PRESERVE method (REST ref + `createCommitOnBranch`; never `open_signed_pr.py`) |
| B2-03 S0.1 not executable by one isolated session | MAJOR | Accepted | XC-PRESERVE method (per-row actor, manifest) |
| B2-04 Finishing #2129 in place | MAJOR | Accepted | S0.3; XC-FLEET |
| B2-05 Testing `--down` kills the trio | MAJOR | Accepted | S0.8 hazard |
| B2-06 `SENTRY_SDK_DSN` exported | MAJOR | Accepted (re-derived) | H-14 |
| B2-07 L9's grant line | MAJOR | Accepted (re-derived) | XC-GRANT; §10 P1 |
| B2-08 A1 as a forward grant | MAJOR | Accepted | §6 ("no standing merge grant") |
| B2-09 Peer relay launders authority | MAJOR | Accepted | §1.3; XC-P12; H-19 |
| B2-10 H-6 parenthetical narrows the ban | MAJOR | Accepted | H-6 |
| B2-11 Backup media as targets | MINOR | Accepted | XC-PRESERVE; H-20 |
| B2-12 Step 8 one stick; hidden deletions | MINOR | Accepted | Wave 0 steps 1–2; §10 P1 |
| B2-13 "Read-only"; authority list; "hold" | MINOR | Accepted | S0.10; Out of Scope; XC-FLEET; Appendix A P1-11 |
| B2-14 Memory re-measure; stale loaded index | MINOR | Accepted | XC-MEM |
| B2-15 Validation-record tense; partial inputs | MINOR | Accepted | Scope "Inputs"; §12 |
| B2-16 Naming-rule violations | MINOR | Accepted | "Documents referenced" table; references throughout |
| B2-17 The hazard pointer | MINOR | Accepted | §4 preamble |

## Unresolved dissent

There is none. B1's "alternative orderings" note judged the owner-step reorder harmless. That note was weighed against A5-13, and the source order was restored.

## What the reconciliation cannot support

- That round 1's corrections introduced no new error. Round 2 is briefed on exactly that.
- XC-LEAKS for juniper-data, juniper-canopy and juniper-deploy, which is reported by B2 and not measured.
- Any state after about 22:00Z.
