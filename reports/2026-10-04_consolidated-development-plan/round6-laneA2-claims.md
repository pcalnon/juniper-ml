# Round 6 — Lane A2 (re-derive round 5's claims)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-6 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round6-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` below), v1.5.0. Its sha256 prefix was `17a9c12de47992c2` at 13:11:53Z (start) and `17a9c12de47992c2` at 13:37:42Z (end) on 2026-10-05, so it did not change. "Lnnn" is a line of it. Other short forms are the ones it defines.
  - **Read locally**:
    - the v1.4→v1.5 diff (session scratchpad);
    - in this directory: `round5-reconciliation.md`, `round5-laneA-reprobe.md`, `round5-laneB-attack.md`, `round1-laneA2-residue-P4-P5-P11-P12.md` and `extraction-P1-backup.md`;
    - all of `…CONSENSUS-PROCEDURE.md`, and `…RECOVERY-PLAN.md` L227 and L243–308;
    - `juniper-service-core/` in this worktree;
    - the scan tool's source, with two `grep`s only. It was not run; its sha256 prefix is `5ed0da7dd84e8523`.
  - **Installed packages, read-only**:
    - `JuniperCascor1`: sentry-sdk 2.58.0, juniper-observability 0.4.0, juniper-service-core 0.5.0, and the editable-install finder files;
    - `JuniperCanopy1`: a listing only.
  - **REST**: read-only `gh api` GETs, on `main` unless noted.
    - recurrence: `routers/{training,predict,crossval,_common}.py`, `app.py`, `main.py`, `logging_config.py`, `settings.py`, `data.py`, `juniper-recurrence/pyproject.toml`, `publish-image.yml`, tags;
    - cascor: `src/api/routes/training.py`, `src/api/secrets.py`, `src/api/lifecycle/manager.py`, `src/api/app.py`, `src/main.py`, `src/api/observability.py`, both locks, `Dockerfile`;
    - canopy: `src/backend/cascor_service_adapter.py`, `src/outbound_errors.py`, `src/observability.py`, `src/main.py`, `pyproject.toml`, `ci.yml`;
    - data-client: `client.py`, `exceptions.py`, `pyproject.toml`;
    - ml: `pyproject.toml`, `ci.yml`, and `…equities-p0-executed-go-verdict-p1-next.md`;
    - data: `ci.yml`. deploy: `ci.yml`, `docker-compose.yml`;
    - gitleaks-action: `src/index.js` and `src/gitleaks.js` at `e0c47f4f`;
    - gitleaks at v8.30.1: `config/gitleaks.toml`, `config/config.go`, `detect/detect.go`, `cmd/root.go`, `sources/{git,file,files}.go`. At v8.24.3, their counterparts;
    - code search.
  - **Ran**: only `grep`, `sed`, `ls`, `cat`, `sha256sum` and `date`.
  - **Not read**: no secret, `.env` file, credential file or transcript. There were no host actions.
- Entry point: the round-5 corrections (the v1.4→v1.5 diff and `round5-reconciliation.md`)
- Sample: 78 claims from the added and changed lines. 66 hold, and 12 do not hold in full. They are reported as 11 findings: 0 BLOCKER, 1 MAJOR, 8 MINOR and 2 NIT.

## Findings

| ID | Severity | Plan location (v1.5 "Lnnn") | Claim | Re-derived (command / file:line → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R6A2-01 | MAJOR | L497; L608; L659; L826 | Trio route: "R-DC-PATCH on PyPI", then an env upgrade; "`JuniperCascor1` holds data-client 0.5.0" | It holds data-client 0.5.0 and cascor 0.11.0 as editable installs of the primary checkouts (finder L9). The trio runs those at restart: PyPI is not its input, pip says 0.5.0 whatever they hold, and a sync past W1.4 skips the `<0.6.0` caps | Name them. Sync to the fix (never past W1.4) and restart, or swap in the 0.5.1 wheel; verify code, not version |
| R6A2-02 | MINOR | L82 | "Every hop re-raises … and Sentry records the whole chain"; the log lines above "reach Sentry as log records" | Recurrence has no Sentry init (`app.py`, `main.py`, `settings.py`). Canopy returns the text and does not raise (adapter L1114–1116). Only a 5xx `HTTPException` is captured (`integrations/__init__.py` L12), so cascor's 409 reaches Sentry only by its L129 WARNING | Per service: cascor's 502 chain and log lines; canopy's ERROR line. Recurrence: none |
| R6A2-03 | MINOR | L482; L956 | Cascor relays to fix: `manager.py:4353`, `:4955`; `training.py:129–130`, `:337`; H-22: cascor logs at WARNING | Also `manager.py` L189–195 (WARNING with `exc`; flag on, caller silent) and `app.py` L589–591 (ERROR, and `auto_start_failure` in a 200 status body, `manager.py` L3361, which H-22 omits). A loader returning None lets data-client re-read the raw env var (`client.py` L213, L88) | Fix L189–195 too; add the status body to H-22; the loader must raise |
| R6A2-04 | MINOR | L319; unchanged L307, L949 | Rescans: data's `schedule`, ml's `workflow_dispatch`; canopy and deploy are "checked in their own step-3 PRs" | All four run the action on `workflow_dispatch`, a full-history scan (`index.js` L176; no `--log-opts`, `gitleaks.js` L103–117): canopy `ci.yml` L53 (guard L508), deploy L41 (job L101), data L51 besides cron L49–50, ml L55. L307 and H-17 still say only data's cron | List all four; option (b) must stop dispatch too; fix L307 and H-17 |
| R6A2-05 | MINOR | L324 | CI inherits "the scanner's 100,000-byte read chunks" | CI runs `detect` in git mode, which scans each hunk's added lines whole (v8.30.1 `sources/git.go` L394–402; 8.24.3 `detect/git.go` L53–59). The 100 kB buffer belongs to the file source (`sources/file.go` L21, L204–232), so it binds the local `--scan-dir` gate, not CI. The allowlist half holds in both versions | Drop the chunk half for CI |
| R6A2-06 | MINOR | L440 | Step 1 holds "the rulings the host steps need": all of A2, plus O13 | The Gates column of `…RECOVERY-PLAN.md` §6.6 (L295–308): O-2 → D step 7, O-7 → D, O-8 → B, O-12 → B. Only O-10 → C. `EX/extraction-P1-backup.md` L65–79 agrees (P1-10, P1-18). So four of A2's seven gate Phase B or D, not a Wave 0 host step | Retitle step 1, or move O-2, O-7, O-8 and O-12 to step 8, so that deferring one never holds Phase C or Tier 2 |
| R6A2-07 | MINOR | L748 | "a fix … hangs on it" moves an item up a cell. "So these items sit in the top cell" | `…CONSENSUS-PROCEDURE.md` L87 and L93: each escalator moves one cell. One escalator reaches the top cell (L85) only from Medium uncertainty. From Low it gives Medium × High: 2 A + 1–2 B (L84). The plan states no base row. The top cell holds where a second escalator applies (a universal quantifier; an instrument that was wrong before) | State each item's base row and its escalators |
| R6A2-08 | MINOR | L749 | The de-escalator can lower an item; "The XC-LEAKS configs are the likely case, because the probe tool reproduces their detection end to end" | Procedure L96–97 require "a different instrument". The probe tool made the XC-LEAKS measurement (plan L86) and was wrong twice (R4B-01, R5A-01), an escalator (procedure L91). Applied, it breaks L749's "at least 22 rounds and 110 agent runs" | Drop the example or name a different instrument; keep XC-LEAKS in the top cell |
| R6A2-09 | MINOR | L109; L745–753 | Waves 0–1 take "three to five weeks", and the rounds are "the binding constraint" | §7.1's own figures give 22 rounds in 11–22 days, which is 1.6–3.1 weeks. "Three weeks needs two rounds a day" leaves 10 of 21 days unaccounted for. Five weeks at one round a day leaves 13 of 35. §7.1 names nothing that fills them | Name what fills the gap (fix authoring between rounds, sittings, merges), or restate the range from the rounds |
| R6A2-10 | NIT | L285 | "a line over 60,000 bytes. The scanner would skip each of these silently" | The scanner reads a long line, in 100 kB chunks cut at a safe boundary (`sources/file.go` L21, L210–212). It can split a value but does not skip the line. The 60,000 figure is the tool's margin. Symlinks, binaries and empty files are skipped at debug level (`files.go` L88, L103–106; `file.go` L204) | "…would read it in pieces, and may miss a value cut at a chunk boundary" |
| R6A2-11 | NIT | L318 | Run `b9.toml` under 8.24.3 too, "because a hit that only CI's 8.24.3 finds would otherwise reach the public log unrotated" | Step 3 sets `GITLEAKS_VERSION: 8.30.1` in the same PR that adds the rules, and `index.js` L138 reads it. So CI never runs 8.24.3 with rules unless they land without the pin | Say that the 8.24.3 scan covers a step-3 PR merged without the pin |

There is no BLOCKER.

- **R6A2-01 does not leak a credential.** If the owner upgrades with pip, the wheel replaces the editable install and the fix arrives. It is rated MAJOR because §9's "Hard" edge and the mid-wave timing rest on a premise the environment contradicts.
- **The trio's exposure to an unreleased data-client** comes from the primary checkout's HEAD, which no cap or cut order governs.

## Checked and holds (short)

66 claims, grouped by source.

- **Recurrence `main` (5).**
  - The raise sites are `routers/training.py:60`, `predict.py:62` and `crossval.py:76`. Each is `raise map_data_error(exc) from exc`.
  - The WARNING lines are one line above each: L59, L61 and L75.
  - `map_data_error` returns an `HTTPException` (`routers/_common.py` L36–55).
  - The header error lands in its catch-all 502. Data-client wraps it as `JuniperDataClientError`, a plain `Exception` (`client.py` L349–351; `exceptions.py`).
  - The bench caps are `<0.17.0`, at `juniper-recurrence/pyproject.toml:97` and `:106`.
- **Cascor `main` (6).**
  - `src/api/secrets.py:42` returns the env value unstripped, although its docstring says "stripped".
  - `manager.py` L4353 and L4955, the latter raising `from exc`.
  - `routes/training.py` L129 (WARNING) and L130 (the 409, `from e`).
  - `routes/training.py` L337 (the 502, `from exc`).
  - H-22's named log lines exist.
  - The key comes from that loader (`manager.py` L4922).
- **Canopy `main` (1).** The adapter's L1114–1116 logs at ERROR and returns `outbound_error_text(e)`. `outbound_errors.py` L61 passes `str(exc)` for any integer status.
- **Sentry (5).**
  - Installed observability 0.4.0 sets `enable_logs=True` (`sentry.py` L71).
  - Its `before_send` scrubs three request headers and nothing else (L23–37).
  - sentry-sdk 2.58.0 sends every INFO+ record, on any logger, as a Sentry log (`integrations/logging.py` L28, L126, L162–195, L394–407). That is the channel XC-SENTRY (a) must cover. Both cascor (`app.py` L335; `main.py` L244) and canopy (`main.py` L312, via `observability.py` L58–80) reach it, and `JuniperCanopy1` also holds observability 0.4.0.
  - S0.11's chain walk is sentry-sdk's (`utils.py` L818–821, used at L999).
  - `raise … from None` keeps the original on `__context__`, and that walk skips it.
- **Data-client (2).**
  - `client.py` L349–351 chains `from e`.
  - `main` and the primary checkout are both at 0.5.0 (`pyproject.toml` L7), so a 0.5.1 patch is coherent.
- **Locks, images, deploy (6).**
  - Cascor's `requirements.lock` L57 and `requirements-cpu.lock` L120 pin `juniper-data-client==0.5.0`.
  - Cascor's `Dockerfile` L41–42 installs the cpu lock.
  - Recurrence's `publish-image.yml` fires on `release: published`.
  - Deploy's `docker-compose.yml` runs `juniper-recurrence` (L589) at `:0.5.0` (L598).
  - Deploy runs cascor at `:0.11.0` (L233, L427).
  - The tag `juniper-recurrence-v0.5.0` exists.
- **Caps (3).**
  - Recurrence `juniper-recurrence/pyproject.toml:54` caps data-client `<0.6.0`.
  - Canopy `pyproject.toml:192` caps data-client `<0.6.0`.
  - ml `pyproject.toml:105` caps `juniper-recurrence<0.6.0`.
- **gitleaks-action at `e0c47f4f` (5).**
  - `src/index.js` L138 defaults `GITLEAKS_VERSION` to 8.24.3.
  - `src/gitleaks.js` L79 builds `v${version}`, so `8.30.1` without a `v` is the right form.
  - The `-v` flag is at L96.
  - `workflow_dispatch` and `schedule` scan full history (`index.js` L176). Data's cron (`ci.yml` L49–50) and ml's dispatch (`ci.yml` L55) both do.
  - Fingerprints are `commit:file:rule:line` (v8.30.1 `detect.go` L714; 8.24.3 L581).
- **gitleaks scanner (7).**
  - The default global allowlist is `(?i)^true|false|null$` (v8.30.1 `config/gitleaks.toml` L52; 8.24.3 L19). It drops a value that starts "true", contains "false" or ends "null".
  - `[extend]` imports that allowlist: v8.30.1 `config.go` L487, and 8.24.3's `extend()` appends the regexes. So CI inherits it.
  - `--ignore-gitleaks-allow` exists (`root.go` L85; `detect.go` L510).
  - `--max-archive-depth` defaults to 0 (`root.go` L92), and symlinks are skipped (`files.go` L103–106).
  - Secret-group selection is the same in both versions (v8.30.1 L521–539; 8.24.3 L442–458).
  - 8.24.3 parses `[[rules.allowlists]]` with `regexTarget` (`config.go` L41–58, L148–155), so note 1's 8.24.3 run of `b9.toml` loads. This answers an open question in `round5-laneB-attack.md`.
  - A part under 60,000 bytes fits the 100 kB buffer (`file.go` L21).
- **B9 and juniper-ml's forms (3).**
  - B9 is `(SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password|passphrase)=` (`…RECOVERY-PLAN.md` L227).
  - That `NAME=` form misses the quoted, spaced, suffixed and table forms.
  - juniper-ml's files use all four (`grep -l`, names only): table cells in 3 files, suffixed names in 11, and quoted keys or a spaced flag in 21.
- **The tool's step-1 configs (1).** `defaults.toml` and `b9.toml` are written to `--workdir` (tool L343).
- **The procedure (3).**
  - The top cell (L85) is 3+ Lane A, 2+ Lane B and at least two iterations. L110 makes that cell a trigger for a second round.
  - The escalator wording at L87 and L93 is quoted faithfully.
  - §4 is L104–110.
- **`…equities-p0-executed-go-verdict-p1-next.md` on ml `main` (4).**
  - L32's order ends with W1.14.
  - L34 is item 3, which comes before R5. That supports S0.9's "gates only R5".
  - L35 gives Phase 1's order.
  - L36 names P12's parallel task-executors.
- **§7.1 arithmetic (4).**
  - 1+1+1+1+1+3+1+1+1 = 11 items.
  - 11 × 2 = 22 rounds, and 22 × 5 = 110 runs.
  - 22 rounds at two a day or one a day take 11–22 days.
  - Under a three-agent cap, a 3 A + 2 B round runs in two batches.
- **Other arithmetic and structure (5).**
  - The metric's 5 = 1 + 3 + 1.
  - 21–24 subagents = 7 × 3 to 8 × 3, and the ecosystem guide says seven to eight sessions.
  - Each of A1–A9 has one Wave 0 slot, and S0.9, S0.10 and S0.12 precede step 8.
  - `…RECOVERY-PLAN.md` §6.3's "In this order" covers steps 1–9 (L245–256).
  - A9's A2-02 citation is the DC-0.6 cap-width finding.
- **Validation record (5).**
  - Round 5's sha256 prefix and its 12:04Z–12:52Z window.
  - The 54 claims and 24 gate tests.
  - The finding counts: 3/7/4 and 5/10/5.
  - Every finding accepted.
  - Rounds 2–5 ran two, two, one and two agents.
- **XC-P12's pointer (1).** The Wave 1 "F-S10 delivery" routes exist (L495–499).

## Could not check

- **The live `:8202` cascor.** Which interpreter it runs. The plan and `…equities-p0-executed-go-verdict-p1-next.md` L33 say `JuniperCascor1`; `/proc` was not read. R6A2-01 rests on that.
- **Host state**:
  - whether the data API key meets the F-S10 condition;
  - the services' DSNs;
  - whether cascor's auto-start and its truncation flag are on;
  - whether the primary checkouts are synced past any P12 commit.
- **Sentry server-side**: whether its scrubbing rules apply to Sentry Logs (XC-SENTRY (a)).
- **The deployed stack's keys file.** It hands each consumer the data service's keys file (`docker-compose.yml` L274, L614, L714). The loaders strip a file value, so leading whitespace cannot survive. An interior line break, such as two keys one per line, would. The file's format was not read.
- **Frame locals.** Observability 0.4.0 leaves `include_local_variables` at its default. Whether any frame on cascor's 502 path holds the key text was not traced.
- **The scan tool's behaviour**, which is Lane A1's remit. Its source was read only for two file names.

## What this report cannot support

- **Severities are judgement.**
- **Coverage of time.** Code was read on `main` between 13:11Z and 13:37Z. Images, PyPI wheels and running services were not read.
- **Other errors.** That round 5's corrections introduced none outside the 78 claims sampled.
- **The other lanes' findings.** This lane ran without them.
- **Code search as a census.** It returned no hit for `auto_start_failure` in cascor's `manager.py`, which has one at L3361. So every zero-hit claim here was confirmed by reading the files.

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round6-laneA2-claims.md`. The REST outputs went to the session scratchpad (`r6a2_*`), outside every repository.
