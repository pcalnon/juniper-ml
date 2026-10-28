#!/usr/bin/env python3
"""
Probe a PUBLISHED juniper-recurrence-client wheel for 0.3.1's fix: ``crossval`` no longer sends ``embargo: 0``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-27
Status: ad-hoc — one-off (post-publication check of juniper-recurrence-client 0.3.1)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/releases/RELEASE_NOTES_juniper-recurrence-client_v0.3.1.md (the fix this checks);
         notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W5.2 made one look-back per entity the service's default embargo; v1.7.23 records this probe);
         util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py (the pattern this follows)

Why this exists
---------------
Up to 0.3.0, ``JuniperRecurrenceClient.crossval`` defaulted ``embargo`` to ``0`` and always sent it.
juniper-recurrence 0.8.0's ``POST /v1/crossval`` honours an explicit value, so every caller who did not
pass ``embargo`` ran with no embargo, the leakage W5.2's default exists to prevent. 0.3.1 defaults it to
``None`` and sends it only when given. A checkout is not a deployment, so this reads nothing from a git
tree: it refuses to run unless ``juniper_recurrence_client`` was imported from an installed,
non-editable distribution of exactly the version asked for.

The probe points the installed client at a stub HTTP server on 127.0.0.1 (an ephemeral port), which
records every request body and answers 200 with an empty ``CrossValResponse``. No real service, key
or dataset is involved; ``JUNIPER_RECURRENCE_API_KEY`` and its ``_FILE`` form are removed from this
process's environment first, so the client sends no key.

1. ``crossval`` called without ``embargo`` sends a body with no ``embargo`` key;
2. ``embargo=0`` is still sent, as 0 (an explicitly unembargoed run stays possible);
3. ``embargo=7`` is sent as 7;
4. the signature's default for ``embargo`` is ``None``.

Run it against a fresh venv per version. The 0.3.0 run is the control: it must FAIL at check 1,
because 0.3.0 sends ``embargo: 0`` on every call.

    python3 -m venv <scratch>/rc031
    <scratch>/rc031/bin/pip install --no-cache-dir --ignore-installed --only-binary=:all: 'juniper-recurrence-client==0.3.1'
    <scratch>/rc031/bin/python -I util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py --expect-version 0.3.1

Exit status: 0 when every check passes, 1 when any check fails (check 1 stops the run; checks 2-4 are all reported),
2 on a provenance refusal.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CROSSVAL_PATH = "/v1/crossval"
EMPTY_CROSSVAL_RESPONSE = {"folds": [], "eval_aggregate": {}, "eval_std": {}}
PROBE_DATASET_ID = "ds-embargo-probe"


class RecordingHandler(BaseHTTPRequestHandler):
    """Record each POST's path and JSON body on the server; answer 200 with an empty CrossValResponse."""

    def do_POST(self) -> None:  # noqa: N802 - the http.server hook name
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self.server.records.append((self.path, json.loads(raw) if raw else None))
        payload = json.dumps(EMPTY_CROSSVAL_RESPONSE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - the http.server signature
        pass


def check_provenance(expect_version: str) -> None:
    """Refuse unless juniper_recurrence_client comes from an installed, non-editable wheel of that version."""
    import juniper_recurrence_client

    dist = importlib.metadata.distribution("juniper-recurrence-client")
    module_path = Path(juniper_recurrence_client.__file__).resolve()
    site_dirs = [Path(p).resolve() for p in sys.path if p.endswith("site-packages")]
    direct_url = dist.read_text("direct_url.json")
    print(f"  juniper-recurrence-client {dist.version} (__version__ {juniper_recurrence_client.__version__}) from {module_path}")
    if dist.version != expect_version or juniper_recurrence_client.__version__ != expect_version:
        print(f"REFUSED: installed juniper-recurrence-client is {dist.version} / {juniper_recurrence_client.__version__}, not {expect_version}")
        sys.exit(2)
    if not any(site in module_path.parents for site in site_dirs):
        print(f"REFUSED: juniper_recurrence_client imported from {module_path}, outside every site-packages on sys.path")
        sys.exit(2)
    if direct_url is not None:
        print(f"REFUSED: juniper-recurrence-client was installed from a URL or path, not an index: {json.loads(direct_url)}")
        sys.exit(2)
    print("  OK: an index-installed wheel, not a checkout")


def sent_body(client: object, server: HTTPServer, **kwargs: object) -> dict:
    """Call crossval once and return the JSON body the stub received for it."""
    before = len(server.records)
    client.crossval(n_folds=3, dataset_id=PROBE_DATASET_ID, **kwargs)
    new = server.records[before:]
    if len(new) != 1 or new[0][0] != CROSSVAL_PATH:
        raise SystemExit(f"FAIL: expected one POST {CROSSVAL_PATH}, got {new!r}")
    return new[0][1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect-version", required=True, help="the juniper-recurrence-client version the venv must hold")
    args = ap.parse_args()

    for name in ("JUNIPER_RECURRENCE_API_KEY", "JUNIPER_RECURRENCE_API_KEY_FILE"):
        os.environ.pop(name, None)
    check_provenance(args.expect_version)
    from juniper_recurrence_client import JuniperRecurrenceClient

    server = HTTPServer(("127.0.0.1", 0), RecordingHandler)
    server.records = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client = JuniperRecurrenceClient(base_url=f"http://127.0.0.1:{server.server_address[1]}", retries=0)
    failures = 0
    try:
        body = sent_body(client, server)
        print(f"  1. no embargo passed -> body keys {sorted(body)}")
        if "embargo" in body:
            print(f"FAIL 1: the body carries embargo={body['embargo']!r}; the service's look-back default never applies")
            return 1
        print("  OK 1: no embargo key, so the service picks its default")

        body = sent_body(client, server, embargo=0)
        print(f"  2. embargo=0 -> body embargo {body.get('embargo', '<absent>')!r}")
        if "embargo" not in body or body["embargo"] != 0:
            print("FAIL 2: an explicit embargo=0 was not sent as 0")
            failures += 1

        body = sent_body(client, server, embargo=7)
        print(f"  3. embargo=7 -> body embargo {body.get('embargo', '<absent>')!r}")
        if body.get("embargo") != 7:
            print("FAIL 3: an explicit embargo=7 was not sent as 7")
            failures += 1

        default = inspect.signature(JuniperRecurrenceClient.crossval).parameters["embargo"].default
        print(f"  4. signature default for embargo: {default!r}")
        if default is not None:
            print("FAIL 4: the signature's embargo default is not None")
            failures += 1
    finally:
        server.shutdown()
        server.server_close()

    print("PASS: every check passed" if not failures else f"FAIL: {failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
