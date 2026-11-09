"""
3-way merge the flood-4 ml tests carrier's four shared files onto origin/main 147263ec (juniper-ml#2516).

#2516 (the yamaguchi securityfs incident) changed .github/workflows/ci.yml, AGENTS.md, CHANGELOG.md and
docs/REFERENCE.md after the carrier (juniper-ml#2517) was built on 58397dbb. For each file this runs
`git merge-file` with base = 58397dbb's blob, ours = 147263ec's (main) and theirs = the carrier's staged
blob, then resolves each conflict by an EXPLICIT rule that first asserts the conflict is the one expected
(anything else aborts):
  - AGENTS.md, the suite-count line: one line, with the TRUE count of the merged ci.yml regression list;
  - docs/REFERENCE.md, the `### Running every suite` tally: main's line, then the carrier's addition
    re-counted on top of main's 228;
  - CHANGELOG.md, the top `## [Unreleased]`: main's `### Added` entry first, then the carrier's entry
    under the same heading (one `### Added`).
Non-conflicting hunks merge as git merges them (main's and the carrier's lines both kept, in file order).

--inspect prints every conflict block (diff3 style) and writes nothing in the repository.
--write writes each merged file to <work-dir>/<flat name>.merged.log only (the worktree is untouched, so
  it can still be detached onto 147263ec first).
--freeze copies the four files AS THEY STAND IN THE WORKTREE to <frozen-dir>/<repo path> and writes
  <frozen-dir>/SHA256SUMS.txt. Run it last: juniper-check-doc-links scans tmp/ (until juniper-ml#2360),
  so the frozen .md copies would fail a later pre-commit run in this worktree.

Usage: python3 util/ad-hoc/2026-11-07_flood4_rebase_147263ec_merge.py (--inspect | --write | --freeze) <work-dir> <frozen-dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier, rebase onto juniper-ml#2516)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2517 (the carrier), juniper-ml#2516 (147263ec)
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

BASE = "58397dbb357e6024bdedf15d982af717c7aead9b"
MAIN = "147263ec146324d859dd6a45839f04862a155099"
PATHS = [".github/workflows/ci.yml", "AGENTS.md", "CHANGELOG.md", "docs/REFERENCE.md"]
CI_STEP = "      - name: Run Python regression tests"
CI_INVOKE = re.compile(r"^          python3 -m unittest -v (tests/\S+\.py)\s*$", re.M)
FLOOD4_TALLY = (
    ", **232** on 2026-11-08 with the four flood-4 suites (`tests/test_release_train_exact_caps.py`, "
    "`tests/test_per_run_timeout_boundary.py`, `tests/test_claude_agent_guard_brace_cap.py`, "
    "`tests/test_host_state_gate_boundaries.py`)"
)
MAIN_TALLY_TAIL = "**228** on 2026-11-07 with the securityfs incident's `tests/test_host_api_filesystems_check.py`"
_CONFLICT = re.compile(r"^<<<<<<< ours\n(.*?)^\|\|\|\|\|\|\| base\n(.*?)^=======\n(.*?)^>>>>>>> theirs\n", re.M | re.S)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def merge(work: Path, path: str) -> str:
    flat = path.replace("/", "__")
    files = {}
    for role, spec in (("ours", f"{MAIN}:{path}"), ("base", f"{BASE}:{path}"), ("theirs", f":{path}")):
        f = work / f"{flat}.{role}.log"
        f.write_text(git("show", spec), encoding="utf-8")
        files[role] = f
    proc = subprocess.run(
        ["git", "merge-file", "-p", "--diff3", "-L", "ours", "-L", "base", "-L", "theirs", str(files["ours"]), str(files["base"]), str(files["theirs"])],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode < 0:
        raise SystemExit(f"{path}: git merge-file failed: {proc.stderr}")
    return proc.stdout


def ci_count(ci_text: str) -> int:
    start = ci_text.index(CI_STEP)
    nxt = ci_text.find("\n      - name: ", start + len(CI_STEP))
    block = ci_text[start : nxt if nxt >= 0 else len(ci_text)]
    suites = CI_INVOKE.findall(block)
    if len(suites) != len(set(suites)):
        raise SystemExit("ci.yml: a suite is invoked twice in the regression step")
    return len(suites)


def resolve(path: str, text: str, count: int | None) -> str:
    blocks = list(_CONFLICT.finditer(text))
    out, pos = [], 0
    for m in blocks:
        ours, base, theirs = m.group(1), m.group(2), m.group(3)
        out.append(text[pos : m.start()])
        if path == "AGENTS.md":
            assert "the full ordered list of 227 `python3 -m unittest`" in base, base
            assert "the full ordered list of 228 `python3 -m unittest`" in ours and "the full ordered list of 231 `python3 -m unittest`" in theirs, (ours, theirs)
            assert count is not None
            out.append(theirs.replace("of 231 `python3", f"of {count} `python3"))
        elif path == "docs/REFERENCE.md":
            assert MAIN_TALLY_TAIL in ours and "**231** on 2026-11-08 with the four flood-4 suites" in theirs, "unexpected REFERENCE.md conflict"
            assert ours.count(MAIN_TALLY_TAIL) == 1
            out.append(ours.replace(MAIN_TALLY_TAIL, MAIN_TALLY_TAIL + FLOOD4_TALLY, 1))
        elif path == "CHANGELOG.md":
            assert ours.startswith("### Added\n\n") and theirs.startswith("### Added\n\n") and base == "", (ours[:40], theirs[:40], base[:40])
            out.append(ours + theirs[len("### Added\n\n") :])
        else:
            raise SystemExit(f"{path}: unexpected conflict:\n{m.group(0)[:2000]}")
        pos = m.end()
    out.append(text[pos:])
    merged = "".join(out)
    if "<<<<<<<" in merged or ">>>>>>>" in merged or "\n=======\n" in merged:
        raise SystemExit(f"{path}: conflict markers remain")
    return merged


def freeze(frozen: Path) -> int:
    sums = []
    for p in PATHS:
        data = Path(p).read_bytes()
        target = frozen / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        sums.append(f"{digest}  {p}")
        print(f"froze {p} -> {target} sha256={digest}")
    (frozen / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    mode, work, frozen = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if mode == "--freeze":
        return freeze(frozen)
    work.mkdir(parents=True, exist_ok=True)
    raw = {p: merge(work, p) for p in PATHS}
    for p in PATHS:
        n = len(_CONFLICT.findall(raw[p]))
        print(f"{p}: {n} conflict block(s)")
        if mode == "--inspect":
            for m in _CONFLICT.finditer(raw[p]):
                print("----- ours\n" + m.group(1)[:1500] + "----- base\n" + m.group(2)[:600] + "----- theirs\n" + m.group(3)[:1500] + "-----")
    if mode == "--inspect":
        return 0
    merged_ci = resolve(".github/workflows/ci.yml", raw[".github/workflows/ci.yml"], None)
    count = ci_count(merged_ci)
    print(f"merged ci.yml regression list: {count} suites")
    merged = {".github/workflows/ci.yml": merged_ci}
    for p in PATHS[1:]:
        merged[p] = resolve(p, raw[p], count)
    for p in PATHS:
        out = work / (p.replace("/", "__") + ".merged.log")
        out.write_text(merged[p], encoding="utf-8")
        print(f"wrote {out} sha256={hashlib.sha256(merged[p].encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
