# Handoff — turing bring-up: H6 applied (VS Code's Serena and markitdown removed, Hugging Face token-less, autostart and the gallery off); the token's rotation and the first sync are the owner's

- **From:** the 2026-10-26 session on turing named "c9-landed-h6-audited-owner-decides" (bd4cfc; worktree `.claude/worktrees/clever-finding-lemon`).
  - The owner pointed it at `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md` and resumed H6.
  - That file had been superseded twice, so the session continued from the arc's main handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`.
  - "cached-enchanting-cosmos-84" (760fde) continued from it too, and took H3 by cross-session agreement.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.9.
  - §18.1 holds H6's resumption.
  - §18.2 holds the H6 row, now applied.
  - §18.3 holds erratum E-H6-APPLY.
- **This file is the arc's main handoff.** It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`, which now points here. H3's session agreed to take v1.4.10 for its record and re-anchor on v1.4.9.
- **Standing approval:** the owner granted merge approval for the work arc on 2026-10-26, merging only after green. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2368 | `fb5598b2` | **H6, applied on turing** by `util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py`, at 2026-10-27T00:32:24Z (19:32 local, 2026-10-26). Also the record: plan v1.4.9 by `util/ad-hoc/2026-10-26_turing_h6_applied_record.py`, the previous handoff's pointer, and this file |
| the follow-up PR | — | `util/ad-hoc/2026-10-26_turing_h6_apply_evidence.py`: the read-only evidence behind E-H6-APPLY. It replaces three probes the session first wrote to its scratchpad, against the script-placement rule. Also E-H6-APPLY's pointer to it (the record script's edit 7) |

## The owner's tasks, item by item

1. **The scope first.** It stood as ruled on 2026-10-25: every synced host. The change reaches them through Settings Sync once VS Code runs on turing (owner step 2).
2. **VS Code's unpinned Serena entry: removed** before E-H4-WHEEL's wheel build. uv's cache holds only the cryptography 50.0.0 sdist directory, no wheel, and Rust is still 1.71.
3. **The Hugging Face token: out of `mcp.json`.** The entry runs token-less, the H6 audit's recommended form (§8.4); the owner named none. **Rotating it is the owner's** (owner step 1).
4. **markitdown removed; Context7 kept, unchanged;** `"chat.mcp.autostart": "never"`; `"chat.mcp.gallery.enabled": false`; **the 20 unreferenced inputs deleted.** Only `context7_api_key` remains.
5. **H4's usage report** was already off on `main`: juniper-ml#2335 (`1e4db700`). `util/mcp_setup.bash:206` writes `"env": {"SERENA_USAGE_REPORTING": "false"}`, the exact string Serena compares against (E-H6-VALUE).

## What changed on turing (outside git)

- **`~/Library/Application Support/Code/User/mcp.json`**:
  - `oraios/serena` and `microsoft/markitdown` removed;
  - `huggingface`'s literal `Authorization` header removed;
  - the 20 inputs no server references deleted.
  - `upstash/context7` and `context7_api_key` are untouched.
- **`settings.json`**, same directory: `chat.mcp.autostart` added as `"never"`; `chat.mcp.gallery.enabled` changed from `true` to `false`.
- **Nothing else changed.** A structural diff against the backup:
  - `mcp.json` lost 97 leaf paths and gained or changed none;
  - `settings.json` gained one leaf and changed one of its 901;
  - both files kept their layout and mode 0644.
- **The backup** is `~/.local/state/juniper/quarantine/2026-10-26-vscode-mcp/`, mode 0700. It holds `mcp.json`, `settings.json` and `MANIFEST.json`, each 0600. The manifest records one redaction in `mcp.json` and none in `settings.json`. The script re-read both copies and found no `hf_`-shaped string before it edited anything.
- **Verification:**
  - the script's `--check`: 8 of 8 hold;
  - its `--self-test`: 15 of 15 pass;
  - `python3 -I util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py` lists `upstash/context7` and a token-less `huggingface`, one input, and both settings;
  - a re-run reports "nothing to do".

## State (2026-10-26)

- **Settings Sync has uploaded nothing yet.** VS Code's newest session on turing is still 2026-03-26.
- **The token still sits in** the sync service, and in VS Code's sync state, on turing (`User/sync/mcp/lastSyncmcp.json`, rewritten at the next sync) and on every other synced host. VS Code's local history on turing keeps no copy of `mcp.json`. Rotation makes every copy inert.
- **No other unpinned Serena would start** once the wheel exists:
  - `~/.claude.json` registers no MCP server;
  - `amp.mcpServers` is empty;
  - `~/.claude/settings.json`'s 23-server `mcpServers` block holds an unpinned Serena, but Claude Code does not read MCP servers from `settings.json`.

  So **E-H4-WHEEL no longer waits on H6**, provided the first sync keeps turing's version.
- **K13 is still open.** `chat.tools.terminal.autoApprove` still holds `"/.*/"`, `"xargs"` and the fragment keys. Context7 and Hugging Face are kept, and the H6 audit says to use them only after K13 (H6-X2). With autostart at `never`, neither starts unless asked.
- **The guard.** C8 is installed: per "cached-enchanting-cosmos-84", the owner ran it on 2026-10-26 at about 22:30Z, and that session records it. It denies `gh pr create` and `gh api -X`, so land through `util/open_signed_pr.py`. The repo's guard is 1.2.0.
- **H5, option B** is intact: `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline` exited 0.

## Owner steps

1. **Rotate the Hugging Face token** at <https://huggingface.co/settings/tokens>. The VS Code entry no longer uses it, so delete it. If something else uses it, choose "Invalidate and refresh" instead, and update that place.
2. **Let Settings Sync upload the change.** Open VS Code on turing once, signed in to Settings Sync with "MCP Servers" and "Settings" ticked.
   - If VS Code reports a conflict, keep the local version: it is turing's.
   - Each other synced host takes the change at its next sync. On a Linux host, `python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check` reads `~/.config/Code/User` by default.
   - Little Snitch may ask about VS Code's connections on that first run.
3. **K13 before Context7 or Hugging Face is used** (H6-X2). Delete `"/.*/"`, `"xargs"` and the fragment keys from `chat.tools.terminal.autoApprove`. The plan is `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`, task K13.
4. **Optional, in VS Code** (the H6 audit's §8.5):
   - "Chat: Reset Tool Confirmations";
   - `workbench.mcp.resetTrust`;
   - `workbench.mcp.removeStoredInput` for any value stored under a deleted input (`token`, `voyageApiKey` and the rest).
5. **Unchanged:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers`;
   - E-H4-WHEEL, whose route is the owner's choice; it is now free of H6;
   - A1; `~/.condarc` `ssl_verify: true`; the JuniperPython `PYTHONPATH` unset; F2/A6; F3 node mode; C1 and C3;
   - the signing order: no YubiKey into turing until C8 is installed with K12, and K13 is done.

## Agent next

1. **After the owner's first sync:** re-run `--check` on turing; it should still hold 8 of 8. Run it on another synced host if a session runs there.
2. **H3** belongs to "cached-enchanting-cosmos-84". Its record takes plan v1.4.10.
3. **After E-H4-WHEEL:** H4's live check, `timeout 30 claude mcp list`.
4. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5 in the next plan revision.
5. **F7** (AGENT, P2), if the owner wants it before F4. Its design notes are in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`.
6. **Before numbering the next plan revision,** check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check       # 8 of 8 hold
python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --self-test   # 15 of 15 passed
python3 -I util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py                     # context7 + token-less huggingface; 1 input
python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_evidence.py                           # both settings sync; diff 97/0/0 and 0/1/1; no 50 wheel
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline                # exit 0: option B intact
python3 -I util/claude_agent_guard.py --version                                         # juniper-agent-guard 1.2.0
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py`;
  - `util/ad-hoc/2026-10-26_turing_h6_applied_record.py`;
  - `util/ad-hoc/2026-10-26_turing_h6_apply_evidence.py`, the read-only evidence behind E-H6-APPLY (the follow-up PR to this handoff's);
  - this file.
- **Modified in this session:**
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.9;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`: a pointer to this file.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md` (§8, §8.4, §8.5; SER-P1, MKD-T1, HF-P1, HF-T1, H6-X2 to H6-X5);
  - `util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`;
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` (K13);
  - `util/mcp_setup.bash` (H4's opt-out);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md`.
- **Worktree:** `.claude/worktrees/clever-finding-lemon`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`).
- **Host changes:** the two VS Code files and the quarantine directory above, nothing else.
- **Memory notes:** `turing-host-profile` (H6 applied).
