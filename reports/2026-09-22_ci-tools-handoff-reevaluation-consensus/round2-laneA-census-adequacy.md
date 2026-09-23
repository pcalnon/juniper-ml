<!-- markdownlint-disable -->
# Round 2, lane R2-B (Lane A)

**Entry point:** instrument adequacy: its own instrument, then mutations of the census.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T20:41:46Z to 2026-09-22T21:09:05Z, read-only. Agent `agent-a2e258a1c14e72162`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-2 Lane A (instrument adequacy) in an independent-agent consensus review. The artifact is a census script that a handoff now tells every successor to use as THE verification command: `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, in the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl (identical to juniper-ml PR #2020's branch head 50430e02; FROZEN for this review). Round 1 showed its first version was blind to prose-form ranges (a range separated from the package name, sometimes on the next line), missed `.lock`/Makefile/Dockerfile, exempted whole files, and crashed with exit 1 on errors. Version 2 claims to fix all of that and ships a `--self-test`. Your brief: **prove v2 can report clean while stale drift exists, or report stale where none exists.** "UNTRACEABLE" is allowed. A finding that it is fine is worth nothing unless you tried hard to break it.

READ-ONLY (hard): do not edit/create/delete files in any repo or the worktree (copy the script into your scratch dir to experiment); do not commit, push, comment, merge or approve anything. Worktree-isolated harness: no `git` against other repos; use `gh api` (tarballs: `gh api repos/pcalnon/<repo>/tarball/main > f.tgz`). Plain commands only; put logic in python files. Scratch: /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r2b/ .

DO:
1. Run `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test` and the live run (it downloads 9 repo tarballs via `gh api`; takes a few minutes). Record the output. The author expects: exit 1; 54 LIVE pins, one range `<0.10.0,>=0.9.0`; a STALE list of 18 lines across juniper-ml, canopy, cascor, cascor-client, data-client, deploy (all fixed only in OPEN PRs, not yet on main); an AMBIGUOUS list of 10.
2. Build YOUR OWN independent instrument (do not reuse the author's regexes) that finds every current-state description of a juniper-ci-tools version RANGE (with an upper bound) at each of the 9 repos' remote main (pcalnon/juniper-ml, juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy, juniper-recurrence), including prose forms, and compare against v2's STALE + AMBIGUOUS lists. Report anything v2 misses (false negative) and anything it flags that is not stale (false positive). Treat notes/, prompts/, reports/, releases/, CHANGELOG, util/ad-hoc/ as historical (not current-state).
3. Simulate the post-merge world: apply the diffs of the open PRs (juniper-ml#2020, juniper-canopy#655, juniper-cascor#673, juniper-cascor-client#170, juniper-data-client#210, juniper-deploy#228 — `gh pr diff N --repo pcalnon/<repo>`) to extracted tarballs in your scratch dir and run v2's `census_text` logic (import the module from your scratch copy) over those trees. The author claims it then exits 0. Does it? Is anything stale left that it does not report?
4. Attack the design: crafted lines through `census_text()` — e.g. a range BEFORE the name (`>=0.8.0,<0.9.0 of juniper-ci-tools`), a range in a markdown table whose column header names juniper-ci-tools, `juniper-ci-tools` followed by another package with no specifier and then a range, a range 2 paragraphs away, a YAML block scalar `run: |` line containing `# ...` inside a quoted string, `pip install -r requirements-ci.txt` where that file pins ci-tools, an `.in` file with a stale cap, `~=0.8.0`, `==0.8.*`, `!=0.9.0`. Also check: the EXCEPTIONS keying (can an exception suppress a different stale line?), the exit-2 wrapper (simulate a gh failure by putting a fake `gh` first on PATH that exits 1, and a corrupted tarball), `has_upper_bound` semantics, the `0.x` restriction (what happens at 1.0.0?), and whether `--expect` with an invalid spec exits 2.
5. Is `--self-test` itself adequate — does each case discriminate (would it fail if the corresponding logic were removed)? Pick 3 cases and mutate the script in your scratch copy to prove they bite.

OUTPUT (final message only is returned): numbered findings — claim tested, verdict (CONFIRMED / FALSE-NEGATIVE / FALSE-POSITIVE / BUG / OK), severity (CRITICAL/MAJOR/MINOR), evidence (the crafted input or file:line + output), minimal fix. Include the live-run summary lines and your independent instrument's list. Overall verdict: ADEQUATE / ADEQUATE WITH FIXES / INADEQUATE. Terse, no preamble.

## Final report

**Overall verdict: ADEQUATE WITH FIXES.** Today's job works: it exits 1 on remote main with the correct 18 stale lines and exits 0 once the six PRs merge. But it can report clean while stale drift exists (findings 1, 3–6), and its `--self-test` doesn't cover the verdict code that produces every stale line it reports (finding 2). Fix 1 and 2 before a successor treats it as THE verification command. Failing that, the handoff (`HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`) has to say that exit 0 means "every judged line equals `--expect`". It does not mean "no stale range exists", and it does not mean "the pins admit the latest release".

**Changed:** nothing in any repo or the worktree. The script is byte-identical to PR #2020's head 50430e02 (sha256 e7ffe451…). Everything I built is in `…/scratchpad/lanes/r2b/`.

## Live run: matches your prediction exactly
- `--self-test`: 31 passed, 0 failed.
- Commits measured: ml d0582a21 (199 mentions), canopy 9bffaba1 (16), cascor 05c13d55 (17), cascor-client 0366f4f1 (11), worker 48a523e6 (20), data 6c81cc4c (16), data-client f7494ff1 (16), deploy 13ee87aa (9), recurrence 749e7a35 (13).
- Latest published is 0.9.0. Classes: AMBIGUOUS 10, COMMENT 16, DECLARATION 1, DOC 19, EXCEPTION 2, FIXTURE 32, HISTORICAL 113, LIVE 54, LOCK 19, REQUIREMENT 51.
- 54 live pins, one range `<0.10.0,>=0.9.0`. STALE list has 18 lines, AMBIGUOUS has 10, exit 1.
- Running the script's own logic over my local copies of the trees reproduces this exactly.

## My independent list (my own regexes, all file types, every upper-bounded range read by hand; notes/, prompts/, reports/, releases/, CHANGELOG and util/ad-hoc/ treated as history)
I count 21 current stale ci-tools ranges at main; v2 lists 18 of them as stale.
- **Listed as STALE by v2 (18):**
  - ml `ci.yml:1879`, `docs/REFERENCE.md:3754`, `:6392`, `:7072`, `predict_merge.py:57/180/234`
  - canopy `sequence-safety.yml:27`, `AGENTS.md:517`
  - cascor `main-verify:64`, `sequence-safety:60`
  - cascor-client `main-verify:28`, `sequence-safety:28`, `docs/REFERENCE.md:715`
  - data-client `main-verify:28`, `sequence-safety:28`
  - deploy `main-verify:69`, `sequence-safety:72`
- **Only listed as AMBIGUOUS, never failed:** ml `docs/REFERENCE.md:3023`.
- **Missed entirely:**
  - ml `tests/test_coverage_gap_mapper_drift.py:53` (classed FIXTURE).
  - ml `docs/QUICK_START.md:92`, `juniper-ci-tools 0.4.x` (not seen at all).
- **Judgement calls:** deploy `ci.yml:243` is a dated "Pin healed 2026-08-08" note (AMBIGUOUS). data-client `main-verify.yml:127` and `sequence-safety.yml:126` say "the >=0.8.0 floor is…" directly above a `>=0.9.0` pin; floor-only statements are outside the script's declared scope.
- **Other checks:**
  - My live-pin count is also 54.
  - The files v2 skips (by suffix, or because they never name the package) hold no ci-tools range.
  - All 54 live pins and the remaining DOC/COMMENT lines equal `--expect`.

## Findings
1. **FALSE-NEGATIVE, MAJOR — `--expect` is never checked against the latest release.** I patched `latest_published()` to return 0.10.0 and ran the real `main()` over the post-merge trees. It printed "latest published juniper-ci-tools: 0.10.0" and "(one entry, equal to --expect, is clean)", found no stale lines, and returned 0. All 54 live pins exclude 0.10.0; this is the 2026-07-06 incident class. *Fix:* fail when `Version(latest) not in SpecifierSet(expect)`.
2. **Self-test inadequate, MAJOR.** I mutated my copy of the script 16 ways.
   - **M4** deletes the DOC/COMMENT verdict branch: the self-test still passes 31/31, but the real census drops from 18 stale to 0 and exits 0.
   - **Also survive:** the LIVE verdict, the UNRESOLVED verdict, EXCEPTIONS, util/ad-hoc-is-HISTORICAL (removing it adds 14 stale lines), DECLARATION-always-fails (there is no "declaration admits latest" case), OWN-EXTRA, `normalise`, and the AMBIGUOUS window.
   - **Non-discriminating cases:** the "commented-out list item" case passes with the `- #` branch deleted, because the general ` #` rule already covers it. The locally-built-wheel case never exercises its `/` branch.
   - **Proven to bite (5):** paragraph break, possessive/PR ref, trailing comment, notes/ path segment, non-juniper package's range.
   - *Fix:* add verdict-level cases for LIVE mismatch, DOC/COMMENT mismatch, UNRESOLVED, declaration-admits, EXCEPTION, OWN-EXTRA, util/ad-hoc, and latest-vs-expect.
3. **FALSE-NEGATIVE, MAJOR, real corpus — everything under tests/ is exempt.** `test_coverage_gap_mapper_drift.py:53` is an operator runbook line (`pip install "juniper-ci-tools>=0.6.0,<0.7.0"`). The script classed it FIXTURE; #2020 fixed it by hand. My crafted `tests/README.md` case behaves the same. *Fix:* list upper-bounded ranges under tests/ as AMBIGUOUS, or judge comments and docstrings there.
4. **FALSE-NEGATIVE, MAJOR, design — any juniper-* token between the name and the range silently drops it (not even AMBIGUOUS).** No real instance today. All of these crafted lines produce zero hits:
   - a markdown PR link `[#869](https://github.com/pcalnon/juniper-ml/pull/869)`
   - a curly-apostrophe possessive `juniper-ml’s`
   - `juniper-ml PR #1909`
   - a repo path `juniper-cascor/.github/…`
   - a repo name before the range, or rows that name repos under a ci-tools column header
   - the release tag `juniper-ci-tools-v0.8.0`
   - a second juniper package in between

   26 current-state lines already have ci-tools followed by a juniper link, ref or path on the same line. *Fix:* when the fallback returns "other" and the paragraph names ci-tools, emit AMBIGUOUS. Treat URL/path tokens, `’s` and `PR #` as transparent.
5. **FALSE-NEGATIVE, MAJOR — paragraph breaks and wide tables.**
   - `### juniper-ci-tools` + blank line + `The CI pin is >=0.8.0,<0.9.0` gives no hit.
   - In a table shaped like `docs/REFERENCE.md`'s compatibility table, rows 1–2 of the ci-tools column come out AMBIGUOUS and a stale row 3 is dropped.
   - The real table shows the same effect: lines 173 and 174 are AMBIGUOUS, while 175 has identical content and is unlisted.
   - *Fix:* attribute table cells by their column header; widen the context to the enclosing section.
6. **FALSE-NEGATIVE, MINOR — post-merge exit 0 CONFIRMED, but one stale line remains.** Over the six patched trees: 0 stale, 10 AMBIGUOUS, exit 0. `QUICK_START.md:92` (`0.4.x`) is untouched by every PR and invisible to the script. *Fix:* match `0\.\d+\.x` next to the name.
7. **FALSE-NEGATIVE, MINOR — unpinned live installs.** `pip3 install`, `uv tool install`, `pipx`/`uvx`, and a `pip install \` continuation line are not flagged UNRESOLVED. *Fix:* widen the installer match and join backslash continuations.
8. **FALSE-NEGATIVE, MINOR — misclassified or dropped specifier forms.**
   - A doc saying `>=0.8.0,!=0.9.0` (excludes latest) is counted as REQUIREMENT.
   - `>=0.8.0,<1.0` is truncated to `>=0.8.0` and counted as REQUIREMENT.
   - The short form `ci-tools>=0.8.0,<0.9.0` is attributed to "other".
   - *Fix:* also judge DOC lines with `latest in SpecifierSet(spec)`.
9. **FALSE-NEGATIVE, MINOR — exceptions ignore the version.** They are keyed by a substring of the line, so new drift appended to the `pyproject.toml:54` line is suppressed. Any `propose.py` line containing "minimum-pin note, and a" is suppressed too. *Fix:* include the exact version range in the key.
10. **BUG, MINOR — the exit-2 wrapper.**
    - **Correct:** a fake `gh` that exits 1, a non-gzip body, a truncated gzip, and a PyPI TLS timeout all exit 2.
    - **Wrong:** an empty but valid tarball gives mentions=0 for all nine repos, live pins 0, the "is clean" line, and exit 0.
    - *Fix:* exit 2 when any repo yields 0 live pins.
11. **BUG, MINOR — `--expect garbage`.** It exits 2 only because juniper-ml's LOCK hits happen to reach `SpecifierSet()`, after all nine downloads. With no LOCK hit in play it exits 1 and reports every live pin stale. *Fix:* validate `--expect` before any network call.
12. **MINOR — at 1.0 (known limitation, no guard).** Every pip-install pin, correct or not, becomes UNRESOLVED; hoisted `CI_TOOLS_PIN:` pins and all docs become invisible. *Fix:* exit 2 if latest or `--expect` is not 0.x.
13. **FALSE-POSITIVE, MINOR, latent.** The 18 dated `conf/requirements_ci_<timestamp>.txt` snapshots are classed LOCK. After the next minor all 19 LOCK lines fail, and 18 of them are frozen records that can never be fixed. *Fix:* classify timestamped snapshots as HISTORICAL.
14. **FALSE-POSITIVE, MINOR — string comparison, all fail-safe.** These are all flagged stale:
    - Forms that mean the same as `--expect`: `~=0.9.0`, `==0.9.*`, `>=0.9,<0.10`.
    - A doc naming exactly the latest release, `==0.9.0`.
    - A correct cap mentioned on its own (`<0.10.0`).
    - A range belonging to uv written after the ci-tools name.
    - A trailing comment preceded by an unbalanced apostrophe, which gets read as live.
15. **MINOR — AMBIGUOUS list is noisy and has no memory.** At main, 5 of the 10 aren't ci-tools at all: the three rows of the doc-tools column and `propose.py:750` (service-core). Most of the rest are dated history. Post-merge, line 3023 is still listed although it now equals `--expect`. *Fix:* keep an allow-list of adjudicated entries and print only new ones.
16. **OK.**
    - All 18 stale lines are genuine ci-tools ranges that differ from `--expect`. Line 7072's `>=0.8.0,<0.10.0` admits 0.9.0, so it is stale only under the script's equality rule.
    - A `#` inside quotes on a `run: |` line is handled correctly.
    - A stale cap in a `.in` file, `.in` with `!=`, `~=0.8.0`, `==0.8.*`, a requirements-file range, a range in a code-fence comment, and console-script or import-path attribution are all correctly flagged.
