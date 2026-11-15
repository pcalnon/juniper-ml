You are an independent reviewer. Read two release-notes bodies as an OUTSIDE READER on their publication day (2026-11-15 UTC) and report every statement that is false, stale, self-contradictory, misfiled or unclear. Do NOT edit, commit, push or comment anywhere; return your findings as your FINAL MESSAGE (you cannot write report files here).

## What you are reviewing
A GitHub Release body cannot be re-cut once published, and the same text is archived permanently, so errors here are expensive. Both bodies are rendered by the Juniper release train from each repo's CHANGELOG section, then a script fills the security template's header:
- juniper-cascor v0.14.0: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/filled_cascor_0_14_0.md` (rendered from the `## [0.14.0] - 2026-11-15` section of `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/eco-head/juniper-cascor/CHANGELOG.md`, a tarball of release head `668f88e903e8d72ab283544cfc61f2709047da59`).
- juniper-canopy v0.10.0: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/filled_canopy_0_10_0.md` (from `## [0.10.0] - 2026-11-15` of `.../tmp/s2/eco-head/juniper-canopy/CHANGELOG.md`, release head `1c2dbd01ef152f770d0f33883c62469751f0207c`). Note: that CHANGELOG also has an OLD `## [0.10.0] - 2025-12-06` far below, from a pre-2026 numbering; the renderer takes the topmost, which is correct.
- The header texts (title, Priority, intro paragraph, Security Impact table) come from `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/util/ad-hoc/2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py`. Everything below "## Changes in v…" is the CHANGELOG section verbatim (with link rewriting).

## Sources to check against
- Each release's tag window (every commit that ships): `gh api repos/pcalnon/juniper-cascor/compare/v0.13.0...668f88e903e8d72ab283544cfc61f2709047da59` and `gh api repos/pcalnon/juniper-canopy/compare/v0.9.0...1c2dbd01ef152f770d0f33883c62469751f0207c`. The full trees are the two tarball extracts above (read code there; never touch the primary checkouts under `/home/pcalnon/Development/python/Juniper/juniper-*`).
- Lock diffs across each window, measured by the briefing session: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/cascor_lock_window.txt` and `.../tmp/s2/canopy_lock_window.txt` (measured to the PREVIOUS heads 3c4d1dec / cb3f1562; only CHANGELOG.md changed since).
- juniper-observability 0.4.2's own notes (the security content both releases pick up): `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`; juniper-service-core 0.7.2's: `.../notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`.
- PyPI is the truth for what is published (`https://pypi.org/pypi/<pkg>/<version>/json`).

## What to look for (in priority order)
1. **Statements true when written and false on publication day.** Each CHANGELOG entry was written when its PR merged; later merges in the same window can falsify it ("not yet landed", "an open question", "still", "the next release", "the lock holds X", "a later PR will…", a count, a version). This is the failure class a previous cut (juniper-ml 0.11.5) found four instances of. Check every version or pin a bullet states against the release head's own files (locks, pyproject, conf files) and against the other bullets.
2. **The header**: every factual claim in the intro and Priority against the Security entries, the code at the head, and the 0.4.2 notes. In particular: what was exposed under juniper-observability 0.4.1 in each service, whether `send_pii` is really off in each, what stays open, and whether calling each release "security-bearing minor" with Severity Medium is consistent with the 0.4.2 notes.
3. **Coverage**: a commit in the window that changes what the wheel or the image ships (code under `src/`, `pyproject.toml`, a lock, the Dockerfile) and that no bullet describes. CI-action bumps and `conf/requirements*.txt`-only updates are deliberately left undescribed.
4. **Misfiled entries**: an entry under the wrong category (Added/Changed/Fixed/Security), or a duplicate heading.
5. **Internal contradictions** between bullets, and anything an outside reader could not follow (a bare "#NNN" whose repo is ambiguous is fine if the bullet's context names it).

One known item for context, not to re-report unless the notes contradict it: canopy's `conf/conda_environment_cpu.yaml` still pins `dash=3.3.0` while the runtime floor is now `dash>=4.0.0`.

## Constraints
- Never write under `/tmp`; if you need scratch space use `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/review/` (create it).
- Read-only on every repository; no `git` writes, no `gh` writes.
- The host's `grep` is ugrep honouring .gitignore; use `command grep` for searches that must see ignored paths.
- A claim you make must cite its evidence (file:line, a commit sha, a URL you fetched). Re-check at the source; do not guess.

## Final message format
For each body separately: a numbered list of findings, each with severity (BLOCKER = false statement or missing shipped change; MAJOR = misleading; MINOR; NIT), the exact quoted text, the evidence, and a proposed replacement text (exact wording, ready to apply). Then a short list of what you checked and found correct. Give times only where a tool printed them.
