# R-OBS-SC-2 follow-ups: the independent reviews, and one fix pass

Archived on 2026-11-15 by `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`, as plan v1.15.16 records
(`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Each review ran as an independent
sub-agent and returned its report as its final message. Four reviewed what R-OBS-SC-2's follow-ups shipped (the
guard and register change, and the two release bodies); the last two reviewed plan v1.15.16's own draft. Before this
archive one report sat in a worktree's gitignored `tmp/`, and the rest existed only in session transcripts, which
Claude Code moves between project directories.

Each `*_brief.md` is the prompt the reviewer was given, and each `*_report.md` is the report it returned: both
verbatim, plus one final newline. Neither was edited, so a report's findings are as the reviewer wrote them,
before any were checked. What was applied, and where, is recorded in plan v1.15.16 and in the PRs named there.

| Review | Session, agent and model | Brief sent (UTC) | Report returned (UTC) | Report sha256 (text) |
| --- | --- | --- | --- | --- |
| [The retry-after-rounds-up guard, round 1](guard-round-1_report.md) ([brief](guard-round-1_brief.md)) | `7d425759`, `agent-a5ec31fdeec16fafe` (prompt 1; rows 0 / 629-630), opus (claude-opus-5-5) | 2026-11-14T10:19:33.971Z | 2026-11-14T10:41:08.199Z | `ab6629d70f0ebb11…` |
| [The APD-ECO-016 change set (guard + register), round 2](guard-round-2_report.md) ([brief](guard-round-2_brief.md)) | `1b4fec84`, `agent-a55b11b832d780f60` (prompt 1; rows 0 / 645-646), opus (claude-opus-5-5) | 2026-11-15T00:58:29.832Z | 2026-11-15T01:31:45.256Z | `6c4a08a59b9acde5…` |
| [The juniper-cascor v0.14.0 and juniper-canopy v0.10.0 release bodies, round 1](notes-round-1_report.md) ([brief](notes-round-1_brief.md)) | `1b4fec84`, `agent-a1bd2c68c56b33137` (prompt 1; rows 0 / 535-536), opus (claude-opus-5-5) | 2026-11-15T00:09:18.716Z | 2026-11-15T00:42:33.529Z | `89c6315846421b4f…` |
| [The release-body corrections, round 2](notes-round-2_report.md) ([brief](notes-round-2_brief.md)) | `1b4fec84`, `agent-a1bd2c68c56b33137` (prompt 2; rows 537 / 660-661), opus (claude-opus-5-5) | 2026-11-15T00:50:34.759Z | 2026-11-15T00:59:55.500Z | `cb5a499bd5fed541…` |
| [Plan v1.15.16's draft: the fact-check](plan-v1-15-16-review-a_report.md) ([brief](plan-v1-15-16-review-a_brief.md)) | `b9dfa450`, `agent-a26341d463f77d37d` (prompt 1; rows 0 / 719-720), opus (claude-opus-5-5) | 2026-11-15T04:13:45.331Z | 2026-11-15T04:41:20.775Z | `35ce751d184fe98e…` |
| [Plan v1.15.16's draft: the adversarial read](plan-v1-15-16-review-b_report.md) ([brief](plan-v1-15-16-review-b_brief.md)) | `b9dfa450`, `agent-a1665ffe2f43192ea` (prompt 1; rows 0 / 512-513), opus (claude-opus-5-5) | 2026-11-15T04:14:10.426Z | 2026-11-15T04:40:44.107Z | `7508c19f061843d2…` |

The round-1 guard report also equals the copy its session saved, `.claude/worktrees/toasty-prancing-karp/tmp/s1/guard_review_round1.md` in the juniper-ml primary
(sha256 `37508e487e0eda00…`), once that copy's one-line HTML comment is removed. The two notes rounds are one
agent: round 2 was a message sent to it while it ran.

Copied verbatim from a worktree's gitignored `tmp/`, which `git worktree remove` deletes:

| File | What it is | Source (in the juniper-ml primary) | sha256 |
| --- | --- | --- | --- |
| [five-prs-validation-fixpass-round-1.md](five-prs-validation-fixpass-round-1.md) | The five PRs' validation, round 1: the fix pass and its list 'For the handoff and plan v1.15.16' (session 6e3bdef0, 2026-11-12) | `.claude/worktrees/logical-percolating-sparkle/tmp/lps/fixpass_r1.md` | `ad8d90912ec864c9…` |

Re-check (it writes nothing; when a source has gone, it checks the archived copy against its pinned sha256):

```bash
python3 util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py --check
```
