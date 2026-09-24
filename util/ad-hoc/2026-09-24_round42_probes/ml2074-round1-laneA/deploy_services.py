#!/usr/bin/env python3
"""Lane A: parse juniper-deploy docker-compose.yml at origin/main and print the canopy services'
environment, secrets and backend-mode-relevant keys (read via git show; nothing written to the repo)."""
import regex as re
import subprocess
import yaml


_TOKEN_PATTERNS = [re.compile(r"hf_[A-Za-z0-9]{20,}"), re.compile(r"pypi-[A-Za-z0-9_\-]{20,}"), re.compile(r"(?i)(x-api-key['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+")] # E: line too long (160 > 79 characters)


def redact(text: str) -> str:
    for pat in _TOKEN_PATTERNS:
        text = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "<redacted>", text)
    return text


D = "/home/pcalnon/Development/python/Juniper/juniper-deploy"
src = subprocess.run(["git", "-C", D, "show", "origin/main:docker-compose.yml"], capture_output=True, text=True, check=True).stdout
doc = yaml.safe_load(src)
for name, svc in doc["services"].items():
    if "canopy" not in name:
        continue
    env = svc.get("environment", {})
    if isinstance(env, list):
        env = dict(e.split("=", 1) if "=" in e else (e, None) for e in env)
    keys = {k: v for k, v in env.items() if any(t in k for t in ("API_KEY", "DEMO", "BACKEND", "REQUIRE_AUTH", "AUTH", "MODE"))}
    print(f"== {name} profiles={svc.get('profiles')} secrets={redact(svc.get('secrets'))} env_file={svc.get('env_file')}")
    print(f"   command={svc.get('command')} entrypoint={svc.get('entrypoint')}")
    for k, v in keys.items():
        print(f"   {k}={v}")
