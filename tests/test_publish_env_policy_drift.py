"""Drift gate: every publish environment must stay ref-gated to release tags.

Companion to ``notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md``
(§6 Option A, §12 implementation record, §12.5 "no drift gate" gap).

On 2026-08-17 every ``pypi`` / ``testpypi`` environment across the 8 publishing
repos was given a **tag-only** deployment ref policy, so a ``workflow_dispatch``
from a branch is refused at the environment gate before any OIDC credential is
minted.  That control lives in **GitHub settings, not in the repository**: no
test covers it, no reviewer sees a diff when one is deleted, and the failure is
silent -- the publish path simply becomes permissive again.  This gate is the
only thing standing between that and a regression.

Two invariants matter more than the rest:

1. **No branch-type policy may exist.**  Adding a ``main`` branch policy is the
   single edit that re-opens the arbitrary-ref hole while leaving every tag
   pattern intact and the environment still looking configured.  Owner decision
   D3 was explicitly tag-only.
2. **The ``pypi`` reviewer gate must survive.**  ``PUT``ing an environment is a
   create-or-update, so a careless payload can clear ``required_reviewers``
   while successfully setting a ref policy -- the environment then looks *more*
   configured while actually being weaker.

**The ``dockerhub`` environment (added 2026-09-23)** is the same control on a different path.
Wave 4 of the container-registry rollout will push release images to Docker Hub, and the owner
ruled (2026-09-22, Option B of
``notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`` §3) that
its credential lives in a ``dockerhub`` environment, readable only by a job that names it, and only
on a release tag. Each environment differs from ``pypi`` in both sets, so each carries its own:

* **Its own repo set**: the five image repos of that procedure's §5.1, not the registry's eight.
  Three registry repos ship no image, and an environment there would be a foothold with no purpose.
* **Its own tag set**: ``v*`` and ``juniper-*-v*`` only. ``pypi`` also admits ``rc*`` / ``hf*``.
* **No reviewer is required**, by the same ruling: the Release is already the owner's act, so a
  second manual gate would only delay every image publish. The gate does not assert the absence of
  one either, because adding a reviewer tightens the path rather than loosening it.
* **The credential must never sit at repository scope**, where every workflow on every ref can read
  it. That is the exposure Option B was chosen to avoid, and a ``gh secret set`` that dropped its
  ``--env dockerhub`` creates it silently. The repository-scope check reads NAMES only: ``gh``
  applies a ``--jq`` name filter, so a variable's value never reaches this process.

Its repair is NOT the ``pypi`` helper named below, which adds all six patterns. Re-run §5.2B steps 1-2
of the procedure named above.

In per-PR CI the ``dockerhub`` half verifies nothing: the token reaches juniper-ml only, and
juniper-ml ships no image, so every one of the five is named as unverified and the class skips.
It is a LOCAL gate. Run it with ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``.

Modes (mirroring ``tests/test_ci_tools_drift.py`` and
``tests/test_docs_full_check_ecosystem.py``):

* **Structural checks always run** -- the registry resolves a publishing-repo
  set, the expected pattern set is coherent, and the detector provably bites on
  synthetic violations (the negative control).  These need no network.
* **Live API assertions are gated** behind ``GITHUB_ACTIONS=true`` or
  ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``, and additionally require ``gh`` on PATH
  with working auth.  A missing / unauthenticated ``gh`` skips loudly rather
  than failing, so the suite stays runnable offline.

Read-only: the live half issues ``gh api`` GETs only and never mutates an
environment.  Repair is
``util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

import yaml

OWNER = "pcalnon"
REGISTRY_REL = Path("util") / "release_train" / "registry.yaml"

# The two environments every publishing repo exposes to the PyPA publish action.
PUBLISH_ENVS = ("pypi", "testpypi")

# Repos that must NOT carry a publish environment at all.  juniper-deploy's
# vestigial pair was deleted 2026-08-17 (owner decision D4); an environment
# named `pypi` on a repo that ships no package is a latent foothold, so this
# doubles as an anti-resurrection guard.
NON_PUBLISHING_REPOS = ("juniper-deploy",)

# Owner decision D2.  `v*` / `juniper-*-v*` are the live conventions; the `rc` /
# `hf` pairs were registered ahead of any release-candidate or hotfix use.
EXPECTED_TAG_PATTERNS = frozenset(
    {
        "v*",
        "juniper-*-v*",
        "rc*",
        "juniper-*-rc*",
        "hf*",
        "juniper-*-hf*",
    }
)

# Environments whose human approval gate must also survive.  testpypi is
# deliberately reviewer-free -- gating it would break hands-free release-train
# operation, which is exactly what the ref policy exists to avoid needing.
ENVS_REQUIRING_REVIEWERS = ("pypi",)

# The Docker Hub credential environment (Option B, owner ruling 2026-09-22).  Its
# repo set is the five image repos of the registration procedure's §5.1 -- NOT the
# registry: juniper-ml, juniper-cascor-client and juniper-data-client ship no image.
# juniper-deploy publishes a test-runner image, and whether that goes to Docker Hub
# is an open owner question (the procedure's §10), so it is deliberately absent
# here; adding it is a decision, and this list is where it gets recorded.
DOCKERHUB_ENV = "dockerhub"
DOCKERHUB_REPOS = ("juniper-cascor", "juniper-cascor-worker", "juniper-canopy", "juniper-data", "juniper-recurrence")

# Only the two live release conventions: the ruling mirrored pypi's LIVE shapes,
# not its reserved rc* / hf* pairs, and §5.2B step 2 added exactly these two.
DOCKERHUB_TAG_PATTERNS = frozenset({"v*", "juniper-*-v*"})

# Any secret or variable name with this prefix belongs in the dockerhub
# environment and nowhere else.
DOCKERHUB_CREDENTIAL_PREFIX = "DOCKERHUB_"

EXPECTED_TAGS_BY_ENV = {
    "pypi": EXPECTED_TAG_PATTERNS,
    "testpypi": EXPECTED_TAG_PATTERNS,
    DOCKERHUB_ENV: DOCKERHUB_TAG_PATTERNS,
}

# The pypi helper applies all six patterns, which would put rc* / hf* on dockerhub.
REPAIR_HINT_BY_ENV = {
    "pypi": "util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> pypi",
    "testpypi": "util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> testpypi",
    DOCKERHUB_ENV: "notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md §5.2B steps 1-2 (two tag rules; NOT the pypi helper, which adds six)",
}


def _repo_root() -> Path:
    """Locate the juniper-ml checkout root from this file."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / REGISTRY_REL).is_file():
            return candidate
    return here.parents[1]


def _registry_repos() -> frozenset[str]:
    """Unique publishing repos from the release-train registry (S4.1 source of truth)."""
    registry_path = _repo_root() / REGISTRY_REL
    if not registry_path.is_file():
        raise unittest.SkipTest(f"{REGISTRY_REL} not found")
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    packages = data.get("packages") or []
    return frozenset(str(pkg["repo"]) for pkg in packages if isinstance(pkg, dict) and pkg.get("repo"))


def check_environment(env_payload: dict, policies: list, *, env_name: str) -> list:
    """Return a list of human-readable violations for one environment.

    Pure: takes already-fetched API payloads so the negative control can drive
    it with synthetic data and no network.  An empty list means compliant.
    """
    violations: list = []

    policy_cfg = env_payload.get("deployment_branch_policy")
    if policy_cfg is None:
        # Everything below reads fields of that object; without it there is
        # nothing further to say and this single finding is the actionable one.
        return ["deployment_branch_policy is null -- environment accepts ANY ref"]

    if policy_cfg.get("protected_branches"):
        violations.append("protected_branches is true -- protected branches may deploy; expected custom policies only")
    if not policy_cfg.get("custom_branch_policies"):
        violations.append("custom_branch_policies is not true -- no custom ref policy is in force")

    # Invariant 1: a branch policy of any kind re-opens the arbitrary-ref path.
    branch_policies = [p for p in policies if (p.get("type") or "branch") != "tag"]
    if branch_policies:
        names = ", ".join(sorted(str(p.get("name")) for p in branch_policies))
        violations.append(f"branch-type deployment policy present ({names}) -- D3 requires tag-only; this re-opens branch dispatch")

    expected = EXPECTED_TAGS_BY_ENV[env_name]
    found_tags = {str(p.get("name")) for p in policies if (p.get("type") or "branch") == "tag"}
    missing = expected - found_tags
    if missing:
        violations.append(f"missing tag pattern(s): {', '.join(sorted(missing))}")
    unexpected = found_tags - expected
    if unexpected:
        constant = "DOCKERHUB_TAG_PATTERNS" if env_name == DOCKERHUB_ENV else "EXPECTED_TAG_PATTERNS"
        violations.append(f"unexpected tag pattern(s): {', '.join(sorted(unexpected))} -- widen {constant} deliberately or remove them")

    # Invariant 2: the reviewer gate must not have been cleared by a PUT.
    if env_name in ENVS_REQUIRING_REVIEWERS:
        rule_types = {str(r.get("type")) for r in env_payload.get("protection_rules") or []}
        if "required_reviewers" not in rule_types:
            violations.append("required_reviewers protection rule is absent -- the human approval gate was cleared")

    return violations


def _gh_json(path: str):
    """GET a gh API path and parse JSON. Raises RuntimeError on failure."""
    proc = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def check_repo_scope_credentials(secret_names, variable_names) -> list:
    """Return a violation per ``DOCKERHUB_*`` name found at REPOSITORY scope.

    Pure, like ``check_environment``: it takes names, never values.  Option B put the
    credential in the ``dockerhub`` environment so that only a release-tag job naming it
    can read it; a copy at repository scope is readable by every workflow on every ref.
    """
    violations: list = []
    for kind, names in (("secret", secret_names), ("variable", variable_names)):
        for name in sorted(str(n) for n in names or []):
            if name.upper().startswith(DOCKERHUB_CREDENTIAL_PREFIX):
                violations.append(f"repository-scope {kind} {name} -- readable by every workflow on every ref; it belongs only in the {DOCKERHUB_ENV} environment (Option B)")
    return violations


def _gh_names(path: str, collection: str) -> list:
    """List the ``name`` of each item in ``collection`` at ``path``, and nothing else.

    The ``--jq`` filter runs inside ``gh``, so a variables endpoint's VALUES never reach
    this process, let alone a log.  If a token were ever pasted into a variable, this
    probe must not be what prints it.  Raises RuntimeError on failure.
    """
    proc = subprocess.run(
        ["gh", "api", path, "--jq", f"[.{collection}[].name]"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout or "[]")


class RegistryResolutionTest(unittest.TestCase):
    """Always-on: the publishing-repo set resolves from the registry."""

    def test_registry_resolves_publishing_repos(self) -> None:
        repos = _registry_repos()
        self.assertGreaterEqual(len(repos), 2, "registry.yaml did not resolve a non-trivial publishing-repo set")
        self.assertIn("juniper-ml", repos)

    def test_non_publishing_repos_are_not_registry_publishers(self) -> None:
        repos = _registry_repos()
        for repo in NON_PUBLISHING_REPOS:
            self.assertNotIn(repo, repos, f"{repo} is a registry publisher; it must not be listed in NON_PUBLISHING_REPOS")


class ExpectedPatternContractTest(unittest.TestCase):
    """Always-on: the expected pattern set is coherent and covers the conventions."""

    def test_pattern_set_is_non_trivial(self) -> None:
        self.assertGreaterEqual(len(EXPECTED_TAG_PATTERNS), 2)

    def test_live_release_conventions_are_covered(self) -> None:
        """The two shapes real releases actually use must be present."""
        self.assertIn("v*", EXPECTED_TAG_PATTERNS, "meta / app releases tag as v<semver>")
        self.assertIn("juniper-*-v*", EXPECTED_TAG_PATTERNS, "sub-package releases tag as juniper-<pkg>-v<semver>")

    def test_no_branch_shaped_pattern_smuggled_in(self) -> None:
        """A bare branch name in the tag set would be a category error."""
        for pattern in EXPECTED_TAG_PATTERNS:
            self.assertNotIn(pattern, {"main", "develop"}, "branch names must never appear as deployment tag patterns")

    def test_no_catch_all_pattern(self) -> None:
        """A bare `*` would admit every tag and silently defeat the gate."""
        self.assertNotIn("*", EXPECTED_TAG_PATTERNS)
        self.assertNotIn("*", DOCKERHUB_TAG_PATTERNS)

    def test_every_env_has_a_tag_set_and_a_repair_hint(self) -> None:
        for env_name in (*PUBLISH_ENVS, DOCKERHUB_ENV):
            self.assertIn(env_name, EXPECTED_TAGS_BY_ENV)
            self.assertIn(env_name, REPAIR_HINT_BY_ENV)


class DockerhubContractTest(unittest.TestCase):
    """Always-on: the dockerhub environment's own repo set and tag set are coherent."""

    def test_dockerhub_tags_are_exactly_the_two_live_release_shapes(self) -> None:
        self.assertEqual(DOCKERHUB_TAG_PATTERNS, frozenset({"v*", "juniper-*-v*"}))

    def test_dockerhub_is_never_wider_than_pypi(self) -> None:
        """A tag that may not publish a wheel must not publish an image either."""
        self.assertLessEqual(DOCKERHUB_TAG_PATTERNS, EXPECTED_TAG_PATTERNS)

    def test_dockerhub_repos_are_the_five_image_repos(self) -> None:
        self.assertEqual(len(DOCKERHUB_REPOS), 5)
        self.assertEqual(len(set(DOCKERHUB_REPOS)), 5, "duplicate repo in DOCKERHUB_REPOS")
        self.assertLessEqual(set(DOCKERHUB_REPOS), _registry_repos(), "every image repo also publishes a registry package")
        for repo in ("juniper-ml", "juniper-cascor-client", "juniper-data-client"):
            self.assertNotIn(repo, DOCKERHUB_REPOS, f"{repo} ships no container image")

    def test_juniper_deploy_is_absent_until_the_owner_decides(self) -> None:
        """juniper-deploy-test on Docker Hub is an open owner question (the procedure's §10)."""
        self.assertNotIn("juniper-deploy", DOCKERHUB_REPOS)


class DetectorNegativeControlTest(unittest.TestCase):
    """Always-on: prove the detector bites. A gate that cannot fail is not a gate."""

    COMPLIANT_ENV = {
        "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
        "protection_rules": [{"type": "required_reviewers"}, {"type": "wait_timer"}, {"type": "branch_policy"}],
    }
    COMPLIANT_POLICIES = [{"name": p, "type": "tag"} for p in sorted(EXPECTED_TAG_PATTERNS)]

    def test_compliant_environment_passes(self) -> None:
        self.assertEqual(check_environment(self.COMPLIANT_ENV, self.COMPLIANT_POLICIES, env_name="pypi"), [])

    def test_null_policy_is_flagged(self) -> None:
        violations = check_environment({"deployment_branch_policy": None, "protection_rules": []}, [], env_name="testpypi")
        self.assertTrue(any("ANY ref" in v for v in violations), violations)

    def test_branch_policy_is_flagged(self) -> None:
        """The critical case: every tag pattern present, but `main` added alongside."""
        policies = [*self.COMPLIANT_POLICIES, {"name": "main", "type": "branch"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("branch-type deployment policy present" in v for v in violations), violations)

    def test_untyped_policy_counts_as_branch(self) -> None:
        """The API omits `type` for legacy branch policies; absence must not read as `tag`."""
        policies = [*self.COMPLIANT_POLICIES, {"name": "main"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("branch-type deployment policy present" in v for v in violations), violations)

    def test_missing_tag_pattern_is_flagged(self) -> None:
        policies = [p for p in self.COMPLIANT_POLICIES if p["name"] != "v*"]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("missing tag pattern" in v and "v*" in v for v in violations), violations)

    def test_unexpected_tag_pattern_is_flagged(self) -> None:
        policies = [*self.COMPLIANT_POLICIES, {"name": "*", "type": "tag"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("unexpected tag pattern" in v for v in violations), violations)

    def test_cleared_reviewer_gate_is_flagged_on_pypi(self) -> None:
        env = {**self.COMPLIANT_ENV, "protection_rules": [{"type": "branch_policy"}]}
        violations = check_environment(env, self.COMPLIANT_POLICIES, env_name="pypi")
        self.assertTrue(any("required_reviewers" in v for v in violations), violations)

    def test_testpypi_does_not_require_reviewers(self) -> None:
        """testpypi is deliberately reviewer-free so the release train stays hands-free."""
        env = {**self.COMPLIANT_ENV, "protection_rules": [{"type": "branch_policy"}]}
        self.assertEqual(check_environment(env, self.COMPLIANT_POLICIES, env_name="testpypi"), [])

    def test_protected_branches_mode_is_flagged(self) -> None:
        env = {**self.COMPLIANT_ENV, "deployment_branch_policy": {"protected_branches": True, "custom_branch_policies": False}}
        violations = check_environment(env, [], env_name="testpypi")
        self.assertTrue(any("protected_branches" in v for v in violations), violations)

    # ---- dockerhub: its own tag set, and no reviewer required ------------------------------

    # The ruled shape (§5.2B steps 1-2 of the registration procedure): custom policy, the
    # two tag rules, and branch_policy as the ONLY protection rule.
    DOCKERHUB_ENV_PAYLOAD = {
        "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
        "protection_rules": [{"type": "branch_policy"}],
    }
    DOCKERHUB_POLICIES = [{"name": p, "type": "tag"} for p in sorted(DOCKERHUB_TAG_PATTERNS)]

    def test_ruled_dockerhub_environment_passes(self) -> None:
        self.assertEqual(check_environment(self.DOCKERHUB_ENV_PAYLOAD, self.DOCKERHUB_POLICIES, env_name=DOCKERHUB_ENV), [])

    def test_pypi_pattern_set_on_dockerhub_is_flagged(self) -> None:
        """What the pypi repair helper would leave behind: rc* / hf* do not belong on dockerhub."""
        violations = check_environment(self.DOCKERHUB_ENV_PAYLOAD, self.COMPLIANT_POLICIES, env_name=DOCKERHUB_ENV)
        self.assertTrue(any("unexpected tag pattern" in v and "rc*" in v and "DOCKERHUB_TAG_PATTERNS" in v for v in violations), violations)

    def test_dockerhub_pattern_set_is_not_enough_for_pypi(self) -> None:
        """The converse, proving the sets are per-environment rather than one shared set."""
        violations = check_environment(self.COMPLIANT_ENV, self.DOCKERHUB_POLICIES, env_name="pypi")
        self.assertTrue(any("missing tag pattern" in v and "rc*" in v for v in violations), violations)

    def test_dockerhub_missing_a_live_pattern_is_flagged(self) -> None:
        policies = [p for p in self.DOCKERHUB_POLICIES if p["name"] != "juniper-*-v*"]
        violations = check_environment(self.DOCKERHUB_ENV_PAYLOAD, policies, env_name=DOCKERHUB_ENV)
        self.assertTrue(any("missing tag pattern" in v and "juniper-*-v*" in v for v in violations), violations)

    def test_branch_policy_on_dockerhub_is_flagged(self) -> None:
        """The same critical case as pypi: both tags intact, `main` added, and every branch run can read the token."""
        policies = [*self.DOCKERHUB_POLICIES, {"name": "main", "type": "branch"}]
        violations = check_environment(self.DOCKERHUB_ENV_PAYLOAD, policies, env_name=DOCKERHUB_ENV)
        self.assertTrue(any("branch-type deployment policy present" in v for v in violations), violations)

    def test_null_policy_on_dockerhub_is_flagged(self) -> None:
        violations = check_environment({"deployment_branch_policy": None, "protection_rules": []}, [], env_name=DOCKERHUB_ENV)
        self.assertTrue(any("ANY ref" in v for v in violations), violations)

    def test_repo_scope_credential_is_flagged(self) -> None:
        """A `gh secret set` / `gh variable set` that dropped its `--env dockerhub`."""
        violations = check_repo_scope_credentials(["CROSS_REPO_DISPATCH_TOKEN", "DOCKERHUB_TOKEN"], ["dockerhub_username"])
        self.assertEqual(len(violations), 2, violations)
        self.assertTrue(any("secret DOCKERHUB_TOKEN" in v for v in violations), violations)
        self.assertTrue(any("variable dockerhub_username" in v for v in violations), violations)

    def test_repo_scope_without_credential_passes(self) -> None:
        """The live state of every image repo at 2026-09-23: other secrets, no DOCKERHUB_* name."""
        self.assertEqual(check_repo_scope_credentials(["CROSS_REPO_DISPATCH_TOKEN", "SOPS_AGE_KEY"], []), [])


class LivePublishEnvironmentPolicyTest(unittest.TestCase):
    """Gated: assert the real environments still carry the tag-only policy."""

    # Registry repos partitioned by what the ambient token can actually read.
    readable: list = []
    unreadable: list = []

    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            raise unittest.SkipTest("skipping live environment lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override)")
        if shutil.which("gh") is None:
            raise unittest.SkipTest("gh not on PATH")

        # Partition the registry repos by what this token can actually read.
        #
        # In juniper-ml's own CI the built-in GITHUB_TOKEN is scoped to
        # juniper-ml alone, so every sibling probe fails on PERMISSION, not on
        # drift.  Treating that as a violation would make ci.yml permanently
        # red; treating it as success would silently shrink coverage to one
        # repo while the test name still claims "every publish environment".
        # So: verify what is readable, NAME what is not, and refuse to pass at
        # all if nothing was readable.
        cls.readable = []
        cls.unreadable = []
        for repo in sorted(_registry_repos()):
            try:
                _gh_json(f"repos/{OWNER}/{repo}/environments")
            except Exception:
                cls.unreadable.append(repo)
            else:
                cls.readable.append(repo)

        if not cls.readable:
            raise unittest.SkipTest(f"gh api could not read environments for ANY registry repo (unauthenticated, or token lacks access): {', '.join(cls.unreadable)}")

    def test_every_publish_environment_is_tag_gated(self) -> None:
        failures: list = []
        for repo in self.readable:
            for env_name in PUBLISH_ENVS:
                try:
                    env_payload = _gh_json(f"repos/{OWNER}/{repo}/environments/{env_name}")
                    policy_doc = _gh_json(f"repos/{OWNER}/{repo}/environments/{env_name}/deployment-branch-policies")
                except RuntimeError as exc:
                    # The repo IS readable, so a failure here is a real finding
                    # -- most likely the environment was deleted outright.
                    failures.append(f"{repo}/{env_name}: could not read environment ({exc})")
                    continue
                policies = (policy_doc or {}).get("branch_policies") or []
                for violation in check_environment(env_payload, policies, env_name=env_name):
                    failures.append(f"{repo}/{env_name}: {violation}")

        # Never let bounded coverage read as full coverage (no silent caps).
        if self.unreadable:
            print(f"\n[publish-env drift] verified {len(self.readable)} repo(s): {', '.join(self.readable)}")
            print(f"[publish-env drift] NOT verified (token lacks access): {', '.join(self.unreadable)}")

        self.assertEqual(
            failures,
            [],
            "publish environment ref-policy drift detected:\n  " + "\n  ".join(failures) + "\nRepair: " + " / ".join(REPAIR_HINT_BY_ENV[env] for env in PUBLISH_ENVS),
        )

    def test_non_publishing_repos_have_no_publish_environment(self) -> None:
        """Anti-resurrection: juniper-deploy's vestigial pypi/testpypi stay deleted."""
        failures: list = []
        for repo in NON_PUBLISHING_REPOS:
            try:
                doc = _gh_json(f"repos/{OWNER}/{repo}/environments")
            except RuntimeError as exc:
                raise unittest.SkipTest(f"could not enumerate {repo} environments: {exc}")
            names = {str(e.get("name")) for e in (doc or {}).get("environments") or []}
            for env_name in PUBLISH_ENVS:
                if env_name in names:
                    failures.append(f"{repo}: environment '{env_name}' exists but {repo} publishes no package (owner decision D4 deleted it)")
        self.assertEqual(failures, [], "\n  ".join(failures))


class LiveDockerhubEnvironmentPolicyTest(unittest.TestCase):
    """Gated: the five ``dockerhub`` environments stay tag-gated, and the credential stays out of repository scope.

    Read-only: ``gh api`` GETs only.  The repository-scope listings go through ``_gh_names``, so
    no variable VALUE is ever read into this process.
    """

    readable: list = []
    unreadable: list = []

    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            raise unittest.SkipTest("skipping live dockerhub environment lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override)")
        if shutil.which("gh") is None:
            raise unittest.SkipTest("gh not on PATH")

        # Same partition as the pypi class, over the IMAGE repos.  None of them is juniper-ml,
        # so per-PR CI reads none and this class skips there -- by name, not silently.
        cls.readable = []
        cls.unreadable = []
        for repo in DOCKERHUB_REPOS:
            try:
                _gh_json(f"repos/{OWNER}/{repo}/environments")
            except Exception:
                cls.unreadable.append(repo)
            else:
                cls.readable.append(repo)

        if not cls.readable:
            raise unittest.SkipTest(f"gh api could not read environments for ANY image repo (per-PR CI reaches juniper-ml only; run locally with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1): {', '.join(cls.unreadable)}")

    def _report_coverage(self, label: str, verified: list, unverified: list) -> None:
        # Never let bounded coverage read as full coverage (no silent caps).
        if unverified:
            print(f"\n[dockerhub drift] {label}: verified {len(verified)} repo(s): {', '.join(verified) or '-'}")
            print(f"[dockerhub drift] {label}: NOT verified (token lacks access): {', '.join(unverified)}")

    def test_every_dockerhub_environment_is_tag_gated(self) -> None:
        failures: list = []
        for repo in self.readable:
            try:
                env_payload = _gh_json(f"repos/{OWNER}/{repo}/environments/{DOCKERHUB_ENV}")
                policy_doc = _gh_json(f"repos/{OWNER}/{repo}/environments/{DOCKERHUB_ENV}/deployment-branch-policies")
            except RuntimeError as exc:
                # The repo IS readable, so the environment itself is missing.  That is worse than it
                # looks: a workflow run that names a missing environment makes GitHub create it with
                # no protection rules at all, admitting every ref (GitHub Docs, "Managing environments
                # for deployment").
                failures.append(f"{repo}/{DOCKERHUB_ENV}: could not read environment ({exc}) -- a job naming a missing environment recreates it UNPROTECTED")
                continue
            policies = (policy_doc or {}).get("branch_policies") or []
            for violation in check_environment(env_payload, policies, env_name=DOCKERHUB_ENV):
                failures.append(f"{repo}/{DOCKERHUB_ENV}: {violation}")

        self._report_coverage("environments", self.readable, self.unreadable)
        self.assertEqual(
            failures,
            [],
            "dockerhub environment ref-policy drift detected:\n  " + "\n  ".join(failures) + "\nRepair: " + REPAIR_HINT_BY_ENV[DOCKERHUB_ENV],
        )

    def test_no_dockerhub_credential_at_repository_scope(self) -> None:
        failures: list = []
        verified: list = []
        unverified: list = list(self.unreadable)
        for repo in self.readable:
            try:
                secret_names = _gh_names(f"repos/{OWNER}/{repo}/actions/secrets", "secrets")
                variable_names = _gh_names(f"repos/{OWNER}/{repo}/actions/variables", "variables")
            except RuntimeError:
                # Listing secrets needs more than read access; name the gap, never pass on it.
                unverified.append(repo)
                continue
            verified.append(repo)
            failures.extend(f"{repo}: {violation}" for violation in check_repo_scope_credentials(secret_names, variable_names))

        self._report_coverage("repository scope", verified, unverified)
        if not verified:
            raise unittest.SkipTest(f"could not list repository-scope secrets/variables in ANY image repo: {', '.join(unverified)}")
        self.assertEqual(
            failures,
            [],
            "Docker Hub credential found at REPOSITORY scope:\n  " + "\n  ".join(failures) + "\nRepair: delete that copy with no --env, then re-run its line from notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md §5.2B step 3 (§6 has the note). If a TOKEN value was ever stored in a variable, it is exposed: §8 first.",
        )

    def test_repos_without_an_image_have_no_dockerhub_environment(self) -> None:
        """Anti-sprawl: the credential environment exists only where an image is published."""
        failures: list = []
        verified: list = []
        unverified: list = []
        for repo in sorted((_registry_repos() | set(NON_PUBLISHING_REPOS)) - set(DOCKERHUB_REPOS)):
            try:
                doc = _gh_json(f"repos/{OWNER}/{repo}/environments")
            except RuntimeError:
                unverified.append(repo)
                continue
            verified.append(repo)
            names = {str(e.get("name")) for e in (doc or {}).get("environments") or []}
            if DOCKERHUB_ENV in names:
                failures.append(f"{repo}: environment '{DOCKERHUB_ENV}' exists but {repo} is not in DOCKERHUB_REPOS -- add the repo deliberately, or delete the environment")

        self._report_coverage("anti-sprawl", verified, unverified)
        if not verified:
            raise unittest.SkipTest(f"could not enumerate environments of ANY non-image repo: {', '.join(unverified)}")
        self.assertEqual(failures, [], "\n  ".join(failures))


if __name__ == "__main__":
    unittest.main(verbosity=2)
