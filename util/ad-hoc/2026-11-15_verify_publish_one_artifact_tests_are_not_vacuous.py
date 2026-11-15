#!/usr/bin/env python3
"""Negative control for the one-artifact publish: prove the tests/test_publish_one_artifact.py cases can FAIL.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (negative control for the one-artifact publish port, the owner's directive of 2026-11-15)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: .github/workflows/publish.yml and the six publish-<pkg>.yml (the steps marked "one-artifact publish template",
         and the republish job); tests/test_publish_one_artifact.py; juniper-cascor's
         util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py, which this ports

WHY THIS EXISTS
---------------
A test that passes against both the fixed and the broken workflow pins nothing. This copies the seven publish workflows
and the test file into a scratch directory, checks that the copy passes, then applies each mutation below: one
exact-match edit, to one file, or to every copy of a template step (so that the byte-identity case cannot be what
catches it). It runs the test file under unittest after each, restores the files, and reports any mutation the tests
still pass. The repository itself is never written.

The test file also pins each template step's sha256 to juniper-cascor's (``PIN`` below), which would catch every edit
to a template step's Python by itself. So a mutation of that Python runs WITHOUT the pin: something else, a rehearsal or
a static case, must catch it. One mutation, which keeps every copy identical and changes only a comment, is there for
the pin alone.

    python3 util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py [--scratch DIR] [--python PY]

The scratch directory defaults to a new one under the repository's gitignored ``tmp/``. It is left in place.

Exit status: 0 when the baseline passes and every mutation fails the tests; 1 otherwise; 2 when the scratch copy could
not be made or does not pass unmutated.
"""

from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess  # nosec B404 -- runs unittest with a fixed argv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUBLISH = ".github/workflows/publish.yml"
CI_TOOLS = ".github/workflows/publish-ci-tools.yml"
CONFIG_TOOLS = ".github/workflows/publish-config-tools.yml"
DOC_TOOLS = ".github/workflows/publish-doc-tools.yml"
MODEL_CORE = ".github/workflows/publish-model-core.yml"
OBSERVABILITY = ".github/workflows/publish-observability.yml"
SERVICE_CORE = ".github/workflows/publish-service-core.yml"
WORKFLOWS = (PUBLISH, CI_TOOLS, CONFIG_TOOLS, DOC_TOOLS, MODEL_CORE, OBSERVABILITY, SERVICE_CORE)
TEST = "tests/test_publish_one_artifact.py"
COPIED = (*WORKFLOWS, TEST)
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
STEP_4 = "      # One-artifact publish template, step 4: before every upload.\n      - name: Verify the dist against SHA256SUMS\n"
STEP_5 = "      # One-artifact publish template, step 5: after the TestPyPI upload, before the install check.\n"
META_GUARD = "(github.event_name == 'release' && startsWith(github.event.release.tag_name, 'v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)"
DISPATCH_ARM = " || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n"
PYPI_GRANT = "      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n"
PIN = "TestTemplate.test_the_template_steps_are_juniper_cascors_byte_for_byte"
WITHOUT_PIN = (PIN,)
#: The test classes that read the workflows, run first so that a caught mutation stops early (failfast).
STATIC = ("TestWiring", "TestUnchanged", "TestTemplate")
#: Loads the test module from the scratch tree, drops the cases named on the command line, runs the rest with failfast.
DRIVER = """\
import sys
import unittest

sys.path.insert(0, "tests")
import test_publish_one_artifact as module

skip = set(sys.argv[1:])
static = %r
groups = sorted(unittest.defaultTestLoader.loadTestsFromModule(module), key=lambda group: 0 if any(test.id().split(".")[1] in static for test in group) else 1)
suite = unittest.TestSuite(test for group in groups for test in group if test.id().split(".", 1)[1] not in skip)
result = unittest.TextTestRunner(failfast=True, verbosity=0).run(suite)
sys.exit(0 if result.wasSuccessful() and suite.countTestCases() else 1)
""" % (STATIC,)

#: (label, files, old, new, mode, cases dropped): mode "one" requires exactly one match in each file; "all" replaces every
#: match (at least one in each file); "last" replaces the last match only; an int N replaces the Nth match (0-based) only.
MUTATIONS = (
    # Only the sha256 pin can catch this one: every copy changes alike, and only a comment.
    ("a template step drifts from juniper-cascor's in every copy at once", WORKFLOWS, "# One-artifact publish template (juniper-cascor publish.yml): copy verbatim; it reads only PUBLISH_DIST_DIR.\n", "# One-artifact publish template (juniper-cascor publish.yml): copy verbatim. It reads only PUBLISH_DIST_DIR.\n", "all", ()),
    # Uploads.
    ("TestPyPI upload skips an existing file", (PUBLISH,), "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n", "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          skip-existing: true\n", "one", ()),
    ("a sub-package's PyPI upload skips an existing file", (SERVICE_CORE,), "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n", "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n          skip-existing: true\n", "last", ()),
    ("the PyPI job builds its own files again", (PUBLISH,), "      - name: Publish to PyPI\n", "      - name: Build package\n        run: python -m build\n\n      - name: Publish to PyPI\n", 0, ()),
    ("the TestPyPI upload reads another directory", (PUBLISH,), "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n", "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: dist-other/\n", "one", ()),
    ("the meta PyPI upload drops its attestations", (PUBLISH,), "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          attestations: true\n\n", "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n", "last", ()),
    ("a sub-package upload drops verbose", (CONFIG_TOOLS,), "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n", "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n", 0, ()),
    # The template scripts.
    ("one copy of the JSON check drifts", (PUBLISH,), '"HASH_CHECK_ATTEMPTS", "20"', '"HASH_CHECK_ATTEMPTS", "21"', "last", ()),
    ("a file with another sha256 is not refused", WORKFLOWS, "                  if wrong:\n", "                  if wrong and False:\n", "all", WITHOUT_PIN),
    ("a file the run did not build is ignored", WORKFLOWS, "if expected.get(name) != digest)", "if name in expected and expected.get(name) != digest)", "all", WITHOUT_PIN),
    ("the dist check ignores an extra file", WORKFLOWS, "if not recorded or present != recorded:", "if not recorded or {k: present.get(k) for k in recorded} != recorded:", "all", WITHOUT_PIN),
    ("the record step takes any file", WORKFLOWS, "          if not names or strays:\n", "          if not names:\n", "all", WITHOUT_PIN),
    ("the JSON check polls without bound", WORKFLOWS, '"HASH_CHECK_ATTEMPTS", "20"', '"HASH_CHECK_ATTEMPTS", "2000"', "all", WITHOUT_PIN),
    ("a 404 is not polled through", WORKFLOWS, "except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:", "except (ValueError, KeyError, TypeError) as exc:", "all", WITHOUT_PIN),
    ("a template step reads a workflow expression", WORKFLOWS, "          # Hash every file the build wrote", "          # ${{ github.repository }}: hash every file the build wrote", "all", WITHOUT_PIN),
    ("another package's file is accepted", WORKFLOWS, "if normalized(project) != normalized(package) or not version", "if not version", "all", WITHOUT_PIN),
    ("an index answering with zero files passes", WORKFLOWS, "                  if not missing:\n", "                  if not missing or not served:\n", "all", WITHOUT_PIN),
    ("the JSON check's request timeout is dropped", WORKFLOWS, "urllib.request.urlopen(request, timeout=30)", "urllib.request.urlopen(request)", "all", WITHOUT_PIN),
    ("the dist check counts dotfiles too", WORKFLOWS, '                  if not p.name.startswith("."):\n                      present[p.name]', "                  if True:\n                      present[p.name]", "all", WITHOUT_PIN),
    ("the JSON check skips the name and version check", WORKFLOWS, "if normalized(project) != normalized(package) or not version or not re.fullmatch", "if not re.fullmatch", "all", WITHOUT_PIN),
    # The artifact and the order of the checks.
    ("the artifact expires before the gate", (PUBLISH,), "          retention-days: 90\n", "          retention-days: 7\n", "one", ()),
    ("a sub-package's artifact expires with the gate", (CI_TOOLS,), "          retention-days: 90\n", "          retention-days: 30\n", "one", ()),
    ("the PyPI check reads TestPyPI", (PUBLISH,), "          INDEX_URL: https://pypi.org\n", "          INDEX_URL: https://test.pypi.org\n", 0, ()),
    ("no TestPyPI check before the PyPI upload", (PUBLISH,), "      - name: Verify TestPyPI still serves exactly these files\n", "      - name: Verify TestPyPI still serves these files\n", "one", ()),
    ("no TestPyPI check after a sub-package's TestPyPI upload", (MODEL_CORE,), "      - name: Verify TestPyPI serves exactly these files\n", "      - name: Verify TestPyPI serves these files\n", "one", ()),
    ("the PyPI job no longer waits for TestPyPI", (PUBLISH,), "    needs: testpypi\n", "    needs: build\n", "one", ()),
    ("the install check runs before the sha256 check", (PUBLISH,), STEP_5, "      - name: Verify TestPyPI install early\n        run: pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-ml\n\n" + STEP_5, "one", ()),
    ("a checkout runs between the TestPyPI job's download and its checks", (PUBLISH,), STEP_4, CHECKOUT + "\n" + STEP_4, 0, ()),
    ("a checkout runs after the PyPI job's download", (PUBLISH,), STEP_4, CHECKOUT + "\n" + STEP_4, 1, ()),
    ("a sub-package's sparse checkout moves before the JSON check", (CI_TOOLS,), STEP_5, CHECKOUT + "        with:\n          sparse-checkout: |\n            juniper-ci-tools/pyproject.toml\n\n" + STEP_5, "one", ()),
    # Triggers, guards, names and permissions.
    ("publish.yml also fires on a tag push", (PUBLISH,), "on:\n  release:\n    types: [published]\n", "on:\n  release:\n    types: [published]\n  push:\n    tags: ['v*']\n", "one", ()),
    ("the meta tag guard leaves the build job", (PUBLISH,), f"    if: {META_GUARD}\n", "", "one", ()),
    ("a plain dispatch no longer re-fires the meta publish", (PUBLISH,), META_GUARD, "startsWith(github.event.release.tag_name, 'v')", "one", ()),
    ("a sub-package's build runs on a republish dispatch", (SERVICE_CORE,), DISPATCH_ARM, " || github.event_name == 'workflow_dispatch'\n", "one", ()),
    ("a sub-package's concurrency cancels a running publish", (DOC_TOOLS,), "  cancel-in-progress: false\n", "  cancel-in-progress: true\n", "one", ()),
    ("the template parameters name another package", (OBSERVABILITY,), "  PUBLISH_PACKAGE: juniper-observability\n", "  PUBLISH_PACKAGE: juniper-service-core\n", "one", ()),
    ("the build job gains id-token: write", (PUBLISH,), "      actions: read  # the reuse step lists this run's artifacts\n", "      actions: read  # the reuse step lists this run's artifacts\n      id-token: write\n", "one", ()),
    ("id-token: write goes back to the workflow level", (PUBLISH,), "permissions: {}\n", "permissions:\n  id-token: write\n", "one", ()),
    ("a sub-package's PyPI job regains contents: read", (OBSERVABILITY,), PYPI_GRANT, PYPI_GRANT + "      contents: read\n", "one", ()),
    ("the TestPyPI job is renamed", (PUBLISH,), "    name: Publish to TestPyPI\n", "    name: Publish to Test PyPI\n", "one", ()),
    ("the build runs inside the testpypi environment", (PUBLISH,), "    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n      actions: read", "    runs-on: ubuntu-latest\n    environment: testpypi\n    permissions:\n      contents: read\n      actions: read", "one", ()),
    # The reuse step.
    ("the upload runs although the artifact is reused", (PUBLISH,), "      - name: Upload dist artifacts\n" + REUSE_IF, "      - name: Upload dist artifacts\n", "one", ()),
    ("the build runs although the artifact is reused", (DOC_TOOLS,), "      - name: Build sdist + wheel\n" + REUSE_IF, "      - name: Build sdist + wheel\n", "one", ()),
    ("the tag assertion runs although the artifact is reused", (CONFIG_TOOLS,), "      - name: Assert release tag matches built version\n" + REUSE_IF, "      - name: Assert release tag matches built version\n", "one", ()),
    ("the reuse step runs only on the first attempt", (PUBLISH,), "        if: github.run_attempt != '1'\n", "        if: github.run_attempt == '1'\n", "one", ()),
    ("the reuse step runs in a directory no checkout has made yet", (MODEL_CORE,), "        working-directory: ${{ github.workspace }}\n", "", "one", ()),
    ("the reuse step reuses an expired artifact", WORKFLOWS, ' if a["name"] == name and not a["expired"]]', ' if a["name"] == name]', "all", WITHOUT_PIN),
    ("the reuse step takes any artifact of the run", WORKFLOWS, ' if a["name"] == name and not a["expired"]]', ' if not a["expired"]]', "all", WITHOUT_PIN),
    # The republish job.
    ("the republish job's name says PyPI", WORKFLOWS, "    name: Republish the tested files (dispatch only)\n", "    name: Republish TestPyPI's files to PyPI\n", "all", ()),
    ("the republish job runs on a release too", WORKFLOWS, "    if: github.event_name == 'workflow_dispatch' && inputs.republish_from_testpypi\n", "    if: inputs.republish_from_testpypi || github.event_name == 'release'\n", "all", ()),
    ("the republish job uploads bytes it did not check", WORKFLOWS, "              if actual != digest:\n", "              if False:\n", "all", WITHOUT_PIN),
    ("the republish job ignores the release run's SHA256SUMS", WORKFLOWS, "              if recorded != digests:\n", "              if False:\n", "all", WITHOUT_PIN),
    ("the republish job accepts a branch named like a tag", WORKFLOWS, 'if os.environ.get("GITHUB_REF_TYPE") == "tag" and tag.startswith("v"):', 'if tag.startswith("v"):', "all", WITHOUT_PIN),
    ("the republish job takes a foreign file from TestPyPI", WORKFLOWS, "if normalized(project) != normalized(package) or file_version != version:", "if False:", "all", WITHOUT_PIN),
    ("the republish job skips the dist check", WORKFLOWS, STEP_4, "      # One-artifact publish template, step 4: before every upload.\n      - name: Verify the dist\n", "last", ()),
)


def run_tests(python: str, scratch: Path, skip: "tuple[str, ...]" = ()) -> int:
    """Run the scratch copy's test module, without the cases in ``skip``; exit 0 only when every case ran and passed."""
    proc = subprocess.run([python, "-c", DRIVER, *skip], cwd=scratch, capture_output=True, text=True, timeout=900, check=False)  # nosec B603 -- fixed argv
    return proc.returncode


def mutate(text: str, old: str, new: str, mode: "str | int") -> "str | None":
    """Return the mutated text, or None when the edit does not apply as its mode requires."""
    count = text.count(old)
    if mode == "one":
        return text.replace(old, new) if count == 1 else None
    if mode == "all":
        return text.replace(old, new) if count >= 1 else None
    nth = count - 1 if mode == "last" else int(mode)
    if not 0 <= nth < count:
        return None
    at = -1
    for _ in range(nth + 1):
        at = text.find(old, at + 1)
    return text[:at] + new + text[at + len(old) :]


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser.add_argument("--scratch", type=Path, default=REPO / "tmp" / f"verify_publish_one_artifact-{stamp}", help="an empty or absent directory to copy into")
    parser.add_argument("--python", default=sys.executable, help="an interpreter with PyYAML")
    args = parser.parse_args(argv)
    if args.scratch.exists() and any(args.scratch.iterdir()):
        print(f"REFUSED: {args.scratch} is not empty")
        return 2
    for rel in COPIED:
        (args.scratch / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, args.scratch / rel)
    originals = {rel: (args.scratch / rel).read_text(encoding="utf-8") for rel in WORKFLOWS}
    baseline = run_tests(args.python, args.scratch)
    print(f"scratch: {args.scratch}")
    print(f"baseline: unittest exit {baseline}")
    if baseline != 0:
        print("REFUSED: the unmutated copy does not pass")
        return 2
    if run_tests(args.python, args.scratch, WITHOUT_PIN) != 0:
        print("REFUSED: the unmutated copy does not pass without the pin")
        return 2
    survivors = []
    for label, files, old, new, mode, skip in MUTATIONS:
        mutated = {rel: mutate(originals[rel], old, new, mode) for rel in files}
        if any(text is None or text == originals[rel] for rel, text in mutated.items()):
            print(f"DID NOT APPLY: {label}")
            survivors.append(label)
            continue
        try:
            for rel, text in mutated.items():
                (args.scratch / rel).write_text(str(text), encoding="utf-8")
            code = run_tests(args.python, args.scratch, skip)
        finally:
            for rel in mutated:
                (args.scratch / rel).write_text(originals[rel], encoding="utf-8")
        print(f"{'caught' if code != 0 else 'SURVIVED'}: {label}{' (without the sha256 pin)' if skip else ''} (unittest exit {code})")
        if code == 0:
            survivors.append(label)
    print(f"{len(MUTATIONS) - len(survivors)} of {len(MUTATIONS)} mutations caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
