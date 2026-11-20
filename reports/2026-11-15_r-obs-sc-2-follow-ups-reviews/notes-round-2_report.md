I've verified all 25 applied corrections: 24 are RESOLVED, and one (canopy 10) introduces a minor new problem. That one comes from my own proposed wording. No edit landed outside its release's section, every "above"/"below" points the right way in the rendered order, and nothing was dropped by accident. I edited nothing.

## How I checked

- **Trees:** `diff -rq` finds only `CHANGELOG.md` differing between `tmp/s2/eco-head/juniper-*` and `tmp/s2/eco-corr/juniper-*`.
- **Sections:** cascor's hunks sit at head lines 122-303, inside `[0.14.0]` (10-321). canopy's sit at 108-430, inside `[0.10.0] - 2026-11-15` (12-458). `[Unreleased]` and canopy's old `[0.10.0] - 2025-12-06` section (now line 5163) are untouched.
- **Nothing dropped:** a whitespace-blind word diff shows 69 change runs for cascor and 32 for canopy, every one inside an intended span.
- **Rendering:** both `filled2_*` bodies are verbatim renders of the corrected sections, apart from the dropped blank lines as before.
  - The headers differ from round 1 only at line 10, which equals the intro text in `2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py`.
  - No template placeholder survives.
- **Idempotency:** `2026-11-15_cascor_canopy_release_notes_corrections.py --check` reports "every edit is at target" for both trees.
- **Leftovers:** neither body still contains "R-OBS-SC-2", "60 pins", "Same record", "next update", "record-update PR", "later pass", "caps pytest", "does not hold the token" or "One path". The one remaining "Not fixed here." (cascor line 293) is a separate #735 item about eight self-timed assertions, and it is still true at the head.
- **Re-probed just now:** juniper-data's latest release is still 0.17.1, juniper-observability's is still 0.4.2, and juniper-data `main`'s `notify-consumers.yml:78` still lists juniper-canopy. The flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) is byte-identical to round 1: "Updated: 2026-11-09", §8 items 1-14.

## juniper-cascor v0.14.0 (`filled2_cascor_0_14_0.md`)

Top-level entries render in this order: paused-fit 105, Bandit comment 144, stop-then-start 213, pytest 9.2 258, five documents 262, memory budget 267, nightly lanes 280, conftest 298.

1. **RESOLVED.** Lines 276-278. "The nightly-lanes entry below" points to line 280.
2. **RESOLVED.** Line 296. The quoted heading is the line-262 entry, above it.
3. **RESOLVED.** The new item at line 137 sits where the old one did, between "Measured locally" and "Docs".
   - "The Overtoadship check above" is the sub-bullet at line 117. The quoted "A start sent after a stop no longer cancels it" is the entry at line 213, below.
   - Line 257 now reads "(the stop-then-start item of the paused-fit entry above)".
   - "record-update PR" and "Candidate fixes, which no ruling chose" are gone.
   - The condensation deliberately drops three details: "every further start … queues another run", "(`mark_completed` is refused from `STOPPED`)" and the juniper-service-core contrast. The #756 entry carries the second one.
4. **RESOLVED.** Line 291. "(the pytest 9.2 entry above)" points to line 258. The dropped "prints the versions it got" is still stated in the line-258 entry.
5. **RESOLVED.** Line 288. The quoted heading is the line-298 entry, below.
6. **RESOLVED** (the "qualifies" form).
   - Line 295 now qualifies the count, and "(the Bandit SARIF comment entry above)" points to line 144.
   - Line 148 points to line 280 and is now true.
7. **RESOLVED.** Line 10.
8. **RESOLVED.** Lines 308-309.
   - "a plain patch" now agrees with the header.
   - The continuation "The image installs `requirements-cpu.lock` (`Dockerfile:42`)." is intact.
   - The 73 / 54 pin counts still hold.
9. **RESOLVED.** Line 257, confirmed against the re-fetched record.
10. **RESOLVED.** Lines 275 and 289. Optional nit: line 289 says "At that change" inside #735's own entry, where line 275 says "At this change". That was my wording.
11. **RESOLVED.** Line 10.

## juniper-canopy v0.10.0 (`filled2_canopy_0_10_0.md`)

1. **RESOLVED.** Line 10. "The first" correctly refers to query strings.
2. **RESOLVED.** Line 391. The lock holds 60 pins at `b4b01904` (#806) and 61 from `95436541` (#810) through `1c2dbd01`, so the "so … 61 pins" arithmetic holds. "(`Dockerfile:40`)" is kept.
3. **RESOLVED.** Line 208. It now agrees with the #802 entry (lines 88-89), and the flood-3 citation after it is kept.
4. **RESOLVED.** Line 124, confirmed by the re-probe above.
5. **RESOLVED.** Line 368. Only `fbf01dff` touched a conda file in the window, so "moves only `conf/conda_environment.yaml`" is right. The trailing sentence is kept.
6. **RESOLVED.** Line 399.
7. **RESOLVED.** Line 10.
8. **RESOLVED.** Line 234 names the flood-3 record directly, and line 238 ("that flood-3 record") now follows it. This matches #775's original order (`42fe6eed`).
9. **RESOLVED.** Line 164.
10. **RESOLVED, with a NEW PROBLEM (MINOR).** Lines 426-428 now read: "…so the next refresh of a conda environment file would have failed the PR scan and then the push scan of `main`. (…) Meanwhile the old global `conf/conda_environment.*\.ya?ml` path entry skipped EVERY rule in those files."
    - Under the old config that next sentence describes, a conda-YAML refresh could not fail.
    - It fails only once that path entry is removed: the entry's own measurement (lines 422-423) shows 29 conda build-hash findings once the `paths` allowlist goes.
    - The original sentence named the one file the old `paths` allowlist did not cover. My replacement names the files it did cover.
    - "the allowlist" could also be read as the old `paths` allowlist, which line 418 calls "the allowlist".
    - Replace the "Why" text, from "Every conda-env refresh" through "in those files.", with:
      ```
      Every conda-env refresh rewrites the `<package>=<version>=<build>` lines under a new commit, and no commit-scoped entry can name that commit in advance. The old global `conf/conda_environment.*\.ya?ml` path entry kept such a refresh from failing only by skipping EVERY rule in those files; without it, the next refresh of a conda environment file would fail the PR scan and then the push scan of `main`. (`conf/requirements-conda.txt`, which the new allowlist also names, has not been in the tree since before 0.9.0; its four findings are in history only.)
      ```
11. **RESOLVED.** Line 203.
12. **RESOLVED.** Line 215. "The next entry" is #814's at line 217, which states banner 0.1.3.
13. **RESOLVED.** Line 117. Both captures are in `src/tests/fixtures/juniper_data_tabular_generator_schemas.json` at the head.
14. **RESOLVED.** Line 10.
15. Not applied, by choice. The category order doesn't affect correctness.

Other in-body cross-references all resolve. In cascor: "(its entry is below)", "(see Added)", "(see Fixed)" and "(Security, below)". In canopy: "the dash floor (above)", "(Security, below)", "the restart modal's plan below" and "The second Security entry".

**Changed:** no document. I added `tmp/s2/review/scripts/word_diff.py`, plus diff outputs and a re-fetched copy of the record (`r2_*`, `flood4_main_r2.md`) in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/review/`.
