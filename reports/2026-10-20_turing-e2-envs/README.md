# turing E2 conda envs: exports of record (2026-10-20)

Bring-up task E2 (decision D8) of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, §18.

| Env | Spec | State | Packages |
|---|---|---|---|
| JuniperCascor1 | `conf/hosts/turing/conda-envs/JuniperCascor1.yml` | created 2026-10-20; not validated | 67 (python 3.14.2, pytorch 2.10.0 `cpu_mkl`, mkl 2023.2.0, numpy 2.4.1) |
| JuniperData | `conf/hosts/turing/conda-envs/JuniperData.yml` | created 2026-10-20; not validated | 91 (python 3.14.8, numpy 2.5.4, scipy 1.18.1, h5py 3.16.0, OpenBLAS 0.3.34) |
| JuniperCanopy1 | `conf/hosts/turing/conda-envs/JuniperCanopy1.yml` | not created | its solve: 223 conda packages, 189 MB, plus a pip section |

## How they were made

Each env came from its spec with mamba 2.1.1, after a `--dry-run` matched the spec header's solve:

```bash
MAMBA_SSL_VERIFY=true /usr/local/miniforge3/bin/mamba env create --override-channels -c conda-forge \
    -f conf/hosts/turing/conda-envs/<Env>.yml --yes
```

- **`MAMBA_SSL_VERIFY`, not `CONDA_SSL_VERIFY`.** `~/.condarc` sets `ssl_verify: false`, and mamba 2.x ignores
  `CONDA_SSL_VERIFY` (`mamba config list ssl_verify --sources` stays `<false>`); `MAMBA_SSL_VERIFY=true` gives
  `<system>`. That is erratum E-SSL in plan §18.3.
- **Sanity check, JuniperCascor1:** `torch 2.10.0`, `numpy 2.4.1`, `torch.backends.mkl.is_available()` is True.

## The exports

`<Env>.export.yml` is `conda env export --no-builds -n <Env>`. **Its `channels:` block is misleading.** It
repeats the eight channels `~/.condarc` lists, but every package came from conda-forge: the create command
passed `--override-channels -c conda-forge`. Owner step 4 trims `~/.condarc`.

## What is still open

- **Validation.** `util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data> --phase install` runs CI's
  pip steps in a venv overlay, and then `--phase test` runs the lanes. The pip steps need `pypi.org` and
  `files.pythonhosted.org` from each env's `python3.14`. On 2026-10-20, Little Snitch held those connections
  with an alert nobody answered (E-NET-3). The `prepare` phase, which copies the owner's checkouts into
  `~/.local/state/juniper/turing-e2/trees/`, is done for both.
- **JuniperCanopy1.** Its spec's pip section needs the same PyPI access, so it is created after the owner allows it.
