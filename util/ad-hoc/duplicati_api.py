#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License

Minimal authenticated client for the local Duplicati web-service API.

Duplicati issues short-lived access tokens, so a long operational session
loses its token repeatedly; this re-authenticates on demand rather than making
the caller handle 401s.  The web-UI password is read in-process from the 0600
credential file that util/ad-hoc/yamaguchi_server_api.py also reads -- through
the same function, read_credential() there, whose docstring is the file's
contract -- and is never passed on a command line (it would be visible in
``ps``), never placed in the environment, and never printed.

Deliberately has no write helpers beyond ``call()`` -- the destructive verbs on
this API (Repair, purge-broken-files, destination operations) must stay explicit
at the call site, not be wrapped in convenience functions.  It also has no
job-scoped verbs: the job id is part of the endpoint the caller types
(``backup/<id>/log``), so there is no default id to get wrong.

Usage
-----
    python3 util/ad-hoc/duplicati_api.py GET  serverstate
    python3 util/ad-hoc/duplicati_api.py POST task/7/abort

Environment
-----------
    DUPLICATI_URL                   default http://127.0.0.1:8300
    DUPLICATI_WEB_CREDENTIAL_FILE   default ~/.config/duplicati-backup/web-credential
                                    (the WEB-UI password, not the archive passphrase)

``DUPLICATI_PW_FILE`` and ``DUPLICATI_PW_KEY`` are NO LONGER READ (B2 of the
2026-10-03 recovery plan).  They pointed this client at the primary checkout's
world-readable ``.env`` (exposure S-5), and ``DUPLICATI_PW_FILE`` also names the
ARCHIVE passphrase file in ``duplicati_purge_dryrun.bash`` -- one variable for two
different secrets.  A set value is reported once on stderr and ignored.  The old
bare-secret fallback, which posted the whole file as the password when no key
matched, went with them.

TWO DIFFERENT SECRETS -- do not conflate them:
  * the **web-UI password** (used by duplicati_api.py to authenticate to :8300)
  * the **archive GPG passphrase** (used to decrypt volumes; restores, purges,
    passphrase verification)
They were the same value once and are not any more. Pointing an archive-passphrase
consumer at the UI-password file fails as "Bad session key", which reads like a
corrupt archive rather than the wrong secret.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yamaguchi_server_api import CRED_FILE_ENV, credential_path, read_credential  # noqa: E402 -- sibling module; path fixed one line above

BASE = os.environ.get("DUPLICATI_URL", "http://127.0.0.1:8300").rstrip("/")
# Read before B2 and ignored since; see the module docstring.
RETIRED_ENV = ("DUPLICATI_PW_FILE", "DUPLICATI_PW_KEY")
_retired_noted = False


def _password() -> str:
    """The WEB-UI password, from the one credential file both API clients read."""
    global _retired_noted
    if not _retired_noted:
        _retired_noted = True
        for name in RETIRED_ENV:
            if os.environ.get(name):
                print(f"note: {name} is set but no longer read; the web-UI password comes from {credential_path()} ({CRED_FILE_ENV} overrides)", file=sys.stderr)
    return read_credential()


def login() -> str:
    body = json.dumps({"Password": _password()}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["AccessToken"]


def call(endpoint: str, method: str = "GET", payload=None, token: str | None = None):
    """Call the API, re-authenticating once on 401. Returns (status, parsed_or_text)."""
    tok = token or login()
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": "Bearer " + tok}
    if data is not None:
        headers["Content-Type"] = "application/json"

    def _do(t):
        h = dict(headers)
        h["Authorization"] = "Bearer " + t
        req = urllib.request.Request(
            f"{BASE}/api/v1/{endpoint.lstrip('/')}", data=data, method=method, headers=h)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return resp.status, raw.decode(errors="replace")

    try:
        return _do(tok)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return _do(login())
        detail = ""
        try:
            detail = exc.read().decode(errors="replace")[:400]
        except Exception:  # nosec B110
            # Best-effort enrichment only. The HTTP status in exc.code is the
            # actual result and is returned either way; a body that is absent,
            # already consumed, or undecodable must not mask it by raising a
            # second exception from the error path.
            detail = "<error body unavailable>"
        return exc.code, detail


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    method, endpoint = argv[1].upper(), argv[2]
    payload = json.loads(argv[3]) if len(argv) > 3 else None
    status, body = call(endpoint, method, payload)
    print(f"[{status}]")
    print(json.dumps(body, indent=1) if not isinstance(body, str) else body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
