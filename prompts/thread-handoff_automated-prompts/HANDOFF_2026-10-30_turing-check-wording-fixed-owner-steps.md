# Handoff — turing bring-up: the host check's wording fixed (E-H3, "Agent next" item 2); owner steps next

- **From:** the 2026-10-30 session on turing named "t1" (8161e3; worktree `.claude/worktrees/composed-forging-dusk`).
  - The owner pointed it at `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md`.
  - That file had been superseded, so the session continued from the arc's main handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_turing-h3-passed-c8-installed-owner-steps.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.11. §18.3's E-H3 records the fix.
- **This file is the arc's main handoff.** It continues the H3 handoff, which now points here, and carries that file's owner steps forward.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green; this session's start repeated it. It does not cover the `pypi` deployment gate.

## Done this session

| PR | Merge | What |
|---|---|---|
| juniper-ml#2392 | `f1f5938a` | **E-H3's wording follow-up**, the H3 handoff's "Agent next" item 2. `util/host_state_check.py`: G-TOOLS kubectl's fix puts task D3, the owner's Docker Desktop upgrade, before task D4, as decision D7 does; G-MEM's memory message reads "free + speculative + inactive". With it: two `FailureTest` tests, `util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py` (4 of 4), `util/ad-hoc/2026-10-30_turing_check_wording_doc_edits.py` and a CHANGELOG entry |
| this handoff's PR | — | The record: plan v1.4.11 by `util/ad-hoc/2026-10-30_turing_check_wording_record.py`, the H3 handoff's pointer, and this file |

## The fix, in brief

- **kubectl.** On turing, `which -a kubectl` lists only `/usr/local/bin/kubectl`. It links to `/Applications/Docker.app/Contents/Resources/bin/kubectl`, which is v1.22.4, built 2021-11-17. So D3's upgrade replaces the very binary G-TOOLS fails on, and D4's `which -a kubectl` acceptance has to run after D3.
- **memory.** The figure was always vm_stat's free + speculative + inactive pages; only the label changed. `util/macvm_ctl.bash` keeps its own label, because its status block defines "free" as Pages free + Pages speculative.
- **No verdict changed.** The evidence:
  - 63 of 63 tests across the two G1 suites;
  - the wording mutants, 4 of 4, each killed by its own pin test;
  - G1's own mutation check, 57 of 57;
  - the symbol-loss screen, 0 findings.

## State (2026-10-30, about 19:10Z)

- **Readiness: 0 of 7 gates pass**, each failing on the same tasks as on 2026-10-27.
  - G-ALIAS fails on A1: the juniper-k8s and juniper-recurrence origins.
  - G-SIGN fails on the I-SIGN record (K10, then K11).
  - G-SEC fails on C1 (SIP's custom configuration) and C3 (15 key-export or recovery files). The firewall passes (C2).
  - G-TOOLS fails on kubectl v1.22.4: D3, then D4 once it is re-planned under E-D6.
  - G-ENV fails on E4: the parent AGENTS.md is absent.
  - G-NET fails on F2 (`en7` does not exist: the dongle is still absent), on A6, and on the unmeasured iperf3 run.
  - G-MEM fails on memory (5797 MiB of the 10240 MiB required), on swap (2544 MiB, over the 2048 MiB limit) and on Docker Desktop, which is running (F3's node mode; D7).
- **Swap is far lower than before.** The 2026-10-17 headroom run's p50 was 17960 MiB; it is now about 2.5 GiB, 0.5 GiB over G-MEM's limit.
- **VS Code has not run since 2026-03-26** (its newest log directory), so the owner's first Settings Sync upload has not happened. H6's `--check` still holds 8 of 8.
- **The guard is 1.2.0 and installed.** It denies `gh pr create` and `gh api -X`. Agents land through `util/open_signed_pr.py` and merge with `util/safe_merge.py`.
- **H5's option B is intact:** the hardening check exited 0. B.5 is still pending for both trees.
- **C0** still reports `[Included]`.
- **The link** (2026-10-30): Wi-Fi on 2.4 GHz channel 5, SNR 30 dB, with 0% loss to the gateway; `en0` is now 192.168.50.222 (DHCP). juniper-ml#2392's five files, about 400 KB, landed through the API on the first attempt.

## Owner steps

1. **D11 item 5.** In a real terminal, run `gh auth status`. Then give agent sessions item 5's fine-grained PAT: the 10 Juniper repos, Contents and Pull requests read/write, Metadata read, no Administration.
2. **H6's, carried forward:**
   - rotate the Hugging Face token;
   - open VS Code on turing once, so that Settings Sync uploads the change; keep the local version on a conflict;
   - optionally, the H6 audit's §8.5 resets.
3. **K13, which comes first in the signing chain** and is also needed before Context7 or Hugging Face is used. Delete VS Code's `"/.*/"`, `"xargs"` and the fragment keys, and Amp's rules 28 and 39; set Cursor to Allowlist with the sandbox on.
4. **The signing chain**, then K10: S11/S12, K8, K6, K7 and K9, in the order and with the guards that the signing report's OWNER command list gives (`reports/2026-10-27_turing-bringup/2026-10-27T0139Z_signing-auth-sme.md` §6). No YubiKey goes into turing until K13 is done; C8 and K12 are done.
5. **Transport.** A1's two remote rewrites, then A2's deploy-key comparison and A3's auth matrix, as that same list gives them.
6. **The network:**
   - F2: re-attach the `en7` dongle and get a 1000baseT link;
   - A6: a DHCP reservation;
   - iperf3 to yamaguchi.
7. **D3, Docker Desktop's upgrade** to the current stable, with the version recorded and the memory capped at 3 GiB. G-TOOLS's kubectl fix now names it first, because the upgrade replaces Docker Desktop's `/usr/local/bin/kubectl`. D4 (AGENT) follows it.
8. **The k8s audit's questions**, F1's D1 ruling first: `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md`, "Open questions for the owner". Question 5 asks whether to split E5 so that X1, X2 and X5 land now.
9. **Unchanged:**
   - B.4, a standing Little Snitch rule for the Cellar `node`;
   - B.5, `git remote remove origin` in each H5 tree, from a separate terminal;
   - C0's `tmutil addexclusion ~/.claude/mcp-servers`, then the backup;
   - C1 and C3; E4;
   - `~/.condarc` `ssl_verify: true`; the JuniperPython `PYTHONPATH` unset;
   - F3 node mode;
   - E-H4-WHEEL's route, now free of H6.

## Agent next

1. **After the owner's first VS Code sync:** re-run `python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check`, which should hold 8 of 8.
2. **After D3:** D4 (AGENT), once it is re-planned under the D6 ruling (E-D6). Its acceptance is that `which -a kubectl` lists the 1.36 binary first, so check it after D3's upgrade has rewritten the Docker Desktop link.
3. **E5's split, if the owner agrees with the audit's question 5(a):** land X1, X2, X5 (and X9) in juniper-k8s through `python3 util/open_signed_pr.py --repo juniper-k8s`. X3 and X4 wait on A6.
4. **H3's upstream half, if the owner wants it** (the audit's question 10): re-run `k8s-node-sme`'s items 2-4 from a session that can WebFetch kubernetes.io.
5. **After K10:** K11 records the I-SIGN matrix and fills in G-SIGN.integration.
6. **After E-H4-WHEEL:** H4's live check, `timeout 30 claude mcp list`.
7. **After B.5:** re-run `python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py`, and record B.4 and B.5.
8. **F7** (AGENT, P2), if the owner wants it before F4. Its design notes are in the c2-applied handoff, and the k8s audit's question 7 bears on its acceptance.
9. **If juniper-ml#2360 lands** (DIRTY since 2026-10-27; it edits `util/host_state_probe.bash` and `tests/test_host_state_probe.py`, which the G1 mutation engine stages), re-run `python3 util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` and the wording one. An anchor it moves exits 2.
10. **Before numbering the next plan revision,** check for an open turing plan PR: `gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh pr list --repo pcalnon/juniper-ml --state open --search "turing in:title"
python3 -I util/claude_agent_guard.py --version                                   # juniper-agent-guard 1.2.0
python3 util/host_state_check.py | tail -1                                        # readiness: 0 of 7 (re-measure; values move)
python3 util/host_state_check.py --section G-TOOLS                                # the kubectl fix names task D3 first
python3 -I util/ad-hoc/2026-10-21_turing_h5_hardening_check.py --offline          # exit 0: option B intact
python3 -I util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py --check # 8 of 8 hold
python3 -I util/ad-hoc/2026-10-30_turing_check_wording_record.py --pr 2392 --sha f1f5938a --dry-run   # every edit "present"
python3 -I util/ad-hoc/2026-10-30_turing_check_wording_doc_edits.py --check --mutants 4/4 --g1 57/57   # nothing to do
```

## Documents and git state at handoff

- **Created in this session:**
  - `util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py`;
  - `util/ad-hoc/2026-10-30_turing_check_wording_doc_edits.py`;
  - `util/ad-hoc/2026-10-30_turing_check_wording_record.py`;
  - this file.
- **Modified in this session:**
  - `util/host_state_check.py`, `tests/test_host_state_check.py` and `CHANGELOG.md` (juniper-ml#2392);
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, to v1.4.11;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_turing-h3-passed-c8-installed-owner-steps.md`, given a pointer here.
- **Referenced, not changed:**
  - `reports/2026-10-27_turing-bringup/2026-10-27T0135Z_macos-host-sme.md` (findings 3 and 4) and `reports/2026-10-27_turing-bringup/README.md` (item 6);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md`;
  - `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py`, `util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py`, `util/ad-hoc/2026-10-27_turing_h3_record.py` and `util/macvm_ctl.bash`;
  - `docs/REFERENCE.md`, whose entries for the check and its suite stay true.
- **Worktree:** `.claude/worktrees/composed-forging-dusk`. Nothing was pushed from it; everything landed through the API (`util/open_signed_pr.py`, `util/safe_merge.py`). The symbol-loss pre-flight used one local commit object, made with `git commit-tree` on no branch and never pushed.
- **Host changes:** none. This session only read the host: the probe and the check, the network probe without load, `which -a kubectl`, VS Code's log directory names and `tmutil isexcluded`.
- **Memory notes:** `turing-host-profile` (the wording fix; the 2026-10-30 state).
