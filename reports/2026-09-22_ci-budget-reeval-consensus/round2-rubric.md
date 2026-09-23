# CI-budget re-evaluation -- consensus round 2, Rubric -- prompt-validator, iteration 2

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `d873aed6`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

```json
{
  "validator_status": "ok",
  "head_sha": "d873aed6c0a46803eb3092472cca7ba31393c789",
  "iteration": 2,
  "findings": [
    {
      "id": "R2.4",
      "severity": "major",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md, first §1 block, NON-OWNER WORK 1: the C2 directive (lines 117-118) against its ACCEPTANCE (line 119)",
      "problem": "New in this rewrite. The C2 mechanism contradicts the acceptance criterion. Taken literally, 'skip a line that continues a paragraph' drops the 2nd through Nth line of any contiguous run of unfenced commands. That turns test_C2_counts_multiplicity_so_duplicated_commands_are_seen red: its fixture has three consecutive 'pip install x' lines and it expects exit 1 with 'C2 2 NEW command line(s)'. ACCEPTANCE says the suite 'stays green' but names only the C4 test as must-stay, so the easiest way through is to edit that fixture. Doing so re-blinds C2 to the duplicated-block damage (ml#1799) that its multiplicity fix exists for. The C4 half was correctly rewritten as a goal plus constraints; the C2 half is still a mechanism that conflicts with its own criterion.",
      "fix": "Restate C2 as a goal with a bound. Skip a command-looking line only when the line before it in the same paragraph is prose: not itself command-looking, and not a heading or a fence. Then 'git). A table' and 'make the credential' stop firing, while N contiguous commands still count as N. Name test_C2_counts_multiplicity_so_duplicated_commands_are_seen as must-stay-green and unedited. Add the negative control 'three contiguous unfenced commands still count 3'.",
      "evidence": "sed -n 117,119p <handoff@d873aed6> -> 'C2: require whitespace after the command word (`\\b` lets `git)` match) and skip a line / that continues a paragraph.' / 'ACCEPTANCE: `python3 -m unittest -v tests/test_md_structure_check.py` stays green,'. tests/test_md_structure_check.py:167-174 -> before='# D\\n\\npip install x\\n', after='# D\\n\\npip install x\\npip install x\\npip install x\\n', assertEqual(code, 1), assertIn('C2 2 NEW command line(s)'). A python3 -c simulation loaded util/ad-hoc/2026-09-05_md_structure_check.py via importlib. It rebuilt the unfenced-line list with CODEY's trailing \\b replaced by (?=\\s), skipping any line whose previous line is non-blank and is neither a fence nor an ATX heading, then compared _newly_added() for each fixture. Output: 'test_C2_counts_multiplicity_so_duplicated_commands_are_seen ... current screen: 2 new C2 line(s); literal NON-OWNER-1 C2 rule: 0 new C2 line(s)'; 'test_a_vcs_command_left_outside_a_fence_is_now_reported ... current 1; literal 1'; '#1980-shape prose continuation ... current 1; literal 0'. Baseline: python3 -m unittest -v tests/test_md_structure_check.py -> 'Ran 15 tests in 1.863s  OK'."
    },
    {
      "id": "R2.4",
      "severity": "major",
      "location": "first §1 block, PREFLIGHT pre-merge branch (lines 50-52), against § Validation record 2026-09-22 (lines 769-770) and OWNER DECISION 2",
      "problem": "The pre-merge path says 'land ml#2017 first (MERGING)' with no precondition. But the document it would land says '**Round 2** ... in progress; this subsection is completed before merge', and the PR's own consensus checkbox is unchecked. #2017 also ships the three budget raises (data and data-client 2400->3300, deploy 700->1400) that OWNER DECISION 2 asks the owner to rule on, with one lane dissenting HOLD. A successor following the prompt on the branch would merge a document of record before its validation finishes and pre-empt OWNER 2. It would also ask for the owner's merge approval without the dissent in front of them. #2017 is OPEN and BEHIND now, so this path is live if the handoff is sent before round 2 closes. The iteration-1 'closed by ml#2017 while open' defect is fixed; this is the same family, one step later.",
      "fix": "Pre-merge branch: 'land ml#2017 only after § Validation record 2026-09-22 round 2 is complete and recorded in the file. Put OWNER DECISION 2 to the owner in the same approval request, because #2017 ships the raises that decision is about.'",
      "evidence": "sed -n 769,770p <handoff@d873aed6> -> '**Round 2** — briefed on the round-1 corrections only: *in progress; this subsection is completed / before merge.*'. Prompt lines 50-52 -> 'If you are reading this on the PR branch instead, land ml#2017 first (MERGING)'. gh pr view 2017 --repo pcalnon/juniper-ml --json state,mergedAt,headRefOid,mergeStateStatus -> 'OPEN  d873aed6  BEHIND'. gh pr view 2017 --json body, line 50 -> '- [ ] independent-agent consensus (...) — in progress'. statusCheckRollup -> 'Verify AGENTS.md Last Updated' FAILURE (non-required). git diff d0582a21 d873aed6 -- util/safe_merge.py -> '-    \"juniper-data\": 2400,' '+    \"juniper-data\": 3300,' ... '-    \"juniper-deploy\": 700,' '+    \"juniper-deploy\": 1400,' under '# DISSENT RECORDED, NOT RESOLVED.'"
    },
    {
      "id": "R4",
      "severity": "major",
      "location": "first §1 block, NON-OWNER WORK 2 (lines 128-132)",
      "problem": "NON-OWNER 2 names an activity (re-measure with first-pass) but no deliverable, and no rule for what to do when a budget reads stale. That is exactly the question OWNER 2 leaves open. The enforced rule (> observed max and <= 4x p90, asserted over MEASURED_SPANS) and the 09-09 and 09-22 precedent both say re-pin; the recorded dissent says HOLD. One competent agent would open a PR raising a budget below the ceiling (cascor-worker 2400 clears its max by 341 s, recurrence 2000 by 334 s). Another would report and wait for the owner. 'Watch the ceiling (OWNER 2)' only covers the four repos already at 3300.",
      "fix": "Give NON-OWNER 2 an output and a decision rule. Run '..._reprobe.py first-pass'. If every row reads OK, record the date, n and window, then stop. If any row reads BELOW HEALTHY MAX or ABOVE 4x p90, do not re-pin while OWNER DECISION 2 is open. Instead report the repo, the max PR and its queue share (laneB2/span_decompose.py) to the owner as input to that decision.",
      "evidence": "sed -n 128,132p <handoff@d873aed6> -> '2. Re-measure the CI budgets before trusting them, with `first-pass`, never raw v2. ... Watch the ceiling (OWNER 2).' There is no output and no action for a stale row. util/safe_merge.py@d873aed6 dissent comment: 'the raises follow the rule as written. But queue-free, all three spans fit their OLD budgets ... Whether a budget should absorb within-span contention at all is an OWNER decision'. tests/test_safe_merge.py:626-634 -> 'for repo, (p90, observed_max) in MEASURED_SPANS.items(): ... assertGreater(...) ... assertLessEqual(budget, 4 * p90, ...)'. safe_merge.py 09-22 comments: cascor-worker 'clears the max by only 341 s', recurrence 'clears the max by only 334 s'; both are below TIMEOUT_CEILING 3300 (safe_merge.py:211)."
    },
    {
      "id": "R4",
      "severity": "major",
      "location": "first §1 block, NON-OWNER WORK 1 ACCEPTANCE replay (lines 123-125)",
      "problem": "The replay cannot be run as written. The screen reads the base with 'git show <base>:<path>' in the current directory's repo, and reads the head with open(<path>) from the current directory's working tree. The prompt calls the script by a RELATIVE path. Run in a checkout at the flagged head, it runs that head's pre-fix screen, so the 7 false findings still fire. Run from the dev tree, it reads today's file rather than the flagged head's, so #1999's true C3 finding (fixed before merge) cannot fire. '<base sha>' also has no stated source: neither the prompt nor § Re-evaluation gives a base for any finding, heads are given only for #1999, and the soak probe records the head but not the base. Two competent agents would get materially different results from the only end-to-end acceptance, and both would be wrong.",
      "fix": "Spell the replay out. For each distinct finding the soak probe lists, take <base sha> from its soak job log line 'examining N changed markdown file(s) against <sha>' (or from the job summary's 'Base:'). Create a detached worktree at the flagged head. From inside it, run the NEW screen by ABSOLUTE path: python3 <dev-tree>/util/ad-hoc/2026-09-05_md_structure_check.py --base <base sha> <path>.",
      "evidence": "util/ad-hoc/2026-09-05_md_structure_check.py:130-133 base_text -> subprocess.run(['git', 'show', f'{base}:{path}']) in the current directory; :236-238 -> 'with open(path) as f: ht = f.read()'. Prompt line 124 -> '`python3 util/ad-hoc/2026-09-05_md_structure_check.py --base <base sha> <path>`' (relative path). Handoff lines 587-588: ml#1999 C3 'at heads `ea4c3596` / `25c001bd` / `276db114`. It was fixed before merge.' util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py:528-539 stores 'head' per soak check-run and no base. .github/workflows/ci.yml:1687 'echo \"examining ${#files[@]} changed markdown file(s) against ${base}\"' and :1698 'Base:' are the only places the base is recorded."
    },
    {
      "id": "R3.2",
      "severity": "minor",
      "location": "first §1 block, PREFLIGHT comment 'Exit 0 = every probe measured every row' (lines 58-61)",
      "problem": "The iteration-1 item is still open. The docstring was strengthened from '0 every probe ran' to '0 every probe measured every row', but three probes can still exit 0 over unmeasured data. alarm reads a single page of 50 runs and never paginates; juniper-ml has 54, so 4 go unread without any notice. soak records an unreadable log after its retries but raises only for 'unclassified' readable logs. first-pass puts a head with no span under `unmeas` and raises only when a repo has no healthy head. No current figure changes: the 4 unread alarm runs are OK, and the 12 unreadable soak logs are printed.",
      "fix": "Either paginate alarm and raise Unmeasurable on an unreadable non-cancelled soak log and on a head with no span, or reword the claim: 'exit 0 = no probe refused; each probe prints its own unread and unmeasured counts, so read them'.",
      "evidence": "python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py alarm -> 'juniper-ml alarm=present webhook=yes runs=50 2026-08-04..2026-09-22 ...' then 'exit=0'. gh api 'repos/pcalnon/juniper-ml/actions/workflows/pr-budget-alarm.yml/runs?per_page=1' --jq .total_count -> 54. Page 2 -> 4 runs, 2026-07-31..08-03, each with its Slack step 'skipped'. reprobe.py:427 '...runs?per_page=50' is a single read; :541 and :577-580 raise only when there are no checks or on unclassified logs; :357-359 and :405-407 cover first-pass."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "first §1 block, PREFLIGHT reprobe command and Sandbox note (lines 55-63)",
      "problem": "(1) No command assigns $S, and this harness does not keep shell variables between calls. If S is unset, the argument becomes '/reprobe.json'. Its parent '/' exists, so the directory check the rewrite relies on passes. The run then spends its ~2,500 REST calls and crashes with exit 1 when it tries to write to the unwritable '/'. (2) `all` without `--fetch` exits 2 today, because slack refuses a stale sibling (juniper-cascor-worker). (3) The sandbox note is too broad. In this worktree-isolated session a plain pipe and a plain redirect naming git both ran; only compound, `cd`, `$(...)` and heredoc forms were refused.",
      "fix": "Use \"${S:?set S to the session scratchpad}/reprobe.json\" or the literal scratchpad path. Run `all --fetch`, or say that slack refuses a stale sibling and names `--fetch`. Narrow the sandbox note to the forms that are actually refused.",
      "evidence": "unset S; echo \"[$S/reprobe.json]\" -> '[/reprobe.json]'. python3 -c (Path('/reprobe.json').parent.is_dir(), os.access('/', os.W_OK)) -> 'is_dir: True', 'writable: False'. reprobe.py:701 checks only parent.is_dir(); :729 write_text. python3 ...reprobe.py slack -> 'UNMEASURABLE: slack: ['juniper-cascor-worker'] read growth from a local origin/main that disagrees with GitHub -- re-run with --fetch', exit=2. In this session, `git show --format= --unified=0 c4a67481 -- '*.md' | grep -E ...` and `git show d873aed6:<handoff path> > <scratchpad>/handoff_d873.md` both ran. A 'cd ... && ...; diff <(git show ...)' form and a '$(git merge-base ...)' form were refused."
    },
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "first §1 block, OWNER DECISION 2 (lines 77-88)",
      "problem": "(a) 'Every re-measure so far has only raised budgets' holds only if ml#1828's pinning of deploy and recurrence counts as a first measurement. That re-measure cut their effective budget from the 2400 s DEFAULT_TIMEOUT to 700 s. Recurrence's 700 went stale within a day and was raised to 2000. That is the only precedent for the 'size on queue-free span' option, which would lower budgets. (b) 'raise the ceiling (bounded by the ~3600 s worker lease)' repeats the hard-bound framing that util/safe_merge.py withdraws. (c) The 'do NOT raise a budget to absorb a queue' quote leaves out that the paragraph was narrowed to pre-start queue, which is a SHIP-side point.",
      "fix": "Say 'every re-measure of an already-pinned budget' and add that the one lowering went stale in a day. Replace 'bounded by' with 'at rising risk above ~3600 s (safe_merge.py: a risk threshold, not a hard bound)'. Point the owner at the dissent comment above REPO_TIMEOUTS, which states both sides.",
      "evidence": "git show b26acd62 -- util/safe_merge.py -> '+    \"juniper-deploy\": 700,' '+    \"juniper-recurrence\": 700,'. git show b26acd62^:util/safe_merge.py -> :197 'DEFAULT_TIMEOUT = 2400', :235 'return REPO_TIMEOUTS.get(repo, DEFAULT_TIMEOUT)'. The ml#1828 message says 'juniper-deploy and juniper-recurrence fell through to DEFAULT_TIMEOUT at 9x their p90'. git show 3cab4783 -> '+    \"juniper-recurrence\": 2000,'. util/safe_merge.py:199 'The CEILING is a RISK threshold, not a hard bound'; :202-203 '8 background tasks ... ran past 3600 s'; :247-248 'That paragraph was narrowed on 2026-09-10 to PRE-start queue'."
    },
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "first §1 block, OWNER DECISION 3 promotion recipe (lines 94-96)",
      "problem": "The recipe keeps the #2017 correction (replace the FINAL exit 0 with exit \"$rc\") but drops the caveat #2017 wrote next to it in ci.yml. If only the final exit 0 is replaced, the early `exit 0` on a failed `git diff` survives. A promoted required check would then pass green on a run that examined nothing.",
      "fix": "Append: 'and decide in the same change whether rc 2 fails and whether the early exit 0 on a failed git diff becomes a failure; see the PROMOTION PATH comment in ci.yml'.",
      "evidence": "The ci.yml@d873aed6 soak comment: 'Decide at the same time whether rc 2 (\"refused to report\") should fail, and whether the early `exit 0` on a failed diff should.' ci.yml:1674 'if ! git diff -z --name-only --diff-filter=d \"$base\" HEAD -- '*.md' > changed.z; then' is followed by '...nothing examined\"' and 'exit 0'."
    },
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "first §1 block, GIT STATE AT HANDOFF (lines 182-188)",
      "problem": "The section does not name the worktree's local branch (worktree-ancient-yawning-biscuit, which is not the PR branch). It also omits that the worktree holds #2017's content as 14 modified, uncommitted tracked files that are byte-identical to d873aed6. 'Consensus-lane scripts sit untracked' is true only in that worktree: three of them are tracked in #2017. A successor reading `git status` there cannot tell what is safe to discard from what is unpushed.",
      "fix": "Add: 'local branch worktree-ancient-yawning-biscuit = e3186919 plus the unsigned 18d3d5e3; its 14 modified files are identical to d873aed6; laneA2/span_all_attempts.py, laneA2/queue_share.py and laneB2/span_decompose.py are tracked in #2017, and everything else under that directory is untracked lane scratch'.",
      "evidence": "git branch --show-current -> 'worktree-ancient-yawning-biscuit'. git status --short -> 14 ' M' tracked files plus '?? util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/'. git diff --stat d873aed6 -- <the 14 files> -> (empty). git log -1 --format='%h %G? %p %s' 18d3d5e3 -> '18d3d5e3 N e3186919 local-only: ...'. git branch -r --contains 18d3d5e3 -> (empty). git hash-object of the 3 lane scripts equals git rev-parse d873aed6:<same paths> (5ef091e6, 0e07b0b3, 238bb688)."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "first §1 block, USE THE RIGHT TOOL relocation line (162-163), NON-OWNER 1 (line 110), OWNER DECISION 5 (lines 102-103)",
      "problem": "(a) 'the four traps in the SUPERSEDED block below' points at nothing inside the copied block. (b) The claim that § Re-evaluation 'lists all ten lost headings, before and after' fails on row 8: '… — CHOSEN 2026-09-22' reads as an append, but the real heading dropped '(recommended)'. A fixture built from the table is therefore substring-clearable, which contradicts 'clears only 3'. (c) '97 unmerged fleet PRs' does not state its scope. It counts only juniper-ml's cursor/-headed PRs; fleet-wide the figure is 138.",
      "fix": "Write 'the four traps in the SUPERSEDED second block of §1 of THIS DOCUMENT'. Build the C4 fixtures from the merge diffs rather than the table. Write '97 juniper-ml cursor/ PRs (138 fleet-wide)'.",
      "evidence": "sed -n 162,163p <handoff@d873aed6> -> 'the four traps in the SUPERSEDED block below'. git show --format= --unified=0 c4a67481 -- '*.md' -> '-### Option B — a dedicated `dockerhub` environment (recommended)' and '+### Option B — a dedicated `dockerhub` environment — CHOSEN 2026-09-22'. Across the ten headings the substring rule clears exactly 3 (0.6, Option A, 5.2A). gh search prs --owner pcalnon --created 2026-09-01..2026-09-06 --state closed --merged=false -> 138, all cursor[bot] (ml 100, data 30, canopy 8). gh pr list --repo pcalnon/juniper-ml ... -> 100 PRs, of which #1728, #1729 and #1732 have non-cursor/ heads."
    }
  ],
  "hallucination_risk": [
    {
      "claim": "util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py with subcommands `all` and `first-pass`; `--json` refuses a missing directory",
      "class": "path",
      "grounded": true,
      "evidence": "git cat-file -e d873aed6:util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -> exit 0. On origin/main -> 'exists on disk, but not in origin/main', exit 128; PREFLIGHT covers both states. reprobe.py:690 and :695 define the choices as PROBES plus 'all'. python3 ...reprobe.py waiter --json /nonexistent-dir-for-validator/reprobe.json -> 'error: --json directory /nonexistent-dir-for-validator does not exist', exit=2."
    },
    {
      "claim": "exit codes: 0, 2 (named on the UNMEASURABLE line), 1 = crash; python exits 2 on a missing script",
      "class": "flag",
      "grounded": true,
      "evidence": "reprobe.py:731-733 prints 'UNMEASURABLE: {failed}' and returns 2, otherwise 0. python3 /nonexistent-dir-for-validator/absent_script.py -> \"can't open file ... [Errno 2] No such file or directory\", exit=2. Reading exit 0 as proof of completeness is overstated; see the R3.2 finding."
    },
    {
      "claim": "python3 util/ad-hoc/2026-09-05_md_structure_check.py --base <sha> <path>",
      "class": "flag",
      "grounded": true,
      "evidence": "md_structure_check.py:222-223 -> add_argument('--base', default='origin/main') and add_argument('paths', nargs='+')."
    },
    {
      "claim": "tests/test_md_structure_check.py::test_C4_reports_a_lost_heading_even_when_another_is_gained",
      "class": "symbol",
      "grounded": true,
      "evidence": "Defined at tests/test_md_structure_check.py:189. python3 -m unittest -v tests/test_md_structure_check.py -> 'Ran 15 tests ... OK'."
    },
    {
      "claim": "util/ad-hoc/2026-09-05_markdown_structure_check.py is the REQUIRED gate's engine; util/ad-hoc/2026-09-05_md_structure_check.py is the advisory soak's",
      "class": "path",
      "grounded": true,
      "evidence": "util/markdown_structure_delta.py:103 sets SCREEN to util/ad-hoc/2026-09-05_markdown_structure_check.py. ci.yml:1605 runs markdown_structure_delta.py in the docs job, which is the required context 'Documentation Links'. ci.yml:1644 and :1689 run md_structure_check.py in 'Markdown Structure (advisory soak)'."
    },
    {
      "claim": "v1 util/ad-hoc/2026-08-20_measure_required_check_span.py filters nothing; v2 reads filter=latest",
      "class": "path",
      "grounded": true,
      "evidence": "ls shows both files exist. v1 docstring line 7 says it 'filters NOTHING'. v2 line 91: '`head_rows` reads check-runs with the API's default `filter=latest`'."
    },
    {
      "claim": "the soak step's FINAL `exit 0`; promotion by `exit \"$rc\"` plus a ruleset context, never via the Quality Gate's `needs:`",
      "class": "symbol",
      "grounded": true,
      "evidence": "In ci.yml@d873aed6 the soak step ends 'fi' then 'exit 0', after `if [ \"$rc\" -ne 0 ]`. The job at ci.yml:1988 is named 'Quality Gate'. gh api repos/pcalnon/juniper-ml/rules/branches/main -> 17 required contexts, strict true, and the soak job is not among them."
    },
    {
      "claim": "python3 util/safe_merge.py --repo juniper-ml --pr <N> --execute; a refusal disarms the net",
      "class": "flag",
      "grounded": true,
      "evidence": "safe_merge.py:1134-1154 defines --pr, --repo, --owner and --execute. safe_merge.py:876-900 wraps every refusal path in the disarm."
    },
    {
      "claim": "util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo --pr --max-syncs --per-pr-timeout; never merges; returns NOT-ARMED on an unarmed PR",
      "class": "flag",
      "grounded": true,
      "evidence": "shepherd.py:209-215 defines the four flags. :48 says 'Never merges.' :186-189 -> 'if not s[\"armed\"]: return \"NOT-ARMED\"'."
    },
    {
      "claim": "util/open_signed_pr.py refuses an existing branch; util/ad-hoc/2026-09-08_push_signed_commit.py appends a commit to an existing PR branch",
      "class": "path",
      "grounded": true,
      "evidence": "open_signed_pr.py:276 prints 'REFUSED: branch {args.branch} already exists'. push_signed_commit.py docstring: 'Append ONE GitHub-signed commit to an EXISTING branch'."
    },
    {
      "claim": "SLACK_WEBHOOK_URL is set on juniper-ml only; the alarm runs daily on all nine; no breach since 2026-09-17; juniper-ml had 8 breaches 2026-08-06..09-05",
      "class": "env",
      "grounded": true,
      "evidence": "python3 ...reprobe.py alarm -> juniper-ml webhook=yes, runs=50, {'OK': 42, 'BREACH (slack step success)': 8}, spanning 2026-08-06T14:48:34Z..2026-09-05T14:09:17Z. The eight siblings show webhook=NO, runs=6 (2026-09-17..2026-09-22), {'OK': 6}. exit=0. pr-budget-alarm.yml:53 cron is '0 14 * * *'."
    },
    {
      "claim": "allow_update_branch is FALSE on all nine repos and the rulesets are strict",
      "class": "flag",
      "grounded": true,
      "evidence": "python3 ...reprobe.py settings -> allow_update_branch=False on all 9 (admin=True), exit=0. gh api repos/pcalnon/<ml, canopy, deploy, recurrence, data>/rules/branches/main -> strict_required_status_checks_policy is true for each."
    },
    {
      "claim": "#2017 raises data and data-client 2400->3300 and deploy 700->1400; 4 of 9 repos sit at TIMEOUT_CEILING 3300; recurrence max 1666 (margin 334 s); cascor-worker max 2059 (margin 341 s); cascor-client p90 1264 / max 1626, window (1626, 5056]",
      "class": "symbol",
      "grounded": true,
      "evidence": "git diff d0582a21 d873aed6 -- util/safe_merge.py shows the three raises and the 09-22 comments ('only 341 s', 'only 334 s', 'p90 1264, max 1626 ... (1626, 5056]'). safe_merge.py:211 sets TIMEOUT_CEILING = 3300. reprobe.py waiter -> canopy, cascor-client, data and data-client each at 3300s, all matching safe_merge."
    },
    {
      "claim": "docs/REFERENCE.md 'Memory-Budget Slack (Planning)' says not to start a relocation for a negative planning margin; four repos are negative",
      "class": "path",
      "grounded": true,
      "evidence": "The heading is at docs/REFERENCE.md:2416, and the section says 'do not start a relocation because headroom < `max`'. python3 ...reprobe.py slack -> 'negative: 4 [juniper-canopy, juniper-cascor-worker, juniper-data, juniper-deploy]'."
    },
    {
      "claim": "the lockfile App-token arm is verified on n = 1 (#1970); of 18 GITHUB_TOKEN PRs, 5 got no run",
      "class": "symbol",
      "grounded": true,
      "evidence": "python3 ...reprobe.py lockfile -> tally {'app/github-actions': {'NO RUN': 5, 'PARKED': 13}, 'app/juniper-release-train': {'EXECUTED': 1}}. #1970 (2026-09-21) shows EXECUTED with 5 bot runs, all 5 running jobs."
    },
    {
      "claim": "ml#1955 wired the soak at 2026-09-18 00:37 UTC; false C4 findings in #1976/#1973/#1992/#1983/#2009 and false C2 findings in #1980/#2007; true findings in #1969 and #1999",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh pr view 1955 -> 2026-09-18T00:37:10Z, e7c191c1. git show --unified=0 of 739a233c, 2dec7631, 3b656b57, 78e36d8e and c4a67481 -> the 10 renamed headings. 93c0942b adds '+git). A table that...'. 1b4c3fa9 adds '+make the credential stop working.'. origin/main:notes/backup_tests_pre-and-post_reboot.md contains the 'python3 ${HOME}/.../yamaguchi_census.py' line. #1999's commits include ea4c3596, 25c001bd and 276db114."
    },
    {
      "claim": "the #1749 swallow",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh pr view 1749 -> 'fix(docs): restore the closing fence #1746 dropped — 36 headings were inside a code block'. #1749 is the repair; the damage is #1746 (bcc89c45), as item 6 of the re-evaluation says. md_structure_check.py:94 uses the same '#1749' label."
    },
    {
      "claim": "the required link checker verifies same-file anchors only",
      "class": "symbol",
      "grounded": true,
      "evidence": "juniper-doc-tools/juniper_doc_tools/check_doc_links.py:286-296 validates an anchor only when file_part is empty. For cross-file targets, the branch below checks only that the file exists."
    },
    {
      "claim": "notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md and notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md (cascor-client ruled out of the pin on 2026-09-15)",
      "class": "path",
      "grounded": true,
      "evidence": "ls shows both files exist. The walkthrough's §1: 'Ruled: the value STANDS; the row stays excluded from KillResilienceTest's pin.'"
    },
    {
      "claim": "worktree .claude/worktrees/ancient-yawning-biscuit; branch fix/ci-budget-arc-2026-09-22-waiter-default-and-stale-budgets; an unsigned local-only commit that was never pushed",
      "class": "path",
      "grounded": true,
      "evidence": "gh pr view 2017 -> headRefName fix/ci-budget-arc-2026-09-22-waiter-default-and-stale-budgets, headRefOid d873aed6. git log -1 --format='%h %G? %p %s' 18d3d5e3 -> '18d3d5e3 N e3186919 local-only: sequence-safety screen test (never pushed)'. git branch -r --contains 18d3d5e3 -> (empty)."
    },
    {
      "claim": "the 22 flood-2 harvestable PRs are 'not closeable'; 97 unmerged fleet PRs from 2026-09-01..06 were closed on 09-05/06",
      "class": "symbol",
      "grounded": true,
      "evidence": "notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md:265-266 -> '22 juniper-ml harvestable PRs whose production half is absent ... Not closeable'. gh pr list --repo pcalnon/juniper-ml --state closed --search 'created:2026-09-01..2026-09-06 author:app/cursor is:unmerged' -> 100 PRs; minus 3 with test/ heads, 97 are cursor/-headed. All were closed 09-05 (68) or 09-06 (32). The unstated scope is covered by the R4 minor finding."
    }
  ],
  "overall": "FAIL"
}
```
