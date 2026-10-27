# GraphQL request-body cap: runner-side measurement (2026-10-26)

**What this settles.** `util/release_train/ceremony.py` HALTs `archive-too-large` when a release-notes archive's
base64 exceeds `ARCHIVE_B64_MAX_DEFAULT`, because the archive travels inside one `createCommitOnBranch` request
(juniper-ml#2227). The default was 125,000 B, the figure measured from turing on 2026-10-17 (130,000 B accepted,
131,000 B refused with HTTP 499). It was later re-diagnosed as turing's weak link: GitHub's GraphQL frontend drops a
request that runs past about 7-10 s. The owner ruled on 2026-10-18 to keep that conservative default until a
runner-side measurement settled the real cap. This directory is that measurement.

## Result

| Where | Run | Bodies sent | Refused | Slowest |
| --- | --- | --- | --- | --- |
| GitHub-hosted runner (`ubuntu-latest`) | juniper-ml Actions run 40410086979 | 100,000 B to 16,777,216 B, 12 sizes per mode | none | 3.29 s (16 MiB, comment-padded) |
| The Linux host (direct link) | `workstation-linux-host.json` | 100,000 B to 8,388,608 B, 11 sizes per mode | none | 2.15 s (8 MiB, comment-padded) |

Every body was accepted, in both modes:

- `comment` mode pads a no-op query with a `#` comment, which was turing's method;
- `variable` mode carries the padding in a declared String variable, the way `createCommitOnBranch` carries
  `contents`.

There was no boundary to bisect. A variable-padded body is answered with HTTP 200 and the GraphQL validation error
"Variable $pad is declared by anonymous query but not used". That is the expected answer, and it proves the whole
body was received and parsed.

**Consequence.** The owner ruled on 2026-10-26 to raise the default to 1,000,000 B. That is 16x below the largest body
the runner was seen to accept, and about 8x the largest archive so far: juniper-ml 0.11.0's 122,032 B came within 7 KB
of the old cap, and juniper-canopy 0.9.0's 103 KB notes had to be condensed under it.

## How it was run

- **The instrument**: `util/ad-hoc/2026-10-26_graphql_body_cap_probe.py`. It sends read-only no-op queries, never
  prints the token, and records the HTTP status, elapsed time and reply shape for each size.
- **Runner side**: a throwaway draft PR, juniper-ml#2361, targeted a throwaway base branch, so no `main`-scoped
  workflow ran. It added only a `pull_request` workflow that ran the probe under `contents: read`. The PR was closed
  unmerged and both branches were deleted. `runner-run-40410086979.log` is the job's full log. GitHub masks the
  token as `***`, and a scan for token patterns found none.
- **Host side**: `python3 -I util/ad-hoc/2026-10-26_graphql_body_cap_probe.py --mode both --bisect --json …`, with
  the owner's `gh` token.

## Files

- `README.md`: this summary.
- `runner-run-40410086979.log`: the runner job's log, as downloaded by `gh run view 40410086979 --log`.
- `workstation-linux-host.json`: the host run's per-request results.
