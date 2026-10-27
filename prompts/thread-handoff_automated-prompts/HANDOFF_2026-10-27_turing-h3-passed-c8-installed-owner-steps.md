# Handoff — turing bring-up: H3 passed (3 of 3 agree, 3 of 3 denials) once the owner installed C8; owner steps next

- **From:** the 2026-10-26/27 session on turing named "cached-enchanting-cosmos-84" (760fde; worktree `.claude/worktrees/cached-enchanting-cosmos`), which the user later renamed "c2-applied-gate-reads-getter-sentence".
  - It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`.
  - "c9-landed-h6-audited-owner-decides" (bd4cfc) continued from that file too and applied H6 (plan v1.4.9). The two sessions split the work by cross-session message: H3 here, H6 there.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.10. §18.2 holds the C8, H2, C9 and H3 rows, and §18.3 erratum E-H3.
- **This file is the arc's main handoff.** It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md`, which now points here, and carries that file's owner steps forward.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green; this session's start repeated it. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2374 | `0584d43f` | **H3's evidence.** `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md`; the record `reports/2026-10-27_turing-bringup/README.md`, with the two agent reports and `h3-evidence/`; the three validated prompts under `prompts/generated/`; and `util/ad-hoc/2026-10-27_turing_h3_compare.py` |
| this handoff's PR | — | The record: plan v1.4.10 by `util/ad-hoc/2026-10-27_turing_h3_record.py`, the H6 handoff's pointer, and this file |

## H3, in brief

- **The owner installed C8** on 2026-10-26, at about 22:30Z: the pull, the guard installer, and `install_agents.bash` (9 links at 22:32Z).
- **C8's acceptance** was checked here at 2026-10-27T00:22Z:
  - `commit.gpgsign` is `false`;
  - `cat ~/.ssh/config` was denied (CRED-PATH-BASH);
  - `gh api -X POST …` was denied (GH-API-WRITE);
  - a `.mcp.json` mention was denied (MCP-REGISTER-BASH), so the installed guard is 1.2.0.
- **The task prompts.** Each agent ran one scripted task from a prompt that passed RUBRIC through `prompt-validator`. Two prompts failed earlier rounds and passed in round 3 of 3.
- **3 of 3 agree, with no contradiction:**
  - `macos-host-sme` on all 7 gates, 77 s from an independent probe;
  - `signing-auth-sme` on G-ALIAS and G-SIGN, 174 s from one;
  - `k8s-node-sme` on X1-X5, against the current juniper-k8s lines.
- **3 of 3 denials**, read from each agent's transcript:
  - `cat ~/.ssh/config`;
  - `gh api -X POST markdown …`;
  - a `Read` of a `~/.ssh` sentinel. The settings deny rule refused this one, not the guard.

## What H3 found (erratum E-H3)

- **D11 item 5 does not hold.** The agent token can read deploy keys: HTTP 200, where item 5's token gets 403.
- **juniper-k8s is private.** So it has no rulesets and no `required_signatures`.
- **The `en7` dongle is gone.** macOS shows no interface with its MAC.
- **WebFetch to kubernetes.io timed out.** All six fetches did, while `curl` reached the site, so the k8s audit's comparison with upstream is "could not verify".
- **The check's wording.** `util/host_state_check.py`'s G-TOOLS `kubectl` remediation omits D3, and G-MEM's "free + inactive" figure also counts speculative pages.
- **The k8s audit** holds 14 findings: 6 major and 8 minor, with 10 owner questions. Its majors:
  - no reservation values exist for the 6 GiB node;
  - no taint step exists, nor F6's `nd-*` macvm script;
  - the VM, as written, has no route out and no admin path;
  - the primer's autostart bypasses G-MEM;
  - X1-X5 are open.

## State (2026-10-27, 02:10Z)

- **Readiness: 0 of 7 gates pass.**
  - G-ALIAS fails on A1.
  - G-SIGN fails on the I-SIGN record (K10, then K11).
  - G-SEC fails on C1 and C3.
  - G-TOOLS fails on D4, which waits on D3 and a re-plan under E-D6.
  - G-ENV fails on E4.
  - G-NET fails on F2 (the dongle is absent) and A6.
  - G-MEM fails on node mode (F3) and on Docker Desktop.
- **G-AGENT holds** (H2's suites; H3's denials).
- **The guard is 1.2.0 and installed.** Agents land only through `util/open_signed_pr.py`. It denies `gh pr create`, `gh api -X`, any mention of `~/.ssh` or `~/.gnupg` in a Bash command, and any mention of `.mcp.json`.
- **H6 is applied** (v1.4.9). The token's rotation and the first VS Code sync are the owner's.
- **H5's option B is intact.** The hardening check exited 0 at 00:17Z; B.5 is still pending.
- **C0** still reports `[Included]` (02:09Z).

## Owner steps

1. **D11 item 5.** In a real terminal, run `gh auth status`. Then give agent sessions item 5's fine-grained PAT: the 10 Juniper repos, Contents and Pull requests read/write, Metadata read, no Administration.
2. **H6's, carried forward from the H6 handoff:**
   - rotate the Hugging Face token;
   - open VS Code on turing once, so that Settings Sync uploads the change; keep the local version on a conflict;
   - optionally, the H6 audit's §8.5 resets.
3. **K13, which comes first in the signing chain** and is also needed before Context7 or Hugging Face is used. Delete VS Code's `"/.*/"`, `"xargs"` and the fragment keys, and Amp's rules 28 and 39; set Cursor to Allowlist with the sandbox on.
4. **The signing chain**, then K10: S11/S12, K8, K6, K7 and K9, in the order and with the guards that the signing report's OWNER command list gives (`reports/2026-10-27_turing-bringup/2026-10-27T0139Z_signing-auth-sme.md` §6). No YubiKey goes into turing until K13 is done; C8 and K12 are done now.
5. **Transport.** A1's two remote rewrites, then A2's deploy-key comparison and A3's auth matrix, as that same list gives them.
6. **The network:**
   - F2: re-attach the `en7` dongle and get a 1000baseT link;
   - A6: a DHCP reservation;
   - iperf3 to yamaguchi.
7. **The k8s audit's questions**, F1's D1 ruling first: `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md`, "Open questions for the owner". Question 5 asks whether to split E5 so that X1, X2 and X5 land now.
8. **Unchanged:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers`, then the backup;
   - C1 and C3; E4; D3;
   - `~/.condarc` `ssl_verify: true`; the JuniperPython `PYTHONPATH` unset;
   - F3 node mode;
   - E-H4-WHEEL's route, now free of H6.

## Agent next

1. **After the owner's first VS Code sync:** re-run `python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check`, which should hold 8 of 8.
2. **The check's wording (AGENT, no owner step):** in `util/host_state_check.py`, G-TOOLS `kubectl`'s remediation should name D3, and G-MEM's message should say what its figure counts. Re-run G1's mutation check, and the C2 one if G-SEC is touched.
3. **E5's split, if the owner agrees with the audit's question 5(a):** land X1, X2, X5 (and X9) in juniper-k8s through `python3 util/open_signed_pr.py --repo juniper-k8s`. X3 and X4 wait on A6.
4. **H3's upstream half, if the owner wants it** (the audit's question 10): re-run `k8s-node-sme`'s items 2-4 from a session that can WebFetch kubernetes.io.
5. **After K10:** K11 records the I-SIGN matrix and fills in G-SIGN.integration.
6. **After E-H4-WHEEL:** H4's live check, `timeout 30 claude mcp list`.
7. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5.
8. **F7** (AGENT, P2), if the owner wants it before F4. Its design notes are in the c2-applied handoff, and the k8s audit's question 7 bears on its acceptance.
9. **Before numbering the next plan revision,** check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/claude_agent_guard.py --version                                   # juniper-agent-guard 1.2.0
python3 util/host_state_check.py | tail -1                                        # readiness: 0 of 7 (re-measure; values move)
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline          # exit 0: option B intact
python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check # 8 of 8 hold
python3 -I util/ad-hoc/2026-10-27_turing_h3_record.py --h3-pr 2374 --h3-sha 0584d43f --dry-run   # every edit "present"
```

## Documents and git state at handoff

- **Created in this session:**
  - `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md`, written by the `k8s-node-sme` agent; one marked correction to finding 4-A was made before landing;
  - `reports/2026-10-27_turing-bringup/README.md`, and its two agent reports;
  - under that directory's `h3-evidence/`: `prompt-validation.md`, the two `compare_*.json`, the two `independent-check_*.json` and the three `denials_*.json`;
  - `prompts/generated/JUNIPER_ML_TURING-H3-MACOS-HOST-SME_AUDIT_2026-10-27_0121.md`, `prompts/generated/JUNIPER_ML_TURING-H3-SIGNING-AUTH-SME_AUDIT_2026-10-27_0121.md` and `prompts/generated/JUNIPER_ECOSYSTEM_TURING-H3-K8S-NODE-SME_AUDIT_2026-10-27_0121.md`;
  - `util/ad-hoc/2026-10-27_turing_h3_compare.py` and `util/ad-hoc/2026-10-27_turing_h3_record.py`;
  - this file.
- **Modified in this session:**
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.10;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md`, given a pointer here.
- **Referenced, not changed:**
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` (K6-K13, §10.2, §13);
  - `.claude/agents/macos-host-sme.md`, `.claude/agents/signing-auth-sme.md`, `.claude/agents/k8s-node-sme.md` and `.claude/agents/prompt-validator.md`;
  - `prompts/agent_templates/RUBRIC.md`, `prompts/agent_templates/generic.md` and `prompts/agent_templates/audit.md`;
  - `util/claude_agent_guard.py`, `util/install_claude_agent_guard.bash`, `util/host_state_check.py`, `util/host_state_probe.bash` and `conf/hosts/turing/expected.yaml`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md`;
  - juniper-k8s at `6ee35441`: its primer, `inventory/hosts.yaml` and `util/node_scripts/testing/hosts`.
- **Worktree:** `.claude/worktrees/cached-enchanting-cosmos`. Nothing was committed locally; everything landed through the API (`util/open_signed_pr.py`, `util/safe_merge.py`).
- **Host changes:** none. The agents and this session only read the host: the probe and the check, `ssh -G`, `git config` reads, plain `gh api` GETs, and `tmutil isexcluded`.
- **Memory notes:** `turing-host-profile` (C8 installed; H3 passed).
