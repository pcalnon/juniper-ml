# Handoff — turing Session 3, final: G5, G6 and G4 landed; E2 validated (all three envs); G1 next

- **From:** the 2026-10-19/20 session on turing named "mac dev env". It continues
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-2-e6-d5-d6-h1-done-e2-blocked-on-little-snitch.md`,
  and supersedes this session's earlier handoff,
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-session-3-g5-g6-g4-landed-e2-two-envs-created-pypi-blocked.md`,
  which was written before E2 finished.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.4.1. This session's
  record, task status and errata are in its §18; §19 is the "code signing" session's. Task IDs below refer to the plan.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover
  the `pypi` deployment gate.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2272 | `a5311979` | G5: `util/home_path_literal_check.py` (the G-PATH gate) and `conf/home_path_literal_baseline.json` |
| juniper-ml#2274 | `223d09a7` | G6: the `git-remote-alias` pre-push hook, `default_stages: [pre-commit]` and a CI smoke step |
| juniper-ml#2276 | `3968ca04` | G4: ci.yml's advisory `host-tooling-macos` job, gated by `tests/test_ci_host_tooling_macos.py` |
| juniper-ml#2277 | `3aac025f` | the Session 3 record: plan v1.3.0 §18, the E-SSL spec-header fixes, the first two E2 exports |
| the E2 record PR | — | plan v1.4.1 (§18.2's E2 row; errata E-BLAS and E-REQ), the three spec STATUS paragraphs, JuniperCanopy1's MKL spec, `reports/2026-10-20_turing-e2-envs/`, and this file |

The "code signing" session's juniper-ml#2280 (`fd48ca5c`, plan §19 and v1.4.0) merged in between. After it, dry runs of
`util/ad-hoc/2026-10-20_turing_g{5,6,4}_apply.py` on `fd48ca5c` reported all 25 blocks `present` (E-LAND-2).

## E2: done

All three envs were created with `MAMBA_SSL_VERIFY=true` and validated against their repos' CI lanes by
`python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data|canopy>`:

| Env | Unit lane | Integration lane |
|---|---|---|
| JuniperCascor1 | 5777 of 5777 passed (coverage 96.55%) | 172 of 172 |
| JuniperData | 2201 passed, 3 skipped (GNU `base64`/`date`), of 2204 (97.82%) | 62 of 62 |
| JuniperCanopy1 | 7947 passed, 10 skipped, 2 failed, of 7959 (96.68%) | 523 passed, 79 skipped, of 602 |

- **E-BLAS.** The first JuniperCanopy1 (OpenBLAS 0.3.30 under `cpu_generic` torch) hung canopy's unit lane at the same
  test twice, with three threads spinning in OpenBLAS's `blas_memory_alloc`. `OMP_NUM_THREADS=6` made the lane finish,
  so the trigger is threads with different OpenMP counts. The spec now takes the MKL variant (`libblas` 3.9.0
  `20_osx64_mkl`, `mkl` 2023.2.0, `cpu_mkl` torch), and the env was re-created from it. Evidence:
  `reports/2026-10-20_turing-e2-envs/JuniperCanopy1.openblas-hang.txt`.
- **E-REQ.** canopy's 2 failures assume `requests` refuses a header value with a trailing LF, which it does from 2.33.1.
  The spec keeps the Linux env's 2.32.5, and canopy floors `requests>=2.28.0`. Not a turing defect.
- **juniper-canopy follow-ups (owner's call, not filed):** raise the `requests` floor to 2.33.1, and stop the tests that
  leave demo mode's `_training_loop` thread running.
- `validate_envs.py` gained `--env KEY=VALUE` for experiments; the summary JSON and lane logs record any override.

## Owner steps

1. ~~**Little Snitch**~~: done; the env pythons reach PyPI.
2. **Install the C8 guard, now that K12 is on `main`:** the "code signing" session's juniper-ml#2281 (`188e842e`, `claude_agent_guard` 1.1.0, which adds the signing-config rules) has merged. Fast-forward the primary checkout (`git pull --ff-only origin main`) and run `bash util/install_claude_agent_guard.bash --apply`, so that a single install carries those rules.
3. **A1:** rewrite the juniper-k8s and juniper-recurrence remotes, then confirm `python3 util/git_remote_alias_check.py` exits 0. That is G6's turing acceptance. Opt in with `pre-commit install --hook-type pre-push`.
4. **`~/.condarc`:** set `ssl_verify: true` (closes E-SSL) and trim the seven non-conda-forge channels.
5. **JuniperPython's stray `PYTHONPATH`:** `conda env config vars unset PYTHONPATH -n JuniperPython`. mamba also warns that it cannot parse that env's `conda-meta/state`.
6. **The network:** the open-security radio, roaming or `en7` (F2), and A6.
7. **F3 node mode:** quit the desktop apps and Docker Desktop, with no VM running, then say so.
8. **Commit signing (from §19):** K5 is applied, so the owner's own commits under `~/Development/python/Juniper/` fail closed until B2/B3. Do not insert a YubiKey into turing until the guard is installed with K12's rules (step 2) and K13, the IDE agent approvals, is done.
9. **The rest of Owner block 1:** C0, A2, A3, B2-B6, C1-C3, C5, C7, E4, A6, F1 and F2.

## Agent next

1. **G1:** `util/host_state_probe.bash` (collection) and `util/host_state_check.py`, which evaluates `conf/hosts/turing/expected.yaml` against the probe's JSON. Flags `--json`, `--check`, `--section`; suites `tests/test_host_state_probe.py` and `tests/test_host_state_check.py`; R-G1, the X2 class. G1 graduates `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`. When it lands, its two suites join `HOST_TOOLING_SUITES` and `HOST_TOOLING_PATHS` in the G4 job, and `SUITES` in `tests/test_ci_host_tooling_macos.py`. Design notes:
   - The gates come from §9.3, revised by E-D6. G-TOOLS checks that every tool `hosttools-environment.yml` names resolves from `~/.local/bin`.
   - G-ENV: its env half now holds (E2); its parent-AGENTS.md hash half fails until `~/Development/python/Juniper/AGENTS.md` exists on turing.
   - G-ALIAS can reuse `util/git_remote_alias_check.py --json`, and G-SIGN `util/headless_signing_preflight.bash`.
   - G-MEM's thresholds are already in `util/macvm_ctl.bash` (F5a).
   - Scripts check paths and modes only and never read key contents.
   - It is a suite-adding PR, so build its AGENTS.md count and CHANGELOG entry from main as it stands when it lands (E-LAND-3).
2. **G4 promotion:** after 10 consecutive green runs of `host-tooling-macos`, add it to `required-checks.needs` and flip `test_the_job_is_advisory`.
3. **F3 node mode**, after owner step 7. Then **the Session 3 group:** H2, H4, H5, and E5, which needs A6. D2-upg and D4 still need re-planning under the D6 ruling.
4. **Post-merge check (E-LAND-2):** after the E2 record PR merges, `python3 -I util/ad-hoc/2026-10-20_turing_e2_record.py --dry-run` on `main` should report every edit `present`. Run it again after the next PR that touches the plan.

## Verify the starting state

```bash
git fetch origin && git log -3 --oneline origin/main
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/home_path_literal_check.py                         # PASS (G5)
python3 util/git_remote_alias_check.py                          # exit 1 until A1
/usr/local/miniforge3/condabin/conda env list                   # JuniperCascor1, JuniperData, JuniperCanopy1
python3 -I util/ad-hoc/2026-10-20_turing_e2_record.py --dry-run  # every edit present
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py           # the link
```

## Documents and git state at handoff

- **Created in this session:**
  - G5's files (#2272): `util/home_path_literal_check.py`, `conf/home_path_literal_baseline.json`, `tests/test_home_path_literal_check.py`, `util/ad-hoc/2026-10-20_turing_g5_mutation_check.py` and `util/ad-hoc/2026-10-20_turing_g5_apply.py`;
  - G6's file (#2274): `util/ad-hoc/2026-10-20_turing_g6_apply.py`;
  - G4's files (#2276): `tests/test_ci_host_tooling_macos.py` and `util/ad-hoc/2026-10-20_turing_g4_apply.py`;
  - the record PR (#2277): `util/ad-hoc/2026-10-20_turing_session3_record.py`, `reports/2026-10-20_turing-e2-envs/{README.md,JuniperCascor1.export.yml,JuniperData.export.yml}`, and the earlier handoff;
  - the E2 record PR: `util/ad-hoc/2026-10-20_turing_e2_record.py`, `util/ad-hoc/2026-10-20_turing_e2_blas_concurrency_repro.py`, `reports/2026-10-20_turing-e2-envs/{JuniperCanopy1.export.yml,JuniperCanopy1.openblas-hang.txt,JuniperCanopy1.summary.json,JuniperCanopy1.venv-pip-freeze.txt,JuniperCascor1.summary.json,JuniperCascor1.venv-pip-freeze.txt,JuniperData.summary.json,JuniperData.venv-pip-freeze.txt}`, and this file.
- **Modified in this session:**
  - `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `docs/REFERENCE.md`, `AGENTS.md` and `CHANGELOG.md`, by G5, G6 and G4;
  - `tests/test_git_remote_alias_check.py`, by G6;
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`: v1.3.0 §18 in #2277, then v1.4.1 in the E2 record PR;
  - `conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml`: E-SSL lines in #2277; STATUS paragraphs, and JuniperCanopy1's MKL pins, in the E2 record PR;
  - `conf/hosts/turing/hosttools-environment.yml` (#2277);
  - `reports/2026-10-20_turing-e2-envs/README.md`, `util/ad-hoc/2026-10-19_turing_e2_validate_envs.py` (`--env`), and the earlier handoff (a pointer to this file), in the E2 record PR.
- **Worktree:** `.claude/worktrees/snazzy-stirring-hejlsberg` at `origin/main` plus the E2 record files. Nothing was committed
  locally; everything landed through the API.
- **Host changes:**
  - three conda envs under `/usr/local/miniforge3/envs/`; JuniperCanopy1 was removed and re-created on MKL;
  - the E2 work dir `~/.local/state/juniper/turing-e2/` (`trees/`, `venvs/`, `logs/`);
  - memory notes: `turing-host-profile`, `turing-little-snitch-per-app-filter`, and a new `conda-forge-torch-openblas-livelock`.
