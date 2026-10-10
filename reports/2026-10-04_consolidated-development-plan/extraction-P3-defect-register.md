# Extraction — P3 defect register round 42

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:52Z–21:06Z UTC. juniper-ml `main` = `cf711cf4` = this worktree's HEAD (REST `commits/main`), so local reads of juniper-ml are reads of `main`. Other repos were read through the GitHub REST contents, compare, pulls and refs APIs at `ref=main`, plus PyPI JSON. No GraphQL, no scripts, no tests.

Abbreviations: "consolidated" = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`; "governing" = `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`; "register" = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; "R42/" = `reports/2026-09-24_defect-register-round-42/`.

## 0. Sources read

- **consolidated**: read in full (L1–413).
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: read in full.
- **governing** (`HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`): read in full (L1–641, Appendices A–J).
- `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`: read in full (L1–238).
- **register**:
  - L87–186 (§1 park shapes, §2 status);
  - L764–803;
  - all 136 §4 table rows, parsed by an inline one-liner into ID, Sev and FIXED status;
  - rows L1283–1307;
  - notes L1310–1316, L1428–1432, L1466–1479 and L1595–1639 (the park block).
- `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`: L4738–4746 only.
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: grep for F-CANOPY-05x/06x only.
- R42/ (87 entries listed):
  - `pending-items-snapshot-2026-09-24T1110Z.md` (full);
  - `canopy685-implementation-report.md` L63–74;
  - `bytes-compare-ml2086-data440-cascor689-validation.md` L1–93;
  - `cascor690-implementation-report.md` L38–50, and `cascor690-fixup-implementation-report.md` by grep;
  - `data428-round3-laneA1-security.md` (findings headings);
  - `data438-fixforward-pr-draft.md` (L1, headings, L139–182);
  - the three `*-STOPPED-partial.md` files (full; history, no open work).
- P2:
  - `HANDOFF_2026-10-03_canopy-consolidated.md` L52–53, L84–91, L120–175;
  - `HANDOFF_2026-10-04_canopy-replay-player-fixed-and-live-verified-p2-items-2-to-7-next.md` L30–49;
  - `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md` L118–132.
- P4: `HANDOFF_2026-10-03_release-and-distribution-consolidated.md` L38–47 and L64.
- P7: `HANDOFF_2026-10-03_logging-arc-consolidated.md` L97 (grep).
- P6:
  - `HANDOFF_2026-10-03_perf-lane-consolidated.md` L1, L54–56, L71 and L126–137;
  - `HANDOFF_2026-09-24_perf-lane-helper-binds-axis3-run-d6-control-micro-cut.md` (the data#432 lines).
- `HANDOFF_2026-09/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`: §0 (L80–279).
- Code on `main`, read but not run:
  - juniper-observability: `CHANGELOG.md` L9–72, `sentry.py`, `tests/test_sentry.py`;
  - juniper-service-core: `CHANGELOG.md`, `tests/test_security.py`, `security.py`;
  - juniper-ml: `tests/test_service_fork_drift.py` L200–212, `docs/REFERENCE.md` (grep), `pyproject.toml`.
- **Not read:**
  - document 1 (`HANDOFF_2026-09/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-…`): the governing source's Appendix I maps every item in it, and that mapping was validated in four rounds;
  - the other Lane F reports, the handoff-validation reports, and `owner-rulings-verbatim.md` / `owner-ruling-key-leaks-verbatim.md`, which are records only.
- Nothing failed to open.

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P3-00 | Get the owner's merge grant in THIS session; ask the non-release item-10 questions in the same turn | consolidated L35, L50–51 | [NOT RE-PROBED — a grant cannot be probed; no handoff carries one] | OWNER-ACTION | — | all | S | UNBLOCKER |
| P3-01 | Run data fix-forward pre-PR round 2 (two lanes) on `94ce8b1f`: `d1c66a11..94ce8b1f` in full, `0f0f7e0e..94ce8b1f` for regressions, and the trial merge with `main` | L39–40, L133–172 | [VERIFIED 2026-10-04: ref → `94ce8b1f`, signed, waiver in body; `pulls?head=` → `[]`; compare → ahead 2 / behind 6, diverged; the only overlap with `main` is `CHANGELOG.md`; no `data438-fixforward-round2*` report; worktree HEAD on the branch, untouched since 10-01] [CHANGED SINCE HANDOFF: behind 4→6 (data#444, #445)] | STARTABLE | — | juniper-data, juniper-ml | M | DATA-INTEGRITY |
| P3-02 | If round 2 refutes, or corrections are applied pre-PR: brief a task-executor for ONE signed commit (correct the old briefs' `--expected-head` and their DSN "unset"), then run round 3 | L174–179 | [VERIFIED 2026-10-04: `ls` → the executor transcript, the 4 tmpfs spec files and `primer-venv` still exist] | BLOCKED-ON P3-01 | P3-01 | juniper-data | M | DATA-INTEGRITY |
| P3-03 | Open the data PR from the draft (literal title; add the round-2 report names); merge with `safe_merge`, keeping the `Allow-Symbol-Loss:` line; update-branch | L181–183 | [VERIFIED: draft on `main`; no PR] | OWNER-ACTION (merge) | P3-00, P3-01/02 | juniper-data | S | UNBLOCKER |
| P3-04 | Archive the round-2+ reports with the archiver (`SESSION_IDS`, `MISSING`, new `HEADER` date) into the closes PR or its follow-up | L115–121, L180 | [VERIFIED: none exist] | BLOCKED-ON P3-01 | P3-01, P3-11 | juniper-ml | S | HYGIENE |
| P3-05 | Validate cascor#690 post-merge at `0fbb447a` with two lanes (scratch juniper-data via the serve script), then fix forward in a NEW PR | L41, L192–199 | [VERIFIED 2026-10-04: merged 2026-09-25T02:06:36Z `0fbb447a`; no `cascor690-validation*` report] | STARTABLE | — | juniper-cascor | M | USER-FACING |
| P3-06 | Validate canopy#685 at `dc5ea02e` from a fresh tree with two lanes; fix forward in a NEW PR, folding in the stale comment and any D-04 call | L42, L200–204 | [VERIFIED: merged 09-24T23:24:14Z; no report; `src/tests/unit/backend/test_cascor_service_adapter_gate_coverage.py:49-50` still says "only the stub client is installed"] | STARTABLE (D-04 can change scope) | D-04 | juniper-canopy | M | SAFETY |
| P3-07 | juniper-ml F-PR: F2 `before_send_transaction` + test; F6 `in_app: False` frames + wire test; F9; F10; service-core F3 spy + F5 surrogate pair. Two lanes; F2 validated BEFORE it reaches a branch | L43–44, L207–221 | [VERIFIED at `cf711cf4`: `before_send_transaction` count 0; `in_app` count 0 in `test_sentry.py`; svc-core `_ENCODING_PROBES` (`:101`) has no pair and there is no spy; svc-core `CHANGELOG.md:58` "closes 4001"; observability `CHANGELOG.md:64` sentence present] | STARTABLE | P3-00 (merge) | juniper-ml | M | SAFETY |
| P3-08 | cascor F-PR: F3 spy; F4 (`src/tests/conftest.py`, after `import sysconfig` `:37`, three DSNs = `""`); F5 pair; F7 subprocess test (waiver in a COMMIT body); F9. F4 validated pre-branch | same | [VERIFIED: conftest has no SENTRY line; `test_api_security.py:31` lacks the pair; F7 still the AST `_sentry_init_calls`; `CHANGELOG.md:594` "closes 4001"] | STARTABLE | P3-00 | juniper-cascor | M | SAFETY |
| P3-09 | data F-PR: F3 spy marked `unit` (`TestAPIKeyAuth` `:37` is unmarked) + F5 pair; open after P3-03 merges (shared `[Unreleased]`) | L43, L173, L218 | [VERIFIED: `:34` lacks the pair; existing spy `:177-199` unmarked] | BLOCKED-ON P3-03 | P3-03 | juniper-data | S | SAFETY |
| P3-10 | Validate #2088's delta `990ef3f9..2439d049` (two lanes, checklist L271–274); archive; fix forward before, inside, or after the closes PR | L45, L268–275 | [VERIFIED: both commits exist; #2088 head `1f116c38`; no report] | STARTABLE | — | juniper-ml | M | HYGIENE |
| P3-11 | Open the closes PR: file APD-ECO-013/-014 and APD-CASCOR-014 OPEN; APD-DATA-055 update; the Key-leaks quote; residue (see note 1); owner answers; cite the Lane F reports | L46, L233–262 | [VERIFIED: grep for the 3 ids → 0; register last commit `5af9d722` (09-24); own parse → 136 rows / 36 not FIXED] [NOT RE-PROBED: crosscheck "AGREE" (script not run)] | STARTABLE | — | juniper-ml | M | SAFETY |
| P3-12 | data428 round-3 A1 F2 (8,192-byte cap parsed under `_version_lock`) and F4 (header limits): file or decline each, with a reason | L257 | [VERIFIED: register grep → 0] | STARTABLE | P3-11 | juniper-ml, juniper-data | S | HYGIENE |
| P3-13 | Close rows only as their gates clear; validate each closing PR before it reaches a branch; refresh stale row prose | L235–239 | [VERIFIED: every gate still shut (§1b); L1297 still says #690 "open"; L788/800/803 say "PyPI still served 0.15.0"] | BLOCKED-ON P3-03, -05, -06, -07, -08, -09 | — | juniper-ml | M | HYGIENE |
| P3-14 | Fork-drift marker: pin `encode("utf-8", "surrogatepass")` + `compare_digest(presented,`; fix comment `:205-209`; mutation-check; FORCE_LOCAL scratch-root run; update guard counts | L47, L277–290 | [VERIFIED anchors at `main`: svc-core `:88/:91`, data `:115/:118`, cascor `:84/:87`, canopy `:52/:137`, csrf `:91/:97`; marker count 0; comment present] [CHANGED: REFERENCE.md drift bullet is now L3019, not ~L2977] | BLOCKED-ON P3-11 | P3-11 | juniper-ml | M | SAFETY |
| P3-15 | On real services: measure and file (a) the lone-surrogate 422 echo (data generic 400; cascor 400 `detail: null`) and (b) the primer toy's copy; correct primer L4742–4743 in place | L48, L292–302 | [VERIFIED: data handlers `RequestValidationError` `:187`, `ValueError` `:214`; cascor `:858/:918`; primer L4742–4743 still say no handler] [CHANGED: data lock now starlette 1.7.0 / pydantic 2.13.5] | STARTABLE | — | data, cascor, juniper-ml | M | USER-FACING |
| P3-16 | PATCH PR bodies: ml#2080 (drop the L69 bullet; add the Corrected row), ml#2088 (L47 wording), cascor#689 (F9 "4001") | L49, L304–308 | [VERIFIED: #2080 L69 present; #2088 L47 "Extended beyond the lanes"; #689 "4001" ×2] | STARTABLE | — | juniper-ml, juniper-cascor | S | HYGIENE |
| P3-17 | Ask D-02 / D-03 (release path; who opens the cap, lock and floor PRs) | L50, L230 | [VERIFIED: PyPI juniper-observability 0.4.0 (06-14), juniper-service-core 0.7.0 (08-31)] | BLOCKED-ON P3-07 | P3-07 | juniper-ml | S | SAFETY |
| P3-18 | Cap PRs before the Release; owner cuts observability and service-core; then lock and floor PRs (note 2) | L223–231 | [VERIFIED 2026-10-04: every lock and cap line via the contents API] | OWNER-ACTION | P3-17, P4 | ml, data, cascor, canopy, recurrence | M | SAFETY |
| P3-19 | Ask D-12 (the next data release) and D-07 (#437's breaking marker) | L320, L326 | [VERIFIED: latest is v0.16.0; `main` is 9 commits ahead (#436, #437, #438, #440 + 5 dependabot); `[Unreleased] ### Changed` carries `equities_seq` 6.0.0] [NOT RE-PROBED: renderer "breaking: NO"] | BLOCKED-ON P3-03 | P3-03, P4 | juniper-data | S | UNBLOCKER |
| P3-20 | Hand the canopy items to P2: F-060; 061/062 FIXED-BY #685 only after P3-06; the "Nothing was loaded" copies. If no P2 session exists, record them yourself | L52, L262–265 | [VERIFIED: the ledger stops at F-CANOPY-059; `dashboard_manager.py:8410` cut list and `:8381` copy; test `:42`; cascor `manager.py` "Nothing was loaded" count 0] | STARTABLE (060, copies) / BLOCKED-ON P3-06 (061/062) | P2 item 2 | juniper-ml (ledger) | S | HYGIENE |
| P3-21 | Fix F-CANOPY-060 (cut only at `" To accept it,"`) and refresh canopy's stale copies | L263–265 | [VERIFIED: `:8410` reads `for stop in (" To accept it,", " The resulting dataset")`] | STARTABLE (no owner) | P3-20 | juniper-canopy | S | USER-FACING |
| P3-22 | Surface rulings on the nine parked rows (D-10), APD-DATA-055 `If-Match` (D-08) and APD-ML-008's remedy (D-09) | L321–323 | [VERIFIED: the park block at L1619–1637 is unchanged since `5af9d722`] | OWNER-DECISION | P3-00 | juniper-ml | S | SAFETY |
| P3-23 | Surface the CodeQL residual (D-11); never dismiss alerts or edit probes | L324–325 | [VERIFIED: alerts 843/876 dismissed "used in tests" 09-26; `codeql.yml` has `+security-and-quality` and no paths-ignore] [NOT RE-PROBED: the 207-alert count] | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P3-24 | Later arc D-C (APD-DATA-030/-031/-022; RFC 9457; absorbs P3-15(a)) then D-D (-026/-027/-028/-008); sequence on `routes/datasets.py` | L328–335 | [VERIFIED: rows open] | OWNER-DECISION (timing); after P3-03 | P3-03, P5 | juniper-data | L | USER-FACING |
| P3-25 | Later arc D-F (APD-DATA-019, all stores), then D-E (APD-ECO-001; TTL, backend and route list undecided) | L332–333 | [VERIFIED: rows open] | OWNER-DECISION; after P3-03 | P3-03 | data (+ clients) | L | DATA-INTEGRITY |
| P3-26 | Later arc D-G (APD-DATA-048/-049/-051, which the register calls "actionable") | L334 | [VERIFIED: open] | OWNER-DECISION (timing) | — | juniper-data | M | USER-FACING |
| P3-27 | Later arc C-A (APD-ECO-003, relaunch fresh) then C-B (APD-ECO-004; 38 colliding `def` lines); C-C (APD-RCLIENT-004) | L336–339 | [VERIFIED: open] | OWNER-DECISION (timing) | — | data-client, cascor-client, recurrence-client | L | USER-FACING |
| P3-28 | Round 39 §0.4's no-row items: `equities_seq` `data_quality` has no consumer in recurrence; canopy's `val_ratio` removal is recorded only in register §4.9 | L340 | [NOT RE-PROBED] | OWNER-DECISION | — | recurrence, canopy | S | HYGIENE |
| P3-29 | Worktree and branch cleanup with the owner's go-ahead (keep the data worktree until P3-03 and the cascor shortfall worktree until P3-05) | L341, L394–412 | [VERIFIED: 11 shared + 3 session worktrees exist; canopy `pr-63`/`pr-683` = `4caf9389`; cascor `fix/shortfall-mixed-provenance-and-678-followups` = `e452a660`] [NOT RE-PROBED: dirty state; local cascor branches] | OWNER-DECISION | P3-03, P3-05 | all | S | HYGIENE |
| P3-30 | Keep MEMORY.md under ~25,000 characters: retire entries before adding any | L327 | [CHANGED SINCE HANDOFF: `wc -m` 24,929 → 24,993] | STARTABLE | P2 item 6 | auto-memory | S | HYGIENE |
| P3-31 | Ask D-06 (purge the live Sentry test events) and D-05 (the stray canopy branches) | L318–319 | [VERIFIED: branches] [NOT RE-PROBED: Sentry] | OWNER-DECISION | — | canopy, Sentry | S | HYGIENE |
| P3-32 | Record D-15: canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its retire condition | L254 | [NOT RE-PROBED] | OWNER-DECISION | — | juniper-canopy | S | HYGIENE |
| P3-33 | **Residue:** file juniper-data#432 as an APD-DATA row (an additive-sizing overflow gives a generic 400, with the cause logged at DEBUG) | P6 consolidated L71 | [VERIFIED: #432 open, 0 comments, no labels; absent from the register and P3] | STARTABLE | P6 (PF-2 ceiling) | juniper-ml, juniper-data | S | USER-FACING |
| P3-34 | **Residue:** carry APD-DATA-046 (C, Berkshire dual-class) on the later-arc list ("do it later in this path") | register L1470–1472; round 39 §0.1 | [VERIFIED: open; in no 2026-10-0x handoff] | OWNER-DECISION (timing) | — | juniper-data | M | DATA-INTEGRITY |
| P3-35 | **Residue:** record the fix-forward's known issues (naive cursor / `created_after` → 500; unparseable metadata → 400; a metadata-only dataset stays a cache hit; L7 expiry outside the locks) | PR draft L165–170 | [VERIFIED: register grep → 0; data `main` API doc grep "naive" → 0] | BLOCKED-ON P3-03 (or note in P3-11) | P3-03 | juniper-ml, juniper-data | S | DATA-INTEGRITY |
| P3-36 | **Cross-path:** the APD-ML-002…006 rulings (carried by P6 item 4; the rows live in P3's register) | P6 L54, L71; register L1312 | [VERIFIED: open, "UNPARKED, NOT actionable"] | OWNER-DECISION | P6 | juniper-ml | M | RESEARCH |

**Note 1 (residue for P3-11):**
- the shortfall-message residue;
- the wholesale auto-start bind;
- `current_dataset` (no row);
- canopy#683 item 3;
- F9's `b9484fef` message;
- #685's residue, including the anonymous rate-limiter 500 behind `rate_limit_enabled`;
- the false "which no lane named" message in `2439d049`.

**Note 2 (cap, lock and floor lines for P3-18, all VERIFIED):**
- observability `<0.5.0` caps: canopy `pyproject.toml:109`, recurrence `:79`, recurrence-client `:41/:46`.
- service-core `<0.8.0` caps: data `:110`, cascor `:105`, canopy `:119`, recurrence `:51`, juniper-ml `:94`.
- Locks:
  - data `requirements.lock:88/:90`;
  - cascor `:63/:65`, and `requirements-cpu.lock:129/:133`;
  - canopy `:79/:81`;
  - recurrence `:70/:74`.

### 1b. Open defects (register Sev; my parse: 36 open + 3 reserved and unfiled)

| ID(s) | Sev | Repo | Fix named → live state [VERIFIED 2026-10-04 unless marked] |
|---|---|---|---|
| APD-DATA-017 / -029 / -032 | R / E / E | data | data#428 merged 09-23 and IS in v0.16.0 (compare `af7831be...v0.16.0` → ahead 3, behind 0). #438 merged 09-24 and is NOT in any release. The fix-forward is unmerged |
| APD-DATA-057 | C | data | #438 merged, unreleased; closes after P3-03 validates |
| APD-DATA-055 | C | data | lock half by #438 (unreleased); the `If-Match` half is parked |
| APD-CASCOR-008 / -013 | M / C | cascor | #678, #688 and #690 merged (#690 unvalidated); none released (PyPI 0.11.0, 09-10) |
| APD-ECO-013 (unfiled) | S | canopy, data, cascor, svc-core, obs | ml#2086, canopy#685, data#440 and cascor#689 merged. NONE released: obs 0.4.0, svc-core 0.7.0, canopy 0.8.1 (09-18), data 0.16.0 (tag before #440) and cascor 0.11.0 all predate them. #685 is unvalidated; F2/F3 are unfixed |
| APD-ECO-014 (unfiled) | S | canopy | canopy#685 merged, unvalidated, unreleased |
| APD-CASCOR-014 (unfiled) | S | cascor | F4 unfixed |
| APD-ECO-009 / -010 / -011 / -012 | S / S / S / C | canopy | none; parked |
| APD-DATA-054 / -056 | R / R | data | none; parked |
| APD-ML-007 / -008 | C / M | juniper-ml | none; parked |
| APD-ML-002 / -003 / -004 / -005 / -006 | C / R / R / R / M | juniper-ml (`util/experiments/`) | none; ruling owed (P6) |
| APD-DATA-046 | C | data | none; deferred by ruling |
| APD-DATA-048 / -049 / -051 | M / E / E | data | none (D-G) |
| APD-DATA-008 / -026 / -027 / -028 | E / E / E / E | data | none (D-D) |
| APD-DATA-022 / -030 / -031 | M / E / E | data | none (D-C) |
| APD-DATA-019 | R | data | none (D-F) |
| APD-ECO-001 / -003 / -004 | R / R / M | ecosystem / three clients | none (D-E, C-A, C-B) |
| APD-RCLIENT-004 | M | recurrence-client | none (C-C) |

## 2. Owner decisions pending

| ID | Question | Options; the source's recommendation | Blocks | Source |
|---|---|---|---|---|
| D-01 | Merge grant for this session | grant / withhold; ask at first action | every merge (P3-03…) | consolidated L35 |
| D-02 | How are observability and service-core released? | (1) the owner prepares and cuts both; (2) an agent opens bump and notes PRs at owner-named versions, and the owner cuts. No recommendation. Ask only after P3-07 validates | P3-18; the Sentry fix reaching any service | L230 |
| D-03 | Who opens the cap, lock and floor PRs? | none stated | P3-18 | L230 |
| D-04 | canopy#685 calls: (a) make upstream errors type-only (`outbound_errors.py:57-61`, a 62-line file [VERIFIED]); (b) refuse a space or tab inside a key; (c) a blank `*_API_KEY_FILE` shadowing a real env var sends no key | yes/no each; none | P3-06's content | L314–317 |
| D-05 | Delete the stray `pr-63` / `pr-683`? | yes/no; "do not delete unasked" | P3-29 | L318 |
| D-06 | Purge round-42 test events from live Sentry? | yes/no | — | L319 |
| D-07 | Mark #437 (`equities_seq` 6.0.0) breaking? | yes/no. Precedent: 0.15.0 flagged 4.0.0 "BREAKING (contract)" | next data release notes | L320; PR draft L139 |
| D-08 | APD-DATA-055's `If-Match` half | implement / document; none | closing -055 | L321 |
| D-09 | APD-ML-008's silent-path remedy | "a variable only the drift step sets"; rulable separately | ML-008 | L322; register L1631 |
| D-10 | The nine parked rows, asked together, one question each | ECO-009/-010/-012: fix, and does canopy become a site of `streaming-body-cap` / `pre-auth-throttle` / `cors-outside-auth`? ECO-011: an Origin check on every state-changing route, or refuse non-JSON `POST /api/dataset/generate`. DATA-054/-055/-056 and ML-007/-008: per row | those 9 rows | L323; register L1619–1634 |
| D-11 | CodeQL residual on the probe paths | a `paths-ignore` config, or a tarball, never ruled; record who dismissed the highs only if the owner says | — | L324–325 |
| D-12 | Cut the next juniper-data release once P3-03 merges and validates? | yes/no; the owner cuts | shipping #438, #440, the fix-forward and X8; P5 W10 | L326 |
| D-13 | When to start the later arc items | order per round 39 §0 | P3-24…27, P3-34 | L328 |
| D-14 | Worktree and branch cleanup | per worktree | P3-29 | L341 |
| D-15 | Retire canopy's ad-hoc mutation script? | record only | — | L254 |
| D-16 | APD-ML-002…006 rulings | per row (carried by P6) | P6 item 4 | P6 L54 |

## 3. Cross-path dependencies

- **P3 → P4:**
  - P3-03 must merge and validate before the next data release (D-12, P4 item 5).
  - P3-07 → D-02 → P4's owner-gated observability and service-core cuts; only one session cuts them.
  - The canopy release (23 SHIP), the cascor release (17) and the data release are what deliver APD-ECO-013/-014's fixes to PyPI and images.
- **P4 → P3 (resolved):** the dispatch token was widened. Notify run 37114403856 finished `success` at 2026-10-03T09:50:35Z [VERIFIED], so the next data release's notify job is no longer blocked.
- **P3 → P5:** P5's `routes/datasets.py` edits sequence after P3-03, as do D-B…D-D (P3-24). P5 W10 waits on the data release.
- **P3 ↔ P2:**
  - P2 item 2 (the Phase 10 ledger PR) files F-CANOPY-060/-061/-062 and the "Nothing was loaded" item.
  - P3 sends P3-06's outcome; P2 sends back the id it assigns.
  - P2 is named for P3-21 but has no owner.
- **P6 ↔ P3:**
  - P6 item 4 needs D-16; those rows live in P3's register.
  - data#432 (P3-33) needs P3's id, and its fix moves PF-2 axis 2's 5,882 ceiling.
- **P7:** soft. An observability release bundles whatever is under `[Unreleased]`; P7 itself found no hard dependency (P7 L97).
- **P8:** soft. Stagger the consensus rounds (P3-01, -05, -06, -07, -08 and -10 are all two-lane).
- **All paths:** MEMORY.md (P3-30; P2 item 6).

## 4. Hazards

- **The owner's sweeper merges green PRs.** Validate F2/F4 (P3-07/08) and any row-CLOSING register PR before it reaches a branch. Never draft or disarm a PR.
- **Merging:**
  - A grant never carries across sessions.
  - Merge only via `util/safe_merge.py`, and read its `MERGED` line.
  - `strict: true` means running update-branch after every move on `main`.
- **Uploads:**
  - Uploads are whole-file and signed commits have one parent: rebuild from `origin/main`, and keep at most ONE open register or primer PR.
  - P3-03 and P3-09 share data's `[Unreleased]`.
- **Register and primer:**
  - The primer is cited by bare line number: edit it in place only.
  - Never put an OPEN id on register L177.
  - Data squashes with `COMMIT_MESSAGES`: dropping `Allow-Symbol-Loss: method:LocalFSDatasetStore.save func:_file_lock_is_held` turns `main` red.
- **Sentry:**
  - Set the six DSN variables to `""` (never unset); the shell exports `SENTRY_SDK_DSN`.
  - Never use ports 8100, 8201 or 8050.
  - Releasing early ships F2's leak and F10's false sentence.
- **Fork-drift marker:** a premature marker passes PR CI and fails the weekly `docs-full-check` on `main`.
- **tmpfs:** the four executor spec files and `primer-venv` live only on tmpfs (2fba4397's scratchpad). Copy them out before P3-02.
- **Never:**
  - run `util/worktree_cleanup.bash` or `util/remove_stale_worktrees.bash`;
  - push unsigned scratch commits (fizzy's three; canopy `4caf9389`);
  - message session `bc31e993`.
- **Preserved probes:** `make_nv1_tree.py` deletes its second argument and `fix_probe_pairs.py` rewrites files. Pass only fresh scratch paths.

## 5. Discrepancies (handoff vs live, 2026-10-04)

1. **Data branch divergence.** "2 ahead / 4 behind" is now **2 / 6**. data#444 and #445 merged at 09:08Z and 09:21Z on 10-03, after the handoff's probe. The only overlap is still `CHANGELOG.md`.
2. **Data's lock moved.** data#441 (10-02) moved it to starlette **1.7.0**, pydantic **2.13.5** and sentry-sdk 2.70.0, with fastapi 0.141.1. The governing source's item-8 measurement says data's locked starlette is 1.6.0, so re-measure on the new pair.
3. **Dependency (ii) is stale.** "The next data release fails the same way until the token is fixed" no longer holds: the token was fixed and verified on 10-03.
4. **P7 bullet is wrong.** "Observability `[Unreleased]` holds only #2086's change" is false. It also holds the APD-OBS-001…004 fixes (ml#1156, #1237, #1245, backfilled by #1513), all unreleased since 0.4.0. The release therefore also ships APD-OBS-001's `X-Request-ID` ingress validation.
5. **Small drifts:**
   - MEMORY.md: 24,929 → 24,993 characters.
   - `/tmp` inodes: 39% → 29%.
   - The drift-gate bullet in `docs/REFERENCE.md` moved from L2972 to L3019 (ml#2114, #2115, #2117).
6. **P2's gate differs from P3's.** P3 says P2 records 061/062 FIXED-BY #685 "only after item 3 validates". P2's own items (canopy-consolidated L86–87; the 10-04 handoff L38) plan FIXED-BY with no validation gate, and P2's source F10 says only "Record FIXED-BY #685".
7. **The register's own prose is stale:**
   - APD-CASCOR-013 says #690 is "open on 2026-09-24".
   - APD-DATA-017/-029/-032 say "PyPI still served 0.15.0".
8. **Data's lead over v0.16.0.** P4 said 7 commits ahead; it is now 9.

## 6. Residue (open, and not carried by the P3 consolidated handoff)

- **juniper-data#432** (P3-33). P6 assigns it to the register lane; neither P3 nor the register mentions it.
- **APD-DATA-046** (P3-34): open, deferred "to later in this development path", and named in no 2026-10-0x handoff. The D-G list carries only -048/-049/-051.
- **The fix-forward's known issues** (P3-35) are recorded only on the unmerged data branch and in R42/; no register row covers them.
- **APD-ML-002…006** are carried by P6, not P3, although they are rows in P3's register (P3-36).

## 7. Path assessment

- **Urgency: HIGH.** Nothing has moved since 2026-09-26. Until observability and service-core are released and the locks bumped, any unhandled exception during a keyed request records the caller's key in Sentry. Under `send_pii=True` (data), transactions also carry the raw `x-api-key` (F2). Three S rows are unrecorded in the register.
- **Leverage:**
  - P3-07 unlocks the release question (D-02), and with it the whole delivery chain.
  - P3-01→03 unlock the next data release (P4), P5, D-B's closes and D-F/D-E.
  - P3-06 unlocks the APD-ECO-013/-014 closes and P2's ledger.
- **Cost:** mostly M agent work (about 7 two-lane rounds). Merges and releases are owner-gated.

**Recommended next actions:**
1. **P3-00, then P3-07 and P3-08 together:** fix F2/F10 (plus F6, F9, F3, F5) and F4, validated before either reaches a branch. That makes D-02 askable (P3-17).
2. **P3-01:** round 2 on the data fix-forward, then P3-03 with the grant, then D-12 (P3-19).
3. **P3-06, then P3-05:** validate canopy#685 and cascor#690. In the same owner turn, open P3-11 to file the three S rows OPEN.

## 8. What this report cannot support

- **No repo scripts or tests were run.** These are therefore NOT RE-PROBED:
  - the 136/100/36 counts (mine come from a one-line parse);
  - the crosscheck's "AGREE";
  - the archiver's `--check`;
  - the fork-drift unittest;
  - the notes renderer's "breaking: NO".
- **Other sessions:** `ListAgents` is unavailable here. "No session is working P3" rests only on no file changes since 10-01 in the data, cascor and canopy worktrees.
- **Not probed:** live Sentry, the CodeQL lesser-alert count, the data branch's trial merge, the real-service 422 measurements, dirty-worktree contents, local cascor branches, and the JuniperData conda environment's fastapi/starlette versions.
- **Judgement, not measurement:** the Effort and Criticality columns.
