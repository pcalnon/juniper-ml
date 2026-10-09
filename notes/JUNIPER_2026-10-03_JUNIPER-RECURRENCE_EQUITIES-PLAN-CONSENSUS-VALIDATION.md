# Juniper-Recurrence × Equities — Consensus Validation of the Audit and Development Plan

- **Project**: Juniper — juniper-recurrence (with juniper-data, juniper-data-client, juniper-canopy, juniper-ml experiment stack)
- **Author**: Paul Calnon
- **Date**: 2026-10-03
- **Status**: Validation complete after two rounds; plan **upheld with corrections** at v1.2.0. One item is left to the owner: the milestone dates (§7). Planning only — no code changed, nothing committed, no GitHub objects created or modified.
- **Validates**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md) (v1.0.0 → v1.1.0 after round 1 → v1.2.0 after round 2)
- **Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) (§2 lanes, §4 iteration, §5 reconciliation, §7 minimum record)
- **Precedent followed**: [`JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md`](JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md)
- **Agent reports**: `reports/2026-10-03_recurrence-equities-consensus/{laneA1,laneA2,laneA3,laneB1,laneB2,oracle}.md` (round 1) and `{laneA1-r2,laneB1-r2}.md` (round 2)
- **Evidence**: `juniper-ml/.amp/in/artifacts/recurrence-equities-audit/` (103 files; git-excluded; indexed in the plan's §2.3)

---

## 1. Why this ran

The plan is a document of record for six repositories and proposes a release train, a Compose pin move, two breaking defaults (model target, validator dtype) and a scientific go/no-go on a number (aggregate crossval r² of −18,081) whose cause the audit could not isolate.
Under §3 of the procedure that is **high criticality × high uncertainty**: three or more Lane A agents with distinct entry points, two or more Lane B agents with opposing briefs, and iteration until the last round changes nothing of substance. Six reviewers ran in round 1 and two in round 2.

The user asked for the plan to be "validated by consensus"; this note is that record. It records what the plan got wrong at each version, what was attacked and held, what remains disputed, and what the evidence cannot support.

---

## 2. Instrument and sample

| Instrument | Could it have produced a different answer? | Sample |
| --- | --- | --- |
| Live shadowed `curl` probes against the recurrence service as served from `JuniperCascor1` and from a `PYTHONPATH`-shadowed checkout, same request bodies | Yes — the pair returned 422 and 200 on the identical `/v1/crossval` request; a non-ENV cause would have failed both | n = 1 host, 1 day, 1 ticker set (AAPL 2015–2022); 5-symbol canopy seed for `/v1/train` only |
| `pip check`, `python -s` import probes, `pip show` under the as-served env | Yes — a consistent env would have reported no recurrence-closure lines | 1 env (`JuniperCascor1`); `JuniperCanopy1` probed for canopy tests only |
| Bench and app test suites under both envs | Yes — 14 failed / 23 passed as served vs 37 passed shadowed | 1 run each |
| Log reads: recurrence shadow log, Scenario-A `registry.jsonl`, run manifests, `stats.json` | Partly — logs record what was emitted, not what was omitted; absence claims (F-S7 theta never logged) rest on code reading | 1 Scenario-A run (`scenario-a-runs/`), 1 shadow log |
| Source reading across six checkouts at the SHAs Lane A2 recorded (`juniper-recurrence be081fa`, `juniper-canopy 72b1a5f6`, `juniper-data 1c67f8d`, `juniper-data-client 0ec4b30`, `juniper-ml afb02801`, `juniper-deploy 9403dbf`) | Yes — 39 of 40 citations re-derived; line drift ≤ 10 accepted | all citations in the plan's §3 |
| `gh` issue census, PyPI JSON, git tags | Yes — produced four contradictions in round 1 (§4.1) | as of 2026-10-03 |

**The E-H suite's own RFF configuration was never run on the artifact.** Every crossval number in the plan is from the service defaults (`readout=linear`, `ridge=0.0`); the plan now says so (F-SCI1) and makes measuring the real configuration its first scientific item (W0.8/W0.9).

---

## 3. Lanes, agents and entry points

| Round | Lane | Agent | Entry point | Brief |
| --- | --- | --- | --- | --- |
| 1 | A | A1 | the 103-file artifact archive only; no source | re-derive every artifact-backed claim |
| 1 | A | A2 | source checkouts only; artifacts not opened | re-derive every source citation and stated behaviour |
| 1 | A | A3 | run state, installed metadata, git/tags, GitHub issues, PyPI, parent inventory, launcher text | re-derive everything that is neither artifact nor cited source |
| 1 | B | B1 | plan + source | refute; lens **correctness / omission** |
| 1 | B | B2 | plan + source | refute; lens **actionability / priority / self-consistency** |
| 1 | B | oracle | plan v1.0.0 + five repos | refute; lens **interpretation** (phase order, scoping, dependency edges, rulings) |
| 2 | A | A1-r2 | artifacts + code for the claims round 1 changed; not the plan's own reasoning | re-derive the v1.1.0 numbers and citations |
| 2 | B | B1-r2 | plan v1.1.0 phases, gating, milestones, rulings; briefed on the round-1 changes, **not** on B2's report | refute; lens **sequencing / gating / actionability / self-serving framing** |

Round-2 agents were told which changes round 1 had forced and asked what those changes broke. They were not given the round-1 reports, so B1-r2's agreement with B2 (§5) is independent.

Round-1 tallies: A1 19 confirmed / 3 refuted / 5 partial; A2 39 verified / 1 contradicted / 0 not found; A3 4 verified / 4 contradicted; B1 1 FATAL / 7 MAJOR / 4 MINOR; B2 3 FATAL / 13 MAJOR / 4 MINOR; oracle 1 FATAL (O1) / 6 MAJOR (O2–O7).
Round-2 tallies: A1-r2 4 confirmed / 3 partial / 0 refuted; B1-r2 0 FATAL / 7 MAJOR / 1 MINOR / 2 HELD.

---

## 4. Round 1 — what v1.0.0 got wrong (→ v1.1.0)

### 4.1 Refuted

- **F-SCI1 attributed the −18,081 to the E-H RFF configuration.** Oracle O1 (FATAL), A1 (CONTRADICTED), B1 (MAJOR). The request that produced it was a bare curl; the service log line shows `readout=linear` and `settings.py:183` has `default_ridge = 0.0`. v1.1.0 rewrote the finding as "cause unresolved", withdrew the normalisation hypothesis to candidate (b), and added W0.8 (replay the real configuration) and the matrix.
- **W5.4 claimed a suite-YAML `acceptance:` facility the driver "already supports".** Oracle O7, B2 (FATAL). `run_suite.py:742` is reporting-only; `run_experiment.py`'s `acceptance` block is per-phase pass/fail, not a band. v1.1.0 made W5.4 a build item (M–L) and forbade W0.3 from deriving `degraded` from `acceptance.ok`.
- **W5.2 proposed a new model-core algorithm.** Oracle O5, B1 (FATAL — "can create a second CV API while leaving `/v1/crossval` unchanged, and silently changes the public meaning of `embargo`"). `walk_forward_folds` already takes `order=`/`groups=`; the route does not pass them. v1.1.0 reowned W5.2 as recurrence + model-core integration, kept embargo in windows and named the duration gap separately.
- **The published Compose stack was not in scope.** Oracle O3, B2 (FATAL — "the advertised M1 cannot work against published components"). Compose pins juniper-data 0.16.0, whose `equities_seq` is `classification`, so canopy refuses it; nothing owned the pin move. v1.1.0 added §3.10 DEPLOY (F-DEP1/2), W1.11 (0.17.0 release + floors + pins + smoke) into P1 as an M1 requirement, and W1.12 (snapshot bind mount).
  - **Correction 2026-10-08 (plan v1.5.0):** "so canopy refuses it" did not reproduce. Canopy's `compatible()` compares with canopy's own `DATASET_TYPES` label (`GeneratorInfo` carries no `task_type`), and against the published canopy 0.8.1 / recurrence 0.5.0 / data 0.16.0 images the fit completed (juniper-deploy#245's smoke). The scope finding stands — the published stack still serves the wrong producer meta and nothing owned the pin move — but its mechanism was the producer's stored label, not a canopy refusal.
- **Shared-service identity was absent.** Oracle O3, B1 (MAJOR). Canopy and the CLI stack can point at the same service with one `train_lock`, one in-memory model and no operation id. v1.1.0 added §3.11 CONCURRENCY (F-CON1–3) and folded `operation_id` / `expect_operation_id` into W1.5.
- **Inner timeout.** Oracle O4. `data.py:73` builds `JuniperDataClient` without a timeout, so the client's 30 s default applies regardless of canopy's 300 s or the driver's budget. v1.1.0 added F-S9 and the `juniper_data_timeout_seconds` setting to W1.5.
- **R4 was posed as an open question.** Oracle O6. Fold-local preprocessing is required for CV whatever W0.9 finds, because producer `normalize_features` is fitted on the pooled train partition. v1.1.0 converted R4 to a note; B1-r2 attacked the conversion as self-serving and it **held** (§6).
- **Lane A3 contradictions** (state drift, not reasoning): run-state census was larger than stated and contained a second recurrence × equities run that day; the `juniper-recurrence-model 0.3.2` wheel named in the parent `AGENTS.md` paragraph does not exist on PyPI (latest 0.3.0); one `isolated_stack.bash` line range was off; one GitHub issue characterisation was imprecise. All corrected in v1.1.0.
- **A2's single contradiction**: F-S1 said the CLI explicitly passes `params={}`; it omits the argument and the callee's `dict(params or {})` yields the same empty bundle. Wording fixed; the defect stands.

### 4.2 Structural changes round 1 forced

P0 gained W0.6 (CLI `--params`, from P1 — the CLI entry point cannot run without it), W0.7 (`metrics_scope` label) and W0.8 (the replay). W1.0 (matrix + go/no-go) was created in P1. W1.11 moved from P5 to P1. W3.0a/W3.0b were added. R6–R8 were added. Milestones were rebaselined from "M4 in seven weeks" to eleven.
B2 dissented that the matrix should itself be P0; the reconciler kept it in P1 and recorded the dissent in the plan's gating paragraph. That decision was reversed in round 2 (§5).

---

## 5. Round 2 — what v1.1.0 got wrong (→ v1.2.0)

### 5.1 Measurement (Lane A1-r2)

- **"1,346 windows" was the train partition, not the CV population.** The shadow crossval response says `split="full"`, `n_windows=1698`; the frozen meta has `n_samples=1698`, `n_train=1346`. v1.2.0 states 1,698 and re-derives the per-fold train sizes (281–1,413, from model-core `splits.py:111`'s `fold_size = n // (n_folds + 1)`), marking them as derived because the response carries no fold sizes.
- **"Train-fold RMSE ≈ 0.012" understated folds 4–5** (0.0143, 0.0175). v1.2.0 lists all five train and eval values.
- **`00-baseline.txt` does not show `derive_full_split` is absent** — it shows versions only. The absence is in `tests-bench-env.log` (14 × `cannot import name 'derive_full_split'`). F-E1's evidence column now names both for what each proves.
- **F-CON2 "snapshots take no id"** could be read as denying snapshot resource ids. Reworded: snapshot resources have ids; nothing ties a snapshot or a prediction to the training *request*.
- Confirmed without change: the E-H YAML configuration (d 16, theta null, ridge 1.0, RFF, 256 features, median gamma); `data.py:73` passes no timeout and the client default is 30 s; the 5 ms / 3 ms lock-contention measurement; Compose pins and the missing volume; `training.py:44–105` lock scope; schemas carrying no ids; `run_suite.py:78/81/737–750`; `walk_forward_folds` accepting `order=`/`groups=` and the route not passing them.

### 5.2 Sequencing and gating (Lane B1-r2)

- **Q4 — the matrix is the real gate (MAJOR; agrees with B2's round-1 dissent).** B1-r2's argument: the plan itself gates all of P5 and R5 on the matrix verdict; W1.1(a) sets `normalize_features` "per its finding"; M1 required its verdict; and its prerequisites (W0.1, W0.6) are P0 items, so "run it once the env and CLI can" argues for the end of P0, not P1. The reconciler re-derived this against the plan text and accepted it. **W1.0 is now W0.9, closes P0, and M0 requires it.** No dissent remains on placement.
- **Q2 — "Independent of W1.1–W1.12" was false (MAJOR).** Resolved by the move; W1.1(a) now says it may be drafted early but merges after W0.9 reports.
- **Q3 / Q10 — W1.11 as a hard M1 gate had no slip rule, and M1 named four publications no work item owned (MAJOR).** v1.2.0 adds a slip rule to W1.11 (the code half is M1-blocking; publication is not under the plan's control; if pending, M1 is declared "code complete, publication pending") and **W1.13**, a P1 release train owning recurrence 0.6.0, model 0.4.0, data-client 0.6.0 and canopy 0.9.0 in dependency order.
- **Q6 / Q9 — W5.4's "missing metric → `flagged (metric absent)`" contradicted gate-mode semantics (MAJOR).** Now mode-dependent: under `gate` a metric that cannot be evaluated is `failed (metric absent)` with non-zero exit; under `report` it is `flagged (metric absent)`. Distinguished from `degraded` (phase did not run).
- **Q9 — W5.2's compact row said "embargo ≥ `lookback` + `embargo_days`", adding a window count to a duration (MAJOR).** Row now matches its normative Details.
- **Q10 — W5.6 "documented in W4.1" but W4.1 (P4) precedes W5.6 (P5); W3.0a "shares the W3.2 fixture" but its id sorts first.** W5.6 now documents itself; the P3 row states the landing order W3.1 → W3.2 → W3.0a.
- **Q7 — M1 2026-11-07 not credible (MAJOR).** See §7.
- **Q8 — the gating paragraph softened B2 (MINOR).** Replaced by a paragraph that states B2's reason (the matrix is the gate; one replay cannot carry a go/no-go), B1-r2's independent agreement, and the reversal.

---

## 6. Attacked and held

- **ENV attribution (F-E1).** Oracle, A1, A3: shadow vs as-served on the identical request is a measurement; no alternative explanation was found.
- **Flat `equities` refusal (F-S4) and canopy's metrics-panel honesty (F-C10)** hold as verified controls; neither is a work item.
- **Driver outcome defect (F-D1) and `_headline_metrics` key mismatch (F-D2)** hold as stated (oracle, A1, A2).
- **R4 as a note, not a ruling** (B1-r2 Q5, HELD): the note states an invariant (pooled-train normalisation leaks into early full-view folds) with a scoped remedy; no competing valid leakage policy was offered, so there is nothing for the owner to choose between.
- **No P0 forward dependency** (B1-r2 Q1, HELD): W0.2 → W0.1 is intra-phase order; W0.3 reserves semantics for W5.4 without needing it; W0.7 defines the constant W5.3 extends; W0.8 runs by hand.
- **F-D10 accepted without a work item** (round 1): `isolated_stack.bash` roots its scratch tree under `/tmp` by design and writes no script source there, so the ecosystem rule is not breached; the plan's §3.2 row records the disposition.

---

## 7. Unresolved dissent

**Milestone dates.** B1-r2 (Q7) judged v1.1.0's M1 non-credible for one owner plus agents and would "dissent from M1's date until every required release has an owned work item and a slip policy". v1.2.0 supplies both (W1.13; the W1.11 slip rule) and rebaselines: M0 2026-10-24, M1 2026-11-21, M2/M3 2026-12-12, M4 2027-01-15.
The new dates are the author's estimate and were **not** put back through a reviewer; the plan marks every milestone "owner to confirm date". The reconciler records this as the one open item rather than claiming the dates are validated.

No other dissent remains. The round-1 B2 placement dissent was resolved in B2's favour in round 2.

---

## 8. What the evidence cannot support

- **Any statement about how the E-H RFF configuration behaves on the artifact.** It was never run. W0.8 is the first measurement; until it exists, "the model is broken on equities" and "the service defaults are wrong for equities" are equally consistent with the −18,081.
- **The fold-local theta.** F-S7: the data-driven `median(sum(dt))` is never logged, so a theta mismatch between folds cannot be ruled in or out from any artifact. W0.8 requires a temporary debug print to capture it.
- **Per-fold train sizes.** Derived from `splits.py`, not reported by the service (§5.1).
- **Generality beyond one host, one day, one ticker set.** The ENV defect is this host's env; the Compose defect is the published pins as of 2026-10-03; the −18,081 is AAPL 2015–2022 at one seed. A3's instruments "cannot establish uninspected source behaviour, causal claims beyond issue/run records, or what an unpublished future release will contain".
- **That the repaired env stays repaired.** W0.2's preflight is the control; until it lands, the next conda operation can recreate F-E1 silently.
- **The dates** (§7).

---

## 9. Disposition

The plan is **upheld with corrections** at v1.2.0 and lints clean (`markdownlint-cli2@0.17.2`, repo `.markdownlint.yaml`, 0 errors). The owner decisions it now waits on, in the order the plan needs them:

| Decision | Gates | Plan's recommendation |
| --- | --- | --- |
| Milestone dates (§7) | the schedule | confirm or re-set the v1.2.0 dates |
| R6 — exit semantics for `degraded` / `flagged` | W0.3 (P0) | non-zero for `degraded`; unchanged for `flagged`; `gate` opts in to fail |
| R2 — enforce `float32` or document tolerance | W1.4 | enforce |
| R3 — pre-`purchase_date` `cost_basis` under `drop` | W1.8 | refuse when `purchase_date > start_date`; otherwise drop rows |
| R7 — canopy forwarding precedence | W1.2 | seed wins over generic defaults; explicit edits win over the seed; preview shown |
| R8 — ship the `reg` default as a pre-1.0 "Breaking" minor | W1.3 | ship in recurrence 0.6.0 |
| R1 — optional `equities_seq` preset | W1.1b | optional; the documented bundle ships regardless |
| R5 — acceptance band for E-H | W5.4 | ruled only after W0.9's verdict and the W5.1 recommendation |

R4 is a note, not a decision (§6).

---

## Change Log

| Date | Version | Changes | Author |
| --- | --- | --- | --- |
| 2026-10-03 | 1.0.0 | Record of two consensus rounds against plan v1.0.0 → v1.2.0 | Paul Calnon |
