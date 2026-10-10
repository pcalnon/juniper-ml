# Round 2 — reconciliation of two lanes into plan v1.2.0

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.1.0 (sha256 prefix `b81c6afaa8580c0b`) → v1.2.0 (sha256 prefix `68ba9e62dbc6c803`).
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 2 was briefed on round 1's corrections only.
- **Lane reports** (both in this directory): `round2-laneA-reprobe-corrections.md` and `round2-laneB-attack-the-corrections.md`.
- **State re-probe**: on 2026-10-05 at 10:25Z, with `util/ad-hoc/2026-10-05_ecosystem_live_census.py`, before v1.2.0 was written.
- **ID coverage**: v1.0 → v1.2 drops no ID, and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Lane(s) | Re-derivation | Result |
| --- | --- | --- | --- |
| The secret-shape script is not a screen | B (R2B-01) | Read the script's header and `main()` | Its own docstring says it tests fake values against regexes. **Confirmed: the round-1 reconciler's error** |
| The six DSN variable names | A (R2A-02) | `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` L126 | All six are named there |
| L86's exact wording | A (R2A-09), B (R2B-09) | `awk 'NR==86'` on `HANDOFF_2026-10-03_dynamic-workflow-harness-consolidated.md` | "**Soft** … lost three round-1 validators and both round-2 validators" |
| The watchdog redeploy command | A (R2A-04), B (R2B-07) | ml#2134's PR body | `bash util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id 2` |
| The zero-rule probe is reproducible from the repository | — | `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --config .gitleaks.toml` | Default rules: 1. Repo config: 0 → ZERO-RULE (exit 1) |
| F-S10 / W1.14 (found in the 2026-10-05 re-probe) | — | `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` on `main`, L146 and L401 | `map_data_error` relays a padded `JUNIPER_DATA_API_KEY` in 502 bodies. W1.14 is proposed and needs owner acceptance |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.2.0 |
| --- | --- | --- | --- |
| R2A-01 GitHub-native scanning off in deploy; non-provider patterns off ×9; all nine repos public; recurrence has no gitleaks; P1-11's owner half dropped | MAJOR | Accepted | Overview 2; XC-LEAKS; §6 A3; Wave 0 owner step 7; H-17, H-18 |
| R2A-02 The DSN names are not in the cited report | MAJOR | Accepted (re-derived) | XC-SENTRY; H-14 (inline, citing L126) |
| R2A-03 The push ban blocks the Tier-1 path | MAJOR | Accepted (with R2B-02) | XC-PRESERVE method: the ban covers preservation copies only; rows a, b and k go through P1-10/P1-09 |
| R2A-04 ml#2134 merged | MAJOR | Accepted (drift) | §2 P1; Appendix A "Done"; S0.3; Wave 0 owner step 5; §6 A2 N-1 |
| R2A-05 P12's phase 0 merged | MAJOR | Accepted (drift) | XC-P12 rewritten as ratify-or-revert; §6 A1; §7.1; Appendix A P12 "Done" |
| R2A-06 What gitleaks-action actually scans | MINOR | Accepted (with R2B-06) | XC-LEAKS: PRs go green; history is never rescanned; local full-history scans; hits go to the owner |
| R2A-07 "Only copy" overstated | MINOR | Accepted | Overview; H-16 (S-7 cleartext copy; the only *in-backup* copy of `PASSPHRASE_OLD`) |
| R2A-08 Tier 2 keeps `.git` | MINOR | Accepted (with R2B-14) | Overview 4; XC-PRESERVE rows a and f |
| R2A-09 L86 misquoted; the three-agent cap's source | MINOR | Accepted | §1.3 (quoted exactly; cap sourced to `EX/extraction-P8-harness.md` §4) |
| R2A-10 Two bench caps; they bind only at 0.17.0 | MINOR | Accepted | Wave 1 data step 3; §5 R-DATA; §9 |
| R2A-11 L2277 vs L2278 | NIT | Accepted | Wave 0 owner step 3; §10 P1 |
| R2A-12 Row details; cascor's two locks | NIT | Accepted | XC-PRESERVE rows i, m, n; Wave 1 security step 4; §5 R-CASCOR |
| R2B-01 Not a screen | BLOCKER | Accepted (re-derived) | XC-PRESERVE method; §9 "Every public push" row; the tripwire is labelled as one |
| R2B-02 The no-push rule blocks P1-09/P1-10 | MAJOR | Accepted | XC-PRESERVE method |
| R2B-03 §3/§9 contradiction | MAJOR | Accepted | Pushes are gated on a local scan, not on XC-LEAKS landing (§3, §9) |
| R2B-04 S0.8 deletion path | MAJOR | Accepted | S0.8 also sets `JUNIPER_E2E_PROJECT_DIR`, checks the dry run's `rm` path, and rebases on ml#2139; H-15 |
| R2B-05 All nine repositories are public | MAJOR | Accepted | Overview 2; H-18 |
| R2B-06 "Expect red" is wrong | MAJOR | Accepted | XC-LEAKS work table |
| R2B-07 Drift inside the validation window | MAJOR | Accepted | Snapshot line; §2; S0.3; XC-FLEET; re-probe on 2026-10-05 |
| R2B-08 Rulings come last in the owner sitting | MAJOR | Accepted | Wave 0 owner order: rulings first, then steps 1–9 in source order |
| R2B-09 The concurrency rule stated as fixed | MAJOR | Accepted | §1.3 (soft; owner's choice at §6 A7; preempt defined); §7.1 (P3-09 added; arithmetic shown) |
| R2B-10 The index is over its load limit | MAJOR | Accepted | XC-MEM (net-negative; retirement set in Group A, A6); H-11 |
| R2B-11 The lock-PR edge is overstated; the trio's environments | MAJOR | Accepted | §9 (images only; trio environment row); XC-SENTRY; §5 R-OBS-SC |
| R2B-12 Consistency | MINOR | Accepted | P7-18 → T2; P5-09 split T0/T1; "Done" lists; path prefixes on D-IDs; P4 D-1 moved mid-wave; count of *(v)* items |
| R2B-13 P1-11's hook and owner setting dropped | MINOR | Accepted | XC-LEAKS work table; §6 A3; Appendix B row 22 |
| R2B-14 What Tier 2 protects | MINOR | Accepted (with R2A-08) | Overview 4; XC-PRESERVE |
| R2B-15 Missing filenames | MINOR | Accepted | "Documents referenced" table extended; references rewritten throughout |
| R2B-16 Validation-record accuracy; `/tmp` instruments | MINOR | Accepted | Validation record rewritten (round-1 limits stated); scripts moved to `util/ad-hoc/`; transcript rows copied locally now |
| R2B-17 H-16's stated reason; "pypi gate"; deploy is not on PyPI | NIT | Accepted | H-16; §5 "every cut"; success metrics |

## Added from the 2026-10-05 re-probe (not lane findings)

- **ml#2151** merged (P12 P0 close-out). P12's current handoff is `HANDOFF_2026-10-04_recurrence-equities-p0-executed-go-verdict-p1-next.md`.
- **F-S10 / W1.14** (a security item). Added to Overview 2, XC-P12, S0.11, §5 R-RECURRENCE-SEC, §6 A1, §7.1 (safety round), H-22 and XC-CRED.
- **The fleet**: 42 drafts across five repositories (ml 28, canopy 8, cascor 2, worker 2, deploy 2).
- **ml#2154** (the weekly lockfile PR, 08:32Z) makes P9-14 runnable.
- **No releases** and no PyPI uploads since 2026-09-24.

## Unresolved dissent

None.

## What this reconciliation cannot support

- That round 2's corrections introduced no new error. Round 3 is briefed on exactly that.
- Host state, and whether `JUNIPER_DATA_API_KEY` was ever padded.
- Any state after 2026-10-05T10:25Z.
