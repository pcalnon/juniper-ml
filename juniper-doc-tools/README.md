# juniper-doc-tools

[![PyPI](https://img.shields.io/pypi/v/juniper-doc-tools)](https://pypi.org/project/juniper-doc-tools/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**A zero-dependency markdown link validator (CLI + library) for documentation CI.**

`juniper-doc-tools` checks that the links in your markdown actually resolve — relative file links,
same-file heading anchors, cross-repo links into sibling repositories, and links into a parent
ecosystem directory. It ships the `juniper-check-doc-links` console script (also
`python -m juniper_doc_tools`) and a `juniper_doc_tools` library API. It is **pure stdlib — no runtime
dependencies** — so it installs into the slimmest CI image, and it is the single replacement for the
`scripts/check_doc_links.py` copy that used to be duplicated across the Juniper repositories.

> **Part of the Juniper platform.** juniper-doc-tools is the shared documentation-link gate of
> [Juniper](https://github.com/pcalnon/juniper-ml) — a multi-package ML research platform. It's a
> standalone tool with no Juniper dependencies; you can point it at any repo's docs.

## Install

```bash
pip install juniper-doc-tools          # direct
pip install "juniper-ml[doc-tools]"    # via the meta-package
```

## Quick start

CLI — the pattern every Juniper repo's docs lane uses:

```bash
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo skip
```

Library:

```python
from pathlib import Path
from juniper_doc_tools import validate_directory

result = validate_directory(Path("."), exclude_dirs={"templates", "history"}, cross_repo_mode="skip")
if not result.ok:
    for error in result.errors:
        print(error)
    raise SystemExit(1)
print(f"All {result.scanned_files} files OK ({result.cross_repo_skipped} cross-repo links skipped)")
```

Exit code `0` if all links are valid, `1` on broken links or invalid arguments.

## What it validates

Across `.md` / `.markdown` / `.rst` / `.txt` files:

| Link class | Example | Check |
|---|---|---|
| Relative file links | `[text](path/to/file.md)` | target exists on disk |
| Same-file anchors | `[text](#some-heading)` | heading exists in the file |
| Cross-repo links | `../juniper-<repo>/path.md` | per the `--cross-repo {skip,warn,check}` policy |
| Ecosystem-root links | `../../notes/…` | per `--cross-repo` (unless `--strict-repo-boundary`) |

External URLs (`http`, `https`, `mailto`) and embedded images are skipped.

## Status

**Live** on PyPI, published independently of the meta-package on `juniper-doc-tools-v*` tags. Adopted
by all eight Juniper repositories' documentation-link CI lanes (the per-repo
`scripts/check_doc_links.py` copies were deleted). The current version is shown by the badge above;
see [`CHANGELOG.md`](./CHANGELOG.md). Pin `juniper-doc-tools>=0.1.0,<0.2.0`.

## Design

Part of the [Juniper](https://github.com/pcalnon) ML research platform. The PyPI-migration plan
(four-wave structure + per-repo PR references):
[`JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md`](../notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md).

## License

MIT — see [LICENSE](./LICENSE).
