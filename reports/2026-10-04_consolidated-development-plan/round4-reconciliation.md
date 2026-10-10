# Round 4 — reconciliation of one lane into plan v1.4.0

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.3.0 (sha256 prefix `51226ccf258bb19f`, unchanged through the round per the lane's own two readings) → v1.4.0.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 4 was briefed on round 3's corrections only.
- **Lane report** (in this directory): `round4-laneB-attack.md`.
- **Re-derivations** below ran on 2026-10-05 between 11:45Z and 12:05Z, read-only. They used GitHub REST on `main` of juniper-canopy, juniper-cascor, juniper-cascor-client and juniper-recurrence, gitleaks-action at its pinned SHA `e0c47f4f`, the installed packages in `JuniperCascor1`, and the scan tool itself on synthetic fakes in the session scratchpad. No secret was read or printed.
- **Also changed during the round**: `round3-reconciliation.md`'s ID-coverage line was clarified (the tool's two-digit pattern cannot see `P2-R8`). No disposition changed.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| The pre-push gate fails open | R4B-01 | The v1.3 tool run with `--scan-dir` on a missing directory, then on an empty one | Both printed "0 finding(s)" and exited 0. **Confirmed** |
| Canopy passes cascor's 409 text on | R4B-02 | canopy `main`: `src/backend/cascor_service_adapter.py` L1114–1116, `src/outbound_errors.py` L32–34 and L56–62; cascor-client `main`: `client.py` L623–624 | Cascor-client raises a 409 with `status_code` set; canopy logs `{e}` at ERROR and returns `str(exc)` for any exception with an int `status_code`. Its own docstring assumes such text is "the upstream's ANSWER", which does not hold when the upstream relays its own upstream's error. **Confirmed** |
| Sentry receives the chained cause | R4B-03 | `sentry_sdk/utils.py` `walk_exception_chain` (L799–821) and `juniper_observability/sentry.py` in `JuniperCascor1` | The walk follows `__cause__` when `__suppress_context__` is set (as `raise … from e` sets it), else `__context__`. The scrubber rewrites request headers only. `raise … from None` ends the walk. **Confirmed** |
| Cascor's image and environment pin data-client 0.5.0 | R4B-04 | cascor `main`: `Dockerfile` L41–42; `requirements-cpu.lock` L120; `requirements.lock` L57 | The image installs `requirements-cpu.lock`; both locks pin `juniper-data-client==0.5.0`. **Confirmed** |
| Phase 1 waits on R2, R8, R7 | R4B-05 | `…equities-p0-executed-go-verdict-p1-next.md` L32 and L35 | L35 opens Phase 1 with data-client W1.4 (R2), then W1.3 (R8), then canopy W1.2 (R7). **Confirmed** |
| The procedure sizes these rounds larger | R4B-06 | `…CONSENSUS-PROCEDURE.md` L81–94 and L104–110 | Medium uncertainty × high criticality is 2 Lane A + 1–2 Lane B; a fix hanging on it escalates; any round with corrections needs another. **Confirmed** |
| The action hard-codes `-v` | R4B-08 | gitleaks-action `src/gitleaks.js` L92–101 at `e0c47f4f` | `detect --redact -v --exit-code=2 …`. **Confirmed** |
| The `<0.6.0` caps | R4B-11 | recurrence `juniper-recurrence/pyproject.toml` L54; canopy `pyproject.toml` L192; cascor `pyproject.toml` L118 | Recurrence and canopy cap `<0.6.0`; cascor is uncapped (`>=0.3.0`). **Confirmed** |
| The `\b` misses prefixed names | R4B-07 | The rewritten tool's canary plants `TIER2_PASSPHRASE=`; the defaults miss it and the new rule (no `\b`) catches it | **Confirmed** (case 1 below) |

## The rewritten scan tool, tested

`util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py` was rewritten for R4B-01 and R4B-07. Every case ran with gitleaks v8.30.1 in a fresh workdir under the session scratchpad. All inputs were synthetic.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | `--config .gitleaks.toml` (probe mode) | Canary 4/4; repo config zero-rule; exit 1 | Canary: token, `PASSPHRASE=`, `TIER2_PASSPHRASE=`, `SETTINGS_ENCRYPTION_KEY:` all 1/1. Defaults alone: 1, 0, 0, 1. `.gitleaks.toml`: 0, 0, 0, 0, ZERO-RULE. Exit 1 |
| 2 | `--scan-dir` on a missing directory | Exit 3 | "is not a directory", exit 3 |
| 3 | `--scan-dir` on an empty directory | Exit 3 | "holds no files", exit 3 |
| 4 | `--release v8.29.0` without `--sha256` | Exit 3 | "no pinned sha256", exit 3 |
| 5 | An unknown flag | Exit 3, not argparse's 2 | Exit 3 |
| 6 | A planted `export TIER2_PASSPHRASE=…` | Reported, exit 2 | `juniper-b9-passphrase-assignment notes.md:3`, exit 2 |
| 7 | Real-looking values starting `.` and `$9` | Both reported | Both reported at their lines (3 findings with case 6), exit 2 |
| 8 | Placeholders only: `<…>`, backtick text, `$VAR`, `${VAR}` | Clean, exit 0 | 0 findings, exit 0 |
| 9 | A `.gitleaksignore` in the directory | Exit 3 | "would silence findings", exit 3 |
| 10 | An inline `gitleaks:allow` marker | Reported, exit 2 | Marker at `notes.md:3`, exit 2 |
| 11 | First download | The tarball matches the pin | sha256 `551f6fc8…` matched the value in v8.30.1's `gitleaks_8.30.1_checksums.txt` |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.4.0 |
| --- | --- | --- | --- |
| R4B-01 The pre-push gate fails open | BLOCKER | Accepted (re-derived; fixed and tested) | The tool: pinned scanner by sha256, refuses a missing or empty directory and any `.gitleaksignore`, canary first, exit-code and report checks, inline allow markers reported; exit 0 clean, 2 found, 3 not run. XC-PRESERVE method ("only exit 0 passes"); §9 "Every public push" |
| R4B-02 Canopy is a fourth relay | MAJOR | Accepted (re-derived) | Overview 2; metric (4 paths); XC-CRED; XC-P12 (canopy#685 (a) note); §6 A1; H-22; §12 |
| R4B-03 The chained cause reaches Sentry | MAJOR | Accepted (re-derived) | Overview 2; XC-P12 action 2 (`from None` or a sanitized cause); S0.11 (a chain-walking test; W1.14 also raises without chaining); R-DC-PATCH's content; H-22; §12 |
| R4B-04 The vehicle row overclaimed | MAJOR | Accepted (re-derived) | §5: the vehicle row states what it closes; new R-DC-PATCH row; Wave 1 "F-S10 delivery"; §9 rows for R-DC-PATCH and for cascor's and canopy's running services; XC-P12 and §6 A1 state (b)'s wait for W1.13 and R-ML-b |
| R4B-05 Phase 1 still stalled | MAJOR | Accepted (re-derived) | New §6 A9 (dates, DC-0.6, R2, R3, R7, R8, R1) ruled at Wave 0 step 8; Group B's P12 list keeps W5.8, W5.9, R5, O8, O12, P4-Q6; §2 and Wave 2 P12 rows; §9 "P12 Phase 1" row; §5 DC-0.6 now at A9 |
| R4B-06 The §7.1 totals are a floor | MAJOR | Accepted (re-derived) | §7.1: 11 first rounds (XC-LEAKS as three, F-S10 as one), 3–4 agents each, about 22 rounds and 66–88 runs (floor 11 and 33), one round at a time; Waves 0–1 now two to four weeks (Scope & Timeframe); S0.5 no longer fixes "two lanes" |
| R4B-07 The interim rule was not a superset | MINOR | Accepted (re-derived) | The tool's rule drops `\b`; the canary plants `TIER2_PASSPHRASE=`; XC-PRESERVE method restates what the rule matches. `round3-reconciliation.md`'s "superset" stays as the record of round 3 |
| R4B-08 The job log publishes anyway | MINOR | Accepted (re-derived) | XC-LEAKS intro (`-v` hard-coded) and note 2 (stop the scheduled scan, or a `.gitleaksignore` baseline); §9 XC-LEAKS row |
| R4B-09 Step 4's place in the order | MINOR | Accepted | XC-LEAKS step 4 marked independent; Wave 0 step 7 |
| R4B-10 P6-34's gate fix unscheduled | MINOR | Accepted | XC-MEM step 2 and §6 A6: the owner rules whether the snapshots stand in for the gate fix |
| R4B-11 The data-client patch had no slot | MINOR | Accepted (re-derived) | §5 R-DC-PATCH, cut before W1.4 merges; recommended order item 1; §9 W1.4 row; Wave 2 P12 notes |
| R4B-12 The `--skip-env-preflight` flag | MINOR | Accepted | §7.2 names the flag and both variables; all need the owner's OK |
| R4B-13 The tool is not on `main` | MINOR | Accepted | §9: P1-09, P1-10 and every other pre-push scan wait for this plan's PR; XC-PRESERVE method says so |
| R4B-14 The cap counted validation agents only | MINOR | Accepted | §1.3: three subagents of any kind, account-wide; no instrument shows the count, so each session caps its own and asks before a round |
| R4B-15 Pre-sitting work and A1's third ruling | MINOR | Accepted | Wave 0 intro: S0.9, S0.10 and the new S0.12 run before the sitting; step 1 lists A1's W0.1 timing |
| R4B-16 Round 4 recorded before it ran; three files missing | MINOR | Accepted | Status line; Validation record (round 4 entry, round 5 pending); "Changed by this plan" lists every report, reconciliation and script |
| R4B-17 Remaining bare references | NIT | Accepted | "Method (validation rounds 1–4)"; `EX/round3-laneB-attack.md`; `…equities-p0-executed-go-verdict-p1-next.md` named twice; "juniper-ml's `AGENTS.md`" |

## Unresolved dissent

None.

## Deviations

- **Round 4 ran one lane.** For a document of record with corrections, `…CONSENSUS-PROCEDURE.md` §3 calls for more. Round 5 therefore runs a Lane A, which re-derives the corrections and tests the rewritten tool, beside a Lane B.

## What this reconciliation cannot support

- That round 4's corrections introduced no new error. Round 5 is briefed on exactly that.
- Host state: whether the key condition holds, whether the running services have Sentry DSNs, and what canopy's deployed auth exposes.
- That the rewritten tool has no other way to fail open. Round 5's Lane A is asked to find one.
- Any state after 2026-10-05T12:05Z.
