#!/usr/bin/env python3
"""
Paginated, read-only state probe of the nine public Juniper repositories, for re-baselining the consolidated plan.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2-REBASELINE.md

Why this exists beside ``util/ad-hoc/2026-10-05_ecosystem_live_census.py``: that census reads one page of 50 commits
per repository and says so when the page is full. Over the month since the plan's final census (2026-10-10T21:30Z)
two repositories fill that page, so a re-baseline needs every page. This probe pages through, and adds what a
re-baseline asks beyond a census: every Release and PyPI upload in the window, how far each ``main`` is past its
newest Release, each repository's gitleaks config, and GitHub's own secret-scanning settings.

Read-only: GitHub REST GETs through ``gh api`` and the PyPI JSON API. No GraphQL (its quota is shared), no write, no
git command. It prints counts, names, versions, times and titles of PUBLIC repositories only. juniper-harcot and
juniper-k8s are private and are deliberately absent, so nothing of theirs can reach a public file.

It fails closed, as the census does: a read that fails prints UNREADABLE, never "0" or "none", and the exit status is
then 3. A paged read stops only on a short page or on ``MAX_PAGES``, and hitting the cap is reported as a failure.

Usage
-----
    python3 -B util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py --since 2026-10-10T21:30:00Z
    python3 -B util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py --since 2026-10-10T21:30:00Z --list-merges
    python3 -B util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py --self-test
"""
import argparse
import base64
import collections
import datetime
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "pcalnon"
REPOS = ["juniper-ml", "juniper-data", "juniper-data-client", "juniper-cascor", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy", "juniper-deploy", "juniper-recurrence"]
PACKAGES = [
    "juniper-ml",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-cascor-model",
    "juniper-canopy",
    "juniper-recurrence",
    "juniper-recurrence-model",
    "juniper-recurrence-client",
    "juniper-observability",
    "juniper-service-core",
    "juniper-ci-tools",
    "juniper-config-tools",
    "juniper-doc-tools",
    "juniper-model-core",
]
PER_PAGE = 100
MAX_PAGES = 30
BOT_SUFFIX = "[bot]"
GITLEAKS_PATHS = [".gitleaks.toml", ".github/.gitleaks.toml"]
SECTIONS = ["prs", "merges", "releases", "pypi", "gitleaks", "wiring", "settings"]

FAILED = []


def gh(path):
    """GET one GitHub REST path. Return (status, body): status is 'ok', 'absent' (HTTP 404) or 'failed'."""
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode == 0:
        try:
            return "ok", json.loads(out.stdout)
        except json.JSONDecodeError:
            return "failed", None
    if "HTTP 404" in out.stderr:
        return "absent", None
    return "failed", None


def gh_ok(path):
    """GET a path that must exist. On any other answer, record the failure and return None."""
    status, body = gh(path)
    if status != "ok":
        FAILED.append(path)
        return None
    return body


def gh_paged(path):
    """GET every page of a list endpoint. Return the whole list, or None if a page failed or the cap was reached."""
    sep = "&" if "?" in path else "?"
    items = []
    for page in range(1, MAX_PAGES + 1):
        chunk = gh_ok(f"{path}{sep}per_page={PER_PAGE}&page={page}")
        if chunk is None:
            return None
        items.extend(chunk)
        if len(chunk) < PER_PAGE:
            return items
    FAILED.append(f"{path} (more than {MAX_PAGES} pages)")
    return None


def parse_since(text):
    """Return the time as a UTC 'Z' string, or None. GitHub reads a malformed ``since`` as "no commits"."""
    try:
        when = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None or "T" not in text:
        return None
    if when > datetime.datetime.now(datetime.timezone.utc):
        return None
    return when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def first_line(message, width=110):
    """The first line of a commit message, cut to ``width``."""
    lines = message.splitlines()
    return lines[0][:width] if lines else ""


def is_bot_commit(commit):
    """True when GitHub attributes the commit's author to a bot account."""
    author = commit.get("author") or {}
    return str(author.get("login", "")).endswith(BOT_SUFFIX)


def summarize_gitleaks(text):
    """Count what decides whether a gitleaks config finds anything: its own rules, and whether it extends the defaults."""
    rules = len(re.findall(r"(?m)^\s*\[\[rules\]\]", text))
    extends = len(re.findall(r"(?m)^\s*\[extend\]", text))
    use_default = bool(re.search(r"(?m)^\s*useDefault\s*=\s*true\b", text))
    return {"rules": rules, "extend": extends, "use_default": use_default, "effective": bool(rules or use_default)}


def probe_open_prs():
    print("== open PRs (author / draft counts; every non-bot PR listed)")
    for repo in REPOS:
        prs = gh_paged(f"repos/{OWNER}/{repo}/pulls?state=open")
        if prs is None:
            print(f"{repo}: UNREADABLE")
            continue
        by = collections.Counter((p["user"]["login"], bool(p["draft"])) for p in prs)
        # "/draft", not "(draft)": after a bot login's "[bot]" a parenthesis reads as a markdown link to the doc-link hook
        parts = ", ".join(f"{user}{'/draft' if draft else ''}={n}" for (user, draft), n in sorted(by.items()))
        off_main = sorted(p["number"] for p in prs if p["base"]["ref"] != "main")
        armed = sorted(p["number"] for p in prs if p.get("auto_merge"))
        print(f"{repo}: {len(prs)} open; {parts or '-'}; base not main: {off_main}; auto-merge armed: {armed}")
        for p in prs:
            if not p["user"]["login"].endswith(BOT_SUFFIX):
                print(f"     #{p['number']} {'draft ' if p['draft'] else ''}{p['title'][:90]}")


def probe_merges(since, list_merges):
    print(f"== commits on main since {since} (every page)")
    total = 0
    for repo in REPOS:
        commits = gh_paged(f"repos/{OWNER}/{repo}/commits?sha=main&since={since}")
        if commits is None:
            print(f"{repo}: UNREADABLE")
            continue
        bots = sum(1 for c in commits if is_bot_commit(c))
        total += len(commits)
        newest = commits[0]["commit"]["committer"]["date"] if commits else "-"
        print(f"{repo}: {len(commits)} commits ({bots} by a bot account, {len(commits) - bots} other); newest {newest}")
        if list_merges:
            for c in commits:
                print(f"     {c['sha'][:8]} {c['commit']['committer']['date']} {first_line(c['commit']['message'])}")
    print(f"all nine: {total} commits")


def probe_releases(since):
    print(f"== GitHub Releases published since {since}, and how far main is past the newest Release")
    for repo in REPOS:
        rels = gh_paged(f"repos/{OWNER}/{repo}/releases")
        if rels is None:
            print(f"{repo}: UNREADABLE")
            continue
        live = [r for r in rels if not r["draft"] and r.get("published_at")]
        live.sort(key=lambda r: r["published_at"], reverse=True)
        window = [r for r in live if r["published_at"] >= since]
        newest = live[0] if live else None
        ahead = "-"
        if newest is not None:
            cmp_body = gh_ok(f"repos/{OWNER}/{repo}/compare/{newest['tag_name']}...main")
            ahead = "UNREADABLE" if cmp_body is None else str(cmp_body["ahead_by"])
        head = f"{newest['tag_name']} {newest['published_at']}" if newest else "none"
        print(f"{repo}: {len(window)} in the window; newest {head}; main is {ahead} commits past it")
        for r in window:
            print(f"     {r['published_at']} {r['tag_name']}")


def probe_pypi(since):
    print(f"== PyPI: newest version, and every version uploaded since {since}")
    for pkg in PACKAGES:
        try:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json", timeout=20) as fh:
                doc = json.load(fh)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            FAILED.append(f"pypi:{pkg}")
            print(f"{pkg}: UNREADABLE ({type(exc).__name__})")
            continue
        version = doc["info"]["version"]
        uploads = {}
        for ver, files in doc["releases"].items():
            times = [f["upload_time_iso_8601"] for f in files]
            if times:
                uploads[ver] = min(times)
        window = sorted((when, ver) for ver, when in uploads.items() if when >= since)
        listed = ", ".join(f"{ver} ({when[:16]}Z)" for when, ver in window) or "none"
        print(f"{pkg}: newest {version} ({uploads.get(version, '?')[:16]}Z); in the window: {listed}")


def probe_gitleaks():
    print("== gitleaks config on main (0 rules and no useDefault finds nothing)")
    for repo in REPOS:
        found = False
        for path in GITLEAKS_PATHS:
            status, body = gh(f"repos/{OWNER}/{repo}/contents/{path}?ref=main")
            if status == "absent":
                continue
            if status != "ok":
                FAILED.append(f"{repo}:{path}")
                print(f"{repo}: UNREADABLE ({path})")
                found = True
                break
            text = base64.b64decode(body["content"]).decode("utf-8", errors="replace")
            s = summarize_gitleaks(text)
            verdict = "finds" if s["effective"] else "FINDS NOTHING"
            print(f"{repo}: {path}: [[rules]]={s['rules']} [extend]={s['extend']} useDefault={s['use_default']} -> {verdict}")
            found = True
            break
        if not found:
            print(f"{repo}: no gitleaks config at {' or '.join(GITLEAKS_PATHS)} (the tool's defaults apply where it runs)")


def mentions_gitleaks(text):
    """True when a workflow or hook file names gitleaks outside a comment line."""
    return any("gitleaks" in line.lower() for line in text.splitlines() if not line.lstrip().startswith("#"))


def read_text(repo, path):
    """Return (status, text) for one file on main: status is 'ok', 'absent' or 'failed'."""
    status, body = gh(f"repos/{OWNER}/{repo}/contents/{path}?ref=main")
    if status != "ok":
        return status, ""
    if isinstance(body, list) or body.get("encoding") != "base64":
        return "failed", ""
    return "ok", base64.b64decode(body["content"]).decode("utf-8", errors="replace")


def probe_gitleaks_wiring():
    print("== where gitleaks runs: workflows and the pre-commit config on main that name it (comment lines ignored)")
    for repo in REPOS:
        status, listing = gh(f"repos/{OWNER}/{repo}/contents/.github/workflows?ref=main")
        if status != "ok" or not isinstance(listing, list):
            FAILED.append(f"{repo}:.github/workflows")
            print(f"{repo}: UNREADABLE (.github/workflows)")
            continue
        names = sorted(e["name"] for e in listing if e["type"] == "file" and e["name"].endswith((".yml", ".yaml")))
        hits = []
        unreadable = False
        for name in names:
            st, text = read_text(repo, f".github/workflows/{name}")
            if st != "ok":
                FAILED.append(f"{repo}:.github/workflows/{name}")
                unreadable = True
                continue
            if mentions_gitleaks(text):
                hits.append(name)
        st, text = read_text(repo, ".pre-commit-config.yaml")
        if st == "ok":
            hook = "yes" if mentions_gitleaks(text) else "no"
        elif st == "absent":
            hook = "no pre-commit config"
        else:
            FAILED.append(f"{repo}:.pre-commit-config.yaml")
            hook = "UNREADABLE"
        flag = " (some workflow UNREADABLE)" if unreadable else ""
        print(f"{repo}: {len(names)} workflows; naming gitleaks: {hits or 'none'}{flag}; pre-commit names it: {hook}")


def probe_security_settings():
    print("== GitHub secret scanning settings (security_and_analysis; absent keys print as '-')")
    keys = ["secret_scanning", "secret_scanning_push_protection", "secret_scanning_non_provider_patterns", "secret_scanning_validity_checks", "dependabot_security_updates"]
    for repo in REPOS:
        body = gh_ok(f"repos/{OWNER}/{repo}")
        if body is None:
            print(f"{repo}: UNREADABLE")
            continue
        sa = body.get("security_and_analysis")
        if sa is None:
            FAILED.append(f"{repo}:security_and_analysis")
            print(f"{repo}: visibility={body.get('visibility')}; security_and_analysis not returned (the token cannot read it): UNREADABLE")
            continue
        parts = ", ".join(f"{k}={(sa.get(k) or {}).get('status', '-')}" for k in keys)
        print(f"{repo}: visibility={body.get('visibility')}; {parts}")


def self_test():
    """Check the pure functions on fixed inputs: the config verdicts, the time parser and the bot test."""
    cases = [
        ("", {"rules": 0, "extend": 0, "use_default": False, "effective": False}),
        ('title = "x"\n[allowlist]\npaths = []\n', {"rules": 0, "extend": 0, "use_default": False, "effective": False}),
        ("[extend]\nuseDefault = true\n", {"rules": 0, "extend": 1, "use_default": True, "effective": True}),
        ("[extend]\nuseDefault = false\n", {"rules": 0, "extend": 1, "use_default": False, "effective": False}),
        ('[[rules]]\nid = "a"\n  [[rules]]\nid = "b"\n', {"rules": 2, "extend": 0, "use_default": False, "effective": True}),
        ("# [[rules]]\n# useDefault = true\n", {"rules": 0, "extend": 0, "use_default": False, "effective": False}),
    ]
    bad = [(text, summarize_gitleaks(text)) for text, want in cases if summarize_gitleaks(text) != want]
    times = [("2026-10-10T21:30:00Z", "2026-10-10T21:30:00Z"), ("2026-10-10T16:30:00-05:00", "2026-10-10T21:30:00Z"), ("2026-10-10", None), ("2026-10-10T21:30:00", None), ("nonsense", None), ("2999-01-01T00:00:00Z", None)]
    bad += [(text, parse_since(text)) for text, want in times if parse_since(text) != want]
    bots = [({"author": {"login": "dependabot[bot]"}}, True), ({"author": {"login": "pcalnon"}}, False), ({"author": None}, False), ({}, False)]
    bad += [(c, is_bot_commit(c)) for c, want in bots if is_bot_commit(c) != want]
    if first_line("") != "" or first_line("a\nb") != "a" or first_line("x" * 200, 10) != "x" * 10:
        bad.append(("first_line", None))
    names = [("      - uses: gitleaks/gitleaks-action@v3\n", True), ("# gitleaks is not run here\n", False), ("  # gitleaks\nrun: echo\n", False), ("id: GitLeaks\n", True), ("", False)]
    bad += [(text, mentions_gitleaks(text)) for text, want in names if mentions_gitleaks(text) != want]
    total = len(cases) + len(times) + len(bots) + 3 + len(names)
    for item in bad:
        print("SELF-TEST FAIL:", item)
    print(f"self-test: {total - len(bad)} of {total} pass")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--since", help="an ISO 8601 time with a zone, such as 2026-10-10T21:30:00Z")
    ap.add_argument("--list-merges", action="store_true", help="print every commit in the window, not only the counts")
    ap.add_argument("--self-test", action="store_true", help="check the pure functions and exit")
    ap.add_argument("--only", choices=sorted(SECTIONS), action="append", help="run only this section (repeatable); the default is every section")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    since = parse_since(args.since or "")
    if since is None:
        print(f"--since {args.since!r}: not a past ISO 8601 time with a zone; nothing was read", file=sys.stderr)
        return 3
    wanted = args.only or list(SECTIONS)
    print(f"probe run at {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}; window starts {since}; sections: {', '.join(s for s in SECTIONS if s in wanted)}")
    for name in SECTIONS:
        if name not in wanted:
            continue
        if name == "prs":
            probe_open_prs()
        elif name == "merges":
            probe_merges(since, args.list_merges)
        elif name == "releases":
            probe_releases(since)
        elif name == "pypi":
            probe_pypi(since)
        elif name == "gitleaks":
            probe_gitleaks()
        elif name == "wiring":
            probe_gitleaks_wiring()
        elif name == "settings":
            probe_security_settings()
    if FAILED:
        print(f"INCOMPLETE: {len(FAILED)} read(s) failed: {FAILED}; a failed read is not '0' or 'none'", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
