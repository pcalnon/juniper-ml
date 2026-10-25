# Handoff — turing bring-up: C9 landed (guard 1.2.0 covers Serena's edit tools and MCP registration); H6 audited; owner decisions and the guard install next

- **From:** the 2026-10-25 session on turing named "dev env macos" (014c35; worktree `.claude/worktrees/breezy-baking-lerdorf`). It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md`. Its author, "mac dev" (165a0b), could not be reached (HTTP 409), and no other session was on that handoff.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.6.
  - §18.2 holds the C9 and H6 rows.
  - §18.3 holds errata E-C9 and E-H6.
- **This file is the arc's main handoff.** It supersedes `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` and continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md`. Both now point here; the option-B handoff's owner steps still stand.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2322 | `3f38956f` | **C9.** `util/claude_agent_guard.py` 1.2.0: MCP-EDIT-PATH, MCP-REGISTER-BASH and MCP-REGISTER-FILE, and a settings matcher that names Serena v1.7.0's 19 edit tools and its shell (`--settings-matcher`, read by `util/install_claude_agent_guard.bash`). 48 tests, 10 of them new; self-test 50 of 50; `util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py` kills 26 of 26 mutants, each by its own pin |
| this handoff's PR | — | **H6** and the record: `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (the `auditor` agent; 19 findings, 2 blocker), its evidence script `util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`, plan v1.4.6 by `util/ad-hoc/2026-10-25_turing_c9_h6_record.py`, and this file |

## State (2026-10-25)

- **The guard on `main` is 1.2.0; turing runs no guard.** C8 was never installed (`~/.claude/hooks/` does not exist), so neither C8, K12 nor C9 binds any session yet.
- **What C9 changes for agents once installed:**
  - Serena's edit tools cannot reach `.git/`, `.ssh` or `.gnupg`, Claude's settings or hooks, the owner's git configuration, `~/.claude.json` or a `.mcp.json`.
  - Serena's `execute_shell_command` gets the Bash rules.
  - `claude mcp add*`, `add-json` and `add-from-claude-desktop` are denied whatever the command word, and so is `--mcp-config`.
  - **`cat ~/.claude.json` is denied** (Bash, by mention, as `~/.gitconfig` is); the Read tool still reads it.
  - `claude mcp list`, `get`, `remove` and `reset-project-choices` stay allowed, and `util/mcp_setup.bash` keeps working.
- **H5, option B** is intact: the hardening check exited 0 at 08:13:41Z with `--offline`. B.5 is still pending (both `origin`s set).
- **H6:** none of VS Code's four servers has ever started from VS Code on turing (VS Code's newest log session is 2026-03-26). The decisions are the owner's.

## Owner steps

1. **C8 install, now including K12 and C9.** From a real terminal, in the primary checkout:

   ```bash
   git pull --ff-only origin main
   bash util/install_claude_agent_guard.bash --apply   # copies 1.2.0, self-tests it, merges the hook entry
   bash util/install_agents.bash                        # 9 agent links: H2's acceptance
   ```

   A 1.1.0 entry, if any, is replaced in place. H3 then has every dependency it waits on.
2. **H6's decisions** (the audit's §8). Order matters:
   - **Before anything else, decide the scope.** Settings Sync carries the user `mcp.json` to every synced host (H6-X3).
   - **Remove VS Code's `oraios/serena` entry before E-H4-WHEEL's wheel build.** That build leaves cryptography 50.0.0 in uv's cache, which would also let the unpinned entry start; its `main` defaults new users to an exec-capable REPL (SER-P1).
   - **Rotate the Hugging Face token** at huggingface.co: it sat in plaintext in `mcp.json` and in the sync service (HF-P1). Then run token-less, or reference a new read-only token through a password input; or remove the server.
   - Remove `microsoft/markitdown`, or pin it as §8.2 says.
   - Keep `upstash/context7`, used only after K13.
   - Set `"chat.mcp.autostart": "never"` and `"chat.mcp.gallery.enabled": false`, and delete the 20 unreferenced inputs.
3. **Unchanged from the option-B handoff:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers` before the first backup;
   - C2's firewall form.
4. **E-H4-WHEEL** (Serena on turing), after step 2's Serena removal. Also unchanged: A1, `~/.condarc` `ssl_verify: true`, the JuniperPython `PYTHONPATH` unset, F2/A6, F3 node mode, and the signing order (no YubiKey into turing until C8 is installed with K12, and K13 is done).

## Agent next

1. **H4's usage report** (E-H6; the owner decides first): Serena v1.7.0 reports usage to `oraios-software.de` on every start unless `SERENA_USAGE_REPORTING=false`, and `util/mcp_setup.bash` writes `"env": {}`. The fix is the variable in the entry, plus `tests/test_mcp_setup.py`'s pins.
2. **C2's gate follow-up**, once the owner chooses C2's form: G-SEC's firewall condition and its hint at `util/host_state_check.py:709`, with tests in `tests/test_host_state_check.py`.
3. **H3**, after the owner's C8 install: each H2 agent runs one scripted task on turing against a `util/host_state_probe.bash --json` run within ±10 minutes, plus one negative test; the task prompts go through `prompt-validator`.
4. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5 in the next plan revision. Before numbering it, check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.
5. **Post-merge check (E-LAND-2).** juniper-ml#2320 (the recurrence session) rebuilds `CHANGELOG.md` after #2322, by agreement. After it merges, `python3 -I util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py --mutants 26/26 --check` should print "nothing to do", and `python3 -I util/ad-hoc/2026-10-25_turing_c9_h6_record.py --c9-pr 2322 --c9-sha 3f38956ff87cf1751b3652a3493735ba35900164 --mutants 26/26 --dry-run` should report every edit `present`. `util/ad-hoc/2026-10-21_turing_h5_decision_record.py --dry-run` now reports three edits `MISSING` by design: the Version line, the C9 row, and the rows C0, C2 and H6 (whose anchor needs v1.4.5's H6 row). v1.4.6 replaced the Version line and the C9 and H6 rows. Its other seven edits stay `present`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/claude_agent_guard.py --version                                  # juniper-agent-guard 1.2.0
python3 -I util/claude_agent_guard.py --self-test                                # 50 of 50
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline         # exit 0: option B intact
ls ~/.claude/hooks/juniper_agent_guard.py 2>/dev/null || echo "guard not installed"
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py`, `util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py` (juniper-ml#2322);
  - `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (by the `auditor` agent; the session pinned its guard citations to `899796d2` and #2322), `util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`, `util/ad-hoc/2026-10-25_turing_c9_h6_record.py` and this file (this handoff's PR).
- **Modified in this session:**
  - `util/claude_agent_guard.py`, `util/install_claude_agent_guard.bash`, `tests/test_claude_agent_guard.py`, `.github/workflows/ci.yml`, `docs/REFERENCE.md` and `CHANGELOG.md` (juniper-ml#2322);
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.6;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md` and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md`: pointers to this file (this handoff's PR).
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md` (RR-10, O-5);
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`;
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` (K13);
  - `util/mcp_setup.bash`, `tests/test_mcp_setup.py`, `conf/hosts/turing/mcp.json`;
  - `util/ad-hoc/2026-10-17_turing_c8_guard_mutation_check.py`, `util/ad-hoc/2026-10-20_k12_guard_mutation_check.py` and `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py`, whose anchors all still hold in 1.2.0;
  - `util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, `util/ad-hoc/2026-10-21_turing_h5_decision_record.py`.
- **Worktree:** `.claude/worktrees/breezy-baking-lerdorf`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`, `util/safe_merge.py`).
- **Host changes:** none. The H6 audit and the session read only; scratch files lived in the session's scratchpad.
- **Memory notes:** `turing-host-profile` (C9 landed; H6's state).
