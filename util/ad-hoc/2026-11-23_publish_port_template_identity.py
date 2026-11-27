#!/usr/bin/env python3
"""Check a ported publish workflow against juniper-cascor's one-artifact template, as swept: identical steps, same wiring, pinned install scripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (the one-artifact template sweep: rulings 1 and 2 of 2026-11-16, PUBLISH_TAG_PREFIX, items 23 and 25; the owner's rulings of 2026-11-24, "Pin exact scripts" and "Pin template SHAs")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-24_publish_port_install_pins.json (the pinned install scripts, read from beside this file);
         util/ad-hoc/2026-11-15_publish_port_template_identity.py (the checker this copies: provenance of record for the
         15/15 result of 2026-11-16, never edited); util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py (the
         template's sweep); juniper-cascor src/tests/unit/test_publish_one_artifact.py (the checks this applies across
         repos); util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py (the review that found what this
         checker let through); util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py (the round-2 review, whose port
         simulation ran the 15 ports through this checker); tmp/sweep/REVIEW_DISPOSITIONS.md (every review round and fix
         pass, the install-script rules fix pass 7 removed among them)

Why
---
Each port copies juniper-cascor's template steps "verbatim", and each repo's own test can only compare the copies inside
that repo. This compares every copy in every repo with cascor's ``publish.yml`` (the template's source), step by step,
as parsed YAML, so a whitespace, comment-free or reordering difference in a run script fails here even when the repo's
own test passes. It re-checks the wiring cascor's test pins, and (fix pass 7) it requires each publisher's install step
to equal a pinned, reviewed script. Beyond the 2026-11-15 checker it requires:

- ruling 2 of 2026-11-16: a job named ``Verify the TestPyPI install`` that needs the TestPyPI job, holds exactly
  ``contents: read``, has no environment, no ``env``, no upload, no ``if:`` and no ``continue-on-error`` (job or step);
  the PyPI job needs both; the TestPyPI job holds exactly ``id-token: write``, checks nothing out, installs nothing and
  ends at its JSON check;
- ruling 1 of 2026-11-16 and ``PUBLISH_TAG_PREFIX``: the republish job equal to the template's (its find step carries
  both), ``PUBLISH_TAG_PREFIX`` in the workflow ``env``, equal to ``v`` with ``PUBLISH_DIST_DIR`` ``dist``, or to
  ``<PUBLISH_PACKAGE>-v`` with ``<PUBLISH_PACKAGE>/dist``, and the build job's guard EQUAL to one of its two forms
  (``GUARD_FORMS``) with that prefix filled in;
- item 23: ``uses:`` compared by action name, the ``@ref`` dropped, so a Dependabot bump in one repo fails nothing;
  superseded in every job of the chain by the owner's ruling "Pin template SHAs" (fix pass 9, below): each ``uses:``
  there equals the template's exact ``owner/repo@<SHA>``, and each repository's own CI keeps item 23's ref-free digests;
- item 25: the reuse-condition exemption narrowed to the step named ``Require a GitHub Release for this tag``;
- the review of 2026-11-23 (test lens K1-K9, workflow lens M1, N1, N2, N4): each publish job's steps, as (name, action),
  equal the template's; an install-job checkout keeps no credential; no ``env`` on the TestPyPI, install, PyPI or
  republish job; no ``continue-on-error`` or ``if:`` on any upload step; the PyPI job holds exactly ``id-token: write``;
  no job but the TestPyPI, install and PyPI jobs has "pypi" in its name (juniper-ml's release-train ceremony tells the
  publish jobs apart by it); and every failure that can still be checked is reported, even when a job is missing;
- the round-2 review (tmp/sweep/REVIEW_DISPOSITIONS.md, § Round-2 review), which ran the 15 ports through this checker:
  F1, each step between the build and ``Record SHA256SUMS`` holds ``name``, ``if`` and ``run`` alone, and its commands
  are EXACTLY one of the window's forms (``twine check dist/*``; juniper-ml's tag assert with the workflow's prefix,
  ``util/`` at the root and ``../util/`` in a sub-package's directory; canopy's wheel smoke test), never a prefix; F4,
  no ``PIP_*``, ``PYTHON*``, ``UV_*`` or ``HASH_CHECK_*`` key in any ``env``: workflow, job, a job's container, or step
  (``BUILD_PYTHON_ENV`` admitted on a build step, below); F8c, ``shell:`` on an install step refused unless it is
  ``bash``; the install job runs no ``container`` and uses no action but ``actions/setup-python`` and
  ``actions/checkout``, and an install step's ``env`` holds ``RELEASE_TAG: ${{ github.event.release.tag_name }}`` alone;
  the workflow sets no ``defaults.run.shell`` (nor, since fix pass 7, ``defaults.run.working-directory``); no
  ``concurrency`` group, the workflow's or a job's, cancels a run in progress; and every bash ``run`` step in the
  workflow parses (``bash -n``);
- the round-4 review (the same file, § Round-4 review): R4-4, no job sets a ``concurrency`` group of its own (by default,
  ``queue: single``, GitHub keeps one pending job per group and cancels the older one when another queues, so a group on
  a job could stop a run between its two uploads; the build job is held to the same rule), the workflow's admitted when
  its own ``cancel-in-progress`` is false, which read the setting of the wrong run: a group is repository-wide, and the
  run queued NEXT in it decides, by its own ``cancel-in-progress``, whether the run in progress is cancelled, so since
  fix pass 10 (round 11's M11-D) the workflow's group is exactly ``<file stem>-${{ github.ref_name }}`` with
  ``cancel-in-progress: false``, or absent (a group no other publisher's file uses, for the refs the publishers use:
  fix pass 11, n12-b); R4-6, ``--repo``, the repository the workflows belong to, as the operator states
  it (the workflow text, which a port controls, never decides it), juniper-ml's tag assert admitted in the window in
  juniper-ml alone, for its seven packages, and canopy's smoke test in juniper-canopy alone, and no
  ``defaults.run.shell`` on the build job; and its NITs: the lag error the template's text exactly, with the loop's own
  try count (``LAG_ERROR``, now checked on each pin), ``shell: bash`` admitted on an install step (the runner runs it as
  ``bash --noprofile --norc -eo pipefail {0}``, which keeps ``-e``), and ``PYTHONUNBUFFERED``,
  ``PYTHONDONTWRITEBYTECODE``, ``PYTHONHASHSEED``, ``PYTHONIOENCODING`` or ``PYTHONUTF8`` in a build step's env (and
  the build job's own until fix pass 8, whose key set gives that job no env) (``BUILD_PYTHON_ENV``: each changes how
  Python reports, encodes or hashes, never what it imports or runs);
- fix pass 4 (round 5's review): R5-F4, ``BASH_ENV``, ``ENV``, ``BASHOPTS`` and ``SHELLOPTS`` refused as env keys at
  every level of the workflow's YAML (round 5's R5-13 ran a checkout script before every bash step of the build job
  through ``BASH_ENV``; an environment a step writes to ``$GITHUB_ENV`` is not YAML, and round 11's M11-9 set
  ``BASH_ENV`` there: fix pass 10, below, refuses a build step that names that file); and,
  beyond the review, the build job's own ``env`` (and its container's) holding no key but ``BUILD_PYTHON_ENV`` (since
  fix pass 8 the build job carries no env and no container at all, below) (there
  ``PATH`` chose which ``twine`` the window step ran, ``BASH_FUNC_twine%%`` stood in for it and ``SHELLOPTS: xtrace``
  ran ``PS4``); at every level, an env key that is not a shell identifier (bash imports ``BASH_FUNC_<name>%%`` as a
  function) or an ``env`` that is not a mapping; an install job's checkout other than a sparse checkout of the one file
  the version is read from (``SPARSE_PATH``: a ``pyproject.toml`` or ``_version.py``, in cone mode, with
  ``persist-credentials: false`` and no other input), which keeps the package's source and any config file out of the
  workspace; and a build job that runs anywhere but ``ubuntu-latest``, or in a container, or with services (each would
  choose what the window steps' ``twine`` is);
- fix pass 5 (round 6's review): at the build window, every rule of ``line_problems`` (below).

Fix pass 7: exact pins (the owner's ruling of 2026-11-24, "Pin exact scripts")
-------------------------------------------------------------------------------
Rounds 4 to 8 each found a MAJOR-or-worse bypass of the install-script rules, every one where this checker's reading of
shell differed from bash's (R4-2, R5-F1, R6-F1, R7-1, R8-1 to R8-3). The owner ruled that the checker stop judging port
install scripts with its own reader: each port's install step must equal a pinned, reviewed script. The decisions:

- What is pinned: every ``run`` step of the job named ``Verify the TestPyPI install``, juniper-cascor's three
  publishers' included (the template's scripts are pins too). No other per-port run script needed a pin: the only other
  one this checker read with a shell reader is a build-window step, judged against the checker's own exact allow-list,
  which stays (below).
- The key is (repo, workflow, step): ``--repo`` (the operator's), the workflow file's name as the operator passes its
  path (a workflow's own text never chooses it), and the step's ``name``. Each pin also names its package, which must be
  the workflow's ``PUBLISH_PACKAGE``, so a pin never vouches for another package's publisher.
- The pins live in ``util/ad-hoc/2026-11-24_publish_port_install_pins.json`` (``PINS_FILE``), loaded from this file's
  own directory; ``--pins PATH`` overrides it, an operator argument only. The file holds ``format``
  (``PINS_FORMAT``), ``about`` and ``pins``, a list whose entries hold exactly ``repo``, ``workflow``, ``step``,
  ``package``, ``source`` (provenance), ``sha256`` and ``lines``. A pin's text is its lines joined with a newline, with
  no final newline (one line per array element, so a port's review reads and diffs it line by line); ``sha256`` is that
  text's, UTF-8. The file is pure ASCII, every other character written as an escape, so a reviewer sees each one. A
  pins file is refused whole (exit 1, nothing checked) when it holds a byte outside ASCII (fix pass 8, m9-b), does not
  parse, repeats a key in any JSON object, is not of its format, or holds a pin that: does not hold exactly those fields
  (``lines`` a list of strings, every other a string);
  names a repository not in ``REPOS``, a workflow that is no file name, or no step; has no lines, a final empty line or a
  line holding a newline; repeats another pin's key; holds a text that a step's script would be refused for (below);
  holds a sha256 that is not its text's (an edit without its hash, or a tampered file); or holds no single retry loop
  with the template's lag error (``LAG_ERROR``, below). Its path and sha256 are printed first, to be matched with the
  sweep's manifest (tmp/arc/sweep_scripts.sha256).
- The install job: every run step must have a pin for its key, under a name no other run step holds, and every pin of
  (repo, workflow) must have its run step. A step key GitHub does not define (``Run:``, a look-alike ``run``) is refused
  there, so no step runs a script under a key this checker does not read. Where a pinned script starts is part of what
  runs: a step's ``working-directory`` and the job's ``defaults`` were refused already, and the workflow's
  ``defaults.run.working-directory`` is refused now (no port sets one).
- The comparison: the step's ``run`` as YAML delivers it (a string, each ``\\r\\n`` already ``\\n``) is refused when it
  holds a NUL, a character other than printable text, a tab and a newline (a CR, a NEL, a line or paragraph separator, a
  control or format character), trailing whitespace on any line (never stripped: a backslash then a space at a line's
  end is an escaped space to bash, and stripping the space would make a continuation), a final backslash (a final
  newline would decide what it means) or ``${{`` (the runner substitutes an expression into the text before bash reads
  it). A text ending in more than one newline is refused (fix pass 8, m9-a: a script that ends inside a here-document
  reads each newline after its last line as a line of its body, so ``|+`` keeping blank lines is another script);
  otherwise its one final newline, if any, is removed (``|`` and ``|-`` deliver the same script) and the rest is compared
  with the pin byte for byte, comments included. Nothing else is normalized, so the text compared is the text the
  runner writes for bash.
- A mismatch names the key, the first differing line (the pin's and the step's) and a unified diff (``DIFF_LINES``
  lines at most), and says to update the pin through that port's review, in the pins file this run loaded, if the change
  is intended. A step without a pin, and a pin without its step, each fail with their own message.
- What the runner runs is what GitHub's YAML parser delivers, and this checker reads PyYAML's events, typed (since fix
  pass 8) as GitHub's reader types them (``UniqueKeyLoader``, below). What is refused (``file_problems``,
  ``UniqueKeyLoader``): a character other than printable text, a tab or a line break (LF, or CR LF) anywhere in the
  workflow file, as defence in depth (round 9 found GitHub's YamlDotNet reading a raw U+0085 as PyYAML does, as a line
  break, and only a YAML 1.2 parser such as Node's ``yaml`` keeping it in the line; a byte order mark or a no-break space
  changes nothing PyYAML reads, and is refused all the same); a mapping that repeats a key, by its text (``on`` and
  ``"on"``) or by the value made of it (``1`` and ``01``): PyYAML keeps the last, and another parser need not (GitHub's
  reader refuses such a file, and one whose keys are equal but for case); and a merge key (a plain ``<<``), which a
  YAML 1.1 parser applies and GitHub's reader keeps as a key. The file is read as bytes and decoded, never through
  Python's newline translation, so these rules and the parser see its characters as they are.
- ``LAG_ERROR`` stays, checked on each pin as it loads (``lag_problems``): one retry-loop header (``LOOP_HEADER``) and
  one lag error, exactly the template's text with the pin's package, a version variable and the loop's own try count
  (the operator signature docs/ci_cd/MANUAL.md quotes). A text check of a reviewed pin: it reads lines, never decides
  what bash runs, and can only refuse a pin.
- Removed, as an exact pin now covers each install script: the shell reader (``lex``, ``structure``, ``shlex``'s
  ``shell_words``, ``pieces``, ``skeleton``, ``operators``) and every rule that read an install script with it: the
  positive allow-list (fix pass 4), the F2 and F3 fetch and later-install rules, F4's script rules, the retry-loop rule,
  R4-2's last command, R4-3's deny rules, the cd-first, ``||``, ``set +``, ``trap`` and ``exit`` rules, the dest and
  wheel naming rule, R7-1's two-readers comparison, R7-4's loop comparison, and ``line_problems`` on install steps.
  Round 8's R8-1 (a digit before ``&>``), R8-2 (``$_``) and R8-3 (an ``if`` hidden from ``shlex``) close by construction
  for install scripts: any such edit changes the text. Round 8's probed fixes had nothing left to apply to, since every
  place they touched (``structure``, ``pieces``, the allow-list, its ``if`` rule, R4-2's last command) is gone; N8-2 to
  N8-4 (over-strict install-script rules) went with their rules, and N8-5's three docstring claims with this rewrite.
- The reader that stays, and why: the build window. Each step between the build and ``Record SHA256SUMS`` is still read
  by ``commands()`` and checked by ``line_problems`` (fix pass 5's line rules), because its allow-list is the checker's
  own (``TWINE_CHECK``, ``TAG_ASSERT``, ``CANOPY_SMOKE``), scoped by ``--repo`` and compared as commands, so layout
  edits that bash reads alike (round 7's W1-W8) keep their verdicts, as the ruling's brief requires of edits outside
  install scripts. Its forms hold no quote, substitution or pip of the kind the lexer bypasses of rounds 4 to 8 used,
  and round 8 found no window bypass (its B8-16). Round 8's N8-1 fix applies there: ``line_problems`` reads a "blank"
  next line with ``.strip(" \\t")``, so a line holding a CR, VT, FF or no-break space falls through to the rule that
  names it.
- Expected pin updates: the pins are seeded from the 15 port simulations (and cascor's three from ``f5ed3017``), and
  each port's own review replaces its pin with the port's final script. Known content updates, beyond each port's own
  comments: R4-5, a failing ``importlib.util.find_spec(<module>)`` check, for juniper-cascor-client, juniper-cascor-worker,
  juniper-data, juniper-data-client, juniper-ml's ci-tools and observability; and juniper-ml ``publish.yml`` (R5-F5 with
  R4-1), the simulation's three edits (the flag-form fetch, ``ls -la`` without ``|| true``, the template's lag error),
  with ``tests/test_publish_testpypi_verify.py:477`` moved to the template's lag text.

Fix pass 8: the jobs' keys and YAML 1.2 typing (round 9's review)
-----------------------------------------------------------------
Round 9 found fix pass 7's pin comparison sound, and four gaps one level outside it: where, and beside what, the
compared text runs, and how a compared value is typed. The decisions:

- B9-1 and M9-A: each job of the template's chain carries exactly the keys its template job carries, the sets
  juniper-cascor's own test pins (``CHAIN_JOB_KEYS``), with ``timeout-minutes`` (``OPTIONAL_JOB_KEYS``) admitted on every
  job but the republish job, which is compared whole. So the build job holds ``name``, ``if``, ``runs-on``,
  ``permissions`` and ``steps`` (and, in a sub-package's publisher, ``defaults``, exactly ``run.working-directory:
  <PUBLISH_PACKAGE>``; a root package's build job carries none, not even ``working-directory: .``); the TestPyPI and
  PyPI jobs ``name``, ``needs``, ``runs-on``, ``environment``, ``permissions``
  and ``steps``; the install job ``name``, ``needs``, ``runs-on``, ``permissions`` and ``steps``; the republish job its
  template's six. ``container``, ``services``, ``strategy``, ``env``, ``outputs``, ``concurrency`` and every other key
  are refused on each (a job container runs the template's ``python3`` checks in an image of the port's choosing; a
  service beside the PyPI job can rewrite the dist after its check and before its upload). Every job's ``runs-on`` is
  ``ubuntu-latest`` (the TestPyPI and PyPI jobs' compared since fix pass 8); ``permissions``, ``needs``, ``if`` and the
  environment's name are compared as before. An environment given as GitHub's ``{name, url}`` mapping, as cascor's
  sub-package publishers write it, is admitted on its name, holding those two keys alone (the runner's schema defines no
  other), its url a string: a URL only labels the deployment. The build job's own ``env``, which fix pass 4 admitted
  holding ``BUILD_PYTHON_ENV`` keys, is outside the set and refused (a build step's env still may hold them).
- M9-B: every setup-python step of the build and install jobs takes ``with: {python-version: "3.N"}`` alone
  (``setup_python_problems``): ``mirror`` with ``check-latest`` installed an interpreter from a URL of the port's
  choosing and ran its setup.sh; ``cache``, ``update-environment``, ``python-version-file`` and the rest each choose
  where the interpreter comes from, or what runs first. The template's value is "3.12"; canopy's port uses "3.14", so
  the form is held (a CPython version written as a string), not the one value.
- M9-C: plain scalars are typed as GitHub's reader types them (``GITHUB_SCALARS``, transcribed from actions/runner's
  YamlObjectReader: YAML 1.2's core schema), never by PyYAML's YAML 1.1 resolvers. ``retention-days: 1:30`` is the text
  "1:30" (upload-artifact's ``parseInt`` makes it 1 day) and fails the 90-day rule; ``0132`` is 132; ``default: no`` is
  the text "no" and fails the dispatch comparison. Tags follow GitHub's reader too: ``!!str`` in any style, the four
  core tags on a plain scalar holding their form, and no other.
- m9-a: a pinned step's ``run`` ends in one newline at most (above). m9-b: the pins file is pure ASCII. n9-a: the file
  rule's message says what is true of each character it refuses. n9-b: a mismatch names the pins file loaded. n9-c: a
  workflow whose ``on``, jobs or steps are not mappings is refused with a message (``shape_problems``), any other shape
  no rule reads fails that workflow alone, and the next one is still checked.

Fix pass 9: upload inputs, extra jobs and action SHAs (round 10's review; the owner's ruling "Pin template SHAs")
--------------------------------------------------------------------------------------------------------------
Round 10 found fix pass 8's code sound, and three gaps one level further out, each a part of the workflow this checker
read without judging, or never read: the upload steps' inputs beyond four literal keys, the jobs beside the chain, and
the actions' refs. Each is closed by an exact set taken from the template, not by a new deny rule:

- B10-1: each upload step of the TestPyPI and PyPI jobs holds exactly ``name``, ``uses`` and ``with``
  (``UPLOAD_STEP_KEYS``), as the template's do, and its ``with`` holds exactly the template's upload inputs, under their
  literal names, with the template's values as GitHub types them (TestPyPI: ``repository-url`` and ``packages-dir``;
  PyPI: ``packages-dir``), adding only ``verbose`` and ``attestations`` (``UPLOAD_OPTIONAL_INPUTS``), each the boolean
  true: cascor's sub-package publishers add ``verbose``, three ports ``attestations`` (the action's default), and no
  port adds any other (``upload_problems``). GitHub matches an action's inputs case-insensitively and evaluates an
  expression key in a step's ``with``, and the pinned action reads five deprecated underscore aliases
  (``repository_url``, ``packages_dir``, ``verify_metadata``, ``skip_existing``, ``print_hash``) whenever the
  kebab-case input is empty: round 10 sent the PyPI job's OIDC token to a host of its choosing through
  ``repository_url:``, ``Repository-URL:`` and ``${{ 'repository-url' }}:`` (R10-1 to R10-3), and turned
  ``--skip-existing`` on and ``--attestations`` off (R10-4). So any other key is refused, one equal to an input but for
  case or ``-`` and ``_``, and an expression key, each with its own message. Every other step of the TestPyPI, PyPI and
  republish jobs is a template step compared whole, so every step of a job holding id-token is held exactly. Beyond the
  brief (round 10's O-2): a mapping key holding ``${{`` is refused wherever it stands (``document_problems``); no
  template, port or simulation holds one.
- B10-2: every job outside the chain's five is refused, except an exact allow-list (``EXTRA_JOBS``), keyed as a pin is
  (``--repo``, the workflow file's name, the job id): the job compared whole, as GitHub types it, and the reusable
  workflow it calls read beside the workflow (a local ``./.github/workflows/<file>`` call runs that file at the caller's
  commit) and compared by sha256, as a pinned install script is (``extra_job_problems``). Today it holds juniper-data's
  ``notify-consumers`` alone: ``needs: pypi``, ``permissions: {}``, one named secret, and a ``notify-consumers.yml`` of
  run steps alone, read at juniper-data ``main`` (``6b734fd9``). Round 10 replaced ``<PUBLISH_PACKAGE>-dist`` from an
  extra job (``actions/upload-artifact`` with ``overwrite: true``, R10-5), named a remote reusable workflow called with
  ``secrets: inherit`` (R10-6), and left a 0.14.1 artifact after the PyPI job that "Re-run failed jobs" published with
  no install check (R10-7): any job of the run can replace the artifact, so the rule is the set of jobs, not their
  ``needs``.
- B10-3, the owner's ruling of 2026-11-24, "Pin template SHAs": in the jobs that hold id-token (TestPyPI, PyPI,
  republish) and the jobs they need (build, install), every ``uses:`` equals the template's exact
  ``owner/repo@<40-hex SHA>``, and a step whose action the template does not use in that job is refused
  (``uses_problems``). The install job may use ``actions/setup-python`` (the template's install job does) and
  ``actions/checkout`` (cascor's sub-package publishers' sparse checkout), each at the template's SHA
  (``INSTALL_ACTIONS``). A template whose ``uses:`` there is not ``owner/repo@<40 lowercase hex>``, or that names one
  action at two refs, is refused (exit 1, nothing checked). A Dependabot bump in a port's repository fails this
  cross-repository check until cascor's template takes the same bump; each repository's own CI keeps item 23's ref-free
  digests. Round 10's R10-8 passed with ``actions/download-artifact@main``, and with the publish action at a commit that
  exists only in a fork, which GitHub's API serves under the upstream name.
- m10-a: nothing one workflow holds stops the next being judged. Each workflow is judged, labelled and printed inside a
  catch-all, so a crash fails that workflow alone and never passes it; output the stream cannot encode is printed as
  escapes; a file nested beyond Python's recursion limit is a load failure; and a lone surrogate (a double-quoted
  ``\\uD800`` escape loads as one) is refused in any string (``document_problems``). The exit status is 1 when any
  workflow failed or crashed. Round 11 found the claim untrue twice, and fix pass 10 (below) closes both: an alias bomb
  held the run for hours, so the next workflow was never judged (M11-4); and text a workflow holds, printed raw, could
  display a refused workflow, and the next one's FAIL, as PASS (M11-1, M11-2), though the exit status stayed 1. Round
  12 found it untrue again (M12-A): a workflow, or the file an allow-listed job calls, linked to ``/dev/stdin`` held
  the read for good, so the next workflow was never judged, and the called file linked to ``/dev/zero`` grew until
  memory ran out (it alone was read with no bound); since fix pass 11 (below) a file is read only when it is a regular
  file, within its bound.
- n10-a, n10-b: messages true of every form they refuse: ``runs-on`` must be the string ``ubuntu-latest``, as the
  template writes it (a one-label list naming it included), and ``persist-credentials`` the boolean false the template
  gives (the text ``"false"``, which the runner would hand checkout as the same input, included).
- Outside this checker, recorded only: R10-7's root cause, that no publish job ties the version in SHA256SUMS to the
  release tag (SWEEP item 28), is the template's; this pass changes no template.

Fix pass 10: what is printed, aliases, the build job's upload and file commands, concurrency (round 11's review)
-------------------------------------------------------------------------------------------------------------
Round 11 found fix pass 9's rules sound, and one level further out, what this checker PRINTS: a step name loaded
through a double-quoted escape (``"\\x1b[2J..."``, ``"...\\nPASS ..."``) was echoed raw in a message, so a refused port
displayed as PASS in a terminal, and could conceal the next workflow's FAIL (M11-1 to M11-3), while the exit status
stayed 1. Each fix is an exact rule the template, every port and every simulation meet (37 files: round 11's
fixcheck_r11.out, and checker-r11/evidence/survey_fp10.out, which also reads the build jobs' file commands and the pins
file):

- M11-A, at load (``document_problems``): every loaded string, keys and values at every depth, holds printable text, a
  tab and a newline alone (a lone surrogate keeps fix pass 9's own message), and no mapping key, and no ``name`` of the
  workflow, a job or a step, holds a newline. The pins file is held to the same (``load_pins``): every string in it is
  printable text alone, a pin's lines keeping their own rule, which admits a tab.
- M11-A, at output: every workflow-derived value a message names goes through ``shown()`` (a string of letters, digits
  and ``._/@+-`` alone as it stands, its ``!r`` would only add quotes; every other value as its ``repr``, which escapes
  each character but printable text; at most ``SHOWN_CHARS`` characters of a string, or of a repr, then the count of
  the rest), through ``!r``, or inside a list or a mapping, whose ``str()`` is its ``repr``; a YAML error's text, a
  crash's and bash's own through ``visible()``. As defence in depth, ``main()`` passes every line it prints, to stdout
  and to stderr, through ``visible()``, which writes each character but printable text (C0 and C1 controls, DEL, line
  and paragraph separators, format characters, surrogates) as an escape; and it prints each line of a message after
  its first (a pin mismatch's diff) indented. So no text a workflow holds can move the cursor, clear or conceal, or
  begin a line, where the checker's own verdicts stand. Since fix pass 11 every such value is also cut and folded, an
  ``!r`` and a list's ``str()`` included (round 12's M12-C, below).
- M11-B (``UniqueKeyLoader.compose_node``): a YAML anchor or alias is refused at load, before any rule walks the
  document, so the loaded workflow is a tree no larger than its file (round 11's M11-4: an alias bomb of 49 KB ran past
  120 s, about 70 minutes extrapolated, and the next workflow was never judged; no template or port uses an anchor).
  Beyond the brief, the same class without aliases (checker-r11/evidence/cost_probe_fp10.out): the duplicate-key check
  read a list, so a flat mapping of 16,000 keys took 2.7 s and grew as its square, and ``bash -n`` runs once per run
  step (about 3 ms each). So the check reads a set, and a workflow file larger than ``MAX_WORKFLOW_BYTES`` (256 KiB; the
  largest publisher is 52 KB) is refused before it is parsed. Five more paths grew as the square of the file, and each
  is linear now, giving what it gave (checker-r11/evidence/cost_probe_square_fp10.*.out, before and after;
  equivalence_fp10.out): a key's text copied into the place of each node beneath it (``place()``: 795 MB of memory
  from a file of 128 KB, so gigabytes from one under the bound), and a job's id into a scope or a message for each of
  its steps (``shown()``; both cut at ``SHOWN_CHARS``); the substitution of ``${{ }}`` before ``bash -n``
  (``expression_words``: a line of 40,000 ``${{`` took 22.7 s); the window's check of a continuation into a blank line
  (``line_problems``); and the duplicate check of keys that are lists (``frozen``). The largest cost left is
  ``bash -n``, once per run step: the most run steps the bound holds take a few minutes on this host at most, and the
  next workflow is then judged (cost_probe_live_fp10*.out, cost_probe_square_fp10.*.out): a delay, bounded, never a
  stop, for the workflow files themselves. Round 12 found two reads outside that claim (M12-A: the called file was read
  with no bound, and a workflow or the called file could be a device or a pipe), which fix pass 11 brings inside it.
- M11-C (the build job's steps before the build): ``actions/upload-artifact`` is admitted in the build job only as its
  ``Upload dist artifacts`` step, the template's, compared whole and last (round 11's M11-12 uploaded staged files as
  ``<PUBLISH_PACKAGE>-dist`` before the build, which "Re-run failed jobs" then published, never built nor recorded);
  and a run step of the build job whose ``run`` or ``env`` names the runner's file commands for the environment or the
  PATH (``GITHUB_ENV``, ``GITHUB_PATH``, ``github.env``, ``github.path`` or ``_runner_file_commands``, in any case:
  ``ENV_FILE_NAMES``) is refused (round 11's M11-9 wrote ``BASH_ENV`` to ``$GITHUB_ENV``, and its hook ran inside the
  unchanged twine check; no port's build step names one). That rule reads text, literal spellings alone, so what it
  cannot see stays below (round 12's M12-B).
- M11-D (``check()``): the workflow's ``concurrency``, when present, is exactly ``{group: <the workflow file's
  stem>-${{ github.ref_name }}, cancel-in-progress: false}``, the form every publisher that sets one writes (22 of the
  37 files, 11 publishers), compared with its types. Round 11's M11-10 named ``pr-budget-alarm``, the group of cascor's
  scheduled workflow that cancels in progress, so a scheduled run could cancel a publish run while its PyPI job waited
  at the gate (R4-4's harm, availability only: the republish ladder recovers it). That is a group no other publisher's
  file uses, for the refs the publishers use (fix pass 11, n12-b): for refs a writer crafts, ``publish`` at
  ``ci-tools-main`` and ``publish-ci-tools`` at ``main`` share one, each ``cancel-in-progress: false``, so at most a
  pending run is replaced (round 12's N12-7).
- M11-E: the publish action's SHA pins its composite steps and the NAME of the image they run, not the image (below).
- n11-a, n11-b, n11-d, n11-e: a called file whose sha256 differs from its pin is refused with what is true (its bytes
  differ, a change of line endings alone among them); an action named in another case is refused with what is true
  (GitHub reads an owner and a repository without regard to case, so it names the template's action, and this checker
  compares the template's exact text), and an upload so named is counted as one (``action_name``); ``template()``'s
  local is ``install_jobs``; the two-refs refusal says why (the install job admits one ref of each action).
- n11-c, by design and unchanged: ``needs: [pypi]`` on the allow-listed job and ``verbose: "true"`` on an upload are
  refused by exactness. Each is harmless, no port writes either, and each message is true.

Fix pass 11: files that are not regular, the env file's spellings, what a terminal wraps (round 12's review)
-----------------------------------------------------------------------------------------------------------
Round 12 found fix pass 10's rules sound, and three MINORs one level past them. No review round follows, so each change
is small, and each has a FAIL and a PASS case (checker-r12/new_mutants_r12.py). The 37 files of fix pass 10's survey,
and the called file fix pass 10 fetched, meet every new rule (checker-r12/evidence/survey_fp11.out).

- M12-A (``read_regular``): every file this checker reads (a workflow, the file an allow-listed job calls, the template
  and the pins file) is read only when it is a regular file, at most its bound. ``lstat`` decides before anything is
  opened, so no device is ever opened; the file is then opened without following a link and without blocking
  (``O_NOFOLLOW | O_NONBLOCK``), and ``fstat`` must find a regular file again. A symlink, a FIFO, a socket, a device or a
  directory is refused (``FileRefused``): that workflow fails and the next is judged, and a refused template or pins
  file stops the run with nothing checked. A symlink to a regular file is refused too, by choice: git holds a link's
  target path at that path, not the file it names, so bytes read through a link are not the bytes the tree holds there,
  and no template, port, simulation or driver uses one (round 12's control C12-1 passed through one; it fails now). The
  called file is read within the workflows' bound (``MAX_WORKFLOW_BYTES``; ``read_bytes()`` had none), the pins file
  within ``MAX_PINS_BYTES``. Round 12's N12-1 to N12-3 (a called file, or a workflow, linked to ``/dev/zero`` or
  ``/dev/stdin``) held the run for good or until memory ran out; each now fails at once, and the next workflow is
  judged.
- M12-B: ``ENV_FILE_NAMES`` adds the index forms ``github['env']`` and ``github['path']``, and the prefix
  ``_runner_file_c`` in place of ``_runner_file_commands`` (round 12's N12-4b and N12-4c), which none of the 37 files
  holds. The rule stays a text check of literal spellings alone ("What this cannot see", below).
- M12-C (``shown()``, ``quoted()``, ``fold()``, ``said()``, ``clipped()``): every value read from a workflow that a
  message names (alone, in a list or a mapping, as a place, as a line of a pin mismatch's diff, or quoted by a tool's
  own message) is cut, to ``SHOWN_CHARS`` characters then the count of the rest (a diff line at ``DIFF_CHARS``; a
  tool's message at 300 characters, a crash's at 200, as fix pass 10 cut them), and folded: a run of more than
  ``BLANKS_KEPT`` blanks (spaces, or characters a terminal draws blank: ``BLANKS``) is written as its count,
  ``<N blanks>``, so no two values that differ in their blanks print alike. Every
  ``!r`` of such a value is ``quoted()`` now, which prints what ``!r`` printed for a value of at most ``SHOWN_CHARS``
  characters with no such run. Round 12's N12-5b (an upload input's key of blanks, holding a PASS line and a summary
  each placed where a terminal of 80, 100 or 200 columns begins a row) prints ``'<200 blanks>'... (12570 more
  characters)``, and tmux shows no fake row at 80x50 or 200x50. What remains is below ("What a terminal does").
- n12-a (``place()``): a place longer than ``SHOWN_CHARS`` keeps its first ``PLACE_HEAD`` and its last ``PLACE_TAIL``
  characters and counts those between, so places that share a long prefix still print apart (round 12's N12-6).
- n12-b: the concurrency claims are worded as they hold: the group is one no other publisher's file uses, for the refs
  the publishers use (above).
- n12-c, recorded: a step id repeated in one job passes this checker, and GitHub refuses the file, so it never runs
  (round 12's N12-10; not a bypass). n12-d: ``check_pinned_steps`` holds the names it has seen in a set. n12-e: a file
  refused for its kind or its size is reported as refused before it is parsed, not as a YAML load failure. n12-f,
  recorded: a ``timeout-minutes`` value is not read (``OPTIONAL_JOB_KEYS``): fail-closed, but for a timeout between two
  uploads, R4-4's availability harm (round 12's N12-8).

What this cannot see
--------------------
- What a pin does: equality is all this proves. The pinned script's fetch, retries, installs and import check are each
  port's review's business, read under both shells this admits (``bash -e {0}``, and ``bash --noprofile --norc -eo
  pipefail {0}`` with ``shell: bash``). A later ``pip install`` of another package from PyPI that a pin makes runs that
  package's code; ``python -c`` code can run anything.
- GitHub's YAML parser: this reads PyYAML's events, typed as GitHub's reader types them (fix pass 8). The refusals
  above cover the differences known (line breaks, duplicate and merge keys, tags); another difference in a scalar's own
  grammar (a folded or quoted scalar's folding, a double-quoted scalar's escapes) would let the runner write a text other
  than the one compared, and none is known (round 9's fuzz found none against GitHub's lineage). A rule holding a
  ``run`` to a literal block (``|``) or to one line was considered and not made: the juniper-ml simulation's install
  step (a seed) and, at the window, canopy's smoke step and round 7's W3, W4 and W7 are single-quoted scalars over
  several lines, the YAML dump's choice (tmp/sweep/checker-r8/evidence/survey_scalar_styles.out); a port written by
  hand uses ``|``.
- The runner: this assumes it writes the ``run`` string, its expressions substituted (a pin holds none), to a file that
  bash runs unchanged, as actions/runner's script handler does for bash.
- What an action's code does: since fix pass 9 every action of the chain runs at the template's exact commit SHA, which
  pins a JavaScript or composite action's own code; a SHA the template's review took from a fork (round 10's R10-8:
  GitHub's API serves a fork-only commit under the upstream name) would pass here, as the template's choice. The SHA
  does not pin a container image an action runs by a tag (round 11's M11-E): ``pypa/gh-action-pypi-publish`` at
  ``7245906f`` is a composite action whose step writes a Docker action running
  ``docker://ghcr.io/pypa/gh-action-pypi-publish:<the action's ref>``, and the code that exchanges the job's OIDC token,
  makes the attestations and runs twine (``oidc-exchange.py``, ``attestations.py``, ``twine-upload.sh``) lives in that
  image, under a registry tag that can be pushed again with no SHA in any workflow changing. A residual for plan
  v1.15.18: accept it in writing, or record the image digest the template's review saw.
- What an allow-listed job's called workflow does: its sha256 is all this proves, as for a pin; the file is its own
  review's business, and an operator must fetch it beside the workflow, as a regular file (a missing file fails, and
  since fix pass 11 so does a link).
- The build job's steps up to the build (round 11's M11-C): each repository's own business, its checkout's inputs among
  them (a token, another repository or ref, a fetch depth: only the actions they run are judged, since fix pass 9).
  They can change what every later step of the build job runs, the window's twine check and ``Record SHA256SUMS``
  among them: through ``$GITHUB_ENV`` or ``$GITHUB_PATH`` (since fix pass 10 a build step naming either is refused, a
  text check of literal spellings alone: a name computed from parts (round 11's R11-1), another file command's
  directory (``$(dirname "$GITHUB_OUTPUT")``), a glob, another expression's spelling (``github[format(...)]``,
  ``toJSON(github)``) or another shell passes it (round 12's N12-4a); fix pass 11 adds ``github['env']``,
  ``github['path']`` and ``_runner_file_c``, round 12's N12-4b and N12-4c. Only pinning the steps before the build,
  as install scripts are pinned, closes the class: plan v1.15.18), a background process, or a tool they install in
  place of ``build`` or ``twine``. And they can make the files ``<PUBLISH_PACKAGE>-dist`` carries, through the build or a
  background process (since fix pass 10 upload-artifact is admitted only as the template's last step). Nothing there
  reaches a job holding id-token but the artifact's bytes, which the repository's own build decides anyway, and which
  the TestPyPI install check then tests. A port's review reads every step before the build as code that runs inside
  the window.
- Unchanged from earlier passes: files a sparse checkout brings (in cone mode, with its parent directories' own files)
  are not read; and juniper-ml's tag assert pastes ``${{ github.ref }}`` into its window script by design (its own tests
  pin it). A port's review still reads its install script and its build job.
- What a terminal does with printable text: every line this checker prints holds printable text alone (fix pass 10),
  and no text a workflow holds begins one. Since fix pass 11 every value a line names is cut and folded (above), so no
  value fills a row with blanks, or shows more than its first ``SHOWN_CHARS`` characters (a diff line ``DIFF_CHARS``, a
  tool's message 300).
  A terminal still wraps a line wider than itself, and where a wrap falls inside a value, the row begins with the
  workflow's own text: a refused workflow can still show a row that begins like a PASS line, or like a summary, inside
  one of its FAIL messages, in any terminal narrower than that line, which most messages are (at 80 columns, 130
  characters of one value place one: checker-r12's F11-5b; round 12's M12-C). The exit status, and the lines as
  printed, are the verdict, and the last line printed is the summary.
- A link in a directory above a file: ``lstat`` refuses a link at the file's own name, and a link among the
  directories of its path is followed (an operator's own path may pass through one). A port's tree that makes
  ``.github`` or ``workflows`` a link is read through it, though git holds the link there, not that directory's files
  (fix pass 11, M12-A).
- Another workflow of the repository: it can still name this workflow's concurrency group, or cancel its run through
  the API (``actions: write``); this checker reads only the workflows it is given. Either costs availability, which the
  republish ladder recovers, never the artifact's bytes or a credential (round 11's starting point 6).
- The template's own residual (SWEEP item 28, recorded by fix pass 9, not changed): no publish job ties the version in
  SHA256SUMS to the release tag, so files of another version that reach the artifact are published; round 10's R10-7
  did that through an extra job, which fix pass 9 refuses.

    python3 -I util/ad-hoc/2026-11-23_publish_port_template_identity.py --repo REPO --template <cascor publish.yml> [--pins PINS] WORKFLOW [WORKFLOW ...]

``--repo`` names the repository every WORKFLOW belongs to (one of ``REPOS``); ``--pins`` the pins file, when not the one
beside this checker.

Exit status: 0 when every workflow passes every check; 1 otherwise (each failure is printed, a crash on one workflow
among them), or when the pins file or the template is refused (nothing is checked).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import yaml

REUSE = "Reuse an earlier attempt's artifact"
REUSE_IF = "steps.reuse.outputs.reuse != 'true'"
RECORD = "Record SHA256SUMS"
UPLOAD = "Upload dist artifacts"
DOWNLOAD = "Download dist artifacts"
VERIFY_DIST = "Verify the dist against SHA256SUMS"
TESTPYPI_AFTER = "Verify TestPyPI serves exactly these files"
TESTPYPI_BEFORE = "Verify TestPyPI still serves exactly these files"
PYPI_AFTER = "Verify PyPI serves exactly these files"
REPUBLISH = "republish"
INSTALL_NAME = "Verify the TestPyPI install"
RELEASE_GATE = "Require a GitHub Release for this tag"
PUSH_ONLY = "github.event_name == 'push'"
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
PARAMETERS = {"PUBLISH_PACKAGE", "PUBLISH_DIST_DIR", "PUBLISH_TAG_PREFIX"}
RETENTION_DAYS = 90
#: The two build guards the template allows, with PUBLISH_TAG_PREFIX filled in: a release of the package's own tag; or
#: that, or a plain dispatch from the package's own tag (a sub-package publisher's re-fire), never the republish one.
GUARD_FORMS = (
    "startsWith(github.event.release.tag_name, '{prefix}')",
    "(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))",
)
BUILD_COMMAND = re.compile(r"\bpython3?\s+-m\s+build\b|\bpip3?\s+wheel\b|\buv\s+build\b|\bsetup\.py\s+(?:sdist|bdist_wheel)\b")
#: R4-6: the repositories whose publishers port the template; ``--repo`` names one, and only the operator decides it.
REPOS = ("juniper-canopy", "juniper-cascor", "juniper-cascor-client", "juniper-cascor-worker", "juniper-data", "juniper-data-client", "juniper-ml", "juniper-recurrence")
#: juniper-ml's seven publishers: the meta-package and its six sub-packages.
ML_PACKAGES = frozenset({"juniper-ml", "juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core"})
#: F1 of the round-2 review: what a step between the build and Record SHA256SUMS may run, as its exact commands, since
#: what the build wrote is what the record hashes. ``twine check`` only reads the dist. The two others run more, and
#: each is admitted only where its repository's own tests pin it (R4-6): juniper-ml's tag assert runs a script of the
#: checkout's own (``util/assert_release_tag.bash``), in juniper-ml alone; canopy's smoke test installs the built wheel
#: and its dependencies from PyPI into a venv under ``$RUNNER_TEMP``, so code from PyPI runs in the build job before
#: the record, in juniper-canopy alone.
TWINE_CHECK = ["twine check dist/*"]
#: juniper-ml's tag assert (M5's fix there: the built version must match the tag); ``{tool}`` is ``util/`` at the root
#: and ``../util/`` in a sub-package's directory, ``{prefix}`` the workflow's PUBLISH_TAG_PREFIX.
TAG_ASSERT = '{tool}assert_release_tag.bash --ref "${{{{ github.ref }}}}" --dist-dir dist --expect-prefix {prefix}'
#: juniper-canopy's import smoke test of the built wheel, from a directory outside the checkout.
CANOPY_SMOKE = [
    'python -m venv "${RUNNER_TEMP}/smoke"',
    '"${RUNNER_TEMP}/smoke/bin/pip" install --quiet dist/*.whl',
    'mkdir -p "${RUNNER_TEMP}/smoke-cwd"',
    'cd "${RUNNER_TEMP}/smoke-cwd"',
    '"${RUNNER_TEMP}/smoke/bin/python" "${GITHUB_WORKSPACE}/util/wheel_import_smoke.py"',
]
WINDOW_STEP_KEYS = {"name", "if", "run"}
#: F4: env keys no workflow, job, container or step may set.
ENV_PREFIXES = ("PIP_", "PYTHON", "UV_", "HASH_CHECK_")
#: The NIT of the round-4 review: PYTHON* keys a build step's env may set (the build job's own env, too, until fix pass
#: 8's key set). Each changes how Python reports, encodes or hashes, never what it imports or runs; any other PYTHON*
#: key stays refused there.
BUILD_PYTHON_ENV = frozenset({"PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "PYTHONIOENCODING", "PYTHONUTF8"})
#: What the install job may use, and the one env an install step may set (publish.yml's tag, N1).
INSTALL_ACTIONS = ("actions/setup-python", "actions/checkout")
INSTALL_STEP_ENV = {"RELEASE_TAG": "${{ github.event.release.tag_name }}"}
#: Fix pass 7: the keys GitHub defines for a step. An install step holding any other (``Run``, a look-alike ``run``) is
#: refused, so no step there runs a script under a key this checker does not read.
STEP_KEYS = frozenset({"name", "id", "uses", "with", "run", "env", "shell", "if", "continue-on-error", "working-directory", "timeout-minutes"})
#: Fix pass 8 (B9-1, M9-A): the keys each job of the template's chain carries, as juniper-cascor's own test pins them
#: (src/tests/unit/test_publish_one_artifact.py: BUILD_JOB_KEYS, PUBLISH_JOB_KEYS for the TestPyPI and PyPI jobs,
#: INSTALL_JOB_KEYS, REPUBLISH_JOB_KEYS). A sub-package's build job also carries ``defaults``, exactly
#: ``{run: {working-directory: <PUBLISH_PACKAGE>}}``, as that test requires of cascor's sub-package publishers.
CHAIN_JOB_KEYS = {
    "build": frozenset({"name", "if", "runs-on", "permissions", "steps"}),
    "publish": frozenset({"name", "needs", "runs-on", "environment", "permissions", "steps"}),
    "install": frozenset({"name", "needs", "runs-on", "permissions", "steps"}),
    "republish": frozenset({"name", "if", "runs-on", "environment", "permissions", "steps"}),
}
#: The key a job of the chain may add (that test's OPTIONAL_JOB_KEYS): a job its timeout stops fails, so nothing that
#: needs it runs. The republish job takes none here: it is compared whole with the template's. Fix pass 11 (n12-f),
#: recorded: its value is not read (round 12's N12-8, ``timeout-minutes: 1`` on the PyPI job, passes): fail-closed, but
#: for a timeout between two uploads, R4-4's availability harm, which the republish ladder recovers.
OPTIONAL_JOB_KEYS = frozenset({"timeout-minutes"})
#: Fix pass 8 (M9-B): setup-python's one admitted input, ``python-version``, holds a CPython version written as a string,
#: as the template writes it ("3.12"; canopy's port uses "3.14"). Unquoted, YAML makes 3.10 the number 3.1.
SETUP_PYTHON = "actions/setup-python"
SETUP_PYTHON_VERSION = re.compile(r"3\.[0-9]+")
#: Fix pass 9 (B10-1): the keys an upload step (pypa/gh-action-pypi-publish) holds, exactly, as the template's do; and the
#: inputs its ``with`` may add to the template's, each only as the boolean true (cascor's sub-package publishers add
#: verbose, three ports attestations, the action's default). Every other key and input is refused.
UPLOAD_STEP_KEYS = frozenset({"name", "uses", "with"})
UPLOAD_OPTIONAL_INPUTS = ("verbose", "attestations")
#: The pinned publish action's deprecated underscore aliases (action.yml at 7245906f), each read whenever its kebab-case
#: input is empty (``repository-url: ${{ inputs.repository-url || inputs.repository_url }}``): named in messages only.
UPLOAD_ALIASES = ("repository_url", "packages_dir", "verify_metadata", "skip_existing", "print_hash")
#: Fix pass 9 (B10-3, the owner's ruling "Pin template SHAs"): how the template names each action in its chain's jobs,
#: owner/repo at a full commit SHA, as git writes one (40 lowercase hex characters).
PINNED_USES = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+@[0-9a-f]{40}")
#: Fix pass 9 (B10-2): the jobs a publisher may hold beside the chain's five, each exactly. (repo, workflow file, job id)
#: -> the job as GitHub types it, and the reusable workflow it calls: its file name, read beside the workflow, and that
#: file's sha256. Every other job is refused. juniper-data's notify-consumers, as its publish.yml holds it at main
#: 6b734fd9 (its notify-consumers.yml there: blob ab0cade2, 11039 bytes, run steps alone under permissions: {}).
EXTRA_JOBS = {
    ("juniper-data", "publish.yml", "notify-consumers"): {
        "job": {
            "name": "Notify consumer repos",
            "needs": "pypi",
            "permissions": {},
            "uses": "./.github/workflows/notify-consumers.yml",
            "with": {"version": "${{ github.event.release.tag_name }}"},
            "secrets": {"CROSS_REPO_DISPATCH_TOKEN": "${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}"},
        },
        "calls": ("notify-consumers.yml", "e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078"),
    },
}
#: The retry loop's header: its values listed (``1 2 3 4 5``), or (a NIT of the round-4 review) ``$(seq N)`` or
#: ``$(seq 1 N)``. Read from a pin's lines by ``lag_problems``.
LOOP_HEADER = re.compile(r"for (\w+) in (?:((?:\d+ )*\d+)|\$\(seq (?:1 )?(\d+)\)); do")
#: The lag error the template prints after its last try, exactly (the NIT of the round-4 review): the operator signature
#: docs/ci_cd/MANUAL.md quotes, with the fetch's package and version variable and the loop's own try count.
LAG_ERROR = 'echo "::error::{package} ${{{version}}} is not installable from TestPyPI after {tries} tries (index lag?): Re-run failed jobs; a real failure repeats"'
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
#: The one path an install job's checkout may hold, as the ports' sparse checkouts name it: the file the version is read
#: from (in cone mode, git adds each parent directory's own files, never a subdirectory such as .config/pip/).
SPARSE_PATH = re.compile(r"(?:juniper[-_][a-z0-9_-]+/){0,2}(?:pyproject\.toml|_version\.py)")
#: The characters Python's ``str.splitlines()`` (and so ``commands()``) ends a line at besides ``\n``; bash ends a line at
#: ``\n`` alone. Built from code points, so that none is written into this file.
LINE_BREAKS = frozenset(chr(code) for code in (0x0B, 0x0C, 0x0D, 0x1C, 0x1D, 0x1E, 0x85, 0x2028, 0x2029))
#: Fix pass 5 (R6-F1): the NUL byte, which bash drops from what it reads. Built from its code point, as above.
NUL = chr(0)
#: R5-F4: env keys bash reads before a step's first line: ``BASH_ENV`` (and ``ENV`` in sh mode) name a file it runs,
#: ``SHELLOPTS`` and ``BASHOPTS`` turn options on (``SHELLOPTS=noexec`` runs nothing; ``xtrace`` expands ``PS4``).
SHELL_ENV = frozenset({"BASH_ENV", "ENV", "BASHOPTS", "SHELLOPTS"})
#: Fix pass 7: the pins file (its name, beside this checker), its format and each pin's fields.
PINS_FILE = "2026-11-24_publish_port_install_pins.json"
PINS_FORMAT = "juniper-publish-install-pins/1"
PIN_FIELDS = frozenset({"repo", "workflow", "step", "package", "source", "sha256", "lines"})
#: A workflow file's name, as a pin's key holds it.
WORKFLOW_FILE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.ya?ml")
#: The most lines of a pin mismatch's unified diff that are printed.
DIFF_LINES = 24
#: Fix pass 10 (M11-B's class): the largest workflow file this checker reads; a larger one is refused before it is
#: parsed, so every rule works on a bounded size (the largest publisher is 52,353 bytes).
MAX_WORKFLOW_BYTES = 256 * 1024
#: Fix pass 10 (M11-A): a string ``shown()`` prints as it stands, letters, digits and ``._/@+-`` alone (its repr would
#: only add quotes); every other value is printed as its repr.
PLAIN = re.compile(r"[A-Za-z0-9._/@+-]+")
#: The most places a refusal of fix pass 10 lists (``few()``); the rest are counted.
FEW = 12
#: Fix pass 10 (M11-B's class): the most characters of one value (``shown()``), or of one place in the document
#: (``place()``), that this checker holds for a message; the rest is cut. A job's id is named once for each of its steps,
#: and a key's text was copied into the place of every node beneath it, so a long key grew as the square of the file.
SHOWN_CHARS = 200
#: Fix pass 11 (n12-a): a place longer than SHOWN_CHARS keeps its first PLACE_HEAD and its last PLACE_TAIL characters.
PLACE_HEAD, PLACE_TAIL = 140, 40
#: Fix pass 11 (M12-C): the most characters of one line of a pin mismatch's diff that are printed (the longest line of
#: a pin is 436 characters); the rest is counted.
DIFF_CHARS = 1000
#: Fix pass 11 (M12-C): the characters a terminal draws as blank cells that a printed value can hold (every other
#: character but printable text is escaped already, by visible() and repr): the space, U+2800 BRAILLE PATTERN BLANK, and
#: the Hangul fillers U+115F, U+1160, U+3164 and U+FFA0. Built from code points, so that none is written into this file.
BLANKS = "".join(chr(code) for code in (0x20, 0x2800, 0x115F, 0x1160, 0x3164, 0xFFA0))
#: The longest run of them that a printed value keeps as it stands (fold()); a longer run is written as its count. In
#: the 37 files, no key or name holds two, a pin's line four, a run script sixteen.
BLANKS_KEPT = 8
BLANK_RUN = re.compile(f"[{re.escape(BLANKS)}]{{{BLANKS_KEPT + 1},}}")
#: Fix pass 11 (M12-A): the most bytes of the pins file this checker reads (34,258 at fix pass 11): like the template,
#: an operator's input, read through the same guard as a workflow (read_regular()).
MAX_PINS_BYTES = 1024 * 1024
#: Fix pass 10 (M11-C): the action the build job runs only as its last step, the template's UPLOAD; and the names of the
#: runner's file commands for the environment and the PATH, which no build step's run or env may name (in any case).
#: Fix pass 11 (M12-B): the index forms github['env'] and github['path'], and the prefix _runner_file_c (of
#: _runner_file_commands), round 12's N12-4b and N12-4c; literal spellings alone (the docstring's "What this cannot see").
UPLOAD_ARTIFACT = "actions/upload-artifact"
ENV_FILE_NAMES = ("github_env", "github_path", "github.env", "github.path", "github['env']", "github['path']", "_runner_file_c")
#: Fix pass 10 (M11-D): the workflow's concurrency group, when it sets one: its own file's stem and the ref.
CONCURRENCY_GROUP = "{stem}-${{{{ github.ref_name }}}}"
#: Fix pass 10 (M11-B): why an anchor or an alias is refused at load.
ALIAS_REASON = "no template or port uses a YAML anchor or alias, so each is refused at load, before any rule walks the document: the loaded workflow is then a tree no larger than its file (round 11's M11-4, an alias bomb of 49 KB, held the run past 120 s, and the next workflow was never judged)"
#: Fix pass 8 (M9-C): how GitHub's reader types a plain scalar, transcribed from actions/runner's
#: YamlObjectReader.AllowLiteral (MatchNull, MatchBoolean, MatchInteger, MatchFloat, tried in that order: YAML 1.2's
#: core schema), each form exactly: tag, form, and its value. Any other plain scalar is a string. PyYAML's own resolvers
#: are YAML 1.1's (``yes``, ``no``, ``on`` and ``off`` booleans, ``0132`` octal, ``1:30`` base 60, ``1_000``, ``0b1``,
#: dates), where GitHub reads text (or, for ``0132``, 132), so this checker does not use them. GitHub reads a hexadecimal
#: or octal integer as 32 bits (above 0x7FFFFFFF it turns negative, or is refused), so one above that is refused here.
#: Every integer is a double to GitHub, so a decimal beyond 2**53 is read as the double it rounds to.
STR_TAG = "tag:yaml.org,2002:str"


def github_int(text: str) -> "int | float":
    """A plain scalar GitHub reads as an integer: decimal (a sign and leading zeros allowed, so ``0132`` is 132),
    ``0x`` hexadecimal or ``0o`` octal."""
    number = int(text[2:], 16) if text.startswith("0x") else int(text[2:], 8) if text.startswith("0o") else int(text)
    if text.startswith(("0x", "0o")) and number > 0x7FFFFFFF:
        raise ValueError("GitHub reads a hexadecimal or octal integer as 32 bits, so above 0x7FFFFFFF it turns negative or is refused")
    return number if abs(number) <= 2**53 else float(text)


def github_float(text: str) -> float:
    """A plain scalar GitHub reads as a float (its special forms, or a decimal with an optional exponent)."""
    body = text.lstrip("+-")
    if body in (".inf", ".Inf", ".INF"):
        return float("-inf") if text.startswith("-") else float("inf")
    if body in (".nan", ".NaN", ".NAN"):
        return float("nan")
    return float(text)


#: tag -> (its plain form, its value, the first characters the form can start with: PyYAML picks a plain scalar's
#: resolvers by its first character, the empty scalar by "").
GITHUB_SCALARS = {
    "tag:yaml.org,2002:null": (re.compile(r"(?:~|null|Null|NULL)?\Z"), lambda text: None, ["~", "n", "N", ""]),
    "tag:yaml.org,2002:bool": (re.compile(r"(?:true|True|TRUE|false|False|FALSE)\Z"), lambda text: text in ("true", "True", "TRUE"), list("tTfF")),
    "tag:yaml.org,2002:int": (re.compile(r"(?:[-+]?[0-9]+|0x[0-9a-fA-F]+|0o[0-7]+)\Z"), github_int, list("-+0123456789")),
    "tag:yaml.org,2002:float": (re.compile(r"(?:[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)|[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)\Z"), github_float, list("-+.0123456789")),
}


def frozen(value: object) -> object:
    """Fix pass 10 (M11-B's class): VALUE, a list or a mapping as this loader builds them, as a hashable value that
    equals another's exactly when the two values are equal: a list as its items in a tuple, a mapping as the frozenset
    of its items, each tagged with its kind."""
    if isinstance(value, list):
        return ("list", tuple(frozen(item) for item in value))
    if isinstance(value, dict):
        return ("dict", frozenset((frozen(key), frozen(item)) for key, item in value.items()))
    return value


class UniqueKeyLoader(yaml.SafeLoader):
    """PyYAML's safe loader, reading scalars as GitHub's reader types them (fix pass 8, M9-C) and refusing what YAML
    parsers resolve differently (fix pass 7).

    - Typing (``GITHUB_SCALARS``): a plain scalar is null, a boolean, an integer or a float exactly where GitHub's reader
      makes it one, and a string otherwise (``on``, ``no`` and ``1:30`` are text; ``0132`` is 132). A tag is admitted
      where GitHub's reader admits it: ``!!str`` in any style, and ``!!null``, ``!!bool``, ``!!int`` or ``!!float`` on a
      plain scalar holding that type's form. Every other tag is refused: GitHub refuses it on a scalar (``!``, ``!!binary``,
      ``!!timestamp``), and it ignores one on a sequence or a mapping, where PyYAML would build a set or pairs
      (``!!set``, ``!!omap``, ``!!pairs``).
    - A mapping that repeats a key, by its text or by the value made of it (PyYAML keeps the last value, and another
      parser need not; GitHub refuses keys equal but for case), and a merge key (a plain ``<<``), which a YAML 1.1
      parser applies and GitHub's reader keeps as a key. Since fix pass 10 the keys before are held in sets, so the
      check is linear in a mapping's size (a list made it quadratic).
    - Fix pass 10 (M11-B): an anchor on any node, and an alias, before the node is composed (``ALIAS_REASON``)."""

    yaml_implicit_resolvers: "dict[str, list]" = {}  # GITHUB_SCALARS' forms alone (below); PyYAML's are not inherited

    def compose_node(self, parent, index):
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent):
            raise yaml.composer.ComposerError(None, None, f"found an alias ({event.anchor!r}): {ALIAS_REASON}", event.start_mark)
        if getattr(event, "anchor", None) is not None:
            raise yaml.composer.ComposerError(None, None, f"found an anchor ({event.anchor!r}): {ALIAS_REASON}", event.start_mark)
        tag = getattr(event, "tag", None)
        if tag is not None and tag != STR_TAG and not (isinstance(event, yaml.ScalarEvent) and event.style is None and tag in GITHUB_SCALARS):
            raise yaml.composer.ComposerError(None, None, f"found the tag {tag!r}: GitHub's reader admits !!str, and !!null, !!bool, !!int or !!float on a plain scalar, and no other tag on a scalar (on a sequence or a mapping it ignores a tag, where PyYAML builds a set or pairs)", event.start_mark)
        return super().compose_node(parent, index)

    def construct_github(self, node):
        """A scalar under one of GITHUB_SCALARS' tags (implicit, or an explicit tag on a plain scalar), typed as GitHub
        types it; text that is not the tag's form is refused, as GitHub refuses it."""
        pattern, convert, _ = GITHUB_SCALARS[node.tag]
        try:
            if not pattern.match(node.value):
                raise ValueError(f"GitHub's reader refuses it for the tag {node.tag}")
            return convert(node.value)
        except ValueError as exc:
            raise yaml.constructor.ConstructorError(None, None, f"found {node.value!r}: {exc}", node.start_mark) from None

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            # Fix pass 10 (M11-B's class): sets, so the check is linear; a key whose value is unhashable (a list or a
            # mapping, which PyYAML then refuses as a key) is held as frozen(value), equal to another's exactly when the
            # values are equal, in a set of its own (a list never equals a hashable value). Compared with each unhashable
            # key before it, the check grew as their square (a file of 10,000 list keys took 3.5 s, of 5,000 1.6 s).
            texts: set[str] = set()
            values: set[object] = set()
            unhashable: set[object] = set()
            for key_node, _ in node.value:
                if isinstance(key_node, yaml.ScalarNode) and key_node.style is None and key_node.value == "<<":
                    raise yaml.constructor.ConstructorError("while reading a mapping", node.start_mark, "found a merge key (<<), which a YAML 1.1 parser applies (PyYAML's own loader among them) and GitHub's reader keeps as a key", key_node.start_mark)
                text = key_node.value if isinstance(key_node, yaml.ScalarNode) else None
                value = self.construct_object(key_node, deep=True)
                try:
                    hash(value)
                except TypeError:
                    held, pool = frozen(value), unhashable
                else:
                    held, pool = value, values
                seen = held in pool
                pool.add(held)
                if (text is not None and text in texts) or seen:
                    raise yaml.constructor.ConstructorError("while reading a mapping", node.start_mark, f"found the key {text if text is not None else value!r} twice: PyYAML keeps the last value, and another parser need not", key_node.start_mark)
                if text is not None:
                    texts.add(text)
        return super().construct_mapping(node, deep=deep)


for _tag, (_form, _, _first) in GITHUB_SCALARS.items():
    UniqueKeyLoader.add_implicit_resolver(_tag, _form, _first)
    UniqueKeyLoader.add_constructor(_tag, UniqueKeyLoader.construct_github)


def load_text(text: str) -> dict:
    """TEXT's single YAML document through ``UniqueKeyLoader``, typed as GitHub's reader types it (since fix pass 8 the
    key ``on`` is the text ``on``, as GitHub reads it, and needs no restoring); a document that is not a mapping is
    refused."""
    loader = UniqueKeyLoader(text)
    try:
        data = loader.get_single_data()
    finally:
        loader.dispose()
    if not isinstance(data, dict):
        raise yaml.YAMLError(f"the document is {type(data).__name__}, not a mapping")
    return data


class FileRefused(OSError):
    """Fix pass 11 (M12-A, n12-e): a file refused before any of it is parsed, for its kind (not a regular file) or for
    its size (more than its bound). An OSError, so every reader's own refusal catches it; each gives it its own words."""


def file_kind(mode: int) -> str:
    """Fix pass 11 (M12-A): what MODE, an ``lstat`` or ``fstat`` mode, names, in words."""
    kinds = ((stat.S_ISREG, "a regular file"), (stat.S_ISLNK, "a symlink"), (stat.S_ISDIR, "a directory"), (stat.S_ISFIFO, "a FIFO (a named pipe)"), (stat.S_ISSOCK, "a socket"), (stat.S_ISCHR, "a character device"), (stat.S_ISBLK, "a block device"))
    return next((kind for test, kind in kinds if test(mode)), "a file of no kind this checker knows")


def read_regular(path: Path, limit: int, bound: str) -> bytes:
    """Fix pass 11 (M12-A): PATH's bytes, when PATH is a regular file of LIMIT bytes or fewer (BOUND names the limit);
    anything else is refused (``FileRefused``) before any of it is parsed. ``lstat`` decides first, so nothing but a
    regular file is ever opened (a device never is); the file is then opened without following a link and without
    blocking (``O_NOFOLLOW | O_NONBLOCK``), and ``fstat`` must find a regular file again, so a swap between the two is
    refused too. No more than LIMIT and one byte is read. A symlink is refused even when it names a regular file: git
    holds a link's target path at that path, not the file it names, so the bytes read through a link are not the bytes
    the tree holds there (round 12's C12-1 passed through one). A FIFO, a socket or a device could hold the read up for
    good, or never end it (round 12's N12-1 to N12-3: links to /dev/stdin and /dev/zero)."""
    kind = file_kind(os.lstat(path).st_mode)
    if kind == "a regular file":
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0))
        with os.fdopen(descriptor, "rb") as handle:
            kind = file_kind(os.fstat(handle.fileno()).st_mode)
            raw = handle.read(limit + 1) if kind == "a regular file" else b""
    if kind != "a regular file":
        raise FileRefused(f"it is {kind}, not a regular file: this checker reads a regular file alone, by lstat before anything is opened, then opened without following a link and without blocking (a link names bytes the tree does not hold at its path; a FIFO, a socket or a device can hold the read up for good, or never end it: round 12's M12-A)")
    if len(raw) > limit:
        raise FileRefused(f"the file holds more than {limit} bytes, the most this checker reads ({bound}), so it is refused before it is parsed or hashed: every cost this checker has grows with a file's size")
    return raw


def read_text(path: Path) -> str:
    """Fix pass 10 (M11-B's class): PATH's text, read as bytes and decoded as UTF-8 (no newline translation); a file of
    more than ``MAX_WORKFLOW_BYTES`` is refused before it is parsed, and no more than that and one byte is read. Since
    fix pass 11 through ``read_regular()``, so anything but a regular file is refused before it is read (M12-A)."""
    return read_regular(path, MAX_WORKFLOW_BYTES, "MAX_WORKFLOW_BYTES; the largest publisher is 52,353 bytes").decode("utf-8")


def load(path: Path) -> dict:
    """PATH's YAML, read by ``read_text`` (bytes, decoded, no newline translation, its size bounded), through
    ``UniqueKeyLoader``."""
    return load_text(read_text(path))


def file_problems(raw: str) -> "list[str]":
    """Fix pass 7, its message made true by fix pass 8 (n9-a): a character other than printable text, a tab or a line
    break (LF, or CR LF) anywhere in the workflow file is refused wherever it stands, as defence in depth. Round 9 ran
    GitHub's parser lineage: a raw U+0085 is a line break to PyYAML and to GitHub's YamlDotNet alike, and only a YAML 1.2
    parser such as Node's ``yaml`` keeps it in the line; a byte order mark (PyYAML strips one at the file's start) or a
    no-break space in a comment changes nothing PyYAML reads. Each is refused all the same: YAML parsers do not all agree
    on such characters, and a reviewer may see one as nothing, a space or a line break."""
    found = sorted({f"U+{ord(char):04X}" for char in raw.replace("\r\n", "\n") if not (char.isprintable() or char in "\t\n")})
    if not found:
        return []
    return [f"the workflow file holds a character other than printable text, a tab or a line break (LF, or CR LF) ({found}), refused wherever it stands, harmless there or not: YAML parsers do not all agree on such characters (a raw U+0085 is a line break to PyYAML and to GitHub's YamlDotNet, and not to a YAML 1.2 parser such as Node's yaml), and a reviewer may see one as nothing, a space or a line break (a byte order mark, a no-break space, a lone CR)"]


def lone_surrogate(text: str) -> bool:
    """Whether TEXT holds a lone surrogate (U+D800 to U+DFFF), which a double-quoted ``\\uD800`` escape loads as."""
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)


def unprintable(text: str) -> "set[str]":
    """Fix pass 10 (M11-A): the code points in TEXT of every character but printable text, a tab and a newline, a lone
    surrogate left to its own rule (fix pass 9's)."""
    return {f"U+{ord(char):04X}" for char in text if not (char.isprintable() or char in "\t\n" or 0xD800 <= ord(char) <= 0xDFFF)}


def visible(text: str) -> str:
    """Fix pass 10 (M11-A): TEXT with every character but printable text written as Python's own escape for it, as repr
    writes it: C0 and C1 controls, DEL, line and paragraph separators, format characters and surrogates among them."""
    return "".join(char if char.isprintable() else repr(char)[1:-1] for char in text)


def fold(text: str) -> str:
    """Fix pass 11 (M12-C): TEXT with each run of more than ``BLANKS_KEPT`` blanks (``BLANKS``: spaces, and characters a
    terminal draws blank) written as its count, ``<N blanks>``: a printed value then never fills a terminal's row with
    blanks (round 12's N12-5b pushed the real FAIL line off the screen with blank rows), and no two values that differ
    in their blanks print alike."""
    return BLANK_RUN.sub(lambda run: f"<{len(run.group())} blanks>", text)


def shown(value: object, bare: bool = True) -> str:
    """Fix pass 10 (M11-A): VALUE, read from a workflow, as a message names it: a string of letters, digits and ``._/@+-``
    alone as it stands (its repr would only add quotes; not when BARE is false, for ``quoted()``), every other value as
    its repr, which escapes each character but printable text. At most ``SHOWN_CHARS`` characters of the string, or of
    the repr, then the count of the rest (M11-B's class): a message names a job's id once for each of its steps. Since
    fix pass 11 (M12-C) folded (``fold()``)."""
    if isinstance(value, str):
        head = value[:SHOWN_CHARS]
        text, rest = (head if bare and PLAIN.fullmatch(head) else repr(head)), len(value) - len(head)
    else:
        text = repr(value)
        text, rest = text[:SHOWN_CHARS], max(0, len(text) - SHOWN_CHARS)
    text = fold(text)
    return f"{text}... ({rest} more characters)" if rest else text


def quoted(value: object) -> str:
    """Fix pass 11 (M12-C): VALUE as ``shown()`` names it, a string always as its repr, so it prints what ``!r`` printed
    for a value of at most ``SHOWN_CHARS`` characters with no run of more than ``BLANKS_KEPT`` blanks; every ``!r`` of a
    workflow's value is this now, cut and folded (round 12's N12-5b went through an uncut ``{key!r}``)."""
    return shown(value, bare=False)


def said(text: object, limit: int = 300) -> str:
    """Fix pass 11 (M12-C): a tool's own message (PyYAML's, bash's, a crash's), which can quote the workflow, as printed:
    its whitespace runs as one blank, at most LIMIT characters, folded, and every character but printable text escaped
    (fix pass 10's ``visible(' '.join(str(exc).split())[:300])``, folded; bash's message was printed uncut)."""
    return visible(fold(" ".join(str(text).split())[:limit]))


def clipped(text: str, limit: int) -> str:
    """Fix pass 11 (M12-C): TEXT, a line printed as it stands (a line of a pin mismatch's diff), at most LIMIT
    characters, then the count of the rest, folded."""
    return fold(text[:limit]) + (f"... ({len(text) - limit} more characters)" if len(text) > limit else "")


def place(where: str, part: object) -> str:
    """Fix pass 10 (M11-B's class): the place WHERE, then PART, in the document, as a message names it: at most
    ``SHOWN_CHARS`` characters, then ``...``. The walk holds a place for every node it has still to read, so a key's
    text copied whole into the place of each node beneath it grew as the square of the file (a key of 40,000
    characters over a list of 20,000 items: 795 MB at the peak, checker-r11/evidence/cost_probe_square_fp10.before.out).
    Fix pass 11 (n12-a): a longer place keeps its first ``PLACE_HEAD`` and its last ``PLACE_TAIL`` characters, the count
    of those between, so two places that share a long prefix still print apart (round 12's N12-6); and it is folded
    (M12-C)."""
    here = f"{where}{part}"
    if len(here) > SHOWN_CHARS:
        here = f"{here[:PLACE_HEAD]}...({len(here) - PLACE_HEAD - PLACE_TAIL} characters)...{here[-PLACE_TAIL:]}"
    return fold(here)


def few(items: "list[str]") -> "list[str]":
    """Fix pass 10: the first ``FEW`` of ITEMS, the rest counted, for a refusal that lists places."""
    return items[:FEW] + ([f"... {len(items) - FEW} more"] if len(items) > FEW else [])


def action_name(value: object) -> str:
    """Fix pass 10 (n11-b): the owner/repo a ``uses:`` names, its ``@ref`` dropped, in lower case: GitHub reads an owner
    and a repository without regard to case."""
    return str(value).split("@", 1)[0].lower()


def document_problems(wf: dict) -> "list[str]":
    """Fix pass 9: in the whole loaded workflow, a mapping key holding ``${{`` (B10-1, and round 10's O-2: the runner
    evaluates an expression key in a step's ``with`` into an input's name, GitHub's TypeScript lineage at a step's level
    too; no template, port or simulation holds one), and a lone surrogate in any key or string (m10-a: it is no
    character, and printing one stopped round 10's run, R10-11). Each is refused wherever it stands. Walked without
    recursion, so a deep document cannot stop the walk; since fix pass 10 the loader refuses anchors and aliases, so the
    document is a tree no larger than its file (M11-B).

    Fix pass 10 (M11-A): every other character but printable text, a tab and a newline in any key or string
    (``unprintable``), and a newline in a mapping key or in the ``name`` of the workflow, a job or a step: a double-quoted
    escape loads either while the file holds printable text alone, and printed raw, a step's name displayed a refused
    port as PASS (round 11's M11-1 to M11-3). No template, port or simulation holds either (37 files)."""
    expression_keys: list[str] = []
    surrogates: list[str] = []
    # Fix pass 10 (M11-B's class): a list, since two places cut at SHOWN_CHARS can read alike (place()).
    odd: list[tuple[str, set[str]]] = []
    broken: list[str] = []
    stack: list[tuple[object, str]] = [(wf, "")]
    while stack:
        value, where = stack.pop()
        if isinstance(value, dict):
            for key, inner in value.items():
                here = place(where, f"/{key}")
                if isinstance(key, str) and "${{" in key:
                    expression_keys.append(here)
                if isinstance(key, str) and lone_surrogate(key):
                    surrogates.append(f"{here} (a key)")
                if isinstance(key, str) and "\n" in key:
                    broken.append(f"{here} (a key)")
                if isinstance(key, str) and unprintable(key):
                    odd.append((f"{here} (a key)", unprintable(key)))
                stack.append((inner, here))
        elif isinstance(value, list):
            stack.extend((inner, place(where, f"[{number}]")) for number, inner in enumerate(value))
        elif isinstance(value, str):
            if lone_surrogate(value):
                surrogates.append(where)
            if unprintable(value):
                odd.append((where, unprintable(value)))
    # Fix pass 10 (M11-A): the names this checker prints as part of one line; each job's place made once (M11-B's class:
    # a long id was copied whole into the place of each of its steps).
    named: list[tuple[str, object]] = [("/name", wf.get("name"))]
    for job_id, job in (wf.get("jobs") if isinstance(wf.get("jobs"), dict) else {}).items():
        if isinstance(job, dict):
            prefix = place("/jobs", f"/{job_id}")
            named.append((place(prefix, "/name"), job.get("name")))
            named.extend((place(prefix, f"/steps[{number}]/name"), s.get("name")) for number, s in enumerate(job.get("steps") if isinstance(job.get("steps"), list) else []) if isinstance(s, dict))
    broken.extend(where for where, name in named if isinstance(name, str) and "\n" in name)
    bad = []
    if odd:
        bad.append(f"the workflow holds a character other than printable text, a tab or a newline ({sorted(set().union(*(points for _, points in odd)))}) at {few(sorted(where for where, _ in odd))}: a double-quoted escape (\\x1b, \\x85, \\u200b) loads as one while the file holds printable text alone, and printed raw, one can move a terminal's cursor, clear its screen or hide what follows (round 11's M11-1 displayed a refused port as PASS); no template or port holds one, so it is refused wherever it stands")
    if broken:
        bad.append(f"the workflow holds a newline in a mapping key, or in the name of the workflow, a job or a step, at {few(sorted(broken))}: each is printed as part of one line, and a newline there would write lines of its own into what this checker prints (round 11's M11-3); no template or port holds one, so it is refused")
    # Fix pass 11 (M12-C): the places listed as few() lists them, the rest counted, as the two refusals above do.
    if expression_keys:
        bad.append(f"the workflow holds a mapping key with ${{{{ at {few(sorted(expression_keys))}: GitHub's reader admits an expression key in a mapping its schema gives a context, a step's with among them, where the runner evaluates it into an input's name (round 10's R10-3 sent the PyPI job's OIDC token to the host it named), and GitHub's two lineages disagree on one among a step's own keys (round 10's O-2); no template key is an expression, so one is refused wherever it stands")
    if surrogates:
        bad.append(f"the workflow holds a lone surrogate (U+D800 to U+DFFF, which a double-quoted \\uD800 escape loads as, and which is no character) at {few(sorted(surrogates))}: what GitHub's runner makes of one is not known here, and no template or port holds one, so it is refused wherever it stands")
    return bad


def by_action(value):
    """VALUE with every ``uses:`` reduced to the action's name: the ``@ref`` is dropped here and compared on its own (fix
    pass 9, ``uses_problems``), so a ref that is not the template's is reported once, by that rule."""
    if isinstance(value, dict):
        return {k: (str(v).split("@", 1)[0] if k == "uses" and isinstance(v, str) else by_action(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [by_action(v) for v in value]
    return value


def names(job: dict) -> "list[str]":
    return [str(s.get("name") or s.get("uses") or "") for s in job.get("steps") or []]


def step_list(job: dict) -> "list[tuple[object, object]]":
    """Each step as (its name, the action it uses with the ``@ref`` dropped)."""
    return [(s.get("name"), str(s["uses"]).split("@", 1)[0] if s.get("uses") else None) for s in job.get("steps") or []]


def step(job: dict, name: str) -> "dict | None":
    found = [s for s in job.get("steps") or [] if s.get("name") == name]
    return found[0] if len(found) == 1 else None


def uploads(job: dict) -> "list[int]":
    """The publish action's steps, the owner and repository read without regard to case, as GitHub reads them (fix pass
    10, n11-b: ``PyPA/...`` is an upload, and its ref is judged by ``uses_problems``)."""
    return [i for i, s in enumerate(job.get("steps") or []) if "@" in str(s.get("uses") or "") and action_name(s.get("uses")) == PUBLISH_ACTION[:-1]]


def checkouts(job: dict) -> "list[dict]":
    """The checkout steps, read as ``uploads`` reads its own (fix pass 10, n11-b)."""
    return [s for s in job.get("steps") or [] if "@" in str(s.get("uses") or "") and action_name(s.get("uses")) == "actions/checkout"]


def installs(job: dict) -> "list[dict]":
    return [s for s in job.get("steps") or [] if "pip install" in str(s.get("run") or "")]


def environment(job: dict) -> str:
    env = job.get("environment")
    return str(env.get("name") if isinstance(env, dict) else env)


def needs(job: dict) -> "list[str]":
    value = job.get("needs")
    return sorted([value] if isinstance(value, str) else list(value or []))


def commands(run: str) -> "list[str]":
    """A build-window step's commands: its non-blank lines that are not comments, stripped, each line a backslash
    continues joined to the next. The window's reader (fix pass 7 keeps it there alone), guarded by ``line_problems``."""
    out: list[str] = []
    pending = ""
    for line in (raw.strip() for raw in run.splitlines()):
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending += line[:-1].strip() + " "
            continue
        out.append(pending + line)
        pending = ""
    if pending:
        out.append(pending.strip())
    return out


def line_problems(run: str) -> "list[str]":
    """Where ``commands()``'s reading of a build-window step's lines and bash's could differ, each refused (fix pass 4,
    and fix pass 5 for round 6's R6-F1; since fix pass 7, at the window alone): a line break other than a newline
    (``commands()`` splits at each, bash at ``\\n`` alone); a NUL byte, which bash drops; any other character but
    printable text, a tab and a newline (``commands()`` strips a no-break space, or another space Python knows, from a
    line's ends, where bash reads it as part of a word); a line ending in an even run of backslashes, or in a backslash
    and then whitespace (bash continues neither); a continuation into a blank or comment line (bash ends the command
    there, where ``commands()`` joins the next command line to it); a continuation whose backslash no space or tab
    precedes, or whose space or tab there is itself escaped (bash deletes the backslash and the newline, so the two
    lines' text abuts, where ``commands()`` joins it with one space); and a continuation on a script's last line (bash
    passes that backslash on as an argument; ``commands()`` drops it)."""
    problems: list[str] = []
    found = sorted({f"U+{ord(char):04X}" for char in run if char in LINE_BREAKS})
    if found:
        problems.append(f"holds a line break other than a newline ({found}), which this checker reads as one and bash does not")
    if NUL in run:
        problems.append("holds a NUL byte, which bash drops from what it reads: $<NUL>( is a command substitution to bash and a literal $ to this checker")
    odd = sorted({f"U+{ord(char):04X}" for char in run if not (char.isprintable() or char in "\t\n" or char == NUL or char in LINE_BREAKS)})
    if odd:
        problems.append(f"holds a character other than printable text, a space, a tab or a newline ({odd}): this checker strips a no-break space, or another space Python knows, from a line's ends, where bash reads it as part of a word; a control or format character hides text from the review that reads the script")
    lines = run.split("\n")
    # Fix pass 10 (M11-B's class): whether a line after each holds a character but a space or a tab, found once; the
    # text of every later line, joined for each continuation into a blank line, grew as the square of the lines.
    later = [False] * (len(lines) + 1)
    for at in range(len(lines) - 1, -1, -1):
        later[at] = later[at + 1] or bool(lines[at].strip(" \t"))
    for at, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("#") or not line.endswith("\\"):
            continue
        tail = len(line) - len(line.rstrip("\\"))
        # Fix pass 7 (round 8's N8-1): the next line blank to bash, as bash reads blanks (a space or a tab), so that a line
        # holding a CR, VT, FF or no-break space falls through to the rule that names it.
        following = lines[at + 1].strip(" \t") if at + 1 < len(lines) else None
        # Fix pass 5: the text before the continuation's backslash, and that text without the blanks before it.
        body = line[:-1]
        spaced = body.rstrip(" \t")
        if tail % 2 == 0:
            problems.append(f"has a line ending in an even run of backslashes, which bash does not continue: {quoted(line)}")
        elif raw != raw.rstrip():
            problems.append(f"has a line ending in a backslash and then whitespace, which bash reads as an escaped space, not a continuation: {quoted(line)}")
        elif following is None:
            problems.append(f"continues the script's last line, whose backslash bash passes on as an argument and this checker drops: {quoted(line)}")
        elif following == "" or following.startswith("#"):
            # Fix pass 6 (R7-3): each message true wherever it is given; blank lines alone to the script's end have one.
            if later[at + 1]:
                problems.append(f"continues a line into a blank or comment line: bash ends the command at a blank line, and at a comment line's end, where the comment line's text joins the command unless an unescaped blank before its # makes it a comment, while this checker skips both and joins the next command line, if one follows, to this one: {quoted(line)}")
            else:
                problems.append(f"continues the script's last command line into the end of the script (only blank lines follow it): bash runs that command alone there, and it is refused all the same, like a continuation into a blank line: {quoted(line)}")
        elif spaced == body:
            problems.append(f"continues a line whose backslash no space or tab precedes: bash deletes the backslash and the newline, so this line's last character abuts the next line's first ($ then ( is a command substitution), where this checker joins them with a space: {quoted(line)}")
        elif (len(spaced) - len(spaced.rstrip("\\"))) % 2:
            # Fix pass 6 (R7-2): a message true wherever it is given (an unindented next line can read alike to both).
            problems.append(f"continues a line whose space or tab before the backslash is itself escaped: this checker strips that blank and joins the next line with one space, where bash keeps the blank (a tab stays a tab) and reads the next line as it stands, so that outside quotes an indented next line, or a blank after the escaped one, ends bash's word there; refused wherever it stands: {quoted(line)}")
    return problems


def script_problems(text: str) -> "list[str]":
    """Fix pass 7: what is refused in a pinned step's ``run`` (and in a pin's own text) before it is compared, rather than
    normalized away. Each would let the text compared differ from what bash runs."""
    problems: list[str] = []
    if NUL in text:
        problems.append("holds a NUL byte, which bash drops from what it reads: the text compared would not be the text run")
    odd = sorted({f"U+{ord(char):04X}" for char in text if not (char.isprintable() or char in "\t\n" or char == NUL)})
    if odd:
        problems.append(f"holds a character other than printable text, a tab or a newline ({odd}): a CR, a NEL or another line break, a control or format character reads otherwise to bash than to a reviewer")
    trailing = [number for number, line in enumerate(text.split("\n"), 1) if line != line.rstrip(" \t")]
    if trailing:
        problems.append(f"has trailing whitespace on line(s) {trailing}: refused, never stripped, since bash reads a backslash then a blank at a line's end as an escaped blank, not a continuation, and stripping the blank would make one")
    if text.rstrip("\n").endswith("\\"):
        problems.append("ends in a backslash: bash continues it into a final newline, or passes it on where none follows, so the block scalar's chomping would decide what runs")
    if "${{" in text:
        problems.append("holds ${{, an expression the runner substitutes into the script's text before bash reads it, so the text compared would not be the text run (pass the value through env)")
    return problems


def lag_problems(text: str, package: str) -> "list[str]":
    """The lag rule (the NIT of the round-4 review), on a pin's TEXT as it loads: one retry-loop header (``LOOP_HEADER``,
    its values 1 2 ... N) and one lag error, exactly ``LAG_ERROR`` with PACKAGE, a version variable and N. Lines are read
    with their leading blanks removed; nothing here decides what bash runs, and it can only refuse a pin."""
    lines = [line.strip(" \t") for line in text.split("\n")]
    headers = [found for found in map(LOOP_HEADER.fullmatch, lines) if found]
    errors = [line for line in lines if "is not installable from TestPyPI" in line]
    if len(headers) != 1 or len(errors) != 1:
        return [f"holds {len(headers)} retry-loop header(s) and {len(errors)} lag error(s): a pin holds the template's one retry loop (`for <var> in 1 2 ... N; do`, or `in $(seq [1] N)`) and its one lag error (LAG_ERROR)"]
    values = headers[0].group(2).split() if headers[0].group(2) else [str(k) for k in range(1, int(headers[0].group(3)) + 1)]
    tries = len(values)
    if tries < 2 or values != [str(k) for k in range(1, tries + 1)]:
        return [f"its retry loop runs over {values}, not 1 2 ... N"]
    pattern = re.escape(LAG_ERROR.format(package=package, version="VERSION_VARIABLE", tries=tries)).replace("VERSION_VARIABLE", r"\w+")
    if not re.fullmatch(pattern, errors[0]):
        return [f"its lag error is not the template's for {shown(package)} after {tries} tries (LAG_ERROR, the operator signature MANUAL.md quotes): {errors[0]!r}"]
    return []


def load_pins(path: Path) -> "tuple[dict[tuple[str, str, str], dict[str, str]], str]":
    """Fix pass 7: the pins file at PATH, every pin validated, and the sha256 of the bytes validated; a refused file stops
    the run (``SystemExit``, exit 1)."""

    def unique(pairs: "list[tuple[str, object]]") -> dict:
        keys = [key for key, _ in pairs]
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        if repeated:
            raise ValueError(f"a JSON object repeats the key(s) {repeated}")
        return dict(pairs)

    try:
        # Fix pass 11 (M12-A): through read_regular(), as a workflow is (a FIFO or a device named by --pins held the run).
        raw = read_regular(path, MAX_PINS_BYTES, "MAX_PINS_BYTES")
        # Fix pass 8 (m9-b): the file is pure ASCII, every other character written as an escape (\uXXXX), so a reviewer
        # sees each one (a Cyrillic look-alike of TestPyPI's host read as Latin in the raw text).
        if not raw.isascii():
            raise ValueError(f"it holds a byte outside ASCII (the first at offset {next(i for i, byte in enumerate(raw) if byte > 0x7F)}): every other character is written as an escape (\\uXXXX), so a reviewer sees each one")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError) as exc:  # a UnicodeDecodeError and a JSONDecodeError are ValueErrors
        raise SystemExit(f"pins file {path}: refused: {exc}") from None
    if not isinstance(data, dict) or set(data) != {"format", "about", "pins"} or data["format"] != PINS_FORMAT or not isinstance(data["pins"], list):
        raise SystemExit(f"pins file {path}: refused: not a {PINS_FORMAT} file (exactly the keys format, about and pins)")
    problems: list[str] = []
    pins: dict[tuple[str, str, str], dict[str, str]] = {}
    # Fix pass 10 (M11-A): the pins file's text other than its pins' lines (which script_problems reads, admitting a
    # tab) is printable text alone: its about here, each pin's fields below. A JSON escape (\u001b) loads a control
    # character from an ASCII file, and a message names a pin's step and package.
    if not (isinstance(data["about"], str) and data["about"].isprintable()):
        problems.append("its about is not a string of printable text alone (no control, format or line-break character)")
    for number, entry in enumerate(data["pins"], 1):
        if not isinstance(entry, dict) or set(entry) != PIN_FIELDS or not all(isinstance(entry[field], str) for field in PIN_FIELDS - {"lines"}) or not isinstance(entry["lines"], list) or not all(isinstance(line, str) for line in entry["lines"]):
            problems.append(f"pin {number}: needs exactly the fields {sorted(PIN_FIELDS)}, lines a list of strings and every other field a string")
            continue
        key = (entry["repo"], entry["workflow"], entry["step"])
        label = f"pin {number} {key}"
        text = "\n".join(entry["lines"])
        for field in sorted(PIN_FIELDS - {"lines"}):
            if not entry[field].isprintable():
                problems.append(f"{label}: its {field} holds a character other than printable text ({sorted({f'U+{ord(char):04X}' for char in entry[field] if not char.isprintable()})}): every string of the pins file is printable text alone, so what a message names from it cannot move a terminal's cursor or hide what follows")
        if entry["repo"] not in REPOS:
            problems.append(f"{label}: names a repository that is not one of {list(REPOS)}")
        if not WORKFLOW_FILE.fullmatch(entry["workflow"]):
            problems.append(f"{label}: its workflow is not a workflow file's name")
        if not entry["step"] or "${{" in entry["step"]:
            problems.append(f"{label}: its step names no step")
        if not entry["lines"] or entry["lines"][-1] == "" or [line for line in entry["lines"] if "\n" in line]:
            problems.append(f"{label}: its lines are empty, end in an empty line (a pin's text has no final newline) or hold a newline")
        found = script_problems(text)
        problems.extend(f"{label}: its text {problem}" for problem in found)
        if not found and hashlib.sha256(text.encode("utf-8")).hexdigest() != entry["sha256"]:
            problems.append(f"{label}: its sha256 {shown(entry['sha256'])} is not its text's ({hashlib.sha256(text.encode('utf-8')).hexdigest()}): the file was changed without its hash, or the hash without its text")
        problems.extend(f"{label}: {problem}" for problem in lag_problems(text, entry["package"]))
        if key in pins:
            problems.append(f"{label}: repeats a pin's key")
        pins[key] = {"package": entry["package"], "text": text, "file": str(path)}
    if problems:
        raise SystemExit(f"pins file {path}: refused:\n" + "\n".join(f"  - {problem}" for problem in problems))
    return pins, hashlib.sha256(raw).hexdigest()


def pin_mismatch(job_id: str, name: str, key: str, have: str, want: str, pins_file: str) -> str:
    """A pinned step's text HAVE differs from its pin's WANT: the key, the first differing line, a unified diff, and
    (fix pass 8, n9-b) PINS_FILE, the pins file this run loaded, default or ``--pins``."""
    have_lines, want_lines = have.split("\n"), want.split("\n")
    at = next((i for i, (a, b) in enumerate(zip(want_lines, have_lines)) if a != b), min(len(want_lines), len(have_lines)))
    # Fix pass 11 (M12-C): the step's lines, and the pin's beside them, cut and folded: quoted() for the first differing
    # line, clipped() at DIFF_CHARS for each diff line (printed as it stands, so a pin's indentation still shows).
    pin_line = quoted(want_lines[at]) if at < len(want_lines) else "nothing (the pin ends before it)"
    step_line = quoted(have_lines[at]) if at < len(have_lines) else "nothing (the step ends before it)"
    diff = list(difflib.unified_diff(want_lines, have_lines, "pin", "step", n=1, lineterm=""))
    # Fix pass 10: the local was named shown, which now names the module's helper (as n11-d's installs did).
    diff_lines = diff[:DIFF_LINES] + ([f"... {len(diff) - DIFF_LINES} more diff lines"] if len(diff) > DIFF_LINES else [])
    return f"{shown(job_id)}: step {quoted(name)} differs from its pin {key}, first at line {at + 1}: the pin has {pin_line}, the step {step_line}. If the change is intended, update the pin through that port's review (its lines and its sha256 in {pins_file})" + "".join(f"\n        | {clipped(line, DIFF_CHARS)}" for line in diff_lines)


def check_pinned_steps(job_id: str, runs: "list[dict]", package: str, repo: str, workflow: str, pins: "dict[tuple[str, str, str], dict[str, str]]") -> "list[str]":
    """Fix pass 7: each of RUNS, the install job's run steps, equals its pin for (REPO, WORKFLOW, its name); each pin of
    (REPO, WORKFLOW) has its step; each pin is for PACKAGE."""
    bad: list[str] = []
    pinned = {key[2]: pin for key, pin in pins.items() if key[:2] == (repo, workflow)}
    # Fix pass 10 (M11-A): the job id, the workflow file's name and the package, each through shown().
    job = shown(job_id)
    if not pinned:
        bad.append(f"{job}: the pins file pins no install script for ({repo}, {shown(workflow)}): every publisher's install step must equal a pinned, reviewed script; add this publisher's pin through its port's review")
    # Fix pass 11 (n12-d): a set (a list made this check grow as the square of the run steps); M12-C: each step's name
    # through quoted(), cut and folded, as !r wrote it.
    seen: set[str] = set()
    for s in runs:
        name, run = s.get("name"), s.get("run")
        if not isinstance(name, str) or not name:
            bad.append(f"{job}: a step runs a script without a name ({quoted(name)}): a step's name is its pin's key")
            continue
        if name in seen:
            bad.append(f"{job}: two steps run a script under one name, {quoted(name)}: a pin's key names one step")
            continue
        seen.add(name)
        key = f"({repo}, {shown(workflow)}, {quoted(name)})"
        pin = pinned.get(name)
        if pin is None:
            bad.append(f"{job}: step {quoted(name)} runs a script with no pin: the pins file holds no {key}. Every run step of the install job must equal a pinned, reviewed script; if this step is intended, add its pin through that port's review")
            continue
        if pin["package"] != package:
            bad.append(f"{job}: step {quoted(name)}: its pin {key} is for {shown(pin['package'])}, and the workflow publishes {shown(package)} (PUBLISH_PACKAGE): the check would test another package than the one published")
        if not isinstance(run, str):
            bad.append(f"{job}: step {quoted(name)} runs {type(run).__name__}, not a script's text")
            continue
        problems = script_problems(run)
        if problems:
            bad.extend(f"{job}: step {quoted(name)} {problem}" for problem in problems)
            continue
        # Fix pass 8 (m9-a): at most one final newline (a block scalar's | or |-). A script that ends inside a
        # here-document reads each newline after its last line as a line of the here-document's body, so |+ keeping
        # blank lines at the end delivers another script than the pin's.
        if run.endswith("\n\n"):
            bad.append(f"{job}: step {quoted(name)} ends in {len(run) - len(run.rstrip(chr(10)))} newlines, and at most one is admitted (a block scalar's | or |-, never |+ keeping blank lines): bash reads each newline after a script that ends inside a here-document as a line of its body, so the text compared would not be the text run")
            continue
        text = run[:-1] if run.endswith("\n") else run
        if text != pin["text"]:
            bad.append(pin_mismatch(job_id, name, key, text, pin["text"], pin["file"]))
    for name in pinned:
        if name not in seen:
            bad.append(f"{job} has no run step named {quoted(name)}, which the pins file pins for ({repo}, {shown(workflow)}): the pinned script must run in the install job")
    return bad


def expression_words(run: str) -> str:
    """Fix pass 10 (M11-B's class): RUN with each ``${{ }}`` expression that closes on its own line made the word
    EXPRESSION, exactly as ``re.sub(r"\\$\\{\\{.*?\\}\\}", "EXPRESSION", run)`` made it until fix pass 10, in time linear in
    RUN: that expression scanned from each ``${{`` to its line's end, so a line of 40,000 ``${{`` took 22.7 s."""
    out: list[str] = []
    at = scan = 0
    line_end = -1
    while (start := run.find("${{", scan)) >= 0:
        if start > line_end:
            line_end = run.find("\n", start)
            line_end = len(run) if line_end < 0 else line_end
        end = run.find("}}", start + 3, line_end)
        if end < 0:
            scan = line_end  # no }} after this ${{ on its line, so no expression begins on that line from here on
            continue
        out.append(run[at:start])
        out.append("EXPRESSION")
        at = scan = end + 2
    out.append(run[at:])
    return "".join(out)


def bash_parses(run: str) -> str:
    """'' when RUN parses as bash (``bash -n``, with each ``${{ }}`` expression made a plain word), else bash's error."""
    proc = subprocess.run(["bash", "-n"], input=expression_words(run), capture_output=True, text=True, check=False)
    return "" if proc.returncode == 0 else (proc.stderr.strip().splitlines() or ["(no message)"])[0]


def template(path: Path) -> "dict[str, object]":
    # Fix pass 10 (M11-B): a template that does not load (an anchor among the reasons now) is refused with a message.
    # Fix pass 11 (M12-A, n12-e): one that is not a regular file, or too large, is refused in its own words.
    try:
        wf = load(path)
    except FileRefused as exc:
        raise SystemExit(f"template {path}: refused before any of it is parsed: {exc}") from None
    except (OSError, UnicodeDecodeError, yaml.YAMLError, RecursionError) as exc:
        raise SystemExit(f"template {path}: refused: it does not load as YAML this checker can read ({type(exc).__name__}): {said(exc)}") from None
    jobs = wf["jobs"]
    want = {
        f"build/{REUSE}": step(jobs["build"], REUSE),
        f"build/{RECORD}": step(jobs["build"], RECORD),
        f"build/{UPLOAD}": step(jobs["build"], UPLOAD),
        f"test/{DOWNLOAD}": step(jobs["testpypi"], DOWNLOAD),
        f"test/{VERIFY_DIST}": step(jobs["testpypi"], VERIFY_DIST),
        f"test/{TESTPYPI_AFTER}": step(jobs["testpypi"], TESTPYPI_AFTER),
        f"prod/{DOWNLOAD}": step(jobs["pypi"], DOWNLOAD),
        f"prod/{VERIFY_DIST}": step(jobs["pypi"], VERIFY_DIST),
        f"prod/{TESTPYPI_BEFORE}": step(jobs["pypi"], TESTPYPI_BEFORE),
        f"prod/{PYPI_AFTER}": step(jobs["pypi"], PYPI_AFTER),
        "republish-job": jobs[REPUBLISH],
        "dispatch": wf["on"]["workflow_dispatch"],
    }
    missing = sorted(k for k, v in want.items() if v is None)
    if missing:
        raise SystemExit(f"template {path} lacks {missing}")
    out: dict[str, object] = by_action(want)
    # Each publish job's steps as (name, action): nothing may be added, dropped or moved, a rebuild least of all.
    out["test-steps"] = step_list(jobs["testpypi"])
    out["prod-steps"] = step_list(jobs["pypi"])
    # Fix pass 9 (B10-3, the owner's ruling "Pin template SHAs"): each job of the template's chain, by kind, and the
    # exact uses: strings its steps name, each owner/repo@<40 hex>, one ref per action across the chain. The install job
    # may also use the template's checkout, as cascor's sub-package publishers' install jobs do (INSTALL_ACTIONS).
    # Fix pass 10 (n11-d): install_jobs, not installs, which names the module's function.
    install_jobs = [job for job in jobs.values() if isinstance(job, dict) and job.get("name") == INSTALL_NAME]
    if len(install_jobs) != 1:
        raise SystemExit(f"template {path} holds {len(install_jobs)} jobs named {INSTALL_NAME!r}, not one")
    chain = {"build": jobs["build"], "TestPyPI": jobs["testpypi"], "install": install_jobs[0], "PyPI": jobs["pypi"], "republish": jobs[REPUBLISH]}
    refs: dict[str, set[str]] = {}
    listed: dict[str, set[str]] = {}
    for kind, job in chain.items():
        values = [s["uses"] for s in job.get("steps") or [] if "uses" in s]
        loose = [value for value in values if not (isinstance(value, str) and PINNED_USES.fullmatch(value))]
        if loose:
            raise SystemExit(f"template {path}: its {kind} job uses {loose}, not owner/repo@<a 40-hex commit SHA>: under the owner's ruling \"Pin template SHAs\" every action of the template's chain is pinned to a full commit SHA, which each port's must equal")
        listed[kind] = set(values)
        for value in values:
            refs.setdefault(value.split("@", 1)[0], set()).add(value)
    twice = {action: sorted(found) for action, found in refs.items() if len(found) > 1}
    if twice:
        # Fix pass 10 (n11-e): the reason is the install job's set, which takes one ref of each of INSTALL_ACTIONS.
        raise SystemExit(f"template {path} pins an action at more than one ref ({twice}): the install job admits the template's one ref of each of {list(INSTALL_ACTIONS)}, and with two, which one it admitted would be arbitrary, so the template is refused rather than a ref chosen")
    listed["install"] |= {next(iter(refs[action])) for action in INSTALL_ACTIONS if action in refs}
    out["uses"] = {kind: frozenset(found) for kind, found in listed.items()}
    # Fix pass 9 (B10-1): the TestPyPI and PyPI jobs' upload steps, one each, holding UPLOAD_STEP_KEYS, and their inputs
    # under literal names: what each port's upload is compared with.
    for kind, job in (("TestPyPI", jobs["testpypi"]), ("PyPI", jobs["pypi"])):
        found = [job["steps"][i] for i in uploads(job)]
        if len(found) != 1 or set(found[0]) != UPLOAD_STEP_KEYS or not isinstance(found[0].get("with"), dict) or not all(isinstance(key, str) and "${{" not in key for key in found[0]["with"]):
            raise SystemExit(f"template {path}: its {kind} job's upload is not one step holding exactly {sorted(UPLOAD_STEP_KEYS)}, its inputs under literal names: {found}")
        out[f"{kind}-upload"] = dict(found[0]["with"])
    return out


def setup_python_problems(job_id: str, job: dict) -> "list[str]":
    """Fix pass 8 (M9-B): each setup-python step of JOB (the build job, or the install job) takes ``python-version``
    alone, a CPython version written as a string (``SETUP_PYTHON_VERSION``), as the template's do. Every other input
    chooses where the interpreter that runs the job's later steps comes from, or what runs first: ``mirror`` with
    ``check-latest`` installs an interpreter from a manifest at a URL of the port's choosing, running its setup.sh, and
    puts it first on PATH; ``python-version-file`` reads a file the checkout brings; ``cache`` restores a pip cache;
    ``update-environment: false`` leaves the runner's own python and pip under the steps after it."""
    bad: list[str] = []
    for s in job.get("steps") or []:
        if str(s.get("uses") or "").split("@", 1)[0].lower() != SETUP_PYTHON:
            continue
        inputs = s.get("with")
        version = inputs.get("python-version") if isinstance(inputs, dict) else None
        if not (isinstance(inputs, dict) and set(inputs) == {"python-version"} and isinstance(version, str) and SETUP_PYTHON_VERSION.fullmatch(version)):
            bad.append(f"{shown(job_id)}: step {shown(s.get('name') or s.get('uses'))} gives setup-python {quoted(inputs)}: it takes python-version alone, a CPython version written as a string, as the template's \"3.12\" (mirror, check-latest, python-version-file, cache, update-environment and the other inputs choose where the interpreter running the steps after it comes from, or what runs first)")
    return bad


def runs_on_problem(job_id: str, value: object) -> str:
    """Fix pass 9 (n10-a): JOB_ID's runs-on VALUE is not the string ubuntu-latest; a message true of every form refused,
    a one-label list naming ubuntu-latest among them."""
    return f"{shown(job_id)} gives runs-on {quoted(value)}: it gives runs-on as the template writes it, the string ubuntu-latest, and any other form is refused, a one-label list naming ubuntu-latest among them (another label, a group or a longer list can name a runner the repository chooses)"


def uses_problems(job_id: str, job: dict, kind: str, allowed: "frozenset[str]") -> "list[str]":
    """Fix pass 9 (B10-3, the owner's ruling of 2026-11-24, "Pin template SHAs"): each step of JOB, a job of the chain
    (KIND: build, TestPyPI, install, PyPI or republish), that holds ``uses`` names exactly one of ALLOWED: the template's
    owner/repo@<SHA> for an action its KIND job uses (the install job: INSTALL_ACTIONS at the template's SHAs)."""
    bad: list[str] = []
    for s in job.get("steps") or []:
        if "uses" not in s:
            continue
        value = s["uses"]
        if isinstance(value, str) and value in allowed:
            continue
        label = s.get("name") or value
        pinned = sorted(u for u in allowed if u.split("@", 1)[0] == str(value).split("@", 1)[0])
        # Fix pass 10 (n11-b): the template's action, its owner or repository in another case.
        cased = sorted(u for u in allowed if u.split("@", 1)[0] != str(value).split("@", 1)[0] and action_name(u) == action_name(value))
        if pinned:
            bad.append(f"{shown(job_id)}: step {quoted(label)} uses {quoted(value)}, and the template pins {pinned[0]!r}: under the owner's ruling of 2026-11-24 (\"Pin template SHAs\") every action of a job that holds id-token, or that such a job needs, runs at the template's exact commit SHA (a tag, a branch, a short SHA or another commit is refused; a Dependabot bump lands in cascor's template first, and each repository's own CI keeps its ref-free digests)")
        elif cased:
            same_ref = str(value).partition("@")[2] == cased[0].partition("@")[2]
            bad.append(f"{shown(job_id)}: step {quoted(label)} uses {quoted(value)}, the template's {cased[0].split('@', 1)[0]!r} in another case{'' if same_ref else ', at another ref'}: GitHub reads an owner and a repository without regard to case, so it names that action, and it is refused all the same, since this checker compares the template's exact text ({cased[0]!r})")
        else:
            bad.append(f"{shown(job_id)}: step {quoted(label)} uses {quoted(value)}, an action the template's {kind} job does not use ({sorted(allowed)}): under the owner's ruling of 2026-11-24 (\"Pin template SHAs\") a step of a job that holds id-token, or that such a job needs, runs no action but the template's, at its exact commit SHA (another owner, a fork, a local action or a container image is refused)")
    return bad


def upload_problems(job_id: str, s: dict, template_inputs: "dict[str, object]") -> "list[str]":
    """Fix pass 9 (B10-1): an upload step S of the TestPyPI or PyPI job holds exactly UPLOAD_STEP_KEYS, and its ``with``
    exactly TEMPLATE_INPUTS (the template's upload inputs under their literal names, with its values, as GitHub types
    them), adding only UPLOAD_OPTIONAL_INPUTS, each the boolean true. A key equal to an input but for case or ``-`` and
    ``_``, and an expression key, are each refused with their own message."""
    bad: list[str] = []
    who = shown(job_id)  # fix pass 10 (M11-A): the job id through shown()
    label = s.get("name") or s.get("uses")
    if set(s) != UPLOAD_STEP_KEYS:
        bad.append(f"{who}: its upload step {quoted(label)} holds the keys {shown(sorted(map(str, s)))}, and an upload step holds exactly {sorted(UPLOAD_STEP_KEYS)}, as the template's do (no port adds an env, an id, a timeout or any other key)")
    inputs = s.get("with")
    if not isinstance(inputs, dict):
        return bad + [f"{who}: its upload step {quoted(label)} gives with {quoted(inputs)}, not a mapping of the template's inputs"]
    known = {name.lower().replace("_", "-"): name for name in (*template_inputs, *UPLOAD_OPTIONAL_INPUTS)}
    for key, value in inputs.items():
        if not isinstance(key, str):
            bad.append(f"{who}: its upload gives an input under the key {quoted(key)}, which is not a name: the template gives each input under its literal name")
        elif "${{" in key:
            bad.append(f"{who}: its upload gives an input under the expression key {quoted(key)}: GitHub evaluates an expression key in a step's with into an input's name (round 10's R10-3 sent the PyPI job's OIDC token to the host its repository-url named), so an input is given under its literal name alone")
        elif key in template_inputs:
            if not (type(value) is type(template_inputs[key]) and value == template_inputs[key]):
                bad.append(f"{who}: its upload gives {key} {quoted(value)}, and the template's gives {template_inputs[key]!r}")
        elif key in UPLOAD_OPTIONAL_INPUTS:
            if value is not True:
                bad.append(f"{who}: its upload gives {key} {quoted(value)}: a port may add {key} only as the boolean true, as cascor's publishers and the ports do")
        elif key.lower().replace("_", "-") in known:
            bad.append(f"{who}: its upload gives {quoted(key)}, which is the input {known[key.lower().replace('_', '-')]!r} but for case or - and _: GitHub matches an action's inputs case-insensitively, and the pinned action reads its deprecated underscore aliases ({', '.join(UPLOAD_ALIASES)}) whenever the kebab-case input is empty (round 10's R10-1, R10-2 and R10-4), so an input is given under the template's exact name alone")
        else:
            bad.append(f"{who}: its upload gives {quoted(key)}, which the template's upload does not give (it gives {sorted(template_inputs)}, and a port may add {list(UPLOAD_OPTIONAL_INPUTS)} as true): another input of the publish action can send the upload, or the job's OIDC token, elsewhere (repository_url, password, user), or switch a check off (skip-existing, verify-metadata)")
    missing = [key for key in template_inputs if key not in inputs]
    if missing:
        bad.append(f"{who}: its upload does not give {missing}, which the template's gives as {[template_inputs[key] for key in missing]}")
    return bad


def extra_job_problems(job_id: object, job: object, repo: str, path: Path) -> "list[str]":
    """Fix pass 9 (B10-2): JOB, outside the chain's five, is refused unless EXTRA_JOBS holds it for (REPO, PATH's file
    name, JOB_ID), exactly as GitHub types it, and the reusable workflow it calls, read beside PATH, has the sha256 the
    allow-list pins."""
    entry = EXTRA_JOBS.get((repo, path.name, job_id)) if isinstance(job_id, str) else None
    if entry is None:
        return [f"job {quoted(job_id)} is not one of the template's five, and the allow-list (EXTRA_JOBS) holds no job ({repo}, {shown(path.name)}, {quoted(job_id)}): every other job is refused, since a job of the same run can replace the build's artifact (upload-artifact with overwrite: true: round 10's R10-5, and R10-7 after the PyPI job) or call a reusable workflow this checker never reads (R10-6)"]
    if job != entry["job"]:
        return [f"job {quoted(job_id)} is not exactly the allow-listed ({repo}, {shown(path.name)}, {quoted(job_id)}): it holds {quoted(job)}, and the allow-list {entry['job']!r}; if the change is intended, update EXTRA_JOBS through that port's review"]
    name, digest = entry["calls"]
    called = path.parent / name
    # Fix pass 11 (M12-A): through read_regular(), the workflows' guard and bound (read_bytes() had neither: a link to
    # /dev/stdin held the run for good, one to /dev/zero grew until memory ran out, round 12's N12-1 to N12-3).
    try:
        have = hashlib.sha256(read_regular(called, MAX_WORKFLOW_BYTES, "MAX_WORKFLOW_BYTES; the pinned file is 11,039 bytes")).hexdigest()
    except FileRefused as exc:
        return [f"job {quoted(job_id)} calls {name}, which is refused before its sha256 is taken: {exc}"]
    except OSError as exc:
        return [f"job {quoted(job_id)} calls {name}, which is not readable beside this workflow ({type(exc).__name__}): a local reusable workflow runs the file at the caller's commit, so fetch it with the workflow (the allow-list pins its sha256 {digest})"]
    if have != digest:
        # Fix pass 10 (n11-a): what is true of every file refused here, one whose line endings alone differ among them.
        return [f"job {quoted(job_id)} calls {shown(str(called))}, whose sha256 is {have}, not the {digest} the allow-list pins: its bytes differ from the pinned file's (a change of line endings alone, which YAML reads alike, is refused all the same: the pin is of the bytes); if the change is intended, update EXTRA_JOBS through that port's review"]
    return []


def check_install_job(job_id: str, job: dict, test_id: "str | None", package: str, repo: str, workflow: str, pins: "dict[tuple[str, str, str], dict[str, str]]") -> "list[str]":
    """Ruling 2 of 2026-11-16: the install check's own job, which cannot mint a credential, run outside any checkout,
    and (fix pass 7) runs exactly the scripts pinned for (REPO, WORKFLOW, each step's name)."""
    bad: list[str] = []
    who = shown(job_id)  # fix pass 10 (M11-A): the job id, each step's label and each value read through shown()
    if test_id is not None and needs(job) != [test_id]:
        bad.append(f"{who} needs {shown(job.get('needs'))}, expected the TestPyPI job {shown(test_id)}")
    if job.get("runs-on") != "ubuntu-latest":
        bad.append(runs_on_problem(job_id, job.get("runs-on")))
    if job.get("permissions") != {"contents": "read"}:
        bad.append(f"{who} permissions {shown(job.get('permissions'))}, expected exactly contents: read")
    if "environment" in job or uploads(job):
        bad.append(f"{who} holds an environment or uploads")
    if "if" in job or "continue-on-error" in job:
        bad.append(f"{who} sets if: or continue-on-error, so its check can be skipped or ignored")
    if "defaults" in job:
        bad.append(f"{who} sets defaults: its commands must run from the runner's temporary directory")
    if "env" in job:
        bad.append(f"{who} sets a job env, which every step of the check reads (PIP_EXTRA_INDEX_URL would add an index)")
    if "container" in job:
        bad.append(f"{who} runs in a container, whose image sets an environment this file does not show")
    for s in checkouts(job):
        inputs = s.get("with") if isinstance(s.get("with"), dict) else {}
        # Fix pass 9 (n10-b): a message true of every form refused, the text "false" among them.
        if inputs.get("persist-credentials") is not False:
            given = f"gives persist-credentials {quoted(inputs['persist-credentials'])}" if "persist-credentials" in inputs else "does not give persist-credentials"
            bad.append(f"{who}: its checkout {given}, and the template's gives the boolean false: checkout keeps its credential in the workspace, where the package TestPyPI serves runs, unless that input is false, and any form but the boolean is refused (the text \"false\", which the runner would hand checkout as the same input, among them)")
        # Added beyond the review (fix pass 4): the checkout holds the one file the version is read from, as every port's
        # does; a wider one can bring the package's source or a pip.conf into the workspace.
        paths = str(inputs.get("sparse-checkout") or "").split()
        if set(inputs) != {"sparse-checkout", "persist-credentials"} or len(paths) != 1 or not SPARSE_PATH.fullmatch(paths[0]):
            bad.append(f"{who}: its checkout is not a sparse checkout of the one file the version is read from (a pyproject.toml or _version.py, with persist-credentials: false and nothing else): {quoted(inputs)}")
    runs: list[dict] = []
    for s in job.get("steps") or []:
        label = shown(s.get("name") or s.get("uses"))
        unknown = sorted(str(k) for k in s if k not in STEP_KEYS)
        if unknown:
            bad.append(f"{who}: step {label} holds {shown(unknown)}, which GitHub does not define for a step: no install step may run a script under a key this checker does not read")
        if "continue-on-error" in s or "if" in s:
            bad.append(f"{who}: step {label} sets continue-on-error or if:, so the check can be skipped or ignored")
        if "working-directory" in s:
            bad.append(f"{who}: step {label} sets working-directory")
        if "shell" in s and s["shell"] != "bash":
            bad.append(f"{who}: step {label} sets a shell, {quoted(s['shell'])}: a step's own shell can drop -e (bash {{0}}) or change the interpreter (sh, python). Only the runner's default (bash -e {{0}}) and shell: bash (bash --noprofile --norc -eo pipefail {{0}}, which keeps -e) are admitted")
        # Fix pass 10 (n11-b): the action read as GitHub reads it, without regard to case (uses_problems refuses the case).
        if s.get("uses") and action_name(s["uses"]) not in INSTALL_ACTIONS:
            bad.append(f"{who}: step {label} uses an action the install job does not need: only {list(INSTALL_ACTIONS)}")
        env = s.get("env") or {}
        if not isinstance(env, dict) or not set(env) <= set(INSTALL_STEP_ENV) or [k for k in env if str(env[k]) != INSTALL_STEP_ENV[k]]:
            bad.append(f"{who}: step {label} sets env {quoted(sorted(env) if isinstance(env, dict) else env)}: an install step may set RELEASE_TAG: {INSTALL_STEP_ENV['RELEASE_TAG']} alone")
        if "run" in s:
            runs.append(s)
    bad.extend(setup_python_problems(job_id, job))
    bad.extend(check_pinned_steps(job_id, runs, package, repo, workflow, pins))
    return bad


def shape_problems(wf: dict) -> "list[str]":
    """Fix pass 8 (n9-c): the shapes every later rule reads, refused with a message rather than a traceback: ``on`` and
    ``jobs`` mappings, each job a mapping, each job's ``steps`` a list of mappings (GitHub reads a step's keys)."""
    bad = [f"{key} is {type(wf[key]).__name__}, not a mapping: no rule here can read it" for key in ("on", "jobs") if key in wf and not isinstance(wf[key], dict)]
    for job_id, job in (wf.get("jobs") or {}).items() if isinstance(wf.get("jobs"), dict) else ():
        if not isinstance(job, dict):
            bad.append(f"job {shown(job_id)} is {type(job).__name__}, not a mapping: no rule here can read it")
        elif job.get("steps") is not None and not isinstance(job["steps"], list):
            bad.append(f"job {shown(job_id)}: its steps are {type(job['steps']).__name__}, not a list: no rule here can read them")
        else:
            bad.extend(f"job {shown(job_id)}: step {number} is {type(s).__name__} ({quoted(str(s)[:60])}), not a mapping: no rule here can read it" for number, s in enumerate(job.get("steps") or [], 1) if not isinstance(s, dict))
    return bad


def check(path: Path, want: "dict[str, object]", repo: str, pins: "dict[tuple[str, str, str], dict[str, str]]") -> "list[str]":
    """Every failure found in PATH, a workflow of REPO (as the operator names it), its install steps compared with PINS
    under PATH's own file name. A missing job fails the checks that need it; every other check still runs. A workflow
    whose jobs or steps are not mappings is refused at once (fix pass 8, n9-c), and the next workflow is still checked."""
    bad: list[str] = []
    try:
        raw = read_text(path)  # fix pass 10 (M11-B's class): its size bounded, refused before it is parsed
        wf = load_text(raw)
    except FileRefused as exc:  # fix pass 11 (M12-A, n12-e): refused for its kind or its size, in its own words
        return [f"the workflow file is refused before any of it is parsed: {exc}"]
    except (OSError, UnicodeDecodeError, yaml.YAMLError, AttributeError, TypeError, RecursionError) as exc:  # fix pass 9 (m10-a): a file nested beyond the recursion limit is a load failure
        return [f"the workflow file does not load as YAML this checker can read ({type(exc).__name__}): {said(exc)}"]
    bad.extend(file_problems(raw))
    bad.extend(document_problems(wf))
    shapes = shape_problems(wf)
    if shapes:
        return bad + shapes
    jobs = wf.get("jobs") or {}
    env = wf.get("env") or {}
    # Fix pass 10 (M11-A): from here on, every value read from the workflow that a message names goes through shown(),
    # or !r (a mapping's or a list's str() is already its repr).
    if set(env) != PARAMETERS:
        bad.append(f"workflow env is {quoted(env)}, expected exactly {sorted(PARAMETERS)}")
    package, dist_dir, prefix = str(env.get("PUBLISH_PACKAGE")), str(env.get("PUBLISH_DIST_DIR")), str(env.get("PUBLISH_TAG_PREFIX"))
    if (dist_dir, prefix) not in (("dist", "v"), (f"{package}/dist", f"{package}-v")):
        bad.append(f"PUBLISH_DIST_DIR {quoted(dist_dir)} with PUBLISH_TAG_PREFIX {quoted(prefix)}: expected 'dist' with 'v', or {quoted(package + '/dist')} with {quoted(package + '-v')}")
    if (wf.get("on") or {}).get("workflow_dispatch") != want["dispatch"]:
        bad.append(f"workflow_dispatch is {shown((wf.get('on') or {}).get('workflow_dispatch'))}, expected the template's")
    if set((wf.get("on") or {})) != {"release", "workflow_dispatch"} or (wf.get("on") or {}).get("release") != {"types": ["published"]}:
        bad.append(f"triggers are {shown(wf.get('on'))}, expected release: published and workflow_dispatch only")
    if not str(wf.get("name") or "").lower().endswith("to pypi"):
        bad.append(f"workflow name {quoted(wf.get('name'))} does not end in 'to PyPI': juniper-ml's release-train monitor would drop its runs")
    top = wf.get("permissions")
    if top not in ({}, {"contents": "read"}):
        bad.append(f"top-level permissions {shown(top)} must be {{}} or contents: read")
    if ((wf.get("defaults") or {}).get("run") or {}).get("shell"):
        bad.append(f"the workflow sets defaults.run.shell {quoted(wf['defaults']['run']['shell'])}, which the install job's steps would run under")
    # Fix pass 7: where a pinned script starts is part of what the runner runs; no port sets a workflow default.
    if ((wf.get("defaults") or {}).get("run") or {}).get("working-directory"):
        bad.append(f"the workflow sets defaults.run.working-directory {quoted(wf['defaults']['run']['working-directory'])}: every run step without one of its own, the pinned install steps among them, would start there, not where their review read them")
    # A concurrency group may queue publish runs (F7 admits one on the cascor side), never cancel one in progress.
    for scope, group in [("the workflow", wf.get("concurrency"))] + [(f"job {shown(j)}", job.get("concurrency")) for j, job in jobs.items()]:
        if isinstance(group, dict) and group.get("cancel-in-progress", False) is not False:
            bad.append(f"{scope}'s concurrency group cancels a run in progress, which could stop it between two uploads")
    # Fix pass 10 (M11-D): the rule above read this workflow's own cancel-in-progress, and the run queued NEXT in a group
    # decides, by its own, whether the run in progress is cancelled; a group is repository-wide. So the workflow's group
    # is exactly <file stem>-${{ github.ref_name }}, or absent (the template sets none), the form every publisher that
    # sets one writes: a group no other publisher's file uses, for the refs the publishers use (fix pass 11, n12-b: for
    # refs a writer crafts, two publishers' groups can coincide, each cancel-in-progress: false, so at most a pending
    # run is replaced).
    if "concurrency" in wf:
        given, group = wf["concurrency"], CONCURRENCY_GROUP.format(stem=path.stem)
        if not (isinstance(given, dict) and set(given) == {"group", "cancel-in-progress"} and given["group"] == group and given["cancel-in-progress"] is False):
            bad.append(f"the workflow's concurrency is {shown(given)}: it is absent, as the template's is, or exactly {{group: {quoted(group)}, cancel-in-progress: false}}, as every publisher that sets one writes it. A group is repository-wide, and the run queued next in it decides, by its own cancel-in-progress, whether the run in progress is cancelled: a group another workflow names lets it cancel this run between uploads (round 11's M11-10: pr-budget-alarm, cascor's scheduled workflow's)")
    # R4-4: a job's own group, even one that never cancels a run in progress, cancels its pending job when another
    # queues (by default, queue: single, GitHub keeps one pending per group): a group on the PyPI job could stop a run
    # between its two uploads.
    for j, job in jobs.items():
        if "concurrency" in job:
            bad.append(f"job {shown(j)} sets a concurrency group of its own, which by default cancels its pending job when another queues: only the workflow's group is admitted")
    test_ids = [j for j, job in jobs.items() if job.get("name") == "Publish to TestPyPI"]
    install_ids = [j for j, job in jobs.items() if job.get("name") == INSTALL_NAME]
    prod_ids = [j for j, job in jobs.items() if job.get("name") == "Publish to PyPI"]
    if len(test_ids) != 1 or len(install_ids) != 1 or len(prod_ids) != 1 or "build" not in jobs or REPUBLISH not in jobs:
        bad.append(f"jobs {shown(sorted(jobs))}: need build, one 'Publish to TestPyPI', one '{INSTALL_NAME}', one 'Publish to PyPI' and republish")
    test_id = test_ids[0] if len(test_ids) == 1 else None
    install_id = install_ids[0] if len(install_ids) == 1 else None
    prod_id = prod_ids[0] if len(prod_ids) == 1 else None
    build, republish = jobs.get("build"), jobs.get(REPUBLISH)
    test, install, prod = jobs.get(test_id) if test_id else None, jobs.get(install_id) if install_id else None, jobs.get(prod_id) if prod_id else None
    # Fix pass 9 (B10-2): a job outside the chain's five is refused, unless the allow-list holds it exactly (EXTRA_JOBS);
    # until fix pass 8 it was noted, never judged.
    for job_id in sorted(set(jobs) - {"build", test_id, install_id, prod_id, REPUBLISH}, key=str):
        bad.extend(extra_job_problems(job_id, jobs[job_id], repo, path))
    # Fix pass 8 (B9-1, M9-A): each job of the chain carries exactly its template job's keys (CHAIN_JOB_KEYS) and,
    # but the republish job, a timeout; a sub-package's build job also its defaults. No container, services, strategy,
    # env, outputs or other key: a job container runs the template's python3 checks in an image of the port's choosing,
    # a service beside the job can rewrite the dist after it is checked and before it is uploaded, and runs-on another
    # runner moves the whole job to a machine the repository chooses.
    sub = (dist_dir, prefix) == (f"{package}/dist", f"{package}-v")
    for job_id, job, kind in (("build", build, "build"), (test_id, test, "publish"), (install_id, install, "install"), (prod_id, prod, "publish"), (REPUBLISH, republish, "republish")):
        if job is None:
            continue
        required = CHAIN_JOB_KEYS[kind]
        optional = (OPTIONAL_JOB_KEYS if kind != "republish" else frozenset()) | ({"defaults"} if kind == "build" and sub else set())
        if not required <= set(job) <= required | optional:
            bad.append(f"job {shown(job_id)} carries the keys {shown(sorted(map(str, job)))}: its template job's are exactly {sorted(required)}, and {sorted(optional) or 'nothing'} may be added; a container, services, a matrix, an env or another key would change what its steps run, or where")
    if build is not None and sub and "defaults" in build and build["defaults"] != {"run": {"working-directory": package}}:
        bad.append(f"the build job sets defaults {quoted(build['defaults'])}: a sub-package's build job may set defaults.run.working-directory to its package's directory ({shown(package)}) and nothing else")
    for job_id, job in ((test_id, test), (prod_id, prod)):
        if job is not None and job.get("runs-on") != "ubuntu-latest":
            bad.append(runs_on_problem(job_id, job.get("runs-on")))
    # Fix pass 9 (B10-3, the owner's ruling "Pin template SHAs"): every action of the chain's jobs, those that hold
    # id-token and those they need, at the template's exact owner/repo@<SHA>, and none the template's job does not use.
    for job_id, job, kind in (("build", build, "build"), (test_id, test, "TestPyPI"), (install_id, install, "install"), (prod_id, prod, "PyPI"), (REPUBLISH, republish, "republish")):
        if job is not None:
            bad.extend(uses_problems(job_id, job, kind, want["uses"][kind]))
    # juniper-ml's ceremony counts a job whose name holds "testpypi" as a TestPyPI job and one holding "pypi" as a PyPI
    # job (ceremony.py:660-661): any other job so named would be read as one of them.
    for job_id, job in jobs.items():
        if job_id not in (test_id, install_id, prod_id) and "pypi" in str(job.get("name") or "").lower():
            bad.append(f"job {shown(job_id)} is named {quoted(job.get('name'))}: only the TestPyPI, install and PyPI jobs may hold 'pypi'")
    # No env on a job that runs a template check, the install or an upload. F4: no PIP_*, PYTHON*, UV_* or HASH_CHECK_*
    # at any level -- workflow, job, a job's container, step: each can send pip elsewhere, change what python imports or
    # move a JSON check's bounds.
    for job_id in (test_id, prod_id, REPUBLISH):
        if job_id is not None and "env" in (jobs.get(job_id) or {}):
            bad.append(f"job {shown(job_id)} sets a job env, which every step reads (HASH_CHECK_ATTEMPTS would move a JSON check's bounds)")
    levels = [("workflow", wf.get("env"), False)]
    for j, job in jobs.items():
        levels.append((f"job {shown(j)}", job.get("env"), j == "build"))
        if isinstance(job.get("container"), dict):
            levels.append((f"job {shown(j)} container", job["container"].get("env"), False))
        levels.extend((f"{shown(j)}: {shown(s.get('name') or s.get('uses'))}", s.get("env"), j == "build") for s in job.get("steps") or [])
    for scope, values, build_env in levels:
        # Added beyond the review (fix pass 4): an env no rule can read is refused.
        if values is not None and not isinstance(values, dict):
            bad.append(f"{scope} sets an env that is not a mapping, {quoted(values)}: no rule here can read its keys")
            continue
        for key in values or {}:
            if str(key).upper().startswith(ENV_PREFIXES) and not (build_env and str(key) in BUILD_PYTHON_ENV):
                bad.append(f"{scope} sets {shown(key)}")
            # R5-F4: what bash reads from the environment before a step's first line.
            if str(key).upper() in SHELL_ENV:
                bad.append(f"{scope} sets {shown(key)}, which bash reads before a step's first line (BASH_ENV and ENV name a file it runs; SHELLOPTS and BASHOPTS turn options on, SHELLOPTS=noexec running nothing)")
            # Added beyond the review (fix pass 4): bash imports BASH_FUNC_<name>%% as a function named <name>.
            if not IDENTIFIER.fullmatch(str(key)) or str(key).upper().startswith("BASH_FUNC_"):
                bad.append(f"{scope} sets {quoted(str(key))}, which is not a plain shell identifier: bash imports BASH_FUNC_<name>%% as a function that stands in for <name>")
    # Added beyond the review (fix pass 4, R5-13's capability three more ways): the build job's own env, and its
    # container's, reaches every step between the build and Record SHA256SUMS. Fix pass 4 admitted BUILD_PYTHON_ENV keys
    # there; since fix pass 8 the build job carries neither an env nor a container (its keys are the template's), and
    # this rule still names each other key.
    build_job = jobs.get("build") if isinstance(jobs.get("build"), dict) else {}
    container = build_job.get("container") if isinstance(build_job.get("container"), dict) else {}
    for scope, values in (("job build", build_job.get("env")), ("job build container", container.get("env"))):
        for key in values if isinstance(values, dict) else {}:
            if str(key) not in BUILD_PYTHON_ENV:
                bad.append(f"{scope} sets {shown(key)}: the build job's own env reaches every step between the build and {RECORD} (PATH there chose which twine ran), and since fix pass 8 the build job carries no env and no container at all (its keys are the template's)")
    # Every bash step of the workflow parses: a syntax error fails the step on every run.
    for j, job in jobs.items():
        for s in job.get("steps") or []:
            if "run" in s and str(s.get("shell") or "bash").split()[0] == "bash":
                error = bash_parses(str(s["run"]))
                if error:
                    # Fix pass 10 (M11-A): bash's message quotes the script, so it goes through visible(); since fix pass
                    # 11 (M12-C) through said(), cut and folded too.
                    bad.append(f"{shown(j)}: step {shown(s.get('name') or s.get('uses'))} does not parse as bash (bash -n): {said(error)}")
    if build is not None:
        if build.get("name") != "Build and Validate" or "environment" in build or uploads(build):
            bad.append("the build job must be 'Build and Validate', hold no environment and upload nothing")
        # Added beyond the review (fix pass 4, R5-13's class): what runs the window steps' twine is the runner's, as in
        # every port; a container image, a self-hosted runner or a service would each choose it.
        if build.get("runs-on") != "ubuntu-latest" or "container" in build or "services" in build:
            # Fix pass 9 (n10-a): a message true of every form refused.
            bad.append(f"the build job gives runs-on {quoted(build.get('runs-on'))}{', a container' if 'container' in build else ''}{', services' if 'services' in build else ''}: it gives runs-on as the template writes it, the string ubuntu-latest (any other form is refused, a one-label list naming ubuntu-latest among them), and no container or services: a container image, a service or another runner would choose what the steps between the build and {RECORD} run")
        # Fix pass 8 (M9-B): the build job's setup-python, which chooses the python3 that runs Record SHA256SUMS.
        bad.extend(setup_python_problems("build", build))
        # R4-6: a shell of the job's own wraps every step without one, those between the build and the record among them.
        if ((build.get("defaults") or {}).get("run") or {}).get("shell"):
            bad.append(f"the build job sets defaults.run.shell {quoted(build['defaults']['run']['shell'])}: every build step without a shell of its own, those between the build and {RECORD} among them, would run under it")
        guard = str(build.get("if") or "")
        if guard not in [form.format(prefix=prefix) for form in GUARD_FORMS]:
            bad.append(f"build guard {quoted(guard)} is neither of the template's two forms for PUBLISH_TAG_PREFIX {quoted(prefix)}: {[form.format(prefix=shown(prefix)) for form in GUARD_FORMS]}")
        if build.get("permissions") != {"contents": "read", "actions": "read"}:
            bad.append(f"build permissions {shown(build.get('permissions'))}")
        # Reuse step first; every later build step skipped on reuse, but the push-only release gate, exempt by its name.
        steps = build.get("steps") or []
        if not steps or steps[0].get("name") != REUSE:
            bad.append("the reuse step is not the build job's first step")
        for s in steps[1:]:
            if s.get("name") == RELEASE_GATE and s.get("if") == PUSH_ONLY:
                continue
            if s.get("if") != REUSE_IF:
                bad.append(f"build step {shown(s.get('name') or s.get('uses'))} lacks if: {REUSE_IF}")
        # Fix pass 10 (M11-C): upload-artifact in the build job only as its last step, the template's Upload dist
        # artifacts (compared whole below); and no run step of the job naming the runner's file commands for the
        # environment or the PATH, in its run or its env, in any case (ENV_FILE_NAMES). No port's build job does either.
        for s in steps:
            label = shown(s.get("name") or s.get("uses"))
            if "uses" in s and action_name(s["uses"]) == UPLOAD_ARTIFACT and s.get("name") != UPLOAD:
                bad.append(f"build: step {label} uses {quoted(s['uses'])}: the build job runs upload-artifact only as its {UPLOAD!r} step, the template's, compared whole and last, since an artifact named <PUBLISH_PACKAGE>-dist that a step uploads before the build is the one a re-run's reuse step finds (round 11's M11-12 published files the build never made, nor Record SHA256SUMS recorded)")
            if "run" in s:
                text = "\n".join(str(part) for part in [s["run"], *(s["env"].values() if isinstance(s.get("env"), dict) else [])]).lower()
                named = [name for name in ENV_FILE_NAMES if name in text]
                if named:
                    bad.append(f"build: step {label} names {named} in its run or env: a line written to the runner's file command for the environment ($GITHUB_ENV) or the PATH ($GITHUB_PATH) changes what every later build step runs, the window's twine check and {RECORD} among them (round 11's M11-9: a BASH_ENV hook added a wheel the build never made); no port's build step names either. A text check of literal spellings alone: a name built from parts, a glob or another spelling is not seen (M12-B)")
        # What the build wrote is what Record SHA256SUMS hashes (F1): each step between them runs exactly one of the
        # allowed checks, and the upload follows the record at once, as the job's last step.
        built = [i for i, s in enumerate(steps) if BUILD_COMMAND.search(str(s.get("run") or ""))]
        listed = names(build)
        if len(built) != 1 or RECORD not in listed or names(build)[-2:] != [RECORD, UPLOAD]:
            bad.append(f"the build job must build once and end at {RECORD} then {UPLOAD}: {shown(listed)}")
        else:
            # R4-6: the tag assert in juniper-ml's seven publishers alone, the smoke test in juniper-canopy's alone.
            allowed, admitted = [TWINE_CHECK], ["twine check"]
            if repo == "juniper-ml" and package in ML_PACKAGES:
                allowed.append([TAG_ASSERT.format(tool="util/" if dist_dir == "dist" else "../util/", prefix=prefix)])
                admitted.append("juniper-ml's tag assert")
            if repo == "juniper-canopy" and package == "juniper-canopy":
                allowed.append(CANOPY_SMOKE)
                admitted.append("canopy's smoke test")
            between = steps[built[0] + 1 : listed.index(RECORD)]
            odd = [s.get("name") or s.get("uses") for s in between if not set(s) <= WINDOW_STEP_KEYS or "run" not in s or commands(str(s["run"])) not in allowed]
            if odd:
                bad.append(f"a step other than {' or '.join(admitted)}, verbatim, runs between the build and {RECORD} in {repo} (each may hold name, if and run alone; the tag assert is admitted in juniper-ml alone, the smoke test in juniper-canopy alone): {shown(odd)}")
            # Fix pass 5 (R6-F1's class at the window): each step here is read by commands(), so the lines where that
            # reading and bash's could differ are refused. `twine check dist/*\` then `# || cp stash/*.whl dist/` read as
            # the allowed `twine check dist/*` (commands() skips a comment line, even inside a continuation), while bash
            # ran `twine check 'dist/*#'`, which fails, and then the cp.
            for s in between:
                if "run" in s:
                    bad.extend(f"build: step {shown(s.get('name') or s.get('uses'))} {problem}" for problem in line_problems(str(s["run"])))
        upload = step(build, UPLOAD) or {}
        if (upload.get("with") or {}).get("retention-days") != RETENTION_DAYS:
            bad.append(f"the artifact's retention is not {RETENTION_DAYS} days")
    if test is not None and prod is not None and install_id is not None:
        if needs(test) != ["build"] or needs(prod) != sorted([test_id, install_id]):
            bad.append(f"chain: {shown(test_id)}.needs={shown(test.get('needs'))}, {shown(prod_id)}.needs={shown(prod.get('needs'))}, expected build and both TestPyPI jobs")
    for job_id, job, env_name in ((test_id, test, "testpypi"), (prod_id, prod, "pypi")):
        if job is not None and environment(job) != env_name:
            bad.append(f"{shown(job_id)} environment {shown(environment(job))}, expected {env_name}")
        # Fix pass 8 (B9-1): the mapping form (cascor's sub-package publishers write it) holds the two keys GitHub's
        # schema defines for it, name and url, alone; a url is a string and only labels the deployment.
        given = job.get("environment") if job is not None else None
        if isinstance(given, dict) and not (set(given) <= {"name", "url"} and isinstance(given.get("url", ""), str)):
            bad.append(f"{shown(job_id)} environment {quoted(given)}: the mapping form holds name and url (a string, a label) alone")
    # Permissions: only the uploading jobs mint. What a job that can mint runs is its template steps, compared whole, and
    # its upload, held to the template's keys and inputs (fix pass 9, B10-1, below), each action at the template's exact
    # SHA (fix pass 9, B10-3, above); where it runs, its keys (fix pass 8, above: no container, services or other
    # runner); and beside what, the run's other jobs (fix pass 9, B10-2, above: the chain's five and the allow-list).
    minting = sorted(j for j, job in jobs.items() if (job.get("permissions") or {}).get("id-token") == "write")
    uploading = sorted(j for j, job in jobs.items() if uploads(job))
    if minting != uploading or sorted(uploading) != sorted(j for j in (test_id, prod_id, REPUBLISH) if j is not None):
        bad.append(f"id-token: write is held by {shown(minting)}, uploads are in {shown(uploading)}")
    if (top or {}).get("id-token"):
        bad.append("top-level permissions hold id-token")
    # A check made non-blocking is a check switched off: no job of the chain may continue on error, nor be skipped by an
    # if: of its own (a step-level continue-on-error or if: on a template step already fails the step comparison below).
    for job_id in ("build", test_id, install_id, prod_id, REPUBLISH):
        if job_id is not None and "continue-on-error" in (jobs.get(job_id) or {}):
            bad.append(f"job {shown(job_id)} sets continue-on-error, so its checks do not block")
    for job_id, job in ((test_id, test), (prod_id, prod)):
        if job is not None and "if" in job:
            bad.append(f"job {shown(job_id)} carries if: {quoted(job['if'])}")
    # An upload step is not a template step, so the step comparison does not see its keys.
    for job_id, job in jobs.items():
        for i in uploads(job):
            if "continue-on-error" in job["steps"][i] or "if" in job["steps"][i]:
                bad.append(f"{shown(job_id)}: its upload step sets continue-on-error or if:, so it can be skipped or ignored")
    if test is not None:
        if test.get("permissions") != {"id-token": "write"}:
            bad.append(f"{shown(test_id)} permissions {shown(test.get('permissions'))}, expected exactly id-token: write")
        # Ruling 2: the install check left the TestPyPI job for its own.
        if checkouts(test) or installs(test):
            bad.append(f"{shown(test_id)} still checks out or installs: the install check belongs in '{INSTALL_NAME}'")
        if names(test)[-1:] != [TESTPYPI_AFTER]:
            bad.append(f"{shown(test_id)} does not end at {TESTPYPI_AFTER}")
        if step_list(test) != want["test-steps"]:
            bad.append(f"{shown(test_id)} steps {shown(step_list(test))} differ from the template's {want['test-steps']}")
    if prod is not None:
        if prod.get("permissions") != {"id-token": "write"}:
            bad.append(f"{shown(prod_id)} permissions {shown(prod.get('permissions'))}, expected exactly id-token: write (it checks nothing out)")
        if step_list(prod) != want["prod-steps"]:
            bad.append(f"{shown(prod_id)} steps {shown(step_list(prod))} differ from the template's {want['prod-steps']}")
    if install is not None:
        bad.extend(check_install_job(install_id, install, test_id, package, repo, path.name, pins))
    # The template steps, as parsed YAML with every action compared by name, equal cascor's.
    have = {}
    for key, job, name in (
        (f"build/{REUSE}", build, REUSE),
        (f"build/{RECORD}", build, RECORD),
        (f"build/{UPLOAD}", build, UPLOAD),
        (f"test/{DOWNLOAD}", test, DOWNLOAD),
        (f"test/{VERIFY_DIST}", test, VERIFY_DIST),
        (f"test/{TESTPYPI_AFTER}", test, TESTPYPI_AFTER),
        (f"prod/{DOWNLOAD}", prod, DOWNLOAD),
        (f"prod/{VERIFY_DIST}", prod, VERIFY_DIST),
        (f"prod/{TESTPYPI_BEFORE}", prod, TESTPYPI_BEFORE),
        (f"prod/{PYPI_AFTER}", prod, PYPI_AFTER),
    ):
        if job is not None:
            have[key] = by_action(step(job, name))
    if republish is not None:
        have["republish-job"] = by_action(republish)
    for key, value in have.items():
        if value != want[key]:
            bad.append(f"{key} differs from the template")
    # Order, and no checkout inside the template run of each publish job.
    for job_id, job, sequence, last in (
        (test_id, test, [DOWNLOAD, VERIFY_DIST, "UPLOAD", TESTPYPI_AFTER], TESTPYPI_AFTER),
        (prod_id, prod, [DOWNLOAD, VERIFY_DIST, TESTPYPI_BEFORE, "UPLOAD", PYPI_AFTER], PYPI_AFTER),
    ):
        if job is None:
            continue
        listed = names(job)
        ups = uploads(job)
        if len(ups) != 1:
            bad.append(f"{shown(job_id)} has {len(ups)} uploads")
            continue
        try:
            at = [ups[0] if n == "UPLOAD" else listed.index(n) for n in sequence]
        except ValueError as exc:
            bad.append(f"{shown(job_id)}: {exc}")
            continue
        if at != sorted(at):
            bad.append(f"{shown(job_id)}: steps out of order {list(zip(sequence, at))}")
        between = job["steps"][at[0] : listed.index(last)]
        if [s for s in between if "@" in str(s.get("uses") or "") and action_name(s.get("uses")) == "actions/checkout"]:
            bad.append(f"{shown(job_id)}: a checkout runs between the download and {last}")
    for job_id, job in jobs.items():
        for i in uploads(job):
            # Fix pass 9: a with that is not a mapping is read as empty here (upload_problems names it), so these rules
            # never stop the others.
            inputs = job["steps"][i].get("with") if isinstance(job["steps"][i].get("with"), dict) else {}
            if "skip-existing" in inputs or "skip_existing" in inputs:
                bad.append(f"{shown(job_id)}: an upload sets skip-existing")
            if inputs.get("attestations", True) is not True:
                bad.append(f"{shown(job_id)}: an upload turns attestations off")
            if inputs.get("packages-dir") != DIST_INPUT:
                bad.append(f"{shown(job_id)}: an upload takes packages-dir {shown(inputs.get('packages-dir'))}")
    if test is not None and uploads(test) and (test["steps"][uploads(test)[0]].get("with") if isinstance(test["steps"][uploads(test)[0]].get("with"), dict) else {}).get("repository-url") != "https://test.pypi.org/legacy/":
        bad.append(f"{shown(test_id)}: the upload does not target TestPyPI")
    if prod is not None and uploads(prod) and "repository-url" in (prod["steps"][uploads(prod)[0]].get("with") if isinstance(prod["steps"][uploads(prod)[0]].get("with"), dict) else {}):
        bad.append(f"{shown(prod_id)}: the upload names a repository-url")
    # Fix pass 9 (B10-1): the four rules above read four literal keys; GitHub reads an input under any case, an expression
    # key and the action's underscore aliases. So each upload of the TestPyPI and PyPI jobs holds exactly the template's
    # keys, and its with exactly the template's inputs (upload_problems). The republish job's is compared whole, above.
    for job_id, job, kind in ((test_id, test, "TestPyPI"), (prod_id, prod, "PyPI")):
        if job is not None:
            for i in uploads(job):
                bad.extend(upload_problems(job_id, job["steps"][i], want[f"{kind}-upload"]))
    return bad


def main(argv: "list[str] | None" = None) -> int:
    # Fix pass 9 (m10-a): text a workflow holds that the output cannot encode (a lone surrogate: round 10's R10-11) is
    # printed as an escape, so printing never stops the run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True, choices=REPOS, help="the repository every WORKFLOW belongs to, as the operator knows it (R4-6)")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--pins", type=Path, default=Path(__file__).resolve().with_name(PINS_FILE), help=f"the pinned install scripts (default: {PINS_FILE}, beside this checker); an operator argument: nothing a workflow holds chooses it")
    parser.add_argument("workflows", nargs="+", type=Path)
    args = parser.parse_args(argv)
    # Fix pass 10 (M11-A): a refused pins file or template is reported on stderr with every line through visible(), as
    # every line this checker prints is (exit 1, nothing checked).
    try:
        pins, digest = load_pins(args.pins)
        print(visible(f"pins: {args.pins} (sha256 {digest}, {len(pins)} pins)"))
        want = template(args.template)
    except SystemExit as exc:
        if not isinstance(exc.code, str):
            raise
        print("\n".join(visible(part) for part in exc.code.split("\n")), file=sys.stderr)
        return 1
    failed = 0
    for path in args.workflows:
        # Fix pass 9 (m10-a): everything one workflow makes this checker do, its label and its printed lines included,
        # runs inside a catch-all: a crash (RecursionError, UnicodeEncodeError or any other) fails that workflow alone,
        # never passes it, and the next workflow is still judged.
        try:
            bad = check(path, want, args.repo, pins)
        except Exception as exc:  # noqa: BLE001 -- a crash fails this workflow alone, never passes it
            bad = [f"the checker stopped on this workflow ({type(exc).__name__}: {said(exc, 200)}): it is refused, as every crash is, and the next workflow is still checked"]
        try:
            env = load(path).get("env")
        except Exception:  # noqa: BLE001 -- m10-a: the label never stops the next workflow
            env = None
        env = env if isinstance(env, dict) else {}
        # Fix pass 10 (M11-A): the label's values through shown(); each message's first line after "    - " and every
        # further line of it (a pin mismatch's diff) indented, so no text a workflow holds begins a line; and every line
        # through visible(), so no control, line-break or format character reaches the terminal.
        try:
            label = f"{shown(path.parent.parent.parent.name)}/{shown(path.name)}"
            lines = [f"{'PASS' if not bad else 'FAIL'} {label}  (PUBLISH_PACKAGE={shown(env.get('PUBLISH_PACKAGE'))}, PUBLISH_DIST_DIR={shown(env.get('PUBLISH_DIST_DIR'))}, PUBLISH_TAG_PREFIX={shown(env.get('PUBLISH_TAG_PREFIX'))})"]
            for message in bad:
                first, *more = str(message).split("\n")
                lines.append(f"    - {first}")
                lines.extend(f"        {part.lstrip(' ')}" for part in more)
            print("\n".join(visible(line) for line in lines))
        except Exception as exc:  # noqa: BLE001 -- m10-a: a line that cannot be printed fails this workflow alone
            bad = bad or ["its result could not be printed"]
            print(visible(f"FAIL {quoted(path.name)}: its result could not be printed ({type(exc).__name__}): refused, and the next workflow is still checked"))
        failed += bool(bad)
    print(f"{len(args.workflows) - failed} of {len(args.workflows)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
