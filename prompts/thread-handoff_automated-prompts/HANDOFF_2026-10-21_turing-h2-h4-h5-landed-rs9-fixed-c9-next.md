# Handoff — turing bring-up: H2, H4 and H5 landed (plan v1.4.4), main's R-S9 flake fixed; C9 next, owner decisions pending

- **Superseded (2026-10-25, plan v1.4.6).** C9 landed (juniper-ml#2322) and H6's audit ran. The arc's main handoff is now `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`. What follows is this file's state before C9.

- **From:** the 2026-10-20/21 session on turing named "code signing" (ae687e; worktree `.claude/worktrees/linked-floating-sprout`). It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md`.
- **This file supersedes** this session's earlier `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md`. That one was written before H5, plan v1.4.4 and the R-S9 fix. The "mac dev" session's `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md` stays the authority on H5's state and the removal commands. **Since plan v1.4.5** the owner has chosen H5's option B (keep, hardened), and the authority on H5 is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.4.
  - §18.1 holds the owner's two rulings of 2026-10-21: the split, and Serena's edit tools leading to C9.
  - §18.2 holds the H2, H4, C9 and H5 rows.
  - §18.3 holds errata E-SPLIT, E-H4-WHEEL, E-SERENA-EDIT and E-H5.
  - Task IDs below are the plan's.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.
- **Coordination.**
  - "mac dev" (37a935) took H5 and owns its follow-up. Once the owner decides on removal, it writes v1.4.5.
  - "canopy" reported the R-S9 flake. Run `ListAgents` before starting, and check `gh pr list --repo pcalnon/juniper-ml --state all --search "<task>"` before taking a task.
  - `main` moved every 10–20 minutes on 2026-10-21. Two PRs refreshed together go BEHIND each other, so agree a merge order by message (E-LAND-3).

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2294 | `b16121ac` | **H2**: `.claude/agents/{macos-host-sme,signing-auth-sme,k8s-node-sme}.md`, with three contract suites sharing `tests/agent_contract_support.py` (49 tests). Each suite runs `util/claude_agent_guard.py`: 43 denials under the cited rules, 25 procedure calls passed. 28 of 28 mutants killed |
| juniper-ml#2295 | `a005063e` | **H4**: `util/mcp_setup.bash` and the pin in `conf/hosts/turing/mcp.json` (Serena v1.7.0, `949a27ef1e5fda1a6e7b561e777bcece345c6ffd`). `.serena/project.yml` excludes `execute_shell_command`, and `.gitignore` covers `.mcp.json.bak-*`. 35 tests, also on `host-tooling-macos`; 20 of 20 mutants killed. **Live check blocked** (E-H4-WHEEL) |
| juniper-ml#2297 | `d9b29f38` | Plan v1.4.3, `util/ad-hoc/2026-10-21_turing_h2_h4_record.py`, and the superseded handoff |
| juniper-ml#2299 | `be0ab745` | That handoff's correction: the expected `MISSING`, and H5's record being "mac dev"'s |
| juniper-ml#2300 | `2f831b60` | **H5** ("mac dev"): `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`, which recommends REMOVE for both servers (3 blockers) |
| juniper-ml#2302 | `cf70e259` | Plan v1.4.4 ("mac dev"): the H5 row, with the owner's decision pending, and erratum E-H5 |
| juniper-ml#2304 | `fcaf5e0c` | **R-S9 flake fix.** Post-merge main verification failed `test_r_s9_never_opens_credentials_never_runs_gpg_and_writes_only_its_files` on 4 of 5 heads. A runner whose Python 3.12.15 toolcache lacked `encodings/__pycache__/utf_8_sig`'s .pyc wrote one, and the audit hook counted it. The audited child now runs with `-B`. Main verification run 39564516111 is green |
| this handoff's PR | — | this file |

## State measured 2026-10-21 (08:40Z)

- **Readiness**, from `python3 util/host_state_check.py`: **0 of 7**, the same seven failures as on 2026-10-20 (G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET, G-MEM).
- **H2's install has not happened.**
  - `~/.claude/agents` holds the 6 older agents, and the primary checkout still has 6. It has not been fast-forwarded.
  - The three SME agents *are* usable today as project agents in any session whose working directory is a juniper-ml checkout at or after `b16121ac`. Claude Code loads `.claude/agents/` from the checkout.
- **C8 is not installed:** `~/.claude/hooks/juniper_agent_guard.py` is absent.
- **H5:** both `~/.claude/mcp-servers/adaptive-graph-of-thoughts` and `~/.claude/mcp-servers/agi-mcp-server` are still present. The owner's decision is pending.
- **E-H4-WHEEL:** rustup holds no toolchain at 1.83 or later. The default `stable` is 1.71.0, beside 1.49.0, 1.56.0 and 1.56.1. So Serena v1.7.0 still cannot build on turing.

## Owner decisions and steps

1. **E-H4-WHEEL: Serena on turing.** Choose one:
   - (a) install a Rust 1.83+ toolchain beside 1.71 and build once (the command is in plan §18.3);
   - (b) pin Serena v1.6.1, whose cryptography 48.0.1 has Intel wheels but carries CVE-2026-69247, -69248 and -69249;
   - (c) keep Serena off turing.

   H4's live check, `timeout 30 claude mcp list` showing serena connected, waits on this.
2. **H5: remove the two unvetted servers, or keep them.** The audit recommends REMOVE; the commands are in "mac dev"'s handoff.
3. **C8 step 1.** Fast-forward the primary checkout (`git pull --ff-only origin main`) and install the guard (`bash util/install_claude_agent_guard.bash --apply`). Then `bash util/install_agents.bash` from that checkout should give 9 agent links, which is H2's acceptance.
4. **Unchanged:**
   - A1 (the two remotes, then `pre-commit install --hook-type pre-push`);
   - `~/.condarc` `ssl_verify: true`;
   - `conda env config vars unset PYTHONPATH -n JuniperPython`;
   - the network (F2, A6);
   - F3 node mode;
   - commit signing (§19): no YubiKey into turing until C8 and K12 are installed and K13 is done;
   - the rest of Owner block 1.

   After each block, run `python3 util/host_state_check.py`.

## Agent next

1. **C9** (owner ruling 2026-10-21; H3 waits on it): extend `util/claude_agent_guard.py` to MCP file-writing tools (E-SERENA-EDIT).
   - **The matcher.** The installed settings matcher is `Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob`. `util/install_claude_agent_guard.bash` writes it, so it must also name Serena's tools (`mcp__serena__<tool>`).
   - **The tools.** At v1.7.0 they are `replace_content`, `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol`, `replace_in_files`, the optional `delete_lines` / `replace_lines` / `insert_at_line`, and the memory writers.
   - **The paths.** Serena's `relative_path` resolves against its `--project` root, the checkout. Deny a call that reaches `.git/` (hooks, config), `~/.ssh`, `~/.gnupg` or the Claude settings. Keep the guard's contract: an unknown tool passes silently.
   - **Tests and install.** Add cases in `tests/test_claude_agent_guard.py`, plus a mutation check on the C8 and K12 pattern. The owner re-installs the guard.
   - **H5 found** that neither unvetted server has file-writing tools, so C9 does not cover them. Their DB and network tools would need `permissions.deny` rules instead (H5-X1).
   - C9 can be built and landed before C8 is installed. Only its installation is the owner's.
   - **Widened by plan v1.4.5 (owner, RR-10):** C9 also denies MCP registration: the `mcp add*` subcommands whatever the command word, writes to `~/.claude.json` and any `.mcp.json` (H4's `util/mcp_setup.bash` must keep working), and settings writes that set `enabledMcpjsonServers` or `enableAllProjectMcpServers`. The plan's §18.2 C9 row has the detail.
2. **H3**, after C8 is installed, C9 has landed and H2's agents are installed. Each agent runs one scripted task on turing, compared with a `util/host_state_probe.bash --json` run taken within ±10 minutes, plus one negative test. The task prompts go through `prompt-validator`.
3. **H4's live check**, once E-H4-WHEEL is resolved:
   - `bash util/mcp_setup.bash` in the primary checkout;
   - pre-warm with `uvx --from git+https://github.com/oraios/serena@949a27ef1e5fda1a6e7b561e777bcece345c6ffd serena --version`;
   - then `timeout 30 claude mcp list`.
4. **Plan revisions.** "mac dev" writes v1.4.5 for the owner's H5 decision, and C9's landing needs its own record. Before numbering, check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.
5. F3 node mode follows its owner step. E5 waits on A6. D2-upg and D4 still need re-planning under the D6 ruling.
6. **Post-merge check (E-LAND-2).** Done at `036e53e2` for H2, H4 and v1.4.3: every edit present after three concurrent PRs. After any later merge that touches the shared files, re-run the dry-runs below. Three deviations are expected, none of them a revert:
   - `util/ad-hoc/2026-10-20_turing_g1_g4_record.py` reports its Version-line edit `MISSING`, because v1.4.3 replaced the line;
   - `util/ad-hoc/2026-10-21_turing_h2_h4_record.py` does the same, because v1.4.4 replaced it. Each script's other edits stay `present`;
   - on a later UTC day, an apply script that touches AGENTS.md reports `would change ... AGENTS.md` for the **Last Updated** date.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --json number,title
python3 util/host_state_check.py                                     # readiness (0 of 7 on 2026-10-21)
python3 -I util/ad-hoc/2026-10-20_turing_h2_apply.py --dry-run        # 0 files to change
python3 -I util/ad-hoc/2026-10-21_turing_h4_apply.py --dry-run        # 0 files to change
python3 -I util/ad-hoc/2026-10-21_turing_h2_h4_record.py --dry-run    # Version line MISSING by design; the rest present
python3 -m unittest tests/test_macos_host_sme_contract.py tests/test_signing_auth_sme_contract.py tests/test_k8s_node_sme_contract.py tests/test_mcp_setup.py tests/test_claude_agent_guard.py
ls ~/.claude/agents | wc -l                                           # 9 once H2 is installed (6 on 2026-10-21)
ls ~/.claude/mcp-servers 2>/dev/null || echo "removed"                # H5's decision
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py                 # the link, before any large API upload
```

## Documents and git state at handoff

- **Created in this session:**
  - H2: `.claude/agents/macos-host-sme.md`, `.claude/agents/signing-auth-sme.md`, `.claude/agents/k8s-node-sme.md`, `tests/agent_contract_support.py`, `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py`, `tests/test_k8s_node_sme_contract.py`, `util/ad-hoc/2026-10-20_turing_h2_apply.py` and `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py`;
  - H4: `util/mcp_setup.bash`, `tests/test_mcp_setup.py`, `conf/hosts/turing/mcp.json`, `util/ad-hoc/2026-10-21_turing_h4_apply.py` and `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py`;
  - the records: `util/ad-hoc/2026-10-21_turing_h2_h4_record.py`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md` and this file.
- **Modified in this session:**
  - `.github/workflows/ci.yml`, `docs/REFERENCE.md`, `AGENTS.md` (suite count 224; `conf/hosts/<host>/` names `mcp.json`) and `CHANGELOG.md`, by H2, H4 and #2304;
  - `tests/test_ci_host_tooling_macos.py`, `.serena/project.yml` and `.gitignore`, by H4;
  - `tests/test_configure_commit_signing.py` (the audited child runs with `-B`), by #2304;
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (v1.4.3), by #2297; v1.4.4 is "mac dev"'s.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md` (A2-F1, A2-F4);
  - `notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`;
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` (R-S9, K12);
  - `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md`;
  - `util/claude_agent_guard.py`, `util/configure_commit_signing.py`, `util/host_state_check.py`, `conf/hosts/turing/expected.yaml`;
  - `juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`.
- **Worktree:** `.claude/worktrees/linked-floating-sprout`, clean at `fcaf5e0c` before this handoff's PR. Everything landed through the API (`util/open_signed_pr.py`, `util/ad-hoc/2026-10-17_push_signed_with_retry.py`, server-side `update-branch`), and nothing was pushed from the worktree.
- **Host changes:** none persistent. A failed `uvx` build left Serena v1.7.0's dependencies in uv's cache. The test `.mcp.json` was removed.
- **Memory notes:**
  - updated: `turing-host-profile`, `duplicate-handoff-pickup`;
  - new: `serena-intel-mac-cryptography`, `c8-guard-misses-mcp-tools`, `owner-question-latency` and `audit-hook-tests-need-dash-b`.
