# Handoff — turing Session 3: G5, G6 and G4 landed; E2 has two envs created, PyPI blocked by Little Snitch; G1 next

- **From:** the 2026-10-19/20 session on turing named "mac dev env". It continues
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-2-e6-d5-d6-h1-done-e2-blocked-on-little-snitch.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.3.0. This session's
  record, task status and errata are in its §18. Task IDs below refer to the plan.
- **Standing approval:** the owner granted merge approval for the work arc, merging only after green. It does not cover
  the `pypi` deployment gate.

## Landed (squash-merged to `main` after green)

| PR | Merge | What |
|---|---|---|
| juniper-ml#2272 | `a5311979` | G5: `util/home_path_literal_check.py`, the G-PATH gate, and `conf/home_path_literal_baseline.json` (436 files, 651 lines). It runs as the `home-path-literal` pre-commit hook and as a whole-scope step in the Pre-commit job |
| juniper-ml#2274 | `223d09a7` | G6: the `git-remote-alias` pre-push hook. Also `default_stages: [pre-commit]`, explicit stages on `check-added-large-files` and `isort`, `minimum_pre_commit_version` 3.2.0, and a CI smoke step |
| juniper-ml#2276 | `3968ca04` | G4: ci.yml's advisory `host-tooling-macos` job, gated by `tests/test_ci_host_tooling_macos.py`. Its first run, on the PR, was green on arm64 macOS 26 with `/bin/bash` 3.2.57: 371 tests, 7 skipped, 2 m 13 s. That counts as green run 1 of the 10 the promotion needs |
| the record PR | — | plan v1.3.0 §18, the E2 spec-header corrections, `reports/2026-10-20_turing-e2-envs/`, and this file |

## E2: two of three envs created, none validated

- **Created** with `MAMBA_SSL_VERIFY=true /usr/local/miniforge3/bin/mamba env create --override-channels -c conda-forge -f conf/hosts/turing/conda-envs/<Env>.yml`:
  - JuniperCascor1, 67 packages (torch 2.10.0 `cpu_mkl`, and MKL is available);
  - JuniperData, 91 packages.
- **Exports:** `reports/2026-10-20_turing-e2-envs/`. Their `channels:` block repeats `~/.condarc`; every package came from conda-forge.
- **Blocked.** The pip half of E2 needs `pypi.org` and `files.pythonhosted.org` from each new env's `python3.14`. That is
  validation phase `install` for cascor and data, and JuniperCanopy1's own pip section. Little Snitch holds those
  connections for an alert nobody answered (§18.3 E-NET-3): the probe hangs past its 15 s socket timeout.
  Do **not** route around it.
- **Resume** once the owner has allowed them. Run each env in turn, cascor then data:
  1. Run `python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data> --phase install`, then `--phase test`. The `prepare` copies are done. Classify each failure as host-environment or a real env problem; fix the real ones.
  2. Create JuniperCanopy1 (dry run first), then run `validate_envs.py canopy`.
  3. Update each spec header's STATUS paragraph, and add the E2 outcome to the plan (a §19 row, or a §18 erratum if the session is short).
- **The probe** shows whether the alert was answered:
  ```bash
  timeout 25 /usr/local/miniforge3/envs/JuniperCascor1/bin/python3.14 -I -c "import urllib.request as u; print(u.urlopen(u.Request('https://pypi.org/simple/pip/', method='HEAD'), timeout=15).status)"   # 200 once allowed
  ```

## Findings this session (all in plan §18.3)

- **E-SSL.** mamba 2.x ignores `CONDA_SSL_VERIFY`, so the D6 and E2 recipes ran with TLS verification off; use `MAMBA_SSL_VERIFY=true`. Owner step 4 (`ssl_verify: true`) fixes the root, and re-creating JuniperHostTools with verification is the owner's call.
- **E-NET-3.** Little Snitch verdicts moved: mamba is allowed, base `python3.13` is denied (a fast TLS EOF), and new env pythons are held.
- **E-G6.** A hook without `stages` runs at every stage, and a manifest's `stages` overrides `default_stages`. G6 handles both.
- **E-CQ2.** CodeQL `py/overly-permissive-file` (a `chmod 0o644`) blocked #2272 until fixed. The pre-screen does not predict it, so grep for `chmod(` before landing.
- **E-LAND-3.** Concurrent PRs that both insert at the top of CHANGELOG's `### Added`, or both change AGENTS.md's suite count, conflict on update-branch. Anchor a turing entry below an existing turing entry (G6 sits below G5, G4 below G2), and build a suite-adding PR after the other one merges. Coordinated with the recurrence session over #2273; the agreed order was #2273, then #2274, then G4.

## Owner steps (unchanged from Session 2 unless noted)

1. **Little Snitch (updated):** allow `pypi.org` and `files.pythonhosted.org` for `/usr/local/miniforge3/envs/JuniperCascor1/bin/python3.14` and `/usr/local/miniforge3/envs/JuniperData/bin/python3.14`, then for JuniperCanopy1's once it exists. mamba is already allowed. Say when this is done, and the agent resumes E2.
2. **Install the C8 guard:** fast-forward the primary checkout (`git pull --ff-only origin main`), then `bash util/install_claude_agent_guard.bash --apply`.
3. **A1:** rewrite the juniper-k8s and juniper-recurrence remotes, then confirm `python3 util/git_remote_alias_check.py` exits 0. After A1, G6's `pre-commit run --hook-stage pre-push` passes on turing, which is its acceptance. Opt in to the hook with `pre-commit install --hook-type pre-push`.
4. **`~/.condarc`:** set `ssl_verify: true`, which also closes E-SSL, and trim the seven non-conda-forge channels.
5. **JuniperPython's stray `PYTHONPATH`:** run `conda env config vars unset PYTHONPATH -n JuniperPython`.
6. **The network:** the open-security radio, roaming or `en7` (F2), and A6.
7. **F3 node mode:** quit the desktop apps and Docker Desktop, with no VM running, then say so.
8. **The rest of Owner block 1:** C0, A2, A3, B2-B6, C1-C3, C5, C7, E4, A6, F1 and F2.

## Agent next

1. **E2 resume**, after owner step 1.
2. **G1:** `util/host_state_probe.bash` (collection) and `util/host_state_check.py`, which evaluates `conf/hosts/turing/expected.yaml` against the probe's JSON. Flags `--json`, `--check`, `--section`; suites `tests/test_host_state_probe.py` and `tests/test_host_state_check.py`; R-G1, the X2 class. G1 graduates `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`. When it lands, its two suites join `HOST_TOOLING_SUITES` and `HOST_TOOLING_PATHS` in the G4 job, and `SUITES` in `tests/test_ci_host_tooling_macos.py`. Design notes:
   - The gates come from §9.3, revised by E-D6. G-TOOLS checks that every tool `hosttools-environment.yml` names resolves from `~/.local/bin`.
   - G-ALIAS can reuse `util/git_remote_alias_check.py --json`, and G-SIGN `util/headless_signing_preflight.bash`.
   - G-MEM's thresholds are already in `util/macvm_ctl.bash` (F5a).
   - Scripts check paths and modes only and never read key contents.
3. **G4 promotion:** after 10 consecutive green runs, add `host-tooling-macos` to `required-checks.needs`, and flip `test_the_job_is_advisory`.
4. **F3 node mode**, after owner step 7. Then **the Session 3 group:** H2, H4, H5, and E5, which needs A6. D2-upg and D4 still need re-planning under the D6 ruling.
5. **Post-merge check (E-LAND-2).** After juniper-ml#2273 merged, dry runs of `util/ad-hoc/2026-10-20_turing_g{5,6,4}_apply.py` on `main` at `3968ca04` reported all 25 blocks `present`. The next uploader of the same shared files is the "code signing" session's PR. It adds the plan's §19 and v1.4.0 on top of this record, and its edit script rebuilds from origin/main after this record merges. After it merges, run the three dry runs again: each block reports `present`, or the script re-applies it.

## Verify the starting state

```bash
git fetch origin && git log -3 --oneline origin/main
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/home_path_literal_check.py                    # PASS (G5)
python3 util/git_remote_alias_check.py                     # exit 1 until A1
/usr/local/miniforge3/condabin/conda env list              # JuniperCascor1 and JuniperData present
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py      # the link
```

## Documents and git state at handoff

- **Created in this session:**
  - G5's files (#2272): `util/home_path_literal_check.py`, `conf/home_path_literal_baseline.json`, `tests/test_home_path_literal_check.py`, `util/ad-hoc/2026-10-20_turing_g5_mutation_check.py` and `util/ad-hoc/2026-10-20_turing_g5_apply.py`;
  - G6's file (#2274): `util/ad-hoc/2026-10-20_turing_g6_apply.py`;
  - G4's files: `tests/test_ci_host_tooling_macos.py` and `util/ad-hoc/2026-10-20_turing_g4_apply.py`;
  - the record PR: `util/ad-hoc/2026-10-20_turing_session3_record.py`, `reports/2026-10-20_turing-e2-envs/{README.md,JuniperCascor1.export.yml,JuniperData.export.yml}`, and this file.
- **Modified in this session:**
  - `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `docs/REFERENCE.md`, `AGENTS.md` and `CHANGELOG.md`, by G5, G6 and G4;
  - `tests/test_git_remote_alias_check.py`, by G6;
  - in the record PR: `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (v1.3.0, §18), `conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml` and `conf/hosts/turing/hosttools-environment.yml`.
- **Worktree:** `.claude/worktrees/snazzy-stirring-hejlsberg` at `origin/main` plus the record files. Nothing was committed
  locally; everything landed through the API.
- **Host changes:**
  - two new conda envs under `/usr/local/miniforge3/envs/`;
  - the E2 work dir `~/.local/state/juniper/turing-e2/trees/`;
  - memory notes updated: `homebrew-intel-no-bottles` (E-SSL), `turing-little-snitch-per-app-filter` (E-NET-3) and `turing-api-landing-pitfalls` (E-CQ2).
