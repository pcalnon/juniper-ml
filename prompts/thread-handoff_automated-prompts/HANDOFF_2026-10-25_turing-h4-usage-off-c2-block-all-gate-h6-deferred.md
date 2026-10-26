# Handoff — turing bring-up: H4's Serena usage report off; C2's block-all gate landed; H6 deferred; owner steps next

- **From:** the 2026-10-25 session on turing named "macos dev env setup" (9d4723; worktree `.claude/worktrees/cozy-snuggling-fountain`). It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`. That handoff's author, "dev env macos" (014c35), could not be reached (HTTP 409), and no other session was on it.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.7.
  - §18.1 holds the three rulings of 2026-10-25.
  - §18.2 holds the H4, C2 and H6 rows.
  - §18.3 holds errata E-C2-GATE, E-H6-VALUE and E-CUT.
- **This file is the arc's main handoff.** It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`, which now points here. Its owner steps still stand, and C2's now takes the block-all form.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2335 | `1e4db700` | **H4's usage report off** (E-H6, owner ruling). `util/mcp_setup.bash` writes `"env": {"SERENA_USAGE_REPORTING": "false"}`. Serena v1.7.0 skips the report only for that exact string (`src/serena/agent.py:724-737` at `949a27ef`, read through `gh api`). The pin's `verified` record names the check. 38 tests; `util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py` kills 7 of 7 mutants, and H4's original 20 still apply |
| juniper-ml#2338 | `95634772` | **C2's gate, block-all form** (owner ruling). The probe captures `socketfilterfw --getblockall`. G-SEC's firewall condition passes only when the firewall is on and that capture reports block all, and its fix names the missing steps. 59 tests in the two G1 suites; `util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py` kills 11 of 11 mutants, and the G1 check's 57 still apply, C12 included |
| this handoff's PR | — | The record: plan v1.4.7 by `util/ad-hoc/2026-10-25_turing_rulings_1025_record.py`, the previous handoff's pointer, and this file. Also E-CUT: the three turing doc-edits scripts (H4, C2 and C9) now find their CHANGELOG marker anywhere in the file, so the 0.11.2 cut no longer looks like a pending edit, and a re-run no longer adds an entry twice |

## The owner's rulings (2026-10-25, one question)

1. **H4's usage report:** opt out. Done (juniper-ml#2335).
2. **C2's form:** block all incoming connections while nothing inbound is needed. The gate is done (juniper-ml#2338); applying it is the owner's. Revisit when Arc F's VM needs inbound.
3. **H6:** deferred. When it resumes, its changes cover every synced host, and the agent makes them, backing up `mcp.json` and `settings.json` first with the Hugging Face token redacted. SER-P1's order stands: remove VS Code's Serena entry before E-H4-WHEEL's wheel build. Rotating the Hugging Face token (HF-P1) is still advised: it sat in plaintext in `mcp.json` and in Settings Sync.

## State (2026-10-25)

- **The guard on `main` is 1.2.0; turing still runs no guard.** `~/.claude/hooks/` does not exist, so neither C8, K12 nor C9 binds any session yet.
- **Firewall:** off (`State = 0`), block all disabled, stealth off, downloaded signed software auto-allowed. G-SEC therefore still fails. Nothing on turing listens beyond loopback except Dropbox's LAN sync (`*.17500`) and link-local services on the T2 chip's internal interface; there is no sshd and no Screen Sharing.
- **C0:** `tmutil isexcluded ~/.claude/mcp-servers` still reports `[Included]`.
- **H5, option B** is intact. `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline` exited 0 at 22:01:56Z; B.5 is still pending (both `origin`s set).
- **No checkout on turing has an `.mcp.json`**, so no H4 entry needed rewriting. The live check still waits on E-H4-WHEEL.
- **Release 0.11.2.** The recurrence session's 0.11.2 proposal, juniper-ml#2339, moves `[Unreleased]` into `## [0.11.2]`. It held its merge for #2338 by agreement (cross-session message), so the CHANGELOG entries of #2335 and #2338 ride 0.11.2. On the proposal's head, `9a0d8b29`, both sit under `[0.11.2]` / `### Changed`. The three doc-edits scripts' checks, the H4 (`--mutants 7/7`), C2 (`--mutants 11/11`) and C9 (`--mutants 26/26`) ones, print "nothing to do" both before and after the cut, measured on that head's CHANGELOG (E-CUT). Before this session's record PR, they reported the cut as a pending edit.
- **E-LAND-2 is closed.** After #2320 merged, the C9 doc-edits check printed "nothing to do", and the C9/H6 record's dry run reported all 7 edits `present`.

## Owner steps

1. **C8 install, including K12 and C9** (unchanged). From a real terminal, in the primary checkout:

   ```bash
   git pull --ff-only origin main
   bash util/install_claude_agent_guard.bash --apply   # copies 1.2.0, self-tests it, merges the hook entry
   bash util/install_agents.bash                        # 9 agent links: H2's acceptance
   ```

2. **C2, block-all form** (new commands). In a terminal:

   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
   python3 util/host_state_check.py --section G-SEC     # the firewall condition should pass
   ```

   Then paste the output of `/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate` and `--getblockall` into the next session. E-C2-GATE's on-state sentences have not been observed yet.
3. **Unchanged from the option-B handoff:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers` before the first backup.
4. **E-H4-WHEEL** (Serena on turing) waits on H6's Serena removal, which is now deferred. Also unchanged: A1, `~/.condarc` `ssl_verify: true`, the JuniperPython `PYTHONPATH` unset, F2/A6, F3 node mode, and the signing order (no YubiKey into turing until C8 is installed with K12, and K13 is done).

## Agent next

1. **After the owner's C2 commands:** record the on-state sentences in the plan, and narrow E-C2-GATE's accepted sentences if one never appears. Re-run `python3 util/host_state_check.py --section G-SEC`.
2. **H3**, after the owner's C8 install: each H2 agent runs one scripted task on turing against a `util/host_state_probe.bash --json` run within ±10 minutes, plus one negative test. The task prompts go through `prompt-validator`.
3. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5 in the next plan revision.
4. **H6, when the owner resumes it:** apply §8 of `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (the H6 audit) to every synced host through a script that never prints a value. Back up both files first, with the token redacted, to `~/.local/state/juniper/quarantine/<date>-vscode-mcp/`, and verify with `python3 -I util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`.
5. **Before numbering the next plan revision**, check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/claude_agent_guard.py --version                                  # juniper-agent-guard 1.2.0
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline         # exit 0: option B intact
ls ~/.claude/hooks/juniper_agent_guard.py 2>/dev/null || echo "guard not installed"
python3 util/host_state_check.py --section G-SEC                                 # firewall: fail until the owner's C2 commands
python3 -I util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py --mutants 7/7 --check   # nothing to do
python3 -I util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py --mutants 11/11 --check         # nothing to do
python3 -I util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py --mutants 26/26 --check        # nothing to do
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py`, `util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py` (juniper-ml#2335);
  - `util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py`, `util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py` (juniper-ml#2338);
  - `util/ad-hoc/2026-10-25_turing_rulings_1025_record.py` and this file (this handoff's PR).
- **Modified in this session:**
  - `util/mcp_setup.bash`, `tests/test_mcp_setup.py`, `conf/hosts/turing/mcp.json` (juniper-ml#2335);
  - `util/host_state_check.py`, `util/host_state_probe.bash`, `conf/hosts/turing/expected.yaml`, `tests/test_host_state_check.py`, `tests/test_host_state_probe.py` (juniper-ml#2338);
  - `docs/REFERENCE.md` and `CHANGELOG.md` (both PRs);
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.7, and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`, a pointer to this file (this handoff's PR);
  - `util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py`, `util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py` and `util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py`: the CHANGELOG marker counts anywhere in the file (E-CUT; this handoff's PR).
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (SER-E1, SER-P1, HF-P1, H6-X3, §8);
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md` (RR-11);
  - `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py` (20 of 20) and `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` (57 of 57), whose anchors still hold;
  - `util/ad-hoc/2026-10-25_turing_c9_h6_record.py` (E-LAND-2's check), `util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`.
- **Worktree:** `.claude/worktrees/cozy-snuggling-fountain`. Nothing was committed locally; everything landed through the API (`util/push_signed_commit.py`, `util/ad-hoc/2026-10-17_push_signed_with_retry.py`, `gh pr create`, `util/safe_merge.py`).
- **Host changes:** none. The session read the host only: `socketfilterfw --get*`, `tmutil isexcluded`, `netstat`, and the hardening check.
- **Memory notes:** `turing-host-profile` (this session's landings and rulings).
