#!/usr/bin/env python3
"""
Re-derive the git and GnuPG option-abbreviation claims of the ml-code carrier against this host's real git and gpg.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 round 2, ml-code carrier: #2485 (rewritten), #2493, #2502, #2508.

Usage: python3 -I 2026-11-08_flood4r2_ml_code_git_gpg_probe.py <out dir>

Hazard design (the owner's keyring, agent and YubiKey are never reachable):
- git runs with HOME, XDG_CONFIG_HOME and GIT_CONFIG_GLOBAL in a throwaway directory under <out dir>,
  GIT_CONFIG_NOSYSTEM=1, every inherited GIT_* variable dropped, and gpg.program set to a STUB that
  records its argv and exits 1. A signing request is therefore observed as "the stub was called";
  real gpg is never run by git. A push goes to a local bare repository that does not advertise
  push certificates, so a signed push dies before any signing program is consulted.
- gpg runs with --homedir set to a fresh empty directory under <out dir> (GNUPGHOME too), --batch
  --no-tty --no-options, --no-autostart and --agent-program /bin/false. No gpg-agent can start, so
  no pinentry and no scdaemon (the only path to a smartcard) can run. stdin is /dev/null.

Writes <out dir>/git_probe.json, gpg_probe.json and probe_summary.txt.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

FAKE_GPG = """#!/bin/sh
printf '%s\\n' "$*" >> "$(dirname "$0")/fake_gpg_calls.log"
exit 1
"""

GITCONFIG = """[user]
\tname = Probe
\temail = probe@example.invalid
\tsigningkey = PROBEKEY
[gpg]
\tprogram = {fake}
[commit]
\tgpgsign = false
[tag]
\tgpgsign = false
[push]
\tgpgSign = false
[init]
\tdefaultBranch = main
[advice]
\tdetachedHead = false
"""


def run(cmd, cwd, env, stdin=subprocess.DEVNULL, timeout=30):
    cp = subprocess.run(cmd, cwd=str(cwd), env=env, stdin=stdin, capture_output=True, text=True, timeout=timeout)  # nosec B603
    return cp


class GitLab(object):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.home = root / "home"
        self.home.mkdir(parents=True)
        (self.home / ".config").mkdir()
        self.fake = root / "bin" / "fake-gpg"
        self.fake.parent.mkdir()
        self.fake.write_text(FAKE_GPG, encoding="utf-8")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)
        self.calls = self.fake.parent / "fake_gpg_calls.log"
        (self.home / ".gitconfig").write_text(GITCONFIG.format(fake=self.fake), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in ("GNUPGHOME", "GPG_AGENT_INFO")}
        env.update(
            {
                "HOME": str(self.home),
                "XDG_CONFIG_HOME": str(self.home / ".config"),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(self.home / ".gitconfig"),
                "GNUPGHOME": str(root / "gnupg-unused"),
                "GIT_CEILING_DIRECTORIES": str(root),
                "GIT_EDITOR": "true",
                "EDITOR": "true",
                "GIT_TERMINAL_PROMPT": "0",
                "LC_ALL": "C",
            }
        )
        self.env = env
        self.counter = 0

    def git(self, repo: Path, *args: str):
        return run(["git", "-C", str(repo), *args], repo, self.env)

    def must(self, repo: Path, *args: str) -> str:
        cp = self.git(repo, *args)
        if cp.returncode != 0:
            raise RuntimeError("setup git %s failed: %s" % (" ".join(args), cp.stderr.strip()))
        return cp.stdout.strip()

    def fresh_repo(self) -> Path:
        self.counter += 1
        repo = self.root / ("r%03d" % self.counter)
        repo.mkdir()
        self.must(repo, "init", "-q")
        (repo / "a.txt").write_text("a0\n", encoding="utf-8")
        self.must(repo, "add", "-A")
        self.must(repo, "commit", "-q", "-m", "c0")
        return repo

    def commit_on(self, repo: Path, branch: str, name: str) -> str:
        self.must(repo, "checkout", "-q", branch)
        (repo / name).write_text(name + "\n", encoding="utf-8")
        self.must(repo, "add", "-A")
        self.must(repo, "commit", "-q", "-m", name)
        return self.must(repo, "rev-parse", "HEAD")

    def observe(self, repo: Path, args: list) -> dict:
        before = self.calls.read_text(encoding="utf-8") if self.calls.exists() else ""
        cp = self.git(repo, *args)
        after = self.calls.read_text(encoding="utf-8") if self.calls.exists() else ""
        err = cp.stderr.strip()
        lowered = err.casefold()
        if "ambiguous option" in lowered:
            parse = "ambiguous"
        elif "unknown option" in lowered or "unknown switch" in lowered:
            parse = "unknown"
        else:
            parse = "accepted"
        return {
            "argv": ["git", *args],
            "rc": cp.returncode,
            "signing_program_called": after != before,
            "parse": parse,
            "stderr_head": err.splitlines()[:3],
            "stderr": err[:1500],
        }


def git_commit_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    lab.must(repo, "add", "-A")
    return lab.observe(repo, ["commit", *opts, "-m", "x"])


def git_merge_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    lab.must(repo, "checkout", "-q", "-b", "topic")
    lab.commit_on(repo, "topic", "t.txt")
    lab.commit_on(repo, "main", "m.txt")
    return lab.observe(repo, ["merge", "--no-edit", *opts, "topic"])


def git_rebase_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    lab.must(repo, "checkout", "-q", "-b", "topic")
    lab.commit_on(repo, "topic", "t.txt")
    lab.commit_on(repo, "main", "m.txt")
    lab.must(repo, "checkout", "-q", "topic")
    return lab.observe(repo, ["rebase", *opts, "main"])


def git_pick_probe(lab: GitLab, sub: str, opts: list) -> dict:
    repo = lab.fresh_repo()
    lab.must(repo, "checkout", "-q", "-b", "topic")
    sha = lab.commit_on(repo, "topic", "t.txt")
    lab.commit_on(repo, "main", "m.txt")
    if sub == "revert":
        target = lab.must(repo, "rev-parse", "HEAD")
        return lab.observe(repo, ["revert", "--no-edit", *opts, target])
    return lab.observe(repo, ["cherry-pick", *opts, sha])


def git_am_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    lab.must(repo, "checkout", "-q", "-b", "topic")
    lab.commit_on(repo, "topic", "t.txt")
    mbox = lab.root / ("p%03d.mbox" % lab.counter)
    mbox.write_text(lab.must(repo, "format-patch", "-1", "--stdout") + "\n", encoding="utf-8")
    lab.must(repo, "checkout", "-q", "main")
    return lab.observe(repo, ["am", *opts, str(mbox)])


def git_pull_probe(lab: GitLab, opts: list) -> dict:
    upstream = lab.fresh_repo()
    lab.commit_on(upstream, "main", "u.txt")
    repo = lab.fresh_repo()
    lab.commit_on(repo, "main", "l.txt")
    return lab.observe(repo, ["pull", "--no-rebase", "--no-edit", "--no-ff", *opts, str(upstream), "main"])


def git_commit_tree_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    tree = lab.must(repo, "rev-parse", "HEAD^{tree}")
    return lab.observe(repo, ["commit-tree", *opts, tree, "-p", "HEAD", "-m", "x"])


def git_tag_probe(lab: GitLab, opts: list) -> dict:
    repo = lab.fresh_repo()
    return lab.observe(repo, ["tag", *opts])


def git_skip_probe(lab: GitLab, sub: str) -> dict:
    repo = lab.fresh_repo()
    return lab.observe(repo, [sub, "--skip"])


def git_push_probe(lab: GitLab, opts: list) -> dict:
    remote = lab.root / ("remote%03d.git" % (lab.counter + 1))
    lab.counter += 1
    run(["git", "init", "-q", "--bare", str(remote)], lab.root, lab.env)
    repo = lab.fresh_repo()
    obs = lab.observe(repo, ["push", *opts, str(remote), "HEAD:refs/heads/probe"])
    text = "\n".join(obs["stderr_head"]).casefold()
    if "not sending a push certificate" in text:
        mode = "IF_ASKED (signs when the remote asks; this one does not)"
    elif "does not support --signed push" in text:
        mode = "ALWAYS (signed push requested; died before signing)"
    elif "bad" in text and "signed" in text:
        mode = "bad value (git refuses)"
    elif obs["parse"] != "accepted":
        mode = obs["parse"]
    elif obs["rc"] == 0:
        mode = "NEVER (pushed without a certificate)"
    else:
        mode = "error"
    obs["push_cert_mode"] = mode
    return obs


def git_probes(root: Path) -> list:
    lab = GitLab(root)
    results = []
    commit_signing = [["--g"], ["--gp"], ["--gpg"], ["--gpg-s"], ["--gpg-si"], ["--gpg-sign"], ["--gpg-sign=KEY"], ["--gpg=KEY"], ["-S"]]
    commit_not = [["--signoff"], ["-s"], ["--no-gpg-sign"], ["--no-gpg"], ["--no-g"], ["--gpg-sign", "--no-gpg-sign"]]
    for opts in commit_signing + commit_not:
        results.append(dict(git_commit_probe(lab, opts), case="commit " + " ".join(opts)))
    for opts in (["--g"], ["--gpg"], ["--verify-signatures"], ["--signoff"]):
        results.append(dict(git_merge_probe(lab, opts), case="merge " + " ".join(opts)))
    for opts in (["--gpg"], ["--g"]):
        results.append(dict(git_rebase_probe(lab, opts), case="rebase " + " ".join(opts)))
    for opts in (["--gpg-sign"], ["--gpg"], ["--g"]):
        results.append(dict(git_pick_probe(lab, "cherry-pick", opts), case="cherry-pick " + " ".join(opts)))
        results.append(dict(git_pick_probe(lab, "revert", opts), case="revert " + " ".join(opts)))
    for opts in (["--gpg"], ["--gpg-sign"], ["--g"]):
        results.append(dict(git_am_probe(lab, opts), case="am " + " ".join(opts)))
    for opts in (["--gpg"], ["--g"]):
        results.append(dict(git_pull_probe(lab, opts), case="pull " + " ".join(opts)))
    for opts in (["--gpg"], ["--g"]):
        results.append(dict(git_commit_tree_probe(lab, opts), case="commit-tree " + " ".join(opts)))
    tag_cases = [
        ["--sign", "-m", "t", "v1"],
        ["--si", "-m", "t", "v1"],
        ["--sig", "-m", "t", "v1"],
        ["--si=", "-m", "t", "v1"],
        ["--local-user", "KEY", "-m", "t", "v1"],
        ["--lo", "KEY", "-m", "t", "v1"],
        ["--loc", "KEY", "-m", "t", "v1"],
        ["--local-u", "KEY", "-m", "t", "v1"],
        ["--lo=KEY", "-m", "t", "v1"],
        ["--s", "-m", "t", "v1"],
        ["--l", "-m", "t", "v1"],
        ["--so", "creator", "v1"],
        ["--sort=refname"],
        ["--no-sign", "-m", "t", "v1"],
        ["--signoff", "-m", "t", "v1"],
        ["-a", "v1", "-m", "x"],
    ]
    for opts in tag_cases:
        results.append(dict(git_tag_probe(lab, opts), case="tag " + " ".join(opts)))
    for sub in ("rebase", "cherry-pick", "am", "revert"):
        results.append(dict(git_skip_probe(lab, sub), case=sub + " --skip"))
    push_cases = [
        ["--si"], ["--sig"], ["--sign"], ["--signe"], ["--signed"], ["--sign=true"], ["--signed=true"], ["--signed=1"],
        ["--signed=yes"], ["--signed=on"], ["--signed=YES"], ["--si=if-asked"], ["--signed=if-asked"], ["--signed="],
        ["--si="], ["--signed=00"], ["--signed=falsehood"], ["--s"], ["--se"], ["--set-upstream"], ["--si=false"],
        ["--si=0"], ["--si=no"], ["--si=off"], ["--signed=false"], ["--signed=FALSE"], ["--signed=No"], ["--signed=off"],
        ["--signed=0"], ["--no-signed"], ["--no-si"], ["--no-sig"], ["--signoff"], ["--SIGNED"], ["--Si"],
    ]
    for opts in push_cases:
        results.append(dict(git_push_probe(lab, opts), case="push " + " ".join(opts)))
    return results


def gpg_probes(root: Path) -> list:
    home = root / "gnupg"
    home.mkdir(mode=0o700)
    env = {k: v for k, v in os.environ.items() if k not in ("GNUPGHOME", "GPG_AGENT_INFO", "GPG_TTY")}
    env.update({"GNUPGHOME": str(home), "LC_ALL": "C"})
    base = ["gpg", "--homedir", str(home), "--batch", "--no-tty", "--no-options", "--no-autostart", "--agent-program", "/bin/false", "--dirmngr-program", "/bin/false", "--no-permission-warning"]
    dump = run(base + ["--dump-options"], root, env)
    # warm-up: the first command creates the keybox and says so, which would spoil the stderr comparisons
    run(base + ["--list-keys"], root, env)
    options = sorted({line.strip()[2:] for line in dump.stdout.splitlines() if line.startswith("--")})
    (root / "gpg_dump_options.txt").write_text("\n".join(options) + "\n", encoding="utf-8")
    cases = [
        # every first letter of a denied option (sign, clear-sign, card-*, change-*, detach-sign, decrypt*,
        # lsign-key, list-secret-keys, quick-*sign-key, passwd, edit-card, export-secret-*)
        ["--s"], ["--c"], ["--d"], ["--l"], ["--q"], ["--p"], ["--e"],
        # the prefixes #2493 says GnuPG 2.4 runs, and their full spellings
        ["--cl"], ["--cle"], ["--clea"], ["--clear-sign"], ["--clearsign"],
        ["--ls", "PROBEKEY"], ["--lsi", "PROBEKEY"], ["--lsign-key", "PROBEKEY"],
        ["--det"], ["--deta"], ["--detach-sign"],
        ["--si"], ["--sig"], ["--sign"],
        ["--de"], ["--dec"], ["--decrypt"],
        # #2485's floor and export cases
        ["--li"], ["--lis"], ["--list"], ["--LIST"], ["--list-k"], ["--list-keys"],
        ["--ex"], ["--exp"], ["--expo"], ["--expor"], ["--export"], ["--export-s"],
    ]
    results = []
    reference = {}
    for args in cases:
        cp = run(base + args, root, env, timeout=20)
        err = cp.stderr.strip()
        lowered = err.casefold()
        if "is ambiguous" in lowered:
            parse = "ambiguous"
        elif "invalid option" in lowered:
            parse = "invalid"
        else:
            parse = "ran"
        name = args[0][2:]
        matches = [opt for opt in options if opt.startswith(name)]
        record = {"argv": args, "rc": cp.returncode, "parse": parse, "stderr_head": err.splitlines()[:3], "dump_options_matching_prefix": matches[:12], "dump_match_count": len(matches)}
        results.append(record)
        reference[" ".join(args)] = err
    for prefix, full in (("--cl", "--clear-sign"), ("--cle", "--clear-sign"), ("--ls PROBEKEY", "--lsign-key PROBEKEY"), ("--lsi PROBEKEY", "--lsign-key PROBEKEY"), ("--det", "--detach-sign"), ("--si", "--sign"), ("--sig", "--sign")):
        results.append({"same_stderr_as_full_spelling": [prefix, full], "identical": reference.get(prefix) == reference.get(full)})
    return results


def main(argv: list) -> int:
    out = Path(argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    root = out / "probe-root"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    git_version = run(["git", "--version"], out, dict(os.environ)).stdout.strip()
    gpg_version = run(["gpg", "--version"], out, dict(os.environ)).stdout.splitlines()[0]
    git_results = git_probes(root / "git")
    gpg_results = gpg_probes(root)
    (out / "git_probe.json").write_text(json.dumps({"git_version": git_version, "results": git_results}, indent=2) + "\n", encoding="utf-8")
    (out / "gpg_probe.json").write_text(json.dumps({"gpg_version": gpg_version, "results": gpg_results}, indent=2) + "\n", encoding="utf-8")
    lines = [git_version, gpg_version, ""]
    for r in git_results:
        extra = r.get("push_cert_mode", "")
        lines.append("%-40s rc=%-3s parse=%-9s signer_called=%-5s %s | %s" % (r["case"], r["rc"], r["parse"], r["signing_program_called"], extra, (r["stderr_head"] or [""])[0][:110]))
    lines.append("")
    for r in gpg_results:
        if "argv" in r:
            lines.append("gpg %-22s rc=%-3s parse=%-9s dump_matches=%-3s %s" % (" ".join(r["argv"]), r["rc"], r["parse"], r["dump_match_count"], (r["stderr_head"] or [""])[0][:110]))
        else:
            lines.append("same stderr %s vs %s: %s" % (r["same_stderr_as_full_spelling"][0], r["same_stderr_as_full_spelling"][1], r["identical"]))
    (out / "probe_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
