# PyPI Manual Setup Steps

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Created**: 2026-02-25
**Status**: COMPLETE
**Related**: [PYPI_DEPLOYMENT_PLAN.md](PYPI_DEPLOYMENT_PLAN.md)

---

These steps must be performed manually through web UIs. They cannot be automated
via CLI or API. Complete each section before triggering the corresponding publish
workflow.

---

## 1. Trusted Publishing — TestPyPI

For each package below, go to **<https://test.pypi.org>** > Account Settings >
Publishing > **Add a new pending publisher**.

> If the project already exists on TestPyPI (from a prior upload), go to the
> project's Settings > Publishing > Add a new publisher instead.

| # | PyPI Project Name     | GitHub Owner | GitHub Repo           |   Workflow    | Environment |
|:-:|-----------------------|:------------:|-----------------------|:-------------:|:-----------:|
| 1 | `juniper-data-client` |  `pcalnon`   | `juniper-data-client` | `publish.yml` | `testpypi`  |
| 2 | `juniper-data`        |  `pcalnon`   | `juniper-data`        | `publish.yml` | `testpypi`  |
| 3 | `juniper-cascor`      |  `pcalnon`   | `juniper-cascor`      | `publish.yml` | `testpypi`  |

**Already configured** (published successfully before):

- `juniper-ml` — testpypi trusted publishing OK
- `juniper-cascor-client` — testpypi trusted publishing OK
- `juniper-cascor-worker` — testpypi trusted publishing OK

### Steps per package

1. Log in to <https://test.pypi.org>
2. Go to **Account Settings** > **Publishing**
3. Under "Add a new pending publisher", fill in:
   - **PyPI project name**: (from table above)
   - **Owner**: `pcalnon`
   - **Repository name**: (from table above)
   - **Workflow name**: `publish.yml`
   - **Environment name**: `testpypi`
4. Click **Add**

---

## 2. Trusted Publishing — PyPI

Same process on **<https://pypi.org>** for each package.

| # | PyPI Project Name     | GitHub Owner | GitHub Repo           |   Workflow    | Environment |
|:-:|-----------------------|:------------:|-----------------------|:-------------:|:-----------:|
| 1 | `juniper-data-client` |  `pcalnon`   | `juniper-data-client` | `publish.yml` |   `pypi`    |
| 2 | `juniper-data`        |  `pcalnon`   | `juniper-data`        | `publish.yml` |   `pypi`    |
| 3 | `juniper-cascor`      |  `pcalnon`   | `juniper-cascor`      | `publish.yml` |   `pypi`    |

**Already configured** (published successfully before):

- `juniper-ml` — pypi trusted publishing OK
- `juniper-cascor-client` — pypi trusted publishing OK
- `juniper-cascor-worker` — pypi trusted publishing OK

### Steps per package: Trusted Publishing

1. Log in to <https://pypi.org>
2. Go to **Account Settings** > **Publishing**
3. Under "Add a new pending publisher", fill in:
   - **PyPI project name**: (from table above)
   - **Owner**: `pcalnon`
   - **Repository name**: (from table above)
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click **Add**

---

## 3. GitHub Environments

GitHub environments are required for the publish workflow's OIDC token exchange.

### Already configured (no action needed)

- `pcalnon/juniper-ml` — `pypi`, `testpypi`
- `pcalnon/juniper-data-client` — `pypi`, `testpypi`
- `pcalnon/juniper-cascor-client` — `pypi`, `testpypi`
- `pcalnon/juniper-cascor-worker` — `pypi`, `testpypi`

### Need environments created

These will be created automatically by the agent via the GitHub API:

- `pcalnon/juniper-data` — needs `pypi` and `testpypi`
- `pcalnon/juniper-cascor` — needs `pypi` and `testpypi`

If they were not created automatically, create them manually:

1. Go to **github.com/pcalnon/< repo >** > Settings > Environments
2. Click **New environment**
3. Name: `testpypi` — no protection rules needed
4. Click **New environment** again
5. Name: `pypi` — optionally add **Required reviewers** as a production gate

---

## 4. Verification After Setup

After completing all manual steps, re-run the failed publish workflows:

```bash
# Re-run juniper-data-client publish
cd ~/Development/python/Juniper/juniper-data-client
gh run rerun 22403454114

# Once juniper-data and juniper-cascor have publish.yml committed:
# Create releases to trigger their publish workflows
```

### Verification checklist

- [x] TestPyPI trusted publisher configured for `juniper-data-client`
- [x] PyPI trusted publisher configured for `juniper-data-client`
- [x] TestPyPI trusted publisher configured for `juniper-data`
- [x] PyPI trusted publisher configured for `juniper-data`
- [x] TestPyPI trusted publisher configured for `juniper-cascor`
- [x] PyPI trusted publisher configured for `juniper-cascor`
- [x] GitHub environments exist for `juniper-data` (`testpypi`, `pypi`)
- [x] GitHub environments exist for `juniper-cascor` (`testpypi`, `pypi`)
- [x] Re-run `juniper-data-client` publish workflow succeeds
- [x] TestPyPI trusted publisher configured for `juniper-canopy`
- [x] PyPI trusted publisher configured for `juniper-canopy`
- [x] GitHub environments exist for `juniper-canopy` (`testpypi`, `pypi`)
- [x] TestPyPI trusted publisher configured for `juniper-ml`
- [x] PyPI trusted publisher configured for `juniper-ml`
- [x] GitHub environments exist for `juniper-ml` (`testpypi`, `pypi`)

### Published packages (verified)

| Package | Version | TestPyPI | PyPI | Verified |
|---------|---------|:--------:|:----:|:--------:|
| `juniper-cascor` | 0.3.17 | OK | OK | Prior session |
| `juniper-data` | 0.4.2 | OK | OK | Prior session |
| `juniper-cascor-client` | — | OK | OK | Prior session |
| `juniper-cascor-worker` | — | OK | OK | Prior session |
| `juniper-data-client` | 0.3.1 | OK | OK | 2026-02-27 |
| `juniper-canopy` | 0.3.0 | OK | OK | 2026-02-27 |
| `juniper-ml` | 0.2.0 | OK | OK | 2026-02-27 |

---

## Document History

| Date       | Author                 | Changes          |
|------------|------------------------|------------------|
| 2026-02-25 | Paul Calnon / AI Agent | Initial creation |
| 2026-02-27 | Paul Calnon / AI Agent | All packages published; checklist complete |
