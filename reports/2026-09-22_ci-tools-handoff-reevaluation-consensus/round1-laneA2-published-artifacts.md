<!-- markdownlint-disable -->
# Round 1, lane A2

**Entry point:** published artifacts: PyPI, GHCR and the images.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T19:54:56Z to 2026-09-22T20:13:52Z, read-only. Agent `agent-a5d09c52db51477c5`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are Lane A2 (measurement re-creation) in an independent-agent consensus review. Your entry point is the PUBLISHED ARTIFACTS: PyPI's JSON API and wheel files, GHCR's registry API (anonymous token: `https://ghcr.io/token?scope=repository:pcalnon/<image>:pull&service=ghcr.io`, then `/v2/pcalnon/<image>/tags/list` and `/manifests/<tag>` with an OCI index Accept header), and pulled container images. Do NOT trust prose or PR bodies; re-derive every value from the artifacts. "UNTRACEABLE"/"NO ARTIFACT" are allowed answers. Default to REFUTED/UNTRACEABLE when you cannot re-derive.

READ-ONLY RULES (hard): do not edit/create/delete files in any repo; do not commit, push, comment, merge, close, approve anything. Worktree-isolated harness: do NOT run `git` against any repo; use `gh api`, `curl`, `python3`, `docker pull`, and `docker run --rm --entrypoint python <image> -c "..."` (the harness refuses `sh -c` and refuses shell loops over variables touching gh/git — write plain commands, or put logic inside one `python3 -c`/heredoc-free script file). If you run a container that listens on a port, bind to 127.0.0.1 on a port above 18000, give it a unique --name containing "lane-a2", and STOP it when done. Downloads go under /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a2/ (create it). Pull an image fully BEFORE measuring inside it, and never fold docker's stderr into a count.

ARTIFACTS UNDER REVIEW:
(a) juniper-deploy PR #227 (`gh pr view 227 --repo pcalnon/juniper-deploy`, `gh pr diff 227 --repo pcalnon/juniper-deploy`) — pins ghcr.io/pcalnon/juniper-data 0.14.0 -> 0.15.0 and adds CHANGELOG text. Verify every factual claim in its PR body and CHANGELOG diff: 0.15.0 manifest is an OCI index with linux/amd64 + linux/arm64 + two attestation manifests (digest sha256:2da73f06bbd3...); image label org.opencontainers.image.version 0.15.0 and revision 46894ba1 (the v0.15.0 tag commit — check the tag via `gh api repos/pcalnon/juniper-data/git/refs/tags/v0.15.0`); inside the image juniper_data.__version__ == importlib.metadata.version == 0.15.0; `GET /v1/health` answers 200 with version 0.15.0 when the default CMD runs; NO site-packages/juniper_data/tests/ in the image; the equities/equities_seq generator VERSION is 3.0.0 in the 0.14.0 image and 5.0.0 in the 0.15.0 image; the 0.15.0 WHEEL on PyPI carries 97 test members of 201; PyPI serves 0.15.0; `scripts/verify_published_images.py` (fetch it from the PR branch `chore/pin-juniper-data-0.15.0` via the contents API, with the PR's docker-compose.yml, into your scratch dir, and run it there) reports data as current and exits 0 with --fail-on-stale.
(b) In the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl, the new "## Status banner (added 2026-09-22 ...)" section of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` (read-only; `git diff` there shows the change). Verify its artifact claims: GHCR release tags for juniper-cascor (0.11.0), juniper-data (0.14.0, 0.15.0), juniper-canopy (0.8.0, 0.8.1), juniper-cascor-worker (0.6.0), juniper-recurrence (0.5.0); worker image 0.6.0 carries torch 2.14.0+cpu; inside ghcr.io/pcalnon/juniper-cascor-worker:0.6.0, `juniper_cascor_worker.__version__` is 0.4.0 while metadata says 0.6.0; PyPI dates (worker 0.6.0 on PyPI 2026-09-18; data 0.15.0).
(c) Instrument adequacy: for each check, state whether it could have produced a different answer (e.g. a tests-absent probe that looks in the wrong directory passes vacuously — where does this image install juniper_data?).

OUTPUT (final message only is returned): numbered findings — quoted claim, verdict (CONFIRMED / REFUTED / PARTIAL / UNTRACEABLE), severity (CRITICAL/MAJOR/MINOR/NONE), evidence (command + short output). Then an overall verdict (PASS / PASS WITH FINDINGS / FAIL). Terse, no preamble.

## Final report

**Lane A2: measurements re-created from the published artifacts**

Scratch instruments (`ghcr_probe.py`, `layer_scan.py`) and all downloads are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/a2/`. Every `lane-a2` container was stopped and removed. The images were already on this machine (each pull said "up to date", with the same digest).

### (a) juniper-deploy PR #227 (branch head `d1bb95df`, which is the PR's headRefOid)

1. **"0.15.0 manifest is an OCI index with amd64 + arm64 + two attestation manifests (sha256:2da73f06bbd3…), same shape as 0.14.0"** — CONFIRMED, NONE.
   - Registry query returns `oci.image.index.v1+json`, digest `2da73f06bbd36538c586…3e972`.
   - Children: linux/amd64, linux/arm64, and two unknown/unknown manifests tagged `attestation-manifest`. 0.14.0 (`315f4f06`) has the same shape.

2. **"Label version 0.15.0, revision 46894ba1 = the v0.15.0 tag commit"** — CONFIRMED, NONE.
   - Both arch configs carry `version=0.15.0` and `revision=46894ba1904cf8bedff5787f080651e5eed42169`.
   - `gh api …/git/refs/tags/v0.15.0` shows a lightweight tag pointing at that commit.
   - The Release was published 2026-09-22T18:55:30Z, so "cut 18:55 UTC" holds.

3. **"`__version__` and `importlib.metadata.version` both return 0.15.0"** — CONFIRMED but tautological, MINOR.
   - `docker run --rm --entrypoint python …:0.15.0` prints 0.15.0 for both.
   - `juniper_data/__init__.py:24` is `__version__ = importlib.metadata.version("juniper-data")`, so these are one reading and cannot disagree.
   - The fallback on line 26 is a stale literal `"0.14.0"`. It is only reached when package metadata is missing.

4. **"GET /v1/health → 200 with version 0.15.0 when the default CMD runs"** — CONFIRMED, NONE.
   - Ran `-p 127.0.0.1:18471:8100`, CMD `python -m juniper_data`. Response: `200 {"status":"ok","version":"0.15.0","service":"juniper-data","git_sha":"46894ba1…","build_date":"2026-09-22T18:55:43Z"}`.
   - The PR's quoted JSON leaves out `build_date`.
   - The 200 is real evidence. The fields are not independent: `version` is `__version__` (metadata again) and `git_sha` comes from the same build argument as the label.
   - The container ran with auth off, not the compose file's `REQUIRE_AUTH=true`.

5. **"site-packages/juniper_data/tests/ absent (0 files)"** — CONFIRMED, NONE.
   - `__file__` shows the package installed at `/usr/local/lib/python3.14/site-packages/juniper_data`.
   - A walk of the whole filesystem found exactly one `juniper_data` directory and no tests directory.
   - The package's install record lists 205 files, none under tests. `/app` holds only `data/`.
   - arm64, checked by streaming the registry layers: zero `juniper_data/tests` entries.
   - Control: the same probe on 0.14.0 finds the tests directory (95 files).
   - `.dockerignore` at v0.15.0 line 124 is `**/tests/`, and data#405 is an ancestor of the tag (the tag is 11 commits ahead of it).

6. **"equities/equities_seq go from 3.0.0 to 5.0.0, measured in both images"** — CONFIRMED, NONE.
   - Read three ways: the module `VERSION`, `GENERATOR_REGISTRY`, and the served `GET /v1/generators`.
   - 0.14.0 gives 3.0.0/3.0.0; 0.15.0 gives 5.0.0/5.0.0. All other generators are 3.0.0 in both.

7. **"The version is hashed into dataset_id, so a cached 0.14.0 equities artifact is not served"** — CONFIRMED, NONE.
   - `datasets.py:109` takes the registry version, `generate_dataset_id` hashes it, and the cache lookup is at line 156.
   - Same params give `equities-3.0.0-6274a70c…` in 0.14.0 and `equities-5.0.0-556ab172…` in 0.15.0.
   - Control: `spiral-3.0.0-99f84c75…` is identical in both.

8. **"0.15.0 wheel carries 97 test members of 201"** — CONFIRMED, NONE.
   - The downloaded wheel's sha256 (`8b8434a7…`) matches PyPI's digest.
   - 201 members, 97 under `juniper_data/tests/`. Every "test" criterion gives 97.
   - The 0.14.0 wheel has 95 of 199.

9. **"juniper-data#420 fixed it after the tag was cut"** — CONFIRMED, NONE. No published wheel carries the fix yet.
   - #420 merged 19:05:53Z, 10 minutes after the Release, and is 1 commit ahead of the tag.
   - A wheel built locally from #420's merge commit (`6c81cc4c`) has 104 members and 0 tests.
   - The image's lock-pinned `multidict 6.9.0` and `sentry-sdk 2.69.2` are the pre-#420 values. That is independent content evidence that the image was built before #420.

10. **"PyPI serves 0.15.0 since 19:07 UTC"** — CONFIRMED, NONE. PyPI JSON `info.version` is 0.15.0; the wheel was uploaded 2026-09-22T19:07:34Z and is not yanked.

11. **"`verify_published_images.py --fail-on-stale` exits 0; data 0.15.0 is current"** — CONFIRMED, NONE.
    - Fetched from the PR branch and run: exit 0, `currency: current (latest published is 0.15.0)`, all 6 refs resolve.
    - The check can fail: the same script (byte-identical to main's copy) run on main's compose prints `::warning::STALE PIN — 0.15.0 is published, this pins 0.14.0` and `1 of 6 pins are BEHIND…`. It exits 1 with `--fail-on-stale` and 0 without, so "advisory by default" holds.

12. **"#226 flagged the pin… one day after it landed"** — PARTIAL. The flag is CONFIRMED; "one day after" is REFUTED, MINOR.
    - #226 merged 2026-09-22T08:34:09Z and the PR was created 19:43Z the same day, about 11 hours later.

13. **"Pins at L164 / L517 / values.yaml L40; 14 services; 6 unique refs; Helm data 0.15.0, cascor 0.11.0, canopy 0.8.1, worker 0.6.0; only data moved; no test modified"** — CONFIRMED, NONE.
    - Checked by `grep -n`, `yaml.safe_load` and `helm template`; the rendered chart shows `ghcr.io/pcalnon/juniper-data:0.15.0`.
    - The PR's file list is CHANGELOG.md, docker-compose.yml and values.yaml only.

14. **"289 passed, 42 skipped"** — CONFIRMED from the CI log, not re-run here.
    - The CI Unit Tests job (`106907941570`) on `d1bb95df` logged: 331 collected, 289 passed, 42 skipped.
    - Locally, `--collect-only` gives 331. The full suite runs `git` in temp repos, which this lane's rules exclude.

15. **"`test_shared_images_are_pinned_to_one_version` is why the two compose sites move together"** — CONFIRMED, NONE. In a scratch copy with demo-seed left at 0.14.0, that test fails and the other 15 pass.

16. **"Neither `*_ALLOW_TRUNCATION` variable is set anywhere in this repo"** — CONFIRMED, NONE.
    - Grep of the PR-head tarball: the only hits are the PR's own CHANGELOG prose; notes/ has 0.
    - The compose service has no `env_file` and its `environment` block omits both; Helm `data.env` likewise.
    - The names are the real ones: the image's `Settings` uses prefix `JUNIPER_DATA_` with fields `csv_import_allow_truncation` and `equities_allow_truncation`.

17. **"allow_truncation is now a tri-state"** — CONFIRMED, NONE. The parameter changes from `bool` (default False) to `bool | None` (default None) for csv_import, equities and equities_seq.

18. **"arc_agi gains task_type=structured, which the data CHANGELOG records as additive"** — PARTIAL, MINOR.
    - The data CHANGELOG at v0.15.0 does say "Additive by construction".
    - Measured, arc_agi's task_type is *replaced* (`classification` → `structured`), and its `VERSION` stays 3.0.0.
    - Result: `arc_agi-3.0.0-5cbabfa9…` is the same id in both images, and a cache hit returns the stored metadata (`datasets.py:156-175`).
    - So an arc_agi artifact stored by 0.14.0, with the made-up `n_classes` that data#401 fixed, would still be served by 0.15.0.
    - No consumer in juniper-deploy requests arc_agi.

19. **"demo-seed requests spiral only; nothing requests equities"** — CONFIRMED, NONE.

20. **CHANGELOG: "#395's causal share history, then its scale-typo fix"** — PARTIAL, MINOR. The scale-typo fix (5.0.0) is juniper-data#404, which the text does not name; #395 is the 4.0.0 change.

21. **CHANGELOG: "#226 landed without an entry"; canopy 0.8.0 stayed pinned about three days** — CONFIRMED, NONE. #226 touched only the script and its test; canopy 0.8.1 published 09-18 00:38Z, deploy#225 merged 09-21 13:11Z.

### (b) Status banner in the 2026-09-11 handoff (+110/−0 against juniper-ml main)

22. **GHCR release tags: cascor 0.11.0; data 0.14.0 and 0.15.0; canopy 0.8.0 and 0.8.1; worker 0.6.0; recurrence 0.5.0** — CONFIRMED, NONE. The tag lists are complete (no pagination link). Each is a two-arch index.

23. **"worker 0.6.0 image carries torch 2.14.0+cpu"** — CONFIRMED on both arches, NONE.
    - amd64, run: `torch.__version__` is `2.14.0+cpu`, cuda None.
    - arm64, read from the registry layer: `torch/version.py` says `'2.14.0+cpu'`, dist-info is `torch-2.14.0+cpu`.

24. **"`__version__` reads 0.4.0 while metadata says 0.6.0; fixed by worker#192"** — CONFIRMED on both arches, NONE.
    - `__init__.py` has the literal `__version__ = "0.4.0"`; metadata says 0.6.0. The PyPI 0.6.0 wheel has the same literal.
    - #192 merged 09-21, 6 commits after the v0.6.0 tag (`763826bb`, the image's revision). Main now reads metadata.

25. **Dates: worker Release 09-15, on PyPI 09-18; canopy 0.8.0 on 09-12, 0.8.1 on 09-18; data 0.15.0** — CONFIRMED in UTC, NONE.
    - Worker: Release 2026-09-15T22:59Z, PyPI 2026-09-18T00:18Z (that is 09-17 in CDT; the document says it uses UTC).
    - Canopy: 09-12T21:50Z and 09-18T00:38Z.
    - Data 0.15.0 on PyPI: 2026-09-22T19:07Z.

26. **"97 of 201; data#420 merged after the tag"** — CONFIRMED (items 8 and 9).

27. **Extra check: "turing 100% ping loss; no arm64 binfmt handler; yamaguchi is x86_64"** — CONFIRMED.

28. **"Use the census instead: `util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py`"** — UNTRACEABLE on main, MINOR. The contents API returns 404 on main; the file is untracked in this worktree. It has to be committed in the banner's PR, or the banner's first verification command points at nothing.

29. **The `__VALIDATION_RECORD__` placeholder (line 102) is still unfilled** — MINOR.

### (c) Could each check have given a different answer?

- **Registry index / arch probe, currency check, generator VERSION, wheel counts, worker version (literal vs metadata):** yes. Each either gave different answers across versions or has a working negative control.
- **Tests-absent probe:** yes, but only because it looks in the right place. The package installs under `/usr/local/lib/python3.14/site-packages`, while the working directory `/app` holds only `data/`, so a probe of `/app` would pass vacuously. The 0.14.0 control (95 files found) shows this probe is a real negative.
- **Data `__version__` vs metadata, health `version`, health `git_sha` vs label revision:** no. These come from the same source. The independent "built from the tag" evidence is the image content: it has #404 and #405 and lacks #420.
- **`verify_published_images.py` coverage:** it checks the compose file only. No script or test checks the Helm tags; I verified those with `helm template`. This gap predates the PR (MINOR). Its tag-list read has no pagination, which is harmless at today's 6 or fewer tags.
- **arm64 torch version:** read from files, not executed (no emulator here). That is enough for the version string, not for "it runs on a Pi".

**Overall: PASS WITH FINDINGS.** Every load-bearing artifact claim re-derived and held. All findings are MINOR; none is CRITICAL or MAJOR.
