I made no edits, staged nothing and pushed nothing. My scratch files are in `tmp/review-b/` (an options extractor, a pull finder, a credential-word counter, and saved outputs).

## 1. Verdict

The revision records the rulings faithfully. I checked every option label and its text against the `AskUserQuestion` entries in the transcripts of sessions `a4e1e914`, `218ff61e` and `1b4fec84`, and none is stretched:
- Ruling 6 is applied only to the trio's restart. The 2026-11-15 handoff (line 59) and `1b4fec84`'s cascor-version question ("the stack restart follows your probe-per-environment ruling") both blur it into the juniper-deploy stack; the plan does not.
- Ruling 7 is applied only to the juniper-ml primary, and the canopy primary stays open everywhere.

All eight open items in the brief are visible in the §5 note at L1106–1112 and in §6 at L1255. The writer's `--check` exits 0, ID coverage holds at 381 of 381, and lines over 512 characters stay at 19.

The coherence is weaker than the fidelity. The revision edits the R-OBS-SC-2 note, Security step 5 and XC-P12 in place, but leaves present-tense sentences next to its edits that those edits now contradict ("P3-17 stays open", "still truncates", "The restart waits for … S0.11's relay tests", canopy PRs "in no release"). It also leaves stale:
- §8's "Owner-only" rule for the primaries;
- the "not probed" Sentry sentence;
- the cut-ahead-of-gates rows, which say nothing of canopy 0.10.0 and P3-06.

It adds one false "Unchanged" about `JuniperCascor1`, and it places the start of the 0.4.3 design session nowhere. Fix the BLOCKER and the nine MAJORs before landing.

I treated these dated passages as history and did not flag them: L34 (v1.15.15's Status bullet), L177, L892, L1132–1137 and L1155. I did not treat the R-OBS-SC-2 note (L1022–1052) as history, because the revision edits it.

## 2. Findings (most severe first)

1. **BLOCKER** — L502 and L1046: "…`JuniperCascor1` imports 0.4.2's and 0.7.2's code from the juniper-ml primary (…). Unchanged on 2026-11-15 (v1.15.16)."
   - **Why**: the import source moved, and the code with it.
     - L661 of this same revision says the primary was "on `main` at `eeb5c694`" on 11-15. On 11-09, L846 had it "on another session's feature branch".
     - The primary's reflog shows six fast-forward pulls after ruling 7. The last, `4a786c81`→`eeb5c694`, was at 2026-11-15T02:04:55Z.
     - `git log juniper-service-core-v0.7.2..eeb5c694 -- juniper-service-core/juniper_service_core` lists four unreleased fixes: #2531, #2534, #2547 and #2557. Its `[Unreleased]` makes the next release 0.8.0.
     - Observability has no change since v0.4.2.
     - `JuniperCascor1`'s `direct_url.json` points both packages at the primary, while pip reports 0.7.1 and 0.4.1.
   - The scrubbing level is unchanged, so XC-SENTRY's conclusion holds. The record's sentence is still false, and it is the error step 5's own rule ("record the commit it runs, not pip's version") exists to prevent.
   - **Fix**: "On 2026-11-15 it imports the primary at `eeb5c694` (`main`): observability is 0.4.2's code; service-core is 0.7.2's plus ml#2531, #2534, #2547 and #2557 (bound for 0.8.0); pip reports 0.4.1 and 0.7.1 (v1.15.16)."

2. **MAJOR** — L847: "The restart waits for a recorded pass of S0.11's relay tests, which are unwritten: … A pass for cascor and canopy may also need those fixes or 0.4.3…"
   - **Why**: the next bullet (L848) records ruling 6, which replaces this condition. L842's "a smoke import and the relay test's fast subset" is stale for the same reason.
   - **Fix**: "Until ruling 6, the restart waited for a recorded pass of S0.11's relay tests (unwritten …); it now waits for the per-lock probe's recorded pass in each environment (next bullet)." At L842: "…a smoke import and the per-lock probe…".

3. **MAJOR** — L1035: "No `pyproject.toml` moved: the floors stay at observability `>=0.4.1` and service-core `>=0.7.1`. … That plan is a session's, not a ruling (P3-17 stays open; §6)."
   - **Why**: round 1's ruling 1 ("In release PRs", 2026-11-09) made it a ruling. cascor#758 and canopy#818 raised the floors. This revision's own L1247 ("so P3-17 is answered") and L1687 contradict the sentence.
   - **Fix**: append "(v1.15.16: ruled 2026-11-09, round 1's ruling 1; cascor#758 and canopy#818 raised them; data's and recurrence's wait for their release PRs; P3-17 is answered)". Change "stays open" to "stayed open until then".

4. **MAJOR** — L1049: "The forks' `RateLimiter` still truncates with no floor…"
   - **Why**: the same edit changed "is live" to "was live" and "keep" to "kept", but left "still truncates", and its sub-bullet (L1050) says "Fixed 2026-11-13". L1051 ("pass no `telemetry=`… is missing in both") and L1048 ("floors `>=0.4.1`") are also present tense under a lead-in saying they "were carried out".
   - **Fix**: "truncated", "passed", "was missing", "floored".

5. **MAJOR** — L620: "…canopy#777 closes #737…; neither is in a canopy release yet." L630: "Canopy `main` still reads 0.9.0, so no release carries it yet."
   - **Why**: the compare API shows canopy#776 (`c7846b4e`), #777 (`33619d6d`) and #788 (`af650373`) are all ancestors of `v0.10.0` (ahead by 39, 38 and 18; behind by 0).
   - **Fix**: append "(v1.15.16: all three ship in canopy 0.10.0, Release cut 2026-11-15; PyPI at the Overtoad's gate)".

6. **MAJOR** — L1429 (§8): "conda env `JuniperCascor1` …, and the primary checkouts its editable installs map | … | Owner-only changes…"
   - **Why**: this contradicts O13 (2026-11-03; guarded session pulls of the cascor, data, data-client and recurrence primaries) and ruling 7 (the juniper-ml primary).
   - **Fix**: "Owner-only environment changes; pulls of the primaries follow O13: guarded session pulls for cascor, data, data-client, recurrence and, since ruling 7 of 2026-11-13, juniper-ml (on `main` and clean, never a branch switch); canopy's is open."

7. **MAJOR** — L506: "Whether the running services actually send to Sentry was not probed." Also L1648: "Not probed: … the trio, whether running services send to Sentry…"
   - **Why**: `HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md` (Q2, "New since") read the deploy containers by variable name. cascor, canopy and data set `JUNIPER_*_SENTRY_DSN` empty, and recurrence has no Sentry variable. It says outright: "That answers, for this stack, the plan's 'Whether the running services actually send to Sentry was not probed'."
     - Ruling 4's own question carried this as background.
     - cascor `v0.14.0`'s `_resolve_sentry_dsn` still reads environment variables only (unchanged from `v0.13.0`), so the mounted `secrets.example` DSN file still initializes nothing.
     - The trio's ports and environments were read on 2026-11-15.
     - The four canopy E2E legs (:8052, :8053, :8058, :8059) are listening now, and their DSN state is unread.
   - **Fix**: "Probed 2026-11-12 (names only) for the juniper-deploy stack: cascor, canopy and data run with empty DSNs and recurrence has none (the four-ruled handoff); the trio is stopped. Not probed: the four canopy E2E legs." Update L1648 to match.

8. **MAJOR** (dropped open item) — L504 and L1088: "…no design is on `main` yet".
   - **Why**: ruling 4 has "a fresh session" write and validate the design, but nobody is named to start it.
     - It is absent from "Still open with the Overtoad" (L1106–1112), from §6 (L1255), from §4's waves and from §7.1's calendar. §7.1 counts every round against the account-wide cap.
     - No transcript since 11-15 00:00Z was started from the prompt.
   - **Fix**: add "start the 0.4.3 design session from `prompts/generated/…_2026-11-15_0010.md`" to both lists, and add its rounds to §7.1 as **S**.

9. **MAJOR** (stale and asymmetric) — L1008: "**R-CASCOR**: juniper-cascor (PyPI 0.11.0) … Bypassed in part: cascor#712 bumped it to 0.12.0 … served 2026-10-25". Also L1461: "…juniper-cascor 0.12.0 was cut ahead of P3-05 and P3-08 (…PyPI at the gate), and canopy#740 proposed canopy 0.9.0 (open)".
   - **Why**: 0.13.0 and 0.14.0 were also cut ahead of P3-05 and P3-08, and PyPI serves 0.13.0. The plan says "ahead of P3-05 and P3-08" for cascor 0.14.0 three times.
   - It never says that canopy 0.10.0, like 0.9.0, was cut without P3-06:
     - P3-06 is T0 in Appendix A (L1685);
     - §7.1 item 4 is not done;
     - v0.10.0's `[0.10.0]` CHANGELOG section does not mention #685, O3 or APD-ECO-009..012.
   - **Fix**: L1008 should read "(PyPI 0.13.0; 0.14.0 at the gate)", and its bypass list should include 0.13.0 and 0.14.0. At L899 and L1083 add "Like 0.9.0, it was cut without P3-06's validation, the O3 wording fix and A4's asks (S0.5 open)". Bring L1461 up to date the same way.

10. **MAJOR** — L1249: "Its PyPI gate (run 38085392643) waits: approving it publishes the 0.12.0 wheel as cut."
    - **Why**: it has been served since 2026-10-25 (L1137). The new L1255 points to it ("cascor 0.12.0's fix-forward (above)").
    - Also, "whether a fix-forward is owed for cascor 0.12.0" (L1110, L1255) now covers 0.12.0 to 0.14.0, all cut ahead of the same gates. The re-asked Q2 tied this to "whether cascor may again be cut ahead of its own gates".
    - **Fix**: add "Overtaken: served 2026-10-25". Word the open question as "whether a fix-forward is owed for cascor 0.12.0–0.14.0, all cut ahead of P3-05 and P3-08".

11. **MINOR** — L759, L1069, L1222: "Ruling 5 … bears on both" (P4 D-4 and D-5).
    - **Why**: D-4 asked "cut now for the P0 and again after its lock PR, or once after it". 0.9.0 and then 0.10.0 settle it. D-5 is settled for 0.14.0 only. "Bears on" leaves both looking askable at sitting item 8.
    - **Fix**: "D-4: answered (0.10.0 is the second cut; ruling 5 of 2026-11-13). D-5: answered for 0.14.0 only; R-CASCOR's own timing after P3-05 and P3-08 stays open."

12. **MINOR** — L850, L1107, L1255: "the stack's restart".
    - **Why**: the plan calls the trio "The stack trio" (L142), and both sources conflate the two restarts. The plan is right, but ambiguous.
    - **Fix**: "the juniper-deploy stack's restart (an Overtoad action; ruling 6 governs only the trio's)".

13. **MINOR** — L498, L1262, L1447 list the restart's conditions without P3-05. L1262 and L1447 also omit the blank DSNs.
    - **Why**: ruling 6's text says "on P3-05, and with blank Sentry DSNs". L503 and L848 carry both.
    - **Fix**: add both to all three.

14. **MINOR** — L496 and L753 (sitting item 6): "XC-SENTRY (a) or (b) or both".
    - **Why**: ruling 6 requires blank DSNs at the trio's restart, which settles (b) for the trio. Only (a), and (b) for other services, stay open.
    - **Fix**: say so at L503 and at sitting item 6.

15. **MINOR** — L1050, L35 and L310: "Fixed 2026-11-13 in all three" and "APD-ECO-016, filed FIXED".
    - **Why**: the fixes are on `main` only. Round 1's ruling 3 says "each fix ships with its repo's next release":
      - data's waits for 0.18.0;
      - cascor's and canopy's sit at the gates;
      - the deployed images (cascor 0.13.0, canopy 0.9.0, data 0.17.1) still truncate.
      - Round 2 of the guard review flagged the register's own "No release of a fork carries its fix yet".
    - **Fix**: add "(on `main`; in cascor 0.14.0 and canopy 0.10.0 at their gates; in no data release before 0.18.0)".

16. **MINOR** — L1080: "Two Opus reviews read the guard: round 1 … round 2 … (3 BLOCKERs, false statements in the register text…)".
    - **Why**: it does not say the findings were applied, so a reader may think three BLOCKERs remain. ml#2576's body says "all applied" for both rounds. The archive's `README.md` promises that "What was applied, and where, is recorded in plan v1.15.16."
    - **Fix**: "…all applied before the merge (ml#2576's body); only the optional tripwire was not built…".

17. **MINOR** — L1066: ruling 2 is recorded, but not that it was carried out.
    - **Why**: the 11-13 handoff records the four fork worktrees as removed. Ruling 2's text also says "The never-opened juniper-data worktree and the two juniper-ml session worktrees stay."
    - **Fix**: add "carried out 2026-11-13; the juniper-data worktree and the two session worktrees stay by the ruling".

18. **MINOR** — L991 and L994 say "the Overtoad cuts it", against L1065, L1081 and L1083.
    - **Why**: sessions cut `v0.11.5`, `v0.14.0` and `v0.10.0` on the Overtoad's rulings. v1.15.15 recorded the same departure for R-OBS-SC-2 at L1025; v1.15.16 does not.
    - **Fix**: one line in the note: "each Release was cut by a session on the Overtoad's rulings, where §5's rules have the Overtoad cut".

19. **MINOR** — L1102: "…cite a flood-4 'ruling 17' for different items (cascor `:244` at `v0.14.0` …; canopy `:156` at `v0.10.0` …), and the flood-4 record's §8 lists rulings 1 to 14, so neither can be checked…"
    - **Why**: flood-4's ruling 17 is one ruling over four fixes. `HO/HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md` item 3 names them: data's 44 unmarked tests, cascor's stop-then-start race, canopy's unit-lane port guard, and canopy's `lockfile-update.yml` print. So the citations agree.
    - Canopy also cites ruling 17 at `:221` at `v0.10.0`, which the finding misses.
    - The lead-in at L1089 says "Each one's cited lines were re-read on `main`", but this finding cites tag lines. On `main` they are cascor `:289` and canopy `:200`.
    - **Fix**: reframe the finding as "the record's §8 stops at 14; ruling 17 is in flood-4's handoffs". Add `:221`, and amend the lead-in.

20. **MINOR** — L1103–1104 record only `:150` and `:153` of the v2 draft (`notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`).
    - **Why**: the brief says `:322` is recorded; it is not. v2's `:110`, `:315`, `:322`, `:357`, `:358`, `:398-399`, `:409`, `:455` and `:480` are stale too.
    - `:398-399` lists round 2's Q1–Q4 as open, and `:455` ("No session moves it (Q4)") and `:480` (H-26, "Never pull one") contradict rulings 4–7.
    - v2 claims to replace v1's §2, §4 and §6, yet v1 mentions v2 nowhere outside this finding.
    - **Fix**: list them all. Add one Status sub-bullet: "a draft v2 (ml#2550, not validated) proposes to replace §2, §4 and §6; v1 stays the record until the Overtoad rules (v2's §6.4 item 20)."

21. **MINOR** — L663: "…'next releases raise theirs', which goes stale once 0.14.0 and 0.10.0 are on PyPI".
    - **Why**: the parent `Juniper/AGENTS.md`'s cascor 0.13.0 and canopy 0.9.0 bullets (L240–260), including its "juniper-deploy pins the `0.13.0` image" line, also change. The 11-15 handoff says "that sentence and the cascor/canopy bullets".
    - **Fix**: widen the sentence to cover them.

22. **MINOR** (retention) — L2388: the only copy of the parent file from before the 11-14 edit is `tmp/s2/parent_AGENTS_before_2026-11-14.md` in `buzzing-growing-whale`.
    - **Why**: that worktree is on the housekeeping list, and `git worktree remove` deletes its `tmp/`. Earlier copies live in the primary's `tmp/` (L655, L2379, L2382).
    - **Fix**: before that worktree goes, copy the file to `juniper-ml/tmp/2026-11-14-parent-agents-md-backup/`, and say so in L1112.

23. **MINOR** — L1111 lists A1's open limbs without "whether host recurrence legs take a port of W1.14", which §6 A1 (L1232) lists as open.
    - **Fix**: add it, or write "among them".

24. **MINOR** — L1089–1105: the 13 findings have no lane, actor or tier, though Appendix A claims "every ID, placed". Some need the Overtoad (#2507), and some are §5 rules (the service-core 0.8.0 caps, which juniper-ml 0.11.5, cascor 0.14.0 and canopy 0.10.0 have just set at `<0.8.0`).
    - **Fix**: give each finding its next actor, or place it under Hygiene (T6).

25. **MINOR** — L1184: "Both are cut: canopy 0.10.0 and cascor 0.14.0".
    - **Why**: read after "R-DATA-2, R-CANOPY-A and R-CASCOR", it implies R-CASCOR is cut, against L1151 ("R-CASCOR's other gates stand").
    - **Fix**: "The later canopy release and a cascor release on the new locks are cut…; R-CASCOR's own gates stand."

26. **MINOR** (§2) — L311 (P4) and L309 (P2).
    - **Why**: the P4 row omits the two releases waiting at the Overtoad's gates. The P2 row says the replay fix is "unreleased (74 commits past v0.8.1)", although 0.9.0 and 0.10.0 carry it.
    - **Fix**: update both rows.

27. **MINOR** (naming rule, mandatory) — unnamed documents:
    - "the flood-4 record" (L1102; `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, also missing from Documents referenced);
    - "its handoff" (L1064, L1073, L1074);
    - "the 2026-11-15 handoff" (L663);
    - "each handoff" (L1112).
    - **Fix**: name the files.

28. **MINOR** — L1106: "Still open with the Overtoad (§6, mid-wave sitting)".
    - **Why**: A1's limbs and O13's canopy limb are Group A items (sitting item 8; A5).
    - **Fix**: "(§6)".

29. **NIT**s:
    - L661, "it replaces the handoffs' 'never pull or switch'": it replaces only the pull half.
    - L626 and L846, "the same guarded pulls": ruling 7 adds "on main and clean".
    - L1081, "`1b4fec84`'s ruling" is garbled; "the Overtoad's version ruling in session `1b4fec84`".
    - L683 still says "nor does 0.13.0" and is not updated for 0.14.0.
    - L1652, "cannot support: GHCR images", is stale.
    - L1054, "labels are verbatim", while round 1's and L1252's drop "(Recommended)".
    - L1635 puts the 0.13.0 and 0.14.0 occurrences in the Mitigation column instead of Likelihood.
    - L2256, "The four reviews it cites": "it" is ambiguous.
    - The six primary pulls since ruling 7 match no `git pull` in any of the 18 transcripts written since 2026-11-13 10:00Z, so record them as unattributed or as the Overtoad's own moves.

30. **MINOR** (outside-reader test)
    - **Status bullet (L35–36)**:
      - "the forks'" is undefined.
      - "`APD-ECO-016` … its guard" is never explained.
      - It does not say that rulings 6 and 7 change the restart gate and O13.
    - **Note — sentences that need a handoff to understand**:
      - L1061: round 2's four questions are never stated, and rulings 4–7 are not mapped to Q1–Q4.
      - L1065: "this session" is ambiguous.
      - L1075: "#2555's two interim clauses" is not explained.
      - L1080: "Round 2's tripwire" is undefined.
      - L1083: "three fallback version literals" is unexplained.
      - L1091: "as one change for all three" is unclear.
      - L1097: "the paragraph" and "that arc's ruling 14" are not identified.
      - L1103: "v1's" is used though the plan never calls itself v1 elsewhere.
    - **Note — terms used before, or without, definition**:
      - "flood-4" (L1063) and "carrier" (L1063);
      - "fork-drift guard" (L1059);
      - "went DIRTY", "scoped sites" and "cross-repo arms" (L1078–1079);
      - "APD-DATA-024" (L1093);
      - "N-4" (L1095), which collides with P1's N-4 (`EX/extraction-P1-backup.md` row 81);
      - "the 2026-10-26 rulings" (L1096), defined only in `AGENTS.md`;
      - "the per-lock probe", used at L498 and L503 before L1036 defines it (this predates the revision).

## 3. Judgment calls 1–8

1. **R-ML-TOOLS-2: keep the ID.** It follows R-ML-TOOLS, R-ML-SERVERS and R-ML-RECURRENCE-FLOOR, and "-2" mirrors R-OBS-SC-2. Release IDs do not affect ID coverage, since `2026-10-04_plan_id_coverage.py` counts only path IDs (381 of 381). Drop the §9 row (L1450): no other shipped juniper-ml release has one, and §9 lists dependencies of open work.
2. **Numbering: keep 1–7**, which matches the 11-13 handoff that holds the verbatim text. But:
   - map rulings 4–7 to round 2's Q1–Q4;
   - qualify every bare "ruling N" (L1004, L1043, L1081, L1088, L1109, L1252, L1254, L1255, L1447) as "ruling N of 2026-11-13", because the same note also cites flood-4's rulings 14 and 17.
   "Round 1's ruling N" is fine.
3. **"Ruling 17" lines: cite at the tags.** Tags are immutable and are what ships. Then fix the L1089 lead-in, add canopy `:221`, and reframe the finding as in item 19.
4. **Step 6: keep it**, but say it follows step 4 and runs beside step 5 (the image path and the trio path), and that 0.14.0 is not R-CASCOR.
5. **P3-17: reverse.** Move it to Done as "asked and answered". It is "Ask D-02/D-03" (extraction-P3 row 73), and every part is answered; the cap part is moot for a patch. Leave the data and recurrence floors under P3-18, which is already annotated, and fix L1035 (item 3).
6. **Changed by this plan: list all five tools now**, plus `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/`:
   - State which tools ran: the probe did; the verify tool ran on TestPyPI and the control only; the deploy-pin and lock-move tools are prepared for the deploy PR.
   - The archive is transcript-derived text. §9 (L1464) and H-21/H-22 require the gate plus `--names` and `--all` over those nine files before the push, with keys and counts in the PR body.
   - A count that printed nothing found 9 lines naming an API key, 4 with "secret" and 4 with "token". These are names, not known values.
7. **Validation record: record both reviews before landing**, as v1.15.15 did (counts, and that the findings are applied). The five-PRs handoff set "two independent reviewers" as v1.15.16's bar. Optionally archive their briefs and reports with the other four.
8. **v1.15.15's Status bullet: keep it as history.** Leaving v2 unedited is defensible: it is "paused at the Overtoad's request", and its header says it does not edit v1. But v1 must list v2's stale lines completely (item 20). Ask the Overtoad whether v2 gets a one-line pointer, since its Overtoad packet would re-ask questions already ruled.

## 4. New facts 1–5

1. **juniper-ml#2574** (merged at 03:29:46Z as `7914ba9f`, confirmed): no text change is needed. L2358 already says the handoff landed through ml#2574.
2. **The image probe: record it.**
   - In the 0.14.0 and 0.10.0 bullets (L1082, L1084): pulled by index digest (cascor `sha256:6b3e64bd…`, canopy `sha256:d9a966ff…`), revision labels `bf6f0108` and `57d90dec`, run with no network; each installs observability 0.4.2 and service-core 0.7.2 on Python 3.14.10.
   - In "No running image carries it yet" (L1041): the published images carry the fix, and no deployed service does.
   - Also in the Validation record, in Changed by this plan, and at L1652.
3. **cascor's PyPI hashes: record it** in the 0.14.0 bullet and the first "Still open" bullet. After the gate, cascor's PyPI sha256 will differ from TestPyPI's by design (L1142 says so for 0.13.0), so compare member by member with `…_verify_cascor_0_14_0_canopy_0_10_0_published.py`. Canopy's must match by hash. This corrects the 11-15 handoff's "each wheel's sha256 equals TestPyPI's", which would raise a false alarm.
4. **juniper-deploy's recurrence pin: record it** (confirmed: `docker-compose.yml:598` pins `juniper-recurrence:0.8.0`). Put it in L1107, at §4 step 6 and in §8's deploy row (L1430). The pin PR either moves recurrence to 0.8.1 (its image exists since 2026-11-06, L641) or accepts `--fail-on-stale`'s exit 1. L1148's "passes" was true on 2026-10-30.
5. **The "answered None" print: already recorded, and accurately**, at L1072 and L2254. I confirmed both `user` timestamps and that an untimed `api-request-blob` row follows each one. Optionally list it as a tool defect among the findings.
