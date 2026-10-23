# Lane 15-C — replay, consistency and conventions review of the canopy E2E ledger's Phase 15

You are an independent validator (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).
Work only inside the juniper-ml worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sequential-coalescing-boot`
(read-only there; write scratch under `/private/tmp/claude-501/lane15C/`). Record the worktree HEAD sha you review.
Do not start any service. The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs,
`$(…)` in command text and env prefixes: one plain command per call, interpreters by path.

## 1. Replay the apply pass from `origin/main`

The phase was applied by `util/ad-hoc/2026-10-20_phase15_items31_32_apply.py`. Make a copy of `origin/main`'s five
edited files WITHOUT git outside the worktree (`git show origin/main:<path> > <copy>` from inside the worktree is
allowed; so is `gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-ml/contents/<path>?ref=main"`),
under `/private/tmp/claude-501/lane15C/main/`, with the same relative paths:

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`

Run `python3 -I util/ad-hoc/2026-10-20_phase15_items31_32_apply.py --root /private/tmp/claude-501/lane15C/main` and
compare the six resulting files (the five above plus the new
`HANDOFF_2026-10-20_canopy-phase15-items-31-32-done-f069-f028-fixed.md`) byte for byte with the worktree's. Report
every difference: a difference means a hand edit after the apply, which the landing procedure (whole-file uploads
rebuilt from `origin/main`) would lose. Also run the canopy apply scripts in `--check` mode against a fresh copy of
canopy `main` (`util/ad-hoc/2026-10-20_f069_apply_fix.py --root <copy> --check` must report every step `done`
once #760 is on main; `2026-10-20_f028_apply_fix.py --check` likewise once #761 is), to show the scripts describe
what landed.

## 2. Consistency

- `python3 -B util/ad-hoc/e2e_finding_triage.py` and `--open-only`: do the counts match every place the phase states
  them (the Phase 15 heading, "Matrix effect and counts", the handoff's Completed and verification commands, the
  INDEX row, the parent's pointer, the SUPERSEDED banner)?
- Every verification command in the new handoff: run it; does it print what the comment says?
- Every path the phase, the blockquotes and the handoff name: does it exist (scripts, records, logs, briefs)? Is any
  record file named that is not in the worktree (the screenshots under `item31-turing/shots/` are LFS PNGs and are
  said to stay on turing: is that stated everywhere a shot is mentioned)? Every `file:line` into canopy source:
  check against the fix trees (`/Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy-f069`, `-f028`) or
  canopy `main` through `gh api`.
- Do M-PARAMETERS-06's cell, F-CANOPY-028's header, its blockquote and the Phase 15 item 31 section agree with one
  another and with the records?
- Does the Still-owed list carry every item Phase 14 listed (0–32) with the right status, and is item 33 consistent
  with the E2 record (juniper-ml#2282; `reports/2026-10-20_turing-e2-envs/`) and with canopy's new floor?
- The CHANGELOG entries canopy#760 and #761 carry: do they name the same tests, files and figures as the ledger?

## 3. Conventions

- `notes/` file naming and the "name every document a summary references or changes" rule (`AGENTS.md`): the
  handoff's Changed-by-this-session list must name every file this phase created or modified, in juniper-ml and in
  juniper-canopy.
- The ad-hoc scripts' headers (`util/ad-hoc/README.md` convention): every new `2026-10-20_*` script has one.
- The handoff follows `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (goal statement, verification
  commands, git state) and carries the merge-approval rule.
- No secret, environment value or the owner's email anywhere in the landed files (grep the records for `@` and for
  key shapes).

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND. Then §1's byte comparison result, §2's findings one per bullet
with the exact text and the correction, §3's findings. Mark each MAJOR (a count, a disposition, an item, a missing
file or a replay difference) or MINOR.
