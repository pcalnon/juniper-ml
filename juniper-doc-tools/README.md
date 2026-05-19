# juniper-doc-tools

Shared documentation tooling for the Juniper ML platform: a markdown link
validator with cross-repo and ecosystem-root awareness.

This is the long-term replacement for the standalone
`scripts/check_doc_links.py` script that historically lived in every Juniper
repo. See
[`JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
in the parent `juniper-ml` repo for the design rationale and migration plan.

## Install

```bash
pip install juniper-doc-tools
```

No runtime dependencies — pure stdlib.

## CLI usage

Two invocation forms are supported:

```bash
juniper-check-doc-links \
  --exclude templates --exclude history --exclude legacy \
  --cross-repo skip

# or, equivalently:
python -m juniper_doc_tools \
  --exclude templates --exclude history --exclude legacy \
  --cross-repo skip
```

Common flags:

| Flag | Description |
|---|---|
| `--exclude DIR` | Directory name to exclude from scanning (repeatable). |
| `--cross-repo {skip,warn,check}` | How to handle cross-repo / ecosystem-root links. `check` (default) validates them against the filesystem; `skip` is the typical CI mode. |
| `--strict-repo-boundary` | Disable ecosystem-root link classification. Links like `../../CLAUDE.md` are flagged as "outside repository boundary" instead of being subject to `--cross-repo` policy. Off by default. |
| `--repo-root PATH` | Repository root for resolving paths (default: CWD). |
| `-v`, `--verbose` | Print every link checked. |
| `--version` | Print the package version. |

Exit codes: `0` if all links valid, `1` if broken links found or arguments
are invalid.

## Library usage

```python
from pathlib import Path
from juniper_doc_tools import validate_directory

result = validate_directory(
    Path("."),
    exclude_dirs={"templates", "history"},
    cross_repo_mode="skip",
)
if not result.ok:
    for error in result.errors:
        print(error)
    raise SystemExit(1)
print(f"All {result.scanned_files} files OK ({result.cross_repo_skipped} cross-repo links skipped)")
```

## What it validates

For every `.md` (and `.markdown` / `.rst` / `.txt`) file under the repo root:

- **Relative file links** — `[text](path/to/file.md)` — the target must
  exist on disk.
- **Same-file anchors** — `[text](#some-heading)` — the heading must
  exist in the source file.
- **Cross-repo links** — `../juniper-X/path/in/sibling.md` — classified
  by regex against the known Juniper ecosystem repo set; subject to
  `--cross-repo` policy.
- **Ecosystem-root links** — `../../CLAUDE.md`, `../../notes/...`, etc. —
  paths into the Juniper parent directory; also subject to `--cross-repo`
  policy (unless `--strict-repo-boundary` is set).

External URLs (`http://`, `https://`, `mailto:`) and embedded images
(`data:`, `//`) are skipped.

## License

MIT. See [`LICENSE`](LICENSE).
