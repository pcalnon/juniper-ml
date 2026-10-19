# Handoff — turing Session 2: E6, D5, D6 and H1 done; E2 derived but blocked by Little Snitch; owner steps next

- **From:** the 2026-10-19 session on turing named "mac dev". It continues
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-1-six-code-prs-landed-owner-steps-next.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.2.0. This session's
  record, task status and errata are in its §17. Task IDs below refer to the plan.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2259 | `c92ed76d` | E6. X6: dated corrections in the eight archived handoffs that called turing down or the Pi-pull candidate, and on the P4-27 extraction row. X10: `~/` worktree paths in `AGENTS.md` and `docs/REFERENCE.md`. Also erratum E-CQ, and plan v1.1.1 |
| juniper-ml#2268 | `63358646` | X10 re-applied: #2262 (W5.4) had reverted those six lines through a whole-file upload from an older base (E-LAND-2) |
| the record PR | — | plan v1.2.0 §17, `conf/hosts/turing/conda-envs/`, the E2 and D5 scripts, the D5 evidence, and this file |

## Done on the host (agent)

- **D6:** pre-commit's gitleaks env builds and its hook passes, so `SKIP=gitleaks` is retired on turing.
- **H1:** `~/.claude/agents` and `~/.claude/skills` link to the primary checkout's 6 agents and 3 skills, via `util/install_agents.bash`.
- **D5**, as the owner ruled ("demote"):
  - `~/.bash_profile:87` now reads `export PATH="${HOME}/.local/bin:${PATH}:/opt/local/bin:/opt/local/sbin"`;
  - the backup is `~/.bash_profile.bak-2026-10-19-pre-D5`;
  - the evidence is `reports/2026-10-19_turing-d5-path-inventory/` (128 MacPorts-only commands would have been lost).

## E2: specs derived, envs not created

- `conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml` are ported from each repo's linux-64
  export by `util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py`. All three solve under `mamba --dry-run`.
  - The relaxations are in each header. The main ones are pytorch 2.9.1 → 2.10.0 and MKL 2025.3 → 2023.2.
  - Each header's STATUS line says the env is not yet created.
- **Blocked by per-app outbound filtering (§17.3 E-NET-2).**
  - Miniforge's base `python3.13` (conda's interpreter) and `mamba` time out to conda.anaconda.org and pypi.org.
  - `curl`, `gh` and JuniperPython's `python3.14` reach the same URLs.
  - Little Snitch 5.8 is active. Do **not** route around it (curl downloads, or conda driven by another interpreter):
    that would override the owner's firewall decision.
- **Resume, once the owner has allowed the binaries.** Take one env at a time, in the order cascor, data, canopy:
  1. Run `CONDA_SSL_VERIFY=true /usr/local/miniforge3/bin/mamba env create --override-channels -c conda-forge -f conf/hosts/turing/conda-envs/<Env>.yml --dry-run`, then the same without `--dry-run`.
  2. Run `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data|canopy>`. It does prepare, install and test in one go, with the work dir at `~/.local/state/juniper/turing-e2`. Classify each failure as host-environment or a real env problem; fix the real ones.
  3. Run `/usr/local/miniforge3/condabin/conda env export --no-builds -n <Env>` for the record. Update the spec header's STATUS line, and the E2 row of plan §17.2.
- **Agent findings for the owner to weigh:**
  - cascor's BLAS: MKL is kept, matching the Linux `*_mkl` builds. The alternative is libblas 3.11 with the non-MKL torch.
  - canopy's X11, dbus and nss/nspr packages could be pruned.
  - Upstream drift: cascor's Linux spec pins torch 2.9.1, below the repo's own 2.10.0 floor. canopy's `[test]` extra
    needs newer packaging, coverage and anyio than its spec pins.

## Owner steps

1. **Install the C8 guard.** The primary checkout is 21 commits behind `main` and predates juniper-ml#2242, so pull
   it first:
   ```bash
   cd ~/Development/python/Juniper/juniper-ml && git pull --ff-only origin main
   bash util/install_claude_agent_guard.bash          # prints the entry
   bash util/install_claude_agent_guard.bash --apply  # installs it
   ```
   The hook runs under `/usr/bin/python3` (Xcode's 3.9.6), and the guard's `--self-test` passes 32 of 32 under it.
2. **Little Snitch.** Allow `conda.anaconda.org` for `/usr/local/miniforge3/bin/python3.13` and
   `/usr/local/miniforge3/bin/mamba`. Allow `pypi.org` and `files.pythonhosted.org` for the new envs' interpreters.
   Approving the alerts while a build runs also works. Say when this is done, and the agent resumes E2.
3. **A1**, then check that `python3 util/git_remote_alias_check.py` exits 0:
   ```bash
   ! git -C ~/Development/python/Juniper/juniper-k8s remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git && git -C ~/Development/python/Juniper/juniper-recurrence remote set-url origin git@github_juniper-recurrence:pcalnon/juniper-recurrence.git
   ```
4. **`~/.condarc`:** set `ssl_verify: true`, and trim the seven non-conda-forge channels.
5. **JuniperPython's stray `PYTHONPATH`:** run `conda env config vars unset PYTHONPATH -n JuniperPython`. It is a Python 3.9-era literal
   that leaks into every shell (E-ENV).
6. **The network:**
   - identify the radio that broadcasts your network name with `Security: None` (2.4 GHz ch 10);
   - fix roaming, or use Ethernet on `en7` (F2);
   - reserve turing's address (A6).
7. **F3 node mode:** quit the desktop apps and Docker Desktop, with no VM running, then say so.
8. **The rest of Owner block 1:** C0, A2, A3, B2-B6, C1-C3, C5, C7, E4, A6, F1 and F2.

## Agent next

1. **E2 resume**, after owner step 2.
2. **F3 node mode**, after owner step 7. Append its summary to `reports/2026-10-17_turing-headroom/`.
3. **The rest of the Session 2 group:** G5, G6, G1 and G4, one signed PR each, merged serially.
   - D2-upg and D4 need re-planning under the D6 ruling.
   - A candidate for D4: kubectl 1.36 from conda-forge into `JuniperHostTools`, linked into `~/.local/bin`. That
     directory precedes Docker Desktop's `/usr/local/bin/kubectl`, which would drop D4's dependency on D3.
4. **The Session 3 group:** H2 (three SME agents, then re-run `util/install_agents.bash`), H4, H5, and E5 (which
   needs A6).

## Landing notes (measured this session)

- **Concurrent whole-file uploads can revert merged lines.** #2262 reverted #2259's X10 lines about 50 minutes after
  #2259 merged, and no check flagged it.
  - Re-check `origin/main` after merging a change to a shared file.
  - Keep such edits in an idempotent `util/ad-hoc` script; re-running `util/ad-hoc/2026-10-19_turing_e6_errata.py`
    restored X10 in one two-file PR.
  - The recurrence session was warned by cross-session message, and it saved a memory.
- **A 499 while downloads share the link.** One `createCommitOnBranch` returned HTTP 499 while E2's downloads shared
  the link. `open_signed_pr.py` had already created the branch, empty, at `main`. A re-read of the ref, then
  `util/ad-hoc/2026-10-17_push_signed_with_retry.py` and `gh pr create`, landed it on attempt 1.
- **Foreground `util/safe_merge.py --pr N --execute` worked both times.** For #2259 it did one `update-branch`
  refresh, and #2268 merged directly.

## Verify the starting state

```bash
git fetch origin && git log -1 --oneline origin/main
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/git_remote_alias_check.py                     # exit 1 until A1
jq '.hooks.PreToolUse' ~/.claude/settings.json             # the guard entry appears once C8 is installed
conda env list                                             # the three E2 envs, once resumed
/usr/local/miniforge3/bin/python3.13 -I -c "import urllib.request as u; print(u.urlopen(u.Request('https://conda.anaconda.org/conda-forge/noarch/repodata.json.zst', method='HEAD'), timeout=15).status)"   # 200 once allowed
ls ~/.claude/agents                                        # the 6 agent links (H1)
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py      # the link
```

## Documents and git state at handoff

- **Created in this session's record PR:**
  - `conf/hosts/turing/conda-envs/JuniperCascor1.yml`, `JuniperData.yml` and `JuniperCanopy1.yml`;
  - `util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py`, `util/ad-hoc/2026-10-19_turing_e2_validate_envs.py` and
    `util/ad-hoc/2026-10-19_turing_d5_path_inventory.py`;
  - `reports/2026-10-19_turing-d5-path-inventory/README.md` and `2026-10-19_before-demote.txt`;
  - this file.
- **Modified in it:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, now v1.2.0 with §17.
- **Worktree:** `.claude/worktrees/snuggly-inventing-clover` at `origin/main` plus the record files. Nothing was
  committed locally; everything landed through the API.
- **Host files changed:**
  - `~/.bash_profile`, with a backup;
  - the new `~/.claude/agents/` and `~/.claude/skills/` links;
  - `~/.cache/pre-commit`, which gained the gitleaks env.
