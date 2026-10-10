# Round 2 — Lane A (re-probe the corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-2 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round2-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- Instrument: `gh api` REST (PRs, check-runs, job logs, rulesets, `security_and_analysis`, contents on `main`), PyPI JSON, reads of this worktree at `cf711cf4`, `ls`/`find`/`stat` metadata, and the scratch scanner (gitleaks v8.30.1). The scanner ran on one synthetic token in a scratch dir, against scratch copies of six fetched configs. I also read gitleaks-action at its pinned `e0c47f4f`, and gitleaks' config loader at v8.24.3 and v8.30.1. Nothing was executed in a repository, and nothing was written there. measured_at 2026-10-04T22:03Z–22:27Z.
- Entry point: the lines that `plan_v1.0_to_v1.1.diff` adds or changes in `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` ("the plan"; sha256 prefix `b81c6afaa8580c0b` verified). L-numbers are the plan's v1.1 lines.
- Sample: about 95 claims re-derived; 12 mismatches (5 MAJOR, 5 MINOR, 2 NIT).

## Findings

| ID | Severity | Plan location (v1.1) | Plan says | Re-derived (command / file:line → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R2A-01 | MAJOR | Overview 2 (L55); L121; XC-LEAKS (L222–231); H-17/H-18 (L798–799) | "Secret scanning is vacuous". Three repos are public. The fix is `useDefault` plus B9 | `repos/<r> .security_and_analysis`: GitHub's own secret scanning and push protection are **on in 8 repos and both off in juniper-deploy**. `non_provider_patterns` is off in all 9. **All nine repos are public.** recurrence has no `.gitleaks.toml`, no gitleaks step in its 17 workflows, and no gitleaks hook. P1-11's owner half (enable `secret_scanning_non_provider_patterns`, `extraction-P1-backup.md` L34) is absent from the plan (grep: 0), although `round1-reconciliation.md` lists B2-13 as applied to it | Say exactly what is vacuous: gitleaks has zero rules in ml, data, canopy and deploy. Deploy has no scanning at all, and non-provider secrets (passphrases, DSNs) are uncovered everywhere. Add owner settings to Wave 0: scanning and push protection on deploy, and non-provider patterns on all nine. H-18 should say all nine are public. Add gitleaks to recurrence |
| R2A-02 | MAJOR | H-14 (L795) | "the six Sentry DSN variables named in `EX/extraction-P3-defect-register.md` §4" | §4 L186 names none of them. They are in `HO/HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` L126: `SENTRY_SDK_DSN`, `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` | List the six names inline and cite L126 |
| R2A-03 | MAJOR | XC-PRESERVE Method (L213–214) against L407 and L429 | "Never push … to a public repository": rows a, b, g, i–l. Repository-destined rows are only c and d | P1-09 archives row b verbatim into a `notes/` record (`extraction-P1-backup.md` L32). P1-10 is the Phase B PR, carrying row a (L33). Both go into public juniper-ml, and "P1-10 merged" is a Wave 0–1 exit. Row k exists to satisfy release limit 2, "archived verbatim into a record merged to `main`" (`round1-laneA1-residue-P1-P3.md` A1-03). Read literally, the rule blocks the Tier-1 path | Limit the ban to preservation (`wip/`) pushes. Make rows a, b and k repository-destined through P1-10 and P1-09, after a screen with a ruled scanner and an owner-approved file list |
| R2A-04 | MAJOR | §2 P1 (L169); S0.3 (L363–367); XC-FLEET (L250); §6 A2 N-1 (L522) | "ml#2115 needs a fix-forward": #2129 is red. S0.3 supersedes #2129, and "if N-1 is ruled yes" sets the default to `""` | **ml#2134 merged 21:56:08Z**, inside the declared 21:27–22:00Z window and before the plan's 22:01Z mtime. It is ml#2115's fix-forward, it ran two lanes (F1, F2), it supersedes #2129 ("Recommend closing it"), and it records P1-04's residue. `main`'s watchdog now has `--backup-id default=""`: an absent id records `JOB_MISSING`, and a usage error exits 64 (`util/ad-hoc/yamaguchi_watchdog.py:313`). It also confirms the watchdog has been dark since the 10-04 12:00 check | Mark P1-01..04 done and #2129 "close". Make N-1 ratify-or-revert. Add an owner step: sync the primary, then run `yamaguchi_watchdog_deploy.bash --backup-id 2` |
| R2A-05 | MAJOR | §2 P12 (L180); XC-P12 (L295, L304, L311); §6 A1 (L521); §9 (L690); §7.1 #14 | ml#2130 is "armed". The owner decides whether it merges before review. S0.9 asks for holds; rulings come before W0.3–W0.5 | **ml#2130 merged 21:41:43Z**, before the plan was written. After it was written: **ml#2145** (the #2131 re-land) merged at 22:11:33Z by auto-merge. Its W0.3 "applies … R6 … pending the owner's ruling", and its W0.4 is APD-ML-002's recurrence half. **canopy#702** (W0.5) merged at 22:11:47Z and keeps the 4xx detail, which is #685(a) = "keep". **ml#2139** (W0.2) merged at 22:21:08Z | Make A1 ratify-or-revert for R6, OD-2 and #685(a). Drop the holds and the "merge before review" ruling. The register records APD-ML-002 as partly fixed; the cascor half still has P6-08's 2-of-6 trap |
| R2A-06 | MINOR | XC-LEAKS (L229–230); S0.2 (L362) | "land each on a branch … watch the required `Security Scan` check"; "Expect the check to go red" | The action defaults to gitleaks **8.24.3** (`src/index.js:138`; CI logs agree). A push scans `--log-opts=-1`, which is 1 commit; a PR scans only its own commits. `ci.yml` pushes fire on `main`/`develop` only. The check is "Security Scans" in data and canopy and "Gitleaks" in deploy. Only data's daily cron scans history (1,094 commits, green) | Verify with the scratch probe, then one owner-run full-history scan per repo. Expect red there, not on the PR |
| R2A-07 | MINOR | Overview (L65); H-16 (L797) | "holds the only copy of a backup passphrase" (`…backup-arc-consolidated.md` L283) | L283 says it "holds S-7, a world-readable `.env`". `…INTEGRATED-DESIGN.md` L2255 puts the passphrase in S-7 **and** S-4, the Dropbox escrow (`…RECOVERY-PLAN.md` L80). `JUNIPER_2026-08-25_…BACKUP-CERTIFICATION.md` L1683–1684 says a sweep removes "the only **in-backup** copy of `PASSPHRASE_OLD`" | "Holds S-7, a cleartext copy of both passphrases". "Only copy" contradicts H-16's own removal step, and invites copying the secret |
| R2A-08 | MINOR | Overview 4 (L59) | Tier 2 "protects none of them, because it excludes `.claude`, `.amp` and `reports`" | `--exclude-vcs` is commented out (`util/juniper-backup.bash:202`) and TAR_ARGS keeps `.git` (L613). So row f's commits, which REST does not have (422), are archived from `juniper-canopy/.git`, as is row a's `6a1514e4`. The other rows sit outside the archived repos | "None except row f and row a's committed half" |
| R2A-09 | MINOR | §1.3 (L156) | The window "killed every one of P8's round-1 and round-2 validators" (L86) | L86 says "lost three round-1 validators and both round-2 validators", and round 1's five reports exist (row j). L86 does not set "three agents account-wide" | Quote L86, and source the 3-agent cap separately |
| R2A-10 | MINOR | L392; §5 R-DATA (L485); §9 (L684) | The recurrence `[bench]` cap PR is "Hard" | There are two caps, `[bench]` (`juniper-recurrence/pyproject.toml:97`) and `[bench-equities]` (`:106`), both `<0.17.0`. They bind only if D-07 makes the release 0.17.0, and B1-11 found that the bench CI installs past them | Name both lines; "Hard if R-DATA is 0.17.0" |
| R2A-11 | NIT | §10 P1 (L713) | "L2277 is stale: installer landed" | The stale sentence is on L2278. L2277 itself prescribes "one SKIPPED (unplugged) and one OK (plugged)", which `pr2114.md:88` flags (BLOCKER-1) | Add L2277's ordering correction |
| R2A-12 | NIT | Rows i, m, n; L351; L124; App. A P7 | — | Row m: `shadow-ec-cap64` is a directory; the symlink is `shadow-ec-cap64/juniper-cascor`. Row n: 109 `.py` files, 8 of them tracked (A3). Row i's 103 files include the npz, and a second npz (133,092 B against 133,161 B) is in `scratch/data-store/`. The installer citation `:205-212` omits the drill at L214. deploy is not on PyPI. P7-18 is in the Wave 2 lane but tiered T5. cascor's image uses `requirements-cpu.lock`, so its lock PR moves two locks | Fix in place |

## Live drift since 21:40Z (compact)

- **ml merges**:
  - #2130 at 21:41:43Z (the P12 plan is now v1.3.0 on `main`);
  - #2134 at 21:56:08Z;
  - #2145 at 22:11:33Z (#2131 closed unmerged at 22:03Z);
  - #2139 at 22:21:08Z (it changes `util/isolated_stack.bash` +92/−4, which S0.8 concerns).
- **canopy**: #702 merged at 22:11:47Z, leaving 59 commits and 24 ship-path `.py` files unreleased.
- **Drafts**: there are now 24 ml and 6 canopy cursor drafts, against the plan's 12.
  - All 12 that XC-FLEET lists remain open, in the stated CI states. #2129 and canopy #700 are now `dirty`.
  - #2134 says #2119 and #2128 would land false statements.
- **P12 worktrees**: only `juniper-ml--feat--p0-recurrence-env-preflight--…cf711cf4` remains of XC-P12's four.
- **Memory index**: `MEMORY.md` is 25,906 B (22:16:52Z) and still rising.
- **Unchanged**: no Release or publish since data v0.16.0. recurrence#189 and #190 merged at 21:19:20Z and 21:22:34Z, as stated.

## Checked and holds (short)

- **gitleaks configs.** ml, data, canopy and deploy have no `[extend]` and no rules, and the probe found 0 of 1 with each. cascor and cascor-client extend the defaults, and the probe found 1 of 1 with each. The CI logs show the repository config auto-loaded. v8.24.3 has no empty-rules fallback.
- **Credentials and locks.**
  - `~/.bashrc:152` exports `SENTRY_SDK_DSN` (name only).
  - Four consumer locks pin observability 0.4.0 and service-core 0.7.0, and their Dockerfiles install from a lock.
  - Both `[Unreleased]` sections are Fixed/Security only, and the caps exist.
  - PyPI versions are as stated.
- **Backup citations.** These all hold as stated:
  - `…fold-in-pending.md` L9;
  - `…RECOVERY-PLAN.md` L255, and Phase C steps 1 and 3;
  - the installer's order at L205–214;
  - the PF-3 header at L59–64;
  - `juniper-backup.bash:142`;
  - the secret screen;
  - `/` on nvme, `/home` on `sdc3`.
- **Preservation and cleanup paths.** All worktrees, the 32 `.prof` files and the baselines exist, and the KEEP and XC-CLEAN gate sources hold. Transcript expiries match 30-day pruning; no override is set.
- **Appendix A.**
  - P2-R8..R12 are at `extraction-P2-canopy.md` L132–136.
  - P2-R13 is at the ledger's L9205.
  - P10-11 is in the 09-11 handoff's Corrections item 2 (L244–262).
  - canopy#552 is open.
  - The moved IDs are consistent with the body.
- **Documents and records.** All 18 files in the documents table exist. The Validation-record severity counts match the lane reports. The spec's §11.2 numbering and the XC-FLEET overlaps hold.

## Could not check

- The counts behind rows a and n: git is refused in other worktrees.
- Rows b and g on tmpfs, and transcript contents.
- Whether push protection covers `createCommitOnBranch`.
- The 21:03Z measurement time, which comes from lane A4.
- Host state.

## What this report cannot support

- State after 22:27Z.
- That any repository's history is leak-free; no real repository was scanned.
- Rulings or grants given in other sessions' chats.
- The severities, which are judgement.

**Changed**: this file only (`reports/2026-10-04_consolidated-development-plan/round2-laneA-reprobe-corrections.md`). The scratch scripts live in the session scratchpad.
