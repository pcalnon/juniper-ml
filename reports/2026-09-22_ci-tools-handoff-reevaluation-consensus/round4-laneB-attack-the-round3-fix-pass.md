<!-- markdownlint-disable -->
# Round 4, lane R4-A (Lane B)

**Entry point:** adversarial: attack the round-3 fix pass, plus a ledger of every round-3 finding.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`, `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` and `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` and the PRs named in the brief.

**Ran:** 2026-09-23T01:01:55Z to 2026-09-23T01:42:44Z, read-only. Agent `agent-a9312208b5c44d2c7`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-4 Lane B (analysis review) in an independent-agent consensus review, run under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml repo). Rounds 1–3 found defects, and after round 3 the author made a third fix pass. Your brief: **the fix pass is the least trustworthy part of any document. Find what the round-3 corrections broke, over-claimed, got wrong, or silently dropped.** Default to REFUTED when you cannot verify a new claim against a primary source. A report that everything is fine is worth nothing. **Keep to the diff.** Earlier rounds reviewed everything else; re-open unchanged text only when a change depends on it.

READ-ONLY (hard): do not edit, create or delete files in any repo. Do not commit, push, comment, merge, close, approve, or approve deployments. The harness isolates this session to the juniper-ml worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl`. Inside it, run only read-only `git diff`, `git show` and `git log`; the objects are fetched. Do not run `git fetch`. Use `gh api` or GraphQL for everything else. Use plain commands only: the harness refuses shell loops over variables that call gh or git, `$(...)` feeding a command, and complex one-liners. If a command is refused, put the logic into a Python script under your scratch dir. Copy scripts into your scratch dir before running mutated versions. Scratch dir: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r4a/` (create it). **Everything below is FROZEN for this review.**

THE FIX PASS UNDER REVIEW is juniper-ml PR #2020 commit `f68380dd` (head), against the round-3 head `4855bf8c`. Get it with `git diff 4855bf8c f68380dd`. It touches:
1. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`, the status banner. Changed areas:
   - the "What has moved" blockquote, including the worker `v0.6.1` facts;
   - note b's image and pin-drift lines;
   - note c;
   - note d's list of later documents;
   - note f, the X7 flake: five runs, the mechanism paragraph, and ownership;
   - note g, the worktrees (30 plus 2);
   - Corrections 1's census bullets and Corrections 2;
   - the remaining-work lists: the owner-gated, startable, claimed-repin and authored items;
   - the verification block;
   - the rewritten `### Validation record for this banner` (sizing, lane table, deviations, conduct disclosures, reconciliation, instrument).
2. `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`:
   - `main(argv)` and a `run()` wrapper;
   - an exit 2 for `--ref`/`--local` keys not in `REPOS`;
   - an exit 2 for a repo read with zero live pins;
   - 12 new self-test cases (history paths, OWN-EXTRA, and seven `run()` scenarios with the network stubbed);
   - a "Known silent drops" docstring section.
3. `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`: nine new mutants, and a docstring on scope.
4. `docs/QUICK_START.md`: a new "Expected output" block of 18 packages, which claims to be what `juniper-ml[all]` 0.9.0 resolved to on 2026-09-22.
5. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`: the Status line's "Option B".
6. `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`:
   - three new round-3 files;
   - a header change to the eight earlier files, claimed to leave their brief and report text verbatim;
   - `README.md`.
7. PR metadata:
   - #2020's new title and body (`gh api repos/pcalnon/juniper-ml/pulls/2020 --jq .title,.body`);
   - the juniper-deploy#227 body's new "Since then" note (`gh api repos/pcalnon/juniper-deploy/pulls/227 --jq .body`).

The round-3 reports that asked for these corrections are the three `round3-*.md` files in that `reports/` directory. They are the specification of what round 3 asked for.

REQUIRED:
- **A round-3 ledger.** For every finding in the three round-3 reports, record one of: applied correctly / applied wrongly / declined (with the banner's stated reason) / dropped with no trace. A dropped finding that changes a number, a disposition or an action is MAJOR.
- **Re-run the instruments.** Run `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test` (it claims 93 passed) and `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py` (it claims 24 of 24 killed). Then run the post-merge simulation: `python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --ref juniper-ml=f68380dd --ref juniper-canopy=fdb9e2de --ref juniper-cascor=a824829b --ref juniper-cascor-client=daa6c675 --ref juniper-data-client=ee1fb5d7 --ref juniper-deploy=e6091c46`. The banner says it exits 0 with no STALE line and two passing AMBIGUOUS lines.
- **Attack the new census code.** Can `run()` still exit 0 when it read nothing, or when it should have refused? Do the stubbed scenarios discriminate? Write at least three mutations of the new code that are not among the 24, and report which survive.
- **Check QUICK_START's 18 packages** against PyPI and a real resolution. For example, `uv pip compile` of `juniper-ml[all]==0.9.0` into your scratch dir (uv is at `/opt/miniforge3/envs/JuniperCascor1/bin/uv`).
- **Naming.** The ecosystem rule: once two or more documents are cited, every reference carries its filename, whether by section number, by role or by implication. List every violation in the changed text and in the #2020 body.

OUTPUT. Only your final message is returned. Give numbered findings. Each has: the claim tested (quoted, with its line number at `f68380dd`), a verdict (CONFIRMED / REFUTED / PARTIAL / OVER-CLAIM / CONTRADICTION / DROPPED / NAMING), a severity (CRITICAL / MAJOR / MINOR), the evidence (a command and its output, or file:line), and a minimal fix. Then the ledger as a compact table. End with **Overall verdict** (SAFE / SAFE WITH FIXES / UNSAFE TO MERGE), a sentence on whether any finding changes a number, a disposition or an action (the procedure's termination test), and a **Changed:** line.

## Final report

**Round 4, Lane B: review of the round-3 fix pass (juniper-ml#2020 `f68380dd` against `4855bf8c`)**

Conventions for this report:
- Bare `L` numbers are lines of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` at `f68380dd`.
- `census_remote.py` means `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, and `mutation_check.py` means `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`.

`f68380dd` is not in the local object store. I read it through `gh api …/compare/4855bf8c...f68380dd` and `contents?ref=`, and the worktree copies have identical sha256.

## Findings

**1. L44–45, "Its publish run, `35795531350`, waits on the owner's `pypi` deployment approval", and L319–320, "The `0.6.1` wheel waits on the owner's `pypi` deployment approval (run `35795531350`)".**
- **Verdict:** REFUTED. These were already stale when the commit was made. **MAJOR**: an Owner-gated item is actually done.
- **Evidence:**
  - PyPI shows `juniper_cascor_worker-0.6.1` uploaded at 2026-09-23T00:37:07Z.
  - Run `35795531350` completed with `success` at 00:37:13Z; `…/approvals` shows `pcalnon approved`.
  - The commit `f68380dd` was made at 01:00:40Z.
  - The author's last PyPI probe was at 00:31:34Z, according to the orchestrator log.
  - L49 still says "Every repository fact below was re-probed on 2026-09-22", while L44, L143 and L669 are stamped 2026-09-23.
- **Fix:** mark the wheel published at 00:37Z and drop it from the Owner-gated list.

**2. L314–317 (Owner-gated): "Whether the juniper-data image should carry the equities extra…"**
- **Verdict:** REFUTED. The fact moved before the commit, in text the fix pass re-asserted. **MAJOR**: a disposition changes.
- **Evidence:**
  - juniper-data#421 ("the container image can generate equities -- yfinance joins the image lock") merged at 00:56:08Z as `68c3cd7c`.
  - Its body opens: "Owner decision, 2026-09-22: the juniper-data container image must be able to generate the equities datasets."
  - The post-merge census run itself reads juniper-data at `68c3cd7c`.
  - No data release has been cut since v0.15.0.
- **Fix:** "Ruled; lock fixed by data#421; ships with the next juniper-data release."

**3. `census_remote.py` L871–874: the new per-repo guard ("zero live pins … remove it from REPOS").**
- **Verdict:** REFUTED. This is a regression. **MAJOR** (latent; no instance today).
- **What happens:** a repo whose only installs are unpinned (the UNRESOLVED class) now exits 2 as "could not run", with advice that would blind the census to that repo.
- **Evidence (crafted, network stubbed; `crafted_runs.py`):**
  - At `4855bf8c`: `exit=1`, with the stale line `juniper-deploy/.github/workflows/ci.yml:1  (none)  [UNRESOLVED]`.
  - At `f68380dd`: `exit=2`, with `RuntimeError: juniper-deploy: zero live pins … remove it from REPOS`.
  - A repo pinned only through a `==${VAR}` variable gets the same message.
- **Fix:** count LIVE and UNRESOLVED together for the guard, or run the verdicts first. Reword the remedy.

**4. The new `run()` scenarios (`census_remote.py` L780–818): do they discriminate?**
- **Verdict:** PARTIAL. **MAJOR**.
- **Evidence (`mutants.py` against the 93-case self-test):** my mutants N1–N5 survive, N6 is killed.

  | mutant | kind | result |
  | --- | --- | --- |
  | N1: `__main__` calls `main()` instead of `run()` | new code | survives; the CLI exits 1 on `--ref juniper-cascr=abc` (unmutated: 2), so the entry point the verification block uses is untested |
  | N2: the unknown-key check ignores `--local` | new code | survives; `--local juniper-deplyo=/nonexistent` exits 0 (unmutated: 2) |
  | N3: the guard fires only when a repo has zero hits | new code | survives, because the scenario repo has no hits at all; exits 0 on the variable-pin case (unmutated: 2) |
  | N4: `.md` dropped from `TEXT_SUFFIXES` | reading layer | survives; over the real corpus, `main` goes from 23 stale lines to 16 |
  | N5: `.py` dropped from `TEXT_SUFFIXES` | reading layer | survives; `main` goes from 23 to 18 |
  | N6: `run()` reports a crash as exit 1 | new code | killed |

  - N4 and N5 survive because the stub replaces `load_remote` wholesale, so the tarball member filter is never exercised.
  - "a repo read as empty" (L806) passes through the zero-live guard, not the empty-read guard; the empty-read guard's mutant, R3-B's M12, still survives.
  - No scenario checks output. The passing-AMBIGUOUS listing mutants (R3-A's and R3-B's M18) survive, and they erase the two lines the verification block at L372 promises.
- **Fix:** stub `gh`/tarball bytes rather than `load_remote`. Assert the stderr reason and the listed lines. Add a `--local` case, a hits-but-no-live case, and one CLI subprocess case.

**5. L246–249: "added cases, and nine mutants, for the fail-open ones among them… and for the repo's own extra. The rest still survive. The docstring … names them."** The same claim appears at L497–498 and in the #2020 body at L44–45.
- **Verdict:** OVER-CLAIM. **MAJOR**, because a verdict-producing survivor remains.
- **Evidence:** I re-applied all 47 round-3 lane mutants to `f68380dd`.
  - 13 are now killed and 23 still survive.
  - R3-B's M16 (the extra taken from the first spec anywhere in `pyproject.toml`) survives. At `main` it loses `juniper-ml/.github/workflows/ci.yml:1879` (23 stale lines become 22). That is the "repo's own extra".
  - `mutation_check.py`'s docstring (L23–28) leaves 12 surviving rules unnamed, among them M16, the pre-filter, the bare-release verbs, composite actions, the ADJUDICATED lookup and table, the floor-only skip, three run guards, the `--expect` 0.x check and the listing.
  - "47 … 36" counts duplicates: 8 of the anchors are identical across the two lanes.
  - Two of the "nine … survivors" (L56) mutate code this same pass added.
  - `mutation_check.py` L13 still says the banner cites "15 of 15".
- **Fix:** add a `census_members` case for extra extraction, name every survivor, and state the numbers as distinct mutants.

**6. #2020 metadata: auto-merge and the stored squash body.**
- **Verdict:** DROPPED: the squash half of R3-A #15 was not applied. **MAJOR**, as an action.
- **Evidence:**
  - At 01:08:14Z someone re-armed SQUASH auto-merge as `pcalnon`, after the author disarmed it at 01:03:39Z and promised "a curated squash message".
  - The repo is set to `squash_merge_commit_message: COMMIT_MESSAGES`, so the stored body carries the first commit's "31-case --self-test", "19 current-state lines", "81 cases", "15 of 15", "28 sibling worktrees" and "Role references carry filenames throughout."
  - The PR is `BEHIND`, so the merge fires on the next update-branch, with L510 "Round 4: pending" still in place.
- **Fix:** disarm now; re-arm with an explicit curated body once round 4 is applied.

**7. Naming.**
- **Verdict:** NAMING. **MINOR**.
- **Banner, changed lines:**
  - L15 "Its own status banner"
  - L191 "The table row"
  - L194 "it also names"
  - L350 "the census's"
  - L366 "The census. Run it"
  - L415 "those reports"
  - L436 bare "§2"
  - L441 "its report", meaning `round1-laneB2-amputation-executability.md`
  - L449, L451 and L455: four memory files left unnamed
  - L468 "the census's limits"
  - L473–475 "the lane transcripts, the test file"
  - L476 "R2-A's X7 mechanism", meaning `round2-laneB-attack-the-fix-pass.md`
  - L478 "B1 said … A2 measured"
  - L498 "that script's docstring"
  - L501 "its own docstring"
  - L504 "the census reads"
- **#2020 body:**
  - L8 "It said"
  - L15 "Its 'want 0'" (flagged in round 3, not fixed)
  - L19 "that document's items" (not fixed)
  - L27 "the banner corrects"
  - L31 "it recorded"
  - L72 "its §3" (not fixed)
  - L87 "the conduct record"
  - L89 "recorded in the banner" (not fixed)
  - L92 "The census"

**8. L469, the R3-B row: "its independent list misses nothing the census misses".**
- **Verdict:** CONTRADICTION: it inverts what R3-B found. **MINOR**.
- **Evidence:** `round3-laneA-census-adequacy.md` says the census misses 0 lines against the independent list, under the census's own rules.

**9. L238–240: "an independent instrument agreed with it … the one stale line left".**
- **Verdict:** OVER-CLAIM. **MINOR**.
- **Evidence:**
  - That instrument disagreed on 5 floor-only lines, and none is recorded as remaining work.
  - One of them is juniper-ml's own `main-verify.yml:72`, `(PyPI >=0.8.0)`. Its siblings, cascor `main-verify.yml:64` and deploy `:69`, were fixed as stale by cascor#673 and deploy#228.

**10. `census_remote.py` L41–66 ("Known silent drops") and L250–256.**
- **Verdict:** PARTIAL. **MINOR**.
- **Evidence:**
  - The heading says "Each is dropped with NO output", but floor-only prose (REQUIREMENT) and `tests/` literals (FIXTURE) are counted.
  - "non-.py files are FIXTURE" is false: `tests/README.md` and `tests/*.rst` are judged as COMMENT.
  - Not listed:
    - `juniper-ci-tools<1.0,>=0.8.0` passes as REQUIREMENT;
    - the `| repo | ci-tools pin |` table shape;
    - SNAPSHOT_RE anchoring;
    - the risk of an ADJUDICATED key on a long line.
- **Fix:** state each rule as either dropped or passed-and-counted.

**11. L455–456: "No round-3 lane read either".**
- **Verdict:** PARTIAL. **MINOR**.
- **Evidence:**
  - At 23:50:33Z R3-C read the orchestrator's narration of those edits, including "ml 11, canopy 3, cascor 2, cascor-client 3, data-client 2, deploy 2".
  - The two files edited mid-round-3 are `reference_prose_form_version_ranges_evade_pin_regexes.md` (23:29:30Z) and `MEMORY.md` (23:30:02Z). Neither is named.

**12. `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/README.md`.**
- **Verdict:** CONTRADICTION. **MINOR**.
- **Evidence:**
  - L8–9 says "restates none of the record's content", yet L12–13 restates conduct facts.
  - The "Target:" line of `round3-laneA-census-adequacy.md` omits the two scripts that R3-B reviewed.

**13. #2020 body L77: "Round 2 had three lanes, briefed on the round-1 corrections".**
- **Verdict:** PARTIAL. **MINOR**.
- **Evidence:** R2-C was briefed on the whole document (R3-A #16).

**14. L337–338: "default seed (42, since juniper-data#319)".**
- **Verdict:** PARTIAL. **MINOR**.
- **Evidence:**
  - #319 is an issue; the change was PR #322.
  - 42 is only a fallback: the `JUNIPER_DATA_DEFAULT_GENERATOR_SEED` environment variable can override it.
  - deploy#227's body (L49) still says "a seeded request", so R3-C #4 was not carried there.

**15. L185: "a 0.6–0.8 s reading fits … plus 0.2–0.4 s".**
- **Verdict:** PARTIAL. **MINOR**.
- **Evidence:** the 0.586 s reading falls below that range; it implies 0.19 s of other delay.

**16. L423–431, the lane table.**
- **Verdict:** DROPPED. **MINOR**.
- **Evidence:** rounds 2 and 3 ran 2 Lane A and 1 Lane B each, below the §3 cell of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, which asks for 3+ and 2+. The shortfall is not listed as a deviation.

**17. Refusal gaps in `census_remote.py` itself.**
- **Verdict:** REFUTED, against "a census that could not run is not clean". **MINOR**.
- **Evidence:**
  - Duplicate `--ref juniper-ml=aaaa --ref juniper-ml=bbbb` silently reads `bbbb` and exits 0.
  - When `--ref` and `--local` name the same repo, `--local` wins silently.

**18. After the freeze: moved during round 4 (01:02:51–01:12:14Z). Not a fix-pass defect.**
- cascor-client#170, data-client#210, deploy#227, deploy#228 and canopy#655 have all merged.
- So the "awaiting merge" list (L347–357) and L344 "sequenced after juniper-deploy#227" are now stale.
- Round 4's own conduct record must not claim that no reviewed PR changed during the round.

**19. CONFIRMED.**
- **Instruments:**
  - The self-test prints `93 passed, 0 failed`.
  - `mutation_check.py` prints "24 of 24", and every kill is a genuine FAIL line.
  - The post-merge command exits 0 with `STALE (none)` and two passing AMBIGUOUS lines, `REFERENCE.md:3023` and `test_ci_tools_drift.py:461`. An offline replay reproduces this.
  - At `main` as of the commit it exits 1 with 23 stale lines (11/3/2/3/2/2).
- **QUICK_START:** its 18 packages match `uv pip compile 'juniper-ml[all]==0.9.0'` on Python 3.12, 3.13 and 3.14. The metadata names match, and the two transitive packages are correct. The author also ran `uv` at 23:32Z.
- **Worktrees:** 30 unique and 2.
- **X7:** the five runs, their branches and PRs, 4 green re-runs, `main` never re-run, and the constants.
- **Keepalive:** §E item 13 at `:349-362`.
- **6f:** absent from the five later documents.
- **publish-image.yml:** all five import their application package on the publish path.
- **v0.6.1:** the tag is on `38f39cb8`; #192 made the version metadata-derived; the manifest was published at 23:08:23Z.
- **Archive:** the round-3 briefs, mid-run messages and reports are byte-identical to the transcripts. The header edits to the eight earlier files are header-only.
- **Tests and CI:** 482 tests OK (skipped=1) on the extracted tree; 28 CI checks green.
- **deploy#227:** the "Since then" note is accurate.

## Ledger

| report | finding | status |
| --- | --- | --- |
| `round3-laneB-attack-the-round2-fix-pass.md` | 1–4, 7–14, 17, 18 | applied correctly |
| same | 5 | applied, with inaccuracies (#10) |
| same | 6 | applied, then over-claimed again (#5) |
| same | 15 | title applied; squash half **DROPPED** (#6, MAJOR) |
| same | 16, 19 | partial (#13, #7) |
| same | ledger items A3#8, B1#6, B2#12 | applied correctly |
| same | `#163's` | declined; the reason (original text) is verified |
| `round3-laneA-census-adequacy.md` | 2 | partial (M13 not added but now killed; verdict cases still hand-fed; ADJUDICATED keying declined); new gaps (#4) |
| same | 3–7 | declined, recorded (4 only in part) |
| same | 8 | applied (#10) |
| same | 9 | applied, but it introduced a regression (#3) |
| same | 10 | applied; `--local` untested (#4) |
| same | 11 (clause order), 14, 15 (long line) | **DROPPED**, no trace (MINOR; no number changes) |
| same | 12 | declined; "agreed" over-states (#9) |
| same | 13 | recorded inaccurately (#10) |
| same | 1, 16 | n/a |
| `round3-laneA-record-and-new-numbers.md` | 2, 3, 5–9, the untraceable list, caveats | applied correctly (3: pool shortfall, #16) |
| same | 1 | applied; the round-3 disclosure is partial (#11) |
| same | 4 | applied in the banner; not carried to deploy#227 (#14) |

## Overall verdict

**SAFE WITH FIXES.** Before any update-branch on #2020, apply the fixes for findings 1, 2, 3 and 5, and disarm or curate the auto-merge (finding 6). This round does not meet the termination test: findings 1 and 2 change dispositions, 3 and 6 change actions, and 5 changes the stated adequacy of the census. The next fix pass therefore needs its own round.

**Changed:** no repository files. Everything I wrote is under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r4a/`:
- the fetched `old/`, `new/`, `corpus/` and `tree_f683/`;
- `harness.py`, `mutants.py` and `mutants/`, `survivor_effects.py`, `crafted_runs.py`;
- the verification scripts: `verify_r3_archive.py`, `orch_window.py`, `sibling_prs.py`, `x7_runs.py`, `publish_image_imports.py`, `sixf_scan.py`, `floor_lines.py`, `docstring_claims.py`, `metadata_names.py`;
- the `uv` resolutions and the run outputs.
