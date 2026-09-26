<!-- Archived verbatim 2026-09-24 from subagent a395d3bc7b4186fe5 of session bc31e993 (final message). -->

I re-derived all 12 items you listed, and every one holds against primary sources. The v2 → v3 changes I checked beyond that list turned up **3 LOW and 4 NIT** problems, and no HIGH or MEDIUM. Nothing was edited: v3's hash is unchanged (`62f9b2bf…`), `hvF/` is pruned, and the juniper-data server I started is stopped (port free, nothing written).

## Findings

**LOW-1. The canopy ledger status is wrong (L141).**
- **Text:** "At 20:25Z the register lane said it would forward them to the canopy E2E session … No forward has been confirmed."
- **What is true:**
  - The 20:25:20Z message covers only the "Nothing was loaded" copies ("send me the exact file:lines … I'll forward them").
  - The other three items were already filed. The canopy E2E handoff reserves F-CANOPY-060 for the `:8410` cut, 061 for LOW 3 and 062 for LOW 4. It is `graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md:53-66`, saved 19:40:55Z.
  - The `:8381`/`:42` copies have no id. They sit in `bubbly-meandering-pie/…/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`, saved 20:43:56Z.
  - The register lane's 00:25Z handoff says "The canopy E2E session has exited" and that 060's fix is unowned.
- **Corrected text:** "060–062 hold the `:8410` item, LOW3 and LOW4 (untracked, in the canopy E2E handoff). #685 fixes 061 and 062; 060 has no owner. The `:8381`/`:42` copies sit, with no id, in the canopy-combined handoff. The canopy E2E session has exited."

**LOW-2. The juniper-data serve recipe leaves out the fixture the probes need (L68-70).**
- **Text:** "Serve juniper-data by hand, with … scratch storage and import dirs".
- **What is true:**
  - `probe_realjd_refusals.py`, `probe_realjd_blank.py` and `…_cascor688_realjd_error_texts.py` all request `csv_import` with `file_path: "big.csv"`.
  - juniper-data looks that file up under `import_dir` and raises `FileNotFoundError` (`generator.py:223`) before the cap check (`:261`). With an empty import dir, the three "REAL refusal" cases never reach the refusal.
  - Only the harness docstring (`:17-18`) describes the file: "a small CSV with a `label` column; `max_bytes=40` puts it over the cap".
- The command and the env names themselves are fine (Verified, item 9).
- **Corrected text:** add "set `JUNIPER_DATA_STORAGE_PATH` and `JUNIPER_DATA_IMPORT_DIR` to scratch dirs, and put `big.csv` (a small CSV with a `label` column, over 40 bytes) in the import dir. Auth, metrics and Sentry are off by default; still set the six DSN variables to `""`."

**LOW-3. A plain `git push` does not land on `pr-683` (L122).**
- **Text:** "That worktree's upstream is `refs/heads/pr-683`, so a plain `git push` from it lands there."
- **What is true:**
  - The upstream is right: `branch.fix/secret-leaks-683-validation.merge` is `refs/heads/pr-683`. It came from `fetch origin pull/683/head:refs/remotes/origin/pr-683` at 18:33:06Z.
  - No `push.*` key is set in any scope, so `push.default` is Git's default, `simple`.
  - A scratch reproduction on git 2.53.0 exited 128 with "The upstream branch of your current branch does not match the name of your current branch" and moved nothing. Only `push.default=upstream` landed on `pr-683`.
  - An IDE push, or `git push origin HEAD:pr-683`, would land there. The branch config carries `vscode-merge-base`.
- **Corrected text:** "…upstream is `refs/heads/pr-683`. A plain `git push` from the command line refuses because the names differ, but an IDE push or `HEAD:pr-683` lands there."

**NIT-1. The sandbox refusal list is too broad (L160).**
- **These ran:** loops around `git`, `gh`, `tar`, `find` and `sed -n`, and variables around `gh`, `tar` and a `git` argument.
- **These were refused:** a computed `git -C "$d"`, variables around `sed` and `find`, and `env -u` inside any compound command. That includes `env -u FOO true; echo`; on its own, `env -u` runs.
- **Corrected text:** "variables around `sed` or `find`; a computed `git -C` path; `env -u` inside any compound command."
- The unchanged "backticks inside a heredoc" did not reproduce with `cat`.

**NIT-2. The gate-comment request date (L134).** "(2026-09-24)" is wrong in UTC: the SendMessage went at 2026-09-25T00:19:33Z. Every other time in the file is in Z.

**NIT-3. "Published after this file's PR merges" (L9).**
- At 23:34:29Z the register lane asked for "the final path plus the commit SHA or PR number". It is not waiting for the merge.
- Since v3 was written, the register lane has saved its own handoff, marked "Superseded if consolidated" (untracked, about 00:25Z): `fizzy-hugging-dream/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. `[24f8d8]` may be gone before it consolidates, so name that path beside L25's fallback.

**NIT-4. "Signed commits cannot merge" (L53).** The accurate claim is narrower: a merge commit cannot be signed, because API-signed commits are single-parent. PRs made of signed commits merge normally. L148 already states this correctly.

## Verified

1. **Owner's option text:** transcript line 5164 (10:22:00Z) has "Fix everywhere now (Recommended)", whose description ends "Releases stay yours." Line 5166 (18:30:09Z) has the answer "Fix everywhere now (Recommended)".
2. **F5:**
   - `_ENCODING_PROBES` is at service-core `:101` (`main`), data `:34` (`0bee089e`) and cascor `:31` (`97341680`); each holds `\U0001f511`.
   - canopy `:172` is `NON_ASCII`, used only as `APIKeyAuth(["key1"])` (`:174-176`).
   - The pair and U+1F511 both encode to `b'=\xd8\x11\xdd'` under UTF-16-LE with `surrogatepass`.
3. **F9 and F3:**
   - service-core `CHANGELOG.md:58` says "closes 4001", and so do cascor#689's commit message and CHANGELOG diff.
   - data#440 has no such text in its one commit, CHANGELOG diff or PR body. Neither do juniper-ml's root CHANGELOG nor observability's.
   - F3: under CI's `-m "unit and not slow"`, 72 of 116 tests are selected and `TestAPIKeyAuth`'s spy test is deselected.
4. **Locks and caps:** every listed line holds on each `origin/main`. That includes cascor `requirements-cpu.lock:129/:133`, whose header says "CONTAINER IMAGE", and juniper-ml `pyproject.toml:94`. None is missing:
   - juniper-deploy, juniper-cascor-worker and juniper-cascor-client pin neither package.
   - juniper-data-client has only `>=0.1.1` floors.
   - data `conf/requirements_ci.txt:100` and cascor `:92` pin `==0.4.0`, but they are `juniper-generate-dep-docs` output that CI uploads (`ci.yml:461`, `:573`), not something anything installs from.
5. **Stray branches:**
   - Both point at `4caf9389`, and neither has a PR.
   - The reflog shows "update by push" at 22:55:30Z and 22:55:40Z.
   - None of the 34 transcripts written after 22:50Z has a push naming them, or any `git push` between 22:40Z and 23:10Z.
6. **Signing:** `24103c23` is signed with the Yubikey key; `5bd5eec5` and `4caf9389` are unsigned. The three HEAD trees equal `97341680`, `0bee089e` and `4a8af2a0`.
7. **`095a2108`:**
   - It is the fifth of #2077's six branch commits (pcalnon, 19:39:42Z), before the squash at 19:52:49Z, and it is not an ancestor of `main`.
   - `main`'s blob `b4a6164b` equals its blob, and its behaviour is unchanged.
   - canopy#685's two added commits are also pcalnon's.
8. **Message times:**
   - 19:06:26Z, to the register lane: the `:8410` item, LOW3 and LOW4.
   - 20:42:33Z: `:8381` and `:42`.
   - 20:25:20Z: the register lane's promise.
   - Also confirmed: APD-CASCOR-014 stays open "until the conftest fix lands" (20:37:02Z), and none of the three APD IDs is in the register on `main`.
9. **Serve command:**
   - `create_app(settings=None)` is a factory at `app.py:81`.
   - From a scratch `0f0f7e0e` tree: `/v1/health` 200, anonymous `/v1/generators` 200 (auth off), `/metrics` 404 (metrics off).
   - All six env names exist under the `JUNIPER_DATA_` prefix.
   - The shared checkout's `main` is one commit behind `origin/main`, so serve from a fresh tree.
10. **Sandbox, refused as listed:** `git -C` and `cd … &&` git into the shared checkout, "git" inside `python3 -c`, `$(...)` feeding `git` or `gh`, and a `-C` path relative to a `cd`. `git -C` into the other juniper-ml worktree is allowed.
11. **Verification commands:**
    - GraphQL: #690, #689 and #440 are OPEN, CLEAN and unarmed at the documented heads; #685 is MERGED as `dc5ea02e`.
    - `gh pr list --head …` printed `[]`.
    - Fork-drift tests: "OK (skipped=3)", and "OK" with the opt-in. The shared checkout's copy equals `main`, and `:205-209` holds the comment.
    - `ls` prints six rows; `df -i` shows 83%.
12. **Git status:**
    - The branch is at `5af9d722`, and nothing is staged.
    - There are 17 reports (12 of this lane's plus 5 validation), 5 harnesses, 63 probes (21/10/19/13), 3 ad-hoc scripts and this file.
    - The README adds four rows plus a five-line paragraph.

Also confirmed:
- CI is green on all six merge commits.
- #686's branch and `refs/pull/686/head` are both `e452a660`.
- The PR opener's `BRANCH` matches L13.
- #683 has 60 non-blank CHANGELOG lines, all under `[Unreleased]`.
- (b)'s "the clients would send" holds: both clients put the key in the header without checking it.
- The three memory files v3 cites say what it claims.

**Changed:** nothing in any repository.
