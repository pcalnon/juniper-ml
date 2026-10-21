# Handoff — turing bring-up: H2 and H4 landed; C9 next (H4's live check waits on a Rust toolchain)

- **From:** the 2026-10-20/21 session on turing named "code signing" (ae687e; worktree `.claude/worktrees/linked-floating-sprout`). It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.3. This session's record is in §18.1 (two owner rulings), §18.2 (the H2, H4, C9 and H5 rows) and §18.3 (errata E-SPLIT, E-H4-WHEEL and E-SERENA-EDIT). Task IDs below are the plan's.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.
- **Coordination.** The owner gave H2 and H4 to this session and H5 to the "mac dev" session (37a935). "mac dev" later received a different answer, all three for itself. Both sessions kept the first split, and the owner was told (E-SPLIT).
  - "mac dev" is doing H5, one `notes/` audit. It will write H5's record itself, as plan v1.4.4, after checking for an open turing plan PR. It will also message any next session on this arc, so H5 is not recorded twice. The audit marks any server it would enable that has file-writing tools as falling under C9.
  - Run `ListAgents` and `gh pr list --repo pcalnon/juniper-ml --state all --search "<task>"` before starting any task here.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2294 | `b16121ac` | H2: `.claude/agents/{macos-host-sme,signing-auth-sme,k8s-node-sme}.md`. Three contract suites share `tests/agent_contract_support.py` (49 tests). Each runs `util/claude_agent_guard.py` on every Must-never item: 43 denials under the cited rules and 25 procedure calls passed. 28 of 28 mutants killed (`util/ad-hoc/2026-10-20_turing_h2_mutation_check.py`) |
| juniper-ml#2295 | `a005063e` | H4: `util/mcp_setup.bash`, with the pin in `conf/hosts/turing/mcp.json` (Serena v1.7.0 `949a27ef1e5fda1a6e7b561e777bcece345c6ffd`, claude-code context). `.serena/project.yml` excludes `execute_shell_command`, and `.gitignore` covers `.mcp.json.bak-*`. `tests/test_mcp_setup.py` has 35 tests, also on `host-tooling-macos`. 20 of 20 mutants killed (`util/ad-hoc/2026-10-21_turing_h4_mutation_check.py`) |
| the record PR | — | plan v1.4.3, `util/ad-hoc/2026-10-21_turing_h2_h4_record.py`, and this file |

## Owner decisions and steps

1. **E-H4-WHEEL: Serena does not start on turing yet.**
   - Serena v1.7.0 pins `cryptography==50.0.0` exactly, and cryptography has no Intel-macOS wheel from 49 on. Building it needs Rust 1.83; turing's rustup default is 1.71.0.
   - Choose one:
     - (a) install a Rust 1.83+ toolchain beside 1.71 and build once (the command is in §18.3);
     - (b) pin Serena v1.6.1, whose cryptography 48.0.1 has wheels but CVE-2026-69247, -69248 and -69249;
     - (c) keep Serena off turing.
   - H4's live check (`timeout 30 claude mcp list` shows serena connected) waits on this.
2. **C8 step 1, then H2's install.** Fast-forward the primary checkout (`git pull --ff-only origin main`); it is still at 6 agents. Then run `bash util/install_agents.bash` from it, which should give 9 agent links (H2's acceptance). The C8 guard install (`bash util/install_claude_agent_guard.bash --apply`) is the same owner step.
3. **E-SPLIT:** confirm the split, or overrule it.
4. **Unchanged from the previous handoff:**
   - A1 (rewrite the two remotes, then `pre-commit install --hook-type pre-push`);
   - `~/.condarc` `ssl_verify: true`;
   - `conda env config vars unset PYTHONPATH -n JuniperPython`;
   - the network (F2, A6);
   - F3 node mode;
   - commit signing (§19): no YubiKey into turing until C8 and K12 are installed and K13 is done;
   - the rest of Owner block 1.

   After each block, run `python3 util/host_state_check.py`; it read 0 of 7 on 2026-10-20.

## Agent next

1. **C9** (new; H3 waits on it): extend `util/claude_agent_guard.py` to MCP file-writing tools (E-SERENA-EDIT).
   - **The matcher.** The installed settings matcher is `Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob`. `util/install_claude_agent_guard.bash` writes it, so the matcher must grow to name the Serena tools (`mcp__serena__...`).
   - **The tools.** At v1.7.0 they are `replace_content`, `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol`, `replace_in_files`, the optional `delete_lines` / `replace_lines` / `insert_at_line`, and the memory writers.
   - **The paths.** Serena's paths are `relative_path` values against its `--project` root, which is the checkout. Deny a call that resolves into `.git/`, `~/.ssh`, `~/.gnupg` or the Claude settings. An unknown MCP tool must keep passing silently, as the guard's contract says.
   - **Tests and install.** Add tests in `tests/test_claude_agent_guard.py`, plus a mutation check on the C8 and K12 pattern. The owner re-installs the guard.
2. **H3**, after C8 is installed, C9 has landed and H2's agents are installed. Each agent runs one scripted task on turing, compared against a `util/host_state_probe.bash --json` run taken within ±10 minutes, plus one negative test. The task prompts go through `prompt-validator`.
3. **H4's live check**, once E-H4-WHEEL is resolved:
   - `bash util/mcp_setup.bash` in the primary checkout;
   - pre-warm with `uvx --from git+https://github.com/oraios/serena@949a27ef1e5fda1a6e7b561e777bcece345c6ffd serena --version`;
   - then `timeout 30 claude mcp list`.
4. **H5's record is "mac dev"'s:** it writes v1.4.4. Number any later revision after that one lands, and check for an open turing plan PR first.
5. F3 node mode follows owner step 6. E5 waits on A6. D2-upg and D4 still need re-planning under the D6 ruling.
6. **Post-merge check (E-LAND-2).** About an hour after the last merge, re-run each of these against `main`. Each should report every edit `present`:
   - `python3 -I util/ad-hoc/2026-10-20_turing_h2_apply.py --dry-run`;
   - `python3 -I util/ad-hoc/2026-10-21_turing_h4_apply.py --dry-run`;
   - `python3 -I util/ad-hoc/2026-10-21_turing_h2_h4_record.py --dry-run`.

   G1's and G4's apply scripts still report every edit present too: H4 kept their markers. Two expected deviations, neither of them a revert:

   - The v1.4.2 record script, `util/ad-hoc/2026-10-20_turing_g1_g4_record.py`, reports its Version-line edit `MISSING` ("the plan is at neither 1.4.1 nor 1.4.2"). That is by design: v1.4.3 replaced the line. Its other edits stay `present`.
   - On a later UTC day, an apply script that touches AGENTS.md also reports `would change ... AGENTS.md`. That is only the **Last Updated** date.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/host_state_check.py                                    # the readiness report
python3 -I util/ad-hoc/2026-10-20_turing_h2_apply.py --dry-run       # every edit present
python3 -I util/ad-hoc/2026-10-21_turing_h4_apply.py --dry-run
python3 -I util/ad-hoc/2026-10-21_turing_h2_h4_record.py --dry-run
python3 -m unittest tests/test_macos_host_sme_contract.py tests/test_signing_auth_sme_contract.py tests/test_k8s_node_sme_contract.py tests/test_mcp_setup.py
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py                # the link, before any large API upload
```

## Documents and git state at handoff

- **Created in this session:**
  - H2: `.claude/agents/macos-host-sme.md`, `.claude/agents/signing-auth-sme.md`, `.claude/agents/k8s-node-sme.md`, `tests/agent_contract_support.py`, `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py`, `tests/test_k8s_node_sme_contract.py`, `util/ad-hoc/2026-10-20_turing_h2_apply.py` and `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py`;
  - H4: `util/mcp_setup.bash`, `tests/test_mcp_setup.py`, `conf/hosts/turing/mcp.json`, `util/ad-hoc/2026-10-21_turing_h4_apply.py` and `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py`;
  - the record PR: `util/ad-hoc/2026-10-21_turing_h2_h4_record.py` and this file.
- **Modified in this session:**
  - `.github/workflows/ci.yml`, `docs/REFERENCE.md`, `AGENTS.md` (suite count 224; `conf/hosts/<host>/` names `mcp.json`) and `CHANGELOG.md`, by H2 and H4;
  - `tests/test_ci_host_tooling_macos.py`, `.serena/project.yml` and `.gitignore`, by H4;
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (v1.4.3), by the record PR.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md` (A2-F1, A2-F4);
  - `notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`;
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`;
  - `util/claude_agent_guard.py`, `util/host_state_check.py`, `conf/hosts/turing/expected.yaml`;
  - `juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`.
- **Worktree:** `.claude/worktrees/linked-floating-sprout`. Nothing was pushed from it: everything landed through the API (`util/open_signed_pr.py`, `util/ad-hoc/2026-10-17_push_signed_with_retry.py`). A local WIP commit used to move the worktree onto a newer `main` was unwound with `git reset --soft`, never pushed.
- **Host changes:** none persistent.
  - A uvx build attempt left Serena v1.7.0's downloaded dependencies in uv's cache (`~/.cache/uv`), without the failed cryptography build.
  - The worktree's test `.mcp.json` was removed.
- **Memory notes:**
  - updated: `turing-host-profile`, `duplicate-handoff-pickup`;
  - new: `serena-intel-mac-cryptography`, `c8-guard-misses-mcp-tools` and `owner-question-latency`.
