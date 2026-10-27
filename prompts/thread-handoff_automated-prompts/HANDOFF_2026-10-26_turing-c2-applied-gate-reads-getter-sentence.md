# Handoff — turing bring-up: the owner applied C2; G-SEC's firewall condition reads the sentence turing printed; owner steps next

- **Continued (2026-10-26, plan v1.4.9).** Two sessions took this handoff. "cached-enchanting-cosmos-84" (760fde) took H3. "c9-landed-h6-audited-owner-decides" (bd4cfc) applied H6 on turing once the owner resumed it, and its handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md`, is now the arc's main handoff. The other owner steps below still stand; H6's item under Agent next is done.

- **From:** the 2026-10-26 session on turing named "modular-meandering-crayon-bf" (f5e44f; worktree `.claude/worktrees/modular-meandering-crayon`). It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md`. That handoff's author, "macos dev env setup" (9d4723), was idle, and no other session was on it.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.8.
  - §18.2 holds the C2 row, now applied.
  - §18.3 holds erratum E-C2-GATE, now with the observed on-state sentences.
- **This file is the arc's main handoff.** It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md`, which now points here. That file's owner steps still stand, except C2's, which is done.
- **Standing approval:** the owner granted merge approval for the work arc again on 2026-10-26, merging only after green. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2346 | `89f5af48` | **G-SEC's firewall condition reads the block-all sentence turing printed** (E-C2-GATE). Once the owner applied C2, `socketfilterfw --getblockall` printed "Firewall is blocking all non-essential incoming connections." It never printed "Firewall is set to block all non-essential incoming connections", which juniper-ml#2338 had taken for the getter's sentence. The binary's strings place that sentence beside "Block all DISABLED!", the shape of `--setblockall`'s confirmations. `util/host_state_check.py` now accepts only the getter's sentence, and a capture holding the setter's cannot be judged. `tests/test_host_state_check.py` pins turing's on-state captures (61 tests across the two G1 suites). `util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py` redefines B7 (the setter's sentence accepted), adds B12 (#2338's premise) and kills 12 of 12; `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` still kills 57 of 57, C12 included |
| this handoff's PR | — | The record: plan v1.4.8 by `util/ad-hoc/2026-10-26_turing_c2_applied_record.py`, the previous handoff's pointer, and this file |

## What the owner did (2026-10-26)

- **C2, applied** between 08:44Z and 08:47Z: the firewall on, blocking all incoming connections, with stealth mode. On macOS 15.7.1:
  - `--getglobalstate`: "Firewall is blocking all non-essential incoming connections. (State = 2)";
  - `--getblockall`: "Firewall is blocking all non-essential incoming connections.";
  - `--getstealthmode`: "Firewall stealth mode is on";
  - `--getallowsigned`: built-in and downloaded signed software both still ENABLED. Under block all only essential services take incoming connections, so this matters again only if block all is turned off for Arc F's VM.
- **The owner's G-SEC run** at 08:47:40Z came from the primary checkout. Its `util/host_state_check.py` predates juniper-ml#2338, so it judged the global state alone. C8's step 1 below brings the block-all gate there.

## State (2026-10-26)

- **G-SEC:** the firewall condition passes; the gate still fails on `sip` (C1) and `key-exports` (C3), both the owner's.
- **Readiness:** 0 of 7 gates pass. G-ALIAS fails on A1; G-SIGN on the I-SIGN record (K10, K11); G-SEC on C1 and C3; G-TOOLS on D4's kubectl, which E-D6 says needs re-planning; G-ENV on E4; G-NET on F2 and A6; G-MEM on node mode (F3) and a running Docker Desktop.
- **The guard on `main` is 1.2.0; turing still runs no guard.** `~/.claude/hooks/` does not exist.
- **The primary checkout is behind `main`.** Its `util/host_state_check.py` and `util/host_state_probe.bash` lack juniper-ml#2338.
- **C0:** `tmutil isexcluded ~/.claude/mcp-servers` still reports `[Included]`.
- **H5, option B** is intact. `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline` exited 0 at 08:44:34Z; B.5 is still pending (both `origin`s set).

## Owner steps

1. **C8 install, including K12 and C9** (unchanged). From a real terminal, in the primary checkout:

   ```bash
   git pull --ff-only origin main
   bash util/install_claude_agent_guard.bash --apply   # copies 1.2.0, self-tests it, merges the hook entry
   bash util/install_agents.bash                        # 9 agent links: H2's acceptance
   ```

2. **Unchanged from the option-B handoff:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers` before the first backup.
3. **E-H4-WHEEL** (Serena on turing) waits on H6's Serena removal, which is deferred. Also unchanged: A1, `~/.condarc` `ssl_verify: true`, the JuniperPython `PYTHONPATH` unset, F2/A6, F3 node mode, C1 and C3, and the signing order (no YubiKey into turing until C8 is installed with K12, and K13 is done).
4. **Optional:** if the terminal still shows it, paste what `sudo socketfilterfw --setblockall on` printed. "Firewall is set to block all non-essential incoming connections" would confirm E-C2-GATE's attribution of that sentence to the setter.

## Agent next

1. **H3**, after the owner's C8 install: each H2 agent runs one scripted task on turing against a `util/host_state_probe.bash --json` run within ±10 minutes, plus one negative test. The task prompts go through `prompt-validator`.
2. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5 in the next plan revision.
3. **If the owner pastes `--setblockall on`'s output:** record it in E-C2-GATE, which confirms or corrects the setter attribution.
4. **H6, when the owner resumes it:** apply §8 of `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` to every synced host, backing up both files first with the token redacted (unchanged).
5. **F7 (AGENT, P2), if the owner wants it before F4.** It is the one AGENT task in §6 whose dependency has landed (F5a, juniper-ml#2237) with no artifact yet. A4 and B9 landed in juniper-ml#2228, though no status row records them. Installing the plist into `/Library/LaunchDaemons` needs sudo, so the install is the owner's. Points to settle when it is built (unverified design notes, not decisions):
   - `AbandonProcessGroup` true, or launchd may kill the VM's processes when `util/macvm_ctl.bash start` exits; `RunAtLoad` true, with no `KeepAlive`;
   - run a root-owned copy of `util/macvm_ctl.bash`, not the checkout's, so that a branch switch or an agent edit cannot change what runs at boot;
   - "installed disabled" means the plist is present, `launchctl disable system/local.juniper-macvm` is set, and the job is not bootstrapped. `launchctl print system/local.juniper-macvm` then likely reports no such service, so the acceptance may need `launchctl print-disabled system` instead (an erratum candidate).
6. **Before numbering the next plan revision**, check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/claude_agent_guard.py --version                                  # juniper-agent-guard 1.2.0
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline         # exit 0: option B intact
ls ~/.claude/hooks/juniper_agent_guard.py 2>/dev/null || echo "guard not installed"
python3 util/host_state_check.py --section G-SEC                                 # firewall PASS; sip and key-exports fail
python3 -I util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py --mutants 12/12 --check     # nothing to do
python3 -I util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py --mutants 11/11 --check         # nothing to do
python3 -I util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py --mutants 7/7 --check   # nothing to do
python3 -I util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py --mutants 26/26 --check        # nothing to do
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py` (juniper-ml#2346);
  - `util/ad-hoc/2026-10-26_turing_c2_applied_record.py` and this file (this handoff's PR).
- **Modified in this session:**
  - `util/host_state_check.py`, `tests/test_host_state_check.py`, `util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py`, `docs/REFERENCE.md` and `CHANGELOG.md` (juniper-ml#2346);
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.8, and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md`, a pointer to this file (this handoff's PR).
- **Referenced, not changed:**
  - `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` (57 of 57), `util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py`, `util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py` and `util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py`, whose checks still print "nothing to do";
  - `util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, `util/ad-hoc/2026-10-18_turing_link_gate.py` (5 GHz ch 149, SNR 24 dB, 0% loss, the 1.33 MB upload in 0.65 s), `util/macvm_ctl.bash` (F7's notes);
  - `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (§8).
- **Worktree:** `.claude/worktrees/modular-meandering-crayon`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`, `util/safe_merge.py`).
- **Host changes:** none by the agent. It only read the host: `socketfilterfw --get*`, the strings of the `socketfilterfw` binary, `tmutil isexcluded`, the probe, the hardening check, and the link gate, which uploads random bytes to Cloudflare's speed test.
- **Landing detours for juniper-ml#2346:**
  - **Sequence Safety** failed its first head (`5f330b8e`): renaming `FirewallTest.test_block_all_passes_in_either_sentence_and_either_state` is a LOST method. Commit `d6f88127` carries `Allow-Symbol-Loss` trailers for it and for `const:_BLOCKALL_ON_RE`, a WARN-only finding. The screen, run locally through `juniper_ci_tools.cli_symbol_loss_check` with CI's scopes, then reported `fail=0`.
  - **CHANGELOG.** juniper-ml#2333 merged first (`da5e8de3`) with a `### Fixed` at the top of `[Unreleased]`. #2346 then read CONFLICTING on CHANGELOG.md only; `git merge-tree` showed REFERENCE.md merging cleanly. So `d6f88127` also set CHANGELOG.md back to its base copy.
  - **The 0.11.3 cut.** "draft PRs" (75eba4, Linux host) cut juniper-ml 0.11.3 right after "recurrence equities 0" (4156c8) landed juniper-ml#2345. #2346 took option (b): it re-homed its entry under the new empty `[Unreleased]` after the cut, by update-branch and `util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py` on the new main. Re-cutting before a proposal merges and merging after it would have filed the entry under the release with no conflict.
- **Memory notes:** `turing-host-profile` (C2 applied, the gate narrowed).
