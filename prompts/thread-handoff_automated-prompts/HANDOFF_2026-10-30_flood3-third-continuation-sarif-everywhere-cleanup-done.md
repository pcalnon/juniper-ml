# Handoff: Cursor flood-3 arc, the owner's third continuation. Every call a session could act on is done; what remains is the owner's

**Date**: 2026-10-30 (UTC)

**Arc**: The Cursor flood-3 disposition and its follow-ups. This stretch is the owner's request of 2026-10-30: "continue from handoff: …HANDOFF_2026-10-30_flood3-second-continuation-rows-fixed-owner-calls-open.md", with merge approval for this session's PRs.

**Record**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, cited below as `…FLOOD-3-DISPOSITION.md`. This handoff's PR makes the record's tenth update: the header, §4, §6, §7, §8 and §9.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_flood3-second-continuation-rows-fixed-owner-calls-open.md`, cited below as `HANDOFF_…owner-calls-open.md`.

**Host**: the Linux host.
- **This session:**
  - session `719f66a2` (pid 945136), ListAgents `flood3-second-continuation-rows-fixed-owner-calls-open [a78c34]`;
  - worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/proud-crunching-neumann`.
- **No other session continues this arc.** The duplicate `2fc3f4e1` (`[901969]`) was stopped at 18:46:09Z.
- **Commits** go only through GraphQL `createCommitOnBranch`: `util/open_signed_pr.py` and `util/push_signed_commit.py`.

**Git status**: the worktree's branch, `worktree-proud-crunching-neumann`, is at `d6b29bb5`, behind `origin/main`; no commit is made locally.
- This PR's four files were uploaded through `util/open_signed_pr.py` from the worktree's uncommitted copies.
- Until that PR merges, a worktree cut from `main` lacks this file and the two new tools.
- Check: `git log origin/main --oneline -1 -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_flood3-third-continuation-sarif-everywhere-cleanup-done.md`.

---

## Goal

Nothing is owed unless the owner asks. What remains:
- the owner's calls (Remaining work, item 1);
- one watch item (item 2);
- a cleanup inventory that needs an owner signal (item 3).

## Completed (verified on GitHub, PyPI or the host)

- **The owner's rulings of 2026-10-30**, answered at 18:45Z, after the question dialog had been open since 08:29Z:
  - the duplicate continuation: "Terminate; remove worktrees";
  - the SARIF upload in the other five repositories: "Yes, all five";
  - the two low rows: "Docs + the PASS message";
  - the cleanup inventory: "Yes; keep evidence only".
- **Both watch items of `HANDOFF_…owner-calls-open.md` were checked.**
  - The first scheduled cascor nightly after #735 and #736, run 40994888636 (03:00Z, `d042de23`), matched on every lane. Its JUnit reports read: smoke 153, none failed; slow integration 20, with 5 golden skips; long 1 xfail; slow unit 15.
  - pytest-benchmark is still at 5.3.0, so the cap stays.
- **The duplicate is stopped:** `claude stop 2fc3f4e1`, which `~/.claude/daemon.log` records as settled (killed) at 18:46:09Z. Its five queued messages were never delivered.
- **The PRs, all merged under this session's approval:**

  | PR | Squash | What it did |
  |---|---|---|
  | juniper-data#502 | `8e710d20` | the SARIF rule, with a PR-aware `hashFiles` guard; juniper-data#500's leftovers, docs plus the PASS line of `scripts/check_module_coverage.py` |
  | juniper-canopy#781 | `63fe4b6d` | the SARIF rule; `docs/ci_cd/CICD_MANUAL.md` |
  | juniper-data-client#249 | `e1a9530d` | the SARIF rule, with a PR-aware `hashFiles` guard |
  | juniper-cascor-client#189 | `6393d948` | the SARIF rule |
  | juniper-cascor-worker#220 | `cadb168b` | the SARIF rule |
  | juniper-cascor#737 | `012d4737` | five docs that named the nonexistent `src/tests/pytest.ini`; the README's timeouts; the marker list |
  | this PR | | the record's tenth update; two `util/ad-hoc/` tools |

  Each SARIF PR's run uploaded under the new rule, and code scanning posted `Bandit: success` on its head.
- **The cleanup.** The ledger is `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-10-30/`: `REMOVED.tsv` (its header holds the gates), `MANIFEST.tsv` and `_work/`.
  - **Removed:** ten worktrees and seven local branches.
    - the duplicate's three `fix/flood3-backlog-3` worktrees;
    - the six centralized worktrees of `HANDOFF_…owner-calls-open.md` item 5;
    - `.claude/worktrees/whimsical-leaping-glacier`.
  - **Gates:**
    - holder check: all ten clear, with a positive control that read HELD;
    - merged PRs whose head branches are gone (the duplicate's three had no PR and no commit);
    - every HEAD an ancestor of `origin/main`. Nine were the base commits their worktrees are named for; `whimsical-leaping-glacier`'s was juniper-ml#2378's squash.
  - **Kept**, by `util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py`: 393 files (70 MB). The 18 regenerable entries it skipped (about 480 MB) are listed as `SKIPPED-REGEN` rows. Every copy re-hashed equal, and every `tmp/`'s `diff -rq` is clean.
  - **Not removed, and not in the ruling:**
    - the duplicate's own worktree (item 1.3);
    - the predecessor's own worktree (item 1.4), which this file's first draft missed.
- **Found on the way** (`…FLOOD-3-DISPOSITION.md` §4, §6, §8):
  - **`test_accuracy` is filled:** the recurrence arc's run `20261030T084056Z-0ac7` recorded 0.575 (juniper-ml#2390). juniper-deploy#266 pins cascor 0.13.0.
  - **The cascor primary moved:** a `pull origin` fast-forwarded it to `d042de23` at 18:18:33Z; the actor is unrecorded.
  - **The upload survey, posted on the five SARIF PRs:** every PR head whose upload ran carries `Bandit`: data 102, data-client 132, cascor-client 120, cascor-worker 113. Canopy has 1 of 109; its other 108 heads (10-16 to 10-29) uploaded nothing, which is juniper-canopy#780's failure.
  - **The survey's step-conclusion half is blind.** The jobs API reports a step's conclusion after `continue-on-error`, so cascor's "165 of 165 uploads succeeded" is not established.

## Remaining work

1. **Owner calls.** A session acts on none of these without the owner's word, and on 1.7 not even then.
   1. **Close register row APD-ML-002.** The close condition is met by evidence:
      - the run's state is `/home/pcalnon/.local/state/juniper-experiments/20261030T084056Z-0ac7` (juniper-ml#2390);
      - the procedure is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` § "Closing a row", four touches, since the row has no §3 entry;
      - the recurrence arc's handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled.md` (item 3), carries the same close. It says "the five touches"; the register's rule makes it four for a row with no §3 entry, so do not look for one. The owner rules once, and whichever session acts tells the other.
   2. **`CODECOV_TOKEN` in the Dependabot stores** of juniper-data and juniper-canopy, the only two that upload to Codecov. Only the owner can add it. `python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py` re-reads the stores (GET only); `dependabot=-` means absent.
   3. **The stopped duplicate's own worktree:** `.claude/worktrees/iridescent-sniffing-snail`, HEAD `c77b7be5`, branch `worktree-iridescent-sniffing-snail`. It has been unlocked since about 18:50Z.
      - **Preserve its `tmp/` first**, into `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-<date>/`.
      - **Route A,** `claude rm 2fc3f4e1`: deletes the session record and the worktree, ignored `tmp/` included.
        - Its help says "the branch is kept" only under `--force-remove-worktree`, so check `git branch --list worktree-iridescent-sniffing-snail` afterwards.
        - That flag and `--discard-unpushed` take a value that an earlier `claude rm` printed.
      - **Route B,** the four gates in `REMOVED.tsv`'s header, then `git worktree remove` and `git branch -d worktree-iridescent-sniffing-snail`. The session record survives.
      - **Done when** `git worktree list` no longer shows it.
   4. **The predecessor's own worktree:** `.claude/worktrees/prancy-whistling-knuth`, HEAD `110d5e40`, branch `worktree-prancy-whistling-knuth`, a 1.1 GB `tmp/` (`session/`, `validate-a/`, `-b/`, `-c/`). Its session has ended, and it is unlocked.
      - `HANDOFF_…owner-calls-open.md` item 5 kept it while that session lived, and the 2026-10-30 ruling did not name it.
      - On the owner's signal, preserve its `tmp/` first, then apply the gates. The 2026-10-30 ruling kept evidence only, without regenerable parts; whether that applies here is the owner's call.
   5. **Three open low items, in two rows of `…FLOOD-3-DISPOSITION.md` §4** (the juniper-data row and the new cascor row). A session may fix them on the owner's word.
      - juniper-data's `make coverage` does not run CI's per-file gate (a behaviour change).
      - juniper-data's `.github/workflows/agents-md-touch-up.yml:80` pins `actions/checkout@v7.0.1` by tag. Pinning it also means editing `docs/ci_cd/CICD_REFERENCE.md:256`, which names the exception; the pin table at `:260` already holds the SHA.
      - juniper-cascor's upload comment in `.github/workflows/ci.yml` ("165 of 165 uploads succeeded over 200 runs") and `util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`'s docstring rest on the blind step-conclusion measure. The fix is a comment and a docstring, plus, if wanted, a failure count read from the check run's error annotations.
   6. **Promote claim-backing scripts?** This is carried from `HANDOFF_…owner-calls-open.md`. No list exists: neither ledger marks a script as claim-backing.
      - The candidates: 59 scripts under `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-10-30/` and 3 under `…-2026-10-29/` (`find <ledger> -path '*/_work' -prune -o -type f \( -name '*.py' -o -name '*.bash' -o -name '*.sh' \) -print`).
      - A "yes" means: map each to the record claim it backs, then promote those into their repository's `util/ad-hoc/` by signed PR.
   7. **Host environments**, the owner's own action; never a session's, even on the owner's word.
      - `JuniperCanopy1` holds juniper-observability 0.4.0 and juniper-service-core 0.5.0, below canopy's floors (0.4.1 and 0.7.1). Two local test failures follow.
      - `JuniperCascor1`'s editable install still reports juniper-cascor 0.11.0, so cascor's `test_version_matches_pyproject` fails locally.
2. **Watch: drop the pytest cap.** The cap is `pip install "pytest<9.2"` in cascor's `performance-smoke` job (`.github/workflows/scheduled-tests.yml:294`).
   - **The trigger:** either a pytest-benchmark release that supports pytest 9.2, or a pytest 9.2.x release that restores what pytest-benchmark reads (`'Function' object has no attribute '_nodeid'`). 5.3.0 and 5.2.3 both error at setup on 9.2.0.
   - **The check:** rerun a one-line test that takes the `benchmark` fixture under the new pair. The 10-29 probe lives in `.claude/worktrees/prancy-whistling-knuth/tmp/session/bench-probe/` until item 1.4 removes that worktree.
   - **The fix:** a signed PR. Merging needs the owner's approval in that session. Keep plugin file paths out of workflow comments (Key context).
3. **Cleanup inventory (this pass).** Nothing here is removed; each item needs an owner signal.
   - **The gate for a worktree reset to a squashed PR's head:** HEAD equals the PR's final head (`gh pr view <n> --repo pcalnon/<repo> --json headRefOid`). A squashed head is never an ancestor of `main`, so the `REMOVED.tsv` gate "HEAD an ancestor of `origin/main`" cannot pass for these.
   - **The branches:** delete them with `git branch -d` while the stale `origin/<branch>` ref survives locally. The head branches are already deleted on GitHub, and no prune is configured. After a prune, `-d` refuses, and `-D` needs the same `headRefOid` check first.
   - **This pass's six centralized worktrees**, each reset to its PR's head, clean, with no `tmp/`:
     - `worktrees/juniper-data--fix--flood3-sarif-upload-and-ci-docs--20261030-1347--95163c47` (#502, head `6d092bd9`);
     - `worktrees/juniper-canopy--ci--sarif-upload-fails-on-prs--20261030-1347--18a49c85` (#781, `cfaf588b`);
     - `worktrees/juniper-data-client--ci--sarif-upload-fails-on-prs--20261030-1347--e23540d9` (#249, `8bf0d218`);
     - `worktrees/juniper-cascor-client--ci--sarif-upload-fails-on-prs--20261030-1347--741c8fb9` (#189, `d65b8a38`);
     - `worktrees/juniper-cascor-worker--ci--sarif-upload-fails-on-prs--20261030-1347--ef250661` (#220, `c923a43e`);
     - `worktrees/juniper-cascor--docs--pytest-ini-stale-references--20261030-1347--d042de23` (#737, `6e8b4e89`).
   - **This session's worktree,** `.claude/worktrees/proud-crunching-neumann`.
     - **When:** once this session (`719f66a2`, pid 945136) has ended and its lock is gone.
     - **First:** preserve `tmp/session/`. It holds the nightly's JUnit artifacts, the SARIF survey outputs, the cleanup's working listings (already copied into the ledger's `_work/`), the PR bodies, the `safe_merge` logs and scratch probes.
     - **Then** apply the gates. The branch `worktree-proud-crunching-neumann` is at `d6b29bb5`, an ancestor of `main`.
   - **Keep until the owner says otherwise:**
     - `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/release-cascor-0.13.0/`;
     - `…/tmp/worktree-cleanup-2026-10-26/`, `-27/`, `-29/` and `-30/`;
     - `…/tmp/flood3-deleted-branches.tsv`;
     - 84 `cascor-test-snapshots-*` directories in `…/tmp/`. By date: 49 from 10-26, 24 from 10-27, 7 from 10-28 and 4 from 10-29; none since.

## Key context and traps

- **Merge approval is per session** (memory `feedback_headless_merge_approval_policy.md`). This file cannot carry it.
- **Never attach or resume `2fc3f4e1`.** `claude attach` would resume a session that believes it holds merge approval, with its stale dialog and five undelivered messages.
- **The cascor primary:** never pull, check out or edit it from a session.
  - At 20:02Z nothing listened on 8100, 8200-8202 or 8050, and someone else had fast-forwarded it at 18:18Z.
  - But `util/ad-hoc/2026-10-29_worktree_holder_check.py` read it HELD by four canopy `main.py` processes (pids 2902773, 2913427, 2913613, 2913899), on ports 8052, 8053, 8058 and 8059. They reference it through their environment (`JUNIPER_CANOPY_SNAPSHOT_DIR`) rather than an import.
  - Run `ss -ltnp` and the holder check before relying on its state.
- **juniper-ml#2360** (the `/tmp` arc) is OPEN, CONFLICTING/DIRTY, with auto-merge armed.
  - It shares five files with `main`'s later work: `.github/workflows/ci.yml`, `AGENTS.md`, `CHANGELOG.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` and `docs/REFERENCE.md`.
  - Its re-sync must keep `main`'s side of each. A whole-file re-sync that passes CI would merge a revert unreviewed.
- **Count a step's failures by an effect, never by its API `conclusion`.** That `conclusion` is taken after `continue-on-error` (`…FLOOD-3-DISPOSITION.md` §6). Use the `Bandit` check or the check run's error annotations instead.
- **GitHub served HTTP 502 for some runs' job lists on every attempt within a survey.** The same runs loaded later, so the errors were transient, but they outlasted the survey's retries. juniper-cascor's `util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py` aborts on the first one. juniper-ml's `util/ad-hoc/2026-10-30_bandit_sarif_upload_survey_tolerant.py` takes that file's path as its first argument and tallies such runs `unreadable`.
- **Preservation traps:**
  - The 2026-10-26 blob classifier skips image and PDF suffixes everywhere. Sweep them with `util/ad-hoc/2026-10-29_cleanup_skipped_suffix_sweep.py`, or use `util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py`, which never skips them.
  - In juniper-ml, compare images by LFS oid (`git lfs ls-files -l`), never by blob id.
  - `git worktree remove` without `--force` is no dirty test when a worktree's unique files are all ignored: git deletes ignored files without asking.
  - Run a whole-tree `diff -rq` against every preserved copy.
- **A pip torch on this host needs `env -u LD_LIBRARY_PATH -u LIBTORCH`.** Without it, rust_mudgeon's libtorch loads first.
- **cascor's `Documentation Links` lint reads a `.py` path in a workflow comment as a script reference.** Pre-commit does not run it.
- **Release dates are UTC.** No release is pending in this arc.
- **Worktree isolation refuses some shell shapes**, and each refusal names the shape:
  - `git -C` into this repository's shared checkout or its sibling `.claude/worktrees/`, or a `cd` there before git;
  - variables in a git or `sed` argument, `$(…)` or `${PIPESTATUS…}` around git or gh, loops, and `xargs -a`;
  - braces with commas inside a quoted argument (a GraphQL query), and `sudo`.

  Write and Edit into the primary checkout are refused too; Bash may write its `tmp/`.
- **`util/safe_merge.py` and `util/wait_for_checks.py` take a bare `--repo` name.** Read the `MERGED` line, not the exit status.

## Verification

Run these first. On any mismatch, stop, re-probe and report to the owner rather than act. An earlier draft of this file shipped an expected output that the host had already falsified.

```bash
gh pr view 502 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'               # MERGED 8e710d20
gh pr view 781 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'             # MERGED 63fe4b6d
gh pr view 249 --repo pcalnon/juniper-data-client --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'        # MERGED e1a9530d
gh pr view 189 --repo pcalnon/juniper-cascor-client --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'      # MERGED 6393d948
gh pr view 220 --repo pcalnon/juniper-cascor-worker --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'      # MERGED cadb168b
gh pr view 737 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'             # MERGED 012d4737
python3 -I util/ad-hoc/2026-10-29_sarif_upload_continue_on_error_census.py /home/pcalnon/Development/python/Juniper   # six ci.yml rows read ${{ github.event_name != 'pull_request' }}; deploy's security-scan.yml: absent. It runs `git fetch origin` in every primary (remote-tracking refs only)
python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py                                                       # dependabot=- in all nine rows until the owner acts (item 1.2)
/home/pcalnon/.local/bin/claude agents --json --all | python3 -I -c 'import json,sys; [print(a.get("id"), a.get("state")) for a in json.load(sys.stdin) if a.get("id") == "2fc3f4e1"]'   # "2fc3f4e1 stopped" (no line after `claude rm`)
git worktree list --porcelain | grep -A3 -E 'iridescent-sniffing-snail$|prancy-whistling-knuth$'   # both listed, with no `locked` line, until items 1.3 and 1.4
curl -s https://pypi.org/pypi/pytest-benchmark/json | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])'   # 5.3.0 until item 2 fires
```

## Residue: the remaining work of `HANDOFF_…owner-calls-open.md`, item by item

1. **Owner calls:**
   - 1.0, the duplicate: stopped, and its three worktrees removed.
   - 1.1, Codecov in the Dependabot stores: still open (item 1.2 here).
   - 1.2, SARIF elsewhere: done, in five PRs.
   - 1.3, the duplicate's worktrees: removed. Its own harness worktree is item 1.3 here.
   - 1.4, APD-ML-002: `test_accuracy` filled by another session, so only the close remains (item 1.1 here).
   - 1.5, host environments: unchanged (item 1.7 here).
2. **The pytest cap:** still open (item 2 here).
3. **The nightly watch:** done, and matched.
4. **The §4 low rows:** fixed (#502, #737), apart from two juniper-data#500 items the ruling did not cover (item 1.5 here).
5. **The cleanup inventory:**
   - Its removal targets are removed, with their evidence kept.
   - Its "This session's worktree", `prancy-whistling-knuth`, is now item 1.4, its session having ended.
   - Its "Keep" list and its promotion question are items 3 and 1.6 here.

**Its traps** are all carried under Key context, with the GraphQL, `sudo`, classifier, `--force`, torch, lint, UTC and #2360 details restored after the review. The one no longer live is the live duplicate.

## Documents created or modified

- **This file's PR:**
  - this file (new);
  - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`;
  - new: `util/ad-hoc/2026-10-30_worktree_cleanup_keep_evidence.py` and `util/ad-hoc/2026-10-30_bandit_sarif_upload_survey_tolerant.py`.
- **Other PRs:**
  - juniper-data#502: `.github/workflows/ci.yml`, `scripts/check_module_coverage.py`, `docs/REFERENCE.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/ci_cd/CICD_REFERENCE.md`, `docs/ci_cd/CICD_QUICK_START.md`, `CHANGELOG.md`;
  - juniper-canopy#781: `.github/workflows/ci.yml`, `docs/ci_cd/CICD_MANUAL.md`, `CHANGELOG.md`;
  - juniper-data-client#249, juniper-cascor-client#189 and juniper-cascor-worker#220: `.github/workflows/ci.yml` and `CHANGELOG.md` each;
  - juniper-cascor#737: `docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `src/tests/README.md`, `CHANGELOG.md`.
- **Comments:** one survey comment on each of the five SARIF PRs.
- **Unversioned auto-memory** (`/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`), which every concurrent session reads:
  - `reference_claude_bg_daemon_forensics.md`: how to stop a background session; never attach a stopped duplicate; the lock line vanishes on its own;
  - `reference_worktree_sweep_hazards_2026-09-12.md`: LFS images in a blob comparison; the empty-directory `diff -rq` line;
  - `reference_ci_merge_mechanics_hub.md`: job-list HTTP 502s and the tolerant survey;
  - `reference_verification_discipline_hub.md`: a step's API `conclusion` is taken after `continue-on-error`.
- **Unversioned:** `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-10-30/`: `MANIFEST.tsv`, `REMOVED.tsv`, `_work/` and the preserved files.
- **Referenced:**
  - `HANDOFF_…owner-calls-open.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled.md` (juniper-ml#2390);
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
