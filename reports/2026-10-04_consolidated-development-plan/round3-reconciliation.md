# Round 3 — reconciliation of two lanes into plan v1.3.0

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.2.0 (sha256 prefix `68ba9e62dbc6c803`, rebuilt from v1.1.0 plus the saved diff and hash-verified) → v1.3.0.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 3 was briefed on round 2's corrections only.
- **Lane reports** (both in this directory): `round3-laneA-reprobe.md` and `round3-laneB-attack.md`.
- **Re-derivations** below ran on 2026-10-05 between 10:55Z and 11:15Z, read-only: GitHub REST on `main` of juniper-ml, juniper-cascor, juniper-recurrence, juniper-data and juniper-data-client; gitleaks-action at its pinned SHA `e0c47f4f`; gitleaks v8.30.1 on planted fakes in the session scratchpad. No secret was read or printed.
- **ID coverage**: v1.0 → v1.3 and v1.2 → v1.3 drop no ID, and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0). The tool counts 380 IDs: the 375, plus five of the six that validation added. Its two-digit pattern cannot see the sixth, `P2-R8`, which the plan places in Appendix A.
- **Lint**: the plan passes markdownlint-cli v0.42.0 (the pre-commit pin) with `.markdownlint.yaml`. One pre-existing MD001 (an H3 directly under the H1) was fixed.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Lane(s) | Re-derivation | Result |
| --- | --- | --- | --- |
| The default rules miss the passphrase class | B (R3B-01) | `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --config .gitleaks.toml`, rewritten to plant one token-class and one passphrase-class fake and to scan through an explicit config | Default rules: token 1/1, passphrase **0/1**. The tool's config (defaults plus the interim B9-class rule): 1/1 and **1/1**. juniper-ml's `.gitleaks.toml`: 0/1 and 0/1 (zero-rule). **Confirmed** |
| What B9 covers | B (R3B-01) | `…RECOVERY-PLAN.md` L227 | `(SETTINGS_ENCRYPTION_KEY\|PASSPHRASE(_OLD)?\|DUPLICATI_WEB_CREDENTIAL\|webservice-password\|passphrase)=` with a non-placeholder value. The interim rule is case-insensitive and also accepts `:`, so it is a superset; it does not filter placeholders, so it over-reports, which is the safe failure for a pre-push screen |
| juniper-data's cron publishes links to history hits | B (R3B-03) | data `ci.yml` on `main` L49–50 and L565; gitleaks-action `src/gitleaks.js` L103–116 and `src/summary.js` L30 at `e0c47f4f` | The cron is `0 6 * * *`. The action adds `--log-opts` only for `push` and `pull_request`, so a `schedule` run scans full history. The summary links each hit as `blob/<sha>/<file>#L<line>`. `GITLEAKS_ENABLE_SUMMARY` and `GITLEAKS_ENABLE_UPLOAD_ARTIFACT` turn both off (`src/index.js` L15–25). **Confirmed** |
| Cascor relays the same text | B (R3B-05) | cascor `main`: `src/api/lifecycle/manager.py` L4350–4353 and L4955; `src/api/routes/training.py` L129–130 and L337; `src/api/secrets.py` L35 and L42. data-client `main`: `juniper_data_client/client.py` L349–350 | The data client wraps a `RequestException` as `f"Request failed: {e}"`. Cascor wraps that as `f"juniper-data fetch failed: {detail}"`, raises it as a `RuntimeError`, logs it at WARNING and returns it in a 409 (`Training cannot be started: …`) or a 502 (`str(exc)`). The loader strips the `_FILE` form only. **Confirmed** |
| Recurrence relays it on three routes | A (R3A-03) | recurrence `main`: `routers/predict.py` L60–62, `routers/crossval.py` L74–76 | Both log `exc` at WARNING and raise `map_data_error(exc)`. **Confirmed** |
| The preflight's scope and overrides | A (R3A-04), B (R3B-09) | `util/experiment_stack.bash` and `util/isolated_stack.bash` on `main` | `run_env_preflight` is called from `recurrence_up()` only (experiment_stack L815–832; isolated_stack L434–438, and only with `--with-recurrence`). The overrides are `JUNIPER_EXP_SKIP_ENV_PREFLIGHT` and `JUNIPER_E2E_SKIP_ENV_PREFLIGHT`. **Confirmed** |
| Fleet drafts that touch §8's serialized files | B (R3B-09) | `gh api repos/pcalnon/juniper-ml/pulls/{2147,2149}/files` | ml#2147 edits `util/experiments/run_experiment.py` and `run_suite.py`; ml#2149 edits `util/experiment_stack.bash`, `util/isolated_stack.bash` and `util/recurrence_env_preflight.bash`. Both also edit `ci.yml`, `CHANGELOG.md` and `docs/REFERENCE.md`. Both are open `cursor[bot]` drafts. **Confirmed** |
| Which commit brought which P12 IDs | A (R3A-07) | The commit history of `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` on `main`, and each commit's added lines | `bba22f4a` (ml#2130) added F-P8, W5.8 and W5.9. `a0a120d5` (ml#2151, 22:31:33Z) added F-S10 and W1.14. **Confirmed, and refines R3A-07**: the plan's v1.2 credited all five to ml#2130 |
| The P12 handoff's owner order | A (R3A-08) | `…equities-p0-executed-go-verdict-p1-next.md` L32 and L34 | L32: the dates; R6; R2, R3, R7, R8; "R1 optional"; W5.8, W5.9 and W1.14. R5 follows the W5.1 review in item 3 (L34). DC-0.6, O8, O12 and P4-Q6 are not named. **Confirmed** |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.3.0 |
| --- | --- | --- | --- |
| R3A-01 A "patch" recurrence release would be cut from `main` as 0.6.0, P12's version | MAJOR | Accepted (with R3B-04) | §5: the R-RECURRENCE-SEC row is replaced by "F-S10's release vehicle", an owner ruling at §6 A1 between (a) 0.5.1 from the `juniper-recurrence-v0.5.0` tag, an exception to the clean-`origin/main` rule, and (b) the P12-chain release. §5 recommended order item 3; §9 row; XC-P12 action 2 |
| R3A-02 Phase 1 stalled behind R5 | MAJOR | Accepted | §4 Wave 2 P12 row ("M0 · Phase 1 → M1 · in parallel: the review → R5 → W5.4"); §2 P12 row; XC-P12 action 3; §7.1 item 11; §9 R5 row |
| R3A-03 F-S10 reaches three routes | MINOR | Accepted (with R3B-05) | Overview; S0.11 tests `map_data_error` itself and all three routes; §8 recurrence row |
| R3A-04 The preflight refuses recurrence legs only | MINOR | Accepted (with R3B-09) | §7.2: scoped to `recurrence_up()`; both override variables named; owner OK required |
| R3A-05 canopy#701 is `dirty` | MINOR | Accepted | XC-FLEET: "Fix: rebase onto `main`, resolving `CHANGELOG.md` (or close)" |
| R3A-06 "Padded" is the wrong condition | NIT | Accepted | "An env-var key with leading whitespace or a line break" in the Overview, S0.11, XC-CRED, §12's risk row and its "cannot support" list, and Appendix B row 10 |
| R3A-07 ml#2151 brought F-S10 and W1.14 | NIT | Accepted, refined | Documents table; §10 P12; Appendix A P12 (ml#2130 brought F-P8, W5.8, W5.9; ml#2151 brought F-S10, W1.14) |
| R3A-08 The handoff does not name DC-0.6 | NIT | Accepted | §6 Group B P12: DC-0.6 first; then L32's order less R6 and W1.14, which Group A rules; "R1 (optional)"; R5 after the review (item 3); then O8, O12 and P4-Q6 |
| R3A-09 ml#2151 merged inside round 2's freeze | NIT | Accepted | Validation record, round 2 |
| R3B-01 The pre-push scan misses B9's class, and the tool could load the scanned directory's config | BLOCKER | Accepted (re-derived) | The probe tool's `--scan-dir` now always passes an explicit config (defaults plus the interim B9-class rule). XC-PRESERVE method; §9 "Every public push" is permanent, with no lapse; a new §9 edge puts the scan before P1-09 and P1-10; §12 risk row; H-17 |
| R3B-02 Row k is transcripts | MAJOR | Accepted | XC-PRESERVE method: P1-09 archives the lane reports' final text, extracted from the transcripts; the transcripts never enter a repository (H-21) |
| R3B-03 XC-LEAKS is unordered, and data's cron would publish the links | MAJOR | Accepted (re-derived) | XC-LEAKS work table in order: the history scan (defaults plus B9, `--redact`, report to an owner-only `0600` path) → owner rotation → config PRs with B9 required, data's last, which turns off the summary and artifact for `schedule` → owner settings. Step 1 names its config source and says `--scan-dir` cannot scan history. New §9 edge |
| R3B-04 R-RECURRENCE-SEC is the P12 chain by definition | MAJOR | Accepted (with R3A-01) | As R3A-01 |
| R3B-05 The text is the data client's; cascor relays it; H-22 lapses early | MAJOR | Accepted (re-derived) | Overview; XC-P12 action 2 (the data-client source fix covers cascor once it runs the patched client; cascor's loader is unstripped); §6 A1; S0.11; §5 vehicle row; §7.1 item 3; §8 cascor and data-client rows; H-22 (every relay, bodies and logs, until the **running** services carry the fix); the metric now counts 3 leak paths; XC-CRED; §12 |
| R3B-06 Owner rulings with no slot | MAJOR | Accepted | Wave 0 sitting: step 1 rules A1, all of A2, A5's O13, A6 and A7; steps 2–7 are A3; step 8 rules A4, the rest of A5 and A8. A session drafts A6's set before the sitting. §6 Group A header; A5's note on O13 |
| R3B-07 Safety rounds were exempt from the cap; the arithmetic undercounted | MAJOR | Accepted | §1.3: at most three validation agents at once, account-wide; safety rounds obey the cap and only jump the queue. §7.1: 13–15 rounds, about 20–22 agent runs, five to eight days at two to three rounds a day or seven to fifteen at one to two, and at least four sittings. Scope & Timeframe |
| R3B-08 Three XC-FLEET rows were not dispositions; ml#2122 is mergeable | MAJOR | Accepted | XC-FLEET: every row is merge, fix, close or supersede, with an alternative; ml#2122 close |
| R3B-09 The draft metric counted drafts, not dispositions; §8 missed the fleet; the override was ungated | MINOR | Accepted | Metric: "42 open, none dispositioned"; §8 lists ml#2147 and ml#2149; §7.2 as R3A-04 |
| R3B-10 Re-probe additions sat under round 2; the drift exemption was unrecorded; "as of" overreached | MINOR | Accepted | Validation record: "added after round 2's freeze; round 3 checked them". Deviations: the drift exemption. Header and Deviations: "as of" covers the census's scope only |
| R3B-11 Bare references | MINOR | Accepted | Documents table rows for `pr2114.md`/`pr2115.md` and the ecosystem guide. Rewritten: "the W5.1 note" (seven places), "Step 8's text on `main`", "the handoff" (P6's D6 recount; P12's DC-0.6), "that design's §6.5", "(§11.1)", "the procedure's §4", "the spec's route citations" |
| R3B-12 *(v)* count; P6-34; OD-12 | NIT | Accepted | Six *(v)* IDs: W1.14 is P12's own (ml#2151), not a validation finding. XC-MEM restores P6 OD-12 and states P6-34 as the retirement ruling, which says to fix the gates first |

## Unresolved dissent

None. R3A-01 and R3B-04 proposed the same two options, and the plan leaves the choice to the owner.

## What this reconciliation cannot support

- That round 3's corrections introduced no new error. Round 4 is briefed on exactly that.
- Host state: whether `JUNIPER_DATA_API_KEY`'s env-var value ever had leading whitespace or a line break, where the running cascor reads it from, and which `requests` version each image carries.
- Whether any repository's history holds real hits.
- Any state after 2026-10-05T11:15Z.
