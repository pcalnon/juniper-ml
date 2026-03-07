# Cross-Repository Link Resolution Proposal

## Documentation Link Integrity in a Polyrepo Worktree Environment

| Meta Data         | Value                                                          |
|-------------------|----------------------------------------------------------------|
| **Version:**      | 1.1.0                                                          |
| **Status:**       | Proposed                                                       |
| **Last Updated:** | March 7, 2026                                                  |
| **Author:**       | Paul Calnon (analysis by Claude Code)                          |
| **Project:**      | Juniper - Cascade Correlation Neural Network Research Platform |
| **Scope:**        | All Juniper repositories with `check_doc_links.py`             |
| **Analyzed At:**  | Commit `bc0d582` on `main` branch                              |

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Problem Statement](#problem-statement)
- [Root Cause Analysis](#root-cause-analysis)
  - [Dimension 1: GitHub Actions CI (Single-Repo Checkout)](#dimension-1-github-actions-ci-single-repo-checkout)
  - [Dimension 2: Git Worktrees (Altered Directory Depth)](#dimension-2-git-worktrees-altered-directory-depth)
  - [Dimension 3: Local Scanning of Worktree Directories](#dimension-3-local-scanning-of-worktree-directories)
- [Link Checker Behavior: Dual-Resolution Strategy](#link-checker-behavior-dual-resolution-strategy)
- [Link Classification](#link-classification)
  - [Category A: Cross-Repo Relative Links](#category-a-cross-repo-relative-links)
  - [Category B: Self-Referencing Cross-Repo Links](#category-b-self-referencing-cross-repo-links)
  - [Category C: Missing Intra-Repo Files](#category-c-missing-intra-repo-files)
  - [Category D: False-Negative Deep Relative Link](#category-d-false-negative-deep-relative-link)
  - [Quantitative Breakdown](#quantitative-breakdown)
- [Proposed Solutions](#proposed-solutions)
  - [Component 1: Link Checker Enhancement](#component-1-link-checker-enhancement)
    - [Approach 1A: Cross-Repo Link Classification with Configurable Policy](#approach-1a-cross-repo-link-classification-with-configurable-policy)
    - [Approach 1B: Ecosystem Root Discovery with Fallback](#approach-1b-ecosystem-root-discovery-with-fallback)
    - [Approach 1C: Allowlist-Based Pattern Exclusion](#approach-1c-allowlist-based-pattern-exclusion)
  - [Component 2: Documentation Content Remediation](#component-2-documentation-content-remediation)
    - [Approach 2A: Hybrid Link Strategy (Recommended)](#approach-2a-hybrid-link-strategy-recommended)
    - [Approach 2B: Full GitHub URL Conversion (Considered and Rejected)](#approach-2b-full-github-url-conversion-considered-and-rejected)
    - [Approach 2C: Reference-Style Link Definitions (Complementary)](#approach-2c-reference-style-link-definitions-complementary)
  - [Component 3: Worktree Directory Exclusion](#component-3-worktree-directory-exclusion)
    - [Approach 3A: Exclude .claude/worktrees from Scanning (Recommended)](#approach-3a-exclude-claudeworktrees-from-scanning-recommended)
    - [Approach 3B: Git-Aware File Discovery (Future Enhancement)](#approach-3b-git-aware-file-discovery-future-enhancement)
  - [Component 4: Missing File Resolution](#component-4-missing-file-resolution)
  - [Component 5: Link Checker Security Hardening](#component-5-link-checker-security-hardening)
- [Approaches Considered and Rejected](#approaches-considered-and-rejected)
  - [Move Cheatsheet to Ecosystem Parent Directory](#move-cheatsheet-to-ecosystem-parent-directory)
  - [Check Out Sibling Repos in CI](#check-out-sibling-repos-in-ci)
  - [Documentation Site Generator (MkDocs/Sphinx)](#documentation-site-generator-mkdocssphinx)
- [Ecosystem-Wide Scope](#ecosystem-wide-scope)
- [Recommended Implementation Plan](#recommended-implementation-plan)
  - [Phase 1: Immediate CI Stabilization](#phase-1-immediate-ci-stabilization)
  - [Phase 2: Link Checker Enhancement and Security Hardening](#phase-2-link-checker-enhancement-and-security-hardening)
  - [Phase 3: Documentation Content Cleanup](#phase-3-documentation-content-cleanup)
- [Security Considerations](#security-considerations)
  - [Existing Vulnerability: Filesystem Existence Oracle](#existing-vulnerability-filesystem-existence-oracle)
  - [Path Traversal in Link Resolution](#path-traversal-in-link-resolution)
  - [Input Validation](#input-validation)
  - [Git Command Injection](#git-command-injection)
  - [Ecosystem Repo Name Validation](#ecosystem-repo-name-validation)
  - [CI Supply Chain Security Invariant](#ci-supply-chain-security-invariant)
  - [Cross-Repo Skip Mode: Structural Validation](#cross-repo-skip-mode-structural-validation)
  - [Information Disclosure](#information-disclosure)
- [Maintenance Guidelines](#maintenance-guidelines)
- [Appendix A: Full Broken Link Inventory](#appendix-a-full-broken-link-inventory)
- [Appendix B: Ecosystem Directory Layout Reference](#appendix-b-ecosystem-directory-layout-reference)

---

## Executive Summary

The juniper-ml CI pipeline reports 124 broken documentation links, all from `notes/DEVELOPER_CHEATSHEET.md`. These links reference files in sibling Juniper repositories (e.g., `../juniper-data/AGENTS.md`) using relative paths that cannot be resolved during CI, where only the single juniper-ml repository is checked out.

The problem is compounded by the project's mandatory use of git worktrees for development. Worktrees exist at a different directory depth (`.claude/worktrees/<name>/` or `worktrees/<name>/`) than the standard repository root, causing even locally-valid relative paths to break when running local validation from within a worktree.

Additionally, the link checker has a security weakness: it performs no bounds checking on resolved paths, enabling filesystem probing via crafted markdown links.

This proposal classifies the broken links into four categories, presents multiple solution approaches for each component, and recommends a phased implementation plan that preserves both critical project requirements: **worktree-based development** and **CI documentation verification**.

**Note:** The identical `check_doc_links.py` script exists in at least 6 Juniper repos. This proposal addresses juniper-ml specifically but all enhancements should be propagated ecosystem-wide.

---

## Problem Statement

Two critical Juniper project requirements are in conflict:

1. **Git worktrees for task isolation** -- All feature and bugfix work uses git worktrees, creating repository checkouts at non-standard directory depths.

2. **CI documentation verification** -- The `docs` CI job runs `check_doc_links.py` to validate all markdown links, blocking PRs that contain broken references.

The `DEVELOPER_CHEATSHEET.md` is an ecosystem-wide reference document that lives in juniper-ml but cross-references files across 6 sibling repositories. These cross-repo relative links work only in one specific filesystem layout: when juniper-ml is at `Juniper/juniper-ml/` alongside its sibling repos. They fail in every other context:

- **CI (GitHub Actions):** Only juniper-ml is checked out; sibling repos don't exist.
- **Worktrees (`.claude/worktrees/`):** The directory depth changes, so `../` no longer reaches the ecosystem parent directory.
- **Worktrees (`worktrees/`):** The centralized worktree location has a different parent hierarchy.

---

## Root Cause Analysis

### Dimension 1: GitHub Actions CI (Single-Repo Checkout)

The CI workflow checks out only the juniper-ml repository:

```yaml
# .github/workflows/ci.yml, line 90
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

The link checker resolves `repo_root` as the checkout directory. From `notes/DEVELOPER_CHEATSHEET.md`:

```bash
notes/                          <-- file location
../                             <-- resolves to repo root (juniper-ml/)
../juniper-data/                <-- resolves to juniper-ml/juniper-data/ -- DOES NOT EXIST
```

All 107 cross-repo relative links fail because the sibling repositories are not present. This is the **primary** cause of CI failures and the dimension that blocks PRs.

### Dimension 2: Git Worktrees (Altered Directory Depth)

When working in a worktree, the directory hierarchy differs from the standard layout:

**Standard layout:**

```bash
Juniper/
  juniper-ml/                   <-- repo root
    notes/                      <-- ../juniper-data/ resolves to Juniper/juniper-data/ (EXISTS)
  juniper-data/
  juniper-cascor/
```

**Claude Code worktree layout:**

```bash
Juniper/
  juniper-ml/
    .claude/worktrees/
      purring-bubbling-dragonfly/   <-- worktree root
        notes/                      <-- ../juniper-data/ resolves to .../purring-bubbling-dragonfly/juniper-data/ (MISSING)
```

**Centralized worktree layout:**

```bash
Juniper/
  worktrees/
    juniper-ml--feature--xyz--20260307-1200--abc12345/  <-- worktree root
      notes/                    <-- ../juniper-data/ resolves to .../worktrees/juniper-data/ (MISSING)
```

In both worktree layouts, `../` from `notes/` reaches the worktree root, not the Juniper ecosystem parent directory. This causes cross-repo links to fail when running the link checker locally from a worktree.

### Dimension 3: Local Scanning of Worktree Directories

**Note:** This dimension is a **local-only** concern. The `.claude/worktrees/` directory is not tracked by git and does not exist in CI checkouts.

When the link checker runs locally from the main repo directory, it recursively scans all markdown files including those inside `.claude/worktrees/`. This causes:

1. **Duplicate scanning** -- The same `DEVELOPER_CHEATSHEET.md` is checked once per worktree, multiplying error counts.
2. **False positives from worktrees** -- Cross-repo links that resolve correctly from the main repo fail when the scanner processes worktree copies of the same files.

Evidence from a main-repo scan: 759 markdown files scanned (vs. 68 in a single checkout), with broken links reported across 22 files (mostly worktree copies of the same cheatsheet).

---

## Link Checker Behavior: Dual-Resolution Strategy

The link checker (`scripts/check_doc_links.py`) uses a dual-resolution strategy that is important to understanding the broken link behavior and a related false-negative:

```python
# scripts/check_doc_links.py, line 211-216
target_path = (file_dir / file_part).resolve()                   # Resolution 1: relative to file
target_path_from_root = (repo_root / file_part).resolve()        # Resolution 2: relative to repo root

if target_path.exists() or target_path_from_root.exists():       # Either succeeds = "OK"
    ...
```

A link is considered valid if it resolves to an existing file via **either** path. This fallback is the reason certain links that appear broken are not reported (see Category D below). It also means `repo_root` determination is critical: `Path(__file__).resolve().parent.parent` (the script's grandparent directory).

---

## Link Classification

### Category A: Cross-Repo Relative Links

**Pattern:** `../juniper-<name>/path/to/file`

These links reference files in 6 distinct sibling repositories:

| Prefix                      | Count | Example Target                                                                   |
|-----------------------------|-------|----------------------------------------------------------------------------------|
| `../juniper-deploy/`        | 30    | `AGENTS.md`, `.env.example`, `docker-compose.yml`, `docs/OBSERVABILITY_GUIDE.md` |
| `../juniper-data/`          | 29    | `AGENTS.md`, `juniper_data/api/settings.py`, `docs/api/API_SCHEMAS.md`           |
| `../juniper-cascor/`        | 17    | `AGENTS.md`, `docs/api/api-reference.md`, `conf/logging_config.yaml`             |
| `../juniper-canopy/`        | 14    | `AGENTS.md`, `docs/testing/TESTING_QUICK_START.md`, `conf/app_config.yaml`       |
| `../juniper-cascor-client/` | 10    | `AGENTS.md`, `juniper_cascor_client/client.py`, `ws_client.py`                   |
| `../juniper-data-client/`   | 7     | `AGENTS.md`, `juniper_data_client/client.py`                                     |

**Total: 107 links:**

**Note:** The cheatsheet also contains 8 references to `../AGENTS.md` (the parent ecosystem AGENTS.md). These are **not broken** -- from `notes/`, `../AGENTS.md` resolves to the repo root's own `AGENTS.md`, which exists. These are false negatives (see Category D discussion for the same pattern).

### Category B: Self-Referencing Cross-Repo Links

**Pattern:** `../juniper-ml/notes/<file>` or `../juniper-ml/AGENTS.md`

These links reference files within the same repository but use a cross-repo path style. They fail because from `notes/`, `../juniper-ml/` resolves to `<repo_root>/juniper-ml/` which does not exist.

Unique targets:

| Link                                                 | Correct Relative Path            |
|------------------------------------------------------|----------------------------------|
| `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            | `SOPS_USAGE_GUIDE.md`            |
| `../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md`    | `SOPS_IMPLEMENTATION_PLAN.md`    |
| `../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md`       | `SOPS_AUDIT_2026-03-02.md`       |
| `../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md` | `SECRETS_MANAGEMENT_ANALYSIS.md` |
| `../juniper-ml/notes/pypi-publish-procedure.md`      | `pypi-publish-procedure.md`      |
| `../juniper-ml/AGENTS.md`                            | `../AGENTS.md`                   |

**Total: 12 instances** across lines 95, 106 (x2), 112, 123, 163 (x3), 174 (x2), 500, 720.

These are unambiguously fixable -- they should use direct relative paths within the repo.

### Category C: Missing Intra-Repo Files

**Pattern:** `<filename>.md` (no directory prefix, implies same directory)

These reference files in `notes/` that do not exist. Git history confirms **none of these files were ever committed** to the repository -- they were planned documents that were never created. The resolution is to remove the links or redirect to existing equivalent documentation.

| Referenced File                             | Line | Resolution                                                                       |
|---------------------------------------------|------|----------------------------------------------------------------------------------|
| `plan_7.5_7.6_dependency_management.md`     | 491  | Remove link (planned doc, never created)                                         |
| `STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md` | 575  | Remove link (planned doc, never created)                                         |
| `PYPI_PUBLISH_PROCEDURE.md`                 | 720  | Replace with `pypi-publish-procedure.md` (exists, different filename convention) |
| `PYPI_PUBLISH_PLAN_3_PACKAGES.md`           | 720  | Remove link (planned doc, never created)                                         |
| `WORKTREE_IMPLEMENTATION_PLAN.md`           | 755  | Remove link or redirect to `WORKTREE_SETUP_PROCEDURE.md`                         |

**Total: 5 links:**

**Note:** Line 720 contains both a Category B link (`../juniper-ml/notes/pypi-publish-procedure.md`) and a Category C link (`PYPI_PUBLISH_PROCEDURE.md`). Both need separate fixes.

### Category D: False-Negative Deep Relative Link

**Pattern:** `../../../CLAUDE.md`

In `notes/SECURITY_AUDIT_PLAN.md` (line 845):

```markdown
[Worktree Procedures](../../../CLAUDE.md#worktree-procedures-mandatory--task-isolation)
```

This link attempts to reach the parent Juniper ecosystem `CLAUDE.md` by traversing three directory levels up. However, **the link checker does not report this as broken** due to the dual-resolution fallback:

1. **Resolution 1 (file-relative):** `notes/../../../CLAUDE.md` resolves to two levels above the repo root -- file not found.
2. **Resolution 2 (repo-root-relative):** `repo_root / "../../../CLAUDE.md"` normalizes through `Path.resolve()` to a path that leads to the repo root's `CLAUDE.md` (a symlink to `AGENTS.md`) -- **file found**.

The link passes validation but points to the **wrong document**: it resolves to juniper-ml's own `AGENTS.md` rather than the ecosystem parent `CLAUDE.md` at `Juniper/CLAUDE.md`. This is a **false negative** in the link checker.

**Impact:** 0 broken links in CI (passes validation), but the link is semantically incorrect. The recommended fix is to change to `../CLAUDE.md` (the repo's own `CLAUDE.md`), which contains an identical `#worktree-procedures-mandatory--task-isolation` section and is semantically appropriate as a local reference.

### Quantitative Breakdown

| Category                       | Count   | Fix Complexity                                 | CI Impact                  |
|--------------------------------|---------|------------------------------------------------|----------------------------|
| A: Cross-repo relative links   | 107     | Medium-High                                    | All break in CI            |
| B: Self-referencing cross-repo | 12      | Low (simple path fix)                          | All break in CI            |
| C: Missing intra-repo files    | 5       | Low (remove or redirect)                       | All break in CI            |
| D: False-negative deep link    | 1       | Low (not a CI failure, but semantically wrong) | None (passes via fallback) |
| **Total CI failures**          | **124** |                                                |                            |

---

## Proposed Solutions

### Component 1: Link Checker Enhancement

The link checker needs to distinguish between links it can validate and links it cannot validate in isolation.

#### Approach 1A: Cross-Repo Link Classification with Configurable Policy

**Description:** Enhance the link checker to detect and classify cross-repo links, applying a configurable validation policy.

**Implementation:**

Add a configuration section to the checker that defines known ecosystem repo names:

```python
# Known Juniper ecosystem repositories (sibling repos that may be referenced).
# This set is hardcoded intentionally -- auto-discovery from the filesystem would
# allow a malicious directory name to be trusted. This set is version-controlled
# and changes go through code review.
_ECOSYSTEM_REPOS = {
    "juniper-data",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-ml",
}

_CROSS_REPO_PATTERN = re.compile(
    r"^(?:\.\./)+(?:" + "|".join(re.escape(r) for r in sorted(_ECOSYSTEM_REPOS)) + r")/"
)
```

Add a `--cross-repo` flag with three modes:

| Mode                   | Behavior                                                 | Use Case                                     |
|------------------------|----------------------------------------------------------|----------------------------------------------|
| `skip` (default in CI) | Log cross-repo links as "skipped", don't count as errors | CI where sibling repos unavailable           |
| `warn`                 | Report cross-repo links as warnings (non-blocking)       | Local development awareness                  |
| `check`                | Validate cross-repo links as normal (current behavior)   | Full local validation with all repos present |

**CI integration:**

```yaml
- name: Validate Documentation Links
  run: python scripts/check_doc_links.py --exclude templates --exclude history --cross-repo skip
```

In `skip` mode, the checker outputs a summary annotation: `N cross-repo links skipped` so that a sudden spike in skipped links is visible in CI logs.

**Local validation with ecosystem:**

```bash
python scripts/check_doc_links.py --cross-repo check
```

**Advantages:**

- Transparent: clearly reports which links were skipped and why
- Flexible: configurable per-environment via CLI flag
- Secure: the repo list is explicit and reviewed, not inferred from filesystem
- Maintains full validation capability when repos are available locally

**Disadvantages:**

- Cross-repo links are not validated in CI (links could silently rot)
- Requires maintaining the `_ECOSYSTEM_REPOS` list across all repos

#### Approach 1B: Ecosystem Root Discovery with Fallback

**Description:** Enhance the link checker to discover the ecosystem parent directory and resolve cross-repo links against it, with graceful fallback when siblings are unavailable.

**Implementation:**

```python
import subprocess

def _discover_ecosystem_root(repo_root: Path) -> Path | None:
    """Attempt to find the Juniper ecosystem parent directory.

    Walks up from repo_root looking for a directory that contains
    at least 3 known sibling repos (strong indicator of ecosystem root).
    Also handles worktree detection via git.
    """
    # Method 1: Check if git reports a different toplevel (worktree detection)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip())
            candidate = git_root.parent
            if _is_ecosystem_root(candidate):
                return candidate
    except FileNotFoundError:
        pass

    # Method 2: Walk up from repo_root (limited depth)
    for parent in [repo_root.parent, repo_root.parent.parent]:
        if _is_ecosystem_root(parent):
            return parent

    return None


def _is_ecosystem_root(candidate: Path) -> bool:
    """Check if a directory appears to be the Juniper ecosystem root."""
    found = sum(
        1 for repo in _ECOSYSTEM_REPOS
        if (candidate / repo).is_dir()
    )
    return found >= 3  # Require at least 3 sibling repos present
```

When the ecosystem root is found, cross-repo links are resolved against it. When not found (CI), they are skipped with a warning.

**Advantages:**

- Works automatically in all local environments (standard, worktree, centralized worktree)
- No CLI flag needed for local use
- Validates cross-repo links when possible

**Disadvantages:**

- Adds `subprocess` dependency (the current script is pure Python: `re`, `sys`, `unicodedata`, `pathlib`)
- Filesystem probing adds complexity and fragility
- The "3 repos" heuristic could produce false positives in unexpected layouts
- Walking up the directory tree has path traversal implications (mitigated by checking for specific known directory names only)
- Still cannot validate in CI (same fallback as 1A)

#### Approach 1C: Allowlist-Based Pattern Exclusion

**Description:** Define a configuration file that lists link patterns to skip during validation, with explanation for each.

**Implementation:**

Create `.doc-link-config.yml` at the repo root:

```yaml
# Documentation link validation configuration
# Used by scripts/check_doc_links.py

# Link patterns to skip during CI validation.
# These are cross-repository links that can only resolve in a local
# multi-repo checkout. They are validated locally via --cross-repo check.
skip_patterns:
  - pattern: "^\\.\\./(juniper-data|juniper-cascor|juniper-canopy|juniper-data-client|juniper-cascor-client|juniper-cascor-worker|juniper-deploy|juniper-ml)/"
    reason: "Cross-repo link - validates locally, skipped in CI"
```

The link checker reads this config and applies the skip patterns.

**Advantages:**

- Fully declarative and transparent (config file is versioned and reviewable)
- Easy to extend or modify without code changes
- Patterns and reasons serve as documentation
- Can complement Approach 1A (the `--cross-repo` flag reads patterns from config)

**Disadvantages:**

- Regex patterns can be fragile if link conventions change
- Over-broad patterns could mask legitimate broken links
- Yet another config file to maintain
- Adds a runtime dependency on a YAML parser (unless using a simpler format)

---

### Component 2: Documentation Content Remediation

Independent of how the link checker handles cross-repo links, the documentation content itself should be improved.

#### Approach 2A: Hybrid Link Strategy (Recommended)

**Description:** Use a combination of strategies based on link target stability:

| Target Type                                    | Strategy                              | Example                                                         |
|------------------------------------------------|---------------------------------------|-----------------------------------------------------------------|
| Intra-repo files                               | Relative path (always resolvable)     | `SOPS_USAGE_GUIDE.md`                                           |
| Cross-repo stable files (AGENTS.md, README.md) | Relative path + annotated for CI skip | `../juniper-data/AGENTS.md`                                     |
| Cross-repo source code files                   | GitHub permalink                      | `https://github.com/.../blob/main/juniper_data/api/settings.py` |
| Cross-repo docs (may move)                     | Relative path + annotated             | `../juniper-data/docs/api/API_SCHEMAS.md`                       |
| Ecosystem parent files                         | Local reference                       | `../CLAUDE.md`                                                  |

**Rationale:**

- Relative paths are the most maintainable for stable cross-repo files (AGENTS.md rarely moves)
- Source code file links are inherently fragile (files refactor); GitHub URLs with `main` branch are more durable and clickable from GitHub's rendered markdown
- Intra-repo links should always be direct relative paths

**Category B fix** -- Convert self-referencing cross-repo links to direct relative paths:

```markdown
<!-- BEFORE (broken in CI) -->
[SOPS Usage Guide](../juniper-ml/notes/SOPS_USAGE_GUIDE.md)

<!-- AFTER (always works) -->
[SOPS Usage Guide](SOPS_USAGE_GUIDE.md)
```

**Category D fix** -- Replace deep relative link with local reference:

```markdown
<!-- BEFORE (semantically incorrect -- resolves to wrong doc via fallback) -->
[Worktree Procedures](../../../CLAUDE.md#worktree-procedures-mandatory--task-isolation)

<!-- AFTER (references repo's own CLAUDE.md, which contains the same section) -->
[Worktree Procedures](../CLAUDE.md#worktree-procedures-mandatory--task-isolation)
```

**Note:** The repo's `CLAUDE.md` is a symlink to `AGENTS.md`, which contains the `#worktree-procedures-mandatory--task-isolation` section. This fix changes the semantic target from the ecosystem-level doc to the repo-level doc, but both contain the same content.

**Advantages:**

- Each link type uses the strategy best suited to its stability
- Cross-repo relative links remain human-readable and work locally
- All intra-repo links are immediately fixable

**Disadvantages:**

- Mixed strategies require awareness of the conventions
- GitHub URLs for source code files may become stale if repos are renamed or go private

#### Approach 2B: Full GitHub URL Conversion (Considered and Rejected)

Converting all 107 cross-repo relative links to absolute GitHub URLs (e.g., `https://github.com/pcalnon/juniper-data/blob/main/AGENTS.md`) would make them universally resolvable. However, this approach is **rejected** because:

- Hardcodes the GitHub owner and branch name (fragile if repos transfer or fork)
- 107+ URLs to construct and maintain
- Links break if repos go private
- Loses the "living reference" quality of relative paths that work when repos are side-by-side
- Mass URL updates needed if the GitHub organization changes

Approach 2A's hybrid strategy selectively uses GitHub URLs only for source code files, where the trade-off is favorable.

#### Approach 2C: Reference-Style Link Definitions (Complementary)

**Note:** This is an orthogonal formatting choice that can be combined with any approach above, not a standalone alternative.

Use markdown reference-style links with definitions in a centralized block:

```markdown
## API Endpoints

> **Docs:** [juniper-data AGENTS.md][jd-agents] | [API Schemas][jd-schemas]

<!-- Reference definitions (maintained in one place) -->
[jd-agents]: ../juniper-data/AGENTS.md
[jd-schemas]: ../juniper-data/docs/api/API_SCHEMAS.md
```

**Advantages:**

- All link targets are defined in one place per file, making bulk updates easy
- Cleaner inline text (shorter link syntax)
- Easy to script bulk updates

**Disadvantages:**

- Less readable for contributors unfamiliar with reference-style links
- Adds a large reference block at the end of files

---

### Component 3: Worktree Directory Exclusion

The link checker must not scan worktree directories when running from the main repo.

#### Approach 3A: Exclude .claude/worktrees from Scanning (Recommended)

**Description:** Add `.claude` to the `_SKIP_DIRS` set in the link checker.

```python
_SKIP_DIRS = {
    ".git",
    ".claude",          # Claude Code worktrees (separate checkouts, validated independently)
    "__pycache__",
    # ... existing entries
}
```

This prevents the scanner from recursing into `.claude/worktrees/` when run from the main repo.

**Note:** This does not cover centralized worktrees at `Juniper/worktrees/`. Those are outside the repo root and would only be scanned if explicitly passed as an argument.

**Advantages:**

- Simple, minimal change (one line)
- Prevents duplicate scanning and false positives from worktree copies
- `.claude/` directory is infrastructure, not project content

**Disadvantages:**

- Does not address worktree-internal validation (each worktree must run its own check)

#### Approach 3B: Git-Aware File Discovery (Future Enhancement)

**Description:** Replace recursive directory walking with `git ls-files` to discover only tracked files, automatically excluding worktrees, untracked files, and build artifacts.

```python
def _find_markdown_files_git(repo_root: Path, exclude_dirs: set[str]) -> list[Path]:
    """Find markdown files using git's index (respects .gitignore, excludes worktrees)."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "*.md"],
        capture_output=True, text=True, cwd=repo_root
    )
    if result.returncode != 0:
        return []  # Fallback to directory walking

    files = []
    skip = _SKIP_DIRS | (exclude_dirs or set())
    for line in result.stdout.strip().splitlines():
        path = repo_root / line
        rel = Path(line)
        if not any(part in skip for part in rel.parts):
            files.append(path)
    return sorted(files)
```

**Note:** Uses `--cached` only (committed/staged files) rather than `--cached --others` to avoid picking up untracked temporary files. For link checking purposes, only committed content should be validated.

**Advantages:**

- Only scans files that git tracks (definitive source of truth)
- Automatically excludes worktrees, build outputs, and ignored files
- More efficient than recursive directory walking
- Produces consistent results regardless of local filesystem state

**Disadvantages:**

- Requires git to be available (always true in CI, may not be in edge cases)
- Adds `subprocess` dependency
- `.gitignore` must be correctly configured

This is recommended as a future enhancement (Phase 2), not a Phase 1 requirement. Approach 3A is sufficient for immediate stabilization.

---

### Component 4: Missing File Resolution

The 5 missing intra-repo files in Category C were **never committed** to the repository (verified via git history). They were references to planned documents that were never created.

| Referenced File                             | Line | Resolution                                                                                |
|---------------------------------------------|------|-------------------------------------------------------------------------------------------|
| `plan_7.5_7.6_dependency_management.md`     | 491  | **Remove link** -- planned doc, never created                                             |
| `STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md` | 575  | **Remove link** -- planned doc, never created                                             |
| `PYPI_PUBLISH_PROCEDURE.md`                 | 720  | **Replace** with `pypi-publish-procedure.md` (existing file, different naming convention) |
| `PYPI_PUBLISH_PLAN_3_PACKAGES.md`           | 720  | **Remove link** -- planned doc, never created                                             |
| `WORKTREE_IMPLEMENTATION_PLAN.md`           | 755  | **Remove link** or redirect to `WORKTREE_SETUP_PROCEDURE.md`                              |

---

### Component 5: Link Checker Security Hardening

The security review identified several vulnerabilities in the existing link checker that should be addressed alongside the cross-repo enhancement. See [Security Considerations](#security-considerations) for full details.

**Required changes:**

1. **Add universal bounds check** -- All resolved link targets must be constrained to the repo root (or ecosystem root when available). This closes the existing filesystem existence oracle vulnerability.

2. **Add input validation** -- Reject null bytes and absolute paths in link targets before path construction.

3. **Add traversal depth limit** -- Reject links with excessive `../` segments (>5 levels). No legitimate link in this ecosystem requires more than 3-4 levels.

4. **Structural validation in skip mode** -- Even when cross-repo links are skipped, validate that the path after the repo name doesn't traverse back out (e.g., `../juniper-data/../../etc/passwd` should be flagged).

---

## Approaches Considered and Rejected

### Move Cheatsheet to Ecosystem Parent Directory

The `DEVELOPER_CHEATSHEET.md` is fundamentally an ecosystem-wide document. Moving it to `Juniper/notes/DEVELOPER_CHEATSHEET.md` (the ecosystem parent) would make all `../juniper-*` links resolve correctly, eliminating Category A entirely.

**Rejected because:**

- The cheatsheet would no longer be CI-validated by any single repo's pipeline
- The `Juniper/` parent directory is not a git repository; the file would not be version-controlled
- Cross-repo documentation ownership becomes ambiguous
- The file was intentionally placed in juniper-ml as the ecosystem's meta-package

However, if a future `juniper-docs` repository is created for ecosystem-wide documentation, this approach should be reconsidered.

### Check Out Sibling Repos in CI

The CI workflow could check out all 8 Juniper repos to validate cross-repo links:

```yaml
- uses: actions/checkout@v4
  with:
    repository: pcalnon/juniper-data
    path: ../juniper-data
```

**Rejected because** (elevated to a security invariant):

> **Security Invariant:** The CI pipeline for any individual Juniper repo MUST NOT check out, clone, or access the contents of sibling repositories. Cross-repo validation is a local-only operation.

Rationale:

- Widens CI attack surface (compromised sibling repo could affect this pipeline)
- `GITHUB_TOKEN` scope creep if private repos are involved
- Adds complex CI dependencies between repos
- Significantly slows CI execution

### Documentation Site Generator (MkDocs/Sphinx)

A documentation site generator with a monorepo plugin could aggregate docs from all repos and resolve cross-references at build time.

**Rejected because:**

- Significant infrastructure complexity for a research platform
- Over-engineering for the current scale of cross-repo documentation
- Would require a dedicated documentation build pipeline

This remains a viable long-term option if the ecosystem's documentation needs grow.

---

## Ecosystem-Wide Scope

The identical `check_doc_links.py` script exists in at least 6 Juniper repositories:

- juniper-ml
- juniper-data
- juniper-cascor
- juniper-data-client
- juniper-cascor-client
- juniper-cascor-worker

All copies are byte-for-byte identical (except file headers). Any enhancement to the link checker must be propagated to all repos to maintain consistency. Options for managing this:

| Strategy                              | Pros                        | Cons                         |
|---------------------------------------|-----------------------------|------------------------------|
| Manual propagation                    | Simple, no infra changes    | Error-prone, drift risk      |
| Shared script in ecosystem parent     | Single source of truth      | Parent dir is not a git repo |
| Pre-commit hook from shared source    | Centralized, auto-updated   | Complex setup                |
| Pip-installable tool (`juniper-lint`) | Clean dependency, versioned | New package to maintain      |

**Recommendation:** For Phase 1, manually propagate changes to all repos. For Phase 2+, evaluate the `juniper-lint` package approach if the script grows in complexity.

---

## Recommended Implementation Plan

### Phase 1: Immediate CI Stabilization

**Goal:** Unblock the CI pipeline without reducing validation coverage for resolvable links.
**Delivery:** Single PR to juniper-ml, then propagated to other repos.

**Selected approaches:**

- **1A** (Cross-repo link classification) for the link checker
- **3A** (Exclude `.claude`) for worktree scanning
- **Category B** fixes (self-referencing links) in documentation
- **Category C** fixes (missing files) in documentation
- **Category D** fix (semantic correction) in `SECURITY_AUDIT_PLAN.md`
- **Component 5** security hardening (bounds check, input validation)

**Changes:**

1. **`scripts/check_doc_links.py`:**
   - Add `--cross-repo` flag with `skip`/`warn`/`check` modes
   - Add `.claude` to `_SKIP_DIRS`
   - Define `_ECOSYSTEM_REPOS` and `_CROSS_REPO_PATTERN`
   - Add universal bounds check (constrain resolved paths to repo root)
   - Add input validation (null bytes, absolute paths)
   - Add traversal depth limit (reject >5 `../` segments)
   - Add structural validation in skip mode

2. **`.github/workflows/ci.yml`:**
   - Update docs job: `python scripts/check_doc_links.py --exclude templates --exclude history --cross-repo skip`

3. **`notes/DEVELOPER_CHEATSHEET.md`:**
   - Fix 12 Category B links (self-referencing) to use direct relative paths
   - Fix 5 Category C links (remove or redirect missing file references)

4. **`notes/SECURITY_AUDIT_PLAN.md`:**
   - Change `../../../CLAUDE.md` to `../CLAUDE.md` (line 845)

**Verification:** CI passes with zero broken links. Cross-repo links are reported as skipped with a count annotation in CI logs.

### Phase 2: Link Checker Enhancement and Security Hardening

**Goal:** Enable full local validation with ecosystem root discovery. Propagate changes ecosystem-wide.

**Changes:**

1. **`scripts/check_doc_links.py`:**

   - Add `_discover_ecosystem_root()` function (Approach 1B)
   - When `--cross-repo check` is used and ecosystem root is found, resolve cross-repo links against it
   - When not found, fall back to `skip` behavior with a warning

2. **Ecosystem propagation:**

   - Copy updated `check_doc_links.py` to all 6 repos
   - Update CI workflows in each repo to use `--cross-repo skip`

3. **Scheduled full validation:**

   - Add `.github/workflows/docs-full-check.yml` with weekly cron schedule
   - This workflow checks out all sibling repos locally (within the job, not as separate repo checkouts -- uses `git clone` into the workspace) and runs `--cross-repo check`
   - Non-blocking (runs on schedule, not on PRs)
   - This compensates for the `--cross-repo skip` blind spot in PR checks

**Verification:** Running `--cross-repo check` from any local context (standard, worktree) validates all links including cross-repo.

### Phase 3: Documentation Content Cleanup

**Goal:** Improve link durability and reduce future maintenance burden.

**Changes:**

1. Apply Approach 2A (hybrid link strategy) to `DEVELOPER_CHEATSHEET.md`:
   - Keep cross-repo relative links for stable files (AGENTS.md, README.md, docs/)
   - Convert source code file links (~30 links to `.py`, `.yaml`, `.yml` files) to GitHub URLs
   - Ensure all intra-repo links use direct relative paths

2. Add a link conventions note at the top of the cheatsheet:

   ```markdown
   > **Link conventions:** Cross-repo relative links (e.g., `../juniper-data/...`) resolve
   > locally when all Juniper repos are checked out as siblings. They are skipped during CI
   > validation. See [CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md](CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md)
   > for details.
   ```

3. Add guidance to contributor workflow: authors adding new cross-repo links should run `python scripts/check_doc_links.py --cross-repo check` locally before submitting PRs.

---

## Security Considerations

### Existing Vulnerability: Filesystem Existence Oracle

**Severity: Medium:**

The current `_validate_file()` function constructs paths directly from markdown link content without bounds checking:

```python
target_path = (file_dir / file_part).resolve()    # file_part from markdown link
```

A crafted markdown link like `[x](../../../../etc/passwd)` causes `Path.resolve()` to produce `/etc/passwd`, and the checker calls `.exists()` on it. The result is observable:

- In verbose mode: "OK (file)" is printed for existing paths
- In normal mode: broken links are reported for nonexistent paths, silence for existing paths

An attacker who can submit a PR and observe CI output can probe the CI runner's filesystem via existence checks on arbitrary paths.

**Required fix:** Add a universal bounds check:

```python
resolved = target_path.resolve()
boundary = ecosystem_root.resolve() if ecosystem_root else repo_root.resolve()
if not resolved.is_relative_to(boundary):
    errors.append(f"  {rel_source}:{line_num}: link resolves outside repository boundary")
    continue
```

**Note:** `Path.is_relative_to()` (Python 3.9+) is the correct method. Do NOT use `str(resolved).startswith(str(boundary))` -- this is vulnerable to string prefix confusion (e.g., `/home/foo` starts with `/home/fo`). Since the project requires Python >=3.12, `is_relative_to()` is available.

### Path Traversal in Link Resolution

When adding ecosystem root discovery (Approach 1B):

- The checker must never resolve links to files outside the ecosystem directory tree.
- `Path.resolve()` follows symlinks. After resolution, validate that the final path is still within bounds. The `is_relative_to()` check on the resolved (canonicalized) path handles this correctly since `resolve()` follows symlinks before the check.
- Limit directory traversal depth to prevent deep filesystem probing:

  ```python
  if file_part.count("..") > 5:
      errors.append(f"  {rel_source}:{line_num}: excessive directory traversal")
      continue
  ```

### Input Validation

Add validation before path construction:

```python
# Reject null bytes (path truncation attacks on some platforms)
if "\x00" in file_part:
    errors.append(f"  {rel_source}:{line_num}: null byte in link target")
    continue

# Reject absolute paths in links (must always be relative)
if Path(file_part).is_absolute():
    errors.append(f"  {rel_source}:{line_num}: absolute path in documentation link (must be relative)")
    continue
```

### Git Command Injection

If using `subprocess.run(["git", ...])` for worktree detection or file listing:

- **Constraint:** Never interpolate user-controlled strings into git commands. Always use list-form arguments (not `shell=True`).
- **Current implementation:** Uses `Path` objects and list-form arguments. This is safe.

### Ecosystem Repo Name Validation

The `_ECOSYSTEM_REPOS` set defines which directory names are recognized as sibling repos:

- **This set is hardcoded intentionally.** Auto-discovery from the filesystem would allow a malicious directory name (e.g., `juniper-evil`) to be automatically trusted.
- **The set is version-controlled** and changes go through code review.
- **The regex is built with `re.escape()`** on each repo name, preventing regex injection.
- **Update when repos are added/removed** from the ecosystem.

### CI Supply Chain Security Invariant

> **Security Invariant:** The CI pipeline for any individual Juniper repo MUST NOT check out, clone, or access the contents of sibling repositories during PR validation. Cross-repo validation is a local-only operation.

Rationale:

- Checking out sibling repos widens CI attack surface
- A compromised sibling repo could affect this pipeline's CI runner
- `GITHUB_TOKEN` scope creep if private repos are involved
- Fork-based PRs could craft workflows that leak credentials

The scheduled full-validation workflow (Phase 2) is an exception: it runs on `schedule` (not on PRs), does not use fork code, and uses explicit repo URLs.

### Cross-Repo Skip Mode: Structural Validation

Even in `skip` mode, the checker should validate structural correctness of cross-repo links:

```python
def _validate_cross_repo_structure(file_part: str) -> str | None:
    """Validate that a cross-repo link doesn't traverse back out of its target repo."""
    parts = Path(file_part).parts
    # Find the repo name part, then check remaining path doesn't escape
    for i, part in enumerate(parts):
        if part in _ECOSYSTEM_REPOS:
            remainder = Path(*parts[i + 1:]) if i + 1 < len(parts) else Path(".")
            if ".." in remainder.parts:
                return f"cross-repo link escapes target repository: {file_part}"
            break
    return None
```

This prevents patterns like `../juniper-data/../../etc/passwd` from being silently skipped.

### Information Disclosure

- Cross-repo relative links reveal internal file structure to anyone viewing the markdown on GitHub. For this project (MIT-licensed, public repos), this is acceptable.
- **If any Juniper repo transitions to private:** audit all cross-repo links in public repos referencing the private repo. The link paths themselves reveal internal directory structure of the private codebase.

---

## Maintenance Guidelines

### When Adding Cross-Repo Links

1. Use relative paths for stable files (AGENTS.md, README.md, docs/)
2. Use GitHub URLs for source code files (subject to refactoring)
3. Never use deep relative paths (`../../../` or more) -- they are context-fragile
4. Self-referencing links (`../juniper-ml/...`) must use direct relative paths instead
5. Run `python scripts/check_doc_links.py --cross-repo check` locally before submitting PRs

### When Adding a New Ecosystem Repository

1. Add the repo name to `_ECOSYSTEM_REPOS` in `check_doc_links.py` across all repos
2. Update this proposal's Category A table

### When Archiving or Removing an Ecosystem Repository

1. Remove the repo name from `_ECOSYSTEM_REPOS` across all repos
2. Update or remove all cross-repo links referencing the archived repo
3. Run full validation to catch any remaining references

### When Renaming or Moving Files

1. Search for all cross-repo references to the moved file: `grep -rn "old-filename" notes/`
2. Update all references in the cheatsheet and other documentation
3. Run `python scripts/check_doc_links.py --cross-repo check` locally to verify

### Periodic Validation

**Automated (recommended):** The scheduled CI workflow (Phase 2) runs weekly full validation. Monitor its results.

**Manual:** Run full local validation before major releases:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
python scripts/check_doc_links.py --cross-repo check
```

This catches cross-repo link rot that the PR-level `--cross-repo skip` mode would miss.

### Pre-Commit Hook Considerations

The link checker is not currently configured as a pre-commit hook. If added in the future:

- Pre-commit hooks run locally (`.claude/worktrees/` would be present on disk)
- The `pre-commit` framework operates on staged files, limiting the scanning scope
- Ensure the hook uses `--cross-repo skip` or `--cross-repo warn` to avoid blocking commits due to unresolvable cross-repo links
- Add `.claude` to `_SKIP_DIRS` (Phase 1) to prevent worktree scanning

---

## Appendix A: Full Broken Link Inventory

### Category A: Cross-Repo Relative Links (107 instances)

All in `notes/DEVELOPER_CHEATSHEET.md`. Unique cross-repo targets by prefix:

**`../juniper-deploy/` (30 instances):**

| Target                                                                      | Occurrences |
|-----------------------------------------------------------------------------|-------------|
| `../juniper-deploy/.env.example`                                            | 10          |
| `../juniper-deploy/AGENTS.md`                                               | 6           |
| `../juniper-deploy/docs/OBSERVABILITY_GUIDE.md`                             | 6           |
| `../juniper-deploy/docker-compose.yml`                                      | 2           |
| `../juniper-deploy/.env.demo`                                               | 1           |
| `../juniper-deploy/.env.observability`                                      | 1           |
| `../juniper-deploy/Makefile`                                                | 1           |
| `../juniper-deploy/grafana/provisioning/dashboards/`                        | 1           |
| `../juniper-deploy/grafana/provisioning/dashboards/dashboard-providers.yml` | 1           |
| `../juniper-deploy/notes/DOCKER_PYTHON_314_MIGRATION_PLAN.md`               | 1           |

**`../juniper-data/` (29 instances):**

| Target                                                | Occurrences |
|-------------------------------------------------------|-------------|
| `../juniper-data/AGENTS.md`                           | 7           |
| `../juniper-data/juniper_data/api/settings.py`        | 5           |
| `../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md` | 5           |
| `../juniper-data/juniper_data/api/app.py`             | 2           |
| `../juniper-data/juniper_data/api/observability.py`   | 3           |
| `../juniper-data/juniper_data/api/security.py`        | 2           |
| `../juniper-data/docs/api/API_SCHEMAS.md`             | 2           |
| `../juniper-data/docs/api/JUNIPER_DATA_API.md`        | 1           |
| `../juniper-data/notes/WORKTREE_SETUP_PROCEDURE.md`   | 1           |
| `../juniper-data/notes/WORKTREE_CLEANUP_PROCEDURE.md` | 1           |

**`../juniper-cascor/` (17 instances):**

| Target                                               | Occurrences |
|------------------------------------------------------|-------------|
| `../juniper-cascor/AGENTS.md`                        | 5           |
| `../juniper-cascor/docs/api/api-schemas.md`          | 2           |
| `../juniper-cascor/conf/logging_config.yaml`         | 1           |
| `../juniper-cascor/docs/api/api-reference.md`        | 1           |
| `../juniper-cascor/docs/ci/manual.md`                | 1           |
| `../juniper-cascor/docs/ci/quick-start.md`           | 1           |
| `../juniper-cascor/docs/ci/reference.md`             | 1           |
| `../juniper-cascor/docs/overview/constants-guide.md` | 1           |
| `../juniper-cascor/docs/testing/quick-start.md`      | 1           |
| `../juniper-cascor/docs/testing/reference.md`        | 2           |
| `../juniper-cascor/notes/API_REFERENCE.md`           | 1           |

**`../juniper-canopy/` (14 instances):**

| Target                                                       | Occurrences |
|--------------------------------------------------------------|-------------|
| `../juniper-canopy/AGENTS.md`                                | 2           |
| `../juniper-canopy/conf/app_config.yaml`                     | 1           |
| `../juniper-canopy/conf/logging_config.yaml`                 | 1           |
| `../juniper-canopy/docs/api/API_SCHEMAS.md`                  | 1           |
| `../juniper-canopy/docs/cascor/CASCOR_BACKEND_MANUAL.md`     | 1           |
| `../juniper-canopy/docs/cascor/CONSTANTS_GUIDE.md`           | 1           |
| `../juniper-canopy/docs/ci_cd/CICD_MANUAL.md`                | 1           |
| `../juniper-canopy/docs/ci_cd/CICD_QUICK_START.md`           | 1           |
| `../juniper-canopy/docs/ci_cd/CICD_REFERENCE.md`             | 1           |
| `../juniper-canopy/docs/testing/SELECTIVE_TEST_GUIDE.md`     | 1           |
| `../juniper-canopy/docs/testing/TESTING_QUICK_START.md`      | 1           |
| `../juniper-canopy/docs/testing/TESTING_REFERENCE.md`        | 1           |
| `../juniper-canopy/docs/testing/TESTING_REPORTS_COVERAGE.md` | 1           |

**`../juniper-cascor-client/` (10 instances):**

| Target                                                        | Occurrences |
|---------------------------------------------------------------|-------------|
| `../juniper-cascor-client/AGENTS.md`                          | 4           |
| `../juniper-cascor-client/juniper_cascor_client/ws_client.py` | 3           |
| `../juniper-cascor-client/juniper_cascor_client/client.py`    | 3           |

**`../juniper-data-client/` (7 instances):**

| Target                                                 | Occurrences |
|--------------------------------------------------------|-------------|
| `../juniper-data-client/AGENTS.md`                     | 3           |
| `../juniper-data-client/juniper_data_client/client.py` | 4           |

### Category B: Self-Referencing Cross-Repo Links (12 instances)

All in `notes/DEVELOPER_CHEATSHEET.md`:

| Line | Link                                                 |
|------|------------------------------------------------------|
| 95   | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 106  | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 106  | `../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md`    |
| 112  | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 123  | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 163  | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 163  | `../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md`    |
| 163  | `../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md`       |
| 174  | `../juniper-ml/notes/SOPS_USAGE_GUIDE.md`            |
| 174  | `../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md` |
| 500  | `../juniper-ml/AGENTS.md`                            |
| 720  | `../juniper-ml/notes/pypi-publish-procedure.md`      |

### Category C: Missing Intra-Repo Files (5 instances)

All in `notes/DEVELOPER_CHEATSHEET.md`:

| Line | Referenced File                             | Resolution                                          |
|------|---------------------------------------------|-----------------------------------------------------|
| 491  | `plan_7.5_7.6_dependency_management.md`     | Remove                                              |
| 575  | `STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md` | Remove                                              |
| 720  | `PYPI_PUBLISH_PROCEDURE.md`                 | Replace with `pypi-publish-procedure.md`            |
| 720  | `PYPI_PUBLISH_PLAN_3_PACKAGES.md`           | Remove                                              |
| 755  | `WORKTREE_IMPLEMENTATION_PLAN.md`           | Remove or redirect to `WORKTREE_SETUP_PROCEDURE.md` |

### Category D: False-Negative Deep Relative Link (0 CI failures, 1 semantic issue)

In `notes/SECURITY_AUDIT_PLAN.md`, line 845: `../../../CLAUDE.md#worktree-procedures-mandatory--task-isolation`

Not reported as broken by CI (passes via repo-root-relative fallback). Semantically incorrect -- resolves to the wrong document. Fix: change to `../CLAUDE.md#worktree-procedures-mandatory--task-isolation`.

---

## Appendix B: Ecosystem Directory Layout Reference

### Standard Local Development Layout

```bash
Juniper/                            <-- ecosystem root
  juniper-ml/                       <-- this repo (standard checkout)
    notes/DEVELOPER_CHEATSHEET.md   <-- ../ = juniper-ml/, ../../ = Juniper/
  juniper-data/                     <-- sibling repo
  juniper-cascor/                   <-- sibling repo
  juniper-deploy/                   <-- sibling repo
  (... other repos ...)
  worktrees/                        <-- centralized worktree directory
```

### Claude Code Worktree Layout

```bash
Juniper/
  juniper-ml/
    .claude/worktrees/
      purring-bubbling-dragonfly/    <-- worktree checkout
        notes/DEVELOPER_CHEATSHEET.md  <-- ../ = worktree root, not Juniper/
```

### Centralized Worktree Layout

```bash
Juniper/
  worktrees/
    juniper-ml--feature--xyz--20260307-1200--abc12345/  <-- worktree checkout
      notes/DEVELOPER_CHEATSHEET.md    <-- ../ = worktree root, not Juniper/
```

### GitHub Actions CI Layout

```bash
/home/runner/work/juniper-ml/juniper-ml/   <-- single repo checkout
  notes/DEVELOPER_CHEATSHEET.md            <-- ../ = repo root (no siblings exist)
```

---
