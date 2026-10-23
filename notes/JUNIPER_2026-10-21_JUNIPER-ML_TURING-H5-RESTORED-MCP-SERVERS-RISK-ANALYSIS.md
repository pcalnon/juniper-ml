# Turing H5: risk analysis of the restored MCP-server trees

- **Project**: Juniper ML Research Platform, juniper-ml, turing host bring-up. The analysed trees sit outside every repository, in `~/.claude/mcp-servers/`.
- **Author**: Paul Calnon (analysis via Claude Code on turing, the "mac dev" session)
- **Date**: 2026-10-21
- **Version**: 1.0.0
- **Status**: VALIDATED. One round, three independent reviewers, each ACCEPT-WITH-CHANGES with no blocker. All findings were applied or dispositioned (§9).
- **Scope**: the two MCP-server trees as restored on 2026-10-21 after their removal, and every host surface that could activate them. It covers security risks and every other issue the restored state carries: operational, records, supply chain and backup.
- **Builds on**: [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md) (the H5 audit, juniper-ml#2300). Its finding IDs (AGOT-*, AGI-*, H5-X1) are cited, not repeated.
  - This register's risk IDs are `RR-n`. The prefix keeps them apart from the signing plan's `R-S` test IDs, such as the "rs9" in a handoff file name.
- **Plan task**: H5 of [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md). In v1.4.4, §18.2's H5 row says the owner's decision is pending, and §18.3 carries erratum E-H5.
- **Evidence**, all in `reports/2026-10-21_turing-h5-restore/` (§10):
  - [`util/ad-hoc/2026-10-21_turing_h5_restore_check.py`](../util/ad-hoc/2026-10-21_turing_h5_restore_check.py), read-only, with its output in `restore-check.json`;
  - the March baselines;
  - the restore's npm debug logs.

  The check reuses the provenance functions of the H5 evidence script, [`util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`](../util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py).
- **Host**: turing, macOS 15.7.1, Intel i7-8850H, 16 GiB.

---

## 1. Summary

- **What happened.** The owner chose REMOVE after the H5 audit, and the agent deleted both trees and their parent. The owner then asked to reconsider, and the trees were restored.
  - The source came back by `git clone --revision` at the audited commits.
  - agi-mcp-server's npm install was rebuilt to its March state: offline, from npm's cache as the March install left it, with install scripts off (§2, §3).
- **Parity.** The restored state matches the pre-removal state wherever that is safe and reproducible (§3.2, §4).
  - Every tracked file of both trees matches upstream at the audited commit: 305 of 305, and 33 of 33. A reviewer recomputed both root tree hashes, so the trees are bit-identical, modes included.
  - `package-lock.json` holds exactly the March lockfile's 270 package@version pairs.
  - `node_modules` holds exactly the March install's 174 (175 package directories).
- **Deliberate deviations:**
  - agi-mcp-server's `origin` is now `QuixiAI`, not the squatted name;
  - both trees are on a detached HEAD at the audited commit;
  - no install-time code ran;
  - the two March `.pyc` files and a stray `fsevents` package were not kept.
- **Risk today: dormant.** Neither server is configured in any MCP client config checked. No process runs from or holds a file in either tree. Nothing listens on their ports. Claude Code 2.1.306 refers to no host path named `mcp-servers`. No Claude Code session has ever run in either tree (§4).
- **The triggers that matter** (§5; each rated Medium):
  - **RR-1:** a Claude Code session opened in the adaptive-graph-of-thoughts tree. Its tracked `.claude/settings.local.json` pre-approves `python3`, `node`, `npx`, `rm` and `claude mcp add` (AGOT-A2).
  - **RR-13:** an IDE agent (VS Code, Amp, Cursor) set loose on a tree. VS Code here auto-approves every terminal command.
  - **RR-2, which corrects AGOT-P1:** opening a `.dxt` bundle. **Claude Desktop is installed** and bound to `.dxt`, though never launched.
  - **RR-3 and RR-5:** enabling either server.
  - **RR-6:** fetching or pulling upstream code. The detached HEAD is **not** a pull barrier.
  - **RR-10:** an agent registering a server through one of several MCP-registration paths that no guard rule covers.
- **Compounding host factors, not caused by the trees:**
  - application firewall off and SIP in a custom configuration (G-SEC);
  - the C8 guard not installed;
  - IDE auto-approval (K13 pending);
  - no backup today, while plan task C0 would back the trees up (RR-11, O-8).
- **Recommendation.** The H5 audit's REMOVE recommendation stands, strengthened. If the owner keeps the trees, option B (§7) gives five reversible steps that close RR-2, RR-9 and RR-6's fetch path, and close RR-1 for every session mode except bypass. **The decision is the owner's.**

## 2. Timeline (UTC)

| Time | Event | Evidence |
| --- | --- | --- |
| 2026-03-01T06:40:51Z | agi-mcp-server cloned from `cognitivecomputations/agi-mcp-server` | H5 audit §5.1 |
| 2026-03-01T06:41:15Z to 06:42:12Z | first `npm install`, with no lockfile. Packuments were fetched 06:41:15Z to 06:41:56Z and tarballs 06:41:57Z to 06:42:12Z; `node_modules` was born 06:41:56Z. Three esbuild postinstall hooks ran native binaries. By fsevents' registry manifest, npm's bundled `node-gyp rebuild` most likely ran as well, failed, and npm dropped the package (O-7) | AGI-H1; npm cache index times |
| 2026-03-01T21:24:03Z | a second npm operation rewrites `package-lock.json`. `~/Library/Caches/node-gyp` (empty) carries the same mtime | AGI-H1; `stat` |
| 2026-03-01T21:28:27Z, 21:33:06Z | adaptive-graph-of-thoughts cloned; two of its modules imported | AGOT-H1 |
| 2026-05-07 | other npm use on the host refreshes 11 of the 218 packuments in npm's cache. A reviewer attributes it to pre-commit's markdownlint-cli installs | cache index times; npm logs dated 2026-05-07 |
| 2026-10-21T05:31:39Z, 05:31:50Z | the H5 auditor captures the March lockfile pairs (270) and installed pairs (174), before any removal | the transient source files, with sha256 values in §10 |
| 2026-10-21T06:46:51Z | the H5 audit lands: juniper-ml#2300, `2f831b60` | GitHub |
| 2026-10-21T07:10:57Z | plan v1.4.4 lands, with the decision pending: juniper-ml#2302, `cf70e259` | GitHub |
| after 07:10:57Z | the owner chooses "remove both; you run it". The agent confirms neither is configured, runs `rm -rf` on both trees and `rmdir` on the parent, and the H5 evidence script then exits 2 | this session |
| (same) | the owner's "let's pause and reconsider" arrives after all three removal commands had completed | this session |
| before 08:33Z | the owner's own `!` restore fails, with its output withheld; it created nothing | `ls` |
| 2026-10-21T08:33:07Z to 08:33:14Z | both trees re-cloned with `git clone --revision=<audited commit>`. The parent is born 08:33:07Z; the reflogs read 08:33:09Z and 08:33:14Z | `stat`; reflogs |
| 2026-10-21T08:53:55Z | `npm config get registry` returns the default registry | npm log (rotated) |
| 2026-10-21T08:54:26Z | an online `npm install --package-lock-only --before=2026-03-01T06:41:56Z --ignore-scripts --fetch-timeout=60000 --fetch-retries=1` stalls at its first packument fetch. No exit is logged, and the run is stopped before 09:03:13Z. A separate `node` `fetch` probe gets `UND_ERR_CONNECT_TIMEOUT` while `curl` gets HTTP 200 in 0.53 s | `npm-logs/2026-10-21T08_54_26_942Z-debug-0.log`; this session |
| 2026-10-21T09:03:13Z | offline lockfile generation without `--before` matches 268 of the 270 March pairs; it picks `picomatch` 4.0.4 and `tinyglobby` 0.2.16 | `npm-logs/2026-10-21T09_03_13_789Z-debug-0.log` |
| 2026-10-21T09:04:09Z | the same run with `--before` is a no-op ("up to date"): `--before` does not re-resolve an existing lockfile | `npm-logs/2026-10-21T09_04_09_946Z-debug-0.log` |
| 09:04:09Z to 09:04:19Z | the 09:03 lockfile is deleted | this session. npm writes the lockfile in place, so the new file's birth time shows the deletion |
| 2026-10-21T09:04:19Z to 09:04:26Z | offline with `--before`: 270 of 270. The lockfile is born 09:04:26Z | `npm-logs/2026-10-21T09_04_19_390Z-debug-0.log`; `stat` |
| 2026-10-21T09:04:55Z to 09:04:57Z | `npm ci --offline --ignore-scripts` adds 176 packages, every tarball a cache hit and no script run: March's set plus `fsevents` | `npm-logs/2026-10-21T09_04_55_207Z-debug-0.log` |
| 2026-10-21T09:06:07Z | `node_modules/fsevents` removed for parity | `stat` |
| 2026-10-21T09:12:23Z to 10:11Z | first restore check; validation round V1, V2, V3 (§9); script fixes from the round | this document |
| 2026-10-21T10:11:34Z | the final restore check: every judged check passes | `restore-check.json` |

## 3. Restoration record

### 3.1 The recipe

§3.1 is the recipe from scratch. §2 is the record of what actually ran.

```bash
# source (git 2.51.0; --revision fetches the history reachable from the commit and detaches HEAD there)
git clone --revision=1f7c6cee241aa387399848e323e66c665e82b7df https://github.com/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server.git ~/.claude/mcp-servers/adaptive-graph-of-thoughts
git clone --revision=9eceac9e214896c3af0ba5d3f4b7bd1770cda07a https://github.com/QuixiAI/agi-mcp-server.git ~/.claude/mcp-servers/agi-mcp-server
# agi-mcp-server's March install, rebuilt with npm 11.11.0 / node v25.8.1
# (March's was likely npm 11.5.1 / node 24.7.0, since both arrived on this host later)
rm -f ~/.claude/mcp-servers/agi-mcp-server/package-lock.json   # no-op on a fresh clone; --before ignores an existing lockfile
npm install --package-lock-only --offline --before=2026-03-01T06:41:56Z --ignore-scripts --no-audit --no-fund --prefix ~/.claude/mcp-servers/agi-mcp-server
npm ci --offline --ignore-scripts --no-audit --no-fund --prefix ~/.claude/mcp-servers/agi-mcp-server
rm -rf ~/.claude/mcp-servers/agi-mcp-server/node_modules/fsevents
```

- **Why offline.** npm's cache (`~/.npm/_cacache`, 562 MiB) holds full March packuments for 207 of the 218 package names, and every tarball the install needs: 169 cached in March, 7 cached since 2025-02-26.
  - An offline run makes no request, so the per-app outbound filter that holds `node`'s connections is not routed around.
  - The offline runs finished in seconds while `node` could not connect at all, which they could not have done had they needed the network.
  - The bits are the ones npm verified when it cached them: the cache is content-addressed by SHA-512.
- **Why `--before`.**
  - Of the 11 packuments refreshed on 2026-05-07, two (`picomatch`, `tinyglobby`) then offered newer in-range versions, and offline resolution took them.
  - The cutoff restores March's choice, giving 270 of 270.
  - The strict bound is 06:41:15Z, the first March fetch; it gives the same result.
- **Why `--ignore-scripts`.** This is a deliberate deviation from March: no dependency code runs at install time.
  - The March install ran three esbuild postinstall hooks, which executed native binaries (AGI-H1). Most likely it also ran fsevents' registry-declared `node-gyp rebuild` (O-7).
  - esbuild is not on the server's runtime path; only `drizzle-kit`, `vite` and `vitest` use it. Its stock `bin/esbuild` node shim still works without the hook.
- **Why remove `fsevents`.** fsevents' registry manifest (cached 2026-03-01T06:41:55Z) declares `install: node-gyp rebuild` and `gypfile: true`, but its tarball ships no `binding.gyp`.
  - March's lockfile-less `npm install` took scripts from the registry manifest, so it ran that build, which cannot succeed, and npm silently dropped the optional package. Both lockfiles still list it, as optional, dev and `hasInstallScript`. Which run touched node-gyp's cache directory is unconfirmed (O-7).
  - `npm ci` reads the tarball's own `package.json`, which declares no script, so this restore installed it.
  - It is a prebuilt native addon that only file watchers load, so it was removed to match March.

### 3.2 Parity with the pre-removal state

| Item | Before the removal | Restored | Status |
| --- | --- | --- | --- |
| adaptive-graph-of-thoughts tracked files | 305, all identical to upstream at `1f7c6cee` | 305 identical. The root tree hash equals the commit's tree, `78fffcc7`, so modes match too | identical |
| its HEAD | `refs/heads/main` at `1f7c6cee` | detached at `1f7c6cee` | deliberate, for the same content. **A detached HEAD is not a pull barrier here** (RR-6) |
| its `origin` | `https://github.com/SaptaDey/Adaptive-Graph-of-Thoughts-MCP-server.git` | the same | identical |
| its `.claude/settings.local.json` | tracked upstream: 41 allow, 0 deny | the same file | identical. The hazard returns with it (RR-1) |
| its two `.pyc` files | from the 2026-03-01 import | absent | not restored. Recreating them means importing the tree's code; Python writes them on any import, and they do nothing else |
| agi-mcp-server tracked files | 33, all identical to upstream at `9eceac9e` | 33 identical; the root tree hash equals the commit's tree, `0a8d2664`. The regenerated `package-lock.json` is the only local file | identical |
| its HEAD | `refs/heads/main` at `9eceac9e` | detached at `9eceac9e` | deliberate, as above |
| its `origin` | `https://github.com/cognitivecomputations/agi-mcp-server.git` (squatted, AGI-P1) | `https://github.com/QuixiAI/agi-mcp-server.git` | deliberate: the old URL would bring back AGI-P1's fetch hazard |
| its `package-lock.json` | 133,254 B | 133,781 B; the same 270 pairs | equivalent, fully explained: March's file plus 13 `libc` arrays (527 B) on the rollup linux entries, which npm 11.11.0 writes and npm 11.5.1 does not. The audit's March line numbers 110 and 526 coincide, and 3452 moves to 3491, 13 three-line blocks down |
| its `node_modules` | 175 package directories, 174 distinct versions | 175 directories, the same 174 | identical set |
| its esbuild `bin/esbuild` (3 copies) | hard links to the native binaries, made by the postinstall hooks | the stock node shims, byte-identical to the tarballs. The native binaries sit in `@esbuild/darwin-x64` as shipped | deliberate (`--ignore-scripts`) |
| npm's hidden lockfile `node_modules/.package-lock.json` | (not recorded) | 176 entries, one being the removed `fsevents` | benign: it is older than the tree it describes, so npm ignores it |
| git metadata | full clones with remote-tracking refs and `[branch "main"]` | `--revision` clones: no remote-tracking refs, empty `packed-refs`, and only `[core]` plus `remote.origin.url` in `.git/config` | deliberate. Not a pull barrier (RR-6) |
| clone and install timestamps | 2026-03-01 | 2026-10-21 | not restorable. The H5 audit records the March times |

## 4. Validation of the restored state

### 4.1 The restore check (`restore-check.json`, 2026-10-21T10:11:34Z)

| Check | Result |
| --- | --- |
| provenance, adaptive-graph-of-thoughts | PASS: HEAD `1f7c6cee241aa387399848e323e66c665e82b7df`, origin SaptaDey, no command-running git config key and no live hook (both judged); 305 identical, 0 modified, 0 local-only, 0 missing |
| provenance, agi-mcp-server | PASS: HEAD `9eceac9e214896c3af0ba5d3f4b7bd1770cda07a`, origin QuixiAI, no such key or hook; 33 identical, and `package-lock.json` is the only local file |
| npm-lock | PASS: 0 extra and 0 missing against the 270 March lockfile pairs |
| npm-tree | PASS: 175 package directories and 174 distinct versions; 0 extra and 0 missing against the March install |
| no-scripts | PASS: all three `esbuild/bin/esbuild` are node shims (`#!`); no native copy; no node-gyp `build/config.gypi` |
| configured | PASS: no client config checked names either server or points into `~/.claude/mcp-servers/`, and every config that exists parses. The project `.mcp.json` search covers `~/Development/python/Juniper` only. The check reads `~/.claude.json` by key name, so only the owner's account can reproduce it |
| processes | PASS: no command line names either tree, and `lsof +D` finds no process holding a file or working directory under the root |
| agot-claude (reported) | `.claude/settings.local.json` present: 41 allow, 0 deny, its only key is `permissions`, no `hooks`, no `disableAllHooks` |
| advisories (reported) | 89 active for the installed npm set: 3 critical, 29 high, 53 medium, 4 low (4 withdrawn excluded). That is identical to the H5 audit's count for the March install (AGI-P3), as an identical set should give |

Reviewers reproduced these results by other means (§9):
- V1 re-ran the check online twice, and the JSON was identical apart from `collected`.
- V3 derived parity with its own walk, and compared every tracked file by blob sha1 and git mode.

### 4.2 Host checks (2026-10-21)

- **File modes.** Nothing in either tree is group- or world-writable, nothing is setuid or setgid, and every file belongs to the owner. The sizes are 24 MiB (adaptive-graph-of-thoughts) and 100 MiB (agi-mcp-server).
- **Listeners and Docker.** Nothing listens on 8000, 7474, 7687 or 5432 (`lsof -nP -iTCP -sTCP:LISTEN`, this user's sockets only). No Neo4j, Postgres, pgvector, AGoT or Hexis image or container exists.
- **Claude Desktop.** `/Applications/Claude.app` exists (`com.anthropic.claudefordesktop` 1.1.4498). Its `Info.plist` declares the `dxt` and `mcpb` types, and `mdls` reports a `.dxt` as kind "Desktop Extension". `~/Library/Application Support/Claude` does not exist, so the app has never been launched under this account.
- **Guards and agent history.** The C8 guard is not installed: `~/.claude/hooks/` does not exist. No `~/.claude/projects/` directory exists for either tree path, so no Claude Code session has ever run in one.
- **Spotlight.** `mdfind -onlyin ~/.claude/mcp-servers` returns nothing; the trees are not indexed.
- **Outbound filter.** `/usr/local/bin/node`, which links to `/usr/local/Cellar/node/25.8.1_1/bin/node`, is held on `registry.npmjs.org` (`UND_ERR_CONNECT_TIMEOUT`) while `curl` connects (RR-12).
- **Host posture** (`python3 util/host_state_check.py --section G-SEC`, re-run):
  - SIP is "Custom Configuration" and the application firewall is off.
  - The firewall would auto-allow downloaded signed software (`socketfilterfw --getallowsigned`).
  - Docker Desktop is running (`com.docker.backend`).
- **VS Code.** The user `mcp.json` configures four servers: `huggingface` (http), `microsoft/markitdown` (stdio), `oraios/serena` (stdio) and `upstash/context7` (http). Only names and transport type were read (O-5). The user `settings.json:1083` opens a `chat.tools.terminal.autoApprove` block, and no workspace-trust override is set (RR-13).
- **Backups.** `tmutil destinationinfo`: "No destinations configured". `tmutil isexcluded` reports `~/.claude/mcp-servers` and `~/.npm` as Included (O-8).

### 4.3 Claude Code does not read the trees on its own

- **The binary.** `~/.local/share/claude/versions/2.1.306` (284,167,840 B) contains `mcp-servers` 7 times. Two are an API beta flag, `mcp-servers-2025-12-04`. Five are a bundled skill's reference file in the binary's embedded file system. **None is a host path.**
- **Nothing else names them.** Nothing under `~/.claude/{agents,skills,plugins}` names the trees.
- **The consequence.** The trees act only when a client config names them, which none does (§4.1), or when a session or tool works inside one (RR-1, RR-13).
- **This reading is version-bound.** The versions directory also holds 2.1.304 and 2.1.305. Dormancy rests on §4.1's configured check, so re-run both after a Claude Code update (O-9).

## 5. Risk register

**Scales.** Likelihood is judged for the state as it is today:
- **Remote:** needs several independent, unusual steps.
- **Low:** needs one deliberate, unusual action.
- **Medium:** plausible in routine work.
- **High:** expected.

Impact runs from **Low** through **Moderate** and **High** to **Severe**; Severe means arbitrary code as the owner, or the owner's credentials. Ratings come from this matrix:

| Likelihood \ Impact | Low | Moderate | High | Severe |
| --- | --- | --- | --- | --- |
| Remote | Low | Low | Low | Medium |
| Low | Low | Low | Medium | Medium |
| Medium | Low | Medium | Medium | High |
| High | Medium | High | High | Critical |

**Assets.**
- The owner's GitHub token, through `gh`.
- The SSH deploy-key aliases and the GPG configuration.
- The Juniper repositories.
- Claude Code's own configuration (`~/.claude.json`, settings) and the IDE configurations.
- LLM API keys, wherever they are set.
- The integrity of research results.
- The host itself.

| ID | Risk | Trigger | Likelihood | Impact | Rating | Controls today | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RR-1 | A Claude Code session whose project is the adaptive-graph-of-thoughts tree. Its tracked `.claude/settings.local.json` allows `Bash(python3:*)`, `Bash(node:*)`, `Bash(npx:*)`, `Bash(timeout:*)`, `Bash(rm:*)`, `Bash(chmod:*)`, `Bash(cp:*)`, `Bash(npm install:*)`, `Bash(./install-dxt.sh:*)`, `Bash(claude mcp add:*)` and `Bash(claude mcp:*)` (AGOT-A2). The list pre-approves those commands in default and accept-edits sessions. In auto mode, allow rules approve calls without the classifier (the binary's own string). A bypass-permissions session, which is how turing's agent sessions run, approves every command that no deny rule or hook blocks; there the exposure is steering by the tree's content | anyone, or any agent, starting Claude Code inside the tree | Low (it has never happened) | Severe: arbitrary code as the owner, and MCP registration | Medium | none installed (C8 is pending). The handoff says "never open Claude Code inside that tree", and E-H5 says "Never open Claude Code inside an untrusted clone". The folder-trust dialog is not counted (CNV) | A. Otherwise B.1, which closes the allow-list path for default, accept-edits and auto sessions. A bypass session in the tree stays exposed |
| RR-2 | A bundle installed into Claude Desktop. The three `.dxt` files are bound to Claude Desktop, so opening one, by double-click or `open x.dxt` from the owner or an agent, starts the installer. An installed bundle runs its vendored `server/node_modules` (1,237 entries, including `form-data` 4.0.3 with critical CVE-2025-7783) with `"sandbox": false`, at every Desktop start, on Desktop's own runtime, which RR-12's `node` hold does not cover (own knowledge). The three `.dxt` servers fabricate their results (AGOT-A1). The `.zip` opens in Archive Utility instead, extracting a second tree that proxies to `localhost:8000` and needs a manual install (AGOT-P1) | opening a `.dxt` and confirming the install | Low | High. That is a floor, which assumes the vendored code is benign | Medium | Claude Desktop has never been launched; nothing is installed | A. Otherwise B.2. This corrects AGOT-P1's fix note: the app is present (O-1) |
| RR-3 | adaptive-graph-of-thoughts enabled. Its results are fabricated (AGOT-A1), and no standard client can use its Python stdio server (AGOT-A6). Starting `mcp-server` gives an HTTP server on `0.0.0.0:8000` with fail-open Basic auth, unauthenticated `/mcp`, and every-origin CORS with credentials that spends the LLM key (AGOT-A3). Starting a compose file publishes Neo4j with a well-known password (AGOT-E2) | an MCP config entry, `mcp-server`, or `docker compose up` | Low | High, compounded by RR-11 | Medium | not configured; not running | A. The H5 audit §8.3 offers no enable path |
| RR-4 | Database-wide Neo4j deletes from pipeline stage 5 (AGOT-A5) | RR-3's trigger, plus a Neo4j the host lacks, plus a stage loader that likely loads nothing (AGOT-A7) | Remote | High | Low | no Neo4j present | None beyond RR-3's |
| RR-5 | agi-mcp-server enabled. Its persistent memory store returns stored text to the model in later sessions, a cross-session prompt-injection channel (AGI-A1). It ships a persona prompt (AGI-A2), and uses default database credentials with no TLS (AGI-A3) | an MCP config entry, plus the Postgres, pgvector and AGE stack (`QuixiAI/Hexis`, not on the host) | Low | High for agent integrity | Medium | not configured; no database stack | A. Otherwise the H5 audit §8.3's eight conditions |
| RR-6 | **Fetching or pulling upstream code.** With no fetch refspec configured, a bare `git fetch` gets origin's HEAD into FETCH_HEAD, and a bare `git pull` most likely fast-forwards the detached HEAD onto it. That is git's documented default, not tested here, because this session's guard refuses git outside its worktree. `git pull origin main` certainly does. For adaptive-graph-of-thoughts that is a single user's account (AGOT-P3). A pull never delivers hooks or git config, but it does deliver tracked files that other tools treat as configuration: `.claude/settings*.json`, `.vscode/`, and a `util/` (RR-13). agi-mcp-server's documents also keep the squatted references alive: `npx -y github:cognitivecomputations/agi-mcp-server` (`example-config.json:7`; `README.md:102`, `:148`; `USAGE.md:16`, `:44`); `npx -y @cognitivecomputations/agi-mcp-server`, an unpublished npm scope that anyone could claim (`USAGE.md:58-62`); and `git clone` of `cognitivecomputations/agi-mcp-server.git` (`README.md:55`) and `agi-memory.git` (`README.md:32`, `USAGE.md:103`) | a `git fetch` or `git pull` in a tree, or following the tree's example config or install steps | Low | High: unaudited or squatter code | Medium | agi's `origin` is QuixiAI. Little Snitch holds `node`, which blocks the `npx` path. Worktree-isolated agent sessions refuse git outside their worktree (O-3). The detached HEAD is **not** a control | A. Otherwise B.5, and never follow the tree's example configs or install steps |
| RR-7 | Known-vulnerable dependencies: 89 active npm advisories, dormant unless code runs | running the server, `npm test` (vitest pulls `tinypool`: 2 critical RCE gadgets), or `vite` | Low | Moderate | Low | nothing runs | A. Before any use, take `drizzle-orm` 0.45.2 or later and re-run the advisory query |
| RR-8 | Native binaries on disk: three `@esbuild/darwin-x64` versions and `@rollup/rollup-darwin-x64` | running `drizzle-kit`, `vite`, `vitest` or rollup | Low | Moderate | Low | npm verified them (SHA-512); nothing has run them since the restore | Covered by RR-9's control |
| RR-9 | Install-time code on a future `npm install` or `npm rebuild` in the tree: esbuild's postinstall hooks, fsevents' registry-declared `node-gyp rebuild`, and anything else npm decides to run | anyone running npm there without `--ignore-scripts` | Low | Moderate | Low | none in the tree | B.3 |
| RR-10 | **MCP-registration paths with no guard.** The C8 guard is not installed. Once installed it would not see MCP tools (H5-X1), and **no rule covers any registration path**: `claude mcp add`, `add-json` and `add-from-claude-desktop` (which write `~/.claude.json`); a direct write of `~/.claude.json`; or a project `.mcp.json` pre-approved through `enabledMcpjsonServers` or `enableAllProjectMcpServers` in that worktree's `.claude/settings.local.json`. SELF-PROTECT-FILE blocks only `disableAllHooks` there (`util/claude_agent_guard.py:188`, `:1615`). Both files are gitignored (`.gitignore:166-167`, `:170`), so neither shows in `git status` or a PR. A rule keyed on the `claude` command word also misses the direct versions path, because the guard compares basenames, and script internals stay invisible (guard gap 1). RR-1's allow list pre-approves exactly `claude mcp add` | a prompt-injected or mistaken agent action | Low | High | Medium | Claude Code's permission prompts, which bypass-permissions sessions never show. In practice, only the owner's review | A C8 extension, as a C9 candidate (owner decision). It would deny (a) the `mcp add*` subcommands, whatever the command word, (b) writes to `~/.claude.json` and to any `.mcp.json`, and (c) project-settings writes that set either approval key. Gap 1 still bypasses it. Also install C8 |
| RR-11 | Host posture amplifies RR-1, RR-3, RR-5 and RR-13. The application firewall is off, so any listener a server opens is on the LAN, and possibly within reach of anyone in radio range (plan §16.3 E-NET records an unidentified open radio broadcasting the owner's network name). AGOT-A3's every-origin CORS reaches `localhost:8000` from any web page whatever the firewall says. C2, as worded, auto-allows downloaded signed software, so Docker's signed backend would keep publishing compose ports. SIP's protections are off, which matters after a compromise | any of RR-1, RR-3, RR-5 or RR-13 | as for the triggering risk (Low) | High | Medium | Little Snitch, which also supports inbound rules (own knowledge) | C2 with "block all incoming connections" while nothing inbound is needed, or per-app inbound denies for `com.docker.backend`, `node` and the env Pythons. C1 for containment. Never run the compose files |
| RR-12 | The node rule in Little Snitch. The stopped online attempt may have left an alert pending for `/usr/local/Cellar/node/25.8.1_1/bin/node`; whether one is pending was not checked. Its scope matters. An allow for `registry.npmjs.org` alone would not open `npx -y github:`, which needs `github.com` or `codeload.github.com`. A blanket deny breaks pre-commit's node hook environments (the markdownlint hook at `.pre-commit-config.yaml:233-239`). A rule on the Cellar path lapses at the next `brew upgrade node` | answering an alert, or a later `brew upgrade` | Medium | Moderate | Medium | the alert holds the connection | B.4 |
| RR-13 | **An IDE agent on a tree.** Suppose the owner opens a tree in VS Code (Copilot agent mode, Amp) or Cursor and asks the agent to set it up or run it. VS Code auto-approves every terminal command (`"/.*/": true` under `chat.tools.terminal.autoApprove`, `settings.json:1083`). Amp has two unconditional `Bash` allow rules (28, 39), and Cursor's Auto-review can allow unsandboxed calls ([`JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`](JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md), K13 pending). The agent would follow the tree's own steps: `install-dxt.sh`, `docker compose up`, `npx -y github:...`. AGoT's `.devcontainer` offers a `poetry install` under the running Docker Desktop. A reviewer reads the user-level run-on-save as running `<nearest ancestor holding util>/util/last_mod_update.bash`. None exists in or above the trees today, but a pulled `util/` (RR-6) would turn saving a file into running tree code. The `.claude/settings.local.json` plays no part | opening a tree folder in VS Code or Cursor, trusting it, and prompting the IDE agent | Low | Severe: unprompted code as the owner | Medium | the VS Code Workspace Trust prompt (not overridden; whether a trusted parent covers `~/.claude` is CNV); no auto-run file in either tree | A. Otherwise never open the trees in an IDE, and finish K13 (owner) |
| RR-14 | **Tree text reaching agents through searches.** A Grep or `grep -r` rooted at `~/.claude`, where agents look for agents, skills and settings, returns tree text, including `prompt.md`'s persona lines (AGI-A2). In a bypass session any steering acts unprompted | a routine search under `~/.claude` | Low | Moderate. A reviewer's grep of both trees' documents found no other agent-directed text; a pull could change that | Low | Spotlight does not index the trees. Once installed, C8 denies searches rooted at home or above, but not at `~/.claude` | A. Otherwise narrow search roots |

## 6. Other issues

- **O-1. The H5 audit's AGOT-P1 fix note is incomplete.** It says the bundle hazard needs Claude Desktop and that turing has no extensions directory. In fact the app is installed, bound to `.dxt` and `.mcpb`, and never launched (§4.2). RR-2 carries the corrected view. The audit file itself is left as written.
- **O-2. The plan records the decision as pending.** Plan v1.4.4's H5 row is accurate, but it predates the removal, the restore and this analysis. The next turing plan revision should fold them in with the owner's decision. It should also point §18 at the arc's current main handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` (juniper-ml#2305).
- **O-3. The owner's `!` commands failed here.** The restore the owner ran through `!` created nothing, and its error detail was withheld.
  - The likeliest cause is the session's worktree guard (CNV). It refuses any git aimed outside the worktree; it also refused this analysis' scratch-directory pull experiment (RR-6).
  - Owner-run git on host trees belongs in a separate terminal.
- **O-4. The restored trees are pinned at the audited commits, not the upstream tips.**
  - **adaptive-graph-of-thoughts' six newer commits.** Two are dependabot bumps, one is a README-badge commit (`07b97361c130`, no net change) and three are merges. Net, they touch only `package.json`, `poetry.lock` and `server/package-lock.json`. The three security bumps (`mcp` 1.10.0, `form-data` 4.0.4, the Inspector at ^0.16.1) sit in two of them. Moving to that tip needs a new audit.
  - **agi-mcp-server's one newer commit**, `472bd965`, is the namespace fix. AGI-P1 read its whole diff, and the H5 audit's §8.3 names it as the pin. Moving there would remove RR-6's squatted references, for the cost of one fetch.
- **O-5. VS Code's four MCP servers were never reviewed.** H5 checked VS Code's `mcp.json` only for the two trees; neither H0 nor H5 reviewed the four servers it configures (§4.2). D10's concern about an unpinned Serena applies there too, but was not checked: no argument values were read. That is a candidate follow-up, outside H5.
- **O-6. npm's cache.** It keeps the March tarballs and packuments (562 MiB). They are content-addressed and never execute, and they are what made the offline, verified restore possible. Keep them or clean them; neither choice changes a risk here.
- **O-7. AGI-H1's "what ran" is incomplete.**
  - By fsevents' registry manifest, March's lockfile-less install most likely also ran npm's bundled `node-gyp rebuild` for fsevents. Without a `binding.gyp` that build cannot succeed, and the optional package was dropped (§3.1).
  - Nothing from the trees ran in that step: node-gyp is npm's own tool.
  - `~/Library/Caches/node-gyp` is empty, with an mtime of 2026-03-01T21:24:03Z, which is the second npm operation's time. Which operation touched it is unconfirmed.
- **O-8. Backups.** No Time Machine destination is configured, and the only local snapshots are OS-update ones, so no backup holds the trees today. `~/.claude/mcp-servers`, `~/.claude` and `~/.npm` are not excluded.
  - Plan task C0's encrypted Time Machine backup would therefore copy kept trees, and a later restore from it would bring back removed ones.
  - Choose option A before C0, or have the owner exclude the path.
- **O-9. §4.3's binary reading belongs to one Claude Code version.** Re-run it, and §4.1's configured check, after each update.

## 7. Options for the owner

| Option | What it does | Residual risk |
| --- | --- | --- |
| **A. Remove both** (the H5 audit's recommendation, strengthened here) | `rm -rf ~/.claude/mcp-servers/adaptive-graph-of-thoughts ~/.claude/mcp-servers/agi-mcp-server`, then `rmdir ~/.claude/mcp-servers`. The source can be re-cloned as in §3.1 at any time, and the March install rebuilt offline while npm's cache lasts | RR-10 to RR-12, which are host-wide. O-8 then has nothing to back up |
| **B. Keep, dormant and hardened** | Five reversible steps (below). Then record the choice in the plan | RR-1 for bypass sessions; RR-3 to RR-5, RR-7 and RR-8 latent behind "never configure"; RR-13 and RR-14; RR-10 to RR-12 |
| **C. Keep as restored** | Nothing changes. Rely on the handoff's rules and E-H5 | all of §5 |

Option B's steps, each with its reversal:

- **B.1** (RR-1): rename the allow list in place, to a name Claude Code does not read:

  ```bash
  mv ~/.claude/mcp-servers/adaptive-graph-of-thoughts/.claude/settings.local.json ~/.claude/mcp-servers/adaptive-graph-of-thoughts/.claude/settings.local.json.h5-disabled
  ```

  Reverse it with the opposite `mv`. Never move the file into another project's `.claude/`, which would transplant the allow list. It closes the allow-list path for default, accept-edits and auto sessions; a bypass session in the tree stays exposed.
- **B.2** (RR-2): rename the four bundles in place to extensions nothing opens, for example `mv <bundle> <bundle>.h5-disabled` for `adaptive-graph-of-thoughts-v1.0.2-final.dxt`, `adaptive-graph-of-thoughts-v1.0.1-submission.dxt`, `Adaptive-Graph-of-Thoughts-MCP-server.dxt` and `adaptive-graph-of-thoughts-dxt-v1.0.0-production.zip`. Or delete them.
  - Reverse it with the opposite `mv`. For deleted bundles, use `git checkout -- <path>` in the tree. That is safe for the owner to run, because the trees have no command-running git config key and no live hook (§4.1).
  - Do not move the bundles to another Finder-visible folder, which would make opening one more likely.
- **B.3** (RR-9): `printf 'ignore-scripts=true\n' > ~/.claude/mcp-servers/agi-mcp-server/.npmrc`. Reverse it by deleting the file.
- **B.4** (RR-12): write a standing Little Snitch rule for the Cellar `node`. Allow `registry.npmjs.org` only if npm is needed, and deny `github.com` and `codeload.github.com`. Answer any pending alert with "Deny once". Reverse it by deleting the rule.
- **B.5** (RR-6): the owner runs `git -C ~/.claude/mcp-servers/<tree> remote remove origin` for each tree. It is safe for the same reason as B.2. A bare fetch or pull then has nowhere to go. Reverse it with `git -C <tree> remote add origin <URL from §3.1>`.

After B, the restore check's provenance FAILs by design. The renamed files show as missing locally, `.npmrc` as local-only, and `origin` as absent. The reverse steps return it to PASS.

**Recommendation: A**, as the H5 audit concluded, and more firmly with RR-13 and O-8 in view. Neither server offers the plan anything (H5 audit §8). If the owner keeps them, B. **The decision is the owner's.**

## 8. Method

- **Static throughout.** No code from either tree was executed, imported or built.
  - **git:** ran only as `git clone --revision` into new directories, and `git ls-remote` on a URL. Nothing ran inside a tree. A scratch-repository pull experiment was refused by the session's guard (RR-6).
  - **npm:** every completed run had `--offline --ignore-scripts`; the stalled first attempt was online and received no response.
  - **Everything else was read as data:** manifests, lockfiles, the trees' `.git/config`, the Claude binary's strings and the npm logs.
- **The check script.** It runs with `sys.dont_write_bytecode`, so it writes nothing, not even `__pycache__`.
- **Network use:**
  - `gh api` GETs, with no method or field flags;
  - the two clones and `git ls-remote`;
  - one `curl` and the `node` `fetch` probes to `registry.npmjs.org`;
  - the stalled online npm run.
- **Client configs:** server names and transport type only. No command, argument, URL, header or environment value was read.
- **Likelihoods** are judgments about this host's routine: one owner, and agent sessions in Juniper worktrees. Impacts follow the H5 audit's findings.

## 9. Validation record

**One round, 2026-10-21, three independent reviewers** with fresh context. All were read-only and barred from running code from the trees.

| Reviewer | Focus | Verdict | Findings | Disposition |
| --- | --- | --- | --- | --- |
| V1 | factual verification of every checkable claim | ACCEPT-WITH-CHANGES | 0 blocker, 0 major, 12 minor, 11 nit | all applied |
| V2 | security completeness and calibration | ACCEPT-WITH-CHANGES | 0 blocker, 4 major, 6 minor, 3 nit | all applied; V2-01 with a caveat, below |
| V3 | restoration procedure and reproducibility | ACCEPT-WITH-CHANGES | 0 blocker, 2 major, 9 minor, 4 nit | all applied but V3-13, deferred, below |

**V1, factual verification.**
- It reproduced the parity counts, the timeline (`stat`, reflogs, merge times), the allow list, the bundles, Claude Desktop, G-SEC, Docker and the listeners.
- It ran the check online twice; the JSON was identical apart from `collected`.
- What it corrected:
  - the online attempt's time (08:54:26Z);
  - the March install's start (06:41:15Z);
  - two squatted references missing from RR-6;
  - the pull and fetch nuance;
  - the Cellar `node` path;
  - the rating matrix;
  - B.1's reach in bypass sessions;
  - the check's `__pycache__` write;
  - units;
  - the baselines' provenance;
  - this document's claim that the handoff was already updated.

**V2, security completeness.**
- It added RR-13 (IDE agents) and RR-14 (searches), and widened RR-10 to every registration path.
- It corrected RR-6's pull reasoning; split RR-2 between the `.dxt` files and the `.zip`; re-calibrated RR-11 and RR-12; and made B.1 and B.2 safe, renaming in place rather than moving.
- It added B.5, O-8 (backups) and O-9 (version binding), and set the agi pin per the audit's §8.3.
- **V2-01's suggested experiment was not run.** It proposed a scratch-repository `git pull` after `clone --revision`, and the session's guard refuses git outside its worktree. RR-6 therefore states the pull behaviour as git's documented default, untested, and B.5 is the control that holds either way.

**V3, restoration reproducibility.**
- It derived parity by its own walk: 270 of 270 lockfile pairs, and 174 of 174 installed in 175 directories.
- It compared every tracked file by blob sha1 and git mode, and recomputed both root tree hashes, which equal the commits' trees.
- It re-ran the advisories (89, with the same three criticals), and explained the 527-byte lockfile difference exactly.
- What it corrected:
  - the fsevents explanation (V3-01);
  - the missing runs and the lockfile deletion (V3-02);
  - the cache account;
  - the npm versions;
  - the pull nuance;
  - option B's reversals;
  - four check-script defects. The check now labels offline provenance as not tree-compared, judges git hooks and command-running config keys, fails a config that exists but does not parse, and adds an `lsof +D` probe.
- **V3-13 is deferred.** It concerns the H5 inventory script, which excludes `.git` and `node_modules` at every depth and does not compare modes. V3's root-tree-hash comparison already covers modes and the full tree. The inventory script landed with the audit and is left as is.

**The author's own checks of the reviewers' load-bearing claims**, re-run this session:
- `.gitignore:166-167` and `:170`;
- `claude_agent_guard.py:188` and `:1615`;
- the binary's `enabledMcpjsonServers`, `enableAllProjectMcpServers`, `add-from-claude-desktop` and auto-mode strings;
- `settings.json:1083`;
- `socketfilterfw --getallowsigned`;
- `tmutil`;
- no Claude Code project directory for either tree;
- `mdfind`.

## 10. Documents and evidence

**Documents.**
- [`JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`](JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md): the H5 audit, whose finding IDs this analysis cites.
- [`JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md), v1.4.4. Cited for H5's row and erratum E-H5, G-SEC (§9.3), H0 (§16.2 :853), E-NET (§16.3), D11's auto-mode record, and C0, C1, C2, C8 and C9.
- [`JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`](JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md): the IDE auto-approval findings and K13 (RR-13).

**Scripts.**
- [`util/ad-hoc/2026-10-21_turing_h5_restore_check.py`](../util/ad-hoc/2026-10-21_turing_h5_restore_check.py): the restore check.
- [`util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py`](../util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py): the H5 evidence script.
- [`util/claude_agent_guard.py`](../util/claude_agent_guard.py): C8's rules. None covers an MCP-registration path.

**Evidence, in `reports/2026-10-21_turing-h5-restore/`.**
- **The March baselines:** `march-lockfile-packages.txt` (270 pairs, sha256 `cdd3097067e60a406c2b2832db18bccef122f49a43ce313cbc7e06faa9eec74a`) and `march-installed-packages.txt` (174 pairs, sha256 `70e06dead96dc94f6d7e330492f1d76da211b349f58e9e7c23b11d0eaae2c262`).
  - They are sorted, one-per-line copies, made at 09:07:57Z, of two comma-joined files the H5 auditor wrote before the removal. Each source holds the same items, in the same order, as its copy:
    - `agi_affects.txt`: born 2026-10-21T05:31:39Z, sha256 `d6175fc60e43f47503c53a4bbf542827b2dde004849839b04660be00cc654819`;
    - `agi_installed_affects.txt`: born 05:31:50Z, sha256 `50588c3b660ca3818a304576cfc421cf2c57fbc62bd49534c6b6c81a79c25718`.
  - Both sources sit in that session's transient scratchpad. The corroboration that outlives them: the audit's counts and versions, the identical 89-advisory tally, and the lockfile's line and byte accounting.
- **`restore-check.json`:** the final check's output.
- **`npm-logs/`:** the five npm debug logs of the restore. npm keeps only ten, so they were copied here; a grep found no secret in them.
  - `2026-10-21T08_54_26_942Z-debug-0.log`
  - `2026-10-21T09_03_13_789Z-debug-0.log`
  - `2026-10-21T09_04_09_946Z-debug-0.log`
  - `2026-10-21T09_04_19_390Z-debug-0.log`
  - `2026-10-21T09_04_55_207Z-debug-0.log`

**Handoffs.**
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md`: H5's handoff, updated with this analysis in the same PR.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md`: the arc's main handoff (juniper-ml#2305).
