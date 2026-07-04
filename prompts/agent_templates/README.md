# Custom-Agent Prompt Templates

Curated, version-controlled prompt **templates** for the Juniper custom-agent suite. The
**Template Agent** (a Claude Code Skill, shipped in a later PR) selects a template here,
instantiates a **copy**, fills it, and validates the result before emitting it to
`prompts/generated/`.

- **Design-of-record:** [`notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`](../../notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md) (§5.4).
- **Sole gate:** [`tests/test_template_library_drift.py`](../../tests/test_template_library_drift.py).
  `prompts/**` is excluded from every pre-commit hook, so this drift test (wired into
  `ci.yml`) is the only thing keeping the library consistent. Any edit here must keep it green.

## Layout

| File | Purpose |
|------|---------|
| `manifest.yaml` | Machine-readable registry: the canonical skeleton, the placeholder convention, and one entry per template (`id`, `when_to_use`, `match_signals`, `file`, `class`, `required_fields`). |
| `generic.md` | Fallback template (always matches). Output is a candidate for **promotion** into a new named template if the shape recurs. |
| `RUBRIC.md` | Validation criteria R1–R5 (lands in PR 2b). |
| `<category>.md` | One per task category — `code-review`, `failing-tests`, … (land in PR 2b). |

## Canonical skeleton

Every template instantiates this section order (optional sections may be dropped):

```
# {{CATEGORY_TITLE}}
## Role
## Resources
## Primary Objective
## Assigned Tasks / Directives
## Key Deliverables & Requirements
## Constraints            (optional)
## Finalize / Validation  (optional)
```

## Placeholder convention

`NAME` is `UPPER_SNAKE`; every slot is wrapped in double braces:

| Form | Meaning |
|------|---------|
| `{{NAME}}` | fill slot |
| `{{!NAME: hint}}` | **required** — must be filled before the prompt is valid |
| `{{?NAME: hint}}` | optional — may be dropped |

The drift test rejects any `{{…}}` token that does not match one of these three forms.

## Adding or changing a template

1. Add/edit the `<id>.md` file following the canonical skeleton + placeholder convention.
2. Register it in `manifest.yaml` (every `*.md` except this README must be registered).
3. Run `python3 -m unittest -v tests/test_template_library_drift.py` until green.

These are **read-only sources** (D-5): the Template Agent fills a copy, never the original.
