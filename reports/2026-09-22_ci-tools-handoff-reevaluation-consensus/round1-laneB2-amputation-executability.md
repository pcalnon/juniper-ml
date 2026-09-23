<!-- markdownlint-disable -->
# Round 1, lane B2

**Entry point:** adversarial: amputation and executability.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T19:55:49Z to 2026-09-22T20:20:36Z, read-only. Agent `agent-a765f117f302f2596`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are Lane B2 (analysis review: AMPUTATION + EXECUTABILITY) in an independent-agent consensus review. Your brief is to REFUTE: find what the changes broke, dropped, contradicted, or made unexecutable. "It looks fine" is worth nothing.

READ-ONLY RULES (hard): do not edit/create/delete files in any repo; do not commit, push, comment, merge, close or approve anything. Worktree-isolated harness: only read-only `git diff`/`git show`/`git log` inside the juniper-ml worktree below; use `gh api` for other repos; plain commands only (the harness refuses shell loops over variables touching gh/git and very complex one-liners). Scratch dir: /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/b2/.

WORKTREE (frozen): /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl. `git diff` there shows every uncommitted change: a status banner + header lines + four in-place notes in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`; two SHA corrections in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`; three range edits in `docs/REFERENCE.md`; three in `util/fleet_triage/predict_merge.py`; plus an untracked new script `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`. The `__VALIDATION_RECORD__` placeholder in the banner is intentional (to be filled after this review). Also review the diffs of juniper-deploy#227 and juniper-canopy#655 (`gh pr diff N --repo pcalnon/<repo>`).

CHECK:
1. AMPUTATION / CONTRADICTION: Does the banner contradict anything still stated elsewhere in the same document (the goal section, "Remaining work", "Verification commands", "Git state", "Validation record") without an in-place note? Does it contradict the later chain (`HANDOFF_2026-09-15_...`, `HANDOFF_2026-09-17_...`, `HANDOFF_2026-09-22_ten-prs-landed-...` in the same directory, read from the worktree which equals origin/main) or the design of record `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`? Did the in-place edits damage the original text (e.g. a note inserted mid-list or mid-code-block in a way that breaks rendering or meaning)?
2. FRESH-SESSION ROLE-PLAY: pretend you are a new session given ONLY the updated 09-11 document. Would you be misled into doing something wrong (re-running a closed item, removing worktrees, approving a deploy, trusting the wrong grep)? Is it clear where to go next?
3. EXECUTABILITY: in the banner's "### Verification commands (use these, not the goal's)" block, check each command's quoting and jq syntax as literal shell (e.g. escaped `\(` inside double quotes, `?recursive=1` needing quotes, a `ls -d` glob relative to the `cd` directory, whether the `cd` target contains the paths used). You MAY run the read-only ones to confirm.
4. MARKDOWN: `.markdownlint.yaml` in the worktree (MD013 line length 512 applies to table rows too); check the banner's table rows, any row over 512 chars, broken table (a newline inside a cell), unbalanced backticks. You may run `python3` to measure line lengths. If `markdownlint`/`pre-commit` is available (`/opt/miniforge3/bin/pre-commit`), you may run `pre-commit run markdownlint --files <the two handoff files>` read-only (it must not modify files; if it would, report instead).
5. CI TRAPS in the four artifacts: any literal skip-CI marker token in commit messages or PR bodies (`gh pr view 227 --repo pcalnon/juniper-deploy --json body,commits`, same for canopy#655) — that token orphans required checks; a hidden test pinning a changed string (`grep` the juniper-ml `tests/` for the old ranges and for `predict_merge` hint text; for juniper-canopy check its AGENTS.md date check workflow `.github/workflows/agents-md-touch-up.yml` against the PR's Last Updated value 2026-09-22 in UTC); for juniper-deploy, whether any test or doc pins `juniper-data:0.14.0` elsewhere; whether the CHANGELOG edits in deploy#227 sit under the right headings.
6. The census script: does it follow `util/ad-hoc/README.md`'s header convention; any bug that would make its documented exit codes wrong?

OUTPUT (final message only is returned): numbered findings — location (file:line or PR), verdict/type (AMPUTATION / CONTRADICTION / UNEXECUTABLE / RENDER / CI-TRAP / MISLEADING / OK), severity (CRITICAL/MAJOR/MINOR), evidence, minimal fix. Then overall verdict: SAFE / SAFE WITH FIXES / NOT SAFE. Terse, no preamble.

## Final report

1. **L76–80 (the "Where the remaining work lives" section) — MISLEADING, MAJOR.** The bullet labels juniper-deploy#227, juniper-canopy#655 and "this banner's own juniper-ml PR" as **"Not owner-gated"**. The only merge-approval rule ("obtain your own before merging anything") is in the goal at L113–114, and L12 tells the reader not to use the goal. `feedback_headless_merge_approval_policy.md` says every merge needs Paul's explicit approval in that session. deploy#227 is `mergeStateStatus: CLEAN` right now, so it could be merged on the spot. **Fix:** "not owner-gated to prepare; merging each still needs the owner's explicit approval in your session."

2. **L36 vs L76–78 — CONTRADICTION, MAJOR.** L36 says the census found the same class "in two more places, **now fixed too**". canopy#655 is OPEN (BLOCKED, unit legs pending), and the juniper-ml half is uncommitted. The census against remote `main` still exits 1 on 7 lines. The counts also disagree: "two more places" (L36), "three … install ranges" (L77), and in fact 7 lines in 3 files across 2 repos. **Fix:** "fixes opened, not merged: canopy#655 (AGENTS.md:517) and this PR (docs/REFERENCE.md:3754/6392/7072, predict_merge.py:57/180/234)."

3. **L14 and L79 — MISLEADING, MAJOR.** The banner sends the reader to the tip handoff `HANDOFF_2026-09-22_ten-prs-landed…`. Its L12–14 still says "three concrete items are startable", but:
   - Item 3 (the data wheel `exclude`) was closed by data#420 at 19:05Z.
   - Item 4 (the worker docs) was closed by worker#193 at 18:59Z.
   - Item 1 still claims the import smoke is missing from the publish path. That has been false since the 09-21 hardening: juniper-data `publish-image.yml:213-214` imports the app on the publish path.
   - The tip's check "expect 95 of 199" now reads `0.15.0 201 97`.
   - Its Wave 4 bullet was written before the Option B ruling.
   
   No open PR updates the tip. "Re-scoped item 1" implies the tip did the re-scoping; it did not. **Fix:** one sentence saying the tip's items 3 and 4 are done and item 1's import half has shipped, or a dated note in the tip.

4. **L85–88 — UNEXECUTABLE until pulled, MINOR.** The census script is absent from the primary checkout (whose `main` is `c4a67481`). The 09-17 handoff (`HANDOFF_2026-09-17_container-registry-wave-3-complete…`, L211–216) recorded this exact trap. **Fix:** add a line saying the PR must be merged and `juniper-ml` pulled first, or an API fallback: `gh api repos/pcalnon/juniper-ml/contents/util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --jq .content | base64 -d | python3 -`.

5. **L28 — RENDER/convention, MINOR.** This table row is 563 characters, over the 512 limit; it is the only row over. The original file's longest line was 193. `prompts/` is excluded from the markdownlint hook, so CI will not fail. **Fix:** move the environment details into a note below the table.

6. **L5, L19, L27, L36, L46–47, L61, L71, L79 — naming convention, MINOR.** `HANDOFF_2026-09-15_…` and `HANDOFF_2026-09-17_…` are each ambiguous: two files match each prefix. With two or more documents cited, role references ("the successor", "the tip handoff", "plan §5.1", "the procedure above", "the predecessor's") must carry filenames. **Fix:** write the full filenames.

7. **Table L21–36 and note L207 — AMPUTATION, MINOR.** The goal lists items 1, 3, 4, 5 and 7, but item 1 (first publish in recurrence and canopy, and checking package visibility) has no row. It is closed: recurrence 0.5.0 on 09-10, canopy 0.8.0 on 09-12, which came up public. **Fix:** add a row.

8. **L30 and L65–66 — MINOR.** § What shipped also lists ml#1869 without a SHA; it is `ee57a892`, merged 2026-09-10T00:55Z, which is correctly 09-10 in UTC. The banner names only canopy#619 and cascor#645 as missing SHAs. "CONFIRMED" re-checked only SHAs and runs, not the section's "47 pin lines across 26 files per pass". That figure sits next to the banner's "54 live pins" and counts something different.

9. **L25 — CONTRADICTION (time zone), MINOR.** Worker "on PyPI 2026-09-18" is correct in UTC (upload 00:18:32Z). The container-registry plan (L71) and the 09-17 handoff (L124) say 2026-09-17, the local (CDT) date. The banner doesn't flag the difference. **Fix:** add a parenthetical noting it.

10. **Container-registry plan (`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`) — CONTRADICTION, MINOR.** Its §5 note (L286–288, "a separate check that does not exist") and §5.2 (L419–422, "nothing in juniper-deploy detects a stale pin") are made stale by deploy#226 (merged 08:34Z). Banner L26 cites deploy#226 but sends readers to the plan without a caveat. **Fix:** add a caveat in the banner or a one-line fix to the plan.

11. **`util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py` — MINOR, latent.** Today's exit 1 is correct, and a post-merge simulation over the worktree is clean.
    - (a) Docstring L40–43 promises exit 2 when a download fails, but L192–196 catch only `RuntimeError`. A missing `gh` (`FileNotFoundError`), a `JSONDecodeError`, a truncated tarball (`TarError`/`EOFError`), missing `packaging` (L141) or a bad `--expect` (`InvalidSpecifier`) all crash with a traceback and exit 1 — the same code as "stale pins found".
    - (b) `is_floor_only` (L123–126) also treats `==`, `~=` and `!=` as floor-only, so a stale doc line like `pip install juniper-ci-tools==0.6.0` is exempted. The Exit text doesn't mention this exemption or the known-example one.
    - (c) `KNOWN_EXAMPLES` matches by file, not by line, so any future stale line in `propose.py` would be suppressed.
    - (d) `__doc__` starts with a newline, so the `--help` description is empty (L175).
    - The header follows the `util/ad-hoc/README.md` convention; the `--` style is used by 85 of 139 siblings.
    - **Fix:** catch `(RuntimeError, OSError, ValueError, tarfile.TarError, EOFError, ImportError)` and return 2; treat only `>=`/`>` clauses as floors; use `__doc__.strip()`.

12. **`HANDOFF_2026-09-11_container-registry-oq1-ruled…`, L1–7 — MISLEADING, MINOR.** It now carries "Corrected 2026-09-22" markers (L34, L172) but no superseded status line. Its body still says Wave 3 is not cut, "no post-#179 image exists", and Wave 4 means repository secrets. **Fix:** add one Status line pointing to the tip.

13. **L95, L97, L18–19, L28, L70–71 — MINOR.**
    - The verification commands check 1 of 5 `dockerhub` environments and count 8 of the 15 worktrees claimed at L34. I checked all of them: every environment has 0 secrets, no repository-scope `DOCKERHUB_*` exists, and all 15 directories exist.
    - "Against GitHub, PyPI and GHCR" doesn't fit the ping/binfmt check or the `worktrees/` listing, which are local probes.
    - Nothing says who created the five environments at 19:45:59Z. ml#2009's body says "Nothing was registered or created."
    - "Can be run as written": steps 1–2 of the procedure's §5.2B are already done; only step 3 remains. Re-running steps 1–2 is harmless.

14. **canopy#655 PR body — MINOR.** It says the census found "one of two … current-state documents … The other is juniper-ml's own docs/REFERENCE.md, fixed there". That leaves out predict_merge.py (3 lines), and "fixed there" is uncommitted. **Fix:** update the body with `gh api -X PATCH` (`gh pr edit` is broken on gh 2.46).

15. **docs/REFERENCE.md push — CI-TRAP (operational), MINOR.** The file is 808,872 bytes. Uploading it whole through createCommitOnBranch is in the size range that has returned HTTP 499 before (327 KB did, twice), and it is the file most at risk of being clobbered by a stale whole-file upload. **Fix:** run the staleness pre-flight immediately before pushing, push REFERENCE.md as a separate follow-up commit, and confirm `gh pr diff` shows exactly 3 changed lines in it.

16. **L77, L88, L102 — MINOR.** "This banner's own juniper-ml PR" is unnumbered, and `__VALIDATION_RECORD__` is still a placeholder. Fill both before merging.

17. **L110–113 — MINOR.** The goal's "Nothing is left that does not need the owner" and "ran to completion across all nine repos" were false when written (the two stale cascor pins, Corrections 1). There is no in-place marker; L12's "do not paste" mitigates this.

18. **OK — checked and clean:**
    - **Verification commands:** all 9 run as literal shell and print the values stated. The census reports 54 live pins in one range and exits 1. The others return `…juniper-ci-tools-0.9.0 packaging-26.3`, `[]`, `[]`, `0`, `true`, `0`, `43785fe0 b374f285` and `8`. The jq quoting is correct.
    - **Markdown:** the structure screen finds 0 problems, the doc-link validator passes, backticks balance, every table row has 3 pipes, and the in-place notes don't break any list or code block. Nothing was deleted from the 09-11 document (+110/−0).
    - **CI-skip markers:** none in either PR's title, body or commits, or in the diff.
    - **Hidden tests:** none pin the changed strings; `test_predict_merge` checks only for "unavailable". 107 related tests pass. The docs-additions check only warns on these edits, and the memory budget covers AGENTS.md only.
    - **deploy#227:** CLEAN with 14 checks green. No other `juniper-data:0.14.0` pin remains, `### Added` sits correctly before `### Changed` with no duplicate categories, and the Helm chart version convention is unaffected.
    - **canopy#655:** the date check passes on "line changed in this PR", so a re-run after the UTC day rolls over still passes.
    - **Values re-checked live:** all 23 SHAs in § What shipped, the #646 SHA fix, the 97/201 wheel count, the environments' tag policies, turing's 100% ping loss, and the X7 test's constants.

**Incidental:** a `py_compile` check I ran wrote two gitignored `.pyc` files: `util/ad-hoc/__pycache__/2026-09-22_ci_tools_pin_census_remote.cpython-314.pyc` and `util/fleet_triage/__pycache__/predict_merge.cpython-314.pyc`. `git status` is unchanged, and I left them in place.

**Overall verdict: SAFE WITH FIXES.** Findings 1–3 must be fixed before merging.
