# CI-budget re-evaluation -- consensus round 1, Rubric -- prompt-validator, iteration 1

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

```json
{
  "validator_status": "partial",
  "head_sha": "53d05121f6b97fc090197383c8fb35185fba00bf",
  "iteration": 1,
  "findings": [
    {
      "id": "R1.1",
      "severity": "major",
      "location": "§1 first prompt block, STATE — frozen file /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad/round1/HANDOFF_frozen_round1.md lines 57-60 (prompt block = lines 39-107)",
      "problem": "STATE says, in the past tense, that item 10 was 'closed on 2026-09-22 by ml#2017', that 'the same PR re-pinned three CI budgets', and that 'nothing is blocked'. ml#2017 is OPEN and unmerged. On origin/main the waiter still defaults to 1800 s, and juniper-data / juniper-data-client / juniper-deploy still sit at 2400 / 2400 / 700 s, below their observed maxima of 2589 / 2565 / 965 s. The source's own 'Validation record 2026-09-22 — In progress … completed before merge' is also dropped. No directive lands #2017, although the predecessor prompt in the same file made its open PR (#1862) REMAINING WORK item 1 ('Shepherd it. Until it merges, … NOT closed'). The source state 'fixed on an open PR' has been flattened to 'closed'.",
      "fix": "Make the first NON-OWNER item: 'Land ml#2017. It is BEHIND and allow_update_branch is false, so use the shepherd per MERGING. Until it merges, item 10 and the three re-pins are NOT on main.' Reword STATE conditionally ('closes when ml#2017 merges'). Give the PREFLIGHT an expected observable: `gh pr view 2017 --repo pcalnon/juniper-ml --json state,mergedAt` should read MERGED.",
      "evidence": "gh pr view 2017 --repo pcalnon/juniper-ml --json number,state,headRefOid,mergedAt,mergeStateStatus -&gt; state=OPEN, headRefOid=53d05121f6b97fc090197383c8fb35185fba00bf, mergedAt=null, mergeStateStatus=BLOCKED; re-read at 2026-09-22T20:46:41Z -&gt; mergeState=BEHIND, rollup NEUTRAL:5,SKIPPED:1,SUCCESS:21. git grep -n -E 'OWNER RULED|\"juniper-(data|data-client|deploy|cascor-worker|recurrence)\": [0-9]+' origin/main -- util/safe_merge.py -&gt; :278 \"juniper-data\": 2400, :306 \"juniper-data-client\": 2400, :308 \"juniper-deploy\": 700. tests/test_safe_merge.py:64-73 at 53d05121 -&gt; MEASURED_SPANS juniper-data (1651, 2589), juniper-data-client (1545, 2565), juniper-deploy (450, 965). git diff origin/main 53d05121 -- util/wait_for_checks.py -&gt; the `--timeout` default of DEFAULT_TIMEOUT=1800 becomes None/measured budget on the PR only. Frozen file lines 530-532: 'In progress … This subsection is completed before merge.' Frozen lines 131-132: '#1862 is OPEN, green, armed … Shepherd it. Until it merges, flood-2 §3 item 5 is NOT closed.'"
    },
    {
      "id": "R1.1",
      "severity": "minor",
      "location": "§1 first prompt block — STATE (frozen lines 57-60) and OWNER DECISIONS 2 (frozen lines 66-73)",
      "problem": "Three non-blocking source findings have no carrier. (a) The re-evaluation's planning-margin result: item 3 is 'Informational; re-measured', with 4 repos negative (canopy −1795, data −1514, cascor-worker −325, deploy −1), and the correction that relocation is NOT the remedy for a negative planning margin. PREFLIGHT's `all` runs `slack`, which prints 'negative: 4 [...]' with no disposition in the prompt. Meanwhile the SUPERSEDED block in the same file says 'RELOCATION IS THE REMEDY', and STATE's 'All ten … closed or ruled' overstates item 3. (b) Item 8's 'n = 1' caveat: only one post-fix lockfile week has been observed. (c) The walkthrough's promotion mechanics: promote in the ruleset, never via the Quality Gate's `needs:`, and drop the step's trailing `exit 0`.",
      "fix": "Add one line each. 'slack: 4 negative, informational only, do not start a relocation (docs/REFERENCE.md \"Memory-Budget Slack (Planning)\")'. 'lockfile arm verified on n = 1; re-check the next weekly PR'. In OWNER 2: 'if ruled yes, promote via the ruleset, never `needs:`; drop the trailing exit 0'.",
      "evidence": "Frozen file line 400 (item 3 row: 'Informational; re-measured — FOUR are negative now'), line 405 (item 8: 'one post-fix week, `n = 1`'), lines 485-495 (slack table), lines 508-511 ('It is not the remedy for a negative *planning* margin'). git show origin/main:notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md -&gt; lines 187-191 ('promote **in the ruleset** — never via the Quality Gate's `needs:`') and 269-271 ('dropping the step's trailing `exit 0`'). With S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad: sed -n '40,106p' $S/round1/HANDOFF_frozen_round1.md &gt; $S/drafted_prompt.txt; grep -n -i -E 'slack|margin|headroom|relocat' $S/drafted_prompt.txt -&gt; only the doc filename and 'SLACK_WEBHOOK_URL'; grep -n -i -E 'ruleset|needs:' $S/drafted_prompt.txt -&gt; only 'the rulesets are strict'. util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py:209 prints 'negative: {len(neg)} {neg}'."
    },
    {
      "id": "R1.3",
      "severity": "minor",
      "location": "§1 first prompt block — opening and PREFLIGHT (frozen lines 40-49)",
      "problem": "There is no objective line (the handoff template's 'Continue [TASK]…'), so the session's goal must be inferred from section labels. PREFLIGHT also drops the predecessor's anchor discipline: `git log --oneline -1 origin/main` and `gh pr list` carry no anchor SHA or expected observable, and nothing says #2017 is this arc's open PR. The bundle's anchor is d0582a21, and main moved to 56b14c2b during this validation.",
      "fix": "Open with 'Continue the CI-budget arc: land ml#2017, then NON-OWNER 1-2; surface OWNER 1-3 to the owner.' Add 'anchor d0582a21: `git log --oneline d0582a21..origin/main` non-empty = figures predate main' and 'expect #2017 (this arc's) among open PRs until it merges'.",
      "evidence": "git fetch origin --quiet &amp;&amp; git log --oneline -3 origin/main -&gt; 56b14c2b (#2018), d0582a21 (#2016), a2e63d1d (#2014). gh pr list --repo pcalnon/juniper-ml --state open -&gt; count=8 incl. #2017. Frozen lines 115-116 (predecessor: 'git log --oneline 6ccf80fa..origin/main   # non-empty = this document is already stale', '# 5 open at handoff, incl. #1862 (this arc's)'). Frozen lines 387-388 (re-eval anchor e3186919 through d0582a21)."
    },
    {
      "id": "R2.2",
      "severity": "major",
      "location": "§1 first prompt block — NON-OWNER WORK 1 (frozen lines 79-85)",
      "problem": "The acceptance criterion 'keep the 2 true positives and drop the 8 false ones' has no C4 sensitivity. The true positives are ml#1999 (C3) and #1969 (C2). Six of the 8 false findings are C4, so deleting C4 outright satisfies the criterion. That is the 'no longer fires' vs 'was removed' trap the repo pins with negative controls. The prompt does not mention those controls in tests/test_md_structure_check.py, including test_C4_reports_a_lost_heading_even_when_another_is_gained (## Beta → ## Gamma at an unchanged count must exit 1). It also names no command to replay the backtest or run the suite (R3.1).",
      "fix": "Add to acceptance that `python3 -m unittest -v tests/test_md_structure_check.py` stays green. Add new negative controls per class: a status-suffix or strikethrough rename passes; Beta→Gamma still fails; `git status` outside a fence still fires C2; a prose line opening `git).` or `make the …` does not. Name the replay command: `python3 util/ad-hoc/2026-09-05_md_structure_check.py --base &lt;base SHA from the annotation&gt; &lt;path&gt;` at each flagged head.",
      "evidence": "gh api repos/pcalnon/juniper-ml/actions/jobs/106669955808/logs (soak on ml#1999 head 276db114) -&gt; '[FAIL] notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md' / 'C3 1 NEW table row(s) with no header above'. gh api repos/pcalnon/juniper-ml/actions/jobs/106257046490/logs (#1969 head aab07eba) -&gt; '[FAIL] notes/backup_tests_pre-and-post_reboot.md' / 'C2 1 NEW command line(s) outside a fence (base has 0)'. Hence zero C4 true positives. grep -n -E '^\\s*def test_|1749|swallow|negative control' tests/test_md_structure_check.py -&gt; :189 test_C4_reports_a_lost_heading_even_when_another_is_gained, :198 test_C4_does_not_fire_when_headings_are_only_added, :218 test_a_vcs_command_left_outside_a_fence_is_now_reported, :228 test_ordinary_prose_beginning_with_a_covered_word_is_still_prose. .github/workflows/ci.yml:1066 'python3 -m unittest -v tests/test_md_structure_check.py'."
    },
    {
      "id": "R2.4",
      "severity": "major",
      "location": "§1 first prompt block — NON-OWNER WORK 1 (frozen lines 79-82)",
      "problem": "The pinned mechanism conflicts with the same item's acceptance criterion. 'C4 must accept a heading whose old text survives inside a renamed one' cannot achieve 'drop the 8 false ones'. In at least 2 of the 6 C4 PRs the renames drop words, so the old text does not survive. In #2009, 3 of the 5 flagged headings rewrote or trimmed text: '## 3. DECISION REQUIRED — repository secret, or environment secret?' became '## 3. RULED 2026-09-22 — Option B: …', and '(recommended)' and ', recommended' were removed. Only 2 were suffix appends. In #1976, the source's own example, '### 0.5 `JuniperCascor1` environment repair — owner has not ruled, asked 3+ times' became '### 0.5 ~~`JuniperCascor1` environment repair~~ — **MOOT, CLOSED 2026-09-21**', which drops words and inserts `~~`. The how is over-specified (R5), and the pinned how is insufficient. The prompt also transliterates the markers as '-- MOOT' / '-- NOT CHOSEN', but the files use an em dash.",
      "fix": "State the goal and constraints instead of the substring rule. Goal: a status-marking rename (suffix, strikethrough, a same-numbered section retitled) must not read as a loss. Constraints: normalise emphasis and strikethrough first, and the Beta→Gamma negative control must still fail. Or list the 6 C4 cases' before/after headings so the rule is designed against the real data.",
      "evidence": "With S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad: git diff --unified=0 --output=$S/pr2009.diff c4a67481^ c4a67481 -- notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md; grep -E '^[-+]#{1,6} ' $S/pr2009.diff -&gt; '-## 3. DECISION REQUIRED — repository secret, or environment secret?' / '+## 3. RULED 2026-09-22 — Option B: environment secrets in a dedicated `dockerhub` environment'; '-### Option B — a dedicated `dockerhub` environment (recommended)' / '+### Option B — a dedicated `dockerhub` environment — CHOSEN 2026-09-22'; '-### 5.2B Environment secrets (Option B, recommended)' / '+### 5.2B Environment secrets (Option B) — THE PATH, ruled 2026-09-22'; Option A and 5.2A are suffix-only. gh api repos/pcalnon/juniper-ml/actions/jobs/106896076110/logs (#2009 head 4ec55cbf) -&gt; 'C4 5 heading(s) LOST (count 19 -&gt; 19; the #1749 swallowed-heading signature, which a net count could hide)'. git log --oneline -S'MOOT, CLOSED 2026-09-21' origin/main -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md -&gt; 739a233c (#1976); git diff --unified=0 --output=$S/pr1976.diff 739a233c^ 739a233c -- &lt;that file&gt;; grep -n -E '^[-+]#{1,6} ' $S/pr1976.diff -&gt; '-### 0.5 `JuniperCascor1` environment repair — owner has not ruled, asked 3+ times' / '+### 0.5 ~~`JuniperCascor1` environment repair~~ — **MOOT, CLOSED 2026-09-21**' and '-### 5.1 `JuniperCascor1` is broken and the owner has not ruled' / '+### 5.1 ~~`JuniperCascor1` is broken~~ — **OBSOLETE as of 2026-09-21, the env is REPAIRED**'."
    },
    {
      "id": "R2.5",
      "severity": "major",
      "location": "§1 first prompt block — whole block (no git-status element); THIS DOCUMENT IS (frozen lines 51-54)",
      "problem": "The prompt states no branch, worktree, staged or uncommitted work, which the standing handoff convention requires (juniper-ml AGENTS.md 'How to Execute a Handoff' step 7; notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md Step 3.3). Here the omission is load-bearing. The first reading instruction, 'Read its § Re-evaluation 2026-09-22 first', targets a section that exists only as an uncommitted edit in worktree .claude/worktrees/ancient-yawning-biscuit (branch worktree-ancient-yawning-biscuit, HEAD 18d3d5e3, 'local-only … (never pushed)'). It is absent at origin/main and at #2017's head, because #2017 does not carry the doc. Main's copy of the file holds only the SUPERSEDED 2026-09-09 prompt ('PREFLIGHT — five commands', 'RELOCATION IS THE REMEDY'), so a fresh session following the pointer lands on obsolete instructions. #2017's walkthrough addition cites 'the re-evaluation in HANDOFF_2026-09-09_…md', so merging #2017 alone would leave main citing a section that is not there.",
      "fix": "Add a GIT STATUS block. Name the worktree and branch, say the re-evaluation and this prompt are uncommitted, and name the PR that will carry them (they must land with or before ml#2017). Until then, name the path to read them from.",
      "evidence": "git show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md | grep -n 'Re-evaluation 2026-09-22' -&gt; (no output). git show 53d05121:&lt;same path&gt; | grep -c 'Re-evaluation 2026-09-22' -&gt; 0. gh pr view 2017 --json files -&gt; 10 files, the handoff doc is not among them. git grep -n -E 'PREFLIGHT|RE-EVALUATED 2026-09-22|RELOCATION IS THE REMEDY|## Re-evaluation' origin/main -- &lt;same path&gt; -&gt; only :17 'PREFLIGHT — five commands. Run the third one TWICE, before and after a fetch.' and :76 'RELOCATION IS THE REMEDY, four traps (proven on ml#1754):'. git status --short -&gt; ' M prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md', '?? util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/'. git rev-parse HEAD -&gt; 18d3d5e38356af0919fcdcb0d088c4546d61caf4 ('local-only: sequence-safety screen test (never pushed)'). git diff origin/main 53d05121 -- notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md -&gt; '+&gt; **Mechanism corrected 2026-09-22** (the re-evaluation in' / '+&gt; [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](…)).' With S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad: grep -n -i -E 'branch|worktree|uncommitted|staged|git status|ancient-yawning' $S/drafted_prompt.txt -&gt; only the merge-lane lines (frozen 102-103)."
    },
    {
      "id": "R3.2",
      "severity": "major",
      "location": "§1 first prompt block, PREFLIGHT — frozen line 44 (exit semantics lines 46-47)",
      "problem": "The PREFLIGHT's only instrument, util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py, exists solely on ml#2017's branch and in this worktree. It is absent from origin/main, and ml#2017 is OPEN, unmerged and 1 commit BEHIND main. The prompt gives no stop-and-report, fallback or abort path for a session that starts from main. That session gets `python3: can't open file … [Errno 2]` with exit 2, the exact code the prompt defines as 'a probe could not measure'. The tool's absence therefore reads as the tool's own failure mode.",
      "fix": "Put `gh pr view 2017 --repo pcalnon/juniper-ml --json state,mergedAt,headRefOid` first in PREFLIGHT. If it is not MERGED, land it first (MERGING block), or run the probe from the PR ref (`git fetch origin fix/ci-budget-arc-2026-09-22-waiter-default-and-stale-budgets` plus a worktree on it). Add: 'if the script is absent, STOP and report; python exits 2 on a missing file, and that is not a probe result.'",
      "evidence": "git cat-file -e origin/main:util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -&gt; \"fatal: path 'util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py' exists on disk, but not in 'origin/main'\" (origin/main then d0582a21; it moved to 56b14c2b, and git show --stat 56b14c2b shows 2 unrelated files). git cat-file -e 53d05121:util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -&gt; present. git diff 53d05121 -- util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -&gt; empty. git rev-list --count 53d05121..origin/main -&gt; 1. gh pr view 2017 at 2026-09-22T20:46:41Z -&gt; mergeState=BEHIND. With S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad: python3 $S/no_such_dir/2026-09-22_ci_budget_handoff_reprobe.py all; echo rc=$? -&gt; \"python3: can't open file '…/no_such_dir/2026-09-22_ci_budget_handoff_reprobe.py': [Errno 2] No such file or directory\" rc=2."
    },
    {
      "id": "R3.3",
      "severity": "minor",
      "location": "§1 first prompt block — NON-OWNER WORK 1 (frozen lines 79-85)",
      "problem": "The work changes the engine of the CI job that OWNER 2 may promote to a required check, yet no independent cross-validation of the C4/C2 change is asked for before it is offered for promotion. The source doc itself goes through independent-agent consensus. Stakes are low while the job stays advisory.",
      "fix": "Add: 'Before the change is offered for promotion, have an independent agent validate it per notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md.'",
      "evidence": "grep -n -i -E 'advisory soak|md_structure_check|Markdown structure C1-C4' .github/workflows/ci.yml -&gt; :1608 '# Markdown structure C1-C4 -- ADVISORY SOAK. NEVER BLOCKING, and NOT in any ruleset.', :1632 'name: Markdown Structure (advisory soak)', :1677 'python3 util/ad-hoc/2026-09-05_md_structure_check.py --base \"$base\" \"${files[@]}\" …'. Frozen file lines 66 and 79 (promotion is the stated end state) and 530-531 (consensus procedure)."
    },
    {
      "id": "R3.4",
      "severity": "minor",
      "location": "§1 first prompt block — PREFLIGHT comments (frozen lines 45-49)",
      "problem": "Four statements about the tool and sandbox are inaccurate. (a) 'Each probe prints what could have made it read differently' is false for 2 of 9 probes; `settings` and `waiter` print no such line. (b) 'Exit 2 = a probe could not measure' holds in one direction only. `spans` and `rerun-split` append per-repo UNMEASURABLE rows and `alarm` records a webhook as 'unreadable' without raising, so exit 0 can still carry unmeasured rows. (c) 'rerun-split, soak and alarm are the slow probes' omits `spans`. It runs v2 for each of 9 repos at n=30, at 2 gh calls per head, which comes to ~540 calls against alarm's ~300. (d) The sandbox note covers only commands that name git, but the gate also refuses a `gh` loop over a runtime variable.",
      "fix": "Reword to: '7 of 9 probes print …; exit 0 does not mean every row measured, so grep the output for UNMEASURABLE/unreadable; spans is slow too; the gate also refuses loops that run gh over a variable.'",
      "evidence": "awk '/^def probe_/{name=$2} /could it read differently/{c[name]++} END{for(k in c) print k, c[k]}' util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -&gt; probe_alarm, probe_lockfile, probe_rerun_split, probe_slack, probe_soak, probe_spans, probe_structure (7); PROBES at :643 lists 9. python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py waiter -&gt; a single '[waiter] util/wait_for_checks.py DEFAULT_TIMEOUT=1800; per-repo budgets above it: 8 of 9 …' line, rc=0. reprobe.py:232-235, 293-295 and 327-329 append UNMEASURABLE rows without raising; :371 sets has_webhook=None without raising; :686 'return 2 if failed else 0'. util/ad-hoc/2026-09-08_measure_required_check_span_v2.py:180-216 makes two gh calls per head, and reprobe.py:225 runs v2 per repo. The sandbox refused this validator's `for r in juniper-ml …; do gh api \"repos/pcalnon/$r\" …; done` with 'runs gh with a value computed at runtime (the variable r) inside a construct too complex to verify'."
    },
    {
      "id": "R3.4",
      "severity": "minor",
      "location": "OWNER DECISIONS 2 evidence base (frozen lines 66-73); bundle artifacts .github/workflows/ci.yml:1698 and util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py:483,494",
      "problem": "Incidental defect in the evidence pipeline the prompt leans on. The soak step emits `::warning title=Markdown structure C1-C4 (advisory, exit ${rc})::`, but the comma ends the title property, so the API title is truncated to 'Markdown structure C1-C4 (advisory' and the exit code never reaches the API. The soak probe derives `screen_exit` from `exit (\\d)` in that title, which never matches. Every examined run's JSON `screen_exit` therefore reads 0, including runs that FAILed, and for the 11 unreadable-log runs a findings exit (1) cannot be told from a refusal (2).",
      "fix": "In ci.yml, encode the comma as %2C or drop it. In the prompt, note that `checks[].screen_exit` in the reprobe JSON is not the screen's exit code.",
      "evidence": "gh api repos/pcalnon/juniper-ml/check-runs/106872695251/annotations --jq '.[] | [.annotation_level, (.title // \"\"), ((.message // \"\")[0:110])] | @tsv' -&gt; 'warning | Markdown structure C1-C4 (advisory | findings against 836393cf4a9a4c1f1a1ce3d529cc08bd13357d44; see the job summary. Not blocking during the soak.' and 'notice | (empty title) | \"The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026. For more information, see https'. The same job's log (#2007 head f042bfec) shows '[FAIL] notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md' / 'C2 1 NEW command line(s) outside a fence', i.e. screen exit 1. .github/workflows/ci.yml:1698 -&gt; 'echo \"::warning title=Markdown structure C1-C4 (advisory, exit ${rc})::findings against ${base}; see the job summary. Not blocking during the soak.\"'. reprobe.py:483 'rc = next((re.search(r\"exit (\\d)\", a[\"title\"] or \"\") …' and :494 '\"screen_exit\": int(rc.group(1)) if rc else (0 if examined else None),'."
    },
    {
      "id": "R3.4",
      "severity": "minor",
      "location": "validator coverage, not a prompt defect (reason for validator_status=partial)",
      "problem": "The bundle has no formal head_sha/ttl stamp, so freshness was established by re-probe. PR #2017's head was unchanged at 53d05121. 8 of #2017's 10 files (every one the prompt cites) are byte-identical in the worktree. origin/main advanced d0582a21 → 56b14c2b (#2018) during validation, touching 2 unrelated files. The drafted block is identical in the frozen and worktree copies. Sampled rather than recounted, to stay frugal with the API: the soak aggregates (184 runs / 156 examined / 30 warnings / 10 distinct / 9 PRs). 4 of the 10 distinct findings were checked and all 4 match (#1969 C2 true, #1999 C3 true, #2007 C2-on-'make' false, #2009 C4 false). Not re-measured: '~2,500 REST calls', where a static count gives ~2,100 (plausible), and cascor-client's p90 1264 / max 1626, taken from the bundle. All git and grep commands ran in W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit. Known-miss ledger (R3.5): its single entry (register_or_reuse at collectors.py:120) is not re-asserted.",
      "fix": "None for the prompt. A round-2 validator can run `python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py soak` (~600 calls) if those counts become load-bearing.",
      "evidence": "gh pr view 2017 --repo pcalnon/juniper-ml --json headRefOid -&gt; 53d05121f6b97fc090197383c8fb35185fba00bf, both at start and at 2026-09-22T20:46:41Z. git diff --stat 53d05121 -- tests/test_safe_merge.py util/safe_merge.py util/wait_for_checks.py docs/REFERENCE.md notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md .github/workflows/lockfile-update.yml -&gt; empty. git diff 53d05121 -- util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py util/ad-hoc/2026-09-08_measure_required_check_span_v2.py -&gt; empty. git show --stat 56b14c2b -&gt; 2 files (…_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md, …ur-decisions-shipped-residue-is-owner-scoped.md). sed -n '39,107p' &lt;worktree doc&gt; | sha256sum and sed -n '39,107p' &lt;frozen file&gt; | sha256sum both -&gt; 9c16255b2547acca4811394f71e3b0556fd9a1ac366b8771761387b6cbee0f1d. Soak job logs read: 106257046490, 106669955808, 106872695251, 106896076110. cat prompts/agent_templates/data/known_misses.yaml -&gt; 1 miss (register_or_reuse)."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "§1 first prompt block — NON-OWNER WORK 2 (frozen line 87)",
      "problem": "'cascor-worker is the thinnest: max 2059 against 2400' has no unit, and in seconds it is false. The bundle's own MEASURED_SPANS put juniper-recurrence at 2000 − 1666 = 334 s, against cascor-worker's 2400 − 2059 = 341 s. cascor-worker is thinnest only as a ratio of budget (85.8% vs 83.3%). #2017's safe_merge.py comment makes the same claim explicitly in seconds ('clears the max by only 341 s -- the thinnest margin in the table'). Recurrence's p90 also rose from 587 to 1114.",
      "fix": "Write: 'thinnest: recurrence 334 s (1666/2000 = 83.3%) and cascor-worker 341 s (2059/2400 = 85.8%)'. Correct the #2017 comment to match.",
      "evidence": "tests/test_safe_merge.py:64-73 (worktree = 53d05121) -&gt; \"juniper-cascor-worker\": (1576, 2059), \"juniper-recurrence\": (1114, 1666). git grep -n -E 'OWNER RULED|\"juniper-(data|data-client|deploy|cascor-worker|recurrence)\": [0-9]+' origin/main -- util/safe_merge.py -&gt; :284 \"juniper-cascor-worker\": 2400, :321 \"juniper-recurrence\": 2000 (neither changed by #2017). git diff origin/main 53d05121 -- util/safe_merge.py -&gt; '# clears the max by only 341 s -- the thinnest margin in the table' and '# 09-22: p90 1114, max 1666 (27 clean heads; …) -&gt; window (1666, 4456]. 2000 stands.'; main's comment reads '# p90 587, max 1666 -&gt; window (1666, 2348]'."
    },
    {
      "id": "R4",
      "severity": "minor",
      "location": "§1 first prompt block — PREFLIGHT (frozen line 44)",
      "problem": "`&lt;scratch&gt;` is an unbound placeholder, and `--json` does not create parent directories. If the directory does not exist, the script raises FileNotFoundError and exits 1, but only after every probe has run (minutes, ~2,500 API calls). The JSON is lost, and exit 1 falls outside the prompt's 0/2 semantics.",
      "fix": "Bind it: `mkdir -p \"$SCRATCH\"` first, then pass `--json \"$SCRATCH\"/reprobe.json`, with SCRATCH set to the session scratchpad. Add 'exit 1 = crash, not a measurement'.",
      "evidence": "python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py waiter --json /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad/no_such_dir/reprobe.json -&gt; 'FileNotFoundError: [Errno 2] No such file or directory: …/no_such_dir/reprobe.json' rc=1, raised at the final write after the probes ran. reprobe.py:683-684 'if args.json: args.json.write_text(json.dumps(results, indent=2, default=list), encoding=\"utf-8\")' creates no directory."
    }
  ],
  "hallucination_risk": [
    {
      "claim": "util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py (PREFLIGHT instrument)",
      "class": "path",
      "grounded": true,
      "evidence": "git cat-file -e 53d05121:util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py -&gt; present; git diff 53d05121 -- &lt;path&gt; -&gt; empty (worktree copy = PR copy); git cat-file -e origin/main:&lt;path&gt; -&gt; \"fatal: path … exists on disk, but not in 'origin/main'\". In the bundle (PR #2017) but unreachable from main; see the R3.2 finding"
    },
    {
      "claim": "reprobe.py `all --json &lt;file&gt;`",
      "class": "flag",
      "grounded": true,
      "evidence": "reprobe.py:648 'ap.add_argument(\"probe\", choices=PROBES + [\"all\"])'; :652 'ap.add_argument(\"--json\", type=Path, help=\"also write every result to this JSON file\")'"
    },
    {
      "claim": "reprobe probes `rerun-split`, `soak`, `alarm` (and `settings`)",
      "class": "flag",
      "grounded": true,
      "evidence": "reprobe.py:643 'PROBES = [\"structure\", \"slack\", \"spans\", \"rerun-split\", \"alarm\", \"soak\", \"lockfile\", \"settings\", \"waiter\"]'"
    },
    {
      "claim": "Exit 2 = a probe could not measure",
      "class": "flag",
      "grounded": true,
      "evidence": "reprobe.py:678-681 'except Unmeasurable as exc: failed.append(name)'; :686 'return 2 if failed else 0'. One-directional; see the R3.4 minor finding"
    },
    {
      "claim": "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md",
      "class": "path",
      "grounded": true,
      "evidence": "git ls-tree origin/main -- &lt;path&gt; -&gt; 100644 blob 86b36727217beb86a1403d7681df4be8b3c048fc"
    },
    {
      "claim": "§ Re-evaluation 2026-09-22 of that document",
      "class": "path",
      "grounded": true,
      "evidence": "Present in the uncommitted worktree copy and the frozen file (line 381). git show origin/main:&lt;doc&gt; | grep -n 'Re-evaluation 2026-09-22' -&gt; no output; git show 53d05121:&lt;doc&gt; | grep -c 'Re-evaluation 2026-09-22' -&gt; 0. Unreachable from any ref; see the R2.5 finding"
    },
    {
      "claim": "notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md",
      "class": "path",
      "grounded": true,
      "evidence": "git ls-tree origin/main -- &lt;path&gt; -&gt; 100644 blob 0399491ccdf6aed883bf43d366c1a1c1b507cd43"
    },
    {
      "claim": "Item 10 (waiter 1800 s default) was DROPPED by the 2026-09-17 arc",
      "class": "symbol",
      "grounded": true,
      "evidence": "git show origin/main:notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md &gt; &lt;scratchpad&gt;/walkthrough_main.md; grep -n -i -E 'wait_for_checks|1800|waiter|item 10|^#{1,3} ' -&gt; heading lines only, no waiter mention. git diff origin/main 53d05121 -- util/wait_for_checks.py -&gt; on main `--timeout` defaults to DEFAULT_TIMEOUT = 1800"
    },
    {
      "claim": "ml#2017 closes item 10 and re-pins three CI budgets",
      "class": "symbol",
      "grounded": true,
      "evidence": "git diff origin/main 53d05121 -- util/safe_merge.py -&gt; juniper-data 2400-&gt;3300, juniper-data-client 2400-&gt;3300, juniper-deploy 700-&gt;1400; util/wait_for_checks.py --timeout default -&gt; the measured budget. Content grounded, but the PR is OPEN and unmerged (gh pr view 2017 -&gt; state=OPEN, mergedAt=null), so 'closed' is premature; see the R1.1 major finding"
    },
    {
      "claim": "SLACK_WEBHOOK_URL is set on juniper-ml only",
      "class": "env",
      "grounded": true,
      "evidence": "gh api repos/pcalnon/&lt;repo&gt;/actions/secrets --jq '… select(.==\"SLACK_WEBHOOK_URL\") | length' (9 literal calls) -&gt; ml 1, canopy 0, cascor 0, cascor-client 0, cascor-worker 0, data 0, data-client 0, deploy 0, recurrence 0"
    },
    {
      "claim": "PR-budget alarm runs daily on all nine repos, 0 breaches since 2026-09-17",
      "class": "symbol",
      "grounded": true,
      "evidence": ".github/workflows/pr-budget-alarm.yml:53 'cron: \"0 14 * * *\"'. gh api 'repos/pcalnon/juniper-ml/actions/workflows/pr-budget-alarm.yml/runs?per_page=10' -&gt; daily schedule runs 09-13..09-22, all success. gh api repos/pcalnon/juniper-ml/actions/runs/&lt;id&gt;/jobs for the 6 runs 09-17..09-22 -&gt; Slack step 'skipped' on all 6; that step is gated by `if: steps.count.outputs.level != 'OK'` (:148), so the level was OK every time. juniper-canopy -&gt; 6 schedule runs 09-17..09-22, all success. The other siblings rest on the bundle (frozen lines 418-420)"
    },
    {
      "claim": "job `Markdown Structure (advisory soak)` runs util/ad-hoc/2026-09-05_md_structure_check.py",
      "class": "symbol",
      "grounded": true,
      "evidence": "grep -n on .github/workflows/ci.yml (worktree and origin/main) -&gt; :1632 'name: Markdown Structure (advisory soak)', :1677 'python3 util/ad-hoc/2026-09-05_md_structure_check.py --base \"$base\" \"${files[@]}\"'"
    },
    {
      "claim": "soak live record: 184 runs, 156 examined, 30 warnings, 10 distinct findings across 9 PRs, 2 true / 8 false",
      "class": "symbol",
      "grounded": true,
      "evidence": "Bundle: frozen file lines 459-477 (11 unreadable + 17 idle + 156 examined = 184). Sample-verified 4 of 10 from soak job logs: #1969 aab07eba C2 (true), #1999 276db114 C3 (true), #2007 f042bfec C2 on 'make the credential stop working…' (false), #2009 4ec55cbf C4, 5 renamed headings (false). Aggregates not recounted"
    },
    {
      "claim": "status markers in headings ('-- MOOT, CLOSED 2026-09-21', '-- NOT CHOSEN')",
      "class": "symbol",
      "grounded": true,
      "evidence": "grep -rn 'MOOT, CLOSED 2026-09-21' prompts/ -&gt; HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md:436; grep -rn -E '^#{2,4} .*(MOOT, CLOSED 2026-09-21|NOT CHOSEN)' notes -&gt; JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md:97 and :205 ('— NOT CHOSEN'). The real separator is an em dash (bold on MOOT), not '--'"
    },
    {
      "claim": "cascor-client p90 1264 / max 1626; 3300 inside (1626, 5056]; ruled OUT 2026-09-15",
      "class": "symbol",
      "grounded": true,
      "evidence": "53d05121 util/safe_merge.py comment '09-22: p90 1264, max 1626 (28 clean heads) -&gt; window (1626, 5056], which now CONTAINS 3300'; 4 × 1264 = 5056. git grep origin/main -- util/safe_merge.py -&gt; :297 '# OWNER RULED 2026-09-15: the VALUE STANDS at 3300 and the row stays excluded from the'. Figures taken from the bundle, not independently re-measured"
    },
    {
      "claim": "util/ad-hoc/2026-09-05_md_structure_check.py (checks C2, C4)",
      "class": "path",
      "grounded": true,
      "evidence": "git ls-tree origin/main -&gt; 100644 blob 923a9ff3be2f9f05d5e5575d3e67c0a2fc750679; the soak logs label findings C2/C3/C4"
    },
    {
      "claim": "ml#1999 orphaned table row at heads ea4c3596 / 25c001bd / 276db114, fixed before merge",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh api 'repos/pcalnon/juniper-ml/pulls/1999/commits?per_page=100' -&gt; ea4c3596 25c001bd 276db114 7bc30e7b b8b2ec2a 94d3aa62 2ca164ed 5e507812 8e7a6d97 be82d281; gh pr view 1999 -&gt; MERGED 2026-09-22T09:55:30Z (43980f13). Soak log at 276db114 -&gt; 'C3 1 NEW table row(s) with no header above'. 'Fixed before merge' comes from the bundle and was not re-read"
    },
    {
      "claim": "notes/backup_tests_pre-and-post_reboot.md is a bash script saved as .md",
      "class": "path",
      "grounded": true,
      "evidence": "git ls-tree origin/main -&gt; 100755 blob 8e82efb6a8ce10af74316d8951e500def7f1b592; head -3 -&gt; '#!/usr/bin/env bash'"
    },
    {
      "claim": "cascor-worker max 2059 against 2400",
      "class": "symbol",
      "grounded": true,
      "evidence": "tests/test_safe_merge.py:69 (53d05121) '\"juniper-cascor-worker\": (1576, 2059)'; git grep origin/main -- util/safe_merge.py -&gt; :284 '\"juniper-cascor-worker\": 2400'. The 'thinnest' superlative is the R4 finding"
    },
    {
      "claim": "v2 (util/ad-hoc/2026-09-08_measure_required_check_span_v2.py) reads check-runs with the default filter=latest",
      "class": "symbol",
      "grounded": true,
      "evidence": "v2 line 184 'f\"repos/{slug}/commits/{sha}/check-runs?per_page=100\",' passes no filter parameter; #2017 adds the docstring section 'KNOWN DEFECT -- RE-RUN TAILS'"
    },
    {
      "claim": "canopy#653 read 33,299 s for a pass that failed at 10:08 UTC with one job re-run at 19:01",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh pr view 653 --repo pcalnon/juniper-canopy -&gt; MERGED 2026-09-22T19:08:50Z, head d724822331d9b30736faba2ae6402a3cac383666. gh api 'repos/pcalnon/juniper-canopy/commits/d724822…/check-runs?filter=all&amp;per_page=100' -&gt; 'UI Sub-suite (Playwright)' failure 09:53:23-09:58:37; 'Quality Gate' failure 10:08:19-10:08:23; 'UI Sub-suite (Playwright)' success 19:01:43-19:07:30; 'Quality Gate' success 19:08:22. 19:08:22 - 09:53:23 = 33,299 s"
    },
    {
      "claim": "pre-fix lockfile PRs ran ZERO jobs on attempt 1; closing the PR flips a parked run to failure",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh api 'repos/pcalnon/juniper-ml/actions/runs?head_sha=01ca9ba07174df562713495870a4cb0f973001e8&amp;per_page=50' (#1806's opening commit) -&gt; github-actions[bot] runs 34100534753 / 34100534750 / 34100534858, conclusion failure. attempts/1/jobs total_count -&gt; 0 (CI/CD Pipeline) and 0 (PR Base-Branch Guard). Run 34100534753 updated_at 2026-09-07T13:59:38Z"
    },
    {
      "claim": "the runner attaches a `notice` annotation (ubuntu-latest migration notice) to every job",
      "class": "symbol",
      "grounded": true,
      "evidence": "gh api repos/pcalnon/juniper-ml/check-runs/106872695251/annotations -&gt; notice 'The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026…' beside the soak warning. 1 job sampled; the soak check-runs on #1969, #1999, #2007 and #2009 each carry annotations_count=2"
    },
    {
      "claim": "allow_update_branch is FALSE on all nine repos",
      "class": "env",
      "grounded": true,
      "evidence": "gh api repos/pcalnon/&lt;repo&gt; --jq .allow_update_branch (9 literal calls) -&gt; false for ml, canopy, cascor, cascor-client, cascor-worker, data, data-client, deploy, recurrence"
    },
    {
      "claim": "rulesets are strict; every commit must be GitHub-signed",
      "class": "env",
      "grounded": true,
      "evidence": "gh api repos/pcalnon/juniper-ml/rulesets/13805432 -&gt; required_status_checks strict=true (17 contexts) plus required_signatures. gh api repos/pcalnon/juniper-data/rulesets/14748749 -&gt; strict=true (22) plus required_signatures. 2 of 9 repos sampled"
    },
    {
      "claim": "util/open_signed_pr.py for a new branch",
      "class": "path",
      "grounded": true,
      "evidence": "git ls-tree origin/main -&gt; 100644 blob 5563ce0781b90e829edd9196978c58496031418a; argparse :193 '--repo' required=True, :195 '--branch' required=True"
    },
    {
      "claim": "python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo pcalnon/juniper-ml --pr &lt;N&gt; --max-syncs 4 --per-pr-timeout 2700",
      "class": "flag",
      "grounded": true,
      "evidence": "git ls-tree origin/main -&gt; 100644 blob 74da3aa32efb434140885064813aa3d7bee675db; shepherd.py :209 --repo (default pcalnon/juniper-ml), :210 --pr (append, required), :211 --max-syncs, :213 --per-pr-timeout ('wall-clock bound per PR, seconds (default 45 min)')"
    },
    {
      "claim": "Sandbox: no loop, pipe, redirect or `python -c` string that names git",
      "class": "symbol",
      "grounded": true,
      "evidence": "The gate refused this validator's `for p in …; do git cat-file -e …; done` ('names git in a form too complex to verify') and a heredoc into the scratchpad; reprobe.py:15-17 says the same. It also refused a `gh` loop over a runtime variable, a wider restriction than stated (R3.4 minor finding)"
    }
  ],
  "overall": "FAIL"
}
```
