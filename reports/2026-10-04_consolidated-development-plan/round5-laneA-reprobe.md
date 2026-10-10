# Round 5 — Lane A (re-derive the round-4 corrections; test the rewritten gate)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-5 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round5-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Artifacts and the four readings.** "Lnnn" is a line of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.4.0 (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` below); "tool Lnn" is a line of `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`. Other short forms are the plan's own.
    - Plan, at 12:04:55Z: `2cc51727a5c2b27261442b9fcd1ed37b52ceb25a6046742e708155fc8d04f1d9`. At 12:52:01Z: the same.
    - Tool, at 12:04:55Z: `a248352b9ffe8a0b06f18c03aa888f832309e32564b412d32ee97b680e7b3965`. At 12:52:01Z: the same.
    - Window: 2026-10-05, 12:04:55Z–12:52:01Z.
  - **Read**: the plan diff v1.3.0 → v1.4.0 and the tool diff; `round4-reconciliation.md` and `round4-laneB-attack.md`; the cited sections of `…CONSOLIDATED-DEVELOPMENT-PLAN.md`; the whole tool; `…CONSENSUS-PROCEDURE.md` §3–§4; `…RECOVERY-PLAN.md` L227 (B9); `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (W1.4, W1.13).
  - **REST**, read-only `gh api` GETs, inside the window:
    - juniper-ml `main`: `…equities-p0-executed-go-verdict-p1-next.md`, the `util/ad-hoc` listing, `pyproject.toml`, `util/experiment_stack.bash`, `util/isolated_stack.bash`;
    - juniper-data `main`: `ci.yml`, `security-scan.yml`, the workflow list;
    - juniper-data-client: `client.py`, `pyproject.toml`, releases;
    - juniper-cascor `main`: `routes/training.py`, `api/secrets.py`, `lifecycle/manager.py`;
    - juniper-recurrence `main`: `routers/_common.py`, `routers/training.py`, `Dockerfile`, `publish-image.yml`;
    - juniper-canopy `main`: `src/backend/cascor_service_adapter.py`, `src/outbound_errors.py`, `src/observability.py`;
    - gitleaks-action: tag v3.0.0, and `src/gitleaks.js` and `src/summary.js` at `e0c47f4f`;
    - gitleaks v8.30.1: release metadata and `checksums.txt`;
    - code search across the pcalnon repositories.
  - **Installed packages, read-only**, in `JuniperCascor1`: sentry-sdk 2.58.0, juniper-observability 0.4.0, juniper-data-client 0.5.0.
  - **Ran**:
    - the tool 24 times, each with `--workdir` under the session scratchpad's `round5/`;
    - the pinned scanner it downloads (`round5/work/scanner-v8.30.1`) directly, 8 times: `dir --help`, D1–D5, and a trace of test 7;
    - four scratch helpers in `round5/`: a default-config extractor, a byte-case generator, a missed-line locator and a `raise … from None` check.
  - **Synthetic values only.** Every planted value was invented, and none is reproduced here. No secret, `.env`, credential file or transcript was read. There were no host actions. The isolation hook refused one piped command, which was re-run with a redirect.
- Entry point: the round-4 corrections (plan diff, tool diff, `round4-reconciliation.md`)
- Sample: 54 claims re-derived from the added and changed lines, 42 hold and 12 do not hold in full. 24 gate tests (14 behaved as expected, 10 did not), plus 6 diagnostics (D1–D5 on the scanner directly, D6 in Python).

## Findings

| ID | Severity | Location (plan v1.4 "Lnnn", or tool "tool Lnn") | Claim or behaviour | Re-derived (command / file:line → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R5A-01 | MAJOR | L279–286; tool L239–246, L161 | "The gate fails closed"; exit 0 means clean | The scanner skips files the tool counts. For a symlinked file it logs "skipping symlink" and "scanned ~0 bytes"; the tool prints "files to scan: 1", exit 0. Likewise a `.gz` (archive depth 0), a SQLite-magic file and `.pdf` paths. Tests 3–6, D1–D3 | Refuse symlinks or add `--follow-symlinks`; add `--max-archive-depth`; exit 3 on any "skipping" line |
| R5A-02 | MAJOR | L277, L310 | The B9-class rule closes the class the defaults miss | B9's `NAME=` form (`…RECOVERY-PLAN.md` L227) and the interim rule both miss forms juniper-ml writes: quoted keys (JSON, dict; 49 `PASSPHRASE"` uses), spaced flags (`--passphrase '…'`), suffixed names (`--webservice-password-init`, 33 uses, B10's form; `SETTINGS_ENCRYPTION_KEY_OLD`, 12). Test 23: exit 0 | Widen the rule (quote before the separator, spaced flags, `[-_]\w+` suffixes); add each to the canary; ask the owner about B9 |
| R5A-03 | MAJOR | L733–734; L109 | §3 sizes a high-criticality item with a fix at 2 Lane A + 1–2 Lane B | In `…CONSENSUS-PROCEDURE.md`, escalators "each one moves the cell up" (L88); a fix is one (L93). 2A + 1–2B is Medium × High (L84), which a fix reaches only from Low. F-S10's fixes carry universal quantifiers; XC-LEAKS rests on a tool "wrong before": the top-right cell, 3+ A + 2+ B, ≥2 iterations (L86) | Size from base cell plus escalators: ≥5 agents, two batches, ≥110 runs; re-derive the weeks |
| R5A-04 | MINOR | L277; tool L85–87, L103–109 | Placeholders skipped "by shape"; a real `$` value "is still reported" (tool) | The allowlist anchors only at `^`, so it matches prefixes: values starting `$` + letter, `${VAR:-…}`, `%` + letter or `changeme` are skipped (matrix 13, 14, 38, 22); round 4 tested `$9`. A `#`, space or quote in the first 8 characters drops a value (15, 16). Juniper's generators never emit these; human-chosen values can | Anchor shapes at both ends; allow only `${VAR:-}`; fix the comment |
| R5A-05 | MINOR | L276; L310 | Defaults plus the B9 rule | `useDefault = true` imports the default global allowlist into the B9 rule. Its `(?i)^true\|false\|null$` is an unanchored alternation: values that start "true", contain "false" or end "null" are dropped, and `.pdf` and `gitleaks\.toml` paths are skipped. Without `[extend]` (D1) the rule catches matrix 19, 20, 21 and 37; with it, none. XC-LEAKS step 3 deploys the same | Scan the B9 rule separately, without `[extend]`, or record the quirk |
| R5A-06 | MINOR | L286 | Every public push is gated on a scan of the files' content | In a file without blank lines the scanner cuts chunks mid-line. Of 16,000 planted assignments 15,993 were reported, and of 12,000 tokens 11,996 (test 9). The first miss spans bytes 124,992–125,027, consistent with 100,000-byte chunks plus a 25,000-byte peek. CI's scans share the limit | Note it for long logs, CSV and JSONL, or add a line-based pass for the B9 pattern |
| R5A-07 | MINOR | L314 against L275, L281 | Data's PR may add a `.gitleaksignore` of rotated fingerprints | The gate refuses any `.gitleaksignore` (exit 3), and only exit 0 passes; a clean copy carrying one exited 3 (test 17). So that option cannot pass the permanent gate unless the scanned copy omits a pushed file. Refusing by default is right: the scanner honours a source-root file despite `-i` (D5) | Name the exception: scan the copy without the file, and check it holds only fingerprints |
| R5A-08 | MINOR | L467 | Raise `from None`; a test walks `__cause__` and `__context__` and fails if any link carries the key | `from None` sets `__suppress_context__` but keeps the original on `__context__`: on Python 3.14.7 a cause-and-context walk finds a fake key that a suppress-aware walk does not (D6). sentry-sdk 2.58.0 is suppress-aware (`utils.py` L818–821). So the prescribed test fails the prescribed fix | Also clear `__context__` (raise outside the `except`), or specify sentry-sdk's walk |
| R5A-09 | MINOR | L82, L165, L940 | Sentry gets the key "in the exception chain"; 4 open paths | observability 0.4.0 sets `enable_logs=True` (`sentry.py` L66–74), so sentry-sdk 2.58.0 ships INFO+ logs past `before_send` (`logging.py` L394–408). Cascor's WARNING line (`training.py` L129) carries the 409 text. Canopy's ERROR line (adapter L1115) also becomes an event; canopy does not re-raise. F-S10's Sentry path is not among the 4 | Name the log path (Overview 2, H-22); check that XC-SENTRY (a) covers Sentry Logs; count 5 |
| R5A-10 | MINOR | L593 | Recurrence's relay closes "for its image after the lock PR" | Recurrence's `Dockerfile` installs dependencies from `requirements.lock`, then the app from source (L35–49), and `publish-image.yml` builds on the `juniper-recurrence-v*` Release. W1.14 is in the image at that Release; a running stack needs juniper-deploy's image pin moved, and a restart | Say "for its image at the vehicle's Release; for a deployed stack once juniper-deploy's pin moves" |
| R5A-11 | NIT | L285; tool L208–211 | Every could-not-run case exits 3 | `--workdir` naming a file raises `FileExistsError` at tool L211, outside the `try`: exit 1, which the tool's table reserves for "zero-rule" (test 13). `--config X --scan-dir ''` skips the scan without a word and exits 0 (test 15) | Move the workdir setup into the `try`; reject an empty `--scan-dir` |
| R5A-12 | NIT | L280, L285; tool L131–134, L214 | It pins v8.30.1 by the tarball's sha256, and an unpinned release exits 3 | The pin is checked at first download only. A reused `--workdir` trusts a stamp the tool wrote itself: a do-nothing binary with a matching stamp passed that check, and the canary stopped it (test 16). `--sha256` admits any release | Re-verify against the pin on reuse; say "without `--sha256`" |
| R5A-13 | NIT | L1231–1232 | "Created" lists the round-5 lane reports and reconciliation | They do not exist at v1.4.0, which repeats R4B-16's pattern; the Validation record (L1205) correctly says pending | List them once they exist, or mark them pending |
| R5A-14 | NIT | L688 | "W5.8 and W5.9, the end of … L32's order" | L32 of `…equities-p0-executed-go-verdict-p1-next.md` on ml `main` ends with W5.8, W5.9 and then W1.14, which A1 rules | Say "…L32's order, less W1.14 (A1)" |

There is no BLOCKER. The table holds 0 BLOCKER, 3 MAJOR, 7 MINOR and 4 NIT. R5A-01 would be a BLOCKER if scratch copies were made as symlinks: the gate is then vacuous. The plan says "copies", so it is rated MAJOR.

## Gate tests

Tests 1–24 ran the tool with `--scan-dir` (test 1 used `--config`); D1–D6 ran the pinned scanner or Python directly. Matrix numbers refer to test 2's files.

| # | Input (synthetic) | Expected | Observed (exit code; findings) |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml`, fresh workdir (first download) | Pin verified; canary 4/4; repo config zero-rule; exit 1 | "tarball sha256 verified against the pin"; canary 4/4; defaults 1, 0, 0, 1; repo config 0, 0, 0, 0, ZERO-RULE; exit 1. As expected |
| 2 | `matrix/`: 37 files, one planted value each: env, YAML, INI, JSON, dict, CLI, systemd, Compose, TOML, markdown, dotfiles, nested dirs, prefixes, suffixes | All 37 reported; exit 2 | Exit 2 with 17 findings (14 B9-class, 3 generic-api-key). 20 unreported: 04–07, 10, 12–16, 18–23, 32, 37–39. Not as expected |
| 3 | `symlink_only/`: one symlink to a planted file outside the directory | Exit 2 or 3 | "files to scan: 1", 0 findings, exit 0. Not as expected |
| 4 | `symlink_mixed/`: a clean file plus a symlinked planted file | Exit 2 or 3 | "files to scan: 2", 0 findings, exit 0. Not as expected |
| 5 | `gz/`: a gzip of a planted assignment | Exit 2 or 3 | 0 findings, exit 0. Not as expected |
| 6 | `sqlite_magic/`: a SQLite header, then a planted line | Exit 2 or 3 | 0 findings, exit 0. Not as expected |
| 7 | `utf16/`: UTF-16LE with a BOM, planted assignment | Exit 2 or 3 | 0 findings, exit 0. Not as expected. The file is scanned (102 bytes) but cannot match; B9 shares the miss, and UTF-16 is not a realistic Juniper encoding, so no finding is raised |
| 8 | `crlf/`: CRLF line endings | Exit 2 | 1 finding at line 2, exit 2. As expected |
| 9 | `chunk/`: 16,000 assignment lines and 12,000 token lines, no blank lines (576 KB and 612 KB) | All 28,000 reported | 27,989 reported, exit 2; 11 silently missed at chunk cuts. Not as expected |
| 10 | `big/`: a 30 MB log, planted line at 400,001 | Exit 2 | Reported at line 400,001, exit 2. As expected |
| 11 | `toml_override/`: a `.gitleaks.toml` allowlisting every path, beside a planted file | Exit 2 | 1 finding, exit 2. As expected |
| 12 | `unreadable/`: a mode-000 planted file plus a clean file | Exit 3 | Exit 3, from a `PermissionError` in the tool's marker pass (the scanner itself skips the file). As expected |
| 13 | `--workdir` naming an existing regular file | Exit 3 | `FileExistsError` traceback, exit 1. Not as expected |
| 14 | `--scan-dir ''` alone | Exit 3 | Usage error, exit 3. As expected |
| 15 | `--config <scan-config.toml> --scan-dir ''` | Exit 3 | Probe output only, no scan, exit 0. Not as expected |
| 16 | A fresh workdir holding a do-nothing `scanner-v8.30.1` and a matching self-written `.sha256` stamp | Exit 3 | Stamp accepted (no pin message); canary 0/4; exit 3. As expected: the canary is the backstop |
| 17 | `data_pr_baseline/`: a root `.gitleaksignore` of fingerprints plus a clean workflow file (XC-LEAKS note 2's PR shape) | Exit 3, by the tool's design | "would silence findings", exit 3. As designed; it conflicts with note 2 (R5A-07) |
| 18 | A missing directory | Exit 3 | "is not a directory", exit 3. As expected |
| 19 | An empty directory | Exit 3 | "holds no files", exit 3. As expected |
| 20 | `--release v8.29.0`, no `--sha256` | Exit 3 | "no pinned sha256", exit 3, nothing downloaded. As expected |
| 21 | An unknown flag | Exit 3 | Usage error, exit 3. As expected |
| 22 | `allow_variants/`: upper-case, mixed-case and exact allow markers, plus a control | Exit 2, exact marker reported | 3 findings and "1 inline allow marker(s)" for the exact one, exit 2. As expected |
| 23 | `misses_only/`: the 14 realistic-format misses from test 2 (04–07, 10, 12–16, 19, 20, 23, 39) | Exit 2 | "files to scan: 14", 0 findings, exit 0. Not as expected |
| 24 | `symlinked_dir_only/`: a symlink to a directory holding a planted file | Exit 2 or 3 | "holds no files", exit 3. As expected |
| D1 | Scanner direct: test 2's files with the B9-class rule alone (no `[extend]`) | Control | 18 findings, including 19, 20, 21 (true/false/null) and 37 (`.pdf`), which test 2 missed |
| D2 | Scanner direct, debug log: test 3's directory | — | "skipping symlink: follow symlinks disabled", "scanned ~0 bytes", exit 0 |
| D3 | Scanner direct, trace log: tests 5 and 6 | — | "skipping archive: exceeds max archive depth max_archive_depth=0"; "skipping binary file mime_type=application/vnd.sqlite3"; "scanned ~0 bytes" each |
| D4 | Scanner direct: test 22's directory | — | Only the exact lower-case marker suppresses; the other two are reported, as the tool's case-sensitive check assumes |
| D5 | Scanner direct with `-i` at an empty directory: a source-root `.gitleaksignore` naming a planted finding | — | "no leaks found", exit 0. The scanner honours a source-root file despite `-i`, so the tool's refusal is needed |
| D6 | Python 3.14.7: `raise … from None` inside an `except`, with a fake key in the original | — | `__context__` keeps the original; a cause-and-context walk finds the fake key, and a suppress-aware walk does not |

## Checked and holds (short)

- **The pin.** `551f6fc8…f2470eb` equals the linux_x64 line of v8.30.1's `checksums.txt` and GitHub's asset digest. The tool verified it at first download (test 1).
- **The gate's guards**, as tested:
  - the explicit config holds against a scanned `.gitleaks.toml` (test 11), and `GITLEAKS_*` variables are stripped (tool L160);
  - a missing directory, an empty one, an unpinned release, a usage error, an unreadable file and a symlinked directory each exit 3 (tests 12, 18–21, 24);
  - the canary backstops a substituted scanner (test 16);
  - the exact allow marker is reported (test 22, D4), and refusing `.gitleaksignore` is necessary (D5);
  - CRLF, a 30 MB file, dotfiles and hidden and nested directories are scanned (tests 2, 8, 10).
- **The round-4 measurement.** Defaults alone catch 0/1 `PASSPHRASE=` and 0/1 `TIER2_PASSPHRASE=`; the config catches 4/4 (test 1).
- **gitleaks-action.**
  - v3.0.0 resolves to `e0c47f4f8be3…`. At that SHA, `src/gitleaks.js` L96 is `"-v",` beside `--exit-code=2`, and `src/summary.js` L30 builds `blob/<sha>/<file>#L<line>`.
  - juniper-data's `ci.yml` L49–50 runs a daily cron. Its `security` job runs the action on every event but `repository_dispatch`, with `fetch-depth: 0` and no summary or artifact switch.
- **No suppression on any default branch.** Code search finds no `.gitleaksignore` and no inline allow marker on any pcalnon default branch; the control search found 7 `.gitleaks.toml` files. Step 1's history scans are therefore not suppressed today.
- **The F-S10 hops.**
  - data-client `client.py` L349–351 re-raises `from e`.
  - cascor: `manager.py` L4955 re-raises `from exc`; `training.py` L129 logs at WARNING, L130 raises the 409 `from e` and L337 the 502 `from exc`; `secrets.py` L42 does not strip.
  - recurrence: `routers/training.py` L59 logs at WARNING and L60 re-raises `from exc`. It has no Sentry code (0 search hits).
  - canopy: adapter L1114–1116 logs at ERROR and returns `outbound_error_text`, whose L61 passes the text.
  - sentry-sdk's `walk_exception_chain` is at L799–821. observability 0.4.0's `before_send` scrubs request headers only (L23–38).
- **Versions.**
  - `JuniperCascor1` holds data-client 0.5.0.
  - data-client's latest release is v0.5.0, and `main` is 0.5.0, so 0.5.1 is coherent.
  - `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` L556 ships W1.4 in data-client 0.6.0.
  - ml `pyproject.toml` L105 caps `juniper-recurrence<0.6.0`, and R-ML-b is at L598.
- **`…equities-p0-executed-go-verdict-p1-next.md` on ml `main`.**
  - L32: the dates; R2, R3, R7 and R8 before W1.4, W1.8, W1.2 and W1.3; R1 optional.
  - L34 is item 3.
  - L35: Phase 1 runs W1.4 (R2), then W1.3 (R8), …, then W1.2 (R7).
  - L36: "W1.13 publications last".
- **§7.2.**
  - The `--skip-env-preflight` flag is parsed at `experiment_stack.bash` L1309 and `isolated_stack.bash` L663.
  - The refusal messages are at L357 and L329, and the variables at L167 and L112.
  - The check runs in `recurrence_up()` (L815, L434).
- **The tool is not on ml `main`.** None of `main`'s 963 `util/ad-hoc` entries is one of the plan's instruments.
- **§7.1 arithmetic.**
  - Items 1–9 map onto the Waves 0–1 exit bullets.
  - 1+1+1+1+1+3+1+1+1 = 11; 22×3 = 66; 22×4 = 88; 11×3 = 33; 22/3 rounds up to 8.
  - `…CONSENSUS-PROCEDURE.md` §3 is L77–101 and §4 is L102–122.
- **The round-4 record.** Its counts (1/5/10/1) and its 11:13Z–11:43Z window match `round4-laneB-attack.md` L10 and L39.
- **The sitting.** Each of A1–A9 has one Wave 0 slot.

## Could not check

- **Sentry, server-side**: whether its scrubbing rules (XC-SENTRY (a)) apply to Sentry Logs. Also whether the running services have DSNs.
- **How sessions actually make the scratch copies** (`cp`, `rsync -a`, symlinks), and so how often R5A-01 would trigger.
- **The shape of Juniper's human-chosen secrets**, such as the Duplicati UI password, which R5A-04 and R5A-05 turn on.
- **Git history** for allow markers or ignore files. Code search sees default branches only.
- **A deliberately crafted scanner** that passes the canary. That is tampering, and out of scope.
- **Platforms other than Linux x86-64**, which the tool refuses.

## What this report cannot support

- **Severities are judgement.** R5A-03 reads the plan's unstated base cell as Medium or above; a Low base with exactly one escalator gives the plan's 3–4 agents.
- **The gate tests used invented values.** They show which shapes the gate misses, not that any real secret has such a shape.
- **That the tool has no other way to fail open.**
- **State after 2026-10-05T12:52Z.**
- **Lane B's findings.** It ran independently.

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round5-laneA-reprobe.md`. The scanner download, planted fakes, scan reports and scratch helpers stayed under the session scratchpad's `round5/`, outside every repository.
