# turing E2 conda envs: exports and validation of record (2026-10-20)

Bring-up task E2 (decision D8) of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, §18.

| Env | Spec | Packages | Unit lane | Integration lane |
|---|---|---|---|---|
| JuniperCascor1 | `conf/hosts/turing/conda-envs/JuniperCascor1.yml` | 67 (python 3.14.2, pytorch 2.10.0 `cpu_mkl`, mkl 2023.2.0, numpy 2.4.1) | 5777 of 5777 passed; coverage 96.55%; 297 s | 172 of 172 passed |
| JuniperData | `conf/hosts/turing/conda-envs/JuniperData.yml` | 91 (python 3.14.8, numpy 2.5.4, scipy 1.18.1, h5py 3.16.0, OpenBLAS 0.3.34) | 2201 passed, 3 skipped, of 2204; coverage 97.82%; 170 s | 62 of 62 passed |
| JuniperCanopy1 | `conf/hosts/turing/conda-envs/JuniperCanopy1.yml` | 224 conda (python 3.14.2, pytorch 2.10.0 `cpu_mkl`, mkl 2023.2.0, numpy 2.3.5), plus the pip section | 7947 passed, 10 skipped, 2 failed, of 7959; coverage 96.68%; 558 s | 523 passed, 79 skipped, of 602 |

All three envs were created on 2026-10-20 and validated the same day. JuniperCanopy1's first build was replaced; see
its section below.

## How they were made

Each env came from its spec with mamba 2.1.1, after a `--dry-run` matched the spec header's solve:

```bash
MAMBA_SSL_VERIFY=true /usr/local/miniforge3/bin/mamba env create --override-channels -c conda-forge \
    -f conf/hosts/turing/conda-envs/<Env>.yml --yes
```

- **`MAMBA_SSL_VERIFY`, not `CONDA_SSL_VERIFY`.** `~/.condarc` sets `ssl_verify: false`, and mamba 2.x ignores
  `CONDA_SSL_VERIFY` (`mamba config list ssl_verify --sources` stays `<false>`); `MAMBA_SSL_VERIFY=true` gives
  `<system>`. That is erratum E-SSL in plan §18.3.
- **Sanity check:** in JuniperCascor1 and JuniperCanopy1, `torch.backends.mkl.is_available()` is True and
  `torch.__config__.show()` reports `BLAS_INFO=mkl`.

## How they were validated

`python3 -I util/ad-hoc/2026-10-19_turing_e2_validate_envs.py <cascor|data|canopy>` ran each repo's CI lanes:

1. It copied the owner's checkout into `~/.local/state/juniper/turing-e2/trees/`, without `.git`.
2. It made a `python -m venv --system-site-packages` overlay on the env, and ran the repo's CI pip steps in it, so
   the env stayed exactly what its spec builds.
3. It ran ci.yml's unit and integration lanes with `--maxfail` dropped, so the counts are complete.

The child environment comes from a minimal allow-list (the script's docstring lists the deviations from CI).

- `<Env>.summary.json` is the runner's summary: counts, coverage, and every failure.
- `<Env>.venv-pip-freeze.txt` is the overlay's `pip list --format=freeze`: the env's packages plus whatever CI's
  pip steps added or upgraded.

## Notes per env

- **JuniperData.** Its 3 skips are by design. The workflow steps those tests exercise use GNU `base64 -w0` and
  `date -d`, which macOS's BSD userland lacks.
- **JuniperCanopy1, first build (OpenBLAS).** The first spec kept the Linux env's `libblas 3.11.0`, which on osx-64
  means OpenBLAS 0.3.30 and conda-forge's `cpu_generic` torch on top of it. In that env, canopy's unit lane hung at
  the same test in two runs, at about 300% CPU. Three threads were spinning in OpenBLAS's `blas_memory_alloc`, two
  of them demo-mode training threads that earlier tests had left running. With `OMP_NUM_THREADS=6` the same lane
  ran to the end. The spec now takes the MKL variant: on Linux, canopy's torch is the PyPI wheel, which carries its
  own MKL. The stacks, both runs and the experiment are in `JuniperCanopy1.openblas-hang.txt` (plan §18.3 E-BLAS).
- **JuniperCanopy1, as validated (MKL).** Its 10 unit and 79 integration skips are by design: these lanes run
  without juniper-data-client, and the Cassandra, Redis and JuniperData E2E tests are opt-in. Its 2 failures are
  `test_internal_api_key_rules.py::test_a_key_requests_refuses_to_send_is_left_off_the_self_call[trailing-lf]` and
  `test_blank_api_key_warning_boot.py::test_a_padded_key_never_reaches_a_log_record`. Both assume `requests`
  refuses a header value with a trailing LF. requests does that from 2.33.1, and canopy's CI resolves 2.34.2, while
  the spec keeps the Linux env's 2.32.5. That is a juniper-canopy floor gap, not a turing defect (plan §18.3 E-REQ).

## The exports

`<Env>.export.yml` is `conda env export --no-builds -n <Env>`. **Its `channels:` block is misleading.** It
repeats the eight channels `~/.condarc` lists, but every package came from conda-forge: the create command
passed `--override-channels -c conda-forge`. Owner step 4 trims `~/.condarc`.
