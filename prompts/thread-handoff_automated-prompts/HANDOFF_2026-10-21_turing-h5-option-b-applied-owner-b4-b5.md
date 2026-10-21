# Handoff — turing bring-up: H5 decided (option B: the trees kept, dormant and hardened); B.4 and B.5 are the owner's; four follow-ups adopted

- **From:** the 2026-10-21 session on turing now named "mac dev" (165a0b; worktree `.claude/worktrees/unified-jumping-marble`). It started as "unified-jumping-marble-dc" and took the name after the first "mac dev" (37a935) exited. It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md`. "mac dev" (37a935), which wrote that file, stood down by cross-session message: it had no question open with the owner and no v1.4.5 draft.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.5.
  - §18.1 holds the owner's ruling on H5's trees.
  - §18.2 holds the H5, C9, C0, C2 and H6 rows.
  - §18.3 holds errata E-H5-RESTORE and E-H5-B.
- **The arc's main handoff** stays the "code signing" session's `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` (juniper-ml#2305), where C9 is next. It now points here for H5, and its C9 item carries RR-10's widening.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.

## The owner's decisions (2026-10-21)

1. **H5: option B** of `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md` §7: keep both trees, dormant and hardened. The analysis recommended A (remove), and B if kept.
2. **All four of the analysis' follow-ups become tasks:**
   - RR-10 widens C9: MCP registration denies;
   - RR-11 rewords C2: block all incoming connections;
   - O-8 adds a Time Machine exclusion to C0;
   - O-5 becomes the new task H6: review VS Code's four MCP servers.

## Done this session

| Step | What |
|---|---|
| evidence before | `reports/2026-10-21_turing-h5-hardening/restore-check-before.json` (20:53:08Z): the restore check, online, passes: 305 of 305 and 33 of 33 files identical to upstream |
| B.1 | adaptive-graph-of-thoughts' `.claude/settings.local.json` renamed to `settings.local.json.h5-disabled` (20:53Z) |
| B.2 | its three `.dxt` bundles and the `.zip` renamed with the same suffix. No other `.dxt` or `.mcpb` exists in either tree, `node_modules` included |
| B.3 | `agi-mcp-server/.npmrc` holds exactly `ignore-scripts=true` (20:54Z) |
| renames | sha256 identical before and after. The git blob ids equal upstream's at the audited commit, read through `gh api` |
| the check | `util/ad-hoc/2026-10-21_turing_h5_hardening_check.py` (new): exit 0 at 21:00:51Z. Eight scenarios on copy-on-write clones gave the expected verdicts: the unchanged clone, each step reverted, a modified bundle, a squatted origin, a stray file, a second remote, and both origins removed (B.5 simulated) |
| evidence after | `hardening-check.json` passes; `restore-check-after.json` fails by design, on provenance only, with exactly B's deviations |
| the record | plan v1.4.5 and the two handoff pointers, by `util/ad-hoc/2026-10-21_turing_h5_decision_record.py` |

## State (2026-10-21T21:01Z)

- **The trees.** Both are present at the audited commits on detached HEADs, with B.1 to B.3 applied. `origin` is still set in both, so B.5 is pending; agi's `origin` is `QuixiAI`.
- **Dormant.** Neither server is named in any client config checked, no process names either tree, and none holds a file under them. These are the restore check's own judged checks, reused unchanged.
- **Advisories.** 92 active for the installed npm set (3 critical, 29 high, 55 medium, 5 low), against the analysis' 89 at 10:11Z. They are reported, not judged.
- **Re-check it any time** with `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`; exit 0 means option B is intact and the rest of the restored state holds. `--offline` skips the GitHub reads and the tree comparison. The restore check now exits 1 by design.

## Owner steps

1. **B.4 (RR-12).** In Little Snitch, add a standing rule for `/usr/local/Cellar/node/25.8.1_1/bin/node`:
   - deny `github.com` and `codeload.github.com`;
   - allow `registry.npmjs.org` only if npm is needed.

   Answer any pending alert for that binary with "Deny once". A blanket deny breaks pre-commit's node hook environments, and a rule on the Cellar path lapses at the next `brew upgrade node`.
2. **B.5 (RR-6).** In a separate terminal, not through `!` in an agent session, whose worktree guard refuses git outside its worktree:

   ```bash
   git -C ~/.claude/mcp-servers/adaptive-graph-of-thoughts remote remove origin
   git -C ~/.claude/mcp-servers/agi-mcp-server remote remove origin
   python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py   # b5-origin: done for both, exit 0
   ```

   Reverse with `git -C <tree> remote add origin <URL>`; the URLs are in the analysis' §3.1.
3. **C0 (O-8)**, before the first Time Machine backup: `tmutil addexclusion ~/.claude/mcp-servers`, then `tmutil isexcluded ~/.claude/mcp-servers` should report `[Excluded]`.
4. **C2 (RR-11)**, with Owner block 1: firewall on, stealth on, and `socketfilterfw --setblockall on`. Or, if something inbound is needed, per-app inbound denies for `com.docker.backend`, `node` and the env Pythons.

## Standing rules (unchanged by B)

- Never open Claude Code inside either tree. B.1 closes the allow list for default, accept-edits and auto sessions, but a bypass-permissions session stays exposed to the tree's content (RR-1).
- Never open either tree in VS Code or Cursor with an agent (RR-13).
- Never open the `.h5-disabled` bundles, and rename them back only as B.2's deliberate reversal (RR-2).
- Never `git fetch` or `git pull` in the trees, and never follow their example configs or install steps (RR-6).
- The `.npmrc` covers install scripts for npm run inside agi-mcp-server. An `npm test` or `npm run` there still runs that named script (RR-7).

## Agent next

1. **C9, widened.** See the arc's main handoff and the plan's §18.2 C9 row. RR-10 adds denies for the `mcp add*` subcommands whatever the command word, for writes to `~/.claude.json` and any `.mcp.json` (H4's `util/mcp_setup.bash` must keep working), and for settings writes that set `enabledMcpjsonServers` or `enableAllProjectMcpServers`.
2. **H6** (P2, AGENT): an `auditor` audit of VS Code's four MCP servers (`huggingface`, `upstash/context7`, `microsoft/markitdown`, `oraios/serena`), with a keep, pin or remove recommendation per server. Secrets stay unread: no env, header or URL-query value. The plan's §18.2 H6 row has the scope.
3. **C2's gate follow-up**, once the owner chooses C2's form: G-SEC's firewall condition still passes at `State = 1`, and its hint at `util/host_state_check.py:709` still quotes the old wording. Update both, with tests in `tests/test_host_state_check.py`. The test at `:428` pins only the hint's prefix.
4. **After B.5:** re-run the hardening check, and record B.4 and B.5 in the next turing plan revision. Before numbering it, check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.
5. **Post-merge check (E-LAND-2).** After any later merge that touches the plan or these handoffs, re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_decision_record.py --dry-run`; every edit should read `present`. `util/ad-hoc/2026-10-21_turing_h5_record.py --dry-run` now reports its Version-line and H5-row edits `MISSING`, because v1.4.5 replaced both. Its other two edits stay `present`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline   # exit 0: option B intact
python3 -I util/ad-hoc/2026-10-21_turing_h5_decision_record.py --dry-run     # v1.4.5's edits present
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`;
  - `util/ad-hoc/2026-10-21_turing_h5_decision_record.py`;
  - `reports/2026-10-21_turing-h5-hardening/`, holding `restore-check-before.json`, `hardening-check.json` and `restore-check-after.json`;
  - this file.
- **Modified in this session:**
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.5;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md`: a pointer to this file;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md`: the H5 pointer and C9's widening.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md` (§3.1, §5, §6, §7);
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`;
  - `util/ad-hoc/2026-10-21_turing_h5_restore_check.py` and `util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`, whose functions the hardening check reuses;
  - `util/claude_agent_guard.py` (`:188`, `:1615`), `util/host_state_check.py` (`:709`), `tests/test_host_state_check.py` (`:428`) and `.gitignore` (`:166-167`, `:170`);
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`, for K13.
- **Worktree:** `.claude/worktrees/unified-jumping-marble`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`).
- **Host changes this session:**
  - B.1 to B.3 in `~/.claude/mcp-servers`, as above;
  - copy-on-write clones of the trees, made in this session's scratchpad for the check's scenarios, deleted afterwards.

  Nothing else on the host changed.
- **Memory notes:** `turing-host-profile` (H5's decision and option B's state).
