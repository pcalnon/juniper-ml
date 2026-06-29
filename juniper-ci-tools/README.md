<!-- markdownlint-disable -->

# juniper-ci-tools

Shared CI / build tooling for the [Juniper ML platform](https://github.com/pcalnon/juniper-ml).

This package is the **single source of truth** for the dependency-documentation
generator that historically lived as `scripts/generate_dep_docs.sh` (or
`util/generate_dep_docs.sh`) in every Juniper repo. Three variants of that
script drifted on `origin/main`; the 2026-05-20 bug fix in
[juniper-cascor#276](https://github.com/pcalnon/juniper-cascor/pull/276)
(switching the conda-dependency extraction from `sed` to `awk` to avoid
emitting an invalid trailing `prefix:` / `variables:` key) shipped in 1 of 8
repos. This package distributes that fix as `pip install`-able tooling so it
cannot drift again.

This work mirrors the
[`juniper-doc-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
that addressed the analogous 2026-05-18 doc-link validator incident.

## Installation

```bash
pip install juniper-ci-tools
```

This installs the following console scripts:

- `juniper-generate-dep-docs` — dependency-documentation generator (the
  consolidated `scripts/generate_dep_docs.sh` port; see "Usage" below).
- `juniper-lint-workflow-paths` — lints that every
  `python|bash <path>` invocation in `.github/workflows/*.yml`
  references a file that exists on disk. Added in 0.2.0;
  consolidates the 6 byte-identical copies of
  `util/test_workflow_script_paths.py` that existed across consumer
  repos.
- `juniper-env-drift-check` — asserts the `juniper-*` distributions
  installed in the active environment (**plain wheels included**)
  satisfy the floors a target repo's `pyproject.toml` declares, and —
  with `--check-lock` — that its `requirements.lock` pins do too.
  Added in 0.5.0; the shared, reusable form of the dependency-
  satisfaction guard (test-suite audit plan §10.1) that closes the
  2026-06-26 "green tests / dead app" client-floor-drift class.

The package requires Python 3.11 or newer and depends on PyYAML and packaging.

## Usage

Run from the root of any Juniper repo that has a `pyproject.toml`:

```bash
juniper-generate-dep-docs
```

Equivalent module form:

```bash
python -m juniper_ci_tools
```

This will:

1. Create `conf/` if needed.
2. Back up any existing `conf/requirements_ci.txt` with a timestamp infix.
3. Render `notes/PIP_DEPENDENCY_FILE_HEADER.md` (substituting placeholders
   like `<X.Y.Z ...>`, `<YYYY-MM-dd ...>`, `<Python Version>`, `<Pip Version>`)
   and append `pip list --format=freeze` output.
4. If `conda` is on `PATH`: back up any existing
   `conf/conda_environment_ci.yaml`, render
   `notes/CONDA_DEPENDENCY_FILE_HEADER.md`, append the dependency block
   extracted from `conda env export --no-builds` (using the awk-equivalent
   logic that produces valid YAML), and validate the result with
   `yaml.safe_load`.

If conda is not available the conda step is skipped with a warning (matches
the legacy bash script). If the generated YAML fails to parse, the command
exits non-zero.

### CLI options

| Flag | Default | Purpose |
|---|---|---|
| `--repo-root` | cwd | Repo root containing `pyproject.toml` |
| `--conf-dir` | `conf` | Output directory |
| `--notes-dir` | `notes` | Directory containing header templates |
| `--pip-header` | `PIP_DEPENDENCY_FILE_HEADER.md` | Pip header template filename |
| `--conda-header` | `CONDA_DEPENDENCY_FILE_HEADER.md` | Conda header template filename |
| `--pip-filename` | `requirements_ci.txt` | Pip output filename |
| `--conda-filename` | `conda_environment_ci.yaml` | Conda output filename |
| `--no-conda` | off | Skip conda generation even if conda is installed |
| `--no-yaml-validation` | off | Skip `yaml.safe_load` on generated conda file |

## Environment floor-drift check (`juniper-env-drift-check`)

Run from (or against) any Juniper repo to assert the active environment is not
*below* the client floors the repo's `pyproject.toml` declares — the durable,
reusable form of the dependency-satisfaction guard (added in 0.5.0). Unlike
`util/editable_install_drift_check.py`, it reads versions via
`importlib.metadata`, so **plain wheels are checked identically to editable
installs** (the 2026-06-26 canopy "green tests / dead app" incident class).

```bash
# Scan the active interpreter against ./pyproject.toml
juniper-env-drift-check

# Check a specific repo, and also assert its lockfile pins satisfy the floors
juniper-env-drift-check --repo-root /path/to/repo --check-lock

# Scan a specific environment's site-packages (e.g. a conda env), as JSON
juniper-env-drift-check --site-packages /opt/miniforge3/envs/MyEnv/lib/python3.13/site-packages --json
```

Exit codes: `0` (no floor below its requirement), `1` (drift — an installed
wheel, or a `--check-lock` lock pin, below a floor), `2` (usage error — no
`pyproject.toml`, no `juniper-*` floors, or `--check-lock` with no lockfile). A
not-installed floor is a soft note unless `--strict` is given. Every floor (OK
and drifted alike) is listed — no silent truncation.

## Library API

```python
from juniper_ci_tools import generate_dep_docs

result = generate_dep_docs(repo_root="/path/to/repo")
print(result.pip_file, result.conda_file, result.yaml_validated)
```

See the package's `juniper_ci_tools/generate_dep_docs.py` docstring for the
full surface.

## Development

```bash
cd juniper-ci-tools
pip install -e ".[test]"
pytest
```

## License

MIT. Copyright (c) 2024-2026 Paul Calnon.
