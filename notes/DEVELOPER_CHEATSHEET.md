# Juniper Developer Cheatsheet

## Quick-Reference Procedures for Common Developer Tasks

| Meta Data         | Value                                                          |
|-------------------|----------------------------------------------------------------|
| **Version:**      | 1.0.0                                                          |
| **Status:**       | Active                                                         |
| **Last Updated:** | March 3, 2026                                                  |
| **Project:**      | Juniper - Cascade Correlation Neural Network Research Platform |

---

## Table of Contents

- [Secrets](#secrets)
  - [View Current Secrets](#view-current-secrets)
  - [Add a New Secret](#add-a-new-secret)
  - [Change an Existing Secret](#change-an-existing-secret)
  - [Remove a Secret](#remove-a-secret)
  - [Enable API Key Authentication](#enable-api-key-authentication)
  - [Disable API Key Authentication](#disable-api-key-authentication)
  - [Add SOPS to a New Repo](#add-sops-to-a-new-repo)
  - [Rotate the SOPS Age Key](#rotate-the-sops-age-key)
- [API Endpoints](#api-endpoints)
  - [Add an Endpoint to juniper-data](#add-an-endpoint-to-juniper-data)
  - [Add an Endpoint to juniper-cascor](#add-an-endpoint-to-juniper-cascor)
  - [Add a WebSocket Endpoint](#add-a-websocket-endpoint)
  - [Change an Existing Endpoint](#change-an-existing-endpoint)
  - [Remove an Endpoint](#remove-an-endpoint)
  - [Add Request/Response Models](#add-requestresponse-models)
  - [Add Middleware](#add-middleware)
- [Clients](#clients)
  - [Add a Method to juniper-data-client](#add-a-method-to-juniper-data-client)
  - [Add a Method to juniper-cascor-client](#add-a-method-to-juniper-cascor-client)
  - [Add a WebSocket Event Handler](#add-a-websocket-event-handler)
  - [Change a Client Method](#change-a-client-method)
  - [Remove a Client Method](#remove-a-client-method)
  - [Change Client Retry/Timeout Defaults](#change-client-retrytimeout-defaults)
- [Services](#services)
  - [Start the Full Stack (Docker)](#start-the-full-stack-docker)
  - [Start in Demo Mode](#start-in-demo-mode)
  - [Start in Dev Mode](#start-in-dev-mode)
  - [Add a New Docker Service](#add-a-new-docker-service)
  - [Change a Service Port](#change-a-service-port)
  - [Add an Environment Variable to a Service](#add-an-environment-variable-to-a-service)
  - [Run a Service Natively (No Docker)](#run-a-service-natively-no-docker)
  - [Check Service Health](#check-service-health)
- [Testing](#testing)
  - [Run Tests per Repo](#run-tests-per-repo)
  - [Run Tests with Coverage](#run-tests-with-coverage)
  - [Add a Pytest Marker](#add-a-pytest-marker)
  - [Run Specific Marker Subsets](#run-specific-marker-subsets)
- [Dependencies](#dependencies)
  - [Add a Dependency](#add-a-dependency)
  - [Remove a Dependency](#remove-a-dependency)
  - [Regenerate Lockfile](#regenerate-lockfile)
  - [Add an Optional Dependency Group](#add-an-optional-dependency-group)
- [Configuration](#configuration)
  - [Add a Setting to juniper-data](#add-a-setting-to-juniper-data)
  - [Add a Constant to juniper-cascor](#add-a-constant-to-juniper-cascor)
  - [Add a Config Entry to juniper-canopy](#add-a-config-entry-to-juniper-canopy)
- [Logging and Observability](#logging-and-observability)
  - [Change Log Level at Runtime](#change-log-level-at-runtime)
  - [Enable JSON Logging](#enable-json-logging)
  - [Enable Sentry Error Tracking](#enable-sentry-error-tracking)
  - [Enable Prometheus Metrics](#enable-prometheus-metrics)
- [CI/CD and Pre-commit](#cicd-and-pre-commit)
  - [Run Pre-commit Locally](#run-pre-commit-locally)
  - [Publish a Package to PyPI](#publish-a-package-to-pypi)
  - [Add a CI Job](#add-a-ci-job)
- [Claude Code Session Script](#claude-code-session-script)
  - [Launch a New Session](#launch-a-new-session)
  - [Resume an Existing Session](#resume-an-existing-session)
  - [Session ID Files and Safety Constraints](#session-id-files-and-safety-constraints)
  - [Troubleshoot Resume Failures](#troubleshoot-resume-failures)
- [Git Worktrees](#git-worktrees)
  - [Create a Worktree for a New Task](#create-a-worktree-for-a-new-task)
  - [Merge and Clean Up a Worktree](#merge-and-clean-up-a-worktree)
- [Data Contract](#data-contract)
  - [Add a New Generator](#add-a-new-generator)
  - [Download a Dataset Artifact](#download-a-dataset-artifact)
- [Docker](#docker)
  - [Add a Package to Docker Containers](#add-a-package-to-docker-containers)
  - [Upgrade a Package Version](#upgrade-a-package-version)
  - [Upgrade Python Version in Docker](#upgrade-python-version-in-docker)

---

## Secrets

### View Current Secrets

Decrypt the encrypted `.env` to inspect values.

```bash
sops -d --input-type dotenv --output-type dotenv .env.enc
```

> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md) | [Deploy .env.example](../juniper-deploy/.env.example)

### Add a New Secret

1. Decrypt: `sops -d --input-type dotenv --output-type dotenv .env.enc > .env`
2. Add the new key-value pair to `.env`
3. Re-encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Commit the encrypted file: `git add .env.enc && git commit -m "chore: add new secret"`
5. If the variable is consumed by Docker, also add it to `juniper-deploy/.env.example` with a commented-out default

> **Pre-commit guard:** The `no-unencrypted-env` hook blocks committing plaintext `.env` files.
> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md) | [SOPS Implementation Plan](../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md) | [Deploy .env.example](../juniper-deploy/.env.example)

### Change an Existing Secret

Same as [Add a New Secret](#add-a-new-secret) -- decrypt, edit the value, re-encrypt, commit `.env.enc`.

> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md)

### Remove a Secret

1. Decrypt: `sops -d --input-type dotenv --output-type dotenv .env.enc > .env`
2. Remove the key-value pair from `.env`
3. Re-encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Remove any references in code (`settings.py`, `app_config.yaml`, `docker-compose.yml`)
5. Remove from `juniper-deploy/.env.example` if present
6. Commit all changes

> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md)

### Enable API Key Authentication

Set the API keys environment variable for the target service. When unset, all endpoints are open.

```bash
# juniper-data
export JUNIPER_DATA_API_KEYS="key1,key2"

# juniper-cascor
export JUNIPER_CASCOR_API_KEYS="key1,key2"

# juniper-canopy
export CANOPY_API_KEY="your-key"
```

Clients authenticate via the `X-API-Key` header, configured by `JUNIPER_DATA_API_KEY` or `JUNIPER_CASCOR_API_KEY`.

> **Docs:** [juniper-data Settings](../juniper-data/juniper_data/api/settings.py) | [juniper-data Security](../juniper-data/juniper_data/api/security.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Disable API Key Authentication

Unset or remove the API keys variable. When no keys are configured, authentication is disabled (development mode).

```bash
unset JUNIPER_DATA_API_KEYS
```

> **Docs:** [juniper-data Settings](../juniper-data/juniper_data/api/settings.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Add SOPS to a New Repo

1. Copy `.sops.yaml` from an existing repo (all share the same age public key)
2. Create `.env` with the secret values
3. Encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Add `no-unencrypted-env` hook to `.pre-commit-config.yaml`
5. Ensure `.env` is in `.gitignore`
6. Commit `.env.enc` and `.sops.yaml`

> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md) | [SOPS Implementation Plan](../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md) | [SOPS Audit](../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md)

### Rotate the SOPS Age Key

1. Generate new age key: `age-keygen -o new-key.txt`
2. Update `~/.config/sops/age/keys.txt` with the new private key
3. Update the `age` public key in `.sops.yaml` across all 8 repos
4. Re-encrypt every `.env.enc`: decrypt with old key, re-encrypt with new
5. Update the `SOPS_AGE_KEY` GitHub Actions secret in each repo
6. Commit updated `.sops.yaml` and `.env.enc` files

> **Docs:** [SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md) | [Secrets Management Analysis](../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md)

---

## API Endpoints

### Add an Endpoint to juniper-data

1. Create route file: `juniper_data/api/routes/my_resource.py`
2. Define `router = APIRouter(prefix="/my-resource", tags=["my-resource"])`
3. Add route functions with type-annotated Pydantic request/response models
4. Register in `juniper_data/api/app.py`: `app.include_router(my_resource_router, prefix="/v1")`
5. Add tests in `juniper_data/tests/`
6. Run: `pytest juniper_data/tests/ -v`

> **Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [juniper-data API Reference](../juniper-data/docs/api/JUNIPER_DATA_API.md) | [API Schemas](../juniper-data/docs/api/API_SCHEMAS.md) | [App Factory](../juniper-data/juniper_data/api/app.py)

### Add an Endpoint to juniper-cascor

Same pattern as juniper-data. Routes live in the FastAPI app under `/v1`. After adding a server-side endpoint, add a corresponding client method to `juniper-cascor-client` (see [Add a Method to juniper-cascor-client](#add-a-method-to-juniper-cascor-client)).

> **Docs:** [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md) | [juniper-cascor API Reference](../juniper-cascor/notes/API_REFERENCE.md) | [juniper-cascor API Docs](../juniper-cascor/docs/api/api-reference.md) | [API Schemas](../juniper-cascor/docs/api/api-schemas.md)

### Add a WebSocket Endpoint

juniper-cascor exposes WebSocket endpoints at `/ws/training` (metrics stream) and `/ws/control` (command/response). To add a new WebSocket endpoint:

1. Add the WebSocket route handler in the juniper-cascor API layer
2. Add a corresponding stream class in `juniper-cascor-client/juniper_cascor_client/ws_client.py`
3. Update juniper-canopy if it consumes the new stream

> **Docs:** [juniper-cascor-client WebSocket](../juniper-cascor-client/juniper_cascor_client/ws_client.py) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md) | [juniper-canopy CasCor Backend Docs](../juniper-canopy/docs/cascor/CASCOR_BACKEND_MANUAL.md)

### Change an Existing Endpoint

1. Modify the route handler in `api/routes/`
2. Update Pydantic request/response models if the schema changed
3. Update the corresponding client library method (breaking change = bump client version)
4. Update affected consumers (juniper-cascor, juniper-canopy)
5. Run tests in all affected repos

> **Cross-repo triggers:** CI dispatches `data-client-updated` and `cascor-client-updated` events to downstream repos.
> **Docs:** [Ecosystem Dependency Graph](../AGENTS.md#dependency-graph) | [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md)

### Remove an Endpoint

1. Remove the route handler and its Pydantic models
2. Remove or update the client method (mark as deprecated first if a public API)
3. Remove from router registration in `app.py`
4. Update all consumers and tests
5. Run full test suite across affected repos

> **Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md)

### Add Request/Response Models

Define Pydantic models co-located with the route or in a shared `models.py`. All juniper-data models use Pydantic v2 with `model_config`. juniper-cascor uses dataclasses for network config and Pydantic for API models.

> **Docs:** [juniper-data API Schemas](../juniper-data/docs/api/API_SCHEMAS.md) | [juniper-cascor API Schemas](../juniper-cascor/docs/api/api-schemas.md) | [juniper-canopy API Schemas](../juniper-canopy/docs/api/API_SCHEMAS.md)

### Add Middleware

juniper-data middleware stack (applied in `create_app()`): CORS -> SecurityMiddleware -> PrometheusMiddleware -> RequestIdMiddleware.

1. Create middleware class in `juniper_data/api/`
2. Add to `create_app()` in `app.py` (order matters -- outermost runs first)
3. Add tests

> **Docs:** [juniper-data Security Middleware](../juniper-data/juniper_data/api/security.py) | [juniper-data Observability Middleware](../juniper-data/juniper_data/api/observability.py) | [App Factory](../juniper-data/juniper_data/api/app.py)

---

## Clients

### Add a Method to juniper-data-client

1. Add method to `JuniperDataClient` in `juniper_data_client/client.py`
2. Follow existing pattern: `self._session.get/post(f"{self._base_url}/v1/...")` with error handling
3. Add Pydantic or dataclass models if needed
4. Add tests in `tests/`
5. Run: `pytest tests/ -v`

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [Client Source](../juniper-data-client/juniper_data_client/client.py)

### Add a Method to juniper-cascor-client

Same pattern as juniper-data-client. REST methods in `client.py`, WebSocket in `ws_client.py`.

> **Docs:** [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md) | [REST Client](../juniper-cascor-client/juniper_cascor_client/client.py) | [WebSocket Client](../juniper-cascor-client/juniper_cascor_client/ws_client.py)

### Add a WebSocket Event Handler

In `juniper-cascor-client`, `CascorTrainingStream` supports callback registration for message types: `metrics`, `state`, `topology`, `cascade_add`, `event`.

1. Add `on_<type>(callback)` method to `CascorTrainingStream` in `ws_client.py`
2. Handle the new message type in the async iteration loop
3. Add tests

> **Docs:** [WebSocket Client](../juniper-cascor-client/juniper_cascor_client/ws_client.py) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md)

### Change a Client Method

1. Update the method signature and implementation in `client.py`
2. If breaking: bump the package version in `pyproject.toml`
3. Update all consumers (juniper-cascor, juniper-canopy)
4. Run downstream tests to verify

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md)

### Remove a Client Method

1. Remove the method from `client.py`
2. Remove associated models and exceptions
3. Update all consumers and tests
4. Bump the package version

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md)

### Change Client Retry/Timeout Defaults

Both clients use `requests.Session` with `urllib3.Retry` (backoff_factor=0.5, status_forcelist=[500,502,503,504]) and `HTTPAdapter` for connection pooling. Modify defaults in the `__init__` method of the client class.

> **Docs:** [Data Client Source](../juniper-data-client/juniper_data_client/client.py) | [CasCor Client Source](../juniper-cascor-client/juniper_cascor_client/client.py)

---

## Services

### Start the Full Stack (Docker)

```bash
cd juniper-deploy
make up    # or: docker compose --profile full up -d
```

Starts juniper-data (8100) -> juniper-cascor (8200) -> juniper-canopy (8050) with health-check dependencies.

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md) | [docker-compose.yml](../juniper-deploy/docker-compose.yml) | [Deploy .env.example](../juniper-deploy/.env.example)

### Start in Demo Mode

```bash
cd juniper-deploy
make demo  # or: docker compose --profile demo up -d
```

Auto-configures CasCor with a spiral dataset and starts training automatically.

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md) | [.env.demo](../juniper-deploy/.env.demo)

### Start in Dev Mode

```bash
cd juniper-deploy
make dev   # or: docker compose --profile dev up -d
```

Runs canopy in demo mode (no real CasCor backend needed).

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md)

### Add a New Docker Service

1. Add service definition in `juniper-deploy/docker-compose.yml`
2. Set `depends_on` with `condition: service_healthy` for upstream dependencies
3. Add a health check following the existing Python-based pattern
4. Add environment variables to `.env.example`
5. Assign to appropriate profile(s): `full`, `demo`, `dev`
6. Test: `docker compose --profile <profile> config`

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md) | [docker-compose.yml](../juniper-deploy/docker-compose.yml)

### Change a Service Port

1. Update the default port constant in the service's settings/constants module
2. Update `juniper-deploy/.env.example`
3. Update the port mapping in `docker-compose.yml`
4. Update inter-service URL defaults (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`)
5. Update the health check `urlopen` port
6. Update the parent `AGENTS.md` service ports table

> **Docs:** [Ecosystem Service Ports](../AGENTS.md#service-ports) | [Deploy .env.example](../juniper-deploy/.env.example)

### Add an Environment Variable to a Service

1. Add to the service's settings module (Pydantic `BaseSettings` or constants)
2. Add to `juniper-deploy/.env.example` with a commented-out default and description
3. Add to the `environment:` section in `docker-compose.yml` using `${VAR:-default}` substitution
4. Document in the service's `AGENTS.md` environment variables table

> **Docs:** [juniper-data Settings](../juniper-data/juniper_data/api/settings.py) | [Deploy .env.example](../juniper-deploy/.env.example) | [Deploy AGENTS.md Env Vars](../juniper-deploy/AGENTS.md#environment-variables)

### Run a Service Natively (No Docker)

```bash
# juniper-data
conda activate JuniperData
cd juniper-data
pip install -e ".[all]"
python -m juniper_data   # or: uvicorn juniper_data.api.app:app --port 8100

# juniper-cascor
conda activate JuniperCascor
cd juniper-cascor
pip install -e ".[all]"
uvicorn juniper_cascor.api.app:app --port 8200

# juniper-canopy
conda activate JuniperPython
cd juniper-canopy/src
pip install -e ".."
uvicorn main:app --port 8050
```

> **Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md) | [juniper-canopy AGENTS.md](../juniper-canopy/AGENTS.md) | [Conda Environments](../AGENTS.md#conda-environments)

### Check Service Health

```bash
# Single service
curl -s http://localhost:8100/v1/health | python -m json.tool

# All services
for port in 8100 8200 8050; do
  echo "Port $port:"; curl -sf http://localhost:$port/v1/health | python -m json.tool
done

# Docker
docker compose ps   # shows health status column
```

Each service also exposes `/v1/health/live` (liveness) and `/v1/health/ready` (readiness with dependency checks).

> **Docs:** [Ecosystem Service Ports](../AGENTS.md#service-ports) | [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md)

---

## Testing

### Run Tests per Repo

| Repo                  | Command                                                      |
|-----------------------|--------------------------------------------------------------|
| juniper-data          | `cd juniper-data && pytest juniper_data/tests/ -v`           |
| juniper-cascor        | `cd juniper-cascor/src/tests && bash scripts/run_tests.bash` |
| juniper-canopy        | `cd juniper-canopy/src && pytest tests/ -v`                  |
| juniper-data-client   | `cd juniper-data-client && pytest tests/ -v`                 |
| juniper-cascor-client | `cd juniper-cascor-client && pytest tests/ -v`               |
| juniper-cascor-worker | `cd juniper-cascor-worker && pytest tests/ -v`               |
| juniper-deploy        | `cd juniper-deploy && bash scripts/test_demo_profile.sh`     |

> **Docs:** Per-repo [AGENTS.md](../juniper-data/AGENTS.md) files | [juniper-canopy Testing Quick Start](../juniper-canopy/docs/testing/TESTING_QUICK_START.md) | [juniper-cascor Testing Quick Start](../juniper-cascor/docs/testing/quick-start.md)

### Run Tests with Coverage

```bash
# Standard pattern (80% threshold)
pytest tests/ --cov=<package> --cov-report=term-missing --cov-fail-under=80

# juniper-data (95% aggregate, 85% per-module in CI)
pytest juniper_data/tests/ --cov=juniper_data --cov-report=html --cov-report=term-missing --cov-fail-under=80

# juniper-cascor
cd src/tests && bash scripts/run_tests.bash -v -c
```

> **Docs:** [juniper-canopy Testing Reports/Coverage](../juniper-canopy/docs/testing/TESTING_REPORTS_COVERAGE.md) | [juniper-cascor Testing Reference](../juniper-cascor/docs/testing/reference.md)

### Add a Pytest Marker

1. Register in `pyproject.toml` under `[tool.pytest.ini_options]` -> `markers`
2. Apply with `@pytest.mark.<name>` in test files
3. Document in the repo's `AGENTS.md` test markers section

Common markers: `unit`, `integration`, `slow`, `performance`, `api`, `generators`, `storage`, `gpu`, `e2e`

> **Docs:** [juniper-canopy Testing Reference](../juniper-canopy/docs/testing/TESTING_REFERENCE.md) | [juniper-cascor Testing Reference](../juniper-cascor/docs/testing/reference.md) | Per-repo AGENTS.md files

### Run Specific Marker Subsets

```bash
pytest -m unit                   # Unit tests only
pytest -m "not integration"      # Skip integration tests
pytest -m "api and not slow"     # API tests, exclude slow
pytest --run-long                # Include long-running tests (juniper-cascor)
```

> **Docs:** Per-repo AGENTS.md files | [juniper-canopy Selective Test Guide](../juniper-canopy/docs/testing/SELECTIVE_TEST_GUIDE.md)

---

## Dependencies

### Add a Dependency

1. Add to `pyproject.toml` under `[project]` -> `dependencies` (core) or `[project.optional-dependencies]` (extras)
2. Regenerate lockfile: `uv pip compile pyproject.toml --extra <extras> -o requirements.lock`
3. Install: `pip install -e ".[<extra>]"`
4. CI enforces lockfile freshness via `lockfile-check` job

> **Docs:** Per-repo `pyproject.toml` | [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md)

### Remove a Dependency

1. Remove from `pyproject.toml`
2. Remove all import references in source code
3. Regenerate lockfile
4. Run full test suite

> **Docs:** Per-repo `pyproject.toml` | [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md)

### Regenerate Lockfile

```bash
uv pip compile pyproject.toml --extra all -o requirements.lock
```

> **Docs:** [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md) | [Dependency Management Plan](plan_7.5_7.6_dependency_management.md)

### Add an Optional Dependency Group

1. Add new group under `[project.optional-dependencies]` in `pyproject.toml`
2. If creating an "all" aggregate, include the new group
3. Update `juniper-ml` meta-package if the group should be installable via `pip install juniper-ml[...]`
4. Update install instructions in `AGENTS.md` and `README.md`

> **Docs:** [juniper-ml AGENTS.md](../juniper-ml/AGENTS.md)

---

## Configuration

### Add a Setting to juniper-data

1. Add field to `Settings` class in `juniper_data/api/settings.py`
2. Define a default constant following the `_JUNIPER_DATA_*` naming convention
3. The field is automatically configurable via `JUNIPER_DATA_<FIELD_NAME>` env var (pydantic-settings)
4. Add to `juniper-deploy/.env.example` if Docker-relevant

> **Docs:** [juniper-data Settings](../juniper-data/juniper_data/api/settings.py) | [juniper-data AGENTS.md](../juniper-data/AGENTS.md)

### Add a Constant to juniper-cascor

1. Add to the appropriate module in `src/cascor_constants/` (model, candidates, activation, logging, problem, hdf5)
2. Follow `_UPPER_SNAKE` naming with component prefix
3. Extended log levels: TRACE (5), VERBOSE (7), DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL (60)

> **Docs:** [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md) | [Constants Guide](../juniper-cascor/docs/overview/constants-guide.md)

### Add a Config Entry to juniper-canopy

juniper-canopy has a 3-level config hierarchy (highest priority first):

1. **Environment variables** (`CASCOR_*`, `JUNIPER_CANOPY_*`)
2. **YAML config** (`conf/app_config.yaml`) -- supports `${VAR:default}` substitution
3. **Constants module** (`src/canopy_constants.py`)

Add the config entry at the appropriate level based on how dynamic it needs to be.

> **Docs:** [juniper-canopy AGENTS.md](../juniper-canopy/AGENTS.md) | [App Config YAML](../juniper-canopy/conf/app_config.yaml) | [Constants Guide](../juniper-canopy/docs/cascor/CONSTANTS_GUIDE.md)

---

## Logging and Observability

### Change Log Level at Runtime

```bash
# juniper-data
export JUNIPER_DATA_LOG_LEVEL=DEBUG

# juniper-cascor
export JUNIPER_CASCOR_LOG_LEVEL=DEBUG

# Extended levels (cascor/canopy): TRACE, VERBOSE, DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
```

> **Docs:** [juniper-data Settings](../juniper-data/juniper_data/api/settings.py) | [juniper-cascor Logging Config](../juniper-cascor/conf/logging_config.yaml) | [juniper-canopy Logging Config](../juniper-canopy/conf/logging_config.yaml) | [Deploy .env.example](../juniper-deploy/.env.example)

### Enable JSON Logging

```bash
export JUNIPER_DATA_LOG_FORMAT=json       # juniper-data
export JUNIPER_CASCOR_LOG_FORMAT=json     # juniper-cascor
export JUNIPER_CANOPY_LOG_FORMAT=json     # juniper-canopy
```

JSON output includes `request_id`, `service`, `timestamp`, `level`, and `message` fields.

> **Docs:** [juniper-data Observability](../juniper-data/juniper_data/api/observability.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Enable Sentry Error Tracking

Set the DSN environment variable for each service:

```bash
export JUNIPER_DATA_SENTRY_DSN="https://your-dsn@sentry.io/project"
export JUNIPER_CASCOR_SENTRY_DSN="https://your-dsn@sentry.io/project"
export JUNIPER_CANOPY_SENTRY_DSN="https://your-dsn@sentry.io/project"
```

> **Docs:** [juniper-data Observability](../juniper-data/juniper_data/api/observability.py) | [Observability Plan](STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md) | [Deploy .env.example](../juniper-deploy/.env.example)

### Enable Prometheus Metrics

```bash
export JUNIPER_DATA_METRICS_ENABLED=true
export JUNIPER_CASCOR_METRICS_ENABLED=true
export JUNIPER_CANOPY_METRICS_ENABLED=true
```

23 namespaced metrics across all services (e.g., `juniper_data_http_requests_total`, `juniper_cascor_training_loss`, `juniper_canopy_websocket_connections_active`). Use `make obs` for the easiest setup — it auto-enables metrics via `.env.observability`.

```bash
# Preferred: Makefile targets auto-enable metrics
make obs        # full stack + Prometheus + Grafana
make obs-demo   # demo stack + Prometheus + Grafana

# Manual: compose with observability profile
docker compose --env-file .env --env-file .env.observability \
  --profile full --profile observability up -d
```

> **Docs:** [Observability Guide](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md) | [Deploy .env.observability](../juniper-deploy/.env.observability)

### Start Observability Stack

```bash
# Full stack with monitoring
make obs

# Demo stack with monitoring
make obs-demo
```

Access points:
- **Grafana**: http://localhost:3000 (admin / admin)
- **Prometheus**: http://localhost:9090

> **Docs:** [Observability Guide](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md) | [Deploy Makefile](../juniper-deploy/Makefile)

### View Grafana Dashboards

Four auto-provisioned dashboards in the "Juniper" folder:

| Dashboard | UID | Purpose |
|-----------|-----|---------|
| Juniper Overview | `juniper-overview` | Cross-service health, request rates, error rates, latency (home dashboard) |
| JuniperData | `juniper-data` | Dataset generation metrics, cache status, build info |
| JuniperCascor | `juniper-cascor` | Training sessions, loss/accuracy, hidden units, inference |
| JuniperCanopy | `juniper-canopy` | WebSocket connections/messages, demo mode, build info |

> **Docs:** [Observability Guide](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md) | [Dashboard JSON](../juniper-deploy/grafana/provisioning/dashboards/)

### Metric Naming Convention

All metrics use service namespace prefix: `juniper_data_`, `juniper_cascor_`, `juniper_canopy_`.

Pattern: `<namespace>_<subsystem>_<metric_name>_<unit>`

Examples:
- `juniper_data_dataset_generations_total` — Counter of dataset generations
- `juniper_cascor_training_loss` — Current training loss gauge
- `juniper_canopy_websocket_connections_active` — Active WebSocket connections

> **Docs:** [Observability Guide — Metrics Catalog](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md#metrics-catalog)

### Add a Custom Metric to a Service

```python
from prometheus_client import Counter, Gauge, Histogram

# 1. Define in observability.py with service namespace
my_metric = Counter(
    "juniper_data_my_operations_total",
    "Total operations processed",
    ["operation_type"],
)

# 2. Instrument in route/handler
my_metric.labels(operation_type="create").inc()
```

Metric types: Counter (monotonic), Gauge (up/down), Histogram (distributions), Info (static labels).

> **Docs:** [Prometheus Python Client](https://github.com/prometheus/client_python) | [Observability Guide](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md#adding-custom-metrics)

### Add a Grafana Dashboard

1. Create JSON in `juniper-deploy/grafana/provisioning/dashboards/`
2. Set `uid`, `title`, use `datasource: { type: "prometheus", uid: "prometheus" }`
3. Use template variables `$datasource` and `$interval` for flexibility
4. Dashboard auto-loads within 30 seconds (configurable in `dashboard-providers.yml`)

> **Docs:** [Dashboard Providers YAML](../juniper-deploy/grafana/provisioning/dashboards/dashboard-providers.yml) | [Grafana Provisioning Docs](https://grafana.com/docs/grafana/latest/administration/provisioning/)

### Query Prometheus Directly

```bash
# Check if all services are UP
curl -s 'http://localhost:9090/api/v1/query?query=up' | python -m json.tool

# HTTP request rate (last 5 minutes)
curl -s 'http://localhost:9090/api/v1/query?query=rate(juniper_data_http_requests_total[5m])'

# View all Juniper metrics
curl -s 'http://localhost:9090/api/v1/label/__name__/values' | python -m json.tool | grep juniper
```

> **Docs:** [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/) | [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)

### Troubleshoot Missing Metrics

1. **Metrics not in Prometheus?** Verify `*_METRICS_ENABLED=true` is set (check `.env.observability`). Check http://localhost:9090/targets — all should show "UP". Curl the service `/metrics` endpoint directly: `curl http://localhost:8100/metrics`.

2. **Grafana shows "No data"?** Check dashboard time range (metrics only exist after stack start). Verify Prometheus datasource (Settings > Data Sources). Check PromQL in panel edit mode.

3. **Custom metric not scraped?** Ensure metric is defined at module level (not inside a function). Restart the service after adding new metrics.

> **Docs:** [Observability Guide — Troubleshooting](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md#troubleshooting)

---

## CI/CD and Pre-commit

### Run Pre-commit Locally

```bash
pip install pre-commit       # one-time
pre-commit install           # one-time, installs git hooks
pre-commit run --all-files   # run all hooks on all files
```

Key hooks: `ruff` (juniper-data) or `black`+`isort`+`flake8` (others), `mypy`, `bandit`, `yamllint`, `shellcheck`, `no-unencrypted-env`, `detect-private-key`.

> **Docs:** Per-repo `.pre-commit-config.yaml` | [juniper-canopy CI/CD Quick Start](../juniper-canopy/docs/ci_cd/CICD_QUICK_START.md) | [juniper-cascor CI Quick Start](../juniper-cascor/docs/ci/quick-start.md)

### Publish a Package to PyPI

1. Create a GitHub Release with a version tag (e.g., `v0.5.0`)
2. `publish.yml` triggers: build -> TestPyPI -> PyPI
3. The `pypi` environment has a 5-minute wait + required reviewer approval
4. Approve: `gh api repos/<owner>/<repo>/actions/runs/<run_id>/pending_deployments -X POST ...`

Uses OIDC trusted publishing (no API tokens). SHA-pinned actions. `attestations: false`.

> **Docs:** [PyPI Publish Procedure](PYPI_PUBLISH_PROCEDURE.md) | [PyPI Publish Plan](PYPI_PUBLISH_PLAN_3_PACKAGES.md) | [juniper-ml PyPI Procedure](../juniper-ml/notes/pypi-publish-procedure.md)

### Add a CI Job

1. Edit `.github/workflows/ci.yml` in the target repo
2. Follow the existing pattern: SHA-pinned actions, Python version matrix, `needs:` dependencies
3. Add the new job to the `required-checks` quality gate aggregator
4. Test locally with `act` or by pushing to a feature branch

CI pipeline: pre-commit -> unit-tests -> integration-tests -> build -> security -> lockfile-check -> docs -> required-checks -> notify.

> **Docs:** [juniper-canopy CI/CD Reference](../juniper-canopy/docs/ci_cd/CICD_REFERENCE.md) | [juniper-canopy CI/CD Manual](../juniper-canopy/docs/ci_cd/CICD_MANUAL.md) | [juniper-cascor CI Reference](../juniper-cascor/docs/ci/reference.md) | [juniper-cascor CI Manual](../juniper-cascor/docs/ci/manual.md)

---

## Claude Code Session Script

### Launch a New Session

Use `scripts/wake_the_claude.bash` to construct and launch `claude` invocations with validated flags:

```bash
bash scripts/wake_the_claude.bash \
  --id \
  --prompt "Review recent test failures and suggest fixes" \
  -- --effort high --print
```

Notes:
- `--id` stores the generated/provided UUID in `<uuid>.txt` in the current working directory.
- The script launches `claude` via `nohup ... &` and exits after dispatch.

> **Docs:** [Script Source](../juniper-ml/scripts/wake_the_claude.bash)

### Resume an Existing Session

Resume by UUID:

```bash
bash scripts/wake_the_claude.bash \
  --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd \
  --prompt "Continue from previous analysis"
```

Resume by saved session file (basename only, from current directory):

```bash
bash scripts/wake_the_claude.bash \
  --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd.txt \
  --prompt "Continue from previous analysis"
```

### Session ID Files and Safety Constraints

- `--resume` accepts either a UUID or a local `.txt` filename.
- Filenames containing `/` are rejected to block path traversal.
- Non-`.txt` resume filenames are rejected.
- Resume file content must itself be a valid UUID.
- Resume reads are non-destructive: session files are not deleted.
- `--id` refuses to write when the target `*.txt` path is a symlink.

### Troubleshoot Resume Failures

Enable debug logging for parser/validation traces:

```bash
WTC_DEBUG=1 bash scripts/wake_the_claude.bash --resume session-id.txt --prompt "hello" 2>&1
```

Common failure patterns:

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Error: Session ID is invalid. Exiting...` | Invalid UUID or file content | Verify UUID format in value/file |
| `Error: Received Resume Flag but no Valid Session ID to Resume. Exiting...` | `--resume` provided without value | Provide UUID or `.txt` basename after flag |
| Resume by file fails immediately | Filename includes `/` or non-`.txt` extension | Use a local `*.txt` session file in current directory |

> **Docs:** [Regression Tests](../juniper-ml/tests/test_wake_the_claude.py) | [Session Validation Bugfix Plan](../juniper-ml/notes/SESSION_ID_VALIDATION_BUGFIX_PLAN.md) | [Security Remediation Plan](../juniper-ml/notes/SECURITY_REMEDIATION_PLAN.md)

---

## Git Worktrees

### Create a Worktree for a New Task

```bash
cd /home/pcalnon/Development/python/Juniper/<repo>
git fetch origin && git checkout main && git pull origin main

BRANCH_NAME="feature/my-task"
git branch "$BRANCH_NAME" main

REPO_NAME=$(basename "$(pwd)")
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's|/|--|g')
SHORT_HASH=$(git rev-parse --short=8 HEAD)
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--${SHORT_HASH}"

git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
```

> **Docs:** Per-repo [WORKTREE_SETUP_PROCEDURE.md](../juniper-data/notes/WORKTREE_SETUP_PROCEDURE.md) | [Ecosystem Worktree Conventions](../AGENTS.md#worktree-procedures-mandatory--task-isolation) | [Worktree Implementation Plan](WORKTREE_IMPLEMENTATION_PLAN.md)

### Merge and Clean Up a Worktree

```bash
cd "$WORKTREE_DIR" && git push origin "$BRANCH_NAME"
cd /home/pcalnon/Development/python/Juniper/<repo>
git checkout main && git pull origin main
git merge "$BRANCH_NAME"
git push origin main
git worktree remove "$WORKTREE_DIR"
git branch -d "$BRANCH_NAME"
git push origin --delete "$BRANCH_NAME"
git worktree prune
```

> **Docs:** Per-repo [WORKTREE_CLEANUP_PROCEDURE.md](../juniper-data/notes/WORKTREE_CLEANUP_PROCEDURE.md) | [Ecosystem Worktree Conventions](../AGENTS.md#worktree-procedures-mandatory--task-isolation)

---

## Data Contract

### Add a New Generator

1. Create subpackage under `juniper_data/generators/<name>/`
2. Implement generator class following `SpiralGenerator` pattern
3. Register in `generators/__init__.py`
4. Add API routes in `api/routes/` (or leverage existing `/v1/datasets` with new generator name)
5. Output must conform to NPZ contract: keys `X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full` (all `float32`)
6. Add tests and generator schema

Available generators: `spiral`, `xor`, `gaussian`, `circles`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`

> **Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [Data Contract](../AGENTS.md#data-contract)

### Download a Dataset Artifact

```python
from juniper_data_client import JuniperDataClient

client = JuniperDataClient(base_url="http://localhost:8100")

# Create a dataset
dataset_id = client.create_dataset("spiral", {"n_points": 200, "noise": 0.1})

# Download as parsed NumPy arrays
npz = client.download_artifact_npz(dataset_id)
X_train, y_train = npz["X_train"], npz["y_train"]

# Or download raw bytes
raw = client.download_artifact_bytes(dataset_id)
```

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [Client Source](../juniper-data-client/juniper_data_client/client.py) | [Data Contract](../AGENTS.md#data-contract)

---

## Quick Reference Tables

### Service Ports

| Service        | Port | Health           |
|----------------|------|------------------|
| juniper-data   | 8100 | `GET /v1/health` |
| juniper-cascor | 8200 | `GET /v1/health` |
| juniper-canopy | 8050 | `GET /v1/health` |

### Conda Environments

| Environment   | Repo           | Python |
|---------------|----------------|--------|
| JuniperData   | juniper-data   | 3.14   |
| JuniperCascor | juniper-cascor | 3.14   |
| JuniperPython | juniper-canopy | 3.14   |

### Key Auth Environment Variables

| Variable                  | Side   | Service               |
|---------------------------|--------|-----------------------|
| `JUNIPER_DATA_API_KEYS`   | Server | juniper-data          |
| `JUNIPER_CASCOR_API_KEYS` | Server | juniper-cascor        |
| `CANOPY_API_KEY`          | Server | juniper-canopy        |
| `JUNIPER_DATA_API_KEY`    | Client | juniper-data-client   |
| `JUNIPER_CASCOR_API_KEY`  | Client | juniper-cascor-client |

### Docker Compose Profiles

| Profile         | Services                         | Use Case                        |
|-----------------|----------------------------------|---------------------------------|
| `full`          | data + cascor + canopy           | Production-like                 |
| `demo`          | data + cascor-demo + canopy-demo | Auto-configured demo            |
| `dev`           | data + cascor + canopy-dev       | Development                     |
| `observability` | prometheus + grafana             | Monitoring (combine with above) |

---

## Docker

### Add a Package to Docker Containers

1. Add the package to `pyproject.toml` under `dependencies` or `[project.optional-dependencies]`
2. Regenerate the lockfile:

   ```bash
   uv pip compile pyproject.toml --extra <extras> -o requirements.lock
   ```

3. Rebuild the Docker image:

   ```bash
   docker build -t <service>:test <repo-dir>/
   ```

4. Verify the package is importable:

   ```bash
   docker run --rm <service>:test python -c "import <package>; print('ok')"
   ```

> **Docs:** [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md) | Per-repo `pyproject.toml`

### Upgrade a Package Version

1. Update the version pin in `pyproject.toml`
2. Regenerate the lockfile:

   ```bash
   uv pip compile pyproject.toml --extra <extras> -o requirements.lock
   ```

3. Rebuild and test:

   ```bash
   docker build -t <service>:test <repo-dir>/
   docker run --rm <service>:test python -c "import <package>; print(<package>.__version__)"
   ```

> **Docs:** [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md) | Per-repo `pyproject.toml`

### Upgrade Python Version in Docker

Three things to update per repo:

1. **Dockerfile** — change the base image and site-packages path:

   ```dockerfile
   FROM python:<version>-slim AS builder   # Stage 1
   FROM python:<version>-slim AS runtime   # Stage 2
   COPY --from=builder /usr/local/lib/python<version>/site-packages ...
   ```

2. **pyproject.toml** — update linter targets:
   - `black` / `ruff` `target-version`
   - `mypy` `python_version`
3. **Lockfile** — regenerate:

   ```bash
   uv pip compile pyproject.toml --extra <extras> -o requirements.lock
   ```

4. **Verify**:

   ```bash
   docker build -t <service>:test <repo-dir>/
   docker run --rm <service>:test python --version
   ```

> **Docs:** [Docker Python 3.14 Migration Plan](../juniper-deploy/notes/DOCKER_PYTHON_314_MIGRATION_PLAN.md)

---

**Last Updated:** March 7, 2026
**Version:** 1.2.0
**Maintainer:** Paul Calnon
