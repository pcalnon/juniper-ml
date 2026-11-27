# Plan v1.15.18, round 2: validate the corrections

Read `tmp/v1_15_18/val/VALIDATION_BRIEF_COMMON.md` first: its sources, rules, severity scale and output format apply
here, with these changes. Your output directory is `tmp/v1_15_18/val/round2/`. All paths are relative to
`ME=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/purring-hugging-hippo` unless absolute.

## What is under review now

Draft 1 (`tmp/v1_15_18/val/plan_v1_15_18_draft1.md`) was read by two independent validators. Their findings are
`tmp/v1_15_18/val/facts/findings.txt` (a fact re-probe: 0 BLOCKER, 3 MAJOR, 11 MINOR, 10 NIT) and
`tmp/v1_15_18/val/attack/findings.txt` (a completeness attack: 1 BLOCKER, 8 MAJOR, 18 MINOR, 11 NIT). The orchestrator
re-checked them and rewrote the writer; the result is draft 2:

- `tmp/v1_15_18/val/plan_v1_15_18_draft2.md` (sha256 `09c9516c…`), the post-edit plan;
- `tmp/v1_15_18/val/plan_v1_15_18_draft2.diff` (`4b5d1f72…`), main's v1.15.17 -> draft 2;
- `tmp/v1_15_18/val/draft1_to_draft2.diff` (`07388b0c…`), the interdiff: THIS is what you review first;
- `tmp/v1_15_18/val/writer_draft2.py` (`4d4d4bed…`), the writer that produced it.

## Your lens: the corrections, adversarially

The documented failure of correction passes is that they introduce new errors: a fixed number that is now wrong
elsewhere, a new sentence that contradicts an old one, a citation that no longer resolves, a list that now renders at
the wrong depth. Round 2 on an earlier plan found twelve defects in one correction pass, six of them introduced by it.

1. **Every added or changed line in the interdiff**: re-derive each fact from its primary source yourself (not from
   the round-1 findings, which can be wrong too). New facts in draft 2 include: the primary's reflog
   (`/home/pcalnon/Development/python/Juniper/juniper-ml/.git/logs/HEAD`; read it with `cat`/`python3`, never git),
   `docker ps -a`, the 2026-11-23 archive's contents (`/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-archive-2026-11-23/`),
   the 2026-11-26 archive (`…/juniper-ml/tmp/worktree-archive-2026-11-26/`), juniper-observability 0.4.2's PyPI
   `requires_dist`, the start prompt's addenda (`prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md`),
   the inventory's rows R9, R11 to R13, R21, R22, R25, R45 to R53, and the transcripts' timestamps for four messages:
   this session's `~/.claude/projects/*/d769e173-*.jsonl` and the ports session's `~/.claude/projects/*/3792e0cc-*.jsonl`
   (date each message by its FIRST timestamped entry; `api-request-blob` copies carry no time).
2. **Each round-1 finding**: was it applied, applied correctly, or declined? The orchestrator says none was declined.
   For each finding id in both files, give APPLIED-OK, APPLIED-WRONG (and why) or MISSING.
3. **New contradictions**: does any new sentence contradict another line of the plan, old or new? Pay particular
   attention to: the 0.4.3 / 0.4.4 renumbering (every passage that names 0.4.3, R-OBS-SC-3 or the start prompt); the
   trio's environments (0.4.0/0.5.0 vs 0.4.2/0.7.2 vs the second pass); "restart" vs "bring-up"; what is archived and
   what is not (the "What remains" bullet against the archives on disk); and the times of the merge approvals.
4. **Structure**: every new sub-bullet's list depth (is it nested under the line it annotates, at a depth that renders
   as intended?), the new top-level bullets in §5 and §6, and the two table rows edited in place (does each still have
   its column count?).

Also say whether anything in draft 2 is now WORSE than in draft 1.
