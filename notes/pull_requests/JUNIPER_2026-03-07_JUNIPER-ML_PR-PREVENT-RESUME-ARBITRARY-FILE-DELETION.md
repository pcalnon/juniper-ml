# Pull Request: Prevent Resume from Deleting Arbitrary Files

**Date:** 2026-03-07  
**Version(s):** N/A (tooling script, no package version)  
**Author:** cursor[bot]  
**Status:** READY_FOR_REVIEW

---

## Summary

Hardens `scripts/wake_the_claude.bash` so `--resume <file>` only deletes script-generated session files (`<uuid>.txt`) after successful UUID validation, and never deletes user-managed files on validation failure.

---

## Context / Motivation

`wake_the_claude.bash` accepts `--resume <session-id-or-file>`. A high-severity data-loss path existed where providing a filename to `--resume` could delete that file even when its contents failed session validation.

This follow-up change makes file lifecycle rules explicit:

- Resume values that are direct UUIDs are passed through unchanged.
- Resume values that are filenames are read and validated.
- File cleanup is scoped to script-generated filenames only.

---

## Interface Contract: `--resume`

### Expected Input Forms

- `--resume <uuid>`
- `--resume <filename>` where file content is a UUID

### Behavior Matrix

| Input | UUID Valid? | Claude Invoked? | File Deleted? | Notes |
| --- | --- | --- | --- | --- |
| `--resume <uuid>` | Yes | Yes | N/A | UUID forwarded directly |
| `--resume session-id.txt` with valid UUID | Yes | Yes | No | Non-generated file is preserved |
| `--resume <uuid>.txt` with matching valid UUID | Yes | Yes | Yes | Generated file is consumed |
| `--resume not-a-uuid` | No | No | No | Fails once, prints usage once |
| `--resume session-id.txt` with invalid content | No | No | No | Invalid file is preserved |

---

## Implementation Notes

### Codepaths

- `validate_session_id()`
  - Accepts UUID input directly.
  - Resolves file input, reads value, validates resolved UUID.
  - Calls cleanup only after resolved UUID is valid.
- `maybe_remove_generated_session_id_file()`
  - Deletes only when input filename exactly matches `<resolved_uuid>.txt`.
  - Preserves all other filenames.

### Operational Constraint

- File lookup uses `-f "./${session_id}"`, so the file must exist relative to the current working directory.

---

## Usage Examples

```bash
# Resume with direct UUID
./wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd --prompt "Continue"

# Resume from user-managed file (preserved)
echo "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd" > session-id.txt
./wake_the_claude.bash --resume session-id.txt --prompt "Continue"

# Resume from generated file (consumed)
echo "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd" > 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd.txt
./wake_the_claude.bash --resume 7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd.txt --prompt "Continue"
```

---

## Test Coverage

Validated by `tests/test_wake_the_claude.py`:

- `test_resume_with_uuid_passes_session_id_to_claude`
- `test_resume_with_filename_loads_uuid_and_preserves_non_generated_file`
- `test_resume_with_generated_session_file_loads_uuid_and_deletes_file`
- `test_resume_with_invalid_uuid_fails_once_without_invoking_claude`
- `test_resume_with_file_containing_invalid_uuid_fails_and_preserves_file`

Run with:

```bash
python3 -m unittest tests/test_wake_the_claude.py -v
```

---

## Knowledge Gaps Closed

- Clarifies when resume files are preserved vs consumed.
- Documents the exact cleanup predicate (`<uuid>.txt` only).
- Captures failure-mode guarantees (no Claude invocation, no file deletion on invalid resume inputs).
