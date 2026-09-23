<!-- markdownlint-disable -->
# Round 3, lane R3-B (Lane A)

**Entry point:** instrument adequacy: its own instrument, then 26 mutations of the census.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T23:28:21Z to 2026-09-23T00:45:47Z, read-only. Agent `agent-ad373550cfa2cb2a4`.

**Paused:** 2026-09-22T23:52:49Z to 2026-09-23T00:31:22Z, stopped by a usage limit and resumed in place.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-3 Lane A (instrument adequacy) in an independent-agent consensus review, run under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml repo). A handoff now tells every successor to use a census script as THE verification command. Round 2 found the previous version (v2) inadequate, and the author rewrote it as v3. Your job is to decide whether v3 is adequate, and to find where it can report clean while stale text exists. Default to FALSE-NEGATIVE when you cannot prove a shape is handled. A report that everything is fine is worth nothing.

READ-ONLY (hard): do not edit, create or delete files in any repo. Do not commit, push, comment, merge, close or approve. The harness isolates this session to the juniper-ml worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl`. Inside it, run only read-only `git diff`, `git show` and `git log`. Use `gh api` for everything else. Use plain commands only: the harness refuses shell loops over variables that call gh or git, and complex one-liners. If a command is refused, put the logic into a Python script under your scratch dir and run it. Copy the scripts into your scratch dir before mutating them, and never mutate the originals. Scratch dir: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r3b/` (create it). **Everything below is FROZEN for this review.**

ARTIFACTS, identical in the worktree and at juniper-ml PR #2020's head `4855bf8c`:
- `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, census v3. v2 is at `50430e02`; `git diff 50430e02 4855bf8c -- util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` shows what changed.
- `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`. It claims that removing each of 15 rules makes `--self-test` fail.
- The round-2 lane that reviewed v2 is archived at `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/round2-laneA-census-adequacy.md`. Read it to see what v3 was meant to fix.
- The census's claims as the handoff states them: Corrections 1 and the verification block of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`.

THE AUTHOR'S POST-MERGE PREDICTION. The command is `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --ref juniper-ml=4855bf8c --ref juniper-canopy=fdb9e2de --ref juniper-cascor=a824829b --ref juniper-cascor-client=daa6c675 --ref juniper-data-client=ee1fb5d7 --ref juniper-deploy=e6091c46`. The other three repos (juniper-cascor-worker, juniper-data, juniper-recurrence) read at `main`. It predicts:
- 54 live pins, one distinct range `>=0.9.0,<0.10.0`;
- exit 1 with exactly one STALE line, `juniper-ml/docs/QUICK_START.md:92`;
- two passing AMBIGUOUS lines: `docs/REFERENCE.md:3023` and `tests/test_ci_tools_drift.py:461`;
- 6 ADJUDICATED.

TASKS:
1. **Run the census.** Run `--self-test`, the mutation check, and the prediction above. Report the outputs verbatim.
2. **Build your own independent instrument.** Do not reuse the census's regexes or code. It must find every current-state description of a `juniper-ci-tools` version (ranges and bare releases, in any prose or table form, in any file type) in the post-merge trees. Get them with `gh api repos/pcalnon/<repo>/tarball/<ref>` into your scratch dir. The nine repos are pcalnon/juniper-ml, juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy and juniper-recurrence. Treat `notes/`, `prompts/`, `reports/`, releases, CHANGELOGs and `util/ad-hoc/` as history. Diff your list against the census's classes, and name every line the census misses or misjudges.
3. **Attack v3's NEW rules with crafted inputs** through `census_text()` or the equivalent entry point:
   - table-cell attribution by column header;
   - paragraph lookback bounded by headings, code fences and comment blocks;
   - transparent tokens (possessives, PR refs, URL and path segments);
   - docstring and comment judging under `tests/`, via tokenize/ast;
   - `0.N.x` mentions;
   - present-tense bare-version install claims;
   - timestamped lock snapshots classed HISTORICAL;
   - EXCEPTIONS and ADJUDICATED keyed by (repo, path, substring, spec);
   - `--expect` validation and the latest-release lag guard;
   - the exit-2 wrapper;
   - the new passing-AMBIGUOUS listing.

   Look especially for silent drops (not even AMBIGUOUS), and for a stale range that an ADJUDICATED or EXCEPTION key could swallow.
4. **Is the self-test adequate?** Write at least 5 mutations of your own that are NOT among the 15 the harness uses. Report which survive. A surviving mutation of verdict-producing code is MAJOR.
5. **Review every ADJUDICATED and EXCEPTION entry.** For each: is the verdict right, and is the key tight enough that new drift on that line would still be caught?
6. **Check the handoff's statements about the census** in Corrections 1 and the verification block against what it actually does.

OUTPUT. Only your final message is returned. Give numbered findings. Each has: the claim tested, a verdict (CONFIRMED / FALSE-NEGATIVE / FALSE-POSITIVE / BUG / OK), a severity (CRITICAL / MAJOR / MINOR), the evidence (the crafted input or file:line, with output), and a minimal fix. Include your independent list and its diff against the census. End with **Overall verdict** (ADEQUATE / ADEQUATE WITH FIXES / INADEQUATE) and a **Changed:** line.

## Message sent mid-run

The coordinator sent a message while you were working:
A usage limit stopped you mid-review; you had just started the attack harness. Continue from where you stopped, and deliver the FINAL REPORT exactly as your brief specifies: numbered findings, your independent list and its diff against the census, the overall verdict and the Changed: line. Everything under review is still frozen: juniper-ml#2020 head 4855bf8c, and the same sibling PR heads as in your brief. It is now 2026-09-23 00:30 UTC.

Address this before completing your current task.

## Final report

# Round 3, Lane A: is census v3 adequate as a verification instrument?

**Frozen check.** I compared both reviewed files in the worktree against juniper-ml#2020 head `4855bf8c` (still open), before and after the lane. Both are byte-identical:
- `2026-09-22_ci_tools_pin_census_remote.py`, sha256 `49d04b01…`
- `2026-09-22_ci_tools_pin_census_mutation_check.py`, sha256 `bea6c3e0…`

## Task 1: the three runs

**`--self-test`.** All 81 case lines read `ok`. The last line is `self-test: 81 passed, 0 failed`, exit 0.

**Mutation check, verbatim:**
```
  killed    DOC/COMMENT verdict removed
  killed    LIVE verdict removed
  killed    latest-lag guard neutered
  killed    table-column attribution removed
  killed    exceptions keyed without the specifier
  killed    tests/ docstrings treated as fixture
  killed    PR/URL tokens not transparent
  killed    snapshot locks not historical
  killed    markdown fences/headings do not bound lookback
  killed    variable pins treated as unresolved
  killed    arithmetic read as a specifier
  killed    bare 'ci-tools 0.8.0' mentions ignored
  killed    heading naming another package drops the range
  killed    comment block inherits a code line's name
  killed    unresolved installs ignore continuations
15 of 15 mutations killed          (exit 0)
```

**The prediction command, verbatim:**
```
juniper-ml               4855bf8c57ae42d97c33e303112fc8725d7f66b7  mentions=274  live=13
juniper-canopy           fdb9e2de32adf61aacf664fbe78153eb49d73048  mentions=17  live=6
juniper-cascor           a824829bfaf8f0d1c9f959dc539edf30b66a2b6f  mentions=17  live=6
juniper-cascor-client    daa6c67558353a6941096f1b273e87264177c64b  mentions=11  live=5
juniper-cascor-worker    38f39cb8f0654d9954db565fa449bc3a2dbf0f9f  mentions=20  live=5
juniper-data             6c81cc4ca9a6aaa59d460f4eb54c6d0195e65407  mentions=16  live=5
juniper-data-client      ee1fb5d71b59d709c288badaf889667154b63eb3  mentions=14  live=5
juniper-deploy           e6091c468187fcbfabcf235a702ad8f3a2c766cf  mentions=9  live=3
juniper-recurrence       749e7a359e232c2a1d65338518a4fdb9db31ed11  mentions=13  live=6

latest published juniper-ci-tools: 0.9.0
mentions by class: {'ADJUDICATED': 6, 'AMBIGUOUS': 2, 'COMMENT': 19, 'DECLARATION': 1, 'DOC': 20, 'EXCEPTION': 6, 'FIXTURE': 21, 'HISTORICAL': 204, 'LIVE': 54, 'LOCK': 1, 'REQUIREMENT': 57}
live pins: 54  by repo: {'juniper-ml': 13, 'juniper-canopy': 6, 'juniper-cascor': 6, 'juniper-cascor-client': 5, 'juniper-cascor-worker': 5, 'juniper-data': 5, 'juniper-data-client': 5, 'juniper-deploy': 3, 'juniper-recurrence': 6}
distinct live ranges: {'<0.10.0,>=0.9.0': 54}

--- STALE (fails the census) against >=0.9.0,<0.10.0 ---
  juniper-ml/docs/QUICK_START.md:92  ==0.4.*  [DOC]

--- AMBIGUOUS, matching >=0.9.0,<0.10.0: passes, but the owner is unproven -- read each ---
  juniper-ml/docs/REFERENCE.md:3023  <0.10.0,>=0.9.0
  juniper-ml/tests/test_ci_tools_drift.py:461  <0.10.0,>=0.9.0

(6 adjudicated ranges not listed; see ADJUDICATED in this script for each verdict)
EXIT=1
```

At current `main`, with no `--ref`, it exits 1 with 23 STALE lines, 54 live pins and 140 HISTORICAL mentions.

## Findings

**1. The post-merge prediction holds — CONFIRMED (severity n/a).**
- **Claim tested:** the author's four predictions, and that PR heads stand in for the merge result.
- **Evidence:** the output above matches all four predictions.
  - `main` has moved past three of the PR heads: juniper-ml by 7 commits, canopy by 1 and cascor by 1.
  - The only ci-tools text those commits touch is `notes/releases/RELEASE_NOTES_juniper-cascor-worker_v0.6.1.md`, which is HISTORICAL. The merged trees therefore census identically to the PR heads.
  - The script's own `census_members()` over my extracted tarballs reproduces 391 hits, the same classes and the same one STALE line.
- **Fix:** none.

**2. The self-test does not discriminate — BUG in the adequacy evidence, MAJOR.**
- **Claim tested:** the handoff's "15 of 15 code mutations fail that self-test" and "The self-test discriminates" (validation record of `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`).
- **The 15 are real.** Each dies on a genuine FAIL line, not a crash.
- **Evidence:** I wrote 26 mutations of my own, none among the 15. 21 survive at 81/81, and several change real verdicts:

| my mutation | real effect |
|---|---|
| M5: OWN-EXTRA matches any spec (`spec == extra` becomes `extra is not None`) | post-merge `QUICK_START.md:92` is lost, so the run **exits 0**; at `main`, 23 stale lines become 14 |
| M13: DOC/COMMENT set test weakened to "admits latest" | at `main`, loses `REFERENCE.md:7072` and `test_ci_tools_drift.py:461` |
| M16: `extra` taken from the first spec anywhere in `pyproject.toml` | at `main`, loses `ci.yml:1879` |
| M4: `candidate_set()` without the next patch, minor and major | `>=0.9.0,<0.11.0` and `~=0.9` pass (unmutated, both are STALE) |
| M1: `main()` always returns 0 | STALE lines printed, exit 0 |
| M2: lag line not inserted into `bad` | with latest = 0.10.0: `STALE (none)`, exit 0 |
| M3 / M12: the zero-live guard / the per-repo empty-read guard removed | exit 0 on empty reads |
| M11 / M9: the 1.0 guard / the `--expect` 0.x check removed | M11 exits 1 instead of 2 |
| M7: `util/ad-hoc/` not HISTORICAL | +52 false STALE lines |
| M27 / M28: `prompts/` + `reports/` / CHANGELOG not HISTORICAL | +59 / +12 false STALE lines |
| M15: `LOOKBACK_CHARS` raised to 2000 | +1 false positive, `propose.py:750` |
| M14, M17, M6, M8, M10, M18, M19 | no effect today (M18 removes the new passing-AMBIGUOUS listing) |

  Controls M29, M30, C1, C2 and C3 were killed, so the harness does bite where a case exists.
- **Root causes:**
  - `--self-test` never executes `main()`, so it never checks the exit code, the lag insertion, the run guards or the listing.
  - The verdict cases pass a hand-written `cand` list, so `candidate_set()` is never called.
  - There are no `location_class()` cases for `util/ad-hoc/`, `prompts/`, `reports/` or CHANGELOG.
  - There is no case for OWN-EXTRA classification, and none for ADJUDICATED keying.
  - `round2-laneA-census-adequacy.md` finding 2 named both the `util/ad-hoc` and OWN-EXTRA survivors. Both still survive.
  - The author's "latest-lag guard neutered" mutation mutates the helper the self-test calls directly, so it proves the helper, not its wiring into `main()`.
- **Fix:**
  - Add a `main()`-level self-test with monkeypatched `load_remote` and `published_versions`, asserting exit codes for: stale, clean, latest 0.10.0, zero live pins, one empty repo, and a misspelt `--ref`.
  - Call `candidate_set()` in the verdict cases.
  - Add classification cases for the HISTORICAL segments, OWN-EXTRA and ADJUDICATED keying.
  - Add M1, M2, M4, M5, M7 and M13 to `2026-09-22_ci_tools_pin_census_mutation_check.py`.

**3. A repo name next to the range drops it silently — FALSE-NEGATIVE, MAJOR.**
- **Claim tested:** the docstring of `2026-09-22_ci_tools_pin_census_remote.py` (lines 37–38: "another juniper name … is AMBIGUOUS rather than silently dropped"), and the first limit in the handoff's Corrections 1.
- **Evidence, crafted.** An "other" owner is discarded before the context check runs. Each of these produces `hits=[]`:
  - `The sequence-safety workflows in juniper-cascor pin \`>=0.8.0,<0.9.0\`.`
  - a `tests/` docstring: `juniper-cascor pins \`\`>=0.8.0,<0.9.0\`\` in its sequence-safety workflow today.`
  - a workflow comment `# juniper-ci-tools pins:` followed by `#   juniper-cascor  >=0.8.0,<0.9.0`. `DIRECT_RE`'s "juniper name across spaces" rule reads this as cascor's own range.
  - a list item `- **juniper-cascor**: \`>=0.8.0,<0.9.0\`` under `### juniper-ci-tools pins by repo`.
- **Evidence, real prose.** I fed the text of `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` through `census_text()` as if it were a current `docs/` page. It silently drops:
  - line 186, "Both were in juniper-cascor, … pinned `>=0.6.0,<0.7.0`";
  - line 245, "two live juniper-cascor pins were still `>=0.6.0,<0.7.0`".

  That is the arc's central finding, in the arc's own phrasing.
- **Fix:** only a glued name (no gap) owns a range outright. A repo name (a `REPOS` member), or any "other" owner in a section matching `CONTEXT_WORDS_RE`, should yield AMBIGUOUS, never a drop.

**4. Table attribution — FALSE-NEGATIVE, MAJOR (one v3 regression).**
- **Regression (T2):** the header `| package | pin in juniper-ml |` with the row `| juniper-ci-tools | >=0.8.0,<0.9.0 |` gave DOC and failed in v2. In v3 it gives `[]`, because a header naming a repo returns "other" and overrides the row's own ci-tools cell.
- **Also silent:**
  - `| repo | ci-tools pin |` with the row `| juniper-cascor | >=0.8.0,<0.9.0 |`. The header check is `NAME_RE` only, so the short form is not recognised, and the row then falls to the repo token.
  - a header of `CI tools pin`;
  - a generic-header table under a ci-tools-only heading.
- **Why it matters:** these are the natural shapes for a per-repo fan-out table.
- **Fix:**
  - Header ownership should use `OWNER_NAME_RE` or the context words.
  - A header that names a repo is not an owner.
  - If the header says nothing, the row's cell should win.
  - Unattributed cells in ci-tools context should be AMBIGUOUS.

**5. Context outside the range's own block is invisible — FALSE-NEGATIVE, MAJOR.**
- **Claim tested:** the handoff's limit that a range described only by context "lists … as AMBIGUOUS".
- **The rule is narrower.** That holds only when `ci-tools`, `screen pin` or `sequence-safety` appears in the range's own paragraph or comment block (after the last blank or bare-`#` line), or in its nearest `#`-style heading.
- **Evidence.** Each of these gives `[]`:
  - a workflow comment split by a bare `#` line: `# Install juniper-ci-tools for the screens.` / `#` / `# Pinned >=0.8.0,<0.9.0 so each new minor is adopted deliberately.`
  - the same shape in a `.bash` file;
  - a name paragraph, then a blank line, then the range paragraph;
  - a `util/*.py` docstring with a paragraph break;
  - a loose list-item continuation;
  - a ci-tools heading one level up;
  - a name only inside the preceding code fence;
  - an RST underline heading.
- **Why it matters:** bare-`#` separators are the house style in these workflows (juniper-deploy `ci.yml:240`).
- **Fix:**
  - A bare `#` should continue the comment block for attribution.
  - Section context should include parent headings.
  - Any unattributed 0.x range in a file that names ci-tools should become AMBIGUOUS rather than be dropped.

**6. Bare releases and `0.N.x` are matched in one word order only — FALSE-NEGATIVE, MAJOR.**
- **Claim tested:** the handoff's "It sees a bare release only in a present-tense install claim, such as 'ci-tools 0.8.0 is already installed'".
- **How narrow it is.** `BARE_VERSION_RE` needs the name, then `X.Y.Z` at once, then `is/are [already|now] installed|pinned|in use|required`. It was drawn from the one real instance (canopy `ci.yml:270`).
- **Silent bare-release claims:**
  - `CI installs juniper-ci-tools 0.8.0.`
  - `# The preflight step installs ci-tools 0.8.0 already.`
  - `… 0.8.0 is currently installed.`
  - ``ci-tools `0.8.0` is installed.``
  - `CI is pinned to juniper-ci-tools 0.8.0.`
  - `… version 0.8.0 is installed.`
  - `The installed juniper-ci-tools is 0.8.0.`
  - the `v0.8.0` form, the `0.8` form, a parenthetical, and two packages in one sentence.
- **`XMENTION_RE` has the same shape.** It sees only `juniper-ci-tools` followed by spaces and `0.N.x`. Silent: `ci-tools 0.8.x`, `juniper-ci-tools: 0.8.x`, `(0.8.x)`, `v0.8.x`, `0.8.*`, a table row `| juniper-ci-tools | 0.8.x |`, a backticked version, a line break.
- **False positive:** `juniper-ci-tools 0.8.0 is required for --scope.` is a correct floor statement, but it is judged `==0.8.0` and fails. This is fail-safe.
- **Fix:** detect the name within a few tokens of a bare `0.x.y`, `0.N.x` or `0.N.*`, in either order, including table cells and backticks. Use the install verb only to exempt history, not to detect.

**7. Live-install blind spots — FALSE-NEGATIVE, MAJOR (two v3 regressions).**
- **Regression (W1):** `CI_TOOLS_VERSION: "0.8.0"` plus `pip install "juniper-ci-tools==${CI_TOOLS_VERSION}"` was UNRESOLVED in v2. In v3 it gives `[]`.
  - `VARIABLE_PIN_RE` exempts every `==${…}` pin.
  - It was added for `publish-ci-tools.yml:152`, which is the only real instance.
- **Regression (W3):** `pip install juniper-ci-tools "juniper-doc-tools>=0.1.0,<0.2.0"` was UNRESOLVED in v2. In v3 it gives `[]`.
  - Any 0.x spec anywhere on the logical line skips the unresolved check.
  - Multi-package install lines are common (canopy `ci.yml:733`).
- **Silent, never checked:** unpinned installs in a Dockerfile, a Makefile or `.pre-commit-config.yaml`. The unresolved check runs only on workflows. There is no real instance today.
- **Fix:**
  - Exempt variable pins only in `publish-*.yml` verify loops.
  - Run the unresolved check per name occurrence, not per line.
  - Extend it to Dockerfile, Makefile and pre-commit configs.

**8. The handoff's statements about the census — mixed; MAJOR for the limits (task 6).**
Statements are from `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`.
- **Confirmed:**
  - "81 passed, 0 failed" and "15 of 15 mutations killed";
  - "live pins: 54, one distinct range";
  - "exits 1 and names each stale line" (23 lines at `main`);
  - "22 of the census's 23 current-state lines";
  - after the merges, "exactly one STALE line, docs/QUICK_START.md:92";
  - two passing AMBIGUOUS lines, both describing the ci-tools screen pins (I read both);
  - "54 = 13 + 39 + 2".
- **Overstated:**
  - "judges versions as sets": LIVE is compared textually and LOCK by membership.
  - "The self-test discriminates": see finding 2.
  - "lists such a range as AMBIGUOUS": false for the shapes in findings 3–5.
  - "sees a bare release only in a present-tense install claim": false for the forms in finding 6.
- **Missing from "Its limits":**
  - the floor-only exemption (finding 12);
  - unresolved installs are checked in workflows only (finding 7);
  - one repo with zero live pins exits 0 (finding 9);
  - `--ref` keys are unvalidated (finding 10);
  - string literals under `tests/` are never judged (finding 13).
- **Why it is MAJOR:** the handoff's disclaimer "cannot support … outside the forms the census reads" depends on those forms being described correctly.
- **Fix:** rewrite "Its limits" from findings 3–13.

**9. One repo with zero live pins exits 0 — BUG, MINOR.**
- **Background:** this is `round2-laneA-census-adequacy.md` finding 10, only half applied.
- **Evidence:** in an offline `main()` run, with juniper-deploy's read reduced to a README, or with its `.github/` removed:
  - the run prints `WARNING: no live pins` and `live pins: 51`;
  - STALE is `(none)`, and the exit code is 0.
- **Fix:** exit 2 when any repo yields 0 live pins, or accept `--expect-live 54`.

**10. `--ref` / `--local` keys are not validated — BUG, MINOR.**
- **Evidence:** `--ref juniper-cascr=a824829b --local juniper-deplyo=/nonexistent` reads `juniper-cascor@main` and `juniper-deploy@main` without a word.
- **Risk:** the prediction command carries six hand-typed refs. A typo when checking a drifting PR head censuses a clean `main` instead.
- **Fix:** exit 2 on any key not in `REPOS`.

**11. Set equality over a sample — FALSE-NEGATIVE, MINOR.**
- **Evidence:**
  - `CI pins juniper-ci-tools>=0.9.0,<0.9.2` passes. The candidate set lacks 0.9.2, so the sample cannot tell `<0.9.2` from `<0.10.0`. v2 failed it.
  - `juniper-ci-tools<1.0,>=0.8.0` is truncated to `>=0.8.0`, classed REQUIREMENT, and passes. The reverse clause order is judged.
- **Fix:**
  - Compare normalised bounds, not a sample.
  - Let `SPEC_RE` start at any clause.

**12. Prose floors are exempt — FALSE-NEGATIVE by design, MINOR.**
- **The mismatch:** the handoff's Corrections 1 replaces a check that wanted "no stale floor anywhere". The census judges prose floor-only specs only against the latest release, and it drops unattributed ones silently.
- **Real post-merge lines that pass:**
  - juniper-ml `.github/workflows/main-verify.yml:72`, `(PyPI >=0.8.0)`. This is the literal sibling of cascor `main-verify.yml:64` and deploy `main-verify.yml:69`, which cascor#673 and deploy#228 fixed.
  - juniper-ml `docs/REFERENCE.md:3758` and `:4018`, "installs `juniper-ci-tools` (>=0.8.0)".
  - data-client `main-verify.yml:127` and `sequence-safety.yml:126`, "the >=0.8.0 floor". These are dropped outright, not even classed REQUIREMENT.
- **Why it matters:** the handoff's own Corrections 6 says a floor below CI's leaves a pre-populated environment (JuniperCascor1 holds 0.8.0) on the old release.
- **Fix:** state the exemption in the handoff, or list present-tense descriptions whose floor differs from `--expect` as AMBIGUOUS.

**13. String literals and non-`.py` files under `tests/` — FALSE-NEGATIVE, MINOR.**
- **Evidence:** each of these is classed FIXTURE and passes:
  - an assertion message carrying a stale operator hint;
  - a module-level runbook string;
  - a `tests/*.bash` script, comments included;
  - `tests/requirements.txt` with `==0.6.0` (never LOCK);
  - an unparseable test file.
- **Real instances:** none today.
- **Fix:** classify non-`.py` files under `tests/` by their own type, and list `pip install` ranges inside string literals as AMBIGUOUS.

**14. HISTORICAL by path — OK, MINOR notes.**
- **Where the rule reaches:**
  - `SNAPSHOT_RE` applies to any basename: a timestamped workflow becomes HISTORICAL, where v2 classed it LIVE.
  - `history/` anywhere is HISTORICAL; `juniper-canopy/docs/history` is the only such directory.
- **The snapshots are not frozen.** Dependabot rewrote `conf/requirements_ci_2026-05-25_09-31-00.txt` on 2026-09-14 (#1933), and all 18 snapshots read `==0.9.0`.
- **The verdict still holds:** the snapshots are uploaded as artifacts (`ci.yml:1899-1900`) and are not install inputs.
- **Fix:** anchor `SNAPSHOT_RE` to `conf/requirements_ci_*` and `conf/conda_environment_ci_*`.

**15. EXCEPTIONS and ADJUDICATED review — OK.** All 12 verdicts are right, and each key matches exactly one hit.

| entry | verdict |
|---|---|
| deploy `ci.yml:242` and `:243` | dated "Pin healed 2026-08-08" history |
| `REFERENCE.md:3022` | dated "Scope history (2026-09-11)" |
| `propose.py:750` | service-core's range, not ci-tools |
| `propose.py:1093`, both specs | incident narrative |
| `propose.py:747` | example |
| `pyproject.toml:54`, `test_pyproject_extras.py:39` | the #293/#295 history |
| `test_ci_tools_drift.py:52`, `test_coverage_gap_mapper_drift.py:88` | pattern examples |
| cascor `test_sequence_safety_retired.py:18` | example |

- **Residual risks:**
  - The key unit is a physical line, and `REFERENCE.md:3022` is one line of about 1,000 characters. Appending a current-state sentence with the same range there would be swallowed.
  - The spec and substring components of the ADJUDICATED keys are not pinned by any test (M14, M17).
  - `propose.py:747` says the CI-pin description "lives ELSEWHERE in AGENTS.md". It no longer does, which is harmless.

**16. Exit-2 wrapper, `--expect` validation, lag guard and the new listing — OK.**
- **Exit 2 (verified):** each of these exits 2 before any verdict:
  - `--expect garbage`, `--expect '>=1.0,<2.0'` and `--expect ''`;
  - a fake `gh` that exits 1;
  - a non-gzip tarball;
  - `--ref` without `=`;
  - latest = 1.0.0.
- **Lag guard:** with latest = 0.10.0, the run exits 1 with the lag line.
- **Passing-AMBIGUOUS listing:** it works.
- **Caveat:** the lag wiring and the listing are untested (finding 2).

## My independent list, and its diff against the census

**How I built it.** It uses my own regexes and none of the census's code.
- One pass matches any spelling of the name plus all 8 console scripts (checked against `juniper-ci-tools/pyproject.toml`), with any 0.x token (`0.N.x`, `0.N.*`, `v`-prefixed) within 12 lines before or 3 lines after.
- A second, window-free pass reads every 0.x token in every current-state file that names ci-tools.
- A table scan reads every markdown table whose header names ci-tools.
- It covers every file type in the 9 tarballs at the frozen refs; no binary file mentions ci-tools.
- **Size:** 332 files mention ci-tools, 156 of them current-state. That gave 725 windowed candidates and 859 window-free lines. I joined all of them to the census's per-line classes and read them by hand.

**What it finds post-merge** (all agree with the census):

| current-state ci-tools version text | census class |
|---|---|
| 54 live pins, all `>=0.9.0,<0.10.0` | LIVE 54 |
| 38 prose and comment ranges, all `>=0.9.0,<0.10.0`, in 31 files | DOC 19 + COMMENT 19 |
| `juniper-ml/docs/QUICK_START.md:92`, `juniper-ci-tools 0.4.x` (**stale**) | DOC, STALE |
| `REFERENCE.md:3023` and `test_ci_tools_drift.py:461`; both genuinely ci-tools, both correct | AMBIGUOUS, listed as passing |
| `pyproject.toml:89` `>=0.1.0`, and its mirrors in README:41, AGENTS:257, QUICK_START:61, REFERENCE:112/173–175, DOCUMENTATION_OVERVIEW:219 | DECLARATION / REQUIREMENT |
| `conf/requirements_ci.txt:45` `==0.9.0`; 18 snapshots `==0.9.0` | LOCK / HISTORICAL |
| 12 history lines inside current files | 6 EXCEPTION / 6 ADJUDICATED |
| 21 test-data ranges | FIXTURE |
| bare-release claims: 0 (canopy `ci.yml:270` was fixed by canopy#655) | none |

- **Skipped files:** the files the census does not read, by suffix or by its pre-filter, hold no current version text.
- **Diff:** under the census's own rules, it misses 0 lines and misjudges 0 lines. The only disagreement is the 5 floor-only lines in finding 12, which is a scope question.

## Overall verdict: ADEQUATE WITH FIXES

On the frozen corpus it is right. The prediction reproduces exactly, and an independent instrument finds nothing it misses.

It is not yet safe as *the* verification command:
- A successor's exit 0 would only mean "none of the shapes it happens to parse". Silent drops remain in natural shapes, three of them regressions from v2 (findings 3–7).
- The self-test cannot protect the exit code or four verdict rules. One of those mutations (M5) turns the post-merge run into exit 0 (finding 2).
- The handoff misdescribes both of those facts (finding 8).

Findings 2, 3 and 7, and the handoff rewording in finding 8, should land before a successor relies on it.

**Changed:** nothing in any repo or in the worktree. The two reviewed files are unchanged; the sha256 values match before and after the lane. Everything I built is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r3b/`:
- **Instrument:** `indep_instrument.py`, `indep_pass2.py`, `census_harness.py`, `join.py`, `skipped_files.py`, `other_decisions.py`, `corpus_checks.py`, `prose_demo.py`.
- **Attacks:** `attack.py`, `attack_v2.py`.
- **Mutations:** `mut_mine.py`, `mut_mine2.py`, `mut_effect.py`, `mut_effect2.py`, and the `mutants/` directory.
- **Exit-code checks:** `run_main.py`, `run_main_all.py`, `wrapper_checks.py`, `ref_typo.py`, `fakebin_fail/gh`, `fakebin_junk/gh`.
- **Fetching and comparison:** `resolve_refs.py`, `compare_heads.py`, `main_ahead.py`, `main_ahead2.py`, `fetch_trees.py`, `fetch_main_trees.py`.
- **Downloaded copies and extracted trees:** `census_v3_pr.py`, `census_v2.py`, `mutation_check_pr.py`, the `trees/` and `trees_main/` directories.
- **Run outputs:** `prediction_run.txt`, `main_run.txt`, `review_all.txt`, `pass2.txt`, `dropped.txt`, and the `*.json` files.
