# Round 5 — Lane B (attack the round-4 corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-5 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round5-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` below) v1.4.0. sha256 prefix `2cc51727a5c2b272` at 12:05:23Z (start), at 12:35:10Z and at 12:38:30Z (end) on 2026-10-05, so it was unchanged. The lane ran 12:05Z–12:38Z. "Lnnn" is one of its lines; "tool Lnn" is a line of `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`; "procedure Lnn" is a line of `…CONSENSUS-PROCEDURE.md`. Other short forms are the ones `…CONSOLIDATED-DEVELOPMENT-PLAN.md` defines.
  - **Read**: the v1.3→v1.4 plan and tool diffs (session scratchpad); `round4-reconciliation.md`, `round4-laneB-attack.md`, `round3-laneB-attack.md` (R3B-01..05), `extraction-P9-ci-budget-P10-ci-tools.md` (P9-13) and `extraction-P5-partition.md` (version claims), all in this directory; the whole of `…CONSOLIDATED-DEVELOPMENT-PLAN.md`; the tool; `…CONSENSUS-PROCEDURE.md` §2–§4; `…RECOVERY-PLAN.md` L222–227; juniper-ml `pyproject.toml`, `.github/workflows/ci.yml` L1–60 and `juniper-observability/juniper_observability/sentry.py` at `cf711cf4`; the installed juniper-observability 0.4.0 `sentry.py` in `JuniperCascor1` (read-only).
  - **REST**, read-only GETs, 12:10–12:33Z: `…equities-p0-executed-go-verdict-p1-next.md` on ml `main` (it is not in this worktree); data-client `juniper_data_client/client.py`; recurrence's root listing, `juniper-recurrence/pyproject.toml`, `routers/_common.py`, `training.py`, `predict.py`, `crossval.py`, `settings.py` and `data.py`, plus code search; the root listings of ml, data, canopy and deploy; Actions runs by event (`schedule`, `workflow_dispatch`) for ml, data, canopy and deploy, their job and step names, and the public log of ml job 98348407419.
  - **Ran**: `grep`, `sed`, `ls`; one `python3 -c` on Python's exception-chaining semantics (synthetic string); one `python3 -c` that applied the B9-class regex and allowlist to the 35 files of this plan's PR, printing only names, lengths and positions. The scan tool was not run (Lane A's remit). No secret, `.env` file or transcript was read; there were no host actions.
- Entry point: the round-4 corrections (the v1.3→v1.4 diff and `round4-reconciliation.md`)

## Findings

| ID | Severity | Plan location (v1.4) | What the correction says | What it broke (evidence: file:line, command → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R5B-01 | MAJOR | L733–735; L109 | S rounds are 3–4 agents (procedure §3, L81–94); the floor is 11 rounds, 33 runs | The cited range holds the escalator: "a fix or revert hangs on it" moves the cell up (procedure L87, L93). Medium×High (L84) becomes top-right: 3+ Lane A, 2+ Lane B, at least two iterations (L85, L110). `round4-reconciliation.md` L20 says it "escalates". So the floor is 22 rounds and ≥110 runs | Size S rounds per the top-right cell; recompute totals, rate and timeframe |
| R5B-02 | MAJOR | L275, L284; §9 L817–818 | Only exit 0 passes; every other pre-push scan waits for this plan's PR | The PR fails its own gate: any line holding the tool's allow-marker string exits 2 (tool L247–252, L263). The string is at L284, `round4-reconciliation.md` L40 (verbatim, L1095) and tool L32, L81 (`grep -rln` → 3 files). Nothing clears a false positive, so every later push stalls | Owner triage for exit 2; build the constant from parts; reword the prose |
| R5B-03 | MAJOR | Note 2 L314; §9 L820 | Data's PR stops the scheduled scan or adds a `.gitleaksignore` of rotated fingerprints | The gate refuses any `.gitleaksignore` (tool L242–244 → exit 3), and exit 3 blocks the push (L275, L817), so that branch can never ship. The other drops the only scheduled history scan (H-17 L933) unremarked. Fingerprints also publish each hit's commit, path and line | Owner rules an exception for that file, or picks "stop the scan" and records the lost coverage |
| R5B-04 | MAJOR | §5 L591, L593; §9 L808, L811; S0.11 L465–467 | The vehicle row carries "a cascor fix if accepted" | Its options are recurrence releases ((a): 0.5.1 "with only the fix"); its Unblocks names recurrence only. R-CASCOR omits the fix, S0.11 has no cascor bullet, and §9 closes cascor only via R-DC-PATCH. A cascor fix accepted alone has no vehicle; with both, R-CASCOR can ship without it | Move it to R-CASCOR's Carries and Ready when; add an S0.11 bullet, a §9 edge and a trio step |
| R5B-05 | MAJOR | §1.3 L204–205; L448; §7.1 L735 | Three subagents of any kind, account-wide; a 3+ round runs alone; meanwhile each session caps its own at three | Not the same rule: 7–8 sessions (L203) × 3 is 21–24. The owner ask covers rounds only, yet P12 runs Phase 1 through task-executors, data and deploy in parallel (`…equities-p0-executed-go-verdict-p1-next.md` L36). L735 assumes rounds run alone | While a round runs, no other session launches subagents; say how P12's fan-out fits |
| R5B-06 | MINOR | L428, L430–446, L463 | S0.9, S0.10 and S0.12 come before the sitting | S0.10 feeds A8 and S0.9's A9 menu feeds A9, both at step 8, after the host steps; step 1 also holds non-host rulings (A1, A6, A7). So Phase C and Tier 2 wait on prep they do not use. S0.9 ("before the sitting … then the consensus review") can also hold the sitting for §7.1 item 11 | Host-gating rulings and steps 2–7 first; other prep only before step 8 |
| R5B-07 | MINOR | L165 | 4 known credential-leak paths | The Overview lists five: round 42's Sentry capture (L71), the recurrence, cascor and canopy relays (L79–81), and F-S10's chain into Sentry (L82, R4B-03). The row's "Sentry capture" is XC-SENTRY's (its source column), and R4B-03's disposition left the row alone | Count 5, or say the chain is counted with the relays |
| R5B-08 | MINOR | S0.11 L467 | `from None` (or a sanitized cause); a test walks `__cause__` and `__context__`, failing on the key | Inside `except`, `from None` keeps `__context__`: `python3 -c` → `cause: None`, `suppress_context: True`, `context: ValueError('carries FAKEKEY')`. The prescribed fix fails the prescribed test; Sentry stops at `__suppress_context__` (`round4-reconciliation.md` L17) | Raise outside the handler or clear `__context__`; or let the test honour `__suppress_context__` |
| R5B-09 | MINOR | L1231–1232 | Created: `round5-laneA-reprobe.md`, `round5-laneB-attack.md`, `round5-reconciliation.md` | None existed at v1.4.0's freeze (`ls` of this directory, before 12:35Z), and Lane A's file name is assumed. Same class as R4B-16 (a round recorded before it ran) | Mark them planned, or add them once written |
| R5B-10 | MINOR | Exit L525–533; §6 L624–646 | Wave 1 gains an "F-S10 delivery" block (L480–486) | The exit needs the fixes only "merged and validated": no patch cut, vehicle cut, R-CASCOR or environment upgrade. No §6 sitting holds the owner's upgrade and restart. Waves 0–1 can close with every F-S10 path live, against L165's target of 0 | Add the cuts and the running-service step to the exit; give the upgrade an owner slot |
| R5B-11 | MINOR | L480–486; §5 L594, L603; §9 L811 | Patch, then lock PRs, then the recurrence release and R-CASCOR, then the upgrade | Independent routes in series. The trio runs from conda environments (L74–75), so it needs the patch on PyPI and a restart, not R-CASCOR, which waits on P3-05 and P3-08 (L591). Recurrence's vehicle needs only step 1. "Pick up both" (L603) holds only if the patch beats R-OBS-SC's lock PRs | Split into trio, image and recurrence routes |
| R5B-12 | MINOR | L277 | Placeholders are skipped "by shape (`<name>`, `$VAR`, backtick-quoted text)" | The allowlist anchors only the start (tool L103–109): a value is skipped if it begins with `$`, `{` or `%` plus a letter, a backtick, or `example`/`your-`. So `$Tr0ub4dor…` is skipped, though tool L85 says a value starting with `$` "is still reported". Code reading; not run | Anchor both ends, and plant such a value in the canary |
| R5B-13 | MINOR | L298; L308–309; note 1 L313 | Step 1 scans with the tool's config; step 2 rotates those hits | Step 1 runs the tool's pinned v8.30.1 defaults, but data's cron and ml's dispatch run 8.24.3's (L298; job 98348407419's log). A hit only 8.24.3 finds reaches the public `-v` log unrotated. Whether the two sets differ on this history is unmeasured | Run step 1 under both versions, or pin the action's scanner to v8.30.1 in the step-3 PRs |
| R5B-14 | MINOR | L302; H-17 L933; note 2 L314 | Only data's daily cron scans history, so note 2 handles data alone | ml's CI has `workflow_dispatch:` (ml `.github/workflows/ci.yml` L55). Dispatched run 33020188744 ran `detect --redact -v --exit-code=2` with no `--log-opts`: "2157 commits scanned". After ml's config PR, each dispatch prints every history hit and fails. Canopy and deploy have dispatched CI too (last April–May); not checked | Extend note 2 to ml; check canopy and deploy |
| R5B-15 | MINOR | L1205; L1209–1217 | Round 5 is one Lane A and one Lane B | A document of record whose corrections rewrote an instrument that had been wrong is the top-right cell (procedure L85, L91): 3+ A, 2+ B, at least two iterations. That is below even L733's 3–4. `round4-reconciliation.md` L71 notes a shortfall; the plan's Deviations do not | Record the deviation, and plan a sixth round |
| R5B-16 | NIT | L388 | A fix reaches a running service "only through §5's delivery steps" | The steps are §4 Wave 1's "F-S10 delivery" (L480–486); §5 holds rows | Point to §4 |
| R5B-17 | NIT | L1199; L492 | "recurrence `pyproject.toml:54`" | Recurrence has no root `pyproject.toml` (root listing on `main`); the cap is `juniper-recurrence/pyproject.toml:54`, as `round4-reconciliation.md` L22 says. L492's `:97`/`:106` lack the directory too | Add `juniper-recurrence/` |
| R5B-18 | NIT | S0.11 L466 | "`map_data_error` … raises without chaining" | It returns an `HTTPException` (`routers/_common.py:36–55`). The routes chain it (`raise map_data_error(exc) from exc`) and log `exc` at WARNING a line earlier: `training.py:59–60`, `predict.py:61–62`, `crossval.py:75–76` | Name the three raise sites |
| R5B-19 | NIT | L109; L738 | Waves 0–1 take two to four weeks | §7.1's last bullet makes the slow case "four weeks or more" | One bound in both places |
| R5B-20 | NIT | A9 L636 | Report: `…equities-p0-executed-go-verdict-p1-next.md` L32, L35 | That handoff never names DC-0.6 (v1.3's Group B said so); its source is §5 and `EX/round1-laneA2-residue-P4-P5-P11-P12.md` A2-02. A9's Unblocks also omits P5 W10 (§9 L827) | Cite §5 for DC-0.6 |

There are no BLOCKER findings: the table holds 0 BLOCKER, 5 MAJOR, 10 MINOR and 5 NIT.

## Corrections checked and sound (short)

- **The sitting.** A1–A9 each have exactly one slot in Wave 0 (A5 is split on purpose; A2's O-6 waits by its own text). The mid-wave, Group B and Group C lists repeat none of them. A9 plus Group B's P12 list equals v1.3's Group B P12 list, so nothing was dropped. A9 sits at step 8, after the host steps.
- **DC-0.6** is at A9 wherever it appears (L611, L636, L812; L595 and L827 name no group). The Overview and Appendix A do not mention it.
- **A9 against `…equities-p0-executed-go-verdict-p1-next.md`.** L32 gives the order (dates, R6, R2/R3/R7/R8 before W1.4/W1.8/W1.2/W1.3, R1 optional, W5.8, W5.9, W1.14); L34 is item 3 (R5); L35 opens Phase 1 with W1.4 (R2), W1.3 (R8) and W1.2 (R7); L36 puts W1.13 last. The plan matches.
- **Caps.** ml's `[recurrence]` `<0.6.0` is `pyproject.toml:105`; recurrence's data-client `<0.6.0` is `juniper-recurrence/pyproject.toml:54`.
- **§7.1's sums are internally consistent.** 1+1+1+1+1+3+1+1+1 = 11 first rounds; 22×3 = 66, 22×4 = 88, 11×3 = 33; 22 rounds take 8 days at three a day and 22 at one. R5B-01 disputes the cell, not the sums. The procedure ranges (L81–94, L104–110) are where the plan says.
- **The hard-coded `-v`**, corroborated a second way: ml's dispatched job 98348407419 ran `detect --redact -v --exit-code=2 --report-format=sarif` on scanner 8.24.3.
- **XC-LEAKS step 4's independence** holds, because the alerts are private.
- **No root `.gitleaksignore`** exists on `main` in ml, data, canopy or deploy, so step 1's history scans are not silently baselined today.
- **F-S10 at its source.** Data-client `client.py` L349–351 wraps the `RequestException` text and chains `from e`, and its env-var key path is unstripped (L89). Recurrence's routes log `exc` at WARNING and chain `from exc`. Its settings read the unprefixed `JUNIPER_DATA_API_KEY` through `get_secret` (`settings.py` L221–234), so W1.14's loader refusal covers that path too.
- **Sentry's other channels.** Installed observability 0.4.0 keeps frame locals on and sets `enable_logs=True`. Both carry the same key text, so the text fix closes them along with the chain. The unreleased `sentry.py` at `cf711cf4` turns frame locals off.
- **This plan's PR against the B9-class rule alone**: one B9-shaped match in 35 files (`round3-laneB-attack.md` L22), skipped for its leading backtick. R5B-02 is the only gate failure found.
- **Stale forms.** None of "about two weeks" (except L1189's history), "13 to 15", "one lane each", "A1–A8", "3 paths" or "recorded in the Validation record" remains. L7 and L1205 call round 5 pending.
- **Naming.** Round 4's additions carry filenames or defined short forms, except R5B-16 and R5B-17.
- **The Deviations record** agrees with the new cap: ten, seven and two concurrent agents exceeded it, as L1211 says.
- **Citations.** R3B-03 (L304) is the summary-links finding. B9 is at `…RECOVERY-PLAN.md` L227, and the interim rule's names are a superset of B9's.

## Could not check

- **gitleaks-action's source at `e0c47f4f`** (`src/gitleaks.js` L96, `src/summary.js` L30), because of the command-hygiene rule. The `-v` flag was corroborated from a public job log instead.
- **Version behaviour**: whether gitleaks 8.24.3's and v8.30.1's default rules differ on these histories (R5B-13), and whether 8.24.3 honours the `[[rules.allowlists]]` block that the step-3 configs would copy from the tool. If it does not, CI would flag placeholder lines.
- **Canopy's and deploy's current gitleaks triggers.** Their workflow files were not fetched, because of the command-hygiene rule.
- **Host state**:
  - the key condition;
  - the services' DSNs;
  - whether the trio's cascor runs from the primary checkout or from an installed wheel (this shapes R5B-04's and R5B-11's trio route);
  - whether any recurrence service is running.
- **Canopy's own data-client calls** as a further relay. Code search shows canopy reads `JUNIPER_DATA_API_KEY` in `src/settings.py`, `src/secrets_util.py` and others; not traced.
- **Tracked root `.env.*` files** in canopy (`.env.dev`, `.env.prod`) and deploy (`.env.demo`, `.env.observability`, `.env.local.poc-backup`), seen only by name in a contents listing and not opened. XC-LEAKS step 1 would cover them.
- **Facts left to Lane A**: the scan tool's behaviour (it was not run here), the canopy and cascor line citations, and the `--skip-env-preflight` sites.

## What this report cannot support

- **Severities are judgement.**
  - R5B-01 reads the procedure's escalators as applying to the S rounds' base cell, as `round4-reconciliation.md` L20 does.
  - R5B-05's weight depends on how sessions launch their work.
- **The evidence behind some findings.**
  - R5B-13 is a risk, not a measured divergence.
  - R5B-02, R5B-03 and R5B-12 come from reading code and from `grep`, not from running the tool.
- **That the corrections introduced no other error** outside the lines named here.
- **State after 2026-10-05T12:38Z.**

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round5-laneB-attack.md`. The REST outputs went to the session scratchpad, outside every repository.
