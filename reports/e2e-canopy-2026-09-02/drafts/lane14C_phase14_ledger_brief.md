# Lane 14-C — replay, consistency and conventions review of the canopy E2E ledger's Phase 14

You are an independent validator (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).
Work only inside the juniper-ml worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/serialized-noodling-cray`
(read-only there; write scratch under `/private/tmp/claude-501/lane14C/`). Record the worktree HEAD sha you review.
Do not start any service. The worktree-isolation guard refuses `git -C`, `for` loops over tools, `awk` programs,
`$(…)` in command text and env prefixes: one plain command per call, interpreters by path.

## 1. Replay the apply pass from `origin/main`

The phase was applied by `util/ad-hoc/2026-10-20_phase14_item30_apply.py`. Make a whole-tree copy of `origin/main`
WITHOUT git (for example `gh api -H "Accept: application/vnd.github.raw"` for each of the five files it edits, or
`git archive`/`git show origin/main:<path>` from inside the worktree, which the guard allows), under
`/private/tmp/claude-501/lane14C/main/`, with the same relative paths:

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`

Run `python3 -I util/ad-hoc/2026-10-20_phase14_item30_apply.py --root /private/tmp/claude-501/lane14C/main` and
compare the six resulting files (the five above plus the new
`HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`) byte for byte with the worktree's. Report every
difference: a difference means a hand edit after the apply, which the landing procedure (whole-file uploads rebuilt
from `origin/main`) would lose.

## 2. Consistency

- `python3 -B util/ad-hoc/e2e_finding_triage.py` and `--open-only`: do the counts match every place the phase states
  them (the Phase 14 Summary, "Matrix effect and counts", the handoff's Completed and verification commands, the
  INDEX row, the parent's pointer)?
- Every verification command in the new handoff: run it; does it print what the comment says?
- Every path the phase, the blockquotes and the handoff name: does it exist (scripts, records, transcripts, shots,
  briefs)? Every `file:line` into canopy source: check against the E2 tree
  `/Users/pcalnon/.local/state/juniper/turing-e2/trees/juniper-canopy` (canopy `main` `571743db`).
- Do the eleven matrix cells agree with the entries and the records? Does M-PARAMETERS-06's note agree with
  F-CANOPY-028's blockquote?
- Does the Still-owed list carry every item Phase 13 listed (0–30) with the right status, and are 31 and 32
  consistent with the entries?
- Is anything the phase says contradicted elsewhere in the ledger (search the file for the findings' ids and for
  `item 30`)?

## 3. Conventions

- `util/ad-hoc/README.md`: the ad-hoc header convention; do the seven new `util/ad-hoc/2026-10-20_*` files meet it?
- `AGENTS.md`/`CLAUDE.md` § Conventions: the summary-names-every-document rule (the handoff's Completed, Changed and
  Remaining sections); notes file naming (no new notes file, confirm); script placement (nothing under `/tmp` that
  produces repository content).
- Lint: `shellcheck` on the two bash scripts; `/usr/local/miniforge3/envs/JuniperPython/bin/python -m flake8
  --max-line-length 512` on the five python scripts; markdownlint config `.markdownlint.yaml` (line length 512) —
  check the changed markdown with whatever is available (`pre-commit run markdownlint --files <paths>` from the
  JuniperPython env if the hook is installed; otherwise reason from the config).
- The repo's tests that read these files: `python3 -m unittest discover -s tests -p 'test_*handoff*.py'` and
  `-p 'test_*ad_hoc*.py'`, and any test naming `e2e_finding_triage` or the ledger (grep `tests/` for the ledger's
  filename), run them.

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND. Then each defect, numbered, marked MAJOR (a replay difference, a
count mismatch, a verification command that prints the wrong thing, a missing path, a failing test) or MINOR, with the
exact evidence. Then what you checked and found right, briefly. Then what you could not check and why.
