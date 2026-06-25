<!--
  TEMPLATE — lean Juniper package README.
  Canonical style per notes/JUNIPER_README_STYLE_RECONCILIATION_2026-06-24.md.

  HOW TO USE:
    1. Copy this file to <package>/README.md.
    2. Replace every <PLACEHOLDER>. Delete optional sections that don't apply.
    3. Delete this comment block.

  PRINCIPLES (why this template looks the way it does):
    - Problem-first: lead with what it does and the problem it solves, in plain
      language. Put design rationale behind a link, not in the README.
    - Badges, not hardcoded versions: never paste a version number or a
      "latest published" column into prose — it rots. The PyPI badge is the
      version surface.
    - One platform narrative: do NOT add the Juniper logo or the shared
      "Research Philosophy" essay. That lives once, in the juniper-ml root
      README. Use the short callout below instead (the canonical text is
      notes/templates/SNIPPET_JUNIPER_PLATFORM_CALLOUT.md).
    - Verified examples: the quick-start must run against the real public API.
-->

# <package-name>

[![PyPI](https://img.shields.io/pypi/v/<package-name>)](https://pypi.org/project/<package-name>/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**<One-line tagline: what it is + the problem it solves, in plain language.>**

<One or two short paragraphs, problem-first: what this package does, the problem it solves, and who
would reach for it. No design rationale — link that under "Design" below.>

> **Part of the Juniper platform.** <package-name> is <its one-line role> in
> [Juniper](https://github.com/pcalnon/juniper-ml) — a multi-package ML research platform built around
> constructive (Cascade-Correlation) and recurrent neural networks. You don't need the rest of the
> platform to use this package; its Juniper dependencies resolve from PyPI.

## Install

```bash
pip install <package-name>
```

## Quick start

```python
<The smallest runnable example that delivers value. Verify it against the code before committing.>
```

<!-- OPTIONAL — for libraries with a multi-part public API. Delete if not useful. -->
## What's in the box

| Surface | What it gives you |
|---|---|
| `<name>` | <one line> |

<!-- OPTIONAL — for a service: the HTTP/CLI surface. Delete if not applicable. -->
## API / CLI

| Route / command | Purpose |
|---|---|
| `<...>` | <one line> |

## Status

<Live / Beta / Alpha>. The current version is shown by the badge above; see
[`CHANGELOG.md`](./CHANGELOG.md) for history. Pin with `<package-name>>=X,<X+1>`.

<!-- OPTIONAL — delete if there's nothing beyond the standard editable-install + pytest. -->
## Development

```bash
pip install -e ".[test]"
pytest tests/ -v
```

<!-- OPTIONAL — link the design-of-record; do NOT inline it. Delete if none. -->
## Design

Part of the [Juniper](https://github.com/pcalnon) ML research platform. <Link the design doc /
deep-dive docs that hold the rationale.>

## License

MIT — see [LICENSE](./LICENSE).
