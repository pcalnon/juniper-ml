## Verdict

Almost every fact in the v1.15.16 revision of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` matches its primary source. I found one BLOCKER and three MAJORs, and the BLOCKER plus two of the MAJORs sit where the re-probe does not look. These held when re-derived:
- **GitHub:** all 26 PRs it names (state, merge or close time, merge commit, files), the three Releases, and the six runs with their jobs, approvals and pending gates.
- **Registries:** PyPI and TestPyPI files, hashes and floors, and the GHCR tags.
- **Repos:** the floors on `main`, juniper-deploy's pins (in `docker-compose.yml` and also in Helm `values.yaml`), and the locks at `v0.14.0` and `v0.10.0`.
- **Citations:** every `file:line` cited, read at its ref.
- **Defect register and CI:** the two `APD-ECO-016` rows, the note on `APD-ECO-010`'s row, and the Docs Full Check log (17 tests, OK).
- **Owner rulings:** all 14 labels, times and option texts, read from the transcripts.
- **Host:** the primary on `main` at `eeb5c694`; parent `AGENTS.md` at `f3f69b34…` (mtime 23:54:29.62Z), with its prior copy at `90df2783…`; both environments at 0.4.0/0.5.0; trio ports closed.

Both `pypi` gates were still waiting at 04:19Z (my own read) and again at 04:36Z (my run of the re-probe: 156 PASS, 0 FAIL). The defects are listed below.

## Findings
Line numbers are in `…CONSOLIDATED-DEVELOPMENT-PLAN.md` as it stands now.

**1. BLOCKER — `…DEVELOPMENT-PLAN.md:1086`.** The canopy review tally is wrong.
- **Text:** "Round 1 found 2 BLOCKERs, 4 MAJORs and 5 smaller items in cascor's, and 5 BLOCKERs and 9 smaller items in canopy's … round 2 found 24 of 25 corrections resolved, and the last was fixed."
- **Evidence:**
  - `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/notes-round-1_report.md` lists 15 canopy items: 1–5 BLOCKER, 6–11 MINOR, 12–15 NIT. That is 10 smaller items, not 9.
  - `notes-round-2_brief.md` says: "Applied: cascor 1-11 …; canopy 1-14. canopy 15 (the category order) was left as is." `notes-round-2_report.md` agrees: "all 25 applied corrections: 24 are RESOLVED, and one (canopy 10) introduces a minor new problem" and "15. Not applied, by choice."
  - Cascor's 2/4/5 is correct. Canopy 10's follow-up fix did land (the canopy `v0.10.0` Release body, line 426).
- **Fix:** "…and 5 BLOCKERs and 10 smaller items in canopy's, … 25 of the 26 were applied (canopy's item 15, the order of its categories, was left as is); round 2 found 24 of the 25 resolved, and the 25th (canopy 10), whose new wording raised a MINOR, was reworded."

**2. MAJOR — `…DEVELOPMENT-PLAN.md:2388`, under 2385.** The memory record leaves out two files `1b4fec84` changed.
- **Text:** "by `1b4fec84` (2026-11-14 23:54:29Z): the parent `Juniper/AGENTS.md` (…)". Line 2385 says the list comes from "their transcripts' Write and Edit calls and memory-writing commands".
- **Evidence:**
  - In `1b4fec84`'s transcript, a Bash call at 2026-11-15T02:53:56.520Z (result `ok`) inserts a bullet into `reference_worktree_isolated_session_command_refusals.md`. The same command appends the "A DIRTY PR cannot be cured…" bullet (about #2573/#2576) to `reference_commit_pr_mechanics_hub.md`.
  - Both files have mtime 2026-11-15T02:53:56Z. The plan credits neither to `1b4fec84`; their only mentions are lines 2368 and 2386, for other sessions.
  - The session's other memory-naming commands (23:42:29Z, 00:00:58Z, 02:53:40Z, 02:53:43Z) are reads.
- **Fix:** add "and on 2026-11-15 (one command at 02:53:56Z) `reference_worktree_isolated_session_command_refusals.md` (a bullet inserted before its index digest) and `reference_commit_pr_mechanics_hub.md` (a bullet appended); it did not change `MEMORY.md`." The ecosystem's rule on naming every changed document makes this must-fix.

**3. MAJOR — `…DEVELOPMENT-PLAN.md:1054` and `:2254`.** The re-probe's coverage is overstated.
- **Text:** "…`2026-11-15_r_obs_sc_2_followups_record_reprobe.py` re-checked the other facts on 2026-11-15 (0 FAIL)." Line 2254 says "re-checked its other facts".
- **Evidence:** the probe passes 156/0 while findings 1 and 2 are present. It has no check for the review tallies, the memory records, or the items in §3 below, and line 2255's own list is narrower than "the other facts".
- **Fix:** "re-checked the facts listed below (0 FAIL); the review tallies, memory records and option texts were read by hand from the archived reports and transcripts". Or add those checks to the probe.

**4. MAJOR — `…DEVELOPMENT-PLAN.md:1049`, and the same pattern at 1048 and 1051.** Three statements are worded as current but are no longer true.
- **Text:**
  - 1049: "The forks' `RateLimiter` still truncates with no floor (…), so … `Retry-After: 0` was live…"
  - 1048: "juniper-ml's `[tools]` floors `juniper-observability>=0.4.1`"
  - 1051: "cascor and canopy pass no `telemetry=`…"
- **Evidence:**
  - On `main`, data's `security.py:243` returns `max(1, math.ceil(...))`. The truncation was at `:250`/`:254` of `c68e6b4c`, the parent of data#537.
  - juniper-ml's `pyproject.toml:98` reads `>=0.4.2`.
  - cascor `src/api/app.py:778` and canopy `src/main.py:546` both pass `telemetry={`.
  - The writer changed "is" to "was" on line 1049 but kept "still truncates", which contradicts its own sub-bullet at 1050 ("Fixed 2026-11-13").
- **Fix:** past tense with the date: "truncated with no floor on 2026-11-09", "floored `>=0.4.1`", "passed no `telemetry=`".

**5. MINOR — `…DEVELOPMENT-PLAN.md:1089`.** The findings' source is neither named nor archived.
- **Text:** "the behaviour each states is its reviewer's, not re-run here."
- **Evidence:**
  - Lines 1090–1098 come from `6e3bdef0`'s five-PR validation (A-4, A-5, B-8, B-9, B-10 and others). Their only copy is `tmp/lps/fixpass_r1.md` in the gitignored `tmp/` of worktree `logical-percolating-sparkle`. Only `HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md:61-77` names it.
  - It is not among the four archived reviews, and `git worktree remove` would delete it.
  - Lines 1100–1102 come from `notes-round-1_report.md`, and line 1099 from `HANDOFF_2026-11-13_…:268`.
- **Fix:** give each finding its source, and archive `fixpass_r1.md` with the four reviews.

**6. MINOR — `…DEVELOPMENT-PLAN.md:1092`.** B-9's comparison is widened beyond what was checked.
- **Text:** "canopy's `_evict_expired` (`:234`) then answers differently from the others."
- **Evidence:** B-9 (`fixpass_r1.md:167`) compares canopy with cascor only. Data evicts through a `TTLCache` (`juniper_data/api/security.py:260`); nobody compared it. Service-core's prune at `:170-177` is identical to cascor's at `:156-163`.
- **Fix:** "…differently from cascor's and service-core's (identical prunes); data's TTLCache path was not compared."

**7. MINOR — `…DEVELOPMENT-PLAN.md:1087`, `:2256` and `:2347`.** The review archive is untracked, and the plan's change list does not name it.
- **Evidence:**
  - `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/` is untracked (`??`) and not ignored (`git check-ignore` exits 1).
  - Line 2347 names only the writer and the re-probe. It leaves out the archive directory and `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`, although the archive's `README.md` says it was made "as plan v1.15.16 records".
- **Fix:** add both to line 2347 if they ride this PR. Otherwise, stop calling the reviews archived.

**8. NIT — `…DEVELOPMENT-PLAN.md:1062`.** "each one signed commit" is ambiguous. Each PR landed as one GitHub-signed squash commit (all five verified: one parent, `valid`), but ml#2555's branch had 3 commits and cascor#757's had 2. The handoff's wording is "each one GitHub-signed commit, squash-merged". Use that.

**9. NIT — `…DEVELOPMENT-PLAN.md:838, 1247, 1252, 1253`.** These quote "In release PRs", "Floor PR, then 0.11.5" and "Guarded session pulls" without "(Recommended)", while line 1054 says "Option labels are verbatim" and line 1071 quotes the marker. Either add the marker or state the convention ("less the (Recommended) marker").

**10. NIT — `…DEVELOPMENT-PLAN.md:2254`.** "five sessions' transcripts" should be six. Line 1095 dates flood-4's answer from `f2b4e7c3`.

**11. NIT — `…DEVELOPMENT-PLAN.md:1103`.** ml#2576's body says "a second passage near its §6 A1 follow-ups" and gives no line number for the v2 draft. "Line 153" is correct (`…PLAN-V2.md:153` on `main`), but it is the plan's addition, not the body's.

**12. NIT — `…DEVELOPMENT-PLAN.md:1089`.** "re-read on `main`" does not cover line 1102, whose CHANGELOG lines were read at `v0.14.0` and `v0.10.0`. Add "(the two CHANGELOG lines at the release tags)".

**13. NIT — `…DEVELOPMENT-PLAN.md:1085`.** The dates are correct, but R-CASCOR's 0.13.0 note at line 1139 gives times. Add them: runs created 01:28:21Z and 01:41:32Z, so 2026-12-15 01:28Z/01:41Z and 2026-12-20 01:28Z/01:41Z.

**14. NIT — `…DEVELOPMENT-PLAN.md:1096`.** The reviewer measured the failure with "mini-roots and lane scratch" in `tmp/` (`fixpass_r1.md:242-243`). Say "whenever `tmp/` holds any `pyproject.toml`".

**15. NIT — `…DEVELOPMENT-PLAN.md:2256`.** In "The four reviews it cites", "it" reads as the probe, which cites no reviews. Make it "v1.15.16 cites".

**16. NIT — `…DEVELOPMENT-PLAN.md:1107` and `:1262`.** These list juniper-deploy's pins as Overtoad items. Per `HANDOFF_2026-11-15_…:54,58`, a session opens the pin PR after the gates, on the Overtoad's merge approval.

**17. NIT — `…DEVELOPMENT-PLAN.md:626`.** "the same guarded pulls" understates ruling 7, which adds "on `main` and clean" and "never switch its branch". Lines 657–658 state both.

## Claims the re-probe does not check
(I checked each by hand; all hold except findings 1 and 2.)
- The four reviews' tallies, outcomes and models (lines 1080, 1086). The models are confirmed `opus` in the agents' `meta.json` files.
- The memory records (lines 2363, 2385–2388).
- Option-description paraphrases and which question each label answered (lines 503, 659–660, 849–850, 1057–1060, 1065–1071). The probe checks labels and times only.
- Round 2's "(No answer provided)", `7d425759`'s four questions, and the `api-request-blob` explanation (line 1072).
- "each one signed commit"; ml#2573's seven files and its DIRTY state; the tool lists of ml#2555 and ml#2558 (the probe sets their files to `None`).
- "eleven scoped sites in four copies" (true per ml#2576's body); "the only workflow that runs the cross-repo arms" (ci.yml runs the guard, but the arms skip without sibling checkouts); that the note sits in `APD-ECO-010`'s row (the probe only checks it appears somewhere in the register).
- The QUICK_START diff; the content of ml#2558's co-change commit; the misfiling #2360 caused.
- The primary at `eeb5c694`, the two `AGENTS.md` hashes and the 23:54:29Z time (the probe prints these as INFO only); the prior copy's path; "ran first" (the log at 23:53:08Z, all OK).
- The day-30/35 dates; data#537 as "flood-4's carrier"; data#501 and ml#2534 as origins; `f2b4e7c3`'s option text; "notes name no F-S10"; "no design on `main`".
- Helm `values.yaml` pins (the probe reads `docker-compose.yml` only).

## What I sampled rather than checked in full
- **Findings' behaviour:** I re-ran none of it (e.g. "3 tests fail"). I checked only the cited lines and the source list.
- **Memory scan:** it covered tool inputs that name memory paths, in five main transcripts plus sub-agent transcripts. A write made by a script whose path never appears in a command would be missed. Modification times since 2026-11-09 showed nothing else attributable to these sessions.
- **Transcript text:** question backgrounds were cut at 900 characters; option texts were read in full.
- **Other limits:**
  - I verified "eleven sites" from ml#2576's body and round 2's "88 = 8 × 11", not by parsing the guard.
  - I checked only one unchanged line (1052, still true: legs `:8052` and `:8053` write about 51 MB each to `/tmp/juniper-e2e/`).
  - The primary's fast-forward at 2026-11-15 02:04:55Z (`4a786c81` → `eeb5c694`) appears in no session transcript, so it was presumably the Overtoad's own move.

**Changed:** no repository file. Scratch only, under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humble-humming-flask/tmp/review-a/` (gitignored).
