# Handoff: flood-4 session 4 — seven fixes landed; validations, two carriers and the owner's open decisions pending

**Date**: 2026-11-11 (written 2026-11-12 00:25Z UTC)

**Arc**: the Cursor flood-4 disposition, session 4. It started as `polymorphic-knitting-pie` and ran in `humming-stargazing-papert` via EnterWorktree. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md` (session 3's handoff; untracked in this worktree).

**Host**: the Linux host.

**Why the session stopped**: the account's **weekly API limit** was hit around 16:15Z on 2026-11-09. It "resets Nov 11, 9pm (America/Chicago)", which is 2026-11-12 03:00Z. Five background agents died mid-task (listed under Goal), and their work is on disk only. The owner then rejected a batched question (decisions D1–D4 below) because they wanted to **clarify** those questions, and asked for this handoff.

---

## Git status

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert`. HEAD is `734aab58` (fast-forwarded in session 4); `origin/main` was `68f9ebcd` at the last fetch.
- **Untracked there: 126 files.**
  - 39 `util/ad-hoc/2026-11-08_flood4r2_*.py`;
  - 86 `util/ad-hoc/2026-11-09_flood4r2_*.py`. These include session 4's six landing helpers: `…_land_findings_to_edits.py`, `…_land_snapshot.py`, `…_land_gitleaks.py`, `…_land_open_pr.py`, `…_land_m4m7_rebuild.py` and `2026-11-08_flood4r2_fix_apply_edits.py`'s companion specs;
  - session 3's handoff;
  - this handoff;
  - `tmp/` is ignored.
- **The running log** is `tmp/flood4/STATE.txt`; read its "== SESSION 4" section first.
- **The landing evidence** is in `tmp/flood4/session4/land/<item>/`: freeze, scans, texts, safe_merge logs and close logs.
- **The primary checkout** is on the owner's branch. Do not touch it.

---

## Landed in session 4 (all squash-merged by `util/safe_merge.py`, each signed and frozen, scanned against `main`'s copies with a planted-token control)

| Item | PR | Squash | Merged (UTC, 2026-11-09) | Drafts closed |
|---|---|---|---|---|
| M-3 service-core paused-fit wedge | juniper-ml#2531 | `7b3b91b7` | 11:22:25Z | — |
| canopy-tests carrier | juniper-canopy#807 | `d2cc7cd1` | 14:59:18Z | #800, #801 |
| M-4/M-7 service-core resume losses | juniper-ml#2534 | `f85fbc8b` | 15:13:37Z | — |
| canopy-docs carrier | juniper-canopy#808 | `609a26a3` | 15:29:00Z | #798, #799 (canopy round 2 complete) |
| Ruling 17: data's 44 unrun tests | juniper-data#529 | `97138bd6` | 15:43:01Z | — |
| N-1 cascor paused-fit wedge | juniper-cascor#753 | `96cf891b` | 15:43:23Z | — |
| M-1 data gitleaks PR-commit scan | juniper-data#530 | `05c1f446` | 16:03:45Z | — |

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md (in the humming-stargazing-papert worktree, uncommitted).
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert).
Run the Verification block first; if an invariant fails, stop, re-derive it from GitHub, and report.

FIRST:
(1) Ask the owner for THIS session's merge approval (a handoff cannot carry it).
(2) The owner asked to CLARIFY decisions D1-D4 before answering. Ask what they want clarified, then present D1-D9 (this
    file's "Open decisions") with their context.
(3) Confirm the weekly API limit has reset (it reset 2026-11-12 03:00Z). Agents died on it once; launch a few, not ten.

1. Re-run the five work items the limit killed, with FRESH agents. A new session cannot SendMessage the old ones. Point
   each at its partial work:
   a. N-2 (service-core stop-then-start; built in .claude/worktrees/agent-a001ff6d68bf06099, tmp/flood4-fix/n2/):
      two lenses, code and claims. The dead ones' partial work is in .claude/worktrees/agent-a69d8c2809c3b4840 (code)
      and agent-af6b55f5ab45c409b (claims). Then fix-up, then land (D7 applies).
   b. N-4 (service-core failed-socket close; built in agent-ab006c2d3dc68fe8c, tmp/flood4-fix/n4/):
      - the claims lens is done: tmp/flood4r2-val/n4-claims-lens/findings.json, 0/0/5;
      - re-run the code lens (the dead one's partial work is in agent-ad9caecdbf851e588);
      - fix-up, then land.
      N-2 and N-4 both bump REFERENCE 0.6.66 -> 0.6.67 (N-4 also cheatsheet 1.0.67). The second to land re-derives from
      its stamps.json, the way util/ad-hoc/2026-11-09_flood4r2_land_m4m7_rebuild.py did for #2534.
   c. ml-code round 3. The dead fix-up's partial work is in agent-a82c2300eca19f450, tmp/flood4r2/ml-code/r3/; the r2
      carrier is agent-a675564a3fa0194a8.
      - Apply tmp/flood4r2-val/ml-code-port-lens/findings.json: F1, the REGRESSION (a quadratic scan makes a 25.8 KB
        `python3 -c` word take 9.5 s, against the hook's 10 s timeout: add a fail-closed budget); F2, the tests; F5 and
        F6, text and stamps.
      - Apply tmp/flood4r2-val/ml-code-claims-lens/findings.json: 1 BLOCKER, 1 MAJOR, 9 MINOR.
      - NOT F3/F4: they wait for D1.
      - Then a final check, then land. Tell the owner to reinstall guard 1.3.0 after the merge.
   d. Ruling 17, cascor stop-then-start. The builder died while writing the PR body, in
      worktrees/juniper-cascor--fix--stop-then-start-race--20261109-0944--96cf891b, tmp/flood4-fix/r17-cascor-stop-start/.
      Finish it, validate it with two lenses, and land it after N-3.

2. Land, in this order within each repo (a strict ruleset applies to each). For each item:
   - apply the last check's fixes;
   - freeze on the CURRENT main with util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (three-way the CHANGELOGs;
     --prebuilt for files rebuilt by hand);
   - scan with util/ad-hoc/2026-11-09_flood4r2_land_gitleaks.py --baseline <freeze>/main;
   - push with util/ad-hoc/2026-11-09_flood4r2_land_open_pr.py;
   - run util/safe_merge.py --execute and read its MERGED line;
   - close the item's drafts with util/ad-hoc/2026-11-07_flood4_close_carried.py: a dry run first, then --execute.
   juniper-ml: N-2 and N-4 (either order); ml-code; ml-propose (orchestrator decision in session 4: IMMEDIATELY BEFORE
     ml-tests, because #2507's tests fail any release proposal until propose.py rewrites the four REFERENCE sites; it
     needs a final check first: agent-a89a45162cee4b2e8, tmp/flood4r2/ml-propose/r2/); ml-tests (built in
     agent-a67685d30bfa19727, tmp/flood4r2/ml-tests/: 18 drafts; validate the post-ml-code state in its
     overlay/post_mlcode/ with two lenses; read its manifest's open_questions); ml-docs (build it after ml-code); then
     ruling 18's escape-gap PR (plus F3/F4 per D1).
   juniper-data:
     - data-tests, then data-docs, then data-code (tmp/flood4r2-fix/<carrier>/; rebuild on data main 05c1f446 or later).
       M-1 changed CICD_MANUAL.md and CICD_REFERENCE.md, which data-docs also edits: merge them three-way and re-derive
       their stamps. Apply data-code/apply_after_data_docs.json on the main that holds data-docs.
     - Then ruling 10's port of M-1 to the seven other repos, once a later data PR's security job has run the new scan
       green LIVE. A port is not a copy: see the record's ruling 10.
   juniper-cascor:
     - N-3. Its round-3 fix-up applies tmp/flood4r2-val/n3-r2-claims-lens/findings.json (BLOCKER F1: the "service-core
       still has both losses / not yet merged" texts are false since #2534; MAJOR F2: observability.py's ruling-11
       citation) and n3-r2-code-lens F2/F3. Worktree: juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c,
       tmp/flood4-fix/n3-r2/.
     - Rebuild it on cascor main 96cf891b or later. The cheatsheet MERGES SILENTLY keeping 1.0.9: set it to main+1 by
       hand. API_SCHEMAS conflicts: take main+1.
     - Then r17 cascor stop-then-start.
   juniper-canopy:
     - the r17 network guard: apply tmp/flood4r2-val/r17-canopy-network-guard/findings.json, whose MAJOR F1 (a refused
       connect on another thread fails the running test) has a verified 3-edit fix; worktree
       juniper-canopy--test--unit-lane-network-guard--20261109-0827--b4b01904;
     - the r17 lockfile failure print: worktree juniper-canopy--ci--lockfile-graphql-failure-print--20261109-0930--609a26a3;
       validate it first (one combined lens is enough), then land it.

3. Round 3: #2404 and #2406, individually.
4. Ruling 7 cleanup. FIRST archive, out of tmp/:
   - the evidence the record cites (its §8 "The evidence in tmp/");
   - session 3's tmp/flood4/val-record/v5 and v6, round2-fixes/, push/ml-record-r2/, tmp/flood4r2-val/ and
     tmp/flood4r2-fix/;
   - session 4's tmp/flood4/session4/.
   Commit the util/ad-hoc/2026-11-0[89]_flood4r2_*.py helpers as provenance, after fixing G-PATH and G-TMP in the five
   jd-gitleaks ones. Then remove the merged items' worktrees, checking each tmp/ first. Never use
   util/remove_stale_worktrees.bash. curious-plotting-hummingbird is DO NOT SWEEP.
5. The record-update PR: rulings 15-18; session 4's orchestrator decisions; the answers to D1-D9; round 2's table and
   outcome; every fix PR (the seven above and the rest); and the new findings and traps (STATE.txt, session 4).
6. Archive the next handoff.
```

---

## Open decisions (the owner's; none answered — the owner asked to clarify D1–D4 first)

| # | Decision | Context | Options (recommended first) |
|---|---|---|---|
| D1 | Where do guard bypasses **F3/F4** go? | The ml-code port lens found both. They are already on `main`, so neither is an ml-code regression. F3: an unbalanced `{` inside `$(...)` or backticks in a brace list stops `util/claude_agent_guard.py` expanding the group (bash skips those bodies). F4: an empty `$(:)` or `${x}` joins a protected name together after `X/..`. Ruling 18 already gives the escape gap (`cat ~/.ss{h,b\}c}/config`) its own PR right after ml-code, and that PR reworks how the guard reads a word's structure. Evidence: `tmp/flood4r2-val/ml-code-port-lens/findings.json`. | **Fold into ruling 18's PR** (one word-structure PR, one validation); own PR each; carry in ml-code (delays ml-code and the three ml carriers behind it). |
| D2 | juniper-data: **178 more tests in 9 files** run in no CI lane | #529's builder found them. They include `test_phase1d_security.py` (35) and `test_local_fs_path_traversal.py` (28). Each sits in an unmarked class or module, or a class marked only `api`/`performance`. The validator re-derived the census. Evidence: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--test-security-unit-marks--20261109-0827--272ff615/tmp/flood4-fix/r17-data-unit-marks/manifest.json` `open_questions`. | **Follow-up PR now** (same method as #529; fix any test that fails once it runs); record only. |
| D3 | M-1's **force-push gap**: open a GitHub issue? | Commits that a force-push removed from a PR are never scanned. The gap is pre-existing, the action has it too, and #530 documents it as a limit (round-1 validator A's A-02). An issue is a write outside PR operations. | **Open one juniper-data issue**; record only. |
| D4 | N-4's **adjacent gaps** | (a) With N-4, an unserialisable broadcast closes EVERY socket 1011; `main` silently stranded them all. That is better than `main`, but cascor serialises first. (b) `/ws/control` has the same crash after a server close that N-4 fixes for `/ws/training`. | **One follow-up service-core PR after N-4**; fold into N-4 (another validation round); record only. |
| D5 | **lockfile-update.yml's unreachable failure print** exists in five sibling repos | The ruling-17 canopy builder found the same defect on `main` in juniper-data, juniper-cascor, juniper-data-client, juniper-cascor-client and juniper-cascor-worker. Ruling 17 covered canopy only. | **Port the canopy fix after it lands** (one PR per repo, as ruling 10 ports M-1); record only. |
| D6 | canopy's **:8100 unit-lane connects** | The ruling-17 guard fixed the :8050 and :8200 connects and deferred :8100: 124 tests in 38 files, through the app's own startup and readiness probes. The guard does not cover 8100. | **A follow-up PR** that mocks the data client at app startup for the unit lane and adds 8100 to the guard; record only. |
| D7 | **N-2's design** changes behaviour | A start right after a stop now gets a **409** until the old `fit` unwinds. The validators died before reporting, so this is pending their verdict. No consumer (canopy, cascor, data, recurrence) imports service-core's lifecycle manager or routes. The builder notes that a stop followed at once by a snapshot load has the same shape; it is not probed. | **Accept the 409** (refuse until the old thread ends); prefer a bounded wait or per-run fencing (the builder argues both are worse: waiting blocks the event loop, fencing still runs two `fit`s on one model). |
| D8 | **Guard suites missing from host-tooling-macos** | Found by the ml-tests builder: the guard's suites are not wired into the macOS host-tooling workflow. | Wire them in the ml-tests carrier (orchestrator may decide) or as a follow-up. |
| D9 | canopy `docs/ci_cd/CICD_MANUAL.md:796` | It says the workflow comment claims the `[dependabot skip]` tag keeps Dependabot from rebasing, but `lockfile-update.yml:176-177` now says the opposite. The text is pre-existing. Source: `tmp/flood4r2-fix/canopy-docs/manifest.json` `open_questions`. | A one-line follow-up; record only. |

**Orchestrator decisions taken in session 4** (record them; the owner may overrule):
- ml-propose lands immediately **before** ml-tests.
- M-1's R3-02 fix was kept as code: the `remerge` git filter. The quick check recommended KEEP: its output is byte-identical to git's and it fails closed.
- The canopy guard covers 8050–8059, 8200–8202 and 8210–8211, not just :8050.
- canopy#807's py3.13 failure (`test_x7_sites_outside_main_gate.py::…test_relay_cascade_add_does_not_block_the_loop`, a 0.875 s loop stall) was treated as a flake and rerun. It ran on the same runner image as main's green run, and the rerun passed.

## The owner's rulings

- Session 4's opening message: "approval granted for merging and related PR operations". It is per session and does not carry.
- **Ruling 18** (AskUserQuestion, label verbatim). The question was where the escape gap `cat ~/.ss{h,b\}c}/config` should be fixed. Answer: "Own PR, right after (Recommended)". ml-code lands at its current scope, and one quote/escape-aware brace-expansion PR follows it.
- Rulings 1–14 are in the record's §8. Rulings 15–17 are in session 3's handoff. The record (#2530) covers 1–14 only.

## Traps (new this session)

- **CodeQL flags a bare `await <name>` statement** as "Statement has no effect" (`py/ineffectual-statement`). It was alert 1088 on #2534. Its review thread blocked the merge with every check green. Write `await asyncio.gather(x)`. The prescreen does not model this, so grep `^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$`. `tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt` lists it with the other three patterns.
- **safe_merge may update a BEHIND branch itself, then refuse** with "head moved during the wait". GitHub's merge commit moves the head. Re-run it; #2534 merged on the third run.
- **gitleaks `dir` on a snapshot flags content already on `main`.** For example, canopy's `CHANGELOG.md:1381` holds a fake `CANOPY_API_KEY` example, which the insertion moved down. Scan `main`'s copies of the same paths as a baseline and key findings by (path, rule, line text). The helper does this now.
- **Worktree-isolated session refusals:**
  - `git -C <another juniper-ml worktree>` is refused, even through a symlink under your own `tmp/`;
  - sibling-repo worktrees are fine;
  - inline heredoc Python is refused, so use script files;
  - `$(...)` in a command whose text contains "gitleaks" is refused.
- **A weekly API limit kills every running agent at once.** Their results never reach `tmp/flood4r2-val/`. A new session cannot SendMessage them, so relaunch fresh agents pointed at the partial worktrees.
- **AskUserQuestion can block for hours.** Session 4's first question waited about 2.5 h, and STATE times before 14:59Z were estimates that ran ahead. Use `date -u`, and ask while agents run.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert
git fetch -q origin; git log -1 --format=%h origin/main
gh pr view 2531 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'      # MERGED 7b3b91b7
gh pr view 2534 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'      # MERGED f85fbc8b
gh pr view 807 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED d2cc7cd1
gh pr view 808 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 609a26a3
gh pr view 529 --repo pcalnon/juniper-data --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'     # MERGED 97138bd6
gh pr view 530 --repo pcalnon/juniper-data --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'     # MERGED 05c1f446
gh pr view 753 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 96cf891b
gh pr list --repo pcalnon/juniper-canopy --state open --json author --jq '[.[]|select(.author.login=="app/cursor")]|length'   # 0
gh pr list --repo pcalnon/juniper-data --state open --json number,isDraft --jq '[.[]|select(.isDraft)|.number]'   # [520,521,522,523,524] (data round 2)
ls util/ad-hoc/ | grep -c '^2026-11-0[89]_flood4r2_'          # 125
ls tmp/flood4r2-val/n4-claims-lens/findings.json tmp/flood4r2-val/n3-r2-code-lens/findings.json tmp/flood4r2-val/r17-canopy-network-guard/findings.json
tail -40 tmp/flood4/STATE.txt
```

## Documents created or modified in session 4

- **Merged on GitHub** (each PR's own files; see its body):
  - juniper-ml#2531 (12 files) and #2534 (10 files plus a CodeQL fix commit). Both change `docs/REFERENCE.md` (now 0.6.66), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.66), `CHANGELOG.md` and `juniper-service-core/CHANGELOG.md`.
  - juniper-canopy#807 (4 files) and #808 (5 files).
  - juniper-data#529 (2 files) and #530 (7 files).
  - juniper-cascor#753 (11 files).
  - Comments posted when closing juniper-canopy #798, #799, #800 and #801.
- **Uncommitted, in this worktree:**
  - this handoff;
  - `tmp/flood4/STATE.txt` (session 4 section);
  - `tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt`;
  - `tmp/flood4/session4/land/*` (per-item freeze, scans, texts and logs);
  - the session-4 helpers `util/ad-hoc/2026-11-09_flood4r2_land_{findings_to_edits,snapshot,gitleaks,open_pr,m4m7_rebuild}.py`, plus about 80 agents' `2026-11-09_flood4r2_*` helpers.
- **Carrier and validator worktrees** (all uncommitted) are under `/home/pcalnon/Development/python/Juniper/worktrees/` and `juniper-ml/.claude/worktrees/agent-*`, as named in Goal. Validators' scratch worktrees named `*--val--*` are to be cleaned up in step 4.
- **Outside any repo:** auto-memory `reference_codeql_unused_global_cascor.md` gained the bare-`await` CodeQL pattern. The other new traps above are not in auto-memory yet.
