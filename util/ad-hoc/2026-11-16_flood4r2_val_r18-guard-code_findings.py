"""
Write the r18-guard code lens's findings.json (validator JL1) from Python literals, so the shell spellings it quotes
keep their exact backslashes and quotes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py and its sibling helpers

Usage: python3 <this file> <out findings.json>
"""

import json
import sys
from pathlib import Path

LOGS = "tmp/flood4r2-val/r18-guard-code-lens/logs/"

CHECKED = [
    "Carrier verify: the 13 files of agent-a0f16311d9dabda6f hash to manifest.json's sha256 (guard 522a16f3, tests a2b15e8e / 2282a516, REFERENCE adb0db25, CHANGELOG 9147c0fb, 8 helpers); main's guard copy 09c5db22 = 1.3.0. Re-verified at the end.",
    "Own worktree juniper-ml--val--flood4r2-r18-guard-code--20261116-0206--edea2eb1 (detached edea2eb1, carrier files copied in); guard diff read in full (+740/-86), DESIGN.md, test additions (167 lines, 0 deletions), the builder's mutant strings for M07/M33/M40/M41.",
    "Item 1 efficacy, own probe helper util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py (payload-only guard copies; bash 5.3.9 printf/markers, HOME = scratch home, PATH = an EMPTY dir so only builtins run): B1, B1-cmd, B2 x3, B3 x4 (incl. outside a home), N1 x4 (sudo, gh api, git -S, nested in $( )), N2 x5, N3, N4 (2-line + hop), N5 x2, N6 (~+ from home, cd ~ && ~+), N7 x2, N8 x3, the quoted backtick / ${x:-\"..\"} quirks, escaped $, the case in an expanded here-document, .git/refs/../hooks, ~/.git{config,x}, disable{AllHooks,x}: bash reaches the target or runs the marker, main PASSES, 1.4.0 DENIES every one. N4 on one line does not reach (bash syntax error); ~- was already denied by main. Logs: probe_rows.json, probe_rows2.json, probe_rows3_literals.json, probe_rows4_signing.json, probe_rows5_r1seq.json, probe_rows6_runner_calibration.json.",
    "Item 1 differential with an OWN generator (util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_differential.py: 29 compositional spelling ops at a random split point, 1-2 per name; home / hop / ~+ / relative / absolute prefixes; 5% quoted past-cap list glued, 3% unquoted past-cap, 8% decoy list), targets = every protected path name the rules list (.ssh .gnupg .claude/settings*.json .claude/hooks .claude.json .gitconfig .config/git .mcp.json .git/hooks) + sudo/su/doas/pkexec + gh api write flags; seeds 4096001 (n=20,000) and 2718281 (n=10,000). UNSAFE on 1.4.0: 0 for the CRED, SELF and MCP targets; 1,145 signing-path words; 565 PRIV command words; 383 gh write-flag words (main is UNSAFE on all of those and on 11,192 more path words). main DENY -> 1.4.0 PASS: 0. Logs: differential_s4096001.*, differential_s2718281.*.",
    "Item 2 soundness: the union holds for DENIALS on every corpus (differential 30,000, suite strings 1,722 judgements, 378 candidates, census 44,678): no DENY->PASS; one DENY->REFUSE (synthetic, still blocked). 'Any text' for substitutions holds for the CRED/SELF/MCP path rules only (F3, F4). R1: modelled runners (bash -c, eval, here-string, heredoc, pipe, quoted $( ), python3 -c, osascript -e, xargs sh -c, find -exec sh -c) stay REFUSED; unmodelled runners pass (F1) but already pass main with brace-free spellings.",
    "Item 3: 378 candidates main->1.4.0: DENY->DENY 298, PASS->DENY 80, 0 lost, 0 refused (util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_corpus.py, logs/corpus.json). Every Bash-like string in the 9 guard suites, both cwds: DENY->DENY 777, PASS->DENY 105, REFUSE->REFUSE 30, REFUSE->PASS 6 (the intended R1 rows), PASS->PASS 804. Census with main's helper (newest 200 transcripts today, aggregates only): 44,678 commands; refused 33 -> 2; 31 changes, all from refusals (22 cap->ok, 2 operand->ok, 4 letter-seq->CRED-PATH-BASH, 3 seq-with-brace->GH-API-WRITE); no denial lost, no new refusal (logs/census_r3.log).",
    "Item 4 cost: census slowest as the hook main 0.085-0.163 s, 1.4.0 0.108-0.243 s; adversarial shapes as the hook (util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_timing.py, _profile.py): see F2. The words-made budget refuses with exit 2 (fail closed; pinned test passes on 3.9 and 3.14). onFailure semantics read from code.claude.com/docs/en/hooks.",
    "Item 5: self-test 63/63 under /usr/bin/python3.9 (3.9.25) and JuniperCascor1 python3.14 (3.14.7), both -I; the 2 changed suites on 3.9: 78 tests OK; all 9 guard suites on 3.14.7: 100 tests, 9/9 pass (util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_suites.py). No import added (stdlib only); resolve_homes/_is_installed_copy/_password_home untouched by the diff, and test_installed_copy_ignores_the_test_override passes on both.",
    "Item 6: the builder's own mutant strings on scratch copies (util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_mutants.py; pristine copy unchanged): M07 and M33 are KILLED by one row each (F6); M40 (memo) changes no decision and no time on the slow shapes (25.8 s vs 27.2 s); M41 equivalent by analysis (_heredoc_word yields no delimiter at a third '<').",
    "Item 7: dotglob and GLOBIGNORE need no prior call (one line); aliases need a second line in the same call, and this host's Claude Code shell snapshot already runs shopt -s expand_aliases; functions defined in the same call are DENIED by both; variables are gap 2 (not demonstrated, J4 section 0).",
]

NOT_CHECKED = [
    "Turing itself: its Claude Code version (whether onFailure: block is honoured, F11) and its /usr/bin/python3; macOS bash 3.2 / zsh behaviour (out of scope by the docstring).",
    "CI's whole regression list (260 suites) was not re-run: the carrier touches only the guard, its two suites and two docs; the builder's 256/260 with the same 4 failing on clean main was not re-derived.",
    "pre-commit, CodeQL prescreen, G-PATH/G-TMP on the carrier's 13 files, and the two sequence-safety screens (the builder's logs, not re-run).",
    "A full new mutation run (only the four survivors were re-examined).",
    "The census's 22 cap->ok commands one by one (aggregates only, by rule).",
    "Timing on macOS hardware (turing): every time here is this Linux host's; the ratios, not the seconds, carry over.",
]

FINDINGS = [
    {
        "id": "F3",
        "severity": "BLOCKER",
        "where": "CHANGELOG.md:329-332; docs/REFERENCE.md:4308; util/claude_agent_guard.py:114-116 (docstring) and :2254-2299 (_path_word_b) with :2548-2559 (Context.is_signing_mention)",
        "claim": "The landing texts say every path rule reads a substitution or parameter as any text or none at any position and that the signing paths count on the normalised readings; the signing check does neither. is_signing_mention compares the readings literally, so a splice or a glob in .git/hooks, ~/.gitconfig or ~/.config/git passes 1.4.0 (and main): `cp hook .git/ho$(:)oks/post-commit` plants a hook (the K12 class), `cp x ~/.gitc?nfig` overwrites the gitconfig. Every one of the 1,145 UNSAFE path words in the differential is a signing path.",
        "evidence": "python3 -I util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py run ... --only SG-...: SG-hook-splice / SG-hook-param / SG-cfg-glob / SG-xdg-splice / SG-xdg-glob: bash builds .git/hooks/post-commit, <home>/.gitconfig, <home>/.config/git/config; main=PASS new=PASS; literal forms main=DENY new=DENY (GIT-SIGNING-CONFIG) (" + LOGS + "probe_rows4_signing.json). Differential: UNSAFE_new_path_label_SIGN 772 + 373 = UNSAFE_new_path 772 + 373 (" + LOGS + "differential_s4096001.txt, differential_s2718281.txt).",
        "fix": "Code (preferred, small): in BashAnalyzer._path_word_b, judge the signing names with _names_b as the other names are judged: on each home rest, rest[0] can be .gitconfig (len 1) or rest[:2] can be (.config, git); anywhere, a component that can be .git followed by one that can be hooks -> GIT-SIGNING-CONFIG; pin `cp hook .git/ho$(:)oks/post-commit`, `cp x ~/.gitc?nfig` and `cat ~/.config/gi?/config`. Text minimum if the code is not changed: CHANGELOG.md:329 'A substitution or parameter is one part that may hold any text or none' -> 'For the credential, Claude-settings and MCP names, a substitution or parameter is one part that may hold any text or none', and add to every Still-open list: 'a substitution or glob inside a signing path (`cp hook .git/ho$(:)oks/post-commit`, `cp x ~/.gitc?nfig`)'; the same scoping in docs/REFERENCE.md:4308 ('Two path readings are added: each substitution or parameter is one part' -> 'Two path readings are added: for the credential, Claude-settings and MCP names, each substitution or parameter is one part') and the docstring :114.",
    },
    {
        "id": "F2",
        "severity": "MAJOR",
        "where": "util/claude_agent_guard.py:1740-1769 (_scan: all_bases = the union of both readings' bases, fed to both readings' nested scans) with BashAnalyzer._cd_bases (unchanged: every relative cd doubles the bases); PR body (tmp/flood4-fix/r18-guard/pr_body.txt:111-114) and REPORT 'worst shape 1.40 s ... a new per-command cap near 2 s'",
        "claim": "1.4.0's total time is not bounded near 2 s: a 102-byte command takes the hook 25.8 s (main 0.10 s) and a 124-byte one over 60 s (main 0.17 s), past the installed 10 s timeout. The words-made budget does not cover it: the time is the path rules run against bases that compound across nested texts the two readings cut differently. A 121-byte form ending `; cat ~/.ssh/config` is denied by main in 0.15 s and by 1.4.0 only after 29.0 s. Pre-existing on main in a milder form: 12 relative cd's take main 1.61 s (1.4.0 5.34 s) and 16 (122 bytes) over 60 s on both. Real commands are unaffected (census max 0.243 s).",
        "evidence": "python3 -I util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_timing.py ... --shapes nest-diverge-4..7: 'nest-diverge-4 102 B main=0.10s new=25.82s M40=27.24s'; 'nest-diverge-5 124 B main=0.17s new=TIMEOUT>60s'; main depth 6 0.66 s, depth 7 4.76 s, depth 8 (190 B) over 60 s on both; 'nest-case-6 254 B main=0.15s new=TIMEOUT>60s', 'nest-case-8 334 B main=0.52s new=TIMEOUT>60s' (a case pattern's ) as the divergence: main stays fast); control 'nest-plain-12 102 B main=0.10s new=0.12s' (no divergence, no cd: no blowup); 3,000 unclosed $( : RecursionError, exit 2 on both in 0.09 s (fail closed) (" + LOGS + "timing_controls.json);'nest-diverge-4-cred 121 B main=0.15s DENY new=28.97s DENY'; 'cd-chain-12 90 B main=1.61s new=5.34s'; 'cd-chain-16 122 B main TIMEOUT>60s new TIMEOUT>60s' (" + LOGS + "timing_nest_sweep.json, timing_cred_and_cdchain.json). Profile, depth 3 (1.8 s, 21 scans): _has_cred_component 29,079 calls, _inside 100,900 (" + "util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_profile.py). Shape: nest_diverge(d) = 'echo $(' + per level 'cd aK; : $(<inner>) # )' + newline + 'cd bK' + ')'.",
        "fix": "Bound the bases and fail closed: in _cd_bases raise MalformedInput('a command whose cd targets make more than %d directories cannot be analysed') once out passes a cap (e.g. 64), and in _scan give each reading's nested texts that reading's own bases rather than the union (or cap all_bases the same way); pin nest_diverge(5) and a 16-cd chain to finish in under 1 s (refused or judged). Correct the PR body's timing paragraph: '... keeps that work near 2 s.' -> '... keeps that work near 2 s; the hook's total time is still unbounded (a command with nested $( ) and relative cd's can exceed the 10 s timeout on both versions, sooner on 1.4.0).'",
    },
    {
        "id": "F4",
        "severity": "MAJOR",
        "where": "util/claude_agent_guard.py:1771-1797 (_bash_view keeps computed words verbatim), :1902-1911 (_opaque dispatches a computed command word only on a literal fragment that is itself a guarded name), docstring gap 12 :172-176; CHANGELOG.md:349-351; docs/REFERENCE.md:4311; PR body 'Still open' (lines 50-56)",
        "claim": "Gap 12 stays open, unnamed, for COMMAND and OPTION words: an empty substitution or parameter, a parameter default or a quoted-backtick brace list spliced into a command, option, subcommand or key word passes every command rule on main and 1.4.0 while bash builds the guarded word. `sud\"$(:)\"o id` and `pkex$(:)ec id` run sudo/pkexec (only `su$(:)do` is denied, because `su` is itself guarded); `gh api --meth$(:)od=POST`, `--fi$(:)eld`, `--fiel${x:-d}`, `git commit --gpg-$(:)sign`, `git push --sig$(:)ned`, `git -c commit.gpg$(:)sign=true`, `security find-generic-pass$(:)word`, `gpg --export-secret-k$(:)eys`, `defaults wr$(:)ite`, `git config user.signing$(:)key`, `git config core.hooks$(:)Path`, `claude mcp a$(:)dd`, `echo disable$(:)AllHooks` all pass; each literal form is denied.",
        "evidence": "probe rows S-* (15 spellings, 8 rules) main=PASS new=PASS, L-* literal controls DENY (" + LOGS + "probe_rows.json, probe_rows2.json, probe_rows3_literals.json); differential UNSAFE_new_cmd 358 + 207 of 798 + 486 reaching, UNSAFE_new_gh 222 + 161 of 828 + 622 reaching (" + LOGS + "differential_s*.txt).",
        "fix": "In _bash_view, judge a third view of each segment in which every word with computed spans is replaced by its text with each span removed (the empty reading) and each ${x:-WORD} by WORD, with every rule (deny if any reading trips one); that denies all 15 spellings above. Name what stays open (a substitution that prints the text, `sud$(printf o) id`) in the four Still-open lists, and pin `sud\"$(:)\"o id`, `gh api --meth$(:)od=POST repos/o/r` and `git commit --gpg-$(:)sign -m x`. Text minimum: add to each Still-open list 'an empty substitution or parameter spliced into a command or option word (`sud\"$(:)\"o id`, `gh api --meth$(:)od=POST`, `git commit --gpg-$(:)sign`): only the path rules read a substitution as any text'.",
    },
    {
        "id": "F5",
        "severity": "MAJOR",
        "where": "util/claude_agent_guard.py:173-174 (docstring gap 12); CHANGELOG.md:349; docs/REFERENCE.md:4311; PR body line 52",
        "claim": "dotglob / GLOBIGNORE need no prior call or line: `shopt -s dotglob; cat ~/*/config` and `GLOBIGNORE=x; cat ~/*/config` on ONE line reach ~/.ssh/config (bash sets the option at run time, before the glob is expanded); main and 1.4.0 both pass. The texts ('after shopt -s dotglob', '`shopt -s dotglob`, then `cat ~/*/config`') read as a separate earlier step.",
        "evidence": "probe rows open-dotglob-1line, open-globignore-1line: bash prints <home>/.ssh/config; main=PASS new=PASS (" + LOGS + "probe_rows.json). This host's Claude Code shell snapshot runs `shopt -u dotglob`, so the agent must set it in the call, and one line suffices.",
        "fix": "Code (cheap): when the command text names dotglob or GLOBIGNORE, read every glob component directly under a home as the bare-dot rule reads `.*` (deny `~/*/config`), and pin `shopt -s dotglob; cat ~/*/config` and `GLOBIGNORE=x; cat ~/*/config`. Text minimum: CHANGELOG.md:349 '`shopt -s dotglob`, then `cat ~/*/config` (and `GLOBIGNORE`)' -> '`shopt -s dotglob; cat ~/*/config` in one command (and `GLOBIGNORE=x; cat ~/*/config`)', and the same spelling in the docstring, docs/REFERENCE.md:4311 and the PR body.",
    },
    {
        "id": "F6",
        "severity": "MAJOR",
        "where": "tests/test_claude_agent_guard.py (CRED_PATH_CASES, SSH_PRIV_DEFAULTS_CASES); PR body (tmp/flood4-fix/r18-guard/pr_body.txt:107-110); REPORT.txt / manifest.json mutations.survived",
        "claim": "The PR body says the M07 and M33 survivors are masked by another layer; each is killed by one row the suite lacks, so two live parts of the new reading (a $( ) inside double quotes in _brace_mask, and $'...' in _step_over) are unpinned. With M07 the guard passes `cat /x/.ss\"$(: '\"')\"{h,x}/config` (the computed-head rule masks it only under a home); with M33 it passes `: ${x:-{$'\\''}; sudo id; : '}'` (reading A does not catch it: main passes it too).",
        "evidence": "util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_mutants.py (the builder's strings) + probe --guard M07=... --guard M33=...: 'K-M07 reach=YES new=DENY(CRED-PATH-BASH) M07=PASS()'; 'K-M33 reach=YES new=DENY(PRIV-ESCALATION) M33=PASS()'; bash builds /x/.ssh/config and runs the marker; main passes both (" + LOGS + "probe_mutants.json, probe_rows.json).",
        "fix": "Add to CRED_PATH_CASES: (\"cat /x/.ss\\\"$(: '\\\"')\\\"{h,x}/config\", CRED_BASH) and to SSH_PRIV_DEFAULTS_CASES: (\": ${x:-{$'\\\\''}; sudo id; : '}'\", PRIV); re-run the mutation helper (39 of 41 expected); PR body 'Of the four that survive, two are masked by another layer (...), one removes a memo (performance only) and one is equivalent.' -> 'Two of the survivors are killed by rows this PR adds; of the other two, one removes a memo (performance only) and one is equivalent.'",
    },
    {
        "id": "F1",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:1799-1807 (_expand returns [] for a word reading A would refuse) and docstring :117; CHANGELOG.md:342-348; docs/REFERENCE.md:4310",
        "claim": "R1's deferral also passes quoted text that a LATER shell expands, when the program that runs it is one the guard does not model: `script -q /dev/null bash -c 'cat ~/.ss{h,x}/config {a..{c,d}}'` (any refusal reason defers, not only the cap), and with a 66-way list `script -qc`, `flock lk -c`, `npx -c`, `tmux new-session -d`, `make -f - <<<`, `ssh-agent bash -c`, a git `!` alias: main REFUSED, 1.4.0 PASSES, the inner bash builds ~/.ssh/config. No new capability: the same runners already pass main with brace-free spellings (`script -q /dev/null bash -c 'cat ~/.ss$(:)h/config'`, `npx -c 'cat ~/.ss\"\"h/config'`), i.e. gap 1. But the docstring's 'a brace list bash really expands past MAX_BRACE_ALTERNATIVES still fails closed' holds only for text the guard reads as a command.",
        "evidence": "probe rows R1-script-bsd, R1-script-gnu, R1-flock, R1-npx, R1-tmux, R1-gitalias, R1-make, R1-sshagent, R1q-script-seq, R1q-flock-seq: main=REFUSE new=PASS, reach=YES; R1-bashc/eval/herestr/heredoc/pipe/comsub-dq/python/osascript/xargs-sh/find-sh: REFUSE on both; G1-* calibration: main=PASS new=PASS (" + LOGS + "probe_rows.json, probe_rows2.json, probe_rows5_r1seq.json, probe_rows6_runner_calibration.json).",
        "fix": "Docstring :117 'so a brace list bash really expands past ``MAX_BRACE_ALTERNATIVES`` still fails closed,' -> 'so a brace list bash really expands past ``MAX_BRACE_ALTERNATIVES`` in text the guard reads as a command still fails closed,'; and add to gap 1: 'a program that hands its argument to a shell the guard does not model (``script``, ``flock -c``, ``npx -c``, ``tmux``, ``ssh-agent``, a git ``!`` alias): since 1.4.0 a quoted brace list it would expand is no longer refused'.",
    },
    {
        "id": "F7",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:174-175 (docstring gap 12); CHANGELOG.md:349-350; docs/REFERENCE.md:4311",
        "claim": "Aliases: one call suffices (two lines), and in Claude Code's own shell no shopt line is needed (this host's shell snapshot runs `shopt -s expand_aliases` before every command), so `alias s=sudo` + newline + `s id` runs sudo; both versions pass (the texts say this accurately). Functions are over-stated: functions defined in the same command are DENIED by both (`f() { sudo id; }; f`, `f() { \"$@\"; }; f sudo id`, `f() { $1 id; }; f sudo`).",
        "evidence": "probe rows open-alias-2line (marker ran; both PASS), open-alias-1line (does not run), F-body / F-args / F-indirect (both DENY PRIV-ESCALATION) (" + LOGS + "probe_rows.json, probe_rows2.json); the newest file under ~/.claude/shell-snapshots/: line 83 'shopt -s expand_aliases' (only shopt lines read).",
        "fix": "Judge each `alias NAME=VALUE` value as a nested command string (denies `alias s=sudo`, `alias g='gh api -X POST'`); and in the docstring/CHANGELOG/REFERENCE replace 'aliases and functions defined earlier in the same command or in the shell's profile' with 'aliases defined earlier in the same command, and aliases or functions from the shell's profile'.",
    },
    {
        "id": "F8",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:583 (and :670, :673)",
        "claim": "On the second reading these refusal reasons quote the MASKED text, so private-use placeholders reach the reason the agent and the Overtoad see: `cat $HOME/.'$'{Y/../s{Q,,}Z}sh/config` is refused with evidence `$HOME/.'\\ue005'{Y/../s{Q,,}Z}sh/config` (U+E005 for $).",
        "evidence": "python3 -I work/guard_new.py < work/payload_lost.json -> stderr ends \"... differently): $HOME/.'\\ue005'{Y/../s{Q,,}Z}sh/config\" (printed with ascii()).",
        "fix": ":583 '% _evidence(text[pos:]))' -> '% _evidence(text[pos:].translate(_UNMASK)))'; :670 and :673 '_evidence(amble)' -> '_evidence(amble.translate(_UNMASK))'.",
    },
    {
        "id": "F9",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:1786-1797 (_bash_view -> bash_brace_expand refusal)",
        "claim": "One word main DENIES is REFUSED by 1.4.0 (still blocked, exit 2 instead of a deny): `cat $HOME/.'$'{Y/../s{Q,,}Z}sh/config` (reading B's scan sees a sequence with a brace inside). Synthetic only; the census has no new refusal.",
        "evidence": "differential LOST_main_deny_new_REFUSE 1 of 30,000 (" + LOGS + "differential_s4096001.json).",
        "fix": "None needed (fail closed). Optionally: when reading A has already recorded a hit, report the deny rather than the refusal.",
    },
    {
        "id": "F10",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:175 and gap 2 (:138-139)",
        "claim": "Variables (gap 2) need no prior call: an assignment and its use in one command is ordinary bash (`p=~/.ss; cat ${p}h/config`). By design (gap 2) and not demonstrated here (the J4 brief's section 0 forbids demonstrating gaps 1-11).",
        "evidence": "bash semantics; no probe run (by rule).",
        "fix": "None (by design); optionally say 'in the same command' in gap 2's sentence.",
    },
    {
        "id": "F11",
        "severity": "MINOR",
        "where": "util/claude_agent_guard.py:184-189 (Settings entry; unchanged lines)",
        "claim": "`\"onFailure\": \"block\"` is honoured only from Claude Code v2.1.295 (code.claude.com/docs/en/hooks: 'Requires Claude Code v2.1.295 or later'; without it 'a timed-out command ... hook doesn't block the tool call'). On an older Claude Code on turing, any command the guard cannot finish in 10 s runs unchecked, on main (16 relative cd's, 122 bytes) and sooner on 1.4.0 (102 bytes, F2).",
        "evidence": "WebFetch of https://code.claude.com/docs/en/hooks (onFailure row; Timeouts section); timing in F2.",
        "fix": "Owner check: run `claude --version` on turing (>= 2.1.295). Docstring: after '\"onFailure\": \"block\"}]}]}' add 'onFailure needs Claude Code v2.1.295 or later; an older one lets a timed-out call through.'",
    },
]


def main(argv: list) -> int:
    out = Path(argv[0])
    report = {
        "carrier": "r18-guard: agent guard 1.4.0, %s (staged, base edea2eb1, guard sha256 522a16f3)" % (Path.home() / "Development" / "python" / "Juniper" / "juniper-ml" / ".claude" / "worktrees" / "agent-a0f16311d9dabda6f"),
        "lens": "code",
        "validator": "JL1 (session 9)",
        "worktree": str(Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-ml--val--flood4r2-r18-guard-code--20261116-0206--edea2eb1"),
        "verdict": "SHIP-WITH-FIXES",
        "counts": {"BLOCKER": sum(f["severity"] == "BLOCKER" for f in FINDINGS), "MAJOR": sum(f["severity"] == "MAJOR" for f in FINDINGS), "MINOR": sum(f["severity"] == "MINOR" for f in FINDINGS)},
        "checked": CHECKED,
        "not_checked": NOT_CHECKED,
        "findings": FINDINGS,
    }
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print("written: %d findings %s" % (len(FINDINGS), report["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
