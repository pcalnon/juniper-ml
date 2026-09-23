# CI-budget re-evaluation -- consensus round 3, Rubric -- prompt-validator, iteration 3

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `f0b3cc73`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

```json
{
  "validator_status": "ok",
  "head_sha": "f0b3cc7331f311f23e87e35b4c7ac79eb76a9698",
  "iteration": 3,
  "findings": [
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md lines 945-946 (§ Validation record 2026-09-22, 'Round 3'), and first §1 block lines 53-54 (PREFLIGHT landing gate)",
      "problem": "NEW (a change in live state, not in the text): ml#2017 merged while this round was running. It merged at 2026-09-23T01:17:13Z, by pcalnon, as squash commit 7b226ca0 of final head 6f17aea5. The handoff file is byte-identical, and main's tree equals 6f17aea5's. Main's document of record therefore still says 'Round 3 ... in progress; this subsection is completed before merge'. The PREFLIGHT gate ('ml#2017 lands only once § Validation record ... records every consensus round as complete') was not honoured. The section the prompt says to read first now misstates its own validation state and records none of round 3's outcome. That is the residue-loss shape the re-evaluation itself warns about. The prompt's content is otherwise unaffected: its 'Expect MERGED' path is now the live one, and every figure re-probed this round was measured within minutes of the merge.",
      "fix": "Open a follow-up PR against main. In § Validation record, record that round 3 ran against f0b3cc73 and that ml#2017 merged before round 3 completed. Record round 3's outcome there too (this verdict's minor findings and whichever fixes are adopted). Drop the PREFLIGHT pre-merge clause, which can no longer be reached.",
      "evidence": "gh pr view 2017 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit,headRefOid,mergedBy -> {state: MERGED, mergedAt: 2026-09-23T01:17:13Z, merge: 7b226ca03ee37f809a187d4472b4e0d173bb80ae, head: 6f17aea5658ba649ef76da23d92cba5a2f3e1441, by: pcalnon}. git rev-parse f0b3cc73:<handoff> -> 23057174ec4dc7ee82146b81a8ee75c69a5434a6. gh api repos/pcalnon/juniper-ml/contents/<handoff>?ref=6f17aea5 --jq .sha and ?ref=7b226ca0 --jq .sha -> 23057174ec4dc7ee82146b81a8ee75c69a5434a6 for both. gh api repos/pcalnon/juniper-ml/commits/7b226ca0 and commits/6f17aea5 --jq .commit.tree.sha -> 36b5e41caadc6b12097501847ee4e19dc1f3b571 for both. gh api compare/f0b3cc73...6f17aea5 -> 1 commit, 'Potential fix for pull request finding CodeQL / Unused import', files ['util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round2-laneA/r2a_spans.py +1 -1']. Handoff lines 945-946: '**Round 3** — briefed on the round-2 corrections only: *in progress; this subsection is completed before merge.*'"
    },
    {
      "id": "R2.4",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 53-56 (PREFLIGHT pre-merge clause), against line 93 (OWNER DECISION 2) and lines 936-937 (owner ruling)",
      "problem": "Iteration-2 finding 2 (R2.4 major: the pre-merge path had no precondition) is RESOLVED: landing is now gated on the validation record. Remaining: the fix's rationale is stale. The clause says the merge request 'must put OWNER DECISION 2 to the owner, because ml#2017 ships the raises that decision is about'. But line 93 says 'THE THREE RAISES ARE RULED ... The general question stays open', and lines 936-937 say the owner ruled SHIP on 2026-09-22. Read literally, the clause asks the owner to rule again on the raises, or holds the merge on the open general question. The merge has now happened, so the clause cannot be acted on.",
      "fix": "Delete the clause, since it can no longer be reached. Otherwise reword it: 'note that OWNER DECISION 2's general question stays open; the three raises ml#2017 ships were ruled SHIP on 2026-09-22.'",
      "evidence": "sed -n 55,56p <handoff> -> '# and its merge-approval request must put OWNER DECISION 2 to the owner, because ml#2017' / '# ships the raises that decision is about.' sed -n 93p -> '2. Should CI budgets absorb runner queue? THE THREE RAISES ARE RULED: the owner approved'. sed -n 936,937p -> 'The three raises went to the owner with both cases; the owner ruled SHIP on 2026-09-22.'"
    },
    {
      "id": "R2.4",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 150-153 (NON-OWNER 1 C2 rule) and 158-159 (its control)",
      "problem": "Iteration-2 finding 1 (R2.4 major: the C2 directive contradicted its acceptance) is RESOLVED. Under the stated rule, all 15 existing tests keep their outcomes, and test_C2_counts_multiplicity still reports 2 new lines. #1980 clears at all 7 flagged heads and #2007 clears. #1969's true C2 finding still fires, because the line before it is a heading. Remaining: the rule skips the FIRST line of any command run glued to a prose line. So 'N contiguous commands must still count N' holds only for a run that starts a paragraph: a prose line followed by 3 commands counts 2, and a duplicated single command glued to prose goes from 2 to 0. The listed control 'three contiguous unfenced commands still count 3' passes only if its fixture puts a blank line first. No pass/fail result changes for N>=2.",
      "fix": "Skip only when the line before is prose AND the line after is not command-looking. That keeps a glued 3-command run at 3, still clears #1980 and #2007, and still fires #1969. Alternatively, restate the invariant as 'a run that starts a paragraph counts N'. Either way, require the 3-command control in both layouts: after a blank line and glued to prose.",
      "evidence": "Simulation, run as python3 -c: it loads util/ad-hoc/2026-09-05_md_structure_check.py via importlib, replaces CODEY's trailing \\b with (?=\\s), and applies the stated skip rule to head and base text fetched with gh api -H 'Accept: application/vnd.github.raw' at every soak replay pair. Output: '[1980] ... proposed-rule C2 new: 0' at all 7 heads; '[1969] aab07eba ... proposed-rule C2 new: 1'; '[2007] f042bfec ... proposed-rule C2 new: 0'; 'fixture multiplicity current: 2 proposed: 2'; '3 cmds after a BLANK line -> current: 3 proposed: 3'; '3 cmds glued to a prose line -> current: 3 proposed: 2'; '1 cmd glued to prose, duplicated -> current: 2 proposed: 0'. With the next-line clause added: '3 glued 3', '[1980] ... [0, 0, 0, 0, 0, 0, 0]', '[1969] ... [1]', '[2007] ... [0]'. python3 -m unittest -v tests/test_md_structure_check.py -> 'Ran 15 tests in 1.778s OK'."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 160-166 (NON-OWNER 1 REPLAY)",
      "problem": "Iteration-2 finding 4 (R4 major: the replay could not be run as written) is RESOLVED. The base now has a named source: the soak probe prints 'replay: head <sha> base <sha>', which this round's run showed. The screen's use of the current directory is stated correctly, and an absolute path from a detached worktree gives the intended comparison. Every flagged head yields the intended verdict. Remaining: many flagged heads are not in the local object store, and their PR branches are deleted. These include the final heads of #1976, #1973, #1983, #2009, #1980 and #2007, and every listed head of #1983 and #2007. PREFLIGHT's 'git fetch origin' does not bring them, so 'make a detached worktree at the flagged head' fails until the head is fetched explicitly. The prompt does not say how.",
      "fix": "Before the worktree step, add: 'if the head is not local, fetch it first: git fetch origin pull/<N>/head (the PR branch is deleted after merge)'.",
      "evidence": "git cat-file --batch-check marks these 'missing': 6b38ca8a (#1976 final head), 8c826f54 (#1973 final head), 71a2aad5 and b9377f64 (#1983, both heads), 4ec55cbf (#2009 final head), 5908be23 (#1980 final head), f042bfec (#2007, its only head). gh api graphql pullRequest(number: 1976/1973/1983/2009/1980/2007){headRef{name}} -> headRef null for all six. reprobe.py:637 prints 'replay: head {head} base {base}'. This round's soak run printed, e.g., 'replay: head f042bfeca754c80b479f003b666b29b296c1084c base 836393cf4a9a4c1f1a1ce3d529cc08bd13357d44'."
    },
    {
      "id": "R2.2",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 176-177 (NON-OWNER 2 DELIVERABLE)",
      "problem": "Iteration-2 finding 3 (R4 major: NON-OWNER 2 had no deliverable or decision rule) is RESOLVED. The rule's verdict strings match the instrument exactly, the report tool takes '<repo> <pr>', and today's run reproduces the ALREADY TRIPPED row. Remaining: the OK branch says 'record the date, n and each row's window' but names no file or PR to record it in. Also, first-pass does not output a window: its table and JSON carry max_pr and counts but no PR range. The window would have to be rebuilt with a separate gh pr list call, which can race the measurement. That cuts against the prompt's own trap: 'Quote a figure with its window, or not at all'.",
      "fix": "Name where the record goes, e.g. a dated line under § Re-evaluation in a follow-up PR, or the next handoff. Then either have first-pass print each repo's first and last PR, or say 'take the window from gh pr list --repo pcalnon/<repo> --state merged --limit 30, run in the same minute'.",
      "evidence": "python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py first-pass -n 30 --json <scratch>/fp.json -> exit=0. Output rows: 'juniper-ml 30 0 0 680 1061 #2003 2800 2720 1061 ABOVE 4x p90'; recurrence max 1666 against budget 2000; cascor-worker 2059 against 2400; cascor-client 1264/1626 OK. fp.json row keys: ['budget','four_p90','healthy','incomplete','margin','max','max_pr','p90','raw_max','repo','unhealthy','unmeasurable','verdict','worst_unhealthy_first_pass'], with no window. reprobe.py:401 sets the verdict to 'OK' / 'BELOW HEALTHY MAX' / 'ABOVE 4x p90'. laneB2/span_decompose.py:57 'repo, number = sys.argv[1], int(sys.argv[2])'."
    },
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 101-103 (OWNER DECISION 2, the HOLD case)",
      "problem": "Iteration-2 finding 7 (R1.1 minor: OWNER 2's balance) is RESOLVED. Both sides are present, along with the 09-08 lowering, the risk-threshold framing of the ceiling, the cost of holding and a keep-as-shipped option, and each checks out. Remaining: 'Every re-measure of an already-pinned budget has raised it' is literally false. On 09-22, six pinned budgets were re-measured and stayed where they were: ml, cascor, cascor-worker, canopy, cascor-client and recurrence. On 09-08, ml's 1500 and canopy's budget were re-measured and kept. What holds is narrower: no re-measure has lowered an already-pinned budget, and every change was a raise. As written, the sentence overstates the ratchet on the HOLD side of an open owner decision. util/safe_merge.py's dissent comment carries the same sentence.",
      "fix": "In both places, write: 'No re-measure has lowered an already-pinned budget; every change was a raise (09-22: 3 raised, 6 stood).'",
      "evidence": "grep -n 'stands' util/safe_merge.py -> 313 '2800 stands.', 325 '2800 stands.', 328 '2400 stands', 335 '3300 stands.', 377 '2000 stands'. git show 3cab4783^:util/safe_merge.py -> 238 '1500 kept from the 2026-09-05 re-tier', 251 'Kept at the ceiling'. git log -S'So do NOT raise a budget to absorb a queue' -- util/safe_merge.py -> 3cab4783 (2026-09-09) only, and git show db627616 -- util/safe_merge.py leaves that paragraph unedited, so the claim 'the paragraph itself was not edited' is correct."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md first §1 block lines 60-71 (PREFLIGHT reprobe command and exit legend)",
      "problem": "Iteration-2 finding 6 (R4 minor: $S unset, no --fetch, sandbox note too broad) is RESOLVED. The prompt now uses ${S:?}, 'all --fetch', the write pre-check and a narrower sandbox note, and all of them held in this session. Iteration-2 finding 5 (R3.2 minor: the exit-0 overclaim) is also RESOLVED. Remaining (1): 'set S in the same command' allows the prefix form S=<dir> python3 ... '${S:?...}', which fails because bash expands the argument before the assignment takes effect. It fails safe via ${S:?}, but the working form is 'S=<dir>; python3 ...'. Remaining (2): exit 2 has a second source that the legend omits. An unwritable --json path prints 'error: cannot write --json ...' and returns 2 with no UNMEASURABLE line.",
      "fix": "Show the working form explicitly ('S=<scratchpad>; python3 ...', or the literal path). Add 'or the --json pre-check refused' to the exit-2 legend.",
      "evidence": "unset S; S=/tmp/claude-1000 python3 -c '...' '${S:?set S to the session scratchpad}/reprobe.json' (double-quoted in the shell) -> '/bin/bash: line 1: S: set S to the session scratchpad', exit code 127. reprobe.py:795 prints 'error: cannot write --json {args.json}: {exc}' to stderr, then returns 2; reprobe.py:825 'return 2 if failed else 0'. In this session, a 'for n in ...; do gh pr view $n ...' loop was refused, while 'cd <worktree> && git cat-file ...' and 'git show ... | python3 -c ...' ran."
    }
  ],
  "hallucination_risk": [
    {
      "claim": "util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py: subcommands all/first-pass/soak/slack; flags --fetch, --json, -n; exit 0 means no probe refused, NOT that every row was measured [iteration-2 finding 5, R3.2 minor: RESOLVED]",
      "class": "flag",
      "grounded": true,
      "evidence": "git ls-tree f0b3cc73 lists the path. reprobe.py:50-53 docstring 'Exit 0 is NOT \"every row was measured\"'; :783-786 add_argument --fetch/-n/--json; :825 'return 2 if failed else 0'. This round: first-pass exit=0 while printing an 'ABOVE 4x p90' row. alarm, soak, settings, waiter, slack and lockfile each exited 0. fp.json read '{}' right after launch, which proves the write pre-check."
    },
    {
      "claim": "Soak probe prints 'replay: head <sha> base <sha>'; ci.yml logs 'examining N changed markdown file(s) against <sha>'; the screen reads the base via git show in the current directory and the head via open(path) [iteration-2 finding 4, R4 major: RESOLVED, residue above]",
      "class": "symbol",
      "grounded": true,
      "evidence": "reprobe.py:637; .github/workflows/ci.yml:1688 'echo \"examining ${#files[@]} changed markdown file(s) against ${base}\"'; util/ad-hoc/2026-09-05_md_structure_check.py:130-133 subprocess git show f'{base}:{path}' with no cwd, and :236-238 'with open(path) as f'."
    },
    {
      "claim": "C4: a substring rule clears 3 of the 11 lost headings; pairing on the same level plus the same leading identifier clears all 11",
      "class": "symbol",
      "grounded": true,
      "evidence": "git show --format='COMMIT %h' --unified=0 739a233c 2dec7631 3b656b57 78e36d8e c4a67481 200409f5 -- '*.md' | python3 -c <pairing sim> -> 'lost headings: 11 substring-cleared: 3 identifier-cleared: 11' (substring clears 0.6, Option A and 5.2A). The same simulation against API-fetched text at all 21 flagged C4 head/base pairs -> lost == cleared at every head."
    },
    {
      "claim": "tests/test_md_structure_check.py::test_C4_reports_a_lost_heading_even_when_another_is_gained and ::test_C2_counts_multiplicity_so_duplicated_commands_are_seen; the C2 rule is consistent with them [iteration-2 finding 1, R2.4 major: RESOLVED, residue above]",
      "class": "symbol",
      "grounded": true,
      "evidence": "Defined at tests/test_md_structure_check.py:167 and :189; python3 -m unittest -v tests/test_md_structure_check.py -> 'Ran 15 tests ... OK'. The simulation of the stated C2 rule leaves every fixture's count unchanged (multiplicity 2, VCS 1, pytest 1, makeshift 0)."
    },
    {
      "claim": "PREFLIGHT pre-merge precondition gated on § Validation record 2026-09-22 [iteration-2 finding 2, R2.4 major: RESOLVED, residue above]",
      "class": "path",
      "grounded": true,
      "evidence": "§ Validation record 2026-09-22 is at handoff line 863, with Round 3 at line 945. ml#2017 is now MERGED (7b226ca0), so the clause can no longer be reached."
    },
    {
      "claim": "NON-OWNER 2: decision rule verdicts; span_decompose.py <repo> <pr>; recurrence 334 (1666/2000); cascor-worker 341 (2059/2400); deploy p90 262 on 09-08; data p90 955 -> 1651; ml 680/1061 (#2003), 4x p90 = 2720, 80 s over; pinned (910, 2005) from #1981-#2014 [iteration-2 finding 3, R4 major: RESOLVED, residue above]",
      "class": "symbol",
      "grounded": true,
      "evidence": "The first-pass run this round printed these rows. util/safe_merge.py:307-313 records '09-22: p90 910, max 2005 (30 healthy heads, window #1981-#2014)' and 'At 680, 2800 exceeds 4x p90 (2720) by 80 s'. :320 'Was p90 955 / max 2126 on 09-09'; :362 'Was p90 262 / max 375 ... on 09-08'. laneB2/span_decompose.py:21 usage 'span_decompose.py juniper-data 405'."
    },
    {
      "claim": "OWNER 1: SLACK_WEBHOOK_URL is set on juniper-ml only; the alarm runs daily on all nine; no breach since 2026-09-17; juniper-ml's 54 runs include 8 breaches (4 WARN, 4 ALARM, 2026-08-06..09-05), each of which ran its Slack step; on the siblings a breach without the webhook is a ::warning::",
      "class": "env",
      "grounded": true,
      "evidence": "python3 ...reprobe.py alarm -> 'juniper-ml alarm=present webhook=yes runs=54 2026-07-31..2026-09-22 {OK: 46, ALARM: 4, WARN: 4}'. The 8 non-OK runs fall 2026-08-06..2026-09-05, each with 'slack step ran: True'. The eight siblings show 'webhook=NO runs=6 2026-09-17..2026-09-22 {OK: 6}'; exit=0. pr-budget-alarm.yml:142 'PR budget: total=... level=$level', :148 'if: steps.count.outputs.level != OK', cron '0 14 * * *'. juniper-data's copy at :164 has '::warning title=PR budget ${LEVEL} with no Slack webhook::'."
    },
    {
      "claim": "OWNER 2: four of nine budgets at TIMEOUT_CEILING 3300; maxima 2589/2565/965; queue share 64-82%; 'do NOT raise a budget to absorb a queue'; the WITHDRAWN (1) note of 2026-09-10; the 09-08 lowering from 2400 to 700; the 09-09 raises (ml 1500->2800, recurrence 700->2000); the ceiling is a risk threshold, not a hard bound; both cases written above REPO_TIMEOUTS",
      "class": "symbol",
      "grounded": true,
      "evidence": "util/safe_merge.py:199 'The CEILING is a RISK threshold, not a hard bound'; :211 TIMEOUT_CEILING = 3300; :248-260 the owner's ruling and both cases; :285 'So do NOT raise a budget to absorb a queue'; REPO_TIMEOUTS has canopy, cascor-client, data and data-client at 3300. git show b26acd62 (2026-09-08) adds deploy 700 and recurrence 700. git show 3cab4783 (2026-09-09) raises ml 1500->2800 and recurrence 700->2000. The waiter probe matches every budget."
    },
    {
      "claim": "OWNER 3: 10 distinct findings, 2 true and 8 false, the 8 false ones still present at the PR's FINAL head (6 C4, 2 C2); promotion by the FINAL exit 0 -> exit \"$rc\", plus the early exit 0 on a failed git diff; PROMOTION PATH comment; ruleset, not needs: [iteration-2 finding 8, R1.1 minor: RESOLVED]",
      "class": "symbol",
      "grounded": true,
      "evidence": "python3 ...reprobe.py soak -> 'DISTINCT findings ...: 10; PRs flagged at their FINAL head: [1969, 1973, 1976, 1980, 1983, 1992, 2007, 2009, 2024]', with 65 PRs examined at about 01:10 UTC; the prompt's 62 is stamped 00:50. ci.yml:1636-1642 PROMOTION PATH; :1645 job name; :1674-1677 the early 'exit 0'; :1717 the final 'exit 0'. gh api repos/pcalnon/juniper-ml/rules/branches/main -> 17 contexts, strict true, soak absent. ml#1955 mergedAt 2026-09-18T00:37:10Z."
    },
    {
      "claim": "OWNER 4: cascor-client p90 1264 / max 1626; 3300 lies inside (1626, 5056]; ruled 2026-09-15",
      "class": "symbol",
      "grounded": true,
      "evidence": "first-pass row 'juniper-cascor-client 30 0 0 1264 1626 #163 3300 5056 1626 OK'. util/safe_merge.py 'OWNER RULED 2026-09-15: the VALUE STANDS at 3300'."
    },
    {
      "claim": "OWNER 5: 97 unmerged juniper-ml PRs on cursor/ branches created 2026-09-01..06, closed on 09-05/06; the Cursor app has 100 unmerged in that window on juniper-ml (3 on test/) and 138 fleet-wide; flood-2 said 'not closeable' [iteration-2 finding 10, R4 minor, '97' scope: RESOLVED]",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh pr list --repo pcalnon/juniper-ml --state all --search 'created:2026-09-01..2026-09-06' --limit 1000 -> cursor/ heads 100 (97 CLOSED, 3 MERGED), closed dates {2026-09-05: 65, 2026-09-06: 32}; Cursor-app unmerged 100 (cursor 97, test 3). gh search prs --owner pcalnon --created 2026-09-01..2026-09-06 --state closed --merged=false -> 138 (ml 100, data 30, canopy 8); --state open -> 0. notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md:265-266 'Not closeable — the test is the evidence'."
    },
    {
      "claim": "Merge tooling: safe_merge.py --repo/--pr/--execute; gh pr merge --squash --auto; shepherd --repo/--pr/--max-syncs/--per-pr-timeout, never merges, returns NOT-ARMED; open_signed_pr.py refuses an existing branch; 2026-09-08_push_signed_commit.py appends to an EXISTING branch; PUT /contents does not sign",
      "class": "flag",
      "grounded": true,
      "evidence": "util/safe_merge.py:1143-1163; util/ad-hoc/2026-09-05_auto_merge_shepherd.py:48 'Never merges', :189 'return \"NOT-ARMED\"', :209-213; util/open_signed_pr.py:276 'REFUSED: branch ... already exists'; 2026-09-08_push_signed_commit.py docstring 'Append ONE GitHub-signed commit to an EXISTING branch' and 'YubiKey'; 2026-09-22_push_signed_commit.py@f0b3cc73 'REST PUT /contents does NOT sign'."
    },
    {
      "claim": "allow_update_branch is FALSE on all nine repos, and the rulesets are strict",
      "class": "flag",
      "grounded": true,
      "evidence": "python3 ...reprobe.py settings -> allow_update_branch=False on all 9, admin=True, exit=0. gh api repos/pcalnon/{juniper-ml,juniper-cascor,juniper-cascor-client,juniper-cascor-worker,juniper-data-client}/rules/branches/main -> strict true, checked this round. Iteration 2 checked canopy, deploy, recurrence and data -> true."
    },
    {
      "claim": "Four repos have a negative planning margin; docs/REFERENCE.md 'Memory-Budget Slack (Planning)' says not to start a relocation on that basis; the lockfile App-token arm is proven on n = 1 (#1970), with a weekly PR",
      "class": "path",
      "grounded": true,
      "evidence": "python3 ...reprobe.py slack (no --fetch; every local origin/main matched the API) -> 'negative: 4 [juniper-canopy, juniper-cascor-worker, juniper-data, juniper-deploy]', exit=0. docs/REFERENCE.md:2416 heading; :2473 'do not start a relocation because headroom < `max`'. reprobe.py lockfile -> tally {app/github-actions: {NO RUN: 5, PARKED: 13}, app/juniper-release-train: {EXECUTED: 1}}. .github/workflows/lockfile-update.yml:46 cron '0 8 * * 1'."
    },
    {
      "claim": "GIT STATE: local branch worktree-ancient-yawning-biscuit = e3186919 + 18d3d5e3 (unsigned, never pushed); the modified tracked files are identical to the PR head; five lane scripts are tracked in ml#2017 [iteration-2 finding 9, R1.1 minor: RESOLVED]",
      "class": "path",
      "grounded": true,
      "evidence": "git branch --show-current -> worktree-ancient-yawning-biscuit. git log -1 --format='%h %G? parents=%p' 18d3d5e3 -> '18d3d5e3 N parents=e3186919'; git branch -r --contains 18d3d5e3 -> empty. git diff --stat f0b3cc73 -- <the 15 modified files> -> empty, and 6f17aea5 touches none of them. git hash-object of the 5 lane scripts equals the blobs in git ls-tree f0b3cc73 (0e07b0b3, 5ef091e6, 238bb688, 686c877f, 4db27ea9)."
    },
    {
      "claim": "Relocation pointer to the four traps in the SUPERSEDED second §1 block; the Option B table row notes that '(recommended)' was dropped; v1 filters NOTHING; v2 uses filter=latest; markdown_structure_check.py is the engine of the required gate and md_structure_check.py of the soak [iteration-2 finding 10, R4 minor, relocation pointer and Option B row: RESOLVED]",
      "class": "path",
      "grounded": true,
      "evidence": "Handoff lines 318-325 hold the four traps; line 699 is the Option B row, ending '(`(recommended)` dropped)'. util/ad-hoc/2026-08-20_measure_required_check_span.py:7 'filters NOTHING'. v2:91-92 'filter=latest ... WITHIN EACH WORKFLOW RUN'. util/markdown_structure_delta.py:103 SCREEN = ...2026-09-05_markdown_structure_check.py, run at ci.yml:1605 in 'Documentation Links', a required context. ci.yml:1690 runs md_structure_check.py in the soak."
    },
    {
      "claim": "The required link checker verifies same-file anchors only; no tracked file links an old anchor",
      "class": "symbol",
      "grounded": true,
      "evidence": "juniper-doc-tools/juniper_doc_tools/check_doc_links.py:292-296 validates an anchor only when file_part is empty. git grep -E over the 11 old anchor slugs at d594a9d3 -- '*.md' -> no matches."
    },
    {
      "claim": "canopy#653 read 33,299 s for a pass that failed at 10:08 and had jobs re-run at 19:01; #1806 was closed at 13:59:37Z and reopened at 13:59:38Z",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh api repos/pcalnon/juniper-canopy/commits/d7248223/check-runs?filter=all -> Quality Gate failure at 10:08:19Z, UI Sub-suite re-run at 19:01:43Z, Quality Gate success at 19:08:19Z; the first-pass raw max for canopy was 33299. gh api repos/pcalnon/juniper-ml/issues/1806/timeline -> 'closed 2026-09-07T13:59:37Z', 'reopened 2026-09-07T13:59:38Z'."
    }
  ],
  "overall": "PASS"
}
```
