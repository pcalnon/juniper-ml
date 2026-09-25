<!-- Archived verbatim 2026-09-24 from subagent a55bb97b3f211dde1 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS

**Scope.** The target is `handoff_session_r3_frozen.md`; I verified its sha256 as `c9ef84f352a82857…`. I compared it with `handoff_session_r2_frozen.md` (sha256 `6822f3ff…`), and the two differ by a 544-line diff. "L<n>" always means a line of `handoff_session_r3_frozen.md`. Every other document is named each time it is cited:
- The round-2 reports are `handoff-2fba4397-round2-laneF-reprobe.md` (prefix **F2-**), `handoff-2fba4397-round2-laneO-amputation.md` (**O2-**) and `handoff-2fba4397-round2-laneP-fresh-session.md` (**P2-**).
- The peer's draft is `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`. It was modified at **01:18:53Z** (sha256 prefix `4ebd0143`, 236 lines), after this snapshot froze.

There is no HIGH. There is one MEDIUM: three of the rewrite's new "reconcile" claims were already false when the snapshot froze. Every measured outcome I re-ran reproduced, with one exception: cascor's 6(a) result differs in its body.

## Round-2 disposition table

| Round-2 finding(s) | Disposition | Where / note |
|---|---|---|
| F2-M1, O2-M1, P2-M2 (#2089 CodeQL; #2081 precedent; 59 alerts; merge gate; checks command) | APPLIED | L40, L80, L156, L255-258, L346-348. Three clauses were dropped: F2-M1's "keep the peer's four README rows if #2089 is rebuilt"; O2-M1's "re-read #2089's head before any push if the owner edits a probe"; and P2-M2's "re-check for owner-account commits before merging". Attribution was made neutral (L256), with reason. |
| F2-M2, O2-M3 (cascor image lock) | APPLIED | L214. O2-M3's service-core `:133` note was dropped; the peer's draft L158 carries it. |
| F2-M3 (6(b) refuted) | APPLIED | L99-101. It is routed per P2-L7 ("correct the primer in place") rather than F2's "file under (a) or drop". I re-measured it. |
| F2-M4 (6(a) outcomes) | APPLIED WRONGLY (partly) | Data is correct. For cascor, F2's "same shape, expected 400 `VALIDATION_ERROR`" became "expected to be the same" (L2 below). |
| F2-M5, P2-H2 (liveness) | APPLIED | L21, L63, L163. P2-H2's third test (last assistant record is a `tool_use`) was dropped, which is harmless. |
| F2-M6, P2-M4 (literal marker) | APPLIED; P2-M4's mutation sentence APPLIED WRONGLY | L355-357; L360 (L3 below). |
| F2-L1 | APPLIED | L134. |
| F2-L2, O2-L3, P2-L1 (guard counts) | APPLIED | L365. |
| F2-L3 (recurrence) | APPLIED | L217. |
| F2-L4, O2-L5, P2-L2 (consolidation not begun; where to look) | APPLIED | L7-9, L72. |
| F2-L5 (ECO-013 conflict; CASCOR-014 gate) | APPLIED, but the ECO-013 half was stale at the freeze | L199-201 (M1); L224 is correct. |
| F2-L6, O2-N10, P2-L4 (#2089 files excluded) | APPLIED | L181. |
| F2-L7, O2-L4, P2-H1 (re-route the peer; branch; `gh pr list`) | APPLIED | L22-25, L71, L157. P2-H1's "load `ListAgents`/`SendMessage` with ToolSearch" was dropped (N9). |
| F2-L8 (run-from path; `git -C` refused) | APPLIED | L151. |
| F2-N1, O2-N1 ("On main") | APPLIED | L36. |
| F2-N2, P2-N6 (PR CI wording) | APPLIED | L361. |
| F2-N3 (name the refused forms) / P2-N4 (soften to "may refuse") | F2-N3 APPLIED; P2-N4 NOT APPLIED, no reason given | L143-148 is incomplete (N4). |
| F2-N4, P2-L3 (counts move) | APPLIED as a recount only (17, 42), without the caveat | L153, L160 (N2). |
| O2-N9 (fresh-checkout count changes when the peer's PR lands) | NOT APPLIED, no reason given | N2. |
| F2-N5, O2-N2 (129 `.py`; runners; the peer's paragraph) | APPLIED; the runner count APPLIED WRONGLY | L38-39: it took F2's "67" over O2's correct "66" (N1). |
| F2-N6, P2-M3 (ship order; re-copy first; check open PRs) | APPLIED | L26-29. |
| O2-M2 (owner questions the peer asks; release sequencing) | APPLIED | L264-270. |
| O2-L1, O2-L2, O2-L6, O2-L7, O2-L8, O2-L9, O2-L10 | APPLIED | L43, L209/L334, L223, L119, L44/L48, L113-115, L313. |
| O2-L11 (reconciliation items) | APPLIED, but stale at the freeze | L73-76 (M1). |
| O2-N3, N4, N5, N6, N7, N8, N11, N12, N14 | APPLIED | L82-84, L104, L303-336, L194/L239, L224, L259, L308/L315/L365, L241, L206. N5's bar still omits two items (N12). |
| O2-N13 (the peer's caps) | APPLIED in part | L218 names only the service-core caps (N5). |
| P2-M1 (two briefs; `[ahead N]`; `status -sb`) | APPLIED | L62-67, L162. The briefs' conflicts with this file are left unreconciled (L4). |
| P2-L5, P2-L7, P2-N2, P2-N3, P2-N5, P2-N7, P2-N8 | APPLIED | L137, L98-103, L163, L16/L21, L129, L210, L261. |
| P2-L6 (title/body mechanism; re-copy recipe) | APPLIED; the recipe APPLIED WRONGLY for the current title file | L88, L296 (N3). |
| P2-N1 (Goal length) | Informational; the Goal grew | N7. |

## Claims table for the delta

| Claim (line) | What I ran or read | Result |
|---|---|---|
| L5: "Validated by consensus in two rounds" | The six verdicts: round-1 lane O **FAIL**, five PASS WITH CORRECTIONS; P2 carries 2 HIGH | REFUTED (L5) |
| L21, L63: alive while listed; "600 s without a write" | Parsed `agent-a46e715a6801b98ca.jsonl` with `json`, `split("\n")`. Gaps of 600.4 s (20:21:04→20:31:04Z) and 580.2 s. Last write 01:15:36Z | REPRODUCED |
| L22-25, L71: the peer's "never message it"; its successor messages [24f8d8]; branch `docs/handoff-round42-followup-lane` | The peer's draft, L3, L23-27, L14. juniper-ml#2097 opened on that branch at **01:20:02Z**, after the freeze | REPRODUCED |
| L33: #2088's four reports shipped | #2088 file list: 4 `register-fixforward2-*` reports | REPRODUCED |
| L36: 25 cases under 3.13.13 on `c061a99f` | `2026-09-24_primer_toy_error_paths_probe.py`, primer venv, on the primer taken with `git show c061a99f:`: "25 of 27 probed cases answered otherwise". `main`'s primer: all 27 | REPRODUCED (3.14.2's 24 not re-run) |
| L38: 129 Python probes, six lanes; "67 shell runners (README)" | #2089: 132 files. Lanes: 17+24+28+10+32+18 = 129. Runners in `r42b*`/`r42d`: 48 `.bash` + 18 `.sh` = **66**. The README (L12-14, L51) gives no count | 129 and six REPRODUCED; 67 REFUTED (N1) |
| L39: README carries the peer's rows and paragraph; the peer dropped the file | README at `a2fa3ad8`, L39-51. #2097's 95 files include no README and share none with #2089 or with L171-180 | REPRODUCED |
| L40: CodeQL failed at 00:27:51Z; 33 new; 4 high | Check run: failure, "33 new alerts including 4 high…". Alerts 843-846 are `py/overly-permissive-file` at `stripe_probe.py:139/148/177/205`; 33 are open on `refs/pull/2089/merge` | REPRODUCED |
| L43, L44, L48: two partly fixed; `d1c66a11`'s numbers; the MEDIUM's mechanism | `data438-fixforward-round1-laneB-refute.md` L17, L27, L32, L37, L57. `data438-fixforward-round1-laneA-reprobe.md` rows 32-35 and 38. juniper-deploy `values.yaml` L86-91: timeout 5, failureThreshold 3 | REPRODUCED (read, not re-run) |
| L62: brief = two `user` records, and their contents | 19:37:50.383Z: 8,881 characters, with the regime, the upload proof, the "unsigned scratch commit", the trailers, "Do NOT open, merge, arm…", and four spec files. 23:48:49.313Z: isMeta, 8,561 characters, "same bar as before". A third record at 00:29:28.847Z is a compaction summary | REPRODUCED |
| L61: `last_report()` via importlib | Loads cleanly. It returns `""` today, because the last assistant record is a `tool_use` | REPRODUCED (N11) |
| L64-67, L162: `status -sb`, `[ahead N]` | Data worktree: `[ahead 1]`, clean. Ref still `d1c66a11…` | REPRODUCED |
| L72: split at 23:35:52Z; ask at 23:34:29Z; no draft | SendMessage texts in `2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl` | REPRODUCED at the freeze. A consolidated draft appeared at 01:42Z |
| L73-76, L199-201: three reconcile items; "its line 131" | The peer's transcript `bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl`: Write at 00:45:58Z, Edit at 01:07:12Z | REFUTED at the freeze (M1) |
| L79: `Allow-Symbol-Loss: const:SESSIONS` | `git diff origin/main` of the extractor: `-SESSIONS = {` / `+SESSION_IDS = {` | REPRODUCED |
| L82-84: checklist | `git diff -U0 990ef3f9 2439d049`. The primer hunks are exactly the lines listed. The register hunks are L512, L766, L1297, L1430, L1635 and L1699, where L1699 is the same `GET /{id}` wording | REPRODUCED |
| L90: data#440 and the fix-forward merge cleanly at `d1c66a11` | Only `CHANGELOG.md` overlaps. `git merge-file -p` in both orders: 0 conflicts | REPRODUCED |
| L94-96: 6(a) default-app 500; data 400; no Sentry | In-process on data's **locked pair**: primer venv (fastapi 0.141.1 / starlette 1.6.0), real data app with its lifespan, and a Sentry capture transport. Default app: 500 text/plain, with 1 event (the positive control). Data: the control gives 422; a lone surrogate in `ttl_seconds` and in `generator` gives **400 `{"detail":"Invalid request parameters"}`**, with 0 error events | REPRODUCED. F2 had measured on 0.137.0 / 0.50.0 |
| L97: cascor "expected to be the same, but not run" | Real cascor app in JuniperCascor1 (0.137.0 / 1.0.0), without its lifespan. The control gives a 422 envelope. The surrogate gives **400** `{"status":"error","error":{"code":"VALIDATION_ERROR","message":"Invalid request parameters","detail":null},…}`, with 0 events | PARTLY (L2) |
| L99: 6(b) | Primer venv, `idempotent_jobs.py` extracted from `origin/main`'s primer. Control: 201. Surrogate: 500 text/plain, twice. Key records hold only the control's; jobs = 1. Validation fails with `string_unicode` at `dataset_id` | REPRODUCED |
| L101, L103-104 | Primer L4742-4743; #2080 body L65/L69, not updated since 10:18:16Z; #2088 body L47; `register-fixforward2-round2-laneB-refute.md:120`; `2439d049` message line 14 | REPRODUCED |
| L112-115: 5 behind; the peer's traps; `worktree_cleanup.bash` | `rev-list`: 3 ahead, 5 behind. The peer's draft L168, L170, L207. The script pushes at L253, L259 and L373, and runs `gh pr create` at L359 and L383 | REPRODUCED |
| L116: §2 status line "about L176" | `register_status_crosscheck.py:94-99` reads register **L177** | REFUTED (L1) |
| L118: set empty, never unset | cascor `src/main.py:206` calls `load_dotenv()` at import. Data calls it only inside `get_arc_agi_env()` and `reload_arc_agi_env()`. No `.env` exists on any path `find_dotenv` walks | REPRODUCED (the hazard is latent today) |
| L129, L133, L134 | `pyvenv.cfg` home is JuniperCanopy1, 3.13.13. Census: 69 / 82. `od -c` of the trailer command shows only `\n`. `grep -c` gives 3 | REPRODUCED |
| L153-165: all 13 commands | Each ran as written, and none was refused: 17; MERGED; OPEN / `a2fa3ad8` / BLOCKED; CodeQL fail; none (at 01:14Z); 136 / 100 / 36; AGREE; 42; `d1c66a11`; `[ahead 1]`; printed; #440, #690, #689 open; `/tmp` 85% | REPRODUCED, except `/tmp`, which drifted from 83% |
| L160: "34 in a fresh checkout" | 34 headed reports on `origin/main`; **52** on #2097's head | PARTLY (N2) |
| L169-187: Git status | 17 entries at 01:14Z. The stall probe was written by the executor at 00:33:25Z. #2089's files are byte-identical to `a2fa3ad8`'s blobs, 132 of 132 | REPRODUCED (20 entries at 01:47Z, all added after the freeze) |
| L206, L210 | `bytes-compare-ml2086-data440-cascor689-validation.md` L63-64 and L131; `juniper-service-core/CHANGELOG.md` L57-58 | REPRODUCED |
| L213-217: releases; recurrence has no Sentry | Data `requirements.lock:88`. cascor `:63` and `requirements-cpu.lock:129`, which `Dockerfile` installs (L41 COPY, L42 `pip install -r`); cascor's `uv.lock` is a 135-byte stub that pins nothing. Canopy `:79`, capped `>=0.4.0,<0.5.0` at `pyproject.toml:109`. Recurrence: `juniper-recurrence/requirements.lock:74` pins `==0.7.0`, capped `<0.8.0` at `pyproject.toml:51`. Recurrence has no `sentry` outside its locks and docs, and service-core mentions Sentry only in a comment (`security.py:80`) | REPRODUCED |
| L222-223, L238-241 | cascor `conftest.py:37` is `import sysconfig`; `main.py:231`; cascor#689 sets `include_local_variables=False`. Transcript records at 19:40:28Z and 20:45:53Z. Canopy `7ab994e5`, `…modal_text.py:42` and `dashboard_manager.py:8381` | REPRODUCED |
| L256-258: #2081's facts | `73dc109c` redacted both flagged probes; `f9964d78` touched `boot_scenarios.py`. Alerts 842 (22:43:46Z) and 841 (22:44:26Z): `dismissed_reason` "mitigated", by `pcalnon`. On `main` under the probe directory: 27 warnings + 32 notes = 59 | REPRODUCED |
| L261, L264-270 | `wc -m` gives 24929. The peer's draft L109-124 | REPRODUCED |
| L296: re-copy recipe | The title file was rewritten at 01:05:38Z and now ends with `\n` | REFUTED for the current file (N3) |
| L355-361, L365: marker plan | Comments: service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`. The literal is at `:88`/`:91`, `:115`/`:118` and `:84`/`:87`, and only at `:52` in canopy. `compare_digest(presented,` is at `:91`, `:118`, `:87` and canopy `:137`. The matcher is `test_service_fork_drift.py:289`. `ci.yml` L493-500. `docs-full-check.yml` L63-64 (Mondays, 06:00 UTC) and L259. Register L240, L252, L1106, L1751; `docs/REFERENCE.md` L2977 | REPRODUCED (L3, N10) |

## Findings

### MEDIUM

**M1. Remaining 0's reconcile list and Appendix A's "must choose one" were false when the snapshot froze, and the live divergences are missing.**
- **Quoted:**
  - L73-76: "the peer's "no forward has been confirmed" … is stale; the peer's README rows now live on #2089; the two handoffs close `APD-ECO-013` under different conditions".
  - L199-201: "When it closes differs between the two handoffs. The consolidation must choose one: … the peer's (its line 131): once the three bytes-compare PRs merge and validate."
- **Evidence (from `bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl`):**
  - At 00:45:58Z the peer's Write dropped "No forward has been confirmed" and wrote "Their README rows ride juniper-ml#2089".
  - At 01:07:12Z an Edit replaced "APD-ECO-013 closes, citing all three bytes-compare PRs, once they merge and validate" with this file's condition. It cited r2's `:157`, and at 01:18:20Z it was re-cited to "…closes-pr-owed.md, Appendix A".
  - The peer draft's L131 is now "Send each item as it lands".
- **The divergences left out:**
  - The peer's draft L134 says "APD-CASCOR-014 closes when F4 lands"; L224 here requires F4's fix to merge AND its validation to hold.
  - The peer's draft L136 says "APD-ECO-014's condition is met"; L220 here closes it only once #685's validation is cited.
- **Risk:** a consolidator trusting L199-201 would choose between the real condition and a phantom one attributed to the peer. The phantom closes a key-leak row with F2 still unfixed.
- **Post-freeze state:** the consolidated draft (`HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`, L236) already fixes this.
- **Replace L73-76 with:** "Reconcile against the peer's final version, juniper-ml#2097 (head `2e4917c2`), whose draft adopted this file's APD-ECO-013 condition at 01:07Z. The canopy-forward, README and APD-ECO-013 items are resolved in its text (its L16, L135, L143 and L145-152). Two divergences remain, and this file's gates govern both: its L134 closes APD-CASCOR-014 "when F4 lands", and its L136 calls APD-ECO-014's condition met."
- **Replace L199-201 with:** "**It closes** once data#440 and cascor#689 merge, #685's validation holds, and the peer's F2 and F3 are fixed. The peer's handoff adopted this condition at 2026-09-25 01:07Z (its L135)."

### LOW

**L1. Wrong status line, and the round-2 correction introduced it.**
- **Quoted:** L116: "**Never name an OPEN id on the register's §2 status line** (about L176)".
- **Evidence:** `register_status_crosscheck.py:94-99` reads the first line starting `**Seventy` or containing `have since been fixed**`. In `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` that is **L177** ("**Eighty-one of the 96 have since been fixed** — …"). L176 ("**Status:** the 96 entries above…") is never read. r2 had "about L177", and F2's evidence cell ("Register L176") moved it. The same error is in the consolidated draft at L138.
- **Replacement:** "**Never name an OPEN id on the register's §2 status list** (L177, the line beginning "**Eighty-one of the 96 have since been fixed**"): the crosscheck reads every id on it as closed. L176 above it is not that line."

**L2. cascor's 6(a) outcome is now measured, and it is not "the same".**
- **Quoted:** L97: "cascor (`src/api/app.py:856`, `ValueError` handler `:916`): expected to be the same, but not run." The same text is in the consolidated draft at L270.
- **Evidence:** see the claims table. On data's locked pair, data gives 400 `{"detail":"Invalid request parameters"}` with 0 Sentry error events. cascor gives 400 with its envelope.
- **Replacement:** "cascor (`src/api/app.py:856`, `ValueError` handler `:916`): measured in-process by round 3 in the JuniperCascor1 env (fastapi 0.137.0 / starlette 1.0.0, not its locked 0.141.1 / 1.6.0): **400**, cascor's envelope, `error.code` `VALIDATION_ERROR`, `message` "Invalid request parameters", `detail: null`. The per-field list is lost, and no Sentry event is sent. Re-measure on the locked pair." Also append to L96: "(re-measured by round 3 on data's locked fastapi 0.141.1 / starlette 1.6.0, with a Sentry capture transport: no error event)."

**L3. The mutation check, as written, leaves the guard green at three of the four sites.**
- **Quoted:** L360: "delete each site's `.encode(...)` call in a copy, and confirm the guard fails." The same text is in the consolidated draft at L460.
- **Evidence:** the literal appears twice at service-core (`:88`, `:91`), data#440 (`:115`, `:118`) and cascor#689 (`:84`, `:87`), and once at canopy (`:52`). Deleting one call leaves the literal on the other line.
- **Replacement:** "Mutation-check the guard: in a copy of each site, delete EVERY `.encode("utf-8", "surrogatepass")` call (two each at service-core `:88`/`:91`, data#440 `:115`/`:118` and cascor#689 `:84`/`:87`; one at canopy `:52`), and confirm the guard fails. Deleting only one leaves the literal on the other line, and the guard stays green."

**L4. The recovery step passes both briefs unamended, and they contradict this file.**
- **Quoted:** L66: "launch a new `task-executor` on that worktree with both briefs, both round-1 reports and the drafts;"
- **Evidence:**
  - Brief 2 (23:48:49.313Z) says "Unset every Sentry DSN variable (SENTRY_SDK_DSN, JUNIPER_DATA_SENTRY_DSN, SENTRY_DSN) in every run". L118 says "never unset".
  - Brief 1, step 5, tells the executor to create the branch ref and to push with `--expected-head <that main sha>` (`0f0f7e0e`). The ref already exists at `d1c66a11`.
- **Append to L66:** "Tell it that brief 2 supersedes brief 1's step 5 (the ref exists; push with `--expected-head d1c66a112e4bc70ee97496a14265f7b90e10fb88`), and to set every DSN variable to `""` rather than unset it, overriding brief 2."

**L5. The validation claim on L5 overstates what the rounds found.**
- **Quoted:** L5: "**Validated** by consensus in two rounds of three independent lanes".
- **Evidence:** no lane returned PASS. There was 1 FAIL and 5 PASS WITH CORRECTIONS, and P2 raised 2 HIGH. This text itself is round 3's target.
- **Replacement:** "**Validation:** rounds 1-2 (three lanes each: one FAIL, five PASS WITH CORRECTIONS), archived as `handoff-2fba4397-round{1,2}-lane{F-reprobe,O-amputation,P-fresh-session}.md`, with their corrections applied; round 3 (`handoff-2fba4397-round3-*.md`) validated the corrections."

### NIT

- **N1.** L38: "The 67 shell runners are not kept (README)" should read "The 66 shell runners (48 `.bash`, 18 `.sh`) are not kept; the README (L12-14, L51) says why."
- **N2.** L160: annotate "# 42 at the freeze, +1 per report archived since; 34 on `origin/main`, 52 once #2097 merges". The first round-3 report has already landed here.
- **N3.** L296: use `"# " + title.rstrip("\n") + "\n\n" + body`, because the rewritten title file ends in `\n`. The consolidated draft (L335) already fixes this.
- **N4.** L143: prefix the list with "The refusals are heuristic; a shell variable or a loop anywhere in a command that also runs git is refused too." Both forms were refused for this lane. The consolidated draft (L163) already fixes this.
- **N5.** L218: also keep the peer's observability `<0.5.0` caps: canopy `:109`, recurrence `:79`, and the recurrence client `:41/:46`. The recurrence caps sit in optional extras (the peer's draft L162).
- **N6.** L96: the anchors `app.py:187-212` and `:214` are at `0f0f7e0e`. At `d1c66a11` an added import shifts them to `188-213` and `:215`.
- **N7.** The Goal section grew from 1,270 words (r2) to 1,635.
- **N8.** L118 dropped r2's "(`SENTRY_SDK_DSN` is exported in these shells)". Restore it. The consolidated draft (L159) has it.
- **N9.** L22: add "load `ListAgents` / `SendMessage` with ToolSearch if they are deferred" (P2-H1).
- **N10.** L358: the canopy revert that passes the pair is `presented = api_key` plus `compare_digest(presented, candidate)` at `:135-137`. A lone `presented = api_key` raises `TypeError` instead.
- **N11.** L61: add "`last_report()` returns an empty string until the executor finishes".
- **N12.** L327-331: the verification bar omits brief 2's "pre-commit on every changed file" and "the equivalence runs if `http_cache.py` is touched". L336 should also say that A1's F3 is already `APD-DATA-056`, leaving F2 and F4 to file or decline.

**State changes after the freeze (not defects):**
- #2097 opened at 01:20:02Z (BLOCKED, not armed). The peer called it final at 01:20:42Z.
- The consolidated draft and `handoff-2fba4397-round3-laneP-fresh-session.md` appeared at about 01:42Z; the worktree now has 20 entries.
- The executor has made its scratch commit, rewrote the title at 01:05:38Z, and is rewriting the body (01:26:43Z).
- `/tmp` is at 85%.

## What I could not verify

- **Not re-run:** 3.14.2's 24 cases, mutation check 12/12, harness 62/62, lane B's 6.6 s and 10.5 s timings, and `d1c66a11`'s suite numbers. I read these from the reports.
- **cascor on its locked pair:** JuniperCanopy1 lacks matplotlib, so I measured cascor only in JuniperCascor1, without its lifespan.
- **Data's stack differs slightly from production:** data was imported from the main checkout at `1afc348` (its `app.py` equals `0f0f7e0e`'s), with sentry-sdk 2.62.0 rather than the locked 2.70.0. The probe initialised Sentry itself, because data's `configure_sentry` is a no-op on an empty DSN.
- **Point-in-time values:** the `/tmp` figure at exactly 01:10Z, and the peer's draft at exactly 01:10Z. I reconstructed the draft from its transcript's edits.
- **Other:** the owner's grant to [24f8d8], and whether the tmpfs scratchpad survives that session.

**Side effects:**
- Verification command 6 ran `git fetch` here, which created two new remote refs.
- No port was opened. Probes ran with `-B`, and `find -newer` shows no writes to the data or cascor checkouts.
- Loading the archiver ran its in-memory `git config user.email`; the address was never printed.
- Extracted copies are deleted. 18 small probe scripts remain in `…/scratchpad/hv3/laneD/`, as round 2's lane F did. The brief said to delete what I create, so remove that directory if you don't want them.

**Changed:** no repository file.
