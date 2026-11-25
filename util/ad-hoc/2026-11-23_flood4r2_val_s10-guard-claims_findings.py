#!/usr/bin/env python3
"""
Write the claims lens's findings.json for the agent guard 1.4.0 carrier (validator JL2b).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; text_fixes.json beside the output

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_findings.py <out findings.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CARRIER = "r18-guard (agent guard 1.4.0), 16 files staged in .claude/worktrees/agent-a0f16311d9dabda6f on 9d9ec797, tree 6dff6751; read from the session-10 staged copies (sha256 = both manifests)"

CHECKED = [
    "the 16 staged copies against the orchestrator's and the builder's manifests (sha256); the guard copies 4baecede (1.4.0) and 09c5db22 (1.3.0)",
    "every Closed spelling in pr_body.txt, commit_body.txt, changelog_entry.txt / CHANGELOG.md, docs/REFERENCE.md and the docstring: 63 payload probes, two guard copies, scratch home (logs/guardprobe.txt): all 63 denied by 1.4.0; 61 passed by 1.3.0 (C30/C31, written without a hop, 1.3.0 already denies)",
    "every Still-open spelling and 20 + 8 neighbours of the path-reading claim (logs/guardprobe_set2.txt, guardprobe_set3.txt); bash 5.3.9 printf-only in the scratch home for the open ones (logs/bashprint.json)",
    "pinning of each closed spelling: ast string constants of both staged suites plus the @ROOT@ templates (tests/test_claude_agent_guard.py:299, :314, :315); 3 named variants unpinned (F10); the 3 rows F10 adds pass on 1.4.0 and fail on 1.3.0 (BashRuleTests, 10 tests, logs/suite_new_bashrules.txt, suite_main_bashrules.txt)",
    "self-test: 66 of 66 on /opt/miniforge3/envs/JuniperCascor1 python 3.14.7 and /usr/bin/python3.9 3.9.25, staged copy and the text-fixed copy",
    "brace_expand unchanged: base vs staged on 35,671 words (test strings, all words of up to 5 characters over { } , . a backslash, 30,000 random), 0 differences (logs/brace_expand_diff.json)",
    "BashAnalyzer._path_word -> _path_alt: the body moved with one level of de-indentation and continue -> return (ast segments, base :1664 vs staged :2341)",
    "numbers from the builder's untouched round2/ logs (mtime 2026-11-16): census_final.log (44,678; 33 -> 2; 22 + 2 pass, 4 + 3 denied, 1 new denial; 54.77 s vs 125.72 s; hook 0.08-0.13 / 0.10-0.26 s); timing_jl1_final/main (33 shapes, max 3.73 s; SEVEN 1.3.0 timeouts); differential_final_s2026111[56].stdout (3,990/3,986/0/4; 18,885/18,864/0/21); candidates_378_final.json (298 + 80, 0 lost, 0 refused); v3_probe_final.json (59 rows; 41 reach + 3 marker rows + K-heredoc-case = 45; 1.3.0 passes 38); jl1_probe_final.json 136 rows; mutants_r2.log + mutants_r2b.json (48 + 3 = 51 of 53; M40, M41 survive); ci_list_final.txt (257 of 261; the same 4 fail on clean main); guard_suites_9_py39.txt (103 tests OK); jl1_diff_s4096001/s2718281 (80 + 46 command, 51 + 40 gh, 1 signing = 218)",
    "BashWordTest 22 + 7 = 29 words; AnalysisBoundTest six/sixteen cds, depths 4, 5, 8, LOOSE_SECONDS 8.0 (ast and source)",
    "sequence safety: the staged tree rebuilt twice without touching the carrier (write-tree over a COPY of its index; a private index from 9d9ec797 + the staged blobs): both 6dff6751; dangling unsigned probe commits; juniper-symbol-loss-check (juniper-ci-tools 0.9.1, CI's scope): body only exit 1 (WEAKENED method:BashAnalyzer._path_word, 35 -> 9 lines), body + trailer exit 0, trailer followed by an attribution paragraph exit 0; docs screen exit 0 (4 small-deletion warnings); the screen's parser (symbol_loss_check.py:418-444) matches the token on any line of base..head",
    "three-way of the 16 files onto origin/main cbb13154 (fetched 2026-11-23 21:3xZ; git show only, never S's working tree): 4 modified files clean and equal to staged, 11 helpers absent from main, docs/REFERENCE.md 2 conflicts (stamp sites)",
    "item 4: no CI-skip marker, no 'Overtoad', ruling citations only in the three prescribed forms (2,687 added or text lines, logs/textscan.json); '## Requirements' None verified (no JR id under notes/requirements on main names the guard); helpers' session/arc words match landed practice (66 landed flood4r2 helpers name it)",
    "stamps.json against the staged sites and today's main; AGENTS.md needs no change (no new suite file; main says 261, the CI list has 261)",
]

NOT_CHECKED = [
    "JL1's generator was not re-run: 117 of the 218 unsafe words are in no log (25 examples per category per seed), so 8(a) classifies the 101 kept",
    "the full CI regression list, pre-commit, the CodeQL prescreen and the mutation run: kept from the builder's round2/ logs; the 16 files' bytes are unchanged (sha256)",
    "the census itself (aggregates read from round2/census_final.log, not re-run)",
    "the 'v2.1.295' onFailure version (docstring :210-211): not re-fetched; turing's Claude Code version and macOS timings",
    "K-heredoc-case 'runs its command': its logged bash output is empty; JL1 reproduced it independently",
    "the D-14 pull request's own edits (not landed; the re-stamp rule covers it)",
]

FINDINGS = [
    {
        "id": "F1", "severity": "BLOCKER",
        "where": "CHANGELOG.md:416-418 and :449-451 (staged; changelog_entry.txt:13-15, :46-48); docs/REFERENCE.md:4319 and :4323; util/claude_agent_guard.py:116-118 and :189-194 (docstring); commit_body.txt:12-14, :36-38; pr_body.txt:23-26, :67-73. Mechanism: util/claude_agent_guard.py:779-795 (_spliced), :798-806 (_glob_pattern), :809-827 (_names_b), :830-841 (_can_be_b, 'a bare * is not counted'), :2389-2414 (_path_word_b)",
        "claim": "Every landing text says a substitution or parameter in a path 'may hold any text or none' 'at any position' (CHANGELOG, REFERENCE) for the credential directories, Claude's settings, the MCP files and the signing paths 'alike'. In the code a computed part is one placeholder read as '*', and a component that is ONLY computed, or a lone dot plus a computed part, is not counted, except as the first component under a home (a computed head) and inside ~/.claude. So a substitution, or a parameter without a :- default, that makes up a whole component passes 1.4.0 (and 1.3.0) while bash 5.3.9 builds the protected path: 'cp hook .git/$(printf %s hoo ks)/post-commit' and 'cp hook .git/$d/post-commit' plant a post-commit hook (the K12 class of JL1's F3); 'cp x ~/.config/$(printf %s gi t)/config', 'cp x ~/.config/$d/config', 'cp x /etc/$(printf %s gitc onfig)'; 'cat /x/$(printf %s .s sh)/config', 'cat ~/X/$(printf %s .s sh)/config', 'cat /x/.$d/config'; 'cp x /x/$(printf %s .mcp .json)'. No text names this class (the Still-open lists name only 'cat ~/.config/*/config'): a false efficacy claim on main, and a spelling left open unnamed against the owner's ruling of 2026-11-15.",
        "evidence": "Guard payloads, scratch home (logs/guardprobe_set2.txt, guardprobe_set3.txt): W01 'cat /x/$(printf %s .s sh)/config' new=PASS main=PASS; W03 'cp x ~/.config/$(printf %s gi t)/config' new=PASS; W04 'cp hook .git/$(printf %s hoo ks)/post-commit' new=PASS; W05 'cp hook .git/$d/post-commit' new=PASS; W09 'cat /x/.$d/config' new=PASS; O11 'cp x ~/.config/$d/config' new=PASS; X01 '.mcp.json' form new=PASS; X02 'cat ~/X/$(printf %s .s sh)/config' new=PASS; X06 '/etc/$(printf %s gitc onfig)' new=PASS. Controls denied: W08 'cat ~/X/../$(printf %s .s sh)/config' (first under home), W06/W07/X03/X04/X08 (inside ~/.claude), W12 '${x:-git}' (default reading), W14 '${d}t', W15 'h$(printf %s ooks)'. bash 5.3.9 printf-only (logs/bashprint.json): W01 -> /x/.ssh/config; W03 and O11 -> <home>/.config/git/config; W04 and W05 -> .git/hooks/post-commit; W09 -> /x/.ssh/config.",
        "fix": "Text (minimum; text_fixes.json rows F1): replace 'at any position' / the unscoped claim with 'wherever its path component also holds a literal character other than a leading dot' (CHANGELOG, changelog_entry.txt, REFERENCE, docstring, PR and commit bodies), and add to every Still-open list 'a substitution, or a parameter with no :- default, that makes up a whole path component or follows a lone dot, anywhere but the first component under a home or inside ~/.claude (cp hook .git/$(printf %s hoo ks)/post-commit, cp x ~/.config/$d/config, cat /x/$(printf %s .s sh)/config, cat /x/.$d/config)'. Code (optional, the owner's call): in _path_word_b count an only-computed component as 'hooks' after a component that can be .git, and as 'git' after a home's .config; doing the same for the dot-names would deny every 'cat /x/$d/config', so leave those named.",
    },
    {
        "id": "F2", "severity": "BLOCKER",
        "where": "CHANGELOG.md:446-447 (staged; changelog_entry.txt:43-44); pr_body.txt:133",
        "claim": "'1.3.0 runs past 60 s on eight of them': the log the texts rest on (round2/timing_jl1_main.txt / .json, the same 33 shapes) has SEVEN TIMEOUT>60s rows (cd-chain-16, nest-diverge-8, -10, -12, cd200-rel200, cd200-tplus200, cd200-tminus200; nest-case-12 took 11.87 s). A false count on main (the manifest repeats it).",
        "evidence": "count over round2/timing_jl1_main.json rows whose verdict is TIMEOUT>60s: 7; timing_jl1_main.txt lists the same seven.",
        "fix": "'60 s on eight of them)' -> '60 s on seven of them)' (CHANGELOG.md, changelog_entry.txt); pr_body.txt '(1.3.0 runs past 60 s on eight of them:' -> '(1.3.0 runs past 60 s on seven of them:' (text_fixes.json F2).",
    },
    {
        "id": "F3", "severity": "MAJOR",
        "where": "docs/REFERENCE.md:4323; CHANGELOG.md:445-451; util/claude_agent_guard.py:189-195; commit_body.txt:35-39 (the spelling appears only in pr_body.txt:121, Testing)",
        "claim": "The one non-printing spelling among the 101 kept unsafe words, s\"${x$':'-\"{u,Q}\"}\" id (a ${x:-...} default whose ':' is spelled $':'), stays open and is named only in the PR body's Testing paragraph: not in docs/REFERENCE.md nor any Still-open list, against the owner's ruling of 2026-11-15.",
        "evidence": "logs/guardprobe.txt O15 new=PASS main=PASS; logs/bashprint.json O15: bash 5.3.9 prints 'su' and 'sQ'; round2/jl1_diff_s4096001.json UNSAFE_new_cmd example 2.",
        "fix": "Add 'a parameter expansion whose operator is quoted (s\"${x$':'-\"{u,Q}\"}\" id)' to each Still-open list (inside the F1 rows of text_fixes.json for REFERENCE, CHANGELOG, changelog_entry.txt, the docstring, the PR and commit bodies).",
    },
    {
        "id": "F4", "severity": "MAJOR",
        "where": "pr_body.txt:55; commit_body.txt:23-24; CHANGELOG.md:430 (changelog_entry.txt:27); docs/REFERENCE.md:4320; util/claude_agent_guard.py:181-182",
        "claim": "Every Closed list says 'the lists bash expands inside a quoted backtick body' are closed, unscoped. They are closed in PATH words only; in a command or option word the same construct prints part of the word and passes 1.4.0 (d\"`echo \"{o,Q}\"`\"as id builds doas; gh api repos/o/r --inpu\"`echo \"{t,Q}\"`\" f builds --input): 47 of the 101 kept unsafe words. Also, the PR body's example written without a hop (cat ~/.ss\"`echo \"{h,x}\"`\"/config) is already denied by 1.3.0 (a computed first component under home), under a heading that says each closed spelling passed 1.3.0; the pinned row is the hop form (tests/test_claude_agent_guard.py:308).",
        "evidence": "logs/guardprobe.txt O14 new=PASS, C30/C31 main=DENY; logs/guardprobe_set2.txt V05 new=PASS, V01-V04 new=DENY main=PASS; logs/bashprint.json O14 -> doas, V05 -> --input.",
        "fix": "Scope the closed item to path words in all five texts, use the pinned hop form as the PR body's example, and name the backtick spelling in the PR body's printing-substitution item (text_fixes.json F4 rows and the PR-body F1 row).",
    },
    {
        "id": "F5", "severity": "MAJOR",
        "where": "commit_body.txt:44; stamps.json; docs/REFERENCE.md:5, :7, :9770 and the footer",
        "claim": "commit_body.txt names 'docs/REFERENCE.md 0.6.78', a site stamps.json does not list, and origin/main (cbb13154) already holds 0.6.78 (juniper-ml#2592's row, 2026-11-23; header and footer Last Updated 2026-11-23): the commit message would name the wrong version (0.6.79 today, higher after the D-14 pull request). The three-way onto origin/main conflicts only in docs/REFERENCE.md, at 2 stamp sites; the header Version merges silently to 0.6.78 (both sides made the same edit), so a clean header must not be trusted.",
        "evidence": "util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_threeway.py -> threeway/threeway.json: CHANGELOG.md, the guard and both suites conflicts=0, merged == staged (main == base for each); docs/REFERENCE.md conflicts=2 at :9770 (origin-main '| 0.6.78 | 2026-11-23 | juniper-ml#2592's edits ...' vs staged '| 0.6.78 | 2026-11-16 | The agent guard 1.4.0 ...') and :10352 (Last Updated 2026-11-23 vs 2026-11-16); the 11 helpers are not on main.",
        "fix": "commit_body.txt 'docs/REFERENCE.md 0.6.78 and CHANGELOG.md describe the change.' -> 'docs/REFERENCE.md and CHANGELOG.md describe the change.' (text_fixes.json F5); at landing apply stamps.json's rule (header = footer = row = main's version + 1, the landing date, the row after main's highest).",
    },
    {
        "id": "F6", "severity": "MINOR",
        "where": "util/claude_agent_guard.py:194 ('a whole name') and :147-148 (gap 2); CHANGELOG.md:451; docs/REFERENCE.md:4323; pr_body.txt:73; commit_body.txt:38",
        "claim": "The variable item disagrees across texts (docstring 'a whole name', the rest 'part of a name'), and 'a variable that holds part of a name' is closed when it sits beside a literal in its component (cat ~/X/../.ss${x}h/config and cat /x/$x.ssh/config are denied and pinned). What stays open is a variable that holds .. or / (d=~/.ss; cat ${d}h/config), plus F1's whole-component case.",
        "evidence": "logs/guardprobe.txt C08, C11 new=DENY; O04 and O09 new=PASS; O05/O06 (computed first component under home) DENY on both versions.",
        "fix": "'holds `..`, `/` or part of a name' -> 'holds `..` or `/`' (and the docstring's 'or a whole name' likewise); gap 2 'a variable that holds part of a name' -> 'a variable that holds a directory and part of a name' (text_fixes.json F6 rows and the F1 list rows).",
    },
    {
        "id": "F7", "severity": "MINOR",
        "where": "pr_body.txt:119",
        "claim": "'while passing the round-1 1.4.0' is arc-internal wording a PR reader cannot resolve.",
        "evidence": "pr_body.txt:118-119.",
        "fix": "'while passing the round-1 1.4.0 are down to 218' -> 'while passing this change's first draft are down to 218' (text_fixes.json F7).",
    },
    {
        "id": "F8", "severity": "MINOR",
        "where": "docs/REFERENCE.md:4322",
        "claim": "'nested $( ) with cd at every level, which took 25 s to over 60 s before the bound' describes an unreleased draft of 1.4.0; on main it reads as 1.3.0's cost, which was 0.09-0.15 s at depths 4-5 (over 60 s only from depth 8).",
        "evidence": "round2/timing_jl1_main.txt: nest-diverge-4 0.09 s, -5 0.15 s, -8 TIMEOUT; JL1 F2 (round-1 1.4.0 25.8 s / over 60 s).",
        "fix": "'(nested `$( )` with `cd` at every level, which took 25 s to over 60 s before the bound, is refused in 0.1 s)' -> '(nested `$( )` with `cd` at every level is refused in 0.1 s)' (text_fixes.json F8).",
    },
    {
        "id": "F9", "severity": "MINOR",
        "where": "util/claude_agent_guard.py:171",
        "claim": "Gap 12 opens 'which denies the spellings known to pass 1.3.0:', which reads as every spelling known to pass 1.3.0; the printing substitutions, F1's class and F3 also pass 1.3.0 and stay open.",
        "evidence": "logs/guardprobe.txt O01, O02, O15 and logs/guardprobe_set2.txt W01-W05: main=PASS new=PASS.",
        "fix": "'which denies the spellings known to pass 1.3.0:' -> 'which denies these spellings, each known to pass 1.3.0:' (text_fixes.json F9).",
    },
    {
        "id": "F10", "severity": "MINOR",
        "where": "tests/test_claude_agent_guard.py:304, :347, :406 (pr_body.txt:49 'with or without a hop', :64 'also over two lines'; docstring :184 'pke${x:-x}ec id')",
        "claim": "Three closed spellings the texts name have no pinned row: cat ~/X/../.ss{h,$'\\x7d'c}/config (the hop form), GLOBIGNORE=x + newline + cat ~/*/config, and pke${x:-x}ec id. Each is denied by 1.4.0 and passed by 1.3.0.",
        "evidence": "logs/guardprobe.txt C21, C58, C35: new=DENY main=PASS, pinned=none; with the three rows added, BashRuleTests passes on 1.4.0 (10 tests, logs/suite_new_bashrules.txt) and each new row fails on 1.3.0 (logs/suite_main_bashrules.txt).",
        "fix": "Add the three rows after :304, :347 and :406 (text_fixes.json F10, exact).",
    },
    {
        "id": "F11", "severity": "MINOR",
        "where": "stamps.json (the docs/REFERENCE.md timing site)",
        "claim": "The site is described as ('at most 3.2 s as the hook', '25 s to over 60 s'); the staged REFERENCE says 'under 4 s as the hook', so a re-stamp searching for the quoted phrase finds nothing.",
        "evidence": "docs/REFERENCE.md:4322 (staged) vs stamps.json sites[8].",
        "fix": "'('at most 3.2 s as the hook', '25 s to over 60 s')' -> '('under 4 s as the hook', 'refused in 0.1 s', '(16 relative `cd`s)')' (text_fixes.json F11).",
    },
]


def main(argv: list) -> int:
    counts = {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0}
    for f in FINDINGS:
        counts[f["severity"]] += 1
    report = {"carrier": CARRIER, "lens": "claims", "validator": "JL2b (flood-4 session 10)", "verdict": "SHIP-WITH-FIXES", "counts": counts, "checked": CHECKED, "not_checked": NOT_CHECKED, "findings": FINDINGS}
    Path(argv[1]).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
