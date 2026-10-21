# Handoff — turing bring-up: H5's audit landed; the owner decides on removal

- **From:** the 2026-10-21 session on turing named "mac dev". It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md` and took H5 under the owner's split (plan erratum E-SPLIT).
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.4. This session's record is §18.2's H5 row and §18.3's erratum E-H5.
- **The arc's main handoff is the "code signing" session's**, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md`: C9 is next there. Its step to fold H5 into the next revision is **done** by v1.4.4. Use this file only for H5's state.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2300 | `2f831b60` | H5: `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`, with the evidence script `util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py` |
| the record PR | — | plan v1.4.4, `util/ad-hoc/2026-10-21_turing_h5_record.py` and this file |

## H5 in brief

- The `auditor` agent's static audit of `~/.claude/mcp-servers/adaptive-graph-of-thoughts` and `~/.claude/mcp-servers/agi-mcp-server` found 25 findings: 3 blocker, 9 major and 13 minor. **It recommends REMOVE for both.**
- **adaptive-graph-of-thoughts**
  - The only standard-MCP entry point fabricates results from `Math.random()` (AGOT-A1).
  - The HTTP default binds `0.0.0.0:8000`, with fail-open Basic auth (AGOT-A3).
  - A tracked `.claude/settings.local.json` pre-approves interpreters for any session opened in the tree (AGOT-A2). **Never open Claude Code inside that tree.**
- **agi-mcp-server**
  - Its `origin` and its documented `npx -y github:` launch point into the squatted `cognitivecomputations` namespace (AGI-P1). **Never `git pull` it, and never use its `npx` config.**
  - Its tools are a cross-session memory store (AGI-A1).
- **On the host:** neither server is configured in any client config checked, and neither is running. What ran on 2026-03-01 is dated in the audit (AGI-H1, AGOT-H1).
- **C9 does not attach:** neither server exposes a file-writing or command-running tool. Their database and network tools would need `permissions.deny` rules instead (H5-X1).

## The owner's decision (pending at handoff unless recorded below)

The audit's §8 gives the commands for each choice. For removal, the owner runs:

```bash
python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py --offline   # confirm: neither configured
rm -rf ~/.claude/mcp-servers/adaptive-graph-of-thoughts
rm -rf ~/.claude/mcp-servers/agi-mcp-server
rmdir ~/.claude/mcp-servers
python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py --offline   # exit 2: no server directories left
```

Once the owner decides, the next turing plan revision replaces the H5 row's "the owner's decision is pending" with the decision and its date. Before numbering that revision, check for an open turing plan PR (`gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`).

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --json number,title
python3 -I util/ad-hoc/2026-10-21_turing_h5_record.py --dry-run           # every edit present
python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py --offline
ls ~/.claude/mcp-servers 2>/dev/null || echo "removed"
```

## Documents and git state at handoff

- **Created in this session:**
  - by H5 (#2300): `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md` (the audit, by the `auditor` agent) and `util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py` (its evidence script);
  - by the record PR: `util/ad-hoc/2026-10-21_turing_h5_record.py` and this file.
- **Modified in this session:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (v1.4.4: the Version line, §18's opening paragraph, §18.2's H5 row and §18.3's erratum E-H5), by the record PR.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`;
  - `notes/JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`;
  - `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`;
  - `util/claude_agent_guard.py`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md`.
- **Worktree:** `.claude/worktrees/zippy-drifting-kettle`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`).
- **Host changes:** none. The audit changed neither tree and no configuration.
