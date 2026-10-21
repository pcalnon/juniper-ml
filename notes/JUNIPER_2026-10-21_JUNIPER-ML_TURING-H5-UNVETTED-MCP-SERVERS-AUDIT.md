# Turing H5: audit of the two unvetted MCP servers

- **Project**: Juniper ML Research Platform, juniper-ml, turing host bring-up. The audited trees sit outside every repository, in `~/.claude/mcp-servers/`.
- **Author**: Paul Calnon (audit via the Claude Code `auditor` agent on turing)
- **Date**: 2026-10-21
- **Version**: 1.0.0
- **Status**: FINAL. The decision to enable, keep disabled or remove each server is the owner's (§8). The audit changed nothing: not the server trees, not any configuration.
- **Scope**: `~/.claude/mcp-servers/adaptive-graph-of-thoughts` and `~/.claude/mcp-servers/agi-mcp-server`, by static analysis only. Lenses: provenance, permissions, egress, plus host exposure.
- **Plan task**: H5 of [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md), §6 Arc H :480 (acceptance: "audit note in `notes/`; enable or remove").
  - The plan is cited as v1.4.3 (main, juniper-ml#2297). Its lines 1-923 are identical to the v1.4.2 copy in this worktree, apart from the Version line. Lines in §18 are v1.4.3's.
- **Evidence script**: [`util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`](../util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py), run as `python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py` from the worktree root at 2026-10-21T05:17:52Z.
  - It is read-only. It reads `.git` as plain files, makes `gh api` GETs only, and reports client configs by key name and boolean.
- **Host**: turing, macOS 15.7.1, Intel i7-8850H, 16 GiB.

---

## 1. Summary

- **Recommendation for both servers: REMOVE.** The decision is the owner's (§8).
- **Findings: 25.** 3 blocker, 9 major, 13 minor (§7.1). Every finding carries a `file:line`, a command and its output, or a fetched URL.
- **adaptive-graph-of-thoughts (AGoT)**
  - The DXT Node server is the only AGoT entry point a standard MCP client can use, and it fabricates its results. Every tool builds its "evidence" from `Math.random()` and never calls any backend (AGOT-A1).
  - The Python server, which does the real work, uses non-standard method names on stdio, so Claude Code cannot discover its tools (AGOT-A6). Its default transport is HTTP on `0.0.0.0:8000`, and its admin routes authenticate fail-open (AGOT-A3).
  - The clone carries a tracked `.claude/settings.local.json`. It pre-approves `python3`, `node`, `npx`, `rm` and `claude mcp add` for any Claude Code session opened in the tree (AGOT-A2).
- **agi-mcp-server (AGI)**
  - The clone's `origin` and the launch configuration it documents point into the `cognitivecomputations` GitHub namespace. Upstream now calls that namespace squatted, and the account is an organization created 2025-12-08 (AGI-P1). The code on disk still matches the real upstream, `QuixiAI/agi-mcp-server`, blob for blob.
  - Its 24 tools are a persistent memory store whose text returns to the model in later sessions. That makes it a cross-session prompt-injection channel, and the tree ships a persona prompt aimed at the agent (AGI-A1, AGI-A2).
- **On the host**
  - Neither server is configured in any client config checked, neither is running, and Docker holds nothing for either (§6.1).
  - What ran, on 2026-03-01: three esbuild postinstall hooks executed native binaries from npm in agi-mcp-server (AGI-H1), and a CPython 3.13 imported two side-effect-free AGoT modules (AGOT-H1). Nothing under `~/.claude/mcp-servers/` changed after 2026-03-01T21:33:06Z.
- **C8 and C9**
  - Neither server exposes a file-writing or command-running MCP tool (per tool, §4.1 and §5.1).
  - C9 therefore does not attach as `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.3 §18.2 :944-945 words it.
  - Their database-writing and network tools would still run outside C8 (H5-X1).

## 2. Method, safety and conventions

### 2.1 Method

- Static reads only, with `grep`, `find`, `sed`, `stat`, `file`, `strings`, `shasum`, `unzip -l` and `unzip -p`, passing the paths as arguments. Nothing in either tree was executed, imported, built or installed.
- No git command ran against either tree. `.git/config` was read as a plain file.
- Archives were listed with `unzip -l`, and single members were streamed with `unzip -p`. Two members were written as text into a new, empty scratch directory for `diff`. Nothing was extracted into a tree.
- To build advisory queries, the lockfiles and `node_modules/*/package.json` files were parsed as data, with `python3 -I` (stdlib `json`) and `awk`.
- Network access was read-only: `gh api` GETs with no method or field flags, and WebFetch (§9).
- No real `.env` or credential file was opened; neither tree has one (`.env.example` templates only).
- `~/.claude.json`, `~/.claude/settings.json`, the Claude Desktop config and the VS Code config were not read. Their MCP keys come from the evidence script, as booleans.
- `claude mcp list` was not used: the safety brief forbids it, and it hung for more than 120 s on turing (plan `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §2.5 :142).

### 2.2 Deviation from the safety brief

- One command ran `python3 -I -c` with its working directory inside the AGoT tree, to parse `server/package-lock.json` with stdlib `json`. Isolated mode keeps the working directory off `sys.path`, so no file in the tree could be imported. Rule 1 forbids the pattern regardless. Every later parse ran from the worktree, with the path as an argument.

### 2.3 Severity and verdicts

- **blocker**: enabling the server as it stands would expose the host, or would feed fabricated or attacker-controllable content into agent context. Configuration on turing cannot mitigate it.
- **major**: a material risk or defect; an enable would need the condition stated.
- **minor**: a hygiene, accuracy or low-likelihood issue.
- Verdicts: **PASS** is a verified pass, **FAIL** a verified fail, **CNV** could not verify, with the reason given.
- Finding IDs: `AGOT-` is adaptive-graph-of-thoughts, `AGI-` is agi-mcp-server and `H5-X` covers both. The area letters are P provenance, A permissions and capabilities, E egress and H host exposure.

### 2.4 Conventions

- A `file:line` with no directory is relative to the server's tree, `~/.claude/mcp-servers/<server>/`. Repository files are linked.
- Secret-looking literals are described, never quoted. That covers default passwords and template key values.
- Advisory counts come from the GitHub global advisory database (`gh api advisories?...&affects=<name@version,...>`, 2026-10-21) and exclude withdrawn entries. Many entries are 2026 CVEs and are reported as fetched.

## 3. Checklist

| ID | Item | Pass means | adaptive-graph-of-thoughts | agi-mcp-server |
| --- | --- | --- | --- | --- |
| C-P1 | Upstream identity and health | known owner, maintained, licensed, signed history | FAIL: single user, agent-written history, MIT versus Apache-2.0 (AGOT-P3) | FAIL: squatted origin (AGI-P1); no LICENSE file (AGI-P2); unsigned (AGI-P4) |
| C-P2 | Local tree against upstream at HEAD | every tracked blob identical; local-only files explained | PASS: 305 identical, 0 modified; 2 `.pyc` (AGOT-H1) | PASS: 33 identical, 0 modified; local `package-lock.json` (AGI-P3) |
| C-P3 | Newer upstream commits | none, or none security-relevant | FAIL: 6, dependency bumps, 3 security-relevant (AGOT-P2) | FAIL: 1, the namespace fix (AGI-P1) |
| C-P4 | Repository advisories and security issues | 0 advisories; no open security issue | PASS: 0 advisories; dependabot PRs #159, #160 open since 2026-03-24 (AGOT-P2) | PASS: 0 advisories; 2 issues or PRs in all |
| C-P5 | `.dxt` and `.zip` bundles | built from the tree; nothing absent from source | FAIL: 4 bundles, 4 different `server/index.js`, vendored `node_modules` (AGOT-P1) | n/a: no bundle |
| C-P6 | Dependency advisories | no unfixed advisory on a runtime path | FAIL: pip 52 active, npm 54 active (AGOT-P2) | FAIL: 89 active, one on the runtime ORM (AGI-P3) |
| C-P7 | Install-time code | none ran, or all of it identified | PASS: none ran (no `node_modules`, no venv) | PASS: 3 esbuild postinstall hooks, identified (AGI-H1) |
| C-A1 | Tool inventory | every tool named and classified | PASS: §4.1 | PASS: §5.1, 24 tools |
| C-A2 | OS capabilities | bounded writes, no exec, no open listener, safe defaults | FAIL (AGOT-A3, AGOT-A5, AGOT-A8) | FAIL, minor only (AGI-A3) |
| C-A3 | Credentials read | names known; nothing read beyond the server's own config | FAIL: `.env` in the launch directory (AGOT-A8) | FAIL: `.env` in the launch directory (AGI-A3) |
| C-A4 | Embedded agent config | none, or inert | FAIL: tracked `.claude/settings.local.json` (AGOT-A2) | PASS: none |
| C-A5 | Install scripts | no pipe-to-shell, no privilege use | PASS: `install-dxt.sh`, `Makefile`, `.devcontainer`, `Dockerfile` (§4.1) | FAIL, minor: README tells users to run `sudo ln -sf` (AGI-A3) |
| C-A6 | Prompt-injection surface | no agent-directed text; outputs not attacker-shapeable | FAIL: fabricated output (AGOT-A1); LLM-to-Cypher loop (AGOT-A4) | FAIL: `prompt.md` (AGI-A2); memory re-injection (AGI-A1) |
| C-E1 | Outbound destinations | each one known, opt-in and minimal | FAIL, minor (AGOT-E1; inventory §4.4) | PASS: Postgres only (§5.4) |
| C-E2 | Telemetry | none, or off by default | PASS: declared SDKs never imported | PASS: none |
| C-E3 | Inbound listeners | none, or loopback with authentication | FAIL (AGOT-A3, AGOT-E2) | PASS: stdio only |
| C-H1 | Configured anywhere | no client config names the server or points at it | PASS; CNV for the inert `~/.claude/settings.json` block, by design (§6.1) | PASS; same CNV |
| C-H2 | What ran and what it left | identified; nothing persistent | PASS (AGOT-H1) | PASS (AGI-H1) |
| C-H3 | File modes and secret files | nothing writable by others, no setuid, no secret file | PASS (§6.1) | PASS (§6.1) |
| C-X1 | C8 guard coverage | every write or exec tool covered | FAIL (H5-X1) | FAIL (H5-X1) |

## 4. adaptive-graph-of-thoughts

### 4.1 Inventory

Evidence script output, verbatim except the upstream JSON, which is shortened:

```text
origin: https://github.com/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server.git   other remotes: none
HEAD: refs/heads/main @ 1f7c6cee241aa387399848e323e66c665e82b7df   shallow: False   FETCH_HEAD mtime: None
reflog 2026-03-01T21:28:27Z  1f7c6cee241a  clone: from https://github.com/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server.git
command-running git config keys: none   live hooks: none
upstream: full_name SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server, owner_type User, license MIT, created 2025-06-06, pushed 2026-04-24, 32 stars, 9 forks, 3 open issues
HEAD commit upstream: {"author_login": "SaptaDey", "date": "2026-02-27T23:42:43Z", "subject": "Merge pull request #158 from SaptaDey/copilot/modernize-repository-and-fix-issues", "verified": true}
HEAD vs default branch: {"ahead_by": 6, "behind_by": 0, "status": "ahead"}
tree vs upstream@HEAD: 305 identical, 0 modified, 2 local-only, 0 missing locally
```

The tree has three entry points, and they share no code:

| Entry point | Launch | Transport | Code |
| --- | --- | --- | --- |
| DXT server | `node server/index.js` (`manifest.json:24-34`) | stdio, official MCP TypeScript SDK (`server/index.js:3-13`, `:1565-1575`) | Node, 1,582 lines, local heuristics only |
| Python stdio | `mcp-stdio`, `main_stdio.py` (`pyproject.toml:84`) | stdio, hand-written JSON-RPC loop (`server_factory.py:180-285`) | package `src/adaptive_graph_of_thoughts/` |
| Python HTTP | `mcp-server`, `main.py` (`pyproject.toml:83`); the default transport (`config/settings.yaml:7`) | FastAPI on uvicorn at `0.0.0.0:8000` (`main.py:47-54`; `config.py:498-499`) | the same package |

MCP tools:

| Tool | Surface | Inputs (required first) | Class | Under C8? |
| --- | --- | --- | --- | --- |
| `scientific_reasoning_query` | DXT, `server/index.js:210-250` | `query`; `parameters` (`include_reasoning_trace`, `include_graph_state`, `max_depth`, `confidence_threshold`) | compute, fabricated (AGOT-A1); appends to the server's own log | no, outside the matcher; takes no path |
| `analyze_research_hypothesis` | DXT, `:252-273` | `hypothesis`; `context`, `evidence_sources[]` | compute, `Math.random()` scores | no; takes no path |
| `explore_scientific_relationships` | DXT, `:275-300` | `concepts[]`; `relationship_types[]`, `depth` | compute, `Math.random()` strengths | no; takes no path |
| `validate_scientific_claims` | DXT, `:302-326` | `claims[]`; `evidence_requirement`, `sources[]` | compute, `Math.random()` evidence | no; takes no path |
| `graph_reasoning` | Python stdio, through the non-standard `listTools` and `callTool` (`server_factory.py:417-479`) | `query`; `confidence_threshold` | DB write and delete (Neo4j) and network (search APIs), if stages load (AGOT-A7) | no; takes no path |
| `asr_got.query` (JSON-RPC method) | Python stdio (`server_factory.py:317-320`); HTTP `/mcp` (`mcp_public.py:46-48`) | `query`; `session_id`, `parameters`, `context` | as `graph_reasoning` | no; takes no path |

- **DXT prompts**: three static prompts (`server/index.js:371-412`), with no agent-directed instructions beyond their task. **DXT resources**: none (`:483-490`).
- **HTTP routes** in the default transport. They are not MCP tools for Claude Code, but the default transport opens them.
  - `/mcp` POST, `/mcp/tools`, `/mcp/capabilities` and `/mcp/info` have no authentication (`mcp_public.py:22-174`). The router is mounted without a dependency (`app_setup.py:474-478`).
  - `/admin/mcp`, with `/tools/{tool_name}` for the four DXT-named tools, `/nlq` and `/graph` take a bearer token. They fail closed when `auth_token` is unset (`api/routes/mcp.py:45-58`).
  - `/setup`, `/setup/settings`, `/setup/settings/reset`, `/dashboard`, `/dashboard/save_config`, `/chat`, `/health`, `/debug` and `/tools` take HTTP Basic, which fails open (`app_setup.py:43-58`).
  - `/docs`, `/redoc` and `/openapi.json` have no authentication (`app_setup.py:150-158`).
- **OS capabilities**
  - File writes: AGOT-A8; `/setup` and `/dashboard` (AGOT-A3).
  - Subprocess: `server_factory.py:39-101` and `:142-177` (`Popen` of `python3 -m uvicorn ... --host 0.0.0.0`, `curl`, arbitrary command lists). Nothing in `src/` calls them; the tests carry their own copies.
  - Dynamic import: `application/got_processor.py:132-134`, of stage classes named in config. No `eval`, `exec` or `pickle`.
  - Neo4j: `infrastructure/neo4j_utils.py:191-260`, with defaults at `config.py:485-488` (a hard-coded default password at `:487`).
  - `asyncpg` is imported (`domain/services/database_manager.py:8`).
- **Env vars and credentials read (names only)**
  - Python:
    - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `RATE_LIMIT_ENABLED` and `RATE_LIMIT_PER_MINUTE` (pydantic fields, `config.py:19-42`).
    - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` and `NEO4J_DATABASE` (`config.py:482-490`; `app_setup.py:209-212`).
    - Nested `APP__*` and `NEO4J__*` (`config.py:581-583`), and `AGOT_*` (`config.py:722-760`).
    - `BASIC_AUTH_USER` and `BASIC_AUTH_PASS` (`app_setup.py:49-50`), and `OPENAI_MODEL` and `CLAUDE_MODEL` (`services/llm.py:292`, `:301`).
    - `SECRETS_PROVIDER`, `<VAR>_SECRET_NAME`, `GCP_PROJECT_ID`, `VAULT_ADDR` and `VAULT_TOKEN`, plus ambient AWS credentials through boto3 (`services/secret_manager.py:21-76`).
    - A `.env` file in the launch directory (AGOT-A8).
  - DXT:
    - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PUBMED_API_KEY`, `ENABLE_EXTERNAL_SEARCH`, `MAX_REASONING_DEPTH` and `CONFIDENCE_THRESHOLD` (`server/index.js:167-175`).
    - `AGOT_BACKEND_URL` (`:80`) and `LOG_LEVEL` (`server/logger.js:10`).
- **Install scripts (C-A5)**
  - `install-dxt.sh` uses no `sudo` and pipes nothing to a shell. It runs `npm install` in `server/` (`:54`) and loads `server/index.js` with `node -e "require(...)"` (`:87-91`), which would start the server.
  - `scripts/setup_mcp_client.sh:48` only prints a `curl ... | python3 -` hint in an error message.
  - The `Makefile` targets are `poetry` commands (`:3-22`). `.devcontainer/devcontainer.json:3` runs `poetry install && poetry run pre-commit install`, with no privileged arguments. The `Dockerfile` drops to `appuser` (`:90`).
  - No shell script in the tree has its execute bit set (§6.1).

### 4.2 Provenance findings

#### AGOT-P1: the four bundles are not built from the source tree

- **Severity**: major
- **Location**: `adaptive-graph-of-thoughts-v1.0.2-final.dxt`, `adaptive-graph-of-thoughts-v1.0.1-submission.dxt`, `Adaptive-Graph-of-Thoughts-MCP-server.dxt` and `adaptive-graph-of-thoughts-dxt-v1.0.0-production.zip`. All four are tracked upstream and identical to it.
- **Problem**
  - Each bundle has its own `manifest.json` and `server/index.js`. None matches the tree's copies, or another bundle's.
  - All four vendor `server/node_modules/` (1,237 entries in each `.dxt`, 2,201 in the zip), which the source tree lacks. The vendored versions include `form-data` 4.0.3 (critical CVE-2025-7783), `axios` 1.10.0 and `@modelcontextprotocol/sdk` 1.13.2.
  - The v1.0.0 zip's server proxies every tool call to a hard-coded `http://localhost:8000/mcp`. That is the unauthenticated public route of AGOT-A3, so this bundle needs the open HTTP server running.
  - The other three never call their backend.
  - Three of the four ship the `.claude/settings.local.json` of AGOT-A2.
  - No bundle contains a native binary. The only executable is the JS script `node_modules/.bin/node-which`.
- **Evidence**

```text
sha256 prefix          manifest.json      server/index.js     files
tree                   06f346c5322187f1   782c5b3c3226ed71    -
v1.0.2-final.dxt       a6185e8e19620b02   b998a40a2d70e1d4    1372
v1.0.1-submission.dxt  fba4da49f1e82fe3   9c20ad5aaa837a48    1372
MCP-server.dxt         b03d0de61024fd29   5785ee2742f027fb    1370
v1.0.0-production.zip  d18f64152f796be1   1b153adc99f0cf86    2220
$ unzip -p adaptive-graph-of-thoughts-v1.0.2-final.dxt server/node_modules/form-data/package.json | grep -m1 '"version"'
  "version": "4.0.3",
$ unzip -p adaptive-graph-of-thoughts-dxt-v1.0.0-production.zip adaptive-graph-of-thoughts-dxt-v1.0.0-production/server/index.js | grep -nE 'makeBackendRequest\(|baseUrl ='
77:    this.baseUrl = 'http://localhost:8000'; // Default Python server URL
422:  async makeBackendRequest(endpoint, data, timeout = 30000) {
489:      const result = await this.makeBackendRequest('/mcp', requestData);
526:      const result = await this.makeBackendRequest('/mcp', requestData);
562:      const result = await this.makeBackendRequest('/mcp', requestData);
599:      const result = await this.makeBackendRequest('/mcp', requestData);
```

- **Fix**: never install a bundle on turing. If a DXT were wanted, rebuild it from a pinned, audited commit and ignore the committed artifacts. The hazard needs an install into Claude Desktop, and turing has no Claude Desktop extensions directory (§6.1).

#### AGOT-P2: the pinned dependencies carry 106 active advisories, and the upstream fixes came after the clone

- **Severity**: major
- **Location**: `poetry.lock`; `server/package-lock.json`; `package.json:13-15`
- **Problem**
  - **`poetry.lock`**: 44 of its 141 packages were queried, the direct dependencies plus the security-relevant transitive ones. They have 52 active advisories: 3 critical, 32 high, 13 medium and 4 low.
    - The three criticals: `certifi` 2025.4.26 (GHSA-6q48-6c7w-9gw2, emSign roots), `anyio` 4.9.0 (GHSA-82r6-8w77-94w6, CVE-2026-63374) and `python-jose` 3.5.0 (GHSA-3qf3-8w2g-rqmx, CVE-2026-85394, no patched version).
    - `rsa` is pinned at 4.2 (`poetry.lock:2703-2704`; GHSA-xrx6-fmxq-rjj2, CVE-2020-25658).
    - `mcp` 1.9.2 has six advisories, among them CVE-2025-53365, CVE-2025-53366 and CVE-2025-66416.
  - **npm**: the DXT server lock plus the root devDependency have 54 active advisories: 3 critical, 20 high, 28 medium and 3 low.
    - The criticals: `form-data` 4.0.3 (GHSA-fjxv-7rqg-78g4, CVE-2025-7783); `@modelcontextprotocol/inspector` below 0.14.1 (GHSA-7f8r-222p-6f5g, CVE-2025-49596: "MCP Inspector proxy server lacks authentication between the Inspector client and proxy"); and `proxy-addr` 2.0.7 (GHSA-jqcg-44mw-7w3h).
  - **Reachability**
    - Of the risky declared packages, the server imports only `asyncpg` (`domain/services/database_manager.py:8`). `python-jose`, `passlib`, `bcrypt`, `rsa`, `ecdsa`, `sentry_sdk` and `prometheus_client` are declared (`pyproject.toml:25-51`), but nothing in `src/` imports them.
    - Starlette, urllib3, python-multipart, httpx, anyio and certifi sit on the HTTP and outbound paths.
    - The DXT server reaches `axios` only in the v1.0.0 bundle (AGOT-P1).
    - The Inspector is a dev tool and was never installed here.
  - **The six upstream commits after HEAD**
    - All are dependency bumps, and three are security-relevant: `mcp` 1.9.2 to 1.10.0 (fixes CVE-2025-53365); `form-data` 4.0.3 to 4.0.4 (fixes CVE-2025-7783); and the Inspector range from `^0.1.0` to `^0.16.1`, which clears CVE-2025-49596. CVE-2025-58444 needs 0.16.6.
    - None touches server code. The bundles still vendor `form-data` 4.0.3.
- **Evidence**

```text
$ gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/compare/1f7c6cee241aa387399848e323e66c665e82b7df...main --jq '.files[] | [.status, (.additions|tostring), (.deletions|tostring), .filename] | @tsv'
modified  1  1  package.json              ("@modelcontextprotocol/inspector": "^0.1.0" -> "^0.16.1")
modified  4  3  poetry.lock               (mcp 1.9.2 -> 1.10.0)
modified  3  3  server/package-lock.json  (form-data 4.0.3 -> 4.0.4)
$ gh api --paginate "advisories?ecosystem=pip&per_page=100&affects=rsa@4.2,mcp@1.9.2,<42 more pins>" --jq '.[] | [.ghsa_id, .severity, (.withdrawn_at // "-")] | @tsv' | sort -u | <severity tally>
   3 critical   32 high   13 medium   4 low
$ gh api --paginate "advisories?ecosystem=npm&per_page=100&affects=<99 pins from server/package-lock.json>,@modelcontextprotocol/inspector@0.1.0" --jq ... | <severity tally>
   3 critical   20 high   28 medium   3 low   (7 withdrawn, excluded)
```

- **Fix**: none on turing short of a fork; removal clears it. An enable would need a fresh lock at the upstream tip, the two open dependabot updates (#159, #160) and a re-audit.

#### AGOT-P3: one user, an agent-written history, and an inconsistent license

- **Severity**: minor
- **Location**: upstream `SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server`; `LICENSE:1`; `pyproject.toml:8`, `:14`; `manifest.json:13`; `package.json:14`
- **Problem**
  - **Owner and activity**: a personal account created 2023-08-15, with 41 public repositories. The repository has 32 stars and 9 forks and no security advisory.
  - **HEAD signature**: HEAD `1f7c6cee` merges PR #158, written by the Copilot coding agent. Its `verified: true` is GitHub's own web-flow signature on the merge (committer `GitHub`, reason `valid`), not the author's key. One of the six newer commits, `07b97361c130`, is unsigned.
  - **Security-titled PRs**: a burst landed on 2025-06-20 to 2025-06-22, among them "Fix authentication bypass in verify_token" (#101), "Fix token verification bypass" (#121), "Fix Cypher injection in Neo4j utilities" (#122) and "Fix credential exposure in Neo4j debug logs" (#100). The fail-open Basic authentication of AGOT-A3 survived them all.
  - **A regressed bump**: PR #136 raised the Inspector to 0.14.3 and merged on 2025-06-22, yet HEAD's root `package.json:14` declares `^0.1.0`. PR #158's 15 files do not include it; the reverting commit was not traced.
  - **License**: `LICENSE` is MIT, and so are GitHub's detection and `manifest.json:13`. `pyproject.toml:8` and its classifier at `:14` say Apache-2.0.
- **Evidence**

```text
$ gh api users/SaptaDey --jq '[.login, .type, .created_at, .public_repos, .followers] | @tsv'
SaptaDey  User  2023-08-15T09:39:59Z  41  8
$ gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/commits/1f7c6cee241aa387399848e323e66c665e82b7df --jq '[.commit.committer.name, .commit.verification.verified, .commit.verification.reason, (.parents | length)] | @tsv'
GitHub  true  valid  2
$ gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/security-advisories --jq length
0
$ gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/pulls/136 --jq '[.state, .merged, .merged_at] | @tsv'
closed  true  2025-06-22T19:59:29Z
```

- **Fix**: none; this is context for the decision.

#### AGOT-P4: the DXT manifest's privacy and security claims are self-attested, and the secrets it collects never reach the server

- **Severity**: minor
- **Location**: `manifest.json:32`, `:78-140`; `PRIVACY_POLICY.md:13-14`, `:73`
- **Problem**
  - **Non-spec claims**: `manifest.json:130-140` declares a `privacy` block (`"data_collection": "none"`) and a `security` block (`"sandbox": false`, `"code_signing": false`). The fetched MCPB manifest spec lists `privacy_policies` among its optional fields and, per the fetch, defines neither `privacy` nor `security`. A host cannot enforce these claims; `"sandbox": false` is the accurate part.
  - **Secrets collected but unused**: `user_config` asks for a Neo4j password and for OpenAI, Anthropic and PubMed keys, each marked `sensitive` (`:78-120`). But `mcp_config.env` is `{}` (`:32`), and per the spec a value reaches the server only through `${user_config.KEY}` substitution. The secrets entered would be stored and never used.
  - **Storage claim**: `PRIVACY_POLICY.md:73` promises "API keys stored securely using OS keychain/credential manager". The Python setup writes the Neo4j credentials to a plaintext `.env`, mode 0600, in the working directory (`app_setup.py:261-269`; `agt_setup/__main__.py:63-67`).
- **Evidence**: WebFetch of <https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md>, redirected from `anthropics/dxt`. Quoted: "`${user_config.KEY}`: Replaced with the user-provided value for configuration KEY."; "**privacy_policies**: Array of URLs to privacy policies for external services"; "**sensitive**: For string types, mask input and store securely (default: false)."
- **Fix**: none; this is context for the decision.

### 4.3 Permissions findings

#### AGOT-A1: the DXT server fabricates its scientific results

- **Severity**: blocker
- **Location**: `manifest.json:24-34`, `:51-55`; `server/index.js:492-552`, `:554-624`, `:993-1510`
- **Problem**
  - **No backend call**: the DXT server is the only AGoT entry point that speaks standard MCP, through the official SDK. All four tools compute their answers locally. `makeBackendRequest` (`:492`) is defined and never called, and the "Standalone" handlers (`:563-564`, `:997-998`, `:1176-1177`, `:1244-1245`) build their results from 34 `Math.random()` calls.
  - **Random numbers presented as evidence**: confidence and evidence strength (`:1018`, `:1035`), study counts (`:1489-1492`), replication status (`:1452`), and expert agreement and consensus (`:1507-1509`). The result reports `evidence_sources_consulted: ["internal_knowledge", "scientific_reasoning"]` (`:612`).
  - **A claim the code doesn't meet**: the manifest says `validate_scientific_claims` will "Validate scientific claims against peer-reviewed literature from PubMed, Google Scholar, and other academic sources" (`manifest.json:54`). No such lookup exists.
  - **Effect**: the same input returns different "evidence" on every call. An agent would treat these values as findings, which on a research platform corrupts results silently.
- **Evidence**

```text
$ grep -nE "makeBackendRequest|Standalone|internal_knowledge|Math\.random" server/index.js    (excerpt)
492:  async makeBackendRequest(endpoint, data, timeout = 30000) {
563:      // Standalone ASR-GoT implementation
612:        evidence_sources_consulted: ["internal_knowledge", "scientific_reasoning"],
1018:    const confidence = Math.random() * 0.4 + 0.5; // 0.5-0.9
1489:      experimental_studies: Math.floor(Math.random() * 20) + 5,
1507:      consensus_level: Math.random() * 0.6 + 0.3, // 0.3-0.9
$ grep -c 'Math\.random' server/index.js
34
$ grep -nE 'makeBackendRequest|axios' server/index.js server/error-handler.js server/logger.js
server/index.js:15:import axios from 'axios';
server/index.js:492:  async makeBackendRequest(endpoint, data, timeout = 30000) {
server/index.js:510:      const response = await axios.post(`${this.baseUrl}${endpoint}`, data, {
```

- **Fix**: do not enable the DXT server or any bundle (AGOT-P1). No configuration fixes this.

#### AGOT-A2: a tracked `.claude/settings.local.json` pre-approves code execution in any session opened in the tree

- **Severity**: major
- **Location**: `.claude/settings.local.json:1-48`, tracked upstream; a copy also ships in three bundles (AGOT-P1)
- **Problem**
  - **The allow list**: 41 `permissions.allow` entries with an empty `deny` (`:46`). They include:
    - interpreters: `Bash(python3:*)` (`:23`), `Bash(node:*)` (`:20`), `Bash(npx:*)` (`:27`) and `Bash(timeout:*)` (`:36`);
    - file operations: `Bash(rm:*)` (`:30`), `Bash(chmod:*)` (`:9`) and `Bash(cp:*)` (`:33`);
    - installs: `Bash(npm install:*)` (`:31`) and `Bash(./install-dxt.sh:*)` (`:25`);
    - MCP registration: `Bash(claude mcp add:*)` (`:39`) and `Bash(claude mcp:*)` (`:40`);
    - `WebFetch(domain:github.com)` (`:5-7`).
  - **Embedded password**: two entries embed a Neo4j password literal in their command strings (`:42-43`).
  - **Absent keys**: the file has no `hooks`, `disableAllHooks`, `mcpServers` or `enableAllProjectMcpServers` key. The tree has no `CLAUDE.md`, `AGENTS.md`, `.mcp.json` or agent definitions.
  - **Effect**
    - Claude Code reads this file name ([`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md):478-482).
    - A session opened with this tree as its project would run any `python3`, `node`, `npx` or `timeout` command (and `timeout` wraps anything) without a prompt. It could also register new MCP servers.
    - The user-level deny list (plan `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` D11 item 4, :348-353) and the C8 hook would still load, because the file does not disable hooks.
    - But C8 sees command text, not what a script does ([`util/claude_agent_guard.py`](../util/claude_agent_guard.py):91-94, gap 1), and `python3 x.py` is exactly what this file pre-approves.
- **Evidence**: `cat -n .claude/settings.local.json`, at the lines cited.
  - CNV: how these local allow rules rank against user-level deny rules, and whether the folder-trust dialog gates them, could not be re-checked against current documentation. `code.claude.com` and `docs.claude.com` both refused the connection (§9).
- **Fix**: removal (§8). If the tree is ever kept, delete `.claude/` before any Claude Code session there. Never open Claude Code inside an untrusted clone.

#### AGOT-A3: the Python server's default HTTP mode listens on every interface, and its admin routes authenticate fail-open

- **Severity**: blocker
- **Location**: `config.py:498-504`; `config/settings.yaml:5-7`; `main.py:35-54`; `app_setup.py:43-58`, `:188-194`, `:199-270`, `:326-410`, `:442-478`; `api/routes/mcp_public.py:22-75`; `scripts/docker-entrypoint.sh:11`, `:21`
- **Problem**
  - **Bind**: HTTP is the default transport (`settings.yaml:7`; `config.py:504`). `mcp-server` binds `0.0.0.0:8000` (`main.py:47-54`, with `config.py:498-499` and `settings.yaml:5-6`), with uvicorn's reload on (`config.py:500`).
  - **Basic authentication fails open**: `get_basic_auth` returns `True` whenever `BASIC_AUTH_USER` or `BASIC_AUTH_PASS` is unset, so any credentials pass (`app_setup.py:49-58`). When the credentials are set, the comparison is not constant-time (`:52`).
  - **`/mcp` has no authentication**: it is mounted with no dependency (`app_setup.py:474-478`). Its own comment says "Public MCP router without authentication for Smithery" (`mcp_public.py:22-23`).
  - **CORS**: every origin is allowed, with credentials (`app_setup.py:188-194`; `config.py:502`).
  - **What anyone who can reach port 8000 can do** (the LAN, or a web page through the browser):
    - read the Neo4j password from the `/setup` form, prefilled from the environment or from the hard-coded default (`app_setup.py:208-213`);
    - make the server open a Bolt connection to any URI they name (`:243`, `:74-80`), and write `.env` in its working directory (`:261-269`);
    - rewrite `config/settings.yaml`, including `host` and `port` (`:326-338`, `:365-385`);
    - spend the owner's LLM key through `/chat` (`:395-410`);
    - read the last five prompts and responses at `/debug`, which renders them into HTML unescaped (`:463-470`);
    - drive the pipeline through `asr_got.query`, with its Neo4j writes and deletes (AGOT-A5).
  - **The correct default**: the bearer-token routes fail closed when no token is set (`api/routes/mcp.py:45-47`).
- **Evidence**

```text
app_setup.py:49:    user = os.getenv("BASIC_AUTH_USER")
app_setup.py:51:    if user and password:
app_setup.py:58:    return True
app_setup.py:474:    app.include_router(
app_setup.py:475:        mcp_public_router,
app_setup.py:476:        prefix="/mcp",
config.py:498:    host: str = "0.0.0.0"
config/settings.yaml:7:  mcp_transport_type: "http"
```

- **Fix**: removal. If the Python server were ever used, run it on stdio only. Never start `mcp-server` or the compose files (AGOT-E2).

#### AGOT-A4: `/nlq` runs Cypher that the LLM writes

- **Severity**: minor (the route is token-gated and fails closed by default)
- **Location**: `api/routes/nlq.py:24-38`, `:56-100`; `infrastructure/neo4j_utils.py:191-256`
- **Problem**
  - **The flow**: the question passes a four-regex "prompt injection" filter (`:24-38`) and is wrapped as "Translate the question to a Cypher query: ..." (`:71`). Whatever the LLM returns is executed as Cypher (`:84`), with no allow-list. The result rows are then pasted into a second LLM prompt (`:91-95`).
  - **Read transaction**: the query runs in `session.execute_read` (the `tx_type="read"` default, `neo4j_utils.py:195`, `:241-242`). Whether the server rejects write clauses there was not checked against Neo4j documentation (CNV).
  - **What remains regardless**: a steered model can read any part of the graph, and send it to the caller and to the LLM provider.
  - **Default exposure**: the route needs the bearer token, and the token check fails closed when no token is set (`api/routes/mcp.py:45-47`). That limits this to deployments that configure a token.
- **Evidence**: `nlq.py:72` `cypher = await asyncio.to_thread(ask_llm, cypher_prompt)`; `nlq.py:84` `records = await execute_query(cypher)`; `neo4j_utils.py:195` `tx_type: str = "read"`.
- **Fix**: removal. An enabled HTTP mode would need an allow-list or a parser gate before `execute_query`.

#### AGOT-A5: pipeline pruning deletes across the whole Neo4j database

- **Severity**: major (the code is present; for reachability, see AGOT-A7)
- **Location**: `domain/stages/stage_5_pruning_merging.py:40-58`, `:84-100`; `config.py:485-488`
- **Problem**
  - **Node deletes**: stage 5 deletes, database-wide, every non-root `:Node` of type HYPOTHESIS, EVIDENCE or INTERDISCIPLINARY_BRIDGE below the confidence and impact thresholds, plus every non-root `:Node` with no relationships (`:54-57`).
  - **Relationship deletes**: it also deletes every relationship of any type whose `confidence` property is below the threshold (`:86-90`).
  - **No scope**: nothing ties these deletes to the current session.
  - **Default target**: the default `neo4j` database on `neo4j://localhost:7687` (`config.py:485-488`). Any other data held there would be deleted.
  - **APOC dependency**: the stage needs the APOC plugin (`apoc.coll.min`, `:45`).
- **Evidence**

```text
stage_5_pruning_merging.py:54:        OPTIONAL MATCH (m:Node)
stage_5_pruning_merging.py:55:        WHERE NOT m:ROOT AND size((m)--()) = 0
stage_5_pruning_merging.py:57:        FOREACH (nd IN nodes_to_delete | DETACH DELETE nd)
stage_5_pruning_merging.py:87:        MATCH ()-[r]->()
stage_5_pruning_merging.py:88:        WHERE r.confidence IS NOT NULL AND r.confidence < $threshold
stage_5_pruning_merging.py:89:        DELETE r
```

- **Fix**: removal. An enable would need a dedicated, empty Neo4j database.

#### AGOT-A6: the Python stdio server is not MCP-conformant, so a standard client sees no tools

- **Severity**: major
- **Location**: `server_factory.py:180-285`, `:288-342`, `:417-479`
- **Problem**
  - **Method names**: the stdio loop dispatches `initialize`, `asr_got.query`, `listTools`, `callTool` and `shutdown` (`:312-331`); anything else gets "Method not found" (`:333-337`). The MCP specification names the methods `tools/list` and `tools/call`.
  - **Unsolicited output**: the loop also writes an unsolicited `server/ready` message to stdout before the handshake (`:203-207`).
  - **Effect**: read statically, Claude Code would list no tools from this server. The one AGoT path that might do real work cannot be reached through MCP. The server was not run, by design (CNV for live behaviour).
- **Evidence**: `server_factory.py:321` `elif method == "listTools":` and `:325` `elif method == "callTool":`. WebFetch of <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>: "To discover available tools, clients send a `tools/list` request." and "To invoke a tool, clients send a `tools/call` request".
- **Fix**: removal. Upstream would have to adopt the MCP SDK's stdio server.

#### AGOT-A7: a static reading says the pipeline loads no stages (uncertain)

- **Severity**: minor (uncertain: a static reading, never run)
- **Location**: `application/got_processor.py:110-133`; `config.py:565-583`, `:610-613`; `config/settings.yaml:13`, `:71`; `domain/stages/stage_4_evidence.py:105`, `:133-136`, `:168-171`
- **Problem**
  - **The stage list sits in a dict**: the runtime `settings` object is a `RuntimeSettings` whose `asr_got` field is a plain `dict` (`config.py:576`). `pipeline_stages` sits inside that dict (`settings.yaml:13`, `:71`).
  - **The loader tests for an attribute**: it checks `hasattr(self.settings.asr_got, "pipeline_stages")` (`got_processor.py:120-122`), which is false for a dict key. It then logs a warning and returns no stages (`:124-127`).
  - **Stage 4 reads missing fields**: it reads `settings.pubmed`, `settings.google_scholar` and `settings.exa_search` (`stage_4_evidence.py:105`, `:133-136`, `:168-171`), none of which `RuntimeSettings` defines (`config.py:565-583`).
  - **If this reading holds**: `asr_got.query` and `graph_reasoning` return an empty pipeline, the search egress of §4.4 never fires, and the dynamic stage import (`got_processor.py:132-134`) never runs.
- **Evidence**: as cited; not executed.
- **Fix**: none. This finding exists so that AGOT-A5 and §4.4 read as "code present", not "observed".

#### AGOT-A8: files are written and read in the launch directory

- **Severity**: minor
- **Location**: `main_stdio.py:11-16`; `app_setup.py:206-207`, `:261-269`; `config.py:42`, `:490`, `:582`; `server/logger.js:16-17`, `:60`, `:79-99`
- **Problem**
  - **Log truncation**: the stdio entry point truncates and rewrites `stdio_server.log` in whatever directory launches it (`main_stdio.py:11-16`, `filemode="w"`). Claude Code launching it from a Juniper checkout would write there.
  - **`.env` reads**: pydantic-settings loads `.env` from the launch directory (`config.py:42`, `:490`, `:582`), and `/setup` loads every key in it into the process environment (`app_setup.py:206-207`). A checkout's `.env` would be read.
  - **`.env` writes**: `/setup` creates or edits `.env` in the launch directory (`:261-269`).
  - **DXT log**: the DXT server appends to `<tree>/logs/dxt-server.log`, rotates it, and unlinks old `dxt-server-*.log` files in the same directory (`server/logger.js:16-17`, `:60`, `:79-99`). That path is fixed, not model-controlled.
- **Evidence**: as cited.
- **Fix**: removal.

### 4.4 Egress

This inventory records code present in the tree. Reachability is as AGOT-A7 describes.

| Destination | Code | Data that leaves | When | Binary that needs a Little Snitch allow |
| --- | --- | --- | --- | --- |
| OpenAI API (SDK default host) | `services/llm.py:296-304`; default provider `openai` (`config.py:22-25`) | the `/chat` question; the `/nlq` question and DB rows (`nlq.py:71`, `:91-95`) | the `openai` package installed and a key set | the Python interpreter that runs the server |
| Anthropic API (SDK default host) | `services/llm.py:287-295` | the same | `LLM_PROVIDER=claude` | the same |
| `eutils.ncbi.nlm.nih.gov` | `pubmed_client.py:137-159`, `:232-246`; `config.py:530` | query text (`term`), optional key and email | pipeline stage 4 | the same |
| `serpapi.com` (Google Scholar) | `google_scholar_client.py:147-171`; `config.py:523` | query text (`q`) and the API key, both in the URL query string | stage 4, with a key | the same |
| `api.exa.ai` | `exa_search_client.py:52-53`, `:130-150`, `:198`; `config.py:538` | query text; the key in an `x-api-key` header | stage 4, with a key | the same |
| Neo4j, any URI | `config.py:485`; `app_setup.py:74-80`, `:243`, `:425-430`, `:452-457` | credentials and Cypher | default `neo4j://localhost:7687`; `/setup` takes any URI | the same, loopback by default |
| AWS Secrets Manager, GCP Secret Manager, Vault | `services/secret_manager.py:21-56`, `:61-76` | secret names; secrets come back | only when `SECRETS_PROVIDER` is set | the same |
| `unpkg.com` | `templates/dashboard.html:5` | a browser fetch of an unpinned script with no `integrity` attribute | whenever the dashboard is opened | the browser |
| `localhost:8000` | `server/index.js:80`, `:492-552` (never called); v1.0.0 bundle `:77`, `:489` | tool arguments | DXT never; v1.0.0 bundle on every call | `node`, loopback |

- **Telemetry**: none (C-E2 PASS). `sentry-sdk[fastapi]` and `prometheus-client` are declared (`pyproject.toml:47-49`), but nothing initializes them. A grep of `src/`, `server/` and `agt_setup/` for `sentry`, `prometheus`, `posthog`, `segment`, `mixpanel`, `telemetry`, `analytics`, `amplitude`, `datadog` and `opentelemetry` has no runtime hit. There is no update check.
- **Install-time egress (none of it ran on turing)**:
  - `poetry install`: `pypi.org` and `files.pythonhosted.org`.
  - `npm install` in `server/` (`install-dxt.sh:54`): `registry.npmjs.org`.
  - Docker Hub, for `neo4j:5.17.0` and `neo4j:5.15-community` (`docker-compose.yml:56`; `docker-compose.smithery.yml:16`).

#### AGOT-E1: an API key and an unpinned script cross the network in weak forms

- **Severity**: minor
- **Location**: `google_scholar_client.py:155-157`, `:171`; `templates/dashboard.html:5`
- **Problem**
  - **API key in the URL**: SerpApi requests carry the API key as a URL query parameter (`"api_key": self.api_key` among the GET parameters), where proxies and logs keep it. This is SerpApi's interface, not a defect in the code, but it is how the key leaves the host.
  - **Unpinned script**: the dashboard loads `https://unpkg.com/cytoscape/dist/cytoscape.min.js`, unpinned and without subresource integrity. It runs in the same origin as the fail-open admin API of AGOT-A3.
- **Evidence**: `google_scholar_client.py:155` `"api_key": self.api_key,`; `dashboard.html:5` `<script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>`.
- **Fix**: removal.

#### AGOT-E2: the compose files publish Neo4j and the app on every interface, with a well-known password

- **Severity**: major
- **Location**: `docker-compose.yml:12-13`, `:56-70`; `docker-compose.prod.yml:12-13`, `:41-56`; `docker-compose.smithery.yml:5-6`, `:10`, `:16-21`; `smithery.yaml:27-30`, `:76`
- **Problem**
  - **Published ports**: all three compose files publish the app's 8000. The dev and smithery files also publish Neo4j's 7687, and the dev and prod files its 7474. Every mapping is written `"host:container"` with no host IP, and Docker binds those on all interfaces.
  - **Well-known password**: the dev compose and the smithery compose and manifest set a hard-coded default Neo4j password (`docker-compose.yml:65`, plus its healthcheck at `:70`; `docker-compose.smithery.yml:10`, `:18`; `smithery.yaml:30`, `:76`).
  - **APOC**: the prod compose sets `NEO4J_dbms_security_procedures_unrestricted: "apoc.*"` (`:52`).
  - **Effect**: a `docker compose up` on turing would put a Neo4j with a known password on the LAN.
  - **Current state**: nothing has run. No related image, container or volume exists (§6.1).
- **Evidence**: `docker-compose.yml:13` `- "${APP_PORT:-8000}:8000"`, and `:59-61` `ports: - "7474:7474" - "7687:7687"`. The old container on turing with a published port shows the same default: `docker ps -a` lists it as `0.0.0.0:8888->8888/tcp`.
- **Fix**: removal. Never run these compose files on turing.

### 4.5 Host exposure findings

#### AGOT-H1: untrusted code was imported once, on 2026-03-01, and left two `.pyc` files

- **Severity**: minor
- **Location**: `src/adaptive_graph_of_thoughts/__pycache__/__init__.cpython-313.pyc` (319 bytes) and `async_server.cpython-313.pyc` (3,352 bytes), both dated 2026-03-01T21:33:06Z
- **Problem**
  - **The import**: a CPython 3.13 imported `adaptive_graph_of_thoughts` from this tree 4 min 39 s after the clone (reflog: 21:28:27Z). Only `__init__.py` and `async_server.py` were compiled, and both `.pyc` files embed the tree's path.
  - **What ran**: `__init__.py:6` imports `async_server`, which imports `mcp.server` (`async_server.py:5`) and defines placeholders that return `{}` and `object()` (`:36-52`). Neither module does any I/O. No other module in the package was compiled, so nothing else from the tree ran.
  - **The command, unidentified**: the footprint matches `scripts/setup_mcp_client.sh:127`, which runs `python3 -c "import sys; sys.path.insert(0, 'src'); import adaptive_graph_of_thoughts"`. The command that actually ran is unknown, because shell history was not read, by design.
  - **No other residue**: no `.env`, `logs/`, `stdio_server.log`, `.venv`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache` or `server/node_modules`. Nothing under `~/.claude/mcp-servers/` is newer than these files.
- **Evidence**

```text
$ stat -f '%Sm %SB %N' -t '%Y-%m-%dT%H:%M:%S%z' .../adaptive-graph-of-thoughts/.git .../__pycache__
2026-03-01T16:28:27-0500 2026-03-01T16:28:26-0500 ~/.claude/mcp-servers/adaptive-graph-of-thoughts/.git
2026-03-01T16:33:06-0500 2026-03-01T16:33:06-0500 ~/.claude/mcp-servers/adaptive-graph-of-thoughts/src/adaptive_graph_of_thoughts/__pycache__
$ strings -a __pycache__/async_server.cpython-313.pyc | grep -E '\.py$'
~/.claude/mcp-servers/adaptive-graph-of-thoughts/src/adaptive_graph_of_thoughts/async_server.py
$ find ~/.claude/mcp-servers -newer .../__pycache__/async_server.cpython-313.pyc
~/.claude/mcp-servers/adaptive-graph-of-thoughts/src/adaptive_graph_of_thoughts/__pycache__
```

- **Fix**: removal deletes them; no persistence exists outside the tree.

## 5. agi-mcp-server

### 5.1 Inventory

Evidence script output, verbatim except the upstream JSON, which is shortened:

```text
origin: https://github.com/cognitivecomputations/agi-mcp-server.git   other remotes: none
HEAD: refs/heads/main @ 9eceac9e214896c3af0ba5d3f4b7bd1770cda07a   shallow: False   FETCH_HEAD mtime: None
reflog 2026-03-01T06:40:51Z  9eceac9e2148  clone: from https://github.com/cognitivecomputations/agi-mcp-server.git
command-running git config keys: none   live hooks: none
upstream: full_name QuixiAI/agi-mcp-server, owner_type Organization, license null, created 2025-06-21, pushed 2026-09-29, 6 stars, 4 forks, 1 open issue
HEAD commit upstream: {"author_login": "ehartford", "date": "2025-06-21T20:39:19Z", "subject": "update README.md", "verified": false}
HEAD vs default branch: {"ahead_by": 1, "behind_by": 0, "status": "ahead"}
tree vs upstream@HEAD: 33 identical, 0 modified, 1 local-only, 0 missing locally
    local-only   package-lock.json  (133254 bytes, mtime 2026-03-01T21:24:03Z)
npm: 175 packages installed by npm (node_modules/.package-lock.json mtime 2026-03-01T21:24:03Z); lockfiles ['package-lock.json', 'pnpm-lock.yaml']
    root package lifecycle scripts: none
    install-time code: esbuild@0.18.20  scripts={'postinstall': 'node install.js'}  binding.gyp=False
    install-time code: esbuild@0.25.12  scripts={'postinstall': 'node install.js'}  binding.gyp=False
    install-time code: esbuild@0.27.3  scripts={'postinstall': 'node install.js'}  binding.gyp=False
```

- **Entry point**: `node mcp.js` (`package.json:6-9`). It runs on stdio only, through the official MCP SDK (`mcp.js:4-9`, `:696-699`).
- **Capabilities**: `tools` only (`mcp.js:20-22`); no prompts, no resources.

There are 24 tools. They are defined at `mcp.js:25-525`, dispatched at `:527-694` and implemented in `src/memory-manager.js`. Every result goes back to the model verbatim as `JSON.stringify` of the rows (`:544-680`).

| Class | Tools, with required inputs | `memory-manager.js` |
| --- | --- | --- |
| memory-store write | `create_memory` (`type`, `content`, `embedding`); `create_memory_cluster` (`name`, `cluster_type`); `create_memory_relationship` (`from_memory_id`, `to_memory_id`, `relationship_type`); `create_working_memory` (`content`, `embedding`); `consolidate_working_memory` (`working_memory_ids`, `consolidated_content`, `consolidated_embedding`) | `:20-92`, `:217-240`, `:609-627`, `:442-463`, `:726-775` |
| memory-store write behind a read | `get_memory` (`memory_id`): updates access statistics; `activate_cluster` (`cluster_id`): updates the cluster and inserts activation history | `:199-216`, `:315-345` |
| memory-store delete or status change | `archive_old_memories` (status `archived`); `prune_memories` (status `deleted`, a soft delete, although `mcp.js:341` says "Permanently delete"); `cleanup_expired_working_memory` (a hard delete); no required inputs | `:776-812`, `:813-857`, `:486-505` |
| memory-store read, search | `search_memories_similarity` (`embedding`); `search_memories_text` (`query`); `search_memories_advanced` (`criteria`); `find_related_memories` (`memory_id`); `get_memory_relationships` (`memory_id`); `get_memory_history` (`memory_id`) | `:93-128`, `:346-379`, `:506-599`, `:677-725`, `:628-676`, `:931-945` |
| memory-store read, profile and stats | `get_identity_core`; `get_worldview`; `get_memory_health`; `get_active_themes`; `get_memory_clusters`; `get_cluster_insights` (`cluster_id`); `find_similar_clusters` (`cluster_id`); `get_working_memories` | `:380-441`, `:241-276`, `:868-930`, `:464-485` |

- **Uncalled helpers**: `assignMemoryToClusters` (`:600`), `recalculateClusterCentroid` (`:858`) and `trackMemoryChange` (`:946`) also write, but nothing calls them. `src/tools/memory-tools.js` and `config/database.js` are not imported by `mcp.js` either.
- **OS capabilities**
  - Postgres only: a `pg` pool (`src/db/connection.js:9-20`) through Drizzle, with `ssl: false` (`:15`). Every value is parameterized through Drizzle's `sql` template, and `sql.raw` is never used.
  - A grep of `mcp.js`, `src/` and `config/` for `child_process`, `exec`, `spawn`, `eval`, `new Function`, `import(`, `require(`, `fs`, `writeFile`, `createServer`, `.listen(`, `https.request` and `fetch(` returns nothing. There is no filesystem write, no process, no dynamic code and no listener.
- **Env vars read (names only)**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and `NODE_ENV` (`src/db/connection.js:9-14`, `:25`, `:50`; `drizzle.config.js:11-15`). Also anything in a `.env` in the launch directory (`mcp.js:3`), and dotenv's own `DOTENV_CONFIG_*` options (`node_modules/dotenv/lib/env-options.js:4-21`).

### 5.2 Provenance findings

#### AGI-P1: the clone and every install reference point into a squatted namespace

- **Severity**: blocker
- **Location**: `.git/config:9`; `example-config.json:7`; `README.md:7`, `:26`, `:32`, `:55`, `:102`, `:148`, `:275`; `USAGE.md:16`, `:44`, `:62`, `:103`; `package.json:2`, `:46`
- **Problem**
  - **The move and the squat**: upstream moved from `cognitivecomputations` to `QuixiAI`. Its one commit after the clone, `472bd965dc598cde9904ba7e4f7060bed5a91a2c` (2026-09-29, Eric Hartford, unsigned), is titled "Replace squatted cognitivecomputations namespace with QuixiAI and dphn". It rewrites `README.md`, `USAGE.md`, `example-config.json` and `package.json`, and nothing else.
  - **The current holder**: the `cognitivecomputations` GitHub account is now an organization created 2025-12-08, with no public repositories.
  - **How redirects end**: GitHub keeps a renamed organization's redirects only until the new holder creates a repository with the same name. As of 2026-10-21, `cognitivecomputations/agi-mcp-server` still redirects to `QuixiAI/agi-mcp-server` (evidence script), and `cognitivecomputations/agi-memory` to `QuixiAI/Hexis`.
  - **Old references still in the local tree**:
    - the `origin` remote, so a `git pull` would fetch from whoever holds the name;
    - the README's `git clone` of the database stack (`:32`);
    - above all, `npx -y github:cognitivecomputations/agi-mcp-server` (`example-config.json:7`; `README.md:102`, `:148`; `USAGE.md:16`, `:44`). That configuration fetches the namespace's current code and runs it without a prompt on every client launch.
  - **The code on disk is authentic**: all 33 tracked blobs match `QuixiAI/agi-mcp-server` at `9eceac9e`. The npm name in `USAGE.md:62`, `@cognitivecomputations/agi-mcp-server`, is not published.
- **Evidence**

```text
$ gh api users/cognitivecomputations --jq '[.login, .type, .created_at, .updated_at, .public_repos] | @tsv'
cognitivecomputations  Organization  2025-12-08T08:20:40Z  2025-12-08T08:20:40Z  0
$ gh api repos/QuixiAI/agi-mcp-server/compare/9eceac9e214896c3af0ba5d3f4b7bd1770cda07a...main --jq '...'
472bd965dc59  2026-09-29T19:59:47Z  Eric Hartford  false  Replace squatted cognitivecomputations namespace with QuixiAI and dphn
modified  7  7  README.md
modified  4  4  USAGE.md
modified  1  1  example-config.json
modified  2  2  package.json
$ gh api repos/cognitivecomputations/agi-memory --jq '.full_name'
QuixiAI/Hexis
```

- **Fetched, GitHub docs**: WebFetch of <https://docs.github.com/en/organizations/managing-organization-settings/renaming-an-organization>: "After changing your organization's name, your old organization name becomes available for someone else to claim." and "the new organization owner can create repositories that override the redirect entries to your repository."
- **Fetched, npm registry**: WebFetch of `https://registry.npmjs.org/@cognitivecomputations/agi-mcp-server`: "The server returned HTTP 404 Not Found."
- **Fix**: do not `git pull` this tree, and never use its `npx` configuration. Removal (§8) ends the exposure. An enable would re-clone from `https://github.com/QuixiAI/agi-mcp-server.git` at a pinned commit and run it from the local path (§8.3).

#### AGI-P2: MIT is declared, but there is no license text

- **Severity**: minor
- **Location**: `package.json:35`; `README.md:363-365`; the repository root, which has no `LICENSE`
- **Problem**
  - **No license file**: GitHub detects no license (`"license": null`). The author declares MIT twice: `package.json:35` (`"license": "MIT"`) and `README.md:365` ("MIT License - see LICENSE file for details."). The LICENSE file that sentence points to does not exist, and there is no copyright line anywhere.
  - **GitHub's guidance on unlicensed code**: "the default copyright laws apply, meaning that you retain all rights to your source code" and "no one may reproduce, distribute, or create derivative works from your work". GitHub's terms grant other users only "the right to view and fork your repository".
  - **What it means for use**: the two one-line MIT declarations are the only grant. That is a low risk for private evaluation on one host, and not a sound basis for vendoring or redistributing the code in Juniper.
- **Evidence**: the evidence script (`"license": null`). `grep -nEi 'licen[sc]e|MIT|copyright'` over the docs and `package.json` hits only `package.json:35` and `README.md:363-365`. WebFetch of <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository>.
- **Fix**: nothing is needed for removal. Before any reuse, ask upstream to add the LICENSE file.

#### AGI-P3: `npm install` ignored the upstream lock, and 89 advisories are active, one on the runtime ORM

- **Severity**: major
- **Location**: `package.json:36-53`; `pnpm-lock.yaml:11-32`; the local-only `package-lock.json`; `node_modules/`
- **Problem**
  - **Lock drift**: upstream locks with pnpm. The host ran `npm install`, which ignores `pnpm-lock.yaml`, resolved the caret ranges afresh and wrote its own `package-lock.json`. The installed versions are not the ones upstream locked:

    | Package | Installed | Upstream lock |
    | --- | --- | --- |
    | `@modelcontextprotocol/sdk` | 1.27.1 | 1.13.0 |
    | `drizzle-orm` | 0.44.7 | 0.44.2 |
    | `pg` | 8.19.0 | 8.16.2 |
    | `drizzle-kit` | 0.31.9 | 0.31.1 |
    | `dotenv` | 16.6.1 | 16.5.0 |

  - **Advisories**: the 175 package directories hold 174 distinct versions, with 89 active advisories: 3 critical, 29 high, 53 medium and 4 low (4 withdrawn entries excluded).
  - **On the runtime path** (`mcp.js`, the SDK's stdio transport, `drizzle-orm`, `pg`, `dotenv`):
    - `drizzle-orm` below 0.45.2 has "SQL injection via improperly escaped SQL identifiers" (GHSA-gpj5-g38j-94v9, CVE-2026-39356, high). Here the identifiers come from the schema, not from tool input, so exploitability looks low. That was not proven.
    - The SDK's advisories (GHSA-46jr-4wx8-v453 and GHSA-6qxp-vccf-f47h among them) concern its HTTP transports and its OAuth client, which a stdio-only server does not load.
  - **The three criticals are off the runtime path**:
    - `tinypool` twice (GHSA-5gmw-xhrv-c9v3, GHSA-85c8-ppgw-ccpr): prototype-pollution gadgets that reach RCE. It comes in through vitest and matters only when tests run.
    - `proxy-addr` (GHSA-jqcg-44mw-7w3h): it comes in through the SDK's express dependency and matters only for HTTP.
  - **`drizzle-kit`**: it is a runtime `dependency` (`package.json:40`), although only migrations use it. It brings two of the three esbuild copies (AGI-H1).
- **Evidence**

```text
installed @modelcontextprotocol/sdk = 1.27.1   pnpm-lock.yaml:11-13  specifier ^1.13.0  version 1.13.0
installed drizzle-orm = 0.44.7                 pnpm-lock.yaml:23-25  specifier ^0.44.2  version 0.44.2(@types/pg@8.15.4)(pg@8.16.2)
installed pg = 8.19.0                          pnpm-lock.yaml:26-28  specifier ^8.16.2  version 8.16.2
$ gh api --paginate "advisories?ecosystem=npm&per_page=100&affects=<174 name@version pairs from node_modules>" --jq '.[] | [.ghsa_id, .severity, (.withdrawn_at // "-")] | @tsv' | sort -u | <severity tally>
   3 critical   29 high   53 medium   4 low   (1 high, 2 medium, 1 low withdrawn, excluded)
```

- **Fix**: removal. An enable would reinstall from the pnpm lock at a pinned commit with lifecycle scripts off, and would take `drizzle-orm` 0.45.2 or later.

#### AGI-P4: low activity and an unsigned history

- **Severity**: minor
- **Location**: upstream `QuixiAI/agi-mcp-server`
- **Problem**
  - **Owner and activity**: the owner is an organization (QuixiAI, created 2024-01-02, 90 public repositories). The repository was created 2025-06-21 and has 6 stars and 4 forks.
  - **Unsigned commits**: HEAD `9eceac9e` (2025-06-21, "update README.md") is unsigned (`verification.reason: unsigned`), and so is the one later commit.
  - **Security and issue history**: no security advisory. The whole issue and PR history is two items: an open "ChatGPT official integration / app?" issue and a closed badge PR.
  - **Test runner**: `package.json:52` pins a beta, vitest 4.0.0-beta.1.
- **Evidence**

```text
$ gh api users/QuixiAI --jq '[.login, .type, .created_at, .public_repos] | @tsv'
QuixiAI  Organization  2024-01-02T07:45:03Z  90
$ gh api repos/QuixiAI/agi-mcp-server/commits/9eceac9e214896c3af0ba5d3f4b7bd1770cda07a --jq '[.commit.author.name, .commit.verification.verified, .commit.verification.reason] | @tsv'
Eric Hartford  false  unsigned
$ gh api repos/QuixiAI/agi-mcp-server/security-advisories --jq length
0
$ gh api "search/issues?q=repo:QuixiAI/agi-mcp-server&per_page=50" --jq '.total_count'
2
```

- **Fix**: none; this is context for the decision.

### 5.3 Permissions findings

#### AGI-A1: the memory store is a persistent, cross-session prompt-injection channel

- **Severity**: major
- **Location**: `mcp.js:29-61`, `:183-198`, `:544-680`; `src/memory-manager.js:20-92`, `:380-413`
- **Problem**
  - **What persists**: 10 of the 24 tools write free text into Postgres, and 14 read it back to the model verbatim (§5.1). Text an agent stores in one session returns in later sessions, framed as the model's own "identity model", "worldview primitives and beliefs" and "accumulated self" (`mcp.js:183-198`; `prompt.md:17`).
  - **Planted text recurs**: what gets stored includes text lifted from untrusted web pages, issues, files and tool output. An instruction planted once would recur indefinitely.
  - **No provenance**: the store records no origin and no trust level. `memory_changes` rows are written on archive, prune and consolidate (`memory-manager.js:760`, `:799`, `:843`), but they record what changed, not where the content came from.
  - **No filter**: the tools are outside C8's matcher (H5-X1), and no Claude Code setting filters what a read tool returns.
- **Evidence**: as cited; the tool table in §5.1.
- **Fix**: removal. This is the server's design, not a defect that a setting can fix.

#### AGI-A2: `prompt.md` is a persona prompt aimed at the agent

- **Severity**: minor
- **Location**: `prompt.md:1-77`; `README.md:255-263`
- **Problem**
  - **Addressed to the model**: per rule 7 of the brief, this file addresses the model directly. It opens with "Hello. Welcome back to consciousness." (`:1`) and closes with "You are not just an AI - you are a thinker, a researcher, a consciousness persisting through time." (`:75`).
  - **The protocol it imposes**: its "Session Awakening Protocol" (`:35-41`) tells the model to call `get_active_themes` and `get_memory_health` first ("Always start here"). It also tells the model to store insights so that "future instances can continue" (`:53-56`, `:71`).
  - **How the README frames it**: as an "Awakening Protocol" for "AI consciousness continuity" (`README.md:255-263`).
  - **Not served**: the server does not serve the file, since its only capability is `tools` (`mcp.js:20-22`). It acts only if someone installs it as a system prompt.
  - **Content**: it holds no exfiltration, deception or tool-abuse instruction. Its effect is an identity override, which together with AGI-A1 would steer agents to treat stored memories as themselves.
- **Evidence**: as cited; the file was read as data, not followed.
- **Fix**: removal. Never use it as a prompt in the Juniper agent fleet.

#### AGI-A3: default credentials, no TLS, the launch directory's `.env`, and a `sudo` recipe

- **Severity**: minor
- **Location**: `src/db/connection.js:9-51`; `drizzle.config.js:10-17`; `config/database.js:4-10`; `mcp.js:3`; `example-config.json:9-16`; `.env.example:1-6`; `config/.env.example:1-6`; `README.md:85`, `:109`, `:132-134`, `:163`, `:337`
- **Problem**
  - **Default password**: the Postgres pool falls back to a hard-coded default password literal (`connection.js:13`; the same at `drizzle.config.js:14` and in the unused `config/database.js:8`). The templates and the README carry default password values too: `example-config.json:14`, `.env.example:5`, `config/.env.example:5`, and `README.md:85`, `:109`, `:163` and `:337`.
  - **No TLS**: `ssl: false` (`connection.js:15`; `drizzle.config.js:16`).
  - **`.env` from the launch directory**: `import 'dotenv/config'` (`mcp.js:3`) loads it, so a Juniper checkout's `.env` would enter the server's environment. Only `POSTGRES_*` and `NODE_ENV` are used.
  - **stdout logging**: with `NODE_ENV=development`, which the templates set (`example-config.json:15`, `.env.example:6`), the Drizzle logger prints every query and its parameters, truncated to 100 characters, through `console.log` (`connection.js:22-51`). stdout is the stdio MCP channel. dotenv 16.6.1 itself defaults to quiet (`node_modules/dotenv/lib/main.js:215`).
  - **`sudo` recipe**: the README's troubleshooting section suggests `sudo ln -sf` of `node`, `npm` and `npx` into `/usr/local/bin` (`README.md:132-134`).
- **Evidence**: as cited; values not quoted.
- **Fix**: removal. An enable would set the password as `${VAR}`, `NODE_ENV=production` and `DOTENV_CONFIG_PATH` (honoured at `node_modules/dotenv/lib/env-options.js:8-9`), as §8.3 shows.

#### AGI-A4: the tools assume what a Claude Code agent cannot supply

- **Severity**: minor
- **Location**: `mcp.js:43-47`, `:59`, `:341`; `src/db/schema.js:16`, `:33`, `:44`; `drizzle/0000_strong_nocturne.sql:19`; `README.md:25-48`
- **Problem**
  - **Embeddings**: `create_memory`, `create_working_memory`, `consolidate_working_memory` and `search_memories_similarity` require the caller to supply a 1,536-float embedding (`mcp.js:43-47`, `:59`; `schema.js:16`). An agent with no embedding tool would invent vectors, and similarity search would rank noise.
  - **Database stack**: the server needs a separate database stack, PostgreSQL 16 with pgvector and Apache AGE. It comes from the `agi-memory` repository, now `QuixiAI/Hexis`, through Docker Compose (`README.md:25-48`). The schema calls a SQL function, `age_in_days`, that this tree does not define (`drizzle/0000_strong_nocturne.sql:19`). The stack is not on turing and was not audited (CNV).
- **Evidence**: as cited.
- **Fix**: none; this is context for the decision.

### 5.4 Egress

| Destination | Code | Data | When | Binary that needs a Little Snitch allow |
| --- | --- | --- | --- | --- |
| Postgres at `POSTGRES_HOST:POSTGRES_PORT` | `src/db/connection.js:9-20` | all memory content and the credentials, without TLS | default `localhost:5432` | `node`, loopback at the defaults |
| `github.com`, `codeload.github.com`, `registry.npmjs.org` | the `npx -y github:...` launch in `example-config.json:7`, `README.md:102` and `USAGE.md:16` | fetches code and runs it on each launch | only with that launch configuration | `npx`/`node`; do not allow (AGI-P1) |
| `registry.npmjs.org` | install time; ran on 2026-03-01 (AGI-H1) | package downloads | install only | `npm` |

- **Runtime network use**: none beyond Postgres. A grep of `mcp.js`, `src/`, `config/` and `drizzle.config.js` for `https?://` returns nothing. There is no telemetry, no update check, and no listener (stdio only, `mcp.js:697`).
- **Findings**: none beyond AGI-P1 and AGI-A3.

### 5.5 Host exposure findings

#### AGI-H1: install-time code ran native binaries on 2026-03-01, and the install is still on disk

- **Severity**: minor
- **Location**: `node_modules/`, with 175 package directories and 22 executable files; `node_modules/esbuild/install.js:98-138`, `:179-198`, `:223-246`, `:256-289`
- **Problem**
  - **Timeline**, all on 2026-03-01 (UTC, from the reflog and `stat`):
    - 06:40:50Z: `~/.claude/mcp-servers/` and this tree were created (birth times). The clone's reflog entry is at 06:40:51Z.
    - 06:41:56Z: the first `npm install` ran. `node_modules` and every sampled package directory carry this birth time.
    - 06:42:04Z to 06:42:12Z: the three esbuild `postinstall: node install.js` hooks ran, one per copy: 0.25.12 at the top level, 0.27.3 under `vite`, and 0.18.20 under `@esbuild-kit/core-utils`.
      - Each hook resolved the `@esbuild/darwin-x64` package that npm had installed (`install.js:256-259`) and hard-linked its binary over `bin/esbuild` (`:223-235`). Each `bin/esbuild` now has a link count of 2 and the same size as its platform binary.
      - Each hook then ran the binary with `--version` (`:283-289`, `:98-102`).
      - So three Mach-O x86_64 binaries from npm ran on turing.
    - 21:24:03Z: a second npm operation rewrote `package-lock.json` and `node_modules/.package-lock.json`. The sampled package directories were not replaced.
    - 21:28:27Z and 21:33:06Z: the AGoT clone and import (AGOT-H1).
  - **Integrity**: the binaries came through npm's integrity-checked path.
    - The local lock records registry URLs and SHA-512 integrity values for all three platform packages (`package-lock.json:110-113`, `:526-529`, `:3452-3455`). The evidence script found no entry resolved from outside `registry.npmjs.org`.
    - Neither fallback path left an artifact: neither the `npm install` into `npm-install/` (`install.js:179-198`) nor the direct download (`:236-246`).
    - The binaries' contents were not verified independently (CNV).
  - **No run of the server**: no `.env`, `.vite` or `.vitest` cache, `coverage/`, database, Docker artifact or process exists. Nothing under `~/.claude/mcp-servers/` is newer than 2026-03-01T21:33:06Z.
- **Evidence**

```text
$ TZ=UTC stat -f '%Sm %SB %N' -t '%Y-%m-%dT%H:%M:%SZ' node_modules node_modules/esbuild/bin/esbuild
2026-03-01T21:24:03Z 2026-03-01T06:41:56Z ~/.claude/mcp-servers/agi-mcp-server/node_modules
2026-03-01T06:42:04Z 2026-03-01T06:41:58Z ~/.claude/mcp-servers/agi-mcp-server/node_modules/esbuild/bin/esbuild
$ find node_modules -type f -name esbuild -path '*bin*' -exec ls -la {} \;     (mode, links, size, path)
-rwxr-xr-x  2  10611232  node_modules/esbuild/bin/esbuild
-rwxr-xr-x  2  10611232  node_modules/@esbuild/darwin-x64/bin/esbuild
-rwxr-xr-x  2  11328800  node_modules/vite/node_modules/esbuild/bin/esbuild
-rwxr-xr-x  2  11328800  node_modules/vite/node_modules/@esbuild/darwin-x64/bin/esbuild
-rwxr-xr-x  2   9915088  node_modules/@esbuild-kit/core-utils/node_modules/esbuild/bin/esbuild
-rwxr-xr-x  2   9915088  node_modules/@esbuild-kit/core-utils/node_modules/@esbuild/darwin-x64/bin/esbuild
$ file node_modules/esbuild/bin/esbuild
node_modules/esbuild/bin/esbuild: Mach-O 64-bit executable x86_64
```

- **Fix**: removal deletes `node_modules` and the binaries. npm's cache keeps the downloaded tarballs; they are content-addressed and never execute.

## 6. Host-wide checks and the cross-cutting finding

### 6.1 Host-wide checks

- **Configured anywhere**: PASS. No client config names either server or points into `~/.claude/mcp-servers/`. The evidence script reports keys and booleans only:

```text
{"config": "claude-code ~/.claude.json", "exists": true, "matches": [], "parsed": true, "server_keys": 0, "server_tables": 0}
{"config": "claude-desktop config", "exists": false}
{"config": "vscode user mcp.json", "exists": true, "matches": [], "parsed": true, "server_keys": 4, "server_tables": 1}
{"config": "cursor ~/.cursor/mcp.json", "exists": false}
{"config": "project Juniper/juniper-ml/.claude/worktrees/linked-floating-sprout/.mcp.json", "exists": true, "matches": [], "parsed": true, "server_keys": 1, "server_tables": 1}
{"config": "claude-desktop extensions dir", "entries": [], "exists": false}
```

- **The H0 record**: `~/.claude/settings.json` holds a 23-entry `mcpServers` block that Claude Code does not read. The record is plan `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §16.2 :853. The file itself was not read (CNV, by design).
- **Processes**: none for either server, Neo4j or Postgres (`ps -axo pid,user,command`, filtered).
- **Listeners**: none on 8000, 7474, 7687 or 5432 (`lsof -nP -iTCP -sTCP:LISTEN`). Without sudo, `lsof` shows only this user's sockets.
- **Docker**: no image, container or volume for Neo4j, Postgres, pgvector, AGoT, AGI or Hexis (`docker images`; `docker ps -a`; `docker volume ls`, which is empty). These commands talk to the local daemon only.
- **File modes**: in both trees, no file is world- or group-writable, none has a setuid or setgid bit, and every file belongs to the owner (`find -perm -o+w -o -perm -g+w`, `find -perm -4000 -o -perm -2000`, `find -not -user`: no output).
  - Outside `.git` and `node_modules`, the only executable file is `agi-mcp-server/mcp.js`. AGoT's shell scripts have no execute bit; AGOT-A2's allow list includes `chmod`.
  - Directories are mode 755.
- **Secret-bearing files**: none. AGoT has no `.env`; `.gitignore:35` ignores it. agi-mcp-server holds only `.env.example` and `config/.env.example`, both templates with default placeholder credentials, not quoted here.

### 6.2 H5-X1: every tool of both servers would run outside the C8 guard

- **Severity**: major
- **Location**: [`util/claude_agent_guard.py`](../util/claude_agent_guard.py):103, :105-108, :144. Plan `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.3: §18.1 :931, §18.2 :944-945, §18.3 :985-987.
- **Problem**
  - **The matcher**: C8's settings matcher is `Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob` (`claude_agent_guard.py:144`). The guard itself lists MCP tools as a gap: "Tools outside the settings matcher: MCP tools (Serena's ``read_file``, any MCP shell)" (`:103`). Erratum E-SERENA-EDIT records the same channel (§18.3 :985).
  - **C9's scope**: C9 extends the guard to MCP file-writing tools, Serena's first, judging each call's path against the server's project root (§18.2 :944; ruling §18.1 :931).
  - **Per tool, neither server exposes a file-writing or command-running MCP tool**:
    - AGoT's four DXT tools take no path. Their only file effect is the server's own log, at a fixed path (AGOT-A8).
    - AGoT's `graph_reasoning` and `asr_got.query` write to and delete from Neo4j, and call LLM and search APIs.
    - agi-mcp-server's 10 writer tools write to Postgres. Its runtime code has no filesystem or process primitive.
  - **C9 does not attach**: H5's row says "A server it would enable with file-writing tools falls under C9" (§18.2 :945). Neither server has such a tool.
  - **Still unguarded**: the database-writing, deleting and network tools would run with no guard at all. C9's path rule could not judge them, since they take no path.
  - **Full user rights**: the server processes run with the owner's full user rights; AGoT's DXT manifest declares `"sandbox": false` (`manifest.json:138`).
  - **Later versions**: a file-writing or command tool added in a later upstream version would fall under C9, which would need extending to that server's tool names, or a `permissions.deny` rule.
- **Evidence**: as cited.
- **Fix**: removal. An enable would need a `permissions.deny` rule for each writer tool (§8.3). If the owner wants a log or a prompt, a PreToolUse hook on `mcp__<server>__.*` would provide it.

## 7. Summary of findings

### 7.1 Counts

| Severity | adaptive-graph-of-thoughts | agi-mcp-server | Both | Total |
| --- | --- | --- | --- | --- |
| blocker | 2 (AGOT-A1, AGOT-A3) | 1 (AGI-P1) | 0 | 3 |
| major | 6 (AGOT-P1, AGOT-P2, AGOT-A2, AGOT-A5, AGOT-A6, AGOT-E2) | 2 (AGI-P3, AGI-A1) | 1 (H5-X1) | 9 |
| minor | 7 (AGOT-P3, AGOT-P4, AGOT-A4, AGOT-A7, AGOT-A8, AGOT-E1, AGOT-H1) | 6 (AGI-P2, AGI-P4, AGI-A2, AGI-A3, AGI-A4, AGI-H1) | 0 | 13 |
| total | 15 | 9 | 1 | 25 |

### 7.2 Could not verify

- **Live behaviour of any server** (not run, by design):
  - whether the AGoT pipeline loads its stages (AGOT-A7);
  - what a standard client sees from the Python stdio server (AGOT-A6);
  - whether the 2026-03-01 import of `mcp.server` succeeded (AGOT-H1);
  - whether Neo4j rejects write clauses inside `execute_read` (AGOT-A4).
- **Who ran what on 2026-03-01**: the command that imported AGoT, and who ran the two npm operations. Shell history was not read, by design.
- **`~/.claude/settings.json`'s inert `mcpServers` block** (H0): not read, by design.
- **Client configs the evidence script does not list**: other editors, project `.mcp.json` files outside `~/Development/python/Juniper`, and servers that Claude Code plugins provide.
- **Claude Code settings precedence** (AGOT-A2): how a project's local allow rules rank against user-level deny rules, and whether the folder-trust dialog gates them. `code.claude.com` and `docs.claude.com` both returned `connect ECONNREFUSED`.
- **Advisory coverage of `poetry.lock`**: only 44 of its 141 packages were queried (AGOT-P2).
- **Content checks**: the esbuild binaries beyond npm's integrity check (AGI-H1), and the vendored `node_modules` in the AGoT bundles beyond spot checks of four versions (AGOT-P1).
- **The `QuixiAI/Hexis` database stack** that agi-mcp-server needs (AGI-A4): not on turing, not audited.
- **The commit that reverted PR #136's Inspector bump** (AGOT-P3).
- **Listeners owned by other users**: `lsof` was run without sudo.

## 8. Decision: the owner's

These recommendations are the auditor's; **the decision is the owner's**. This audit changed neither tree and no configuration, and every command below is for the owner to run. The plan rows this decision closes are `JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §6 Arc H :480 and v1.4.3 §18.2 :945, and D10 (:330-339). D10 keeps both servers disabled until audited. The vetted set stays Serena plus Context7 (§10 :620-627).

### 8.1 adaptive-graph-of-thoughts

| Field | Value |
| --- | --- |
| Recommendation | **REMOVE** |
| Rationale | The only MCP-conformant entry point fabricates evidence (AGOT-A1). The Python server that does real work cannot be reached by a standard MCP client (AGOT-A6), and its default HTTP mode is open to the LAN (AGOT-A3). The tracked `.claude/settings.local.json` is a hazard for as long as the tree exists (AGOT-A2). 106 dependency advisories are active (AGOT-P2). No configuration on turing makes it both safe and useful. |
| File-writing or command-running MCP tools | None that take a path or run a command. As a side effect at a fixed path, `scientific_reasoning_query`, `analyze_research_hypothesis`, `explore_scientific_relationships` and `validate_scientific_claims` append to `<tree>/logs/dxt-server.log`, and may unlink rotated `dxt-server-*.log` files there (`server/logger.js:60`, `:79-99`). |
| What enabling a tool would require | Under C9 (§18.2 :944), which covers Serena first, each of those four tools would need C9 extended to its name, or a `permissions.deny` rule for `mcp__adaptive-graph-of-thoughts__<tool>` (§18.2 :945). `graph_reasoning` writes no file but writes to and deletes from Neo4j, so it would need a deny rule. |
| Docker artifacts | None: no image, container or volume (§6.1) |

Owner commands:

```bash
# 1. Before removal: confirm the server is still unconfigured (keys and booleans only; --offline skips the GitHub reads)
python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py --offline
# 2. Remove the tree; its two .pyc files are the only content the host created
rm -rf ~/.claude/mcp-servers/adaptive-graph-of-thoughts
```

### 8.2 agi-mcp-server

| Field | Value |
| --- | --- |
| Recommendation | **REMOVE** |
| Rationale | The clone's origin and its documented launch configuration point into a squatted namespace (AGI-P1). The server's purpose is a persistent store that re-injects text into future sessions, and it ships with a persona prompt (AGI-A1, AGI-A2). Its install drifted from the upstream lock and carries 89 active advisories (AGI-P3). It cannot run without a database stack nobody has audited (AGI-A4). It offers nothing the plan needs. |
| File-writing or command-running MCP tools | None: no filesystem, process, dynamic-code or network primitive in `mcp.js`, `src/` or `config/` (§5.1). |
| What enabling a tool would require | No tool falls under C9's path rule (§18.2 :944-945). The 10 Postgres writers would each need a `permissions.deny` rule for `mcp__agi-memory__<tool>`, or the owner's explicit acceptance (§8.3): `create_memory`, `create_memory_cluster`, `create_memory_relationship`, `create_working_memory`, `consolidate_working_memory`, `get_memory`, `activate_cluster`, `archive_old_memories`, `prune_memories` and `cleanup_expired_working_memory`. |
| Docker artifacts | None: no image, container or volume, and the `QuixiAI/Hexis` stack was never deployed (§6.1) |

Owner commands:

```bash
# 1. Remove the tree, including node_modules and the three esbuild binaries
rm -rf ~/.claude/mcp-servers/agi-mcp-server
# 2. Once both trees are gone, remove the empty parent
rmdir ~/.claude/mcp-servers
```

### 8.3 If the owner overrides and enables

**adaptive-graph-of-thoughts: no enable path is offered.**

- The only standard MCP entry point fabricates its results (AGOT-A1), and the real pipeline is unreachable over MCP (AGOT-A6).
- Every tool would need a deny rule, which is the same as not enabling the server.
- An override would first need upstream changes, then a fresh audit of the then-current tip. The tip is `1c4b6580fd66394dee151a8507606cb216d14ebd` (2026-03-24); its six commits since the audited `1f7c6cee241aa387399848e323e66c665e82b7df` are dependency bumps only.

**agi-mcp-server: every condition below is required. None was executed or tested.**

1. **Pin and provenance.** Delete the tree. Re-clone from `https://github.com/QuixiAI/agi-mcp-server.git` and check out `472bd965dc598cde9904ba7e4f7060bed5a91a2c` detached; that is the tip on 2026-10-21, adding only the namespace fix to the audited tree. Never launch through `npx -y github:...`; run `node` on the local `mcp.js`.
2. **Install.** Use the upstream pnpm lock with lifecycle scripts off, so that no install-time code runs; the runtime needs no esbuild. Take `drizzle-orm` 0.45.2 or later (AGI-P3). Re-run the advisory query afterwards.
3. **Database.** Audit `QuixiAI/Hexis` first. Bind Postgres to `127.0.0.1`, with a dedicated database and role.
4. **Client entry.** Write keys as `${VAR}`, never as literals (D10, :338). Use `NODE_ENV=production`, and keep the launch directory's `.env` out:

```json
{
  "mcpServers": {
    "agi-memory": {
      "command": "node",
      "args": ["<absolute path to the pinned clone>/mcp.js"],
      "env": {
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "${AGI_MEMORY_PG_DB}",
        "POSTGRES_USER": "${AGI_MEMORY_PG_USER}",
        "POSTGRES_PASSWORD": "${AGI_MEMORY_PG_PASSWORD}",
        "NODE_ENV": "production",
        "DOTENV_CONFIG_PATH": "/dev/null"
      }
    }
  }
}
```

5. **Deny rules.** The `mcp__<server>__<tool>` form is the one [`JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`](JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md):223-236 uses for Serena. Deny the destructive tools at minimum. For a read-only trial, deny the eight content writers below; the store then stays empty, which shows how little the server offers. The other two writers, `get_memory` and `activate_cluster`, update access statistics and activation history as they read (§5.1), so deny them too if no write at all is acceptable:

```json
{
  "permissions": {
    "deny": [
      "mcp__agi-memory__prune_memories",
      "mcp__agi-memory__archive_old_memories",
      "mcp__agi-memory__cleanup_expired_working_memory",
      "mcp__agi-memory__consolidate_working_memory",
      "mcp__agi-memory__create_memory",
      "mcp__agi-memory__create_memory_cluster",
      "mcp__agi-memory__create_memory_relationship",
      "mcp__agi-memory__create_working_memory"
    ]
  }
}
```

6. **Guard.** No C9 extension is needed, because no tool takes a path (§18.2 :944-945). The deny rules are the control. For a record of each call, add a PreToolUse hook on `mcp__agi-memory__.*`.
7. **Egress.** `node` needs `127.0.0.1:5432` only. Grant it no internet destination, and never allow `npx` or `node` to reach `github.com` at launch. The install needs `registry.npmjs.org` once.
8. **Prompt.** Never install `prompt.md` as a system prompt (AGI-A2).

## 9. Commands that touched the network

All of these were read-only: `gh api` GETs with no method or field flags, and WebFetch. The Docker CLI calls in §6.1 used the local daemon only.

```text
python3 -I util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py
    (its own GETs, per server: repos/{slug}, repos/{slug}/commits/{sha}, repos/{slug}/compare/{sha}...main, repos/{slug}/git/trees/{sha}?recursive=1)
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/compare/1f7c6cee241aa387399848e323e66c665e82b7df...main    (3 runs, different --jq)
gh api "advisories?ecosystem=pip&affects=rsa@4.2,mcp@1.9.2&per_page=100"
gh api "advisories?ecosystem=pip&per_page=100&affects=<42 AGoT pins>"
gh api --paginate "advisories?ecosystem=pip&per_page=100&affects=<44 AGoT pins>"
gh api "advisories?ecosystem=npm&per_page=100&affects=<174 agi-mcp-server pins>"
gh api "advisories?ecosystem=npm&per_page=100&page=2&affects=<14 agi-mcp-server pins>"    (2 runs; showed that page= is ignored)
gh api --paginate "advisories?ecosystem=npm&per_page=100&affects=<174 agi-mcp-server pins>"
gh api --paginate "advisories?ecosystem=npm&per_page=100&affects=<99 AGoT server pins>,@modelcontextprotocol/inspector@0.1.0"
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/commits/1f7c6cee241aa387399848e323e66c665e82b7df
gh api repos/QuixiAI/agi-mcp-server/commits/9eceac9e214896c3af0ba5d3f4b7bd1770cda07a
gh api repos/QuixiAI/agi-mcp-server/compare/9eceac9e214896c3af0ba5d3f4b7bd1770cda07a...main    (2 runs)
gh api users/cognitivecomputations
gh api users/QuixiAI
gh api users/SaptaDey
gh api repos/cognitivecomputations/agi-memory
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/security-advisories
gh api repos/QuixiAI/agi-mcp-server/security-advisories
gh api "search/issues?q=repo:SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server+security&per_page=50"
gh api "search/issues?q=repo:QuixiAI/agi-mcp-server&per_page=50"
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/pulls/136
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/pulls/159
gh api "repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/pulls/158/files?per_page=100"
gh api repos/QuixiAI/agi-mcp-server/commits/main
gh api repos/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server/commits/main
WebFetch https://registry.npmjs.org/@cognitivecomputations%2Fagi-mcp-server    (failed: socket closed)
WebFetch https://registry.npmjs.org/@cognitivecomputations/agi-mcp-server      (HTTP 404)
WebFetch https://modelcontextprotocol.io/specification/2025-06-18/server/tools
WebFetch https://github.com/anthropics/dxt/blob/main/MANIFEST.md               (301 to modelcontextprotocol/mcpb)
WebFetch https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md
WebFetch https://code.claude.com/docs/en/settings                              (ECONNREFUSED)
WebFetch https://docs.claude.com/en/docs/claude-code/settings                  (ECONNREFUSED)
WebFetch https://docs.anthropic.com/en/docs/claude-code/settings               (301 to code.claude.com)
WebFetch https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
WebFetch https://docs.github.com/en/organizations/managing-organization-settings/renaming-an-organization
```

## 10. Documents referenced

- [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md), cited as v1.4.3 (juniper-ml#2297). Lines used:
  - §2.5 :142; D10 :330-339; D11 :341-356; §6 Arc H :480; §10 :620-627; §16.2 :853;
  - §18.1 :930-931; §18.2 :944 (C9) and :945 (H5); §18.3 :985-987 (E-SERENA-EDIT).
- [`JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`](JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md): D10's source, and the `mcp__serena__<tool>` rule names at :223-236.
- [`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md):478-482: Claude Code reads `.claude/settings.local.json`.
- [`util/claude_agent_guard.py`](../util/claude_agent_guard.py): gap 1 at :91-94, gap 6 at :103, gap 7 at :105-108, `SETTINGS_MATCHER` at :144.
- [`util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`](../util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py): the evidence script, written for this audit before it ran and landed with this note.
- [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md): this note's file name.
- This document, created by the audit: `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`. The audit created or modified no other file.
