#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     2.0.0
License:     MIT License

Build-context hygiene sweep across the five published image repos, plus juniper-deploy.

WHY THIS EXISTS
---------------
HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md
left one non-owner-gated instruction open: *"Check the other repos before their next image
change."* It refers to the juniper-deploy defect where the Docker build context held
`secrets/` with eight live credential files and there was no `.dockerignore` -- Docker does
not honour `.gitignore`.

SCOPE -- READ THIS BEFORE QUOTING THE OUTPUT
--------------------------------------------
The source instruction (`memory/reference_juniper_deploy_image_publish_traps.md`) names
**TWO** defect classes. This script answers **class 1 only** (secrets reachable from the
build context). **Class 2 -- "an image can build, start and still be useless; assert the
artifact DOES ITS JOB"** -- is NOT swept here. Do not report class 1's result as "the
defect class does not repeat"; say which class.

Answering class 1 needs several facts per repo, not one. A missing `.dockerignore` pattern
is only a defect if a COPY can reach the file, and the `.dockerignore` must sit at the
CONTEXT root -- which is not the repo root for every repo (juniper-recurrence builds from a
nested subdirectory, so a repo-root check reports a false gap; v1.0.0 did exactly that).

    1. the build CONTEXT, read from .github/workflows/publish-image.yml
    2. whether a `.dockerignore` exists AT THAT CONTEXT ROOT, and what it excludes
    3. whether the Dockerfile uses an explicit COPY allowlist or a broad `COPY . .`
    4. ROOT-ANCHORING: whether an exclusion pattern actually covers the paths a COPY ships

Layer 3 -- a post-build assertion that no secrets/.git/.env reached the image -- is reported
separately; juniper-deploy#219 added it and no other repo has it.

WHAT v2.0.0 FIXED (all found by adversarial review of v1.0.0, 2026-09-21)
------------------------------------------------------------------------
- **Root-anchoring blindness -- the one that mattered.** Docker matches `.dockerignore`
  patterns with Go `filepath.Match` against the path RELATIVE TO THE CONTEXT ROOT. A bare
  `cascor_snapshots/` therefore does NOT match `src/cascor_snapshots/`. v1.0.0 reported
  cascor's `.dockerignore` as merely "missing secrets/" and never noticed that its
  `cascor_snapshots/` entry fails to exclude 766 `.h5` files -- every one carrying a
  plaintext `authkey_hex` -- sitting directly under the shipping `COPY src/ ./src/`.
  `check_anchoring()` now reports patterns that are shadowed this way.
- **A directory allowlist is not a file allowlist.** `COPY src/ ./src/` ships everything
  tracked under `src/`. v1.0.0's binary allowlist/broad verdict implied safety it cannot
  establish; `copy_style()` now distinguishes DIR-ALLOWLIST from FILE-ALLOWLIST.
- **Broad-COPY detector false negatives**: missed `COPY ./. /app`, lowercase `copy . .`,
  JSON-array `COPY [".", "/app"]`, and line-continuation forms.
- **Sensitive scan reached one subdirectory deep only** -- which is precisely how
  `src/cascor_snapshots/` stayed invisible. Now recursive, with pruning.

NOTE ON THE REAL MECHANISM: what keeps secrets out of the PUBLISHED images is `.gitignore`
plus CI building from `actions/checkout` (tracked files only) -- not `.dockerignore`, and
not the allowlist. This script measures the LOCAL context, which is what `docker compose
build` uses. The two differ, and the local path stamps the published release tag.

Read-only. Prints a report and exits 0 always; it is a report, not a gate.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

ROOT = Path("/home/pcalnon/Development/python/Juniper")

# repo -> (dockerfile path relative to repo, publish workflow relative to repo)
REPOS = {
    "juniper-cascor": ("Dockerfile", ".github/workflows/publish-image.yml"),
    "juniper-data": ("Dockerfile", ".github/workflows/publish-image.yml"),
    "juniper-canopy": ("Dockerfile", ".github/workflows/publish-image.yml"),
    "juniper-cascor-worker": ("Dockerfile", ".github/workflows/publish-image.yml"),
    "juniper-recurrence": ("juniper-recurrence/Dockerfile", ".github/workflows/publish-image.yml"),
    "juniper-deploy": ("Dockerfile.test", ".github/workflows/publish-image.yml"),
}

# The credential patterns this defect class needs, each with the equivalent spellings that
# would satisfy it. Exact-string membership alone produces false "missing" reports.
WANTED = {
    "secrets/": ("secrets/", "secrets", "**/secrets/", "**/secrets"),
    "*.key": ("*.key", "**/*.key"),
    "*.pem": ("*.pem", "**/*.pem"),
    ".env": (".env", "**/.env"),
    ".env.*": (".env.*", "**/.env.*", ".env*", "**/.env*"),
}

SENSITIVE_NAMES = ("secrets", "private", ".ssh", ".aws", ".gnupg")
SENSITIVE_GLOBS = ("*.key", "*.pem", "*.p12", "*.pfx", "*.age", "*.gpg", "id_rsa", ".netrc", ".npmrc", ".pypirc")
ENV_GLOB = ".env*"
PRUNE = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def resolve_context(workflow: Path) -> str:
    """Read `context:` out of the publish workflow, expanding a single `env:` indirection."""
    if not workflow.is_file():
        return "(no publish-image.yml)"
    text = workflow.read_text(encoding="utf-8", errors="replace")
    # `${{ env.APP_DIR }}` carries spaces, so capture the rest of the line, not \S+.
    m = re.search(r"^\s*context:\s*(.+?)\s*$", text, re.MULTILINE)
    if not m:
        return "(no context: key)"
    ctx = m.group(1)
    var = re.fullmatch(r"\$\{\{\s*env\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", ctx)
    if var:
        em = re.search(rf"^\s*{var.group(1)}:\s*(\S+)\s*$", text, re.MULTILINE)
        ctx = em.group(1) if em else f"(unresolved env.{var.group(1)})"
    return ctx


def copy_directives(dockerfile: Path) -> list[str]:
    """Logical COPY/ADD lines, joining `\\` continuations, excluding --from= stage copies."""
    if not dockerfile.is_file():
        return []
    raw = dockerfile.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"\\\s*\n\s*", " ", raw)  # join continuations
    out = []
    for line in raw.splitlines():
        s = line.strip()
        if re.match(r"^(COPY|ADD)\b", s, re.IGNORECASE) and "--from=" not in s:
            out.append(s)
    return out


def copy_style(dockerfile: Path) -> tuple[str, list[str]]:
    """BROAD vs DIR-allowlist vs FILE-allowlist, plus the context dirs actually shipped."""
    directives = copy_directives(dockerfile)
    if not directives:
        return ("(missing)", [])
    shipped_dirs: list[str] = []
    for s in directives:
        body = s.split(None, 1)[1] if len(s.split(None, 1)) > 1 else ""
        if body.strip().startswith("["):  # JSON-array form
            srcs = re.findall(r'"([^"]+)"', body)[:-1]
        else:
            srcs = [p for p in body.split() if not p.startswith("--")][:-1]
        for src in srcs:
            if src.rstrip("/.") == "" or src in (".", "./", "./."):
                return ("BROAD (COPY . .)", [])
            if src.endswith("/") and src not in shipped_dirs:
                # A multi-stage Dockerfile copies the same dir in builder AND runtime;
                # dedupe or every finding beneath it is reported twice.
                shipped_dirs.append(src)
    return ("DIR-allowlist" if shipped_dirs else "FILE-allowlist", shipped_dirs)


def read_patterns(ctx_dir: Path) -> list[str] | None:
    di = ctx_dir / ".dockerignore"
    if not di.is_file():
        return None
    return [
        ln.strip()
        for ln in di.read_text(encoding="utf-8", errors="replace").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def dockerignore_state(pats: list[str] | None) -> str:
    if pats is None:
        return "ABSENT at context root"
    have = set(pats)
    missing = [want for want, equivs in WANTED.items() if not have.intersection(equivs)]
    return "present, full" if not missing else f"missing {','.join(missing)}"


def _match_segments(pat_segs: list[str], path_segs: list[str]) -> bool:
    """Docker/Go `filepath.Match` semantics, segment-wise, with `**` spanning segments.

    The distinction that matters, and that a naive `fnmatch` gets WRONG: in Go's
    `filepath.Match` a `*` NEVER crosses a `/`. Python's `fnmatch` translates `*` to `.*`,
    which does. Using fnmatch directly made `excluded("sub/dir/app.log", ["*.log"])` return
    True when Docker excludes only a ROOT-level `.log`, and `excluded("a/b/c.txt", ["a/*"])`
    return True when `a/*` reaches exactly one level. Both errors read in the SAFE
    direction -- they claim a file is excluded when it ships -- which is the worst way for a
    security instrument to be wrong.
    """
    if not pat_segs:
        return not path_segs
    head, *rest = pat_segs
    if head == "**":
        if not rest:
            return True
        for i in range(len(path_segs) + 1):
            if _match_segments(rest, path_segs[i:]):
                return True
        return False
    if not path_segs:
        return False
    if not fnmatch.fnmatchcase(path_segs[0], head):
        return False
    return _match_segments(rest, path_segs[1:])


def excluded(rel: str, pats: list[str]) -> bool:
    """Is `rel` (context-relative, POSIX) excluded? Last matching pattern wins, as Docker does."""
    path_segs = [s for s in rel.split("/") if s]
    hit = False
    for p in pats:
        neg = p.startswith("!")
        pat = (p[1:] if neg else p).strip()
        # Docker treats a leading `/` as equivalent to the bare pattern; the old code never
        # stripped it, so any `/secrets`-style pattern could never match anything.
        pat = pat.lstrip("/").rstrip("/")
        if not pat:
            continue
        pat_segs = [s for s in pat.split("/") if s]
        matched = _match_segments(pat_segs, path_segs)
        if not matched:
            # A directory pattern excludes everything beneath it.
            for i in range(1, len(path_segs)):
                if _match_segments(pat_segs, path_segs[:i]):
                    matched = True
                    break
        if matched:
            hit = not neg
    return hit


def check_anchoring(ctx_dir: Path, pats: list[str] | None, shipped_dirs: list[str]) -> list[str]:
    """Patterns that LOOK like they exclude something but are root-anchored past it.

    This is the class that hid juniper-cascor/src/cascor_snapshots/: `.dockerignore` says
    `cascor_snapshots/`, the real path is `src/cascor_snapshots/`, and `filepath.Match` is
    anchored at the context root, so the pattern never fires.
    """
    if pats is None or not shipped_dirs:
        return []
    findings = []
    # Take the LAST path segment of every non-negated pattern, INCLUDING `**/`-prefixed ones.
    #
    # The first version filtered out any pattern containing `*`, which made this check
    # incapable of verifying the very fix it recommends: once `cascor_snapshots/` becomes
    # `**/cascor_snapshots/`, the pattern was dropped from `basenames`, the finding
    # disappeared, and a reader would have read that as "fixed" when it was "no longer
    # looked at". A check that stops looking after the remediation is worse than no check,
    # because it manufactures a passing result. `excluded()` below is what decides; this
    # only nominates candidates.
    basenames: dict[str, str] = {}
    for p in pats:
        if p.startswith("!"):
            continue
        last = p.rstrip("/").split("/")[-1]
        if "*" in last:  # a wildcard LEAF names no specific directory
            continue
        basenames.setdefault(last, p)
    for d in shipped_dirs:
        base = ctx_dir / d.rstrip("/")
        if not base.is_dir():
            continue
        # Walk with PRUNING. `rglob` descends into .mypy_cache and friends, which produced
        # noise like "`data/` does not match src/.mypy_cache/.../torch/utils/data/" -- a
        # real pattern miss inside a directory nothing ships, drowning the real findings.
        walk = [base]
        children: list[Path] = []
        while walk:
            cur = walk.pop()
            try:
                kids = list(cur.iterdir())
            except (PermissionError, OSError):
                continue
            for k in kids:
                # DO NOT follow symlinks. juniper-canopy's `src/logs` is a symlink to
                # `../logs`; following it attributed the ROOT `logs/` tree's 52 files to
                # `src/logs/` and reported a gap that does not exist -- the root-anchored
                # `logs/` already excludes those files correctly. A symlink is also a
                # different object to Docker than the directory it points at.
                if k.is_dir() and not k.is_symlink() and k.name not in PRUNE:
                    children.append(k)
                    walk.append(k)
        for child in sorted(children):
            if child.name in basenames:
                rel = child.relative_to(ctx_dir).as_posix()
                if not excluded(rel, pats):
                    n = sum(1 for _ in child.rglob("*") if _.is_file())
                    findings.append(f"`{basenames[child.name]}` does NOT match `{rel}/` ({n} files) — SHIPPED by COPY {d}")
    return findings


def sensitive_in(ctx_dir: Path, pats: list[str] | None) -> list[str]:
    """Recursive scan for credential-shaped paths; flags whether each is actually excluded."""
    found: list[str] = []
    stack = [ctx_dir]
    while stack:
        cur = stack.pop()
        try:
            entries = list(cur.iterdir())
        except (PermissionError, OSError):
            continue
        for p in entries:
            if p.name in PRUNE:
                continue
            rel = p.relative_to(ctx_dir).as_posix()
            is_sensitive = (
                (p.is_dir() and p.name in SENSITIVE_NAMES)
                or any(fnmatch.fnmatch(p.name, g) for g in SENSITIVE_GLOBS)
                or (fnmatch.fnmatch(p.name, ENV_GLOB) and not p.name.endswith(".example"))
            )
            if is_sensitive:
                mark = "" if (pats and excluded(rel, pats)) else "  [NOT excluded]"
                found.append(rel + mark)
            if p.is_dir():
                stack.append(p)
    return sorted(found)


def main() -> int:
    print("BUILD-CONTEXT HYGIENE SWEEP — CLASS 1 ONLY (secrets reachable from the context).")
    print("Class 2 ('does the image do its job?') is NOT covered here. See module docstring.\n")

    for name, (dfile, wf) in REPOS.items():
        repo = ROOT / name
        if not repo.is_dir():
            print(f"── {name}: repo absent\n")
            continue

        ctx_rel = resolve_context(repo / wf)
        ctx_dir = repo if ctx_rel in (".", "./") else repo / ctx_rel
        if not ctx_dir.is_dir():
            ctx_dir = repo

        pats = read_patterns(ctx_dir)
        style, shipped = copy_style(repo / dfile)
        wf_path = repo / wf
        wf_text = wf_path.read_text(encoding="utf-8", errors="replace") if wf_path.is_file() else ""
        asserts = "yes" if '"secrets"' in wf_text and "iterdir" in wf_text else "no"

        print(f"── {name}")
        print(f"   context            : {ctx_rel}")
        print(f"   COPY style         : {style}" + (f"  ships: {' '.join(shipped)}" if shipped else ""))
        print(f"   .dockerignore      : {dockerignore_state(pats)}")
        print(f"   post-build assert  : {asserts}")

        anchoring = check_anchoring(ctx_dir, pats, shipped)
        if anchoring:
            print("   ROOT-ANCHORING GAP :")
            for a in anchoring:
                print(f"       {a}")

        sens = sensitive_in(ctx_dir, pats)
        if sens:
            print(f"   sensitive (recursive, {len(sens)}):")
            for s in sens[:12]:
                print(f"       {s}")
            if len(sens) > 12:
                print(f"       … and {len(sens) - 12} more")
        print()

    print("A BROAD COPY is not the only way a context file reaches an image: a DIR-allowlist")
    print("(`COPY src/ ./src/`) ships everything tracked beneath it. `.dockerignore` is layer 2")
    print("and is ROOT-ANCHORED; the CI assert is layer 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
