# Handoff — turing bring-up: G1 landed, G4 promoted; H2 next (the owner splits the arc first)

- **From:** the 2026-10-20 session on turing named "code signing". It continued from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-session-3-final-e2-validated-g1-next.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.2. This session's record is in §18.2 (the G1 and G4 rows) and §18.3 (errata E-G1 and E-DUP). Task IDs below are the plan's.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover the `pypi` deployment gate.
- **Coordination.** Two sessions picked up the previous handoff (E-DUP). The "mac dev env" session closed its G1 PR, juniper-ml#2288, as superseded. It has stood down on this arc and is waiting for the owner to split the remaining items between the sessions. **Ask the owner which session takes H2, H4 and H5 before starting any of them.**

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2287 | `e3ba1936` | G1: `util/host_state_probe.bash` (collector), `util/host_state_check.py` (seven of the ten §9.3 gates), `conf/hosts/turing/expected.yaml`, 54 tests, 57 of 57 mutants killed |
| juniper-ml#2289 | `5a383ae1` | G4's promotion: `host-tooling-macos` is a hard Quality Gate need after 12 consecutive green push runs; the "mac dev env" session drafted its apply script |
| the record PR | — | plan v1.4.2, `util/ad-hoc/2026-10-20_turing_g1_g4_record.py`, and this file |

## The readiness measure

`python3 util/host_state_check.py` is the readiness report. Add `--check` to get I-G1's exit code, `--json` for one object, and `--section G-MEM` to evaluate a single gate. On 2026-10-20, 0 of 7 gates passed:

| Gate | Fails on | Task |
|---|---|---|
| G-ALIAS | the juniper-k8s and juniper-recurrence origins | A1 (owner) |
| G-SIGN | no I-SIGN record | signing plan K10 after B2/B3 (owner), recorded by K11 |
| G-SEC | SIP in a custom configuration, firewall off, 15 key-export files | C1, C2, C3 (owner) |
| G-TOOLS | kubectl v1.22.4 | D4 (re-plan under D6) |
| G-ENV | the parent `AGENTS.md` is absent | E4 (owner) |
| G-NET | en7 with no carrier, no reserved address, no iperf3 record | F2, A6 (owner) |
| G-MEM | memory headroom, swap, Docker Desktop running | F3 node mode, D7 |

A `null` record in `expected.yaml` is filled in by the PR that closes its task:

- `gates.G-SIGN.integration`: K11;
- `gates.G-ENV.parent_agents_md.sha256`: E4;
- `gates.G-NET.reserved_ip`: A6;
- `gates.G-NET.throughput`: F2.

Each `record` path points at a file under `reports/`, which the check confirms exists.

## Owner steps (unchanged from the previous handoff, plus the records)

1. **C8:** fast-forward the primary checkout (`git pull --ff-only origin main`), then run `bash util/install_claude_agent_guard.bash --apply`. That installs guard 1.1.0 with K12's rules.
2. **A1:** rewrite the juniper-k8s and juniper-recurrence remotes, then confirm that `python3 util/git_remote_alias_check.py` exits 0. Then opt in with `pre-commit install --hook-type pre-push`.
3. **`~/.condarc`:** set `ssl_verify: true` (closes E-SSL), and trim the seven non-conda-forge channels.
4. **JuniperPython's env:** run `conda env config vars unset PYTHONPATH -n JuniperPython`.
5. **The network:** the open-security radio, roaming or `en7` (F2), and A6.
6. **F3 node mode:** quit the desktop apps and Docker Desktop, with no VM running, then say so.
7. **Commit signing (§19):** no YubiKey goes into turing until C8 and K12 are installed and K13 is done.
8. **The rest of Owner block 1:** C0, A2, A3, B2–B6, C1–C3, C5, C7, E4, A6, F1 and F2.
9. **After each block:** run `python3 util/host_state_check.py`.

## Agent next (after the owner's split)

1. **H2:** the three SME agents of plan §11 (`macos-host-sme`, `signing-auth-sme`, `k8s-node-sme`).
   - Each needs `tests/test_agents_frontmatter.py` to stay green and its own `tests/test_<agent>_contract.py`, on the pattern of `tests/test_fleet_supervisor_contract.py`.
   - After the merge, re-run `util/install_agents.bash` from a clean `main` to get 9 symlinks.
   - `macos-host-sme` measures with `util/host_state_check.py --json`.
2. **H4** (`util/mcp_setup.bash`, Serena pinned, D10) and **H5** (the `auditor` agent on the two unvetted `~/.claude/mcp-servers/` entries).
3. **F3 node mode**, after owner step 6.
4. **E5** waits on A6. D2-upg and D4 still need re-planning under the D6 ruling.
5. **Post-merge check (E-LAND-2).** About an hour after the last merge, re-run these against `main`:
   - `python3 -I util/ad-hoc/2026-10-20_turing_g1_apply.py --dry-run`;
   - `python3 -I util/ad-hoc/2026-10-20_turing_g4_promote_apply.py --dry-run`;
   - `python3 -I util/ad-hoc/2026-10-20_turing_g1_g4_record.py --dry-run`.

   Each should report every edit `present`. The previous session's `util/ad-hoc/2026-10-20_turing_e2_record.py --dry-run` now reports its §18.2 G1 row `MISSING`. That is by design, because v1.4.2 replaced the row. Its other edits stay `present`.

## Verify the starting state

```bash
git fetch origin && git log -5 --oneline origin/main
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/host_state_check.py                                  # the readiness report (0 of 7 on 2026-10-20)
python3 -I util/ad-hoc/2026-10-20_turing_g1_apply.py --dry-run     # every edit present
python3 -I util/ad-hoc/2026-10-20_turing_g4_promote_apply.py --dry-run
python3 -I util/ad-hoc/2026-10-20_turing_g1_g4_record.py --dry-run
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py              # the link, before any large API upload
```

## Documents and git state at handoff

- **Created in this session:**
  - G1 (#2287): `util/host_state_probe.bash`, `util/host_state_check.py`, `conf/hosts/turing/expected.yaml`, `tests/test_host_state_probe.py`, `tests/test_host_state_check.py`, `util/ad-hoc/2026-10-20_turing_g1_apply.py` and `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py`;
  - the promotion (#2289): `util/ad-hoc/2026-10-20_turing_g4_promote_apply.py`;
  - the record PR: `util/ad-hoc/2026-10-20_turing_g1_g4_record.py` and this file.
- **Modified in this session:**
  - `.github/workflows/ci.yml`, `docs/REFERENCE.md` and `CHANGELOG.md`, by G1 and the promotion;
  - `AGENTS.md` (suite count 220, a Key Files pointer to `conf/hosts/<host>/`) and `util/ad-hoc/2026-10-15_turing_host_state_probe.bash` (the graduation note), by G1;
  - `tests/test_ci_host_tooling_macos.py`, by G1 and the promotion;
  - `tests/test_ci_quality_gate.py`, by the promotion;
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (v1.4.2), by the record PR.
- **Referenced, not changed:** `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` (K10/K11 produce the I-SIGN record), `util/macvm_ctl.bash` (G-MEM's arithmetic), and `conf/hosts/turing/hosttools-environment.yml` and `conf/hosts/turing/conda-envs/*.yml` (pinned by the check's suite).
- **Worktree:** `.claude/worktrees/robust-jumping-moler`. Nothing was committed locally: everything landed through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`).
- **Host changes:** none.
- **Memory notes:** `turing-host-profile` (G1 landed; readiness 0 of 7). The "mac dev env" session added `bash32-background-exec-and-patsub-traps` and `duplicate-handoff-pickup`.
