<!-- Archived verbatim 2026-09-24 from subagent af0a79cb3c9b8332d of session bc31e993 (final message). -->

v4 holds up. Every v3→v4 claim I re-derived is true against primary sources, and the new serve script works and stays in scratch. There are no HIGH or MEDIUM problems: I found 1 LOW and 5 NITs. v4 (`HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`) is unedited (sha256 `11ddd865…`), the server is stopped and `hvH/` is pruned.

## Findings

**LOW-1. v4's Step 0 fallback (L25) can hand this lane the register lane's work.**
- **Text:** "If `[24f8d8]` is gone: use the consolidated handoff if it is on `main`, else the register lane's own handoff named above. Otherwise ask the user."
- **What is true:** the register lane's handoff (`…defect-register-round-42-ml2088-…-closes-pr-owed.md`) opens with "Continue defect-register round 42". That work is what v4 L38 says to start none of, and v4 L11 says v4 governs until the consolidated handoff lands.
- **Corrected:** "If `[24f8d8]` is gone and no consolidated handoff is on `main`, this file still governs this lane. Read the register lane's own handoff for its state, and ask the user who takes over its items."

**NIT-1. The `pkill` remedy is incomplete (v4 L168).**
- **Text:** "Bracket one character of the pattern, e.g. `--port 1879[7]`."
- **What is true:** the self-kill is real. A `bash -c` running an unbracketed `pkill -f` died (rc −15); bracketed, it survived. But:
  - `pkill --signal 0 -f '--port 1879[7]'` exits 2 with "unrecognized option", killing nothing.
  - A bracketed pattern still matched my own shell when the same command also held the unbracketed text.
  - `pkill -A` (`--ignore-ancestors`, procps-ng 4.0.4) spared the shell.
- **Corrected:** "Use `pkill -A -f 'uvicorn.*--port 18797'`, or bracket a character (`'uvicorn.*--port 1879[7]'`) and run pkill as its own command. A pattern starting with `-` needs `--` before it."

**NIT-2. The export recipe fails unless `<tree>` already exists** (v4 L66; script header L15). `tar -x -C` into a missing directory fails with "Cannot open: No such file or directory" (exit 2). **Corrected:** add "`mkdir -p <tree>` first".

**NIT-3. Two `realjd` harnesses need the server, not one** (v4 L65; script header L10-11). `2026-09-24_cascor690_bool_stance_realjd_probe.py` also takes `tree, url` (`:38`), and its docstring says it "Needs a juniper-data server" (`:15`). **Corrected:** "…and both `realjd` harnesses need a live juniper-data."

**NIT-4. The sandbox list (v4 L169-175) is off in both directions.**
- **Listed but ran for me:** `d=…; git -C "$d" rev-parse --short HEAD` printed `5af9d722`, and `env -u X true; echo …` ran.
- **Refused but not listed:**
  - `git -C` into the sibling worktree `juniper-ml/.claude/worktrees/fizzy-hugging-dream`, which v4 L12 sends the reader to ("redirects git to the shared checkout");
  - "git" inside a `for` word list;
  - `bash -c` with computed text.
- **Corrected:** extend the last bullet with "including sibling worktrees under `juniper-ml/.claude/worktrees/` (read files there with `cat`)", and mark the computed `-C` and `env -u` bullets "sometimes".

**NIT-5. Two small gaps.**
- **Untracked, but also pushed.** v4 L139 calls the E2E handoff (`…canopy-e2e-phase9-…-followup-684.md`) "untracked". The same bytes (blob `cc267d2b`) are also pushed on `origin/docs/canopy-e2e-handoff-2026-09-24` (`dd4413e5`, no PR). Say so.
- **A dropped item.** v4 no longer routes the stale-comment NIT that v3 carried. The comment is still on canopy `main` at `test_cascor_service_adapter_gate_coverage.py:49-50` ("in CI, where only the stub client is installed"), and `canopy685-implementation-report.md:69` records it. Restore it in OPEN 2 with "(NIT; can ride any later canopy PR)".

## Verified

1. **The register handoff exists and is untracked.** `…closes-pr-owed.md:6` reads "Superseded if consolidated". It is in neither fizzy-hugging-dream's index nor its HEAD. Its header names session `2fba4397` as "defect reg [24f8d8]", and `:86` says "The canopy E2E session has exited". PID 6555 is that session, still running.
2. **The 00:21:47Z message** from that session says "My lane corrects it together with the surrogatepass marker" and "I consolidate the three once you send your final path and PR number".
3. **`…followup-684.md:53-66`** reserves F-CANOPY-060 ("no owner yet"), 061 (LOW 3) and 062 (LOW 4). They are FIXED-BY `fix/secret-leaks-683-validation`, which is #685's head branch.
4. **`…canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`** holds the `:42` copy (line `:168`) and the `:8381` copy (line `:170`), with "no id reserved" at `:162`. The anchors hold on:
   - canopy `main` `dc5ea02e`, where the files are unchanged since `7ab994e5` (`:8381`, `:8410`, test `:42`);
   - cascor `main` `:4766`;
   - `78e99414:4841`, where the sentence is reworded.
5. **#2089** is open, not armed, at `a2fa3ad8`, and adds the four follow-up-lane README rows. The worktree's README equals `main`'s (blob `8fb8f7ec`).
6. **F3 at `0bee089e`:** `@pytest.mark.unit` at `:205` sits over `TestNonAsciiApiKey` at `:206`. `TestAPIKeyAuth` (`:37`) is unmarked, and `ci.yml:287` holds `-m "unit and not slow"`. A real collection selects 72 of 116 tests, and none from `TestAPIKeyAuth`.
7. **F9:** #689's PR body says "4001 close" and "closes 4001". **F2:** only juniper-data passes `send_pii`.
8. **`pr-683`:** no `push.*` key is set in any scope, and `@{push}` fails with "cannot resolve 'simple' push to a single destination" (git 2.53.0).
9. **Merged table:** `095a2108`'s blob `b4a6164b` equals the one in #2077's squash `6c23fdde` and in `main`. #686 is CLOSED and #687 MERGED.
10. **v4 L16:** 44 of the 63 probes take argv, 5 write under `work/` or `out/`, and none names a scratchpad.
11. **The serve script:**
    - shellcheck 0.11.0 is clean; `-o all` adds only the style warning SC2292.
    - It refused a `.git` directory, a `.git` file, a `.env` and the real checkout, each with exit 2 and nothing created.
    - Served from an `origin/main` export on a free port: `/v1/health` 200, `/metrics` 404, anonymous `/v1/generators` 200. The over-cap POST returned 422 containing "Re-submit with allow_truncation=true". With `allow_truncation` on it returned 201, and the dataset landed in `<scratch>/jdstore`.
    - Under strace there were zero `connect` calls and no writes to the tree. Outside the scratch dir it wrote only `/dev/null` and one CPython temp-file probe in `/tmp`, created and deleted at once.
    - I stopped it with `pkill -f 'uvicorn.*--port 1894[3]'`; the port is free. juniper-data's `git status` (including 7,008 ignored entries) is byte-identical before and after.
12. **Verification commands, all run:**
    - GraphQL: #690, #689 and #440 are open, CLEAN and not armed at `78e99414`, `97341680` and `0bee089e`; #685 is MERGED as `dc5ea02e`.
    - `gh pr list --head …` prints `[]`, and #2089 is OPEN.
    - The fork-drift test prints "Ran 11 tests … OK (skipped=3)", and "OK" with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`.
    - `ls` prints six rows; `df -i /tmp` shows 84%.
13. **Git status:** 92 entries, all untracked, with nothing staged or modified. They are 1 handoff, 19 reports (12 lane plus 7 validation), 63 probes (19/10/13/21), 5 harnesses and 4 ad-hoc scripts. The PR opener collects untracked paths, so it will include the new `.bash` script.

**Changed:** nothing. One departure from read-only: I ran `git fetch` in canopy, cascor, data and my own worktree. That moves only remote-tracking refs and `FETCH_HEAD`, and data's `origin/main` did not move.
