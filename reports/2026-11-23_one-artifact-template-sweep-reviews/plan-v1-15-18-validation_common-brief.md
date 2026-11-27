# Plan v1.15.18 draft 1: independent validation (common part of both lenses' briefs)

You are one of two independent validators of a DRAFT revision of a planning record. You have not seen the other
validator's work and must not look for it. Your job is to REFUTE the draft, not to confirm it: a claim stands only
when you re-derive it yourself from its primary source. When a source does not support a claim exactly, report it;
when you cannot reach a source, say UNVERIFIABLE, never "probably fine".

## What is under review

- The draft diff: `tmp/v1_15_18/val/plan_v1_15_18_draft1.diff` (sha256 `1b4d6e92…`), of
  `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.15.17 -> v1.15.18. The full
  post-edit plan is frozen as `tmp/v1_15_18/val/plan_v1_15_18_draft1.md`. Only the ADDED and CHANGED lines are under
  review, but read the plan around them as context.
- The writer that produced it: `util/ad-hoc/2026-11-26_consolidated_plan_v1_15_18_template_sweep.py`.

All paths are relative to `ME=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/purring-hugging-hippo`
unless absolute.

## Primary sources (all READ ONLY)

- The arc's live record: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock/tmp/sweep/REVIEW_DISPOSITIONS.md`
  (2733 lines; `grep -n '^## '` lists its sections), and beside it the round briefs (`ROUND*_BRIEF.md`,
  `FIXPASS*_BRIEF.md`, `LAND_BRIEF.md`); the round reports `…/ethereal-munching-peacock/tmp/r{6..12}review/ROUND*_REPORT.md`;
  `…/ethereal-munching-peacock/tmp/arc/plan_v1_15_18_inputs.md` and `…/tmp/arc/sweep_scripts.sha256`.
- The ports' worktree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun/tmp/ports/`
  (each `<repo>/review/REVIEW.txt`, `<repo>/REPORT*.txt`, `SWEEP_PORT_BRIEF.md`, `SWEEP_PORT_REVIEW_BRIEF.md`).
- In `$ME` (juniper-ml `main` at `557490fb`): `prompts/thread-handoff_automated-prompts/` (the arc's handoffs,
  `HANDOFF_2026-11-2[3-6]_one-artifact-sweep-*.md`, `HANDOFF_2026-11-23_r-obs-sc-2-owner-items-recurrence-pin-0-8-1-seven-worktrees-archived.md`,
  `HANDOFF_2026-11-23_overtoad-rename-repair-ml-2606-recurrence-deploy-next.md`) and
  `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (ml#2619's inventory).
- GitHub, read-only: `gh pr view <n> --repo pcalnon/<repo> --json ...`, `gh run view`, `gh api` GETs. PyPI / TestPyPI
  JSON (`https://pypi.org/pypi/<pkg>/<ver>/json`, `https://test.pypi.org/pypi/<pkg>/<ver>/json`).
- This session's host probe output: `tmp/v1_15_18/probe_state.out` (2026-11-26 21:54:57Z). You may re-run read-only
  host probes yourself (`docker ps`, `ss -ltn`, reading files); report the time from `date -u`.

The draft also cites a review archive, `reports/2026-11-23_one-artifact-template-sweep-reviews/` (`SW/`), which another
agent is building in `$ME` while you work. Do not judge whether its files exist yet; judge the claims against the
primary sources above.

## Rules

- NEVER write under `/tmp` or `/var/tmp`. Write only inside your own output directory (below).
- Never modify the plan, the writer, or anything in the other worktrees; never commit, push, stash or delete.
- This session is worktree-isolated: a command line that runs git against another checkout is refused. Read other
  worktrees' files with `cat`, `sed`, `grep`, never with git there. The host `grep` is ugrep, which honours
  `.gitignore` and so SKIPS `tmp/`: use `command grep` or `/usr/bin/grep` for anything under a `tmp/` directory.
- Times from `date -u`, never estimated.
- Severity: BLOCKER (the record states something false that a successor would act on, or misstates a ruling),
  MAJOR (a false or unsupported fact, a missing item a source says this revision must record, or a contradiction
  with the rest of the plan), MINOR (imprecise, misleading by omission, a citation that does not resolve), NIT.

## Output

Write two files in your output directory, then end with a final message that repeats the findings in full (the final
message is the record if a file write is refused):

1. `findings.txt` (plain text; a `.md` write may be refused): one block per finding, with an id, the severity, the
   draft's exact text (quote the plan line), what the source says (with path:line or the `gh` command and its output),
   and a proposed replacement text. Then a list of every claim you checked and found CONFIRMED (one line each, with its
   source), so the reader can see the coverage.
2. `fixes.json`: `[{"id": ..., "old": <exact text in the post-edit plan>, "new": <replacement>}]`, each `old` unique in
   `tmp/v1_15_18/val/plan_v1_15_18_draft1.md`.
