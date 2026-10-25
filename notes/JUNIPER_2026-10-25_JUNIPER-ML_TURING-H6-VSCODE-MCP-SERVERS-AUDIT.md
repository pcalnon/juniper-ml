# Turing H6: audit of the four MCP servers in VS Code's user `mcp.json`

- **Project**: Juniper ML Research Platform, juniper-ml, turing host bring-up. The audited configuration sits outside every repository, in VS Code's user profile: `~/Library/Application Support/Code/User/mcp.json`.
- **Author**: Paul Calnon (audit via the Claude Code `auditor` agent on turing)
- **Date**: 2026-10-25
- **Version**: 1.0.0
- **Status**: FINAL. The keep, pin or remove decision for each server is the owner's (§8). The audit changed nothing: no VS Code file, no cache, no server, and no repository file other than this note.
- **Scope**: `huggingface` and `upstash/context7` (http), `microsoft/markitdown` and `oraios/serena` (stdio), plus the VS Code settings and host traces that govern them. Lenses: provenance and pin, arguments, tools, egress, controls and local evidence. Static only: no server, `uvx` or VS Code was started.
- **Plan task**: H6 of [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md) v1.4.5, §18.2 :949. Acceptance: "an `auditor` audit in `notes/` with a keep, pin or remove recommendation per server; the owner decides".
  - Origin: O-5 of [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md) :226.
  - Layout: [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md) (the H5 audit).
- **Evidence script**: [`util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`](../util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py), written for this audit by the launching session and run as `python3 -I util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py` at 2026-10-25T08:35Z. It prints a default-deny projection: env and header values are classified, never printed. The auditor never opened `mcp.json` or `settings.json`.
- **Host**: turing, macOS 15.7.1, Intel i7-8850H, 16 GiB, VS Code 1.108.2 (`CFBundleShortVersionString`), GitHub Copilot Chat 0.36.2 (`~/.vscode/extensions/extensions.json`). The host clock is UTC-5 in March and October and UTC-6 in December; times are UTC unless marked local.

---

## 1. Summary

- **Recommendations** (the owner decides, §8):
  - `oraios/serena`: **REMOVE**, in favour of Claude Code's pinned, project-bound Serena (H4). Alternative: **PIN** to H4's commit with corrected arguments.
  - `microsoft/markitdown`: **REMOVE**. Alternative: **PIN** 0.0.1a8 together with its markitdown.
  - `upstash/context7`: **KEEP**, unchanged; use it only after K13.
  - `huggingface`: **KEEP only re-credentialed**: rotate the token now, then run token-less or with a read-only token behind a password input. Otherwise **REMOVE**.
- **Findings: 19.** 2 blocker, 8 major, 9 minor (§7.1). Each carries a `file:line`, a command and its output, or a fetched URL.
- **The blockers**
  - **SER-P1.** Serena is unpinned, and `main` is now 2.1.1.dev0, whose new-user default is the REPL interface: one tool, `serena_repl`, that runs Python with `exec`. Under REPL the context's tool exclusions do not apply, so the entry's shell exclusion is void, and turing has no `~/.serena/serena_config.yml` to override the default. Only E-H4-WHEEL's cryptography build failure stops it today, and H4's own owner step (building that wheel once) would lift the barrier for this entry too.
  - **HF-P1.** The Hugging Face `Authorization` header is a 44-character literal: a plaintext token at rest. Settings Sync synchronizes this file (H6-X3), so the token also sits in the sync service and on every synced host.
- **No logged start, ever.** No VS Code log on turing records a start of any of the four. Every per-server log is empty, and VS Code's newest log session is 2026-03-26. During it uv began installing `markitdown-mcp` 0.0.1a4 and a Serena dependency, and never finished (§4.2).
- **The second Serena checkout in uv's cache** is v0.1.4 at `0c915bd18d51e2225508b6dccc8ae3bd9c20be1e`, resolved from the unpinned URL on 2026-03-21T19:28:04Z, when no VS Code session was running. It is not what VS Code's entry resolved to (SER-H1).
- **C8 and C9 see none of it.** Copilot agent mode calls these tools, not Claude Code (H6-X1). VS Code's own controls are per-call approval, disabling, autostart and trust, and `"/.*/": true` turns any instruction injected through a tool result into unprompted terminal commands (H6-X2, K13).

## 2. Method, safety and conventions

### 2.1 Method

- **The two VS Code files** were read only through the evidence script. No env, header, URL-query or input value was printed or copied here. Secret storage, `state.vscdb`, the keychain and every token file stayed unread; no credential probe ran.
- **Nothing from the servers ran**: no `uvx`, `npx`, `pip`, `docker`, VS Code or MCP server. `code` is not on `PATH`, and the bundled CLI (`.../Resources/app/bin/code`) launches Electron, so extension versions come from listing `~/.vscode/extensions/` and from `extensions.json`.
- **Source and upstream.** Server source was read from uv's cache (`~/.cache/uv/`) as plain files, and upstream through read-only `gh api` GETs and WebFetch (§9).
- **Logs.** VS Code's log tree was listed by name, size and mtime. Only start, stop and discovered-tools lines were printed, plus three Settings Sync status lines; any line naming Authorization, Bearer, token, key or secret was dropped first.
- **The installed workbench** (`/Applications/Visual Studio Code.app/Contents/Resources/app/out/vs/workbench/workbench.desktop.main.js`) was grepped for setting registrations and command ids, as the commit-signing plan did (its §3 :113).

### 2.2 Severity and verdicts

- **blocker**: as configured, the entry exposes a credential or would give an agent arbitrary code execution as the owner. It must change before VS Code chat next runs on turing.
- **major**: a material risk or defect; keeping the server needs the change stated.
- **minor**: hygiene, accuracy, records, or a low-likelihood issue.
- Verdicts: **PASS** is a verified pass, **FAIL** a verified fail, and **CNV** could not verify, with the reason given.
- IDs: `SER-` Serena, `MKD-` markitdown, `C7-` Context7, `HF-` Hugging Face, `H6-X` all four. Area letters: P provenance and pin, A arguments, T tools, E egress, H host evidence.

### 2.3 Conventions

- **Serena** is cited at three commits: **1.7.0** (`949a27ef`, H4's pin) and **0c915bd1**, from uv's cache at `~/.cache/uv/git-v0/checkouts/42910dfe8296368e/<commit>/`; and **HEAD** (`abb0a0f01b94bc8050086f0fb860077d17730324`, `main` on 2026-10-20), through `gh api`.
- **markitdown** is cited from uv's cache: `markitdown-mcp` 0.0.1a4 at `~/.cache/uv/archive-v0/__a9kk0SOoPsix9OzDcFd/markitdown_mcp/`, and markitdown 0.1.5 at `~/.cache/uv/archive-v0/aD3fmrVNPQKfgtRhGmaLT/markitdown/`.
- **Repository files.** The plan is cited as v1.4.5 (main `899796d2`). `util/claude_agent_guard.py` is cited at 1.1.0 (main `899796d2`) and at 1.2.0, task C9's version (juniper-ml#2322), which was the launching session's uncommitted work when the audit ran.
- **VS Code documentation** is the current online text. Where 1.108.2 differs, the bundle grep decides.

## 3. Checklist

| ID | Item | Pass means | serena | markitdown | context7 | huggingface |
| --- | --- | --- | --- | --- | --- | --- |
| C-P1 | Publisher and source | publisher known, repository identified | PASS: `oraios/serena`, an Organization; signed commits | PASS: `microsoft/markitdown` | PASS: `upstash/context7` | PASS: Hugging Face's hosted server |
| C-P2 | Pin | exact version or full commit (D10 :336) | FAIL (SER-P1) | FAIL: only the wrapper is pinned (MKD-P1) | n/a: remote | n/a: remote |
| C-P3 | Gallery record | current and well-formed | FAIL: names an unrelated PyPI project (SER-A1) | FAIL: stale 0.0.1a4 (MKD-P1) | FAIL: id returns 404 (C7-P1) | n/a: no gallery entry |
| C-A1 | Arguments | each understood, none anomalous | FAIL (SER-A1, SER-A2) | PASS | PASS | PASS |
| C-T1 | Tool inventory | every tool named and classified | PASS (SER-T1) | PASS (MKD-T1) | PASS (C7-E1) | CNV: chosen server-side (HF-T1) |
| C-T2 | Writers and runners | none, or bounded and guarded | FAIL (SER-P1, SER-T1) | FAIL: reads any file (MKD-T1) | PASS: none | CNV: write tools exist; the token's scope decides (HF-T1) |
| C-E1 | Egress | every destination known and minimal | FAIL, minor (SER-E1) | FAIL, minor (MKD-E1) | PASS, with an injection surface (C7-E1) | FAIL, minor (HF-E1) |
| C-E2 | Credentials | referenced, never literal (D10 :338) | PASS: none | PASS: none | PASS: password input | FAIL (HF-P1) |
| C-C1 | Guard coverage | every writer or runner covered | FAIL (H6-X1) | FAIL (H6-X1) | FAIL (H6-X1) | FAIL (H6-X1) |
| C-H1 | What ran on turing | known | PASS: never through VS Code; 0.1.4 once through another client (SER-H1) | PASS: an install began 2026-03-26 and never finished (§4.2) | PASS: no logged start | PASS: no logged start |

## 4. Inventory and host evidence

### 4.1 Inventory

The evidence script's output (2026-10-25T08:35Z), reflowed onto fewer lines, with the inputs and the auto-approve keys summarized:

```text
mcp.json  ~/Library/Application Support/Code/User/mcp.json  (top-level keys: inputs, servers)
server servers.microsoft/markitdown  type stdio  command uvx  args markitdown-mcp==0.0.1a4
  gallery https://api.mcp.github.com/2025-09-15/v0/servers/976a2f68-e16c-4e2b-9709-7133487f8c14  version 1.0.0
server servers.upstash/context7  type http  url https://mcp.context7.com/mcp
  headers CONTEXT7_API_KEY  reference only: ${input:context7_api_key}
  gallery https://api.mcp.github.com/2025-09-15/v0/servers/dcec7705-b81b-4e0f-8615-8032604be7ad  version 1.0.0
server servers.oraios/serena  type stdio  command uvx
  args --from git+https://github.com/oraios/serena serena start-mcp-server serena==latest --context ide-assistant
  gallery https://api.mcp.github.com/2025-09-15/v0/servers/0658e342-7ae7-493a-b378-a324363ee322  version 1.0.0
server servers.huggingface  url https://huggingface.co/mcp  headers Authorization  literal (44 chars)  type http
inputs (21): context7_api_key (password), token (password), e, and 18 without a password flag:
  disableEmbeddingsValidation disabledTools exportCleanupIntervalMs exportTimeoutMs exportsPath httpHost httpPort
  idleTimeoutMs indexCheck logPath loggers maxBytesPerQuery maxDocumentsPerQuery notificationTimeoutMs readOnly
  telemetry transport voyageApiKey
settings chat.mcp.gallery.enabled true
         chat.tools.terminal.autoApprove: 15 keys: "/.*/": true, "sed": true, "xargs": true, 11 fragment keys
         ("output_size", "history", "def.*run\\", ...) and one object-valued key
         ("sleep 3 && curl -s http://localhost:8050/api/health | python -m json.tool")
workspace .vscode/mcp.json under ~/Development/python/Juniper: none
```

No other `chat.mcp.*` or `chat.tools.*` key is set: `chat.mcp.autostart`, `chat.mcp.discovery.enabled`, `chat.tools.global.autoApprove`, `chat.tools.eligibleForAutoApproval` and `chat.tools.terminal.enableAutoApprove` are at their defaults.

### 4.2 Host evidence and timeline

| Time (UTC) | Event | Evidence |
| --- | --- | --- |
| to 2025-12-14T07:42:29Z | VS Code's user-config MCP log channels name only `github` and `microsoft` (markitdown) | log names in sessions `20251107T160415` and `20251214T014222` |
| 2025-12-14T07:43:24Z | the user `mcp.json` is last written | `stat -f %m`, then `date -u -r 1765698204` |
| 2025-12-14T07:43:26Z | channels for `huggingface`, `oraios/serena` and `upstash/context7` appear; `github` never does again | `logs/20251214T014222/window1/` names and mtimes |
| 2026-01-23 to 2026-03-21T18:11:12Z | one long VS Code session; Settings Sync logs "Mcp: No changes found during synchronizing mcp." 412 times | `logs/20260123T184407/userDataSync.log`, counted |
| 2026-03-21T19:27:22Z | uv's cache is created | `~/.cache/uv/CACHEDIR.TAG` birth time |
| 2026-03-21T19:28:04Z | uv resolves the unpinned Serena URL to `0c915bd1` and builds a 0.1.4 environment (19:28:31Z); `~/.serena/memories/global` appears (19:28:34Z) | SER-H1 |
| 2026-03-26T23:04:21Z to about 23:07:41Z | VS Code's newest log session | directory `20260326T180421`; mtime of `main.log` |
| 2026-03-26T23:05:48Z to 23:06:02Z | uv fetches the `markitdown-mcp` index; caches `markitdown-mcp` 0.0.1a4, markitdown 0.1.5, `mcp` 1.8.1 and `pyright` metadata; leaves 13 unpack directories unfinished (`magika`, `onnxruntime`, `pdfminer`, `youtube_transcript_api`, `speech_recognition`, `pypdfium2`, `pyright` and others); completes no environment | birth times under `~/.cache/uv/simple-v20`, `wheels-v6`, `archive-v0` and `.tmp*` |
| 2026-10-21T05:12:45Z | H4 fetches `949a27ef`; the cryptography 50.0.0 sdist is unpacked and no wheel is built (E-H4-WHEEL) | `~/.cache/uv/sdists-v9/pypi/cryptography/50.0.0/`; no `*.whl` |

The newest session's per-server logs (host-local time, UTC-5; size in bytes):

```text
2026-03-26T18:04:32 0 .../logs/20260326T180421/window1/mcpServer.mcp.config.usrlocal.huggingface.log
2026-03-26T18:04:32 0 .../logs/20260326T180421/window1/mcpServer.mcp.config.usrlocal.upstashcontext7.log
2026-03-26T18:04:32 0 .../logs/20260326T180421/window1/mcpServer.mcp.config.usrlocal.oraiosserena.log
2026-03-26T18:04:32 0 .../logs/20260326T180421/window1/mcpServer.mcp.config.usrlocal.microsoftmarkitdown.log
```

- **No logged start, ever.** Each server's log is 0 bytes in every retained session that opened one: markitdown's from the 2025-11-07 session on, the other three from 2025-12-14 on. A started server writes "Starting server", "Connection state: Running" and "Discovered N tools", as GitLens's extension-provided GitKraken server did in 2025-11 ("Discovered 19 tools").
- **The 2026-03-26 install.** `markitdown-mcp==0.0.1a4` is VS Code's exact pin, and something installed it during VS Code's newest session while VS Code logged no start. The launcher is CNV: the Amp extension's log for that session names markitdown and serena on 9 lines each, but holds no start line.
- **Out of scope**: two extension-provided MCP servers (GitLens "GitKraken", Container Tools "Copilot Container Tools") and Amp's own MCP settings, which the inventory does not project. Their tools are equally outside C8.

## 5. Cross-cutting findings

### H6-X1: every tool of all four servers runs outside C8 and C9

- **Severity**: major
- **Location**: [`util/claude_agent_guard.py`](../util/claude_agent_guard.py) 1.1.0 at `899796d2` (matcher :144, gap 6 :103) and 1.2.0, juniper-ml#2322 (:133-134, :145-146); plan §18.2 :945 (C9) and §18.3 :996 (H5-X1).
- **Problem**
  - **No guard sees these calls.** Copilot agent mode calls the tools through VS Code's MCP client. The C8 guard is a Claude Code PreToolUse hook; its 1.1.0 matcher is `Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob`. C9's 1.2.0 covers Serena's edit tools under Claude Code only, and names "VS Code's `mcp.json`" as gap 11. The guard is not installed on turing either: `~/.claude/hooks/` does not exist.
  - **VS Code has no `permissions.deny` equivalent.** Its controls, at turing's settings:
    - **Approval**: "MCP tool invocations require explicit user approval, which you can grant at different scopes" (security page). Saved "always" approvals live in VS Code's state, not read here (CNV). `workbench.action.chat.resetTrustedTools` ("Reset Tool Confirmations") clears them.
    - **Per tool**: "Set a tool to `false` in chat.tools.eligibleForAutoApproval to always require manual approval" (approvals page). 1.108.2 registers the setting; turing does not set it.
    - **Disable**: deselect the tool or server in the tools picker, or disable the server ("A disabled server doesn't start"). This is the closest thing to a deny rule.
    - **Trust**: "Non-workspace sources can use a separate trust decision and might prompt on first start or after a configuration change" (manage page). `workbench.mcp.resetTrust` exists in 1.108.2; the trust state is CNV.
    - **Sandbox**: the documented stdio sandbox (`"sandboxEnabled": true`, macOS and Linux) is absent from every file under 1.108.2's `out/`. And "Tool calls from sandboxed servers are auto-approved".
- **Evidence**: `git grep -n -e "SETTINGS_MATCHER = " ... HEAD -- util/claude_agent_guard.py`, with HEAD at `899796d2`, gives `:103`, `:121` and `:144`. `ls ~/.claude/hooks/` gives "No such file or directory". The workbench grep finds `chat.tools.eligibleForAutoApproval`, `workbench.action.chat.resetTrustedTools` and `workbench.mcp.resetTrust`. `grep -rlE sandboxEnabled .../app/out` prints nothing.
- **Fix**: VS Code-side controls only (§8.5). No guard can reach these calls.

### H6-X2: terminal auto-approval turns injected tool output into unprompted commands

- **Severity**: major
- **Location**: `chat.tools.terminal.autoApprove` in VS Code's user `settings.json` (inventory). [`JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`](JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md) (the signing plan): §3 :112-113, S7 :249, K13 :479.
- **Problem**
  - `"/.*/": true` approves every terminal command the agent proposes. Three of the servers return third-party text: Context7's crawled documentation, Hugging Face Hub and Space output, and any page markitdown fetches. Serena returns repository text.
  - So an instruction planted in any of them can become a terminal command that runs with no prompt, outside every guard. The MCP tool calls still need approval (H6-X1); the terminal commands they prompt do not.
  - VS Code's docs: "Terminal auto-approval is a best-effort convenience, not a security boundary" (approvals page); "malicious instructions embedded in that content can be interpreted as legitimate commands" (security page).
- **Evidence**: the inventory (§4.1). The signing plan §3 :112 records "15 entries, including `"/.*/": true`, `"xargs": true` and accidental fragment keys", with `chat.tools.terminal.enableAutoApprove` unset (default `true`).
- **Fix**: K13 (OWNER): delete `"/.*/"`, `"xargs"` and the fragment keys (signing plan :249, :626-630). Every KEEP or PIN in §8 waits on it.

### H6-X3: Settings Sync carries the user `mcp.json` between hosts

- **Severity**: major
- **Location**: `~/Library/Application Support/Code/logs/20260326T180421/userDataSync.log`; VS Code's "Manage MCP servers" page.
- **Problem**
  - VS Code: "This synchronizes the user-profile `mcp.json`, not workspace `.mcp.json` files". The logs show the `mcp` resource in sync: 412 status lines in the January-to-March session and 3 in the newest.
  - So HF-P1's literal is in the Settings Sync service and on every host that syncs MCP servers. [`JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`](JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md):35-42, written on a Linux host, lists the same four servers, with the Hugging Face entry as `Bearer <HF_TOKEN>`.
  - Edits travel too: a §8 edit made on turing reaches the other hosts, and theirs reach turing.
- **Evidence**: `2026-03-26 18:04:40.388 [info] Mcp: No changes found during synchronizing mcp.` (host-local time; one of the three lines). The 412 lines of the January session all carry that one message.
- **Fix**: first decide whether §8 applies to every synced host. If it is for turing only, untick MCP Servers under "Settings Sync: Configure" before editing. Rotate the token either way (HF-P1).

### H6-X4: autostart at its default, and the gallery on

- **Severity**: minor
- **Location**: the inventory's settings; the workbench's setting registrations.
- **Problem**
  - **Autostart.** `chat.mcp.autostart` is unset, and 1.108.2 registers it with `default:"newAndOutdated"` (experimental): "Start servers that have never run or whose configuration has changed" (manage page). None of the four has a logged start, so the next chat message would start all four, behind any trust prompt.
  - **Gallery.** `chat.mcp.gallery.enabled` is `true`, where 1.108.2's default is `false` (preview). Three of these entries came through the gallery, and its records are stale or malformed (SER-A1, MKD-P1, C7-P1).
  - **Discovery.** `chat.mcp.discovery.enabled` is unset, and 1.108.2 defaults every source to `false`: PASS.
- **Evidence**: the workbench grep gives `[Gie]:{type:"string",...,default:"newAndOutdated",enum:["never","onlyNew","newAndOutdated"],...,tags:["experimental"]` and `[aO]:{type:"boolean",default:!1,tags:["preview"]`, where the bundle binds `Gie` to `chat.mcp.autostart` and `aO` to `chat.mcp.gallery.enabled`.
- **Fix**: `"chat.mcp.autostart": "never"` until the owner has decided, and `"chat.mcp.gallery.enabled": false` unless the gallery is wanted.

### H6-X5: 20 of the 21 inputs belong to no configured server

- **Severity**: minor
- **Location**: the `inputs` array of `mcp.json` (inventory).
- **Problem**
  - Only `context7_api_key` is referenced. `token` (a password input) and `e` match no configured server.
  - The other 18 are the MongoDB MCP server's options: 17 appear by name in the options table of `mongodb-js/mongodb-mcp-server`; `disableEmbeddingsValidation` is not listed there. `voyageApiKey` ("API key for Voyage AI embeddings service") is an API-key input without `"password": true`.
  - Whether any value was ever stored is CNV: secret storage was not read.
- **Evidence**: the inventory; WebFetch of `https://github.com/mongodb-js/mongodb-mcp-server` (§9).
- **Fix**: delete the 20 entries; clear any stored value with `workbench.mcp.removeStoredInput` (present in 1.108.2).

## 6. Per-server findings

### 6.1 `oraios/serena`

#### SER-P1: unpinned, and HEAD's default interface executes Python

- **Severity**: blocker
- **Location**: the inventory args; D10 (plan :336). HEAD: `src/serena/resources/serena_config.template.yml`:10-22, `src/serena/config/serena_config.py`:958-962 and :1026-1065, `src/serena/repl/repl.py`:316-356, `src/serena/repl/api/shell_api.py`:59-87, `pyproject.toml`:7 and :52, `docs/02-usage/070_security.md`.
- **Problem**
  - **No ref.** `--from git+https://github.com/oraios/serena` names no ref, so every fresh resolve runs `main`. D10 requires a pin, for Serena a full 40-hex commit. `main` is now `abb0a0f01b94bc8050086f0fb860077d17730324` (2026-10-20): 2.1.1.dev0, after v2.0.0 (2026-10-13) and v2.1.0 (2026-10-19).
  - **REPL by default.** HEAD's template sets `agent_interface: REPL`: "operations are accessed programmatically via the serena_repl tool, which executes Python code ... the tool inclusion/exclusion settings do not apply" (:14-17, :22). The dataclass default is TOOLS (:958), but "The default for new users is defined in the template file" (:962), and a missing config is generated from the template (:1026-1065). turing has none: `~/.serena/` holds only `memories/global`.
  - **Arbitrary code.** The REPL runs submitted code with `exec(compile(...), namespace)` in a plain dict (repl.py:354-356), so builtins and imports work, and `ShellApi.execute_shell_command` ships alongside (shell_api.py:59-87). Serena's security page: "the submitted code can, in principle, do anything the Serena process can do ... Excluding shell execution, for example, does not prevent the code from achieving the same effect by other means."
  - **So the shell control is void.** The entry's only shell control is `--context ide-assistant`, which maps to `claude-code`, whose `excluded_tools` holds `execute_shell_command`. It has no force at HEAD, and VS Code passes no `--agent-interface`.
  - **What stops it today, and why that will not last.** HEAD pins `cryptography==50.0.0` (pyproject :52), which has no Intel macOS wheel and does not build with turing's Rust 1.71 (E-H4-WHEEL, plan :986-988). uv's cache holds the 50.0.0 sdist from H4's attempt, and no wheel. E-H4-WHEEL's own owner option builds the wheel once, and "A built wheel lives in uv's cache". The next unpinned resolve would then reuse it and start Serena 2.x (an inference; live behaviour is CNV).
- **Evidence**: `gh api repos/oraios/serena/commits/main`; `gh api "repos/oraios/serena/releases?per_page=8"`; the jq-filtered contents GETs (§9). `find ~/.cache/uv/sdists-v9/pypi/cryptography/50.0.0 ~/.cache/uv/archive-v0 -maxdepth 3 ( -name "*.whl" -o -name "cryptography-50*" )` prints nothing.
- **Fix**: remove the entry (§8.1), or pin it to H4's commit. 1.7.0 has no REPL: `grep -rln -i "agent_interface\|serena_repl" .../949a27ef/src/serena` prints nothing.

#### SER-A1: `serena==latest` is a gallery artifact that leaves Serena unbound

- **Severity**: major
- **Location**: the inventory args; gallery record `0658e342-...`. 1.7.0: `src/serena/cli.py`:126-135, :236 and :374; `src/serena/agent.py`:670-675, :770 and :1349-1360. 0c915bd1: `cli.py`:161, `agent.py`:351 and :429. HEAD: `cli.py`:305.
- **Problem**
  - **Origin.** The gallery record gives the package `identifier` "serena" and `version` "latest". Its runtime arguments are `--from`, `git+https://github.com/oraios/serena`, `serena` and `start-mcp-server`; its package arguments are `--context` and `ide-assistant`. VS Code rendered `identifier==version` between the two lists, and uvx passes it on as an argument of `serena`. PyPI's `serena` is an unrelated project ("An AMQP 0-9-1 client using AnyIO", 0.9.1); only `--from` keeps uvx away from it.
  - **Effect.** `start-mcp-server` takes the value as its deprecated positional project argument at all three commits (HEAD's handling beyond the argument was not read). At 1.7.0 and 0c915bd1, `ProjectType` returns a non-directory unchanged, so Serena tries to activate a project named `serena==latest`, and the resulting `ProjectNotFoundError` is logged and swallowed (1.7.0 agent.py:670-675; 0c915bd1 :351).
  - **Result.** With no active project `is_single_project` is false (1.7.0 :770; 0c915bd1 :429), although the context sets `single_project: true`. So `activate_project` and `get_current_config` stay exposed. `activate_project` accepts any directory (:1349-1360) and writes `<dir>/.serena/project.yml` there (serena_config.py:413-466): the agent can bind Serena's edit tools to any path, the home directory included.
- **Evidence**: WebFetch of the gallery record and of `https://pypi.org/pypi/serena/json` (§9); the cited lines.
- **Fix**: drop the argument. A user-level entry cannot bind the workspace either: `${workspaceFolder}` does not resolve there (`microsoft/vscode#245905`, open; Serena's VS Code guide, `docs/02-usage/030_clients.md`:277-279). That is one more reason to prefer H4's per-checkout entry (§8.1).

#### SER-A2: `ide-assistant` is a deprecated alias for the Claude Code context

- **Severity**: minor
- **Location**: `src/serena/config/context_mode.py` at 1.7.0 :235-244, HEAD :236-245 and 0c915bd1 :215-224; the contexts `claude-code.yml` and `vscode.yml`.
- **Problem**: every commit maps `ide-assistant` to `claude-code` with a deprecation warning, and no `ide-assistant.yml` exists. VS Code therefore gets a prompt written for Claude Code ("Read -> FORBIDDEN for discovery", tool-search instructions), not the `vscode` context Serena documents for VS Code (`docs/02-usage/030_clients.md`:277). Both contexts exclude `execute_shell_command`, `create_text_file` and `read_file` under the tool interface (1.7.0 `claude-code.yml`:36-42, `vscode.yml`:14-19).
- **Evidence**: the cited lines; `ls .../contexts/` at both cached commits; `gh api ".../contents/src/serena/resources/config/contexts?ref=abb0a0f0..."`.
- **Fix**: `--context vscode` if the entry is kept.

#### SER-T1: the tools at H4's pin, and what they reach from VS Code

- **Severity**: major
- **Location**: 1.7.0 `src/serena/tools/`: `tools_base.py`:88, :110 and :466; `cmd_tools.py`:11; `file_tools.py`:58, :173, :218 and :451-511; `symbol_tools.py`:585-698; `memory_tools.py`:9, :62, :74 and :94. `src/serena/resources/config/modes/editing.yml`:40-43.
- **Problem**
  - `ToolMarkerCanEdit` (:88) marks the writers, and `ToolMarkerSymbolicEdit` extends it (:110). Under the `claude-code` or `vscode` context, the exposed writers are `replace_content`, `replace_in_files`, `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol` and `safe_delete_symbol`, plus the memory writers `write_memory`, `delete_memory`, `rename_memory` and `edit_memory`.
  - `execute_shell_command` and `create_text_file` are excluded, and the base `editing` mode excludes the optional line tools.
  - From VS Code none of them reaches C8 or C9 (H6-X1). E-SERENA-EDIT's `.git/hooks/` path applies in a primary checkout (plan :990), and with SER-A1's `activate_project` any directory can become the project root.
- **Evidence**: `grep -rn "^class .*Tool" .../949a27ef/src/serena/tools/`.
- **Fix**: remove the entry; or pin it (§8.1), keep per-call approval for every writer, and set each writer to `false` in `chat.tools.eligibleForAutoApproval`.

#### SER-E1: a usage report and a dashboard on every start

- **Severity**: minor
- **Location**: 1.7.0 `src/serena/agent.py`:722-737; HEAD `agent.py`:752-765; 1.7.0 `src/serena/resources/serena_config.template.yml`:38, :49 and :70, and `src/serena/dashboard.py`:203; [`util/mcp_setup.bash`](../util/mcp_setup.bash):202.
- **Problem**
  - **Usage report.** At each start 1.7.0 and HEAD send the OS, the dashboard flag, the version, the backend and the context name to `https://oraios-software.de/serena_usage.php`, unless `SERENA_USAGE_REPORTING=false` (or `CI` or `GITHUB_ACTIONS`) is set. 0c915bd1 has no such call.
  - **Dashboard.** With no `--open-web-dashboard False`, the template's `web_dashboard: True` and `web_dashboard_open_on_launch: True` open a dashboard at every start, served on `127.0.0.1`.
  - **Other egress.** The install fetches from `github.com` and PyPI. Serena downloads some language servers on demand (security page, "Supply Chain Security"); juniper-ml's [`.serena/project.yml`](../.serena/project.yml):5-6 lists only `python`, whose server is a pip dependency.
  - **H4 too.** H4's entry has `"env": {}`, so Claude Code's Serena sends the report as well; that is outside H6, for H4's owner.
- **Evidence**: the cited lines.
- **Fix**: `"env": {"SERENA_USAGE_REPORTING": "false"}` and `--open-web-dashboard False` on any kept entry, H4's included.

#### SER-H1: the `0c915bd1` checkout is v0.1.4, resolved unpinned by another client

- **Severity**: minor
- **Location**: `~/.cache/uv/git-v0/checkouts/42910dfe8296368e/0c915bd1/` (`.git/refs/heads/master`, `.git/logs/HEAD`, `pyproject.toml`:7); `~/.cache/uv/git-v0/db/42910dfe8296368e/.git/refs/commit/`; `~/.cache/uv/environments-v2/8cf043bef111b8b9`, which links to `~/.cache/uv/archive-v0/MeJJuCKV6OyxfIqjbvRq3/`.
- **Problem**
  - **What it is.** `0c915bd18d51e2225508b6dccc8ae3bd9c20be1e`: "Merge pull request #1183 ...", committed 2026-03-17T12:50:25Z with a verified signature; version 0.1.4.
  - **When.** uv recorded `reset: moving to 0c915bd1...` at epoch 1774121284 (2026-03-21T19:28:04Z), 42 seconds after the cache was created. Its environment holds `serena_agent-0.1.4`, whose `direct_url.json` names `https://github.com/oraios/serena` with no ref and commit `0c915bd1`, on JuniperPython's CPython 3.13.7. `~/.serena/memories/global` appeared at 19:28:34Z, so that build started.
  - **Not VS Code's.** No VS Code session ran then: the previous one ended by 18:11:12Z and the next began 2026-03-26T23:04:21Z. VS Code's Serena log is empty in every retained session. The likeliest client is Claude Code, whose 2026-03-09 MCP plan registers the same unpinned `uvx --from git+https://github.com/oraios/serena` (:107-111); that attribution is CNV.
  - **At that commit**, `claude-code.yml` also excludes `execute_shell_command` (:11-16), and the dependencies are ranges, not pins (`pyright>=1.1.396,<2`, pyproject :18).
- **Evidence**: the cited files; `gh api repos/oraios/serena/commits/0c915bd18d51e2225508b6dccc8ae3bd9c20be1e`.
- **Fix**: none needed; it is inert. Leave uv's cache alone, or remove entries reversibly.

### 6.2 `microsoft/markitdown`

#### MKD-P1: the pin covers only the wrapper

- **Severity**: major
- **Location**: the inventory args; PyPI `markitdown-mcp`; gallery record `976a2f68-...`.
- **Problem**
  - **Provenance and age.** The publisher is Microsoft (`microsoft/markitdown`, MIT; a PyPI author email at microsoft.com). `markitdown-mcp==0.0.1a4` is a pre-release of 2025-05-23; the current one is 0.0.1a8 (2026-10-21). The gallery record still names 0.0.1a4 (`is_latest`: true, published 2025-09-09).
  - **Floating dependencies.** 0.0.1a4 requires `markitdown[all]<0.2.0,>=0.1.1` and `mcp~=1.8.0`, so markitdown and its whole tree are unpinned. On 2026-03-26 uv resolved markitdown 0.1.5 and `mcp` 1.8.1.
  - **Advisories.** Six are active against `mcp` 1.8.1: five high (CVE-2026-59950, CVE-2026-52869, CVE-2025-66416, CVE-2025-53366, CVE-2025-53365) and one medium (CVE-2026-59951). All but CVE-2025-53366 concern HTTP transports, which this stdio entry does not use. None is active against markitdown 0.1.5 or `markitdown-mcp` 0.0.1a4.
- **Evidence**: WebFetch of `https://pypi.org/pypi/markitdown-mcp/json` and `https://pypi.org/pypi/markitdown-mcp/0.0.1a4/json`; `gh api "advisories?ecosystem=pip&per_page=100&affects=mcp@1.8.1,markitdown@0.1.5,markitdown-mcp@0.0.1a4"`; uv cache birth times (§4.2).
- **Fix**: remove the entry; or pin 0.0.1a8 with an exact markitdown, and re-run the advisory query.

#### MKD-T1: one tool that reads any file and fetches any URL

- **Severity**: major
- **Location**: `markitdown_mcp/__main__.py`:19-22 and :113-114; `markitdown/_markitdown.py`:154-176, :419-431 and :451-460; `markitdown/converters/_exiftool.py`:22-42.
- **Problem**
  - **One tool.** `convert_to_markdown(uri)` is `MarkItDown().convert_uri(uri).markdown`. It writes no file and opens no listener (stdio, :113-114).
  - **Any file.** A `file:` URI goes to `convert_local(path)` with no path restriction (:419-431). So the tool returns to the model any file the owner can read: `~/.ssh`, `~/.gnupg`, `~/.config/gh/`, or VS Code's own `mcp.json` with HF-P1's token. D11 denies Claude Code that class for `~/.ssh` and `~/.gnupg` (plan :348).
  - **Any URL.** `http:` and `https:` get a plain `requests` GET, loopback and LAN included (:451-460). VS Code's own fetch tool uses "a two-step approval flow" (security page); this tool has only the per-call MCP approval.
  - **A subprocess.** It runs `exiftool` when one sits in `/usr/local/bin` or another standard directory (:154-176; `_exiftool.py`:22-42). turing has none (`which -a exiftool` exits 1), so that path is inert.
  - **Upstream**: "The server does not support authentication, and runs with the privileges if the user running it."
- **Evidence**: the cited lines, read from uv's cache.
- **Fix**: remove the entry. If it is kept: per-call approval, `false` in `chat.tools.eligibleForAutoApproval`, and K13 first.

#### MKD-E1: egress follows the URI

- **Severity**: minor
- **Location**: as MKD-T1, plus `converters/_transcribe_audio.py`:48 and `converters/_youtube_converter.py`:148.
- **Problem**: egress goes wherever the model's URL points. An audio file goes to Google's speech recognizer (`recognize_google`), and a YouTube URL to YouTube's transcript service. The first run fetches the dependency tree from PyPI. The grep found no credential and no telemetry.
- **Evidence**: the cited lines.
- **Fix**: as MKD-T1.

### 6.3 `upstash/context7`

#### C7-P1: a sound remote whose gallery record has moved

- **Severity**: minor
- **Location**: the inventory; gallery record `dcec7705-...`; the official registry's `io.github.upstash/context7`.
- **Problem**
  - `https://mcp.context7.com/mcp` is the remote of the official registry's current record, `io.github.upstash/context7` 4.4.4 (latest, 2026-10-19; repository `upstash/context7`, MIT). A remote cannot be pinned: Upstash runs it, and its "API backend, parsing engine, and crawling engine — are private" (README).
  - The gallery id recorded in the entry now returns HTTP 404.
  - The registry declares an `Authorization` header (`isSecret`; it accepts a `Bearer`-prefixed key or the raw key), and the README says to pass the key "via the `Authorization: Bearer YOUR_API_KEY` header". The entry sends `CONTEXT7_API_KEY`. Whether that header still authenticates, or the server falls back to its keyless rate limit, is CNV.
- **Evidence**: WebFetch of the gallery URL (404), of `https://registry.modelcontextprotocol.io/v0/servers?search=context7` and of `https://github.com/upstash/context7`.
- **Fix**: optional. Re-add the server from the current registry record, or, after a check, rename the header to `Authorization` with the value `Bearer ${input:context7_api_key}`. Either stays a reference, never a literal.

#### C7-E1: read-only tools; the query leaves the host

- **Severity**: minor
- **Location**: the Context7 README.
- **Problem**
  - Two tools, `resolve-library-id(query, libraryName)` and `query-docs(libraryId, query, language)`. Neither writes, runs or reads anything on the host.
  - Each sends "The user's question or task" (`query`) to Upstash with the API key, so project detail can leave the host. The responses are documentation from a private crawler: third-party text that feeds H6-X2.
  - The key is a password input, which VS Code keeps in its "secure credentials store" (security page): D10's reference-not-literal rule passes (plan :338). Query retention is CNV: the README is silent, and `https://context7.com/privacy` timed out.
- **Evidence**: the README quotes (§9).
- **Fix**: none beyond K13. D10 already vets Context7, at user scope for Claude Code (plan §10 :625).

### 6.4 `huggingface`

#### HF-P1: a plaintext token at rest, and synced

- **Severity**: blocker
- **Location**: `servers.huggingface.headers.Authorization` in `mcp.json` (inventory: "literal (44 chars)"); D10 (plan :338).
- **Problem**
  - **A literal.** The header value is a literal, not a `${input:...}` reference. 44 characters fits the word `Bearer`, a space and a 37-character `hf_` user token, the shape of Hugging Face's own VS Code snippet (`"Authorization": "Bearer <YOUR_HF_TOKEN>"`). That reading is an inference; the value was not read (CNV).
  - **VS Code's guidance**: "Do not commit tokens, passwords, or populated authentication headers", and "A personal configuration file is not a secret store" (configuration reference).
  - **Who can read it.** The file is mode 0644 inside the 0700 directory `~/Library/Application Support/Code`, so other local users cannot read it. Every process running as the owner can, including markitdown's `file:` tool (MKD-T1) and any auto-approved terminal command (H6-X2), and Settings Sync copies it off the host (H6-X3).
  - **Provenance.** There is no gallery entry, and the key order (`url`, `headers`, `type`) fits a pasted snippet.
- **Evidence**: the inventory; `stat -f "%Sp"` on the file and its parent directories; WebFetch of `https://github.com/huggingface/hf-mcp-server` and of VS Code's MCP configuration reference.
- **Fix**: rotate the token at huggingface.co (OWNER), whatever else is chosen, since it has sat in plaintext and in sync. Then go token-less, or use a read-only token through a password input (§8.4).

#### HF-T1: the tool set is chosen server-side, and only the token bounds it

- **Severity**: major
- **Location**: the Hugging Face MCP documentation and the server's README.
- **Problem**
  - **Server-side choice.** The built-in `hf_fs` "lets your assistant efficiently navigate the Hub". Further tools are chosen per account at `https://huggingface.co/settings/mcp`: "Contribute Repos" ("Create and write files to those created repositories"), "Sandboxes", "Run and Manage Jobs" ("Run, monitor, and schedule jobs on Hugging Face infrastructure"), community Gradio Spaces, and "Dynamic Spaces" ("discover and use MCP-compatible Spaces on-the-fly").
  - **Only the token bounds it.** The README: "These settings control which deployed tools are advertised, not whether a direct `tools/call` to a known tool may execute", and "Repository creation, Jobs, dynamic Space, and sandbox tools require Hugging Face authentication". So the token's scope is the boundary, not the settings page.
  - The token's scope and the account's settings are CNV: no credential probe ran and no login happened.
- **Evidence**: WebFetch of `https://huggingface.co/docs/hub/en/hf-mcp-server` and of the README (§9).
- **Fix**: go token-less, since "token-less requests continue with the anonymous tool set"; or use a fine-grained read-only token. In the account's settings, turn off Dynamic Spaces and the write and Jobs tools.

#### HF-E1: egress to the Hub and to any Space called

- **Severity**: minor
- **Location**: as HF-T1.
- **Problem**: every request goes to `huggingface.co` with the token. A Space call sends its tool arguments to third-party code on Spaces, whose output returns to the model (H6-X2). Hugging Face states some usage logging ("historical product-usage logging", README); its full retention is CNV.
- **Evidence**: as HF-T1.
- **Fix**: as HF-T1.

## 7. Summary of findings

### 7.1 Counts

| Severity | serena | markitdown | context7 | huggingface | all four | Total |
| --- | --- | --- | --- | --- | --- | --- |
| blocker | 1 (SER-P1) | 0 | 0 | 1 (HF-P1) | 0 | 2 |
| major | 2 (SER-A1, SER-T1) | 2 (MKD-P1, MKD-T1) | 0 | 1 (HF-T1) | 3 (H6-X1, H6-X2, H6-X3) | 8 |
| minor | 3 (SER-A2, SER-E1, SER-H1) | 1 (MKD-E1) | 2 (C7-P1, C7-E1) | 1 (HF-E1) | 2 (H6-X4, H6-X5) | 9 |
| total | 6 | 3 | 2 | 3 | 5 | 19 |

### 7.2 Could not verify

- **Live behaviour** (nothing ran): what each server exposes when started; whether Serena 2.x starts on turing once cryptography 50.0.0 is built; whether Context7 still accepts `CONTEXT7_API_KEY`; how HEAD's agent handles the stray positional.
- **VS Code state and secrets** (not read, by rule): saved tool approvals, trust decisions and stored input values; the Hugging Face token's value and scope.
- **The 2026-03-26 launcher.** Something installed `markitdown-mcp` 0.0.1a4 and pyright during VS Code's newest session while every VS Code MCP log stayed empty. VS Code's autostart (H6-X4) and the Amp extension are the candidates.
- **Which client built 0c915bd1** (SER-H1): Claude Code is the likeliest.
- **Amp**: whether the Amp extension uses VS Code's MCP servers, and what its own MCP settings hold. The inventory projects only `chat.mcp.*` and `chat.tools.*`.
- **Upstream policies**: Context7's query retention (its privacy page timed out) and the full terms of Hugging Face's logging. Serena's docs site (`oraios.github.io`) also timed out, so its text was read from the repository at HEAD.
- **Version gaps.** The current VS Code docs describe a newer release than 1.108.2. The stdio sandbox is absent from 1.108.2, and 1.108.2 does not read a workspace-root `.mcp.json`: the bundle has no `.mcp.json` string and no `workspaceRootConfig` setting. After an update, check whether VS Code starts reading H4's per-checkout `.mcp.json` files.

## 8. Decision: the owner's

These recommendations are the auditor's; **the decision is the owner's**. The audit changed no configuration, and every step below is the owner's. Two rules apply to all of them:

- **Order.** The removals and the settings changes need nothing first. Every KEEP or PIN waits on K13 (H6-X2).
- **Scope.** First decide whether the changes are for every synced host (H6-X3).

| Server | Recommendation | Exact change (owner) | Needs K13 |
| --- | --- | --- | --- |
| `oraios/serena` | **REMOVE**; Claude Code's Serena (H4) stays the vetted one | delete `servers["oraios/serena"]` | no. The PIN alternative (§8.1) does, and needs E-H4-WHEEL first |
| `microsoft/markitdown` | **REMOVE** | delete `servers["microsoft/markitdown"]` | no. The PIN alternative does |
| `upstash/context7` | **KEEP** | none; optionally refresh the header (C7-P1) | yes, before use |
| `huggingface` | **KEEP, re-credentialed**; otherwise **REMOVE** | rotate the token, then delete the `headers` block (token-less) or reference a new read-only token (§8.4) | yes, before use |
| settings | autostart off; gallery off | `"chat.mcp.autostart": "never"` and `"chat.mcp.gallery.enabled": false` | no |
| inputs | prune | delete the 20 unreferenced inputs (H6-X5); run `workbench.mcp.removeStoredInput` for any stored value | no |

### 8.1 Serena

**REMOVE.** H4 already gives Claude Code a pinned, project-bound Serena: v1.7.0 at `949a27ef1e5fda1a6e7b561e777bcece345c6ffd` ([`conf/hosts/turing/mcp.json`](../conf/hosts/turing/mcp.json):4-8). Its shell tool is excluded twice, by the context and by `.serena/project.yml`:25-26, and its edit tools are the ones C9 covers. A VS Code copy would duplicate it outside every guard, and a user-level entry cannot bind the workspace (SER-A1).

**PIN, if the owner wants Serena in Copilot**: H4's commit and the `vscode` context, with no stray positional, no dashboard tab and no usage report. It builds only once E-H4-WHEEL is resolved, and `activate_project` stays exposed, since a user-level entry starts with no project:

```json
"oraios/serena": {
  "type": "stdio",
  "command": "uvx",
  "args": ["--from", "git+https://github.com/oraios/serena@949a27ef1e5fda1a6e7b561e777bcece345c6ffd",
           "serena", "start-mcp-server", "--context", "vscode", "--open-web-dashboard", "False"],
  "env": {"SERENA_USAGE_REPORTING": "false"}
}
```

Never move this entry to 2.x without `--agent-interface tools` (SER-P1).

### 8.2 markitdown

**REMOVE.** It has no role in the plan, and its one tool reads any file the owner can read and fetches any URL, outside every guard (MKD-T1). The `markitdown` CLI, run from an audited and pinned environment, covers occasional conversions without exposing the agent. **PIN alternative**: `markitdown-mcp==0.0.1a8` with an exact `markitdown[all]` version and a fresh advisory query (MKD-P1); per-call approval for its tool; K13 first.

### 8.3 Context7

**KEEP.** D10 vets it (plan §10 :625), the entry already references its key through a password input, and its tools neither write nor execute. Use it only after K13, because its output is third-party text (C7-E1, H6-X2).

### 8.4 Hugging Face

**KEEP, re-credentialed.** First rotate the token at huggingface.co, because it has sat in plaintext on turing and in Settings Sync (HF-P1). Then choose one of two entries. Token-less is recommended, since the anonymous tool set has no repository, Jobs, dynamic Space or sandbox tools (HF-T1):

```json
"huggingface": {"type": "http", "url": "https://huggingface.co/mcp"}
```

Or a new fine-grained read-only token behind a password input, with `{"id": "hf_token", "type": "promptString", "description": "Hugging Face read-only token", "password": true}` added to `inputs`:

```json
"huggingface": {"type": "http", "url": "https://huggingface.co/mcp",
                "headers": {"Authorization": "Bearer ${input:hf_token}"}}
```

Either way, turn off Dynamic Spaces and the write and Jobs tools at `https://huggingface.co/settings/mcp`. **REMOVE** the server if the owner does not use it.

### 8.5 VS Code controls, whatever is kept

- Run "Chat: Reset Tool Confirmations" (`workbench.action.chat.resetTrustedTools`) and the `workbench.mcp.resetTrust` command, so that every kept server and tool asks again.
- Never enable `chat.tools.global.autoApprove` (signing plan :263).
- Set each kept writer tool to `false` in `chat.tools.eligibleForAutoApproval`; the key format is CNV, so check it in the Settings UI.
- A later VS Code brings the stdio sandbox, which auto-approves sandboxed tool calls. Give any sandboxed server a tight `filesystem` and `network` set.

## 9. Commands that touched the network

All read-only: `gh api` GETs with no method or field flags, and WebFetch.

```text
gh api repos/oraios/serena ; repos/oraios/serena/commits/0c915bd18d51e2225508b6dccc8ae3bd9c20be1e ; repos/oraios/serena/commits/main
gh api "repos/oraios/serena/releases?per_page=8" ; "repos/oraios/serena/git/trees/abb0a0f01b94bc8050086f0fb860077d17730324?recursive=1" (2 runs)
gh api [-H "Accept: application/vnd.github.raw"] "repos/oraios/serena/contents/<path>?ref=abb0a0f01b94bc8050086f0fb860077d17730324", <path> =
    src/serena/resources/config/contexts/ and its claude-code.yml, src/serena/config/context_mode.py, src/serena/cli.py,
    src/serena/resources/serena_config.template.yml, src/serena/config/serena_config.py, src/serena/repl/repl.py,
    src/serena/repl/api/shell_api.py, src/serena/agent.py, pyproject.toml, docs/02-usage/030_clients.md, docs/02-usage/070_security.md
gh api repos/microsoft/vscode/issues/245905 ; "advisories?ecosystem=pip&per_page=100&affects=mcp@1.8.1,markitdown@0.1.5,markitdown-mcp@0.0.1a4"
WebFetch https://pypi.org/pypi/markitdown-mcp/json ; https://pypi.org/pypi/markitdown-mcp/0.0.1a4/json ; https://pypi.org/pypi/serena/json
WebFetch https://api.mcp.github.com/2025-09-15/v0/servers/{976a2f68-...,0658e342-...,dcec7705-... (HTTP 404)} ; .../v0/servers?search=context7 (first 100,000 chars)
WebFetch https://registry.modelcontextprotocol.io/v0/servers?search=context7 ; https://github.com/upstash/context7 ; https://context7.com/privacy (timed out)
WebFetch https://huggingface.co/docs/hub/en/hf-mcp-server ; https://huggingface.co/changelog/hf-mcp-server ; https://github.com/huggingface/hf-mcp-server
WebFetch https://github.com/mongodb-js/mongodb-mcp-server ; https://oraios.github.io/serena/02-usage/030_clients.html (timed out)
WebFetch https://code.visualstudio.com/docs/copilot/customization/mcp-servers ; .../docs/copilot/security ; .../docs/agents/reference/mcp-configuration
WebFetch https://code.visualstudio.com/docs/agents/run/manage-mcp-servers ; .../docs/agents/run/approvals ; .../docs/agents/run/tools
```

## 10. Documents referenced

- [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md), v1.4.5: D10 :330-339; D11 :348; §10 :625; §18.1 :931-932; §18.2 :944 (H4), :945 (C9) and :949 (H6); §18.3 :986-988 (E-H4-WHEEL), :989-991 (E-SERENA-EDIT) and :996 (H5-X1).
- [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md): §4.2 :163, RR-13 :213, O-5 :226.
- [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md): this note's layout; H5-X1 in §6.2 :758-774.
- [`JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`](JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md): §3 :106 and :112-113; S7 :249-263; K13 :479 and :626-630.
- [`JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`](JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md): :35-42 and :107-111.
- Configuration and tools: [`conf/hosts/turing/mcp.json`](../conf/hosts/turing/mcp.json):4-8; [`util/mcp_setup.bash`](../util/mcp_setup.bash):202; [`.serena/project.yml`](../.serena/project.yml):5-6 and :25-26; [`util/claude_agent_guard.py`](../util/claude_agent_guard.py) 1.1.0 at `899796d2` :103 and :144, and 1.2.0 (juniper-ml#2322) :133-134 and :145-146.
- [`util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py`](../util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py): the evidence script.
- [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md): this note's file name.
- This document, created by the audit: `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md`. The audit created or modified no other file.
