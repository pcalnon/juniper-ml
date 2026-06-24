# prompt-discovery

Environment-discovery helpers for the Juniper custom-agent suite (PR 4). They emit a JSON
**grounding bundle** — a closed-world fact set plus provenance — that grounds a generated
prompt in the *real* target repo so it never asserts an unverified path, symbol, version,
port, or convention.

## Invocation

`util/` is not a package, so invoke by path (the house idiom — no `python -m`):

```bash
python util/prompt_discovery/cli.py --repo-root <path> [--subject S] [--symbols a,b]
```

- `--repo-root` — the repo to ground against (default: CWD).
- `--subject` — a task subject; `file_probe` greps it for candidate `file:line` anchors.
- `--symbols` — comma-separated symbol names for `symbol_probe`.

A discovery failure (`repo_context` cannot resolve the target HEAD) is a hard stop: exit
code `2` and a `discovery_failed` envelope, never an empty-but-valid bundle.

## Bundle shape

The bundle carries a `provenance` envelope and one slice per probe:

- `provenance` — `captured_at`, `head_sha`, `dirty`, `ttl_seconds`, `per_probe_status`.
- `repo_context` — repo / branch / dirty / HEAD sha.
- `test_status` — last pytest result; distinguishes `cold_cache` / `unavailable` from an empty `ok`.
- `file_probe` — candidate `file:line` anchors for the subject.
- `symbol_probe` — a `resolved` def `file:line` + signature, or `unresolved`.
- `dependency_facts` — pyproject extras + version; ports / env from the parent `AGENTS.md`.
- `conventions` — AGENTS.md header, line-length, deliverable locations.
- `concurrency` — open PRs (`gh`) + worktrees (a *work* dup-guard, not a filename collision).

Every probe degrades gracefully: a missing tool or path sets that slice's `status` (e.g.
`unavailable`, `cold_cache`, `partial`) instead of aborting the bundle.

## Tests

`tests/test_prompt_discovery.py` (wired into `.github/workflows/ci.yml`) carries the
behavioural coverage — bundle schema, the provenance envelope, and the cold/empty
`test_status` distinction.
