# MCP Server Setup Plan for juniper-ml

**Project**: Juniper/juniper (juniper-ml meta-package)
**Author**: Claude Code (Opus 4.6)
**Date**: 2026-02-23
**Status**: PLAN — Awaiting user approval before execution

---

## Objective

Add MCP server configurations to `Juniper/juniper/` to match the tooling available in sibling projects (JuniperCascor, JuniperCanopy, JuniperData). This includes Serena, HuggingFace, Kaggle, DeepWiki, and other available servers.

---

## Current State

### Existing Configuration

| File | Contents |
|------|----------|
| `.claude/settings.local.json` | Minimal permissions (git add/push/commit, claude mcp, WebSearch, WebFetch for a few domains) |
| `.mcp.json` | Does not exist |
| `.serena/` | Does not exist |

### Reference Configurations (Sibling Projects)

| Project | MCP Servers | Config Location |
|---------|-------------|-----------------|
| `JuniperCascor/juniper_cascor/` | Serena (via `.claude/settings.local.json` permissions) | `.claude/settings.local.json` (126 rules) |
| `JuniperCanopy/juniper_canopy/` | Exa (via `.mcp.json`), Serena + HuggingFace (via permissions) | `.mcp.json` + `.claude/settings.local.json` (116 rules) |
| `JuniperData/juniper_data/` | Serena (via permissions) | `.claude/settings.local.json` (62 rules) |
| `juniper-cascor/` | Serena (via `.serena/project.yml`) | `.serena/project.yml` |

### Globally Available MCP Servers (VS Code)

Already installed but not project-configured:
- **microsoft/markitdown** (stdio, no auth)
- **upstash/context7** (HTTP, optional API key)
- **oraios/serena** (stdio, no auth)
- **huggingface** (HTTP, Bearer token: `<HF_TOKEN>`)

---

## Servers to Add

### Tier 1: Core (must have)

| # | Server | Transport | Auth | Rationale |
|---|--------|-----------|------|-----------|
| 1 | **Serena** | stdio | None | Code intelligence, symbol navigation, refactoring — used across all other Juniper projects |
| 2 | **HuggingFace** | HTTP | HF Bearer token | Model/dataset/paper search — relevant for ML research platform |
| 3 | **DeepWiki** | HTTP | None (public repos) | Repository documentation access — already available in this session |

### Tier 2: Recommended

| # | Server | Transport | Auth | Rationale |
|---|--------|-----------|------|-----------|
| 4 | **Kaggle** | stdio | Kaggle API key (`~/.kaggle/kaggle.json`) | Dataset search/download — relevant for ML research |
| 5 | **Context7** | stdio | None (optional API key) | Up-to-date library documentation — useful for dependency management |

### Tier 3: Optional (user decision needed)

| # | Server | Transport | Auth | Rationale |
|---|--------|-----------|------|-----------|
| 6 | **Exa** | HTTP | API key (already in JuniperCanopy) | Web/paper search — used in JuniperCanopy |
| 7 | **arXiv** | stdio | None | Academic paper search — high value for CasCor research |
| 8 | **W&B (Weights & Biases)** | HTTP | W&B API key | Experiment tracking — useful if W&B is used for training |

---

## Execution Plan

### Phase 1: Create `.mcp.json` for HTTP MCP Servers

**File**: `/home/pcalnon/Development/python/Juniper/juniper/.mcp.json`

This file defines MCP servers that use HTTP transport (remote/hosted). It follows the same pattern used in JuniperCanopy.

```json
{
  "mcpServers": {
    "hf-mcp-server": {
      "type": "http",
      "url": "https://huggingface.co/mcp",
      "headers": {
        "Authorization": "Bearer <HF_TOKEN>"
      }
    },
    "deepwiki": {
      "type": "http",
      "url": "https://mcp.deepwiki.com/mcp"
    }
  }
}
```

**Decision needed**: Should Exa and/or W&B be included here?

### Phase 2: Add stdio MCP Servers via `claude mcp add`

These servers run as local subprocesses and are registered via the CLI:

#### 2a. Serena

```bash
claude mcp add -s project serena -- \
  uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server --context claude-code
```

#### 2b. Context7

```bash
claude mcp add -s project context7 -- npx -y @upstash/context7-mcp
```

#### 2c. Kaggle (requires `kaggle-mcp` installed)

```bash
pip install git+https://github.com/54yyyu/kaggle-mcp.git
claude mcp add -s project kaggle -- kaggle-mcp
```

**Prerequisite**: Kaggle API credentials must exist at `~/.kaggle/kaggle.json`.

#### 2d. arXiv (optional)

```bash
claude mcp add -s project arxiv -- \
  uv tool run arxiv-mcp-server \
  --storage-path /home/pcalnon/.arxiv-mcp-server/papers
```

### Phase 3: Create Serena Project Configuration

**File**: `/home/pcalnon/Development/python/Juniper/juniper/.serena/project.yml`

Based on the template from `juniper-cascor/.serena/project.yml`, adapted for the meta-package:

```yaml
project_name: "juniper_ml"
languages:
- python
- toml
encoding: "utf-8"
ignore_all_files_in_gitignore: true
ignored_paths:
- "dist/"
- "*.egg-info/"
read_only: false
excluded_tools: []
included_optional_tools: []
fixed_tools: []
base_modes:
default_modes:
initial_prompt: ""
symbol_info_budget:
```

Also create `.serena/.gitignore`:
```
memories/
```

### Phase 4: Update `.claude/settings.local.json` Permissions

Update the existing permissions file to:
1. Enable all project MCP servers (`enableAllProjectMcpServers: true`)
2. Whitelist MCP server tools for pre-approval
3. Add the `.mcp.json` servers to `enabledMcpjsonServers`

**File**: `/home/pcalnon/Development/python/Juniper/juniper/.claude/settings.local.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(git add:*)",
      "Bash(git push:*)",
      "Bash(git commit:*)",
      "Bash(git:*)",
      "Bash(claude mcp:*)",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:oraios.github.io)",
      "WebFetch(domain:mcp.deepwiki.com)",
      "WebFetch(domain:dasroot.net)",
      "mcp__serena__check_onboarding_performed",
      "mcp__serena__onboarding",
      "mcp__serena__list_dir",
      "mcp__serena__think_about_collected_information",
      "mcp__serena__write_memory",
      "mcp__serena__list_memories",
      "mcp__serena__read_memory",
      "mcp__serena__get_symbols_overview",
      "mcp__serena__find_symbol",
      "mcp__serena__search_for_pattern",
      "mcp__serena__initial_instructions",
      "mcp__serena__think_about_task_adherence",
      "mcp__serena__think_about_whether_you_are_done",
      "mcp__hf-mcp-server__space_search",
      "mcp__hf-mcp-server__hub_repo_search"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "hf-mcp-server",
    "deepwiki"
  ]
}
```

### Phase 5: Verify Configuration

Run the following to confirm all servers are registered:

```bash
claude mcp list
```

Expected output should show: serena, hf-mcp-server, deepwiki, context7, kaggle (and optionally arxiv).

### Phase 6: Update `.gitignore`

Ensure `.claude/settings.local.json` is not committed (it contains local preferences). Check if it's already in `.gitignore`.

---

## Decision Points for User

Before execution, the following decisions are needed:

1. **Kaggle**: Do you have Kaggle API credentials at `~/.kaggle/kaggle.json`? Should we install `kaggle-mcp`?
2. **Exa**: Should Exa (web search) be added? The API key from JuniperCanopy can be reused.
3. **arXiv**: Should the arXiv paper search server be added?
4. **W&B**: Do you use Weights & Biases? If so, should we add the W&B MCP server?
5. **HuggingFace token**: The global VS Code config uses `<HF_TOKEN>`. Should we reuse this token, or do you prefer OAuth login?
6. **Scope**: Should any servers be added at `--scope user` (global for all projects) instead of `--scope project` (this project only)?

---

## File Summary

| Action | File | Description |
|--------|------|-------------|
| **Create** | `.mcp.json` | HTTP MCP server definitions (HuggingFace, DeepWiki) |
| **Create** | `.serena/project.yml` | Serena project configuration |
| **Create** | `.serena/.gitignore` | Ignore Serena memories from git |
| **Update** | `.claude/settings.local.json` | Permissions + MCP enablement flags |
| **Run** | `claude mcp add` (x3-5) | Register stdio MCP servers (Serena, Context7, Kaggle, optionally arXiv) |
| **Verify** | `claude mcp list` | Confirm all servers registered |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| HuggingFace token in `.mcp.json` committed to git | Ensure `.mcp.json` is in `.gitignore` |
| Kaggle credentials missing | Check for `~/.kaggle/kaggle.json` before adding |
| `kaggle-mcp` package not stable (community project) | Can be removed easily via `claude mcp remove kaggle` |
| Too many MCP servers slow down Claude Code startup | Start with Tier 1+2, add Tier 3 only if needed |
| `.claude/settings.local.json` is local-only, not portable | This is by design — local settings shouldn't be committed |

---

## References

- Serena docs: https://oraios.github.io/serena/02-usage/030_clients.html
- HuggingFace MCP: https://huggingface.co/docs/hub/en/hf-mcp-server
- Kaggle MCP: https://github.com/54yyyu/kaggle-mcp
- DeepWiki MCP: https://mcp.deepwiki.com/
- Context7 MCP: https://github.com/upstash/context7
- JuniperCanopy reference: `/home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy/.mcp.json`
- JuniperCascor reference: `/home/pcalnon/Development/python/Juniper/JuniperCascor/juniper_cascor/.claude/settings.local.json`
- juniper-cascor Serena reference: `/home/pcalnon/Development/python/Juniper/juniper-cascor/.serena/project.yml`
