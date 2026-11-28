# Handoff: run_tests rollout -- the two conversions are open (data-client#275, recurrence#242) and held on the ci-tools 0.10.0 Release; then re-run, merge, and the seven

**Date**: 2026-11-28 (written about 09:50Z)
**From**: session 37a87570, in worktree `juniper-ml/.claude/worktrees/happy-forging-scone`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-27_run-tests-rollout-ci-tools-0-10-0-proposal-and-notes-landed-release-cut-next.md`.
Its eight verification commands ran at 08:15Z and every result was the one it predicted: no Release yet, PyPI at 0.9.1.
Its traps still stand.
**Memory**: `project_run_tests_rollout_2026-11-24.md`
**The plan**: § 4.3 of the proposal, `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md`.
Steps 1 and 2 are done. Step 3, the Release, is still the Overtoad's. Step 4 is built, proven and open. Step 5 remains.

---

## Goal

Continue § 4.3 of `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md`:

1. Once the Overtoad has cut the `juniper-ci-tools-v0.10.0` Release and approved its `pypi` gate, run
   `util/ad-hoc/2026-11-28_verify_ci_tools_0_10_0_published_wheel.py`.
2. Re-run the two failed CI runs and merge juniper-data-client#275 and juniper-recurrence#242.
3. Convert the seven other repos (§ 4.3 step 5).

**Merge approval does not carry over.** At about 08:59Z the Overtoad granted session 37a87570 "commit, push, PR, and
merge changes. approval granted for this work arc". It covers merges, not the Release cut, which this arc's rulings
make a deploy needing its own approval. Ask before merging anything.

## Completed (this session)

- **juniper-ml#2693 MERGED** at 09:17:40Z as `87285b19` (by the armed net, required checks green; Post-Merge Main Verification passed): three `util/ad-hoc/` scripts (signed `f181e77f`).
  - `2026-11-28_verify_ci_tools_0_10_0_published_wheel.py` checks what PyPI serves:
    - PyPI's and TestPyPI's wheels are one artifact (sha256);
    - METADATA;
    - every module is byte-identical to the Release target `7e485e9a`;
    - under `python -I` in a fresh venv: `__version__`, `run_tests.ENGINE_VERSION` and `run_tests.__all__`.
    - Its control run against 0.9.1 fails where it must, and caught 0.9.1's known double build: PyPI `1dc8e01e…`
      and TestPyPI `ade363e8…`.
  - `2026-11-28_run_tests_conversion_mutation_check.py`: 14 mutants, 14 killed.
  - `2026-11-28_run_tests_conversion_help_text_check.py`: the thin specs carry the old copies' `_DESCRIPTION` and
    `_EPILOG` byte for byte, and so does data-client's `OPT_IN` (recurrence has none).
- **juniper-data-client#275**, OPEN (branch `refactor/run-tests-thin-spec`, signed `6cb02bf8`):
  - `util/run_tests.py` goes from 2,533 to 140 lines.
  - The `[test]` extra gains `juniper-ci-tools>=0.10.0,<0.11.0`. Every job that collects `tests/` installs `.[test]`,
    and `tests/test_run_tests.py` loads the runner.
  - `ci.yml`'s per-file gate and `dependency-docs` reinstall ci-tools after `.[test]`, so both move to the same range.
    Otherwise each would downgrade the engine to 0.9.1, and dependency-docs would record that
    (`pip list --format=freeze`).
  - Tests go from 62 to 18. The commit carries a 71-symbol `Allow-Symbol-Loss:` trailer, covering class, func and
    method only; the 14 const and import entries stay WARN.
  - `docs/REFERENCE.md` is now 0.5.6, with a `CHANGELOG.md` `Changed` entry.
- **juniper-recurrence#242**, OPEN (branch `refactor/run-tests-thin-spec`, signed `8a68f344`):
  - `util/run_tests.py` goes from 2,229 to 138 lines, and tests go from 49 to 12.
  - `ci-tooling.yml` installs the engine.
  - **A defect the conversion would have introduced, fixed in it:**
    - The unittest lane's requirements MERGE the "Install…" steps of every job that runs a suite.
    - `sequence-safety.yml`'s job runs one, with `<0.10.0`. The lane's requirements would have been unsatisfiable
      together: a preflight WARN on every run, whose suggested install downgrades the engine.
    - The fix widens the sequence-safety and main-verify ceilings to `<0.11.0`. The screens are byte-identical in
      0.9.1 and 0.10.0.
    - `EngineTest` pins the fix.
  - AGENTS.md's edits are length-neutral (19,972 of 20,000 characters).
- **Proof, both repos**, with ci-tools 0.10.0 built from `main`'s tree (`git diff 7e485e9a origin/main --
  juniper-ci-tools/` is empty):
  - Every `--dry-run` is identical to `main`'s copy.
  - The other differences are exactly the 11-26 prototype's: 16 distinct lines for data-client and 26 for
    recurrence.
  - The pin edits alone move only the preflight counts.
  - `--list --changed` selects the same jobs.
  - Local `all`: data-client passed in 1m00s (682 passed, both gates); recurrence's 7 jobs passed in 1m06s.
  - Sequence Safety probe and `pre-commit`: pass in both. The CodeQL prescreen predicts 0 alerts.
- **CI on both PRs is red ONLY where the pin is installed:** `No matching distribution found for
  juniper-ci-tools<0.11.0,>=0.10.0`.
  - data-client: 10 failing checks, the Quality Gate included. 12 passed.
  - recurrence: only `Local test runner suite` failed. 15 passed.
  - Neither PR has a review thread or a Cursor draft.
- The Overtoad was notified by push at about 08:50Z that the Release is the blocker.

## Remaining work

### 1. The Release (the Overtoad's), then the wheel

- **For the Overtoad only: a session must not run this.** The Release fires an irreversible TestPyPI upload before
  any human gate (the `testpypi` environment has no reviewer). The command is unchanged from the predecessor
  handoff, from the juniper-ml primary:
  ```bash
  cd ~/Development/python/Juniper/juniper-ml && git fetch origin
  git show origin/main:notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md > tmp/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md
  gh release create juniper-ci-tools-v0.10.0 --repo pcalnon/juniper-ml --target 7e485e9ab990662436dc9d1126ca94d64b995836 --title "juniper-ci-tools v0.10.0" --notes-file tmp/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md --latest=false
  ```
- It fires `publish-ci-tools.yml`, which waits at the `pypi` gate. A waiting gate can end at day 30
  (`project_pypi_publish_workflow_dual_gate.md`), so state both dates when handing one over.
- Then verify the wheel.
  - The script landed in #2693 (`87285b19`), and the juniper-ml primary's local `main` predates it. So run it from a
    checkout at `origin/main` or later, such as your own session's juniper-ml worktree cut from `origin/main`.
  - The command:
    `python3 util/ad-hoc/2026-11-28_verify_ci_tools_0_10_0_published_wheel.py --work tmp/<new dir> --python /usr/bin/python3.14`.
  - Every check must PASS. The CDN can lag a few minutes.

### 2. Re-run, then merge

- `gh run rerun 46128744416 --failed -R pcalnon/juniper-data-client`: the CI/CD Pipeline run of `6cb02bf8`.
- `gh run rerun 46128761521 --failed -R pcalnon/juniper-recurrence`: the CI — repo tooling run of `8a68f344`.
- Both PRs' bodies say what is pending and keep the post-release test-plan box unticked.
  - Update them through the API (`gh pr edit` is broken in gh 2.46): `gh api -X PATCH
    repos/pcalnon/<repo>/pulls/<n> -F body=@<file>`.
  - Before ticking the post-release box, re-run each repo's runner suite against the published wheel, not a local
    build:
    - data-client: a fresh venv with `pip install -e ".[test]"`;
    - recurrence: `pip install "juniper-ci-tools>=0.10.0,<0.11.0"` into an overlay venv over `JuniperCascor1`, as in
      the traps.
    - Then tick it, and replace the "not published yet" bullet with the publish time. Tick "CI green" when it is.
- Merge each with `python3 -u util/safe_merge.py --pr <n> --repo <repo> --execute`, and read its MERGED line.
  - All three repos squash with `COMMIT_OR_PR_TITLE` / `COMMIT_MESSAGES`, so a one-commit PR's squash carries its
    message. For data-client#275 that includes the 71-symbol waiver, which `main-verify.yml` re-reads after the
    merge.
    - GitHub moves the `Co-Authored-By:` trailer into a final paragraph of its own (#2693's squash did).
    - That is harmless: the screens match `Allow-Symbol-Loss:` anywhere in the message (`re.MULTILINE`, in 0.9.1 and
      0.10.0 alike).
  - If an update-branch merge commit joins data-client#275, arm GitHub's net with the commit's own message first,
    so the squash keeps the waiver. `util/safe_merge.py` then merges with the stored text: ml#2656 (`8aa58b08`)
    made it pass the net's stored headline and body.
    - Memory `reference_squash_body_excludes_merge_commits.md` says why. Its 11-14 "do not run safe_merge" advice
      predates ml#2656 and is marked superseded.
    - Arming `--auto` on a PR that is already green merges it on the spot, so arming is itself a merge: do it only
      under a fresh approval.
    - A `safe_merge` refusal disarms the net (`disarm_auto_merge`), so re-arm after one.
    ```bash
    gh pr merge 275 -R pcalnon/juniper-data-client --squash --auto --match-head-commit <the PR's head sha> \
      --subject "refactor(util): run_tests.py is a thin spec over juniper_ci_tools.run_tests (juniper-ci-tools 0.10) (#275)" \
      --body-file ~/Development/python/Juniper/juniper-ml/tmp/run-tests-convert--happy-forging-scone/dc_commit_body.txt
    ```
- After each merge:
  - check Post-Merge Main Verification on the merge commit;
  - remove its worktree with `python3 util/ad-hoc/2026-11-25_run_tests_rollout_sibling_worktree.py remove --path
    <worktree> --merged-into main`. That command refuses a worktree whose `tmp/` is not empty; both are empty now.
    The worktrees are under `Juniper/worktrees/`, named
    `juniper-{data-client,recurrence}--refactor--run-tests-thin-spec--20261128-0217--*`.

### 3. Then

- The seven, in the 2026-11-24 order. Section 2.3 of
  `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md` says what cascor, canopy and
  deploy need from the engine first. **In each repo, check every job that runs a `python3 -m unittest` suite.** If
  its install pins ci-tools below 0.10.0, widen it in the conversion PR (recurrence's defect above). And widen every
  later reinstall in a job that installs the engine (data-client's).
- `MEMORY.md` is 23,154 bytes (22.6 KiB) against its 20 KB target (`feedback_memory_index_target_is_20kb.md`). It
  needs a pass that retires entries. The longest lines belong to other active arcs: coordinate rather than rewrite
  them.

## Key context and traps (this session)

- **`open_signed_pr.py` hit GraphQL HTTP 499 AFTER it had created the branch**: the branch sat at `main` with no
  commit and no PR.
  - Recover with `util/push_signed_commit.py --expected-head <main sha>`, then `gh pr create`.
  - Never delete the branch and re-run: the branch check refuses a re-run anyway, and you lose nothing by pushing.
  - The data-client upload was about 243 KB raw, so this was not a size limit; the same call then worked for
    recurrence.
- **gh 2.46 has no `gh pr checks --json`.** Read `repos/<o>/<r>/commits/<sha>/check-runs` instead.
- **A Sequence Safety probe from a worktree BEHIND `main` reports `main`'s newer commits as reverse diffs**: here,
  24 phantom docs deletions. Run `git merge --ff-only origin/main` first, when the worktree holds only untracked
  files.
  - Git refuses that fast-forward when it would overwrite an untracked file, even an identical copy.
  - So check the copy's `git hash-object` against the merged blob, delete the copy, then fast-forward.
- **`git diff <ref> -- <untracked files>` shows them as deleted**, which compares nothing. To compare an upload,
  use `util/ad-hoc/2026-11-25_run_tests_rollout_sibling_worktree.py verify-upload --path <worktree> --branch <b>`.
  It works for a juniper-ml worktree too.
- **Sibling tests use the engine's public API only** (`__all__`). Names like `group_lanes`, `lane_aliases` and
  `requirement_name` are internal, and a 0.10.x patch may change them. juniper-ml's own tests may use internals,
  because the engine and those tests change together.
- **Recurrence's overlay venv:** a venv with `--system-site-packages` over `JuniperCascor1`, with ci-tools 0.10.0
  installed into the venv only. It runs recurrence's lanes without touching the shared env, which still reports
  0.9.1.
- **Kept scratch** is copied to the juniper-ml primary's `tmp/run-tests-convert--happy-forging-scone/` (30 entries,
  7 MB). It holds:
  - the `main` exports (`x/`);
  - the captures and comparisons (`cap/`);
  - the old copies (`old/`);
  - the probes;
  - the commit and PR bodies;
  - the mutation and waiter logs.
  - The four venvs stayed in this worktree's `tmp/convert/`; they can be regenerated.
  - A background waiter (`wait_for_ci_tools.py`) runs in this session until about 10:41Z, and dies with it. The
    kept `wait_log.txt` is a snapshot taken before its last line.

## Verification commands

```bash
git fetch origin && git log --oneline -3 origin/main       # from your own juniper-ml worktree (the guard refuses cd into the primary); 87285b19 or later
gh pr view 2693 -R pcalnon/juniper-ml --json state,mergeCommit --jq '.state, .mergeCommit.oid'          # MERGED 87285b19...
gh pr view 275 -R pcalnon/juniper-data-client --json state,headRefOid --jq '.state, .headRefOid'      # OPEN 6cb02bf8...
gh pr view 242 -R pcalnon/juniper-recurrence --json state,headRefOid --jq '.state, .headRefOid'       # OPEN 8a68f344...
gh release view juniper-ci-tools-v0.10.0 -R pcalnon/juniper-ml --json tagName,publishedAt             # "release not found" until cut
curl -s https://pypi.org/pypi/juniper-ci-tools/json | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])'   # 0.9.1 until published
gh run view 46128744416 -R pcalnon/juniper-data-client --json conclusion --jq .conclusion             # failure (until re-run)
gh run view 46128761521 -R pcalnon/juniper-recurrence --json conclusion --jq .conclusion              # failure (until re-run)
```

## Git state

- **juniper-ml**: #2693 is merged (`87285b19`).
  - This handoff lands in its own PR, from branch `docs/handoff-run-tests-rollout-conversions-open`. Find it with
    `gh pr list -R pcalnon/juniper-ml --head docs/handoff-run-tests-rollout-conversions-open --state all`.
  - The worktree `happy-forging-scone` is at `origin/main` (`87285b19`), on its own branch
    `worktree-happy-forging-scone`. The shared local `main` ref is older, at `1b62c111`.
  - It is clean apart from this file. Its gitignored `tmp/convert/` holds the scratch, which is also kept in the
    primary, as above.
- **juniper-data-client**, **juniper-recurrence**: one branch each, `refactor/run-tests-thin-spec`, each a single
  signed commit on `main`. Their worktrees match the uploads byte for byte.
