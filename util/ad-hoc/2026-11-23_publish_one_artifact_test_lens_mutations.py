#!/usr/bin/env python3
"""Mutation run for juniper-cascor's test_publish_one_artifact.py: which workflow mutations does the suite fail on?

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (TEST-lens review of the one-artifact template sweep: cascor's test and the 11-23 checker)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: tmp/sweep/cascor/juniper-cascor (the frozen clone under review: never edited, only copied);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker, also run on each mutant)

Why
---
A test that claims to pin a property must fail when the property breaks. Each mutation below breaks (or, for the
controls, deliberately does not break) one property of cascor's three publishers. Template mutations are applied to
EVERY copy in all three workflows, so the byte-identity test cannot mask a rehearsal that fails to notice them. Each
mutant is run against the suite in a private copy of the clone and against the checker (template = the pristine
publish.yml), then the pristine files are restored.

    /opt/miniforge3/envs/JuniperCascor1/bin/python -I util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py \
        --work tmp/review-test-lens --copies 4 [--only ID ...]

The work dir must hold ``juniper-cascor/`` (a copy of the clone) and ``pristine/`` (its three publishers). Results go to
``<work>/mutations.json`` and are printed as a table.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import queue
import re
import shutil
import subprocess  # nosec B404 - fixed argv: this interpreter, pytest, actionlint and the checker
import sys
from pathlib import Path

import yaml

PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
ACTIONLINT = "/opt/miniforge3/envs/JuniperCascor1/bin/actionlint"
CHECKER = Path(__file__).resolve().parent / "2026-11-23_publish_port_template_identity.py"
FILES = ("publish.yml", "publish-protocol.yml", "publish-cascor-model.yml")
TEST = "src/tests/unit/test_publish_one_artifact.py"
ALL = FILES
P, PR, M = "publish.yml", "publish-protocol.yml", "publish-cascor-model.yml"

DOWNLOAD_STEP = """      - name: Download dist artifacts
        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2
        with:
          name: ${{ env.PUBLISH_PACKAGE }}-dist
          path: ${{ github.workspace }}
"""

#: id -> (expected: "catch" or "pass", description, {file: [(old, new, count)]}). `count` is how often `old` must occur.
MUTATIONS: dict[str, tuple[str, str, dict[str, list[tuple[str, str, int]]]]] = {}


def mutation(mid: str, expected: str, description: str, edits: dict) -> None:
    MUTATIONS[mid] = (expected, description, edits)


def everywhere(old: str, new: str, count: int = 1) -> dict:
    return {f: [(old, new, count)] for f in ALL}


# ── Ruling 1: the republish gate (the find step), applied to all three copies ────────────────────────────────────────
mutation("G1", "catch", "gate accepts a `skipped` TestPyPI job as passed", everywhere('any(job["conclusion"] != "success" for job in checks)', 'any(job["conclusion"] not in ("success", "skipped") for job in checks)'))
mutation("G2", "catch", "gate checks only the first TestPyPI job (by name)", everywhere('if "testpypi" in job["name"].lower()), key=lambda job: job["name"])', 'if "testpypi" in job["name"].lower()), key=lambda job: job["name"])[:1]'))
mutation("G3", "catch", "gate lists jobs with filter=latest", everywhere('"filter": "all"', '"filter": "latest"'))
mutation("G4", "catch", "gate checks the OLDEST release run (min id)", everywhere("run_id = max(ids)", "run_id = min(ids)"))
mutation("G5", "catch", "gate reads only the first page of jobs", everywhere('if not listing["jobs"] or len(jobs) >= listing["total_count"]:', "if True:"))
mutation("G6", "catch", "version derived from any ref, prefix stripped if present", {f: [('if os.environ.get("GITHUB_REF_TYPE") == "tag" and prefix and tag.startswith(prefix):', "if tag:", 1), ("version = tag[len(prefix) :]", "version = tag.removeprefix(prefix)", 1)] for f in ALL})
mutation("G6b", "catch", "version accepted from a branch named like a tag (ref type unchecked)", everywhere('os.environ.get("GITHUB_REF_TYPE") == "tag" and prefix and tag.startswith(prefix)', "prefix and tag.startswith(prefix)"))
mutation("G7", "catch", "per-name record: the LAST listed wins, not the highest (run_attempt, id)", everywhere('if job["name"] not in latest or (job["run_attempt"], job["id"]) > (latest[job["name"]]["run_attempt"], latest[job["name"]]["id"]):', "if True:"))
mutation("G8", "catch", "per-name record: the FIRST listed wins", everywhere('if job["name"] not in latest or (job["run_attempt"], job["id"]) > (latest[job["name"]]["run_attempt"], latest[job["name"]]["id"]):', 'if job["name"] not in latest:'))
mutation("G9", "catch", "gate refuses only `failure` (cancelled, in progress pass)", everywhere('any(job["conclusion"] != "success" for job in checks)', 'any(job["conclusion"] == "failure" for job in checks)'))
mutation("G10", "catch", "runs of another tag are not filtered out", everywhere('ids = [r["id"] for r in runs if r["head_branch"] == tag]', 'ids = [r["id"] for r in runs]'))
mutation("G12", "catch", "an EXPIRED artifact still yields run-id", everywhere('if any(a["name"] == name and not a["expired"] for a in artifacts)', 'if any(a["name"] == name for a in artifacts)'))
mutation("G13", "catch", "an artifacts-API failure is swallowed (treated as no artifact)", everywhere('artifacts = get(f"actions/runs/{run_id}/artifacts?" + urllib.parse.urlencode({"name": name, "per_page": 100}))["artifacts"]', 'try:\n              artifacts = get(f"actions/runs/{run_id}/artifacts?" + urllib.parse.urlencode({"name": name, "per_page": 100}))["artifacts"]\n          except Exception:\n              artifacts = []'))
mutation("G15", "catch", "a run with NO TestPyPI job passes the gate", everywhere("if not checks or any(", "if checks and any("))
G16_OLD = """run_id = max(ids)
          jobs = []
          page = 1
          while True:
              listing = get(f"actions/runs/{run_id}/jobs?" + urllib.parse.urlencode({"filter": "all", "per_page": 100, "page": page}))
              jobs.extend(listing["jobs"])
              if not listing["jobs"] or len(jobs) >= listing["total_count"]:
                  break
              page += 1"""
G16_NEW = """def _listing(rid):
              found, pg = [], 1
              while True:
                  lst = get(f"actions/runs/{rid}/jobs?" + urllib.parse.urlencode({"filter": "all", "per_page": 100, "page": pg}))
                  found.extend(lst["jobs"])
                  if not lst["jobs"] or len(found) >= lst["total_count"]:
                      return found
                  pg += 1


          def _passes(found):
              best = {}
              for j in found:
                  if j["name"] not in best or (j["run_attempt"], j["id"]) > (best[j["name"]]["run_attempt"], best[j["name"]]["id"]):
                      best[j["name"]] = j
              cs = [j for j in best.values() if "testpypi" in j["name"].lower()]
              return bool(cs) and all(j["conclusion"] == "success" for j in cs)


          ordered = sorted(ids, reverse=True)
          listings = {}
          run_id = ordered[0]
          for rid in ordered:
              listings[rid] = _listing(rid)
              if _passes(listings[rid]):
                  run_id = rid
                  break
          jobs = listings[run_id]"""
mutation("G16", "catch", "gate falls back to an OLDER release run of the tag that passed when the newest failed", everywhere(G16_OLD, G16_NEW))

# ── Republish step 2 and the other template steps, all copies ───────────────────────────────────────────────────────
mutation("F2", "catch", "FETCH skips the release run's SHA256SUMS even when it exists", everywhere("if recorded_path.is_file():", "if False:"))
mutation("F4", "catch", "FETCH compares the release run's SHA256SUMS as a SUBSET (extra or missing TestPyPI files pass)", everywhere("if recorded != digests:", "if any(recorded.get(n, d) != d for n, d in digests.items()):"))
mutation("X1", "catch", "index check ignores a served file this run did not build", everywhere("if expected.get(name) != digest)", "if name in expected and expected[name] != digest)", 4))
mutation("V1", "catch", "dist check ignores extra/missing files (digest of listed ones only)", everywhere("if not recorded or present != recorded:", "if not recorded:", 3))
mutation("U1", "catch", "reuse step reuses an EXPIRED artifact", everywhere('if a["name"] == name and not a["expired"]]', 'if a["name"] == name]'))
mutation("R1", "catch", "record step accepts any file in the dist dir", everywhere('strays = [n for n in names if not ((dist / n).is_file() and n.endswith((".whl", ".tar.gz")))]', "strays = []"))

# ── Ruling 2: the install check's job, and switching the check off ──────────────────────────────────────────────────
mutation("W1", "catch", "publish.yml: install runs before the cd to $RUNNER_TEMP", {P: [('          cd "${RUNNER_TEMP}"\n          VERSION="${{ github.event.release.tag_name }}"', '          VERSION="${{ github.event.release.tag_name }}"', 1), ('"juniper-cascor==${VERSION}"\n', '"juniper-cascor==${VERSION}"\n          cd "${RUNNER_TEMP}"\n', 1)]})
mutation("W2", "catch", "publish.yml: install job gains id-token: write", {P: [("      contents: read  # and nothing else: this job runs the package TestPyPI serves\n", "      contents: read  # and nothing else: this job runs the package TestPyPI serves\n      id-token: write\n", 1)]})
mutation("W3", "catch", "cascor-model: install job gains environment: testpypi", {M: [("    needs: publish-testpypi\n    runs-on: ubuntu-latest\n    permissions:\n      contents: read  # the sparse checkout", "    needs: publish-testpypi\n    runs-on: ubuntu-latest\n    environment: testpypi\n    permissions:\n      contents: read  # the sparse checkout", 1)]})
mutation("W4", "catch", "protocol: PyPI needs only the TestPyPI job", {PR: [("    needs: [publish-testpypi, verify-testpypi-install]\n", "    needs: publish-testpypi\n", 1)]})
mutation("W5", "catch", "publish.yml: PyPI job `if: always()`", {P: [("    needs: [testpypi, verify-testpypi-install]\n", "    needs: [testpypi, verify-testpypi-install]\n    if: always()\n", 1)]})
mutation("W6", "catch", "cascor-model: PyPI job `if: success() || failure()`", {M: [("    needs: [publish-testpypi, verify-testpypi-install]\n", "    needs: [publish-testpypi, verify-testpypi-install]\n    if: success() || failure()\n", 1)]})
mutation("W7", "catch", "publish.yml: retention 90 -> 89", {P: [("          retention-days: 90\n", "          retention-days: 89\n", 1)]})
mutation("W8", "catch", "protocol: a step between the TestPyPI job's download and its dist check", {PR: [("url: https://test.pypi.org/p/juniper-cascor-protocol\n    steps:\n      # One-artifact publish template, step 3. A checkout empties the workspace: none may run between this step and the\n      # job's last template step.\n" + DOWNLOAD_STEP, "url: https://test.pypi.org/p/juniper-cascor-protocol\n    steps:\n      # One-artifact publish template, step 3. A checkout empties the workspace: none may run between this step and the\n      # job's last template step.\n" + DOWNLOAD_STEP + "\n      - name: List the dist\n        run: ls -la \"${{ env.PUBLISH_DIST_DIR }}\"\n", 1)]})
mutation("W8b", "catch", "publish.yml: a build step writes into dist/ before Record SHA256SUMS", {P: [("      # One-artifact publish template, step 1: record what was built.\n      - name: Record SHA256SUMS", "      - name: Stamp the dist\n        if: steps.reuse.outputs.reuse != 'true'\n        run: echo stamped > dist/juniper_cascor-0.0.0-py3-none-any.whl\n\n      # One-artifact publish template, step 1: record what was built.\n      - name: Record SHA256SUMS", 1)]})
mutation("W9", "catch", "protocol ONLY: the find step checks the oldest run (template drift in one copy)", {PR: [("run_id = max(ids)", "run_id = min(ids)", 1)]})
mutation("I1", "catch", "publish.yml: `exit 0` before the install", {P: [("          sleep 30\n", "          sleep 30\n          exit 0\n", 1)]})
mutation("I2", "catch", "cascor-model: `exit 0` before the import check", {M: [('          done\n          python -c "import juniper_cascor_model', '          done\n          exit 0\n          python -c "import juniper_cascor_model', 1)]})
mutation("I3", "catch", "publish.yml: PIP_EXTRA_INDEX_URL=pypi.org in the install STEP's env", {P: [("      - name: Verify TestPyPI install\n        run: |\n", "      - name: Verify TestPyPI install\n        env:\n          PIP_EXTRA_INDEX_URL: https://pypi.org/simple/\n        run: |\n", 1)]})
mutation("I4", "catch", "protocol: PIP_EXTRA_INDEX_URL=pypi.org in the install JOB's env", {PR: [("  verify-testpypi-install:\n    name: Verify the TestPyPI install\n    needs: publish-testpypi\n    runs-on: ubuntu-latest\n", "  verify-testpypi-install:\n    name: Verify the TestPyPI install\n    needs: publish-testpypi\n    runs-on: ubuntu-latest\n    env:\n      PIP_EXTRA_INDEX_URL: https://pypi.org/simple/\n", 1)]})
mutation("I5", "catch", "publish.yml: pre-install the version from PyPI, so the TestPyPI install is 'already satisfied'", {P: [("          sleep 30\n", '          sleep 30\n          pip install --no-deps "juniper-cascor==${VERSION}"\n', 1)]})
mutation("I6", "catch", "publish.yml: VERSION overridden to an older release before the install", {P: [("          sleep 30\n", '          sleep 30\n          VERSION="0.13.0"\n', 1)]})
mutation("I7", "catch", "cascor-model: `trap 'exit 0' ERR` after set -euo pipefail", {M: [("          set -euo pipefail\n          # `python -c` puts its working directory first on sys.path", "          set -euo pipefail\n          trap 'exit 0' ERR\n          # `python -c` puts its working directory first on sys.path", 1)]})
mutation("I8", "catch", "publish.yml: `trap 'exit 0' ERR` after the cd", {P: [('          cd "${RUNNER_TEMP}"\n          VERSION=', "          cd \"${RUNNER_TEMP}\"\n          trap 'exit 0' ERR\n          VERSION=", 1)]})
mutation("I9", "catch", "publish.yml: `|| true` on the TestPyPI pip install (control)", {P: [('"juniper-cascor==${VERSION}"\n', '"juniper-cascor==${VERSION}" || true\n', 1)]})
mutation("I10", "catch", "protocol: continue-on-error on the install step (control)", {PR: [("      - name: Verify install from TestPyPI\n        run: |\n", "      - name: Verify install from TestPyPI\n        continue-on-error: true\n        run: |\n", 1)]})

# ── Bounds, build checks, runners ───────────────────────────────────────────────────────────────────────────────────
mutation("J1", "catch", "publish.yml: PyPI JOB env sets HASH_CHECK_ATTEMPTS=1 / INTERVAL=0 (bounds overridden)", {P: [("    needs: [testpypi, verify-testpypi-install]\n    runs-on: ubuntu-latest\n", '    needs: [testpypi, verify-testpypi-install]\n    runs-on: ubuntu-latest\n    env:\n      HASH_CHECK_ATTEMPTS: "1"\n      HASH_CHECK_INTERVAL: "0"\n', 1)]})
mutation("B1", "catch", "cascor-model: `twine check dist/* || true` (build check switched off)", {M: [("        run: twine check dist/*\n", "        run: twine check dist/* || true\n", 1)]})
mutation("B2", "catch", "protocol: build the wheel only (no sdist)", {PR: [("        run: python -m build --sdist --wheel\n", "        run: python -m build --wheel\n", 1)]})
mutation("B3", "catch", "publish.yml: build guard also admits rc* tags (prefix no longer agrees)", {P: [("    if: startsWith(github.event.release.tag_name, 'v')\n", "    if: startsWith(github.event.release.tag_name, 'v') || startsWith(github.event.release.tag_name, 'rc')\n", 1)]})
mutation("R2", "catch", "publish.yml: the TestPyPI job (id-token holder) runs on a self-hosted runner", {P: [("  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n", "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: self-hosted\n", 1)]})

# ── Edits that must NOT fail (comments; a Dependabot-style bump) and the edge cases between ─────────────────────────
mutation("C1", "pass", "YAML comments only (one added, one reworded)", {P: [("  pypi:\n    name: Publish to PyPI\n", "  pypi:\n    # a reviewer's note\n    name: Publish to PyPI\n", 1)], M: [("# Release-convention gate: a tag-triggered publish only proceeds", "# Release-convention gate (reworded): a tag-triggered publish only proceeds", 1)]})
mutation("C2", "pass", "comment inside the install step's run script, between pip and python (publish.yml)", {P: [('"juniper-cascor==${VERSION}"\n          python -c', '"juniper-cascor==${VERSION}"\n          # the import below runs from RUNNER_TEMP\n          python -c', 1)]})
mutation("C3", "pass", "comment inside the sub-package install loop (cascor-model)", {M: [('          for attempt in 1 2 3 4 5; do\n            if pip install \\\n              --no-deps \\\n              --index-url https://test.pypi.org/simple/ \\\n              "juniper-cascor-model==${version}"; then', '          for attempt in 1 2 3 4 5; do\n            # TestPyPI alone\n            if pip install \\\n              --no-deps \\\n              --index-url https://test.pypi.org/simple/ \\\n              "juniper-cascor-model==${version}"; then', 1)]})
mutation("C4", "pass", "comment line inside a TEMPLATE run script in ONE workflow (protocol's find step)", {PR: [("# One-artifact publish template (juniper-cascor publish.yml): copy verbatim; it reads PUBLISH_PACKAGE,\n          # PUBLISH_TAG_PREFIX", "# One-artifact publish template (juniper-cascor publish.yml): copy verbatim (reworded); it reads PUBLISH_PACKAGE,\n          # PUBLISH_TAG_PREFIX", 1)]})
mutation("D1", "pass", "@ref bump of checkout in publish.yml ONLY (partial bump, non-republish step)", {P: [("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1", "actions/checkout@1111111111111111111111111111111111111111  # v7.0.2", 1)]})
mutation("D2", "pass", "@ref bump of download-artifact in protocol's REPUBLISH job only (partial bump)", {PR: [("uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2\n        with:\n          name: ${{ env.PUBLISH_PACKAGE }}-dist\n          run-id:", "uses: actions/download-artifact@2222222222222222222222222222222222222222  # v8.0.3\n        with:\n          name: ${{ env.PUBLISH_PACKAGE }}-dist\n          run-id:", 1)]})
mutation("D3", "pass", "@ref bump of download-artifact everywhere (a whole Dependabot bump)", everywhere("actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2", "actions/download-artifact@2222222222222222222222222222222222222222  # v8.0.3", 3))

# ── Aimed at the cross-repo checker (each is also run against the suite) ────────────────────────────────────────────
mutation("K1", "catch", "publish.yml: install adds --extra-index-url https://pypi.org/simple/", {P: [('pip install --no-deps --index-url https://test.pypi.org/simple/ "juniper-cascor==${VERSION}"', 'pip install --no-deps --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "juniper-cascor==${VERSION}"', 1)]})
mutation("K2", "catch", "publish.yml: install from PyPI (no TestPyPI --index-url at all)", {P: [('pip install --no-deps --index-url https://test.pypi.org/simple/ "juniper-cascor==${VERSION}"', 'pip install --no-deps "juniper-cascor==${VERSION}"', 1)]})
mutation("K3", "catch", "publish.yml: build guard also runs on every dispatch (the republish dispatch builds)", {P: [("    if: startsWith(github.event.release.tag_name, 'v')\n", "    if: startsWith(github.event.release.tag_name, 'v') || github.event_name == 'workflow_dispatch'\n", 1)]})
mutation("K4", "catch", "publish.yml: a rebuild step in the PyPI job between the TestPyPI re-check and the upload", {P: [("          sys.exit(1)\n\n      - name: Publish to PyPI\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n      # One-artifact publish template, step 5, after the PyPI upload", "          sys.exit(1)\n\n      - name: Refresh the dist\n        run: pip install build && rm -rf dist && pyproject-build --outdir dist\n\n      - name: Publish to PyPI\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n      # One-artifact publish template, step 5, after the PyPI upload", 1)]})
mutation("K5", "catch", "publish.yml: continue-on-error on the TestPyPI UPLOAD step (not a template step)", {P: [("      - name: Publish to TestPyPI\n        uses:", "      - name: Publish to TestPyPI\n        continue-on-error: true\n        uses:", 1)]})
mutation("K6", "catch", "publish.yml: `if: github.run_attempt == '1'` on the PyPI job's upload step", {P: [("          sys.exit(1)\n\n      - name: Publish to PyPI\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n      # One-artifact publish template, step 5, after the PyPI upload", "          sys.exit(1)\n\n      - name: Publish to PyPI\n        if: github.run_attempt == '1'\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n      # One-artifact publish template, step 5, after the PyPI upload", 1)]})
mutation("K7", "catch", "cascor-model: the release gate renamed (push-only if: kept): item 25's exemption is by name", {M: [("      - name: Require a GitHub Release for this tag\n", "      - name: Require a Release for this tag\n", 1)]})
mutation("K8", "catch", "publish.yml: single-package publisher uses the <package>-v prefix, guard to match", {P: [("  PUBLISH_TAG_PREFIX: v\n", "  PUBLISH_TAG_PREFIX: juniper-cascor-v\n", 1), ("    if: startsWith(github.event.release.tag_name, 'v')\n", "    if: startsWith(github.event.release.tag_name, 'juniper-cascor-v')\n", 1)]})
mutation("K9", "catch", "publish.yml: the TestPyPI job keeps contents: read beside id-token (old shape)", {P: [("      id-token: write  # trusted publishing to TestPyPI; this job checks out nothing and runs no install check\n", "      contents: read\n      id-token: write  # trusted publishing to TestPyPI; this job checks out nothing and runs no install check\n", 1)]})


def apply(pristine: Path, edits: dict) -> dict[str, str]:
    out = {}
    for name in FILES:
        text = (pristine / name).read_text(encoding="utf-8")
        for old, new, count in edits.get(name, []):
            found = text.count(old)
            if found != count:
                raise ValueError(f"{name}: anchor occurs {found} times, expected {count}: {old[:90]!r}")
            text = text.replace(old, new)
        out[name] = text
    return out


def failed_tests(output: str) -> list[str]:
    return sorted({re.sub(r"\s+-\s.*$", "", line[len("FAILED ") :]).split("::", 1)[1] for line in output.splitlines() if line.startswith("FAILED ")})


def run_one(mid: str, pristine: Path, tree: Path) -> dict:
    expected, description, edits = MUTATIONS[mid]
    workflows = tree / ".github" / "workflows"
    result: dict = {"id": mid, "expected": expected, "description": description}
    try:
        texts = apply(pristine, edits)
    except ValueError as exc:
        return {**result, "error": str(exc)}
    try:
        changed = [n for n in FILES if texts[n] != (pristine / n).read_text(encoding="utf-8")]
        for name, text in texts.items():
            (workflows / name).write_text(text, encoding="utf-8")
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                return {**result, "error": f"{name} is not valid YAML: {exc}"}
        lint = subprocess.run([ACTIONLINT, *[str(workflows / n) for n in changed]], capture_output=True, text=True, check=False)  # nosec B603
        result["actionlint"] = "clean" if lint.returncode == 0 else lint.stdout.strip().splitlines()[:3]
        env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
        proc = subprocess.run([PY, "-m", "pytest", TEST, "-p", "no:cacheprovider", "-rf", "--tb=no"], cwd=tree, capture_output=True, text=True, env=env, check=False, timeout=900)  # nosec B603
        summary = [line for line in proc.stdout.splitlines() if re.search(r"\d+ (passed|failed)", line)]
        result["summary"] = summary[-1] if summary else proc.stdout[-300:]
        result["failed"] = failed_tests(proc.stdout)
        result["suite"] = "FAILS" if proc.returncode else "passes"
        checker = subprocess.run([sys.executable, "-I", str(CHECKER), "--template", str(pristine / "publish.yml"), *[str(workflows / n) for n in FILES]], capture_output=True, text=True, check=False)  # nosec B603
        result["checker"] = "FAILS" if checker.returncode else "passes"
        result["checker_lines"] = [line.strip() for line in checker.stdout.splitlines() if line.strip().startswith("- ")]
        caught = proc.returncode != 0
        result["verdict"] = ("caught" if caught else "SURVIVED") if expected == "catch" else ("passes, as it should" if not caught else "FAILS on a harmless edit")
    finally:
        for name in FILES:
            shutil.copyfile(pristine / name, workflows / name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--copies", type=int, default=4)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    pristine = args.work / "pristine"
    ids = args.only or list(MUTATIONS)
    for mid in ids:
        apply(pristine, MUTATIONS[mid][2])  # every anchor must match before anything runs
    trees: queue.Queue[Path] = queue.Queue()
    for k in range(args.copies):
        tree = args.work / f"work-{k}"
        if not tree.exists():
            shutil.copytree(args.work / "juniper-cascor", tree, symlinks=True)
        for name in FILES:
            shutil.copyfile(pristine / name, tree / ".github" / "workflows" / name)
        trees.put(tree)

    def job(mid: str) -> dict:
        tree = trees.get()
        try:
            return run_one(mid, pristine, tree)
        finally:
            trees.put(tree)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.copies) as pool:
        results = list(pool.map(job, ids))
    out = args.work / ("mutations.json" if not args.only else "mutations-only.json")
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for r in results:
        if "error" in r:
            print(f"{r['id']:5} ERROR {r['error']}")
            continue
        print(f"{r['id']:5} {r['verdict']:26} suite {r['suite']:6} checker {r['checker']:6} lint {'clean' if r['actionlint'] == 'clean' else 'WARN'}  {r['description']}")
        for name in r["failed"][:6]:
            print(f"        x {name}")
        if len(r["failed"]) > 6:
            print(f"        ... {len(r['failed']) - 6} more")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
