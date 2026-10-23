# Handoff — turing bring-up: H5's audit landed; the trees were removed, restored and risk-analysed; the owner decides

- **Superseded (2026-10-21, plan v1.4.5).** The owner chose option B: keep both trees, dormant and hardened. B.1 to B.3 are applied. H5's current state, the owner's B.4 and B.5, and the check are in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md`. What follows is this file's state before the decision.

- **From:** the 2026-10-21 session on turing named "mac dev". It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md`, and took H5 under the owner's split (plan erratum E-SPLIT).
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.4.
  - §18.2's H5 row says "the owner's decision is pending", and §18.3 carries erratum E-H5.
  - The removal, the restore and the risk analysis are **not yet in the plan** (analysis O-2). The next turing plan revision folds them in, together with the owner's decision.
- **The arc's main handoff** is the "code signing" session's `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` (juniper-ml#2305), where C9 is next. It names this file as the authority on H5. The earlier `HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md` now points to it.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2300 | `2f831b60` | H5: `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`, with `util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py` |
| juniper-ml#2302 | `cf70e259` | plan v1.4.4, `util/ad-hoc/2026-10-21_turing_h5_record.py`, and the first version of this file |
| the restored-state PR | — | `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`, `util/ad-hoc/2026-10-21_turing_h5_restore_check.py`, `reports/2026-10-21_turing-h5-restore/`, and this update |

## The state of `~/.claude/mcp-servers` (2026-10-21T10:11Z)

- **History.**
  - The trees were removed at the owner's REMOVE choice, after 07:10:57Z. The owner then asked to reconsider.
  - At 08:33Z both were restored with `git clone --revision` at the audited commits.
  - agi-mcp-server's npm install was rebuilt at 09:04Z, offline from npm's cache, with `--before` the March install and `--ignore-scripts`. `fsevents` was then removed for parity.
- **Parity.** Every tracked file matches upstream: 305 of 305, and 33 of 33. A reviewer found both root tree hashes equal to the commits' trees. The lockfile holds the 270 March pairs, and `node_modules` the 174 March pairs, in 175 directories.
- **Deliberate deviations.**
  - agi's `origin` is now `QuixiAI`.
  - Both trees are on a detached HEAD. That is **not** a pull barrier (RR-6).
  - No install-time code ran.
  - There are no `.pyc` files and no `fsevents`.
- **Dormant.** Neither server is configured in any client config checked. Nothing runs from, or holds a file in, either tree, and nothing listens on their ports. No Claude Code session has ever run in either tree.
- **Re-check it any time** with `python3 -I util/ad-hoc/2026-10-21_turing_h5_restore_check.py`; exit 0 means every judged check passes. `--offline` skips the GitHub reads and the tree comparison.

## The risk analysis in brief

- `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md` is **VALIDATED**: three independent reviewers each returned ACCEPT-WITH-CHANGES, and every finding was applied or dispositioned (its §9).
- **The register.** It holds 14 risks: 9 Medium (RR-1, RR-2, RR-3, RR-5, RR-6, RR-10, RR-11, RR-12, RR-13) and 5 Low (RR-4, RR-7, RR-8, RR-9, RR-14). None is High; all are dormant until something triggers them.
- **Standing rules until the owner decides:**
  - Never open Claude Code inside `~/.claude/mcp-servers/adaptive-graph-of-thoughts` (RR-1).
  - Never open either tree in VS Code or Cursor with an agent; VS Code here auto-approves every terminal command (RR-13).
  - Never open the `.dxt` bundles. Claude Desktop is installed, though never launched, and bound to `.dxt` (RR-2). This corrects AGOT-P1.
  - Never `git fetch` or `git pull` in the trees, and never follow their example configs or install steps (RR-6).
  - Never run npm in agi-mcp-server without `--ignore-scripts` (RR-9).
  - A Little Snitch alert for `/usr/local/Cellar/node/25.8.1_1/bin/node` may be pending. Answer it "Deny once" unless the owner decides otherwise (RR-12).
- **Other issues for the owner:**
  - RR-10: no guard covers the MCP-registration paths. A C9-candidate extension of C8 is the owner's decision.
  - O-5: VS Code's four MCP servers were never reviewed.
  - O-8: plan task C0's Time Machine backup would include the trees.

## The owner's decision (open)

- **A. Remove both.** This is the recommendation, and the analysis strengthens it. Run `rm -rf ~/.claude/mcp-servers/adaptive-graph-of-thoughts ~/.claude/mcp-servers/agi-mcp-server`, then `rmdir ~/.claude/mcp-servers`. The trees can be re-created later with the analysis' §3.1.
- **B. Keep, hardened.** Steps B.1 to B.5 are in the analysis' §7, each with its reversal:
  - B.1: rename the allow list in place;
  - B.2: rename the bundles in place;
  - B.3: a tree-local `.npmrc` with `ignore-scripts=true`;
  - B.4: a standing Little Snitch rule for `node`;
  - B.5: remove `origin` from both clones.
- **C. Keep as restored.**

## Next steps

1. **The owner decides A, B or C.** With the owner's go, an agent carries it out: the removal, or B.1 to B.3. B.4 and B.5 are the owner's own steps. Then re-run the check:
   - after A, the inventory script exits 2;
   - after B, the restore check's provenance fails by design.
2. **The next turing plan revision (v1.4.5)** records H5's row with the decision and its date, the removal and restore, and the risk analysis. It also points §18 at the #2305 handoff. Check for an open turing plan PR first.
3. **Candidate follow-ups, each the owner's decision:**
   - a C8/C9 rule set for MCP registration (RR-10);
   - a review of VS Code's four MCP servers (O-5);
   - C2 with "block all incoming connections" (RR-11);
   - excluding the trees from C0's backup if they are kept (O-8).

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/ad-hoc/2026-10-21_turing_h5_restore_check.py --offline   # every judged check passes, unless the owner has acted
python3 -I util/ad-hoc/2026-10-21_turing_h5_record.py --dry-run          # v1.4.4's edits present
ls ~/.claude/mcp-servers 2>/dev/null || echo "removed"
```

## Documents and git state at handoff

- **Created in this session:**
  - by juniper-ml#2300: `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`, written by the `auditor` agent, and `util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`;
  - by juniper-ml#2302: `util/ad-hoc/2026-10-21_turing_h5_record.py`, and this file's first version;
  - by the restored-state PR:
    - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`;
    - `util/ad-hoc/2026-10-21_turing_h5_restore_check.py`;
    - `reports/2026-10-21_turing-h5-restore/`, holding `march-lockfile-packages.txt`, `march-installed-packages.txt`, `restore-check.json` and five npm debug logs under `npm-logs/`.
- **Modified in this session:**
  - by juniper-ml#2302: `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.4;
  - by the restored-state PR: this file.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`, for RR-13's IDE auto-approval and K13;
  - `util/claude_agent_guard.py`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md`.
- **Worktree:** `.claude/worktrees/zippy-drifting-kettle`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`).
- **Host changes this session:**
  - `~/.claude/mcp-servers` was removed at the owner's choice, then restored at the owner's reconsideration, as above. The restore reinstalled agi-mcp-server's npm packages, offline.
  - npm wrote its own debug logs for the restore runs, rotating older ones out (it keeps ten); the five restore logs are preserved in `reports/2026-10-21_turing-h5-restore/npm-logs/`. npm's cache was used offline.
  - Nothing else on the host changed.
- **Memory notes:** `turing-host-profile` (H5, the removal and the restore).
