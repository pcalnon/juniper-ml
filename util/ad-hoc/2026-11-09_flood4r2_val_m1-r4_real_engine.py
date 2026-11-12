#!/usr/bin/env python3
"""
Run juniper-data's pull-request Gitleaks step (round 2's and round 4's ci.yml) on synthetic repositories, real engine.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
The validator's own shapes, independent of the builder's and the round-3 validator's builders. Each shape builds a
repository under --out (no remote) with fabricated GitHub-PAT-shaped values assembled at runtime, runs the step's
`run:` block from the given ci.yml under `bash -e` (GitHub's default shell) with the official engine first on PATH,
and records the exit status, the octopus/::error lines, and the (commit, file) of every finding from the SARIF.

Shapes: single-parent token; conflict-resolution token; a merged-in side commit's token; 35 commits with tokens in
commits 1 and 35; a clean merge of a base branch holding a token; octopus (evil, clean); a token on a line that LOOKS
like a remerge note (in a commit, and in a conflict resolution); a token-shaped conflicted PATH; a header-only
remerge stanza (modify/delete) followed in the same merge by a file holding a token; a conflicted path holding a
newline; a criss-cross merge; and the failure paths (no RUNNER_TEMP, a git that rejects --remerge-diff, no engine,
an invalid .gitleaks.toml).

Usage:
    python3 <this> --r2-ci <ci.yml> --r4-ci <ci.yml> --engine <gitleaks> --repo-config <dir with .gitleaks.toml> --out <dir>
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import string
import subprocess  # nosec B404 - fixed argv: git, bash running the workflow step, in scratch repositories
import sys
from pathlib import Path

import yaml

STEP = "Run Gitleaks over the pull request (Secrets Detection)"
ALPHA = string.ascii_letters + string.digits
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def pat(step: int, start: int = 0) -> str:
    return "ghp_" + "".join(ALPHA[(start + i * step) % 62] for i in range(36))


class Repo:
    def __init__(self, root: Path, cfg_dir: Path) -> None:
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        self.root = root
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(root.parent), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        self.git("init", "-q", "-b", "main")
        self.git("config", "commit.gpgsign", "false")
        shutil.copyfile(cfg_dir / ".gitleaks.toml", root / ".gitleaks.toml")
        shutil.copyfile(cfg_dir / ".gitleaksignore", root / ".gitleaksignore")
        self.git("add", ".gitleaks.toml", ".gitleaksignore")
        self.git("commit", "-q", "--no-verify", "-m", "root")

    def git(self, *args: str, ok: tuple[int, ...] = (0,)) -> str:
        res = subprocess.run(["/usr/bin/git", *args], cwd=self.root, env=self.env, capture_output=True, text=True, check=False)  # nosec B603
        if res.returncode not in ok:
            raise SystemExit(f"git {args} -> {res.returncode}: {res.stdout}{res.stderr}")
        return res.stdout.strip()

    def write(self, rel: str, content: str | bytes) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")

    def commit(self, rel: str, content: str | bytes, subject: str | None = None) -> str:
        self.write(rel, content)
        self.git("add", "--", rel)
        self.git("commit", "-q", "--no-verify", "-m", subject or f"add {rel}")
        return self.git("rev-parse", "HEAD")

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")


def step_script(ci: Path) -> str:
    wf = yaml.safe_load(ci.read_text(encoding="utf-8"))
    return next(s["run"] for s in wf["jobs"]["security"]["steps"] if s.get("name") == STEP)


def run_step(ci: Path, repo: Repo, base: str, head: str, pr_commits: str, path_prefix: str, runner_temp: bool = True) -> dict:
    rep = repo.root / "reports"
    if rep.exists():
        shutil.rmtree(rep)
    env = {"PATH": f"{path_prefix}:/usr/bin:/bin", "HOME": str(repo.root.parent), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "BASE_SHA": base, "HEAD_SHA": head, "PR_COMMITS": pr_commits, "GITHUB_STEP_SUMMARY": str(repo.root.parent / "summary.md")}
    if runner_temp:
        rt = repo.root.parent / "runner-temp"
        rt.mkdir(exist_ok=True)
        env["RUNNER_TEMP"] = str(rt)
    res = subprocess.run(["bash", "-e", "-c", step_script(ci)], cwd=repo.root, env=env, capture_output=True, text=True, timeout=300, check=False)  # nosec B603 B607
    sarif = rep / "security" / "gitleaks.sarif"
    found = None
    if sarif.is_file():
        data = json.loads(sarif.read_text(encoding="utf-8"))
        results = data["runs"][0].get("results") or []
        found = sorted({(r["partialFingerprints"].get("commitSha", ""), r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]) for r in results})
    text = ANSI.sub("", res.stdout + res.stderr)
    fps = sorted(ln.split("Fingerprint:", 1)[1].strip() for ln in text.splitlines() if "Fingerprint:" in ln)
    notes = [ln for ln in text.splitlines() if "::error" in ln or "::warning" in ln or "[git]" in ln or "FTL" in ln]
    return {"rc": res.returncode, "engine_ran": sarif.is_file(), "found": found, "fingerprints": fps, "notes": notes[:6], "_log": text}


def conflict_merge(repo: Repo, rel: str, start: str | bytes, pr_side: str | bytes, base_side: str | bytes, resolution: str | bytes, extra: dict[str, str] | None = None, pr_subject: str | None = None) -> tuple[str, str, str]:
    """PR branch `pr` changes rel, main changes rel (that is `base`), pr merges base over the conflict. Returns (base, merge, head)."""
    repo.commit(rel, start)
    repo.git("checkout", "-q", "-b", "pr")
    repo.commit(rel, pr_side, pr_subject)
    repo.git("checkout", "-q", "main")
    base = repo.commit(rel, base_side)
    repo.git("checkout", "-q", "pr")
    repo.git("merge", "--no-ff", "--no-verify", "-q", "-m", "merge main", base, ok=(1,))
    if resolution is None:
        repo.git("rm", "-q", "--", rel)
    else:
        repo.write(rel, resolution)
        repo.git("add", "--", rel)
    for k, v in (extra or {}).items():
        repo.write(k, v)
        repo.git("add", "--", k)
    repo.git("commit", "-q", "--no-verify", "-m", "merge main")
    merge = repo.head()
    head = repo.commit("pr/after.txt", "after\n")
    return base, merge, head


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-ci", required=True, type=Path)
    ap.add_argument("--r4-ci", required=True, type=Path)
    ap.add_argument("--engine", required=True, type=Path)
    ap.add_argument("--repo-config", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out = args.out / "engine-shapes"
    out.mkdir(parents=True, exist_ok=True)
    engine_bin = out / "engine-bin"
    engine_bin.mkdir(exist_ok=True)
    link = engine_bin / "gitleaks"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(args.engine.resolve())
    old_git_dir = out / "old-git"
    old_git_dir.mkdir(exist_ok=True)
    (old_git_dir / "git").write_text('#!/bin/sh\nfor a in "$@"; do [ "$a" = "--remerge-diff" ] && { echo "fatal: unrecognized argument: --remerge-diff" >&2; exit 128; }; done\nexec /usr/bin/git "$@"\n', encoding="utf-8")
    (old_git_dir / "git").chmod(0o755)
    cfg = args.repo_config
    results: dict[str, dict] = {}

    def record(name: str, repo: Repo, base: str, head: str, n: str, expect: dict, both: bool = True, **kw: object) -> None:
        row: dict = {"expect": expect, "base": base, "head": head}
        for label, ci in (("r4", args.r4_ci), ("r2", args.r2_ci)):
            if label == "r2" and not both:
                continue
            r = run_step(ci, repo, base, head, n, str(kw.get("path_prefix", engine_bin)), bool(kw.get("runner_temp", True)))
            (out / f"{name}.{label}.log").write_text(r.pop("_log"), encoding="utf-8")
            row[label] = r
        results[name] = row
        print(json.dumps({name: {k: (v if k not in ("r2", "r4") else {kk: vv for kk, vv in v.items() if kk in ("rc", "engine_ran", "found", "notes")}) for k, v in row.items() if k not in ("base", "head")}}))
        sys.stdout.flush()

    # 1 single-parent
    r = Repo(out / "s01" / "repo", cfg)
    base = r.head()
    c1 = r.commit("pr/a.txt", "GITHUB_TOKEN=" + pat(7) + "\n")
    record("s01_single_parent", r, base, c1, "1", {"r4_rc": 1, "found": [[c1, "pr/a.txt"]]})
    # 2 conflict-resolution token
    r = Repo(out / "s02" / "repo", cfg)
    tok = "GITHUB_TOKEN=" + pat(11) + "\n"
    base, merge, head = conflict_merge(r, "conf/settings.txt", "a=1\nb=2\nc=3\n", "a=1\nb=PR\nc=3\n", "a=1\nb=BASE\nc=3\n", "a=1\nb=PR\n" + tok + "c=3\n")
    record("s02_conflict_resolution_token", r, base, head, "3", {"r4_rc": 1, "found": [[merge, "conf/settings.txt"]]})
    # 3 merged-in side commit
    r = Repo(out / "s03" / "repo", cfg)
    base = r.commit("base/b.txt", "b\n")
    r.commit("pr/p1.txt", "p1\n")
    r.git("checkout", "-q", "-b", "side")
    side = r.commit("pr/side.txt", "GITHUB_TOKEN=" + pat(13) + "\n")
    r.git("checkout", "-q", "main")
    r.commit("pr/p2.txt", "p2\n")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "merge side", "side")
    head = r.commit("pr/p3.txt", "p3\n")
    record("s03_merged_in_side_commit", r, base, head, "5", {"r4_rc": 1, "found": [[side, "pr/side.txt"]]})
    # 4 long range
    r = Repo(out / "s04" / "repo", cfg)
    base = r.commit("base/b.txt", "b\n")
    shas = [r.commit(f"pr/c{i:02d}.txt", ("GITHUB_TOKEN=" + pat(17 if i == 1 else 19) if i in (1, 35) else f"f{i}") + "\n") for i in range(1, 36)]
    record("s04_long_35", r, base, shas[-1], "35", {"r4_rc": 1, "found": sorted([[shas[0], "pr/c01.txt"], [shas[-1], "pr/c35.txt"]])})
    # 5 clean merge of a base branch that holds a token (main's history)
    r = Repo(out / "s05" / "repo", cfg)
    r.git("checkout", "-q", "-b", "pr")
    r.commit("pr/p1.txt", "p1\n")
    r.git("checkout", "-q", "main")
    r.commit("base/tok.txt", "GITHUB_TOKEN=" + pat(23) + "\n")
    base = r.commit("base/later.txt", "later\n")
    r.git("checkout", "-q", "pr")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "merge main", base)
    head = r.commit("pr/p2.txt", "p2\n")
    record("s05_clean_merge_of_main_with_token", r, base, head, "3", {"r4_rc": 0, "found": []})
    # 6 octopus, evil and clean
    for evil in (True, False):
        r = Repo(out / f"s06{'e' if evil else 'c'}" / "repo", cfg)
        base = r.commit("base/b.txt", "b\n")
        for s in ("s1", "s2"):
            r.git("checkout", "-q", "-b", s, base)
            r.commit(f"pr/{s}.txt", f"{s}\n")
        r.git("checkout", "-q", "main")
        r.commit("pr/p1.txt", "p1\n")
        r.git("merge", "--no-ff", "--no-verify", "--no-commit", "-q", "s1", "s2")
        if evil:
            r.write("pr/added-in-octopus.txt", "GITHUB_TOKEN=" + pat(29) + "\n")
            r.git("add", "pr/added-in-octopus.txt")
        r.git("commit", "-q", "--no-verify", "-m", "octopus")
        head = r.head()
        record(f"s06_octopus_{'evil' if evil else 'clean'}", r, base, head, "4", {"r4_rc": 1, "r4_engine_ran": False})
    # 7 a token on a line that looks like a remerge note, in an ordinary commit
    r = Repo(out / "s07" / "repo", cfg)
    base = r.head()
    c1 = r.commit("pr/looks.txt", "remerge CONFLICT (content): Merge conflict in x GITHUB_TOKEN=" + pat(31) + "\n")
    record("s07_remerge_looking_line_in_commit", r, base, c1, "1", {"r4_rc": 1, "found": [[c1, "pr/looks.txt"]]})
    # 8 the same line written into a conflict resolution
    r = Repo(out / "s08" / "repo", cfg)
    line = "remerge CONFLICT (content): Merge conflict in conf/x.txt GITHUB_TOKEN=" + pat(37) + "\n"
    base, merge, head = conflict_merge(r, "conf/x.txt", "a\nb\nc\n", "a\nPR\nc\n", "a\nBASE\nc\n", "a\n" + line + "c\n")
    record("s08_remerge_looking_line_in_resolution", r, base, head, "3", {"r4_rc": 1, "found": [[merge, "conf/x.txt"]]})
    # 9 a token-shaped conflicted PATH (no token in content); plus control: a plain commit adding such a path
    r = Repo(out / "s09" / "repo", cfg)
    p = "conf/" + pat(41) + ".txt"
    triple = conflict_merge(r, p, "a\nb\nc\n", "a\nPR\nc\n", "a\nBASE\nc\n", "a\nRESOLVED\nc\n")
    base, head = triple[0], triple[2]
    record("s09_token_shaped_conflicted_path", r, base, head, "3", {"note": "compare r2 and r4; gitleaks scans patch lines, not paths"})
    r = Repo(out / "s09c" / "repo", cfg)
    base = r.head()
    c1 = r.commit("conf/" + pat(43) + ".txt", "plain content\n")
    record("s09c_control_token_shaped_path_plain_commit", r, base, c1, "1", {"note": "does the engine flag a token in a path at all?"})
    # 10 header-only remerge stanza (modify/delete kept modified, note quotes subjects with 'commit'), then a token file in the same merge
    r = Repo(out / "s10" / "repo", cfg)
    r.commit("a/moddel.txt", "one\ntwo\n")
    r.git("checkout", "-q", "-b", "pr")
    r.commit("a/moddel.txt", "one\nTWO-PR\n", "chore: pre-commit autoupdate")
    r.git("checkout", "-q", "main")
    r.git("rm", "-q", "a/moddel.txt")
    r.git("commit", "-q", "--no-verify", "-m", "delete it on main")
    base = r.head()
    r.git("checkout", "-q", "pr")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "merge main", base, ok=(1,))
    r.git("add", "a/moddel.txt")
    r.write("zz/added-in-merge.txt", "GITHUB_TOKEN=" + pat(47) + "\n")
    r.git("add", "zz/added-in-merge.txt")
    r.git("commit", "-q", "--no-verify", "-m", "merge main")
    merge = r.head()
    head = r.commit("pr/after.txt", "after\n")
    plain = r.git("log", "-p", "-U0", "--remerge-diff", "-1", merge)
    (out / "s10.plain-remerge.txt").write_text(plain, encoding="utf-8")
    record("s10_header_only_stanza_then_token_file", r, base, head, "3", {"r4_rc": 1, "found": [[merge, "zz/added-in-merge.txt"]]})
    # 11 a conflicted path holding a newline, then a token file in the same merge (two continuation-line shapes)
    for tag, nl in (("a", "conf/odd\nremerge name.txt"), ("b", "conf/odd\nthe commit name.txt")):
        r = Repo(out / f"s11{tag}" / "repo", cfg)
        base, merge, head = conflict_merge(r, nl, "a\nb\nc\n", "a\nPR\nc\n", "a\nBASE\nc\n", "a\nRESOLVED\nc\n", extra={"zz/added-in-merge.txt": "GITHUB_TOKEN=" + pat(53) + "\n"})
        plain = r.git("log", "-p", "-U0", "--remerge-diff", "-1", merge)
        (out / f"s11{tag}.plain-remerge.txt").write_text(plain, encoding="utf-8")
        record(f"s11{tag}_newline_in_conflicted_path_then_token_file", r, base, head, "3", {"r4_rc": 1, "found": [[merge, "zz/added-in-merge.txt"]]})
    # 12 criss-cross: two merges that cross, then a resolution holding a token
    r = Repo(out / "s12" / "repo", cfg)
    r.commit("f.txt", "1\n2\n3\n")
    base0 = r.head()
    r.git("checkout", "-q", "-b", "pr")
    r.commit("f.txt", "1\nPR\n3\n")
    pr1 = r.head()
    r.git("checkout", "-q", "main")
    r.commit("g.txt", "g\n")
    main1 = r.head()
    r.git("checkout", "-q", "pr")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "x1", main1)
    r.git("checkout", "-q", "main")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "x2", pr1)
    r.commit("f.txt", "1\nMAIN\n3\n")
    base = r.head()
    r.git("checkout", "-q", "pr")
    r.commit("f.txt", "1\nPR2\n3\n")
    r.git("merge", "--no-ff", "--no-verify", "-q", "-m", "merge main", base, ok=(1,))
    r.write("f.txt", "1\nGITHUB_TOKEN=" + pat(59) + "\n3\n")
    r.git("add", "f.txt")
    r.git("commit", "-q", "--no-verify", "-m", "merge main")
    merge = r.head()
    head = r.commit("pr/after.txt", "after\n")
    n = r.git("rev-list", "--count", f"{base}..{head}")
    record("s12_criss_cross_resolution_token", r, base, head, n, {"r4_rc": 1, "found": [[merge, "f.txt"]], "base0": base0})
    # 13 failure paths (round 4 only)
    r = Repo(out / "s13" / "repo", cfg)
    base = r.head()
    c1 = r.commit("pr/a.txt", "GITHUB_TOKEN=" + pat(61) + "\n")
    record("s13a_no_runner_temp", r, base, c1, "1", {"r4_rc": "non-zero, engine not run"}, both=False, runner_temp=False)
    record("s13b_git_rejects_remerge_diff", r, base, c1, "1", {"r4_rc": 1}, both=False, path_prefix=f"{old_git_dir}:{engine_bin}")
    record("s13c_no_engine", r, base, c1, "1", {"r4_rc": 127}, both=False, path_prefix=str(out / "empty-bin"))
    bad = r.commit(".gitleaks.toml", "[extend\nuseDefault = true\n")
    record("s13d_invalid_config", r, base, bad, "2", {"r4_rc": 1}, both=False)
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
