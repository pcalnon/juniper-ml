# Juniper Developer Cheatsheet

## Quick-Reference Procedures for Common Developer Tasks

| Meta Data         | Value                                                          |
|-------------------|----------------------------------------------------------------|
| **Version:**      | 1.3.0                                                          |
| **Status:**       | Active                                                         |
| **Last Updated:** | March 8, 2026                                                  |
| **Project:**      | Juniper - Cascade Correlation Neural Network Research Platform |

> **Link conventions:** Cross-repo relative links (e.g., `../juniper-data/...`) resolve
> locally when all Juniper repos are checked out as siblings. They are skipped during CI
> validation. Source code file links use GitHub URLs for durability. See
> [CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md](CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md) for details.

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
- [Claude Automation Script](#claude-automation-script)
  - [Validate wake_the_claude.bash usage/help flags](#validate-wake_the_claudebash-usagehelp-flags)
  - [Enable debug mode and verify clean stderr](#enable-debug-mode-and-verify-clean-stderr)
  - [Troubleshoot --resume validation failures](#troubleshoot---resume-validation-failures)
  - [Troubleshoot --id UUID generation fallback](#troubleshoot---id-uuid-generation-fallback)
  - [Verify pattern-matching hardening (no eval)](#verify-pattern-matching-hardening-no-eval)
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
  - [Validate Documentation Links Locally](#validate-documentation-links-locally)
  - [Troubleshoot Cross-Repo Link Checks](#troubleshoot-cross-repo-link-checks)
- [Claude Code Session Script](#claude-code-session-script)
  - [Entry Points](#entry-points)
  - [Launch Modes: Interactive vs Headless](#launch-modes-interactive-vs-headless)
  - [Session ID and Resume Workflow](#session-id-and-resume-workflow)
  - [Current Argument-Handling Pitfalls (Known)](#current-argument-handling-pitfalls-known)
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

> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md) | [Deploy .env.example](../juniper-deploy/.env.example)

### Add a New Secret

1. Decrypt: `sops -d --input-type dotenv --output-type dotenv .env.enc > .env`
2. Add the new key-value pair to `.env`
3. Re-encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Commit the encrypted file: `git add .env.enc && git commit -m "chore: add new secret"`
5. If the variable is consumed by Docker, also add it to `juniper-deploy/.env.example` with a commented-out default

> **Pre-commit guard:** The `no-unencrypted-env` hook blocks committing plaintext `.env` files.
> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md) | [SOPS Implementation Plan](SOPS_IMPLEMENTATION_PLAN.md) | [Deploy .env.example](../juniper-deploy/.env.example)

### Change an Existing Secret

Same as [Add a New Secret](#add-a-new-secret) -- decrypt, edit the value, re-encrypt, commit `.env.enc`.

> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md)

### Remove a Secret

1. Decrypt: `sops -d --input-type dotenv --output-type dotenv .env.enc > .env`
2. Remove the key-value pair from `.env`
3. Re-encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Remove any references in code (`settings.py`, `app_config.yaml`, `docker-compose.yml`)
5. Remove from `juniper-deploy/.env.example` if present
6. Commit all changes

> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md)

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

> **Docs:** [juniper-data Settings](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/settings.py) | [juniper-data Security](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/security.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Disable API Key Authentication

Unset or remove the API keys variable. When no keys are configured, authentication is disabled (development mode).

```bash
unset JUNIPER_DATA_API_KEYS
```

> **Docs:** [juniper-data Settings](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/settings.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Add SOPS to a New Repo

1. Copy `.sops.yaml` from an existing repo (all share the same age public key)
2. Create `.env` with the secret values
3. Encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Add `no-unencrypted-env` hook to `.pre-commit-config.yaml`
5. Ensure `.env` is in `.gitignore`
6. Commit `.env.enc` and `.sops.yaml`

> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md) | [SOPS Implementation Plan](SOPS_IMPLEMENTATION_PLAN.md) | [SOPS Audit](SOPS_AUDIT_2026-03-02.md)

### Rotate the SOPS Age Key

1. Generate new age key: `age-keygen -o new-key.txt`
2. Update `~/.config/sops/age/keys.txt` with the new private key
3. Update the `age` public key in `.sops.yaml` across all 8 repos
4. Re-encrypt every `.env.enc`: decrypt with old key, re-encrypt with new
5. Update the `SOPS_AGE_KEY` GitHub Actions secret in each repo
6. Commit updated `.sops.yaml` and `.env.enc` files

> **Docs:** [SOPS Usage Guide](SOPS_USAGE_GUIDE.md) | [Secrets Management Analysis](SECRETS_MANAGEMENT_ANALYSIS.md)

---

## API Endpoints

### Add an Endpoint to juniper-data

1. Create route file: `juniper_data/api/routes/my_resource.py`
2. Define `router = APIRouter(prefix="/my-resource", tags=["my-resource"])`
3. Add route functions with type-annotated Pydantic request/response models
4. Register in `juniper_data/api/app.py`: `app.include_router(my_resource_router, prefix="/v1")`
5. Add tests in `juniper_data/tests/`
6. Run: `pytest juniper_data/tests/ -v`

> **Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [juniper-data API Reference](../juniper-data/docs/api/JUNIPER_DATA_API.md) | [API Schemas](../juniper-data/docs/api/API_SCHEMAS.md) | [App Factory](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/app.py)

### Add an Endpoint to juniper-cascor

Same pattern as juniper-data. Routes live in the FastAPI app under `/v1`. After adding a server-side endpoint, add a corresponding client method to `juniper-cascor-client` (see [Add a Method to juniper-cascor-client](#add-a-method-to-juniper-cascor-client)).

> **Docs:** [juniper-cascor AGENTS.md](../juniper-cascor/AGENTS.md) | [juniper-cascor API Reference](../juniper-cascor/notes/API_REFERENCE.md) | [juniper-cascor API Docs](../juniper-cascor/docs/api/api-reference.md) | [API Schemas](../juniper-cascor/docs/api/api-schemas.md)

### Add a WebSocket Endpoint

juniper-cascor exposes WebSocket endpoints at `/ws/training` (metrics stream) and `/ws/control` (command/response). To add a new WebSocket endpoint:

1. Add the WebSocket route handler in the juniper-cascor API layer
2. Add a corresponding stream class in `juniper-cascor-client/juniper_cascor_client/ws_client.py`
3. Update juniper-canopy if it consumes the new stream

> **Docs:** [juniper-cascor-client WebSocket](https://github.com/pcalnon/juniper-cascor-client/blob/main/juniper_cascor_client/ws_client.py) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md) | [juniper-canopy CasCor Backend Docs](../juniper-canopy/docs/cascor/CASCOR_BACKEND_MANUAL.md)

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

> **Docs:** [juniper-data Security Middleware](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/security.py) | [juniper-data Observability Middleware](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/observability.py) | [App Factory](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/app.py)

---

## Clients

### Add a Method to juniper-data-client

1. Add method to `JuniperDataClient` in `juniper_data_client/client.py`
2. Follow existing pattern: `self._session.get/post(f"{self._base_url}/v1/...")` with error handling
3. Add Pydantic or dataclass models if needed
4. Add tests in `tests/`
5. Run: `pytest tests/ -v`

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [Client Source](https://github.com/pcalnon/juniper-data-client/blob/main/juniper_data_client/client.py)

### Add a Method to juniper-cascor-client

Same pattern as juniper-data-client. REST methods in `client.py`, WebSocket in `ws_client.py`.

> **Docs:** [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md) | [REST Client](https://github.com/pcalnon/juniper-cascor-client/blob/main/juniper_cascor_client/client.py) | [WebSocket Client](https://github.com/pcalnon/juniper-cascor-client/blob/main/juniper_cascor_client/ws_client.py)

### Add a WebSocket Event Handler

In `juniper-cascor-client`, `CascorTrainingStream` supports callback registration for message types: `metrics`, `state`, `topology`, `cascade_add`, `event`.

1. Add `on_<type>(callback)` method to `CascorTrainingStream` in `ws_client.py`
2. Handle the new message type in the async iteration loop
3. Add tests

> **Docs:** [WebSocket Client](https://github.com/pcalnon/juniper-cascor-client/blob/main/juniper_cascor_client/ws_client.py) | [juniper-cascor-client AGENTS.md](../juniper-cascor-client/AGENTS.md)

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

> **Docs:** [Data Client Source](https://github.com/pcalnon/juniper-data-client/blob/main/juniper_data_client/client.py) | [CasCor Client Source](https://github.com/pcalnon/juniper-cascor-client/blob/main/juniper_cascor_client/client.py)

---

## Services

### Start the Full Stack (Docker)

```bash
cd juniper-deploy
make up    # or: docker compose --profile full up -d
```

Starts juniper-data (8100) -> juniper-cascor (8200) -> juniper-canopy (8050) with health-check dependencies.

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md) | [docker-compose.yml](https://github.com/pcalnon/juniper-deploy/blob/main/docker-compose.yml) | [Deploy .env.example](../juniper-deploy/.env.example)

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

> **Docs:** [juniper-deploy AGENTS.md](../juniper-deploy/AGENTS.md) | [docker-compose.yml](https://github.com/pcalnon/juniper-deploy/blob/main/docker-compose.yml)

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

> **Docs:** [juniper-data Settings](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/settings.py) | [Deploy .env.example](../juniper-deploy/.env.example) | [Deploy AGENTS.md Env Vars](../juniper-deploy/AGENTS.md#environment-variables)

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

## Claude Automation Script

### Validate wake_the_claude.bash usage/help flags

```bash
bash scripts/wake_the_claude.bash -u >/tmp/wtc_usage.out 2>/tmp/wtc_usage.err; echo "exit=$?"
bash scripts/wake_the_claude.bash -h >/tmp/wtc_help.out 2>/tmp/wtc_help.err; echo "exit=$?"
```

Expected:

- `-u` exits `1` and prints usage
- `-h` exits `0` and prints usage
- stderr files remain empty (no `command not found` noise)

### Enable debug mode and verify clean stderr

```bash
WTC_DEBUG=1 bash scripts/wake_the_claude.bash -u >/tmp/wtc_debug.out 2>/tmp/wtc_debug.err; echo "exit=$?"
rg "Define Claude Code parameter flags|usage:" /tmp/wtc_debug.out
test ! -s /tmp/wtc_debug.err && echo "stderr clean"
```

`WTC_DEBUG=1` enables parser/flow debug logs. For `-u` and `-h`, debug and usage output are emitted on stdout.

### Troubleshoot --resume validation failures

`--resume` accepts either:

- A UUID value
- A `.txt` basename resolved from `${WTC_SESSIONS_DIR}` (defaults to `scripts/sessions`, no `/` path separators)

Quick failure-path checks (do not require a successful `claude` launch):

```bash
bash scripts/wake_the_claude.bash --resume ../secret.txt --print; echo "exit=$?"
WTC_DEBUG=1 bash scripts/wake_the_claude.bash --resume ../secret.txt --print >/tmp/wtc_resume_debug.out 2>/tmp/wtc_resume_debug.err
rg "contains path separators|Session ID is invalid" /tmp/wtc_resume_debug.err /tmp/wtc_resume_debug.out
bash scripts/test_resume_file_safety.bash
```

Expected:

- Exit code `1`
- Error output includes path-separator rejection and invalid-session message
- `scripts/test_resume_file_safety.bash` prints `PASS: invalid resume file is preserved`

Edge-case checks for missing and empty `.txt` resume sources:

```bash
script_path="$(pwd)/scripts/wake_the_claude.bash"
session_dir="$(mktemp -d)"
: > "${session_dir}/empty-session-id.txt"

WTC_SESSIONS_DIR="${session_dir}" \
  bash "$script_path" --resume missing-session-id.txt --prompt "hello" >/tmp/wtc_missing.out 2>/tmp/wtc_missing.err
echo "missing_exit=$?"

WTC_SESSIONS_DIR="${session_dir}" \
  bash "$script_path" --resume empty-session-id.txt --prompt "hello" >/tmp/wtc_empty.out 2>/tmp/wtc_empty.err
echo "empty_exit=$?"

test -f "${session_dir}/empty-session-id.txt" && echo "empty_file_preserved=yes"
python3 - <<'PY'
from pathlib import Path
for name in ("missing", "empty"):
    content = (Path(f"/tmp/wtc_{name}.out").read_text() + Path(f"/tmp/wtc_{name}.err").read_text())
    print(f"{name}_usage_count={content.count('usage: wake_the_claude.bash')}")
    print(f"{name}_executing_claude={'Executing claude' in content}")
PY
```

Expected:

- `missing_exit=1` and `empty_exit=1`
- `missing_usage_count=1` and `empty_usage_count=1`
- `missing_executing_claude=False` and `empty_executing_claude=False`
- `empty_file_preserved=yes`

### Troubleshoot --id UUID generation fallback

When `--id` is provided without a value, `wake_the_claude.bash` must generate a session UUID before launching Claude.

Fallback order:

1. `uuidgen`
2. `/proc/sys/kernel/random/uuid`
3. `python3 -c 'import uuid; print(uuid.uuid4())'`

Constraints:

- Each fallback output is validated as a UUID before use.
- If all fallback sources fail or produce invalid output, the script exits `1`, prints usage once, and does not invoke `claude`.

Quick verification:

```bash
rg "command -v uuidgen|/proc/sys/kernel/random/uuid|python3 -c 'import uuid; print\\(uuid.uuid4\\(\\)\\)'" scripts/wake_the_claude.bash
rg "Failed to generate a valid UUID for Session ID" scripts/wake_the_claude.bash
```

Expected:

- `generate_uuid()` includes all three fallback sources in order.
- The `--id` parser path has an explicit hard failure when no valid UUID can be generated.

### Verify pattern-matching hardening (no eval)

```bash
rg "eval" scripts/wake_the_claude.bash
```

Expected: no matches.

The flag pattern parser in `matches_pattern()` now compares candidates in a split loop. Keep flag constant format as `"flag1 | flag2 | flag3"` when adding aliases.

### Run wake_the_claude regression tests

```bash
python3 -m unittest tests/test_wake_the_claude.py -v
bash scripts/test_resume_file_safety.bash
```

This suite stubs the `claude` binary in a temp directory, so no local Claude install is required.

Coverage highlights:

- `--resume` accepts UUIDs and `.txt` basenames resolved from `${WTC_SESSIONS_DIR}`, and rejects path separators/non-`.txt` names.
- Invalid `--resume <file.txt>` content fails validation without deleting the input file.
- Missing `--resume <file.txt>` sources fail cleanly with one usage print and no Claude launch attempt.
- Empty `--resume <file.txt>` sources fail the same invalid-session path and preserve the input file.
- `save_session_id()` refuses symlink targets before writing `<uuid>.txt`.
- Prompt strings containing shell tokens are passed as a single Claude argument (no flag injection).

Troubleshooting:

- If `test_session_id_save_rejects_symlink_target` fails with `1 != 0`, current script behavior is to abort after refusing the symlink write. Decide whether that should remain the contract, then align test expectation and script behavior together.

Run this suite whenever `scripts/wake_the_claude.bash` parsing, session validation, or argument construction changes.

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

> **Docs:** [Dependency Update Workflow](../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md)

### Add an Optional Dependency Group

1. Add new group under `[project.optional-dependencies]` in `pyproject.toml`
2. If creating an "all" aggregate, include the new group
3. Update `juniper-ml` meta-package if the group should be installable via `pip install juniper-ml[...]`
4. Update install instructions in `AGENTS.md` and `README.md`

> **Docs:** [juniper-ml AGENTS.md](../AGENTS.md)

---

## Configuration

### Add a Setting to juniper-data

1. Add field to `Settings` class in `juniper_data/api/settings.py`
2. Define a default constant following the `_JUNIPER_DATA_*` naming convention
3. The field is automatically configurable via `JUNIPER_DATA_<FIELD_NAME>` env var (pydantic-settings)
4. Add to `juniper-deploy/.env.example` if Docker-relevant

> **Docs:** [juniper-data Settings](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/settings.py) | [juniper-data AGENTS.md](../juniper-data/AGENTS.md)

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

> **Docs:** [juniper-canopy AGENTS.md](../juniper-canopy/AGENTS.md) | [App Config YAML](https://github.com/pcalnon/juniper-canopy/blob/main/conf/app_config.yaml) | [Constants Guide](../juniper-canopy/docs/cascor/CONSTANTS_GUIDE.md)

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

> **Docs:** [juniper-data Settings](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/settings.py) | [juniper-cascor Logging Config](https://github.com/pcalnon/juniper-cascor/blob/main/conf/logging_config.yaml) | [juniper-canopy Logging Config](https://github.com/pcalnon/juniper-canopy/blob/main/conf/logging_config.yaml) | [Deploy .env.example](../juniper-deploy/.env.example)

### Enable JSON Logging

```bash
export JUNIPER_DATA_LOG_FORMAT=json       # juniper-data
export JUNIPER_CASCOR_LOG_FORMAT=json     # juniper-cascor
export JUNIPER_CANOPY_LOG_FORMAT=json     # juniper-canopy
```

JSON output includes `request_id`, `service`, `timestamp`, `level`, and `message` fields.

> **Docs:** [juniper-data Observability](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/observability.py) | [Deploy .env.example](../juniper-deploy/.env.example)

### Enable Sentry Error Tracking

Set the DSN environment variable for each service:

```bash
export JUNIPER_DATA_SENTRY_DSN="https://your-dsn@sentry.io/project"
export JUNIPER_CASCOR_SENTRY_DSN="https://your-dsn@sentry.io/project"
export JUNIPER_CANOPY_SENTRY_DSN="https://your-dsn@sentry.io/project"
```

> **Docs:** [juniper-data Observability](https://github.com/pcalnon/juniper-data/blob/main/juniper_data/api/observability.py) | [Deploy .env.example](../juniper-deploy/.env.example)

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

- **Grafana**: <http://localhost:3000> (admin / admin)
- **Prometheus**: <http://localhost:9090>

> **Docs:** [Observability Guide](../juniper-deploy/docs/OBSERVABILITY_GUIDE.md) | [Deploy Makefile](../juniper-deploy/Makefile)

### View Grafana Dashboards

Four auto-provisioned dashboards in the "Juniper" folder:

| Dashboard        | UID                | Purpose                                                                    |
|------------------|--------------------|----------------------------------------------------------------------------|
| Juniper Overview | `juniper-overview` | Cross-service health, request rates, error rates, latency (home dashboard) |
| JuniperData      | `juniper-data`     | Dataset generation metrics, cache status, build info                       |
| JuniperCascor    | `juniper-cascor`   | Training sessions, loss/accuracy, hidden units, inference                  |
| JuniperCanopy    | `juniper-canopy`   | WebSocket connections/messages, demo mode, build info                      |

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

> **Docs:** [Dashboard Providers YAML](https://github.com/pcalnon/juniper-deploy/blob/main/grafana/provisioning/dashboards/dashboard-providers.yml) | [Grafana Provisioning Docs](https://grafana.com/docs/grafana/latest/administration/provisioning/)

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

1. **Metrics not in Prometheus?** Verify `*_METRICS_ENABLED=true` is set (check `.env.observability`). Check <http://localhost:9090/targets> — all should show "UP". Curl the service `/metrics` endpoint directly: `curl http://localhost:8100/metrics`.

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

> **Docs:** [PyPI Publish Procedure](pypi-publish-procedure.md)

### Add a CI Job

1. Edit `.github/workflows/ci.yml` in the target repo
2. Follow the existing pattern: SHA-pinned actions, Python version matrix, `needs:` dependencies
3. Add the new job to the `required-checks` quality gate aggregator
4. Test locally with `act` or by pushing to a feature branch

CI pipeline: pre-commit -> unit-tests -> integration-tests -> build -> security -> lockfile-check -> docs -> required-checks -> notify.

> **Docs:** [juniper-canopy CI/CD Reference](../juniper-canopy/docs/ci_cd/CICD_REFERENCE.md) | [juniper-canopy CI/CD Manual](../juniper-canopy/docs/ci_cd/CICD_MANUAL.md) | [juniper-cascor CI Reference](../juniper-cascor/docs/ci/reference.md) | [juniper-cascor CI Manual](../juniper-cascor/docs/ci/manual.md)

### Validate Documentation Links Locally

Use the mode that matches your goal:

| Goal                              | Command                                                                                     | Notes                                                                           |
|-----------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Match PR CI behavior              | `python scripts/check_doc_links.py --exclude templates --exclude history --cross-repo skip` | Fast and CI-parity. Cross-repo links are counted as skipped, not errors.        |
| Full local validation             | `python scripts/check_doc_links.py --cross-repo check`                                      | Validates cross-repo links against sibling repos on disk.                       |
| Audit link growth without failing | `python scripts/check_doc_links.py --cross-repo warn`                                       | Prints cross-repo warnings and exits non-failing unless other links are broken. |

If `--cross-repo` is omitted, the default mode is `check`.

`check` mode requires Juniper repos as siblings under a shared parent directory. The script auto-discovers this parent via `git rev-parse --git-common-dir`, which works for standard checkouts and linked worktrees.

### Troubleshoot Cross-Repo Link Checks

```bash
git rev-parse --git-common-dir
```

If `--cross-repo check` reports "Ecosystem root not found":

1. Verify sibling layout: the parent directory should contain `juniper-ml` and other Juniper repos (for example `juniper-data`, `juniper-cascor`, `juniper-canopy`).
2. Re-run with CI parity mode to unblock PR checks while keeping local checks clean:
   `python scripts/check_doc_links.py --exclude templates --exclude history --cross-repo skip`
3. Use the scheduled full validation workflow for periodic ecosystem checks:
   `.github/workflows/docs-full-check.yml` (runs weekly and on manual dispatch).

> **Docs:** [Cross-Repo Link Resolution Proposal](CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md) | [docs-full-check.yml](../.github/workflows/docs-full-check.yml)

---

## Claude Code Session Script

### Entry Points

Use one of these launcher entry points:

```bash
# Interactive (foreground) session; blocks until Claude exits
bash scripts/wake_the_claude.bash \
  --id \
  --worktree \
  --effort high \
  --prompt "Review recent test failures and suggest fixes"

# Headless/background mode (nohup) by adding --print
bash scripts/wake_the_claude.bash \
  --id \
  --worktree \
  --effort high \
  --prompt "Review recent test failures and suggest fixes" \
  --print
```

Notes:

- `--print` enables headless mode (`nohup ... &`) and writes logs to `logs/wake_the_claude.nohup.log`.
- Without `--print`, the script runs `claude` directly in the foreground (interactive mode).
- `--id` stores the generated/provided UUID in `scripts/sessions/<uuid>.txt` by default.
- Storage locations are configurable via `WTC_SESSIONS_DIR` and `WTC_LOGS_DIR`.
- `WTC_DEBUG=1` enables parser and validation debug output.

### Use the Default Interactive Wrapper

Wrapper behavior:

- Invokes `scripts/default_interactive_session_claude_code.bash`.
- Always includes `--id`, `--worktree`, `--effort high`.
- Does **not** include `--dangerously-skip-permissions` unless `CLAUDE_SKIP_PERMISSIONS=1` is set
- Injects default prompt text (`"Hello World, Claude!"`) unless you pass `--prompt ...`.
- Passes through any extra arguments (for example `./cly --prompt "Investigate failing tests"`).

Wrapper defaults:

- `--id --worktree --effort high --prompt "Hello World, Claude!"`
- Currently opts into `--dangerously-skip-permissions` by default.

Use the repo-root launcher symlink for quick interactive sessions with default flags:

```bash
./cly
```

Examples:

```bash
# add your own prompt
./cly --prompt "Audit the latest CI failures"

# explicitly opt in to skip-permissions mode
CLAUDE_SKIP_PERMISSIONS=1 ./cly --prompt "Run fully autonomous"
```

### Launch Modes: Interactive vs Headless

Interactive mode (default; runs in the foreground):

```bash
bash scripts/wake_the_claude.bash \
  --id \
  --worktree \
  --dangerously-skip-permissions \
  --effort high \
  --prompt "Review failing tests and suggest root causes"
```

Headless mode (adds `--print`; launches with `nohup ... &`):

```bash
bash scripts/wake_the_claude.bash \
  --id \
  --worktree \
  --dangerously-skip-permissions \
  --effort high \
  --prompt "Review failing tests and suggest root causes" \
  --print
```

Headless logging behavior:

- Primary log file: `wake_the_claude.nohup.log` in the current working directory.
- Fallback log file (if CWD is not writable): `${HOME}/wake_the_claude.nohup.log`.
- If neither location is writable, launch fails with non-zero exit.

### Session ID and Resume Workflow

Resume by saved session file (basename only, loaded from `${WTC_SESSIONS_DIR:-scripts/sessions}`):

Session generation:

```bash
# Generate and persist a new session ID to <uuid>.txt
bash scripts/wake_the_claude.bash --id --prompt "hello"
# Persist a provided session ID to <uuid>.txt
bash scripts/wake_the_claude.bash --id 3e160ecb-feb5-4047-8438-171fb13db8e5 --prompt "hello"
```

Resume inputs:

- The token after any resume alias must be either a UUID or a `.txt` basename resolved under `WTC_SESSIONS_DIR` (defaults to `scripts/sessions/`).
  - `--resume` accepts either a UUID or a local `.txt` filename.
  - Resume filenames must be basenames only (no `/` path separators).
  - Resume filenames must end in `.txt`.
  - Resume file contents must be a valid UUID.

- If the next token is another flag, the script treats resume as missing/invalid and exits non-zero.
- Alias matching is exact; typo variants are rejected.

Resume examples:

```bash
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "Continue previous thread"
bash scripts/wake_the_claude.bash --resume-session 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "Continue previous thread"
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd.txt --prompt "Continue previous thread"
```

Safety constraints:

- `--id` refuses to write if `<uuid>.txt` is a symlink.
- Invalid resume values fail before launching `claude`.
- Invalid or missing `.txt` resume files are preserved (not deleted).

### Current Argument-Handling Pitfalls (Known)

Current implementation detail in `scripts/wake_the_claude.bash`:

- `claude` is invoked with unquoted `${CLAUDE_CODE_PARAMS[@]}`.
- Prompt text is appended as a quoted string literal (`"\"${prompt}\""`), then expanded unquoted.

Practical impact:

- Prompt strings are split on spaces/tokens at launch time instead of being guaranteed single-argument payloads.
- Some flags with values are assembled as combined strings and rely on shell splitting at invocation.

Verification command:

```bash
python3 -m unittest -v tests/test_wake_the_claude.py
```

### Session ID and Resume Workflow, Claude Code Session Script

Session generation:

```bash
# Generate and persist a new session ID to <uuid>.txt
bash scripts/wake_the_claude.bash --id --prompt "hello"

# Persist a provided session ID to <uuid>.txt
bash scripts/wake_the_claude.bash --id 3e160ecb-feb5-4047-8438-171fb13db8e5 --prompt "hello"
```

Resume by saved session file (basename only, from `${WTC_SESSIONS_DIR}`):

```bash
bash scripts/wake_the_claude.bash \
  --resume session-id.txt \
  --prompt "Continue from previous analysis"
```

Notes:

- Resume filename lookups occur in `scripts/sessions/` by default (or `WTC_SESSIONS_DIR` if overridden).
- Pass only the filename basename for `--resume`; path separators are rejected.

### Session ID Files and Safety Constraints

- `--resume` accepts either a UUID or a `.txt` filename looked up in `${WTC_SESSIONS_DIR}` (default `scripts/sessions`).
- Filenames containing `/` are rejected to block path traversal.
- Non-`.txt` resume filenames are rejected.
- Resume file content must itself be a valid UUID.
- Resume reads are non-destructive: session files are not deleted.
- `--id` refuses to write when the target `*.txt` path is a symlink.

Resume by saved session file (basename only, loaded from `${WTC_SESSIONS_DIR:-scripts/sessions}`):

```bash
bash scripts/wake_the_claude.bash \
  --resume session-id.txt \
  --prompt "Continue from previous analysis"
```

Resume examples:

```bash
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "Continue previous thread"
bash scripts/wake_the_claude.bash --resume-session 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "Continue previous thread"
bash scripts/wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd.txt --prompt "Continue previous thread"
```

Notes:

- Resume filename lookups occur in `scripts/sessions/` by default (or `WTC_SESSIONS_DIR` if overridden).
- Pass only the filename basename for `--resume`; path separators are rejected.

Safety constraints:

- `--id` refuses to write if `<uuid>.txt` is a symlink.
- Invalid resume values fail before launching `claude`.
- Invalid or missing `.txt` resume files are preserved (not deleted).

### Current Argument-Handling Pitfalls (Known), Claude Code Session Script

Current implementation detail in `scripts/wake_the_claude.bash`:

- `claude` is invoked with unquoted `${CLAUDE_CODE_PARAMS[@]}`.
- Prompt text is appended as a quoted string literal (`"\"${prompt}\""`), then expanded unquoted.

Practical impact:

- Prompt strings are split on spaces/tokens at launch time instead of being guaranteed single-argument payloads.
- Some flags with values are assembled as combined strings and rely on shell splitting at invocation.

Verification command:

```bash
python3 -m unittest -v tests/test_wake_the_claude.py
```

If prompt/session forwarding regressions appear, prefer prompt files with simple content and verify the emitted launch line before relying on unattended runs.

### Troubleshoot Resume Failures

Enable debug logging for parser/validation traces:

```bash
WTC_DEBUG=1 bash scripts/wake_the_claude.bash --resume session-id.txt --prompt "hello" 2>&1
```

Common failure patterns:

| Symptom                                                                     | Likely Cause                                                     | Fix                                                                                                       |
|-----------------------------------------------------------------------------|------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `Error: Session ID is invalid. Exiting...`                                  | Invalid UUID or file content                                     | Verify UUID format in value/file                                                                          |
| `Error: Received Resume Flag but no Valid Session ID to Resume. Exiting...` | `--resume` provided without value                                | Provide UUID or `.txt` basename after flag                                                                |
| Resume by file fails immediately                                            | Filename includes `/`, non-`.txt` ext, not in `WTC_SESSIONS_DIR` | Use a basename-only `*.txt` file in `scripts/sessions/` (or set `WTC_SESSIONS_DIR`)                       |
| `--resume-session` or `--resume-thread` not recognized                      | Flag-alias parsing regression                                    | Run `test_resume_alias_flag_passes_session_id_to_claude`, inspect `matches_pattern()` alias list handling |

> **Docs:** [Launcher Script](../scripts/wake_the_claude.bash) | [Interactive Wrapper](../scripts/default_interactive_session_claude_code.bash) | [Manual Harness](../scripts/test.bash) | [Regression Tests](../tests/test_wake_the_claude.py)

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

> **Docs:** Per-repo [WORKTREE_SETUP_PROCEDURE.md](../juniper-data/notes/WORKTREE_SETUP_PROCEDURE.md) | [Ecosystem Worktree Conventions](../AGENTS.md#worktree-procedures-mandatory--task-isolation) | [Worktree Setup Procedure](WORKTREE_SETUP_PROCEDURE.md)

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

> **Docs:** Per-repo [WORKTREE_CLEANUP_PROCEDURE_V2.md](WORKTREE_CLEANUP_PROCEDURE_V2.md) | [Ecosystem Worktree Conventions](../AGENTS.md#worktree-procedures-mandatory--task-isolation)

---

## Claude Automation Scripts

### Resume a Claude Session

Use `scripts/wake_the_claude.bash` with `--resume` to continue an existing Claude session:

```bash
# Resume directly from a UUID (interactive by default)
./scripts/wake_the_claude.bash --resume 3e160ecb-feb5-4047-8438-171fb13db8e5

# Resume from a saved file in scripts/sessions (default WTC_SESSIONS_DIR)
echo "3e160ecb-feb5-4047-8438-171fb13db8e5" > scripts/sessions/session-id.txt
./scripts/wake_the_claude.bash --resume session-id.txt --print
```

`--resume` validation rules:

1. Accepts either a UUID value or a filename.
2. Filenames must be basename-only (no `/` path separators).
3. Filenames must end in `.txt`.
4. File contents must be a valid UUID.
5. Filename lookup is scoped to `${WTC_SESSIONS_DIR}` (default `scripts/sessions`).
6. Session ID files are read, not deleted, during resume.

Common failure messages and fixes:

| Error message                                             | Meaning                                                    | Fix                                                                |
|-----------------------------------------------------------|------------------------------------------------------------|--------------------------------------------------------------------|
| `Session ID filename contains path separators — rejected` | A path like `../file.txt` or `dir/file.txt` was passed     | Place the file in `${WTC_SESSIONS_DIR}` and pass only the basename |
| `Session ID filename must have .txt extension — rejected` | A non-`.txt` file was passed                               | Rename to `.txt` or pass the UUID directly                         |
| `Session ID file did not contain a valid UUID`            | The file content is not a UUID                             | Replace file contents with a single UUID value                     |
| `Session ID is invalid`                                   | Input was neither valid UUID nor valid `.txt` session file | Re-run with a UUID or valid `.txt` file                            |

### Generate and Save a Session ID File

The same script can generate or persist session IDs via `--id`:

```bash
# Generate a new UUID and save it to scripts/sessions/<uuid>.txt
./scripts/wake_the_claude.bash --id --print

# Save a specific UUID (validated first)
./scripts/wake_the_claude.bash --id 3e160ecb-feb5-4047-8438-171fb13db8e5 --print
```

`--id` safety behavior:

1. UUIDs are validated before writing session files.
2. Invalid UUID values fail fast and no file is written.
3. Files are written to `${WTC_SESSIONS_DIR}` (default `scripts/sessions`) as `<uuid>.txt`.

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

**Docs:** [juniper-data AGENTS.md](../juniper-data/AGENTS.md) | [Data Contract](../AGENTS.md#data-contract)

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

> **Docs:** [juniper-data-client AGENTS.md](../juniper-data-client/AGENTS.md) | [Client Source](https://github.com/pcalnon/juniper-data-client/blob/main/juniper_data_client/client.py) | [Data Contract](../AGENTS.md#data-contract)

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

**Last Updated:** March 11, 2026
**Version:** 1.3.0
**Maintainer:** Paul Calnon
