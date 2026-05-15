# Requirements — juniper-cascor-worker (cwk)

**Total entries**: 16

**By status**: proposed=4 | shipped=12

**By priority**: P0=1 | P1=8 | P2=6 | P3=1

**By category**: SEC=4 | DOC=3 | TOOL=3 | TEST=3 | WS=2 | DEP=1

---

### JR-CWK-SEC-001 — v0.2.0 breaking change: remove hardcoded default auth key ("juniper"), make WORKER_AUTH_KEY environment variable required at worker startup with clear error message if not set.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 27-50)

**Detail**:

Breaking change for 0.1.0→0.2.0 (SemVer minor allowed pre-1.0). Rationale: hardcoded default allowed any network-accessible actor to register workers. Removed the 'juniper' default. WORKER_AUTH_KEY now REQUIRED with validation at startup (clear error if not set). Migration: set WORKER_AUTH_KEY environment variable explicitly before worker startup. For production: source from secret store (Docker secrets, K8s secrets, Vault, SOPS-encrypted env file) rather than plaintext export.

**Notes**:

Related: v0.3.0 renamed WORKER_AUTH_KEY to CASCOR_AUTH_TOKEN and the CLI flag from --api-key to --auth-token. Operators upgrading directly from v0.1.x to v0.3.0 should consult v0.3.0 release notes for mapping.

### JR-CWK-DOC-001 — AGENTS.md critical fixes: update version metadata (0.1.0→0.3.0), CLI command flags, env vars defaults, and flake8 line-length to match current codebase.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 9-36)

**Detail**:

Phase 1 critical corrections (blocking): (1.1) Update header version from 0.1.0 to 0.3.0, date to 2026-04-02. (1.2) Replace legacy --host/--port command with WebSocket-mode --server-url/--auth-token as default, add --legacy mode. (1.3) Remove incorrect 'juniper' default for CASCOR_AUTHKEY, add all WebSocket env vars (CASCOR_SERVER_URL, CASCOR_AUTH_TOKEN, CASCOR_HEARTBEAT_INTERVAL, etc.), label legacy-only variables. (1.4) Change flake8 --max-line-length from 120 to 512.

### JR-CWK-DOC-002 — AGENTS.md missing core architecture sections: WebSocket mode, binary tensor protocol, TLS/mTLS support, task executor, exception hierarchy, and deprecation status.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 37-79)

**Detail**:

Phase 2 missing core architecture (high priority): (2.1) Application Architecture section (two-mode WebSocket/legacy, communication flow, worker lifecycle, module dependency graph). (2.2) WebSocket mode docs (CascorWorkerAgent async event loop, WorkerConnection class, binary tensor protocol JSON+struct, TLS/mTLS config). (2.3) Task execution pipeline (execute_training_task, CandidateUnit dynamic import from cascor, --cascor-path flag). (2.4) Public API section (all __init__.py exports, CascorWorkerAgent/CandidateTrainingWorker interfaces, WorkerConfig dataclass, exception hierarchy). (2.5) Complete CLI reference (all flags with WebSocket/Legacy/Shared labels, signal handling, --cascor-path).

### JR-CWK-SEC-002 — v0.2.0 security infrastructure: add .github/workflows/security-scan.yml for weekly scheduled Bandit and pip-audit scanning, Dependabot configuration, SOPS config, and SHA-pinned GitHub Actions.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 51-77)

**Detail**:

Added .github/workflows/security-scan.yml for weekly Bandit (static security) and pip-audit (dependency CVE scanning). Added SOPS configuration (.sops.yaml) and .env.example for secrets management. Updated .gitignore to cover all .env variants. SHA-pinned all GitHub Actions to immutable commit hashes. Added cross-repo CI dispatch to juniper-cascor on push to main. Added Dependabot configuration for weekly automated dependency updates. Added CODEOWNERS file for PR review routing.

### JR-CWK-SEC-003 — v0.3.0 CVE fix: bump setuptools minimum version to >=82.0 in pyproject.toml build-system requirements to remediate source distribution CVE.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 95-109)

**Detail**:

setuptools CVE affecting source distribution handling; bumped to >=82.0. Bandit pre-commit hook tuned to avoid false positives on known-safe test fixtures (B105: hardcoded_password_string suppressed for test auth_token fields). pip-audit dependency scanning runs in CI; torch +cpu local version handling fixed to enable reliable scanning of worker dependency tree.

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

### JR-CWK-WS-001 — v0.3.0 major rewrite: WebSocket-based CascorWorkerAgent replaces BaseManager-based CandidateTrainingWorker as default, with TLS/mTLS support and async event loop.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 10-39)

**Detail**:

v0.3.0 (2026-04-08): WebSocket worker agent (new default) with long-lived WebSocket, work units pushed from cascor backend, binary tensor frames (struct-encoded shape/dtype/numpy data), worker capability reporting (CPU cores, GPU, versions on connect), heartbeat keepalive loop. New classes: CascorWorkerAgent (async event loop), WorkerConnection (WebSocket transport with TLS/mTLS and exponential backoff reconnection). New modules: ws_connection.py, task_executor.py (isolated training pipeline). New CLI flags: --tls-cert, --tls-key, --tls-ca for mTLS. Legacy mode (CandidateTrainingWorker) preserved behind --legacy flag with DeprecationWarning, will be removed in next major. Auth token rename: --api-key/CASCOR_API_KEY → --auth-token/CASCOR_AUTH_TOKEN (old names retained as deprecated fallbacks).

**Notes**:

[v2 ARCH→WS re-bucket] Backward-compatible at deployment level via --legacy. Operators may continue legacy mode during migration window. Default mode changed; no fallback default.

### JR-CWK-TOOL-001 — Worktree cleanup procedure with CWD continuity: create new worktree before removing old one to avoid trapping Claude Code sessions in invalid paths.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (lines 1-15)

**Detail**:

The V1 procedure (see notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md) removed the worktree directory without first creating a replacement, leaving the session trapped. V2 creates a new worktree and switches CWD before removing the old one (Phase 2 must complete before Phase 4). Phases: 1 Save & Push, 2 Create New Worktree (session continuity gate), 3 Merge & Pull Request, 4 Remove Old Worktree (prerequisite: new CWD verified), 5 Verify.

**Design**:

Phase 2 is the critical gate: CWD must move to the new worktree (Step 5) before the old one is removed (Phase 4, Step 9). The procedure enforces this with explicit verification gates in Step 6.

### JR-CWK-TEST-001 — Test import mocking fix: add patch.dict(sys.modules, {"cascade_correlation": None, ...}) to test_connect_without_cascor_raises and test_start_without_cascor_raises to force ImportError regardless of JuniperCascor environment.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/history/FIX_TEST_IMPORT_MOCKING_PLAN.md` (lines 1-50)

**Detail**:

Two tests fail when run in JuniperCascor conda environment where cascade_correlation package is installed: (1) test_connect_without_cascor_raises expects ImportError handler but import succeeds, code attempts real TCP connection to manager (127.0.0.1:50000), gets ConnectionRefusedError wrapped as WorkerConnectionError, regex match fails. (2) test_start_without_cascor_raises bypasses "Not connected" guard, import succeeds, code spawns real forkserver processes, returns normally without raising. Fix: wrap both tests' calls to worker.connect()/start() in patch.dict(sys.modules, {"cascade_correlation": None, "cascade_correlation.cascade_correlation": None}), forcing ImportError on import statement. Matches existing pattern in 6 other tests (lines 87, 115, 134, 161, 186, 307). Setting sys.modules key to None causes Python's import machinery to raise ImportError: import of <module> halted; None in sys.modules.

### JR-CWK-DOC-003 — AGENTS.md missing supplementary content: directory layout, expanded key files, test details, CI/CD, pre-commit hooks, scripts, Python version requirements, and resource location guide.

**Status**: shipped  **Priority**: P2  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 80-160)

**Detail**:

Phase 3 supplementary content (medium priority): (3.1) Expand Key Files table (all Python modules, docs/, scripts/, .github/workflows/, config files). (3.2) Add directory layout tree. (3.3) Update dependencies (add websockets>=11.0). (3.4) Add CI/CD section (6-job pipeline, weekly security scan, PyPI publish, Dependabot). (3.5) Add pre-commit hooks (black, isort, flake8, mypy, bandit, shellcheck, yamllint, markdownlint, SOPS). (3.6) Add test details (6 test files, ~83 tests, fixtures, 80% coverage threshold). (3.7) Add Python version requirements (>=3.11, supported 3.11-3.14, PEP 561 py.typed). (3.8) Add docs/ section. (3.9) Add scripts/ section. Phase 4 cleanup: remove stale conf/ references, update ecosystem compatibility version. Phase 5 validation: run link checker, cross-reference CLI/env vars, test suite.

### JR-CWK-TOOL-002 — Thread handoff procedure: preserve context fidelity when thread compaction degrades output by proactively handing off to fresh thread before context saturation.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/THREAD_HANDOFF_PROCEDURE.md` (lines 1-35)

**Detail**:

Thread compaction introduces information loss (subtle decisions, edge cases, partial progress, reasoning get dropped). Triggers: (1) context saturation after 15+ tool calls or 5+ file edits, (2) phase boundary completion, (3) degraded recall (re-reading files), (4) multi-module transitions, (5) user request. Do NOT handoff when task is nearly complete (<2 steps) or thread is still sharp. Handoff goal structure: original task, completed items, remaining work, key discoveries, file paths.

**Design**:

Handoff protocol: (1) Checkpoint current state (task, completed, remaining, discovered, files in play), (2) Compose concise actionable goal (be specific, include paths, state decisions, mention test status, keep <500 words), (3) Present to user via handoff() tool if available (follow=true for current thread stop, follow=false rare).

### JR-CWK-TOOL-003 — Worktree setup procedure: standardized protocol for creating git worktrees when beginning a new task, centralizing worktrees in /home/pcalnon/Development/python/Juniper/worktrees/.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_SETUP_PROCEDURE.md` (lines 1-30)

**Detail**:

Prerequisites: must be in primary directory (not already in worktree), working tree clean, target branch not already checked out elsewhere. Protocol: (1) Ensure clean state, (2) Fetch and update parent branch (typically main), (3) Create working branch, (4) Compute worktree directory name using format <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>, (5) Create worktree, (6) Verify and begin work.

**Design**:

Naming convention: <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>. All worktrees in /home/pcalnon/Development/python/Juniper/worktrees/. Example: juniper-cascor-worker--feature--add-gpu-support--20260225-1430--047c3f61.

### JR-CWK-TEST-002 — Bandit B105 pre-commit false positives in test files: suppress B105 (hardcoded_password_string) in test Bandit hook, targeting known-safe test fixture credential values.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 99-106)

**Detail**:

Root cause: auth_token field matches Bandit regex (RE_WORDS includes "token") introduced in WebSocket Phase 2 refactoring after pre-commit config finalized. Original api_key didn't trigger B105 ("key" not in word list). 11 B105 false positives across 3 test files (test_cli.py:4, test_config.py:6, test_worker_agent.py:1) — all test fixtures using dummy credentials. Solution: Add B105 to --skip in .pre-commit-config.yaml test Bandit hook (line 195), maintaining numerical order (--skip=B101,B104,B105,B108,B110,B311). Source Bandit hook unaffected; detect-private-key hook catches real secrets.

### JR-CWK-WS-002 — Hardcoded values refactoring: create juniper_cascor_worker/constants.py to consolidate ~50 hardcoded values (protocol messages, activation functions, training defaults, WebSocket config, validation bounds).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 1-50)

**Detail**:

~50 hardcoded values across 7 source files. Existing infrastructure: config.py WorkerConfig dataclass (8 field defaults, partial coverage). Gaps: protocol message type strings (7), activation function names (3), training hyperparameters (6 — epochs, learning rate, display frequency, value scales), WebSocket config (4), config duplicates across config.py/cli.py/env defaults (6), validation constants (2), error handling (2). Coverage summary: ~3 covered (partial), ~47 not covered. Proposed solution: create constants.py with sections for protocol types, activation functions, training defaults, WebSocket, config defaults, validation, error handling. Update config.py, cli.py, worker.py, task_executor.py, ws_connection.py to import from constants.py. Key benefit: eliminates 3-way duplication between config.py, cli.py, env var defaults.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CWK-TEST-003 — Test warning elimination: suppress DeprecationWarnings in test_worker.py (expected legacy API tests), RuntimeWarnings for unawaited CascorWorkerAgent coroutines, enforce warnings-as-errors baseline in pyproject.toml.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 107-144)

**Detail**:

DeprecationWarnings (23): CandidateTrainingWorker.__init__() emits at worker.py:326; test_worker.py exercises deprecated legacy API. Solution: module-level pytestmark filterwarnings in test_worker.py. RuntimeWarnings (3): unawaited CascorWorkerAgent.run() coroutines during mock-based test cleanup. Solution: targeted filterwarnings in pyproject.toml for coroutine pattern. Baseline: filterwarnings = ["error", ...] in pytest config treats all warnings as errors by default with explicit exceptions for known, intentional warnings. Prevents silent warning accumulation; new unexpected warnings cause test failures.

### JR-CWK-SEC-004 — v0.3.0 deprecations: CandidateTrainingWorker (legacy), --api-key CLI flag, CASCOR_API_KEY env var; migrate to CascorWorkerAgent and --auth-token before next major release.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 113-122)

**Detail**:

CandidateTrainingWorker (legacy): use --legacy to opt in; emits DeprecationWarning. --api-key CLI flag (old flag still parsed, deprecated). CASCOR_API_KEY env var (old var still read as fallback, deprecated). Plan migration to CascorWorkerAgent and --auth-token before next major release.

**Notes**:

[v2 ARCH→SEC re-bucket]

