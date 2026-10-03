# Dynamic workflow harness — design for limit-paced, goal-driven agent dispatch

**Project**: juniper-ml — Meta-package & automation hub for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Document Type**: Design (design-of-record candidate; nothing here is implemented)
**Document Version**: v3 (round-1 Lane A and Lane B applied; the maps are Appendix D and Appendix E)
**Status**: DRAFT — consensus round 1 complete (Lane A ×3, Lane B ×2, all applied or recorded as dissent); round 2 on the corrections pending; owner decisions D-1..D-12 (§10) open
**Last Updated**: 2026-09-23
**Measured at**: juniper-ml `25b78f55` (#2013); Claude Code `2.1.280`; host `yamaguchi`, 16 CPUs; every count in §2 carries its instant because every one of them moved during the round
**Seed**: branch `design/dynamic-workflow` (`27ea09a1`) carries the owner's requirements text as `notes/dynamic_workflow_design.out`; Appendix A reproduces it (whitespace-normalised) and it is the requirement set this design answers
**Companions**:
[`JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`](JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md) (the agent suite this extends, "SUITE"),
[`JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`](JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md) (the removal gates this adopts, with one amendment, "V3"),
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) (the validation procedure the workflow runs and this document is held to, "CON"),
[`JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md) ("HANDOFF"),
[`JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md) §20 (the one prior headless-dispatch instrument, "SOAK"),
[`JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md`](JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md) (the five inventories §2 cites, verbatim, "INV"),
[`JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md`](JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md) (the five validator reports this version answers, verbatim, "R1")

---

## 0. How this document was produced, and what it is not

Five read-only inventories and two probes, each with a different entry point, were run before a line of design was written (INV). The v1 draft then went through CON Lane A with three agents on three entry points; v2 applied their findings; v2 went through CON Lane B with two opposing briefs (R1). Every finding from both lanes is applied here or recorded as dissent (Appendix D, Appendix E). Every `file:line` below is at `25b78f55` unless a URL is given.

| Step | Entry point | Instrument | Could it have said something else? |
| --- | --- | --- | --- |
| Harness inventory (INV I1) | `scripts/`, `prompts/agent_templates/`, `util/prompt_discovery/`, `.claude/agents/`, `.claude/skills/`, `tests/` | Explore agent, grep-verified absences | Yes: it reported the zero-hit greps for scheduler / usage-limit / goal-set / hooks / workflows |
| Worktree inventory (INV I2) | `util/worktree_*.bash`, `scripts/cleanup_session_worktrees.py`, `docs/REFERENCE.md` § Worktree, V3, `git worktree list --porcelain` | Explore agent | Yes: its counts had moved by the time Lane A1 re-counted six hours later (§2.4) |
| Design-path inventory (INV I3) | `notes/` naming + templates + recent headers, handoff archive, `conf/memory_budget.json`, CI gates | Explore agent | Yes: it found the header Status is free prose with no `Superseded-by` field anywhere (§2.5) |
| Documented behaviour (INV I4, I5) | `code.claude.com/docs` pages for workflows, sub-agents, worktrees, headless, hooks, statusline, interactive-mode, costs, agent-teams, cross-session-messaging, goal, agent-view, scheduled-tasks, routines, settings-reference | `claude-code-guide` agent ×2, direct fetches, then Lane A2's raw-page re-derivation | Yes: Lane A2 reversed four of its "NOT DOCUMENTED" verdicts (Appendix D) |
| Usage-limit records (Appendix B) | `~/.claude/projects/<juniper-ml slug>/*.jsonl` | `util/ad-hoc/2026-09-22_rate_limit_record_probe.py` (read-only; lands with this document's PR) | Yes: it would have printed `records: 0`; Lane A3 then showed the sample is an mtime window other sessions move |
| Round-1 Lane A | A1 repository only; A2 docs + local state only; A3 execution only | three `general-purpose` agents, killed by a 429 and resumed in place | 17 DISAGREE / 9 demonstrated failures / 17 underspecified rules |
| Round-1 Lane B | B1 refute the architecture, premises granted; B2 amputation against the seed + actionability for a successor | two `general-purpose` agents on v2 | 20 refutations (3 blockers) and one steelmanned alternative; 12 amputation rows, 10 standing-rule conflicts, 31 actionability defects |

What this document is **not**: it is not a plan of record, nothing in it is built, and no step of §11 except the measurement step P0 may start before round 2 reports and the decisions each step names in §11 are ruled. It adopts V3's removal gates by reference and proposes one amendment to them (§7.3); V3 is itself unratified.

---

## 1. Purpose, requirements, scope

### 1.1 Purpose

Extend the juniper-ml Claude Code harness (SUITE) so that, without a human choosing each task, agents are dispatched against the *current* set of active design-path documents, those documents are kept current as work lands, consumption is paced against the account's 5-hour and 7-day usage windows, every executing agent gets a fresh worktree whose removal is ordered when its arc completes, and every owner decision is routed to the owner while work continues on what is not blocked.

### 1.2 Requirements (from the seed, Appendix A) and the three re-scopings the owner must ratify by name

| ID | Seed clause (condensed) | Where answered | Re-scoping, if any (Lane B2) |
| --- | --- | --- | --- |
| R1 | a dynamic workflow dispatches agents to perform prompts, written and validated dynamically **if necessary** | §6 | validation is *always* run (a prompt validated against an older HEAD is stale by the rubric's own rule); writing is skipped when the ledger names a prompt |
| R2 | given an initial set of notes design-path documents that define current, active goals | §4 | the initial set is the owner's pick from INV I3 §3's arc table, seeded as §4.2 |
| R3 | as work is performed, the documents are kept up to date | §4.4, §6.5 | "up to date" = append-only state lines and task lists on a per-document dispatch branch, visible on `main` only after the owner merges that branch (§6.5) |
| R4 | as docs complete or are superseded, the goal set updates | §4.3 | automatic only for the design's own append form and for a successor's `Supersedes` line; every other transition is a drift flag the owner confirms |
| R5 | dispatch optimises progress while the session and weekly limits are **met but not exceeded** by their expiry | §8, D-5, D-10 | "met" = the *binding* window (in practice the weekly one) reaches an owner-set target at its reset; the non-binding window is necessarily under-used; "optimises" = greedy first-fit in owner priority order with a retry budget |
| R6 | every agent is handed a fresh worktree | §7.1 | the agents that *edit repository content* (executor, prompt-writer, doc-maintainer) get one; read-only validators and refuters do not; a decision-blocked task's redo reuses its own worktree by design |
| R7 | when the arc is complete and the worktree meets the removal criteria, the workflow specifies removal | §7.2–§7.3 | as written; the criteria are V3's with one amendment (§7.3) and nothing executes before ratification |
| R8 | open decisions go to the owner, their tasks listed as blocked, the agents reassigned so cadence continues | §9 | "reassigned" = the freed cost is spent on a standby task in the same cycle (§6.2) and the blocked task is excluded from selection until ruled |

Cross-cutting (from the request that produced this document): reuse the existing harness, apply the repo's best practices, minimise tokens, respect session limits, and validate by consensus (§6.4, §12).

### 1.3 Scope and non-goals

In scope: juniper-ml as the orchestration home; tasks may target any of the nine ecosystem repos, because every existing agent already does (`.claude/agents/task-executor.md:3`, "1-3 repos"), and §7.1 creates the task's worktree in the task's repo. Out of scope: cloud Routines and Projects (they cannot reach this host's conda environments, services, or the parent `Juniper/AGENTS.md`, which is not in any repository); Agent Teams (§3.3); merging PRs (`prompts/agent_templates/data/standing_rules.yaml:6`, `:15`: the owner merges); executing any worktree removal before V3 (as amended) is ratified.

---

## 2. Ground truth the design rests on

### 2.1 Usage limits are observable, and this account is limit-bound today

Three independent signals exist; none is used by anything in the repo today (Lane A1: zero hits for `quotaLimits|five_hour|seven_day|used_percentage|rate_limits|resetsAt` anywhere in the repo outside the probe script).

**Signal 1 — the transcript record on a hit.** Every session transcript under `~/.claude/projects/<slug>/` carries, on the assistant line that announces a limit, a `quotaLimits` object at the line's root (a sibling of `message`, on a record of `type: "assistant"` whose model is `<synthetic>`; Lane A2 re-derived the chain on 143/143 records):

```json
{"status": "rejected", "resetsAt": 1790116800, "unifiedRateLimitFallbackAvailable": false,
 "rateLimitType": "five_hour", "overageStatus": "rejected",
 "overageDisabledReason": "out_of_credits", "isUsingOverage": false}
```

`rateLimitType` is `five_hour` or `seven_day`; `resetsAt` is Unix epoch seconds; the text is `You've hit your session limit · resets 5:40pm (America/Chicago)`. A second shape adds `lowPriorityOffer` (`control`/`treatment`), `lowPriorityMaxWaitSeconds` (1200), `lowPriorityRetryAfterSeconds` (20). **`overageDisabledReason: out_of_credits` on every record means usage credits are not a fallback for this account**: a hit is a hard stop until `resetsAt`.

**The record is not written when the limit is hit.** Lane A3 traced a transcript whose 429 burst is timestamped 02:20Z, absent from an all-file scan at 05:14Z and present at 05:19Z, right after the owner's resume prompt at 05:15Z: a session waiting at a limit flushes its records only when it next writes. A reader of Signal 1 learns **when a window resets**; it must never conclude "no hit" from absence (§5.2).

**Signal 2 — the status line JSON.** Claude Code passes a status-line script, on stdin, `rate_limits.five_hour.used_percentage`, `rate_limits.five_hour.resets_at`, `rate_limits.seven_day.used_percentage`, `rate_limits.seven_day.resets_at` ("from 0 to 100, and `resets_at`, the Unix epoch seconds when the window resets"), which "appears only for claude.ai Pro and Max subscribers, or behind a Claude apps gateway …, and only after the first API response in the session"; Claude Code "drops a window once its `resets_at` time passes", re-runs the script on a documented trigger list and an optional `refreshInterval` timer (1 s minimum), and warns that "the event-driven triggers can go quiet when the main session is idle" (https://code.claude.com/docs/en/statusline). Each session's payload is **that session's** snapshot, so the values differ across the 7–8 concurrent sessions and a timer re-render repeats a possibly old payload (Lane B1 #5; §5.1). This is the only documented *continuous* utilisation signal, and it exists only in interactive sessions. **No status line is configured on this host** (`~/.claude/settings.json` keys at 2026-09-23 05:3xZ: `agentPushNotifEnabled, autoMode, editorMode, effortLevel, model, skipDangerousModePermissionPrompt, tui`).

**Signal 3 — per-message token usage** (`message.usage.{input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens}`) on every assistant line of every transcript, including subagent transcripts under `<session>/subagents/agent-<id>.jsonl` (70 session directories with a `subagents/` child and 558 agent transcripts in the juniper-ml slug at 05:3xZ, 728 under all of `~/.claude`; swept after `cleanupPeriodDays`, 30). This is the only signal that attributes tokens to a *specific* agent or cycle, which §8 uses for debits.

What the transcripts measured, per window, with the Chicago date each window was hit on (Lane A3's enumeration over the union of the 01:5xZ and 05:2xZ 80-file samples plus the all-slug scan for the weekly total):

| Window reset (Chicago) | Hit on | Records |
| --- | --- | --- |
| Mon Aug 24 07:30am | Aug 24 | 13 |
| Tue Aug 25 10:40pm | Aug 25 | 16 |
| Wed Aug 26 05:50am | Aug 26 | 32 |
| Tue Sep 08 11:20am | Sep 8 | 21 |
| Tue Sep 08 11:40pm | Sep 8 | 53 |
| Mon Sep 21 06:10am | Sep 21 | 15 |
| Mon Sep 21 06:30pm | Sep 21 | 2 |
| Tue Sep 22 05:40pm | Sep 22 | 12 |
| Wed Sep 23 12:10am | Sep 22, 9:05pm | 1 (and the three round-1 validators, §12) |
| **Weekly** Wed Aug 26 10:00pm | Aug 25 | 3–4 (population-dependent) |
| **Weekly** Thu Sep 10 07:00pm | Sep 9 | 3 |
| **Weekly** Wed Sep 23 10:00pm | Sep 22, 23:52Z–00:03Z | 9 in the slug, 17 across all slugs |

Weekly reset times are not a fixed weekday or hour; the reset must always be read from the record. Two consequences drive the design: the windows are account-wide and shared with the seven or eight interactive sessions the owner runs concurrently (`/home/pcalnon/Development/python/Juniper/AGENTS.md:147`), so "met but not exceeded" cannot be satisfied by counting the dispatcher's own tokens; and the weekly window is the binding constraint roughly every second week (three hits in four weeks) — the owner alone reached the weekly wall in three of the last four weeks, which is what makes D-10 a real question.

### 2.2 What Claude Code documents about each primitive at a limit

Re-derived by Lane A2 from the raw pages on 2026-09-23 (R1 Report A2 quotes the sentence per claim).

| Primitive | Behaviour at a usage limit | Persistence / resume | Isolation | Concurrency | NOT DOCUMENTED |
| --- | --- | --- | --- | --- | --- |
| Interactive session | Waits and continues after reset when `autoContinueAtUsageLimit` is on (default `true` for claude.ai subscriptions, v2.1.234+); re-arms **at most twice in a row**; no auto-wait for a reset >24 h away, in Remote Control / teammate / background sessions or `-p`; the wait ends on exit. **Trap**: the key is read from user, `--settings` and managed settings only, and "a project or local settings file that sets it turns the feature off rather than being ignored" (settings-reference) | `--resume` restores history, model (with exceptions), the active goal, and `CronCreate` tasks not yet expired; **a self-paced `/loop` is not restored** | `--worktree` | — | the algorithm behind `used_percentage` |
| Dynamic workflow (saved `.claude/workflows/<name>.js`, `/<name>`) | **Pauses rather than fails** only when all hold: interactive claude.ai session, `autoContinueAtUsageLimit` on, reset within 24 h, not already waited twice (v2.1.271+); "A run doesn't pause in non-interactive mode with `claude -p` or the Agent SDK, in a background session, or in a Remote Control or agent team teammate session": the agent **fails** (→ `null` to the script) | Same-session resume replays failed agents **and every agent started after them**; a `-p` run can start a saved workflow by name with the `Workflow(<name>)` allow rule; `claude -p` "stays open until that work completes", 10-minute idle ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, `0` = none) | `agent(…, {isolation:'worktree'})` gives a worktree **of the repository the session launched from** | min(16, CPUs − 2) = 14 here; `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` 1–256; 1,000 agents per run; the `budget` global is a hard in-run ceiling on **output** tokens only; "No mid-run user input — A run pauses on its own only for agent permission prompts and a usage-limit wait" | whether `SendMessage` can resume a *workflow* agent; whether the `Workflow(<name>)` rule suppresses the interactive consent prompt |
| Subagent (`Agent` tool) | "a subagent whose run ends on an API error, such as a usage limit": foreground returns partial text, background is marked failed; "ask Claude to retry the task or resume the subagent" | `SendMessage` resume retains full history; Explore/Plan are one-shot; `SubagentStart` hooks receive `agent_id`, `agent_type`; `SubagentStop` adds `agent_transcript_path`, `last_assistant_message` | `isolation: worktree` frontmatter, same repository rule; auto-removed only if unchanged | 20 running per session; resumes bypass the cap | — |
| Agent team | teammate sessions do not auto-wait | no resumption after `/resume`; while enabled, a **named** subagent launches as a teammate | none | ≈7× tokens | — |
| Background session (`claude --bg`) | workflows do not pause; the wait menu is unavailable | supervisor under `~/.claude/jobs/<id>/`; attach with `claude attach <id>` | moves into `.claude/worktrees/` before editing | — | — |
| `claude -p` | the affected agent fails; `system/api_retry` events carry `error: rate_limit` and `error_status` | `--resume <session-id>` from any directory (v2.1.223+) continues an unfinished turn; binds an inbox socket (`--bare` does not) | `-p --worktree` skips the trust check and leaves the worktree locked until a later sweep | — | any status-line behaviour (none renders) |
| `/loop` + `ScheduleWakeup`, `CronCreate` | "Tasks only fire while Claude Code is running and idle"; each fire sends the full context | `CronCreate` restored on `--resume` except expired/past-due; self-paced `/loop` not restored; both carry the 7-day expiry; ≤50 per session; 1 min–1 h dynamic interval; fallback wakeup ≈20 min | — | — | whether a task fires during a usage-limit wait |
| `/goal` | "Goal paused" resumes with the session's auto-continue (v2.1.269+); judged by the small fast model per turn | survives `--resume`; usable under `-p` | — | — | a per-evaluation figure |
| Cross-session messaging | a message to an idle session starts a new turn; a bypass-permissions receiver delivers a message only from a sender that is also bypassing, otherwise holds it; a `-p` receiver drops held messages after `dialogExpiry` (5 min); a script can post to a session's own socket (`CLAUDE_CODE_MESSAGING_SOCKET`) | `notify_when_idle` one-shot, 12 h | — | — | — |
| Routines (cloud) | n/a | cloned repo only; cannot reach this host | — | — | — |

Three documented facts constrain the executor path: `--bare` "never reads OAuth credentials" and is unusable on this subscription-authenticated host (SOAK unsets `ANTHROPIC_API_KEY` for the same reason, `util/soak_run_probe.py:345-354`); worktree isolation checks "apply to the repository you launched Claude Code from", so `isolation: worktree` can never hand an agent a worktree of another repo (Lane B1 #11); and every session the owner launches through `claudey` runs with `--dangerously-skip-permissions` (`scripts/claude_interactive.bash:84`, forced by `DEBUG` at `:17`), which is the permission mode this design assumes (§3.2, D-1).

### 2.3 What the harness has, and what it lacks

Re-derived by Lane A1 against `25b78f55`; the full inventory is INV I1.

| Exists | Reused as |
| --- | --- |
| `/template-agent` skill: discovery (`util/prompt_discovery/cli.py`: JSON on stdout, `schema_version: 1`, `ttl_seconds: 900`, `head_sha`; `--target-repo`, `--subject`) → template selection (`prompts/agent_templates/manifest.yaml`, 10 templates: execution 4, analysis 2, planning 2, review 1, generic 1; placeholders `{{NAME}}` / `{{!NAME: hint}}` / `{{?NAME: hint}}`) → fill → `Agent(prompt-validator)` → "max 3 rounds" → `prompts/generated/…`, terminal states `EMIT_CLEAN`, `EMIT_WITH_CAVEATS`, `ESCALATE_TO_PAUL` (`.claude/skills/template-agent/SKILL.md:59-74`; `disable-model-invocation: true` at `:8`) | the prompt-writer stage (§6.3) follows `SKILL.md`'s steps by reference; because the skill is deliberately user-only, invoking its procedure from an unattended agent is an owner decision (D-11) |
| `prompt-validator` with the pinned verdict schema `tests/fixtures/prompt_validator/verdict.schema.json` (`overall ∈ {PASS, FAIL}`; hard gates R2.0, R3.4 at `prompt-validator.md:83`, `RUBRIC.md:20`) | the validate stage, unchanged |
| `task-executor` (`isolation: worktree` at frontmatter line 5; opens a PR, never merges; `Agent` in tools, "may nest") | the execute stage's *body*; §7.1 explains why the dispatcher uses a copy without `isolation` |
| `planner`, `auditor`, `mock-seam-auditor` | analysis-class tasks |
| `fleet-supervisor` + `util/fleet_triage/predict_merge.py` (`--pr N --json`; `MERGE-CLEAN` / `NEEDS-UPDATE-BRANCH` / `DAMAGED-FIX-FIRST` / `CONFLICT`) | the merge-readiness screen (§6.6) |
| `util/soak_run_probe.py`: `claude -p <task> --output-format stream-json --verbose --session-id <uuid>` (`:772-775`), a run directory with `task.txt`, `meta.json`, `stream.jsonl`, `status.json`, pidfile; exit **3 = refused by design**, distinct from 2 (misuse) so `SuccessExitStatus=3` in `util/systemd/juniper-soak-probe.service:114` never reads a typo as success; `util/systemd/juniper-soak-probe.timer` (`OnCalendar=*-*-* 03,09,15,21:23:00`), units present but not installed | the cycle child's invocation shape, run directory, exit-code contract and timer unit (§3.1, §8.5) |
| CON procedure; `reports/<date>_round-NN-consensus/` precedent (rounds 37, 38, 39) | §6.4 and §12 |
| `util/open_signed_pr.py` (`createCommitOnBranch` at `:68`; `expectedHeadOid` pinned to the resolved *remote* base at `:49-50`, `:83-84`, `:146`; `find_open_pr(owner, repo, branch)` at `:175`, called at `:251` — the DUP-GUARD is keyed on the **branch name**; refuses an existing branch at `:276`; whole-file `--add`) | the only signing route for an unattended executor (§6.5); §6.5 and §7.4 add two modes it lacks |
| `util/wait_for_checks.py` (`--json`; exit 0 also for `pr_closed`), `util/safe_merge.py` | owner-side merge path; the dispatcher reads `gh pr view --json state,mergedAt` |
| Defect register close protocol (`**FIXED (<pr>)**`, register `:57`; `register_open_set.py:22`; three `tests/test_register_*.py` in CI) and its lesson at `:51-52` | the ledger keeps status resident, not in the handoff chain (§4) |

| Absent (grep-verified) | Added by |
| --- | --- |
| Any scheduler or queue (the soak timer is `not-found` to `systemctl --user`) | the tick script and timer (§3.1, §8.5) |
| Any awareness of usage limits | the odometer (§5) |
| Any goal-set or work-state tracking (the session store is 606 bare `<uuid>.txt` files at 2026-09-23 00:30 CDT) | the goal ledger (§4) |
| A generate → validate → **execute** pipeline (the skill stops at the written prompt; bundles and verdicts are never persisted) | the cycle workflow (§6) |
| Worktree lifecycle tied to agents; any hook; `.claude/workflows/`; `.claude/settings.json`; `statusLine`/`hooks` keys in the main checkout's `settings.local.json` | manifest, reaper, status-line hook (§5, §7) |

CI facts that bound the first PRs: every agent **and skill** is pinned to `model: opus`, `effort: max` by six tests (`tests/test_agents_frontmatter.py` over every `.claude/agents/*.md`; `test_template_agent_skill_lint.py`, `test_service_smoke_skill_lint.py`, `test_ui_test_author_skill_lint.py`; `test_prompt_validator_contract.py`, `test_fleet_supervisor_contract.py`); `tests/test_ci_test_wiring_drift.py` fails any `tests/test_*.py` not invoked by `ci.yml`'s regression job, so every roadmap step wires its tests there; `conf/memory_budget.json` caps `AGENTS.md` at 38,000 characters (28,273 used).

### 2.4 Worktree state and tooling

Counts move with every session start and end; the design's rule is **re-measure rather than cite**. At 2026-09-23 00:30 CDT, Lane A1 registered 168 juniper-ml worktrees (145 under `.claude/worktrees/`, 22 under `Juniper/worktrees/`, plus the main checkout), 14 locked — all native, one whose pid was dead — 8 detached, 593 local branches of which 94 `worktree-*` branches are checked out nowhere; `Juniper/worktrees/` holds 177 worktrees across nine repos plus a stray `logs/` directory.

**No tool in the repo can today decide a worktree is safe to remove.** V3 ("DESIGN, revision 2", revision 1 "REJECTED by independent consensus (4 reviewers)", V3:6; "It has not been executed", V3:1054) is the only complete specification: worktree gates G1–G5 (G2 = `git -c status.showUntrackedFiles=normal --no-optional-locks status --porcelain -uall`, "must be empty AND exit 0", V3:307-308), branch gates B1–B4 (B3 = `git diff --quiet "origin/main...$BRANCH"`, V3:767; B4 refuses an armed auto-merge), §6.5 "Preserve the admin directory before removal" (V3:817-820), and §7's "recent mtime is a veto. A tree written within the last 7 days is not swept regardless of lock state. `--force --force` … is forbidden outright" (V3:886-888). **Two of V3's branch gates cannot pass on this repo as written**: Lane B1 ran B1 and B3 over six squash-merged, remote-deleted branches (#1854, #1113, #1106, #1459, #1110, #1792) and both refused 6/6, because a squash merge never makes the branch's commits ancestors of `main` and the three-dot diff is therefore never empty — V3 §6.3 says "Ancestry is false for every squash-merge" and then specifies a content test that is ancestry in disguise. §7.3 proposes the amendment. `scripts/cleanup_session_worktrees.py` (predicates in order at `:261-296`) never inspects ignored files and would pass `curious-plotting-hummingbird`, which V3 §5.1 records as carrying the backup passphrase in a gitignored `.env`; `util/remove_stale_worktrees.bash` selects N−1 of N registered trees and CI asserts the removal succeeds (`tests/test_cleanup_open_remove_stale_worktrees.py:92-95`); `docs/REFERENCE.md:3691` marks it `DO NOT RUN`, and INV I2 recommended against `cleanup_open_worktrees.bash` and `worktree_close.bash` as well. The V2 procedure removes a worktree right after `gh pr create`, contradicting `standing_rules.yaml:16` `worktree_cleanup_only_on_merge: true` (the 2026-05-15 / 2026-05-20 incidents are memory of record, not repository artifacts).

Claude Code's own worktrees: `.claude/worktrees/<name>` on branch `worktree-<name>`, base `origin/<default>` fetched when stale (capped at 5 s), a marker in the git metadata (observed as `.git/worktrees/<name>/CLAUDE_BASE`), a lock held by the owning process, and "the checks apply to the repository you launched Claude Code from". The ecosystem convention is the opposite location: `/home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--<YYYYMMDD-HHMM>--<hash8>` (`standing_rules.yaml:9`; `docs/REFERENCE.md:2294` "Never create worktrees inside the repo directory"; `:2295` "Clean before you start"; `:2297` "Prune after cleanup"). The design follows the ecosystem convention for the worktrees it creates (§7.1) and names the one place it does not (D-2).

### 2.5 How design paths carry status today

627 tracked markdown files under `notes/` (Lane A1, `find notes -name '*.md'`); the naming convention is ratified but ungated. **The header Status is not a controlled vocabulary**: 153 distinct leading tokens over 366 docs that carry a Status in their first 30 lines (261 do not); 42 of those headers use `**Status:**` (colon inside the bold) and 3 plain `Status:`, which a `**Status**:`-only regex misses (Lane B2). Lane B1 applied v2's class rules to 629 notes: 20 headers whose leading token is an ACTIVE-class word were classified terminal by a later word in the line — among them V3 itself ("DESIGN, revision 2. Revision 1 was REJECTED …") and "Analysis — owner decisions required, nothing implemented" — so a terminal keyword *anywhere* in the line is not a usable transition signal (§4.3). There is no `Superseded-by` field anywhere; supersession is a banner in the older doc or a `**Supersedes…**:` header line in the newer one (18 such lines, 3 in the exact spelling). Owner decisions are per-document tables whose rulings are appended with the chosen and rejected options (defect register §2.4, `:325-326`); decision ids are local to each document (every arc has a D-1). The live state of an arc sits in its handoff chain (210 handoffs). Edits are effectively append-only: the Sequence Safety docs screen (`juniper-ci-tools/juniper_ci_tools/docs_additions_check.py`) fails a PR that deletes a heading unless the same hunk adds one, or deletes ≥5 consecutive lines with no adjacent addition, absent an `Allow-Docs-Rewrite: <path>` trailer.

Design consequence: the goal ledger holds an **explicit, owner-owned class** per path; the document's prose is read only for two unambiguous transition signals (§4.3).

---

## 3. Architecture

### 3.1 The shape (v3)

```text
 owner (interactive sessions, bypass mode)                              GitHub
   │ rules decisions; merges PRs                                          ▲ PRs (API-signed commits)
   ▼                                                                      │
 systemd --user timer  util/systemd/juniper-dispatch.timer (every 10 min; zero tokens when idle)
   └─ util/dispatch/dispatch_tick.py   (pure code; exit 0 ran / 1 no usable result / 2 misuse / 3 REFUSED BY DESIGN)
        1. reconcile  conf/design_paths.yaml  (goal ledger, §4)
        2. read       ~/.claude/juniper-dispatch/usage_state.json  (odometer, §5) + calibration.json + controller_state.json
        3. decide     allowance, window, in-flight, selection (§8)  → exit 3 if nothing dispatchable
        4. create     one ecosystem worktree per selected task IN THE TASK'S REPO; manifest rows (§7.1)
        5. launch     claude -p "/juniper-cycle <plan path>" --output-format stream-json --verbose --session-id <uuid>
                      in the juniper-ml MAIN checkout, run dir under ~/.claude/juniper-dispatch/cycles/<stamp>/  (§6.1)
                      └─ the saved workflow runs the per-task pipeline: prompt → validate → execute → verify → maintain
        6. apply      cycle_report from the child's result → ledger, manifest, decisions, cycle record (§6.9, §9)
        7. notify     owner: cycle record appended on the docs branch + cross-session message to live sessions (§9.2)
 heartbeat (interactive, only outside the owner's hours): keeps the odometer fresh at ~one turn per 45 min (§5.1)
```

Six components, each a single-PR roadmap step (§11): **goal ledger** (§4), **usage odometer and calibration** (§5), **cycle workflow** (§6), **worktree manifest + reaper** (§7), **cadence controller** (§8), **decision routing** (§9). One rule governs the split: *everything that can be decided by code is decided by code, and agents are spent only on judgement*. In v3 the controller is entirely code and the only model-bearing process is the cycle child, which exists only while a cycle runs.

### 3.2 Why the controller is a timer and the cycle is a `-p` child running the saved workflow

v2 made the controller an interactive `/loop` session because it is the only surface where a running workflow *pauses* at a usage limit. Lane B1 refuted that choice on the design's own criteria (R1 Report B1 §3, Appendix E rows 9, 10, 16, 17): the pause is bounded (two waits per run, none for the weekly wall, none at all in three of the six surfaces), so §8 already forbids relying on it; every idle tick of an interactive dispatcher sends its full context (≥25 K tokens of `AGENTS.md` + parent `Juniper/AGENTS.md` + user `CLAUDE.md` before the first tool), which at the illustrative `k` of §8.3 costs as much per day as the loop dispatches; a self-paced loop must be re-armed after every resume; permission prompts stall the run unless the session bypasses them; the synchronised auto-continue of 8 sessions at a reset re-hits the wall; and the runtime's replay re-runs every agent started after a failed one. The timer surface has none of these and loses only the pause. What it keeps is the owner's stated primitive: the cycle child invokes the **saved dynamic workflow** by name, which is documented for `-p` ("Workflows are available in … non-interactive mode with `claude -p`"; the `Workflow(<name>)` allow rule "approves one saved workflow by name"; a `-p` process "stays open until that work completes").

| Criterion | v2: interactive `/loop` dispatcher | v3: timer → `-p` child running `/juniper-cycle` |
| --- | --- | --- |
| Idle cost | one full-context turn per tick (≥25 K tokens, cached only within the 1 h TTL) | zero: the tick is a Python process |
| At a 5-hour limit | run pauses (≤2 waits, interactive only); killed subagents resumable by `SendMessage` (Agent tool; undocumented for workflow agents) | affected agents fail → `null` → the task is re-queued at `resetsAt` (parsed from `system/api_retry` / the result text); the child's own session can be `--resume`d to finish an unfinished turn |
| At the weekly wall | identical: nothing waits; one-shot cron vs. the timer's next tick after `resetsAt` | identical |
| Permissions | prompts surface in the dispatcher and pause the run unless bypass | `--dangerously-skip-permissions`, the mode every `claudey` session already runs in, or `--permission-mode` + allow rules with `--permission-prompts none` (v2.1.259+) |
| Worktrees | `isolation: worktree` = juniper-ml only; agents' cwd fixed | code-created ecosystem worktree per task in the task's repo, absolute paths in every brief; no isolation checks in the child (it launches from the main checkout, edits nothing there) |
| Replay / idempotence | the runtime replays failed-and-later agents inside the session | each cycle is a fresh run; idempotence comes from deterministic branch names and DUP-GUARD (§6.5) |
| Handoff | needed after N ticks (context growth) | none: the controller has no context; each child starts fresh |
| Owner visibility | `/workflows` live view | the run directory (`stream.jsonl`, `status.json`) and the cycle record; no live view |
| Odometer | refreshed by the dispatcher's own turns | needs an interactive heartbeat when no owner session is live (§5.1) |
| Precedent in repo | none | SOAK (`util/soak_run_probe.py`, timer unit, exit-code contract) |

**D-1** presents both; the recommendation is v3's. The one property the timer cannot supply on its own — an odometer refreshed while every human session sleeps — is the heartbeat's job and costs about one small turn per 45 minutes (§5.1).

### 3.3 Rejected primitives

Agent Teams (experimental; no resumption after `/resume`; teammates share one checkout; ≈7× tokens; and while enabled any *named* subagent becomes a teammate, so `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` stays unset), background sessions as the controller (no pause, no wait menu, and the same idle-context cost), `/goal` as the loop driver (the condition "nothing dispatchable within the allowance" is computed by code for free), cloud Routines and Projects (cannot reach this host).

---

## 4. Goal ledger

### 4.1 File and schema

`conf/design_paths.yaml` (next to `conf/memory_budget.json`, `conf/soak_probes.json`, `conf/memory_index_baseline.json`); parameters live in `conf/dispatch.yaml` (§8.1). Version 1:

```yaml
version: 1
writers:                                  # the only writers; each owns the fields listed (Lane B2 P1-5)
  reconcile: [class, superseded_by, header_status, "tasks[].blocked_on (clear on ruling)"]
  apply_report: ["tasks[].state", "tasks[].pr", "tasks[].worktree", "tasks[].last_cycle", "tasks[] append PROPOSED"]
  owner: everything
paths:
  - id: DP-CASCOR-001                     # DP-<REPO token of the doc's filename>-<NNN>; never reused; split → -001a/-001b
    doc: notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md
    repo: juniper-cascor                  # the repo the tasks' worktrees are created in (§7.1)
    class: ACTIVE                         # ACTIVE | BLOCKED | COMPLETE | SUPERSEDED — owner-owned (§4.3)
    header_status: "ROADMAP — phases, steps, dependencies, concurrency and guardrails for cascor#573"
                                          # the doc's Status line verbatim (this one is list-form `- **Status**:`)
    superseded_by: null
    handoff: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md
    docs_branch: dispatch/docs/DP-CASCOR-001   # the long-lived branch every Maintain append lands on (§6.5)
    priority: 2
    decisions_open: []                    # qualified ids: "DP-CASCOR-001/D-P6.4"
    tasks:
      - id: DP-CASCOR-001/T1
        title: "P0.4 — envelope + marker harness: produce and validate the implementation prompt (planning-class; no code in the pilot)"
        source_section: "§3.1 P0.4"      # roadmap `:153` "P0.4 — the harness, in detail"; the 2026-09-22 handoff §0.1 says P0.4 blocks P2.1/P2.2
        class: planning
        size: S
        depends_on: []
        blocked_on: null
        prompt: generate                  # generate | prompts/generated/<file>.md
        state: READY                      # READY | RUNNING | PROMPT_VALIDATED | PR_OPEN | VERIFY_PENDING | LANDED | BLOCKED | PROPOSED | ABANDONED
        retries: 0                        # refutation returns; at 2 the task becomes BLOCKED on an owner review (Lane B2 row 6)
        pr: null
        worktree: null                    # manifest id (§7)
        last_cycle: null
  - id: DP-ECOSYSTEM-001
    doc: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
    repo: juniper-ml
    class: ACTIVE
    header_status: "Living register — …"    # copied verbatim at seeding
    docs_branch: dispatch/docs/DP-ECOSYSTEM-001
    priority: 3
    tasks:
      - id: DP-ECOSYSTEM-001/T1
        title: "APD-ML-005 — re-derive the open finding at current HEAD and append a dated verification note (analysis-class)"
        source_section: "§4 row APD-ML-005"
        class: analysis
        size: S
        prompt: generate
        state: READY
```

The ledger holds no prose; `header_status` is a verbatim copy that the drift check compares against the document's current header, read with `^\s*(?:[-*]\s+)?\*\*Status:?\*\*:?` over the first 30 lines (bold, list-form, and the `**Status:**` spelling 42 documents use). Runtime state (`usage_state.json`, `calibration.json`, `controller_state.json`, `worktrees.json`, `cycles/`) lives under `~/.claude/juniper-dispatch/`, **outside every repository**, so no tick dirties a checkout (`docs/REFERENCE.md:2295`; Lane B2 §3-2, P0-2).

### 4.2 Seeding

The initial goal set is the owner's pick from the arc table in INV I3 §3 (eleven arcs, each with its main document and latest handoff). Pilot recommendation (D-9): the two entries above — the logging roadmap's P0.4 as a planning-class task whose deliverable is a validated prompt, and one register row as an analysis-class task — so the first cycles exercise every stage without opening code PRs. Perf lane, backup migration and container registry are excluded because each is owner-gated on host actions.

### 4.3 Reconciliation (R4): how the goal set updates

`util/dispatch/design_path_ledger.py reconcile` runs at the start of every tick and, as `reconcile --check`, in CI (`tests/test_design_path_ledger.py`). It changes `class` in exactly three cases; everything else is a **drift flag** surfaced to the owner and never a guess (v2's "terminal keyword anywhere in the line" rule is withdrawn: Lane B1 #3 measured it retiring 20 live documents):

1. **Supersession, from the successor.** A tracked note whose header carries `^\*\*Supersedes\b[^*]*\*\*\s*:` (qualified spellings count) naming a ledger `doc` marks that entry `SUPERSEDED` with `superseded_by` set and its `READY` tasks `ABANDONED`; a parenthetical qualifier such as `(on ratification)` is recorded as *conditional* and does not flip the class.
2. **The design's own append form.** A header Status line that **ends** with ` — (COMPLETE|SUPERSEDED) \d{4}-\d{2}-\d{2}$` — the only form the doc-maintainer writes (§4.4) and one no existing header uses — flips the class accordingly. Any other terminal-looking word, anywhere, is a drift flag.
3. **Task exhaustion with no proposals.** `apply_report.py` marks a path `COMPLETE` only when its `tasks[]` has no `READY`/`RUNNING`/`VERIFY_PENDING`/`PR_OPEN`/`BLOCKED` entry **and no `PROPOSED` entry** (Lane B1 #2); new tasks enter as `PROPOSED` from the doc-maintainer's `tasks_proposed[]` (§6.5) and the owner promotes them to `READY`.

`--check` exits 1 when `header_status` differs from the current header of any entry without a recorded drift flag, and it checks that every `doc`, `handoff` and `prompt` path exists (the archive test `tests/test_thread_handoff_archive.py` scans only top-level `notes/*.md`, never `conf/`). The `handoff` field is maintained by the owner or by a `PROPOSED` update from the maintainer; the reconciler does not guess which newer handoff belongs to which path (Lane B2 P1-7). A `COMPLETE` or `SUPERSEDED` path is never selected and its worktrees become removal candidates (§7.3). The reconciler never edits a design document.

### 4.4 Keeping documents current (R3)

The doc-maintainer appends, under the task's `source_section`, one line per state change in the register's proven shape, `**<STATE> (<pr or cycle id>)** — <one sentence>`, on the path's `docs_branch` (§6.5), and bumps `Last Updated`. It never rewrites or deletes (the docs screen would fail the PR, and append-only is what keeps rulings distinguishable from drift). When a path transitions class, the maintainer appends ` — COMPLETE <date>` (or `SUPERSEDED`) to the existing Status line: that suffix is §4.3 case 2's only trigger. What the document does **not** show, by design: tasks dropped, deferred or `ABANDONED` are tracked in the ledger only; the document on `main` lags the docs branch by one owner merge.

### 4.5 Status map

`conf/design_path_status_map.yaml` classifies a *new* entry the owner seeds without a class, and labels drift flags; it never changes a class. Rules are ordered regexes over the whole line, first match wins, precedence SUPERSEDED → BLOCKED → COMPLETE → ACTIVE:

```yaml
version: 1
rules:
  - {class: SUPERSEDED, pattern: '\bSUPERSEDED\b(?! IN PART)|\bREJECTED\b|\bWITHDRAWN\b'}
  - {class: BLOCKED,    pattern: '\bBLOCKED\b|\bAWAITING\b|\bOWNER DECISION\b|\bPENDING\b|\bDRAFT\b|\bDECISION BRIEF\b|\bNOT RATIFIED\b'}
  - {class: COMPLETE,   pattern: '\bCOMPLETE\b(?!\s*\(SOAK\))|\bSHIPPED\b|\bCLOSED\b|\bDISCHARGED\b|\bRESOLVED\b|\bSETTLED\b|\bCERTIFIED\b|(?<!NOT )\bIMPLEMENTED\b'}
  - {class: ACTIVE,     pattern: '\bACTIVE\b|\bDESIGN OF RECORD\b|\bPLAN OF RECORD\b|\bDESIGN\b|\bPLAN\b|\bROADMAP\b|\bRATIFIED\b|\bADOPTED\b|\bACCEPTED\b|\bAPPROVED\b|\bIN PROGRESS\b|\bVALIDATED\b|\bREADY TO EXECUTE\b|\bOPEN\b|\bLIVING REGISTER\b|\bANALYSIS\b|\bFINDINGS\b|\bAUDIT\b|\bEVIDENCE\b|\bRESULTS\b'}
```

A line no rule matches is `UNMAPPED`; `tests/test_design_path_ledger.py` reports the UNMAPPED and dual-match shares over the Aug/Sep notes (Lane A3 measured 52–74 % unmapped under v1's table; the residue is why the class is owner-owned).

---

## 5. Usage odometer and calibration

### 5.1 Writer, merge rule, heartbeat

`util/dispatch/statusline_usage_writer.bash` is installed as the `statusLine` command in `~/.claude/settings.json` by `util/install_agents.bash --install-statusline`, which merges `{"statusLine": {"type": "command", "command": "<absolute path>", "refreshInterval": 60}}` with `jq -s '.[0] * .[1]'` into a temp file and `mv`s it, refusing if `statusLine` already exists unless `--force`. On every render it reads stdin and writes **its own session's** file `~/.claude/juniper-dispatch/sessions/<session_id>.json` atomically (`mktemp` + `mv`), then recomputes the shared `~/.claude/juniper-dispatch/usage_state.json` by merging every session file:

```json
{"schema_version": 2, "merged_at": 1790120000,
 "five_hour": {"used_percentage": 60.0, "resets_at": 1790134800, "seen_at": 1790119800, "from_session": "<uuid>"},
 "seven_day": {"used_percentage": 41.2, "resets_at": 1790218800, "seen_at": 1790119800, "from_session": "<uuid>"},
 "sessions": 3}
```

Merge rule per window (Lane B1 #5, Lane B2 P0-3): among session files whose `resets_at` equals the newest `resets_at` seen, take the **maximum** `used_percentage` (usage is monotone within a window; a stale re-render can only be lower); a session file whose window has passed is ignored; `seen_at` is the time that session's *values* last changed (`payload_hash` differs), not the time its script ran. Three further rules, each from a documented behaviour: (a) when `rate_limits` is absent (before the first API response) the script writes nothing about the windows and prints `limits n/a`; (b) when a window is absent because its `resets_at` passed, the session file keeps the last value with `reset_seen: true`; (c) `context_window.used_percentage` goes to the session file only, never to the shared file (it is that session's context). Lane A3 built and timed the single-writer version on this host: `jq` 1.8.1, 42–124 ms per render.

**Heartbeat.** The percentages change only on API responses, and only interactive sessions render the status line (§2.2). During the owner's hours their sessions refresh the file; outside them, `util/dispatch/heartbeat.bash` starts `claude` in `~/.claude/juniper-dispatch/heartbeat/` (an empty directory: no project `AGENTS.md`, so the turn carries only the user `CLAUDE.md`) with `/loop 45m` and a one-word prompt, so one small turn per 45 minutes keeps the odometer fresh inside the cache TTL. This is the one interactive process the design needs, and its cost is the price of Signal 2.

### 5.2 Reader and fallback

`util/dispatch/usage_state.py read(max_age_s=600)` measures age from the newest `seen_at`. When stale or absent it falls back to the transcript signal over `~/.claude/projects/*/*.jsonl` and `~/.claude/projects/*/*/subagents/*.jsonl`, which yields `resetsAt` per window for the newest recorded hit and nothing else: it can say "unknown", never a percentage, and never "no hit" (§2.1). When the fallback yields a future `resetsAt` for a window, the controller treats that window as at its wall until then (§8.2). The real-time signal for a hit inside a cycle is the child's stream: `system/api_retry` events with `error: rate_limit` and the failure text `You've hit your session limit · resets HH:MMam/pm (America/Chicago)`, which `apply_report.py` parses with the same Chicago rendering the `quotaLimits` text uses.

### 5.3 Calibration: tokens per percent, measured actively, class-resolved

`k_w`, the tokens the account may spend per percentage point of window `w`, has no default (Lane A3 F3) and cannot be identified from passive account-wide sums: cache reads draw usage "at the cached token rate", the owner's all-day sessions serve "91 % of input tokens from cache" while the dispatcher's agents are fresh-context and thinking-heavy, and usage from other devices or claude.ai is inside `Δused_percentage` but not in any local transcript (Lane B1 #8). The design therefore calibrates **actively**: in a quiet `dispatch_window` (§8.1) with no owner session live, `util/dispatch/calibrate.py` records `used_percentage` before, runs one known S-class agent (`claude -p`, fixed prompt, fixed effort), reads its transcript's `message.usage` totals by class (uncached input, cache creation, cache read, output), records `used_percentage` after from the heartbeat's next render, and stores the burst; a handful of bursts across both windows fits the four per-class weights `ω_c` and `k_w` by least squares with a residual `σ_w`. Passive samples (Δu between consecutive heartbeat renders, tokens from all local transcripts since the previous render, byte cursors kept in `calibration.json`) are recorded too, but only to monitor **drift** of the external term, never fitted into `k`; a sample containing a reset is discarded. `calibrate.py` runs at most once per 5 minutes, never per render. **The controller refuses to dispatch until `calibration.json` holds ≥5 bursts per window with `σ_w / k_w ≤ 0.35`** (`calibration: none | provisional | ok`); a refusal is a logged outcome (exit 3), a guessed `k` is not.

---

## 6. The cycle workflow

### 6.1 Saved script and invocation

`.claude/workflows/juniper-cycle.js` (project workflow, invoked as `/juniper-cycle`; `args` arrives as a JSON value). `meta` is a pure literal with `phases: [Prompt, Validate, Execute, Verify, Maintain]`. The tick launches, from the juniper-ml **main checkout** (the child edits nothing there; every write goes to a task worktree or through the API):

```bash
CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=4 CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 \
claude -p "/juniper-cycle ~/.claude/juniper-dispatch/cycles/<stamp>/plan.json" \
  --output-format stream-json --verbose --session-id <uuid> --dangerously-skip-permissions
```

with `ANTHROPIC_API_KEY` unset (SOAK), a run directory holding `plan.json`, `task.txt`, `meta.json`, `stream.jsonl`, `status.json` and a pidfile, and the `Workflow(juniper-cycle)` allow rule in the main checkout's `.claude/settings.local.json` for the non-bypass variant (D-1). The concurrency cap is the run-rate brake (§8.4). The workflow's `return` value is the cycle report; the tick reads it from the child's final `result` message in `stream.jsonl` (`apply_report.py --stream`), so nothing re-emits it (Lane B2 P2-8).

### 6.2 The script (helpers and schemas in the same file; a script may not `import`)

```javascript
export const meta = { name: 'juniper-cycle', description: 'One paced dispatch cycle over the design-path ledger',
  phases: [{title:'Prompt'},{title:'Validate'},{title:'Execute'},{title:'Verify'},{title:'Maintain'}] }

// ---- schemas (JSON Schema; root object; required ⊆ properties) ----
const PROMPT_OUT  = { type:'object', required:['prompt_path','bundle_path','template_id','escalate'],
  properties:{ prompt_path:{type:'string'}, bundle_path:{type:'string'}, template_id:{type:'string'},
               escalate:{type:'boolean'}, escalation_reason:{type:'string'} } }
const VERDICT     = { type:'object', required:['validator_status','head_sha','iteration','findings','hallucination_risk','overall'],
  properties:{ validator_status:{type:'string'}, head_sha:{type:'string'}, iteration:{type:'integer'},
               findings:{type:'array'}, hallucination_risk:{type:'array'}, overall:{type:'string', enum:['PASS','FAIL']} } }
const EXEC_OUT    = { type:'object', required:['pr','head_sha','files','tests_run','tests_passed','decisions_raised'],
  properties:{ pr:{type:['string','null']}, head_sha:{type:['string','null']}, files:{type:'array'},
               tests_run:{type:'integer'}, tests_passed:{type:'integer'},
               decisions_raised:{type:'array', items:{type:'object', required:['id','question','why_not_defaultable'],
                 properties:{id:{type:'string'}, question:{type:'string'}, why_not_defaultable:{type:'string'}, options:{type:'array'}}}} } }
const REFUTATION  = { type:'object', required:['lens','refuted','evidence','severity'],
  properties:{ lens:{type:'string'}, refuted:{type:'boolean'}, evidence:{type:'array'}, severity:{type:'string'} } }
const MAINTAIN_OUT= { type:'object', required:['doc','appended_lines','docs_pr','tasks_proposed'],
  properties:{ doc:{type:'string'}, appended_lines:{type:'integer'}, docs_pr:{type:['string','null']},
               tasks_proposed:{type:'array', items:{type:'object', required:['title','source_section','class','size'],
                 properties:{title:{type:'string'}, source_section:{type:'string'}, class:{type:'string'}, size:{type:'string'}}}} } }
const LENSES = ['re-probe', 'conclusion', 'amputation']
const lensesFor = t => t.class === 'execution' ? LENSES : ['re-probe']          // CON §3 sizing: docs/analysis tasks get one refuter

// ---- briefs: every rule an agent needs is NAMED; absolute worktree paths come from plan.json ----
const RULES = 'Rules: never merge; never delete a worktree; never put a CI-skip marker in a commit message or PR; ' +
  'the PR body carries a "## Requirements" section with JR ids where the requirements index has them and names every document changed; ' +
  'if a shell command is refused by an isolation check, write it to a script under your evidence directory and run that.'
const promptWriter  = t => `Follow .claude/skills/template-agent/SKILL.md steps 1-5 by reference for task ${t.id} (${t.title}), working in the worktree ${t.worktree_path} (repo ${t.repo}, HEAD ${t.base_sha}). Discovery bundle already at ${t.bundle_path} (run by the tick; re-run cli.py yourself only if it is older than 900 s). Write the prompt to ${t.prompt_path}. If the procedure would ESCALATE_TO_PAUL, return escalate=true with the reason instead of asking. ${RULES}`
const validatorBrief= (p, t) => `Validate ${t.prompt_path} against prompts/agent_templates/RUBRIC.md with bundle ${p.bundle_path}; target worktree ${t.worktree_path}, expected head ${t.base_sha}. Return only the verdict JSON; write a copy to ${t.evidence_dir}/verdict.json.`
const executorBrief = (v, t) => `Execute the validated prompt ${t.prompt_path} for task ${t.id} in the worktree ${t.worktree_path} on branch ${t.branch} (base ${t.base_sha}). Land the change with util/open_signed_pr.py --branch ${t.branch} --expect-base ${t.base_sha} (reuse the branch and PR if they exist). Before returning, write your EXEC_OUT JSON to ${t.evidence_dir}/exec_out.json. If you hit a genuine owner decision, commit WIP locally with -c commit.gpgsign=false, do not push, and return it in decisions_raised with the question and the options. ${RULES}`
const refuteBrief   = (x, t, lens) => `Lens ${lens}: try to refute the result of task ${t.id} (PR ${x.pr}, head ${x.head_sha}) from the worktree ${t.worktree_path} and the PR diff, never from any report. Default to refuted=true when uncertain. ${lens === 're-probe' ? 'Re-derive every path, symbol, number and test claim.' : lens === 'conclusion' ? 'Grant the premises; attack whether the deliverable meets the acceptance criteria and whether the tests could catch a wrong implementation.' : 'List what the task asked for that the PR omits, and what the PR contains that the task did not ask for.'}`
const maintainBrief = (r, t) => `In the worktree ${t.docs_worktree_path} (branch ${t.docs_branch}, the path's long-lived docs branch), append to ${t.doc} under ${t.source_section} one state line **<STATE> (<pr>)** — <sentence> for task ${t.id} (${r.launched} refuters launched, ${r.votes.filter(v => !v.refuted).length} not refuted${r.decision ? '; decision raised: ' + r.decision.id : ''}). ${r.decision ? 'Also append the decision row (id, question, why it cannot be defaulted, options) to the document\'s decision table.' : ''} If the document\'s next steps changed, list them in tasks_proposed; never rewrite or delete existing text; bump Last Updated; land with util/open_signed_pr.py --branch ${t.docs_branch} --append (reuse the open docs PR). ${RULES}`

// ---- the pipeline: no barrier between stages; a stage that THROWS drops the item to null and skips the rest;
// ---- a stage that RETURNS null (validator FAIL, decision raised) still reaches later stages, which guard on it ----
const plan = args
const results = await pipeline(plan.tasks,
  t => t.prompt === 'generate'
        ? agent(promptWriter(t), {phase:'Prompt', label:`prompt:${t.id}`, schema: PROMPT_OUT, effort:'high'})
        : Promise.resolve({prompt_path: t.prompt_path, bundle_path: t.bundle_path, template_id: 'given', escalate: false}),
  (p, t) => p.escalate ? {decision: {id: `${t.path_id}/D-escalation-${t.id}`, question: p.escalation_reason, why_not_defaultable: 'ESCALATE_TO_PAUL', options: []}}
        : agent(validatorBrief(p, t), {phase:'Validate', label:`validate:${t.id}`, agentType:'prompt-validator', schema: VERDICT}),
  (v, t) => (v == null || v.decision || v.overall !== 'PASS') ? (v && v.decision ? v : null)
        : t.class === 'execution' || t.class === 'analysis' || t.class === 'planning'
          ? agent(executorBrief(v, t), {phase:'Execute', label:`exec:${t.id}`, agentType:'dispatch-executor', schema: EXEC_OUT})
          : {pr: null, head_sha: null, files: [], tests_run: 0, tests_passed: 0, decisions_raised: [], prompt_validated: true},
  (x, t) => x == null ? null
        : x.decision || (x.decisions_raised && x.decisions_raised.length)
          ? {x, votes: [], launched: 0, decision: x.decision || x.decisions_raised[0]}
          : parallel(lensesFor(t).map(l => () => agent(refuteBrief(x, t, l), {phase:'Verify', label:`verify:${l}:${t.id}`, schema: REFUTATION, effort:'high'})))
              .then(vs => ({ x, votes: vs.filter(Boolean), launched: lensesFor(t).length })),
  (r, t) => r == null ? null
        : agent(maintainBrief(r, t), {phase:'Maintain', label:`doc:${t.id}`, schema: MAINTAIN_OUT, effort:'medium'}))
log(`${results.filter(Boolean).length}/${plan.tasks.length} tasks reached Maintain`)
return { cycle_id: plan.cycle_id, tasks: results, dropped: plan.tasks.filter((t, i) => !results[i]).map(t => t.id) }
```

Top-level `return` is the documented shape of a workflow body (the docs' saved-script example ends with `return audits.filter(Boolean)`). A decision raised at Prompt or Execute short-circuits Verify and reaches Maintain with `decision` set, so the decision row is written and no refuter attacks a null PR (Lane B1 #15, Lane B2 row 12). **Standby**: `plan.json` may carry `standby[]`; the tick launches a second, smaller child for the first standby task when a primary task's evidence directory shows a decision exit before Execute completed, so a freed cost is spent in the same cycle (R8).

### 6.3 Prompt stage (R1, "if necessary")

The discovery bundle is produced **by the tick** (`cli.py` is pure code) for every task, in the task's worktree at `base_sha`, and its path is in `plan.json`; the prompt-writer re-runs it only when the bundle is older than the rubric's TTL. For `prompt: generate` tasks the writer follows `SKILL.md` steps 1–5 by reference and writes the prompt to the path the tick pre-assigned per `conventions.yaml:23` (`PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md`), inside the task worktree so it lands with the task's PR. For `prompt: <path>` tasks the stage is skipped and the validator still runs — with the fresh bundle, so `bundle.head_sha` = the worktree's HEAD = the executor's base, which closes Lane B1 #1 (v2 validated against the dispatcher's HEAD and executed against a different one). The rubric's freshness rule is the reason: "reject the bundle (set `validator_status` accordingly) if `bundle.head_sha` ≠ current HEAD or the bundle exceeds its TTL; the Skill must re-discover before re-validating" (`RUBRIC.md:163-164`). Bundles and verdicts are saved under the cycle's evidence directory; today neither is persisted anywhere.

### 6.4 Verify stage: consensus inside the loop

Refuters per task come from `lensesFor(t)`: execution-class tasks get three lenses (**re-probe**: re-derive every claim from the worktree and the PR diff; **conclusion**: grant the premises and attack the deliverable against its acceptance criteria; **amputation**: what was asked and omitted, what was delivered and not asked), docs/analysis/planning tasks get one (CON §3 sizing). Rule: `PR_OPEN` requires every launched refuter to have returned and at least ⌈launched/2⌉+… concretely 2 of 3, or 1 of 1, `refuted: false`. A refuter that died (null) does **not** count as a refutation (v2's rule turned a usage-limit death into a correctness verdict, Lane B1 #17); the task goes to `VERIFY_PENDING` with its `pr`/`head_sha` kept and re-enters at Verify next cycle. A refuted task returns to `READY` with `retries += 1`, the PR left open and labelled `needs-rework`; at `retries == 2` the task becomes `BLOCKED` on an owner review (Lane B2 row 6). Refuters run with CLAUDE.md loaded (they need the hazards) and without the executor's report until they have re-derived the facts.

### 6.5 Execute and Maintain stages

**Execute** runs `dispatch-executor` — a copy of `task-executor` without `isolation: worktree` (the frontmatter field would create a juniper-ml worktree regardless of the task's repo), pinned opus/max like every agent — in the code-created worktree named in the brief, on branch `dispatch/<task-id>` (deterministic, so a replayed or re-queued executor finds the branch and the DUP-GUARD refuses a duplicate PR instead of opening one). It lands the change through `util/open_signed_pr.py` with two modes this design adds to that script (P4, with tests): `--expect-base <sha>` refuses when the remote base has moved **and** GitHub's compare shows any `--add` path changed between `base_sha` and the current base (the v2 pre-check compared two local refs that API pushes never advance, Lane B1 #12), and `--reuse` returns the existing PR when the branch and an open PR already exist. After the upload the executor resets its local branch to the remote (`git fetch origin dispatch/<task-id> && git reset --hard FETCH_HEAD`) so the worktree carries the API-minted commits and V3's B1 sees nothing unpushed. It writes `exec_out.json` to the evidence directory **before** returning, so a structured-output failure after the PR exists loses nothing (Lane B1 #18). A raised decision ends execution with a local WIP commit (`-c commit.gpgsign=false`, never pushed).

**Maintain** runs in the path's **docs worktree**, a second code-created worktree on the long-lived branch `dispatch/docs/<DP-id>` that every cycle appends to (v2 opened a fresh whole-file PR per cycle from `origin/main`, so each cycle's append conflicted with the previous unmerged one, Lane B1 #4). The open docs PR for that branch stays open across cycles; the owner merges it when they choose; `open_signed_pr.py --append` (P3) commits on the existing branch with `expectedHeadOid` = that branch's head. It appends the state line, the decision row when one was raised, and `tasks_proposed[]` for the ledger; the same PR carries the cycle record (§6.9) and the ledger diff, which is the one-PR-per-work-unit answer for a cycle's documentation (`standing_rules.yaml:14`).

### 6.6 Merge readiness (owner-side)

The workflow never merges. When a tick finds a task's PR `OPEN` with checks green (`util/wait_for_checks.py --json`, reading `status`), it runs `predict_merge.py --pr N --json` and lists the PR to the owner with its verdict. Merging remains the owner's explicit act (`standing_rules.yaml:6`).

### 6.7 Isolated headless children, when a task must be unprimed

A task that must not inherit any context (a scorer, a blind re-measure) is itself run as a `claude -p` child in the SOAK shape from inside the Execute stage, with the exit-code contract `0 / 1 / 2 / 3 refused by design`; the child reads the odometer too and refuses to spend a session past the allowance.

### 6.8 Token efficiency, by mechanism

| Mechanism | Effect | Source |
| --- | --- | --- |
| Code before agents: reconcile, plan, discovery, worktree creation, manifest, gates, report application are scripts | zero tokens for every decision that is a comparison, and zero tokens while idle | §3.1 |
| The cycle child is the only model process; it starts fresh each cycle | no accumulating context, no handoff | §3.2 |
| `schema` on every `agent()`; the report is read from the child's stream | no prose returns; nothing re-emitted through an orchestrator | §6.1 |
| `effort` per stage: `high` for prompt-writer and refuters, `medium` for doc-maintainer | thinking tokens are billed as output tokens | costs |
| `lensesFor(t)`: one refuter for docs/analysis/planning tasks, three for execution tasks | the largest per-task cost scaled by CON §3 | §6.4 |
| Same-shaped agents launched together share the prompt-cache prefix; `subagentPromptCacheTtl: 1h` in user settings (installed by `--install-statusline`) | the refuters and executors read one cached prefix | workflows |
| `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=4` | bounds the burn rate (§8.4) | workflows |
| Reports archived by copying from transcripts (`util/ad-hoc/2026-09-23_archive_subagent_reports.py`, which lands with this PR) | ~100 K characters of R1 and INV archived at zero orchestrator output | §6.9 |

### 6.9 Evidence trail per cycle

`~/.claude/juniper-dispatch/cycles/<stamp>/` holds the run directory, `plan.json`, the child's `stream.jsonl`, `report.json` (extracted), per-task `bundle.json`, `verdict.json`, `exec_out.json`, `refutations.json`. The cycle report is appended verbatim to `notes/JUNIPER_<date>_JUNIPER-ML_DISPATCH-CYCLE-RECORD.md` (one file per day) on the docs branch by the maintainer, after `util/dispatch/secret_screen.py` (P3; the repo has no gitleaks hook — `.pre-commit-config.yaml` carries `detect-private-key` and the SOPS `no-unencrypted-env` hook only). Runtime state outside the repo follows `~/.claude`'s own retention; the roadmap adds an explicit cap (P8).

---

## 7. Worktrees: created by code, fresh per task, removed only under V3 as amended

### 7.1 Fresh worktree per editing agent (R6)

For every selected task the tick creates, **before the child starts**, one worktree in the task's repo at the ecosystem location and naming (`git -C <repo> worktree add <Juniper/worktrees/<repo>--dispatch--<task-id>--<YYYYMMDD-HHMM>--<hash8>> -b dispatch/<task-id> origin/<default>` after a fetch), and for every path with a Maintain step one docs worktree on `dispatch/docs/<DP-id>`. The manifest row is written **by the code that created the tree**, so its identity is never the agent's word (Lane B1 #14):

```json
{"id": "WT-2026-09-23-0001", "task": "DP-CASCOR-001/T1", "cycle": "<stamp>", "repo": "juniper-cascor",
 "path": "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--dispatch--DP-CASCOR-001-T1--20260923-0300--a1b2c3d4",
 "branch": "dispatch/DP-CASCOR-001/T1", "base_sha": "<origin/main at creation>", "created_at": 1790120000,
 "pr": null, "state": "CREATED", "removal_order": null}
```

Agents receive absolute paths and edit nothing elsewhere; the child launches from the main checkout, so no isolation check interferes (§3.2). Read-only stages (validator, refuters) need no worktree of their own. A decision-blocked task's redo reuses its worktree (the path is in the ledger row), which is the one intended non-fresh case (§9.3). **D-2** records that the ecosystem rule "Never create worktrees inside the repo directory" is honoured for everything the design creates, while Claude Code's own `isolation: worktree` (which `task-executor` already uses today) is not used by the dispatcher at all.

### 7.2 What "arc complete" means for a worktree

A task reaches `LANDED` when the PR the manifest names reports `state == "MERGED"` with non-null `mergedAt` (`gh pr view --json state,mergedAt`), the docs branch commit carrying its state line has merged, and no other task references the worktree. Only then is `removal_order` set — later than V2's "after the PR is opened", and the explicit merge signal the standing rule requires, from the API rather than from a chat message.

### 7.3 Removal orders (R7), the reaper, and the V3 amendment

The workflow **specifies**; a script **executes**, never inside an agent. `apply_report.py` writes `removal_order` into the manifest row and the tick runs `util/dispatch/reap_worktrees.py --manifest … --dry-run`, which implements V3's gates as written — G1 not locked; G2 clean by the `--no-optional-locks … -uall` command, empty **and** exit 0; G3 ignored files judged by type, any `*.env` / SOPS-covered file refuses at any size; G4 HEAD and every per-worktree ref reachable, no rebase/merge/bisect in progress; G5 no nested repository; B1 nothing unpushed; B4 no armed auto-merge; V3 §6.5's admin-directory dump; V3 §7's 7-day recent-mtime veto — **with one amendment for B3**: "content landed" is tested by patch identity, `git diff origin/main...<branch> | git patch-id --stable` equal to the merged PR's squash commit's patch-id (`gh pr view --json mergeCommit`, then `git show <sha> | git patch-id --stable`), because the three-dot diff of a squash-merged branch is never empty (§2.4). The amendment is proposed to V3's owner as D-12; until V3 as amended is ratified, `--execute` does not exist and the owner message reports "N worktrees removable under V3-as-amended (dry-run passed)". Removal, when it exists, is `git worktree remove` without `--force`, `branch -d`, then `git worktree prune` (`docs/REFERENCE.md:2297`), reusing `util/worktree_cleanup.bash`'s stop-and-print sequence (`:427-431`).

### 7.4 Hazards the manifest and the executor path close

A worktree behind `origin/main` is a clobber source for a whole-file API upload; `--expect-base` (§6.5) makes the check remote-side, so a local `origin/main` that API pushes never advanced cannot pass it. A decision-blocked task's unpushed WIP commit fails B1 by design and keeps its tree alive until the owner rules. A crashed executor leaves a `CREATED` row with a path the code knows, distinguishable from a task dropped at Validate (whose row stays `PLANNED`).

---

## 8. Cadence controller: meeting the limits without hitting them

### 8.1 Definitions and parameters (`conf/dispatch.yaml`)

| Symbol / key | Meaning | Default |
| --- | --- | --- |
| `u_w`, `r_w` | odometer `used_percentage` and seconds to `resets_at` for window `w ∈ {five_hour, seven_day}` | fresh within `max_age_s` = 600 |
| `k_w`, `σ_w` | tokens per percent and residual SE, from active calibration (§5.3); no default | `calibration: ok` required |
| `reserve_w`, `slack_w` | headroom left for the owner's sessions; estimation slack | 10 / 15; 5 / 5 |
| `wall_w = 100 − reserve_w`; `target_w = wall_w − slack_w` | the plan never crosses the wall; the allowance drips toward the target at reset | 90 / 85; 85 / 80 |
| `H_w = max(0, target_w − u_w) × k_w` | headroom in tokens, recomputed every tick from the account-wide `u_w` (already net of everyone's consumption, so it is never debited for the owner's usage) | — |
| `d_w = H_w / r_w` | drip toward even pacing | — |
| `A_w` | allowance bucket: `A_w := min(H_w, max(0, A_w(prev) + d_w × Δt))`, `Δt` = seconds since the previous tick; on a reset, `A_w := 0` then accrue only from `resets_at_old` | persisted in `controller_state.json` |
| debit | `A_w −= tokens the cycle actually spent`, from the child's transcripts (Signal 3, class-weighted with the calibrated `ω_c`), never from `Δu × k` (which is account-wide, Lane B1 #6) | — |
| `A = min_w A_w` | the binding allowance | — |
| `c_i = class_tokens[size] × m` | cost estimate; `m = 1 + 2σ/k`, floor 1.2 | §8.3 |
| `D_i` | duration estimate | §8.3 |
| `dispatch_windows` | local time windows in which a cycle may start; empty = never | `[]` (D-5) |
| `timer_period` | the systemd timer's period | 600 s |
| `burn_cap` | the child's `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` | 4 |

### 8.2 The rule per tick (pure code; exit 3 = refused by design)

0. **Window.** If now is outside every `dispatch_windows` entry → exit 3 (`outside_window`).
1. **Freshness and calibration.** Odometer stale (newest `seen_at` older than `max_age_s`) and no fresh fallback reset → exit 3 (`odometer_stale`); a fallback reset in the future → that window is at its wall until then; `calibration ≠ ok` → exit 3 (`uncalibrated`).
2. **In flight.** A previous cycle's pidfile alive → exit 3 (`run_in_flight`); a dead pidfile with no `status.json` → apply what `stream.jsonl` holds, re-queue the rest, continue.
3. **Accrue.** Update `A_w`; `A = min_w A_w`; if `u_w ≥ wall_w` for any window, `A := 0`.
4. **Weekly wall.** If `u_seven_day ≥ target_seven_day` and `r_seven_day > 24 h` → exit 3 (`weekly_wall`); the timer keeps firing, and the first tick after `resets_at + 300 + jitter(≤600 s)` proceeds (the jitter avoids the synchronised re-hit of every auto-continuing session at the reset, Lane B1 #10).
5. **Select.** Walk `READY` and `VERIFY_PENDING` tasks in order (path `priority`, `depends_on` satisfied, oldest first), adding task `i` while `Σc ≤ A` and `max(D)` ≤ `r_binding − margin` (20 %; concurrent tasks overlap in time, so the guard uses the longest, not the sum); list the rest as `deferred: allowance | duration`. If nothing fits → exit 3 (`allowance`), with the estimated wait `(c_min − A) / d_binding` written to `status.json`.
6. **Dispatch.** Create worktrees, write `plan.json` (with `standby[]`), launch the child (§6.1), wait, apply the report, debit `A_w` by the measured spend, record a calibration drift sample, write the cycle record and owner message, exit 0 (or 1 when the child produced no usable result).
7. **Hit inside the cycle.** `system/api_retry` with `error: rate_limit` or a result naming a reset: parse `resetsAt`, set `A_w := 0` for that window, mark dropped tasks `READY`/`VERIFY_PENDING` with `not_before: resetsAt`, and `--resume` the child's session once after the reset if its turn was unfinished (documented for `-p`).

### 8.3 Size classes, durations, and a worked example

| Class | Tokens (chain incl. verify) | Duration | Basis |
| --- | --- | --- | --- |
| S | 250 K | 15 min | prompt-writer + validator + a docs/analysis executor + one refuter; this session's docs-facts agents cost 74 K / 115 K and ran 1–3 min |
| M | 900 K | 45 min | + code executor + three refuters; this session's inventory agents cost 337–358 K and ran 15–16 min each; the round-1 validators cost 225–305 K over ≈20–35 min each |
| L | 2.0 M | 120 min | + sub-agent fan-out inside the executor, or a document-of-record deliverable with round 2 |

**No execution-class run has been measured**; P8 replaces both columns with measured medians, and `c_M` can be estimated before then from the 558 existing `task-executor`-type transcripts (Lane B1 #19). Worked example, **illustrative only because `k` is unmeasured**: `u_5h = 23.5 %` with 4 h to reset, `u_7d = 41.2 %` with 3 days to reset, `k = 100,000` tokens/percent. `H_5h = (85 − 23.5) × 100 K = 6.15 M` over 14,400 s, `d_5h ≈ 427` tok/s; `H_7d = (80 − 41.2) × 100 K = 3.88 M` over 259,200 s, `d_7d ≈ 15` tok/s. The weekly bucket affords an S task (300 K with `m` = 1.2) after ≈5.6 h and an M task (1.08 M) after ≈20 h; the 5-hour bucket affords the same M in 42 min. Under that `k` the weekly window binds and throughput is roughly one M task per day: **the dispatcher's value would lie in using idle hours the owner does not, not in adding capacity**. A `k` ten times larger changes that tenfold; a smaller one argues for stopping at P0. That is D-10's question.

### 8.4 Bounding the run, not only the plan

The cap `H_w` bounds the plan; nothing in a workflow bounds the run's *rate* except concurrency (Lane B1 #7): at the measured ≈380 tok/s per agent, 14 concurrent agents burn ≈5.3 K tok/s and the 5-point slack in 94 s. The child therefore runs with `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=4` (≈1.5 K tok/s, the slack lasts ≈5 min at the illustrative `k`), the tick sizes `Σc` to the allowance, and the executor re-reads the odometer before any sub-agent fan-out. The documented in-run `budget` ceiling counts output tokens only and is set from the plan's allowance as a second brake.

### 8.5 Stopping rules

- Never dispatch on a stale odometer, an uncalibrated `k`, outside a window, into a reset, or with a cycle in flight.
- Never rely on a pause: none exists in the `-p` child; a hit fails the affected agents and the tick re-queues them.
- The weekly wall ends dispatch until `resets_at + 300 + jitter`; the owner is told once.
- Exit codes follow SOAK: `0` ran, `1` no usable result, `2` misuse, `3` refused by design (`SuccessExitStatus=3` in the unit, so a refusal never fires `OnFailure=`); the timer unit is `util/systemd/juniper-dispatch.{service,timer}` with `OnCalendar=*:0/10`.

---

## 9. Decision routing (R8)

### 9.1 Where a decision lives

A decision is a row in the **design document's own decision table**, appended on the docs branch by the doc-maintainer from the `decision` the pipeline carries (§6.2), with a qualified id `<DP-id>/<doc-local id>` echoed into the ledger's `decisions_open[]` and every blocked task's `blocked_on`. Rulings are appended later with chosen and rejected options (register §2.4). There is no separate inbox file.

### 9.2 What the owner receives

Each cycle's owner message lists: new decisions with the document and section that holds each, the task ids blocked on each, drift flags and `PROPOSED` tasks from the reconciler, PRs ready with their `predict_merge` verdict, worktrees that passed the V3-as-amended dry run, the allowance state per window, and the next possible dispatch time. It is delivered three ways (D-6): appended to the cycle record on the docs branch; posted as a cross-session message to every live owner session that is also in bypass mode (documented delivery rule; a script can post to a session's socket); and, when enabled, as a push notification. Nothing is asked mid-run. A ruling is given by editing the document's Rulings subsection or by telling any owner session, which appends it; the next tick's reconciler clears `blocked_on`.

### 9.3 Reassignment

The freed cost of a task that raises a decision is spent in the same cycle on a `standby` task (§6.2); the blocked task is excluded from selection until ruled; its worktree keeps the WIP commit. When the ruling lands, the task returns to `READY` with `prompt: generate` and is executed in the **same** worktree (its path is in the ledger row and the executor takes absolute paths), so the WIP is not orphaned (Lane B1 #15).

---

## 10. Owner decisions

| ID | Decision | Recommendation | Why it cannot be defaulted |
| --- | --- | --- | --- |
| D-1 | Controller surface: (a) interactive `/loop` dispatcher running the workflow in-session (v2), or (b) a systemd timer running a pure-code tick that launches a `claude -p` child per cycle, the child running the saved workflow (v3) | **(b)**, with `--dangerously-skip-permissions` as every `claudey` session already runs, teams off, `ultracode` off | (a) alone offers the pause, which is bounded and which §8.5 forbids relying on; (b) costs nothing while idle, needs no re-arm or handoff, and creates worktrees in the right repo; the owner loses the `/workflows` live view |
| D-2 | Worktree location for what the design creates: ecosystem `Juniper/worktrees/` with the naming convention (as specified) — and an explicit acknowledgement that Claude Code's native `isolation: worktree`, which `task-executor` uses today, puts trees inside the repo | **As specified**; no waiver needed for the dispatcher | the ecosystem rule "Never create worktrees inside the repo directory" |
| D-3 | Ledger shape: `conf/design_paths.yaml` with an owner-owned class, `conf/design_path_status_map.yaml`, `conf/dispatch.yaml` | **As specified** | it fixes where "the goal set" is and who may write it |
| D-4 | Worktree removal: dry-run only until V3 as amended is ratified | **Dry-run only now** | the repo has no safe remover; V3's own B1/B3 cannot pass on squash merges |
| D-5 | `reserve` (10 / 15), `slack` (5 / 5), `dispatch_windows`, and ratifying that "met" means the binding window reaching `target_w` while the other is under-used | **Defaults; windows = the owner's sleeping hours at first** | the windows are shared with 7–8 interactive sessions |
| D-6 | Decision delivery: cycle record + cross-session message to live bypass sessions + push | **All three** | reach vs noise |
| D-7 | (retired: no handoff relaunch exists in v3) | — | — |
| D-8 | Model/effort tiering: call-time `effort` overrides only vs relaxing the six frontmatter pins for a dispatcher agent set | **Call-time only for the pilot** | six CI tests; the saving is unmeasured |
| D-9 | Pilot goal set | **The two §4.1 entries**, docs/analysis/planning tasks only | the first cycles must exercise every stage without code PRs |
| D-10 | Go / no-go after measurement: inputs are the active-calibration `k_7d`, the end-of-window `u_7d` the owner's own sessions reach over ≥3 weekly windows, and `c_M` from existing executor transcripts; the resulting M-tasks-per-day figure decides whether P4–P8 are worth building | **Measure first; decide with the numbers**; below roughly one M task per day, stop at P0–P3 | the design's value hinges on unmeasured quantities and the owner alone hit the weekly wall in 3 of 4 weeks |
| D-11 | Invoking the `/template-agent` procedure from an unattended agent, although the skill is `disable-model-invocation: true` by SUITE's ratified design | **Allow for the dispatcher only**, by reference to `SKILL.md` steps, with the validator gate unchanged | a ratified suite decision is being widened |
| D-12 | Amend V3's B3 to the patch-id landed test (§7.3) and record the squash-merge finding in V3 | **Amend** | V3 is unratified and its author is the owner |

Rulings will be recorded in §10.1 (to be added) with the chosen and rejected options; the sections above are not rewritten.

---

## 11. Roadmap — single-work-unit PRs; P0, P1 and P3 can run in parallel now

Every step wires its tests into `ci.yml`'s regression job (`tests/test_ci_test_wiring_drift.py`), names every document it changes in its PR body, and carries `References JR-ML-*` ids where the index has them.

| Step | PR content | Depends on | Acceptance (tested in CI unless stated) |
| --- | --- | --- | --- |
| P0 | `util/dispatch/statusline_usage_writer.bash` (per-session files + merge rule), `usage_state.py`, `calibrate.py` (active bursts + passive drift), `heartbeat.bash`, `install_agents.bash --install-statusline` (settings merge, `subagentPromptCacheTtl`), `docs/REFERENCE.md` pointer, `tests/test_usage_state.py`, `tests/test_calibrate.py` (synthetic bursts → known `k` and `ω_c`; reset-straddling sample dropped; max-merge across session files) | none (**exempt from the §0 gate: it is the measurement D-10 needs**) | CI: the tests; manual, pasted into the PR: the file appears within one render, and after ≥3 days `calibration.json` reports `k_w`, `σ_w`, burst count per window |
| P1 | `conf/design_paths.yaml` (the two §4.1 entries), `conf/design_path_status_map.yaml`, `conf/dispatch.yaml`, `design_path_ledger.py reconcile [--check]`, `tests/test_design_path_ledger.py` (regex accepts the three header forms; only case 1 and case 2 change a class; `(on ratification)` is conditional; UNMAPPED share reported; every path exists) | D-3, D-9 | `--check` exits 1 on unrecorded drift; a fixture `Supersedes` line flips its target; the append form flips COMPLETE; a terminal word mid-line does not |
| P2 | `dispatch_tick.py` (steps 0–7 as pure code, emitting `plan.json`, `controller_state.json`, `next: {kind, at, reason}`), `apply_report.py --stream|--report`, the three JSON schemas (fenced in `docs/REFERENCE.md`), `tests/test_dispatch_tick.py` on Lane A3's fixtures (a)–(e) (R1 Report A3, Check 2) plus a calibrated case, a reset-between-ticks case, an in-flight case, and an outside-window case | P0, P1, D-5 | (a) with an illustrative `k` accrues and dispatches after the computed wait; (b) defers on duration; (c)/(d) exit 3 `weekly_wall`; (e) exit 3 `odometer_stale`; uncalibrated exit 3; a reset zeroes the bucket and accrues only from the reset |
| P3 | `.claude/workflows/juniper-cycle.js` with Prompt → Validate → Maintain only (docs pilot; state token `PROMPT_VALIDATED`), `open_signed_pr.py --append` with `tests/test_open_signed_pr.py` additions, `secret_screen.py` + test, `tests/test_juniper_cycle_script.py` (meta literal; phases match the `phase` strings; no `Date.now`; no `import`; every helper defined in-file; parses when wrapped as the runtime wraps it) | P2 | one manual cycle on the pilot set yields a validated prompt in the task worktree, a saved verdict, and an append on the docs branch |
| P4 | `.claude/agents/dispatch-executor.md`, the Execute stage, `open_signed_pr.py --expect-base` and `--reuse` with tests, the decision early-exit, `exec_out.json`; `tests/test_worktree_manifest.py`; exercised on a juniper-ml sandbox task (a `util/ad-hoc/` change), not on the pilot paths | P3, D-10 | a task ends with a `CREATED` row, a PR on `dispatch/<task-id>`, a re-queued executor finds the same PR, and a raised decision exits with WIP preserved and a decision row appended |
| P5 | Verify stage (`lensesFor`, the "every launched refuter returned" rule, `VERIFY_PENDING`, retries) | P4 | a fixture report with a fabricated path is refuted; a dead refuter yields `VERIFY_PENDING`, not `needs-rework` |
| P6 | `reap_worktrees.py --dry-run` implementing V3 G1–G5, B1, B4, V3 §6.5 dump, V3 §7 veto, the manifest gate and the patch-id landed test; `tests/test_reap_worktrees.py` with a tmp repo including a squash-merged branch and a 0-byte `.env` | P4, D-4, D-12 | every gate has a failing and a passing fixture; the squash-merged branch passes the landed test and fails V3's original B3; `--execute` absent |
| P7 | `util/systemd/juniper-dispatch.{service,timer}` (`SuccessExitStatus=3`), the standby child, the owner message and cross-session delivery, `heartbeat` scheduling | P2–P5, D-1, D-6 | a dry week on the pilot set with a run directory per cycle and zero tokens on idle ticks |
| P8 | measured medians replace the class table; `predict_merge` readiness screen; retention cap for `~/.claude/juniper-dispatch/` | P7 | per-class medians and the drift monitor reported after 20 cycles |
| P9 | `reap_worktrees.py --execute` | V3 as amended ratified, D-4 | not before |

---

## 12. Validation record

Sizing under CON §3: a document of record with high uncertainty — 3+ Lane A with distinct entry points, 2+ Lane B with opposing briefs, at least two iterations. Verbatim reports: R1.

| Round | Lane | Entry point / brief | Result |
| --- | --- | --- | --- |
| 1 | A1 | repository and CI only | 62 claims; 17 DISAGREE; 6 UNTRACEABLE (2 overturned by the reconciler reading V3) |
| 1 | A2 | docs raw pages + `~/.claude` state | the primitive table verified verbatim; DISAGREE on window dates, a transcript count, four "NOT DOCUMENTED" cells, the `/loop`-resume claim, the statusline refresh statement |
| 1 | A3 | execution | 9 demonstrated failures (the v1 rule dispatched nothing; no default `k`; undefined helpers; transcript lag; unmapped headers), 17 underspecified rules |
| 1 | B1 | refute the architecture, premises granted | 20 refutations, 3 blockers (`isolation: worktree` is single-repo; V3 B1/B3 refuse squash merges; the terminal-keyword rule retires live paths), one steelmanned alternative that v3 adopts |
| 1 | B2 | amputation against the seed; actionability for P0–P2 | no clause dropped; 3 re-scopings named for ratification (§1.2); 10 standing-rule conflicts; 31 actionability gaps; 14 internal-consistency defects |
| 1 | reconciler | re-derived every lone load-bearing finding before accepting it (window dates, the `.meta.json` double count, the `/loop` sentence, the `autoContinueAtUsageLimit` scope, V3 §6.5/§7, the DUP-GUARD key, `task-executor`'s isolation line, `claudey`'s skip-permissions) | v2 (Appendix D), v3 (Appendix E) |
| 2 | — | on v3's corrections only: one Lane A (execute the §8 rule and the §6.2 script again; re-probe the new §7.3 test on real squash-merged branches) and one Lane B (do the corrections break what survived) | pending |

**Observed during round 1**: all three Lane A agents, launched together at 02:05Z, were killed within a minute by the 12:10am 5-hour window; the orchestrator's turn survived; at 05:15Z each was resumed in place with `SendMessage` and delivered its report with its earlier reading intact. Their transcripts carry the `quotaLimits` record with the low-priority offer fields.

Minimum record (CON §7), to be completed after round 2: instruments and adequacy (§0; each report's §4); sample size (80–99 transcripts of one slug, 143–171 records; all slugs 232; one account, one host; the sample is an mtime window); agents per lane and entry points (above); iterations (two so far, the second changed the controller surface, the ledger's transition rules, the worktree mechanism and the V3 landed test); unresolved dissent (Appendix D row 25; Appendix E rows marked "recorded"); and **what the evidence cannot support**: no execution-class cost or duration has been measured; `k_w` and `ω_c` are unmeasured; the `quotaLimits` shape and the `-p` behaviours are observed in one Claude Code version; whether a `-p` child running a saved workflow behaves as documented on this host is untested.

---

## 13. Risks and what would make this design wrong

- **`k` may be small.** If the weekly headroom yields less than about one M task per day, the dispatcher adds little beyond the status line; D-10 decides that from measurement.
- **Active calibration is itself spend**, and `ω_c` may drift with model or cache changes; the passive drift monitor exists to say so, not to correct it.
- **The heartbeat is a single point of failure for the odometer** outside the owner's hours; a stale odometer stops dispatch (fail-closed), which is the intended failure.
- **`used_percentage` is account-wide**: any target the dispatcher meets can starve interactive work; `dispatch_windows` is the mitigation.
- **A `-p` child has no pause**: every hit costs the affected agents' work; the duration guard and the allowance exist so hits are rare, and idempotent branches make the re-queue cheap.
- **A workflow cannot ask**: every escalation becomes a decision row and a blocked task; the pilot measures the escalation rate.
- **Signed commits via whole-file API uploads**: `--expect-base` is the only defence and depends on GitHub's compare being consulted before every upload.
- **V3 is unratified and one of its gates is wrong for squash merges**; nothing is removed until D-12 and ratification, so the worktree count (168 at last measurement) grows by two per execution-class task (task + docs) per cycle beyond the pilot.
- **The Status vocabulary is uncontrolled**: the map will leave residue; the class is owner-owned at the cost of reviewing drift flags.
- **This account hit the weekly wall on 2026-09-22 and four 5-hour walls across Sep 21–22**: any pilot before Sep 23, 10pm Chicago runs into a wall the design predicts and cannot cross.

---

## Appendix A — The seed requirements, verbatim

From `notes/dynamic_workflow_design.out` on branch `design/dynamic-workflow` (`27ea09a1`); Lane A1 confirmed the reproduction differs only in leading/trailing whitespace:

```text
define dynamic workflow that dispatches agents to perform prompts, prompts that are written and validated dynamically if necessary, given an initial set of notes file, design path documents that define current, active goals.
as work is performed on these design paths, the documents should be maintained in an up-to-date state.
as design docs are completed or superceeded, the dynamic workflow's goal set should be updated accordingly.

agents should be dispatched and managed in a manner that optimizes progress on the set of design path notes files while simultaneously ensuring that the current session and weekly limits are met but not exceeded by their expiration times.

agents should be handed a fresh worktree to perform their development.
when the agent's work arc is complete and its worktree meets criterea for removal, the workflow should specifiy that the worktree be removed.

open decisions should be sent to me, with the associated tasks listed as blocked on my response
with the agents working on the blocked tasks being reassigned to other tasks to continue the managed progress cadence.
```

Cross-cutting instruction from the request that produced this document: "this design should be validated by consensus when appropriate. this design should incorporate existing harness, best practices, token efficiency concerns, session limits and consensus validation to ensure correctness and avoid hallucinations."

## Appendix B — Measured usage-limit records

Output of `python3 util/ad-hoc/2026-09-22_rate_limit_record_probe.py --max-files 80`, run 2026-09-23 01:5xZ over the 80 transcripts then newest by mtime in the juniper-ml slug (the probe prints `·` for the middle dot because `json.dumps` escapes non-ASCII). The set is a moving window: Lane A3's re-run at 05:28Z returned 149 records, one more 5-hour window (12:10am) and one fewer weekly window; all 99 transcripts gave 171; all slugs gave 232; the probe's default directory never sees worktree-launched sessions (29 such slug directories), so §5.2's reader scans `~/.claude/projects/*/`.

```text
files scanned: 80  records: 143
    104  assistant.quotaLimits  keys=['isUsingOverage', 'overageDisabledReason', 'overageStatus', 'rateLimitType', 'resetsAt', 'status', 'unifiedRateLimitFallbackAvailable']
     39  assistant.quotaLimits  keys=['isUsingOverage', 'lowPriorityMaxWaitSeconds', 'lowPriorityOffer', 'lowPriorityRetryAfterSeconds', 'overageDisabledReason', 'overageStatus', 'rateLimitType', 'resetsAt', 'status', 'unifiedRateLimitFallbackAvailable']
by rateLimitType: {'five_hour': 131, 'seven_day': 12}
distinct resetsAt for five_hour: 8 (last 8, UTC): ['2026-08-24T12:30Z', '2026-08-26T03:40Z', '2026-08-26T10:50Z', '2026-09-08T16:20Z', '2026-09-09T04:40Z', '2026-09-21T11:10Z', '2026-09-21T23:30Z', '2026-09-22T22:40Z']
distinct resetsAt for seven_day: 3 (last 8, UTC): ['2026-08-27T03:00Z', '2026-09-11T00:00Z', '2026-09-24T03:00Z']
SAMPLE keypath: assistant.quotaLimits
SAMPLE object: {"status": "rejected", "resetsAt": 1790116800, "unifiedRateLimitFallbackAvailable": false, "rateLimitType": "five_hour", "overageStatus": "rejected", "overageDisabledReason": "out_of_credits", "isUsingOverage": false}
SAMPLE record meta: {'type': 'assistant', 'isSidechain': False, 'timestamp': '2026-09-22T22:09:36.107Z'}
SAMPLE message content: [{"type": "text", "text": "You've hit your session limit · resets 5:40pm (America/Chicago)"}]
```

`assistant.quotaLimits` means a JSON line of `type: "assistant"` with `quotaLimits` at its root. Weekly-limit records in that set were written 2026-08-25 20:53–22:32Z (3, one session), 2026-09-09 19:51–20:11Z (3), and 2026-09-22 23:52Z–2026-09-23 00:03Z (6, three sessions). Sessions that wrote a limit-hit record dated 2026-09-22 (Chicago): 5 in the slug.

## Appendix C — Documented facts relied on, by page (each re-derived verbatim by Lane A2, R1 Report A2)

| Page (`https://code.claude.com/docs/en/…`) | Facts used |
| --- | --- |
| `workflows` | pause conditions and their exclusions (incl. `-p`, Agent SDK, background, Remote Control, teammate); saved workflows in `.claude/workflows/`, `/<name>`, `args`, `meta` literal, `Date.now()` throws; replay re-runs failed-and-later agents; `Workflow(<name>)` allow rule for `-p`; workflows available in `-p`; `ultracode` ignored from `-p`; concurrency and its env var; the `budget` global; prompt-cache prefix sharing, `subagentPromptCacheTtl`; "No mid-run user input"; five structured-output attempts |
| workflow-authoring reference (bundled, 2.1.280) | `agent()` options; min(16, CPUs − 2); throw → null; `parallel()` null on failure; top-level `return`; no `import` |
| `sub-agents` | frontmatter fields incl. `isolation` (same repository), `omitClaudeMd`; API errors incl. usage limits end a run; `SendMessage` resume; Explore/Plan one-shot; 20 concurrent; hooks payloads; named subagents become teammates while teams are on |
| `worktrees` | `.claude/worktrees/<name>`, `worktree-<name>`, `baseRef`; `-p` leaves worktrees and locks; the sweep; the lock; `WorktreeCreate` hook; isolation checks apply to the launching repository and cover the main checkout |
| `headless` | `--bare` needs an API key; `-p` stays open for background work, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`; SIGTERM leaves the turn resumable; `system/api_retry` with `error: rate_limit`; `--resume` by id from any directory; `--permission-prompts none` (v2.1.259+); `--json-schema` |
| `interactive-mode` | wait-for-reset semantics, twice-in-a-row re-arm, exclusions, `/rate-limit-options`, "Background sessions and `-p` runs: the menu row isn't available" |
| `statusline` | `rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}`; Pro/Max or gateway; after the first API response; per-session payload; a window dropped once `resets_at` passes; `refreshInterval`; "event-driven triggers can go quiet when the main session is idle" |
| `settings-reference` | `autoContinueAtUsageLimit` default `true`, user/managed scope, project/local file turns it off; `cleanupPeriodDays` 30; `dialogExpiry` 5m |
| `costs` | windows "shared across all models"; cached-rate re-reads; "91 % of input tokens from cache"; usage from other devices not local; scheduled tasks and cross-session messages cost a full-context turn; thinking billed as output; teams ≈7× |
| `hooks` | `SubagentStart/Stop` payloads; `WorktreeCreate/Remove`; `quota_auto_resume_*` matchers |
| `scheduled-tasks`, tools reference | fire only while running and idle; `CronCreate` restored on resume, self-paced `/loop` not; 7-day expiry; 1 min–1 h; `stop: true` |
| `cross-session-messaging` | idle receiver starts a turn; bypass receiver's delivery rule; `-p` receiver and `dialogExpiry`; scripts may post to the session socket |
| `agent-teams`, `agents`, `goal`, `agent-view`, `routines` | the comparison in §2.2 and §3.3 |

## Appendix D — Round 1 Lane A finding → resolution map (applied in v2, carried in v3)

| # | Finding (lane) | Resolution |
| --- | --- | --- |
| 1 | "five windows hit on 09-22" is false (A2, A3; reconciler re-derived with per-window dates) | §2.1 table with hit dates |
| 2 | weekly 08-25 count; "8 limit-hit sessions" not reproducible (A2, A3) | Appendix B corrected |
| 3 | 1,220 agent transcripts (A2, A3; reconciler: `.meta.json` companions counted) | §2.1 Signal 3 |
| 4 | four "NOT DOCUMENTED" cells are documented (A2) | §2.2 |
| 5 | self-paced `/loop` not restored on `--resume` (A2; reconciler re-derived) | §2.2; a reason for v3's timer surface |
| 6 | scheduled-task-at-limit undocumented; clamp/noop from the tool description (A2) | §2.2 |
| 7 | statusline refresh triggers documented (A2) | §5.1 |
| 8 | `Workflow(<name>)` rule documented for `-p`/SDK only (A2) | §6.1 (v3 uses `-p`) |
| 9 | concurrency min(16, CPUs − 2); Agent SDK fails too (A2) | §2.2 |
| 10 | `CLAUDE_BASE` observed not documented; three-conjunct reuse predicate (A2) | §2.4 |
| 11 | `autoContinueAtUsageLimit` project/local trap (A2; reconciler re-derived) | §2.2 |
| 12 | Appendix B not verbatim; moving window (A3) | Appendix B |
| 13 | transcript records lag the event (A3) | §2.1, §5.2 |
| 14 | the v1 pacing rule dispatched nothing; no default `k`; undefined quantities (A3) | §8 (v2 bucket; v3 own-token debit and reset semantics) |
| 15 | §6.2 snippet: undefined helpers, phase mismatch, null vs throw (A3, A1) | §6.2 |
| 16 | status-class table unmapped 52–74 %; contains-match flips (A3, A1) | §4.3/§4.5 (v3: transitions only on the append form) |
| 17 | worktree counts moved; dead lock pid; 177 + `logs/`; N−1 (A1) | §2.4 |
| 18 | six CI tests, not four (A1) | §2.3 |
| 19 | 606 session files; 627 notes; Supersedes 18/3; CORRECTION 46/53; status counts instrument-dependent (A1, A3) | §2.3, §2.5 |
| 20 | `status_source` example wrong; list-form header (A1) | §4.1 `header_status` |
| 21 | RUBRIC freshness sentence misquoted (A1) | §6.3 |
| 22 | no gitleaks hook (A1) | §6.9 |
| 23 | archive test scans only top-level notes; docs screen qualifiers (A1) | §4.3, §2.5 |
| 24 | V3 G2 includes `--no-optional-locks` (A1) | §2.4, §7.3 |
| 25 | UNTRACEABLE V3 veto and admin dump (A1) — **dissent overturned** by the reconciler reading V3:817-820 and :886-888 | §2.4, §7.3 cite them by line |
| 26 | "three scripts marked do not use" (A1) | §2.4 |
| 27 | ml#1869 and the 2026-05 incidents are memory of record (A1) | §2.4, §7.4 |
| 28 | `budget` global, `Goal paused`, backgrounding restarts subagents, named subagents become teammates (A2) | §2.2, §3.3 |
| 29 | markdownlint MD013 in `notes/` is ungated (A3) | norm, not gate |

## Appendix E — Round 1 Lane B finding → resolution map (applied in v3)

| # | Finding (lane) | Resolution |
| --- | --- | --- |
| 1 | validator and executor ran on different HEADs (B1 #1) | §6.3: discovery by the tick in the task worktree; `head_sha = base_sha` for all stages |
| 2 | no path for new tasks into the ledger; exhaustion read as completion (B1 #2) | `tasks_proposed[]`, `PROPOSED` state, §4.3 case 3 guarded |
| 3 | **BLOCKER** terminal-keyword-anywhere retires live paths, V3 included (B1 #3; B2 P1-2) | §4.3 case 2 restricted to the design's own append form; §4.5 never changes a class |
| 4 | stacked whole-file docs PRs conflict (B1 #4) | long-lived `dispatch/docs/<DP-id>` branch and `--append` (§6.5) |
| 5 | **BLOCKER** shared odometer file with last-writer-wins and hash-refreshed staleness (B1 #5; B2 P0-3, P0-4) | per-session files, max-within-window merge, `context_window` per session (§5.1) |
| 6 | bucket double-charged the owner's usage, went negative, undefined across a reset (B1 #6) | own-token debit, floor 0, reset semantics (§8.1) |
| 7 | nothing bounds the run's rate (B1 #7) | concurrency cap 4, `budget` ceiling, executor re-reads the odometer (§8.4) |
| 8 | passive calibration unidentifiable on a shared account (B1 #8; B2 P0-5) | active class-resolved bursts; passive samples monitor drift only (§5.3) |
| 9 | idle ticks cost as much as the loop dispatches (B1 #9) | timer + pure-code tick: zero idle tokens (§3.2) |
| 10 | auto-continue bounded and synchronised; ticks fire mid-run (B1 #10) | no pause relied on; jitter after resets; in-flight check (§8.2) |
| 11 | **BLOCKER** `isolation: worktree` is single-repo; cross-repo tasks would touch live checkouts (B1 #11) | code-created ecosystem worktrees in the task's repo; `dispatch-executor` without isolation; child launched from the main checkout (§7.1, §6.5) |
| 12 | clobber pre-check compared local refs API pushes never advance (B1 #12) | `open_signed_pr.py --expect-base` with remote compare (§6.5) |
| 13 | **BLOCKER** V3 B1/B3 refuse every squash-merged branch (B1 #13) | executor resets to the remote after upload; patch-id landed test proposed as V3 amendment (D-12, §7.3) |
| 14 | manifest identity was the agent's word; crash states conflated (B1 #14) | rows written by the code that creates the tree; `PLANNED`/`CREATED` (§7.1, §7.4) |
| 15 | no stage wrote the decision row; refuters attacked a null PR; worktree reuse impossible under isolation (B1 #15; B2 row 12, §5-6, §5-7) | decision short-circuit in §6.2; maintainer appends the row; same-worktree redo (§9.3) |
| 16 | permission prompts stall the run unless bypass (B1 #16) | `--dangerously-skip-permissions` as every `claudey` session, or `--permission-prompts none` + allow rules (D-1) |
| 17 | dead refuter counted as refutation; replay re-runs non-idempotent stages (B1 #17) | `VERIFY_PENDING`; deterministic branches + DUP-GUARD (§6.4, §6.5) |
| 18 | side effects survive a dropped stage (B1 #18) | `exec_out.json` written before returning (§6.5) |
| 19 | D-10 inputs unmeasurable by P0; over-gated roadmap (B1 #19; B2 P0-1) | D-10 inputs redefined; P0 exempt; P0 ‖ P1 ‖ P3 (§10, §11) |
| 20 | `lensesFor` sizing; `EXECUTED` rule; skill withheld from models (B1 #20) | §6.2, §4.5, D-11 |
| 21 | pre-written prompt validated with a null bundle (B2 row 2) | tick-produced bundle for every task (§6.3) |
| 22 | "arc table" cited but not on disk (B2 row 3) | INV archived; §4.2 cites INV I3 §3 |
| 23 | "up to date" weakened; Maintain skips dropped tasks (B2 row 4) | stated in §1.2 and §4.4 |
| 24 | "optimises" = greedy; no retry budget (B2 row 6) | `retries`, BLOCKED at 2 (§4.1, §6.4) |
| 25 | "met" re-scoped; non-binding window under-used (B2 row 7) | §1.2, D-5 |
| 26 | "agents" re-scoped to editing agents; reuse exception (B2 row 8) | §1.2, §7.1 |
| 27 | standing-rule conflicts: worktree location, dirty checkout, prune, `/tmp` scripts, one PR per unit, CI-skip marker, PR-body conventions, handoff threshold, `ci.yml` wiring, untracked scripts (B2 §3) | §7.1/D-2; runtime state outside repos; prune; evidence-dir scripts; docs PR = the cycle's unit; `RULES` in every brief; no handoff in v3; §11 wires tests; the scripts land with this PR |
| 28 | P0/P1/P2 actionability gaps (B2 §4: absolute paths, merge semantics, calibration closure, schemas, `dispatch_windows` unused, parameters' home, fixtures, two weekly predicates, step-8 direction, script cannot act, report producer, missing branch, `prompt_path` undefined, P3 state token) | §5.1, §5.3, §8.1–§8.2 (`next`, `conf/dispatch.yaml`, one predicate, step 7), §6.1 (`--stream`), §6.3 (pre-assigned paths), P3 (`PROMPT_VALIDATED`); the three schemas are P2's deliverable in `docs/REFERENCE.md` |
| 29 | internal-consistency defects (B2 §5: R1 → §6; §2.1 caption; two matching rules; writers; LENSES; §9.1; guard; Appendix D row 25 lines; P6 prefixes; missing tests; untracked scripts; §13 count) | each corrected in place |
| 30 | the steelmanned timer alternative (B1 §3) | **adopted** as the controller surface; the saved workflow kept inside the child (§3.2); recorded as the round's largest change |
