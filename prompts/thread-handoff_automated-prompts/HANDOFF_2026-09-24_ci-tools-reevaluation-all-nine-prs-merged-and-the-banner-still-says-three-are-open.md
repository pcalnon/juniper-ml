# HANDOFF 2026-09-24 — ci-tools re-evaluation: all nine PRs merged, and the banner still says three are open

**Session**: "ci tools", the re-evaluation of `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`
**Predecessor**: `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. Its status banner is this arc's main artifact.
**Container-registry arc tip**: `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`
**Validation**: **none for this handoff**, by the owner's instruction. The banner it describes passed five consensus rounds. The record is § "Validation record for this banner" of `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`.

---

## Handoff goal

Continue the ci-tools re-evaluation arc. First, make the post-merge edit to the status banner of
`HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. Then pick up a
startable item.

### Completed (SHAs are merge commits)

- **juniper-ml#2020** merged as `b6580529` on 2026-09-23, blob-verified (25 files, 0 differ). It
  added:
  - the status banner and its validation record to
    `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`;
  - a Status line to
    `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`;
  - `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`, which censuses every
    `juniper-ci-tools` specifier at each repo's remote `main`. Its `--self-test` has 103 cases;
  - `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py`, which kills 42 of 42 mutants;
  - fixes to juniper-ml's 11 stale ci-tools lines:
    - `docs/REFERENCE.md` (four);
    - `util/fleet_triage/predict_merge.py` (three);
    - `.github/workflows/ci.yml`;
    - `tests/test_coverage_gap_mapper_drift.py`;
    - `tests/test_ci_tools_drift.py`;
    - the "Expected output" block of `docs/QUICK_START.md`;
  - the verbatim lane reports in `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`.
- **The sibling PRs**, which fixed the other 12 of the 23 stale lines and moved two pins:
  - juniper-canopy#655, `26e0546f`;
  - juniper-cascor-client#170, `346d11b8`;
  - juniper-data-client#210, `9bc8870a`;
  - juniper-deploy#228, `fc21de93`;
  - juniper-cascor#673, `e7c24896`, merged 2026-09-23 13:54Z. **Not blob-verified yet.**
  - Pins: juniper-deploy#227, `a725f69b` (data `0.15.0`), and juniper-deploy#229, `d589dd95`
    (worker `0.6.1`). This session merged #229 through `util/safe_merge.py`, blob-verified. The
    owner's sweeper merged the rest.
- **Issues filed**:
  - juniper-canopy#661: the X7 flake;
  - juniper-recurrence#182: the 6f starlette watch;
  - juniper-data#427: arc_agi's `VERSION` was not bumped after data#402.
- **Post-merge census simulation** at the PR heads (ml `120660d3`, cascor `0e831a97`):
  - exit 0;
  - 54 live pins, all `>=0.9.0,<0.10.0`;
  - two AMBIGUOUS lines, both passing: `docs/REFERENCE.md:3028` and `tests/test_ci_tools_drift.py:461`.
    ml#2036 moved the first of these from `:3023`.
- **Memory** (outside git):
  - created `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`. Another session
    has since rewritten it with the owner's ruling;
  - updated `project_container_registry_rollout_2026-09-08.md` (the arc_agi, X7 and census bullets);
  - updated `reference_canopy_x7_timing_tests_flake_on_ci_runners.md` to point at canopy#661;
  - added one pointer to `MEMORY.md`.

### Remaining work

1. **Blob-verify juniper-cascor#673.** Compare `gh api repos/pcalnon/juniper-cascor/commits/e7c24896`
   against the PR's final head, file by file.
2. **Make the post-merge edit to the banner** of
   `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. The banner
   dates its state to 2026-09-23 01:50 UTC and still calls three merged PRs open. Change these
   anchors:
   - "In flight when this was written" in the one-minute block: all three merged, with the SHAs
     above;
   - note b's "(juniper-deploy#229, open)": merged, `d589dd95`;
   - the Startable bullet "The juniper-deploy repin to worker `0.6.1` is open as
     juniper-deploy#229": drop it, because it is done;
   - the Authored list: deploy#229, cascor#673 and ml#2020 become merged, with their SHAs. Also
     qualify "This is the state at 2026-09-23 01:50 UTC";
   - "Later moves are not reflected": add "except the merges above";
   - the Verification comment "Once juniper-ml#2020 and juniper-cascor#673 have merged, it exits
     0": both have now merged, so run the census and record what it prints.

   Word the merge claim as "each merge commit's files are byte-identical to that PR's final head".
   Do not say "reviewed head": ml#2036 reached #2020's `ci.yml` and `docs/REFERENCE.md` through an
   update-branch, and #2020's last commit postdates round 5. Handoff PRs carry no CHANGELOG entry.
3. **Optional.** In `project_container_registry_rollout_2026-09-08.md`, change the line "PRs opened:
   … ml#2020" to record the outcomes.
4. **Startable, not owner-gated.** The banner's § "Where the remaining work lives" lists them:
   - **Diagnose X7** (canopy#661) before changing any bound.
   - **arc_agi's version bump** (data#427). The allow-list in data's
     `juniper_data/tests/unit/test_val_emission_guards.py` must name arc_agi.
   - **The `dockerhub` drift gate**: §10 of
     `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
   - **The serve and version check**: item 1 of
     `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`. Check the
     five image repos for an open PR first.
   - **The 6f watch** (recurrence#182).
5. **Owner-gated. Do not start these.**
   - Wave 4, step 3 of §5.2B of
     `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`;
   - the Pi pull;
   - OQ-2 and OQ-4;
   - the next juniper-data release, which would carry data#420 (the wheel without its test suite)
     and data#421 (the image that can generate equities);
   - the worktree-cleanup signal.

### Key context

- **The PR sweeper is the owner's.** He ruled on 2026-09-24: "Mine: fix forward". It readies, arms
  and merges open PRs as `pcalnon`, with the DEFAULT squash body. Do not fight it. When a PR must be
  validated before it merges, validate the pushed branch before opening the PR. See
  `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`.
- **juniper-ml's ruleset is `strict`.** An armed PR that goes BEHIND waits forever. Fix it with
  `gh api -X PUT repos/pcalnon/<repo>/pulls/<n>/update-branch`.
- **Census exit 0** means "none of the shapes it parses", not "clean". Its limits are in its
  docstring. `--ref REPO=REF` and `--local REPO=PATH` simulate a merge.
- **`MEMORY.md` is at the load limit** of about 25,000 characters. The owner's target is 20 KB, and
  it overrides the hook's 17.1 KB request (`feedback_memory_index_target_is_20kb.md`). Never strip a
  hook.
- **The tip's banner is stale on three facts.** The banner of
  `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` was last
  updated by ml#2025. Since then:
  - the worker `0.6.1` wheel reached PyPI;
  - data#421 merged;
  - deploy#227 merged.

  The containers session owns that file and has been told.
- **Commits must be signed.** Use `util/open_signed_pr.py` for a new PR and
  `util/push_signed_commit.py` for an append (promoted by ml#2036).
- **Tool traps.**
  - gh 2.46.0 has no `gh pr checks --json`.
  - A worktree-isolated session refuses `git -C` and awk programs.

### Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git pull --ff-only     # needs b6580529 or later
gh pr view 673 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'   # MERGED e7c24896
python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test   # 103 passed, 0 failed
python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py      # 42 of 42 mutations killed
python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py              # expect exit 0 and two passing AMBIGUOUS lines
grep -n 'In flight when this was written\|: open\.\|, open)\|is open as juniper-deploy#229' prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md
```

### Git status

- The worktree is `.claude/worktrees/jolly-wibbling-pearl`, on branch `worktree-jolly-wibbling-pearl`.
  It holds uncommitted copies of ml#2020's files, all merged in `b6580529`. Nothing else in it is
  uncommitted except this handoff, which has its own PR. Removing the worktree still needs the
  owner's signal.
- This handoff's PR was opened but not merged by this session.
