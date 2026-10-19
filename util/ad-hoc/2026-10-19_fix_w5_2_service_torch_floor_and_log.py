#!/usr/bin/env python3
"""Fix-up commit for juniper-recurrence#215 (W5.2 service half): the `[torch]` extra's model floor, and the CodeQL log line.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (the second commit on juniper-recurrence#215)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W5.2 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-19_apply_w5_2_service.py (the PR's first commit, which this follows);
         util/ad-hoc/2026-10-19_apply_w5_8b_service.py (the 0.7.0 floor raise that missed the `[torch]` site)

Why this exists
---------------
Two things found on 2026-10-19 while the PR waited for model 0.6.0's PyPI gate:

1. **juniper-recurrence 0.7.0's `[torch]` extra cannot resolve.** The W5.8 (B) service change raised the base
   floor to ``juniper-recurrence-model>=0.5.0,<0.6.0`` and ``[bench-torch]`` with it, but left the ``[torch]``
   extra at ``juniper-recurrence-model[torch]>=0.4.0,<0.5.0`` -- disjoint ranges, so ``pip install
   "juniper-recurrence[torch]==0.7.0"`` is unsatisfiable (PyPI's ``requires_dist`` shows it; 0.6.1 and earlier
   were consistent). The 0.7.0 CHANGELOG says the extra moved; it did not. #215 repeats the miss (its CHANGELOG
   says ``[torch]`` moves to ``>=0.6.0,<0.7.0``; its diff touches ``dependencies`` and ``[bench-torch]`` only).
   This moves the extra and adds ``tests/test_pyproject_floors.py``, which pins the three ranges and the image
   lock to one specifier set so the miss cannot recur.

2. **CodeQL ``py/log-injection`` on ``_folds.py``**: the WARNING for an explicit ``embargo`` below the look-back
   interpolated the request's ``embargo`` value. The repo's rule (``required_review_thread_resolution``) makes
   that thread block ``util/safe_merge.py``. The request value comes off the log line; the response's ``folding``
   block carries the resolved embargo already. The test asserts only ``"below the look-back"``.

Runs against a tree laid out like ``juniper-recurrence/juniper-recurrence/`` (the scratch copy built from the
PR head with ``gh api .../contents/<path>?ref=<sha>``), never the owner's checkout. Each edit asserts its exact
old text and must match exactly once; "new present once" counts as applied.

Usage
-----
    python3 util/ad-hoc/2026-10-19_fix_w5_2_service_torch_floor_and_log.py --root <scratch tree> [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_PYPROJECT_OLD = '    "juniper-recurrence-model[torch]>=0.4.0,<0.5.0",\n'
_PYPROJECT_NEW = (
    "    # Moves with the base floor above. 0.7.0 shipped this extra at >=0.4.0,<0.5.0 against a base of\n"
    "    # >=0.5.0,<0.6.0 -- disjoint ranges, so `pip install \"juniper-recurrence[torch]==0.7.0\"` could not\n"
    "    # resolve (found 2026-10-19 in the index's requires_dist). tests/test_pyproject_floors.py pins the\n"
    "    # three model ranges and the image lock to one specifier set.\n"
    '    "juniper-recurrence-model[torch]>=0.6.0,<0.7.0",\n'
)

_LOG_OLD = (
    '        logger.warning("crossval embargo=%d is below the look-back of %d windows, so an eval window\'s history can overlap a train window\'s; '
    'omit embargo for the default of one look-back (plan W5.2)", embargo, lookback)\n'
)
_LOG_NEW = (
    "        # The request's value stays off the log line (CodeQL py/log-injection); the response's `folding` block carries it.\n"
    '        logger.warning("crossval request set an embargo below the look-back of %d windows, so an eval window\'s history can overlap a train window\'s; '
    'omit embargo for the default of one look-back (plan W5.2)", lookback)\n'
)

_CL_ANCHOR = "\n\n## [0.7.0] - 2026-10-19\n"
_CL_MARKER = "**The `[torch]` extra resolves again.**"
_CL_NEW = f"""

### Fixed

- {_CL_MARKER} 0.7.0 raised the base floor to `juniper-recurrence-model>=0.5.0,<0.6.0`
  but left the `[torch]` extra at `juniper-recurrence-model[torch]>=0.4.0,<0.5.0` (its entry below says
  otherwise), so the two ranges were disjoint and `pip install "juniper-recurrence[torch]==0.7.0"` cannot
  resolve; 0.6.1 and earlier were consistent, and the base install and the image (which ships no torch)
  are unaffected. The extra now follows the base floor (`>=0.6.0,<0.7.0`), and the new
  `tests/test_pyproject_floors.py` pins `dependencies`, `[torch]`, `[bench-torch]` and the image lock to
  one `juniper-recurrence-model` range. Found 2026-10-19 in the index's `requires_dist`.
- The WARNING for an explicit crossval `embargo` below the look-back no longer interpolates the request's
  value (CodeQL `py/log-injection`); the response's `folding.embargo` carries it.

## [0.7.0] - 2026-10-19
"""

_TEST = '''"""The ``juniper-recurrence-model`` range is one range: ``dependencies``, ``[torch]``, ``[bench-torch]`` and the image lock agree.

0.7.0 shipped ``[torch]`` at ``>=0.4.0,<0.5.0`` against a base of ``>=0.5.0,<0.6.0`` -- disjoint, so
``pip install "juniper-recurrence[torch]==0.7.0"`` could not resolve, and no lane installs the extra at a
pinned version. A floor raise edits four sites; this fails when one is missed.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

_ROOT = Path(__file__).resolve().parents[1]
_MODEL = re.compile(r"^juniper-recurrence-model(?:\\[(?P<extras>[^\\]]*)\\])?\\s*(?P<spec>[^;]*?)\\s*(?:;.*)?$")
_LOCK = re.compile(r"^juniper-recurrence-model==(?P<version>\\S+)\\s*$", re.MULTILINE)


def _model_spec(requirements: list[str], where: str) -> SpecifierSet:
    found = [m.group("spec") for r in requirements if (m := _MODEL.match(r.strip()))]
    assert len(found) == 1, f"{where}: expected one juniper-recurrence-model requirement, found {found}"
    return SpecifierSet(found[0])


def _project() -> dict:
    return tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_torch_extras_carry_the_base_model_range():
    project = _project()
    base = _model_spec(project["dependencies"], "dependencies")
    extras = project["optional-dependencies"]
    assert _model_spec(extras["torch"], "[torch]") == base
    assert _model_spec(extras["bench-torch"], "[bench-torch]") == base


def test_image_lock_pins_a_model_inside_the_base_range():
    base = _model_spec(_project()["dependencies"], "dependencies")
    lock = (_ROOT / "requirements.lock").read_text(encoding="utf-8")
    pinned = _LOCK.findall(lock)
    assert len(pinned) == 1, f"requirements.lock: expected one juniper-recurrence-model pin, found {pinned}"
    assert Version(pinned[0]) in base, f"requirements.lock pins juniper-recurrence-model=={pinned[0]}, outside {base}"
'''


def _replace_once(path: Path, old: str, new: str, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if text.count(new) == 1 and old not in text:
        print(f"  = {path.name}: already applied")
        return False
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: {path}: expected exactly one occurrence of the anchor, found {text.count(old)}")
    if check:
        print(f"  ~ {path.name}: WOULD rewrite")
        return True
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  + {path.name}: rewrote")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="scratch tree laid out like juniper-recurrence/juniper-recurrence/")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    root = args.root.resolve()

    changed = False
    changed |= _replace_once(root / "pyproject.toml", _PYPROJECT_OLD, _PYPROJECT_NEW, args.check)
    changed |= _replace_once(root / "juniper_recurrence" / "_folds.py", _LOG_OLD, _LOG_NEW, args.check)

    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if _CL_MARKER in text:
        print("  = CHANGELOG.md: entry already present")
    else:
        if text.count(_CL_ANCHOR) != 1:
            raise SystemExit(f"ERROR: CHANGELOG.md: expected exactly one 0.7.0 heading anchor, found {text.count(_CL_ANCHOR)}")
        if args.check:
            print("  ~ CHANGELOG.md: WOULD add a '### Fixed' block to [Unreleased]")
        else:
            changelog.write_text(text.replace(_CL_ANCHOR, _CL_NEW, 1), encoding="utf-8")
            print("  + CHANGELOG.md: added a '### Fixed' block to [Unreleased]")
        changed = True

    test = root / "tests" / "test_pyproject_floors.py"
    if test.exists() and test.read_text(encoding="utf-8") == _TEST:
        print("  = tests/test_pyproject_floors.py: already present")
    else:
        if args.check:
            print("  ~ tests/test_pyproject_floors.py: WOULD write")
        else:
            test.parent.mkdir(parents=True, exist_ok=True)
            test.write_text(_TEST, encoding="utf-8")
            print("  + tests/test_pyproject_floors.py: written")
        changed = True

    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
