#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : juniper-canopy 0.8.1 -- packaging fix
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Apply the juniper-canopy 0.8.1 packaging fix to a sandbox copy of the tree.

Edits, all in one place so the set can be reviewed before anything is pushed:

  1. ``pyproject.toml`` -- version 0.8.0 -> 0.8.1, plus the two blocks that actually fix
     canopy#631. ``py-modules`` alone does NOT work here and fails *silently*: with build
     isolation it produces a wheel with 0 of 19 modules and exit 0. ``py-modules`` resolves
     against ``package-dir``, which this project never set, so the empty-string entry has
     to point at ``src`` -- and because ``juniper_canopy/`` lives at the repo root rather
     than under ``src/``, it needs its own entry or the build dies with
     "package directory 'src/juniper_canopy' does not exist". Measured across four
     candidate configs; this is the only one that ships 19/19 modules AND keeps all five
     packages.
  2. the three version fallback literals, which
     ``test_source_checkout_fallback_literals_track_pyproject`` pins to pyproject.
  3. a ``[0.8.1]`` CHANGELOG section -- the release-train ceremony renders the published
     Release body from exactly this section, so a fix absent from it ships unmentioned.
  4. ``publish.yml`` -- the import smoke test, in the BUILD job, against the wheel about to
     ship rather than after it is public.

Usage:
  python util/ad-hoc/2026-09-15_canopy_081_apply.py --tree /tmp/.../canopy-build
"""

import argparse
import re
import sys
from pathlib import Path

OLD, NEW = "0.8.0", "0.8.1"

PY_MODULES = [
    "audit_log", "canopy_constants", "config_manager", "csrf", "dataset_import",
    "dataset_schema", "demo_mode", "discovery", "health", "main", "middleware",
    "model_registry", "observability", "provenance", "secrets_util", "security",
    "settings", "validation_gate", "ws_security",
]

PACKAGING_BLOCK = '''[tool.setuptools.packages.find]
where = [".", "src"]
include = ["juniper_canopy*", "backend*", "communication*", "frontend*", "logger*"]

# ``packages.find`` collects PACKAGES -- directories carrying ``__init__.py``. Every bare
# ``src/<name>.py`` is a top-level MODULE, which it never collects, so releases 0.5.0
# through 0.8.0 shipped ``frontend/dashboard_manager.py`` without the ``canopy_constants``
# it imports on its first line (canopy#631). Thirteen of the 49 shipped files imported a
# module that was not in the wheel.
#
# ``py-modules`` resolves against ``package-dir``, NOT against ``packages.find.where``, and
# adding it without the block below is worse than useless: the build succeeds and produces a
# wheel with none of the modules in it. ``juniper_canopy`` needs its own mapping because it
# sits at the repository root while everything else is under ``src/``; without it the build
# fails with "package directory 'src/juniper_canopy' does not exist".
#
# ``util/wheel_import_smoke.py`` runs in ``publish.yml`` and fails the publish if any of
# these stops reaching the wheel. Adding a new ``src/*.py`` means adding it in both places.
[tool.setuptools]
py-modules = [
{modules}
]

[tool.setuptools.package-dir]
"" = "src"
juniper_canopy = "juniper_canopy"
'''

MY_ADDED = '''- **`util/wheel_import_smoke.py`, wired into `publish.yml` before TestPyPI.** It installs
  the built wheel into a fresh venv, changes to an empty directory so nothing resolves out
  of the checkout, and imports all 27 shipped packages and modules that a bare install can
  import — failing the publish if any is missing. It also refuses to run from the
  repository root, where `juniper_canopy/` would be imported from the checkout and the
  defect would be invisible. `backend.service_backend` and `demo_mode` are deliberately
  excluded: they need the `juniper-cascor` and `demo` extras, and a guard that cries wolf
  is a guard someone deletes.
'''

MY_FIXED = '''- **The published wheel omitted ten top-level modules that thirteen of its own shipped
  files import, so `pip install juniper-canopy` produced a package whose dashboard could
  not be imported.** Every release from **0.5.0** onward:

  ```
  $ python -c "import frontend.dashboard_manager"     # only the wheel on the path
  ModuleNotFoundError: No module named 'canopy_constants'
  ```

  `[tool.setuptools.packages.find]` collects **packages** — directories carrying
  `__init__.py`. Each bare `src/<name>.py` is a top-level **module**, which that mechanism
  never collects and which needs a `py-modules` entry; there was none. `canopy_constants`
  and `settings` are each imported by **13 of the 49 shipped `.py` files**. The sdist was
  no better: it carried **zero** of the twenty, and shipped `pyproject.toml` alongside
  them, so rebuilding from source reproduced the same wheel.

  **`py-modules` alone does not fix it, and fails silently.** It resolves against
  `package-dir`, which this project never set, so a build with `py-modules` and nothing
  else succeeds and emits a wheel containing **none** of the nineteen. `package-dir` now
  points the empty-string root at `src`, with an explicit entry for `juniper_canopy`
  because it lives at the repository root rather than under `src/` — without that entry
  the build fails outright on `package directory 'src/juniper_canopy' does not exist`.
  Measured across four candidate configurations against real builds; this is the only one
  that ships 19/19 modules and keeps all five packages.

  Nineteen modules ship: the twelve reachable from the shipped packages, plus the seven
  `main` pulls in. `adapter_validation` is excluded because nothing imports it.

  **Nothing in the pipeline could have caught this.** `twine check` reads metadata and the
  README, never code. `pip check` reads the dependency graph, never importability — it
  passes on a wheel that cannot import itself. And the TestPyPI verification step's
  `from juniper_canopy import __version__` passes on **all four** broken wheels, because
  that one module always shipped. The container never noticed either: `Dockerfile` copies
  `src/` in and sets `PYTHONPATH=/app/src`, so the running service resolves these from
  source and shadows site-packages. The deployed image was healthy throughout; only the
  artifact on PyPI was broken.
'''

SMOKE_STEP = '''      - name: Check package
        run: twine check dist/*

      # `twine check` reads metadata and the README; it cannot tell whether the wheel
      # carries the modules its own code imports. Releases 0.5.0-0.8.0 all passed it while
      # shipping a wheel whose dashboard could not be imported (canopy#631). This runs
      # against the artifact about to ship, before TestPyPI and long before PyPI.
      - name: Import smoke test (built wheel, nothing from the checkout)
        run: |
          python -m venv "${RUNNER_TEMP}/smoke"
          "${RUNNER_TEMP}/smoke/bin/pip" install --quiet dist/*.whl
          mkdir -p "${RUNNER_TEMP}/smoke-cwd"
          cd "${RUNNER_TEMP}/smoke-cwd"
          "${RUNNER_TEMP}/smoke/bin/python" "${GITHUB_WORKSPACE}/util/wheel_import_smoke.py"
'''


def sub_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{what}: expected exactly one occurrence, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tree", required=True)
    args = ap.parse_args()
    root = Path(args.tree).resolve()

    # 1. pyproject: version + the packaging blocks
    pp = root / "pyproject.toml"
    text = pp.read_text(encoding="utf-8")
    text = sub_once(text, f'version = "{OLD}"', f'version = "{NEW}"', "pyproject version")
    old_block = ('[tool.setuptools.packages.find]\n'
                 'where = [".", "src"]\n'
                 'include = ["juniper_canopy*", "backend*", "communication*", "frontend*", "logger*"]\n')
    mods = "\n".join(f'    "{m}",' for m in PY_MODULES)
    text = sub_once(text, old_block, PACKAGING_BLOCK.format(modules=mods), "packages.find block")
    pp.write_text(text, encoding="utf-8")
    print(f"pyproject.toml: version -> {NEW}, py-modules ({len(PY_MODULES)}) + package-dir added")

    # 2. the three pinned fallback literals
    for rel, old, new in (
        ("src/canopy_constants.py", f'def resolve_app_version(fallback: str = "{OLD}")',
         f'def resolve_app_version(fallback: str = "{NEW}")'),
        ("src/__init__.py", f'__version__ = "{OLD}"', f'__version__ = "{NEW}"'),
        ("juniper_canopy/__init__.py", f'__version__ = "{OLD}"', f'__version__ = "{NEW}"'),
    ):
        p = root / rel
        p.write_text(sub_once(p.read_text(encoding="utf-8"), old, new, rel), encoding="utf-8")
        print(f"{rel}: -> {NEW}")

    # 3. CHANGELOG: MOVE [Unreleased] into a new [0.8.1] and merge this fix into it.
    #
    # Not an insert. Whatever sits in [Unreleased] ships in this release too, and the
    # release-train ceremony renders the published Release body from the [<version>] section
    # alone -- so anything left behind in [Unreleased] ships unmentioned. That is exactly how
    # v0.8.0 nearly went out without canopy#613 / #614 / #618.
    #
    # canopy's version numbers are also REUSED: the file was written under an earlier scheme
    # that reached [0.31.0] and then reset, so a historical "## [0.8.1] - 2025-12-05" sits
    # ~3500 lines down. The ceremony anchors on `^##\s*\[?<version>\]?` and takes the FIRST
    # match, so the new section must go strictly above [0.8.0]; a blunt `"## [0.8.1]" in text`
    # check would also read that 2025 heading as "already done".
    cl = root / "CHANGELOG.md"
    text = cl.read_text(encoding="utf-8")
    start = text.index("## [Unreleased]")
    end = text.index(f"## [{OLD}] - ")
    if f"## [{NEW}]" in text[:end]:
        raise SystemExit(f"CHANGELOG already has a current [{NEW}] section")

    # Split the [Unreleased] body into {Category: body}, preserving each verbatim.
    body = text[start + len("## [Unreleased]"):end]
    carried: "dict[str, str]" = {}
    parts = re.split(r"^### +([A-Za-z]+) *$", body, flags=re.M)
    for name, chunk in zip(parts[1::2], parts[2::2]):
        if chunk.strip():
            carried[name] = chunk.strip("\n")

    merged = dict(carried)
    for name, bullet in (("Added", MY_ADDED), ("Fixed", MY_FIXED)):
        merged[name] = (bullet.rstrip("\n") + "\n\n" + merged[name]) if name in merged else bullet.rstrip("\n")

    out = [f"## [Unreleased]\n\n## [{NEW}] - 2026-09-15\n"]
    for name in ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"):
        if name in merged:
            out.append(f"\n### {name}\n\n{merged[name].strip()}\n")
    out.append("\n")
    cl.write_text(text[:start] + "".join(out) + text[end:], encoding="utf-8")
    historical = text.count(f"## [{NEW}]")
    note = f"; a historical [{NEW}] remains ~3500 lines down" if historical else ""
    print(f"CHANGELOG.md: [Unreleased] ({', '.join(carried) or 'empty'}) moved into [{NEW}] "
          f"and merged with this fix -> {', '.join(k for k in ('Added','Changed','Fixed') if k in merged)}{note}")

    # 4. publish.yml: the smoke test, in the build job
    wf = root / ".github" / "workflows" / "publish.yml"
    text = wf.read_text(encoding="utf-8")
    old_check = '      - name: Check package\n        run: twine check dist/*\n'
    wf.write_text(sub_once(text, old_check, SMOKE_STEP, "publish.yml check-package step"), encoding="utf-8")
    print("publish.yml: import smoke test added to the build job")

    # 5. sanity: the smoke script must exist in the tree we are about to ship
    if not (root / "util" / "wheel_import_smoke.py").is_file():
        print("util/wheel_import_smoke.py is MISSING from the tree", file=sys.stderr)
        return 2
    print("util/wheel_import_smoke.py present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
